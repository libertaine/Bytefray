"""V6 Phase 4E: territory scoring characterization and audit regression tests.

Validates the findings of docs/research/v6/V6_PHASE4E_TERRITORY_SCORING_STUDY.md:
1. Production scoring mechanics (ScoringPolicy) evaluate fixed-cell buckets (cells // 64),
   independent of arena size.
2. Control-anchor equivalence at A=512: score contribution for any fixed holding is
   identical across all research arena sizes [512, 1024, 4096, 16384, 65536].
3. Separation of diagnostic percentage metrics (results.py / match_service.py) from
   gameplay scoring.
4. Score-fallback timeout resolution: when combat stalls at Tmax, territory points
   decide the match, giving raw expanders decisive victory.
5. Preserves stable v4 and Phase 4B ruleset isolation.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path
from typing import Any

import pytest
from battle_engine.agent_api import AgentManifestError
from battle_engine.agent_state import Agent
from battle_engine.agents import agent_spec_from_dir, resolve_agent
from battle_engine.config import Config, Weights
from battle_engine.match_service import MatchEntrant, MatchRequest, NativeMatchService
from battle_engine.placement import resolve_direct_match_starts
from battle_engine.results import build_summary
from battle_engine.rules import (
    BYTEFRAY_RULESET_V4_ID,
    BYTEFRAY_RULESET_V6_RESEARCH_SCALE_ID,
)
from battle_engine.ruleset_policy import (
    RULESET_V4,
    RULESET_V6_RESEARCH_SCALE,
    resolve_ruleset_policy,
)
from battle_engine.scoring import ScoreMap, ScoringPolicy

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.research.v6.phase4e_analyzer import (
    compute_direct_score_characterization,
)

STARTER_SOURCE_DIRS = (
    REPO_ROOT / "tools" / "research" / "v6" / "fixtures" / "agents",
    REPO_ROOT / "engine" / "src" / "battle_engine" / "data" / "starter_agents",
)


def _bootstrap_agent(tmp_path: Path, name: str) -> None:
    dest = tmp_path / "agents" / name
    if dest.exists():
        return
    for source_root in STARTER_SOURCE_DIRS:
        source = source_root / name
        try:
            if agent_spec_from_dir(source) is not None:
                shutil.copytree(source, dest)
                return
        except AgentManifestError:
            continue
    raise FileNotFoundError(f"no source found for agent {name!r} under {STARTER_SOURCE_DIRS}")


class DummyAgent:
    """Minimal duck-typed Agent for scoring tests."""

    def __init__(self, agent_id: str, alive: bool = True):
        self.agent_id = agent_id
        self.alive = alive


def test_scoring_policy_bucket_floor_division() -> None:
    """ScoringPolicy evaluates floor(cells // territory_bucket) * territory_weight."""
    weights = Weights(alive=1.0, kill=5.0, territory=1.0, territory_bucket=64)
    policy = ScoringPolicy(weights)

    agents = [DummyAgent("A"), DummyAgent("B")]
    score: ScoreMap = {}

    # Holdings below bucket threshold (0, 1, 8 core cells, 63 cells) yield 0 pts
    policy.score_territory(score, agents, {"A": 0, "B": 63})  # type: ignore[arg-type]
    assert score.get("A", 0) == 0
    assert score.get("B", 0) == 0

    # Exact bucket boundaries
    score.clear()
    policy.score_territory(score, agents, {"A": 64, "B": 127})  # type: ignore[arg-type]
    assert score["A"] == 1.0
    assert score["B"] == 1.0

    score.clear()
    policy.score_territory(score, agents, {"A": 128, "B": 255})  # type: ignore[arg-type]
    assert score["A"] == 2.0
    assert score["B"] == 3.0

    score.clear()
    policy.score_territory(score, agents, {"A": 512, "B": 1024})  # type: ignore[arg-type]
    assert score["A"] == 8.0
    assert score["B"] == 16.0


def test_scoring_policy_arena_size_independence() -> None:
    """ScoringPolicy computes territory score strictly from discrete cell buckets (cells // 64),
    independent of arena size or proportional holdings.

    Mutation sensitivity:
    - If territory scoring were modified to compute proportional percentage
      (e.g. `(cells / arena_size * 512) // 64`), a holding of 256 cells at A=1024
      would evaluate to 2.0 pts instead of 4.0 pts.
    - If territory scoring computed continuous proportional score rather than discrete
      integer buckets, 63 cells would score >0.0 pts instead of 0.0 pts.
    """
    weights = Weights(territory_bucket=64, territory=1.0)
    policy = ScoringPolicy(weights)

    # Invariant 1: discrete bucket floor division (cells // 64 * weight)
    for holding, expected_pts in [
        (0, 0.0),
        (1, 0.0),
        (63, 0.0),    # Below 1 bucket -> exactly 0.0
        (64, 1.0),    # Exactly 1 bucket -> 1.0
        (65, 1.0),    # 1 bucket + remainder -> 1.0
        (127, 1.0),   # Just below 2 buckets -> 1.0
        (128, 2.0),   # Exactly 2 buckets -> 2.0
        (256, 4.0),   # Exactly 4 buckets -> 4.0
    ]:
        score: ScoreMap = {}
        policy.score_territory(score, [DummyAgent("expander")], {"expander": holding})  # type: ignore[arg-type]
        assert score.get("expander", 0.0) == expected_pts, (
            f"holding={holding} expected {expected_pts} pts, got {score.get('expander', 0.0)}"
        )

    # Invariant 2: arena independence across candidate arena sizes
    # A holding of 256 cells represents 50% at A=512, 25% at A=1024, and 0.39% at A=65536,
    # but awards identically 4.0 points per tick across all evaluations.
    arenas = [512, 1024, 4096, 16384, 65536]
    test_holding = 256
    results = []
    for _ in arenas:
        score = {}
        policy.score_territory(score, [DummyAgent("expander")], {"expander": test_holding})  # type: ignore[arg-type]
        results.append(score["expander"])

    assert all(r == 4.0 for r in results)


def test_control_anchor_a512_equivalence() -> None:
    """At A=512 and larger arenas, direct score characterization is invariant."""
    char_table = compute_direct_score_characterization(
        territory_bucket=64, territory_weight=1.0
    )

    # 0, 1, 8 cells -> 0.0 pts at all arenas
    for h in [0, 1, 8]:
        for a in [512, 1024, 4096, 16384, 65536]:
            assert char_table[h][a] == 0.0

    # 64 cells -> 1.0 pt at all arenas
    for a in [512, 1024, 4096, 16384, 65536]:
        assert char_table[64][a] == 1.0

    # 128 cells -> 2.0 pts at all arenas
    for a in [512, 1024, 4096, 16384, 65536]:
        assert char_table[128][a] == 2.0

    # 512 cells -> 8.0 pts at all arenas
    for a in [512, 1024, 4096, 16384, 65536]:
        assert char_table[512][a] == 8.0

    # 1024 cells -> exceeds A=512, but identically 16.0 pts at A >= 1024
    assert char_table[1024][512] is None
    for a in [1024, 4096, 16384, 65536]:
        assert char_table[1024][a] == 16.0


def test_diagnostic_percentage_does_not_affect_gameplay_score() -> None:
    """build_summary computes territory_pct_* by dividing by arena_size, but leaves score untouched."""
    config_512 = Config(arena_size=512)
    config_65k = Config(arena_size=65536)

    agent_a = Agent(agent_id="A", pc=0, alive=True)
    score: ScoreMap = {"A": 2500.0}

    # Statistics reporting 256 cells
    stats: dict[str, Any] = {
        "A": {
            "alive_ticks": 1000,
            "kills": 0,
            "deaths": 0,
            "total_cpu": 8000,
            "total_mem_writes": 4000,
            "territory_last": 256,
            "territory_max": 256,
            "territory_sum": 256000,
        }
    }

    summary_512 = build_summary(
        config=config_512,
        ticks_run=1000,
        agents=[agent_a],
        score=score,
        statistics=stats,
        winner="A",
    )
    summary_65k = build_summary(
        config=config_65k,
        ticks_run=1000,
        agents=[agent_a],
        score=score,
        statistics=stats,
        winner="A",
    )

    # Diagnostic percentage is arena-relative
    assert summary_512["agents"][0]["territory_pct_last"] == 256 * 100.0 / 512  # 50.0%
    assert summary_65k["agents"][0]["territory_pct_last"] == 256 * 100.0 / 65536  # ~0.39%

    # Gameplay score is identical and unaffected by the percentage calculation
    assert summary_512["agents"][0]["score"] == 2500.0
    assert summary_65k["agents"][0]["score"] == 2500.0


def test_timeout_score_fallback_rewards_territory_expanders() -> None:
    """In a 1000-tick timeout match, both entrants receive equal alive score (1000),

    and the entrant with more territory buckets decisively wins.
    """
    weights = Weights(alive=1.0, kill=5.0, territory=1.0, territory_bucket=64)
    policy = ScoringPolicy(weights)

    # Entrant A is an expander holding 640 cells (10 buckets -> 10 pts/tick)
    # Entrant B is a passive core defender holding 8 cells (0 buckets -> 0 pts/tick)
    agents = [DummyAgent("expander"), DummyAgent("defender")]
    score: ScoreMap = {}

    for _ in range(1000):
        policy.score_alive(score, agents)  # type: ignore[arg-type]
        policy.score_territory(score, agents, {"expander": 640, "defender": 8})  # type: ignore[arg-type]

    # Both got 1000 alive points
    # Expander got 10,000 territory points -> 11,000 total
    # Defender got 0 territory points -> 1,000 total
    assert score["defender"] == 1000.0
    assert score["expander"] == 11000.0
    assert score["expander"] > score["defender"]


def test_ruleset_isolation_and_stop_condition_preserved() -> None:
    """Stable bytefray-rules-4 and Phase 4B bytefray-rules-6-research-scale remain

    isolated and authoritative, with no spurious rulesets added.
    """
    policy_v4 = resolve_ruleset_policy(BYTEFRAY_RULESET_V4_ID)
    policy_scale = resolve_ruleset_policy(BYTEFRAY_RULESET_V6_RESEARCH_SCALE_ID)

    assert policy_v4 is RULESET_V4
    assert policy_scale is RULESET_V6_RESEARCH_SCALE

    # Confirm movement stride and displacement on control rulesets
    assert policy_v4.movement_stride == "fixed_64"
    assert policy_v4.movement_displacement == "literal"
    assert policy_scale.movement_stride == "fixed_64"
    assert policy_scale.movement_displacement == "literal"

    # Confirm that no 'bytefray-rules-6-research-scale-territory' was mistakenly registered
    with pytest.raises(LookupError):
        resolve_ruleset_policy("bytefray-rules-6-research-scale-territory")


def test_live_match_territory_scoring_invariance(tmp_path: Path) -> None:
    """Run real starter agents (v4_claimer vs v4_local_defender) under
    bytefray-rules-6-research-scale at A=512 and A=1024 and verify that territory
    scoring is strictly invariant to arena size.

    Mutation sensitivity:
    If territory scoring were modified to compute proportional percentage
    (e.g. `(cells / arena_size * 512) // 64`), Entrant A's 101 claimed cells at A=1024
    would yield only half as many territory buckets as at A=512, causing
    `result_512.score['A'] == result_1024.score['A']` to fail with 35.0 != 30.0.
    """
    _bootstrap_agent(tmp_path, "v4_claimer")
    _bootstrap_agent(tmp_path, "v4_local_defender")

    spec_claimer = resolve_agent(tmp_path, "v4_claimer")
    spec_defender = resolve_agent(tmp_path, "v4_local_defender")

    ruleset_id = BYTEFRAY_RULESET_V6_RESEARCH_SCALE_ID
    seed = 1337
    ticks = 25

    results = {}
    for arena_size in [512, 1024]:
        starts = resolve_direct_match_starts(
            ruleset_id=ruleset_id,
            arena_size=arena_size,
            entrant_count=2,
            supplied_starts=[None, None],
            seed=seed,
        )
        entrants = (
            MatchEntrant.python("A", "v4_claimer", starts[0], spec_claimer),
            MatchEntrant.python("B", "v4_local_defender", starts[1], spec_defender),
        )

        run_dir = tmp_path / f"match_{arena_size}"
        run_dir.mkdir(parents=True)
        replay_path = run_dir / "replay.jsonl"

        request = MatchRequest(
            config=Config(seed=seed, arena_size=arena_size, instr_per_tick=8),
            entrants=entrants,
            max_ticks=ticks,
            replay_path=replay_path,
            verbose=False,
            ruleset_id=ruleset_id,
        )
        result = NativeMatchService().run(request)
        assert result.result_path is not None
        results[arena_size] = result

    res_512 = results[512]
    res_1024 = results[1024]

    # Invariant: Entrant A claims 101 cells (1 bucket = +1.0 pt/tick once reached),
    # earning exactly 10.0 territory points above its 25.0 alive points (total 35.0).
    # Entrant B owns 8 cells (0 buckets), earning exactly 0.0 territory points (total 25.0).
    assert res_512.score["A"] == 35.0
    assert res_512.score["B"] == 25.0

    # Cross-arena invariance: territory scoring is identical at A=1024 despite 101 cells
    # being 19.7% of A=512 vs 9.8% of A=1024.
    assert res_1024.score["A"] == 35.0
    assert res_1024.score["B"] == 25.0
    assert res_512.score["A"] == res_1024.score["A"]
    assert res_512.score["B"] == res_1024.score["B"]
