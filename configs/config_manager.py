"""
configs/config_manager.py
─────────────────────────
Central configuration loader. Reads environment variables and YAML overrides,
then exposes a single typed Config object to the entire framework.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Literal

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator

# ── Resolve project root ────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env", override=False)

EnvName = Literal["dev", "staging", "production"]


# ── Sub-models ──────────────────────────────────────────────────────────────

class AuthConfig(BaseModel):
    username: str = Field(default="")
    password: str = Field(default="")
    api_key: str = Field(default="")
    jwt_secret: str = Field(default="")


class RetryConfig(BaseModel):
    max_retries: int = Field(default=3, ge=0, le=10)
    retry_delay: float = Field(default=2.0, ge=0)
    retry_on_status: list[int] = Field(default=[429, 500, 502, 503, 504])


class LoggingConfig(BaseModel):
    level: str = Field(default="DEBUG")
    to_file: bool = Field(default=True)
    log_dir: Path = Field(default=ROOT / "logs")

    @field_validator("level")
    @classmethod
    def validate_level(cls, v: str) -> str:
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper = v.upper()
        if upper not in allowed:
            raise ValueError(f"Log level must be one of {allowed}")
        return upper


class EnvironmentConfig(BaseModel):
    base_url: str
    api_version: str = Field(default="v1")
    timeout: int = Field(default=30, ge=1)


# ── Root config ─────────────────────────────────────────────────────────────

class Config(BaseModel):
    env: EnvName = Field(default="dev")
    environment: EnvironmentConfig
    auth: AuthConfig = Field(default_factory=AuthConfig)
    retry: RetryConfig = Field(default_factory=RetryConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    reports_dir: Path = Field(default=ROOT / "reports")
    data_dir: Path = Field(default=ROOT / "data")

    @property
    def base_url(self) -> str:
        return self.environment.base_url

    @property
    def timeout(self) -> int:
        return self.environment.timeout

    @property
    def api_version(self) -> str:
        return self.environment.api_version


# ── YAML loader (optional per-env overrides) ────────────────────────────────

def _load_yaml_overrides(env: str) -> dict:
    yaml_path = ROOT / "configs" / f"{env}.yaml"
    if yaml_path.exists():
        with yaml_path.open() as f:
            return yaml.safe_load(f) or {}
    return {}


# ── Factory ─────────────────────────────────────────────────────────────────

def _build_env_config(env: str) -> EnvironmentConfig:
    prefix = {"dev": "DEV", "staging": "STAGING", "production": "PROD"}.get(env, "DEV")
    return EnvironmentConfig(
        base_url=os.getenv(f"{prefix}_BASE_URL", "https://jsonplaceholder.typicode.com"),
        api_version=os.getenv(f"{prefix}_API_VERSION", "v1"),
        timeout=int(os.getenv(f"{prefix}_TIMEOUT", "30")),
    )


@lru_cache(maxsize=1)
def get_config() -> Config:
    """Return the singleton Config for the active environment."""
    env: EnvName = os.getenv("ENV", "dev").lower()  # type: ignore[assignment]

    yaml_overrides = _load_yaml_overrides(env)

    cfg = Config(
        env=env,
        environment=_build_env_config(env),
        auth=AuthConfig(
            username=os.getenv("AUTH_USERNAME", ""),
            password=os.getenv("AUTH_PASSWORD", ""),
            api_key=os.getenv("API_KEY", ""),
            jwt_secret=os.getenv("JWT_SECRET", ""),
        ),
        retry=RetryConfig(
            max_retries=int(os.getenv("MAX_RETRIES", "3")),
            retry_delay=float(os.getenv("RETRY_DELAY", "2")),
        ),
        logging=LoggingConfig(
            level=os.getenv("LOG_LEVEL", "DEBUG"),
            to_file=os.getenv("LOG_TO_FILE", "true").lower() == "true",
        ),
    )

    # Apply YAML overrides (deep merge — flat for now)
    if yaml_overrides:
        cfg = cfg.model_copy(update=yaml_overrides)

    return cfg
