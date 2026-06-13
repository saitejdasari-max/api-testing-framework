"""
utils/data_manager.py
──────────────────────
Centralised test-data loader.
Reads JSON / YAML fixtures from data/test_data/ and exposes them to tests.
Also provides a Faker-based generator for dynamic payloads.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from faker import Faker

from configs.config_manager import get_config
from utils.logger import get_logger

logger = get_logger(__name__)
fake = Faker()

_DATA_DIR: Path | None = None


def _data_dir() -> Path:
    global _DATA_DIR
    if _DATA_DIR is None:
        _DATA_DIR = get_config().data_dir / "test_data"
        _DATA_DIR.mkdir(parents=True, exist_ok=True)
    return _DATA_DIR


# ── File loaders ─────────────────────────────────────────────────────────────

@lru_cache(maxsize=64)
def load_json(filename: str) -> Any:
    path = _data_dir() / filename
    if not path.exists():
        raise FileNotFoundError(f"Test data file not found: {path}")
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    logger.debug("Loaded JSON fixture: %s", filename)
    return data


@lru_cache(maxsize=64)
def load_yaml(filename: str) -> Any:
    path = _data_dir() / filename
    if not path.exists():
        raise FileNotFoundError(f"Test data file not found: {path}")
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    logger.debug("Loaded YAML fixture: %s", filename)
    return data


def load_schema(filename: str) -> dict:
    """Load a Pydantic/JSON-Schema file from data/schemas/."""
    schema_dir = get_config().data_dir / "schemas"
    schema_dir.mkdir(parents=True, exist_ok=True)
    path = schema_dir / filename
    if not path.exists():
        raise FileNotFoundError(f"Schema file not found: {path}")
    with path.open(encoding="utf-8") as f:
        return json.load(f)


# ── Dynamic data generators ───────────────────────────────────────────────────

class UserDataFactory:
    """Generates realistic user payloads for CRUD tests."""

    @staticmethod
    def create_user(**overrides: Any) -> dict[str, Any]:
        data: dict[str, Any] = {
            "name": fake.name(),
            "username": fake.user_name(),
            "email": fake.email(),
            "phone": fake.phone_number(),
            "website": fake.domain_name(),
            "address": {
                "street": fake.street_address(),
                "city": fake.city(),
                "zipcode": fake.zipcode(),
                "geo": {"lat": str(fake.latitude()), "lng": str(fake.longitude())},
            },
            "company": {
                "name": fake.company(),
                "catchPhrase": fake.catch_phrase(),
                "bs": fake.bs(),
            },
        }
        data.update(overrides)
        return data

    @staticmethod
    def create_partial_user(**fields: Any) -> dict[str, Any]:
        """Return only the supplied fields — useful for PATCH requests."""
        return dict(fields)


class PostDataFactory:
    """Generates blog-post payloads."""

    @staticmethod
    def create_post(user_id: int = 1, **overrides: Any) -> dict[str, Any]:
        data: dict[str, Any] = {
            "userId": user_id,
            "title": fake.sentence(nb_words=6).rstrip("."),
            "body": fake.paragraph(nb_sentences=4),
        }
        data.update(overrides)
        return data


class CommentDataFactory:
    @staticmethod
    def create_comment(post_id: int = 1, **overrides: Any) -> dict[str, Any]:
        data: dict[str, Any] = {
            "postId": post_id,
            "name": fake.sentence(nb_words=4).rstrip("."),
            "email": fake.email(),
            "body": fake.paragraph(nb_sentences=3),
        }
        data.update(overrides)
        return data


# ── Module-level singletons ──────────────────────────────────────────────────
user_factory = UserDataFactory()
post_factory = PostDataFactory()
comment_factory = CommentDataFactory()
