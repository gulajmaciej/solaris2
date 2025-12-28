
# SOLARIS2

Decision-driven simulation focused on agent conflict, institutional pressure,
and evolving world state.

One player decision per agent per turn. Agents plan actions, the world updates
deterministically, and LLM observers generate reports.

## Run
1. Install requirements
2. Start the game loop

python game/loop.py

## Docs
- `docs/helps/cheatsheet.csv` - variables, update rules, and impacts
- `docs/helps/system_map.md` - feedback loop overview
- `docs/helps/turn_pipeline.md` - turn order of operations

## Structure
- `core/` world state and deterministic rules
- `agents/` agent logic and planners
- `game/` orchestration, CLI, and turn loop
