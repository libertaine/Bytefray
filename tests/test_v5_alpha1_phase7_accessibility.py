"""Focused accessibility regressions for V5 Alpha 1 Phase 7.

These tests exercise stable Qt contracts rather than platform-specific focus
rendering or pixel geometry: label/buddy relationships, concise accessible
names/descriptions, and keyboard activation of important table rows.
"""

from __future__ import annotations

import os
from pathlib import Path
from types import SimpleNamespace

import pytest


def _make_app():
    pytest.importorskip("PySide6")
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication

    return QApplication.instance() or QApplication([])


def _label(container, text: str):
    from PySide6.QtWidgets import QLabel

    return next(label for label in container.findChildren(QLabel) if label.text() == text)


def _assert_buddy(container, text: str, control) -> None:
    assert _label(container, text).buddy() is control


def _tab_reaches(app, window, start, targets: set, *, limit: int = 120) -> None:
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest

    start.setFocus()
    app.processEvents()
    reached = set()
    for _ in range(limit):
        focus = app.focusWidget()
        if focus in targets:
            reached.add(focus)
        if reached == targets:
            return
        QTest.keyClick(window, Qt.Key_Tab)
        app.processEvents()
    missing = [
        widget.accessibleName()
        or (widget.text() if hasattr(widget, "text") else type(widget).__name__)
        for widget in targets - reached
    ]
    raise AssertionError(f"Tab traversal did not reach: {missing}")


def _parameter_schema():
    from battle_engine.agent_parameters import parse_parameter_schema

    return parse_parameter_schema(
        {
            "api_version": 2,
            "parameters": {
                "reach": {
                    "type": "integer",
                    "default": 16,
                    "minimum": 10,
                    "maximum": 64,
                    "description": "How far the process senses and writes.",
                },
                "mode": {
                    "type": "choice",
                    "default": "sweep",
                    "choices": ["sweep", "hold"],
                },
            },
            "presets": {
                "aggressive": {
                    "description": "Press harder.",
                    "values": {"reach": 48, "mode": "hold"},
                }
            },
        }
    )


@pytest.mark.gui
def test_dynamic_agent_parameters_expose_labels_and_help_programmatically() -> None:
    _make_app()
    from app.widgets.agent_parameters import AgentParameterForm

    form = AgentParameterForm("Agent A Parameters")
    try:
        form.set_agent("typed", _parameter_schema())

        assert form._presetLabel.buddy() is form.presets
        assert "named set" in form.presets.accessibleDescription().lower()
        assert "manifest declares" in form.btnReset.accessibleDescription().lower()

        for key, control in form._controls.items():
            label = form._form.labelForField(control)
            assert label is not None
            assert label.text() == key
            assert label.buddy() is control
            assert control.accessibleDescription() == control.toolTip()

        reach_help = form._controls["reach"].accessibleDescription()
        assert "how far" in reach_help.lower()
        assert ">= 10" in reach_help and "<= 64" in reach_help
        assert "default: 16" in reach_help.lower()
    finally:
        form.deleteLater()


