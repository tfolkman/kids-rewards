import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from unittest.mock import patch

from conftest import (
    KID_USER,
    PARENT_USER,
    make_chore,
    make_chore_log,
    make_purchase_log,
    make_store_item,
)
from helpers import assert_envelope, assert_envelope_list, assert_error


class TestEnvelopeOnSuccess:
    def test_health_not_wrapped(self, api):
        r = api.get("/health")
        body = r.json()
        assert body == {"status": "healthy"}
        assert "success" not in body

    def test_root_not_wrapped(self, api):
        r = api.get("/")
        body = r.json()
        assert "message" in body
        assert "success" not in body

    @patch("crud.get_all_active_chores")
    def test_list_endpoint_wrapped(self, mock_chores, parent_api):
        chore = make_chore()
        mock_chores.return_value = [chore]
        r = parent_api.get("/chores/")
        data = assert_envelope_list(r, 200)
        assert len(data) == 1
        assert data[0]["name"] == "Test Chore"

    @patch("crud.get_all_active_chores")
    def test_list_meta_has_count(self, mock_chores, parent_api):
        mock_chores.return_value = [make_chore(), make_chore()]
        r = parent_api.get("/chores/")
        body = r.json()
        assert body["meta"]["count"] == 2

    @patch("crud.get_store_item_by_id")
    def test_single_item_wrapped(self, mock_get, parent_api):
        item = make_store_item()
        mock_get.return_value = item
        r = parent_api.get(f"/store/items/{item.id}")
        data = assert_envelope(r, 200)
        assert data["name"] == "Test Item"

    @patch("crud.create_store_item")
    def test_create_wrapped_with_201(self, mock_create, parent_api):
        item = make_store_item()
        mock_create.return_value = item
        r = parent_api.post("/store/items/", json={"name": "New", "points_cost": 10})
        data = assert_envelope(r, 201)
        assert data["name"] == item.name

    @patch("crud.delete_store_item")
    def test_delete_returns_success_envelope(self, mock_del, parent_api):
        mock_del.return_value = True
        r = parent_api.delete("/store/items/test-id")
        data = assert_envelope(r, 200)
        assert data is None


class TestEnvelopeOnError:
    def test_404_wrapped(self, parent_api):
        with patch("crud.get_store_item_by_id", return_value=None):
            r = parent_api.get("/store/items/nonexistent")
            err = assert_error(r, 404, "NOT_FOUND")
            assert "not found" in err["message"].lower()

    def test_401_wrapped(self):
        from fastapi.testclient import TestClient

        from backend.main import app

        app.dependency_overrides.clear()
        with TestClient(app) as unauth:
            r = unauth.get("/users/me/")
            assert_error(r, 401, "INVALID_CREDENTIALS")
        app.dependency_overrides.clear()

    def test_validation_error_wrapped(self, parent_api):
        r = parent_api.post("/store/items/", json={"name": "Bad", "points_cost": -1})
        err = assert_error(r, 422, "VALIDATION_ERROR")
        assert "fields" in err.get("details", {})

    @patch("crud.get_user_by_username")
    def test_400_already_exists(self, mock_get, api):
        from backend.models import User, UserRole

        mock_get.return_value = User(id="x", username="exists", role=UserRole.KID, hashed_password="h", points=0)
        r = api.post("/users/", json={"username": "exists", "password": "pass1234"})
        assert_error(r, 400, "ALREADY_EXISTS")

    @patch("crud.get_store_item_by_id")
    def test_400_insufficient_points(self, mock_item, kid_api):
        item = make_store_item(points_cost=99999)
        mock_item.return_value = item
        r = kid_api.post("/kids/redeem-item/", json={"item_id": item.id})
        assert_error(r, 400, "INSUFFICIENT_POINTS")


class TestEnvelopeListEndpoints:
    @patch("crud.get_store_items")
    def test_store_items_list(self, mock_items, parent_api):
        mock_items.return_value = [make_store_item(), make_store_item()]
        r = parent_api.get("/store/items/")
        data = assert_envelope_list(r, 200, min_count=2)
        assert all("name" in item for item in data)

    @patch("crud.get_all_users")
    def test_leaderboard(self, mock_users, parent_api):
        mock_users.return_value = [PARENT_USER, KID_USER]
        r = parent_api.get("/leaderboard")
        assert_envelope_list(r, 200, min_count=2)

    @patch("crud.get_chore_logs_by_kid_id")
    def test_chore_history(self, mock_logs, kid_api):
        mock_logs.return_value = [make_chore_log()]
        r = kid_api.get("/chores/history/me")
        assert_envelope_list(r, 200, min_count=1)

    @patch("crud.get_purchase_logs_by_user_id")
    def test_purchase_history(self, mock_logs, kid_api):
        mock_logs.return_value = [make_purchase_log()]
        r = kid_api.get("/users/me/purchase-history")
        assert_envelope_list(r, 200, min_count=1)

    @patch("crud.get_chore_logs_by_status_for_parent")
    def test_pending_chore_submissions(self, mock_logs, parent_api):
        mock_logs.return_value = []
        r = parent_api.get("/parent/chore-submissions/pending")
        assert_envelope_list(r, 200)

    @patch("crud.get_purchase_logs_by_status")
    def test_pending_purchases(self, mock_logs, parent_api):
        mock_logs.return_value = []
        r = parent_api.get("/parent/purchase-requests/pending")
        assert_envelope_list(r, 200)

    @patch("crud.get_requests_by_status")
    def test_pending_requests(self, mock_reqs, parent_api):
        mock_reqs.return_value = []
        r = parent_api.get("/parent/requests/pending/")
        assert_envelope_list(r, 200)

    @patch("crud.get_assignments_by_kid_id")
    def test_kid_assignments(self, mock_assigns, kid_api):
        mock_assigns.return_value = []
        r = kid_api.get("/kids/my-assignments/")
        assert_envelope_list(r, 200)

    @patch("crud.get_active_pets")
    def test_pets_list(self, mock_pets, parent_api):
        mock_pets.return_value = []
        r = parent_api.get("/pets/")
        assert_envelope_list(r, 200)


class TestEnvelopeSingleEndpoints:
    @patch("crud.get_chore_by_id")
    def test_get_chore(self, mock_get, parent_api):
        chore = make_chore()
        mock_get.return_value = chore
        r = parent_api.get(f"/chores/{chore.id}")
        data = assert_envelope(r, 200)
        assert data["id"] == chore.id

    def test_get_me(self, parent_api):
        r = parent_api.get("/users/me/")
        data = assert_envelope(r, 200)
        assert data["username"] == PARENT_USER.username
