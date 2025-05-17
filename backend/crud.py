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
PURCHASE_LOGS_TABLE_NAME = os.getenv("PURCHASE_LOGS_TABLE_NAME", "KidsRewardsPurchaseLogs")
CHORES_TABLE_NAME = os.getenv("CHORES_TABLE_NAME", "KidsRewardsChores")
CHORE_LOGS_TABLE_NAME = os.getenv("CHORE_LOGS_TABLE_NAME", "KidsRewardsChoreLogs")

if DYNAMODB_ENDPOINT_OVERRIDE:
    dynamodb = boto3.resource("dynamodb", endpoint_url=DYNAMODB_ENDPOINT_OVERRIDE, region_name=AWS_REGION)
else:
    dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)

# Table resources are now initialized after dynamodb client is configured
users_table = dynamodb.Table(USERS_TABLE_NAME)
store_items_table = dynamodb.Table(STORE_ITEMS_TABLE_NAME)
purchase_logs_table = dynamodb.Table(PURCHASE_LOGS_TABLE_NAME)
chores_table = dynamodb.Table(CHORES_TABLE_NAME)
chore_logs_table = dynamodb.Table(CHORE_LOGS_TABLE_NAME)


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
    except Exception as e:  # Catch potential isoformat or Pydantic errors
        print(f"Error parsing purchase log {log_id} (possibly timestamp or model validation): {e}")
        return None


# --- Chore CRUD ---


def create_chore(chore_in: models.ChoreCreate, parent_id: str) -> models.Chore:
    chore_id = str(uuid.uuid4())
    timestamp = datetime.utcnow()
    chore_data = {
        "id": chore_id,
        "name": chore_in.name,
        "description": chore_in.description,
        "points_value": Decimal(chore_in.points_value),
        "created_by_parent_id": parent_id,
        "created_at": timestamp.isoformat(),
        "updated_at": timestamp.isoformat(),
        "is_active": "true",  # Store as string "true"
    }
    # Remove None values for DynamoDB. If description is None, it will be omitted.
    chore_item = {k: v for k, v in chore_data.items() if v is not None}

    try:
        chores_table.put_item(Item=chore_item)
        # Construct model for response
        return models.Chore(
            id=chore_id,
            name=chore_in.name,
            description=chore_in.description,
            points_value=chore_in.points_value,
            created_by_parent_id=parent_id,
            created_at=timestamp,
            updated_at=timestamp,
            is_active=True,
        )
    except ClientError as e:
        print(f"Error creating chore {chore_in.name}: {e}")
        raise HTTPException(status_code=500, detail="Could not create chore in database.") from e


def get_chore_by_id(chore_id: str) -> Optional[models.Chore]:
    try:
        response = chores_table.get_item(Key={"id": chore_id})
        item = response.get("Item")
        if item:
            return models.Chore(**replace_decimals(item))
        return None
    except ClientError as e:
        print(f"Error getting chore {chore_id}: {e}")
        return None


def get_all_active_chores() -> List[models.Chore]:  # noqa: UP006
    try:
        # This requires a GSI on 'is_active' or a filter expression.
        # For simplicity, scanning and filtering. For production, a GSI is better.
        # GSI: IndexName='ActiveChoresIndex', KeySchema=[{AttributeName: 'is_active', KeyType: 'HASH'}]
        # ProjectionType='ALL'. Query where is_active = True.
        # For now, using a FilterExpression.
        response = chores_table.scan(FilterExpression=boto3.dynamodb.conditions.Attr("is_active").eq("true"))
        items = response.get("Items", [])
        while "LastEvaluatedKey" in response:
            response = chores_table.scan(
                FilterExpression=boto3.dynamodb.conditions.Attr("is_active").eq("true"),
                ExclusiveStartKey=response["LastEvaluatedKey"],
            )
            items.extend(response.get("Items", []))
        return [models.Chore(**replace_decimals(item)) for item in items]
    except ClientError as e:
        print(f"Error scanning active chores: {e}")
        return []


