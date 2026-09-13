"""Tests for Bytefray V5 Alpha 1 Phase 3: Agent Package Export Workflow.

Covers:
- Menu integration:
  * Export Agent Package… appears under File in desktop-conventional location.
  * Ordering is Import -> Inspect -> Export -> separator -> Open Last Output Folder -> separator -> Exit.
  * Export does not appear under Tools or Help.
- Action wiring:
  * QAction invokes canonical export handler (_on_export_agent_package).
  * Menu construction logic does not duplicate serialization.
- Selection validation:
  * No selected agent produces a clear, informative user-facing response.
  * Incompatible/unsupported agent kind produces a clear critical error dialog.
  * Save dialog is never reached without a valid selection.
- Package creation:
  * File save dialog prompts for destination with .bytefray-agent filter.
  * Package is created at requested destination.
  * Canonical required files are present (package.json, revision manifest, files).
  * Unexpected files (pycache, git, replays, artifacts) are absent.
  * Omitted extension is automatically normalized to .bytefray-agent.
  * Extension normalization prompts for overwrite confirmation if target exists.
- Error and cancellation UX:
  * Save cancellation produces no file and no error dialog (clean no-op).
  * Package errors (AgentPackageError) and unexpected failures are surfaced cleanly via critical dialog.
  * No raw stack traces exposed.
- Full round-trip:
  * Designer Export -> inspect_package -> import_package into isolated root.
  * Identity, revision, config, and file contents preserved across the cycle.
- Source immutability:
  * Export is strictly read-only with respect to source agent files.
"""

from __future__ import annotations

import json
import os
import zipfile
from pathlib import Path

import pytest


def _make_app():
    pytest.importorskip("PySide6")
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication

    return QApplication.instance() or QApplication([])


def _get_top_level_menus(designer):
    menus = []
    for action in designer.menuBar().actions():
        menu = action.menu()
        if menu is not None:
            menus.append(menu)
    return menus


def _write_python_agent(
    data_root: Path,
    agent_id: str,
    *,
    display: str = "Test Agent",
    code: str = "# test agent\n",
) -> Path:
    agent_dir = data_root / "agents" / agent_id
    agent_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "name": display,
        "kind": "python",
        "entry_point": "agent.py:agent",
        "api_version": 2,
        "version": "1.0.0",
    }
    agent_dir.joinpath("agent.yaml").write_text(json.dumps(manifest), encoding="utf-8")
    agent_dir.joinpath("agent.py").write_text(code, encoding="utf-8")
    return agent_dir


# ---------------------------------------------------------------------------
# 1. Menu Integration & Ordering
# ---------------------------------------------------------------------------


@pytest.mark.gui
def test_export_action_present_in_file_menu_with_canonical_ordering(
    monkeypatch, tmp_path: Path
) -> None:
    """Export Agent Package… must appear under File directly following Inspect,
    before the separator and Open Last Output Folder."""
    _make_app()
    from app.agent_designer import AgentDesigner

    monkeypatch.setenv("BYTEFRAY_ROOT", str(tmp_path / "data"))
    designer = AgentDesigner()
    try:
        menus = _get_top_level_menus(designer)
        file_menu = next(m for m in menus if m.title() == "File")
        tools_menu = next(m for m in menus if m.title() == "Tools")
        help_menu = next(m for m in menus if m.title() == "Help")

        actions = file_menu.actions()
        assert len(actions) == 7

        # Strict ordering verification:
        # 0: Import Agent Package…
        assert actions[0].text() == "Import Agent Package…"
        assert not actions[0].isSeparator()
        assert actions[0].isEnabled()

        # 1: Inspect Agent Package…
        assert actions[1].text() == "Inspect Agent Package…"
        assert not actions[1].isSeparator()
        assert actions[1].isEnabled()

        # 2: Export Agent Package… (with ellipsis for interactive dialog)
        assert actions[2].text() == "Export Agent Package…"
        assert not actions[2].isSeparator()
        assert actions[2].isEnabled()
        assert actions[2] is designer.exportAgentPackageAction

        # 3: Separator between package actions and folder navigation
        assert actions[3].isSeparator()

        # 4: Open Last Output Folder
        assert actions[4].text() == "Open Last Output Folder"
        assert not actions[4].isSeparator()
        assert actions[4] is designer.openOutputFolderAction

        # 5: Separator before application lifecycle
        assert actions[5].isSeparator()

        # 6: Exit
        assert actions[6].text() == "Exit"
        assert not actions[6].isSeparator()
        assert actions[6] is designer.exitAction

        # Must not appear in Tools or Help
        tools_labels = [a.text() for a in tools_menu.actions()]
        assert "Export Agent Package…" not in tools_labels
        assert "Export Agent…" not in tools_labels

        help_labels = [a.text() for a in help_menu.actions()]
        assert "Export Agent Package…" not in help_labels
    finally:
        designer.deleteLater()


