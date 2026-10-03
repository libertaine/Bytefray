"""V6 E8: the frozen family in the engine, against scripted non-family opponents (phase I8-3).

docs/research/v6/V6_E8_ACTIVE_SPATIAL_SENSING_PREREGISTRATION.md (PR8) Sec 3.2
("engine-level behavior tests against scripted non-family opponents verify
them before the freeze"), and the implementation plan Sec 5.6. Every match
here pairs one family package with a scripted opponent under one of the four
registered conditions; the family's actions and state are asserted, and no
outcome is recorded or asserted. No E8 seed, matrix cell or family-versus-
family match exists.

Each scenario first asserts that its precondition really occurred in the
trace (a tick without a callback, a lost anchor, a confirmed core), so a
test cannot pass because the mechanic never ran.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from _e8_family_engine_harness import (
    ACTIVE_RULESETS,
    ARENA,
    C8,
    C8L,
    CONDITIONS,
    IDLE,
    SEATS,
    STATIC,
    WHOLE_TICK,
    Plan,
    Played,
    agent_stream,
    callbacks_by_tick,
    play,
    sigma_of,
    with_index,
)
from _e8_sensing_harness import presence_problems, status_problems
from battle_engine.ruleset_policy import (
    BYTEFRAY_RULESET_V4_ID,
    BYTEFRAY_RULESET_V6_RESEARCH_SCALE_ID,
)

from tools.research.v6.e6.family import FIXTURE_DIR as E6_FIXTURES
from tools.research.v6.e6.family import package_id as e6_package_id
from tools.research.v6.e8 import compatibility
from tools.research.v6.e8.family import MEMBERS, OPPONENTS, package_id

ALL = tuple(CONDITIONS.values())
CONTROLS = (C8, C8L)


def other(seat: str) -> str:
    return "B" if seat == "A" else "A"


def entrants(seat: str, family: str | Path, opponent: Plan) -> tuple[str | Path | Plan, str | Path | Plan]:
    return (family, opponent) if seat == "A" else (opponent, family)


# ---------------------------------------------------------------------------
# Every member under every condition: legal, contained, traced as registered
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("seat", SEATS)
@pytest.mark.parametrize("member", OPPONENTS)
@pytest.mark.parametrize("ruleset_id", ALL)
def test_every_member_plays_legally_and_contained(tmp_path: Path, ruleset_id: str, member: str, seat: str) -> None:
    played = play(tmp_path, ruleset_id, *entrants(seat, package_id(member), STATIC), ticks=40)
    family = played.decisions(seat)
    assert family
    assert {r["applied_result"]["status"] for r in family} == {"APPLIED"}
    assert status_problems(played.records) == []  # D8-14's universe
    assert '"forfeit"' not in played.replay
    senses = [r for r in family if r["action"]["kind"] == "sense"]
    active = ruleset_id in ACTIVE_RULESETS
    assert presence_problems(played.records, active=active) == []  # PR8 Sec 10, both ways
    if not active:
        assert senses == []  # CQ8-1: no SENSE under C8 or C8L
    elif MEMBERS[member]["acquire"] in ("spatial-fast", "spatial-paced"):
        assert senses  # the treatment's channel is used
    else:
        assert senses == []  # ownership and none never sense


@pytest.mark.parametrize("ruleset_id", ALL)
def test_seat_a_moves_first_on_tick_one_under_every_e8_condition(tmp_path: Path, ruleset_id: str) -> None:
    # The premise of E6-A1 C-1's first-mover rule, carried to E8: chunk 2,
    # Seat A first on odd ticks and Seat B first on even ticks.
    played = play(tmp_path, ruleset_id, IDLE, IDLE, ticks=2)
    order = [(r["observation"]["current_tick"], r["agent_id"]) for r in played.decisions()]
    assert order[:4] == [(1, "A"), (1, "A"), (1, "B"), (1, "B")]
    assert order[16:18] == [(2, "B"), (2, "B")]


# ---------------------------------------------------------------------------
# The pre-match compatibility gate in front of a run (PR8 Sec 13)
# ---------------------------------------------------------------------------

UNGATED = """from battle_engine.agent_api import ActionKindV2, AgentAction, ProcessDeclaration


