"""``bytefray agents evaluate <candidate-id>`` — a deterministic evaluation matrix.

Runs a candidate agent (and, optionally, a baseline agent for comparison)
against an explicit, author-chosen opponent/seed matrix, reusing
``agent_test.test_agent`` as the exact per-cell executor so every
evaluation cell is byte-for-byte reproducible via a plain ``bytefray
agents test`` invocation. Produces an additive, independently versioned
``bytefray.evaluation`` v1 artifact that references (never duplicates) the
canonical ``replay.jsonl``/``result.json`` each cell's real match already
writes. See ``docs/specs/agent_evaluation.md`` for the full design
rationale.

This module is Qt-free and headless: it executes agent code only via
``agent_test.test_agent`` (the same production execution boundary
``agents test`` itself uses), never independently.
"""

from __future__ import annotations

import argparse
import json
import queue
import sys
import threading
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import replace
from pathlib import Path
from typing import Any

import battle_engine.evaluation_contracts as _evaluation_contracts
import battle_engine.evaluation_identity as _evaluation_identity
from battle_engine.agent_api import (
    LOCAL_SOURCE_FINGERPRINT_VERSION,
    local_source_fingerprint,
)
from battle_engine.agent_test import DEFAULT_TICKS
from battle_engine.agent_worker import WorkerCallStatus
from battle_engine.agents import AgentSpec
from battle_engine.config import Config
from battle_engine.evaluation_analysis import (
    aggregate_cells,
    all_subject_aggregates,
    classify,
    compare_candidate_baseline,
)

# V6 Phase 3I: evaluation artifact persistence and resume trust --
# checkpoint construction, atomic writing, persisted-cell reconstruction and
# re-verification, expected-match reconstruction, and revision/provenance
# restoration -- is owned by ``evaluation_artifact``.  This module keeps only
# the coordinator policy around it: whether resume is enabled, when a
# checkpoint is due, whether execution continues, and when finalization
# happens.  ``read_evaluation`` is a direct re-export (never a wrapper)
# because it is part of this module's permanent ``__all__`` compatibility
# surface.
from battle_engine.evaluation_artifact import (
    RevisionPlanEntry,
    checkpoint_cells,
    load_evaluation_state,
    read_evaluation,
    resolve_cell_from_state,
    resolve_revision_results,
    write_evaluation_state,
)
from battle_engine.evaluation_artifact import (
    utc_now_iso as _utc_now_iso,
)

# V6 Phase 3H: executing one already-planned cell is owned by
# ``evaluation_cell_execution``.  The serial dispatch path below and
# ``evaluation_worker``'s subprocess path call the *same* ``execute_cell``;
# this module keeps only the coordination around it.  ``current_execution_
# context`` is re-exported (never wrapped) because it is part of this
# module's permanent ``__all__`` compatibility surface.
from battle_engine.evaluation_cell_execution import (
    CellExecutionResult,
    _resolve_python_agent,
    current_execution_context,
    execute_cell,
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
    STANDARD_V4_ARENA_SIZE,
    STANDARD_V4_SEEDS,
    TERMINAL_LIFECYCLE_STATES,
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
    _resolved_lifecycle_state,
    effective_conditions_for,
    is_ruleset_v2_methodology,
    is_ruleset_v4_methodology,
    physical_slots_for_orientation,
    resolve_evaluation_ruleset_id,
    resolved_arena_alignment_mode,
    resolved_identity_version,
    resolved_schema_version,
    seat_label,
)
from battle_engine.evaluation_identity import (
    agent_identity,
    effective_conditions_payload,
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
    resolve_v4_seed_geometry,
    standard_layouts,
    standard_placements,
)
from battle_engine.evaluation_presets import (
    ORIENTATION_BOTH as _PRESET_ORIENTATION_BOTH,
)
from battle_engine.evaluation_presets import (
    EvaluationPreset,
    EvaluationPresetError,
    load_preset,
)
from battle_engine.evaluation_worker import (
    EvaluationCellWorkerHandle,
    WorkerFailure,
    _cell_from_wire,
)
from battle_engine.match_service import NativeMatchResult
from battle_engine.paths import get_data_root
from battle_engine.project_info import get_project_info
from battle_engine.python_runtime import CORE_SIZE
from battle_engine.results import WINNER_TIE_SENTINEL
from battle_engine.rules import BYTEFRAY_RULESET_ID
from battle_engine.ruleset_policy import (
    BYTEFRAY_RULESET_V2_ID,
    BYTEFRAY_RULESET_V4_ID,
)

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


def _register_execution_context(
    context: ExecutionContext,
    execution_contexts: list[dict[str, Any]],
    known_context_ids: set[str],
) -> None:
    """Coordinator-owned dedup/append, extracted from the old ``record_context_
    usage`` closure so both the serial and parallel dispatch paths call the
    exact same logic -- never a worker, and never duplicated.
    """

    if context.context_id in known_context_ids:
        return
    execution_contexts.append({**context.to_dict(), "first_used_at": _utc_now_iso()})
    known_context_ids.add(context.context_id)


def rerun_command(
    subject_id: str,
    opponent_id: str,
    seed: int,
    ticks: int,
    orientation: str = ORIENTATION_CANDIDATE_FIRST,
) -> str:
    """The exact ``agents test`` invocation that reproduces one cell (Sec 8/10).

    v0.9 Phase 6 (Phase 5 spec Sec H.1): an ``opponent_first`` cell's real
    physical match ran with roles swapped
    (``test_agent(opponent_id, opponent=subject_id, ...)``) -- the printed
    command mirrors that exactly, so it reproduces the cell byte for byte
    rather than silently reproducing the opposite orientation.
    """

    if orientation == ORIENTATION_OPPONENT_FIRST:
        first_id, second_id = opponent_id, subject_id
    else:
        first_id, second_id = subject_id, opponent_id
    return f"bytefray agents test {first_id} --opponent {second_id} --seed {seed} --ticks {ticks}"


# ---------------------------------------------------------------------------
# Seed/opponent parsing shared by the CLI and Designer (Sec 12/13)
# ---------------------------------------------------------------------------


def parse_opponents(text: str) -> tuple[str, ...]:
    opponents = tuple(chunk.strip() for chunk in text.split(",") if chunk.strip())
    if not opponents:
        raise EvaluationConfigurationError("--opponents requires at least one agent id.")
    return opponents


def parse_seed_list(text: str) -> tuple[int, ...]:
    seeds: list[int] = []
    for chunk in text.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        try:
            seeds.append(int(chunk))
        except ValueError as exc:
            raise EvaluationConfigurationError(f"Invalid seed value {chunk!r}.") from exc
    if not seeds:
        raise EvaluationConfigurationError("--seeds requires at least one seed.")
    return tuple(seeds)


def parse_seed_range(text: str) -> tuple[int, ...]:
    start_text, sep, end_text = text.partition(":")
    if not sep:
        raise EvaluationConfigurationError(
            f"--seed-range must be START:END, got {text!r}."
        )
    try:
        start, end = int(start_text.strip()), int(end_text.strip())
    except ValueError as exc:
        raise EvaluationConfigurationError(
            f"--seed-range values must be integers, got {text!r}."
        ) from exc
    if end < start:
        raise EvaluationConfigurationError(
            f"--seed-range end must be >= start, got {text!r}."
        )
    return tuple(range(start, end + 1))


# ---------------------------------------------------------------------------
# Service
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


def _drift_detail(cell: EvaluationCell) -> dict[str, Any]:
    """The ``abort_detail`` payload shape for a drift-detected cell (unchanged
    from pre-Phase-2 behavior -- see ``EvaluationService.run``)."""

    return {
        "role": cell.subject_role,
        "subject_id": cell.subject_id,
        "opponent_id": cell.opponent_id,
        "schedule_id": cell.schedule_id,
        "code": cell.error_code,
        "detail": cell.error_message,
    }


def _drain_abandoned_cells(
    pending_queue: queue.Queue[EvaluationCell | None],
) -> list[EvaluationCell]:
    """Non-blocking drain of whatever is still sitting in ``pending_queue``.

    Used by the parallel dispatch path (v1.6 Phase 2) both when a drift is
    observed (those cells are simply abandoned -- never dispatched, never
    recorded at all, matching what today's serial ``break`` already does for
    matrix positions it never reaches) and when every worker has died with
    cells still queued (those are recorded as failed, never silently
    dropped -- see ``_run_pending_parallel``). A best-effort race against
    dispatcher threads concurrently popping the same queue is acceptable
    here: whichever side wins a given item only changes which cell happens
    to be "one more in flight" at the moment of the decision, which is
    already an explicitly disclosed, worker-count/timing-dependent behavior
    (Phase 0-1 baseline Sec 8).
    """

    drained: list[EvaluationCell] = []
    while True:
        try:
            item = pending_queue.get_nowait()
        except queue.Empty:
            break
        if item is not None:
            drained.append(item)
    return drained


def _evaluation_dispatcher_loop(
    handle: Any,
    pending_queue: queue.Queue[EvaluationCell | None],
    results_queue: queue.Queue[tuple[str, CellExecutionResult | None, Any]],
    ticks: int,
    data_root: Path | None,
    planned_identities: Mapping[str, dict[str, Any]],
    arena_size: int | None = None,
    instr_per_tick: int | None = None,
    locality_reach: int | None = None,
    kill_weight: float | None = None,
    scheduler_chunk_size: int | None = None,
    scheduler_rotate_start: bool = False,
) -> None:
    """One dispatcher thread's body: owns exactly one worker subprocess handle
    for its entire lifetime, processing cells strictly one at a time against
    it -- mirrors ``agent_worker.AgentWorkerHandle``'s existing single-
    in-flight-call model exactly, so no wire-protocol correlation IDs are
    needed. Blocks indefinitely on ``pending_queue.get()`` between cells
    (never a polling timeout): the coordinator never pushes a shutdown
    sentinel (``None``) until it is certain no more work -- including any
    retry -- will ever be enqueued, so a thread can never legitimately give
    up early, and never blocks forever on work that will never arrive.

    V6 Phase 3H: ``evaluation_worker`` no longer imports this module at all
    (it calls ``evaluation_cell_execution.execute_cell`` directly), so the
    worker-side names this loop needs are now ordinary module-scope imports
    rather than the function-local ones the old cycle forced.
    """

    while True:
        cell = pending_queue.get()
        if cell is None:
            return
        call_result = handle.submit_cell(
            cell,
            ticks=ticks,
            data_root=data_root,
            planned_identities=planned_identities,
            arena_size=arena_size,
            instr_per_tick=instr_per_tick,
            locality_reach=locality_reach,
            kill_weight=kill_weight,
            scheduler_chunk_size=scheduler_chunk_size,
            scheduler_rotate_start=scheduler_rotate_start,
        )

        if call_result.status == WorkerCallStatus.OK:
            payload = call_result.payload or {}
            resolved_cell = _cell_from_wire(payload["cell"])
            context_payload = payload.get("execution_context")
            context = ExecutionContext(**context_payload) if context_payload else None
            results_queue.put(
                (cell.schedule_id, CellExecutionResult(cell=resolved_cell, execution_context=context), None)
            )
        elif call_result.status == WorkerCallStatus.FAILED:
            # A well-formed {"ok": false, ...} -- the worker's own
            # belt-and-suspenders catch-all (evaluation_worker._handle_run_
            # cell), expected to be rare since _execute_cell/test_agent
            # already handle nearly everything internally. The worker
            # process itself is still alive and protocol-intact; only this
            # one cell failed -- this dispatcher thread keeps running.
            diagnostic = (call_result.payload or {}).get("diagnostic") or {}
            failed_cell = replace(
                cell,
                status="failed",
                outcome=None,
                error_code=str(diagnostic.get("code", "evaluation_worker_error")),
                error_message=str(diagnostic.get("message", ""))[:240],
            )
            results_queue.put((cell.schedule_id, CellExecutionResult(cell=failed_cell), None))
        else:
            # EXITED / PROTOCOL_ERROR / TIMEOUT (TIMEOUT is unreachable --
            # submit_cell never passes a protocol timeout): this worker is
            # presumed dead. Report the failure and stop -- no automatic
            # replacement subprocess is spawned (v1.6 Phase 2 Sec 9's
            # smallest-change policy); the coordinator decides whether to
            # retry this specific cell on a different, still-live worker.
            results_queue.put(
                (
                    cell.schedule_id,
                    None,
                    WorkerFailure(schedule_id=cell.schedule_id, status=call_result.status, detail=str(call_result.status)),
                )
            )
            handle.close()
            return


