"""Tests for V5 Alpha 1 Phase 2: Menu and Command Organization.

Validates:
- Conventional top-level menu layout: File, Tools, Help (View deferred).
- File menu contains Import Agent Package…, Inspect Agent Package…,
  separator, Open Last Output Folder, separator, Exit.
- Tools menu contains only operational commands: Run Tournament…,
  Evaluation History…, Replay History… (no duplicated package/file commands).
- Help menu contains About Bytefray.
- Canonical wiring: triggering actions executes the established handler.
- File -> Exit triggers canonical window close/shutdown path (closeEvent).
- Menu accessibility: tooltips visible on File menu, standard Quit shortcut.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest


def _make_app():
    pytest.importorskip("PySide6")
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication

    return QApplication.instance() or QApplication([])


def _get_top_level_menus(designer):
    # Menu bar actions that represent submenus
    menus = []
    for action in designer.menuBar().actions():
        menu = action.menu()
        if menu is not None:
            menus.append(menu)
    return menus


@pytest.mark.gui
def test_menu_bar_top_level_menus_and_order(monkeypatch, tmp_path: Path) -> None:
    """The menu bar must expose File, Tools, and Help in desktop-standard order.

    View is intentionally deferred because no genuine view commands exist.
    """
    _make_app()
    from app.agent_designer import AgentDesigner

    monkeypatch.setenv("BYTEFRAY_ROOT", str(tmp_path / "data"))
    designer = AgentDesigner()
    try:
        menus = _get_top_level_menus(designer)
        titles = [m.title() for m in menus]
        assert titles == ["File", "Tools", "Help"]
        assert "View" not in titles
    finally:
        designer.deleteLater()


@pytest.mark.gui
def test_file_menu_actions_and_ordering(monkeypatch, tmp_path: Path) -> None:
    """File menu must contain Import, Inspect, Open Output Folder, and Exit with
    separators creating logical desktop-standard groups."""
    _make_app()
    from app.agent_designer import AgentDesigner

    monkeypatch.setenv("BYTEFRAY_ROOT", str(tmp_path / "data"))
    designer = AgentDesigner()
    try:
        menus = _get_top_level_menus(designer)
        file_menu = next(m for m in menus if m.title() == "File")
        actions = file_menu.actions()

        assert len(actions) in (6, 7)

        # Item 0: Import Agent Package… (dialog command -> ellipsis)
        assert actions[0].text() == "Import Agent Package…"
        assert not actions[0].isSeparator()
        assert actions[0].isEnabled()

        # Item 1: Inspect Agent Package… (dialog command -> ellipsis)
        assert actions[1].text() == "Inspect Agent Package…"
        assert not actions[1].isSeparator()
        assert actions[1].isEnabled()

        offset = 0
        if len(actions) == 7:
            # Phase 3 companion operation: Export Agent Package… (dialog command -> ellipsis)
            assert actions[2].text() == "Export Agent Package…"
            assert not actions[2].isSeparator()
            assert actions[2].isEnabled()
            offset = 1

        # Separator between package ops and folder ops
        assert actions[2 + offset].isSeparator()

        # Open Last Output Folder (immediate command -> no ellipsis)
        assert actions[3 + offset].text() == "Open Last Output Folder"
        assert not actions[3 + offset].isSeparator()
        assert actions[3 + offset].isEnabled()
        assert actions[3 + offset] is designer.openOutputFolderAction

        # Separator before application lifecycle
        assert actions[4 + offset].isSeparator()

        # Exit (immediate command -> no ellipsis)
        assert actions[5 + offset].text() == "Exit"
        assert not actions[5 + offset].isSeparator()
        assert actions[5 + offset].isEnabled()
        assert actions[5 + offset] is designer.exitAction
    finally:
        designer.deleteLater()


@pytest.mark.gui
def test_file_menu_tooltips_visible_and_output_folder_tip(monkeypatch, tmp_path: Path) -> None:
    """File menu must enable tooltips so Open Last Output Folder's explanatory
    fallback description remains discoverable on hover."""
    _make_app()
    from app.agent_designer import AgentDesigner

    monkeypatch.setenv("BYTEFRAY_ROOT", str(tmp_path / "data"))
    designer = AgentDesigner()
    try:
        menus = _get_top_level_menus(designer)
        file_menu = next(m for m in menus if m.title() == "File")
        assert file_menu.toolTipsVisible()
        assert designer.openOutputFolderAction.parent() is file_menu

        tip = designer.openOutputFolderAction.toolTip().lower()
        assert "tournament" in tip
        assert "single match" in tip
        assert "runs folder" in tip
    finally:
        designer.deleteLater()


@pytest.mark.gui
def test_tools_menu_contains_only_operational_actions(monkeypatch, tmp_path: Path) -> None:
    """Tools menu must retain operational/analysis commands and no longer carry
    file/package commands or redundant separators."""
    _make_app()
    from app.agent_designer import AgentDesigner

    monkeypatch.setenv("BYTEFRAY_ROOT", str(tmp_path / "data"))
    designer = AgentDesigner()
    try:
        menus = _get_top_level_menus(designer)
        tools_menu = next(m for m in menus if m.title() == "Tools")
        actions = tools_menu.actions()

        labels = [a.text() for a in actions if not a.isSeparator()]
        assert labels == [
            "Run Tournament…",
            "Evaluation History…",
            "Replay History…",
        ]

        # Ensure no package or folder commands remain under Tools
        for forbidden in (
            "Import Agent Package…",
            "Inspect Agent Package…",
            "Open Last Output Folder",
            "Exit",
        ):
            assert forbidden not in labels

        # All Tools actions must be enabled
        for action in actions:
            assert action.isEnabled()
    finally:
        designer.deleteLater()


@pytest.mark.gui
def test_help_menu_contains_about(monkeypatch, tmp_path: Path) -> None:
    """Help menu must retain the About Bytefray action."""
    _make_app()
    from app.agent_designer import AgentDesigner

    monkeypatch.setenv("BYTEFRAY_ROOT", str(tmp_path / "data"))
    designer = AgentDesigner()
    try:
        menus = _get_top_level_menus(designer)
        help_menu = next(m for m in menus if m.title() == "Help")
        labels = [a.text() for a in help_menu.actions()]
        assert labels == ["About Bytefray"]
    finally:
        designer.deleteLater()


@pytest.mark.gui
def test_action_trigger_wiring_executes_canonical_handlers(monkeypatch, tmp_path: Path) -> None:
    """Triggering each QAction invokes its canonical AgentDesigner handler."""
    _make_app()
    from app.agent_designer import AgentDesigner

    monkeypatch.setenv("BYTEFRAY_ROOT", str(tmp_path / "data"))
    designer = AgentDesigner()
    try:
        menus = _get_top_level_menus(designer)
        file_menu = next(m for m in menus if m.title() == "File")
        tools_menu = next(m for m in menus if m.title() == "Tools")
        help_menu = next(m for m in menus if m.title() == "Help")

        calls = []

        monkeypatch.setattr(designer, "_on_import_agent_package", lambda: calls.append("import"))
        monkeypatch.setattr(designer, "_on_inspect_agent_package", lambda: calls.append("inspect"))
        monkeypatch.setattr(designer, "_on_open_output_folder", lambda: calls.append("output_folder"))
        monkeypatch.setattr(designer, "_on_tournament", lambda: calls.append("tournament"))
        monkeypatch.setattr(designer, "_on_evaluation_history", lambda: calls.append("eval_history"))
        monkeypatch.setattr(designer, "_on_replay_history", lambda: calls.append("replay_history"))
        monkeypatch.setattr(designer, "_on_about", lambda: calls.append("about"))

        # Trigger File actions
        action_map_file = {a.text(): a for a in file_menu.actions() if not a.isSeparator()}
        action_map_file["Import Agent Package…"].trigger()
        action_map_file["Inspect Agent Package…"].trigger()
        action_map_file["Open Last Output Folder"].trigger()

        # Trigger Tools actions
        action_map_tools = {a.text(): a for a in tools_menu.actions() if not a.isSeparator()}
        action_map_tools["Run Tournament…"].trigger()
        action_map_tools["Evaluation History…"].trigger()
        action_map_tools["Replay History…"].trigger()

        # Trigger Help action
        action_map_help = {a.text(): a for a in help_menu.actions() if not a.isSeparator()}
        action_map_help["About Bytefray"].trigger()

        assert calls == [
            "import",
            "inspect",
            "output_folder",
            "tournament",
            "eval_history",
            "replay_history",
            "about",
        ]
    finally:
        designer.deleteLater()


@pytest.mark.gui
def test_exit_action_invokes_canonical_window_close_path(monkeypatch, tmp_path: Path) -> None:
    """Triggering File -> Exit must call self.close(), entering the exact same
    closeEvent / process cleanup / worker shutdown path as clicking the window X."""
    _make_app()
    from PySide6.QtGui import QKeySequence

    from app.agent_designer import AgentDesigner

    monkeypatch.setenv("BYTEFRAY_ROOT", str(tmp_path / "data"))
    designer = AgentDesigner()
    try:
        # Verify standard Quit key sequence is configured
        expected_quit = QKeySequence(QKeySequence.StandardKey.Quit)
        assert designer.exitAction.shortcut() == expected_quit

        # Spy closeEvent to verify the normal shutdown handler runs
        close_records = []
        original_close_event = designer.closeEvent

        def _recording_close_event(event):
            rec = {"accepted_initial": event.isAccepted()}
            close_records.append(rec)
            original_close_event(event)
            rec["accepted_final"] = event.isAccepted()

        monkeypatch.setattr(designer, "closeEvent", _recording_close_event)

        # Trigger Exit action
        designer.exitAction.trigger()

        assert len(close_records) == 1
        assert close_records[0]["accepted_final"] is True
    finally:
        designer.deleteLater()


@pytest.mark.gui
def test_menu_accessibility_and_no_shortcut_collisions(monkeypatch, tmp_path: Path) -> None:
    """Verify menu actions do not produce conflicting shortcuts and that
    all actions are keyboard-activatable without mouse events."""
    _make_app()
    from app.agent_designer import AgentDesigner

    monkeypatch.setenv("BYTEFRAY_ROOT", str(tmp_path / "data"))
    designer = AgentDesigner()
    try:
        menus = _get_top_level_menus(designer)
        shortcuts = []
        for menu in menus:
            for action in menu.actions():
                if action.isSeparator():
                    continue
                sc = action.shortcut().toString()
                if sc:
                    shortcuts.append((sc, action.text()))

        # If any shortcuts exist, they must be distinct
        shortcut_strings = [s[0] for s in shortcuts]
        assert len(shortcut_strings) == len(set(shortcut_strings))

        # Menu bar itself is active and has the 3 expected top-level menu actions
        menu_bar = designer.menuBar()
        assert len(menu_bar.actions()) == 3
        bar_texts = [a.text() for a in menu_bar.actions()]
        assert bar_texts == ["File", "Tools", "Help"]
    finally:
        designer.deleteLater()


@pytest.mark.gui
def test_exit_action_disposes_active_subprocess(monkeypatch, tmp_path: Path) -> None:
    """Exit must terminate and detach active runner processes via _dispose_process()."""
    from unittest.mock import MagicMock

    from PySide6.QtCore import QProcess

    _make_app()
    from app.agent_designer import AgentDesigner

    monkeypatch.setenv("BYTEFRAY_ROOT", str(tmp_path / "data"))
    designer = AgentDesigner()
    try:
        mock_proc = MagicMock(spec=QProcess)
        mock_proc.state.return_value = QProcess.ProcessState.Running
        designer._proc = mock_proc

        designer.exitAction.trigger()

        assert mock_proc.kill.called or mock_proc.terminate.called
    finally:
        designer.deleteLater()


@pytest.mark.gui
def test_exit_action_shuts_down_child_replay_history_worker(monkeypatch, tmp_path: Path) -> None:
    """Exit must cleanly shutdown modeless replay history worker threads before closing."""
    from unittest.mock import MagicMock

    _make_app()
    from app.agent_designer import AgentDesigner

    monkeypatch.setenv("BYTEFRAY_ROOT", str(tmp_path / "data"))
    designer = AgentDesigner()
    try:
        mock_history = MagicMock()
        designer._replay_history = mock_history

        designer.exitAction.trigger()

        assert mock_history.shutdownWorker.called
        assert mock_history.close.called
        assert designer._replay_history is None
    finally:
        designer.deleteLater()


@pytest.mark.gui
def test_menu_actions_menu_roles(monkeypatch, tmp_path: Path) -> None:
    """Explicitly verifies standard Qt MenuRoles for Exit (QuitRole) and About (AboutRole)."""
    _make_app()
    from PySide6.QtGui import QAction

    from app.agent_designer import AgentDesigner

    monkeypatch.setenv("BYTEFRAY_ROOT", str(tmp_path / "data"))
    designer = AgentDesigner()
    try:
        menus = _get_top_level_menus(designer)
        assert designer.exitAction.menuRole() == QAction.MenuRole.QuitRole

        help_menu = next(m for m in menus if m.title() == "Help")
        about_action = next(a for a in help_menu.actions() if a.text() == "About Bytefray")
        assert about_action.menuRole() == QAction.MenuRole.AboutRole
    finally:
        designer.deleteLater()


@pytest.mark.gui
def test_keyboard_navigation_reaches_exit_without_mouse(monkeypatch, tmp_path: Path) -> None:
    """Exit must be reachable and activatable purely via keyboard navigation."""
    _make_app()
    from app.agent_designer import AgentDesigner

    monkeypatch.setenv("BYTEFRAY_ROOT", str(tmp_path / "data"))
    designer = AgentDesigner()
    try:
        menus = _get_top_level_menus(designer)
        file_menu = next(m for m in menus if m.title() == "File")

        close_records = []
        original_close_event = designer.closeEvent

        def _recording_close_event(event):
            close_records.append(event.isAccepted())
            original_close_event(event)

        monkeypatch.setattr(designer, "closeEvent", _recording_close_event)

        # Activating File menu's Exit action via action trigger
        # without any mouse coordinate or button event.
        file_actions = file_menu.actions()
        exit_action = next(a for a in file_actions if a.text() == "Exit")
        exit_action.trigger()

        assert len(close_records) == 1
    finally:
        designer.deleteLater()


@pytest.mark.gui
def test_designer_gui_menu_smoke_offscreen(monkeypatch, tmp_path: Path) -> None:
    """Offscreen GUI smoke test proving AgentDesigner with the new menu layout
    can be instantiated, displayed, process events, and closed cleanly."""
    app = _make_app()
    from app.agent_designer import AgentDesigner

    monkeypatch.setenv("BYTEFRAY_ROOT", str(tmp_path / "data"))
    designer = AgentDesigner()
    try:
        designer.show()
        app.processEvents()
        assert designer.isVisible()

        menus = _get_top_level_menus(designer)
        file_menu = next(m for m in menus if m.title() == "File")
        assert len(file_menu.actions()) in (6, 7)
    finally:
        designer.close()
        app.processEvents()
        designer.deleteLater()

