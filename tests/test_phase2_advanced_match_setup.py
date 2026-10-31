"""Advanced match setup: roster derivation, focused coverage.

Agent A/B list only the agents the Designer's Ruleset can run (UX-15
through UX-19). Phase 2 (RC2->final) originally put a Ruleset selector
ahead of the agent rows; Active Sensing is now the only Ruleset, so that
selector is gone and the roster is filtered by the same compatibility
check every other Designer surface uses.

The bulk of the behavioral coverage lives in
``tests/test_designer_agent_compatibility.py`` and
``tests/test_agent_combo_runtime_labels.py``. This module adds round-trip
stability, the identifier-vs-display-text distinction for Advanced
specifically, and unrelated-field preservation across a catalog refresh.

Marked ``gui`` like the other Designer tests: excluded from the default
headless run, exercised by the dedicated display-backed workflow.
"""

from __future__ import annotations

import os

import pytest


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


# ---------------------------------------------------------------------------
# Round trip
# ---------------------------------------------------------------------------


@pytest.mark.gui
def test_advanced_current_roster_refresh_is_deterministic(tmp_path):
    """Refreshing the same catalog preserves roster order and selections."""

    _make_app()
    from app.views.advanced import AdvancedPanel

    panel = AdvancedPanel(catalog=None, data_root=tmp_path)
    try:
        rows = [
            _row("legacy", "python", 1),
            _row("proc", "python", 2),
            _row("proc2", "python", 2),
        ]
        panel.setAgents(rows)
        panel.agentA.setCurrentIndex(panel.agentA.findData("proc2"))
        panel.agentB.setCurrentIndex(panel.agentB.findData("proc"))
        roster_before = [panel.agentA.itemData(i) for i in range(panel.agentA.count())]
        selection_before = (panel.agentA.currentData(), panel.agentB.currentData())

        panel.setAgents(rows)

        roster_after = [panel.agentA.itemData(i) for i in range(panel.agentA.count())]
        selection_after = (panel.agentA.currentData(), panel.agentB.currentData())
        assert roster_after == roster_before
        assert selection_after == selection_before
    finally:
        panel.deleteLater()


# ---------------------------------------------------------------------------
# Underlying config: identifiers, never display text
# ---------------------------------------------------------------------------


@pytest.mark.gui
def test_advanced_run_config_uses_discovery_ids_not_display_text(tmp_path):
    """Two agents sharing a display name must still resolve to their own
    discovery ids in the emitted RunConfig -- the presentation label never
    leaks into the submitted identifier."""

    _make_app()
    from app.services.agent_catalog import AgentRow
    from app.views.advanced import AdvancedPanel

    rows = [
        AgentRow(
            "Friendly",
            "/agents/alpha_id",
            None,
            {"display": "Friendly", "kind": "python", "api_version": 2},
            agent_id="alpha_id",
        ),
        AgentRow(
            "Friendly",
            "/agents/beta_id",
            None,
            {"display": "Friendly", "kind": "python", "api_version": 2},
            agent_id="beta_id",
        ),
    ]
    panel = AdvancedPanel(catalog=None, data_root=tmp_path)
    try:
        panel.setAgents(rows)
        panel.agentA.setCurrentIndex(panel.agentA.findData("alpha_id"))
        panel.agentB.setCurrentIndex(panel.agentB.findData("beta_id"))

        captured = []
        panel.runRequested.connect(captured.append)
        panel._emit_run()

        assert len(captured) == 1
        assert captured[0].a_type == "alpha_id"
        assert captured[0].b_type == "beta_id"
        assert "Friendly" not in captured[0].a_type
        assert "Friendly" not in captured[0].b_type
    finally:
        panel.deleteLater()


# ---------------------------------------------------------------------------
# No unrelated config regression
# ---------------------------------------------------------------------------


@pytest.mark.gui
def test_advanced_catalog_refresh_does_not_reset_unrelated_fields(tmp_path):
    """Compatibility refresh leaves match controls and Agent Params untouched."""

    _make_app()
    from app.views.advanced import AdvancedPanel

    panel = AdvancedPanel(catalog=None, data_root=tmp_path)
    try:
        rows = [_row("legacy", "python", 1), _row("proc", "python", 2)]
        panel.setAgents(rows)

        panel.arena.setValue(1024)
        panel.ticks.setValue(4242)
        panel.alive_w.setValue(3.5)
        panel.kill_w.setValue(9.0)
        panel.territory_w.setValue(2.0)
        panel.territory_bucket.setValue(96)
        panel.seed.setValue(777)
        panel.editorA.text.setPlainText('{"x": 1}')

        panel.setAgents(rows)

        assert panel.arena.value() == 1024
        assert panel.ticks.value() == 4242
        assert panel.alive_w.value() == 3.5
        assert panel.kill_w.value() == 9.0
        assert panel.territory_w.value() == 2.0
        assert panel.territory_bucket.value() == 96
        assert panel.seed.value() == 777
        assert panel.editorA.get_data_or_none() == {"x": 1}
    finally:
        panel.deleteLater()
