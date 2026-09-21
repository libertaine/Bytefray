"""Deterministic evaluation planning: one request becomes one ordered matrix.

This module owns the pure transformation from a normalized
``EvaluationRequest`` plus its resolved methodology into the exact ordered
tuple of ``EvaluationCell`` objects an evaluation will execute -- the
"which matches, in exactly what deterministic order" half of evaluation.
It resolves placement geometry, expands every deterministic axis (subject
role, opponent, opponent occurrence, seed, seed occurrence, placement,
orientation), assigns matrix ordinals, and builds each cell's artifact path
label.

It executes nothing, persists nothing, and reads no artifacts.  Identity
values are deliberately not hashed here: this module resolves the semantic
coordinates and hands them to ``evaluation_identity``, which owns every
canonical payload recipe.  The dependency direction is strictly
``evaluation_contracts`` -> ``evaluation_identity`` ->
``evaluation_planning``; nothing here imports ``agent_evaluation``,
evaluation history, the CLI, the Designer, the worker, or service
orchestration, so the matrix can be understood without loading any of them.

Retired multi-entrant ("group") planning vocabulary lives here because this
is its semantic owner, not because it is executable: ``build_matrix``
refuses a group request outright, and the retained group helpers exist only
so historical artifacts stay reconstructable and independently verifiable.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from itertools import permutations as _permutations

import battle_engine.evaluation_identity as _evaluation_identity
from battle_engine.agents import AgentSpec
from battle_engine.config import Config
from battle_engine.evaluation_contracts import (
    BASELINE,
    CANDIDATE,
    EVALUATION_ARENA_ALIGNMENT_MODE_V2_GROUP_STANDARD,
    ORIENTATION_CANDIDATE_FIRST,
    ORIENTATION_OPPONENT_FIRST,
    EvaluationCell,
    EvaluationConfigurationError,
    EvaluationLayout,
    EvaluationPlacement,
    EvaluationRequest,
    EvaluationSeatAssignment,
    is_ruleset_v2_methodology,
    is_ruleset_v4_methodology,
    resolved_identity_version,
)
from battle_engine.evaluation_identity import agent_identity
from battle_engine.placement import resolve_direct_match_starts, spread_seat_starts

# ---------------------------------------------------------------------------
# Placement / layout geometry
# ---------------------------------------------------------------------------


def standard_placements(arena_size: int | None = None) -> tuple[EvaluationPlacement, ...]:
    """The standard Ruleset-v2 1v1 placement set (design doc Sec Placement).

    Three deterministic conditions, derived mechanically as fractions of
    ``arena_size`` -- never hand-picked coordinates, never dependent on any
    specific opponent's scan geometry (alpha.7's COLD/HOT fixtures were
    calibrated to one superseded attacker and are deliberately not reused
    here as permanent methodology; see the design doc):

    * ``opposed`` -- maximal, half-arena separation, phase 0. The control
      condition: as far apart as the arena allows.
    * ``quarter`` -- a closer, non-opposed quarter-arena separation, phase
      0. Proves a conclusion is not an artifact of exact-half separation.
    * ``opposed-shifted`` -- the same half-arena separation as ``opposed``,
      phase-shifted by a quarter turn. Proves an ``opposed`` conclusion is
      not an artifact of starting exactly at address 0.

    Non-overlapping by construction: every gap here is a quarter or half of
    ``arena_size``, vastly larger than ``CORE_SIZE`` (8). Never random --
    every coordinate is a pure function of ``arena_size``.
    """

    size = arena_size if arena_size is not None else Config().arena_size
    half = size // 2
    quarter = size // 4
    return (
        EvaluationPlacement("opposed", subject_start=0, opponent_start=half),
        EvaluationPlacement("quarter", subject_start=0, opponent_start=quarter),
        EvaluationPlacement(
            "opposed-shifted",
            subject_start=quarter,
            opponent_start=(quarter + half) % size,
        ),
    )


# ---------------------------------------------------------------------------
# Multi-entrant ("group") domain model (v2.0.0-beta2 Phase 2)
# ---------------------------------------------------------------------------
#
# Deliberately a separate model from EvaluationPlacement/standard_placements
# above, not a generalization written in place of them: Phase 1's 1v1
# identity path must stay untouched, byte-for-byte, forever (see
# docs/V2_0_BETA2_PHASE2_MULTI_ENTRANT_EVALUATION.md's "why two placement
# models" note for the worked proof that standard_layouts(2, ...) below
# reproduces standard_placements()'s exact three 1v1 conditions -- evidence
# this is a genuine generalization, not a coincidence, without ever routing
# 1v1 cells through this new code).



def enumerate_seat_assignments(roster: Sequence[str]) -> tuple[EvaluationSeatAssignment, ...]:
    """Every distinct seat assignment for ``roster`` (Phase 2: exhaustive
    permutation policy only).

    Deduplicates by the resulting ``seat_agent_ids`` tuple, not by the
    underlying index permutation, so a roster with a repeated agent id
    yields fewer than ``len(roster)!`` assignments (see
    ``EvaluationSeatAssignment``). ``itertools.permutations`` enumerates in
    deterministic lexicographic index order, so generation order is
    reproducible run to run. Future scheduling policies (rotation-only,
    balanced subsets, an explicit preset-driven policy) can live as sibling
    functions with this identical return shape without changing this
    function's own contract -- see the design doc's "permutation model"
    section for why exhaustive-only is the right Phase 2 scope.
    """

    seen: dict[tuple[str, ...], None] = {}
    for perm in _permutations(range(len(roster))):
        seats = tuple(roster[i] for i in perm)
        seen.setdefault(seats, None)
    return tuple(EvaluationSeatAssignment(seat_agent_ids=seats) for seats in seen)


def standard_layouts(entrant_count: int, arena_size: int | None = None) -> tuple[EvaluationLayout, ...]:
    """The standard Ruleset-v2 multi-entrant layout set for ``entrant_count`` seats.

    Three deterministic conditions, mechanically derived as fractions of
    ``arena_size`` -- the direct N-seat generalization of
    ``standard_placements()``'s own three 1v1 conditions:

    * ``spread`` -- seats evenly spaced starting at address 0 (the N-seat
      generalization of ``opposed``'s maximal, phase-0 separation).
    * ``spread-shifted`` -- the same even spacing, phase-shifted by half a
      seat gap (generalizes ``opposed-shifted``).
    * ``close`` -- a tighter, non-maximal spacing (generalizes ``quarter``).

    For ``entrant_count=2`` this formula reproduces ``standard_placements()``'s
    exact three placements (``opposed``/``opposed-shifted``/``quarter``) --
    verified by ``test_standard_layouts_reproduce_1v1_placements_at_n_equals_2``
    -- but this function is never called for 1v1 cells; only group-mode
    cells (``entrant_count >= 2`` where 2 is reachable only via an explicit
    2-entrant group, not ordinary 1v1) use it, so Phase 1's frozen
    ``standard_placements()`` path is never touched by this addition.

    Requires ``entrant_count >= 2``. Non-overlapping by construction for any
    arena size where ``arena_size // (2 * entrant_count) > CORE_SIZE``, true
    for every arena size this project documents as supported.
    """

    if entrant_count < 2:
        raise ValueError(f"standard_layouts requires at least 2 entrants, got {entrant_count}")
    size = arena_size if arena_size is not None else Config().arena_size
    gap = size // entrant_count
    half_gap = gap // 2
    return (
        EvaluationLayout("spread", spread_seat_starts(entrant_count, size)),
        EvaluationLayout(
            "spread-shifted", tuple((i * gap + half_gap) % size for i in range(entrant_count))
        ),
        EvaluationLayout("close", tuple((i * half_gap) % size for i in range(entrant_count))),
    )


def resolve_v4_seed_geometry(
    rules_compatibility_id: str, arena_size: int, seed: int
) -> tuple[int, int]:
    """The (seat A, seat B) start addresses one v4-seeded placement sample resolves to.

    A thin, single-call wrapper around `placement.resolve_direct_match_starts`
    -- bit-for-bit the same seam `bytefray run`/`agent_test` use, called with
    both starts omitted so the Ruleset's own seeded placement (`placement.
    seeded_seat_starts`, shared identically by `bytefray-rules-4-alpha2` and
    its stable promotion `bytefray-rules-4`) resolves them --
    rather than a second, independently-maintained placement formula. Both
    `build_matrix` and `EvaluationService._evaluation_id` call this one
    function so the persisted schedule and the identity hash can never drift
    from each other or from the production seam (research report Sec H.1
    items 1/7).
    """

    starts = resolve_direct_match_starts(
        ruleset_id=rules_compatibility_id,
        arena_size=arena_size,
        entrant_count=2,
        supplied_starts=[None, None],
        seed=seed,
    )
    return starts[0], starts[1]


# ---------------------------------------------------------------------------
# Artifact path labels
# ---------------------------------------------------------------------------
#
# Path labels never affect gameplay, but they do decide where a cell's
# artifacts land on disk, so a resumed evaluation that labelled its cells
# differently would fail to find its own prior work. They are treated as
# compatibility-sensitive: exact characters, exact ordering, exact
# occurrence/placement/orientation suffixes.


def _safe_path_segment(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("._") or "entrant"


def pairwise_cell_label(
    *,
    ordinal: int,
    role: str,
    subject_id: str,
    opponent_id: str,
    seed: int,
    placement_id: str,
    orientation: str,
    include_placement: bool,
) -> str:
    """One pairwise cell's ``matches/<label>`` artifact directory name.

    ``include_placement`` is true for the v2 and v4 methodologies, whose
    cells differ by placement and must therefore say which placement they
    are; a v1-methodology cell has only the one constant ``"fixed"``
    placement and keeps its historical, placement-free label so a legacy
    artifact tree stays resumable at its own recorded paths.
    """

    if include_placement:
        return (
            f"{ordinal:04d}-{role}-{_safe_path_segment(subject_id)}"
            f"-vs-{_safe_path_segment(opponent_id)}-seed{seed}"
            f"-{placement_id}-{orientation}"
        )
    return (
        f"{ordinal:04d}-{role}-{_safe_path_segment(subject_id)}"
        f"-vs-{_safe_path_segment(opponent_id)}-seed{seed}-{orientation}"
    )


def group_cell_label(
    *, ordinal: int, seat_agent_ids: Sequence[str], seed: int, layout_id: str
) -> str:
    """One retired multi-entrant cell's artifact directory name.

    Retained so schema-6 group artifacts stay locatable and verifiable by
    the historical readers; nothing here makes group execution valid again.
    """

    return (
        f"{ordinal:04d}-group-"
        f"{_safe_path_segment('-'.join(seat_agent_ids))}-seed{seed}-{layout_id}"
    )


# ---------------------------------------------------------------------------
# Matrix compilation
# ---------------------------------------------------------------------------


def build_matrix(
    request: EvaluationRequest,
    evaluation_id: str,
    specs: Mapping[str, AgentSpec] | None = None,
    conditions_fingerprint: str | None = None,
    rules_compatibility_id: str | None = None,
    arena_alignment_mode: str | None = None,
) -> tuple[EvaluationCell, ...]:
    """Build the deterministic subject x opponent x seed x placement x orientation matrix.

    Iteration order is candidate, then baseline (if present); opponents
    and seeds in exact request order, never re-sorted or deduplicated
    (docs/specs/agent_evaluation.md Sec 7); placement (v2.0.0-beta2 Phase 1)
    nests inside seed; entrant orientation nests innermost, ``candidate_
    first`` then ``opponent_first`` when ``request.both_orientations``
    (Phase 5 spec Sec I.3) -- only ``candidate_first`` otherwise.

    Placement is resolved from ``request.ruleset_id`` (via ``request.
    is_v2_methodology``/``request.is_v4_methodology``), never from an
    external parameter: a v1-methodology request (omitted or explicit
    ``bytefray-rules-1``) generates exactly one placement per (subject,
    opponent, seed) -- the historical fixed alignment, ``placement_id=
    "fixed"``, both starts ``0`` -- reproducing today's exact matrix shape
    and size. A v2-methodology request (``bytefray-rules-2``) generates
    ``len(standard_placements())`` (3) placements per (subject, opponent,
    seed) instead. A v4-methodology request (``bytefray-rules-4-alpha2``)
    generates exactly one placement per seed too, but that placement is
    itself a function of the seed (``resolve_v4_seed_geometry``), and the
    two orientation cells for one seed share that placement's resolved
    geometry with occupants swapped rather than each keeping its own
    role-anchored start (research report Sec H.1 items 1/4).

    ``specs``/``conditions_fingerprint``/``rules_compatibility_id``/
    ``arena_alignment_mode`` are optional and, when given, feed only
    ``condition_fingerprint`` -- unrelated to placement/ruleset resolution,
    which always comes from ``request`` itself so even a ``--dry-run``
    (no specs/conditions_fingerprint) matrix preview shows real placements.
    """

    subjects: list[tuple[str, str]] = [(CANDIDATE, request.candidate_id)]
    if request.baseline_id is not None:
        subjects.append((BASELINE, request.baseline_id))

    orientations: tuple[str, ...] = (
        (ORIENTATION_CANDIDATE_FIRST, ORIENTATION_OPPONENT_FIRST)
        if request.both_orientations
        else (ORIENTATION_CANDIDATE_FIRST,)
    )

    resolved_rules_id = request.resolved_rules_compatibility_id
    resolved_is_v2 = is_ruleset_v2_methodology(resolved_rules_id)
    resolved_is_v4 = is_ruleset_v4_methodology(resolved_rules_id)

    # v2.0.0-beta2 Phase 2: multi-entrant ("group") matrix generation is a
    # structurally different generation strategy (seed x layout x seat
    # assignment, over one N-entrant roster) from the pairwise loop below
    # (subject x opponent x seed x placement x orientation) -- it lives in
    # its own function and returns early, rather than threading a "group"
    # branch through every line of the pairwise loop.
    if request.group:
        raise EvaluationConfigurationError(
            "Multi-entrant evaluation is retired and cannot build a new execution matrix."
        )
    identity_version = resolved_identity_version(resolved_is_v2, False, resolved_is_v4)

    # v3 Phase 0D: placements are pure functions of arena size, so they
    # MUST be derived from this request's own resolved arena size, never
    # from `Config().arena_size` independently. A non-default arena with
    # default-derived placements would place entrants at addresses outside
    # it, which `MatchEntrant.python` silently wraps (`% arena_size`) --
    # collapsing two supposedly-separated starts onto the same cell and
    # measuring placement collision instead of the variable under test.
    #
    # v4.0.0-rc1 Phase 1: v4-seeded placement is NOT a pure function of
    # arena size alone (it also depends on each cell's own seed -- research
    # report Sec H.1 item 1), so it cannot be precomputed here the way the
    # v2 standard placements are; it is instead resolved once per seed,
    # inside the seed loop below, via `resolve_v4_seed_geometry`.
    placements: tuple[EvaluationPlacement | None, ...] = (
        standard_placements(request.resolved_arena_size) if resolved_is_v2 else (None,)
    )

    cells: list[EvaluationCell] = []
    ordinal = 0
    for role, subject_id in subjects:
        occurrence_counts: dict[tuple[str, int], int] = {}
        for opponent_index, opponent_id in enumerate(request.opponent_ids):
            for seed_index, seed in enumerate(request.seeds):
                condition_occurrence_index = occurrence_counts.get((opponent_id, seed), 0)
                occurrence_counts[(opponent_id, seed)] = condition_occurrence_index + 1
                # v4.0.0-rc1 Phase 1 (research report Sec H.1 items 1/4): one
                # seeded placement sample per seed -- the Ruleset's own
                # production placement seam, resolved once here and reused,
                # unswapped, for both orientation cells of this seed (the
                # orientation loop below swaps which *occupant* sits at each
                # resolved seat, never draws a second, independent
                # placement for the reverse orientation).
                seed_placements: tuple[EvaluationPlacement | None, ...]
                if resolved_is_v4:
                    seat_a, seat_b = resolve_v4_seed_geometry(
                        resolved_rules_id, request.resolved_arena_size, seed
                    )
                    seed_placements = (
                        EvaluationPlacement(
                            f"seeded-{seed}", subject_start=seat_a, opponent_start=seat_b
                        ),
                    )
                else:
                    seed_placements = placements
                for placement_index, placement in enumerate(seed_placements):
                    placement_id = placement.placement_id if placement is not None else "fixed"
                    subject_start = placement.subject_start if placement is not None else 0
                    opponent_start = placement.opponent_start if placement is not None else 0
                    for orientation_index, orientation in enumerate(orientations):
                        ordinal += 1
                        # v4.0.0-rc1 Phase 1 (research report Sec H.1 item 4,
                        # Sec G.3 "Option 3, paired"): under the v4-seeded
                        # methodology, the resolved seat geometry is fixed
                        # per seed and orientation decides which occupant
                        # sits at which seat -- seat A always gets
                        # `seed_placements[0]`'s first address, and swapping
                        # orientation swaps who is standing there, not where
                        # "seat A" is. Every other methodology keeps its
                        # existing role-anchored behavior (the subject
                        # starts at its own `subject_start` regardless of
                        # which physical slot/scheduler order it executes
                        # in, unaffected by this branch: `cell_subject_
                        # start`/`cell_opponent_start` equal `subject_start`/
                        # `opponent_start` unconditionally there).
                        if resolved_is_v4 and orientation == ORIENTATION_OPPONENT_FIRST:
                            cell_subject_start, cell_opponent_start = opponent_start, subject_start
                        else:
                            cell_subject_start, cell_opponent_start = subject_start, opponent_start
                        # `ordinal` is included so a repeated (role,
                        # subject_id, opponent_id, seed, placement,
                        # orientation) tuple -- explicitly preserved as
                        # distinct cells above -- still gets a distinct
                        # schedule_id. Without it, duplicate cells collide
                        # in the resume-state lookup dict
                        # (EvaluationService._resolve_from_state keys prior
                        # cells by schedule_id), which silently
                        # misattributes one duplicate's persisted state to
                        # another and can demote a legitimately never-yet-
                        # run duplicate to "corrupted". `orientation` is
                        # included in its own right too (not just via
                        # ordinal) so two cells differing only by
                        # orientation are guaranteed distinct even if the
                        # ordinal derivation ever changed (v0.9 Phase 6,
                        # Sec 9/W.1).
                        #
                        # H5 (Beta2 Phase 4.1 correction): `placement_id`
                        # does NOT unconditionally join this payload the way
                        # `orientation` does. `orientation` was already part
                        # of the pre-Beta2 (v0.9 Phase 6) historical v1
                        # schedule_id recipe -- see the pre-Beta2 source at
                        # 2076576, whose payload here is exactly
                        # {evaluation_id, role, subject_id, opponent_id,
                        # seed, orientation, ordinal}. `placement_id` is new
                        # in this phase; unlike `condition_fingerprint`'s
                        # sibling "placement" sub-key just below (added only
                        # `if placement is not None`), it was previously
                        # added here unconditionally -- "every v1 cell
                        # shares the constant 'fixed'" does not make this a
                        # hash no-op the way it would for the cell's own
                        # *value*: a hash payload with an extra key present
                        # (even holding a constant) differs from one where
                        # that key is absent entirely. That silently changed
                        # every v1 schedule_id relative to a pre-Beta2
                        # artifact resumed under this build (evaluation_id/
                        # condition_fingerprint were unaffected, since
                        # neither's payload construction has this defect),
                        # so a legacy v1 artifact lost schedule-id resume
                        # continuity and re-executed its entire matrix.
                        # Restored by mirroring `condition_fingerprint`'s
                        # own "conditionally add, never for v1" discipline:
                        # `placement_id` joins this payload only when
                        # `placement` is not `None` (v2 methodology).
                        schedule_id = _evaluation_identity.build_pairwise_schedule_id(
                            identity_version=identity_version,
                            evaluation_id=evaluation_id,
                            role=role,
                            subject_id=subject_id,
                            opponent_id=opponent_id,
                            seed=seed,
                            orientation=orientation,
                            ordinal=ordinal,
                            placement_id=placement_id,
                        )
                        label = pairwise_cell_label(
                            ordinal=ordinal,
                            role=role,
                            subject_id=subject_id,
                            opponent_id=opponent_id,
                            seed=seed,
                            placement_id=placement_id,
                            orientation=orientation,
                            include_placement=resolved_is_v2 or resolved_is_v4,
                        )
                        condition_fingerprint = None
                        if specs is not None and conditions_fingerprint is not None:
                            condition_fingerprint = (
                                _evaluation_identity.build_pairwise_condition_fingerprint(
                                    identity_version=identity_version,
                                    opponent=agent_identity(specs[opponent_id]),
                                    seed=seed,
                                    effective_conditions=conditions_fingerprint,
                                    rules_compatibility_id=rules_compatibility_id,
                                    condition_occurrence_index=condition_occurrence_index,
                                    orientation=orientation,
                                    arena_alignment_mode=arena_alignment_mode,
                                    placement_id=placement_id,
                                    subject_start=cell_subject_start,
                                    opponent_start=cell_opponent_start,
                                )
                            )
                        cells.append(
                            EvaluationCell(
                                schedule_id=schedule_id,
                                subject_role=role,
                                subject_id=subject_id,
                                opponent_id=opponent_id,
                                seed=seed,
                                artifact_dir=request.output_dir / "matches" / label,
                                opponent_index=opponent_index,
                                seed_index=seed_index,
                                matrix_ordinal=ordinal,
                                condition_occurrence_index=condition_occurrence_index,
                                condition_fingerprint=condition_fingerprint,
                                orientation=orientation,
                                orientation_index=orientation_index,
                                rules_compatibility_id=resolved_rules_id,
                                placement_id=placement_id,
                                subject_start=cell_subject_start,
                                opponent_start=cell_opponent_start,
                                placement_index=placement_index,
                            )
                        )
    return tuple(cells)


def _build_group_matrix(
    request: EvaluationRequest,
    evaluation_id: str,
    resolved_rules_id: str,
    specs: Mapping[str, AgentSpec] | None,
    conditions_fingerprint: str | None,
) -> tuple[EvaluationCell, ...]:
    """Multi-entrant ("group") matrix: seed x layout x seat assignment.

    Only ever called when ``request.group`` and ``request.is_v2_methodology``
    are both true (validated in ``EvaluationService._validate`` before this
    is reached). The full roster (``request.candidate_id`` plus every
    ``request.opponent_ids`` entry, duplicates preserved) is fielded
    together each cell -- one N-entrant match per cell, never N pairwise
    1v1 matches. Seed and layout nest outside seat assignment, matching
    the pairwise matrix's own "environment axes outside the
    permutation/orientation axis" convention.
    """

    roster = request.roster_agent_ids
    canonical_roster = request.canonical_roster
    layouts = standard_layouts(len(roster), request.resolved_arena_size)
    seat_assignments = enumerate_seat_assignments(roster)
    arena_alignment_mode = EVALUATION_ARENA_ALIGNMENT_MODE_V2_GROUP_STANDARD

    cells: list[EvaluationCell] = []
    ordinal = 0
    for seed_index, seed in enumerate(request.seeds):
        for layout_index, layout in enumerate(layouts):
            for assignment_index, assignment in enumerate(seat_assignments):
                ordinal += 1
                seat_agent_ids = assignment.seat_agent_ids
                other_agent_ids = tuple(
                    sorted(agent_id for agent_id in seat_agent_ids if agent_id != request.candidate_id)
                )
                opponent_label = "+".join(other_agent_ids) if other_agent_ids else "none"
                # `ordinal` guarantees a distinct schedule_id even under a
                # repeated (seed, layout_id, seat_agent_ids) tuple (e.g. a
                # user-supplied duplicate seed) -- the identical defensive
                # role `ordinal` already plays in the pairwise matrix above
                # (Phase 1F/v0.9 Phase 6 precedent).
                schedule_id = _evaluation_identity.build_group_schedule_id(
                    evaluation_id=evaluation_id,
                    role=CANDIDATE,
                    roster=canonical_roster,
                    seat_agent_ids=seat_agent_ids,
                    seed=seed,
                    layout_id=layout.layout_id,
                    ordinal=ordinal,
                )
                label = group_cell_label(
                    ordinal=ordinal,
                    seat_agent_ids=seat_agent_ids,
                    seed=seed,
                    layout_id=layout.layout_id,
                )
                condition_fingerprint = None
                if specs is not None and conditions_fingerprint is not None:
                    condition_fingerprint = (
                        _evaluation_identity.build_group_condition_fingerprint(
                            roster=[
                                agent_identity(specs[agent_id])
                                for agent_id in canonical_roster
                            ],
                            seat_agent_ids=seat_agent_ids,
                            seed=seed,
                            effective_conditions=conditions_fingerprint,
                            rules_compatibility_id=resolved_rules_id,
                            arena_alignment_mode=arena_alignment_mode,
                            layout_id=layout.layout_id,
                            seat_starts=layout.seat_starts,
                        )
                    )
                cells.append(
                    EvaluationCell(
                        schedule_id=schedule_id,
                        subject_role=CANDIDATE,
                        subject_id=request.candidate_id,
                        opponent_id=opponent_label,
                        seed=seed,
                        artifact_dir=request.output_dir / "matches" / label,
                        seed_index=seed_index,
                        matrix_ordinal=ordinal,
                        condition_fingerprint=condition_fingerprint,
                        rules_compatibility_id=resolved_rules_id,
                        roster_agent_ids=canonical_roster,
                        seat_agent_ids=seat_agent_ids,
                        layout_id=layout.layout_id,
                        seat_starts=layout.seat_starts,
                        seat_assignment_index=assignment_index,
                        layout_index=layout_index,
                    )
                )
    return tuple(cells)
