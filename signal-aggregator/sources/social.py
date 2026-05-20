"""Social signal source: X/Twitter, Discord, Telegram sentiment."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp

from normalizer import Signal, normalize_raw
from sources.base import BaseSource

logger = logging.getLogger(__name__)


class SocialSource(BaseSource):
    def __init__(self, config: dict[str, Any]):
        super().__init__("social", config)
        self.twitter_bearer = config.get("twitter_bearer_token", "")
        self.discord_webhooks = config.get("discord_webhooks", [])
        self.telegram_tokens = config.get("telegram_bot_tokens", [])
        self.sentiment_threshold = config.get("sentiment_threshold", 0.6)
        self._session: aiohttp.ClientSession | None = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15))
        return self._session

    async def fetch(self) -> list[Signal]:
        tasks = [
            self._twitter_sentiment(),
            self._discord_alpha(),
            self._telegram_feeds(),
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        signals: list[Signal] = []
        for res in results:
            if isinstance(res, Exception):
                logger.warning("Social sub-task failed: %s", res)
                continue
            signals.extend(res)
        return signals

    async def _twitter_sentiment(self) -> list[Signal]:
        """Fetch Twitter/X sentiment for crypto keywords."""
        session = await self._get_session()
        signals = []
        if not self.twitter_bearer:
            # Simulated data for hackathon
            simulated = [
                {"asset": "ETH", "sentiment": 0.75, "volume": 1200},
                {"asset": "BTC", "sentiment": -0.4, "volume": 800},
            ]
            for item in simulated:
                if abs(item["sentiment"]) >= self.sentiment_threshold:
                    signals.append(
                        normalize_raw(
                            source="social.twitter",
                            asset=item["asset"],
                            raw_direction=item["sentiment"],
                            confidence=min(abs(item["sentiment"]), 0.95),
                            metadata={
                                "tweet_volume": item["volume"],
                                "sentiment_score": item["sentiment"],
                            },
                            expiry_seconds=1800,
                        )
                    )
            return signals

        headers = {"Authorization": f"Bearer {self.twitter_bearer}"}
        try:
            async with session.get(
                "https://api.twitter.com/2/tweets/search/recent?query=ETH&max_results=10",
                headers=headers,
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    # Simplified sentiment logic
                    tweets = data.get("data", [])
                    sentiment = len(tweets) / 100.0  # placeholder
                    signals.append(
                        normalize_raw(
                            source="social.twitter",
                            asset="ETH",
                            raw_direction=sentiment,
                            confidence=0.5,
                            metadata={"tweet_count": len(tweets)},
                            expiry_seconds=1800,
                        )
                    )
        except Exception as exc:
            logger.warning("Twitter fetch failed: %s", exc)
        return signals

    async def _discord_alpha(self) -> list[Signal]:
        """Scrape Discord alpha channels via webhooks or bot integration."""
        signals = []
        # Simulated alpha signals
        alpha_signals = [
            {"asset": "SOL", "direction": "bull", "confidence": 0.72, "channel": "alpha-1"},
        ]
        for alpha in alpha_signals:
            signals.append(
                normalize_raw(
                    source="social.discord",
                    asset=alpha["asset"],
                    raw_direction=alpha["direction"],
                    confidence=alpha["confidence"],
                    metadata={"channel": alpha["channel"]},
                    expiry_seconds=3600,
                )
            )
        return signals

    async def _telegram_feeds(self) -> list[Signal]:
        """Fetch signals from Telegram bot channels."""
        signals = []
        # Simulated Telegram feed
        if self.telegram_tokens:
            for token in self.telegram_tokens:
                pass  # Production: use python-telegram-bot
        signals.append(
            normalize_raw(
                source="social.telegram",
                asset="ARB",
                raw_direction="bull",
                confidence=0.65,
                metadata={"channel": "arbitrum-alpha"},
                expiry_seconds=2400,
            )
        )
        return signals

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()
