"""Designer shows the Ruleset's display name, not release or program labels.

The component-identity reset (docs/COMPONENT_VERSIONING.md) gave the Ruleset
the shared display name "Active Sensing (Alpha)". Active Sensing is now the
only Ruleset, so no Designer surface offers a Ruleset control; these pin the
places a person still sees the name, and that development-only labels
("V6", program codes) stay out of view. Compatibility gating is pinned by
test_designer_agent_compatibility.py and test_v6_alpha_m1_5_designer.py.

Marked ``gui`` like the other Designer tests.
"""

from __future__ import annotations

import os

import pytest


def _make_app():
    pytest.importorskip("PySide6")
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication

    return QApplication.instance() or QApplication([])


def _row(name: str, *, sensing: bool):
    from app.services.agent_catalog import AgentRow

    meta: dict[str, object] = {"name": name, "kind": "python", "api_version": 2}
    if sensing:
        meta["capabilities"] = {"version": 1, "required": ["sense"]}
    return AgentRow(name, f"/agents/{name}", None, meta, agent_id=name)


@pytest.mark.gui
def test_development_names_active_sensing_in_its_guide():
    _make_app()
    from app.views.development import AgentDevelopmentPanel

    panel = AgentDevelopmentPanel()
    try:
        panel.setAgents([_row("my_keeper", sensing=True)])
        panel.selectAgent("my_keeper")
        # A sensing agent is testable straight away: there is nothing to switch.
        assert panel.btnTest.isEnabled()
        assert panel.compatibilityExplanation.text() == ""
        assert panel.btnSensingGuide.text() == "Active Sensing (Alpha) sensing guide…"
        assert panel.btnSensingGuide.accessibleName() == "Active Sensing (Alpha) sensing guide"
        dialog = panel.showSensingGuide()
        assert dialog.windowTitle() == "Active Sensing (Alpha) sensing guide"
        dialog.close()
    finally:
        panel.deleteLater()


@pytest.mark.gui
def test_new_agent_and_evaluation_carry_no_release_or_program_labels(tmp_path):
    _make_app()
    from app.views.development import NewAgentDialog
    from app.views.evaluation import EvaluationDialog

    new_agent = NewAgentDialog(tmp_path)
    evaluation = EvaluationDialog(
        [("Candidate", "candidate"), ("Opponent", "opponent")],
        default_candidate="candidate",
        default_output=tmp_path / "out",
    )
    try:
        labels = {
            str(new_agent.templateCombo.itemData(index)): new_agent.templateCombo.itemText(index)
            for index in range(new_agent.templateCombo.count())
        }
        assert labels["window_scout"] == "Window Scout — personal copy"
        assert labels["watchful_keeper"] == "Watchful Keeper — personal copy"
        assert labels["roaming_reacquirer"] == "Roaming Reacquirer — personal copy"
        assert not any("V6" in label for label in labels.values())
        # Evaluation has no Ruleset choice to make.
        assert not hasattr(evaluation, "pairwiseRulesetCombo")
    finally:
        new_agent.deleteLater()
        evaluation.deleteLater()