# ---------------------------------------------------------------------------
# Revision capture (docs/specs/agent_revision.md Sec 4/5 -- Phase 3)
# ---------------------------------------------------------------------------


class EvaluationService:
    """Headless orchestrator: schedules and executes an evaluation matrix.

    Sibling to ``TournamentService``, not a wrapper around it -- both sit
    over ``NativeMatchService`` (here, via ``agent_test.test_agent``) but
    schedule fundamentally different experiment shapes (see
    docs/specs/agent_evaluation.md Sec 3/Sec 4).
    """

    def preflight(
        self,
        *,
        candidate_id: str,
        opponent_ids: tuple[str, ...],
        seeds: tuple[int, ...],
        baseline_id: str | None = None,
        ticks: int = DEFAULT_TICKS,
        data_root: Path | None = None,
        both_orientations: bool = True,
        ruleset_id: str | None = None,
        group: bool = False,
        arena_size: int | None = None,
        instr_per_tick: int | None = None,
        locality_reach: int | None = None,
        kill_weight: float | None = None,
    ) -> tuple[dict[str, AgentSpec], str]:
        """Validate a request's agent/seed/tick shape and resolve its evaluation id.

        Independent of ``output_dir`` (unlike :class:`EvaluationRequest`
        itself), so a caller -- the CLI in particular -- can compute a
        default ``--output`` directory from the resolved ``evaluation_id``
        before constructing the full request. Called both by the CLI and
        by :meth:`run` itself, so there is exactly one implementation of
        "resolve and validate the matrix inputs," not one for callers that
        already know their output directory and a second for ones that
        don't.
        """

        request = EvaluationRequest(
            candidate_id=candidate_id,
            opponent_ids=opponent_ids,
            seeds=seeds,
            output_dir=Path("."),
            baseline_id=baseline_id,
            ticks=ticks,
            data_root=data_root,
            both_orientations=both_orientations,
            ruleset_id=ruleset_id,
            group=group,
            arena_size=arena_size,
            instr_per_tick=instr_per_tick,
            locality_reach=locality_reach,
            kill_weight=kill_weight,
        )
        specs = self._validate(request)
        conditions = self._effective_conditions(request)
        identities = {agent_id: agent_identity(spec) for agent_id, spec in specs.items()}
        evaluation_id = self._evaluation_id(request, identities, conditions)
        return specs, evaluation_id

    def run(
        self,
        request: EvaluationRequest,
        *,
        checkpoint_batch_size: int = 16,
        checkpoint_batch_interval: float = 1.0,
    ) -> EvaluationResult:
        """Run (or resume) an evaluation.

        ``checkpoint_batch_size``/``checkpoint_batch_interval`` (v1.6 Phase
        2, docs/V1_6_PHASE2_PARALLEL_EVALUATION.md Sec 8): ``evaluation.json``
        is checkpointed after every ``checkpoint_batch_size`` newly-completed
        cells or every ``checkpoint_batch_interval`` seconds, whichever comes
        first -- applied uniformly regardless of ``request.workers``, since
        the O(n^2) cumulative cost of rewriting the whole, growing ``cells``
        list after literally every single cell (Phase 0-1 baseline Sec 5.4)
        exists independent of dispatch mode. The unconditional checkpoint
        before any cell executes and the unconditional final checkpoint are
        both unaffected -- only the *frequency* of the intermediate
        checkpoints changes, never their completeness (each one is always a
        full, canonically matrix-ordered snapshot) or the final persisted
        content. On an ungraceful crash, at most ``checkpoint_batch_size``
        cells or ``checkpoint_batch_interval`` seconds of already-completed
        work (whichever bound was reached last) is not yet durable; resume
        simply re-executes exactly those cells, the same as it always has
        for any cell absent from a prior checkpoint -- no new durable
        "in-progress" cell state is introduced.
        """

        specs = self._validate(request)
        # Frozen at validate time, deliberately never re-derived from a live
        # AgentSpec.source_path later -- Sec 7's pre-check compares a fresh
        # resolve against *this* snapshot, not against `specs` (whose
        # source_path would just re-read whatever the file currently
        # contains, silently defeating drift detection). `evaluation_id` is
        # derived from this exact same dict (never from a second independent
        # `agent_identity()` call) so the persisted `planned_identities`
        # payload is *structurally* guaranteed to reproduce the recorded
        # `evaluation_id` -- see `_evaluation_id` and `_write_state` below.
        planned_identities = {agent_id: agent_identity(spec) for agent_id, spec in specs.items()}
        conditions = self._effective_conditions(request)
        conditions_fp = _evaluation_identity.effective_conditions_fingerprint(
            effective_conditions_payload(conditions, request.resolved_locality_reach),
        )
        evaluation_id = self._evaluation_id(request, planned_identities, conditions)
        resolved_rules_id = request.resolved_rules_compatibility_id
        resolved_is_v2 = is_ruleset_v2_methodology(resolved_rules_id)
        resolved_is_v4 = is_ruleset_v4_methodology(resolved_rules_id)
        resolved_group = request.group and resolved_is_v2
        state_path = request.output_dir / "evaluation.json"
        prior = (
            self._load_state(
                state_path,
                evaluation_id,
                resolved_schema_version(resolved_is_v2, resolved_group, resolved_is_v4),
            )
            if request.resume
            else {}
        )
        prior_cells = {item["schedule_id"]: item for item in prior.get("cells", ())}
        # Revision capture (docs/specs/agent_revision.md Sec 4): resolved
        # here, after `prior` is loaded (so an already-planned agent's
        # revision ID can be retained rather than recomputed) and strictly
        # before `matrix`/any checkpoint/any cell execution. A detected
        # freeze-time mismatch raises out of this call, aborting `run()`
        # before any of that happens -- no evaluation.json is written or
        # modified for this invocation.
        revision_plan = self._resolve_revision_results(request, specs, planned_identities, prior)
        matrix = build_matrix(
            request,
            evaluation_id,
            specs,
            conditions_fp,
            resolved_rules_id,
            resolved_arena_alignment_mode(resolved_is_v2, resolved_group, resolved_is_v4),
        )

        created_at = prior.get("created_at") or _utc_now_iso()
        execution_contexts: list[dict[str, Any]] = list(prior.get("execution_contexts", ()))
        known_context_ids: set[str] = {
            item["context_id"] for item in execution_contexts if item.get("context_id") is not None
        }

        # First checkpoint: written before any cell executes, so a crash
        # during cell 1 still leaves discoverable lifecycle state (Sec 5).
        # Only valid for a genuinely *new* evaluation (no prior cells) --
        # writing an empty ``cells=()`` checkpoint over an *existing*
        # artifact's already-persisted cells would erase it the instant
        # resume starts, before a single prior cell has even been
        # reconstructed/verified (B2). A resumed artifact's own on-disk
        # state already serves as adequate discoverable state; it is left
        # untouched until this run has something at least as good to
        # replace it with.
        if not prior_cells:
            self._write_state(
                state_path,
                evaluation_id,
                request,
                (),
                matrix,
                planned_identities=planned_identities,
                revision_plan=revision_plan,
                conditions=conditions,
                created_at=created_at,
                lifecycle_state="running",
                execution_contexts=execution_contexts,
            )

        # -- Phase A: resolve everything possible from prior state --------
        #
        # A single forward pass over `matrix`, in order -- zero dependency
        # on dispatch mode, no threads involved (v1.6 Phase 2 Sec 4).
        # Mirrors today's per-cell resume decision exactly. Stops early
        # (matching the old loop's `break`) the instant it resolves a cell
        # whose *persisted* status is already `drift_detected` -- cells at
        # or after that point in matrix order are never eligible for
        # dispatch this run, exactly as the old serial loop never reached
        # them either (M2: the only correct recovery from a drifted
        # evaluation is a fresh one). Any *pending* cell strictly before
        # that point may still independently drift when actually executed
        # in Phase B below -- since it is, by construction, earlier in
        # matrix order, that drift (if any) is what actually determines the
        # abort point; see the min-matrix_ordinal selection after Phase B.
        completed_by_schedule_id: dict[str, EvaluationCell] = {}
        pending: list[EvaluationCell] = []
        drifted_cells: list[EvaluationCell] = []
        for cell in matrix:
            previous = prior_cells.get(cell.schedule_id)
            resolved: EvaluationCell | None = None
            if previous is not None:
                resolved = self._resolve_from_state(cell, previous, specs, request)
                if (
                    resolved is not None
                    # M2: `drift_detected` is deliberately excluded here --
                    # it signals the *frozen plan itself* no longer
                    # matches the agent(s) as they exist on disk. Retrying
                    # inside this same artifact would silently execute a
                    # new revision under the old plan's evaluation_id; the
                    # only correct recovery is a fresh evaluation (a new
                    # plan/output directory), never `--retry-failed` on
                    # this one -- regardless of whether the source has
                    # since been restored to its original content.
                    and resolved.status in ("failed", "corrupted")
                    and request.retry_failures
                ):
                    resolved = None
            if resolved is not None:
                completed_by_schedule_id[cell.schedule_id] = resolved
                if resolved.status == "drift_detected":
                    drifted_cells.append(resolved)
                    break
            else:
                pending.append(cell)

        # -- Phase B: dispatch `pending` (serial or a bounded worker pool) --
        any_newly_executed = False
        batch_count = 0
        last_checkpoint_time = time.monotonic()

        def ingest(result: CellExecutionResult) -> bool:
            """Coordinator-only: record one Phase-B result, register its
            execution context, and checkpoint on the batch policy. Returns
            True iff this result is itself a newly observed drift (the
            caller stops feeding further cells to workers when this fires).
            """

            nonlocal any_newly_executed, batch_count, last_checkpoint_time
            any_newly_executed = True
            completed_by_schedule_id[result.cell.schedule_id] = result.cell
            if result.execution_context is not None:
                _register_execution_context(result.execution_context, execution_contexts, known_context_ids)
            is_drift = result.cell.status == "drift_detected"
            if is_drift:
                drifted_cells.append(result.cell)
            batch_count += 1
            now = time.monotonic()
            if batch_count >= checkpoint_batch_size or (now - last_checkpoint_time) >= checkpoint_batch_interval:
                self._write_state(
                    state_path,
                    evaluation_id,
                    request,
                    checkpoint_cells(completed_by_schedule_id, matrix, prior_cells),
                    matrix,
                    planned_identities=planned_identities,
                    revision_plan=revision_plan,
                    conditions=conditions,
                    created_at=created_at,
                    lifecycle_state="running",
                    execution_contexts=execution_contexts,
                )
                batch_count = 0
                last_checkpoint_time = now
            return is_drift

        if pending:
            if request.workers <= 1:
                for cell in pending:
                    result = execute_cell(
                        cell,
                        request.ticks,
                        request.data_root,
                        planned_identities,
                        arena_size=request.resolved_arena_size,
                        instr_per_tick=request.instr_per_tick,
                        locality_reach=request.resolved_locality_reach,
                        kill_weight=request.kill_weight,
                        scheduler_chunk_size=request.scheduler_chunk_size,
                        scheduler_rotate_start=request.scheduler_rotate_start,
                    )

                    if ingest(result):
                        break
            else:
                self._run_pending_parallel(pending, request, planned_identities, ingest)

        # The authoritative drift (if any) is the one with the smallest
        # `matrix_ordinal` among every drifted cell actually observed this
        # run -- whether resolved instantly from prior state (Phase A) or
        # discovered by real execution (Phase B). Phase A's own early
        # `break` already guarantees `pending` never contains a cell at or
        # after a Phase-A-found drift point, so any Phase-B drift is always
        # earlier in matrix order and naturally wins this selection -- no
        # special-case "which phase wins" logic is needed (v1.6 Phase 2
        # Sec 6/Sec 7; Phase 0-1 baseline Sec 8 option (a)).
        drift = _drift_detail(min(drifted_cells, key=lambda c: c.matrix_ordinal)) if drifted_cells else None

        # Every derived view (aggregates, comparison, the persisted `cells[]`,
        # and the returned `EvaluationResult.cells`) is built from this one
        # canonically matrix-ordered list -- never from `completed_by_
        # schedule_id`'s raw insertion order, which (under parallel dispatch)
        # reflects wall-clock completion order, not matrix order. This keeps
        # every worker count's output identical for anything order-sensitive,
        # and matches invariant #4 (docs/V1_6_PHASE2_PARALLEL_EVALUATION.md).
        final_cells = checkpoint_cells(completed_by_schedule_id, matrix, prior_cells)

        aggregates = self._all_aggregates(request, final_cells)
        comparison = compare_candidate_baseline(final_cells) if request.baseline_id is not None else ()
        # M1: a true no-op resume -- everything reconstructed from prior
        # state, nothing newly executed, and that prior state was already a
        # genuinely finished evaluation -- must preserve the original
        # completion chronology rather than minting a new `finished_at` on
        # every idle resume. A resume that did real new work (or completes
        # for the first time) still gets its own fresh timestamp.
        if drift is not None:
            finished_at = None
        elif (
            not any_newly_executed
            and prior.get("lifecycle_state") in TERMINAL_LIFECYCLE_STATES
            and isinstance(prior.get("finished_at"), str)
        ):
            finished_at = prior["finished_at"]
        else:
            finished_at = _utc_now_iso()
        self._write_state(
            state_path,
            evaluation_id,
            request,
            final_cells,
            matrix,
            aggregates=aggregates,
            comparison=comparison,
            planned_identities=planned_identities,
            revision_plan=revision_plan,
            conditions=conditions,
            created_at=created_at,
            lifecycle_state=_resolved_lifecycle_state(final_cells, drift),
            finished_at=finished_at,
            abort_reason="source_drift" if drift is not None else None,
            abort_detail=drift,
            execution_contexts=execution_contexts,
        )
        return EvaluationResult(
            evaluation_id=evaluation_id,
            request=request,
            cells=tuple(final_cells),
            aggregates=aggregates,
            comparison=comparison,
            state_path=state_path,
        )

    # -- parallel dispatch (v1.6 Phase 2) ----------------------------------

    def _run_pending_parallel(
        self,
        pending: list[EvaluationCell],
        request: EvaluationRequest,
        planned_identities: Mapping[str, dict[str, Any]],
        ingest: Callable[[CellExecutionResult], bool],
    ) -> None:
        """Dispatch ``pending`` across ``min(request.workers, len(pending))``
        long-lived worker subprocesses.

        Only this method (and the dispatcher threads it starts) touch the
        two thread-safe queues; ``ingest`` (and everything it touches --
        ``completed_by_schedule_id``, ``execution_contexts``, checkpoint
        timing) is only ever called from *this* thread (the coordinator),
        never from a dispatcher thread -- dispatcher threads only ever push
        onto ``results``. See docs/V1_6_PHASE2_PARALLEL_EVALUATION.md Sec 4
        for the full race-freedom argument (in particular: why no polling
        timeout is needed anywhere in this method, and why a dead worker can
        never strand a cell forever).
        """

        pending_by_schedule_id = {cell.schedule_id: cell for cell in pending}
        worker_count = min(request.workers, len(pending))

        pending_queue: queue.Queue[EvaluationCell | None] = queue.Queue()
        for cell in pending:
            pending_queue.put(cell)
        results_queue: queue.Queue[tuple[str, CellExecutionResult | None, Any]] = queue.Queue()

        handles = [EvaluationCellWorkerHandle() for _ in range(worker_count)]
        for handle in handles:
            handle.start()
        threads = [
            threading.Thread(
                target=_evaluation_dispatcher_loop,
                args=(
                    handle,
                    pending_queue,
                    results_queue,
                    request.ticks,
                    request.data_root,
                    planned_identities,
                    request.resolved_arena_size,
                    request.instr_per_tick,
                    request.resolved_locality_reach,
                    request.kill_weight,
                    request.scheduler_chunk_size,
                    request.scheduler_rotate_start,
                ),

                daemon=True,
            )
            for handle in handles
        ]
        for thread in threads:
            thread.start()

        outstanding = len(pending)
        retried: set[str] = set()
        live_worker_count = len(threads)
        stop_requested = False

        try:
            while outstanding > 0:
                schedule_id, result, failure = results_queue.get()
                if failure is not None:
                    live_worker_count -= 1
                    if schedule_id not in retried and live_worker_count > 0 and not stop_requested:
                        retried.add(schedule_id)
                        pending_queue.put(pending_by_schedule_id[schedule_id])
                    else:
                        outstanding -= 1
                        error_code = (
                            "evaluation_worker_exited"
                            if schedule_id in retried
                            else "evaluation_worker_unavailable"
                        )
                        failed_cell = replace(
                            pending_by_schedule_id[schedule_id],
                            status="failed",
                            outcome=None,
                            error_code=error_code,
                            error_message=(
                                "the evaluation cell worker process exited while "
                                "executing this cell."
                            ),
                        )
                        ingest(CellExecutionResult(cell=failed_cell))
                    if live_worker_count == 0 and not stop_requested:
                        for stranded in _drain_abandoned_cells(pending_queue):
                            outstanding -= 1
                            stranded_cell = replace(
                                stranded,
                                status="failed",
                                outcome=None,
                                error_code="evaluation_worker_unavailable",
                                error_message="no evaluation worker was available to execute this cell.",
                            )
                            ingest(CellExecutionResult(cell=stranded_cell))
                else:
                    outstanding -= 1
                    assert result is not None
                    if ingest(result) and not stop_requested:
                        stop_requested = True
                        # Cells still sitting in the queue are simply
                        # abandoned -- never dispatched, never recorded at
                        # all (matches what the serial loop's `break`
                        # already does for matrix positions it never
                        # reaches). Already in-flight cells are left alone
                        # and allowed to finish normally.
                        for abandoned in _drain_abandoned_cells(pending_queue):
                            outstanding -= 1
        finally:
            # No more work will ever be enqueued past this point (the loop
            # above only exits once every dispatched cell has produced a
            # result and nothing remains in `pending_queue`) -- safe to
            # shut every surviving thread down now. A thread can only be
            # blocked on `pending_queue.get()` here, never mid-`submit_cell`
            # (that would still be `outstanding`), so a shutdown sentinel
            # always reaches it promptly.
            for _ in threads:
                pending_queue.put(None)
            for thread in threads:
                thread.join(timeout=5.0)
            for handle in handles:
                handle.close()

    # -- validation -----------------------------------------------------

    def _validate(self, request: EvaluationRequest) -> dict[str, AgentSpec]:
        if not request.opponent_ids:
            raise EvaluationConfigurationError("Evaluation requires at least one opponent.")
        if not request.seeds:
            raise EvaluationConfigurationError("Evaluation requires at least one seed.")
        if request.ticks < 1:
            raise EvaluationConfigurationError("Evaluation requires a positive tick limit.")
        if request.workers < 1:
            raise EvaluationConfigurationError("Evaluation requires a positive worker count.")
        # v3 Phase 0D: fail closed rather than letting a nonsensical arena
        # reach match execution. The lower bound is not arbitrary: `standard_
        # placements`/`standard_layouts` derive every start address as a
        # fraction of arena size, and both are documented non-overlapping
        # only while that fraction stays larger than one core (CORE_SIZE,
        # 8). A roster of N entrants uses `arena_size // (2 * N)` as its
        # tightest ("close" layout) gap, so require that gap to exceed
        # CORE_SIZE -- otherwise two entrants would silently start inside
        # one another's core and the experiment would measure placement
        # collision rather than the variable under test.
        if request.arena_size is not None:
            entrant_count = len(request.roster_agent_ids) if request.group else 2
            minimum = 2 * entrant_count * (CORE_SIZE + 1)
            if request.arena_size < minimum:
                raise EvaluationConfigurationError(
                    f"Evaluation --arena-size {request.arena_size} is too small for "
                    f"{entrant_count} entrants; standard placements/layouts would overlap. "
                    f"Require at least {minimum}."
                )
        if request.instr_per_tick is not None and request.instr_per_tick < 1:
            raise EvaluationConfigurationError(
                "Evaluation requires a positive --instr-per-tick action budget."
            )
        # v3 Phase 3: fail closed on a negative kill weight rather than
        # silently scoring with one -- alpha.3 already excluded negative
        # weights as having no meaningful interpretation in this game's
        # design (docs/V2_0_ALPHA3_SCORING_SENSITIVITY.md Sec 8), and this
        # phase does not revisit that exclusion. Zero is allowed: it is one
        # of the phase's own predeclared-adjacent boundary values (see K0).
        if request.kill_weight is not None and request.kill_weight < 0:
            raise EvaluationConfigurationError(
                "Evaluation requires a non-negative --kill-weight."
            )
        if request.baseline_id is not None and request.baseline_id == request.candidate_id:
            raise EvaluationConfigurationError(
                "Candidate and baseline must be different agents."
            )
        # Phase 1H: evaluation is product-facing and must never expose a
        # historical alpha Ruleset identity. This mirrors agent_test's own
        # --ruleset choices exactly. Every entrant is
        # already restricted to Python agents by _resolve_python_agent
        # below regardless of Ruleset, so this never needs to separately
        # duplicate the runtime-kind check Beta1's runtime boundary already
        # performs (RulesetRuntimeUnsupportedError, raised through
        # AgentTestError/test_agent if that boundary is ever reached).
        #
        # V6 Phase 2B.10 Scope B removed bytefray-rules-4-alpha1/-alpha2
        # from this allow-list alongside their executable registration
        # (docs/research/v6/V6_PHASE2B10_SCOPE_B_V4_ALPHA_RETIREMENT.md).
        # V6 Phase 2B.12 removed bytefray-rules-1/-2 the same way, retiring
        # Agent API v1 and VM/blob execution entirely
        # (docs/research/v6/V6_PHASE2B12_SCOPE_C_RUNTIME_RETIREMENT.md):
        # bytefray-rules-4 is the only Ruleset that can create a new
        # evaluation artifact now.
        if request.ruleset_id is not None and request.ruleset_id != BYTEFRAY_RULESET_V4_ID:
            raise EvaluationConfigurationError(
                f"Unsupported evaluation --ruleset {request.ruleset_id!r}; expected "
                f"{BYTEFRAY_RULESET_V4_ID!r}."
            )

        # v4.0.0-rc1 Phase 1 (research report Sec H.1 item 3/Sec 6.2 of the
        # governing task): arena 512 is a ratified *methodology* constant
        # for the stable v4 evaluation path, not a casual per-run knob --
        # the research found it the single largest lever on the resulting
        # leaderboard (Sec G.1b), larger than the placement rule it was
        # introduced to evaluate. A standard v4 evaluation must not be able
        # to silently produce a non-standard-arena artifact that still
        # claims the standard `ruleset_v4_seeded_placements` methodology;
        # an incompatible explicit --arena-size fails closed here instead.
        if (
            request.is_v4_methodology
            and request.arena_size is not None
            and request.arena_size != STANDARD_V4_ARENA_SIZE
        ):
            raise EvaluationConfigurationError(
                f"Evaluation --arena-size {request.arena_size} is incompatible with the "
                f"stable v4 evaluation methodology, which is pinned to "
                f"{STANDARD_V4_ARENA_SIZE} cells (research report Sec H.1 item 3); omit "
                "--arena-size, or select a different --ruleset for a non-standard arena."
            )

        # v3 Phase 2's experimental bounded-locality Ruleset
        # (bytefray-rules-3-alpha1) was retired from executable
        # registration by V6 Phase 2B.9: fail closed rather than silently
        # discarding a reach no Ruleset can honor anymore, so an evaluation
        # that names one never writes artifacts describing conditions it
        # did not run under.
        if request.locality_reach is not None:
            raise EvaluationConfigurationError(
                "Evaluation --locality-reach is no longer supported: "
                "bounded-locality gameplay was retired from execution "
                "(V6 Phase 2B.9)."
            )
        # v2.0.0-beta2 Phase 2: multi-entrant ("group") methodology
        # constraints -- fail closed rather than silently degrading to
        # pairwise or silently ignoring `group`.
        #
        # V6 Phase 2B.12 retired bytefray-rules-2, the only Ruleset identity
        # `is_v2_methodology` ever accepts for a *new* request (the gate at
        # the top of this method already rejects any explicit --ruleset
        # other than bytefray-rules-4, so `request.is_v2_methodology` can
        # never be true here any longer): multi-entrant evaluation's
        # methodology -- balanced placement, standard seeds, capture
        # metrics -- was defined specifically for Ruleset v2 gameplay, and
        # redesigning it for Ruleset v4's placement/scoring model is a
        # gameplay-methodology decision this retirement phase does not make
        # (see docs/research/v6/V6_PHASE2B12_SCOPE_C_RUNTIME_RETIREMENT.md
        # Sec 51's "no Ruleset 4 gameplay changes" boundary). A historical
        # group evaluation artifact (schema 6) remains fully readable --
        # only creating a *new* one is retired.
        if request.group:
            raise EvaluationConfigurationError(
                "Multi-entrant (--group) evaluation is retired: it required Ruleset "
                "bytefray-rules-2, which V6 Phase 2B.12 retired. Existing group "
                "evaluation artifacts remain readable."
            )
        subject_ids = [request.candidate_id]
        if request.baseline_id is not None:
            subject_ids.append(request.baseline_id)
        all_ids = sorted(set(subject_ids) | set(request.opponent_ids))
        root = request.data_root or get_data_root()
        return {agent_id: _resolve_python_agent(root, agent_id) for agent_id in all_ids}

    def _effective_conditions(self, request: EvaluationRequest) -> EffectiveConditions:
        # New evaluation execution is exclusively Agent API v2 / Ruleset 4.
        # Historical adapters read their recorded value directly and never
        # call this new-run conditions builder.
        agent_api_version = get_project_info().agent_api_version
        return effective_conditions_for(
            request.ticks,
            agent_api_version,
            arena_size=request.resolved_arena_size,
            instr_per_tick=request.instr_per_tick,
            kill_weight=request.kill_weight,
        )

    def _evaluation_id(
        self,
        request: EvaluationRequest,
        identities: Mapping[str, dict[str, Any]],
        conditions: EffectiveConditions,
    ) -> str:
        """Derive the evaluation id from an already-frozen identity snapshot.

        Deliberately takes ``identities`` (a plain ``agent_id -> agent_identity()``
        dict), never ``specs``/``AgentSpec`` -- computing identity here via a
        second, independent ``agent_identity()`` call would re-read each
        entrant's source file from disk a second time, which could observe
        different bytes than whatever snapshot the caller persists as
        ``planned_identities`` if a source edit lands in between. Every
        caller must build ``identities`` exactly once and pass that same
        dict to both this method and ``_write_state`` (Sec 7/B1).
        """

        resolved_rules_id = request.resolved_rules_compatibility_id
        resolved_is_v2 = is_ruleset_v2_methodology(resolved_rules_id)
        resolved_is_v4 = is_ruleset_v4_methodology(resolved_rules_id)
        resolved_group = request.group and resolved_is_v2
        identity_version = resolved_identity_version(
            resolved_is_v2, resolved_group, resolved_is_v4
        )
        layouts: list[dict[str, Any]] | None = None
        placements: list[dict[str, Any]] | None = None
        if resolved_group:
            # v2.0.0-beta2 Phase 2: multi-entrant identity. `orientation_
            # mode` is not meaningful here -- seat assignment (per cell,
            # not evaluation-wide) is the generalized scheduler-order axis
            # instead, so it is omitted rather than hashed as a stale
            # value. The actual resolved layout set (not just a mode
            # label) enters the hash directly, mirroring Phase 1F's own
            # "placements" precedent exactly -- two different N-seat
            # layout sets must never collide on evaluation_id.
            layouts = [
                _evaluation_identity.layout_identity_payload(
                    layout.layout_id, layout.seat_starts
                )
                for layout in standard_layouts(
                    len(request.roster_agent_ids), request.resolved_arena_size
                )
            ]
        else:
            # Phase 1F: the actual resolved placement set, not just a mode
            # label -- two different v2 placement sets must never collide
            # on evaluation_id. Omitted entirely for v1 (placements is
            # always `None` there) so a v1 payload's key set is byte-
            # identical to every evaluation_id ever computed before Phase 1.
            if resolved_is_v2:
                placements = [
                    _evaluation_identity.placement_identity_payload(
                        placement.placement_id,
                        placement.subject_start,
                        placement.opponent_start,
                    )
                    for placement in standard_placements(request.resolved_arena_size)
                ]
            elif resolved_is_v4:
                # v4.0.0-rc1 Phase 1 (research report Sec H.1 item 7): the
                # methodology's actual resolved *sample set* -- each seed's
                # resolved seat geometry -- enters the hash directly, the
                # exact same "placements" key the v2 branch above uses, so
                # two evaluations naming different seed sets (or whose
                # identical seed set resolves differently because arena
                # size differs) can never collide on evaluation_id, and two
                # evaluations at different sample counts (say seeds 1-8 vs
                # 1-16) share a prefix rather than colliding wholesale.
                placements = []
                for seed in request.seeds:
                    seat_a, seat_b = resolve_v4_seed_geometry(
                        resolved_rules_id, request.resolved_arena_size, seed
                    )
                    placements.append(
                        _evaluation_identity.seeded_placement_identity_payload(
                            seed, seat_a, seat_b
                        )
                    )
        return _evaluation_identity.build_evaluation_id(
            identity_version=identity_version,
            candidate=identities[request.candidate_id],
            baseline=(
                identities[request.baseline_id] if request.baseline_id is not None else None
            ),
            opponents=[identities[opponent_id] for opponent_id in request.opponent_ids],
            seeds=request.seeds,
            ticks=request.ticks,
            effective_conditions=effective_conditions_payload(
                conditions, request.resolved_locality_reach
            ),
            rules_compatibility_id=resolved_rules_id,
            orientation_mode=request.orientation_mode,
            arena_alignment_mode=resolved_arena_alignment_mode(
                resolved_is_v2, resolved_group, resolved_is_v4
            ),
            group=resolved_group,
            layouts=layouts,
            placements=placements,
        )

    def _resolve_revision_results(
        self,
        request: EvaluationRequest,
        specs: Mapping[str, AgentSpec],
        planned_identities: Mapping[str, dict[str, Any]],
        prior: Mapping[str, Any],
    ) -> dict[str, RevisionPlanEntry]:
        """Coordinator entry point for :func:`evaluation_artifact.resolve_revision_results`.

        ``run`` calls this after ``prior`` is loaded and before ``matrix``/any
        checkpoint/any cell execution -- that *ordering* is the coordinator's
        responsibility; recovering or archiving the revisions themselves is
        the artifact layer's.
        """

        return resolve_revision_results(request, specs, planned_identities, prior)

    # -- resume -----------------------------------------------------------

    def _resolve_from_state(
        self,
        cell: EvaluationCell,
        previous: Mapping[str, Any],
        specs: dict[str, AgentSpec],
        request: EvaluationRequest,
    ) -> EvaluationCell | None:
        """Coordinator entry point for :func:`evaluation_artifact.resolve_cell_from_state`.

        Retained as a method for the same reason as the two persistence
        delegates below: it marks where the coordinator asks the artifact
        layer to reconstruct and re-verify one persisted cell, and existing
        resume-interruption tests inject failures at this exact seam.  The
        trust rules themselves live in the artifact layer, not here.
        """

        return resolve_cell_from_state(cell, previous, specs, request)

    # -- aggregation --------------------------------------------------------

    def _all_aggregates(
        self, request: EvaluationRequest, cells: Sequence[EvaluationCell]
    ) -> tuple[SubjectAggregate, ...]:
        return all_subject_aggregates(request.candidate_id, request.baseline_id, cells)

    # -- persistence --------------------------------------------------------

    def _load_state(self, path: Path, evaluation_id: str, expected_schema_version: int) -> dict[str, Any]:
        """Coordinator entry point for :func:`evaluation_artifact.load_evaluation_state`.

        Retained as a method (rather than inlining the call in ``run``)
        because it is the coordinator's single "may this prior artifact be
        resumed at all?" decision point, and because several checkpoint/
        interruption tests inject failures at exactly this seam.  It holds no
        logic of its own: the compatibility gate lives in the artifact layer.
        """

        return load_evaluation_state(path, evaluation_id, expected_schema_version)

    def _write_state(
        self,
        path: Path,
        evaluation_id: str,
        request: EvaluationRequest,
        cells: Sequence[EvaluationCell],
        matrix: Sequence[EvaluationCell],
        *,
        planned_identities: Mapping[str, dict[str, Any]],
        revision_plan: Mapping[str, RevisionPlanEntry],
        conditions: EffectiveConditions,
        created_at: str,
        lifecycle_state: str,
        execution_contexts: Sequence[Mapping[str, Any]],
        aggregates: Sequence[SubjectAggregate] = (),
        comparison: Sequence[ComparisonEntry] = (),
        finished_at: str | None = None,
        abort_reason: str | None = None,
        abort_detail: Mapping[str, Any] | None = None,
    ) -> None:
        """Coordinator entry point for :func:`evaluation_artifact.write_evaluation_state`.

        Deciding *when* a checkpoint is due (the unconditional first write,
        the batch/interval policy, the final write) is coordinator policy and
        stays in ``run``; what a checkpoint *contains* and how it reaches disk
        atomically is the artifact layer's.  Retained as a method because the
        existing checkpoint-interruption tests deliberately crash the process
        at this seam to assert what is already durable.
        """

        write_evaluation_state(
            path,
            evaluation_id,
            request,
            cells,
            matrix,
            planned_identities=planned_identities,
            revision_plan=revision_plan,
            conditions=conditions,
            created_at=created_at,
            lifecycle_state=lifecycle_state,
            execution_contexts=execution_contexts,
            aggregates=aggregates,
            comparison=comparison,
            finished_at=finished_at,
            abort_reason=abort_reason,
            abort_detail=abort_detail,
        )


