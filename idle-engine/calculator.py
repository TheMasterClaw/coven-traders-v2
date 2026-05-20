"""
Calculator module — handles resource generation, fleet efficiency,
and sector-based modifiers for the idle engine.
"""
from __future__ import annotations

from typing import Dict, List, Optional
from datetime import datetime

from models import (
    Fleet, FleetShip, Sector, Boost, BoostType,
    ResourceType, CalculationResult, PlayerState, ShipClass
)


class FleetCalculator:
    """Calculates fleet stats and generation rates."""

    SHIP_CLASS_BASE_STATS: Dict[ShipClass, Dict[str, float]] = {
        ShipClass.SCOUT: {"efficiency": 1.0, "cargo": 50, "speed": 3.0, "gen_factor": 0.5},
        ShipClass.HAULER: {"efficiency": 1.2, "cargo": 500, "speed": 1.0, "gen_factor": 0.8},
        ShipClass.MINER: {"efficiency": 1.5, "cargo": 200, "speed": 0.8, "gen_factor": 2.0},
        ShipClass.FRIGATE: {"efficiency": 1.3, "cargo": 300, "speed": 1.5, "gen_factor": 1.0},
        ShipClass.CRUISER: {"efficiency": 1.8, "cargo": 800, "speed": 1.2, "gen_factor": 1.2},
        ShipClass.DREADNOUGHT: {"efficiency": 2.5, "cargo": 2000, "speed": 0.6, "gen_factor": 1.5},
    }

    @classmethod
    def get_ship_base_stats(cls, ship_class: ShipClass) -> Dict[str, float]:
        return cls.SHIP_CLASS_BASE_STATS.get(ship_class, {"efficiency": 1.0, "cargo": 100, "speed": 1.0, "gen_factor": 1.0})

    @classmethod
    def calculate_ship_generation(cls, ship: FleetShip, sector: Optional[Sector] = None) -> Dict[ResourceType, float]:
        base = cls.get_ship_base_stats(ship.ship_class)
        level_factor = 1.0 + (ship.level - 1) * 0.05
        efficiency = ship.efficiency * base["efficiency"] * level_factor

        generation = {}
        for res_type, base_rate in ship.base_generation.items():
            rate = base_rate * base["gen_factor"] * efficiency
            if sector and res_type in sector.resource_richness:
                rate *= sector.resource_richness[res_type]
            generation[res_type] = rate
        return generation

    @classmethod
    def calculate_fleet_totals(cls, fleet: Fleet, sector: Optional[Sector] = None) -> Dict[str, any]:
        total_generation: Dict[ResourceType, float] = {}
        total_efficiency = 0.0
        total_cargo = 0
        avg_speed = 0.0

        for ship in fleet.ships:
            ship_gen = cls.calculate_ship_generation(ship, sector)
            for res, rate in ship_gen.items():
                total_generation[res] = total_generation.get(res, 0.0) + rate
            base = cls.get_ship_base_stats(ship.ship_class)
            total_efficiency += ship.efficiency * base["efficiency"]
            total_cargo += ship.cargo_capacity
            avg_speed += ship.speed * base["speed"]

        ship_count = max(len(fleet.ships), 1)
        fleet_efficiency = (total_efficiency / ship_count) * fleet.total_efficiency * fleet.generation_multiplier
        cargo = total_cargo * fleet.cargo_multiplier
        speed = (avg_speed / ship_count) * fleet.speed_multiplier

        # Apply fleet-wide multipliers to generation
        for res in total_generation:
            total_generation[res] *= fleet.generation_multiplier * fleet.trade_multiplier

        return {
            "generation_per_second": total_generation,
            "fleet_efficiency": fleet_efficiency,
            "total_cargo": cargo,
            "avg_speed": speed,
        }


class ResourceCalculator:
    """Handles resource accumulation over time with all modifiers."""

    MAX_OFFLINE_SECONDS: float = 86400 * 3  # 3 days cap
    OFFLINE_PENALTY_THRESHOLD: float = 86400  # 1 day
    OFFLINE_PENALTY_FACTOR: float = 0.5

    @classmethod
    def calculate_generation(
        cls,
        player_state: PlayerState,
        delta_seconds: float,
        sector: Optional[Sector] = None,
        active_boosts: Optional[List[Boost]] = None,
    ) -> CalculationResult:
        if delta_seconds <= 0:
            return CalculationResult(player_id=player_state.player_id, timestamp=datetime.utcnow(), delta_seconds=0.0)

        fleet = player_state.fleet
        if not fleet or not fleet.ships:
            return CalculationResult(player_id=player_state.player_id, timestamp=datetime.utcnow(), delta_seconds=delta_seconds)

        # Fleet totals
        fleet_data = FleetCalculator.calculate_fleet_totals(fleet, sector)
        generation = fleet_data["generation_per_second"]
        fleet_efficiency = fleet_data["fleet_efficiency"]

        # Apply boosts
        boost_multiplier = 1.0
        applied_boosts = []
        if active_boosts:
            for boost in active_boosts:
                if boost.is_active and boost.boost_type in (BoostType.PRODUCTION, BoostType.TIME_WARP):
                    boost_multiplier *= boost.multiplier
                    applied_boosts.append(boost.boost_id)

        # Offline penalty
        effective_time = delta_seconds
        penalty_factor = 1.0
        if delta_seconds > cls.OFFLINE_PENALTY_THRESHOLD:
            penalty_factor = cls.OFFLINE_PENALTY_FACTOR
            effective_time = cls.OFFLINE_PENALTY_THRESHOLD + (delta_seconds - cls.OFFLINE_PENALTY_THRESHOLD) * penalty_factor

        effective_time = min(effective_time, cls.MAX_OFFLINE_SECONDS)

        # Calculate resources
        resources_generated = {}
        for res_type, rate in generation.items():
            resources_generated[res_type] = rate * effective_time * boost_multiplier * fleet_efficiency

        # Credits from trade
        trade_rate = sum(generation.values()) * 0.1 * fleet.trade_multiplier
        if sector:
            trade_rate *= sector.trade_bonus
        credits_earned = trade_rate * effective_time * boost_multiplier

        # XP from activity
        xp_rate = 0.1 * fleet_efficiency
        if sector:
            xp_rate *= sector.xp_bonus
        xp_gained = xp_rate * effective_time * boost_multiplier

        sector_mods = {}
        if sector:
            sector_mods = {
                "difficulty": sector.difficulty,
                "trade_bonus": sector.trade_bonus,
                "xp_bonus": sector.xp_bonus,
            }

        return CalculationResult(
            player_id=player_state.player_id,
            timestamp=datetime.utcnow(),
            delta_seconds=delta_seconds,
            resources_generated=resources_generated,
            xp_gained=xp_gained,
            credits_earned=credits_earned,
            boosts_applied=applied_boosts,
            fleet_efficiency=fleet_efficiency,
            sector_modifiers=sector_mods,
        )

    @classmethod
    def apply_result(cls, player_state: PlayerState, result: CalculationResult) -> PlayerState:
        for res_type, amount in result.resources_generated.items():
            player_state.resources[res_type] = player_state.resources.get(res_type, 0.0) + amount
        player_state.resources[ResourceType.CREDITS] = player_state.resources.get(ResourceType.CREDITS, 0.0) + result.credits_earned
        player_state.progression.xp += result.xp_gained
        player_state.progression.total_play_time_seconds += int(result.delta_seconds)
        player_state.last_online_at = result.timestamp
        return player_state
