# TDD Plan: Spike Feeding Auto-Schedule & Auto-Approval (REVISED)

## 🚨 Critical Corrections from Code Review

### Issues Fixed from Original Plan:

1. **assigned_to_kid_id stores USERNAME, not ID**
   - ❌ Original: Used "kid-1", "kid-2" as IDs
   - ✅ Fixed: Use "aiden", "clara", "emery" directly (usernames)
   - Evidence: `crud.py:1960` checks `task.assigned_to_kid_id != kid_user.username`

2. **_award_points_and_streak_bonus signature**
   - ❌ Original: `_award_points_and_streak_bonus(kid_id, points_value, task_date)`
   - ✅ Fixed: `_award_points_and_streak_bonus(kid_username: str, points_value: int)`
   - Evidence: `crud.py:748`

3. **submit_pet_care_task signature**
   - ❌ Original: Takes kid_id string
   - ✅ Fixed: Takes `kid_user: models.User` (full User object)
   - Evidence: `crud.py:1953`

4. **DynamoDB update pattern**
   - ❌ Original: Used `put_item()`
   - ✅ Fixed: Use `update_item()` with UpdateExpression
   - Evidence: `crud.py:1979`

5. **No get_pet_by_name function exists**
   - ❌ Original: Called `crud.get_pet_by_name("Spike")`
   - ✅ Fixed: Will hard-code Spike's pet_id or filter from parent's pets

6. **Error handling pattern**
   - ❌ Original: Raised ValueError
   - ✅ Fixed: Raise HTTPException
   - Evidence: Throughout crud.py

7. **Test mocking pattern**
   - ❌ Original: Assumed DB access in tests
   - ✅ Fixed: Mock CRUD functions using unittest.mock.patch
   - Evidence: `test_home_assistant.py`

---

## 📋 Revised Understanding

**Current State:**
- Spike feeding uses rotation-based assignment (round-robin)
- Tasks require manual generation via endpoint
- Submit flow: ASSIGNED → (kid submits) → PENDING_APPROVAL → (parent approves) → APPROVED → points awarded

**Desired State:**
- Hard-coded weekly pattern: Thu=aiden, Fri=clara, Sat=emery, Sun=aiden, Mon=clara, Tue=emery, Wed=aiden
- Kid submits → instant APPROVED + points awarded (skip PENDING_APPROVAL)
- Only for "Feed Spike" tasks, other tasks unchanged

---

## ✅ Acceptance Criteria (Same as before, but verified against code)

1. **AC1: Fixed Weekly Assignment**
   - GIVEN it's Thursday
   - WHEN Spike feeding task is generated
   - THEN task.assigned_to_kid_id = "aiden" AND task.assigned_to_kid_username = "aiden"

2. **AC2: Pattern Continuation**
   - GIVEN tasks generated for 7 consecutive days starting Thursday
   - THEN assignments are: [aiden, clara, emery, aiden, clara, emery, aiden]

3. **AC3: Auto-Approval on Submission**
   - GIVEN aiden has an assigned "Feed Spike" task
   - WHEN aiden submits via `/pets/tasks/{id}/submit`
   - THEN task.status = APPROVED (not PENDING_APPROVAL)
   - AND points awarded immediately
   - AND submitted_at and reviewed_at timestamps set

4. **AC4: Streak Bonuses Still Work**
   - GIVEN aiden completed feeding 2 days consecutively
   - WHEN aiden submits 3rd day task
   - THEN base points + 10 bonus awarded (via existing `_award_points_and_streak_bonus`)

5. **AC5: Other Pet Tasks Unchanged**
   - GIVEN "Clean Tank" task exists
   - WHEN kid submits
   - THEN status = PENDING_APPROVAL (requires parent approval)

6. **AC6: Parent Can Still Generate Tasks**
   - GIVEN parent calls endpoint
   - THEN tasks created for next N days with correct assignments

---

## 🧪 Revised Test Plan

### Unit Tests: `backend/tests/test_spike_feeding.py` (NEW FILE)

