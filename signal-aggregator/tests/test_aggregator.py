"""Tests for the async orchestrator."""

import asyncio
from decimal import Decimal

import pytest

from signal_aggregator.aggregator import SignalAggregator
from signal_aggregator.config import AggregatorConfig, RedisConfig, SourceConfig
from signal_aggregator.schema import Signal, SignalSource, SignalType


@pytest.fixture
def mock_config():
    return AggregatorConfig(
        redis=RedisConfig(host="localhost", port=6379, channel="test:coven:signals"),
        sources={
            "onchain": SourceConfig(enabled=False),
            "social": SourceConfig(enabled=False),
            "news": SourceConfig(enabled=False),
            "technical": SourceConfig(enabled=False),
            "prediction_market": SourceConfig(enabled=False),
            "arbitrage": SourceConfig(enabled=False),
        },
    )


@pytest.mark.asyncio
async def test_aggregator_run_once(mock_config):
    agg = SignalAggregator(mock_config)
    signals = await agg.run_once()
    assert signals == []
    await agg.stop()


@pytest.mark.asyncio
async def test_aggregator_dedup(mock_config):
    agg = SignalAggregator(mock_config)
    sig1 = Signal(
        id="d-1",
        source=SignalSource.SOCIAL,
        type=SignalType.SENTIMENT,
        raw_payload={"a": 1},
    )
    sig2 = Signal(
        id="d-2",
        source=SignalSource.SOCIAL,
        type=SignalType.SENTIMENT,
        raw_payload={"a": 1},
    )
    assert not agg._is_duplicate(sig1)
    assert agg._is_duplicate(sig2)
    await agg.stop()


@pytest.mark.asyncio
async def test_aggregator_queue(mock_config):
    agg = SignalAggregator(mock_config)
    sig = Signal(
        id="q-1", source=SignalSource.NEWS, type=SignalType.ALERT, confidence=Decimal("0.9")
    )
    await agg._queue.put(sig)
    fetched = await asyncio.wait_for(agg._queue.get(), timeout=1.0)
    assert fetched.id == "q-1"
    await agg.stop()
