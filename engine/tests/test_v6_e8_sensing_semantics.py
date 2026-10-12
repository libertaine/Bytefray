"""V6 E8: the SENSE action, active sensing, delivery and the trace's presence contract (phase I8-2).

docs/research/v6/V6_E8_ACTIVE_SPATIAL_SENSING_PREREGISTRATION.md (PR8) Sec 2.1,
2.3 and 10, and the implementation plan Sec 4.2, 4.3 and 4.6. What is proven
here, under T8 and T8L (and, for the controls' side, C8 and C8L):

* **The window** (Sec 2.3). A SENSE at *t* returns the ascending tuple of
  distinct positions of the processes of every other live entrant with
  circular distance <= 27 from ``t mod 512``: inclusive at exactly 27, across
  the wrap, co-located anchors once, suppressed enemy processes included, the
  acting entrant's own processes and a dead entrant's never.
* **The action.** Reach is checked as for READ; one SENSE is one offer; it
  changes nothing in the match; the sensed entrant's observations are
  unchanged; under ``"active"`` the passive visible set is empty.
* **Delivery** (Sec 10's delivery tests, under both treatments): the next
  offer in the same chunk, the next tick, after suppression for the rest of
  the tick, and the two genuinely terminal cases.
* **The three serialization states** and their transitions: an absent field,
  an explicit ``null``, and a list (including ``[]``), checked by the
  independent oracle of ``_e8_sensing_harness`` both ways.

Every scenario uses scripted executors with explicit positions. None is an E8
family member, and no outcome is asserted.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
from _e8_sensing_harness import (
    ARENA,
    CONTROLS,
    QUOTA,
    TREATMENTS,
    WINDOW,
    Scripted,
    e8_keys_in,
    ids,
    presence_problems,
    process,
    read,
    run_traced,
    sense,
    status_problems,
    write,
)
from battle_engine.agent_api import ActionKindV2, AgentAction
from battle_engine.agent_trace import ABSENT, read_trace_v2
from battle_engine.config import Config
from battle_engine.process_runtime import ProcessEntrantSpec, ProcessMatchController
from battle_engine.ruleset_policy import RulesetPolicy


def _dist(a: int, b: int) -> int:
    d = abs(a - b) % ARENA
    return min(d, ARENA - d)


def sensed(policy: RulesetPolicy, target: int, enemies: list[int], *, own: tuple[int, ...] = (),
           enemy_alive: bool = True, suppressed: bool = False) -> tuple[int, ...]:
    """What a SENSE at ``target`` by seat A returns, with seat B's processes at ``enemies``."""

    log: list[tuple[str, int, int]] = []
    a = [process(f"a{i}", position, 200, QUOTA if i == 0 else 0, Scripted(f"a{i}", log))
         for i, position in enumerate([100, *own])]
    b = [process(f"b{i}", position, 1, QUOTA if i == 0 else 0, Scripted(f"b{i}", log))
         for i, position in enumerate(enemies)]
    controller = ProcessMatchController(
        Config(seed=1, arena_size=ARENA, instr_per_tick=QUOTA),
        [ProcessEntrantSpec("A", "A", a, start=0), ProcessEntrantSpec("B", "B", b, start=256)], 1,
        ruleset_policy=policy)
    controller._states_by_agent_id["B"].alive = enemy_alive
    if suppressed:
        for p in b:
            p.disrupted_until_tick = 2
    return controller._sensed_anchors(controller.entrant_specs[0], target % ARENA)


# ---------------------------------------------------------------------------
# The window (PR8 Sec 2.3)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("policy", TREATMENTS, ids=ids)
def test_the_window_is_inclusive_at_exactly_27(policy: RulesetPolicy) -> None:
    for enemy in (227, 173):  # distance 27 on either side of 200
        assert sensed(policy, 200, [enemy]) == (enemy,)
    for enemy in (228, 172):  # distance 28
        assert sensed(policy, 200, [enemy]) == ()
    assert policy.sensing_window == WINDOW == 27


@pytest.mark.parametrize("policy", TREATMENTS, ids=ids)
def test_distance_is_circular_across_the_wrap(policy: RulesetPolicy) -> None:
    assert _dist(500, 15) == 27 and _dist(500, 16) == 28
    assert sensed(policy, 500, [15]) == (15,)
    assert sensed(policy, 500, [16]) == ()
    assert sensed(policy, 10, [495]) == (495,)
    assert sensed(policy, 10, [494]) == ()


