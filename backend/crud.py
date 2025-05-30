import os
import random
import string
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, List, Optional  # noqa: UP035

import boto3
from boto3.dynamodb.conditions import Key
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
REQUESTS_TABLE_NAME = os.getenv("REQUESTS_TABLE_NAME", "KidsRewardsRequests")  # New table for requests
FAMILIES_TABLE_NAME = os.getenv("FAMILIES_TABLE_NAME", "KidsRewardsFamilies")  # New table for families

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
requests_table = dynamodb.Table(REQUESTS_TABLE_NAME)  # New table resource for requests
families_table = dynamodb.Table(FAMILIES_TABLE_NAME)  # New table resource for families


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


# Helper to prepare Python dicts for DynamoDB (convert numbers to Decimal, handle None)
def prepare_item_for_dynamodb(item: Any) -> Any:
    if isinstance(item, dict):
        new_dict = {}
        for k, v in item.items():
            if v is not None:  # Skip None values, DynamoDB doesn't store them well unless explicitly needed
                new_dict[k] = prepare_item_for_dynamodb(v)
        return new_dict
    elif isinstance(item, list):
        new_list = []
        for i in item:
            if i is not None:  # Optionally skip None values in lists too
                new_list.append(prepare_item_for_dynamodb(i))
        return new_list
    elif isinstance(item, (int, float)):
        return Decimal(str(item))
    return item  # For strings, booleans, Decimals, etc.


# --- Family CRUD ---
def create_family(family_in: models.FamilyCreate) -> models.Family:
    family_id = str(uuid.uuid4())
    family_data = {
        "id": family_id,
        "name": family_in.name,
        "invitation_codes": {},  # Initialize empty invitation codes
    }
    try:
        families_table.put_item(Item=prepare_item_for_dynamodb(family_data))
        return models.Family(**family_data)
    except ClientError as e:
        print(f"Error creating family {family_in.name}: {e}")
        raise HTTPException(status_code=500, detail="Could not create family in database.") from e


def get_family_by_id(family_id: str) -> Optional[models.Family]:
    try:
        response = families_table.get_item(Key={"id": family_id})
        item = response.get("Item")
        if item:
            return models.Family(**replace_decimals(item))
        return None
    except ClientError as e:
        print(f"Error getting family {family_id}: {e}")
        return None


# --- Invitation CRUD ---
def generate_invitation_code() -> str:
    """Generate a 6-character alphanumeric code (case-insensitive)"""
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=6))


def create_invitation(family_id: str, invitation_in: models.InvitationCreate, created_by: str) -> models.InvitationInfo:
    """Create a new invitation code for a family"""
    family = get_family_by_id(family_id)
    if not family:
        raise HTTPException(status_code=404, detail="Family not found")

    # Clean up expired invitations first
    clean_expired_invitations(family_id)

    # Check rate limit (max 10 active invitations)
    invitation_codes = family.invitation_codes or {}
    if len(invitation_codes) >= 10:
        raise HTTPException(status_code=429, detail="Too many active invitations (max 10)")

    # Generate unique code
    code = generate_invitation_code()
    while code in invitation_codes:
        code = generate_invitation_code()

    # Create invitation
    now = datetime.utcnow()
    expires = now + timedelta(days=7)

    invitation_data = {
        "role": invitation_in.role.value,
        "expires": expires.isoformat(),
        "created_by": created_by,
        "created_at": now.isoformat(),
    }

    # Update family with new invitation
    try:
        families_table.update_item(
            Key={"id": family_id},
            UpdateExpression="SET invitation_codes.#code = :inv",
            ExpressionAttributeNames={"#code": code},
            ExpressionAttributeValues={":inv": prepare_item_for_dynamodb(invitation_data)},
        )

        return models.InvitationInfo(
            code=code, role=invitation_in.role, expires=expires, created_by=created_by, created_at=now
        )
    except ClientError as e:
        print(f"Error creating invitation: {e}")
        raise HTTPException(status_code=500, detail="Could not create invitation") from e


def validate_invitation(code: str) -> Optional[tuple[str, models.InvitationInfo]]:
    """Validate an invitation code and return (family_id, invitation_info) if valid"""
    if not code or len(code) != 6:
        return None

    code = code.upper()  # Case insensitive

    # Scan all families for the invitation code (this is okay for small scale)
    try:
        response = families_table.scan()
        items = response.get("Items", [])

        for item in items:
            family_id = item.get("id")
            invitation_codes = item.get("invitation_codes", {})

            if code in invitation_codes:
                inv_data = invitation_codes[code]
                expires = datetime.fromisoformat(inv_data["expires"])

                # Check if expired
                if expires < datetime.utcnow():
                    return None

                invitation_info = models.InvitationInfo(
                    code=code,
                    role=models.UserRole(inv_data["role"]),
                    expires=expires,
                    created_by=inv_data["created_by"],
                    created_at=datetime.fromisoformat(inv_data["created_at"]),
                )

                return (family_id, invitation_info)

        return None
    except Exception as e:
        print(f"Error validating invitation: {e}")
        return None


