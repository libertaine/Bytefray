"""Pure construction of stable evaluation identity values.

This module owns the canonical payload recipes shared by live evaluation
production and historical verification.  It consumes already-resolved agent
and methodology inputs; it does not discover agents, calculate geometry,
compile matrices, execute matches, or read artifacts.

Historical identity versions remain readable vocabulary only.  Supporting
their pure payload shapes here does not make their retired Rulesets or group
methodologies executable.
"""

from __future__ import annotations

import hashlib
import re
from collections.abc import Mapping, Sequence
from dataclasses import asdict
from pathlib import Path
from typing import Any

from battle_engine.agent_api import local_source_fingerprint
from battle_engine.agents import AgentSpec
from battle_engine.evaluation_contracts import EffectiveConditions
from battle_engine.result_model import stable_id


def source_digest(source_path: Path | None) -> str | None:
    """Hash an entry-point source file's bytes, or ``None`` if unavailable.

    The one primitive genuinely shared with ``tournament_service.
    _entrant_identity``/``match_service.canonical_match_id`` -- each of
    those builds its own differently shaped identity dict for its own
    purpose and is left untouched (see Sec 8/Sec 2 finding 8 of the spec
    for why unifying the dict shapes themselves would be a premature
    abstraction).
    """

    if source_path is None or not source_path.is_file():
        return None
    return hashlib.sha256(source_path.read_bytes()).hexdigest()


def agent_identity(spec: AgentSpec) -> dict[str, Any]:
    """A stable, hashable identity fingerprint for one resolved Python agent."""

    return {
        "agent_id": spec.name,
        "kind": spec.kind,
        "api_version": spec.api_version,
        "agent_version": spec.version,
        "entry_point": spec.entry_point,
        "source_sha256": source_digest(spec.source_path),
        # H3/B1(v0.7 closure pass): catches an imported local helper/nested
        # local package edit that source_sha256 alone (entry-point file
        # only) would miss. Cross-checked post-execution against the
        # executor's own recorded ``NativeAgentResult.metadata`` -- which
        # now carries a matching ``local_source_fingerprint`` computed by
        # the executor itself at load time (``python_runtime``/
        # ``supervised_runtime``), not a second independent disk read by
        # this module -- see ``_ACTUAL_IDENTITY_FIELDS``/
        # ``_post_execution_identity_drift``.
        "local_source_fingerprint": local_source_fingerprint(spec.dir),
    }