class Agent:
    def reset(self, context):
        self.n = 0

    def declare_processes(self):
        return [ProcessDeclaration("p", 256, 1.0)]

    def act(self, observation):
        self.n += 1
        if self.n % 4 == 1:
            return AgentAction(ActionKindV2.SENSE, observation.own_core_base + 100)
        return AgentAction(ActionKindV2.READ, observation.own_core_base)


def create_agent():
    return Agent()
"""


def _ungated_package(root: Path) -> Path:
    package = root / "ungated_sense"
    package.mkdir(parents=True)
    (package / "agent.yaml").write_text('{"name": "ungated_sense", "kind": "python", "api_version": 2, '
                                        '"entrypoint": "agent.py:create_agent", "version": "1.0.0"}')
    (package / "agent.py").write_text(UNGATED)
    return package


@pytest.mark.parametrize("ruleset_id", [BYTEFRAY_RULESET_V6_RESEARCH_SCALE_ID, BYTEFRAY_RULESET_V4_ID])
def test_a_family_package_is_refused_before_any_match_off_the_four_conditions(tmp_path: Path,
                                                                              ruleset_id: str) -> None:
    with pytest.raises(compatibility.IncompatiblePairing, match="context-gated SENSE"):
        play(tmp_path / "match", ruleset_id, package_id("RUSH8"), IDLE, ticks=2)
    assert not (tmp_path / "match" / "trace.jsonl").exists()  # nothing ran
    assert not (tmp_path / "match" / "run").exists()


@pytest.mark.parametrize("ruleset_id", ALL)
def test_an_ungated_sense_package_plays_only_under_the_treatments(tmp_path: Path, ruleset_id: str) -> None:
    ungated = _ungated_package(tmp_path / "source")
    assert compatibility.compatible("ungated", ruleset_id) is (ruleset_id in ACTIVE_RULESETS)
    if ruleset_id not in ACTIVE_RULESETS:
        with pytest.raises(compatibility.IncompatiblePairing, match="ungated SENSE"):
            play(tmp_path / "match", ruleset_id, ungated, package_id("GREED8"), ticks=2)
        assert not (tmp_path / "match" / "trace.jsonl").exists()  # refused before the match
        return
    played = play(tmp_path / "match", ruleset_id, ungated, package_id("GREED8"), ticks=2)
    senses = [r for r in played.decisions("A") if r["action"]["kind"] == "sense"]
    assert senses and {r["applied_result"]["status"] for r in senses} == {"APPLIED"}


# ---------------------------------------------------------------------------
# Discovery in the engine (PR8 Sec 2.5)
# ---------------------------------------------------------------------------


def _center(base: int, k: int, sigma: int) -> int:
    return (base + sigma * (91 + 55 * k)) % ARENA


@pytest.mark.parametrize("seat", SEATS)
@pytest.mark.parametrize("member", ["RUSH8", "PACED8", "SPLIT8", "GUARD8", "EVADE8", "REACQ8", "ADAPT8"])
@pytest.mark.parametrize("ruleset_id", ACTIVE_RULESETS)
def test_active_discovery_senses_the_registered_centers_until_the_first_find(
        tmp_path: Path, ruleset_id: str, member: str, seat: str) -> None:
    played = play(tmp_path, ruleset_id, *entrants(seat, package_id(member), STATIC), ticks=6)
    base = played.starts[SEATS.index(seat)]
    enemy = played.starts[SEATS.index(other(seat))]
    sigma = sigma_of(played.seed, seat)
    assert played.agents[seat].direction == sigma
    senses = [r for r in played.decisions(seat) if r["action"]["kind"] == "sense"]
    found = next(i for i, r in enumerate(senses) if r["applied_result"]["sensed_anchors"])
    assert [r["action"]["operand"] for r in senses[:found + 1]] == [_center(base, k, sigma) for k in range(found + 1)]
    assert senses[found]["applied_result"]["sensed_anchors"] == [enemy]  # the stationary anchor, on its core base
    # Discovery stops there: any later SENSE is a verification of the known anchor.
    assert {r["action"]["operand"] for r in senses[found + 1:]} <= {enemy}
    if member == "PACED8":
        assert {index for index, r in with_index(played.decisions(seat)) if r["action"]["kind"] == "sense"} <= {
            1, 3, 5, 7}


@pytest.mark.parametrize("seat", SEATS)
@pytest.mark.parametrize("ruleset_id", CONTROLS)
def test_passive_discovery_is_the_full_stride_sweep_until_something_is_visible(
        tmp_path: Path, ruleset_id: str, seat: str) -> None:
    played = play(tmp_path, ruleset_id, *entrants(seat, package_id("RUSH8"), STATIC), ticks=6)
    sigma = sigma_of(played.seed, seat)
    family = played.decisions(seat)
    first_seen = next(i for i, r in enumerate(family) if r["observation"]["visible_enemy_anchor_addresses"])
    assert first_seen > 0  # D8-7: nothing is visible at first
    assert [r["action"] for r in family[:first_seen]] == [
        {"kind": "move", "operand": 64 * sigma, "value": None}] * first_seen
    assert all(r["action"]["kind"] != "move" for r in family[first_seen:])


# ---------------------------------------------------------------------------
# E6 parity: under the controls the attack and paint members are the frozen
# E6 family's members, decision for decision
# ---------------------------------------------------------------------------

E6_TWINS = {"RUSH8": "RUSH", "PACED8": "PACED", "STEALTH8": "STEALTH", "LURK8": "LURK", "GREED8": "GREED"}
SCRIPTS = {
    "static": STATIC,
    "evading": Plan(moves={2: 20}, repair=8),
    "below": Plan(moves={1: -1}),
    "responsive": Plan(evade=(30, -30), repair=8),
}


@pytest.mark.parametrize("opponent", sorted(SCRIPTS))
@pytest.mark.parametrize("seat", SEATS)
@pytest.mark.parametrize("member", sorted(E6_TWINS))
@pytest.mark.parametrize("ruleset_id", CONTROLS)
def test_under_the_controls_the_attack_and_paint_members_are_e6s(tmp_path: Path, ruleset_id: str, member: str,
                                                                 seat: str, opponent: str) -> None:
    starts = (100, 180) if seat == "A" else (180, 100)
    e8 = play(tmp_path / "e8", ruleset_id, *entrants(seat, package_id(member), SCRIPTS[opponent]), starts=starts,
              ticks=30)
    e6 = play(tmp_path / "e6", ruleset_id, *entrants(seat, E6_FIXTURES / e6_package_id(E6_TWINS[member]),
                                                      SCRIPTS[opponent]), starts=starts, ticks=30)
    assert e8.stream(seat) == e6.stream(seat)
    assert e8.stream(other(seat)) == e6.stream(other(seat))
    assert len(e8.stream(seat)) >= 8


# ---------------------------------------------------------------------------
# Scenario opponents
# ---------------------------------------------------------------------------


def _beside(seed: int, seat: str, gap: int = 74) -> tuple[int, int]:
    """Starts that put the opponent ``gap`` cells along the family seat's sweep direction."""

    base = 100
    starts = (base, (base + sigma_of(seed, seat) * gap) % ARENA)
    return starts if seat == "A" else (starts[1], starts[0])


