"""GUI regression coverage for Phase 4's Advanced dynamic multi-agent roster.

Phase 1-3 (v4.0.0-rc2) left Advanced Match Setup hard-coded to exactly two
entrant slots (Agent A/Agent B) even though the engine itself already runs
3-entrant matches (see ``engine/tests/test_v2_alpha4_multi_entrant.py`` and
the CLI's pre-existing ``--c-type``/``--c-blob`` flags,
``engine/tests/test_v2_default_placement.py::
test_cli_default_v2_three_entrants_run_a_real_match``). Phase 4 exposes that
existing capability through a dynamic Add/Remove Agent roster capped at the
CLI's real ceiling of three entrants (Agent A/B/C) -- these tests pin the
GUI-layer behavior: roster add/remove, Ruleset-driven per-slot filtering,
runtime-kind homogeneity across all three slots, order preservation into
RunConfig, and that Simple stays an intentionally two-agent surface with a
small pointer toward Advanced.

Marked ``gui`` like the other Designer tests: excluded from the default
headless run, exercised by the dedicated display-backed workflow.
"""

from __future__ import annotations

import os

import pytest

BYTEFRAY_RULESET_ID = "bytefray-rules-1"
BYTEFRAY_RULESET_V2_ID = "bytefray-rules-2"
BYTEFRAY_RULESET_V4_ID = "bytefray-rules-4"


def _make_app():
    pytest.importorskip("PySide6")
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication

    return QApplication.instance() or QApplication([])


def _row(name: str, kind: str, api_version: int | None = None):
    from app.services.agent_catalog import AgentRow

    meta: dict[str, object] = {"name": name, "kind": kind}
    if api_version is not None:
        meta["api_version"] = api_version
    return AgentRow(name, f"/agents/{name}", None, meta, agent_id=name)


def _panel(tmp_path, rows):
    from app.views.advanced import AdvancedPanel

    panel = AdvancedPanel(catalog=None, data_root=tmp_path)
    # V5 Alpha 1 Phase 1: Advanced's fresh-session Ruleset default changed
    # from v2 to the stable v4 identity, which this module's Agent API v1
    # ("legacy"/"x_id"/...) rows are not compatible with. This suite is
    # about roster add/remove/order mechanics under a Python Agent API v1
    # roster, not about which Ruleset a fresh panel starts on (that is
    # covered by engine/tests/test_designer_ruleset_options.py and
    # tests/test_v5_alpha1_phase1_corrective_cleanup.py) -- so every caller
    # explicitly pins v2 here, exactly as the callers that already did this
    # individually before this helper existed.
    panel.setAgents(rows)
    panel.ruleset.setCurrentIndex(panel.ruleset.findData(BYTEFRAY_RULESET_V2_ID))
    return panel


@pytest.mark.gui
def test_default_roster_is_exactly_two_agents(tmp_path):
    """UX-29/Tests item 1: on construction, only the minimum roster exists."""
    _make_app()
    panel = _panel(tmp_path, [_row("legacy", "python", 1), _row("legacy2", "python", 1)])
    try:
        assert panel.roster_size == 2
        assert panel.agentA.currentData() == "legacy"
        assert panel.agentB.currentData() == "legacy2"
        assert not panel.agentC.isVisibleTo(panel)
        assert not panel.btnRemoveAgentC.isVisibleTo(panel)
        # editorC lives on the (currently inactive) Agent Params tab page,
        # which QTabWidget itself hides regardless of our own visibility
        # toggling -- isHidden() reflects only editorC's own explicit
        # show/hide state, independent of that ancestor-chain noise.
        assert panel.editorC.isHidden()
        assert panel.btnAddAgent.isVisibleTo(panel)
    finally:
        panel.deleteLater()


