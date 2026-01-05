# Turn Pipeline (Order of Operations)

1. Collect player decisions (per agent).
2. Agent tool phase (LangGraph, deterministic): agents run their tool graph and apply MCP tool deltas.
3. Apply Earth governance constraints to decisions.
4. Update agent registry (goals + priorities).
5. Plan agent actions (per agent plan).
6. Execute actions deterministically on the world state.
7. Apply fatigue -> stress coupling.
8. Compute base tension and update agent drift (conflict + drift).
9. Apply stress and ocean feedback into tension.
10. Apply ocean escalation if tension crosses thresholds.
11. Apply tension relief if stabilization conditions are met.
12. Apply stress -> drift influence (record drift debug).
13. Update Earth pressure (hysteresis + drift influence).
14. Advance the turn counter.
15. Update Solaris intensity from tension + Earth pressure.
16. Generate agent observations (LLM reports).
17. Check end conditions.

This sequence matches `SimulationRunner.step()` and the internal ordering
inside `game/turn.py`, with the tool phase occurring before `run_turn`.
Tool definitions and decision rules live in docs/helps/agent_tools.md.
