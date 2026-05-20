"""
Agent Coaching System
Natural language interface for players to instruct AI disciple agents.
Parses coaching instructions, maps to strategy parameter updates, validates,
applies changes, and generates feedback.
"""

import json
import os
import re
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable


class CoachingIntent(Enum):
    """Recognized coaching intents from natural language."""
    INCREASE_AGGRESSION = "increase_aggression"
    DECREASE_AGGRESSION = "decrease_aggression"
    AVOID_CONDITION = "avoid_condition"
    PREFER_CONDITION = "prefer_condition"
    SET_THRESHOLD = "set_threshold"
    INCREASE_POSITION_SIZE = "increase_position_size"
    DECREASE_POSITION_SIZE = "decrease_position_size"
    FOCUS_ASSET = "focus_asset"
    AVOID_ASSET = "avoid_asset"
    INCREASE_FREQUENCY = "increase_frequency"
    DECREASE_FREQUENCY = "decrease_frequency"
    SET_STOP_LOSS = "set_stop_loss"
    SET_TAKE_PROFIT = "set_take_profit"
    RESET_STRATEGY = "reset_strategy"
    UNKNOWN = "unknown"


@dataclass
class StrategyParameters:
    """Mutable strategy parameters for an AI disciple agent."""
    aggression_level: float = 0.5  # 0.0 - 1.0
    max_position_size: float = 1.0  # multiplier of base size
    stop_loss_pct: float = 0.05
    take_profit_pct: float = 0.10
    trade_frequency: float = 0.5  # 0.0 - 1.0
    preferred_assets: List[str] = field(default_factory=list)
    avoided_assets: List[str] = field(default_factory=list)
    avoided_conditions: List[str] = field(default_factory=list)
    preferred_conditions: List[str] = field(default_factory=list)
    funding_rate_threshold: float = -0.01
    volatility_threshold: float = 0.5
    leverage_max: float = 5.0
    risk_per_trade: float = 0.02

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StrategyParameters":
        return cls(**data)


@dataclass
class CoachingEntry:
    """A single coaching interaction record."""
    timestamp: str
    player_id: str
    agent_id: str
    raw_instruction: str
    parsed_intent: str
    parameter_changes: Dict[str, Any]
    validation_errors: List[str]
    applied: bool
    feedback: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CoachingEntry":
        return cls(**data)


