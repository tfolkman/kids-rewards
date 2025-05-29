#!/usr/bin/env python3
"""
Seed characters using the API directly
"""

import requests
import json

# First, we need to login to get a token
login_url = "http://localhost:3000/token"
base_url = "http://localhost:3000"

# Login as parent
login_data = {
    "username": "testparent",
    "password": "password456"
}

# Get the token
print("Logging in as parent...")
response = requests.post(login_url, data=login_data)
if response.status_code != 200:
    print(f"Login failed: {response.text}")
    exit(1)

token = response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# Default characters to seed
DEFAULT_CHARACTERS = [
    {
        "name": "Dragon",
        "emoji": "🐉",
        "color": "#FF6B6B",
        "description": "A fierce and powerful dragon",
        "unlocked_at_points": 0
    },
    {
        "name": "Unicorn",
        "emoji": "🦄",
        "color": "#C77DFF",
        "description": "A magical unicorn",
        "unlocked_at_points": 50
    },
    {
        "name": "Robot",
        "emoji": "🤖",
        "color": "#4ECDC4",
        "description": "A futuristic robot",
        "unlocked_at_points": 100
    },
    {
        "name": "Wizard",
        "emoji": "🧙",
        "color": "#667BC6",
        "description": "A wise and powerful wizard",
        "unlocked_at_points": 200
    },
    {
        "name": "Dinosaur",
        "emoji": "🦕",
        "color": "#95D5B2",
        "description": "A friendly dinosaur",
        "unlocked_at_points": 300
    },
    {
        "name": "Astronaut",
        "emoji": "👨‍🚀",
        "color": "#1D3557",
        "description": "An explorer of space",
        "unlocked_at_points": 500
    },
    {
        "name": "Ninja",
        "emoji": "🥷",
        "color": "#2A2A2A",
        "description": "A stealthy ninja warrior",
        "unlocked_at_points": 750
    },
    {
        "name": "Phoenix",
        "emoji": "🔥",
        "color": "#FF9F1C",
        "description": "A legendary phoenix rising from the ashes",
        "unlocked_at_points": 1000
    }
]

# Check existing characters
print("Checking existing characters...")
response = requests.get(f"{base_url}/characters/", headers=headers)
if response.status_code == 200:
    existing_characters = response.json()
    existing_names = {char["name"] for char in existing_characters}
    print(f"Found {len(existing_characters)} existing characters")
else:
    print(f"Failed to get characters: {response.text}")
    existing_names = set()

# Create characters
created_count = 0
for char_data in DEFAULT_CHARACTERS:
    if char_data["name"] not in existing_names:
        print(f"Creating character: {char_data['name']} {char_data['emoji']}")
        response = requests.post(f"{base_url}/characters/", json=char_data, headers=headers)
        if response.status_code == 201:
            print(f"✓ Created successfully")
            created_count += 1
        else:
            print(f"✗ Failed: {response.text}")
    else:
        print(f"Character {char_data['name']} already exists, skipping...")

print(f"\nSeeding complete! Created {created_count} new characters.")

# Verify total characters
response = requests.get(f"{base_url}/characters/", headers=headers)
if response.status_code == 200:
    total_characters = len(response.json())
    print(f"Total characters in database: {total_characters}")