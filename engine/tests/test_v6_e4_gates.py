"""The E4 D9' real-fixture gate and G.4' manipulation gate (design review Sec J, Sec R).

Both run controlled, non-matrix scenarios (seeds 42, 1001, 1002; scripted
entrants) under the mirrored Rulesets, with sensitivity checks under Rulesets
that must fail them. No matrix cell runs here.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from tools.research.v6.e4 import d9_gate, manipulation_gate, matrix


@pytest.fixture(scope="module")
def reduced_d9() -> dict[str, Any]:
    return d9_gate.run_gate(seeds=(42,), adversaries=("omniscient", "anchor"))


def test_the_d9_prime_gate_holds_on_the_real_guards_and_its_sensitivity_checks_fire(reduced_d9: dict[str, Any]) -> None:
    record = reduced_d9
    assert record["status"] == "PASS"
    assert (record["primary_scenarios"], record["primary_guard_completions"], record["primary_failure_count"]) == (8, 0, 0)
    assert record["primary_max_guard_streak"] <= 1
    assert record["primary_min_actions"] == {"first": 5, "second": 5}
    # Whole-tick E2 captures the repair guard; the forward parent puts a guard at zero on
    # its own first-mover tick, which the mirrored parity condition forbids.
    assert record["capture_sensitivity_repair_guard_captured_scenarios"] > 0
    assert record["parity_sensitivity_scenarios_with_own_first_zero"] > 0
    assert all(row["final_chunk_owner_role"] == "first" for row in record["scenarios"]["primary"])
    assert {row["ruleset_id"] for row in record["scenarios"]["primary"]} == {matrix.condition("T-E4").ruleset_id}


@pytest.mark.parametrize(("change", "value"), [
    ("guard_completions", 1), ("guard_max_streak", 2), ("guard_zero_ticks_own_first", 1), ("exclusive_ticks", 1),
    ("zero_action_live_ticks", 1), ("final_chunk_owner_role", "second"), ("checks_ok", False),
    ("min_actions", {"first": 5, "second": 4}),
])
def test_a_violation_fails_the_scenario(reduced_d9: dict[str, Any], change: str, value: Any) -> None:
    row = dict(reduced_d9["scenarios"]["primary"][0])
    assert d9_gate.scenario_ok(row)
    row[change] = value
    assert not d9_gate.scenario_ok(row)


def test_the_gate_refuses_matrix_seeds() -> None:
    with pytest.raises(d9_gate.D9PrimeGateError, match="matrix seeds"):
        d9_gate.run_gate(seeds=(7,))


def test_only_the_full_registered_gate_unlocks(reduced_d9: dict[str, Any], tmp_path: Path) -> None:
    path = tmp_path / "d9.json"
    d9_gate.write_record(path, reduced_d9, freeze_id="f", provenance={})
    with pytest.raises(d9_gate.D9PrimeGateError, match="full registered gate"):
        d9_gate.require_gate(path, freeze_id="f")
    full = {**reduced_d9, "seeds": list(d9_gate.SEEDS), "adversaries": list(d9_gate.ADVERSARIES)}
    d9_gate.write_record(path, full, freeze_id="f", provenance={})
    assert d9_gate.require_gate(path, freeze_id="f")["status"] == "PASS"
    with pytest.raises(d9_gate.D9PrimeGateError, match="freeze_id"):
        d9_gate.require_gate(path, freeze_id="other")
    failed = {**full, "status": "FAIL"}
    path.write_text(json.dumps({**failed, "freeze_id": "f"}), encoding="utf-8")
    with pytest.raises(d9_gate.D9PrimeGateError, match="status"):
        d9_gate.require_gate(path, freeze_id="f")


@pytest.mark.parametrize(("condition_id", "expected"), [("T-E4", "FFLLFFLLLLFFLLFF"), ("T-E4K1", "FFLLFFLLLLFFLLFF"),
                                                        ("C-E4", "FFLLFFLLFFLLFFLL"), ("C-E4K1", "FFLLFFLLFFLLFFLL")])
def test_the_runtime_offer_sequence(condition_id: str, expected: str) -> None:
    sequence = manipulation_gate.offer_sequence(matrix.condition(condition_id).ruleset_id)
    assert {tick: row["roles"] for tick, row in sequence["ticks"].items()} == {t: expected for t in range(1, 5)}
    assert all(row["slots_in_order"] for row in sequence["ticks"].values())


def test_the_full_manipulation_gate() -> None:
    record = manipulation_gate.run_gate()
    assert record["status"] == "PASS"
    for arm in record["arms"]:
        assert all(arm["checks"].values()), arm["checks"]
        assert arm["bounds"][arm["treatment"]]["minimum"] == {"first": 5, "second": 5}
        assert arm["bounds"][arm["parent"]]["minimum"] == {"first": 5, "second": 4}
        assert arm["fixtures"][arm["treatment"]]["status"] == "PASS"
        assert arm["fixtures"][arm["parent"]]["violations"]["g4_prime_violation"] > 0


def test_a_sequence_mismatch_fails_the_gate(monkeypatch: pytest.MonkeyPatch) -> None:
    real = manipulation_gate.offer_sequence

    def shifted(ruleset_id: str, ticks: int = 4) -> dict[str, Any]:
        record = real(ruleset_id, ticks)
        record["ticks"][2]["roles"] = "FFLLFFLLFFLLFFLL"
        return record

    monkeypatch.setattr(manipulation_gate, "offer_sequence", shifted)
    monkeypatch.setattr(manipulation_gate, "jam_bound", lambda rid: {
        "minimum": {"first": 5, "second": 5 if "mirrored" in rid else 4}, "zero_occurs": False})
    monkeypatch.setattr(manipulation_gate, "fixture_checks", lambda rid, work, mirrored: {
        "status": "PASS" if mirrored else "FAIL", "second_mover_min": 5 if mirrored else 4,
        "violations": {} if mirrored else {"g4_prime_violation": 1}})
    record = manipulation_gate.run_gate()
    assert record["status"] == "FAIL"
    assert [arm["checks"]["treatment_sequence"] for arm in record["arms"]] == [False, False]