@pytest.mark.parametrize("policy", TREATMENTS, ids=ids)
def test_the_window_covers_exactly_55_cells(policy: RulesetPolicy) -> None:
    for target in (0, 27, 200, 485, 511):
        covered = [cell for cell in range(ARENA) if sensed(policy, target, [cell])]
        assert len(covered) == 55
        assert covered == sorted(cell for cell in range(ARENA) if _dist(cell, target) <= 27)


@pytest.mark.parametrize("policy", TREATMENTS, ids=ids)
def test_the_result_is_ascending_and_distinct_with_co_located_anchors_once(policy: RulesetPolicy) -> None:
    assert sensed(policy, 200, [210, 190, 210, 180]) == (180, 190, 210)
    assert sensed(policy, 500, [5, 490, 5]) == (5, 490)  # ascending by address, across the wrap


@pytest.mark.parametrize("policy", TREATMENTS, ids=ids)
def test_only_other_live_entrants_are_sensed(policy: RulesetPolicy) -> None:
    # The acting entrant's own processes never appear, even inside the window.
    assert sensed(policy, 200, [210], own=(205, 200)) == (210,)
    # A dead entrant's anchors are not sensed.
    assert sensed(policy, 200, [210], enemy_alive=False) == ()
    # Suppression does not hide an enemy process: SENSE reports positions.
    assert sensed(policy, 200, [210], suppressed=True) == (210,)


# ---------------------------------------------------------------------------
# The action, end to end
# ---------------------------------------------------------------------------


def _duel(tmp_path: Path, policy: RulesetPolicy, a_steps: dict, b_steps: dict | None = None, *, a_pos: int = 100,
          a_reach: int = 64, b_positions: tuple[int, ...] = (120,), ticks: int = 1, name: str = "trace.jsonl"):
    log: list[tuple[str, int, int]] = []
    a = Scripted("A", log, a_steps)
    b = Scripted("B", log, b_steps or {})
    b_processes = [process(f"b{i}", position, 1, QUOTA if i == 0 else 0, b if i == 0 else Scripted(f"b{i}", log))
                   for i, position in enumerate(b_positions)]
    run = run_traced(tmp_path, policy, [("A", 0, [process("a", a_pos, a_reach, QUOTA, a)]), ("B", 256, b_processes)],
                     ticks=ticks, name=name)
    return run, a, b, log


@pytest.mark.parametrize("policy", TREATMENTS, ids=ids)
def test_an_applied_sense_with_anchors(tmp_path: Path, policy: RulesetPolicy) -> None:
    run, a, _, _ = _duel(tmp_path, policy, {1: sense(130)}, b_positions=(120, 150, 158, 200))
    first, second = run.decisions("A")[:2]
    assert first["action"] == {"kind": "sense", "operand": 130, "value": None}
    assert first["applied_result"] == {"status": "APPLIED", "normalized_address": 130, "read_value": None,
                                       "read_owner": None, "sensed_anchors": [120, 150]}
    assert "previous_sense_anchors" not in first["observation"]
    assert second["observation"]["previous_sense_anchors"] == [120, 150]
    obs = a.observations[1]
    assert obs.previous_sense_anchors == (120, 150)
    assert obs.previous_action_applied is True
    assert obs.previous_read_value is None and obs.previous_read_owner is None
    assert presence_problems(run.records, active=True) == []


@pytest.mark.parametrize("policy", TREATMENTS, ids=ids)
def test_an_applied_sense_that_finds_nothing_is_an_explicit_empty_list(tmp_path: Path, policy: RulesetPolicy) -> None:
    run, a, _, _ = _duel(tmp_path, policy, {1: sense(40)}, b_positions=(120,))
    first, second = run.decisions("A")[:2]
    assert first["applied_result"]["status"] == "APPLIED"
    assert first["applied_result"]["sensed_anchors"] == []
    assert second["observation"]["previous_sense_anchors"] == []
    assert a.observations[1].previous_sense_anchors == ()
    assert a.observations[1].previous_action_applied is True
    assert presence_problems(run.records, active=True) == []


