import os
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, List, Optional  # noqa: UP035

import boto3
from boto3.dynamodb.conditions import Key  # Adding Key and Attr
from botocore.exceptions import ClientError
from fastapi import HTTPException

import models
import security

# --- DynamoDB Setup ---
DYNAMODB_ENDPOINT_OVERRIDE = os.getenv("DYNAMODB_ENDPOINT_OVERRIDE")  # For local testing e.g. 'http://localhost:8000'
AWS_REGION = os.getenv("AWS_REGION", "us-west-2")  # Default to us-west-2

# These should be defined regardless of local or deployed environment
USERS_TABLE_NAME = os.getenv("USERS_TABLE_NAME", "KidsRewardsUsers")  # Default for safety, but should be set by SAM
STORE_ITEMS_TABLE_NAME = os.getenv("STORE_ITEMS_TABLE_NAME", "KidsRewardsStoreItems")  # Default for safety
PURCHASE_LOGS_TABLE_NAME = os.getenv("PURCHASE_LOGS_TABLE_NAME", "KidsRewardsPurchaseLogs")  # New table

if DYNAMODB_ENDPOINT_OVERRIDE:
    dynamodb = boto3.resource("dynamodb", endpoint_url=DYNAMODB_ENDPOINT_OVERRIDE, region_name=AWS_REGION)
else:
    dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)

# Table resources are now initialized after dynamodb client is configured
users_table = dynamodb.Table(USERS_TABLE_NAME)
store_items_table = dynamodb.Table(STORE_ITEMS_TABLE_NAME)
purchase_logs_table = dynamodb.Table(PURCHASE_LOGS_TABLE_NAME)  # New table resource


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
        response = users_table.get_item(Key={"username": username})
        item = response.get("Item")
        if item:
            return models.User(**replace_decimals(item))
        return None
    except ClientError as e:
        print(f"Error getting user {username}: {e}")
        return None


