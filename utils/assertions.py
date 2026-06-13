"""
utils/assertions.py
────────────────────
Domain-level custom assertions used across all test layers.
These sit one level above ResponseValidator for high-signal test code.
"""

from __future__ import annotations

from typing import Any

from requests import Response

from utils.logger import get_logger
from utils.response_validator import validate

logger = get_logger(__name__)


# ── HTTP-level ────────────────────────────────────────────────────────────────

def assert_ok(response: Response) -> None:
    """Assert 200 OK with JSON content-type."""
    validate(response).status(200).content_type("application/json").assert_all()


def assert_created(response: Response) -> None:
    validate(response).status(201).assert_all()


def assert_no_content(response: Response) -> None:
    validate(response).status(204).assert_all()


def assert_not_found(response: Response) -> None:
    validate(response).status(404).assert_all()


def assert_bad_request(response: Response) -> None:
    validate(response).status(400).assert_all()


def assert_unauthorized(response: Response) -> None:
    validate(response).status(401).assert_all()


def assert_forbidden(response: Response) -> None:
    validate(response).status(403).assert_all()


# ── Collection assertions ────────────────────────────────────────────────────

def assert_list_response(response: Response, min_length: int = 1) -> list:
    """Assert the response is a non-empty JSON array."""
    v = validate(response).status(200).body_is_list()
    if min_length > 0:
        v.list_not_empty()
    v.assert_all()
    return v.body


def assert_paginated(
    response: Response,
    expected_total: int | None = None,
) -> dict:
    """Assert a paginated envelope has standard keys."""
    v = validate(response).status(200).has_key("data")
    if expected_total is not None:
        v.key_equals("total", expected_total)
    v.assert_all()
    return v.body


# ── Field-level ───────────────────────────────────────────────────────────────

def assert_field_equals(response: Response, field: str, expected: Any) -> None:
    validate(response).status(200).key_equals(field, expected).assert_all()


def assert_field_present(response: Response, *fields: str) -> None:
    v = validate(response).status(200)
    for field in fields:
        v.has_key(field)
    v.assert_all()


def assert_id_returned(response: Response) -> int:
    """Assert the response contains an 'id' field and return its value."""
    v = validate(response).success().has_key("id")
    v.assert_all()
    return v.body["id"]


# ── Performance ───────────────────────────────────────────────────────────────

def assert_fast(response: Response, max_ms: float = 2000) -> None:
    validate(response).response_time_under(max_ms).assert_all()


# ── Generic helper ────────────────────────────────────────────────────────────

def soft_assert(condition: bool, message: str) -> None:
    """
    Non-fatal assertion. Logs a warning instead of raising.
    Useful for informational checks that should not fail the test.
    """
    if not condition:
        logger.warning("Soft assertion failed: %s", message)
    else:
        logger.debug("Soft assertion passed: %s", message)
