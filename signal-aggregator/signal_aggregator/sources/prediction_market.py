"""Prediction market source — Polymarket, Kalshi, etc."""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any, Dict

import aiohttp

from signal_aggregator.config import SourceConfig
from signal_aggregator.schema import Signal, SignalSource, SignalType
from signal_aggregator.sources.base import BaseSource

logger = logging.getLogger(__name__)

# Polymarket Gamma API (public, no key)
POLYMARKET_API = "https://gamma-api.polymarket.com/events"


class PredictionMarketSource(BaseSource):
    """Scans prediction markets for implied probability shifts."""

    @property
    def source_type(self) -> SignalSource:
        return SignalSource.PREDICTION_MARKET

    async def fetch(self) -> list[Signal]:
        signals: list[Signal] = []
        async with aiohttp.ClientSession() as session:
            try:
                params = {"active": "true", "closed": "false", "limit": "10"}
                async with session.get(
                    POLYMARKET_API,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=self.config.timeout_sec),
                ) as resp:
                    data = await resp.json()
                    events = data if isinstance(data, list) else []
                    for event in events:
                        sig = self._parse_event(event)
                        if sig:
                            signals.append(sig)
            except Exception as exc:
                logger.warning("Polymarket fetch failed: %s", exc)
        return signals

    def _parse_event(self, event: Dict[str, Any]) -> Signal | None:
        try:
            markets = event.get("markets", [])
            if not markets:
                return None
            best = markets[0]
            prob = Decimal(str(best.get("outcomePrices", [0])[0]))
            sig_type = SignalType.ALERT
            direction = "neutral"
            if prob > Decimal("0.7"):
                sig_type = SignalType.BUY
                direction = "long"
            elif prob < Decimal("0.3"):
                sig_type = SignalType.SELL
                direction = "short"
            return self._make_signal(
                raw=event,
                type=sig_type,
                symbol=event.get("ticker"),
                price=prob,
                direction=direction,
                confidence=prob if prob >= Decimal("0.5") else Decimal("1") - prob,
                metadata={
                    "title": event.get("title"),
                    "slug": event.get("slug"),
                    "market_id": best.get("id"),
                    "volume": best.get("volume"),
                },
            )
        except Exception as exc:
            logger.debug("Failed to parse Polymarket event: %s", exc)
            return None