def get_chores_by_parent(parent_id: str) -> List[models.Chore]:  # noqa: UP006
    try:
        # Requires a GSI on 'created_by_parent_id'.
        # GSI: IndexName='ParentChoresIndex', KeySchema=[{AttributeName: 'created_by_parent_id', KeyType: 'HASH'}]
        # ProjectionType='ALL'.
        response = chores_table.query(
            IndexName="ParentChoresIndex",  # Assumed GSI
            KeyConditionExpression=Key("created_by_parent_id").eq(parent_id),
        )
        items = response.get("Items", [])
        return [models.Chore(**replace_decimals(item)) for item in items]
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceNotFoundException":
            print("Warning: GSI 'ParentChoresIndex' not found for chores_table. Falling back to scan.")
            all_chores = get_all_chores_scan_fallback()  # Implement a full scan if GSI fails
            return [c for c in all_chores if c.created_by_parent_id == parent_id]
        print(f"Error getting chores for parent {parent_id}: {e}")
        return []


def get_all_chores_scan_fallback() -> List[models.Chore]:  # noqa: UP006
    try:
        response = chores_table.scan()
        items = response.get("Items", [])
        while "LastEvaluatedKey" in response:
            response = chores_table.scan(ExclusiveStartKey=response["LastEvaluatedKey"])
            items.extend(response.get("Items", []))
        return [models.Chore(**replace_decimals(item)) for item in items]
    except ClientError as e:
        print(f"Error scanning all chores (fallback): {e}")
        return []


def update_chore(chore_id: str, chore_in: models.ChoreCreate, current_parent_id: str) -> Optional[models.Chore]:
    existing_chore = get_chore_by_id(chore_id)
    if not existing_chore:
        return None  # Chore not found
    if existing_chore.created_by_parent_id != current_parent_id:
        raise HTTPException(status_code=403, detail="Not authorized to update this chore.")

    timestamp = datetime.utcnow().isoformat()
    try:
        response = chores_table.update_item(
            Key={"id": chore_id},
            UpdateExpression="SET #n = :n, description = :d, points_value = :pv, updated_at = :ua",
            ExpressionAttributeNames={"#n": "name"},
            ExpressionAttributeValues={
                ":n": chore_in.name,
                ":d": chore_in.description,  # Can be None
                ":pv": Decimal(chore_in.points_value),
                ":ua": timestamp,
                ":cpid": current_parent_id,  # Merged :cpid here
            },
            ConditionExpression="created_by_parent_id = :cpid",  # Ensure parent owns it
            ReturnValues="ALL_NEW",
        )
        updated_attributes = response.get("Attributes")
        if updated_attributes:
            return models.Chore(**replace_decimals(updated_attributes))
        return None
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            raise HTTPException(
                status_code=403, detail="Conditional check failed. Not authorized or chore changed."
            ) from e
        print(f"Error updating chore {chore_id}: {e}")
        return None


def deactivate_chore(chore_id: str, current_parent_id: str) -> Optional[models.Chore]:
    existing_chore = get_chore_by_id(chore_id)
    if not existing_chore:
        return None
    if existing_chore.created_by_parent_id != current_parent_id:
        raise HTTPException(status_code=403, detail="Not authorized to deactivate this chore.")

    timestamp = datetime.utcnow().isoformat()
    try:
        response = chores_table.update_item(
            Key={"id": chore_id},
            UpdateExpression="SET is_active = :ia, updated_at = :ua",
            ExpressionAttributeValues={
                ":ia": "false",  # Store as string "false"
                ":ua": timestamp,
                ":cpid": current_parent_id,  # For condition
            },
            ConditionExpression="created_by_parent_id = :cpid",
            ReturnValues="ALL_NEW",
        )
        updated_attributes = response.get("Attributes")
        if updated_attributes:
            return models.Chore(**replace_decimals(updated_attributes))
        return None
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            raise HTTPException(
                status_code=403, detail="Conditional check failed. Not authorized or chore changed."
            ) from e
        print(f"Error deactivating chore {chore_id}: {e}")
        return None


def delete_chore(chore_id: str, current_parent_id: str) -> bool:
    # Consider implications: what if chore logs exist?
    # For now, direct delete if parent matches.
    existing_chore = get_chore_by_id(chore_id)
    if not existing_chore:
        return False  # Chore not found
    if existing_chore.created_by_parent_id != current_parent_id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this chore.")

    try:
        chores_table.delete_item(
            Key={"id": chore_id},
            ConditionExpression="created_by_parent_id = :cpid",
            ExpressionAttributeValues={":cpid": current_parent_id},
        )
        return True
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            raise HTTPException(
                status_code=403, detail="Conditional check failed. Not authorized or chore changed."
            ) from e
        print(f"Error deleting chore {chore_id}: {e}")
        return False


