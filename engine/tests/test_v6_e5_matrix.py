"""V6 E5 frozen definition, pre-registration and runner guards.

The matrix and the pre-registration are digest-pinned; the runner never
executes implicitly, refuses a treatment without separate confirmation, and
every control-phase command stops if a treatment artifact exists.
"""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path
from typing import Any

import pytest

from tools.research.v6.e4 import matrix as e4_matrix
from tools.research.v6.e5 import matrix, run_e5
from tools.research.v6.e5 import preregistration as p


def test_matrix_definition_is_frozen() -> None:
    assert matrix.matrix_digest() == matrix.E5_MATRIX_DIGEST
    assert matrix.matrix_id() == f"v6-e5-matrix-v1-{matrix.E5_MATRIX_DIGEST[:12]}"
    matrix.verify_frozen_matrix()


def test_fields_and_expected_match_counts() -> None:
    assert matrix.E5_AGENTS == ("e2_sniper", "e2_repair_guard", "e2_disrupt_guard", "e2_min_guard",
                                "e2_guarded_painter", "e2_spread_sniper", "e2_spread_defender")
    assert (len(matrix.F1.pairs), matrix.F1.expected_matches) == (21, 1344)
    assert (len(matrix.F2.pairs), matrix.F2.expected_matches) == (7, 448)
    assert matrix.matches_per_condition() == 1792 and matrix.matches_total() == 7168
    assert matrix.SEEDS == tuple(range(1, 33)) and matrix.MAX_TICKS == 1000 and matrix.ARENA_SIZE == 512


def test_exclusions_are_exactly_the_four_decided_ones() -> None:
    assert set(matrix.EXCLUDED_AGENTS) == {"v4_probe", "e3_jam_sniper", "e2_greedy_painter", "e2_counter"}
    assert set(matrix.E5_AGENTS).isdisjoint(matrix.EXCLUDED_AGENTS)
    assert set(matrix.E5_AGENTS) == set(e4_matrix.E4_AGENTS) - set(matrix.EXCLUDED_AGENTS)


def test_the_field_preserves_e4_pair_orientation() -> None:
    # Every E5 pair is an E4 pair with the same candidate/opponent roles, so the
    # re-run controls align key for key with the preserved C-E4 cells.
    assert set(matrix.F1.pairs) <= set(e4_matrix.F1.pairs)
    assert set(matrix.F2.pairs) <= set(e4_matrix.F2.pairs)


def test_sweep_roles_are_e4_source_roles() -> None:
    assert matrix.SWEEP_ROLE == {
        "e2_sniper": True, "e2_repair_guard": False, "e2_disrupt_guard": False, "e2_min_guard": True,
        "e2_guarded_painter": False, "e2_spread_sniper": True, "e2_spread_defender": True,
    }
    assert matrix.sweeps("e2_min_guard_twin") is True


def test_conditions_and_the_one_field_difference() -> None:
    matrix.verify_ruleset_registry()
    for item in matrix.CONDITIONS:
        if item.historical_condition is not None:
            assert e4_matrix.condition(item.historical_condition).ruleset_id == item.ruleset_id
    assert [c.condition_id for c in matrix.CONDITIONS] == ["C-E5", "T-E5", "C-E5K1", "T-E5K1"]


def test_a_registry_drift_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    original = matrix.resolve_ruleset_policy

    def drifted(ruleset_id: str) -> Any:
        policy = original(ruleset_id)
        if ruleset_id == matrix.condition("T-E5").ruleset_id:
            return dataclasses.replace(policy, capture_hold_ticks=3)
        return policy

    monkeypatch.setattr(matrix, "resolve_ruleset_policy", drifted)
    with pytest.raises(matrix.MatrixDefinitionError):
        matrix.verify_ruleset_registry()


def test_historical_generation_is_the_real_e4_control_commit() -> None:
    assert matrix.HISTORICAL_GENERATION["source_commit"].startswith("e0d39b3")
    assert matrix.PARENT_FREEZE == {"commit": "8f6717d", "path": "engine/tests/test_v6_e5_parent_byte_identity.py",
                                    "matches": 96}


def test_preregistration_is_frozen_and_complete() -> None:
    data = p.load_preregistration()
    assert tuple(item["id"] for item in data["hypotheses"]) == p.REQUIRED_HYPOTHESES
    decisions = {item["id"]: item["decision"] for item in data["decisions"]}
    assert decisions["O-4"].startswith("MODIFIED: at least 6")
    assert p.MIN_SWEEP_BACKED_UNITS == 6


def test_a_changed_preregistration_does_not_load(tmp_path: Path) -> None:
    copy = tmp_path / "preregistration.json"
    data = json.loads(p.PREREGISTRATION_PATH.read_text(encoding="utf-8"))
    data["hypotheses"][1]["criterion"]["supported_min"] = "3/5"
    copy.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    with pytest.raises(p.PreregistrationError, match="digest"):
        p.load_preregistration(copy)


def test_execute_needs_confirmation_and_a_treatment_needs_separate_confirmation(tmp_path: Path) -> None:
    with pytest.raises(run_e5.E5ConfigurationError, match="Refusing to execute"):
        run_e5.execute("C-E5", "F1", run_root=tmp_path)
    for treatment in matrix.TREATMENT_CONDITIONS:
        with pytest.raises(run_e5.E5ConfigurationError, match="separate authorization"):
            run_e5.execute(treatment, "F1", run_root=tmp_path, confirm=True)


def test_control_phase_commands_stop_on_any_treatment_artifact(tmp_path: Path) -> None:
    run_e5.assert_no_treatment_artifacts(tmp_path)
    (tmp_path / matrix.matrix_id() / "T-E5" / "F2").mkdir(parents=True)
    with pytest.raises(run_e5.TreatmentExposureError):
        run_e5.assert_no_treatment_artifacts(tmp_path)


def test_treatment_telemetry_is_a_treatment_artifact_too(tmp_path: Path) -> None:
    (tmp_path / matrix.matrix_id() / "freezes" / "x" / "telemetry" / "T-E5K1").mkdir(parents=True)
    assert run_e5.treatment_artifacts(tmp_path)


def test_any_request_override_fails_closed(tmp_path: Path) -> None:
    class Request:
        candidate_id = "c"
        ruleset_id = matrix.condition("C-E5").ruleset_id
        arena_size = 512
        ticks = 1000
        seeds = matrix.SEEDS
        both_orientations = True

    request = Request()
    for name in matrix.FORBIDDEN_REQUEST_OVERRIDES:
        setattr(request, name, None)
    run_e5.check_requests([request], "C-E5", "F1")  # type: ignore[list-item]
    for name in matrix.FORBIDDEN_REQUEST_OVERRIDES:
        setattr(request, name, 1)
        with pytest.raises(run_e5.E5ConfigurationError, match="forbidden override"):
            run_e5.check_requests([request], "C-E5", "F1")  # type: ignore[list-item]
        setattr(request, name, None)


def test_dry_run_counts_one_field_with_the_real_planner_and_runs_nothing() -> None:
    row = run_e5.dry_run_plan("T-E5", "F2")
    assert (row["planned_cells"], row["expected_cells"], row["consistent"]) == (448, 448, True)
    assert row["rulesets"] == [matrix.condition("T-E5").ruleset_id]