def effective_conditions_payload(
    conditions: EffectiveConditions,
    locality_reach: int | None = None,
    scheduler_override: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """The hashed/persisted form of one evaluation's effective conditions.

    ``asdict(conditions)`` verbatim, plus -- for a bounded-locality
    evaluation only -- the resolved reach ``R``, plus -- for an evaluation
    that overrides gameplay scheduler semantics only -- the resolved
    effective scheduler fields.

    Reach is deliberately *not* a field of :class:`EffectiveConditions`
    itself. Adding one would put ``"locality_reach": null`` into
    ``asdict()`` for every evaluation ever run, changing every
    ``evaluation_id`` and every ``effective_conditions_fingerprint`` in the
    project's history to disclose a condition that does not apply to them.
    Gating the key here keeps every non-locality payload byte-identical
    while still making reach fully identity-bearing and
    comparability-gating where it is real: two locality evaluations that
    differ only in ``R`` get different ids and are correctly reported as
    running under different conditions.

    ``scheduler_override`` follows the identical precedent (V6 research-
    integrity hardening): ``None`` for every evaluation that does not opt
    into the ``scheduler_chunk_size``/``scheduler_rotate_start`` research
    override -- which is every evaluation before that override existed and
    every one since that omits it -- keeps this payload, and therefore
    ``evaluation_id``, byte-identical to before. An evaluation that *does*
    override scheduler semantics folds the resolved effective policy's
    scheduling fields in directly, so two otherwise-identical evaluations
    that actually schedule entrants differently can never collide on
    ``evaluation_id`` (closing the scheduler-identity defect this override
    used to admit).
    """

    payload = asdict(conditions)
    if locality_reach is not None:
        payload["locality_reach"] = locality_reach
    if scheduler_override is not None:
        payload["scheduler_override"] = dict(scheduler_override)
    return payload


def effective_conditions_fingerprint(payload: Mapping[str, Any]) -> str:
    """Hash an already-normalized effective-conditions payload."""

    return stable_id("evaluation-conditions", payload)


def placement_identity_payload(
    placement_id: Any, subject_start: Any, opponent_start: Any
) -> dict[str, Any]:
    """Normalize one pairwise placement for an identity payload."""

    return {
        "placement_id": placement_id,
        "subject_start": subject_start,
        "opponent_start": opponent_start,
    }


def layout_identity_payload(layout_id: Any, seat_starts: Sequence[Any]) -> dict[str, Any]:
    """Normalize one historical group layout for an identity payload."""

    return {"layout_id": layout_id, "seat_starts": list(seat_starts)}


def seeded_placement_identity_payload(
    seed: Any, subject_start: Any, opponent_start: Any
) -> dict[str, Any]:
    """Normalize one stable-v4 seed-derived geometry sample."""

    return {
        "seed": seed,
        "subject_start": subject_start,
        "opponent_start": opponent_start,
    }


def build_evaluation_identity_payload(
    *,
    identity_version: int,
    candidate: Any,
    baseline: Any,
    opponents: Sequence[Any],
    seeds: Sequence[Any],
    ticks: int,
    effective_conditions: Any,
    rules_compatibility_id: str,
    orientation_mode: Any = None,
    arena_alignment_mode: Any = None,
    group: bool = False,
    layouts: Sequence[Mapping[str, Any]] | None = None,
    placements: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build the exact versioned evaluation-ID payload for identities 2-7.

    Callers remain responsible for independently resolving or reconstructing
    semantic inputs.  This function owns only the stable version-dependent
    field inclusion recipe.

    ``layouts``/``placements`` use ``None`` to mean that an untrusted reader
    could not reconstruct that input.  Omitting the corresponding key in
    that case preserves the verifier's pre-extraction behavior for malformed
    artifacts; valid producer and historical inputs always supply the value
    required by their identity version.
    """

    payload: dict[str, Any] = {
        "identity_version": identity_version,
        "candidate": candidate,
        "baseline": baseline,
        "opponents": list(opponents),
        "seeds": list(seeds),
        "ticks": ticks,
        "effective_conditions": effective_conditions,
        "rules_compatibility_id": rules_compatibility_id,
    }
    if identity_version >= 4:
        payload["orientation_mode"] = orientation_mode
        payload["arena_alignment_mode"] = arena_alignment_mode
    if identity_version >= 6 and group:
        payload.pop("orientation_mode", None)
        if layouts is not None:
            payload["group"] = True
            payload["layouts"] = list(layouts)
    elif identity_version >= 5 and placements is not None:
        payload["placements"] = list(placements)
    return payload


def build_evaluation_id(
    *,
    identity_version: int,
    candidate: Any,
    baseline: Any,
    opponents: Sequence[Any],
    seeds: Sequence[Any],
    ticks: int,
    effective_conditions: Any,
    rules_compatibility_id: str,
    orientation_mode: Any = None,
    arena_alignment_mode: Any = None,
    group: bool = False,
    layouts: Sequence[Mapping[str, Any]] | None = None,
    placements: Sequence[Mapping[str, Any]] | None = None,
) -> str:
    """Hash the canonical versioned evaluation identity payload."""

    return stable_id(
        "evaluation-v2",
        build_evaluation_identity_payload(
            identity_version=identity_version,
            candidate=candidate,
            baseline=baseline,
            opponents=opponents,
            seeds=seeds,
            ticks=ticks,
            effective_conditions=effective_conditions,
            rules_compatibility_id=rules_compatibility_id,
            orientation_mode=orientation_mode,
            arena_alignment_mode=arena_alignment_mode,
            group=group,
            layouts=layouts,
            placements=placements,
        ),
    )


#: The exact shape :func:`build_evaluation_id` always produces --
#: ``stable_id``'s literal ``"evaluation-v2"`` prefix plus its 24-hex-digit
#: truncated SHA-256 -- regardless of the ``identity_version`` embedded
#: inside the hashed payload. Used only to *recognize* a directory that was
#: named verbatim after an evaluation id (see ``looks_like_evaluation_id``);
#: never used to validate or reconstruct one.
_EVALUATION_ID_PATTERN = re.compile(r"^evaluation-v2_[0-9a-f]{24}$")


def looks_like_evaluation_id(name: str) -> bool:
    """Return whether ``name`` has the exact shape ``build_evaluation_id`` produces.

    V6 research-integrity hardening (preflight/run double-freeze): a
    content-addressed output directory is always named verbatim after its
    evaluation id (``evaluation_cli._default_output_dir``), and no arbitrary
    user-chosen directory name ever accidentally has this exact shape. This
    lets :meth:`~battle_engine.evaluation_service.EvaluationService.run`
    recognize "this destination claims to be addressed by a specific
    evaluation id" from ``output_dir`` alone, with no caller needing to say
    so explicitly, and cross-check that claim against what this run's own
    freshly resolved agent source actually yields -- while leaving every
    explicit, non-addressed ``--output`` directory (which never matches this
    shape) completely unaffected.
    """

    return bool(_EVALUATION_ID_PATTERN.match(name))


def build_pairwise_schedule_id(
    *,
    identity_version: int,
    evaluation_id: str,
    role: str,
    subject_id: str,
    opponent_id: str,
    seed: int,
    orientation: str,
    ordinal: int,
    placement_id: Any = None,
) -> str:
    """Build one pairwise schedule ID without owning matrix ordering."""

    payload: dict[str, Any] = {
        "evaluation_id": evaluation_id,
        "role": role,
        "subject_id": subject_id,
        "opponent_id": opponent_id,
        "seed": seed,
        "orientation": orientation,
        "ordinal": ordinal,
    }
    if identity_version >= 5:
        payload["placement_id"] = placement_id
    return stable_id("evaluation-cell", payload)


def build_group_schedule_id(
    *,
    evaluation_id: str,
    role: str,
    roster: Sequence[str],
    seat_agent_ids: Sequence[str],
    seed: int,
    layout_id: str,
    ordinal: int,
) -> str:
    """Build one historical group schedule ID from compiled coordinates."""

    return stable_id(
        "evaluation-cell",
        {
            "evaluation_id": evaluation_id,
            "role": role,
            "roster": list(roster),
            "seat_agent_ids": list(seat_agent_ids),
            "seed": seed,
            "layout_id": layout_id,
            "ordinal": ordinal,
        },
    )


def build_pairwise_condition_fingerprint(
    *,
    identity_version: Any,
    opponent: Any,
    seed: Any,
    effective_conditions: str,
    rules_compatibility_id: Any,
    condition_occurrence_index: Any,
    orientation: Any = None,
    arena_alignment_mode: Any = None,
    group: bool = False,
    placement_id: Any = None,
    subject_start: Any = None,
    opponent_start: Any = None,
) -> str:
    """Build the versioned pairwise condition fingerprint for identities 2-7."""

    payload: dict[str, Any] = {
        "opponent": opponent,
        "seed": seed,
        "effective_conditions": effective_conditions,
        "rules_compatibility_id": rules_compatibility_id,
        "condition_occurrence_index": condition_occurrence_index,
    }
    if isinstance(identity_version, int) and identity_version >= 4:
        payload["orientation"] = orientation
        payload["arena_alignment_mode"] = arena_alignment_mode
    if isinstance(identity_version, int) and identity_version >= 5 and not group:
        payload["placement"] = placement_identity_payload(
            placement_id, subject_start, opponent_start
        )
    return stable_id("evaluation-condition", payload)


def build_group_condition_fingerprint(
    *,
    roster: Sequence[Any],
    seat_agent_ids: Sequence[str],
    seed: int,
    effective_conditions: str,
    rules_compatibility_id: str,
    arena_alignment_mode: str,
    layout_id: str,
    seat_starts: Sequence[int],
) -> str:
    """Build one historical group condition fingerprint from normalized inputs."""

    return stable_id(
        "evaluation-condition",
        {
            "roster": list(roster),
            "seat_agent_ids": list(seat_agent_ids),
            "seed": seed,
            "effective_conditions": effective_conditions,
            "rules_compatibility_id": rules_compatibility_id,
            "arena_alignment_mode": arena_alignment_mode,
            "layout": layout_identity_payload(layout_id, seat_starts),
        },
    )
