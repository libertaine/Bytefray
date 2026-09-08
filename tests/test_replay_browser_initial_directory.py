"""Phase 3 (UX-24, UX-26): Replay Browser's Choose Replay... must start
browsing somewhere useful instead of a stale/random previous directory, and
View Replay must fail gracefully rather than crashing on a missing/unset
selection.

Marked ``gui`` like the other Designer tests: excluded from the default
headless run, exercised by the dedicated display-backed workflow. Uses
temporary directories throughout -- never a developer machine's real
ProgramData contents -- per the Phase 3 test-fixture requirement.
"""

from __future__ import annotations

import os

import pytest


def _make_app():
    pytest.importorskip("PySide6")
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication

    return QApplication.instance() or QApplication([])


# ---------------------------------------------------------------------------
# _initial_replay_directory priority order
# ---------------------------------------------------------------------------


@pytest.mark.gui
def test_prefers_the_currently_selected_replays_directory_when_it_exists(tmp_path):
    _make_app()
    from app.views.advanced import AdvancedPanel

    selected_dir = tmp_path / "somewhere_else"
    selected_dir.mkdir()
    selected_replay = selected_dir / "replay.jsonl"
    selected_replay.write_text("{}")
    # A canonical directory also exists, but the explicit current selection
    # must win (priority #1).
    (tmp_path / "runs" / "_designer").mkdir(parents=True)

    panel = AdvancedPanel(catalog=None, data_root=tmp_path)
    try:
        panel.lblReplay.setText(str(selected_replay))
        assert panel._initial_replay_directory() == selected_dir
    finally:
        panel.deleteLater()


@pytest.mark.gui
def test_falls_back_to_current_session_replay_directory(tmp_path):
    _make_app()
    from app.views.advanced import AdvancedPanel

    session_dir = tmp_path / "runs" / "_designer" / "20260101-000000-abcd1234"
    session_dir.mkdir(parents=True)
    session_replay = session_dir / "replay.jsonl"
    session_replay.write_text("{}")

    panel = AdvancedPanel(catalog=None, data_root=tmp_path)
    try:
        # No current selection (still the placeholder), but a session
        # replay is known.
        panel.note_completed_replay(session_replay)
        assert panel._initial_replay_directory() == session_dir
    finally:
        panel.deleteLater()


@pytest.mark.gui
def test_falls_back_to_canonical_designer_run_directory(tmp_path):
    _make_app()
    from app.views.advanced import AdvancedPanel

    designer_dir = tmp_path / "runs" / "_designer"
    designer_dir.mkdir(parents=True)

    panel = AdvancedPanel(catalog=None, data_root=tmp_path)
    try:
        # No current selection, no session replay -- but a prior session
        # (or an earlier Designer install) already populated runs/_designer.
        assert panel._initial_replay_directory() == designer_dir
    finally:
        panel.deleteLater()


@pytest.mark.gui
def test_falls_back_to_data_root_when_nothing_else_exists(tmp_path):
    _make_app()
    from app.views.advanced import AdvancedPanel

    panel = AdvancedPanel(catalog=None, data_root=tmp_path)
    try:
        assert panel._initial_replay_directory() == tmp_path.resolve()
    finally:
        panel.deleteLater()


@pytest.mark.gui
def test_stale_selection_that_no_longer_exists_is_ignored(tmp_path):
    """A previously chosen replay that was since deleted must not pin the
    chooser to a directory that might not even exist anymore -- policy
    falls through to the next priority instead."""
    _make_app()
    from app.views.advanced import AdvancedPanel

    designer_dir = tmp_path / "runs" / "_designer"
    designer_dir.mkdir(parents=True)

    panel = AdvancedPanel(catalog=None, data_root=tmp_path)
    try:
        panel.lblReplay.setText(str(tmp_path / "deleted" / "replay.jsonl"))
        assert panel._initial_replay_directory() == designer_dir
    finally:
        panel.deleteLater()


@pytest.mark.gui
def test_choose_replay_dialog_opens_at_the_computed_initial_directory(tmp_path, monkeypatch):
    _make_app()
    from app.views import advanced as advanced_module
    from app.views.advanced import AdvancedPanel

    designer_dir = tmp_path / "runs" / "_designer"
    designer_dir.mkdir(parents=True)

    panel = AdvancedPanel(catalog=None, data_root=tmp_path)
    try:
        captured = {}

        def fake_dialog(parent, caption, directory, filter_):
            captured["directory"] = directory
            captured["filter"] = filter_
            return "", ""

        monkeypatch.setattr(
            advanced_module.QFileDialog, "getOpenFileName", staticmethod(fake_dialog)
        )
        panel.btnChooseReplay.click()

        assert captured["directory"] == str(designer_dir)
        assert "Bytefray Replays" in captured["filter"]
        assert "*.jsonl" in captured["filter"]
    finally:
        panel.deleteLater()


# ---------------------------------------------------------------------------
# View Replay error handling (no parallel replay parser, graceful failure)
# ---------------------------------------------------------------------------


@pytest.mark.gui
def test_view_replay_with_nothing_selected_shows_a_message_and_does_not_launch(tmp_path, monkeypatch):
    _make_app()
    from app.views.advanced import AdvancedPanel

    panel = AdvancedPanel(catalog=None, data_root=tmp_path)
    try:
        launched = []
        monkeypatch.setattr(
            "app.services.engine.open_pygame_client_direct",
            lambda root, path: launched.append((root, path)),
        )
        shown = []
        monkeypatch.setattr(
            "app.views.advanced.QMessageBox.information",
            staticmethod(lambda *a, **k: shown.append(a)),
        )

        panel.btnOpenReplay.click()

        assert launched == []
        assert shown  # a message was shown instead of attempting a launch
    finally:
        panel.deleteLater()


@pytest.mark.gui
def test_view_replay_with_a_missing_file_shows_a_message_and_does_not_launch(tmp_path, monkeypatch):
    _make_app()
    from app.views.advanced import AdvancedPanel

    panel = AdvancedPanel(catalog=None, data_root=tmp_path)
    try:
        panel.lblReplay.setText(str(tmp_path / "deleted" / "replay.jsonl"))
        launched = []
        monkeypatch.setattr(
            "app.services.engine.open_pygame_client_direct",
            lambda root, path: launched.append((root, path)),
        )
        shown = []
        monkeypatch.setattr(
            "app.views.advanced.QMessageBox.critical",
            staticmethod(lambda *a, **k: shown.append(a)),
        )

        panel.btnOpenReplay.click()

        assert launched == []
        assert shown
    finally:
        panel.deleteLater()


@pytest.mark.gui
def test_note_completed_replay_accepts_none_and_clears_session_state(tmp_path):
    _make_app()
    from app.views.advanced import AdvancedPanel

    panel = AdvancedPanel(catalog=None, data_root=tmp_path)
    try:
        replay = tmp_path / "runs" / "_designer" / "r1" / "replay.jsonl"
        replay.parent.mkdir(parents=True)
        replay.write_text("{}")

        panel.note_completed_replay(replay)
        assert panel._session_replay_path == replay

        panel.note_completed_replay(None)
        assert panel._session_replay_path is None
    finally:
        panel.deleteLater()