@pytest.mark.parametrize("policy", TREATMENTS, ids=ids)
def test_an_out_of_reach_sense_is_an_ordinary_refusal_with_explicit_nulls(tmp_path: Path, policy: RulesetPolicy) -> None:
    # Reach 64 from 100: 164 is in reach, 165 is not -- the same check as READ.
    run, a, _, _ = _duel(tmp_path, policy, {1: sense(165), 3: sense(164)}, b_positions=(170,))
    records = run.decisions("A")
    refused, reflected, applied = records[0], records[1], records[2]
    assert refused["applied_result"] == {"status": "REJECTED_OUT_OF_REACH", "normalized_address": None,
                                         "read_value": None, "read_owner": None, "sensed_anchors": None}
    assert reflected["observation"]["previous_sense_anchors"] is None  # present, and null
    assert "previous_sense_anchors" in reflected["observation"]
    assert a.observations[1].previous_sense_anchors is None and a.observations[1].previous_action_applied is False
    assert applied["applied_result"]["status"] == "APPLIED" and applied["applied_result"]["sensed_anchors"] == [170]
    assert presence_problems(run.records, active=True) == []
    assert status_problems(run.records) == []


@pytest.mark.parametrize("policy", TREATMENTS, ids=ids)
def test_the_target_is_normalized_mod_512(tmp_path: Path, policy: RulesetPolicy) -> None:
    run, _, _, _ = _duel(tmp_path, policy, {1: sense(130 + ARENA), 3: sense(130 - 2 * ARENA)}, b_positions=(120,))
    first, third = run.decisions("A")[0], run.decisions("A")[2]
    for record, operand in ((first, 130 + ARENA), (third, 130 - 2 * ARENA)):
        assert record["action"]["operand"] == operand  # the operand as returned
        assert record["applied_result"]["normalized_address"] == 130
        assert record["applied_result"]["sensed_anchors"] == [120]


@pytest.mark.parametrize("policy", TREATMENTS, ids=ids)
def test_one_sense_is_one_offer(tmp_path: Path, policy: RulesetPolicy) -> None:
    steps = {n: sense(120) for n in range(1, 17)}
    run, a, _, _ = _duel(tmp_path, policy, steps, ticks=2)
    assert a.calls == 2 * QUOTA
    for tick in (1, 2):
        assert sum(1 for r in run.decisions("A") if r["observation"]["current_tick"] == tick) == QUOTA
    assert run.controller.states[0].total_actions == 2 * QUOTA


@pytest.mark.parametrize("policy", TREATMENTS, ids=ids)
def test_sense_changes_nothing_in_the_match(tmp_path: Path, policy: RulesetPolicy) -> None:
    run, _, _, _ = _duel(tmp_path, policy, {n: sense(120) for n in range(1, 9)})
    vm = run.controller.vm
    # Only the two seeded cores are owned, with their beacons, and nothing moved.
    owned = {address: owner for address, owner in enumerate(vm.writer) if owner is not None}
    assert owned == {**{address: "A" for address in range(8)}, **{address: "B" for address in range(256, 264)}}
    assert all(vm.arena[address] == 0xCE for address in owned)
    assert all(vm.arena[address] == vm.arena[511] for address in range(8, 256))
    assert [p.position for spec in run.controller.entrant_specs for p in spec.processes] == [100, 120]
    assert all(p.telemetry.disruption_hits_received == 0 for spec in run.controller.entrant_specs
               for p in spec.processes)
    assert run.controller.states[0].mem_writes == 0


@pytest.mark.parametrize("policy", TREATMENTS, ids=ids)
def test_the_sensed_entrant_learns_nothing(tmp_path: Path, policy: RulesetPolicy) -> None:
    # B's observations are identical whether A senses B or reads its own anchor.
    _, _, sensed_b, _ = _duel(tmp_path, policy, {n: sense(120) for n in range(1, 17)}, ticks=2, name="sensing.jsonl")
    _, _, quiet_b, _ = _duel(tmp_path, policy, {}, ticks=2, name="quiet.jsonl")
    assert sensed_b.observations == quiet_b.observations


@pytest.mark.parametrize("policy", TREATMENTS, ids=ids)
def test_under_active_the_passive_visible_set_is_empty(tmp_path: Path, policy: RulesetPolicy) -> None:
    # B's anchor is 20 cells from A's: inside A's reach and E6's radius of 32.
    run, a, _, _ = _duel(tmp_path, policy, {}, b_positions=(120,), ticks=2)
    assert policy.detection_radius == 32
    assert all(obs.visible_enemy_anchor_addresses == () for obs in a.observations)
    assert all(r["observation"]["visible_enemy_anchor_addresses"] == [] for r in run.decisions())
    # The parent sees it.
    _, parent_a, _, _ = _duel(tmp_path, CONTROLS[TREATMENTS.index(policy)], {}, b_positions=(120,),
                                       name="parent.jsonl")
    assert parent_a.observations[0].visible_enemy_anchor_addresses == (120,)