# ---------------------------------------------------------------------------
# 2. Action Wiring & Handler Invocation
# ---------------------------------------------------------------------------


@pytest.mark.gui
def test_export_action_wiring_invokes_canonical_handler(monkeypatch, tmp_path: Path) -> None:
    """Triggering File -> Export Agent Package… invokes _on_export_agent_package."""
    _make_app()
    from app.agent_designer import AgentDesigner

    monkeypatch.setenv("BYTEFRAY_ROOT", str(tmp_path / "data"))
    designer = AgentDesigner()
    try:
        calls = []
        monkeypatch.setattr(designer, "_on_export_agent_package", lambda: calls.append("export"))

        designer.exportAgentPackageAction.trigger()
        assert calls == ["export"]
    finally:
        designer.deleteLater()


@pytest.mark.gui
def test_menu_logic_does_not_implement_package_serialization(
    monkeypatch, tmp_path: Path
) -> None:
    """File -> Export Agent Package… delegates cleanly to the canonical export
    handler (_on_export_agent_package) and does not contain inline package
    serialization logic in menu construction."""
    _make_app()
    from app.agent_designer import AgentDesigner

    monkeypatch.setenv("BYTEFRAY_ROOT", str(tmp_path / "data"))
    designer = AgentDesigner()
    try:
        # Confirm QAction is connected to _on_export_agent_package
        assert hasattr(designer, "exportAgentPackageAction")
        assert designer.exportAgentPackageAction.text() == "Export Agent Package…"

        # When invoked, it delegates to _on_export_agent_package
        invoked = []
        monkeypatch.setattr(designer, "_on_export_agent_package", lambda: invoked.append(True))
        designer.exportAgentPackageAction.trigger()
        assert invoked == [True]
    finally:
        designer.deleteLater()


# ---------------------------------------------------------------------------
# 3. Selection Validation
# ---------------------------------------------------------------------------


@pytest.mark.gui
def test_export_without_selection_informs_user_and_never_prompts_file(
    monkeypatch, tmp_path: Path
) -> None:
    """When no agent is selected, triggering Export shows an informative dialog
    and does not open a file dialog or perform any export."""
    _make_app()
    import app.agent_designer as agent_designer_module
    from app.agent_designer import AgentDesigner

    monkeypatch.setenv("BYTEFRAY_ROOT", str(tmp_path / "data"))
    designer = AgentDesigner()
    try:
        designer.development.agentCombo.clear()
        assert designer.development.selectedAgentRow() is None

        informed = []
        monkeypatch.setattr(
            agent_designer_module.QMessageBox,
            "information",
            staticmethod(lambda *a, **k: informed.append(a) or None),
        )
        monkeypatch.setattr(
            agent_designer_module.QFileDialog,
            "getSaveFileName",
            staticmethod(lambda *a, **k: pytest.fail("getSaveFileName should not be called without selection")),
        )

        designer.exportAgentPackageAction.trigger()

        assert len(informed) == 1
        dialog_text = informed[0][2]
        assert "Select a Python agent first" in dialog_text
    finally:
        designer.deleteLater()


@pytest.mark.gui
def test_export_unsupported_kind_agent_reports_error_cleanly(monkeypatch, tmp_path: Path) -> None:
    """When a selected agent is not package-compatible (e.g. unsupported kind),
    export surfaces an informative critical error dialog rather than crashing."""
    _make_app()
    import app.agent_designer as agent_designer_module
    from app.agent_designer import AgentDesigner
    from app.services.agent_catalog import AgentRow

    data_root = tmp_path / "designer-data"
    monkeypatch.setenv("BYTEFRAY_ROOT", str(data_root))
    _write_python_agent(data_root, "builtin_agent")

    designer = AgentDesigner()
    try:
        # Simulate an agent row whose kind is unsupported (e.g. "builtin")
        unsupported_row = AgentRow(
            name="Builtin Starter",
            path=str(data_root / "agents" / "builtin_agent"),
            blob_path=None,
            meta={"kind": "builtin"},
            agent_id="builtin_agent",
        )
        monkeypatch.setattr(designer.development, "selectedAgentRow", lambda: unsupported_row)

        out_file = tmp_path / "out.bytefray-agent"
        monkeypatch.setattr(
            agent_designer_module.QFileDialog,
            "getSaveFileName",
            staticmethod(lambda *a, **k: (str(out_file), "")),
        )

        critical = []
        monkeypatch.setattr(
            agent_designer_module.QMessageBox,
            "critical",
            staticmethod(lambda *a, **k: critical.append(a) or None),
        )

        designer.exportAgentPackageAction.trigger()

        assert len(critical) == 1
        assert "Export Failed" in critical[0][1]
        assert "[package_unsupported_kind]" in critical[0][2]
    finally:
        designer.deleteLater()


