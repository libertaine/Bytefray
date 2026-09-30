"""V6 E8: totality and invariants of the registered decision logic.

Pre-registration revision 4, §4 to §8. Every registered mapping is total and
fails closed: the interpretation rows cover every (E8-D, H8-SUB, H8-PAR)
triple exactly once; the four-outcome core answer is exhaustive and applied
in its registered order; the H8-ADAPT table covers every combination; the
KC8 labels are deterministic; the disposition is exhaustive. stab(P) >= 9/10
means at least 900 of the 1,000 registered resamples. H8-SEAT's and PF8-4's
bootstrap is joint: one seed-position tuple recomputes control and treatment
within each draw. No registered set can be changed after the freeze.
"""

from __future__ import annotations

import dataclasses
import random
from collections.abc import Collection
from fractions import Fraction
from itertools import chain, combinations, permutations, product
from types import MappingProxyType

import pytest

from tools.research.v6.e6 import payoff as e6_payoff
from tools.research.v6.e8 import decision as d

S, R, N = d.SUPPORTED, d.REFUTED, d.NEITHER
NE = d.NOT_EVALUABLE


def _subsets(items: tuple[str, ...]) -> list[frozenset[str]]:
    return [frozenset(c) for c in chain.from_iterable(combinations(items, k) for k in range(1, len(items) + 1))]


# ---------------------------------------------------------------------------
# O-BOOT and stability
# ---------------------------------------------------------------------------


def test_the_draws_are_e6s_convention_exactly() -> None:
    assert d.DRAWS == tuple(e6_payoff.resample_positions(32))
    assert len(d.DRAWS) == 1000 and all(len(draw) == 32 for draw in d.DRAWS)
    assert all(0 <= position < 32 for draw in d.DRAWS for position in draw)
    rng = random.Random(42)
    assert d.DRAWS[0] == tuple(rng.randrange(32) for _ in range(32))
    assert d.resample_positions() == d.DRAWS


def test_stab_at_least_nine_tenths_means_at_least_900_of_1000() -> None:
    assert d.RESAMPLES == 1000 and d.STABILITY == Fraction(9, 10) and d.STABILITY_COUNT == 900
    assert [count for count in range(1001) if d.stable(count)] == list(range(900, 1001))
    assert d.stable(900) and not d.stable(899)


@pytest.mark.parametrize("count", [-1, 1001, 900.0, True, Fraction(900)])
def test_a_malformed_stability_count_fails_closed(count: object) -> None:
    with pytest.raises(d.DecisionInvariantError):
        d.stable(count)  # type: ignore[arg-type]


def test_only_the_registered_resample_count_is_accepted() -> None:
    with pytest.raises(d.DecisionInvariantError):
        d.stable(900, 999)
    with pytest.raises(d.DecisionInvariantError):
        d.stability_count(lambda positions: True, d.DRAWS[:999])
    assert d.stability_count(lambda positions: positions[0] < 16) == sum(1 for p in d.DRAWS if p[0] < 16)


def test_the_quantiles_are_the_registered_indices() -> None:
    values = [Fraction(k) for k in range(1000)]
    random.Random(7).shuffle(values)
    assert [d.quantile(values, q) for q in d.QUANTILES] == [25, 500, 974]
    with pytest.raises(d.DecisionInvariantError):
        d.quantile(values[:999], "0.5")


# ---------------------------------------------------------------------------
# Hypothesis statuses
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(("point_for", "count_for", "point_against", "count_against", "wanted"), [
    (True, 900, False, 0, S), (True, 899, False, 0, N), (False, 1000, True, 900, R), (False, 0, True, 899, N),
    (False, 0, False, 1000, N), (True, 1000, False, 1000, S), (False, 1000, False, 0, N),
])
def test_bootstrap_status(point_for: bool, count_for: int, point_against: bool, count_against: int,
                          wanted: str) -> None:
    assert d.bootstrap_status(point_for, count_for, point_against, count_against) == wanted


def test_both_point_predicates_holding_fails_closed() -> None:
    with pytest.raises(d.DecisionInvariantError):
        d.bootstrap_status(True, 1000, True, 1000)


