import os
from typing import Optional

import httpx
from fastmcp import FastMCP

BASE_URL = os.environ.get("KIDS_REWARDS_API_URL", "http://localhost:3000")

mcp = FastMCP(
    "Kids Rewards",
    instructions=(
        "Manage a family chore and reward system. Parents create chores and store items, "
        "kids earn points by completing chores, and redeem points for rewards. "
        "Includes pet care management. You must login first to get a token."
    ),
)

_token: str | None = None


def _headers() -> dict:
    if _token:
        return {"Authorization": f"Bearer {_token}"}
    return {}


def _url(path: str) -> str:
    return f"{BASE_URL}{path}"


def _get(path: str, params: dict | None = None) -> dict:
    r = httpx.get(_url(path), headers=_headers(), params=params, timeout=30)
    return r.json()


def _post(path: str, json: dict | None = None, data: dict | None = None) -> dict:
    r = httpx.post(_url(path), headers=_headers(), json=json, data=data, timeout=30)
    return r.json()


def _put(path: str, json: dict) -> dict:
    r = httpx.put(_url(path), headers=_headers(), json=json, timeout=30)
    return r.json()


def _delete(path: str) -> dict:
    r = httpx.delete(_url(path), headers=_headers(), timeout=30)
    if r.status_code == 200:
        return r.json()
    return {"success": True, "data": None}


# ── Auth & Users ──────────────────────────────────────────────


@mcp.tool
def login(username: str, password: str) -> dict:
    """Authenticate and store token. Must be called before other tools."""
    global _token
    r = httpx.post(
        _url("/token"),
        data={"username": username, "password": password},
        timeout=30,
    )
    result = r.json()
    if "access_token" in result:
        _token = result["access_token"]
        return {"success": True, "message": f"Logged in as {username}"}
    return {"success": False, "error": result}


@mcp.tool
def register_user(username: str, password: str, role: str = "kid") -> dict:
    """Register a new user account. Role: 'kid' or 'parent'."""
    return _post("/users/", json={"username": username, "password": password, "role": role})


@mcp.tool
def get_current_user() -> dict:
    """Get the currently authenticated user's profile."""
    return _get("/users/me/")


@mcp.tool
def list_users(role: Optional[str] = None, limit: int = 100, offset: int = 0) -> dict:
    """List all users. Parent-only. Optional filter by role ('kid' or 'parent')."""
    params = {"limit": limit, "offset": offset}
    if role:
        params["role"] = role
    return _get("/users/", params=params)


@mcp.tool
def promote_to_parent(username: str) -> dict:
    """Promote a kid user to parent role. Parent-only."""
    return _post("/users/promote-to-parent", json={"username": username})


@mcp.tool
def award_points(kid_username: str, points: int) -> dict:
    """Award bonus points to a kid. Parent-only."""
    return _post("/kids/award-points/", json={"kid_username": kid_username, "points": points})


@mcp.tool
def get_leaderboard() -> dict:
    """Get all users sorted by points (highest first)."""
    return _get("/leaderboard")


# ── Store ─────────────────────────────────────────────────────


@mcp.tool
def list_store_items(
    sort: Optional[str] = None,
    order: str = "asc",
    limit: int = 100,
    offset: int = 0,
) -> dict:
    """List store items. Sort by 'points_cost' or 'name'. Order: 'asc' or 'desc'."""
    params = {"limit": limit, "offset": offset, "order": order}
    if sort:
        params["sort"] = sort
    return _get("/store/items/", params=params)


@mcp.tool
def get_store_item(item_id: str) -> dict:
    """Get a specific store item by ID."""
    return _get(f"/store/items/{item_id}")


@mcp.tool
def create_store_item(name: str, points_cost: int, description: str = "") -> dict:
    """Create a new store reward item. Parent-only."""
    return _post("/store/items/", json={"name": name, "points_cost": points_cost, "description": description})


@mcp.tool
def update_store_item(item_id: str, name: str, points_cost: int, description: str = "") -> dict:
    """Update an existing store item. Parent-only."""
    return _put(f"/store/items/{item_id}", json={"name": name, "points_cost": points_cost, "description": description})


@mcp.tool
def delete_store_item(item_id: str) -> dict:
    """Delete a store item. Parent-only."""
    return _delete(f"/store/items/{item_id}")


@mcp.tool
def purchase_store_item(item_id: str) -> dict:
    """Purchase a store item using points. Kid action."""
    return _post("/store/items/purchase", json={"item_id": item_id})


# ── Chores ────────────────────────────────────────────────────