def first_mover_tick(mover: str, at_least: int) -> int:
    """The first tick >= ``at_least`` in which ``mover``'s seat moves first (Seat A on odd ticks)."""

    tick = at_least
    while (tick % 2 == 1) != (mover == "A"):
        tick += 1
    return tick


def decoy_opponent(seat: str, *, leave_at: int | None = None, hits: tuple[tuple[int, int], ...] = (),
                   evade: tuple[int, ...] = ()) -> Plan:
    """The family's opponent: a decoy anchor on its core base, which the family finds, and a hitter.

    The hitter first moves 128 cells further along the family's sweep direction,
    outside its view and its sensing windows, so the family never disrupts it:
    it repairs the opponent's core (the opponent survives whole-tick denial) and
    makes the scheduled ``hits`` on the family's current anchor at exact entrant
    offers. With ``leave_at`` the decoy moves 60 cells on, out of view, at its
    first callback of that tick (a tick the opponent moves first). With
    ``evade`` it evades responsively instead.
    """

    sigma = sigma_of(7, seat)
    moves = {} if leave_at is None else {leave_at: 60 * sigma}
    return Plan(moves=moves, hits=dict.fromkeys(hits), evade=evade, repair=8, processes=2, away=64 * sigma)


# ---------------------------------------------------------------------------
# Initial acquisition ends at core confirmation: SPLIT8 under the controls (K-1)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("seat", SEATS)
@pytest.mark.parametrize("ruleset_id", CONTROLS)
def test_k1_split8s_sensor_never_moves_once_its_entrant_confirms_the_core(tmp_path: Path, ruleset_id: str,
                                                                          seat: str) -> None:
    away = decoy_opponent(seat, leave_at=first_mover_tick(other(seat), 6))
    played = play(tmp_path, ruleset_id, *entrants(seat, package_id("SPLIT8"), away), starts=_beside(7, seat),
                  ticks=16)
    enemy_base = played.starts[SEATS.index(other(seat))]
    snaps = played.snaps[seat]
    confirmed = next(i for i, s in enumerate(snaps) if s.enemy_core is not None)
    assert snaps[confirmed].enemy_core == enemy_base
    assert any(s.action.kind.value == "move" for s in snaps[:confirmed])  # the initial sweep
    after = snaps[confirmed:]
    lost = [s for s in after if not s.obs.visible_enemy_anchor_addresses]
    assert len(lost) >= 16  # the precondition: the visible set empties after confirmation
    assert {s.obs.self_process_id for s in lost} == {"sensor", "striker"}
    assert [s for s in after if s.action.kind.value == "move"] == []  # no generic sweep, ever
    own = played.starts[SEATS.index(seat)]
    assert all(s.obs.self_anchor == own for s in snaps if s.obs.self_process_id == "striker")  # never moves


