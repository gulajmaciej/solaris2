from typing import List

from core.state import GameState
from core.engine import GameEngine
from core.tension import update_tension_and_drift
from core.earth import EarthState, update_earth_pressure

from agents.config import AgentRegistry, AgentGoal
from agents.planner import plan_actions
from game.decision import PlayerDecision
from game.governance import apply_earth_constraints


# --- tension → ocean coupling constants ---
TENSION_INSTABILITY_THRESHOLD = 0.3
TENSION_ACTIVITY_THRESHOLD = 0.6

INSTABILITY_COEFF = 0.04
ACTIVITY_COEFF = 0.02

# --- tension reduction constants ---
TENSION_RELIEF_AMOUNT = 0.05
MIN_TENSION = 0.3

# --- fatigue/stress coupling ---
FATIGUE_STRESS_COEFF = 0.02

# --- stress/ocean feedback into tension ---
STRESS_TENSION_COEFF = 0.017
OCEAN_TENSION_COEFF = 0.045

# --- stress influence on drift ---
STRESS_DRIFT_COEFF = 0.01


def _goals_are_stabilizing(registry: AgentRegistry) -> bool:
    """
    Returns True if agent goals are non-conflicting
    and at least one agent is in stabilization mode.
    """
    goals = [cfg.goal for cfg in registry.configs.values()]

    if len(set(goals)) == 1:
        return True

    stabilizing_goals = {
        AgentGoal.STABILIZE_MEASUREMENT_BASELINES,
        AgentGoal.MINIMIZE_CREW_STRESS,
    }

    return any(goal in stabilizing_goals for goal in goals)


def run_turn(
    *,
    state: GameState,
    registry: AgentRegistry,
    decisions: List[PlayerDecision],
    engine: GameEngine,
    current_tension: float,
    earth: EarthState,
) -> float:
    """
    Execute exactly ONE game turn.
    """

    # reset debug containers
    state.flags["ocean_debug"] = []
    state.flags["tension_debug"] = []
    state.flags["earth_debug"] = []
    state.flags["drift_debug"] = []

    # 0. apply institutional constraints
    constrained_decisions = []
    for d in decisions:
        original_goal = d.goal
        original_priority = d.priority
        constrained_decisions.append(
            apply_earth_constraints(decision=d, earth=earth)
        )
        if d.goal != original_goal or d.priority != original_priority:
            print(
                "[EARTH] Constraints applied to "
                f"{d.agent_id}: goal {original_goal.name} -> {d.goal.name}, "
                f"priority {original_priority.name} -> {d.priority.name}"
            )

    # 1. apply (possibly constrained) player decisions
    for d in constrained_decisions:
        registry.set_goal(d.agent_id, d.goal)
        registry.set_priority(d.agent_id, d.priority)

    # 2. agent planning
    plans = []
    for agent_id in registry.configs:
        cfg = registry.get_config(agent_id)
        plan = plan_actions(
            agent_id=agent_id,
            state=state,
            goal=cfg.goal,
            priority=cfg.priority,
        )
        plans.append(plan)

    # 3. deterministic execution
    engine.execute_plans(state=state, plans=plans)

    # 3.5 fatigue -> stress feedback
    state.crew.stress += state.crew.fatigue * FATIGUE_STRESS_COEFF
    state.crew.stress = max(0.0, min(1.0, state.crew.stress))

    # 4. tension + drift (base increase)
    next_tension = update_tension_and_drift(
        registry=registry,
        current_tension=current_tension,
    )

    # 4.1 stress and ocean feedback into tension
    stress_delta = state.crew.stress * STRESS_TENSION_COEFF
    if stress_delta > 0:
        prev = next_tension
        next_tension = max(0.0, min(1.0, next_tension + stress_delta))
        state.flags["tension_debug"].append(
            {
                "previous": round(prev, 3),
                "next": round(next_tension, 3),
                "delta": round(next_tension - prev, 3),
                "reason": "stress_feedback",
            }
        )

    ocean_delta = (
        (state.ocean.activity + state.ocean.instability) / 2.0
    ) * OCEAN_TENSION_COEFF
    if ocean_delta > 0:
        prev = next_tension
        next_tension = max(0.0, min(1.0, next_tension + ocean_delta))
        state.flags["tension_debug"].append(
            {
                "previous": round(prev, 3),
                "next": round(next_tension, 3),
                "delta": round(next_tension - prev, 3),
                "reason": "ocean_feedback",
            }
        )

    # 4.5 world reaction to tension (OCEAN ESCALATION)
    ocean_escalated = False

    if next_tension > TENSION_INSTABILITY_THRESHOLD:
        delta = (next_tension - TENSION_INSTABILITY_THRESHOLD) * INSTABILITY_COEFF
        state.ocean.instability += delta
        ocean_escalated = True

        state.flags["ocean_debug"].append(
            {
                "parameter": "instability",
                "delta": round(delta, 4),
                "reason": "tension_exceeded_instability_threshold",
                "tension": round(next_tension, 3),
            }
        )

    if next_tension > TENSION_ACTIVITY_THRESHOLD:
        delta = (next_tension - TENSION_ACTIVITY_THRESHOLD) * ACTIVITY_COEFF
        state.ocean.activity += delta
        ocean_escalated = True

        state.flags["ocean_debug"].append(
            {
                "parameter": "activity",
                "delta": round(delta, 4),
                "reason": "tension_exceeded_activity_threshold",
                "tension": round(next_tension, 3),
            }
        )

    # clamp ocean
    state.ocean.activity = max(0.0, min(1.0, state.ocean.activity))
    state.ocean.instability = max(0.0, min(1.0, state.ocean.instability))

    # 4.6 NEGATIVE FEEDBACK: tension relief
    if not ocean_escalated and _goals_are_stabilizing(registry):
        prev = next_tension
        next_tension = max(MIN_TENSION, next_tension - TENSION_RELIEF_AMOUNT)

        state.flags["tension_debug"].append(
            {
                "previous": round(prev, 3),
                "next": round(next_tension, 3),
                "delta": round(next_tension - prev, 3),
                "reason": "stabilization_without_ocean_escalation",
            }
        )
    else:
        state.flags["tension_debug"].append(
            {
                "previous": round(current_tension, 3),
                "next": round(next_tension, 3),
                "delta": round(next_tension - current_tension, 3),
                "reason": "agent_goal_conflicts_and_drift",
            }
        )

    # 4.7 stress -> drift influence
    if state.crew.stress > 0:
        for agent_id in registry.runtime:
            prev = registry.runtime[agent_id].drift
            registry.runtime[agent_id].drift = min(
                1.0,
                registry.runtime[agent_id].drift
                + state.crew.stress * STRESS_DRIFT_COEFF,
            )
            state.flags["drift_debug"].append(
                {
                    "agent_id": agent_id,
                    "previous": round(prev, 3),
                    "next": round(registry.runtime[agent_id].drift, 3),
                    "delta": round(
                        registry.runtime[agent_id].drift - prev,
                        3,
                    ),
                    "reason": "stress_feedback",
                }
            )

    # 5. earth pressure update
    prev_pressure = earth.pressure
    update_earth_pressure(
        earth=earth,
        registry=registry,
        tension=next_tension,
    )

    state.flags["earth_debug"].append(
        {
            "previous": round(prev_pressure, 3),
            "next": round(earth.pressure, 3),
            "delta": round(earth.pressure - prev_pressure, 3),
            "reason": "tension_and_avg_drift",
            "tension": round(next_tension, 3),
        }
    )

    # 6. advance time
    state.next_turn()

    return next_tension
