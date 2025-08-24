"""
Integration test for the Bearded Dragon purchases endpoint.
Tests the critical functionality of filtering and returning correct purchases.
"""

import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import models


def test_bearded_dragon_purchases_filtering():
    """
    Test that the bearded dragon endpoint correctly:
    1. Filters by the specific item_id
    2. Only returns purchases from clara, emery, and aiden
    3. Excludes other users and other items
    4. Returns data sorted by timestamp (newest first)
    """
    from main import app
    from fastapi.testclient import TestClient
    
    BEARDED_DRAGON_ITEM_ID = "4d35256f-f226-43d7-8211-627891059ebf"
    
    # Create mock purchase data with various scenarios
    mock_purchases = [
        # Valid bearded dragon purchases from the three kids
        models.PurchaseLog(
            id="1",
            user_id="clara-id",
            username="clara",
            item_id=BEARDED_DRAGON_ITEM_ID,
            item_name="$25 Bearded Dragon",
            points_spent=875,
            timestamp=datetime(2025, 1, 15, 10, 0, 0),
            status=models.PurchaseStatus.APPROVED
        ),
        models.PurchaseLog(
            id="2",
            user_id="emery-id",
            username="emery",
            item_id=BEARDED_DRAGON_ITEM_ID,
            item_name="$25 Bearded Dragon",
            points_spent=875,
            timestamp=datetime(2025, 1, 20, 14, 30, 0),
            status=models.PurchaseStatus.APPROVED
        ),
        models.PurchaseLog(
            id="3",
            user_id="aiden-id",
            username="AIDEN",  # Test case insensitive
            item_id=BEARDED_DRAGON_ITEM_ID,
            item_name="$25 Bearded Dragon",
            points_spent=875,
            timestamp=datetime(2025, 1, 10, 9, 15, 0),
            status=models.PurchaseStatus.APPROVED
        ),
        # Purchase from a different user (should be excluded)
        models.PurchaseLog(
            id="4",
            user_id="other-kid-id",
            username="oliver",
            item_id=BEARDED_DRAGON_ITEM_ID,
            item_name="$25 Bearded Dragon",
            points_spent=875,
            timestamp=datetime(2025, 1, 18, 11, 0, 0),
            status=models.PurchaseStatus.APPROVED
        ),
        # Purchase of a different item from clara (should be excluded)
        models.PurchaseLog(
            id="5",
            user_id="clara-id",
            username="clara",
            item_id="different-item-id",
            item_name="Video Game",
            points_spent=500,
            timestamp=datetime(2025, 1, 12, 16, 45, 0),
            status=models.PurchaseStatus.APPROVED
        ),
        # Pending bearded dragon purchase from emery (should be included)
        models.PurchaseLog(
            id="6",
            user_id="emery-id",
            username="emery",
            item_id=BEARDED_DRAGON_ITEM_ID,
            item_name="$25 Bearded Dragon",
            points_spent=875,
            timestamp=datetime(2025, 1, 22, 8, 0, 0),
            status=models.PurchaseStatus.PENDING
        ),
    ]
    
    # Mock the crud.get_all_purchase_logs function
    with patch('crud.get_all_purchase_logs') as mock_get_all:
        mock_get_all.return_value = mock_purchases
        
        # Mock the authentication dependency
        mock_user = models.User(
            id="test-user-id",
            username="clara",
            role=models.UserRole.KID,
            hashed_password="hashed",
            points=1000
        )
        
        client = TestClient(app)
        
        # Override the dependency
        from main import get_current_active_user
        
        def override_get_current_user():
            return mock_user
        
        app.dependency_overrides[get_current_active_user] = override_get_current_user
        
        try:
            # Make the request
            response = client.get("/kids/bearded-dragon-purchases")
            
            # Verify response status
            assert response.status_code == 200
            
            # Parse response data
            data = response.json()
            
            # Verify correct number of purchases returned (should be 4: 3 from kids + 1 pending)
            assert len(data) == 4, f"Expected 4 purchases, got {len(data)}"
            
            # Verify all returned purchases are for the bearded dragon item
            for purchase in data:
                assert purchase["item_id"] == BEARDED_DRAGON_ITEM_ID
            
            # Verify only the three kids' purchases are included
            usernames = [p["username"].lower() for p in data]
            assert all(username in ["clara", "emery", "aiden"] for username in usernames)
            assert "oliver" not in usernames
            
            # Verify sorting by timestamp (newest first)
            timestamps = [datetime.fromisoformat(p["timestamp"].replace("Z", "")) for p in data]
            assert timestamps == sorted(timestamps, reverse=True), "Purchases not sorted by timestamp descending"
            
            # Verify the newest purchase is first
            assert data[0]["id"] == "6"  # Jan 22 purchase
            assert data[1]["id"] == "2"  # Jan 20 purchase
            assert data[2]["id"] == "1"  # Jan 15 purchase
            assert data[3]["id"] == "3"  # Jan 10 purchase
        finally:
            # Clean up the dependency override
            app.dependency_overrides.clear()


if __name__ == "__main__":
    # Run the test directly
    test_bearded_dragon_purchases_filtering()
    print("✓ All tests passed!")