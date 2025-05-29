#!/usr/bin/env python3
"""
Create character-related tables in local DynamoDB
"""

import boto3
import os
from botocore.exceptions import ClientError

# Check for local endpoint override
dynamodb_endpoint_override = os.getenv("DYNAMODB_ENDPOINT_OVERRIDE", "http://localhost:8000")
aws_region = os.getenv("AWS_REGION", "us-west-2")

print(f"Using local DynamoDB endpoint: {dynamodb_endpoint_override}")
dynamodb = boto3.resource(
    "dynamodb", endpoint_url=dynamodb_endpoint_override, region_name=aws_region
)

# Create characters table
print("Creating KidsRewardsCharacters table...")
try:
    characters_table = dynamodb.create_table(
        TableName='KidsRewardsCharacters',
        KeySchema=[
            {
                'AttributeName': 'id',
                'KeyType': 'HASH'  # Partition key
            }
        ],
        AttributeDefinitions=[
            {
                'AttributeName': 'id',
                'AttributeType': 'S'
            }
        ],
        BillingMode='PAY_PER_REQUEST'
    )
    print("✓ Characters table created successfully")
    characters_table.wait_until_exists()
except ClientError as e:
    if e.response['Error']['Code'] == 'ResourceInUseException':
        print("✓ Characters table already exists")
    else:
        print(f"✗ Error creating characters table: {e}")

# Create user_characters table
print("\nCreating KidsRewardsUserCharacters table...")
try:
    user_characters_table = dynamodb.create_table(
        TableName='KidsRewardsUserCharacters',
        KeySchema=[
            {
                'AttributeName': 'user_id',
                'KeyType': 'HASH'  # Partition key
            }
        ],
        AttributeDefinitions=[
            {
                'AttributeName': 'user_id',
                'AttributeType': 'S'
            }
        ],
        BillingMode='PAY_PER_REQUEST'
    )
    print("✓ User characters table created successfully")
    user_characters_table.wait_until_exists()
except ClientError as e:
    if e.response['Error']['Code'] == 'ResourceInUseException':
        print("✓ User characters table already exists")
    else:
        print(f"✗ Error creating user characters table: {e}")

print("\nTables setup complete!")