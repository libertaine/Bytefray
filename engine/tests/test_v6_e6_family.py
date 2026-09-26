"""V6 E6: the matched family -- packages, manifests, the D-5 discipline gate,
and every behavior of plan Sec 5.2 on synthetic observations.

docs/research/v6/V6_E6_PRICED_SENSING_IMPLEMENTATION_PLAN.md Sec 5 and
docs/research/v6/V6_E6_PRICED_SENSING_PREREGISTRATION.md Sec 3. The policy
object is driven with constructed ``ObservationV2`` sequences: no match is
played here. The only matches the family plays before authorization are the
control-Ruleset smoke tests at the end, which assert that no action is
invalid or forfeited and record no outcome.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import random
import shutil
import subprocess
from itertools import pairwise
from pathlib import Path
from types import MappingProxyType, ModuleType
from typing import Any

import pytest
from battle_engine.agent_api import ActionKindV2, AgentAction, MatchContextV2, ObservationV2
from battle_engine.agent_parameters import resolve_parameters
from battle_engine.agents import resolve_agent
from battle_engine.config import Config
from battle_engine.match_service import MatchEntrant, MatchRequest, NativeMatchService
from battle_engine.placement import resolve_direct_match_starts
from battle_engine.ruleset_policy import (
    BYTEFRAY_RULESET_V6_RESEARCH_DISRUPTION_SLOT1_ID,
    BYTEFRAY_RULESET_V6_RESEARCH_DISRUPTION_SLOT1_SENSING_R32_ID,
    BYTEFRAY_RULESET_V6_RESEARCH_SCALE_ID,
    BYTEFRAY_RULESET_V6_RESEARCH_SENSING_R32_ID,
)

from tools.research.v6.e6 import discipline
from tools.research.v6.e6.family import (
    FIXED_MEMBERS,
    FIXTURE_DIR,
    MEMBERS,
    OPPONENTS,
    PACKAGE_ID_SHUFFLE_SEED,
    PACKAGES,
    ROLES,
    manifest_text,
    package_id,
    prepare_data_root,
)

ARENA = 512
BASE = 100
BEACON = 0xCE
FINGERPRINTS = FIXTURE_DIR.parent.parent / "family_fingerprints.json"


def _load(pid: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(f"e6_family_policy_{pid}", FIXTURE_DIR / pid / "agent.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


POLICY = _load("e6_q01")


def _parameters(pid: str) -> dict[str, Any]:
    return resolve_parameters(resolve_agent(FIXTURE_DIR.parent, pid).parameter_schema)


def make(member: str, *, seat: str = "A", rng_seed: int = 0, module: ModuleType = POLICY,
         parameters: dict[str, Any] | None = None) -> Any:
    agent = module.create_agent()
    agent.reset(MatchContextV2(agent_id=seat, seed=0, arena_size=ARENA, tick_limit=1000, rng=random.Random(rng_seed),
                               parameters=MappingProxyType(dict(parameters or MEMBERS[member]))))
    return agent


def obs(tick: int, *, pid: str = "main", anchor: int = BASE, visible: tuple[int, ...] = (), applied: bool = True,
        value: int | None = None, owner: str | None = None) -> ObservationV2:
    return ObservationV2(current_tick=tick, last_callback_tick=0, previous_action_tick=0, self_process_id=pid,
                         self_anchor=anchor, self_reach=ARENA // 2, own_core_base=BASE, own_core_size=8,
                         visible_enemy_anchor_addresses=visible, previous_action_applied=applied,
                         previous_read_value=value, previous_read_owner=owner)


def hit(tick: int, **kwargs: Any) -> ObservationV2:
    return obs(tick, value=BEACON, owner="B", **kwargs)


def miss(tick: int, **kwargs: Any) -> ObservationV2:
    return obs(tick, value=0, owner=None, **kwargs)


def move(delta: int) -> AgentAction:
    return AgentAction(ActionKindV2.MOVE, operand=delta)


def read(address: int) -> AgentAction:
    return AgentAction(ActionKindV2.READ, operand=address % ARENA)


def write(address: int, value: int = 1) -> AgentAction:
    return AgentAction(ActionKindV2.WRITE, operand=address % ARENA, value=value)


def draws(rng_seed: int) -> tuple[int, int, int, int]:
    """The four reset draws, in their fixed order: direction, paint side, evade sign, evade magnitude."""
    rng = random.Random(rng_seed)
    return (-1, 1)[rng.randrange(2)], rng.randrange(2), (-1, 1)[rng.randrange(2)], rng.randint(8, 64)


def paint_sequence(side: int, count: int) -> list[int]:
    cells = []
    for k in range(count):
        pair, second = divmod(k, 2)
        up, down = BASE + 8 + pair, BASE - 1 - pair
        cells.append((up if (side == 0) != bool(second) else down) % ARENA)
    return cells


def seed_with(direction: int | None = None, side: int | None = None, sign: int | None = None) -> int:
    """The first rng seed whose reset draws have the requested values."""
    for candidate in range(10_000):
        d, s, e, _ = draws(candidate)
        if (direction in (None, d)) and (side in (None, s)) and (sign in (None, e)):
            return candidate
    raise AssertionError("no such seed")


# ---------------------------------------------------------------------------
# Packages, manifests and IDs
# ---------------------------------------------------------------------------


def test_the_family_is_the_registered_nine_members() -> None:
    assert OPPONENTS == ("RUSH", "PACED", "SPLIT", "STEALTH", "LURK", "GUARD", "EVADER", "GREED", "ADAPT")
    assert FIXED_MEMBERS == tuple(member for member in OPPONENTS if member != "ADAPT")
    assert {member: (v["search"], v["posture"], v["evade"], v["processes"]) for member, v in MEMBERS.items()
            if not v["adaptive"]} == {
        "RUSH": ("fast", "attack", False, 1),
        "PACED": ("paced", "attack", False, 1),
        "SPLIT": ("fast", "attack", False, 2),
        "STEALTH": ("read", "attack", False, 1),
        "LURK": ("none", "attack", False, 1),
        "GUARD": ("none", "guard", False, 1),
        "EVADER": ("none", "guard", True, 1),
        "GREED": ("none", "paint", False, 1),
    }
    assert [member for member, v in MEMBERS.items() if v["adaptive"]] == ["ADAPT"]


def test_package_ids_are_opaque_and_the_documented_shuffle() -> None:
    assert sorted(PACKAGES) == [f"e6_q{i:02d}" for i in range(1, 19)]
    slots = [(member, role) for member in OPPONENTS for role in ROLES]
    random.Random(PACKAGE_ID_SHUFFLE_SEED).shuffle(slots)
    assert dict(PACKAGES) == {f"e6_q{i:02d}": slot for i, slot in enumerate(slots, start=1)}
    assert sorted(PACKAGES.values()) == sorted((member, role) for member in OPPONENTS for role in ROLES)
    for member in OPPONENTS:
        assert package_id(member, "primary") != package_id(member, "twin")


def test_the_package_directories_are_exactly_the_eighteen() -> None:
    assert sorted(path.name for path in FIXTURE_DIR.iterdir()) == sorted(PACKAGES)
    for pid in PACKAGES:
        assert sorted(path.name for path in (FIXTURE_DIR / pid).iterdir() if path.name != "__pycache__") == [
            "agent.py", "agent.yaml"]


def test_every_package_shares_one_byte_identical_policy_source() -> None:
    sources = {(FIXTURE_DIR / pid / "agent.py").read_bytes() for pid in PACKAGES}
    assert len(sources) == 1
    (source,) = sources
    assert b"\r" not in source


@pytest.mark.parametrize("pid", sorted(PACKAGES))
def test_each_manifest_is_its_members_parameters_as_defaults(pid: str) -> None:
    member, _role = PACKAGES[pid]
    assert (FIXTURE_DIR / pid / "agent.yaml").read_text(encoding="utf-8") == manifest_text(pid)
    assert _parameters(pid) == dict(MEMBERS[member])


def test_family_fingerprints_are_recorded_and_current() -> None:
    recorded = json.loads(FINGERPRINTS.read_text(encoding="utf-8"))
    assert recorded == {
        pid: {
            "member": PACKAGES[pid][0],
            "role": PACKAGES[pid][1],
            "agent_py_sha256": hashlib.sha256((FIXTURE_DIR / pid / "agent.py").read_bytes()).hexdigest(),
            "agent_yaml_sha256": hashlib.sha256((FIXTURE_DIR / pid / "agent.yaml").read_bytes()).hexdigest(),
        }
        for pid in sorted(PACKAGES)
    }


def test_prepare_data_root_copies_packages_byte_for_byte(tmp_path: Path) -> None:
    prepare_data_root(tmp_path, ["e6_q03", "e6_q10"])
    for pid in ("e6_q03", "e6_q10"):
        for name in ("agent.py", "agent.yaml"):
            assert (tmp_path / "agents" / pid / name).read_bytes() == (FIXTURE_DIR / pid / name).read_bytes()
    with pytest.raises(KeyError):
        prepare_data_root(tmp_path, ["e2_sniper"])


# ---------------------------------------------------------------------------
# D-5: the static discipline gate
# ---------------------------------------------------------------------------


def test_every_package_passes_the_discipline_gate() -> None:
    assert discipline.check_packages(FIXTURE_DIR / pid for pid in PACKAGES) == {pid: [] for pid in sorted(PACKAGES)}
    assert discipline.passes(FIXTURE_DIR / pid for pid in PACKAGES)


PLANTED = {
    "imports placement": ("from battle_engine.placement import seeded_seat_starts\n", "import"),
    "imports it plainly": ("import battle_engine.placement\n", "import"),
    "imports python_runtime": ("from battle_engine.python_runtime import derive_agent_seed\n", "import"),
    "imports random": ("import random\n", "import"),
    "relative import": ("from . import helper\n", "import"),
    "reads context.seed": ("def reset(self, context):\n    self.s = context.seed\n", "attribute"),
    "calls open": ("def f():\n    return open('x')\n", "name"),
    "calls exec": ("exec('1')\n", "name"),
    "calls eval": ("eval('1')\n", "name"),
    "calls compile": ("compile('1', 'x', 'eval')\n", "name"),
    "calls __import__": ("__import__('os')\n", "name"),
    "calls globals": ("globals()\n", "name"),
    "contains a package id": ('ME = "e6_q03"\n', "package-id"),
    "package id in a comment": ("# I am e6_q11\n", "package-id"),
}


@pytest.mark.parametrize("name", sorted(PLANTED))
def test_the_gate_fails_every_planted_negative_control(name: str, tmp_path: Path) -> None:
    source, rule = PLANTED[name]
    found = discipline.violations(source)
    assert found and {violation.rule for violation in found} == {rule}
    package = tmp_path / "planted"
    package.mkdir()
    (package / "agent.py").write_text(
        (FIXTURE_DIR / "e6_q01" / "agent.py").read_text(encoding="utf-8") + "\n" + source, encoding="utf-8"
    )
    assert not discipline.passes([package])


def test_the_gate_accepts_the_whitelist() -> None:
    allowed = (
        "from __future__ import annotations\nimport math\nimport collections.abc\nfrom dataclasses import dataclass\n"
        "from typing import Any\nfrom enum import Enum\nimport itertools\nimport functools\n"
        "from battle_engine.agent_api import AgentAction\nx = context.rng.random()\n"
    )
    assert discipline.violations(allowed) == []


# ---------------------------------------------------------------------------
# Declarations and randomness
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("member", OPPONENTS)
def test_declarations(member: str) -> None:
    declared = [(d.id, d.reach, d.share) for d in make(member).declare_processes()]
    if member == "SPLIT":
        assert declared == [("sensor", 256, 0.25), ("striker", 256, 0.75)]
    else:
        assert declared == [("main", 256, 1.0)]


@pytest.mark.parametrize("rng_seed", [0, 1, 2, 3, 99, 12345])
def test_reset_draws_exactly_four_values_in_the_fixed_order(rng_seed: int) -> None:
    expected_state = random.Random(rng_seed)
    expected = ((-1, 1)[expected_state.randrange(2)], expected_state.randrange(2),
                (-1, 1)[expected_state.randrange(2)], expected_state.randint(8, 64))
    for member in OPPONENTS:
        rng = random.Random(rng_seed)
        agent = POLICY.create_agent()
        agent.reset(MatchContextV2(agent_id="A", seed=0, arena_size=ARENA, tick_limit=1000, rng=rng,
                                   parameters=MappingProxyType(dict(MEMBERS[member]))))
        assert (agent.direction, agent.paint_side, agent.evade_sign, agent.evade_magnitude) == expected
        assert rng.getstate() == expected_state.getstate()  # nothing else was drawn


def _script(agent: Any, observations: list[ObservationV2]) -> list[AgentAction]:
    return [agent.act(observation) for observation in observations]


QUIET = [obs(tick) for tick in range(1, 4) for _ in range(8)]


@pytest.mark.parametrize("member", OPPONENTS)
def test_the_same_seat_seed_and_script_gives_the_same_actions(member: str) -> None:
    assert _script(make(member, rng_seed=5), QUIET) == _script(make(member, rng_seed=5), QUIET)


@pytest.mark.parametrize("member", OPPONENTS)
def test_primary_and_twin_packages_behave_identically(member: str) -> None:
    primary, twin = package_id(member, "primary"), package_id(member, "twin")
    runs = []
    for pid in (primary, twin):
        agent = make(member, rng_seed=3, module=_load(pid), parameters=_parameters(pid))
        pids = ["sensor", "striker"] if member == "SPLIT" else ["main"]
        script = [obs(tick, pid=pids[i % len(pids)], visible=(300,) if tick >= 3 else ())
                  for tick in range(1, 6) for i in range(8)]
        runs.append(_script(agent, script))
    assert runs[0] == runs[1]


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("direction", [-1, 1])
def test_fast_search_moves_a_full_stride_in_the_drawn_direction_every_callback(direction: int) -> None:
    agent = make("RUSH", rng_seed=seed_with(direction=direction))
    assert _script(agent, [obs(tick) for tick in (1, 2) for _ in range(8)]) == [move(64 * direction)] * 16


@pytest.mark.parametrize("side", [0, 1])
def test_paced_search_moves_only_on_odd_callback_indexes(side: int) -> None:
    rng_seed = seed_with(direction=1, side=side)
    agent = make("PACED", rng_seed=rng_seed)
    actions = _script(agent, [obs(tick) for tick in (1, 2) for _ in range(8)])
    paint = paint_sequence(side, 8)
    expected: list[AgentAction] = []
    for _tick in (1, 2):
        for index in range(1, 9):
            expected.append(move(64) if index % 2 == 1 else write(paint.pop(0)))
    assert actions == expected
    # The index restarts with the tick, even after an odd number of callbacks.
    agent = make("PACED", rng_seed=rng_seed)
    assert _script(agent, [obs(1), obs(1), obs(1), obs(2)]) == [move(64), write(paint_sequence(side, 1)[0]),
                                                              move(64), move(64)]


@pytest.mark.parametrize("direction", [-1, 1])
def test_read_search_probes_the_whole_allowed_arc_in_order_and_never_moves(direction: int) -> None:
    agent = make("STEALTH", rng_seed=seed_with(direction=direction))
    expected = [read(BASE + direction * (64 + 8 * m)) for m in range(49)] + [read(BASE + direction * 64)]
    actions = [agent.act(miss(1 + i // 8)) for i in range(50)]
    assert actions == expected
    assert {(BASE + direction * (64 + 8 * m)) % ARENA for m in range(49)} == {
        (BASE + direction * offset) % ARENA for offset in range(64, 449, 8)}


def test_a_read_search_hit_is_grown_into_an_eight_cell_run_then_attacked() -> None:
    agent = make("STEALTH", rng_seed=seed_with(direction=1))
    assert agent.act(miss(1)) == read(164)
    assert agent.act(miss(1)) == read(172)      # 164 missed
    assert agent.act(hit(1)) == read(171)       # 172 hit: the run grows down from it
    for address in (170, 169, 168, 167):
        assert agent.act(hit(1)) == read(address)
    assert agent.act(miss(1)) == read(173)      # 167 missed: the run grows up
    assert agent.act(hit(2)) == read(174)
    assert agent.act(hit(2)) == read(175)
    assert agent.act(hit(2)) == write(168)      # 175 hit: eight beacons 168..175, base 168
    assert agent.enemy_core == 168


def test_search_never_runs_once_anything_is_known() -> None:
    agent = make("RUSH", rng_seed=seed_with(direction=1))
    assert agent.act(obs(1)) == move(64)
    assert agent.act(obs(1, visible=(300,))) == write(300)
    # The anchor is gone from view but remembered: verification, not search.
    assert agent.act(obs(1)) == read(301)


@pytest.mark.parametrize("member", ["LURK", "GUARD", "EVADER", "GREED"])
def test_members_without_search_never_move_to_search(member: str) -> None:
    agent = make(member, rng_seed=seed_with(direction=1))
    actions = _script(agent, QUIET)
    moves = [action for action in actions if action.kind is ActionKindV2.MOVE]
    assert len(moves) == (1 if member == "EVADER" else 0)


# ---------------------------------------------------------------------------
# Core inference
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("anchor", [BASE + 64, BASE - 64, BASE + 256, (BASE + 300) % ARENA])
def test_a_single_far_anchor_at_the_first_callback_is_adopted_as_the_core(anchor: int) -> None:
    agent = make("LURK")
    actions = [agent.act(obs(1, visible=(anchor,))) for _ in range(8)]
    assert actions == [write(anchor + i) for i in range(8)]


@pytest.mark.parametrize("anchor", [BASE + 63, BASE - 63, BASE + 32, BASE + 1])
def test_an_anchor_closer_than_64_is_not_adopted(anchor: int) -> None:
    agent = make("LURK")
    assert agent.act(obs(1, visible=(anchor,))) == write(anchor)
    assert agent.act(obs(1, visible=(anchor,))) == read(anchor + 1)  # verification starts one past the anchor


def test_two_visible_addresses_are_not_adopted() -> None:
    agent = make("LURK")
    assert agent.act(obs(1, visible=(300, 400))) == write(300)
    assert agent.act(obs(1, visible=(300, 400))) == write(400)
    assert agent.act(obs(1, visible=(300, 400))) == read(301)


def test_adoption_happens_only_at_the_first_callback() -> None:
    agent = make("LURK")
    assert agent.act(obs(1)) == write(paint_sequence(agent.paint_side, 1)[0])
    assert agent.act(obs(1, visible=(300,))) == write(300)
    assert agent.act(obs(1, visible=(300,))) == read(301)


def test_verification_reads_outward_then_grows_the_run_down_and_up() -> None:
    # The anchor (300) is off the core (307..314), as after an evasion.
    agent = make("LURK")
    agent.act(obs(1))  # first callback: nothing visible
    seen = (300,)
    assert agent.act(obs(1, visible=seen)) == write(300)
    assert agent.act(obs(1, visible=seen)) == read(301)
    assert agent.act(miss(1, visible=seen)) == read(293)
    assert agent.act(miss(1, visible=seen)) == read(309)
    assert agent.act(hit(1, visible=seen)) == read(308)       # 309 hit: grow down
    assert agent.act(hit(1, visible=seen)) == read(307)
    assert agent.act(hit(1, visible=seen)) == read(306)
    assert agent.act(miss(2, visible=seen)) == write(300)     # new tick: the anchor first; 306 missed
    assert agent.act(obs(2, visible=seen)) == read(310)       # grow up
    for address in (311, 312, 313, 314):
        assert agent.act(hit(2, visible=seen)) == read(address)
    assert agent.act(hit(2, visible=seen)) == write(307)      # 314 hit: eight beacons, base 307
    assert agent.enemy_core == 307


def test_the_window_order_and_extent() -> None:
    agent = make("LURK")
    agent.act(obs(1))
    agent.act(obs(1, visible=(300,)))
    reads = [agent.act(miss(1 + i // 8)) for i in range(17)]
    expected = [301] + [a for step in range(8, 65, 8) for a in (301 - step, 301 + step)]
    assert reads == [read(a) for a in expected]


def test_eight_contiguous_beacons_confirm_the_core_at_once() -> None:
    agent = make("LURK")
    agent.act(obs(1))
    agent.act(obs(1, visible=(300,)))
    assert agent.act(obs(1)) == read(301)
    assert agent.act(hit(1)) == read(300)  # 301 hit: grow down
    for address in range(299, 293, -1):
        assert agent.act(hit(2)) == read(address)
    assert agent.act(hit(3)) == write(294)  # 294 is the eighth beacon: no further READ, base 294
    assert agent.enemy_core == 294


def test_an_exhausted_window_forgets_the_anchor_and_search_resumes() -> None:
    agent = make("RUSH", rng_seed=seed_with(direction=1))
    assert agent.act(obs(1)) == move(64)
    assert agent.act(obs(1, visible=(300,))) == write(300)
    for i in range(17):
        agent.act(miss(1 + i // 8))
    # The 17th probe missed too: the window is exhausted, so the anchor is
    # forgotten and the fast search resumes.
    assert agent.act(miss(4)) == move(64)
    assert agent.last_known is None


def test_own_or_unowned_beacons_are_not_hits() -> None:
    agent = make("LURK")
    agent.act(obs(1))
    agent.act(obs(1, visible=(300,)))
    assert agent.act(miss(1)) == read(301)
    assert agent.act(obs(1, value=BEACON, owner="A")) == read(293)
    assert agent.act(obs(1, value=BEACON, owner=None)) == read(309)
    assert agent.act(obs(1, value=BEACON, owner="B", applied=False)) == read(285)


# ---------------------------------------------------------------------------
# Postures
# ---------------------------------------------------------------------------


def test_attack_writes_each_visible_anchor_once_per_tick_then_the_core() -> None:
    agent = make("LURK")
    first = [agent.act(obs(1, visible=(300,))) for _ in range(8)]
    assert first == [write(300 + i) for i in range(8)]
    # Next tick: the anchor again, then the core again.
    assert agent.act(obs(2, visible=(300,))) == write(300)
    assert agent.act(obs(2, visible=(300,))) == write(301)


def test_attack_idles_by_painting_once_the_core_is_written_this_tick() -> None:
    agent = make("LURK")
    actions = [agent.act(obs(1, visible=(300,))) for _ in range(9)]
    assert actions[8] == write(paint_sequence(agent.paint_side, 1)[0])


def test_guard_disrupts_on_sight_and_otherwise_repairs_cyclically_across_ticks() -> None:
    agent = make("GUARD")
    assert [agent.act(obs(1)) for _ in range(5)] == [write(BASE + i, BEACON) for i in range(5)]
    assert agent.act(obs(1, visible=(200,))) == write(200)
    assert agent.act(obs(1, visible=(200,))) == write(BASE + 5, BEACON)
    assert [agent.act(obs(2)) for _ in range(4)] == [write(BASE + i, BEACON) for i in (6, 7, 0, 1)]


@pytest.mark.parametrize("side", [0, 1])
def test_paint_writes_outward_alternating_sides_from_the_drawn_side(side: int) -> None:
    agent = make("GREED", rng_seed=seed_with(side=side))
    actions = [agent.act(obs(1 + i // 8, visible=(300,))) for i in range(24)]
    assert actions == [write(cell) for cell in paint_sequence(side, 24)]


def test_paint_covers_every_non_core_cell_then_cycles() -> None:
    cells = paint_sequence(0, 504)
    assert len(set(cells)) == 504
    assert set(cells).isdisjoint({BASE + i for i in range(8)})
    agent = make("GREED", rng_seed=seed_with(side=0))
    actions = [agent.act(obs(1 + i // 8)) for i in range(505)]
    assert [a.operand for a in actions[:504]] == cells
    assert actions[504] == actions[0]


@pytest.mark.parametrize("sign", [-1, 1])
def test_evasion_moves_exactly_once_at_the_first_callback(sign: int) -> None:
    rng_seed = seed_with(sign=sign)
    agent = make("EVADER", rng_seed=rng_seed)
    magnitude = draws(rng_seed)[3]
    assert 8 <= magnitude <= 64
    actions = _script(agent, QUIET)
    assert actions[0] == move(sign * magnitude)
    assert all(action.kind is not ActionKindV2.MOVE for action in actions[1:])
    assert actions[1:5] == [write(BASE + i, BEACON) for i in range(4)]


def test_evade_magnitudes_span_eight_to_sixty_four() -> None:
    # The agent's own draws, not this file's helper: every magnitude in
    # [8, 64] occurs, and nothing outside it.
    assert {make("EVADER", rng_seed=seed).evade_magnitude for seed in range(3000)} == set(range(8, 65))


def test_split_roles_by_process_id() -> None:
    agent = make("SPLIT", rng_seed=seed_with(direction=-1))
    side = agent.paint_side
    # Nothing known: the sensor searches, the striker never moves.
    assert agent.act(obs(1, pid="sensor")) == move(-64)
    assert agent.act(obs(1, pid="striker")) == write(paint_sequence(side, 1)[0])
    # Contact: the sensor disrupts, the striker verifies and attacks.
    assert agent.act(obs(1, pid="sensor", visible=(300,))) == write(300)
    assert agent.act(obs(1, pid="striker", visible=(300,))) == read(301)
    assert agent.act(obs(1, pid="sensor", visible=(300,))) == write(paint_sequence(side, 2)[1])
    assert agent.act(hit(1, pid="striker", visible=(300,))) == read(300)


def test_a_remembered_anchor_alone_stops_the_search() -> None:
    # Out of sight, core unknown, no scan under way: only the memory of the
    # anchor keeps the sensor from searching (plan Sec 5.2: search runs only
    # when nothing is visible, nothing is remembered and the core is unknown).
    agent = make("SPLIT", rng_seed=seed_with(direction=1))
    assert agent.act(obs(1, pid="sensor")) == move(64)
    assert agent.act(obs(1, pid="sensor", visible=(300,))) == write(300)
    assert (agent.last_known, agent.enemy_core, agent.run_low) == ((300, 1), None, None)
    assert agent.act(obs(2, pid="sensor")) == write(paint_sequence(agent.paint_side, 1)[0])


# ---------------------------------------------------------------------------
# ADAPT (plan Sec 5.2's transition table, each at its exact tick)
# ---------------------------------------------------------------------------


def test_adapt_starts_painting_and_reads_one_own_core_cell_per_tick() -> None:
    agent = make("ADAPT", rng_seed=seed_with(side=0))
    for tick in range(1, 12):
        assert agent.act(obs(tick, value=BEACON, owner="A")) == read(BASE + (tick - 1) % 8)
        assert agent.act(obs(tick, value=BEACON, owner="A")).kind is ActionKindV2.WRITE  # paint
    assert agent.mode == "paint"


def test_adapt_guards_while_an_anchor_was_visible_within_eight_ticks() -> None:
    agent = make("ADAPT")
    agent.act(obs(1))
    agent.act(obs(1, value=BEACON, owner="A"))
    assert agent.act(obs(5, visible=(200,))) == read(BASE + 4)
    assert agent.act(obs(5, value=BEACON, owner="A")) == write(BASE, BEACON)  # guard: repair
    assert agent.mode == "guard"
    for tick in range(6, 13):
        agent.act(obs(tick))
        assert agent.act(obs(tick, value=BEACON, owner="A")).value == BEACON  # still guarding
    agent.act(obs(13))
    assert agent.act(obs(13, value=BEACON, owner="A")).value == 1  # tick 13 = 5 + 8: paint again
    assert agent.mode == "paint"


def test_adapt_evades_once_on_damage_then_guards_for_eight_ticks() -> None:
    rng_seed = seed_with(sign=1)
    agent = make("ADAPT", rng_seed=rng_seed)
    magnitude = draws(rng_seed)[3]
    assert agent.act(obs(3)) == read(BASE + 2)
    assert agent.act(obs(3, value=1, owner="B")) == move(magnitude)  # damage seen at tick 3
    assert agent.act(obs(3)) == write(BASE, BEACON)
    assert agent.act(obs(4)) == read(BASE + 3)
    assert agent.act(obs(4, value=1, owner="B")) == write(BASE + 1, BEACON)  # damage again: no second evade
    for tick in range(5, 12):
        agent.act(obs(tick))
        assert agent.act(obs(tick, value=BEACON, owner="A")).value == BEACON
    agent.act(obs(12))
    assert agent.act(obs(12, value=BEACON, owner="A")).value == 1  # 4 + 8


def test_adapt_switches_to_fast_search_and_attack_after_tick_sixteen_without_contact() -> None:
    agent = make("ADAPT", rng_seed=seed_with(direction=1))
    for tick in range(1, 17):
        assert agent.act(obs(tick, value=BEACON, owner="A")).kind is ActionKindV2.READ
        assert agent.act(obs(tick, value=BEACON, owner="A")).kind is ActionKindV2.WRITE
    assert agent.act(obs(17, value=BEACON, owner="A")) == move(64)
    assert agent.mode == "hunt"
    # Permanent: contact later does not bring back paint or guard.
    assert agent.act(obs(18, visible=(300,))) == write(300)
    assert agent.act(obs(40)) == read(301)
    assert agent.mode == "hunt"


def test_adapt_does_not_switch_after_an_information_event() -> None:
    agent = make("ADAPT")
    agent.act(obs(1))
    agent.act(obs(1, visible=(300,), value=BEACON, owner="A"))  # an own, undamaged cell
    assert agent.last_damage_tick is None
    for tick in range(2, 30):
        assert agent.act(obs(tick, value=BEACON, owner="A")).kind is ActionKindV2.READ
        agent.act(obs(tick, value=BEACON, owner="A"))
    assert agent.mode == "paint"


def test_adapt_does_not_switch_after_damage() -> None:
    agent = make("ADAPT")
    agent.act(obs(2))
    agent.act(obs(2, value=1, owner="B"))
    for tick in range(3, 30):
        assert agent.act(obs(tick, value=BEACON, owner="A")).kind is ActionKindV2.READ
        agent.act(obs(tick, value=BEACON, owner="A"))
    assert agent.mode == "paint"


# ---------------------------------------------------------------------------
# Control-Ruleset smoke tests: no invalid action, no forfeit, no outcome
# ---------------------------------------------------------------------------

IDLE_OPPONENT = """\
from battle_engine.agent_api import ActionKindV2, AgentAction, ProcessDeclaration


