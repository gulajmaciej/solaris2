from datetime import datetime, UTC

from game.cli import prompt_decision, render_agent_event
from game.simulation import SimulationRunner


def main():
    thread_id = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    print(f"\n[SESSION] thread_id: {thread_id}")
    runner = SimulationRunner(
        thread_id=thread_id,
        log_sink=render_agent_event,
    )

    # --- MAIN LOOP ---
    while True:
        print("\n==============================")
        print(f"TURN {runner.state.turn}")
        print("==============================")

        # --- PLAYER DECISIONS ---
        print("\n--- PLAYER DECISIONS ---")
        decisions = []
        for agent_id in runner.registry.configs:
            decision = prompt_decision(
                agent_id=agent_id,
                registry=runner.registry,
            )
            if decision:
                decisions.append(decision)

        # --- SYSTEM EXECUTION ---
        print("\n--- SYSTEM EXECUTION ---")
        result = runner.step(decisions)

        # --- OBSERVATIONS ---
        print("\n--- OBSERVATIONS ---")
        for agent_id, report in result.reports.items():
            label = agent_id.replace("_", " ").upper()
            print(f"\n[{label}]")
            print(report)

        # --- DEBUG VIEW (LANGGRAPH) ---
        for agent_id, agent in runner.agents.items():
            if hasattr(agent, "debug_render"):
                agent.debug_render(
                    thread_id=f"{runner.thread_id}:{agent_id}"
                )

        # --- SYSTEM FEEDBACK ---
        print("\n--- SYSTEM FEEDBACK ---")
        print(f"Tension: {round(result.tension, 3)}")
        print(f"Earth pressure: {round(result.earth_pressure, 3)}")
        print(f"Solaris intensity: {round(result.solaris_intensity, 3)}")

        print("\nAgent drift levels:")
        for agent_id, drift in result.drift_levels.items():
            print(f"  {agent_id}: {round(drift, 3)}")

        # --- DEBUG: WHY SYSTEM CHANGED ---
        if result.state.flags.get("tension_debug"):
            print("\n--- TENSION DEBUG ---")
            for d in result.state.flags["tension_debug"]:
                print(
                    f"Tension {d['previous']} ƒÅ' {d['next']} "
                    f"({d['delta']:+}) | reason: {d['reason']}"
                )

        if result.state.flags.get("earth_debug"):
            print("\n--- EARTH PRESSURE DEBUG ---")
            for d in result.state.flags["earth_debug"]:
                print(
                    f"Earth pressure {d['previous']} ƒÅ' {d['next']} "
                    f"({d['delta']:+}) | reason: {d['reason']} "
                    f"| tension={d['tension']}"
                )

        if result.state.flags.get("ocean_debug"):
            print("\n--- OCEAN DEBUG ---")
            for d in result.state.flags["ocean_debug"]:
                print(
                    f"{d['parameter']} {d['delta']:+} | "
                    f"reason: {d['reason']} | tension={d['tension']}"
                )

        if result.state.flags.get("drift_debug"):
            print("\n--- DRIFT DEBUG ---")
            for d in result.state.flags["drift_debug"]:
                print(
                    f"{d['agent_id']} {d['previous']} -> {d['next']} "
                    f"({d['delta']:+}) | reason: {d['reason']}"
                )

        # --- END CONDITIONS ---
        if result.ending:
            print("\n=== END OF SIMULATION ===")
            print(
                f"ENDING: {result.ending.type.value.replace('_', ' ').title()}"
            )
            print(result.ending.reason)
            break

        input("\n[ENTER] Next turn...")


if __name__ == "__main__":
    main()
