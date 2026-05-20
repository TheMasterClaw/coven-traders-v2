"""Prediction market signal source: Polymarket, Kalshi, Azuro."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp

from normalizer import Signal, normalize_raw
from sources.base import BaseSource

logger = logging.getLogger(__name__)


class PredictionSource(BaseSource):
    def __init__(self, config: dict[str, Any]):
        super().__init__("prediction", config)
        self.polymarket_api = config.get("polymarket_api", "https://gamma-api.polymarket.com")
        self.kalshi_api = config.get("kalshi_api", "https://trading-api.kalshi.com")
        self.azuro_oracle = config.get("azuro_oracle", "")
        self.prob_threshold = config.get("probability_shift_threshold", 0.05)
        self._session: aiohttp.ClientSession | None = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15))
        return self._session

    async def fetch(self) -> list[Signal]:
        tasks = [
            self._polymarket(),
            self._kalshi(),
            self._azuro(),
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        signals: list[Signal] = []
        for res in results:
            if isinstance(res, Exception):
                logger.warning("Prediction sub-task failed: %s", res)
                continue
            signals.extend(res)
        return signals

    async def _polymarket(self) -> list[Signal]:
        session = await self._get_session()
        signals = []
        try:
            async with session.get(f"{self.polymarket_api}/markets?limit=5&active=true") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    markets = data if isinstance(data, list) else data.get("markets", [])
                    for market in markets[:5]:
                        outcome_prices = market.get("outcomePrices", "[]")
                        # Simple parsing
                        prob = 0.5
                        if isinstance(outcome_prices, str):
                            try:
                                import json
                                prices = json.loads(outcome_prices)
                                prob = float(prices[0]) if prices else 0.5
                            except Exception:
                                pass
                        elif isinstance(outcome_prices, list):
                            prob = float(outcome_prices[0]) if outcome_prices else 0.5
                        if abs(prob - 0.5) >= self.prob_threshold:
                            direction = "bull" if prob > 0.5 else "bear"
                            asset = self._extract_asset(market.get("question", ""))
                            signals.append(
                                normalize_raw(
                                    source="prediction.polymarket",
                                    asset=asset,
                                    raw_direction=direction,
                                    confidence=min(abs(prob - 0.5) * 2 + 0.5, 0.95),
                                    metadata={
                                        "market": market.get("question", ""),
                                        "probability": prob,
                                        "volume": market.get("volume", 0),
                                    },
                                    expiry_seconds=7200,
                                )
                            )
        except Exception as exc:
            logger.warning("Polymarket fetch failed: %s", exc)
        return signals

    async def _kalshi(self) -> list[Signal]:
        session = await self._get_session()
        signals = []
        try:
            async with session.get(f"{self.kalshi_api}/trade-api/v2/markets?status=open&limit=5") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    markets = data.get("markets", [])
                    for market in markets[:5]:
                        yes_ask = market.get("yes_ask", 50)
                        prob = yes_ask / 100.0
                        if abs(prob - 0.5) >= self.prob_threshold:
                            direction = "bull" if prob > 0.5 else "bear"
                            asset = self._extract_asset(market.get("title", ""))
                            signals.append(
                                normalize_raw(
                                    source="prediction.kalshi",
                                    asset=asset,
                                    raw_direction=direction,
                                    confidence=min(abs(prob - 0.5) * 2 + 0.5, 0.95),
                                    metadata={
                                        "market": market.get("title", ""),
                                        "probability": prob,
                                        "ticker": market.get("ticker", ""),
                                    },
                                    expiry_seconds=7200,
                                )
                            )
        except Exception as exc:
            logger.warning("Kalshi fetch failed: %s", exc)
        return signals

    async def _azuro(self) -> list[Signal]:
        signals = []
        if not self.azuro_oracle:
            # Simulated Azuro oracle data
            signals.append(
                normalize_raw(
                    source="prediction.azuro",
                    asset="ETH",
                    raw_direction="bull",
                    confidence=0.68,
                    metadata={
                        "sport": "esports",
                        "event": "crypto_trading_competition",
                        "odds_shift": 0.12,
                    },
                    expiry_seconds=3600,
                )
            )
            return signals
        # Production: query Azuro subgraph
        return signals

    @staticmethod
    def _extract_asset(text: str) -> str:
        text = text.upper()
        for asset in ["BTC", "ETH", "SOL", "ARB", "DOGE", "XRP"]:
            if asset in text:
                return asset
        return "ETH"

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()
