
# SOLARIS2

Decision-driven simulation focused on agent conflict, institutional pressure,
and evolving world state.

One player decision per agent per turn. Agents plan actions, the world updates
deterministically, and LLM observers generate reports.
Agents also have deterministic MCP tools that can alter existing world variables
in the same turn before planning.
Add new agents by registering them in `agents/catalog.py` with default config,
allowed goals, and act/observe bindings.

## Run
1. Install requirements
2. Start the game loop

python game/loop.py

## Docs
- `docs/helps/cheatsheet.csv` - variables, update rules, and impacts
- `docs/helps/agent_tools.md` - MCP agent tools and deltas
- `docs/helps/system_map.md` - feedback loop overview
- `docs/helps/turn_pipeline.md` - turn order of operations

## Structure
- `core/` world state and deterministic rules
- `agents/` agent logic and planners
- `game/` orchestration, CLI, and turn loop
