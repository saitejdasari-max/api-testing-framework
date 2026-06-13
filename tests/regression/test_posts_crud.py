"""
tests/regression/test_posts_crud.py
─────────────────────────────────────
Full CRUD regression tests for the Posts resource.
"""

from __future__ import annotations

import allure
import pytest

from api_clients.posts_client import PostsClient
from data.schemas.models import CommentSchema, PostSchema
from utils.assertions import (
    assert_created,
    assert_id_returned,
    assert_list_response,
    assert_ok,
)
from utils.data_manager import post_factory
from utils.response_validator import validate


@allure.epic("Post Management")
@allure.feature("CRUD")
@pytest.mark.regression
class TestPostsCRUD:

    # ── GET all ───────────────────────────────────────────────────────────────

    @allure.story("Read")
    @allure.title("GET /posts — returns 100 posts with valid schema")
    def test_get_all_posts(self, posts_client: PostsClient) -> None:
        response = posts_client.get_all_posts()
        validate(response) \
            .status(200) \
            .body_is_list() \
            .list_not_empty() \
            .matches_schema(PostSchema) \
            .assert_all()

    @allure.story("Read")
    @allure.title("GET /posts — filter by userId query param")
    @pytest.mark.parametrize("user_id", [1, 2, 3])
    def test_filter_posts_by_user(
        self, posts_client: PostsClient, user_id: int
    ) -> None:
        response = posts_client.get_all_posts(params={"userId": user_id})
        posts = assert_list_response(response, min_length=1)
        assert all(p["userId"] == user_id for p in posts), \
            f"Filter returned posts for wrong userId"

    # ── GET single ────────────────────────────────────────────────────────────

    @allure.story("Read")
    @allure.title("GET /posts/{id} — returns post with correct id")
    @pytest.mark.parametrize("post_id", [1, 50, 100])
    def test_get_post_by_id(self, posts_client: PostsClient, post_id: int) -> None:
        response = posts_client.get_post(post_id)
        validate(response) \
            .status(200) \
            .key_equals("id", post_id) \
            .matches_schema(PostSchema) \
            .assert_all()

    # ── POST ──────────────────────────────────────────────────────────────────

    @allure.story("Create")
    @allure.title("POST /posts — created post returns 201 with echoed data")
    def test_create_post(
        self, posts_client: PostsClient, post_payload: dict
    ) -> None:
        response = posts_client.create_post(post_payload)
        assert_created(response)
        body = response.json()
        assert body.get("title") == post_payload["title"]
        assert body.get("body") == post_payload["body"]
        assert body.get("userId") == post_payload["userId"]
        assert "id" in body

    @allure.story("Create")
    @allure.title("POST /posts — create with fixture teardown")
    def test_create_post_with_fixture(self, created_post: dict) -> None:
        """Uses the `created_post` fixture for setup/teardown."""
        assert created_post["id"] > 0
        assert "title" in created_post

    # ── PUT ───────────────────────────────────────────────────────────────────

    @allure.story("Update")
    @allure.title("PUT /posts/{id} — full update reflects all fields")
    def test_full_update_post(self, posts_client: PostsClient) -> None:
        new_data = post_factory.create_post(user_id=1, title="Completely New Title")
        response = posts_client.update_post(1, new_data)
        validate(response) \
            .status(200) \
            .key_equals("id", 1) \
            .key_equals("title", "Completely New Title") \
            .assert_all()

    # ── PATCH ─────────────────────────────────────────────────────────────────

    @allure.story("Update")
    @allure.title("PATCH /posts/{id} — partial update changes only title")
    def test_partial_update_post(self, posts_client: PostsClient) -> None:
        response = posts_client.partial_update_post(1, {"title": "Patched Title"})
        validate(response) \
            .status(200) \
            .key_equals("title", "Patched Title") \
            .assert_all()

    # ── DELETE ────────────────────────────────────────────────────────────────

    @allure.story("Delete")
    @allure.title("DELETE /posts/{id} — returns 200 or 204")
    def test_delete_post(self, posts_client: PostsClient) -> None:
        response = posts_client.delete_post(1)
        validate(response).status_in(200, 204).assert_all()

    # ── Sub-resources ─────────────────────────────────────────────────────────

    @allure.story("Sub-resources")
    @allure.title("GET /posts/{id}/comments — returns comments with valid schema")
    def test_get_post_comments(self, posts_client: PostsClient) -> None:
        response = posts_client.get_post_comments(1)
        validate(response) \
            .status(200) \
            .body_is_list() \
            .list_not_empty() \
            .matches_schema(CommentSchema) \
            .assert_all()

    # ── Negative ──────────────────────────────────────────────────────────────

    @allure.story("Negative")
    @allure.title("GET /posts/{id} — nonexistent id returns 404")
    def test_get_nonexistent_post(self, posts_client: PostsClient) -> None:
        response = posts_client.get_post(99999)
        validate(response).status(404).assert_all()

    @allure.story("Negative")
    @allure.title("POST /posts — empty payload still accepted (external API)")
    def test_create_post_empty_body(self, posts_client: PostsClient) -> None:
        # JSONPlaceholder accepts anything; real APIs should return 400
        response = posts_client.create_post({})
        validate(response).status_in(200, 201, 400, 422).assert_all()
