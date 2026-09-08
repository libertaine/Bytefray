from __future__ import annotations

from pathlib import Path

from battle_engine.paths import canonical_replay_directory
from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from app.services.agent_catalog import AgentRow
from app.services.engine import RunConfig
from app.services.osutil import get_default_paths
from app.services.ruleset_options import (
    VM_RULESET_EXPLANATION,
    agent_row_supported_by_ruleset,
)
from app.widgets.agent_combo import (
    repopulate_paired_agent_combos,
    selected_agent_kind,
    selected_agent_name,
    sync_compatible_b_choices,
)
from app.widgets.json_editor import JsonEditor
from app.widgets.ruleset_combo import (
    populate_ruleset_combo,
    selected_ruleset_id,
)

# Placeholder shown in the Replay Browser's path label before any replay has
# been chosen -- deliberately not a real path (so accidentally treating it as
# one is harmless: Path(...).is_file() is False for it) and checked for
# explicitly in _open_replay_browser so that case gets its own clear message
# rather than a "Replay not found: No replay selected yet." dialog.
_NO_REPLAY_SELECTED = "No replay selected yet."


class AdvancedPanel(QWidget):
    """Advanced mode with tabs: Setup, Agent Params, Replay Browser, Results."""

    runRequested = Signal(RunConfig)
    stopRequested = Signal()
    openReplayRequested = Signal()
    refreshAgentsRequested = Signal()

    def __init__(self, catalog, data_root: Path) -> None:
        super().__init__()
        self._catalog = catalog
        self._paths = get_default_paths(data_root)
        # The current Designer session's most recently completed successful
        # match replay, if any -- purely a hint for the Replay Browser's
        # initial directory (UX-24 priority #2), set by note_completed_replay.
        # Independent of "View Last Match" (enableOpenReplay), which is
        # driven by AgentDesigner's own _last_replay.
        self._session_replay_path: Path | None = None
        self._all_rows: list[AgentRow] = []
        # Whether the selected Ruleset has any compatible discovered agent;
        # recomputed by _refilter_agents and respected by setBusy.
        self._has_eligible_agents = False

        root = QVBoxLayout(self)
        self.tabs = QTabWidget()
        root.addWidget(self.tabs)

        # ---- Match Setup ----
        setup = QWidget()
        form = QFormLayout(setup)

        # Ruleset is the controlling selector (UX-14/UX-15): it is
        # established before Agent A/B so a first-time user learns the same
        # "Ruleset determines which Agents can participate" rule Simple
        # already teaches, rather than the reverse.
        self.ruleset = QComboBox()
        populate_ruleset_combo(self.ruleset)
        self.rulesetExplanation = QLabel()
        self.rulesetExplanation.setWordWrap(True)
        form.addRow("Ruleset", self.ruleset)
        form.addRow("", self.rulesetExplanation)

        self.agentA = QComboBox()
        self.agentB = QComboBox()
        form.addRow("Agent A", self.agentA)
        form.addRow("Agent B", self.agentB)

        self.arena = QSpinBox()
        self.arena.setRange(64, 8192)
        self.arena.setValue(512)
        self.arena.setToolTip(
            "Side length of the square arena, in cells. A larger arena gives "
            "agents more room to maneuver; a smaller one forces conflict "
            f"sooner. GUI limit: {self.arena.minimum()}-{self.arena.maximum()}; "
            "the engine itself only requires an arena larger than 1 cell."
        )
        form.addRow("Arena Size", self.arena)

        self.ticks = QSpinBox()
        self.ticks.setRange(1, 100000)
        self.ticks.setValue(600)
        self.ticks.setToolTip(
            "Maximum number of simulation ticks before the match ends, "
            "subject to the selected Ruleset's win condition."
        )
        form.addRow("Ticks", self.ticks)

        self.alive_w = QDoubleSpinBox()
        self.alive_w.setRange(0.0, 1000.0)
        self.alive_w.setDecimals(3)
        self.alive_w.setValue(1.0)
        self.alive_w.setToolTip(
            "Points added to a surviving agent's score every tick. Higher "
            "values reward staying alive longer. Starting value shown here: "
            f"{self.alive_w.value():g}."
        )
        self.kill_w = QDoubleSpinBox()
        self.kill_w.setRange(0.0, 1000.0)
        self.kill_w.setDecimals(3)
        self.kill_w.setValue(1.0)
        self.kill_w.setToolTip(
            "Points awarded to an agent immediately when it eliminates an "
            "opponent. Starting value shown here: "
            f"{self.kill_w.value():g}."
        )
        self.territory_w = QDoubleSpinBox()
        self.territory_w.setRange(0.0, 1000.0)
        self.territory_w.setDecimals(3)
        self.territory_w.setValue(1.0)
        self.territory_w.setToolTip(
            "Points added every tick for each Territory Bucket Size worth of "
            "arena cells an agent owns, whether or not that agent is still "
            "alive. Set to 0 to turn off territory scoring entirely. "
            f"Starting value shown here: {self.territory_w.value():g}."
        )
        form.addRow("Survival Weight", self.alive_w)
        form.addRow("Kill Weight", self.kill_w)
        form.addRow("Territory Weight", self.territory_w)

        self.territory_bucket = QSpinBox()
        self.territory_bucket.setRange(1, 4096)
        self.territory_bucket.setValue(32)
        self.territory_bucket.setToolTip(
            "Number of owned arena cells that make up one territory-scoring "
            "block. Smaller values convert owned territory into points more "
            "readily; larger values require controlling more cells before "
            f"Territory Weight points accrue. Starting value shown here: "
            f"{self.territory_bucket.value()}."
        )
        form.addRow("Territory Bucket Size", self.territory_bucket)

        self.seed = QSpinBox()
        self.seed.setRange(0, 1_000_000)
        self.seed.setValue(0)
        self.seed.setToolTip(
            "Sets the deterministic seed for this match's randomness. Using "
            "the same configuration and seed reproduces the same match. A "
            "value of 0 does not pick a fresh random seed -- it uses the "
            "engine's own built-in default seed, so repeated runs left at 0 "
            "are still reproducible, not randomized."
        )
        form.addRow("Random Seed (0 = default)", self.seed)

        btns = QHBoxLayout()
        self.btnRun = QPushButton("Run Match")
        self.btnStop = QPushButton("Stop")
        self.btnOpen = QPushButton("View Last Match")
        self.btnOpen.setEnabled(False)
        self.btnOpen.setToolTip(
            "Opens the replay from your most recently completed successful "
            "match. Stays on that match's replay if a later match fails, so "
            "it never opens a replay a failed run does not actually have."
        )
        self.btnRefresh = QPushButton("Refresh Agents")
        btns.addWidget(self.btnRun)
        btns.addWidget(self.btnStop)
        btns.addWidget(self.btnOpen)
        btns.addWidget(self.btnRefresh)
        form.addRow(btns)

        self.tabs.addTab(setup, "Match Setup")

        # ---- Agent Params ----
        params = QWidget()
        pv = QVBoxLayout(params)
        paramsIntro = QLabel(
            "Optional settings that change how supported agents behave "
            "during a match. Not every agent reads these -- an agent that "
            "does not use parameters simply ignores them. Leave a field "
            "empty for that agent's own defaults."
        )
        paramsIntro.setWordWrap(True)
        pv.addWidget(paramsIntro)
        self.editorA = JsonEditor(title="Agent A Params (JSON)")
        self.editorB = JsonEditor(title="Agent B Params (JSON)")
        pv.addWidget(self.editorA)
        pv.addWidget(self.editorB)
        self.tabs.addTab(params, "Agent Params")

        # ---- Replay Browser ----
        replay = QWidget()
        rl = QVBoxLayout(replay)
        replayIntro = QLabel(
            "Browse saved Bytefray match replays. Agent Designer creates one "
            "automatically each time you run a match. Select a replay file, "
            "then view it here."
        )
        replayIntro.setWordWrap(True)
        rl.addWidget(replayIntro)
        row = QHBoxLayout()
        self.lblReplay = QLabel(_NO_REPLAY_SELECTED)
        self.btnChooseReplay = QPushButton("Choose Replay…")
        self.btnOpenReplay = QPushButton("View Replay")
        row.addWidget(self.lblReplay, 1)
        row.addWidget(self.btnChooseReplay)
        row.addWidget(self.btnOpenReplay)
        rl.addLayout(row)
        self.tabs.addTab(replay, "Replay Browser")

        # ---- Results ----
        results = QWidget()
        rv = QVBoxLayout(results)
        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Field", "Value"])
        self.table.horizontalHeader().setStretchLastSection(True)

        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setMaximumBlockCount(10000)
        group = QGroupBox("Engine Log")
        gl = QVBoxLayout(group)
        gl.addWidget(self.log)

        rv.addWidget(self.table, 1)
        rv.addWidget(group)
        self.tabs.addTab(results, "Results")

        # Signals
        self.btnRun.clicked.connect(self._emit_run)
        self.btnStop.clicked.connect(self.stopRequested.emit)
        self.btnOpen.clicked.connect(self.openReplayRequested.emit)
        self.btnRefresh.clicked.connect(self.refreshAgentsRequested.emit)
        self.btnChooseReplay.clicked.connect(self._choose_replay)
        self.btnOpenReplay.clicked.connect(self._open_replay_browser)
        self.ruleset.currentIndexChanged.connect(self._on_ruleset_changed)
        self.agentA.currentIndexChanged.connect(self._on_agent_a_changed)

    # API for MainWindow
    def setAgents(self, rows: list[AgentRow]) -> None:
        self._all_rows = list(rows)
        self._refilter_agents()

    def _on_ruleset_changed(self, _index: int) -> None:
        self._refilter_agents()

    def _on_agent_a_changed(self, _index: int) -> None:
        sync_compatible_b_choices(self.agentA, self.agentB)
        self._update_ruleset_explanation()

    def _refilter_agents(self) -> None:
        """Populate Agent A/B from the selected Ruleset's compatible agents.

        The Ruleset is the controlling selector (UX-15/UX-16): changing it
        never happens as a side effect of an agent choice, only the
        reverse. ``repopulate_paired_agent_combos`` is the same shared
        helper Simple uses (UX-19 parity): it preserves each combo's own
        selection when it remains eligible and steers Agent B to a
        deterministic opponent distinct from Agent A otherwise. Within the
        Ruleset-compatible roster, ``sync_compatible_b_choices`` still
        applies the pre-existing runtime-kind restriction on Agent B: Ruleset
        v1 is the one identity that admits both Python and VM/blob agents,
        which still may not be mixed in the same match
        (``validate_homogeneous`` at launch), so that check is layered on
        top rather than replaced.
        """

        ruleset_id = selected_ruleset_id(self.ruleset)
        eligible = [
            row
            for row in self._all_rows
            if agent_row_supported_by_ruleset(row, ruleset_id)
        ]
        repopulate_paired_agent_combos(self.agentA, self.agentB, eligible)
        sync_compatible_b_choices(self.agentA, self.agentB)

        self._has_eligible_agents = bool(eligible)
        self.btnRun.setEnabled(self._has_eligible_agents)
        self._update_ruleset_explanation()

    def _update_ruleset_explanation(self) -> None:
        if not self._has_eligible_agents:
            self.rulesetExplanation.setText(
                "No compatible agents were found for this Ruleset. "
                "Create or import a compatible agent, then refresh."
            )
        elif "vm" in (selected_agent_kind(self.agentA), selected_agent_kind(self.agentB)):
            # Only Ruleset v1 offers both kinds; explains why some Agent B
            # entries are grayed out when a VM/blob agent is selected.
            self.rulesetExplanation.setText(VM_RULESET_EXPLANATION)
        else:
            self.rulesetExplanation.clear()

    def setBusy(self, busy: bool) -> None:
        for w in (
            self.btnRefresh,
            self.agentA,
            self.agentB,
            self.arena,
            self.ticks,
            self.alive_w,
            self.kill_w,
            self.territory_w,
            self.territory_bucket,
            self.seed,
            self.ruleset,
        ):
            w.setEnabled(not busy)
        # Run stays disabled while no compatible agents exist, so becoming
        # idle never re-enables launching an invalid selection.
        self.btnRun.setEnabled(not busy and self._has_eligible_agents)
        self.btnStop.setEnabled(busy)

    def enableOpenReplay(self, enable: bool) -> None:
        self.btnOpen.setEnabled(enable)

    def note_completed_replay(self, path: Path | None) -> None:
        """Record the current session's most recently completed successful
        match replay -- used only to steer Choose Replay's initial directory
        (UX-24 priority #2) toward a replay the user just produced, never to
        change what "View Last Match" opens (that stays AgentDesigner's own
        responsibility)."""
        self._session_replay_path = Path(path) if path else None

    def appendLog(self, line: str) -> None:
        self.log.appendPlainText(line.rstrip("\n"))

    def load_results(self) -> None:
        from app.services.osutil import read_summary_json

        data = read_summary_json(self._paths.summary_path)
        if data is None:
            return
        # Populate table
        self.table.setRowCount(0)
        for k in [
            "winner",
            "ticks",
            "A_score",
            "B_score",
            "A_territory",
            "B_territory",
            "seed",
        ]:
            if k in data:
                r = self.table.rowCount()
                self.table.insertRow(r)
                self.table.setItem(r, 0, QTableWidgetItem(k))
                self.table.setItem(r, 1, QTableWidgetItem(str(data[k])))

    def show_result(self, result) -> None:
        """Display the small canonical-result subset useful during normal runs."""
        values = (
            ("winner", result.winner),
            ("termination_reason", result.termination_reason),
            ("result", result.result_path),
            ("replay", result.replay_path or "not available"),
        )
        self.table.setRowCount(0)
        for key, value in values:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(key))
            self.table.setItem(row, 1, QTableWidgetItem(str(value)))

    # Helpers
    def _emit_run(self) -> None:
        cfg = RunConfig(
            a_type=selected_agent_name(self.agentA) or "runner",
            b_type=selected_agent_name(self.agentB) or "writer",
            ruleset_id=selected_ruleset_id(self.ruleset),
            arena=int(self.arena.value()),
            ticks=int(self.ticks.value()),
            alive_w=float(self.alive_w.value()),
            kill_w=float(self.kill_w.value()),
            territory_w=float(self.territory_w.value()),
            territory_bucket=int(self.territory_bucket.value()),
            seed=int(self.seed.value()) or None,
            a_params=self.editorA.get_data_or_none(),
            b_params=self.editorB.get_data_or_none(),
        )
        self.runRequested.emit(cfg)

    def _initial_replay_directory(self) -> Path:
        """Where Choose Replay should start browsing (UX-24).

        Priority: 1) the directory of the currently selected replay, if it
        still exists; 2) the directory of this session's own most recent
        successful match replay (note_completed_replay); 3) Bytefray's
        canonical replay/run directory; 4) the writable data root itself --
        the latter two both handled by canonical_replay_directory, which
        never returns a nonexistent path.
        """
        current_text = self.lblReplay.text().strip()
        if current_text and current_text != _NO_REPLAY_SELECTED:
            current = Path(current_text)
            if current.is_file():
                return current.parent
        if self._session_replay_path is not None and self._session_replay_path.is_file():
            return self._session_replay_path.parent
        return canonical_replay_directory(self._paths.root)

    def _choose_replay(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Choose Replay",
            str(self._initial_replay_directory()),
            "Bytefray Replays (*.jsonl)",
        )
        if path:
            self.lblReplay.setText(path)

    def _open_replay_browser(self) -> None:
        from app.services.engine import open_pygame_client_direct

        text = self.lblReplay.text().strip()
        if not text or text == _NO_REPLAY_SELECTED:
            QMessageBox.information(self, "No Replay Selected", "Choose a replay first.")
            return
        path = Path(text)
        if not path.is_file():
            QMessageBox.critical(self, "Replay Not Found", f"Replay not found:\n{path}")
            return
        try:
            open_pygame_client_direct(self._paths.root, path)
        except (FileNotFoundError, OSError) as exc:
            QMessageBox.critical(self, "Replay Launch Failed", str(exc))
