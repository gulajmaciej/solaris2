from typing import Optional

from agents.config import AgentGoal, PriorityLevel, AgentRegistry
from game.decision import PlayerDecision


GOAL_DESCRIPTIONS = {
    AgentGoal.MAXIMIZE_ANOMALY_DETECTION: "↑ knowledge, ↑ ocean instability",
    AgentGoal.STABILIZE_MEASUREMENT_BASELINES: "↓ noise, ↓ anomaly visibility",
    AgentGoal.REDUCE_DATA_UNCERTAINTY: "↑ confidence, ↑ blind spots",
    AgentGoal.MINIMIZE_CREW_STRESS: "↓ stress, ↓ information flow",
    AgentGoal.MAINTAIN_OPERATIONAL_EFFICIENCY: "↑ predictability, ↓ exploration",
    AgentGoal.PRESERVE_CREW_COHESION: "↑ morale, ↑ conformity",
}


def _choose_enum(enum_cls, current_value):
    print("[x] keep current")
    for i, e in enumerate(enum_cls):
        print(f"[{i}] {e.name.replace('_', ' ').title()}")
        if e in GOAL_DESCRIPTIONS:
            print(f"    {GOAL_DESCRIPTIONS[e]}")

    choice = input("> ").strip()
    if choice.lower() == "x" or choice == "":
        return current_value

    idx = int(choice)
    return list(enum_cls)[idx]


def prompt_decision(
    *,
    agent_id: str,
    registry: AgentRegistry,
) -> Optional[PlayerDecision]:
    cfg = registry.get_config(agent_id)
    rt = registry.get_runtime(agent_id)

    print(f"\nAgent: {agent_id}")
    print(f"Current goal: {cfg.goal.name.replace('_', ' ').title()}")
    print(f"Current priority: {cfg.priority.name}")
    print(f"Drift: {rt.drift:.3f}")

    print("\nChoose new goal:")
    new_goal = _choose_enum(AgentGoal, cfg.goal)

    print("\nChoose new priority:")
    new_priority = _choose_enum(PriorityLevel, cfg.priority)

    if new_goal == cfg.goal and new_priority == cfg.priority:
        return None

    return PlayerDecision(
        agent_id=agent_id,
        goal=new_goal,
        priority=new_priority,
    )
