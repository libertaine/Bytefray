"""Frozen V6 E4 experiment definition (design review Sec I, Sec O, Sec Q).

Pure data plus pure functions: the four conditions (two controls, each the
one-field parent of one treatment), the four fields, the seeds, per-field
orientations and tick limits, the arena, the request overrides that must stay
unset, the tracked-agent fingerprints every run must reproduce, the frozen
contest-class table, and the historical E3 corpora the new controls must
reproduce. Nothing in this module executes a match.

* **Conditions.** C-E4 (``...-capture-hold-k2-disruption-slot1``: K = 2,
  lambda = 1, forward passes; historical T-E3) is the parent of the primary
  treatment T-E4 (the same with mirrored passes). C-E4K1
  (``...-disruption-slot1``: K = 1; historical T-E3K1) is the parent of the
  companion T-E4K1.
* **Fields.** F1 is the triangular round robin of the E2 agents minus
  ``e2_counter`` (Sec S-9: under lambda = 1 it behaves exactly as the greedy
  painter, so it would double-weight that archetype). F2 is their nine twin
  mirrors, both orientations -- the duplicate orientation is kept only for the
  relabel gate; the analysis unit is the seed. F2-P is F2 at 1001 ticks, one
  orientation. F4 is the E3 jam sniper against the nine agents plus the jam
  mirror, never pooled with F1 or F2.

``E4_MATRIX_DIGEST`` is the SHA-256 of the canonical definition. It is pinned
here and by the test suite, so any edit to the definition is a deliberate,
visible re-freeze -- and must never happen after treatment data exists.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
from dataclasses import dataclass
from itertools import combinations
from typing import Any

from battle_engine.ruleset_policy import (
    BYTEFRAY_RULESET_V6_RESEARCH_CAPTURE_HOLD_K2_DISRUPTION_SLOT1_ID,
    BYTEFRAY_RULESET_V6_RESEARCH_CAPTURE_HOLD_K2_DISRUPTION_SLOT1_MIRRORED_PASSES_ID,
    BYTEFRAY_RULESET_V6_RESEARCH_DISRUPTION_SLOT1_ID,
    BYTEFRAY_RULESET_V6_RESEARCH_DISRUPTION_SLOT1_MIRRORED_PASSES_ID,
    resolve_ruleset_policy,
)

from tools.research.v6.e3 import matrix as e3_matrix
from tools.research.v6.e3.entrants import JAM_SNIPER, JAM_SNIPER_TWIN
from tools.research.v6.e4 import contest_classes

E4_MATRIX_VERSION = 1

ARENA_SIZE = 512
MAX_TICKS = 1000
# F2-P: the tick-limit tick is a first-mover tick of the other seat, and the
# treatment flips the final-word seat at the tick limit (Sec S-11).
PARITY_MAX_TICKS = 1001
# Explicit 1..32 -- never the harness's eight-seed default.
SEEDS: tuple[int, ...] = tuple(range(1, 33))
QUOTA = 8

# Request-level overrides that would make "exactly one gameplay field
# differs" false (hard stop 4). Every E4 evaluation request leaves all None.
FORBIDDEN_REQUEST_OVERRIDES: tuple[str, ...] = e3_matrix.FORBIDDEN_REQUEST_OVERRIDES

# Sec S-9 / Sec O: e2_counter is excluded on a source proof, not on outcomes.
EXCLUDED_AGENTS: tuple[str, ...] = ("e2_counter",)
E4_AGENTS: tuple[str, ...] = tuple(a for a in e3_matrix.E2_AGENTS if a not in EXCLUDED_AGENTS)
twin_of = e3_matrix.twin_of
E4_TWINS: tuple[str, ...] = tuple(twin_of(agent) for agent in E4_AGENTS)

CONTROL = "control"
TREATMENT = "treatment"
PRIMARY_ARM = "primary"
COMPANION_ARM = "companion"
FORWARD = "forward"
MIRRORED = "mirrored"


@dataclass(frozen=True)
class Condition:
    condition_id: str
    ruleset_id: str
    role: str
    arm: str
    # A treatment's one-field parent (its control); None for a control.
    parent: str | None
    # The Ruleset parameters this condition must resolve to.
    capture_hold_ticks: int
    disruption_slot_limit: int
    scheduler_pass_order: str
    # A control's preserved historical corpus (E3 matrix), which it must reproduce.
    historical_condition: str | None


CONDITIONS: tuple[Condition, ...] = (
    Condition("C-E4", BYTEFRAY_RULESET_V6_RESEARCH_CAPTURE_HOLD_K2_DISRUPTION_SLOT1_ID, CONTROL, PRIMARY_ARM,
              None, 2, 1, FORWARD, "T-E3"),
    Condition("T-E4", BYTEFRAY_RULESET_V6_RESEARCH_CAPTURE_HOLD_K2_DISRUPTION_SLOT1_MIRRORED_PASSES_ID, TREATMENT,
              PRIMARY_ARM, "C-E4", 2, 1, MIRRORED, None),
    Condition("C-E4K1", BYTEFRAY_RULESET_V6_RESEARCH_DISRUPTION_SLOT1_ID, CONTROL, COMPANION_ARM,
              None, 1, 1, FORWARD, "T-E3K1"),
    Condition("T-E4K1", BYTEFRAY_RULESET_V6_RESEARCH_DISRUPTION_SLOT1_MIRRORED_PASSES_ID, TREATMENT,
              COMPANION_ARM, "C-E4K1", 1, 1, MIRRORED, None),
)
CONTROL_CONDITIONS: tuple[str, ...] = tuple(c.condition_id for c in CONDITIONS if c.role == CONTROL)
TREATMENT_CONDITIONS: tuple[str, ...] = tuple(c.condition_id for c in CONDITIONS if c.role == TREATMENT)
PRIMARY_TREATMENT = "T-E4"
PRIMARY_CONTROL = "C-E4"
COMPANION_TREATMENT = "T-E4K1"
COMPANION_CONTROL = "C-E4K1"
ARM_CONTROLS: dict[str, str] = {PRIMARY_ARM: PRIMARY_CONTROL, COMPANION_ARM: COMPANION_CONTROL}
ARM_TREATMENTS: dict[str, str] = {PRIMARY_ARM: PRIMARY_TREATMENT, COMPANION_ARM: COMPANION_TREATMENT}

# Strata (Sec O, Sec P rule 6): the standard fields form the P-PAR population;
# F2-P is the tick-limit parity stratum; F4 is the manipulation/re-disruption
# stratum. The three are never pooled.
STANDARD = "standard"
TICK_PARITY_REPLICATE = "tick_parity_replicate"
JAMMER = "jammer"
ROUND_ROBIN = "round_robin"
TWIN_MIRROR = "twin_mirror"


@dataclass(frozen=True)
class Field:
    field_id: str
    role: str
    agents: tuple[str, ...]
    pairs: tuple[tuple[str, str], ...]
    pairing: str
    max_ticks: int
    both_orientations: bool
    stratum: str
    # "round_robin": each ordered orientation is its own matchup; "twin_mirror":
    # the orientation swap is a relabelling, so the unit is the seed.
    unit: str
    # The E3 field whose preserved T-E3 / T-E3K1 corpus the controls reproduce.
    historical_field: str

    @property
    def orientations(self) -> int:
        return 2 if self.both_orientations else 1

    @property
    def expected_matches(self) -> int:
        return len(self.pairs) * len(SEEDS) * self.orientations


_MIRROR_AGENTS = tuple(name for agent in E4_AGENTS for name in (agent, twin_of(agent)))
_MIRROR_PAIRS = tuple((agent, twin_of(agent)) for agent in E4_AGENTS)
JAM_MIRROR = (JAM_SNIPER, JAM_SNIPER_TWIN)

F1 = Field("F1", "primary: triangular round robin of the nine E4 agents (E2 set minus e2_counter)",
           E4_AGENTS, tuple(combinations(E4_AGENTS, 2)), "triangular", MAX_TICKS, True, STANDARD, ROUND_ROBIN, "F1")
F2 = Field("F2", "mirrors: the nine twin mirrors; the duplicate orientation is the relabel gate only",
           _MIRROR_AGENTS, _MIRROR_PAIRS, "explicit", MAX_TICKS, True, STANDARD, TWIN_MIRROR, "F2")
F2P = Field("F2-P", "tick-limit parity replicate: the nine twin mirrors at 1001 ticks, one orientation",
            _MIRROR_AGENTS, _MIRROR_PAIRS, "explicit", PARITY_MAX_TICKS, False, TICK_PARITY_REPLICATE,
            TWIN_MIRROR, "F2-P")
F4 = Field("F4", "jammer: e3_jam_sniper against the nine E4 agents, plus the jam mirror (never pooled)",
           (JAM_SNIPER, *E4_AGENTS, JAM_SNIPER_TWIN),
           tuple((JAM_SNIPER, agent) for agent in E4_AGENTS) + (JAM_MIRROR,),
           "explicit", MAX_TICKS, True, JAMMER, ROUND_ROBIN, "F4")
FIELDS: tuple[Field, ...] = (F1, F2, F2P, F4)
FIELD_IDS: tuple[str, ...] = tuple(f.field_id for f in FIELDS)
STANDARD_FIELDS: tuple[str, ...] = tuple(f.field_id for f in FIELDS if f.stratum == STANDARD)
MIRROR_FIELDS: tuple[str, ...] = tuple(f.field_id for f in FIELDS if f.unit == TWIN_MIRROR)

# The preserved E3 corpus each new control reproduces cell for cell (Sec Q).
HISTORICAL_MATRIX_ID = e3_matrix.matrix_id()
HISTORICAL_MATRIX_DIGEST = e3_matrix.E3_MATRIX_DIGEST
HISTORICAL_FREEZE_ID = "v6-e3-freeze-v1-506811e78ad8"
HISTORICAL_GENERATION = {
    "source_commit": "6f0fd3f3fb7fc6203daba5b9e049b4a4e58e801e",
    "engine_tree": "67b73c9ae7d40209ef68e9512a58c5adfef0ac2f",
}
# The 96-match E4 parent byte-identity freeze, committed before any scheduler change.
PARENT_FREEZE = {
    "commit": "b144e1d",
    "path": "engine/tests/test_v6_e4_parent_byte_identity.py",
    "matches": 96,
}
HISTORICAL_PARENT: dict[str, str] = {
    c.condition_id: c.historical_condition for c in CONDITIONS if c.historical_condition is not None
}

# Content fingerprints (agent_revisions.agent_revision_fingerprint) of every
# agent the matrix runs, resolved from tracked sources; E3's frozen values.
AGENT_FINGERPRINTS: dict[str, str] = {
    name: e3_matrix.AGENT_FINGERPRINTS[name] for name in (*E4_AGENTS, *E4_TWINS, JAM_SNIPER, JAM_SNIPER_TWIN)
}

# Fixtures that follow the single-location enemy-core inference contract;
# the capture analyzer audits their inference (E3's set, restricted to E4).
CORE_INFERRING_AGENTS: frozenset[str] = frozenset(
    name for name in e3_matrix.CORE_INFERRING_AGENTS if name in AGENT_FINGERPRINTS
)

E4_MATRIX_DIGEST = "fc29d575dd256777a9b18c1d076716677a89a6e4eac8943ec2cefc703ceff4ef"


class MatrixDefinitionError(RuntimeError):
    """The live E4 definition or Ruleset registry differs from the frozen experiment."""


def condition(condition_id: str) -> Condition:
    for item in CONDITIONS:
        if item.condition_id == condition_id:
            return item
    raise KeyError(f"unknown E4 condition {condition_id!r}")


def field(field_id: str) -> Field:
    for item in FIELDS:
        if item.field_id == field_id:
            return item
    raise KeyError(f"unknown E4 field {field_id!r}")


def contest_class_fields() -> dict[str, tuple[tuple[str, str], ...]]:
    """The pairings the contest-class table covers: every field's pairs."""
    return {f.field_id: f.pairs for f in FIELDS}


