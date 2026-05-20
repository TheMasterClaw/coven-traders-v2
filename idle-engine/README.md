# Coven Traders — Idle Engine

Core calculation server for the Coven Traders idle RPG sci-fi trading game.

## Modules

| Module | Purpose |
|--------|---------|
| `models.py` | Pydantic data models: PlayerState, Fleet, Ship, Boost, Sector, etc. |
| `calculator.py` | Resource generation math, fleet efficiency, sector modifiers |
| `progression.py` | XP curves, leveling, prestige system |
| `offline_sync.py` | Offline catch-up calculations with penalty caps |
| `boost_manager.py` | Time-based boosts, stacking rules, accelerators |
| `redis_store.py` | Redis persistence layer for player/fleet/sector state |
| `engine.py` | Main orchestrator tying all modules together |

## Key Features

- **Time-based resource generation**: Fleets generate resources per-second based on ship class, level, and efficiency.
- **Offline sync**: Calculates earnings for up to 72h offline. Beyond 24h, a 0.5x penalty applies.
- **XP & Leveling**: Polynomial XP curve with prestige resets that grant permanent multipliers.
- **Boosts**: Production, trade, XP, fleet speed, and time-warp boosts with stacking rules.
- **Sector modifiers**: Difficulty, resource richness, trade/XP bonuses per sector.
- **Redis state**: All player/fleet/sector state persisted to Redis with JSON serialization.

## Quick Start

```python
from engine import IdleEngine
from models import Fleet, FleetShip, ShipClass, ResourceType

engine = IdleEngine()

# Initialize player
state = engine.initialize_player("player_1")

# Assign a fleet
fleet = Fleet(
    fleet_id="f1",
    owner_id="player_1",
    ships=[
        FleetShip(
            ship_id="s1",
            ship_class=ShipClass.MINER,
            base_generation={ResourceType.ORE: 10.0},
        )
    ]
)
state.fleet = fleet
engine.save_player(state)

# Sync (calculates offline + online earnings)
result = engine.sync("player_1")
print(result)
```

## Running Tests

```bash
source venv/bin/activate
pytest test_engine.py -v
```

## Redis

Requires a running Redis instance (default: localhost:6379).