def test_complement_status_is_exhaustive() -> None:
    for point, count in product((True, False), range(1001)):
        status = d.complement_status(point, count)
        wanted = S if point and count >= 900 else R if not point and 1000 - count >= 900 else N
        assert status == wanted


def test_h8_repeat_is_not_evaluable_exactly_when_the_census_is_empty() -> None:
    assert d.repeat_status(()) == NE
    assert d.repeat_status(("EVADE8",), True, 950, False, 0) == S
    with pytest.raises(d.DecisionInvariantError):
        d.repeat_status((), True, 950, False, 0)
    with pytest.raises(d.DecisionInvariantError):
        d.repeat_status(("EVADE8",))


def test_h8_fl() -> None:
    cells = [(a, dd) for a in d.ATTACKERS for dd in d.DEFENDERS]
    assert d.fl_status(dict.fromkeys(cells, Fraction(0))) == R
    assert d.fl_status(dict.fromkeys(cells, Fraction(1, 10))) == R
    fl = dict.fromkeys(cells, Fraction(0))
    fl.update({("RUSH8", dd): Fraction(9, 10) for dd in d.DEFENDERS})
    assert d.fl_status(fl) == S
    fl[("RUSH8", "STRESS8")] = Fraction(89, 100)
    assert d.fl_status(fl) == N
    with pytest.raises(d.DecisionInvariantError):
        d.fl_status({("RUSH8", "GUARD8"): Fraction(1)})


@pytest.mark.parametrize(("a", "b", "wanted"), [
    (Fraction(0), None, R), (Fraction(2, 3), Fraction(1), R), (Fraction(9, 10), Fraction(9, 10), S),
    (Fraction(1), Fraction(1), S), (Fraction(9, 10), Fraction(89, 100), N), (Fraction(89, 100), Fraction(1), N),
])
def test_h8_tax(a: Fraction, b: Fraction | None, wanted: str) -> None:
    assert d.tax_status(a, b) == wanted


def test_h8_tax_has_no_empty_denominator_convention() -> None:
    with pytest.raises(d.DecisionInvariantError):
        d.tax_status(Fraction(0), Fraction(1))
    with pytest.raises(d.DecisionInvariantError):
        d.tax_status(Fraction(1, 2), None)


# ---------------------------------------------------------------------------
# §7.1: every triple maps to exactly one row
# ---------------------------------------------------------------------------


def test_every_triple_maps_to_exactly_one_row() -> None:
    covered = {}
    for triple in product(d.GATE_STATUSES, d.STATUSES, d.STATUSES):
        covered[triple] = d.row_for(*triple).row_id
    assert len(covered) == 18
    assert {t for t, row in covered.items() if row == "STOP"} == set(product(("FAIL",), d.STATUSES, d.STATUSES))
    assert covered[("PASS", S, S)] == "R8-PRESERVES" and covered[("PASS", S, R)] == "R8-CREATES"
    assert covered[("PASS", R, S)] == "R8-REMOVES" and covered[("PASS", R, R)] == "R8-NO-CHOICE"
    assert covered[("PASS", S, N)] == "R8-T-ONLY" and covered[("PASS", R, N)] == "R8-T-DOMINANT"
    assert {covered[("PASS", N, par)] for par in d.STATUSES} == {"NONE"}
    rows_as_partition = [pair for row in d.ROWS if row.e8_d == "PASS" for pair in row.pairs]
    assert len(rows_as_partition) == 9 == len(set(rows_as_partition))


@pytest.mark.parametrize("triple", [("PASS", "SUPPORTED", "NOT EVALUABLE"), ("OK", S, S), ("PASS", "supported", S)])
def test_an_unregistered_status_fails_closed(triple: tuple[str, str, str]) -> None:
    with pytest.raises(d.DecisionInvariantError):
        d.row_for(*triple)


