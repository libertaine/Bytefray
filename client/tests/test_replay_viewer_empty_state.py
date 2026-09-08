"""Phase 3 (UX-20..UX-23): the standalone Replay Viewer's no-argument
startup must show a visible empty state instead of exiting immediately, and
picking a replay from it must feed into the exact same loading/playback
path a direct ``--replay <path>`` invocation uses.

Most coverage here monkeypatches the empty-state's event loop
(``run_empty_state``) rather than driving a real Pygame window, so the
startup-state *decision* (argparse routing, retry-on-bad-pick, reuse of the
one loading path) is tested fast and without a display -- matching the
Phase 3 brief's "isolate/test the startup state decision separately"
guidance. One bounded, real-window smoke test at the bottom (marked
``gui``, mirroring ``test_linux_pygame_smoke.py``) proves the actual event
loop opens and closes cleanly rather than hanging.
"""

from __future__ import annotations

import json

import pytest
from battle_client import cli
from battle_engine.cli import main as engine_main


def _make_valid_replay(tmp_path, name="replay.jsonl"):
    replay = tmp_path / name
    assert (
        engine_main(
            [
                "--ticks", "2", "--arena", "64", "--a-type", "writer",
                "--b-type", "runner", "--replay", str(replay), "--quiet",
            ]
        )
        == 0
    )
    return replay


# ---------------------------------------------------------------------------
# Argument-parsing-level routing (no display involved)
# ---------------------------------------------------------------------------


def test_no_argument_pygame_renderer_enters_empty_state(monkeypatch):
    captured = {}

    def fake_empty_state(args):
        captured["called"] = True
        captured["renderer"] = args.renderer
        return 0

    monkeypatch.setattr(cli, "_run_interactive_empty_state", fake_empty_state)

    assert cli.main(["--renderer", "pygame"]) == 0
    assert captured == {"called": True, "renderer": "pygame"}


def test_no_argument_headless_renderer_still_required():
    """Only the interactive viewer gained a "no replay yet" state --
    headless (a one-shot stream) has nothing to stream without a path, so
    its --replay requirement must stay exactly as strict as before."""
    with pytest.raises(SystemExit) as excinfo:
        cli.main([])  # renderer defaults to headless
    assert excinfo.value.code == 2


def test_no_argument_default_renderer_is_still_headless_and_required(capsys):
    with pytest.raises(SystemExit):
        cli.main([])
    assert "--replay is required" in capsys.readouterr().err


# ---------------------------------------------------------------------------
# Existing direct --replay <path> invocation must not regress
# ---------------------------------------------------------------------------


def test_valid_replay_argument_still_reaches_the_loading_path(tmp_path, monkeypatch):
    replay = _make_valid_replay(tmp_path)
    captured = {}

    def fake_finish(args, replay_path, session):
        captured["replay_path"] = replay_path
        captured["session_loaded"] = session.loaded
        return 0

    monkeypatch.setattr(cli, "_run_interactive_with_session", fake_finish)

    assert cli.main(["--replay", str(replay), "--renderer", "pygame"]) == 0
    assert captured["replay_path"] == replay.resolve()
    assert captured["session_loaded"] is True


def test_invalid_missing_replay_argument_exits_cleanly(tmp_path):
    missing = tmp_path / "does-not-exist.jsonl"
    with pytest.raises(SystemExit) as excinfo:
        cli.main(["--replay", str(missing), "--renderer", "pygame"])
    assert excinfo.value.code == 2


def test_malformed_replay_argument_reports_error_and_returns_1(tmp_path, capsys):
    malformed = tmp_path / "malformed.jsonl"
    malformed.write_text(json.dumps({"tick": 0, "agents": []}) + "\n", encoding="utf-8")

    assert cli.main(["--replay", str(malformed), "--renderer", "pygame"]) == 1
    assert "error" in capsys.readouterr().err.lower()


# ---------------------------------------------------------------------------
# Empty-state "Open Replay..." reuses the one loading path -- no parallel
# replay parser for the picker UI.
# ---------------------------------------------------------------------------


def test_empty_state_valid_pick_reuses_the_same_finish_path(tmp_path, monkeypatch):
    replay = _make_valid_replay(tmp_path)
    picks = iter([replay])

    def fake_run_empty_state(pg, *, title, initial_directory, message=""):
        return next(picks, None)

    finish_captured = {}

    def fake_finish(args, replay_path, session):
        finish_captured["replay_path"] = replay_path
        finish_captured["session_loaded"] = session.loaded
        return 0

    monkeypatch.setattr(
        "battle_client.renderers.replay_picker.run_empty_state", fake_run_empty_state
    )
    monkeypatch.setattr(cli, "_run_interactive_with_session", fake_finish)

    result = cli.main(["--renderer", "pygame"])

    assert result == 0
    assert finish_captured["replay_path"] == replay
    assert finish_captured["session_loaded"] is True


def test_empty_state_malformed_pick_retries_instead_of_crashing(tmp_path, monkeypatch, capsys):
    malformed = tmp_path / "malformed.jsonl"
    malformed.write_text(json.dumps({"tick": 0, "agents": []}) + "\n", encoding="utf-8")
    picks = iter([malformed, None])  # bad pick, then the user closes the window
    seen_messages = []

    def fake_run_empty_state(pg, *, title, initial_directory, message=""):
        seen_messages.append(message)
        return next(picks)

    finish_calls = []
    monkeypatch.setattr(
        "battle_client.renderers.replay_picker.run_empty_state", fake_run_empty_state
    )
    monkeypatch.setattr(
        cli, "_run_interactive_with_session", lambda *a, **k: finish_calls.append(a) or 0
    )

    result = cli.main(["--renderer", "pygame"])

    assert result == 0  # closing the window after a bad pick is not a failure
    assert finish_calls == []  # the malformed pick never reached playback
    assert "error" in capsys.readouterr().err.lower()
    # The reopened window must explain the bad pick itself -- a Start-Menu
    # launch has no terminal to read the stderr message from.
    assert seen_messages[0] == ""
    assert seen_messages[1] != "" and malformed.name in seen_messages[1]


def test_empty_state_cancel_without_picking_returns_cleanly(monkeypatch):
    monkeypatch.setattr(
        "battle_client.renderers.replay_picker.run_empty_state",
        lambda pg, *, title, initial_directory, message="": None,
    )

    assert cli.main(["--renderer", "pygame"]) == 0


# ---------------------------------------------------------------------------
# Bounded real-window smoke test (mirrors test_linux_pygame_smoke.py)
# ---------------------------------------------------------------------------


@pytest.mark.gui
def test_empty_state_real_window_opens_and_closes_on_quit(monkeypatch):
    pygame = pytest.importorskip("pygame")
    from battle_client.renderers import replay_picker

    original_run = replay_picker.run_empty_state

    def run_and_immediately_quit(pg, *, title, initial_directory, message="", window_size=(720, 460)):
        # Post QUIT before entering the loop's own event pump so the very
        # first iteration exits -- same technique as the existing pygame
        # smoke tests' "post QUIT right after window setup".
        if not pg.get_init():
            pg.init()
        pg.display.set_mode(window_size, pg.RESIZABLE)
        pg.event.post(pg.event.Event(pg.QUIT))
        return original_run(
            pg, title=title, initial_directory=initial_directory, message=message, window_size=window_size
        )

    monkeypatch.setattr(replay_picker, "run_empty_state", run_and_immediately_quit)

    assert cli.main(["--renderer", "pygame"]) == 0
    assert not pygame.get_init()
