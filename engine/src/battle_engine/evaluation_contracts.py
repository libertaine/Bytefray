"""Stable evaluation contracts and methodology vocabulary.

This module is the low-level owner of evaluation values that can be
interpreted without constructing a matrix, executing a match, reading an
artifact, or aggregating results.  ``battle_engine.agent_evaluation`` remains
the supported compatibility facade and re-exports these objects.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any

from battle_engine.config import Config
from battle_engine.rules import BYTEFRAY_RULESET_ID, normalize_ruleset_id
from battle_engine.ruleset_policy import (
    BYTEFRAY_RULESET_V2_ID,
    BYTEFRAY_RULESET_V4_ALPHA1_ID,
    BYTEFRAY_RULESET_V4_ALPHA2_ID,
    BYTEFRAY_RULESET_V4_ID,
)

# These values are part of the evaluation contract.  They deliberately do
# not depend on agent_test's execution implementation merely because that
# module currently uses the same defaults and physical slot labels.
_DEFAULT_TICKS = 200
_TESTED_AGENT_SLOT = "A"
_OPPONENT_SLOT = "B"

SCHEMA_NAME = "bytefray.evaluation"
SCHEMA_VERSION = 4
# Bumped 2 -> 3: each planned_identities entry (candidate/baseline/each
# opponent) gains "agent_revision_id"/"agent_revision_error"
# (docs/specs/agent_revision.md Sec 5) -- an additive wire-shape change,
# versioned explicitly per AGENTS.md rather than silently changing what a
# reader can expect to find, even though it does NOT change evaluation_id's
# hash payload (see IDENTITY_VERSION below, deliberately left unchanged).
# A v2 evaluation.json is not resumable under this schema_version (Sec 5.3
# of the spec -- the same "old artifact needs a fresh evaluation" pattern
# v1 -> v2 already established); it remains fully readable via
# evaluation_history's own adapters, never mutated.
#
# Bumped 2 -> 3 (identity): agent_identity() gained "local_source_
# fingerprint" (H3), which changes the identity dict's shape/hash for every
# existing candidate/baseline/opponent -- an identity-affecting change,
# versioned explicitly per AGENTS.md rather than silently changing
# evaluation_id's wire meaning in place. agent_revision_id (above) is
# deliberately NOT folded into this hash -- see
# docs/specs/agent_revision.md Sec 1.4 -- so IDENTITY_VERSION does not bump
# again here.
#
# Bumped 3 -> 4 (schema and identity together, v0.9 Phase 6, per
# runs/research_v0.9/PHASE5_EVALUATION_METHODOLOGY_SPEC.md Sec J.1/AA.4.8):
# each cell gains "orientation"/"orientation_index" (schema-additive, and
# identity-affecting because orientation enters schedule_id/
# condition_fingerprint -- two cells differing only by orientation must
# never collide); the evaluation level gains "orientation_mode" and
# "arena_alignment_mode" (both enter _evaluation_id's payload and are
# persisted as top-level sibling fields, following the exact
# EVALUATION_RULES_COMPATIBILITY_ID sibling-key pattern below). None of
# this changes EVALUATION_RULES_COMPATIBILITY_ID itself -- it is a
# methodology/coverage change, never a gameplay-rules change.
IDENTITY_VERSION = 4

# Narrowly scoped compatibility identifier surfaced at evaluation scope, in
# the historical wire field name ``rules_compatibility_id``
# (``bytefray.evaluation``'s per-evaluation and per-execution-context
# payloads). Preserved under its original name and comparison behavior for
# compatibility with existing artifacts and tests -- its *value* now
# changes to track ``BYTEFRAY_RULESET_ID`` (still "bytefray-rules-1" today,
# since Ruleset v1 is what "evaluation-rules-1" always meant; see the
# historical note below). As of v0.10 Phase 2 this is a derived alias of
# ``battle_engine.rules.BYTEFRAY_RULESET_ID``, the first-class gameplay
# Ruleset identity (see docs/RULES.md), rather than an independently
# maintained second rules counter -- a gameplay-semantic change now
# requires exactly one Ruleset bump, not a Ruleset bump plus a separate
# evaluation-rules bump. Deliberately still separate from
# ``ProjectInfo.version``. See docs/COMPATIBILITY.md for the full
# compatibility-axis table.
#
# Historical note: for the whole period this value has existed as the
# literal string ``"evaluation-rules-1"`` (schema v1 onward), it has always
# meant exactly the gameplay semantics ``bytefray-rules-1`` now names
# explicitly -- see docs/RULES.md's "Historical relationship to
# evaluation-rules-1" section for the supporting git-history evidence.
# Evaluation artifacts persisted before this alias existed still literally
# contain the string ``"evaluation-rules-1"``, not ``"bytefray-rules-1"``;
# readers must not pretend otherwise. See docs/specs/evaluation_history.md
# Sec 4 for the original field design.
EVALUATION_RULES_COMPATIBILITY_ID = BYTEFRAY_RULESET_ID

# v0.9's only supported arena-alignment methodology (Phase 5 spec Sec AA):
# every cell in every evaluation places both entrants at the same
# untranslated arena alignment. This is evaluation-level methodology
# provenance, not a gameplay rule -- it never causes address translation
# and never changes EVALUATION_RULES_COMPATIBILITY_ID. Threaded through
# identity/comparison the same sibling-key way
# EVALUATION_RULES_COMPATIBILITY_ID already is (Sec AA.3/AA.4).
EVALUATION_ARENA_ALIGNMENT_MODE = "fixed"

# v2.0.0-beta2 Phase 1 (docs/V2_0_BETA2_PHASE1_EVALUATION_METHODOLOGY.md): the
# Ruleset-v2 1v1 evaluation methodology's own arena-alignment identifier --
# a sibling value to EVALUATION_ARENA_ALIGNMENT_MODE above, never a
# replacement for it. Selected only when a request's --ruleset resolves to
# BYTEFRAY_RULESET_V2_ID; every v1 evaluation (omitted --ruleset, or
# --ruleset bytefray-rules-1) keeps EVALUATION_ARENA_ALIGNMENT_MODE ==
# "fixed" exactly as before -- see resolve_evaluation_methodology.
EVALUATION_ARENA_ALIGNMENT_MODE_V2_STANDARD = "ruleset_v2_standard_placements"

# v2.0.0-beta2 Phase 2: the multi-entrant ("group") v2 methodology's own
# arena-alignment identifier -- a third sibling value. Deliberately
# distinct from EVALUATION_ARENA_ALIGNMENT_MODE_V2_STANDARD above (never
# reused): a 1v1 evaluation and a group evaluation must never be presented
# as comparable merely because a mode label happened to match --
# evaluation_history.comparison's _arena_alignment_id gate already fails
# closed on any string difference, generalizing correctly for free.
EVALUATION_ARENA_ALIGNMENT_MODE_V2_GROUP_STANDARD = "ruleset_v2_group_standard_layouts"

# A second, additive identity/schema recipe used only by an evaluation whose
# resolved Ruleset is BYTEFRAY_RULESET_V2_ID (Sec F/G of the design doc).
# IDENTITY_VERSION/SCHEMA_VERSION above are never bumped for this -- every
# v1 evaluation (omitted or explicit bytefray-rules-1) keeps hashing and
# persisting under identity_version/schema_version 4 exactly as before, so
# no historical evaluation_id, schedule_id, or artifact schema_version is
# affected by these constants merely existing. A v2 evaluation has no
# historical artifact to stay compatible with -- this module's evaluation
# methodology has never supported Ruleset v2 before this phase.
IDENTITY_VERSION_V2 = 5
SCHEMA_VERSION_V2 = 5

# v2.0.0-beta2 Phase 2 (docs/V2_0_BETA2_PHASE2_MULTI_ENTRANT_EVALUATION.md):
# a THIRD, additive identity/schema recipe, used only by a multi-entrant
# ("group") v2 evaluation. Every 1v1 v2 evaluation (Phase 1's own
# capability) keeps hashing/persisting under IDENTITY_VERSION_V2/
# SCHEMA_VERSION_V2 (5) exactly as Phase 1 left it -- group mode introduces
# genuinely new identity-affecting fields (roster, seat assignment, N-seat
# layout) that a pure 1v1 v2 cell never has, mirroring exactly how Phase 1
# itself justified bumping past v1's 4 rather than reusing it. No v6
# artifact has ever existed before this phase, so there is no historical
# compatibility burden for this version.
IDENTITY_VERSION_V2_GROUP = 6
SCHEMA_VERSION_V2_GROUP = 6

# Ruleset-v2's standard 1v1 seed methodology (docs/V2_0_BETA2_PHASE1_
# EVALUATION_METHODOLOGY.md Sec D): alpha.8/alpha.10 proved single-seed
# evaluation insufficient for any RNG-consuming agent (Core Tracker's win
# rate against expansion varied 25%-75% across five seeds at otherwise
# identical conditions). Used only as permanent-v2's *default* when the CLI
# is not given an explicit --seeds/--seed-range and no --preset supplies
# seeds -- an explicit seed selection always overrides it.
STANDARD_V2_SEEDS: tuple[int, ...] = (1, 2, 3, 4, 5)

# v4.0.0-rc1 Phase 1 (docs/research/v4/V4_PRE_RC_GAMEPLAY_EVALUATION_RESEARCH.md
# Sec H): the stable v4 evaluation methodology's own arena-alignment
# identifier -- a fourth sibling value to EVALUATION_ARENA_ALIGNMENT_MODE/
# _V2_STANDARD/_V2_GROUP_STANDARD above, never a replacement for any of
# them. Selected only when a request's --ruleset resolves to
# BYTEFRAY_RULESET_V4_ALPHA2_ID. Unlike the v2 methodologies, this one does
# not impose explicit placements at all: the Ruleset's own production
# placement seam (placement.resolve_direct_match_starts, the same one
# `bytefray run` uses) derives entrant cores from each cell's own seed, so
# "seeded" names what changed -- fixed/imposed placement becomes
# Ruleset-derived, deterministic placement.
EVALUATION_ARENA_ALIGNMENT_MODE_V4_SEEDED = "ruleset_v4_seeded_placements"

# A third, additive identity/schema recipe (research report Sec H.1 item 6),
# used only by an evaluation whose resolved Ruleset is
# BYTEFRAY_RULESET_V4_ALPHA2_ID. Every v1/v2/v2-group evaluation keeps
# hashing and persisting under its own existing identity_version/
# schema_version exactly as before -- this constant has no historical
# artifact to stay compatible with, since bytefray-rules-4-alpha2 evaluation
# has never been a supported product path before this phase (the v2
# methodologies explicitly reject it; see resolve_evaluation_ruleset_id's
# _V2_METHODOLOGY_RULESET_IDS, which never includes alpha2).
IDENTITY_VERSION_V4 = 7
SCHEMA_VERSION_V4 = 7

# Stable v4 evaluation methodology (research report Sec H.1 items 2/3):
# eight deterministic placement samples, and the arena size the methodology
# is pinned to -- not inherited from Config().arena_size, and not a casual
# per-run tuning knob for the *standard* methodology (an explicit
# --arena-size override that disagrees with this is rejected, never
# silently honored under the v4-seeded methodology label; see
# EvaluationService._validate). Used only as the v4-seeded methodology's
# *default* seed set when the CLI is not given an explicit --seeds/
# --seed-range and no --preset supplies seeds, mirroring exactly how
# STANDARD_V2_SEEDS is used today -- an explicit seed selection always
# overrides it.
STANDARD_V4_SEEDS: tuple[int, ...] = (1, 2, 3, 4, 5, 6, 7, 8)
STANDARD_V4_ARENA_SIZE: int = 512

CANDIDATE = "candidate"
BASELINE = "baseline"

# Entrant orientation (Phase 5 spec Sec H/I): which of the two match-
# defining agents occupies the always-first-acting physical slot for one
# cell. Named constants, mirroring CANDIDATE/BASELINE above, rather than a
# runtime string validator -- orientation values are always constructed
# internally by build_matrix from this fixed pair, never accepted as
# free-text external/CLI input (the CLI only exposes the boolean
# --single-orientation), so this is the existing project convention for a
# closed internal string enum.
ORIENTATION_CANDIDATE_FIRST = "candidate_first"
ORIENTATION_OPPONENT_FIRST = "opponent_first"
ORIENTATION_MODE_BOTH = "both"
ORIENTATION_MODE_CANDIDATE_FIRST_ONLY = "candidate_first_only"

# v4.0.0-rc1 Phase 1 (F.6 remediation, docs task Sec 4): the top-level
# `lifecycle_state` an evaluation.json's *scheduler* reaches when it stops
# running. `LIFECYCLE_STATE_FINISHED` and `LIFECYCLE_STATE_FINISHED_WITH_
# FAILURES` are both "the scheduler is done" -- the distinction is entirely
# about whether every persisted cell also executed successfully, never
# about whether more work remains to schedule. This was previously
# conflated: every non-aborted evaluation, including one in which every
# single cell failed (`bytefray-rules-2` rejecting an Agent API v2 roster,
# for example), was persisted as the bare `"finished"` a fully successful
# evaluation gets, with `"complete": true` alongside it -- a reader had to
# open `cells[]` and count statuses to discover the evaluation had not
# actually succeeded. See `_resolved_lifecycle_state` below, the one
# function both `EvaluationService.run` and
# `evaluation_artifact.write_evaluation_state` now go through for this
# decision.
LIFECYCLE_STATE_RUNNING = "running"
LIFECYCLE_STATE_FINISHED = "finished"
LIFECYCLE_STATE_FINISHED_WITH_FAILURES = "finished_with_failures"
LIFECYCLE_STATE_ABORTED = "aborted"

#: Which per-cell `EvaluationCell.status` values represent a cell that did
#: NOT execute successfully, for the purpose of the top-level lifecycle-
#: state/`complete` integrity rule above. Deliberately the same two
#: statuses `evaluation_history`'s own health-code computation already
#: flags a "finished" artifact's cells against (`HealthCode.
#: FINISHED_WITH_FAILED_CELLS`/`FINISHED_WITH_CORRUPTED_CELLS`) -- this
#: generalizes that existing read-side reasoning to the write side rather
#: than inventing a second, competing definition of "unsuccessful cell".
#: `"drift_detected"` is deliberately excluded: a drifted cell already
#: forces the whole evaluation to `LIFECYCLE_STATE_ABORTED` unconditionally
#: (see `_resolved_lifecycle_state`), a stronger and more specific signal
#: than "finished with failures" would be.
UNSUCCESSFUL_CELL_STATUSES: frozenset[str] = frozenset({"failed", "corrupted"})

#: Which `lifecycle_state` values represent "the scheduler has stopped and
#: will not resume this evaluation's cell dispatch on its own" -- used by
#: `EvaluationService.run`'s M1 no-op-resume chronology check, which must
#: treat a bare resume of an already-`LIFECYCLE_STATE_FINISHED_WITH_
#: FAILURES` artifact exactly like one of an already-`LIFECYCLE_STATE_
#: FINISHED` one (preserve the original `finished_at` rather than minting a
#: new one), since both are equally "nothing new was scheduled this run".
TERMINAL_LIFECYCLE_STATES: frozenset[str] = frozenset(
    {LIFECYCLE_STATE_FINISHED, LIFECYCLE_STATE_FINISHED_WITH_FAILURES}
)

_REAL_OUTCOMES = frozenset({"loss", "tie", "win"})

#: Which resolved rules-compatibility ids select the v2 evaluation
#: methodology. Finite and explicit, never a prefix check.
#:
#: V6 Phase 2B.9 removed ``BYTEFRAY_RULESET_V3_ALPHA1_ID`` from this set:
#: the v3 research Phase 2 bounded-locality identity it supported was
#: retired from executable registration
#: (docs/research/v6/V6_PHASE2B9_SCOPE_A_RULESET_RETIREMENT.md), so no
#: request can resolve to it any longer and its membership here was dead.
_V2_METHODOLOGY_RULESET_IDS: frozenset[str] = frozenset(
    {BYTEFRAY_RULESET_V2_ID, BYTEFRAY_RULESET_V4_ALPHA1_ID}
)

#: Which resolved rules-compatibility ids select the stable v4 seeded-
#: placement evaluation methodology (research report Sec H; promoted to the
#: permanent identity in v4.0.0-rc1 Phase 2, docs/research/v4/
#: V4_RC1_PHASE2_STABLE_CONTRACT_PROMOTION.md). Finite and explicit,
#: mirroring `_V2_METHODOLOGY_RULESET_IDS` exactly. Deliberately disjoint
#: from that set -- a Ruleset id selects at most one evaluation
#: methodology, never both -- and deliberately excludes
#: `BYTEFRAY_RULESET_V4_ALPHA1_ID`: alpha1 keeps its existing, historical
#: v2-methodology evaluation behavior (fixed standard placements) exactly as
#: it has always had it; only the identities whose defining gameplay change
#: *is* seed-derived placement -- alpha2, and now its permanent promotion
#: `BYTEFRAY_RULESET_V4_ID` -- get the methodology that actually lets them
#: place. Alpha2 remains in this *classification* table so historical schema-7
#: artifacts retain their methodology attribution; new-run validation rejects
#: that retired identity before execution.
_V4_METHODOLOGY_RULESET_IDS: frozenset[str] = frozenset(
    {BYTEFRAY_RULESET_V4_ALPHA2_ID, BYTEFRAY_RULESET_V4_ID}
)


class EvaluationConfigurationError(ValueError):
    """An invalid evaluation request or incompatible existing artifact state."""

    code = "evaluation_configuration_invalid"


def resolve_evaluation_ruleset_id(ruleset_id: str | None) -> str:
    """The ``rules_compatibility_id`` a request's optional ``--ruleset`` resolves to.

    V6 Phase 2B.12 (docs/research/v6/V6_PHASE2B12_SCOPE_C_RUNTIME_RETIREMENT.md)
    split this function's two prior uses of ``EVALUATION_RULES_COMPATIBILITY_ID``
    apart, per its own trap T-K-1: that constant remains ``bytefray-rules-1``
    forever, because it is the historical attribution value stamped on
    every evaluation artifact recorded before this phase and must keep
    meaning exactly that -- never the current control. This function's
    *new-request* omitted-``--ruleset`` default is a different concern
    (which methodology a *new* evaluation with no explicit selection
    actually runs under), and now resolves to the retained control
    ``BYTEFRAY_RULESET_V4_ID`` instead, since ``bytefray-rules-1`` can no
    longer execute at all. An explicit ``--ruleset`` is still returned
    unchanged (normalized), including a historical explicit selection such
    as ``bytefray-rules-4-alpha2`` for reproducing a prerelease methodology
    -- ``EvaluationService._validate`` is what rejects a now-unsupported
    explicit choice, not this resolver.
    """

    if ruleset_id is None:
        return BYTEFRAY_RULESET_V4_ID
    return normalize_ruleset_id(ruleset_id)


def is_ruleset_v2_methodology(rules_compatibility_id: str) -> bool:
    """Whether a resolved rules-compatibility id selects the v2 evaluation methodology.

    Methodology is tied 1:1 to Ruleset identity (design doc Sec Ruleset
    selection): only ``BYTEFRAY_RULESET_V2_ID`` gets balanced placement/
    standard-seed/capture-metric methodology. Every *historical* alpha
    Ruleset identity a result/replay artifact might still reference is
    deliberately excluded -- product-facing evaluation methodology never
    advertises an alpha Ruleset identity.
    """

    return rules_compatibility_id in _V2_METHODOLOGY_RULESET_IDS


def is_ruleset_v4_methodology(rules_compatibility_id: str) -> bool:
    """Whether a resolved rules-compatibility id selects the stable v4 methodology.

    See `is_ruleset_v2_methodology`'s docstring for the general shape of
    this question; this is its v4 sibling; Sec H.1 item 6 of
    docs/research/v4/V4_PRE_RC_GAMEPLAY_EVALUATION_RESEARCH.md is the
    accepted decision this implements.
    """

    return rules_compatibility_id in _V4_METHODOLOGY_RULESET_IDS


def resolved_arena_alignment_mode(
    is_v2_methodology: bool, group: bool = False, is_v4_methodology: bool = False
) -> str:
    if is_v4_methodology:
        return EVALUATION_ARENA_ALIGNMENT_MODE_V4_SEEDED
    if is_v2_methodology and group:
        return EVALUATION_ARENA_ALIGNMENT_MODE_V2_GROUP_STANDARD
    return (
        EVALUATION_ARENA_ALIGNMENT_MODE_V2_STANDARD
        if is_v2_methodology
        else EVALUATION_ARENA_ALIGNMENT_MODE
    )


def resolved_identity_version(
    is_v2_methodology: bool, group: bool = False, is_v4_methodology: bool = False
) -> int:
    if is_v4_methodology:
        return IDENTITY_VERSION_V4
    if is_v2_methodology and group:
        return IDENTITY_VERSION_V2_GROUP
    return IDENTITY_VERSION_V2 if is_v2_methodology else IDENTITY_VERSION


def resolved_schema_version(
    is_v2_methodology: bool, group: bool = False, is_v4_methodology: bool = False
) -> int:
    if is_v4_methodology:
        return SCHEMA_VERSION_V4
    if is_v2_methodology and group:
        return SCHEMA_VERSION_V2_GROUP
    return SCHEMA_VERSION_V2 if is_v2_methodology else SCHEMA_VERSION


def physical_slots_for_orientation(orientation: str) -> tuple[str, str]:
    """The physical ``(subject_slot, opponent_slot)`` a cell's orientation executes in.

    ``candidate_first`` (today's only historical behavior): the subject
    occupies the always-first-acting slot, exactly as every cell ever run
    before Phase 6. ``opponent_first``: the physical roles are swapped --
    the opponent occupies the first-acting slot, the subject the second --
    while every *stored* evaluation field stays expressed from the
    evaluation-role (subject/opponent) perspective, never the physical
    slot. See Phase 5 spec Sec H.1/Sec 12.

    Every place that reads real match-execution evidence keyed by physical
    slot (result/envelope score-and-outcome mapping, post-execution
    identity drift, initialization-failure classification, resumed-cell
    verification, and ``evaluation_history.verification``'s deep-verify
    path) must resolve slots through this one function rather than
    hardcoding ``TESTED_AGENT_SLOT``/``OPPONENT_SLOT`` as "subject"/
    "opponent" directly -- that hardcoding is exactly what made every
    cell ever run give the candidate role a first-mover advantage with no
    way to test the reverse (Phase 5 spec Sec C.6/C.7/B.6).
    """

    if orientation == ORIENTATION_OPPONENT_FIRST:
        return _OPPONENT_SLOT, _TESTED_AGENT_SLOT
    return _TESTED_AGENT_SLOT, _OPPONENT_SLOT


def seat_label(index: int) -> str:
    """The seat identity for position ``index`` (0-based): "A", "B", "C", ...

    Mirrors ``agent_test.TESTED_AGENT_SLOT``/``OPPONENT_SLOT``'s existing
    ``"A"``/``"B"`` convention exactly -- a seat *is* the entrant's
    ``MatchEntrant.agent_id`` for that position, and for sequential-mode
    Rulesets also its scheduler/execution-order position: production
    dispatches through ``battle_engine.scheduler.run_chunked_quota`` with
    ``chunk_size`` equal to the entrant quota and no start rotation, which
    preserves the same given-order execution ``run_sequential_quota`` used
    to provide directly, so there is no separate "execution order" axis to
    track. Ruleset v4 alpha1 is the one exception -- it uses
    ``run_chunked_quota`` with a rotating start (``chunk_size=2``), so
    declared seat order and a given tick's execution order diverge there.
    """

    if not (0 <= index < 26):
        raise ValueError(f"seat_label supports at most 26 seats, got index {index}")
    return chr(ord("A") + index)


@dataclass(frozen=True)
class EvaluationPlacement:
    """One deterministic pair of Python-entrant start addresses for a 1v1 cell.

    ``placement_id`` is a short, human-documentable label; ``subject_start``/
    ``opponent_start`` are absolute arena addresses (before ``% arena_size``
    wraparound, matching ``MatchEntrant.python``'s own convention) expressed
    from the *evaluation-role* perspective (subject/opponent) -- independent
    of which physical slot or scheduler order actually executes each role
    for a given cell. Named to mirror ``EvaluationCell.subject_id``/
    ``opponent_id`` (not ``candidate_start``/``opponent_start``): a
    baseline cell's "subject" is the baseline, not the candidate, and
    placement must describe *where the subject starts* regardless of role.
    Deliberately 1v1-scoped (two named fields, not a generic seat map) --
    see ``docs/archive/v2/V2_0_BETA2_PHASE1_EVALUATION_METHODOLOGY.md``'s multi-entrant
    extension seam for how this generalizes to N seats in Beta2 Phase 2.
    """

    placement_id: str
    subject_start: int
    opponent_start: int


@dataclass(frozen=True)
class EvaluationSeatAssignment:
    """One deterministic assignment of a roster's entrants to seats.

    ``seat_agent_ids`` is ordered by seat (index 0 = seat "A", index 1 =
    seat "B", ...) -- the agent_id occupying each seat. This is the
    identity-bearing representation of "permutation": two seat assignments
    are the same experimental condition iff this tuple is equal, which
    correctly treats a roster containing a duplicate agent id (the same
    agent occupying two seats -- self-play) as producing fewer distinct
    conditions than a fully-distinct roster's ``N!`` permutations would,
    since two seats holding the identical agent are truly indistinguishable
    for identity purposes.
    """

    seat_agent_ids: tuple[str, ...]


@dataclass(frozen=True)
class EvaluationLayout:
    """One deterministic set of per-seat start addresses for an N-entrant cell.

    ``seat_starts[i]`` is the start address for seat ``i`` (``seat_label(i)``),
    independent of which roster entrant occupies that seat this cell --
    layout and seat assignment are orthogonal identity dimensions, exactly
    as ``EvaluationPlacement``/orientation are for 1v1 (Phase 1J's
    "orientation vs. placement" separation, generalized).
    """

    layout_id: str
    seat_starts: tuple[int, ...]


@dataclass(frozen=True)
class EffectiveConditions:
    """Readable effective execution conditions, constant across one evaluation.

    ``agent_test.py`` gives no per-cell override surface for anything but
    seed/ticks (docs/specs/agent_evaluation.md Sec 2 finding 4), so every
    field below is the same for every cell in a matrix -- but it is recorded
    explicitly rather than assumed, per docs/specs/evaluation_history.md
    Sec 3 ("avoid duplicating mutable defaults without resolving them
    first").
    """

    tick_limit: int
    arena_size: int
    action_budget: int
    win_mode: str
    weights: dict[str, float | int]
    agent_api_version: int
    subject_slot: str = _TESTED_AGENT_SLOT
    opponent_slot: str = _OPPONENT_SLOT
    entrant_order: tuple[str, str] = (_TESTED_AGENT_SLOT, _OPPONENT_SLOT)
    runtime_kind: str = "python"
    supervision: str = "unsupervised"
    tracing: str = "untraced"


def effective_conditions_for(
    ticks: int,
    agent_api_version: int,
    arena_size: int | None = None,
    instr_per_tick: int | None = None,
    kill_weight: float | None = None,
) -> EffectiveConditions:
    """Resolve one evaluation's effective conditions.

    v3 Phase 0D: ``arena_size``/``instr_per_tick`` are the two controlled
    experimental variables Phase 1's arena-size-vs-action-budget research
    needs to vary (docs/V3_PHASE0_RESEARCH_BASELINE.md). ``None`` -- the
    default, and what every pre-Phase-0 caller passes -- resolves to
    ``Config()``'s own field default, which is exactly the literal this
    function already hardcoded, so an omitted-parameter call returns a
    byte-identical ``EffectiveConditions`` and therefore a byte-identical
    ``evaluation_id``/``effective_conditions_fingerprint``.

    No new identity axis is introduced by this change: both values were
    *already* fields of ``EffectiveConditions``, already hashed into
    ``_evaluation_id``'s ``"effective_conditions"`` key, already persisted
    in ``evaluation.json``, and already part of ``canonical_match_id``'s
    ``reproducibility`` block. Phase 0 makes them *variable*, not
    *identity-bearing* -- they always were.

    v3 Phase 3: ``kill_weight`` is a third controlled variable, of exactly
    the same kind and by exactly the same reasoning -- ``EffectiveConditions
    .weights`` already exists and is already hashed/persisted (it has
    always carried ``asdict(Config().weights)``); this only makes the
    ``kill`` entry of that already-identity-bearing dict variable. ``None``
    reproduces ``Config()``'s own default ``Weights`` byte for byte, so
    every existing caller (which never passes this parameter) is
    unaffected. Only ``weights.kill`` varies; ``alive``/``territory``/
    ``territory_bucket`` stay at their ``Weights`` defaults, since Phase 3
    tests one scoring lever, not a general reweighting facility.
    """

    defaults = Config()
    resolved_weights = (
        defaults.weights if kill_weight is None else replace(defaults.weights, kill=kill_weight)
    )
    return EffectiveConditions(
        tick_limit=ticks,
        arena_size=defaults.arena_size if arena_size is None else arena_size,
        action_budget=defaults.instr_per_tick if instr_per_tick is None else instr_per_tick,
        win_mode=defaults.win_mode,
        weights=asdict(resolved_weights),
        agent_api_version=agent_api_version,
    )


@dataclass(frozen=True)
class ExecutionContext:
    """One observed runtime environment a v2 cell may be attributable to.

    docs/specs/evaluation_history.md Sec 6: every newly executed cell must be
    attributable to an entry in ``execution_contexts``; a resumed/trusted
    cell keeps whatever context it was originally recorded under.
    """

    context_id: str
    bytefray_version: str
    agent_api_version: int
    python_version: str
    result_schema_version: int
    replay_schema_version: int
    rules_compatibility_id: str
    first_used_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class EvaluationRequest:
    candidate_id: str
    opponent_ids: tuple[str, ...]
    seeds: tuple[int, ...]
    output_dir: Path
    baseline_id: str | None = None
    ticks: int = _DEFAULT_TICKS
    resume: bool = True
    retry_failures: bool = False
    data_root: Path | None = None
    # v0.9 Phase 6 (Phase 5 spec Sec H.3/I.2): both entrant orientations run
    # by default -- a default that still only ran candidate_first would
    # reproduce the exact "misleading default methodology" trap the shipped
    # `adaptive` starter agent's own first-mover exploit (spec Sec B.6)
    # demonstrates is real. False restores exactly today's historical,
    # single-orientation (candidate_first-only) behavior and matrix size.
    both_orientations: bool = True
    # v1.6 Phase 2: bounded subprocess-worker parallelism across independent
    # EvaluationCells (docs/V1_6_PHASE2_PARALLEL_EVALUATION.md). Default 1 is
    # the serial-equivalent path -- deliberately conservative, matching this
    # module's existing default-conservatism precedent (--seeds). Never part
    # of _evaluation_id's hash payload (see _evaluation_id below): worker
    # count must never affect what an evaluation *means*, only how fast it
    # runs.
    workers: int = 1
    # Explicit Ruleset selection for `agents evaluate`. For new requests,
    # `None` resolves to stable v4; retired explicit identities are preserved
    # as data long enough for validation to reject them clearly, never execute.
    ruleset_id: str | None = None
    # v2.0.0-beta2 Phase 2: opt into multi-entrant ("group") methodology --
    # `candidate_id` plus every `opponent_ids` entry are fielded TOGETHER as
    # one N-entrant roster each cell, instead of Phase 1's pairwise "one
    # cell per opponent" matrix. Default False preserves every existing
    # evaluation's exact pairwise behavior, v1 and v2 1v1 alike, completely
    # unchanged. Requires v2 methodology (`is_v2_methodology`) -- validated
    # in `EvaluationService._validate`, never silently ignored.
    group: bool = False
    # v3 Phase 0 (docs/V3_PHASE0_RESEARCH_BASELINE.md): the two controlled
    # experimental variables Phase 1's arena-size-vs-action-budget research
    # varies. `None` (the default) resolves to `Config()`'s own field
    # default -- exactly the value this evaluation path already used
    # unconditionally -- so every omitted-parameter evaluation keeps its
    # exact historical behavior, matrix shape, and evaluation_id, byte for
    # byte. These are per-match *configuration*, not Ruleset semantics
    # (docs/RULES.md, "Configuration values are not Ruleset identity"), so
    # selecting one never implies a Ruleset/Agent-API/schema bump; they are
    # nevertheless fully identity-bearing, because `EffectiveConditions`
    # already carries both into `_evaluation_id` and
    # `effective_conditions_fingerprint`.
    arena_size: int | None = None
    instr_per_tick: int | None = None
    # v3 research Phase 2's experimental bounded-locality reach. V6
    # Phase 2B.9 retired every Ruleset identity that supported bounded
    # locality, so `_validate` now rejects any non-`None` value
    # unconditionally rather than silently ignoring it (an evaluation that
    # names a reach and does not get one would produce a corpus whose
    # conditions its own artifacts misdescribe). Kept as a field, rather
    # than removed, so existing callers need no change.
    locality_reach: int | None = None
    # v3 research Phase 3 (docs/V3_PHASE3_OFFENSE_PAYOFF_CHARACTERIZATION.md):
    # the one controlled scoring variable this phase tests. `None` (the
    # default, and what every pre-Phase-3 caller passes) resolves to
    # `Config()`'s own `Weights.kill` default -- exactly the value this
    # evaluation path already used unconditionally -- so every
    # omitted-parameter evaluation keeps its exact historical behavior and
    # evaluation_id, byte for byte. Per-match configuration, not Ruleset
    # semantics (docs/RULES.md, "Configuration values are not Ruleset
    # identity"), but already identity-bearing: `EffectiveConditions.weights`
    # already carries it into `_evaluation_id`/`effective_conditions_
    # fingerprint`, and `Config.weights` already carries it into
    # `canonical_match_id`'s `reproducibility` block.
    kill_weight: float | None = None
    scheduler_chunk_size: int | None = None
    scheduler_rotate_start: bool = False


    @property
    def resolved_locality_reach(self) -> int | None:
        """The reach this request's cells actually execute under.

        Always `None`: V6 Phase 2B.9 retired every Ruleset identity that
        supported bounded-locality addressing. Kept as a stable named seam
        rather than inlined at each call site, so every locality-gated key
        downstream (identity payloads, conditions fingerprint, disclosure)
        stays absent without those call sites needing to change, and so a
        future locality-capable Ruleset has one obvious place to restore
        this resolution.
        """

        return None

    @property
    def resolved_arena_size(self) -> int:
        """The arena size this evaluation actually runs at.

        The single authority for arena size across matrix generation
        (placements/layouts are pure functions of it), identity, execution,
        and display -- never `Config().arena_size` read independently at
        each site, which is exactly how a matrix could otherwise be built
        for one arena and executed in another.

        v4.0.0-rc1 Phase 1 (research report Sec H.1 item 3): an omitted
        ``arena_size`` under the stable v4 methodology resolves to the
        pinned ``STANDARD_V4_ARENA_SIZE`` (512), never the inherited
        ``Config().arena_size`` default (4096) every other methodology
        still falls back to -- the whole point of pinning the arena is that
        it must not silently track an unrelated global default.
        ``EvaluationService._validate`` already rejects any *explicit*
        ``arena_size`` that disagrees with the pin for a v4-methodology
        request, so by the time this property is read on a validated
        request, ``self.arena_size`` is either ``None`` or already exactly
        ``STANDARD_V4_ARENA_SIZE`` here.
        """

        if self.arena_size is not None:
            return self.arena_size
        if self.is_v4_methodology:
            return STANDARD_V4_ARENA_SIZE
        return Config().arena_size

    @property
    def resolved_instr_per_tick(self) -> int:
        """The per-tick action budget this evaluation actually runs at."""

        return Config().instr_per_tick if self.instr_per_tick is None else self.instr_per_tick

    @property
    def resolved_kill_weight(self) -> float:
        """The ``weights.kill`` value this evaluation's matches actually score with."""

        return Config().weights.kill if self.kill_weight is None else self.kill_weight

    @property
    def orientation_mode(self) -> str:
        return ORIENTATION_MODE_BOTH if self.both_orientations else ORIENTATION_MODE_CANDIDATE_FIRST_ONLY

    @property
    def resolved_rules_compatibility_id(self) -> str:
        return resolve_evaluation_ruleset_id(self.ruleset_id)

    @property
    def is_v2_methodology(self) -> bool:
        return is_ruleset_v2_methodology(self.resolved_rules_compatibility_id)

    @property
    def is_v4_methodology(self) -> bool:
        return is_ruleset_v4_methodology(self.resolved_rules_compatibility_id)

    @property
    def roster_agent_ids(self) -> tuple[str, ...]:
        """The full multi-entrant roster (candidate + every opponent), in
        request order, preserving duplicates -- meaningful only when
        ``group`` is True. See ``canonical_roster`` for the identity form.
        """

        return (self.candidate_id, *self.opponent_ids)

    @property
    def canonical_roster(self) -> tuple[str, ...]:
        """The roster's canonical (sorted, order-independent) identity form.

        Roster *membership* is order-independent -- "Claimer+Core Defender
        +Reactive Core Defender" is the same roster regardless of which
        order the user listed them in; seat *assignment* (the ordered,
        permutation-bearing axis) is a separate identity dimension, carried
        per cell by ``EvaluationCell.seat_agent_ids``, never here. Sorting
        preserves duplicate agent ids correctly (a self-play roster's
        repeat count survives sorting).
        """

        return tuple(sorted(self.roster_agent_ids))


@dataclass(frozen=True)
class EvaluationCell:
    schedule_id: str
    subject_role: str
    subject_id: str
    opponent_id: str
    seed: int
    artifact_dir: Path
    status: str = "pending"
    outcome: str | None = None
    match_id: str | None = None
    result_id: str | None = None
    ticks_run: int | None = None
    score_subject: float | None = None
    score_opponent: float | None = None
    territory_subject: float | None = None
    territory_opponent: float | None = None
    error_code: str | None = None
    error_message: str | None = None
    # Duplicate occurrence coordinates (docs/specs/evaluation_history.md
    # Sec 8) -- distinct from schedule_id, survive candidate-source changes
    # across evaluations, and are what cross-evaluation alignment uses.
    opponent_index: int = -1
    seed_index: int = -1
    matrix_ordinal: int = 0
    condition_occurrence_index: int = 0
    # Execution provenance and comparison support (Sec 6, Sec 14).
    execution_context_id: str | None = None
    condition_fingerprint: str | None = None
    # v0.9 Phase 6 (Phase 5 spec Sec I.2): which evaluation-defining agent
    # occupies the always-first-acting physical slot for this specific
    # cell -- a matrix axis, structurally a sibling of seed/opponent_index,
    # never folded into EffectiveConditions (Sec I.1). Two cells differing
    # only by orientation must never collide in identity (Sec 9/W.1-2);
    # `orientation_index` (0 or 1) is the duplicate-occurrence-style
    # coordinate build_matrix assigns alongside it, mirroring
    # condition_occurrence_index's own role for repeated (opponent, seed)
    # tuples.
    orientation: str = ORIENTATION_CANDIDATE_FIRST
    orientation_index: int = 0
    # v2.0.0-beta2 Phase 1 (design doc Sec Placement/Sec Identity): which
    # deterministic start-address pair this cell executed under, and this
    # cell's own resolved Ruleset -- matrix axes, structurally siblings of
    # seed/orientation, mirroring orientation's own default-sentinel
    # pattern exactly. Every v1 cell (the overwhelming majority, forever)
    # gets the fixed historical sentinel values below; only a v2-methodology
    # cell (`rules_compatibility_id == BYTEFRAY_RULESET_V2_ID`) ever sets
    # `placement_id` to anything other than "fixed" or either start to a
    # nonzero address. `rules_compatibility_id` is stored per cell (not
    # read from a module constant at execution time) because `execute_cell`
    # must stay a pure function of its own arguments (v1.6 Phase 2's worker-
    # purity invariant) -- see evaluation_cell_execution.execute_cell.
    rules_compatibility_id: str = EVALUATION_RULES_COMPATIBILITY_ID
    placement_id: str = "fixed"
    subject_start: int = 0
    opponent_start: int = 0
    placement_index: int = 0
    # v2.0.0-beta2 Phase 2 (design doc Sec Identity): multi-entrant
    # ("group") axes -- matrix-axis siblings of placement_id/orientation
    # above, mirroring their identical default-sentinel pattern. Every
    # non-group cell (every 1v1 cell ever scheduled, v1 or v2, forever)
    # gets the empty-tuple/empty-string sentinels below; only a
    # `request.group=True` cell ever populates them. `roster_agent_ids` is
    # the canonical (sorted) roster; `seat_agent_ids` is the ordered
    # per-seat assignment for this specific cell (also its scheduler/
    # execution order -- see `seat_label`); `layout_id`/`seat_starts`
    # mirror `placement_id`/(`subject_start`,`opponent_start`)'s role, for
    # N seats instead of 2. `opponent_id` is still populated for a group
    # cell (every OTHER roster agent id, canonically joined) but is
    # display/artifact-labeling only there -- never identity-bearing;
    # `seat_agent_ids`/`roster_agent_ids` are authoritative.
    roster_agent_ids: tuple[str, ...] = ()
    seat_agent_ids: tuple[str, ...] = ()
    layout_id: str = ""
    seat_starts: tuple[int, ...] = ()
    seat_assignment_index: int = 0
    layout_index: int = 0

    @property
    def is_group(self) -> bool:
        return bool(self.roster_agent_ids)

    @property
    def subject_seat(self) -> str | None:
        """The seat label the subject occupies in this group cell, or
        ``None`` for a non-group cell.

        If ``subject_id`` occupies more than one seat (self-play, a
        duplicate agent id in the roster), the first (lowest-index)
        occurrence is used, deterministically -- a documented Phase 2
        simplification for reporting the subject's own outcome; every
        seat's real result remains fully recoverable from this cell's own
        persisted ``result.json`` regardless.
        """

        if not self.is_group:
            return None
        try:
            index = self.seat_agent_ids.index(self.subject_id)
        except ValueError:
            return None
        return seat_label(index)

    @property
    def is_scored(self) -> bool:
        return self.status == "completed" and self.outcome in _REAL_OUTCOMES


@dataclass(frozen=True)
class SubjectAggregate:
    subject_role: str
    subject_id: str
    matches_played: int = 0
    wins: int = 0
    losses: int = 0
    ties: int = 0
    subject_init_failures: int = 0
    opponent_init_failures: int = 0
    failed: int = 0
    score_total: float = 0.0
    score_avg: float = 0.0
    # v2.0.0-beta2 Phase 3 (design doc Sec 34): ``None`` for a group scope
    # rather than a silently-computed number -- "opponent" is not a single
    # entrant in a >2-entrant cell, so `score_opponent`/`territory_opponent`
    # are always `None` on a group `EvaluationCell` (Phase 2), and treating
    # that as "opponent score/territory = 0" here would produce a number
    # that *looks* like a real differential but is actually just the raw
    # score/territory relabeled. A non-group scope's arithmetic is
    # completely unchanged (Sec 34: "existing pairwise differential fields
    # may remain None for group cells... do not overload old names with
    # new semantics").
    score_differential_avg: float | None = 0.0
    ticks_avg: float = 0.0
    territory_avg: float = 0.0
    territory_differential_avg: float | None = 0.0
    # v0.9 Phase 6 (Phase 5 spec Sec K.2): which cells this aggregate
    # summarizes -- "all" (pooled across both orientations, today's only
    # view before Phase 6), "candidate_first", or "opponent_first". Never
    # averaged away: all three are always computed side by side (see
    # `all_subject_aggregates`) so a regression hidden by pooling (e.g.
    # candidate wins every candidate-first cell but loses every
    # opponent-first cell) stays visible without extra author effort.
    orientation_scope: str = "all"

    @property
    def win_rate_display(self) -> str:
        if self.matches_played == 0:
            return "0/0 (n/a)"
        pct = 100.0 * self.wins / self.matches_played
        return f"{self.wins}/{self.matches_played} ({pct:.0f}%)"


@dataclass(frozen=True)
class ComparisonEntry:
    opponent_id: str
    seed: int
    classification: str  # "improved" | "regressed" | "unchanged" | "inconclusive"
    candidate_outcome: str | None = None
    baseline_outcome: str | None = None
    candidate_score: float | None = None
    baseline_score: float | None = None
    candidate_score_differential: float | None = None
    baseline_score_differential: float | None = None
    candidate_territory: float | None = None
    baseline_territory: float | None = None
    reason: str | None = None
    # A repeated (opponent_id, seed) pair produces multiple ComparisonEntry
    # rows (see compare_candidate_baseline below); these carry each row's
    # exact paired cell identity so a consumer (the Designer results dialog)
    # can resolve the specific duplicate a row was built from instead of
    # re-deriving it from (opponent_id, seed) alone, which -- absent this --
    # always resolves to the *first* matching duplicate regardless of which
    # row was actually selected.
    candidate_schedule_id: str | None = None
    baseline_schedule_id: str | None = None
    # v0.9 Phase 6 (Phase 5 spec Sec K.3): part of the grouping key now, so
    # it must be visible on the entry itself -- without it, a
    # both_orientations comparison would show two rows with an identical
    # "opponent=X seed=Y" header that are actually different orientation
    # pairs, with no way to tell them apart.
    orientation: str = ORIENTATION_CANDIDATE_FIRST
    # v2.0.0-beta2 Phase 1 (design doc Sec Compare/Sec Q): part of the
    # grouping key now, mirroring orientation immediately above -- without
    # it, a v2 both_orientations-and-placements comparison could pair a
    # candidate's "opposed" cell against a baseline's "quarter" cell for
    # the "same" nominal (opponent, seed, orientation), silently
    # attributing a placement effect to a candidate/baseline difference
    # that isn't real. Always "fixed" for v1 comparisons.
    placement_id: str = "fixed"


@dataclass(frozen=True)
class EvaluationResult:
    evaluation_id: str
    request: EvaluationRequest
    cells: tuple[EvaluationCell, ...]
    aggregates: tuple[SubjectAggregate, ...]
    comparison: tuple[ComparisonEntry, ...]
    state_path: Path

    @property
    def failed_cells(self) -> tuple[EvaluationCell, ...]:
        return tuple(cell for cell in self.cells if cell.status == "failed")

    @property
    def corrupted_cells(self) -> tuple[EvaluationCell, ...]:
        return tuple(cell for cell in self.cells if cell.status == "corrupted")

    @property
    def drift_cells(self) -> tuple[EvaluationCell, ...]:
        return tuple(cell for cell in self.cells if cell.status == "drift_detected")


def _resolved_lifecycle_state(
    cells: Sequence[EvaluationCell], drift: Mapping[str, Any] | None
) -> str:
    """The truthful top-level terminal state for one fully-scheduled evaluation write.

    F.6 remediation (docs task Sec 4): "the scheduler finished attempting
    every cell" and "the evaluation succeeded" are different claims, and an
    evaluation must never be represented as successfully complete merely
    because the former is true. Source drift is checked first and wins
    unconditionally -- an aborted evaluation is already an unambiguous,
    stronger signal and must never be relabeled by this function. Otherwise:
    every persisted cell must have executed successfully (`status` not in
    `UNSUCCESSFUL_CELL_STATUSES`) for the truthful state to be
    `LIFECYCLE_STATE_FINISHED`; if even one has not -- whether every cell
    failed or only some did -- this evaluation's scheduling completed but
    its outcome did not, and the persisted state says so explicitly rather
    than reusing the same string a fully successful evaluation gets.

    Applies uniformly to every methodology (v1/v2/v2-group/v4) and to a
    bare resume that reconstructs a historically-failed cell from prior
    state without re-executing anything -- it is a pure function of
    ``cells``' own persisted status, never of whether *this* invocation did
    any new work, so a resumed evaluation can never convert historical
    failed cells into a successful aggregate merely because no work
    remained to schedule.
    """

    if drift is not None:
        return LIFECYCLE_STATE_ABORTED
    if any(cell.status in UNSUCCESSFUL_CELL_STATUSES for cell in cells):
        return LIFECYCLE_STATE_FINISHED_WITH_FAILURES
    return LIFECYCLE_STATE_FINISHED
