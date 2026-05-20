#!/usr/bin/env python3
"""
Unit tests for the Agent Coaching System.
"""

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from coaching_engine import (
    AgentCoachingSystem,
    CoachingEntry,
    CoachingHistory,
    CoachingIntent,
    FeedbackGenerator,
    NLUParser,
    ParameterMapper,
    StrategyParameters,
    SuggestedCoaching,
    Validator,
)


class TestNLUParser(unittest.TestCase):
    def setUp(self):
        self.parser = NLUParser()

    def test_aggression_increase(self):
        intent, extracted = self.parser.parse("be more aggressive")
        self.assertEqual(intent, CoachingIntent.INCREASE_AGGRESSION)

    def test_aggression_decrease(self):
        intent, extracted = self.parser.parse("play safe")
        self.assertEqual(intent, CoachingIntent.DECREASE_AGGRESSION)

    def test_avoid_condition(self):
        intent, extracted = self.parser.parse("avoid funding rate negative zones")
        self.assertEqual(intent, CoachingIntent.AVOID_CONDITION)
        self.assertEqual(extracted.get("condition"), "funding rate negative zone")

    def test_focus_asset(self):
        intent, extracted = self.parser.parse("focus on ETH")
        self.assertEqual(intent, CoachingIntent.FOCUS_ASSET)
        self.assertEqual(extracted.get("asset"), "ETH")

    def test_set_stop_loss(self):
        intent, extracted = self.parser.parse("set stop loss to 3")
        self.assertEqual(intent, CoachingIntent.SET_STOP_LOSS)
        self.assertEqual(extracted.get("value"), 3.0)

    def test_unknown(self):
        intent, extracted = self.parser.parse("make me a sandwich")
        self.assertEqual(intent, CoachingIntent.UNKNOWN)


class TestParameterMapper(unittest.TestCase):
    def setUp(self):
        self.mapper = ParameterMapper()
        self.base = StrategyParameters()

    def test_increase_aggression(self):
        updates = self.mapper.map_to_updates(
            CoachingIntent.INCREASE_AGGRESSION, {}, self.base
        )
        self.assertAlmostEqual(updates["aggression_level"], 0.6)

    def test_decrease_aggression(self):
        updates = self.mapper.map_to_updates(
            CoachingIntent.DECREASE_AGGRESSION, {}, self.base
        )
        self.assertAlmostEqual(updates["aggression_level"], 0.4)

    def test_avoid_condition(self):
        updates = self.mapper.map_to_updates(
            CoachingIntent.AVOID_CONDITION, {"condition": "high volatility"}, self.base
        )
        self.assertIn("high volatility", updates["avoided_conditions"])

    def test_focus_asset(self):
        updates = self.mapper.map_to_updates(
            CoachingIntent.FOCUS_ASSET, {"asset": "BTC"}, self.base
        )
        self.assertIn("BTC", updates["preferred_assets"])

    def test_reset(self):
        updates = self.mapper.map_to_updates(
            CoachingIntent.RESET_STRATEGY, {}, self.base
        )
        self.assertEqual(updates["aggression_level"], 0.5)


class TestValidator(unittest.TestCase):
    def setUp(self):
        self.validator = Validator()

    def test_valid(self):
        errors = self.validator.validate({"aggression_level": 0.7})
        self.assertEqual(errors, [])

    def test_out_of_bounds(self):
        errors = self.validator.validate({"aggression_level": 1.5})
        self.assertTrue(any("out of bounds" in e for e in errors))


class TestFeedbackGenerator(unittest.TestCase):
    def setUp(self):
        self.gen = FeedbackGenerator()

    def test_increase_aggression(self):
        text = self.gen.generate(
            CoachingIntent.INCREASE_AGGRESSION,
            {"aggression_level": 0.7},
            [],
            True,
        )
        self.assertIn("Aggression level set to 0.7", text)

    def test_unknown(self):
        text = self.gen.generate(CoachingIntent.UNKNOWN, {}, [], False)
        self.assertIn("didn't understand", text)

    def test_errors(self):
        text = self.gen.generate(
            CoachingIntent.INCREASE_AGGRESSION,
            {"aggression_level": 1.5},
            ["aggression_level=1.5 out of bounds"],
            False,
        )
        self.assertIn("Could not apply", text)


class TestSuggestedCoaching(unittest.TestCase):
    def setUp(self):
        self.suggester = SuggestedCoaching()

    def test_low_win_rate(self):
        suggestions = self.suggester.generate({"win_rate": 0.3})
        self.assertTrue(any("win rate" in s["suggestion"] for s in suggestions))

    def test_high_drawdown(self):
        suggestions = self.suggester.generate({"drawdown": 0.3})
        self.assertTrue(any("drawdown" in s["suggestion"] for s in suggestions))

    def test_no_suggestions(self):
        suggestions = self.suggester.generate({"win_rate": 0.8, "drawdown": 0.05, "trades_per_day": 5})
        self.assertEqual(suggestions, [])


class TestCoachingHistory(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.history = CoachingHistory(Path(self.tmpdir) / "history.json")

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_add_and_retrieve(self):
        entry = CoachingEntry(
            timestamp="2024-01-01T00:00:00",
            player_id="p1",
            agent_id="a1",
            raw_instruction="test",
            parsed_intent="increase_aggression",
            parameter_changes={},
            validation_errors=[],
            applied=True,
            feedback="ok",
        )
        self.history.add(entry)
        retrieved = self.history.get_for_agent("a1")
        self.assertEqual(len(retrieved), 1)
        self.assertEqual(retrieved[0].feedback, "ok")


class TestAgentCoachingSystem(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.system = AgentCoachingSystem(base_dir=Path(self.tmpdir))

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_coach_increase_aggression(self):
        result = self.system.coach("p1", "a1", "be more aggressive")
        self.assertTrue(result["applied"])
        self.assertIn("Aggression level", result["feedback"])
        params = self.system.get_agent_params("a1")
        self.assertAlmostEqual(params.aggression_level, 0.6)

    def test_coach_avoid_condition(self):
        result = self.system.coach("p1", "a1", "avoid funding rate negative zones")
        self.assertTrue(result["applied"])
        params = self.system.get_agent_params("a1")
        self.assertIn("funding rate negative zone", params.avoided_conditions)

    def test_coach_unknown(self):
        result = self.system.coach("p1", "a1", "make me a sandwich")
        self.assertFalse(result["applied"])
        self.assertIn("didn't understand", result["feedback"])

    def test_suggest(self):
        suggestions = self.system.suggest("a1", {"win_rate": 0.3, "drawdown": 0.3})
        self.assertTrue(len(suggestions) >= 1)

    def test_history(self):
        self.system.coach("p1", "a1", "be more aggressive")
        hist = self.system.get_history("a1")
        self.assertEqual(len(hist), 1)

    def test_reset(self):
        self.system.coach("p1", "a1", "be more aggressive")
        result = self.system.reset_agent("a1")
        self.assertTrue(result["applied"])
        params = self.system.get_agent_params("a1")
        self.assertAlmostEqual(params.aggression_level, 0.5)


if __name__ == "__main__":
    unittest.main()
