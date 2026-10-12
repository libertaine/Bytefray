"""V6 E8: the runner's unlock chain and its preconditions, without running any matrix cell (phase I8-5).

docs/research/v6/V6_E8_ACTIVE_SPATIAL_SENSING_PREREGISTRATION.md (PR8) Sec 9, 12
and 13; implementation plan Sec 8. These tests check that every step refuses
to run out of the registered order, and that the two hard preconditions the
research lead set fail closed before any match artifact exists:

* ``family_freeze.verify_engine_source`` before any cell may run;
* ``compatibility.require_compatible`` before every match.

They use temporary run roots, hand-built records and synthetic seed lists. No
test passes ``--confirm-matrix-execution`` for a real field, no seed is
generated, no family match is played, and nothing is written under ``runs/``.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from tools.research.v6.e8 import compatibility, family, family_freeze, matrix, run_e8, seed_protocol
from tools.research.v6.e8.analysis_freeze import PENDING

SYNTHETIC = [(7919 * k * k + 104729 * k + 13) % seed_protocol.SEED_BOUND for k in range(1, 33)]


def _block(commitment: str) -> dict[str, Any]:
    return {"seed_commitment": commitment,
            "execution_matrix_identity": seed_protocol.execution_identity(matrix.STRUCTURAL_DIGEST, commitment),
            "generated_at_utc": "2026-10-01T00:00:00Z", "tool_commit": "0" * 40}


def test_the_structural_plan_counts_and_gates_every_cell_with_the_real_planner() -> None:
    report = run_e8.plan_report()
    assert report["all_consistent"] is True and report["placeholder_seeds"] is True
    assert report["planned_total"] == report["expected_total"] == 16_896
    assert report["structural_matrix_id"] == matrix.matrix_id()
    for row in report["rows"]:
        assert row["planned_cells"] == row["gated_matches"] == row["expected_cells"]
        assert row["rulesets"] == [matrix.condition(row["condition"]).ruleset_id]


# ---------------------------------------------------------------------------
# Confirmations and the seed lock
# ---------------------------------------------------------------------------


def test_execution_needs_explicit_confirmation(tmp_path: Path) -> None:
    with pytest.raises(run_e8.E8ConfigurationError, match="confirm-matrix-execution"):
        run_e8.execute("C8", "F1", run_root=tmp_path)
    for treatment in ("T8", "T8L"):
        with pytest.raises(run_e8.E8ConfigurationError, match="confirm-treatment-execution"):
            run_e8.execute(treatment, "F2", confirm=True, run_root=tmp_path)
    assert not any(tmp_path.iterdir())


def test_seed_generation_needs_explicit_confirmation(tmp_path: Path) -> None:
    private = tmp_path / "seeds.private.txt"
    with pytest.raises(run_e8.E8ConfigurationError, match="confirm-seed-generation"):
        run_e8.generate_seeds(confirm=False, run_root=tmp_path, seeds_path=private)
    assert not private.exists() and not any(tmp_path.iterdir())


def test_no_cell_runs_without_a_committed_matching_seed_list(tmp_path: Path) -> None:
    private = tmp_path / "seeds.private.txt"
    with pytest.raises(run_e8.E8ConfigurationError, match="no seed commitment"):
        run_e8.committed_seeds({"seed_commitment": dict(PENDING)}, private)
    commitment = seed_protocol.commitment(SYNTHETIC)
    with pytest.raises(run_e8.E8ConfigurationError, match="missing or does not match"):
        run_e8.committed_seeds({"seed_commitment": _block(commitment)}, private)
    seed_protocol.write_private(SYNTHETIC, private)
    assert run_e8.committed_seeds({"seed_commitment": _block(commitment)}, private)[0] == SYNTHETIC
    with pytest.raises(run_e8.E8ConfigurationError, match="missing or does not match"):
        run_e8.committed_seeds({"seed_commitment": _block("e" * 64)}, private)
    wrong = {**_block(commitment), "execution_matrix_identity": "v6-e8-exec-v1-000000000000"}
    with pytest.raises(run_e8.E8ConfigurationError, match="does not recompute"):
        run_e8.committed_seeds({"seed_commitment": wrong}, private)


def test_a_treatment_needs_a_pass_qualification_with_committed_strata(tmp_path: Path) -> None:
    with pytest.raises(run_e8.E8ConfigurationError, match="no PASS control qualification"):
        run_e8.require_control_qualification({"control_qualification": dict(PENDING)}, tmp_path)
    path = run_e8.records_root(tmp_path) / run_e8.QUALIFICATION_RECORD
    digest = run_e8.write_json(path, {"status": "PASS", "CQ8-5": {"strata": {}}})
    with pytest.raises(run_e8.E8ConfigurationError, match="strata"):
        run_e8.require_control_qualification({"control_qualification": {"status": "PASS", "record_sha256": digest}},
                                             tmp_path)
    digest = run_e8.write_json(path, {"status": "PASS", "CQ8-5": {"strata": {"neutral": ["x"], "non_neutral": []}}})
    block = {"status": "PASS", "record_sha256": digest}
    assert run_e8.require_control_qualification({"control_qualification": block}, tmp_path) == block
    path.write_text('{"status": "PASS", "edited": true}\n', encoding="utf-8")
    with pytest.raises(run_e8.E8ConfigurationError, match="differs"):
        run_e8.require_control_qualification({"control_qualification": block}, tmp_path)


def test_control_steps_stop_on_any_treatment_artifact(tmp_path: Path) -> None:
    run_e8.assert_no_treatment_artifacts(tmp_path)
    run_e8.condition_root(tmp_path, "T8L", "F1").mkdir(parents=True)
    with pytest.raises(run_e8.TreatmentExposureError):
        run_e8.assert_no_treatment_artifacts(tmp_path)
    other = tmp_path / "other"
    run_e8.write_json(run_e8.records_root(other) / "treatment_gates_T8.json", {})
    with pytest.raises(run_e8.TreatmentExposureError):
        run_e8.assert_no_treatment_artifacts(other)


def test_any_matrix_cell_is_detected(tmp_path: Path) -> None:
    assert not run_e8.any_matrix_cell(tmp_path)
    run_e8.condition_root(tmp_path, "C8", "F2").mkdir(parents=True)
    assert run_e8.any_matrix_cell(tmp_path)


def test_treatment_gates_refuse_a_control(tmp_path: Path) -> None:
    with pytest.raises(run_e8.E8ConfigurationError, match="not a treatment"):
        run_e8.treatment_gates("C8", run_root=tmp_path)


# ---------------------------------------------------------------------------
# The two hard preconditions
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("condition_id", ["C8", "T8", "C8L", "T8L"])
@pytest.mark.parametrize("field_id", ["F1", "F2"])
def test_every_planned_match_of_the_family_passes_the_pre_match_gate(condition_id: str, field_id: str) -> None:
    gated = run_e8.gate_every_match(field_id, matrix.condition(condition_id).ruleset_id, family.FIXTURE_DIR)
    assert gated == matrix.field(field_id).expected_matches


def test_the_planned_matches_are_every_pair_in_both_orientations() -> None:
    f1 = run_e8.planned_matches("F1")
    assert len(f1) == 110 and len(set(f1)) == 110
    assert {frozenset(pair) for pair in f1} == {frozenset(pair) for pair in matrix.F1.pairs}
    assert len(run_e8.planned_matches("F2")) == 22


def test_an_ungated_package_is_refused_before_anything_is_written(tmp_path: Path) -> None:
    packages = tmp_path / "agents"
    family.prepare_data_root(tmp_path, matrix.F2.agents)
    victim = packages / family.package_id("RUSH8")
    source = (victim / "agent.py").read_text(encoding="utf-8")
    # A planted, unguarded SENSE path: D8-9 now classes the package as ungated.
    planted = "\n\ndef _probe():\n    return AgentAction(ActionKindV2.SENSE, 0)\n"
    (victim / "agent.py").write_text(source + planted, encoding="utf-8")
    assert compatibility.discipline.classify_package(victim) == compatibility.discipline.UNGATED
    before = sorted(p.relative_to(tmp_path) for p in tmp_path.rglob("*"))
    with pytest.raises(compatibility.IncompatiblePairing, match=family.package_id("RUSH8")):
        run_e8.gate_every_match("F2", matrix.condition("C8").ruleset_id, packages)
    assert sorted(p.relative_to(tmp_path) for p in tmp_path.rglob("*")) == before


def test_a_failing_engine_source_check_stops_before_the_pre_match_gate(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    def drifted(_frozen: Any) -> None:
        calls.append("engine")
        raise family_freeze.FreezeError("the engine source differs")

    monkeypatch.setattr(family_freeze, "verify_engine_source", drifted)
    monkeypatch.setattr(run_e8, "gate_every_match", lambda *a, **k: calls.append("gate") or 0)
    monkeypatch.setattr(run_e8, "verify_execution_source", lambda record: calls.append("source"))
    with pytest.raises(family_freeze.FreezeError):
        run_e8.preconditions("C8", "F1", record={})
    assert calls == ["engine"]


def test_the_preconditions_run_in_order_and_gate_every_match(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []
    monkeypatch.setattr(family_freeze, "verify_engine_source", lambda frozen: calls.append("engine"))
    monkeypatch.setattr(run_e8, "verify_execution_source", lambda record: calls.append("source"))
    gated = run_e8.preconditions("T8", "F1", record={})
    assert calls == ["engine", "source"] and gated == 3520


def test_copied_packages_must_equal_the_family_freeze(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    env = tmp_path / "env"
    assert run_e8.copy_packages(env, "F2", matrix.condition("T8").ruleset_id) == 704
    real = family.prepare_data_root

    def tampered(root: Path, package_ids: Any) -> None:
        real(root, package_ids)
        target = root / "agents" / family.package_id("GREED8") / "agent.py"
        target.write_text(target.read_text(encoding="utf-8") + "\n# edited\n", encoding="utf-8")

    monkeypatch.setattr(family, "prepare_data_root", tampered)
    with pytest.raises(run_e8.E8ConfigurationError, match="differs from the family freeze"):
        run_e8.copy_packages(tmp_path / "env2", "F2", matrix.condition("T8").ruleset_id)


# ---------------------------------------------------------------------------
# E8-D's final status, from the records
# ---------------------------------------------------------------------------


def _records(root: Path, *, d8_10: str = "PASS", gate: str = "PASS", d8_6: str = "PASS",
             control: str = "PASS") -> None:
    records = run_e8.records_root(root)
    control_clauses = {name: {"status": control} for name in
                       ("D8-1", "D8-7", "D8-8", "D8-11", "D8-12", "D8-13", "D8-14", "D8-15")}
    run_e8.write_json(records / run_e8.QUALIFICATION_RECORD,
                      {"D8-6": {"status": d8_6}, **{c: control_clauses for c in matrix.CONTROL_CONDITIONS}})
    run_e8.write_json(records / run_e8.D8_10_RECORD, {"status": d8_10})
    for condition_id in matrix.TREATMENT_CONDITIONS:
        run_e8.write_json(records / f"treatment_gates_{condition_id}.json", {
            name: {"status": gate if name == "D8-1" else "PASS"} for name in
            ("D8-1", "D8-2", "D8-3", "D8-4", "D8-5", "D8-8", "D8-11", "D8-12", "D8-13", "D8-14", "D8-15")})


@pytest.mark.parametrize(("d8_10", "gate", "d8_6", "control", "expected"), [
    ("PASS", "PASS", "PASS", "PASS", "PASS"), ("FAIL", "PASS", "PASS", "PASS", "FAIL"),
    ("PASS", "FAIL", "PASS", "PASS", "FAIL"), ("PASS", "PASS", "FAIL", "PASS", "FAIL"),
    ("PASS", "PASS", "PASS", "FAIL", "FAIL"),
])
def test_e8_d_needs_every_clause(tmp_path: Path, d8_10: str, gate: str, d8_6: str, control: str,
                                 expected: str) -> None:
    _records(tmp_path, d8_10=d8_10, gate=gate, d8_6=d8_6, control=control)
    status = run_e8.e8d_status(tmp_path)
    assert status["status"] == expected
    assert list(status["clauses"]) == [f"D8-{n}" for n in range(1, 16)]
    assert status["clauses"]["D8-9"] == "PASS"  # the family passes the static gate


def test_e8_d_needs_the_d8_10_record(tmp_path: Path) -> None:
    _records(tmp_path)
    (run_e8.records_root(tmp_path) / run_e8.D8_10_RECORD).unlink()
    with pytest.raises(run_e8.E8ConfigurationError, match="required record"):
        run_e8.e8d_status(tmp_path)


def test_interpretation_needs_the_analysis_and_the_reveal(tmp_path: Path) -> None:
    with pytest.raises((run_e8.E8ConfigurationError, run_e8.AnalysisFreezeError)):
        run_e8.interpret(run_root=tmp_path, freeze_path=tmp_path / "absent.json")


# ---------------------------------------------------------------------------
# Records and the seed filter
# ---------------------------------------------------------------------------


def test_records_are_written_canonically_and_atomically(tmp_path: Path) -> None:
    digest = run_e8.write_json(tmp_path / "r.json", {"b": 1, "a": [2]})
    data = (tmp_path / "r.json").read_bytes()
    assert data == b'{\n  "a": [\n    2\n  ],\n  "b": 1\n}\n' and digest == hashlib.sha256(data).hexdigest()
    assert not list(tmp_path.glob("*.tmp"))


def test_outputs_pass_the_seed_filter_before_the_reveal(tmp_path: Path) -> None:
    freeze = tmp_path / "analysis_freeze.json"
    private = tmp_path / "seeds.private.txt"
    text = f"artifact seed{SYNTHETIC[5]}"
    assert run_e8.guarded(text, freeze_path=freeze, run_root=tmp_path, seeds_path=private) == text  # no record
    commitment = seed_protocol.write_private(SYNTHETIC, private)
    freeze.write_text(json.dumps({"seed_commitment": _block(commitment)}), encoding="utf-8")
    filtered = run_e8.guarded(text, freeze_path=freeze, run_root=tmp_path, seeds_path=private)
    assert str(SYNTHETIC[5]) not in filtered and seed_protocol.REDACTED in filtered
    private.unlink()
    withheld = run_e8.guarded(text, freeze_path=freeze, run_root=tmp_path, seeds_path=private)
    assert str(SYNTHETIC[5]) not in withheld and withheld.startswith("[withheld")
    run_e8.write_json(run_e8.records_root(tmp_path) / run_e8.D8_10_RECORD, {"status": "PASS"})
    assert run_e8.guarded(text, freeze_path=freeze, run_root=tmp_path, seeds_path=private) == text  # revealed


def test_the_cli_refuses_without_confirmation() -> None:
    assert run_e8.main(["execute", "C8", "F1"]) == 2
    assert run_e8.main(["generate-seeds"]) == 2
