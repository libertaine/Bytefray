"""V6 E3 slot-limited disruption: per-offer semantics, the action bound, the
hold/order immunity, and mechanic characterizations.

docs/research/v6/V6_E3_SLOT_LIMITED_DISRUPTION_REGISTRATION.md. Under
``RulesetPolicy.disruption_slot_limit == 1`` a disruptive hit suppresses each
victim process for exactly its entrant's next action offer -- not a global
scheduler slot -- and never past the end of the tick; ``None`` is the
historical whole-tick rule (proven byte-identical by
``test_v6_e3_parent_byte_identity.py``).

* **Sequence-level semantics (G.3)** drive a directly constructed
  ``ProcessMatchController`` with scripted entrants. Every process acts
  through an ``executor``, which the runtime hands the scheduler's action
  slot -- the entrant's offer index -- so each test records exactly which of
  an entrant's eight offers were forfeited, which process took each
  executed offer, and what that process could see, and asserts the whole
  per-offer sequence by value. A recording replay sink supplies each tick's
  real replay record (``cpu_used`` and each process's ``disrupted`` flag).
  The engine is not instrumented or patched.
* **The action bound (G.4)** is proven by exhaustive enumeration: every
  jammer action sequence over the victim's anchors for one tick, with the
  victim in each scheduler position.
* **Hold/order immunity (G.5)** plays a K=2 guard against adversarial
  jammers, including an omniscient one, for many ticks.
* **Mechanic characterizations** run the tracked E2 research fixtures end to
  end through ``NativeMatchService`` at seed 42 (the E2 design review's Sec D
  geometry) and assert per-tick mechanics from the canonical replay alone.
  They pin *mechanics*, never a balance outcome.
"""

from __future__ import annotations

import itertools
import random
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
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
    BYTEFRAY_RULESET_V6_RESEARCH_CAPTURE_HOLD_K2_DISRUPTION_SLOT1_ID,
    BYTEFRAY_RULESET_V6_RESEARCH_CAPTURE_HOLD_K2_ID,
    BYTEFRAY_RULESET_V6_RESEARCH_DISRUPTION_SLOT1_ID,
    BYTEFRAY_RULESET_V6_RESEARCH_SCALE_ID,
    RULESET_V4,
    RULESET_V6_RESEARCH_CAPTURE_HOLD_K2,
    RULESET_V6_RESEARCH_CAPTURE_HOLD_K2_DISRUPTION_SLOT1,
    RULESET_V6_RESEARCH_DISRUPTION_SLOT1,
    RULESET_V6_RESEARCH_SCALE,
    RulesetPolicy,
)

from tools.research.v6.experiment_harness import prepare_benchmark_data_root

PRIMARY = RULESET_V6_RESEARCH_CAPTURE_HOLD_K2_DISRUPTION_SLOT1
COMPANION = RULESET_V6_RESEARCH_DISRUPTION_SLOT1
# The primary's parent: identical except whole-tick disruption.
WHOLE_TICK = RULESET_V6_RESEARCH_CAPTURE_HOLD_K2
TREATMENTS = (PRIMARY, COMPANION)


def _policy_id(policy: RulesetPolicy) -> str:
    return policy.ruleset_id


# ---------------------------------------------------------------------------
# Harness: scripted multi-process entrants on a directly constructed controller
# ---------------------------------------------------------------------------

ARENA = 512
QUOTA = 8
OFFERS = tuple(range(QUOTA))
# Core bases, and default process anchors placed away from every core.
CORE = {"A": 100, "B": 300}
J_ANCHOR = 40
V_ANCHOR = 440


def _w(address: int) -> AgentAction:
    return AgentAction(ActionKindV2.WRITE, operand=address % ARENA, value=1)


# An action with no ownership or disruption effect.
_IDLE = AgentAction(ActionKindV2.READ, operand=0)


@dataclass(frozen=True)
class Proc:
    pid: str
    anchor: int
    share: int
    reach: int = ARENA // 2


# A process's decision for one offer: (controller, observation, offer slot, process id).
Brain = Callable[[ProcessMatchController, ObservationV2, int, str], AgentAction]


def _scripted(script: Mapping[tuple[int, int], AgentAction]) -> Brain:
    """The action scripted for each (tick, offer slot); idle otherwise."""

    def brain(_c: ProcessMatchController, obs: ObservationV2, slot: int, _pid: str) -> AgentAction:
        return script.get((obs.current_tick, slot), _IDLE)

    return brain


def _hits(*offers: tuple[int, int], target: int = V_ANCHOR) -> Brain:
    """A jammer that writes ``target`` at exactly the given (tick, slot) offers."""

    return _scripted({offer: _w(target) for offer in offers})


@dataclass(frozen=True)
class Call:
    tick: int
    seat: str
    slot: int
    process: str
    visible: tuple[int, ...]
    action: AgentAction


@dataclass(frozen=True)
class TickRecord:
    tick: int
    cpu: dict[str, int]
    disrupted: dict[tuple[str, str], bool]
    owned: dict[str, int]
    streak: dict[str, int]
    alive: dict[str, bool]
    events: tuple[dict[str, Any], ...]


class _Recorder:
    """A replay sink that also snapshots live core ownership and capture streaks."""

    def __init__(self, controller: ProcessMatchController) -> None:
        self.controller = controller
        self.ticks: list[TickRecord] = []

    def emit(self, record: dict[str, Any]) -> None:
        if "config" in record or record["tick"] == 0:
            return
        writer = self.controller.vm.writer
        states = self.controller.states
        self.ticks.append(
            TickRecord(
                tick=record["tick"],
                cpu={agent["id"]: agent["cpu_used"] for agent in record["agents"]},
                disrupted={
                    (process["entrant_id"], process["process_id"]): process["disrupted"]
                    for process in record["processes"]
                },
                owned={
                    st.agent_id: sum(1 for cell in st.core_cells if writer[cell] == st.agent_id)
                    for st in states
                },
                streak={st.agent_id: st.core_zero_streak for st in states},
                alive={st.agent_id: st.alive for st in states},
                events=tuple(dict(event) for event in record["events"]),
            )
        )

    def close(self) -> None:
        return None


