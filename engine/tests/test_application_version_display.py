"""One application version, three spellings (docs/COMPONENT_VERSIONING.md §4.1).

``pyproject.toml`` holds the PEP 440 form (``5.1.0a1``), which result.json
records. People see the SemVer form (``5.1.0-alpha.1``) in About, ``bytefray
--version``, the installer and executable metadata. Windows binaries also need
a numeric four-part version (``5.1.0.1011``: 5.1.0a1, Windows build revision 1).
These must always agree.
"""

from __future__ import annotations

import os
import subprocess
import sys
from importlib.metadata import version as distribution_version
from pathlib import Path

import pytest
from battle_engine.project_info import ProjectInfo, get_project_info, public_version

from tools import windows_version_info as wvi
from tools.release_compatibility import python_package_version

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize(
    ("package", "public", "numeric"),
    [
        ("5.1.0a1", "5.1.0-alpha.1", (5, 1, 0, 1010)),
        ("5.1.0a12", "5.1.0-alpha.12", (5, 1, 0, 1120)),
        ("5.1.0b2", "5.1.0-beta.2", (5, 1, 0, 2020)),
        ("5.1.0rc1", "5.1.0-rc.1", (5, 1, 0, 3010)),
        ("5.1.0", "5.1.0", (5, 1, 0, 9000)),
        ("5.0.0", "5.0.0", (5, 0, 0, 9000)),
    ],
)
def test_the_three_spellings_agree(package: str, public: str, numeric: tuple[int, int, int, int]) -> None:
    assert public_version(package) == wvi.public_version(package) == public
    assert python_package_version(public) == package
    assert wvi.windows_file_version(package, revision=0) == numeric


def test_numeric_versions_sort_like_the_releases() -> None:
    ordered = [("5.1.0a1", 0), ("5.1.0a1", 1), ("5.1.0a1", 9), ("5.1.0a2", 0), ("5.1.0b1", 0), ("5.1.0rc1", 0),
               ("5.1.0", 0), ("5.1.1a1", 0)]
    numeric = [wvi.windows_file_version(version, revision) for version, revision in ordered]
    assert numeric == sorted(numeric) and len(set(numeric)) == len(numeric)


def test_the_rebuild_replaces_the_first_alpha_1_windows_build() -> None:
    """The first 5.1.0-alpha.1 build recorded 5.1.0.101 with its uninstall entry;
    the installer refuses to install over a higher recorded build, so this
    rebuild must be higher and every later version higher still."""

    current = wvi.windows_file_version("5.1.0a1")
    assert wvi.BUILD_REVISION == 1 and current == (5, 1, 0, 1011)
    assert (5, 1, 0, 101) < current < wvi.windows_file_version("5.1.0a2", revision=0)
    assert max(wvi.windows_file_version("5.1.0rc99", revision=9)) < 2**16


@pytest.mark.parametrize("revision", [-1, 10])
def test_a_revision_that_does_not_fit_is_refused(revision: int) -> None:
    with pytest.raises(SystemExit, match="revision"):
        wvi.windows_file_version("5.1.0a1", revision)


@pytest.mark.parametrize("version", ["development checkout", "5.1.0.dev3", "5.1.0+local", "5.1"])
def test_unrecognized_versions_are_displayed_unchanged(version: str) -> None:
    assert public_version(version) == version


def test_display_version_names_both_spellings_only_when_they_differ() -> None:
    def info(version: str) -> ProjectInfo:
        return ProjectInfo(version, 2, 2, 4, "3.13.14")

    assert info("5.1.0a1").display_version == "5.1.0-alpha.1 (package 5.1.0a1)"
    assert info("5.0.0").display_version == "5.0.0"
    assert get_project_info().version == distribution_version("bytefray")  # result.json keeps PEP 440


def test_version_flag_shows_the_public_version() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "battle_engine", "--version"], capture_output=True, text=True, check=False, cwd=ROOT
    )
    assert result.returncode == 0, result.stderr
    package = distribution_version("bytefray")
    assert " ".join(result.stdout.split()).startswith(f"Bytefray {get_project_info().display_version},")
    assert public_version(package) in result.stdout


def test_executables_get_a_complete_version_resource() -> None:
    pytest.importorskip("PyInstaller.utils.win32.versioninfo")
    resource = wvi.executable_version_info(ROOT, "bytefray-agent-designer", "Bytefray Agent Designer")
    package = wvi.project_version(ROOT)
    assert resource.ffi.fileVersionMS >> 16 == wvi.windows_file_version(package)[0]
    text = str(resource)
    for expected in (
        f"'ProductVersion', '{wvi.public_version(package)}'",
        f"'FileVersion', '{wvi.public_version(package)}'",
        "'OriginalFilename', 'bytefray-agent-designer.exe'",
        "'ProductName', 'Bytefray'",
        "'CompanyName', 'Bytefray Project'",
    ):
        assert expected in text


@pytest.mark.parametrize(
    ("environ", "expected"),
    [
        ({}, b"\\u03a9 \xe9"),  # escaped, Latin-1 text unchanged
        ({"PYTHONIOENCODING": "utf-8"}, "Ω é".encode()),
        ({"PYTHONIOENCODING": "utf-8:strict"}, "Ω é".encode()),
        ({"PYTHONIOENCODING": "no-such-codec"}, b"\\u03a9 \xe9"),
    ],
)
def test_output_streams_follow_pythonioencoding_as_a_frozen_build_must(monkeypatch, environ, expected) -> None:
    """A frozen interpreter ignores PYTHON* variables, so ``bytefray`` applies
    PYTHONIOENCODING itself (Designer sets it to utf-8 for its child commands
    and parses their output); without it, unencodable text is escaped."""

    import io

    from battle_engine import command

    streams = [io.TextIOWrapper(io.BytesIO(), encoding="cp1252") for _ in range(2)]
    monkeypatch.setattr(sys, "stdout", streams[0])
    monkeypatch.setattr(sys, "stderr", streams[1])
    command._configure_output_streams(environ)
    for stream in streams:
        stream.write("Ω é")
        stream.flush()
        assert stream.buffer.getvalue() == expected  # type: ignore[attr-defined]


def test_redirected_output_never_crashes_on_an_unencodable_path(tmp_path: Path) -> None:
    """Designer reads child output through a pipe, which uses the ANSI code page
    on Windows; an installed data root under a profile folder named in Greek,
    Cyrillic or CJK must not turn a finished match into a failure."""

    data_root = tmp_path / "Ωmega 数据"
    match = data_root / "runs" / "m"
    match.mkdir(parents=True)
    env = {key: value for key, value in os.environ.items() if key not in ("PYTHONIOENCODING", "PYTHONUTF8")}
    env["BYTEFRAY_ROOT"] = str(data_root)
    result = subprocess.run(
        [sys.executable, "-m", "battle_engine", "run", "--ticks", "5",
         "--replay", str(match / "replay.jsonl")],
        capture_output=True, check=False, cwd=tmp_path, env=env,
    )
    assert result.returncode == 0, result.stderr.decode("utf-8", "replace")
    assert (match / "result.json").is_file()
