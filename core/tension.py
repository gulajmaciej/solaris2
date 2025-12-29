from typing import Dict
from agents.config import AgentRegistry
from core.conflicts import conflict_strength


DECAY = 0.9          # memory of the system
DRIFT_RATE = 0.03    # how fast agents drift under tension


def priority_factor(p_a: int, p_b: int) -> float:
    if p_a == p_b:
        return 1.0
    if abs(p_a - p_b) == 1:
        return 1.05
    return 1.1


def compute_delta_tension(registry: AgentRegistry) -> float:
    """
    Compute delta tension for current turn based on agent configs and drift.
    """
    agent_ids = list(registry.configs.keys())
    delta = 0.0

    for i in range(len(agent_ids)):
        for j in range(i + 1, len(agent_ids)):
            a = agent_ids[i]
            b = agent_ids[j]

            cfg_a = registry.get_config(a)
            cfg_b = registry.get_config(b)

            rt_a = registry.get_runtime(a)
            rt_b = registry.get_runtime(b)

            base = conflict_strength(cfg_a.goal, cfg_b.goal) / 3.0
            if base == 0:
                continue

            pf = priority_factor(cfg_a.priority.value, cfg_b.priority.value)
            autonomy = 1.0 + (rt_a.drift + rt_b.drift) / 2.0

            delta += base * pf * autonomy

    return delta


def update_tension_and_drift(
    *,
    registry: AgentRegistry,
    current_tension: float,
) -> float:
    """
    Update system tension and agent drift.
    """
    delta = compute_delta_tension(registry)

    next_tension = max(
        0.0,
        min(1.0, current_tension * DECAY + delta),
    )

    # apply drift to agents
    for agent_id in registry.runtime:
        registry.runtime[agent_id].drift = min(
            1.0,
            registry.runtime[agent_id].drift + next_tension * DRIFT_RATE,
        )

    return next_tension