def _default_output_dir(root: Path, evaluation_id: str) -> Path:
    return root / "runs" / "evaluations" / evaluation_id


def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return parsed


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bytefray agents evaluate",
        description=(
            "Run a deterministic Python-agent evaluation matrix: a candidate "
            "(and optional baseline) against explicit opponents and seeds, "
            "through the exact 'bytefray agents test' execution boundary. "
            "See docs/specs/agent_evaluation.md."
        ),
    )
    parser.add_argument(
        "candidate_id",
        nargs="?",
        default=None,
        help="candidate agent's discovery id (may instead be set by --preset)",
    )
    parser.add_argument(
        "--preset",
        default=None,
        help=(
            "name of a bytefray.evaluation_preset (see 'bytefray agents "
            "evaluation-presets') supplying default values for any option not "
            "explicitly given below; an explicit option always overrides the "
            "preset. Never affects evaluation_id or any per-cell result -- see "
            "docs/V1_6_PHASE3_EVALUATION_PRESETS.md."
        ),
    )
    parser.add_argument(
        "--baseline", default=None, help="baseline agent's discovery id to compare against"
    )
    parser.add_argument(
        "--ruleset",
        choices=[BYTEFRAY_RULESET_V4_ID],
        default=None,
        help=(
            f"gameplay Ruleset identity. {BYTEFRAY_RULESET_V4_ID} is the only "
            "Ruleset Agent API v2 rosters can evaluate under, and is selected "
            "automatically when this flag is omitted (and no --preset "
            f"supplies one). {BYTEFRAY_RULESET_V4_ID} runs Agent API v2 "
            "process entrants through the same production match service "
            "under the stable v4 seeded-placement methodology: arena pinned "
            f"to {STANDARD_V4_ARENA_SIZE}, {len(STANDARD_V4_SEEDS)} "
            "deterministic placement samples by default, both orientations "
            "paired over the same seat-bound geometry. See "
            "docs/research/v4/V4_RC1_PHASE2_STABLE_CONTRACT_PROMOTION.md and "
            "docs/research/v4/V4_RC1_PHASE1_EVALUATION_METHODOLOGY.md."
        ),
    )
    parser.add_argument(
        "--opponents",
        default=None,
        help="comma-separated opponent discovery ids (may instead be set by --preset)",
    )
    parser.add_argument(
        "--group",
        action="store_true",
        help=(
            "retired compatibility flag: new group evaluations can no longer be "
            "created because their Ruleset 2 methodology is retired; historical "
            "group artifacts remain readable"
        ),
    )
    seed_group = parser.add_mutually_exclusive_group()
    seed_group.add_argument("--seeds", default=None, help="comma-separated explicit seeds")
    seed_group.add_argument(
        "--seed-range", default=None, help="inclusive seed range START:END"
    )
    parser.add_argument(
        "--ticks",
        type=_positive_int,
        default=None,
        help=f"tick budget per cell (default: {DEFAULT_TICKS}, unless set by --preset)",
    )
    parser.add_argument(
        "--arena-size",
        type=_positive_int,
        default=None,
        help=(
            f"arena size in cells (default: {Config().arena_size}, unless set by "
            "--preset). A controlled experimental variable: it changes the standard "
            "placement/layout coordinates (which are fractions of arena size) and "
            "therefore the evaluation_id, but is NOT a Ruleset change. See "
            "docs/V3_PHASE0_RESEARCH_BASELINE.md."
        ),
    )
    parser.add_argument(
        "--instr-per-tick",
        type=_positive_int,
        default=None,
        help=(
            f"per-entrant action budget per tick (default: {Config().instr_per_tick}, "
            "unless set by --preset). A controlled experimental variable, not a "
            "Ruleset change -- see docs/V3_PHASE0_RESEARCH_BASELINE.md."
        ),
    )
    parser.add_argument(
        "--kill-weight",
        type=float,
        default=None,
        help=(
            f"score awarded per attributed core capture (default: {Config().weights.kill}). "
            "A controlled experimental variable, per-match configuration rather than a "
            "Ruleset change -- see docs/V3_PHASE3_OFFENSE_PAYOFF_CHARACTERIZATION.md."
        ),
    )
    parser.add_argument("--output", type=Path, default=None, help="evaluation artifact directory")
    parser.add_argument("--retry-failed", action="store_true")
    parser.add_argument(
        "--dry-run", action="store_true", help="print the matrix and exit without running anything"
    )
    parser.add_argument("--quiet", action="store_true")
    parser.add_argument(
        "--json",
        action="store_true",
        help=(
            "print the result as JSON instead of the human-readable summary -- the same "
            "analysis/behavior/capture/group_analysis structure 'bytefray agents "
            "evaluations show --json' produces, over the artifact this run just wrote, so "
            "no second command is needed to get structured output for a run just executed. "
            "Replaces the human summary entirely (never mixed with it); --quiet still "
            "suppresses it. See docs/V3_PRODUCT_SCOPE.md Phase 3."
        ),
    )
    orientation_group = parser.add_mutually_exclusive_group()
    orientation_group.add_argument(
        "--single-orientation",
        action="store_true",
        default=None,
        help=(
            "opt out of the both-entrant-orientations methodology; candidate_first "
            "only, matching pre-v0.9 behavior and matrix size. Overrides --preset. "
            "Does not generalize across entrant order -- see docs/AGENT_LAB.md."
        ),
    )
    orientation_group.add_argument(
        "--both-orientations",
        action="store_true",
        default=None,
        help=(
            "force the both-entrant-orientations methodology, overriding a "
            "--preset that requested single-orientation. Redundant with the "
            "ordinary default when no --preset is given."
        ),
    )
    parser.add_argument(
        "--workers",
        type=_positive_int,
        default=1,
        help=(
            "number of evaluation cells to execute concurrently, via a pool of "
            "long-lived worker subprocesses (default: 1, serial). Never affects "
            "evaluation_id or any per-cell result -- only wall-clock speed. Never "
            "settable by --preset -- execution machinery, not experiment content. "
            "See docs/V1_6_PHASE2_PARALLEL_EVALUATION.md."
        ),
    )
    return parser


