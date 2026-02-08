import json
import logging
import os
from typing import Optional

import httpx
from fastmcp import FastMCP

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("kids-rewards-mcp")

BASE_URL = os.environ.get("KIDS_REWARDS_API_URL", "http://localhost:3000")
API_KEY = os.environ.get("KIDS_REWARDS_API_KEY")
logger.info("API_KEY configured: %s", bool(API_KEY))

mcp = FastMCP(
    "Kids Rewards",
    instructions=(
        "Manage a family chore and reward system. Parents create chores and store items, "
        "kids earn points by completing chores, and redeem points for rewards. "
        "Includes pet care management. "
        "If KIDS_REWARDS_API_KEY is set, authentication is automatic. "
        "Otherwise, call the login tool first."
    ),
)

_client = httpx.AsyncClient(base_url=BASE_URL, timeout=30)
_token: str | None = None


def _headers() -> dict:
    if _token:
        return {"Authorization": f"Bearer {_token}"}
    return {}


def _fmt(data) -> str:
    return json.dumps(data, indent=2, default=str)


async def _authenticate_with_api_key() -> bool:
    global _token
    if not API_KEY:
        return False
    try:
        r = await _client.post("/auth/api-key", json={"api_key": API_KEY})
        if r.status_code == 200:
            result = r.json()
            _token = result.get("access_token")
            logger.info("API key authentication successful")
            return True
        logger.warning("API key authentication failed: %d", r.status_code)
        return False
    except httpx.HTTPError as exc:
        logger.error("API key authentication error: %s", exc)
        return False


async def _ensure_authenticated():
    if _token or not API_KEY:
        return
    await _authenticate_with_api_key()


async def _request(
    method: str,
    path: str,
    json_data: dict | None = None,
    data: dict | None = None,
    params: dict | None = None,
) -> str:
    await _ensure_authenticated()
    try:
        r = await _client.request(method, path, headers=_headers(), json=json_data, data=data, params=params)
        logger.info("%s %s -> %d", method, path, r.status_code)
        if r.status_code == 401 and API_KEY:
            global _token
            _token = None
            if await _authenticate_with_api_key():
                r = await _client.request(method, path, headers=_headers(), json=json_data, data=data, params=params)
                logger.info("%s %s (retry) -> %d", method, path, r.status_code)
        if method == "DELETE" and r.status_code != 200:
            return _fmt({"success": True, "data": None})
        return _fmt(r.json())
    except httpx.HTTPError as exc:
        logger.error("%s %s failed: %s", method, path, exc)
        return _fmt({"success": False, "error": {"code": "CONNECTION_ERROR", "message": str(exc)}})


async def _get(path: str, params: dict | None = None) -> str:
    return await _request("GET", path, params=params)


async def _post(
    path: str, json_data: dict | None = None, data: dict | None = None, params: dict | None = None
) -> str:
    return await _request("POST", path, json_data=json_data, data=data, params=params)


async def _put(path: str, json_data: dict) -> str:
    return await _request("PUT", path, json_data=json_data)


async def _delete(path: str) -> str:
    return await _request("DELETE", path)


# ── Auth & Users ──────────────────────────────────────────────


@mcp.tool()
async def login(username: str, password: str) -> str:
    """Authenticate and store a session token. Not needed if KIDS_REWARDS_API_KEY env var is set.

    Args:
        username: The user's login name.
        password: The user's password.
    """
    global _token
    try:
        r = await _client.post("/token", data={"username": username, "password": password})
        result = r.json()
        if "access_token" in result:
            _token = result["access_token"]
            logger.info("Login successful for %s", username)
            return _fmt({"success": True, "message": f"Logged in as {username}"})
        logger.warning("Login failed for %s", username)
        return _fmt({"success": False, "error": result})
    except httpx.HTTPError as exc:
        logger.error("Login failed: %s", exc)
        return _fmt({"success": False, "error": {"code": "CONNECTION_ERROR", "message": str(exc)}})