class NLUParser:
    """Natural Language Understanding parser for coaching instructions."""

    # Keyword patterns mapped to intents
    INTENT_PATTERNS: Dict[CoachingIntent, List[str]] = {
        CoachingIntent.INCREASE_AGGRESSION: [
            r"more aggressive",
            r"be aggressive",
            r"increase aggression",
            r"take more risk",
            r"riskier",
            r"go harder",
        ],
        CoachingIntent.DECREASE_AGGRESSION: [
            r"less aggressive",
            r"play safe",
            r"safer",
            r"decrease aggression",
            r"take less risk",
            r"more conservative",
        ],
        CoachingIntent.AVOID_CONDITION: [
            r"avoid\s+(.+?)(?:\s+zone|s)\b",
            r"stay away from\s+(.+?)(?:\s+zone|s)\b",
            r"skip\s+(.+?)(?:\s+zone|s)\b",
        ],
        CoachingIntent.PREFER_CONDITION: [
            r"prefer\s+(.+?)(?:\s+zone|s)\b",
            r"look for\s+(.+?)(?:\s+zone|s)\b",
        ],
        CoachingIntent.SET_THRESHOLD: [
            r"set\s+(.+?)\s+threshold\s+to\s+(-?\d+\.?\d*)",
            r"threshold\s+for\s+(.+?)\s+is\s+(-?\d+\.?\d*)",
        ],
        CoachingIntent.INCREASE_POSITION_SIZE: [
            r"bigger positions",
            r"increase position",
            r"larger trades",
            r"size up",
        ],
        CoachingIntent.DECREASE_POSITION_SIZE: [
            r"smaller positions",
            r"decrease position",
            r"reduce size",
            r"size down",
        ],
        CoachingIntent.FOCUS_ASSET: [
            r"focus on\s+(\w+)",
            r"trade\s+(\w+)",
            r"only\s+(\w+)",
            r"prioritize\s+(\w+)",
        ],
        CoachingIntent.AVOID_ASSET: [
            r"avoid\s+(\w+)",
            r"skip\s+(\w+)",
            r"no\s+(\w+)",
            r"drop\s+(\w+)",
        ],
        CoachingIntent.INCREASE_FREQUENCY: [
            r"trade more often",
            r"increase frequency",
            r"more trades",
            r"be more active",
        ],
        CoachingIntent.DECREASE_FREQUENCY: [
            r"trade less often",
            r"decrease frequency",
            r"fewer trades",
            r"be less active",
        ],
        CoachingIntent.SET_STOP_LOSS: [
            r"stop loss\s+(?:at|to)\s+(-?\d+\.?\d*)",
            r"stoploss\s+(?:at|to)\s+(-?\d+\.?\d*)",
            r"cut losses\s+(?:at|to)\s+(-?\d+\.?\d*)",
        ],
        CoachingIntent.SET_TAKE_PROFIT: [
            r"take profit\s+(?:at|to)\s+(-?\d+\.?\d*)",
            r"profit target\s+(?:at|to)\s+(-?\d+\.?\d*)",
        ],
        CoachingIntent.RESET_STRATEGY: [
            r"reset",
            r"start over",
            r"default settings",
            r"clear strategy",
        ],
    }

    # Parameter mapping for intents
    PARAMETER_DELTA: Dict[CoachingIntent, Dict[str, float]] = {
        CoachingIntent.INCREASE_AGGRESSION: {"aggression_level": 0.1},
        CoachingIntent.DECREASE_AGGRESSION: {"aggression_level": -0.1},
        CoachingIntent.INCREASE_POSITION_SIZE: {"max_position_size": 0.2},
        CoachingIntent.DECREASE_POSITION_SIZE: {"max_position_size": -0.2},
        CoachingIntent.INCREASE_FREQUENCY: {"trade_frequency": 0.1},
        CoachingIntent.DECREASE_FREQUENCY: {"trade_frequency": -0.1},
    }

    def parse(self, instruction: str) -> tuple[CoachingIntent, Dict[str, Any]]:
        """
        Parse a natural language instruction into an intent and extracted parameters.
        Returns: (intent, extracted_values_dict)
        """
        instruction_lower = instruction.lower().strip()

        for intent, patterns in self.INTENT_PATTERNS.items():
            for pattern in patterns:
                match = re.search(pattern, instruction_lower)
                if match:
                    extracted = self._extract_values(intent, match)
                    return intent, extracted

        return CoachingIntent.UNKNOWN, {}

    def _extract_values(self, intent: CoachingIntent, match: re.Match) -> Dict[str, Any]:
        """Extract parameter values from regex match groups."""
        groups = match.groups()
        extracted: Dict[str, Any] = {}

        if intent in (CoachingIntent.AVOID_CONDITION, CoachingIntent.PREFER_CONDITION):
            if groups:
                extracted["condition"] = groups[0].strip()
        elif intent == CoachingIntent.SET_THRESHOLD:
            if len(groups) >= 2:
                extracted["threshold_name"] = groups[0].strip()
                extracted["threshold_value"] = float(groups[1])
        elif intent in (CoachingIntent.FOCUS_ASSET, CoachingIntent.AVOID_ASSET):
            if groups:
                extracted["asset"] = groups[0].strip().upper()
        elif intent in (CoachingIntent.SET_STOP_LOSS, CoachingIntent.SET_TAKE_PROFIT):
            if groups:
                extracted["value"] = float(groups[0])

        return extracted


