"""V6 E5: the semantics of ``RulesetPolicy.initial_anchor_placement``.

docs/research/v6/V6_E5_ANCHOR_CORE_SEPARATION_DESIGN_REVIEW.md Sec B/F and
docs/research/v6/V6_E5_DESIGN_REVIEW_REVISION_1.md Sec R2/R3. What is proven
here, and what is deliberately *not* claimed:

* **Ruleset invariants** (D-1, D-2). Under ``"before_core"`` every process
  with no declared position spawns at ``(core_base - 1) % arena_size`` --
  never a cell of its own core -- and the core itself (base, cells, seeding,
  the recorded ``pc``) is untouched (P1). An explicit ``initial_position`` is
  kept.
* **No movement prohibition** (Revision 1 Sec R3). A process may MOVE onto
  its own core afterwards; an enemy WRITE there then both disrupts it and
  flips the core cell -- a DUAL write -- exactly as under ``"core_base"``.
  ``"before_core"`` is a spawn rule, not a spatial rule.
* **E5-corpus characterization** (D-3, D-4). For the tracked V6 research
  fixtures, which never move onto their own core, no hostile WRITE is both an
  anchor hit and a core write of the same victim (P4), while under the parent
  every anchor hit on an unmoved process is one.
* **The observation delta** (review Sec L gate 5). An entrant's first
  observation differs from the parent's only in ``self_anchor`` (-1) and in
  every visible enemy anchor (-1).
* **Unchanged scheduling and hold** (P7). The G.4 minimum-actions bound and
  G.5 immunity of the continuous repairers hold under both treatments.
* **Opening-pass traces** (review Sec B.4) at seed 42, outside matrix seeds
  1-32: short mechanical characterizations, not treatment results.

Behavioral inertness of the fixtures' anchor-derived enemy-core inference
(P5) is a research-instrument gate and lives with the E5 tooling
(``tools/research/v6/e5``); the ``"core_base"``-path byte identity is
``test_v6_e5_parent_byte_identity.py``.
"""

from __future__ import annotations

from collections.abc import Callable
from itertools import pairwise
from pathlib import Path
from typing import Any

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
)
from battle_engine.replay import KillDeathEvent, TickSnapshot, iter_replay
from battle_engine.ruleset_policy import (
    BYTEFRAY_RULESET_V6_RESEARCH_CAPTURE_HOLD_K2_DISRUPTION_SLOT1_ANCHOR_BEFORE_CORE_ID,
    BYTEFRAY_RULESET_V6_RESEARCH_CAPTURE_HOLD_K2_DISRUPTION_SLOT1_ID,
    BYTEFRAY_RULESET_V6_RESEARCH_DISRUPTION_SLOT1_ANCHOR_BEFORE_CORE_ID,
    BYTEFRAY_RULESET_V6_RESEARCH_DISRUPTION_SLOT1_ID,
    resolve_ruleset_policy,
)

from tools.research.v6.e3.entrants import prepare_data_root

PRIMARY_ID = BYTEFRAY_RULESET_V6_RESEARCH_CAPTURE_HOLD_K2_DISRUPTION_SLOT1_ANCHOR_BEFORE_CORE_ID
COMPANION_ID = BYTEFRAY_RULESET_V6_RESEARCH_DISRUPTION_SLOT1_ANCHOR_BEFORE_CORE_ID
T_E3_ID = BYTEFRAY_RULESET_V6_RESEARCH_CAPTURE_HOLD_K2_DISRUPTION_SLOT1_ID
T_E3K1_ID = BYTEFRAY_RULESET_V6_RESEARCH_DISRUPTION_SLOT1_ID
E5_IDS = (PRIMARY_ID, COMPANION_ID)
PARENT_ID = {PRIMARY_ID: T_E3_ID, COMPANION_ID: T_E3K1_ID}
ARENA = 512
QUOTA = 8
SEED = 42  # outside the matrix seeds 1..32
IDLE = AgentAction(ActionKindV2.READ, operand=0)

