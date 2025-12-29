import csv
import random
from datetime import datetime, UTC
from pathlib import Path

from agents.config import (
    AgentRegistry,
    AgentGoal,
    PriorityLevel,
)
from agents.catalog import list_agent_specs, get_agent_spec
from agents.planner import AgentPlan, PlannedAction
from core.state import GameState
from core.engine import GameEngine
from core.earth import EarthState, update_earth_pressure
from core.solaris import SolarisState, update_solaris_intensity
from core.tension import update_tension_and_drift, compute_delta_tension
from game.decision import PlayerDecision
from game.endings import check_end_conditions
from game.governance import apply_earth_constraints

# Import constants from turn logic to keep behavior aligned.
from game.turn import (
    TENSION_INSTABILITY_THRESHOLD,
    TENSION_ACTIVITY_THRESHOLD,
    INSTABILITY_COEFF,
    ACTIVITY_COEFF,
    TENSION_RELIEF_AMOUNT,
    MIN_TENSION,
    FATIGUE_STRESS_COEFF,
    STRESS_TENSION_COEFF,
    OCEAN_TENSION_COEFF,
    STRESS_DRIFT_COEFF,
)


def _goals_are_stabilizing(registry: AgentRegistry) -> bool:
    goals = [cfg.goal for cfg in registry.configs.values()]
    if len(set(goals)) == 1:
        return True

    stabilizing_goals = {
        AgentGoal.STABILIZE_MEASUREMENT_BASELINES,
        AgentGoal.MINIMIZE_CREW_STRESS,
    }
    return any(goal in stabilizing_goals for goal in goals)


def choose_decisions(
    state: GameState,
    *,
    randomSelection: bool = False,
) -> list[PlayerDecision]:
    decisions: list[PlayerDecision] = []

    if randomSelection:
        priorities = [
            PriorityLevel.LOW,
            PriorityLevel.MEDIUM,
            PriorityLevel.HIGH,
        ]

        for spec in list_agent_specs():
            decisions.append(
                PlayerDecision(
                    agent_id=spec.agent_id,
                    goal=random.choice(list(spec.allowed_goals)),
                    priority=random.choice(priorities),
                )
            )

        return decisions

    # Instrument specialist decision rules
    if state.ocean.instability > 0.6:
        inst_goal = AgentGoal.STABILIZE_MEASUREMENT_BASELINES
        inst_priority = PriorityLevel.HIGH
    elif state.ocean.activity < 0.3:
        inst_goal = AgentGoal.MAXIMIZE_ANOMALY_DETECTION
        inst_priority = PriorityLevel.MEDIUM
    else:
        inst_goal = AgentGoal.REDUCE_DATA_UNCERTAINTY
        inst_priority = PriorityLevel.MEDIUM

    decisions.append(
        PlayerDecision(
            agent_id="instrument_specialist",
            goal=inst_goal,
            priority=inst_priority,
        )
    )

    # Crew officer decision rules
    if state.crew.stress > 0.5 or state.crew.fatigue > 0.4:
        crew_goal = AgentGoal.MINIMIZE_CREW_STRESS
        crew_priority = PriorityLevel.HIGH
    elif state.station.power_level < 0.4:
        crew_goal = AgentGoal.MAINTAIN_OPERATIONAL_EFFICIENCY
        crew_priority = PriorityLevel.MEDIUM
    else:
        crew_goal = AgentGoal.PRESERVE_CREW_COHESION
        crew_priority = PriorityLevel.LOW

    decisions.append(
        PlayerDecision(
            agent_id="crew_officer",
            goal=crew_goal,
            priority=crew_priority,
        )
    )

    for spec in list_agent_specs():
        if spec.agent_id in {"instrument_specialist", "crew_officer"}:
            continue
        cfg = spec.default_config
        decisions.append(
            PlayerDecision(
                agent_id=spec.agent_id,
                goal=cfg.goal,
                priority=cfg.priority,
            )
        )

    return decisions


