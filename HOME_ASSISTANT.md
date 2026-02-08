# Home Assistant Integration

This guide explains how to integrate Kids Rewards with Home Assistant to display pet care tasks.

## Features

- Display whose turn it is to feed Spike (or other pets)
- Show task completion status (pending, done, awaiting approval)
- Track overdue tasks
- Get summary statistics (total, done, pending, etc.)

## Prerequisites

- Kids Rewards backend deployed and accessible
- Home Assistant instance running
- API key for authentication (32+ characters)

## Setup

### 1. Generate API Key

Generate a secure API key (minimum 32 characters):

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 2. Configure Backend

#### Local Development

Create `backend/local-env.json` based on `local-env.example.json`:

```json
{
  "KidsRewardsLambdaFunction": {
    "HOME_ASSISTANT_API_KEY": "your-generated-key-here",
    "APP_SECRET_KEY": "your-app-secret-key-here-min-32-chars"
  }
}
```

#### Production Deployment

Deploy with SAM CLI:

```bash
cd backend
sam build
sam deploy --parameter-overrides HomeAssistantApiKey=<your-secure-key>
```

### 3. Configure Home Assistant

#### Add Secrets

Edit `~/.homeassistant/secrets.yaml`:

```yaml
# Kids Rewards API
kids_rewards_api_key: "your-secure-key-here"
kids_rewards_api_url: "http://localhost:3000"  # Local dev
# kids_rewards_api_url: "https://your-lambda.amazonaws.com"  # Production
```

#### Add RESTful Sensor

Edit `~/.homeassistant/configuration.yaml`:

```yaml
# Kids Rewards - Spike's Care Tasks
rest:
  - resource: !secret kids_rewards_api_url
    resource_template: "{{ value }}/api/home-assistant/pet-tasks/today"
    scan_interval: 60
    headers:
      X-HA-API-Key: !secret kids_rewards_api_key
    sensor:
      # Spike's feeding task
      - name: "Spike Feeding Task"
        value_template: >
          {% set task = value_json.tasks | selectattr('pet_name', 'eq', 'Spike')
                                          | selectattr('task_name', 'search', 'Feed')
                                          | first | default(None) %}
          {% if task %}
            {{ task.assigned_to }}'s turn at {{ task.due_time }}
          {% else %}
            No feeding scheduled today
          {% endif %}

      - name: "Spike Feeding Status"
        value_template: >
          {% set task = value_json.tasks | selectattr('pet_name', 'eq', 'Spike')
                                          | selectattr('task_name', 'search', 'Feed')
                                          | first | default(None) %}
          {% if task %}
            {{ task.status }}
          {% else %}
            none
          {% endif %}
        icon: >
          {% set task = value_json.tasks | selectattr('pet_name', 'eq', 'Spike')
                                          | selectattr('task_name', 'search', 'Feed')
                                          | first | default(None) %}
          {% if task %}
            {% if task.status == 'done' %}
              mdi:check-circle
            {% elif task.status == 'pending' %}
              mdi:clock-outline
            {% else %}
              mdi:help-circle
            {% endif %}
          {% else %}
            mdi:calendar-blank
          {% endif %}

      # Who's assigned to feed Spike (for notifications)
      - name: "Spike Feeding Assigned To"
        value_template: >
          {% set task = value_json.tasks | selectattr('pet_name', 'eq', 'Spike')
                                          | selectattr('task_name', 'search', 'Feed')
                                          | first | default(None) %}
          {% if task %}
            {{ task.assigned_to }}
          {% else %}
            none
          {% endif %}

    binary_sensor:
      # Has Spike been fed today?
      - name: "Spike Fed Today"
        value_template: >
          {% set task = value_json.tasks | selectattr('pet_name', 'eq', 'Spike')
                                          | selectattr('task_name', 'search', 'Feed')
                                          | first | default(None) %}
          {{ task and task.status == 'done' }}
        device_class: occupancy

      # Is feeding task overdue?
      - name: "Spike Feeding Overdue"
        value_template: >
          {% set task = value_json.tasks | selectattr('pet_name', 'eq', 'Spike')
                                          | selectattr('task_name', 'search', 'Feed')
                                          | first | default(None) %}
          {{ task and task.is_overdue }}
        device_class: problem
```

#### Restart Home Assistant

```bash
# Check configuration first
ha core check

# Restart
ha core restart
```

### 4. Create Dashboard Card

Via UI: Settings > Dashboards > Add Card > Entities

