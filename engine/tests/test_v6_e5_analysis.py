"""V6 E5 analysis: bands, transitions, units, classification, census, statuses
and the interpretation table (Revision 1 Sec R5-R6; ``preregistration.json``).

The research lead required, before any treatment exists, tests proving that:

1. every possible control/treatment BP-band pair maps to exactly one
   transition class (``test_every_band_pair_maps_to_exactly_one_class``);
2. every (E5-D, E5-H1, E5-H2) status combination maps to exactly one
   interpretation outcome, including "none", or fails closed as impossible
   (``test_every_status_combination_maps_to_exactly_one_outcome_or_fails_closed``);
3. simultaneous H1/H2 SUPPORTED is an invariant violation, never resolved by
   precedence (``test_both_supported_is_an_invariant_violation``, and
   ``test_the_census_cannot_support_both``);
4. NEITHER is never treated as REFUTED
   (``test_neither_is_never_read_as_refuted`` and the status tests).
"""

from __future__ import annotations

import json
from fractions import Fraction
from itertools import product
from typing import Any

import pytest

from tools.research.v6.e5 import analyze_e5 as a
from tools.research.v6.e5 import preregistration as p
from tools.research.v6.e5.cell_metrics import DEFINED, parity_value

PREREG = p.load_preregistration()
CRITERIA = {item["id"]: item["criterion"] for item in PREREG["hypotheses"]}
S, R, N, NE = "SUPPORTED", "REFUTED", "NEITHER", "NOT_EVALUABLE"


def summary(value: Fraction | None) -> dict[str, Any]:
    return a.median_summary([value] * 4 if value is not None else [None] * 4)


# ---------------------------------------------------------------------------
# O-BP and the bands
# ---------------------------------------------------------------------------


def test_parity_value_is_the_exact_second_minus_first_share() -> None:
    assert parity_value(500, 500, 0, 500) == 1
    assert parity_value(0, 500, 500, 500) == -1
    assert parity_value(497, 500, 1, 500) == Fraction(496, 500)
    assert parity_value(1, 3, 1, 3) == 0
    # Unequal parity counts: shares, not counts.
    assert parity_value(5, 10, 0, 11) == Fraction(1, 2)


@pytest.mark.parametrize(("value", "band"), [
    (Fraction(1), a.SECOND_STRONG), (Fraction(2, 3), a.SECOND_STRONG),
    (Fraction(2, 3) - Fraction(1, 10**9), a.SECOND_MODERATE), (Fraction(1, 3), a.SECOND_MODERATE),
    (Fraction(1, 3) - Fraction(1, 10**9), a.NEUTRAL), (Fraction(0), a.NEUTRAL),
    (-Fraction(1, 3) + Fraction(1, 10**9), a.NEUTRAL), (-Fraction(1, 3), a.FIRST_MODERATE),
    (-Fraction(2, 3) + Fraction(1, 10**9), a.FIRST_MODERATE), (-Fraction(2, 3), a.FIRST_STRONG),
    (Fraction(-1), a.FIRST_STRONG),
])
def test_bp_band_edges_are_exact_and_closed_away_from_neutral(value: Fraction, band: str) -> None:
    assert a.bp_band(value) == band


def test_band_sides_and_strengths() -> None:
    assert [a.band_side(b) for b in a.BANDS] == [a.FIRST_SIDE, a.FIRST_SIDE, None, a.SECOND_SIDE, a.SECOND_SIDE]
    assert [a.band_strength(b) for b in a.BANDS] == [2, 1, 0, 1, 2]
    with pytest.raises(ValueError):
        a.band_side("second-mild")


def test_near_boundary_flags_within_one_fiftieth_of_an_edge() -> None:
    assert a.near_boundary(Fraction(1, 3) + Fraction(1, 50))
    assert a.near_boundary(-Fraction(2, 3))
    assert not a.near_boundary(Fraction(1, 3) + Fraction(1, 49))
    assert not a.near_boundary(Fraction(1))


# ---------------------------------------------------------------------------
# Unit values (O-UNIT-STATUS, O-BP-UNIT)
# ---------------------------------------------------------------------------


def test_unit_median_is_exact_and_even_counts_average_the_middle_pair() -> None:
    s = a.median_summary([Fraction(1), Fraction(0), Fraction(1, 3), Fraction(2, 3)])
    assert (s["status"], s["median_exact"], s["band"]) == (DEFINED, "1/2", a.SECOND_MODERATE)


