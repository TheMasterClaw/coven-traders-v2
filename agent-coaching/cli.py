#!/usr/bin/env python3
"""
CLI interface for the Agent Coaching System.
Usage:
    python cli.py coach <player_id> <agent_id> "be more aggressive on ETH perps"
    python cli.py suggest <agent_id> --win-rate 0.35 --drawdown 0.25
    python cli.py history <agent_id>
    python cli.py reset <agent_id>
"""

import argparse
import json
import sys
from typing import Any, Dict

from coaching_engine import AgentCoachingSystem, get_system


def cmd_coach(args: argparse.Namespace) -> None:
    system = get_system()
    result = system.coach(args.player_id, args.agent_id, args.instruction)
    print(json.dumps(result, indent=2))


def cmd_suggest(args: argparse.Namespace) -> None:
    system = get_system()
    metrics: Dict[str, Any] = {}
    if args.win_rate is not None:
        metrics["win_rate"] = args.win_rate
    if args.drawdown is not None:
        metrics["drawdown"] = args.drawdown
    if args.avg_trade_duration is not None:
        metrics["avg_trade_duration"] = args.avg_trade_duration
    if args.funding_paid is not None:
        metrics["funding_paid"] = args.funding_paid
    if args.sharpe_ratio is not None:
        metrics["sharpe_ratio"] = args.sharpe_ratio
    if args.trades_per_day is not None:
        metrics["trades_per_day"] = args.trades_per_day

    suggestions = system.suggest(args.agent_id, metrics)
    print(json.dumps(suggestions, indent=2))


def cmd_history(args: argparse.Namespace) -> None:
    system = get_system()
    hist = system.get_history(args.agent_id)
    print(json.dumps(hist, indent=2))


def cmd_reset(args: argparse.Namespace) -> None:
    system = get_system()
    result = system.reset_agent(args.agent_id)
    print(json.dumps(result, indent=2))


def main() -> int:
    parser = argparse.ArgumentParser(description="Agent Coaching System CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    coach_parser = subparsers.add_parser("coach", help="Send a coaching instruction")
    coach_parser.add_argument("player_id")
    coach_parser.add_argument("agent_id")
    coach_parser.add_argument("instruction")
    coach_parser.set_defaults(func=cmd_coach)

    suggest_parser = subparsers.add_parser("suggest", help="Get coaching suggestions")
    suggest_parser.add_argument("agent_id")
    suggest_parser.add_argument("--win-rate", type=float)
    suggest_parser.add_argument("--drawdown", type=float)
    suggest_parser.add_argument("--avg-trade-duration", type=float)
    suggest_parser.add_argument("--funding-paid", type=float)
    suggest_parser.add_argument("--sharpe-ratio", type=float)
    suggest_parser.add_argument("--trades-per-day", type=float)
    suggest_parser.set_defaults(func=cmd_suggest)

    history_parser = subparsers.add_parser("history", help="Get coaching history")
    history_parser.add_argument("agent_id")
    history_parser.set_defaults(func=cmd_history)

    reset_parser = subparsers.add_parser("reset", help="Reset agent strategy")
    reset_parser.add_argument("agent_id")
    reset_parser.set_defaults(func=cmd_reset)

    args = parser.parse_args()
    args.func(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