def _resolve_seeds(args: argparse.Namespace) -> tuple[int, ...]:
    if args.seeds is not None:
        return parse_seed_list(args.seeds)
    if args.seed_range is not None:
        return parse_seed_range(args.seed_range)
    return (Config().seed,)


def methodology_lines(
    orientation_mode: str, *, arena_alignment_mode: str = EVALUATION_ARENA_ALIGNMENT_MODE
) -> tuple[str, str]:
    """Shared human-readable methodology disclosure (Phase 5 spec Sec O.1/AA.5).

    Takes the same ``orientation_mode`` string vocabulary
    (``ORIENTATION_MODE_BOTH``/``ORIENTATION_MODE_CANDIDATE_FIRST_ONLY``)
    identity/provenance already use, rather than a bare bool, so both the
    live-run CLI (``request.orientation_mode``) and the historical-read
    path (``evaluation_history``'s recovered/recorded
    ``EvaluationSummary.orientation_mode.value``) can call this one shared
    function -- never two independently authored copies of the same
    wording (Designer reuses it too, via
    ``app.services.designer_workflows``). Must never describe a
    both-orientations evaluation as "fully unbiased"/"fully robust": it
    discloses entrant-orientation coverage and, separately, that arena
    alignment is always fixed in v0.9 (translation robustness is not
    evaluated -- Sec AA.1/AA.2).
    """

    orientation_line = (
        "Entrant orientation: both"
        if orientation_mode == ORIENTATION_MODE_BOTH
        else (
            "Entrant orientation: candidate-first only -- does not generalize "
            "across entrant order"
        )
    )
    alignment_line = (
        f"Arena alignment: {arena_alignment_mode} -- translation robustness not evaluated"
    )
    return orientation_line, alignment_line


