"""Native Linux replay and current Active Sensing Designer execution witness."""

import hashlib
import importlib.metadata
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

BASE = Path(os.environ.get("BYTEFRAY_LINUX_QUALIFICATION_DIR", "/tmp/bytefray-m1-6b"))
EV = BASE / "evidence/final"
FRAMES = EV / "frames"
FRAMES.mkdir(parents=True, exist_ok=True)
os.environ.update(
    BYTEFRAY_ROOT=str(BASE / "designer-data"),
    BYTEFRAY_LINUX_WITNESS=str(EV / "viewer_states.jsonl"),
)
from battle_engine.result_model import read_result, verify_result_replay
from battle_engine.ruleset_names import ACTIVE_SENSING_DISPLAY_NAME
from battle_engine.sensing_demo import run_sensing_demo
from battle_engine.sensing_playback import verify_demonstration
from PySide6.QtCore import QProcess, Qt, QTimer, qVersion
from PySide6.QtGui import QGuiApplication
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QDialogButtonBox

from app.agent_designer import AgentDesigner
from app.services.ruleset_options import DESIGNER_RULESET_ID
from app.views.development import NewAgentDialog

app = QApplication([])
summary = {"baseline": "5d6fc19e2b84805e0453da2c851f1ab0d7804f2f", "steps": []}
if "--resume-engine" in sys.argv:
    summary = json.loads((EV / "native.json").read_text())
    # Retained engine evidence is rechecked, not counted as new executions.
    summary["steps"] = []


def save_json(name, payload):
    (EV / name).write_text(json.dumps(payload, indent=2, default=str) + "\n")


def record(name, **values):
    summary["steps"].append({"step": name, **values})
    save_json("native.json", summary)
    print(name, values, flush=True)


def pump(seconds=0.15):
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        app.processEvents()
        time.sleep(0.01)


def wait_process(d):
    end = time.monotonic() + 30
    while d._proc is not None and d._proc.state() != QProcess.NotRunning and time.monotonic() < end:
        pump(0.02)
    assert d._proc is not None and d._proc.state() == QProcess.NotRunning


def capture_qt(name, d):
    assert d.grab().save(str(FRAMES / name))


def states(pid=None):
    path = EV / "viewer_states.jsonl"
    values = []
    if path.exists():
        for line in path.read_text().splitlines():
            try:
                val = json.loads(line)
            except json.JSONDecodeError:
                continue
            if pid is None or val["pid"] == pid:
                values.append(val)
    return values


def await_state(predicate, pid=None, timeout=10):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        vals = states(pid)
        if vals and predicate(vals[-1]):
            return vals[-1]
        pump(0.03)
    raise AssertionError(f"Viewer state timeout; last={states(pid)[-1:]!r}")


def xdo(*args):
    return subprocess.check_output(["xdotool", *map(str, args)], text=True).strip()


