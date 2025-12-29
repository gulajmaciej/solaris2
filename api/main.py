from fastapi import FastAPI

from api.schemas import (
    TurnRequest,
    TurnResponse,
    AgentReport,
)

from api.state import SESSION
from agents.catalog import get_agent_spec
from api.mcp import router as mcp_router

from game.turn import run_turn
from game.decision import PlayerDecision
from game.endings import check_end_conditions

from core.solaris import update_solaris_intensity
from mcp.context import set_session


app = FastAPI(title="Solaris Simulation API")
app.include_router(mcp_router)


@app.post("/turn", response_model=TurnResponse)
def run_turn_endpoint(payload: TurnRequest):
    set_session(SESSION)
    decisions = [
        PlayerDecision(
            agent_id=d.agent_id,
            goal=d.goal,
            priority=d.priority,
        )
        for d in payload.decisions
    ]

    for agent_id in SESSION.registry.configs:
        spec = get_agent_spec(agent_id)
        agent = SESSION.agents[agent_id]
        drift = SESSION.registry.get_runtime(agent_id).drift
        spec.act(agent, drift, f"{SESSION.thread_id}:{agent_id}")

    SESSION.tension = run_turn(
        state=SESSION.state,
        registry=SESSION.registry,
        decisions=decisions,
        engine=SESSION.engine,
        current_tension=SESSION.tension,
        earth=SESSION.earth,
    )

    update_solaris_intensity(
        solaris=SESSION.solaris,
        tension=SESSION.tension,
        earth_pressure=SESSION.earth.pressure,
    )
    set_session(SESSION)

    reports = []
    for agent_id in SESSION.registry.configs:
        spec = get_agent_spec(agent_id)
        agent = SESSION.agents[agent_id]
        drift = SESSION.registry.get_runtime(agent_id).drift
        reports.append(
            AgentReport(
                agent_id=agent_id,
                text=spec.observe(
                    agent,
                    SESSION.state,
                    drift,
                    SESSION.solaris,
                    f"{SESSION.thread_id}:{agent_id}",
                ),
            )
        )

    return TurnResponse(
        turn=SESSION.state.turn,
        tension=SESSION.tension,
        earth_pressure=SESSION.earth.pressure,
        solaris_intensity=SESSION.solaris.intensity,
        reports=reports,
    )
