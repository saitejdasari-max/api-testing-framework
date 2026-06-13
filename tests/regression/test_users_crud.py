"""
tests/regression/test_users_crud.py
─────────────────────────────────────
Full CRUD regression tests for the Users resource.
Covers happy-path and negative scenarios.
"""

from __future__ import annotations

import allure
import pytest

from api_clients.users_client import UsersClient
from data.schemas.models import UserSchema
from utils.assertions import (
    assert_created,
    assert_field_present,
    assert_id_returned,
    assert_list_response,
    assert_no_content,
    assert_not_found,
    assert_ok,
)
from utils.data_manager import UserDataFactory
from utils.response_validator import validate


@allure.epic("User Management")
@allure.feature("CRUD")
@pytest.mark.regression
class TestUsersCRUD:

    # ── GET all ───────────────────────────────────────────────────────────────

    @allure.story("Read")
    @allure.title("GET /users — schema validation for every item")
    def test_get_all_users_schema(self, users_client: UsersClient) -> None:
        response = users_client.get_all_users()
        validate(response).status(200).matches_schema(UserSchema).assert_all()

    @allure.story("Read")
    @allure.title("GET /users — filter by username query param")
    def test_filter_users_by_username(self, users_client: UsersClient) -> None:
        response = users_client.get_all_users(params={"username": "Bret"})
        users = assert_list_response(response, min_length=1)
        assert all(u["username"] == "Bret" for u in users), \
            "Filter returned users with wrong username"

    # ── GET single ────────────────────────────────────────────────────────────

    @allure.story("Read")
    @allure.title("GET /users/{id} — verify all required fields present")
    @pytest.mark.parametrize("user_id", [1, 2, 5, 10])
    def test_get_user_fields(self, users_client: UsersClient, user_id: int) -> None:
        response = users_client.get_user(user_id)
        assert_field_present(response, "id", "name", "username", "email")
        validate(response).key_equals("id", user_id).assert_all()

    @allure.story("Read")
    @allure.title("GET /users/{id} — nested address and company present")
    def test_get_user_nested_objects(self, users_client: UsersClient) -> None:
        response = users_client.get_user(1)
        body = validate(response).status(200).has_key("address").has_key("company")
        body.assert_all()
        assert isinstance(response.json()["address"], dict)
        assert isinstance(response.json()["company"], dict)

    # ── POST ──────────────────────────────────────────────────────────────────

    @allure.story("Create")
    @allure.title("POST /users — creates a user and returns id")
    def test_create_user(
        self, users_client: UsersClient, user_payload: dict
    ) -> None:
        with allure.step("Send POST request"):
            response = users_client.create_user(user_payload)

        with allure.step("Assert 201 and id returned"):
            assert_created(response)
            new_id = assert_id_returned(response)
            assert new_id > 0

        with allure.step("Verify echoed fields"):
            body = response.json()
            assert body.get("name") == user_payload["name"]
            assert body.get("email") == user_payload["email"]

    @allure.story("Create")
    @allure.title("POST /users — minimal payload still returns 201")
    def test_create_user_minimal_payload(self, users_client: UsersClient) -> None:
        minimal = {"name": "Min User", "username": "minuser", "email": "min@test.com"}
        response = users_client.create_user(minimal)
        assert_created(response)

    # ── PUT ───────────────────────────────────────────────────────────────────

    @allure.story("Update")
    @allure.title("PUT /users/{id} — full replacement returns updated data")
    def test_full_update_user(self, users_client: UsersClient) -> None:
        updated_payload = UserDataFactory.create_user(name="Updated Name")
        response = users_client.update_user(1, updated_payload)

        validate(response) \
            .status(200) \
            .key_equals("id", 1) \
            .key_equals("name", "Updated Name") \
            .assert_all()

    # ── PATCH ─────────────────────────────────────────────────────────────────

    @allure.story("Update")
    @allure.title("PATCH /users/{id} — partial update applies only changed fields")
    def test_partial_update_user(self, users_client: UsersClient) -> None:
        patch_data = {"name": "Patched Name Only"}
        response = users_client.partial_update_user(1, patch_data)

        validate(response) \
            .status(200) \
            .key_equals("name", "Patched Name Only") \
            .assert_all()

    # ── DELETE ────────────────────────────────────────────────────────────────

    @allure.story("Delete")
    @allure.title("DELETE /users/{id} — returns 200 or 204")
    def test_delete_user(self, users_client: UsersClient) -> None:
        response = users_client.delete_user(1)
        validate(response).status_in(200, 204).assert_all()

    # ── Sub-resources ─────────────────────────────────────────────────────────

    @allure.story("Sub-resources")
    @allure.title("GET /users/{id}/posts — returns posts for user")
    def test_get_user_posts(self, users_client: UsersClient) -> None:
        response = users_client.get_user_posts(1)
        posts = assert_list_response(response, min_length=1)
        assert all(p.get("userId") == 1 for p in posts)

    @allure.story("Sub-resources")
    @allure.title("GET /users/{id}/albums — returns albums for user")
    def test_get_user_albums(self, users_client: UsersClient) -> None:
        response = users_client.get_user_albums(1)
        assert_list_response(response, min_length=1)

    # ── Negative ──────────────────────────────────────────────────────────────

    @allure.story("Negative")
    @allure.title("GET /users — invalid id type returns 404 or 400")
    def test_get_user_invalid_id(self, users_client: UsersClient) -> None:
        response = users_client.get_user(99999)
        validate(response).status_in(400, 404).assert_all()

    @allure.story("Negative")
    @allure.title("GET /users — empty string id returns 404 or 400")
    def test_get_user_string_id(self, users_client: UsersClient) -> None:
        # Direct call to bypass type hints
        response = users_client._client.get("users/abc")
        validate(response).status_in(400, 404).assert_all()
