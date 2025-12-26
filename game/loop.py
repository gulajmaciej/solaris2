from core.state import GameState
from core.engine import GameEngine
from core.earth import EarthState
from core.solaris import SolarisState, update_solaris_intensity

from agents.config import (
    AgentRegistry,
    AgentConfig,
    AgentGoal,
    PriorityLevel,
)

from agents.instrument_specialist import observe as observe_instruments
from agents.crew_officer import observe as observe_crew

from game.cli import prompt_decision
from game.turn import run_turn
from game.endings import check_end_conditions


def main():
    state = GameState.initial()
    tension = 0.0
    earth = EarthState()
    solaris = SolarisState()
    engine = GameEngine()

    registry = AgentRegistry()
    registry.register_agent(
        "instrument_specialist",
        AgentConfig(
            goal=AgentGoal.MAXIMIZE_ANOMALY_DETECTION,
            priority=PriorityLevel.HIGH,
        ),
    )
    registry.register_agent(
        "crew_officer",
        AgentConfig(
            goal=AgentGoal.MINIMIZE_CREW_STRESS,
            priority=PriorityLevel.MEDIUM,
        ),
    )

    while True:
        print("\n==============================")
        print(f"TURN {state.turn}")
        print("==============================")

        print("\n--- PLAYER DECISIONS ---")
        decisions = []
        for agent_id in registry.configs:
            d = prompt_decision(agent_id=agent_id, registry=registry)
            if d:
                decisions.append(d)

        print("\n--- AGENT EXECUTION ---")
        tension = run_turn(
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

        print("\n--- OBSERVATIONS ---")
        print(
            "INSTRUMENT:",
            observe_instruments(
                state,
                registry.get_runtime("instrument_specialist").drift,
                solaris,
            ),
        )
        print(
            "CREW:",
            observe_crew(
                state,
                registry.get_runtime("crew_officer").drift,
                solaris,
            ),
        )

        print("\n--- SYSTEM FEEDBACK ---")
        print("TENSION:", round(tension, 3))
        print("EARTH PRESSURE:", round(earth.pressure, 3))
        print("SOLARIS INTENSITY:", round(solaris.intensity, 3))
        print("DRIFT:")
        for aid, rt in registry.runtime.items():
            print(f"  {aid}: {rt.drift:.3f}")

        ending = check_end_conditions(
            state=state,
            registry=registry,
            tension=tension,
        )

        if ending:
            print("\n=== END OF SIMULATION ===")
            print(f"ENDING: {ending.type.value.replace('_', ' ').title()}")
            print(ending.reason)
            break


if __name__ == "__main__":
    main()