def plan_actions_rule(
    *,
    agent_id: str,
    state: GameState,
    goal: AgentGoal,
    priority: PriorityLevel,
) -> AgentPlan:
    if goal == AgentGoal.MAXIMIZE_ANOMALY_DETECTION:
        if state.ocean.activity < 0.5:
            actions = [PlannedAction.INCREASE_MEASUREMENT_FREQUENCY]
        else:
            actions = [PlannedAction.ADJUST_SENSOR_SENSITIVITY]

    elif goal == AgentGoal.STABILIZE_MEASUREMENT_BASELINES:
        if state.ocean.instability > 0.4:
            actions = [PlannedAction.FILTER_DATA_AGGRESSIVELY]
        else:
            actions = [PlannedAction.ADJUST_SENSOR_SENSITIVITY]

    elif goal == AgentGoal.REDUCE_DATA_UNCERTAINTY:
        actions = [PlannedAction.FILTER_DATA_AGGRESSIVELY]

    elif goal == AgentGoal.MINIMIZE_CREW_STRESS:
        if state.crew.stress > 0.4:
            actions = [PlannedAction.INITIATE_REST_PROTOCOL]
        else:
            actions = [PlannedAction.REDUCE_INFORMATION_FLOW]

    elif goal == AgentGoal.MAINTAIN_OPERATIONAL_EFFICIENCY:
        if state.station.power_level < 0.3:
            actions = [PlannedAction.ENFORCE_PROCEDURES]
        else:
            actions = [PlannedAction.REDUCE_INFORMATION_FLOW]

    elif goal == AgentGoal.PRESERVE_CREW_COHESION:
        actions = [PlannedAction.REDUCE_INFORMATION_FLOW]
    else:
        actions = []

    return AgentPlan(
        agent_id=agent_id,
        goal=goal,
        priority=priority,
        actions=actions,
    )


def run_bot_turn(
    *,
    state: GameState,
    registry: AgentRegistry,
    decisions: list[PlayerDecision],
    engine: GameEngine,
    current_tension: float,
    earth: EarthState,
) -> tuple[float, list[AgentPlan], list[PlayerDecision]]:
    # Apply institutional constraints
    constrained_decisions: list[PlayerDecision] = []
    for d in decisions:
        constrained_decisions.append(
            apply_earth_constraints(decision=d, earth=earth)
        )

    # Apply constrained decisions
    for d in constrained_decisions:
        registry.set_goal(d.agent_id, d.goal)
        registry.set_priority(d.agent_id, d.priority)

    # Deterministic planning (no LLM)
    plans: list[AgentPlan] = []
    for agent_id in registry.configs:
        cfg = registry.get_config(agent_id)
        plan = plan_actions_rule(
            agent_id=agent_id,
            state=state,
            goal=cfg.goal,
            priority=cfg.priority,
        )
        plans.append(plan)

    # Deterministic execution
    engine.execute_plans(state=state, plans=plans)

    # Fatigue -> stress
    state.crew.stress += state.crew.fatigue * FATIGUE_STRESS_COEFF
    state.crew.stress = max(0.0, min(1.0, state.crew.stress))

    # Conflict signal before drift update
    conflict_score = compute_delta_tension(registry)

    # Tension + drift (base)
    next_tension = update_tension_and_drift(
        registry=registry,
        current_tension=current_tension,
    )

    # Stress and ocean feedback into tension
    stress_feedback_delta = state.crew.stress * STRESS_TENSION_COEFF
    next_tension = max(
        0.0,
        min(1.0, next_tension + stress_feedback_delta),
    )
    ocean_feedback_delta = (
        (state.ocean.activity + state.ocean.instability) / 2.0
    ) * OCEAN_TENSION_COEFF
    next_tension = max(0.0, min(1.0, next_tension + ocean_feedback_delta))

    # Ocean escalation
    ocean_escalated = False

    if next_tension > TENSION_INSTABILITY_THRESHOLD:
        delta = (next_tension - TENSION_INSTABILITY_THRESHOLD) * INSTABILITY_COEFF
        state.ocean.instability += delta
        ocean_escalated = True

    if next_tension > TENSION_ACTIVITY_THRESHOLD:
        delta = (next_tension - TENSION_ACTIVITY_THRESHOLD) * ACTIVITY_COEFF
        state.ocean.activity += delta
        ocean_escalated = True

    state.ocean.activity = max(0.0, min(1.0, state.ocean.activity))
    state.ocean.instability = max(0.0, min(1.0, state.ocean.instability))

    # Tension relief
    if not ocean_escalated and _goals_are_stabilizing(registry):
        next_tension = max(MIN_TENSION, next_tension - TENSION_RELIEF_AMOUNT)

    # Stress -> drift influence
    if state.crew.stress > 0:
        for agent_id in registry.runtime:
            registry.runtime[agent_id].drift = min(
                1.0,
                registry.runtime[agent_id].drift
                + state.crew.stress * STRESS_DRIFT_COEFF,
            )

    # Earth pressure update
    update_earth_pressure(
        earth=earth,
        registry=registry,
        tension=next_tension,
    )

    # Advance time
    state.next_turn()

    return (
        next_tension,
        plans,
        constrained_decisions,
        conflict_score,
        stress_feedback_delta,
        ocean_feedback_delta,
    )


