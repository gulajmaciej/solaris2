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

from agents.instrument_specialist import (
    observe as observe_instruments,
    debug_render as debug_instrument,
)
from agents.crew_officer import observe as observe_crew

from game.cli import prompt_decision
from game.turn import run_turn
from game.endings import check_end_conditions


def main():
    # --- INITIAL STATE ---
    state = GameState.initial()
    engine = GameEngine()

    earth = EarthState()
    solaris = SolarisState()
    tension = 0.0

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

    # --- MAIN LOOP ---
    while True:
        print("\n==============================")
        print(f"TURN {state.turn}")
        print("==============================")

        # --- PLAYER DECISIONS ---
        print("\n--- PLAYER DECISIONS ---")
        decisions = []
        for agent_id in registry.configs:
            decision = prompt_decision(agent_id=agent_id, registry=registry)
            if decision:
                decisions.append(decision)

        # --- SYSTEM EXECUTION ---
        print("\n--- SYSTEM EXECUTION ---")
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

        # --- OBSERVATIONS ---
        print("\n--- OBSERVATIONS ---")

        instrument_report = observe_instruments(
            state,
            registry.get_runtime("instrument_specialist").drift,
            solaris,
        )
        print("\n[INSTRUMENT SPECIALIST]")
        print(instrument_report)

        crew_report = observe_crew(
            state,
            registry.get_runtime("crew_officer").drift,
            solaris,
        )
        print("\n[CREW OFFICER]")
        print(crew_report)

        # --- DEBUG VIEW (LANGGRAPH) ---
        debug_instrument()

        # --- SYSTEM FEEDBACK ---
        print("\n--- SYSTEM FEEDBACK ---")
        print(f"Tension: {round(tension, 3)}")
        print(f"Earth pressure: {round(earth.pressure, 3)}")
        print(f"Solaris intensity: {round(solaris.intensity, 3)}")

        print("\nAgent drift levels:")
        for agent_id, runtime in registry.runtime.items():
            print(f"  {agent_id}: {round(runtime.drift, 3)}")

        # --- DEBUG: WHY SYSTEM CHANGED ---
        if state.flags.get("tension_debug"):
            print("\n--- TENSION DEBUG ---")
            for d in state.flags["tension_debug"]:
                print(
                    f"Tension {d['previous']} → {d['next']} "
                    f"({d['delta']:+}) | reason: {d['reason']}"
                )

        if state.flags.get("earth_debug"):
            print("\n--- EARTH PRESSURE DEBUG ---")
            for d in state.flags["earth_debug"]:
                print(
                    f"Earth pressure {d['previous']} → {d['next']} "
                    f"({d['delta']:+}) | reason: {d['reason']} "
                    f"| tension={d['tension']}"
                )

        if state.flags.get("ocean_debug"):
            print("\n--- OCEAN DEBUG ---")
            for d in state.flags["ocean_debug"]:
                print(
                    f"{d['parameter']} {d['delta']:+} | "
                    f"reason: {d['reason']} | tension={d['tension']}"
                )

        # --- END CONDITIONS ---
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

        input("\n[ENTER] Next turn...")


if __name__ == "__main__":
    main()
