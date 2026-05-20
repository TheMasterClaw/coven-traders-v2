"""News signal source: RSS feeds, macro calendar, earnings."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

import aiohttp
import feedparser

from normalizer import Signal, normalize_raw
from sources.base import BaseSource

logger = logging.getLogger(__name__)

# Keyword-based sentiment mapping for hackathon
BULLISH_KEYWORDS = {"rally", "surge", "adoption", "partnership", "launch", "bull", "upgrade", "etf", "approval"}
BEARISH_KEYWORDS = {"crash", "hack", "sec", "lawsuit", "ban", "bear", "dump", "liquidation", "fud"}


class NewsSource(BaseSource):
    def __init__(self, config: dict[str, Any]):
        super().__init__("news", config)
        self.rss_feeds = config.get("rss_feeds", [])
        self.macro_url = config.get("macro_calendar_url", "")
        self.earnings_api = config.get("earnings_api", "")
        self._session: aiohttp.ClientSession | None = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15))
        return self._session

    async def fetch(self) -> list[Signal]:
        tasks = [
            self._rss_news(),
            self._macro_calendar(),
            self._earnings(),
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        signals: list[Signal] = []
        for res in results:
            if isinstance(res, Exception):
                logger.warning("News sub-task failed: %s", res)
                continue
            signals.extend(res)
        return signals

    async def _rss_news(self) -> list[Signal]:
        session = await self._get_session()
        signals = []
        for url in self.rss_feeds:
            try:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        text = await resp.text()
                        feed = feedparser.parse(text)
                        for entry in feed.entries[:5]:
                            title = entry.get("title", "").lower()
                            summary = entry.get("summary", "").lower()
                            combined = f"{title} {summary}"
                            bull_count = sum(1 for w in BULLISH_KEYWORDS if w in combined)
                            bear_count = sum(1 for w in BEARISH_KEYWORDS if w in combined)
                            if bull_count > bear_count and bull_count > 0:
                                direction = "bull"
                                confidence = min(0.5 + bull_count * 0.1, 0.9)
                            elif bear_count > bull_count and bear_count > 0:
                                direction = "bear"
                                confidence = min(0.5 + bear_count * 0.1, 0.9)
                            else:
                                continue
                            signals.append(
                                normalize_raw(
                                    source="news.rss",
                                    asset=self._extract_asset(combined),
                                    raw_direction=direction,
                                    confidence=confidence,
                                    metadata={
                                        "title": entry.get("title", ""),
                                        "link": entry.get("link", ""),
                                        "published": entry.get("published", ""),
                                    },
                                    expiry_seconds=7200,
                                )
                            )
            except Exception as exc:
                logger.warning("RSS fetch failed for %s: %s", url, exc)
        return signals

    async def _macro_calendar(self) -> list[Signal]:
        signals = []
        # Simulated macro events for hackathon
        events = [
            {"event": "FOMC Rate Decision", "impact": "high", "asset": "BTC", "direction": "bear"},
            {"event": "CPI Release", "impact": "high", "asset": "ETH", "direction": "bull"},
        ]
        for ev in events:
            confidence = 0.8 if ev["impact"] == "high" else 0.6
            signals.append(
                normalize_raw(
                    source="news.macro",
                    asset=ev["asset"],
                    raw_direction=ev["direction"],
                    confidence=confidence,
                    metadata={
                        "event": ev["event"],
                        "impact": ev["impact"],
                    },
                    expiry_seconds=14400,
                )
            )
        return signals

    async def _earnings(self) -> list[Signal]:
        signals = []
        # Simulated earnings impact on crypto-correlated equities (MSTR, COIN, etc.)
        earnings = [
            {"ticker": "MSTR", "beat": True, "asset": "BTC"},
            {"ticker": "COIN", "beat": False, "asset": "ETH"},
        ]
        for er in earnings:
            direction = "bull" if er["beat"] else "bear"
            signals.append(
                normalize_raw(
                    source="news.earnings",
                    asset=er["asset"],
                    raw_direction=direction,
                    confidence=0.7,
                    metadata={
                        "ticker": er["ticker"],
                        "beat": er["beat"],
                    },
                    expiry_seconds=7200,
                )
            )
        return signals

    @staticmethod
    def _extract_asset(text: str) -> str:
        text = text.upper()
        if "BTC" in text or "BITCOIN" in text:
            return "BTC"
        if "ETH" in text or "ETHEREUM" in text:
            return "ETH"
        if "SOL" in text or "SOLANA" in text:
            return "SOL"
        if "ARB" in text:
            return "ARB"
        return "ETH"  # default

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()
