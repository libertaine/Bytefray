"""Frozen V6 E5 experiment definition.

docs/research/v6/V6_E5_ANCHOR_CORE_SEPARATION_DESIGN_REVIEW.md Sec I and
docs/research/v6/V6_E5_DESIGN_REVIEW_REVISION_1.md Sec R1. Pure data plus pure
functions: the four conditions (two controls, each the one-field parent of one
treatment), the two fields, the seeds, orientations and tick limit, the arena,
the request overrides that must stay unset, the tracked-agent fingerprints,
the fixture exclusions and their reasons, the sweep roles the directed-contest
classification reads, and the historical E4 corpora the new controls must
reproduce. Nothing in this module executes a match.

* **Conditions.** C-E5 (``...-capture-hold-k2-disruption-slot1``: K = 2,
  lambda = 1, forward passes, core-base spawn; historical C-E4 = T-E3) is the
  parent of the primary treatment T-E5 (the same with the spawn one cell before
  the core). C-E5K1 (``...-disruption-slot1``: K = 1; historical C-E4K1 =
  T-E3K1) is the parent of the companion T-E5K1.
* **Fields.** F1 is the triangular round robin of the seven E5 fixtures, both
  orientations; F2 is their seven twin mirrors, both orientations (the
  duplicate orientation is the relabel gate only). No F2-P (E5 changes no pass
  order, so the tick-limit final-word seat cannot flip) and no F4 (it depends
  on the jam sniper, which is excluded).
* **Exclusions** (review Sec H, Revision 1 Sec R1 decision 2). ``v4_probe`` and
  ``e3_jam_sniper`` are excluded because their co-location dependence lives in
  their target sets, so the offset is not inert for them. ``e2_greedy_painter``
  and ``e2_counter`` are excluded because they write no enemy anchor and
  therefore provide no directed base contest (``e2_counter`` is also the greedy
  painter under lambda = 1, E4 review Sec S-9).

``E5_MATRIX_DIGEST`` is the SHA-256 of the canonical definition. It is pinned
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
    BYTEFRAY_RULESET_V6_RESEARCH_CAPTURE_HOLD_K2_DISRUPTION_SLOT1_ANCHOR_BEFORE_CORE_ID,
    BYTEFRAY_RULESET_V6_RESEARCH_CAPTURE_HOLD_K2_DISRUPTION_SLOT1_ID,
    BYTEFRAY_RULESET_V6_RESEARCH_DISRUPTION_SLOT1_ANCHOR_BEFORE_CORE_ID,
    BYTEFRAY_RULESET_V6_RESEARCH_DISRUPTION_SLOT1_ID,
    resolve_ruleset_policy,
)

from tools.research.v6.e4 import contest_classes as e4_contest_classes
from tools.research.v6.e4 import matrix as e4_matrix

E5_MATRIX_VERSION = 1

ARENA_SIZE = 512
MAX_TICKS = 1000
# Explicit 1..32 -- never the harness's eight-seed default.
SEEDS: tuple[int, ...] = tuple(range(1, 33))
QUOTA = 8

FORBIDDEN_REQUEST_OVERRIDES: tuple[str, ...] = e4_matrix.FORBIDDEN_REQUEST_OVERRIDES

# Review Sec H / Revision 1 decision 2, each with its registered reason.
EXCLUDED_AGENTS: dict[str, str] = {
    "v4_probe": "anchor-relative target set: the -1 offset is not inert (review Sec H, P5)",
    "e3_jam_sniper": "co-location-authored coverage (cursor skips cell 0): not inert (review Sec H)",
    "e2_greedy_painter": "writes no enemy anchor: no directed base contest (review Sec I)",
    "e2_counter": "writes no enemy anchor under lambda = 1 (E4 review Sec S-9): no directed base contest",
}
E5_AGENTS: tuple[str, ...] = tuple(a for a in e4_matrix.E4_AGENTS if a not in EXCLUDED_AGENTS)
twin_of = e4_matrix.twin_of
E5_TWINS: tuple[str, ...] = tuple(twin_of(agent) for agent in E5_AGENTS)

CONTROL = "control"
TREATMENT = "treatment"
PRIMARY_ARM = "primary"
COMPANION_ARM = "companion"
CORE_BASE = "core_base"
BEFORE_CORE = "before_core"


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
    initial_anchor_placement: str
    # A control's preserved historical corpus (E4 matrix), which it must reproduce.
    historical_condition: str | None


CONDITIONS: tuple[Condition, ...] = (
    Condition("C-E5", BYTEFRAY_RULESET_V6_RESEARCH_CAPTURE_HOLD_K2_DISRUPTION_SLOT1_ID, CONTROL, PRIMARY_ARM,
              None, 2, 1, "forward", CORE_BASE, "C-E4"),
    Condition("T-E5", BYTEFRAY_RULESET_V6_RESEARCH_CAPTURE_HOLD_K2_DISRUPTION_SLOT1_ANCHOR_BEFORE_CORE_ID, TREATMENT,
              PRIMARY_ARM, "C-E5", 2, 1, "forward", BEFORE_CORE, None),
    Condition("C-E5K1", BYTEFRAY_RULESET_V6_RESEARCH_DISRUPTION_SLOT1_ID, CONTROL, COMPANION_ARM,
              None, 1, 1, "forward", CORE_BASE, "C-E4K1"),
    Condition("T-E5K1", BYTEFRAY_RULESET_V6_RESEARCH_DISRUPTION_SLOT1_ANCHOR_BEFORE_CORE_ID, TREATMENT,
              COMPANION_ARM, "C-E5K1", 1, 1, "forward", BEFORE_CORE, None),
)
CONTROL_CONDITIONS: tuple[str, ...] = tuple(c.condition_id for c in CONDITIONS if c.role == CONTROL)
TREATMENT_CONDITIONS: tuple[str, ...] = tuple(c.condition_id for c in CONDITIONS if c.role == TREATMENT)
PRIMARY_TREATMENT = "T-E5"
PRIMARY_CONTROL = "C-E5"
COMPANION_TREATMENT = "T-E5K1"
COMPANION_CONTROL = "C-E5K1"
ARM_CONTROLS: dict[str, str] = {PRIMARY_ARM: PRIMARY_CONTROL, COMPANION_ARM: COMPANION_CONTROL}
ARM_TREATMENTS: dict[str, str] = {PRIMARY_ARM: PRIMARY_TREATMENT, COMPANION_ARM: COMPANION_TREATMENT}

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
    # "round_robin": each ordered orientation is its own matchup; "twin_mirror":
    # the orientation swap is a relabelling, so the unit is the seed.
    unit: str
    # The E4 field whose preserved C-E4 / C-E4K1 corpus the controls reproduce.
    historical_field: str

    @property
    def orientations(self) -> int:
        return 2 if self.both_orientations else 1

    @property
    def expected_matches(self) -> int:
        return len(self.pairs) * len(SEEDS) * self.orientations


_MIRROR_AGENTS = tuple(name for agent in E5_AGENTS for name in (agent, twin_of(agent)))
_MIRROR_PAIRS = tuple((agent, twin_of(agent)) for agent in E5_AGENTS)

F1 = Field("F1", "primary: triangular round robin of the seven E5 fixtures", E5_AGENTS,
           tuple(combinations(E5_AGENTS, 2)), "triangular", MAX_TICKS, True, ROUND_ROBIN, "F1")
F2 = Field("F2", "mirrors: the seven twin mirrors; the duplicate orientation is the relabel gate only",
           _MIRROR_AGENTS, _MIRROR_PAIRS, "explicit", MAX_TICKS, True, TWIN_MIRROR, "F2")
FIELDS: tuple[Field, ...] = (F1, F2)
FIELD_IDS: tuple[str, ...] = tuple(f.field_id for f in FIELDS)
RELABEL_FIELDS: tuple[str, ...] = ("F2",)

# The preserved E4 control corpus each new control reproduces cell for cell.
HISTORICAL_MATRIX_ID = e4_matrix.matrix_id()
HISTORICAL_MATRIX_DIGEST = e4_matrix.E4_MATRIX_DIGEST
HISTORICAL_FREEZE_ID = "v6-e4-freeze-v1-101a941f5e30"
# Where the preserved C-E4 / C-E4K1 corpora were generated: every field's
# provenance.json records this clean commit, whose engine/src is this tree.
HISTORICAL_GENERATION = {
    "source_commit": "e0d39b3560477e21ac619e2fd26130e25938c798",
    "engine_tree": "940a27bcf8c62268eb15210cc30c28cae4d33e50",
}
# The 96-match E5 parent byte-identity freeze, committed before any placement change.
PARENT_FREEZE = {
    "commit": "8f6717d",
    "path": "engine/tests/test_v6_e5_parent_byte_identity.py",
    "matches": 96,
}
HISTORICAL_PARENT: dict[str, str] = {
    c.condition_id: c.historical_condition for c in CONDITIONS if c.historical_condition is not None
}

AGENT_FINGERPRINTS: dict[str, str] = {name: e4_matrix.AGENT_FINGERPRINTS[name] for name in (*E5_AGENTS, *E5_TWINS)}

# Fixtures that follow the single-location enemy-core inference contract; the
# capture analyzer audits their inference (E4's set, restricted to E5).
CORE_INFERRING_AGENTS: frozenset[str] = frozenset(
    name for name in e4_matrix.CORE_INFERRING_AGENTS if name in AGENT_FINGERPRINTS
)

# Revision 1 Sec R5.6: the sweep role is E4's a-priori source role
# ``writes_enemy_non_base`` (a fixture that attacks the enemy core beyond the
# anchor, from its inferred core base). A twin has its primary's role.
SWEEP_ROLE: dict[str, bool] = {
    agent: e4_contest_classes.SOURCE_ROLES[agent].writes_enemy_non_base for agent in E5_AGENTS
}

E5_MATRIX_DIGEST = "ef7fa327ea81904c3f8e21161b3c5472837822e298a960d1b3087be8d2388d28"


class MatrixDefinitionError(RuntimeError):
    """The live E5 definition or Ruleset registry differs from the frozen experiment."""


def condition(condition_id: str) -> Condition:
    for item in CONDITIONS:
        if item.condition_id == condition_id:
            return item
    raise KeyError(f"unknown E5 condition {condition_id!r}")


def field(field_id: str) -> Field:
    for item in FIELDS:
        if item.field_id == field_id:
            return item
    raise KeyError(f"unknown E5 field {field_id!r}")


def primary_name(agent: str) -> str:
    return agent.removesuffix("_twin")


def sweeps(agent: str) -> bool:
    return SWEEP_ROLE[primary_name(agent)]


def matches_per_condition() -> int:
    return sum(item.expected_matches for item in FIELDS)


def matches_total() -> int:
    return matches_per_condition() * len(CONDITIONS)


def matrix_definition() -> dict[str, Any]:
    """The canonical, JSON-serializable experiment definition."""
    return {
        "matrix_version": E5_MATRIX_VERSION,
        "arena_size": ARENA_SIZE,
        "seeds": list(SEEDS),
        "quota": QUOTA,
        "forbidden_request_overrides": list(FORBIDDEN_REQUEST_OVERRIDES),
        "excluded_agents": dict(sorted(EXCLUDED_AGENTS.items())),
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
                "initial_anchor_placement": c.initial_anchor_placement,
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
        "sweep_role": dict(sorted(SWEEP_ROLE.items())),
        "matches_per_condition": matches_per_condition(),
        "matches_total": matches_total(),
    }


def matrix_digest() -> str:
    canonical = json.dumps(matrix_definition(), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def matrix_id() -> str:
    return f"v6-e5-matrix-v{E5_MATRIX_VERSION}-{E5_MATRIX_DIGEST[:12]}"


def verify_ruleset_registry() -> None:
    """Each condition's Ruleset resolves to its registered parameters, each
    treatment differs from its parent only in ``initial_anchor_placement`` (and
    its identity), and each control runs its historical E4 parent's Ruleset."""
    problems: list[str] = []
    policies = {c.condition_id: resolve_ruleset_policy(c.ruleset_id) for c in CONDITIONS}
    for item in CONDITIONS:
        policy = policies[item.condition_id]
        actual = (policy.capture_hold_ticks, policy.disruption_slot_limit, policy.scheduler_pass_order,
                  policy.initial_anchor_placement)
        expected = (item.capture_hold_ticks, item.disruption_slot_limit, item.scheduler_pass_order,
                    item.initial_anchor_placement)
        if actual != expected:
            problems.append(f"{item.condition_id}: (K, lambda, pass order, spawn) {actual} != registered {expected}")
        if item.parent is not None:
            parent = policies[item.parent]
            differing = sorted(
                f.name for f in dataclasses.fields(policy) if getattr(policy, f.name) != getattr(parent, f.name)
            )
            if differing != ["initial_anchor_placement", "ruleset_id"]:
                problems.append(f"{item.condition_id} differs from {item.parent} in {differing}")
        if item.historical_condition is not None:
            historical = e4_matrix.condition(item.historical_condition)
            if historical.ruleset_id != item.ruleset_id:
                problems.append(f"{item.condition_id} does not run its historical parent's Ruleset")
    if problems:
        raise MatrixDefinitionError("E5 Ruleset registry check failed: " + "; ".join(problems))


def verify_frozen_matrix() -> None:
    """Fail closed if the definition drifted from its frozen digest or the Ruleset
    registry no longer matches the conditions."""
    actual = matrix_digest()
    if actual != E5_MATRIX_DIGEST:
        raise MatrixDefinitionError(
            f"E5 matrix definition digest {actual} does not match the frozen "
            f"E5_MATRIX_DIGEST {E5_MATRIX_DIGEST}; the experiment definition changed."
        )
    if matches_total() != 7168:
        raise MatrixDefinitionError(f"E5 matrix count {matches_total()} != 7,168")
    verify_ruleset_registry()
