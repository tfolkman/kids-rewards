"""
Pet Care Module - Age-adaptive care logic for bearded dragons and other pets.

This module provides:
- Age and life stage calculation
- Age-appropriate care recommendations
- Weight evaluation against healthy ranges
- Task generation for care schedules
"""

from datetime import datetime, timedelta, time
from typing import Optional

import models


BEARDED_DRAGON_CARE = {
    models.BeardedDragonLifeStage.BABY: {
        "feeding_frequency": "5x daily",
        "diet_ratio": "80% insects / 20% vegetables",
        "healthy_weight_range_grams": (10, 50),
        "care_tips": [
            "Feed small insects 5 times daily",
            "Mist enclosure 2-3 times daily for hydration",
            "Maintain basking spot at 100-110°F",
            "Handle gently and briefly to build trust",
        ],
    },
    models.BeardedDragonLifeStage.JUVENILE: {
        "feeding_frequency": "2-3x daily",
        "diet_ratio": "60% insects / 40% vegetables",
        "healthy_weight_range_grams": (50, 200),
        "care_tips": [
            "Gradually introduce more vegetables",
            "Feed appropriately-sized insects",
            "Weekly tank spot cleaning",
            "Regular handling to socialize",
        ],
    },
    models.BeardedDragonLifeStage.SUB_ADULT: {
        "feeding_frequency": "1-2x daily insects, daily vegetables",
        "diet_ratio": "40% insects / 60% vegetables",
        "healthy_weight_range_grams": (200, 400),
        "care_tips": [
            "Daily fresh vegetables",
            "Insects 1-2 times per day",
            "Deep clean tank weekly",
            "Check UVB bulb efficiency",
        ],
    },
    models.BeardedDragonLifeStage.ADULT: {
        "feeding_frequency": "Insects 2-3x per week, daily vegetables",
        "diet_ratio": "20% insects / 80% vegetables",
        "healthy_weight_range_grams": (380, 500),
        "care_tips": [
            "Daily salad with variety of vegetables",
            "Insects as treats 2-3 times per week",
            "Regular weight monitoring",
            "Annual vet checkup recommended",
        ],
    },
}


def calculate_age_months(birthday: datetime, reference_date: Optional[datetime] = None) -> int:
    """
    Calculate age in months from birthday to reference date.

    Args:
        birthday: The pet's birthday
        reference_date: The date to calculate age from (defaults to now)

    Returns:
        Age in months (integer)
    """
    if reference_date is None:
        reference_date = datetime.utcnow()

    # Handle timezone-aware datetimes
    if birthday.tzinfo is not None and reference_date.tzinfo is None:
        reference_date = reference_date.replace(tzinfo=birthday.tzinfo)
    elif birthday.tzinfo is None and reference_date.tzinfo is not None:
        birthday = birthday.replace(tzinfo=reference_date.tzinfo)

    # Calculate months difference
    months = (reference_date.year - birthday.year) * 12 + (reference_date.month - birthday.month)

    # Adjust if the day hasn't been reached yet this month
    if reference_date.day < birthday.day:
        months -= 1

    return max(0, months)


def calculate_life_stage(
    species: models.PetSpecies, age_months: int
) -> models.BeardedDragonLifeStage:
    """
    Calculate life stage based on species and age.

    For bearded dragons:
    - Baby: 0-3 months
    - Juvenile: 3-12 months
    - Sub-adult: 12-17 months
    - Adult: 18+ months

    Args:
        species: The pet species
        age_months: Age in months

    Returns:
        The appropriate life stage enum
    """
    if species == models.PetSpecies.BEARDED_DRAGON:
        if age_months < 3:
            return models.BeardedDragonLifeStage.BABY
        elif age_months < 12:
            return models.BeardedDragonLifeStage.JUVENILE
        elif age_months < 18:
            return models.BeardedDragonLifeStage.SUB_ADULT
        else:
            return models.BeardedDragonLifeStage.ADULT

    # Default to adult for unknown species
    return models.BeardedDragonLifeStage.ADULT


def get_care_recommendations(
    species: models.PetSpecies, life_stage: models.BeardedDragonLifeStage
) -> models.CareRecommendation:
    """
    Get age-appropriate care recommendations for a pet.

    Args:
        species: The pet species
        life_stage: The pet's current life stage

    Returns:
        CareRecommendation with feeding, diet, weight, and tips
    """
    if species == models.PetSpecies.BEARDED_DRAGON:
        care_data = BEARDED_DRAGON_CARE.get(life_stage, BEARDED_DRAGON_CARE[models.BeardedDragonLifeStage.ADULT])
        return models.CareRecommendation(
            life_stage=life_stage,
            feeding_frequency=care_data["feeding_frequency"],
            diet_ratio=care_data["diet_ratio"],
            healthy_weight_range_grams=care_data["healthy_weight_range_grams"],
            care_tips=care_data["care_tips"],
        )

    # Default recommendations for unknown species
    return models.CareRecommendation(
        life_stage=life_stage,
        feeding_frequency="Consult a veterinarian",
        diet_ratio="Species-appropriate diet",
        healthy_weight_range_grams=(0, 0),
        care_tips=["Research specific care requirements for this species"],
    )


