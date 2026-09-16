from __future__ import annotations

"""V5 research Phase R3: research-agent construction, containment and legality.

R3's evidentiary standard is asymmetric: a positive result is strong
evidence that stable V4 mechanics can support combat-to-victory conversion,
so the construction that produces it has to be provably clean. These tests
establish, from real matches rather than by inspection:

* the research agents are unreachable from every product code path;
* the point-control clone plays a bit-for-bit identical match to the bundled
  ``v4_concentrated_attacker`` it was transcribed from, so the research
  agent directory and its resolution path change no gameplay;
* the sweeper differs from the baseline in address selection alone -- same
  API version, process id, declared reach and quota share;
* the sweeper never bypasses reach, never issues an invalid action, and
  never exceeds its ordinary per-tick action budget;
* the sweeper receives no privileged information: it runs under stable
  ``bytefray-rules-4`` with no oracle and no mortality, and every address it
  was ever shown was a genuine live enemy process anchor;
* the sweeper is deterministic.
"""

import json
from pathlib import Path

import pytest
from battle_engine.agents import agent_spec_from_dir, discover_agents
from battle_engine.config import Config
from battle_engine.match_service import MatchEntrant, MatchRequest, NativeMatchService
from battle_engine.placement import resolve_direct_match_starts
from battle_engine.ruleset_policy import BYTEFRAY_RULESET_V4_ID
from battle_engine.starters import STARTER_AGENT_NAMES