def use_invitation(family_id: str, code: str) -> bool:
    """Mark an invitation as used by removing it from the family"""
    code = code.upper()

    try:
        families_table.update_item(
            Key={"id": family_id},
            UpdateExpression="REMOVE invitation_codes.#code",
            ExpressionAttributeNames={"#code": code},
        )
        return True
    except ClientError as e:
        print(f"Error using invitation: {e}")
        return False


def clean_expired_invitations(family_id: str) -> None:
    """Remove expired invitations from a family"""
    family = get_family_by_id(family_id)
    if not family or not family.invitation_codes:
        return

    now = datetime.utcnow()
    codes_to_remove = []

    for code, inv_data in family.invitation_codes.items():
        expires = datetime.fromisoformat(inv_data["expires"])
        if expires < now:
            codes_to_remove.append(code)

    # Remove expired codes
    for code in codes_to_remove:
        try:
            families_table.update_item(
                Key={"id": family_id},
                UpdateExpression="REMOVE invitation_codes.#code",
                ExpressionAttributeNames={"#code": code},
            )
        except ClientError:
            pass  # Continue even if individual removal fails


def get_family_members(family_id: str) -> List[models.User]:
    """Get all users in a family"""
    try:
        response = users_table.scan(FilterExpression=Key("family_id").eq(family_id))
        items = response.get("Items", [])

        while "LastEvaluatedKey" in response:
            response = users_table.scan(
                FilterExpression=Key("family_id").eq(family_id), ExclusiveStartKey=response["LastEvaluatedKey"]
            )
            items.extend(response.get("Items", []))

        return [models.User(**replace_decimals(item)) for item in items]
    except ClientError as e:
        print(f"Error getting family members: {e}")
        return []


def remove_family_member(family_id: str, username: str) -> bool:
    """Remove a user from a family (set their family_id to None)"""
    user = get_user_by_username(username, family_id=family_id)
    if not user:
        return False

    try:
        users_table.update_item(
            Key={"username": username},
            UpdateExpression="REMOVE family_id",
            ConditionExpression="family_id = :fid",
            ExpressionAttributeValues={":fid": family_id},
        )
        return True
    except ClientError as e:
        print(f"Error removing family member: {e}")
        return False


def assign_user_to_new_family(user_id: str, family_name: str) -> Optional[models.User]:
    """Create a new family and assign the user as the first parent"""
    # Find user by ID
    try:
        response = users_table.scan(FilterExpression=Key("id").eq(user_id))
        items = response.get("Items", [])
        if not items:
            return None

        user_data = items[0]
        username = user_data["username"]

        # Create new family
        new_family = create_family(models.FamilyCreate(name=family_name))

        # Update user with family_id and parent role
        response = users_table.update_item(
            Key={"username": username},
            UpdateExpression="SET family_id = :fid, #r = :role",
            ExpressionAttributeNames={"#r": "role"},
            ExpressionAttributeValues={":fid": new_family.id, ":role": models.UserRole.PARENT.value},
            ReturnValues="ALL_NEW",
        )

        updated_item = response.get("Attributes")
        if updated_item:
            return models.User(**replace_decimals(updated_item))
        return None

    except ClientError as e:
        print(f"Error assigning user to new family: {e}")
        return None


# --- User CRUD ---
def get_user_by_username(username: str, family_id: Optional[str] = None) -> Optional[models.User]:  # Add family_id
    try:
        response = users_table.get_item(Key={"username": username})
        item = response.get("Item")
        if item:
            user = models.User(**replace_decimals(item))
            if family_id and user.family_id and user.family_id != family_id:
                return None  # User found but not in the specified family
            return user
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
    user_id = str(uuid.uuid4())  # Use UUID for user ID

    family_id_to_assign = user_in.family_id
    user_role = models.UserRole.KID  # Default role

    # Handle invitation code
    if user_in.invitation_code:
        if user_in.family_id or user_in.family_name:
            raise HTTPException(status_code=400, detail="Cannot provide invitation code with family_id or family_name.")

        validation_result = validate_invitation(user_in.invitation_code)
        if not validation_result:
            raise HTTPException(status_code=400, detail="Invalid or expired invitation code.")

        family_id_to_assign, invitation_info = validation_result
        user_role = invitation_info.role

        # Use the invitation (remove it)
        if not use_invitation(family_id_to_assign, user_in.invitation_code):
            raise HTTPException(status_code=500, detail="Failed to process invitation.")

    # Handle creating new family
    elif user_in.family_name:
        if user_in.family_id:
            raise HTTPException(status_code=400, detail="Cannot provide both family_id and family_name.")
        new_family = create_family(models.FamilyCreate(name=user_in.family_name))
        family_id_to_assign = new_family.id
        user_role = models.UserRole.PARENT

    # Handle joining existing family by ID (legacy support)
    elif family_id_to_assign:
        existing_family = get_family_by_id(family_id_to_assign)
        if not existing_family:
            raise HTTPException(status_code=404, detail=f"Family with id {family_id_to_assign} not found.")
        user_role = models.UserRole.KID

    # No family specified - create as parent without family (legacy support)
    else:
        user_role = models.UserRole.PARENT
        family_id_to_assign = None

    user_data = {
        "id": user_id,
        "username": user_in.username,
        "hashed_password": hashed_password,
        "role": user_role.value,
        "points": 0 if user_role == models.UserRole.KID else None,
        "family_id": family_id_to_assign,
    }

    user_item = prepare_item_for_dynamodb(user_data)

    try:
        users_table.put_item(Item=user_item)
        user_for_response = models.User(**user_data)
        user_for_response.role = user_role  # Use the enum member for the response
        return user_for_response
    except ClientError as e:
        print(f"Error creating user {user_in.username}: {e}")
        raise HTTPException(status_code=500, detail="Could not create user in database.") from e


