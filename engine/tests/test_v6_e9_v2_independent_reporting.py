"""Independent frozen scientific priorities, exact boundaries and overrides."""

from __future__ import annotations

import hashlib
import json
from fractions import Fraction

import pytest

from engine.tests._e9_v2_synthetic_records import fixture, through_g
from tools.research.v6.e9.v2 import reporting
from tools.research.v6.e9.v2.records import record_ref


@pytest.mark.parametrize("row,integrity,positions,seat_b,status,severe,label", [
    (1, False, 2, 1, "SUPPORTED", (), "NOT EVALUABLE"),
    (2, True, 0, 0, "SUPPORTED", (), "REFUTED bounded benefit claim"),
    (3, True, 1, 0, "SUPPORTED", (), "NOT EVALUABLE"),
    (4, True, 2, 1, "REFUTED", (), "REFUTED bounded benefit claim"),
    (5, True, 2, 1, "UNRESOLVED", (), "Behavior demonstrated; benefit NEITHER"),
    (6, True, 2, 1, "SUPPORTED", ("seat dependence",), "Behavior demonstrated; benefit NEITHER"),
    (7, True, 2, 1, "SUPPORTED", (), "SUPPORTED beneficial adaptation"),
])
def test_seven_priorities_derive_from_frozen_truth_table(row, integrity, positions, seat_b, status, severe, label):
    result = reporting.classify_report(integrity=integrity, realized_positions=positions,
        seat_a_positions=min(positions, 1), seat_b_positions=seat_b,
        statuses={"F": status, "D": "SUPPORTED", "S": "SUPPORTED", "H": "UNRESOLVED"},
        severe_constraints=severe, gates_valid=True)
    assert result["scientific_priority_row"] == row
    assert result["scientific_classification"] == label
    assert result["effective_registered_status"] == label
    assert result["requirement_C_eligible"] is (row == 7)
    assert result["historical_coverage"] == "NOT ESTABLISHED"
    assert "Complete prior qualification history and exhaustive historical non-reuse were NOT ESTABLISHED" in result["permanent_limitation"]


@pytest.mark.parametrize("history,effective", [
    ("HOLD_PENDING_ADJUDICATION", "INTEGRITY_HOLD_PENDING_ADJUDICATION"),
    ("HISTORICAL_OVERLAP", "NOT EVALUABLE"),
    ("UNRESOLVED_HISTORICAL_INTEGRITY", "NOT EVALUABLE"),
    ("CANCELLED_PRECOLLECTION", "NOT PRODUCED"),
])
def test_historical_override_preserves_scientific_audit_withdraws_c(history, effective):
    result = reporting.classify_report(integrity=True, realized_positions=2, seat_a_positions=1,
        seat_b_positions=1, statuses=dict.fromkeys(("F", "D", "S", "H"), "SUPPORTED"),
        gates_valid=True, historical_integrity=history)
    assert result["effective_registered_status"] == effective
    assert result["requirement_C_eligible"] is False
    assert result["requirement_C"] == "NOT ESTABLISHED"
    if history != "CANCELLED_PRECOLLECTION":
        assert result["scientific_priority_row"] == 7
        assert result["F_D_S_H_statuses"]["F"] == "SUPPORTED"
    else:
        assert result["scientific_priority_row"] is None
        assert result["scientific_classification"] is None


def test_stored_supported_label_never_substitutes_for_missing_gates():
    result = reporting.classify_report(integrity=True, realized_positions=2, seat_a_positions=1,
        seat_b_positions=1, statuses=dict.fromkeys(("F", "D", "S", "H"), "SUPPORTED"))
    assert result["scientific_priority_row"] == 7
    assert result["requirement_C_eligible"] is False


@pytest.mark.parametrize("low,high,status", [
    (Fraction(1, 10), Fraction(1, 10), "SUPPORTED"),
    (Fraction(0), Fraction(1, 10), "UNRESOLVED"),
    (Fraction(0), Fraction(99, 1000), "REFUTED"),
    (Fraction(99, 1000), Fraction(101, 1000), "UNRESOLVED"),
])
def test_exact_rational_support_refutation_equalities(low, high, status):
    assert reporting.contrast_status(low, high) == status


def test_guarded_clipped_rows_and_upper_timing_width():
    means = {"A": Fraction(1, 2), "q": Fraction(1, 2), "zero": Fraction(0), "one": Fraction(1)}
    narrow = reporting.row_intervals(means, Fraction(0))
    assert narrow["zero"] == (Fraction(0), Fraction(1, 20))
    assert narrow["one"] == (Fraction(19, 20), Fraction(1))
    gap = reporting.contrast_interval(narrow["A"], [narrow["q"]])
    assert gap == (Fraction(-1, 10), Fraction(1, 10))
    assert reporting.timing_reproduced(Fraction(1, 10), gap[1]) is True
    wide = reporting.row_intervals(means, Fraction(51, 1000))
    wide_gap = reporting.contrast_interval(wide["A"], [wide["q"]])
    assert wide_gap[1] == Fraction(51, 500)
    assert reporting.timing_reproduced(Fraction(1, 10), wide_gap[1]) is False
    assert reporting.timing_reproduced(Fraction(99, 1000), gap[1]) is False