# ---------------------------------------------------------------------------
# The registered channel difference (K-4): guard members under each channel
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("seat", SEATS)
@pytest.mark.parametrize("member", ["GUARD8", "EVADE8"])
@pytest.mark.parametrize("ruleset_id", ALL)
def test_k4_guard_members_resweep_on_lost_sight_only_under_passive(tmp_path: Path, ruleset_id: str, member: str,
                                                                    seat: str) -> None:
    sigma = sigma_of(7, seat)
    away = decoy_opponent(seat, leave_at=first_mover_tick(other(seat), 4))
    played = play(tmp_path, ruleset_id, *entrants(seat, package_id(member), away), starts=_beside(7, seat),
                  ticks=12)
    snaps = played.snaps[seat]
    assert {s.action.operand for s in snaps if s.action.kind.value == "move"} <= {64 * sigma}  # no hit: no evasion
    if ruleset_id in ACTIVE_RULESETS:
        found = next(i for i, s in enumerate(snaps) if s.known)
        assert all(s.action.kind.value == "sense" for s in snaps[:found])  # discovery only
        assert [s for s in snaps[found:] if s.action.kind.value in ("sense", "move")] == []  # remembered
        assert snaps[-1].known == (played.starts[SEATS.index(other(seat))],)  # stale, and still known
    else:
        seen = next(i for i, s in enumerate(snaps) if s.obs.visible_enemy_anchor_addresses)
        lost = next(i for i, s in enumerate(snaps) if i > seen and not s.obs.visible_enemy_anchor_addresses)
        assert (snaps[lost].action.kind.value, snaps[lost].action.operand) == ("move", 64 * sigma)  # re-sweep


# ---------------------------------------------------------------------------
# Re-acquisition in the engine: the search, its precedence and RP-2
# ---------------------------------------------------------------------------


def _tau(seed: int, seat: str) -> int:
    """The first play draw of the family stream: tau, when its first search starts."""

    stream = agent_stream(seed, seat)
    stream.randrange(2), stream.randrange(2)
    return (-1, 1)[stream.randrange(2)]


