"""
Boost Manager — handles time-based boosts, accelerators, and stacking logic.
"""
from __future__ import annotations

from typing import Dict, List, Optional
from datetime import datetime, timedelta

from models import Boost, BoostType, PlayerState


class BoostManager:
    """Manages active boosts, durations, and stacking rules."""

    # Which boost types can stack with each other
    STACKING_RULES: Dict[BoostType, List[BoostType]] = {
        BoostType.PRODUCTION: [BoostType.TIME_WARP, BoostType.FLEET_SPEED],
        BoostType.TRADE: [BoostType.TIME_WARP],
        BoostType.XP: [BoostType.TIME_WARP, BoostType.FLEET_SPEED],
        BoostType.FLEET_SPEED: [BoostType.PRODUCTION, BoostType.XP, BoostType.TIME_WARP],
        BoostType.TIME_WARP: [BoostType.PRODUCTION, BoostType.TRADE, BoostType.XP, BoostType.FLEET_SPEED],
    }

    # Maximum number of concurrent boosts of the same type
    MAX_SAME_TYPE_BOOSTS: int = 3

    def __init__(self):
        self._boosts: Dict[str, Boost] = {}

    def add_boost(self, boost: Boost) -> Boost:
        """Register a new boost and activate it."""
        now = datetime.utcnow()
        boost.started_at = now
        boost.expires_at = now + timedelta(seconds=boost.duration_seconds)
        boost.is_active = True
        self._boosts[boost.boost_id] = boost
        return boost

    def get_active_boosts(self, boost_type: Optional[BoostType] = None) -> List[Boost]:
        """Get all currently active boosts, optionally filtered by type."""
        now = datetime.utcnow()
        active = []
        for boost in self._boosts.values():
            if boost.is_active and boost.expires_at and boost.expires_at > now:
                if boost_type is None or boost.boost_type == boost_type:
                    active.append(boost)
        return active

    def get_boost_multiplier(self, boost_type: BoostType) -> float:
        """Calculate combined multiplier for a boost type (multiplicative stacking)."""
        active = self.get_active_boosts(boost_type)
        if not active:
            return 1.0
        multiplier = 1.0
        for boost in active:
            multiplier *= boost.multiplier
        return multiplier

    def get_all_multipliers(self) -> Dict[BoostType, float]:
        """Get combined multipliers for all boost types."""
        return {
            bt: self.get_boost_multiplier(bt)
            for bt in BoostType
        }

    def can_stack(self, existing: Boost, new_boost: Boost) -> bool:
        """Check if two boosts can stack together."""
        if existing.boost_type == new_boost.boost_type:
            same_type_count = len(self.get_active_boosts(new_boost.boost_type))
            return same_type_count < self.MAX_SAME_TYPE_BOOSTS
        allowed = self.STACKING_RULES.get(existing.boost_type, [])
        return new_boost.boost_type in allowed

    def apply_boost_to_player(self, player_state: PlayerState, boost: Boost) -> PlayerState:
        """Apply a boost to a player state, respecting stacking rules."""
        # Check stacking against existing player boosts
        active_same_type = [b for b in player_state.boosts if b.boost_type == boost.boost_type and b.is_active]
        if len(active_same_type) >= self.MAX_SAME_TYPE_BOOSTS:
            # Replace oldest boost of same type
            oldest = min(active_same_type, key=lambda b: b.started_at or datetime.min)
            player_state.boosts.remove(oldest)

        now = datetime.utcnow()
        boost.started_at = now
        boost.expires_at = now + timedelta(seconds=boost.duration_seconds)
        boost.is_active = True
        player_state.boosts.append(boost)
        return player_state

    def expire_boosts(self, player_state: Optional[PlayerState] = None) -> List[Boost]:
        """Expire all ended boosts. Returns list of expired boosts."""
        now = datetime.utcnow()
        expired = []

        # Expire from internal registry
        for boost_id, boost in list(self._boosts.items()):
            if boost.is_active and boost.expires_at and boost.expires_at <= now:
                boost.is_active = False
                expired.append(boost)

        # Expire from player state if provided
        if player_state:
            for boost in list(player_state.boosts):
                if boost.is_active and boost.expires_at and boost.expires_at <= now:
                    boost.is_active = False
                    expired.append(boost)

        return expired

    def get_remaining_duration(self, boost: Boost) -> float:
        """Get remaining duration in seconds for a boost."""
        if not boost.is_active or not boost.expires_at:
            return 0.0
        remaining = (boost.expires_at - datetime.utcnow()).total_seconds()
        return max(0.0, remaining)

    def extend_boost(self, boost_id: str, extra_seconds: int) -> Optional[Boost]:
        """Extend an active boost's duration."""
        boost = self._boosts.get(boost_id)
        if not boost or not boost.is_active:
            return None
        boost.expires_at = boost.expires_at + timedelta(seconds=extra_seconds)
        boost.duration_seconds += extra_seconds
        return boost

    def create_time_warp(self, warp_seconds: int, player_state: PlayerState) -> Boost:
        """Create a time warp boost that simulates offline progress instantly."""
        boost = Boost(
            boost_id=f"timewarp_{player_state.player_id}_{int(datetime.utcnow().timestamp())}",
            boost_type=BoostType.TIME_WARP,
            multiplier=1.0,
            duration_seconds=warp_seconds,
        )
        return self.add_boost(boost)

    def cleanup_expired(self) -> int:
        """Remove fully expired boosts from internal registry. Returns count removed."""
        expired_ids = [bid for bid, b in self._boosts.items() if not b.is_active]
        for bid in expired_ids:
            del self._boosts[bid]
        return len(expired_ids)
