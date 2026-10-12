"""V6 E8: pins for three I8-3 fixed details that had no test of their own (phase I8-4).

The family's README (``tools/research/v6/e8/fixtures/README.md``) says each of
its fixed details is pinned by a test. At the family freeze, three were found
pinned only in part or not at all. The research lead approved judgment calls 2
and 3 at the I8-3 close (2026-09-30). These tests pin what the frozen policy
already does. No family source changes, and no family member plays another.

* **Judgment call 2** (README item 4). "After first discovery" includes the
  discovering callback. That callback is the one on which the SENSE result is
  *delivered* through ``previous_sense_anchors``, not the one that issued the
  SENSE. When the delivery callback is an entrant's first callback of a tick,
  ``repeat`` and ``adaptive`` members verify there and then: under active, a
  SENSE centered on the lowest known address (PR8 Sec 3.2, KU-8).
* **Judgment call 3** (README item 7). ADAPT8's verification observation is
  about one selected address *a*: the lowest known address under active, the
  lowest tracked one under passive. Another known address found missing does
  not reset the count unless it is *a*.
* **Fixed detail 14.** Without parameters, which only a validation dry run
  produces, a package behaves as GREED8.

Each synthetic test drives the policy with constructed observations, as the
I8-3 state-machine tests do. The engine-level test plays judgment call 2's
case through the real match path against a scripted, non-family opponent. It
first asserts that the case occurs in the trace, then asserts the policy's
response. No test records or asserts an outcome.
"""

from __future__ import annotations

import random
from pathlib import Path
from types import MappingProxyType
from typing import Any

import pytest
from _e8_family_engine_harness import ARENA as ENGINE_ARENA
from _e8_family_engine_harness import SEATS, T8, T8L, Plan, play, sigma_of, with_index
from _e8_family_harness import (
    ACTIVE,
    ARENA,
    MEMBERS,
    MODES,
    PASSIVE,
    POLICY,
    center,
    make,
    miss,
    obs,
    seed_with,
    sense,
    write,
)
from battle_engine.agent_api import ActionKindV2, AgentAction, MatchContextV2, ObservationV2

from tools.research.v6.e8.family import package_id


def _issue_eight_discovery_senses(agent: Any) -> list[AgentAction]:
    """Tick 1: eight callbacks, every delivered discovery result empty. The eighth SENSE is c_0 again."""

    actions = [agent.act(obs(1))]
    actions += [agent.act(obs(1, sensed=())) for _ in range(7)]
    return actions


# ---------------------------------------------------------------------------
# Judgment call 2: the discovering callback is the delivery callback
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("member", ["REACQ8", "ADAPT8"])
def test_a_first_discovery_delivered_at_a_ticks_first_callback_is_verified_there(member: str) -> None:
    agent = make(member, mode=ACTIVE, rng_seed=seed_with(sigma=1, tau=1))
    issued = _issue_eight_discovery_senses(agent)
    # c_0 .. c_6, then c_0 again after seven empty results (PR8 Sec 2.5).
    assert issued == [sense(center(k % 7, 1)) for k in range(8)]
    found = center(0, 1)
    # Issuing the SENSE that will find the anchor discovers nothing: no result exists yet.
    assert not agent.discovered and agent.known == ()
    # Tick 2, callback 1: the result is delivered. First discovery happens here,
    # and verification applies here: a SENSE centered on the lowest known address.
    assert agent.act(obs(2, sensed=(found,))) == sense(found)
    assert agent.callback_index == 1 and agent.discovered and agent.known == (found,)
    assert agent.act(obs(2, sensed=(found,))) == write(found)  # the verification confirms it: disrupt


@pytest.mark.parametrize("member", ["REACQ8", "ADAPT8"])
def test_the_delivery_callback_picks_the_lowest_of_several_found(member: str) -> None:
    agent = make(member, mode=ACTIVE, rng_seed=seed_with(sigma=1, tau=1))
    _issue_eight_discovery_senses(agent)
    low, high = center(0, 1) - 10, center(0, 1) + 10
    assert agent.act(obs(2, sensed=(low, high))) == sense(low)  # KU-8


def test_adapt8s_discovery_result_is_not_a_verification_observation() -> None:
    agent = make("ADAPT8", mode=ACTIVE, rng_seed=seed_with(sigma=1, tau=1))
    _issue_eight_discovery_senses(agent)
    found = center(0, 1)
    agent.act(obs(2, sensed=(found,)))
    assert agent.adapt_count == 0  # a discovery result neither confirms nor relocates a
    agent.act(obs(2, sensed=(found,)))
    assert (agent.adapt_count, agent.switched) == (1, False)  # the verification SENSE's result does