class Agent:
    def reset(self, context):
        self.base = None

    def declare_processes(self):
        return [ProcessDeclaration("p", 16, 1.0)]

    def act(self, observation):
        return AgentAction(ActionKindV2.READ, observation.own_core_base)


def create_agent():
    return Agent()
"""


@pytest.mark.parametrize("ruleset_id", [BYTEFRAY_RULESET_V6_RESEARCH_SCALE_ID, BYTEFRAY_RULESET_V6_RESEARCH_DISRUPTION_SLOT1_ID])
@pytest.mark.parametrize("member", OPPONENTS)
def test_control_smoke_every_member_acts_legally(tmp_path: Path, ruleset_id: str, member: str) -> None:
    pid = package_id(member)
    prepare_data_root(tmp_path, [pid])
    opponent = tmp_path / "agents" / "idle_opponent"
    opponent.mkdir(parents=True)
    (opponent / "agent.yaml").write_text(json.dumps({"name": "idle_opponent", "kind": "python", "api_version": 2,
                                                     "entrypoint": "agent.py:create_agent", "version": "1.0.0"}))
    (opponent / "agent.py").write_text(IDLE_OPPONENT)
    starts = resolve_direct_match_starts(ruleset_id=ruleset_id, arena_size=ARENA, entrant_count=2,
                                         supplied_starts=[None, None], seed=7)
    spec = resolve_agent(tmp_path, pid)
    trace = tmp_path / "trace.jsonl"
    NativeMatchService().run(MatchRequest(
        config=Config(seed=7, arena_size=ARENA, instr_per_tick=8),
        entrants=(MatchEntrant.python("A", pid, starts[0], spec, resolve_parameters(spec.parameter_schema)),
                  MatchEntrant.python("B", "idle_opponent", starts[1], resolve_agent(tmp_path, "idle_opponent"))),
        max_ticks=40, replay_path=tmp_path / "run" / "replay.jsonl", verbose=False, ruleset_id=ruleset_id,
        trace_path=trace))
    decisions = [json.loads(line) for line in trace.read_text(encoding="utf-8").splitlines()]
    family = [record for record in decisions if record.get("record_type") == "decision_v2" and record["agent_id"] == "A"]
    assert family
    assert {record["applied_result"]["status"] for record in family} == {"APPLIED"}
    assert all(record.get("diagnostic") is None for record in family)
    replay = (tmp_path / "run" / "replay.jsonl").read_text(encoding="utf-8")
    assert '"forfeit"' not in replay


# ---------------------------------------------------------------------------
# Amendment 1 (docs/research/v6/V6_E6_AMENDMENT_1_FAMILY_CORRECTIONS.md): the
# three pre-freeze corrections. Synthetic cases first; then the engine: the
# scheduler's first mover under every E6 Ruleset (scripted agents only), and
# the family against scripted, non-family opponents under the two controls
# only. These are behavior tests: no family member plays another, and no
# outcome is recorded.
# ---------------------------------------------------------------------------

SEARCH_VARIANTS = ("RUSH", "PACED", "STEALTH", "LURK")  # the members CQ-1 compares [O-2]
FAR = (BASE + 200) % ARENA  # a stationary enemy core base, at least 64 from BASE


def beacon_of(owner: str, tick: int, **kwargs: Any) -> ObservationV2:
    """The previous READ returned an intact core beacon owned by ``owner``."""
    return obs(tick, value=BEACON, owner=owner, **kwargs)


def own_write(owner: str, tick: int, **kwargs: Any) -> ObservationV2:
    """The previous READ returned a cell holding ``owner``'s own write (a disruption or paint)."""
    return obs(tick, value=1, owner=owner, **kwargs)