@dataclass(frozen=True)
class Played:
    calls: list[Call]
    ticks: list[TickRecord]
    summary: dict[str, Any]
    controller: ProcessMatchController

    def taken_by(self, seat: str, tick: int) -> list[str | None]:
        """Per offer slot: the process that acted, or ``None`` if the offer was forfeited."""

        by_slot = {call.slot: call.process for call in self.calls if (call.tick, call.seat) == (tick, seat)}
        return [by_slot.get(slot) for slot in OFFERS]

    def visible(self, seat: str, tick: int) -> list[tuple[int, ...] | None]:
        by_slot = {call.slot: call.visible for call in self.calls if (call.tick, call.seat) == (tick, seat)}
        return [by_slot.get(slot) for slot in OFFERS]

    def process(self, seat: str, pid: str) -> ProcessInstance:
        spec = next(spec for spec in self.controller.entrant_specs if spec.agent_id == seat)
        return next(process for process in spec.processes if process.process_id == pid)


def _play(
    processes: Mapping[str, Sequence[Proc]],
    brains: Mapping[str, Brain],
    *,
    policy: RulesetPolicy,
    max_ticks: int = 1,
    order: Sequence[str] = ("A", "B"),
    cores: Mapping[str, int] = CORE,
) -> Played:
    """Play a scripted match; ``order[0]`` moves first on tick 1 (then rotation)."""

    calls: list[Call] = []
    holder: dict[str, ProcessMatchController] = {}

    def executor(seat: str, pid: str) -> Callable[[ObservationV2, int], AgentAction]:
        def run(obs: ObservationV2, slot: int) -> AgentAction:
            action = brains.get(seat, _scripted({}))(holder["controller"], obs, slot, pid)
            calls.append(
                Call(obs.current_tick, seat, slot, pid, tuple(obs.visible_enemy_anchor_addresses), action)
            )
            return action

        return run

    specs = [
        ProcessEntrantSpec(
            agent_id=seat,
            name=f"seat-{seat}",
            processes=[
                ProcessInstance(
                    proc.pid,
                    ProcessRole.GENERALIST,
                    initial_position=proc.anchor,
                    reach=proc.reach,
                    quota_share=proc.share,
                    logic=lambda _obs, _state: _IDLE,
                    executor=executor(seat, proc.pid),
                )
                for proc in processes[seat]
            ],
            start=cores[seat],
        )
        for seat in order
    ]
    controller = ProcessMatchController(
        Config(seed=1, arena_size=ARENA, instr_per_tick=QUOTA),
        specs,
        max_ticks,
        ruleset_policy=policy,
    )
    holder["controller"] = controller
    recorder = _Recorder(controller)
    summary = controller.run(recorder)
    return Played(calls, recorder.ticks, summary, controller)


def _jammer_vs(victim: Sequence[Proc], jammer: Brain, *, policy: RulesetPolicy, max_ticks: int = 1) -> Played:
    """Seat A is a one-process jammer; Seat B is the victim (second mover on tick 1)."""

    return _play(
        {"A": (Proc("j", J_ANCHOR, QUOTA),), "B": victim},
        {"A": jammer},
        policy=policy,
        max_ticks=max_ticks,
    )


SINGLE = (Proc("p", V_ANCHOR, QUOTA),)
P = "p"
Q = "q"


# ---------------------------------------------------------------------------
# Policy preconditions
# ---------------------------------------------------------------------------


def test_policies_under_test() -> None:
    assert (PRIMARY.disruption_slot_limit, PRIMARY.capture_hold_ticks) == (1, 2)
    assert (COMPANION.disruption_slot_limit, COMPANION.capture_hold_ticks) == (1, 1)
    assert (WHOLE_TICK.disruption_slot_limit, WHOLE_TICK.capture_hold_ticks) == (None, 2)
    for policy in TREATMENTS:
        assert (policy.scheduler_mode, policy.scheduler_chunk_size, policy.scheduler_rotate_start) == (
            "chunked",
            2,
            True,
        )
        assert policy.process_selection == "round_robin"


@pytest.mark.parametrize(
    "policy",
    [RULESET_V4, RULESET_V6_RESEARCH_SCALE, WHOLE_TICK, PRIMARY, COMPANION],
    ids=_policy_id,
)
def test_the_one_tick_disruption_window_is_unchanged(policy: RulesetPolicy) -> None:
    played = _jammer_vs(SINGLE, _hits(), policy=policy)
    assert played.controller.disruption_duration == 1


# ---------------------------------------------------------------------------
# G.3 sequence-level semantics
# ---------------------------------------------------------------------------
#
# Tick 1 offer order (Seat A first, chunk size 2):
#   A0 A1 | B0 B1 | A2 A3 | B2 B3 | A4 A5 | B4 B5 | A6 A7 | B6 B7


@pytest.mark.parametrize("hit_slot", [0, 1])
@pytest.mark.parametrize("policy", TREATMENTS, ids=_policy_id)
def test_single_hit_suppresses_only_the_victims_next_offer(policy: RulesetPolicy, hit_slot: int) -> None:
    played = _jammer_vs(SINGLE, _hits((1, hit_slot)), policy=policy)

    # B0 is forfeited; B1, in the same chunk and the same tick, is eligible.
    assert played.taken_by("B", 1) == [None, P, P, P, P, P, P, P]
    assert played.ticks[0].cpu == {"A": 8, "B": 7}
    assert played.process("B", P).disruption_slots_left == 0