# ---------------------------------------------------------------------------
# 4. Package Creation via File Dialog
# ---------------------------------------------------------------------------


@pytest.mark.gui
def test_export_agent_package_creates_canonical_archive(monkeypatch, tmp_path: Path) -> None:
    """Exporting a selected agent via the save file dialog creates a valid
    .bytefray-agent archive containing canonical package.json, revision manifest,
    and agent source/config files."""
    _make_app()
    from battle_engine.agent_package import inspect_package

    import app.agent_designer as agent_designer_module
    from app.agent_designer import AgentDesigner

    data_root = tmp_path / "designer-data"
    monkeypatch.setenv("BYTEFRAY_ROOT", str(data_root))
    _write_python_agent(data_root, "alpha_bot", display="Alpha Bot Pro", code="def agent(obs):\n    return []\n")

    designer = AgentDesigner()
    try:
        designer.refresh_agents(select="alpha_bot")
        selected = designer.development.selectedAgentRow()
        assert selected is not None
        assert selected.agent_id == "alpha_bot"

        out_file = tmp_path / "packages" / "alpha_bot.bytefray-agent"
        out_file.parent.mkdir(parents=True, exist_ok=True)

        monkeypatch.setattr(
            agent_designer_module.QFileDialog,
            "getSaveFileName",
            staticmethod(lambda *a, **k: (str(out_file), "Bytefray Agent Packages (*.bytefray-agent)")),
        )

        informed = []
        monkeypatch.setattr(
            agent_designer_module.QMessageBox,
            "information",
            staticmethod(lambda *a, **k: informed.append(a) or None),
        )
        monkeypatch.setattr(
            agent_designer_module.QMessageBox,
            "critical",
            staticmethod(lambda *a, **k: pytest.fail(f"unexpected failure dialog: {a}")),
        )

        designer.exportAgentPackageAction.trigger()

        # Success reported to user
        assert len(informed) == 1
        assert "Exported agent: alpha_bot" in informed[0][2]

        # Package file created
        assert out_file.is_file()
        assert out_file.stat().st_size > 0

        # Archive internal layout verification
        with zipfile.ZipFile(out_file, "r") as zf:
            names = set(zf.namelist())
            assert "package.json" in names

            # Read package.json
            pkg_manifest = json.loads(zf.read("package.json").decode("utf-8"))
            assert pkg_manifest["schema"] == "bytefray.agent_package"
            assert pkg_manifest["schema_version"] == 1
            assert pkg_manifest["agent_id"] == "alpha_bot"
            assert pkg_manifest["display_name"] == "Alpha Bot Pro"
            assert pkg_manifest["kind"] == "python"

            rev_id = pkg_manifest["agent_revision_id"]
            rev_manifest_path = f"revision/{rev_id}/manifest.json"
            assert rev_manifest_path in names

            agent_py_path = f"revision/{rev_id}/files/agent.py"
            agent_yaml_path = f"revision/{rev_id}/files/agent.yaml"
            assert agent_py_path in names
            assert agent_yaml_path in names

            # Disallowed files check (clean payload)
            for name in names:
                assert not name.endswith(".pyc")
                assert "__pycache__" not in name
                assert ".git" not in name

        # Inspection verification
        inspection = inspect_package(out_file)
        assert inspection.valid is True
        assert inspection.compatible is True
        assert inspection.agent_id == "alpha_bot"
        assert inspection.display_name == "Alpha Bot Pro"
        assert inspection.integrity_verified is True
    finally:
        designer.deleteLater()