def create_user(user_in: models.UserCreate) -> models.User:
    if len(user_in.username) < 3:
        raise HTTPException(status_code=400, detail="Username must be at least 3 characters long.")
    if len(user_in.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters long.")

    hashed_password = security.get_password_hash(user_in.password)

    # DynamoDB doesn't have auto-incrementing IDs in the same way SQL does.
    # We use username as the primary key for users.
    # 'id' field in Pydantic model can be same as username or a separate UUID if preferred.
    # For simplicity, let's assume 'id' in the model is the username for now.

    user_data = {
        "id": user_in.username,  # Using username as ID
        "username": user_in.username,
        "hashed_password": hashed_password,
        "role": models.UserRole.KID.value,  # Always create as KID
        "points": 0,  # Kids always start with 0 points
    }
    # All fields are now non-optional for the initial DynamoDB item
    user_item = user_data

    try:
        users_table.put_item(Item=user_item)
        # Construct the User model for return, ensuring role is the enum type
        user_for_response = models.User(
            id=user_data["id"],
            username=user_data["username"],
            hashed_password=user_data["hashed_password"],
            role=models.UserRole.KID,  # Use the enum member directly
            points=user_data["points"],
        )
        return user_for_response
    except ClientError as e:
        print(f"Error creating user {user_in.username}: {e}")
        # Consider raising a custom exception or re-raising
        raise HTTPException(status_code=500, detail="Could not create user in database.") from e


def update_user_points(username: str, points_to_add: int) -> Optional[models.User]:
    user = get_user_by_username(username)
    if not user or user.role != models.UserRole.KID:
        return None

    new_points = (user.points or 0) + points_to_add

    try:
        response = users_table.update_item(
            Key={"username": username},
            UpdateExpression="SET points = :p",
            ExpressionAttributeValues={":p": Decimal(new_points)},  # Store numbers as Decimal
            ReturnValues="ALL_NEW",  # Get the updated item
        )
        updated_attributes = response.get("Attributes")
        if updated_attributes:
            return models.User(**replace_decimals(updated_attributes))
        return None  # Should not happen if update is successful
    except ClientError as e:
        print(f"Error updating points for user {username}: {e}")
        return None


def promote_user_to_parent(username: str) -> Optional[models.User]:
    user = get_user_by_username(username)
    if not user:
        return None  # User not found

    if user.role == models.UserRole.PARENT:
        return user  # Already a parent

    try:
        response = users_table.update_item(
            Key={"username": username},
            UpdateExpression="SET #r = :r REMOVE points",  # Set role to parent and remove points attribute
            ExpressionAttributeNames={"#r": "role"},  # 'role' is not a reserved keyword but good practice
            ExpressionAttributeValues={":r": models.UserRole.PARENT.value},
            ReturnValues="ALL_NEW",
        )
        updated_attributes = response.get("Attributes")
        if updated_attributes:
            # Ensure points is None for parent role in the returned model
            if "points" in updated_attributes:  # Should have been removed by REMOVE
                del updated_attributes["points"]
            updated_attributes["points"] = None  # Explicitly set to None for Pydantic model
            return models.User(**replace_decimals(updated_attributes))
        return None
    except ClientError as e:
        print(f"Error promoting user {username} to parent: {e}")
        return None


def get_all_users() -> list[models.User]:
    try:
        response = users_table.scan()
        items = response.get("Items", [])
        # Add pagination handling if the table grows large
        while "LastEvaluatedKey" in response:
            response = users_table.scan(ExclusiveStartKey=response["LastEvaluatedKey"])
            items.extend(response.get("Items", []))
        print(f"Raw data from DynamoDB: {items}")
        replaced_items = [replace_decimals(item) for item in items]
        print(f"Data after replace_decimals: {replaced_items}")
        return [models.User(**item) for item in replaced_items]
    except ClientError as e:
        print(f"Error scanning users: {e}")
        return []


# --- Store Item CRUD ---
def get_store_items() -> list[models.StoreItem]:
    try:
        response = store_items_table.scan()
        items = response.get("Items", [])
        # Add pagination handling if the table grows large
        while "LastEvaluatedKey" in response:
            response = store_items_table.scan(ExclusiveStartKey=response["LastEvaluatedKey"])
            items.extend(response.get("Items", []))
        return [models.StoreItem(**replace_decimals(item)) for item in items]
    except ClientError as e:
        print(f"Error scanning store items: {e}")
        return []


def get_store_item_by_id(item_id: str) -> Optional[models.StoreItem]:
    try:
        response = store_items_table.get_item(Key={"id": item_id})
        item = response.get("Item")
        if item:
            return models.StoreItem(**replace_decimals(item))
        return None
    except ClientError as e:
        print(f"Error getting store item {item_id}: {e}")
        return None


def create_store_item(item_in: models.StoreItemCreate) -> models.StoreItem:
    item_id = str(uuid.uuid4())  # Generate a unique ID for the store item
    item_data = {
        "id": item_id,
        "name": item_in.name,
        "description": item_in.description,
        "points_cost": Decimal(item_in.points_cost),  # Store numbers as Decimal
    }
    item_item = {k: v for k, v in item_data.items() if v is not None}

    try:
        store_items_table.put_item(Item=item_item)
        return models.StoreItem(**item_data)  # Construct from item_data
    except ClientError as e:
        print(f"Error creating store item {item_in.name}: {e}")
        raise HTTPException(status_code=500, detail="Could not create store item in database.") from e


def update_store_item(item_id: str, item_in: models.StoreItemCreate) -> Optional[models.StoreItem]:
    try:
        response = store_items_table.update_item(
            Key={"id": item_id},
            UpdateExpression="SET #n = :n, description = :d, points_cost = :pc",
            ExpressionAttributeNames={"#n": "name"},  # 'name' is a reserved keyword
            ExpressionAttributeValues={
                ":n": item_in.name,
                ":d": item_in.description if item_in.description is not None else None,  # Handle optional description
                ":pc": Decimal(item_in.points_cost),
            },
            ReturnValues="ALL_NEW",
        )
        updated_attributes = response.get("Attributes")
        if updated_attributes:
            # Ensure description is handled correctly if it's None from DB
            if "description" not in updated_attributes or updated_attributes["description"] is None:
                updated_attributes["description"] = None  # Pydantic expects None, not missing
            return models.StoreItem(**replace_decimals(updated_attributes))
        return None  # Item not found or update failed silently (should be caught by ClientError)
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":  # Or if item doesn't exist
            print(f"Store item {item_id} not found for update.")  # Item not found
            return None
        print(f"Error updating store item {item_id}: {e}")
        return None


def delete_store_item(item_id: str) -> bool:
    try:
        # Check if item exists before deleting to provide better feedback, though delete is idempotent
        # For simplicity, we'll rely on DeleteItem's behavior.
        store_items_table.delete_item(Key={"id": item_id})
        return True  # Assume success if no error, or add a get_item check
    except ClientError as e:
        print(f"Error deleting store item {item_id}: {e}")
        return False


# --- Import HTTPException for create_user and create_store_item ---
# This should ideally be at the top of the file, but placing it here to avoid re-reading the whole file


# --- Purchase Log CRUD ---


def create_purchase_log(log_in: models.PurchaseLogCreate) -> models.PurchaseLog:
    log_id = str(uuid.uuid4())
    log_data = {
        "id": log_id,
        "user_id": log_in.user_id,
        "username": log_in.username,
        "item_id": log_in.item_id,
        "item_name": log_in.item_name,
        "points_spent": Decimal(log_in.points_spent),  # Store as Decimal
        "timestamp": log_in.timestamp.isoformat(),  # Store ISO format string
        "status": log_in.status.value,
    }
    try:
        purchase_logs_table.put_item(Item=log_data)
        # Construct the model for response, ensuring correct types
        return models.PurchaseLog(
            id=log_id,
            user_id=log_in.user_id,
            username=log_in.username,
            item_id=log_in.item_id,
            item_name=log_in.item_name,
            points_spent=log_in.points_spent,  # Keep as int for Pydantic model
            timestamp=log_in.timestamp,  # Keep as datetime for Pydantic model
            status=log_in.status,
        )
    except ClientError as e:
        print(f"Error creating purchase log for user {log_in.username}, item {log_in.item_name}: {e}")
        raise HTTPException(status_code=500, detail="Could not create purchase log in database.") from e


def get_purchase_logs_by_user_id(user_id: str) -> List[models.PurchaseLog]:  # noqa: UP006
    try:
        # This query assumes 'user_id' is a Global Secondary Index (GSI) on the purchase_logs_table
        # If not, you'd need to scan and filter, which is less efficient for large tables.
        # For now, let's assume a GSI 'UserIdIndex' with 'user_id' as the hash key.
        # If you don't have a GSI, you might need to use a scan or reconsider the query.
        # A more common pattern might be to query by username if that's indexed.
        # Let's use a GSI named 'UserIdTimestampIndex' with user_id as HASH and timestamp as RANGE for sorting.
        response = purchase_logs_table.query(
            IndexName="UserIdTimestampIndex",  # Assuming this GSI exists
            KeyConditionExpression=Key("user_id").eq(user_id),
            ScanIndexForward=False,  # Sort by timestamp descending (newest first)
        )
        items = response.get("Items", [])
        return [models.PurchaseLog(**replace_decimals(item)) for item in items]
    except ClientError as e:
        # Handle case where GSI might not exist or other errors
        if e.response["Error"]["Code"] == "ResourceNotFoundException":
            print("Warning: GSI 'UserIdTimestampIndex' not found for purchase_logs_table. Falling back to scan.")
            # Fallback to scan if GSI doesn't exist (less efficient)
            return get_all_purchase_logs(filter_user_id=user_id)
        print(f"Error getting purchase logs for user_id {user_id}: {e}")
        return []


def get_all_purchase_logs(filter_user_id: Optional[str] = None) -> List[models.PurchaseLog]:  # noqa: UP006
    try:
        scan_kwargs = {}
        if filter_user_id:
            scan_kwargs["FilterExpression"] = Key("user_id").eq(filter_user_id)

        response = purchase_logs_table.scan(**scan_kwargs)
        items = response.get("Items", [])
        while "LastEvaluatedKey" in response:
            scan_kwargs["ExclusiveStartKey"] = response["LastEvaluatedKey"]
            response = purchase_logs_table.scan(**scan_kwargs)
            items.extend(response.get("Items", []))

        # Sort by timestamp client-side if not using a query with sort key
        # DynamoDB scan doesn't guarantee order unless you sort after fetching
        parsed_items = [models.PurchaseLog(**replace_decimals(item)) for item in items]
        parsed_items.sort(key=lambda x: x.timestamp, reverse=True)  # Sort newest first
        return parsed_items
    except ClientError as e:
        print(f"Error scanning all purchase logs: {e}")
        return []


def get_purchase_logs_by_status(status: models.PurchaseStatus) -> List[models.PurchaseLog]:  # noqa: UP006
    try:
        # This query assumes 'status' is a Global Secondary Index (GSI) on the purchase_logs_table
        # For example, a GSI named 'StatusTimestampIndex' with 'status' as HASH and 'timestamp' as RANGE.
        response = purchase_logs_table.query(
            IndexName="StatusTimestampIndex",  # Assuming this GSI exists
            KeyConditionExpression=Key("status").eq(status.value),
            ScanIndexForward=False,  # Sort by timestamp descending (newest first)
        )
        items = response.get("Items", [])
        return [models.PurchaseLog(**replace_decimals(item)) for item in items]
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceNotFoundException":
            print(f"Warning: GSI 'StatusTimestampIndex' not found. Falling back to scan for status '{status.value}'.")
            # Fallback to scan if GSI doesn't exist (less efficient)
            all_logs = get_all_purchase_logs()
            return sorted([log for log in all_logs if log.status == status], key=lambda x: x.timestamp, reverse=True)
        print(f"Error getting purchase logs by status {status.value}: {e}")
        return []


def update_purchase_log_status(log_id: str, new_status: models.PurchaseStatus) -> Optional[models.PurchaseLog]:
    try:
        response = purchase_logs_table.update_item(
            Key={"id": log_id},
            UpdateExpression="SET #s = :s",
            ExpressionAttributeNames={"#s": "status"},
            ExpressionAttributeValues={":s": new_status.value},
            ReturnValues="ALL_NEW",
        )
        updated_attributes = response.get("Attributes")
        if updated_attributes:
            return models.PurchaseLog(**replace_decimals(updated_attributes))
        return None  # Log not found or update failed
    except ClientError as e:
        print(f"Error updating status for purchase log {log_id}: {e}")
        return None


def get_purchase_log_by_id(log_id: str) -> Optional[models.PurchaseLog]:
    try:
        response = purchase_logs_table.get_item(Key={"id": log_id})
        item = response.get("Item")
        if item:
            # Ensure timestamp is parsed correctly if stored as string
            if isinstance(item.get("timestamp"), str):
                item["timestamp"] = datetime.fromisoformat(item["timestamp"])
            return models.PurchaseLog(**replace_decimals(item))
        return None
    except ClientError as e:
        print(f"Error getting purchase log {log_id}: {e}")
        return None
    except Exception as e:  # Catch potential isoformat errors
        print(f"Error parsing purchase log {log_id} (possibly timestamp): {e}")
        return None
