"""
Core data models for the Idle Engine.
"""
from __future__ import annotations

from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime


class ResourceType(str, Enum):
    CREDITS = "credits"
    ORE = "ore"
    GAS = "gas"
    CRYSTAL = "crystal"
    ENERGY = "energy"
    DATA_SHARDS = "data_shards"


class ShipClass(str, Enum):
    SCOUT = "scout"
    HAULER = "hauler"
    MINER = "miner"
    FRIGATE = "frigate"
    CRUISER = "cruiser"
    DREADNOUGHT = "dreadnought"


class BoostType(str, Enum):
    PRODUCTION = "production"
    TRADE = "trade"
    XP = "xp"
    FLEET_SPEED = "fleet_speed"
    TIME_WARP = "time_warp"


class FleetShip(BaseModel):
    ship_id: str
    ship_class: ShipClass
    level: int = 1
    efficiency: float = 1.0
    cargo_capacity: int = 100
    speed: float = 1.0
    base_generation: Dict[ResourceType, float] = Field(default_factory=dict)
    modifiers: Dict[str, float] = Field(default_factory=dict)


class Fleet(BaseModel):
    fleet_id: str
    owner_id: str
    ships: List[FleetShip] = Field(default_factory=list)
    sector_id: str = "sector_0"
    total_efficiency: float = 1.0
    cargo_multiplier: float = 1.0
    speed_multiplier: float = 1.0
    generation_multiplier: float = 1.0
    trade_multiplier: float = 1.0


class Boost(BaseModel):
    boost_id: str
    boost_type: BoostType
    multiplier: float = 1.0
    duration_seconds: int = 3600
    started_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    is_active: bool = False
    stacks_with: List[BoostType] = Field(default_factory=list)


class PlayerProgression(BaseModel):
    player_id: str
    level: int = 1
    xp: int = 0
    prestige_count: int = 0
    total_play_time_seconds: int = 0
    last_sync_at: Optional[datetime] = None
    xp_multiplier: float = 1.0
    level_cap: int = 100


class Sector(BaseModel):
    sector_id: str
    name: str
    difficulty: float = 1.0
    resource_richness: Dict[ResourceType, float] = Field(default_factory=dict)
    danger_level: float = 1.0
    trade_bonus: float = 1.0
    xp_bonus: float = 1.0


class PlayerState(BaseModel):
    player_id: str
    resources: Dict[ResourceType, float] = Field(default_factory=dict)
    fleet: Optional[Fleet] = None
    progression: PlayerProgression
    boosts: List[Boost] = Field(default_factory=list)
    unlocked_sectors: List[str] = Field(default_factory=list)
    last_online_at: Optional[datetime] = None
    settings: Dict[str, Any] = Field(default_factory=dict)


class CalculationResult(BaseModel):
    player_id: str
    timestamp: datetime
    delta_seconds: float
    resources_generated: Dict[ResourceType, float] = Field(default_factory=dict)
    xp_gained: float = 0.0
    credits_earned: float = 0.0
    boosts_applied: List[str] = Field(default_factory=list)
    fleet_efficiency: float = 1.0
    sector_modifiers: Dict[str, float] = Field(default_factory=dict)