def window_for(pid):
    end = time.monotonic() + 10
    while time.monotonic() < end:
        result = subprocess.run(
            [
                "xdotool",
                "search",
                "--onlyvisible",
                "--pid",
                str(pid),
                "--name",
                f"{ACTIVE_SENSING_DISPLAY_NAME} replay",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            return int(result.stdout.splitlines()[-1])
        pump(0.05)
    raise AssertionError("Actual viewer X11 window unavailable")


def key(window, name):
    xdo("windowfocus", "--sync", window)
    xdo("key", "--clearmodifiers", name)
    pump(0.08)


def capture_viewer(name, window):
    pump(0.1)
    assert QGuiApplication.primaryScreen().grabWindow(window).save(str(FRAMES / name))


def close_viewer(pid, window, proc=None):
    key(window, "Escape")
    if proc is not None:
        assert proc.wait(timeout=10) == 0
        record("viewer_clean_exit", pid=pid, exit_code=proc.returncode)
    else:
        end = time.monotonic() + 10
        while time.monotonic() < end:
            try:
                got, status = os.waitpid(pid, os.WNOHANG)
            except ChildProcessError:
                raise AssertionError("Viewer exit code unavailable")
            if got:
                assert os.waitstatus_to_exitcode(status) == 0
                record(
                    "designer_viewer_clean_exit",
                    pid=pid,
                    exit_code=os.waitstatus_to_exitcode(status),
                )
                return
            pump(0.03)
        raise AssertionError("Viewer did not close")


try:
    import battle_client
    import battle_engine
    import pygame

    pygame.display.init()
    pygame.display.set_mode((320, 240))
    env = {
        "distribution": Path("/etc/os-release").read_text(),
        "kernel": platform.release(),
        "machine": platform.machine(),
        "python": sys.version,
        "executable": sys.executable,
        "dependencies": {
            k: importlib.metadata.version(k)
            for k in ["bytefray", "PySide6", "pygame-ce", "PyYAML", "pytest", "ruff", "mypy"]
        },
        "virtualization": subprocess.run(
            ["systemd-detect-virt"], capture_output=True, text=True, check=False
        ).stdout.strip(),
        "pid1": Path("/proc/1/comm").read_text().strip(),
        "qt_version": qVersion(),
        "qt_platform": app.platformName(),
        "sdl_version": pygame.get_sdl_version(),
        "sdl_driver": pygame.display.get_driver(),
        "display": os.environ["DISPLAY"],
        "screen": str(app.primaryScreen().geometry()),
        "module_origins": {
            k: v.__file__
            for k, v in [("battle_engine", battle_engine), ("battle_client", battle_client)]
        },
        "xdpyinfo": subprocess.check_output(["xdpyinfo"], text=True),
    }
    pygame.quit()
    save_json("environment.json", env)
    assert env["qt_platform"] == "xcb" and env["sdl_driver"] == "x11"

    # Full contract profile, plus the Windows-equivalent completed 100-tick input.
    demos = []
    for label, ticks in [
        ("teaching_1000", 1000),
        ("teaching_1000_repeat", 1000),
        ("teaching_windows_equivalent", 100),
    ]:
        if "--resume-engine" in sys.argv:
            from types import SimpleNamespace

            folder = BASE / label
            demo = SimpleNamespace(
                demo_path=folder / "demo.json",
                replay_path=folder / "replay.jsonl",
                trace_path=folder / "trace.jsonl",
                result_path=folder / "result.json",
                match_result=read_result(folder / "result.json"),
                is_verified=True,
            )
        else:
            demo = run_sensing_demo(BASE / label, ticks=ticks, seed=0)
        check = verify_demonstration(demo.demo_path)
        assert demo.is_verified and check.teaching_verification.is_verified
        demos.append(demo)
        record(
            label,
            match_id=demo.match_result.match_id,
            result_id=demo.match_result.result_id,
            winner=demo.match_result.winner,
            steps=[
                {"name": s.name, "status": s.status.value, "tick": s.tick}
                for s in check.teaching_verification.steps
            ],
            states=len(check.sub_tick_states),
        )

    def logical_trace(d):
        return [
            {k: v for k, v in json.loads(line).items() if k != "wall_time_ms"}
            for line in d.trace_path.read_text().splitlines()
        ]

    assert demos[0].replay_path.read_bytes() == demos[1].replay_path.read_bytes()
    assert logical_trace(demos[0]) == logical_trace(demos[1])
    r1, r2 = read_result(demos[0].result_path), read_result(demos[1].result_path)
    assert r1.match_id == r2.match_id and r1.result_id == r2.result_id
    record(
        "determinism",
        replay_lines=len(demos[0].replay_path.read_text().splitlines()),
        trace_records=len(logical_trace(demos[0])),
        replay_sha256=hashlib.sha256(demos[0].replay_path.read_bytes()).hexdigest(),
        logical_trace_differences=0,
    )
    from battle_engine.starters import ensure_starter_agents

    from tools.qualification.run_determinism_and_neg_cases import run_negative_cases

    bootstrap = ensure_starter_agents(data_root=BASE / "designer-data")
    assert not bootstrap.errors
    run_negative_cases(BASE / "negative")
    record("artifact_fallback_and_preflight", passed=True)

    # Actual CLI subprocess; XTest controls and passive post-draw snapshots.
    log = (EV / "teaching_viewer.log").open("w")
    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "battle_client.cli",
            "--replay",
            str(demos[2].replay_path),
            "--renderer",
            "pygame",
            "--paused",
        ],
        stdout=log,
        stderr=subprocess.STDOUT,
    )
    pid = proc.pid
    state = await_state(lambda s: s["index"] == 0, pid)
    win = window_for(pid)
    record("teaching_viewer_launched", pid=pid, window=win, argv=state["argv"])
    capture_viewer("A_unknown.png", win)
    key(win, "Right")
    s = await_state(lambda s: s["index"] == 1, pid)
    assert s["contacts"] == []
    capture_viewer("B_observation_unknown.png", win)
    key(win, "Right")
    s = await_state(lambda s: s["index"] == 2, pid)
    assert s["receipt_status"] == "PENDING" and s["contacts"] == []
    assert any("1 action" in line for line in s["lines"])
    capture_viewer("C_sense_cost_pending.png", win)
    key(win, "Right")
    s = await_state(lambda s: s["index"] == 3, pid)
    assert s["contacts"][0]["address"] == 91
    capture_viewer("D_delayed_receipt.png", win)
    key(win, "Right")
    s = await_state(lambda s: s["index"] == 4, pid)
    assert s["own_anchors"] == [64]
    capture_viewer("E_move.png", win)
    key(win, "Right")
    key(win, "Right")
    s = await_state(lambda s: s["index"] == 6, pid)
    capture_viewer("F_write.png", win)
    key(win, "Left")
    await_state(lambda s: s["index"] == 5, pid)
    key(win, "plus")
    s = await_state(lambda s: s["speed"] > 1, pid)
    faster = s["speed"]
    key(win, "minus")
    s = await_state(lambda s: s["speed"] < faster, pid)
    key(win, "space")
    s = await_state(lambda s: s["playing"] and s["index"] > 5, pid)
    key(win, "space")
    s = await_state(lambda s: not s["playing"], pid)
    assert s["index"] > 5
    record(
        "play_pause_speed_and_rewind",
        paused_index=s["index"],
        increased_speed=faster,
        restored_speed=s["speed"],
    )
    key(win, "Home")
    await_state(lambda s: s["index"] == 0 and s["contacts"] == [], pid)
    xdo("mousemove", "--window", win, 550, 660)
    xdo("click", 1)
    s = await_state(lambda s: s["index"] > 100 and not s["playing"], pid)
    record("mouse_seek", index=s["index"], tick=s["tick"])
    key(win, "Home")
    await_state(lambda s: s["index"] == 0, pid)
    key(win, "shift+Right")
    s = await_state(lambda s: s["tick"] == 10, pid)
    assert s["contacts"] and s["contacts"][0]["age_ticks"] > 0
    capture_viewer("G_historical_age.png", win)
    key(win, "1")
    s = await_state(lambda s: s["view"] == "OmniscientView", pid)
    assert "Omniscient" in s["label"]
    capture_viewer("H_omniscient.png", win)
    key(win, "2")
    await_state(lambda s: s["view"] == "SensingView", pid)
    xdo("windowsize", win, 950, 680)
    await_state(lambda s: s["size"] == [950, 680], pid)
    win = window_for(pid)  # SDL may replace the X11 window on resize.
    key(win, "End")
    s = await_state(lambda s: s["terminal"] is not None, pid)
    capture_viewer("I_terminal.png", win)
    record("seek_restart_views_resize_terminal", terminal=s["terminal"], size=s["size"])
    close_viewer(pid, win, proc)
    log.close()

    # Real Qt workflow, actual QProcess matches and unmodified replay launcher.
    d = AgentDesigner()
    d.show()
    pump()
    assert d.isVisible() and DESIGNER_RULESET_ID == "bytefray-rules-6-alpha1"
    assert not hasattr(d.development, "rulesetCombo")
    assert not hasattr(d.advanced, "ruleset")
    capture_qt("01_designer_default.png", d)
    d.tabs.setCurrentWidget(d.development)

    def fill():
        for w in QApplication.topLevelWidgets():
            if isinstance(w, NewAgentDialog):
                w.agentId.setText("my_window_scout")
                w.templateCombo.setCurrentIndex(w.templateCombo.findData("window_scout"))
                box = w.findChild(QDialogButtonBox)
                QTest.mouseClick(box.button(QDialogButtonBox.Ok), Qt.LeftButton)
                return
        raise AssertionError("New Agent dialog not found")

    QTimer.singleShot(100, fill)
    QTest.mouseClick(d.development.btnNewAgent, Qt.LeftButton)
    pump()
    assert (d.data_root / "agents/my_window_scout/agent.py").is_file()
    d.development.selectAgent("my_window_scout")
    assert d.development.btnTest.isEnabled()
    record("designer_sensing_agent_selected", agent="my_window_scout", test_enabled=True)
    capture_qt("02_sensing_agent_selected.png", d)
    advanced = d.advanced
    d.tabs.setCurrentWidget(advanced)
    assert advanced.agentA.findData("my_window_scout") >= 0
    assert advanced.agentB.findData("v6_watchful_keeper") >= 0
    advanced.agentA.setCurrentIndex(advanced.agentA.findData("my_window_scout"))
    advanced.agentB.setCurrentIndex(advanced.agentB.findData("v6_watchful_keeper"))
    assert advanced.agentA.currentData() == "my_window_scout"
    assert advanced.agentB.currentData() == "v6_watchful_keeper"
    advanced.ticks.setValue(5)
    advanced.tabs.setCurrentIndex(1)
    advanced.schemaA._controls["search_interval"].setValue(2)
    advanced.schemaA._controls["move_step"].setValue(32)
    assert not advanced.parameter_validation_errors()
    capture_qt("03_parameters.png", d)
    d.tabs.setCurrentWidget(d.development)
    QTest.mouseClick(d.development.btnValidate, Qt.LeftButton)
    wait_process(d)
    assert "Last validation: Valid" in d.development.statusLabel.text()
    record("designer_alpha_validation", status=d.development.statusLabel.text())
    capture_qt("04_validation.png", d)
    d.tabs.setCurrentWidget(advanced)
    advanced.tabs.setCurrentIndex(0)
    QTest.mouseClick(advanced.btnRun, Qt.LeftButton)
    wait_process(d)
    first_path = Path(d._last_result_path)
    first = read_result(first_path)
    assert verify_result_replay(first_path)
    assert first.ruleset_id == "bytefray-rules-6-alpha1"
    assert first.entrants[0]["metadata"]["parameters"] == {"search_interval": 2, "move_step": 32}
    record(
        "designer_match_1",
        result_path=str(first_path),
        result_id=first.result_id,
        parameters=first.entrants[0]["metadata"]["parameters"],
    )
    advanced.tabs.setCurrentIndex(3)
    capture_qt("05_first_result.png", d)

    def open_and_confirm(path):
        known = {s["pid"] for s in states()}
        # Actual button -> Designer result preflight -> unmocked Popen launcher.
        QTest.mouseClick(advanced.btnOpen, Qt.LeftButton)
        s = await_state(lambda s: s["pid"] not in known)
        child = s["pid"]
        window = window_for(child)
        assert s["argv"][s["argv"].index("--replay") + 1] == str(path.with_name("replay.jsonl"))
        key(window, "Home")
        s = await_state(lambda s: s["index"] == 0, child)
        key(window, "Right")
        await_state(lambda s: s["index"] == 1, child)
        record("designer_reopened_correct_match", pid=child, argv=s["argv"])
        capture_viewer("06_designer_replay_" + str(len(summary["steps"])) + ".png", window)
        close_viewer(child, window)

    open_and_confirm(first_path)
    before = {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in first_path.parent.iterdir()
        if p.is_file()
    }
    advanced.tabs.setCurrentIndex(1)
    advanced.schemaA._controls["search_interval"].setValue(3)
    advanced.schemaA._controls["move_step"].setValue(16)
    pump()
    assert "Earlier revision/settings" in advanced.resultRevisionLabel.text()
    record("earlier_revision_label", label=advanced.resultRevisionLabel.text())
    open_and_confirm(first_path)
    advanced.tabs.setCurrentIndex(0)
    QTest.mouseClick(advanced.btnRun, Qt.LeftButton)
    wait_process(d)
    second_path = Path(d._last_result_path)
    second = read_result(second_path)
    assert verify_result_replay(second_path)
    assert second.ruleset_id == "bytefray-rules-6-alpha1"
    assert second_path != first_path and second.result_id != first.result_id
    assert second.entrants[0]["metadata"]["parameters"] == {"search_interval": 3, "move_step": 16}
    assert before == {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in first_path.parent.iterdir()
        if p.is_file()
    }
    record(
        "designer_match_2",
        result_path=str(second_path),
        result_id=second.result_id,
        parameters=second.entrants[0]["metadata"]["parameters"],
        first_match_unchanged=True,
    )
    advanced.tabs.setCurrentIndex(3)
    capture_qt("07_second_result.png", d)
    open_and_confirm(second_path)
    d.close()
    pump()
    assert not d.isVisible()
    d.deleteLater()
    pump()
    assert not (EV / "viewer_states.jsonl.errors").exists()
    record("designer_clean_close", visible=False)
    summary["passed"] = True
    save_json("native.json", summary)
finally:
    app.quit()
