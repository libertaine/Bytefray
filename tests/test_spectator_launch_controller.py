"""SpectatorLaunchController: a missing exporter, request identity, and QProcess lifecycle.

The ``bytefray spectator prepare`` child is replaced by ``_ScriptedProcess``, a
real ``QProcess`` subclass that never spawns anything. Each test decides
exactly when a preparation starts, writes, exits, fails to start, or reports
its death after a kill, so overlapping preparations and late signals happen
by construction rather than by timing. The last tests run real child
processes. Marked ``gui`` like the other Designer tests.
"""

from __future__ import annotations

import json
import os
import sys
import time
import warnings
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest
from battle_engine.replay_integrity import ResultReplayRequest

QtCore = pytest.importorskip("PySide6.QtCore")
QProcess = QtCore.QProcess

pytestmark = pytest.mark.gui

NOT_RUNNING = QProcess.ProcessState.NotRunning
RUNNING = QProcess.ProcessState.Running
MISSING_EXPORTER = (
    "Packaged executable not found: bytefray.exe. Checked: "
    "C:\\Bytefray\\bytefray.exe, C:\\bytefray\\bytefray.exe"
)


class _Registry:
    def __init__(self) -> None:
        self.created: list[_ScriptedProcess] = []
        self.destroyed: list[int] = []
        self.fail_next_start = False


class _ScriptedProcess(QProcess):
    """A prepare child driven by the test.

    As with a real ``QProcess`` on Windows, a failed start is reported inside
    ``start()``; a kill takes effect only when the test calls ``die()``, the
    way the OS reports a killed child later.
    """

    registry: _Registry | None = None  # set per test

    def __init__(self, parent) -> None:
        super().__init__(parent)
        self.index = len(self.registry.created)
        self.registry.created.append(self)
        self.kills = 0
        self.waits = 0
        self._state = NOT_RUNNING
        self._stdout = b""
        index, destroyed = self.index, self.registry.destroyed
        self.destroyed.connect(lambda *_: destroyed.append(index))

    # ---- what the controller calls --------------------------------------

    def start(self, *_args) -> None:
        if self.registry.fail_next_start:
            self.registry.fail_next_start = False
            self.errorOccurred.emit(QProcess.ProcessError.FailedToStart)
            return
        self._state = RUNNING

    def state(self):
        return self._state

    def kill(self) -> None:
        self.kills += 1

    def waitForFinished(self, msecs: int = 30000) -> bool:
        self.waits += 1
        return False

    def readAllStandardOutput(self):
        data, self._stdout = self._stdout, b""
        return QtCore.QByteArray(data)

    def errorString(self) -> str:
        return "scripted: the exporter could not be started"

    # ---- what the test does ---------------------------------------------

    def say(self, record: dict) -> None:
        self._stdout += (json.dumps(record) + "\n").encode()
        self.readyReadStandardOutput.emit()

    def finish(self, code: int, *records: dict) -> None:
        self._stdout += "".join(json.dumps(r) + "\n" for r in records).encode()
        self._state = NOT_RUNNING
        self.stateChanged.emit(NOT_RUNNING)
        self.finished.emit(code, QProcess.ExitStatus.NormalExit)

    def die(self) -> None:
        """The OS reports the child gone, in the order Qt reports a kill."""
        self._state = NOT_RUNNING
        self.stateChanged.emit(NOT_RUNNING)
        self.errorOccurred.emit(QProcess.ProcessError.Crashed)
        self.finished.emit(62097, QProcess.ExitStatus.CrashExit)


def _flush_deletions() -> None:
    QtCore.QCoreApplication.sendPostedEvents(None, QtCore.QEvent.Type.DeferredDelete)


def _option(proc: QProcess, flag: str) -> str | None:
    args = proc.arguments()
    return args[args.index(flag) + 1] if flag in args else None


def _ok(presentation: Path, match_id: str, result_id: str) -> dict:
    return {
        "status": "ok",
        "presentation": str(presentation),
        "reused": False,
        "match_id": match_id,
        "result_id": result_id,
    }