def test_an_overlapping_or_missing_row_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    overlapping = (*d.ROWS, d.Row("EXTRA", "PASS", frozenset({(S, S)}), "extra"))
    monkeypatch.setattr(d, "ROWS", overlapping)
    with pytest.raises(d.DecisionInvariantError, match="R8-PRESERVES"):
        d.row_for("PASS", S, S)
    monkeypatch.setattr(d, "ROWS", tuple(row for row in overlapping if row.row_id not in ("EXTRA", "NONE")))
    with pytest.raises(d.DecisionInvariantError):
        d.row_for("PASS", N, N)


def test_qualifiers() -> None:
    assert d.qualifiers(d.row_for("FAIL", S, S), h8_channel=S, h8_less=S, h8_tax=S) == ()
    preserves = d.qualifiers(d.row_for("PASS", S, S), h8_channel=S, h8_less=N, h8_tax=S)
    assert [(q.hypothesis, q.status) for q in preserves] == [("H8-CHANNEL", S), ("H8-LESS", N)]
    no_choice = d.qualifiers(d.row_for("PASS", R, R), h8_channel=R, h8_less=R, h8_tax=N,
                             universal_a8={"LURK8"})
    assert [(q.hypothesis, q.status) for q in no_choice] == [("H8-CHANNEL", R), ("H8-LESS", R), ("H8-TAX", N)]
    assert no_choice[0].naming == "naming every universal member of A8 and giving KC8-6's label"
    assert no_choice[0].label == d.Label("information dominated", ("LURK8",), False)
    assert no_choice[2].text == "a dominant policy under both channels; delay-only is neither established nor excluded"
    assert {status: d.no_choice_qualifier(status) for status in d.STATUSES} == {
        S: "the substitution acts only as a delay: outcomes are preserved and delayed",
        R: "a dominant policy under both channels, with outcomes restructured",
        N: "a dominant policy under both channels; delay-only is neither established nor excluded"}
    with pytest.raises(d.DecisionInvariantError):
        d.qualifiers(d.row_for("PASS", R, R), h8_channel=R, h8_less=R, h8_tax=N)


# ---------------------------------------------------------------------------
# §7.4: the four outcomes are exhaustive and applied in order
# ---------------------------------------------------------------------------


def _definitions(e8_d: str, sub: str, channel: str, repeat: str) -> list[str]:
    """Each registered definition, read on its own, without the order."""
    components = (sub, channel, repeat)
    holds = []
    if e8_d == "FAIL" or (R not in components and repeat == NE):
        holds.append("NOT EVALUABLE")
    if e8_d == "PASS" and R in components:
        holds.append("NO")
    if all(c == S for c in components):
        holds.append("YES")
    if R not in components and N in components:
        holds.append("INDETERMINATE")
    return holds


def test_the_core_answer_is_exhaustive_and_ordered() -> None:
    assert d.CORE_ORDER == ("NOT EVALUABLE", "NO", "YES", "INDETERMINATE")
    combinations_seen = 0
    for e8_d, sub, channel, repeat in product(d.GATE_STATUSES, d.STATUSES, d.STATUSES, d.REPEAT_STATUSES):
        combinations_seen += 1
        answer = d.core_answer(e8_d=e8_d, h8_sub=sub, h8_channel=channel, h8_repeat=repeat)
        holding = _definitions(e8_d, sub, channel, repeat)
        assert holding, (e8_d, sub, channel, repeat)
        assert answer.outcome == min(holding, key=d.CORE_ORDER.index)
        assert (answer.scope_sentence is not None) == (answer.outcome == "YES")
    assert combinations_seen == 2 * 3 * 3 * 4


def test_the_order_decides_the_overlaps() -> None:
    # A failed gate voids every reading, even a refuted one.
    assert d.core_answer(e8_d="FAIL", h8_sub=R, h8_channel=S, h8_repeat=S).outcome == "NOT EVALUABLE"
    assert d.core_answer(e8_d="FAIL", h8_sub=S, h8_channel=S, h8_repeat=S).outcome == "NOT EVALUABLE"
    # One refuted component falsifies the conjunction whether or not the others can be evaluated.
    assert d.core_answer(e8_d="PASS", h8_sub=R, h8_channel=N, h8_repeat=NE).outcome == "NO"
    assert d.core_answer(e8_d="PASS", h8_sub=S, h8_channel=S, h8_repeat=NE).outcome == "NOT EVALUABLE"
    assert d.core_answer(e8_d="PASS", h8_sub=S, h8_channel=N, h8_repeat=S).outcome == "INDETERMINATE"
    assert d.core_answer(e8_d="PASS", h8_sub=S, h8_channel=S, h8_repeat=S).scope_sentence == d.SCOPE_SENTENCE


