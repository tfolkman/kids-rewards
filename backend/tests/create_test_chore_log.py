#!/usr/bin/env python3
"""Create a test pending chore log for testparent's family"""
import os
import sys
import uuid
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import boto3
from boto3.dynamodb.conditions import Key

# Setup DynamoDB
dynamodb = boto3.resource(
    'dynamodb',
    endpoint_url='http://localhost:8000',
    region_name='us-west-2',
    aws_access_key_id='test',
    aws_secret_access_key='test'
)

# Get tables
users_table = dynamodb.Table('KidsRewardsUsers')
chores_table = dynamodb.Table('KidsRewardsChores')
chore_logs_table = dynamodb.Table('KidsRewardsChoreLogs')

# Find testkid in folkman-family
print("Finding testkid in folkman-family...")
response = users_table.scan(
    FilterExpression=Key('username').eq('testkid') & Key('family_id').eq('folkman-family')
)

if not response['Items']:
    print("testkid not found in folkman-family. Let's check all kids...")
    response = users_table.scan(
        FilterExpression=Key('role').eq('kid') & Key('family_id').eq('folkman-family')
    )
    if response['Items']:
        kid = response['Items'][0]
        print(f"Found kid: {kid['username']} (id: {kid['id']})")
    else:
        print("No kids found in folkman-family. Creating testkid...")
        kid = {
            'id': 'testkid-folkman',
            'username': 'testkid',
            'role': 'kid',
            'points': 100,
            'family_id': 'folkman-family',
            'hashed_password': '$2b$12$K.XmGBhcOg0vAw4yqF7sAuanDN2IQQD5HFJJbZqLHbBZYs/WnBqEe'  # password123
        }
        users_table.put_item(Item=kid)
        print(f"Created kid: {kid['username']}")
else:
    kid = response['Items'][0]
    print(f"Found kid: {kid['username']} (id: {kid['id']})")

# Find or create a chore for folkman-family
print("\nFinding chores in folkman-family...")
response = chores_table.scan(
    FilterExpression=Key('family_id').eq('folkman-family')
)

if not response['Items']:
    print("No chores found. Creating a test chore...")
    chore = {
        'id': str(uuid.uuid4()),
        'name': 'Test Chore - Clean Kitchen',
        'description': 'Clean the kitchen counters and sink',
        'points_value': 25,
        'family_id': 'folkman-family',
        'created_by_parent_id': 'testparent',
        'is_active': 'true',
        'created_at': datetime.utcnow().isoformat(),
        'updated_at': datetime.utcnow().isoformat()
    }
    chores_table.put_item(Item=chore)
    print(f"Created chore: {chore['name']} (id: {chore['id']})")
else:
    chore = response['Items'][0]
    print(f"Found chore: {chore['name']} (id: {chore['id']})")

# Create a pending chore log
chore_log_id = str(uuid.uuid4())
chore_log = {
    'id': chore_log_id,
    'chore_id': chore['id'],
    'chore_name': chore['name'],
    'kid_id': kid['id'],
    'kid_username': kid['username'],
    'points_value': chore['points_value'],
    'status': 'pending_approval',
    'submitted_at': datetime.utcnow().isoformat(),
    'family_id': 'folkman-family'
}

print(f"\nCreating pending chore log...")
chore_logs_table.put_item(Item=chore_log)
print(f"Created chore log with ID: {chore_log_id}")
print(f"Status: {chore_log['status']}")
print(f"Family: {chore_log['family_id']}")
print(f"Kid: {chore_log['kid_username']} (id: {chore_log['kid_id']})")
print(f"Chore: {chore_log['chore_name']} ({chore_log['points_value']} points)")

print(f"\nYou can now test approval with this chore log ID: {chore_log_id}")
print(f"curl -X PUT http://localhost:3000/chores/logs/{chore_log_id}/approve -H 'Authorization: Bearer <token>'")