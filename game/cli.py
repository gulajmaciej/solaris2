import re
from typing import Type, TypeVar

from agents.catalog import get_agent_spec
from agents.config import AgentGoal, PriorityLevel, AgentRegistry
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
    agent = event.get("agent", "agent")
    node = event.get("node", "node")
    event_type = event.get("event", "event")
    data = event.get("data") or {}

    label = agent.replace("_", " ").upper()
    color = {
        "INSTRUMENT SPECIALIST": "\x1b[36m",
        "CREW OFFICER": "\x1b[33m",
    }.get(label, "\x1b[37m")
    reset = "\x1b[0m"

    if event_type == "decision":
        tool = data.get("tool") or "none"
        reason = data.get("reason") or "-"
        print(f"{color}[{label}] decide_tool -> {tool} ({reason}){reset}")
        return

    if event_type == "tool_call":
        tool = data.get("tool") or "unknown"
        print(f"{color}[{label}] apply_tool -> {tool} ...{reset}")
        return

    if event_type == "tool_result":
        tool = data.get("tool") or "unknown"
        print(f"{color}[{label}] apply_tool -> {tool} OK{reset}")
        return

    if event_type == "node_end" and node == "observe":
        observation = data.get("observation")
        if observation:
            def _fmt(match: re.Match) -> str:
                try:
                    value = float(match.group(0))
                except ValueError:
                    return match.group(0)
                return f"{value:.4f}"

            formatted = re.sub(r"\d+\.\d+", _fmt, observation)
            print(f"{color}[{label}] observe -> {formatted}{reset}")
        return
