"""
Pet Care Guide Module

Generates detailed, kid-friendly care instructions for different pet species.
Instructions are tailored to the pet's life stage and specific task type.
"""
from enum import Enum
from typing import Optional


class CareTaskType(str, Enum):
    FEEDING = "feeding"
    WATER = "water"
    CLEANING = "cleaning"
    EXERCISE = "exercise"
    HEALTH_CHECK = "health_check"


class PetSpecies(str, Enum):
    BEARDED_DRAGON = "bearded_dragon"
    DOG = "dog"
    CAT = "cat"
    FISH = "fish"
    HAMSTER = "hamster"
    RABBIT = "rabbit"


class LifeStage(str, Enum):
    BABY = "baby"
    JUVENILE = "juvenile"
    SUB_ADULT = "sub_adult"
    ADULT = "adult"
    SENIOR = "senior"


# Bearded Dragon Care Instructions
BEARDED_DRAGON_INSTRUCTIONS = {
    "feeding": {
        "insects": {
            LifeStage.BABY: """
**Feeding Baby Bearded Dragon - Insects**

📋 What you need:
• 30-50 micro Dubia roaches (1/4 inch size - very small!)
• Calcium powder
• Escape-proof feeding dish

📊 Daily amount: 30-50 micro roaches

📝 Steps:
1. Put the roaches in a bag or container
2. Add a small pinch of calcium powder
3. Shake gently so roaches get a light white coating
4. Put ALL the dusted roaches in the feeding dish
5. Place dish in tank (NOT under the basking light - roaches will overheat!)
6. Let your beardie hunt throughout the day
7. Remove any uneaten roaches at night before bed

💡 Tip: You can add greens to the same dish - roaches will eat them too!

⚠️ Remember: Roaches should be NO bigger than the space between the eyes!
""",
            LifeStage.JUVENILE: """
**Feeding Juvenile Bearded Dragon - Insects**

📋 What you need:
• Medium Dubia roaches (1/2 inch size)
• Calcium powder
• Escape-proof feeding dish

📊 Daily amount (by age):
• 4-5 months old: 15-25 medium roaches
• 6-9 months old: 10-15 medium roaches
• 10-11 months old: 10-13 medium roaches

📝 Steps:
1. Put the roaches in a bag or container
2. Add a small pinch of calcium powder
3. Shake gently so roaches get a light white coating
4. Put ALL the dusted roaches in the feeding dish
5. Place dish in tank (NOT under the basking light - roaches will overheat!)
6. Let your beardie hunt throughout the day
7. Remove any uneaten roaches at night before bed

💡 Tip: You can add greens to the same dish - roaches will eat them too!

⚠️ Remember: Roaches should be NO bigger than the space between the eyes!
""",
            LifeStage.SUB_ADULT: """
**Feeding Sub-Adult Bearded Dragon - Insects**

📋 What you need:
• 5-7 medium Dubia roaches (1/2 inch) OR 3-5 large roaches (3/4 inch)
• Calcium powder
• Escape-proof feeding dish

🥬 Diet balance: 60% veggies, 40% protein (bugs)

📝 Steps:
1. Put the roaches in a bag or container
2. Add a pinch of calcium powder
3. Shake gently so roaches get a light white coating
4. Put the dusted roaches in the feeding dish
5. Place dish in tank (NOT under the basking light!)
6. Let your beardie hunt throughout the day
7. Remove any uneaten roaches at night before bed

💡 Tip: Add greens to the same dish!
""",
            LifeStage.ADULT: """
**Feeding Adult Bearded Dragon - Insects**

📋 What you need:
• 3-5 adult Dubia roaches (1 inch size)
• Calcium powder
• Escape-proof feeding dish

📊 Daily amount: 3-5 large roaches (or skip a day - adults don't need bugs daily!)

📝 Steps:
1. Put the roaches in a bag or container
2. Add a small pinch of calcium powder
3. Shake gently so roaches get a light white coating
4. Put the dusted roaches in the feeding dish
5. Place dish in tank (NOT under the basking light!)
6. Let your beardie hunt throughout the day
7. Remove any uneaten roaches at night before bed

💡 Tip: Adults need mostly veggies (80%) with only some bugs (20%)!
""",
        },
        "greens": {
            LifeStage.BABY: """
**Feeding Baby Bearded Dragon - Greens**

📋 What you need:
• Fresh greens: collard greens, dandelion greens, or mustard greens
• Clean food dish
• Cutting board and knife (ask an adult to help chop)

📝 Steps:
1. Wash the greens under water
2. Chop into tiny pieces (easier for babies to eat)
3. Put a small handful in the food dish
4. Place dish in the tank
5. Remove uneaten greens at the end of the day

🥬 Best greens: Collard greens, dandelion greens, mustard greens
🚫 DON'T feed: Spinach, lettuce, or avocado (these are bad for beardies!)

💡 Babies may not eat much greens - that's okay! Keep offering them.
""",
            LifeStage.JUVENILE: """
**Feeding Juvenile Bearded Dragon - Greens**

📋 What you need:
• Fresh greens: collard greens, dandelion greens, or mustard greens
• Clean food dish

📊 Diet balance by age:
• 4-5 months: 10% veggies, 90% protein (bugs)
• 6-9 months: 20% veggies, 80% protein
• 10-11 months: 30% veggies, 70% protein

📝 Steps:
1. Wash the greens under water
2. Tear or chop into small bite-sized pieces
3. Make a salad about the size of your beardie's head
4. Place in the food dish in the tank EVERY MORNING
5. Remove uneaten greens at the end of the day

🥬 Best greens: Collard greens, dandelion greens, mustard greens, butternut squash
🚫 DON'T feed: Spinach (blocks calcium!), lettuce (no nutrition), avocado (toxic!)
""",
            LifeStage.SUB_ADULT: """
**Feeding Sub-Adult Bearded Dragon - Greens**

📋 What you need:
• Fresh greens: collard greens, dandelion greens, or mustard greens
• Clean food dish

📝 Steps:
1. Wash the greens under cold water
2. Tear or chop into bite-sized pieces
3. Make a salad about the size of your beardie's head
4. You can add some butternut squash, bell pepper, or blueberries as treats!
5. Place in the food dish
6. Remove uneaten food at the end of the day

🥬 Good greens: Collard greens, dandelion greens, mustard greens
🍓 Treats (sometimes): Blueberries, strawberries, butternut squash
🚫 AVOID: Spinach, lettuce, avocado, citrus fruits
""",
            LifeStage.ADULT: """
**Feeding Adult Bearded Dragon - Greens**

📋 What you need:
• Fresh greens: collard greens, dandelion greens, or mustard greens
• Clean food dish

📝 Steps:
1. Wash the greens under cold water
2. Tear or chop into bite-sized pieces
3. Make a salad about the size of your beardie's head
4. You can mix in some butternut squash, bell pepper, or a few blueberries!
5. Place in the food dish
6. Remove uneaten food at the end of the day

🥬 Best greens (feed daily):
• Collard greens ⭐
• Dandelion greens ⭐
• Mustard greens
• Turnip greens

🍓 Occasional treats:
• Blueberries, strawberries (1-2 pieces)
• Butternut squash
• Bell peppers

🚫 NEVER feed:
• Spinach (blocks calcium absorption!)
• Iceberg lettuce (no nutrition)
• Avocado (toxic!)
• Citrus fruits (too acidic)

💡 Adults need 80% greens, only 20% insects!
""",
        },
    },
    "water": {
        "default": """
**Changing Water**

📋 What you need:
• Fresh filtered or bottled water (room temperature)
• Clean paper towels
• Reptile water conditioner

📝 Steps:
1. Remove the water dish from the tank
2. Dump out the old water in the sink
3. Rinse the dish with warm water
4. Wipe it clean with a paper towel
5. Fill with fresh filtered or bottled water
6. Add ONE drop of reptile water conditioner
7. Put back in the tank (away from the heat lamp!)

💡 Tips:
• Change water every day - beardies can poop in it!
• Use room temperature water, not cold
• Don't put the dish directly under the basking light

⚠️ Note: Beardies don't drink much from dishes - they get most water from their food!
""",
    },
    "cleaning": {
        "spot_clean": """
**Daily Spot Cleaning** ☀️ Do this FIRST thing every morning!

📋 What you need:
• Paper towels
• Small trash bag

📝 Steps:
1. **FIRST: Remove yesterday's uneaten food** - throw away old greens and any dead insects
2. Check the water dish - dump and refill if it looks dirty
3. Wipe up any wet spots with a paper towel
4. Throw away the dirty paper towels

⏰ Do this BEFORE feeding breakfast - start with a clean tank!

💡 Tip: Poop gets cleaned during the weekly deep clean!
""",
        "deep_clean": """
**Weekly Deep Clean** 🧹 The big clean!

📋 What you need:
• Paper towels
• Reptile-safe cleaner (or 1 part vinegar + 2 parts water)
• Clean cloth
• Temporary container for your beardie
• Small trash bag

📝 Steps:
1. **FIRST: Find and remove ALL poop** - look for brownish droppings with white part (urate)
   👀 Check: under basking spot, near food dish, in corners, on decorations
2. Safely move your beardie to a temporary container
3. Remove all decorations, food dish, and water dish
4. Remove loose substrate or liner
5. Spray the tank walls and floor with reptile-safe cleaner
6. Wipe everything down with paper towels
7. Clean all decorations with the cleaner and rinse well
8. Let everything dry completely
9. Put clean substrate/liner back
10. Return decorations, dishes, and your beardie!

⏱️ This takes about 20-30 minutes

⚠️ Important: Make sure everything is completely dry before putting your beardie back!
""",
    },
    "dusting": {
        "calcium": """
**Calcium Dusting**

📋 What you need:
• Calcium powder (WITHOUT D3 if your beardie has UVB light, WITH D3 if no UVB)
• Small container or plastic bag
• Feeder insects

📝 Steps:
1. Put insects in a small plastic bag or container
2. Add a tiny pinch of calcium powder
3. Shake gently until insects have a light white coating
4. Feed the dusted insects to your beardie right away!

💡 How much: Just a light coating - like a dusting of powdered sugar!
⏰ How often: Every feeding for adults (3x per week is fine too)

⚠️ Don't use too much - excess calcium can cause problems!
""",
        "multivitamin": """
**Multivitamin Dusting**

📋 What you need:
• Reptile multivitamin powder
• Small container or plastic bag
• Feeder insects

📝 Steps:
1. Put insects in a small plastic bag or container
2. Add a tiny pinch of multivitamin powder
3. Shake gently until insects have a light coating
4. Feed the dusted insects to your beardie!

⏰ How often: 2 times per week (like Tuesday and Saturday)

💡 Tip: On vitamin days, use multivitamin instead of calcium, not both at once!
""",
    },
}


