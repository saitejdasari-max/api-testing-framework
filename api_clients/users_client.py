"""
api_clients/users_client.py
────────────────────────────
Resource client for the /users endpoint.
Maps every public operation to a clean method signature.
"""

from __future__ import annotations

from typing import Any

from requests import Response

from api_clients.base_client import BaseClient


class UsersClient(BaseClient):
    RESOURCE = "users"

    # ── Read ──────────────────────────────────────────────────────────────────

    def get_all_users(self, params: dict | None = None) -> Response:
        """GET /users"""
        return self._get(params=params)

    def get_user(self, user_id: int) -> Response:
        """GET /users/{user_id}"""
        return self._get(user_id)

    def get_user_posts(self, user_id: int) -> Response:
        """GET /users/{user_id}/posts"""
        return self._get(user_id, "posts")

    def get_user_albums(self, user_id: int) -> Response:
        """GET /users/{user_id}/albums"""
        return self._get(user_id, "albums")

    # ── Write ─────────────────────────────────────────────────────────────────

    def create_user(self, payload: dict[str, Any]) -> Response:
        """POST /users"""
        return self._post(json=payload)

    def update_user(self, user_id: int, payload: dict[str, Any]) -> Response:
        """PUT /users/{user_id}"""
        return self._put(user_id, json=payload)

    def partial_update_user(self, user_id: int, payload: dict[str, Any]) -> Response:
        """PATCH /users/{user_id}"""
        return self._patch(user_id, json=payload)

    def delete_user(self, user_id: int) -> Response:
        """DELETE /users/{user_id}"""
        return self._delete(user_id)
