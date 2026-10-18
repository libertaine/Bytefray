"""Qt-free Bytefray Spectator discovery, eligibility and launch for Designer.

Bytefray Spectator is a separate Godot application that plays verified
presentations written by ``bytefray spectator`` (``battle_client.spectator_export``).
Designer prefers it for completed two-entrant V6 alpha1 matches and keeps the
existing Pygame replay viewer for everything else.

Discovery, first match wins:

1. ``BYTEFRAY_SPECTATOR`` - an exported Spectator executable, a folder holding
   one, or a Spectator Godot project folder (``project.godot``; development
   mode, which also needs ``BYTEFRAY_GODOT`` or ``GODOT`` naming the Godot
   4.7.2 executable). ``off`` (or ``pygame``/``none``/``0``/``false``) turns
   Spectator off. A value that names nothing usable is reported, never
   silently replaced by a guess.
2. ``<data root>/spectator/`` - a portable Spectator export unpacked there.
3. ``bytefray-spectator`` on ``PATH``.

No location is hardcoded beyond these, and no shell is involved: every
command is an argument list, so paths with spaces need no quoting.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from battle_client.spectator_export import SpectatorSupport, spectator_support
from battle_engine.launchers import build_spectator_command

ENV_SPECTATOR = "BYTEFRAY_SPECTATOR"
ENV_GODOT = ("BYTEFRAY_GODOT", "GODOT")
DISABLED_VALUES = frozenset({"off", "0", "false", "none", "no", "pygame", "disabled"})
DROP_IN_DIRECTORY = "spectator"
PATH_COMMAND = "bytefray-spectator"
WINDOWS_EXECUTABLES = ("bytefray-spectator.exe", "Bytefray Spectator.exe")
POSIX_EXECUTABLES = ("bytefray-spectator.x86_64", "bytefray-spectator")

SPECTATOR_UNAVAILABLE_TITLE = "Spectator Unavailable"


@dataclass(frozen=True)
class SpectatorInstall:
    """A runnable Spectator: an exported executable, or Godot plus a project."""

    program: Path
    project: Path | None = None
    origin: str = ""

    def command(self, presentation: Path) -> list[str]:
        """Viewer arguments go after Godot's ``--`` separator in both modes."""
        prefix = [str(self.program)]
        if self.project is not None:
            prefix += ["--path", str(self.project)]
        return [*prefix, "--", f"--fixture={Path(presentation)}", "--perspective=broadcast"]


@dataclass(frozen=True)
class SpectatorDiscovery:
    install: SpectatorInstall | None = None
    disabled: bool = False
    problem: str | None = None


def _executable_names(platform: str) -> tuple[str, ...]:
    return WINDOWS_EXECUTABLES if platform == "win32" else POSIX_EXECUTABLES


def _runnable(path: Path, platform: str) -> bool:
    if not path.is_file():
        return False
    if platform == "win32":
        # Only a real executable: a .cmd/.bat shim would be re-parsed by cmd.exe,
        # which does not treat a presentation path as one opaque argument.
        return path.suffix.lower() == ".exe"
    return os.access(path, os.X_OK)


def _executable_in(folder: Path, platform: str) -> Path | None:
    for name in _executable_names(platform):
        candidate = folder / name
        if _runnable(candidate, platform):
            return candidate
    return None


def _godot(environ: Mapping[str, str], platform: str) -> Path | None:
    for name in ENV_GODOT:
        value = environ.get(name, "").strip()
        if value:
            candidate = Path(value).expanduser()
            return candidate if _runnable(candidate, platform) else None
    return None