@pytest.mark.parametrize("hit_slot", [0, 1])
def test_whole_tick_parent_silences_the_victim_for_the_rest_of_the_tick(hit_slot: int) -> None:
    played = _jammer_vs(SINGLE, _hits((1, hit_slot)), policy=WHOLE_TICK)

    assert played.taken_by("B", 1) == [None] * 8
    assert played.ticks[0].cpu == {"A": 8, "B": 0}


@pytest.mark.parametrize("policy", TREATMENTS, ids=_policy_id)
def test_two_hits_before_one_offer_suppress_it_once(policy: RulesetPolicy) -> None:
    played = _jammer_vs(SINGLE, _hits((1, 0), (1, 1)), policy=policy)

    assert played.taken_by("B", 1) == [None, P, P, P, P, P, P, P]
    assert played.ticks[0].cpu["B"] == 7


@pytest.mark.parametrize("policy", TREATMENTS, ids=_policy_id)
def test_each_hit_between_victim_offers_suppresses_its_own_offer(policy: RulesetPolicy) -> None:
    played = _jammer_vs(SINGLE, _hits((1, 0), (1, 2)), policy=policy)
    assert played.taken_by("B", 1) == [None, P, None, P, P, P, P, P]

    # A hit landing after the victim's first chunk suppresses only the next one.
    played = _jammer_vs(SINGLE, _hits((1, 2)), policy=policy)
    assert played.taken_by("B", 1) == [P, P, None, P, P, P, P, P]

    # One hit before every victim chunk: one lost offer per chunk.
    played = _jammer_vs(SINGLE, _hits((1, 0), (1, 2), (1, 4), (1, 6)), policy=policy)
    assert played.taken_by("B", 1) == [None, P, None, P, None, P, None, P]
    assert played.ticks[0].cpu["B"] == 4


@pytest.mark.parametrize("policy", TREATMENTS, ids=_policy_id)
def test_hit_on_the_victims_offer_consumes_the_victims_next_offer(policy: RulesetPolicy) -> None:
    # Seat B writes A's anchor on B0: A's own next offer (A2) is the one
    # lost -- never an offer of the entrant that made the hit, and never the
    # rest of the hitting offer.
    played = _play(
        {"A": (Proc(P, J_ANCHOR, QUOTA),), "B": SINGLE},
        {"B": _hits((1, 0), target=J_ANCHOR)},
        policy=policy,
    )
    assert played.taken_by("A", 1) == [P, P, None, P, P, P, P, P]
    assert played.taken_by("B", 1) == [P] * 8


@pytest.mark.parametrize("hit_slot", [6, 7])
@pytest.mark.parametrize("policy", [*TREATMENTS, WHOLE_TICK], ids=_policy_id)
def test_hit_after_the_victims_final_offer_does_not_carry_into_the_next_tick(
    policy: RulesetPolicy, hit_slot: int
) -> None:
    # Seat A is the victim and moves first on tick 1, so B's final chunk
    # (B6 B7) comes after A's final offer. Tick 2 rotates: B moves first.
    played = _play(
        {"A": SINGLE, "B": (Proc("j", J_ANCHOR, QUOTA),)},
        {"B": _hits((1, hit_slot))},
        policy=policy,
        max_ticks=2,
    )
    assert played.taken_by("A", 1) == [P] * 8
    assert played.taken_by("A", 2) == [P] * 8
    assert [tick.disrupted[("A", P)] for tick in played.ticks] == [True, False]
    if policy.disruption_slot_limit is not None:
        # The counter set by the late hit is never consumed, and never read.
        assert played.process("A", P).disruption_slots_left == 1


@pytest.mark.parametrize("policy", TREATMENTS, ids=_policy_id)
def test_a_stale_counter_never_adds_to_a_new_hit(policy: RulesetPolicy) -> None:
    # Tick 1 leaves A's counter at 1 (hit after its final offer); tick 2's
    # hit before A's first offer assigns 1 again rather than making it 2.
    played = _play(
        {"A": SINGLE, "B": (Proc("j", J_ANCHOR, QUOTA),)},
        {"B": _hits((1, 7), (2, 0))},
        policy=policy,
        max_ticks=2,
    )
    # Tick 2 order: B0 B1 | A0 A1 | ...
    assert played.taken_by("A", 2) == [None, P, P, P, P, P, P, P]


@pytest.mark.parametrize("policy", TREATMENTS, ids=_policy_id)
def test_one_hit_suppresses_every_colocated_process(policy: RulesetPolicy) -> None:
    victim = (Proc(P, V_ANCHOR, 4), Proc(Q, V_ANCHOR, 4))
    played = _jammer_vs(victim, _hits((1, 0)), policy=policy)

    # Both processes are suppressed for B0 -- the whole offer is forfeited --
    # and both are eligible again from B1, in their usual rotation.
    assert played.taken_by("B", 1) == [None, P, Q, P, Q, P, Q, P]
    assert played.process("B", P).disruption_slots_left == 0
    assert played.process("B", Q).disruption_slots_left == 0
    assert played.ticks[0].disrupted[("B", P)] and played.ticks[0].disrupted[("B", Q)]

    whole_tick = _jammer_vs(victim, _hits((1, 0)), policy=WHOLE_TICK)
    assert whole_tick.taken_by("B", 1) == [None] * 8