def test_negative_uncertainty_envelope_never_becomes_valid_through_guard():
    with pytest.raises(ValueError):
        reporting.row_intervals({"A": Fraction(1, 2)}, Fraction(-1, 100))


@pytest.mark.parametrize("bad", [0.1, True, "2/20", "1/0", "nan"])
def test_new_scientific_arithmetic_requires_reduced_exact_rationals(bad):
    with pytest.raises(ValueError):
        reporting.rational(bad)


def constraint_fixture(n, *, tick_limit=False):
    protocol = {"logical_aliases": {}, "groups": {"F": ["FIXED"]}, "historical_members": {"OPP": {}}}
    evidence = {}
    for row in ("A", "FIXED"):
        for position in range(1, n + 1):
            for seat in ("A", "B"):
                evidence[row, "OPP", position, seat] = {
                    "payoff_doubled": 1 if row == "A" else 0,
                    "terminal": "tick_limit" if tick_limit else "last_agent_standing",
                    "pressure": {"A": True, "B": True},
                    "captures": {"A": row == "FIXED", "B": row == "FIXED"},
                    "behavior": {"phase_exposure": [1, 2, 3], "phase_differences": {"1": 0, "2": 0, "3": 0}}}
    return evidence, protocol


@pytest.mark.parametrize("n,severe", [(29, False), (30, True)])
def test_distinct_position_pressure_exposure_threshold(n, severe):
    evidence, protocol = constraint_fixture(n, tick_limit=True)
    result = reporting.evaluate_constraints(evidence, protocol, n=n)
    immunity = result["strata"]["OPP/A"]["immunity"]["focal"]
    assert immunity["exposed_positions"] == n
    assert immunity["severe"] is severe


@pytest.mark.parametrize("percent,severe", [(94, False), (95, True)])
def test_phase_ninety_five_percent_equality_and_full_exposure(percent, severe):
    evidence, protocol = constraint_fixture(100)
    for (row, _, position, _), item in evidence.items():
        if row == "A":
            item["behavior"]["phase_differences"]["1" if position <= percent else "2"] = 1
    result = reporting.evaluate_constraints(evidence, protocol, n=100)
    phase = next(detail for detail in result["strata"]["OPP/A"]["phase_details"] if detail["phase"] == 1)
    assert phase["severe"] is severe


def test_seat_dependence_exact_tenth_equality():
    evidence, protocol = constraint_fixture(5)
    for (row, _, position, seat), item in evidence.items():
        item["payoff_doubled"] = int(position == 1 and ((row == "A" and seat == "A")
                                                      or (row == "FIXED" and seat == "B")))
    result = reporting.evaluate_constraints(evidence, protocol, n=5)
    assert result["strata"]["seat/A"]["gap"] == Fraction(1, 10)
    assert result["strata"]["seat/B"]["gap"] == Fraction(-1, 10)
    assert result["severe_seat_dependence"] is True


def test_stall_half_exposure_and_nonlimit_full_denominator():
    evidence, protocol = constraint_fixture(2)
    for (row, _, position, _), item in evidence.items():
        item["terminal"] = "tick_limit" if position == 1 else "last_agent_standing"
        item["payoff_doubled"] = int(row == "A" and position == 1)
    result = reporting.evaluate_constraints(evidence, protocol, n=2)
    stratum = result["strata"]["OPP/A"]
    assert stratum["tick_limit_fraction"] == Fraction(1, 2)
    assert stratum["nonlimit_contribution_full_denominator"] == {"FIXED": Fraction(0)}
    assert stratum["severe_stall"] is True


def test_constraint_rectangle_missing_denominator_fails():
    evidence, protocol = constraint_fixture(2)
    evidence.pop(("FIXED", "OPP", 2, "B"))
    with pytest.raises(ValueError):
        reporting.evaluate_constraints(evidence, protocol, n=2)


