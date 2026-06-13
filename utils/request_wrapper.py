"""
utils/request_wrapper.py
─────────────────────────
Low-level HTTP client that wraps `requests.Session` with:
  • Automatic retries (tenacity)
  • Full request / response logging
  • Elapsed-time tracking
  • Allure attachment hooks
"""

from __future__ import annotations

import json
import time
from typing import Any

import allure
import requests
from requests import Response
from tenacity import (
    retry,
    retry_if_exception_type,
    retry_if_result,
    stop_after_attempt,
    wait_fixed,
)

from configs.config_manager import get_config
from utils.logger import get_logger

logger = get_logger(__name__)

# Status codes that should trigger a retry
_RETRYABLE_STATUSES: frozenset[int] = frozenset([429, 500, 502, 503, 504])


def _is_retryable_response(response: Response) -> bool:
    return response.status_code in _RETRYABLE_STATUSES


class RequestWrapper:
    """
    Thin wrapper around `requests.Session`.

    Each instance owns one Session so that connection pooling and
    per-client headers are kept separate.
    """

    def __init__(
        self,
        base_url: str = "",
        default_headers: dict[str, str] | None = None,
        timeout: int | None = None,
    ) -> None:
        cfg = get_config()
        self._base_url = base_url or cfg.base_url
        self._timeout = timeout or cfg.timeout
        self._session = requests.Session()
        self._session.headers.update(
            {
                "Content-Type": "application/json",
                "Accept": "application/json",
                **(default_headers or {}),
            }
        )
        logger.debug(
            "RequestWrapper initialised — base_url=%s timeout=%s",
            self._base_url,
            self._timeout,
        )

    # ── Session header shortcuts ─────────────────────────────────────────────

    def set_auth_header(self, token: str, scheme: str = "Bearer") -> None:
        self._session.headers["Authorization"] = f"{scheme} {token}"

    def set_headers(self, headers: dict[str, str]) -> None:
        self._session.headers.update(headers)

    # ── Core HTTP verbs ──────────────────────────────────────────────────────

    def get(self, endpoint: str, **kwargs: Any) -> Response:
        return self._send("GET", endpoint, **kwargs)

    def post(self, endpoint: str, **kwargs: Any) -> Response:
        return self._send("POST", endpoint, **kwargs)

    def put(self, endpoint: str, **kwargs: Any) -> Response:
        return self._send("PUT", endpoint, **kwargs)

    def patch(self, endpoint: str, **kwargs: Any) -> Response:
        return self._send("PATCH", endpoint, **kwargs)

    def delete(self, endpoint: str, **kwargs: Any) -> Response:
        return self._send("DELETE", endpoint, **kwargs)

    # ── Internal dispatcher ──────────────────────────────────────────────────

    def _send(self, method: str, endpoint: str, **kwargs: Any) -> Response:
        cfg = get_config()
        url = self._build_url(endpoint)
        kwargs.setdefault("timeout", self._timeout)

        @retry(
            stop=stop_after_attempt(cfg.retry.max_retries + 1),
            wait=wait_fixed(cfg.retry.retry_delay),
            retry=(
                retry_if_result(_is_retryable_response)
                | retry_if_exception_type(requests.exceptions.ConnectionError)
                | retry_if_exception_type(requests.exceptions.Timeout)
            ),
            reraise=True,
        )
        def _do_request() -> Response:
            self._log_request(method, url, kwargs)
            start = time.perf_counter()
            response = self._session.request(method, url, **kwargs)
            elapsed_ms = (time.perf_counter() - start) * 1000
            self._log_response(response, elapsed_ms)
            self._attach_to_allure(method, url, kwargs, response, elapsed_ms)
            return response

        return _do_request()

    def _build_url(self, endpoint: str) -> str:
        if endpoint.startswith("http://") or endpoint.startswith("https://"):
            return endpoint
        return f"{self._base_url.rstrip('/')}/{endpoint.lstrip('/')}"

    # ── Logging helpers ──────────────────────────────────────────────────────

    @staticmethod
    def _log_request(method: str, url: str, kwargs: dict) -> None:
        body = kwargs.get("json") or kwargs.get("data") or ""
        params = kwargs.get("params", "")
        logger.info("→ %s %s  params=%s  body=%s", method, url, params, body)

    @staticmethod
    def _log_response(response: Response, elapsed_ms: float) -> None:
        level = logger.warning if response.status_code >= 400 else logger.info
        level(
            "← %s %s  [%dms]",
            response.status_code,
            response.url,
            elapsed_ms,
        )
        if response.status_code >= 400:
            logger.debug("Response body: %s", response.text[:2000])

    # ── Allure attachment ────────────────────────────────────────────────────

    @staticmethod
    def _attach_to_allure(
        method: str,
        url: str,
        kwargs: dict,
        response: Response,
        elapsed_ms: float,
    ) -> None:
        try:
            req_body = kwargs.get("json") or kwargs.get("data") or {}
            allure.attach(
                json.dumps(
                    {
                        "method": method,
                        "url": url,
                        "params": kwargs.get("params"),
                        "headers": dict(kwargs.get("headers", {})),
                        "body": req_body,
                    },
                    indent=2,
                    default=str,
                ),
                name="Request",
                attachment_type=allure.attachment_type.JSON,
            )

            try:
                resp_body = response.json()
            except Exception:
                resp_body = response.text

            allure.attach(
                json.dumps(
                    {
                        "status_code": response.status_code,
                        "elapsed_ms": round(elapsed_ms, 2),
                        "headers": dict(response.headers),
                        "body": resp_body,
                    },
                    indent=2,
                    default=str,
                ),
                name="Response",
                attachment_type=allure.attachment_type.JSON,
            )
        except Exception:
            # Allure attachment must never break a test
            pass

    # ── Context manager support ──────────────────────────────────────────────

    def __enter__(self) -> "RequestWrapper":
        return self

    def __exit__(self, *_: Any) -> None:
        self._session.close()
