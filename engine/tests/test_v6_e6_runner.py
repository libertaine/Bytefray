"""V6 E6: the runner's unlock chain, without running any matrix cell.

Implementation plan Sec 9; pre-registration Sec 9 and 11. These tests check
that every step refuses to run out of the registered order. They use
temporary run roots and hand-built records. No seed is generated, no
family match is played, and nothing is written under ``runs/``.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from tools.research.v6.e6 import matrix, run_e6, seeds
from tools.research.v6.e6.analysis_freeze import PENDING

TEST_SEEDS = [(7919 * k * k + 104729 * k + 13) % seeds.SEED_BOUND for k in range(1, 33)]


def test_the_structural_plan_counts_every_cell_with_the_real_planner() -> None:
    report = run_e6.plan_report()
    assert report["all_consistent"] is True
    assert report["planned_total"] == report["expected_total"] == 11_520
    assert report["placeholder_seeds"] is True
    assert report["structural_matrix_id"] == matrix.matrix_id()


def test_execution_needs_explicit_confirmation(tmp_path: Path) -> None:
    with pytest.raises(run_e6.E6ConfigurationError, match="confirm-matrix-execution"):
        run_e6.execute("C-E6", "F1", run_root=tmp_path)
    with pytest.raises(run_e6.E6ConfigurationError, match="confirm-treatment-execution"):
        run_e6.execute("T-E6", "F1", confirm=True, run_root=tmp_path)
    with pytest.raises(run_e6.E6ConfigurationError, match="confirm-treatment-execution"):
        run_e6.execute("T-E6L", "F2", confirm=True, run_root=tmp_path)
    assert not any(tmp_path.iterdir())


def test_seed_generation_needs_explicit_confirmation(tmp_path: Path) -> None:
    private = tmp_path / "seeds.private.txt"
    with pytest.raises(run_e6.E6ConfigurationError, match="confirm-seed-generation"):
        run_e6.generate_seeds(confirm=False, run_root=tmp_path, seeds_path=private)
    assert not private.exists()


def _block(commitment: str) -> dict[str, Any]:
    return {"seed_commitment": commitment, "execution_matrix_identity": matrix.execution_identity(commitment),
            "generated_at_utc": "2026-09-25T00:00:00Z", "tool_commit": "0" * 40}


def test_no_cell_runs_without_a_committed_matching_seed_list(tmp_path: Path) -> None:
    private = tmp_path / "seeds.private.txt"
    with pytest.raises(run_e6.E6ConfigurationError, match="no seed commitment"):
        run_e6.committed_seeds({"seed_commitment": dict(PENDING)}, private)
    commitment = seeds.commitment(TEST_SEEDS)
    with pytest.raises(run_e6.E6ConfigurationError, match="missing or does not match"):
        run_e6.committed_seeds({"seed_commitment": _block(commitment)}, private)
    seeds.write_private(TEST_SEEDS, private)
    assert run_e6.committed_seeds({"seed_commitment": _block(commitment)}, private)[0] == TEST_SEEDS
    with pytest.raises(run_e6.E6ConfigurationError, match="missing or does not match"):
        run_e6.committed_seeds({"seed_commitment": _block("e" * 64)}, private)
    wrong_identity = {**_block(commitment), "execution_matrix_identity": "v6-e6-exec-v1-000000000000"}
    with pytest.raises(run_e6.E6ConfigurationError, match="does not recompute"):
        run_e6.committed_seeds({"seed_commitment": wrong_identity}, private)


def test_a_treatment_needs_a_pass_qualification_named_by_the_freeze_record(tmp_path: Path) -> None:
    with pytest.raises(run_e6.E6ConfigurationError, match="Checkpoint B"):
        run_e6.require_control_qualification({"control_qualification": dict(PENDING)}, tmp_path)
    with pytest.raises(run_e6.E6ConfigurationError, match="Checkpoint B"):
        run_e6.require_control_qualification({"control_qualification": {"status": "FAIL"}}, tmp_path)
    path = run_e6.records_root(tmp_path) / run_e6.QUALIFICATION_RECORD
    digest = run_e6._write_json(path, {"status": "PASS"})
    block = {"status": "PASS", "record_sha256": digest}
    assert run_e6.require_control_qualification({"control_qualification": block}, tmp_path) == block
    path.write_text('{"status": "PASS", "edited": true}\n', encoding="utf-8")
    with pytest.raises(run_e6.E6ConfigurationError, match="differs"):
        run_e6.require_control_qualification({"control_qualification": block}, tmp_path)


def test_control_steps_stop_on_any_treatment_artifact(tmp_path: Path) -> None:
    run_e6.assert_no_treatment_artifacts(tmp_path)
    (run_e6.condition_root(tmp_path, "T-E6L", "F1")).mkdir(parents=True)
    with pytest.raises(run_e6.TreatmentExposureError):
        run_e6.assert_no_treatment_artifacts(tmp_path)
    other = tmp_path / "other"
    run_e6._write_json(run_e6.records_root(other) / "treatment_gates_T-E6.json", {})
    with pytest.raises(run_e6.TreatmentExposureError):
        run_e6.assert_no_treatment_artifacts(other)


def test_any_matrix_cell_is_detected(tmp_path: Path) -> None:
    assert not run_e6.any_matrix_cell(tmp_path)
    run_e6.condition_root(tmp_path, "C-E6", "F2").mkdir(parents=True)
    assert run_e6.any_matrix_cell(tmp_path)


def test_treatment_gates_refuse_a_control(tmp_path: Path) -> None:
    with pytest.raises(run_e6.E6ConfigurationError, match="not a treatment"):
        run_e6.treatment_gates("C-E6", run_root=tmp_path)


def _records(root: Path, *, d6: str = "PASS", gate: str = "PASS", d3: str = "PASS") -> None:
    records = run_e6.records_root(root)
    run_e6._write_json(records / run_e6.QUALIFICATION_RECORD, {"D-3": {"status": d3}})
    run_e6._write_json(records / run_e6.D6_RECORD, {"status": d6})
    for condition_id in matrix.TREATMENT_CONDITIONS:
        run_e6._write_json(records / f"treatment_gates_{condition_id}.json", {
            "D-1:F1": {"status": gate}, "D-1:F2": {"status": "PASS"}, "D-2": {"status": "PASS"},
            "D-4": {"status": "PASS"}, "D-7": {"status": "PASS"}})


@pytest.mark.parametrize(("d6", "gate", "d3", "expected"), [
    ("PASS", "PASS", "PASS", "PASS"), ("FAIL", "PASS", "PASS", "FAIL"), ("PASS", "FAIL", "PASS", "FAIL"),
    ("PASS", "PASS", "FAIL", "FAIL"),
])
def test_e6d_final_status_needs_every_clause(tmp_path: Path, d6: str, gate: str, d3: str, expected: str) -> None:
    _records(tmp_path, d6=d6, gate=gate, d3=d3)
    status = run_e6.e6d_status(tmp_path)
    assert status["status"] == expected
    assert set(status["clauses"]) == {f"D-{n}" for n in range(1, 8)}
    assert status["clauses"]["D-5"] is True  # the family passes the static gate


def test_e6d_needs_the_d6_record(tmp_path: Path) -> None:
    _records(tmp_path)
    (run_e6.records_root(tmp_path) / run_e6.D6_RECORD).unlink()
    with pytest.raises(run_e6.E6ConfigurationError, match="required record"):
        run_e6.e6d_status(tmp_path)


def test_records_are_written_canonically(tmp_path: Path) -> None:
    digest = run_e6._write_json(tmp_path / "r.json", {"b": 1, "a": [2]})
    data = (tmp_path / "r.json").read_bytes()
    assert data == b'{\n  "a": [\n    2\n  ],\n  "b": 1\n}\n' and digest == hashlib.sha256(data).hexdigest()
    assert json.loads(data) == {"a": [2], "b": 1}
