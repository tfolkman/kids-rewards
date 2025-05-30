"""Test chore log approval functionality"""
import uuid
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError
from fastapi import HTTPException

import crud
import models
from models import ChoreStatus, UserRole


class TestChoreLogApproval:
    """Test suite for chore log approval functionality"""

    @pytest.fixture
    def mock_tables(self):
        """Mock DynamoDB tables"""
        with patch('crud.chore_logs_table') as mock_chore_logs, \
             patch('crud.users_table') as mock_users, \
             patch('crud.chores_table') as mock_chores:
            yield {
                'chore_logs': mock_chore_logs,
                'users': mock_users,
                'chores': mock_chores
            }

    @pytest.fixture
    def sample_chore_log(self):
        """Sample chore log data"""
        return {
            'id': 'log123',
            'chore_id': 'chore456',
            'chore_name': 'Clean Room',
            'kid_id': 'kid789',
            'kid_username': 'testkid',
            'points_value': 10,
            'status': ChoreStatus.PENDING_APPROVAL.value,
            'submitted_at': datetime.utcnow().isoformat(),
            'family_id': 'family123'
        }

    @pytest.fixture
    def sample_kid_user(self):
        """Sample kid user data"""
        return {
            'id': 'kid789',
            'username': 'testkid',
            'role': UserRole.KID.value,
            'points': 50,
            'family_id': 'family123'
        }

    def test_approve_chore_log_success(self, mock_tables, sample_chore_log, sample_kid_user):
        """Test successful chore log approval"""
        # Setup mocks
        mock_tables['chore_logs'].scan.return_value = {
            'Items': [sample_chore_log]
        }
        
        mock_tables['chore_logs'].update_item.return_value = {
            'Attributes': {
                **sample_chore_log,
                'status': ChoreStatus.APPROVED.value,
                'reviewed_by_parent_id': 'parent123',
                'reviewed_at': datetime.utcnow().isoformat()
            }
        }
        
        mock_tables['users'].get_item.return_value = {
            'Item': sample_kid_user
        }
        
        # Call the function
        result = crud.approve_chore_log(
            chore_log_id='log123',
            parent_id='parent123',
            family_id='family123'
        )
        
        # Assertions
        assert result.status == ChoreStatus.APPROVED
        assert result.reviewed_by_parent_id == 'parent123'
        
        # Verify scan was called correctly
        mock_tables['chore_logs'].scan.assert_called_once()
        scan_kwargs = mock_tables['chore_logs'].scan.call_args[1]
        assert 'FilterExpression' in scan_kwargs
        
        # Verify update was called
        mock_tables['chore_logs'].update_item.assert_called_once()
        
        # Verify points were updated
        mock_tables['users'].update_item.assert_called_once_with(
            Key={'id': 'kid789'},
            UpdateExpression='SET points = :points',
            ExpressionAttributeValues={':points': 60}  # 50 + 10
        )

    def test_approve_chore_log_not_found(self, mock_tables):
        """Test approval when chore log doesn't exist"""
        # Setup mock to return empty results
        mock_tables['chore_logs'].scan.return_value = {
            'Items': []
        }
        
        # Should raise 404
        with pytest.raises(HTTPException) as exc_info:
            crud.approve_chore_log(
                chore_log_id='nonexistent',
                parent_id='parent123',
                family_id='family123'
            )
        
        assert exc_info.value.status_code == 404
        assert "Chore log not found" in str(exc_info.value.detail)

    def test_approve_chore_log_wrong_family(self, mock_tables, sample_chore_log):
        """Test approval when chore log belongs to different family"""
        # Setup mock with different family_id
        wrong_family_log = {**sample_chore_log, 'family_id': 'different_family'}
        mock_tables['chore_logs'].scan.return_value = {
            'Items': [wrong_family_log]
        }
        
        # Should raise 404
        with pytest.raises(HTTPException) as exc_info:
            crud.approve_chore_log(
                chore_log_id='log123',
                parent_id='parent123',
                family_id='family123'
            )
        
        assert exc_info.value.status_code == 404
        assert "not found in your family" in str(exc_info.value.detail)

    def test_approve_chore_log_already_approved(self, mock_tables, sample_chore_log):
        """Test approval when chore is already approved"""
        # Setup mock with already approved status
        approved_log = {**sample_chore_log, 'status': ChoreStatus.APPROVED.value}
        mock_tables['chore_logs'].scan.return_value = {
            'Items': [approved_log]
        }
        
        # Should raise 400
        with pytest.raises(HTTPException) as exc_info:
            crud.approve_chore_log(
                chore_log_id='log123',
                parent_id='parent123',
                family_id='family123'
            )
        
        assert exc_info.value.status_code == 400
        assert "not pending approval" in str(exc_info.value.detail)

    def test_approve_chore_log_kid_not_found(self, mock_tables, sample_chore_log):
        """Test approval when kid user doesn't exist"""
        # Setup mocks
        mock_tables['chore_logs'].scan.return_value = {
            'Items': [sample_chore_log]
        }
        
        mock_tables['chore_logs'].update_item.return_value = {
            'Attributes': {
                **sample_chore_log,
                'status': ChoreStatus.APPROVED.value
            }
        }
        
        # Kid not found
        mock_tables['users'].get_item.return_value = {}
        
        # Should raise 404
        with pytest.raises(HTTPException) as exc_info:
            crud.approve_chore_log(
                chore_log_id='log123',
                parent_id='parent123',
                family_id='family123'
            )
        
        assert exc_info.value.status_code == 404
        assert "Kid user not found" in str(exc_info.value.detail)

    def test_approve_chore_log_dynamodb_error(self, mock_tables, sample_chore_log):
        """Test approval when DynamoDB operation fails"""
        # Setup mock to raise ClientError
        mock_tables['chore_logs'].scan.side_effect = ClientError(
            {'Error': {'Code': 'InternalServerError', 'Message': 'DB Error'}},
            'scan'
        )
        
        # Should raise 500
        with pytest.raises(HTTPException) as exc_info:
            crud.approve_chore_log(
                chore_log_id='log123',
                parent_id='parent123',
                family_id='family123'
            )
        
        assert exc_info.value.status_code == 500
        assert "Could not approve chore submission" in str(exc_info.value.detail)

    def test_approve_chore_log_empty_id(self, mock_tables):
        """Test approval with empty chore log ID"""
        # Should raise 400
        with pytest.raises(HTTPException) as exc_info:
            crud.approve_chore_log(
                chore_log_id='',
                parent_id='parent123',
                family_id='family123'
            )
        
        assert exc_info.value.status_code == 400
        assert "Chore log ID is required" in str(exc_info.value.detail)

    def test_approve_chore_log_with_pagination(self, mock_tables, sample_chore_log):
        """Test approval when scan requires pagination"""
        # First page returns no items but has more pages
        mock_tables['chore_logs'].scan.side_effect = [
            {
                'Items': [],
                'LastEvaluatedKey': {'id': 'somekey'}
            },
            {
                'Items': [sample_chore_log]
            }
        ]
        
        mock_tables['chore_logs'].update_item.return_value = {
            'Attributes': {
                **sample_chore_log,
                'status': ChoreStatus.APPROVED.value
            }
        }
        
        mock_tables['users'].get_item.return_value = {
            'Item': {'id': 'kid789', 'points': 50}
        }
        
        # Should succeed after pagination
        result = crud.approve_chore_log(
            chore_log_id='log123',
            parent_id='parent123',
            family_id='family123'
        )
        
        assert result.status == ChoreStatus.APPROVED
        assert mock_tables['chore_logs'].scan.call_count == 2


