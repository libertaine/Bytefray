"""``EvaluationService`` -- coordinates (validates, freezes, dispatches,
checkpoints, and finalizes) one evaluation run.

V6 Phase 3J: this module is the canonical owner of ``EvaluationService`` and
the coordinator-level helpers it alone uses (execution-context
deduplication, drift-detail shaping, the parallel dispatch loop and its
abandoned-cell draining).  It is the last stop in the Phase 3 sequence that
gave every lower-level evaluation concept -- contracts, identity, planning,
cell execution, the worker protocol, and artifact/resume persistence -- its
own dedicated module: this module *composes* those owners into "run (or
resume) an evaluation," and nothing here reimplements what any of them
already own.

``battle_engine.agent_evaluation`` remains the permanent compatibility
facade and the CLI/presentation surface (``main``, argument parsing, result
printing, the rerun/opponent/seed parsing helpers Designer also reuses).  It
imports ``EvaluationService`` from here -- never the other way around, and
never a copy -- so ``agent_evaluation.EvaluationService is
evaluation_service.EvaluationService`` always holds.  This module therefore
must never import ``agent_evaluation``, any CLI/presentation helper,
Designer/app code, or ``evaluation_history``.
"""

from __future__ import annotations

import queue
import threading
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import replace
from pathlib import Path
from typing import Any

import battle_engine.evaluation_identity as _evaluation_identity
from battle_engine.agent_test import DEFAULT_TICKS
from battle_engine.agent_worker import WorkerCallStatus
from battle_engine.agents import AgentSpec
from battle_engine.evaluation_analysis import all_subject_aggregates, compare_candidate_baseline
from battle_engine.evaluation_artifact import (
    RevisionPlanEntry,
    checkpoint_cells,
    load_evaluation_state,
    resolve_cell_from_state,
    resolve_revision_results,
    write_evaluation_state,
)
from battle_engine.evaluation_artifact import (
    utc_now_iso as _utc_now_iso,
)
from battle_engine.evaluation_cell_execution import (
    CellExecutionResult,
    _resolve_python_agent,
    execute_cell,
)
from battle_engine.evaluation_contracts import (
    RESEARCH_SCALE_MAX_ARENA_SIZE,
    RESEARCH_SCALE_MIN_ARENA_SIZE,
    STANDARD_V4_ARENA_SIZE,
    TERMINAL_LIFECYCLE_STATES,
    ComparisonEntry,
    EffectiveConditions,
    EvaluationCell,
    EvaluationConfigurationError,
    EvaluationRequest,
    EvaluationResult,
    ExecutionContext,
    SubjectAggregate,
    _resolved_lifecycle_state,
    effective_conditions_for,
    is_ruleset_v2_methodology,
    is_ruleset_v4_methodology,
    is_ruleset_v6_research_scale_methodology,
    is_ruleset_v6_research_scale_move_methodology,
    resolved_arena_alignment_mode,
    resolved_identity_version,
    resolved_schema_version,
)
from battle_engine.evaluation_identity import (
    agent_identity,
    effective_conditions_payload,
)
from battle_engine.evaluation_planning import (
    build_matrix,
    resolve_v4_seed_geometry,
    standard_layouts,
    standard_placements,
)
from battle_engine.evaluation_worker import (
    EvaluationCellWorkerHandle,
    WorkerFailure,
    _cell_from_wire,
)
from battle_engine.paths import get_data_root
from battle_engine.project_info import get_project_info
from battle_engine.python_runtime import CORE_SIZE
from battle_engine.ruleset_policy import (
    BYTEFRAY_RULESET_V4_ID,
    BYTEFRAY_RULESET_V6_RESEARCH_SCALE_ID,
    BYTEFRAY_RULESET_V6_RESEARCH_SCALE_MOVE_ID,
)