@mcp.tool()
async def register_user(username: str, password: str, role: str = "kid") -> str:
    """Register a new user account.

    Args:
        username: Desired username for the new account.
        password: Password for the new account.
        role: User role - 'kid' or 'parent'.
    """
    return await _post("/users/", json_data={"username": username, "password": password, "role": role})


@mcp.tool()
async def get_current_user() -> str:
    """Get the currently authenticated user's profile including points and role."""
    return await _get("/users/me/")


@mcp.tool()
async def list_users(role: Optional[str] = None, limit: int = 100, offset: int = 0) -> str:
    """List all users. Parent-only.

    Args:
        role: Filter by role - 'kid' or 'parent'. Omit for all users.
        limit: Maximum number of results (1-500).
        offset: Number of results to skip for pagination.
    """
    params = {"limit": limit, "offset": offset}
    if role:
        params["role"] = role
    return await _get("/users/", params=params)


@mcp.tool()
async def promote_to_parent(username: str) -> str:
    """Promote a kid user to parent role. Parent-only.

    Args:
        username: Username of the kid to promote.
    """
    return await _post("/users/promote-to-parent", json_data={"username": username})


@mcp.tool()
async def award_points(kid_username: str, points: int) -> str:
    """Award bonus points to a kid. Parent-only.

    Args:
        kid_username: Username of the kid to award points to.
        points: Number of points to award.
    """
    return await _post("/kids/award-points/", json_data={"kid_username": kid_username, "points": points})


@mcp.tool()
async def get_leaderboard() -> str:
    """Get all users sorted by points, highest first."""
    return await _get("/leaderboard")


# ── Store ─────────────────────────────────────────────────────


@mcp.tool()
async def list_store_items(
    sort: Optional[str] = None,
    order: str = "asc",
    limit: int = 100,
    offset: int = 0,
) -> str:
    """List available store reward items.

    Args:
        sort: Sort field - 'points_cost' or 'name'. Omit for default order.
        order: Sort direction - 'asc' or 'desc'.
        limit: Maximum number of results (1-500).
        offset: Number of results to skip for pagination.
    """
    params = {"limit": limit, "offset": offset, "order": order}
    if sort:
        params["sort"] = sort
    return await _get("/store/items/", params=params)


@mcp.tool()
async def get_store_item(item_id: str) -> str:
    """Get a specific store item by its ID.

    Args:
        item_id: The unique identifier of the store item.
    """
    return await _get(f"/store/items/{item_id}")


@mcp.tool()
async def create_store_item(name: str, points_cost: int, description: str = "") -> str:
    """Create a new store reward item. Parent-only.

    Args:
        name: Display name for the reward item.
        points_cost: Number of points required to purchase.
        description: Optional longer description of the item.
    """
    return await _post("/store/items/", json_data={"name": name, "points_cost": points_cost, "description": description})


@mcp.tool()
async def update_store_item(item_id: str, name: str, points_cost: int, description: str = "") -> str:
    """Update an existing store item. Parent-only.

    Args:
        item_id: ID of the store item to update.
        name: New display name.
        points_cost: New points cost.
        description: New description.
    """
    return await _put(
        f"/store/items/{item_id}",
        json_data={"name": name, "points_cost": points_cost, "description": description},
    )


@mcp.tool()
async def delete_store_item(item_id: str) -> str:
    """Delete a store item permanently. Parent-only.

    Args:
        item_id: ID of the store item to delete.
    """
    return await _delete(f"/store/items/{item_id}")


@mcp.tool()
async def purchase_store_item(item_id: str) -> str:
    """Purchase a store item using the current kid's points.

    Args:
        item_id: ID of the store item to purchase.
    """
    return await _post("/kids/redeem-item/", json_data={"item_id": item_id})


# ── Chores ────────────────────────────────────────────────────


@mcp.tool()
async def list_chores(include_inactive: bool = False, limit: int = 100, offset: int = 0) -> str:
    """List chores. By default only active chores are returned.

    Args:
        include_inactive: Set True to include deactivated chores.
        limit: Maximum number of results (1-500).
        offset: Number of results to skip for pagination.
    """
    params = {"limit": limit, "offset": offset}
    if include_inactive:
        params["include_inactive"] = "true"
    return await _get("/chores/", params=params)


