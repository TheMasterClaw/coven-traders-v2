"""Social media source — Twitter/X sentiment, crypto influencer mentions."""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any, Dict

import aiohttp

from signal_aggregator.config import SourceConfig
from signal_aggregator.schema import Signal, SignalSource, SignalType
from signal_aggregator.sources.base import BaseSource

logger = logging.getLogger(__name__)

# Placeholder: use a free crypto sentiment aggregator if no API key
ALTERNATIVE_ME_API = "https://api.alternative.me/fng/"


class SocialSource(BaseSource):
    """Aggregates social sentiment signals."""

    @property
    def source_type(self) -> SignalSource:
        return SignalSource.SOCIAL

    async def fetch(self) -> list[Signal]:
        signals: list[Signal] = []
        async with aiohttp.ClientSession() as session:
            # Fear & Greed index as a proxy for social sentiment
            try:
                async with session.get(
                    ALTERNATIVE_ME_API,
                    timeout=aiohttp.ClientTimeout(total=self.config.timeout_sec),
                ) as resp:
                    data = await resp.json()
                    for item in data.get("data", [])[:1]:
                        value = int(item.get("value", 50))
                        sentiment = Decimal(str((value - 50) / 50))  # normalize -1..1
                        sig_type = (
                            SignalType.BUY
                            if value < 25
                            else SignalType.SELL
                            if value > 75
                            else SignalType.SENTIMENT
                        )
                        signals.append(
                            self._make_signal(
                                raw=item,
                                type=sig_type,
                                sentiment_score=sentiment,
                                confidence=Decimal(str(value / 100)),
                                metadata={
                                    "classification": item.get("value_classification"),
                                    "timestamp": item.get("timestamp"),
                                },
                            )
                        )
            except Exception as exc:
                logger.warning("Alternative.me fetch failed: %s", exc)

            # TODO: integrate X API v2 when API key is available
            if self.config.api_key:
                logger.debug("X API key present — integration stub")

        return signals
