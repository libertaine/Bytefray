"""V6 E6: the frozen analysis on hand-built tables with known answers.

Implementation plan Sec 7.2. Every table below is synthetic: package IDs
come from the family, but no match is played. The test seeds are never
matrix seeds.
"""

from __future__ import annotations

import random
from collections.abc import Callable
from dataclasses import dataclass, replace
from fractions import Fraction
from itertools import product
from typing import Any

import pytest

from tools.research.v6.e3.gates import cell_key
from tools.research.v6.e6 import analyze_e6, family, interpretation, payoff
from tools.research.v6.e6.analyze_e6 import ConditionData
from tools.research.v6.e6.interpretation import (
    CANDIDATE,
    FAIL,
    NEITHER,
    NOT_ESTABLISHED,
    PASS,
    REFUTED,
    REJECT,
    ROWS,
    STATUSES,
    SUPPORTED,
    VOID,
    InterpretationInvariantError,
)

SEEDS = (11, 22, 33, 44)
MEMBERS = family.OPPONENTS
PID = {m: family.package_id(m) for m in MEMBERS}
TWIN = {m: family.package_id(m, "twin") for m in MEMBERS}


@dataclass(frozen=True)
class Match:
    """One synthetic match, from Seat A's side."""

    result: str  # "A", "B" or "tie"
    ticks: int = 100
    captured: tuple[str, ...] = ()  # seats whose core was captured

    @classmethod
    def win(cls, seat: str, ticks: int = 100) -> Match:
        return cls(seat, ticks, ("B" if seat == "A" else "A",))

    @classmethod
    def tie(cls, ticks: int = 1000) -> Match:
        return cls("tie", ticks, ())


Rule = Callable[[str, str, int], Match]


def _cell(subject: str, opponent: str, orientation: str, seed: int, match: Match) -> dict[str, Any]:
    subject_is_a = orientation == "candidate_first"
    if match.result == "tie":
        outcome = "tie"
    else:
        outcome = "win" if (match.result == "A") == subject_is_a else "loss"
    capture = bool(match.captured)
    return {
        "schedule_id": f"{subject}|{opponent}|{seed}|{orientation}",
        "subject_id": subject, "opponent_id": opponent, "orientation": orientation, "seed": seed,
        "status": "completed", "outcome": outcome, "ticks_run": match.ticks,
        "termination_reason": "last_agent_standing" if capture else "tick_limit",
        "entrant_terminations": {seat: ("core_captured" if seat in match.captured else None) for seat in "AB"},
        "score_subject": 1.0, "score_opponent": 1.0, "territory_subject": 0.0, "territory_opponent": 0.0,
        "artifact_dir": f"{subject}-{opponent}-{seed}-{orientation}",
    }


def f1(rule: Rule, seeds: tuple[int, ...] = SEEDS) -> tuple[dict[str, Any], ...]:
    """The triangular round robin of the primaries, both orientations: rule(seat A member, seat B member, seed)."""
    cells = []
    for index, first in enumerate(MEMBERS):
        for second in MEMBERS[index + 1:]:
            for seed in seeds:
                cells.append(_cell(PID[first], PID[second], "candidate_first", seed, rule(first, second, seed)))
                cells.append(_cell(PID[first], PID[second], "opponent_first", seed, rule(second, first, seed)))
    return tuple(cells)


def f2(rule: Callable[[str, int], Match] = lambda m, s: Match.win("A" if s % 2 else "B"),
       seeds: tuple[int, ...] = SEEDS) -> tuple[dict[str, Any], ...]:
    return tuple(
        _cell(PID[m], TWIN[m], orientation, seed, rule(m, seed))
        for m in MEMBERS for seed in seeds for orientation in ("candidate_first", "opponent_first")
    )


def condition(condition_id: str, rule: Rule, *, contact: Callable[[dict[str, Any]], bool] = lambda cell: True,
              mirror: Callable[[str, int], Match] | None = None, seeds: tuple[int, ...] = SEEDS) -> ConditionData:
    cells = f1(rule, seeds)
    return ConditionData(condition_id, cells, f2(mirror, seeds) if mirror else f2(seeds=seeds),
                         {cell_key(cell): contact(cell) for cell in cells})


# Class-based rules: the four search variants are one class, so CQ-1 holds by construction.
CLASS = {"RUSH": "att", "PACED": "att", "STEALTH": "att", "LURK": "att", "SPLIT": "split", "GUARD": "guard",
         "EVADER": "evader", "GREED": "greed", "ADAPT": "adapt"}
STRENGTH = {"att": 5, "split": 4, "guard": 3, "evader": 2, "adapt": 1, "greed": 0}


