"""
conftest.py
────────────
Global pytest fixtures, hooks, and plugin configuration.
This file is auto-loaded by pytest for every test in the project.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Generator

import allure
import pytest
from requests import Response

from api_clients.posts_client import PostsClient
from api_clients.users_client import UsersClient
from configs.config_manager import get_config
from utils.data_manager import post_factory, user_factory
from utils.logger import get_logger
from utils.token_manager import token_manager

logger = get_logger("conftest")


# ═══════════════════════════════════════════════════════════════════════════════
# Session-scoped fixtures
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="session")
def config():
    """Expose the active Config object to all tests."""
    cfg = get_config()
    logger.info(
        "Test session started — env=%s  base_url=%s",
        cfg.env,
        cfg.base_url,
    )
    return cfg


@pytest.fixture(scope="session")
def users_client() -> Generator[UsersClient, None, None]:
    client = UsersClient()
    yield client


@pytest.fixture(scope="session")
def posts_client() -> Generator[PostsClient, None, None]:
    client = PostsClient()
    yield client


# ═══════════════════════════════════════════════════════════════════════════════
# Function-scoped fixtures
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.fixture
def user_payload() -> dict:
    return user_factory.create_user()


@pytest.fixture
def post_payload() -> dict:
    return post_factory.create_post(user_id=1)


@pytest.fixture
def created_post(posts_client: PostsClient, post_payload: dict) -> Generator[dict, None, None]:
    """Create a post before the test, yield its data, skip teardown for placeholder API."""
    response = posts_client.create_post(post_payload)
    assert response.status_code == 201, f"Setup failed: {response.text}"
    post = response.json()
    logger.debug("Test fixture: created post id=%s", post.get("id"))
    yield post
    # Teardown — real APIs: posts_client.delete_post(post["id"])
    logger.debug("Test fixture: teardown for post id=%s", post.get("id"))


# ═══════════════════════════════════════════════════════════════════════════════
# Hooks
# ═══════════════════════════════════════════════════════════════════════════════

def pytest_configure(config: pytest.Config) -> None:
    """Register custom markers so pytest doesn't warn about unknown marks."""
    config.addinivalue_line("markers", "smoke: quick sanity checks")
    config.addinivalue_line("markers", "regression: full regression suite")
    config.addinivalue_line("markers", "integration: cross-service tests")
    config.addinivalue_line("markers", "slow: tests expected to run > 2 s")
    config.addinivalue_line("markers", "auth: tests that require authentication")


def pytest_runtest_setup(item: pytest.Item) -> None:
    logger.info("▶ %s", item.nodeid)


def pytest_runtest_teardown(item: pytest.Item, nextitem: pytest.Item | None) -> None:
    logger.debug("■ %s", item.nodeid)


def pytest_runtest_logreport(report: pytest.TestReport) -> None:
    if report.when == "call":
        status = "PASSED" if report.passed else ("FAILED" if report.failed else "SKIPPED")
        level = logger.info if report.passed else logger.error
        level("%s — %s", status, report.nodeid)


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    passed = session.testscollected - session.testsfailed - getattr(session, "testsskipped", 0)
    logger.info(
        "Session finished — collected=%d  passed=%d  failed=%d  exit=%d",
        session.testscollected,
        passed,
        session.testsfailed,
        exitstatus,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Allure environment properties
# ═══════════════════════════════════════════════════════════════════════════════

def pytest_sessionstart(session: pytest.Session) -> None:
    cfg = get_config()
    allure_dir = Path("reports/allure-results")
    allure_dir.mkdir(parents=True, exist_ok=True)
    env_props = allure_dir / "environment.properties"
    env_props.write_text(
        f"Environment={cfg.env}\n"
        f"Base.URL={cfg.base_url}\n"
        f"API.Version={cfg.api_version}\n"
        f"Python.Version=3.11\n",
        encoding="utf-8",
    )