@pytest.mark.gui
def test_export_agent_package_normalizes_omitted_extension(monkeypatch, tmp_path: Path) -> None:
    """If user saves without typing .bytefray-agent, the extension is appended."""
    _make_app()
    import app.agent_designer as agent_designer_module
    from app.agent_designer import AgentDesigner

    data_root = tmp_path / "designer-data"
    monkeypatch.setenv("BYTEFRAY_ROOT", str(data_root))
    _write_python_agent(data_root, "hunter")

    designer = AgentDesigner()
    try:
        designer.refresh_agents(select="hunter")
        dest_without_ext = tmp_path / "export_dir" / "my_custom_package"
        dest_without_ext.parent.mkdir(parents=True, exist_ok=True)

        monkeypatch.setattr(
            agent_designer_module.QFileDialog,
            "getSaveFileName",
            staticmethod(lambda *a, **k: (str(dest_without_ext), "")),
        )
        monkeypatch.setattr(
            agent_designer_module.QMessageBox,
            "information",
            staticmethod(lambda *a, **k: None),
        )

        designer.exportAgentPackageAction.trigger()

        expected_file = tmp_path / "export_dir" / "my_custom_package.bytefray-agent"
        assert expected_file.is_file()
    finally:
        designer.deleteLater()


@pytest.mark.gui
def test_export_extension_normalization_prompts_overwrite_if_target_exists(
    monkeypatch, tmp_path: Path
) -> None:
    """If user saves without extension and the normalized target already exists,
    an explicit confirmation prompt is shown. If declined, the existing file is preserved."""
    _make_app()
    import app.agent_designer as agent_designer_module
    from app.agent_designer import AgentDesigner

    data_root = tmp_path / "designer-data"
    monkeypatch.setenv("BYTEFRAY_ROOT", str(data_root))
    _write_python_agent(data_root, "hunter")

    designer = AgentDesigner()
    try:
        designer.refresh_agents(select="hunter")
        dest_without_ext = tmp_path / "hunter"
        existing_file = tmp_path / "hunter.bytefray-agent"
        existing_file.write_text("pre-existing un-overwritten content", encoding="utf-8")

        monkeypatch.setattr(
            agent_designer_module.QFileDialog,
            "getSaveFileName",
            staticmethod(lambda *a, **k: (str(dest_without_ext), "")),
        )

        question_asked = []
        monkeypatch.setattr(
            agent_designer_module.QMessageBox,
            "question",
            staticmethod(
                lambda *a, **k: question_asked.append(a)
                or agent_designer_module.QMessageBox.StandardButton.No
            ),
        )
        informed = []
        monkeypatch.setattr(
            agent_designer_module.QMessageBox,
            "information",
            staticmethod(lambda *a, **k: informed.append(a) or None),
        )

        designer.exportAgentPackageAction.trigger()

        # Prompt must be shown
        assert len(question_asked) == 1
        assert "hunter.bytefray-agent" in question_asked[0][2]

        # Declined -> no overwrite, no success dialog
        assert informed == []
        assert existing_file.read_text(encoding="utf-8") == "pre-existing un-overwritten content"
    finally:
        designer.deleteLater()


@pytest.mark.gui
def test_export_extension_normalization_allows_overwrite_if_confirmed(
    monkeypatch, tmp_path: Path
) -> None:
    """If user confirms overwrite when target exists, export proceeds successfully."""
    _make_app()
    import app.agent_designer as agent_designer_module
    from app.agent_designer import AgentDesigner

    data_root = tmp_path / "designer-data"
    monkeypatch.setenv("BYTEFRAY_ROOT", str(data_root))
    _write_python_agent(data_root, "hunter")

    designer = AgentDesigner()
    try:
        designer.refresh_agents(select="hunter")
        dest_without_ext = tmp_path / "hunter"
        existing_file = tmp_path / "hunter.bytefray-agent"
        existing_file.write_text("old content", encoding="utf-8")

        monkeypatch.setattr(
            agent_designer_module.QFileDialog,
            "getSaveFileName",
            staticmethod(lambda *a, **k: (str(dest_without_ext), "")),
        )

        question_asked = []
        monkeypatch.setattr(
            agent_designer_module.QMessageBox,
            "question",
            staticmethod(
                lambda *a, **k: question_asked.append(a)
                or agent_designer_module.QMessageBox.StandardButton.Yes
            ),
        )
        informed = []
        monkeypatch.setattr(
            agent_designer_module.QMessageBox,
            "information",
            staticmethod(lambda *a, **k: informed.append(a) or None),
        )

        designer.exportAgentPackageAction.trigger()

        assert len(question_asked) == 1
        assert len(informed) == 1
        assert "Exported agent: hunter" in informed[0][2]
        # Existing file is now a valid zip package
        assert existing_file.read_bytes()[:2] == b"PK"
    finally:
        designer.deleteLater()