def test_a_unit_is_decided_early_with_fewer_than_half_defined_cells() -> None:
    assert a.median_summary([None, None, None, Fraction(1)])["status"] == a.DECIDED_EARLY_CLASS
    # Exactly half defined is DEFINED (E4's rule: 2 x defined < cells).
    half = a.median_summary([None, None, Fraction(1), Fraction(1)])
    assert (half["status"], half["median_exact"]) == (DEFINED, "1/1")
    assert a.median_summary([])["status"] == a.DECIDED_EARLY_CLASS


def _e5(bp_a: str | None, bp_b: str | None) -> dict[str, Any]:
    def reading(value: str | None) -> dict[str, Any]:
        return {"status": DEFINED if value is not None else "DECIDED_EARLY", "exact": value}
    return {"bp": {"A": reading(bp_a), "B": reading(bp_b)}}


def test_a_mirror_cell_is_the_mean_of_its_two_victims() -> None:
    assert a.cell_value(_e5("1/1", "0/1"), a.MIRROR_VICTIMS) == Fraction(1, 2)
    assert a.cell_value(_e5("1/1", "0/1"), "A") == 1
    assert a.cell_value(_e5(None, None), a.MIRROR_VICTIMS) is None
    with pytest.raises(ValueError):
        a.cell_value(_e5("1/1", None), a.MIRROR_VICTIMS)


# ---------------------------------------------------------------------------
# Transitions (O-TRANSITION-E5) -- requirement 1
# ---------------------------------------------------------------------------

EXPECTED_SECOND_SIDE = {
    # (control band, treatment band) -> class, for a second-side control
    (a.SECOND_STRONG, a.SECOND_STRONG): a.STAYS, (a.SECOND_STRONG, a.SECOND_MODERATE): a.WEAKENED,
    (a.SECOND_STRONG, a.NEUTRAL): a.NEUTRALIZED, (a.SECOND_STRONG, a.FIRST_MODERATE): a.FLIPPED,
    (a.SECOND_STRONG, a.FIRST_STRONG): a.FLIPPED, (a.SECOND_MODERATE, a.SECOND_STRONG): a.STRENGTHENED,
    (a.SECOND_MODERATE, a.SECOND_MODERATE): a.STAYS, (a.SECOND_MODERATE, a.NEUTRAL): a.NEUTRALIZED,
    (a.SECOND_MODERATE, a.FIRST_MODERATE): a.FLIPPED, (a.SECOND_MODERATE, a.FIRST_STRONG): a.FLIPPED,
}
BAND_VALUE = {a.SECOND_STRONG: Fraction(1), a.SECOND_MODERATE: Fraction(1, 2), a.NEUTRAL: Fraction(0),
              a.FIRST_MODERATE: -Fraction(1, 2), a.FIRST_STRONG: Fraction(-1)}


def _expected(c_band: str, t_band: str) -> str:
    if a.band_side(c_band) == a.FIRST_SIDE:
        return a.FIRST_SIDE_CONTROL
    if a.band_side(c_band) is None:
        return a.UNCHANGED_NEUTRAL if a.band_side(t_band) is None else a.NEW
    return EXPECTED_SECOND_SIDE[(c_band, t_band)]


@pytest.mark.parametrize(("c_band", "t_band"), list(product(a.BANDS, a.BANDS)))
def test_every_band_pair_maps_to_exactly_one_class(c_band: str, t_band: str) -> None:
    got = a.transition_class(summary(BAND_VALUE[c_band]), summary(BAND_VALUE[t_band]))
    assert got == _expected(c_band, t_band)
    assert got in a.TRANSITION_CLASSES


@pytest.mark.parametrize("band", a.BANDS)
def test_decided_early_takes_precedence_on_either_side(band: str) -> None:
    early = summary(None)
    assert a.transition_class(early, summary(BAND_VALUE[band])) == a.DECIDED_EARLY_CLASS
    assert a.transition_class(summary(BAND_VALUE[band]), early) == a.DECIDED_EARLY_CLASS
    assert a.transition_class(early, early) == a.DECIDED_EARLY_CLASS


def test_the_transition_classes_partition_the_band_space() -> None:
    seen = {a.transition_class(summary(BAND_VALUE[c]), summary(BAND_VALUE[t])) for c, t in product(a.BANDS, a.BANDS)}
    seen.add(a.transition_class(summary(None), summary(Fraction(0))))
    assert seen == set(a.TRANSITION_CLASSES)


@pytest.mark.parametrize("band", a.BANDS)
def test_a_control_against_itself_is_always_an_identity_class(band: str) -> None:
    same = summary(BAND_VALUE[band])
    assert a.transition_class(same, same) in a.IDENTITY_CLASSES


