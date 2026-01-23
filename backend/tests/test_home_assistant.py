"""
Tests for Home Assistant integration endpoint.
Following TDD: Write these tests FIRST, then implement to make them pass.
"""

import os
from datetime import date, datetime, time, timedelta
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

import main
import models


@pytest.fixture
def client():
    """Test client for FastAPI app"""
    return TestClient(main.app)


@pytest.fixture
def valid_api_key():
    """Valid API key for testing"""
    return "test-key-32-characters-minimum!!"


@pytest.fixture(autouse=True)
def setup_env_vars(valid_api_key):
    """Set required environment variables for tests"""
    os.environ["HOME_ASSISTANT_API_KEY"] = valid_api_key
    os.environ["APP_SECRET_KEY"] = "test-secret-key-for-testing-32-chars"
    yield
    # Cleanup not strictly necessary in tests but good practice


class TestHomeAssistantAuth:
    """Test authentication for HA endpoint"""

    def test_endpoint_requires_api_key(self, client):
        """RED: Endpoint should return 401 without API key"""
        response = client.get("/api/home-assistant/pet-tasks/today")
        assert response.status_code == 401
        assert "Missing X-HA-API-Key" in response.json()["detail"]

    def test_endpoint_rejects_invalid_key(self, client):
        """RED: Endpoint should return 403 with invalid API key"""
        response = client.get("/api/home-assistant/pet-tasks/today", headers={"X-HA-API-Key": "wrong-key"})
        assert response.status_code == 403
        assert "Invalid API key" in response.json()["detail"]

    def test_endpoint_accepts_valid_key(self, client, valid_api_key):
        """RED: Endpoint should return 200 with valid API key"""
        response = client.get("/api/home-assistant/pet-tasks/today", headers={"X-HA-API-Key": valid_api_key})
        assert response.status_code == 200


