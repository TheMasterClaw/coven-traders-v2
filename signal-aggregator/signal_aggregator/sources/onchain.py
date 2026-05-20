"""On-chain data source — whale moves, liquidity shifts, DEX volume."""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any, Dict, List

import aiohttp

from signal_aggregator.config import SourceConfig
from signal_aggregator.schema import Signal, SignalSource, SignalType
from signal_aggregator.sources.base import BaseSource

logger = logging.getLogger(__name__)

# Public free endpoints (no API key required for basic usage)
DEXSCREENER_API = "https://api.dexscreener.com/latest/dex/search"
ETHERSCAN_API = "https://api.etherscan.io/api"


class OnChainSource(BaseSource):
    """Scans on-chain metrics and large transfers."""

    @property
    def source_type(self) -> SignalSource:
        return SignalSource.ONCHAIN

    async def fetch(self) -> list[Signal]:
        signals: list[Signal] = []
        async with aiohttp.ClientSession() as session:
            # Example: fetch trending pairs from DexScreener
            try:
                async with session.get(
                    f"{DEXSCREENER_API}?q=USDC",
                    timeout=aiohttp.ClientTimeout(total=self.config.timeout_sec),
                ) as resp:
                    data = await resp.json()
                    pairs = data.get("pairs", [])[:5]
                    for pair in pairs:
                        sig = self._parse_pair(pair)
                        if sig:
                            signals.append(sig)
            except Exception as exc:
                logger.warning("DexScreener fetch failed: %s", exc)

            # Placeholder: Etherscan large tx scan (requires API key for production)
            if self.config.api_key:
                try:
                    etherscan_signals = await self._fetch_etherscan(session)
                    signals.extend(etherscan_signals)
                except Exception as exc:
                    logger.warning("Etherscan fetch failed: %s", exc)

        return signals

    def _parse_pair(self, pair: Dict[str, Any]) -> Signal | None:
        try:
            price = Decimal(str(pair.get("priceUsd", 0)))
            volume = Decimal(str(pair.get("volume", {}).get("h24", 0)))
            liquidity = Decimal(str(pair.get("liquidity", {}).get("usd", 0)))
            return self._make_signal(
                raw=pair,
                type=SignalType.LIQUIDITY_SHIFT,
                symbol=pair.get("baseToken", {}).get("symbol"),
                quote_symbol=pair.get("quoteToken", {}).get("symbol"),
                price=price,
                volume_24h=volume,
                liquidity_usd=liquidity,
                confidence=Decimal("0.6"),
                metadata={
                    "dexId": pair.get("dexId"),
                    "pairAddress": pair.get("pairAddress"),
                    "chainId": pair.get("chainId"),
                },
            )
        except Exception as exc:
            logger.debug("Failed to parse pair: %s", exc)
            return None

    async def _fetch_etherscan(self, session: aiohttp.ClientSession) -> list[Signal]:
        """Fetch last 10 large ETH transfers as whale-move signals."""
        params = {
            "module": "account",
            "action": "txlist",
            "address": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",  # USDC contract
            "startblock": "latest",
            "endblock": "latest",
            "sort": "desc",
            "apikey": self.config.api_key,
        }
        async with session.get(ETHERSCAN_API, params=params) as resp:
            data = await resp.json()
            txs = data.get("result", [])[:10]
            signals: list[Signal] = []
            for tx in txs:
                value_eth = Decimal(tx.get("value", "0")) / Decimal("1e18")
                if value_eth > Decimal("100"):
                    signals.append(
                        self._make_signal(
                            raw=tx,
                            type=SignalType.WHALE_MOVE,
                            symbol="ETH",
                            price=value_eth,
                            confidence=Decimal("0.75"),
                            metadata={
                                "from": tx.get("from"),
                                "to": tx.get("to"),
                                "blockNumber": tx.get("blockNumber"),
                                "hash": tx.get("hash"),
                            },
                        )
                    )
            return signals