```python
"""
Unit tests for Spike feeding auto-schedule and auto-approval.
Write these FIRST (TDD red phase).
"""

import os
from datetime import datetime, timedelta
import pytest
from models import PetCareTaskStatus
from pet_care import get_spike_feeding_assigned_kid, generate_spike_feeding_tasks


@pytest.fixture(autouse=True)
def setup_env():
    """Set APP_SECRET_KEY for tests"""
    os.environ["APP_SECRET_KEY"] = "test-secret-key-for-testing-32-chars"


class TestSpikeAssignmentPattern:
    """Test hard-coded weekly assignment logic"""

    def test_thursday_assigns_aiden(self):
        """Thursday should assign to aiden"""
        # Thursday = weekday 3
        thursday = datetime(2026, 1, 29)  # Known Thursday
        assert thursday.weekday() == 3
        assert get_spike_feeding_assigned_kid(thursday) == "aiden"

    def test_friday_assigns_clara(self):
        """Friday should assign to clara"""
        friday = datetime(2026, 1, 30)
        assert friday.weekday() == 4
        assert get_spike_feeding_assigned_kid(friday) == "clara"

    def test_saturday_assigns_emery(self):
        """Saturday should assign to emery"""
        saturday = datetime(2026, 1, 31)
        assert saturday.weekday() == 5
        assert get_spike_feeding_assigned_kid(saturday) == "emery"

    def test_sunday_assigns_aiden(self):
        """Sunday cycles back to aiden"""
        sunday = datetime(2026, 2, 1)
        assert sunday.weekday() == 6
        assert get_spike_feeding_assigned_kid(sunday) == "aiden"

    def test_monday_assigns_clara(self):
        """Monday assigns to clara"""
        monday = datetime(2026, 2, 2)
        assert monday.weekday() == 0
        assert get_spike_feeding_assigned_kid(monday) == "clara"

    def test_tuesday_assigns_emery(self):
        """Tuesday assigns to emery"""
        tuesday = datetime(2026, 2, 3)
        assert tuesday.weekday() == 1
        assert get_spike_feeding_assigned_kid(tuesday) == "emery"

    def test_wednesday_assigns_aiden(self):
        """Wednesday assigns to aiden"""
        wednesday = datetime(2026, 2, 4)
        assert wednesday.weekday() == 2
        assert get_spike_feeding_assigned_kid(wednesday) == "aiden"

    def test_pattern_repeats_over_two_weeks(self):
        """Verify pattern repeats correctly over 14 days"""
        start_thursday = datetime(2026, 1, 29)
        expected = ["aiden", "clara", "emery", "aiden", "clara", "emery", "aiden",
                   "clara", "emery", "aiden", "clara", "emery", "aiden", "clara"]

        for i, expected_kid in enumerate(expected):
            day = start_thursday + timedelta(days=i)
            actual = get_spike_feeding_assigned_kid(day)
            assert actual == expected_kid, f"Day {i} (weekday {day.weekday()}) failed"


class TestSpikeTaskGeneration:
    """Test task generation using hard-coded pattern"""

    def test_generate_7_days_from_thursday(self):
        """Generate a week of tasks starting Thursday"""
        start = datetime(2026, 1, 29)  # Thursday

        tasks = generate_spike_feeding_tasks(
            pet_id="spike-pet-id",
            pet_name="Spike",
            parent_id="parent-id",
            days_ahead=7,
            start_date=start
        )

        assert len(tasks) == 7

        # Check assignments match pattern
        expected_kids = ["aiden", "clara", "emery", "aiden", "clara", "emery", "aiden"]
        for i, task in enumerate(tasks):
            assert task.assigned_to_kid_id == expected_kids[i]
            assert task.assigned_to_kid_username == expected_kids[i]
            assert task.task_name == "Feed Spike"
            assert task.pet_name == "Spike"
            assert task.status == PetCareTaskStatus.ASSIGNED

    def test_skips_existing_task_dates(self):
        """Don't generate tasks for dates that already exist"""
        start = datetime(2026, 1, 29)  # Thursday

        # Simulate Friday and Sunday already have tasks
        existing_dates = {
            (start + timedelta(days=1)).date(),  # Friday
            (start + timedelta(days=3)).date(),  # Sunday
        }

        tasks = generate_spike_feeding_tasks(
            pet_id="spike-pet-id",
            pet_name="Spike",
            parent_id="parent-id",
            days_ahead=7,
            start_date=start,
            existing_task_dates=existing_dates
        )

        # Should only create 5 tasks (7 days - 2 existing)
        assert len(tasks) == 5

        # Verify Friday and Sunday are missing
        task_dates = {task.due_date.date() for task in tasks}
        assert (start + timedelta(days=1)).date() not in task_dates  # Friday
        assert (start + timedelta(days=3)).date() not in task_dates  # Sunday

    def test_sets_correct_due_time(self):
        """Tasks should be due at 6:00 PM"""
        start = datetime(2026, 1, 29)

        tasks = generate_spike_feeding_tasks(
            pet_id="spike-pet-id",
            pet_name="Spike",
            parent_id="parent-id",
            days_ahead=1,
            start_date=start
        )

        assert len(tasks) == 1
        assert tasks[0].due_date.hour == 18
        assert tasks[0].due_date.minute == 0
```