@mcp.tool()
async def get_chore(chore_id: str) -> str:
    """Get details of a specific chore.

    Args:
        chore_id: The unique identifier of the chore.
    """
    return await _get(f"/chores/{chore_id}")


@mcp.tool()
async def create_chore(name: str, description: str, points_value: int, is_active: bool = True) -> str:
    """Create a new chore definition. Parent-only.

    Args:
        name: Short name for the chore.
        description: What the chore involves.
        points_value: Points awarded upon approval.
        is_active: Whether the chore is immediately available.
    """
    return await _post(
        "/chores/",
        json_data={"name": name, "description": description, "points_value": points_value, "is_active": is_active},
    )


@mcp.tool()
async def update_chore(
    chore_id: str, name: str, description: str, points_value: int, is_active: bool = True
) -> str:
    """Update an existing chore definition. Parent-only.

    Args:
        chore_id: ID of the chore to update.
        name: Updated chore name.
        description: Updated description.
        points_value: Updated points value.
        is_active: Whether the chore should be active.
    """
    return await _put(
        f"/chores/{chore_id}",
        json_data={"name": name, "description": description, "points_value": points_value, "is_active": is_active},
    )


@mcp.tool()
async def deactivate_chore(chore_id: str) -> str:
    """Deactivate a chore so it no longer appears in active lists. Parent-only.

    Args:
        chore_id: ID of the chore to deactivate.
    """
    return await _post(f"/chores/{chore_id}/deactivate")


@mcp.tool()
async def delete_chore(chore_id: str) -> str:
    """Permanently delete a chore. Parent-only.

    Args:
        chore_id: ID of the chore to delete.
    """
    return await _delete(f"/chores/{chore_id}")


@mcp.tool()
async def submit_chore(chore_id: str, effort_minutes: int = 0) -> str:
    """Submit a chore as completed for parent approval. Kid action.

    Args:
        chore_id: ID of the chore being submitted.
        effort_minutes: Time spent on the chore in minutes (0-240). Earns effort points.
    """
    return await _post(f"/chores/{chore_id}/submit", json_data={"effort_minutes": effort_minutes})


# ── Chore History & Stats ─────────────────────────────────────


@mcp.tool()
async def get_my_chore_history(status: Optional[str] = None, limit: int = 100, offset: int = 0) -> str:
    """Get the current kid's chore submission history.

    Args:
        status: Filter by status - 'pending_approval', 'approved', 'rejected'.
        limit: Maximum number of results (1-500).
        offset: Number of results to skip for pagination.
    """
    params = {"limit": limit, "offset": offset}
    if status:
        params["status"] = status
    return await _get("/chores/history/me", params=params)


@mcp.tool()
async def get_my_chore_stats() -> str:
    """Get aggregated chore statistics for the current kid, including totals, effort, and streaks."""
    return await _get("/chores/history/me/stats")


@mcp.tool()
async def get_my_streak() -> str:
    """Get the current kid's streak data including current streak days and bonus milestones."""
    return await _get("/kids/streak/")


# ── Chore Submissions (Parent) ───────────────────────────────


@mcp.tool()
async def get_pending_chore_submissions() -> str:
    """Get all chore submissions awaiting parent approval. Parent-only."""
    return await _get("/parent/chore-submissions/pending")


@mcp.tool()
async def approve_chore_submission(log_id: str) -> str:
    """Approve a kid's chore submission and award points. Parent-only.

    Args:
        log_id: ID of the chore log entry to approve.
    """
    return await _post("/parent/chore-submissions/approve", json_data={"chore_log_id": log_id})


@mcp.tool()
async def reject_chore_submission(log_id: str, reason: str = "") -> str:
    """Reject a kid's chore submission. Parent-only.

    Args:
        log_id: ID of the chore log entry to reject.
        reason: Optional explanation for the rejection.
    """
    return await _post("/parent/chore-submissions/reject", json_data={"chore_log_id": log_id, "reason": reason})


