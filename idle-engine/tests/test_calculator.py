import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from calculator import calculate_offline_earnings, calculate_tick_earnings


def test_basic_offline_earnings():
    earnings, breakdown = calculate_offline_earnings(
        fleet_power=100,
        sector_id="core_systems",
        active_boosts=[],
        time_elapsed_seconds=10,
    )
    # base_rate=100, power=100 -> 10_000/sec
    # core_systems = 0.5x -> 5_000/sec
    # 10 sec -> 50_000
    assert earnings == 50_000
    assert breakdown["total_earnings"] == 50_000


def test_with_boost():
    earnings, _ = calculate_offline_earnings(
        fleet_power=100,
        sector_id="outer_rim",
        active_boosts=[{"type": "time_accel", "multiplier_bp": 20_000}],
        time_elapsed_seconds=10,
    )
    # base 10_000 * 1.5 = 15_000/sec
    # *2 boost = 30_000/sec
    # 10 sec = 300_000
    assert earnings == 300_000


def test_tick():
    assert calculate_tick_earnings(10, "core_systems", []) == 500


def test_max_offline_cap():
    earnings, _ = calculate_offline_earnings(
        fleet_power=1,
        sector_id="core_systems",
        active_boosts=[],
        time_elapsed_seconds=999_999,
    )
    # capped at 72h = 259_200 sec
    # 100 * 1 * 0.5 * 259_200 = 12_960_000
    assert earnings == 12_960_000


def test_multiple_boosts():
    earnings, _ = calculate_offline_earnings(
        fleet_power=10,
        sector_id="nebula",
        active_boosts=[
            {"type": "time_accel", "multiplier_bp": 20_000},
            {"type": "offline", "multiplier_bp": 20_000},
        ],
        time_elapsed_seconds=1,
    )
    # base 100*10=1000 * 2.0 (nebula) = 2000
    # *2 *2 = 8000
    assert earnings == 8_000