# --- P-6: unverified adoption only by the first mover, on tick 1 ------------


@pytest.mark.parametrize("member", SEARCH_VARIANTS)
def test_seat_a_adopts_a_stationary_core_at_its_tick_one_first_callback(member: str) -> None:
    agent = make(member, seat="A")
    assert [agent.act(obs(1, visible=(FAR,))) for _ in range(8)] == [write(FAR + i) for i in range(8)]
    assert agent.enemy_core == FAR


@pytest.mark.parametrize("member", SEARCH_VARIANTS)
def test_seat_b_never_adopts_without_verification(member: str) -> None:
    agent = make(member, seat="B")
    assert agent.act(obs(1, visible=(FAR,))) == write(FAR)  # disruption, unchanged
    assert agent.act(obs(1, visible=(FAR,))) == read(FAR + 1)  # then verification, not the core
    assert agent.enemy_core is None


def test_seat_a_adopts_only_at_tick_one() -> None:
    # The engine never gives Seat A its first callback after tick 1; this
    # pins the tick clause on its own.
    agent = make("LURK", seat="A")
    assert agent.act(obs(2, visible=(FAR,))) == write(FAR)
    assert agent.act(obs(2, visible=(FAR,))) == read(FAR + 1)
    assert agent.enemy_core is None