@pytest.mark.gui
def test_add_agent_grows_roster_with_compatible_deterministic_default(tmp_path):
    """UX-30: Add Agent adds exactly one slot, populated only with agents
    compatible with the selected Ruleset, defaulting to an agent distinct
    from A/B when one is available, and leaves A/B untouched."""
    _make_app()
    panel = _panel(
        tmp_path,
        [_row("legacy", "python", 1), _row("legacy2", "python", 1), _row("legacy3", "python", 1)],
    )
    try:
        panel.ruleset.setCurrentIndex(panel.ruleset.findData(BYTEFRAY_RULESET_V2_ID))
        a_before, b_before = panel.agentA.currentData(), panel.agentB.currentData()

        panel.btnAddAgent.click()

        assert panel.roster_size == 3
        assert panel.agentA.currentData() == a_before
        assert panel.agentB.currentData() == b_before
        assert panel.agentC.currentData() not in (None, a_before, b_before)
        listed_c = {panel.agentC.itemData(i) for i in range(panel.agentC.count())}
        assert listed_c == {"legacy", "legacy2", "legacy3"}
        assert not panel.btnAddAgent.isVisibleTo(panel)  # max reached
        assert panel.agentC.isVisibleTo(panel)
        assert panel.btnRemoveAgentC.isVisibleTo(panel)
        assert not panel.editorC.isHidden()
    finally:
        panel.deleteLater()


@pytest.mark.gui
def test_remove_agent_shrinks_roster_and_preserves_ab(tmp_path):
    """UX-31: removing Agent C returns to the minimum roster, restores the
    Add control, and never touches Agent A/B's selections."""
    _make_app()
    panel = _panel(tmp_path, [_row("legacy", "python", 1), _row("legacy2", "python", 1)])
    try:
        panel.btnAddAgent.click()
        assert panel.roster_size == 3
        a_before, b_before = panel.agentA.currentData(), panel.agentB.currentData()

        panel.btnRemoveAgentC.click()

        assert panel.roster_size == 2
        assert panel.agentA.currentData() == a_before
        assert panel.agentB.currentData() == b_before
        assert panel.btnAddAgent.isVisibleTo(panel)
        assert not panel.agentC.isVisibleTo(panel)
        assert panel.editorC.isHidden()

        # Adding again afterward must still produce a sane, populated slot.
        panel.btnAddAgent.click()
        assert panel.roster_size == 3
        assert panel.agentC.currentData() in ("legacy", "legacy2")
    finally:
        panel.deleteLater()


@pytest.mark.gui
def test_add_agent_is_unavailable_once_maximum_reached(tmp_path):
    """UX-30 item 5: the Add control disappears at the runtime/CLI-derived
    maximum (3) and clicking it again (defensively) does not create a
    fourth slot."""
    _make_app()
    panel = _panel(tmp_path, [_row("legacy", "python", 1), _row("legacy2", "python", 1)])
    try:
        panel.btnAddAgent.click()
        assert panel.roster_size == 3
        panel._add_agent_slot()  # Defensive: must be a no-op past the max.
        assert panel.roster_size == 3
    finally:
        panel.deleteLater()


@pytest.mark.gui
def test_every_roster_slot_is_ruleset_filtered(tmp_path):
    """UX-32: Agent C is filtered by the same ``agent_row_supported_by_ruleset``
    predicate as Agent A/B -- no separate compatibility logic."""
    _make_app()
    panel = _panel(
        tmp_path,
        [
            _row("legacy", "python", 1),
            _row("proc", "python", 2),
            _row("vm_agent", "builtin"),
        ],
    )
    try:
        panel.ruleset.setCurrentIndex(panel.ruleset.findData(BYTEFRAY_RULESET_ID))
        panel.btnAddAgent.click()
        listed_c = {panel.agentC.itemData(i) for i in range(panel.agentC.count())}
        assert listed_c == {"legacy", "vm_agent"}  # v1 excludes the API-v2 agent

        panel.ruleset.setCurrentIndex(panel.ruleset.findData(BYTEFRAY_RULESET_V2_ID))
        listed_c = {panel.agentC.itemData(i) for i in range(panel.agentC.count())}
        assert listed_c == {"legacy"}  # v2 is Python-only
    finally:
        panel.deleteLater()


