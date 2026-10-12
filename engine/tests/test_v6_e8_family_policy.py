"""V6 E8: the family policy as a state machine, on synthetic observations (phase I8-3).

docs/research/v6/V6_E8_ACTIVE_SPATIAL_SENSING_PREREGISTRATION.md (PR8) Sec 2.5
and 3.2, and the implementation plan Sec 5.2 to 5.6. The policy object is
driven with constructed ``ObservationV2`` sequences, so every transition is
pinned exactly: action for action, and where the registration names internal
state (the known set, missing addresses, replacements, the search, ADAPT8's
count), that state too. No match is played here.

Under ``"active"`` a SENSE's result reaches the next callback of the same
process as ``previous_sense_anchors`` (``sensed=``); under ``"passive"`` the
known set is the callback's ``visible`` set.
"""

from __future__ import annotations

import random
from typing import Any

import pytest
from _e8_family_harness import (
    ACTIVE,
    ARENA,
    BASE,
    BEACON,
    MODES,
    PASSIVE,
    center,
    dist,
    hit,
    make,
    miss,
    move,
    obs,
    own_write,
    paint_sequence,
    read,
    seed_with,
    sense,
    with_params,
    write,
)
from battle_engine.agent_api import ActionKindV2, AgentAction, ObservationV2

FAR = (BASE + 200) % ARENA  # a stationary enemy core base, at least 64 from BASE


def run(agent: Any, script: list[ObservationV2]) -> list[AgentAction]:
    return [agent.act(observation) for observation in script]


def beacon_a(tick: int, **kwargs: Any) -> ObservationV2:
    """The previous READ returned an intact core beacon owned by Seat A (the enemy of a Seat B agent)."""
    return obs(tick, value=BEACON, owner="A", **kwargs)


def probes(anchor: int) -> list[int]:
    """E6-A1 C-2's 17 verification READs around ``anchor``, in order."""
    return [anchor + 1] + [a for step in range(8, 65, 8) for a in (anchor + 1 - step, anchor + 1 + step)]


# ---------------------------------------------------------------------------
# Discovery (PR8 Sec 2.5; plan Sec 5.3)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("sigma", [-1, 1])
def test_the_seven_discovery_windows_tile_the_registered_arc(sigma: int) -> None:
    covered = [cell for k in range(7) for cell in range(ARENA) if dist(cell, center(k, sigma)) <= 27]
    assert len(covered) == len(set(covered)) == 385
    assert set(covered) == {(BASE + sigma * offset) % ARENA for offset in range(64, 449)}


