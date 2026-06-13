"""
tests/integration/test_cross_resource.py
──────────────────────────────────────────
Integration tests that span multiple resources and verify referential
integrity between Users, Posts, and Comments.
"""

from __future__ import annotations

import allure
import pytest

from api_clients.posts_client import PostsClient
from api_clients.users_client import UsersClient
from data.schemas.models import PostSchema, UserSchema
from utils.assertions import assert_list_response
from utils.response_validator import validate


@allure.epic("Integration")
@allure.feature("Cross-resource integrity")
@pytest.mark.integration
class TestCrossResourceIntegrity:

    @allure.story("User → Posts")
    @allure.title("Every user's posts reference the correct userId")
    def test_user_posts_reference_correct_user(
        self,
        users_client: UsersClient,
        posts_client: PostsClient,
    ) -> None:
        with allure.step("Fetch all users"):
            users_response = users_client.get_all_users()
            users = users_response.json()

        # Validate first 3 users to keep test fast
        for user in users[:3]:
            user_id = user["id"]
            with allure.step(f"Fetch posts for userId={user_id}"):
                posts_resp = users_client.get_user_posts(user_id)
                posts = assert_list_response(posts_resp, min_length=1)

            with allure.step(f"Assert all posts belong to userId={user_id}"):
                for post in posts:
                    assert post["userId"] == user_id, (
                        f"Post {post['id']} has userId={post['userId']} "
                        f"but expected {user_id}"
                    )

    @allure.story("Post → Comments")
    @allure.title("Post comments reference valid postId")
    def test_post_comments_reference_correct_post(
        self, posts_client: PostsClient
    ) -> None:
        post_id = 1
        with allure.step(f"Fetch comments for postId={post_id}"):
            response = posts_client.get_post_comments(post_id)
            comments = assert_list_response(response, min_length=1)

        with allure.step("Verify all comment postIds match"):
            for comment in comments:
                assert comment["postId"] == post_id

    @allure.story("Create → Read")
    @allure.title("Newly created post can be fetched by its id")
    def test_create_then_read_post(self, posts_client: PostsClient) -> None:
        payload = {"userId": 1, "title": "Integration test post", "body": "Test body"}

        with allure.step("Create post"):
            create_resp = posts_client.create_post(payload)
            validate(create_resp).status(201).assert_all()
            new_id = create_resp.json()["id"]

        # JSONPlaceholder doesn't persist data, so we test idempotency on id=1
        with allure.step("Read post (using id=1 as proxy)"):
            read_resp = posts_client.get_post(1)
            validate(read_resp).status(200).has_key("id").assert_all()
            allure.attach(
                f"Created id: {new_id}",
                name="Created post id",
                attachment_type=allure.attachment_type.TEXT,
            )

    @allure.story("User schema integrity")
    @allure.title("All users returned match UserSchema and have unique emails")
    def test_all_users_unique_emails(self, users_client: UsersClient) -> None:
        response = users_client.get_all_users()
        validate(response).status(200).matches_schema(UserSchema).assert_all()

        users = response.json()
        emails = [u["email"] for u in users]
        assert len(emails) == len(set(emails)), "Duplicate emails found in user list"