@pytest.mark.gui
def test_ruleset_change_with_three_entrants_preserves_compatible_replaces_rest(tmp_path):
    """Ruleset-change contract (Sec "Ruleset changes with a multi-agent
    roster"): a compatible selection survives; an incompatible one is
    replaced deterministically; no roster-size change occurs (Advanced's
    ceiling is CLI-derived, not per-Ruleset)."""
    _make_app()
    panel = _panel(
        tmp_path,
        [
            _row("legacy", "python", 1),
            _row("legacy2", "python", 1),
            _row("proc", "python", 2),
            _row("proc2", "python", 2),
            _row("proc3", "python", 2),
        ],
    )
    try:
        panel.ruleset.setCurrentIndex(panel.ruleset.findData(BYTEFRAY_RULESET_V2_ID))
        panel.agentA.setCurrentIndex(panel.agentA.findData("legacy"))
        panel.agentB.setCurrentIndex(panel.agentB.findData("legacy2"))
        panel.btnAddAgent.click()
        panel.agentC.setCurrentIndex(panel.agentC.findData("legacy"))  # explicit duplicate of A

        panel.ruleset.setCurrentIndex(panel.ruleset.findData(BYTEFRAY_RULESET_V4_ID))

        # None of legacy/legacy2/legacy (Agent API v1) survive into v4
        # (Agent API v2 only); all three slots deterministically fall
        # through to the eligible v4 roster in its catalog order.
        assert panel.roster_size == 3  # ceiling unchanged by the Ruleset switch
        assert panel.agentA.currentData() == "proc"
        assert panel.agentB.currentData() == "proc2"
        assert panel.agentC.currentData() == "proc3"
        assert panel.btnRun.isEnabled()
    finally:
        panel.deleteLater()


@pytest.mark.gui
def test_runtime_kind_homogeneity_applies_to_agent_c_too(tmp_path):
    """Extends the Phase 2 Agent-B-compatible-with-Agent-A rule to every
    roster slot, not just the pair -- reuses the existing
    ``sync_compatible_b_choices`` helper against Agent A a second time
    rather than inventing separate pairwise GUI logic."""
    _make_app()
    panel = _panel(
        tmp_path,
        [_row("claimer", "python", 1), _row("runner", "vm"), _row("hunter", "python", 1)],
    )
    try:
        panel.ruleset.setCurrentIndex(panel.ruleset.findData(BYTEFRAY_RULESET_ID))
        panel.btnAddAgent.click()
        panel.agentA.setCurrentIndex(panel.agentA.findData("claimer"))  # Python

        model = panel.agentC.model()
        enabled = {panel.agentC.itemData(i): model.item(i).isEnabled() for i in range(panel.agentC.count())}
        assert enabled == {"claimer": True, "runner": False, "hunter": True}
        assert panel.agentC.currentData() != "runner"

        panel.agentA.setCurrentIndex(panel.agentA.findData("runner"))  # VM
        model = panel.agentC.model()
        enabled = {panel.agentC.itemData(i): model.item(i).isEnabled() for i in range(panel.agentC.count())}
        assert enabled == {"claimer": False, "runner": True, "hunter": False}
        assert panel.agentC.currentData() == "runner"  # repaired to the only compatible choice
    finally:
        panel.deleteLater()