def _actions_str(plan: AgentPlan) -> str:
    return ",".join(action.value for action in plan.actions)


def main(max_turns: int = 500, *, randomSelection: bool = False):
    state = GameState.initial()
    engine = GameEngine()
    earth = EarthState()
    solaris = SolarisState()
    tension = 0.0

    registry = AgentRegistry()
    for spec in list_agent_specs():
        registry.register_agent(spec.agent_id, spec.default_config)

    root = Path(__file__).resolve().parents[1]
    out_dir = root / "notes" / "tests"
    out_dir.mkdir(parents=True, exist_ok=True)

    run_id = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    out_path = out_dir / f"bot_run_{run_id}.csv"

    columns = [
        "turn",
        "ocean_activity",
        "ocean_instability",
        "crew_stress",
        "crew_fatigue",
        "station_power_level",
        "tension",
        "conflict_score",
        "avg_drift",
        "stress_feedback_delta",
        "ocean_feedback_delta",
        "earth_pressure",
        "solaris_intensity",
        "ending_type",
    ]

    for spec in list_agent_specs():
        columns.extend(
            [
                f"{spec.agent_id}_goal_chosen",
                f"{spec.agent_id}_priority_chosen",
                f"{spec.agent_id}_goal_effective",
                f"{spec.agent_id}_priority_effective",
                f"{spec.agent_id}_actions",
                f"{spec.agent_id}_drift",
            ]
        )

    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()

        for _ in range(max_turns):
            decisions = choose_decisions(state, randomSelection=randomSelection)
            decisions_by_id = {d.agent_id: d for d in decisions}

            (
                tension,
                plans,
                constrained,
                conflict_score,
                stress_feedback_delta,
                ocean_feedback_delta,
            ) = run_bot_turn(
                state=state,
                registry=registry,
                decisions=decisions,
                engine=engine,
                current_tension=tension,
                earth=earth,
            )

            update_solaris_intensity(
                solaris=solaris,
                tension=tension,
                earth_pressure=earth.pressure,
            )

            plans_by_id = {p.agent_id: p for p in plans}
            constrained_by_id = {d.agent_id: d for d in constrained}

            ending = check_end_conditions(
                state=state,
                registry=registry,
                tension=tension,
            )

            if registry.runtime:
                avg_drift = (
                    sum(rt.drift for rt in registry.runtime.values())
                    / len(registry.runtime)
                )
            else:
                avg_drift = 0.0

            row = {
                "turn": state.turn,
                "ocean_activity": round(state.ocean.activity, 4),
                "ocean_instability": round(state.ocean.instability, 4),
                "crew_stress": round(state.crew.stress, 4),
                "crew_fatigue": round(state.crew.fatigue, 4),
                "station_power_level": round(state.station.power_level, 4),
                "tension": round(tension, 4),
                "conflict_score": round(conflict_score, 4),
                "avg_drift": round(avg_drift, 4),
                "stress_feedback_delta": round(stress_feedback_delta, 4),
                "ocean_feedback_delta": round(ocean_feedback_delta, 4),
                "earth_pressure": round(earth.pressure, 4),
                "solaris_intensity": round(solaris.intensity, 4),
                "ending_type": ending.type.value if ending else "",
            }

            for spec in list_agent_specs():
                runtime = registry.runtime.get(spec.agent_id)
                plan = plans_by_id.get(spec.agent_id)
                decision = decisions_by_id.get(spec.agent_id)
                constrained_decision = constrained_by_id.get(spec.agent_id)
                row.update(
                    {
                        f"{spec.agent_id}_goal_chosen": decision.goal.name
                        if decision
                        else "",
                        f"{spec.agent_id}_priority_chosen": decision.priority.name
                        if decision
                        else "",
                        f"{spec.agent_id}_goal_effective": constrained_decision.goal.name
                        if constrained_decision
                        else "",
                        f"{spec.agent_id}_priority_effective": constrained_decision.priority.name
                        if constrained_decision
                        else "",
                        f"{spec.agent_id}_actions": _actions_str(plan)
                        if plan
                        else "",
                        f"{spec.agent_id}_drift": round(runtime.drift, 4)
                        if runtime
                        else "",
                    }
                )

            writer.writerow(row)

            if ending:
                break

    print(f"[BOT RUN] Saved: {out_path}")


if __name__ == "__main__":
    main()
