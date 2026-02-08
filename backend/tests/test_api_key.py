from unittest.mock import patch

import pytest

from tests.conftest import PARENT_USER, make_user


@pytest.fixture()
def parent_api_with_crud(parent_api):
    return parent_api


def _mock_get_user(user):
    return patch("crud.get_user_by_username", return_value=user)


def _mock_set_key(user):
    return patch("crud.set_user_api_key_hash", return_value=user)


class TestGenerateApiKey:
    def test_generate_api_key(self, parent_api):
        with _mock_set_key(PARENT_USER):
            resp = parent_api.post("/users/me/api-key")
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        api_key = body["data"]["api_key"]
        assert api_key.startswith(f"{PARENT_USER.username}.")
        parts = api_key.split(".", 1)
        assert len(parts) == 2
        assert len(parts[1]) > 10

    def test_generate_api_key_message(self, parent_api):
        with _mock_set_key(PARENT_USER):
            resp = parent_api.post("/users/me/api-key")
        body = resp.json()
        assert "cannot be retrieved" in body["data"]["message"].lower()


class TestAuthWithApiKey:
    def test_auth_with_valid_key(self, client):
        from backend.security import generate_api_key

        full_key, key_hash = generate_api_key(PARENT_USER.username)
        user_with_key = make_user("parent", PARENT_USER.username)
        user_with_key.api_key_hash = key_hash

        with _mock_get_user(user_with_key):
            resp = client.post("/auth/api-key", json={"api_key": full_key})
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_auth_with_invalid_key(self, client):
        from backend.security import generate_api_key

        _real_key, real_hash = generate_api_key(PARENT_USER.username)
        user_with_key = make_user("parent", PARENT_USER.username)
        user_with_key.api_key_hash = real_hash

        with _mock_get_user(user_with_key):
            resp = client.post("/auth/api-key", json={"api_key": f"{PARENT_USER.username}.wrongtoken"})
        assert resp.status_code == 401

    def test_auth_with_wrong_username(self, client):
        with _mock_get_user(None):
            resp = client.post("/auth/api-key", json={"api_key": "nonexistent.sometoken"})
        assert resp.status_code == 401

    def test_auth_with_no_dot(self, client):
        resp = client.post("/auth/api-key", json={"api_key": "nodotinthiskey"})
        assert resp.status_code == 401

    def test_auth_no_key_stored(self, client):
        user_no_key = make_user("parent", PARENT_USER.username)
        user_no_key.api_key_hash = None

        with _mock_get_user(user_no_key):
            resp = client.post("/auth/api-key", json={"api_key": f"{PARENT_USER.username}.sometoken"})
        assert resp.status_code == 401


class TestRegenerateApiKey:
    def test_regenerate_invalidates_old(self, parent_api, client):
        from backend.security import generate_api_key

        old_key, old_hash = generate_api_key(PARENT_USER.username)
        new_key, new_hash = generate_api_key(PARENT_USER.username)

        user_with_new = make_user("parent", PARENT_USER.username)
        user_with_new.api_key_hash = new_hash

        with _mock_get_user(user_with_new):
            resp_old = client.post("/auth/api-key", json={"api_key": old_key})
        assert resp_old.status_code == 401

        with _mock_get_user(user_with_new):
            resp_new = client.post("/auth/api-key", json={"api_key": new_key})
        assert resp_new.status_code == 200
        assert "access_token" in resp_new.json()
