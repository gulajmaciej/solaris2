from typing import Type, TypeVar

from agents.config import AgentGoal, PriorityLevel, AgentRegistry
from game.decision import PlayerDecision

T = TypeVar("T")


def _choose_enum(enum_cls: Type[T], current: T) -> T:
    values = list(enum_cls)

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

    print(f"\n--- Decision for agent: {agent_id} ---")

    new_goal = _choose_enum(AgentGoal, cfg.goal)
    new_priority = _choose_enum(PriorityLevel, cfg.priority)

    return PlayerDecision(
        agent_id=agent_id,
        goal=new_goal,
        priority=new_priority,
    )