def matches_per_condition() -> int:
    return sum(item.expected_matches for item in FIELDS)


def matches_total() -> int:
    return matches_per_condition() * len(CONDITIONS)


def matrix_definition() -> dict[str, Any]:
    """The canonical, JSON-serializable experiment definition."""
    return {
        "matrix_version": E4_MATRIX_VERSION,
        "arena_size": ARENA_SIZE,
        "seeds": list(SEEDS),
        "quota": QUOTA,
        "forbidden_request_overrides": list(FORBIDDEN_REQUEST_OVERRIDES),
        "excluded_agents": list(EXCLUDED_AGENTS),
        "conditions": [
            {
                "condition_id": c.condition_id,
                "ruleset_id": c.ruleset_id,
                "role": c.role,
                "arm": c.arm,
                "parent": c.parent,
                "capture_hold_ticks": c.capture_hold_ticks,
                "disruption_slot_limit": c.disruption_slot_limit,
                "scheduler_pass_order": c.scheduler_pass_order,
                "historical_condition": c.historical_condition,
            }
            for c in CONDITIONS
        ],
        "fields": [
            {
                "field_id": f.field_id,
                "role": f.role,
                "pairing": f.pairing,
                "agents": list(f.agents),
                "pairs": [list(pair) for pair in f.pairs],
                "max_ticks": f.max_ticks,
                "both_orientations": f.both_orientations,
                "stratum": f.stratum,
                "unit": f.unit,
                "historical_field": f.historical_field,
                "expected_matches": f.expected_matches,
            }
            for f in FIELDS
        ],
        "historical_parent": {
            "matrix_id": HISTORICAL_MATRIX_ID,
            "matrix_digest": HISTORICAL_MATRIX_DIGEST,
            "freeze_id": HISTORICAL_FREEZE_ID,
            "generation": dict(sorted(HISTORICAL_GENERATION.items())),
            "conditions": dict(sorted(HISTORICAL_PARENT.items())),
        },
        "parent_freeze": dict(sorted(PARENT_FREEZE.items())),
        "agent_fingerprints": dict(sorted(AGENT_FINGERPRINTS.items())),
        "core_inferring_agents": sorted(CORE_INFERRING_AGENTS),
        "contest_classes_sha256": contest_classes.CONTEST_CLASSES_SHA256,
        "matches_per_condition": matches_per_condition(),
        "matches_total": matches_total(),
    }