def test_h1_and_h2_numerators_are_disjoint_second_side_classes() -> None:
    assert set(a.H1_CLASSES).isdisjoint(a.H2_CLASSES)
    assert set(a.H1_CLASSES) | set(a.H2_CLASSES) == set(EXPECTED_SECOND_SIDE.values())


# ---------------------------------------------------------------------------
# Statuses (O-STATUS-E5) -- requirement 4
# ---------------------------------------------------------------------------


def test_status_thresholds_are_inclusive() -> None:
    two_thirds, tenth = Fraction(2, 3), Fraction(1, 10)
    assert a.status_of(Fraction(2, 3), two_thirds, tenth) == S
    assert a.status_of(Fraction(1, 10), two_thirds, tenth) == R
    assert a.status_of(None, two_thirds, tenth) == NE


@pytest.mark.parametrize("value", [Fraction(1, 10) + Fraction(1, 10**6), Fraction(1, 3), Fraction(1, 2),
                                   Fraction(2, 3) - Fraction(1, 10**6)])
def test_neither_is_never_read_as_refuted(value: Fraction) -> None:
    assert a.status_of(value, Fraction(2, 3), Fraction(1, 10)) == N


def _rows(**classes: int) -> list[dict[str, Any]]:
    return [{"transition": name.replace("_", "-")} for name, count in classes.items() for _ in range(count)]


def test_census_values_and_the_decided_early_denominator() -> None:
    rows = _rows(STAYS=4, WEAKENED=1, NEUTRALIZED=1, FLIPPED=1, STRENGTHENED=1, DECIDED_EARLY=2)
    out = a.census_hypotheses(rows, CRITERIA)
    assert out["units"] == 10
    assert (out["E5-H1"]["count"], out["E5-H2"]["count"], out["decided_early"]["count"]) == (3, 5, 2)
    assert out["E5-H1"]["split"] == {"NEUTRALIZED": 1, "WEAKENED": 1, "FLIPPED": 1}
    assert (out["E5-H1"]["status"], out["E5-H2"]["status"]) == (N, N)


def test_a_non_census_class_in_p_base_fails_closed() -> None:
    with pytest.raises(a.InterpretationInvariantError):
        a.census_hypotheses(_rows(STAYS=5, NEW=1), CRITERIA)


def test_the_census_cannot_support_both() -> None:
    # Requirement 3 at the census level: disjoint numerators never both reach 2/3.
    for h1, h2, de in product(range(10), repeat=3):
        n = h1 + h2 + de
        if n == 0:
            continue
        rows = _rows(NEUTRALIZED=h1, STAYS=h2, DECIDED_EARLY=de)
        out = a.census_hypotheses(rows, CRITERIA)
        assert (out["E5-H1"]["status"], out["E5-H2"]["status"]) != (S, S)


def test_supported_h2_with_a_neither_h1_is_reachable_and_is_not_r_h2() -> None:
    # 24 of 30 STAY, 6 neutralize: H2 supported, H1 NEITHER (the E4 trap).
    out = a.census_hypotheses(_rows(STAYS=24, NEUTRALIZED=6), CRITERIA)
    assert (out["E5-H1"]["status"], out["E5-H2"]["status"]) == (N, S)
    assert a.interpret("PASS", N, S, PREREG)["outcome"] == "R-H2-PRIME"


# ---------------------------------------------------------------------------
# The interpretation table (O-INTERPRETATION-E5) -- requirements 2-4
# ---------------------------------------------------------------------------

EXPECTED_OUTCOME = {
    ("PASS", R, S): "R-H2", ("PASS", N, S): "R-H2-PRIME", ("PASS", S, R): "R-H1", ("PASS", S, N): "R-H1-PRIME",
    ("PASS", N, N): "NONE", ("PASS", N, R): "NONE", ("PASS", R, N): "NONE", ("PASS", R, R): "NONE",
}


@pytest.mark.parametrize(("d", "h1", "h2"), list(product(("PASS", "FAIL"), (S, R, N, NE), (S, R, N, NE))))
def test_every_status_combination_maps_to_exactly_one_outcome_or_fails_closed(d: str, h1: str, h2: str) -> None:
    impossible = (h1, h2) == (S, S) or NE in (h1, h2)
    if impossible:
        with pytest.raises(a.InterpretationInvariantError, match="impossible"):
            a.interpret(d, h1, h2, PREREG)
        return
    out = a.interpret(d, h1, h2, PREREG)
    assert out["outcome"] == ("STOP" if d == "FAIL" else EXPECTED_OUTCOME[(d, h1, h2)])
    assert out["reading"]