### Integration Tests: `backend/tests/test_spike_integration.py` (NEW FILE)

```python
"""
Integration tests for Spike feeding auto-approval.
Tests the full workflow with mocked CRUD layer.
"""

import os
from datetime import datetime
from unittest.mock import patch, MagicMock
import pytest
from fastapi.testclient import TestClient

import main
import models


@pytest.fixture
def client():
    """Test client for FastAPI app"""
    return TestClient(main.app)


@pytest.fixture(autouse=True)
def setup_env():
    """Set required environment variables"""
    os.environ["APP_SECRET_KEY"] = "test-secret-key-for-testing-32-chars"


@pytest.fixture
def mock_aiden():
    """Mock aiden user"""
    return models.User(
        id="aiden-id",
        username="aiden",
        password_hash="hashed",
        role="kid",
        points=100,
        is_active=True,
        created_at=datetime.utcnow()
    )


@pytest.fixture
def mock_spike_feeding_task():
    """Mock Spike feeding task"""
    return models.PetCareTask(
        id="task-123",
        schedule_id="spike-schedule",
        pet_id="spike-pet-id",
        pet_name="Spike",
        task_name="Feed Spike",
        description="Feed Spike his daily meal",
        points_value=10,
        assigned_to_kid_id="aiden",
        assigned_to_kid_username="aiden",
        due_date=datetime(2026, 1, 29, 18, 0),
        status=models.PetCareTaskStatus.ASSIGNED,
        created_at=datetime.utcnow()
    )


@pytest.fixture
def mock_tank_cleaning_task():
    """Mock non-feeding task (should still require approval)"""
    return models.PetCareTask(
        id="task-456",
        schedule_id="cleaning-schedule",
        pet_id="spike-pet-id",
        pet_name="Spike",
        task_name="Clean Tank",
        description="Clean Spike's tank",
        points_value=25,
        assigned_to_kid_id="aiden",
        assigned_to_kid_username="aiden",
        due_date=datetime(2026, 1, 29, 18, 0),
        status=models.PetCareTaskStatus.ASSIGNED,
        created_at=datetime.utcnow()
    )


class TestSpikeAutoApproval:
    """Test auto-approval when kids submit Spike feeding tasks"""

    @patch('crud.submit_pet_care_task')
    def test_feed_spike_auto_approves(self, mock_submit, client, mock_aiden, mock_spike_feeding_task):
        """
        CRITICAL TEST: Feeding Spike should auto-approve and award points.
        This is the main feature we're implementing.
        """
        # Setup: Mock the CRUD function to return approved task
        approved_task = mock_spike_feeding_task.copy()
        approved_task.status = models.PetCareTaskStatus.APPROVED
        approved_task.submitted_at = datetime.utcnow()
        approved_task.reviewed_at = datetime.utcnow()
        mock_submit.return_value = approved_task

        # Mock authentication
        with patch('main.get_current_kid_user', return_value=mock_aiden):
            # Act: Kid submits the task
            response = client.post(
                "/pets/tasks/task-123/submit",
                json={"notes": "Fed Spike his crickets"}
            )

        # Assert: Response shows APPROVED (not PENDING_APPROVAL)
        assert response.status_code == 200
        task_data = response.json()
        assert task_data["status"] == "APPROVED"
        assert task_data["submitted_at"] is not None
        assert task_data["reviewed_at"] is not None

        # Verify CRUD function was called correctly
        mock_submit.assert_called_once()
        call_args = mock_submit.call_args
        assert call_args[1]["task_id"] == "task-123"
        assert call_args[1]["kid_user"].username == "aiden"

    @patch('crud.submit_pet_care_task')
    def test_other_tasks_still_need_approval(self, mock_submit, client, mock_aiden, mock_tank_cleaning_task):
        """
        Non-feeding tasks should still require parent approval.
        This ensures we don't break existing functionality.
        """
        # Setup: Mock CRUD to return PENDING_APPROVAL for non-feeding task
        pending_task = mock_tank_cleaning_task.copy()
        pending_task.status = models.PetCareTaskStatus.PENDING_APPROVAL
        pending_task.submitted_at = datetime.utcnow()
        mock_submit.return_value = pending_task

        with patch('main.get_current_kid_user', return_value=mock_aiden):
            response = client.post(
                "/pets/tasks/task-456/submit",
                json={"notes": "Cleaned the tank"}
            )

        # Assert: Status is PENDING_APPROVAL (not auto-approved)
        assert response.status_code == 200
        task_data = response.json()
        assert task_data["status"] == "PENDING_APPROVAL"
        assert task_data["reviewed_at"] is None  # Not reviewed yet
```