def dominance(a: str, b: str, seed: int) -> Match:
    """A strict ladder: the stronger class wins by capture at tick 2; equal classes tie."""
    ca, cb = CLASS[a], CLASS[b]
    if ca == cb:
        return Match.tie()
    return Match.win("A" if STRENGTH[ca] > STRENGTH[cb] else "B", ticks=2)


def cyclic(a: str, b: str, seed: int) -> Match:
    """No fixed member is a best response to everyone: GUARD beats att, att beats the rest, the rest beat GUARD."""
    ca, cb = CLASS[a], CLASS[b]
    if ca == cb:
        return Match.tie()
    order = {("guard", "att"), ("att", "split"), ("att", "evader"), ("att", "greed"), ("att", "adapt"),
             ("split", "guard"), ("evader", "guard"), ("greed", "guard"), ("adapt", "guard")}
    if (ca, cb) in order:
        return Match.win("A", ticks=5)
    if (cb, ca) in order:
        return Match.win("B", ticks=5)
    return Match.win("A" if STRENGTH[ca] > STRENGTH[cb] else "B", ticks=50)


# ---------------------------------------------------------------------------
# O-VALUE, O-PAYOFF
# ---------------------------------------------------------------------------


def _table(rule: Rule, seeds: tuple[int, ...] = SEEDS) -> payoff.ValueTable:
    return payoff.value_table(f1(rule, seeds), member_of=analyze_e6.member_of(), members=MEMBERS, seeds=seeds)


def test_match_values_are_one_half_zero() -> None:
    cell = _cell(PID["RUSH"], PID["GUARD"], "candidate_first", 11, Match.win("A"))
    assert payoff.seat_a_value(cell) == 1
    assert payoff.seat_a_value(_cell(PID["RUSH"], PID["GUARD"], "opponent_first", 11, Match.win("A"))) == 1
    assert payoff.seat_a_value(_cell(PID["RUSH"], PID["GUARD"], "candidate_first", 11, Match.win("B"))) == 0
    assert payoff.seat_a_value(_cell(PID["RUSH"], PID["GUARD"], "candidate_first", 11, Match.tie())) == Fraction(1, 2)
    with pytest.raises(payoff.PayoffDataError):
        payoff.seat_a_value({**cell, "outcome": None, "status": "failed"})


def test_payoff_is_the_equal_weight_mean_of_per_seed_orientation_means() -> None:
    def rule(a: str, b: str, seed: int) -> Match:
        if {a, b} == {"RUSH", "GUARD"}:
            # RUSH wins both orientations at 11, loses both at 22, splits the seats at 33, ties at 44.
            return {11: Match.win("A" if a == "RUSH" else "B"), 22: Match.win("B" if a == "RUSH" else "A"),
                    33: Match.win("A"), 44: Match.tie()}[seed]
        return Match.tie()

    table = _table(rule)
    assert [payoff.per_seed(table, "RUSH", "GUARD", k) for k in range(4)] == [1, 0, Fraction(1, 2), Fraction(1, 2)]
    u = payoff.payoffs(table)
    assert u[("RUSH", "GUARD")] == Fraction(1, 2) == u[("GUARD", "RUSH")]
    assert all(u[(m, m)] == Fraction(1, 2) for m in MEMBERS)
    for i, j in product(MEMBERS, MEMBERS):
        assert u[(i, j)] + u[(j, i)] == 1
    # Positions with repetition weight exactly as drawn.
    assert payoff.payoffs(table, (0, 0, 0, 1))[("RUSH", "GUARD")] == Fraction(3, 4)


@pytest.mark.parametrize("problem", ["missing seed", "mirror in F1", "unknown seed", "duplicate"])
def test_an_incomplete_or_malformed_f1_is_rejected(problem: str) -> None:
    cells = list(f1(dominance))
    if problem == "missing seed":
        cells.pop()
    elif problem == "mirror in F1":
        cells.append(_cell(PID["RUSH"], TWIN["RUSH"], "candidate_first", 11, Match.tie()))
    elif problem == "unknown seed":
        cells[0] = {**cells[0], "seed": 99}
    else:
        cells.append(cells[0])
    with pytest.raises(payoff.PayoffDataError):
        payoff.value_table(cells, member_of=analyze_e6.member_of(), members=MEMBERS, seeds=SEEDS)


# ---------------------------------------------------------------------------
# O-BR, O-CONTRAST: the epsilon boundary, ties and universality
# ---------------------------------------------------------------------------


def _u(values: dict[tuple[str, str], Fraction], default: Fraction = Fraction(1, 2)) -> dict[tuple[str, str], Fraction]:
    return {(i, j): values.get((i, j), default) for i in MEMBERS for j in MEMBERS}


