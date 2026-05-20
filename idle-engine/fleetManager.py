"""
idle-engine/fleetManager.py
Fleet stats, gacha logic, upgrades, and merges.
Deterministic integer math for all stats.
"""

from __future__ import annotations

import yaml
import random
from pathlib import Path
from typing import Dict, List, Tuple, Optional

CONFIG_PATH = Path(__file__).with_name("config.yaml")
with open(CONFIG_PATH, "r") as f:
    _CONFIG = yaml.safe_load(f)

_FLEET_CFG = _CONFIG["game_balance"]["fleet"]
_BP = int(_CONFIG["game_balance"]["math"]["basis_points"])
_MAX_FLEET = int(_FLEET_CFG["max_fleet_size"])
_UPGRADE_BASE = int(_FLEET_CFG["upgrade_base_cost"])


def _tier_weights() -> Dict[str, int]:
    return {
        tier: int(data["weight"])
        for tier, data in _FLEET_CFG["tiers"].items()
    }


def roll_tier(seed: Optional[int] = None) -> str:
    """Weighted random tier roll."""
    weights = _tier_weights()
    tiers = list(weights.keys())
    w = list(weights.values())
    rng = random.Random(seed)
    return rng.choices(tiers, weights=w, k=1)[0]


def roll_drone(tier: Optional[str] = None, seed: Optional[int] = None) -> Dict:
    """
    Generate a drone with stats in the tier range.
    Uses integer math; stats are whole numbers.
    """
    if tier is None:
        tier = roll_tier(seed=seed)
    cfg = _FLEET_CFG["tiers"][tier]
    rng = random.Random(seed)

    def _roll(rng, lo, hi):
        return rng.randint(int(lo), int(hi))

    drone = {
        "tier": tier,
        "power": _roll(rng, *cfg["power_range"]),
        "speed": _roll(rng, *cfg["speed_range"]),
        "luck": _roll(rng, *cfg["luck_range"]),
        "defense": _roll(rng, *cfg["defense_range"]),
        "level": 1,
        "experience": 0,
    }
    return drone


def fleet_power(fleet: List[Dict]) -> int:
    """Sum of all drone power in fleet."""
    return sum(d["power"] for d in fleet)


def fleet_speed(fleet: List[Dict]) -> int:
    """Average speed (integer division)."""
    if not fleet:
        return 0
    return sum(d["speed"] for d in fleet) // len(fleet)


def fleet_luck(fleet: List[Dict]) -> int:
    """Average luck."""
    if not fleet:
        return 0
    return sum(d["luck"] for d in fleet) // len(fleet)


def fleet_defense(fleet: List[Dict]) -> int:
    """Sum of defense."""
    return sum(d["defense"] for d in fleet)


def upgrade_cost(drone: Dict) -> int:
    """Cost to upgrade a drone one level."""
    tier = drone["tier"]
    cfg = _FLEET_CFG["tiers"][tier]
    mult = int(cfg["upgrade_cost_bp"])
    # Cost scales linearly with level
    return (_UPGRADE_BASE * mult * drone["level"]) // _BP


def upgrade_drone(drone: Dict, currency: int) -> Tuple[Dict, int, bool]:
    """
    Attempt to upgrade a drone.

    Returns:
        (updated_drone, remaining_currency, success)
    """
    cost = upgrade_cost(drone)
    if currency < cost:
        return drone, currency, False
    updated = dict(drone)
    updated["level"] += 1
    # Stat increase: +10% per level (basis points)
    updated["power"] = (drone["power"] * (_BP + _BP // 10)) // _BP
    updated["speed"] = (drone["speed"] * (_BP + _BP // 10)) // _BP
    updated["luck"] = (drone["luck"] * (_BP + _BP // 10)) // _BP
    updated["defense"] = (drone["defense"] * (_BP + _BP // 10)) // _BP
    return updated, currency - cost, True


def merge_drones(drone_a: Dict, drone_b: Dict) -> Dict:
    """
    Merge two drones. Same tier gives bonus.
    Result takes higher base stats + merge bonus.
    """
    if drone_a["tier"] == drone_b["tier"]:
        bonus_bp = int(_FLEET_CFG["tiers"][drone_a["tier"]]["merge_bonus_bp"])
        bonus_bp += int(_FLEET_CFG["merge_same_tier_bonus_bp"])
    else:
        # Use the lower tier's merge bonus
        tier = min(drone_a["tier"], drone_b["tier"], key=lambda t: _FLEET_CFG["tiers"][t]["weight"])
        bonus_bp = int(_FLEET_CFG["tiers"][tier]["merge_bonus_bp"])

    def _pick(a, b):
        return a if a > b else b

    merged = {
        "tier": _pick(drone_a["tier"], drone_b["tier"]),
        "power": (_pick(drone_a["power"], drone_b["power"]) * (_BP + bonus_bp)) // _BP,
        "speed": (_pick(drone_a["speed"], drone_b["speed"]) * (_BP + bonus_bp)) // _BP,
        "luck": (_pick(drone_a["luck"], drone_b["luck"]) * (_BP + bonus_bp)) // _BP,
        "defense": (_pick(drone_a["defense"], drone_b["defense"]) * (_BP + bonus_bp)) // _BP,
        "level": max(drone_a["level"], drone_b["level"]),
        "experience": 0,
    }
    return merged


def can_add_to_fleet(fleet: List[Dict], max_slots: int) -> bool:
    return len(fleet) < min(max_slots, _MAX_FLEET)


def add_to_fleet(fleet: List[Dict], drone: Dict, max_slots: int) -> List[Dict]:
    if not can_add_to_fleet(fleet, max_slots):
        raise ValueError("Fleet is full")
    return fleet + [drone]


def remove_from_fleet(fleet: List[Dict], index: int) -> List[Dict]:
    if index < 0 or index >= len(fleet):
        raise IndexError("Invalid fleet index")
    return fleet[:index] + fleet[index + 1:]