@pytest.mark.gui
def test_configuration_dialog_inputs_have_programmatic_labels(tmp_path: Path) -> None:
    _make_app()
    from app.views.development import AgentDevelopmentPanel, NewAgentDialog
    from app.views.evaluation import EvaluationDialog
    from app.views.tournament import TournamentDialog

    new_agent = NewAgentDialog(tmp_path)
    development = AgentDevelopmentPanel()
    evaluation = EvaluationDialog(
        [("Alpha", "alpha"), ("Beta", "beta"), ("Gamma", "gamma")],
        default_candidate="alpha",
        default_output=tmp_path / "evaluation",
    )
    tournament = TournamentDialog([], tmp_path / "tournament")
    try:
        _assert_buddy(new_agent, "Agent ID", new_agent.agentId)
        _assert_buddy(new_agent, "Starting point", new_agent.templateCombo)

        for text, control in (
            ("Agent", development.agentCombo),
            ("Opponent", development.opponentCombo),
            ("Seed", development.seedSpin),
            ("Ticks", development.ticksSpin),
            ("Timeout (s)", development.timeoutSpin),
            ("Ruleset", development.rulesetCombo),
        ):
            _assert_buddy(development, text, control)
        assert development.btnRandomizeSeed.accessibleName() == (
            "Randomize development test seed"
        )
        from PySide6.QtCore import Qt
        from PySide6.QtWidgets import QScrollArea

        dev_scrolls = development.findChildren(QScrollArea)
        assert any(s.focusPolicy() == Qt.FocusPolicy.NoFocus for s in dev_scrolls)

        assert evaluation.opponentsLabel.buddy() is evaluation.opponentsList
        assert evaluation.previewLabel.buddy() is evaluation.previewText
        assert evaluation.outputLabel.buddy() is evaluation.outputEdit
        assert evaluation.chooseOutputButton.accessibleName() == (
            "Choose evaluation output folder"
        )

        assert tournament.agentsLabel.buddy() is tournament.agents
        assert tournament.outputLabel.buddy() is tournament.output
        assert tournament.chooseOutputButton.accessibleName() == (
            "Choose tournament output folder"
        )
    finally:
        for widget in (new_agent, development, evaluation, tournament):
            widget.deleteLater()


@pytest.mark.gui
def test_dense_result_and_history_widgets_have_concise_accessible_names(
    monkeypatch,
    tmp_path: Path,
) -> None:
    _make_app()
    from PySide6.QtWidgets import QLabel, QScrollArea

    from app.services.designer_workflows import EvaluationPresentation
    from app.services.tournament_results import TournamentResults
    from app.views.evaluation import EvaluationResultsDialog
    from app.views.evaluation_history import EvaluationHistoryDialog
    from app.views.tournament import TournamentHistoryDialog, TournamentResultsDialog

    monkeypatch.setattr(
        "app.views.evaluation._build_visual_evidence_panel",
        lambda _p: QLabel("Visual metrics"),
    )

    tournament_results = TournamentResultsDialog(
        TournamentResults(
            output_dir=tmp_path / "cup",
            tournament_id="cup",
            division="vm",
            finished=False,
            standings=(),
            matches=(),
            ruleset_ids=(),
        )
    )
    tournament_history = TournamentHistoryDialog(tmp_path)
    evaluation_results = EvaluationResultsDialog(
        EvaluationPresentation(
            evaluation_id="evaluation",
            candidate_id="alpha",
            baseline_id=None,
            ticks=200,
            state_path=tmp_path / "evaluation.json",
            cells=(),
            aggregates=(),
            comparison=(),
        )
    )
    evaluation_history = EvaluationHistoryDialog(tmp_path, allow_restore=False)
    try:
        expected = (
            (tournament_results.standingsTable, "Tournament standings"),
            (tournament_results.matchesTable, "Tournament matches"),
            (tournament_results.matchDetail, "Selected tournament match details"),
            (tournament_results.replayStatusLabel, "Tournament replay status"),
            (tournament_history.table, "Tournament history"),
            (tournament_history.statusLabel, "Tournament history status"),
            (evaluation_results.resultsList, "Evaluation results"),
            (evaluation_results.detailText, "Selected evaluation result details"),
            (evaluation_results.findChild(QScrollArea), "Evaluation metric visuals"),
            (evaluation_history.list, "Evaluation history"),
            (evaluation_history.detailText, "Evaluation details"),
            (evaluation_history.visualPanelScroll, "Evaluation metric visuals"),
            (evaluation_history.cellsList, "Evaluation cells"),
            (evaluation_history.verifyStatusLabel, "Evaluation verification status"),
        )
        for widget, name in expected:
            assert widget.accessibleName() == name
    finally:
        for widget in (
            tournament_results,
            tournament_history,
            evaluation_results,
            evaluation_history,
        ):
            widget.close()
            widget.deleteLater()