def test_seat_b_does_not_adopt_an_evaders_moved_anchor() -> None:
    # EVADER (Seat A) moved its anchor 20 cells up before Seat B's first
    # callback: 220 from Seat B's core, so the unrefined rule would have
    # adopted it. Seat B verifies and finds the real core, FAR .. FAR + 7.
    moved = FAR + 20
    agent = make("LURK", seat="B")
    seen = (moved,)
    assert agent.act(obs(1, visible=seen)) == write(moved)
    assert agent.act(obs(1, visible=seen)) == read(moved + 1)
    assert agent.act(miss(1, visible=seen)) == read(moved - 7)
    assert agent.act(miss(1, visible=seen)) == read(moved + 9)
    assert agent.act(miss(1, visible=seen)) == read(moved - 15)  # FAR + 5
    assert agent.act(beacon_of("A", 1, visible=seen)) == read(FAR + 4)  # FAR + 5 hit: grow down
    for address in (FAR + 3, FAR + 2):
        assert agent.act(beacon_of("A", 1, visible=seen)) == read(address)
    assert agent.act(beacon_of("A", 2, visible=seen)) == write(moved)  # new tick: the anchor first
    assert agent.act(obs(2, visible=seen)) == read(FAR + 1)
    assert agent.act(beacon_of("A", 2, visible=seen)) == read(FAR)
    assert agent.act(beacon_of("A", 2, visible=seen)) == read(FAR - 1)
    assert agent.act(miss(2, visible=seen)) == read(FAR + 6)  # FAR - 1 missed: grow up
    assert agent.act(beacon_of("A", 2, visible=seen)) == read(FAR + 7)
    assert agent.act(beacon_of("A", 2, visible=seen)) == write(FAR)  # FAR + 7 hit: eight beacons, base FAR
    assert agent.enemy_core == FAR


