"""
Offline Sync module — calculates catch-up earnings for time spent offline.
"""
from __future__ import annotations

from typing import Optional, Dict, List
from datetime import datetime

from models import PlayerState, Sector, Boost, CalculationResult
from calculator import ResourceCalculator
from boost_manager import BoostManager


class OfflineSyncEngine:
    """Handles offline progress calculation and application."""

    # Maximum offline time that earns full rewards (seconds)
    MAX_FULL_REWARD_SECONDS: float = 86400  # 24 hours

    # Maximum offline time that earns any rewards (seconds)
    MAX_OFFLINE_SECONDS: float = 259200  # 72 hours

    # Penalty factor for offline time beyond full reward threshold
    OFFLINE_PENALTY_FACTOR: float = 0.5

    # Minimum sync interval to prevent spam
    MIN_SYNC_INTERVAL_SECONDS: float = 60  # 1 minute

    def __init__(self, boost_manager: Optional[BoostManager] = None):
        self.boost_manager = boost_manager or BoostManager()

    def calculate_offline_time(self, player_state: PlayerState, now: Optional[datetime] = None) -> float:
        """Calculate how many seconds the player was offline."""
        if not player_state.last_online_at:
            return 0.0

        now = now or datetime.utcnow()
        delta = (now - player_state.last_online_at).total_seconds()

        # Enforce minimum sync interval
        if delta < self.MIN_SYNC_INTERVAL_SECONDS:
            return 0.0

        return min(delta, self.MAX_OFFLINE_SECONDS)

    def calculate_offline_earnings(
        self,
        player_state: PlayerState,
        sector: Optional[Sector] = None,
        now: Optional[datetime] = None,
    ) -> CalculationResult:
        """Calculate all earnings accumulated while offline."""
        delta_seconds = self.calculate_offline_time(player_state, now)

        if delta_seconds <= 0:
            return CalculationResult(
                player_id=player_state.player_id,
                timestamp=now or datetime.utcnow(),
                delta_seconds=0.0,
            )

        # Get active boosts that were running before going offline
        # (boosts pause while offline unless they are permanent or time-warp)
        active_boosts = self._get_offline_applicable_boosts(player_state)

        result = ResourceCalculator.calculate_generation(
            player_state=player_state,
            delta_seconds=delta_seconds,
            sector=sector,
            active_boosts=active_boosts,
        )

        return result

    def _get_offline_applicable_boosts(self, player_state: PlayerState) -> List[Boost]:
        """
        Determine which boosts apply to offline progress.
        By default, only permanent boosts and time-warps apply offline.
        """
        applicable = []
        for boost in player_state.boosts:
            if not boost.is_active:
                continue
            # Time warp boosts explicitly apply offline
            if boost.boost_type.value == "time_warp":
                applicable.append(boost)
            # Permanent boosts (duration -1) apply offline
            if boost.duration_seconds < 0:
                applicable.append(boost)
        return applicable

    def apply_offline_earnings(
        self,
        player_state: PlayerState,
        result: CalculationResult,
    ) -> PlayerState:
        """Apply offline calculation result to player state."""
        return ResourceCalculator.apply_result(player_state, result)

    def sync_player(
        self,
        player_state: PlayerState,
        sector: Optional[Sector] = None,
        now: Optional[datetime] = None,
    ) -> Dict:
        """
        Full offline sync: calculate and apply offline earnings.
        Returns a summary dict with results.
        """
        now = now or datetime.utcnow()

        # Expire any ended boosts first
        self.boost_manager.expire_boosts(player_state)

        # Calculate offline earnings
        result = self.calculate_offline_earnings(player_state, sector, now)

        # Apply to state
        updated_state = self.apply_offline_earnings(player_state, result)
        updated_state.last_online_at = now

        return {
            "player_id": updated_state.player_id,
            "offline_seconds": result.delta_seconds,
            "resources_generated": result.resources_generated,
            "credits_earned": result.credits_earned,
            "xp_gained": result.xp_gained,
            "fleet_efficiency": result.fleet_efficiency,
            "boosts_applied": result.boosts_applied,
            "sector_modifiers": result.sector_modifiers,
            "timestamp": now.isoformat(),
        }

    def estimate_offline_earnings(
        self,
        player_state: PlayerState,
        offline_hours: float,
        sector: Optional[Sector] = None,
    ) -> CalculationResult:
        """Estimate earnings for a given offline duration without applying."""
        delta_seconds = min(offline_hours * 3600, self.MAX_OFFLINE_SECONDS)
        active_boosts = self._get_offline_applicable_boosts(player_state)

        return ResourceCalculator.calculate_generation(
            player_state=player_state,
            delta_seconds=delta_seconds,
            sector=sector,
            active_boosts=active_boosts,
        )