def _detect_task_subtype(task_name: str, task_type: CareTaskType) -> str:
    """Detect the task subtype from the task name."""
    name_lower = task_name.lower()

    if task_type == CareTaskType.FEEDING:
        if any(word in name_lower for word in ["roach", "dubia", "cricket", "insect", "bug", "protein"]):
            return "insects"
        elif any(word in name_lower for word in ["green", "salad", "vegetable", "veggie", "leaf"]):
            return "greens"
        else:
            return "insects"  # Default for feeding

    elif task_type == CareTaskType.CLEANING:
        if any(word in name_lower for word in ["deep", "weekly", "full", "thorough"]):
            return "deep_clean"
        else:
            return "spot_clean"

    elif task_type == CareTaskType.WATER:
        return "default"

    return "default"


def get_feeding_instructions(
    species: str,
    life_stage: LifeStage,
    task_subtype: str = "insects"
) -> str:
    """Get feeding instructions for a specific species and life stage."""
    if species == PetSpecies.BEARDED_DRAGON or species == "bearded_dragon":
        instructions = BEARDED_DRAGON_INSTRUCTIONS.get("feeding", {})
        subtype_instructions = instructions.get(task_subtype, instructions.get("insects", {}))

        if isinstance(subtype_instructions, dict):
            # Get instructions for the specific life stage, or default to adult
            return subtype_instructions.get(
                life_stage,
                subtype_instructions.get(LifeStage.ADULT, "Follow standard feeding guidelines for your pet.")
            ).strip()

    return "Follow the standard feeding guidelines for your pet type. Consult a vet or care guide for specific instructions."