@pytest.mark.parametrize("sigma", [-1, 1])
def test_active_discovery_senses_c0_to_c6_then_restarts_at_c0(sigma: int) -> None:
    agent = make("RUSH8", mode=ACTIVE, rng_seed=seed_with(sigma=sigma))
    actions = [agent.act(obs(1))] + [agent.act(obs(1 + i // 8, sensed=())) for i in range(1, 16)]
    expected = [sense(center(k % 7, sigma)) for k in range(16)]
    assert actions == expected  # seven empty results, then k = 0 again
    assert agent.known == () and not agent.discovered


@pytest.mark.parametrize("sigma", [-1, 1])
def test_discovery_stops_at_the_first_result_with_an_enemy_anchor(sigma: int) -> None:
    agent = make("RUSH8", mode=ACTIVE, rng_seed=seed_with(sigma=sigma))
    found = (center(2, sigma) + 5) % ARENA
    assert run(agent, [obs(1), obs(1, sensed=()), obs(1, sensed=())]) == [
        sense(center(0, sigma)), sense(center(1, sigma)), sense(center(2, sigma))]
    assert agent.act(obs(1, sensed=(found,))) == write(found)  # known: the attack disrupts it
    assert agent.known == (found,) and agent.discovered
    assert agent.act(obs(1)) == read(found + 1)  # then verification READs, never another discovery SENSE


def test_a_later_discovery_traversal_starts_again_at_c0() -> None:
    # Fixed detail (judgment call 1): the traversal "stops at the first result
    # containing an enemy anchor"; once nothing is known again, the member's
    # successive sensing actions are c_0, c_1, ... afresh.
    agent = make("REACQ8", mode=ACTIVE, rng_seed=seed_with(sigma=1, tau=1))
    a = 250
    assert run(agent, [obs(1), obs(1, sensed=())]) == [sense(center(0, 1)), sense(center(1, 1))]
    assert agent.act(obs(1, sensed=(a,))) == write(a)
    reads = run(agent, [miss(1) for _ in range(5)])
    assert reads == [read(x) for x in probes(a)[:5]]
    assert agent.act(miss(2)) == sense(a)  # tick 2, index 1: verification
    assert agent.act(obs(2, sensed=())) == sense(a + 46)  # missing: the search
    assert agent.act(obs(2, sensed=())) == sense(a - 46)
    # The third window is empty: a is unknown. The verification READ window
    # around the last-known anchor goes on until it is exhausted, then discovery.
    actions = [agent.act(obs(2, sensed=()))] + [agent.act(miss(2 + i // 8)) for i in range(40)]
    first_sense = next(i for i, action in enumerate(actions) if action.kind is ActionKindV2.SENSE)
    assert actions[:first_sense] == [read(x) for x in probes(a)[5:]]
    assert actions[first_sense] == sense(center(0, 1))


@pytest.mark.parametrize("sigma", [-1, 1])
def test_paced_acquisition_only_on_odd_callback_indexes(sigma: int) -> None:
    rng_seed = seed_with(sigma=sigma)
    side = make("PACED8", rng_seed=rng_seed).paint_side
    paint = paint_sequence(side, 8)
    passive = run(make("PACED8", mode=PASSIVE, rng_seed=rng_seed), [obs(tick) for tick in (1, 2) for _ in range(8)])
    assert passive == [move(64 * sigma) if index % 2 == 1 else write(paint[(tick - 1) * 4 + index // 2 - 1])
                       for tick in (1, 2) for index in range(1, 9)]
    agent = make("PACED8", mode=ACTIVE, rng_seed=rng_seed)
    active = [agent.act(obs(1))] + [agent.act(obs(1 + i // 8, sensed=() if i % 2 == 1 else None))
                                    for i in range(1, 16)]
    assert active == [sense(center((i // 2) % 7, sigma)) if i % 2 == 0 else write(paint[i // 2])
                      for i in range(16)]
    # The index restarts with the tick, even after an odd number of callbacks.
    agent = make("PACED8", mode=PASSIVE, rng_seed=rng_seed)
    assert run(agent, [obs(1), obs(1), obs(1), obs(2)]) == [move(64 * sigma), write(paint[0]), move(64 * sigma),
                                                          move(64 * sigma)]


@pytest.mark.parametrize("sigma", [-1, 1])
def test_passive_spatial_fast_is_e6s_full_stride_sweep(sigma: int) -> None:
    agent = make("RUSH8", mode=PASSIVE, rng_seed=seed_with(sigma=sigma))
    assert run(agent, [obs(tick) for tick in (1, 2) for _ in range(8)]) == [move(64 * sigma)] * 16


# ---------------------------------------------------------------------------
# Knowledge: KU-1 to KU-9 (PR8 Sec 2.5)
# ---------------------------------------------------------------------------


def _discovered(member: str, found: tuple[int, ...], *, tau: int = 1, sigma: int = 1) -> Any:
    """``member`` under active, having discovered ``found`` with its first SENSE (at tick 1, callback 2)."""

    agent = make(member, mode=ACTIVE, rng_seed=seed_with(sigma=sigma, tau=tau))
    assert agent.act(obs(1)) == sense(center(0, sigma))
    agent.act(obs(1, sensed=found))
    assert agent.known == tuple(sorted(found))
    return agent


def _to_tick_two_verification(agent: Any) -> AgentAction:
    """Finish tick 1 on misses; return tick 2's first action."""

    for _ in range(6):
        agent.act(miss(1))
    return agent.act(miss(2))


def test_ku2_every_returned_address_becomes_known() -> None:
    agent = _discovered("REACQ8", (180, 200))
    assert agent.known == (180, 200) and agent.discovered


def test_ku1_ku3_ku4_only_the_sensed_window_is_updated() -> None:
    # Known: 180, 207 (distance 27 from 180: inside) and 208 (28: outside).
    agent = _discovered("REACQ8", (180, 207, 208))
    assert _to_tick_two_verification(agent) == sense(180)  # KU-8: the lowest known address
    agent.act(obs(2, sensed=()))
    assert agent.known == (208,)  # 180 and 207 are missing; 208 is unchanged
    assert (agent.search_address, agent.missing) == (180, [207])


def test_ku7_a_missing_address_is_replaced_by_the_nearest_returned_one() -> None:
    agent = _discovered("REACQ8", (180, 200))
    assert _to_tick_two_verification(agent) == sense(180)
    agent.act(obs(2, sensed=(200,)))
    assert agent.known == (200,)
    assert agent.replacements == {180: 200}
    assert agent.search_address is None and agent.missing == []  # replaced: no search


def test_ku7_a_tie_goes_to_the_lower_address() -> None:
    agent = _discovered("REACQ8", (180,))
    assert _to_tick_two_verification(agent) == sense(180)
    agent.act(obs(2, sensed=(170, 190)))
    assert agent.replacements == {180: 170}
    agent = make("REACQ8", mode=ACTIVE)
    assert agent._nearest(0, (10, 502)) == 10  # a tie across the wrap: the lower numeric address
    assert agent._nearest(5, (20, 500)) == 20  # 15 against 17, circularly
    assert agent._nearest(500, (10, 490)) == 490  # 10 against 22


def test_ku6_missing_addresses_are_serviced_in_ascending_order() -> None:
    agent = _discovered("REACQ8", (180, 200), tau=1)
    assert _to_tick_two_verification(agent) == sense(180)
    rng_state = agent.rng.getstate()
    assert agent.act(obs(2, sensed=())) == sense(226)  # both missing: 180 first, tau = +1
    assert agent.missing == [200]
    assert agent.act(obs(2, sensed=())) == sense(134)
    # 180's search is exhausted; 200's starts, with a fresh tau.
    probe = random.Random()
    probe.setstate(rng_state)
    probe.randrange(2)
    tau = (-1, 1)[probe.randrange(2)]
    assert agent.act(obs(2, sensed=())) == sense(200 + 46 * tau)
    assert (agent.search_address, agent.missing) == (200, [])


@pytest.mark.parametrize("known", [(180, 450), (10, 500), (300, 310, 320)])
def test_ku8_ku9_verification_centers_on_the_lowest_numeric_address(known: tuple[int, ...]) -> None:
    agent = _discovered("REACQ8", known)
    assert _to_tick_two_verification(agent) == sense(min(known))


def test_ku5_passive_tracked_addresses_absent_from_view_become_missing() -> None:
    agent = make("REACQ8", mode=PASSIVE, rng_seed=seed_with(sigma=1, tau=1))
    assert agent.act(obs(1)) == move(64)
    assert agent.act(obs(1, anchor=164, visible=(180, 190))) == write(180)
    assert agent.act(obs(1, anchor=164, visible=(180, 190))) == write(190)
    # Both vanish at once: missing, no replacement; 180's search starts first.
    assert agent.act(obs(1, anchor=164)) == move(16)
    assert (agent.search_address, agent.missing) == (180, [190])


def test_ku5_ku7_passive_a_vanished_anchor_is_replaced_by_a_visible_one() -> None:
    # K-2: under passive no search starts while any enemy anchor is visible.
    agent = make("REACQ8", mode=PASSIVE, rng_seed=seed_with(sigma=1))
    agent.act(obs(1))
    agent.act(obs(1, anchor=164, visible=(180, 200)))
    agent.act(obs(1, anchor=164, visible=(180, 200)))
    agent.act(obs(1, anchor=164, visible=(200, 230)))
    assert agent.replacements == {180: 200}
    assert agent.search_address is None and agent.missing == []


def test_a_refused_sense_changes_nothing() -> None:
    # Unreachable in the family (every process declares reach 256, the largest
    # circular distance), pinned anyway: knowledge is unchanged, and the window
    # that was to be sensed is sensed next.
    agent = _discovered("REACQ8", (180,))
    assert _to_tick_two_verification(agent) == sense(180)
    agent.act(obs(2, applied=False, sensed=None))
    assert agent.known == (180,) and agent.search_address is None
    agent = make("RUSH8", mode=ACTIVE, rng_seed=seed_with(sigma=1))
    assert run(agent, [obs(1), obs(1, sensed=())]) == [sense(center(0, 1)), sense(center(1, 1))]
    assert agent.act(obs(1, applied=False, sensed=None)) == sense(center(1, 1))  # discovery: the same c_k
    agent = _discovered("REACQ8", (200,), tau=1)
    assert _to_tick_two_verification(agent) == sense(200)
    assert agent.act(obs(2, sensed=())) == sense(246)
    assert agent.act(obs(2, applied=False, sensed=None)) == sense(246)  # the search: the same window
    assert agent.act(obs(2, sensed=())) == sense(154)
    assert agent.act(obs(2, sensed=())).kind is ActionKindV2.READ  # exhausted after two sensed windows


# ---------------------------------------------------------------------------
# Passive and active knowledge persistence; the channel difference (K-4)
# ---------------------------------------------------------------------------


def test_passive_knowledge_is_only_the_current_visible_set() -> None:
    agent = make("RUSH8", mode=PASSIVE, rng_seed=seed_with(sigma=1))
    agent.act(obs(1))
    assert agent.act(obs(1, visible=(300,))) == write(300)
    assert agent.act(obs(2)) == read(301)  # out of view: not known, never disrupted; verification READs go on
    assert agent.known == () and agent.last_known == (300, 1)
    assert agent.act(obs(3)) == read(293)


def test_active_knowledge_persists_until_a_sense_replaces_it() -> None:
    agent = _discovered("RUSH8", (300,))
    reads = run(agent, [miss(1) for _ in range(6)])
    assert all(action.kind is ActionKindV2.READ for action in reads)
    for tick in (2, 3, 4):
        assert agent.act(miss(tick)) == write(300)  # remembered: disrupted once a tick, never re-sensed
        assert agent.act(miss(tick)).kind is ActionKindV2.READ
    assert agent.known == (300,)


@pytest.mark.parametrize("member", ["GUARD8", "EVADE8"])
def test_k4_passive_guard_members_resume_sweeping_when_they_lose_sight(member: str) -> None:
    agent = make(member, mode=PASSIVE, rng_seed=seed_with(sigma=1))
    assert agent.act(obs(1)) == move(64)
    assert agent.act(obs(1, visible=(300,))) == write(300)
    assert agent.act(obs(1, visible=(300,))) == write(BASE, BEACON)  # guard: repair
    assert agent.act(obs(1)) == move(64)  # out of view: discovery applies again
    assert agent.act(obs(1)) == move(64)
    assert agent.act(obs(1, visible=(320,))) == write(320)


@pytest.mark.parametrize("member", ["GUARD8", "EVADE8"])
def test_k4_active_guard_members_never_re_sense_a_remembered_anchor(member: str) -> None:
    agent = _discovered(member, (300,))
    actions = run(agent, [obs(1) for _ in range(6)]) + run(agent, [obs(t) for t in range(2, 6) for _ in range(8)])
    assert all(action.kind is not ActionKindV2.SENSE for action in actions)
    assert actions[0] == write(BASE, BEACON)  # 300 was disrupted at discovery: repair
    assert actions[6] == write(300)  # tick 2: the anchor first, once a tick
    assert actions[7:14] == [write(BASE + i % 8, BEACON) for i in range(6, 13)]


def test_k4_evade8_sweeps_after_its_own_evasion_under_passive() -> None:
    rng_seed = seed_with(sigma=1)
    agent = make("EVADE8", mode=PASSIVE, rng_seed=rng_seed)
    agent.act(obs(1))
    for _ in range(6):
        agent.act(obs(1, visible=(300,)))  # seven callbacks in tick 1: a hit is inferred at tick 2
    evasion = agent.act(obs(2, visible=(300,)))
    assert evasion.kind is ActionKindV2.MOVE
    assert agent.act(obs(2, anchor=BASE + evasion.operand)) == move(64)  # lost sight after its own move


# ---------------------------------------------------------------------------
# Initial acquisition ends at core confirmation (Revision 3): SPLIT8
# ---------------------------------------------------------------------------


def _split_confirms_core(agent: Any) -> None:
    """Drive SPLIT8 (passive) until its striker confirms the core at 300 over its sensor's written anchor."""

    assert agent.act(obs(1, pid="sensor")) == move(64)
    assert agent.act(obs(1, pid="striker")).kind is ActionKindV2.WRITE  # no acquisition: paint
    assert agent.act(obs(1, pid="sensor", visible=(300,))) == write(300)  # the sensor disrupts
    assert agent.act(obs(1, pid="striker", visible=(300,))) == read(301)
    assert agent.act(hit(1, pid="striker", visible=(300,))) == read(300)  # 301 hit: grow down
    assert agent.act(own_write("A", 1, pid="striker", visible=(300,))) == read(302)
    for address in (303, 304, 305, 306, 307):
        assert agent.act(hit(1, pid="striker", visible=(300,))) == read(address)
    assert agent.act(hit(1, pid="striker", visible=(300,))) == read(308)
    assert agent.enemy_core is None
    assert agent.act(miss(1, pid="striker", visible=(300,))).kind is ActionKindV2.WRITE
    assert agent.enemy_core == 300  # seven beacons over its own written anchor


def test_split8s_sensor_sweeps_while_the_core_is_unconfirmed_and_nothing_is_visible() -> None:
    agent = make("SPLIT8", mode=PASSIVE, rng_seed=seed_with(sigma=1))
    assert agent.act(obs(1, pid="sensor")) == move(64)
    assert agent.act(obs(1, pid="sensor", visible=(300,))) == write(300)
    # Out of view before confirmation: initial acquisition has not ended, so the
    # sensor sweeps again, although the anchor is remembered (K-1's remaining
    # difference from E6's SPLIT).
    assert agent.last_known == (300, 1) and agent.enemy_core is None
    assert agent.act(obs(1, pid="sensor")) == move(64)


def test_split8s_sensor_never_moves_again_once_its_entrant_confirms_the_core() -> None:
    agent = make("SPLIT8", mode=PASSIVE, rng_seed=seed_with(sigma=1))
    _split_confirms_core(agent)
    actions = run(agent, [obs(tick, pid=pid) for tick in range(3, 12) for pid in ("sensor", "striker", "striker",
                                                                                 "striker")])
    assert actions and all(action.kind is ActionKindV2.WRITE for action in actions)  # nothing visible: never a MOVE
    sensor = [a for a, pid in zip(actions, ["sensor", "striker", "striker", "striker"] * 9, strict=True)
              if pid == "sensor"]
    assert all(a.value == 1 and not 300 <= a.operand < 308 for a in sensor)  # the sensor paints


def test_split8s_striker_never_moves_or_acquires() -> None:
    for mode in MODES:
        agent = make("SPLIT8", mode=mode, rng_seed=seed_with(sigma=1))
        actions = run(agent, [obs(tick, pid="striker") for tick in range(1, 6) for _ in range(6)])
        assert all(action.kind is ActionKindV2.WRITE and action.value == 1 for action in actions)


def test_split8s_sensor_under_active_stops_sensing_once_anything_is_known() -> None:
    agent = make("SPLIT8", mode=ACTIVE, rng_seed=seed_with(sigma=1))
    assert agent.act(obs(1, pid="sensor")) == sense(center(0, 1))
    assert agent.act(obs(1, pid="striker")).kind is ActionKindV2.WRITE
    assert agent.act(obs(1, pid="sensor", sensed=(200,))) == write(200)
    actions = run(agent, [obs(tick, pid=pid) for tick in range(2, 6) for pid in ("sensor", "striker", "striker")])
    assert all(action.kind is not ActionKindV2.SENSE for action in actions)


@pytest.mark.parametrize("mode", MODES)
def test_attack_members_never_reach_acquisition_once_the_core_is_confirmed(mode: str) -> None:
    agent = make("RUSH8", mode=mode, seat="A")
    agent.act(obs(1, visible=(FAR,)) if mode == PASSIVE else obs(1))
    if mode == ACTIVE:
        return  # under active nothing is known at a first callback: no adoption (K-3)
    assert agent.enemy_core == FAR
    actions = run(agent, [obs(tick) for tick in range(1, 5) for _ in range(8)])
    assert all(action.kind is ActionKindV2.WRITE for action in actions)


# ---------------------------------------------------------------------------
# Re-acquisition precedence: RP-1 to RP-7, active
# ---------------------------------------------------------------------------


def _reacq_after_discovery(member: str = "REACQ8", *, tau: int = 1, parameters: dict[str, Any] | None = None) -> Any:
    agent = make(member, mode=ACTIVE, rng_seed=seed_with(sigma=1, tau=tau), parameters=parameters)
    assert agent.act(obs(1)) == sense(center(0, 1))
    assert agent.act(obs(1, sensed=(200,))) == write(200)
    for _ in range(6):
        agent.act(miss(1))
    return agent


@pytest.mark.parametrize("tau", [-1, 1])
def test_verification_then_the_second_and_third_windows_precede_the_posture_steps(tau: int) -> None:
    agent = _reacq_after_discovery(tau=tau)
    assert agent.act(miss(2)) == sense(200)  # tick 2, index 1: verification
    assert agent.act(obs(2, sensed=())) == sense(200 + 46 * tau)  # a missing, nothing returned: the search
    assert agent.act(obs(2, sensed=())) == sense(200 - 46 * tau)
    assert agent.act(obs(2, sensed=())) == read(probes(200)[6])  # exhausted: a is unknown; posture steps
    assert agent.known == () and agent.search_address is None


def test_the_search_ends_on_replacement_by_the_second_window() -> None:
    agent = _reacq_after_discovery(tau=1)
    assert agent.act(miss(2)) == sense(200)
    assert agent.act(obs(2, sensed=())) == sense(246)
    assert agent.act(obs(2, sensed=(240,))) == write(240)  # replaced: the search ends; disrupt it
    assert agent.replacements == {200: 240} and agent.search_address is None
    assert agent.known == (240,)


def test_rp2_a_search_continues_on_the_first_offer_of_a_later_tick() -> None:
    agent = _reacq_after_discovery(tau=1)
    assert agent.act(miss(2)) == sense(200)
    assert agent.act(obs(2, sensed=())) == sense(246)
    # Suppressed for the rest of tick 2 and all of tick 3. At tick 4's first
    # offer the search continues; verification of the stale address does not restart.
    assert agent.act(obs(4, sensed=())) == sense(154)
    assert agent.act(obs(4, sensed=(150,))) == write(150)


def test_the_search_takes_precedence_over_core_writes() -> None:
    agent = make("REACQ8", mode=ACTIVE, rng_seed=seed_with(sigma=1, tau=1))
    agent.act(obs(1))
    assert agent.act(obs(1, sensed=(200,))) == write(200)
    assert agent.act(obs(1)) == read(201)
    assert agent.act(hit(1)) == read(200)
    assert agent.act(own_write("A", 1)) == read(202)
    for address in (203, 204, 205, 206):
        assert agent.act(hit(1)) == read(address)
    assert agent.act(hit(2)) == sense(200)  # tick 2, index 1: verification precedes the scan
    assert agent.act(obs(2, sensed=())) == sense(246)  # and the search precedes it too
    assert agent.act(obs(2, sensed=())) == sense(154)
    assert agent.act(obs(2, sensed=())) == read(207)  # exhausted: the posture's scan resumes


def test_rp5_a_pending_evasion_keeps_its_priority_over_a_search() -> None:
    # A synthetic setting (no family member both evades and re-acquires):
    # RP-5's order in the shared source.
    agent = _reacq_after_discovery(tau=1, parameters=with_params("REACQ8", evade="on-hit"))
    assert agent.act(miss(2)) == sense(200)
    assert agent.act(obs(2, sensed=())) == sense(246)
    evasion = agent.act(obs(4, sensed=()))  # tick 3 had no callback: an inferred hit
    assert evasion.kind is ActionKindV2.MOVE and 8 <= abs(evasion.operand) <= 64
    assert agent.act(obs(4)) == sense(154)  # the search resumes next


def test_a_once_member_neither_verifies_nor_searches() -> None:
    agent = _reacq_after_discovery("RUSH8")
    actions = run(agent, [miss(tick) for tick in range(2, 5) for _ in range(8)])
    assert all(action.kind is not ActionKindV2.SENSE for action in actions)


# ---------------------------------------------------------------------------
# Re-acquisition, passive: MOVE toward a, a + tau 46, a - tau 46
# ---------------------------------------------------------------------------


def _passive_reacq(tau: int, member: str = "REACQ8") -> Any:
    agent = make(member, mode=PASSIVE, rng_seed=seed_with(sigma=1, tau=tau))
    assert agent.act(obs(1)) == move(64)
    assert agent.act(obs(1, anchor=164, visible=(180,))) == write(180)
    assert agent.act(obs(1, anchor=164, visible=(180,))) == read(181)
    return agent


@pytest.mark.parametrize("tau", [-1, 1])
def test_the_passive_search_moves_toward_each_center_and_is_exhausted_at_the_last(tau: int) -> None:
    agent = _passive_reacq(tau)
    assert agent.act(obs(1, anchor=164)) == move(16)  # toward a = 180
    assert agent.act(obs(1, anchor=180)) == move(46 * tau)  # reached; toward a + tau 46
    second, third = 180 + 46 * tau, 180 - 46 * tau
    assert agent.act(obs(1, anchor=second)) == move(-64 * tau)  # 92 away: at most 64 per MOVE
    assert agent.act(obs(1, anchor=second - 64 * tau)) == move(-28 * tau)
    assert agent.act(obs(1, anchor=third)) == read(173)  # the last center, nothing visible: exhausted
    assert agent.search_address is None and agent.known == ()


def test_the_passive_search_ends_on_the_first_visible_anchor() -> None:
    agent = _passive_reacq(1)
    assert agent.act(obs(1, anchor=164)) == move(16)
    assert agent.act(obs(1, anchor=180)) == move(46)
    assert agent.act(obs(1, anchor=226, visible=(240,))) == write(240)
    assert agent.replacements == {180: 240} and agent.search_address is None


def test_cq8_2_rush8_and_reacq8_agree_until_the_first_trigger() -> None:
    script = [obs(1), obs(1, anchor=164, visible=(180,)), obs(1, anchor=164, visible=(180,)),
              obs(2, anchor=164, visible=(180,)), obs(2, anchor=164)]
    rush = run(make("RUSH8", mode=PASSIVE, rng_seed=seed_with(sigma=1)), script)
    reacq = run(make("REACQ8", mode=PASSIVE, rng_seed=seed_with(sigma=1)), script)
    assert rush[:4] == reacq[:4]
    assert (rush[4], reacq[4]) == (read(173), move(16))  # the trigger: 180 is missing


# ---------------------------------------------------------------------------
# ADAPT8: consecutive verification observations, k = 2 (R-8)
# ---------------------------------------------------------------------------


def test_adapt8_active_switches_at_the_second_consecutive_confirmation() -> None:
    agent = _reacq_after_discovery("ADAPT8")
    assert agent.act(miss(2)) == sense(200)
    assert agent.act(obs(2, sensed=(200,))) == write(200)
    assert (agent.adapt_count, agent.switched) == (1, False)
    for _ in range(6):
        agent.act(miss(2))
    assert agent.act(miss(3)) == sense(200)
    assert agent.act(obs(3, sensed=(200,))) == write(200)
    assert (agent.adapt_count, agent.switched) == (2, True)
    for _ in range(6):
        agent.act(miss(3))
    actions = run(agent, [miss(tick) for tick in range(4, 8) for _ in range(8)])
    assert all(action.kind is not ActionKindV2.SENSE for action in actions)  # as once: no verification


def test_adapt8_active_an_unobserved_tick_neither_advances_nor_resets_the_count() -> None:
    agent = _reacq_after_discovery("ADAPT8")
    agent.act(miss(2))
    agent.act(obs(2, sensed=(200,)))
    assert agent.adapt_count == 1
    # No callback at all in ticks 3 and 4.
    assert agent.act(miss(5)) == sense(200)
    assert agent.adapt_count == 1
    agent.act(obs(5, sensed=(200,)))
    assert (agent.adapt_count, agent.switched) == (2, True)


def test_adapt8_active_a_verification_delivered_after_suppression_still_counts() -> None:
    agent = _reacq_after_discovery("ADAPT8")
    assert agent.act(miss(2)) == sense(200)
    # Suppressed for the rest of tick 2 and all of tick 3: the result arrives
    # at tick 4's first callback, which then verifies again.
    assert agent.act(obs(4, sensed=(200,))) == sense(200)
    assert agent.adapt_count == 1
    agent.act(obs(4, sensed=(200,)))
    assert (agent.adapt_count, agent.switched) == (2, True)


def test_adapt8_active_an_observed_relocation_resets_the_count() -> None:
    agent = _reacq_after_discovery("ADAPT8")
    agent.act(miss(2))
    agent.act(obs(2, sensed=(200,)))
    for _ in range(6):
        agent.act(miss(2))
    assert agent.adapt_count == 1
    assert agent.act(miss(3)) == sense(200)
    assert agent.act(obs(3, sensed=(220,))) == write(220)  # 200 missing, replaced by 220
    assert (agent.adapt_count, agent.switched) == (0, False)
    for _ in range(6):
        agent.act(miss(3))
    for tick, expected in ((4, 1), (5, 2)):
        assert agent.act(miss(tick)) == sense(220)
        agent.act(obs(tick, sensed=(220,)))
        assert agent.adapt_count == expected
        for _ in range(6):
            agent.act(miss(tick))
    assert agent.switched


def test_adapt8_active_a_first_callback_during_a_search_is_not_a_verification() -> None:
    agent = _reacq_after_discovery("ADAPT8")
    agent.act(miss(2))
    assert agent.act(obs(2, sensed=())) == sense(246)  # relocation: count 0, and the search
    assert agent.adapt_count == 0
    assert agent.act(obs(4, sensed=())) == sense(154)  # tick 4's first callback continues the search
    assert agent.adapt_count == 0
    assert agent.act(obs(4, sensed=(160,))) == write(160)
    assert agent.adapt_count == 0  # a search window is not a verification observation


def _passive_adapt() -> Any:
    agent = make("ADAPT8", mode=PASSIVE, rng_seed=seed_with(sigma=1, tau=1))
    agent.act(obs(1))
    agent.act(obs(1, anchor=164, visible=(180,)))
    for _ in range(6):
        agent.act(obs(1, anchor=164, visible=(180,)))
    assert agent.adapt_count == 0  # no observation yet: tick 1 had no first offer with anything tracked
    return agent


def test_adapt8_passive_the_first_offer_of_a_tick_is_the_observation() -> None:
    agent = _passive_adapt()
    agent.act(obs(2, anchor=164, visible=(180,)))
    assert agent.adapt_count == 1
    for _ in range(7):
        agent.act(obs(2, anchor=164, visible=(180,)))
    assert agent.adapt_count == 1  # later offers of the tick are not observations
    agent.act(obs(3, anchor=164, visible=(180,)))
    assert (agent.adapt_count, agent.switched) == (2, True)
    # As once: a lost anchor no longer starts a search toward it. The core is
    # unconfirmed, so once the verification READ window is exhausted, initial
    # acquisition (E6's sweep) applies again.
    actions = run(agent, [obs(3, anchor=164) for _ in range(6)])
    assert agent.search_address is None and agent.missing == []
    assert move(16) not in actions
    assert [a.kind for a in actions] == [ActionKindV2.READ] * 4 + [ActionKindV2.MOVE] * 2
    assert actions[4:] == [move(64), move(64)]


def test_adapt8_passive_a_relocation_at_any_callback_resets_and_unobserved_ticks_do_nothing() -> None:
    agent = _passive_adapt()
    agent.act(obs(2, anchor=164, visible=(180,)))
    assert agent.adapt_count == 1
    agent.act(obs(2, anchor=164, visible=(190,)))  # 180 missing at a later offer: relocation
    assert agent.adapt_count == 0
    agent.act(obs(3, anchor=164, visible=(190,)))
    assert agent.adapt_count == 1
    # Ticks 4 and 5: no callback.
    agent.act(obs(6, anchor=164, visible=(190,)))
    assert (agent.adapt_count, agent.switched) == (2, True)


def test_adapt8_passive_before_its_switch_searches_like_reacq8() -> None:
    agent = _passive_adapt()
    assert agent.act(obs(2, anchor=164)) == move(16)
    assert agent.adapt_count == 0 and agent.search_address == 180


# ---------------------------------------------------------------------------
# EVADE8: hit inference, fresh draws, repetition (PR8 Sec 3.2)
# ---------------------------------------------------------------------------

EVADE_SEED = 11


def _evasion_draws(count: int, rng_seed: int = EVADE_SEED) -> list[AgentAction]:
    """The first ``count`` evasions a fresh stream gives: sigma_e, then m, after the two reset draws."""

    reference = random.Random(rng_seed)
    reference.randrange(2), reference.randrange(2)
    moves = []
    for _ in range(count):
        sign = (-1, 1)[reference.randrange(2)]
        moves.append(move(sign * reference.randint(8, 64)))
    return moves


@pytest.mark.parametrize("mode", MODES)
def test_evade8_never_infers_a_hit_at_its_first_callback_of_the_match(mode: str) -> None:
    rng = random.Random(EVADE_SEED)
    agent = make("EVADE8", mode=mode, rng=rng)
    state = rng.getstate()
    assert agent.act(obs(3)).kind is not ActionKindV2.MOVE or mode == PASSIVE  # P8-5: no earlier tick
    assert rng.getstate() == state or mode == PASSIVE
    if mode == PASSIVE:
        assert agent.act(obs(3)) == move(64 * agent.direction)  # the passive sweep, not an evasion
    assert agent.previous_tick is None


@pytest.mark.parametrize("mode", MODES)
def test_evade8_infers_a_hit_from_a_tick_without_a_callback(mode: str) -> None:
    agent = make("EVADE8", mode=mode, rng_seed=EVADE_SEED)
    run(agent, [obs(1) for _ in range(8)])
    assert agent.act(obs(3)) == _evasion_draws(1)[0]  # (i): tick 2 had no callback


@pytest.mark.parametrize("mode", MODES)
def test_evade8_infers_a_hit_from_fewer_than_eight_callbacks(mode: str) -> None:
    agent = make("EVADE8", mode=mode, rng_seed=EVADE_SEED)
    run(agent, [obs(1) for _ in range(7)])
    assert agent.act(obs(2)) == _evasion_draws(1)[0]  # (ii): seven callbacks in tick 1


@pytest.mark.parametrize("mode", MODES)
def test_evade8_infers_nothing_after_a_full_tick(mode: str) -> None:
    rng = random.Random(EVADE_SEED)
    agent = make("EVADE8", mode=mode, rng=rng)
    if mode == PASSIVE:
        run(agent, [obs(1, visible=(300,)) for _ in range(8)])
    else:
        run(agent, [obs(1), obs(1, sensed=(300,))] + [obs(1) for _ in range(6)])
    state = rng.getstate()
    assert agent.act(obs(2, visible=(300,))) == write(300)  # no hit inferred: the guard posture
    assert rng.getstate() == state


@pytest.mark.parametrize("mode", MODES)
def test_evade8_draws_fresh_for_every_evasion_and_repeats_on_every_hit(mode: str) -> None:
    rng = random.Random(EVADE_SEED)
    agent = make("EVADE8", mode=mode, rng=rng)
    moves = []
    run(agent, [obs(1) for _ in range(5)])
    moves.append(agent.act(obs(2)))  # (ii)
    run(agent, [obs(2) for _ in range(7)])
    moves.append(agent.act(obs(4)))  # (i)
    run(agent, [obs(4) for _ in range(3)])
    moves.append(agent.act(obs(5)))  # (ii)
    assert moves == _evasion_draws(3)
    assert len(set(moves)) == 3
    # Sigma and the paint side at reset; sigma_e then m at each evasion; nothing else.
    reference = random.Random(EVADE_SEED)
    reference.randrange(2), reference.randrange(2)
    for _ in range(3):
        reference.randrange(2), reference.randint(8, 64)
    assert rng.getstate() == reference.getstate()


def test_guard8_and_evade8_agree_until_the_first_inferred_hit() -> None:
    script = [obs(1)] + [obs(1, visible=(300,)) for _ in range(6)] + [obs(2, visible=(300,))]
    guard = run(make("GUARD8", mode=PASSIVE, rng_seed=5), script)
    evade = run(make("EVADE8", mode=PASSIVE, rng_seed=5), script)
    assert guard[:7] == evade[:7]
    assert evade[7].kind is ActionKindV2.MOVE and guard[7] == write(300)


# ---------------------------------------------------------------------------
# STRESS8: the tick- and callback-keyed check and the beacon repair (PR8 Sec 3.2)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("mode", MODES)
def test_stress8_checks_own_core_cell_t_minus_1_mod_8_at_each_first_callback(mode: str) -> None:
    agent = make("STRESS8", mode=mode)
    for tick in range(1, 18):
        assert agent.act(obs(tick, value=BEACON, owner="A")) == read(BASE + (tick - 1) % 8)
        assert agent.act(obs(tick, value=BEACON, owner="A")).value == BEACON  # undamaged: the guard posture


@pytest.mark.parametrize("owner", ["B", None])
@pytest.mark.parametrize("mode", MODES)
def test_stress8_repairs_a_damaged_checked_cell_with_the_core_beacon_next(mode: str, owner: str | None) -> None:
    agent = make("STRESS8", mode=mode)
    assert agent.act(obs(4)) == read(BASE + 3)
    assert agent.act(obs(4, value=1, owner=owner)) == write(BASE + 3, BEACON)
    assert agent.act(obs(4)) == write(BASE, BEACON)  # then the guard posture's cyclic repair
    assert agent.guard_cursor == 1  # the beacon repair does not move the guard cursor


@pytest.mark.parametrize("mode", MODES)
def test_stress8_drops_a_stale_obligation_at_a_new_ticks_first_callback(mode: str) -> None:
    agent = make("STRESS8", mode=mode)
    assert agent.act(obs(1)) == read(BASE)
    # Unreachable in the engine (P8-6), pinned anyway: the check's result
    # arrives at a new tick's first callback. The check comes first.
    assert agent.act(obs(2, value=1, owner="B")) == read(BASE + 1)
    assert agent.act(obs(2, value=BEACON, owner="A")) == write(BASE, BEACON)  # no repair of BASE + 0 is owed


@pytest.mark.parametrize("mode", MODES)
def test_stress8_a_tick_without_a_callback_skips_its_cell(mode: str) -> None:
    agent = make("STRESS8", mode=mode)
    checked = []
    for tick in (1, 2, 4, 5, 9):
        checked.append(agent.act(obs(tick, value=BEACON, owner="A")).operand)
        agent.act(obs(tick, value=BEACON, owner="A"))
    assert checked == [BASE + 0, BASE + 1, BASE + 3, BASE + 4, BASE + 0]


@pytest.mark.parametrize("mode", MODES)
def test_stress8_disrupts_a_known_anchor_after_its_check(mode: str) -> None:
    agent = make("STRESS8", mode=mode)
    seen = {"visible": (300,)} if mode == PASSIVE else {}
    assert agent.act(obs(1, **seen)) == read(BASE)
    second = agent.act(obs(1, value=BEACON, owner="A", **seen))
    assert second == (write(300) if mode == PASSIVE else write(BASE, BEACON))  # under active nothing is ever known


# ---------------------------------------------------------------------------
# E6 parity under passive: posture, verification, core cursor and adoption
# (E6 plan Sec 5.2 as corrected by E6 amendment 1), ported from
# test_v6_e6_family.py to the E8 members.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("anchor", [BASE + 64, BASE - 64, BASE + 256, (BASE + 300) % ARENA])
def test_e6_a_single_far_anchor_at_seat_as_tick_one_first_callback_is_adopted(anchor: int) -> None:
    agent = make("LURK8", seat="A")
    assert [agent.act(obs(1, visible=(anchor,))) for _ in range(8)] == [write(anchor + i) for i in range(8)]


@pytest.mark.parametrize("anchor", [BASE + 63, BASE - 63, BASE + 32, BASE + 1])
def test_e6_an_anchor_closer_than_64_is_not_adopted(anchor: int) -> None:
    agent = make("LURK8")
    assert agent.act(obs(1, visible=(anchor,))) == write(anchor)
    assert agent.act(obs(1, visible=(anchor,))) == read(anchor + 1)


def test_e6_seat_b_and_later_callbacks_never_adopt() -> None:
    for agent in (make("LURK8", seat="B"), make("LURK8", seat="A")):
        if agent.me == "A":
            agent.act(obs(1))
        assert agent.act(obs(1, visible=(FAR,))) == write(FAR)
        assert agent.act(obs(1, visible=(FAR,))) == read(FAR + 1)
        assert agent.enemy_core is None
    agent = make("LURK8", seat="A")
    assert agent.act(obs(1, visible=(300, 400))) == write(300)  # two known: not adopted
    assert agent.act(obs(1, visible=(300, 400))) == write(400)
    assert agent.act(obs(1, visible=(300, 400))) == read(301)


def test_e6_the_window_order_and_extent() -> None:
    agent = make("LURK8")
    agent.act(obs(1))
    agent.act(obs(1, visible=(300,)))
    assert [agent.act(miss(1 + i // 8)) for i in range(17)] == [read(a) for a in probes(300)]


def test_e6_verification_grows_the_run_down_and_up_and_confirms_eight() -> None:
    agent = make("LURK8")
    agent.act(obs(1))
    seen = (300,)
    assert agent.act(obs(1, visible=seen)) == write(300)
    assert agent.act(obs(1, visible=seen)) == read(301)
    assert agent.act(miss(1, visible=seen)) == read(293)
    assert agent.act(miss(1, visible=seen)) == read(309)
    assert agent.act(hit(1, visible=seen)) == read(308)
    assert agent.act(hit(1, visible=seen)) == read(307)
    assert agent.act(hit(1, visible=seen)) == read(306)
    assert agent.act(miss(2, visible=seen)) == write(300)
    assert agent.act(obs(2, visible=seen)) == read(310)
    for address in (311, 312, 313, 314):
        assert agent.act(hit(2, visible=seen)) == read(address)
    assert agent.act(hit(2, visible=seen)) == write(307)
    assert agent.enemy_core == 307


def test_e6_an_overwritten_anchor_on_core_cell_0_stands_in_for_it() -> None:
    agent = make("LURK8", seat="B")
    seen = (300,)
    assert agent.act(obs(1, visible=seen)) == write(300)
    assert agent.act(obs(1, visible=seen)) == read(301)
    assert agent.act(beacon_a(1, visible=seen)) == read(300)
    assert agent.act(own_write("B", 1, visible=seen)) == read(302)
    for address in (303, 304, 305, 306):
        assert agent.act(beacon_a(1, visible=seen)) == read(address)
    assert agent.act(beacon_a(2, visible=seen)) == write(300)
    assert agent.act(obs(2, visible=seen)) == read(307)
    assert agent.act(beacon_a(2, visible=seen)) == read(308)
    assert agent.act(miss(2, visible=seen)) == write(301)
    assert agent.enemy_core == 300


def test_e6_an_anchor_just_below_the_core_is_not_taken_for_core_cell_0() -> None:
    agent = make("LURK8", seat="B")
    seen = (299,)
    assert agent.act(obs(1, visible=seen)) == write(299)
    assert agent.act(obs(1, visible=seen)) == read(300)
    assert agent.act(beacon_a(1, visible=seen)) == read(299)
    assert agent.act(own_write("B", 1, visible=seen)) == read(301)
    for address in (302, 303, 304, 305):
        assert agent.act(beacon_a(1, visible=seen)) == read(address)
    assert agent.act(beacon_a(2, visible=seen)) == write(299)
    assert agent.act(obs(2, visible=seen)) == read(306)
    assert agent.act(beacon_a(2, visible=seen)) == read(307)
    assert agent.act(beacon_a(2, visible=seen)) == write(300)
    assert agent.enemy_core == 300


def test_e6_seven_beacons_over_a_cell_that_is_not_a_written_anchor_stay_unconfirmed() -> None:
    agent = make("LURK8", seat="B")
    seen = (292,)
    assert agent.act(obs(1, visible=seen)) == write(292)
    assert agent.act(obs(1, visible=seen)) == read(293)
    assert agent.act(miss(1, visible=seen)) == read(285)
    assert agent.act(miss(1, visible=seen)) == read(301)
    assert agent.act(beacon_a(1, visible=seen)) == read(300)
    assert agent.act(own_write("B", 1, visible=seen)) == read(302)
    for address in (303, 304):
        assert agent.act(beacon_a(1, visible=seen)) == read(address)
    assert agent.act(beacon_a(2, visible=seen)) == write(292)
    for address in (305, 306, 307, 308):
        assert agent.act(beacon_a(2, visible=seen)) == read(address)
    assert agent.act(miss(2, visible=seen)) == read(277)
    assert agent.enemy_core is None


def test_e6_an_exhausted_window_forgets_the_anchor_and_acquisition_resumes() -> None:
    agent = make("RUSH8", rng_seed=seed_with(sigma=1))
    assert agent.act(obs(1)) == move(64)
    assert agent.act(obs(1, visible=(300,))) == write(300)
    for i in range(17):
        agent.act(miss(1 + i // 8))
    assert agent.act(miss(4)) == move(64)
    assert agent.last_known is None


def test_e6_own_or_unowned_beacons_are_not_hits() -> None:
    agent = make("LURK8")
    agent.act(obs(1))
    agent.act(obs(1, visible=(300,)))
    assert agent.act(miss(1)) == read(301)
    assert agent.act(obs(1, value=BEACON, owner="A")) == read(293)
    assert agent.act(obs(1, value=BEACON, owner=None)) == read(309)
    assert agent.act(obs(1, value=BEACON, owner="B", applied=False)) == read(285)


def test_e6_the_core_cursor_rotates_the_omitted_cell_across_ticks() -> None:
    agent = make("LURK8", seat="A")
    assert [agent.act(obs(1, visible=(FAR,))) for _ in range(8)] == [write(FAR + i) for i in range(8)]
    assert agent.act(obs(1, visible=(FAR,))) == write(paint_sequence(agent.paint_side, 1)[0])
    moved = FAR + 20
    omitted = []
    for tick in range(2, 10):
        actions = [agent.act(obs(tick, visible=(moved,))) for _ in range(8)]
        assert actions[0] == write(moved)
        cells = [action.operand - FAR for action in actions[1:]]
        assert len(set(cells)) == 7 and set(cells) <= set(range(8))
        (missing,) = set(range(8)) - set(cells)
        omitted.append(missing)
    assert omitted == [7, 6, 5, 4, 3, 2, 1, 0]


def test_e6_guard_disrupts_on_sight_and_otherwise_repairs_cyclically_across_ticks() -> None:
    agent = make("GUARD8", mode=PASSIVE)
    seen = (200,)
    assert agent.act(obs(1, visible=seen)) == write(200)
    assert [agent.act(obs(1, visible=seen)) for _ in range(4)] == [write(BASE + i, BEACON) for i in range(4)]
    assert agent.act(obs(2, visible=seen)) == write(200)
    assert [agent.act(obs(2, visible=seen)) for _ in range(5)] == [write(BASE + i, BEACON) for i in (4, 5, 6, 7, 0)]


@pytest.mark.parametrize("side", [0, 1])
def test_e6_paint_writes_outward_alternating_sides_and_covers_504_cells(side: int) -> None:
    agent = make("GREED8", rng_seed=seed_with(side=side))
    actions = [agent.act(obs(1 + i // 8, visible=(300,))) for i in range(505)]
    cells = paint_sequence(side, 504)
    assert len(set(cells)) == 504 and set(cells).isdisjoint({BASE + i for i in range(8)})
    assert [a.operand for a in actions[:504]] == cells
    assert actions[504] == actions[0]


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("sigma", [-1, 1])
def test_e6_the_read_search_probes_the_whole_arc_in_order_and_never_moves(sigma: int, mode: str) -> None:
    agent = make("STEALTH8", mode=mode, rng_seed=seed_with(sigma=sigma))
    expected = [read(BASE + sigma * (64 + 8 * m)) for m in range(49)] + [read(BASE + sigma * 64)]
    assert [agent.act(miss(1 + i // 8)) for i in range(50)] == expected


def test_e6_a_read_search_hit_is_grown_into_an_eight_cell_run_then_attacked() -> None:
    agent = make("STEALTH8", rng_seed=seed_with(sigma=1))
    assert agent.act(miss(1)) == read(164)
    assert agent.act(miss(1)) == read(172)
    assert agent.act(hit(1)) == read(171)
    for address in (170, 169, 168, 167):
        assert agent.act(hit(1)) == read(address)
    assert agent.act(miss(1)) == read(173)
    assert agent.act(hit(2)) == read(174)
    assert agent.act(hit(2)) == read(175)
    assert agent.act(hit(2)) == write(168)
    assert agent.enemy_core == 168


@pytest.mark.parametrize("member", ["LURK8", "GREED8", "STRESS8"])
def test_members_without_acquisition_never_move_or_sense(member: str) -> None:
    for mode in MODES:
        agent = make(member, mode=mode, rng_seed=seed_with(sigma=1))
        actions = run(agent, [obs(tick) for tick in range(1, 5) for _ in range(8)])
        assert all(action.kind in (ActionKindV2.WRITE, ActionKindV2.READ) for action in actions)


def test_lurk8_and_greed8_act_identically_without_information() -> None:
    for mode in MODES:
        lurk = run(make("LURK8", mode=mode, rng_seed=9), [obs(tick) for tick in range(1, 6) for _ in range(8)])
        greed = run(make("GREED8", mode=mode, rng_seed=9), [obs(tick) for tick in range(1, 6) for _ in range(8)])
        assert lurk == greed
