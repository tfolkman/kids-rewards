"""
Tests for the Pet Care module.

Tests cover:
- Age calculation from birthday
- Life stage determination based on age
- Care recommendations for each life stage
- Weight evaluation
- Task generation for schedules
"""

from datetime import datetime, timedelta

import pytest

from models import (
    BeardedDragonLifeStage,
    CareFrequency,
    Pet,
    PetCareSchedule,
    PetSpecies,
    WeightStatus,
)
from pet_care import (
    calculate_age_months,
    calculate_life_stage,
    evaluate_weight,
    generate_tasks_for_schedule,
    get_care_recommendations,
    get_next_assigned_kid,
    get_pet_with_age,
)


class TestAgeCalculation:
    def test_calculate_age_months_same_month(self):
        now = datetime(2025, 6, 15)
        birthday = datetime(2025, 6, 1)
        assert calculate_age_months(birthday, now) == 0

    def test_calculate_age_months_one_month(self):
        now = datetime(2025, 7, 15)
        birthday = datetime(2025, 6, 15)
        assert calculate_age_months(birthday, now) == 1

    def test_calculate_age_months_day_not_reached(self):
        now = datetime(2025, 7, 10)
        birthday = datetime(2025, 6, 15)
        assert calculate_age_months(birthday, now) == 0

    def test_calculate_age_months_multiple_months(self):
        now = datetime(2025, 12, 15)
        birthday = datetime(2025, 2, 15)
        assert calculate_age_months(birthday, now) == 10

    def test_calculate_age_months_cross_year(self):
        now = datetime(2026, 3, 15)
        birthday = datetime(2025, 2, 15)
        assert calculate_age_months(birthday, now) == 13

    def test_calculate_age_months_spike_born_feb_2025(self):
        birthday = datetime(2025, 2, 1)
        check_date = datetime(2025, 11, 1)
        assert calculate_age_months(birthday, check_date) == 9

    def test_calculate_age_months_negative_returns_zero(self):
        now = datetime(2025, 1, 15)
        birthday = datetime(2025, 6, 15)
        assert calculate_age_months(birthday, now) == 0


class TestLifeStageCalculation:
    def test_baby_stage_zero_months(self):
        assert calculate_life_stage(PetSpecies.BEARDED_DRAGON, 0) == BeardedDragonLifeStage.BABY

    def test_baby_stage_two_months(self):
        assert calculate_life_stage(PetSpecies.BEARDED_DRAGON, 2) == BeardedDragonLifeStage.BABY

    def test_juvenile_stage_three_months(self):
        assert calculate_life_stage(PetSpecies.BEARDED_DRAGON, 3) == BeardedDragonLifeStage.JUVENILE

    def test_juvenile_stage_eleven_months(self):
        assert calculate_life_stage(PetSpecies.BEARDED_DRAGON, 11) == BeardedDragonLifeStage.JUVENILE

    def test_sub_adult_stage_twelve_months(self):
        assert calculate_life_stage(PetSpecies.BEARDED_DRAGON, 12) == BeardedDragonLifeStage.SUB_ADULT

    def test_sub_adult_stage_seventeen_months(self):
        assert calculate_life_stage(PetSpecies.BEARDED_DRAGON, 17) == BeardedDragonLifeStage.SUB_ADULT

    def test_adult_stage_eighteen_months(self):
        assert calculate_life_stage(PetSpecies.BEARDED_DRAGON, 18) == BeardedDragonLifeStage.ADULT

    def test_adult_stage_three_years(self):
        assert calculate_life_stage(PetSpecies.BEARDED_DRAGON, 36) == BeardedDragonLifeStage.ADULT

    def test_spike_at_nine_months_is_juvenile(self):
        assert calculate_life_stage(PetSpecies.BEARDED_DRAGON, 9) == BeardedDragonLifeStage.JUVENILE


