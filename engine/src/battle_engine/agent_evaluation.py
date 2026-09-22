"""``bytefray agents evaluate <candidate-id>`` -- permanent compatibility facade.

The real implementation lives in dedicated modules: CLI parsing, input
resolution, and presentation in ``evaluation_cli``; orchestration in
``evaluation_service``; deterministic planning, cell execution, identity,
and artifact persistence in their own respective modules. This module
re-exports the stable public surface those modules expose -- including
``main``, the exact canonical CLI entry point -- so every existing import of
``battle_engine.agent_evaluation`` keeps working unchanged. See
``docs/specs/agent_evaluation.md`` for the full design rationale.
"""

from __future__ import annotations

from dataclasses import replace

import battle_engine.evaluation_contracts as _evaluation_contracts
from battle_engine.agent_api import (
    LOCAL_SOURCE_FINGERPRINT_VERSION,
    local_source_fingerprint,
)
from battle_engine.evaluation_analysis import (
    aggregate_cells,
    all_subject_aggregates,
    classify,
    compare_candidate_baseline,
)

# V6 Phase 3I: evaluation artifact persistence and resume trust is owned by
# ``evaluation_artifact``; V6 Phase 3J moved the coordinator policy around it
# (whether resume is enabled, when a checkpoint is due, whether execution
# continues, and when finalization happens) to ``evaluation_service``.
# ``read_evaluation`` is a direct re-export (never a wrapper) because it is
# part of this module's permanent ``__all__`` compatibility surface.
from battle_engine.evaluation_artifact import read_evaluation

# V6 Phase 3H: executing one already-planned cell is owned by
# ``evaluation_cell_execution``.  V6 Phase 3J's coordination around it
# (``execute_cell``'s serial and parallel call sites) now lives in
# ``evaluation_service``.  ``current_execution_context`` and ``execute_cell``
# are direct re-exports (never wrappers) because they are part of this
# module's permanent compatibility surface.
from battle_engine.evaluation_cell_execution import (
    current_execution_context,
    execute_cell,  # noqa: F401 -- live facade attribute, no internal caller post-Phase-3J
)

# V6 Phase 3K: CLI parsing, input resolution, and presentation are owned by
# ``evaluation_cli``.  These are direct re-exports, never wrappers, so
# ``agent_evaluation.main is evaluation_cli.main`` (and the same for the
# parsing/rerun helpers below) holds for every caller that still reaches
# them through this permanent facade.
from battle_engine.evaluation_cli import (
    main,
    methodology_lines,
    parse_opponents,
    parse_seed_list,
    parse_seed_range,
    rerun_command,
)
from battle_engine.evaluation_contracts import (
    BASELINE,
    CANDIDATE,
    EVALUATION_ARENA_ALIGNMENT_MODE,
    EVALUATION_ARENA_ALIGNMENT_MODE_V2_GROUP_STANDARD,
    EVALUATION_ARENA_ALIGNMENT_MODE_V2_STANDARD,
    EVALUATION_RULES_COMPATIBILITY_ID,
    IDENTITY_VERSION,
    IDENTITY_VERSION_V2,
    IDENTITY_VERSION_V2_GROUP,
    ORIENTATION_CANDIDATE_FIRST,
    ORIENTATION_MODE_BOTH,
    ORIENTATION_MODE_CANDIDATE_FIRST_ONLY,
    ORIENTATION_OPPONENT_FIRST,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    SCHEMA_VERSION_V2,
    SCHEMA_VERSION_V2_GROUP,
    STANDARD_V2_SEEDS,
    STANDARD_V4_ARENA_SIZE,  # noqa: F401 -- live facade attribute, no internal caller post-Phase-3K
    STANDARD_V4_SEEDS,  # noqa: F401 -- live facade attribute, no internal caller post-Phase-3K
    ComparisonEntry,
    EffectiveConditions,
    EvaluationCell,
    EvaluationConfigurationError,
    EvaluationLayout,
    EvaluationPlacement,
    EvaluationRequest,
    EvaluationResult,
    EvaluationSeatAssignment,
    ExecutionContext,
    SubjectAggregate,
    effective_conditions_for,
    is_ruleset_v2_methodology,
    is_ruleset_v4_methodology,  # noqa: F401 -- live facade attribute, no internal caller post-Phase-3J
    physical_slots_for_orientation,
    resolve_evaluation_ruleset_id,
    resolved_arena_alignment_mode,
    resolved_identity_version,
    resolved_schema_version,
    seat_label,
)
from battle_engine.evaluation_identity import (
    agent_identity,
    effective_conditions_payload,  # noqa: F401 -- live facade attribute, no internal caller post-Phase-3J
    source_digest,
)

# V6 Phase 3G: deterministic planning -- placement/layout geometry and the
# ordered matrix compiler -- is owned by ``evaluation_planning``.  These are
# direct re-exports, never wrappers, so ``agent_evaluation.build_matrix is
# evaluation_planning.build_matrix`` holds for every caller that still
# reaches these through this permanent facade.
from battle_engine.evaluation_planning import (
    build_matrix,
    enumerate_seat_assignments,
    resolve_v4_seed_geometry,  # noqa: F401 -- live facade attribute, no internal caller post-Phase-3J
    standard_layouts,
    standard_placements,
)

# V6 Phase 3J: the coordinator itself -- ``EvaluationService`` -- is owned by
# ``evaluation_service``.  This is a direct re-export (never a subclass or a
# wrapper), so ``agent_evaluation.EvaluationService is evaluation_service.
# EvaluationService`` holds for every caller that still reaches it through
# this permanent facade.
from battle_engine.evaluation_service import EvaluationService
from battle_engine.match_service import NativeMatchResult
from battle_engine.results import WINNER_TIE_SENTINEL
from battle_engine.rules import BYTEFRAY_RULESET_ID
from battle_engine.ruleset_policy import BYTEFRAY_RULESET_V2_ID

