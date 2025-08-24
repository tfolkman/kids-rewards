import os
import sys
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import patch

import pytest

# Add the backend directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import crud
import models


class TestEffortTracking:
    """Test suite for effort tracking functionality."""

    @pytest.fixture
    def mock_chore(self):
        """Create a mock chore for testing."""
        return models.Chore(
            id="chore-123",
            name="Clean Room",
            description="Clean your room thoroughly",
            points_value=10,
            created_by_parent_id="parent-1",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            is_active=True,
        )

    @pytest.fixture
    def mock_kid_user(self):
        """Create a mock kid user for testing."""
        return models.User(
            id="kid-1",
            username="kid-1",
            role=models.UserRole.KID,
            hashed_password="hashed",
            points=100,
        )

    @pytest.fixture
    def mock_parent_user(self):
        """Create a mock parent user for testing."""
        return models.User(
            id="parent-1",
            username="parent-1",
            role=models.UserRole.PARENT,
            hashed_password="hashed",
            points=None,
        )

    @patch("crud.chore_logs_table")
    @patch("crud.get_chore_by_id")
    @patch("crud.get_chore_logs_by_kid_id")
    def test_create_chore_log_with_effort_tracking(
        self, mock_get_logs, mock_get_chore, mock_table, mock_chore, mock_kid_user
    ):
        """Test creating a chore log with effort tracking."""
        # Setup
        mock_get_chore.return_value = mock_chore
        mock_get_logs.return_value = []  # No previous attempts
        mock_table.put_item.return_value = True

        # Execute
        result = crud.create_chore_log_submission(chore_id="chore-123", kid_user=mock_kid_user, effort_minutes=30)

        # Assert
        assert result is not None
        assert result.effort_minutes == 30
        assert result.effort_points == 10  # 30 * 0.5 = 15, but capped at 10
        assert result.retry_count == 0
        assert result.is_retry is False

        # Verify the DynamoDB call
        mock_table.put_item.assert_called_once()
        call_args = mock_table.put_item.call_args[1]["Item"]
        assert call_args["effort_minutes"] == 30
        assert call_args["effort_points"] == Decimal(10)  # Capped at 10
        assert call_args["retry_count"] == 0
        assert call_args["is_retry"] is False

    @patch("crud.chore_logs_table")
    @patch("crud.get_chore_by_id")
    @patch("crud.get_chore_logs_by_kid_id")
    def test_effort_points_calculation(self, mock_get_logs, mock_get_chore, mock_table, mock_chore, mock_kid_user):
        """Test effort points calculation (0.5 points per minute, max 10)."""
        mock_get_chore.return_value = mock_chore
        mock_get_logs.return_value = []
        mock_table.put_item.return_value = True

        test_cases = [
            (0, 0),  # No effort
            (5, 2),  # 5 minutes = 2.5 rounded to 2
            (10, 5),  # 10 minutes = 5 points
            (20, 10),  # 20 minutes = 10 points (max)
            (30, 10),  # 30 minutes = still 10 (capped)
            (100, 10),  # 100 minutes = still 10 (capped)
        ]

        for effort_minutes, expected_points in test_cases:
            result = crud.create_chore_log_submission(
                chore_id="chore-123", kid_user=mock_kid_user, effort_minutes=effort_minutes
            )
            assert result.effort_points == expected_points, f"Failed for {effort_minutes} minutes"

    @patch("crud.chore_logs_table")
    @patch("crud.get_chore_by_id")
    @patch("crud.get_chore_logs_by_kid_id")
    def test_retry_detection_within_24_hours(
        self, mock_get_logs, mock_get_chore, mock_table, mock_chore, mock_kid_user
    ):
        """Test retry detection for same chore within 24 hours."""
        # Setup - simulate previous rejected attempt
        previous_log = models.ChoreLog(
            id="log-1",
            chore_id="chore-123",
            chore_name="Clean Room",
            kid_id="kid-1",
            kid_username="kid-1",
            points_value=10,
            status=models.ChoreStatus.REJECTED,
            submitted_at=datetime.utcnow() - timedelta(hours=12),  # 12 hours ago
            reviewed_by_parent_id="parent-1",
            reviewed_at=datetime.utcnow() - timedelta(hours=10),
        )

        mock_get_chore.return_value = mock_chore
        mock_get_logs.return_value = [previous_log]
        mock_table.put_item.return_value = True

        # Execute
        result = crud.create_chore_log_submission(chore_id="chore-123", kid_user=mock_kid_user, effort_minutes=15)

        # Assert
        assert result.is_retry is True
        assert result.retry_count == 1

    @patch("crud.chore_logs_table")
    @patch("crud.get_chore_by_id")
    @patch("crud.get_chore_logs_by_kid_id")
    def test_no_retry_detection_after_24_hours(
        self, mock_get_logs, mock_get_chore, mock_table, mock_chore, mock_kid_user
    ):
        """Test that retries are not detected after 24 hours."""
        # Setup - simulate previous attempt more than 24 hours ago
        previous_log = models.ChoreLog(
            id="log-1",
            chore_id="chore-123",
            chore_name="Clean Room",
            kid_id="kid-1",
            kid_username="kid-1",
            points_value=10,
            status=models.ChoreStatus.REJECTED,
            submitted_at=datetime.utcnow() - timedelta(hours=25),  # 25 hours ago
            reviewed_by_parent_id="parent-1",
            reviewed_at=datetime.utcnow() - timedelta(hours=24),
        )

        mock_get_chore.return_value = mock_chore
        mock_get_logs.return_value = [previous_log]
        mock_table.put_item.return_value = True

        # Execute
        result = crud.create_chore_log_submission(chore_id="chore-123", kid_user=mock_kid_user, effort_minutes=15)

        # Assert
        assert result.is_retry is False
        assert result.retry_count == 0

    @patch("crud.chore_logs_table")
    @patch("crud.get_chore_by_id")
    @patch("crud.get_chore_logs_by_kid_id")
    def test_multiple_retry_attempts_count(self, mock_get_logs, mock_get_chore, mock_table, mock_chore, mock_kid_user):
        """Test that multiple retry attempts are counted correctly."""
        # Setup - simulate two previous attempts within 24 hours
        previous_logs = [
            models.ChoreLog(
                id="log-1",
                chore_id="chore-123",
                chore_name="Clean Room",
                kid_id="kid-1",
                kid_username="kid-1",
                points_value=10,
                status=models.ChoreStatus.REJECTED,
                submitted_at=datetime.utcnow() - timedelta(hours=20),
                reviewed_by_parent_id="parent-1",
                reviewed_at=datetime.utcnow() - timedelta(hours=19),
            ),
            models.ChoreLog(
                id="log-2",
                chore_id="chore-123",
                chore_name="Clean Room",
                kid_id="kid-1",
                kid_username="kid-1",
                points_value=10,
                status=models.ChoreStatus.PENDING_APPROVAL,
                submitted_at=datetime.utcnow() - timedelta(hours=10),
                reviewed_by_parent_id=None,
                reviewed_at=None,
            ),
        ]

        mock_get_chore.return_value = mock_chore
        mock_get_logs.return_value = previous_logs
        mock_table.put_item.return_value = True

        # Execute
        result = crud.create_chore_log_submission(chore_id="chore-123", kid_user=mock_kid_user, effort_minutes=15)

        # Assert
        assert result.is_retry is True
        assert result.retry_count == 2  # Two previous attempts

    @patch("crud.get_chore_logs_by_kid_id")
    def test_streak_calculation_includes_effort_attempts(self, mock_get_logs):
        """Test that streak calculation includes high-effort attempts."""
        # Create mix of approved and high-effort rejected chores
        today = datetime.utcnow()
        chore_logs = [
            # Today - approved chore
            models.ChoreLog(
                id="log-1",
                chore_id="chore-1",
                chore_name="Chore 1",
                kid_id="kid-1",
                kid_username="kid-1",
                points_value=10,
                status=models.ChoreStatus.APPROVED,
                submitted_at=today,
                reviewed_by_parent_id="parent-1",
                reviewed_at=today,
                effort_minutes=5,
                retry_count=0,
                effort_points=2,
                is_retry=False,
            ),
            # Yesterday - rejected but high effort (should count)
            models.ChoreLog(
                id="log-2",
                chore_id="chore-2",
                chore_name="Chore 2",
                kid_id="kid-1",
                kid_username="kid-1",
                points_value=10,
                status=models.ChoreStatus.REJECTED,
                submitted_at=today - timedelta(days=1),
                reviewed_by_parent_id="parent-1",
                reviewed_at=today - timedelta(days=1),
                effort_minutes=15,  # High effort
                retry_count=0,
                effort_points=7,
                is_retry=False,
            ),
            # 2 days ago - rejected with low effort (should not count)
            models.ChoreLog(
                id="log-3",
                chore_id="chore-3",
                chore_name="Chore 3",
                kid_id="kid-1",
                kid_username="kid-1",
                points_value=10,
                status=models.ChoreStatus.REJECTED,
                submitted_at=today - timedelta(days=2),
                reviewed_by_parent_id="parent-1",
                reviewed_at=today - timedelta(days=2),
                effort_minutes=5,  # Low effort
                retry_count=0,
                effort_points=2,
                is_retry=False,
            ),
        ]

        mock_get_logs.return_value = chore_logs

        # Execute
        streak_data = crud.calculate_streak_for_kid("kid-1")

        # Assert
        assert streak_data["current_streak"] == 2  # Today + yesterday (high effort)
        assert streak_data["streak_active"] is True
        assert streak_data["last_completion_date"] is not None

    @patch("crud.get_chore_logs_by_kid_id")
    def test_streak_breaks_without_effort(self, mock_get_logs):
        """Test that streak breaks when there's no effort or approval."""
        today = datetime.utcnow()
        chore_logs = [
            # Today - approved
            models.ChoreLog(
                id="log-1",
                chore_id="chore-1",
                chore_name="Chore 1",
                kid_id="kid-1",
                kid_username="kid-1",
                points_value=10,
                status=models.ChoreStatus.APPROVED,
                submitted_at=today,
                reviewed_by_parent_id="parent-1",
                reviewed_at=today,
                effort_minutes=5,
                retry_count=0,
                effort_points=2,
                is_retry=False,
            ),
            # 3 days ago - approved (streak should break due to gap)
            models.ChoreLog(
                id="log-2",
                chore_id="chore-2",
                chore_name="Chore 2",
                kid_id="kid-1",
                kid_username="kid-1",
                points_value=10,
                status=models.ChoreStatus.APPROVED,
                submitted_at=today - timedelta(days=3),
                reviewed_by_parent_id="parent-1",
                reviewed_at=today - timedelta(days=3),
                effort_minutes=10,
                retry_count=0,
                effort_points=5,
                is_retry=False,
            ),
        ]

        mock_get_logs.return_value = chore_logs

        # Execute
        streak_data = crud.calculate_streak_for_kid("kid-1")

        # Assert
        assert streak_data["current_streak"] == 1  # Only today counts
        assert streak_data["streak_active"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