@pytest.mark.gui
def test_qt_accessibility_interface_exposes_roles_values_headers_and_tabs(
    tmp_path: Path,
) -> None:
    _make_app()
    from PySide6.QtGui import QAccessible

    from app.services.tournament_results import TournamentResults
    from app.views.advanced import AdvancedPanel
    from app.views.tournament import TournamentResultsDialog
    from app.widgets.agent_parameters import AgentParameterForm

    form = AgentParameterForm("Agent A Parameters")
    form.set_agent("typed", _parameter_schema())
    advanced = AdvancedPanel(catalog=None, data_root=tmp_path)
    results = TournamentResultsDialog(
        TournamentResults(tmp_path, "cup", "vm", False, (), (), ())
    )
    try:
        reach = QAccessible.queryAccessibleInterface(form._controls["reach"])
        assert reach.role() == QAccessible.Role.SpinBox
        assert reach.text(QAccessible.Text.Name) == "reach"
        assert reach.text(QAccessible.Text.Value) == "16"
        assert ">= 10" in reach.text(QAccessible.Text.Description)
        assert not reach.state().disabled

        seed = QAccessible.queryAccessibleInterface(advanced.seed)
        assert seed.role() == QAccessible.Role.SpinBox
        assert seed.text(QAccessible.Text.Name) == "Random seed"

        table = QAccessible.queryAccessibleInterface(results.standingsTable)
        assert table.role() == QAccessible.Role.Table
        assert table.text(QAccessible.Text.Name) == "Tournament standings"
        child_roles_and_names = {
            (table.child(index).role(), table.child(index).text(QAccessible.Text.Name))
            for index in range(table.childCount())
        }
        assert (QAccessible.Role.ColumnHeader, "Rank") in child_roles_and_names
        assert (QAccessible.Role.ColumnHeader, "Entrant") in child_roles_and_names

        replay_button = QAccessible.queryAccessibleInterface(results.viewReplayButton)
        assert replay_button.role() == QAccessible.Role.Button
        assert replay_button.text(QAccessible.Text.Name) == "View Replay"
        assert replay_button.state().disabled

        tabs = QAccessible.queryAccessibleInterface(advanced.tabs)
        tab_list = next(
            tabs.child(index)
            for index in range(tabs.childCount())
            if tabs.child(index).role() == QAccessible.Role.PageTabList
        )
        tab_names = [
            tab_list.child(index).text(QAccessible.Text.Name)
            for index in range(tab_list.childCount())
            if tab_list.child(index).role() == QAccessible.Role.PageTab
        ]
        assert tab_names == ["Match Setup", "Agent Params", "Replay Browser", "Results"]
        assert tab_list.child(0).state().selected
    finally:
        for widget in (form, advanced, results):
            widget.deleteLater()