```yaml
type: entities
title: 🦎 Spike's Feeding Schedule
entities:
  - entity: sensor.spike_feeding_task
    name: "Who's Turn?"
  - entity: sensor.spike_feeding_status
    name: "Status"
  - entity: binary_sensor.spike_fed_today
    name: "Fed Today?"
```

## API Endpoint

### `GET /api/home-assistant/pet-tasks/today`

Returns today's pet care tasks in a Home Assistant-friendly format.

**Authentication**: Requires `X-HA-API-Key` header

**Response**:

```json
{
  "today": "2026-01-23",
  "tasks": [
    {
      "pet_name": "Spike",
      "task_name": "Feed Spike",
      "assigned_to": "Clara",
      "due_time": "08:00",
      "status": "pending",
      "points": 5,
      "is_overdue": false
    }
  ],
  "summary": {
    "total": 3,
    "done": 1,
    "pending": 1,
    "awaiting_approval": 1,
    "overdue": 0
  }
}
```

**Status values**:
- `pending`: Task is assigned but not yet submitted
- `awaiting_approval`: Task submitted by kid, waiting for parent approval
- `done`: Task approved by parent

## Optional: Notifications

Add automations for notifications. Edit `~/.homeassistant/automations.yaml` or create via UI:

### Reminder if not fed by noon

```yaml
- alias: "Spike Feeding Reminder"
  description: "Remind family if Spike hasn't been fed by noon"
  trigger:
    - platform: time
      at: "12:00:00"
  condition:
    - condition: state
      entity_id: binary_sensor.spike_fed_today
      state: "off"
    - condition: template
      value_template: "{{ states('sensor.spike_feeding_assigned_to') != 'none' }}"
  action:
    - service: notify.notify
      data:
        title: "🦎 Spike Needs Feeding"
        message: >
          It's {{ states('sensor.spike_feeding_assigned_to') }}'s turn to feed Spike today!
          Still not done yet.
```

### Celebration when task completed

```yaml
- alias: "Spike Fed - Celebrate"
  description: "Notify when someone feeds Spike"
  trigger:
    - platform: state
      entity_id: binary_sensor.spike_fed_today
      from: "off"
      to: "on"
  action:
    - service: notify.notify
      data:
        title: "🎉 Spike Fed!"
        message: >
          {{ states('sensor.spike_feeding_assigned_to') }} just fed Spike! Great job!
```

### Alert if overdue

```yaml
- alias: "Spike Feeding Overdue Alert"
  description: "Alert if Spike feeding is overdue"
  trigger:
    - platform: state
      entity_id: binary_sensor.spike_feeding_overdue
      from: "off"
      to: "on"
  action:
    - service: notify.notify
      data:
        title: "⚠️ Spike Feeding Overdue"
        message: >
          Spike's feeding was scheduled for {{ states('sensor.spike_feeding_task') }} but hasn't been done yet!
        data:
          priority: high
```

## Troubleshooting

### Sensor shows "unavailable"

1. Check API key in secrets.yaml matches backend configuration
2. Verify backend is accessible from Home Assistant
3. Check Home Assistant logs: Settings > System > Logs

### Authentication errors (401/403)

1. Verify `X-HA-API-Key` header is set correctly
2. Ensure API key is at least 32 characters
3. Check backend logs for authentication failures

### No tasks showing

1. Verify pet care tasks are assigned in Kids Rewards app
2. Check task due dates are today
3. Test endpoint directly:

```bash
curl -H "X-HA-API-Key: <your-key>" \
     http://your-backend-url/api/home-assistant/pet-tasks/today | jq
```

## Security Notes

- Store API key in `secrets.yaml`, never commit to version control
- API key must be at least 32 characters for security
- Consider rotating API keys every 90 days
- Use HTTPS in production (not HTTP)
- For production, consider AWS Secrets Manager for key storage

## Extending to Other Pets/Tasks

To monitor other pets or task types, duplicate the sensor configuration and modify:

1. Change `pet_name` filter: `'eq', 'Your Pet Name'`
2. Change `task_name` filter: `'search', 'Clean'` or `'search', 'Exercise'`
3. Update sensor names accordingly

Example for cleaning tasks:

```yaml
- name: "Spike Cleaning Task"
  value_template: >
    {% set task = value_json.tasks | selectattr('pet_name', 'eq', 'Spike')
                                    | selectattr('task_name', 'search', 'Clean')
                                    | first | default(None) %}
    {% if task %}
      {{ task.assigned_to }}'s turn at {{ task.due_time }}
    {% else %}
      No cleaning scheduled today
    {% endif %}
```
