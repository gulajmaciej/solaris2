# Agents Walkthrough (Instrument Specialist + Crew Officer)

This document is a step‑by‑step guide to the agents in this repo. It explains the intent of each file and (almost) every line, focusing on architectural goals and how each node behaves.

---

## High‑level architecture
The agents are LangGraph graphs with explicit state. Each agent has:
- **state schema** (TypedDict)
- **graph wiring** (nodes + edges + routing)
- **node implementations** (deterministic vs LLM)
- **agent wrapper** (thread_id, checkpointer, streaming)

Two agents exist:
- `instrument_specialist`
- `crew_officer`

There is also shared scaffolding:
- `agents/config.py`, `agents/catalog.py`, `agents/langgraph_state.py`

---

## File‑by‑file walkthrough

### `agents/config.py`
Purpose: define agent goals, priority, and a thin registry to hold configs + runtime.

- `AgentGoal` enum: hard‑coded policy goals for each agent type.
- `PriorityLevel` enum: symbolic importance (LOW/MEDIUM/HIGH).
- `AgentConfig`: the “intent layer” (goal + priority), explicitly not world state.
- `AgentRuntimeState`: runtime‑only metrics (currently `drift`).
- `AgentRegistry`: central in‑memory registry:
  - `configs` stores per‑agent `AgentConfig`.
  - `runtime` stores per‑agent `AgentRuntimeState`.
  - `register_agent` seeds both maps.
  - `set_goal` / `set_priority` mutate config and guard against unknown agents.
  - `get_config` / `get_runtime` return the stored objects.

Architectural intent: separate **intent (config)** from **world state** and from **agent cognitive memory**.

---

### `agents/catalog.py`
Purpose: declarative catalog of agent specs used by the simulation runner.

- `AgentSpec`: all metadata needed to construct + call an agent.
- `_instrument_act`, `_instrument_observe`: wrappers that adapt to the agent API.
- `_crew_act`, `_crew_observe`: same, but crew needs `drift`.
- `_CATALOG`: the registry of agent definitions (IDs, default goals, allowed goals).
- `get_agent_spec` / `list_agent_specs`: lookup API for the rest of the app.

Architectural intent: centralize “what agents exist” and how they are called.

---

### `agents/langgraph_state.py`
Purpose: shared TypedDict schemas for LangGraph state (one per agent).

#### `InstrumentAgentState`
Fields are explicitly enumerated so graph nodes know their inputs/outputs.
Key groups:
- **Cognitive state**: `hypothesis`, `confidence`, `contradictions`, `last_observation`.
- **Trace/debug**: `visited_nodes`, `last_route`, `phase`.
- **Tool state**: `tool_decision`, `tool_reason`, `tool_applied`.
- **World snapshot**: `ocean_activity`, `ocean_instability`, `station_power_level`,
  `tension`, `solaris_intensity`, `crew_stress`, `crew_fatigue`.
- **Crew‑coupling deltas**: `crew_confidence_delta`, `crew_contradiction_delta`.

`default_instrument_state()` supplies deterministic defaults for a new thread.

#### `CrewOfficerState`
Similar but smaller:
- World snapshot: `crew_stress`, `crew_fatigue`, `tension`, `solaris_intensity`.
- Cognitive: `last_observation`.
- Runtime: `drift`.
- Tool state: `tool_decision`, `tool_reason`, `tool_applied`.
- Trace: `visited_nodes`, `phase`.

`default_crew_state()` provides defaults.

Architectural intent: typed, explicit state = predictable graph behavior and better logs.

---

### `agents/mcp_client.py`
Purpose: legacy helper to build a LangChain‑style agent using MCP tools.

Step‑by‑step:
- Import `ChatOllama` and LangChain agent utilities.
- Instantiate `MCPServer`.
- Convert MCP tool schemas to LangChain `Tool` wrappers.
- Create a ChatOllama model.
- Return a `ZERO_SHOT_REACT_DESCRIPTION` agent.

Note: This is a different agent style than LangGraph, kept for experimentation.

---

### `agents/planner.py`
Purpose: LLM‑based symbolic planning to produce `PlannedAction` lists.

Key blocks:
- `PlannedAction` enum = symbolic actions (no side effects).
- `AgentPlan` dataclass = output of planning.
- `model`: ChatOllama for planning.
- `SYSTEM_PROMPT`: strict “return JSON array only”.
- `GOAL_ACTION_MAP`: maps `AgentGoal` → allowed actions.
- `plan_actions(...)`: builds prompt with world state + allowed actions, calls LLM,
  parses JSON, filters actions to allowed, returns `AgentPlan`.

Architectural intent: separate “plan” from “execute” to keep engine deterministic.

---

### `agents/instrument_specialist/__init__.py`
Exports the agent class and graph builder.

---

### `agents/instrument_specialist/state.py`
Re‑exports `InstrumentAgentState` and `default_instrument_state` from shared state.

---

### `agents/instrument_specialist/graph.py`
Purpose: define the LangGraph topology for the instrument specialist.

Walkthrough:
- Build a `StateGraph(InstrumentAgentState)`.
- Add nodes: `read_context`, `decide_tool`, `apply_tool`, `observe`,
  `update_hypothesis`, `apply_crew_context`, `flag_event`.
- Entry point: `read_context`.
- Routing:
  - After `read_context`: `decide_tool` if phase == "tool", else `observe`.
  - After `apply_tool`: end if phase == "tool", else `observe`.
- Linear edges:
  - `decide_tool → apply_tool`
  - `observe → update_hypothesis → apply_crew_context`