# ---------------------------------------------------------------------------
# Delivery (PR8 Sec 10's delivery tests)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("policy", TREATMENTS, ids=ids)
def test_delivery_at_the_next_offer_in_the_same_chunk(tmp_path: Path, policy: RulesetPolicy) -> None:
    run, a, _, log = _duel(tmp_path, policy, {1: sense(120)})
    start = log.index(("A", 1, 1))
    assert log[start + 1] == ("A", 1, 2)  # chunk 2: A's second offer follows its first directly
    assert a.observations[1].previous_sense_anchors == (120,)
    assert run.decisions("A")[1]["observation"]["previous_sense_anchors"] == [120]
    assert presence_problems(run.records, active=True) == []


@pytest.mark.parametrize("policy", TREATMENTS, ids=ids)
def test_delivery_at_the_next_tick(tmp_path: Path, policy: RulesetPolicy) -> None:
    run, a, _, _ = _duel(tmp_path, policy, {QUOTA: sense(120)}, ticks=2)
    sensing, delivering = run.decisions("A")[QUOTA - 1], run.decisions("A")[QUOTA]
    assert sensing["observation"]["current_tick"] == 1 and sensing["action"]["kind"] == "sense"
    assert delivering["observation"]["current_tick"] == 2
    assert delivering["observation"]["previous_sense_anchors"] == [120]
    assert a.observations[QUOTA].previous_sense_anchors == (120,)
    assert presence_problems(run.records, active=True) == []


@pytest.mark.parametrize("policy", TREATMENTS, ids=ids)
@pytest.mark.parametrize("refused", [False, True], ids=["applied", "refused"])
def test_delivery_survives_suppression_for_the_rest_of_the_tick(tmp_path: Path, policy: RulesetPolicy,
                                                                refused: bool) -> None:
    # A senses at the last offer of its first chunk; B's next offer then writes
    # A's anchor, disrupting it. Whole-tick disruption (T8) suppresses A for the
    # rest of tick 1; lambda = 1 (T8L) for its next offer. Either way, A's next
    # callback owes the reflection.
    state = {"sensed": False, "wrote": False}

    def a_sense(_obs):
        state["sensed"] = True
        return sense(900) if refused else sense(120)

    def b_step(obs):
        if state["sensed"] and not state["wrote"]:
            state["wrote"] = True
            return write(100)
        return read(obs.self_anchor)

    log: list[tuple[str, int, int]] = []
    a = Scripted("A", log, {2: a_sense})
    b = Scripted("B", log, {n: b_step for n in range(1, 3 * QUOTA)})
    run = run_traced(tmp_path, policy, [("A", 0, [process("a", 100, 64, QUOTA, a)]),
                                        ("B", 256, [process("b", 120, 64, QUOTA, b)])], ticks=3)
    assert state["wrote"] and run.controller.entrant_specs[0].processes[0].telemetry.disruption_hits_received == 1
    records = run.decisions("A")
    sensing, delivering = records[1], records[2]
    assert sensing["action"]["kind"] == "sense"
    expected = None if refused else [120]
    assert "previous_sense_anchors" in delivering["observation"]
    assert delivering["observation"]["previous_sense_anchors"] == expected
    assert a.observations[2].previous_sense_anchors == (None if refused else (120,))
    # B's disrupting write came between the SENSE and its delivery.
    assert any(name == "B" for name, _, _ in log[log.index(("A", 1, 2)) + 1:log.index(
        ("A", delivering["observation"]["current_tick"], 3))])
    if policy.disruption_slot_limit is None:
        # Whole-tick: the rest of tick 1 is lost, so the reflection arrives on a later tick.
        assert delivering["observation"]["current_tick"] == 2
        assert delivering["observation"]["last_callback_tick"] == 1
        assert sum(1 for r in records if r["observation"]["current_tick"] == 1) == 2
    else:
        # lambda = 1: exactly one of A's offers is lost; A is called again within tick 1.
        assert delivering["observation"]["current_tick"] == 1
        assert sum(1 for r in records if r["observation"]["current_tick"] == 1) == QUOTA - 1
    # Exactly once: the callback after the reflection omits the field.
    assert "previous_sense_anchors" not in records[3]["observation"]
    assert presence_problems(run.records, active=True) == []