def test_a_once_member_does_not_verify_at_the_delivery_callback() -> None:
    agent = make("RUSH8", mode=ACTIVE, rng_seed=seed_with(sigma=1, tau=1))
    _issue_eight_discovery_senses(agent)
    found = center(0, 1)
    assert agent.act(obs(2, sensed=(found,))) == write(found)  # the attack posture: disrupt the known anchor
    assert agent.discovered


@pytest.mark.parametrize("member", ["REACQ8", "ADAPT8"])
def test_a_first_discovery_delivered_at_a_later_callback_waits_for_the_next_tick(member: str) -> None:
    agent = make(member, mode=ACTIVE, rng_seed=seed_with(sigma=1, tau=1))
    assert agent.act(obs(1)) == sense(center(0, 1))
    found = center(0, 1)
    assert agent.act(obs(1, sensed=(found,))) == write(found)  # callback 2: no verification
    for _ in range(6):
        assert agent.act(miss(1)).kind is not ActionKindV2.SENSE
    assert agent.act(miss(2)) == sense(found)  # tick 2, callback 1


# The engine-level case. Under T8 the enemy sits in window c_1 and a hit right
# after the family's first chunk suppresses it for the rest of tick 1, so its
# discovering SENSE (its second) is its last callback of the tick. Under T8L a
# hit costs one offer, so the enemy sits in window c_6 and is found by the
# seventh and last callback. Either way the result is delivered at the family
# entrant's first callback of tick 2.
DISCOVERY_WINDOW = {T8: 1, T8L: 6}


def _delivery_case(tmp_path: Path, ruleset_id: str, member: str, seat: str) -> Any:
    sigma = sigma_of(7, seat)
    k = DISCOVERY_WINDOW[ruleset_id]
    base = 100
    enemy = (base + sigma * (91 + 55 * k)) % ENGINE_ARENA
    # The scripted opponent hits the family's anchor at its first offer after the
    # family's first chunk: its first callback in Seat B, its third in Seat A.
    hit = (1, 1) if seat == "A" else (1, 3)
    opponent = Plan(hits={hit: None}, repair=8)
    pid = package_id(member)
    pair = (pid, opponent) if seat == "A" else (opponent, pid)
    starts = (base, enemy) if seat == "A" else (enemy, base)
    return play(tmp_path, ruleset_id, *pair, starts=starts, ticks=3), enemy, k


@pytest.mark.parametrize("member", ["REACQ8", "ADAPT8", "RUSH8"])
@pytest.mark.parametrize("seat", SEATS)
@pytest.mark.parametrize("ruleset_id", [T8, T8L])
def test_engine_a_first_discovery_delivered_at_tick_twos_first_callback(
        tmp_path: Path, ruleset_id: str, seat: str, member: str) -> None:
    played, enemy, k = _delivery_case(tmp_path, ruleset_id, member, seat)
    decisions = with_index(played.decisions(seat))
    snaps = played.snaps[seat]
    tick1 = [record for _, record in decisions if record["observation"]["current_tick"] == 1]
    # The precondition, in the trace: tick 1's last family decision is the
    # discovering SENSE, the first to return an enemy anchor.
    senses = [record for record in tick1 if record["action"]["kind"] == "sense"]
    assert len(senses) == len(tick1) == k + 1
    assert [record["applied_result"]["sensed_anchors"] for record in senses] == [[]] * k + [[enemy]]
    assert not snaps[len(tick1) - 1].discovered  # issuing it discovered nothing
    # The response: at tick 2's first callback the result is delivered, and only there is it discovered.
    index, delivery = decisions[len(tick1)]
    snap = snaps[len(tick1)]
    assert delivery["observation"]["current_tick"] == 2 and index == 1
    assert delivery["observation"]["previous_sense_anchors"] == [enemy]
    assert snap.discovered and snap.known == (enemy,)
    if member == "RUSH8":
        assert delivery["action"] == {"kind": "write", "operand": enemy, "value": 1}  # once: no verification
    else:
        assert delivery["action"] == {"kind": "sense", "operand": enemy, "value": None}  # verification
        assert snap.purpose == "verify"
    if member == "ADAPT8":
        assert snap.adapt_count == 0


# ---------------------------------------------------------------------------
# Judgment call 3: ADAPT8's count is about the selected lowest address a
# ---------------------------------------------------------------------------