@pytest.mark.parametrize("seat", SEATS)
@pytest.mark.parametrize("ruleset_id", ACTIVE_RULESETS)
def test_rp2_reacq8s_search_reaches_its_third_window(tmp_path: Path, ruleset_id: str, seat: str) -> None:
    tau = _tau(7, seat)
    tick = first_mover_tick(other(seat), 2)  # the opponent moves first, then hits after REACQ8's first chunk
    evader = Plan(moves={tick: -46 * tau}, hits={(tick, 3): None}, repair=8)
    played = play(tmp_path, ruleset_id, *entrants(seat, package_id("REACQ8"), evader), starts=_beside(7, seat, 91),
                  ticks=tick + 2)
    a = played.starts[SEATS.index(other(seat))]
    moved = (a - 46 * tau) % ARENA
    mine = with_index(played.decisions(seat))
    in_tick = [(i, r) for i, r in mine if r["observation"]["current_tick"] == tick]
    senses = [(r["observation"]["current_tick"], i, r["action"]["operand"], r["applied_result"]["sensed_anchors"])
              for i, r in mine if r["action"]["kind"] == "sense" and r["observation"]["current_tick"] >= tick]
    assert senses[:2] == [(tick, 1, a, []), (tick, 2, (a + 46 * tau) % ARENA, [])]  # verification, window 2
    if ruleset_id in WHOLE_TICK:
        assert len(in_tick) == 2  # hit after its first chunk: no further callback this tick
        assert senses[2] == (tick + 1, 1, (a - 46 * tau) % ARENA, [moved])  # RP-2: the first offer continues it
    else:
        assert len(in_tick) == 7  # lambda = 1: one offer lost; the search finishes inside the tick
        assert senses[2] == (tick, 3, (a - 46 * tau) % ARENA, [moved])
    after = next(r for i, r in mine if r["observation"].get("previous_sense_anchors") == [moved])
    assert after["action"] == {"kind": "write", "operand": moved, "value": 1}  # replaced: disrupt it
    assert played.agents[seat].replacements == {a: moved}


@pytest.mark.parametrize("seat", SEATS)
@pytest.mark.parametrize("ruleset_id", ACTIVE_RULESETS)
def test_reacq8s_search_is_exhausted_after_its_third_empty_window(tmp_path: Path, ruleset_id: str,
                                                                   seat: str) -> None:
    tau = _tau(7, seat)
    tick = first_mover_tick(other(seat), 2)
    far = Plan(moves={(tick, 1): 64 * tau, (tick, 2): 64 * tau}, repair=8)  # 128 cells: outside all three windows
    played = play(tmp_path, ruleset_id, *entrants(seat, package_id("REACQ8"), far), starts=_beside(7, seat, 91),
                  ticks=tick + 1)
    a = played.starts[SEATS.index(other(seat))]
    snaps = played.snaps[seat]
    windows = [(s.action.operand, s.purpose) for s in snaps if s.obs.current_tick == tick
               and s.action.kind.value == "sense"]
    assert windows == [(a, "verify"), ((a + 46 * tau) % ARENA, "search"), ((a - 46 * tau) % ARENA, "search")]
    third = next(i for i, s in enumerate(snaps)
                 if s.purpose == "search" and s.action.operand == (a - 46 * tau) % ARENA)
    after = snaps[third + 1]
    assert after.obs.previous_sense_anchors == ()
    assert (after.known, after.search_address, after.missing) == ((), None, ())  # a is unknown
    assert after.action.kind.value != "sense"  # the posture steps, not another search window


