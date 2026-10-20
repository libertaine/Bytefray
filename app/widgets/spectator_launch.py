"""Designer's asynchronous Bytefray Spectator launcher.

Verification and projection run in a ``bytefray spectator prepare`` child
process (never on the GUI thread); this object only tracks that process,
launches Spectator with the verified presentation it reports, and hands
anything Spectator cannot show back to Designer's existing replay viewer.

At most one preparation runs. Its ``QProcess`` belongs to this controller
until Qt deletes it, exactly once: a process that ends on its own is
released by its completion handler; a process that is stopped (superseded,
or the window closing) is first disconnected from every job, then killed
without waiting, and deleted when Qt reports that it has stopped. Nothing it
sends after it stops being current can reach a job.
"""

from __future__ import annotations

import subprocess
from collections.abc import Callable
from dataclasses import dataclass, replace
from pathlib import Path

from battle_engine.replay_integrity import ResultReplayRequest
from battle_engine.result_model import read_result
from PySide6.QtCore import QObject, QProcess, QProcessEnvironment, QTimer, Signal
from PySide6.QtWidgets import QMessageBox, QWidget

from app.services.spectator_viewer import (
    SPECTATOR_UNAVAILABLE_TITLE,
    PrepareOutcome,
    SpectatorInstall,
    build_prepare_command,
    discover_spectator,
    last_progress_stage,
    launch_spectator,
    match_support,
    parse_prepare_output,
    presentation_cache_root,
    source_environment,
    unavailable_message,
)

# How long after launch an exit still counts as "Spectator failed to open".
EARLY_EXIT_MS = 2500


@dataclass(frozen=True)
class _Job:
    """One match to prepare: Designer's own preflight request, with its identity pinned."""

    request: ResultReplayRequest
    open_when_ready: bool

    @property
    def result(self) -> Path:
        return Path(self.request.result_path).resolve()

    @property
    def key(self) -> tuple[Path, Path, str | None, str | None]:
        """Everything that decides which files are verified, and as which match.

        Two jobs may share one preparation only when their keys are equal. The
        cache root is the same for every job, and the Spectator install only
        matters at launch, where the newest request's install is used.
        """
        request = self.request
        return (
            self.result,
            Path(request.artifact_root).resolve(),
            request.expected_match_id,
            request.expected_result_id,
        )


def _pinned(request: ResultReplayRequest) -> ResultReplayRequest:
    """Pin the ids Designer's preflight just accepted, so a later replacement is refused.

    Called right after a successful preflight. Ids the caller already expects
    win, whatever they are; otherwise the result's current ids are recorded.
    """
    if request.expected_match_id is not None and request.expected_result_id is not None:
        return request
    try:
        envelope = read_result(request.result_path)
    except (OSError, ValueError, KeyError, TypeError):
        return request  # the export's own preflight will refuse it
    return replace(
        request,
        expected_match_id=(
            envelope.match_id if request.expected_match_id is None else request.expected_match_id
        ),
        expected_result_id=(
            envelope.result_id if request.expected_result_id is None else request.expected_result_id
        ),
    )