def get_user_by_id(user_id: str) -> Optional[models.User]:
    """Get a user by their ID."""
    try:
        response = users_table.scan(FilterExpression=Key("id").eq(user_id))
        items = response.get("Items", [])
        if items:
            return models.User(**replace_decimals(items[0]))
        return None
    except ClientError as e:
        print(f"Error getting user by id {user_id}: {e}")
        return None


def authenticate_user(username: str, password: str) -> Optional[models.User]:
    """Authenticate a user with username and password."""
    user = get_user_by_username(username)
    if not user:
        return None
    if not security.verify_password(password, user.hashed_password):
        return None
    return user


def update_user_points(username: str, points_to_add: int, family_id: str) -> Optional[models.User]:
    user = get_user_by_username(username, family_id=family_id)
    if not user or user.role != models.UserRole.KID or user.family_id != family_id:
        return None

    new_points = (user.points or 0) + points_to_add

    try:
        response = users_table.update_item(
            Key={"username": username},
            UpdateExpression="SET points = :p",
            ConditionExpression="attribute_exists(username) AND family_id = :fid",
            ExpressionAttributeValues={
                ":p": Decimal(new_points),
                ":fid": family_id,
            },
            ReturnValues="ALL_NEW",
        )
        updated_attributes = response.get("Attributes")
        if updated_attributes:
            return models.User(**replace_decimals(updated_attributes))
        return None
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            print(f"Conditional check failed for user {username} in family {family_id}.")
            return None
        print(f"Error updating points for user {username}: {e}")
        return None


def promote_user_to_parent(username: str, family_id: str) -> Optional[models.User]:
    user = get_user_by_username(username, family_id=family_id)
    if not user or user.family_id != family_id:
        return None

    if user.role == models.UserRole.PARENT:
        return user

    try:
        response = users_table.update_item(
            Key={"username": username},
            UpdateExpression="SET #r = :r REMOVE points",
            ConditionExpression="attribute_exists(username) AND family_id = :fid",
            ExpressionAttributeNames={"#r": "role"},
            ExpressionAttributeValues={
                ":r": models.UserRole.PARENT.value,
                ":fid": family_id,
            },
            ReturnValues="ALL_NEW",
        )
        updated_attributes = response.get("Attributes")
        if updated_attributes:
            if "points" in updated_attributes:
                del updated_attributes["points"]
            updated_attributes["points"] = None
            return models.User(**replace_decimals(updated_attributes))
        return None
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            print(f"Conditional check failed promoting user {username} in family {family_id}.")
            return None
        print(f"Error promoting user {username} to parent: {e}")
        return None


def get_all_users(family_id: Optional[str] = None) -> list[models.User]:  # Add family_id filter
    try:
        if family_id:
            response = users_table.scan(FilterExpression=Key("family_id").eq(family_id))
        else:
            response = users_table.scan()

        items = response.get("Items", [])
        while "LastEvaluatedKey" in response:
            if family_id:
                response = users_table.scan(
                    FilterExpression=Key("family_id").eq(family_id),
                    ExclusiveStartKey=response["LastEvaluatedKey"],
                )
            else:
                response = users_table.scan(ExclusiveStartKey=response["LastEvaluatedKey"])
            items.extend(response.get("Items", []))

        replaced_items = [replace_decimals(item) for item in items]
        return [models.User(**item) for item in replaced_items]
    except ClientError as e:
        print(f"Error scanning users: {e}")
        return []


# --- Store Item CRUD ---
def get_store_items(family_id: str) -> list[models.StoreItem]:  # Add family_id filter
    try:
        response = store_items_table.scan(FilterExpression=Key("family_id").eq(family_id))
        items = response.get("Items", [])
        while "LastEvaluatedKey" in response:
            response = store_items_table.scan(
                FilterExpression=Key("family_id").eq(family_id),
                ExclusiveStartKey=response["LastEvaluatedKey"],
            )
            items.extend(response.get("Items", []))
        return [models.StoreItem(**replace_decimals(item)) for item in items]
    except ClientError as e:
        print(f"Error getting store items for family {family_id}: {e}")
        return []