@pytest.mark.parametrize("d", ["PASS", "FAIL"])
def test_both_supported_is_an_invariant_violation(d: str) -> None:
    with pytest.raises(a.InterpretationInvariantError, match="impossible"):
        a.interpret(d, S, S, PREREG)


def test_neither_is_not_refuted_in_the_rows() -> None:
    # A row that would need H1 REFUTED never fires on H1 NEITHER, and vice versa.
    assert a.interpret("PASS", N, S, PREREG)["outcome"] != a.interpret("PASS", R, S, PREREG)["outcome"]
    assert a.interpret("PASS", S, N, PREREG)["outcome"] != a.interpret("PASS", S, R, PREREG)["outcome"]


def test_the_none_row_is_the_registered_outcome_for_mixed_results() -> None:
    out = a.interpret("PASS", N, N, PREREG)
    assert out["outcome"] == "NONE" and "No registered interpretation row applies" in out["reading"]


def test_the_r_h2_reading_is_the_lead_s_combined_wording() -> None:
    reading = a.interpret("PASS", R, S, PREREG)["reading"]
    assert reading.startswith("Co-location is not necessary for the directed base privilege.")
    assert "Combined with E4's finding" in reading


def test_unknown_inputs_fail_closed() -> None:
    for args in (("MAYBE", S, R), ("PASS", "SUPPORTED?", R), ("PASS", S, "")):
        with pytest.raises(a.InterpretationInvariantError):
            a.interpret(*args, PREREG)


def test_a_table_with_a_gap_or_an_overlap_does_not_load() -> None:
    table = json.loads(json.dumps(PREREG["interpretation"]))
    table["rows"] = [row for row in table["rows"] if row["id"] != "R-H2-PRIME"]
    with pytest.raises(p.PreregistrationError, match="matches 0 rows"):
        p.check_table_is_total(table)
    table = json.loads(json.dumps(PREREG["interpretation"]))
    table["rows"][0]["combinations"].append([S, S])
    with pytest.raises(p.PreregistrationError, match="impossible but matches"):
        p.check_table_is_total(table)
    table = json.loads(json.dumps(PREREG["interpretation"]))
    table["rows"][1]["combinations"].append([N, S])
    with pytest.raises(p.PreregistrationError, match="matches 2 rows"):
        p.check_table_is_total(table)


# ---------------------------------------------------------------------------
# Contest classification (O-CONTEST-E5)
# ---------------------------------------------------------------------------


class _Run:
    """A minimal FieldRun stand-in whose cells carry one attacker audit each."""

    def __init__(self, audits: list[dict[str, Any] | None], seat: str = "A") -> None:
        self.audits = audits
        self.seat = seat

    def e3(self, key: str) -> dict[str, Any]:
        audit = self.audits[int(key)]
        return {"seats": {self.seat: {"capture": {"core_inference": audit}}}}


def _audit(status: str, correct: bool | None = True) -> dict[str, Any]:
    return {"status": status, "correct": correct}


@pytest.mark.parametrize(("attacker", "audits", "expected"), [
    ("e2_sniper", [_audit("inferred")] * 3, a.SWEEP_BACKED),
    ("e2_sniper_twin", [_audit("inferred")] * 3, a.SWEEP_BACKED),
    ("e2_sniper", [_audit("not_inferred", None)] * 3, a.ANCHOR_ONLY),
    ("e2_sniper", [_audit("inferred"), _audit("not_inferred", None)], a.MIXED_INFERENCE),
    ("e2_sniper", [_audit("ambiguous", None)] * 2, a.MIXED_INFERENCE),
    ("e2_sniper", [_audit("inferred", False)] * 2, a.MIXED_INFERENCE),
    ("e2_disrupt_guard", [None, None], a.ANCHOR_ONLY),
    ("e2_guarded_painter", [None], a.ANCHOR_ONLY),
    ("e2_repair_guard", [None], a.ANCHOR_ONLY),
    ("e2_min_guard", [_audit("inferred")] * 2, a.SWEEP_BACKED),
    ("e2_spread_defender", [_audit("inferred")] * 2, a.SWEEP_BACKED),
])
def test_directed_class_follows_the_sweep_role_and_the_control_audit(
    attacker: str, audits: list[dict[str, Any] | None], expected: str
) -> None:
    run = _Run(audits)
    keys = [str(i) for i in range(len(audits))]
    assert a.directed_class(run, keys, "A", attacker) == expected  # type: ignore[arg-type]