def test_a_reordered_core_answer_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(d, "CORE_ORDER", ("NO", "NOT EVALUABLE", "YES", "INDETERMINATE"))
    with pytest.raises(d.DecisionInvariantError, match="order"):
        d.core_answer(e8_d="PASS", h8_sub=S, h8_channel=S, h8_repeat=S)


# ---------------------------------------------------------------------------
# §7.3: H8-REPEAT and H8-ADAPT readings
# ---------------------------------------------------------------------------


def test_the_repeat_readings_name_the_census_and_carry_the_scope_sentence() -> None:
    reading = d.repeat_reading(S, ("EVADE8",))
    assert reading.text.startswith("Against the census {EVADE8}, re-acquiring a relocated anchor")
    assert all(d.repeat_reading(status, ("EVADE8",)).scope_sentence == d.SCOPE_SENTENCE for status in d.STATUSES)
    assert d.repeat_reading(NE, ()).text == "The frozen census is empty, so there is no repeated-choice claim."
    with pytest.raises(d.DecisionInvariantError):
        d.repeat_reading(NE, ("EVADE8",))
    with pytest.raises(d.DecisionInvariantError):
        d.repeat_reading(S, ())


def test_every_h8_adapt_combination_maps_to_one_reading_or_fails_closed() -> None:
    outcomes: dict[str, int] = {}
    for sub, repeat, check, adapt in product(d.STATUSES, d.REPEAT_STATUSES, (True, False, None), (*d.STATUSES, None)):
        census = () if repeat == NE else ("EVADE8",)
        interpretable = sub == S and repeat == S and check is True
        consistent = (repeat == NE and check is None and adapt is None) or (
            repeat != NE and check is not None and ((interpretable and adapt is not None)
                                                    or (not interpretable and adapt is None)))
        if not consistent:
            with pytest.raises(d.DecisionInvariantError):
                d.adapt_reading(h8_sub=sub, h8_repeat=repeat, check=check, h8_adapt=adapt, census=census)
            continue
        reading = d.adapt_reading(h8_sub=sub, h8_repeat=repeat, check=check, h8_adapt=adapt, census=census)
        outcomes[reading.status] = outcomes.get(reading.status, 0) + 1
        if repeat == NE:
            assert (reading.interpretable, reading.status) == (None, NE)
        elif interpretable:
            assert (reading.interpretable, reading.status) == (True, adapt)
            assert "{EVADE8}" in reading.text
        else:
            assert (reading.interpretable, reading.status) == (False, d.NOT_INTERPRETABLE)
            assert reading.note == "There was no demonstrated repeated choice to adapt to. It is never read as a refutation of adaptation."
    assert outcomes == {S: 1, R: 1, N: 1, d.NOT_INTERPRETABLE: 3 * 3 * 2 - 1, NE: 3}


def test_the_allocation_check_uses_the_static_set() -> None:
    assert d.static_set(("EVADE8",)) == ("RUSH8", "REACQ8", "PACED8", "STEALTH8", "LURK8", "SPLIT8", "GUARD8",
                                         "GREED8", "STRESS8")
    verification = dict.fromkeys(d.MEMBERS, Fraction(5))
    verification["EVADE8"] = Fraction(6)
    assert d.allocation_check(verification, ("EVADE8",))
    verification["GUARD8"] = Fraction(6)
    assert not d.allocation_check(verification, ("EVADE8",))
    with pytest.raises(d.DecisionInvariantError):
        d.allocation_check(verification, ())


# ---------------------------------------------------------------------------
# §8: the KC8 labels are deterministic
# ---------------------------------------------------------------------------


def _kc8_1_by_definition(universal: frozenset[str]) -> str:
    if all(d.ACQUIRE[m] != "none" for m in universal):
        return "search race"
    if "GREED8" in universal:
        return "greed dominance"
    return "other dominance"