def _error(code: str = "result_unverified", message: str = "the result did not verify") -> dict:
    return {"status": "error", "code": code, "message": message}


def _request(path: Path, root: Path | None = None, match_id=None, result_id=None) -> ResultReplayRequest:
    return ResultReplayRequest(
        path,
        path.parent if root is None else root,
        expected_result_id=result_id,
        expected_match_id=match_id,
    )


def _harness(monkeypatch, tmp_path, *, scripted: bool):
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from battle_client.spectator_export import SpectatorSupport
    from PySide6.QtWidgets import QApplication, QWidget

    import app.widgets.spectator_launch as launch
    from app.services.spectator_viewer import SpectatorDiscovery, SpectatorInstall

    QApplication.instance() or QApplication([])
    (tmp_path / "data").mkdir()
    h = SimpleNamespace(
        tmp=tmp_path,
        registry=_Registry(),
        ids={},
        commands=[],
        exporter_missing=False,
        child=None,
        launched=[],
        fallbacks=[],
        warnings=[],
        log=[],
    )
    if scripted:
        monkeypatch.setattr(_ScriptedProcess, "registry", h.registry)
        monkeypatch.setattr(launch, "QProcess", _ScriptedProcess)
    install = SpectatorInstall(tmp_path / "spectator" / "bytefray-spectator.exe", origin="test")
    monkeypatch.setattr(launch, "discover_spectator", lambda _root: SpectatorDiscovery(install))
    monkeypatch.setattr(launch, "match_support", lambda _path: SpectatorSupport(True))

    def read_result(path):  # what the run directory holds right now
        key = Path(path).resolve()
        if key not in h.ids:
            raise FileNotFoundError(path)
        match_id, result_id = h.ids[key]
        return SimpleNamespace(match_id=match_id, result_id=result_id)

    real_build = launch.build_prepare_command

    def build(*args, **kwargs):
        if h.exporter_missing:
            raise FileNotFoundError(MISSING_EXPORTER)
        command = real_build(*args, **kwargs)
        if h.child is not None:  # a real child process stands in for the exporter
            command = [sys.executable, "-c", h.child(kwargs)]
        h.commands.append(command)
        return command

    monkeypatch.setattr(launch, "read_result", read_result)
    monkeypatch.setattr(launch, "build_prepare_command", build)
    monkeypatch.setattr(
        launch,
        "launch_spectator",
        lambda _install, presentation: h.launched.append(Path(presentation))
        or SimpleNamespace(pid=1, poll=lambda: None),
    )
    monkeypatch.setattr(launch.QMessageBox, "warning", lambda _p, title, body: h.warnings.append((title, body)))
    h.parent = QWidget()
    h.controller = launch.SpectatorLaunchController(tmp_path / "data", h.parent, h.fallbacks.append)
    h.controller.log.connect(h.log.append)
    return h


def _teardown(h) -> None:
    h.controller.shutdown()
    for proc in h.registry.created:
        if proc.registry.destroyed.count(proc.index) == 0 and proc.state() != NOT_RUNNING:
            proc.die()
    h.parent.deleteLater()
    _flush_deletions()


@pytest.fixture
def harness(monkeypatch, tmp_path):
    h = _harness(monkeypatch, tmp_path, scripted=True)
    try:
        yield h
    finally:
        _teardown(h)


def _run(h, name: str, match_id: str = "match-1", result_id: str = "result-1") -> Path:
    """A completed match's result path; ``read_result`` reports these ids for it."""
    path = h.tmp / "data" / "runs" / "_designer" / name / "result.json"
    h.ids[path.resolve()] = (match_id, result_id)
    return path


def _pinned(request: ResultReplayRequest, match_id: str, result_id: str) -> ResultReplayRequest:
    return replace(
        request,
        expected_match_id=request.expected_match_id if request.expected_match_id is not None else match_id,
        expected_result_id=request.expected_result_id if request.expected_result_id is not None else result_id,
    )


def _idle(h) -> None:
    controller = h.controller
    assert not controller.busy()
    assert controller._proc is None and controller._job is None and controller._pending is None