class SpectatorLaunchController(QObject):
    """Prepare and open one match at a time in Spectator.

    A request joins the preparation in flight only when its ``_Job.key`` is
    equal; the job then opens, or falls back, for that newest request. Any
    other click stops a background-only preparation, or waits next in line,
    where a newer click replaces it.

    ``fallback(request)`` opens Designer's existing viewer for the original
    request; it must run its own fresh replay preflight, because time passes
    between a click and a failed export.
    """

    log = Signal(str)

    def __init__(
        self, data_root: Path, parent: QWidget, fallback: Callable[[ResultReplayRequest], None]
    ) -> None:
        super().__init__(parent)
        self._data_root = Path(data_root)
        self._parent = parent
        self._fallback = fallback
        self._proc: QProcess | None = None
        self._job: _Job | None = None
        self._install: SpectatorInstall | None = None
        self._stdout = ""
        self._stage: str | None = None
        self._pending: _Job | None = None
        self._launched: list[subprocess.Popen[bytes]] = []
        self._problem_reported = False

    # ---- public API -----------------------------------------------------

    def busy(self) -> bool:
        return self._proc is not None

    def open_match(self, request: ResultReplayRequest) -> bool:
        """Take over viewing a match Designer has just preflighted, if Spectator applies.

        Returns ``False`` when Spectator is off, absent, misconfigured or does not
        support this match: the caller then opens its usual viewer.
        """
        install = self._usable_install(Path(request.result_path), report=True)
        if install is None:
            return False
        self._submit(_Job(_pinned(request), open_when_ready=True), install)
        return True

    def prewarm(self, result_path: Path) -> None:
        """Quietly prepare a just-finished match so a later View Last Match is quick."""
        install = self._usable_install(result_path, report=False)
        if install is None:
            return
        job = _Job(_pinned(ResultReplayRequest(Path(result_path), Path(result_path).parent)), open_when_ready=False)
        if self._proc is None and self._pending is None:
            self._start(job, install)

    def shutdown(self) -> None:
        """Stop for good when the window closes; Spectator windows already open stay open."""
        self._pending = None
        self._stop_current()

    # ---- internals ------------------------------------------------------

    def _submit(self, job: _Job, install: SpectatorInstall) -> None:
        """Run an explicit request now, share an equal one in flight, or wait next in line."""
        current = self._job
        if current is not None and current.key == job.key:
            # Same files, same expectations: share the preparation, but open and
            # fall back for this request, with the install found for it.
            self._job, self._install = job, install
            self._drop_pending()
            self.log.emit("[Spectator] Still preparing this match; it opens when ready.\n")
            return
        if current is not None and not current.open_when_ready:
            # Nobody is waiting for that background preparation: the click wins.
            self.log.emit("[Spectator] Stopping a background preparation to open the selected match.\n")
            self._stop_current()
        if self._proc is None:
            self._start(job, install)
            return
        if self._pending is None or self._pending.key != job.key:
            self._drop_pending()
        self._pending = job
        self.log.emit("[Spectator] Another match is being prepared; this one is next.\n")

    def _drop_pending(self) -> None:
        pending, self._pending = self._pending, None
        if pending is not None and pending.open_when_ready:
            self.log.emit(f"[Spectator] No longer waiting to open {pending.result}; a newer request replaced it.\n")

    def _stop_current(self) -> None:
        """Abandon the running preparation: its job never completes, and Qt deletes its process."""
        proc, self._proc = self._proc, None
        self._job = None
        self._install = None
        if proc is None:
            return
        for signal in (proc.readyReadStandardOutput, proc.finished, proc.errorOccurred):
            signal.disconnect()
        stopped = QProcess.ProcessState.NotRunning
        if proc.state() == stopped:
            proc.deleteLater()
            return
        # Killing is asynchronous: delete the object once Qt reports the child gone,
        # rather than blocking the GUI thread until it is.
        proc.stateChanged.connect(lambda state, p=proc: p.deleteLater() if state == stopped else None)
        proc.kill()

    def _report_problem(self, problem: str) -> None:
        """An installation problem: logged on every use, shown once per session."""
        self.log.emit(f"[Spectator] {problem} Using the Pygame replay viewer.\n")
        if not self._problem_reported:
            self._problem_reported = True
            QMessageBox.warning(
                self._parent,
                SPECTATOR_UNAVAILABLE_TITLE,
                f"{problem}\n\nBytefray will use the Pygame replay viewer.",
            )

    def _usable_install(self, result_path: Path, *, report: bool) -> SpectatorInstall | None:
        discovery = discover_spectator(self._data_root)
        if discovery.problem:
            if report:
                self._report_problem(discovery.problem)
            return None
        if discovery.install is None:
            return None
        support = match_support(result_path)
        if not support.supported:
            if report:
                self.log.emit(f"[Spectator] Not used: {support.message}. Using the Pygame replay viewer.\n")
            return None
        return discovery.install

    def _start(self, job: _Job, install: SpectatorInstall) -> None:
        request = job.request
        try:
            command = build_prepare_command(
                job.result,
                presentation_cache_root(self._data_root),
                artifact_root=Path(request.artifact_root),
                expected_match_id=request.expected_match_id,
                expected_result_id=request.expected_result_id,
            )
        except OSError as exc:
            # A frozen build without its companion ``bytefray`` executable: the
            # exporter cannot run at all, and nothing was started.
            problem = f"Spectator's match exporter is unavailable ({exc})."
            if job.open_when_ready:
                self._report_problem(problem)
                self._fallback(request)
            else:
                self.log.emit(f"[Spectator] Background preparation skipped: {problem}\n")
            return
        env = QProcessEnvironment()
        for key, value in source_environment(self._data_root).items():
            env.insert(key, value)
        proc = QProcess(self)
        proc.setProcessEnvironment(env)
        proc.setWorkingDirectory(str(self._data_root))
        proc.setProgram(command[0])
        proc.setArguments(command[1:])
        proc.readyReadStandardOutput.connect(lambda p=proc: self._read(p))
        proc.finished.connect(lambda code, _status, p=proc: self._finished(p, code))
        proc.errorOccurred.connect(lambda error, p=proc: self._error(p, error))
        self._proc = proc
        self._job = job
        self._install = install
        self._stdout = ""
        self._stage = None
        if job.open_when_ready:
            self.log.emit(
                "[Spectator] Verifying the match for Spectator (a first export of a "
                "long match can take a minute)...\n"
            )
        proc.start()

    def _read(self, proc: QProcess) -> None:
        if proc is not self._proc:
            return
        self._stdout += bytes(proc.readAllStandardOutput()).decode("utf-8", "replace")
        stage = last_progress_stage(self._stdout)
        if stage and stage != self._stage:
            self._stage = stage
            if self._job is not None and self._job.open_when_ready:
                self.log.emit(f"[Spectator] {stage}...\n")

    def _error(self, proc: QProcess, error: QProcess.ProcessError) -> None:
        # Only a failed start ends a preparation here (Qt sends no ``finished``
        # for it); any other error is followed by ``finished``, which completes it.
        if proc is not self._proc or error != QProcess.ProcessError.FailedToStart:
            return
        self._complete(proc, PrepareOutcome(None, code="exporter_failed", message=proc.errorString()))

    def _finished(self, proc: QProcess, code: int) -> None:
        if proc is not self._proc:
            return
        self._stdout += bytes(proc.readAllStandardOutput()).decode("utf-8", "replace")
        self._complete(proc, parse_prepare_output(self._stdout, code))

    def _complete(self, proc: QProcess, outcome: PrepareOutcome) -> None:
        job, install = self._job, self._install
        self._proc = None
        self._job = None
        self._install = None
        proc.deleteLater()  # it has stopped, and is no longer current: nothing else releases it
        if job is not None and install is not None:
            mismatch = outcome.mismatch(job.request.expected_match_id, job.request.expected_result_id)
            if outcome.ok and mismatch is not None:
                outcome = PrepareOutcome(None, code="identity_changed", message=mismatch)
            if outcome.ok and outcome.presentation is not None:
                note = "reused a verified presentation" if outcome.reused else "presentation verified and written"
                self.log.emit(f"[Spectator] {note}: {outcome.presentation}\n")
                if job.open_when_ready:
                    self._launch(install, outcome.presentation, job.request)
            elif job.open_when_ready:
                self.log.emit(f"[Spectator] Could not prepare the match ({outcome.code}): {outcome.message}\n")
                QMessageBox.warning(
                    self._parent,
                    SPECTATOR_UNAVAILABLE_TITLE,
                    unavailable_message(outcome.code, outcome.message)
                    + "\n\nBytefray will open the Pygame replay viewer instead.",
                )
                self._fallback(job.request)
        # Taken only now: a dialog above runs a nested event loop, during which a
        # newer request may have replaced it or another preparation may have begun.
        pending, self._pending = self._pending, None
        if pending is not None:
            again = self._usable_install(pending.result, report=pending.open_when_ready)
            if again is not None:
                self._submit(pending, again)
            elif pending.open_when_ready:
                self._fallback(pending.request)

    def _launch(self, install: SpectatorInstall, presentation: Path, request: ResultReplayRequest) -> None:
        self._launched = [p for p in self._launched if p.poll() is None]
        try:
            process = launch_spectator(install, presentation)
        except OSError as exc:
            self.log.emit(f"[Spectator] {exc}\n")
            QMessageBox.warning(
                self._parent,
                SPECTATOR_UNAVAILABLE_TITLE,
                f"{exc}\n\nBytefray will open the Pygame replay viewer instead.",
            )
            self._fallback(request)
            return
        self._launched.append(process)
        self.log.emit(f"[Spectator] Started {install.program.name} (process {process.pid}).\n")
        # With this controller as context, the check is dropped if the window goes first.
        QTimer.singleShot(EARLY_EXIT_MS, self, lambda p=process: self._check_early_exit(p))

    def _check_early_exit(self, process: subprocess.Popen[bytes]) -> None:
        code = process.poll()
        if code is not None and code != 0:
            self.log.emit(f"[Spectator] Spectator exited immediately with code {code}.\n")
            QMessageBox.warning(
                self._parent,
                SPECTATOR_UNAVAILABLE_TITLE,
                f"Spectator exited immediately (exit code {code}). Check its installation, "
                "or set BYTEFRAY_SPECTATOR=off to always use the Pygame replay viewer.",
            )