class TestChoreLogEndpoint:
    """Test the FastAPI endpoint for chore approval"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        from fastapi.testclient import TestClient
        from main import app
        return TestClient(app)
    
    @pytest.fixture
    def auth_headers(self):
        """Mock authentication headers"""
        return {"Authorization": "Bearer mock_token"}
    
    @patch('main.get_current_parent_user')
    @patch('crud.approve_chore_log')
    def test_approve_endpoint_success(self, mock_approve, mock_get_parent, client, auth_headers):
        """Test successful approval through endpoint"""
        # Setup mocks
        mock_parent = models.User(
            id='parent123',
            username='testparent',
            role=UserRole.PARENT,
            family_id='family123'
        )
        mock_get_parent.return_value = mock_parent
        
        mock_chore_log = models.ChoreLog(
            id='log123',
            chore_id='chore456',
            chore_name='Clean Room',
            kid_id='kid789',
            kid_username='testkid',
            points_value=10,
            status=ChoreStatus.APPROVED,
            submitted_at=datetime.utcnow(),
            reviewed_by_parent_id='parent123',
            reviewed_at=datetime.utcnow(),
            family_id='family123'
        )
        mock_approve.return_value = mock_chore_log
        
        # Make request
        response = client.put(
            '/chores/logs/log123/approve',
            headers=auth_headers
        )
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'approved'
        assert data['reviewed_by_parent_id'] == 'parent123'
        
        # Verify function was called correctly
        mock_approve.assert_called_once_with(
            chore_log_id='log123',
            parent_id='parent123',
            family_id='family123'
        )


if __name__ == '__main__':
    # Run specific tests to debug the issue
    pytest.main([__file__, '-v', '-s'])