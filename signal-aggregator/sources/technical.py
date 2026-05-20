"""Technical analysis signal source: RSI, MACD, Bollinger, orderbook depth."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp
import pandas as pd

from normalizer import Signal, normalize_raw
from sources.base import BaseSource

logger = logging.getLogger(__name__)

COINBASE_API = "https://api.exchange.coinbase.com"


class TechnicalSource(BaseSource):
    def __init__(self, config: dict[str, Any]):
        super().__init__("technical", config)
        self.exchanges = config.get("exchanges", ["coinbase"])
        self.rsi_overbought = config.get("rsi_overbought", 70)
        self.rsi_oversold = config.get("rsi_oversold", 30)
        self.macd_fast = config.get("macd_fast", 12)
        self.macd_slow = config.get("macd_slow", 26)
        self.macd_signal = config.get("macd_signal", 9)
        self.bb_period = config.get("bollinger_period", 20)
        self.bb_std = config.get("bollinger_std", 2)
        self.ob_depth_threshold = config.get("orderbook_depth_threshold", 0.1)
        self._session: aiohttp.ClientSession | None = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15))
        return self._session

    async def fetch(self) -> list[Signal]:
        tasks = [
            self._rsi_signals(),
            self._macd_signals(),
            self._bollinger_signals(),
            self._orderbook_depth(),
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        signals: list[Signal] = []
        for res in results:
            if isinstance(res, Exception):
                logger.warning("Technical sub-task failed: %s", res)
                continue
            signals.extend(res)
        return signals

    async def _fetch_candles(self, product: str, granularity: int = 3600, limit: int = 100) -> pd.DataFrame:
        session = await self._get_session()
        url = f"{COINBASE_API}/products/{product}/candles?granularity={granularity}"
        async with session.get(url) as resp:
            if resp.status != 200:
                raise RuntimeError(f"Candles fetch failed: {resp.status}")
            data = await resp.json()
        # Coinbase candles: [time, low, high, open, close, volume]
        df = pd.DataFrame(data, columns=["time", "low", "high", "open", "close", "volume"])
        df = df.sort_values("time").reset_index(drop=True)
        df["close"] = df["close"].astype(float)
        return df

    async def _rsi_signals(self) -> list[Signal]:
        signals = []
        for product in ["ETH-USD", "BTC-USD"]:
            try:
                df = await self._fetch_candles(product)
                rsi = self._calculate_rsi(df["close"])
                if rsi.empty:
                    continue
                last_rsi = rsi.iloc[-1]
                asset = product.split("-")[0]
                if last_rsi >= self.rsi_overbought:
                    signals.append(
                        normalize_raw(
                            source="technical.rsi",
                            asset=asset,
                            raw_direction="bear",
                            confidence=min((last_rsi - self.rsi_overbought) / 30 + 0.5, 0.95),
                            metadata={"rsi": round(last_rsi, 2), "threshold": self.rsi_overbought},
                            expiry_seconds=1800,
                        )
                    )
                elif last_rsi <= self.rsi_oversold:
                    signals.append(
                        normalize_raw(
                            source="technical.rsi",
                            asset=asset,
                            raw_direction="bull",
                            confidence=min((self.rsi_oversold - last_rsi) / 30 + 0.5, 0.95),
                            metadata={"rsi": round(last_rsi, 2), "threshold": self.rsi_oversold},
                            expiry_seconds=1800,
                        )
                    )
            except Exception as exc:
                logger.warning("RSI calc failed for %s: %s", product, exc)
        return signals

    @staticmethod
    def _calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
        delta = prices.diff()
        gain = delta.where(delta > 0, 0.0)
        loss = (-delta).where(delta < 0, 0.0)
        avg_gain = gain.ewm(alpha=1 / period, min_periods=period).mean()
        avg_loss = loss.ewm(alpha=1 / period, min_periods=period).mean()
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    async def _macd_signals(self) -> list[Signal]:
        signals = []
        for product in ["ETH-USD", "BTC-USD"]:
            try:
                df = await self._fetch_candles(product)
                macd_line, signal_line, histogram = self._calculate_macd(df["close"])
                if len(macd_line) < 2:
                    continue
                asset = product.split("-")[0]
                prev_hist = histogram.iloc[-2]
                curr_hist = histogram.iloc[-1]
                if prev_hist < 0 < curr_hist:
                    signals.append(
                        normalize_raw(
                            source="technical.macd",
                            asset=asset,
                            raw_direction="bull",
                            confidence=0.75,
                            metadata={
                                "macd": round(macd_line.iloc[-1], 4),
                                "signal": round(signal_line.iloc[-1], 4),
                                "histogram": round(curr_hist, 4),
                            },
                            expiry_seconds=1800,
                        )
                    )
                elif prev_hist > 0 > curr_hist:
                    signals.append(
                        normalize_raw(
                            source="technical.macd",
                            asset=asset,
                            raw_direction="bear",
                            confidence=0.75,
                            metadata={
                                "macd": round(macd_line.iloc[-1], 4),
                                "signal": round(signal_line.iloc[-1], 4),
                                "histogram": round(curr_hist, 4),
                            },
                            expiry_seconds=1800,
                        )
                    )
            except Exception as exc:
                logger.warning("MACD calc failed for %s: %s", product, exc)
        return signals

    def _calculate_macd(self, prices: pd.Series) -> tuple[pd.Series, pd.Series, pd.Series]:
        ema_fast = prices.ewm(span=self.macd_fast, adjust=False).mean()
        ema_slow = prices.ewm(span=self.macd_slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=self.macd_signal, adjust=False).mean()
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram

    async def _bollinger_signals(self) -> list[Signal]:
        signals = []
        for product in ["ETH-USD", "BTC-USD"]:
            try:
                df = await self._fetch_candles(product)
                upper, lower, mid = self._calculate_bollinger(df["close"])
                if len(upper) < 1:
                    continue
                asset = product.split("-")[0]
                last_close = df["close"].iloc[-1]
                last_upper = upper.iloc[-1]
                last_lower = lower.iloc[-1]
                if last_close > last_upper:
                    signals.append(
                        normalize_raw(
                            source="technical.bollinger",
                            asset=asset,
                            raw_direction="bear",
                            confidence=min((last_close - last_upper) / last_upper * 10 + 0.5, 0.9),
                            metadata={
                                "upper": round(last_upper, 2),
                                "lower": round(last_lower, 2),
                                "close": round(last_close, 2),
                            },
                            expiry_seconds=1800,
                        )
                    )
                elif last_close < last_lower:
                    signals.append(
                        normalize_raw(
                            source="technical.bollinger",
                            asset=asset,
                            raw_direction="bull",
                            confidence=min((last_lower - last_close) / last_lower * 10 + 0.5, 0.9),
                            metadata={
                                "upper": round(last_upper, 2),
                                "lower": round(last_lower, 2),
                                "close": round(last_close, 2),
                            },
                            expiry_seconds=1800,
                        )
                    )
            except Exception as exc:
                logger.warning("Bollinger calc failed for %s: %s", product, exc)
        return signals

    def _calculate_bollinger(self, prices: pd.Series) -> tuple[pd.Series, pd.Series, pd.Series]:
        mid = prices.rolling(window=self.bb_period).mean()
        std = prices.rolling(window=self.bb_period).std()
        upper = mid + (std * self.bb_std)
        lower = mid - (std * self.bb_std)
        return upper, lower, mid

    async def _orderbook_depth(self) -> list[Signal]:
        session = await self._get_session()
        signals = []
        for product in ["ETH-USD", "BTC-USD"]:
            try:
                async with session.get(f"{COINBASE_API}/products/{product}/book?level=2") as resp:
                    if resp.status != 200:
                        continue
                    data = await resp.json()
                    bids = data.get("bids", [])
                    asks = data.get("asks", [])
                    if not bids or not asks:
                        continue
                    bid_depth = sum(float(b[1]) for b in bids[:10])
                    ask_depth = sum(float(a[1]) for a in asks[:10])
                    imbalance = (bid_depth - ask_depth) / (bid_depth + ask_depth) if (bid_depth + ask_depth) else 0
                    asset = product.split("-")[0]
                    if abs(imbalance) >= self.ob_depth_threshold:
                        direction = "bull" if imbalance > 0 else "bear"
                        signals.append(
                            normalize_raw(
                                source="technical.orderbook",
                                asset=asset,
                                raw_direction=direction,
                                confidence=min(abs(imbalance) + 0.5, 0.9),
                                metadata={
                                    "bid_depth": round(bid_depth, 4),
                                    "ask_depth": round(ask_depth, 4),
                                    "imbalance": round(imbalance, 4),
                                },
                                expiry_seconds=600,
                            )
                        )
            except Exception as exc:
                logger.warning("Orderbook fetch failed for %s: %s", product, exc)
        return signals

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()
