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
    BYTEFRAY_RULESET_V6_RESEARCH_SCALE_ID,
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


def test_a_read_search_hit_is_scanned_down_to_the_base_then_attacked() -> None:
    agent = make("STEALTH", rng_seed=seed_with(direction=1))
    assert agent.act(miss(1)) == read(164)
    assert agent.act(miss(1)) == read(172)      # 164 missed
    assert agent.act(hit(1)) == read(171)       # 172 hit: scan down from it
    assert agent.act(hit(1)) == read(170)       # 171 hit
    assert agent.act(miss(1)) == write(171)     # 170 missed: the base is 171
    assert agent.enemy_core == 171


def test_search_never_runs_once_anything_is_known() -> None:
    agent = make("RUSH", rng_seed=seed_with(direction=1))
    assert agent.act(obs(1)) == move(64)
    assert agent.act(obs(1, visible=(300,))) == write(300)
    # The anchor is gone from view but remembered: verification, not search.
    assert agent.act(obs(1)) == read(300)


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
    assert agent.act(obs(1, visible=(anchor,))) == read(anchor)  # verification starts at the anchor


def test_two_visible_addresses_are_not_adopted() -> None:
    agent = make("LURK")
    assert agent.act(obs(1, visible=(300, 400))) == write(300)
    assert agent.act(obs(1, visible=(300, 400))) == write(400)
    assert agent.act(obs(1, visible=(300, 400))) == read(300)


def test_adoption_happens_only_at_the_first_callback() -> None:
    agent = make("LURK")
    assert agent.act(obs(1)) == write(paint_sequence(agent.paint_side, 1)[0])
    assert agent.act(obs(1, visible=(300,))) == write(300)
    assert agent.act(obs(1, visible=(300,))) == read(300)


def test_verification_reads_outward_then_scans_down_to_the_base() -> None:
    agent = make("LURK")
    agent.act(obs(1))  # first callback: nothing visible
    assert agent.act(obs(1, visible=(300,))) == write(300)
    assert agent.act(obs(1, visible=(300,))) == read(300)
    assert agent.act(miss(1, visible=(300,))) == read(292)
    assert agent.act(miss(1, visible=(300,))) == read(308)
    assert agent.act(hit(1, visible=(300,))) == read(307)       # 308 hit
    assert agent.act(hit(2, visible=(300,))) == write(300)      # new tick: the anchor first
    assert agent.act(hit(2, visible=(300,))) == read(306)       # 307 hit
    assert agent.act(miss(2, visible=(300,))) == write(307)     # 306 missed: base 307
    assert [agent.act(obs(2, visible=(300,))) for _ in range(7)] == [write(307 + i) for i in range(1, 8)]
    assert agent.enemy_core == 307


def test_the_window_order_and_extent() -> None:
    agent = make("LURK")
    agent.act(obs(1))
    agent.act(obs(1, visible=(300,)))
    reads = [agent.act(miss(1 + i // 8)) for i in range(17)]
    expected = [300] + [a for step in range(8, 65, 8) for a in (300 - step, 300 + step)]
    assert reads == [read(a) for a in expected]


def test_a_scan_stops_after_eight_cells() -> None:
    agent = make("LURK")
    agent.act(obs(1))
    agent.act(obs(1, visible=(300,)))
    assert agent.act(miss(1)) == read(300)
    assert agent.act(hit(1)) == read(299)  # 300 hit
    for address in range(298, 292, -1):
        assert agent.act(hit(2)) == read(address)
    assert agent.act(hit(3)) == write(293)  # 293 is the seventh cell below 300: base
    assert agent.enemy_core == 293


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
    assert agent.act(miss(1)) == read(300)
    assert agent.act(obs(1, value=BEACON, owner="A")) == read(292)
    assert agent.act(obs(1, value=BEACON, owner=None)) == read(308)
    assert agent.act(obs(1, value=BEACON, owner="B", applied=False)) == read(284)


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
    assert agent.act(obs(1, pid="striker", visible=(300,))) == read(300)
    assert agent.act(obs(1, pid="sensor", visible=(300,))) == write(paint_sequence(side, 2)[1])
    assert agent.act(hit(1, pid="striker", visible=(300,))) == read(299)


def test_a_remembered_anchor_alone_stops_the_search() -> None:
    # Out of sight, core unknown, no scan under way: only the memory of the
    # anchor keeps the sensor from searching (plan Sec 5.2: search runs only
    # when nothing is visible, nothing is remembered and the core is unknown).
    agent = make("SPLIT", rng_seed=seed_with(direction=1))
    assert agent.act(obs(1, pid="sensor")) == move(64)
    assert agent.act(obs(1, pid="sensor", visible=(300,))) == write(300)
    assert (agent.last_known, agent.enemy_core, agent.scan_top) == ((300, 1), None, None)
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
    assert agent.act(obs(40)) == read(300)
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