@pytest.mark.parametrize("seat", ["A", "B"])
@pytest.mark.parametrize("offset", [-32, -8, 0, 1, 16, 32])
@pytest.mark.parametrize("member", SEARCH_VARIANTS)
def test_no_unverified_adoption_under_treatment_visibility(member: str, seat: str, offset: int) -> None:
    # Under T-E6 and T-E6L a first callback sees at most 32 cells from its
    # own anchor, which is still on its own core base: never 64 or more.
    anchor = (BASE + offset) % ARENA
    agent = make(member, seat=seat)
    assert agent.act(obs(1, visible=(anchor,))) == write(anchor)
    assert agent.act(obs(1, visible=(anchor,))) == read(anchor + 1)
    assert agent.enemy_core is None


# --- Verification: anchor + 1 sampling and eight-cell confirmation ---------


def test_an_overwritten_anchor_on_core_cell_0_stands_in_for_it() -> None:
    # The stationary case: the anchor (300) sits on core cell 0 of 300..307,
    # and this entrant's own disruption has overwritten it. Seven intact
    # beacons sit directly above the written anchor, so it stands in for the
    # eighth cell and is the base.
    agent = make("LURK", seat="B")
    seen = (300,)
    assert agent.act(obs(1, visible=seen)) == write(300)
    assert agent.act(obs(1, visible=seen)) == read(301)
    assert agent.act(beacon_of("A", 1, visible=seen)) == read(300)  # 301 hit: grow down
    assert agent.act(own_write("B", 1, visible=seen)) == read(302)  # 300 holds this entrant's write: grow up
    for address in (303, 304, 305, 306):
        assert agent.act(beacon_of("A", 1, visible=seen)) == read(address)
    assert agent.act(beacon_of("A", 2, visible=seen)) == write(300)  # new tick: the anchor first
    assert agent.act(obs(2, visible=seen)) == read(307)
    assert agent.act(beacon_of("A", 2, visible=seen)) == read(308)
    assert agent.act(miss(2, visible=seen)) == write(301)  # seven beacons over the written anchor: base 300
    assert agent.enemy_core == 300


def test_an_anchor_just_below_the_core_is_not_taken_for_core_cell_0() -> None:
    # The anchor (299) is one cell below the core (300..307), and this
    # entrant has overwritten it. Eight intact beacons exist without it, so
    # the base is 300, not the anchor.
    agent = make("LURK", seat="B")
    seen = (299,)
    assert agent.act(obs(1, visible=seen)) == write(299)
    assert agent.act(obs(1, visible=seen)) == read(300)
    assert agent.act(beacon_of("A", 1, visible=seen)) == read(299)  # 300 hit: grow down
    assert agent.act(own_write("B", 1, visible=seen)) == read(301)  # the written anchor: grow up
    for address in (302, 303, 304, 305):
        assert agent.act(beacon_of("A", 1, visible=seen)) == read(address)
    assert agent.act(beacon_of("A", 2, visible=seen)) == write(299)  # new tick: the anchor first
    assert agent.act(obs(2, visible=seen)) == read(306)
    assert agent.act(beacon_of("A", 2, visible=seen)) == read(307)
    assert agent.act(beacon_of("A", 2, visible=seen)) == write(300)  # 307 hit: eight beacons, base 300
    assert agent.enemy_core == 300


