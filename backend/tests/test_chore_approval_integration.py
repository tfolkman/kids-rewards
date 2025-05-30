"""Integration test for chore approval against DynamoDB Local"""
import os
import uuid
from datetime import datetime

import boto3
import pytest
from botocore.exceptions import ClientError

# Setup DynamoDB client for local testing
dynamodb = boto3.resource(
    'dynamodb',
    endpoint_url=os.environ.get('DYNAMODB_ENDPOINT_OVERRIDE', 'http://localhost:8000'),
    region_name='us-west-2',
    aws_access_key_id='test',
    aws_secret_access_key='test'
)


def test_chore_approval_integration():
    """Integration test to debug chore approval issues"""
    
    # Table names from environment
    chore_logs_table_name = os.environ.get('CHORE_LOGS_TABLE_NAME', 'KidsRewardsChoreLogs')
    users_table_name = os.environ.get('USERS_TABLE_NAME', 'local-my-table')
    chores_table_name = os.environ.get('CHORES_TABLE_NAME', 'KidsRewardsChores')
    
    # Get table references
    chore_logs_table = dynamodb.Table(chore_logs_table_name)
    users_table = dynamodb.Table(users_table_name)
    chores_table = dynamodb.Table(chores_table_name)
    
    # Test data
    family_id = 'test-family-' + str(uuid.uuid4())
    parent_id = 'test-parent-' + str(uuid.uuid4())
    kid_id = 'test-kid-' + str(uuid.uuid4())
    chore_id = 'test-chore-' + str(uuid.uuid4())
    chore_log_id = 'test-log-' + str(uuid.uuid4())
    
    print(f"\nTest IDs:")
    print(f"  Family: {family_id}")
    print(f"  Parent: {parent_id}")
    print(f"  Kid: {kid_id}")
    print(f"  Chore: {chore_id}")
    print(f"  Log: {chore_log_id}")
    
    try:
        # 1. Create test kid user
        print("\n1. Creating kid user...")
        kid_user = {
            'id': kid_id,
            'username': 'testkid_' + kid_id[:8],
            'role': 'kid',
            'points': 50,
            'family_id': family_id,
            'hashed_password': 'dummy_hash'
        }
        users_table.put_item(Item=kid_user)
        print(f"   Created kid with {kid_user['points']} points")
        
        # 2. Create test chore
        print("\n2. Creating chore...")
        chore = {
            'id': chore_id,
            'name': 'Test Chore',
            'description': 'Test chore description',
            'points_value': 10,
            'family_id': family_id,
            'created_by_parent_id': parent_id,
            'is_active': 'true',
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        chores_table.put_item(Item=chore)
        print(f"   Created chore worth {chore['points_value']} points")
        
        # 3. Create pending chore log
        print("\n3. Creating pending chore log...")
        chore_log = {
            'id': chore_log_id,
            'chore_id': chore_id,
            'chore_name': chore['name'],
            'kid_id': kid_id,
            'kid_username': kid_user['username'],
            'points_value': chore['points_value'],
            'status': 'pending_approval',
            'submitted_at': datetime.utcnow().isoformat(),
            'family_id': family_id
        }
        chore_logs_table.put_item(Item=chore_log)
        print("   Created pending chore log")
        
        # 4. Test scanning for the chore log
        print("\n4. Testing scan operation...")
        scan_response = chore_logs_table.scan(
            FilterExpression='id = :id',
            ExpressionAttributeValues={':id': chore_log_id}
        )
        print(f"   Found {len(scan_response['Items'])} items")
        if scan_response['Items']:
            found_log = scan_response['Items'][0]
            print(f"   Log status: {found_log['status']}")
            print(f"   Log family: {found_log['family_id']}")
        
        # 5. Test the approval update
        print("\n5. Testing approval update...")
        update_response = chore_logs_table.update_item(
            Key={'id': chore_log_id},
            UpdateExpression='SET #status = :status, reviewed_by_parent_id = :parent_id, reviewed_at = :reviewed_at',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': 'approved',
                ':parent_id': parent_id,
                ':reviewed_at': datetime.utcnow().isoformat(),
                ':family_id': family_id
            },
            ConditionExpression='family_id = :family_id',
            ReturnValues='ALL_NEW'
        )
        print("   Updated chore log to approved")
        print(f"   New status: {update_response['Attributes']['status']}")
        
        # 6. Test getting kid user for points update
        print("\n6. Testing get kid user...")
        user_response = users_table.get_item(Key={'id': kid_id})
        if 'Item' in user_response:
            print(f"   Found kid user with {user_response['Item']['points']} points")
        else:
            print("   ERROR: Kid user not found!")
        
        # 7. Test updating kid points
        print("\n7. Testing points update...")
        new_points = user_response['Item']['points'] + chore['points_value']
        users_table.update_item(
            Key={'id': kid_id},
            UpdateExpression='SET points = :points',
            ExpressionAttributeValues={':points': new_points}
        )
        print(f"   Updated kid points to {new_points}")
        
        # 8. Verify final state
        print("\n8. Verifying final state...")
        final_log = chore_logs_table.get_item(Key={'id': chore_log_id})['Item']
        final_user = users_table.get_item(Key={'id': kid_id})['Item']
        
        print(f"   Chore log status: {final_log['status']}")
        print(f"   Kid points: {final_user['points']}")
        
        assert final_log['status'] == 'approved'
        assert final_user['points'] == 60  # 50 + 10
        
        print("\n✅ All tests passed!")
        
    except ClientError as e:
        print(f"\n❌ DynamoDB Error: {e}")
        print(f"   Error Code: {e.response['Error']['Code']}")
        print(f"   Error Message: {e.response['Error']['Message']}")
        raise
    except Exception as e:
        print(f"\n❌ Unexpected Error: {e}")
        raise
    finally:
        # Cleanup
        print("\n9. Cleaning up test data...")
        try:
            chore_logs_table.delete_item(Key={'id': chore_log_id})
            users_table.delete_item(Key={'id': kid_id})
            chores_table.delete_item(Key={'id': chore_id})
            print("   Cleanup complete")
        except:
            pass


def test_check_table_structure():
    """Check the actual structure of data in the tables"""
    chore_logs_table_name = os.environ.get('CHORE_LOGS_TABLE_NAME', 'KidsRewardsChoreLogs')
    chore_logs_table = dynamodb.Table(chore_logs_table_name)
    
    print(f"\nScanning {chore_logs_table_name} table...")
    
    # Scan for any pending approval logs
    response = chore_logs_table.scan(
        FilterExpression='#status = :status',
        ExpressionAttributeNames={'#status': 'status'},
        ExpressionAttributeValues={':status': 'pending_approval'},
        Limit=5
    )
    
    print(f"Found {len(response['Items'])} pending approval items")
    
    if response['Items']:
        print("\nSample item structure:")
        item = response['Items'][0]
        for key, value in item.items():
            print(f"  {key}: {value} (type: {type(value).__name__})")


if __name__ == '__main__':
    # Run with proper environment variables
    print("Running chore approval integration tests...")
    print(f"DynamoDB Endpoint: {os.environ.get('DYNAMODB_ENDPOINT_OVERRIDE', 'http://localhost:8000')}")
    
    # Run the tests
    test_chore_approval_integration()
    print("\n" + "="*50 + "\n")
    test_check_table_structure()