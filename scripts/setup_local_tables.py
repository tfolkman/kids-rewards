#!/usr/bin/env python3
"""
Create all DynamoDB tables for local development.
This script creates the tables with the same structure as defined in template.yaml
"""

import os
import boto3
from botocore.exceptions import ClientError

# Configuration
DYNAMODB_ENDPOINT = os.getenv("DYNAMODB_ENDPOINT_OVERRIDE", "http://localhost:8000")
AWS_REGION = os.getenv("AWS_REGION", "us-west-2")

# Set dummy credentials for local DynamoDB
os.environ["AWS_ACCESS_KEY_ID"] = "dummy"
os.environ["AWS_SECRET_ACCESS_KEY"] = "dummy"

# Initialize DynamoDB
dynamodb = boto3.client("dynamodb", endpoint_url=DYNAMODB_ENDPOINT, region_name=AWS_REGION)


def create_table_if_not_exists(table_name, key_schema, attribute_definitions, 
                               provisioned_throughput=None, global_secondary_indexes=None):
    """Create a DynamoDB table if it doesn't already exist."""
    try:
        # Check if table exists
        dynamodb.describe_table(TableName=table_name)
        print(f"✓ Table {table_name} already exists")
        return True
    except ClientError as e:
        if e.response['Error']['Code'] != 'ResourceNotFoundException':
            print(f"✗ Error checking table {table_name}: {e}")
            return False
    
    # Create table
    try:
        params = {
            'TableName': table_name,
            'KeySchema': key_schema,
            'AttributeDefinitions': attribute_definitions,
            'ProvisionedThroughput': provisioned_throughput or {
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        }
        
        if global_secondary_indexes:
            params['GlobalSecondaryIndexes'] = global_secondary_indexes
        
        dynamodb.create_table(**params)
        print(f"✓ Created table {table_name}")
        return True
    except Exception as e:
        print(f"✗ Error creating table {table_name}: {e}")
        return False


def setup_tables():
    """Create all tables needed for the Kids Rewards app."""
    print("Setting up DynamoDB tables for local development...")
    print(f"DynamoDB endpoint: {DYNAMODB_ENDPOINT}")
    print("-" * 50)
    
    # KidsRewardsUsers table
    create_table_if_not_exists(
        table_name="KidsRewardsUsers",
        key_schema=[{'AttributeName': 'username', 'KeyType': 'HASH'}],
        attribute_definitions=[{'AttributeName': 'username', 'AttributeType': 'S'}]
    )
    
    # KidsRewardsFamilies table
    create_table_if_not_exists(
        table_name="KidsRewardsFamilies",
        key_schema=[{'AttributeName': 'id', 'KeyType': 'HASH'}],
        attribute_definitions=[{'AttributeName': 'id', 'AttributeType': 'S'}],
        provisioned_throughput={'ReadCapacityUnits': 2, 'WriteCapacityUnits': 2}
    )
    
    # KidsRewardsStoreItems table
    create_table_if_not_exists(
        table_name="KidsRewardsStoreItems",
        key_schema=[{'AttributeName': 'id', 'KeyType': 'HASH'}],
        attribute_definitions=[{'AttributeName': 'id', 'AttributeType': 'S'}]
    )
    
    # KidsRewardsPurchaseLogs table
    create_table_if_not_exists(
        table_name="KidsRewardsPurchaseLogs",
        key_schema=[{'AttributeName': 'id', 'KeyType': 'HASH'}],
        attribute_definitions=[
            {'AttributeName': 'id', 'AttributeType': 'S'},
            {'AttributeName': 'user_id', 'AttributeType': 'S'},
            {'AttributeName': 'timestamp', 'AttributeType': 'S'},
            {'AttributeName': 'status', 'AttributeType': 'S'}
        ],
        global_secondary_indexes=[
            {
                'IndexName': 'UserIdTimestampIndex',
                'KeySchema': [
                    {'AttributeName': 'user_id', 'KeyType': 'HASH'},
                    {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
                ],
                'Projection': {'ProjectionType': 'ALL'},
                'ProvisionedThroughput': {'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
            },
            {
                'IndexName': 'StatusTimestampIndex',
                'KeySchema': [
                    {'AttributeName': 'status', 'KeyType': 'HASH'},
                    {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
                ],
                'Projection': {'ProjectionType': 'ALL'},
                'ProvisionedThroughput': {'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
            }
        ]
    )
    
    # KidsRewardsChores table
    create_table_if_not_exists(
        table_name="KidsRewardsChores",
        key_schema=[{'AttributeName': 'id', 'KeyType': 'HASH'}],
        attribute_definitions=[
            {'AttributeName': 'id', 'AttributeType': 'S'},
            {'AttributeName': 'created_by_parent_id', 'AttributeType': 'S'},
            {'AttributeName': 'is_active', 'AttributeType': 'S'}
        ],
        global_secondary_indexes=[
            {
                'IndexName': 'ParentChoresIndex',
                'KeySchema': [{'AttributeName': 'created_by_parent_id', 'KeyType': 'HASH'}],
                'Projection': {'ProjectionType': 'ALL'},
                'ProvisionedThroughput': {'ReadCapacityUnits': 2, 'WriteCapacityUnits': 2}
            },
            {
                'IndexName': 'ActiveChoresIndex',
                'KeySchema': [{'AttributeName': 'is_active', 'KeyType': 'HASH'}],
                'Projection': {'ProjectionType': 'ALL'},
                'ProvisionedThroughput': {'ReadCapacityUnits': 2, 'WriteCapacityUnits': 2}
            }
        ]
    )
    
    # KidsRewardsChoreLogs table
    create_table_if_not_exists(
        table_name="KidsRewardsChoreLogs",
        key_schema=[{'AttributeName': 'id', 'KeyType': 'HASH'}],
        attribute_definitions=[
            {'AttributeName': 'id', 'AttributeType': 'S'},
            {'AttributeName': 'kid_id', 'AttributeType': 'S'},
            {'AttributeName': 'submitted_at', 'AttributeType': 'S'},
            {'AttributeName': 'status', 'AttributeType': 'S'}
        ],
        global_secondary_indexes=[
            {
                'IndexName': 'KidChoreLogIndex',
                'KeySchema': [
                    {'AttributeName': 'kid_id', 'KeyType': 'HASH'},
                    {'AttributeName': 'submitted_at', 'KeyType': 'RANGE'}
                ],
                'Projection': {'ProjectionType': 'ALL'},
                'ProvisionedThroughput': {'ReadCapacityUnits': 2, 'WriteCapacityUnits': 2}
            },
            {
                'IndexName': 'ChoreLogStatusIndex',
                'KeySchema': [
                    {'AttributeName': 'status', 'KeyType': 'HASH'},
                    {'AttributeName': 'submitted_at', 'KeyType': 'RANGE'}
                ],
                'Projection': {'ProjectionType': 'ALL'},
                'ProvisionedThroughput': {'ReadCapacityUnits': 2, 'WriteCapacityUnits': 2}
            }
        ]
    )
    
    # KidsRewardsRequests table
    create_table_if_not_exists(
        table_name="KidsRewardsRequests",
        key_schema=[{'AttributeName': 'id', 'KeyType': 'HASH'}],
        attribute_definitions=[
            {'AttributeName': 'id', 'AttributeType': 'S'},
            {'AttributeName': 'requester_id', 'AttributeType': 'S'},
            {'AttributeName': 'created_at', 'AttributeType': 'S'},
            {'AttributeName': 'status', 'AttributeType': 'S'}
        ],
        global_secondary_indexes=[
            {
                'IndexName': 'RequesterIdCreatedAtGSI',
                'KeySchema': [
                    {'AttributeName': 'requester_id', 'KeyType': 'HASH'},
                    {'AttributeName': 'created_at', 'KeyType': 'RANGE'}
                ],
                'Projection': {'ProjectionType': 'ALL'},
                'ProvisionedThroughput': {'ReadCapacityUnits': 2, 'WriteCapacityUnits': 2}
            },
            {
                'IndexName': 'StatusCreatedAtGSI',
                'KeySchema': [
                    {'AttributeName': 'status', 'KeyType': 'HASH'},
                    {'AttributeName': 'created_at', 'KeyType': 'RANGE'}
                ],
                'Projection': {'ProjectionType': 'ALL'},
                'ProvisionedThroughput': {'ReadCapacityUnits': 2, 'WriteCapacityUnits': 2}
            }
        ]
    )
    
    print("-" * 50)
    print("✓ Table setup complete!")
    print("\nYou can now run the migration script.")


if __name__ == "__main__":
    setup_tables()