@mcp.tool
def list_chores(include_inactive: bool = False, limit: int = 100, offset: int = 0) -> dict:
    """List available chores. Set include_inactive=True to see all."""
    params = {"limit": limit, "offset": offset}
    if include_inactive:
        params["include_inactive"] = "true"
    return _get("/chores/", params=params)


@mcp.tool
def get_chore(chore_id: str) -> dict:
    """Get a specific chore by ID."""
    return _get(f"/chores/{chore_id}")


@mcp.tool
def create_chore(
    name: str,
    description: str,
    points_value: int,
    is_active: bool = True,
) -> dict:
    """Create a new chore. Parent-only."""
    return _post(
        "/chores/",
        json={
            "name": name,
            "description": description,
            "points_value": points_value,
            "is_active": is_active,
        },
    )


@mcp.tool
def update_chore(
    chore_id: str,
    name: str,
    description: str,
    points_value: int,
    is_active: bool = True,
) -> dict:
    """Update an existing chore. Parent-only."""
    return _put(
        f"/chores/{chore_id}",
        json={
            "name": name,
            "description": description,
            "points_value": points_value,
            "is_active": is_active,
        },
    )


@mcp.tool
def deactivate_chore(chore_id: str) -> dict:
    """Deactivate a chore. Parent-only."""
    return _post(f"/chores/{chore_id}/deactivate")


@mcp.tool
def delete_chore(chore_id: str) -> dict:
    """Delete a chore. Parent-only."""
    return _delete(f"/chores/{chore_id}")


@mcp.tool
def submit_chore(chore_id: str, effort_minutes: int = 0) -> dict:
    """Submit a chore completion. Kid action. effort_minutes tracks time spent."""
    return _post(f"/chores/{chore_id}/submit", json={"effort_minutes": effort_minutes})


# ── Chore History & Stats ─────────────────────────────────────


