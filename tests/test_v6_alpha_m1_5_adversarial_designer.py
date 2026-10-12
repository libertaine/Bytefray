"""Independent M1-5 Qt state probes; no research input or execution."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.gui


def test_validation_verdict_is_scoped_when_selected_ruleset_changes(tmp_path, monkeypatch):
    pytest.importorskip("PySide6")
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    monkeypatch.setenv("BYTEFRAY_ROOT", str(tmp_path))
    monkeypatch.setenv("BYTEFRAY_AGENTS_DIR", str(tmp_path / "agents"))
    from battle_engine.agent_scaffold import create_agent
    from battle_engine.rules import BYTEFRAY_RULESET_V4_ID, BYTEFRAY_RULESET_V6_ALPHA1_ID
    from PySide6.QtWidgets import QApplication

    from app.services.agent_catalog import AgentCatalog
    from app.services.agent_workflows import ValidationPresentation
    from app.views.development import AgentDevelopmentPanel

    app = QApplication.instance() or QApplication([])
    create_agent("personal_scout", data_root=tmp_path, template="window_scout")
    panel = AgentDevelopmentPanel(AgentCatalog(tmp_path))
    try:
        panel.setAgents(AgentCatalog(tmp_path).list_agents())
        panel.selectAgent("personal_scout")
        panel.rulesetCombo.setCurrentIndex(panel.rulesetCombo.findData(BYTEFRAY_RULESET_V6_ALPHA1_ID))
        panel.show_validation_result(ValidationPresentation(
            agent_id="personal_scout", valid=True, api_version=2, dry_run_action="sense",
        ))
        assert "Last validation: Valid" in panel.statusLabel.text()
        panel.rulesetCombo.setCurrentIndex(panel.rulesetCombo.findData(BYTEFRAY_RULESET_V4_ID))
        app.processEvents()
        assert not panel.btnTest.isEnabled()
        text = panel.statusLabel.text()
        assert "Last validation: Valid" not in text or (
            BYTEFRAY_RULESET_V6_ALPHA1_ID in text and any(
                word in text.lower() for word in ("earlier", "previous", "changed")
            )
        ), "A SENSE dry-run verdict remains unqualified Valid under stable v4, which refuses SENSE."
    finally:
        panel.close()
        panel.deleteLater()
        app.processEvents()


def test_changed_parameters_label_completed_match_as_earlier_settings(tmp_path, monkeypatch):
    pytest.importorskip("PySide6")
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    monkeypatch.setenv("BYTEFRAY_ROOT", str(tmp_path))
    monkeypatch.setenv("BYTEFRAY_AGENTS_DIR", str(tmp_path / "agents"))
    from battle_engine.agent_scaffold import create_agent
    from battle_engine.result_model import read_result
    from battle_engine.rules import BYTEFRAY_RULESET_V6_ALPHA1_ID
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QApplication, QLabel
    from test_v6_alpha_m1_5_designer import _wait

    from app.agent_designer import AgentDesigner

    app = QApplication.instance() or QApplication([])
    create_agent("personal_scout", data_root=tmp_path, template="window_scout")
    designer = AgentDesigner()
    try:
        advanced = designer.advanced
        advanced.ruleset.setCurrentIndex(advanced.ruleset.findData(BYTEFRAY_RULESET_V6_ALPHA1_ID))
        advanced.agentA.setCurrentIndex(advanced.agentA.findData("personal_scout"))
        advanced.agentB.setCurrentIndex(advanced.agentB.findData("v4_scout"))
        advanced.ticks.setValue(3)
        advanced.schemaA._controls["search_interval"].setValue(2)
        advanced.schemaA._controls["move_step"].setValue(32)
        QTest.mouseClick(advanced.btnRun, Qt.LeftButton)
        _wait(app, designer)
        assert designer._last_result_path is not None, advanced.log.toPlainText()
        result = read_result(designer._last_result_path)
        assert result.entrants[0]["metadata"]["parameters"] == {"search_interval": 2, "move_step": 32}
        previous_result_path = designer._last_result_path
        advanced.schemaA._controls["search_interval"].setValue(3)
        app.processEvents()
        assert designer._last_result_path == previous_result_path
        display = "\n".join(
            [label.text() for label in advanced.findChildren(QLabel)]
            + [advanced.table.item(row, column).text()
               for row in range(advanced.table.rowCount()) for column in range(advanced.table.columnCount())
               if advanced.table.item(row, column) is not None]
            + [advanced.log.toPlainText()]
        ).lower()
        assert any(word in display for word in ("earlier settings", "previous settings", "settings changed", "earlier revision")), (
            "Edited parameters leave the completed match looking applicable to the current settings."
        )
    finally:
        designer.close()
        designer.deleteLater()
        app.processEvents()


def test_reloaded_external_source_change_scopes_previous_validation(tmp_path, monkeypatch):
    pytest.importorskip("PySide6")
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    monkeypatch.setenv("BYTEFRAY_ROOT", str(tmp_path))
    monkeypatch.setenv("BYTEFRAY_AGENTS_DIR", str(tmp_path / "agents"))
    from battle_engine.agent_scaffold import create_agent
    from battle_engine.rules import BYTEFRAY_RULESET_V6_ALPHA1_ID
    from PySide6.QtWidgets import QApplication

    from app.services.agent_catalog import AgentCatalog
    from app.services.agent_workflows import ValidationPresentation
    from app.views.development import AgentDevelopmentPanel

    app = QApplication.instance() or QApplication([])
    scaffold = create_agent("personal_scout", data_root=tmp_path, template="window_scout")
    panel = AgentDevelopmentPanel(AgentCatalog(tmp_path))
    try:
        panel.setAgents(AgentCatalog(tmp_path).list_agents())
        panel.selectAgent("personal_scout")
        panel.rulesetCombo.setCurrentIndex(panel.rulesetCombo.findData(BYTEFRAY_RULESET_V6_ALPHA1_ID))
        panel.show_validation_result(ValidationPresentation(
            agent_id="personal_scout", valid=True, api_version=2, dry_run_action="sense",
        ))
        original = scaffold.source_path.read_bytes()
        scaffold.source_path.write_bytes(original + b"\n# External personal-copy revision.\n")
        panel.reloadSource()
        app.processEvents()
        assert "External personal-copy revision" in panel.pythonSource.toPlainText()
        assert "Last validation: Valid" not in panel.statusLabel.text() or any(
            word in panel.statusLabel.text().lower() for word in ("earlier", "previous", "changed")
        ), "Reloaded source bytes differ, but validation still looks current."
    finally:
        panel.close()
        panel.deleteLater()
        app.processEvents()


def test_reloaded_source_labels_completed_advanced_match_as_earlier_revision(tmp_path, monkeypatch):
    pytest.importorskip("PySide6")
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    monkeypatch.setenv("BYTEFRAY_ROOT", str(tmp_path))
    monkeypatch.setenv("BYTEFRAY_AGENTS_DIR", str(tmp_path / "agents"))
    from battle_engine.agent_scaffold import create_agent
    from battle_engine.rules import BYTEFRAY_RULESET_V6_ALPHA1_ID
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QApplication, QLabel
    from test_v6_alpha_m1_5_designer import _wait

    from app.agent_designer import AgentDesigner

    app = QApplication.instance() or QApplication([])
    scaffold = create_agent("personal_scout", data_root=tmp_path, template="window_scout")
    designer = AgentDesigner()
    try:
        advanced = designer.advanced
        advanced.ruleset.setCurrentIndex(advanced.ruleset.findData(BYTEFRAY_RULESET_V6_ALPHA1_ID))
        advanced.agentA.setCurrentIndex(advanced.agentA.findData("personal_scout"))
        advanced.agentB.setCurrentIndex(advanced.agentB.findData("v4_scout"))
        advanced.ticks.setValue(3)
        QTest.mouseClick(advanced.btnRun, Qt.LeftButton)
        _wait(app, designer)
        previous_result_path = designer._last_result_path
        assert previous_result_path is not None, advanced.log.toPlainText()
        designer.development.selectAgent("personal_scout")
        original = scaffold.source_path.read_bytes()
        scaffold.source_path.write_bytes(original + b"\n# External revision after completed Advanced match.\n")
        designer.development.reloadSource()
        app.processEvents()
        assert designer._last_result_path == previous_result_path
        display = "\n".join(label.text() for label in advanced.findChildren(QLabel)).lower()
        assert "earlier revision" in display or "source changed" in display, (
            "Explicitly reloaded current source changed, but Advanced still presents the prior match without an earlier-revision label."
        )
    finally:
        designer.close()
        designer.deleteLater()
        app.processEvents()
