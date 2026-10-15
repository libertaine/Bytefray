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


def _assert_default_development_artifacts(development, parameters):
    import json

    from battle_engine.result_model import read_result, verify_result_replay

    assert "Complete" in development.testStatusLabel.text()
    path = development.last_test_result_path()
    assert path is not None
    replay = development.last_test_replay_path()
    trace = development.last_test_trace_path()
    assert replay == path.with_name("replay.jsonl")
    assert trace == path.with_name("trace.jsonl") and trace.is_file()
    assert verify_result_replay(path)
    result = read_result(path)
    assert result.ruleset_id == development.selected_ruleset_id() == "bytefray-rules-6-alpha1"
    assert result.entrants[0]["metadata"]["parameters"] == parameters
    assert all(entrant["diagnostic"] is None for entrant in result.entrants)
    body = json.loads(path.read_text())
    assert body["status"] == "completed"
    assert body["ticks"] == 200 or body["termination_reason"] == "last_agent_standing"
    header = json.loads(replay.read_text().splitlines()[0])
    assert header["ruleset_id"] == result.ruleset_id and header["schema_version"] == 4
    trace_header = json.loads(trace.read_text().splitlines()[0])
    assert trace_header["supervised"] and trace_header["schema_version"] == 2
    return path, replay


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


@pytest.mark.parametrize("seat", ["A", "B"])
def test_keeper_native_copy_validate_edit_full_match_reopen(tmp_path, monkeypatch, seat):
    """Real Qt widgets/native children; external viewer controls qualify separately."""
    pytest.importorskip("PySide6")
    import json

    from battle_engine.agent_parameters import AgentParameterError, resolve_parameters
    from battle_engine.agents import agent_spec_from_dir
    from battle_engine.result_model import read_result
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QApplication, QDialogButtonBox, QLabel

    from app.agent_designer import AgentDesigner
    from app.views.development import NewAgentDialog

    monkeypatch.setenv("QT_QPA_PLATFORM", "windows" if sys.platform == "win32" else "xcb")
    monkeypatch.setenv("BYTEFRAY_ROOT", str(tmp_path))
    monkeypatch.setenv("BYTEFRAY_AGENTS_DIR", str(tmp_path / "agents"))
    app = QApplication.instance() or QApplication([])
    assert app.platformName() == ("windows" if sys.platform == "win32" else "xcb")
    dialog = NewAgentDialog(tmp_path)
    dialog.show()
    dialog.agentId.setText("personal_keeper")
    index = dialog.templateCombo.findData("watchful_keeper")
    assert dialog.templateCombo.itemText(index) == "Watchful Keeper — personal copy"
    dialog.templateCombo.setCurrentIndex(index)
    QTest.mouseClick(dialog.findChild(QDialogButtonBox).button(QDialogButtonBox.Ok), Qt.LeftButton)
    assert dialog.result is not None
    source = tmp_path / "agents/personal_keeper/agent.py"
    manifest = json.loads(source.with_name("agent.yaml").read_text())
    assert manifest["capabilities"] == {"version": 1, "required": ["sense"]}
    duplicate = NewAgentDialog(tmp_path)
    duplicate.agentId.setText("personal_keeper")
    duplicate.templateCombo.setCurrentIndex(duplicate.templateCombo.findData("watchful_keeper"))
    QTest.mouseClick(duplicate.findChild(QDialogButtonBox).button(QDialogButtonBox.Ok), Qt.LeftButton)
    assert duplicate.result is None
    designer = AgentDesigner()
    designer.show()
    try:
        development = designer.development
        designer.tabs.setCurrentWidget(development)
        development.selectAgent("personal_keeper")
        assert development.selected_ruleset_id() == "bytefray-rules-4"
        QTest.mouseClick(development.btnValidate, Qt.LeftButton)
        _wait(app, designer)
        assert "capabilit" in development.statusLabel.text().lower()
        development.rulesetCombo.setCurrentIndex(development.rulesetCombo.findData("bytefray-rules-6-alpha1"))
        QTest.mouseClick(development.btnValidate, Qt.LeftButton)
        _wait(app, designer)
        assert "Last validation: Valid" in development.statusLabel.text()
        advanced = designer.advanced
        designer.tabs.setCurrentWidget(advanced)
        assert advanced.ruleset.currentData() == "bytefray-rules-4"
        advanced.ruleset.setCurrentIndex(advanced.ruleset.findData("bytefray-rules-6-alpha1"))
        advanced.agentA.setCurrentIndex(advanced.agentA.findData("personal_keeper" if seat == "A" else "v4_scout"))
        advanced.agentB.setCurrentIndex(advanced.agentB.findData("personal_keeper" if seat == "B" else "v4_scout"))
        schema = advanced.schemaA if seat == "A" else advanced.schemaB
        schema._controls["scan_interval"].setValue(3)
        schema._controls["perimeter_offset"].setValue(64)
        advanced.ticks.setValue(100)
        QTest.mouseClick(advanced.btnRun, Qt.LeftButton)
        _wait(app, designer)
        path = Path(designer._last_result_path)
        result = read_result(path)
        index = 0 if seat == "A" else 1
        assert result.entrants[index]["metadata"]["parameters"] == {"scan_interval": 3, "perimeter_offset": 64}
        assert json.loads(path.read_text())["status"] == "completed"
        launched = []
        monkeypatch.setattr("app.agent_designer.open_pygame_client_direct", lambda root, replay: launched.append(replay))
        designer._on_open_replay()
        assert launched == [path.with_name("replay.jsonl")]
        schema._controls["scan_interval"].setValue(5)
        app.processEvents()
        assert designer._last_result_path == path
        labels = "\n".join(label.text() for label in advanced.findChildren(QLabel)).lower()
        assert "earlier" in labels and "settings" in labels
        with pytest.raises(AgentParameterError):
            resolve_parameters(agent_spec_from_dir(source.parent).parameter_schema, overrides={"scan_interval": 1})
        source.write_bytes(source.read_bytes() + b"\n# Personal revision after match.\n")
        development.reloadSource()
        app.processEvents()
        assert "Last validation: Valid" not in development.statusLabel.text()
        assert path.is_file()
        designer._on_open_replay()
        assert launched[-1] == path.with_name("replay.jsonl")
        assert designer.grab().save(str(tmp_path / f"keeper_{seat}.png"))
        # Keep the manifest-default Test assertion after the independent
        # Advanced checks so a Test route failure retains the other evidence.
        designer.tabs.setCurrentWidget(development)
        QTest.mouseClick(development.btnTest, Qt.LeftButton)
        _wait(app, designer)
        test_path, test_replay = _assert_default_development_artifacts(
            development, {"scan_interval": 4, "perimeter_offset": 27},
        )
        assert test_path != path
        designer._on_open_test_replay()
        assert launched[-1] == test_replay
        assert designer._last_result_path == path and path.is_file()
        designer._on_open_replay()
        assert launched[-1] == path.with_name("replay.jsonl")
        assert result.entrants[index]["metadata"]["parameters"] == {"scan_interval": 3, "perimeter_offset": 64}
        labels = "\n".join(label.text() for label in advanced.findChildren(QLabel)).lower()
        assert "earlier" in labels and "settings" in labels
        assert designer.grab().save(str(tmp_path / f"keeper_{seat}_test.png"))
    finally:
        designer.close()
        designer.deleteLater()
        dialog.deleteLater()
        duplicate.deleteLater()
        app.processEvents()


