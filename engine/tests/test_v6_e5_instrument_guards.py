"""V6 E5 instrument guards: the aggregation rule and the non-matrix gates' pass
conditions, tested without touching the frozen tooling.

* The unit value is the median of *per-seed* BP values; raw ticks are never
  pooled across seeds (the research lead's O-BP requirement), so a long match
  cannot outweigh a short one.
* The P5 inertness gate passes only if every frozen/aware comparison is
  identical *and* its -2 sensitivity case detects a difference.
* The observation-delta gate passes only if every comparison holds *and* its
  -2 shift is rejected in every sensitivity case.
"""

from __future__ import annotations

from fractions import Fraction
from pathlib import Path
from typing import Any

import pytest

from tools.research.v6.e5 import analyze_e5 as a
from tools.research.v6.e5 import nonmatrix_gates as g
from tools.research.v6.e5.cell_metrics import DEFINED


class _Run:
    def __init__(self, rows: dict[str, dict[str, Any]]) -> None:
        self.rows = rows

    def row(self, key: str) -> dict[str, Any]:
        return {"e5": self.rows[key]}


def _cell(owned_second: int, second: int, owned_first: int, first: int) -> dict[str, Any]:
    value = Fraction(owned_second, second) - Fraction(owned_first, first)
    reading = {"status": DEFINED, "exact": f"{value.numerator}/{value.denominator}",
               "base_owned_by_first_mover": {"A": owned_first, "B": owned_second}}
    # Victim A moves first on A-first ticks; the tick counts let a pooled
    # aggregation be computed (and be wrong) rather than fail on a missing key.
    return {"bp": {"A": reading, "B": reading}, "both_alive_ticks_by_first_mover": {"A": first, "B": second}}


def test_the_unit_value_is_the_median_of_per_seed_values_never_pooled_ticks() -> None:
    # Seed 1: a long match with BP 0 (500 + 500 ticks). Seeds 2 and 3: short
    # matches with BP 1 (10 + 10 ticks). Per-seed median = 1; pooling the raw
    # ticks would give (20/520) - 0, i.e. about 0.04.
    rows = {"1": _cell(0, 500, 0, 500), "2": _cell(10, 10, 0, 10), "3": _cell(10, 10, 0, 10)}
    summary = a.bp_summary(_Run(rows), ["1", "2", "3"], "A")  # type: ignore[arg-type]
    assert (summary["median_exact"], summary["band"]) == ("1/1", a.SECOND_STRONG)


def _p5_row(identical: bool) -> dict[str, Any]:
    return {"pairing": "x|y", "seed": 101, "identical": identical,
            "frozen_ticks_sha256": "a", "aware_ticks_sha256": "a" if identical else "b"}


@pytest.mark.parametrize(("main", "sensitivity", "status"), [
    ([True, True], [False, True], "PASS"),
    ([True, False], [False, False], "FAIL"),  # a real difference fails the gate
    ([True, True], [True, True], "FAIL"),  # a gate that cannot see a -2 offset fails
])
def test_the_p5_gate_needs_identity_and_a_detecting_sensitivity_case(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, main: list[bool], sensitivity: list[bool], status: str
) -> None:
    monkeypatch.setattr(g, "prepare_aware_root", lambda dest: (dest, {"copy": "sha"}))
    calls: list[str] = []

    def fake_compare(root: Path, base: Path, pairings: Any, seeds: Any, ticks: int, tag: str) -> list[dict[str, Any]]:
        calls.append(tag)
        return [_p5_row(v) for v in (main if tag == "p5" else sensitivity)]

    monkeypatch.setattr(g, "_compare", fake_compare)
    record = g.run_inertness(tmp_path, seeds=(101,), ticks=5)
    assert calls == ["p5", "p5-minus-2"]
    assert record["status"] == status


def test_the_p5_sensitivity_case_really_moves_the_spawn(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(g, "prepare_aware_root", lambda dest: (dest, {}))
    seen: list[int] = []

    def fake_compare(root: Path, base: Path, pairings: Any, seeds: Any, ticks: int, tag: str) -> list[dict[str, Any]]:
        from battle_engine.ruleset_policy import RulesetPolicy
        policy = RulesetPolicy(ruleset_id="t", initial_anchor_placement="before_core")
        seen.append(policy.resolve_initial_anchor(100, 512))
        return [_p5_row(True)]

    monkeypatch.setattr(g, "_compare", fake_compare)
    g.run_inertness(tmp_path, seeds=(101,), ticks=5)
    assert seen == [99, 98]


@pytest.mark.parametrize(("delta_ok", "shift_two_ok", "status"), [
    (True, False, "PASS"), (False, False, "FAIL"), (True, True, "FAIL"),
])
def test_the_observation_gate_needs_every_delta_and_a_rejected_shift(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, delta_ok: bool, shift_two_ok: bool, status: str
) -> None:
    monkeypatch.setattr(g, "prepare_data_root", lambda dest, names: dest)
    monkeypatch.setattr(g, "first_observations", lambda root, rid, names, seed: {"A": {}, "B": {}})
    monkeypatch.setattr(g, "observation_delta_ok",
                        lambda parent, treatment, shift=1: delta_ok if shift == 1 else shift_two_ok)
    record = g.run_observation(tmp_path, seeds=(101,))
    assert record["status"] == status
