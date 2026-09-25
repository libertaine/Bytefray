"""Bytefray gameplay Ruleset identity.

A single, first-class compatibility axis for Bytefray *gameplay* semantics,
deliberately kept separate from the schema/version identifiers that
describe how those semantics are persisted, exercised, or measured. See
``docs/RULES.md`` for the full Ruleset v1 contract this identifies and
``docs/COMPATIBILITY.md`` for how it relates to the other compatibility
axes (Agent API version, artifact schema versions, evaluation methodology
fields, agent revision identity).

This module is deliberately dependency-free (standard library only) so it
can be imported by the match/runtime, artifact (result/replay), and
evaluation layers without creating a cycle -- see ``docs/COMPATIBILITY.md``.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal

# Identifies the frozen Bytefray gameplay ruleset described in full in
# docs/RULES.md: scoring formulas, ownership/last-writer semantics,
# scheduling order, mortality and match-termination rules, winner
# resolution, and the shared/VM-specific/Python-specific gameplay clauses
# documented there.
#
# Maintainers must bump this identifier (to "bytefray-rules-2", following
# the same naming pattern) only when one of those *semantics* actually
# changes -- see docs/RULES.md's "Ruleset bump policy" and
# docs/COMPATIBILITY.md's compatibility-axis table for worked examples,
# such as a scoring-formula change, an ownership/kill-attribution change, a
# scheduler-order change, or a redefined arena-addressing/observation
# meaning.
#
# This identifier does NOT change for:
#   * per-match configuration *values* (arena size, weights, tick limit,
#     seed, entrant IDs) -- the *meaning* of those fields is Ruleset-
#     defined, but the values selected for one match are not (see
#     docs/RULES.md's "Configuration values are not Ruleset identity");
#   * the Agent API v1 loading/observation/action contract or its
#     deterministic entrant-seed derivation, which is a separate,
#     independently versioned compatibility axis
#     (``battle_engine.agent_api.AGENT_API_VERSION``; see
#     ``docs/AGENT_API_V1.md``);
#   * artifact/schema wire-format changes (``battle2.result``,
#     ``battle2.replay``, ``bytefray.evaluation``, ...), which version
#     independently; and
#   * evaluation methodology changes (entrant-orientation coverage,
#     arena-alignment disclosure, ...), which are evaluation-scope
#     concerns, not gameplay.
BYTEFRAY_RULESET_ID = "bytefray-rules-1"
BYTEFRAY_RULESET_V4_ALPHA1_ID = "bytefray-rules-4-alpha1"

# v4.0.0-alpha2's experimental identity. A *separate* identity, never a
# mutation of ``bytefray-rules-4-alpha1``: alpha2 changes two gameplay
# semantics the alpha1 corpus already depends on (seed-derived entrant core
# placement in place of alpha1's deterministic evenly-spread seats, and
# round-robin intra-entrant process selection in place of alpha1's
# declaration-order priority scan), so the same agents, seed, arena, and
# seat roster can produce a different match under each. Reusing alpha1's
# identity would silently reinterpret every persisted alpha1 artifact.
# alpha1 stays executable with byte-identical historical semantics -- see
# docs/V4_ALPHA2_DESIGN.md for the full delta and the Phase 4 evidence
# behind it.
#
# Spelled ``-alpha2``, never a bare ``bytefray-rules-4``: the two changes
# are evidence-supported prerelease candidates, not a matured contract, and
# this module must never let a prerelease guess masquerade as a durable
# compatibility promise (docs/RULES.md's bump policy).
BYTEFRAY_RULESET_V4_ALPHA2_ID = "bytefray-rules-4-alpha2"

# v4.0.0-rc1 Phase 2's permanent stable identity (see
# docs/research/v4/V4_RC1_PHASE2_STABLE_CONTRACT_PROMOTION.md). Promotes
# alpha2's evidence-backed gameplay semantics -- seed-derived entrant core
# placement, round-robin intra-entrant process selection, and everything
# alpha2 left unchanged from alpha1 (Q=8, core size 8, free/uncosted reach,
# K=2 rotating scheduling, existing MOVE/READ/WRITE/observation/disruption/
# quota/scoring/termination semantics) -- into Bytefray 4.0's durable
# compatibility contract, on the pre-RC research finding that no further
# gameplay alpha is warranted (docs/research/v4/
# V4_PRE_RC_GAMEPLAY_EVALUATION_RESEARCH.md).
#
# A *separate* identity, never a mutation or alias of
# ``bytefray-rules-4-alpha2``: alpha2 stays executable with byte-identical
# historical semantics and its own persisted artifacts remain honestly
# alpha2-attributed forever, following the exact precedent
# ``bytefray-rules-2-alpha11`` -> ``bytefray-rules-2`` already set (see that
# promotion's comment above and ``docs/V2_0_ALPHA11_RULESET_V2_CANDIDATE_
# RESOLUTION.md`` Sec 25-26) -- promoting a prerelease identity's semantics
# has never meant reusing its identity string in this project. The only
# *intended* difference between ``bytefray-rules-4-alpha2`` and
# ``bytefray-rules-4`` is compatibility identity; any gameplay-observable
# difference is a defect, not a feature of the promotion.
BYTEFRAY_RULESET_V4_ID = "bytefray-rules-4"


# V6 Phase 4B's explicit variable-arena research identity (see
# docs/research/v6/V6_PHASE4_GAMEPLAY_RESEARCH_METHODOLOGY.md Sec 10.2 and
# docs/research/v6/V6_PHASE4B_ARENA_SCALING_STUDY.md). A *separate* identity,
# never a mutation or alias of ``BYTEFRAY_RULESET_V4_ID``: it exists to
# permit the one evaluation-methodology variance stable v4 forbids -- an
# arena size other than 512 cells -- as an explicit, identity-bearing
# experimental parameter, while every other gameplay semantic (scheduler,
# seeded placement, process selection, scoring, quota, reach, termination)
# stays byte-for-byte identical to stable v4 (verified live, not merely
# documented -- see ``engine/tests/test_ruleset_v6_research_scale.py``).
#
# Prefixed ``bytefray-rules-6-research-<topic>`` per the V6 research naming
# convention: an experimental Ruleset must never reuse a stable ID, and a
# mechanic ratified for release would receive its own new permanent identity
# via a frozen promotion proof, exactly as ``bytefray-rules-4-alpha2`` ->
# ``bytefray-rules-4`` already did. Deliberately not selectable from
# ``bytefray run``/``agents test``/tournament CLI surfaces or
# ``OMITTED_RULESET_CANDIDATES`` (``ruleset_policy.py``) -- only
# ``agents evaluate`` can select it, and only by explicit ``--ruleset`` name.
BYTEFRAY_RULESET_V6_RESEARCH_SCALE_ID = "bytefray-rules-6-research-scale"


# V6 Phase 4C's movement-normalized variable-arena research identity (see
# docs/research/v6/V6_PHASE4_GAMEPLAY_RESEARCH_METHODOLOGY.md Sec 10.2 and
# docs/research/v6/V6_PHASE4C_MOVEMENT_NORMALIZATION_STUDY.md). A distinct
# research identity, never an alias of stable v4 or raw research-scale: its
# sole intended gameplay difference from ``bytefray-rules-6-research-scale``
# is that maximum displacement per MOVE action scales proportionally with
# arena size according to ``max_move_delta(A) = max(64, floor(A / 8))``.
#
# At A=512, max(64, 512 // 8) = 64, preserving behavioral equivalence to the
# control arena. At larger arenas (1024, 4096, 16384, 65536), allowed movement
# stride increases (128, 512, 2048, 8192 cells) to test whether mobility/search
# latency explains the Phase 4B raw-scaling effects. Deliberately not
# selectable from ``OMITTED_RULESET_CANDIDATES`` -- requires explicit
# ``--ruleset`` selection.
BYTEFRAY_RULESET_V6_RESEARCH_SCALE_MOVE_ID = "bytefray-rules-6-research-scale-move"


# V6 Phase 4D's proportional-movement variable-arena research identity (see
# docs/research/v6/V6_PHASE4D_PROPORTIONAL_MOVEMENT_STUDY.md). A distinct
# research identity, never an alias of stable v4, raw research-scale, or
# scale-move: its sole intended gameplay difference from
# ``bytefray-rules-6-research-scale`` is that accepted MOVE operands (still
# bounded at max 64) are interpreted proportionally to arena scale from the
# 512-cell reference arena:
#     actual_delta = sign(op) * floor(abs(op) * arena_size / 512)
#
# At A=512, actual_delta == op, preserving behavioral equivalence to the
# control arena. At larger arenas (1024, 4096, 16384, 65536), displacement
# scales by 2x, 8x, 32x, 128x while holding benchmark agent source code frozen.
# Deliberately not selectable from ``OMITTED_RULESET_CANDIDATES`` -- requires
# explicit ``--ruleset`` selection.
BYTEFRAY_RULESET_V6_RESEARCH_SCALE_MOVE_PROPORTIONAL_ID = (
    "bytefray-rules-6-research-scale-move-proportional"
)


# V6 E2's multi-tick capture-hold research identity (see
# docs/research/v6/V6_E2_CAPTURE_HOLD_DESIGN_REVIEW.md Sec C/F and
# docs/research/v6/V6_E2_CAPTURE_HOLD_REGISTRATION.md). A distinct research
# identity, never an alias of stable v4 or of raw research-scale: its sole
# intended gameplay difference from ``bytefray-rules-6-research-scale`` (its
# direct parent and the E2 structural control) is that an entrant is
# core-captured only after its core has held zero self-owned cells at two
# consecutive end-of-tick capture evaluations
# (``RulesetPolicy.capture_hold_ticks == 2``) rather than at the first one.
#
# Topic ``capture-hold`` per the ``bytefray-rules-6-research-<topic>``
# convention, deliberately without ``scale`` (the topic is not arena
# scaling, although the parent policy is research-scale); the ``-k2`` suffix
# records the single varied value so a possible K=3 arm would be a sibling
# ``-k3`` rather than a rename. Deliberately not selectable from
# ``bytefray run``/``agents test``/tournament/Designer surfaces or
# ``OMITTED_RULESET_CANDIDATES`` -- only ``agents evaluate`` (or the Python
# API) can select it, and only by explicit ``--ruleset`` name.
BYTEFRAY_RULESET_V6_RESEARCH_CAPTURE_HOLD_K2_ID = (
    "bytefray-rules-6-research-capture-hold-k2"
)


# V6 E3's slot-limited disruption research identities (see
# docs/research/v6/V6_E3_SLOT_LIMITED_DISRUPTION_REGISTRATION.md). Each is a
# distinct research identity, never an alias of its parent: its sole intended
# gameplay difference from that parent is that a disruptive hit suppresses a
# victim process only for its next offer to its own entrant, still inside
# the existing one-tick disruption window, rather than for the whole rest of
# the tick (``RulesetPolicy.disruption_slot_limit == 1`` instead of ``None``).
#
# The primary treatment's parent is the E2 capture-hold identity (K=2); the
# companion's parent is ``bytefray-rules-6-research-scale`` (K=1), so the
# companion measures the same duration change without the capture hold. The
# ``-slot1`` suffix records the single varied value, so a possible second
# arm would be a sibling (``-slot2``) rather than a rename. Deliberately not
# selectable from ``bytefray run``/``agents test``/tournament/Designer
# surfaces or ``OMITTED_RULESET_CANDIDATES`` -- only ``agents evaluate`` (or
# the Python API) can select either, and only by explicit ``--ruleset`` name.
BYTEFRAY_RULESET_V6_RESEARCH_CAPTURE_HOLD_K2_DISRUPTION_SLOT1_ID = (
    "bytefray-rules-6-research-capture-hold-k2-disruption-slot1"
)
BYTEFRAY_RULESET_V6_RESEARCH_DISRUPTION_SLOT1_ID = (
    "bytefray-rules-6-research-disruption-slot1"
)


# V6 E4's mirrored-pass-order research identities (see
# docs/research/v6/V6_E4_ORDER_VS_EVALUATION_TIMING_DESIGN_REVIEW.md Sec I-K
# and docs/research/v6/V6_E4_MIRRORED_PASS_ORDER_REGISTRATION.md). Each is a
# distinct research identity, never an alias of its parent: its sole intended
# gameplay difference from that parent is that the scheduler walks the
# entrant sequence in reverse in the second half of each tick's passes
# (``RulesetPolicy.scheduler_pass_order == "mirrored"`` instead of
# ``"forward"``), so with two entrants the chunk owners run ``F L F L | L F L F``.
#
# The primary treatment's parent is the E3 primary identity (K=2); the
# companion's parent is the E3 companion (K=1). Each ID appends
# ``-mirrored-passes`` to its parent's, so it still names every gameplay
# difference from V4. Deliberately not selectable from ``bytefray run``/
# ``agents test``/tournament/Designer surfaces or
# ``OMITTED_RULESET_CANDIDATES`` -- only ``agents evaluate`` (or the Python
# API) can select either, and only by explicit ``--ruleset`` name.
BYTEFRAY_RULESET_V6_RESEARCH_CAPTURE_HOLD_K2_DISRUPTION_SLOT1_MIRRORED_PASSES_ID = (
    "bytefray-rules-6-research-capture-hold-k2-disruption-slot1-mirrored-passes"
)
BYTEFRAY_RULESET_V6_RESEARCH_DISRUPTION_SLOT1_MIRRORED_PASSES_ID = (
    "bytefray-rules-6-research-disruption-slot1-mirrored-passes"
)


# V6 E5's anchor/core-0 separation research identities (see
# docs/research/v6/V6_E5_ANCHOR_CORE_SEPARATION_DESIGN_REVIEW.md Sec F,
# docs/research/v6/V6_E5_DESIGN_REVIEW_REVISION_1.md Sec R3 and
# docs/research/v6/V6_E5_ANCHOR_CORE_SEPARATION_REGISTRATION.md). Each is a
# distinct research identity, never an alias of its parent: its sole intended
# gameplay difference from that parent is where a process with no declared
# position spawns -- one cell before its entrant's core base
# (``RulesetPolicy.initial_anchor_placement == "before_core"``, i.e.
# ``(core_base - 1) % arena_size``) instead of on it -- so an enemy WRITE to
# a never-moved process's anchor no longer also writes a core cell. It is a
# spawn rule only: movement is unrestricted, and a process that later MOVEs
# onto its own core is legal.
#
# The primary treatment's parent is the E3 primary identity (K=2); the
# companion's parent is the E3 companion (K=1). Each ID appends
# ``-anchor-before-core`` to its parent's, so it still names every gameplay
# difference from V4. Deliberately not selectable from ``bytefray run``/
# ``agents test``/tournament/Designer surfaces or
# ``OMITTED_RULESET_CANDIDATES`` -- only ``agents evaluate`` (or the Python
# API) can select either, and only by explicit ``--ruleset`` name.
BYTEFRAY_RULESET_V6_RESEARCH_CAPTURE_HOLD_K2_DISRUPTION_SLOT1_ANCHOR_BEFORE_CORE_ID = (
    "bytefray-rules-6-research-capture-hold-k2-disruption-slot1-anchor-before-core"
)
BYTEFRAY_RULESET_V6_RESEARCH_DISRUPTION_SLOT1_ANCHOR_BEFORE_CORE_ID = (
    "bytefray-rules-6-research-disruption-slot1-anchor-before-core"
)


# v0.10 Phase 4: a finite, explicit historical-alias table -- deliberately
# not a generic "normalize any evaluation-rules-N-shaped string" function.
# Each entry records a relationship actually established by git-history
# evidence (see docs/RULES.md's "Historical relationship to
# evaluation-rules-1"), not a naming-convention guess. Extend this table
# only when equivalent historical evidence justifies a new entry; an
# unrecognized string must never opportunistically normalize.
_RULESET_ALIASES: Mapping[str, str] = {
    "evaluation-rules-1": BYTEFRAY_RULESET_ID,
}


def normalize_ruleset_id(value: str) -> str:
    """Return the canonical Ruleset identity ``value`` semantically denotes.

    Maps a known historical alias (currently only the pre-v0.10
    ``"evaluation-rules-1"`` literal ``bytefray.evaluation`` wrote before
    ``EVALUATION_RULES_COMPATIBILITY_ID`` became a derived alias of this
    module's ``BYTEFRAY_RULESET_ID``) to the current spelling. An
    unrecognized value is returned unchanged -- this is intentionally a
    finite lookup, never prefix/pattern matching, so an unrelated or future
    Ruleset identity can never be silently misclassified as equivalent to
    today's.
    """

    return _RULESET_ALIASES.get(value, value)


# Confidence states for a Ruleset identity attributed to one persisted
# artifact (result/replay). Deliberately a narrower, self-contained
# vocabulary rather than importing evaluation_history's richer
# ``FieldConfidence``/``ConfidenceValue`` machinery, which depends on
# ``battle_engine.agent_evaluation`` and sits well above this
# dependency-free module in the layering (``docs/COMPATIBILITY.md``) --
# see docs/COMPATIBILITY.md's "Legacy compatibility matrix" for how these
# four states apply to each artifact/version/runtime combination.
#
#   recorded       -- the artifact itself carries an explicit ruleset_id.
#   recovered       -- the artifact predates the ruleset_id field, but its
#                       shape/version is evidence-backed as having run under
#                       BYTEFRAY_RULESET_ID (see docs/RULES.md's historical
#                       source-stability evidence).
#   unknown         -- no ruleset_id, and no evidence strong enough to
#                       recover one (e.g. a pre-v0.3 artifact, or a shape
#                       that predates the proven-stable window).
#   not_applicable  -- the artifact was never a candidate for this identity
#                       at all (a historical redcode94 result never executed
#                       under Bytefray Ruleset v1).
RulesetConfidence = Literal["recorded", "recovered", "unknown", "not_applicable"]


@dataclass(frozen=True)
class RulesetProvenance:
    """A Ruleset identity attribution together with its confidence."""

    value: str | None
    confidence: RulesetConfidence


__all__ = [
    "BYTEFRAY_RULESET_ID",
    "BYTEFRAY_RULESET_V4_ALPHA1_ID",
    "BYTEFRAY_RULESET_V4_ALPHA2_ID",
    "BYTEFRAY_RULESET_V4_ID",
    "BYTEFRAY_RULESET_V6_RESEARCH_CAPTURE_HOLD_K2_DISRUPTION_SLOT1_ANCHOR_BEFORE_CORE_ID",
    "BYTEFRAY_RULESET_V6_RESEARCH_CAPTURE_HOLD_K2_DISRUPTION_SLOT1_ID",
    "BYTEFRAY_RULESET_V6_RESEARCH_CAPTURE_HOLD_K2_DISRUPTION_SLOT1_MIRRORED_PASSES_ID",
    "BYTEFRAY_RULESET_V6_RESEARCH_CAPTURE_HOLD_K2_ID",
    "BYTEFRAY_RULESET_V6_RESEARCH_DISRUPTION_SLOT1_ANCHOR_BEFORE_CORE_ID",
    "BYTEFRAY_RULESET_V6_RESEARCH_DISRUPTION_SLOT1_ID",
    "BYTEFRAY_RULESET_V6_RESEARCH_DISRUPTION_SLOT1_MIRRORED_PASSES_ID",
    "BYTEFRAY_RULESET_V6_RESEARCH_SCALE_ID",
    "BYTEFRAY_RULESET_V6_RESEARCH_SCALE_MOVE_ID",
    "BYTEFRAY_RULESET_V6_RESEARCH_SCALE_MOVE_PROPORTIONAL_ID",
    "RulesetConfidence",
    "RulesetProvenance",
    "normalize_ruleset_id",
]
