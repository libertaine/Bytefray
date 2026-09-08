"""Phase 2 (RC2->final): Ruleset-driven match setup, focused coverage.

Advanced previously taught the backward mental model "Agents -> Ruleset":
Agent A/B were populated from the whole discovered catalog and the Ruleset
combo was narrowed/auto-selected from whatever agents happened to be picked.
This phase inverts that so Advanced matches Simple's existing "Ruleset ->
Agents" model: the Ruleset is selected first, and Agent A/B list only the
agents that Ruleset supports (UX-14 through UX-19).

The bulk of the behavioral coverage for that inversion lives alongside the
pre-existing suites it directly supersedes
(``tests/test_designer_ruleset_compatibility.py``'s Advanced section and
``tests/test_agent_combo_runtime_labels.py``'s cross-panel tests). This
module adds the remaining Phase 2 focused-test items that had no prior
home: structural layout ordering, round-trip stability, the
identifier-vs-display-text distinction for Advanced specifically, and
unrelated-field preservation across a Ruleset change.

Marked ``gui`` like the other Designer tests: excluded from the default
headless run, exercised by the dedicated display-backed workflow.
"""

from __future__ import annotations

import os

import pytest

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


# ---------------------------------------------------------------------------
# UX-14: structural layout ordering
# ---------------------------------------------------------------------------


@pytest.mark.gui
def test_advanced_ruleset_row_precedes_agent_rows_structurally(tmp_path):
    """Ruleset must sit before Agent A/B in the actual QFormLayout row
    order, not merely appear that way on screen by coincidence."""

    _make_app()
    from app.views.advanced import AdvancedPanel

    panel = AdvancedPanel(catalog=None, data_root=tmp_path)
    try:
        form = panel.ruleset.parentWidget().layout()
        ruleset_row, _ = form.getWidgetPosition(panel.ruleset)
        agent_a_row, _ = form.getWidgetPosition(panel.agentA)
        agent_b_row, _ = form.getWidgetPosition(panel.agentB)
        assert ruleset_row < agent_a_row < agent_b_row
    finally:
        panel.deleteLater()


# ---------------------------------------------------------------------------
# Round trip
# ---------------------------------------------------------------------------


@pytest.mark.gui
def test_advanced_ruleset_round_trip_is_deterministic(tmp_path):
    """Ruleset A -> Ruleset B -> Ruleset A must land back on the same
    roster contents and the same selections, not merely "a" valid state."""

    _make_app()
    from app.views.advanced import AdvancedPanel

    panel = AdvancedPanel(catalog=None, data_root=tmp_path)
    try:
        panel.setAgents(
            [
                _row("legacy", "python", 1),
                _row("legacy2", "python", 1),
                _row("proc", "python", 2),
            ]
        )
        panel.ruleset.setCurrentIndex(panel.ruleset.findData(BYTEFRAY_RULESET_V2_ID))
        roster_before = [panel.agentA.itemData(i) for i in range(panel.agentA.count())]
        selection_before = (panel.agentA.currentData(), panel.agentB.currentData())

        panel.ruleset.setCurrentIndex(panel.ruleset.findData(BYTEFRAY_RULESET_V4_ID))
        panel.ruleset.setCurrentIndex(panel.ruleset.findData(BYTEFRAY_RULESET_V2_ID))

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
    leaks into the submitted identifier, and the Ruleset id is the
    canonical string, not its combo label."""

    _make_app()
    from app.services.agent_catalog import AgentRow
    from app.views.advanced import AdvancedPanel

    rows = [
        AgentRow(
            "Friendly",
            "/agents/alpha_id",
            None,
            {"display": "Friendly", "kind": "python", "api_version": 1},
            agent_id="alpha_id",
        ),
        AgentRow(
            "Friendly",
            "/agents/beta_id",
            None,
            {"display": "Friendly", "kind": "python", "api_version": 1},
            agent_id="beta_id",
        ),
    ]
    panel = AdvancedPanel(catalog=None, data_root=tmp_path)
    try:
        panel.setAgents(rows)
        panel.ruleset.setCurrentIndex(panel.ruleset.findData(BYTEFRAY_RULESET_V2_ID))
        panel.agentA.setCurrentIndex(panel.agentA.findData("alpha_id"))
        panel.agentB.setCurrentIndex(panel.agentB.findData("beta_id"))

        captured = []
        panel.runRequested.connect(captured.append)
        panel._emit_run()

        assert len(captured) == 1
        assert captured[0].a_type == "alpha_id"
        assert captured[0].b_type == "beta_id"
        assert captured[0].ruleset_id == BYTEFRAY_RULESET_V2_ID
        assert "Friendly" not in captured[0].a_type
        assert "Friendly" not in captured[0].b_type
    finally:
        panel.deleteLater()


# ---------------------------------------------------------------------------
# No unrelated config regression
# ---------------------------------------------------------------------------


@pytest.mark.gui
def test_advanced_ruleset_change_does_not_reset_unrelated_fields(tmp_path):
    """Changing Ruleset must only touch Agent A/B and the explanation text
    -- Arena Size, Ticks, scoring weights, Seed, and Agent Params are
    untouched by the compatibility recompute."""

    _make_app()
    from app.views.advanced import AdvancedPanel

    panel = AdvancedPanel(catalog=None, data_root=tmp_path)
    try:
        panel.setAgents([_row("legacy", "python", 1), _row("proc", "python", 2)])
        panel.ruleset.setCurrentIndex(panel.ruleset.findData(BYTEFRAY_RULESET_V2_ID))

        panel.arena.setValue(1024)
        panel.ticks.setValue(4242)
        panel.alive_w.setValue(3.5)
        panel.kill_w.setValue(9.0)
        panel.territory_w.setValue(2.0)
        panel.territory_bucket.setValue(96)
        panel.seed.setValue(777)
        panel.editorA.text.setPlainText('{"x": 1}')

        panel.ruleset.setCurrentIndex(panel.ruleset.findData(BYTEFRAY_RULESET_V4_ID))

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