def _from_configured(value: str, environ: Mapping[str, str], platform: str) -> SpectatorDiscovery:
    path = Path(value).expanduser()
    if path.is_file():
        if _runnable(path, platform):
            return SpectatorDiscovery(SpectatorInstall(path.resolve(), origin=ENV_SPECTATOR))
        return SpectatorDiscovery(problem=f"{ENV_SPECTATOR} names a file that is not executable: {path}")
    if path.is_dir():
        if (path / "project.godot").is_file():
            godot = _godot(environ, platform)
            if godot is None:
                return SpectatorDiscovery(
                    problem=(
                        f"{ENV_SPECTATOR} names a Spectator project ({path}); set BYTEFRAY_GODOT or GODOT "
                        "to the Godot 4.7.2 executable to run it."
                    )
                )
            return SpectatorDiscovery(SpectatorInstall(godot.resolve(), path.resolve(), origin=ENV_SPECTATOR))
        executable = _executable_in(path, platform)
        if executable is not None:
            return SpectatorDiscovery(SpectatorInstall(executable.resolve(), origin=ENV_SPECTATOR))
        return SpectatorDiscovery(problem=f"{ENV_SPECTATOR} names a folder with no Spectator executable: {path}")
    return SpectatorDiscovery(problem=f"{ENV_SPECTATOR} names a path that does not exist: {path}")


def discover_spectator(
    data_root: Path,
    environ: Mapping[str, str] | None = None,
    *,
    platform: str | None = None,
    which: Callable[[str], str | None] | None = None,
) -> SpectatorDiscovery:
    """Find Spectator without guessing; see the module docstring for the order."""
    values = os.environ if environ is None else environ
    system = sys.platform if platform is None else platform
    which = shutil.which if which is None else which
    configured = values.get(ENV_SPECTATOR, "").strip()
    if configured:
        if configured.lower() in DISABLED_VALUES:
            return SpectatorDiscovery(disabled=True)
        return _from_configured(configured, values, system)
    drop_in = _executable_in(Path(data_root).expanduser() / DROP_IN_DIRECTORY, system)
    if drop_in is not None:
        return SpectatorDiscovery(SpectatorInstall(drop_in.resolve(), origin="data root"))
    found = which(PATH_COMMAND)
    if found and _runnable(Path(found), system):
        return SpectatorDiscovery(SpectatorInstall(Path(found).resolve(), origin="PATH"))
    return SpectatorDiscovery()


def match_support(result_path: Path) -> SpectatorSupport:
    """Whether Spectator should be tried for this already-preflighted match."""
    return spectator_support(Path(result_path))


def presentation_cache_root(data_root: Path) -> Path:
    from battle_client.spectator_export import default_cache_root

    return default_cache_root(Path(data_root))


def build_prepare_command(
    result_path: Path,
    cache_root: Path,
    *,
    artifact_root: Path | None = None,
    expected_match_id: str | None = None,
    expected_result_id: str | None = None,
) -> list[str]:
    """``bytefray spectator prepare`` for one match, as an argument list.

    The artifact root and expected ids carry Designer's own preflight context
    into the export, whose preflight then enforces them too.
    """
    arguments = ["prepare", "--source", str(Path(result_path)), "--cache", str(Path(cache_root))]
    if artifact_root is not None:
        arguments += ["--artifact-root", str(Path(artifact_root))]
    if expected_match_id is not None:
        arguments += ["--expect-match-id", expected_match_id]
    if expected_result_id is not None:
        arguments += ["--expect-result-id", expected_result_id]
    return build_spectator_command(arguments)


def source_environment(data_root: Path, environ: Mapping[str, str] | None = None) -> dict[str, str]:
    """The child environment Designer's other source-mode commands get."""
    env = dict(os.environ if environ is None else environ)
    sep = ";" if os.name == "nt" else ":"
    root = Path(data_root)
    paths = [str(root / "engine" / "src"), str(root / "client" / "src")]
    if env.get("PYTHONPATH"):
        paths.append(env["PYTHONPATH"])
    env["PYTHONPATH"] = sep.join(paths)
    env["BYTEFRAY_ROOT"] = str(root)
    return env


