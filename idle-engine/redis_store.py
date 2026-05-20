"""
Redis state store — persists player state, fleets, and progression data.
"""
from __future__ import annotations

import json
import redis
from typing import Optional, Dict, Any
from datetime import datetime

from models import PlayerState, Fleet, PlayerProgression, Boost, Sector


class RedisStore:
    """Redis-backed state persistence for the idle engine."""

    KEY_PREFIX = "coven:idle"

    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0, password: Optional[str] = None):
        self.client = redis.Redis(
            host=host,
            port=port,
            db=db,
            password=password,
            decode_responses=True,
        )

    def _key(self, *parts: str) -> str:
        return f"{self.KEY_PREFIX}:{':'.join(parts)}"

    def save_player_state(self, player_state: PlayerState) -> bool:
        """Serialize and save full player state to Redis."""
        key = self._key("player", player_state.player_id)
        data = player_state.model_dump(mode="json")
        # Convert datetime objects to ISO strings for JSON
        data = self._serialize_datetimes(data)
        return self.client.set(key, json.dumps(data))

    def load_player_state(self, player_id: str) -> Optional[PlayerState]:
        """Load and deserialize player state from Redis."""
        key = self._key("player", player_id)
        raw = self.client.get(key)
        if not raw:
            return None
        data = json.loads(raw)
        data = self._deserialize_datetimes(data)
        return PlayerState.model_validate(data)

    def delete_player_state(self, player_id: str) -> int:
        """Delete player state from Redis. Returns number of keys deleted."""
        key = self._key("player", player_id)
        return self.client.delete(key)

    def save_fleet(self, fleet: Fleet) -> bool:
        """Save fleet data separately."""
        key = self._key("fleet", fleet.fleet_id)
        data = fleet.model_dump(mode="json")
        data = self._serialize_datetimes(data)
        return self.client.set(key, json.dumps(data))

    def load_fleet(self, fleet_id: str) -> Optional[Fleet]:
        """Load fleet data from Redis."""
        key = self._key("fleet", fleet_id)
        raw = self.client.get(key)
        if not raw:
            return None
        data = json.loads(raw)
        data = self._deserialize_datetimes(data)
        return Fleet.model_validate(data)

    def save_sector(self, sector: Sector) -> bool:
        """Save sector configuration."""
        key = self._key("sector", sector.sector_id)
        data = sector.model_dump(mode="json")
        data = self._serialize_datetimes(data)
        return self.client.set(key, json.dumps(data))

    def load_sector(self, sector_id: str) -> Optional[Sector]:
        """Load sector configuration from Redis."""
        key = self._key("sector", sector_id)
        raw = self.client.get(key)
        if not raw:
            return None
        data = json.loads(raw)
        data = self._deserialize_datetimes(data)
        return Sector.model_validate(data)

    def update_player_resources(self, player_id: str, resources: Dict[str, float]) -> bool:
        """Partial update of player resources."""
        state = self.load_player_state(player_id)
        if not state:
            return False
        for res_type, amount in resources.items():
            state.resources[res_type] = state.resources.get(res_type, 0.0) + amount
        return self.save_player_state(state)

    def get_leaderboard(self, metric: str = "credits", top_n: int = 100) -> list:
        """Get top N players by a resource metric."""
        # This is a simple implementation; for production use Redis Sorted Sets
        pattern = self._key("player", "*")
        keys = self.client.keys(pattern)
        scores = []
        for key in keys:
            raw = self.client.get(key)
            if raw:
                data = json.loads(raw)
                score = data.get("resources", {}).get(metric, 0.0)
                scores.append((data.get("player_id"), score))
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_n]

    def _serialize_datetimes(self, obj: Any) -> Any:
        """Recursively convert datetime objects to ISO strings."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, dict):
            return {k: self._serialize_datetimes(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [self._serialize_datetimes(item) for item in obj]
        return obj

    def _deserialize_datetimes(self, obj: Any) -> Any:
        """Recursively parse ISO datetime strings back to datetime objects."""
        if isinstance(obj, str):
            try:
                return datetime.fromisoformat(obj)
            except ValueError:
                return obj
        if isinstance(obj, dict):
            return {k: self._deserialize_datetimes(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [self._deserialize_datetimes(item) for item in obj]
        return obj

    def ping(self) -> bool:
        """Check Redis connectivity."""
        try:
            return self.client.ping()
        except redis.ConnectionError:
            return False
