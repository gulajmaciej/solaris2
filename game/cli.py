from typing import Type, TypeVar

from agents.config import AgentGoal, PriorityLevel, AgentRegistry
from game.decision import PlayerDecision

T = TypeVar("T")

ALLOWED_GOALS = {
    "instrument_specialist": {
        AgentGoal.MAXIMIZE_ANOMALY_DETECTION,
        AgentGoal.STABILIZE_MEASUREMENT_BASELINES,
        AgentGoal.REDUCE_DATA_UNCERTAINTY,
    },
    "crew_officer": {
        AgentGoal.MINIMIZE_CREW_STRESS,
        AgentGoal.MAINTAIN_OPERATIONAL_EFFICIENCY,
        AgentGoal.PRESERVE_CREW_COHESION,
    },
}


def _choose_enum(enum_cls: Type[T], current: T, *, allowed: set[T] | None = None) -> T:
    values = list(enum_cls)
    if allowed is not None:
        values = [v for v in values if v in allowed]

    while True:
        print("\nChoose value (press ENTER or '-' to keep current):")
        for i, v in enumerate(values):
            marker = " (current)" if v == current else ""
            print(f"[{i}] {v.name}{marker}")

        choice = input("> ").strip()

        # Keep current value
        if choice == "" or choice == "-":
            return current

        # Try numeric choice
        if choice.isdigit():
            idx = int(choice)
            if 0 <= idx < len(values):
                return values[idx]

        print("Invalid choice. Try again.")


def prompt_decision(agent_id: str, registry: AgentRegistry) -> PlayerDecision:
    cfg = registry.get_config(agent_id)
    allowed_goals = ALLOWED_GOALS.get(agent_id)

    print(f"\n--- Decision for agent: {agent_id} ---")

    new_goal = _choose_enum(AgentGoal, cfg.goal, allowed=allowed_goals)
    new_priority = _choose_enum(PriorityLevel, cfg.priority)

    return PlayerDecision(
        agent_id=agent_id,
        goal=new_goal,
        priority=new_priority,
    )
