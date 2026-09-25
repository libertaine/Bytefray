"""The frozen E6 structural matrix definition (no seed values).

docs/research/v6/V6_E6_PRICED_SENSING_PREREGISTRATION.md Sec 2-3 and 9.
Pure data plus pure functions: the four conditions, the population, the two
fields and their counts, the arena, tick limit and radius, the request
overrides that must stay unset, the family fingerprints and the parent
byte-identity freeze. Nothing here executes a match, and nothing here names
a seed. The matrix has 32 seed *positions*; their values are generated only
after this identity is frozen (PR Sec 9, step 1) and are bound to it by the
execution identity (``seeds.execution_identity``).

* **Structural matrix identity:** ``v6-e6-matrix-v2-<first 12 hex of
  STRUCTURAL_DIGEST>``, where ``STRUCTURAL_DIGEST`` is the SHA-256 of
  ``structural_definition()`` in canonical JSON. It is pinned here and by
  the tests, so any edit is a deliberate, visible re-freeze, and none may
  happen once a seed exists.
* **Execution matrix identity:** ``execution_identity(seed_commitment)``.

Version 2 is the structure after amendment 1
(docs/research/v6/V6_E6_AMENDMENT_1_FAMILY_CORRECTIONS.md): the same
conditions, fields, counts and members, with the corrected family policy, and
so new package fingerprints. Version 1 (``SUPERSEDED_STRUCTURAL_MATRIX``) was
superseded before any seed existed.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
from dataclasses import dataclass
from itertools import combinations
from typing import Any

from battle_engine.ruleset_policy import (
    BYTEFRAY_RULESET_V6_RESEARCH_DISRUPTION_SLOT1_ID,
    BYTEFRAY_RULESET_V6_RESEARCH_DISRUPTION_SLOT1_SENSING_R32_ID,
    BYTEFRAY_RULESET_V6_RESEARCH_SCALE_ID,
    BYTEFRAY_RULESET_V6_RESEARCH_SENSING_R32_ID,
    resolve_ruleset_policy,
)

from tools.research.v6.e2 import matrix as e2_matrix
from tools.research.v6.e6 import family, seeds

E6_MATRIX_VERSION = 2
ARENA_SIZE = 512
MAX_TICKS = 1000
SEED_COUNT = 32
QUOTA = 8
DETECTION_RADIUS = 32
FORBIDDEN_REQUEST_OVERRIDES: tuple[str, ...] = e2_matrix.FORBIDDEN_REQUEST_OVERRIDES

CONTROL = "control"
TREATMENT = "treatment"
PRIMARY_ARM = "primary"
COMPANION_ARM = "companion"


@dataclass(frozen=True)
class Condition:
    condition_id: str
    ruleset_id: str
    role: str
    arm: str
    parent: str | None  # a treatment's one-field parent (its control)
    detection_radius: int | None
    disruption_slot_limit: int | None


CONDITIONS: tuple[Condition, ...] = (
    Condition("C-E6", BYTEFRAY_RULESET_V6_RESEARCH_SCALE_ID, CONTROL, PRIMARY_ARM, None, None, None),
    Condition("T-E6", BYTEFRAY_RULESET_V6_RESEARCH_SENSING_R32_ID, TREATMENT, PRIMARY_ARM, "C-E6",
              DETECTION_RADIUS, None),
    Condition("C-E6L", BYTEFRAY_RULESET_V6_RESEARCH_DISRUPTION_SLOT1_ID, CONTROL, COMPANION_ARM, None, None, 1),
    Condition("T-E6L", BYTEFRAY_RULESET_V6_RESEARCH_DISRUPTION_SLOT1_SENSING_R32_ID, TREATMENT, COMPANION_ARM,
              "C-E6L", DETECTION_RADIUS, 1),
)
CONTROL_CONDITIONS: tuple[str, ...] = tuple(c.condition_id for c in CONDITIONS if c.role == CONTROL)
TREATMENT_CONDITIONS: tuple[str, ...] = tuple(c.condition_id for c in CONDITIONS if c.role == TREATMENT)
ARMS: dict[str, tuple[str, str]] = {PRIMARY_ARM: ("C-E6", "T-E6"), COMPANION_ARM: ("C-E6L", "T-E6L")}

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
    unit: str

    @property
    def orientations(self) -> int:
        return 2 if self.both_orientations else 1

    @property
    def expected_matches(self) -> int:
        return len(self.pairs) * SEED_COUNT * self.orientations


PRIMARIES: tuple[str, ...] = tuple(family.package_id(member) for member in family.OPPONENTS)
TWINS: tuple[str, ...] = tuple(family.package_id(member, "twin") for member in family.OPPONENTS)
F1 = Field("F1", "every ordered pair of distinct members (triangular round robin, both orientations)",
           PRIMARIES, tuple(combinations(PRIMARIES, 2)), "triangular", MAX_TICKS, True, ROUND_ROBIN)
F2 = Field("F2", "every twin mirror, both orientations (the swap is a relabeling: D-7)",
           tuple(name for pair in zip(PRIMARIES, TWINS, strict=True) for name in pair),
           tuple(zip(PRIMARIES, TWINS, strict=True)), "explicit", MAX_TICKS, True, TWIN_MIRROR)
FIELDS: tuple[Field, ...] = (F1, F2)

#: The I-0 parent byte-identity freeze, committed before any engine change (D-3).
PARENT_FREEZE = {"commit": "ddf0eda", "path": "engine/tests/test_v6_e6_parent_byte_identity.py", "matches": 84}

STRUCTURAL_DIGEST = "7de29a4a6954216ea215bf8cda3aa792fb62d69ea084bbe2bfd4b42fad6fbfc2"
#: Structural matrix v1: frozen at Checkpoint A, superseded by amendment 1
#: before any seed existed. Never executed.
SUPERSEDED_STRUCTURAL_MATRIX = {
    "id": "v6-e6-matrix-v1-cd040eac42ef",
    "digest": "cd040eac42ef6554f3d6c0faf4a7fbe83dd963d416cfad8e7f9c4aa8630f13a6",
}


class MatrixDefinitionError(RuntimeError):
    """The live E6 definition or Ruleset registry differs from the frozen experiment."""


def condition(condition_id: str) -> Condition:
    for item in CONDITIONS:
        if item.condition_id == condition_id:
            return item
    raise KeyError(f"unknown E6 condition {condition_id!r}")


def field(field_id: str) -> Field:
    for item in FIELDS:
        if item.field_id == field_id:
            return item
    raise KeyError(f"unknown E6 field {field_id!r}")


def matches_per_condition() -> int:
    return sum(item.expected_matches for item in FIELDS)


def matches_total() -> int:
    return matches_per_condition() * len(CONDITIONS)


def structural_definition() -> dict[str, Any]:
    """The canonical, JSON-serializable structure: everything but the seed values."""
    return {
        "matrix_version": E6_MATRIX_VERSION,
        "arena_size": ARENA_SIZE,
        "max_ticks": MAX_TICKS,
        "seed_count": SEED_COUNT,
        "seed_protocol": {"generator": "secrets.randbelow(2**53)", "bound": seeds.SEED_BOUND,
                          "encoding": "decimal ASCII, one per line, LF, trailing LF, generation order",
                          "commitment": "SHA-256 hex of the encoded bytes",
                          "execution_identity_prefix": seeds.EXECUTION_IDENTITY_PREFIX},
        "quota": QUOTA,
        "detection_radius": DETECTION_RADIUS,
        "forbidden_request_overrides": list(FORBIDDEN_REQUEST_OVERRIDES),
        "conditions": [dataclasses.asdict(c) for c in CONDITIONS],
        "members": {member: dict(values) for member, values in family.MEMBERS.items()},
        "fixed_members": list(family.FIXED_MEMBERS),
        "opponents": list(family.OPPONENTS),
        "packages": {pid: list(slot) for pid, slot in sorted(family.PACKAGES.items())},
        "package_fingerprints": family.fingerprints(),
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
                "expected_matches": f.expected_matches,
            }
            for f in FIELDS
        ],
        "parent_freeze": dict(sorted(PARENT_FREEZE.items())),
        "matches_per_condition": matches_per_condition(),
        "matches_total": matches_total(),
    }


def structural_digest() -> str:
    canonical = json.dumps(structural_definition(), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def matrix_id() -> str:
    return f"v6-e6-matrix-v{E6_MATRIX_VERSION}-{STRUCTURAL_DIGEST[:12]}"


def execution_identity(seed_commitment: str) -> str:
    return seeds.execution_identity(STRUCTURAL_DIGEST, seed_commitment)


def verify_ruleset_registry() -> None:
    """Each condition resolves to its registered radius and lambda; each treatment
    differs from its parent only in ``detection_radius`` (and its identity)."""
    problems: list[str] = []
    policies = {c.condition_id: resolve_ruleset_policy(c.ruleset_id) for c in CONDITIONS}
    for item in CONDITIONS:
        policy = policies[item.condition_id]
        actual = (policy.detection_radius, policy.disruption_slot_limit, policy.capture_hold_ticks,
                  policy.initial_anchor_placement, policy.scheduler_pass_order)
        expected = (item.detection_radius, item.disruption_slot_limit, 1, "core_base", "forward")
        if actual != expected:
            problems.append(f"{item.condition_id}: {actual} != registered {expected}")
        if item.parent is not None:
            parent = policies[item.parent]
            differing = sorted(
                f.name for f in dataclasses.fields(policy) if getattr(policy, f.name) != getattr(parent, f.name)
            )
            if differing != ["detection_radius", "ruleset_id"]:
                problems.append(f"{item.condition_id} differs from {item.parent} in {differing}")
    if problems:
        raise MatrixDefinitionError("E6 Ruleset registry check failed: " + "; ".join(problems))


def verify_frozen_matrix() -> None:
    """Fail closed if the structure drifted from its frozen digest or the registry changed."""
    actual = structural_digest()
    if actual != STRUCTURAL_DIGEST:
        raise MatrixDefinitionError(
            f"E6 structural digest {actual} does not match the frozen STRUCTURAL_DIGEST {STRUCTURAL_DIGEST}; "
            "the experiment definition changed."
        )
    if matches_total() != 11_520:
        raise MatrixDefinitionError(f"E6 matrix count {matches_total()} != 11,520")
    verify_ruleset_registry()
