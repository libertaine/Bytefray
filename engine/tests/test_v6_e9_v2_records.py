"""Implementer synthetic checks; independent reproduction is recorded separately."""
from __future__ import annotations

import copy
from fractions import Fraction

import pytest

from engine.tests._e9_v2_synthetic_records import through_g
from tools.research.v6.e9.v2 import records, reporting
from tools.research.v6.e9.v2.instrument import read_v1_evidence


def test_full_through_g_fixture_serialization_and_exact_resolver():
    rs = through_g()
    resolver = {r["digest"]: r for r in rs.values()}
    for record in rs.values():
        assert records.validate_record(record, resolver) is record


def test_v1_remains_readable_but_never_v2_authority():
    historical = read_v1_evidence(records.BASE / "protocol_freeze.json")
    assert historical["version"] == 1
    with pytest.raises(records.IntegrityError):
        records.validate_record_ref(records.record_ref(historical))


def test_exclusive_writes_keep_original_bytes(tmp_path):
    path = tmp_path / "synthetic-immutable.json"
    before = records.write_once(path, {"opaque": "fixture"})
    with pytest.raises(FileExistsError):
        records.write_once(path, {"opaque": "changed"})
    assert records.sha256(path.read_bytes()) == before


@pytest.mark.parametrize("fault", ["bool_bytes", "bad_digest", "unknown_body", "role_map", "nonfinite"])
def test_invalid_new_record_evidence_is_rejected(fault):
    r = copy.deepcopy(through_g()["A"])
    if fault == "bool_bytes":
        r["body"]["K"]["bytes"] = True
    elif fault == "bad_digest":
        r["digest"] = "A" * 64
    elif fault == "unknown_body":
        r["body"]["optional_authority"] = "YES"
    elif fault == "role_map":
        r["body"]["dependencies"]["P"] = r["body"]["K"]
    else:
        r["body"]["approved_scope"] = float("nan")
    with pytest.raises((records.IntegrityError, ValueError)):
        records.validate_record(r)


@pytest.mark.parametrize("low,high,expected", [
    ("1/10", "1/5", "SUPPORTED"), ("0/1", "1/10", "UNRESOLVED"),
    ("0/1", "99/1000", "REFUTED"),
])
def test_exact_support_and_refutation_equalities(low, high, expected):
    assert reporting.contrast_status(Fraction(low), Fraction(high)) == expected


def test_clipped_guard_and_actual_timing_bound():
    bands = reporting.row_intervals({"A": Fraction(1, 2), "q": Fraction(1, 2)}, Fraction(0))
    assert bands["A"] == (Fraction(9, 20), Fraction(11, 20))
    assert reporting.timing_reproduced(Fraction(1, 10), Fraction(1, 10))
    assert not reporting.timing_reproduced(Fraction(1, 10), Fraction(101, 1000))


def test_scientific_support_does_not_supply_execution_gates():
    result = reporting.classify_report(integrity=True, realized_positions=2,
        seat_a_positions=1, seat_b_positions=1, statuses=dict.fromkeys("FDSH", "SUPPORTED"))
    assert result["scientific_priority_row"] == 7
    assert not result["requirement_C_eligible"]
    assert result["requirement_C"] == "NOT ESTABLISHED"
