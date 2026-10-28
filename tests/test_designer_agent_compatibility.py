"""GUI coverage for the Designer's agent compatibility check.

Active Sensing is Bytefray's only Ruleset, so no Designer surface offers a
Ruleset control. Every surface still asks the engine's compatibility
question for the agents it would launch, and fails closed -- disabled
execution plus an explanation -- for an agent that cannot run, rather than
relying on the engine to reject the match after launch.

The *rules* themselves are pinned once, headlessly, against the engine
policy in ``engine/tests/test_designer_ruleset_options.py``; what these add
is that each view actually applies them, including selection repair and the
fail-closed empty state.

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
# Simple and Advanced
# ---------------------------------------------------------------------------


@pytest.mark.gui
@pytest.mark.parametrize("panel_name", ["simple", "advanced"])
def test_match_panels_offer_only_agents_that_can_run(tmp_path, panel_name):
    """Agent A/B list only Agent API v2 agents, through the engine's own
    predicate, and neither panel has a Ruleset control."""

    _make_app()
    from app.views.advanced import AdvancedPanel
    from app.views.simple import SimplePanel

    panel = (
        SimplePanel(catalog=None)
        if panel_name == "simple"
        else AdvancedPanel(catalog=None, data_root=tmp_path)
    )
    try:
        panel.setAgents(
            [
                _row("legacy", "python", 1),
                _row("proc", "python", 2),
                _row("vm_agent", "builtin"),
            ]
        )
        assert not hasattr(panel, "ruleset")
        listed = [panel.agentA.itemData(i) for i in range(panel.agentA.count())]
        assert listed == ["proc"]
        assert panel.btnRun.isEnabled()
        assert not panel.compatibilityExplanation.isVisibleTo(panel)
    finally:
        panel.deleteLater()


@pytest.mark.gui
def test_advanced_preserves_current_selections_across_catalog_refresh(tmp_path):
    """Eligible API-v2 selections survive a catalog refresh by identifier."""

    _make_app()
    from app.views.advanced import AdvancedPanel

    panel = AdvancedPanel(catalog=None, data_root=tmp_path)
    try:
        rows = [
            _row("legacy", "python", 1),
            _row("proc", "python", 2),
            _row("proc2", "python", 2),
            _row("vm_agent", "builtin"),
        ]
        panel.setAgents(rows)
        panel.agentA.setCurrentIndex(panel.agentA.findData("proc2"))
        panel.agentB.setCurrentIndex(panel.agentB.findData("proc"))
        panel.setAgents(rows)
        assert panel.agentA.currentData() == "proc2"
        assert panel.agentB.currentData() == "proc"
        assert panel.btnRun.isEnabled()
    finally:
        panel.deleteLater()


@pytest.mark.gui
def test_advanced_replaces_both_selections_when_catalog_removes_them(tmp_path):
    """A refreshed current roster deterministically repairs both selections."""

    _make_app()
    from app.views.advanced import AdvancedPanel

    panel = AdvancedPanel(catalog=None, data_root=tmp_path)
    try:
        panel.setAgents(
            [
                _row("proc", "python", 2),
                _row("proc2", "python", 2),
            ]
        )
        panel.agentA.setCurrentIndex(panel.agentA.findData("proc2"))
        panel.agentB.setCurrentIndex(panel.agentB.findData("proc"))
        panel.setAgents(
            [
                _row("legacy", "python", 1),
                _row("proc3", "python", 2),
                _row("proc4", "python", 2),
            ]
        )
        assert panel.agentA.currentData() == "proc3"
        assert panel.agentB.currentData() == "proc4"
        assert panel.btnRun.isEnabled()
    finally:
        panel.deleteLater()


@pytest.mark.gui
def test_advanced_handles_zero_compatible_agents_without_crashing_or_stale_selection(tmp_path):
    """No discovered compatible agent disables Run, shows an explanation,
    and never retains a stale selection. Restoring a current catalog must
    recover."""

    _make_app()
    from app.views.advanced import AdvancedPanel

    panel = AdvancedPanel(catalog=None, data_root=tmp_path)
    try:
        panel.setAgents([_row("proc", "python", 2)])
        assert panel.btnRun.isEnabled()

        panel.setAgents([_row("legacy", "python", 1)])
        assert not panel.btnRun.isEnabled()
        assert panel.agentA.itemText(0) == "(none found)"
        assert panel.agentB.itemText(0) == "(none found)"
        assert "No compatible agents" in panel.compatibilityExplanation.text()

        # Becoming idle must not quietly re-enable an impossible match.
        panel.setBusy(True)
        panel.setBusy(False)
        assert not panel.btnRun.isEnabled()

        panel.setAgents([_row("proc", "python", 2)])
        assert panel.btnRun.isEnabled()
        assert panel.agentA.currentData() == "proc"
    finally:
        panel.deleteLater()


# ---------------------------------------------------------------------------
# Development
# ---------------------------------------------------------------------------


@pytest.mark.gui
@pytest.mark.parametrize(("api_version", "runnable"), [(1, False), (2, True)])
def test_development_enables_test_only_for_an_agent_that_can_run(api_version, runnable):
    _make_app()
    from app.views.development import AgentDevelopmentPanel

    panel = AgentDevelopmentPanel()
    try:
        panel.setAgents([_row("probe", "python", api_version)])
        panel.selectAgent("probe")
        assert not hasattr(panel, "rulesetCombo")
        assert panel.btnTest.isEnabled() is runnable
        assert panel.compatibilityExplanation.isVisibleTo(panel) is not runnable
    finally:
        panel.deleteLater()


@pytest.mark.gui
def test_development_lists_historical_agents_but_disables_their_execution():
    """Historical packages remain inspectable but cannot be tested."""

    _make_app()
    from app.views.development import AgentDevelopmentPanel

    panel = AgentDevelopmentPanel()
    try:
        panel.setAgents([_row("legacy", "python", 1), _row("proc", "python", 2)])
        listed = [panel.agentCombo.itemData(i) for i in range(panel.agentCombo.count())]
        assert listed == ["legacy", "proc"]
        panel.selectAgent("legacy")
        assert not panel.btnTest.isEnabled()
        assert "Agent API v2" in panel.compatibilityExplanation.text()
    finally:
        panel.deleteLater()


@pytest.mark.gui
def test_development_reapplies_compatibility_when_the_selection_changes():
    _make_app()
    from app.views.development import AgentDevelopmentPanel

    panel = AgentDevelopmentPanel()
    try:
        panel.setAgents([_row("legacy", "python", 1), _row("proc", "python", 2)])
        panel.selectAgent("legacy")
        assert not panel.btnTest.isEnabled()

        panel.selectAgent("proc")
        assert panel.btnTest.isEnabled()
        assert panel.compatibilityExplanation.text() == ""
    finally:
        panel.deleteLater()


@pytest.mark.gui
def test_development_disables_test_for_an_incompatible_explicit_opponent():
    """An explicitly chosen opponent is a real entrant, so an incompatible
    pairing must fail closed in the UI -- the internal Reference opponent
    must not."""

    _make_app()
    from app.views.development import AgentDevelopmentPanel

    panel = AgentDevelopmentPanel()
    try:
        panel.setAgents([_row("legacy", "python", 1), _row("proc", "python", 2)])
        panel.selectAgent("proc")
        assert panel.selected_opponent_id() is None  # Reference
        assert panel.btnTest.isEnabled()

        panel.opponentCombo.setCurrentIndex(panel.opponentCombo.findData("legacy"))
        assert not panel.btnTest.isEnabled()

        # Returning to the Reference opponent restores it.
        panel.opponentCombo.setCurrentIndex(panel.opponentCombo.findData(None))
        assert panel.btnTest.isEnabled()
    finally:
        panel.deleteLater()


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------


def _evaluation_dialog(tmp_path, default_candidate, with_metadata=True):
    from app.views.evaluation import EvaluationDialog

    metadata = {
        "legacy": {"kind": "python", "api_version": 1},
        "proc": {"kind": "python", "api_version": 2},
    }
    return EvaluationDialog(
        [("legacy", "legacy"), ("proc", "proc")],
        default_candidate=default_candidate,
        default_output=tmp_path / "out",
        agent_metadata=metadata if with_metadata else None,
    )


@pytest.mark.gui
@pytest.mark.parametrize(("candidate", "runnable"), [("legacy", False), ("proc", True)])
def test_evaluation_runs_only_a_candidate_that_can_run(tmp_path, candidate, runnable):
    _make_app()
    dialog = _evaluation_dialog(tmp_path, candidate)
    try:
        assert not hasattr(dialog, "pairwiseRulesetCombo")
        assert dialog.runButton.isEnabled() is runnable
        assert dialog.compatibilityExplanation.isVisibleTo(dialog) is not runnable
    finally:
        dialog.deleteLater()


@pytest.mark.gui
def test_evaluation_evaluates_compatibility_across_the_whole_roster(tmp_path):
    """Not just the candidate: an incompatible opponent blocks Run exactly
    as an incompatible candidate does."""

    from PySide6.QtCore import Qt

    _make_app()
    dialog = _evaluation_dialog(tmp_path, "proc")
    try:
        assert dialog.runButton.isEnabled()
        for index in range(dialog.opponentsList.count()):
            item = dialog.opponentsList.item(index)
            if item.data(Qt.UserRole) == "legacy":
                item.setSelected(True)
        assert not dialog.runButton.isEnabled()
        assert dialog.compatibilityExplanation.isVisibleTo(dialog)
    finally:
        dialog.deleteLater()


@pytest.mark.gui
def test_evaluation_without_supplied_metadata_keeps_previous_behavior(tmp_path):
    """A programmatic caller or test double that supplies no metadata must
    not have its run silently disabled by that absence."""

    _make_app()
    dialog = _evaluation_dialog(tmp_path, "legacy", with_metadata=False)
    try:
        assert dialog.runButton.isEnabled()
    finally:
        dialog.deleteLater()
