"""Independent exact-arithmetic and exhaustive protocol-table qualification."""

import hashlib
from collections import Counter
from dataclasses import asdict
from fractions import Fraction as Q
from itertools import islice, product

import pytest

from tools.research.v6.e9.analysis import (
    Interval,
    Uncertainty,
    contrasts,
    decimal_display,
    difference,
    positions,
    uncertainty,
)
from tools.research.v6.e9.artifacts import payoff
from tools.research.v6.e9.instrument import deduplicate_copies, pair_blocks
from tools.research.v6.e9.interpretation import classify
from tools.research.v6.e9.protocol import (
    PROTOCOL_DIGEST,
    Cell,
    IntegrityError,
    cells,
    load_protocol,
    package_bytes,
)


@pytest.fixture(scope="module")
def protocol():
    return load_protocol()


def test_frozen_rectangle_aliases_self_twins_and_wrapper_bytes(protocol):
    counts = Counter()
    twin_count = 0
    for cell in cells(protocol):
        counts[cell.row] += 1
        packages = cell.packages(protocol)
        assert len(set(packages)) == 2
        twin_count += cell.row == cell.opponent
    assert sum(counts.values()) == 900856
    assert set(counts.values()) == {31064}
    assert twin_count == 28240
    assert protocol["logical_aliases"] == {"OFF": "RUSH8", "DENSE": "REACQ8", "D": "REACQ8"}
    assert len(protocol["schedules"]) == len({(s["clock"], s["initial"], tuple(s["edges"]))
                                            for s in protocol["schedules"]}) == 16
    for row in ("A", "MEDIUM", "SPARSE", *protocol["groups"]["S"]):
        assert set(package_bytes(row, protocol)) == {"agent.py", "agent.yaml"}


@pytest.mark.parametrize("winner,seat,expected", [("A", "A", 2), ("A", "B", 0), ("B", "B", 2),
                                                 ("B", "A", 0), ("tie", "A", 1), ("tie", "B", 1)])
def test_authoritative_payoff_encoding(winner, seat, expected):
    assert payoff(winner, seat) == expected


@pytest.mark.parametrize("winner", [None, "", "draw", "tick_limit", 0])
def test_no_invalid_record_is_imputed_as_tie(winner):
    with pytest.raises(IntegrityError):
        payoff(winner, "A")


