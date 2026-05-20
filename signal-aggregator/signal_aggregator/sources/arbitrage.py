"""Cross-market arbitrage scanner — price diffs across CEX/DEX."""

from __future__ import annotations

import asyncio
import logging
from decimal import Decimal
from typing import Any, Dict

import aiohttp

from signal_aggregator.config import SourceConfig
from signal_aggregator.schema import Signal, SignalSource, SignalType
from signal_aggregator.sources.base import BaseSource

logger = logging.getLogger(__name__)

BINANCE_TICKER = "https://api.binance.com/api/v3/ticker/price"
COINBASE_TICKER = "https://api.coinbase.com/v2/exchange-rates"
DEXSCREENER_SEARCH = "https://api.dexscreener.com/latest/dex/search"


class ArbitrageSource(BaseSource):
    """Detects cross-market price discrepancies."""

    @property
    def source_type(self) -> SignalSource:
        return SignalSource.ARBITRAGE

    async def fetch(self) -> list[Signal]:
        signals: list[Signal] = []
        async with aiohttp.ClientSession() as session:
            prices: Dict[str, Dict[str, Decimal]] = {}
            tasks = [
                self._fetch_binance(session, prices),
                self._fetch_coinbase(session, prices),
                self._fetch_dex(session, prices),
            ]
            await asyncio.gather(*tasks, return_exceptions=True)
            signals = self._detect_arbitrage(prices)
        return signals

    async def _fetch_binance(
        self, session: aiohttp.ClientSession, prices: Dict[str, Dict[str, Decimal]]
    ) -> None:
        try:
            async with session.get(
                BINANCE_TICKER,
                timeout=aiohttp.ClientTimeout(total=self.config.timeout_sec),
            ) as resp:
                data = await resp.json()
                for item in data:
                    sym = item.get("symbol", "")
                    if sym.endswith("USDT"):
                        asset = sym.replace("USDT", "")
                        prices.setdefault(asset, {})["binance"] = Decimal(
                            str(item.get("price", 0))
                        )
        except Exception as exc:
            logger.warning("Binance fetch failed: %s", exc)

    async def _fetch_coinbase(
        self, session: aiohttp.ClientSession, prices: Dict[str, Dict[str, Decimal]]
    ) -> None:
        try:
            async with session.get(
                f"{COINBASE_TICKER}?currency=USDT",
                timeout=aiohttp.ClientTimeout(total=self.config.timeout_sec),
            ) as resp:
                data = await resp.json()
                rates = data.get("data", {}).get("rates", {})
                for asset, rate in rates.items():
                    if asset in ("BTC", "ETH", "SOL", "USDC"):
                        prices.setdefault(asset, {})["coinbase"] = Decimal(
                            str(rate)
                        )
        except Exception as exc:
            logger.warning("Coinbase fetch failed: %s", exc)

    async def _fetch_dex(
        self, session: aiohttp.ClientSession, prices: Dict[str, Dict[str, Decimal]]
    ) -> None:
        try:
            async with session.get(
                f"{DEXSCREENER_SEARCH}?q=USDC",
                timeout=aiohttp.ClientTimeout(total=self.config.timeout_sec),
            ) as resp:
                data = await resp.json()
                for pair in data.get("pairs", [])[:10]:
                    asset = pair.get("baseToken", {}).get("symbol", "")
                    if asset in ("BTC", "ETH", "SOL", "WBTC", "WETH"):
                        prices.setdefault(asset, {})["dex"] = Decimal(
                            str(pair.get("priceUsd", 0))
                        )
        except Exception as exc:
            logger.warning("DEX fetch failed: %s", exc)

    def _detect_arbitrage(
        self, prices: Dict[str, Dict[str, Decimal]]
    ) -> list[Signal]:
        signals: list[Signal] = []
        threshold = Decimal("0.005")  # 0.5 %
        for asset, venues in prices.items():
            if len(venues) < 2:
                continue
            best_bid = max(venues.values())
            best_ask = min(venues.values())
            if best_bid == 0:
                continue
            spread = (best_bid - best_ask) / best_bid
            if spread > threshold:
                buy_venue = min(venues, key=venues.get)  # type: ignore[arg-type]
                sell_venue = max(venues, key=venues.get)  # type: ignore[arg-type]
                signals.append(
                    self._make_signal(
                        raw=prices,
                        type=SignalType.ARBITRAGE,
                        symbol=asset,
                        price=best_ask,
                        confidence=min(spread * Decimal("10"), Decimal("1")),
                        metadata={
                            "spread_pct": float(spread * Decimal("100")),
                            "buy_venue": buy_venue,
                            "sell_venue": sell_venue,
                            "buy_price": float(venues[buy_venue]),
                            "sell_price": float(venues[sell_venue]),
                        },
                    )
                )
        return signals
