# Agent Tools (MCP)

Deterministic tools that apply deltas to existing world variables in the same
turn, before planning and action execution. Tool selection is rule-based in
agent nodes (`decide_tool`) and tool execution happens in `apply_tool`.

Instrument specialist:
- calibrate_filters: ocean.instability -= 0.04, ocean.activity -= 0.02, crew.fatigue += 0.005
- boost_measurement_frequency: ocean.activity += 0.05, station.power_level -= 0.03, crew.fatigue += 0.02
- adjust_sensor_sensitivity: ocean.activity += 0.03, ocean.instability += 0.02, station.power_level -= 0.02, crew.fatigue += 0.01

Instrument specialist decision rules (decide_tool):
- if ocean_instability >= 0.6 -> calibrate_filters
- else if ocean_activity <= 0.35 and station_power_level >= 0.4 -> boost_measurement_frequency
- else if ocean_activity >= 0.35 and ocean_instability <= 0.45 -> adjust_sensor_sensitivity
- else if crew_fatigue >= 0.6 -> calibrate_filters

Crew officer:
- initiate_rest_protocol: crew.stress -= 0.05, crew.fatigue -= 0.03, station.power_level -= 0.02
- reduce_information_flow: crew.stress -= 0.03, ocean.activity -= 0.03
- enforce_procedures: crew.stress += 0.02, station.power_level -= 0.01, crew.fatigue += 0.01
- report_alarm_to_earth: earth.pressure += 0.02
- report_stabilization_to_earth: earth.pressure -= 0.02

Crew officer decision rules (decide_tool):
- if crew_stress >= 0.6 or crew_fatigue >= 0.6 -> initiate_rest_protocol
- else if crew_stress >= 0.45 and solaris_intensity >= 0.5 -> reduce_information_flow
- else if crew_stress <= 0.35 and crew_fatigue <= 0.35 -> enforce_procedures
- else if tension >= 0.7 and drift >= 0.5 -> report_alarm_to_earth
- else if tension <= 0.25 and crew_stress <= 0.3 -> report_stabilization_to_earth

All variables are clamped to [0.0, 1.0] after application.

Runtime tracing
- Tool calls are emitted as node events with explicit input/output payloads.
- In TUI, tool execution appears as `apply_tool (deterministic) input/output`.

Adding new agents
- Register the agent in agents/catalog.py with default config, allowed goals,
  and act/observe bindings.