# ---- Defect A: the exporter executable is missing ------------------------


def test_a_missing_exporter_skips_background_preparation_quietly(harness):
    h = harness
    h.exporter_missing = True
    h.controller.prewarm(_run(h, "a"))  # must not raise into Designer's result handling

    assert h.registry.created == []
    _idle(h)
    assert h.warnings == [] and h.fallbacks == [] and h.launched == []
    [line] = [line for line in h.log if "bytefray.exe" in line]
    assert line.startswith("[Spectator] Background preparation skipped") and "exporter" in line


def test_a_missing_exporter_on_open_is_reported_once_and_falls_back_each_time(harness):
    h = harness
    h.exporter_missing = True
    request = _request(_run(h, "a"))

    assert h.controller.open_match(request) is True
    [(title, body)] = h.warnings
    assert title == "Spectator Unavailable"
    assert "bytefray.exe" in body and "Pygame replay viewer" in body
    assert "verif" not in body.lower()  # not presented as a damaged match
    assert h.fallbacks == [_pinned(request, "match-1", "result-1")]
    assert h.registry.created == [] and h.launched == []
    _idle(h)

    assert h.controller.open_match(request) is True  # a standing condition: logged, not re-shown
    assert len(h.warnings) == 1
    assert h.fallbacks == [_pinned(request, "match-1", "result-1")] * 2
    assert sum("bytefray.exe" in line for line in h.log) == 2
    _idle(h)


def test_a_missing_exporter_for_a_waiting_request_falls_back_from_the_completion(harness):
    h = harness
    first = _request(_run(h, "a", "match-a", "result-a"))
    second = _request(_run(h, "b", "match-b", "result-b"))
    h.controller.open_match(first)
    h.controller.open_match(second)  # waits behind the first
    [proc] = h.registry.created

    h.exporter_missing = True
    proc.finish(0, _ok(h.tmp / "pa", "match-a", "result-a"))  # Qt delivers this; nothing may escape

    assert h.launched == [h.tmp / "pa"]
    assert h.fallbacks == [_pinned(second, "match-b", "result-b")]
    [(title, body)] = h.warnings
    assert title == "Spectator Unavailable" and "bytefray.exe" in body
    assert len(h.registry.created) == 1
    _idle(h)
    _flush_deletions()
    assert h.registry.destroyed == [0]


# ---- Defect B: which requests may share a preparation --------------------


def test_an_identical_click_shares_the_background_preparation(harness):
    h = harness
    result = _run(h, "a")
    h.controller.prewarm(result)
    [proc] = h.registry.created

    assert h.controller.open_match(_request(result)) is True  # View Last Match: no ids yet
    assert len(h.registry.created) == 1 and proc.kills == 0
    assert any("Still preparing this match" in line for line in h.log)
    proc.finish(0, _ok(h.tmp / "pres", "match-1", "result-1"))

    assert h.launched == [h.tmp / "pres"]
    assert h.fallbacks == [] and h.warnings == []
    _idle(h)


@pytest.mark.parametrize("field", ["artifact_root", "expected_match_id", "expected_result_id"])
def test_a_click_with_other_expectations_gets_its_own_preparation(harness, field):
    h = harness
    result = _run(h, "a")
    h.controller.prewarm(result)
    [background] = h.registry.created
    differs = {
        "artifact_root": {"root": result.parent.parent},
        "expected_match_id": {"match_id": "match-2"},
        "expected_result_id": {"result_id": "result-2"},
    }[field]
    request = _request(result, **differs)

    h.controller.open_match(request)

    assert background.kills == 1, "a background preparation with other expectations was reused"
    [_, own] = h.registry.created
    pinned = _pinned(request, "match-1", "result-1")
    assert h.controller._job.request == pinned
    assert _option(own, "--artifact-root") == str(pinned.artifact_root)
    assert _option(own, "--expect-match-id") == pinned.expected_match_id
    assert _option(own, "--expect-result-id") == pinned.expected_result_id


