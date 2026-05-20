"""
idle-engine/sync.py
State persistence, offline catch-up, Redis/PostgreSQL integration stubs.
"""

from __future__ import annotations

import time
import json
from typing import Dict, Optional, Tuple
from dataclasses import dataclass, asdict

# Stubs for Redis / PostgreSQL — swap for real clients in production
class _RedisStub:
    _store: Dict[str, str] = {}

    @classmethod
    def get(cls, key: str) -> Optional[str]:
        return cls._store.get(key)

    @classmethod
    def set(cls, key: str, value: str, ex: Optional[int] = None):
        cls._store[key] = value

    @classmethod
    def delete(cls, key: str):
        cls._store.pop(key, None)


class _PGStub:
    @classmethod
    def execute(cls, query: str, params: Tuple = ()):
        # Placeholder for real DB call
        pass


REDIS = _RedisStub()
PG = _PGStub()


@dataclass
class PlayerState:
    player_id: str
    level: int
    xp: int
    tech_points: int
    tech_ranks: Dict[str, int]
    fleet: list
    active_boosts: list
    current_sector: str
    last_sync_at: int
    total_earnings: int
    currency: int

    def to_json(self) -> str:
        return json.dumps(asdict(self), default=str)

    @classmethod
    def from_json(cls, raw: str) -> "PlayerState":
        data = json.loads(raw)
        return cls(**data)


def save_state(state: PlayerState, redis_only: bool = False):
    """Persist player state to Redis (hot) and optionally PostgreSQL (cold)."""
    key = f"player:{state.player_id}"
    REDIS.set(key, state.to_json())
    if not redis_only:
        PG.execute(
            "INSERT INTO player_states (player_id, data) VALUES (%s, %s) "
            "ON CONFLICT (player_id) DO UPDATE SET data = EXCLUDED.data",
            (state.player_id, state.to_json()),
        )


def load_state(player_id: str) -> Optional[PlayerState]:
    """Load player state from Redis, fallback to PG (stub)."""
    key = f"player:{player_id}"
    raw = REDIS.get(key)
    if raw:
        return PlayerState.from_json(raw)
    return None


def catch_up_offline(
    state: PlayerState,
    current_time: Optional[int] = None,
) -> Tuple[PlayerState, Dict]:
    """
    Calculate offline earnings and apply them to the player state.

    Returns:
        (updated_state, catch_up_report)
    """
    from .calculator import calculate_offline_earnings
    from .progression import add_xp
    from .boostManager import filter_expired_boosts, get_active_boost_multiplier

    now = current_time if current_time is not None else int(time.time())
    elapsed = now - state.last_sync_at
    if elapsed <= 0:
        return state, {"earnings": 0, "elapsed": 0}

    # Import here to avoid circular imports at module level
    from .fleetManager import fleet_power
    from .sectorManager import calculate_risk_penalty

    fp = fleet_power(state.fleet)
    sector_penalty_bp = calculate_risk_penalty(fp, state.current_sector)

    # Build effective boosts list
    active = filter_expired_boosts(state.active_boosts, now)

    earnings, breakdown = calculate_offline_earnings(
        fleet_power=fp,
        sector_id=state.current_sector,
        active_boosts=active,
        time_elapsed_seconds=elapsed,
    )

    # Apply risk penalty
    earnings = (earnings * sector_penalty_bp) // 10000
    breakdown["risk_penalty_bp"] = sector_penalty_bp
    breakdown["final_earnings"] = earnings

    # Update state
    new_state = PlayerState(
        player_id=state.player_id,
        level=state.level,
        xp=state.xp,
        tech_points=state.tech_points,
        tech_ranks=state.tech_ranks,
        fleet=state.fleet,
        active_boosts=active,
        current_sector=state.current_sector,
        last_sync_at=now,
        total_earnings=state.total_earnings + earnings,
        currency=state.currency + earnings,
    )

    # Grant XP from trade earnings
    new_xp, new_level, levels_gained, xp_breakdown = add_xp(
        current_xp=new_state.xp,
        current_level=new_state.level,
        trade_earnings=earnings,
    )
    new_state.xp = new_xp
    new_state.level = new_level

    report = {
        "elapsed_seconds": elapsed,
        "earnings": earnings,
        "breakdown": breakdown,
        "xp_breakdown": xp_breakdown,
        "levels_gained": levels_gained,
    }
    return new_state, report