def _kc8_6_by_definition(universal: frozenset[str]) -> str:
    if all(d.ACQUIRE[m] != "none" for m in universal):
        return "channel race"
    if universal == {"LURK8"}:
        return "information dominated"
    return "mixed dominance"


def test_kc8_1_labels_every_universal_set_deterministically() -> None:
    subsets = _subsets(d.PI_F)
    assert len(subsets) == 2 ** 10 - 1
    for universal in subsets:
        label = d.kc8_1_label(universal)
        assert label.label == _kc8_1_by_definition(universal)
        assert label.members == tuple(m for m in d.MEMBERS if m in universal)
        assert label.names_members == (label.label == "other dominance")
        for order in list(permutations(sorted(universal)))[:6]:
            assert d.kc8_1_label(list(order)) == label


def test_kc8_6_labels_every_universal_a8_set_deterministically() -> None:
    labels = {}
    for universal in _subsets(d.A8):
        label = d.kc8_6_label(universal)
        assert label.label == _kc8_6_by_definition(universal)
        assert label.names_members == (label.label == "mixed dominance")
        assert all(d.kc8_6_label(list(order)) == label for order in permutations(sorted(universal)))
        labels[universal] = label.label
    assert len(labels) == 31
    assert labels[frozenset({"LURK8"})] == "information dominated"
    assert labels[frozenset({"RUSH8", "REACQ8"})] == "channel race"
    assert labels[frozenset({"RUSH8", "LURK8"})] == "mixed dominance"
    assert sum(1 for label in labels.values() if label == "channel race") == 15


@pytest.mark.parametrize(("function", "universal"), [
    (d.kc8_1_label, set()), (d.kc8_6_label, set()), (d.kc8_1_label, {"ADAPT8"}), (d.kc8_6_label, {"SPLIT8"}),
])
def test_a_label_without_a_universal_member_or_outside_its_set_fails_closed(function: object,
                                                                            universal: Collection[str]) -> None:
    with pytest.raises(d.DecisionInvariantError):
        function(universal)  # type: ignore[operator]


def _kills(**overrides: object) -> dict[str, d.Kill]:
    arguments: dict[str, object] = {"h8_sub": N, "universal": set(), "greed_universal_count": 0, "pf8_1": False,
                                    "pf8_2": False, "h8_fl": N, "pf8_4": False, "h8_seat": N, "h8_channel": N,
                                    "universal_a8": set()}
    arguments.update(overrides)
    return dict(d.kill_criteria(**arguments))  # type: ignore[arg-type]


def test_the_kill_criteria_fire_exactly_as_registered() -> None:
    assert not any(kill.fires for kill in _kills().values())
    assert list(_kills()) == ["KC8-1", "KC8-2", "KC8-3", "KC8-4", "KC8-5", "KC8-6"]
    kc1 = _kills(h8_sub=R, universal={"GREED8", "RUSH8"})["KC8-1"]
    assert kc1.fires and kc1.label == d.Label("greed dominance", ("RUSH8", "GREED8"), False)
    assert _kills(h8_sub=R, universal={"GREED8"}, greed_universal_count=900)["KC8-2"].fires
    assert not _kills(h8_sub=R, universal={"GREED8"}, greed_universal_count=899)["KC8-2"].fires
    assert not _kills(h8_sub=N, universal={"RUSH8"}, greed_universal_count=1000)["KC8-2"].fires
    assert _kills(pf8_2=True)["KC8-3"].fires and _kills(h8_fl=S)["KC8-4"].fires
    seat = _kills(pf8_4=True, h8_seat=S, seat_detail={"delta_g": "1/50"})["KC8-5"]
    assert seat.fires and seat.detail is not None and seat.detail["layers"] == ("unit", "family")
    assert _kills(h8_seat=S)["KC8-5"].detail["layers"] == ("family",)  # type: ignore[index]
    kc6 = _kills(h8_channel=R, universal_a8={"LURK8", "PACED8"})["KC8-6"]
    assert kc6.fires and kc6.label == d.Label("mixed dominance", ("PACED8", "LURK8"), True)


