Agent Coaching System
=====================

Natural language interface for players to instruct their AI disciple agents in
Coven Traders — a sci-fi idle RPG.

Features
--------
- Parse coaching instructions ("be more aggressive on ETH perps")
- Map instructions to strategy parameter updates
- Validate changes against constraints
- Apply updates to agent configs with persistent storage
- Generate human-readable feedback explaining what changed
- Coaching history log (JSON-backed)
- Suggested coaching based on agent performance metrics
- LLM-powered NLU (OpenAI-compatible) with rule-based fallback
- FastAPI HTTP interface
- CLI interface

Project Structure
-----------------
```
agent-coaching/
  coaching_engine.py   Core engine: NLU, mapping, validation, feedback, history
  llm_nlu.py           LLM-powered parser with hybrid fallback
  api.py               FastAPI HTTP endpoints
  cli.py               Command-line interface
  test_coaching.py     Unit tests
  README.md            This file
```

Quick Start
-----------

### Python API
```python
from coaching_engine import AgentCoachingSystem

system = AgentCoachingSystem()
result = system.coach("player_1", "agent_alpha", "be more aggressive on ETH perps")
print(result["feedback"])
```

### CLI
```bash
python cli.py coach player_1 agent_alpha "be more aggressive on ETH perps"
python cli.py suggest agent_alpha --win-rate 0.35 --drawdown 0.25
python cli.py history agent_alpha
python cli.py reset agent_alpha
```

### HTTP API
```bash
uvicorn api:app --host 0.0.0.0 --port 8000

curl -X POST http://localhost:8000/coach \
  -H "Content-Type: application/json" \
  -d '{"player_id":"p1","agent_id":"a1","instruction":"avoid funding rate negative zones"}'

curl "http://localhost:8000/history/a1"
```

### Environment Variables
```bash
export OPENAI_API_KEY="sk-..."
export OPENAI_BASE_URL="https://api.openai.com/v1"  # optional
export COACHING_LLM_MODEL="gpt-4o-mini"             # optional
```

Running Tests
-------------
```bash
python -m pytest test_coaching.py -v
```

Strategy Parameters
-------------------
| Parameter               | Type   | Default | Range       |
|-------------------------|--------|---------|-------------|
| aggression_level        | float  | 0.5     | 0.0 - 1.0   |
| max_position_size       | float  | 1.0     | 0.1 - 5.0   |
| stop_loss_pct           | float  | 0.05    | 0.001 - 0.5 |
| take_profit_pct         | float  | 0.10    | 0.005 - 1.0 |
| trade_frequency         | float  | 0.5     | 0.0 - 1.0   |
| preferred_assets        | list   | []      | e.g. ["ETH"]|
| avoided_assets          | list   | []      | e.g. ["DOGE"]|
| avoided_conditions      | list   | []      | e.g. ["funding rate negative"]|
| preferred_conditions    | list   | []      |             |
| funding_rate_threshold  | float  | -0.01   | -0.5 - 0.5  |
| volatility_threshold    | float  | 0.5     | 0.0 - 5.0   |
| leverage_max            | float  | 5.0     | 1.0 - 100.0 |
| risk_per_trade          | float  | 0.02    | 0.001 - 0.5 |

Supported Instructions
----------------------
- "be more aggressive" / "play safe"
- "avoid funding rate negative zones"
- "focus on ETH"
- "set stop loss to 3%"
- "set take profit to 10%"
- "increase position sizes"
- "trade more often"
- "reset strategy"

License
-------
MIT