def _print_v2_methodology(request: EvaluationRequest, matrix: Sequence[EvaluationCell]) -> None:
    """Phase 1S: make an expanded v2 matrix's size/conditions obvious up front.

    Never left to be inferred from a final win rate -- a permanent-v2
    evaluation multiplies every opponent's cell count by
    ``len(standard_placements()) * (2 if both_orientations else 1)``, which
    a user must see stated plainly, not reverse-engineer from ``matches:``.
    """

    print(f"ruleset: {request.resolved_rules_compatibility_id}")
    print(f"seeds: {', '.join(str(seed) for seed in request.seeds)}")
    if request.group:
        _print_group_methodology(request)
        return
    placements = standard_placements(request.resolved_arena_size)
    orientations = 2 if request.both_orientations else 1
    cells_per_opponent = len(request.seeds) * len(placements) * orientations
    print(f"placements: {len(placements)} ({', '.join(p.placement_id for p in placements)})")
    print(f"scheduler orders: {'balanced' if request.both_orientations else 'candidate-first only'}")
    print(f"cells/opponent: {cells_per_opponent}")


def _print_group_methodology(request: EvaluationRequest) -> None:
    """v2.0.0-beta2 Phase 2: multi-entrant matrix disclosure, mirroring
    the 1v1 disclosure above exactly -- ruleset/seeds are already printed
    by the caller; roster/layout/permutation/cell-count are this mode's
    own additional dimensions.
    """

    roster = request.roster_agent_ids
    layouts = standard_layouts(len(roster), request.resolved_arena_size)
    seat_assignments = enumerate_seat_assignments(roster)
    cells = len(request.seeds) * len(layouts) * len(seat_assignments)
    print(f"roster: {', '.join(roster)} ({len(roster)} entrants)")
    print(f"layouts: {len(layouts)} ({', '.join(layout.layout_id for layout in layouts)})")
    print(f"seat assignments: {len(seat_assignments)}")
    print(f"cells: {cells}")


