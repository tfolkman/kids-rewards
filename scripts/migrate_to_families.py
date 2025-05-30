#!/usr/bin/env python3
"""
One-time migration script to assign all existing users to the Folkman family.

This script:
1. Creates the "Folkman" family if it doesn't exist
2. Updates all existing users to belong to this family
3. Ensures data integrity

Run this script ONCE after deploying the family feature.
"""

import os
import sys
import uuid
from datetime import datetime

import boto3
from botocore.exceptions import ClientError

# Configuration
DYNAMODB_ENDPOINT = os.getenv("DYNAMODB_ENDPOINT_OVERRIDE")  # For local testing
AWS_REGION = os.getenv("AWS_REGION", "us-west-2")
USERS_TABLE_NAME = os.getenv("USERS_TABLE_NAME", "KidsRewardsUsers")
FAMILIES_TABLE_NAME = os.getenv("FAMILIES_TABLE_NAME", "KidsRewardsFamilies")

# Initialize DynamoDB
if DYNAMODB_ENDPOINT:
    dynamodb = boto3.resource("dynamodb", endpoint_url=DYNAMODB_ENDPOINT, region_name=AWS_REGION)
else:
    dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)

users_table = dynamodb.Table(USERS_TABLE_NAME)
families_table = dynamodb.Table(FAMILIES_TABLE_NAME)


def create_folkman_family():
    """Create the Folkman family if it doesn't exist."""
    family_id = "folkman-family"  # Using a fixed ID for consistency
    
    try:
        # Check if family already exists
        response = families_table.get_item(Key={"id": family_id})
        if "Item" in response:
            print(f"Folkman family already exists with ID: {family_id}")
            return family_id
        
        # Create the family
        family_data = {
            "id": family_id,
            "name": "Folkman",
            "invitation_codes": {},
            "created_at": datetime.utcnow().isoformat()
        }
        
        families_table.put_item(Item=family_data)
        print(f"Created Folkman family with ID: {family_id}")
        return family_id
        
    except ClientError as e:
        print(f"Error creating Folkman family: {e}")
        sys.exit(1)


def migrate_users_to_family(family_id):
    """Update all users without a family_id to belong to the Folkman family."""
    updated_count = 0
    skipped_count = 0
    error_count = 0
    
    try:
        # Scan all users
        response = users_table.scan()
        items = response.get("Items", [])
        
        # Handle pagination
        while "LastEvaluatedKey" in response:
            response = users_table.scan(ExclusiveStartKey=response["LastEvaluatedKey"])
            items.extend(response.get("Items", []))
        
        print(f"Found {len(items)} total users")
        
        # Update each user
        for user in items:
            username = user.get("username")
            current_family_id = user.get("family_id")
            
            if current_family_id:
                print(f"User {username} already has family_id: {current_family_id}, skipping...")
                skipped_count += 1
                continue
            
            try:
                # Update user with family_id
                users_table.update_item(
                    Key={"username": username},
                    UpdateExpression="SET family_id = :fid",
                    ExpressionAttributeValues={":fid": family_id}
                )
                print(f"Updated user {username} with family_id: {family_id}")
                updated_count += 1
                
            except ClientError as e:
                print(f"Error updating user {username}: {e}")
                error_count += 1
        
        print(f"\nMigration Summary:")
        print(f"- Total users: {len(items)}")
        print(f"- Updated: {updated_count}")
        print(f"- Skipped (already had family): {skipped_count}")
        print(f"- Errors: {error_count}")
        
    except ClientError as e:
        print(f"Error scanning users: {e}")
        sys.exit(1)


def main():
    """Main migration function."""
    print("Starting family migration...")
    print(f"Using tables: {USERS_TABLE_NAME}, {FAMILIES_TABLE_NAME}")
    
    # Step 1: Create Folkman family
    family_id = create_folkman_family()
    
    # Step 2: Migrate users
    migrate_users_to_family(family_id)
    
    print("\nMigration completed successfully!")
    print("\nNext steps:")
    print("1. Deploy the updated backend code")
    print("2. Test the invitation system")
    print("3. Update the frontend to support invitations")


if __name__ == "__main__":
    # Confirm before running
    print("This will migrate all users without a family to the 'Folkman' family.")
    response = input("Are you sure you want to continue? (yes/no): ")
    
    if response.lower() == "yes":
        main()
    else:
        print("Migration cancelled.")