"""The D9 real-fixture gate (design review Sec G.5, Sec J D9, Sec N hard stop 9).

The tracked ``e2_repair_guard`` and ``e2_disrupt_guard`` run under the
primary treatment Ruleset against scripted, non-matrix adversaries at a seed
outside the matrix. The full registered gate (every adversary, three seeds,
1000 ticks) is run by ``run_e3 d9``; this module runs a reduced gate.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from tools.research.v6.e3 import d9_gate


@pytest.fixture(scope="module")
def reduced() -> dict[str, Any]:
    return d9_gate.run_gate(seeds=(42,), ticks=200, adversaries=("omniscient", "anchor", "alternating", "random-0"))


def test_real_guards_are_never_captured_under_the_primary_treatment(reduced: dict[str, Any]) -> None:
    assert reduced["status"] == "PASS" and reduced["primary_failure_count"] == 0
    assert reduced["primary_scenarios"] == 2 * 2 * 4
    assert (reduced["primary_guard_completions"], reduced["primary_max_guard_streak"]) == (0, 1)
    # The G.4 bound is tight: the adversaries hold both guards to exactly 5 / 4.
    assert reduced["primary_min_guard_actions"] == {"first": 5, "second": 4}
    for row in reduced["scenarios"]["primary"]:
        assert d9_gate.scenario_ok(row), row
        assert row["guard_zero_ticks_on_opponent_first"] == 0 and row["ticks"] == 200
    # Non-vacuous: the omniscient adversary drives the disrupt guard to zero
    # core on some of its own first-mover ticks -- never twice running.
    omniscient = [r for r in reduced["scenarios"]["primary"]
                  if r["guard"] == "e2_disrupt_guard" and r["adversary"] == "omniscient"]
    assert all(r["guard_zero_core_evaluations"] > 0 and r["guard_max_streak"] == 1 for r in omniscient)


def test_the_whole_tick_parent_lets_the_same_adversaries_capture_the_repair_guard(reduced: dict[str, Any]) -> None:
    captured = {(r["guard_seat"], r["adversary"]) for r in reduced["scenarios"]["sensitivity"]
                if r["guard"] == "e2_repair_guard" and r["guard_completions"] > 0}
    assert {("A", "omniscient"), ("B", "omniscient"), ("A", "alternating"), ("B", "alternating")} <= captured
    assert reduced["sensitivity_repair_guard_captured_scenarios"] == len(captured)


def test_a_violation_fails_the_scenario() -> None:
    clean = {"checks_ok": True, "guard_completions": 0, "guard_max_streak": 1, "guard_alive_at_end": True,
             "g4_violations": 0, "zero_action_live_ticks": 0, "guard_zero_ticks_on_opponent_first": 0}
    assert d9_gate.scenario_ok(clean)
    for change in ({"guard_completions": 1}, {"guard_max_streak": 2}, {"guard_alive_at_end": False},
                   {"g4_violations": 1}, {"zero_action_live_ticks": 1}, {"guard_zero_ticks_on_opponent_first": 1},
                   {"checks_ok": False}):
        assert not d9_gate.scenario_ok({**clean, **change}), change


def test_only_the_full_registered_gate_permits_treatment(reduced: dict[str, Any], tmp_path: Path) -> None:
    path = tmp_path / d9_gate.D9_RECORD_NAME
    d9_gate.write_record(path, reduced, freeze_id="v6-e3-freeze-v1-x", provenance={})
    with pytest.raises(d9_gate.D9GateError, match="full registered gate"):
        d9_gate.require_d9_gate(path, freeze_id="v6-e3-freeze-v1-x")
    full = {**reduced, "seeds": list(d9_gate.SEEDS), "ticks": d9_gate.TICKS, "adversaries": list(d9_gate.ADVERSARIES)}
    d9_gate.write_record(path, full, freeze_id="v6-e3-freeze-v1-x", provenance={})
    assert d9_gate.require_d9_gate(path, freeze_id="v6-e3-freeze-v1-x")["status"] == "PASS"
    with pytest.raises(d9_gate.D9GateError, match="freeze_id"):
        d9_gate.require_d9_gate(path, freeze_id="other")
    failing = json.loads(path.read_text(encoding="utf-8")) | {"status": "FAIL"}
    path.write_text(json.dumps(failing), encoding="utf-8")
    with pytest.raises(d9_gate.D9GateError, match="status"):
        d9_gate.require_d9_gate(path, freeze_id="v6-e3-freeze-v1-x")


def test_matrix_seeds_are_refused() -> None:
    with pytest.raises(d9_gate.D9GateError, match="matrix seeds"):
        d9_gate.run_gate(seeds=(1,), ticks=10, adversaries=("anchor",))
