"""Designer's asynchronous Bytefray Spectator launcher.

Verification and projection run in a ``bytefray spectator prepare`` child
process (never on the GUI thread); this object only tracks that process,
launches Spectator with the verified presentation it reports, and hands
anything Spectator cannot show back to Designer's existing replay viewer.
"""

from __future__ import annotations

import subprocess
from collections.abc import Callable
from pathlib import Path

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


class SpectatorLaunchController(QObject):
    """Prepare and open one match at a time in Spectator.

    ``fallback(result_path)`` opens Designer's existing viewer; it must run its
    own fresh replay preflight, because time passes between a click and a
    failed export.
    """

    log = Signal(str)

    def __init__(self, data_root: Path, parent: QWidget, fallback: Callable[[Path], None]) -> None:
        super().__init__(parent)
        self._data_root = Path(data_root)
        self._parent = parent
        self._fallback = fallback
        self._proc: QProcess | None = None
        self._job: Path | None = None
        self._install: SpectatorInstall | None = None
        self._open_when_ready = False
        self._stdout = ""
        self._stage: str | None = None
        self._pending: tuple[Path, bool] | None = None
        self._launched: list[subprocess.Popen[bytes]] = []
        self._problem_reported = False

    # ---- public API -----------------------------------------------------

    def busy(self) -> bool:
        return self._proc is not None

    def open_match(self, result_path: Path) -> bool:
        """Take over viewing ``result_path`` (already preflighted) if Spectator applies.

        Returns ``False`` when Spectator is off, absent, misconfigured or does not
        support this match: the caller then opens its usual viewer.
        """
        install = self._usable_install(result_path, report=True)
        if install is None:
            return False
        result = Path(result_path).resolve()
        if self._job == result:
            self._open_when_ready = True
            self.log.emit("[Spectator] Still preparing this match; it opens when ready.\n")
            return True
        self._enqueue(result, install, open_when_ready=True)
        return True

    def prewarm(self, result_path: Path) -> None:
        """Quietly prepare a just-finished match so a later View Last Match is instant."""
        install = self._usable_install(result_path, report=False)
        if install is None:
            return
        result = Path(result_path).resolve()
        if self._job == result:
            return
        if self._proc is None:
            self._start(result, install, open_when_ready=False)

    def shutdown(self) -> None:
        self._pending = None
        proc, self._proc = self._proc, None
        self._job = None
        if proc is not None and proc.state() != QProcess.NotRunning:
            proc.kill()
            proc.waitForFinished(2000)

    # ---- internals ------------------------------------------------------

    def _usable_install(self, result_path: Path, *, report: bool) -> SpectatorInstall | None:
        discovery = discover_spectator(self._data_root)
        if discovery.problem:
            if report:
                self.log.emit(f"[Spectator] {discovery.problem} Using the classic replay viewer.\n")
                if not self._problem_reported:
                    self._problem_reported = True
                    QMessageBox.warning(
                        self._parent,
                        SPECTATOR_UNAVAILABLE_TITLE,
                        f"{discovery.problem}\n\nBytefray will use the classic replay viewer.",
                    )
            return None
        if discovery.install is None:
            return None
        support = match_support(result_path)
        if not support.supported:
            if report:
                self.log.emit(f"[Spectator] Not used: {support.message}. Using the classic replay viewer.\n")
            return None
        return discovery.install

    def _enqueue(self, result: Path, install: SpectatorInstall, *, open_when_ready: bool) -> None:
        if self._proc is None:
            self._start(result, install, open_when_ready=open_when_ready)
            return
        self._pending = (result, open_when_ready)
        self.log.emit("[Spectator] Another match is being prepared; this one is next.\n")

    def _start(self, result: Path, install: SpectatorInstall, *, open_when_ready: bool) -> None:
        command = build_prepare_command(result, presentation_cache_root(self._data_root))
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
        self._job = result
        self._install = install
        self._open_when_ready = open_when_ready
        self._stdout = ""
        self._stage = None
        if open_when_ready:
            self.log.emit(
                "[Spectator] Verifying and preparing the match for Spectator "
                "(long matches can take a minute)...\n"
            )
        proc.start()

    def _read(self, proc: QProcess) -> None:
        if proc is not self._proc:
            return
        self._stdout += bytes(proc.readAllStandardOutput()).decode("utf-8", "replace")
        stage = last_progress_stage(self._stdout)
        if stage and stage != self._stage:
            self._stage = stage
            if self._open_when_ready:
                self.log.emit(f"[Spectator] {stage}...\n")

    def _error(self, proc: QProcess, error: QProcess.ProcessError) -> None:
        if proc is not self._proc or error != QProcess.FailedToStart:
            return
        self._complete(proc, PrepareOutcome(None, code="exporter_failed", message=proc.errorString()))

    def _finished(self, proc: QProcess, code: int) -> None:
        if proc is not self._proc:
            return
        self._stdout += bytes(proc.readAllStandardOutput()).decode("utf-8", "replace")
        self._complete(proc, parse_prepare_output(self._stdout, code))

    def _complete(self, proc: QProcess, outcome: PrepareOutcome) -> None:
        result, install, open_when_ready = self._job, self._install, self._open_when_ready
        self._proc = None
        self._job = None
        proc.deleteLater()
        if result is not None and install is not None:
            if outcome.ok and outcome.presentation is not None:
                note = "reused a verified presentation" if outcome.reused else "presentation verified and written"
                self.log.emit(f"[Spectator] {note}: {outcome.presentation}\n")
                if open_when_ready:
                    self._launch(install, outcome.presentation, result)
            elif open_when_ready:
                self.log.emit(f"[Spectator] Could not prepare the match ({outcome.code}): {outcome.message}\n")
                QMessageBox.warning(
                    self._parent,
                    SPECTATOR_UNAVAILABLE_TITLE,
                    unavailable_message(outcome.code, outcome.message)
                    + "\n\nBytefray will open the classic replay viewer instead.",
                )
                self._fallback(result)
        pending, self._pending = self._pending, None
        if pending is not None:
            again = self._usable_install(pending[0], report=pending[1])
            if again is not None:
                self._start(pending[0], again, open_when_ready=pending[1])
            elif pending[1]:
                self._fallback(pending[0])

    def _launch(self, install: SpectatorInstall, presentation: Path, result: Path) -> None:
        self._launched = [p for p in self._launched if p.poll() is None]
        try:
            process = launch_spectator(install, presentation)
        except OSError as exc:
            self.log.emit(f"[Spectator] {exc}\n")
            QMessageBox.warning(
                self._parent,
                SPECTATOR_UNAVAILABLE_TITLE,
                f"{exc}\n\nBytefray will open the classic replay viewer instead.",
            )
            self._fallback(result)
            return
        self._launched.append(process)
        self.log.emit(f"[Spectator] Started {install.program.name} (process {process.pid}).\n")
        QTimer.singleShot(EARLY_EXIT_MS, lambda p=process: self._check_early_exit(p))

    def _check_early_exit(self, process: subprocess.Popen[bytes]) -> None:
        code = process.poll()
        if code is not None and code != 0:
            self.log.emit(f"[Spectator] Spectator exited immediately with code {code}.\n")
            QMessageBox.warning(
                self._parent,
                SPECTATOR_UNAVAILABLE_TITLE,
                f"Spectator exited immediately (exit code {code}). Check its installation, "
                "or set BYTEFRAY_SPECTATOR=off to always use the classic replay viewer.",
            )