def create_store_item(item_in: models.StoreItemCreate, family_id: str) -> models.StoreItem:
    item_id = str(uuid.uuid4())
    item_data = item_in.model_dump()
    item_data["id"] = item_id
    item_data["family_id"] = family_id

    try:
        store_items_table.put_item(Item=prepare_item_for_dynamodb(item_data))
        return models.StoreItem(**item_data)
    except ClientError as e:
        print(f"Error creating store item {item_in.name} for family {family_id}: {e}")
        raise HTTPException(status_code=500, detail="Could not create store item.") from e


def get_store_item_by_id(item_id: str, family_id: str) -> Optional[models.StoreItem]:
    try:
        response = store_items_table.get_item(Key={"id": item_id})
        item = response.get("Item")
        if item and item.get("family_id") == family_id:
            return models.StoreItem(**replace_decimals(item))
        return None
    except ClientError as e:
        print(f"Error getting store item {item_id} for family {family_id}: {e}")
        return None


def delete_store_item(item_id: str, family_id: str) -> bool:
    try:
        store_items_table.delete_item(
            Key={"id": item_id},
            ConditionExpression="family_id = :fid",
            ExpressionAttributeValues={":fid": family_id},
        )
        return True
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            print(f"Conditional delete failed for item {item_id}, not in family {family_id} or does not exist.")
            return False
        print(f"Error deleting store item {item_id} for family {family_id}: {e}")
        return False


# --- Purchase Log CRUD ---
def create_purchase_log(
    user: models.User,
    item: models.StoreItem,
    family_id: str,  # Ensure purchase is logged for the correct family
) -> models.PurchaseLog:
    if user.family_id != family_id or item.family_id != family_id:
        raise HTTPException(status_code=400, detail="User and item must belong to the same family.")

    log_id = str(uuid.uuid4())
    log_data = {
        "id": log_id,
        "user_id": user.id,
        "username": user.username,
        "item_id": item.id,
        "item_name": item.name,
        "points_spent": item.points_cost,
        "timestamp": datetime.utcnow().isoformat(),
        "status": models.PurchaseStatus.COMPLETED.value,
        "family_id": family_id,
    }
    try:
        purchase_logs_table.put_item(Item=prepare_item_for_dynamodb(log_data))
        log_data_for_model = log_data.copy()
        log_data_for_model["timestamp"] = datetime.fromisoformat(log_data["timestamp"])
        return models.PurchaseLog(**log_data_for_model)
    except ClientError as e:
        print(f"Error creating purchase log for user {user.username}, item {item.name}: {e}")
        raise HTTPException(status_code=500, detail="Could not create purchase log.") from e


def get_purchase_logs_for_user(user_id: str, family_id: str) -> list[models.PurchaseLog]:
    try:
        response = purchase_logs_table.scan(
            FilterExpression=Key("family_id").eq(family_id) & Key("user_id").eq(user_id)
        )
        items = response.get("Items", [])
        while "LastEvaluatedKey" in response:
            response = purchase_logs_table.scan(
                FilterExpression=Key("family_id").eq(family_id) & Key("user_id").eq(user_id),
                ExclusiveStartKey=response["LastEvaluatedKey"],
            )
            items.extend(response.get("Items", []))
        return [models.PurchaseLog(**replace_decimals(item)) for item in items]
    except ClientError as e:
        print(f"Error getting purchase logs for user {user_id} in family {family_id}: {e}")
        return []


def get_all_purchase_logs(family_id: str) -> list[models.PurchaseLog]:  # Filter by family_id
    try:
        response = purchase_logs_table.scan(FilterExpression=Key("family_id").eq(family_id))
        items = response.get("Items", [])
        while "LastEvaluatedKey" in response:
            response = purchase_logs_table.scan(
                FilterExpression=Key("family_id").eq(family_id),
                ExclusiveStartKey=response["LastEvaluatedKey"],
            )
            items.extend(response.get("Items", []))
        return [models.PurchaseLog(**replace_decimals(item)) for item in items]
    except ClientError as e:
        print(f"Error getting all purchase logs for family {family_id}: {e}")
        return []


# --- Chore CRUD ---
def create_chore(chore_in: models.ChoreCreate, family_id: str, parent_id: str) -> models.Chore:
    chore_id = str(uuid.uuid4())
    chore_data = chore_in.model_dump()
    chore_data["id"] = chore_id
    chore_data["family_id"] = family_id
    chore_data["created_by_parent_id"] = parent_id
    chore_data["is_active"] = "true"  # Store as string for GSI
    chore_data["created_at"] = datetime.utcnow().isoformat()
    chore_data["updated_at"] = datetime.utcnow().isoformat()

    try:
        chores_table.put_item(Item=prepare_item_for_dynamodb(chore_data))
        chore_data_for_model = chore_data.copy()
        chore_data_for_model["created_at"] = datetime.fromisoformat(chore_data["created_at"])
        chore_data_for_model["updated_at"] = datetime.fromisoformat(chore_data["updated_at"])
        chore_data_for_model["is_active"] = True  # Convert back to boolean for model
        return models.Chore(**chore_data_for_model)
    except ClientError as e:
        print(f"Error creating chore {chore_in.name} for family {family_id}: {e}")
        raise HTTPException(status_code=500, detail="Could not create chore.") from e


