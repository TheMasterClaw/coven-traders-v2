"""
idle-engine/boostManager.py
Boost mechanics: time accelerators, offline multipliers, instant completions.
Stored as consumable items with deterministic integer multipliers.
"""

from __future__ import annotations

import yaml
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

CONFIG_PATH = Path(__file__).with_name("config.yaml")
with open(CONFIG_PATH, "r") as f:
    _CONFIG = yaml.safe_load(f)

_BOOST_CFG = _CONFIG["game_balance"]["boosts"]
_BP = int(_CONFIG["game_balance"]["math"]["basis_points"])


def get_boost_template(boost_id: str) -> Dict:
    """Return a copy of the boost definition from config."""
    cfg = _BOOST_CFG.get(boost_id)
    if not cfg:
        raise ValueError(f"Unknown boost_id: {boost_id}")
    return dict(cfg)


def create_boost_instance(boost_id: str, owner: str, quantity: int = 1) -> Dict:
    """Create a player-owned boost item."""
    template = get_boost_template(boost_id)
    return {
        "boost_id": boost_id,
        "owner": owner,
        "type": template["type"],
        "multiplier_bp": int(template["multiplier_bp"]),
        "duration_seconds": int(template["duration_seconds"]),
        "quantity": quantity,
        "created_at": int(time.time()),
    }


def activate_boost(
    boost_instance: Dict,
    current_time: Optional[int] = None,
) -> Tuple[Dict, Dict]:
    """
    Activate a boost instance.

    Returns:
        (active_effect_dict, updated_inventory_item)
    """
    now = current_time if current_time is not None else int(time.time())
    if boost_instance["quantity"] <= 0:
        raise ValueError("Boost quantity is zero")

    active = {
        "boost_id": boost_instance["boost_id"],
        "type": boost_instance["type"],
        "multiplier_bp": boost_instance["multiplier_bp"],
        "activated_at": now,
        "expires_at": now + boost_instance["duration_seconds"],
    }

    updated = dict(boost_instance)
    updated["quantity"] -= 1
    return active, updated


def get_active_boost_multiplier(active_boosts: List[Dict], current_time: Optional[int] = None) -> int:
    """
    Aggregate multipliers of all currently active boosts.
    Multiplicative stacking using basis points.
    """
    now = current_time if current_time is not None else int(time.time())
    total = _BP
    for ab in active_boosts:
        if ab["expires_at"] > now:
            total = (total * ab["multiplier_bp"]) // _BP
    return total


def filter_expired_boosts(active_boosts: List[Dict], current_time: Optional[int] = None) -> List[Dict]:
    """Remove expired boosts from the active list."""
    now = current_time if current_time is not None else int(time.time())
    return [ab for ab in active_boosts if ab["expires_at"] > now]


def list_available_boosts() -> Dict[str, Dict]:
    """Return all boost templates defined in config."""
    return {k: dict(v) for k, v in _BOOST_CFG.items() if not k.startswith("_")}
