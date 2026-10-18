"""View Last Match prefers Bytefray Spectator for supported V6 alpha1 matches.

Drives AgentDesigner's real slots with a real product match (scripted Agent
API v2 entrants played by NativeMatchService, writing the same artifacts a
Designer run writes) and the real ``bytefray spectator prepare`` child
process. Only the final Spectator process start and the Pygame launcher are
replaced by recorders. Marked ``gui`` like the other Designer tests.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import pytest

V6 = "bytefray-rules-6-alpha1"


def _scripted(folder: Path, name: str, script) -> object:
    from battle_engine.agents import agent_spec_from_dir

    folder.mkdir(parents=True)
    (folder / "agent.yaml").write_text(
        f"name: {name}\nkind: python\napi_version: 2\nentrypoint: agent.py:create_agent\n"
        "capabilities: {version: 1, required: [sense]}\n",
        encoding="utf-8",
    )
    (folder / "agent.py").write_text(
        "from battle_engine.agent_api import AgentV2, ProcessDeclaration, AgentAction, ActionKindV2\n"
        f"SCRIPT = {list(script)!r}\n"
        "class Scripted(AgentV2):\n"
        "    def __init__(self): self.calls = 0\n"
        "    def declare_processes(self): return [ProcessDeclaration(id='main', reach=128, share=1.0)]\n"
        "    def act(self, obs):\n"
        "        item = SCRIPT[self.calls % len(SCRIPT)]\n"
        "        self.calls += 1\n"
        "        return AgentAction(ActionKindV2(item[0]), operand=item[1], value=item[2] if len(item)>2 else None)\n"
        "def create_agent(): return Scripted()\n",
        encoding="utf-8",
    )
    spec = agent_spec_from_dir(folder)
    assert spec is not None
    return spec


def _v6_match(data_root: Path, label: str) -> Path:
    """One completed V6 match laid out exactly like a Designer run directory."""
    from battle_engine.config import Config
    from battle_engine.match_service import MatchEntrant, MatchRequest, NativeMatchService

    run = data_root / "runs" / "_designer" / label
    run.mkdir(parents=True)
    a = _scripted(data_root / "scripted" / label / "a", "scripted_a", [("sense", 91), ("move", 16), ("read", 0)])
    b = _scripted(data_root / "scripted" / label / "b", "scripted_b", [("read", 91)])
    NativeMatchService().run(
        MatchRequest(
            config=Config(arena_size=512, instr_per_tick=8, seed=3),
            ruleset_id=V6,
            entrants=(MatchEntrant.python("A", "scripted_a", 0, a), MatchEntrant.python("B", "scripted_b", 91, b)),
            max_ticks=5,
            replay_path=run / "replay.jsonl",
            trace_path=run / "trace.jsonl",
            verbose=False,
        )
    )
    return run / "result.json"


class _FakeProcess:
    pid = 4242

    def poll(self):
        return None


@pytest.fixture
def designer(monkeypatch, tmp_path):
    pytest.importorskip("PySide6")
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtCore import QProcess
    from PySide6.QtWidgets import QApplication

    from app.agent_designer import AgentDesigner

    data_root = tmp_path / "data"
    monkeypatch.setenv("BYTEFRAY_ROOT", str(data_root))
    monkeypatch.delenv("BYTEFRAY_SPECTATOR", raising=False)
    # "Not configured" must not find a Spectator that is on this machine's PATH.
    monkeypatch.setattr("app.services.spectator_viewer.shutil.which", lambda _name: None)
    QApplication.instance() or QApplication([])
    window = AgentDesigner()
    recorded = {"spectator": [], "pygame": [], "warnings": []}
    monkeypatch.setattr(
        "app.widgets.spectator_launch.launch_spectator",
        lambda install, presentation: recorded["spectator"].append((install, Path(presentation))) or _FakeProcess(),
    )
    monkeypatch.setattr(
        "app.agent_designer.open_pygame_client_direct",
        lambda root, path: recorded["pygame"].append(Path(path)),
    )
    for module in ("app.widgets.spectator_launch", "app.agent_designer"):
        monkeypatch.setattr(
            f"{module}.QMessageBox.warning",
            lambda parent, title, body: recorded["warnings"].append((title, body)),
        )
    window.recorded = recorded
    window.data_root_for_test = data_root
    window.QProcess = QProcess
    try:
        yield window
    finally:
        window._spectator.shutdown()
        window.deleteLater()


def _configure_spectator(monkeypatch, tmp_path) -> Path:
    exe = tmp_path / "Bytefray Spectator" / ("bytefray-spectator.exe" if sys.platform == "win32" else "bytefray-spectator")
    exe.parent.mkdir(parents=True)
    exe.write_bytes(b"")
    exe.chmod(0o755)
    monkeypatch.setenv("BYTEFRAY_SPECTATOR", str(exe))
    return exe


def _finish(window, result_path: Path) -> None:
    proc = window.QProcess(window)
    window._proc = proc
    window._result_path = result_path
    window._active_workflow = "match"
    window._on_proc_finished(proc, 0, window.QProcess.ExitStatus.NormalExit)


def _wait_idle(window, timeout: float = 180.0) -> None:
    from PySide6.QtWidgets import QApplication

    deadline = time.monotonic() + timeout
    while window._spectator.busy():
        assert time.monotonic() < deadline, "Spectator prepare did not finish"
        QApplication.processEvents()
        time.sleep(0.02)
    QApplication.processEvents()


@pytest.mark.gui
def test_view_last_match_opens_the_verified_presentation_in_spectator(designer, monkeypatch, tmp_path):
    from battle_client.spectator_export import verify_presentation

    exe = _configure_spectator(monkeypatch, tmp_path)
    result = _v6_match(designer.data_root_for_test, "20261017-000000-aaaaaaaa")
    _finish(designer, result)
    assert designer._spectator.busy()  # the finished match is prepared in the background
    designer._on_open_replay()
    _wait_idle(designer)

    assert designer.recorded["pygame"] == []
    assert designer.recorded["warnings"] == []
    [(install, presentation)] = designer.recorded["spectator"]
    assert install.program == exe.resolve()
    cache = designer.data_root_for_test.resolve() / "cache" / "spectator" / "presentations"
    assert presentation.parent == cache
    manifest = verify_presentation(presentation, require_current_exporter=True)
    assert manifest["match"]["match_id"] == json.loads(result.read_text(encoding="utf-8"))["match_id"]
    assert install.command(presentation)[-2:] == [f"--fixture={presentation}", "--perspective=broadcast"]

    # A second click reuses the verified presentation instead of exporting again.
    designer._on_open_replay()
    _wait_idle(designer)
    assert [p for _, p in designer.recorded["spectator"]] == [presentation, presentation]


@pytest.mark.gui
def test_unsupported_or_unconfigured_matches_keep_the_classic_viewer(designer, monkeypatch, tmp_path):
    result = _v6_match(designer.data_root_for_test, "20261017-000000-bbbbbbbb")
    _finish(designer, result)
    designer._on_open_replay()  # Spectator not configured
    assert designer.recorded["pygame"] == [result.with_name("replay.jsonl").resolve()]
    assert not designer._spectator.busy()

    _configure_spectator(monkeypatch, tmp_path)
    (result.with_name("trace.jsonl")).unlink()  # no sensing trace: Spectator does not apply
    designer._on_open_replay()
    assert designer.recorded["pygame"][-1] == result.with_name("replay.jsonl").resolve()
    assert designer.recorded["spectator"] == [] and designer.recorded["warnings"] == []
    assert not designer._spectator.busy()


@pytest.mark.gui
def test_failed_export_warns_then_falls_back_after_a_fresh_preflight(designer, monkeypatch, tmp_path):
    result = _v6_match(designer.data_root_for_test, "20261017-000000-cccccccc")
    _finish(designer, result)  # finished before Spectator was configured: no prewarm
    trace = result.with_name("trace.jsonl")
    lines = trace.read_text(encoding="utf-8").splitlines()
    for index, line in enumerate(lines):
        record = json.loads(line)
        if record.get("record_type") == "decision_v2" and record["action"]["kind"] == "move":
            record["action"]["operand"] += 1
            lines[index] = json.dumps(record)
            break
    trace.write_text("\n".join(lines) + "\n", encoding="utf-8")

    _configure_spectator(monkeypatch, tmp_path)
    designer._on_open_replay()
    assert designer.recorded["pygame"] == []  # nothing shown before the export answers
    _wait_idle(designer)
    assert designer.recorded["spectator"] == []
    [(title, body)] = designer.recorded["warnings"]
    assert title == "Spectator Unavailable" and "did not verify" in body and "classic replay viewer" in body
    assert designer.recorded["pygame"] == [result.with_name("replay.jsonl").resolve()]


@pytest.mark.gui
def test_a_changed_replay_is_refused_before_either_viewer(designer, monkeypatch, tmp_path):
    _configure_spectator(monkeypatch, tmp_path)
    result = _v6_match(designer.data_root_for_test, "20261017-000000-dddddddd")
    _finish(designer, result)
    _wait_idle(designer)  # the background prepare succeeded
    with result.with_name("replay.jsonl").open("a", encoding="utf-8") as handle:
        handle.write("\n")
    designer._on_open_replay()
    assert designer.recorded["spectator"] == [] and designer.recorded["pygame"] == []
    assert designer.recorded["warnings"][-1][0] == "Replay Changed"
    assert not designer._spectator.busy()


@pytest.mark.gui
def test_view_last_match_never_blocks_the_gui_thread(designer, monkeypatch, tmp_path):
    from PySide6.QtCore import QTimer

    result = _v6_match(designer.data_root_for_test, "20261017-000000-ffffffff")
    _finish(designer, result)  # not configured yet: no background preparation
    _configure_spectator(monkeypatch, tmp_path)
    started = time.monotonic()
    designer._on_open_replay()
    assert time.monotonic() - started < 1.0  # the export runs in a child process
    assert designer._spectator.busy() and designer.recorded["spectator"] == []
    ticks = []
    timer = QTimer()
    timer.timeout.connect(lambda: ticks.append(designer._spectator.busy()))
    timer.start(10)
    _wait_idle(designer)
    timer.stop()
    assert True in ticks  # the event loop kept running while the export worked
    assert len(designer.recorded["spectator"]) == 1


@pytest.mark.gui
def test_a_spectator_that_cannot_start_falls_back(designer, monkeypatch, tmp_path):
    def cannot_start(install, presentation):
        raise OSError(f"Failed to start Spectator '{install.program}': access denied")

    monkeypatch.setattr("app.widgets.spectator_launch.launch_spectator", cannot_start)
    _configure_spectator(monkeypatch, tmp_path)
    result = _v6_match(designer.data_root_for_test, "20261017-000000-abababab")
    _finish(designer, result)
    designer._on_open_replay()
    _wait_idle(designer)
    [(title, body)] = designer.recorded["warnings"]
    assert title == "Spectator Unavailable" and "access denied" in body
    assert designer.recorded["pygame"] == [result.with_name("replay.jsonl").resolve()]


@pytest.mark.gui
def test_a_spectator_that_exits_immediately_is_reported(designer, monkeypatch, tmp_path):
    from PySide6.QtWidgets import QApplication

    class _Crashed(_FakeProcess):
        def poll(self):
            return 3

    monkeypatch.setattr(
        "app.widgets.spectator_launch.launch_spectator",
        lambda install, presentation: designer.recorded["spectator"].append((install, presentation)) or _Crashed(),
    )
    monkeypatch.setattr("app.widgets.spectator_launch.EARLY_EXIT_MS", 50)
    _configure_spectator(monkeypatch, tmp_path)
    result = _v6_match(designer.data_root_for_test, "20261017-000000-cdcdcdcd")
    _finish(designer, result)
    designer._on_open_replay()
    _wait_idle(designer)
    deadline = time.monotonic() + 5
    while not designer.recorded["warnings"] and time.monotonic() < deadline:
        QApplication.processEvents()
        time.sleep(0.02)
    [(title, body)] = designer.recorded["warnings"]
    assert title == "Spectator Unavailable" and "exit code 3" in body
    assert len(designer.recorded["spectator"]) == 1


@pytest.mark.gui
def test_the_export_must_confirm_the_preflighted_match(designer, monkeypatch, tmp_path):
    import app.widgets.spectator_launch as launch

    commands = []
    real_build = launch.build_prepare_command
    monkeypatch.setattr(
        launch,
        "build_prepare_command",
        lambda *args, **kwargs: commands.append(kwargs) or real_build(*args, **kwargs),
    )
    real_parse = launch.parse_prepare_output
    monkeypatch.setattr(  # the child reports a different match than the one preflighted
        launch,
        "parse_prepare_output",
        lambda stdout, code: launch.replace(real_parse(stdout, code), match_id="match_not_the_selected_one"),
    )
    _configure_spectator(monkeypatch, tmp_path)
    result = _v6_match(designer.data_root_for_test, "20261017-000000-efefefef")
    recorded = json.loads(result.read_text(encoding="utf-8"))
    _finish(designer, result)
    designer._on_open_replay()
    _wait_idle(designer)
    assert commands and all(
        (c["expected_match_id"], c["expected_result_id"]) == (recorded["match_id"], recorded["result_id"])
        for c in commands
    )
    assert designer.recorded["spectator"] == []
    [(title, body)] = designer.recorded["warnings"]
    assert title == "Spectator Unavailable" and "not for the selected match" in body
    # The fallback re-runs the preflight with the same pinned identity; this result still matches.
    assert designer.recorded["pygame"] == [result.with_name("replay.jsonl").resolve()]


@pytest.mark.gui
def test_a_background_preparation_yields_to_the_users_click(designer, monkeypatch, tmp_path):
    from battle_client.spectator_export import verify_presentation

    _configure_spectator(monkeypatch, tmp_path)
    log = []
    designer._spectator.log.connect(log.append)
    first = _v6_match(designer.data_root_for_test, "20261017-000000-11111111")
    _finish(designer, first)  # background preparation of the first match starts
    second = _v6_match(designer.data_root_for_test, "20261017-000000-22222222")
    _finish(designer, second)  # busy: no second background preparation
    designer._on_open_replay()  # View Last Match = the second match
    assert any("Stopping a background preparation" in line for line in log)
    _wait_idle(designer)
    [(_install, presentation)] = designer.recorded["spectator"]
    expected = json.loads(second.read_text(encoding="utf-8"))["match_id"]
    assert verify_presentation(presentation)["match"]["match_id"] == expected


@pytest.mark.gui
def test_misconfigured_spectator_is_reported_and_the_classic_viewer_opens(designer, monkeypatch, tmp_path):
    result = _v6_match(designer.data_root_for_test, "20261017-000000-eeeeeeee")
    _finish(designer, result)
    monkeypatch.setenv("BYTEFRAY_SPECTATOR", str(tmp_path / "missing" / "spectator.exe"))
    designer._on_open_replay()
    assert designer.recorded["pygame"] == [result.with_name("replay.jsonl").resolve()]
    [(title, body)] = designer.recorded["warnings"]
    assert title == "Spectator Unavailable" and "does not exist" in body
    designer._on_open_replay()  # reported once per session, logged every time
    assert len(designer.recorded["warnings"]) == 1