def _print_experimental_conditions(request: EvaluationRequest) -> None:
    """Disclose any non-default v3 Phase 0 experimental condition.

    Prints nothing at all when both are at their ordinary defaults, so
    every existing evaluation's human-readable output is unchanged
    character-for-character.
    """

    defaults = Config()
    if request.resolved_arena_size != defaults.arena_size:
        print(f"arena size: {request.resolved_arena_size} (non-default)")
    if request.resolved_instr_per_tick != defaults.instr_per_tick:
        print(f"action budget/tick: {request.resolved_instr_per_tick} (non-default)")
    if request.resolved_kill_weight != defaults.weights.kill:
        print(f"kill weight: {request.resolved_kill_weight} (non-default)")
    # v3 Phase 2: only ever non-None for the experimental locality Ruleset,
    # so this line is absent from every non-locality evaluation's output.
    if request.resolved_locality_reach is not None:
        print(
            f"locality reach: {request.resolved_locality_reach} "
            "(EXPERIMENTAL bounded locality)"
        )


def _print_matrix(
    request: EvaluationRequest,
    matrix: Sequence[EvaluationCell],
    preset: EvaluationPreset | None = None,
) -> None:
    if preset is not None:
        print(f"preset: {preset.name}  (content_digest={preset.content_digest})")
    print(f"candidate: {request.candidate_id}")
    print(f"baseline: {request.baseline_id if request.baseline_id else 'none'}")
    print(f"opponents: {', '.join(request.opponent_ids)}")
    if request.is_v2_methodology:
        _print_v2_methodology(request, matrix)
    else:
        print(f"seeds: {', '.join(str(seed) for seed in request.seeds)}")
    print(f"ticks: {request.ticks}")
    # v3 Phase 0D: disclose the two controlled experimental variables
    # whenever they are NOT at their ordinary defaults. Printed
    # unconditionally would add two noise lines to every ordinary
    # evaluation's output; omitted when non-default, a reader would have no
    # way to tell a 1024-cell arena run from a 4096-cell one -- exactly the
    # "omission would be misleading" case. Same conditional-disclosure
    # discipline `preset:` above already uses.
    _print_experimental_conditions(request)
    # v2.0.0-beta2 Phase 2: "subjects: N opponents: M" and the 2-value
    # "Entrant orientation: both/candidate-first only" line both describe
    # 1v1 methodology's own axes (subject_role, orientation) -- neither is
    # a meaningful description of a group evaluation's roster/seat-
    # assignment axes, and printing them anyway would misrepresent group
    # semantics as if a 2-value orientation were still the scheduler-order
    # axis (Phase 2 design-audit finding). `_print_group_methodology`
    # already discloses roster/layouts/seat assignments above; only the
    # arena-alignment line (still correct and useful for group -- it names
    # the resolved group methodology identifier) is kept.
    if not request.group:
        subjects = [request.candidate_id] + ([request.baseline_id] if request.baseline_id else [])
        print(f"subjects: {len(subjects)}  opponents: {len(request.opponent_ids)}  seeds: {len(request.seeds)}")
    print(f"matches: {len(matrix)}")
    _, alignment_line = methodology_lines(
        request.orientation_mode,
        arena_alignment_mode=resolved_arena_alignment_mode(
            request.is_v2_methodology, request.group, request.is_v4_methodology
        ),
    )
    if not request.group:
        orientation_line, _ = methodology_lines(request.orientation_mode)
        print(orientation_line)
    print(alignment_line)


def _matrix_to_json(
    request: EvaluationRequest, matrix: Sequence[EvaluationCell], preset: EvaluationPreset | None
) -> dict[str, Any]:
    """v3.0 Phase 3: ``--dry-run --json``'s structured counterpart to
    ``_print_matrix`` -- kept a minimal preview (no cells enumerated), since
    the matrix itself is already fully described by ``request``/its size.
    """

    return {
        "preset": preset.name if preset is not None else None,
        "candidate_id": request.candidate_id,
        "baseline_id": request.baseline_id,
        "opponent_ids": list(request.opponent_ids),
        "seeds": list(request.seeds),
        "ticks": request.ticks,
        "matrix_size": len(matrix),
        "group": request.group,
        "orientation_mode": request.orientation_mode,
        "arena_alignment_mode": resolved_arena_alignment_mode(
            request.is_v2_methodology, request.group, request.is_v4_methodology
        ),
    }


def _result_to_json(result: EvaluationResult, request: EvaluationRequest) -> dict[str, Any]:
    """v3.0 Phase 3: the live ``agents evaluate`` command's structured-output
    counterpart to ``evaluations show --json`` -- the same top-level
    ``analysis``/``behavior``/``capture``/``group_analysis`` keys, computed
    the identical way ``_print_result`` computes them for its own text
    presentation, layered onto the artifact this run just wrote (read back
    from ``result.state_path`` rather than re-derived, so this can never
    drift from what was actually persisted). No second command is needed to
    get structured output for a run just executed.
    """

    data: dict[str, Any] = json.loads(result.state_path.read_text(encoding="utf-8"))

    analysis = None
    if request.baseline_id is not None:
        from battle_engine.evaluation_analysis import analyze as _analyze_evaluation

        analysis = _analyze_evaluation(request.candidate_id, request.baseline_id, result.cells)
    data["analysis"] = analysis.to_json() if analysis is not None else None

    behavior = None
    capture = None
    group_analysis = None
    if request.group:
        from battle_engine.evaluation_group_analysis import (
            analyze_group,
            group_cell_ref_from_evaluation_cell,
        )

        group_scored_refs = [
            group_cell_ref_from_evaluation_cell(cell) for cell in result.cells if cell.is_scored
        ]
        if group_scored_refs:
            group_analysis = analyze_group(request.roster_agent_ids, group_scored_refs)
    else:
        from battle_engine.evaluation_behavior import (
            analyze_behavior,
            cell_ref_from_evaluation_cell,
        )

        scored_refs = [cell_ref_from_evaluation_cell(cell) for cell in result.cells if cell.is_scored]
        behavior = analyze_behavior(request.candidate_id, request.baseline_id, scored_refs)
        if request.is_v2_methodology:
            from battle_engine.evaluation_capture import analyze_capture

            capture = analyze_capture(request.candidate_id, request.baseline_id, scored_refs)

    data["behavior"] = behavior.to_json() if behavior is not None else None
    data["capture"] = capture.to_json() if capture is not None else None
    data["group_analysis"] = group_analysis.to_json() if group_analysis is not None else None
    return data


def _fmt_optional_g(value: float | None) -> str:
    return f"{value:g}" if value is not None else "n/a (group)"


def _fmt_optional_pct2(value: float | None) -> str:
    return f"{value:.2f}%" if value is not None else "n/a (group)"


def _print_aggregate(aggregate: SubjectAggregate) -> None:
    print(f"[{aggregate.subject_role}] {aggregate.subject_id}")
    print(f"  win rate: {aggregate.win_rate_display}")
    print(
        f"  wins={aggregate.wins} losses={aggregate.losses} ties={aggregate.ties} "
        f"played={aggregate.matches_played}"
    )
    print(
        f"  score_avg={aggregate.score_avg:g} "
        f"score_differential_avg={_fmt_optional_g(aggregate.score_differential_avg)} "
        f"ticks_avg={aggregate.ticks_avg:g}"
    )
    print(
        f"  territory_avg={aggregate.territory_avg:.2f}% "
        f"territory_differential_avg={_fmt_optional_pct2(aggregate.territory_differential_avg)}"
    )
    if aggregate.subject_init_failures or aggregate.opponent_init_failures or aggregate.failed:
        print(
            f"  subject_init_failed={aggregate.subject_init_failures} "
            f"opponent_init_failed={aggregate.opponent_init_failures} failed={aggregate.failed}"
        )


def _print_orientation_breakdown(subject_aggregates: Sequence[SubjectAggregate]) -> None:
    """K.2: a compact per-orientation win-rate line alongside the pooled block.

    Never averages an orientation split away -- printed only alongside the
    pooled aggregate, so a regression hidden by pooling (candidate wins
    every candidate-first cell but loses every opponent-first cell) stays
    visible in the ordinary, non-verbose CLI output.
    """

    candidate_first = next(
        (a for a in subject_aggregates if a.orientation_scope == ORIENTATION_CANDIDATE_FIRST), None
    )
    opponent_first = next(
        (a for a in subject_aggregates if a.orientation_scope == ORIENTATION_OPPONENT_FIRST), None
    )
    if candidate_first is not None and opponent_first is not None:
        print(
            f"  candidate_first: {candidate_first.win_rate_display}   "
            f"opponent_first: {opponent_first.win_rate_display}"
        )


def _print_comparison_entry(entry: ComparisonEntry, ticks: int) -> None:
    placement_suffix = f" placement={entry.placement_id}" if entry.placement_id != "fixed" else ""
    print(
        f"  opponent={entry.opponent_id} seed={entry.seed} orientation={entry.orientation}"
        f"{placement_suffix}"
    )
    print(f"    candidate: {entry.candidate_outcome}  baseline: {entry.baseline_outcome}")
    if entry.reason:
        print(f"    reason: {entry.reason}")
    if entry.candidate_score is not None and entry.baseline_score is not None:
        print(f"    score: candidate={entry.candidate_score:g} baseline={entry.baseline_score:g}")
    print(
        "    rerun candidate: "
        f"{rerun_command('<candidate>', entry.opponent_id, entry.seed, ticks, entry.orientation)}"
    )
    if entry.baseline_outcome is not None:
        print(
            "    rerun baseline:  "
            f"{rerun_command('<baseline>', entry.opponent_id, entry.seed, ticks, entry.orientation)}"
        )


