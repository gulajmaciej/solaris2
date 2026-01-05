import re
from typing import Optional, Tuple


def format_agent_event(event: dict) -> Optional[Tuple[str, str]]:
    agent = event.get("agent", "agent")
    node = event.get("node", "node")
    event_type = event.get("event", "event")
    data = event.get("data") or {}

    label = agent.replace("_", " ").upper()

    if event_type == "decision":
        tool = data.get("tool") or "none"
        reason = data.get("reason") or "-"
        return label, f"[{label}] decide_tool -> {tool} ({reason})"

    if event_type == "tool_call":
        tool = data.get("tool") or "unknown"
        return label, f"[{label}] apply_tool -> {tool} ..."

    if event_type == "tool_result":
        tool = data.get("tool") or "unknown"
        return label, f"[{label}] apply_tool -> {tool} OK"

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
            return label, f"[{label}] observe -> {formatted}"

    return None
