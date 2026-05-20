import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from boostManager import (
    create_boost_instance,
    activate_boost,
    get_active_boost_multiplier,
    filter_expired_boosts,
    list_available_boosts,
)


def test_create_boost():
    b = create_boost_instance("time_accel_2x", owner="player1", quantity=3)
    assert b["quantity"] == 3
    assert b["type"] == "time_accel"
    assert b["multiplier_bp"] == 20_000


def test_activate_boost():
    b = create_boost_instance("time_accel_2x", owner="player1", quantity=1)
    active, updated = activate_boost(b, current_time=1000)
    assert active["activated_at"] == 1000
    assert active["expires_at"] == 4600  # 1000 + 3600
    assert updated["quantity"] == 0


def test_boost_multiplier():
    boosts = [
        {"type": "time_accel", "multiplier_bp": 20_000, "expires_at": 2000},
        {"type": "offline", "multiplier_bp": 20_000, "expires_at": 2000},
    ]
    mult = get_active_boost_multiplier(boosts, current_time=1000)
    # 1.0 * 2.0 * 2.0 = 4.0  -> 40_000 BP
    assert mult == 40_000


def test_filter_expired():
    boosts = [
        {"type": "time_accel", "multiplier_bp": 20_000, "expires_at": 500},
        {"type": "offline", "multiplier_bp": 20_000, "expires_at": 1500},
    ]
    active = filter_expired_boosts(boosts, current_time=1000)
    assert len(active) == 1
    assert active[0]["type"] == "offline"


def test_list_boosts():
    boosts = list_available_boosts()
    assert "time_accel_2x" in boosts
    assert "offline_multiplier_2x" in boosts