def _print_evidence(analysis: Any) -> None:
    """v1.6 Phase 4 (docs/V1_6_PHASE4_EVALUATION_ANALYSIS.md Sec 12): a
    concise Wilson-interval + exact paired evidence block -- magnitude and
    sample size shown before any p-value, never a bare
    SIGNIFICANT/NOT SIGNIFICANT verdict. ``analysis`` is an
    ``evaluation_analysis.EvaluationAnalysis``, typed as ``Any`` here only
    to avoid a top-level circular import (``evaluation_analysis`` imports
    from this module); see the deferred import at each call site.
    """

    from battle_engine.evaluation_analysis import EvidenceState

    def _rate_line(label: str, estimate: Any) -> str:
        interval = estimate.win_interval
        if interval is None:
            return f"  {label}: insufficient data (0 scored matches)"
        pct = 100.0 * (estimate.observed_win_rate or 0.0)
        return (
            f"  {label}: {estimate.wins}/{estimate.matches_played} ({pct:.0f}%)  "
            f"{round(interval.confidence_level * 100)}% CI "
            f"[{100.0 * interval.lower:.0f}%, {100.0 * interval.upper:.0f}%]"
        )

    print("evidence:")
    print(_rate_line(f"candidate ({analysis.candidate_id})", analysis.candidate_overall))
    if analysis.baseline_overall is not None:
        print(_rate_line(f"baseline ({analysis.baseline_id})", analysis.baseline_overall))
    paired = analysis.overall_paired
    if paired is not None:
        if paired.state == EvidenceState.NO_MATCHED_CONDITIONS:
            print("  paired: no matched candidate/baseline conditions")
        elif paired.state == EvidenceState.NO_DISCORDANT_PAIRS:
            print(
                f"  paired: {paired.paired_count} matched conditions, no discordant pairs "
                "(all unchanged/inconclusive) -- interval/exact test not meaningful"
            )
        else:
            interval = paired.better_interval
            assert interval is not None and paired.exact_p_value is not None
            print(
                f"  paired: candidate better in {paired.improved}/{paired.discordant} discordant "
                f"conditions ({100.0 * (paired.better_proportion_of_discordant or 0.0):.0f}%)  "
                f"{round(interval.confidence_level * 100)}% CI "
                f"[{100.0 * interval.lower:.0f}%, {100.0 * interval.upper:.0f}%]  "
                f"exact two-sided p={paired.exact_p_value:.3g}"
            )
        print(f"  {analysis.opponent_consistency}")
        print(f"  {analysis.orientation_consistency}")


def _fmt_fraction_pct(value: float | None) -> str:
    return f"{100.0 * value:.0f}%" if value is not None else "n/a"


def _fmt_percent(value: float | None) -> str:
    return f"{value:.1f}%" if value is not None else "n/a"


def _fmt_rate(value: float | None) -> str:
    return f"{value:.2f}" if value is not None else "n/a"


def _print_behavior(analysis: Any) -> None:
    """v1.6 Phase 5 (docs/V1_6_PHASE5_BEHAVIOR_ANALYSIS.md Sec 18): a concise
    behavior-profile block -- survival, write activity, territory
    occupancy/retention, kill interaction -- describing *how* the
    candidate played, deliberately kept separate from the evidence: block
    above (which describes outcome) and never derived from it. ``analysis``
    is an ``evaluation_behavior.BehaviorAnalysis``, typed ``Any`` here only
    to avoid a top-level circular import (mirrors ``_print_evidence``'s
    existing pattern -- ``evaluation_behavior`` imports from this module).
    """

    from battle_engine.evaluation_behavior import largest_bounded_differences

    overall = analysis.candidate_overall
    if overall.sample_count == 0:
        return
    survival = overall.dimension("survival_fraction")
    writes = overall.dimension("writes_per_tick")
    last = overall.dimension("territory_last_pct")
    peak = overall.dimension("territory_max_pct")
    avg = overall.dimension("territory_avg_pct")
    retention = overall.dimension("territory_retention")
    kills = overall.dimension("kills_per_match")
    deaths = overall.dimension("deaths_per_match")
    print("behavior:")
    print(
        f"  survival: {_fmt_fraction_pct(survival.mean)} (n={survival.n})   "
        f"writes/tick: {_fmt_rate(writes.mean)}"
    )
    print(
        f"  territory: last={_fmt_percent(last.mean)}  peak={_fmt_percent(peak.mean)}  "
        f"avg={_fmt_percent(avg.mean)}  retention={_fmt_fraction_pct(retention.mean)}"
    )
    print(f"  kills: {_fmt_rate(kills.mean)}/match   deaths: {_fmt_rate(deaths.mean)}/match")
    orientation_largest = largest_bounded_differences(analysis.candidate_orientation_deltas, limit=2)
    if orientation_largest:
        print(f"  orientation-sensitive dimensions: {', '.join(orientation_largest)}")
    if analysis.candidate_vs_baseline_largest:
        print(
            "  largest candidate-vs-baseline behavioral differences: "
            + ", ".join(analysis.candidate_vs_baseline_largest)
        )


def _print_capture_aggregate(aggregate: Any) -> None:
    print(f"  captures caused: {aggregate.captures_caused}/{aggregate.available_count}")
    print(f"  captures suffered: {aggregate.captures_suffered}/{aggregate.available_count}")
    print(
        f"  capture rate: caused={_fmt_fraction_pct(aggregate.capture_rate_caused)} "
        f"suffered={_fmt_fraction_pct(aggregate.capture_rate_suffered)}"
    )
    print(f"  survival rate (capture-avoidance): {_fmt_fraction_pct(aggregate.survival_rate)}")
    if aggregate.capture_ticks:
        print(
            f"  capture tick: mean={_fmt_rate(aggregate.mean_capture_tick)} "
            f"median={_fmt_rate(aggregate.median_capture_tick)}"
        )


def _print_capture(analysis: Any) -> None:
    print("capture/core evidence:")
    print(f"[candidate] {analysis.candidate_id}")
    _print_capture_aggregate(analysis.candidate_overall)
    if analysis.baseline_overall is not None:
        print(f"[baseline] {analysis.baseline_id}")
        _print_capture_aggregate(analysis.baseline_overall)


def _fmt_rate_stat(stat: Any) -> str:
    if stat.trials == 0:
        return "n/a (0 matches)"
    interval = stat.interval
    pct = 100.0 * (stat.rate or 0.0)
    ci = (
        f"  {round(interval.confidence_level * 100)}% CI [{100.0 * interval.lower:.0f}%, {100.0 * interval.upper:.0f}%]"
        if interval is not None
        else ""
    )
    return f"{stat.successes}/{stat.trials} ({pct:.0f}%){ci}"


def _print_entrant_summary(label: str, summary: Any) -> None:
    print(f"  {label}:")
    print(f"    winner: {_fmt_rate_stat(summary.winner)}")
    print(f"    survival: {_fmt_rate_stat(summary.survival)}")
    if summary.score.n:
        print(f"    score: mean={summary.score.mean:.2f} (n={summary.score.n})")
    if summary.capture_suffered.trials:
        print(
            f"    captured: {_fmt_rate_stat(summary.capture_suffered)}   "
            f"caused: {_fmt_rate_stat(summary.capture_caused)}"
        )


def _print_group_analysis(result: EvaluationResult, request: EvaluationRequest) -> None:
    """v2.0.0-beta2 Phase 3: entrant-symmetric group analysis, presented
    candidate-first for CLI familiarity (Sec 22) -- ``evaluation_group_
    analysis.analyze_group`` itself never receives a candidate id (Sec 6/
    21's symmetry invariant), so this is pure presentation-time selection
    over an already-computed, already-symmetric result.
    """

    from battle_engine.evaluation_group_analysis import (
        analyze_group,
        candidate_focused_view,
        group_cell_ref_from_evaluation_cell,
    )

    scored_refs = [group_cell_ref_from_evaluation_cell(cell) for cell in result.cells if cell.is_scored]
    print("group analysis:")
    if not scored_refs:
        print("  no scored cells")
        return
    analysis = analyze_group(request.roster_agent_ids, scored_refs)
    view = candidate_focused_view(analysis, request.candidate_id)
    if view.legacy_subject_outcome_ambiguous:
        print(
            "  candidate logical outcome: ambiguous in legacy cell summaries; "
            f"{view.candidate_multiplicity} physical candidate instances occupy each cell"
        )
        print("  rates below use physical entrant instances as their denominator")
    if view.candidate is not None:
        label = f"candidate ({request.candidate_id}) overall"
        if view.candidate_multiplicity > 1:
            label += " [per physical entrant instance]"
        _print_entrant_summary(label, view.candidate)
    if view.candidate_seat_sensitivity is not None:
        print("  by seat:")
        for seat_summary in view.candidate_seat_sensitivity.by_seat:
            print(f"    {seat_summary.scope_label}: winner={_fmt_rate_stat(seat_summary.winner)}")
        seat_range = view.candidate_seat_sensitivity.winner_rate_range
        if seat_range is not None:
            print(f"    seat sensitivity (winner-rate range): {100.0 * seat_range:.0f} pp")
    if view.candidate_layout_sensitivity is not None:
        print("  by layout:")
        for layout_summary in view.candidate_layout_sensitivity.by_layout:
            print(f"    {layout_summary.scope_label}: winner={_fmt_rate_stat(layout_summary.winner)}")
        layout_range = view.candidate_layout_sensitivity.winner_rate_range
        if layout_range is not None:
            print(f"    layout sensitivity (winner-rate range): {100.0 * layout_range:.0f} pp")
    if view.other_entrants:
        print("  other entrants:")
        for other in view.other_entrants:
            _print_entrant_summary(other.agent_id, other)
    matrix = analysis.interaction_matrix
    if matrix.pairs or matrix.unattributed_captures:
        print("  captures (captor -> victim):")
        for pair in matrix.pairs:
            rate_pct = 100.0 * (pair.rate or 0.0)
            print(f"    {pair.captor_agent_id} -> {pair.victim_agent_id}: {pair.count} ({rate_pct:.0f}%)")
        if matrix.unattributed_captures:
            print(f"    unattributed: {matrix.unattributed_captures}")


