import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from progression import (
    xp_required_for_level,
    total_xp_for_level,
    level_from_xp,
    add_xp,
    drone_slots_for_level,
    tech_points_for_level,
)


def test_xp_required():
    assert xp_required_for_level(1) == 0
    assert xp_required_for_level(2) == 1000
    assert xp_required_for_level(3) == 1500
    assert xp_required_for_level(4) == 2250


def test_total_xp():
    assert total_xp_for_level(2) == 1000
    assert total_xp_for_level(3) == 2500
    assert total_xp_for_level(4) == 4750


def test_level_from_xp():
    assert level_from_xp(0) == 1
    assert level_from_xp(999) == 1
    assert level_from_xp(1000) == 2
    assert level_from_xp(2499) == 2
    assert level_from_xp(2500) == 3


def test_add_xp_trade():
    new_xp, new_level, gained, _ = add_xp(
        current_xp=0, current_level=1, trade_earnings=100_000
    )
    # 5% of 100k = 5000 XP
    assert new_xp == 5000
    assert new_level == 3
    assert gained == 1


def test_add_xp_discovery():
    new_xp, new_level, gained, _ = add_xp(
        current_xp=0, current_level=1, discovery=True
    )
    assert new_xp == 5000
    assert new_level == 3


def test_slots_and_tech():
    assert drone_slots_for_level(1) == 3
    assert drone_slots_for_level(2) == 5
    assert tech_points_for_level(1) == 0
    assert tech_points_for_level(5) == 4
