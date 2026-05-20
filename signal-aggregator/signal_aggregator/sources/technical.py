"""Technical analysis source — RSI, MACD, moving averages via free APIs."""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any, Dict

import aiohttp

from signal_aggregator.config import SourceConfig
from signal_aggregator.schema import Signal, SignalSource, SignalType
from signal_aggregator.sources.base import BaseSource

logger = logging.getLogger(__name__)

# Free Binance API for OHLCV / klines
BINANCE_KLINES = "https://api.binance.com/api/v3/klines"


class TechnicalSource(BaseSource):
    """Computes TA signals from exchange OHLCV data."""

    @property
    def source_type(self) -> SignalSource:
        return SignalSource.TECHNICAL

    async def fetch(self) -> list[Signal]:
        signals: list[Signal] = []
        async with aiohttp.ClientSession() as session:
            for symbol in ("BTCUSDT", "ETHUSDT", "SOLUSDT"):
                try:
                    sig = await self._analyze_symbol(session, symbol)
                    if sig:
                        signals.append(sig)
                except Exception as exc:
                    logger.warning("TA analysis failed for %s: %s", symbol, exc)
        return signals

    async def _analyze_symbol(
        self, session: aiohttp.ClientSession, symbol: str
    ) -> Signal | None:
        params = {"symbol": symbol, "interval": "1h", "limit": "50"}
        async with session.get(
            BINANCE_KLINES,
            params=params,
            timeout=aiohttp.ClientTimeout(total=self.config.timeout_sec),
        ) as resp:
            data = await resp.json()
            if not isinstance(data, list) or len(data) < 50:
                return None
            closes = [Decimal(str(c[4])) for c in data]
            rsi = self._rsi(closes, period=14)
            ema_fast = self._ema(closes, period=12)
            ema_slow = self._ema(closes, period=26)
            price = closes[-1]

            sig_type = SignalType.HOLD
            direction = "neutral"
            confidence = Decimal("0.5")
            if rsi is not None and ema_fast is not None and ema_slow is not None:
                if rsi < 30 and ema_fast > ema_slow:
                    sig_type = SignalType.BUY
                    direction = "long"
                    confidence = Decimal("0.7")
                elif rsi > 70 and ema_fast < ema_slow:
                    sig_type = SignalType.SELL
                    direction = "short"
                    confidence = Decimal("0.7")

            return self._make_signal(
                raw={"closes": [str(c) for c in closes[-5:]]},
                type=sig_type,
                symbol=symbol.replace("USDT", ""),
                quote_symbol="USDT",
                price=price,
                direction=direction,
                confidence=confidence,
                metadata={
                    "rsi": float(rsi) if rsi else None,
                    "ema_fast": float(ema_fast) if ema_fast else None,
                    "ema_slow": float(ema_slow) if ema_slow else None,
                    "interval": "1h",
                },
            )

    @staticmethod
    def _rsi(closes: list[Decimal], period: int = 14) -> Decimal | None:
        if len(closes) < period + 1:
            return None
        gains = []
        losses = []
        for i in range(1, period + 1):
            diff = closes[i] - closes[i - 1]
            gains.append(diff if diff > 0 else Decimal("0"))
            losses.append(-diff if diff < 0 else Decimal("0"))
        avg_gain = sum(gains) / period
        avg_loss = sum(losses) / period
        if avg_loss == 0:
            return Decimal("100")
        rs = avg_gain / avg_loss
        return Decimal("100") - (Decimal("100") / (Decimal("1") + rs))

    @staticmethod
    def _ema(closes: list[Decimal], period: int) -> Decimal | None:
        if len(closes) < period:
            return None
        multiplier = Decimal("2") / (Decimal(str(period)) + Decimal("1"))
        ema = sum(closes[:period]) / period
        for price in closes[period:]:
            ema = (price - ema) * multiplier + ema
        return ema
