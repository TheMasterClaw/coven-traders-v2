"""Abstract base class for all intel sources."""

from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import AsyncIterator, Dict, Any

from signal_aggregator.schema import Signal, SignalSource
from signal_aggregator.config import SourceConfig

logger = logging.getLogger(__name__)


class BaseSource(ABC):
    """Every intel source must implement fetch() and expose source_type."""

    def __init__(self, config: SourceConfig) -> None:
        self.config = config
        self._running = False

    @property
    @abstractmethod
    def source_type(self) -> SignalSource:
        ...

    @abstractmethod
    async def fetch(self) -> list[Signal]:
        """Fetch raw intel and return normalized Signal objects."""
        ...

    async def run(self) -> AsyncIterator[Signal]:
        """Continuous polling loop yielding signals."""
        self._running = True
        while self._running:
            if not self.config.enabled:
                await asyncio.sleep(self.config.poll_interval_sec)
                continue
            try:
                signals = await asyncio.wait_for(
                    self.fetch(), timeout=self.config.timeout_sec
                )
                for sig in signals:
                    yield sig
            except asyncio.TimeoutError:
                logger.warning("%s fetch timed out", self.source_type.value)
            except Exception as exc:
                logger.exception("%s fetch error: %s", self.source_type.value, exc)
            await asyncio.sleep(self.config.poll_interval_sec)

    def stop(self) -> None:
        self._running = False

    def _make_signal(self, raw: Dict[str, Any], **overrides) -> Signal:
        """Helper to build a Signal with auto-generated id."""
        from uuid import uuid4
        return Signal.from_raw(
            source=self.source_type,
            raw=raw,
            id=str(uuid4()),
            **overrides,
        )
