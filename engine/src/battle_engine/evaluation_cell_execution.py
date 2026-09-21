"""The canonical single-``EvaluationCell`` execution primitive (V6 Phase 3H).

One module owns the answer to exactly one question: *"execute this
already-planned evaluation cell exactly once."*  Coordinating a whole
evaluation -- matrix construction, resume decisions, checkpoint
persistence, execution-context deduplication, drift/failure policy -- is a
separate concern and stays in ``agent_evaluation.EvaluationService``.

Before this phase the implementation lived on ``EvaluationService.
_execute_cell``, which forced ``evaluation_worker`` (a subprocess that only
ever needs to run one cell) to import the whole service back -- a genuine
``EvaluationService`` <-> ``evaluation_worker`` cycle that the worker broke
with a function-local import and a throwaway ``EvaluationService()``
instance.  Both execution routes now call :func:`execute_cell` here
instead, so the cycle is gone and there is exactly one implementation of
what a cell *is*:

* serial dispatch -- ``EvaluationService.run`` calls :func:`execute_cell`;
* parallel dispatch -- ``evaluation_worker`` calls the same function inside
  a worker subprocess.

Nothing here reads coordinator state.  :func:`execute_cell` is pure apart
from filesystem I/O under ``cell.artifact_dir`` and reading agent source
under ``data_root``/the default data root, which is precisely what makes it
safe to run unchanged inside a worker process.  This module must therefore
never import ``agent_evaluation``, the CLI, Designer, evaluation history,
or any artifact/resume orchestration; it sits directly above
``evaluation_planning``/``evaluation_identity``/``evaluation_contracts``
and the low-level execution boundary ``agent_test.test_agent``.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from battle_engine.agent_api import AgentValidationError
from battle_engine.agent_test import (
    AgentTestError,
    InitializationFailureOutcome,
    test_agent,
)
from battle_engine.agents import AgentSpec, resolve_agent
from battle_engine.evaluation_contracts import (
    ORIENTATION_OPPONENT_FIRST,
    EvaluationCell,
    EvaluationConfigurationError,
    ExecutionContext,
    physical_slots_for_orientation,
    seat_label,
)
from battle_engine.evaluation_identity import agent_identity
from battle_engine.match_service import NativeMatchResult
from battle_engine.paths import get_data_root
from battle_engine.project_info import get_project_info
from battle_engine.result_model import stable_id
from battle_engine.results import WINNER_TIE_SENTINEL

__all__ = [
    "CellExecutionResult",
    "current_execution_context",
    "execute_cell",
]


# ---------------------------------------------------------------------------
# Execution environment / result envelope
# ---------------------------------------------------------------------------


def current_execution_context(rules_compatibility_id: str) -> ExecutionContext:
    project = get_project_info()
    payload: dict[str, Any] = {
        "bytefray_version": project.version,
        "agent_api_version": project.agent_api_version,
        "python_version": project.python_version,
        "result_schema_version": project.result_schema_version,
        "replay_schema_version": project.replay_schema_version,
        "rules_compatibility_id": rules_compatibility_id,
    }
    context_id = stable_id("evaluation-context", payload)
    return ExecutionContext(
        context_id=context_id,
        bytefray_version=project.version,
        agent_api_version=project.agent_api_version,
        python_version=project.python_version,
        result_schema_version=project.result_schema_version,
        replay_schema_version=project.replay_schema_version,
        rules_compatibility_id=rules_compatibility_id,
    )


@dataclass(frozen=True)
class CellExecutionResult:
    """:func:`execute_cell`'s return value (v1.6 Phase 2).

    ``execution_context`` is ``None`` only for the pre-execution-drift early
    return (no execution was attempted, so there is nothing to attribute to
    an environment) -- every other path sets it, mirroring exactly which
    paths called the old ``record_context_usage()`` closure. Replacing that
    closure (a coordinator-local mutable capture, unsafe to call from a
    worker process) with this explicit return value is what lets
    :func:`execute_cell` run unchanged inside a worker subprocess: the worker
    reports the context it observed, and only the coordinator (never a
    worker) decides whether it is new and appends it -- see
    ``agent_evaluation._register_execution_context`` (coordinator-owned,
    deliberately not part of this module).
    """

    cell: EvaluationCell
    execution_context: ExecutionContext | None = None


def _resolve_python_agent(root: Path, agent_id: str) -> AgentSpec:
    try:
        spec = resolve_agent(root, agent_id)
    except SystemExit as exc:
        raise EvaluationConfigurationError(f"Unknown agent {agent_id!r}: {exc}") from exc
    except AgentValidationError as exc:
        raise EvaluationConfigurationError(
            f"Agent {agent_id!r} manifest is invalid: {exc}"
        ) from exc
    if spec.kind != "python":
        raise EvaluationConfigurationError(
            f"Agent {agent_id!r} is kind {spec.kind!r}; evaluation requires Python "
            "agents only (see docs/specs/agent_evaluation.md Sec 17)."
        )
    if spec.api_version != 2:
        raise EvaluationConfigurationError(
            f"Agent {agent_id!r} declares Agent API v{spec.api_version}; new evaluations "
            "require Agent API v2. Historical evaluation artifacts remain readable."
        )
    return spec


# ---------------------------------------------------------------------------
# Identity drift cross-checks
# ---------------------------------------------------------------------------

# Identity fields recorded both in a frozen ``agent_identity()`` snapshot and
# in a real match's per-entrant ``NativeAgentResult.metadata`` (Python kind)
# -- the intersection usable to cross-check "what the executor actually
# loaded" against "what was planned" without re-reading disk a second time.
# ``entry_point``/``local_source_fingerprint`` (v0.7 closure pass, B1): the
# executor (``python_runtime``/``supervised_runtime``) now records both --
# the entry point string it actually resolved and imported from, and a
# fingerprint of every local ``.py`` file under the agent directory it
# actually loaded from, computed once at load time and never re-derived --
# so a same-file factory retarget (``agent.yaml`` entry point changed but
# the source file's own bytes untouched, which ``source_sha256`` alone
# cannot see) or a helper-file edit landing after this cell's pre-execution
# drift check but before/during the executor's own load is still caught
# here, against genuine executor evidence rather than a second live re-read.
_ACTUAL_IDENTITY_FIELDS = (
    "source_sha256",
    "api_version",
    "agent_version",
    "entry_point",
    "local_source_fingerprint",
)

# Lazy-import closure pass: the executor also records a *second*,
# independently computed ``local_source_fingerprint_final`` -- over the
# identical deterministic scope as ``local_source_fingerprint`` above, but
# taken only after the whole match has finished (every ``reset()``/
# ``act()`` call already happened). A local helper imported lazily from
# inside ``reset()``/``act()`` (rather than at module load time) can change
# the agent directory's contents after the load-time fingerprint was
# captured but before that lazy import actually executes; the load-time
# fingerprint alone cannot see this. Compared against the same *planned*
# ``local_source_fingerprint`` value as the load-time field -- there is
# only one planned value; both executor-recorded readings must agree with
# it (see ``_post_execution_identity_drift``'s three-way invariant).
_FINAL_ONLY_IDENTITY_FIELDS = (("local_source_fingerprint", "local_source_fingerprint_final"),)


def _post_execution_identity_drift(
    cell: EvaluationCell,
    match_result: NativeMatchResult,
    planned_identities: Mapping[str, dict[str, Any]],
) -> dict[str, Any] | None:
    """Cross-check the executor's own recorded entrant metadata against the frozen plan.

    Orientation-aware (Phase 5 spec Sec H.1): resolves which physical slot
    each role actually executed in via ``physical_slots_for_orientation``,
    rather than assuming subject=A/opponent=B -- for an ``opponent_first``
    cell the subject really executed in slot B and the opponent in slot A,
    and checking the wrong slot would silently compare each side's frozen
    identity against the other side's executed metadata.

    ``NativeAgentResult.metadata`` for a Python entrant is populated by
    ``python_runtime.PythonEntrantController``/``match_service.
    _build_python_result`` from the exact source the executor just loaded
    and ran -- it is not a second independent disk read performed by this
    module after the fact. Comparing it against ``planned_identities``
    (frozen once at preflight, before any cell executed) is therefore the
    strongest available check that the identity actually used for
    acceptance corresponds to what the executor actually loaded (Sec 7
    finding), and -- unlike recomputing ``canonical_match_id`` from a live
    ``AgentSpec.source_path`` after execution -- cannot be silently
    defeated by a source edit that is already in place by the time this
    check runs.

    The required invariant (v0.7 closure pass, lazy-import fix) is now
    three-way, not two-way::

        initial executor fingerprint == frozen planned fingerprint == final executor fingerprint

    i.e. both ``local_source_fingerprint`` (captured at load time, before
    ``reset()``/``act()`` ever run) *and* ``local_source_fingerprint_final``
    (captured after the match finishes, so every lazy import a running
    agent performed has already happened) must each independently equal
    the frozen plan's single recorded value. A local helper imported
    lazily from inside ``reset()``/``act()`` -- rather than at module load
    time -- can change between those two executor-recorded readings; the
    load-time fingerprint alone cannot see that, since the lazy import
    that actually reads the changed file has not happened yet when it is
    captured.

    A residual TOCTOU remains and is documented rather than hidden: inside
    ``python_runtime.PythonEntrantController.__init__`` (and its supervised
    counterpart), the agent module is loaded/executed first and its
    ``source_sha256``/``local_source_fingerprint`` are each computed by a
    *separate* subsequent read (see ``PythonEntrantState.source_digest``/
    ``PythonEntrantState.local_source_fingerprint``); symmetrically, the
    final fingerprint is computed once, in a separate step, after the tick
    loop's last actual local-file read. An edit that lands and is then
    reverted before the nearest such read captures it -- at either end --
    is not detectable from outside that call. This module neither
    introduces nor can close that inner window; it only guarantees that
    whatever the executor itself recorded as having run, at both points,
    is cross-checked against the frozen plan.
    """

    subject_slot, opponent_slot = physical_slots_for_orientation(cell.orientation)
    for role, agent_id, slot in (
        (cell.subject_role, cell.subject_id, subject_slot),
        ("opponent", cell.opponent_id, opponent_slot),
    ):
        planned = planned_identities.get(agent_id)
        if planned is None:
            continue
        agent_result = match_result.agents_by_id.get(slot)
        if agent_result is None:
            continue
        actual_metadata = agent_result.metadata
        mismatched = sorted(
            field
            for field in _ACTUAL_IDENTITY_FIELDS
            if planned.get(field) != actual_metadata.get(field)
        )
        mismatched.extend(
            actual_field
            for planned_field, actual_field in _FINAL_ONLY_IDENTITY_FIELDS
            if planned.get(planned_field) != actual_metadata.get(actual_field)
        )
        mismatched.sort()
        if mismatched:
            return {
                "error_code": "post_execution_identity_drift",
                "error_message": (
                    f"{role} {agent_id!r} executed identity does not match the "
                    f"frozen plan (fields: {', '.join(mismatched)}); agent source "
                    "or configuration changed during execution."
                )[:240],
            }
    return None


def _post_execution_identity_drift_group(
    cell: EvaluationCell,
    match_result: NativeMatchResult,
    planned_identities: Mapping[str, dict[str, Any]],
) -> dict[str, Any] | None:
    """The multi-entrant (N seats) generalization of
    :func:`_post_execution_identity_drift` (v2.0.0-beta2 Phase 2).

    Seat *is* physical slot for a group cell (``seat_label(i)`` is
    literally the ``MatchEntrant.agent_id`` each seat executed as -- see
    ``EvaluationSeatAssignment``), so there is no orientation-style
    slot-resolution step here: seat index directly indexes both
    ``cell.seat_agent_ids`` and ``match_result.agents_by_id``.
    """

    for index, agent_id in enumerate(cell.seat_agent_ids):
        planned = planned_identities.get(agent_id)
        if planned is None:
            continue
        agent_result = match_result.agents_by_id.get(seat_label(index))
        if agent_result is None:
            continue
        actual_metadata = agent_result.metadata
        mismatched = sorted(
            field
            for field in _ACTUAL_IDENTITY_FIELDS
            if planned.get(field) != actual_metadata.get(field)
        )
        mismatched.extend(
            actual_field
            for planned_field, actual_field in _FINAL_ONLY_IDENTITY_FIELDS
            if planned.get(planned_field) != actual_metadata.get(actual_field)
        )
        mismatched.sort()
        if mismatched:
            return {
                "error_code": "post_execution_identity_drift",
                "error_message": (
                    f"seat {seat_label(index)} {agent_id!r} executed identity does not "
                    f"match the frozen plan (fields: {', '.join(mismatched)}); agent "
                    "source or configuration changed during execution."
                )[:240],
            }
    return None


def _detect_pre_execution_drift(
    cell: EvaluationCell,
    planned_identities: Mapping[str, dict[str, Any]],
    root: Path,
) -> dict[str, Any] | None:
    """Sec 7 pre-check: re-resolve and compare against the *frozen* plan.

    ``planned_identities`` must be a snapshot captured once at preflight
    time (never re-derived from a live ``AgentSpec.source_path``) -- both
    sides of this comparison reading the same evolving file would
    silently defeat drift detection. Catches a source/identity change
    between preflight and this specific cell's execution --
    ``agent_test.test_agent`` re-resolves both agents itself, so nothing
    else in this codepath would otherwise notice.
    """

    # v2.0.0-beta2 Phase 2: a group cell's `opponent_id` is a joined
    # display label (see EvaluationCell's own docstring), never a real
    # agent id -- resolving it would always fail. Check the real
    # per-seat roster instead; `dict.fromkeys` dedupes a repeated agent
    # id (self-play) so it is checked once, not once per occupied seat.
    role_and_agent_ids: tuple[tuple[str, str], ...] = (
        tuple(("roster", agent_id) for agent_id in dict.fromkeys(cell.seat_agent_ids))
        if cell.is_group
        else ((cell.subject_role, cell.subject_id), ("opponent", cell.opponent_id))
    )
    for role, agent_id in role_and_agent_ids:
        planned_identity = planned_identities.get(agent_id)
        if planned_identity is None:
            continue
        try:
            current = _resolve_python_agent(root, agent_id)
        except EvaluationConfigurationError as exc:
            return {
                "error_code": "pre_execution_agent_unresolvable",
                "error_message": f"{role} {agent_id!r} no longer resolves: {exc}"[:240],
            }
        current_identity = agent_identity(current)
        if planned_identity != current_identity:
            changed = sorted(
                key
                for key in planned_identity
                if planned_identity[key] != current_identity[key]
            )
            return {
                "error_code": "pre_execution_source_drift",
                "error_message": (
                    f"{role} {agent_id!r} identity changed since preflight "
                    f"(fields: {', '.join(changed)})."
                )[:240],
            }
    return None


# ---------------------------------------------------------------------------
# Result mapping
# ---------------------------------------------------------------------------

def _cell_from_match_result(cell: EvaluationCell, match_result: NativeMatchResult) -> EvaluationCell:
    """Resolve outcome/score/territory from the correct physical slot for ``cell.orientation``.

    Every stored field is expressed from the evaluation-role (subject/
    opponent) perspective regardless of which physical slot actually
    executed each role (Phase 5 spec Sec H.1/Sec 12) -- see
    :func:`physical_slots_for_orientation`.
    """

    subject_slot, opponent_slot = physical_slots_for_orientation(cell.orientation)
    winner = match_result.winner
    outcome = (
        "tie"
        if winner == WINNER_TIE_SENTINEL
        else "win"
        if winner == subject_slot
        else "loss"
    )
    agents_by_id = match_result.agents_by_id
    subject_agent = agents_by_id.get(subject_slot)
    opponent_agent = agents_by_id.get(opponent_slot)
    return replace(
        cell,
        status="completed",
        outcome=outcome,
        match_id=match_result.match_id,
        result_id=match_result.result_id,
        ticks_run=match_result.ticks_run,
        score_subject=float(match_result.score.get(subject_slot, 0)),
        score_opponent=float(match_result.score.get(opponent_slot, 0)),
        territory_subject=(subject_agent.territory_pct_last if subject_agent else None),
        territory_opponent=(opponent_agent.territory_pct_last if opponent_agent else None),
        error_code=None,
        error_message=None,
    )


# ---------------------------------------------------------------------------
# The canonical per-cell executor
# ---------------------------------------------------------------------------

def execute_cell(
    cell: EvaluationCell,
    ticks: int,
    data_root: Path | None,
    planned_identities: Mapping[str, dict[str, Any]],
    arena_size: int | None = None,
    instr_per_tick: int | None = None,
    locality_reach: int | None = None,
    kill_weight: float | None = None,
    scheduler_chunk_size: int | None = None,
    scheduler_rotate_start: bool = False,
) -> CellExecutionResult:
    """Execute one cell. Pure apart from filesystem I/O under ``cell.artifact_
    dir`` and reading agent source under ``data_root``/the default data
    root -- no coordinator state is read or mutated, which is exactly what
    lets this run unchanged inside a worker subprocess (v1.6 Phase 2).

    Takes ``ticks``/``data_root`` directly rather than a whole
    ``EvaluationRequest`` -- these are the only two fields this function
    ever reads; narrowing the signature means a worker process can never
    accidentally gain access to a coordinator-only field (``resume``,
    ``retry_failures``, ``workers``, ...) that has no valid meaning
    per-cell.

    v3 Phase 0D adds ``arena_size``/``instr_per_tick`` as two more
    explicit scalar arguments of exactly the same kind as ``ticks``:
    evaluation-wide execution conditions that are constant across a
    matrix but must be transported explicitly into a worker subprocess.
    They are deliberately NOT stored on ``EvaluationCell`` -- doing so
    would change the persisted cell shape for every historical artifact
    while expressing an evaluation-wide fact per cell. ``None`` keeps
    the executor's own historical default (see ``agent_test``).
    """

    root = data_root or get_data_root()
    drift = _detect_pre_execution_drift(cell, planned_identities, root)
    if drift is not None:
        return CellExecutionResult(cell=replace(cell, status="drift_detected", **drift))

    # Persisted group cells remain readable/resumable, but Scope C
    # retired their Ruleset and therefore their new execution path.
    if cell.is_group:
        raise EvaluationConfigurationError(
            "Multi-entrant evaluation execution is retired; historical cells are read-only."
        )

    # v0.9 Phase 6 (Phase 5 spec Sec H.1/T.4): `candidate_first` reuses
    # the exact historical call; `opponent_first` calls the same
    # unmodified executor with the two positional roles swapped --
    # this alone is the entire "opposite entrant orientation"
    # mechanism, no scheduler/executor change. Every subsequent
    # mapping in this function resolves physical slot <-> evaluation
    # role via `physical_slots_for_orientation`, never by assuming
    # subject==A/opponent==B.
    # v2.0.0-beta2 Phase 1 (design doc Sec Placement/Sec J): placement
    # describes *where the subject/opponent start*, independent of
    # which physical slot/scheduler order executes each role -- the
    # subject always starts at `cell.subject_start` regardless of
    # orientation, exactly like every other subject/opponent-role field
    # this function already resolves through orientation rather than
    # assuming subject==A/opponent==B.
    if cell.orientation == ORIENTATION_OPPONENT_FIRST:
        test_agent_id, test_opponent_id = cell.opponent_id, cell.subject_id
        test_agent_start, test_opponent_start = cell.opponent_start, cell.subject_start
    else:
        test_agent_id, test_opponent_id = cell.subject_id, cell.opponent_id
        test_agent_start, test_opponent_start = cell.subject_start, cell.opponent_start

    # Computed once here, after the pre-execution-drift early return
    # (which must keep making zero calls, matching the old closure's
    # exact behavior) -- current_execution_context() is a pure function
    # of environment (and this cell's own resolved Ruleset) only, so
    # every remaining branch below reuses this same value rather than
    # recomputing it. Reads `cell.rules_compatibility_id`, never the
    # module constant, so a v2 cell's execution context correctly
    # records "bytefray-rules-2" -- this function must stay a pure
    # function of its own arguments for v1.6 Phase 2 worker-subprocess
    # purity, so this cannot read `EvaluationRequest.ruleset_id`
    # directly.
    context = current_execution_context(cell.rules_compatibility_id)

    try:
        outcome = test_agent(
            test_agent_id,
            opponent=test_opponent_id,
            seed=cell.seed,
            ticks=ticks,
            timeout=None,
            trace=False,
            run_dir=cell.artifact_dir,
            data_root=data_root,
            ruleset_id=cell.rules_compatibility_id,
            agent_start=test_agent_start,
            opponent_start=test_opponent_start,
            arena_size=arena_size,
            instr_per_tick=instr_per_tick,
            locality_reach=locality_reach,
            kill_weight=kill_weight,
            scheduler_chunk_size=scheduler_chunk_size,
            scheduler_rotate_start=scheduler_rotate_start,
        )

    except AgentTestError as exc:
        return CellExecutionResult(
            cell=replace(
                cell,
                status="failed",
                outcome=None,
                error_code=exc.diagnostic.code,
                error_message=" ".join(str(exc).split())[:240],
                execution_context_id=context.context_id,
            ),
            execution_context=context,
        )
    if isinstance(outcome, InitializationFailureOutcome):
        # A ``RuntimeDiagnostic`` carries no source/version identity
        # fields (see ``python_runtime.RuntimeDiagnostic``), so unlike a
        # completed match there is no executor-recorded ground truth to
        # cross-check here. A live re-resolve against the frozen plan is
        # the only signal available -- it cannot detect an edit that
        # lands and then reverts before this point (the same documented
        # residual as ``_post_execution_identity_drift``), but it does
        # catch a durable edit that caused the observed initialization
        # failure, preventing that failure from being silently
        # attributed to the original, frozen agent (Sec 7 "initialization
        # failure after intervening source change").
        post_init_drift = _detect_pre_execution_drift(cell, planned_identities, root)
        if post_init_drift is not None:
            return CellExecutionResult(
                cell=replace(
                    cell,
                    status="drift_detected",
                    **post_init_drift,
                    execution_context_id=context.context_id,
                ),
                execution_context=context,
            )
        failed_slot = outcome.diagnostic.agent_id
        subject_slot, _opponent_slot = physical_slots_for_orientation(cell.orientation)
        result_outcome = (
            "subject_init_failed" if failed_slot == subject_slot else "opponent_init_failed"
        )
        return CellExecutionResult(
            cell=replace(
                cell,
                status="completed",
                outcome=result_outcome,
                error_code=outcome.diagnostic.code,
                error_message=" ".join(outcome.diagnostic.message.split())[:240],
                execution_context_id=context.context_id,
            ),
            execution_context=context,
        )
    post_drift = _post_execution_identity_drift(cell, outcome.match_result, planned_identities)
    if post_drift is not None:
        return CellExecutionResult(
            cell=replace(
                cell,
                status="drift_detected",
                **post_drift,
                execution_context_id=context.context_id,
            ),
            execution_context=context,
        )
    return CellExecutionResult(
        cell=replace(
            _cell_from_match_result(cell, outcome.match_result),
            execution_context_id=context.context_id,
        ),
        execution_context=context,
    )