from tools.research.v5.r3_runner import (
    RESEARCH_AGENTS_DIR,
    load_research_agent_specs,
    replay_digests,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RESEARCH_AGENT_NAMES = (
    "v5r3_point_control",
    "v5r3_region_sweeper",
    "v5r3_region_sweeper_mobile",
)
BASELINE_ATTACKER = "v4_concentrated_attacker"
OPPONENT = "v4_local_defender"
ARENA_SIZE = 512
SEED = 1


def _run(
    tmp_path: Path,
    agent_a: str,
    agent_b: str,
    label: str,
    *,
    max_ticks: int = 60,
    with_trace: bool = False,
) -> tuple[Path, Path | None]:
    """Run one stable-V4 match, resolving research agents out of tools/."""

    research = load_research_agent_specs()

    def spec(name: str):
        if name in research:
            return research[name]
        resolved = agent_spec_from_dir(REPO_ROOT / "agents" / name)
        assert resolved is not None, name
        return resolved

    starts = resolve_direct_match_starts(
        ruleset_id=BYTEFRAY_RULESET_V4_ID,
        arena_size=ARENA_SIZE,
        entrant_count=2,
        supplied_starts=[None, None],
        seed=SEED,
    )
    entrants = (
        MatchEntrant.python("A", agent_a, starts[0], spec(agent_a)),
        MatchEntrant.python("B", agent_b, starts[1], spec(agent_b)),
    )
    replay_path = tmp_path / label / "replay.jsonl"
    trace_path = (tmp_path / label / "trace.jsonl") if with_trace else None
    request = MatchRequest(
        config=Config(seed=SEED, arena_size=ARENA_SIZE, instr_per_tick=8),
        entrants=entrants,
        max_ticks=max_ticks,
        replay_path=replay_path,
        trace_path=trace_path,
        verbose=False,
        ruleset_id=BYTEFRAY_RULESET_V4_ID,
    )
    result = NativeMatchService().run(request)
    assert result.result_path is not None
    return replay_path, trace_path


def test_research_agents_are_not_reachable_from_any_product_path() -> None:
    """They must not be starters, and must not be in the shipped catalog."""

    catalog = discover_agents(REPO_ROOT)
    for name in RESEARCH_AGENT_NAMES:
        assert name not in STARTER_AGENT_NAMES
        assert name not in catalog
        assert not (REPO_ROOT / "agents" / name).exists()
        assert not (
            REPO_ROOT
            / "engine"
            / "src"
            / "battle_engine"
            / "data"
            / "starter_agents"
            / name
        ).exists()
        assert (RESEARCH_AGENTS_DIR / name / "agent.py").is_file()


def test_research_agents_resolve_only_through_the_research_loader() -> None:
    specs = load_research_agent_specs()
    assert set(specs) == set(RESEARCH_AGENT_NAMES)
    for name in RESEARCH_AGENT_NAMES:
        spec = specs[name]
        assert spec.kind == "python"
        assert spec.api_version == 2
        assert spec.dir.resolve() == (RESEARCH_AGENTS_DIR / name).resolve()


def test_point_control_clone_plays_an_identical_match_to_the_bundled_baseline(
    tmp_path: Path,
) -> None:
    """The paired-construction control.

    Same opponent, seed, slot order, arena and tick limit; only the agent in
    seat A differs, and only by its identity. Every gameplay tick record must
    be byte-identical -- so a sweeper-versus-baseline difference cannot be an
    artifact of the research directory, the alternate spec resolution path,
    or a transcription slip.
    """

    baseline_replay, _ = _run(tmp_path, BASELINE_ATTACKER, OPPONENT, "baseline")
    clone_replay, _ = _run(tmp_path, "v5r3_point_control", OPPONENT, "clone")

    baseline = replay_digests(baseline_replay)
    clone = replay_digests(clone_replay)
    assert baseline["tick_stream_sha256"] == clone["tick_stream_sha256"]
    # The whole-file digests differ only because the header and terminal
    # result records legitimately carry the agent's name and source hash.
    assert baseline["replay_sha256"] != clone["replay_sha256"]


def test_sweeper_preserves_the_baseline_process_declaration(tmp_path: Path) -> None:
    """Paired equivalence: process count, id, reach and share are unchanged.

    Read out of the replay the engine actually wrote, so this is what the
    match ran with, not what the source appears to say.
    """

    def declarations(replay_path: Path) -> list[dict[str, object]]:
        header = json.loads(replay_path.read_text(encoding="utf-8").splitlines()[0])
        entrant = next(e for e in header["entrants"] if e["agent_id"] == "A")
        return entrant["metadata"]["processes"]

    baseline_replay, _ = _run(tmp_path, BASELINE_ATTACKER, OPPONENT, "baseline", max_ticks=5)
    expected = declarations(baseline_replay)
    assert expected == [{"process_id": "attacker", "reach": 4, "share": 1.0}]

    for name in RESEARCH_AGENT_NAMES:
        replay_path, _ = _run(tmp_path, name, OPPONENT, f"decl_{name}", max_ticks=5)
        assert declarations(replay_path) == expected, name


@pytest.mark.parametrize(
    "agent", ["v5r3_region_sweeper", "v5r3_region_sweeper_mobile"]
)
def test_sweeper_never_bypasses_reach_or_wastes_an_action(
    tmp_path: Path, agent: str
) -> None:
    """Every sweep write is an ordinary legal in-reach V4 write.

    A write outside reach is silently discarded by the engine but still
    consumes the quota slot, so an implementation that "swept" by firing at
    unreachable offsets would both bypass nothing and quietly hand itself a
    weaker action budget than the baseline. Neither is allowed: the trace
    must show zero out-of-reach rejections and zero invalid actions.
    """

    _, trace_path = _run(
        tmp_path, agent, OPPONENT, "reach", max_ticks=200, with_trace=True
    )
    assert trace_path is not None
    statuses: dict[str, int] = {}
    actions_per_tick: dict[int, int] = {}
    for line in trace_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        if record.get("record_type") != "decision_v2" or record.get("agent_id") != "A":
            continue
        status = (record.get("applied_result") or {}).get("status", "NONE")
        statuses[status] = statuses.get(status, 0) + 1
        tick = (record.get("observation") or {}).get("current_tick")
        actions_per_tick[tick] = actions_per_tick.get(tick, 0) + 1

    assert statuses.get("REJECTED_OUT_OF_REACH", 0) == 0
    assert statuses.get("REJECTED_INVALID", 0) == 0
    assert statuses.get("EXCEPTION", 0) == 0
    assert statuses.get("APPLIED", 0) > 0
    # Ordinary Q=8 entrant quota, never exceeded.
    assert max(actions_per_tick.values()) <= 8


def test_sweeper_receives_only_ordinary_legal_v4_information(tmp_path: Path) -> None:
    """The legal-information boundary, proven from what the agent was handed.

    Under stable ``bytefray-rules-4`` the R2 objective oracle cannot be
    activated at all, so every address in the sweeper's target channel must
    be an address a live enemy process actually occupied at that tick. If an
    enemy core base had leaked in, it would appear here as an address no
    enemy process was standing on.
    """

    replay_path, trace_path = _run(
        tmp_path, "v5r3_region_sweeper", OPPONENT, "legality", max_ticks=120, with_trace=True
    )
    assert trace_path is not None

    header = json.loads(replay_path.read_text(encoding="utf-8").splitlines()[0])
    assert header["ruleset_id"] == BYTEFRAY_RULESET_V4_ID
    # No experimental key was recorded, so neither R1 mortality nor the R2
    # oracle was requested or resolved for this match.
    assert "process_integrity" not in header["reproducibility"]
    assert "objective_target_oracle" not in header["reproducibility"]

    enemy_anchors_by_tick: dict[int, set[int]] = {}
    for line in replay_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        if record.get("record_type") != "tick":
            continue
        enemy_anchors_by_tick[record["tick"]] = {
            process["anchor"]
            for process in record.get("processes", [])
            if process["entrant_id"] != "A"
        }

    shown = 0
    for line in trace_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        if record.get("record_type") != "decision_v2" or record.get("agent_id") != "A":
            continue
        observation = record.get("observation") or {}
        tick = observation.get("current_tick")
        for address in observation.get("visible_enemy_anchor_addresses", []):
            shown += 1
            # The enemy anchor may move within the tick, so accept the
            # end-of-tick position of either this tick or the one before it.
            candidates = enemy_anchors_by_tick.get(tick, set()) | enemy_anchors_by_tick.get(
                tick - 1, set()
            )
            assert address in candidates, (tick, address, candidates)
    assert shown > 0


def test_sweeper_is_deterministic(tmp_path: Path) -> None:
    """Identical inputs, identical replay -- bytes, not just outcome."""

    first, _ = _run(tmp_path / "a", "v5r3_region_sweeper", OPPONENT, "det", max_ticks=300)
    second, _ = _run(tmp_path / "b", "v5r3_region_sweeper", OPPONENT, "det", max_ticks=300)
    assert replay_digests(first)["tick_stream_sha256"] == (
        replay_digests(second)["tick_stream_sha256"]
    )

    first_m, _ = _run(
        tmp_path / "c", "v5r3_region_sweeper_mobile", OPPONENT, "det", max_ticks=300
    )
    second_m, _ = _run(
        tmp_path / "d", "v5r3_region_sweeper_mobile", OPPONENT, "det", max_ticks=300
    )
    assert replay_digests(first_m)["tick_stream_sha256"] == (
        replay_digests(second_m)["tick_stream_sha256"]
    )


def test_sweeper_actually_diversifies_addresses_versus_the_baseline(tmp_path: Path) -> None:
    """Guard against reporting a null produced by an inert instrument.

    The sweeper must write strictly more distinct addresses than the
    baseline in a matchup where both make contact; otherwise every
    downstream "no difference" result would be uninterpretable.
    """

    from tools.research.v5.analyzer import analyze_match

    baseline_replay, _ = _run(tmp_path, BASELINE_ATTACKER, OPPONENT, "b", max_ticks=300)
    sweeper_replay, _ = _run(tmp_path, "v5r3_region_sweeper", OPPONENT, "s", max_ticks=300)
    baseline = analyze_match(baseline_replay, baseline_replay.with_name("result.json"))
    sweeper = analyze_match(sweeper_replay, sweeper_replay.with_name("result.json"))

    assert baseline["unique_write_addresses"]["A"] == 1
    assert sweeper["unique_write_addresses"]["A"] == 9  # 2 * reach + 1
    assert (
        sweeper["unique_enemy_core_cells_targeted"]["A"]
        > baseline["unique_enemy_core_cells_targeted"]["A"]
    )