- Conditional:
  - `apply_crew_context` routes through `evaluate_concern` to `flag_event` or `END`.
- Compile with `InMemorySaver` by default.

Architectural intent: single graph supports two phases (`tool` vs `observe`) by routing.

---

### `agents/instrument_specialist/agent.py`
Purpose: runtime wrapper around the compiled graph.

Walkthrough:
- Uses `InMemorySaver` unless a checkpointer is provided.
- Builds the graph via `build_instrument_graph`.
- Maintains a `thread_id` and optional `log_sink`.
- `_config`: generates the `thread_id` config for graph calls.
- `_get_state`: retrieves snapshot; falls back to defaults.
- `_run_graph`:
  - sets `phase` in current state
  - streams graph with `stream_mode=["custom","values"]`
  - forwards custom events to `log_sink` or `print(...)`
  - returns the last `values` chunk (final state)
- `act`: runs the graph in `"tool"` phase.
- `observe`: runs in `"observe"` phase and returns `last_observation`.
- `debug_render`: prints a human‑readable view of the internal state.

Architectural intent: isolate graph execution and expose a small API to the runner.

---

### `agents/instrument_specialist/nodes.py`
Purpose: implement each node in the graph.

Global setup:
- `llm`: ChatOllama model for language tasks.
- `mcp`: MCPServer for tool calls.
- constants for crew coupling.
- `_emit_event`: custom stream payloads for logging/telemetry.

Node by node:

1) `read_context`
   - Deterministic.
   - Calls MCP tools to read ocean/crew/system state.
   - Writes these values into state.
   - Emits `node_start` and `node_end` with `output`.

2) `decide_tool`
   - Deterministic.
   - Applies rule‑based thresholds to choose a tool.
   - Stores `tool_decision` and `tool_reason`.
   - Emits decision + node output.

3) `apply_tool`
   - Deterministic side‑effect node.
   - Reads `tool_decision`, calls the tool via MCP.
   - Emits tool call + result, and `node_end` with output payload.

4) `observe`
   - LLM node.
   - Reads ocean state, formats a prompt, invokes LLM.
   - Saves `last_observation`.
   - Emits `node_start` with input snapshot and `node_end` with output.

5) `update_hypothesis`
   - LLM + deterministic update.
   - LLM step 1: propose new hypothesis.
   - LLM step 2: classify relation (CONSISTENT vs CONTRADICTS).
   - Deterministic step: adjust confidence/contradictions.
   - Emits inputs + outputs.

6) `apply_crew_context`
   - Deterministic.
   - Reads crew state, modifies confidence + contradictions.
   - Emits inputs + outputs with deltas.

7) `evaluate_concern`
   - Deterministic router (not a node; used for conditional edges).
   - If confidence high and contradictions >= 2 → "flag", else "end".

8) `flag_event`
   - Deterministic side effect.
   - Calls MCP tool to set a global flag and emits node output.

Architectural intent: explicit input/output for every node to enable traceable agent execution.

---

### `agents/crew_officer/__init__.py`
Exports `CrewOfficerAgent` and `build_crew_graph`.

---

### `agents/crew_officer/state.py`
Re‑exports `CrewOfficerState` and `default_crew_state`.

---

### `agents/crew_officer/graph.py`
Purpose: define the crew officer graph (simpler than instrument specialist).

Walkthrough:
- Nodes: `read_context`, `decide_tool`, `apply_tool`, `observe`.
- Entry: `read_context`.
- Routing:
  - After `read_context`: `decide_tool` if phase == "tool" else `observe`.
  - After `apply_tool`: end if phase == "tool" else `observe`.
- `observe → END`.
- Compiled with `InMemorySaver`.

Architectural intent: same phase‑based routing pattern, fewer cognitive nodes.

---

### `agents/crew_officer/agent.py`
Purpose: same wrapper pattern as instrument specialist, with drift passed in.

Key differences:
- `_run_graph` sets `drift` if provided.
- `act` requires a `drift` parameter (even if 0.0).
- `observe` accepts `GameState` + `SolarisState` but only uses `phase` + `drift`.

---

### `agents/crew_officer/nodes.py`
Purpose: crew officer nodes.

Global setup:
- `llm`: ChatOllama for observation.
- `mcp`: MCPServer.
- `_emit_event`: custom stream payloads.

Nodes:

1) `read_context`
   - Deterministic.
   - Reads crew + system state via MCP.
   - Updates state; emits output.

2) `decide_tool`
   - Deterministic.
   - Rule‑based tool selection from stress/fatigue/tension/drift/solaris.
   - Saves `tool_decision` + `tool_reason`; emits output.

3) `apply_tool`
   - Deterministic side effect.
   - Executes tool via MCP; emits tool result + node output.

4) `observe`
   - LLM node.
   - Prompt uses crew metrics + drift + solaris intensity.
   - Response is trimmed to 2–3 sentences.
   - Emits input snapshot + observation output.

Architectural intent: clear separation between deterministic control and LLM judgment.

---

## Architectural assumptions (implicit in the code)
- **Phase drives routing**: `phase="tool"` vs `phase="observe"` is the switch.
- **MCP is the world adapter**: nodes do not mutate GameState directly.
- **LLM is not trusted for control**: tool decisions are rule‑based.
- **Observations are narrative**: LLM outputs are used as human‑readable reports.
- **Traceability first**: node input/output is logged for debugging and learning.

---

## Suggested next steps for experimentation
1) Add prompt inputs to node `input` payloads if you want full “LLM input” transparency.  
2) Convert MCP side effects into tasks if you plan to use durable execution.  
3) Add tests for deterministic nodes (input → state update).  
