import os
import sys
import uuid
from datetime import datetime, timezone

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from fastapi.testclient import TestClient

from backend.main import (
    app,
    get_current_active_user,
    get_current_kid_user,
    get_current_parent_user,
)

_current_file_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.abspath(os.path.join(_current_file_dir, "..", ".."))


TEST_SECRET_KEY = os.environ.get("APP_SECRET_KEY", "test-secret-key-for-pre-commit-hook-validation-32chars")


def make_user(role="parent", username=None, points=None):
    from backend.models import User, UserRole

    if username is None:
        username = f"test-{role}-{uuid.uuid4().hex[:6]}"
    user_id = f"user-{uuid.uuid4().hex[:8]}"
    return User(
        id=user_id,
        username=username,
        role=UserRole(role),
        hashed_password="$2b$12$fakehash",
        points=points if role == "kid" else None,
    )


PARENT_USER = make_user("parent", "testparent")
KID_USER = make_user("kid", "testkid", points=100)


def _override_parent():
    return PARENT_USER


def _override_kid():
    return KID_USER


def _override_active_parent():
    return PARENT_USER


def _override_active_kid():
    return KID_USER


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def api():
    app.dependency_overrides[get_current_parent_user] = _override_parent
    app.dependency_overrides[get_current_kid_user] = _override_kid
    app.dependency_overrides[get_current_active_user] = _override_active_parent
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def parent_api():
    app.dependency_overrides[get_current_parent_user] = _override_parent
    app.dependency_overrides[get_current_active_user] = _override_active_parent
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def kid_api():
    app.dependency_overrides[get_current_kid_user] = _override_kid
    app.dependency_overrides[get_current_active_user] = _override_active_kid
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def parent_user():
    return PARENT_USER


@pytest.fixture()
def kid_user():
    return KID_USER


def make_chore(parent_id=None, **overrides):
    defaults = {
        "id": f"chore-{uuid.uuid4().hex[:8]}",
        "name": "Test Chore",
        "description": "A test chore",
        "points_value": 10,
        "created_by_parent_id": parent_id or PARENT_USER.id,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
        "is_active": True,
    }
    defaults.update(overrides)
    from backend.models import Chore

    return Chore(**defaults)


def make_store_item(**overrides):
    defaults = {
        "id": f"item-{uuid.uuid4().hex[:8]}",
        "name": "Test Item",
        "description": "A test store item",
        "points_cost": 25,
    }
    defaults.update(overrides)
    from backend.models import StoreItem

    return StoreItem(**defaults)


def make_purchase_log(user=None, item=None, **overrides):
    from backend.models import PurchaseLog, PurchaseStatus

    user = user or KID_USER
    defaults = {
        "id": f"purchase-{uuid.uuid4().hex[:8]}",
        "user_id": user.id,
        "username": user.username,
        "item_id": item.id if item else f"item-{uuid.uuid4().hex[:8]}",
        "item_name": item.name if item else "Test Item",
        "points_spent": item.points_cost if item else 25,
        "timestamp": datetime.now(timezone.utc),
        "status": PurchaseStatus.PENDING,
    }
    defaults.update(overrides)
    return PurchaseLog(**defaults)


def make_chore_log(kid=None, chore=None, **overrides):
    from backend.models import ChoreLog, ChoreStatus

    kid = kid or KID_USER
    defaults = {
        "id": f"log-{uuid.uuid4().hex[:8]}",
        "chore_id": chore.id if chore else f"chore-{uuid.uuid4().hex[:8]}",
        "chore_name": chore.name if chore else "Test Chore",
        "kid_id": kid.id,
        "kid_username": kid.username,
        "points_value": chore.points_value if chore else 10,
        "status": ChoreStatus.PENDING_APPROVAL,
        "submitted_at": datetime.now(timezone.utc),
        "effort_minutes": 0,
        "retry_count": 0,
        "effort_points": 0,
        "is_retry": False,
    }
    defaults.update(overrides)
    return ChoreLog(**defaults)


def make_pet(parent_id=None, **overrides):
    from backend.models import Pet, PetSpecies

    defaults = {
        "id": f"pet-{uuid.uuid4().hex[:8]}",
        "name": "Test Pet",
        "species": PetSpecies.BEARDED_DRAGON,
        "birthday": datetime(2024, 6, 1, tzinfo=timezone.utc),
        "parent_id": parent_id or PARENT_USER.id,
        "is_active": True,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }
    defaults.update(overrides)
    return Pet(**defaults)


def make_assignment(kid=None, chore=None, parent_id=None, **overrides):
    from backend.models import ChoreAssignment, ChoreAssignmentStatus

    kid = kid or KID_USER
    defaults = {
        "id": f"assign-{uuid.uuid4().hex[:8]}",
        "chore_id": chore.id if chore else f"chore-{uuid.uuid4().hex[:8]}",
        "chore_name": chore.name if chore else "Test Chore",
        "assigned_to_kid_id": kid.username,
        "kid_username": kid.username,
        "assigned_by_parent_id": parent_id or PARENT_USER.id,
        "points_value": chore.points_value if chore else 10,
        "due_date": datetime.now(timezone.utc),
        "assignment_status": ChoreAssignmentStatus.ASSIGNED,
        "created_at": datetime.now(timezone.utc),
    }
    defaults.update(overrides)
    return ChoreAssignment(**defaults)


def make_request(kid=None, **overrides):
    from backend.models import Request, RequestStatus, RequestType

    kid = kid or KID_USER
    defaults = {
        "id": f"req-{uuid.uuid4().hex[:8]}",
        "requester_id": kid.id,
        "requester_username": kid.username,
        "request_type": RequestType.OTHER,
        "details": {"message": "test request"},
        "status": RequestStatus.PENDING,
        "created_at": datetime.now(timezone.utc),
    }
    defaults.update(overrides)
    return Request(**defaults)
