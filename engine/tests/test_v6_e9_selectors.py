"""Q-C3–9/15: contract vectors, causal perturbations and independent oracle."""

import ast
from itertools import product
from pathlib import Path

import pytest

from tools.research.v6.e9 import oracle
from tools.research.v6.e9.selectors import Adaptive, Mode, Receipt, Schedule, Scheduled, schedules


def values(state):
    return (int(state.mode), state.c, state.target, state.request, state.changes, state.last_revision)


def test_qc3_qc4_golden_reversals_deferred_promotion_and_budget():
    selector = Adaptive()
    selector.activate()
    expected_modes = [1, 1, 1, 1, 4, 4, 1, 1, 4, 4, 1, 1, 1]
    events = {1: False, 2: False, 3: True, 4: True, 5: False,
              7: True, 8: True, 9: False, 11: True, 12: True}
    for epoch, expected_mode in enumerate(expected_modes):
        evidence = (Receipt(191, epoch + 1, events[epoch]),) if epoch in events else ()
        d = selector.boundary(epoch, epoch + 1, evidence)
        assert int(d.after.mode) == expected_mode
        if epoch in (5, 9):
            assert d.reason == "cooldown" and d.after.request
        if epoch == 12:
            assert d.reason == "budget" and d.after.changes == 4
    assert selector.state.changes == 4


def test_qc4_activation_target_specificity_missing_priority_and_invalid_boundaries():
    s = Adaptive()
    with pytest.raises(ValueError):
        s.boundary(0, 1, ())
    s.activate()
    s.boundary(0, 1, ())
    s.boundary(1, 2, (Receipt(191, 1, True),))
    d = s.boundary(2, 3, (Receipt(192, 2, True),))
    assert d.after.c == 1 and d.after.target == 192 and d.after.mode == Mode.DENSE
    d = s.boundary(3, 4, (Receipt(192, 3, False), Receipt(192, 4, True)))
    assert d.after.c == 0 and not d.after.request and d.after.changes == 0
    with pytest.raises(ValueError):
        s.boundary(3, 4, ())
    with pytest.raises(ValueError):
        s.boundary(4, 5, (Receipt(192, 6, True),))
    with pytest.raises(ValueError):
        s.activate()


def test_qc5_counterfactual_receipt_and_qc7_stale_unknown():
    def history(present):
        s = Adaptive()
        s.activate()
        for r in range(3):
            s.boundary(r, r + 1, (Receipt(191, r + 1, True),) if r else ())
        assert s.mode == Mode.SPARSE
        s.boundary(3, 4, (Receipt(191, 3, present),))
        return s.boundary(4, 5, ())
    assert history(True).after.mode == Mode.SPARSE
    assert history(False).after.mode == Mode.DENSE
    s = Adaptive()
    s.activate()
    s.boundary(0, 1, ())
    d = s.boundary(1, 10, (Receipt(191, 1, True),))
    assert d.after.c == 0 and d.receipts == ()
    s.boundary(2, 11, (Receipt(191, 10, True),))
    assert s.state.c == 1
    s.boundary(3, 20, ())
    assert s.state.c == 1 and s.mode == Mode.DENSE


def test_qc15_independent_oracle_exhaustive_short_histories():
    # Synthetic selector histories, not matches, seeds or an experiment matrix.
    for sequence in product((None, (191, True), (192, True), (191, False), "stale"), repeat=6):
        s = Adaptive()
        s.activate()
        reference = oracle.Expected()
        for r, item in enumerate(sequence):
            raw = () if item is None else ((max(1, r - 2), 191, True),) if item == "stale" else (
                (r + 1, item[0], item[1]),)
            evidence = tuple(Receipt(address, issue, present) for issue, address, present in raw)
            actual = s.boundary(r, r + 1, evidence)
            reference = oracle.advance(reference, r, r + 1, raw)
            assert values(actual.after) == reference


def test_qc9_canonical_schedule_class_and_independent_oracle():
    plans = schedules()
    identities = {p.identity for p in plans}
    assert len(plans) == len(identities) == 1334
    assert identities == oracle.canonical_identities()
    for plan in plans:
        actual = Scheduled(plan)
        expected = oracle.Expected(mode=int(plan.initial))
        for r, wall in enumerate((0, 1, 5, 8, 20, 35, 65, 129, 257, 513, 900)):
            d = actual.boundary(r, wall + 1, wall)
            moment = r if plan.clock == "opportunity" else wall
            expected = oracle.schedule_command(int(plan.initial), plan.edges, moment, r, expected)
            assert values(d.after) == expected
            assert d.after.changes <= len(plan.edges)


def test_qc9_literal_and_performance_schedules_reproduce_two_way_variation():
    control = Scheduled(Schedule(Mode.DENSE, (4, 6, 8, 10)))
    modes = [control.boundary(r, r + 1, r).after.mode for r in range(13)]
    assert modes == [1, 1, 1, 1, 4, 4, 1, 1, 4, 4, 1, 1, 1]
    assert control.plan.identity in {p.identity for p in schedules()}
    wall = Scheduled(Schedule(Mode.DENSE, (2, 4), "wall"))
    assert wall.boundary(0, 1, 0).after.mode == Mode.DENSE
    assert wall.boundary(1, 10, 9).after.changes == 0  # two skipped boundaries, no ghost switches
    with pytest.raises(ValueError):
        Schedule(Mode.OFF, ())
    with pytest.raises(ValueError):
        Schedule(Mode.DENSE, (2, 3))


def test_qc15_oracle_imports_no_production_policy_or_constants():
    tree = ast.parse(Path(oracle.__file__).read_text(encoding="utf-8"))
    modules = [n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)]
    assert modules == ["__future__", "typing"]