def matrix_digest() -> str:
    canonical = json.dumps(matrix_definition(), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def matrix_id() -> str:
    return f"v6-e4-matrix-v{E4_MATRIX_VERSION}-{E4_MATRIX_DIGEST[:12]}"


def verify_ruleset_registry() -> None:
    """Each condition's Ruleset resolves to its registered (K, lambda, pass order),
    and each treatment differs from its parent only in ``scheduler_pass_order``
    (and its identity)."""
    problems: list[str] = []
    policies = {c.condition_id: resolve_ruleset_policy(c.ruleset_id) for c in CONDITIONS}
    for item in CONDITIONS:
        policy = policies[item.condition_id]
        actual = (policy.capture_hold_ticks, policy.disruption_slot_limit, policy.scheduler_pass_order)
        expected = (item.capture_hold_ticks, item.disruption_slot_limit, item.scheduler_pass_order)
        if actual != expected:
            problems.append(f"{item.condition_id}: (K, lambda, pass order) {actual} != registered {expected}")
        if item.parent is not None:
            parent = policies[item.parent]
            differing = sorted(
                f.name for f in dataclasses.fields(policy) if getattr(policy, f.name) != getattr(parent, f.name)
            )
            if differing != ["ruleset_id", "scheduler_pass_order"]:
                problems.append(f"{item.condition_id} differs from {item.parent} in {differing}")
        if item.historical_condition is not None:
            historical = e3_matrix.condition(item.historical_condition)
            if historical.ruleset_id != item.ruleset_id:
                problems.append(f"{item.condition_id} does not run its historical parent's Ruleset")
    if problems:
        raise MatrixDefinitionError("E4 Ruleset registry check failed: " + "; ".join(problems))


def verify_frozen_matrix() -> None:
    """Fail closed if the definition drifted from its frozen digest, the contest
    classes changed, or the Ruleset registry no longer matches the conditions."""
    actual = matrix_digest()
    if actual != E4_MATRIX_DIGEST:
        raise MatrixDefinitionError(
            f"E4 matrix definition digest {actual} does not match the frozen "
            f"E4_MATRIX_DIGEST {E4_MATRIX_DIGEST}; the experiment definition changed."
        )
    contest_classes.load_table()
    if matches_total() != 15232:
        raise MatrixDefinitionError(f"E4 matrix count {matches_total()} != 15,232")
    verify_ruleset_registry()