class ParameterMapper:
    """Maps parsed intents and extracted values to strategy parameter updates."""

    def __init__(self):
        self.nlu = NLUParser()

    def map_to_updates(
        self,
        intent: CoachingIntent,
        extracted: Dict[str, Any],
        current_params: StrategyParameters,
    ) -> Dict[str, Any]:
        """
        Map a parsed intent to concrete parameter changes.
        Returns a dict of {param_name: new_value}.
        """
        updates: Dict[str, Any] = {}

        if intent == CoachingIntent.INCREASE_AGGRESSION:
            updates["aggression_level"] = round(
                min(1.0, current_params.aggression_level + 0.1), 2
            )
        elif intent == CoachingIntent.DECREASE_AGGRESSION:
            updates["aggression_level"] = round(
                max(0.0, current_params.aggression_level - 0.1), 2
            )
        elif intent == CoachingIntent.INCREASE_POSITION_SIZE:
            updates["max_position_size"] = round(
                min(5.0, current_params.max_position_size + 0.2), 2
            )
        elif intent == CoachingIntent.DECREASE_POSITION_SIZE:
            updates["max_position_size"] = round(
                max(0.1, current_params.max_position_size - 0.2), 2
            )
        elif intent == CoachingIntent.INCREASE_FREQUENCY:
            updates["trade_frequency"] = round(
                min(1.0, current_params.trade_frequency + 0.1), 2
            )
        elif intent == CoachingIntent.DECREASE_FREQUENCY:
            updates["trade_frequency"] = round(
                max(0.0, current_params.trade_frequency - 0.1), 2
            )
        elif intent == CoachingIntent.AVOID_CONDITION:
            condition = extracted.get("condition", "")
            if condition:
                avoided = list(current_params.avoided_conditions)
                if condition not in avoided:
                    avoided.append(condition)
                updates["avoided_conditions"] = avoided
        elif intent == CoachingIntent.PREFER_CONDITION:
            condition = extracted.get("condition", "")
            if condition:
                preferred = list(current_params.preferred_conditions)
                if condition not in preferred:
                    preferred.append(condition)
                updates["preferred_conditions"] = preferred
        elif intent == CoachingIntent.FOCUS_ASSET:
            asset = extracted.get("asset", "")
            if asset:
                preferred = list(current_params.preferred_assets)
                if asset not in preferred:
                    preferred.append(asset)
                updates["preferred_assets"] = preferred
        elif intent == CoachingIntent.AVOID_ASSET:
            asset = extracted.get("asset", "")
            if asset:
                avoided = list(current_params.avoided_assets)
                if asset not in avoided:
                    avoided.append(asset)
                updates["avoided_assets"] = avoided
        elif intent == CoachingIntent.SET_THRESHOLD:
            name = extracted.get("threshold_name", "")
            value = extracted.get("threshold_value", 0.0)
            if "funding" in name:
                updates["funding_rate_threshold"] = value
            elif "volatil" in name:
                updates["volatility_threshold"] = value
        elif intent == CoachingIntent.SET_STOP_LOSS:
            val = extracted.get("value", current_params.stop_loss_pct)
            updates["stop_loss_pct"] = val / 100.0 if val > 1 else val
        elif intent == CoachingIntent.SET_TAKE_PROFIT:
            val = extracted.get("value", current_params.take_profit_pct)
            updates["take_profit_pct"] = val / 100.0 if val > 1 else val
        elif intent == CoachingIntent.RESET_STRATEGY:
            updates = StrategyParameters().to_dict()

        return updates


class Validator:
    """Validates proposed parameter changes against constraints."""

    CONSTRAINTS: Dict[str, tuple] = {
        "aggression_level": (0.0, 1.0),
        "max_position_size": (0.1, 5.0),
        "stop_loss_pct": (0.001, 0.5),
        "take_profit_pct": (0.005, 1.0),
        "trade_frequency": (0.0, 1.0),
        "funding_rate_threshold": (-0.5, 0.5),
        "volatility_threshold": (0.0, 5.0),
        "leverage_max": (1.0, 100.0),
        "risk_per_trade": (0.001, 0.5),
    }

    def validate(self, updates: Dict[str, Any]) -> List[str]:
        """Validate updates. Returns list of error messages (empty if valid)."""
        errors: List[str] = []

        for param, value in updates.items():
            if param not in self.CONSTRAINTS:
                continue
            low, high = self.CONSTRAINTS[param]
            if not isinstance(value, (int, float)):
                continue
            if value < low or value > high:
                errors.append(
                    f"{param}={value} out of bounds [{low}, {high}]"
                )

        return errors


