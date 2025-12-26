from typing import List
from pydantic import BaseModel

from agents.config import AgentGoal, PriorityLevel


class DecisionIn(BaseModel):
    agent_id: str
    goal: AgentGoal
    priority: PriorityLevel


class TurnRequest(BaseModel):
    decisions: List[DecisionIn]


class AgentReport(BaseModel):
    agent_id: str
    text: str


class TurnResponse(BaseModel):
    turn: int
    tension: float
    earth_pressure: float
    solaris_intensity: float
    reports: List[AgentReport]
