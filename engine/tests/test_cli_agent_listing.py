"""Runtime-kind disclosure in the current ``bytefray agents`` listing.

V6 Phase 2B.12 leaves one executable runtime contract: Agent API v2 Python
agents under stable Ruleset 4. These tests pin the listing to that boundary
and to the vocabulary shared with the GUI.

Presentation only: the listing has no JSON/machine-readable form, and no
persisted artifact schema carries a runtime label, so nothing here
constrains a serialized contract.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from battle_engine.agents import agent_runtime_label, discover_agents
from battle_engine.command import main as cli_main
from battle_engine.ruleset_policy import BYTEFRAY_RULESET_V4_ID, agent_supported_by_ruleset
from battle_engine.starters import STARTER_AGENT_NAMES, ensure_starter_agents


def _resource_root() -> Path:
    return Path(__file__).resolve().parents[2]


@pytest.fixture
def data_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    ensure_starter_agents(resource_root=_resource_root(), data_root=tmp_path)
    monkeypatch.setenv("BYTEFRAY_ROOT", str(tmp_path))
    return tmp_path


def test_listing_labels_only_current_python_starters(data_root: Path, capsys) -> None:
    assert cli_main(["agents"]) == 0
    lines = capsys.readouterr().out.splitlines()
    labelled = {
        parts[1]: line
        for line in lines
        if line.startswith(" - ") and (parts := line.split())
    }

    assert set(labelled) == set(STARTER_AGENT_NAMES)
    for agent_name in STARTER_AGENT_NAMES:
        assert "[Python]" in labelled[agent_name], labelled[agent_name]
        assert "[VM]" not in labelled[agent_name]

    retired = {
        "claimer",
        "strider",
        "hunter",
        "wanderer",
        "adaptive",
        "raider",
        "sentinel",
        "runner",
        "writer",
        "seeker",
        "spiral",
    }
    assert retired.isdisjoint(labelled)


def test_listing_explains_the_single_current_runtime_contract(
    data_root: Path, capsys
) -> None:
    """The legend names only the remaining executable Ruleset/API pairing."""

    assert cli_main(["agents"]) == 0
    out = capsys.readouterr().out
    assert "[Python] agents run under bytefray-rules-4 with Agent API v2." in out
    assert "Ruleset v1" not in out
    assert "Ruleset v2" not in out
    assert "[VM]" not in out
    assert "edcode" not in out
    assert "pMARS" not in out


def test_listing_is_pure_ascii(data_root: Path, capsys) -> None:
    """The frozen ``bytefray.exe`` mangles non-ASCII stdout.

    A real, shipped defect this suite exists to prevent recurring: the
    listing previously used an em-dash for "no blob", which the source
    build rendered correctly and the PyInstaller executable rendered as a
    replacement character in the same shell.
    """

    assert cli_main(["agents"]) == 0
    out = capsys.readouterr().out
    assert out.isascii(), f"non-ASCII in agents listing: {out!r}"
    assert "blob=none" in out


def test_runtime_label_matches_the_designers_own_vocabulary(data_root: Path) -> None:
    """One shared spelling, so CLI and GUI never disagree about an agent."""

    from app.services.agent_catalog import AgentCatalog
    from app.services.designer_workflows import agent_runtime_label as designer_label

    specs = discover_agents(data_root)
    rows = {row.agent_id: row for row in AgentCatalog(data_root).list_agents()}
    for agent_id, spec in specs.items():
        engine_label = agent_runtime_label(spec)
        assert engine_label == f"[{designer_label(rows[agent_id])}]"


def test_labelling_follows_the_engines_current_ruleset_restriction(data_root: Path) -> None:
    """Every listed ``[Python]`` starter must execute under stable Ruleset 4."""

    for spec in discover_agents(data_root).values():
        assert agent_runtime_label(spec) == "[Python]"
        assert agent_supported_by_ruleset(spec, BYTEFRAY_RULESET_V4_ID)