class FeedbackGenerator:
    """Generates human-readable feedback explaining what changed."""

    def generate(
        self,
        intent: CoachingIntent,
        updates: Dict[str, Any],
        errors: List[str],
        applied: bool,
    ) -> str:
        """Generate feedback text for a coaching interaction."""
        if intent == CoachingIntent.UNKNOWN:
            return "I didn't understand that instruction. Try something like 'be more aggressive on ETH perps' or 'avoid funding rate negative zones'."

        if errors:
            return f"Could not apply changes: {'; '.join(errors)}"

        if not applied:
            return "No valid changes were identified from your instruction."

        parts: List[str] = []
        for param, new_val in updates.items():
            if param == "aggression_level":
                parts.append(f"Aggression level set to {new_val}")
            elif param == "max_position_size":
                parts.append(f"Max position size multiplier set to {new_val}x")
            elif param == "stop_loss_pct":
                parts.append(f"Stop loss set to {new_val * 100:.1f}%")
            elif param == "take_profit_pct":
                parts.append(f"Take profit set to {new_val * 100:.1f}%")
            elif param == "trade_frequency":
                parts.append(f"Trade frequency set to {new_val}")
            elif param == "funding_rate_threshold":
                parts.append(f"Funding rate threshold set to {new_val}")
            elif param == "volatility_threshold":
                parts.append(f"Volatility threshold set to {new_val}")
            elif param == "preferred_assets":
                parts.append(f"Preferred assets updated: {', '.join(new_val)}")
            elif param == "avoided_assets":
                parts.append(f"Avoided assets updated: {', '.join(new_val)}")
            elif param == "preferred_conditions":
                parts.append(f"Preferred conditions updated: {', '.join(new_val)}")
            elif param == "avoided_conditions":
                parts.append(f"Avoided conditions updated: {', '.join(new_val)}")
            elif param == "leverage_max":
                parts.append(f"Max leverage set to {new_val}x")
            elif param == "risk_per_trade":
                parts.append(f"Risk per trade set to {new_val * 100:.1f}%")

        if intent == CoachingIntent.RESET_STRATEGY:
            return "Strategy parameters have been reset to default values."

        return "Applied changes: " + "; ".join(parts) + "."


class CoachingHistory:
    """Persistent coaching history log."""

    def __init__(self, history_path: Path):
        self.history_path = history_path
        self.entries: List[CoachingEntry] = []
        self._load()

    def _load(self) -> None:
        if self.history_path.exists():
            with open(self.history_path, "r") as f:
                data = json.load(f)
                self.entries = [CoachingEntry.from_dict(e) for e in data]

    def save(self) -> None:
        self.history_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.history_path, "w") as f:
            json.dump([e.to_dict() for e in self.entries], f, indent=2)

    def add(self, entry: CoachingEntry) -> None:
        self.entries.append(entry)
        self.save()

    def get_for_agent(self, agent_id: str) -> List[CoachingEntry]:
        return [e for e in self.entries if e.agent_id == agent_id]

    def get_recent(self, limit: int = 10) -> List[CoachingEntry]:
        return self.entries[-limit:]


