"""HD-4 / HD-7: the tracked V6 E2 research fixtures (design review Sec G).

* HD-4: every Sec G.2 agent has exactly one twin -- a byte-identical
  ``agent.py`` under a distinct fixture identity -- and the twin behaves
  identically in real matches.
* HD-7: the fixtures are tracked, fingerprinted, resolved by the harness from
  tracked sources only, Agent API v2, and never product starters.
* ``v4_probe`` reproduces the frozen V4 exploit characterization probe tick
  for tick.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from battle_engine.agents import agent_spec_from_dir, discover_agents, resolve_agent
from battle_engine.config import Config
from battle_engine.match_service import MatchEntrant, MatchRequest, NativeMatchService
from battle_engine.placement import resolve_direct_match_starts
from battle_engine.replay import TickSnapshot, iter_replay
from battle_engine.ruleset_policy import (
    BYTEFRAY_RULESET_V4_ID,
    BYTEFRAY_RULESET_V6_RESEARCH_CAPTURE_HOLD_K2_ID,
)
from battle_engine.starters import STARTER_AGENT_NAMES, ensure_starter_agents
from test_v4_exploit_characterization import _bootstrap_probe

from tools.research.v6.e2 import matrix
from tools.research.v6.experiment_harness import (
    E2_FIXTURE_SOURCE_DIR,
    REPO_ROOT,
    STARTER_AGENT_SOURCE_DIR,
    TRACKED_BENCHMARK_SOURCE_DIRS,
    find_tracked_agent_source,
    fingerprint_corpus,
    prepare_benchmark_data_root,
)

FIXTURE_DIRS = sorted(p for p in E2_FIXTURE_SOURCE_DIR.iterdir() if p.is_dir() and p.name != "__pycache__")


def test_fixture_directory_holds_exactly_the_ten_agents_and_their_twins() -> None:
    assert {p.name for p in FIXTURE_DIRS} == set(matrix.E2_AGENTS) | set(matrix.E2_TWINS)
    assert len(matrix.E2_AGENTS) == len(set(matrix.E2_AGENTS)) == 10


@pytest.mark.parametrize("agent", matrix.E2_AGENTS)
def test_hd4_every_primary_agent_has_exactly_one_valid_twin(agent: str) -> None:
    twins = [p.name for p in FIXTURE_DIRS if p.name != agent and p.name.startswith(agent) and p.name.endswith("_twin")]
    assert twins == [matrix.twin_of(agent)]
    primary_dir, twin_dir = E2_FIXTURE_SOURCE_DIR / agent, E2_FIXTURE_SOURCE_DIR / twins[0]
    # Identical implementation, byte for byte; nothing else in either directory.
    assert (twin_dir / "agent.py").read_bytes() == (primary_dir / "agent.py").read_bytes()
    files = {"agent.py", "agent.yaml"}
    assert {p.name for p in primary_dir.iterdir() if p.name != "__pycache__"} == files
    assert {p.name for p in twin_dir.iterdir() if p.name != "__pycache__"} == files
    # Distinct identity: only the manifest's name and display differ.
    primary, twin = agent_spec_from_dir(primary_dir), agent_spec_from_dir(twin_dir)
    assert (primary.name, twin.name) == (agent, twins[0])
    for spec in (primary, twin):
        assert (spec.kind, spec.api_version) == ("python", 2)
    diff = [
        line
        for a, b in zip(
            (primary_dir / "agent.yaml").read_text(encoding="utf-8").splitlines(),
            (twin_dir / "agent.yaml").read_text(encoding="utf-8").splitlines(),
            strict=True,
        )
        if a != b
        for line in (a.split(":")[0],)
    ]
    assert diff == ["name", "display"]
    fingerprints = fingerprint_corpus([agent, twins[0]])
    assert fingerprints[agent]["fingerprint"] != fingerprints[twins[0]]["fingerprint"]


def test_hd7_fixtures_are_tracked_fingerprinted_and_resolved_from_tracked_sources() -> None:
    assert E2_FIXTURE_SOURCE_DIR in TRACKED_BENCHMARK_SOURCE_DIRS
    roster = sorted(matrix.AGENT_FINGERPRINTS)
    assert set(roster) == {name for f in matrix.FIELDS for name in f.agents}
    live = fingerprint_corpus(roster)
    assert {name: live[name]["fingerprint"] for name in roster} == matrix.AGENT_FINGERPRINTS
    for name in roster:
        source = find_tracked_agent_source(name)
        assert source is not None and source.is_relative_to(REPO_ROOT)
        # Never the ignored runtime catalogue at the repository root.
        assert not source.is_relative_to(REPO_ROOT / "agents")
    if not (REPO_ROOT / ".git").exists():
        pytest.skip("not a git checkout")
    tracked = subprocess.run(
        ["git", "ls-files", "--", "tools/research/v6/e2/fixtures/agents"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=True,
    ).stdout.split()
    expected = sorted(f"tools/research/v6/e2/fixtures/agents/{p.name}/{f}" for p in FIXTURE_DIRS for f in ("agent.py", "agent.yaml"))
    assert sorted(t for t in tracked if t.endswith(("agent.py", "agent.yaml"))) == expected


def test_hd7_fixtures_readme_lists_every_fingerprint() -> None:
    readme = (E2_FIXTURE_SOURCE_DIR / "README.md").read_text(encoding="utf-8")
    for name in (*matrix.E2_AGENTS, *matrix.E2_TWINS):
        assert f"`{name}`" in readme
        assert matrix.AGENT_FINGERPRINTS[name] in readme


def test_hd7_fixtures_are_never_product_starter_agents(tmp_path: Path) -> None:
    e2_names = set(matrix.E2_AGENTS) | set(matrix.E2_TWINS)
    assert not e2_names & set(STARTER_AGENT_NAMES)
    assert not e2_names & {p.name for p in STARTER_AGENT_SOURCE_DIR.iterdir()}
    ensure_starter_agents(data_root=tmp_path)
    assert not e2_names & set(discover_agents(tmp_path))
    pyproject = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert "tools/research/v6/e2" not in pyproject.split("[tool.ruff]")[0]


def test_fixtures_import_only_the_public_agent_api() -> None:
    for path in FIXTURE_DIRS:
        imports = [
            line.strip()
            for line in (path / "agent.py").read_text(encoding="utf-8").splitlines()
            if line.startswith(("import ", "from "))
        ]
        assert imports == ["from __future__ import annotations", "from battle_engine.agent_api import ("], path.name
        assert "random" not in (path / "agent.py").read_text(encoding="utf-8").replace("context.rng", "")
        assert len((path / "agent.py").read_text(encoding="utf-8").splitlines()) < 100


# ---------------------------------------------------------------------------
# Behaviour
# ---------------------------------------------------------------------------


def _run(root: Path, a: str, b: str, *, ruleset_id: str, seed: int, max_ticks: int, tag: str) -> Path:
    starts = resolve_direct_match_starts(
        ruleset_id=ruleset_id, arena_size=512, entrant_count=2, supplied_starts=[None, None], seed=seed
    )
    replay = root / "runs" / tag / f"{a}-{b}-{seed}" / "replay.jsonl"
    replay.parent.mkdir(parents=True)
    NativeMatchService().run(
        MatchRequest(
            config=Config(seed=seed, arena_size=512, instr_per_tick=8),
            entrants=(
                MatchEntrant.python("A", a, starts[0], resolve_agent(root, a)),
                MatchEntrant.python("B", b, starts[1], resolve_agent(root, b)),
            ),
            max_ticks=max_ticks,
            replay_path=replay,
            verbose=False,
            ruleset_id=ruleset_id,
        )
    )
    return replay


def _ticks(replay: Path) -> list[TickSnapshot]:
    return [record for record in iter_replay(replay) if isinstance(record, TickSnapshot)]


@pytest.fixture(scope="module")
def data_root(tmp_path_factory: pytest.TempPathFactory) -> Path:
    root = tmp_path_factory.mktemp("e2-fixtures")
    prepare_benchmark_data_root(root, [p.name for p in FIXTURE_DIRS])
    return root


@pytest.mark.parametrize("agent", matrix.E2_AGENTS)
def test_hd4_twin_plays_exactly_like_its_primary(data_root: Path, agent: str) -> None:
    kwargs = {"ruleset_id": BYTEFRAY_RULESET_V6_RESEARCH_CAPTURE_HOLD_K2_ID, "seed": 3, "max_ticks": 40}
    for opponent in ("e2_greedy_painter", "e2_spread_sniper"):
        primary = _ticks(_run(data_root, agent, opponent, tag="primary", **kwargs))
        twin = _ticks(_run(data_root, matrix.twin_of(agent), opponent, tag="twin", **kwargs))
        # Precondition: the match really ran past its opening.
        assert len(primary) >= 3
        assert twin == primary


def test_rng_agents_are_seed_deterministic_and_seed_sensitive(data_root: Path) -> None:
    kwargs = {"ruleset_id": BYTEFRAY_RULESET_V4_ID, "max_ticks": 5}
    first = _ticks(_run(data_root, "e2_spread_sniper", "e2_greedy_painter", seed=7, tag="rng1", **kwargs))
    again = _ticks(_run(data_root, "e2_spread_sniper", "e2_greedy_painter", seed=7, tag="rng2", **kwargs))
    other = _ticks(_run(data_root, "e2_spread_sniper", "e2_greedy_painter", seed=8, tag="rng3", **kwargs))
    assert first == again

    def spread(ticks: list[TickSnapshot]) -> list[int]:
        home = next(p.anchor for p in ticks[0].processes if p.entrant_id == "A")
        return sorted((p.anchor - home) % 512 for p in ticks[1].processes if p.entrant_id == "A")

    # Offsets from context.rng: magnitude 16..64, opposite signs, seed-dependent.
    offsets = spread(first)
    assert offsets[0] == 0 and 16 <= offsets[1] <= 64 and 512 - 64 <= offsets[2] <= 512 - 16
    assert spread(other) != offsets


@pytest.mark.parametrize("seed", [1, 2, 3, 42])
def test_v4_probe_reproduces_the_frozen_characterization_probe_tick_for_tick(
    data_root: Path, tmp_path: Path, seed: int
) -> None:
    for name in ("probe_alpha", "probe_beta"):
        _bootstrap_probe(tmp_path, name)
    kwargs = {"ruleset_id": BYTEFRAY_RULESET_V4_ID, "seed": seed, "max_ticks": 200}
    fixture = _ticks(_run(data_root, "v4_probe", "v4_probe_twin", tag=f"fixture{seed}", **kwargs))
    gate = _ticks(_run(tmp_path, "probe_alpha", "probe_beta", tag="gate", **kwargs))
    assert fixture == gate
    # The frozen V4 characterization: Seat A captures Seat B on tick 1.
    assert [t.tick for t in fixture] == [0, 1]
    assert [e.event_type for e in fixture[1].events] == ["kill"]
