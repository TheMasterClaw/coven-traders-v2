import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fleetManager import (
    roll_drone,
    fleet_power,
    upgrade_drone,
    merge_drones,
    can_add_to_fleet,
    add_to_fleet,
    remove_from_fleet,
)


def test_roll_drone_deterministic():
    d1 = roll_drone(seed=42)
    d2 = roll_drone(seed=42)
    assert d1 == d2
    assert "tier" in d1
    assert "power" in d1


def test_fleet_power():
    fleet = [roll_drone(tier="common", seed=1), roll_drone(tier="common", seed=2)]
    assert fleet_power(fleet) == fleet[0]["power"] + fleet[1]["power"]


def test_upgrade_drone():
    drone = roll_drone(tier="common", seed=1)
    orig_power = drone["power"]
    updated, remaining, ok = upgrade_drone(drone, currency=1_000_000)
    assert ok is True
    assert updated["level"] == 2
    assert updated["power"] == (orig_power * 11000) // 10000


def test_upgrade_drone_insufficient():
    drone = roll_drone(tier="common", seed=1)
    updated, remaining, ok = upgrade_drone(drone, currency=0)
    assert ok is False


def test_merge_same_tier():
    a = roll_drone(tier="common", seed=1)
    b = roll_drone(tier="common", seed=2)
    merged = merge_drones(a, b)
    assert merged["power"] >= max(a["power"], b["power"])


def test_merge_different_tier():
    a = roll_drone(tier="common", seed=1)
    b = roll_drone(tier="rare", seed=2)
    merged = merge_drones(a, b)
    assert merged["tier"] in (a["tier"], b["tier"])


def test_fleet_add_remove():
    fleet = []
    d = roll_drone(seed=1)
    fleet = add_to_fleet(fleet, d, max_slots=10)
    assert len(fleet) == 1
    fleet = remove_from_fleet(fleet, 0)
    assert len(fleet) == 0


def test_fleet_full():
    fleet = [roll_drone(seed=i) for i in range(10)]
    assert can_add_to_fleet(fleet, max_slots=10) is False
