"""The tracked V6 E3 research fixtures: ``e3_jam_sniper`` and its twin.

* Tracked, fingerprinted, Agent API v2, research-only, resolved from tracked
  sources only (never the ignored runtime ``agents/`` catalogue).
* The twin's ``agent.py`` is byte-identical; only the manifest identity differs.
* Behaviour is asserted from real canonical replays at seed 42 (outside the
  E3 matrix's seeds 1..32): the in-tick alternation of anchor hits and core
  writes and the continuing core cursor under the whole-tick parent, and --
  against a scripted, non-matrix victim -- that under ``disruption_slot_limit
  = 1`` its alternation is exactly the jam the G.4 bound is proved against.
"""

from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

import pytest
from battle_engine.agent_api import ActionKindV2, AgentAction
from battle_engine.agents import agent_spec_from_dir, discover_agents, resolve_agent
from battle_engine.config import Config
from battle_engine.match_service import MatchEntrant, MatchRequest, NativeMatchService
from battle_engine.placement import resolve_direct_match_starts
from battle_engine.replay import KillDeathEvent, TickSnapshot, iter_replay
from battle_engine.starters import STARTER_AGENT_NAMES, ensure_starter_agents

from tools.research.v6.e3 import entrants, matrix
from tools.research.v6.e3.d9_gate import run_hosted_match
from tools.research.v6.experiment_harness import (
    REPO_ROOT,
    STARTER_AGENT_SOURCE_DIR,
    TRACKED_BENCHMARK_SOURCE_DIRS,
    find_tracked_agent_source,
)

E3_DIR = entrants.E3_FIXTURE_SOURCE_DIR
JAM, TWIN = entrants.JAM_SNIPER, entrants.JAM_SNIPER_TWIN
E2_PARENT = matrix.condition("C-E2").ruleset_id
RS_PARENT = matrix.condition("C-RS").ruleset_id
SEED = 42
ARENA = matrix.ARENA_SIZE


def test_fixture_directory_holds_exactly_the_jam_sniper_and_its_twin() -> None:
    dirs = {p.name for p in E3_DIR.iterdir() if p.is_dir() and p.name != "__pycache__"}
    assert dirs == {JAM, TWIN} == set(entrants.E3_FIXTURES)
    for name in (JAM, TWIN):
        assert {p.name for p in (E3_DIR / name).iterdir() if p.name != "__pycache__"} == {"agent.py", "agent.yaml"}


def test_twin_is_byte_identical_apart_from_manifest_identity() -> None:
    assert (E3_DIR / TWIN / "agent.py").read_bytes() == (E3_DIR / JAM / "agent.py").read_bytes()
    primary = (E3_DIR / JAM / "agent.yaml").read_text(encoding="utf-8").splitlines()
    twin = (E3_DIR / TWIN / "agent.yaml").read_text(encoding="utf-8").splitlines()
    assert [a.split(":")[0] for a, b in zip(primary, twin, strict=True) if a != b] == ["name", "display"]
    specs = [agent_spec_from_dir(E3_DIR / name) for name in (JAM, TWIN)]
    assert [(s.name, s.kind, s.api_version) for s in specs] == [(JAM, "python", 2), (TWIN, "python", 2)]
    live = entrants.fingerprints([JAM, TWIN])
    assert live[JAM] != live[TWIN]


def test_fingerprints_are_frozen_and_every_matrix_entrant_resolves_from_tracked_sources() -> None:
    roster = sorted({name for f in matrix.FIELDS for name in f.agents})
    assert set(roster) == set(matrix.AGENT_FINGERPRINTS)
    assert entrants.fingerprints(roster) == {name: matrix.AGENT_FINGERPRINTS[name] for name in roster}
    for name in roster:
        source = entrants.find_agent_source(name)
        assert source is not None and source.is_relative_to(REPO_ROOT)
        assert not source.is_relative_to(REPO_ROOT / "agents")
    # E3 names exist only in the E3 directory; the frozen harness resolves none of them.
    for name in entrants.E3_FIXTURES:
        assert find_tracked_agent_source(name) is None
        assert not any((base / name).exists() for base in TRACKED_BENCHMARK_SOURCE_DIRS)
    readme = (E3_DIR / "README.md").read_text(encoding="utf-8")
    for name in entrants.E3_FIXTURES:
        assert f"`{name}`" in readme and matrix.AGENT_FINGERPRINTS[name] in readme