class TestCareRecommendations:
    def test_baby_care_recommendations(self):
        rec = get_care_recommendations(PetSpecies.BEARDED_DRAGON, BeardedDragonLifeStage.BABY)
        assert rec.life_stage == BeardedDragonLifeStage.BABY
        assert "5x daily" in rec.feeding_frequency
        assert "80%" in rec.diet_ratio
        assert rec.healthy_weight_range_grams == (10, 50)
        assert len(rec.care_tips) > 0

    def test_juvenile_care_recommendations(self):
        rec = get_care_recommendations(PetSpecies.BEARDED_DRAGON, BeardedDragonLifeStage.JUVENILE)
        assert rec.life_stage == BeardedDragonLifeStage.JUVENILE
        assert "2-3x daily" in rec.feeding_frequency
        assert rec.healthy_weight_range_grams == (50, 200)

    def test_sub_adult_care_recommendations(self):
        rec = get_care_recommendations(PetSpecies.BEARDED_DRAGON, BeardedDragonLifeStage.SUB_ADULT)
        assert rec.life_stage == BeardedDragonLifeStage.SUB_ADULT
        assert rec.healthy_weight_range_grams == (200, 400)

    def test_adult_care_recommendations(self):
        rec = get_care_recommendations(PetSpecies.BEARDED_DRAGON, BeardedDragonLifeStage.ADULT)
        assert rec.life_stage == BeardedDragonLifeStage.ADULT
        assert "2-3x per week" in rec.feeding_frequency
        assert rec.healthy_weight_range_grams == (380, 500)


class TestWeightEvaluation:
    def test_baby_healthy_weight(self):
        status = evaluate_weight(PetSpecies.BEARDED_DRAGON, BeardedDragonLifeStage.BABY, 30)
        assert status == WeightStatus.HEALTHY

    def test_baby_underweight(self):
        status = evaluate_weight(PetSpecies.BEARDED_DRAGON, BeardedDragonLifeStage.BABY, 5)
        assert status == WeightStatus.UNDERWEIGHT

    def test_baby_overweight(self):
        status = evaluate_weight(PetSpecies.BEARDED_DRAGON, BeardedDragonLifeStage.BABY, 60)
        assert status == WeightStatus.OVERWEIGHT

    def test_juvenile_healthy_weight(self):
        status = evaluate_weight(PetSpecies.BEARDED_DRAGON, BeardedDragonLifeStage.JUVENILE, 120)
        assert status == WeightStatus.HEALTHY

    def test_adult_healthy_weight(self):
        status = evaluate_weight(PetSpecies.BEARDED_DRAGON, BeardedDragonLifeStage.ADULT, 450)
        assert status == WeightStatus.HEALTHY

    def test_adult_underweight(self):
        status = evaluate_weight(PetSpecies.BEARDED_DRAGON, BeardedDragonLifeStage.ADULT, 300)
        assert status == WeightStatus.UNDERWEIGHT