# V6 Phase 4B (task Sec 6) and Phase 4C: the finite, explicit set of Ruleset
# identities `agents evaluate` may create a *new* evaluation artifact under.
# Mirrors `ruleset_policy._RULESET_POLICIES`'s own "finite table, never a naming
# convention check" philosophy -- an experimental Ruleset becomes evaluable
# only by an explicit, reviewed addition here, never by broadening this
# check to "anything `resolve_ruleset_policy` recognizes" (which would also
# admit any future non-evaluation-scoped Ruleset the moment it gets a
# `RulesetPolicy`).
_EVALUATION_ALLOWED_RULESET_IDS: frozenset[str] = frozenset(
    {
        BYTEFRAY_RULESET_V4_ID,
        BYTEFRAY_RULESET_V6_RESEARCH_SCALE_ID,
        BYTEFRAY_RULESET_V6_RESEARCH_SCALE_MOVE_ID,
    }
)


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
            effective_conditions_payload(
                conditions, request.resolved_locality_reach, self._scheduler_override(request)
            ),
        )
        evaluation_id = self._evaluation_id(request, planned_identities, conditions)
        # V6 research-integrity hardening (preflight/run double-freeze):
        # `preflight()` and `run()` each independently resolve agents and
        # compute `evaluation_id` from whatever is on disk *at that call*.
        # A caller (the CLI in particular) that addresses `output_dir` by a
        # preflight-resolved id and only then calls `run()` leaves a window
        # where a source edit between the two calls makes this freshly
        # resolved id disagree with the directory's own name -- silently
        # writing evaluation_id-B's artifact into evaluation_id-A's
        # supposedly content-addressed directory. `output_dir.name` is only
        # ever a bare evaluation id when a caller built it that way (see
        # `looks_like_evaluation_id`); an explicit, arbitrary `--output`
        # never matches this shape and is completely unaffected. Fires
        # before any state is loaded or written for this invocation.
        if (
            _evaluation_identity.looks_like_evaluation_id(request.output_dir.name)
            and request.output_dir.name != evaluation_id
        ):
            raise EvaluationConfigurationError(
                f"Output directory {request.output_dir} is addressed by evaluation id "
                f"{request.output_dir.name!r}, but this request's freshly resolved agent "
                f"source now yields evaluation id {evaluation_id!r}. Agent source likely "
                "changed since preflight; re-run preflight (or pass an explicit --output) "
                "before running."
            )
        resolved_rules_id = request.resolved_rules_compatibility_id
        resolved_is_v2 = is_ruleset_v2_methodology(resolved_rules_id)
        resolved_is_v4 = is_ruleset_v4_methodology(resolved_rules_id)
        resolved_is_v6_research_scale = is_ruleset_v6_research_scale_methodology(resolved_rules_id)
        resolved_is_v6_research_scale_move = is_ruleset_v6_research_scale_move_methodology(
            resolved_rules_id
        )
        resolved_group = request.group and resolved_is_v2
        state_path = request.output_dir / "evaluation.json"
        prior = (
            self._load_state(
                state_path,
                evaluation_id,
                resolved_schema_version(
                    resolved_is_v2,
                    resolved_group,
                    resolved_is_v4,
                    resolved_is_v6_research_scale,
                    resolved_is_v6_research_scale_move,
                ),
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
            resolved_arena_alignment_mode(
                resolved_is_v2,
                resolved_group,
                resolved_is_v4,
                resolved_is_v6_research_scale,
                resolved_is_v6_research_scale_move,
            ),
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
        # bytefray-rules-4 was the only Ruleset that could create a new
        # evaluation artifact.
        #
        # V6 Phase 4B (docs/research/v6/V6_PHASE4_GAMEPLAY_RESEARCH_
        # METHODOLOGY.md Sec 10.2) added `bytefray-rules-6-research-scale`
        # to `_EVALUATION_ALLOWED_RULESET_IDS` alongside it -- an explicit,
        # narrow research-support addition, never a loosening to "any
        # registered Ruleset": every retired identity (including the two
        # alphas and bytefray-rules-1/-2) stays rejected here exactly as
        # before.
        if request.ruleset_id is not None and request.ruleset_id not in _EVALUATION_ALLOWED_RULESET_IDS:
            raise EvaluationConfigurationError(
                f"Unsupported evaluation --ruleset {request.ruleset_id!r}; expected one of "
                f"{sorted(_EVALUATION_ALLOWED_RULESET_IDS)!r}."
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
        #
        # `request.is_v4_methodology` is deliberately used unchanged here
        # (V6 Phase 4B): it is `True` only for stable v4 (its retired alpha2
        # promotion source can never reach this line -- the allow-list above
        # already rejects any explicit --ruleset other than the two
        # currently supported identities), never for the research Ruleset,
        # so this lock continues to apply to stable v4 alone.
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

        # V6 Phase 4B/4C: the variable-arena research Rulesets
        # accept any explicit arena size within the Phase 4A research
        # range, but are not an unbounded escape hatch -- an out-of-range
        # value fails closed with a clear diagnostic, never silently
        # clamped to the nearest supported bound.
        if (
            (request.is_v6_research_scale_methodology or request.is_v6_research_scale_move_methodology)
            and request.arena_size is not None
            and not (RESEARCH_SCALE_MIN_ARENA_SIZE <= request.arena_size <= RESEARCH_SCALE_MAX_ARENA_SIZE)
        ):
            raise EvaluationConfigurationError(
                f"Evaluation --arena-size {request.arena_size} is outside the "
                f"{request.resolved_rules_compatibility_id} evaluation methodology's supported "
                f"range [{RESEARCH_SCALE_MIN_ARENA_SIZE}, {RESEARCH_SCALE_MAX_ARENA_SIZE}]."
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

    def _scheduler_override(self, request: EvaluationRequest) -> dict[str, Any] | None:
        """The resolved scheduler research override, or ``None`` if unused.

        Gated on the same non-default condition ``match_service.
        _effective_ruleset_policy`` uses to decide whether to override a
        cell's ``RulesetPolicy`` at all: an ordinary evaluation (the
        override omitted, as every evaluation before it existed and every
        one since that does not opt in still is) resolves ``None`` here, so
        callers that fold this into an identity payload get a byte-identical
        payload and therefore an unchanged historical id (V6
        research-integrity hardening; mirrors ``match_service.
        canonical_match_id``'s identical gate at the single-match layer).
        """

        if request.scheduler_chunk_size is None and not request.scheduler_rotate_start:
            return None
        return {
            "chunk_size": request.scheduler_chunk_size,
            "rotate_start": request.scheduler_rotate_start,
        }

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
        resolved_is_v6_research_scale = is_ruleset_v6_research_scale_methodology(resolved_rules_id)
        resolved_is_v6_research_scale_move = is_ruleset_v6_research_scale_move_methodology(
            resolved_rules_id
        )
        resolved_group = request.group and resolved_is_v2
        identity_version = resolved_identity_version(
            resolved_is_v2,
            resolved_group,
            resolved_is_v4,
            resolved_is_v6_research_scale,
            resolved_is_v6_research_scale_move,
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
            elif (
                resolved_is_v4
                or resolved_is_v6_research_scale
                or resolved_is_v6_research_scale_move
            ):
                # v4.0.0-rc1 Phase 1 (research report Sec H.1 item 7): the
                # methodology's actual resolved *sample set* -- each seed's
                # resolved seat geometry -- enters the hash directly, the
                # exact same "placements" key the v2 branch above uses, so
                # two evaluations naming different seed sets (or whose
                # identical seed set resolves differently because arena
                # size differs) can never collide on evaluation_id, and two
                # evaluations at different sample counts (say seeds 1-8 vs
                # 1-16) share a prefix rather than colliding wholesale.
                #
                # V6 Phase 4B/4C: the variable-arena research Rulesets share
                # this exact branch -- `resolve_v4_seed_geometry` resolves
                # through `resolved_rules_id`'s own registered
                # `RulesetPolicy.core_placement`, so it already produces the
                # research Ruleset's correct seeded geometry at whatever
                # arena size this request specifies, with no separate
                # implementation needed.
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
                conditions, request.resolved_locality_reach, self._scheduler_override(request)
            ),
            rules_compatibility_id=resolved_rules_id,
            orientation_mode=request.orientation_mode,
            arena_alignment_mode=resolved_arena_alignment_mode(
                resolved_is_v2,
                resolved_group,
                resolved_is_v4,
                resolved_is_v6_research_scale,
                resolved_is_v6_research_scale_move,
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