def test_best_responses_include_exactly_epsilon_and_exclude_less() -> None:
    eps = payoff.EPSILON
    assert eps == Fraction(1, 16)
    u = _u({("RUSH", "GUARD"): Fraction(3, 4), ("PACED", "GUARD"): Fraction(3, 4) - eps,
            ("LURK", "GUARD"): Fraction(3, 4) - eps - Fraction(1, 128)})
    br = payoff.best_responses(u, candidates=family.FIXED_MEMBERS, opponents=MEMBERS)
    assert {"RUSH", "PACED"} <= br["GUARD"] and "LURK" not in br["GUARD"]
    # A tie at the top is shared.
    tie = payoff.best_responses(_u({}), candidates=family.FIXED_MEMBERS, opponents=MEMBERS)
    assert all(members == frozenset(family.FIXED_MEMBERS) for members in tie.values())


def test_adapt_is_never_a_candidate_best_response() -> None:
    u = _u({("ADAPT", j): Fraction(1) for j in MEMBERS})
    br = payoff.best_responses(u, candidates=family.FIXED_MEMBERS, opponents=MEMBERS)
    assert all("ADAPT" not in members for members in br.values())
    assert "ADAPT" not in family.FIXED_MEMBERS and "ADAPT" in family.OPPONENTS


def test_universality_and_p_none() -> None:
    reading = payoff.reading(_table(dominance), candidates=family.FIXED_MEMBERS, opponents=MEMBERS)
    # The four identical search variants dominate everyone, including each other (ties at 1/2).
    assert reading.universal == frozenset({"RUSH", "PACED", "STEALTH", "LURK"})
    assert not reading.p_none
    cyclic_reading = payoff.reading(_table(cyclic), candidates=family.FIXED_MEMBERS, opponents=MEMBERS)
    assert cyclic_reading.universal == frozenset() and cyclic_reading.p_none


def test_contrasts_and_their_boundaries() -> None:
    eps = payoff.EPSILON
    base = {("RUSH", j): Fraction(1, 2) for j in MEMBERS}
    at_eps = payoff.deltas(_u({**base, ("LURK", "GUARD"): Fraction(1, 2) + eps}), opponents=MEMBERS)
    just_under = payoff.deltas(_u({**base, ("LURK", "GUARD"): Fraction(1, 2) + eps - Fraction(1, 128)}),
                               opponents=MEMBERS)
    assert at_eps[("LURK", "RUSH", "GUARD")] == eps
    assert payoff.p_win(at_eps) and not payoff.p_never(at_eps)
    assert not payoff.p_win(just_under) and not payoff.p_never(just_under)
    zero = payoff.deltas(_u(base), opponents=MEMBERS)
    assert payoff.p_never(zero) and not payoff.p_win(zero)
    assert payoff.LOWER_INFORMATION == (("LURK", "RUSH"), ("PACED", "RUSH"))
    # STEALTH is a mode contrast, never part of L.
    assert all("STEALTH" not in pair for pair in payoff.LOWER_INFORMATION)


# ---------------------------------------------------------------------------
# O-BOOT
# ---------------------------------------------------------------------------


def test_the_bootstrap_is_fixed_and_draws_seed_positions() -> None:
    draws = payoff.resample_positions(32)
    assert len(draws) == payoff.BOOTSTRAP_RESAMPLES == 1000
    assert all(len(draw) == 32 and all(0 <= k < 32 for k in draw) for draw in draws)
    assert draws == payoff.resample_positions(32)
    rng = random.Random(42)
    assert draws[0] == tuple(rng.randrange(32) for _ in range(32))
    assert draws[1] == tuple(rng.randrange(32) for _ in range(32))


def test_resampling_is_joint_across_cells() -> None:
    # RUSH and PACED face GUARD identically seed by seed, but the seeds differ:
    # a joint resample keeps u(RUSH, GUARD) == u(PACED, GUARD) in every draw;
    # an independent per-cell resample would not.
    def rule(a: str, b: str, seed: int) -> Match:
        if {a, b} in ({"RUSH", "GUARD"}, {"PACED", "GUARD"}):
            attacker_wins = seed in (11, 33)
            attacker_is_a = a != "GUARD"
            return Match.win("A" if attacker_wins == attacker_is_a else "B")
        return Match.tie()

    table = _table(rule)
    stab = payoff.stabilities(table, {"equal": lambda r: r.u[("RUSH", "GUARD")] == r.u[("PACED", "GUARD")]},
                              candidates=family.FIXED_MEMBERS, opponents=MEMBERS,
                              draws=payoff.resample_positions(4))
    assert stab["equal"] == 1


def test_stability_counts_the_fraction_of_resamples() -> None:
    table = _table(dominance)
    draws = [(0, 0, 0, 0), (1, 1, 1, 1), (2, 2, 2, 2), (3, 3, 3, 3)]
    stab = payoff.stabilities(table, {"first": lambda r: r.u[("RUSH", "GUARD")] == 1,
                                      "never": lambda r: False},
                              candidates=family.FIXED_MEMBERS, opponents=MEMBERS, draws=draws)
    assert stab == {"first": Fraction(1), "never": Fraction(0)}


