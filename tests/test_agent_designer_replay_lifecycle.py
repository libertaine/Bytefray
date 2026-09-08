"""Phase 3 (UX-25): "View Last Match" must reliably mean the replay from
the user's most recently completed *successful* match -- never a stale
prior replay, never a failed run's nonexistent one, and never a silently
substituted unrelated file.

Exercises AgentDesigner's process-lifecycle slots directly as plain Python
method calls, matching test_agent_designer_lifecycle.py's existing
direct-slot-call idiom (no QTimer/event-loop timing involved). Marked
``gui`` like the other Designer tests: excluded from the default headless
run, exercised by the dedicated display-backed workflow.
"""

from __future__ import annotations

import json
import os

import pytest

RESULT_SCHEMA = {"schema": "battle2.result", "schema_version": 1}


def _write_match_artifacts(run_dir, *, winner="A", replay_name="replay.jsonl"):
    """A minimal but schema-valid result.json + its sibling replay.jsonl,
    exactly as new_match_run_directory/match_artifact_paths lay one real
    match run's artifacts out (docs/specs/agent_designer_workflow.md
    Sec 2.2)."""
    run_dir.mkdir(parents=True)
    replay_path = run_dir / replay_name
    replay_path.write_text('{"tick": 0, "ver": 6, "config": {"arena_size": 32}}\n')
    result_path = run_dir / "result.json"
    result_path.write_text(
        json.dumps(
            {
                **RESULT_SCHEMA,
                "result_id": f"r-{run_dir.name}",
                "match_id": f"m-{run_dir.name}",
                "mode": "b2",
                "winner": winner,
                "termination_reason": "elimination",
                "ticks": 10,
                "replay": {
                    "replay_id": f"rep-{run_dir.name}",
                    "sha256": "0" * 64,
                    "filename": replay_name,
                },
            }
        )
    )
    return result_path, replay_path


def _finish_match(designer, QProcess, *, result_path, code=0):
    proc = QProcess(designer)
    designer._proc = proc
    designer._result_path = result_path
    designer._active_workflow = "match"
    designer._on_proc_finished(proc, code, QProcess.ExitStatus.NormalExit)


def _build_designer(monkeypatch, tmp_path):
    pytest.importorskip("PySide6")
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtCore import QProcess
    from PySide6.QtWidgets import QApplication

    from app.agent_designer import AgentDesigner

    monkeypatch.setenv("BYTEFRAY_ROOT", str(tmp_path / "data"))
    QApplication.instance() or QApplication([])
    return AgentDesigner(), QProcess


@pytest.mark.gui
def test_view_last_match_targets_the_second_match_after_two_successful_runs(monkeypatch, tmp_path):
    designer, QProcess = _build_designer(monkeypatch, tmp_path)
    try:
        result_a, replay_a = _write_match_artifacts(tmp_path / "run-a")
        _finish_match(designer, QProcess, result_path=result_a)
        assert designer._last_replay == replay_a

        result_b, replay_b = _write_match_artifacts(tmp_path / "run-b")
        _finish_match(designer, QProcess, result_path=result_b)
        assert designer._last_replay == replay_b

        launched = []
        monkeypatch.setattr(
            "app.agent_designer.open_pygame_client_direct",
            lambda root, path: launched.append(path),
        )
        designer._on_open_replay()

        assert launched == [replay_b]
    finally:
        designer.deleteLater()


@pytest.mark.gui
def test_view_last_match_targets_match_a_immediately_after_it_completes(monkeypatch, tmp_path):
    designer, QProcess = _build_designer(monkeypatch, tmp_path)
    try:
        result_a, replay_a = _write_match_artifacts(tmp_path / "run-a")
        _finish_match(designer, QProcess, result_path=result_a)

        launched = []
        monkeypatch.setattr(
            "app.agent_designer.open_pygame_client_direct",
            lambda root, path: launched.append(path),
        )
        designer._on_open_replay()

        assert launched == [replay_a]
    finally:
        designer.deleteLater()


@pytest.mark.gui
def test_button_enables_only_after_a_successful_match_with_a_real_replay(monkeypatch, tmp_path):
    designer, QProcess = _build_designer(monkeypatch, tmp_path)
    try:
        assert designer.simple.btnOpen.isEnabled() is False
        assert designer.advanced.btnOpen.isEnabled() is False

        result_a, _replay_a = _write_match_artifacts(tmp_path / "run-a")
        _finish_match(designer, QProcess, result_path=result_a)

        assert designer.simple.btnOpen.isEnabled() is True
        assert designer.advanced.btnOpen.isEnabled() is True
    finally:
        designer.deleteLater()


@pytest.mark.gui
def test_failed_match_after_a_success_keeps_the_prior_successful_replay(monkeypatch, tmp_path):
    """Recommended Phase 3 contract: View Last Match tracks the most recent
    *successful* match. A failed Match B must not clear or replace Match
    A's replay -- and must not itself be treated as having a replay."""
    designer, QProcess = _build_designer(monkeypatch, tmp_path)
    try:
        result_a, replay_a = _write_match_artifacts(tmp_path / "run-a")
        _finish_match(designer, QProcess, result_path=result_a)
        assert designer._last_replay == replay_a

        # Match B fails: exit code 1, its own result.json was never written
        # (matching a real crashed/aborted engine invocation).
        never_written = tmp_path / "run-b" / "result.json"
        _finish_match(designer, QProcess, result_path=never_written, code=1)

        assert designer._last_replay == replay_a  # unchanged, not cleared

        launched = []
        monkeypatch.setattr(
            "app.agent_designer.open_pygame_client_direct",
            lambda root, path: launched.append(path),
        )
        designer._on_open_replay()
        assert launched == [replay_a]  # still opens the last *successful* match
    finally:
        designer.deleteLater()


@pytest.mark.gui
def test_deleted_last_replay_shows_a_warning_instead_of_silently_substituting(monkeypatch, tmp_path):
    designer, QProcess = _build_designer(monkeypatch, tmp_path)
    try:
        result_a, replay_a = _write_match_artifacts(tmp_path / "run-a")
        _finish_match(designer, QProcess, result_path=result_a)
        assert designer._last_replay == replay_a

        replay_a.unlink()  # simulate deletion after the match completed

        warnings = []
        monkeypatch.setattr(
            "app.agent_designer.QMessageBox.warning",
            staticmethod(lambda *a, **k: warnings.append(a)),
        )
        launched = []
        monkeypatch.setattr(
            "app.agent_designer.open_pygame_client_direct",
            lambda root, path: launched.append(path),
        )
        monkeypatch.setattr(
            "app.agent_designer.QFileDialog.getOpenFileName",
            staticmethod(lambda *a, **k: ("", "")),  # user cancels the fallback chooser
        )

        designer._on_open_replay()

        assert warnings, "expected a warning that the last replay is gone"
        assert launched == []  # never silently substitutes a different replay
    finally:
        designer.deleteLater()


@pytest.mark.gui
def test_view_last_match_button_tooltip_documents_successful_match_semantics(monkeypatch, tmp_path):
    designer, _QProcess = _build_designer(monkeypatch, tmp_path)
    try:
        for panel in (designer.simple, designer.advanced):
            tooltip = panel.btnOpen.toolTip().lower()
            assert "successful" in tooltip
    finally:
        designer.deleteLater()