@pytest.mark.gui
def test_primary_designer_pages_have_keyboard_only_focus_paths(
    monkeypatch, tmp_path: Path
) -> None:
    app = _make_app()
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest

    from app.agent_designer import AgentDesigner

    monkeypatch.setenv("BYTEFRAY_ROOT", str(tmp_path / "data"))
    designer = AgentDesigner()
    try:
        designer.show()
        designer.activateWindow()
        app.processEvents()

        designer.tabs.setCurrentWidget(designer.simple)
        _tab_reaches(
            app,
            designer,
            designer.simple.ruleset,
            {
                designer.simple.agentA,
                designer.simple.agentB,
                designer.simple.gridSize,
                designer.simple.ticks,
                designer.simple.btnRun,
                designer.simple.btnRefresh,
            },
        )

        designer.tabs.setCurrentWidget(designer.advanced)
        designer.advanced.tabs.setCurrentIndex(0)
        _tab_reaches(
            app,
            designer,
            designer.advanced.ruleset,
            {
                designer.advanced.agentA,
                designer.advanced.agentB,
                designer.advanced.btnAddAgent,
                designer.advanced.arena,
                designer.advanced.ticks,
                designer.advanced.seed,
                designer.advanced.btnRandomizeSeed,
                designer.advanced.btnRun,
                designer.advanced.btnRefresh,
            },
        )

        designer.tabs.setCurrentWidget(designer.development)
        _tab_reaches(
            app,
            designer,
            designer.development.agentCombo,
            {
                designer.development.btnRefresh,
                designer.development.btnNewAgent,
                designer.development.btnOpenFolder,
                designer.development.btnExportAgent,
                designer.development.sourceTabs.tabBar(),
                designer.development.pythonSource,
                designer.development.btnValidate,
                designer.development.opponentCombo,
                designer.development.seedSpin,
                designer.development.btnRandomizeSeed,
                designer.development.ticksSpin,
                designer.development.timeoutSpin,
                designer.development.rulesetCombo,
                designer.development.btnTest,
                designer.development.btnEvaluate,
            },
        )

        designer.development.sourceTabs.tabBar().setFocus()
        QTest.keyClick(designer.development.sourceTabs.tabBar(), Qt.Key_Right)
        assert designer.development.sourceTabs.currentIndex() == 1
        designer.development.manifestSource.setFocus()
        app.processEvents()
        assert app.focusWidget() is designer.development.manifestSource

        designer.tabs.tabBar().setFocus()
        designer.tabs.setCurrentIndex(0)
        QTest.keyClick(designer.tabs.tabBar(), Qt.Key_Right)
        assert designer.tabs.currentIndex() == 1
        QTest.keyClick(designer.tabs.tabBar(), Qt.Key_Right)
        assert designer.tabs.currentIndex() == 2
    finally:
        designer.close()
        app.processEvents()
        designer.deleteLater()


@pytest.mark.gui
def test_tournament_match_table_enter_uses_the_same_replay_action(
    monkeypatch, tmp_path: Path
) -> None:
    app = _make_app()
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest

    from app.services.tournament_results import MatchRow, TournamentResults
    from app.views import tournament as tournament_view

    replay = tmp_path / "replay.jsonl"
    replay.write_text("{}\n", encoding="utf-8")
    row = MatchRow(
        number=1,
        round_number=1,
        entrant_ids=("alpha", "beta"),
        entrant_names=("Alpha", "Beta"),
        seed=7,
        status="completed",
        artifact_dir=tmp_path,
        replay_path=replay,
    )
    monkeypatch.setattr(
        tournament_view,
        "preflight_match_replay",
        lambda _match: SimpleNamespace(replay_path=replay),
    )
    monkeypatch.setattr(tournament_view, "replay_preflight_state", lambda _outcome: "ready")
    dialog = tournament_view.TournamentResultsDialog(
        TournamentResults(tmp_path, "cup", "vm", False, (), (row,), ())
    )
    opened: list[Path] = []
    dialog.openReplayRequested.connect(opened.append)
    try:
        dialog.show()
        dialog.tabs.setCurrentIndex(1)
        dialog.matchesTable.selectRow(0)
        dialog.matchesTable.setFocus()
        app.processEvents()
        QTest.keyClick(dialog.matchesTable, Qt.Key_Return)
        app.processEvents()
        assert opened == [replay]
    finally:
        dialog.close()
        dialog.deleteLater()


@pytest.mark.gui
def test_tournament_history_table_enter_uses_the_same_results_action(
    monkeypatch, tmp_path: Path
) -> None:
    app = _make_app()
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest

    from app.services.tournament_results import TournamentHistoryEntry
    from app.views import tournament as tournament_view

    entry = TournamentHistoryEntry(output_dir=tmp_path / "cup", updated_at=1.0)
    monkeypatch.setattr(tournament_view, "discover_tournaments", lambda _root: (entry,))
    dialog = tournament_view.TournamentHistoryDialog(tmp_path)
    opened: list[Path] = []
    monkeypatch.setattr(dialog, "_show_results", opened.append)
    try:
        dialog.show()
        dialog.table.setFocus()
        app.processEvents()
        QTest.keyClick(dialog.table, Qt.Key_Return)
        app.processEvents()
        assert opened == [entry.output_dir]
    finally:
        dialog.close()
        dialog.deleteLater()