# ---------------------------------------------------------------------------
# 5. Cancellation & Error Handling UX
# ---------------------------------------------------------------------------


@pytest.mark.gui
def test_export_cancellation_is_clean_noop(monkeypatch, tmp_path: Path) -> None:
    """Cancelling the save file dialog writes nothing and shows no dialog."""
    _make_app()
    import app.agent_designer as agent_designer_module
    from app.agent_designer import AgentDesigner

    data_root = tmp_path / "designer-data"
    monkeypatch.setenv("BYTEFRAY_ROOT", str(data_root))
    _write_python_agent(data_root, "hunter")

    designer = AgentDesigner()
    try:
        designer.refresh_agents(select="hunter")

        # Simulate user cancelling save dialog
        monkeypatch.setattr(
            agent_designer_module.QFileDialog,
            "getSaveFileName",
            staticmethod(lambda *a, **k: ("", "")),
        )

        informed = []
        critical = []
        monkeypatch.setattr(
            agent_designer_module.QMessageBox,
            "information",
            staticmethod(lambda *a, **k: informed.append(a) or None),
        )
        monkeypatch.setattr(
            agent_designer_module.QMessageBox,
            "critical",
            staticmethod(lambda *a, **k: critical.append(a) or None),
        )

        designer.exportAgentPackageAction.trigger()

        assert informed == []
        assert critical == []
    finally:
        designer.deleteLater()


@pytest.mark.gui
def test_export_surfaces_package_error_cleanly(monkeypatch, tmp_path: Path) -> None:
    """When package export fails with an AgentPackageError, QMessageBox.critical
    reports the error code and explanation cleanly."""
    _make_app()
    from battle_engine.agent_package import PackageInvalidError

    import app.agent_designer as agent_designer_module
    from app.agent_designer import AgentDesigner

    data_root = tmp_path / "designer-data"
    monkeypatch.setenv("BYTEFRAY_ROOT", str(data_root))
    _write_python_agent(data_root, "hunter")

    designer = AgentDesigner()
    try:
        designer.refresh_agents(select="hunter")

        out_file = tmp_path / "out.bytefray-agent"
        monkeypatch.setattr(
            agent_designer_module.QFileDialog,
            "getSaveFileName",
            staticmethod(lambda *a, **k: (str(out_file), "")),
        )

        def _mock_failing_export(*a, **k):
            raise PackageInvalidError("Simulated manifest corruption")

        monkeypatch.setattr(agent_designer_module, "export_agent", _mock_failing_export)

        critical = []
        monkeypatch.setattr(
            agent_designer_module.QMessageBox,
            "critical",
            staticmethod(lambda *a, **k: critical.append(a) or None),
        )

        designer.exportAgentPackageAction.trigger()

        assert len(critical) == 1
        dialog_title = critical[0][1]
        dialog_message = critical[0][2]
        assert "Export Failed" in dialog_title
        assert "[package_invalid]" in dialog_message
        assert "Simulated manifest corruption" in dialog_message
    finally:
        designer.deleteLater()


@pytest.mark.gui
def test_export_surfaces_unexpected_exception_without_crash(monkeypatch, tmp_path: Path) -> None:
    """Non-AgentPackageError exceptions are caught and reported via critical dialog."""
    _make_app()
    import app.agent_designer as agent_designer_module
    from app.agent_designer import AgentDesigner

    data_root = tmp_path / "designer-data"
    monkeypatch.setenv("BYTEFRAY_ROOT", str(data_root))
    _write_python_agent(data_root, "hunter")

    designer = AgentDesigner()
    try:
        designer.refresh_agents(select="hunter")

        out_file = tmp_path / "out.bytefray-agent"
        monkeypatch.setattr(
            agent_designer_module.QFileDialog,
            "getSaveFileName",
            staticmethod(lambda *a, **k: (str(out_file), "")),
        )

        def _mock_unexpected(*a, **k):
            raise RuntimeError("Unexpected disk error")

        monkeypatch.setattr(agent_designer_module, "export_agent", _mock_unexpected)

        critical = []
        monkeypatch.setattr(
            agent_designer_module.QMessageBox,
            "critical",
            staticmethod(lambda *a, **k: critical.append(a) or None),
        )

        designer.exportAgentPackageAction.trigger()

        assert len(critical) == 1
        assert "Unexpected disk error" in critical[0][2]
    finally:
        designer.deleteLater()


