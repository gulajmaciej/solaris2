# System Map (Quick Context)

This map shows the main feedback loops and how the world evolves each turn.

```
Player Decisions
    |
    v
Agent Tools (MCP, deterministic) -----> GameState (deltas applied)
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
Observations (LLM nodes read GameState + Drift + Solaris)

Tension + Earth Pressure -> Solaris Intensity -> Observation tone
```

Notes:
- The world evolves deterministically (actions, tension, pressure).
- Observational LLM nodes only interpret; tools act in a separate phase.
- Tool effects are applied before planning, in the same turn.
- Tool list and deltas: docs/helps/agent_tools.md.
- Parameter definitions: docs/helps/solaris_parameters.csv.
- Governance feeds back into the next turn by constraining decisions.
- Ocean state feeds back into tension (ocean feedback).