def get_chores(family_id: str, is_active: Optional[bool] = None) -> list[models.Chore]:
    try:
        filter_expressions = [Key("family_id").eq(family_id)]
        if is_active is not None:
            # Convert boolean to string for DynamoDB query
            filter_expressions.append(Key("is_active").eq("true" if is_active else "false"))

        final_filter_expression = filter_expressions[0]
        for i in range(1, len(filter_expressions)):
            final_filter_expression = final_filter_expression & filter_expressions[i]

        response = chores_table.scan(FilterExpression=final_filter_expression)
        items = response.get("Items", [])
        while "LastEvaluatedKey" in response:
            response = chores_table.scan(
                FilterExpression=final_filter_expression,
                ExclusiveStartKey=response["LastEvaluatedKey"],
            )
            items.extend(response.get("Items", []))
        chores = []
        for item in items:
            chore_data = replace_decimals(item)
            # Convert is_active from string to boolean
            if "is_active" in chore_data:
                chore_data["is_active"] = chore_data["is_active"] == "true"
            chores.append(models.Chore(**chore_data))
        return chores
    except ClientError as e:
        print(f"Error getting chores for family {family_id}: {e}")
        return []


def get_chore_by_id(chore_id: str, family_id: str) -> Optional[models.Chore]:
    try:
        response = chores_table.get_item(Key={"id": chore_id})
        item = response.get("Item")
        if item and item.get("family_id") == family_id:
            chore_data = replace_decimals(item)
            # Convert is_active from string to boolean
            if "is_active" in chore_data:
                chore_data["is_active"] = chore_data["is_active"] == "true"
            return models.Chore(**chore_data)
        return None
    except ClientError as e:
        print(f"Error getting chore {chore_id} for family {family_id}: {e}")
        return None


def update_chore(chore_id: str, chore_update: models.ChoreUpdate, family_id: str) -> Optional[models.Chore]:
    existing_chore = get_chore_by_id(chore_id, family_id)
    if not existing_chore:
        return None

    update_expression_parts = []
    expression_attribute_values = {}
    expression_attribute_names = {}

    update_data = chore_update.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        attr_name_placeholder = f"#{key}" if key in ["name", "description"] else key
        expression_attribute_names[attr_name_placeholder] = key

        update_expression_parts.append(f"{attr_name_placeholder} = :{key}")
        # Convert boolean to string for is_active field
        if key == "is_active":
            expression_attribute_values[f":{key}"] = "true" if value else "false"
        else:
            expression_attribute_values[f":{key}"] = value

    if not update_expression_parts:
        return existing_chore

    update_expression_parts.append("updated_at = :updated_at")
    expression_attribute_values[":updated_at"] = datetime.utcnow().isoformat()

    update_expression = "SET " + ", ".join(update_expression_parts)

    try:
        final_expression_attribute_values = prepare_item_for_dynamodb(expression_attribute_values)
        final_expression_attribute_values[":fid_cond"] = family_id

        response = chores_table.update_item(
            Key={"id": chore_id},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=final_expression_attribute_values,
            ExpressionAttributeNames=expression_attribute_names if expression_attribute_names else None,
            ConditionExpression="family_id = :fid_cond",
            ReturnValues="ALL_NEW",
        )

        updated_attributes = response.get("Attributes")
        if updated_attributes:
            chore_data = replace_decimals(updated_attributes)
            # Convert is_active from string to boolean
            if "is_active" in chore_data:
                chore_data["is_active"] = chore_data["is_active"] == "true"
            return models.Chore(**chore_data)
        return None
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            print(f"Conditional update failed for chore {chore_id}, not in family {family_id}.")
            return None
        print(f"Error updating chore {chore_id} for family {family_id}: {e}")
        return None


def delete_chore(chore_id: str, family_id: str) -> bool:
    try:
        chores_table.delete_item(
            Key={"id": chore_id},
            ConditionExpression="family_id = :fid",
            ExpressionAttributeValues={":fid": family_id},
        )
        return True
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            print(f"Conditional delete failed for chore {chore_id}, not in family {family_id} or does not exist.")
            return False
        print(f"Error deleting chore {chore_id} for family {family_id}: {e}")
        return False