# ── Chore Assignments ─────────────────────────────────────────


@mcp.tool()
async def create_assignment(
    chore_id: str, assigned_to_kid_id: str, due_date: str, notes: str = ""
) -> str:
    """Assign a specific chore to a kid. Parent-only.

    Args:
        chore_id: ID of the chore to assign.
        assigned_to_kid_id: Username of the kid to assign it to.
        due_date: Deadline in YYYY-MM-DD format (required).
        notes: Optional instructions or context.
    """
    payload = {
        "chore_id": chore_id,
        "assigned_to_kid_id": assigned_to_kid_id,
        "due_date": due_date,
        "notes": notes,
    }
    return await _post("/parent/chore-assignments/", json_data=payload)


@mcp.tool()
async def get_my_assignments(status: Optional[str] = None, limit: int = 100, offset: int = 0) -> str:
    """Get the current kid's assigned chores.

    Args:
        status: Filter by status - 'assigned', 'submitted', 'approved', 'rejected', 'overdue'.
        limit: Maximum number of results (1-500).
        offset: Number of results to skip for pagination.
    """
    params = {"limit": limit, "offset": offset}
    if status:
        params["status"] = status
    return await _get("/kids/my-assignments/", params=params)


@mcp.tool()
async def submit_assignment(assignment_id: str, submission_notes: str = "") -> str:
    """Submit an assigned chore as completed. Kid action.

    Args:
        assignment_id: ID of the assignment to submit.
        submission_notes: Optional notes about the completion.
    """
    return await _post(
        f"/chore-assignments/{assignment_id}/submit",
        json_data={"submission_notes": submission_notes},
    )


@mcp.tool()
async def get_pending_assignment_submissions() -> str:
    """Get all assignment submissions awaiting parent approval. Parent-only."""
    return await _get("/parent/assignment-submissions/pending")


@mcp.tool()
async def approve_assignment(assignment_id: str) -> str:
    """Approve a kid's assignment submission. Parent-only.

    Args:
        assignment_id: ID of the assignment to approve.
    """
    return await _post("/parent/assignment-submissions/approve", json_data={"assignment_id": assignment_id})


@mcp.tool()
async def reject_assignment(assignment_id: str, reason: str = "") -> str:
    """Reject a kid's assignment submission. Parent-only.

    Args:
        assignment_id: ID of the assignment to reject.
        reason: Optional explanation for the rejection.
    """
    return await _post(
        "/parent/assignment-submissions/reject",
        json_data={"assignment_id": assignment_id, "reason": reason},
    )


@mcp.tool()
async def list_parent_assignments() -> str:
    """List all chore assignments created by the current parent."""
    return await _get("/parent/chore-assignments/")


# ── Purchases ─────────────────────────────────────────────────


@mcp.tool()
async def get_my_purchase_history(status: Optional[str] = None, limit: int = 100, offset: int = 0) -> str:
    """Get the current user's purchase history.

    Args:
        status: Filter by status - 'pending', 'approved', 'rejected'.
        limit: Maximum number of results (1-500).
        offset: Number of results to skip for pagination.
    """
    params = {"limit": limit, "offset": offset}
    if status:
        params["status"] = status
    return await _get("/users/me/purchase-history", params=params)


@mcp.tool()
async def get_pending_purchases() -> str:
    """Get all pending purchase requests awaiting parent approval. Parent-only."""
    return await _get("/parent/purchase-requests/pending")


@mcp.tool()
async def approve_purchase(log_id: str) -> str:
    """Approve a purchase request. Parent-only.

    Args:
        log_id: ID of the purchase log entry to approve.
    """
    return await _post("/parent/purchase-requests/approve", json_data={"log_id": log_id})


@mcp.tool()
async def reject_purchase(log_id: str) -> str:
    """Reject a purchase request and refund points. Parent-only.

    Args:
        log_id: ID of the purchase log entry to reject.
    """
    return await _post("/parent/purchase-requests/reject", json_data={"log_id": log_id})