def get_water_instructions(
    species: str,
    life_stage: LifeStage
) -> str:
    """Get water change instructions for a specific species."""
    if species == PetSpecies.BEARDED_DRAGON or species == "bearded_dragon":
        instructions = BEARDED_DRAGON_INSTRUCTIONS.get("water", {})
        return instructions.get("default", "Change water daily with fresh, clean water.").strip()

    return "Change water daily with fresh, clean water. Clean the water dish regularly."


def get_cleaning_instructions(
    species: str,
    life_stage: LifeStage,
    task_subtype: str = "spot_clean"
) -> str:
    """Get cleaning instructions for a specific species."""
    if species == PetSpecies.BEARDED_DRAGON or species == "bearded_dragon":
        instructions = BEARDED_DRAGON_INSTRUCTIONS.get("cleaning", {})
        return instructions.get(task_subtype, instructions.get("spot_clean", "Clean the habitat regularly.")).strip()

    return "Clean the habitat regularly to maintain a healthy environment."


def get_dusting_instructions(
    species: str,
    life_stage: LifeStage,
    task_subtype: str = "calcium"
) -> str:
    """Get supplement dusting instructions."""
    if species == PetSpecies.BEARDED_DRAGON or species == "bearded_dragon":
        instructions = BEARDED_DRAGON_INSTRUCTIONS.get("dusting", {})
        return instructions.get(task_subtype, instructions.get("calcium", "Dust insects with calcium powder.")).strip()

    return "Follow supplement guidelines for your pet type."