# --- Chore Log CRUD ---
def log_chore_completion(
    chore_id: str,
    user_id: str,
    family_id: str,
    completed_by_user_id: str,
) -> Optional[models.ChoreLog]:
    chore = get_chore_by_id(chore_id, family_id)
    kid_user = get_user_by_id(user_id)

    if not chore or not kid_user or kid_user.role != models.UserRole.KID:
        raise HTTPException(status_code=404, detail="Chore or kid user not found, or user is not a kid.")
    # Family validation already done in get_chore_by_id and user must be in same family as caller
    if kid_user.family_id != family_id:
        raise HTTPException(status_code=400, detail="Kid must belong to the same family.")

    # Check for existing pending submissions
    existing_pending = get_pending_chore_logs_for_chore(chore_id, kid_user.id, family_id)
    if existing_pending:
        raise HTTPException(status_code=400, detail="A submission for this chore is already pending approval.")

    log_id = str(uuid.uuid4())
    completion_time = datetime.utcnow()

    log_data = {
        "id": log_id,
        "chore_id": chore_id,
        "chore_name": chore.name,
        "kid_id": kid_user.id,
        "kid_username": kid_user.username,
        "points_value": chore.points_value,
        "status": models.ChoreStatus.PENDING_APPROVAL.value,
        "submitted_at": completion_time.isoformat(),
        "family_id": family_id,
    }

    # Don't award points yet - wait for parent approval

    try:
        chore_logs_table.put_item(Item=prepare_item_for_dynamodb(log_data))
        log_data_for_model = log_data.copy()
        log_data_for_model["submitted_at"] = completion_time
        return models.ChoreLog(**log_data_for_model)
    except ClientError as e:
        print(f"Error logging chore completion for chore {chore_id}, user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Could not log chore completion.") from e


def get_chore_logs_for_user(user_id: str, family_id: str) -> list[models.ChoreLog]:
    try:
        response = chore_logs_table.scan(FilterExpression=Key("family_id").eq(family_id) & Key("kid_id").eq(user_id))
        items = response.get("Items", [])
        while "LastEvaluatedKey" in response:
            response = chore_logs_table.scan(
                FilterExpression=Key("family_id").eq(family_id) & Key("kid_id").eq(user_id),
                ExclusiveStartKey=response["LastEvaluatedKey"],
            )
            items.extend(response.get("Items", []))
        return [models.ChoreLog(**replace_decimals(item)) for item in items]
    except ClientError as e:
        print(f"Error getting chore logs for user {user_id} in family {family_id}: {e}")
        return []


def get_all_chore_logs_for_family(family_id: str) -> list[models.ChoreLog]:
    try:
        response = chore_logs_table.scan(FilterExpression=Key("family_id").eq(family_id))
        items = response.get("Items", [])
        while "LastEvaluatedKey" in response:
            response = chore_logs_table.scan(
                FilterExpression=Key("family_id").eq(family_id),
                ExclusiveStartKey=response["LastEvaluatedKey"],
            )
            items.extend(response.get("Items", []))
        return [models.ChoreLog(**replace_decimals(item)) for item in items]
    except ClientError as e:
        print(f"Error getting all chore logs for family {family_id}: {e}")
        return []


def get_pending_chore_logs_for_chore(chore_id: str, kid_id: str, family_id: str) -> list[models.ChoreLog]:
    """Get pending chore logs for a specific chore and kid"""
    try:
        filter_expression = (
            Key("family_id").eq(family_id) & 
            Key("chore_id").eq(chore_id) & 
            Key("kid_id").eq(kid_id) & 
            Key("status").eq(models.ChoreStatus.PENDING_APPROVAL.value)
        )
        response = chore_logs_table.scan(FilterExpression=filter_expression)
        items = response.get("Items", [])
        while "LastEvaluatedKey" in response:
            response = chore_logs_table.scan(
                FilterExpression=filter_expression,
                ExclusiveStartKey=response["LastEvaluatedKey"],
            )
            items.extend(response.get("Items", []))
        return [models.ChoreLog(**replace_decimals(item)) for item in items]
    except ClientError as e:
        print(f"Error getting pending chore logs for chore {chore_id}, kid {kid_id}: {e}")
        return []


def approve_chore_log(chore_log_id: str, parent_id: str, family_id: str) -> models.ChoreLog:
    """Approve a chore submission and award points"""
    if not chore_log_id:
        raise HTTPException(status_code=400, detail="Chore log ID is required")
    
    try:
        # Get the chore log - use scan since get_item seems to have issues with DynamoDB Local
        print(f"Attempting to get chore log with id: {chore_log_id}")
        
        # Use scan to find the item (less efficient but works with DynamoDB Local)
        scan_response = chore_logs_table.scan(
            FilterExpression=Key("id").eq(chore_log_id)
        )
        
        items = scan_response.get('Items', [])
        if not items:
            raise HTTPException(status_code=404, detail="Chore log not found.")
        
        item = items[0]
        if item.get("family_id") != family_id:
            raise HTTPException(status_code=404, detail="Chore log not found in your family.")
        
        chore_log_data = replace_decimals(item)
        
        # Verify it's pending approval
        if chore_log_data["status"] != models.ChoreStatus.PENDING_APPROVAL.value:
            raise HTTPException(status_code=400, detail="Chore submission is not pending approval.")
        
        # Update the chore log
        update_time = datetime.utcnow()
        update_expression = "SET #status = :status, reviewed_by_parent_id = :parent_id, reviewed_at = :reviewed_at"
        expression_attribute_names = {"#status": "status"}
        expression_attribute_values = {
            ":status": models.ChoreStatus.APPROVED.value,
            ":parent_id": parent_id,
            ":reviewed_at": update_time.isoformat(),
            ":family_id": family_id,
        }
        
        response = chore_logs_table.update_item(
            Key={"id": chore_log_id},
            UpdateExpression=update_expression,
            ExpressionAttributeNames=expression_attribute_names,
            ExpressionAttributeValues=expression_attribute_values,
            ConditionExpression="family_id = :family_id",
            ReturnValues="ALL_NEW",
        )
        
        updated_log = response["Attributes"]
        
        # Award points to the kid
        kid_id = updated_log["kid_id"]
        points_to_award = int(updated_log["points_value"])
        
        # Get current user points using the proper function
        kid_user = get_user_by_id(kid_id)
        if not kid_user:
            raise HTTPException(status_code=404, detail="Kid user not found.")
        
        current_points = int(kid_user.points or 0)
        new_points = current_points + points_to_award
        
        # Update user points using the kid's username (primary key)
        users_table.update_item(
            Key={"username": kid_user.username},
            UpdateExpression="SET points = :points",
            ExpressionAttributeValues={":points": new_points},
        )
        
        # Return the updated chore log
        updated_log_data = replace_decimals(updated_log)
        updated_log_data["reviewed_at"] = update_time
        return models.ChoreLog(**updated_log_data)
        
    except ClientError as e:
        print(f"Error approving chore log {chore_log_id}: {e}")
        raise HTTPException(status_code=500, detail="Could not approve chore submission.") from e