def _print_result(result: EvaluationResult, request: EvaluationRequest) -> None:
    print(f"evaluation: {result.evaluation_id}")
    # v2.0.0-beta2 Phase 2: skip the 1v1-only "Entrant orientation:" line
    # for a group evaluation -- see _print_matrix's identical guard.
    orientation_line, alignment_line = methodology_lines(
        request.orientation_mode,
        arena_alignment_mode=resolved_arena_alignment_mode(
            request.is_v2_methodology, request.group, request.is_v4_methodology
        ),
    )
    if not request.group:
        print(orientation_line)
    print(alignment_line)
    for aggregate in result.aggregates:
        if aggregate.orientation_scope != "all":
            continue
        if request.group and request.roster_agent_ids.count(aggregate.subject_id) > 1:
            print(f"[{aggregate.subject_role}] {aggregate.subject_id}")
            print(
                "  legacy candidate outcome aggregate: suppressed because this logical "
                "agent occupies multiple physical seats"
            )
            continue
        _print_aggregate(aggregate)
        # v2.0.0-beta2 Phase 2: orientation is not a meaningful axis for a
        # group cell (seat assignment is the generalized scheduler-order
        # axis instead, per-cell, never pooled into an evaluation-wide
        # orientation breakdown) -- every group cell defaults to
        # "candidate_first" (EvaluationCell.orientation's own sentinel),
        # so printing this breakdown for a group evaluation would show a
        # misleading "opponent_first: 0" rather than "not applicable".
        if request.both_orientations and not request.group:
            subject_aggregates = [
                a
                for a in result.aggregates
                if a.subject_role == aggregate.subject_role and a.subject_id == aggregate.subject_id
            ]
            _print_orientation_breakdown(subject_aggregates)
    # v2.0.0-beta2 Phase 2: evaluation_behavior/evaluation_capture's Tier-2
    # readers resolve the subject's physical match slot via `cell.
    # orientation` (a 2-value candidate_first/opponent_first axis) --
    # meaningless for a group cell, whose subject occupies whichever seat
    # `cell.subject_seat` says, not a fixed slot "A". They stay deferred
    # for group cells for exactly that reason; v2.0.0-beta2 Phase 3 adds
    # `evaluation_group_analysis`, an entrant-symmetric sibling built for
    # this axis instead -- see docs/V2_0_BETA2_PHASE3_MULTI_ENTRANT_
    # ANALYSIS.md.
    if request.group:
        _print_group_analysis(result, request)
    else:
        from battle_engine.evaluation_behavior import (
            analyze_behavior,
            cell_ref_from_evaluation_cell,
        )

        scored_refs = [cell_ref_from_evaluation_cell(cell) for cell in result.cells if cell.is_scored]
        _print_behavior(analyze_behavior(request.candidate_id, request.baseline_id, scored_refs))
        if request.is_v2_methodology:
            from battle_engine.evaluation_capture import analyze_capture

            _print_capture(analyze_capture(request.candidate_id, request.baseline_id, scored_refs))
    if request.baseline_id is not None:
        regressed = [entry for entry in result.comparison if entry.classification == "regressed"]
        improved = [entry for entry in result.comparison if entry.classification == "improved"]
        unchanged = [entry for entry in result.comparison if entry.classification == "unchanged"]
        inconclusive = [entry for entry in result.comparison if entry.classification == "inconclusive"]
        print(
            f"comparison: {len(improved)} improved, {len(regressed)} regressed, "
            f"{len(unchanged)} unchanged, {len(inconclusive)} inconclusive "
            f"(of {len(result.comparison)} matched cells)"
        )
        from battle_engine.evaluation_analysis import analyze as _analyze_evaluation

        _print_evidence(
            _analyze_evaluation(request.candidate_id, request.baseline_id, result.cells)
        )
        if regressed:
            print("regressions:")
            for entry in regressed:
                _print_comparison_entry(entry, request.ticks)
        if inconclusive:
            print("inconclusive:")
            for entry in inconclusive:
                _print_comparison_entry(entry, request.ticks)
    failed = result.failed_cells
    corrupted = result.corrupted_cells
    if failed:
        print("failed cells:")
        for cell in failed:
            print(
                f"  {cell.subject_role}={cell.subject_id} opponent={cell.opponent_id} "
                f"seed={cell.seed} code={cell.error_code} error={cell.error_message}"
            )
    if corrupted:
        print("corrupted cells (rerun with --retry-failed to reconcile):")
        for cell in corrupted:
            print(
                f"  {cell.subject_role}={cell.subject_id} opponent={cell.opponent_id} "
                f"seed={cell.seed} code={cell.error_code} error={cell.error_message}"
            )
    drifted = result.drift_cells
    if drifted:
        print(
            "SOURCE DRIFT DETECTED -- evaluation aborted; matrix execution stopped "
            "before completion. Start a fresh evaluation to evaluate the changed agent:"
        )
        for cell in drifted:
            print(
                f"  {cell.subject_role}={cell.subject_id} opponent={cell.opponent_id} "
                f"seed={cell.seed} code={cell.error_code} error={cell.error_message}"
            )
    print(f"evaluation artifact: {result.state_path}")


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)

    # v1.6 Phase 3: resolution layering is (1) ordinary defaults, (2) the
    # --preset (if any), (3) an explicit CLI option -- explicit always wins.
    # This is the one authoritative resolution path: a preset only ever
    # supplies values into the same variables an explicit invocation would
    # set directly below, so nothing downstream of this block (preflight,
    # EvaluationRequest, evaluation_id) can tell a preset was involved. See
    # docs/V1_6_PHASE3_EVALUATION_PRESETS.md.
    preset: EvaluationPreset | None = None
    if args.preset is not None:
        try:
            preset = load_preset(get_data_root(), args.preset)
        except EvaluationPresetError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 2

    candidate_id = args.candidate_id
    if candidate_id is None and preset is not None:
        candidate_id = preset.candidate_id
    if candidate_id is None:
        print(
            "ERROR: candidate is required (supply it as a positional argument, "
            "or set 'candidate' in the --preset).",
            file=sys.stderr,
        )
        return 2

    baseline_id = args.baseline
    if baseline_id is None and preset is not None:
        baseline_id = preset.baseline_id

    try:
        if args.group and (args.single_orientation or args.both_orientations):
            raise EvaluationConfigurationError(
                "--single-orientation/--both-orientations cannot be combined with --group; "
                "group mode enumerates seat assignments instead of the pairwise orientation axis."
            )
        if args.opponents is not None:
            opponent_ids = parse_opponents(args.opponents)
        elif preset is not None and preset.opponent_ids is not None:
            opponent_ids = preset.opponent_ids
        else:
            raise EvaluationConfigurationError(
                "opponents are required (supply --opponents, or set 'opponents' "
                "in the --preset)."
            )

        # v2.0.0-beta2 Phase 1 / v4.0.0-rc1 Phase 1 (F.6 remediation):
        # resolved before seeds -- the standard v2/v4 seed default (below)
        # depends on which methodology this evaluation resolves to. Same
        # three-tier resolution as every other option (explicit CLI >
        # --preset > ordinary default). Moved after opponent_ids above
        # (F.6): a metadata-aware omitted-Ruleset resolution needs the
        # whole roster's real declared Agent API version, not just
        # candidate/baseline, so opponents must already be known here.
        ruleset_id = args.ruleset
        if ruleset_id is None and preset is not None:
            ruleset_id = preset.ruleset_id
        if ruleset_id is None:
            ruleset_id = BYTEFRAY_RULESET_V4_ID

        if args.seeds is not None or args.seed_range is not None:
            seeds = _resolve_seeds(args)
        elif preset is not None and preset.seeds is not None:
            seeds = preset.seeds
        elif preset is not None and preset.seed_range is not None:
            seeds = tuple(range(preset.seed_range[0], preset.seed_range[1] + 1))
        else:
            # v4.0.0-rc1 Phase 1 (research report Sec H.1 item 2): the
            # stable v4 methodology's own standard sample set -- an
            # explicit --seeds/--seed-range or --preset seed selection
            # always overrides this (see the branches above, checked
            # first).
            seeds = STANDARD_V4_SEEDS
    except EvaluationConfigurationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if args.ticks is not None:
        ticks = args.ticks
    elif preset is not None and preset.ticks is not None:
        ticks = preset.ticks
    else:
        ticks = DEFAULT_TICKS

    # v3 Phase 0D: the identical three-tier resolution `--ticks` above uses
    # (explicit CLI > --preset > ordinary default), with "ordinary default"
    # expressed as `None` rather than a literal so `EvaluationRequest`
    # remains the single place `Config()`'s defaults are resolved.
    if args.arena_size is not None:
        arena_size = args.arena_size
    elif preset is not None and preset.arena_size is not None:
        arena_size = preset.arena_size
    else:
        arena_size = None

    if args.instr_per_tick is not None:
        instr_per_tick = args.instr_per_tick
    elif preset is not None and preset.instr_per_tick is not None:
        instr_per_tick = preset.instr_per_tick
    else:
        instr_per_tick = None

    # v3 Phase 3: `--kill-weight` follows the identical "no --preset field"
    # shape locality_reach uses below -- explicit CLI or ordinary default,
    # since a reweighting experiment has no business being a reusable
    # product-facing preset shape.
    kill_weight = args.kill_weight

    # v3 Phase 2's experimental bounded-locality Ruleset was never reachable
    # from this product CLI, and V6 Phase 2B.9 retired it from execution
    # entirely -- `EvaluationService._validate` now rejects any non-`None`
    # `EvaluationRequest.locality_reach` unconditionally. Always `None` here.
    locality_reach = None

    if args.single_orientation:
        both_orientations = False
    elif args.both_orientations:
        both_orientations = True
    elif preset is not None and preset.orientation is not None:
        both_orientations = preset.orientation == _PRESET_ORIENTATION_BOTH
    else:
        both_orientations = True

    service = EvaluationService()
    try:
        _specs, evaluation_id = service.preflight(
            candidate_id=candidate_id,
            opponent_ids=opponent_ids,
            seeds=seeds,
            baseline_id=baseline_id,
            ticks=ticks,
            both_orientations=both_orientations,
            ruleset_id=ruleset_id,
            group=args.group,
            arena_size=arena_size,
            instr_per_tick=instr_per_tick,
            locality_reach=locality_reach,
            kill_weight=kill_weight,
        )
    except EvaluationConfigurationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    root = get_data_root()
    output_dir = (
        args.output.expanduser().resolve()
        if args.output is not None
        else _default_output_dir(root, evaluation_id).resolve()
    )
    request = EvaluationRequest(
        candidate_id=candidate_id,
        opponent_ids=opponent_ids,
        seeds=seeds,
        output_dir=output_dir,
        baseline_id=baseline_id,
        ticks=ticks,
        retry_failures=args.retry_failed,
        both_orientations=both_orientations,
        workers=args.workers,
        ruleset_id=ruleset_id,
        group=args.group,
        arena_size=arena_size,
        instr_per_tick=instr_per_tick,
        locality_reach=locality_reach,
        kill_weight=kill_weight,
    )
    matrix = build_matrix(request, evaluation_id)
    if args.dry_run:
        if args.json:
            if not args.quiet:
                print(json.dumps(_matrix_to_json(request, matrix, preset), indent=2, sort_keys=True))
        else:
            _print_matrix(request, matrix, preset)
        return 0
    if not args.quiet and not args.json:
        _print_matrix(request, matrix, preset)

    try:
        result = service.run(request)
    except EvaluationConfigurationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if not args.quiet:
        if args.json:
            print(json.dumps(_result_to_json(result, request), indent=2, sort_keys=True))
        else:
            _print_result(result, request)
    return 1 if (result.failed_cells or result.corrupted_cells or result.drift_cells) else 0


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
