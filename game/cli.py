from typing import Type, TypeVar

from agents.catalog import get_agent_spec
from agents.config import AgentGoal, PriorityLevel, AgentRegistry
from game.agent_events import format_agent_event
from game.decision import PlayerDecision

T = TypeVar("T")

def _choose_enum(
    enum_cls: Type[T],
    current: T,
    *,
    allowed: set[T] | None = None,
    label: str = "value",
) -> T:
    values = list(enum_cls)
    if allowed is not None:
        values = [v for v in values if v in allowed]

    while True:
        print(f"\nChoose {label} (press ENTER or '-' to keep current):")
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
    allowed_goals = get_agent_spec(agent_id).allowed_goals

    print(f"\n--- Decision for agent: {agent_id} ---")

    new_goal = _choose_enum(
        AgentGoal,
        cfg.goal,
        allowed=allowed_goals,
        label="goal",
    )
    new_priority = _choose_enum(
        PriorityLevel,
        cfg.priority,
        label="priority",
    )

    return PlayerDecision(
        agent_id=agent_id,
        goal=new_goal,
        priority=new_priority,
    )


def render_agent_event(event: dict) -> None:
    formatted = format_agent_event(event)
    if not formatted:
        return

    label, message = formatted
    color = {
        "INSTRUMENT SPECIALIST": "\x1b[36m",
        "CREW OFFICER": "\x1b[33m",
    }.get(label, "\x1b[37m")
    reset = "\x1b[0m"

    print(f"{color}{message}{reset}")