def test_a_replaced_match_is_never_opened_from_the_earlier_preparation(harness):
    h = harness
    result = _run(h, "a", "match-old", "result-old")
    h.controller.prewarm(result)
    [old] = h.registry.created
    h.ids[result.resolve()] = ("match-new", "result-new")  # the run directory now holds another match
    h.controller.open_match(_request(result))  # pinned to the new match at the click

    assert old.kills == 1
    [_, new] = h.registry.created
    # The old child had already printed its presentation when the kill landed.
    old.finish(0, _ok(h.tmp / "old", "match-old", "result-old"))
    assert h.launched == [] and h.fallbacks == [] and h.warnings == []
    assert h.controller._proc is new
    assert h.controller._job.request.expected_match_id == "match-new"

    new.finish(0, _ok(h.tmp / "new", "match-new", "result-new"))
    assert h.launched == [h.tmp / "new"]
    _idle(h)


def test_a_shared_preparation_falls_back_with_the_request_just_made(harness):
    h = harness
    result = _run(h, "a")
    h.controller.prewarm(result)
    [proc] = h.registry.created
    folder = result.parent.parent / ".." / result.parent.parent.name / result.parent.name
    request = _request(folder / result.name, root=folder)  # the same files, spelled as the click spelled them

    h.controller.open_match(request)
    assert len(h.registry.created) == 1
    proc.finish(1, _error())

    assert h.fallbacks == [_pinned(request, "match-1", "result-1")]
    assert h.fallbacks[0].result_path == request.result_path


def test_a_separate_preparation_falls_back_with_its_own_request(harness):
    h = harness
    result = _run(h, "a")
    h.controller.prewarm(result)
    request = _request(result, result_id="result-the-user-expects")
    h.controller.open_match(request)
    [_, own] = h.registry.created

    own.finish(1, _error(message="the result id is not 'result-the-user-expects'"))

    assert h.fallbacks == [_pinned(request, "match-1", "result-1")]
    assert h.fallbacks[0].expected_result_id == "result-the-user-expects"


def test_a_request_that_cannot_verify_is_not_vouched_for_by_an_earlier_one(harness):
    h = harness
    result = _run(h, "a")
    h.controller.open_match(_request(result))
    [first] = h.registry.created
    bogus = _request(result, match_id="match-1", result_id="not-this-result")
    h.controller.open_match(bogus)  # waits; it is not merged into the verified job in flight
    assert len(h.registry.created) == 1 and h.controller._pending.request == bogus

    first.finish(0, _ok(h.tmp / "pres", "match-1", "result-1"))
    assert h.launched == [h.tmp / "pres"]
    [_, second] = h.registry.created
    assert _option(second, "--expect-result-id") == "not-this-result"
    second.finish(0, _ok(h.tmp / "pres", "match-1", "result-1"))  # the files are still match-1's

    assert h.launched == [h.tmp / "pres"]
    [(title, body)] = h.warnings
    assert title == "Spectator Unavailable" and "not for the selected match" in body
    assert h.fallbacks == [bogus]


def test_only_the_latest_waiting_click_opens(harness):
    h = harness
    a, b, c = (_request(_run(h, name, f"match-{name}", f"result-{name}")) for name in "abc")
    h.controller.open_match(a)
    h.controller.open_match(b)
    h.controller.open_match(c)  # b no longer waits
    assert any("No longer waiting to open" in line for line in h.log)
    [pa] = h.registry.created

    pa.finish(0, _ok(h.tmp / "a", "match-a", "result-a"))
    [_, pc] = h.registry.created
    assert _option(pc, "--expect-match-id") == "match-c"
    pc.finish(0, _ok(h.tmp / "c", "match-c", "result-c"))

    assert h.launched == [h.tmp / "a", h.tmp / "c"]
    assert len(h.registry.created) == 2
    _idle(h)


def test_clicking_the_match_in_flight_again_drops_an_older_waiting_click(harness):
    h = harness
    a = _request(_run(h, "a", "match-a", "result-a"))
    b = _request(_run(h, "b", "match-b", "result-b"))
    h.controller.open_match(a)
    h.controller.open_match(b)
    h.controller.open_match(a)  # the latest choice is the match already being prepared

    assert h.controller._pending is None
    [pa] = h.registry.created
    pa.finish(0, _ok(h.tmp / "a", "match-a", "result-a"))
    assert h.launched == [h.tmp / "a"]
    assert len(h.registry.created) == 1
    _idle(h)