# --- Chore Log CRUD ---


def create_chore_log_submission(chore_id: str, kid_user: models.User) -> Optional[models.ChoreLog]:
    chore = get_chore_by_id(chore_id)
    if not chore or not chore.is_active:
        raise HTTPException(status_code=404, detail="Active chore not found.")
    if kid_user.role != models.UserRole.KID:
        raise HTTPException(status_code=403, detail="Only kids can submit chores.")

    log_id = str(uuid.uuid4())
    timestamp = datetime.utcnow()

    log_data = {
        "id": log_id,
        "chore_id": chore.id,
        "chore_name": chore.name,
        "kid_id": kid_user.id,  # kid_user.id is username
        "kid_username": kid_user.username,
        "points_value": Decimal(chore.points_value),
        "status": models.ChoreStatus.PENDING_APPROVAL.value,
        "submitted_at": timestamp.isoformat(),
        "reviewed_by_parent_id": None,
        "reviewed_at": None,
    }
    try:
        chore_logs_table.put_item(Item=log_data)
        return models.ChoreLog(
            id=log_id,
            chore_id=chore.id,
            chore_name=chore.name,
            kid_id=kid_user.id,
            kid_username=kid_user.username,
            points_value=chore.points_value,  # int for model
            status=models.ChoreStatus.PENDING_APPROVAL,
            submitted_at=timestamp,
            reviewed_by_parent_id=None,
            reviewed_at=None,
        )
    except ClientError as e:
        print(f"Error creating chore log for kid {kid_user.username}, chore {chore.name}: {e}")
        raise HTTPException(status_code=500, detail="Could not submit chore.") from e


def get_chore_log_by_id(log_id: str) -> Optional[models.ChoreLog]:
    try:
        response = chore_logs_table.get_item(Key={"id": log_id})
        item = response.get("Item")
        if item:
            return models.ChoreLog(**replace_decimals(item))
        return None
    except ClientError as e:
        print(f"Error getting chore log {log_id}: {e}")
        return None


def update_chore_log_status(
    log_id: str,
    new_status: models.ChoreStatus,
    parent_user: models.User,
    # points_to_award: Optional[int] = None # Points are on the chore log itself
) -> Optional[models.ChoreLog]:
    chore_log = get_chore_log_by_id(log_id)
    if not chore_log:
        raise HTTPException(status_code=404, detail="Chore log not found.")
    if chore_log.status not in [models.ChoreStatus.PENDING_APPROVAL]:  # Can only approve/reject pending
        raise HTTPException(
            status_code=400, detail=f"Chore log is not pending approval. Current status: {chore_log.status}"
        )

    # Verify the parent reviewing is the one who created the original chore
    original_chore = get_chore_by_id(chore_log.chore_id)
    if not original_chore or original_chore.created_by_parent_id != parent_user.id:  # parent_user.id is username
        raise HTTPException(
            status_code=403, detail="Not authorized to review this chore log. Chore created by another parent."
        )

    reviewed_at_ts = datetime.utcnow()

    update_expression = "SET #s = :s, reviewed_by_parent_id = :pid, reviewed_at = :rat"
    expression_attribute_values = {
        ":s": new_status.value,
        ":pid": parent_user.id,
        ":rat": reviewed_at_ts.isoformat(),
    }
    expression_attribute_names = {"#s": "status"}

    if new_status == models.ChoreStatus.APPROVED:
        # Award points to the kid
        kid_user_to_update = get_user_by_username(chore_log.kid_username)
        if not kid_user_to_update:
            raise HTTPException(
                status_code=404, detail=f"Kid user {chore_log.kid_username} not found for point update."
            )
        # update_user_points handles adding points
        updated_kid = update_user_points(chore_log.kid_username, chore_log.points_value)
        if not updated_kid:
            # This is a critical failure, points were not awarded.
            # Decide on rollback or error. For now, raise error.
            raise HTTPException(status_code=500, detail="Failed to award points to the kid.")
    elif new_status == models.ChoreStatus.REJECTED:
        pass  # No points awarded

    try:
        response = chore_logs_table.update_item(
            Key={"id": log_id},
            UpdateExpression=update_expression,
            ExpressionAttributeNames=expression_attribute_names,
            ExpressionAttributeValues=expression_attribute_values,
            ReturnValues="ALL_NEW",
        )
        updated_attributes = response.get("Attributes")
        if updated_attributes:
            return models.ChoreLog(**replace_decimals(updated_attributes))
        return None
    except ClientError as e:
        print(f"Error updating chore log {log_id} status: {e}")
        # If points were awarded but this failed, there's an inconsistency.
        # More robust transaction handling might be needed for production (e.g. DynamoDB Transactions).
        return None