def test_a_repaired_core_cell_0_confirms_without_the_stand_in() -> None:
    # The defender has repaired core cell 0 since this entrant's disruption:
    # eight intact beacons, so no stand-in is needed.
    agent = make("LURK", seat="B")
    seen = (300,)
    assert agent.act(obs(1, visible=seen)) == write(300)
    assert agent.act(obs(1, visible=seen)) == read(301)
    assert agent.act(beacon_of("A", 1, visible=seen)) == read(300)
    assert agent.act(beacon_of("A", 1, visible=seen)) == read(299)  # 300 repaired: a beacon again
    assert agent.act(miss(1, visible=seen)) == read(302)  # 299 missed: grow up
    for address in (303, 304, 305):
        assert agent.act(beacon_of("A", 1, visible=seen)) == read(address)
    assert agent.act(beacon_of("A", 2, visible=seen)) == write(300)  # new tick: the anchor first
    assert agent.act(obs(2, visible=seen)) == read(306)
    assert agent.act(beacon_of("A", 2, visible=seen)) == read(307)
    assert agent.act(beacon_of("A", 2, visible=seen)) == write(301)  # eight beacons 300..307: base 300
    assert agent.enemy_core == 300


def test_seven_beacons_over_a_cell_that_is_not_a_written_anchor_stay_unconfirmed() -> None:
    # The anchor is at 292; 300, just below the seven beacons 301..307, holds
    # this entrant's own paint, not a disrupted anchor. No stand-in: the core
    # stays unconfirmed and the window goes on.
    agent = make("LURK", seat="B")
    seen = (292,)
    assert agent.act(obs(1, visible=seen)) == write(292)
    assert agent.act(obs(1, visible=seen)) == read(293)
    assert agent.act(miss(1, visible=seen)) == read(285)
    assert agent.act(miss(1, visible=seen)) == read(301)
    assert agent.act(beacon_of("A", 1, visible=seen)) == read(300)
    assert agent.act(own_write("B", 1, visible=seen)) == read(302)
    for address in (303, 304):
        assert agent.act(beacon_of("A", 1, visible=seen)) == read(address)
    assert agent.act(beacon_of("A", 2, visible=seen)) == write(292)
    for address in (305, 306, 307, 308):
        assert agent.act(beacon_of("A", 2, visible=seen)) == read(address)
    assert agent.act(miss(2, visible=seen)) == read(277)  # unconfirmed: the next window probe
    assert agent.enemy_core is None


@pytest.mark.parametrize("below", ["unowned", "not_applied"])
def test_seven_beacons_over_an_anchor_not_successfully_written_stay_unconfirmed(below: str) -> None:
    agent = make("LURK", seat="B")
    seen = (300,)
    result = miss(1, visible=seen) if below == "unowned" else own_write("B", 1, visible=seen, applied=False)
    assert agent.act(obs(1, visible=seen)) == write(300)
    assert agent.act(obs(1, visible=seen)) == read(301)
    assert agent.act(beacon_of("A", 1, visible=seen)) == read(300)
    assert agent.act(result) == read(302)
    for address in (303, 304, 305, 306):
        assert agent.act(beacon_of("A", 1, visible=seen)) == read(address)
    assert agent.act(beacon_of("A", 2, visible=seen)) == write(300)
    assert agent.act(obs(2, visible=seen)) == read(307)
    assert agent.act(beacon_of("A", 2, visible=seen)) == read(308)
    assert agent.act(miss(2, visible=seen)) == read(293)  # unconfirmed: the next window probe
    assert agent.enemy_core is None


def test_six_beacons_over_a_written_anchor_stay_unconfirmed() -> None:
    agent = make("LURK", seat="B")
    seen = (300,)
    assert agent.act(obs(1, visible=seen)) == write(300)
    assert agent.act(obs(1, visible=seen)) == read(301)
    assert agent.act(beacon_of("A", 1, visible=seen)) == read(300)
    assert agent.act(own_write("B", 1, visible=seen)) == read(302)
    for address in (303, 304, 305, 306):
        assert agent.act(beacon_of("A", 1, visible=seen)) == read(address)
    assert agent.act(beacon_of("A", 2, visible=seen)) == write(300)
    assert agent.act(obs(2, visible=seen)) == read(307)
    assert agent.act(own_write("B", 2, visible=seen)) == read(293)  # 307 is not a beacon: six, unconfirmed
    assert agent.enemy_core is None


def test_any_anchor_this_entrant_wrote_may_stand_in() -> None:
    # Two enemy anchors are visible, as when a treatment attacker sees both of
    # SPLIT's: the sensor (292, the lowest, so the last-known anchor) and the
    # striker on core cell 0 (300). The overwritten striker anchor stands in,
    # although it is not the last-known anchor.
    agent = make("LURK", seat="B")
    seen = (292, 300)
    assert agent.act(obs(1, visible=seen)) == write(292)
    assert agent.act(obs(1, visible=seen)) == write(300)
    assert agent.act(obs(1, visible=seen)) == read(293)
    assert agent.act(miss(1, visible=seen)) == read(285)
    assert agent.act(miss(1, visible=seen)) == read(301)
    assert agent.act(beacon_of("A", 1, visible=seen)) == read(300)
    assert agent.act(own_write("B", 1, visible=seen)) == read(302)
    assert agent.act(beacon_of("A", 1, visible=seen)) == read(303)
    assert agent.act(beacon_of("A", 2, visible=seen)) == write(292)
    assert agent.act(obs(2, visible=seen)) == write(300)
    for address in (304, 305, 306, 307, 308):
        assert agent.act(beacon_of("A", 2, visible=seen)) == read(address)
    assert agent.act(miss(2, visible=seen)) == write(301)  # seven over the written striker anchor: base 300
    assert (agent.enemy_core, agent.last_known) == (300, (292, 2))


# --- Attack: the cyclic core cursor ------------------------------------------


def test_the_core_cursor_rotates_the_omitted_cell_across_ticks() -> None:
    agent = make("LURK", seat="A")
    assert [agent.act(obs(1, visible=(FAR,))) for _ in range(8)] == [write(FAR + i) for i in range(8)]
    # Every core cell is written this tick: the idle action, and the cursor stays.
    assert agent.act(obs(1, visible=(FAR,))) == write(paint_sequence(agent.paint_side, 1)[0])
    assert agent.core_cursor == 0
    moved = FAR + 20  # the anchor is now off the core: disrupting it costs one of the eight offers
    omitted = []
    for tick in range(2, 10):
        actions = [agent.act(obs(tick, visible=(moved,))) for _ in range(8)]
        assert actions[0] == write(moved)
        cells = [action.operand - FAR for action in actions[1:]]
        assert len(set(cells)) == 7 and set(cells) <= set(range(8))  # seven distinct core cells
        (missing,) = set(range(8)) - set(cells)
        omitted.append(missing)
    assert omitted == [7, 6, 5, 4, 3, 2, 1, 0]  # the omitted cell rotates instead of starving cell 7


# --- The engine -------------------------------------------------------------

SCRIPTED = """\
from battle_engine.agent_api import ActionKindV2, AgentAction, ProcessDeclaration


class Agent:
    def reset(self, context):
        self.moved = False
        self.cursor = 0

    def declare_processes(self):
        return [ProcessDeclaration("p", 64, 1.0)]

    def act(self, observation):
        if not self.moved and DELTA:
            self.moved = True
            return AgentAction(ActionKindV2.MOVE, DELTA)
        if REPAIR:
            cell = observation.own_core_base + self.cursor
            self.cursor = (self.cursor + 1) % REPAIR
            return AgentAction(ActionKindV2.WRITE, cell, 0xCE)
        return AgentAction(ActionKindV2.READ, observation.own_core_base)


def create_agent():
    return Agent()
"""
#: Scripted, non-family opponents: (first-callback MOVE, or None for 20 cells
#: away from the other core; how many core cells it repairs cyclically).
STATIONARY, EVADING, BELOW, REPAIRING, EVADING_REPAIRING = (
    "stationary", "evading", "below", "repairing", "evading_repairing")
SCRIPTS: dict[str, tuple[int | None, int]] = {
    STATIONARY: (0, 0),
    EVADING: (None, 0),
    BELOW: (-1, 0),  # its anchor ends one cell below its core
    REPAIRING: (0, 1),  # rewrites core cell 0 on every callback
    EVADING_REPAIRING: (None, 8),  # evades, then repairs its whole core cyclically
}
V1_FAMILY_COMMIT = "bd3a3ff"  # analysis freeze v1: the family before amendment 1
REPO_ROOT = Path(__file__).resolve().parents[2]


