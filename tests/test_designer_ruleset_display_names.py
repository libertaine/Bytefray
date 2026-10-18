"""Designer shows Ruleset display names; selection still runs on identities.

The component-identity reset (docs/COMPONENT_VERSIONING.md) replaced the
"Ruleset v4" / "V6 alpha1" labels with the shared display names "Classic" and
"Active Sensing (Alpha)". These pin what a person actually sees on each
Designer surface, and that the canonical identity is still what each combo
stores, selects and exposes on hover. Selection semantics themselves are
pinned by test_designer_ruleset_compatibility.py and
test_v6_alpha_m1_5_designer.py.

Marked ``gui`` like the other Designer tests.
"""

from __future__ import annotations

import os

import pytest

CLASSIC = "bytefray-rules-4"
ALPHA = "bytefray-rules-6-alpha1"


def _make_app():
    pytest.importorskip("PySide6")
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication

    return QApplication.instance() or QApplication([])


def _items(combo) -> list[tuple[str, str, str]]:
    from PySide6.QtCore import Qt

    return [
        (combo.itemText(index), str(combo.itemData(index)), str(combo.itemData(index, Qt.ToolTipRole)))
        for index in range(combo.count())
    ]


def _row(name: str, *, sensing: bool):
    from app.services.agent_catalog import AgentRow

    meta: dict[str, object] = {"name": name, "kind": "python", "api_version": 2}
    if sensing:
        meta["capabilities"] = {"version": 1, "required": ["sense"]}
    return AgentRow(name, f"/agents/{name}", None, meta, agent_id=name)


BOTH = [
    ("Classic — Recommended", CLASSIC, f"Ruleset ID: {CLASSIC}"),
    ("Active Sensing (Alpha)", ALPHA, f"Ruleset ID: {ALPHA}"),
]


@pytest.mark.gui
def test_simple_and_advanced_show_display_names_and_default_to_classic(tmp_path):
    _make_app()
    from app.views.advanced import AdvancedPanel
    from app.views.simple import SimplePanel

    simple = SimplePanel(catalog=None)
    advanced = AdvancedPanel(catalog=None, data_root=tmp_path)
    try:
        assert _items(simple.ruleset) == BOTH[:1]
        assert _items(advanced.ruleset) == BOTH
        for combo in (simple.ruleset, advanced.ruleset):
            assert combo.currentData() == CLASSIC
            assert "Classic (bytefray-rules-4)" in combo.toolTip()
        advanced.ruleset.setCurrentIndex(advanced.ruleset.findData(ALPHA))
        assert advanced.ruleset.currentData() == ALPHA
        assert advanced.ruleset.currentText() == "Active Sensing (Alpha)"
    finally:
        simple.deleteLater()
        advanced.deleteLater()


@pytest.mark.gui
def test_development_names_active_sensing_without_switching_rulesets():
    _make_app()
    from app.views.development import AgentDevelopmentPanel

    panel = AgentDevelopmentPanel()
    try:
        assert _items(panel.rulesetCombo) == BOTH
        panel.setAgents([_row("my_keeper", sensing=True)])
        panel.selectAgent("my_keeper")
        # A sensing agent never repairs the selection into the experiment.
        assert panel.selected_ruleset_id() == CLASSIC
        assert not panel.btnTest.isEnabled()
        assert panel.rulesetExplanation.text() == (
            "Select Active Sensing (Alpha) explicitly to use this agent."
        )
        panel.rulesetCombo.setCurrentIndex(panel.rulesetCombo.findData(ALPHA))
        assert panel.selected_ruleset_id() == ALPHA
        assert panel.rulesetExplanation.text() == ""
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
        # Evaluation keeps its Classic-only scope.
        assert _items(evaluation.pairwiseRulesetCombo) == BOTH[:1]
    finally:
        new_agent.deleteLater()
        evaluation.deleteLater()
