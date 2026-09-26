"""V6 E6: the semantics of ``RulesetPolicy.detection_radius``.

docs/research/v6/V6_PRICED_SENSING_DESIGN_REVIEW.md Sec C,
docs/research/v6/V6_E6_PRICED_SENSING_PREREGISTRATION.md Sec 2 and
docs/research/v6/V6_E6_PRICED_SENSING_IMPLEMENTATION_PLAN.md Sec 4. What is
proven here:

* **Visibility** (PR Sec 2). Under a radius ``d`` an entrant senses an enemy
  anchor iff one of its eligible processes lies at circular distance
  ``<= min(reach, d)`` from it: inclusive at exactly ``d``, across the wrap,
  and never beyond a process's own declared reach. Under ``None`` the
  historical rule, distance ``<= reach``, is unchanged.
* **A pure restriction.** Over an enumerated grid of positions and reaches,
  what the treatment shows is a subset of what the parent shows.
* **Everything else unchanged.** A suppressed process does not sense, a dead
  entrant's anchors are not sensed, sensing stays entrant-wide, co-located
  enemies still collapse to one address, the observation format and
  ``self_reach`` are unchanged, and READ and WRITE still reach the full
  declared reach.
* **Validation in two layers.** The policy accepts ``None`` or an integer
  ``>= 1`` (``test_ruleset_v6_research_sensing.py``); a match requires
  ``2 * d < arena_size``, and a match that fails it stops before any
  entrant's code runs.
* **Initial invisibility, geometry only.** At A = 512, seeded placement puts
  the two cores at least 64 apart, so under ``d = 32`` no tick-0 anchor is
  visible to the other entrant. A placement call; no match is run.

Every scenario uses scripted test executors with explicit positions, never
an E6 family member, and no outcome is asserted.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path

import pytest
from battle_engine.agent_api import ActionKindV2, AgentAction, ObservationV2
from battle_engine.agents import resolve_agent
from battle_engine.config import Config
from battle_engine.match_service import MatchEntrant, MatchRequest, NativeMatchService
from battle_engine.placement import resolve_direct_match_starts
from battle_engine.process_runtime import (
    ProcessEntrantSpec,
    ProcessInstance,
    ProcessMatchController,
    ProcessRole,
    PythonEntrantInitializationError,
)
from battle_engine.ruleset_policy import (
    RULESET_V6_RESEARCH_DISRUPTION_SLOT1,
    RULESET_V6_RESEARCH_DISRUPTION_SLOT1_SENSING_R32,
    RULESET_V6_RESEARCH_SCALE,
    RULESET_V6_RESEARCH_SENSING_R32,
    RulesetPolicy,
)

ARENA = 512
QUOTA = 8
IDLE = AgentAction(ActionKindV2.READ, operand=0)
TREATMENTS = (RULESET_V6_RESEARCH_SENSING_R32, RULESET_V6_RESEARCH_DISRUPTION_SLOT1_SENSING_R32)
PARENTS = (RULESET_V6_RESEARCH_SCALE, RULESET_V6_RESEARCH_DISRUPTION_SLOT1)
PARENT = dict(zip(TREATMENTS, PARENTS, strict=True))
ALL = (*TREATMENTS, *PARENTS)

Executor = Callable[[ObservationV2, int], AgentAction]


def _ids(policy: RulesetPolicy) -> str:
    return policy.ruleset_id


def _idle(_obs: ObservationV2, _slot: int) -> AgentAction:
    return IDLE


def _process(pid: str, position: int | None, reach: int, share: int, act: Executor = _idle) -> ProcessInstance:
    return ProcessInstance(pid, ProcessRole.GENERALIST, initial_position=position, reach=reach,
                           quota_share=share, logic=lambda _obs, _state: IDLE, executor=act)


def _controller(policy: RulesetPolicy, entrants: list[tuple[str, int, list[ProcessInstance]]], *,
                ticks: int = 1, arena: int = ARENA) -> ProcessMatchController:
    specs = [ProcessEntrantSpec(agent_id=seat, name=f"seat-{seat}", processes=processes, start=start)
             for seat, start, processes in entrants]
    return ProcessMatchController(Config(seed=1, arena_size=arena, instr_per_tick=QUOTA), specs, ticks,
                                  ruleset_policy=policy)


def _dist(a: int, b: int, arena: int = ARENA) -> int:
    d = abs(a - b) % arena
    return min(d, arena - d)


def visible(policy: RulesetPolicy, observers: list[tuple[int, int]], enemies: list[int], *,
            suppressed: frozenset[int] = frozenset(), enemy_alive: bool = True, tick: int = 1) -> tuple[int, ...]:
    """What seat A senses: ``observers`` are A's (position, reach) processes,
    ``enemies`` the anchors of seat B's processes. ``suppressed`` indexes the
    observers disrupted at ``tick`` (with one suppressed offer left, so a
    slot-limited Ruleset treats them as suppressed too)."""

    a = [_process(f"a{i}", position, reach, QUOTA if i == 0 else 0) for i, (position, reach) in enumerate(observers)]
    b = [_process(f"b{i}", position, ARENA // 2, QUOTA if i == 0 else 0) for i, position in enumerate(enemies)]
    controller = _controller(policy, [("A", 0, a), ("B", 256, b)])
    for index in suppressed:
        a[index].disrupted_until_tick = tick + 1
        a[index].disruption_slots_left = 1
    controller._states_by_agent_id["B"].alive = enemy_alive
    return controller._visible_enemy_anchors(controller.entrant_specs[0], tick)


# ---------------------------------------------------------------------------
# Visibility
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("policy", TREATMENTS, ids=_ids)
def test_the_boundary_is_inclusive_at_exactly_d(policy: RulesetPolicy) -> None:
    for enemy in (132, 68):  # distance 32 on either side of 100
        assert visible(policy, [(100, 256)], [enemy]) == (enemy,)
    for enemy in (133, 67):  # distance 33
        assert visible(policy, [(100, 256)], [enemy]) == ()


@pytest.mark.parametrize("policy", TREATMENTS, ids=_ids)
def test_distance_is_circular_across_the_wrap(policy: RulesetPolicy) -> None:
    assert _dist(500, 20) == 32
    assert visible(policy, [(500, 256)], [20]) == (20,)
    assert visible(policy, [(20, 256)], [500]) == (500,)
    assert visible(policy, [(500, 256)], [21]) == ()
    assert visible(policy, [(21, 256)], [500]) == ()


@pytest.mark.parametrize("policy", TREATMENTS, ids=_ids)
def test_the_radius_is_min_of_reach_and_d(policy: RulesetPolicy) -> None:
    # A reach below d still bounds sensing ...
    assert visible(policy, [(100, 10)], [110]) == (110,)
    assert visible(policy, [(100, 10)], [111]) == ()
    # ... and d bounds a larger reach.
    assert visible(policy, [(100, 256)], [133]) == ()
    assert visible(policy, [(100, 32)], [132]) == (132,)
    assert visible(policy, [(100, 33)], [133]) == ()


@pytest.mark.parametrize("policy", PARENTS, ids=_ids)
def test_the_parents_keep_sensing_to_the_declared_reach(policy: RulesetPolicy) -> None:
    assert visible(policy, [(100, 256)], [300]) == (300,)  # distance 200
    assert visible(policy, [(100, 256)], [356]) == (356,)  # distance 256
    assert visible(policy, [(100, 10)], [111]) == ()


@pytest.mark.parametrize("policy", TREATMENTS, ids=_ids)
def test_the_treatment_is_a_pure_restriction_of_its_parent(policy: RulesetPolicy) -> None:
    # Every enemy address at once: one seat-B process on every cell.
    everywhere = list(range(ARENA))
    for observer in (0, 100, 255, 500):
        for reach in (1, 8, 16, 31, 32, 33, 64, 128, 255, 256, 511):
            treated = set(visible(policy, [(observer, reach)], everywhere))
            parent = set(visible(PARENT[policy], [(observer, reach)], everywhere))
            assert treated <= parent
            assert parent == {cell for cell in everywhere if _dist(observer, cell) <= reach}
            assert treated == {cell for cell in everywhere if _dist(observer, cell) <= min(reach, 32)}


@pytest.mark.parametrize("policy", ALL, ids=_ids)
def test_a_suppressed_process_does_not_sense(policy: RulesetPolicy) -> None:
    assert visible(policy, [(100, 256)], [110]) == (110,)
    assert visible(policy, [(100, 256)], [110], suppressed=frozenset({0})) == ()


@pytest.mark.parametrize("policy", ALL, ids=_ids)
def test_a_dead_entrants_anchors_are_not_sensed(policy: RulesetPolicy) -> None:
    assert visible(policy, [(100, 256)], [110], enemy_alive=False) == ()


@pytest.mark.parametrize("policy", TREATMENTS, ids=_ids)
def test_sensing_stays_entrant_wide(policy: RulesetPolicy) -> None:
    # Any eligible friendly process within min(reach, d) senses for the whole
    # entrant; a far or suppressed one contributes nothing.
    assert visible(policy, [(300, 256), (100, 256)], [120]) == (120,)
    assert visible(policy, [(300, 256), (100, 256)], [120], suppressed=frozenset({1})) == ()
    assert visible(policy, [(300, 256), (100, 256)], [120, 320]) == (120, 320)


@pytest.mark.parametrize("policy", ALL, ids=_ids)
def test_co_located_enemies_collapse_to_one_address(policy: RulesetPolicy) -> None:
    assert visible(policy, [(100, 256)], [120, 120, 120]) == (120,)


@pytest.mark.parametrize("policy", TREATMENTS, ids=_ids)
def test_the_observation_differs_from_the_parents_only_in_the_visible_set(policy: RulesetPolicy) -> None:
    # Cores 200 apart, both processes spawned on their core base: the parent
    # (reach 256) shows each entrant the other's anchor; the treatment shows
    # nothing, and every other observation field is identical -- including
    # self_reach, which stays the declared reach.
    def first_observations(ruleset: RulesetPolicy) -> dict[str, ObservationV2]:
        seen: dict[str, ObservationV2] = {}

        def recorder(seat: str) -> Executor:
            def act(obs: ObservationV2, _slot: int) -> AgentAction:
                seen.setdefault(seat, obs)
                return IDLE

            return act

        controller = _controller(ruleset, [("A", 100, [_process("a", None, 256, QUOTA, recorder("A"))]),
                                           ("B", 300, [_process("b", None, 256, QUOTA, recorder("B"))])])
        controller.run()
        return seen

    parent, treatment = first_observations(PARENT[policy]), first_observations(policy)
    assert (parent["A"].visible_enemy_anchor_addresses, parent["B"].visible_enemy_anchor_addresses) == ((300,), (100,))
    for seat in "AB":
        p, t = parent[seat], treatment[seat]
        assert t.visible_enemy_anchor_addresses == ()
        assert t.self_reach == p.self_reach == 256
        assert {**vars(t), "visible_enemy_anchor_addresses": None} == {**vars(p), "visible_enemy_anchor_addresses": None}


# ---------------------------------------------------------------------------
# Action reach is unaffected
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("policy", ALL, ids=_ids)
def test_read_and_write_still_reach_the_full_declared_reach(policy: RulesetPolicy) -> None:
    # A process at 100 with reach 200 READs and WRITEs cells exactly 200 away
    # (far beyond d = 32): both apply. A cell 201 away is out of its reach
    # under every Ruleset, exactly as before.
    script = iter([
        AgentAction(ActionKindV2.READ, operand=300),
        AgentAction(ActionKindV2.WRITE, operand=300, value=7),
        AgentAction(ActionKindV2.WRITE, operand=301, value=7),
        AgentAction(ActionKindV2.READ, operand=301),
    ])

    def act(_obs: ObservationV2, _slot: int) -> AgentAction:
        return next(script, IDLE)

    actor = _process("a", 100, 200, QUOTA, act)
    controller = _controller(policy, [("A", 100, [actor]), ("B", 400, [_process("b", 400, 256, QUOTA)])])
    controller.run()
    assert (_dist(100, 300), _dist(100, 301)) == (200, 201)
    assert 300 in actor.telemetry.addresses_read
    assert 300 in actor.telemetry.addresses_written
    assert (controller.vm.arena[300], controller.vm.writer[300]) == (7, "A")
    assert 301 not in actor.telemetry.addresses_written
    assert 301 not in actor.telemetry.addresses_read
    assert controller.vm.writer[301] != "A"


@pytest.mark.parametrize("policy", TREATMENTS, ids=_ids)
def test_an_unseen_enemy_anchor_can_still_be_written_and_disrupted(policy: RulesetPolicy) -> None:
    # Visibility is information only: a WRITE to an enemy anchor 200 away,
    # never sensed under the treatment, still lands and disrupts it.
    seen: list[tuple[int, ...]] = []

    def act(obs: ObservationV2, _slot: int) -> AgentAction:
        seen.append(obs.visible_enemy_anchor_addresses)
        return AgentAction(ActionKindV2.WRITE, operand=300, value=1)

    victim = _process("b", 300, 256, QUOTA)
    controller = _controller(policy, [("A", 100, [_process("a", 100, 256, QUOTA, act)]), ("B", 300, [victim])])
    controller.run()
    assert set(seen) == {()}
    assert victim.telemetry.disruption_hits_received >= 1


# ---------------------------------------------------------------------------
# Match-level validation: 2 * d < arena_size
# ---------------------------------------------------------------------------


def _policy(radius: int | None) -> RulesetPolicy:
    return RulesetPolicy(ruleset_id="test-only", scheduler_mode="chunked", scheduler_chunk_size=2,
                         scheduler_rotate_start=True, core_placement="seeded", process_selection="round_robin",
                         detection_radius=radius)


def _pair(arena: int) -> list[tuple[str, int, list[ProcessInstance]]]:
    return [("A", 0, [_process("a", None, 16, QUOTA)]), ("B", arena // 2, [_process("b", None, 16, QUOTA)])]


@pytest.mark.parametrize(("radius", "arena", "accepted"), [
    (256, 512, False), (255, 512, True), (32, 64, False), (32, 65, True), (32, 512, True), (1, 2, False),
    (1, 3, True), (None, 2, True),
])
def test_a_match_requires_twice_the_radius_below_the_arena(radius: int | None, arena: int, accepted: bool) -> None:
    if accepted:
        _controller(_policy(radius), _pair(arena), arena=arena)
    else:
        with pytest.raises(ValueError, match=f"requires arena_size > {2 * (radius or 0)}; received {arena}"):
            _controller(_policy(radius), _pair(arena), arena=arena)


@pytest.mark.parametrize("policy", TREATMENTS, ids=_ids)
def test_the_registered_treatments_run_only_where_the_radius_fits(policy: RulesetPolicy) -> None:
    with pytest.raises(ValueError, match="detection_radius 32"):
        _controller(policy, _pair(64), arena=64)
    _controller(policy, _pair(65), arena=65)
    # The parents impose nothing.
    _controller(PARENT[policy], _pair(64), arena=64)


RAISING_RESET_AGENT = """\
from battle_engine.agent_api import ActionKindV2, AgentAction, ProcessDeclaration


