from __future__ import annotations

from pathlib import Path
from typing import TypeVar

from battle_engine.agent_parameters import EMPTY_PARAMETER_SCHEMA
from battle_engine.config import Weights
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
from app.services.designer_workflows import (
    agent_parameter_schema,
    describe_effective_parameters,
    random_match_seed,
)
from app.services.engine import RunConfig
from app.services.osutil import get_default_paths
from app.services.ruleset_options import (
    VM_RULESET_EXPLANATION,
    agent_row_supported_by_ruleset,
)
from app.widgets.agent_combo import (
    repopulate_additional_agent_combo,
    repopulate_paired_agent_combos,
    selected_agent_kind,
    selected_agent_name,
    sync_compatible_b_choices,
)
from app.widgets.agent_parameters import AgentParameterForm
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

# Phase 5B: the canonical scoring defaults, read from the engine's own
# ``Weights`` dataclass rather than restated as GUI literals. Advanced
# previously hard-coded kill_w=1.0 and territory_bucket=32 -- values that
# never matched an engine default at any point in this repository's history
# -- and submitted them on every run, so merely opening Advanced scored the
# match differently from Simple and from a bare ``bytefray run``, changing
# scores and every derived match/replay/result identity with no user
# action. Reading the dataclass here means the displayed starting values
# cannot drift from the engine again. Weights are per-match configuration
# and explicitly *not* Ruleset identity (see ``rules.py``'s "Configuration
# values are not Ruleset identity"), so this one default set is correct for
# every Ruleset the Designer offers.
ENGINE_DEFAULT_WEIGHTS = Weights()

_Number = TypeVar("_Number", float, int)


def _weight_override(value: _Number, default: _Number) -> _Number | None:
    """Return ``value``, or ``None`` when it still equals ``default``.

    Advanced sends a scoring flag only when the user has actually moved
    that field off the engine's own default. When it matches, the flag is
    omitted entirely and ``bytefray run`` applies its canonical default --
    byte-identical to Simple, which never sends these flags at all, and to
    a bare CLI invocation. Comparing against the default rather than
    tracking an "edited" flag also means typing the default value back in
    restores exact default behavior, with no stale dirty state to get
    wrong, and keeps programmatic ``setValue`` (tests, future presets)
    behaving the same as a human edit.
    """
    return None if value == default else value


