"""Existence is not validity: a starter-agent directory must expose real,
loadable content before anything treats it as installed.

This pins the invariant Bytefray V6 Phase 2B.1 introduced: the same
discovery-level check ``resolve_agent``/``discover_agents_in`` already use
(``battle_engine.agents.agent_spec_from_dir``) is what now backs every
starter-source candidacy decision that used to be a bare ``Path.is_dir()``
check -- one that could not tell a genuinely installed starter from an
emptied directory holding nothing but a stale ``__pycache__``, which is the
exact local-state failure V6 Phase 0 hit and V6 Phase 1 traced to source
(``docs/research/v6/V6_PHASE0_BASELINE.md`` Sec 4.1;
``docs/research/v6/V6_PHASE1_REPOSITORY_DIET_AUDIT.md`` Sec 8.2).

Every fixture below is an isolated ``tmp_path`` directory -- never the
developer's real, gitignored runtime ``agents/`` catalog, which is exactly
the accidental dependency this phase exists to eliminate.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from battle_engine.agent_api import AgentManifestError
from battle_engine.agents import agent_spec_from_dir
from battle_engine.starters import STARTER_AGENT_NAMES, starter_agent_resource_dir


def _resource_root() -> Path:
    return Path(__file__).resolve().parents[2]


def test_missing_directory_is_not_a_valid_agent(tmp_path: Path):
    """State A: no directory exists at all."""

    assert agent_spec_from_dir(tmp_path / "nonexistent") is None


def test_empty_directory_is_not_a_valid_agent(tmp_path: Path):
    """State B: the directory exists but holds nothing."""

    agent_dir = tmp_path / "empty_agent"
    agent_dir.mkdir()

    assert agent_spec_from_dir(agent_dir) is None


def test_pycache_only_directory_is_not_a_valid_agent(tmp_path: Path):
    """State C: the exact Phase 0 shape -- the directory is present, but its
    only content is a stale bytecode cache left behind by a previous
    interpreter run."""

    agent_dir = tmp_path / "cache_only_agent"
    (agent_dir / "__pycache__").mkdir(parents=True)
    (agent_dir / "__pycache__" / "agent.cpython-313.pyc").write_bytes(b"\x00")

    assert agent_dir.is_dir()  # the old, insufficient check would have passed here
    assert agent_spec_from_dir(agent_dir) is None


def test_malformed_manifest_is_not_a_valid_agent(tmp_path: Path):
    """State D: partially/incorrectly installed -- a manifest is present but
    cannot be parsed, so the directory has *some* content yet is still not
    usable."""

    agent_dir = tmp_path / "broken_manifest_agent"
    agent_dir.mkdir()
    (agent_dir / "agent.yaml").write_text("{not: valid: yaml::", encoding="utf-8")

    with pytest.raises(AgentManifestError):
        agent_spec_from_dir(agent_dir)


def test_manifest_only_agent_is_valid(tmp_path: Path):
    """State E, native-VM shape: a bundled starter like ``runner`` ships only
    ``agent.yaml``, resolved against a built-in VM program by name -- no
    ``agent.py`` is required or expected for this shape."""

    agent_dir = tmp_path / "manifest_only_agent"
    agent_dir.mkdir()
    (agent_dir / "agent.yaml").write_text('{"name": "manifest_only_agent"}', encoding="utf-8")

    spec = agent_spec_from_dir(agent_dir)
    assert spec is not None
    assert spec.name == "manifest_only_agent"


def test_python_agent_with_manifest_and_source_is_valid(tmp_path: Path):
    """State E, Python shape: manifest plus implementation -- the shape every
    non-native bundled starter ships."""

    agent_dir = tmp_path / "python_agent"
    agent_dir.mkdir()
    (agent_dir / "agent.yaml").write_text('{"name": "python_agent"}', encoding="utf-8")
    (agent_dir / "agent.py").write_text(
        "def create_agent(**_kwargs):\n    raise NotImplementedError\n", encoding="utf-8"
    )

    spec = agent_spec_from_dir(agent_dir)
    assert spec is not None
    assert spec.kind == "python"


def test_valid_agent_with_harmless_extra_files_is_still_valid(tmp_path: Path):
    """State F: a real starter plus incidental extras (an interpreter cache,
    a stray note) is still recognized -- the check must not become so strict
    that ordinary runtime byproducts are mistaken for corruption."""

    agent_dir = tmp_path / "python_agent_with_extras"
    agent_dir.mkdir()
    (agent_dir / "agent.yaml").write_text(
        '{"name": "python_agent_with_extras"}', encoding="utf-8"
    )
    (agent_dir / "agent.py").write_text(
        "def create_agent(**_kwargs):\n    raise NotImplementedError\n", encoding="utf-8"
    )
    (agent_dir / "__pycache__").mkdir()
    (agent_dir / "__pycache__" / "agent.cpython-313.pyc").write_bytes(b"\x00")
    (agent_dir / "README.md").write_text("notes\n", encoding="utf-8")

    spec = agent_spec_from_dir(agent_dir)
    assert spec is not None


@pytest.mark.parametrize("name", STARTER_AGENT_NAMES)
def test_every_bundled_starter_is_valid_under_the_same_check(name: str):
    """The fix is generic across the whole catalog: every one of the
    bundled starters -- native VM (manifest-only) and Agent API v1 Python
    alike -- passes the same ``agent_spec_from_dir`` check the fix relies
    on, with no per-starter special-casing required."""

    resource_dir = starter_agent_resource_dir(name, resource_root=_resource_root())
    assert agent_spec_from_dir(resource_dir) is not None