@pytest.mark.parametrize("overrides", [
    {"h8_sub": S, "universal": {"RUSH8"}}, {"h8_sub": R, "universal": set()},
    {"h8_channel": S, "universal_a8": {"RUSH8"}}, {"h8_channel": R, "universal_a8": set()},
    {"universal": {"ADAPT8"}}, {"h8_fl": "NOT EVALUABLE"},
])
def test_an_impossible_kill_record_fails_closed(overrides: dict[str, object]) -> None:
    with pytest.raises(d.DecisionInvariantError):
        _kills(**overrides)


# ---------------------------------------------------------------------------
# §8: the disposition is exhaustive
# ---------------------------------------------------------------------------


def test_the_disposition_is_exhaustive() -> None:
    fired_sets = [(), *[(k,) for k in d.KILL_CRITERIA], d.KILL_CRITERIA]
    seen = set()
    for e8_d, sub, par, less, channel, repeat, fired in product(
            d.GATE_STATUSES, d.STATUSES, d.STATUSES, d.STATUSES, d.STATUSES, d.REPEAT_STATUSES, fired_sets):
        row = d.row_for(e8_d, sub, par)
        core = d.core_answer(e8_d=e8_d, h8_sub=sub, h8_channel=channel, h8_repeat=repeat)
        outcome = d.disposition(e8_d=e8_d, fired=fired, row=row, h8_less=less, core=core)
        seen.add(outcome)
        if e8_d == "FAIL":
            assert outcome == d.VOID
        elif fired:
            assert outcome == d.REJECT
        elif row.row_id in ("R8-PRESERVES", "R8-CREATES") and less == S and core.outcome == "YES":
            assert outcome == d.CANDIDATE
        else:
            assert outcome == d.NOT_ESTABLISHED
    assert seen == set(d.DISPOSITIONS)


def test_an_inconsistent_disposition_record_fails_closed() -> None:
    passing = d.core_answer(e8_d="PASS", h8_sub=S, h8_channel=S, h8_repeat=S)
    with pytest.raises(d.DecisionInvariantError):
        d.disposition(e8_d="FAIL", fired=(), row=d.row_for("PASS", S, S), h8_less=S, core=passing)
    with pytest.raises(d.DecisionInvariantError):
        d.disposition(e8_d="PASS", fired=("KC-1",), row=d.row_for("PASS", S, S), h8_less=S, core=passing)


# ---------------------------------------------------------------------------
# §6.2: the seat layers, with a joint bootstrap
# ---------------------------------------------------------------------------


def _per_seed_source(values: dict[tuple[str, tuple[str, ...]], list[Fraction]], *, sdom: Fraction = Fraction(1, 2)):
    """GSB per unit is the mean of per-seed values over the drawn positions; SDom is fixed."""

    def source(condition: str, unit: tuple[str, ...], positions: tuple[int, ...] | None) -> tuple[Fraction, Fraction]:
        series = values[(condition, unit)]
        drawn = range(len(series)) if positions is None else positions
        return sdom, sum((series[k] for k in drawn), Fraction(0)) / len(drawn)

    return source


def test_every_draw_recomputes_control_and_treatment_from_one_seed_multiset() -> None:
    calls: list[tuple[str, tuple[int, ...] | None]] = []

    def source(condition: str, unit: tuple[str, ...], positions: tuple[int, ...] | None) -> tuple[Fraction, Fraction]:
        calls.append((condition, positions))
        return Fraction(1, 2), Fraction(0)

    reading = d.seat_layers(source, control="C8", treatment="T8", units=d.SEAT_UNITS[:2])
    drawn = [(condition, positions) for condition, positions in calls if positions is not None]
    assert len(drawn) == 1000 * 2 * 2
    for index, draw in enumerate(d.DRAWS):
        block = drawn[index * 4:(index + 1) * 4]
        assert [condition for condition, _ in block] == ["C8", "C8", "T8", "T8"]
        assert all(positions is draw for _, positions in block)
    assert reading.h8_seat == R and reading.delta_g_nonpositive_count == 1000