@pytest.mark.parametrize("policy", TREATMENTS, ids=_policy_id)
def test_all_processes_suppressed_forfeits_the_offer_and_it_still_counts(policy: RulesetPolicy) -> None:
    # Spread processes, both hit before B0: the offer is forfeited, both
    # counters are spent on it, and B gets no replacement offer -- a
    # forfeited offer is one of its eight.
    victim = (Proc(P, V_ANCHOR, 4), Proc(Q, V_ANCHOR + 10, 4))
    played = _play(
        {"A": (Proc("j", J_ANCHOR, QUOTA),), "B": victim},
        {"A": _scripted({(1, 0): _w(V_ANCHOR), (1, 1): _w(V_ANCHOR + 10)})},
        policy=policy,
    )
    assert played.taken_by("B", 1) == [None, P, Q, P, Q, P, Q, P]
    assert played.ticks[0].cpu["B"] == 7
    assert (
        played.process("B", P).disruption_slots_left,
        played.process("B", Q).disruption_slots_left,
    ) == (0, 0)


@pytest.mark.parametrize("policy", TREATMENTS, ids=_policy_id)
def test_partial_suppression_keeps_the_rotation_position_of_the_suppressed_process(
    policy: RulesetPolicy,
) -> None:
    victim = (Proc(P, V_ANCHOR, 4), Proc(Q, V_ANCHOR + 10, 4))

    baseline = _jammer_vs(victim, _hits(), policy=policy)
    assert baseline.taken_by("B", 1) == [P, Q, P, Q, P, Q, P, Q]

    # Only p (at the written anchor) is suppressed for B0: the entrant still
    # acts, through q. p is passed over without consuming its turn, so it
    # takes B1 as soon as it is eligible again.
    played = _jammer_vs(victim, _hits((1, 0)), policy=policy)
    assert played.taken_by("B", 1) == [Q, P, Q, P, Q, P, Q, P]
    assert played.ticks[0].cpu["B"] == 8

    whole_tick = _jammer_vs(victim, _hits((1, 0)), policy=WHOLE_TICK)
    assert whole_tick.taken_by("B", 1) == [Q] * 8


@pytest.mark.parametrize("policy", TREATMENTS, ids=_policy_id)
def test_only_the_written_anchor_is_suppressed_and_siblings_get_redistributed_quota(
    policy: RulesetPolicy,
) -> None:
    # p (share 6) and q (share 2) at different anchors. Unhit, q stops at
    # its own share of two actions.
    victim = (Proc(P, V_ANCHOR, 6), Proc(Q, V_ANCHOR + 10, 2))
    assert _jammer_vs(victim, _hits(), policy=policy).taken_by("B", 1) == [P, Q, P, Q, P, P, P, P]

    # p is hit before B4, after q has used its share: while p is suppressed
    # the whole quota is redistributed to q, which takes a third action --
    # exactly today's redistribution -- and p resumes at B5.
    played = _jammer_vs(victim, _hits((1, 4)), policy=policy)
    assert played.taken_by("B", 1) == [P, Q, P, Q, Q, P, P, P]
    assert played.ticks[0].disrupted == {("A", "j"): False, ("B", P): True, ("B", Q): False}

    whole_tick = _jammer_vs(victim, _hits((1, 4)), policy=WHOLE_TICK)
    assert whole_tick.taken_by("B", 1) == [P, Q, P, Q, Q, Q, Q, Q]


@pytest.mark.parametrize("policy", TREATMENTS, ids=_policy_id)
def test_suppressed_processes_cannot_sense_until_their_suppression_expires(policy: RulesetPolicy) -> None:
    # p (global reach) is the entrant's only sensor that can see the
    # jammer's anchor; q's reach cannot. Sensing is entrant-wide but only
    # through unsuppressed processes.
    victim = (Proc(P, V_ANCHOR, 4), Proc(Q, V_ANCHOR + 20, 4, reach=4))
    seen = (J_ANCHOR,)

    baseline = _jammer_vs(victim, _hits(), policy=policy)
    assert baseline.visible("B", 1) == [seen] * 8

    played = _jammer_vs(victim, _hits((1, 0)), policy=policy)
    assert played.taken_by("B", 1) == [Q, P, Q, P, Q, P, Q, P]
    # Blind only while p is suppressed (B0); p's suppression expires within
    # the tick and sensing returns from B1.
    assert played.visible("B", 1) == [(), seen, seen, seen, seen, seen, seen, seen]

    whole_tick = _jammer_vs(victim, _hits((1, 0)), policy=WHOLE_TICK, max_ticks=2)
    assert whole_tick.visible("B", 1) == [()] * 8
    assert whole_tick.visible("B", 2) == [seen] * 8


@pytest.mark.parametrize("policy", TREATMENTS, ids=_policy_id)
def test_replay_disrupted_flag_keeps_its_tick_level_meaning(policy: RulesetPolicy) -> None:
    # The flag still means "hit during this tick": it is set on tick 1 even
    # though p acted on seven offers after the hit and ended the tick with
    # no suppression left, exactly as it is under whole-tick disruption.
    jammer = _hits((1, 0), (3, 5))
    played = _jammer_vs(SINGLE, jammer, policy=policy, max_ticks=4)
    whole_tick = _jammer_vs(SINGLE, jammer, policy=WHOLE_TICK, max_ticks=4)

    flags = [tick.disrupted for tick in played.ticks]
    assert flags == [tick.disrupted for tick in whole_tick.ticks]
    assert [flag[("B", P)] for flag in flags] == [True, False, True, False]
    assert not any(flag[("A", "j")] for flag in flags)
    assert played.process("B", P).disruption_slots_left == 0
    # Tick 3 (B moves first): the hit at A5 lands before B4.
    assert played.taken_by("B", 3) == [P, P, P, P, None, P, P, P]


