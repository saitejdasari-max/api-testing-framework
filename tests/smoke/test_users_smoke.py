"""
tests/smoke/test_users_smoke.py
────────────────────────────────
Smoke tests — quick sanity checks that the Users API is reachable
and returns well-formed responses.  Should complete in < 30 s.
"""

from __future__ import annotations

import allure
import pytest

from api_clients.users_client import UsersClient
from data.schemas.models import UserSchema
from utils.assertions import assert_fast, assert_list_response, assert_ok
from utils.response_validator import validate


@allure.epic("User Management")
@allure.feature("Smoke")
@pytest.mark.smoke
class TestUsersSmoke:

    @allure.story("Health check")
    @allure.title("GET /users returns HTTP 200")
    def test_get_users_returns_200(self, users_client: UsersClient) -> None:
        with allure.step("Send GET /users"):
            response = users_client.get_all_users()

        with allure.step("Assert 200 OK"):
            assert_ok(response)

    @allure.story("Collection response")
    @allure.title("GET /users returns a non-empty list")
    def test_get_users_returns_list(self, users_client: UsersClient) -> None:
        response = users_client.get_all_users()
        users = assert_list_response(response, min_length=1)
        assert len(users) > 0

    @allure.story("Single resource")
    @allure.title("GET /users/1 returns a valid user object")
    def test_get_single_user(self, users_client: UsersClient) -> None:
        with allure.step("Fetch user with id=1"):
            response = users_client.get_user(1)

        with allure.step("Validate response"):
            validate(response) \
                .status(200) \
                .has_key("id") \
                .has_key("name") \
                .has_key("email") \
                .key_equals("id", 1) \
                .matches_schema(UserSchema) \
                .response_time_under(3000) \
                .assert_all()

    @allure.story("Performance")
    @allure.title("GET /users responds within 3 seconds")
    def test_users_response_time(self, users_client: UsersClient) -> None:
        response = users_client.get_all_users()
        assert_fast(response, max_ms=3000)

    @allure.story("Not found")
    @allure.title("GET /users/9999 returns 404")
    def test_user_not_found(self, users_client: UsersClient) -> None:
        response = users_client.get_user(9999)
        validate(response).status(404).assert_all()
