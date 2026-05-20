"""Tests for the normalized signal schema."""

from decimal import Decimal

import pytest
from pydantic import ValidationError

from signal_aggregator.schema import Signal, SignalSource, SignalType


def test_signal_minimal():
    sig = Signal(id="test-1", source=SignalSource.ONCHAIN, type=SignalType.BUY)
    assert sig.id == "test-1"
    assert sig.source == SignalSource.ONCHAIN
    assert sig.type == SignalType.BUY
    assert sig.confidence is None


def test_signal_full():
    sig = Signal(
        id="test-2",
        source=SignalSource.TECHNICAL,
        type=SignalType.SELL,
        symbol="BTC",
        quote_symbol="USDT",
        confidence=Decimal("0.85"),
        direction="short",
        price=Decimal("65000.50"),
        volume_24h=Decimal("1_200_000_000"),
        liquidity_usd=Decimal("800_000_000"),
        sentiment_score=Decimal("-0.4"),
        raw_payload={"rsi": 72.5},
        metadata={"interval": "1h"},
        tags=["rsi", "overbought"],
    )
    assert sig.confidence == Decimal("0.85")
    assert sig.sentiment_score == Decimal("-0.4")
    assert sig.price == Decimal("65000.50")


def test_signal_coercion():
    sig = Signal(
        id="test-3",
        source=SignalSource.SOCIAL,
        type=SignalType.SENTIMENT,
        confidence=0.77,
        sentiment_score=-0.2,
        price="42000",
    )
    assert isinstance(sig.confidence, Decimal)
    assert sig.confidence == Decimal("0.77")
    assert sig.price == Decimal("42000")


def test_signal_validation_bounds():
    with pytest.raises(ValidationError):
        Signal(
            id="bad",
            source=SignalSource.NEWS,
            type=SignalType.ALERT,
            confidence=Decimal("1.5"),
        )


def test_to_redis_message():
    sig = Signal(id="r-1", source=SignalSource.ARBITRAGE, type=SignalType.ARBITRAGE)
    msg = sig.to_redis_message()
    assert "r-1" in msg
    assert "arbitrage" in msg
