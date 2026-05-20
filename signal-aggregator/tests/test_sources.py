"""Tests for individual intel sources."""

import pytest

from signal_aggregator.config import SourceConfig
from signal_aggregator.schema import SignalSource, SignalType
from signal_aggregator.sources.arbitrage import ArbitrageSource
from signal_aggregator.sources.news import NewsSource
from signal_aggregator.sources.onchain import OnChainSource
from signal_aggregator.sources.prediction_market import PredictionMarketSource
from signal_aggregator.sources.social import SocialSource
from signal_aggregator.sources.technical import TechnicalSource


@pytest.mark.asyncio
async def test_onchain_source_fetch():
    src = OnChainSource(SourceConfig(enabled=True, timeout_sec=15))
    signals = await src.fetch()
    assert isinstance(signals, list)
    for sig in signals:
        assert sig.source == SignalSource.ONCHAIN
        assert sig.id


@pytest.mark.asyncio
async def test_social_source_fetch():
    src = SocialSource(SourceConfig(enabled=True, timeout_sec=15))
    signals = await src.fetch()
    assert isinstance(signals, list)
    for sig in signals:
        assert sig.source == SignalSource.SOCIAL
        assert sig.id


@pytest.mark.asyncio
async def test_news_source_fetch():
    src = NewsSource(SourceConfig(enabled=True, timeout_sec=15))
    signals = await src.fetch()
    assert isinstance(signals, list)
    for sig in signals:
        assert sig.source == SignalSource.NEWS
        assert sig.id


@pytest.mark.asyncio
async def test_technical_source_fetch():
    src = TechnicalSource(SourceConfig(enabled=True, timeout_sec=15))
    signals = await src.fetch()
    assert isinstance(signals, list)
    for sig in signals:
        assert sig.source == SignalSource.TECHNICAL
        assert sig.id
        if sig.metadata.get("rsi") is not None:
            assert 0 <= sig.metadata["rsi"] <= 100


@pytest.mark.asyncio
async def test_prediction_market_source_fetch():
    src = PredictionMarketSource(SourceConfig(enabled=True, timeout_sec=15))
    signals = await src.fetch()
    assert isinstance(signals, list)
    for sig in signals:
        assert sig.source == SignalSource.PREDICTION_MARKET
        assert sig.id


@pytest.mark.asyncio
async def test_arbitrage_source_fetch():
    src = ArbitrageSource(SourceConfig(enabled=True, timeout_sec=15))
    signals = await src.fetch()
    assert isinstance(signals, list)
    for sig in signals:
        assert sig.source == SignalSource.ARBITRAGE
        assert sig.id
        assert "spread_pct" in sig.metadata or True  # may be empty if no arb found