class TestPetWithAge:
    def test_get_pet_with_age_adds_age_and_stage(self):
        pet = Pet(
            id="pet-123",
            parent_id="parent-456",
            name="Spike",
            species=PetSpecies.BEARDED_DRAGON,
            birthday=datetime(2025, 2, 1),
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        pet_with_age = get_pet_with_age(pet)

        assert pet_with_age.id == "pet-123"
        assert pet_with_age.name == "Spike"
        assert pet_with_age.age_months >= 0
        assert pet_with_age.life_stage in BeardedDragonLifeStage


class TestKidRotation:
    def test_get_next_assigned_kid_first_call(self):
        schedule = PetCareSchedule(
            id="schedule-1",
            pet_id="pet-1",
            parent_id="parent-1",
            task_name="Feed Spike",
            frequency=CareFrequency.DAILY,
            points_value=10,
            assigned_kid_ids=["kid-1", "kid-2", "kid-3"],
            rotation_index=0,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        kid_id, new_index = get_next_assigned_kid(schedule)
        assert kid_id == "kid-1"
        assert new_index == 1

    def test_get_next_assigned_kid_wraps_around(self):
        schedule = PetCareSchedule(
            id="schedule-1",
            pet_id="pet-1",
            parent_id="parent-1",
            task_name="Feed Spike",
            frequency=CareFrequency.DAILY,
            points_value=10,
            assigned_kid_ids=["kid-1", "kid-2"],
            rotation_index=1,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        kid_id, new_index = get_next_assigned_kid(schedule)
        assert kid_id == "kid-2"
        assert new_index == 0

    def test_get_next_assigned_kid_empty_list_raises(self):
        schedule = PetCareSchedule(
            id="schedule-1",
            pet_id="pet-1",
            parent_id="parent-1",
            task_name="Feed Spike",
            frequency=CareFrequency.DAILY,
            points_value=10,
            assigned_kid_ids=[],
            rotation_index=0,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        with pytest.raises(ValueError, match="No kids assigned"):
            get_next_assigned_kid(schedule)


class TestTaskGeneration:
    def test_generate_daily_tasks_for_week(self):
        pet = Pet(
            id="pet-1",
            parent_id="parent-1",
            name="Spike",
            species=PetSpecies.BEARDED_DRAGON,
            birthday=datetime(2025, 2, 1),
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        schedule = PetCareSchedule(
            id="schedule-1",
            pet_id="pet-1",
            parent_id="parent-1",
            task_name="Feed Spike",
            frequency=CareFrequency.DAILY,
            points_value=10,
            assigned_kid_ids=["kid-1", "kid-2"],
            rotation_index=0,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        kid_usernames = {"kid-1": "Alice", "kid-2": "Bob"}

        tasks = generate_tasks_for_schedule(schedule, pet, kid_usernames, days_ahead=7)

        assert len(tasks) == 7
        assert tasks[0].assigned_to_kid_id == "kid-1"
        assert tasks[0].assigned_to_kid_username == "Alice"
        assert tasks[1].assigned_to_kid_id == "kid-2"
        assert tasks[1].assigned_to_kid_username == "Bob"
        assert tasks[2].assigned_to_kid_id == "kid-1"

    def test_generate_weekly_tasks(self):
        pet = Pet(
            id="pet-1",
            parent_id="parent-1",
            name="Spike",
            species=PetSpecies.BEARDED_DRAGON,
            birthday=datetime(2025, 2, 1),
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        schedule = PetCareSchedule(
            id="schedule-1",
            pet_id="pet-1",
            parent_id="parent-1",
            task_name="Clean Tank",
            frequency=CareFrequency.WEEKLY,
            day_of_week=0,
            points_value=25,
            assigned_kid_ids=["kid-1"],
            rotation_index=0,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        kid_usernames = {"kid-1": "Alice"}

        tasks = generate_tasks_for_schedule(schedule, pet, kid_usernames, days_ahead=14)

        assert len(tasks) <= 2
        for task in tasks:
            assert task.task_name == "Clean Tank"
            assert task.points_value == 25

    def test_generate_tasks_skips_existing_dates(self):
        pet = Pet(
            id="pet-1",
            parent_id="parent-1",
            name="Spike",
            species=PetSpecies.BEARDED_DRAGON,
            birthday=datetime(2025, 2, 1),
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        schedule = PetCareSchedule(
            id="schedule-1",
            pet_id="pet-1",
            parent_id="parent-1",
            task_name="Feed Spike",
            frequency=CareFrequency.DAILY,
            points_value=10,
            assigned_kid_ids=["kid-1"],
            rotation_index=0,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        kid_usernames = {"kid-1": "Alice"}
        today = datetime.utcnow().date()
        existing_dates = {today.isoformat(), (today + timedelta(days=1)).isoformat()}

        tasks = generate_tasks_for_schedule(
            schedule, pet, kid_usernames, days_ahead=7, existing_task_dates=existing_dates
        )

        assert len(tasks) == 5
