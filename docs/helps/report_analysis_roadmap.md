# Bot Run Report Analysis Roadmap

Purpose
Guide an LLM to analyze bot_run CSV outputs and suggest tuning changes that
improve gameplay (balance, stability, and meaningful variation) without adding
new variables.

Inputs
- CSV report from game/bot_run.py (turn-level metrics and per-agent columns).
- Current tuning constants in core/actions.py, game/turn.py, core/tension.py,
  core/earth.py, and tool deltas in mcp/tools.py.
- Deterministic bot decision rules in game/bot_run.py (choose_decisions,
  plan_actions_rule). These are the behaviors reflected in bot_run CSVs.
- Agent tool decision rules (agents/*/nodes.py) for mapping goals to tool usage.
- World rules summary in docs/helps/solaris_parameters.csv and docs/helps/turn_pipeline.md.

Workflow
1) Load the CSV and compute basic summaries:
   - min/mean/max for tension, ocean activity/instability, crew stress/fatigue,
     station power, earth pressure, solaris intensity.
   - per-agent action frequency and goal/priority distribution.
   - ending_type frequency and average turn length.

2) Diagnose pacing and stability:
   - Too fast endings: median turn count low, tension spikes early.
   - Stagnation: long runs with low variance, ocean activity near 0, or tension
     stuck near MIN_TENSION.
   - Instability runaway: ocean instability or tension pinned near 1.0.

3) Identify dominant feedback loops:
   - Stress loop: fatigue -> stress -> tension -> drift -> earth pressure.
   - Ocean loop: tension -> ocean escalation -> tension feedback.
   - Governance loop: earth pressure -> constrained decisions -> tension.

4) Propose small parameter adjustments (1-2 knobs at a time):
   - If tension rises too quickly: reduce STRESS_TENSION_COEFF or OCEAN_TENSION_COEFF.
   - If ocean escalates too aggressively: raise thresholds or reduce ACTIVITY_COEFF /
     INSTABILITY_COEFF.
   - If drift grows too fast: lower STRESS_DRIFT_COEFF or DRIFT_RATE.
   - If runs are too calm: increase conflict impact (priority_factor) or reduce
     tension relief amount.

5) Validate against gameplay goals:
   - Tension should fluctuate, not plateau.
   - Ocean should respond but not dominate.
   - Crew stress should matter but not lock the game.
   - Earth pressure should react with hysteresis, not oscillate every turn.

6) Output a tuning report:
   - Summary of observed issues with evidence (metric values).
   - Proposed parameter changes with rationale.
   - Expected effects on loops and pacing.

Guardrails
- Change only existing parameters (no new state variables).
- Keep deltas small (5-20 percent per iteration).
- Avoid simultaneous changes to more than two feedback loops.
- Re-run bot_run for validation after each change.
 - Remember bot_run uses deterministic planning; do not assume LLM behavior
   for action selection in these reports.

Suggested outputs (template)
- Problem: ...
- Evidence: ...
- Change: file/constant -> old -> new
- Rationale: ...
- Expected effect: ...