def reject_chore_log(chore_log_id: str, parent_id: str, family_id: str) -> models.ChoreLog:
    """Reject a chore submission"""
    if not chore_log_id:
        raise HTTPException(status_code=400, detail="Chore log ID is required")
    
    try:
        # Get the chore log - use scan since get_item seems to have issues with DynamoDB Local
        print(f"Attempting to reject chore log with id: {chore_log_id}")
        
        # Use scan to find the item (less efficient but works with DynamoDB Local)
        scan_response = chore_logs_table.scan(
            FilterExpression=Key("id").eq(chore_log_id)
        )
        
        items = scan_response.get('Items', [])
        if not items:
            raise HTTPException(status_code=404, detail="Chore log not found.")
        
        item = items[0]
        if item.get("family_id") != family_id:
            raise HTTPException(status_code=404, detail="Chore log not found in your family.")
        
        chore_log_data = replace_decimals(item)
        
        # Verify it's pending approval
        if chore_log_data["status"] != models.ChoreStatus.PENDING_APPROVAL.value:
            raise HTTPException(status_code=400, detail="Chore submission is not pending approval.")
        
        # Update the chore log
        update_time = datetime.utcnow()
        update_expression = "SET #status = :status, reviewed_by_parent_id = :parent_id, reviewed_at = :reviewed_at"
        expression_attribute_names = {"#status": "status"}
        expression_attribute_values = {
            ":status": models.ChoreStatus.REJECTED.value,
            ":parent_id": parent_id,
            ":reviewed_at": update_time.isoformat(),
            ":family_id": family_id,
        }
        
        response = chore_logs_table.update_item(
            Key={"id": chore_log_id},
            UpdateExpression=update_expression,
            ExpressionAttributeNames=expression_attribute_names,
            ExpressionAttributeValues=expression_attribute_values,
            ConditionExpression="family_id = :family_id",
            ReturnValues="ALL_NEW",
        )
        
        updated_log = response["Attributes"]
        
        # Return the updated chore log
        updated_log_data = replace_decimals(updated_log)
        updated_log_data["reviewed_at"] = update_time
        return models.ChoreLog(**updated_log_data)
        
    except ClientError as e:
        print(f"Error rejecting chore log {chore_log_id}: {e}")
        raise HTTPException(status_code=500, detail="Could not reject chore submission.") from e


# --- Request CRUD ---
def _validate_request_prerequisites(
    user: models.User,
    item_id: str,
    family_id: str,
) -> models.StoreItem:
    if user.role != models.UserRole.KID or user.family_id != family_id:
        raise HTTPException(status_code=403, detail="Only kids from the specified family can make requests.")

    store_item = get_store_item_by_id(item_id, family_id)
    if not store_item:
        raise HTTPException(status_code=404, detail="Store item not found in this family.")

    if (user.points or 0) < store_item.points_cost:
        raise HTTPException(status_code=400, detail="Not enough points to request this item.")
    return store_item


def create_request(
    user: models.User,
    item_id: str,
    family_id: str,
) -> models.Request:
    store_item = _validate_request_prerequisites(user, item_id, family_id)

    request_id = str(uuid.uuid4())
    now_iso = datetime.utcnow().isoformat()
    request_data = {
        "id": request_id,
        "user_id": user.id,
        "username": user.username,
        "item_id": store_item.id,
        "item_name": store_item.name,
        "points_cost": store_item.points_cost,
        "family_id": family_id,
        "status": models.RequestStatus.PENDING.value,
        "requested_at": now_iso,
        "updated_at": now_iso,
    }

    try:
        requests_table.put_item(Item=prepare_item_for_dynamodb(request_data))
        request_data_for_model = request_data.copy()
        request_data_for_model["requested_at"] = datetime.fromisoformat(request_data["requested_at"])
        request_data_for_model["updated_at"] = datetime.fromisoformat(request_data["updated_at"])
        return models.Request(**request_data_for_model)
    except ClientError as e:
        print(f"Error creating request for user {user.username}, item {store_item.name}: {e}")
        raise HTTPException(status_code=500, detail="Could not create request.") from e