# ---------------------------------------------------------------------------
# G.4: the action bound, by exhaustive enumeration
# ---------------------------------------------------------------------------
#
# Q = 8, two entrants, chunk size 2, rotating first mover. A tick's
# suppression state never depends on an earlier tick (a hit sets
# ``disrupted_until_tick = tick + 1``), so one tick in each scheduler
# position covers every tick. The victim idles (it never disrupts the
# jammer, the worst case for it); the jammer's only actions that matter are
# writes to the victim's anchors, so enumerating every sequence of eight
# choices from {each victim anchor, a harmless action} is every legal jam.

VICTIM_LAYOUTS: dict[str, tuple[Proc, ...]] = {
    "single-process": SINGLE,
    "co-located": (Proc("v0", V_ANCHOR, 4), Proc("v1", V_ANCHOR, 4)),
    "spread": (Proc("v0", V_ANCHOR, 4), Proc("v1", V_ANCHOR + 10, 4)),
}


def _victim_actions(
    policy: RulesetPolicy, victim: Sequence[Proc], jam: Sequence[AgentAction], *, victim_first: bool
) -> int:
    def process(pid: str, anchor: int, share: int, script: Sequence[AgentAction] | None) -> ProcessInstance:
        def act(_obs: ObservationV2, slot: int) -> AgentAction:
            return _IDLE if script is None else script[slot]

        return ProcessInstance(
            pid,
            ProcessRole.GENERALIST,
            initial_position=anchor,
            reach=ARENA // 2,
            quota_share=share,
            logic=lambda _obs, _state: _IDLE,
            executor=act,
        )

    victim_spec = ProcessEntrantSpec(
        agent_id="V",
        name="victim",
        processes=[process(proc.pid, proc.anchor, proc.share, None) for proc in victim],
        start=CORE["B"],
    )
    jammer_spec = ProcessEntrantSpec(
        agent_id="J", name="jammer", processes=[process("j", J_ANCHOR, QUOTA, jam)], start=CORE["A"]
    )
    controller = ProcessMatchController(
        Config(seed=1, arena_size=ARENA, instr_per_tick=QUOTA),
        [victim_spec, jammer_spec] if victim_first else [jammer_spec, victim_spec],
        1,
        ruleset_policy=policy,
    )
    controller.run()
    victim_state = next(state for state in controller.states if state.agent_id == "V")
    assert victim_state.alive
    return victim_state.cpu_used


def _all_jams(victim: Sequence[Proc]) -> list[tuple[AgentAction, ...]]:
    options = [_w(anchor) for anchor in sorted({proc.anchor for proc in victim})] + [_IDLE]
    return list(itertools.product(options, repeat=QUOTA))


@pytest.mark.parametrize("layout", VICTIM_LAYOUTS)
@pytest.mark.parametrize("policy", TREATMENTS, ids=_policy_id)
def test_g4_every_legal_jam_leaves_five_first_mover_and_four_second_mover_actions(
    policy: RulesetPolicy, layout: str
) -> None:
    victim = VICTIM_LAYOUTS[layout]
    jams = _all_jams(victim)
    for victim_first, bound in ((True, 5), (False, 4)):
        actions = [_victim_actions(policy, victim, jam, victim_first=victim_first) for jam in jams]
        # The bound holds for every jam, and some jam attains it exactly.
        assert min(actions) == bound, (layout, victim_first)
        # Whole-tick denial is impossible.
        assert 0 not in actions


@pytest.mark.parametrize("layout", ["single-process", "co-located"])
def test_g4_whole_tick_parent_still_reaches_the_historical_two_and_zero(layout: str) -> None:
    victim = VICTIM_LAYOUTS[layout]
    jams = _all_jams(victim)
    for victim_first, historical in ((True, 2), (False, 0)):
        actions = [_victim_actions(WHOLE_TICK, victim, jam, victim_first=victim_first) for jam in jams]
        assert min(actions) == historical, (layout, victim_first)


def test_g4_whole_tick_parent_silences_a_spread_victim_hit_at_both_anchors() -> None:
    victim = VICTIM_LAYOUTS["spread"]
    jam = (_w(V_ANCHOR), _w(V_ANCHOR + 10)) + (_IDLE,) * 6
    assert _victim_actions(WHOLE_TICK, victim, jam, victim_first=False) == 0
    assert _victim_actions(PRIMARY, victim, jam, victim_first=False) == 7


@pytest.mark.parametrize("policy", [*TREATMENTS, WHOLE_TICK], ids=_policy_id)
def test_g4_bound_under_natural_rotation(policy: RulesetPolicy) -> None:
    # A jammer that writes the victim's anchor with every action, for six
    # ticks: the victim alternates second mover (odd ticks) and first mover.
    jammer = _hits(*((tick, slot) for tick in range(1, 7) for slot in OFFERS))
    played = _jammer_vs(SINGLE, jammer, policy=policy, max_ticks=6)
    expected = [4, 5] * 3 if policy.disruption_slot_limit == 1 else [0, 2] * 3
    assert [tick.cpu["B"] for tick in played.ticks] == expected


# ---------------------------------------------------------------------------
# G.5: K = 2 hold/order immunity
# ---------------------------------------------------------------------------
#
# With K = 2, lambda = 1 and the rotating first mover, a guard that always
# makes a final own-core repair on every tick in which it moves second can
# never be at zero core at two consecutive end-of-tick evaluations: on those
# ticks its final chunk is the last of the tick, at most its first offer of
# that chunk can be suppressed, and nothing acts after its final offer.

G_CORE = CORE["B"]
G_CELLS = tuple(G_CORE + offset for offset in range(8))


def _repair_guard() -> Brain:
    cursor = {"next": 0}

    def brain(_c: ProcessMatchController, _obs: ObservationV2, _slot: int, _pid: str) -> AgentAction:
        target = G_CELLS[cursor["next"] % 8]
        cursor["next"] += 1
        return _w(target)

    return brain


