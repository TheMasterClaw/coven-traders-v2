"""
FastAPI HTTP interface for the Agent Coaching System.
Provides endpoints for coaching, suggestions, and history.
"""

from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from coaching_engine import AgentCoachingSystem, CoachingIntent, get_system


app = FastAPI(title="Agent Coaching System", version="1.0.0")


class CoachRequest(BaseModel):
    player_id: str
    agent_id: str
    instruction: str


class CoachResponse(BaseModel):
    applied: bool
    feedback: str
    changes: Dict[str, Any]
    errors: List[str]
    intent: str


class SuggestRequest(BaseModel):
    agent_id: str
    metrics: Dict[str, Any]


class SuggestResponse(BaseModel):
    suggestions: List[Dict[str, Any]]


class HistoryResponse(BaseModel):
    history: List[Dict[str, Any]]


class ResetRequest(BaseModel):
    agent_id: str


def get_coaching_system() -> AgentCoachingSystem:
    return get_system()


@app.post("/coach", response_model=CoachResponse)
async def coach(request: CoachRequest):
    """Process a coaching instruction for an agent."""
    system = get_coaching_system()
    result = system.coach(request.player_id, request.agent_id, request.instruction)
    return CoachResponse(**result)


@app.post("/suggest", response_model=SuggestResponse)
async def suggest(request: SuggestRequest):
    """Get coaching suggestions for an agent based on performance metrics."""
    system = get_coaching_system()
    suggestions = system.suggest(request.agent_id, request.metrics)
    return SuggestResponse(suggestions=suggestions)


@app.get("/history/{agent_id}", response_model=HistoryResponse)
async def history(agent_id: str):
    """Get coaching history for an agent."""
    system = get_coaching_system()
    hist = system.get_history(agent_id)
    return HistoryResponse(history=hist)


@app.post("/reset")
async def reset(request: ResetRequest):
    """Reset an agent's strategy parameters to defaults."""
    system = get_coaching_system()
    result = system.reset_agent(request.agent_id)
    return result


@app.get("/health")
async def health():
    return {"status": "ok"}
