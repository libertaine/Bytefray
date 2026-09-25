"""The canonical owner of evaluation artifact persistence and resume trust
(V6 Phase 3I).

One module answers exactly one question: *"how is a live evaluation's state
persisted, trusted, and resumed?"*  Deciding **when** to load, checkpoint,
resume, or finalize stays with ``agent_evaluation.EvaluationService`` -- the
coordinator owns policy, this module owns the mechanics and the trust rules.

Before this phase the implementation was spread across four
``EvaluationService`` methods (``_load_state``, ``_write_state``,
``_resolve_from_state``, ``_resolve_revision_results``) and a handful of
module-level helpers in ``agent_evaluation``, so nothing about resume trust
could be read or tested without constructing the whole service.  Everything
here is a plain function over explicit arguments: not one of those four
methods ever touched ``self``, which is precisely why they could move
without any behavior change at all.

Scope boundaries this module deliberately keeps:

* ``evaluation_history`` owns reading and adapting *completed historical*
  artifacts under their own read-compatibility rules; this module owns
  *live/current* evaluation persistence and resume.  They share contracts
  and identity helpers, never each other's trust rules.
* ``evaluation_cell_execution`` owns executing one cell.  Nothing here ever
  runs a match; it only verifies the evidence a completed cell left behind.
* ``evaluation_planning``/``evaluation_identity``/``evaluation_contracts``
  own the matrix, geometry, and identity vocabulary this module reconstructs
  against.

Resume trust is security-sensitive.  A persisted ``completed`` cell is never
deserialized on faith: :func:`resolve_cell_from_state` re-reads the cell's
own ``result.json``, re-derives the ``match_id`` that exact (subject,
opponent, seed, orientation, Ruleset, geometry) combination would produce
today, and :func:`resumed_cell_mismatch` re-verifies the nested replay's
containment, digest, and header identity before any of that evidence is
reused.  This module is a verifier of persisted evidence, not a
deserializer.

It must therefore never import ``agent_evaluation``, ``EvaluationService``,
the CLI, the Designer, or ``evaluation_worker``; ``agent_evaluation``
imports *it*.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from battle_engine.agent_revisions import (
    RevisionArchivalResult,
    agent_revisions_root,
    archive_agent_revision_from_walk,
    local_python_subset_fingerprint,
    walk_agent_files,
)
from battle_engine.agent_test import OPPONENT_SLOT, TESTED_AGENT_SLOT, _resolve_default_parameters
from battle_engine.agents import AgentSpec
from battle_engine.config import Config
from battle_engine.evaluation_contracts import (
    LIFECYCLE_STATE_FINISHED,
    ORIENTATION_OPPONENT_FIRST,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    SCHEMA_VERSION_V2,
    SCHEMA_VERSION_V2_GROUP,
    SCHEMA_VERSION_V4,
    ComparisonEntry,
    EffectiveConditions,
    EvaluationCell,
    EvaluationConfigurationError,
    EvaluationRequest,
    SubjectAggregate,
    is_ruleset_v2_methodology,
    is_ruleset_v4_methodology,
    is_ruleset_v6_research_capture_hold_disruption_slot_anchor_before_core_methodology,
    is_ruleset_v6_research_capture_hold_disruption_slot_methodology,
    is_ruleset_v6_research_capture_hold_disruption_slot_mirrored_passes_methodology,
    is_ruleset_v6_research_capture_hold_methodology,
    is_ruleset_v6_research_disruption_slot_anchor_before_core_methodology,
    is_ruleset_v6_research_disruption_slot_methodology,
    is_ruleset_v6_research_disruption_slot_mirrored_passes_methodology,
    is_ruleset_v6_research_scale_methodology,
    is_ruleset_v6_research_scale_move_methodology,
    is_ruleset_v6_research_scale_move_proportional_methodology,
    physical_slots_for_orientation,
    resolved_identity_version,
    resolved_schema_version,
    seat_label,
)
from battle_engine.evaluation_identity import (
    effective_conditions_fingerprint,
    effective_conditions_payload,
)
from battle_engine.match_service import MatchEntrant, MatchRequest, canonical_match_id
from battle_engine.paths import contained_path, get_data_root
from battle_engine.project_info import get_project_info
from battle_engine.replay import ReplayHeader, iter_replay
from battle_engine.result_model import (
    ReplayIntegrityError,
    ResultEnvelope,
    read_result,
    verify_replay_digest,
    write_json_atomic,
)
from battle_engine.results import WINNER_TIE_SENTINEL

__all__ = [
    "RevisionPlanEntry",
    "checkpoint_cells",
    "expected_cell_match_id",
    "expected_group_cell_match_id",
    "load_evaluation_state",
    "prior_revision_by_agent_id",
    "read_evaluation",
    "resolve_cell_from_state",
    "resolve_revision_results",
    "resumed_cell_mismatch",
    "utc_now_iso",
    "write_evaluation_state",
]

# The persisted cell statuses a resume may reconstruct from prior state at
# all.  Any other status (or an absent cell) is re-executed.
_TERMINAL_RESUME_STATUSES = ("completed", "failed", "corrupted", "drift_detected")


# ---------------------------------------------------------------------------
# Artifact timestamps
# ---------------------------------------------------------------------------


def utc_now_iso() -> str:
    """Precise UTC timestamp: microsecond precision, ``Z`` suffix (Sec 5)."""

    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="microseconds")
        .replace("+00:00", "Z")
    )


# ---------------------------------------------------------------------------
# Expected match identity reconstruction
# ---------------------------------------------------------------------------


def expected_cell_match_id(
    subject_spec: AgentSpec,
    subject_id: str,
    opponent_spec: AgentSpec,
    opponent_id: str,
    seed: int,
    ticks: int,
    orientation: str,
    ruleset_id: str,
    subject_start: int,
    opponent_start: int,
    arena_size: int | None = None,
    instr_per_tick: int | None = None,
    locality_reach: int | None = None,
    kill_weight: float | None = None,
) -> str:
    """Recompute the ``match_id`` a fresh cell run would produce.

    Mirrors ``agent_test._test_agent``'s own ``MatchRequest`` construction
    exactly (same ``Config(seed=...)``, same physical A/B slot entrants,
    ``orientation``-mapped via :func:`physical_slots_for_orientation`) so a
    *resumed* cell's recorded ``match_id`` can be verified against what this
    exact (subject, opponent, seed, orientation) combination would compute
    today -- catching a source-content change the way
    ``tournament_service``'s resume verification already does
    (docs/specs/agent_evaluation.md Sec 14).

    ``canonical_match_id`` reads ``spec.source_path`` from disk at call
    time (see ``match_service.canonical_match_id``), so this helper is only
    safe to use against *live, freshly re-resolved* specs (resume, where
    ``specs`` is this run's own current resolution and is already
    consistent with this run's freshly computed ``evaluation_id``). It must
    never be used to verify a cell just executed in *this* process against
    a frozen preflight snapshot -- a second live read after the fact can
    silently observe the same (already-drifted) content the executor itself
    just read, making the comparison pass despite drift. See
    ``evaluation_cell_execution._post_execution_identity_drift`` for that
    check instead.

    Phase 7 correctness fix: ``canonical_match_id`` is sensitive to the
    *positional order* of ``request.entrants`` -- both each Python entrant's
    derived seed (keyed by ``enumerate()`` position, not the "A"/"B" slot
    label) and the recorded ``entrant_order`` list depend on it
    (``match_service.canonical_match_id``). ``_test_agent`` always
    constructs its entrants tuple as ``(TESTED_AGENT_SLOT-entrant,
    OPPONENT_SLOT-entrant)`` positionally -- slot A's entrant always comes
    first in the tuple, slot B's always second, regardless of which logical
    role (subject/opponent) occupies which slot. This helper must build the
    identical positional order (always ``TESTED_AGENT_SLOT`` first,
    ``OPPONENT_SLOT`` second), with only *which agent* fills each slot
    varying by orientation -- not a "subject first, opponent second" order,
    which silently recomputes a different id than a real ``opponent_first``
    execution actually produced. Previously this caught every
    already-completed ``opponent_first`` cell in a false
    ``resumed_result_mismatch`` on every subsequent resume, even when
    nothing about the match had changed.
    """

    if orientation == ORIENTATION_OPPONENT_FIRST:
        slot_a_agent_id, slot_a_spec, slot_a_start = opponent_id, opponent_spec, opponent_start
        slot_b_agent_id, slot_b_spec, slot_b_start = subject_id, subject_spec, subject_start
    else:
        slot_a_agent_id, slot_a_spec, slot_a_start = subject_id, subject_spec, subject_start
        slot_b_agent_id, slot_b_spec, slot_b_start = opponent_id, opponent_spec, opponent_start
    _config_defaults = Config()
    request = MatchRequest(
        # v3 Phase 0D: mirrors `_test_agent`'s own `None`-means-default
        # `Config` construction exactly -- an omitted pair reproduces the
        # identical `Config(seed=...)` (and therefore the identical
        # `canonical_match_id`) every historical resume already verified
        # against. v3 Phase 3 extends this to `weights.kill` the same way.
        config=Config(
            seed=seed,
            arena_size=_config_defaults.arena_size if arena_size is None else arena_size,
            instr_per_tick=(
                _config_defaults.instr_per_tick if instr_per_tick is None else instr_per_tick
            ),
            weights=(
                _config_defaults.weights
                if kill_weight is None
                else replace(_config_defaults.weights, kill=kill_weight)
            ),
        ),
        entrants=(
            MatchEntrant.python(
                TESTED_AGENT_SLOT,
                slot_a_agent_id,
                slot_a_start,
                slot_a_spec,
                _resolve_default_parameters(slot_a_spec, role="entrant A"),
            ),
            MatchEntrant.python(
                OPPONENT_SLOT,
                slot_b_agent_id,
                slot_b_start,
                slot_b_spec,
                _resolve_default_parameters(slot_b_spec, role="entrant B"),
            ),
        ),
        max_ticks=ticks,
        replay_path=Path("."),
        ruleset_id=ruleset_id,
        locality_reach=locality_reach,
    )
    return canonical_match_id(request)


def expected_group_cell_match_id(
    specs: Mapping[str, AgentSpec],
    seat_agent_ids: Sequence[str],
    seat_starts: Sequence[int],
    seed: int,
    ticks: int,
    ruleset_id: str,
    arena_size: int | None = None,
    instr_per_tick: int | None = None,
    locality_reach: int | None = None,
    kill_weight: float | None = None,
) -> str:
    """The multi-entrant generalization of :func:`expected_cell_match_id`.

    Mirrors ``agent_test._test_agents``'s own ``MatchRequest`` construction
    exactly: entrants in seat order (``seat_agent_ids[i]`` at
    ``seat_label(i)``), each at its own ``seat_starts[i]``. See
    ``expected_cell_match_id``'s own docstring for why entrant *positional*
    order (not just each entrant's own identity) is load-bearing for
    ``canonical_match_id`` and must be reproduced exactly.
    """

    _config_defaults = Config()
    request = MatchRequest(
        # v3 Phase 0D: same `None`-means-default contract as
        # `expected_cell_match_id` above. v3 Phase 3 extends this to
        # `weights.kill` the same way.
        config=Config(
            seed=seed,
            arena_size=_config_defaults.arena_size if arena_size is None else arena_size,
            instr_per_tick=(
                _config_defaults.instr_per_tick if instr_per_tick is None else instr_per_tick
            ),
            weights=(
                _config_defaults.weights
                if kill_weight is None
                else replace(_config_defaults.weights, kill=kill_weight)
            ),
        ),
        entrants=tuple(
            MatchEntrant.python(
                seat_label(index),
                agent_id,
                start,
                specs[agent_id],
                _resolve_default_parameters(
                    specs[agent_id], role=f"entrant {seat_label(index)}"
                ),
            )
            for index, (agent_id, start) in enumerate(zip(seat_agent_ids, seat_starts, strict=True))
        ),
        max_ticks=ticks,
        replay_path=Path("."),
        ruleset_id=ruleset_id,
        locality_reach=locality_reach,
    )
    return canonical_match_id(request)


# ---------------------------------------------------------------------------
# Persisted cell reconstruction
# ---------------------------------------------------------------------------


def _cell_from_state(cell: EvaluationCell, previous: Mapping[str, Any]) -> EvaluationCell:
    return replace(
        cell,
        status=previous.get("status", cell.status),
        outcome=previous.get("outcome"),
        match_id=previous.get("match_id"),
        result_id=previous.get("result_id"),
        ticks_run=previous.get("ticks_run"),
        score_subject=previous.get("score_subject"),
        score_opponent=previous.get("score_opponent"),
        territory_subject=previous.get("territory_subject"),
        territory_opponent=previous.get("territory_opponent"),
        error_code=previous.get("error_code"),
        error_message=previous.get("error_message"),
        # A resumed cell's own execution provenance is preserved verbatim --
        # never rewritten to the resuming process's context (Sec 5/Sec 6).
        execution_context_id=previous.get("execution_context_id"),
    )


def _cell_from_envelope(cell: EvaluationCell, envelope: ResultEnvelope) -> EvaluationCell:
    """Envelope-based mirror of
    :func:`battle_engine.evaluation_cell_execution._cell_from_match_result`
    (resume path).
    """

    subject_slot, opponent_slot = physical_slots_for_orientation(cell.orientation)
    winner = envelope.winner
    outcome = (
        "tie"
        if winner == WINNER_TIE_SENTINEL
        else "win"
        if winner == subject_slot
        else "loss"
    )
    subject_entrant = next(
        (entry for entry in envelope.entrants if entry.get("agent_id") == subject_slot), {}
    )
    opponent_entrant = next(
        (entry for entry in envelope.entrants if entry.get("agent_id") == opponent_slot), {}
    )
    subject_stats = subject_entrant.get("statistics", {}) or {}
    opponent_stats = opponent_entrant.get("statistics", {}) or {}
    return replace(
        cell,
        status="completed",
        outcome=outcome,
        match_id=envelope.match_id,
        result_id=envelope.result_id,
        ticks_run=envelope.ticks,
        score_subject=float(envelope.score.get(subject_slot, 0)),
        score_opponent=float(envelope.score.get(opponent_slot, 0)),
        territory_subject=subject_stats.get("territory_pct_last"),
        territory_opponent=opponent_stats.get("territory_pct_last"),
        error_code=None,
        error_message=None,
    )


def _cell_from_envelope_group(cell: EvaluationCell, envelope: ResultEnvelope) -> EvaluationCell:
    """Envelope-based mirror of
    :func:`battle_engine.agent_evaluation._cell_from_match_result_group`
    (resume path).
    """

    subject_slot = cell.subject_seat
    winner = envelope.winner
    outcome = (
        "tie"
        if winner == WINNER_TIE_SENTINEL
        else "win"
        if winner == subject_slot
        else "loss"
    )
    subject_entrant = next(
        (entry for entry in envelope.entrants if entry.get("agent_id") == subject_slot), {}
    )
    subject_stats = subject_entrant.get("statistics", {}) or {}
    return replace(
        cell,
        status="completed",
        outcome=outcome,
        match_id=envelope.match_id,
        result_id=envelope.result_id,
        ticks_run=envelope.ticks,
        score_subject=float(envelope.score.get(subject_slot, 0)) if subject_slot else None,
        territory_subject=subject_stats.get("territory_pct_last"),
        error_code=None,
        error_message=None,
    )


# ---------------------------------------------------------------------------
# Resumed-cell trust verification
# ---------------------------------------------------------------------------


def resumed_cell_mismatch(
    envelope: ResultEnvelope, cell: EvaluationCell, expected_match_id: str
) -> str | None:
    """Sec 14: adapted from ``tournament_service._resumed_result_mismatch``."""

    entrant_order = tuple(str(entry.get("agent_id")) for entry in envelope.entrants)
    # v2.0.0-beta2 Phase 2: a group cell's expected physical slot order is
    # seat_label(0..N-1) -- N seats, not the fixed 2-entrant (A, B) pair.
    expected_order = (
        tuple(seat_label(index) for index in range(len(cell.seat_agent_ids)))
        if cell.is_group
        else (TESTED_AGENT_SLOT, OPPONENT_SLOT)
    )
    if entrant_order != expected_order:
        return f"entrant order {entrant_order} does not match expected {expected_order}"
    actual_seed = envelope.reproducibility.get("seed")
    if actual_seed != cell.seed:
        return f"seed {actual_seed!r} does not match the scheduled cell's {cell.seed!r}"
    if envelope.match_id != expected_match_id:
        return (
            f"match ID {envelope.match_id!r} does not match the scheduled cell's "
            f"expected ID {expected_match_id!r}"
        )
    if envelope.replay is None:
        return "result has no replay reference, but a native Python match result always has one"
    # H5: the replay filename comes from a persisted result.json this
    # module does not control -- resolve it through the same containment
    # discipline as any other nested artifact path (M4) rather than a bare
    # join, which a `../`, absolute, or symlink-escaping filename could
    # otherwise walk outside the cell's own artifact directory.
    replay_path = contained_path(cell.artifact_dir, envelope.replay.filename)
    if replay_path is None:
        return (
            f"result replay filename {envelope.replay.filename!r} escapes the "
            "cell's artifact directory"
        )
    try:
        verify_replay_digest(envelope, replay_path)
        header = next(
            (record for record in iter_replay(replay_path) if isinstance(record, ReplayHeader)),
            None,
        )
    except ReplayIntegrityError as exc:
        return f"replay verification failed ({exc.code}): {exc}"
    except (OSError, ValueError) as exc:
        return f"replay header could not be read: {exc}"
    if header is None:
        return "replay has no header"
    if header.match_id != envelope.match_id:
        return "replay header match ID does not match result envelope"
    if header.result_id != envelope.result_id:
        return "replay header result ID does not match result envelope"
    if header.ruleset_id != envelope.ruleset_id:
        return (
            f"replay header ruleset_id {header.ruleset_id!r} does not match "
            f"result envelope ruleset_id {envelope.ruleset_id!r}"
        )
    return None


def resolve_cell_from_state(
    cell: EvaluationCell,
    previous: Mapping[str, Any],
    specs: dict[str, AgentSpec],
    request: EvaluationRequest,
) -> EvaluationCell | None:
    """Reconstruct one persisted cell, or ``None`` to re-execute it.

    The single place resume decides whether a cell already on disk may be
    trusted.  A persisted ``completed`` cell that actually scored a match
    is never taken on faith: its own ``result.json`` is re-read, the
    ``match_id`` this exact (subject, opponent, seed, orientation,
    Ruleset, geometry) combination would produce *today* is recomputed
    (:func:`expected_cell_match_id`/:func:`expected_group_cell_match_id`),
    and the nested replay evidence is re-verified
    (:func:`resumed_cell_mismatch`) before anything is reused.  Any failure
    downgrades the cell to ``corrupted`` with a specific ``error_code``
    rather than silently re-running or silently accepting it.

    A recorded initialization failure (``subject_init_failed``/
    ``opponent_init_failed``) is reusable verbatim -- it never produced a
    ``result.json`` to verify in the first place.  ``failed``/
    ``corrupted``/``drift_detected`` are reconstructed verbatim too; which
    of them the coordinator then chooses to retry is *its* policy
    (``request.retry_failures``), deliberately not decided here.
    """

    status = previous.get("status")
    if status not in _TERMINAL_RESUME_STATUSES:
        return None
    if status != "completed":
        return _cell_from_state(cell, previous)

    outcome = previous.get("outcome")
    if outcome in ("subject_init_failed", "opponent_init_failed"):
        return _cell_from_state(cell, previous)

    result_path = cell.artifact_dir / "result.json"
    if not result_path.is_file():
        return replace(
            _cell_from_state(cell, previous),
            status="corrupted",
            error_code="resumed_result_missing",
            error_message="Recorded completed cell has no result.json to verify.",
        )
    try:
        envelope = read_result(result_path)
    except (OSError, ValueError, KeyError) as exc:
        return replace(
            _cell_from_state(cell, previous),
            status="corrupted",
            error_code="resumed_result_unreadable",
            error_message=f"result.json could not be read: {exc}"[:240],
        )

    if cell.is_group:
        expected_match_id = expected_group_cell_match_id(
            specs,
            cell.seat_agent_ids,
            cell.seat_starts,
            cell.seed,
            request.ticks,
            cell.rules_compatibility_id,
            arena_size=request.arena_size,
            instr_per_tick=request.instr_per_tick,
            locality_reach=request.resolved_locality_reach,
            kill_weight=request.kill_weight,
        )
    else:
        expected_match_id = expected_cell_match_id(
            specs[cell.subject_id],
            cell.subject_id,
            specs[cell.opponent_id],
            cell.opponent_id,
            cell.seed,
            request.ticks,
            cell.orientation,
            cell.rules_compatibility_id,
            cell.subject_start,
            cell.opponent_start,
            arena_size=request.resolved_arena_size,
            instr_per_tick=request.instr_per_tick,
            locality_reach=request.resolved_locality_reach,
            kill_weight=request.kill_weight,
        )
    mismatch = resumed_cell_mismatch(envelope, cell, expected_match_id)
    if mismatch is not None:
        return replace(
            _cell_from_state(cell, previous),
            status="corrupted",
            error_code="resumed_result_mismatch",
            error_message=mismatch[:240],
        )
    resolved = _cell_from_envelope_group(cell, envelope) if cell.is_group else _cell_from_envelope(cell, envelope)
    return replace(
        resolved,
        execution_context_id=previous.get("execution_context_id"),
    )


# ---------------------------------------------------------------------------
# Checkpoint merge and canonical matrix ordering
# ---------------------------------------------------------------------------


def checkpoint_cells(
    completed_by_schedule_id: Mapping[str, EvaluationCell],
    matrix: Sequence[EvaluationCell],
    prior_cells: Mapping[str, Any],
) -> list[EvaluationCell]:
    """B2: a checkpoint must never be less complete than the durable state
    already on disk.

    ``completed_by_schedule_id`` covers only the cells resolved or executed
    *so far* -- during a retry, that is strictly less than every cell a
    *prior* run already durably persisted (e.g. seed 2 completed in an
    earlier run, then seed 1 is retried in this one; the map after seed 1's
    retry contains only seed 1). Writing it verbatim as a mid-run checkpoint
    would silently drop every already-durable cell not yet reached.

    This backfills exactly those cells: any matrix cell not already covered
    by ``completed_by_schedule_id`` that has a prior persisted entry keeps
    that entry verbatim (reconstructed via ``_cell_from_state``), in matrix
    order. A cell with no prior durable state at all (genuinely never before
    recorded) is left out entirely -- never fabricated as a placeholder --
    so an ordinary first-ever run's intermediate checkpoints are byte-for-
    byte unaffected (this is a no-op whenever ``prior_cells`` is empty).

    Keyed by ``schedule_id`` rather than assuming a positionally
    matrix-ordered input (v1.6 Phase 2, docs/V1_6_PHASE2_PARALLEL_
    EVALUATION.md): the parallel dispatch path resolves cells in
    wall-clock/completion order, not matrix order, so canonical ordering is
    reconstructed here -- by walking ``matrix`` and looking each cell up --
    for both the serial and parallel dispatch paths alike. One ordering
    implementation, not two.
    """

    merged: list[EvaluationCell] = []
    for cell in matrix:
        resolved = completed_by_schedule_id.get(cell.schedule_id)
        if resolved is not None:
            merged.append(resolved)
            continue
        previous = prior_cells.get(cell.schedule_id)
        if previous is not None:
            merged.append(_cell_from_state(cell, previous))
    return merged


# ---------------------------------------------------------------------------
# Revision / provenance restoration
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RevisionPlanEntry:
    """The two revision fields rendered into one ``planned_identities`` entry.

    Deliberately narrower than ``agent_revisions.RevisionArchivalResult``:
    ``complete``/``omitted`` are not persisted here at all (Sec 5.1 of the
    spec -- they already live durably in the revision store's own
    ``manifest.json``, keyed by ``agent_revision_id``; duplicating them
    into every evaluation artifact that references a revision would be a
    second, driftable copy of the same fact).
    """

    agent_revision_id: str | None
    agent_revision_error: str | None


def _revision_entry_from_raw(raw: Any) -> RevisionPlanEntry | None:
    if not isinstance(raw, Mapping):
        return None
    revision_id = raw.get("agent_revision_id")
    if not isinstance(revision_id, str):
        return None
    error = raw.get("agent_revision_error")
    return RevisionPlanEntry(revision_id, error if isinstance(error, str) else None)


def prior_revision_by_agent_id(prior: Mapping[str, Any]) -> dict[str, RevisionPlanEntry]:
    """Recover any already-recorded ``agent_revision_id``s from a prior checkpoint.

    Resume/retry must retain the originally planned revision ID (Sec 4 of
    docs/specs/agent_revision.md) -- this is what lets
    :func:`resolve_revision_results` skip re-archiving (and re-reading the
    source tree) for any agent that already has a durable, recorded
    revision from an earlier invocation of this same evaluation, rather
    than silently recomputing one every time ``EvaluationService.run`` is
    called. An agent with no usable prior ``agent_revision_id`` (a
    pre-Phase-3 v2 artifact -- no ``agent_revisions`` key at all -- or a
    prior invocation whose archival never produced an id) is simply absent
    from the returned mapping -- :func:`resolve_revision_results` then
    archives it fresh, exactly as it would for a first invocation.

    ``agent_revisions`` (Sec 5.1/5.2 of the spec, as actually implemented)
    is a role-keyed sibling of ``planned_identities`` -- ``candidate``/
    ``baseline``/``opponents`` -- deliberately carrying no ``agent_id``
    field of its own (unlike ``planned_identities``' entries), so it never
    risks being mistaken for something that could be merged back into
    ``planned_identities`` and rehashed. Recovering an agent_id-keyed
    lookup therefore means correlating positionally against the prior
    artifact's own ``candidate_id``/``baseline_id``/``opponent_ids`` --
    the same ordered-list convention ``EvaluationService._evaluation_id``'s
    own
    ``"opponents": [identities[opponent_id] for opponent_id in
    request.opponent_ids]`` already uses.
    """

    agent_revisions = prior.get("agent_revisions")
    if not isinstance(agent_revisions, Mapping):
        return {}

    result: dict[str, RevisionPlanEntry] = {}

    candidate_id = prior.get("candidate_id")
    if isinstance(candidate_id, str):
        entry = _revision_entry_from_raw(agent_revisions.get("candidate"))
        if entry is not None:
            result[candidate_id] = entry

    baseline_id = prior.get("baseline_id")
    if isinstance(baseline_id, str):
        entry = _revision_entry_from_raw(agent_revisions.get("baseline"))
        if entry is not None and baseline_id not in result:
            result[baseline_id] = entry

    opponent_ids = prior.get("opponent_ids")
    opponent_revisions = agent_revisions.get("opponents")
    if isinstance(opponent_ids, list) and isinstance(opponent_revisions, list):
        for agent_id, raw in zip(opponent_ids, opponent_revisions):
            if not isinstance(agent_id, str) or agent_id in result:
                continue
            entry = _revision_entry_from_raw(raw)
            if entry is not None:
                result[agent_id] = entry
    return result


def resolve_revision_results(
    request: EvaluationRequest,
    specs: Mapping[str, AgentSpec],
    planned_identities: Mapping[str, dict[str, Any]],
    prior: Mapping[str, Any],
) -> dict[str, RevisionPlanEntry]:
    """One ``RevisionPlanEntry`` per distinct agent_id in ``specs``.

    Reused verbatim from ``prior`` when already recorded there (resume/
    retry must retain the originally planned revision ID -- never
    silently recompute one for an agent this evaluation has already
    durably planned, docs/specs/agent_revision.md Sec 4). Freshly
    archived otherwise, from the *same* ``walk_agent_files`` read used
    for the freeze-time consistency check immediately below -- one
    read, never a second independent one racing against
    ``agent_identity()``'s own (Sec 4.2).

    Must be called after ``planned_identities`` is built and after
    ``prior`` is loaded, but before ``evaluation_id``/anything derived
    from it is trusted for scheduling, and strictly before any cell
    executes or any checkpoint is written -- a detected mismatch (see
    below) raises out of this function, aborting ``EvaluationService.run``
    before any of that happens.
    """

    prior_revisions = prior_revision_by_agent_id(prior)
    root = request.data_root or get_data_root()
    store_root = agent_revisions_root(root)

    resolved: dict[str, RevisionPlanEntry] = {}
    for agent_id, spec in specs.items():
        if agent_id in prior_revisions:
            resolved[agent_id] = prior_revisions[agent_id]
            continue

        # Not yet planned by any prior invocation of this evaluation --
        # archive fresh. `walk` is read exactly once and used for both
        # the cross-check below and the archive write itself
        # (`archive_agent_revision_from_walk`), so revision capture and
        # `planned_identities[agent_id]` describe the same source read
        # as closely as this process can prove (Sec 4.2): the frozen
        # `local_source_fingerprint` was computed moments earlier, in
        # this same freeze step, by `agent_identity()`'s own
        # independent read.
        walk = walk_agent_files(spec.dir)
        cross_check = local_python_subset_fingerprint(walk)
        if cross_check != planned_identities[agent_id].get("local_source_fingerprint"):
            raise EvaluationConfigurationError(
                f"Revision archival observed source for agent {agent_id!r} that "
                "does not match the frozen evaluation plan; aborting before any "
                "cell executes. Source changed during evaluation planning -- "
                "start a fresh evaluation."
            )

        result: RevisionArchivalResult = archive_agent_revision_from_walk(
            walk, store_root=store_root, source_agent_id=agent_id
        )
        resolved[agent_id] = RevisionPlanEntry(result.agent_revision_id, result.error)
    return resolved


# ---------------------------------------------------------------------------
# Evaluation state loading
# ---------------------------------------------------------------------------


def load_evaluation_state(path: Path, evaluation_id: str, expected_schema_version: int) -> dict[str, Any]:
    """Load a prior ``evaluation.json`` for resume, or ``{}`` if absent.

    The resume compatibility gate, unchanged: the artifact must declare
    this module's schema name, the methodology-specific schema version
    this request resolved to, and exactly this request's own
    ``evaluation_id``.  Anything else fails closed with an
    :class:`EvaluationConfigurationError` rather than being reinterpreted.
    """

    if not path.is_file():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema") != SCHEMA_NAME:
        raise EvaluationConfigurationError(
            f"Existing evaluation state at {path} uses an unrecognized schema."
        )
    # v2.0.0-beta2 Phase 1: `expected_schema_version` is resolved from
    # *this* request's own methodology (v1 -> SCHEMA_VERSION, v2 ->
    # SCHEMA_VERSION_V2), never the bare module constant -- a v1 resume
    # request must keep matching only SCHEMA_VERSION exactly as before
    # (unaffected by SCHEMA_VERSION_V2 existing), and a v2 resume
    # request must fail closed against a differently-versioned existing
    # artifact rather than silently reinterpreting it.
    if data.get("schema_version") != expected_schema_version:
        raise EvaluationConfigurationError(
            f"Existing evaluation state at {path} uses unsupported schema version "
            f"{data.get('schema_version')!r} (expected {expected_schema_version})."
        )
    if data.get("evaluation_id") != evaluation_id:
        raise EvaluationConfigurationError(
            "Existing evaluation state does not match this request."
        )
    return data


def read_evaluation(path: Path) -> dict[str, Any]:
    """Read a persisted ``evaluation.json`` verbatim (dict form).

    A thin, schema-checked read used by the CLI's ``--dry-run``-adjacent
    presentation code and by the Designer (Sec 13); the richer typed
    ``EvaluationResult`` is only produced by ``EvaluationService.run``
    itself, since that is the only place with the resolved
    ``EvaluationCell``/``SubjectAggregate`` objects to reconstruct.
    """

    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("schema") != SCHEMA_NAME:
        raise EvaluationConfigurationError(f"{path}: not a {SCHEMA_NAME} artifact.")
    # v2.0.0-beta2 Phase 1/2: a caller reading an arbitrary on-disk
    # artifact (unlike load_evaluation_state, which already knows this
    # run's own
    # resolved methodology) cannot know in advance whether it is a v1
    # (SCHEMA_VERSION), v2 1v1 (SCHEMA_VERSION_V2), or v2 group
    # (SCHEMA_VERSION_V2_GROUP), or v4-seeded (SCHEMA_VERSION_V4) artifact
    # -- all four are equally "this module's own current schema," just
    # under different resolved methodologies.
    _supported_versions = (
        SCHEMA_VERSION,
        SCHEMA_VERSION_V2,
        SCHEMA_VERSION_V2_GROUP,
        SCHEMA_VERSION_V4,
    )
    if data.get("schema_version") not in _supported_versions:
        raise EvaluationConfigurationError(
            f"{path}: unsupported schema version {data.get('schema_version')!r} "
            f"(expected one of {_supported_versions})."
        )
    return data


# ---------------------------------------------------------------------------
# Atomic artifact writing
# ---------------------------------------------------------------------------


def _cell_to_dict(cell: EvaluationCell, base: Path) -> dict[str, Any]:
    data = asdict(cell)
    try:
        data["artifact_dir"] = str(cell.artifact_dir.relative_to(base))
    except ValueError:
        data["artifact_dir"] = str(cell.artifact_dir)
    return data


def write_evaluation_state(
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
    """Persist one checkpoint. Never re-derives entrant identity from disk.

    ``planned_identities`` must be the exact ``agent_id -> agent_identity()``
    snapshot ``EvaluationService.run`` built once at preflight (or an unchanged carry-over
    of a prior artifact's own recorded snapshot -- see the B2 resume
    path) -- this method only reshapes it into the persisted
    ``candidate``/``baseline``/``opponents`` structure by lookup, so the
    written ``planned_identities`` payload is structurally guaranteed to
    reproduce ``evaluation_id`` (both come from the same frozen dict; see
    ``EvaluationService._evaluation_id``).

    ``revision_plan`` (docs/specs/agent_revision.md Sec 5.2, revised)
    is rendered into its own **sibling top-level field**,
    ``agent_revisions`` -- never merged into ``planned_identities``
    itself. An earlier version of this method merged the two fields
    directly into each ``planned_identities.candidate``/``.baseline``/
    ``.opponents[]`` entry; that broke the existing, tested "B1"
    invariant (``test_persisted_planned_identity_rehashes_to_the_
    recorded_evaluation_id`` and siblings) that recomputing
    ``evaluation_id`` from ``planned_identities`` *as persisted in the
    artifact* must reproduce the stored value exactly -- a reader
    rehashing the persisted dict verbatim would have picked up the two
    extra keys and produced a different hash than the one actually
    stored. Keeping ``agent_revisions`` a wholly separate JSON key
    keeps ``planned_identities`` byte-for-byte identical to what
    ``_evaluation_id`` hashed, with no copying or filtering required to
    prove it -- the same object is written both times.
    """

    project = get_project_info()

    def _revision_payload(agent_id: str) -> dict[str, str | None]:
        entry = revision_plan.get(agent_id)
        return {
            "agent_revision_id": entry.agent_revision_id if entry is not None else None,
            "agent_revision_error": entry.agent_revision_error if entry is not None else None,
        }

    planned_identities_payload = {
        "candidate": planned_identities[request.candidate_id],
        "baseline": (
            planned_identities[request.baseline_id]
            if request.baseline_id is not None
            else None
        ),
        "opponents": [
            planned_identities[opponent_id] for opponent_id in request.opponent_ids
        ],
    }
    agent_revisions_payload = {
        "candidate": _revision_payload(request.candidate_id),
        "baseline": (
            _revision_payload(request.baseline_id) if request.baseline_id is not None else None
        ),
        "opponents": [_revision_payload(opponent_id) for opponent_id in request.opponent_ids],
    }
    conditions_dict = effective_conditions_payload(
        conditions, request.resolved_locality_reach
    )
    resolved_rules_id = request.resolved_rules_compatibility_id
    resolved_is_v2 = is_ruleset_v2_methodology(resolved_rules_id)
    resolved_is_v4 = is_ruleset_v4_methodology(resolved_rules_id)
    resolved_is_v6_research_scale = is_ruleset_v6_research_scale_methodology(resolved_rules_id)
    resolved_is_v6_research_scale_move = is_ruleset_v6_research_scale_move_methodology(
        resolved_rules_id
    )
    resolved_is_v6_research_scale_move_proportional = (
        is_ruleset_v6_research_scale_move_proportional_methodology(resolved_rules_id)
    )
    resolved_is_v6_research_capture_hold = is_ruleset_v6_research_capture_hold_methodology(
        resolved_rules_id
    )
    resolved_is_v6_research_capture_hold_disruption_slot = (
        is_ruleset_v6_research_capture_hold_disruption_slot_methodology(resolved_rules_id)
    )
    resolved_is_v6_research_disruption_slot = is_ruleset_v6_research_disruption_slot_methodology(
        resolved_rules_id
    )
    resolved_is_v6_research_capture_hold_disruption_slot_mirrored_passes = (
        is_ruleset_v6_research_capture_hold_disruption_slot_mirrored_passes_methodology(
            resolved_rules_id
        )
    )
    resolved_is_v6_research_disruption_slot_mirrored_passes = (
        is_ruleset_v6_research_disruption_slot_mirrored_passes_methodology(resolved_rules_id)
    )
    resolved_is_v6_research_capture_hold_disruption_slot_anchor_before_core = (
        is_ruleset_v6_research_capture_hold_disruption_slot_anchor_before_core_methodology(
            resolved_rules_id
        )
    )
    resolved_is_v6_research_disruption_slot_anchor_before_core = (
        is_ruleset_v6_research_disruption_slot_anchor_before_core_methodology(resolved_rules_id)
    )
    resolved_group = request.group and resolved_is_v2
    write_json_atomic(
        path,
        {
            "schema": SCHEMA_NAME,
            # v2.0.0-beta2 Phase 1: resolved per request, never the bare
            # module constant -- for every v1 request (omitted or
            # explicit bytefray-rules-1) this is exactly SCHEMA_VERSION/
            # IDENTITY_VERSION (4), byte-identical to every artifact
            # this module has ever written. An explicit --ruleset
            # bytefray-rules-2 1v1 request writes SCHEMA_VERSION_V2/
            # IDENTITY_VERSION_V2 (5, Phase 1); a --group request on top
            # of that writes SCHEMA_VERSION_V2_GROUP/
            # IDENTITY_VERSION_V2_GROUP (6, Phase 2); a --ruleset
            # bytefray-rules-4-alpha2 request writes SCHEMA_VERSION_V4/
            # IDENTITY_VERSION_V4 (7, v4.0.0-rc1 Phase 1) -- each a
            # brand-new artifact shape with no historical instance to
            # stay compatible with.
            "schema_version": resolved_schema_version(
                resolved_is_v2,
                resolved_group,
                resolved_is_v4,
                resolved_is_v6_research_scale,
                resolved_is_v6_research_scale_move,
                resolved_is_v6_research_scale_move_proportional,
                is_v6_research_capture_hold_methodology=resolved_is_v6_research_capture_hold,
                is_v6_research_capture_hold_disruption_slot_methodology=(
                    resolved_is_v6_research_capture_hold_disruption_slot
                ),
                is_v6_research_disruption_slot_methodology=resolved_is_v6_research_disruption_slot,
                is_v6_research_capture_hold_disruption_slot_mirrored_passes_methodology=(
                    resolved_is_v6_research_capture_hold_disruption_slot_mirrored_passes
                ),
                is_v6_research_disruption_slot_mirrored_passes_methodology=(
                    resolved_is_v6_research_disruption_slot_mirrored_passes
                ),
                is_v6_research_capture_hold_disruption_slot_anchor_before_core_methodology=(
                    resolved_is_v6_research_capture_hold_disruption_slot_anchor_before_core
                ),
                is_v6_research_disruption_slot_anchor_before_core_methodology=(
                    resolved_is_v6_research_disruption_slot_anchor_before_core
                ),
            ),
            "identity_version": resolved_identity_version(
                resolved_is_v2,
                resolved_group,
                resolved_is_v4,
                resolved_is_v6_research_scale,
                resolved_is_v6_research_scale_move,
                resolved_is_v6_research_scale_move_proportional,
                is_v6_research_capture_hold_methodology=resolved_is_v6_research_capture_hold,
                is_v6_research_capture_hold_disruption_slot_methodology=(
                    resolved_is_v6_research_capture_hold_disruption_slot
                ),
                is_v6_research_disruption_slot_methodology=resolved_is_v6_research_disruption_slot,
                is_v6_research_capture_hold_disruption_slot_mirrored_passes_methodology=(
                    resolved_is_v6_research_capture_hold_disruption_slot_mirrored_passes
                ),
                is_v6_research_disruption_slot_mirrored_passes_methodology=(
                    resolved_is_v6_research_disruption_slot_mirrored_passes
                ),
                is_v6_research_capture_hold_disruption_slot_anchor_before_core_methodology=(
                    resolved_is_v6_research_capture_hold_disruption_slot_anchor_before_core
                ),
                is_v6_research_disruption_slot_anchor_before_core_methodology=(
                    resolved_is_v6_research_disruption_slot_anchor_before_core
                ),
            ),
            "evaluation_id": evaluation_id,
            "candidate_id": request.candidate_id,
            "baseline_id": request.baseline_id,
            "opponent_ids": list(request.opponent_ids),
            "seeds": list(request.seeds),
            "ticks": request.ticks,
            "matrix_size": len(matrix),
            "planned_identities": planned_identities_payload,
            "agent_revisions": agent_revisions_payload,
            "effective_conditions": conditions_dict,
            "effective_conditions_fingerprint": (
                effective_conditions_fingerprint(conditions_dict)
            ),
            "rules_compatibility_id": resolved_rules_id,
            # v0.9 Phase 6: sibling top-level fields, same pattern as
            # rules_compatibility_id immediately above (Phase 5 spec
            # Sec AA.3/AA.4) -- evaluation-wide methodology, never
            # folded into effective_conditions.
            "orientation_mode": request.orientation_mode,
            "arena_alignment_mode": request.resolved_arena_alignment_mode,
            # v2.0.0-beta2 Phase 2: additive top-level disclosure of
            # multi-entrant methodology -- never identity-affecting on
            # its own (the resolved layout set already is, via
            # arena_alignment_mode's distinct value and each cell's own
            # roster/seat fields); purely for `evaluations show`/`list`
            # and JSON consumers to see at a glance without scanning
            # cells.
            "group": resolved_group,
            "roster_agent_ids": list(request.canonical_roster) if resolved_group else None,
            "created_at": created_at,
            "updated_at": utc_now_iso(),
            "finished_at": finished_at,
            "lifecycle_state": lifecycle_state,
            "abort_reason": abort_reason,
            "abort_detail": dict(abort_detail) if abort_detail is not None else None,
            "execution_contexts": [dict(item) for item in execution_contexts],
            # Writer/resumer bookkeeping only (which Bytefray build most
            # recently touched this artifact) -- refreshed on every
            # write, including a no-op resume under a different
            # runtime. It is *not* cell execution provenance; that is
            # `execution_contexts`/each cell's own `execution_context_id`
            # (Sec 6/H2), which are never rewritten by a resuming
            # process (M1).
            "project": asdict(project),
            "cells": [_cell_to_dict(cell, path.parent) for cell in cells],
            "aggregates": [asdict(row) for row in aggregates],
            "comparison": [asdict(row) for row in comparison],
            # F.6 remediation (docs task Sec 4): "every scheduled cell
            # has been attempted" and "the evaluation succeeded" are
            # different claims. `complete` previously conflated them --
            # `len(cells) >= len(matrix)` is true the instant scheduling
            # is exhausted, regardless of whether any cell actually
            # executed successfully, so an evaluation whose every cell
            # failed (an Agent API v2 roster resolved to an incompatible
            # Ruleset, for example) was persisted as `complete: true`.
            # `complete` now means what its name says: scheduling
            # exhausted *and* every persisted cell executed
            # successfully, i.e. exactly the caller-supplied
            # `lifecycle_state` this checkpoint was told to write is
            # `LIFECYCLE_STATE_FINISHED` (never true for `"running"`,
            # `LIFECYCLE_STATE_FINISHED_WITH_FAILURES`, or
            # `LIFECYCLE_STATE_ABORTED`).
            "complete": lifecycle_state == LIFECYCLE_STATE_FINISHED,
        },
    )
