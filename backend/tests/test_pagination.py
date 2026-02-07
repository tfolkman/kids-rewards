import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from unittest.mock import patch

from helpers import assert_envelope


class TestPagination:
    @patch("crud.get_store_items")
    def test_store_items_default_pagination(self, mock_get, api):
        from conftest import make_store_item

        items = [make_store_item(name=f"Item {i}") for i in range(5)]
        mock_get.return_value = items
        r = api.get("/store/items/")
        body = r.json()
        assert body["success"] is True
        assert body["meta"]["total"] == 5
        assert body["meta"]["count"] == 5
        assert body["meta"]["limit"] == 100
        assert body["meta"]["offset"] == 0

    @patch("crud.get_store_items")
    def test_store_items_limit_offset(self, mock_get, api):
        from conftest import make_store_item

        items = [make_store_item(name=f"Item {i}") for i in range(10)]
        mock_get.return_value = items
        r = api.get("/store/items/?limit=3&offset=2")
        body = r.json()
        assert body["meta"]["total"] == 10
        assert body["meta"]["count"] == 3
        assert body["meta"]["limit"] == 3
        assert body["meta"]["offset"] == 2

    @patch("crud.get_store_items")
    def test_store_items_offset_past_end(self, mock_get, api):
        from conftest import make_store_item

        items = [make_store_item(name=f"Item {i}") for i in range(3)]
        mock_get.return_value = items
        r = api.get("/store/items/?offset=10")
        body = r.json()
        assert body["meta"]["total"] == 3
        assert body["meta"]["count"] == 0
        assert body["data"] == []


class TestFiltering:
    @patch("crud.get_all_active_chores")
    def test_chores_default_active_only(self, mock_get, api):
        from conftest import make_chore

        mock_get.return_value = [make_chore()]
        r = api.get("/chores/")
        body = r.json()
        assert body["success"] is True
        mock_get.assert_called_once()

    @patch("crud.get_all_chores_scan_fallback")
    def test_chores_include_inactive(self, mock_get, api):
        from conftest import make_chore

        mock_get.return_value = [make_chore()]
        r = api.get("/chores/?include_inactive=true")
        body = r.json()
        assert body["success"] is True
        mock_get.assert_called_once()

    @patch("crud.get_assignments_by_kid_id")
    def test_assignments_filter_by_status(self, mock_get, kid_api):
        from conftest import make_assignment

        assigned = make_assignment(assignment_status="assigned")
        submitted = make_assignment(assignment_status="submitted")
        mock_get.return_value = [assigned, submitted]
        r = kid_api.get("/kids/my-assignments/?status=assigned")
        body = r.json()
        assert body["meta"]["total"] == 1
        assert body["meta"]["count"] == 1

    @patch("crud.get_all_users")
    def test_users_filter_by_role(self, mock_get, parent_api):
        from conftest import make_user

        parent = make_user("parent", "p1")
        kid = make_user("kid", "k1")
        mock_get.return_value = [parent, kid]
        r = parent_api.get("/users/?role=kid")
        body = r.json()
        assert body["meta"]["count"] == 1
