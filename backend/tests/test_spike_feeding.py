"""
Unit tests for Spike feeding auto-schedule and auto-approval.
Following TDD: Write these tests FIRST, then implement to make them pass.
"""

import os
from datetime import datetime, timedelta

import pytest

from models import PetCareTaskStatus
from pet_care import generate_spike_feeding_tasks, get_spike_feeding_assigned_kid


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
        """Verify simple 3-person rotation repeats correctly over 14 days"""
        start_thursday = datetime(2026, 1, 29)
        expected = [
            "aiden",
            "clara",
            "emery",
            "aiden",
            "clara",
            "emery",
            "aiden",
            "clara",
            "emery",
            "aiden",
            "clara",
            "emery",
            "aiden",
            "clara",
        ]

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
            pet_id="spike-pet-id", pet_name="Spike", parent_id="parent-id", days_ahead=7, start_date=start
        )

        assert len(tasks) == 7

        # Check assignments match pattern
        expected_kids = ["aiden", "clara", "emery", "aiden", "clara", "emery", "aiden"]
        for i, task in enumerate(tasks):
            assert task.assigned_to_kid_id == expected_kids[i]
            assert task.assigned_to_kid_username == expected_kids[i]
            assert task.task_name == "Feed Spike"
            assert task.pet_name == "Spike"
            # Note: PetCareTaskCreate doesn't have status - it's added when creating PetCareTask

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
            existing_task_dates=existing_dates,
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
            pet_id="spike-pet-id", pet_name="Spike", parent_id="parent-id", days_ahead=1, start_date=start
        )

        assert len(tasks) == 1
        assert tasks[0].due_date.hour == 18
        assert tasks[0].due_date.minute == 0