def test_the_joint_bootstrap_keeps_a_paired_shift_stable_where_independent_draws_would_not() -> None:
    rng = random.Random(11)
    units = d.SEAT_UNITS
    noise = {u: [Fraction(rng.randint(-40, 40), 100) for _ in range(32)] for u in units}
    shift = Fraction(1, 200)
    values = {("C8", u): noise[u] for u in units} | {("T8", u): [x + shift if x >= 0 else x - shift for x in noise[u]]
                                                      for u in units}
    joint = d.seat_layers(_per_seed_source(values), control="C8", treatment="T8")
    assert joint.delta_g > 0 and joint.delta_g_positive_count == 1000 and joint.h8_seat == S
    # The same data resampled independently per condition is not stable: jointness is what the rule requires.
    other = random.Random(99)
    independent = [tuple(other.randrange(32) for _ in range(32)) for _ in range(1000)]
    source = _per_seed_source(values)
    positive = 0
    for draw_c, draw_t in zip(d.DRAWS, independent, strict=True):
        gc = {u: source("C8", u, draw_c)[1] for u in units}
        gt = {u: source("T8", u, draw_t)[1] for u in units}
        positive += d.delta_g(gc, gt) > 0
    assert positive < 900


def test_the_unit_layer_needs_a_stable_neutral_to_non_neutral_transition() -> None:
    stable_unit, unstable_unit, control_biased = d.SEAT_UNITS[0], d.SEAT_UNITS[1], d.SEAT_UNITS[2]
    units = (stable_unit, unstable_unit, control_biased)
    base = [Fraction(0)] * 32
    values = {
        ("C8", stable_unit): base, ("T8", stable_unit): [Fraction(1, 2)] * 32,
        # |GSB| = 7/64 > 1/10 at the point, but close enough to the bound to cross it in many draws.
        ("C8", unstable_unit): base, ("T8", unstable_unit): [Fraction(1, 2)] * 7 + [Fraction(0)] * 25,
        ("C8", control_biased): [Fraction(1, 2)] * 32, ("T8", control_biased): [Fraction(1, 2)] * 32,
    }
    reading = d.seat_layers(_per_seed_source(values), control="C8", treatment="T8", units=units)
    assert reading.flagged == (stable_unit,) and reading.pf8_4_raised
    assert reading.unit_stability[stable_unit] == 1000
    assert reading.unit_stability[unstable_unit] < 900
    assert control_biased not in reading.unit_stability


def test_identical_conditions_read_as_cq8_4_requires() -> None:
    values = {(c, u): [Fraction(k % 5, 20) for k in range(32)] for c in ("C8", "T8") for u in d.SEAT_UNITS}
    reading = d.seat_layers(_per_seed_source(values), control="C8", treatment="T8")
    assert reading.delta_g == 0 and reading.h8_seat == R and not reading.pf8_4_raised
    assert set(reading.quantiles) == {"0.025", "0.5", "0.975"} and set(reading.quantiles.values()) == {0}
    check = d.control_against_control(
        h8_sub=N, h8_par=N, h8_tax=S, a=Fraction(1), b=Fraction(1),
        pf8_raised={"PF8-1": False, "PF8-2": False, "PF8-3": False, "PF8-4": False}, flagged_units=0,
        h8_seat=reading.h8_seat, delta_g_point=reading.delta_g, delta_g_draws=[Fraction(0)] * 1000,
        row=d.row_for("PASS", N, N))
    assert check["PASS"]
    failing = d.control_against_control(
        h8_sub=N, h8_par=S, h8_tax=S, a=Fraction(1), b=Fraction(1),
        pf8_raised={"PF8-1": False, "PF8-2": False, "PF8-3": False, "PF8-4": False}, flagged_units=0,
        h8_seat=R, delta_g_point=Fraction(0), delta_g_draws=[Fraction(0)] * 1000, row=d.row_for("PASS", N, S))
    assert not failing["PASS"]


def test_o_neutral_is_closed_as_registered() -> None:
    assert d.neutral(Fraction(89, 100), Fraction(1, 10)) and d.neutral(Fraction(0), Fraction(-1, 10))
    assert not d.neutral(Fraction(9, 10), Fraction(0)) and not d.neutral(Fraction(0), Fraction(11, 100))