# ---------------------------------------------------------------------------
# E6-H1, E6-H2 statuses
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(("point", "stab", "against", "stab_against", "expected"), [
    (True, Fraction(9, 10), False, Fraction(1, 10), SUPPORTED),
    (True, Fraction(9, 10) - Fraction(1, 1000), False, Fraction(0), NEITHER),
    (False, Fraction(0), True, Fraction(9, 10), REFUTED),
    (False, Fraction(1, 10), True, Fraction(89, 100), NEITHER),
    (False, Fraction(1), False, Fraction(1), NEITHER),
])
def test_status_needs_the_point_estimate_and_nine_tenths_stability(
    point: bool, stab: Fraction, against: bool, stab_against: Fraction, expected: str
) -> None:
    assert analyze_e6._status(point, stab, against, stab_against) == expected


def test_h1_and_h2_on_full_tables() -> None:
    dominant = analyze_e6.read_condition(f1(dominance), seeds=SEEDS, draws=payoff.resample_positions(4, resamples=50))
    assert analyze_e6.h1(dominant) == REFUTED
    assert analyze_e6.h2(dominant) == REFUTED  # identical search variants: every Delta is 0
    varied = analyze_e6.read_condition(f1(cyclic), seeds=SEEDS, draws=payoff.resample_positions(4, resamples=50))
    assert analyze_e6.h1(varied) == SUPPORTED

    def lurk_wins(a: str, b: str, seed: int) -> Match:
        if {a, b} == {"LURK", "GUARD"}:
            return Match.win("A" if a == "LURK" else "B")
        return dominance(a, b, seed)

    contrast = analyze_e6.read_condition(f1(lurk_wins), seeds=SEEDS, draws=payoff.resample_positions(4, resamples=50))
    assert contrast.point.delta[("LURK", "RUSH", "GUARD")] == 0  # both beat GUARD outright
    assert analyze_e6.h2(contrast) == REFUTED


# ---------------------------------------------------------------------------
# E6-H0
# ---------------------------------------------------------------------------


def _h0(changes: dict[int, Match]) -> dict[str, Any]:
    """H0 between the dominance table and a copy whose i-th paired cell is replaced."""
    control = list(f1(dominance))
    treatment = list(control)
    for index, match in changes.items():
        cell = control[index]
        treatment[index] = _cell(cell["subject_id"], cell["opponent_id"], cell["orientation"], cell["seed"], match)
    return analyze_e6.h0(control, treatment)


def test_h0_identity_is_supported_with_a_and_b_equal_to_one() -> None:
    result = _h0({})
    assert (result["status"], result["A"], result["B"]) == (SUPPORTED, "1/1", "1/1")