# Phase 4: Advanced's roster minimum/maximum. Not an arbitrary GUI choice --
# it is exactly the entrant-slot ceiling ``bytefray run``'s CLI already
# implements today (``--a-type``/``--b-type``/``--c-type``, cli.py). The
# engine's own match representation (``MatchRequest.entrants``) has no
# fixed maximum, but the single-match CLI surface the Designer launches
# through does; going past three would mean adding new CLI flags that do
# not exist yet, which is out of scope for exposing this already-wired
# capability. See the Phase 4 completion report for the full rationale.
ADVANCED_MIN_ROSTER = 2
ADVANCED_MAX_ROSTER = 3


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
        # Held so the three inputs to "may this match be launched" -- an
        # eligible roster, a running match, and valid agent parameters -- are
        # combined in one place (``_update_run_enabled``) instead of three
        # call sites each re-deciding part of the answer.
        self._busy = False

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

        # Phase 4 UX-29/UX-30/UX-31: Advanced's roster beyond the required
        # Agent A/B pair. Modeled as one additional named slot (Agent C)
        # rather than a general list widget -- ADVANCED_MAX_ROSTER is 3, so
        # a single optional slot is the smallest safe transition (preserves
        # every existing test's `panel.agentA`/`panel.agentB` attributes
        # unchanged) that still reaches the real roster ceiling. Hidden by
        # default: the minimum 2-agent state must not show a Remove button
        # that cannot be used.
        self.agentC = QComboBox()
        self._agentCContainer = QWidget()
        agent_c_row = QHBoxLayout(self._agentCContainer)
        agent_c_row.setContentsMargins(0, 0, 0, 0)
        self.btnRemoveAgentC = QPushButton("Remove")
        agent_c_row.addWidget(self.agentC, 1)
        agent_c_row.addWidget(self.btnRemoveAgentC)
        form.addRow("Agent C", self._agentCContainer)
        self._agentCLabel = form.labelForField(self._agentCContainer)

        self.btnAddAgent = QPushButton("+ Add Agent")
        form.addRow("", self.btnAddAgent)

        # Start hidden directly (rather than via _set_agent_c_visible,
        # which also toggles self.editorC -- not created until the Agent
        # Params tab below is built).
        self._agent_c_visible = False
        self._agentCContainer.setVisible(False)
        if self._agentCLabel is not None:
            self._agentCLabel.setVisible(False)

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
            "subject to the selected Ruleset's win condition. "
            f"GUI limit: {self.ticks.minimum()}-{self.ticks.maximum()}; the "
            "engine itself only requires a positive tick limit (at least 1) "
            "and has no maximum."
        )
        form.addRow("Ticks", self.ticks)

        self.alive_w = QDoubleSpinBox()
        self.alive_w.setRange(0.0, 1000.0)
        self.alive_w.setDecimals(3)
        self.alive_w.setValue(ENGINE_DEFAULT_WEIGHTS.alive)
        self.alive_w.setToolTip(
            "Points added to a surviving agent's score every tick. Higher "
            "values reward staying alive longer. Bytefray's default is "
            f"{ENGINE_DEFAULT_WEIGHTS.alive:g}; left at that value, the match "
            "runs with the engine's own default. "
            f"GUI limit: {self.alive_w.minimum():g}-{self.alive_w.maximum():g}; "
            "Bytefray does not define a maximum scoring weight, so this "
            "range is a practical UI bound, not a gameplay rule."
        )
        self.kill_w = QDoubleSpinBox()
        self.kill_w.setRange(0.0, 1000.0)
        self.kill_w.setDecimals(3)
        self.kill_w.setValue(ENGINE_DEFAULT_WEIGHTS.kill)
        self.kill_w.setToolTip(
            "Points awarded to an agent immediately when it eliminates an "
            "opponent. Bytefray's default is "
            f"{ENGINE_DEFAULT_WEIGHTS.kill:g}; left at that value, the match "
            "runs with the engine's own default. "
            f"GUI limit: {self.kill_w.minimum():g}-{self.kill_w.maximum():g}; "
            "Bytefray does not define a maximum scoring weight, so this "
            "range is a practical UI bound, not a gameplay rule."
        )
        self.territory_w = QDoubleSpinBox()
        self.territory_w.setRange(0.0, 1000.0)
        self.territory_w.setDecimals(3)
        self.territory_w.setValue(ENGINE_DEFAULT_WEIGHTS.territory)
        self.territory_w.setToolTip(
            "Points added every tick for each Territory Bucket Size worth of "
            "arena cells an agent owns, whether or not that agent is still "
            "alive. Set to 0 to turn off territory scoring entirely. "
            f"Bytefray's default is {ENGINE_DEFAULT_WEIGHTS.territory:g}; left "
            "at that value, the match runs with the engine's own default. "
            f"GUI limit: {self.territory_w.minimum():g}-"
            f"{self.territory_w.maximum():g}; Bytefray does not define a "
            "maximum scoring weight, so this range is a practical UI bound, "
            "not a gameplay rule."
        )
        form.addRow("Survival Weight", self.alive_w)
        form.addRow("Kill Weight", self.kill_w)
        form.addRow("Territory Weight", self.territory_w)

        self.territory_bucket = QSpinBox()
        self.territory_bucket.setRange(1, 4096)
        self.territory_bucket.setValue(ENGINE_DEFAULT_WEIGHTS.territory_bucket)
        self.territory_bucket.setToolTip(
            "Number of owned arena cells that make up one territory-scoring "
            "block. Smaller values convert owned territory into points more "
            "readily; larger values require controlling more cells before "
            "Territory Weight points accrue. Bytefray's default is "
            f"{ENGINE_DEFAULT_WEIGHTS.territory_bucket}; left at that value, "
            "the match runs with the engine's own default. "
            f"GUI limit: {self.territory_bucket.minimum()}-"
            f"{self.territory_bucket.maximum()}; Bytefray does not define a "
            "maximum bucket size, so this range is a practical UI bound, not "
            "a gameplay rule."
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
        # V5 Alpha 1 Phase E2. Randomness is an explicit action, never an
        # ambient one: the generated value lands in the field above, in plain
        # view, and from that moment is an ordinary typed seed. Nothing here
        # randomizes on its own, so a match is still reproducible from what
        # the user can see.
        self._seedRow = QWidget()
        seed_layout = QHBoxLayout(self._seedRow)
        seed_layout.setContentsMargins(0, 0, 0, 0)
        self.btnRandomizeSeed = QPushButton("Randomize")
        self.btnRandomizeSeed.setToolTip(
            "Pick a new random seed and put it in the field, so this match "
            "uses a fresh arrangement. The generated value stays visible and "
            "editable: running again with the same number reproduces the same "
            "match."
        )
        seed_layout.addWidget(self.seed, 1)
        seed_layout.addWidget(self.btnRandomizeSeed)
        form.addRow("Random Seed (0 = default)", self._seedRow)
        # The row is a layout container, not the input. Point the generated
        # label at the spin box itself so the label still names the field a
        # screen reader (and every existing label assertion) resolves through
        # its buddy, rather than at the box that happens to hold it.
        _seedLabel = form.labelForField(self._seedRow)
        if _seedLabel is not None:
            _seedLabel.setBuddy(self.seed)

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
            "Optional settings that change how the selected agents behave "
            "during a match. An agent that declares parameters in its "
            "manifest gets controls generated from that declaration, with its "
            "own defaults, ranges and presets. An agent that declares none "
            "keeps the free-form field below it; leave that empty, and leave "
            "any generated control alone, for the agent's own defaults."
        )
        paramsIntro.setWordWrap(True)
        pv.addWidget(paramsIntro)
        # Two surfaces per slot, exactly one visible at a time (V5 Alpha 1
        # Phase E1): generated controls for an agent that declares a schema,
        # and the pre-existing free-form JSON editor for one that does not.
        # The legacy editor is kept rather than replaced -- Agent API v1
        # agents, VM/blob agents and any un-migrated v2 agent still use it,
        # and forcing them through a schema they never declared would break a
        # working path.
        self.schemaA = AgentParameterForm("Agent A Parameters")
        self.schemaB = AgentParameterForm("Agent B Parameters")
        self.schemaC = AgentParameterForm("Agent C Parameters")
        self.editorA = JsonEditor(title="Agent A Params (JSON)")
        self.editorB = JsonEditor(title="Agent B Params (JSON)")
        self.editorC = JsonEditor(title="Agent C Params (JSON)")
        for schema_form, editor in (
            (self.schemaA, self.editorA),
            (self.schemaB, self.editorB),
            (self.schemaC, self.editorC),
        ):
            pv.addWidget(schema_form)
            pv.addWidget(editor)
            schema_form.setVisible(False)
        self.schemaC.setVisible(False)
        self.editorC.setVisible(False)
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
        self.btnRandomizeSeed.clicked.connect(self.randomize_seed)
        self.btnChooseReplay.clicked.connect(self._choose_replay)
        self.btnOpenReplay.clicked.connect(self._open_replay_browser)
        self.ruleset.currentIndexChanged.connect(self._on_ruleset_changed)
        self.agentA.currentIndexChanged.connect(self._on_agent_a_changed)
        self.btnAddAgent.clicked.connect(self._add_agent_slot)
        self.btnRemoveAgentC.clicked.connect(self._remove_agent_slot)
        # Every slot re-targets its own parameter surface when its selection
        # changes; Agent A additionally re-syncs the other slots' compatible
        # choices, which is why it keeps its own richer handler.
        for combo in (self.agentA, self.agentB, self.agentC):
            combo.currentIndexChanged.connect(self._on_agent_selection_changed)
        for schema_form in (self.schemaA, self.schemaB, self.schemaC):
            schema_form.changed.connect(self._update_run_enabled)
        self._sync_parameter_surfaces()

    @property
    def roster_size(self) -> int:
        """How many entrant slots are currently visible: 2 or 3 (Phase 4)."""
        return ADVANCED_MAX_ROSTER if self._agent_c_visible else ADVANCED_MIN_ROSTER

    # API for MainWindow
    def setAgents(self, rows: list[AgentRow]) -> None:
        self._all_rows = list(rows)
        self._refilter_agents()

    def _on_ruleset_changed(self, _index: int) -> None:
        self._refilter_agents()

    def _on_agent_a_changed(self, _index: int) -> None:
        sync_compatible_b_choices(self.agentA, self.agentB)
        if self._agent_c_visible:
            sync_compatible_b_choices(self.agentA, self.agentC)
        self._update_ruleset_explanation()

    # ---- Phase E1: schema-driven agent parameters ----
    def _on_agent_selection_changed(self, _index: int) -> None:
        self._sync_parameter_surfaces()

    def _row_for_slot(self, combo: QComboBox) -> AgentRow | None:
        """The catalog row behind one slot's current selection.

        Matched on the discovery identifier stored under the combo's user
        role, never on display text -- the same rule ``agent_combo`` states
        for every other consumer of these selectors.
        """

        identifier = selected_agent_name(combo)
        if identifier is None:
            return None
        for row in self._all_rows:
            if (row.agent_id or row.name) == identifier:
                return row
        return None

    def _parameter_slots(
        self,
    ) -> tuple[tuple[QComboBox, AgentParameterForm, JsonEditor, bool], ...]:
        return (
            (self.agentA, self.schemaA, self.editorA, True),
            (self.agentB, self.schemaB, self.editorB, True),
            (self.agentC, self.schemaC, self.editorC, self._agent_c_visible),
        )

    def _sync_parameter_surfaces(self) -> None:
        """Point each slot at the right parameter surface for its agent.

        A slot shows generated controls when its agent declares a schema and
        the pre-existing free-form JSON editor when it does not, so a legacy
        or Agent API v1 agent keeps exactly the surface it always had.

        The form is only re-targeted when the *agent* changed. Repopulating
        the combos (a Ruleset change, a catalog refresh) re-enters here with
        the same selection, and rebuilding then would silently discard the
        values a user had already set.
        """

        for combo, schema_form, editor, slot_visible in self._parameter_slots():
            row = self._row_for_slot(combo)
            identifier = (row.agent_id or row.name) if row is not None else None
            if identifier != schema_form.agent_id:
                schema_form.set_agent(
                    identifier,
                    agent_parameter_schema(row) if row is not None else EMPTY_PARAMETER_SCHEMA,
                )
            has_schema = schema_form.has_schema()
            schema_form.setVisible(slot_visible and has_schema)
            editor.setVisible(slot_visible and not has_schema)
        self._update_run_enabled()

    def parameter_validation_errors(self) -> list[str]:
        """Every reason the current parameter selection cannot be launched.

        Sourced entirely from the canonical Phase D resolver via
        ``AgentParameterForm.validation_error`` -- the Designer contributes no
        validation rule of its own.
        """

        errors: list[str] = []
        for slot, (_combo, schema_form, _editor, slot_visible) in zip(
            ("A", "B", "C"), self._parameter_slots(), strict=True
        ):
            if not slot_visible:
                continue
            message = schema_form.validation_error()
            if message:
                errors.append(f"Agent {slot}: {message}")
        return errors

    def _update_run_enabled(self) -> None:
        self.btnRun.setEnabled(
            not self._busy
            and self._has_eligible_agents
            and not self.parameter_validation_errors()
        )

    def _refilter_agents(self) -> None:
        """Populate every visible roster slot from the Ruleset's compatible agents.

        The Ruleset is the controlling selector (UX-15/UX-16): changing it
        never happens as a side effect of an agent choice, only the
        reverse. ``repopulate_paired_agent_combos`` is the same shared
        helper Simple uses (UX-19 parity) for Agent A/B: it preserves each
        combo's own selection when it remains eligible and steers Agent B
        to a deterministic opponent distinct from Agent A otherwise. Agent
        C (UX-32/UX-33), when present, is refiltered from the identical
        ``eligible`` roster via ``repopulate_additional_agent_combo``, so
        it can never offer a Ruleset-incompatible choice the same way
        Agent A/B cannot. ``sync_compatible_b_choices`` still applies the
        pre-existing runtime-kind restriction against Agent A for every
        slot: Ruleset v1 is the one identity that admits both Python and
        VM/blob agents, which still may not be mixed in the same match
        (``validate_homogeneous`` at launch), so that check is layered on
        top rather than replaced -- and generalizes to Agent C by simply
        calling the same pairwise helper against Agent A a second time,
        since "all entrants share Agent A's kind" is transitively "every
        entrant is compatible with Agent A".

        Duplicate *agents* across slots remain a legal, unrestricted
        choice (only per-slot entrant identity must be unique, which the
        Agent A/B/C letters already guarantee) -- so a Ruleset with only
        one compatible discovered agent still leaves the whole roster
        launchable, not just the minimum two slots. There is accordingly
        no "reduce the roster" step here: Advanced's roster ceiling (3) is
        fixed by the CLI contract, not derived per-Ruleset, so a Ruleset
        change can only ever replace incompatible *selections* within the
        roster the user already has, never shrink how many slots are
        offered.
        """

        ruleset_id = selected_ruleset_id(self.ruleset)
        eligible = [
            row
            for row in self._all_rows
            if agent_row_supported_by_ruleset(row, ruleset_id)
        ]
        repopulate_paired_agent_combos(self.agentA, self.agentB, eligible)
        sync_compatible_b_choices(self.agentA, self.agentB)
        if self._agent_c_visible:
            avoid = {
                name
                for name in (selected_agent_name(self.agentA), selected_agent_name(self.agentB))
                if name is not None
            }
            repopulate_additional_agent_combo(self.agentC, eligible, avoid=avoid)
            sync_compatible_b_choices(self.agentA, self.agentC)

        self._has_eligible_agents = bool(eligible)
        self._update_ruleset_explanation()
        # After the selections settle, not before: each slot's parameter
        # surface follows whichever agent it actually ended up on.
        self._sync_parameter_surfaces()

    def _update_ruleset_explanation(self) -> None:
        if not self._has_eligible_agents:
            self.rulesetExplanation.setText(
                "No compatible agents were found for this Ruleset. "
                "Create or import a compatible agent, then refresh."
            )
            return
        kinds = [selected_agent_kind(self.agentA), selected_agent_kind(self.agentB)]
        if self._agent_c_visible:
            kinds.append(selected_agent_kind(self.agentC))
        if "vm" in kinds:
            # Only Ruleset v1 offers both kinds; explains why some Agent
            # B/C entries are grayed out when a VM/blob agent is selected.
            self.rulesetExplanation.setText(VM_RULESET_EXPLANATION)
        else:
            self.rulesetExplanation.clear()

    # ---- Phase 4 dynamic roster (UX-29/UX-30/UX-31) ----
    def _set_agent_c_visible(self, visible: bool) -> None:
        self._agent_c_visible = visible
        self._agentCContainer.setVisible(visible)
        if self._agentCLabel is not None:
            self._agentCLabel.setVisible(visible)
        # Which of Agent C's two parameter surfaces is the visible one
        # depends on the selected agent, so the slot's visibility is applied
        # through the same sync that makes that decision everywhere else.
        self._sync_parameter_surfaces()
        # UX-30 item 5 / UX-31: the Add control disappears once the
        # runtime/CLI-derived maximum (ADVANCED_MAX_ROSTER) is reached, and
        # returns as soon as a slot is removed -- never merely disabled,
        # so the minimum 2-agent state has nothing extra to look at either.
        self.btnAddAgent.setVisible(not visible)

    def _add_agent_slot(self) -> None:
        if self._agent_c_visible:
            return  # Already at ADVANCED_MAX_ROSTER; the control should be hidden.
        self._set_agent_c_visible(True)
        self._refilter_agents()

    def _remove_agent_slot(self) -> None:
        if not self._agent_c_visible:
            return
        self._set_agent_c_visible(False)
        # Agent A/B selections and their JSON params are untouched -- only
        # the removed slot's own state stops being read by _emit_run.

    def setBusy(self, busy: bool) -> None:
        self._busy = busy
        for w in (
            self.btnRefresh,
            self.agentA,
            self.agentB,
            self.agentC,
            self.btnAddAgent,
            self.btnRemoveAgentC,
            self.arena,
            self.ticks,
            self.alive_w,
            self.kill_w,
            self.territory_w,
            self.territory_bucket,
            self.seed,
            self.btnRandomizeSeed,
            self.ruleset,
            self.schemaA,
            self.schemaB,
            self.schemaC,
        ):
            w.setEnabled(not busy)
        # Run stays disabled while no compatible agents exist or a parameter
        # is invalid, so becoming idle never re-enables launching a selection
        # the engine would reject.
        self._update_run_enabled()
        self.btnStop.setEnabled(busy)

    def randomize_seed(self) -> int:
        """Put a freshly generated seed in the seed field and return it.

        The field's own range is the source of truth for what is legal, so the
        generated value is always one the user could have typed. Its floor is
        raised past 0 because Advanced reads 0 as "use the engine default
        seed", which is the opposite of randomizing.
        """

        seed = random_match_seed(
            minimum=max(1, int(self.seed.minimum())),
            maximum=int(self.seed.maximum()),
        )
        self.seed.setValue(seed)
        return seed

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
        """Display the small canonical-result subset useful during normal runs.

        Phase 4 UX-34: ``result.entrants`` (``MatchPresentation.entrants``)
        is already however many entrants the match actually had --
        looping over it, rather than reading fixed A/B fields, is what
        makes this table correct for a 3-agent match without special-
        casing the count.
        """
        values = [
            ("winner", result.winner),
            ("termination_reason", result.termination_reason),
            ("result", result.result_path),
            ("replay", result.replay_path or "not available"),
        ]
        for entrant in result.entrants:
            status = "alive" if entrant.alive else "eliminated"
            values.append(
                (
                    f"entrant {entrant.agent_id}",
                    f"{entrant.name} — {status}, score={entrant.score:g}",
                )
            )
            # V5 Alpha 1 Phase E4. Phase D already records each entrant's
            # resolved parameters in result.json; this closes the loop, so the
            # values a user chose before the run are still visible after it,
            # in the same table they read the outcome from. Added only when
            # the match actually had parameters, so a row never claims a run
            # was configured when it was not -- which is every result written
            # before Phase D, and every default run since.
            if entrant.parameters:
                values.append(
                    (
                        f"entrant {entrant.agent_id} parameters",
                        describe_effective_parameters(entrant.parameters),
                    )
                )
        self.table.setRowCount(0)
        for key, value in values:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(key))
            self.table.setItem(row, 1, QTableWidgetItem(str(value)))

    # Helpers
    def _slot_parameters(
        self, schema_form: AgentParameterForm, editor: JsonEditor
    ) -> dict | None:
        """One slot's parameters, read from whichever surface is in use.

        Exactly one of the two is authoritative for a given agent, so a stale
        value left in the other can never travel: switching from a legacy
        agent to a schema agent must not smuggle the old free-form JSON into a
        schema-validated match, and vice versa.
        """

        if schema_form.has_schema():
            return schema_form.launch_overrides()
        return editor.get_data_or_none()

    def _emit_run(self) -> None:
        # The launch gate. Values are checked by the canonical Phase D
        # resolver before a subprocess exists, so a schema violation is a
        # message here rather than an agent failing several seconds later
        # inside a match the user then has to interpret.
        problems = self.parameter_validation_errors()
        if problems:
            QMessageBox.warning(self, "Invalid Agent Parameters", "\n".join(problems))
            return
        cfg = RunConfig(
            a_type=selected_agent_name(self.agentA) or "runner",
            b_type=selected_agent_name(self.agentB) or "writer",
            ruleset_id=selected_ruleset_id(self.ruleset),
            arena=int(self.arena.value()),
            ticks=int(self.ticks.value()),
            # Phase 5B: each weight is forwarded only when the user has
            # moved it off the engine default; otherwise the flag is
            # omitted so the engine applies its own canonical value,
            # exactly as Simple and a bare CLI run already do.
            alive_w=_weight_override(
                float(self.alive_w.value()), ENGINE_DEFAULT_WEIGHTS.alive
            ),
            kill_w=_weight_override(
                float(self.kill_w.value()), ENGINE_DEFAULT_WEIGHTS.kill
            ),
            territory_w=_weight_override(
                float(self.territory_w.value()), ENGINE_DEFAULT_WEIGHTS.territory
            ),
            territory_bucket=_weight_override(
                int(self.territory_bucket.value()),
                ENGINE_DEFAULT_WEIGHTS.territory_bucket,
            ),
            seed=int(self.seed.value()) or None,
            a_params=self._slot_parameters(self.schemaA, self.editorA),
            b_params=self._slot_parameters(self.schemaB, self.editorB),
            # Only present when the Agent C slot is actually visible -- a
            # hidden slot's stale selection/params must never reach a
            # RunConfig the user cannot see (UX-31/Agent Params contract).
            c_type=selected_agent_name(self.agentC) if self._agent_c_visible else None,
            c_params=(
                self._slot_parameters(self.schemaC, self.editorC)
                if self._agent_c_visible
                else None
            ),
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
