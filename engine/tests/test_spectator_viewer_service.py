"""Designer's Qt-free Bytefray Spectator discovery and launch contract.

app/services/spectator_viewer.py: where Spectator is found (never a guessed
location), how it is launched (argument lists only, no shell), and how the
``bytefray spectator prepare`` child's report is read.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest
from battle_engine import launchers

from app.services import spectator_viewer as sv

_EXE_SUFFIX = ".exe" if sys.platform == "win32" else ""
EXECUTABLE = sv.WINDOWS_EXECUTABLES[0] if sys.platform == "win32" else sv.POSIX_EXECUTABLES[0]


def _executable(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"")
    path.chmod(0o755)
    return path


def _no_path(_name: str) -> None:
    return None


def test_nothing_configured_means_no_spectator(tmp_path):
    assert sv.discover_spectator(tmp_path, {}, which=_no_path) == sv.SpectatorDiscovery()


@pytest.mark.parametrize("value", ["off", "OFF", "pygame", "0", "none", "false"])
def test_spectator_can_be_turned_off(tmp_path, value):
    _executable(tmp_path / "spectator" / EXECUTABLE)  # even with a drop-in present
    found = sv.discover_spectator(tmp_path, {sv.ENV_SPECTATOR: value}, which=lambda _n: "x")
    assert found == sv.SpectatorDiscovery(disabled=True)


def test_configured_executable_folder_and_spaces(tmp_path):
    exe = _executable(tmp_path / "Program Files" / "Bytefray Spectator" / EXECUTABLE)
    by_file = sv.discover_spectator(tmp_path, {sv.ENV_SPECTATOR: str(exe)}, which=_no_path)
    by_folder = sv.discover_spectator(tmp_path, {sv.ENV_SPECTATOR: str(exe.parent)}, which=_no_path)
    assert by_file.install == by_folder.install == sv.SpectatorInstall(exe.resolve(), origin=sv.ENV_SPECTATOR)


def test_configured_project_needs_godot(tmp_path):
    project = tmp_path / "My Spectator"
    project.mkdir()
    (project / "project.godot").write_text("config_version=5\n", encoding="utf-8")
    missing = sv.discover_spectator(tmp_path, {sv.ENV_SPECTATOR: str(project)}, which=_no_path)
    assert missing.install is None and "BYTEFRAY_GODOT" in (missing.problem or "")
    godot = _executable(tmp_path / "Godot Engine" / f"godot{_EXE_SUFFIX}")
    for variable in sv.ENV_GODOT:
        found = sv.discover_spectator(tmp_path, {sv.ENV_SPECTATOR: str(project), variable: str(godot)}, which=_no_path)
        assert found.install == sv.SpectatorInstall(godot.resolve(), project.resolve(), origin=sv.ENV_SPECTATOR)


@pytest.mark.parametrize("kind", ["missing", "empty folder"])
def test_misconfiguration_is_reported_not_guessed_around(tmp_path, kind):
    _executable(tmp_path / "spectator" / EXECUTABLE)
    target = tmp_path / "nowhere"
    if kind == "empty folder":
        target.mkdir()
    found = sv.discover_spectator(tmp_path, {sv.ENV_SPECTATOR: str(target)}, which=lambda _n: "x")
    assert found.install is None and found.problem and str(target) in found.problem


def test_data_root_drop_in_then_path(tmp_path):
    on_path = _executable(tmp_path / "bin" / f"bytefray-spectator{_EXE_SUFFIX}")
    via_path = sv.discover_spectator(tmp_path, {}, which=lambda name: str(on_path) if name == sv.PATH_COMMAND else None)
    assert via_path.install == sv.SpectatorInstall(on_path.resolve(), origin="PATH")
    drop_in = _executable(tmp_path / "spectator" / EXECUTABLE)
    found = sv.discover_spectator(tmp_path, {}, which=lambda _n: str(on_path))
    assert found.install == sv.SpectatorInstall(drop_in.resolve(), origin="data root")


def test_installed_layout_finds_the_bundled_companion_first(tmp_path):
    """<install>/bin/bytefray-spectator/ (the Windows installer's layout) wins
    over a drop-in and PATH; the environment variable still overrides it."""
    bundled = _executable(tmp_path / "Bytefray 5.1 Alpha" / "bin" / sv.BUNDLED_DIRECTORY / EXECUTABLE)
    drop_in = _executable(tmp_path / "data" / "spectator" / EXECUTABLE)
    on_path = _executable(tmp_path / "elsewhere" / EXECUTABLE)
    found = sv.discover_spectator(
        tmp_path / "data", {}, which=lambda _n: str(on_path), bundled_directory=bundled.parent
    )
    assert found.install == sv.SpectatorInstall(bundled.resolve(), origin="bundled")
    configured = sv.discover_spectator(
        tmp_path / "data", {sv.ENV_SPECTATOR: str(on_path)}, which=_no_path, bundled_directory=bundled.parent
    )
    assert configured.install == sv.SpectatorInstall(on_path.resolve(), origin=sv.ENV_SPECTATOR)
    turned_off = sv.discover_spectator(
        tmp_path / "data", {sv.ENV_SPECTATOR: "off"}, which=_no_path, bundled_directory=bundled.parent
    )
    assert turned_off == sv.SpectatorDiscovery(disabled=True)
    bundled.unlink()  # a damaged installation falls through to the other locations
    fallback = sv.discover_spectator(tmp_path / "data", {}, which=_no_path, bundled_directory=bundled.parent)
    assert fallback.install == sv.SpectatorInstall(drop_in.resolve(), origin="data root")


def test_bundled_companion_is_beside_the_frozen_application(tmp_path, monkeypatch):
    assert sv.bundled_spectator_directory() is None  # source and wheel installs bundle nothing
    application = tmp_path / "Bytefray Ω" / "bin" / "bytefray-agent-designer" / f"bytefray-agent-designer{_EXE_SUFFIX}"
    _executable(application)
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", str(application))
    assert sv.bundled_spectator_directory() == (tmp_path / "Bytefray Ω" / "bin" / sv.BUNDLED_DIRECTORY).resolve()
    bundled = _executable(tmp_path / "Bytefray Ω" / "bin" / sv.BUNDLED_DIRECTORY / EXECUTABLE)
    found = sv.discover_spectator(tmp_path / "data", {}, which=_no_path)
    assert found.install == sv.SpectatorInstall(bundled.resolve(), origin="bundled")


def test_windows_accepts_only_real_executables(tmp_path):
    # A .cmd/.bat shim would be re-parsed by cmd.exe; only .exe files are launched.
    for name in ("bytefray-spectator.cmd", "bytefray-spectator.bat"):
        shim = _executable(tmp_path / "bin" / name)
        assert sv.discover_spectator(tmp_path, {}, platform="win32", which=lambda _n, s=shim: str(s)) == sv.SpectatorDiscovery()
        found = sv.discover_spectator(tmp_path, {sv.ENV_SPECTATOR: str(shim)}, platform="win32", which=_no_path)
        assert found.install is None and "not executable" in (found.problem or "")
    exe = _executable(tmp_path / "bin" / "bytefray-spectator.exe")
    assert sv.discover_spectator(tmp_path, {}, platform="win32", which=lambda _n: str(exe)).install is not None


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX execute bit")
def test_a_non_executable_file_is_not_runnable_on_posix(tmp_path):
    exe = tmp_path / "bytefray-spectator"
    exe.write_bytes(b"")
    exe.chmod(0o644)
    found = sv.discover_spectator(tmp_path, {sv.ENV_SPECTATOR: str(exe)}, which=_no_path)
    assert found.install is None and "not executable" in (found.problem or "")


def test_launch_commands_keep_paths_as_single_arguments(tmp_path):
    presentation = tmp_path / "cache with spaces" / "match_x-0123"
    exported = sv.SpectatorInstall(tmp_path / "Bytefray Spectator" / EXECUTABLE)
    assert exported.command(presentation) == [
        str(exported.program),
        "--",
        f"--fixture={presentation}",
        "--perspective=broadcast",
    ]
    project = sv.SpectatorInstall(tmp_path / "godot.exe", tmp_path / "My Spectator")
    assert project.command(presentation) == [
        str(tmp_path / "godot.exe"),
        "--path",
        str(tmp_path / "My Spectator"),
        "--",
        f"--fixture={presentation}",
        "--perspective=broadcast",
    ]


def test_launch_is_detached_with_no_shell_or_pipes(tmp_path):
    calls = []

    def popen(command, **options):
        calls.append((command, options))
        return "process"

    install = sv.SpectatorInstall(tmp_path / "Spectator Folder" / EXECUTABLE)
    assert sv.launch_spectator(install, tmp_path / "p", popen=popen) == "process"
    command, options = calls[0]
    assert command == install.command(tmp_path / "p")
    assert "shell" not in options
    assert options["stdin"] == options["stdout"] == options["stderr"] == subprocess.DEVNULL
    assert options["cwd"] == str(install.program.parent)
    if os.name == "nt":
        assert options["creationflags"] & subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        assert options["start_new_session"] is True

    def failing(command, **options):
        raise FileNotFoundError(2, "not found")

    with pytest.raises(OSError, match="Failed to start Spectator"):
        sv.launch_spectator(install, tmp_path / "p", popen=failing)


def test_prepare_command_source_and_frozen(monkeypatch, tmp_path):
    python = tmp_path / "Python Dir" / "python.exe"
    monkeypatch.setattr(sys, "frozen", False, raising=False)
    monkeypatch.setattr(sys, "executable", str(python))
    result = tmp_path / "runs" / "_designer" / "run one" / "result.json"
    cache = tmp_path / "cache" / "spectator" / "presentations"
    assert sv.build_prepare_command(result, cache) == [
        str(python), "-m", "battle_engine", "spectator", "prepare", "--source", str(result), "--cache", str(cache),
    ]  # fmt: skip
    assert sv.build_prepare_command(
        result, cache, artifact_root=result.parent, expected_match_id="match_1", expected_result_id="result_1"
    )[-6:] == ["--artifact-root", str(result.parent), "--expect-match-id", "match_1", "--expect-result-id", "result_1"]
    app_dir = tmp_path / "Bytefray Portable"
    app_dir.mkdir()
    bytefray = app_dir / f"bytefray{_EXE_SUFFIX}"
    bytefray.touch()
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", str(app_dir / f"bytefray-agent-designer{_EXE_SUFFIX}"))
    assert launchers.build_spectator_command(["verify"]) == [str(bytefray.resolve()), "spectator", "verify"]


def test_presentation_cache_is_outside_the_run_tree(tmp_path):
    assert sv.presentation_cache_root(tmp_path) == tmp_path.resolve() / "cache" / "spectator" / "presentations"


def test_prepare_output_parsing():
    ok = (
        '{"stage": "reconstructing", "status": "progress"}\n'
        '{"match_id": "m", "presentation": "/c/p", "result_id": "r", "reused": true, "status": "ok"}\n'
    )
    outcome = sv.parse_prepare_output(ok, 0)
    assert outcome == sv.PrepareOutcome(Path("/c/p"), True, match_id="m", result_id="r")
    assert outcome.mismatch("m", "r") is None and outcome.mismatch(None, None) is None
    assert "match_id" in (outcome.mismatch("other", "r") or "")
    assert "result_id" in (outcome.mismatch("m", "other") or "")
    assert sv.last_progress_stage(ok) == "reconstructing"
    error = '{"code": "trace_missing", "message": "no trace", "status": "error"}\n'
    assert sv.parse_prepare_output(error, 1) == sv.PrepareOutcome(None, code="trace_missing", message="no trace")
    assert sv.parse_prepare_output("Traceback (most recent call last):\n", 1).code == "exporter_failed"
    # An "ok" line from a process that still failed is not trusted.
    assert not sv.parse_prepare_output(ok, 3).ok


def test_unavailable_messages_are_traceback_free():
    assert sv.unavailable_message("evidence_unverified", "") == (
        "The match trace and replay did not verify against each other."
    )
    assert "Detail: x" in sv.unavailable_message("unknown_code", "x")
