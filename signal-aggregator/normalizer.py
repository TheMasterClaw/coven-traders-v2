"""Signal normalizer - converts raw intel into common schema."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any


class Direction(Enum):
    BULL = "bull"
    BEAR = "bear"
    NEUTRAL = "neutral"


@dataclass
class Signal:
    source: str
    asset: str
    direction: str
    confidence: float
    timestamp: str
    expiry: str
    metadata: dict[str, Any] = field(default_factory=dict)
    signal_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def __post_init__(self):
        if self.direction not in {d.value for d in Direction}:
            raise ValueError(f"Invalid direction: {self.direction}")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be 0-1, got {self.confidence}")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def create(
        cls,
        source: str,
        asset: str,
        direction: Direction | str,
        confidence: float,
        metadata: dict[str, Any] | None = None,
        expiry_seconds: int = 3600,
    ) -> Signal:
        if isinstance(direction, Direction):
            direction = direction.value
        now = datetime.now(timezone.utc)
        expiry = now + timedelta(seconds=expiry_seconds)
        return cls(
            source=source,
            asset=asset,
            direction=direction,
            confidence=round(confidence, 4),
            timestamp=now.isoformat(),
            expiry=expiry.isoformat(),
            metadata=metadata or {},
        )


def normalize_raw(
    source: str,
    asset: str,
    raw_direction: str | float,
    confidence: float,
    metadata: dict[str, Any] | None = None,
    expiry_seconds: int = 3600,
) -> Signal:
    """Normalize various raw direction formats to common schema."""
    direction = _parse_direction(raw_direction)
    return Signal.create(
        source=source,
        asset=asset,
        direction=direction,
        confidence=confidence,
        metadata=metadata,
        expiry_seconds=expiry_seconds,
    )


def _parse_direction(raw: str | float) -> str:
    if isinstance(raw, float):
        if raw > 0.1:
            return Direction.BULL.value
        elif raw < -0.1:
            return Direction.BEAR.value
        return Direction.NEUTRAL.value
    raw = str(raw).lower().strip()
    mapping = {
        "buy": "bull",
        "long": "bull",
        "up": "bull",
        "positive": "bull",
        "sell": "bear",
        "short": "bear",
        "down": "bear",
        "negative": "bear",
        "hold": "neutral",
        "flat": "neutral",
        "none": "neutral",
    }
    return mapping.get(raw, raw) if raw in {d.value for d in Direction} else Direction.NEUTRAL.value
