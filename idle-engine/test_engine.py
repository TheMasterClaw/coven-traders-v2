"""
Tests for the Idle Engine modules.
"""
import pytest
from datetime import datetime, timedelta

from models import (
    PlayerState, Fleet, FleetShip, Sector, Boost, BoostType,
    ResourceType, ShipClass, PlayerProgression, CalculationResult,
)
from calculator import ResourceCalculator, FleetCalculator
from progression import ProgressionEngine, XPCurve, PrestigeSystem
from offline_sync import OfflineSyncEngine
from boost_manager import BoostManager


class TestFleetCalculator:
    def test_ship_generation(self):
        ship = FleetShip(
            ship_id="s1",
            ship_class=ShipClass.MINER,
            level=1,
            efficiency=1.0,
            base_generation={ResourceType.ORE: 10.0},
        )
        gen = FleetCalculator.calculate_ship_generation(ship)
        assert ResourceType.ORE in gen
        assert gen[ResourceType.ORE] > 0

    def test_fleet_totals(self):
        fleet = Fleet(
            fleet_id="f1",
            owner_id="p1",
            ships=[
                FleetShip(ship_id="s1", ship_class=ShipClass.MINER, base_generation={ResourceType.ORE: 10.0}),
                FleetShip(ship_id="s2", ship_class=ShipClass.HAULER, base_generation={ResourceType.CREDITS: 5.0}),
            ],
        )
        totals = FleetCalculator.calculate_fleet_totals(fleet)
        assert "generation_per_second" in totals
        assert ResourceType.ORE in totals["generation_per_second"]
        assert ResourceType.CREDITS in totals["generation_per_second"]


class TestResourceCalculator:
    def test_zero_delta(self):
        state = PlayerState(
            player_id="p1",
            progression=PlayerProgression(player_id="p1"),
            fleet=Fleet(fleet_id="f1", owner_id="p1", ships=[
                FleetShip(ship_id="s1", ship_class=ShipClass.MINER, base_generation={ResourceType.ORE: 10.0}),
            ]),
        )
        result = ResourceCalculator.calculate_generation(state, 0.0)
        assert result.delta_seconds == 0.0
        assert result.xp_gained == 0.0

    def test_basic_generation(self):
        state = PlayerState(
            player_id="p1",
            progression=PlayerProgression(player_id="p1"),
            fleet=Fleet(fleet_id="f1", owner_id="p1", ships=[
                FleetShip(ship_id="s1", ship_class=ShipClass.MINER, base_generation={ResourceType.ORE: 10.0}),
            ]),
        )
        result = ResourceCalculator.calculate_generation(state, 10.0)
        assert result.delta_seconds == 10.0
        assert result.resources_generated[ResourceType.ORE] > 0
        assert result.xp_gained > 0

    def test_offline_penalty(self):
        state = PlayerState(
            player_id="p1",
            progression=PlayerProgression(player_id="p1"),
            fleet=Fleet(fleet_id="f1", owner_id="p1", ships=[
                FleetShip(ship_id="s1", ship_class=ShipClass.MINER, base_generation={ResourceType.ORE: 10.0}),
            ]),
        )
        # 48 hours offline
        result = ResourceCalculator.calculate_generation(state, 86400 * 2)
        assert result.delta_seconds == 86400 * 2
        # Should have penalty applied
        # 10 base * 2 gen_factor * 1.5 efficiency (MINER base) = 30/s per ship
        # Then multiplied by fleet generation_multiplier (1.0) * trade_multiplier (1.0) = still 30/s
        # effective_time = 86400 + 86400 * 0.5 = 129600
        # But fleet_efficiency also multiplies: avg_efficiency=1.5 * total_efficiency=1.0 * generation_multiplier=1.0 = 1.5
        # So 30 * 129600 * 1.5 = 5832000
        expected = 30.0 * 129600 * 1.5
        assert result.resources_generated[ResourceType.ORE] == pytest.approx(expected, rel=0.01)


class TestProgressionEngine:
    def test_xp_curve(self):
        curve = XPCurve(base_xp=100, exponent=1.5)
        xp_l2 = curve.xp_for_level(2)
        assert xp_l2 > 0
        total_l5 = curve.total_xp_for_level(5)
        assert total_l5 > 0

    def test_level_from_xp(self):
        curve = XPCurve(base_xp=100, exponent=1.0, linear_factor=0)
        # level n needs 100*n xp
        progression = PlayerProgression(player_id="p1", xp=250)
        engine = ProgressionEngine(curve)
        prog, levels, leveled = engine.add_xp(progression, 0)
        assert prog.level == 2  # 100 for lvl2, 200 for lvl3, 250 is lvl 2

    def test_prestige(self):
        progression = PlayerProgression(player_id="p1", level=100, xp=1000000, prestige_count=0)
        curve = XPCurve()
        new_prog, bonuses = PrestigeSystem.perform_prestige(progression, curve)
        assert new_prog.prestige_count == 1
        assert new_prog.level > 0
        assert bonuses["generation_multiplier"] > 1.0


class TestBoostManager:
    def test_add_boost(self):
        mgr = BoostManager()
        boost = Boost(boost_id="b1", boost_type=BoostType.PRODUCTION, multiplier=2.0, duration_seconds=3600)
        mgr.add_boost(boost)
        assert boost.is_active
        assert boost.expires_at is not None

    def test_get_multiplier(self):
        mgr = BoostManager()
        mgr.add_boost(Boost(boost_id="b1", boost_type=BoostType.PRODUCTION, multiplier=2.0, duration_seconds=3600))
        mgr.add_boost(Boost(boost_id="b2", boost_type=BoostType.PRODUCTION, multiplier=1.5, duration_seconds=3600))
        mult = mgr.get_boost_multiplier(BoostType.PRODUCTION)
        assert mult == 3.0  # 2.0 * 1.5

    def test_stacking_rules(self):
        mgr = BoostManager()
        b1 = Boost(boost_id="b1", boost_type=BoostType.PRODUCTION, multiplier=2.0, duration_seconds=3600)
        b2 = Boost(boost_id="b2", boost_type=BoostType.TIME_WARP, multiplier=2.0, duration_seconds=3600)
        assert mgr.can_stack(b1, b2)


class TestOfflineSync:
    def test_offline_calculation(self):
        state = PlayerState(
            player_id="p1",
            progression=PlayerProgression(player_id="p1"),
            fleet=Fleet(fleet_id="f1", owner_id="p1", ships=[
                FleetShip(ship_id="s1", ship_class=ShipClass.MINER, base_generation={ResourceType.ORE: 10.0}),
            ]),
            last_online_at=datetime.utcnow() - timedelta(hours=2),
        )
        engine = OfflineSyncEngine()
        result = engine.calculate_offline_earnings(state)
        assert result.delta_seconds > 0
        assert result.resources_generated[ResourceType.ORE] > 0

    def test_sync_player(self):
        state = PlayerState(
            player_id="p1",
            progression=PlayerProgression(player_id="p1"),
            fleet=Fleet(fleet_id="f1", owner_id="p1", ships=[
                FleetShip(ship_id="s1", ship_class=ShipClass.MINER, base_generation={ResourceType.ORE: 10.0}),
            ]),
            last_online_at=datetime.utcnow() - timedelta(hours=1),
        )
        engine = OfflineSyncEngine()
        result = engine.sync_player(state)
        assert result["offline_seconds"] > 0
        assert result["resources_generated"][ResourceType.ORE] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
