"""
api_clients/posts_client.py
────────────────────────────
Resource client for the /posts endpoint.
"""

from __future__ import annotations

from typing import Any

from requests import Response

from api_clients.base_client import BaseClient


class PostsClient(BaseClient):
    RESOURCE = "posts"

    def get_all_posts(self, params: dict | None = None) -> Response:
        """GET /posts"""
        return self._get(params=params)

    def get_post(self, post_id: int) -> Response:
        """GET /posts/{post_id}"""
        return self._get(post_id)

    def get_post_comments(self, post_id: int) -> Response:
        """GET /posts/{post_id}/comments"""
        return self._get(post_id, "comments")

    def create_post(self, payload: dict[str, Any]) -> Response:
        """POST /posts"""
        return self._post(json=payload)

    def update_post(self, post_id: int, payload: dict[str, Any]) -> Response:
        """PUT /posts/{post_id}"""
        return self._put(post_id, json=payload)

    def partial_update_post(self, post_id: int, payload: dict[str, Any]) -> Response:
        """PATCH /posts/{post_id}"""
        return self._patch(post_id, json=payload)

    def delete_post(self, post_id: int) -> Response:
        """DELETE /posts/{post_id}"""
        return self._delete(post_id)