def evaluate_weight(
    species: models.PetSpecies,
    life_stage: models.BeardedDragonLifeStage,
    weight_grams: int,
) -> models.WeightStatus:
    """
    Evaluate if a pet's weight is healthy for their life stage.

    Args:
        species: The pet species
        life_stage: The pet's current life stage
        weight_grams: Current weight in grams

    Returns:
        WeightStatus indicating healthy, underweight, or overweight
    """
    if species == models.PetSpecies.BEARDED_DRAGON:
        care_data = BEARDED_DRAGON_CARE.get(life_stage, BEARDED_DRAGON_CARE[models.BeardedDragonLifeStage.ADULT])
        min_weight, max_weight = care_data["healthy_weight_range_grams"]

        if weight_grams < min_weight:
            return models.WeightStatus.UNDERWEIGHT
        elif weight_grams > max_weight:
            return models.WeightStatus.OVERWEIGHT
        else:
            return models.WeightStatus.HEALTHY

    # Default to healthy for unknown species
    return models.WeightStatus.HEALTHY


def get_pet_with_age(pet: models.Pet) -> models.PetWithAge:
    """
    Enhance a Pet model with calculated age and life stage.

    Args:
        pet: The base Pet model

    Returns:
        PetWithAge model with age_months and life_stage
    """
    age_months = calculate_age_months(pet.birthday)
    life_stage = calculate_life_stage(pet.species, age_months)

    return models.PetWithAge(
        **pet.model_dump(),
        age_months=age_months,
        life_stage=life_stage,
    )


def get_next_assigned_kid(
    schedule: models.PetCareSchedule,
) -> tuple[str, int]:
    """
    Get the next kid in rotation for a task assignment.

    Args:
        schedule: The care schedule with rotation info

    Returns:
        Tuple of (kid_id, new_rotation_index)
    """
    if not schedule.assigned_kid_ids:
        raise ValueError("No kids assigned to this schedule")

    current_index = schedule.rotation_index % len(schedule.assigned_kid_ids)
    kid_id = schedule.assigned_kid_ids[current_index]
    new_index = (current_index + 1) % len(schedule.assigned_kid_ids)

    return kid_id, new_index


def generate_tasks_for_schedule(
    schedule: models.PetCareSchedule,
    pet: models.Pet,
    kid_usernames: dict[str, str],
    days_ahead: int = 7,
    existing_task_dates: Optional[set[str]] = None,
) -> list[models.PetCareTaskCreate]:
    """
    Generate task instances for a care schedule.

    Args:
        schedule: The care schedule to generate tasks for
        pet: The pet associated with this schedule
        kid_usernames: Dict mapping kid_id to username
        days_ahead: Number of days to generate tasks for
        existing_task_dates: Set of dates (ISO format) that already have tasks

    Returns:
        List of PetCareTaskCreate objects
    """
    if existing_task_dates is None:
        existing_task_dates = set()

    tasks = []
    today = datetime.utcnow().date()
    rotation_index = schedule.rotation_index

    for day_offset in range(days_ahead):
        task_date = today + timedelta(days=day_offset)
        date_str = task_date.isoformat()

        # Skip if task already exists for this date
        if date_str in existing_task_dates:
            continue

        # Check if this is a valid day for the schedule
        should_create = False

        if schedule.frequency == models.CareFrequency.DAILY:
            should_create = True
        elif schedule.frequency == models.CareFrequency.WEEKLY:
            # Check if it's the right day of the week
            if schedule.day_of_week is not None and task_date.weekday() == schedule.day_of_week:
                should_create = True

        if should_create:
            # Get next kid in rotation
            kid_index = rotation_index % len(schedule.assigned_kid_ids)
            kid_id = schedule.assigned_kid_ids[kid_index]
            kid_username = kid_usernames.get(kid_id, kid_id)

            # Determine due time from schedule or default to end of day
            if schedule.due_by_time:
                try:
                    hours, minutes = map(int, schedule.due_by_time.split(":"))
                    task_time = time(hours, minutes)
                except (ValueError, AttributeError):
                    task_time = time(23, 59)
            else:
                task_time = time(23, 59)

            task = models.PetCareTaskCreate(
                schedule_id=schedule.id,
                pet_id=pet.id,
                pet_name=pet.name,
                task_name=schedule.task_name,
                description=schedule.description,
                points_value=schedule.points_value,
                assigned_to_kid_id=kid_id,
                assigned_to_kid_username=kid_username,
                due_date=datetime.combine(task_date, task_time),
            )
            tasks.append(task)
            rotation_index += 1

    return tasks