# ---------------------------------------------------------------------------
# Structure
# ---------------------------------------------------------------------------


def test_the_static_census_is_evade8_and_follows_the_parameters() -> None:
    assert d.census() == ("EVADE8",)
    changed = {m: dict(values) for m, values in d.PARAMETERS.items()}
    changed["EVADE8"]["evade"] = "off"
    assert d.census(changed) == ()
    changed["GUARD8"]["evade"] = "on-hit"
    assert d.census(changed) == ("GUARD8",)
    with pytest.raises(d.DecisionInvariantError):
        d.census({"EVADE8": d.PARAMETERS["EVADE8"]})


def test_d8_3_has_576_literal_same_opponent_pairs() -> None:
    pairs = d.d8_3_matched_pairs()
    assert len(pairs) == len(set(pairs)) == 576
    assert {pair.opponent for pair in pairs} == set(d.MEMBERS) - {"LURK8", "GREED8"}
    assert {pair.seat for pair in pairs} == {"A", "B"} and {pair.seed_position for pair in pairs} == set(range(32))


def test_the_seat_units() -> None:
    assert len(d.SEAT_UNITS) == 66 == len(set(d.SEAT_UNITS))
    assert sum(1 for u in d.SEAT_UNITS if u[0] == "pairing") == 55
    assert [u[1] for u in d.SEAT_UNITS if u[0] == "mirror"] == list(d.MEMBERS)


def test_the_companion_reading() -> None:
    statuses = {h: N for h in d.COMPANION_HYPOTHESES}
    kills = dict.fromkeys(d.KILL_CRITERIA, False)
    assert d.companion_reading(statuses, statuses, kills, kills) == d.CompanionReading(True, ())
    differing = d.companion_reading(statuses, {**statuses, "H8-REPEAT": R}, kills, {**kills, "KC8-3": True})
    assert not differing.agrees and len(differing.differences) == 2
    assert d.COMPANION_HYPOTHESES == ("H8-SUB", "H8-CHANNEL", "H8-LESS", "H8-REPEAT", "H8-FL")


# ---------------------------------------------------------------------------
# No registered set can be changed after the freeze
# ---------------------------------------------------------------------------


def test_the_registered_sets_are_immutable() -> None:
    for value in (d.MEMBERS, d.PI, d.PI_F, d.A8, d.ATTACKERS, d.DEFENDERS, d.PHASE_SENSITIVE, d.STATUSES,
                  d.ROWS, d.KILL_CRITERIA, d.CORE_ORDER, d.DISPOSITIONS, d.SEAT_UNITS, d.DRAWS, d.QUANTILES):
        assert isinstance(value, tuple)
    assert all(isinstance(row.pairs, frozenset) for row in d.ROWS)
    for mapping in (d.REGISTRATION, d.PARAMETERS, d.ACQUIRE, d.REGISTRATION["population"]["sets"]):
        assert isinstance(mapping, MappingProxyType)
        with pytest.raises(TypeError):
            mapping["X"] = "Y"  # type: ignore[index]
    with pytest.raises(AttributeError):
        d.REGISTRATION["population"]["sets"]["a8"].append("SPLIT8")
    with pytest.raises(dataclasses.FrozenInstanceError):
        d.ROWS[0].pairs = frozenset()  # type: ignore[misc]
    with pytest.raises(TypeError):
        d.PARAMETERS["EVADE8"]["evade"] = "off"  # type: ignore[index]


def test_results_are_immutable() -> None:
    kills = d.kill_criteria(h8_sub=N, universal=set(), greed_universal_count=0, pf8_1=False, pf8_2=False, h8_fl=N,
                            pf8_4=False, h8_seat=N, h8_channel=N, universal_a8=set())
    with pytest.raises(TypeError):
        kills["KC8-1"] = d.Kill(True)  # type: ignore[index]
    with pytest.raises(dataclasses.FrozenInstanceError):
        kills["KC8-1"].fires = True  # type: ignore[misc]