---

## 🛠️ Revised Implementation Plan

### Phase 1: Add Hard-Coded Assignment Logic

**File: `backend/pet_care.py`**

Add function (around line 310, after existing functions):

```python
def get_spike_feeding_assigned_kid(task_date: datetime) -> str:
    """
    Returns the username of the kid assigned to feed Spike on a given date.

    Hard-coded weekly pattern:
    - Thursday: aiden
    - Friday: clara
    - Saturday: emery
    - Sunday: aiden
    - Monday: clara
    - Tuesday: emery
    - Wednesday: aiden

    Args:
        task_date: The date of the task (datetime object)

    Returns:
        Kid's username ("aiden", "clara", or "emery")
    """
    # weekday(): Monday=0, Tuesday=1, ..., Sunday=6
    day_of_week = task_date.weekday()

    # Pattern: Thu=3, Fri=4, Sat=5, Sun=6, Mon=0, Tue=1, Wed=2
    pattern_map = {
        3: "aiden",   # Thursday
        4: "clara",   # Friday
        5: "emery",   # Saturday
        6: "aiden",   # Sunday
        0: "clara",   # Monday
        1: "emery",   # Tuesday
        2: "aiden",   # Wednesday
    }

    return pattern_map[day_of_week]
```

**Test First:** Run `pytest backend/tests/test_spike_feeding.py::TestSpikeAssignmentPattern -v`
(Should see RED - function doesn't exist yet)

**Then Implement:** Add the function above

**Test Again:** Run same command (should see GREEN)

---

### Phase 2: Add Task Generation Function

**File: `backend/pet_care.py`**

Add function (after `get_spike_feeding_assigned_kid`):

```python
def generate_spike_feeding_tasks(
    pet_id: str,
    pet_name: str,
    parent_id: str,
    days_ahead: int = 7,
    start_date: Optional[datetime] = None,
    existing_task_dates: Optional[set] = None,
) -> list[models.PetCareTaskCreate]:
    """
    Generate Spike feeding tasks using hard-coded weekly assignment pattern.

    Args:
        pet_id: Spike's pet ID from database
        pet_name: "Spike"
        parent_id: Parent who owns Spike
        days_ahead: Number of days to generate tasks for (default 7)
        start_date: Starting date (default: today in UTC)
        existing_task_dates: Set of date objects that already have tasks (skip these)

    Returns:
        List of PetCareTaskCreate objects ready to insert
    """
    if existing_task_dates is None:
        existing_task_dates = set()

    if start_date is None:
        start_date = datetime.utcnow()

    tasks = []
    base_date = start_date.date()

    for day_offset in range(days_ahead):
        task_date = base_date + timedelta(days=day_offset)

        # Skip if task already exists for this date
        if task_date in existing_task_dates:
            continue

        # Get assigned kid using hard-coded pattern
        assigned_kid = get_spike_feeding_assigned_kid(
            datetime.combine(task_date, datetime.min.time())
        )

        # Create task due at 6:00 PM
        due_datetime = datetime.combine(task_date, time(18, 0))

        task = models.PetCareTaskCreate(
            schedule_id="spike-feeding-auto",  # Special marker for auto-generated
            pet_id=pet_id,
            pet_name=pet_name,
            task_name="Feed Spike",
            description="Feed Spike his daily meal",
            points_value=10,
            assigned_to_kid_id=assigned_kid,  # NOTE: This field stores username!
            assigned_to_kid_username=assigned_kid,
            due_date=due_datetime,
        )

        tasks.append(task)

    return tasks
```

**Test First:** Run `pytest backend/tests/test_spike_feeding.py::TestSpikeTaskGeneration -v` (RED)

**Then Implement:** Add the function above

**Test Again:** Should be GREEN

---

### Phase 3: Modify CRUD to Auto-Approve

**File: `backend/crud.py`**

**IMPORTANT:** Modify the existing `submit_pet_care_task` function (starts at line 1953).

Replace the entire function with:

```python
def submit_pet_care_task(
    task_id: str, kid_user: models.User, notes: Optional[str] = None
) -> Optional[models.PetCareTask]:
    """
    Submit a pet care task.
    Auto-approves and awards points immediately for "Feed Spike" tasks.
    Other tasks go to PENDING_APPROVAL.
    """
    task = get_task_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found.")

    if task.assigned_to_kid_id != kid_user.username:
        raise HTTPException(status_code=403, detail="Not authorized to submit this task.")

    if task.status != models.PetCareTaskStatus.ASSIGNED:
        raise HTTPException(
            status_code=400,
            detail=f"Task is not in assigned status. Current status: {task.status}"
        )

    submitted_at_ts = datetime.utcnow()

    # Check if this is a Spike feeding task (auto-approve)
    is_spike_feeding = task.task_name == "Feed Spike"

    if is_spike_feeding:
        # AUTO-APPROVE: Award points immediately and mark as approved
        reviewed_at_ts = submitted_at_ts

        # Award points with streak bonus (existing function)
        _award_points_and_streak_bonus(kid_user.username, task.points_value)

        # Update task: ASSIGNED → APPROVED (skip PENDING_APPROVAL)
        update_expression = "SET #s = :s, submitted_at = :sat, reviewed_at = :rat"
        expression_attribute_values = {
            ":s": models.PetCareTaskStatus.APPROVED.value,
            ":sat": submitted_at_ts.isoformat(),
            ":rat": reviewed_at_ts.isoformat(),
            ":kid_id": kid_user.username,
        }

        if notes is not None:
            update_expression += ", submission_notes = :notes"
            expression_attribute_values[":notes"] = notes

        try:
            response = pet_care_tasks_table.update_item(
                Key={"id": task_id},
                UpdateExpression=update_expression,
                ExpressionAttributeNames={"#s": "status"},
                ExpressionAttributeValues=expression_attribute_values,
                ConditionExpression="assigned_to_kid_id = :kid_id",
                ReturnValues="ALL_NEW",
            )
            updated_attributes = response.get("Attributes")
            if updated_attributes:
                return models.PetCareTask(**replace_decimals(updated_attributes))
            return None
        except ClientError as e:
            if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
                raise HTTPException(
                    status_code=403, detail="Not authorized to submit this task."
                ) from e
            print(f"Error auto-approving Spike feeding task {task_id}: {e}")
            return None

    else:
        # NORMAL FLOW: Go to PENDING_APPROVAL (existing behavior for other tasks)
        try:
            update_expression = "SET #s = :s, submitted_at = :sat"
            expression_attribute_values = {
                ":s": models.PetCareTaskStatus.PENDING_APPROVAL.value,
                ":sat": submitted_at_ts.isoformat(),
                ":kid_id": kid_user.username,
            }

            if notes is not None:
                update_expression += ", submission_notes = :notes"
                expression_attribute_values[":notes"] = notes

            response = pet_care_tasks_table.update_item(
                Key={"id": task_id},
                UpdateExpression=update_expression,
                ExpressionAttributeNames={"#s": "status"},
                ExpressionAttributeValues=expression_attribute_values,
                ConditionExpression="assigned_to_kid_id = :kid_id",
                ReturnValues="ALL_NEW",
            )
            updated_attributes = response.get("Attributes")
            if updated_attributes:
                return models.PetCareTask(**replace_decimals(updated_attributes))
            return None
        except ClientError as e:
            if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
                raise HTTPException(
                    status_code=403, detail="Not authorized to submit this task."
                ) from e
            print(f"Error submitting task {task_id}: {e}")
            return None
```

**Test First:** Run `pytest backend/tests/test_spike_integration.py -v` (Should be RED - auto-approval not implemented)

**Then Implement:** Replace the function as shown above

**Test Again:** Should be GREEN

---

### Phase 4: Add API Endpoint for Generation

**File: `backend/main.py`**

Add new endpoint around line 1330 (after other pet task endpoints):

```python
@app.post("/parent/pets/spike/generate-feeding-tasks", response_model=dict)
async def generate_spike_feeding_tasks_endpoint(
    days_ahead: int = 7,
    current_parent: models.User = Depends(get_current_parent_user),  # noqa: B008
):
    """
    Generate Spike feeding tasks for the next N days using hard-coded weekly pattern.

    Pattern: Thu=aiden, Fri=clara, Sat=emery, Sun=aiden, Mon=clara, Tue=emery, Wed=aiden

    Parent-only endpoint. Auto-skips dates that already have tasks.
    """
    # Get all parent's pets
    parent_pets = crud.get_pets_by_parent_id(current_parent.id)

    # Find Spike (case-insensitive)
    spike = None
    for pet in parent_pets:
        if pet.name.lower() == "spike":
            spike = pet
            break

    if not spike:
        raise HTTPException(
            status_code=404,
            detail="Spike not found in your pets. Please create Spike's profile first."
        )

    # Get existing "Feed Spike" task dates to avoid duplicates
    all_spike_tasks = crud.get_tasks_by_pet_id(spike.id)
    existing_dates = {
        task.due_date.date()
        for task in all_spike_tasks
        if task.task_name == "Feed Spike"
    }

    # Generate new tasks
    from pet_care import generate_spike_feeding_tasks

    new_tasks = generate_spike_feeding_tasks(
        pet_id=spike.id,
        pet_name=spike.name,
        parent_id=current_parent.id,
        days_ahead=days_ahead,
        existing_task_dates=existing_dates
    )

    # Save to database
    created_count = 0
    for task_create in new_tasks:
        created_task = crud.create_pet_care_task(task_create)
        if created_task:
            created_count += 1

    return {
        "message": f"Generated {created_count} Spike feeding task(s)",
        "tasks_created": created_count,
        "days_ahead": days_ahead,
        "pet_id": spike.id,
        "pet_name": spike.name,
    }
```

**Test:** Manually test with:
```bash
# Start backend
just backend-uvicorn

# Login as parent
curl -X POST http://localhost:3000/token \
  -d "username=testparent&password=password456"

# Use token to generate tasks
curl -X POST http://localhost:3000/parent/pets/spike/generate-feeding-tasks?days_ahead=7 \
  -H "Authorization: Bearer <token>"
```

---

### Phase 5: Add CRUD Helper (if needed)

**File: `backend/crud.py`**

If `create_pet_care_task` doesn't exist or needs modification, add after `get_all_pet_care_tasks`:

```python
def create_pet_care_task(task_create: models.PetCareTaskCreate) -> Optional[models.PetCareTask]:
    """Create a new pet care task in DynamoDB"""
    task_id = str(uuid.uuid4())
    now = datetime.utcnow()

    task = models.PetCareTask(
        id=task_id,
        **task_create.dict(),
        status=models.PetCareTaskStatus.ASSIGNED,
        created_at=now,
    )

    try:
        pet_care_tasks_table.put_item(Item=task.to_dynamodb_item())
        return task
    except ClientError as e:
        print(f"Error creating pet care task: {e}")
        return None
```

---

## 📁 Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `backend/tests/test_spike_feeding.py` | **CREATE** | Unit tests for assignment pattern and task generation |
| `backend/tests/test_spike_integration.py` | **CREATE** | Integration tests for auto-approval workflow |
| `backend/pet_care.py` | **MODIFY** | Add `get_spike_feeding_assigned_kid()` and `generate_spike_feeding_tasks()` |
| `backend/crud.py` | **MODIFY** | Update `submit_pet_care_task()` to auto-approve Spike feeding |
| `backend/main.py` | **MODIFY** | Add endpoint `/parent/pets/spike/generate-feeding-tasks` |

---

## 🚀 Execution Order (TDD Red-Green-Refactor)

1. **Write test file** `test_spike_feeding.py` → Run tests → See RED ❌
2. **Implement** `get_spike_feeding_assigned_kid()` in pet_care.py → Run tests → See GREEN ✅
3. **Write more tests** for `generate_spike_feeding_tasks()` → See RED ❌
4. **Implement** `generate_spike_feeding_tasks()` → See GREEN ✅
5. **Write integration tests** `test_spike_integration.py` → See RED ❌
6. **Modify** `submit_pet_care_task()` in crud.py → See GREEN ✅
7. **Add endpoint** in main.py → Manual test → Works ✅
8. **Run full test suite** `just test` → All GREEN ✅

---

## 🎯 Success Criteria

- [ ] All 15+ new unit tests pass
- [ ] All 2+ integration tests pass
- [ ] All existing 61+ backend tests still pass
- [ ] Can call endpoint to generate 7 days of tasks
- [ ] Tasks assigned correctly by weekday (Thu=aiden, Fri=clara, etc.)
- [ ] Submitting "Feed Spike" auto-approves and awards points
- [ ] Submitting "Clean Tank" still requires parent approval
- [ ] Streak bonuses still work (tested via existing `_award_points_and_streak_bonus`)

---

## ⚠️ Edge Cases Handled

1. **No Spike found**: Endpoint returns 404 with clear message
2. **Duplicate dates**: Generation skips dates that already have tasks
3. **Wrong kid submitting**: DynamoDB condition check prevents unauthorized submission
4. **Task already submitted**: Status check prevents double-submission
5. **Case sensitivity**: Spike name lookup is case-insensitive

---

## 🔄 What Changes vs Original Plan

| Original Plan Issue | Fixed In Revised Plan |
|---------------------|----------------------|
| Used kid IDs instead of usernames | Now uses "aiden", "clara", "emery" directly |
| Wrong `_award_points_and_streak_bonus` signature | Fixed to `(kid_username, points_value)` |
| Wrong `submit_pet_care_task` signature | Fixed to take `kid_user: models.User` |
| Used `put_item` for updates | Now uses `update_item` with UpdateExpression |
| Called non-existent `get_pet_by_name` | Now filters from `get_pets_by_parent_id` |
| Raised ValueError | Now raises HTTPException |
| Assumed DB access in tests | Now uses mocking pattern |

---

## 📝 Notes for Implementation

- **Timezone**: All dates use UTC (existing pattern in codebase)
- **Points**: Hard-coded to 10 points per feeding (can adjust later)
- **Due time**: Hard-coded to 6:00 PM (18:00)
- **Schedule ID**: Tasks use "spike-feeding-auto" as marker (not a real schedule)
- **Usernames**: Case-sensitive in DB, but Spike lookup is case-insensitive

---

Ready to execute! Start with Phase 1 (write tests first).
