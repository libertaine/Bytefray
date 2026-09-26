"""V6 Phase 5: Regression test suite for evaluation alignment reporting.

Guarantees that the following five surfaces agree for every registered evaluation-capable ruleset:
1. Resolved evaluation methodology (`request.resolved_arena_alignment_mode`)
2. Normal CLI result output (`_print_evaluation_summary`)
3. Dry-run output (`--dry-run` / `_print_matrix`)
4. Dry-run JSON output (`--dry-run --json` / `_matrix_to_json`)
5. Persisted artifact metadata (`evaluation.json` / `write_evaluation_state`)
"""

from __future__ import annotations

from pathlib import Path

import pytest
from battle_engine.agent_evaluation import EvaluationRequest
from battle_engine.evaluation_artifact import (
    RevisionPlanEntry,
    read_evaluation,
    write_evaluation_state,
)
from battle_engine.evaluation_cli import _matrix_to_json, _print_matrix, _print_result
from battle_engine.evaluation_contracts import (
    EVALUATION_ARENA_ALIGNMENT_MODE_V4_SEEDED,
    EVALUATION_ARENA_ALIGNMENT_MODE_V6_RESEARCH_SCALE,
    EVALUATION_ARENA_ALIGNMENT_MODE_V6_RESEARCH_SCALE_MOVE,
    EVALUATION_ARENA_ALIGNMENT_MODE_V6_RESEARCH_SCALE_MOVE_PROPORTIONAL,
    EvaluationResult,
    effective_conditions_for,
)
from battle_engine.evaluation_planning import build_matrix
from battle_engine.ruleset_policy import (
    BYTEFRAY_RULESET_V4_ID,
    BYTEFRAY_RULESET_V6_RESEARCH_SCALE_ID,
    BYTEFRAY_RULESET_V6_RESEARCH_SCALE_MOVE_ID,
    BYTEFRAY_RULESET_V6_RESEARCH_SCALE_MOVE_PROPORTIONAL_ID,
)


@pytest.mark.parametrize(
    ("ruleset_id", "expected_mode"),
    [
        (BYTEFRAY_RULESET_V4_ID, EVALUATION_ARENA_ALIGNMENT_MODE_V4_SEEDED),
        (
            BYTEFRAY_RULESET_V6_RESEARCH_SCALE_ID,
            EVALUATION_ARENA_ALIGNMENT_MODE_V6_RESEARCH_SCALE,
        ),
        (
            BYTEFRAY_RULESET_V6_RESEARCH_SCALE_MOVE_ID,
            EVALUATION_ARENA_ALIGNMENT_MODE_V6_RESEARCH_SCALE_MOVE,
        ),
        (
            BYTEFRAY_RULESET_V6_RESEARCH_SCALE_MOVE_PROPORTIONAL_ID,
            EVALUATION_ARENA_ALIGNMENT_MODE_V6_RESEARCH_SCALE_MOVE_PROPORTIONAL,
        ),
    ],
)
def test_evaluation_alignment_reporting_surfaces_agree(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    ruleset_id: str,
    expected_mode: str,
) -> None:
    request = EvaluationRequest(
        candidate_id="c",
        opponent_ids=["o"],
        seeds=(1,),
        ticks=10,
        ruleset_id=ruleset_id,
        output_dir=tmp_path / "eval_out",
    )

    # 1. Resolved evaluation methodology
    resolved_mode = request.resolved_arena_alignment_mode
    assert resolved_mode == expected_mode

    # Build dummy matrix for UI / JSON formatting
    matrix = build_matrix(
        request,
        "eval-id-123",
        {},
        None,
        request.resolved_rules_compatibility_id,
        resolved_mode,
    )

    # 2. Dry-run JSON output (--dry-run --json)
    json_data = _matrix_to_json(request, matrix, None)
    assert json_data["arena_alignment_mode"] == expected_mode

    # 3. Dry-run text output (--dry-run)
    capsys.readouterr()  # clear buffer
    _print_matrix(request, matrix)
    out_dry_run = capsys.readouterr().out
    assert f"Arena alignment: {expected_mode}" in out_dry_run

    # 4. Normal CLI result output
    mock_result = EvaluationResult(
        evaluation_id="eval-id-123",
        request=request,
        cells=(),
        aggregates=(),
        comparison=(),
        state_path=tmp_path / "dummy_state.json",
    )
    capsys.readouterr()  # clear buffer
    _print_result(mock_result, request)
    out_summary = capsys.readouterr().out
    assert f"Arena alignment: {expected_mode}" in out_summary

    # 5. Persisted artifact metadata (evaluation.json)
    eval_json_path = tmp_path / f"evaluation_{ruleset_id}.json"
    dummy_identity = {
        "agent_id": "dummy",
        "agent_identity_version": 1,
        "local_source_fingerprint": "abc",
        "runtime_environment": "cpython",
        "system_information": "test",
    }
    write_evaluation_state(
        eval_json_path,
        "eval-id-123",
        request,
        matrix,
        matrix,
        planned_identities={"c": dummy_identity, "o": dummy_identity},
        revision_plan={"c": RevisionPlanEntry("rev-c", None), "o": RevisionPlanEntry("rev-o", None)},
        conditions=effective_conditions_for(10, 2),
        created_at="2026-09-22T00:00:00.000000Z",
        lifecycle_state="completed",
        execution_contexts=(),
    )
    persisted_data = read_evaluation(eval_json_path)
    assert persisted_data["arena_alignment_mode"] == expected_mode
