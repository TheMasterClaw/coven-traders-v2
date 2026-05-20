"""Base class for all signal sources."""

from __future__ import annotations

import abc
import asyncio
import logging
from typing import Any

from normalizer import Signal

logger = logging.getLogger(__name__)


class BaseSource(abc.ABC):
    def __init__(self, name: str, config: dict[str, Any]):
        self.name = name
        self.config = config
        self.enabled = config.get("enabled", True)
        self.interval = config.get("interval", 60)
        self._semaphore = asyncio.Semaphore(config.get("max_concurrent", 5))

    @abc.abstractmethod
    async def fetch(self) -> list[Signal]:
        """Fetch raw signals from the source."""
        ...

    async def fetch_with_retry(self, retries: int = 3, backoff: float = 1.0) -> list[Signal]:
        for attempt in range(1, retries + 1):
            try:
                async with self._semaphore:
                    signals = await self.fetch()
                logger.debug("%s fetched %s signals", self.name, len(signals))
                return signals
            except Exception as exc:
                logger.warning("%s fetch attempt %s/%s failed: %s", self.name, attempt, retries, exc)
                if attempt < retries:
                    await asyncio.sleep(backoff * (2 ** (attempt - 1)))
        logger.error("%s fetch failed after %s retries", self.name, retries)
        return []

    async def run_loop(self, callback: callable) -> None:
        if not self.enabled:
            logger.info("%s is disabled, skipping loop", self.name)
            return
        logger.info("Starting %s loop (interval=%ss)", self.name, self.interval)
        while True:
            signals = await self.fetch_with_retry()
            if signals:
                await callback(signals)
            await asyncio.sleep(self.interval)
