import os
import uuid
from typing import Dict, List, Optional, Any
from decimal import Decimal

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

import models
import security

# --- DynamoDB Setup ---
DYNAMODB_ENDPOINT_URL = os.getenv("DYNAMODB_ENDPOINT_URL") # For local testing e.g. 'http://localhost:8000'
AWS_REGION = os.getenv("AWS_REGION", "us-west-2") # Default to us-west-2

if DYNAMODB_ENDPOINT_URL:
    dynamodb = boto3.resource('dynamodb', endpoint_url=DYNAMODB_ENDPOINT_URL, region_name=AWS_REGION)
else:
    dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)

USERS_TABLE_NAME = "KidsRewardsUsers"
STORE_ITEMS_TABLE_NAME = "KidsRewardsStoreItems"

users_table = dynamodb.Table(USERS_TABLE_NAME)
store_items_table = dynamodb.Table(STORE_ITEMS_TABLE_NAME)

# Helper to convert Decimals from DynamoDB to int/float for Pydantic models
def replace_decimals(obj: Any) -> Any:
    if isinstance(obj, list):
        return [replace_decimals(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: replace_decimals(v) for k, v in obj.items()}
    elif isinstance(obj, Decimal):
        if obj % 1 == 0:
            return int(obj)
        else:
            return float(obj)
    return obj

# --- User CRUD ---
def get_user_by_username(username: str) -> Optional[models.User]:
    try:
        response = users_table.get_item(Key={'username': username})
        item = response.get('Item')
        if item:
            return models.User(**replace_decimals(item))
        return None
    except ClientError as e:
        print(f"Error getting user {username}: {e}")
        return None

def create_user(user_in: models.UserCreate) -> models.User:
    hashed_password = security.get_password_hash(user_in.password)
    
    # DynamoDB doesn't have auto-incrementing IDs in the same way SQL does.
    # We use username as the primary key for users.
    # 'id' field in Pydantic model can be same as username or a separate UUID if preferred.
    # For simplicity, let's assume 'id' in the model is the username for now.
    
    user_data = {
        'id': user_in.username, # Using username as ID for simplicity here
        'username': user_in.username,
        'hashed_password': hashed_password,
        'role': user_in.role.value, # Store enum value
        'points': 0 if user_in.role == models.UserRole.KID else None
    }
    # Filter out None values for DynamoDB, especially for 'points' if parent
    user_item = {k: v for k, v in user_data.items() if v is not None}

    try:
        users_table.put_item(Item=user_item)
        # Fetch the created user to return it (or construct from user_item)
        # Pydantic model expects role to be UserRole enum, not string
        return models.User(**user_data)
    except ClientError as e:
        print(f"Error creating user {user_in.username}: {e}")
        # Consider raising a custom exception or re-raising
        raise HTTPException(status_code=500, detail="Could not create user in database.")


def update_user_points(username: str, points_to_add: int) -> Optional[models.User]:
    user = get_user_by_username(username)
    if not user or user.role != models.UserRole.KID:
        return None

    new_points = (user.points or 0) + points_to_add

    try:
        response = users_table.update_item(
            Key={'username': username},
            UpdateExpression="SET points = :p",
            ExpressionAttributeValues={':p': Decimal(new_points)}, # Store numbers as Decimal
            ReturnValues="ALL_NEW" # Get the updated item
        )
        updated_attributes = response.get('Attributes')
        if updated_attributes:
            return models.User(**replace_decimals(updated_attributes))
        return None # Should not happen if update is successful
    except ClientError as e:
        print(f"Error updating points for user {username}: {e}")
        return None

# --- Store Item CRUD ---
def get_store_items() -> List[models.StoreItem]:
    try:
        response = store_items_table.scan()
        items = response.get('Items', [])
        # Add pagination handling if the table grows large
        while 'LastEvaluatedKey' in response:
            response = store_items_table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            items.extend(response.get('Items', []))
        return [models.StoreItem(**replace_decimals(item)) for item in items]
    except ClientError as e:
        print(f"Error scanning store items: {e}")
        return []

def get_store_item_by_id(item_id: str) -> Optional[models.StoreItem]:
    try:
        response = store_items_table.get_item(Key={'id': item_id})
        item = response.get('Item')
        if item:
            return models.StoreItem(**replace_decimals(item))
        return None
    except ClientError as e:
        print(f"Error getting store item {item_id}: {e}")
        return None

def create_store_item(item_in: models.StoreItemCreate) -> models.StoreItem:
    item_id = str(uuid.uuid4()) # Generate a unique ID for the store item
    item_data = {
        'id': item_id,
        'name': item_in.name,
        'description': item_in.description,
        'points_cost': Decimal(item_in.points_cost) # Store numbers as Decimal
    }
    item_item = {k: v for k, v in item_data.items() if v is not None}


    try:
        store_items_table.put_item(Item=item_item)
        return models.StoreItem(**item_data) # Construct from item_data
    except ClientError as e:
        print(f"Error creating store item {item_in.name}: {e}")
        raise HTTPException(status_code=500, detail="Could not create store item in database.")


def update_store_item(item_id: str, item_in: models.StoreItemCreate) -> Optional[models.StoreItem]:
    try:
        response = store_items_table.update_item(
            Key={'id': item_id},
            UpdateExpression="SET #n = :n, description = :d, points_cost = :pc",
            ExpressionAttributeNames={'#n': 'name'}, # 'name' is a reserved keyword
            ExpressionAttributeValues={
                ':n': item_in.name,
                ':d': item_in.description if item_in.description is not None else None, # Handle optional description
                ':pc': Decimal(item_in.points_cost)
            },
            ReturnValues="ALL_NEW"
        )
        updated_attributes = response.get('Attributes')
        if updated_attributes:
            # Ensure description is handled correctly if it's None from DB
            if 'description' not in updated_attributes or updated_attributes['description'] is None:
                 updated_attributes['description'] = None # Pydantic expects None, not missing
            return models.StoreItem(**replace_decimals(updated_attributes))
        return None # Item not found or update failed silently (should be caught by ClientError)
    except ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException': # Or if item doesn't exist
            print(f"Store item {item_id} not found for update.") # Item not found
            return None
        print(f"Error updating store item {item_id}: {e}")
        return None


def delete_store_item(item_id: str) -> bool:
    try:
        # Check if item exists before deleting to provide better feedback, though delete is idempotent
        # For simplicity, we'll rely on DeleteItem's behavior.
        store_items_table.delete_item(Key={'id': item_id})
        return True # Assume success if no error, or add a get_item check
    except ClientError as e:
        print(f"Error deleting store item {item_id}: {e}")
        return False

# Note: The initialize_store_data function is removed as data will be managed in DynamoDB directly.
# You would typically add initial items via the API or AWS console/CLI after tables are created.

# --- Import HTTPException for create_user and create_store_item ---
# This should ideally be at the top of the file, but placing it here to avoid re-reading the whole file
from fastapi import HTTPException