# ---- Defect C: QProcess ownership and late signals -----------------------


def test_a_successful_preparation_releases_its_process_once(harness):
    h = harness
    h.controller.open_match(_request(_run(h, "a")))
    [proc] = h.registry.created
    proc.say({"status": "progress", "stage": "verifying"})
    assert "[Spectator] verifying...\n" in h.log
    proc.finish(0, _ok(h.tmp / "pres", "match-1", "result-1"))

    assert h.launched == [h.tmp / "pres"]
    _idle(h)
    _flush_deletions()
    assert h.registry.destroyed == [0]


def test_a_failed_preparation_releases_its_process_once_and_falls_back(harness):
    h = harness
    request = _request(_run(h, "a"))
    h.controller.open_match(request)
    [proc] = h.registry.created
    proc.finish(1, _error())

    [(title, body)] = h.warnings
    assert title == "Spectator Unavailable" and "could not be verified" in body
    assert h.fallbacks == [_pinned(request, "match-1", "result-1")]
    _idle(h)
    _flush_deletions()
    assert h.registry.destroyed == [0]


def test_a_crashed_preparation_completes_exactly_once(harness):
    h = harness
    request = _request(_run(h, "a"))
    h.controller.open_match(request)
    [proc] = h.registry.created
    proc.die()  # errorOccurred(Crashed), then finished(CrashExit)

    assert len(h.warnings) == 1
    assert h.fallbacks == [_pinned(request, "match-1", "result-1")]
    _idle(h)
    _flush_deletions()
    assert h.registry.destroyed == [0]


def test_a_preparation_that_cannot_start_falls_back_once(harness):
    h = harness
    h.registry.fail_next_start = True
    request = _request(_run(h, "a"))
    assert h.controller.open_match(request) is True

    [(title, body)] = h.warnings
    assert title == "Spectator Unavailable" and "could not be started" in body
    assert h.fallbacks == [_pinned(request, "match-1", "result-1")]
    _idle(h)
    _flush_deletions()
    assert h.registry.destroyed == [0]


def test_a_superseded_preparation_is_killed_without_waiting_and_deleted_once_it_stops(harness):
    h = harness
    h.controller.prewarm(_run(h, "a", "match-a", "result-a"))
    [old] = h.registry.created
    h.controller.open_match(_request(_run(h, "b", "match-b", "result-b")))
    [_, new] = h.registry.created

    assert (old.kills, old.waits) == (1, 0)  # no blocking wait on the GUI thread
    assert h.controller._proc is new
    _flush_deletions()
    assert h.registry.destroyed == []  # still running until the OS reports it gone

    old.die()
    assert h.launched == [] and h.fallbacks == [] and h.warnings == []
    assert h.controller._proc is new and h.controller.busy()
    _flush_deletions()
    assert h.registry.destroyed == [0]

    new.finish(0, _ok(h.tmp / "b", "match-b", "result-b"))
    assert h.launched == [h.tmp / "b"]
    _flush_deletions()
    assert h.registry.destroyed == [0, 1]


def test_late_signals_from_a_stopped_preparation_never_reach_a_job(harness):
    h = harness
    h.controller.prewarm(_run(h, "a", "match-a", "result-a"))
    [old] = h.registry.created
    h.controller.open_match(_request(_run(h, "b", "match-b", "result-b")))
    [_, new] = h.registry.created
    lines = len(h.log)

    old.say({"status": "progress", "stage": "stale stage"})
    old.errorOccurred.emit(QProcess.ProcessError.FailedToStart)
    old.finish(0, _ok(h.tmp / "a", "match-a", "result-a"))
    # A delivery that slipped past the disconnection is still ignored.
    h.controller._read(old)
    h.controller._error(old, QProcess.ProcessError.FailedToStart)
    h.controller._finished(old, 0)

    assert h.log[lines:] == []
    assert h.launched == [] and h.fallbacks == [] and h.warnings == []
    assert h.controller._proc is new
    assert h.controller._job.request.expected_match_id == "match-b"
    _flush_deletions()
    assert h.registry.destroyed == [0]