@pytest.mark.parametrize("policy", TREATMENTS, ids=ids)
def test_no_later_callback_when_the_entrant_is_eliminated(tmp_path: Path, policy: RulesetPolicy) -> None:
    # B's process sits inside A's core and writes all eight core cells in tick 1;
    # A's process sits away from its core, so it is never disrupted, and senses
    # at its last callback of the tick. A is captured at the end of the tick.
    log: list[tuple[str, int, int]] = []
    a = Scripted("A", log, {QUOTA: sense(4)})
    b = Scripted("B", log, {n: write(n - 1) for n in range(1, QUOTA + 1)})
    run = run_traced(tmp_path, policy, [("A", 0, [process("a", 40, 64, QUOTA, a)]),
                                        ("B", 256, [process("b", 4, 8, QUOTA, b)])], ticks=3)
    records = run.decisions("A")
    assert not run.controller.states[0].alive
    assert len(records) == QUOTA and records[-1]["action"]["kind"] == "sense"
    assert records[-1]["applied_result"]["sensed_anchors"] == [4]  # the authoritative record stands alone
    assert presence_problems(run.records, active=True) == []


@pytest.mark.parametrize("policy", TREATMENTS, ids=ids)
def test_no_later_callback_at_the_tick_limit(tmp_path: Path, policy: RulesetPolicy) -> None:
    run, _, _, _ = _duel(tmp_path, policy, {QUOTA: sense(120)}, ticks=1)
    records = run.decisions("A")
    assert run.result["reason"] == "tick_limit" and len(records) == QUOTA
    assert records[-1]["action"]["kind"] == "sense" and records[-1]["applied_result"]["sensed_anchors"] == [120]
    assert presence_problems(run.records, active=True) == []


@pytest.mark.parametrize("policy", TREATMENTS, ids=ids)
def test_delivery_is_per_process(tmp_path: Path, policy: RulesetPolicy) -> None:
    # Two processes, four offers each: only the sensing process's next callback owes the reflection.
    log: list[tuple[str, int, int]] = []
    sensor = Scripted("s", log, {1: sense(120)})
    striker = Scripted("t", log)
    run = run_traced(tmp_path, policy, [("A", 0, [process("s", 100, 64, 4, sensor), process("t", 110, 64, 4, striker)]),
                                        ("B", 256, [process("b", 120, 1, QUOTA, Scripted("B", log))])], ticks=2)
    assert all(obs.previous_sense_anchors is None for obs in striker.observations)
    assert all("previous_sense_anchors" not in r["observation"] for r in run.decisions("A", "t"))
    assert sensor.observations[1].previous_sense_anchors == (120,)
    assert run.decisions("A", "s")[1]["observation"]["previous_sense_anchors"] == [120]
    assert presence_problems(run.records, active=True) == []


# ---------------------------------------------------------------------------
# The three serialization states and their transitions
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("policy", TREATMENTS, ids=ids)
def test_every_transition_between_the_three_states(tmp_path: Path, policy: RulesetPolicy) -> None:
    # absent -> list -> empty list -> null -> list -> absent, with a READ between two of them.
    steps = {1: read(100), 2: sense(120), 3: sense(40), 4: sense(900), 5: sense(120), 6: read(100), 7: sense(120)}
    run, _, _, _ = _duel(tmp_path, policy, steps, ticks=2)
    records = run.decisions("A")
    sensed_states = [r["applied_result"].get("sensed_anchors", "<absent>") for r in records[:8]]
    reflected_states = [r["observation"].get("previous_sense_anchors", "<absent>") for r in records[:9]]
    assert sensed_states == ["<absent>", [120], [], None, [120], "<absent>", [120], "<absent>"]
    assert reflected_states == ["<absent>", "<absent>", [120], [], None, [120], "<absent>", [120], "<absent>"]
    assert presence_problems(run.records, active=True) == []
    # The parsed document keeps all three states apart.
    document = read_trace_v2(tmp_path / "trace.jsonl")
    parsed = [d.applied_result.sensed_anchors for d in document.decisions if d.agent_id == "A"][:8]
    assert parsed == [ABSENT, (120,), (), None, (120,), ABSENT, (120,), ABSENT]


@pytest.mark.parametrize("policy", CONTROLS, ids=ids)
def test_a_control_trace_carries_no_e8_field(tmp_path: Path, policy: RulesetPolicy) -> None:
    # READ, WRITE, MOVE, an out-of-reach READ, visibility and a disruption, and still no E8 key anywhere.
    a_steps = {1: read(120), 2: write(120), 3: AgentAction(ActionKindV2.MOVE, 5), 4: read(400)}
    run, a, _, _ = _duel(tmp_path, policy, a_steps, ticks=2)
    assert {r["applied_result"]["status"] for r in run.decisions()} == {"APPLIED", "REJECTED_OUT_OF_REACH"}
    assert any(obs.visible_enemy_anchor_addresses for obs in a.observations)
    assert e8_keys_in(run.lines) == []
    assert presence_problems(run.records, active=False) == []
    assert all(obs.previous_sense_anchors is None for obs in a.observations)


