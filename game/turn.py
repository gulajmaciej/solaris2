from typing import List

from core.state import GameState
from core.engine import GameEngine
from core.tension import update_tension_and_drift
from core.earth import EarthState, update_earth_pressure

from agents.config import AgentRegistry
from agents.planner import plan_actions
from game.decision import PlayerDecision
from game.governance import apply_earth_constraints


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

    # 0. apply institutional constraints
    constrained_decisions = []
    for d in decisions:
        constrained_decisions.append(
            apply_earth_constraints(decision=d, earth=earth)
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

    # 4. tension + drift
    next_tension = update_tension_and_drift(
        registry=registry,
        current_tension=current_tension,
    )

    # 5. earth pressure update
    update_earth_pressure(
        earth=earth,
        registry=registry,
        tension=next_tension,
    )

    # 6. advance time
    state.next_turn()

    return next_tension