def _scripted(root: Path, name: str, delta: int, repair: int) -> None:
    package = root / "agents" / name
    package.mkdir(parents=True, exist_ok=True)
    (package / "agent.yaml").write_text(json.dumps({"name": name, "kind": "python", "api_version": 2,
                                                    "entrypoint": "agent.py:create_agent", "version": "1.0.0"}))
    (package / "agent.py").write_text(f"DELTA = {delta}\nREPAIR = {repair}\n{SCRIPTED}")


def _circular(a: int, b: int) -> int:
    return min((a - b) % ARENA, (b - a) % ARENA)


def _starts(ruleset_id: str, seed: int = 7) -> tuple[int, int]:
    starts = resolve_direct_match_starts(ruleset_id=ruleset_id, arena_size=ARENA, entrant_count=2,
                                         supplied_starts=[None, None], seed=seed)
    return starts[0], starts[1]


def _evade_delta(starts: tuple[int, int], evader_seat: str) -> int:
    """A 20-cell evasion away from the other seat's core, so the moved anchor stays 64 or more from it."""
    own, other = (starts[0], starts[1]) if evader_seat == "A" else (starts[1], starts[0])
    return max((20, -20), key=lambda delta: _circular((own + delta) % ARENA, other))


def _play(root: Path, ruleset_id: str, entrants: dict[str, tuple[str, int, int]], *, seed: int = 7,
          ticks: int = 40, source: Path | None = None) -> tuple[list[dict[str, Any]], tuple[int, int]]:
    """One traced match: seat -> (family package or scripted name, MOVE, repair). Decisions in execution order.

    ``source`` replaces the live fixture directory for the family packages (the v1 comparison).
    """
    root.mkdir(parents=True, exist_ok=True)
    starts = _starts(ruleset_id, seed)
    seated = []
    for seat, start in zip(("A", "B"), starts, strict=True):
        name, delta, repair = entrants[seat]
        if name in PACKAGES:
            if source is None:
                prepare_data_root(root, [name])
            else:
                shutil.copytree(source / name, root / "agents" / name, dirs_exist_ok=True)
            spec = resolve_agent(root, name)
            seated.append(MatchEntrant.python(seat, name, start, spec, resolve_parameters(spec.parameter_schema)))
        else:
            _scripted(root, name, delta, repair)
            seated.append(MatchEntrant.python(seat, name, start, resolve_agent(root, name)))
    trace = root / "trace.jsonl"
    NativeMatchService().run(MatchRequest(
        config=Config(seed=seed, arena_size=ARENA, instr_per_tick=8), entrants=tuple(seated), max_ticks=ticks,
        replay_path=root / "run" / "replay.jsonl", verbose=False, ruleset_id=ruleset_id, trace_path=trace))
    records = [json.loads(line) for line in trace.read_text(encoding="utf-8").splitlines()]
    return [r for r in records if r.get("record_type") == "decision_v2"], starts


ALL_E6_RULESETS = (BYTEFRAY_RULESET_V6_RESEARCH_SCALE_ID, BYTEFRAY_RULESET_V6_RESEARCH_SENSING_R32_ID,
                   BYTEFRAY_RULESET_V6_RESEARCH_DISRUPTION_SLOT1_ID,
                   BYTEFRAY_RULESET_V6_RESEARCH_DISRUPTION_SLOT1_SENSING_R32_ID)
CONTROL_RULESETS = (BYTEFRAY_RULESET_V6_RESEARCH_SCALE_ID, BYTEFRAY_RULESET_V6_RESEARCH_DISRUPTION_SLOT1_ID)


@pytest.mark.parametrize("ruleset_id", ALL_E6_RULESETS)
def test_seat_a_is_the_first_mover_on_tick_one_under_every_e6_ruleset(tmp_path: Path, ruleset_id: str) -> None:
    # Scripted agents only. The rule's premise: Seat A takes the first two
    # actions of tick 1, before any Seat B callback, and tick 2 starts with B.
    decisions, _ = _play(tmp_path, ruleset_id, {"A": ("scripted_a", 0, 0), "B": ("scripted_b", 0, 0)}, ticks=2)
    order = [(r["observation"]["current_tick"], r["agent_id"]) for r in decisions]
    assert order[:4] == [(1, "A"), (1, "A"), (1, "B"), (1, "B")]
    assert order[16] == (2, "B")  # quota 8 per entrant: 16 callbacks a tick


def _mine(decisions: list[dict[str, Any]], seat: str) -> list[dict[str, Any]]:
    return [r for r in decisions if r["agent_id"] == seat]


def _writes(decisions: list[dict[str, Any]], seat: str, tick: int | None = None) -> list[int]:
    return [r["action"]["operand"] for r in _mine(decisions, seat) if r["action"]["kind"] == "write"
            and (tick is None or r["observation"]["current_tick"] == tick)]


def _first_actions(decisions: list[dict[str, Any]], seat: str, count: int) -> list[tuple[str, int]]:
    return [(r["action"]["kind"], r["action"]["operand"]) for r in _mine(decisions, seat)][:count]


def _read_results(decisions: list[dict[str, Any]], seat: str, address: int) -> list[tuple[Any, Any]]:
    return [(r["applied_result"]["read_value"], r["applied_result"]["read_owner"]) for r in _mine(decisions, seat)
            if r["action"]["kind"] == "read" and r["action"]["operand"] == address % ARENA]


def _core(base: int) -> list[int]:
    return [(base + i) % ARENA for i in range(8)]


def _no_core_write_before_confirmation(decisions: list[dict[str, Any]], seat: str, base: int) -> bool:
    """No cell of the enemy core but its anchor cell is written before a READ has seen an enemy beacon."""
    mine, rival = _mine(decisions, seat), "B" if seat == "A" else "A"
    seen = next((i for i, r in enumerate(mine) if r["action"]["kind"] == "read"
                 and (r["applied_result"]["read_value"], r["applied_result"]["read_owner"]) == (BEACON, rival)),
                len(mine))
    return not [r for r in mine[:seen] if r["action"]["kind"] == "write"
                and 0 < (r["action"]["operand"] - base) % ARENA < 8]


@pytest.fixture(scope="module")
def control_runs(tmp_path_factory: pytest.TempPathFactory) -> Any:
    """A family member (in ``seat``) against a scripted opponent under a control; cached per module."""
    cache: dict[tuple[str, str, str, str, str], tuple[list[dict[str, Any]], tuple[int, int]]] = {}
    v1_source: list[Path] = []

    def v1_fixture() -> Path:
        if not v1_source:
            root = tmp_path_factory.mktemp("e6_family_v1")
            policy = subprocess.check_output(
                ["git", "show", f"{V1_FAMILY_COMMIT}:tools/research/v6/e6/fixtures/agents/e6_q01/agent.py"],
                cwd=REPO_ROOT).replace(b"\r\n", b"\n")
            for pid in PACKAGES:
                (root / pid).mkdir()
                (root / pid / "agent.py").write_bytes(policy)
                shutil.copyfile(FIXTURE_DIR / pid / "agent.yaml", root / pid / "agent.yaml")
            v1_source.append(root)
        return v1_source[0]

    def run(ruleset_id: str, member: str, seat: str, opponent: str,
            policy: str = "current") -> tuple[list[dict[str, Any]], tuple[int, int]]:
        key = (ruleset_id, member, seat, opponent, policy)
        if key not in cache:
            other = "B" if seat == "A" else "A"
            delta, repair = SCRIPTS[opponent]
            if delta is None:
                delta = _evade_delta(_starts(ruleset_id), other)
            entrants = {seat: (package_id(member), 0, 0), other: (f"scripted_{opponent}", delta, repair)}
            cache[key] = _play(tmp_path_factory.mktemp("e6_amendment_1"), ruleset_id, entrants,
                               source=v1_fixture() if policy == "v1" else None)
        return cache[key]

    return run


@pytest.mark.parametrize("opponent", [STATIONARY, EVADING])
@pytest.mark.parametrize("member", SEARCH_VARIANTS)
@pytest.mark.parametrize("ruleset_id", CONTROL_RULESETS)
def test_engine_seat_a_adopts_the_core_before_the_opponent_acts(control_runs: Any, ruleset_id: str, member: str,
                                                                 opponent: str) -> None:
    decisions, (_start_a, start_b) = control_runs(ruleset_id, member, "A", opponent)
    assert decisions[0]["agent_id"] == "A"
    assert decisions[0]["observation"]["visible_enemy_anchor_addresses"] == [start_b]  # B has not acted yet
    # The forced line: the core base and the next cell, both before B's first callback.
    assert _first_actions(decisions, "A", 2) == [("write", start_b), ("write", (start_b + 1) % ARENA)]