def test_independent_hash_stream_and_empirical_order_statistic():
    instrument = "0123456789abcdef" * 4
    key = hashlib.sha256(("bytefray-e9-analysis-bootstrap-v1\n" + PROTOCOL_DIGEST + "\n"
                          + instrument + "\n").encode()).digest()
    n, samples = 3, 97
    stream = []
    for counter in range(2000):
        value = int(hashlib.sha256(key + counter.to_bytes(8, "big")).hexdigest()[:16], 16)
        if value < (2**64 // n) * n:
            stream.append(value % n)
    assert list(islice(positions(PROTOCOL_DIGEST, instrument, n), 30)) == stream[:30]
    rows = {"A": [44, 0, 22], "F1": [0, 44, 22], "F2": [44, 22, 0]}
    result = uncertainty(rows, protocol_digest=PROTOCOL_DIGEST, instrument_digest=instrument,
                         resamples=samples, order_statistic=92, comparator_groups=[("F1", "F2")],
                         derived_contrasts={"gap": ("A", ("F1", "F2"))})
    deviations, extrema = [], []
    for offset in range(0, n * samples, n):
        totals = {p: sum(v[stream[offset + j]] for j in range(n)) for p, v in rows.items()}
        deviations.append(max(abs(value - sum(rows[p])) for p, value in totals.items()))
        extrema.append(Q(totals["A"] - max(totals["F1"], totals["F2"]), 44 * n))
    expected_c = Q(sorted(deviations)[91], 44 * n)
    assert result.bootstrap_envelope == expected_c
    assert result.half_width == max(Q(1, 20), expected_c)
    assert result.comparator_changes > 0  # selection is actually exercised
    assert result.resampled_quantity_ranges["gap"] == (min(extrema), max(extrema))
    assert result == uncertainty(rows, protocol_digest=PROTOCOL_DIGEST, instrument_digest=instrument,
        resamples=samples, order_statistic=92, comparator_groups=[("F1", "F2")],
        derived_contrasts={"gap": ("A", ("F1", "F2"))})


@pytest.mark.parametrize("lo,hi,expected", [(Q(1, 10), Q(2, 10), "SUPPORTED"),
    (Q(0), Q(1, 10), "UNRESOLVED"), (Q(0), Q(1, 10) - Q(1, 10**12), "REFUTED")])
def test_exact_unrounded_classification_boundaries(lo, hi, expected):
    assert Interval(lo, hi).status == expected
    assert decimal_display(Q(1, 10) - Q(1, 10**12)) == "0.100000"


def test_rho_boundary_refutation_and_unresolved_and_width_caveat(protocol):
    means = {row: Q(1, 5) for row in protocol["physical_rows"]}
    means["A"] = means["S01"] = Q(1, 2)
    for width, expected in ((Q(1, 20), True), (Q(51, 1000), False)):
        bands = {p: Interval(m - width, m + width) for p, m in means.items()}
        out = contrasts(Uncertainty(means, bands, width, width, 0, {}), protocol)
        assert ("S01" in out["timing_reproducing"]) is expected
        if expected:
            assert out["gaps"]["S"].status == "UNRESOLVED"
        assert out["timing_qualifier"] is expected
    means["S01"] = Q(51, 100)
    bands = {p: Interval(m - Q(1, 20), m + Q(1, 20)) for p, m in means.items()}
    out = contrasts(Uncertainty(means, bands, Q(1, 20), Q(0), 0, {}), protocol)
    assert out["timing_qualifier"] and out["gaps"]["S"].status == "REFUTED"
    assert difference(Interval(Q(0), Q(1, 20)), [Interval(Q(0), Q(1, 20))]).high <= Q(1, 10)


def test_all_972_ordered_table_combinations_independently():
    priorities = set()
    statuses = ("SUPPORTED", "REFUTED", "UNRESOLVED")
    for valid, realization, fs, ds, ss, severe, hs in product((False, True), range(3), statuses,
                                                          statuses, statuses, (False, True), statuses):
        # Independent transcription of the seven predicates, without calling
        # any production helper or using its labels to determine expectation.
        expected = (1 if not valid else 2 if realization == 0 else 3 if realization == 1
                    else 4 if "REFUTED" in (fs, ds, ss) else 5 if (fs, ds, ss) != ("SUPPORTED",) * 3
                    else 6 if severe else 7)
        output = classify(integrity=valid, realized_revisions=realization, realized_positions=realization,
            seat_positions={"A": int(realization > 0), "B": int(realization == 2)},
            statuses={"F": fs, "D": ds, "S": ss, "H": hs},
            severe_constraints=("pathology",) if severe else ())
        assert output.priority == expected
        assert output.broader_fixed_superiority == (expected == 7 and hs == "SUPPORTED")
        priorities.add(output.priority)
    assert priorities == set(range(1, 8))


def test_pairing_and_alias_weighting_missing_duplicate_and_corrupt(protocol):
    records = [{"cell": asdict(Cell(row, opp, position, seat)),
                "cell_identity": Cell(row, opp, position, seat).identity,
                "payoff_doubled": (position + (seat == "B")) % 3}
               for position in (1, 2) for row in protocol["physical_rows"]
               for opp in protocol["historical_members"] for seat in ("A", "B")]
    scores, indexed = pair_blocks(records, protocol, n=2)
    assert len(indexed) == 1276
    assert scores["A"] == [33, 22]  # 11 opponents, both seats, each exactly once
    for bad in (records[:-1], [*records, records[0]], [*records[:-1], {**records[-1], "payoff_doubled": None}]):
        with pytest.raises(IntegrityError):
            pair_blocks(bad, protocol, n=2)


def test_identical_copies_require_complete_equal_execution_provenance():
    record = {"cell_identity": "synthetic-cell", "payoff_doubled": 2,
              "execution_provenance": {"attempt_ledger_digest": "a" * 64,
                  "artifact_digests": {name: "b" * 64 for name in
                     ("result.json", "replay.jsonl", "trace.jsonl", "diagnostic.json")}}}
    retained, duplicates = deduplicate_copies([record, {**record}])
    assert retained == [record] and duplicates == 1
    for duplicate in ({**record, "payoff_doubled": 1},
        {**record, "execution_provenance": {}},
        {**record, "execution_provenance": {**record["execution_provenance"], "attempt_ledger_digest": "c" * 64}}):
        with pytest.raises(IntegrityError):
            deduplicate_copies([record, duplicate])


def test_integrity_precedes_unusable_diagnostics_and_never_establishes_historical_claim():
    result = classify(integrity=False, realized_revisions=None, realized_positions=None,
        seat_positions={}, statuses={}, severe_constraints=("untrusted",), timing_reproduced=True)
    assert result.priority == 1 and result.historical == "NOT EVALUABLE" and not result.qualifiers


def test_degenerate_sample_cannot_remove_guard_and_endpoint_clipping_is_exact():
    result = uncertainty({"A": [44] * 3, "F": [0] * 3}, protocol_digest=PROTOCOL_DIGEST,
                         instrument_digest="f" * 64, resamples=20, order_statistic=19)
    assert result.bootstrap_envelope == 0 and result.half_width == Q(1, 20)
    assert result.bands["A"] == Interval(Q(19, 20), Q(1))
    assert result.bands["F"] == Interval(Q(0), Q(1, 20))
    assert difference(result.bands["A"], [result.bands["A"]]).high == Q(1, 20)