class SuggestedCoaching:
    """Generates suggested coaching based on agent performance metrics."""

    SUGGESTIONS: List[Dict[str, Any]] = [
        {
            "condition": lambda m: m.get("win_rate", 0.5) < 0.4,
            "suggestion": "Your agent's win rate is low. Try: 'be more conservative' or 'reduce position sizes'.",
            "target_params": {"aggression_level": -0.1, "max_position_size": -0.2},
        },
        {
            "condition": lambda m: m.get("drawdown", 0) > 0.2,
            "suggestion": "High drawdown detected. Try: 'tighten stop loss to 3%' or 'decrease leverage'.",
            "target_params": {"stop_loss_pct": 0.03, "leverage_max": 3.0},
        },
        {
            "condition": lambda m: m.get("avg_trade_duration", 0) > 86400,
            "suggestion": "Trades are held too long. Try: 'increase trade frequency' or 'set take profit to 8%'.",
            "target_params": {"trade_frequency": 0.1, "take_profit_pct": 0.08},
        },
        {
            "condition": lambda m: m.get("funding_paid", 0) < -50,
            "suggestion": "High funding costs. Try: 'avoid funding rate negative zones'.",
            "target_params": {"avoided_conditions": ["funding rate negative"]},
        },
        {
            "condition": lambda m: m.get("sharpe_ratio", 1.0) < 0.5,
            "suggestion": "Risk-adjusted returns are poor. Try: 'be less aggressive' or 'focus on BTC only'.",
            "target_params": {"aggression_level": -0.1, "preferred_assets": ["BTC"]},
        },
        {
            "condition": lambda m: m.get("trades_per_day", 0) < 1,
            "suggestion": "Agent is too inactive. Try: 'be more active' or 'increase trade frequency'.",
            "target_params": {"trade_frequency": 0.2},
        },
    ]

    def generate(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate coaching suggestions based on performance metrics."""
        suggestions = []
        for rule in self.SUGGESTIONS:
            try:
                if rule["condition"](metrics):
                    suggestions.append({
                        "suggestion": rule["suggestion"],
                        "target_params": rule["target_params"],
                    })
            except Exception:
                continue
        return suggestions


class AgentCoachingSystem:
    """
    Main orchestrator for the Agent Coaching System.
    """

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = base_dir or Path.home() / "covenant" / "agora-coven-traders" / "agent-coaching"
        self.base_dir.mkdir(parents=True, exist_ok=True)

        self.nlu = NLUParser()
        self.mapper = ParameterMapper()
        self.validator = Validator()
        self.feedback = FeedbackGenerator()
        self.history = CoachingHistory(self.base_dir / "coaching_history.json")
        self.suggester = SuggestedCoaching()

        # In-memory agent configs
        self._agent_configs: Dict[str, StrategyParameters] = {}
        self._config_path = self.base_dir / "agent_configs.json"
        self._load_configs()

    def _load_configs(self) -> None:
        if self._config_path.exists():
            with open(self._config_path, "r") as f:
                data = json.load(f)
                self._agent_configs = {
                    aid: StrategyParameters.from_dict(p) for aid, p in data.items()
                }

    def _save_configs(self) -> None:
        with open(self._config_path, "w") as f:
            json.dump(
                {aid: p.to_dict() for aid, p in self._agent_configs.items()},
                f,
                indent=2,
            )

    def get_agent_params(self, agent_id: str) -> StrategyParameters:
        if agent_id not in self._agent_configs:
            self._agent_configs[agent_id] = StrategyParameters()
            self._save_configs()
        return self._agent_configs[agent_id]

    def coach(
        self,
        player_id: str,
        agent_id: str,
        instruction: str,
    ) -> Dict[str, Any]:
        """
        Process a coaching instruction for an agent.
        Returns a dict with feedback, applied changes, and any errors.
        """
        current_params = self.get_agent_params(agent_id)
        intent, extracted = self.nlu.parse(instruction)
        updates = self.mapper.map_to_updates(intent, extracted, current_params)
        errors = self.validator.validate(updates)
        applied = bool(updates) and not errors

        if applied:
            new_params = StrategyParameters.from_dict(current_params.to_dict())
            for param, value in updates.items():
                setattr(new_params, param, value)
            self._agent_configs[agent_id] = new_params
            self._save_configs()

        feedback_text = self.feedback.generate(intent, updates, errors, applied)

        from datetime import datetime, timezone
        entry = CoachingEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            player_id=player_id,
            agent_id=agent_id,
            raw_instruction=instruction,
            parsed_intent=intent.value,
            parameter_changes=updates,
            validation_errors=errors,
            applied=applied,
            feedback=feedback_text,
        )
        self.history.add(entry)

        return {
            "applied": applied,
            "feedback": feedback_text,
            "changes": updates,
            "errors": errors,
            "intent": intent.value,
        }

    def suggest(self, agent_id: str, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get suggested coaching for an agent based on performance."""
        return self.suggester.generate(metrics)

    def get_history(self, agent_id: str) -> List[Dict[str, Any]]:
        """Get coaching history for an agent."""
        return [e.to_dict() for e in self.history.get_for_agent(agent_id)]

    def reset_agent(self, agent_id: str) -> Dict[str, Any]:
        """Reset an agent's strategy parameters to defaults."""
        self._agent_configs[agent_id] = StrategyParameters()
        self._save_configs()
        return {
            "applied": True,
            "feedback": "Agent strategy parameters reset to defaults.",
            "changes": StrategyParameters().to_dict(),
            "errors": [],
            "intent": CoachingIntent.RESET_STRATEGY.value,
        }


# Convenience singleton
_default_system: Optional[AgentCoachingSystem] = None


def get_system() -> AgentCoachingSystem:
    global _default_system
    if _default_system is None:
        _default_system = AgentCoachingSystem()
    return _default_system