def test_shutdown_stops_preparation_forgets_waiting_clicks_and_is_idempotent(harness):
    h = harness
    with warnings.catch_warnings():
        warnings.simplefilter("error")  # a second disconnect or deletion would warn
        h.controller.shutdown()  # nothing to stop
        h.controller.open_match(_request(_run(h, "a", "match-a", "result-a")))
        h.controller.open_match(_request(_run(h, "b", "match-b", "result-b")))
        [proc] = h.registry.created

        h.controller.shutdown()
        _idle(h)
        assert (proc.kills, proc.waits) == (1, 0)
        h.controller.shutdown()
        h.controller._stop_current()
        assert proc.kills == 1

        proc.die()
        _flush_deletions()
    assert h.registry.destroyed == [0]
    assert len(h.registry.created) == 1  # the waiting click never started
    assert h.launched == [] and h.fallbacks == [] and h.warnings == []


# ---- real child processes -----------------------------------------------


def _alive(pid: int) -> bool:
    if sys.platform == "win32":
        import ctypes

        kernel32 = ctypes.windll.kernel32
        handle = kernel32.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
        if not handle:
            return False
        try:
            code = ctypes.c_ulong()
            kernel32.GetExitCodeProcess(handle, ctypes.byref(code))
            return code.value == 259  # STILL_ACTIVE
        finally:
            kernel32.CloseHandle(handle)
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _until(condition, timeout: float = 30.0) -> None:
    from PySide6.QtWidgets import QApplication

    deadline = time.monotonic() + timeout
    while not condition():
        assert time.monotonic() < deadline, "the event loop never delivered the expected state"
        QApplication.processEvents()
        _flush_deletions()
        time.sleep(0.01)


@pytest.fixture
def real(monkeypatch, tmp_path):
    h = _harness(monkeypatch, tmp_path, scripted=False)
    try:
        yield h
    finally:
        h.controller.shutdown()
        h.parent.deleteLater()
        _flush_deletions()


def _real_children(h) -> None:
    """Match a waits like a long export; match b reports its presentation at once."""

    def child(kwargs: dict) -> str:
        if kwargs["expected_match_id"] == "match-a":
            return "import time; time.sleep(120)"
        record = _ok(h.tmp / "b", "match-b", "result-b")
        return f"print({json.dumps(json.dumps(record))}, flush=True)"

    h.child = child


def _watch(proc) -> dict:
    seen = {"pid": int(proc.processId()), "destroyed": False}
    proc.destroyed.connect(lambda *_: seen.__setitem__("destroyed", True))
    return seen


def test_a_superseded_real_preparation_is_killed_and_deleted(real):
    h = real
    _real_children(h)
    h.controller.prewarm(_run(h, "a", "match-a", "result-a"))
    old = h.controller._proc
    _until(lambda: old.state() == RUNNING)
    seen = _watch(old)
    assert _alive(seen["pid"])

    started = time.monotonic()
    h.controller.open_match(_request(_run(h, "b", "match-b", "result-b")))
    assert time.monotonic() - started < 1.0
    _until(lambda: seen["destroyed"] and h.launched)

    assert not _alive(seen["pid"])
    assert h.launched == [h.tmp / "b"]
    assert h.fallbacks == [] and h.warnings == []
    _until(lambda: not h.controller.busy())


def test_shutdown_kills_a_real_preparation(real):
    h = real
    _real_children(h)
    h.controller.prewarm(_run(h, "a", "match-a", "result-a"))
    proc = h.controller._proc
    _until(lambda: proc.state() == RUNNING)
    seen = _watch(proc)

    h.controller.shutdown()
    assert not h.controller.busy()
    _until(lambda: seen["destroyed"])
    assert not _alive(seen["pid"])
    assert h.launched == [] and h.fallbacks == [] and h.warnings == []
