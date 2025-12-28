# System Map (Quick Context)

This map shows the main feedback loops and how the world evolves each turn.

```
Player Decisions
    |
    v
Agent Goals/Priorities -----> Conflict Matrix -----> Tension -----> Drift
    |                               |                  |             |
    |                               |                  v             v
    |                               |            Ocean Escalation   Earth Pressure
    |                               |                  |             |
    |                               v                  v             v
    |                        Planning (Agent Plans)   Ocean State ----+
    |                               |                                  |
    v                               v                                  |
Action Execution --------------> GameState ----------------------------+
    |
    v
Observations (LLM agents read GameState + Drift + Solaris)

Tension + Earth Pressure -> Solaris Intensity -> Observation tone
```

Notes:
- The world evolves deterministically (actions, tension, pressure).
- LLM agents only interpret; they do not change the world directly.
- Governance feeds back into the next turn by constraining decisions.
- Ocean state feeds back into tension (ocean feedback).