def test_complete_synthetic_final_serialization_independently_reproduced_and_immutable(tmp_path):
    earlier = through_g()
    boundary = fixture("GenerationBoundary", earlier)
    earlier["S"] = fixture("S", earlier, generation_boundary=record_ref(boundary))
    for role in ("W", "U", "C", "D"):
        earlier[role] = fixture(role, earlier)
    finding = reporting.classify_report(integrity=True, realized_positions=2, seat_a_positions=1,
        seat_b_positions=1, statuses=dict.fromkeys(("F", "D", "S", "H"), "SUPPORTED"), gates_valid=True)
    final = fixture("F", earlier, **finding,
        dependencies={role: record_ref(earlier[role]) for role in
            ("P", "I", "Q", "O", "V", "A", "R", "B", "G", "S", "W", "U", "C", "D")},
        counts={"physical_cells": 900856, "started_attempts": 900856, "failed_attempts": 0,
                "realized_revisions": 2, "realized_positions": 2, "seat_positions": {"A": 1, "B": 1}},
        approved_inventory_boundary="independent synthetic serialization fixture only")
    body = final["body"]
    raw_body = json.dumps(body, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode()
    expected_digest = hashlib.sha256(raw_body).hexdigest()
    expected = {"schema": "bytefray.v6.e9.final_registered_result", "version": 2,
                "body": body, "digest": expected_digest,
                "identity": "v6-e9-final-registered-result-v2-" + expected_digest[:12],
                "digest_convention": "SHA256 of UTF-8 canonical body, sorted keys, compact separators, no trailing LF"}
    expected_raw = json.dumps(expected, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode() + b"\n"
    destination = tmp_path / "independent-synthetic-final.json"
    actual_digest = reporting.seal_final(destination, body)
    assert destination.read_bytes() == expected_raw
    assert actual_digest == hashlib.sha256(expected_raw).hexdigest()
    with pytest.raises(FileExistsError):
        reporting.seal_final(destination, body)
    assert destination.read_bytes() == expected_raw


# Row inputs: integrity, realized revisions, realized positions, seat A/B positions,
# F/D/S/H statuses and severe constraints. Expected rows follow the frozen table text.
ROWS = {
    1: (False, 2, 2, 1, 1, dict.fromkeys("FDSH", "SUPPORTED"), ()),
    2: (True, 0, 0, 0, 0, dict.fromkeys("FDSH", "SUPPORTED"), ()),
    3: (True, 1, 1, 1, 0, dict.fromkeys("FDSH", "SUPPORTED"), ()),
    4: (True, 3, 2, 1, 1, {**dict.fromkeys("FDSH", "SUPPORTED"), "D": "REFUTED"}, ()),
    5: (True, 3, 2, 1, 1, {**dict.fromkeys("FDSH", "SUPPORTED"), "S": "UNRESOLVED"}, ()),
    6: (True, 3, 2, 1, 1, dict.fromkeys("FDSH", "SUPPORTED"), ("seat dependence", "stall/aggregate")),
    7: (True, 3, 2, 1, 1, dict.fromkeys("FDSH", "SUPPORTED"), ()),
}


def sealed_body(row, **count_changes):
    integrity, revisions, positions, seat_a, seat_b, statuses, severe = ROWS[row]
    earlier = through_g()
    earlier["S"] = fixture("S", earlier, generation_boundary=record_ref(fixture("GenerationBoundary", earlier)))
    for role in ("W", "U", "C", "D"):
        earlier[role] = fixture(role, earlier)
    finding = reporting.classify_report(integrity=integrity, realized_positions=positions,
        seat_a_positions=seat_a, seat_b_positions=seat_b, realized_revisions=revisions, statuses=statuses,
        severe_constraints=severe, gates_valid=True)
    assert finding["scientific_priority_row"] == row
    counts = {"physical_cells": 900856, "started_attempts": 900856, "failed_attempts": 0,
              "realized_revisions": revisions, "realized_positions": positions,
              "seat_positions": {"A": seat_a, "B": seat_b}, **count_changes}
    return fixture("F", earlier, **finding, counts=counts)["body"]


@pytest.mark.parametrize("row", sorted(ROWS))
def test_sealer_independently_reproduces_every_frozen_row_from_recorded_inputs(tmp_path, row):
    body = sealed_body(row)
    assert reporting.reproduce_row(body) == row
    assert reporting.seal_final(tmp_path / f"row{row}-F.json", body)
    assert body["requirement_C_eligible"] is (row == 7)


@pytest.mark.parametrize("row,change", [
    # Review-03 counterexamples: each stored row disagrees with the recorded inputs.
    (7, {"qualifiers": ["seat dependence"]}),  # a severe constraint makes row 6
    (2, {"counts": {"realized_revisions": 10, "realized_positions": 10, "seat_positions": {"A": 5, "B": 5}}}),
    (3, {"counts": {"realized_positions": 2, "seat_positions": {"A": 1, "B": 1}, "realized_revisions": 3}}),
    (5, {"counts": {"realized_revisions": 0, "realized_positions": 0, "seat_positions": {"A": 0, "B": 0}}}),
    # Further inputs the stored label cannot replace.
    (7, {"counts": {"realized_revisions": 3, "realized_positions": 1, "seat_positions": {"A": 1, "B": 1}}}),
    (6, {"qualifiers": ["Payoff gates pass; registered interaction constraint blocks aggregate attribution"]}),
    (4, {"qualifiers": ["D practical benefit refuted", "an unregistered qualifier"]}),
    (7, {"historical_superiority": "Historical practical superiority unresolved"}),
    (7, {"counts": {"realized_positions": 2, "seat_positions": {"A": 1, "B": 1}}}),  # no realization count
])
def test_sealer_rejects_rows_the_recorded_inputs_do_not_reproduce(tmp_path, row, change):
    body = sealed_body(row)
    if "counts" in change:
        change = {"counts": {**{k: v for k, v in body["counts"].items()
                                if k not in ("realized_revisions", "realized_positions", "seat_positions")},
                             **change["counts"]}}
    with pytest.raises(ValueError):
        reporting.seal_final(tmp_path / "unreproduced-F.json", {**body, **change})
    assert not (tmp_path / "unreproduced-F.json").exists()
