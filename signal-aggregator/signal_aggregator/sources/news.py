"""News feed source — crypto headlines, macro events."""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any, Dict

import aiohttp

from signal_aggregator.config import SourceConfig
from signal_aggregator.schema import Signal, SignalSource, SignalType
from signal_aggregator.sources.base import BaseSource

logger = logging.getLogger(__name__)

# Free crypto news API (no key required for basic usage)
CRYPTOCOMPARE_NEWS = "https://min-api.cryptocompare.com/data/v2/news/"


class NewsSource(BaseSource):
    """Aggregates news headlines as ALERT signals."""

    @property
    def source_type(self) -> SignalSource:
        return SignalSource.NEWS

    async def fetch(self) -> list[Signal]:
        signals: list[Signal] = []
        async with aiohttp.ClientSession() as session:
            try:
                params = {"lang": "EN", "categories": "BTC,ETH,USDC,Trading"}
                if self.config.api_key:
                    params["api_key"] = self.config.api_key
                async with session.get(
                    CRYPTOCOMPARE_NEWS,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=self.config.timeout_sec),
                ) as resp:
                    data = await resp.json()
                    for article in data.get("Data", [])[:5]:
                        signals.append(self._parse_article(article))
            except Exception as exc:
                logger.warning("CryptoCompare news fetch failed: %s", exc)
        return signals

    def _parse_article(self, article: Dict[str, Any]) -> Signal:
        sentiment = article.get("sentiment")
        sentiment_score = None
        if sentiment:
            sentiment_score = Decimal(str(sentiment))
        return self._make_signal(
            raw=article,
            type=SignalType.ALERT,
            symbol=article.get("source_info", {}).get("name"),
            sentiment_score=sentiment_score,
            confidence=Decimal("0.5"),
            metadata={
                "title": article.get("title"),
                "url": article.get("url"),
                "published_on": article.get("published_on"),
                "source": article.get("source"),
            },
        )
