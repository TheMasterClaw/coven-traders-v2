"""
Idle Engine — main orchestrator that ties together all modules.
"""
from __future__ import annotations

from typing import Optional, Dict, Any
from datetime import datetime

from models import PlayerState, Fleet, Sector, Boost, PlayerProgression, ResourceType
from calculator import ResourceCalculator, FleetCalculator
from progression import ProgressionEngine, XPCurve, PrestigeSystem
from offline_sync import OfflineSyncEngine
from boost_manager import BoostManager
from redis_store import RedisStore


class IdleEngine:
    """
    Core idle engine for Coven Traders.
    Orchestrates resource generation, progression, boosts, and offline sync.
    """

    def __init__(
        self,
        redis_host: str = "localhost",
        redis_port: int = 6379,
        redis_db: int = 0,
        redis_password: Optional[str] = None,
        xp_curve: Optional[XPCurve] = None,
    ):
        self.store = RedisStore(redis_host, redis_port, redis_db, redis_password)
        self.progression = ProgressionEngine(xp_curve)
        self.offline_sync = OfflineSyncEngine()
        self.boost_manager = BoostManager()

    def initialize_player(self, player_id: str, starting_fleet: Optional[Fleet] = None) -> PlayerState:
        """Create a new player with default state."""
        progression = PlayerProgression(player_id=player_id)
        state = PlayerState(
            player_id=player_id,
            progression=progression,
            fleet=starting_fleet,
            last_online_at=datetime.utcnow(),
        )
        self.store.save_player_state(state)
        return state

    def load_player(self, player_id: str) -> Optional[PlayerState]:
        """Load player state from Redis."""
        return self.store.load_player_state(player_id)

    def save_player(self, player_state: PlayerState) -> bool:
        """Save player state to Redis."""
        return self.store.save_player_state(player_state)

    def sync(self, player_id: str, sector_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Main sync entry point — calculates offline earnings, applies progression,
        updates boosts, and saves state.
        """
        state = self.load_player(player_id)
        if not state:
            raise ValueError(f"Player {player_id} not found")

        # Load sector if specified
        sector = None
        if sector_id:
            sector = self.store.load_sector(sector_id)

        # Expire old boosts
        self.boost_manager.expire_boosts(state)

        # Offline sync
        sync_result = self.offline_sync.sync_player(state, sector)

        # Update state from sync result
        state = self._apply_sync_result(state, sync_result)

        # Check for level-ups
        if sync_result["xp_gained"] > 0:
            state.progression, levels_gained, leveled_up = self.progression.add_xp(
                state.progression, sync_result["xp_gained"]
            )
            sync_result["levels_gained"] = levels_gained
            sync_result["leveled_up"] = leveled_up
            sync_result["new_level"] = state.progression.level

        # Save updated state
        self.save_player(state)

        return sync_result

    def tick(self, player_id: str, delta_seconds: float, sector_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Process a time tick (for online/real-time updates).
        """
        state = self.load_player(player_id)
        if not state:
            raise ValueError(f"Player {player_id} not found")

        sector = None
        if sector_id:
            sector = self.store.load_sector(sector_id)

        active_boosts = self.boost_manager.get_active_boosts()
        result = ResourceCalculator.calculate_generation(state, delta_seconds, sector, active_boosts)
        state = ResourceCalculator.apply_result(state, result)

        # Check level-ups
        if result.xp_gained > 0:
            state.progression, levels_gained, leveled_up = self.progression.add_xp(
                state.progression, result.xp_gained
            )

        self.save_player(state)

        return {
            "player_id": player_id,
            "delta_seconds": delta_seconds,
            "resources_generated": result.resources_generated,
            "credits_earned": result.credits_earned,
            "xp_gained": result.xp_gained,
            "fleet_efficiency": result.fleet_efficiency,
            "level": state.progression.level,
        }

    def apply_boost(self, player_id: str, boost: Boost) -> Dict[str, Any]:
        """Apply a boost to a player."""
        state = self.load_player(player_id)
        if not state:
            raise ValueError(f"Player {player_id} not found")

        state = self.boost_manager.apply_boost_to_player(state, boost)
        self.save_player(state)

        return {
            "player_id": player_id,
            "boost_id": boost.boost_id,
            "boost_type": boost.boost_type.value,
            "multiplier": boost.multiplier,
            "duration_seconds": boost.duration_seconds,
            "expires_at": boost.expires_at.isoformat() if boost.expires_at else None,
        }

    def prestige(self, player_id: str) -> Dict[str, Any]:
        """Perform a prestige reset for a player."""
        state = self.load_player(player_id)
        if not state:
            raise ValueError(f"Player {player_id} not found")

        new_progression, bonuses = PrestigeSystem.perform_prestige(state.progression, self.progression.xp_curve)
        state.progression = new_progression

        # Reset some resources but keep permanent bonuses
        state.resources = {ResourceType.CREDITS: state.resources.get(ResourceType.CREDITS, 0.0) * 0.1}

        self.save_player(state)

        return {
            "player_id": player_id,
            "prestige_count": new_progression.prestige_count,
            "new_level": new_progression.level,
            "bonuses": bonuses,
        }

    def get_player_status(self, player_id: str) -> Dict[str, Any]:
        """Get full player status including progression, resources, and active boosts."""
        state = self.load_player(player_id)
        if not state:
            raise ValueError(f"Player {player_id} not found")

        level_progress = self.progression.get_level_progress(state.progression)
        active_boosts = self.boost_manager.get_active_boosts()

        return {
            "player_id": player_id,
            "level": state.progression.level,
            "xp": state.progression.xp,
            "prestige": state.progression.prestige_count,
            "level_progress": level_progress,
            "resources": state.resources,
            "fleet_efficiency": FleetCalculator.calculate_fleet_totals(state.fleet)["fleet_efficiency"] if state.fleet else 0.0,
            "active_boosts": [
                {
                    "boost_id": b.boost_id,
                    "type": b.boost_type.value,
                    "multiplier": b.multiplier,
                    "remaining_seconds": self.boost_manager.get_remaining_duration(b),
                }
                for b in active_boosts
            ],
            "last_online": state.last_online_at.isoformat() if state.last_online_at else None,
        }

    def _apply_sync_result(self, state: PlayerState, result: Dict[str, Any]) -> PlayerState:
        """Apply offline sync result dict to player state."""
        for res_type, amount in result.get("resources_generated", {}).items():
            state.resources[res_type] = state.resources.get(res_type, 0.0) + amount
        state.resources[ResourceType.CREDITS] = state.resources.get(ResourceType.CREDITS, 0.0) + result.get("credits_earned", 0.0)
        state.progression.xp += result.get("xp_gained", 0.0)
        state.progression.total_play_time_seconds += int(result.get("offline_seconds", 0))
        state.last_online_at = datetime.fromisoformat(result["timestamp"])
        return state