def _adapt8_knowing(low: int, high: int) -> Any:
    """ADAPT8 under active, having discovered ``low`` and ``high`` together at tick 1, callback 2."""

    agent = make("ADAPT8", mode=ACTIVE, rng_seed=seed_with(sigma=1, tau=1))
    assert agent.act(obs(1)) == sense(center(0, 1))
    agent.act(obs(1, sensed=(low, high)))
    for _ in range(6):
        agent.act(miss(1))
    return agent


def test_adapt8_active_another_known_anchor_missing_does_not_reset_the_count() -> None:
    agent = _adapt8_knowing(180, 200)
    assert agent.act(miss(2)) == sense(180)  # a is the lowest known address
    agent.act(obs(2, sensed=(180,)))  # 200 lies in the window and is missing; a is confirmed
    assert agent.adapt_count == 1 and agent.known == (180,)
    assert agent.replacements == {200: 180} and agent.search_address is None  # KU-7: replaced, no search
    for _ in range(6):
        agent.act(miss(2))
    assert agent.act(miss(3)) == sense(180)
    agent.act(obs(3, sensed=(180,)))
    assert (agent.adapt_count, agent.switched) == (2, True)


def test_adapt8_active_the_selected_anchor_missing_resets_the_count() -> None:
    agent = _adapt8_knowing(180, 200)
    agent.act(miss(2))
    agent.act(obs(2, sensed=(200,)))  # a = 180 is missing: an observed relocation
    assert agent.adapt_count == 0 and agent.known == (200,) and agent.replacements == {180: 200}


def test_adapt8_active_a_higher_anchor_that_becomes_a_is_then_the_one_counted() -> None:
    agent = _adapt8_knowing(180, 200)
    agent.act(miss(2))
    agent.act(obs(2, sensed=(200,)))  # 180 missing: 200 is now the selected a
    for _ in range(6):
        agent.act(miss(2))
    for tick, expected in ((3, 1), (4, 2)):
        assert agent.act(miss(tick)) == sense(200)
        agent.act(obs(tick, sensed=(200,)))
        assert agent.adapt_count == expected
        for _ in range(6):
            agent.act(miss(tick))
    assert agent.switched


def _adapt8_tracking(visible: tuple[int, ...]) -> Any:
    agent = make("ADAPT8", mode=PASSIVE, rng_seed=seed_with(sigma=1, tau=1))
    agent.act(obs(1))
    for _ in range(7):
        agent.act(obs(1, anchor=164, visible=visible))
    assert agent.adapt_count == 0
    return agent


def test_adapt8_passive_another_tracked_anchor_vanishing_does_not_reset_the_count() -> None:
    agent = _adapt8_tracking((180, 200))
    agent.act(obs(2, anchor=164, visible=(180,)))  # the first offer of tick 2: a = 180 is still visible
    assert agent.adapt_count == 1
    agent.act(obs(3, anchor=164, visible=(180,)))
    assert (agent.adapt_count, agent.switched) == (2, True)


def test_adapt8_passive_the_selected_anchor_vanishing_resets_the_count() -> None:
    agent = _adapt8_tracking((180, 200))
    agent.act(obs(2, anchor=164, visible=(200,)))  # a = 180 has left the visible set
    assert agent.adapt_count == 0


# ---------------------------------------------------------------------------
# Fixed detail 14: no parameters behaves as GREED8
# ---------------------------------------------------------------------------


def _reset(parameters: dict[str, Any], mode: str) -> Any:
    agent = POLICY.create_agent()
    agent.reset(MatchContextV2(agent_id="A", seed=0, arena_size=ARENA, tick_limit=1000, rng=random.Random(5),
                               parameters=MappingProxyType(parameters), detection_radius=32,
                               sensing_window=27 if mode == ACTIVE else None))
    return agent


def _script(mode: str) -> list[ObservationV2]:
    seen = {"visible": (300,)} if mode == PASSIVE else {}
    return [obs(tick, value=1, owner="B", **seen) for tick in range(1, 6) for _ in range(8)]


@pytest.mark.parametrize("mode", MODES)
def test_a_package_without_parameters_behaves_as_greed8(mode: str) -> None:
    empty, greed = _reset({}, mode), _reset(dict(MEMBERS["GREED8"]), mode)
    assert empty.declare_processes() == greed.declare_processes()
    script = _script(mode)
    actions = [empty.act(o) for o in script]
    assert actions == [greed.act(o) for o in script]
    assert {action.kind for action in actions} == {ActionKindV2.WRITE}  # paint, never SENSE or MOVE