def get_chore_logs_by_kid_id(kid_id: str) -> List[models.ChoreLog]:  # noqa: UP006
    try:
        # Requires GSI on 'kid_id' and 'submitted_at' for sorting.
        # GSI: IndexName='KidChoreLogIndex', HashKey='kid_id', RangeKey='submitted_at'
        response = chore_logs_table.query(
            IndexName="KidChoreLogIndex",  # Assumed GSI
            KeyConditionExpression=Key("kid_id").eq(kid_id),
            ScanIndexForward=False,  # Newest first
        )
        items = response.get("Items", [])
        return [models.ChoreLog(**replace_decimals(item)) for item in items]
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceNotFoundException":
            print(f"Warning: GSI 'KidChoreLogIndex' not found. Falling back to scan for kid_id '{kid_id}'.")
            all_logs = get_all_chore_logs_scan_fallback()
            filtered_logs = [log for log in all_logs if log.kid_id == kid_id]
            return sorted(filtered_logs, key=lambda x: x.submitted_at, reverse=True)
        print(f"Error getting chore logs for kid {kid_id}: {e}")
        return []


def get_chore_logs_by_status_for_parent(status: models.ChoreStatus, parent_id: str) -> List[models.ChoreLog]:  # noqa: UP006
    try:
        # This is more complex. We need logs for chores CREATED BY this parent that have a certain status.
        # One way:
        # 1. Get all chores by parent_id.
        # 2. For each chore, query chore_logs by chore_id and status. (Inefficient)
        # Alternative: GSI on chore_logs_table: 'ChoreStatusIndex' (status HASH, submitted_at RANGE)
        # Then filter client-side by checking original_chore.created_by_parent_id.

        # Assuming GSI: IndexName='ChoreLogStatusIndex', HashKey='status', RangeKey='submitted_at'
        response = chore_logs_table.query(
            IndexName="ChoreLogStatusIndex",  # Assumed GSI
            KeyConditionExpression=Key("status").eq(status.value),
            ScanIndexForward=False,  # Newest first
        )
        items = response.get("Items", [])

        # Filter these logs to only include those where the original chore was created by the parent_id
        parent_chore_logs = []
        for item in items:
            log = models.ChoreLog(**replace_decimals(item))
            # This requires a fetch for each chore, which is not ideal.
            # A better approach might be to denormalize created_by_parent_id onto the chore_log itself.
            # For now, let's do the fetch.
            chore = get_chore_by_id(log.chore_id)
            if chore and chore.created_by_parent_id == parent_id:
                parent_chore_logs.append(log)
        return parent_chore_logs
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceNotFoundException":
            print(f"Warning: GSI 'ChoreLogStatusIndex' not found. Falling back to scan for status '{status.value}'.")
            # Fallback: Get all logs, then filter
            all_logs = get_all_chore_logs_scan_fallback()
            filtered_logs = []
            for log in all_logs:
                if log.status == status:
                    chore = get_chore_by_id(log.chore_id)  # Still need this check
                    if chore and chore.created_by_parent_id == parent_id:
                        filtered_logs.append(log)
            return sorted(filtered_logs, key=lambda x: x.submitted_at, reverse=True)
        print(f"Error getting chore logs by status {status.value} for parent {parent_id}: {e}")
        return []


def get_all_chore_logs_scan_fallback() -> List[models.ChoreLog]:  # noqa: UP006
    try:
        response = chore_logs_table.scan()
        items = response.get("Items", [])
        while "LastEvaluatedKey" in response:
            response = chore_logs_table.scan(ExclusiveStartKey=response["LastEvaluatedKey"])
            items.extend(response.get("Items", []))
        return [models.ChoreLog(**replace_decimals(item)) for item in items]
    except ClientError as e:
        print(f"Error scanning all chore logs (fallback): {e}")
        return []

        # It might be beneficial to add 'created_by_parent_id' to ChoreLog items
        # to simplify queries like get_chore_logs_by_status_for_parent.
        # This would be denormalization. If added, update ChoreLog model and creation logic.
