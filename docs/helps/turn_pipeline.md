# Turn Pipeline (Order of Operations)

1. Collect player decisions (per agent).
2. Apply Earth governance constraints to decisions.
3. Update agent registry (goals + priorities).
4. Plan agent actions (per agent plan).
5. Execute actions deterministically on the world state.
6. Apply fatigue -> stress coupling.
7. Compute tension and update agent drift (base).
8. Apply stress and ocean feedback into tension.
9. Apply ocean escalation if tension crosses thresholds.
10. Apply tension relief if stabilization conditions are met.
11. Apply stress -> drift influence (record drift debug).
12. Update Earth pressure (hysteresis + drift influence).
13. Advance the turn counter.
14. Update Solaris intensity from tension + Earth pressure.
15. Generate agent observations (LLM reports).
16. Check end conditions.

This sequence matches the `SimulationRunner.step()` flow and the logic inside
`game/turn.py`.
