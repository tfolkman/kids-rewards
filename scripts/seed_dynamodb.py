import argparse
import json
import os
import boto3
from botocore.exceptions import ClientError
from decimal import Decimal
from backend.security import get_password_hash  # Import hashing function
from backend.models import PurchaseStatus  # Import PurchaseStatus enum
from datetime import datetime, timedelta
import uuid


# Helper function to convert float/int to Decimal for DynamoDB
def convert_to_decimal(obj):
    if isinstance(obj, list):
        return [convert_to_decimal(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: convert_to_decimal(v) for k, v in obj.items()}
    elif isinstance(obj, (float, int)):
        return Decimal(str(obj))
    return obj


def load_seed_data(file_path: str) -> list:
    """Loads seed data from a JSON file."""
    try:
        with open(file_path, "r") as f:
            data = json.load(f)
            return convert_to_decimal(data)  # Convert numbers to Decimal
    except FileNotFoundError:
        print(f"Error: Seed data file not found at {file_path}")
        return []
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {file_path}")
        return []


def seed_table(table_name: str, data: list, dynamodb_resource):
    """Seeds the specified DynamoDB table with the provided data."""
    try:
        table = dynamodb_resource.Table(table_name)
        print(f"Seeding table: {table_name}")
        for item in data:
            try:
                table.put_item(Item=item)
                print(f"  Put item: {item}")
            except ClientError as e:
                print(f"  Error putting item {item}: {e}")
        print(f"Finished seeding table: {table_name}")
    except ClientError as e:
        print(f"Error accessing table {table_name}: {e}")


def main():
    parser = argparse.ArgumentParser(description="Seed DynamoDB with initial data.")
    parser.add_argument(
        "--environment",
        type=str,
        required=True,
        help="The environment to seed (e.g., local, staging, prod)",
    )
    parser.add_argument("--users-table", type=str, help="Override the users table name")
    parser.add_argument(
        "--store-items-table", type=str, help="Override the store items table name"
    )
    parser.add_argument(
        "--purchase-logs-table", type=str, help="Override the purchase logs table name"
    )

    args = parser.parse_args()

    # --- DynamoDB Setup ---
    # Check for local endpoint override
    dynamodb_endpoint_override = os.getenv("DYNAMODB_ENDPOINT_OVERRIDE")
    aws_region = os.getenv("AWS_REGION", "us-west-2")  # Default to us-west-2

    if dynamodb_endpoint_override:
        print(f"Using local DynamoDB endpoint: {dynamodb_endpoint_override}")
        dynamodb = boto3.resource(
            "dynamodb", endpoint_url=dynamodb_endpoint_override, region_name=aws_region
        )
    else:
        print(f"Using AWS region: {aws_region}")
        dynamodb = boto3.resource("dynamodb", region_name=aws_region)

    # --- Table Names ---
    # Use provided table names or default based on environment (if not overridden)
    # Note: For staging/prod, table names will likely be determined by CloudFormation outputs
    # This script assumes you'll pass the correct names via arguments or environment variables
    # Use environment variables if args are not provided, then default based on environment
    users_table_name = (
        args.users_table
        or os.getenv("USERS_TABLE_NAME")
        or f"{args.environment}-KidsRewardsUsers"
    )
    store_items_table_name = (
        args.store_items_table
        or os.getenv("STORE_ITEMS_TABLE_NAME")
        or f"{args.environment}-KidsRewardsStoreItems"
    )
    purchase_logs_table_name = (
        args.purchase_logs_table
        or os.getenv("PURCHASE_LOGS_TABLE_NAME")
        or f"{args.environment}-KidsRewardsPurchaseLogs"
    )

    # --- Load and Seed Data ---
    seed_data_dir = "seed-data"

    # --- Load and Seed Data ---
    seed_data_dir = "seed-data"

    # Define test users with plain text passwords
    test_users = [
        {
            "username": "testkid",
            "password": "password123",
            "role": "kid",
            "id": "testkid",
            "points": 100,
        },
        {
            "username": "testparent",
            "password": "password456",
            "role": "parent",
            "id": "testparent",
        },
    ]

    # Prepare user data with hashed passwords
    users_to_seed = []
    for user in test_users:
        hashed_password = get_password_hash(user["password"])
        user_item = {
            "id": user["id"],  # Add id field
            "username": user["username"],
            "hashed_password": hashed_password,
            "role": user["role"],  # Role is now lowercase
        }
        if "points" in user:
            user_item["points"] = Decimal(
                str(user["points"])
            )  # Ensure points is Decimal
        else:  # For parents, ensure points is not set or is None if your model expects it
            # If points should explicitly be absent for parents in DB:
            pass  # Do not add points field for parent
            # If points should be null for parents in DB (and model handles Optional[int]):
            # user_item["points"] = None # or handle as Decimal(0) if that's the convention
        users_to_seed.append(user_item)

    # Seed Users Table
    if users_to_seed:
        seed_table(users_table_name, users_to_seed, dynamodb)

    # Seed Store Items Table
    store_items_data_file = os.path.join(seed_data_dir, "store_items.json")
    store_items_data = load_seed_data(store_items_data_file)
    if store_items_data:
        seed_table(store_items_table_name, store_items_data, dynamodb)

    # --- Seed Purchase Logs Table ---
    # Ensure users and items are seeded first to get valid IDs/names
    if users_to_seed and store_items_data:
        purchase_logs_to_seed = []
        kid_user = next((u for u in users_to_seed if u["username"] == "testkid"), None)

        if kid_user and store_items_data:
            # Pending request
            purchase_logs_to_seed.append(
                {
                    "id": str(uuid.uuid4()),
                    "user_id": kid_user["id"],
                    "username": kid_user["username"],
                    "item_id": store_items_data[0]["id"],  # First item
                    "item_name": store_items_data[0]["name"],
                    "points_spent": Decimal(str(store_items_data[0]["points_cost"])),
                    "timestamp": (datetime.utcnow() - timedelta(days=1)).isoformat(),
                    "status": PurchaseStatus.PENDING.value,
                }
            )
            # Approved request
            if len(store_items_data) > 1:
                purchase_logs_to_seed.append(
                    {
                        "id": str(uuid.uuid4()),
                        "user_id": kid_user["id"],
                        "username": kid_user["username"],
                        "item_id": store_items_data[1]["id"],  # Second item
                        "item_name": store_items_data[1]["name"],
                        "points_spent": Decimal(
                            str(store_items_data[1]["points_cost"])
                        ),
                        "timestamp": (
                            datetime.utcnow() - timedelta(days=2)
                        ).isoformat(),
                        "status": PurchaseStatus.APPROVED.value,
                    }
                )
            # Rejected request
            if len(store_items_data) > 2:
                purchase_logs_to_seed.append(
                    {
                        "id": str(uuid.uuid4()),
                        "user_id": kid_user["id"],
                        "username": kid_user["username"],
                        "item_id": store_items_data[2]["id"],  # Third item
                        "item_name": store_items_data[2]["name"],
                        "points_spent": Decimal(
                            str(store_items_data[2]["points_cost"])
                        ),
                        "timestamp": (
                            datetime.utcnow() - timedelta(hours=5)
                        ).isoformat(),
                        "status": PurchaseStatus.REJECTED.value,
                    }
                )

        if purchase_logs_to_seed:
            seed_table(purchase_logs_table_name, purchase_logs_to_seed, dynamodb)


if __name__ == "__main__":
    main()