def _disrupt_first_guard() -> Brain:
    done: dict[str, Any] = {"tick": None, "targets": set()}

    def brain(_c: ProcessMatchController, obs: ObservationV2, _slot: int, _pid: str) -> AgentAction:
        if done["tick"] != obs.current_tick:
            done["tick"], done["targets"] = obs.current_tick, set()
        for target in (*obs.visible_enemy_anchor_addresses, *G_CELLS):
            if target not in done["targets"]:
                done["targets"].add(target)
                return _w(target)
        return _IDLE

    return brain


GUARDS: dict[str, Callable[[], Brain]] = {
    "repair-guard": _repair_guard,
    "disrupt-first-guard": _disrupt_first_guard,
}


def _greedy_jammer(guard_seat: str) -> Brain:
    """Omniscient: re-disrupt the guard whenever it could act, otherwise erase its core.

    The guard is anchored on its own core base, so every disruptive write
    also erases a core cell.
    """

    def brain(c: ProcessMatchController, obs: ObservationV2, _slot: int, _pid: str) -> AgentAction:
        spec = next(spec for spec in c.entrant_specs if spec.agent_id == guard_seat)
        (guard,) = spec.processes
        if not c._is_suppressed(guard, obs.current_tick):
            return _w(G_CORE)
        owned = [cell for cell in G_CELLS if c.vm.writer[cell] == guard_seat]
        return _w(owned[0] if owned else G_CORE)

    return brain


def _chunk_jammer() -> Brain:
    """Disrupt with the first action of every chunk, erase core cells with the second."""

    def brain(_c: ProcessMatchController, obs: ObservationV2, slot: int, _pid: str) -> AgentAction:
        if slot % 2 == 0:
            return _w(G_CORE)
        return _w(G_CELLS[(obs.current_tick + slot) % 8])

    return brain


def _random_jammer(seed: int) -> Brain:
    rng = random.Random(seed)
    options = [_w(cell) for cell in G_CELLS] + [_IDLE]

    def brain(_c: ProcessMatchController, _obs: ObservationV2, _slot: int, _pid: str) -> AgentAction:
        return rng.choice(options)

    return brain


def _guard_match(
    policy: RulesetPolicy, guard: Brain, jammer: Brain, *, guard_first: bool, ticks: int
) -> tuple[Played, str]:
    guard_seat = "A" if guard_first else "B"
    jammer_seat = "B" if guard_first else "A"
    played = _play(
        {guard_seat: (Proc("g", G_CORE, QUOTA),), jammer_seat: (Proc("j", J_ANCHOR, QUOTA),)},
        {guard_seat: guard, jammer_seat: jammer},
        policy=policy,
        max_ticks=ticks,
        order=("A", "B"),
        cores={guard_seat: G_CORE, jammer_seat: CORE["A"]},
    )
    return played, guard_seat


def _assert_immune(played: Played, guard_seat: str, *, ticks: int) -> None:
    assert [tick.tick for tick in played.ticks] == list(range(1, ticks + 1))
    assert all(tick.alive[guard_seat] for tick in played.ticks)
    assert max(tick.streak[guard_seat] for tick in played.ticks) <= 1
    for tick in played.ticks:
        guard_moves_second = (tick.tick % 2 == 1) == (guard_seat == "B")
        if guard_moves_second:
            # The guard took the tick's final offer, with an own-core repair,
            # and so ends the tick owning part of its core.
            last = [call for call in played.calls if call.tick == tick.tick][-1]
            assert (last.seat, last.slot) == (guard_seat, QUOTA - 1)
            assert last.action.kind is ActionKindV2.WRITE and last.action.operand in G_CELLS
            assert tick.owned[guard_seat] >= 1


G5_TICKS = 24


def _g5_jammers(guard_seat: str) -> list[Brain]:
    return [_greedy_jammer(guard_seat), _chunk_jammer()] + [_random_jammer(seed) for seed in range(20)]


# The lowest end-of-tick core ownership the adversaries force on each guard
# under lambda = 1. Non-vacuity: the omniscient jammer presses the repair
# guard down to a single cell and drives the disrupt-first guard to zero on
# some ticks -- just never on two ticks running.
G5_MIN_OWNED = {"repair-guard": 1, "disrupt-first-guard": 0}


@pytest.mark.parametrize("guard_first", [True, False])
@pytest.mark.parametrize("guard", GUARDS)
def test_g5_guard_never_accumulates_two_consecutive_zero_core_evaluations(
    guard: str, guard_first: bool
) -> None:
    guard_seat = "A" if guard_first else "B"
    min_owned = QUOTA
    for jammer in _g5_jammers(guard_seat):
        played, seat = _guard_match(
            PRIMARY, GUARDS[guard](), jammer, guard_first=guard_first, ticks=G5_TICKS
        )
        _assert_immune(played, seat, ticks=G5_TICKS)
        min_owned = min(min_owned, *(tick.owned[seat] for tick in played.ticks))
    assert min_owned == G5_MIN_OWNED[guard]


@pytest.mark.parametrize("guard_first", [True, False])
def test_g5_whole_tick_parent_lets_the_same_adversaries_capture_the_repair_guard(
    guard_first: bool,
) -> None:
    # The same guard and adversaries under the whole-tick parent: silenced
    # for a whole tick, the guard is at zero core twice running and is
    # captured -- the E2 mechanism the bound removes.
    guard_seat = "A" if guard_first else "B"
    captured = 0
    for index, jammer in enumerate(_g5_jammers(guard_seat)):
        played, seat = _guard_match(
            WHOLE_TICK, _repair_guard(), jammer, guard_first=guard_first, ticks=G5_TICKS
        )
        if not played.ticks[-1].alive[seat]:
            captured += 1
            assert played.ticks[-1].streak[seat] == 2
            assert played.summary["reason"] == "last_agent_standing"
        if index == 0:
            # The omniscient jammer captures it on tick 2 from either seat.
            assert [tick.tick for tick in played.ticks] == [1, 2]
            assert played.ticks[-1].alive[seat] is False
    assert captured >= 2


