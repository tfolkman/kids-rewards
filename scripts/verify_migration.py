#!/usr/bin/env python3
"""
Verify the family migration by checking DynamoDB tables.
"""

import os
import boto3
from botocore.exceptions import ClientError

# Configuration
DYNAMODB_ENDPOINT = os.getenv("DYNAMODB_ENDPOINT_OVERRIDE", "http://localhost:8000")
AWS_REGION = os.getenv("AWS_REGION", "us-west-2")
USERS_TABLE_NAME = os.getenv("USERS_TABLE_NAME", "KidsRewardsUsers")
FAMILIES_TABLE_NAME = os.getenv("FAMILIES_TABLE_NAME", "KidsRewardsFamilies")

# Set dummy credentials for local DynamoDB
if DYNAMODB_ENDPOINT:
    os.environ["AWS_ACCESS_KEY_ID"] = "dummy"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "dummy"

# Initialize DynamoDB
dynamodb = boto3.resource("dynamodb", endpoint_url=DYNAMODB_ENDPOINT, region_name=AWS_REGION)
users_table = dynamodb.Table(USERS_TABLE_NAME)
families_table = dynamodb.Table(FAMILIES_TABLE_NAME)


def verify_migration():
    print(f"Checking migration results...")
    print(f"DynamoDB endpoint: {DYNAMODB_ENDPOINT}")
    print(f"Users table: {USERS_TABLE_NAME}")
    print(f"Families table: {FAMILIES_TABLE_NAME}")
    print("-" * 50)
    
    # Check Folkman family
    try:
        response = families_table.get_item(Key={"id": "folkman-family"})
        family = response.get("Item")
        if family:
            print(f"✓ Folkman family exists:")
            print(f"  - ID: {family['id']}")
            print(f"  - Name: {family['name']}")
            print(f"  - Invitation codes: {len(family.get('invitation_codes', {}))}")
        else:
            print("✗ Folkman family not found!")
    except Exception as e:
        print(f"✗ Error checking family: {e}")
    
    print("-" * 50)
    
    # Check users
    try:
        response = users_table.scan()
        users = response.get("Items", [])
        
        # Handle pagination
        while "LastEvaluatedKey" in response:
            response = users_table.scan(ExclusiveStartKey=response["LastEvaluatedKey"])
            users.extend(response.get("Items", []))
        
        print(f"Total users: {len(users)}")
        
        # Count users by family
        family_counts = {}
        no_family_users = []
        
        for user in users:
            family_id = user.get("family_id")
            if family_id:
                family_counts[family_id] = family_counts.get(family_id, 0) + 1
            else:
                no_family_users.append(user["username"])
        
        print(f"\nUsers by family:")
        for family_id, count in family_counts.items():
            print(f"  - {family_id}: {count} users")
        
        if no_family_users:
            print(f"\nUsers without family: {len(no_family_users)}")
            for username in no_family_users[:5]:  # Show first 5
                print(f"  - {username}")
            if len(no_family_users) > 5:
                print(f"  ... and {len(no_family_users) - 5} more")
        else:
            print(f"\n✓ All users have been assigned to families!")
            
    except Exception as e:
        print(f"✗ Error checking users: {e}")


if __name__ == "__main__":
    verify_migration()