# ---------------------------------------------------------------------------
# The oracle rejects every planted departure, both ways
# ---------------------------------------------------------------------------


@pytest.fixture
def clean(tmp_path: Path) -> list[dict]:
    steps = {1: sense(120), 2: read(100), 3: sense(40), 4: sense(900), 5: read(100)}
    run, _, _, _ = _duel(tmp_path, TREATMENTS[0], steps)
    assert presence_problems(run.records, active=True) == []
    return run.records


def _a(records: list[dict]) -> list[int]:
    return [i for i, r in enumerate(records) if r["record_type"] == "decision_v2" and r["agent_id"] == "A"]


def _planted(records: list[dict], index: int, edit) -> list[dict]:
    changed = copy.deepcopy(records)
    edit(changed[index])
    return changed


@pytest.mark.parametrize("name, which, edit", [
    ("a stray sensed_anchors on a READ", 1, lambda r: r["applied_result"].update(sensed_anchors=None)),
    ("a stray empty sensed_anchors on a READ", 1, lambda r: r["applied_result"].update(sensed_anchors=[])),
    ("a stray reflection with no SENSE before it", 0, lambda r: r["observation"].update(previous_sense_anchors=None)),
    ("a stray reflection after a delivered one", 2, lambda r: r["observation"].update(previous_sense_anchors=[120])),
    ("an applied SENSE without sensed_anchors", 0, lambda r: r["applied_result"].pop("sensed_anchors")),
    ("an empty result written as null", 2, lambda r: r["applied_result"].update(sensed_anchors=None)),
    ("a refusal with its null omitted", 3, lambda r: r["applied_result"].pop("sensed_anchors")),
    ("a refusal written as an empty list", 3, lambda r: r["applied_result"].update(sensed_anchors=[])),
    ("an owed reflection omitted", 1, lambda r: r["observation"].pop("previous_sense_anchors")),
    ("an owed null reflection omitted", 4, lambda r: r["observation"].pop("previous_sense_anchors")),
    ("a reflection that disagrees", 1, lambda r: r["observation"].update(previous_sense_anchors=[121])),
    ("a SENSE with an integrity status", 0, lambda r: r["applied_result"].update(status="EXCEPTION")),
])
def test_the_oracle_rejects_a_planted_departure(clean: list[dict], name: str, which: int, edit) -> None:
    assert presence_problems(_planted(clean, _a(clean)[which], edit), active=True), name


def test_the_oracle_rejects_a_window_departure_on_either_side(clean: list[dict]) -> None:
    control_reset = [{"record_type": "reset", "agent_id": "A", "wall_time_ms": 0.0, "diagnostic": None}]
    assert presence_problems(control_reset, active=False) == []
    assert presence_problems([{**control_reset[0], "sensing_window": None}], active=False)  # an explicit control null
    assert presence_problems(control_reset, active=True)  # a missing treatment window
    assert presence_problems([{**control_reset[0], "sensing_window": 28}], active=True)
    assert presence_problems([{**control_reset[0], "sensing_window": 27}], active=True) == []
    assert presence_problems(clean, active=False)  # a SENSE record under a passive Ruleset


def test_the_serialized_bytes_of_a_non_sense_record_are_unchanged_by_the_new_fields(tmp_path: Path) -> None:
    # The same scripted READ/WRITE match under C8 serializes with exactly the keys it had before E8.
    run, _, _, _ = _duel(tmp_path, CONTROLS[0], {1: read(120), 2: write(120)}, ticks=1)
    for line in run.lines[1:]:
        payload = json.loads(line)
        assert set(payload) == {"agent_id", "process_id", "wall_time_ms", "observation", "action", "applied_result",
                                "diagnostic", "record_type"}
        assert set(payload["observation"]) == {
            "current_tick", "last_callback_tick", "previous_action_tick", "self_process_id", "self_anchor",
            "self_reach", "own_core_base", "own_core_size", "visible_enemy_anchor_addresses",
            "previous_action_applied", "previous_read_value", "previous_read_owner"}
        assert set(payload["applied_result"]) == {"status", "normalized_address", "read_value", "read_owner"}
