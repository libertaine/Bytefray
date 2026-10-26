"""Refuse a pytest ``--basetemp`` whose cleanup would delete retained evidence.

pytest empties an existing ``--basetemp`` before first use, and ``pytest.ini``
points it at the repo-local ``.pytest-tmp``. A checkout that keeps research or
qualification evidence at one of the locations below must not lose it to an
ordinary test run, so such a basetemp is refused before pytest touches it. A
checkout without that evidence is unaffected. See docs/WINDOWS_DEV_NOTES.md.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent

# Retained-evidence locations, as glob patterns relative to the repository root.
PROTECTED_EVIDENCE_PATTERNS = (
    ".pytest-tmp/e9*",
    ".pytest_e9_*",
    "runs/e9_capability",
    "runs/research_v6_e8",
    "runs/research_v6_e9_*",
)


def _spellings(path: str | os.PathLike[str]) -> set[Path]:
    """*path* as written and with links/junctions resolved, case-normalized."""
    return {
        Path(os.path.normcase(os.path.abspath(path))),
        Path(os.path.normcase(os.path.realpath(path))),
    }


def _overlaps(a: Path, b: Path) -> bool:
    return a == b or a in b.parents or b in a.parents


def basetemp_conflicts(
    basetemp: str | os.PathLike[str], repo_root: Path = REPO_ROOT
) -> list[Path]:
    """Return the existing evidence locations *basetemp* equals, contains or lies in."""
    targets = _spellings(basetemp)
    return [
        evidence
        for pattern in PROTECTED_EVIDENCE_PATTERNS
        for evidence in sorted(repo_root.glob(pattern))
        if any(_overlaps(t, e) for t in targets for e in _spellings(evidence))
    ]


def pytest_configure(config: pytest.Config) -> None:
    # tmp_path_factory deletes the basetemp lazily, on first use, so this runs first.
    given = config.option.basetemp
    if not given:
        return  # pytest's per-user system temp root, never repository evidence
    # Relative to the current directory, exactly as pytest resolves it.
    conflicts = basetemp_conflicts(given)
    if conflicts:
        listed = "\n".join(f"  {path}" for path in conflicts)
        raise pytest.UsageError(
            f"refusing --basetemp={given}: pytest deletes an existing basetemp "
            f"before use, which would destroy this retained evidence:\n{listed}\n"
            "Pass --basetemp naming a disposable directory outside these "
            "locations; see docs/WINDOWS_DEV_NOTES.md."
        )
