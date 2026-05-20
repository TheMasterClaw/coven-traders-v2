"""Redis pub/sub publisher for normalized signals."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

import redis.asyncio as redis

from normalizer import Signal

logger = logging.getLogger(__name__)


class RedisPublisher:
    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        channel: str = "coven.signals",
    ):
        self.host = host
        self.port = port
        self.db = db
        self.channel = channel
        self._client: redis.Redis | None = None
        self._lock = asyncio.Lock()

    async def connect(self) -> None:
        async with self._lock:
            if self._client is None:
                self._client = redis.Redis(
                    host=self.host,
                    port=self.port,
                    db=self.db,
                    decode_responses=True,
                )
                await self._client.ping()
                logger.info("Redis connected to %s:%s", self.host, self.port)

    async def disconnect(self) -> None:
        async with self._lock:
            if self._client:
                await self._client.close()
                self._client = None
                logger.info("Redis disconnected")

    async def publish(self, signal: Signal) -> bool:
        if self._client is None:
            await self.connect()
        assert self._client is not None
        payload = json.dumps(signal.to_dict(), default=str)
        try:
            result = await self._client.publish(self.channel, payload)
            logger.debug("Published signal %s to %s (receivers=%s)", signal.signal_id, self.channel, result)
            return result is not None
        except Exception as exc:
            logger.error("Redis publish failed: %s", exc)
            return False

    async def publish_batch(self, signals: list[Signal]) -> int:
        if not signals:
            return 0
        if self._client is None:
            await self.connect()
        assert self._client is not None
        pipe = self._client.pipeline()
        for signal in signals:
            payload = json.dumps(signal.to_dict(), default=str)
            pipe.publish(self.channel, payload)
        try:
            results = await pipe.execute()
            published = sum(1 for r in results if r is not None)
            logger.info("Published batch of %s/%s signals", published, len(signals))
            return published
        except Exception as exc:
            logger.error("Redis batch publish failed: %s", exc)
            return 0

    async def health_check(self) -> bool:
        if self._client is None:
            return False
        try:
            return await self._client.ping()
        except Exception:
            return False