IDENTITY_VERSION_V4 = _evaluation_contracts.IDENTITY_VERSION_V4
EVALUATION_ARENA_ALIGNMENT_MODE_V4_SEEDED = (
    _evaluation_contracts.EVALUATION_ARENA_ALIGNMENT_MODE_V4_SEEDED
)
LIFECYCLE_STATE_ABORTED = _evaluation_contracts.LIFECYCLE_STATE_ABORTED
LIFECYCLE_STATE_FINISHED_WITH_FAILURES = (
    _evaluation_contracts.LIFECYCLE_STATE_FINISHED_WITH_FAILURES
)
LIFECYCLE_STATE_RUNNING = _evaluation_contracts.LIFECYCLE_STATE_RUNNING
# V6 Phase 3I: the artifact layer owns every remaining *use* of these two
# constants, but both stay facade attributes -- live consumers still import
# them from here, so they are declared the same way as the other
# non-``__all__`` compatibility attributes around them rather than silently
# disappearing with the code that used to reference them.
LIFECYCLE_STATE_FINISHED = _evaluation_contracts.LIFECYCLE_STATE_FINISHED
SCHEMA_VERSION_V4 = _evaluation_contracts.SCHEMA_VERSION_V4
UNSUCCESSFUL_CELL_STATUSES = _evaluation_contracts.UNSUCCESSFUL_CELL_STATUSES


# ---------------------------------------------------------------------------
# Historical/dead residue -- deliberately retained (Phase 3J/3K); see
# docs/specs/agent_evaluation.md and the Phase 3K report for why this is not
# folded into the CLI/presentation extraction above.
# ---------------------------------------------------------------------------


def _cell_from_match_result_group(cell: EvaluationCell, match_result: NativeMatchResult) -> EvaluationCell:
    """The multi-entrant generalization of
    :func:`battle_engine.evaluation_cell_execution._cell_from_match_result`.

    Only the subject's (candidate's) own outcome/score/territory are
    resolved into the shared summary fields -- `score_opponent`/
    `territory_opponent` stay `None` for a group cell (ill-defined for
    more than one "opponent"); every seat's full result remains fully
    recoverable from this cell's own persisted result.json (Phase 1's
    "cell stores summary, result.json stores everything" pattern,
    unchanged). Per-seat breakdowns beyond the subject's own perspective
    are explicitly deferred to a later phase -- see the design doc's
    "analysis compatibility" section.
    """

    subject_slot = cell.subject_seat
    winner = match_result.winner
    outcome = (
        "tie"
        if winner == WINNER_TIE_SENTINEL
        else "win"
        if winner == subject_slot
        else "loss"
    )
    subject_agent = match_result.agents_by_id.get(subject_slot) if subject_slot else None
    return replace(
        cell,
        status="completed",
        outcome=outcome,
        match_id=match_result.match_id,
        result_id=match_result.result_id,
        ticks_run=match_result.ticks_run,
        score_subject=float(match_result.score.get(subject_slot, 0)) if subject_slot else None,
        territory_subject=(subject_agent.territory_pct_last if subject_agent else None),
        error_code=None,
        error_message=None,
    )


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "BASELINE",
    "BYTEFRAY_RULESET_ID",
    "BYTEFRAY_RULESET_V2_ID",
    "CANDIDATE",
    "EVALUATION_ARENA_ALIGNMENT_MODE",
    "EVALUATION_ARENA_ALIGNMENT_MODE_V2_GROUP_STANDARD",
    "EVALUATION_ARENA_ALIGNMENT_MODE_V2_STANDARD",
    "EVALUATION_RULES_COMPATIBILITY_ID",
    "IDENTITY_VERSION",
    "IDENTITY_VERSION_V2",
    "IDENTITY_VERSION_V2_GROUP",
    "LOCAL_SOURCE_FINGERPRINT_VERSION",
    "ORIENTATION_CANDIDATE_FIRST",
    "ORIENTATION_MODE_BOTH",
    "ORIENTATION_MODE_CANDIDATE_FIRST_ONLY",
    "ORIENTATION_OPPONENT_FIRST",
    "SCHEMA_NAME",
    "SCHEMA_VERSION",
    "SCHEMA_VERSION_V2",
    "SCHEMA_VERSION_V2_GROUP",
    "STANDARD_V2_SEEDS",
    "ComparisonEntry",
    "EffectiveConditions",
    "EvaluationCell",
    "EvaluationConfigurationError",
    "EvaluationLayout",
    "EvaluationPlacement",
    "EvaluationRequest",
    "EvaluationResult",
    "EvaluationSeatAssignment",
    "EvaluationService",
    "ExecutionContext",
    "SubjectAggregate",
    "agent_identity",
    "aggregate_cells",
    "all_subject_aggregates",
    "build_matrix",
    "classify",
    "compare_candidate_baseline",
    "current_execution_context",
    "effective_conditions_for",
    "enumerate_seat_assignments",
    "is_ruleset_v2_methodology",
    "local_source_fingerprint",
    "main",
    "methodology_lines",
    "parse_opponents",
    "parse_seed_list",
    "parse_seed_range",
    "physical_slots_for_orientation",
    "read_evaluation",
    "rerun_command",
    "resolve_evaluation_ruleset_id",
    "resolved_arena_alignment_mode",
    "resolved_identity_version",
    "resolved_schema_version",
    "seat_label",
    "source_digest",
    "standard_layouts",
    "standard_placements",
]
