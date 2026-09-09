from __future__ import annotations

"""V5 research Phase R4: research-population construction, containment, legality.

R4's conclusion is a population-level claim, so the population itself has to
be provably clean. These tests establish, from real deterministic matches
rather than by inspection:

* every R4 research agent is unreachable from every product code path;
* each declares exactly the process configuration R4's frozen manifest
  records, read back out of the match the engine actually ran;
* none bypasses reach, issues an invalid action, or exceeds the ordinary
  Q = 8 per-tick entrant budget;
* none receives privileged information: every match runs under stable
  ``bytefray-rules-4`` with neither R1 mortality nor the R2 oracle, and
  every address any of them was ever shown was a genuine live enemy anchor;
* each expresses the archetype it was admitted for -- region-write
  diversity for the attackers, own-core coverage for the defender,
  displacement for the mobile archetypes;
* all of them are deterministic.
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

from tools.research.v5.analyzer import analyze_match
from tools.research.v5.r4_population import (
    RESEARCH_AGENTS_DIR,
    load_research_agent_specs,
)

REPO_ROOT = Path(__file__).resolve().parents[2]

#: The agents R4 authored. ``v4_quorum`` is a retained bundled agent and is
#: deliberately not in this tuple -- it must stay reachable from product
#: paths, and these containment assertions would be wrong for it.
R4_RESEARCH_AGENTS = (
    "v5r4_core_warden",
    "v5r4_dual_operator",
    "v5r4_recon_striker",
    "v5r4_siege_regional",
    "v5r4_territory_expander",
)

#: Frozen declarations, from R4's preregistered population manifest.
EXPECTED_DECLARATIONS = {
    "v5r4_siege_regional": [("siege", 24, 1.0)],
    "v5r4_recon_striker": [("striker", 40, 1.0)],
    "v5r4_core_warden": [("warden", 12, 1.0)],
    "v5r4_dual_operator": [("raider", 32, 0.5), ("keeper", 12, 0.5)],
    "v5r4_territory_expander": [("expander", 16, 1.0)],
}

ARENA_SIZE = 512
SEED = 3


def _spec(name: str):
    research = load_research_agent_specs()
    if name in research:
        return research[name]
    resolved = agent_spec_from_dir(REPO_ROOT / "agents" / name)
    assert resolved is not None, name
    return resolved


def _run(
    tmp_path: Path,
    agent_a: str,
    agent_b: str,
    label: str,
    *,
    max_ticks: int = 120,
    seed: int = SEED,
    with_trace: bool = False,
) -> tuple[Path, Path, Path | None]:
    """Run one stable-V4 match, resolving research agents out of tools/."""

    starts = resolve_direct_match_starts(
        ruleset_id=BYTEFRAY_RULESET_V4_ID,
        arena_size=ARENA_SIZE,
        entrant_count=2,
        supplied_starts=[None, None],
        seed=seed,
    )
    entrants = (
        MatchEntrant.python("A", agent_a, starts[0], _spec(agent_a)),
        MatchEntrant.python("B", agent_b, starts[1], _spec(agent_b)),
    )
    replay_path = tmp_path / label / "replay.jsonl"
    trace_path = (tmp_path / label / "trace.jsonl") if with_trace else None
    request = MatchRequest(
        config=Config(seed=seed, arena_size=ARENA_SIZE, instr_per_tick=8),
        entrants=entrants,
        max_ticks=max_ticks,
        replay_path=replay_path,
        trace_path=trace_path,
        verbose=False,
        ruleset_id=BYTEFRAY_RULESET_V4_ID,
    )
    result = NativeMatchService().run(request)
    assert result.result_path is not None
    return replay_path, result.result_path, trace_path


def _decisions(trace_path: Path, agent_id: str = "A"):
    for line in trace_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        if record.get("record_type") == "decision_v2" and record.get("agent_id") == agent_id:
            yield record


def test_r4_research_agents_are_not_reachable_from_any_product_path() -> None:
    """Not starters, not in the catalog, not in the shipped starter tree."""

    catalog = discover_agents(REPO_ROOT)
    for name in R4_RESEARCH_AGENTS:
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


def test_r4_research_agents_resolve_only_through_the_research_loader() -> None:
    specs = load_research_agent_specs()
    for name in R4_RESEARCH_AGENTS:
        assert name in specs
        spec = specs[name]
        assert spec.kind == "python"
        assert spec.api_version == 2
        assert spec.dir.resolve() == (RESEARCH_AGENTS_DIR / name).resolve()


def test_canonical_v4_agents_are_untouched_by_r4() -> None:
    """R4 modified no bundled agent source; ``v4_quorum`` stays a product agent."""

    catalog = discover_agents(REPO_ROOT)
    assert "v4_quorum" in catalog
    assert (REPO_ROOT / "agents" / "v4_quorum" / "agent.py").is_file()


@pytest.mark.parametrize("agent", R4_RESEARCH_AGENTS)
def test_r4_agent_declares_its_frozen_process_configuration(
    tmp_path: Path, agent: str
) -> None:
    """Read the declaration back out of the replay the engine actually wrote."""

    replay_path, _, _ = _run(tmp_path, agent, "v4_quorum", f"decl_{agent}", max_ticks=6)
    first_tick = None
    for line in replay_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        if record.get("record_type") == "tick":
            first_tick = record
            break
    assert first_tick is not None
    declared = sorted(
        (p["process_id"], p["reach"])
        for p in first_tick["processes"]
        if p["entrant_id"] == "A"
    )
    expected = sorted((pid, reach) for pid, reach, _ in EXPECTED_DECLARATIONS[agent])
    assert declared == expected


@pytest.mark.parametrize("agent", R4_RESEARCH_AGENTS)
def test_r4_agent_never_bypasses_reach_or_exceeds_its_action_budget(
    tmp_path: Path, agent: str
) -> None:
    """Every action is an ordinary legal in-reach V4 action.

    An out-of-reach write is silently discarded by the engine but still
    consumes the quota slot, so an agent that "swept" by firing at
    unreachable addresses would bypass nothing while quietly weakening
    itself. Neither is allowed.
    """

    _, _, trace_path = _run(
        tmp_path, agent, "v4_quorum", f"reach_{agent}", max_ticks=200, with_trace=True
    )
    assert trace_path is not None
    statuses: dict[str, int] = {}
    actions_per_tick: dict[int, int] = {}
    kinds: set[str] = set()
    for record in _decisions(trace_path):
        status = (record.get("applied_result") or {}).get("status", "NONE")
        statuses[status] = statuses.get(status, 0) + 1
        tick = (record.get("observation") or {}).get("current_tick")
        actions_per_tick[tick] = actions_per_tick.get(tick, 0) + 1
        kind = (record.get("action") or {}).get("kind")
        if kind:
            kinds.add(kind)

    assert statuses.get("REJECTED_OUT_OF_REACH", 0) == 0
    assert statuses.get("REJECTED_INVALID", 0) == 0
    assert statuses.get("EXCEPTION", 0) == 0
    assert statuses.get("APPLIED", 0) > 0
    assert max(actions_per_tick.values()) <= 8
    assert kinds <= {"read", "write", "move"}


@pytest.mark.parametrize("agent", R4_RESEARCH_AGENTS)
def test_r4_agent_receives_only_ordinary_legal_v4_information(
    tmp_path: Path, agent: str
) -> None:
    """The legal-information boundary, proven from what the agent was handed.

    Under stable ``bytefray-rules-4`` the R2 objective oracle cannot be
    activated at all, so every address in the target channel must be one a
    live enemy process actually occupied. An injected enemy core base would
    show up here as an address no enemy process was ever standing on.
    """

    replay_path, _, trace_path = _run(
        tmp_path, agent, "v4_quorum", f"legal_{agent}", max_ticks=120, with_trace=True
    )
    assert trace_path is not None

    header = json.loads(replay_path.read_text(encoding="utf-8").splitlines()[0])
    assert header["ruleset_id"] == BYTEFRAY_RULESET_V4_ID
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

    allowed_fields = {
        "current_tick",
        "last_callback_tick",
        "previous_action_tick",
        "self_process_id",
        "self_anchor",
        "self_reach",
        "own_core_base",
        "own_core_size",
        "visible_enemy_anchor_addresses",
        "previous_action_applied",
        "previous_read_value",
        "previous_read_owner",
    }

    shown = 0
    for record in _decisions(trace_path):
        observation = record.get("observation") or {}
        assert set(observation) <= allowed_fields
        tick = observation.get("current_tick")
        for address in observation.get("visible_enemy_anchor_addresses", []):
            shown += 1
            candidates = enemy_anchors_by_tick.get(
                tick, set()
            ) | enemy_anchors_by_tick.get(tick - 1, set())
            assert address in candidates, (agent, tick, address, candidates)
    assert shown > 0


@pytest.mark.parametrize("agent", R4_RESEARCH_AGENTS)
def test_r4_agent_is_deterministic(tmp_path: Path, agent: str) -> None:
    """Identical inputs reproduce identical replay bytes, not just outcomes."""

    first, _, _ = _run(tmp_path, agent, "v4_quorum", f"det_a_{agent}", max_ticks=150)
    second, _, _ = _run(tmp_path, agent, "v4_quorum", f"det_b_{agent}", max_ticks=150)
    a = [
        line
        for line in first.read_text(encoding="utf-8").splitlines()
        if json.loads(line).get("record_type") == "tick"
    ]
    b = [
        line
        for line in second.read_text(encoding="utf-8").splitlines()
        if json.loads(line).get("record_type") == "tick"
    ]
    assert a == b
    assert a


def test_regional_attacker_covers_a_core_region_not_a_single_address(
    tmp_path: Path,
) -> None:
    """Archetype A's admission property: multi-cell simultaneous pressure.

    The bundled ``v4_concentrated_attacker`` writes one address forever
    (R3 Section J.1: ``unique_write_addresses == 1`` across 1000 ticks). The
    R4 regional attacker must reach a genuinely simultaneous multi-cell
    deficit, which is what capture actually requires.
    """

    replay_path, result_path, _ = _run(
        tmp_path,
        "v5r4_siege_regional",
        "v5r4_core_warden",
        "regional",
        max_ticks=200,
        seed=1,
    )
    analysis = analyze_match(replay_path, result_path)
    assert analysis["unique_enemy_core_cells_targeted"]["A"] >= 4
    assert analysis["unique_enemy_core_cells_damaged"]["A"] >= 4
    assert analysis["max_core_deficit"]["B"] >= 4


def test_core_warden_defends_more_than_two_addresses_of_its_own_core(
    tmp_path: Path,
) -> None:
    """Archetype C's admission property, and the R3 Section C.1 contrast.

    The bundled ``v4_local_defender`` writes exactly two addresses of its own
    core for a whole match because its patrol offset cycles ``1, 0`` under a
    declared reach of 2. An objective-capable defender must cover its actual
    objective region, and must keep doing so while an enemy stands next to
    it -- the first draft of this agent did not, and was rejected for it.
    """

    replay_path, result_path, _ = _run(
        tmp_path,
        "v5r4_core_warden",
        "v5r4_territory_expander",
        "warden",
        max_ticks=400,
        seed=2,
    )
    analysis = analyze_match(replay_path, result_path)
    assert analysis["distinct_own_core_cells_written"]["A"] > 2


def test_mobile_archetypes_actually_search(tmp_path: Path) -> None:
    """Archetypes B and E must move, not drift in place."""

    for agent in ("v5r4_recon_striker", "v5r4_territory_expander"):
        replay_path, result_path, _ = _run(
            tmp_path, agent, "v5r4_core_warden", f"move_{agent}", max_ticks=200, seed=4
        )
        analysis = analyze_match(replay_path, result_path)
        assert analysis["max_displacement_from_core"]["A"] > 32, agent