@pytest.mark.parametrize("opponent", [STATIONARY, EVADING, BELOW, REPAIRING])
@pytest.mark.parametrize("member", SEARCH_VARIANTS)
@pytest.mark.parametrize("ruleset_id", CONTROL_RULESETS)
def test_engine_seat_a_tick_one_is_unchanged_from_v1(control_runs: Any, ruleset_id: str, member: str,
                                                     opponent: str) -> None:
    # Seat A's tick-1 control forced line, and everything else in tick 1, is
    # exactly what the v1 family did.
    streams = []
    for policy in ("current", "v1"):
        decisions, _ = control_runs(ruleset_id, member, "A", opponent, policy)
        streams.append([(r["agent_id"], r["process_id"], r["action"], r["applied_result"]) for r in decisions
                        if r["observation"]["current_tick"] == 1])
    assert streams[0] == streams[1]
    assert streams[0]


@pytest.mark.parametrize("member", SEARCH_VARIANTS)
@pytest.mark.parametrize("ruleset_id", CONTROL_RULESETS)
def test_engine_seat_b_confirms_a_stationary_core_over_its_own_overwritten_anchor(control_runs: Any,
                                                                                   ruleset_id: str,
                                                                                   member: str) -> None:
    decisions, (start_a, start_b) = control_runs(ruleset_id, member, "B", STATIONARY)
    assert _circular(start_a, start_b) >= 64  # the unrefined P-6 would have adopted it
    assert _first_actions(decisions, "B", 2) == [("write", start_a), ("read", start_a + 1)]
    assert _read_results(decisions, "B", start_a)[0] == (1, "B")  # core cell 0 holds B's own disruption
    assert _no_core_write_before_confirmation(decisions, "B", start_a)
    writes = set(_writes(decisions, "B"))
    assert set(_core(start_a)) <= writes
    assert not {(start_a - 1) % ARENA, (start_a + 8) % ARENA} & writes  # no base off by one


@pytest.mark.parametrize("member", SEARCH_VARIANTS)
@pytest.mark.parametrize("ruleset_id", CONTROL_RULESETS)
def test_engine_seat_b_is_not_fooled_by_an_anchor_one_below_the_core(control_runs: Any, ruleset_id: str,
                                                                      member: str) -> None:
    decisions, (start_a, start_b) = control_runs(ruleset_id, member, "B", BELOW)
    below = (start_a - 1) % ARENA
    first_b = _mine(decisions, "B")[0]
    assert first_b["observation"]["visible_enemy_anchor_addresses"] == [below]
    assert _circular(below, start_b) >= 64  # the unrefined P-6 would have adopted it
    assert _read_results(decisions, "B", below)[0] == (1, "B")  # the written anchor was a stand-in candidate
    assert _no_core_write_before_confirmation(decisions, "B", start_a)
    writes = _writes(decisions, "B")
    assert set(_core(start_a)) <= set(writes)  # a base at the anchor would never write start_a + 7
    assert (start_a + 8) % ARENA not in writes


@pytest.mark.parametrize("member", SEARCH_VARIANTS)
@pytest.mark.parametrize("ruleset_id", CONTROL_RULESETS)
def test_engine_seat_b_confirms_a_core_whose_cell_0_is_repaired(control_runs: Any, ruleset_id: str,
                                                                 member: str) -> None:
    decisions, (start_a, _start_b) = control_runs(ruleset_id, member, "B", REPAIRING)
    assert _no_core_write_before_confirmation(decisions, "B", start_a)
    writes = set(_writes(decisions, "B"))
    assert set(_core(start_a)) <= writes
    assert not {(start_a - 1) % ARENA, (start_a + 8) % ARENA} & writes
    if ruleset_id == BYTEFRAY_RULESET_V6_RESEARCH_DISRUPTION_SLOT1_ID:
        # One lost offer: the repair lands before B's scan reads core cell 0.
        assert _read_results(decisions, "B", start_a)[0] == (BEACON, "A")
    else:
        # Whole-tick denial: no repair before the scan, so the written anchor stands in.
        assert _read_results(decisions, "B", start_a)[0] == (1, "B")


@pytest.mark.parametrize("member", SEARCH_VARIANTS)
@pytest.mark.parametrize("ruleset_id", CONTROL_RULESETS)
def test_engine_seat_b_does_not_adopt_an_evaders_moved_anchor(control_runs: Any, ruleset_id: str,
                                                               member: str) -> None:
    decisions, (start_a, start_b) = control_runs(ruleset_id, member, "B", EVADING)
    (moved,) = _mine(decisions, "B")[0]["observation"]["visible_enemy_anchor_addresses"]
    assert _circular(moved, start_a) == 20
    assert _circular(moved, start_b) >= 64  # the trap: the unrefined rule would have adopted it
    assert _first_actions(decisions, "B", 2) == [("write", moved), ("read", (moved + 1) % ARENA)]
    writes = _writes(decisions, "B")
    assert not [a for a in writes if 0 < (a - moved) % ARENA < 8]  # never the false core
    assert set(_core(start_a)) <= set(writes)  # verification finds the real core, and the attack covers it


@pytest.mark.parametrize("seat", ["A", "B"])
@pytest.mark.parametrize("member", SEARCH_VARIANTS)
@pytest.mark.parametrize("ruleset_id", CONTROL_RULESETS)
def test_engine_off_core_disruption_rotates_seven_distinct_core_cells(control_runs: Any, ruleset_id: str,
                                                                       member: str, seat: str) -> None:
    decisions, starts = control_runs(ruleset_id, member, seat, EVADING_REPAIRING)
    base = starts[1] if seat == "A" else starts[0]
    core = set(_core(base))
    full_ticks = []
    for tick in sorted({r["observation"]["current_tick"] for r in _mine(decisions, seat)}):
        writes = _writes(decisions, seat, tick)
        core_writes = [a for a in writes if a in core]
        if len(writes) == 8 and writes[0] not in core and len(core_writes) == 7:
            assert len(set(core_writes)) == 7  # seven distinct core cells beside the disruption
            full_ticks.append(core - set(core_writes))
    assert all(a != b for a, b in pairwise(full_ticks))  # the omitted cell rotates
    assert core <= set(_writes(decisions, seat))  # every core cell, cell 7 included, is targeted
    if not (ruleset_id == BYTEFRAY_RULESET_V6_RESEARCH_SCALE_ID and seat == "A"):
        # (Under C-E6 Seat A's first write denies the evader its whole first
        # tick, so the tick-1 forced line ends the match before it evades.)
        assert len(full_ticks) >= 2


@pytest.mark.parametrize("seat", ["A", "B"])
@pytest.mark.parametrize("ruleset_id", CONTROL_RULESETS)
def test_engine_split_targets_every_core_index(control_runs: Any, ruleset_id: str, seat: str) -> None:
    decisions, starts = control_runs(ruleset_id, "SPLIT", seat, STATIONARY)
    base = starts[1] if seat == "A" else starts[0]
    striker = {r["action"]["operand"] for r in _mine(decisions, seat)
               if r["process_id"] == "striker" and r["action"]["kind"] == "write"}
    assert set(_core(base)) <= striker | set(_writes(decisions, seat))
    assert {(base + i) % ARENA for i in range(1, 8)} <= striker  # the striker itself reaches cells 1..7


@pytest.mark.parametrize("opponent", list(SCRIPTS))
@pytest.mark.parametrize("seat", ["A", "B"])
@pytest.mark.parametrize("ruleset_id", CONTROL_RULESETS)
def test_cq1_search_is_inert_under_each_control(control_runs: Any, ruleset_id: str, seat: str,
                                               opponent: str) -> None:
    streams = []
    for member in SEARCH_VARIANTS:
        decisions, _ = control_runs(ruleset_id, member, seat, opponent)
        streams.append([(r["agent_id"], r["process_id"], r["observation"]["current_tick"], r["action"],
                         r["applied_result"]) for r in decisions])
    assert all(stream == streams[0] for stream in streams[1:])
    assert not [s for s in streams[0] if s[0] == seat and s[3]["kind"] == "move"]
