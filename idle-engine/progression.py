"""
Progression module — XP curves, leveling math, and prestige logic.
"""
from __future__ import annotations

from typing import Dict, Optional, Tuple
from pydantic import BaseModel

from models import PlayerProgression, ResourceType


class XPCurve(BaseModel):
    """Defines XP requirements and scaling for levels."""

    base_xp: float = 100.0
    exponent: float = 1.5
    linear_factor: float = 50.0
    prestige_scaling: float = 2.0
    max_level: int = 100

    def xp_for_level(self, level: int, prestige: int = 0) -> int:
        """Calculate XP needed to reach `level` from `level - 1`."""
        if level <= 1:
            return 0
        prestige_mult = (prestige + 1) ** self.prestige_scaling
        raw = self.base_xp * (level ** self.exponent) + self.linear_factor * level
        return int(raw * prestige_mult)

    def total_xp_for_level(self, target_level: int, prestige: int = 0) -> int:
        """Total XP required to reach target_level from level 1."""
        return sum(self.xp_for_level(lvl, prestige) for lvl in range(2, target_level + 1))

    def level_from_xp(self, total_xp: int, prestige: int = 0) -> int:
        """Determine level given total accumulated XP."""
        level = 1
        accumulated = 0
        while level < self.max_level:
            needed = self.xp_for_level(level + 1, prestige)
            if accumulated + needed > total_xp:
                break
            accumulated += needed
            level += 1
        return level


class PrestigeSystem:
    """Handles prestige resets and permanent bonuses."""

    PRESTIGE_LEVEL_REQUIREMENT: int = 100
    BASE_PRESTIGE_BONUS: float = 0.1  # 10% per prestige

    @classmethod
    def can_prestige(cls, progression: PlayerProgression) -> bool:
        return progression.level >= cls.PRESTIGE_LEVEL_REQUIREMENT

    @classmethod
    def calculate_prestige_bonuses(cls, prestige_count: int) -> Dict[str, float]:
        return {
            "generation_multiplier": 1.0 + cls.BASE_PRESTIGE_BONUS * prestige_count,
            "xp_multiplier": 1.0 + cls.BASE_PRESTIGE_BONUS * prestige_count,
            "cargo_multiplier": 1.0 + (cls.BASE_PRESTIGE_BONUS * 0.5) * prestige_count,
            "start_level": min(prestige_count * 5, 50),
        }

    @classmethod
    def perform_prestige(cls, progression: PlayerProgression, xp_curve: XPCurve) -> Tuple[PlayerProgression, Dict[str, float]]:
        if not cls.can_prestige(progression):
            raise ValueError(f"Must reach level {cls.PRESTIGE_LEVEL_REQUIREMENT} to prestige")

        prestige_count = progression.prestige_count + 1
        bonuses = cls.calculate_prestige_bonuses(prestige_count)

        new_progression = PlayerProgression(
            player_id=progression.player_id,
            level=int(bonuses["start_level"]),
            xp=0,
            prestige_count=prestige_count,
            total_play_time_seconds=progression.total_play_time_seconds,
            xp_multiplier=bonuses["xp_multiplier"],
            level_cap=xp_curve.max_level,
        )
        return new_progression, bonuses


class ProgressionEngine:
    """Main engine for player progression calculations."""

    def __init__(self, xp_curve: Optional[XPCurve] = None):
        self.xp_curve = xp_curve or XPCurve()

    def add_xp(self, progression: PlayerProgression, xp_amount: float) -> Tuple[PlayerProgression, int, bool]:
        """
        Add XP and handle level-ups.
        Returns: (updated_progression, levels_gained, leveled_up)
        """
        progression.xp += xp_amount * progression.xp_multiplier
        old_level = progression.level
        new_level = self.xp_curve.level_from_xp(int(progression.xp), progression.prestige_count)

        if new_level > progression.level_cap:
            new_level = progression.level_cap

        progression.level = new_level
        levels_gained = new_level - old_level
        return progression, levels_gained, levels_gained > 0

    def get_level_progress(self, progression: PlayerProgression) -> Dict[str, float]:
        """Get current level progress as percentage and raw values."""
        current_level = progression.level
        if current_level >= self.xp_curve.max_level:
            return {"percent": 100.0, "current_xp": progression.xp, "needed_xp": 0, "total_needed": 0}

        total_xp_to_current = self.xp_curve.total_xp_for_level(current_level, progression.prestige_count)
        total_xp_to_next = self.xp_curve.total_xp_for_level(current_level + 1, progression.prestige_count)

        xp_into_level = progression.xp - total_xp_to_current
        xp_needed = total_xp_to_next - total_xp_to_current
        percent = (xp_into_level / xp_needed * 100) if xp_needed > 0 else 100.0

        return {
            "percent": round(percent, 2),
            "current_xp": xp_into_level,
            "needed_xp": xp_needed,
            "total_needed": total_xp_to_next,
        }

    def get_stats_at_level(self, level: int, prestige: int = 0) -> Dict[str, float]:
        """Calculate base stats for a given level/prestige."""
        level_factor = 1.0 + (level - 1) * 0.02
        prestige_factor = 1.0 + prestige * 0.1
        return {
            "fleet_efficiency": level_factor * prestige_factor,
            "cargo_bonus": level_factor * 0.5 * prestige_factor,
            "speed_bonus": level_factor * 0.3,
            "trade_bonus": level_factor * 0.4 * prestige_factor,
        }
