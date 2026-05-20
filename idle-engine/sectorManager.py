"""
idle-engine/sectorManager.py
Zone management: risk/reward, unlock requirements, fleet gating.
"""

from __future__ import annotations

import yaml
from pathlib import Path
from typing import Dict, List, Optional

CONFIG_PATH = Path(__file__).with_name("config.yaml")
with open(CONFIG_PATH, "r") as f:
    _CONFIG = yaml.safe_load(f)

_SECTORS = _CONFIG["game_balance"]["sectors"]
_BP = int(_CONFIG["game_balance"]["math"]["basis_points"])


def list_sectors() -> Dict[str, Dict]:
    """Return all sector definitions."""
    return {k: dict(v) for k, v in _SECTORS.items()}


def get_sector(sector_id: str) -> Dict:
    if sector_id not in _SECTORS:
        raise ValueError(f"Unknown sector: {sector_id}")
    return dict(_SECTORS[sector_id])


def can_enter_sector(
    sector_id: str,
    player_level: int,
    fleet_power: int,
    unlocked_sectors: Optional[List[str]] = None,
) -> bool:
    """Check if player meets sector requirements."""
    sector = get_sector(sector_id)
    if player_level < int(sector["unlock_level"]):
        return False
    if fleet_power < int(sector["min_fleet_power"]):
        return False
    if unlocked_sectors is not None and sector_id not in unlocked_sectors:
        return False
    return True


def sector_yield_multiplier(sector_id: str) -> int:
    """Return yield multiplier in basis points."""
    return int(get_sector(sector_id)["yield_multiplier_bp"])


def sector_risk_level(sector_id: str) -> int:
    return int(get_sector(sector_id)["risk_level"])


def recommended_fleet_power(sector_id: str) -> int:
    """Minimum fleet power to avoid penalties."""
    return int(get_sector(sector_id)["min_fleet_power"])


def calculate_risk_penalty(
    fleet_power: int,
    sector_id: str,
) -> int:
    """
    If fleet power is below recommended, apply a penalty.
    Returns a penalty multiplier in basis points (e.g. 8000 = -20%).
    """
    rec = recommended_fleet_power(sector_id)
    if fleet_power >= rec:
        return _BP
    # Linear penalty: at 0 power, 50% penalty
    ratio = (fleet_power * _BP) // rec if rec > 0 else _BP
    penalty = (_BP // 2) + (ratio // 2)
    return penalty