def test_scout_native_manifest_default_development_test(tmp_path, monkeypatch):
    """Explicit Alpha 1 uses the real QProcess CLI, independently of Advanced edits."""
    pytest.importorskip("PySide6")
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QApplication, QDialogButtonBox

    from app.agent_designer import AgentDesigner
    from app.views.development import NewAgentDialog

    monkeypatch.setenv("QT_QPA_PLATFORM", "windows" if sys.platform == "win32" else "xcb")
    monkeypatch.setenv("BYTEFRAY_ROOT", str(tmp_path))
    monkeypatch.setenv("BYTEFRAY_AGENTS_DIR", str(tmp_path / "agents"))
    app = QApplication.instance() or QApplication([])
    assert app.platformName() == ("windows" if sys.platform == "win32" else "xcb")
    dialog = NewAgentDialog(tmp_path)
    dialog.show()
    dialog.agentId.setText("personal_scout")
    dialog.templateCombo.setCurrentIndex(dialog.templateCombo.findData("window_scout"))
    QTest.mouseClick(dialog.findChild(QDialogButtonBox).button(QDialogButtonBox.Ok), Qt.LeftButton)
    assert dialog.result is not None
    designer = AgentDesigner()
    designer.show()
    try:
        development = designer.development
        designer.tabs.setCurrentWidget(development)
        development.selectAgent("personal_scout")
        assert development.selected_ruleset_id() == "bytefray-rules-4"
        assert not development.btnTest.isEnabled()
        development.rulesetCombo.setCurrentIndex(development.rulesetCombo.findData("bytefray-rules-6-alpha1"))
        QTest.mouseClick(development.btnValidate, Qt.LeftButton)
        _wait(app, designer)
        assert "Last validation: Valid" in development.statusLabel.text()
        advanced = designer.advanced
        designer.tabs.setCurrentWidget(advanced)
        advanced.ruleset.setCurrentIndex(advanced.ruleset.findData("bytefray-rules-6-alpha1"))
        advanced.agentA.setCurrentIndex(advanced.agentA.findData("personal_scout"))
        advanced.schemaA._controls["search_interval"].setValue(2)
        advanced.schemaA._controls["move_step"].setValue(32)
        launched = []
        monkeypatch.setattr("app.agent_designer.open_pygame_client_direct", lambda root, replay: launched.append(replay))
        designer.tabs.setCurrentWidget(development)
        QTest.mouseClick(development.btnTest, Qt.LeftButton)
        _wait(app, designer)
        _, replay = _assert_default_development_artifacts(development, {"search_interval": 4, "move_step": 64})
        designer._on_open_test_replay()
        assert launched == [replay]
        assert advanced.schemaA._controls["search_interval"].value() == 2
        assert advanced.schemaA._controls["move_step"].value() == 32
        assert designer.grab().save(str(tmp_path / "scout_test.png"))
    finally:
        designer.close()
        designer.deleteLater()
        dialog.deleteLater()
        app.processEvents()