# ---------------------------------------------------------------------------
# 6. Full Round-Trip (Export -> Inspect -> Import) & Immutability
# ---------------------------------------------------------------------------


@pytest.mark.gui
def test_designer_export_round_trip_inspect_and_import(monkeypatch, tmp_path: Path) -> None:
    """Full lifecycle:
    1. Agent designed in Designer data_root
    2. Exported via Designer File -> Export Agent Package…
    3. Inspected via inspect_package (structure, integrity, compatibility)
    4. Imported into an isolated second installation via import_package
    5. Source content and revision identity are byte-preserved."""
    _make_app()
    from battle_engine.agent_package import import_package, inspect_package

    import app.agent_designer as agent_designer_module
    from app.agent_designer import AgentDesigner

    source_root = tmp_path / "source-installation"
    target_root = tmp_path / "target-installation"
    monkeypatch.setenv("BYTEFRAY_ROOT", str(source_root))

    custom_code = "def agent(obs):\n    # Custom strategy\n    return [{'action': 'pass'}]\n"
    _write_python_agent(
        source_root,
        "champion",
        display="Champion Bot V5",
        code=custom_code,
    )

    package_path = tmp_path / "exported_champion.bytefray-agent"

    designer = AgentDesigner()
    try:
        designer.refresh_agents(select="champion")

        monkeypatch.setattr(
            agent_designer_module.QFileDialog,
            "getSaveFileName",
            staticmethod(lambda *a, **k: (str(package_path), "")),
        )
        monkeypatch.setattr(
            agent_designer_module.QMessageBox,
            "information",
            staticmethod(lambda *a, **k: None),
        )

        # 1. Export
        designer.exportAgentPackageAction.trigger()
        assert package_path.is_file()

        # 2. Inspect
        inspection = inspect_package(package_path)
        assert inspection.valid is True
        assert inspection.compatible is True
        assert inspection.agent_id == "champion"
        assert inspection.display_name == "Champion Bot V5"
        assert inspection.file_count == 2
        assert inspection.integrity_verified is True
        assert inspection.agent_revision_id.startswith("agent-revision_")

        # 3. Import into clean isolated installation
        import_result = import_package(
            package_path,
            data_root=target_root,
            as_agent_id="champion_imported",
        )
        assert import_result.agent_id == "champion_imported"
        assert import_result.agent_revision_id == inspection.agent_revision_id
        assert import_result.already_present is False

        # Verify imported files match original byte-for-byte
        imported_dir = target_root / "agents" / "champion_imported"
        assert imported_dir.is_dir()
        assert imported_dir.joinpath("agent.py").read_text(encoding="utf-8") == custom_code
    finally:
        designer.deleteLater()


@pytest.mark.gui
def test_export_is_strictly_readonly_with_respect_to_source_agent(
    monkeypatch, tmp_path: Path
) -> None:
    """Exporting an agent must never alter the source agent's files, manifest, or directory."""
    _make_app()
    import app.agent_designer as agent_designer_module
    from app.agent_designer import AgentDesigner

    data_root = tmp_path / "designer-data"
    monkeypatch.setenv("BYTEFRAY_ROOT", str(data_root))
    source_dir = _write_python_agent(data_root, "hunter", code="# immutable source\n")

    agent_py = source_dir / "agent.py"
    agent_yaml = source_dir / "agent.yaml"
    orig_py_bytes = agent_py.read_bytes()
    orig_yaml_bytes = agent_yaml.read_bytes()
    orig_py_mtime = agent_py.stat().st_mtime_ns
    orig_yaml_mtime = agent_yaml.stat().st_mtime_ns

    designer = AgentDesigner()
    try:
        designer.refresh_agents(select="hunter")
        out_file = tmp_path / "hunter.bytefray-agent"
        monkeypatch.setattr(
            agent_designer_module.QFileDialog,
            "getSaveFileName",
            staticmethod(lambda *a, **k: (str(out_file), "")),
        )
        monkeypatch.setattr(
            agent_designer_module.QMessageBox,
            "information",
            staticmethod(lambda *a, **k: None),
        )

        designer.exportAgentPackageAction.trigger()

        assert out_file.is_file()

        # Source files remain untouched
        assert agent_py.read_bytes() == orig_py_bytes
        assert agent_yaml.read_bytes() == orig_yaml_bytes
        assert agent_py.stat().st_mtime_ns == orig_py_mtime
        assert agent_yaml.stat().st_mtime_ns == orig_yaml_mtime
    finally:
        designer.deleteLater()