@pytest.mark.gui
def test_emit_run_preserves_roster_order_and_underlying_identifiers(tmp_path):
    """Order preservation + underlying-identifier pinning: RunConfig carries
    the exact discovery ids in A, B, C order -- never display text, never
    reordered."""
    _make_app()
    from app.services.agent_catalog import AgentRow

    rows = [
        AgentRow("Explorer", "/agents/x_id", None, {"name": "x_id", "kind": "python", "api_version": 1}, agent_id="x_id"),
        AgentRow("Quorum", "/agents/y_id", None, {"name": "y_id", "kind": "python", "api_version": 1}, agent_id="y_id"),
        AgentRow("Concentrated Attacker", "/agents/z_id", None, {"name": "z_id", "kind": "python", "api_version": 1}, agent_id="z_id"),
    ]
    panel = _panel(tmp_path, rows)
    try:
        panel.agentA.setCurrentIndex(panel.agentA.findData("x_id"))
        panel.agentB.setCurrentIndex(panel.agentB.findData("y_id"))
        panel.btnAddAgent.click()
        panel.agentC.setCurrentIndex(panel.agentC.findData("z_id"))

        captured = []
        panel.runRequested.connect(captured.append)
        panel._emit_run()

        cfg = captured[0]
        assert (cfg.a_type, cfg.b_type, cfg.c_type) == ("x_id", "y_id", "z_id")
        # None of the display labels ("Explorer", "Quorum [Python]", ...)
        # leaked into the launched config.
        for value in (cfg.a_type, cfg.b_type, cfg.c_type):
            assert value in ("x_id", "y_id", "z_id")
    finally:
        panel.deleteLater()


@pytest.mark.gui
def test_emit_run_omits_c_fields_when_agent_c_not_added(tmp_path):
    """A RunConfig built from the default 2-agent roster must not carry a
    stale/ghost third entrant."""
    _make_app()
    panel = _panel(tmp_path, [_row("legacy", "python", 1), _row("legacy2", "python", 1)])
    try:
        captured = []
        panel.runRequested.connect(captured.append)
        panel._emit_run()

        cfg = captured[0]
        assert cfg.c_type is None
        assert cfg.c_params is None
    finally:
        panel.deleteLater()


@pytest.mark.gui
def test_agent_c_params_do_not_mutate_agent_ab_params(tmp_path):
    """Agent Params contract: Agent C gets its own independent JSON editor
    (Option A -- the engine's per-letter env var parsing is already
    generic); adding/editing it must never mutate Agent A/B's params, and
    it must not be surfaced into RunConfig unless Agent C is present."""
    import json

    _make_app()
    panel = _panel(tmp_path, [_row("legacy", "python", 1), _row("legacy2", "python", 1)])
    try:
        panel.editorA.text.setPlainText(json.dumps({"a": 1}))
        panel.editorB.text.setPlainText(json.dumps({"b": 2}))
        panel.btnAddAgent.click()
        panel.editorC.text.setPlainText(json.dumps({"c": 3}))

        captured = []
        panel.runRequested.connect(captured.append)
        panel._emit_run()
        cfg = captured[0]

        assert cfg.a_params == {"a": 1}
        assert cfg.b_params == {"b": 2}
        assert cfg.c_params == {"c": 3}

        # Removing Agent C afterward must stop forwarding its params, and
        # must not disturb A/B's.
        captured.clear()
        panel.btnRemoveAgentC.click()
        panel._emit_run()
        cfg = captured[0]
        assert cfg.a_params == {"a": 1}
        assert cfg.b_params == {"b": 2}
        assert cfg.c_params is None
    finally:
        panel.deleteLater()


@pytest.mark.gui
def test_empty_catalog_disables_run_regardless_of_roster_size(tmp_path):
    """Empty-catalog handling (Sec "Empty catalog / insufficient compatible
    agents") applies uniformly: it never crashes, and Run stays disabled,
    whether or not Agent C had been added."""
    _make_app()
    panel = _panel(tmp_path, [_row("legacy", "python", 1)])
    try:
        panel.ruleset.setCurrentIndex(panel.ruleset.findData(BYTEFRAY_RULESET_V2_ID))
        panel.btnAddAgent.click()
        assert panel.btnRun.isEnabled()  # one compatible agent: duplicates are legal

        panel.ruleset.setCurrentIndex(panel.ruleset.findData(BYTEFRAY_RULESET_V4_ID))
        assert not panel.btnRun.isEnabled()
        assert panel.agentC.itemText(0) == "(none found)"
    finally:
        panel.deleteLater()