# ---------------------------------------------------------------------------
# Mechanic characterizations with the tracked E2 fixtures (seed 42)
# ---------------------------------------------------------------------------

SEED = 42
E3_ID = BYTEFRAY_RULESET_V6_RESEARCH_CAPTURE_HOLD_K2_DISRUPTION_SLOT1_ID
COMPANION_ID = BYTEFRAY_RULESET_V6_RESEARCH_DISRUPTION_SLOT1_ID
E2_ID = BYTEFRAY_RULESET_V6_RESEARCH_CAPTURE_HOLD_K2_ID
RS_ID = BYTEFRAY_RULESET_V6_RESEARCH_SCALE_ID
# Seed 42: Seat A's core at 485, Seat B's at 203; every single-process
# fixture anchors on its own core base.
A_CORE, B_CORE = 485, 203


@dataclass(frozen=True)
class FixtureTick:
    tick: int
    cpu: dict[str, int]
    alive: dict[str, bool]
    owned: dict[str, int]
    writes: tuple[tuple[int, str | None], ...]
    kills: tuple[tuple[str, str | None], ...]


def _run_fixtures(root: Path, ruleset_id: str, seat_a: str, seat_b: str, *, max_ticks: int = 1000) -> list[FixtureTick]:
    prepare_benchmark_data_root(root, [seat_a, seat_b])
    starts = resolve_direct_match_starts(
        ruleset_id=ruleset_id, arena_size=ARENA, entrant_count=2, supplied_starts=[None, None], seed=SEED
    )
    assert starts == (A_CORE, B_CORE)
    replay_path = root / "runs" / f"{ruleset_id}-{seat_a}-vs-{seat_b}" / "replay.jsonl"
    replay_path.parent.mkdir(parents=True)
    NativeMatchService().run(
        MatchRequest(
            config=Config(seed=SEED, arena_size=ARENA, instr_per_tick=QUOTA),
            entrants=(
                MatchEntrant.python("A", seat_a, starts[0], resolve_agent(root, seat_a)),
                MatchEntrant.python("B", seat_b, starts[1], resolve_agent(root, seat_b)),
            ),
            max_ticks=max_ticks,
            replay_path=replay_path,
            verbose=False,
            ruleset_id=ruleset_id,
        )
    )
    cores = {"A": A_CORE, "B": B_CORE}
    owners: dict[int, str | None] = {}
    ticks: list[FixtureTick] = []
    for record in iter_replay(replay_path):
        if not isinstance(record, TickSnapshot):
            continue
        writes = tuple(
            ((diff.address + offset) % ARENA, diff.owner)
            for diff in record.memory_diffs
            for offset in range(diff.length)
        )
        for address, owner in writes:
            owners[address] = owner
        if record.tick == 0:
            continue
        ticks.append(
            FixtureTick(
                tick=record.tick,
                cpu={agent.agent_id: agent.cpu_used for agent in record.agents},
                alive={agent.agent_id: agent.alive for agent in record.agents},
                owned={
                    seat: sum(1 for offset in range(8) if owners.get((base + offset) % ARENA) == seat)
                    for seat, base in cores.items()
                },
                writes=writes,
                kills=tuple(
                    (event.victim, event.killer)
                    for event in record.events
                    if isinstance(event, KillDeathEvent)
                ),
            )
        )
    return ticks


def _silenced_ticks(ticks: Sequence[FixtureTick]) -> list[tuple[int, str]]:
    """Ticks in which an entrant alive at the end executed no action at all."""

    return [
        (tick.tick, seat)
        for tick in ticks
        for seat in ("A", "B")
        if tick.alive[seat] and tick.cpu[seat] == 0
    ]


def _min_actions(ticks: Sequence[FixtureTick]) -> int:
    return min(tick.cpu[seat] for tick in ticks for seat in ("A", "B") if tick.alive[seat])


def _core(base: int, owner: str, cells: range = range(8)) -> tuple[tuple[int, str], ...]:
    return tuple(((base + offset) % ARENA, owner) for offset in cells)


def test_sniper_vs_disrupt_guard_no_longer_takes_turns_owning_whole_ticks(tmp_path: Path) -> None:
    parent = _run_fixtures(tmp_path / "e2", E2_ID, "e2_sniper", "e2_disrupt_guard", max_ticks=4)
    # E2 (review Sec D.5): each side owns alternate ticks outright.
    assert [tick.cpu for tick in parent] == [{"A": 8, "B": 0}, {"A": 0, "B": 8}] * 2

    ticks = _run_fixtures(tmp_path / "e3", E3_ID, "e2_sniper", "e2_disrupt_guard")
    # Both act in every tick: each loses only the first offer of each chunk
    # that follows a disruptive write.
    assert [tick.cpu for tick in ticks[:4]] == [{"A": 7, "B": 7}] * 4
    # Tick 1: A's first write hits B's anchor (203); B0 is forfeited, B1
    # disrupts A (485); A2 is forfeited; and so on, interleaved.
    assert ticks[0].writes == (
        (203, "A"), (204, "A"), (485, "B"), (205, "A"), (203, "B"), (204, "B"),
        (206, "A"), (207, "A"), (205, "B"), (206, "B"), (208, "A"), (209, "A"),
        (207, "B"), (208, "B"),
    )  # fmt: skip
    assert _silenced_ticks(ticks) == []
    assert _min_actions(ticks) >= 4


