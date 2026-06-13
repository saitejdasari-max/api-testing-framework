"""
api_clients/base_client.py
───────────────────────────
Abstract base for all resource-specific API clients.
Concrete clients inherit from this and add endpoint-specific methods.
"""

from __future__ import annotations

from typing import Any

from requests import Response

from configs.config_manager import get_config
from utils.logger import get_logger
from utils.request_wrapper import RequestWrapper
from utils.token_manager import AuthStrategy, token_manager


class BaseClient:
    """
    Base API client.

    Each concrete client should:
      1. Call ``super().__init__()``
      2. Define a ``RESOURCE`` class variable (e.g. ``"posts"``)
      3. Optionally override ``_build_endpoint`` for non-standard URL shapes
    """

    RESOURCE: str = ""

    def __init__(
        self,
        auth_strategy: AuthStrategy = AuthStrategy.NO_AUTH,
        extra_headers: dict[str, str] | None = None,
    ) -> None:
        cfg = get_config()
        self._logger = get_logger(self.__class__.__name__)
        self._auth_strategy = auth_strategy

        # Build default headers: auth + any extras
        headers: dict[str, str] = token_manager.get_auth_headers(auth_strategy)
        if extra_headers:
            headers.update(extra_headers)

        self._client = RequestWrapper(
            base_url=cfg.base_url,
            default_headers=headers,
            timeout=cfg.timeout,
        )
        self._logger.debug(
            "%s initialised (env=%s, auth=%s)",
            self.__class__.__name__,
            cfg.env,
            auth_strategy.name,
        )

    # ── Endpoint builder ──────────────────────────────────────────────────────

    def _build_endpoint(self, *parts: str | int) -> str:
        segments = [self.RESOURCE] + [str(p) for p in parts]
        return "/".join(s.strip("/") for s in segments if s != "")

    # ── Generic CRUD passthrough ──────────────────────────────────────────────

    def _get(self, *parts: str | int, **kwargs: Any) -> Response:
        return self._client.get(self._build_endpoint(*parts), **kwargs)

    def _post(self, *parts: str | int, **kwargs: Any) -> Response:
        return self._client.post(self._build_endpoint(*parts), **kwargs)

    def _put(self, *parts: str | int, **kwargs: Any) -> Response:
        return self._client.put(self._build_endpoint(*parts), **kwargs)

    def _patch(self, *parts: str | int, **kwargs: Any) -> Response:
        return self._client.patch(self._build_endpoint(*parts), **kwargs)

    def _delete(self, *parts: str | int, **kwargs: Any) -> Response:
        return self._client.delete(self._build_endpoint(*parts), **kwargs)

    # ── Context manager ───────────────────────────────────────────────────────

    def __enter__(self) -> "BaseClient":
        return self

    def __exit__(self, *_: Any) -> None:
        self._client.__exit__()