# The seven fixtures of the E5 field (review Sec I).
E5_FIELD = (
    "e2_sniper", "e2_min_guard", "e2_disrupt_guard", "e2_repair_guard",
    "e2_guarded_painter", "e2_spread_sniper", "e2_spread_defender",
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

Executor = Callable[[ObservationV2, int], AgentAction]


def _process(pid: str, position: int | None, share: int, act: Executor) -> ProcessInstance:
    return ProcessInstance(pid, ProcessRole.GENERALIST, initial_position=position, reach=ARENA // 2,
                           quota_share=share, logic=lambda _obs, _state: IDLE, executor=act)


def _controller(ruleset_id: str, entrants: list[tuple[str, int, list[ProcessInstance]]],
                ticks: int = 1) -> ProcessMatchController:
    specs = [ProcessEntrantSpec(agent_id=seat, name=f"seat-{seat}", processes=processes, start=start)
             for seat, start, processes in entrants]
    return ProcessMatchController(Config(seed=1, arena_size=ARENA, instr_per_tick=QUOTA), specs, ticks,
                                  ruleset_policy=resolve_ruleset_policy(ruleset_id))


def _run_fixtures(root: Path, ruleset_id: str, names: tuple[str, str], *, seed: int = SEED,
                  ticks: int = 1000) -> Path:
    prepare_data_root(root, list(names))
    starts = resolve_direct_match_starts(ruleset_id=ruleset_id, arena_size=ARENA, entrant_count=2,
                                         supplied_starts=[None, None], seed=seed)
    replay = root / "runs" / f"{ruleset_id}-{names[0]}-vs-{names[1]}-s{seed}" / "replay.jsonl"
    replay.parent.mkdir(parents=True, exist_ok=True)
    NativeMatchService().run(MatchRequest(
        config=Config(seed=seed, arena_size=ARENA, instr_per_tick=QUOTA),
        entrants=tuple(MatchEntrant.python(seat, name, start, resolve_agent(root, name))
                       for seat, name, start in zip("AB", names, starts, strict=True)),
        max_ticks=ticks, replay_path=replay, verbose=False, ruleset_id=ruleset_id))
    return replay


def _snapshots(replay: Path) -> list[TickSnapshot]:
    return [record for record in iter_replay(replay) if isinstance(record, TickSnapshot)]


def _writes(snapshot: TickSnapshot) -> list[tuple[int, str | None]]:
    """Every memory write of one tick as (address, owner), in write order."""
    return [((diff.address + i) % ARENA, diff.owner) for diff in snapshot.memory_diffs for i in range(diff.length)]


def dual_writes(replay: Path) -> dict[str, int]:
    """P4 over one replay: hostile writes that hit the anchor of a live victim
    process *and* a cell of that same victim's core. A process's position
    inside tick t is its anchor at the t-1 or the t boundary (a MOVE is
    atomic), so counting either is a conservative superset of the true
    DUAL count. Also counts plain anchor hits on unmoved processes."""
    snaps = _snapshots(replay)
    cores = {agent.agent_id: {(agent.pc + i) % ARENA for i in range(QUOTA)} for agent in snaps[0].agents}
    spawn = {(p.entrant_id, p.process_id): p.anchor for p in snaps[0].processes}
    moved: set[tuple[str, str]] = set()
    counts = {"dual": 0, "unmoved_anchor_hits": 0}
    for before, after in pairwise(snaps):
        alive = {agent.agent_id for agent in before.agents if agent.alive}
        positions: dict[str, set[int]] = {}
        for snap in (before, after):
            for p in snap.processes:
                positions.setdefault(p.entrant_id, set()).add(p.anchor)
        unmoved = {(p.entrant_id, p.anchor) for p in before.processes
                   if (p.entrant_id, p.process_id) not in moved and p.anchor == spawn[(p.entrant_id, p.process_id)]}
        for address, owner in _writes(after):
            for victim in alive - {owner}:
                if address in positions.get(victim, set()) and address in cores[victim]:
                    counts["dual"] += 1
                if (victim, address) in unmoved:
                    counts["unmoved_anchor_hits"] += 1
        for p in after.processes:
            if p.anchor != spawn[(p.entrant_id, p.process_id)]:
                moved.add((p.entrant_id, p.process_id))
    return counts


# ---------------------------------------------------------------------------
# Ruleset invariants: spawn (D-1) and the untouched core (P1)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("ruleset_id", [*E5_IDS, T_E3_ID, T_E3K1_ID])
@pytest.mark.parametrize("starts", [(100, 300), (0, 256), (511, 200), (7, 400)])
def test_every_default_spawn_follows_the_ruleset(ruleset_id: str, starts: tuple[int, int]) -> None:
    before_core = ruleset_id in E5_IDS
    processes = {seat: [_process(f"{seat}{i}", None, share, lambda _o, _s: IDLE) for i, share in enumerate((3, 3, 2))]
                 for seat in "AB"}
    controller = _controller(ruleset_id, [(seat, start, processes[seat]) for seat, start in zip("AB", starts)])
    for state, spec in zip(controller.states, controller.entrant_specs, strict=True):
        expected = (state.core_base - 1) % ARENA if before_core else state.core_base
        assert [p.position for p in spec.processes] == [expected] * 3
        # The core itself is placed and recorded exactly as the start says (P1).
        assert state.core_base == state.pc == state.region[0] == state.region[1] == state.core_start
        assert state.core_cells == tuple((state.core_base + i) % ARENA for i in range(QUOTA))
        for p in spec.processes:
            assert p.telemetry.positions_visited == {expected}
            if before_core:
                assert p.position not in state.core_cells
        # Seeding: every core cell owned by its entrant before tick 1.
        assert all(controller.vm.writer[cell] == state.agent_id for cell in state.core_cells)


@pytest.mark.parametrize("ruleset_id", E5_IDS)
def test_an_explicit_initial_position_is_kept(ruleset_id: str) -> None:
    # The spawn rule reads only processes with no declared position.
    explicit = _process("x", 150, 4, lambda _o, _s: IDLE)
    default = _process("d", None, 4, lambda _o, _s: IDLE)
    _controller(ruleset_id, [("A", 100, [explicit, default]),
                             ("B", 300, [_process("b", None, 8, lambda _o, _s: IDLE)])])
    assert (explicit.position, default.position) == (150, 99)


# ---------------------------------------------------------------------------
# No movement prohibition: MOVE onto the own core, then a DUAL write
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("ruleset_id", E5_IDS)
def test_a_process_may_move_onto_its_own_core_and_be_dual_hit_there(ruleset_id: str) -> None:
    # Revision 1 Sec R3: "before_core" spawns off the core but constrains
    # nothing afterwards. Seat A moves its process +1 onto its own core cell 0
    # with its first action, then idles; seat B writes every visible enemy
    # anchor. B's write to A's core cell 0 then both disrupts A's process and
    # flips the core cell -- a DUAL write, legal under this Ruleset.
    moves: list[int] = []

    def mover(obs: ObservationV2, _slot: int) -> AgentAction:
        if not moves:
            moves.append(obs.self_anchor)
            return AgentAction(ActionKindV2.MOVE, operand=1)
        return IDLE

    def hitter(obs: ObservationV2, _slot: int) -> AgentAction:
        anchors = obs.visible_enemy_anchor_addresses
        return AgentAction(ActionKindV2.WRITE, operand=anchors[0], value=1) if anchors else IDLE

    a = _process("a", None, QUOTA, mover)
    b = _process("b", None, QUOTA, hitter)
    controller = _controller(ruleset_id, [("A", 100, [a]), ("B", 300, [b])], ticks=1)
    controller.run()
    assert moves == [99]  # spawned before the core
    assert a.position == 100  # now on its own core cell 0: allowed
    assert a.telemetry.disruption_hits_received >= 1
    assert controller.vm.writer[100] == "B"  # the same write took the core cell


# ---------------------------------------------------------------------------
# The observation delta (review Sec L gate 5)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("ruleset_id", E5_IDS)
def test_first_observations_differ_only_in_the_anchor_fields(ruleset_id: str) -> None:
    def first_observations(policy_id: str) -> dict[str, ObservationV2]:
        seen: dict[str, ObservationV2] = {}

        def recorder(seat: str) -> Executor:
            def act(obs: ObservationV2, _slot: int) -> AgentAction:
                seen.setdefault(seat, obs)
                return IDLE

            return act

        controller = _controller(policy_id, [("A", 100, [_process("a", None, QUOTA, recorder("A"))]),
                                             ("B", 300, [_process("b", None, QUOTA, recorder("B"))])])
        controller.run()
        return seen

    parent, treatment = first_observations(PARENT_ID[ruleset_id]), first_observations(ruleset_id)
    for seat in "AB":
        p, t = parent[seat], treatment[seat]
        assert t.self_anchor == (p.self_anchor - 1) % ARENA
        assert t.visible_enemy_anchor_addresses == tuple((a - 1) % ARENA for a in p.visible_enemy_anchor_addresses)
        assert t.own_core_base == p.own_core_base and t.own_core_size == p.own_core_size
        assert {**vars(t), "self_anchor": None, "visible_enemy_anchor_addresses": None} == {
            **vars(p), "self_anchor": None, "visible_enemy_anchor_addresses": None}


# ---------------------------------------------------------------------------
# E5-corpus characterization: DUAL = 0 for the research fixtures (P4)
# ---------------------------------------------------------------------------

DUAL_PAIRINGS = (
    ("e2_sniper", "e2_min_guard"),
    ("e2_disrupt_guard", "e2_guarded_painter"),
    ("e2_spread_defender", "e2_min_guard"),
    ("e2_spread_sniper", "e2_disrupt_guard"),
)


@pytest.mark.parametrize("names", DUAL_PAIRINGS, ids=lambda pair: "-vs-".join(pair))
@pytest.mark.parametrize("ruleset_id", E5_IDS)
def test_no_hostile_write_is_both_an_anchor_hit_and_a_core_write(
    tmp_path: Path, ruleset_id: str, names: tuple[str, str]
) -> None:
    treatment = dual_writes(_run_fixtures(tmp_path / "t", ruleset_id, names, ticks=60))
    parent = dual_writes(_run_fixtures(tmp_path / "c", PARENT_ID[ruleset_id], names, ticks=60))
    # The fixtures do hit unmoved anchors in both arms...
    assert treatment["unmoved_anchor_hits"] > 0 and parent["unmoved_anchor_hits"] > 0
    # ...but only under the parent is such a hit also a core write.
    assert parent["dual"] > 0
    assert treatment["dual"] == 0


@pytest.mark.parametrize("ruleset_id", E5_IDS)
def test_no_fixture_process_ever_sits_on_its_own_core(tmp_path: Path, ruleset_id: str) -> None:
    # D-4, a characterization of this fixture set (never a Ruleset rule): the
    # only movers, the spread fixtures, move once by 16..64 from base - 1.
    for names in (("e2_spread_defender", "e2_spread_sniper"), ("e2_spread_sniper", "e2_spread_defender")):
        snaps = _snapshots(_run_fixtures(tmp_path / "-".join(names), ruleset_id, names, ticks=30))
        cores = {agent.agent_id: {(agent.pc + i) % ARENA for i in range(QUOTA)} for agent in snaps[0].agents}
        for snap in snaps:
            for p in snap.processes:
                assert p.anchor not in cores[p.entrant_id], (snap.tick, p)


# ---------------------------------------------------------------------------
# Unchanged scheduling and hold (P7)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("ruleset_id", E5_IDS)
def test_g4_minimum_actions_hold(tmp_path: Path, ruleset_id: str) -> None:
    # Forward order, lambda = 1: an entrant alive throughout a tick executes
    # at least 5 actions as first mover and 4 as second (E3 G.4), and never 0.
    for names in (("e2_sniper", "e2_disrupt_guard"), ("e2_spread_sniper", "e2_min_guard")):
        snaps = _snapshots(_run_fixtures(tmp_path / "-".join(names), ruleset_id, names, ticks=40))
        for before, after in pairwise(snaps):
            first = "AB"[(after.tick - 1) % 2]
            for agent in after.agents:
                was_alive = next(a.alive for a in before.agents if a.agent_id == agent.agent_id)
                if was_alive and agent.alive:
                    assert agent.cpu_used >= (5 if agent.agent_id == first else 4), (after.tick, agent)


@pytest.mark.parametrize("attacker", ["e2_sniper", "e2_min_guard", "e2_spread_sniper", "e2_spread_defender"])
@pytest.mark.parametrize("guard", ["e2_repair_guard", "e2_disrupt_guard"])
def test_g5_continuous_repairers_are_never_captured_under_k2(tmp_path: Path, guard: str, attacker: str) -> None:
    # G.5 needs only the guard's own final action and K = 2, neither of which
    # E5 touches: no capture of a repair or disrupt guard in either seat.
    for names in ((guard, attacker), (attacker, guard)):
        replay = _run_fixtures(tmp_path / "-".join(names), PRIMARY_ID, names)
        guard_seat = "A" if names[0] == guard else "B"
        kills = [event for snap in _snapshots(replay) for event in snap.events
                 if isinstance(event, KillDeathEvent) and event.victim == guard_seat]
        assert kills == [], names


# ---------------------------------------------------------------------------
# Opening-pass traces (review Sec B.4), seed 42
# ---------------------------------------------------------------------------


def _tick_writes(replay: Path, tick: int) -> list[tuple[str | None, int]]:
    (snap,) = [s for s in _snapshots(replay) if s.tick == tick]
    return [(owner, address) for address, owner in _writes(snap)]


def _own_core(replay: Path, tick: int) -> dict[str, int]:
    snaps = _snapshots(replay)
    cores = {agent.agent_id: [(agent.pc + i) % ARENA for i in range(QUOTA)] for agent in snaps[0].agents}
    owners: dict[int, Any] = {}
    for snap in snaps:
        for address, owner in _writes(snap):
            owners[address] = owner
        if snap.tick == tick:
            return {seat: sum(owners.get(c) == seat for c in cells) for seat, cells in cores.items()}
    raise AssertionError(tick)


def test_opening_pass_trace_sniper_v_min_guard(tmp_path: Path) -> None:
    # Seat A (sniper) core 485, Seat B (min guard) core 203 at seed 42. The
    # anchor hit and the core-0 write become two writes, and the min guard
    # still retakes its base after the sniper's last write to it.
    replay = _run_fixtures(tmp_path, PRIMARY_ID, ("e2_sniper", "e2_min_guard"), ticks=2)
    assert _tick_writes(replay, 1) == [
        ("A", 202), ("A", 203), ("B", 484), ("A", 204), ("B", 203), ("B", 485), ("A", 205), ("A", 206),
        ("B", 486), ("B", 487), ("A", 207), ("A", 208), ("B", 488), ("B", 489),
    ]
    assert _own_core(replay, 1) == {"A": 3, "B": 3}


def test_opening_pass_trace_disrupt_guard_v_guarded_painter(tmp_path: Path) -> None:
    # Anchor-only contact: every anchor hit now lands off the core, so both
    # cores stay whole through the opening ticks.
    replay = _run_fixtures(tmp_path, PRIMARY_ID, ("e2_disrupt_guard", "e2_guarded_painter"), ticks=4)
    writes = _tick_writes(replay, 1)
    assert writes[:4] == [("A", 202), ("A", 485), ("B", 484), ("A", 486)]
    for tick in (1, 2, 3, 4):
        assert _own_core(replay, tick) == {"A": 8, "B": 8}