def get_task_description(
    task_type: CareTaskType,
    species: str,
    life_stage: LifeStage,
    task_name: str
) -> str:
    """
    Generate a detailed, kid-friendly task description.

    Args:
        task_type: The type of care task (feeding, water, cleaning, etc.)
        species: The pet species
        life_stage: The pet's current life stage
        task_name: The name of the task (used to detect subtypes)

    Returns:
        A detailed, step-by-step instruction string
    """
    # Detect subtype from task name
    subtype = _detect_task_subtype(task_name, task_type)

    if task_type == CareTaskType.FEEDING:
        return get_feeding_instructions(species, life_stage, subtype)

    elif task_type == CareTaskType.WATER:
        return get_water_instructions(species, life_stage)

    elif task_type == CareTaskType.CLEANING:
        return get_cleaning_instructions(species, life_stage, subtype)

    # For other task types, return generic instructions
    return f"Complete the {task_name} task following standard care guidelines for your pet."


def get_recommended_schedules(species: str, life_stage: LifeStage) -> list[dict]:
    """
    Get recommended care schedules for a species/life stage.

    Returns a list of recommended tasks with their frequencies and descriptions.
    """
    if species == PetSpecies.BEARDED_DRAGON or species == "bearded_dragon":
        schedules = [
            {
                "task_name": "Feed Dubia Roaches",
                "task_type": CareTaskType.FEEDING,
                "frequency": "daily",
                "points_value": 10,
                "description": get_feeding_instructions(species, life_stage, "insects"),
            },
            {
                "task_name": "Feed Fresh Greens",
                "task_type": CareTaskType.FEEDING,
                "frequency": "daily",
                "points_value": 5,
                "description": get_feeding_instructions(species, life_stage, "greens"),
            },
            {
                "task_name": "Calcium Dusting",
                "task_type": CareTaskType.FEEDING,
                "frequency": "daily",
                "points_value": 3,
                "description": get_dusting_instructions(species, life_stage, "calcium"),
            },
            {
                "task_name": "Multivitamin Dusting",
                "task_type": CareTaskType.FEEDING,
                "frequency": "weekly",
                "points_value": 5,
                "description": get_dusting_instructions(species, life_stage, "multivitamin"),
            },
            {
                "task_name": "Change Water",
                "task_type": CareTaskType.WATER,
                "frequency": "daily",
                "points_value": 5,
                "description": get_water_instructions(species, life_stage),
            },
            {
                "task_name": "Daily Spot Clean",
                "task_type": CareTaskType.CLEANING,
                "frequency": "daily",
                "points_value": 5,
                "description": get_cleaning_instructions(species, life_stage, "spot_clean"),
            },
            {
                "task_name": "Weekly Deep Clean",
                "task_type": CareTaskType.CLEANING,
                "frequency": "weekly",
                "points_value": 25,
                "description": get_cleaning_instructions(species, life_stage, "deep_clean"),
            },
        ]
        return schedules

    return []