@pytest.mark.parametrize(
    "seats", [("e2_sniper", "e2_repair_guard"), ("e2_repair_guard", "e2_sniper")], ids="-vs-".join
)
def test_pure_repair_guard_keeps_acting_after_the_first_attacker_response(
    tmp_path: Path, seats: tuple[str, str]
) -> None:
    ticks = _run_fixtures(tmp_path, E3_ID, *seats)
    assert _silenced_ticks(ticks) == []
    assert _min_actions(ticks) >= 4


def test_pure_repair_guard_repairs_between_sniper_chunks(tmp_path: Path) -> None:
    parent = _run_fixtures(tmp_path / "e2", E2_ID, "e2_sniper", "e2_repair_guard")
    # E2 (review Sec D.4): silenced on tick 1, two repairs on tick 2, captured.
    assert [tick.cpu for tick in parent] == [{"A": 8, "B": 0}, {"A": 8, "B": 2}]
    assert parent[-1].kills == (("B", "A"),)

    ticks = _run_fixtures(tmp_path / "e3", E3_ID, "e2_sniper", "e2_repair_guard", max_ticks=3)
    # The sniper hits B's anchor once per tick (its first write); B loses
    # that one offer and then repairs in every one of its later chunks.
    assert [tick.cpu for tick in ticks] == [{"A": 8, "B": 7}] * 3
    assert ticks[0].writes == (
        (203, "A"), (204, "A"), (203, "B"), (205, "A"), (206, "A"), (204, "B"),
        (205, "B"), (207, "A"), (208, "A"), (206, "B"), (207, "B"), (209, "A"),
        (210, "A"), (208, "B"), (209, "B"),
    )  # fmt: skip
    assert all(tick.owned["B"] > 0 for tick in ticks)


def test_spread_sniper_location_count_no_longer_denies_whole_ticks(tmp_path: Path) -> None:
    parent = _run_fixtures(tmp_path / "e2", E2_ID, "e2_spread_sniper", "e2_disrupt_guard")
    # E2 (review Sec D.6): B's two-action chunk on tick 2 can disrupt only
    # two of A's three locations; A's third disrupts B for the rest of the
    # tick, and B is captured on tick 3 without acting again.
    assert [tick.cpu for tick in parent] == [{"A": 8, "B": 0}, {"A": 8, "B": 2}, {"A": 8, "B": 0}]
    assert parent[1].writes[:2] == ((35, "B"), (451, "B"))
    assert parent[-1].kills == (("B", "A"),)

    ticks = _run_fixtures(tmp_path / "e3", E3_ID, "e2_spread_sniper", "e2_disrupt_guard")
    assert [tick.cpu for tick in ticks[:3]] == [{"A": 8, "B": 7}] * 3
    # Tick 2: the same opening -- B disrupts two of A's three locations, and
    # A's surviving p0 hits B's anchor -- but B loses only its next offer
    # and then disrupts p0 and repairs.
    assert ticks[1].writes == (
        (35, "B"), (451, "B"), (203, "A"), (204, "A"), (485, "B"), (205, "A"),
        (206, "A"), (203, "B"), (204, "B"), (207, "A"), (208, "A"), (205, "B"),
        (206, "B"), (209, "A"), (210, "A"),
    )  # fmt: skip
    assert _silenced_ticks(ticks) == []
    assert _min_actions(ticks) >= 4


@pytest.mark.parametrize(
    ("ruleset_id", "parent_id"), [(E3_ID, E2_ID), (COMPANION_ID, RS_ID)], ids=["primary", "companion"]
)
def test_probe_mirror_no_longer_follows_the_exclusive_tick_trace(
    tmp_path: Path, ruleset_id: str, parent_id: str
) -> None:
    parent = _run_fixtures(tmp_path / "parent", parent_id, "v4_probe", "v4_probe_twin")
    ticks = _run_fixtures(tmp_path / "treatment", ruleset_id, "v4_probe", "v4_probe_twin")

    # The parent's forced line: Seat A's first write silences B for the
    # whole tick (E2 then gives B the next tick outright).
    assert parent[0].cpu == {"A": 8, "B": 0}
    assert parent[0].writes == _core(B_CORE, "A")
    if parent_id == E2_ID:
        assert parent[1].cpu == {"A": 0, "B": 8}
    # Under the treatment both mirror halves act in every tick.
    assert [tick.cpu for tick in ticks[:2]] == [{"A": 7, "B": 7}] * 2
    assert ticks[0].writes == (
        (203, "A"), (204, "A"), (485, "B"), (205, "A"), (486, "B"), (487, "B"),
        (206, "A"), (207, "A"), (488, "B"), (489, "B"), (208, "A"), (209, "A"),
        (490, "B"), (491, "B"),
    )  # fmt: skip
    assert _silenced_ticks(ticks) == []


@pytest.mark.parametrize("ruleset_id", [E3_ID, COMPANION_ID], ids=["primary", "companion"])
@pytest.mark.parametrize(
    "seats",
    [
        ("e2_sniper", "e2_disrupt_guard"),
        ("e2_disrupt_guard", "e2_sniper"),
        ("e2_spread_sniper", "e2_disrupt_guard"),
        ("e2_disrupt_guard", "e2_spread_sniper"),
        ("e2_guarded_painter", "e2_guarded_painter_twin"),
    ],
    ids="-vs-".join,
)
def test_no_entrant_is_ever_silenced_for_a_whole_tick(
    tmp_path: Path, ruleset_id: str, seats: tuple[str, str]
) -> None:
    # G.4 on real agents: every entrant alive at the end of a tick executed
    # at least four actions in it.
    ticks = _run_fixtures(tmp_path, ruleset_id, *seats)
    assert _silenced_ticks(ticks) == []
    assert _min_actions(ticks) >= 4
