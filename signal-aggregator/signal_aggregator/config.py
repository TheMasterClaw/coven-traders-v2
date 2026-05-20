"""Configuration loader for source settings and Redis."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

from dotenv import load_dotenv


def _env_bool(val: str | None, default: bool = False) -> bool:
    if val is None:
        return default
    return val.lower() in ("1", "true", "yes", "on")


def _env_int(val: str | None, default: int) -> int:
    if val is None:
        return default
    try:
        return int(val)
    except ValueError:
        return default


def _env_float(val: str | None, default: float) -> float:
    if val is None:
        return default
    try:
        return float(val)
    except ValueError:
        return default


@dataclass(frozen=True)
class RedisConfig:
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: str | None = None
    channel: str = "coven:signals"
    ssl: bool = False

    @classmethod
    def from_env(cls) -> "RedisConfig":
        load_dotenv(Path.home() / ".openclaw" / "credentials" / "api_keys.env")
        return cls(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=_env_int(os.getenv("REDIS_PORT"), 6379),
            db=_env_int(os.getenv("REDIS_DB"), 0),
            password=os.getenv("REDIS_PASSWORD") or None,
            channel=os.getenv("REDIS_CHANNEL", "coven:signals"),
            ssl=_env_bool(os.getenv("REDIS_SSL"), False),
        )


@dataclass(frozen=True)
class SourceConfig:
    enabled: bool = True
    poll_interval_sec: float = 30.0
    timeout_sec: float = 10.0
    api_key: str | None = None
    api_secret: str | None = None
    endpoint: str | None = None
    extra: Dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class AggregatorConfig:
    redis: RedisConfig = field(default_factory=RedisConfig.from_env)
    sources: Dict[str, SourceConfig] = field(default_factory=dict)
    max_queue_size: int = 10_000
    dedup_window_sec: float = 300.0

    @classmethod
    def from_env(cls) -> "AggregatorConfig":
        load_dotenv(Path.home() / ".openclaw" / "credentials" / "api_keys.env")
        sources: Dict[str, SourceConfig] = {}
        for name in (
            "onchain",
            "social",
            "news",
            "technical",
            "prediction_market",
            "arbitrage",
        ):
            prefix = name.upper()
            sources[name] = SourceConfig(
                enabled=_env_bool(os.getenv(f"{prefix}_ENABLED"), True),
                poll_interval_sec=_env_float(
                    os.getenv(f"{prefix}_POLL_INTERVAL_SEC"), 30.0
                ),
                timeout_sec=_env_float(os.getenv(f"{prefix}_TIMEOUT_SEC"), 10.0),
                api_key=os.getenv(f"{prefix}_API_KEY"),
                api_secret=os.getenv(f"{prefix}_API_SECRET"),
                endpoint=os.getenv(f"{prefix}_ENDPOINT"),
            )
        return cls(
            redis=RedisConfig.from_env(),
            sources=sources,
            max_queue_size=_env_int(os.getenv("AGG_MAX_QUEUE"), 10_000),
            dedup_window_sec=_env_float(os.getenv("AGG_DEDUP_WINDOW_SEC"), 300.0),
        )

    def get(self, name: str) -> SourceConfig:
        return self.sources.get(name, SourceConfig())
