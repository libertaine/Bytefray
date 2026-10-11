"""M1-5 authoring workflow through real Qt widgets and native subprocesses."""

from __future__ import annotations

import sys
import time
from pathlib import Path

import pytest

pytestmark = pytest.mark.gui


def _wait(app, designer):
    from PySide6.QtCore import QProcess

    deadline = time.monotonic() + 30
    while designer._proc is not None and designer._proc.state() != QProcess.NotRunning and time.monotonic() < deadline:
        app.processEvents()
        time.sleep(.01)
    app.processEvents()
    assert designer._proc is not None and designer._proc.state() == QProcess.NotRunning, "native product subprocess did not finish"


@pytest.mark.skipif(sys.platform != "win32", reason="bounded native Windows Qt smoke")
def test_native_windows_designer_window_selection_and_parameters(tmp_path, monkeypatch):
    pytest.importorskip("PySide6")
    monkeypatch.setenv("QT_QPA_PLATFORM", "windows")
    monkeypatch.setenv("BYTEFRAY_ROOT", str(tmp_path))
    monkeypatch.setenv("BYTEFRAY_AGENTS_DIR", str(tmp_path / "agents"))
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QApplication

    from app.agent_designer import AgentDesigner

    app = QApplication.instance() or QApplication([])
    if app.platformName() != "windows":
        pytest.skip("run this smoke alone in a fresh process for the native Windows platform")
    designer = AgentDesigner()
    try:
        designer.show()
        designer.tabs.setCurrentWidget(designer.advanced)
        app.processEvents()
        advanced = designer.advanced
        advanced.ruleset.setFocus()
        QTest.keyClick(advanced.ruleset, Qt.Key_Down)
        app.processEvents()
        assert advanced.ruleset.currentData() == "bytefray-rules-6-alpha1"
        advanced.agentA.setCurrentIndex(advanced.agentA.findData("v6_window_scout"))
        advanced.schemaA._controls["search_interval"].setValue(2)
        advanced.schemaA._controls["move_step"].setValue(32)
        advanced.tabs.setCurrentIndex(0)
        app.processEvents()
        assert designer.isVisible()
        assert designer.grab().save(str(tmp_path / "designer.png"))
    finally:
        designer.close()
        designer.deleteLater()
        app.processEvents()


def test_window_scout_copy_validate_edit_run_replay_and_repeat(tmp_path, monkeypatch):
    pytest.importorskip("PySide6")
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    monkeypatch.setenv("BYTEFRAY_ROOT", str(tmp_path))
    monkeypatch.setenv("BYTEFRAY_AGENTS_DIR", str(tmp_path / "agents"))
    from battle_client.sensing import SensingView
    from battle_client.sensing_presentation import load_sensing_presentation
    from battle_client.session import ReplaySession
    from battle_engine.result_model import read_result
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QApplication, QDialogButtonBox

    from app.agent_designer import AgentDesigner
    from app.views.development import NewAgentDialog

    app = QApplication.instance() or QApplication([])
    dialog = NewAgentDialog(tmp_path)
    dialog.agentId.setText("my_window_scout")
    dialog.templateCombo.setCurrentIndex(dialog.templateCombo.findData("window_scout"))
    buttons = dialog.findChild(QDialogButtonBox)
    QTest.mouseClick(buttons.button(QDialogButtonBox.Ok), Qt.LeftButton)
    assert dialog.result is not None
    assert (tmp_path / "agents/my_window_scout/agent.py").is_file()
    designer = AgentDesigner()
    try:
        development = designer.development
        development.selectAgent("my_window_scout")
        assert development.selected_ruleset_id() == "bytefray-rules-4"
        assert not development.btnTest.isEnabled()
        assert "explicitly" in development.rulesetExplanation.text()
        # Validation is allowed here so the engine can report the capability error,
        # before importing the selected agent.
        QTest.mouseClick(development.btnValidate, Qt.LeftButton)
        _wait(app, designer)
        assert "capabilit" in development.statusLabel.text().lower()
        development.rulesetCombo.setCurrentIndex(development.rulesetCombo.findData("bytefray-rules-6-alpha1"))
        assert development.btnTest.isEnabled()
        QTest.mouseClick(development.btnValidate, Qt.LeftButton)
        _wait(app, designer)
        assert "Last validation: Valid" in development.statusLabel.text()

        advanced = designer.advanced
        assert advanced.ruleset.currentData() == "bytefray-rules-4"
        advanced.ruleset.setCurrentIndex(advanced.ruleset.findData("bytefray-rules-6-alpha1"))
        advanced.agentA.setCurrentIndex(advanced.agentA.findData("my_window_scout"))
        advanced.agentB.setCurrentIndex(advanced.agentB.findData("v4_scout"))
        advanced.ticks.setValue(3)
        advanced.schemaA._controls["search_interval"].setValue(2)
        advanced.schemaA._controls["move_step"].setValue(32)
        assert not advanced.parameter_validation_errors()
        assert advanced.schemaA._controls["move_step"].maximum() == 64
        QTest.mouseClick(advanced.btnRun, Qt.LeftButton)
        _wait(app, designer)
        assert designer._last_result_path is not None, advanced.log.toPlainText()
        first_result_path = Path(designer._last_result_path)
        first = read_result(first_result_path)
        assert first.ruleset_id == "bytefray-rules-6-alpha1"
        assert first.entrants[0]["metadata"]["parameters"] == {"search_interval":2,"move_step":32}
        replay = first_result_path.with_name("replay.jsonl")
        session = ReplaySession()
        session.load(replay)
        presentation, reason = load_sensing_presentation(session, replay, replay.with_name("trace.jsonl"), result=first_result_path)
        assert not reason and isinstance(presentation.current_view, SensingView)
        launched = []
        monkeypatch.setattr("app.agent_designer.open_pygame_client_direct", lambda root,path: launched.append(path))
        designer._on_open_replay()
        assert launched == [replay]

        advanced.schemaA._controls["search_interval"].setValue(3)
        advanced.schemaA._controls["move_step"].setValue(16)
        QTest.mouseClick(advanced.btnRun, Qt.LeftButton)
        _wait(app, designer)
        second_result_path = Path(designer._last_result_path)
        second = read_result(second_result_path)
        assert second_result_path != first_result_path
        assert second.result_id != first.result_id
        assert second.entrants[0]["metadata"]["parameters"] == {"search_interval":3,"move_step":16}
        designer._on_open_replay()
        assert launched[-1] == second_result_path.with_name("replay.jsonl")
        assert first_result_path.is_file()
    finally:
        designer.close()
        designer.deleteLater()
        dialog.deleteLater()
        app.processEvents()
