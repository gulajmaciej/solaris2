# Agent Tools (MCP)

Deterministic tools that apply deltas to existing world variables in the same
turn, before planning and action execution.

Instrument specialist:
- calibrate_filters: ocean.instability -= 0.04, ocean.activity -= 0.02, crew.fatigue += 0.005
- boost_measurement_frequency: ocean.activity += 0.05, station.power_level -= 0.03, crew.fatigue += 0.02
- adjust_sensor_sensitivity: ocean.activity += 0.03, ocean.instability += 0.02, station.power_level -= 0.02, crew.fatigue += 0.01

Crew officer:
- initiate_rest_protocol: crew.stress -= 0.05, crew.fatigue -= 0.03, station.power_level -= 0.02
- reduce_information_flow: crew.stress -= 0.03, ocean.activity -= 0.03
- enforce_procedures: crew.stress += 0.02, station.power_level -= 0.01, crew.fatigue += 0.01
- report_alarm_to_earth: earth.pressure += 0.02
- report_stabilization_to_earth: earth.pressure -= 0.02

All variables are clamped to [0.0, 1.0] after application.