# ---------------------------------------------------------------------------
# Simple (UX-27/UX-28): unchanged 2-agent behavior plus the new hint.
# ---------------------------------------------------------------------------


def _capture_match_launch(monkeypatch, designer):
    captured = {"started": False}

    class _FakeProc:
        def start(self):
            captured["started"] = True

    def _fake_start_process(command, env, working_directory, *, label):
        captured.update(command=command, env=env, working_directory=working_directory, label=label)
        return _FakeProc()

    monkeypatch.setattr(designer, "_start_process", _fake_start_process)
    return captured


def _argument_value(command: list[str], flag: str) -> str:
    return command[command.index(flag) + 1]


@pytest.mark.gui
def test_designer_forwards_three_agent_roster_into_the_launched_command(monkeypatch, tmp_path):
    """The GUI-boundary proof: AgentDesigner._on_advanced_run must build a
    RunConfig-consuming command line that actually carries Agent C through
    to ``--c-type``/the ``BYTEFRAY_AGENT_C_PARAMS_JSON`` env var, exactly
    mirroring how Agent A/B already cross this boundary."""
    pytest.importorskip("PySide6")
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication

    from app.agent_designer import AgentDesigner

    monkeypatch.setenv("BYTEFRAY_ROOT", str(tmp_path / "data"))
    QApplication.instance() or QApplication([])
    designer = AgentDesigner()
    captured = _capture_match_launch(monkeypatch, designer)

    panel = designer.advanced
    panel.ruleset.setCurrentIndex(panel.ruleset.findData(BYTEFRAY_RULESET_V2_ID))
    panel.agentA.setCurrentIndex(panel.agentA.findData("adaptive"))
    panel.agentB.setCurrentIndex(panel.agentB.findData("hunter"))
    panel.btnAddAgent.click()
    import json as _json

    panel.editorC.text.setPlainText(_json.dumps({"aggression": 0.5}))
    panel._emit_run()

    assert captured["started"] is True
    assert _argument_value(captured["command"], "--a-type") == "adaptive"
    assert _argument_value(captured["command"], "--b-type") == "hunter"
    assert _argument_value(captured["command"], "--c-type") == panel.agentC.currentData()
    assert captured["env"].value("BYTEFRAY_AGENT_C_PARAMS_JSON") == _json.dumps({"aggression": 0.5})
    assert "could not resolve agents" not in panel.log.toPlainText()
    designer.deleteLater()


@pytest.mark.gui
def test_simple_stays_two_agent_and_gains_only_the_advanced_hint(tmp_path):
    _make_app()
    from app.views.simple import SimplePanel

    panel = SimplePanel(catalog=None)
    try:
        panel.setAgents([_row("legacy", "python", 1), _row("legacy2", "python", 1)])
        # V5 Alpha 1 Phase 1: Simple's fresh-session default is now the
        # stable v4 Ruleset, which these Agent API v1 rows are not
        # compatible with -- select v2 explicitly, since this test is about
        # the 2-agent-only structural behavior, not the fresh default.
        panel.ruleset.setCurrentIndex(panel.ruleset.findData(BYTEFRAY_RULESET_V2_ID))
        assert not hasattr(panel, "agentC")
        assert not hasattr(panel, "btnAddAgent")
        assert "Advanced" in panel.multiAgentHint.text()
        assert "2-agent" in panel.multiAgentHint.text()

        captured = []
        panel.runRequested.connect(captured.append)
        panel.agentA.setCurrentIndex(panel.agentA.findData("legacy"))
        panel.agentB.setCurrentIndex(panel.agentB.findData("legacy2"))
        panel._emit_run()
        cfg = captured[0]
        assert not hasattr(cfg, "c_type") or cfg.c_type is None
    finally:
        panel.deleteLater()