@pytest.mark.parametrize("seat", SEATS)
@pytest.mark.parametrize("ruleset_id", CONTROLS)
def test_passive_reacq8_moves_toward_the_registered_centers(tmp_path: Path, ruleset_id: str, seat: str) -> None:
    tau = _tau(7, seat)
    away = decoy_opponent(seat, leave_at=first_mover_tick(other(seat), 4))
    played = play(tmp_path, ruleset_id, *entrants(seat, package_id("REACQ8"), away), starts=_beside(7, seat),
                  ticks=12)
    a = played.starts[SEATS.index(other(seat))]
    snaps = played.snaps[seat]
    start = next(i for i, s in enumerate(snaps) if s.search_address is not None)
    assert snaps[start].search_address == a and snaps[start - 1].obs.visible_enemy_anchor_addresses == (a,)
    assert snaps[start].obs.visible_enemy_anchor_addresses == ()  # the trigger: a tracked address missing
    centers = [a, (a + 46 * tau) % ARENA, (a - 46 * tau) % ARENA]
    end = next(i for i, s in enumerate(snaps) if i > start and s.search_address is None)
    target = 0
    for s in snaps[start:end]:
        while target < 3 and s.obs.self_anchor == centers[target]:
            target += 1
        delta = (centers[target] - s.obs.self_anchor) % ARENA
        delta = delta - ARENA if delta > ARENA // 2 else delta
        assert (s.action.kind.value, s.action.operand) == ("move", max(-64, min(64, delta)))  # with precedence
    assert end - start >= 2
    assert snaps[end].obs.visible_enemy_anchor_addresses  # ended by replacement: an anchor is visible again
    assert played.agents[seat].replacements == {a: snaps[end].obs.visible_enemy_anchor_addresses[0]}


# ---------------------------------------------------------------------------
# CQ8-2: twin identity until the first trigger, in the engine
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("seat", SEATS)
@pytest.mark.parametrize("ruleset_id", CONTROLS)
def test_cq8_2_rush8_and_reacq8_are_identical_until_reacq8s_first_trigger(tmp_path: Path, ruleset_id: str,
                                                                          seat: str) -> None:
    away = decoy_opponent(seat, leave_at=first_mover_tick(other(seat), 4))
    rush = play(tmp_path / "rush", ruleset_id, *entrants(seat, package_id("RUSH8"), away), starts=_beside(7, seat),
                ticks=12)
    reacq = play(tmp_path / "reacq", ruleset_id, *entrants(seat, package_id("REACQ8"), away),
                 starts=_beside(7, seat), ticks=12)
    mine = reacq.decisions(seat)
    trigger = next(i for i in range(1, len(mine)) if set(mine[i - 1]["observation"]["visible_enemy_anchor_addresses"])
                   - set(mine[i]["observation"]["visible_enemy_anchor_addresses"]))
    assert trigger > 4
    assert rush.stream(seat)[:trigger] == reacq.stream(seat)[:trigger]
    assert rush.stream(seat)[trigger][2] != reacq.stream(seat)[trigger][2]  # REACQ8 searches; RUSH8 does not


def _inferred_hits(decisions: list[dict[str, Any]]) -> list[int]:
    """Positions of the first-of-tick callbacks at which EVADE8's rule infers a hit, from the trace alone."""

    counts: dict[int, int] = {}
    for record in decisions:
        counts[record["observation"]["current_tick"]] = counts.get(record["observation"]["current_tick"], 0) + 1
    ticks = sorted(counts)
    found = []
    for position, (index, record) in enumerate(with_index(decisions)):
        tick = record["observation"]["current_tick"]
        if index != 1 or tick == ticks[0]:
            continue
        previous = max(t for t in ticks if t < tick)
        if tick > previous + 1 or counts[previous] < 8:
            found.append(position)
    return found


def _hits(seat: str) -> tuple[tuple[int, int], ...]:
    """Hits on the family seat: before and after its first chunk in ticks the opponent moves first, and
    after its first and last chunks in ticks the family moves first (PA Sec 8's positions)."""

    opponent_first = [first_mover_tick(other(seat), t) for t in (3, 7)]
    family_first = [first_mover_tick(seat, t) for t in (5, 9)]
    return ((opponent_first[0], 1), (opponent_first[1], 3), (family_first[0], 1), (family_first[1], 7))


@pytest.mark.parametrize("seat", SEATS)
@pytest.mark.parametrize("ruleset_id", CONTROLS)
def test_cq8_2_guard8_and_evade8_are_identical_until_the_first_inferred_hit(tmp_path: Path, ruleset_id: str,
                                                                            seat: str) -> None:
    hitter = decoy_opponent(seat, hits=_hits(seat))
    guard = play(tmp_path / "guard", ruleset_id, *entrants(seat, package_id("GUARD8"), hitter),
                 starts=_beside(7, seat), ticks=12)
    evade = play(tmp_path / "evade", ruleset_id, *entrants(seat, package_id("EVADE8"), hitter),
                 starts=_beside(7, seat), ticks=12)
    first = _inferred_hits(evade.decisions(seat))[0]
    assert first > 0
    assert guard.stream(seat)[:first] == evade.stream(seat)[:first]
    assert evade.decisions(seat)[first]["action"]["kind"] == "move"
    assert guard.decisions(seat)[first]["action"] != evade.decisions(seat)[first]["action"]


