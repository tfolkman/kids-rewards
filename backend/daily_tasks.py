"""
Daily scheduled task handler for automatic Spike feeding task generation.

This Lambda function runs daily at 2 AM Mountain Time (9 AM UTC) to automatically
generate Spike feeding tasks for the next 7 days.
"""

import os
import sys
from datetime import datetime

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

import crud
from pet_care import generate_spike_feeding_tasks


def lambda_handler(event, context):
    """
    Lambda handler for daily automatic task generation.

    Runs daily to generate Spike feeding tasks for the next 7 days.
    Skips dates that already have tasks to avoid duplicates.

    Args:
        event: Lambda event object (from CloudWatch Events)
        context: Lambda context object

    Returns:
        dict: Response with status code and message
    """
    try:
        print(f"[{datetime.utcnow().isoformat()}] Starting daily Spike feeding task generation")

        # Get parent ID from environment variable
        # This should be set in template.yaml
        parent_id = os.environ.get("SPIKE_PARENT_ID")

        if not parent_id:
            error_msg = "SPIKE_PARENT_ID environment variable not set"
            print(f"ERROR: {error_msg}")
            return {"statusCode": 500, "body": error_msg}

        print(f"Using parent ID: {parent_id}")

        # Get all parent's pets
        parent_pets = crud.get_pets_by_parent_id(parent_id)
        print(f"Found {len(parent_pets)} pets for parent")

        # Find Spike (case-insensitive)
        spike = None
        for pet in parent_pets:
            if pet.name.lower() == "spike":
                spike = pet
                break

        if not spike:
            error_msg = f"Spike not found in parent's pets. Available pets: {[p.name for p in parent_pets]}"
            print(f"WARNING: {error_msg}")
            return {"statusCode": 404, "body": error_msg}

        print(f"Found Spike: {spike.id} (name: {spike.name})")

        # Get existing "Feed Spike" task dates to avoid duplicates
        all_spike_tasks = crud.get_tasks_by_pet_id(spike.id)
        existing_dates = {task.due_date.date() for task in all_spike_tasks if task.task_name == "Feed Spike"}

        print(f"Found {len(all_spike_tasks)} total tasks for Spike, {len(existing_dates)} are feeding tasks")

        # Generate tasks for next 7 days
        new_tasks = generate_spike_feeding_tasks(
            pet_id=spike.id,
            pet_name=spike.name,
            parent_id=parent_id,
            days_ahead=7,
            existing_task_dates=existing_dates,
        )

        print(f"Generated {len(new_tasks)} new feeding tasks")

        # Save to database
        created_count = 0
        failed_count = 0

        for task_create in new_tasks:
            try:
                created_task = crud.create_pet_care_task(task_create)
                if created_task:
                    created_count += 1
                    print(
                        f"Created task for {task_create.due_date.date()} "
                        f"assigned to {task_create.assigned_to_kid_username}"
                    )
                else:
                    failed_count += 1
                    print(f"Failed to create task for {task_create.due_date.date()}")
            except Exception as e:
                failed_count += 1
                print(f"Error creating task for {task_create.due_date.date()}: {e}")

        success_msg = (
            f"Daily task generation complete: "
            f"{created_count} created, {failed_count} failed, {len(existing_dates)} already existed"
        )
        print(f"SUCCESS: {success_msg}")

        return {
            "statusCode": 200,
            "body": success_msg,
            "details": {
                "pet_id": spike.id,
                "pet_name": spike.name,
                "tasks_created": created_count,
                "tasks_failed": failed_count,
                "existing_tasks": len(existing_dates),
                "timestamp": datetime.utcnow().isoformat(),
            },
        }

    except Exception as e:
        error_msg = f"Unexpected error in daily task generation: {str(e)}"
        print(f"ERROR: {error_msg}")
        import traceback

        traceback.print_exc()

        return {"statusCode": 500, "body": error_msg}


# For local testing
if __name__ == "__main__":
    # Set test environment variables
    os.environ["SPIKE_PARENT_ID"] = "test-parent-id"
    os.environ["APP_SECRET_KEY"] = "test-secret-key-for-testing-32-chars"

    # Mock event and context
    test_event = {"source": "aws.events", "detail-type": "Scheduled Event"}
    test_context = type("Context", (), {"function_name": "test", "request_id": "test-123"})()

    # Run handler
    result = lambda_handler(test_event, test_context)
    print(f"\nResult: {result}")
