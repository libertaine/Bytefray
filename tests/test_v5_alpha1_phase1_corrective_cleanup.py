"""V5 Alpha 1 Phase 1 -- corrective cleanup from first-user Alpha 1 testing.

Covers the Designer-side items from that phase:

1. The Ruleset combo's new-session default (Simple/Advanced/Development all
   started on ``bytefray-rules-2`` before this phase, purely because it
   sorted first in every option tuple -- see
   ``app.services.ruleset_options.DEFAULT_DESIGNER_RULESET_ID`` and
   ``app.widgets.ruleset_combo.populate_ruleset_combo``).

The headless rules themselves (which Ruleset the constant names, and that
it is actually offered everywhere) are pinned without a display in
``engine/tests/test_designer_ruleset_options.py``; what this file adds is
that each real Designer widget actually starts there.

Marked ``gui`` like the other Designer tests: excluded from the default
headless run, exercised by the dedicated display-backed workflow.
"""

from __future__ import annotations

import os

import pytest

BYTEFRAY_RULESET_V4_ID = "bytefray-rules-4"


def _make_app():
    pytest.importorskip("PySide6")
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication

    return QApplication.instance() or QApplication([])


# ---------------------------------------------------------------------------
# Fresh-session Ruleset default
# ---------------------------------------------------------------------------


@pytest.mark.gui
def test_fresh_simple_panel_defaults_to_stable_v4_not_v2():
    """A brand-new Simple tab, before any agent is ever selected, must show
    the permanent stable V4 identity -- not Ruleset v2, which the pre-Phase-1
    Designer showed purely because it was item 0 in the combo's option list."""

    _make_app()
    from app.views.simple import SimplePanel

    panel = SimplePanel(catalog=None)
    try:
        assert panel.ruleset.currentData() == BYTEFRAY_RULESET_V4_ID
    finally:
        panel.deleteLater()


@pytest.mark.gui
def test_fresh_advanced_panel_defaults_to_stable_v4_not_v2(tmp_path):
    """Advanced must agree with Simple on the fresh-session default -- the
    user-reported bug was exactly that the two tabs agreed on the *wrong*
    one (v2)."""

    _make_app()
    from app.views.advanced import AdvancedPanel

    panel = AdvancedPanel(catalog=None, data_root=tmp_path)
    try:
        assert panel.ruleset.currentData() == BYTEFRAY_RULESET_V4_ID
    finally:
        panel.deleteLater()


@pytest.mark.gui
def test_fresh_development_panel_ruleset_combo_defaults_to_stable_v4():
    """Development's Ruleset combo also starts here before any agent is
    selected, even though it is immediately re-derived from the selected
    agent's own Agent API version once one is chosen (unchanged by this
    phase)."""

    _make_app()
    from app.views.development import AgentDevelopmentPanel

    panel = AgentDevelopmentPanel()
    try:
        assert panel.rulesetCombo.currentData() == BYTEFRAY_RULESET_V4_ID
    finally:
        panel.deleteLater()


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
def test_designer_main_window_simple_and_advanced_agree_on_the_fresh_default(
    monkeypatch, tmp_path
):
    """End-to-end through the real ``AgentDesigner`` window: Simple and
    Advanced must show the identical Ruleset on first launch, before
    ``refresh_agents`` ever runs."""

    pytest.importorskip("PySide6")
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication

    from app.agent_designer import AgentDesigner

    monkeypatch.setenv("BYTEFRAY_ROOT", str(tmp_path / "data"))
    QApplication.instance() or QApplication([])
    designer = AgentDesigner()
    try:
        assert designer.simple.ruleset.currentData() == BYTEFRAY_RULESET_V4_ID
        assert designer.advanced.ruleset.currentData() == BYTEFRAY_RULESET_V4_ID
    finally:
        designer.deleteLater()
