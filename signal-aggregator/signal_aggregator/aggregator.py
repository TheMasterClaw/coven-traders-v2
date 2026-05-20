"""Async orchestrator that runs all sources and publishes to Redis pub/sub."""

from __future__ import annotations

import asyncio
import json
import logging
from collections import deque
from typing import AsyncIterator, Deque, Dict, List, Optional, Set

import redis.asyncio as aioredis

from signal_aggregator.config import AggregatorConfig, SourceConfig
from signal_aggregator.schema import Signal, SignalSource
from signal_aggregator.sources import (
    ArbitrageSource,
    NewsSource,
    OnChainSource,
    PredictionMarketSource,
    SocialSource,
    TechnicalSource,
)
from signal_aggregator.sources.base import BaseSource

logger = logging.getLogger(__name__)

_SOURCE_MAP: Dict[SignalSource, type[BaseSource]] = {
    SignalSource.ONCHAIN: OnChainSource,
    SignalSource.SOCIAL: SocialSource,
    SignalSource.NEWS: NewsSource,
    SignalSource.TECHNICAL: TechnicalSource,
    SignalSource.PREDICTION_MARKET: PredictionMarketSource,
    SignalSource.ARBITRAGE: ArbitrageSource,
}


class SignalAggregator:
    """
    Orchestrates multiple intel sources, deduplicates signals,
    and publishes normalized messages to Redis pub/sub.
    """

    def __init__(self, config: Optional[AggregatorConfig] = None) -> None:
        self.config = config or AggregatorConfig.from_env()
        self._redis: Optional[aioredis.Redis] = None
        self._sources: List[BaseSource] = []
        self._queue: asyncio.Queue[Signal] = asyncio.Queue(
            maxsize=self.config.max_queue_size
        )
        self._seen: Deque[str] = deque(maxlen=10_000)
        self._tasks: Set[asyncio.Task] = set()
        self._running = False

    async def _connect_redis(self) -> aioredis.Redis:
        if self._redis is None:
            self._redis = aioredis.Redis(
                host=self.config.redis.host,
                port=self.config.redis.port,
                db=self.config.redis.db,
                password=self.config.redis.password,
                ssl=self.config.redis.ssl,
                decode_responses=True,
            )
        return self._redis

    def _build_sources(self) -> List[BaseSource]:
        sources: List[BaseSource] = []
        for src_enum, cls in _SOURCE_MAP.items():
            cfg = self.config.get(src_enum.value)
            if cfg.enabled:
                sources.append(cls(cfg))
                logger.info("Registered source: %s", src_enum.value)
            else:
                logger.info("Skipped disabled source: %s", src_enum.value)
        return sources

    async def _source_loop(self, source: BaseSource) -> None:
        async for signal in source.run():
            try:
                self._queue.put_nowait(signal)
            except asyncio.QueueFull:
                logger.warning("Signal queue full — dropping oldest")
                try:
                    self._queue.get_nowait()
                except asyncio.QueueEmpty:
                    pass
                self._queue.put_nowait(signal)

    async def _publisher_loop(self) -> None:
        redis = await self._connect_redis()
        while self._running:
            signal = await self._queue.get()
            if self._is_duplicate(signal):
                continue
            try:
                await redis.publish(
                    self.config.redis.channel, signal.to_redis_message()
                )
                logger.debug("Published signal %s from %s", signal.id, signal.source.value)
            except Exception as exc:
                logger.exception("Redis publish failed: %s", exc)

    def _is_duplicate(self, signal: Signal) -> bool:
        # Simple dedup by raw payload hash within a time window
        key = f"{signal.source.value}:{json.dumps(signal.raw_payload, sort_keys=True, default=str)}"
        if key in self._seen:
            return True
        self._seen.append(key)
        return False

    async def start(self) -> None:
        self._running = True
        self._sources = self._build_sources()
        # Start source consumers
        for src in self._sources:
            task = asyncio.create_task(self._source_loop(src))
            self._tasks.add(task)
            task.add_done_callback(self._tasks.discard)
        # Start publisher
        pub_task = asyncio.create_task(self._publisher_loop())
        self._tasks.add(pub_task)
        pub_task.add_done_callback(self._tasks.discard)
        logger.info("SignalAggregator started with %d sources", len(self._sources))

    async def stop(self) -> None:
        self._running = False
        for src in self._sources:
            src.stop()
        for task in self._tasks:
            task.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)
        if self._redis:
            await self._redis.close()
        logger.info("SignalAggregator stopped")

    async def run_once(self) -> List[Signal]:
        """Single-shot fetch from all sources (useful for testing)."""
        self._sources = self._build_sources()
        results: List[Signal] = []
        coros = [src.fetch() for src in self._sources]
        for sigs in await asyncio.gather(*coros, return_exceptions=True):
            if isinstance(sigs, Exception):
                logger.warning("Source error: %s", sigs)
                continue
            results.extend(sigs)
        return results

    async def publish(self, signal: Signal) -> None:
        """Publish a single signal immediately."""
        redis = await self._connect_redis()
        await redis.publish(self.config.redis.channel, signal.to_redis_message())

    def iter_signals(self) -> AsyncIterator[Signal]:
        """Iterate over the internal queue (for local consumers)."""
        # Helper generator to drain queue
        async def _gen():
            while True:
                yield await self._queue.get()
        return _gen()
