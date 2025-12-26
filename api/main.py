from fastapi import FastAPI

from api.schemas import (
    TurnRequest,
    TurnResponse,
    AgentReport,
)

from api.state import SESSION
from api.mcp import router as mcp_router

from game.turn import run_turn
from game.decision import PlayerDecision
from game.endings import check_end_conditions

from agents.instrument_specialist import observe as observe_instruments
from agents.crew_officer import observe as observe_crew
from core.solaris import update_solaris_intensity


app = FastAPI(title="Solaris Simulation API")
app.include_router(mcp_router)


@app.post("/turn", response_model=TurnResponse)
def run_turn_endpoint(payload: TurnRequest):
    decisions = [
        PlayerDecision(
            agent_id=d.agent_id,
            goal=d.goal,
            priority=d.priority,
        )
        for d in payload.decisions
    ]

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

    reports = [
        AgentReport(
            agent_id="instrument_specialist",
            text=observe_instruments(
                SESSION.state,
                SESSION.registry.get_runtime("instrument_specialist").drift,
                SESSION.solaris,
            ),
        ),
        AgentReport(
            agent_id="crew_officer",
            text=observe_crew(
                SESSION.state,
                SESSION.registry.get_runtime("crew_officer").drift,
                SESSION.solaris,
            ),
        ),
    ]

    return TurnResponse(
        turn=SESSION.state.turn,
        tension=SESSION.tension,
        earth_pressure=SESSION.earth.pressure,
        solaris_intensity=SESSION.solaris.intensity,
        reports=reports,
    )