# ---------------------------------------------------------------------------
# EVADE8: hit inference from callback counting, fresh draws, every hit
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("seat", SEATS)
@pytest.mark.parametrize("ruleset_id", ALL)
def test_evade8_evades_exactly_on_every_inferred_hit_with_fresh_draws(tmp_path: Path, ruleset_id: str,
                                                                      seat: str) -> None:
    played = play(tmp_path, ruleset_id, *entrants(seat, package_id("EVADE8"), decoy_opponent(seat, hits=_hits(seat))),
                  starts=_beside(7, seat), ticks=12)
    mine = played.decisions(seat)
    inferred = _inferred_hits(mine)
    counts = callbacks_by_tick(played.records, seat)
    assert len(inferred) >= 3  # the precondition: the hits land
    if ruleset_id in WHOLE_TICK:
        assert any(t not in counts for t in range(2, max(counts)))  # a whole tick without a callback: (i)
    assert any(c < 8 for t, c in counts.items() if t < max(counts))  # a short tick: (ii)
    stream = agent_stream(played.seed, seat)
    stream.randrange(2), stream.randrange(2)
    sigma = sigma_of(played.seed, seat)
    for position, record in enumerate(mine):
        action = record["action"]
        if position in inferred:
            sign = (-1, 1)[stream.randrange(2)]
            assert action == {"kind": "move", "operand": sign * stream.randint(8, 64), "value": None}
        elif action["kind"] == "move":
            # Otherwise only the passive sweep moves it, and only with nothing visible (K-4).
            assert ruleset_id in CONTROLS and action["operand"] == 64 * sigma
            assert record["observation"]["visible_enemy_anchor_addresses"] == []
    assert played.agents[seat].rng.getstate() == stream.getstate()  # no other draw


# ---------------------------------------------------------------------------
# STRESS8: the tick- and callback-keyed check, the beacon repair, P8-6
# ---------------------------------------------------------------------------


def _damager(seat: str, base: int) -> Plan:
    """Damages STRESS8's core (the cell it checks next tick, at the end of each tick) and denies it offers.

    It sits 200 cells away, out of STRESS8's view, so STRESS8 never disrupts it.
    """

    hits: dict[tuple[int, int], int | None] = {}
    for tick in range(1, 13):
        hits[(tick, 4)] = (base + ((tick + 3) % 8)) % ARENA
        hits[(tick, 8)] = (base + (tick % 8)) % ARENA  # the cell STRESS8 checks next tick
    for tick in (first_mover_tick(other(seat), 3), first_mover_tick(other(seat), 7)):
        hits[(tick, 1)] = None  # before STRESS8's first chunk: whole-tick denial
    return Plan(hits=hits)


def _stress_run(tmp_path: Path, ruleset_id: str, seat: str) -> tuple[Played, int]:
    base = 100 if seat == "A" else 300
    return play(tmp_path, ruleset_id, *entrants(seat, package_id("STRESS8"), _damager(seat, base)),
                starts=(100, 300), ticks=12), base


@pytest.mark.parametrize("seat", SEATS)
@pytest.mark.parametrize("ruleset_id", ALL)
def test_stress8_checks_its_core_cell_each_tick_and_repairs_damage_with_the_beacon(tmp_path: Path, ruleset_id: str,
                                                                                   seat: str) -> None:
    played, base = _stress_run(tmp_path, ruleset_id, seat)
    mine = with_index(played.decisions(seat))
    repairs, guard_cursor = 0, 0
    for position, (index, record) in enumerate(mine):
        tick, action = record["observation"]["current_tick"], record["action"]
        if index == 1:
            assert action == {"kind": "read", "operand": base + (tick - 1) % 8, "value": None}
            continue
        _prior_index, prior = mine[position - 1]
        if index == 2 and prior["applied_result"]["read_owner"] != seat:
            assert action == {"kind": "write", "operand": prior["action"]["operand"], "value": 0xCE}
            repairs += 1
            continue
        assert action == {"kind": "write", "operand": base + guard_cursor, "value": 0xCE}  # the guard posture
        guard_cursor = (guard_cursor + 1) % 8
    assert repairs >= 5  # the precondition: damaged checks occurred
    checked = {r["observation"]["current_tick"] for i, r in mine if i == 1}
    if ruleset_id in WHOLE_TICK:
        assert set(range(1, 13)) - checked  # whole ticks without a callback skip their cell