class TestHomeAssistantResponse:
    """Test response structure and data"""

    @patch("crud.get_all_pet_care_tasks")
    def test_response_structure(self, mock_get_tasks, client, valid_api_key):
        """RED: Response should have correct structure"""
        # Mock empty task list
        mock_get_tasks.return_value = []

        response = client.get("/api/home-assistant/pet-tasks/today", headers={"X-HA-API-Key": valid_api_key})

        assert response.status_code == 200
        data = response.json()

        # Check structure
        assert "today" in data
        assert "tasks" in data
        assert "summary" in data

        # Validate date format
        assert data["today"] == date.today().isoformat()

        # Validate summary structure
        assert "total" in data["summary"]
        assert "done" in data["summary"]
        assert "pending" in data["summary"]
        assert "awaiting_approval" in data["summary"]
        assert "overdue" in data["summary"]

    @patch("crud.get_all_pet_care_tasks")
    def test_filters_todays_tasks_only(self, mock_get_tasks, client, valid_api_key):
        """RED: Should only return tasks due today"""
        # Mock tasks from different days
        today_start = datetime.combine(date.today(), time(8, 0))
        yesterday = datetime.combine(date.today(), time(8, 0)) - timedelta(days=1)
        tomorrow = datetime.combine(date.today(), time(8, 0)) + timedelta(days=1)

        mock_tasks = [
            models.PetCareTask(
                id="1",
                schedule_id="s1",
                pet_id="p1",
                pet_name="Spike",
                task_name="Feed",
                assigned_to_kid_id="clara",
                assigned_to_kid_username="Clara",
                points_value=5,
                due_date=today_start,
                status=models.PetCareTaskStatus.ASSIGNED,
                created_at=today_start,
            ),
            models.PetCareTask(
                id="2",
                schedule_id="s1",
                pet_id="p1",
                pet_name="Spike",
                task_name="Feed",
                assigned_to_kid_id="clara",
                assigned_to_kid_username="Clara",
                points_value=5,
                due_date=yesterday,
                status=models.PetCareTaskStatus.APPROVED,
                created_at=yesterday,
            ),
            models.PetCareTask(
                id="3",
                schedule_id="s1",
                pet_id="p1",
                pet_name="Spike",
                task_name="Feed",
                assigned_to_kid_id="emery",
                assigned_to_kid_username="Emery",
                points_value=5,
                due_date=tomorrow,
                status=models.PetCareTaskStatus.ASSIGNED,
                created_at=tomorrow,
            ),
        ]
        mock_get_tasks.return_value = mock_tasks

        response = client.get("/api/home-assistant/pet-tasks/today", headers={"X-HA-API-Key": valid_api_key})

        data = response.json()
        assert len(data["tasks"]) == 1  # Only today's task
        assert data["tasks"][0]["assigned_to"] == "Clara"

    @patch("crud.get_all_pet_care_tasks")
    def test_task_transformation(self, mock_get_tasks, client, valid_api_key):
        """RED: Should transform tasks to HA-friendly format"""
        today_start = datetime.combine(date.today(), time(8, 30))

        mock_task = models.PetCareTask(
            id="1",
            schedule_id="s1",
            pet_id="p1",
            pet_name="Spike",
            task_name="Feed Spike",
            assigned_to_kid_id="clara",
            assigned_to_kid_username="Clara",
            points_value=5,
            due_date=today_start,
            status=models.PetCareTaskStatus.ASSIGNED,
            created_at=today_start,
            description="Morning feeding",
        )
        mock_get_tasks.return_value = [mock_task]

        response = client.get("/api/home-assistant/pet-tasks/today", headers={"X-HA-API-Key": valid_api_key})

        data = response.json()
        task = data["tasks"][0]

        # Validate transformation
        assert task["pet_name"] == "Spike"
        assert task["task_name"] == "Feed Spike"
        assert task["assigned_to"] == "Clara"
        assert task["due_time"] == "08:30"
        assert task["status"] == "pending"  # ASSIGNED -> "pending"
        assert task["points"] == 5
        assert task["is_overdue"] is False

    @patch("crud.get_all_pet_care_tasks")
    def test_status_mapping(self, mock_get_tasks, client, valid_api_key):
        """RED: Should correctly map PetCareTaskStatus to HA status strings"""
        today = datetime.combine(date.today(), time(8, 0))

        # Test all status mappings
        status_map = [
            (models.PetCareTaskStatus.ASSIGNED, "pending"),
            (models.PetCareTaskStatus.PENDING_APPROVAL, "awaiting_approval"),
            (models.PetCareTaskStatus.APPROVED, "done"),
            (models.PetCareTaskStatus.REJECTED, "pending"),  # Rejected shown as pending
        ]

        for db_status, expected_ha_status in status_map:
            mock_task = models.PetCareTask(
                id="1",
                schedule_id="s1",
                pet_id="p1",
                pet_name="Spike",
                task_name="Feed",
                assigned_to_kid_id="clara",
                assigned_to_kid_username="Clara",
                points_value=5,
                due_date=today,
                status=db_status,
                created_at=today,
            )
            mock_get_tasks.return_value = [mock_task]

            response = client.get("/api/home-assistant/pet-tasks/today", headers={"X-HA-API-Key": valid_api_key})

            data = response.json()
            assert data["tasks"][0]["status"] == expected_ha_status

    @patch("crud.get_all_pet_care_tasks")
    def test_overdue_detection(self, mock_get_tasks, client, valid_api_key):
        """RED: Should detect overdue tasks correctly"""
        past_time = datetime.now() - timedelta(hours=2)

        mock_task = models.PetCareTask(
            id="1",
            schedule_id="s1",
            pet_id="p1",
            pet_name="Spike",
            task_name="Feed",
            assigned_to_kid_id="clara",
            assigned_to_kid_username="Clara",
            points_value=5,
            due_date=past_time,
            status=models.PetCareTaskStatus.ASSIGNED,
            created_at=past_time,
        )
        mock_get_tasks.return_value = [mock_task]

        response = client.get("/api/home-assistant/pet-tasks/today", headers={"X-HA-API-Key": valid_api_key})

        data = response.json()
        assert data["tasks"][0]["is_overdue"] is True
        assert data["summary"]["overdue"] == 1

    @patch("crud.get_all_pet_care_tasks")
    def test_summary_calculation(self, mock_get_tasks, client, valid_api_key):
        """RED: Should calculate summary statistics correctly"""
        today = datetime.combine(date.today(), time(8, 0))

        mock_tasks = [
            models.PetCareTask(
                id="1",
                schedule_id="s1",
                pet_id="p1",
                pet_name="Spike",
                task_name="Feed",
                assigned_to_kid_id="clara",
                assigned_to_kid_username="Clara",
                points_value=5,
                due_date=today,
                status=models.PetCareTaskStatus.APPROVED,
                created_at=today,
            ),
            models.PetCareTask(
                id="2",
                schedule_id="s1",
                pet_id="p1",
                pet_name="Spike",
                task_name="Clean",
                assigned_to_kid_id="emery",
                assigned_to_kid_username="Emery",
                points_value=10,
                due_date=today,
                status=models.PetCareTaskStatus.ASSIGNED,
                created_at=today,
            ),
            models.PetCareTask(
                id="3",
                schedule_id="s1",
                pet_id="p1",
                pet_name="Spike",
                task_name="Exercise",
                assigned_to_kid_id="aiden",
                assigned_to_kid_username="Aiden",
                points_value=5,
                due_date=today,
                status=models.PetCareTaskStatus.PENDING_APPROVAL,
                created_at=today,
            ),
        ]
        mock_get_tasks.return_value = mock_tasks

        response = client.get("/api/home-assistant/pet-tasks/today", headers={"X-HA-API-Key": valid_api_key})

        data = response.json()
        summary = data["summary"]

        assert summary["total"] == 3
        assert summary["done"] == 1
        assert summary["pending"] == 1
        assert summary["awaiting_approval"] == 1
        assert summary["overdue"] == 0


class TestSecurityFunction:
    """Test the verify_ha_api_key security function"""

    def test_api_key_validation_min_length(self):
        """RED: API key must be at least 32 characters"""
        os.environ["HOME_ASSISTANT_API_KEY"] = "short-key"

        import security

        result = security.verify_ha_api_key("short-key")
        assert result is False

    def test_api_key_validation_missing(self):
        """RED: Should handle missing API key gracefully"""
        os.environ.pop("HOME_ASSISTANT_API_KEY", None)

        import security

        result = security.verify_ha_api_key("any-key")
        assert result is False

    def test_api_key_validation_success(self):
        """RED: Should accept valid API key"""
        valid_key = "test-key-32-characters-minimum!!"
        os.environ["HOME_ASSISTANT_API_KEY"] = valid_key

        import security

        result = security.verify_ha_api_key(valid_key)
        assert result is True
