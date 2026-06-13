"""
utils/response_validator.py
────────────────────────────
Fluent, chainable response validator.

Usage
─────
    validate(response) \\
        .status(200) \\
        .has_key("id") \\
        .matches_schema(MyPydanticModel) \\
        .response_time_under(500) \\
        .assert_all()
"""

from __future__ import annotations

import time
from typing import Any, Callable, Type

from pydantic import BaseModel
from requests import Response

from utils.logger import get_logger

logger = get_logger(__name__)


class ValidationError(AssertionError):
    """Raised when one or more response validations fail."""


class ResponseValidator:
    """Fluent response validator with deferred assertion collection."""

    def __init__(self, response: Response) -> None:
        self._response = response
        self._failures: list[str] = []

        try:
            self._body: Any = response.json()
        except Exception:
            self._body = response.text

    # ── Status codes ─────────────────────────────────────────────────────────

    def status(self, expected: int) -> "ResponseValidator":
        actual = self._response.status_code
        if actual != expected:
            self._fail(f"Expected status {expected}, got {actual}")
        else:
            logger.debug("✓ status %d", actual)
        return self

    def status_in(self, *codes: int) -> "ResponseValidator":
        actual = self._response.status_code
        if actual not in codes:
            self._fail(f"Expected status in {codes}, got {actual}")
        return self

    def success(self) -> "ResponseValidator":
        return self.status_in(200, 201, 202, 204)

    # ── Body checks ──────────────────────────────────────────────────────────

    def has_key(self, key: str) -> "ResponseValidator":
        if not isinstance(self._body, dict) or key not in self._body:
            self._fail(f"Response body missing key '{key}'")
        else:
            logger.debug("✓ key '%s' present", key)
        return self

    def key_equals(self, key: str, expected: Any) -> "ResponseValidator":
        if not isinstance(self._body, dict):
            self._fail("Response body is not a JSON object")
            return self
        actual = self._body.get(key)
        if actual != expected:
            self._fail(f"body['{key}'] expected {expected!r}, got {actual!r}")
        return self

    def key_type(self, key: str, expected_type: type) -> "ResponseValidator":
        if not isinstance(self._body, dict):
            self._fail("Response body is not a JSON object")
            return self
        value = self._body.get(key)
        if not isinstance(value, expected_type):
            self._fail(
                f"body['{key}'] expected type {expected_type.__name__}, "
                f"got {type(value).__name__}"
            )
        return self

    def body_contains(self, substring: str) -> "ResponseValidator":
        text = str(self._body)
        if substring not in text:
            self._fail(f"Response body does not contain '{substring}'")
        return self

    def body_is_list(self) -> "ResponseValidator":
        if not isinstance(self._body, list):
            self._fail("Expected response body to be a JSON array")
        return self

    def list_not_empty(self) -> "ResponseValidator":
        self.body_is_list()
        if isinstance(self._body, list) and len(self._body) == 0:
            self._fail("Response body list is empty")
        return self

    def list_length(self, expected: int) -> "ResponseValidator":
        self.body_is_list()
        if isinstance(self._body, list) and len(self._body) != expected:
            self._fail(f"Expected list length {expected}, got {len(self._body)}")
        return self

    # ── Pydantic schema validation ────────────────────────────────────────────

    def matches_schema(self, model: Type[BaseModel]) -> "ResponseValidator":
        """Validate the response body against a Pydantic v2 model."""
        try:
            if isinstance(self._body, list):
                for i, item in enumerate(self._body):
                    model.model_validate(item)
            else:
                model.model_validate(self._body)
            logger.debug("✓ schema validated against %s", model.__name__)
        except Exception as exc:
            self._fail(f"Schema validation failed ({model.__name__}): {exc}")
        return self

    # ── Header checks ────────────────────────────────────────────────────────

    def header_present(self, header: str) -> "ResponseValidator":
        if header.lower() not in {k.lower() for k in self._response.headers}:
            self._fail(f"Response missing header '{header}'")
        return self

    def header_equals(self, header: str, expected: str) -> "ResponseValidator":
        actual = self._response.headers.get(header, "")
        if actual.lower() != expected.lower():
            self._fail(f"Header '{header}': expected '{expected}', got '{actual}'")
        return self

    def content_type(self, expected: str = "application/json") -> "ResponseValidator":
        ct = self._response.headers.get("Content-Type", "")
        if expected.lower() not in ct.lower():
            self._fail(f"Content-Type: expected '{expected}', got '{ct}'")
        return self

    # ── Performance checks ────────────────────────────────────────────────────

    def response_time_under(self, max_ms: float) -> "ResponseValidator":
        elapsed_ms = self._response.elapsed.total_seconds() * 1000
        if elapsed_ms > max_ms:
            self._fail(
                f"Response time {elapsed_ms:.0f}ms exceeds threshold {max_ms}ms"
            )
        else:
            logger.debug("✓ response time %.0fms < %.0fms", elapsed_ms, max_ms)
        return self

    # ── Custom predicate ─────────────────────────────────────────────────────

    def satisfies(
        self,
        predicate: Callable[[Any], bool],
        description: str = "custom predicate",
    ) -> "ResponseValidator":
        try:
            result = predicate(self._body)
        except Exception as exc:
            self._fail(f"Predicate '{description}' raised {exc}")
            return self
        if not result:
            self._fail(f"Predicate '{description}' returned False")
        return self

    # ── Terminal ──────────────────────────────────────────────────────────────

    def assert_all(self) -> "ResponseValidator":
        """Raise ValidationError if any check failed."""
        if self._failures:
            summary = "\n".join(f"  • {f}" for f in self._failures)
            raise ValidationError(
                f"{len(self._failures)} validation failure(s):\n{summary}"
            )
        logger.info("✓ All response validations passed")
        return self

    @property
    def body(self) -> Any:
        return self._body

    @property
    def response(self) -> Response:
        return self._response

    # ── Private ───────────────────────────────────────────────────────────────

    def _fail(self, message: str) -> None:
        logger.warning("✗ %s", message)
        self._failures.append(message)


# ── Convenience factory ───────────────────────────────────────────────────────

def validate(response: Response) -> ResponseValidator:
    """Shorthand: ``validate(resp).status(200).assert_all()``"""
    return ResponseValidator(response)
