from dataclasses import dataclass
from agents.config import AgentGoal, PriorityLevel


@dataclass
class PlayerDecision:
    agent_id: str
    goal: AgentGoal
    priority: PriorityLevel
