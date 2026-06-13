"""
utils/token_manager.py
───────────────────────
Thread-safe token cache with automatic refresh.
Supports Bearer JWT, API-key, and Basic auth strategies.
"""

from __future__ import annotations

import base64
import threading
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional

import requests

from configs.config_manager import get_config
from utils.logger import get_logger

logger = get_logger(__name__)


class AuthStrategy(Enum):
    BEARER = auto()
    API_KEY = auto()
    BASIC = auto()
    NO_AUTH = auto()


@dataclass
class _CachedToken:
    value: str
    expires_at: float  # epoch seconds; 0 = never expires
    strategy: AuthStrategy

    def is_expired(self) -> bool:
        if self.expires_at == 0:
            return False
        # Refresh 60 s before actual expiry to avoid edge-case failures
        return time.time() >= (self.expires_at - 60)


class TokenManager:
    """
    Manages authentication tokens for one environment.

    Usage
    ─────
    tm = TokenManager()
    headers = tm.get_auth_headers()          # Bearer
    headers = tm.get_auth_headers(AuthStrategy.API_KEY)
    """

    _instance: Optional["TokenManager"] = None
    _lock: threading.Lock = threading.Lock()

    def __new__(cls) -> "TokenManager":
        # Singleton per process
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._cache: dict[AuthStrategy, _CachedToken] = {}
                cls._instance._token_lock = threading.Lock()
        return cls._instance

    # ── Public API ──────────────────────────────────────────────────────────

    def get_auth_headers(
        self,
        strategy: AuthStrategy = AuthStrategy.BEARER,
    ) -> dict[str, str]:
        """Return HTTP headers appropriate for *strategy*."""
        match strategy:
            case AuthStrategy.BEARER:
                token = self._get_or_refresh_bearer()
                return {"Authorization": f"Bearer {token}"}
            case AuthStrategy.API_KEY:
                return {"X-API-Key": self._get_api_key()}
            case AuthStrategy.BASIC:
                return {"Authorization": f"Basic {self._get_basic_token()}"}
            case AuthStrategy.NO_AUTH:
                return {}

    def invalidate(self, strategy: AuthStrategy | None = None) -> None:
        """Force re-authentication on next request."""
        with self._token_lock:
            if strategy:
                self._cache.pop(strategy, None)
                logger.debug("Token invalidated for strategy %s", strategy.name)
            else:
                self._cache.clear()
                logger.debug("All tokens invalidated")

    # ── Internal helpers ────────────────────────────────────────────────────

    def _get_or_refresh_bearer(self) -> str:
        with self._token_lock:
            cached = self._cache.get(AuthStrategy.BEARER)
            if cached and not cached.is_expired():
                return cached.value

            logger.info("Fetching fresh Bearer token …")
            token, expires_in = self._fetch_bearer_token()
            self._cache[AuthStrategy.BEARER] = _CachedToken(
                value=token,
                expires_at=time.time() + expires_in if expires_in else 0,
                strategy=AuthStrategy.BEARER,
            )
            return token

    def _fetch_bearer_token(self) -> tuple[str, int]:
        """
        Override this method (or monkey-patch in conftest) to call your real
        auth endpoint. The stub below simulates a successful token fetch.
        """
        cfg = get_config()

        # Example: POST /auth/token  →  {"access_token": "...", "expires_in": 3600}
        # Uncomment and adapt when you have a real auth endpoint:
        #
        # resp = requests.post(
        #     f"{cfg.base_url}/auth/token",
        #     json={"username": cfg.auth.username, "password": cfg.auth.password},
        #     timeout=cfg.timeout,
        # )
        # resp.raise_for_status()
        # body = resp.json()
        # return body["access_token"], body.get("expires_in", 3600)

        # ── Stub for demo / CI without a real auth server ──────────────────
        logger.debug("Using stub token (no real auth endpoint configured)")
        stub_token = base64.b64encode(
            f"{cfg.auth.username}:{cfg.auth.password}".encode()
        ).decode()
        return stub_token, 3600

    def _get_api_key(self) -> str:
        cfg = get_config()
        if not cfg.auth.api_key:
            raise ValueError("API_KEY is not set in the environment configuration.")
        return cfg.auth.api_key

    def _get_basic_token(self) -> str:
        cfg = get_config()
        raw = f"{cfg.auth.username}:{cfg.auth.password}"
        return base64.b64encode(raw.encode()).decode()


# Module-level singleton convenience
token_manager = TokenManager()