def get_request_by_id(request_id: str, family_id: str) -> Optional[models.Request]:
    try:
        response = requests_table.get_item(Key={"id": request_id})
        item = response.get("Item")
        if item and item.get("family_id") == family_id:
            return models.Request(**replace_decimals(item))
        return None
    except ClientError as e:
        print(f"Error getting request {request_id} for family {family_id}: {e}")
        return None


def get_requests_for_family(family_id: str, status: Optional[models.RequestStatus] = None) -> list[models.Request]:
    try:
        filter_expressions = [Key("family_id").eq(family_id)]
        if status:
            filter_expressions.append(Key("status").eq(status.value))

        final_filter_expression = filter_expressions[0]
        for i in range(1, len(filter_expressions)):
            final_filter_expression = final_filter_expression & filter_expressions[i]

        response = requests_table.scan(FilterExpression=final_filter_expression)
        items = response.get("Items", [])
        while "LastEvaluatedKey" in response:
            response = requests_table.scan(
                FilterExpression=final_filter_expression,
                ExclusiveStartKey=response["LastEvaluatedKey"],
            )
            items.extend(response.get("Items", []))
        return [models.Request(**replace_decimals(item)) for item in items]
    except ClientError as e:
        print(f"Error getting requests for family {family_id}: {e}")
        return []


def _handle_approved_request(
    request_to_update: models.Request,
    kid_user: models.User,
    family_id: str,
):
    if (kid_user.points or 0) < request_to_update.points_cost:
        raise HTTPException(status_code=400, detail="Kid no longer has enough points for this item.")

    temp_store_item_for_log = models.StoreItem(
        id=request_to_update.item_id,
        name=request_to_update.item_name,
        points_cost=request_to_update.points_cost,
        family_id=family_id,
    )

    updated_kid = update_user_points(kid_user.username, -request_to_update.points_cost, family_id)
    if not updated_kid:
        raise HTTPException(status_code=500, detail="Failed to deduct points for approved request.")

    create_purchase_log(updated_kid, temp_store_item_for_log, family_id)


def update_request_status(
    request_id: str,
    new_status: models.RequestStatus,
    family_id: str,
    parent_user: models.User,
) -> Optional[models.Request]:
    if parent_user.role != models.UserRole.PARENT or parent_user.family_id != family_id:
        raise HTTPException(status_code=403, detail="Only parents from this family can update request status.")

    request_to_update = get_request_by_id(request_id, family_id)
    if not request_to_update:
        raise HTTPException(status_code=404, detail="Request not found in this family.")

    if request_to_update.status not in [models.RequestStatus.PENDING.value, models.RequestStatus.PENDING]:
        raise HTTPException(
            status_code=400,
            detail=f"Request is already in a terminal state: {request_to_update.status}",
        )

    kid_user = get_user_by_username(request_to_update.username, family_id=family_id)
    if not kid_user:
        raise HTTPException(status_code=404, detail="Kid user associated with the request not found.")

    if new_status == models.RequestStatus.APPROVED:
        _handle_approved_request(request_to_update, kid_user, family_id)

    update_expression = "SET #s = :new_status, updated_at = :ua, reviewed_by_user_id = :rbui"
    expression_attribute_values = {
        ":new_status": new_status.value,
        ":ua": datetime.utcnow().isoformat(),
        ":rbui": parent_user.id,
        ":fid_cond": family_id,
    }
    expression_attribute_names = {"#s": "status"}

    try:
        final_expression_attribute_values = prepare_item_for_dynamodb(expression_attribute_values)
        final_expression_attribute_values[":pending_status"] = models.RequestStatus.PENDING.value

        response = requests_table.update_item(
            Key={"id": request_id},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=final_expression_attribute_values,
            ExpressionAttributeNames=expression_attribute_names,
            ConditionExpression="family_id = :fid_cond AND #s = :pending_status",
            ReturnValues="ALL_NEW",
        )

        updated_attributes = response.get("Attributes")
        if updated_attributes:
            return models.Request(**replace_decimals(updated_attributes))
        return None
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            print(
                f"Conditional update failed for request {request_id}. It might not be pending or not in family {family_id}."
            )
            current_request = get_request_by_id(request_id, family_id)
            if current_request and current_request.status != models.RequestStatus.PENDING.value:
                raise HTTPException(
                    status_code=409,
                    detail=f"Request status was already changed. Current status: {current_request.status}",
                )
            raise HTTPException(
                status_code=409,
                detail="Request status could not be updated due to a conflict or it no longer being pending.",
            )

        print(f"Error updating request status for {request_id}: {e}")
        raise HTTPException(status_code=500, detail="Could not update request status.") from e
