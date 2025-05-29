#!/usr/bin/env python3
"""
Seed script to create default characters in the database.
"""

import os
import sys
import json

# Add parent directory to path to import backend modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

import crud
import models

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

def seed_characters():
    """Seed the database with default characters."""
    print("Seeding characters...")
    
    # Get existing characters to avoid duplicates
    existing_characters = crud.get_all_characters()
    existing_names = {char.name for char in existing_characters}
    
    created_count = 0
    for char_data in DEFAULT_CHARACTERS:
        if char_data["name"] not in existing_names:
            try:
                character = models.CharacterCreate(**char_data)
                created_char = crud.create_character(character)
                print(f"Created character: {created_char.name} {created_char.emoji}")
                created_count += 1
            except Exception as e:
                print(f"Error creating character {char_data['name']}: {e}")
        else:
            print(f"Character {char_data['name']} already exists, skipping...")
    
    print(f"\nSeeding complete! Created {created_count} new characters.")
    print(f"Total characters in database: {len(crud.get_all_characters())}")

if __name__ == "__main__":
    seed_characters()