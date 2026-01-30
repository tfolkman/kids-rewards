"""
Tests for daily automated Spike feeding task generation Lambda function.
"""

import os
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

import daily_tasks
import models


@pytest.fixture(autouse=True)
def setup_env():
    """Set required environment variables"""
    os.environ["APP_SECRET_KEY"] = "test-secret-key-for-testing-32-chars"
    os.environ["SPIKE_PARENT_ID"] = "test-parent-id"


@pytest.fixture
def mock_event():
    """Mock CloudWatch Events event"""
    return {"source": "aws.events", "detail-type": "Scheduled Event", "time": "2026-01-30T09:00:00Z"}


@pytest.fixture
def mock_context():
    """Mock Lambda context"""
    context = MagicMock()
    context.function_name = "DailySpikeTaskGeneratorFunction"
    context.request_id = "test-request-123"
    context.invoked_function_arn = "arn:aws:lambda:us-west-2:123456789:function:daily-tasks"
    return context


@pytest.fixture
def mock_parent():
    """Mock parent user"""
    return models.User(
        id="test-parent-id",
        username="testparent",
        hashed_password="hashed",
        role="parent",
        points=0,
        is_active=True,
        created_at=datetime.utcnow(),
    )


@pytest.fixture
def mock_spike():
    """Mock Spike pet"""
    return models.Pet(
        id="spike-pet-123",
        parent_id="test-parent-id",
        name="Spike",
        species=models.PetSpecies.BEARDED_DRAGON,
        birthday=datetime(2025, 2, 1),
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


class TestDailyTaskGeneration:
    """Test the daily automated task generation Lambda handler"""

    @patch("crud.create_pet_care_task")
    @patch("crud.get_tasks_by_pet_id")
    @patch("crud.get_pets_by_parent_id")
    def test_successful_task_generation(
        self, mock_get_pets, mock_get_tasks, mock_create_task, mock_event, mock_context, mock_spike
    ):
        """Test successful daily task generation"""

        # Setup mocks
        mock_get_pets.return_value = [mock_spike]
        mock_get_tasks.return_value = []  # No existing tasks

        # Mock task creation
        def create_task_side_effect(task_create):
            return models.PetCareTask(
                id=f"task-{task_create.due_date.day}",
                **task_create.dict(),
                status=models.PetCareTaskStatus.ASSIGNED,
                created_at=datetime.utcnow(),
            )

        mock_create_task.side_effect = create_task_side_effect

        # Run handler
        result = daily_tasks.lambda_handler(mock_event, mock_context)

        # Assertions
        assert result["statusCode"] == 200
        assert "Daily task generation complete" in result["body"]
        assert result["details"]["tasks_created"] == 7
        assert result["details"]["pet_name"] == "Spike"

        # Verify create was called 7 times (7 days ahead)
        assert mock_create_task.call_count == 7

    @patch("crud.get_pets_by_parent_id")
    def test_spike_not_found(self, mock_get_pets, mock_event, mock_context):
        """Test error when Spike pet doesn't exist"""

        # Setup: No Spike, only other pets
        other_pet = models.Pet(
            id="other-pet-123",
            parent_id="test-parent-id",
            name="Rex",
            species=models.PetSpecies.BEARDED_DRAGON,
            birthday=datetime(2024, 5, 1),
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        mock_get_pets.return_value = [other_pet]

        # Run handler
        result = daily_tasks.lambda_handler(mock_event, mock_context)

        # Assertions
        assert result["statusCode"] == 404
        assert "Spike not found" in result["body"]

    @patch("crud.get_pets_by_parent_id")
    def test_no_pets_found(self, mock_get_pets, mock_event, mock_context):
        """Test error when parent has no pets"""

        mock_get_pets.return_value = []

        result = daily_tasks.lambda_handler(mock_event, mock_context)

        assert result["statusCode"] == 404
        assert "Spike not found" in result["body"]

    @patch("crud.create_pet_care_task")
    @patch("crud.get_tasks_by_pet_id")
    @patch("crud.get_pets_by_parent_id")
    def test_skips_existing_tasks(
        self, mock_get_pets, mock_get_tasks, mock_create_task, mock_event, mock_context, mock_spike
    ):
        """Test that it skips dates that already have feeding tasks"""

        mock_get_pets.return_value = [mock_spike]

        # Mock 3 existing feeding tasks
        today = datetime.utcnow().date()
        existing_tasks = [
            models.PetCareTask(
                id=f"existing-{i}",
                schedule_id="spike-feeding-auto",
                pet_id=mock_spike.id,
                pet_name="Spike",
                task_name="Feed Spike",
                description="Feed Spike",
                points_value=10,
                assigned_to_kid_id="aiden",
                assigned_to_kid_username="aiden",
                due_date=datetime.combine(today + timedelta(days=i), datetime.min.time()),
                status=models.PetCareTaskStatus.ASSIGNED,
                created_at=datetime.utcnow(),
            )
            for i in range(3)
        ]
        mock_get_tasks.return_value = existing_tasks

        def create_task_side_effect(task_create):
            return models.PetCareTask(
                id=f"new-task-{task_create.due_date.day}",
                **task_create.dict(),
                status=models.PetCareTaskStatus.ASSIGNED,
                created_at=datetime.utcnow(),
            )

        mock_create_task.side_effect = create_task_side_effect

        result = daily_tasks.lambda_handler(mock_event, mock_context)

        assert result["statusCode"] == 200
        # Should only create 4 tasks (7 days - 3 existing)
        assert result["details"]["tasks_created"] == 4
        assert result["details"]["existing_tasks"] == 3
        assert mock_create_task.call_count == 4

    def test_missing_parent_id_env_var(self, mock_event, mock_context):
        """Test error when SPIKE_PARENT_ID not set"""

        # Remove env var
        if "SPIKE_PARENT_ID" in os.environ:
            del os.environ["SPIKE_PARENT_ID"]

        result = daily_tasks.lambda_handler(mock_event, mock_context)

        assert result["statusCode"] == 500
        assert "SPIKE_PARENT_ID environment variable not set" in result["body"]

        # Restore for other tests
        os.environ["SPIKE_PARENT_ID"] = "test-parent-id"

    @patch("crud.create_pet_care_task")
    @patch("crud.get_tasks_by_pet_id")
    @patch("crud.get_pets_by_parent_id")
    def test_handles_task_creation_failures(
        self, mock_get_pets, mock_get_tasks, mock_create_task, mock_event, mock_context, mock_spike
    ):
        """Test graceful handling when some task creations fail"""

        mock_get_pets.return_value = [mock_spike]
        mock_get_tasks.return_value = []

        # Mock: first 3 succeed, next 2 fail, last 2 succeed
        call_count = [0]

        def create_task_side_effect(task_create):
            call_count[0] += 1
            if call_count[0] in [4, 5]:  # 4th and 5th calls fail
                return None  # Simulate failure
            return models.PetCareTask(
                id=f"task-{call_count[0]}",
                **task_create.dict(),
                status=models.PetCareTaskStatus.ASSIGNED,
                created_at=datetime.utcnow(),
            )

        mock_create_task.side_effect = create_task_side_effect

        result = daily_tasks.lambda_handler(mock_event, mock_context)

        assert result["statusCode"] == 200
        assert result["details"]["tasks_created"] == 5  # 3 + 2 succeeded
        assert result["details"]["tasks_failed"] == 2  # 2 failed

    @patch("crud.get_pets_by_parent_id")
    def test_case_insensitive_spike_lookup(self, mock_get_pets, mock_event, mock_context):
        """Test that Spike lookup is case-insensitive"""

        # Pet named "SPIKE" (uppercase)
        spike_upper = models.Pet(
            id="spike-pet-upper",
            parent_id="test-parent-id",
            name="SPIKE",  # Uppercase
            species=models.PetSpecies.BEARDED_DRAGON,
            birthday=datetime(2025, 2, 1),
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        mock_get_pets.return_value = [spike_upper]

        # Should find Spike despite case difference
        with patch("crud.get_tasks_by_pet_id") as mock_get_tasks, patch(
            "crud.create_pet_care_task"
        ) as mock_create_task:

            mock_get_tasks.return_value = []

            def create_task_side_effect(task_create):
                return models.PetCareTask(
                    id=f"task-{task_create.due_date.day}",
                    **task_create.dict(),
                    status=models.PetCareTaskStatus.ASSIGNED,
                    created_at=datetime.utcnow(),
                )

            mock_create_task.side_effect = create_task_side_effect

            result = daily_tasks.lambda_handler(mock_event, mock_context)

            assert result["statusCode"] == 200
            assert result["details"]["pet_name"] == "SPIKE"
            assert result["details"]["tasks_created"] == 7