@pytest.mark.parametrize("seat", SEATS)
@pytest.mark.parametrize("ruleset_id", ALL)
def test_p8_6_the_checks_result_always_reaches_the_same_ticks_second_callback(tmp_path: Path, ruleset_id: str,
                                                                              seat: str) -> None:
    played, _base = _stress_run(tmp_path, ruleset_id, seat)
    decisions = played.decisions()
    positions = [p for p, r in enumerate(decisions) if r["agent_id"] == seat]
    adjacent = []
    for k, p in enumerate(positions):
        tick = decisions[p]["observation"]["current_tick"]
        if k and decisions[positions[k - 1]]["observation"]["current_tick"] == tick:
            continue  # not the tick's first callback
        assert decisions[p]["action"]["kind"] == "read"  # the check
        if k + 1 < len(positions):
            following = positions[k + 1]
            # The check's result reaches the same tick's second callback: P8-6's stale case never arises.
            assert decisions[following]["observation"]["current_tick"] == tick
            adjacent.append(following == p + 1)
    assert len(adjacent) >= 8
    if ruleset_id in WHOLE_TICK:
        assert all(adjacent)  # P8-6's stated premise: callbacks 1 and 2 share a chunk
    else:
        # Under lambda = 1 a hit before STRESS8's first chunk costs it its first offer, which splits
        # them: an opponent decision falls between, so P8-6's stated premise does not hold there,
        # although its conclusion does.
        assert not all(adjacent)


# ---------------------------------------------------------------------------
# D8-3's premise and twin identity in the engine
# ---------------------------------------------------------------------------

OPPONENT_SCRIPTS = {"static": STATIC, "mover": Plan(moves={4: 30, 7: -50}, repair=8), "idle": IDLE}


@pytest.mark.parametrize("opponent", sorted(OPPONENT_SCRIPTS))
@pytest.mark.parametrize("seat", SEATS)
@pytest.mark.parametrize("ruleset_id", ACTIVE_RULESETS)
def test_d8_3_lurk8_and_greed8_records_are_identical_under_the_treatments(tmp_path: Path, ruleset_id: str,
                                                                          seat: str, opponent: str) -> None:
    lurk = play(tmp_path / "lurk", ruleset_id, *entrants(seat, package_id("LURK8"), OPPONENT_SCRIPTS[opponent]),
                ticks=30)
    greed = play(tmp_path / "greed", ruleset_id, *entrants(seat, package_id("GREED8"), OPPONENT_SCRIPTS[opponent]),
                 ticks=30)
    assert lurk.stream(seat) == greed.stream(seat)
    assert len(lurk.stream(seat)) >= 64
    assert lurk.agents[seat].rng.getstate() == greed.agents[seat].rng.getstate()


@pytest.mark.parametrize("member", OPPONENTS)
@pytest.mark.parametrize("ruleset_id", ALL)
def test_primary_and_twin_packages_play_identically(tmp_path: Path, ruleset_id: str, member: str) -> None:
    opponent = Plan(moves={4: 30}, hits={(6, 1): None, (9, 3): None}, repair=8)
    runs = [play(tmp_path / role, ruleset_id, package_id(member, role), opponent, ticks=16)
            for role in ("primary", "twin")]
    assert runs[0].stream("A") == runs[1].stream("A")
    assert runs[0].stream("B") == runs[1].stream("B")
    assert runs[0].agents["A"].rng.getstate() == runs[1].agents["A"].rng.getstate()
