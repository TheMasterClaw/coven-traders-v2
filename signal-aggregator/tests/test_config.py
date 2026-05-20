"""Tests for configuration loading."""

import os

from signal_aggregator.config import AggregatorConfig, RedisConfig, SourceConfig, _env_bool, _env_float, _env_int


def test_env_bool():
    assert _env_bool("1") is True
    assert _env_bool("true") is True
    assert _env_bool("0") is False
    assert _env_bool(None, default=True) is True


def test_env_int():
    assert _env_int("6379", 0) == 6379
    assert _env_int("bad", 42) == 42
    assert _env_int(None, 7) == 7


def test_env_float():
    assert _env_float("30.5", 0.0) == 30.5
    assert _env_float("x", 1.0) == 1.0


def test_redis_config_defaults():
    cfg = RedisConfig()
    assert cfg.host == "localhost"
    assert cfg.port == 6379
    assert cfg.channel == "coven:signals"


def test_source_config_defaults():
    cfg = SourceConfig()
    assert cfg.enabled is True
    assert cfg.poll_interval_sec == 30.0


def test_aggregator_config_from_env(monkeypatch):
    monkeypatch.setenv("ONCHAIN_ENABLED", "false")
    monkeypatch.setenv("SOCIAL_POLL_INTERVAL_SEC", "60")
    cfg = AggregatorConfig.from_env()
    assert cfg.get("onchain").enabled is False
    assert cfg.get("social").poll_interval_sec == 60.0
    assert cfg.get("news").enabled is True
