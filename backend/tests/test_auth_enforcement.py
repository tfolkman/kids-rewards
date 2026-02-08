import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from unittest.mock import patch

from fastapi.testclient import TestClient
from helpers import assert_error

from backend.main import app


def _unauth_client():
    app.dependency_overrides.clear()
    return TestClient(app)


class TestAuthEnforcement:
    def test_store_create_requires_auth(self):
        c = _unauth_client()
        r = c.post("/store/items/", json={"name": "Hack", "points_cost": 1})
        assert_error(r, 401, "INVALID_CREDENTIALS")

    def test_store_update_requires_auth(self):
        c = _unauth_client()
        r = c.put("/store/items/x", json={"name": "Hack", "points_cost": 1})
        assert_error(r, 401, "INVALID_CREDENTIALS")

    def test_store_delete_requires_auth(self):
        c = _unauth_client()
        r = c.delete("/store/items/x")
        assert_error(r, 401, "INVALID_CREDENTIALS")

    def test_award_points_requires_auth(self):
        c = _unauth_client()
        r = c.post("/kids/award-points/", json={"kid_username": "x", "points": 100})
        assert_error(r, 401, "INVALID_CREDENTIALS")

    def test_promote_requires_auth(self):
        c = _unauth_client()
        r = c.post("/users/promote-to-parent", json={"username": "x"})
        assert_error(r, 401, "INVALID_CREDENTIALS")

    def test_purchase_approve_requires_auth(self):
        c = _unauth_client()
        r = c.post("/parent/purchase-requests/approve", json={"log_id": "x"})
        assert_error(r, 401, "INVALID_CREDENTIALS")

    def test_purchase_reject_requires_auth(self):
        c = _unauth_client()
        r = c.post("/parent/purchase-requests/reject", json={"log_id": "x"})
        assert_error(r, 401, "INVALID_CREDENTIALS")

    def test_pending_purchases_requires_auth(self):
        c = _unauth_client()
        r = c.get("/parent/purchase-requests/pending")
        assert_error(r, 401, "INVALID_CREDENTIALS")

    def test_store_create_requires_parent(self, kid_api):
        r = kid_api.post("/store/items/", json={"name": "Hack", "points_cost": 1})
        assert_error(r, 403, "FORBIDDEN")

    def test_award_points_requires_parent(self, kid_api):
        r = kid_api.post("/kids/award-points/", json={"kid_username": "x", "points": 100})
        assert_error(r, 403, "FORBIDDEN")

    @patch("crud.create_store_item")
    def test_store_create_works_for_parent(self, mock_create, parent_api):
        from conftest import make_store_item

        mock_create.return_value = make_store_item()
        r = parent_api.post("/store/items/", json={"name": "OK", "points_cost": 10})
        assert r.status_code == 201

    @patch("crud.get_user_by_username")
    @patch("crud.update_user_points")
    def test_award_points_works_for_parent(self, mock_update, mock_get, parent_api):
        from conftest import KID_USER

        mock_get.return_value = KID_USER
        mock_update.return_value = KID_USER
        r = parent_api.post("/kids/award-points/", json={"kid_username": "testkid", "points": 10})
        assert r.status_code == 200
