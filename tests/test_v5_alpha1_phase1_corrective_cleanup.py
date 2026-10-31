"""V5 Alpha 1 Phase 1 -- corrective cleanup from first-user Alpha 1 testing.

Covers the Designer-side items from that phase:

1. The Ruleset combo's new-session default (Simple/Advanced/Development all
   started on ``bytefray-rules-2`` before this phase, purely because it
   sorted first in every option tuple). Active Sensing is now the only
   Ruleset and the Designer offers no Ruleset control at all, so what this
   file pins is that no fresh surface shows one -- there is no default
   left to get wrong.
5. The "Open last output folder" tooltip.

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


@pytest.mark.gui
def test_open_last_output_folder_tooltip_matches_actual_fallback_behavior(
    monkeypatch, tmp_path
):
    """V5 Alpha 1 Phase 1 item 5: the command's own tooltip must describe
    what it actually opens -- including that a session tournament's output
    permanently outranks a later single match's, per
    ``AgentDesigner._on_open_output_folder``'s own ``or`` chain -- not a
    vague "output" a new user cannot interpret."""

    pytest.importorskip("PySide6")
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication

    from app.agent_designer import AgentDesigner

    monkeypatch.setenv("BYTEFRAY_ROOT", str(tmp_path / "data"))
    QApplication.instance() or QApplication([])
    designer = AgentDesigner()
    try:
        tip = designer.openOutputFolderAction.toolTip().lower()
        assert "tournament" in tip
        assert "single match" in tip
        assert "runs folder" in tip
        # The Tools menu must actually show these tooltips (Qt hides them by
        # default), or the explanation added above is undiscoverable.
        assert designer.openOutputFolderAction.parent().toolTipsVisible()
    finally:
        designer.deleteLater()


@pytest.mark.gui
def test_fresh_designer_offers_no_ruleset_control(monkeypatch, tmp_path):
    """End-to-end through the real ``AgentDesigner`` window: no surface
    shows a Ruleset selector on first launch, before ``refresh_agents``
    ever runs -- Active Sensing is the only Ruleset."""

    pytest.importorskip("PySide6")
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication, QComboBox

    from app.agent_designer import AgentDesigner

    monkeypatch.setenv("BYTEFRAY_ROOT", str(tmp_path / "data"))
    QApplication.instance() or QApplication([])
    designer = AgentDesigner()
    try:
        assert not hasattr(designer.simple, "ruleset")
        assert not hasattr(designer.advanced, "ruleset")
        assert not hasattr(designer.development, "rulesetCombo")
        for combo in designer.findChildren(QComboBox):
            labels = [combo.itemText(index) for index in range(combo.count())]
            assert not any("bytefray-rules" in label or "Classic" in label for label in labels), labels
    finally:
        designer.deleteLater()
