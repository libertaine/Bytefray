from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.services.agent_catalog import AgentRow
from app.services.engine import RunConfig
from app.services.ruleset_options import (
    NO_COMPATIBLE_AGENTS_EXPLANATION,
    agent_row_supported,
)
from app.widgets.agent_combo import (
    repopulate_paired_agent_combos,
    selected_agent_name,
)
from app.widgets.designer_presentation import MatchOutputView

GRID_PRESETS = {
    "Small (256)": 256,
    "Medium (512)": 512,
    "Large (1024)": 1024,
}

TICK_PRESETS = [300, 600, 1200]


class SimplePanel(QWidget):
    """Simple mode panel with minimal controls and a live log."""

    runRequested = Signal(RunConfig)
    stopRequested = Signal()
    openReplayRequested = Signal()
    refreshAgentsRequested = Signal()

    def __init__(self, catalog) -> None:  # catalog kept for future use
        super().__init__()
        self._all_rows: list[AgentRow] = []
        self._has_eligible_agents = False

        root = QVBoxLayout(self)

        # Match configuration and actions
        controls = QGroupBox("Quick Match")
        controls_layout = QVBoxLayout(controls)
        controls_layout.setContentsMargins(12, 12, 12, 12)
        controls_layout.setSpacing(10)
        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(4)

        # Shown only when no discovered agent can run.
        self.compatibilityExplanation = QLabel()
        self.compatibilityExplanation.setWordWrap(True)
        grid.addWidget(self.compatibilityExplanation, 0, 0, 1, 4)

        agent_a_label = QLabel("Agent A")
        self.agentA = QComboBox()
        agent_a_label.setBuddy(self.agentA)
        grid.addWidget(agent_a_label, 1, 0)
        grid.addWidget(self.agentA, 2, 0, 1, 2)

        agent_b_label = QLabel("Agent B")
        self.agentB = QComboBox()
        agent_b_label.setBuddy(self.agentB)
        grid.addWidget(agent_b_label, 1, 2)
        grid.addWidget(self.agentB, 2, 2, 1, 2)

        arena_size_label = QLabel("Arena Size")
        self.gridSize = QComboBox()
        for k in GRID_PRESETS:
            self.gridSize.addItem(k)
        self.gridSize.setCurrentIndex(1)  # Medium
        self.gridSize.setToolTip(
            "How large a square arena the match runs in. A larger arena gives "
            "agents more room to maneuver and hide; a smaller one forces "
            "conflict sooner."
        )
        arena_size_label.setBuddy(self.gridSize)
        grid.addWidget(arena_size_label, 3, 0)
        grid.addWidget(self.gridSize, 4, 0, 1, 2)

        ticks_label = QLabel("Ticks")
        self.ticks = QComboBox()
        for t in TICK_PRESETS:
            self.ticks.addItem(str(t), userData=t)
        self.ticks.setCurrentIndex(1)
        ticks_label.setBuddy(self.ticks)
        grid.addWidget(ticks_label, 3, 2)
        grid.addWidget(self.ticks, 4, 2, 1, 2)
        grid.setColumnStretch(0, 2)
        grid.setColumnStretch(1, 2)
        grid.setColumnStretch(2, 1)
        grid.setColumnStretch(3, 1)
        controls_layout.addLayout(grid)

        # UX-28: Simple stays deliberately 2-agent (UX-27) -- this is the
        # one small, unobtrusive pointer to where a larger roster is
        # actually configured, not a feature Simple itself gains.
        self.multiAgentHint = QLabel(
            "Simple runs 2-agent matches. Use Advanced to add a third agent."
        )
        self.multiAgentHint.setWordWrap(True)
        hint_font = self.multiAgentHint.font()
        hint_font.setItalic(True)
        self.multiAgentHint.setFont(hint_font)
        controls_layout.addWidget(self.multiAgentHint)

        self.btnRun = QPushButton("Run Match")
        run_font = self.btnRun.font()
        run_font.setBold(True)
        self.btnRun.setFont(run_font)
        self.btnRun.setMinimumWidth(120)
        self.btnRun.setAccessibleDescription(
            "Run a match using the selected agents, arena size, and tick limit."
        )
        self.btnStop = QPushButton("Stop")
        self.btnOpen = QPushButton("View Last Match")
        self.btnOpen.setEnabled(False)
        self.btnOpen.setToolTip(
            "Opens the replay from your most recently completed successful "
            "match. Stays on that match's replay if a later match fails, so "
            "it never opens a replay a failed run does not actually have."
        )
        self.btnRefresh = QPushButton("Refresh Agents")

        actions = QHBoxLayout()
        actions.setSpacing(8)
        actions.addWidget(self.btnRun)
        actions.addWidget(self.btnStop)
        actions.addWidget(self.btnOpen)
        actions.addStretch(1)
        actions.addWidget(self.btnRefresh)
        controls_layout.addLayout(actions)

        root.addWidget(controls)

        # Output area: a real UI empty state, never placeholder log data.
        output_group = QGroupBox("Match Output")
        output_layout = QVBoxLayout(output_group)
        self.output = MatchOutputView(output_group)
        self.log = self.output.log  # Existing MainWindow/test compatibility surface.
        output_layout.addWidget(self.output)
        root.addWidget(output_group, 1)

        # Signals
        self.btnRun.clicked.connect(self._emit_run)
        self.btnStop.clicked.connect(self.stopRequested.emit)
        self.btnOpen.clicked.connect(self.openReplayRequested.emit)
        self.btnRefresh.clicked.connect(self.refreshAgentsRequested.emit)
        self.agentA.currentIndexChanged.connect(self._on_agent_a_changed)
        self.agentB.currentIndexChanged.connect(self._update_matchup_summary)
        self._update_matchup_summary()

    # API consumed by MainWindow
    def setAgents(self, rows: list[AgentRow]) -> None:
        self._all_rows = list(rows)
        self._refilter_agents()

    def _on_agent_a_changed(self, _index: int) -> None:
        self._update_matchup_summary()

    def _refilter_agents(self) -> None:
        """Populate both selectors from the agents that can run."""

        eligible = [row for row in self._all_rows if agent_row_supported(row)]
        repopulate_paired_agent_combos(self.agentA, self.agentB, eligible)

        self._has_eligible_agents = bool(eligible)
        self.btnRun.setEnabled(self._has_eligible_agents)
        self.compatibilityExplanation.setVisible(not self._has_eligible_agents)
        if eligible:
            self.compatibilityExplanation.clear()
        else:
            self.compatibilityExplanation.setText(NO_COMPATIBLE_AGENTS_EXPLANATION)
        self._update_matchup_summary()

    def _update_matchup_summary(self, _index: int | None = None) -> None:
        self.output.set_matchup(self.agentA.currentText(), self.agentB.currentText())

    def setBusy(self, busy: bool) -> None:
        for w in (
            self.btnRefresh,
            self.agentA,
            self.agentB,
            self.gridSize,
            self.ticks,
        ):
            w.setEnabled(not busy)
        self.btnRun.setEnabled(not busy and self._has_eligible_agents)
        self.btnStop.setEnabled(busy)

    def enableOpenReplay(self, enable: bool) -> None:
        self.btnOpen.setEnabled(enable)

    def appendLog(self, line: str) -> None:
        self.output.append_log(line)

    def clearLog(self) -> None:
        self.output.clear_log()

    # Helpers
    def _emit_run(self) -> None:
        agent_a = selected_agent_name(self.agentA)
        agent_b = selected_agent_name(self.agentB)
        if agent_a is None or agent_b is None:
            message = NO_COMPATIBLE_AGENTS_EXPLANATION
            self.appendLog(f"[RunMatch] {message}\n")
            self.compatibilityExplanation.setText(message)
            return
        arena = GRID_PRESETS[self.gridSize.currentText()]
        ticks = int(self.ticks.currentText())
        cfg = RunConfig(
            a_type=agent_a,
            b_type=agent_b,
            arena=arena,
            ticks=ticks,
        )
        self.runRequested.emit(cfg)