@mcp.tool
def get_my_chore_history(
    status: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> dict:
    """Get the current kid's chore submission history. Filter by status."""
    params = {"limit": limit, "offset": offset}
    if status:
        params["status"] = status
    return _get("/chores/history/me", params=params)


@mcp.tool
def get_my_chore_stats() -> dict:
    """Get aggregated chore statistics for the current kid."""
    return _get("/chores/history/me/stats")


@mcp.tool
def get_my_streak() -> dict:
    """Get the current kid's streak information."""
    return _get("/kids/streak/")


# ── Chore Submissions (Parent) ───────────────────────────────


@mcp.tool
def get_pending_chore_submissions() -> dict:
    """Get all pending chore submissions awaiting parent approval."""
    return _get("/parent/chore-submissions/pending")


@mcp.tool
def approve_chore_submission(log_id: str) -> dict:
    """Approve a kid's chore submission. Parent-only."""
    return _post("/parent/chore-submissions/approve", json={"log_id": log_id})


@mcp.tool
def reject_chore_submission(log_id: str, reason: str = "") -> dict:
    """Reject a kid's chore submission. Parent-only."""
    return _post("/parent/chore-submissions/reject", json={"log_id": log_id, "reason": reason})


# ── Chore Assignments ─────────────────────────────────────────


@mcp.tool
def create_assignment(
    chore_id: str,
    kid_username: str,
    due_date: Optional[str] = None,
    notes: str = "",
) -> dict:
    """Assign a chore to a kid. Parent-only. due_date format: YYYY-MM-DD."""
    payload = {"chore_id": chore_id, "kid_username": kid_username, "notes": notes}
    if due_date:
        payload["due_date"] = due_date
    return _post("/parent/chore-assignments/", json=payload)


@mcp.tool
def get_my_assignments(
    status: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> dict:
    """Get the current kid's assigned chores. Filter by status."""
    params = {"limit": limit, "offset": offset}
    if status:
        params["status"] = status
    return _get("/kids/my-assignments/", params=params)


@mcp.tool
def submit_assignment(assignment_id: str, notes: str = "") -> dict:
    """Submit an assignment completion. Kid action."""
    return _post(
        f"/kids/my-assignments/{assignment_id}/submit",
        json={"notes": notes},
    )


@mcp.tool
def get_pending_assignment_submissions() -> dict:
    """Get pending assignment submissions. Parent-only."""
    return _get("/parent/assignment-submissions/pending")


@mcp.tool
def approve_assignment(assignment_id: str) -> dict:
    """Approve a kid's assignment submission. Parent-only."""
    return _post("/parent/assignment-submissions/approve", json={"assignment_id": assignment_id})


@mcp.tool
def reject_assignment(assignment_id: str, reason: str = "") -> dict:
    """Reject a kid's assignment submission. Parent-only."""
    return _post(
        "/parent/assignment-submissions/reject",
        json={"assignment_id": assignment_id, "reason": reason},
    )


@mcp.tool
def list_parent_assignments() -> dict:
    """List all chore assignments created by the current parent."""
    return _get("/parent/chore-assignments/")


# ── Purchases ─────────────────────────────────────────────────


@mcp.tool
def get_my_purchase_history(
    status: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> dict:
    """Get the current user's purchase history. Filter by status."""
    params = {"limit": limit, "offset": offset}
    if status:
        params["status"] = status
    return _get("/users/me/purchase-history", params=params)


@mcp.tool
def get_pending_purchases() -> dict:
    """Get all pending purchase requests. Parent-only."""
    return _get("/parent/purchase-requests/pending")


@mcp.tool
def approve_purchase(log_id: str) -> dict:
    """Approve a purchase request. Parent-only."""
    return _post("/parent/purchase-requests/approve", json={"log_id": log_id})


@mcp.tool
def reject_purchase(log_id: str) -> dict:
    """Reject a purchase request. Parent-only."""
    return _post("/parent/purchase-requests/reject", json={"log_id": log_id})


# ── Requests (Feature/Item requests from kids) ───────────────


@mcp.tool
def create_request(request_type: str, title: str, description: str = "") -> dict:
    """Create a feature or item request. Kid action. request_type: 'chore' or 'store_item'."""
    return _post(
        "/requests/",
        json={"request_type": request_type, "title": title, "description": description},
    )


@mcp.tool
def get_my_requests(
    status: Optional[str] = None,
    request_type: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> dict:
    """Get the current kid's requests. Filter by status and type."""
    params = {"limit": limit, "offset": offset}
    if status:
        params["status"] = status
    if request_type:
        params["type"] = request_type
    return _get("/requests/me/", params=params)


@mcp.tool
def get_pending_requests() -> dict:
    """Get all pending feature/item requests. Parent-only."""
    return _get("/parent/requests/pending/")


@mcp.tool
def approve_request(request_id: str) -> dict:
    """Approve a kid's request. Parent-only."""
    return _post(f"/parent/requests/{request_id}/approve/")


@mcp.tool
def reject_request(request_id: str, reason: str = "") -> dict:
    """Reject a kid's request. Parent-only."""
    return _post(f"/parent/requests/{request_id}/reject/", json={"reason": reason})


# ── Pets ──────────────────────────────────────────────────────


@mcp.tool
def list_pets() -> dict:
    """List all family pets."""
    return _get("/pets/")


@mcp.tool
def get_pet(pet_id: str) -> dict:
    """Get a specific pet's profile including age."""
    return _get(f"/pets/{pet_id}")


@mcp.tool
def create_pet(
    name: str,
    species: str,
    birthday: Optional[str] = None,
    photo_url: Optional[str] = None,
) -> dict:
    """Create a new pet. Parent-only. birthday format: YYYY-MM-DD."""
    payload = {"name": name, "species": species}
    if birthday:
        payload["birthday"] = birthday
    if photo_url:
        payload["photo_url"] = photo_url
    return _post("/pets/", json=payload)


@mcp.tool
def update_pet(
    pet_id: str,
    name: str,
    species: str,
    birthday: Optional[str] = None,
    photo_url: Optional[str] = None,
) -> dict:
    """Update a pet's profile. Parent-only."""
    payload = {"name": name, "species": species}
    if birthday:
        payload["birthday"] = birthday
    if photo_url:
        payload["photo_url"] = photo_url
    return _put(f"/pets/{pet_id}", json=payload)


@mcp.tool
def deactivate_pet(pet_id: str) -> dict:
    """Deactivate a pet. Parent-only."""
    return _post(f"/pets/{pet_id}/deactivate")


@mcp.tool
def get_care_recommendations(pet_id: str) -> dict:
    """Get AI-generated care recommendations for a pet."""
    return _get(f"/pets/{pet_id}/care-recommendations")


@mcp.tool
def get_recommended_schedules(pet_id: str) -> dict:
    """Get recommended care schedules for a pet based on species."""
    return _get(f"/pets/{pet_id}/recommended-schedules")


# ── Pet Schedules ─────────────────────────────────────────────


@mcp.tool
def create_schedule(
    pet_id: str,
    care_type: str,
    frequency: str,
    assigned_kid_ids: list[str],
    task_name: str = "",
    points_value: int = 5,
) -> dict:
    """Create a pet care schedule. Parent-only. care_type: feeding/cleaning/exercise/etc."""
    return _post(
        "/pets/schedules/",
        json={
            "pet_id": pet_id,
            "care_type": care_type,
            "frequency": frequency,
            "assigned_kid_ids": assigned_kid_ids,
            "task_name": task_name,
            "points_value": points_value,
        },
    )


@mcp.tool
def list_schedules(pet_id: str) -> dict:
    """List care schedules for a specific pet."""
    return _get(f"/pets/{pet_id}/schedules/")


@mcp.tool
def deactivate_schedule(schedule_id: str) -> dict:
    """Deactivate a pet care schedule. Parent-only."""
    return _post(f"/pets/schedules/{schedule_id}/deactivate")


@mcp.tool
def generate_tasks(schedule_id: str, days: int = 7) -> dict:
    """Generate pet care tasks from a schedule for the next N days."""
    return _post(f"/pets/schedules/{schedule_id}/generate-tasks", json={"days": days})


# ── Pet Tasks ─────────────────────────────────────────────────


@mcp.tool
def get_my_pet_tasks(
    status: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> dict:
    """Get the current kid's pet care tasks. Filter by status."""
    params = {"limit": limit, "offset": offset}
    if status:
        params["status"] = status
    return _get("/kids/my-pet-tasks/", params=params)


@mcp.tool
def get_pet_tasks(pet_id: str) -> dict:
    """Get all care tasks for a specific pet."""
    return _get(f"/pets/{pet_id}/tasks/")


@mcp.tool
def submit_pet_task(task_id: str, notes: str = "") -> dict:
    """Submit a pet care task as completed. Kid action."""
    return _post(f"/pets/tasks/{task_id}/submit", json={"notes": notes})


@mcp.tool
def get_pending_pet_task_submissions() -> dict:
    """Get pending pet task submissions. Parent-only."""
    return _get("/parent/pet-task-submissions/pending")


@mcp.tool
def approve_pet_task(task_id: str) -> dict:
    """Approve a pet task submission. Parent-only."""
    return _post("/parent/pet-task-submissions/approve", json={"task_id": task_id})


@mcp.tool
def reject_pet_task(task_id: str, reason: str = "") -> dict:
    """Reject a pet task submission. Parent-only."""
    return _post("/parent/pet-task-submissions/reject", json={"task_id": task_id, "reason": reason})


# ── Pet Health ────────────────────────────────────────────────


@mcp.tool
def add_health_log(
    pet_id: str,
    weight_grams: float,
    notes: str = "",
) -> dict:
    """Log a pet's weight/health data. Parent-only."""
    return _post(
        f"/pets/{pet_id}/health-logs/",
        json={"weight_grams": weight_grams, "notes": notes},
    )


@mcp.tool
def get_health_logs(pet_id: str) -> dict:
    """Get health/weight logs for a specific pet."""
    return _get(f"/pets/{pet_id}/health-logs/")


# ── Dashboards & Info ─────────────────────────────────────────


@mcp.tool
def get_parent_dashboard() -> dict:
    """Get parent dashboard with pending counts for all categories."""
    return _get("/parent/dashboard")


@mcp.tool
def get_kid_dashboard() -> dict:
    """Get kid dashboard with points, active tasks, and streak."""
    return _get("/kid/dashboard")


@mcp.tool
def get_pet_overview() -> dict:
    """Get overview of all pets with schedules and task summaries."""
    return _get("/pets/overview/")


@mcp.tool
def get_points_rules() -> dict:
    """Get business rules for points calculation, streaks, and pricing."""
    return _get("/config/points-rules")


# ── Lookup by ID ──────────────────────────────────────────────


@mcp.tool
def get_purchase_log(log_id: str) -> dict:
    """Get a specific purchase log by ID."""
    return _get(f"/purchase-logs/{log_id}")


@mcp.tool
def get_chore_log(log_id: str) -> dict:
    """Get a specific chore log by ID."""
    return _get(f"/chore-logs/{log_id}")


@mcp.tool
def get_request_by_id(request_id: str) -> dict:
    """Get a specific request by ID."""
    return _get(f"/requests/{request_id}")


@mcp.tool
def get_assignment(assignment_id: str) -> dict:
    """Get a specific chore assignment by ID."""
    return _get(f"/chore-assignments/{assignment_id}")


@mcp.tool
def get_pet_task(task_id: str) -> dict:
    """Get a specific pet care task by ID."""
    return _get(f"/pets/tasks/{task_id}")


@mcp.tool
def get_schedule(schedule_id: str) -> dict:
    """Get a specific pet care schedule by ID."""
    return _get(f"/pets/schedules/{schedule_id}")


if __name__ == "__main__":
    mcp.run()
