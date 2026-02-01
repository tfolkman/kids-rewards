"""
Integration tests for Spike feeding auto-approval.
Tests the full workflow with mocked CRUD layer.
"""

import os
from datetime import datetime
from unittest.mock import patch

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
        hashed_password="hashed",
        role="kid",
        points=100,
        is_active=True,
        created_at=datetime.utcnow(),
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
        created_at=datetime.utcnow(),
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
        created_at=datetime.utcnow(),
    )


class TestSpikeAutoApproval:
    """Test auto-approval when kids submit Spike feeding tasks"""

    @patch("crud.submit_pet_care_task")
    def test_feed_spike_auto_approves(self, mock_submit, client, mock_aiden, mock_spike_feeding_task):
        """
        CRITICAL TEST: Feeding Spike should auto-approve and award points.
        This is the main feature we're implementing.
        """
        # Setup: Mock the CRUD function to return approved task
        approved_task = mock_spike_feeding_task.model_copy()
        approved_task.status = models.PetCareTaskStatus.APPROVED
        approved_task.submitted_at = datetime.utcnow()
        approved_task.reviewed_at = datetime.utcnow()
        mock_submit.return_value = approved_task

        # Override FastAPI dependency for authentication
        from main import get_current_kid_user

        main.app.dependency_overrides[get_current_kid_user] = lambda: mock_aiden

        try:
            # Act: Kid submits the task
            response = client.post("/pets/tasks/task-123/submit", json={"notes": "Fed Spike his crickets"})

            # Assert: Response shows APPROVED (not PENDING_APPROVAL)
            assert response.status_code == 202
            task_data = response.json()
            assert task_data["status"] == "approved"
            assert task_data["submitted_at"] is not None
            assert task_data["reviewed_at"] is not None

            # Verify CRUD function was called correctly
            mock_submit.assert_called_once()
            call_args = mock_submit.call_args
            assert call_args[1]["task_id"] == "task-123"
            assert call_args[1]["kid_user"].username == "aiden"
        finally:
            # Clean up dependency overrides
            main.app.dependency_overrides.clear()

    @patch("crud.submit_pet_care_task")
    def test_other_tasks_still_need_approval(self, mock_submit, client, mock_aiden, mock_tank_cleaning_task):
        """
        Non-feeding tasks should still require parent approval.
        This ensures we don't break existing functionality.
        """
        # Setup: Mock CRUD to return PENDING_APPROVAL for non-feeding task
        pending_task = mock_tank_cleaning_task.model_copy()
        pending_task.status = models.PetCareTaskStatus.PENDING_APPROVAL
        pending_task.submitted_at = datetime.utcnow()
        mock_submit.return_value = pending_task

        # Override FastAPI dependency
        from main import get_current_kid_user

        main.app.dependency_overrides[get_current_kid_user] = lambda: mock_aiden

        try:
            response = client.post("/pets/tasks/task-456/submit", json={"notes": "Cleaned the tank"})

            # Assert: Status is PENDING_APPROVAL (not auto-approved)
            assert response.status_code == 202
            task_data = response.json()
            assert task_data["status"] == "pending_approval"
            assert task_data["reviewed_at"] is None  # Not reviewed yet
        finally:
            main.app.dependency_overrides.clear()
