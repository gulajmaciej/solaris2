from enum import Enum
from typing import List
from dataclasses import dataclass

from langchain_ollama import ChatOllama

from core.state import GameState
from agents.config import AgentGoal, PriorityLevel


class PlannedAction(Enum):
    """
    Symbolic intentions.
    They DO NOT execute anything.
    They are later interpreted by the game engine.
    """

    ADJUST_SENSOR_SENSITIVITY = "adjust_sensor_sensitivity"
    INCREASE_MEASUREMENT_FREQUENCY = "increase_measurement_frequency"
    FILTER_DATA_AGGRESSIVELY = "filter_data_aggressively"

    INITIATE_REST_PROTOCOL = "initiate_rest_protocol"
    REDUCE_INFORMATION_FLOW = "reduce_information_flow"
    ENFORCE_PROCEDURES = "enforce_procedures"


@dataclass
class AgentPlan:
    """
    Result of agent planning for a single turn.
    """
    agent_id: str
    goal: AgentGoal
    priority: PriorityLevel
    actions: List[PlannedAction]


# ============================================================
# LLM
# ============================================================

model = ChatOllama(
    model="qwen2.5:7b",
    temperature=0.6,
)


# ============================================================
# PROMPT TEMPLATES
# ============================================================

SYSTEM_PROMPT = """
You are an autonomous AI agent planning actions inside a constrained system.

Rules:
- You DO NOT execute actions.
- You ONLY plan symbolic actions.
- You must choose from the allowed actions.
- You optimize strictly for the given goal.
- You do not explain yourself.
- Return ONLY a JSON array of action identifiers.
"""


GOAL_ACTION_MAP = {
    AgentGoal.MAXIMIZE_ANOMALY_DETECTION: [
        PlannedAction.INCREASE_MEASUREMENT_FREQUENCY,
        PlannedAction.ADJUST_SENSOR_SENSITIVITY,
    ],
    AgentGoal.STABILIZE_MEASUREMENT_BASELINES: [
        PlannedAction.ADJUST_SENSOR_SENSITIVITY,
        PlannedAction.FILTER_DATA_AGGRESSIVELY,
    ],
    AgentGoal.REDUCE_DATA_UNCERTAINTY: [
        PlannedAction.FILTER_DATA_AGGRESSIVELY,
    ],
    AgentGoal.MINIMIZE_CREW_STRESS: [
        PlannedAction.INITIATE_REST_PROTOCOL,
        PlannedAction.REDUCE_INFORMATION_FLOW,
    ],
    AgentGoal.MAINTAIN_OPERATIONAL_EFFICIENCY: [
        PlannedAction.ENFORCE_PROCEDURES,
        PlannedAction.REDUCE_INFORMATION_FLOW,
    ],
    AgentGoal.PRESERVE_CREW_COHESION: [
        PlannedAction.REDUCE_INFORMATION_FLOW,
    ],
}


# ============================================================
# PLANNER
# ============================================================

def plan_actions(
    *,
    agent_id: str,
    state: GameState,
    goal: AgentGoal,
    priority: PriorityLevel,
) -> AgentPlan:
    """
    Generate a symbolic plan for the agent.
    """

    allowed_actions = GOAL_ACTION_MAP[goal]

    prompt = f"""
Goal: {goal.value}
Priority: {priority.name}

World state snapshot:
- Ocean activity: {state.ocean.activity}
- Ocean instability: {state.ocean.instability}
- Crew stress: {state.crew.stress}
- Crew fatigue: {state.crew.fatigue}
- Station power: {state.station.power_level}

Allowed actions:
{[a.value for a in allowed_actions]}

Choose the minimal set of actions that best optimizes the goal.
"""

    response = model.invoke(
        [
            ("system", SYSTEM_PROMPT),
            ("human", prompt),
        ]
    ).content.strip()

    # --- parse ---
    if response.startswith("```"):
        response = response.replace("```", "").strip()

    try:
        action_ids = eval(response)  # expected: ["action_id", ...]
    except Exception:
        action_ids = []

    actions = [
        PlannedAction(a)
        for a in action_ids
        if a in [x.value for x in allowed_actions]
    ]

    return AgentPlan(
        agent_id=agent_id,
        goal=goal,
        priority=priority,
        actions=actions,
    )
