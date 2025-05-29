#!/bin/bash

# Add remaining characters
aws dynamodb put-item \
  --table-name KidsRewardsCharacters \
  --item '{
    "id": {"S": "char-4"},
    "name": {"S": "Wizard"},
    "emoji": {"S": "🧙"},
    "color": {"S": "#667BC6"},
    "description": {"S": "A wise and powerful wizard"},
    "unlocked_at_points": {"N": "200"},
    "created_at": {"S": "2025-05-29T15:48:03Z"},
    "is_active": {"BOOL": true}
  }' \
  --endpoint-url http://localhost:8000

aws dynamodb put-item \
  --table-name KidsRewardsCharacters \
  --item '{
    "id": {"S": "char-5"},
    "name": {"S": "Dinosaur"},
    "emoji": {"S": "🦕"},
    "color": {"S": "#95D5B2"},
    "description": {"S": "A friendly dinosaur"},
    "unlocked_at_points": {"N": "300"},
    "created_at": {"S": "2025-05-29T15:48:04Z"},
    "is_active": {"BOOL": true}
  }' \
  --endpoint-url http://localhost:8000

aws dynamodb put-item \
  --table-name KidsRewardsCharacters \
  --item '{
    "id": {"S": "char-6"},
    "name": {"S": "Astronaut"},
    "emoji": {"S": "👨‍🚀"},
    "color": {"S": "#1D3557"},
    "description": {"S": "An explorer of space"},
    "unlocked_at_points": {"N": "500"},
    "created_at": {"S": "2025-05-29T15:48:05Z"},
    "is_active": {"BOOL": true}
  }' \
  --endpoint-url http://localhost:8000

aws dynamodb put-item \
  --table-name KidsRewardsCharacters \
  --item '{
    "id": {"S": "char-7"},
    "name": {"S": "Ninja"},
    "emoji": {"S": "🥷"},
    "color": {"S": "#2A2A2A"},
    "description": {"S": "A stealthy ninja warrior"},
    "unlocked_at_points": {"N": "750"},
    "created_at": {"S": "2025-05-29T15:48:06Z"},
    "is_active": {"BOOL": true}
  }' \
  --endpoint-url http://localhost:8000

aws dynamodb put-item \
  --table-name KidsRewardsCharacters \
  --item '{
    "id": {"S": "char-8"},
    "name": {"S": "Phoenix"},
    "emoji": {"S": "🔥"},
    "color": {"S": "#FF9F1C"},
    "description": {"S": "A legendary phoenix rising from the ashes"},
    "unlocked_at_points": {"N": "1000"},
    "created_at": {"S": "2025-05-29T15:48:07Z"},
    "is_active": {"BOOL": true}
  }' \
  --endpoint-url http://localhost:8000

echo "All characters added successfully!"