class Agent:
    def reset(self, context):
        raise RuntimeError("reset ran")

    def declare_processes(self):
        return [ProcessDeclaration("p", 16, 1.0)]

    def act(self, observation):
        return AgentAction(ActionKindV2.READ, 0)


def create_agent():
    return Agent()
"""


def _write_agent(root: Path, name: str, source: str) -> None:
    agent_dir = root / "agents" / name
    agent_dir.mkdir(parents=True, exist_ok=True)
    (agent_dir / "agent.yaml").write_bytes(json.dumps({
        "name": name, "kind": "python", "api_version": 2, "entrypoint": "agent.py:create_agent", "version": "1.0.0",
    }).encode())
    (agent_dir / "agent.py").write_bytes(source.encode())


def test_an_invalid_match_fails_before_any_entrant_code_runs(tmp_path: Path) -> None:
    # Both entrants raise in reset(): had the check run after loading, the
    # diagnostic would be a reset failure. It is the configuration error.
    for name in ("raiser_a", "raiser_b"):
        _write_agent(tmp_path, name, RAISING_RESET_AGENT)
    entrants = tuple(MatchEntrant.python(seat, name, start, resolve_agent(tmp_path, name))
                     for seat, name, start in (("A", "raiser_a", 0), ("B", "raiser_b", 256)))
    with pytest.raises(PythonEntrantInitializationError) as excinfo:
        ProcessMatchController.from_python_entrants(Config(seed=1, arena_size=512, instr_per_tick=QUOTA), entrants,
                                                    5, ruleset_policy=_policy(256))
    diagnostic = excinfo.value.diagnostic
    assert (diagnostic.code, diagnostic.stage) == ("match_configuration_invalid", "configuration")
    assert "requires arena_size > 512; received 512" in diagnostic.message
    # The same entrants under a radius that fits reach reset() -- and fail there.
    with pytest.raises(PythonEntrantInitializationError) as excinfo:
        ProcessMatchController.from_python_entrants(Config(seed=1, arena_size=512, instr_per_tick=QUOTA), entrants,
                                                    5, ruleset_policy=_policy(255))
    assert excinfo.value.diagnostic.code != "match_configuration_invalid"


def test_a_registered_treatment_at_arena_64_leaves_no_replay(tmp_path: Path) -> None:
    for name in ("raiser_a", "raiser_b"):
        _write_agent(tmp_path, name, RAISING_RESET_AGENT)
    replay = tmp_path / "runs" / "a64" / "replay.jsonl"
    request = MatchRequest(
        config=Config(seed=1, arena_size=64, instr_per_tick=QUOTA),
        entrants=tuple(MatchEntrant.python(seat, name, start, resolve_agent(tmp_path, name))
                       for seat, name, start in (("A", "raiser_a", 0), ("B", "raiser_b", 32))),
        max_ticks=5, replay_path=replay, verbose=False, ruleset_id=RULESET_V6_RESEARCH_SENSING_R32.ruleset_id,
    )
    with pytest.raises(PythonEntrantInitializationError) as excinfo:
        NativeMatchService().run(request)
    assert excinfo.value.diagnostic.code == "match_configuration_invalid"
    assert not replay.exists()


# ---------------------------------------------------------------------------
# Initial invisibility, geometry only (PR D-2's premise)
# ---------------------------------------------------------------------------

GEOMETRY_SEEDS = (*range(2048), 2**31 - 1, 2**31, 2**32 + 7, 2**53 - 1, 9_007_199_254_740_000)


@pytest.mark.parametrize("policy", TREATMENTS, ids=_ids)
def test_seeded_cores_at_512_are_always_farther_apart_than_the_radius(policy: RulesetPolicy) -> None:
    # A pure placement call: the default spawn is the core base under both E6
    # Rulesets, so every tick-0 anchor sits on its core, and seeded placement
    # keeps the two cores >= 64 > 32 apart. No match is run.
    assert policy.initial_anchor_placement == "core_base"
    assert policy.detection_radius is not None
    closest = ARENA
    for seed in GEOMETRY_SEEDS:
        a, b = resolve_direct_match_starts(ruleset_id=policy.ruleset_id, arena_size=ARENA, entrant_count=2,
                                           supplied_starts=[None, None], seed=seed)
        assert (a, b) == resolve_direct_match_starts(ruleset_id=PARENT[policy].ruleset_id, arena_size=ARENA,
                                                     entrant_count=2, supplied_starts=[None, None], seed=seed)
        closest = min(closest, _dist(a, b))
    assert closest >= 64 > policy.detection_radius