@dataclass(frozen=True)
class PrepareOutcome:
    presentation: Path | None
    reused: bool = False
    code: str | None = None
    message: str = ""
    match_id: str | None = None
    result_id: str | None = None

    @property
    def ok(self) -> bool:
        return self.presentation is not None

    def mismatch(self, match_id: str | None, result_id: str | None) -> str | None:
        """Why a successful outcome is for a different match than expected, if it is."""
        for label, expected, actual in (("match_id", match_id, self.match_id), ("result_id", result_id, self.result_id)):
            if expected is not None and actual != expected:
                return f"the presentation's {label} {actual!r} is not the selected match's {expected!r}"
        return None


def parse_prepare_output(stdout: str, exit_code: int) -> PrepareOutcome:
    """Read the final JSON status line ``bytefray spectator prepare`` prints."""
    record: dict[str, Any] | None = None
    for line in reversed(stdout.splitlines()):
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            candidate = json.loads(line)
        except ValueError:
            continue
        if isinstance(candidate, dict) and candidate.get("status") in ("ok", "error"):
            record = candidate
            break
    if record is None:
        return PrepareOutcome(None, code="exporter_failed", message=f"the exporter exited with code {exit_code}")
    if record["status"] == "ok" and exit_code == 0 and isinstance(record.get("presentation"), str):
        return PrepareOutcome(
            Path(record["presentation"]),
            bool(record.get("reused")),
            match_id=record.get("match_id"),
            result_id=record.get("result_id"),
        )
    return PrepareOutcome(
        None, code=str(record.get("code") or "exporter_failed"), message=str(record.get("message") or "")
    )


def last_progress_stage(stdout: str) -> str | None:
    stage = None
    for line in stdout.splitlines():
        try:
            record = json.loads(line)
        except ValueError:
            continue
        if isinstance(record, dict) and record.get("status") == "progress":
            stage = str(record.get("stage"))
    return stage


def launch_spectator(
    install: SpectatorInstall,
    presentation: Path,
    *,
    popen: Callable[..., subprocess.Popen[bytes]] = subprocess.Popen,
) -> subprocess.Popen[bytes]:
    """Start Spectator as an independent process (no shell, no inherited pipes)."""
    command = install.command(presentation)
    options: dict[str, Any] = {
        "cwd": str(install.program.parent),
        "stdin": subprocess.DEVNULL,
        "stdout": subprocess.DEVNULL,
        "stderr": subprocess.DEVNULL,
        "close_fds": True,
    }
    if os.name == "nt":
        options["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        options["start_new_session"] = True
    try:
        return popen(command, **options)
    except OSError as exc:
        raise OSError(f"Failed to start Spectator '{command[0]}': {exc}") from exc


def unavailable_message(code: str | None, detail: str) -> str:
    """Traceback-free text for a Spectator export that did not produce a presentation."""
    reasons = {
        "result_unverified": "The match result or replay could not be verified.",
        "evidence_unverified": "The match trace and replay did not verify against each other.",
        "outcome_unverified": "The recorded outcome did not verify.",
        "source_changed": "The match files changed while they were being prepared.",
        "identity_changed": "The prepared presentation is not for the selected match.",
        "trace_missing": "The match has no sensing trace.",
        "agent_view_leak": "The Agent A view failed its knowledge-isolation check.",
    }
    first = reasons.get(code or "", "Spectator could not prepare this match.")
    return f"{first}\n\nDetail: {detail}" if detail else first


__all__: Sequence[str] = (
    "ENV_GODOT",
    "ENV_SPECTATOR",
    "SPECTATOR_UNAVAILABLE_TITLE",
    "PrepareOutcome",
    "SpectatorDiscovery",
    "SpectatorInstall",
    "build_prepare_command",
    "discover_spectator",
    "last_progress_stage",
    "launch_spectator",
    "match_support",
    "parse_prepare_output",
    "presentation_cache_root",
    "source_environment",
    "unavailable_message",
)