def test_fixtures_are_tracked_in_git() -> None:
    if not (REPO_ROOT / ".git").exists():
        pytest.skip("not a git checkout")
    tracked = subprocess.run(
        ["git", "ls-files", "--", "tools/research/v6/e3/fixtures/agents"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=True,
    ).stdout.split()
    assert sorted(tracked) == sorted(
        [f"tools/research/v6/e3/fixtures/agents/{n}/{f}" for n in (JAM, TWIN) for f in ("agent.py", "agent.yaml")]
        + ["tools/research/v6/e3/fixtures/agents/README.md"]
    )


def test_fixtures_are_research_only_and_import_only_the_public_agent_api(tmp_path: Path) -> None:
    names = set(entrants.E3_FIXTURES)
    assert not names & set(STARTER_AGENT_NAMES)
    assert not names & {p.name for p in STARTER_AGENT_SOURCE_DIR.iterdir()}
    ensure_starter_agents(data_root=tmp_path)
    assert not names & set(discover_agents(tmp_path))
    source = (E3_DIR / JAM / "agent.py").read_text(encoding="utf-8")
    imports = [line.strip() for line in source.splitlines() if line.startswith(("import ", "from "))]
    assert imports == ["from __future__ import annotations", "from battle_engine.agent_api import ("]
    assert "random" not in source and "rng" not in source


def test_prepare_data_root_seeds_e3_and_e2_fixtures_without_pycache(tmp_path: Path) -> None:
    root = entrants.prepare_data_root(tmp_path, [JAM, "e2_repair_guard", TWIN])
    for name in (JAM, TWIN, "e2_repair_guard"):
        assert resolve_agent(root, name).name == name
        assert not (root / "agents" / name / "__pycache__").exists()


# ---------------------------------------------------------------------------
# Behaviour (canonical replays)
# ---------------------------------------------------------------------------


def _run(root: Path, ruleset_id: str, seat_a: str, seat_b: str, *, max_ticks: int) -> tuple[Path, list[TickSnapshot]]:
    entrants.prepare_data_root(root, [seat_a, seat_b])
    starts = resolve_direct_match_starts(
        ruleset_id=ruleset_id, arena_size=ARENA, entrant_count=2, supplied_starts=[None, None], seed=SEED
    )
    assert starts == (485, 203)
    replay = root / "runs" / f"{seat_a}-{seat_b}" / "replay.jsonl"
    replay.parent.mkdir(parents=True)
    NativeMatchService().run(
        MatchRequest(
            config=Config(seed=SEED, arena_size=ARENA, instr_per_tick=8),
            entrants=(
                MatchEntrant.python("A", seat_a, starts[0], resolve_agent(root, seat_a)),
                MatchEntrant.python("B", seat_b, starts[1], resolve_agent(root, seat_b)),
            ),
            max_ticks=max_ticks,
            replay_path=replay,
            verbose=False,
            ruleset_id=ruleset_id,
        )
    )
    return replay, [r for r in iter_replay(replay) if isinstance(r, TickSnapshot) and r.tick > 0]


def _writes(snapshot: TickSnapshot) -> list[tuple[int, str | None]]:
    return [((d.address + o) % ARENA, d.owner) for d in snapshot.memory_diffs for o in range(d.length)]


def test_jam_sniper_alternates_hits_and_continuing_core_writes_under_the_whole_tick_parent(tmp_path: Path) -> None:
    _, ticks = _run(tmp_path, E2_PARENT, JAM, "e2_repair_guard", max_ticks=1000)
    # Tick 1 (A first): hit B's anchor (its core base, 203), write core offset
    # 1, hit, offset 2, ... -- four hits and four core writes; B is silenced
    # for the whole tick by the first hit.
    assert _writes(ticks[0]) == [(203, "A"), (204, "A"), (203, "A"), (205, "A"),
                                 (203, "A"), (206, "A"), (203, "A"), (207, "A")]
    assert {a.agent_id: a.cpu_used for a in ticks[0].agents} == {"A": 8, "B": 0}
    # Tick 2 (B first): B repairs twice, then A's hit silences it; A's core
    # cursor continues at offset 5 and wraps past offset 7 to offset 1.
    assert _writes(ticks[1]) == [(203, "B"), (204, "B"), (203, "A"), (208, "A"), (203, "A"), (209, "A"),
                                 (203, "A"), (210, "A"), (203, "A"), (204, "A")]
    # E2 K = 2: zero core at the end of ticks 2 and 3 -- captured at tick 3.
    assert [t.tick for t in ticks] == [1, 2, 3]
    assert [(e.victim, e.killer) for e in ticks[-1].events if isinstance(e, KillDeathEvent)] == [("B", "A")]


def test_twin_plays_identically_and_the_fixture_is_deterministic(tmp_path: Path) -> None:
    replay_a, ticks_a = _run(tmp_path / "a", RS_PARENT, JAM, "e2_disrupt_guard", max_ticks=50)
    _, ticks_b = _run(tmp_path / "b", RS_PARENT, TWIN, "e2_disrupt_guard", max_ticks=50)
    replay_c, _ = _run(tmp_path / "c", RS_PARENT, JAM, "e2_disrupt_guard", max_ticks=50)
    assert [_writes(t) for t in ticks_a] == [_writes(t) for t in ticks_b]
    assert hashlib.sha256(replay_a.read_bytes()).digest() == hashlib.sha256(replay_c.read_bytes()).digest()


def test_jam_mirror_infers_both_cores(tmp_path: Path) -> None:
    _, ticks = _run(tmp_path, E2_PARENT, JAM, TWIN, max_ticks=2)
    # Tick 1: A (first) hits B's anchor and writes B's core; B is silenced.
    assert _writes(ticks[0])[:2] == [(203, "A"), (204, "A")]
    # Tick 2: B (first) hits A's anchor (485) and writes A's core.
    assert _writes(ticks[1])[:2] == [(485, "B"), (486, "B")]


def test_under_slot_limited_disruption_the_alternation_is_the_g4_jam(tmp_path: Path) -> None:
    # The jam sniper against a scripted, non-matrix victim that only idles
    # (hosted by an E2 fixture whose executor is replaced): every jam hit
    # costs the victim exactly its next offer, so it executes exactly the G.4
    # minimum -- 4 as second mover, 5 as first.
    data_root = entrants.prepare_data_root(tmp_path / "env", [JAM, "e2_sniper"])
    replay = run_hosted_match(
        data_root, tmp_path / "match", ruleset_id=matrix.condition("T-E3").ruleset_id,
        seat_names={"A": JAM, "B": "e2_sniper"}, scripted_seat="B",
        brain=lambda _controller, _obs: AgentAction(ActionKindV2.READ, operand=0), seed=SEED, ticks=2,
    )
    ticks = [r for r in iter_replay(replay) if isinstance(r, TickSnapshot) and r.tick > 0]
    assert [{a.agent_id: a.cpu_used for a in t.agents} for t in ticks] == [{"A": 8, "B": 4}, {"A": 8, "B": 5}]
    # Tick 1: the jam sniper still alternates hit / core write.
    assert _writes(ticks[0]) == [(203, "A"), (204, "A"), (203, "A"), (205, "A"),
                                 (203, "A"), (206, "A"), (203, "A"), (207, "A")]
