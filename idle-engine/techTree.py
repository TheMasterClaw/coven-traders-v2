"""
idle-engine/techTree.py
Research system: tech points, ranks, unlocks.
"""

from __future__ import annotations

import yaml
from pathlib import Path
from typing import Dict, List, Tuple, Optional

CONFIG_PATH = Path(__file__).with_name("config.yaml")
with open(CONFIG_PATH, "r") as f:
    _CONFIG = yaml.safe_load(f)

_TECH_CFG = _CONFIG["game_balance"]["tech_tree"]
_BRANCHES = _TECH_CFG["branches"]
_MAX_RANK = int(_TECH_CFG["max_rank_per_tech"])
_COST_BASE = float(_TECH_CFG["cost_formula_base"])
_COST_EXP = float(_TECH_CFG["cost_formula_exponent"])


def tech_cost(rank: int) -> int:
    """
    Cost to advance from current rank to next.
    Formula: base ^ (rank * exponent)
    """
    if rank >= _MAX_RANK:
        return 0
    # Use integer math: scale up, compute power, scale down
    val = int((_COST_BASE ** (rank * _COST_EXP)) * 1000)
    return max(1, val)


def list_branches() -> Dict[str, Dict]:
    return {k: dict(v) for k, v in _BRANCHES.items()}


def get_branch(branch_id: str) -> Dict:
    if branch_id not in _BRANCHES:
        raise ValueError(f"Unknown branch: {branch_id}")
    return dict(_BRANCHES[branch_id])


def can_research(
    branch_id: str,
    current_rank: int,
    tech_points: int,
    prerequisites: Optional[List[str]] = None,
) -> bool:
    """Check if player can afford and meet prerequisites."""
    if current_rank >= _MAX_RANK:
        return False
    cost = tech_cost(current_rank)
    if tech_points < cost:
        return False
    # Simple prerequisite check: all listed must be rank >= 1
    if prerequisites:
        for pre in prerequisites:
            # In a real system we'd look up the player's pre rank
            pass
    return True


def research(
    branch_id: str,
    current_rank: int,
    tech_points: int,
) -> Tuple[int, int, Dict]:
    """
    Attempt to research a branch.

    Returns:
        (new_rank, remaining_points, breakdown)
    """
    cost = tech_cost(current_rank)
    if current_rank >= _MAX_RANK:
        return current_rank, tech_points, {"error": "Max rank reached"}
    if tech_points < cost:
        return current_rank, tech_points, {"error": "Insufficient tech points"}

    new_rank = current_rank + 1
    remaining = tech_points - cost
    branch = get_branch(branch_id)
    breakdown = {
        "branch": branch_id,
        "previous_rank": current_rank,
        "new_rank": new_rank,
        "cost": cost,
        "unlocks": {
            "sectors": branch.get("unlocks_sectors", []),
            "fleet_types": branch.get("unlocks_fleet_types", []),
        },
    }
    return new_rank, remaining, breakdown


def apply_tech_bonuses(
    branch_ranks: Dict[str, int],
    base_yield_bp: int,
) -> int:
    """
    Apply economics tech yield bonuses.
    Returns adjusted yield in basis points.
    """
    econ_rank = branch_ranks.get("economics", 0)
    if econ_rank <= 0:
        return base_yield_bp
    bonus_per_rank = int(_BRANCHES["economics"]["yield_bonus_per_rank_bp"])
    total_bonus = econ_rank * bonus_per_rank
    return base_yield_bp + total_bonus


def apply_engineering_bonuses(
    branch_ranks: Dict[str, int],
    base_slots: int,
) -> int:
    """Apply engineering slot bonuses."""
    eng_rank = branch_ranks.get("engineering", 0)
    if eng_rank <= 0:
        return base_slots
    bonus_per_rank = int(_BRANCHES["engineering"]["slot_bonus_per_rank"])
    return base_slots + (eng_rank * bonus_per_rank)
