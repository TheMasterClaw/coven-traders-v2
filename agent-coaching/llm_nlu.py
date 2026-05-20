"""
LLM-powered NLU module for the Agent Coaching System.
Uses OpenAI API (or compatible) to parse complex natural language instructions
into structured coaching intents and parameters.
"""

import json
import os
from typing import Dict, Any, Optional


def get_llm_client():
    """Get an LLM client. Tries openai, then falls back to ollama."""
    try:
        import openai
        api_key = os.environ.get("OPENAI_API_KEY")
        base_url = os.environ.get("OPENAI_BASE_URL")
        if api_key:
            client = openai.OpenAI(api_key=api_key, base_url=base_url)
            return client
    except ImportError:
        pass
    return None


SYSTEM_PROMPT = """You are the NLU engine for an Agent Coaching System in a sci-fi idle RPG called Coven Traders.
Players give natural language instructions to their AI disciple agents.

Your job is to parse the player's instruction into a structured JSON object with these fields:
- "intent": one of [
    "increase_aggression", "decrease_aggression",
    "avoid_condition", "prefer_condition",
    "set_threshold", "increase_position_size", "decrease_position_size",
    "focus_asset", "avoid_asset", "increase_frequency", "decrease_frequency",
    "set_stop_loss", "set_take_profit", "reset_strategy", "unknown"
  ]
- "parameters": a dict of parameter changes inferred from the instruction.
  Recognized parameters:
    - aggression_level (float 0.0-1.0)
    - max_position_size (float, multiplier)
    - stop_loss_pct (float, e.g. 0.05 for 5%)
    - take_profit_pct (float, e.g. 0.10 for 10%)
    - trade_frequency (float 0.0-1.0)
    - preferred_assets (list of strings, e.g. ["ETH", "BTC"])
    - avoided_assets (list of strings)
    - avoided_conditions (list of strings, e.g. ["funding rate negative"])
    - preferred_conditions (list of strings)
    - funding_rate_threshold (float)
    - volatility_threshold (float)
    - leverage_max (float)
    - risk_per_trade (float)
- "confidence": float 0.0-1.0 indicating how sure you are
- "explanation": brief explanation of what the player wants

Rules:
- If the instruction is vague or unrelated, use intent "unknown" and empty parameters.
- Convert percentages to decimals (e.g. 5% -> 0.05).
- Asset names should be uppercase.
- Only include parameters that are explicitly mentioned or strongly implied.
- Return ONLY valid JSON. No markdown, no extra text.
"""


def parse_with_llm(instruction: str, model: Optional[str] = None) -> Dict[str, Any]:
    """
    Parse a coaching instruction using an LLM.
    Returns a dict with intent, parameters, confidence, and explanation.
    Falls back to rule-based parsing if no LLM client is available.
    """
    client = get_llm_client()
    if client is None:
        # Fallback: return unknown so caller can use rule-based parser
        return {
            "intent": "unknown",
            "parameters": {},
            "confidence": 0.0,
            "explanation": "No LLM client available.",
        }

    model = model or os.environ.get("COACHING_LLM_MODEL", "gpt-4o-mini")

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": instruction},
            ],
            temperature=0.0,
            max_tokens=512,
        )
        content = response.choices[0].message.content or "{}"
        # Strip markdown code fences if present
        content = content.strip()
        if content.startswith("```"):
            lines = content.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            content = "\n".join(lines)
        parsed = json.loads(content)
        return parsed
    except Exception as e:
        return {
            "intent": "unknown",
            "parameters": {},
            "confidence": 0.0,
            "explanation": f"LLM parsing failed: {e}",
        }


def hybrid_parse(instruction: str, model: Optional[str] = None) -> Dict[str, Any]:
    """
    Hybrid parser: try LLM first, fall back to rule-based parser.
    Returns a dict compatible with coaching_engine.py.
    """
    from coaching_engine import NLUParser, CoachingIntent, ParameterMapper, StrategyParameters

    llm_result = parse_with_llm(instruction, model)
    confidence = llm_result.get("confidence", 0.0)

    if confidence >= 0.7:
        intent_str = llm_result.get("intent", "unknown")
        try:
            intent = CoachingIntent(intent_str)
        except ValueError:
            intent = CoachingIntent.UNKNOWN
        parameters = llm_result.get("parameters", {})
        return {
            "intent": intent,
            "parameters": parameters,
            "source": "llm",
            "explanation": llm_result.get("explanation", ""),
        }

    # Fallback to rule-based
    nlu = NLUParser()
    intent, extracted = nlu.parse(instruction)
    return {
        "intent": intent,
        "parameters": extracted,
        "source": "rule",
        "explanation": "",
    }
