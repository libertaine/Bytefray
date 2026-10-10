"""PA-8: the lockout rule under the four E6 Rulesets, with scripted non-family agents.

docs/research/v6/V6_E7_SENSING_DISRUPTION_INTERACTION_DESIGN_REVIEW.md
Sec 4.3 derives by hand how long a disruptive hit denies its victim; Sec 7.5
and Sec 8.1 (PA-8) ask for that derivation as a tested Ruleset
characterization. This module is it.

An attacker writes a victim's anchor at chosen offers of every tick. The
victim is one stationary process that never acts on the attacker. Both are
scripted executors on a directly constructed ``ProcessMatchController``, the
E3 semantics-test pattern, and no E6 family member is used. Every
callback the engine makes is recorded, as (tick, seat, offer slot).

Each test first asserts its preconditions on the real run: the rotation puts
Seat A first on odd ticks and Seat B first on even ticks, and every scripted
hit lands on the victim. Only then does it assert the victim's callbacks,
tick by tick and offer by offer:

* **Whole tick** (``research-scale``, ``research-sensing-r32``). A victim hit
  at the attacker's first offer gets **no callback** in a tick its opponent
  moves first. In a tick it moves first it gets exactly its first chunk,
  offers 0 and 1. So a re-hit victim acts only on ticks of its own seat's
  parity.
* **One offer** (``research-disruption-slot1`` and its sensing variant). The
  same victim loses exactly one offer per hit. It keeps 7 of 8 offers against
  one hit per tick, and at least 4 even against a hit at the start of every
  attacker chunk.

The sensing radius changes none of this: each rule holds identically with and
without ``detection_radius = 32``. No outcome is asserted.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass

import pytest
from battle_engine.agent_api import ActionKindV2, AgentAction, ObservationV2
from battle_engine.config import Config
from battle_engine.process_runtime import (
    ProcessEntrantSpec,
    ProcessInstance,
    ProcessMatchController,
    ProcessRole,
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
TICKS = 6
CORE = {"A": 100, "B": 300}
ANCHOR = {"A": 40, "B": 440}  # off both cores, so no write here can capture anything
WHOLE_TICK = (RULESET_V6_RESEARCH_SCALE, RULESET_V6_RESEARCH_SENSING_R32)
ONE_OFFER = (RULESET_V6_RESEARCH_DISRUPTION_SLOT1, RULESET_V6_RESEARCH_DISRUPTION_SLOT1_SENSING_R32)
IDLE = AgentAction(ActionKindV2.READ, operand=0)
OTHER = {"A": "B", "B": "A"}


def _ids(policy: RulesetPolicy) -> str:
    return policy.ruleset_id


@dataclass(frozen=True)
class Call:
    tick: int
    seat: str
    slot: int


@dataclass(frozen=True)
class Played:
    calls: list[Call]
    victim: ProcessInstance

    def slots(self, seat: str, tick: int) -> list[int]:
        return [c.slot for c in self.calls if (c.seat, c.tick) == (seat, tick)]

    def first_mover(self, tick: int) -> str:
        return next(c.seat for c in self.calls if c.tick == tick)


def _play(policy: RulesetPolicy, attacker: str, hit_slots: Sequence[int]) -> Played:
    """``attacker`` writes the victim's anchor at each offer slot in ``hit_slots``, every tick."""

    victim = OTHER[attacker]
    calls: list[Call] = []

    def executor(seat: str) -> Callable[[ObservationV2, int], AgentAction]:
        def act(obs: ObservationV2, slot: int) -> AgentAction:
            calls.append(Call(obs.current_tick, seat, slot))
            if seat == attacker and slot in hit_slots:
                return AgentAction(ActionKindV2.WRITE, operand=ANCHOR[victim], value=1)
            return IDLE

        return act

    processes = {
        seat: ProcessInstance("main", ProcessRole.GENERALIST, initial_position=ANCHOR[seat], reach=ARENA // 2,
                              quota_share=QUOTA, logic=lambda _obs, _state: IDLE, executor=executor(seat))
        for seat in ("A", "B")
    }
    specs = [ProcessEntrantSpec(agent_id=seat, name=f"seat-{seat}", processes=[processes[seat]], start=CORE[seat])
             for seat in ("A", "B")]
    controller = ProcessMatchController(Config(seed=1, arena_size=ARENA, instr_per_tick=QUOTA), specs, TICKS,
                                        ruleset_policy=policy)
    controller.run()
    return Played(calls, processes[victim])