# ── Requests (Feature/Item requests from kids) ───────────────


@mcp.tool()
async def create_request(request_type: str, details: str) -> str:
    """Create a feature or item request. Kid action.

    Args:
        request_type: Type of request - 'add_store_item', 'add_chore', or 'other'.
        details: JSON string with request specifics, e.g. '{"name": "New Item", "points_cost": 100}'.
    """
    import json as _json

    try:
        details_dict = _json.loads(details)
    except _json.JSONDecodeError:
        details_dict = {"description": details}
    return await _post(
        "/requests/",
        json_data={"request_type": request_type, "details": details_dict},
    )


@mcp.tool()
async def get_my_requests(
    status: Optional[str] = None,
    request_type: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> str:
    """Get the current kid's submitted requests.

    Args:
        status: Filter by status - 'pending', 'approved', 'rejected'.
        request_type: Filter by type - 'chore' or 'store_item'.
        limit: Maximum number of results (1-500).
        offset: Number of results to skip for pagination.
    """
    params = {"limit": limit, "offset": offset}
    if status:
        params["status"] = status
    if request_type:
        params["type"] = request_type
    return await _get("/requests/me/", params=params)


@mcp.tool()
async def get_pending_requests() -> str:
    """Get all pending feature/item requests from kids. Parent-only."""
    return await _get("/parent/requests/pending/")


@mcp.tool()
async def approve_request(request_id: str) -> str:
    """Approve a kid's feature/item request. Parent-only.

    Args:
        request_id: ID of the request to approve.
    """
    return await _post(f"/parent/requests/{request_id}/approve/")


@mcp.tool()
async def reject_request(request_id: str, reason: str = "") -> str:
    """Reject a kid's feature/item request. Parent-only.

    Args:
        request_id: ID of the request to reject.
        reason: Optional explanation for the rejection.
    """
    return await _post(f"/parent/requests/{request_id}/reject/", json_data={"reason": reason})


# ── Pets ──────────────────────────────────────────────────────


@mcp.tool()
async def list_pets() -> str:
    """List all family pets with their profiles and calculated ages."""
    return await _get("/pets/")


@mcp.tool()
async def get_pet(pet_id: str) -> str:
    """Get a specific pet's full profile including age.

    Args:
        pet_id: The unique identifier of the pet.
    """
    return await _get(f"/pets/{pet_id}")


@mcp.tool()
async def create_pet(
    name: str, species: str, birthday: Optional[str] = None, photo_url: Optional[str] = None
) -> str:
    """Create a new pet profile. Parent-only.

    Args:
        name: The pet's name.
        species: Species/breed (e.g. 'bearded dragon', 'cat', 'dog').
        birthday: Pet's birthday in YYYY-MM-DD format.
        photo_url: URL to a photo of the pet.
    """
    payload = {"name": name, "species": species}
    if birthday:
        payload["birthday"] = birthday
    if photo_url:
        payload["photo_url"] = photo_url
    return await _post("/pets/", json_data=payload)


@mcp.tool()
async def update_pet(
    pet_id: str, name: str, species: str, birthday: str, photo_url: Optional[str] = None
) -> str:
    """Update a pet's profile. Parent-only.

    Args:
        pet_id: ID of the pet to update.
        name: Updated pet name.
        species: Updated species.
        birthday: Pet's birthday in YYYY-MM-DD format.
        photo_url: Updated photo URL.
    """
    payload: dict = {"name": name, "species": species, "birthday": birthday}
    if photo_url:
        payload["photo_url"] = photo_url
    return await _put(f"/pets/{pet_id}", json_data=payload)


@mcp.tool()
async def deactivate_pet(pet_id: str) -> str:
    """Deactivate a pet profile. Parent-only.

    Args:
        pet_id: ID of the pet to deactivate.
    """
    return await _post(f"/pets/{pet_id}/deactivate")


@mcp.tool()
async def get_care_recommendations(pet_id: str) -> str:
    """Get AI-generated care recommendations tailored to this pet's species and age.

    Args:
        pet_id: ID of the pet to get recommendations for.
    """
    return await _get(f"/pets/{pet_id}/care-recommendations")


@mcp.tool()
async def get_recommended_schedules(pet_id: str) -> str:
    """Get suggested care schedules for a pet based on its species.

    Args:
        pet_id: ID of the pet to get schedule recommendations for.
    """
    return await _get(f"/pets/{pet_id}/recommended-schedules")


# ── Pet Schedules ─────────────────────────────────────────────


@mcp.tool()
async def create_schedule(
    pet_id: str,
    task_name: str,
    frequency: str,
    assigned_kid_ids: list[str],
    points_value: int = 5,
    description: Optional[str] = None,
    day_of_week: Optional[int] = None,
    due_by_time: Optional[str] = None,
) -> str:
    """Create a recurring pet care schedule. Parent-only.

    Args:
        pet_id: ID of the pet this schedule is for.
        task_name: Name for the care task (e.g. 'Feed Gecko', 'Clean Tank').
        frequency: How often - 'daily' or 'weekly'.
        assigned_kid_ids: List of kid usernames to rotate through.
        points_value: Points awarded per completed task (default 5).
        description: Optional detailed instructions.
        day_of_week: For weekly tasks, 0=Monday through 6=Sunday.
        due_by_time: Optional deadline time in HH:MM format (e.g. '10:00').
    """
    payload: dict = {
        "pet_id": pet_id,
        "task_name": task_name,
        "frequency": frequency,
        "assigned_kid_ids": assigned_kid_ids,
        "points_value": points_value,
    }
    if description is not None:
        payload["description"] = description
    if day_of_week is not None:
        payload["day_of_week"] = day_of_week
    if due_by_time is not None:
        payload["due_by_time"] = due_by_time
    return await _post("/pets/schedules/", json_data=payload)


@mcp.tool()
async def list_schedules(pet_id: str) -> str:
    """List all care schedules for a specific pet.

    Args:
        pet_id: ID of the pet to list schedules for.
    """
    return await _get(f"/pets/{pet_id}/schedules/")


@mcp.tool()
async def deactivate_schedule(schedule_id: str) -> str:
    """Deactivate a pet care schedule. Parent-only.

    Args:
        schedule_id: ID of the schedule to deactivate.
    """
    return await _post(f"/pets/schedules/{schedule_id}/deactivate")


@mcp.tool()
async def generate_tasks(schedule_id: str, days_ahead: int = 7) -> str:
    """Generate pet care task instances from a schedule.

    Args:
        schedule_id: ID of the schedule to generate tasks from.
        days_ahead: Number of days ahead to generate tasks for (default 7).
    """
    return await _post(
        f"/pets/schedules/{schedule_id}/generate-tasks",
        params={"days_ahead": days_ahead},
    )


# ── Pet Tasks ─────────────────────────────────────────────────


@mcp.tool()
async def get_my_pet_tasks(status: Optional[str] = None, limit: int = 100, offset: int = 0) -> str:
    """Get the current kid's assigned pet care tasks.

    Args:
        status: Filter by status - 'scheduled', 'assigned', 'pending_approval', 'approved', 'rejected'.
        limit: Maximum number of results (1-500).
        offset: Number of results to skip for pagination.
    """
    params = {"limit": limit, "offset": offset}
    if status:
        params["status"] = status
    return await _get("/kids/my-pet-tasks/", params=params)


@mcp.tool()
async def get_pet_tasks(pet_id: str) -> str:
    """Get all care tasks for a specific pet.

    Args:
        pet_id: ID of the pet to list tasks for.
    """
    return await _get(f"/pets/{pet_id}/tasks/")


@mcp.tool()
async def submit_pet_task(task_id: str, notes: str = "") -> str:
    """Submit a pet care task as completed. Kid action.

    Args:
        task_id: ID of the pet care task to submit.
        notes: Optional notes about the completion.
    """
    return await _post(f"/pets/tasks/{task_id}/submit", json_data={"notes": notes})


@mcp.tool()
async def get_pending_pet_task_submissions() -> str:
    """Get all pet care task submissions awaiting parent approval. Parent-only."""
    return await _get("/parent/pet-task-submissions/pending")


@mcp.tool()
async def approve_pet_task(task_id: str) -> str:
    """Approve a pet care task submission and award points. Parent-only.

    Args:
        task_id: ID of the pet care task to approve.
    """
    return await _post("/parent/pet-task-submissions/approve", json_data={"task_id": task_id})


@mcp.tool()
async def reject_pet_task(task_id: str, reason: str = "") -> str:
    """Reject a pet care task submission. Parent-only.

    Args:
        task_id: ID of the pet care task to reject.
        reason: Optional explanation for the rejection.
    """
    return await _post("/parent/pet-task-submissions/reject", json_data={"task_id": task_id, "reason": reason})


# ── Pet Health ────────────────────────────────────────────────


@mcp.tool()
async def add_health_log(pet_id: str, weight_grams: float, notes: str = "") -> str:
    """Log a pet's weight measurement. Parent-only.

    Args:
        pet_id: ID of the pet.
        weight_grams: Weight in grams.
        notes: Optional health observations.
    """
    return await _post(
        f"/pets/{pet_id}/health-logs/",
        json_data={"pet_id": pet_id, "weight_grams": weight_grams, "notes": notes},
    )


@mcp.tool()
async def get_health_logs(pet_id: str) -> str:
    """Get weight and health tracking logs for a pet.

    Args:
        pet_id: ID of the pet to get health logs for.
    """
    return await _get(f"/pets/{pet_id}/health-logs/")


# ── Dashboards & Info ─────────────────────────────────────────


@mcp.tool()
async def get_parent_dashboard() -> str:
    """Get parent dashboard showing pending counts for chores, purchases, assignments, requests, and pet tasks."""
    return await _get("/parent/dashboard")


@mcp.tool()
async def get_kid_dashboard() -> str:
    """Get kid dashboard showing current points, active assignments, active pet tasks, and streak data."""
    return await _get("/kid/dashboard")


@mcp.tool()
async def get_pet_overview() -> str:
    """Get a summary overview of all pets including their schedules and task statistics."""
    return await _get("/pets/overview/")


# ── Resources ─────────────────────────────────────────────────


@mcp.resource("config://points-rules")
async def get_points_rules() -> str:
    """Business rules for points calculation, streak milestones, and suggested pricing formulas."""
    return await _get("/config/points-rules")


# ── Lookup by ID ──────────────────────────────────────────────


@mcp.tool()
async def get_purchase_log(log_id: str) -> str:
    """Get a specific purchase log entry by ID.

    Args:
        log_id: The unique identifier of the purchase log.
    """
    return await _get(f"/purchase-logs/{log_id}")


@mcp.tool()
async def get_chore_log(log_id: str) -> str:
    """Get a specific chore log entry by ID.

    Args:
        log_id: The unique identifier of the chore log.
    """
    return await _get(f"/chore-logs/{log_id}")


@mcp.tool()
async def get_request_by_id(request_id: str) -> str:
    """Get a specific feature/item request by ID.

    Args:
        request_id: The unique identifier of the request.
    """
    return await _get(f"/requests/{request_id}")


@mcp.tool()
async def get_assignment(assignment_id: str) -> str:
    """Get a specific chore assignment by ID.

    Args:
        assignment_id: The unique identifier of the assignment.
    """
    return await _get(f"/chore-assignments/{assignment_id}")


@mcp.tool()
async def get_pet_task(task_id: str) -> str:
    """Get a specific pet care task by ID.

    Args:
        task_id: The unique identifier of the pet care task.
    """
    return await _get(f"/pets/tasks/{task_id}")


@mcp.tool()
async def get_schedule(schedule_id: str) -> str:
    """Get a specific pet care schedule by ID.

    Args:
        schedule_id: The unique identifier of the schedule.
    """
    return await _get(f"/pets/schedules/{schedule_id}")


if __name__ == "__main__":
    mcp.run()
