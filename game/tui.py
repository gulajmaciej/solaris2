from __future__ import annotations

from datetime import datetime, UTC
import subprocess
import sys

from rich.text import Text
from textual import events
from textual._on import on
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, VerticalScroll
from textual.widgets import Button, LoadingIndicator, OptionList, RichLog, Static
from textual.widgets.option_list import Option

from agents.catalog import get_agent_spec
from agents.config import AgentGoal, PriorityLevel
from game.decision import PlayerDecision
from game.simulation import SimulationRunner

GOAL_PHASE = "goal"
PRIORITY_PHASE = "priority"


def _goal_option_id(goal: AgentGoal) -> str:
    return f"goal:{goal.name}"


def _priority_option_id(priority: PriorityLevel) -> str:
    return f"priority:{priority.name}"


class SolarisTUI(App[None]):
    CSS = """
    #root {
        layout: vertical;
    }
    #top {
        layout: horizontal;
        height: 60%;
    }
    #left-panel {
        width: 35%;
        border: solid $border;
        padding: 1;
        background: black;
        color: #00ff5f;
    }
    #right-panel {
        width: 65%;
        border: solid $border;
        padding: 1;
    }
    #terminal-header {
        height: 1;
        layout: horizontal;
        width: 1fr;
    }
    #terminal-title {
        width: 1fr;
    }
    #terminal-copy {
        margin-left: 1;
    }
    #bottom-panel {
        height: 40%;
        padding: 1;
    }
    #bottom-row {
        height: 1fr;
        layout: horizontal;
    }
    #status-panel {
        width: 40%;
        border: solid $border;
        padding: 1;
        align: left top;
    }
    #world-panel {
        width: 60%;
        border: solid $border;
        padding: 1;
    }
    #world-scroll {
        height: 1fr;
    }
    #decision-title {
        height: 2;
    }
    #decision-list {
        height: 1fr;
    }
    #langsmith-log {
        height: 1fr;
        overflow-x: hidden;
    }
    #terminal-loading {
        height: 1;
        padding-left: 1;
    }
    #terminal-loading-text {
        padding-left: 1;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("ctrl+c", "quit", "Quit"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._thread_id = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
        self._runner = SimulationRunner(
            thread_id=self._thread_id,
            log_sink=self._on_agent_event,
        )
        self._agent_ids = list(self._runner.registry.configs.keys())
        self._current_agent_index = 0
        self._decision_phase = GOAL_PHASE
        self._selected_goal: AgentGoal | None = None
        self._pending_decisions: list[PlayerDecision] = []
        self._highlighted_option_id: str | None = None
        self._running_turn = False
        self._game_over = False
        self._terminal_lines: list[str] = []
        self._turn_agent_events: dict[str, dict[str, str]] = {}
        self._last_node_by_agent: dict[str, str] = {}

    def compose(self) -> ComposeResult:
        with Container(id="root"):
            with Horizontal(id="top"):
                with Container(id="left-panel"):
                    yield Static(id="decision-title")
                    yield OptionList(id="decision-list")
                with Container(id="right-panel"):
                    with Horizontal(id="terminal-header"):
                        yield Button("Copy", id="terminal-copy")
                    yield RichLog(id="langsmith-log", highlight=True, markup=True)
                    with Horizontal(id="terminal-loading"):
                        yield LoadingIndicator(id="terminal-spinner")
                        yield Static("Thinking...", id="terminal-loading-text")
            with Container(id="bottom-panel"):
                with Horizontal(id="bottom-row"):
                    with Container(id="status-panel"):
                        yield Static(id="status-bar")
                    with Container(id="world-panel"):
                        with VerticalScroll(id="world-scroll"):
                            yield Static(id="world-bar")

    def on_mount(self) -> None:
        self._update_status_bar()
        self._refresh_decision_list()
        self.query_one(OptionList).focus()
        self._append_log_line(f"[SESSION] thread_id: {self._thread_id}")
        self._set_terminal_loading(False)
        self._set_panel_titles()

    def on_key(self, event: events.Key) -> None:
        if event.key != "enter":
            return
        if self._game_over or self._running_turn:
            return
        option_list = self.query_one(OptionList)
        if option_list.has_focus:
            self._apply_selection()
            event.stop()

    @on(OptionList.OptionHighlighted, selector="#decision-list")
    def _remember_highlight(self, event: OptionList.OptionHighlighted) -> None:
        self._highlighted_option_id = event.option.id

    def append_terminal_line(self, text: str) -> None:
        self._append_log_line(text)

    def _append_log_line(self, text: str) -> None:
        log = self.query_one("#langsmith-log", RichLog)
        self._terminal_lines.append(text)
        wrapped = Text(text, no_wrap=False, overflow="fold")
        log.write(wrapped)

    def _append_log_block(self, lines: list[str]) -> None:
        for line in lines:
            self._append_log_line(line)

    def _on_agent_event(self, event: dict) -> None:
        agent_id = event.get("agent")
        node = event.get("node")
        event_type = event.get("event")
        data = event.get("data") or {}

        if agent_id and event_type:
            entry = self._turn_agent_events.setdefault(agent_id, {})
            if event_type == "decision":
                entry["decision_tool"] = data.get("tool") or "none"
                entry["decision_reason"] = data.get("reason") or "-"
            elif event_type == "tool_call":
                entry["tool_call"] = data.get("tool") or "unknown"
            elif event_type == "tool_result":
                entry["tool_result"] = data.get("tool") or "unknown"

        if not agent_id or not node or not event_type:
            return

        label = agent_id.replace("_", " ").upper()
        node_kind = self._node_kind(node)

        if event_type == "node_start":
            prev = self._last_node_by_agent.get(agent_id)
            if prev and prev != node:
                self.call_from_thread(
                    self._append_log_line,
                    f"[{label}] EDGE {prev} -> {node}",
                )
            self._last_node_by_agent[agent_id] = node

            input_data = data.get("input")
            if input_data:
                rendered = self._format_kv(input_data)
                self.call_from_thread(
                    self._append_log_line,
                    f"[{label}] {node} ({node_kind}) input: {rendered}",
                )
            else:
                self.call_from_thread(
                    self._append_log_line,
                    f"[{label}] {node} ({node_kind}) input: -",
                )
            return

        if event_type == "node_end":
            output_data = data.get("output")
            if output_data:
                rendered = self._format_kv(output_data)
                self.call_from_thread(
                    self._append_log_line,
                    f"[{label}] {node} ({node_kind}) output: {rendered}",
                )
            else:
                self.call_from_thread(
                    self._append_log_line,
                    f"[{label}] {node} ({node_kind}) output: -",
                )

    def _current_agent_id(self) -> str:
        return self._agent_ids[self._current_agent_index]

    def _update_decision_header(self) -> None:
        agent_id = self._current_agent_id()
        header = f"Agent: {agent_id}"
        self.query_one("#decision-title", Static).update(header)

    def _goal_options(self) -> list[Option]:
        agent_id = self._current_agent_id()
        cfg = self._runner.registry.get_config(agent_id)
        allowed_goals = get_agent_spec(agent_id).allowed_goals

        options = []
        for goal in AgentGoal:
            if goal not in allowed_goals:
                continue
            marker = " (current)" if goal == cfg.goal else ""
            label = Text(f"{goal.name}{marker}")
            if goal == cfg.goal:
                label.stylize("bold yellow")
            options.append(Option(label, id=_goal_option_id(goal)))
        return options

    def _priority_options(self) -> list[Option]:
        agent_id = self._current_agent_id()
        cfg = self._runner.registry.get_config(agent_id)
        options = []
        for priority in PriorityLevel:
            marker = " (current)" if priority == cfg.priority else ""
            label = Text(f"{priority.name}{marker}")
            if priority == cfg.priority:
                label.stylize("bold yellow")
            options.append(Option(label, id=_priority_option_id(priority)))
        return options

    def _refresh_decision_list(self) -> None:
        option_list = self.query_one("#decision-list", OptionList)
        option_list.clear_options()

        options = (
            self._goal_options()
            if self._decision_phase == GOAL_PHASE
            else self._priority_options()
        )
        option_list.add_options(options)
        self._highlighted_option_id = options[0].id if options else None
        self._update_decision_header()

    def _apply_selection(self) -> None:
        option_id = self._highlighted_option_id
        if not option_id:
            return

        agent_id = self._current_agent_id()
        cfg = self._runner.registry.get_config(agent_id)

        if self._decision_phase == GOAL_PHASE:
            goal_name = option_id.split(":", 1)[1]
            self._selected_goal = AgentGoal[goal_name]
            self._decision_phase = PRIORITY_PHASE
            self._refresh_decision_list()
            return

        if self._decision_phase == PRIORITY_PHASE:
            priority_name = option_id.split(":", 1)[1]
            selected_priority = PriorityLevel[priority_name]

            goal = self._selected_goal or cfg.goal
            self._pending_decisions.append(
                PlayerDecision(
                    agent_id=agent_id,
                    goal=goal,
                    priority=selected_priority,
                )
            )

            self._advance_or_run_turn()

    def _advance_or_run_turn(self) -> None:
        if self._current_agent_index < len(self._agent_ids) - 1:
            self._current_agent_index += 1
            self._decision_phase = GOAL_PHASE
            self._selected_goal = None
            self._refresh_decision_list()
            return

        decisions = list(self._pending_decisions)
        self._pending_decisions.clear()
        self._current_agent_index = 0
        self._decision_phase = GOAL_PHASE
        self._selected_goal = None

        self._run_turn(decisions)

    def _run_turn(self, decisions: list[PlayerDecision]) -> None:
        if self._running_turn:
            return
        self._running_turn = True
        self._turn_agent_events = {}
        self._last_node_by_agent = {}
        option_list = self.query_one("#decision-list", OptionList)
        option_list.disabled = True
        self._append_log_line("")
        self._append_log_line("--- SYSTEM EXECUTION ---")
        self._append_log_line("[SYSTEM] Running turn...")
        self._set_terminal_loading(True)

        def _worker() -> None:
            result = self._runner.step(decisions)
            self.call_from_thread(self._apply_turn_result, result)

        self.run_worker(_worker, thread=True)

    def _apply_turn_result(self, result) -> None:
        self._running_turn = False
        option_list = self.query_one("#decision-list", OptionList)
        option_list.disabled = False
        self._set_terminal_loading(False)

        turn_done = result.state.turn - 1
        self._append_log_line(f"[SYSTEM] Turn {turn_done} complete.")
        self._update_status_bar(result)

        if result.ending:
            ending_label = result.ending.type.value.replace("_", " ").title()
            self._append_log_line(f"[ENDING] {ending_label}")
            self._append_log_line(result.ending.reason)
            self._game_over = True
            return

        self._refresh_decision_list()

    def _update_status_bar(self, result=None) -> None:
        if result is None:
            state = self._runner.state
            tension = self._runner.tension
            earth_pressure = self._runner.earth.pressure
            solaris_intensity = self._runner.solaris.intensity
        else:
            state = result.state
            tension = result.tension
            earth_pressure = result.earth_pressure
            solaris_intensity = result.solaris_intensity

        drift_bits = []
        for agent_id, runtime in self._runner.registry.runtime.items():
            drift_bits.append(f"{agent_id} {runtime.drift:.2f}")
        drift_text = " | ".join(drift_bits)

        status_lines = [
            f"Turn: {state.turn}",
            f"Tension: {tension:.3f}",
            f"Earth: {earth_pressure:.3f}",
            f"Solaris: {solaris_intensity:.3f}",
            f"Crew: stress {state.crew.stress:.3f}, fatigue {state.crew.fatigue:.3f}",
            f"Ocean: activity {state.ocean.activity:.3f}, instability {state.ocean.instability:.3f}",
            f"Power: {state.station.power_level:.3f}",
            f"Drift: {drift_text}",
        ]
        status = "\n".join(status_lines)
        self.query_one("#status-bar", Static).update(status)
        if result is not None:
            self._update_world_bar(result)
        else:
            self.query_one("#world-bar", Static).update("")
        self._set_panel_titles()

    def _set_panel_titles(self) -> None:
        self.query_one("#left-panel", Container).border_title = "Decisions"
        self.query_one("#right-panel", Container).border_title = "Terminal"
        self.query_one("#status-panel", Container).border_title = "System"
        self.query_one("#world-panel", Container).border_title = "World Updates"

    def _append_debug_sections(self, result) -> None:
        flags = result.state.flags

        tension_debug = flags.get("tension_debug") or []
        if tension_debug:
            self._append_log_line("")
            self._append_log_line("--- TENSION DEBUG ---")
            for d in tension_debug:
                self._append_log_line(
                    f"Tension {d['previous']} -> {d['next']} "
                    f"({d['delta']:+}) | reason: {d['reason']}"
                )

        earth_debug = flags.get("earth_debug") or []
        if earth_debug:
            self._append_log_line("")
            self._append_log_line("--- EARTH PRESSURE DEBUG ---")
            for d in earth_debug:
                self._append_log_line(
                    f"Earth pressure {d['previous']} -> {d['next']} "
                    f"({d['delta']:+}) | reason: {d['reason']} "
                    f"| tension={d['tension']}"
                )

        ocean_debug = flags.get("ocean_debug") or []
        if ocean_debug:
            self._append_log_line("")
            self._append_log_line("--- OCEAN DEBUG ---")
            for d in ocean_debug:
                self._append_log_line(
                    f"{d['parameter']} {d['delta']:+} | reason: {d['reason']} "
                    f"| tension={d['tension']}"
                )

        drift_debug = flags.get("drift_debug") or []
        if drift_debug:
            self._append_log_line("")
            self._append_log_line("--- DRIFT DEBUG ---")
            for d in drift_debug:
                self._append_log_line(
                    f"{d['agent_id']} {d['previous']} -> {d['next']} "
                    f"({d['delta']:+}) | reason: {d['reason']}"
                )

    def _set_terminal_loading(self, active: bool) -> None:
        loading = self.query_one("#terminal-loading", Horizontal)
        loading.display = active

    def _append_turn_summary(self, result, turn_done: int) -> None:
        state = result.state
        self._append_log_line("")
        self._append_log_line(f"TURN {turn_done} - AGENT ACTIONS")

        for agent_id in self._agent_ids:
            label = agent_id.replace("_", " ").title()
            events = self._turn_agent_events.get(agent_id, {})
            report = result.reports.get(agent_id, "")

            self._append_log_line("")
            self._append_log_line(label)

            if agent_id == "instrument_specialist":
                self._append_log_line(
                    "  read_context: "
                    f"ocean activity {state.ocean.activity:.3f} (low), "
                    f"instability {state.ocean.instability:.3f} (low), "
                    f"power {state.station.power_level:.2f}"
                )
            elif agent_id == "crew_officer":
                self._append_log_line(
                    "  read_context: "
                    f"stress {state.crew.stress:.2f}, "
                    f"fatigue {state.crew.fatigue:.2f}, "
                    f"drift {result.drift_levels.get(agent_id, 0.0):.2f}, "
                    f"solaris {result.solaris_intensity:.2f}"
                )

            decision_tool = events.get("decision_tool")
            decision_reason = events.get("decision_reason")
            if decision_tool:
                self._append_log_line(f"  decide_tool: {decision_tool}")
                self._append_log_line(f"    reason: {decision_reason}")

            tool_call = events.get("tool_call")
            tool_result = events.get("tool_result")
            if tool_call:
                status = "OK" if tool_result == tool_call else "..."
                self._append_log_line(f"  apply_tool: {tool_call} -> {status}")

            if report:
                summary = self._summarize_observation(report)
                self._append_log_line(f"  observe: {summary}")


    def _summarize_observation(self, report: str) -> str:
        text = report.strip()
        if not text:
            return "-"
        first_line = text.splitlines()[0].strip()
        if len(first_line) > 120:
            return first_line[:117] + "..."
        return first_line

    def _node_kind(self, node: str) -> str:
        llm_nodes = {
            "observe",
            "update_hypothesis",
        }
        return "LLM" if node in llm_nodes else "deterministic"

    def _format_kv(self, payload: dict) -> str:
        parts = []
        for key in sorted(payload.keys()):
            value = payload[key]
            parts.append(f"{key}={self._format_value(value)}")
        return ", ".join(parts)

    def _format_value(self, value) -> str:
        if isinstance(value, float):
            return f"{value:.4f}"
        if isinstance(value, dict):
            return "{" + self._format_kv(value) + "}"
        if isinstance(value, str):
            return f"\"{self._compact_text(value)}\""
        return str(value)

    def _compact_text(self, text: str, limit: int = 120) -> str:
        single = " ".join(text.split())
        if len(single) <= limit:
            return single
        return single[: limit - 3] + "..."

    def _update_world_bar(self, result) -> None:
        flags = result.state.flags
        lines: list[str] = []

        tension_debug = flags.get("tension_debug") or []
        for d in tension_debug:
            lines.append(
                "  tension "
                f"{d['previous']} -> {d['next']} "
                f"({d['delta']:+}) | {d['reason']}"
            )

        earth_debug = flags.get("earth_debug") or []
        for d in earth_debug:
            lines.append(
                "  earth pressure "
                f"{d['previous']} -> {d['next']} "
                f"({d['delta']:+}) | {d['reason']} "
                f"(tension={d['tension']})"
            )

        ocean_debug = flags.get("ocean_debug") or []
        for d in ocean_debug:
            lines.append(
                f"  ocean {d['parameter']} {d['delta']:+} | "
                f"{d['reason']} (tension={d['tension']})"
            )

        drift_debug = flags.get("drift_debug") or []
        for d in drift_debug:
            lines.append(
                "  drift "
                f"{d['agent_id']} {d['previous']} -> {d['next']} "
                f"({d['delta']:+}) | {d['reason']}"
            )

        self.query_one("#world-bar", Static).update("\n".join(lines))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id != "terminal-copy":
            return
        if self._copy_terminal_log():
            self._append_log_line("[SYSTEM] Terminal log copied to clipboard.")
        else:
            self._append_log_line("[SYSTEM] Failed to copy terminal log.")

    def _copy_terminal_log(self) -> bool:
        text = "\n".join(self._terminal_lines)
        if sys.platform == "win32":
            try:
                subprocess.run(
                    ["clip"],
                    input=text,
                    text=True,
                    check=True,
                )
                return True
            except Exception:
                pass

        try:
            self.copy_to_clipboard(text)
            return True
        except Exception:
            pass

        try:
            import tkinter as tk

            root = tk.Tk()
            root.withdraw()
            root.clipboard_clear()
            root.clipboard_append(text)
            root.update()
            root.destroy()
            return True
        except Exception:
            return False


if __name__ == "__main__":
    app = SolarisTUI()
    app.run()