def _assert_preconditions(played: Played, attacker: str, hits_per_tick: int) -> None:
    # The rotation: Seat A moves first on odd ticks, Seat B on even ticks.
    assert [played.first_mover(t) for t in range(1, TICKS + 1)] == ["A", "B", "A", "B", "A", "B"]
    # The attacker is offered all 8 of its offers every tick (the victim never touches it) ...
    assert all(played.slots(attacker, t) == list(range(QUOTA)) for t in range(1, TICKS + 1))
    # ... and every scripted hit lands on the victim's anchor.
    assert played.victim.telemetry.disruption_hits_received == hits_per_tick * TICKS
    assert played.victim.telemetry.disrupted_match_ticks == set(range(1, TICKS + 1))


@pytest.mark.parametrize("policy", WHOLE_TICK, ids=_ids)
@pytest.mark.parametrize("attacker", ["A", "B"])
def test_whole_tick_lockout_confines_the_victim_to_its_own_first_mover_ticks(policy: RulesetPolicy, attacker: str) -> None:
    played = _play(policy, attacker, hit_slots=(0,))
    _assert_preconditions(played, attacker, hits_per_tick=1)
    victim = OTHER[attacker]
    for tick in range(1, TICKS + 1):
        if played.first_mover(tick) == attacker:
            assert played.slots(victim, tick) == []  # hit before its first offer: no callback at all
        else:
            assert played.slots(victim, tick) == [0, 1]  # its first chunk, then nothing after the hit
    # So the ticks it acts on are exactly those of its own seat's parity.
    acted = sorted({c.tick for c in played.calls if c.seat == victim})
    assert acted == ([1, 3, 5] if victim == "A" else [2, 4, 6])


@pytest.mark.parametrize("policy", WHOLE_TICK, ids=_ids)
@pytest.mark.parametrize("attacker", ["A", "B"])
def test_whole_tick_lockout_does_not_depend_on_how_often_the_attacker_re_hits(policy: RulesetPolicy, attacker: str) -> None:
    once = _play(policy, attacker, hit_slots=(0,))
    every_chunk = _play(policy, attacker, hit_slots=(0, 2, 4, 6))
    victim = OTHER[attacker]
    # A suppressed victim's anchor is still written by the later hits (they land), but it
    # has no offer left in the tick to lose.
    assert every_chunk.victim.telemetry.disruption_hits_received == 4 * TICKS
    assert [every_chunk.slots(victim, t) for t in range(1, TICKS + 1)] == [once.slots(victim, t) for t in range(1, TICKS + 1)]


@pytest.mark.parametrize("policy", ONE_OFFER, ids=_ids)
@pytest.mark.parametrize("attacker", ["A", "B"])
def test_one_offer_disruption_costs_the_victim_one_offer_per_hit(policy: RulesetPolicy, attacker: str) -> None:
    played = _play(policy, attacker, hit_slots=(0,))
    _assert_preconditions(played, attacker, hits_per_tick=1)
    victim = OTHER[attacker]
    for tick in range(1, TICKS + 1):
        if played.first_mover(tick) == attacker:
            assert played.slots(victim, tick) == [1, 2, 3, 4, 5, 6, 7]  # loses offer 0
        else:
            assert played.slots(victim, tick) == [0, 1, 3, 4, 5, 6, 7]  # loses offer 2, its first after the hit
    assert sorted({c.tick for c in played.calls if c.seat == victim}) == list(range(1, TICKS + 1))


@pytest.mark.parametrize("policy", ONE_OFFER, ids=_ids)
@pytest.mark.parametrize("attacker", ["A", "B"])
def test_one_offer_disruption_leaves_at_least_four_offers_against_a_hit_every_chunk(
    policy: RulesetPolicy, attacker: str,
) -> None:
    played = _play(policy, attacker, hit_slots=(0, 2, 4, 6))
    _assert_preconditions(played, attacker, hits_per_tick=4)
    victim = OTHER[attacker]
    for tick in range(1, TICKS + 1):
        if played.first_mover(tick) == attacker:
            assert played.slots(victim, tick) == [1, 3, 5, 7]
        else:
            assert played.slots(victim, tick) == [0, 1, 3, 5, 7]