def test_h0_b_is_taken_over_the_cells_a_counts() -> None:
    control = list(f1(dominance))
    n = len(control)
    # Change the class of exactly n // 10 cells (A = 9/10 at worst) and make them
    # earlier: B over A's cells stays 1, while B over all cells would drop.
    changed = {}
    for index in range(n // 10):
        cell = control[index]
        flipped = "tie" if cell["outcome"] != "tie" else None
        changed[index] = Match.tie(ticks=1) if flipped else Match.win("A", ticks=1)
    result = _h0(changed)
    assert Fraction(result["same_class"], result["paired"]) >= Fraction(9, 10)
    assert result["B"] == "1/1" and result["status"] == SUPPORTED


def test_h0_boundaries() -> None:
    control = list(f1(dominance))
    n = len(control)
    assert n == 36 * 2 * len(SEEDS) == 288

    def with_earlier(count: int) -> dict[str, Any]:
        treatment = [{**cell, "ticks_run": int(cell["ticks_run"]) - 1} if index < count else cell
                     for index, cell in enumerate(control)]
        return analyze_e6.h0(control, treatment)

    def with_changed(count: int) -> dict[str, Any]:
        treatment = [{**cell, "outcome": "tie" if cell["outcome"] != "tie" else "win"} if index < count else cell
                     for index, cell in enumerate(control)]
        return analyze_e6.h0(control, treatment)

    # A = 1 throughout; B = 260/288 >= 9/10 is SUPPORTED, 259/288 < 9/10 is NEITHER.
    assert Fraction(260, 288) >= Fraction(9, 10) > Fraction(259, 288)
    assert (with_earlier(28)["status"], with_earlier(28)["B"]) == (SUPPORTED, "65/72")
    assert (with_earlier(29)["status"], with_earlier(29)["A"]) == (NEITHER, "1/1")
    # A = 260/288 with B = 1 is SUPPORTED; 259/288 is NEITHER.
    assert with_changed(28)["status"] == SUPPORTED
    assert with_changed(29)["status"] == NEITHER
    # A <= 2/3 is REFUTED, exactly at 2/3 included; just above it is NEITHER.
    assert (with_changed(96)["status"], with_changed(96)["A"]) == (REFUTED, "2/3")
    assert with_changed(95)["status"] == NEITHER
    # A = 0: B is undefined and E6-H0 is REFUTED through A.
    assert (with_changed(n)["status"], with_changed(n)["B"]) == (REFUTED, None)
    with pytest.raises(payoff.PayoffDataError):
        analyze_e6.h0(control, control[:-1])


# ---------------------------------------------------------------------------
# E6-H3
# ---------------------------------------------------------------------------


def _h3_rule(tick: int, *, attacker: str = "RUSH") -> Rule:
    def rule(a: str, b: str, seed: int) -> Match:
        pair = {a, b}
        if attacker in pair and pair & {"GUARD", "EVADER"}:
            return Match.win("A" if a == attacker else "B", ticks=tick)
        return Match.tie()
    return rule


def test_forced_line_counts_captures_of_the_defender_at_tick_three_or_earlier() -> None:
    at_three = analyze_e6.h3(f1(_h3_rule(3)), seed_count=len(SEEDS))
    assert at_three["FL"]["RUSH"] == {"GUARD": "1/1", "EVADER": "1/1"}
    assert at_three["status"] == SUPPORTED
    at_four = analyze_e6.h3(f1(_h3_rule(4)), seed_count=len(SEEDS))
    assert at_four["FL"]["RUSH"] == {"GUARD": "0/1", "EVADER": "0/1"}
    assert at_four["status"] == REFUTED


def test_forced_line_is_the_defenders_capture_not_the_attackers() -> None:
    def defenders_win(a: str, b: str, seed: int) -> Match:
        pair = {a, b}
        if "RUSH" in pair and pair & {"GUARD", "EVADER"}:
            return Match.win("B" if a == "RUSH" else "A", ticks=2)
        return Match.tie()
    assert analyze_e6.h3(f1(defenders_win), seed_count=len(SEEDS))["FL"]["RUSH"] == {"GUARD": "0/1", "EVADER": "0/1"}


def test_h3_takes_the_minimum_over_defenders() -> None:
    def only_guard(a: str, b: str, seed: int) -> Match:
        if {a, b} == {"RUSH", "GUARD"}:
            return Match.win("A" if a == "RUSH" else "B", ticks=2)
        return Match.tie()
    result = analyze_e6.h3(f1(only_guard), seed_count=len(SEEDS))
    assert result["min_over_defenders"]["RUSH"] == "0/1"
    assert result["status"] == REFUTED
    cells = list(f1(only_guard))
    cells.remove(next(c for c in cells if {c["subject_id"], c["opponent_id"]} == {PID["RUSH"], PID["GUARD"]}))
    with pytest.raises(payoff.PayoffDataError):
        analyze_e6.h3(cells, seed_count=len(SEEDS))


# ---------------------------------------------------------------------------
# Pathology flags and kill criteria
# ---------------------------------------------------------------------------


def test_pf1_and_pf2_raise_at_one_tenth_exactly() -> None:
    control = condition("C", dominance)
    n = len(control.f1)
    decided = [index for index, cell in enumerate(control.f1) if cell["termination_reason"] != "tick_limit"]
    assert Fraction(29, n) >= Fraction(1, 10) > Fraction(28, n)

    def stalled(count: int) -> ConditionData:
        chosen = set(decided[:count])
        cells = tuple({**cell, "termination_reason": "tick_limit"} if index in chosen else cell
                      for index, cell in enumerate(control.f1))
        return ConditionData("T", cells, control.f2, control.contact)

    assert analyze_e6.pathology(control, stalled(29))["PF-1"]["raised"] is True
    assert analyze_e6.pathology(control, stalled(28))["PF-1"]["raised"] is False

    def detached(count: int) -> ConditionData:
        keys = list(control.contact)
        return ConditionData("T", control.f1, control.f2, {key: index >= count for index, key in enumerate(keys)})

    assert analyze_e6.pathology(control, detached(29))["PF-2"]["raised"] is True
    assert analyze_e6.pathology(control, detached(28))["PF-2"]["raised"] is False
    assert analyze_e6.pathology(control, control)["PF-2"] == {"raised": False, "control": "0/1", "treatment": "0/1"}


def test_pf3_is_new_immunity_of_a_fixed_member() -> None:
    control = condition("C", dominance)  # GREED is captured by every stronger class
    def greed_never_loses(a: str, b: str, seed: int) -> Match:
        if "GREED" in (a, b):
            return Match.tie()
        return dominance(a, b, seed)
    flags = analyze_e6.pathology(control, condition("T", greed_never_loses))
    assert flags["PF-3"] == {"raised": True, "members": ["GREED"]}
    assert analyze_e6.pathology(control, control)["PF-3"]["raised"] is False


def test_pf4_is_a_new_seat_artifact() -> None:
    neutral = condition("C", lambda a, b, s: Match.tie())
    seat_a = condition("T", lambda a, b, s: Match.win("A"))
    flags = analyze_e6.pathology(neutral, seat_a)
    assert flags["PF-4"]["raised"] is True
    assert "F1|RUSH|PACED" in flags["PF-4"]["units"]
    assert analyze_e6.pathology(seat_a, neutral)["PF-4"]["raised"] is False


def test_kill_labels() -> None:
    search_of = {m: str(v["search"]) for m, v in family.MEMBERS.items()}
    assert interpretation.kc1_label({"RUSH", "PACED"}, search_of) == "search race"
    assert interpretation.kc1_label({"GREED"}, search_of) == "greed dominance"
    assert interpretation.kc1_label({"GREED", "RUSH"}, search_of) == "greed dominance"
    assert interpretation.kc1_label({"GUARD", "RUSH"}, search_of) == "other dominance: GUARD, RUSH"
    with pytest.raises(InterpretationInvariantError):
        interpretation.kc1_label(set(), search_of)


def test_kc2_needs_greed_universal_with_stability() -> None:
    def greed_top(a: str, b: str, seed: int) -> Match:
        ca, cb = ("top" if a == "GREED" else CLASS[a]), ("top" if b == "GREED" else CLASS[b])
        if ca == cb:
            return Match.tie()
        rank = {**STRENGTH, "top": 9}
        return Match.win("A" if rank[ca] > rank[cb] else "B", ticks=4)
    reading = analyze_e6.read_condition(f1(greed_top), seeds=SEEDS, draws=payoff.resample_positions(4, resamples=50))
    pf = {"PF-1": {"raised": False}, "PF-2": {"raised": False}, "PF-4": {"raised": False}}
    kills = analyze_e6.kill_criteria(h1t=analyze_e6.h1(reading), treatment=reading, pf=pf, h3_status=NEITHER)
    assert kills["KC-1"] == {"fires": True, "label": "greed dominance"}
    assert kills["KC-2"]["fires"] is True
    assert analyze_e6.fired(kills) == ["KC-1", "KC-2"]


# ---------------------------------------------------------------------------
# Interpretation and disposition: exhaustive and fail-closed
# ---------------------------------------------------------------------------


def test_every_triple_maps_to_exactly_one_row() -> None:
    seen: dict[str, int] = {}
    for e6d, h1t, h1c in product((PASS, FAIL), STATUSES, STATUSES):
        row = interpretation.row_for(e6d, h1t, h1c)
        seen[row.row_id] = seen.get(row.row_id, 0) + 1
        if e6d == FAIL:
            assert row.row_id == "STOP"
    assert seen == {"STOP": 9, "R-CREATES": 1, "R-PREEXISTING": 1, "R-TREATMENT-ONLY": 1, "R-REMOVES": 1,
                    "R-NO-CHOICE": 1, "R-TREATMENT-DOMINANT": 1, "NONE": 3}
    assert interpretation.row_for(PASS, SUPPORTED, REFUTED).row_id == "R-CREATES"
    assert interpretation.row_for(PASS, NEITHER, NEITHER).row_id == "NONE"


def test_a_corrupted_table_fails_closed() -> None:
    duplicated = (*ROWS, replace(ROWS[1], row_id="R-CREATES-AGAIN"))
    with pytest.raises(InterpretationInvariantError):
        interpretation.row_for(PASS, SUPPORTED, REFUTED, duplicated)
    missing = tuple(row for row in ROWS if row.row_id != "NONE")
    with pytest.raises(InterpretationInvariantError):
        interpretation.row_for(PASS, NEITHER, NEITHER, missing)
    with pytest.raises(InterpretationInvariantError):
        interpretation.row_for("MAYBE", SUPPORTED, REFUTED)
    with pytest.raises(InterpretationInvariantError):
        interpretation.row_for(PASS, "NOT SUPPORTED", REFUTED)


def test_qualifiers_cover_every_status() -> None:
    creates, no_choice = interpretation.row_for(PASS, SUPPORTED, REFUTED), interpretation.row_for(PASS, REFUTED, REFUTED)
    texts = {status: interpretation.qualifier(creates, h2=status, h0=NEITHER) for status in STATUSES}
    assert texts[SUPPORTED].startswith("and spending less")
    assert texts[NEITHER] == texts[REFUTED] and texts[NEITHER].startswith("but the registered")
    h0_texts = {status: interpretation.qualifier(no_choice, h2=NEITHER, h0=status) for status in STATUSES}
    assert len(set(h0_texts.values())) == 3
    assert h0_texts[SUPPORTED].startswith("priced sensing acts as a discovery tax")
    assert interpretation.qualifier(interpretation.row_for(PASS, SUPPORTED, SUPPORTED), h2=SUPPORTED, h0=SUPPORTED) is None


def test_disposition_over_every_combination() -> None:
    kills = interpretation.KILL_CRITERIA
    for e6d, h1t, h1c, h2 in product((PASS, FAIL), STATUSES, STATUSES, STATUSES):
        row = interpretation.row_for(e6d, h1t, h1c)
        for size in range(len(kills) + 1):
            for fired in (kills[:size], kills[size:]):
                result = interpretation.disposition(e6d, fired, row, h2=h2)
                if e6d == FAIL:
                    assert result == VOID
                elif fired:
                    assert result == REJECT
                elif row.row_id == "R-CREATES" and h2 == SUPPORTED:
                    assert result == CANDIDATE
                else:
                    assert result == NOT_ESTABLISHED
    with pytest.raises(InterpretationInvariantError):
        interpretation.disposition(PASS, ["KC-9"], ROWS[1], h2=SUPPORTED)


def test_not_supported_is_never_read_as_refuted() -> None:
    # (E6-H1T, E6-H1C) = (SUPPORTED, NEITHER) is R-TREATMENT-ONLY, never R-CREATES.
    assert interpretation.row_for(PASS, SUPPORTED, NEITHER).row_id == "R-TREATMENT-ONLY"
    assert interpretation.row_for(PASS, NEITHER, REFUTED).row_id == "NONE"


# ---------------------------------------------------------------------------
# Whole arms: control against control, the companion reading
# ---------------------------------------------------------------------------

DRAWS = payoff.resample_positions(len(SEEDS), resamples=60)


def test_control_against_control_reads_as_registered() -> None:
    control = condition("C-E6", dominance)
    result = analyze_e6.analyze_arm(control, control, seeds=SEEDS, draws=DRAWS)
    check = analyze_e6.control_against_control(result)
    assert check["status"] == "PASS", check
    assert result["hypotheses"]["E6-H0"] == SUPPORTED and result["hypotheses"]["E6-H2"] == REFUTED
    varied = condition("C-E6", cyclic)
    assert analyze_e6.control_against_control(analyze_e6.analyze_arm(varied, varied, seeds=SEEDS, draws=DRAWS))[
        "status"] == "PASS"


def test_control_against_control_fails_when_search_leaks_into_control_play() -> None:
    def leaky(a: str, b: str, seed: int) -> Match:
        if {a, b} == {"LURK", "GUARD"}:
            return Match.win("B" if a == "LURK" else "A", ticks=2)  # LURK now loses where RUSH wins
        return dominance(a, b, seed)
    control = condition("C-E6", dominance)
    result = analyze_e6.analyze_arm(control, condition("C-E6", leaky), seeds=SEEDS, draws=DRAWS)
    assert analyze_e6.control_against_control(result)["status"] == "FAIL"


def test_the_arm_report_is_complete() -> None:
    result = analyze_e6.analyze_arm(condition("C-E6", dominance), condition("T-E6", cyclic), seeds=SEEDS, draws=DRAWS)
    assert set(result["hypotheses"]) == {"E6-H1T", "E6-H1C", "E6-H2", "E6-H0", "E6-H3"}
    assert (result["hypotheses"]["E6-H1T"], result["hypotheses"]["E6-H1C"]) == (SUPPORTED, REFUTED)
    assert set(result["pathology"]) == {"PF-1", "PF-2", "PF-3", "PF-4"}
    assert set(result["kill_criteria"]) == set(interpretation.KILL_CRITERIA)
    tables = result["payoff"]["treatment"]
    assert set(tables["u"]) == set(MEMBERS) and tables["u"]["RUSH"]["RUSH"]["u"] == "1/2"
    assert set(result["adapt"]["treatment"]) == set(family.FIXED_MEMBERS)
    assert result["decided_by_capture"]["control"] is not None


def test_the_companion_never_decides_and_reports_differences() -> None:
    primary = analyze_e6.analyze_arm(condition("C-E6", dominance), condition("T-E6", cyclic), seeds=SEEDS, draws=DRAWS)
    assert analyze_e6.companion_reading(primary, primary) == {"reading": "agrees with the primary", "differences": []}
    other = analyze_e6.analyze_arm(condition("C-E6L", dominance), condition("T-E6L", dominance), seeds=SEEDS,
                                   draws=DRAWS)
    reading = analyze_e6.companion_reading(primary, other)
    assert reading["reading"] == "differs"
    assert any(item.startswith("E6-H1T") for item in reading["differences"])


@pytest.mark.parametrize(("sdom", "gsb", "neutral"), [
    ("89/100", "1/10", True), ("9/10", "0/1", False), ("89/100", "11/100", False), ("0/1", "-1/10", True),
    ("0/1", "-11/100", False),
])
def test_seat_neutrality_boundaries(sdom: str, gsb: str, neutral: bool) -> None:
    # PF-4: seat-neutral is SDom < 9/10 and |GSB| <= 1/10, both boundaries exact.
    assert analyze_e6._seat_neutral({"exact": {"sdom": sdom, "gsb": gsb}}) is neutral


# ---------------------------------------------------------------------------
# Exact-boundary and exclusion checks
# ---------------------------------------------------------------------------


def test_adapt_is_excluded_from_the_candidate_set_in_the_analysis() -> None:
    # ADAPT beats everyone and the fixed members are cyclic: an adaptive winner
    # must never read as "no choice" (PR Sec 3.1).
    def adapt_on_top(a: str, b: str, seed: int) -> Match:
        if "ADAPT" in (a, b):
            return Match.win("A" if a == "ADAPT" else "B", ticks=3)
        return cyclic(a, b, seed)
    reading = analyze_e6.read_condition(f1(adapt_on_top), seeds=SEEDS, draws=payoff.resample_positions(4, resamples=20))
    assert reading.point.universal == frozenset() and reading.point.p_none
    assert all("ADAPT" not in members for members in reading.point.br.values())
    assert all("ADAPT" in members for members in reading.adapt_br.values())
    assert analyze_e6.h1(reading) == SUPPORTED


def _pairs(n: int) -> list[dict[str, Any]]:
    return [_cell(PID["RUSH"], PID["GUARD"], "candidate_first", seed, Match.win("A", ticks=50))
            for seed in range(1, n + 1)]


def test_h0_b_counts_only_the_cells_a_counts() -> None:
    # 100 paired cells: 5 change class but end later; 10 keep their class but end earlier.
    control = _pairs(100)
    treatment = [
        {**cell, "outcome": "tie", "ticks_run": 900} if index < 5
        else {**cell, "ticks_run": 10} if index < 15 else cell
        for index, cell in enumerate(control)
    ]
    result = analyze_e6.h0(control, treatment)
    assert (result["A"], result["B"]) == ("19/20", "17/19")  # B = 85/95, over A's 95 cells only
    assert result["status"] == NEITHER  # counting the 5 later class-changes too would give 90/95


def test_h0_exact_nine_tenths_bounds_are_inclusive() -> None:
    control = _pairs(10)
    earlier_one = [{**cell, "ticks_run": 10} if index == 0 else cell for index, cell in enumerate(control)]
    assert (analyze_e6.h0(control, earlier_one)["B"], analyze_e6.h0(control, earlier_one)["status"]) == (
        "9/10", SUPPORTED)
    changed_one = [{**cell, "outcome": "tie"} if index == 0 else cell for index, cell in enumerate(control)]
    assert (analyze_e6.h0(control, changed_one)["A"], analyze_e6.h0(control, changed_one)["status"]) == (
        "9/10", SUPPORTED)


FIVE_SEEDS = (11, 22, 33, 44, 55)


def test_pf1_and_pf2_raise_at_exactly_one_tenth() -> None:
    control = condition("C", dominance, seeds=FIVE_SEEDS)
    n = len(control.f1)
    assert n == 360
    decided = [index for index, cell in enumerate(control.f1) if cell["termination_reason"] != "tick_limit"]
    chosen = set(decided[:36])
    stalled = ConditionData("T", tuple({**cell, "termination_reason": "tick_limit"} if index in chosen else cell
                                       for index, cell in enumerate(control.f1)), control.f2, control.contact)
    flags = analyze_e6.pathology(control, stalled)
    assert flags["PF-1"]["raised"] is True
    keys = list(control.contact)
    detached = ConditionData("T", control.f1, control.f2, {key: index >= 36 for index, key in enumerate(keys)})
    flags = analyze_e6.pathology(control, detached)
    assert (flags["PF-2"]["raised"], flags["PF-2"]["treatment"]) == (True, "1/10")


@pytest.mark.parametrize(("stab", "fires"), [(Fraction(9, 10), True), (Fraction(89, 100), False)])
def test_kc2_needs_nine_tenths_stability(stab: Fraction, fires: bool) -> None:
    point = payoff.Reading(u={}, br={}, universal=frozenset({"GREED"}), delta={})
    reading = analyze_e6.ConditionReading(table=None, point=point, stab={"universal:GREED": stab},  # type: ignore[arg-type]
                                          adapt_br={})
    pf = {"PF-1": {"raised": False}, "PF-2": {"raised": False}, "PF-4": {"raised": False}}
    kills = analyze_e6.kill_criteria(h1t=REFUTED, treatment=reading, pf=pf, h3_status=NEITHER)
    assert kills["KC-2"]["fires"] is fires
    assert kills["KC-1"] == {"fires": True, "label": "greed dominance"}
