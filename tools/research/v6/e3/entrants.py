"""Tracked-source resolution for the V6 E3 entrants.

The E3 matrix runs the ten E2 fixtures and their twins, unchanged, plus the
E3 jam sniper and its twin (``fixtures/agents``). The consolidated
experiment harness resolves only its own tracked directories, and it is part
of the frozen E2 analysis instrument, so it is not edited to learn about E3.
Instead this module resolves E3 names from the E3 directory and every other
name through the harness, and seeds an evaluation data root with the E3
fixtures before the harness fills in the rest (``prepare_data_root``): the
harness copies an agent only when its directory is not there yet.

Every source is a tracked repository path; nothing is read from the ignored
runtime ``agents/`` catalogue.
"""

from __future__ import annotations

import shutil
from collections.abc import Sequence
from pathlib import Path

from battle_engine.agent_revisions import agent_revision_fingerprint
from battle_engine.agents import agent_spec_from_dir

from tools.research.v6.experiment_harness import (
    find_tracked_agent_source,
    prepare_benchmark_data_root,
)

E3_FIXTURE_SOURCE_DIR = Path(__file__).resolve().parent / "fixtures" / "agents"
JAM_SNIPER = "e3_jam_sniper"
JAM_SNIPER_TWIN = "e3_jam_sniper_twin"
E3_FIXTURES: tuple[str, ...] = (JAM_SNIPER, JAM_SNIPER_TWIN)


def find_agent_source(name: str) -> Path | None:
    """The tracked source directory of one E3 entrant, or ``None``."""
    if name in E3_FIXTURES:
        directory = E3_FIXTURE_SOURCE_DIR / name
        return directory if directory.is_dir() and agent_spec_from_dir(directory) is not None else None
    return find_tracked_agent_source(name)


def prepare_data_root(dest_root: Path, field: Sequence[str]) -> Path:
    """Copy every entrant of ``field`` from tracked sources into ``dest_root/agents``."""
    agents_dir = dest_root / "agents"
    agents_dir.mkdir(parents=True, exist_ok=True)
    for name in field:
        if name in E3_FIXTURES and not (agents_dir / name).exists():
            source = find_agent_source(name)
            if source is None:
                raise FileNotFoundError(f"Tracked E3 fixture {name!r} not found in {E3_FIXTURE_SOURCE_DIR}")
            shutil.copytree(source, agents_dir / name, ignore=shutil.ignore_patterns("__pycache__"))
    return prepare_benchmark_data_root(dest_root, field)


def fingerprints(names: Sequence[str]) -> dict[str, str]:
    """Live ``agent_revision_fingerprint`` of each entrant's tracked source."""
    out: dict[str, str] = {}
    for name in names:
        source = find_agent_source(name)
        if source is None:
            raise FileNotFoundError(f"E3 entrant {name!r} has no tracked source")
        fingerprint = agent_revision_fingerprint(source)
        if fingerprint is None:
            raise RuntimeError(f"E3 entrant {name!r} has no computable revision fingerprint")
        out[name] = fingerprint
    return out
