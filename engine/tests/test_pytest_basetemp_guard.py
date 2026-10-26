"""Regression tests for the root ``conftest.py`` basetemp guard.

Each case copies the real root ``conftest.py`` and ``pytest.ini`` into a
disposable sandbox repository holding fake evidence, then runs pytest in a
subprocess there. Nothing runs against this checkout or touches real evidence.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]

PROBE = "def test_probe(tmp_path):\n    (tmp_path / 'probe.txt').write_text('ok')\n"

# Fake evidence at two protected patterns; the bytes are deliberately awkward.
FAKE_EVIDENCE = {
    ".pytest-tmp/e9-fake-suite/witness/replay.jsonl": b'{"tick":0}\r\n\x00\xff',
    "runs/research_v6_e8/scope/verification_input.json": b'{"bound": true}\n',
}
EVIDENCE_ROOTS = (".pytest-tmp/e9-fake-suite", "runs/research_v6_e8")


def _sandbox(tmp_path: Path, *, evidence: bool = True) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    shutil.copyfile(ROOT / "conftest.py", repo / "conftest.py")
    shutil.copyfile(ROOT / "pytest.ini", repo / "pytest.ini")
    (repo / "test_probe.py").write_text(PROBE, encoding="utf-8")
    if evidence:
        for relative, data in FAKE_EVIDENCE.items():
            path = repo / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
    return repo


def _snapshot(root: Path) -> dict[str, bytes | None]:
    """Every directory (``None``) and file (bytes) under *root*, by relative path."""
    return {
        path.relative_to(root).as_posix(): None if path.is_dir() else path.read_bytes()
        for path in sorted(root.rglob("*"))
    }


def _evidence(repo: Path) -> dict[str, dict[str, bytes | None]]:
    return {root: _snapshot(repo / root) for root in EVIDENCE_ROOTS}


def _run(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = {k: v for k, v in os.environ.items() if k not in {"PYTEST_ADDOPTS", "PYTEST_PLUGINS"}}
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run(
        [sys.executable, "-m", "pytest", "test_probe.py", *args],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )


def _link_directory(link: Path, target: Path) -> None:
    """A directory link: a Windows junction, or a POSIX symlink."""
    if sys.platform == "win32":
        result = subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(link), str(target)],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            pytest.skip(f"Directory junction creation unavailable: {result.stderr.strip()}")
        return
    try:
        os.symlink(target, link, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("Symlink creation is not permitted in this environment.")


def _assert_refused(
    result: subprocess.CompletedProcess[str], protected: str
) -> None:
    assert result.returncode == pytest.ExitCode.USAGE_ERROR, result.stdout + result.stderr
    assert "refusing --basetemp=" in result.stderr
    assert str(Path(protected)) in result.stderr
    assert "test_probe" not in result.stdout  # refused before any test ran


def _assert_passed(result: subprocess.CompletedProcess[str]) -> None:
    assert result.returncode == pytest.ExitCode.OK, result.stdout + result.stderr
    assert "1 passed" in result.stdout


def test_default_basetemp_is_refused_and_evidence_is_preserved(tmp_path: Path) -> None:
    repo = _sandbox(tmp_path)
    before = _evidence(repo)

    _assert_refused(_run(repo), ".pytest-tmp/e9-fake-suite")

    assert _evidence(repo) == before
    assert before[".pytest-tmp/e9-fake-suite"]["witness/replay.jsonl"] == (
        FAKE_EVIDENCE[".pytest-tmp/e9-fake-suite/witness/replay.jsonl"]
    )


@pytest.mark.parametrize(
    ("basetemp", "protected"),
    [
        pytest.param(".pytest-tmp/e9-fake-suite", ".pytest-tmp/e9-fake-suite", id="equal"),
        pytest.param("runs/research_v6_e8", "runs/research_v6_e8", id="equal-runs"),
        pytest.param(
            "./runs/../runs/research_v6_e8", "runs/research_v6_e8", id="equal-dotted"
        ),
        pytest.param("runs/research_v6_e8/scope/new", "runs/research_v6_e8", id="inside"),
        pytest.param("runs", "runs/research_v6_e8", id="containing"),
        pytest.param(".pytest-tmp", ".pytest-tmp/e9-fake-suite", id="containing-default"),
    ],
)
@pytest.mark.parametrize("absolute", [False, True], ids=["relative", "absolute"])
def test_basetemp_overlapping_evidence_is_refused(
    tmp_path: Path, basetemp: str, protected: str, absolute: bool
) -> None:
    repo = _sandbox(tmp_path)
    before = _evidence(repo)
    given = str(repo / basetemp) if absolute else basetemp

    _assert_refused(_run(repo, f"--basetemp={given}"), protected)

    assert _evidence(repo) == before


@pytest.mark.skipif(sys.platform != "win32", reason="case-insensitive Windows paths")
@pytest.mark.parametrize(
    ("basetemp", "protected"),
    [
        pytest.param(".PYTEST-TMP", ".pytest-tmp/e9-fake-suite", id="default"),
        pytest.param("RUNS/Research_V6_E8/sub", "runs/research_v6_e8", id="inside"),
    ],
)
def test_case_variant_basetemp_is_refused_on_windows(
    tmp_path: Path, basetemp: str, protected: str
) -> None:
    repo = _sandbox(tmp_path)
    before = _evidence(repo)

    _assert_refused(_run(repo, f"--basetemp={basetemp}"), protected)

    assert _evidence(repo) == before


@pytest.mark.parametrize("suffix", ["", "sub"], ids=["link-to-evidence", "inside-link"])
def test_basetemp_linked_into_evidence_is_refused(tmp_path: Path, suffix: str) -> None:
    repo = _sandbox(tmp_path)
    before = _evidence(repo)
    links = tmp_path / "links"
    links.mkdir()
    _link_directory(links / "alias", repo / "runs" / "research_v6_e8")

    _assert_refused(
        _run(repo, f"--basetemp={links / 'alias' / suffix}"), "runs/research_v6_e8"
    )

    assert _evidence(repo) == before


def test_linked_evidence_inside_default_basetemp_is_refused(tmp_path: Path) -> None:
    repo = _sandbox(tmp_path)
    store = tmp_path / "evidence-store"
    store.mkdir()
    (store / "result.json").write_bytes(b'{"retained": true}\n')
    _link_directory(repo / ".pytest-tmp" / "e9-linked", store)

    _assert_refused(_run(repo), ".pytest-tmp/e9-linked")

    assert _snapshot(store) == {"result.json": b'{"retained": true}\n'}
    assert (repo / ".pytest-tmp" / "e9-linked" / "result.json").exists()


@pytest.mark.parametrize(
    "basetemp",
    [
        pytest.param(".pytest-tmp/scratch", id="default-sibling"),
        pytest.param("runs/new-work", id="runs-sibling"),
    ],
)
def test_sibling_basetemp_runs_and_leaves_evidence(tmp_path: Path, basetemp: str) -> None:
    repo = _sandbox(tmp_path)
    stale = repo / basetemp / "stale.txt"
    stale.parent.mkdir(parents=True)
    stale.write_text("disposable", encoding="utf-8")
    before = _evidence(repo)

    _assert_passed(_run(repo, f"--basetemp={basetemp}"))

    assert not stale.exists()  # pytest really did empty the sibling basetemp
    assert _evidence(repo) == before


def test_basetemp_outside_repository_runs(tmp_path: Path) -> None:
    repo = _sandbox(tmp_path)
    before = _evidence(repo)
    outside = tmp_path / "outside-basetemp"

    _assert_passed(_run(repo, f"--basetemp={outside}"))

    assert (outside / "test_probe0" / "probe.txt").read_text(encoding="utf-8") == "ok"
    assert _evidence(repo) == before


def test_default_basetemp_runs_when_no_evidence_exists(tmp_path: Path) -> None:
    repo = _sandbox(tmp_path, evidence=False)
    (repo / "runs").mkdir()

    _assert_passed(_run(repo))

    probe = repo / ".pytest-tmp" / "test_probe0" / "probe.txt"
    assert probe.read_text(encoding="utf-8") == "ok"
