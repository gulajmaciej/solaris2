# Turn Pipeline (Order of Operations)

1. Collect player decisions (per agent).
2. Apply Earth governance constraints to decisions.
3. Update agent registry (goals + priorities).
4. Plan agent actions (per agent plan).
5. Execute actions deterministically on the world state.
6. Compute tension and update agent drift.
7. Apply ocean escalation if tension crosses thresholds.
8. Apply tension relief if stabilization conditions are met.
9. Update Earth pressure (hysteresis + drift influence).
10. Advance the turn counter.
11. Update Solaris intensity from tension + Earth pressure.
12. Generate agent observations (LLM reports).
13. Check end conditions.

This sequence matches the `SimulationRunner.step()` flow and the logic inside
`game/turn.py`.
