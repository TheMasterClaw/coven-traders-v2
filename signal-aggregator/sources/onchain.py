"""On-chain signal source: whale wallets, DEX volume, mempool, funding rates."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp

from normalizer import Signal, normalize_raw
from sources.base import BaseSource

logger = logging.getLogger(__name__)

ETHERSCAN_API = "https://api.etherscan.io/api"
COINBASE_API = "https://api.exchange.coinbase.com"


class OnChainSource(BaseSource):
    def __init__(self, config: dict[str, Any]):
        super().__init__("onchain", config)
        self.whale_threshold = config.get("whale_threshold_usd", 100_000)
        self.volume_spike = config.get("dex_volume_spike_threshold", 3.0)
        self.gas_spike = config.get("mempool_gas_spike_threshold", 2.0)
        self.funding_threshold = config.get("funding_rate_threshold", 0.01)
        self._session: aiohttp.ClientSession | None = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15))
        return self._session

    async def fetch(self) -> list[Signal]:
        tasks = [
            self._whale_wallets(),
            self._dex_volume(),
            self._mempool_gas(),
            self._funding_rates(),
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        signals: list[Signal] = []
        for res in results:
            if isinstance(res, Exception):
                logger.warning("On-chain sub-task failed: %s", res)
                continue
            signals.extend(res)
        return signals

    async def _whale_wallets(self) -> list[Signal]:
        """Simulated whale wallet monitoring via Etherscan-like API."""
        session = await self._get_session()
        signals = []
        # In production: query Etherscan/Alchemy for large transfers
        # Simulated data for hackathon
        simulated_whales = [
            {"asset": "ETH", "value_usd": 250_000, "direction": "sell"},
            {"asset": "WBTC", "value_usd": 500_000, "direction": "buy"},
        ]
        for tx in simulated_whales:
            if tx["value_usd"] >= self.whale_threshold:
                confidence = min(tx["value_usd"] / 1_000_000, 0.95)
                signals.append(
                    normalize_raw(
                        source="onchain.whale",
                        asset=tx["asset"],
                        raw_direction=tx["direction"],
                        confidence=confidence,
                        metadata={
                            "value_usd": tx["value_usd"],
                            "threshold": self.whale_threshold,
                        },
                        expiry_seconds=1800,
                    )
                )
        return signals

    async def _dex_volume(self) -> list[Signal]:
        """Detect DEX volume spikes via Coinbase proxy or DEX APIs."""
        session = await self._get_session()
        signals = []
        try:
            async with session.get(f"{COINBASE_API}/products/ETH-USD/stats") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    volume = float(data.get("volume", 0))
                    # Simulated baseline comparison
                    baseline = volume / 2.5
                    spike_ratio = volume / baseline if baseline else 1.0
                    if spike_ratio >= self.volume_spike:
                        direction = "bull" if spike_ratio > self.volume_spike * 1.5 else "neutral"
                        signals.append(
                            normalize_raw(
                                source="onchain.dex_volume",
                                asset="ETH",
                                raw_direction=direction,
                                confidence=min(spike_ratio / 10, 0.9),
                                metadata={
                                    "volume": volume,
                                    "spike_ratio": spike_ratio,
                                },
                                expiry_seconds=900,
                            )
                        )
        except Exception as exc:
            logger.warning("DEX volume fetch failed: %s", exc)
        return signals

    async def _mempool_gas(self) -> list[Signal]:
        """Monitor mempool gas price spikes."""
        session = await self._get_session()
        signals = []
        try:
            async with session.get("https://api.etherscan.io/api?module=gastracker&action=gasoracle") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    result = data.get("result", {})
                    safe_gas = float(result.get("SafeGasPrice", 0))
                    # Simulated baseline
                    baseline = safe_gas / 1.5
                    spike = safe_gas / baseline if baseline else 1.0
                    if spike >= self.gas_spike:
                        # High gas often = high demand = bullish short term
                        signals.append(
                            normalize_raw(
                                source="onchain.mempool",
                                asset="ETH",
                                raw_direction="bull",
                                confidence=min(spike / 5, 0.85),
                                metadata={
                                    "safe_gas_price": safe_gas,
                                    "spike_ratio": spike,
                                },
                                expiry_seconds=600,
                            )
                        )
        except Exception as exc:
            logger.warning("Mempool gas fetch failed: %s", exc)
        return signals

    async def _funding_rates(self) -> list[Signal]:
        """Fetch perp funding rates from Coinbase or Binance."""
        session = await self._get_session()
        signals = []
        try:
            async with session.get(f"{COINBASE_API}/products/ETH-USD/funding") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    rate = float(data.get("funding_rate", 0))
                    if abs(rate) >= self.funding_threshold:
                        direction = "bear" if rate > 0 else "bull"
                        signals.append(
                            normalize_raw(
                                source="onchain.funding",
                                asset="ETH",
                                raw_direction=direction,
                                confidence=min(abs(rate) * 50, 0.9),
                                metadata={
                                    "funding_rate": rate,
                                    "threshold": self.funding_threshold,
                                },
                                expiry_seconds=3600,
                            )
                        )
        except Exception as exc:
            logger.warning("Funding rate fetch failed: %s", exc)
        return signals

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()
