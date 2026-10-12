"""The frozen E8 structural matrix definition, v1 (phase I8-4; no seed values).

docs/research/v6/V6_E8_ACTIVE_SPATIAL_SENSING_PREREGISTRATION.md (PR8) Sec 2.2,
3 and 9, step 1; the implementation plan Sec 1 (I8-4) and 5.8. Pure data plus
pure functions:

* the four conditions, with their final Ruleset identifiers;
* the population, its sets, the 22 packages and their fingerprints;
* the two fields and their counts;
* the arena, tick limit, quota, chunk and window, and the request overrides
  that must stay unset;
* the parent byte-identity freeze (D8-6, phase I8-1);
* the two inputs PR8 Sec 9, step 1 commits with this identity: the H8-REPEAT
  census (Sec 3.5) and the seat strata inputs (Sec 6.2 and 6.3).

Nothing here executes a match, and nothing here names a seed. The matrix has
32 seed *positions*. Their values are generated only after this identity is
frozen (PR8 Sec 9, step 2; phase I8-6).

* **Structural matrix identity:** ``v6-e8-matrix-v1-<first 12 hex of
  STRUCTURAL_DIGEST>``, where ``STRUCTURAL_DIGEST`` is the SHA-256 of
  ``structural_definition()`` in canonical JSON. It is pinned here and by the
  tests, so any edit is a deliberate, visible re-freeze, and none may happen
  once a seed exists.
* **Execution matrix identity** (phase I8-6): ``v6-e8-exec-v1-<12 hex of
  SHA-256(structural digest hex, LF, commitment hex, LF)>`` (PR8 Sec 9, step
  4). The seed tooling that computes it is not part of this phase.

The final Ruleset identifiers are the provisional ones of PR8 Sec 2.2,
unchanged: ``verify_ruleset_registry`` checks them against the transcription
and the engine's registry.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
from dataclasses import dataclass
from fractions import Fraction
from itertools import combinations
from typing import Any

from battle_engine.config import Config
from battle_engine.ruleset_policy import (
    BYTEFRAY_RULESET_V6_RESEARCH_DISRUPTION_SLOT1_SENSING_ACTIVE_W27_ID,
    BYTEFRAY_RULESET_V6_RESEARCH_DISRUPTION_SLOT1_SENSING_R32_ID,
    BYTEFRAY_RULESET_V6_RESEARCH_SENSING_ACTIVE_W27_ID,
    BYTEFRAY_RULESET_V6_RESEARCH_SENSING_R32_ID,
    resolve_ruleset_policy,
)

from tools.research.v6.e2 import matrix as e2_matrix
from tools.research.v6.e8 import decision, family, preregistration

E8_MATRIX_VERSION = 1
MATRIX_ID_PREFIX = "v6-e8-matrix-v1-"
_registration = decision.REGISTRATION
_fixed = _registration["fixed_across_conditions"]
ARENA_SIZE: int = _fixed["arena_size"]
MAX_TICKS: int = _fixed["tick_limit"]
QUOTA: int = _fixed["quota_Q"]
CHUNK: int = _fixed["chunk"]
SEED_COUNT: int = _registration["decisions"]["R-7"]["value"]
SENSING_WINDOW = 27
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
    sensing_mode: str
    sensing_window: int | None
    disruption_slot_limit: int | None
    detection_radius: int


CONDITIONS: tuple[Condition, ...] = (
    Condition("C8", BYTEFRAY_RULESET_V6_RESEARCH_SENSING_R32_ID, CONTROL, PRIMARY_ARM, None, "passive", None, None,
              DETECTION_RADIUS),
    Condition("T8", BYTEFRAY_RULESET_V6_RESEARCH_SENSING_ACTIVE_W27_ID, TREATMENT, PRIMARY_ARM, "C8", "active",
              SENSING_WINDOW, None, DETECTION_RADIUS),
    Condition("C8L", BYTEFRAY_RULESET_V6_RESEARCH_DISRUPTION_SLOT1_SENSING_R32_ID, CONTROL, COMPANION_ARM, None,
              "passive", None, 1, DETECTION_RADIUS),
    Condition("T8L", BYTEFRAY_RULESET_V6_RESEARCH_DISRUPTION_SLOT1_SENSING_ACTIVE_W27_ID, TREATMENT, COMPANION_ARM,
              "C8L", "active", SENSING_WINDOW, 1, DETECTION_RADIUS),
)
CONTROL_CONDITIONS: tuple[str, ...] = tuple(c.condition_id for c in CONDITIONS if c.role == CONTROL)
TREATMENT_CONDITIONS: tuple[str, ...] = tuple(c.condition_id for c in CONDITIONS if c.role == TREATMENT)
ARMS: dict[str, tuple[str, str]] = {PRIMARY_ARM: ("C8", "T8"), COMPANION_ARM: ("C8L", "T8L")}

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
F2 = Field("F2", "every twin mirror, both orientations (the swap is a relabeling: D8-11)",
           tuple(name for pair in zip(PRIMARIES, TWINS, strict=True) for name in pair),
           tuple(zip(PRIMARIES, TWINS, strict=True)), "explicit", MAX_TICKS, True, TWIN_MIRROR)
FIELDS: tuple[Field, ...] = (F1, F2)

#: The I8-1 parent byte-identity freeze, committed before any engine change (D8-6).
PARENT_FREEZE: dict[str, Any] = {
    "phase": "I8-1",
    "commits": ["3f3f709", "2cfd4e8"],
    "record": "tools/research/v6/e8/parent_goldens.json",
    "test": "engine/tests/test_v6_e8_parent_byte_identity.py",
    "conditions": ["C8", "C8L"],
}

STRUCTURAL_DIGEST = "e0d322b597da298686c7a392a7ae495a96ea6a5428b5fb47f15138fa3af26fc7"


class MatrixDefinitionError(RuntimeError):
    """The live E8 definition or Ruleset registry differs from the frozen experiment."""


def condition(condition_id: str) -> Condition:
    for item in CONDITIONS:
        if item.condition_id == condition_id:
            return item
    raise KeyError(f"unknown E8 condition {condition_id!r}")


def field(field_id: str) -> Field:
    for item in FIELDS:
        if item.field_id == field_id:
            return item
    raise KeyError(f"unknown E8 field {field_id!r}")


def matches_per_condition() -> int:
    return sum(item.expected_matches for item in FIELDS)


def matches_total() -> int:
    return matches_per_condition() * len(CONDITIONS)


def _fraction(value: Fraction) -> str:
    return f"{value.numerator}/{value.denominator}"


def census_inputs() -> dict[str, Any]:
    """PR8 Sec 3.5: the static census, from each role's manifests on disk (no outcome enters it)."""
    census = _registration["census"]
    return {
        "procedure": "decision.census over the parameters each package's manifest declares (family.census)",
        "criteria": [criterion["id"] for criterion in census["criteria"]],
        "contrast": dict(census["contrast"]),
        "defined_under": "the primary parent's economics; the companion evaluates the same census",
        "primary": list(family.census("primary")),
        "twin": list(family.census("twin")),
    }


def seat_strata_inputs() -> dict[str, Any]:
    """PR8 Sec 6.2 and 6.3: the 66 seat units, the phase-sensitive partition, and the neutrality predicate.

    The C8-neutral and C8-non-neutral reporting strata need control data. They
    are computed at the C8 point estimate and committed before any treatment
    cell (CQ8-5), never here.
    """
    sensitive = set(decision.PHASE_SENSITIVE)
    units = decision.SEAT_UNITS
    containing = [list(unit) for unit in units if sensitive & set(unit[1:])]
    not_containing = [list(unit) for unit in units if not sensitive & set(unit[1:])]
    return {
        "units": [list(unit) for unit in units],
        "unit_cells": {
            "pairing": "the F1 cells of the unordered member pair, both orientations, every seed position",
            "mirror": "the F2 cells of the member's primary and twin packages, both orientations, every seed position",
        },
        "phase_sensitive_members": list(decision.PHASE_SENSITIVE),
        "containing_phase_sensitive": containing,
        "not_containing_phase_sensitive": not_containing,
        "neutrality": {"predicate": "O-NEUTRAL", "sdom_lt": _fraction(decision.NEUTRAL_SDOM_LT),
                       "abs_gsb_le": _fraction(decision.NEUTRAL_ABS_GSB_LE)},
        "control_strata": "C8-neutral and C8-non-neutral, by O-NEUTRAL at the C8 point estimate, computed on "
                          "control data and committed before any treatment cell (CQ8-5)",
    }


def parent_freeze() -> dict[str, Any]:
    record = json.loads((preregistration.REPOSITORY_ROOT / PARENT_FREEZE["record"]).read_text(encoding="utf-8"))
    return {**PARENT_FREEZE, "cases": len(record["cases"]),
            "record_sha256": preregistration.file_digest(preregistration.REPOSITORY_ROOT / PARENT_FREEZE["record"])}


def structural_definition() -> dict[str, Any]:
    """The canonical, JSON-serializable structure: everything but the seed values."""
    seed_protocol = _registration["seed_protocol"]
    return {
        "matrix_version": E8_MATRIX_VERSION,
        "arena_size": ARENA_SIZE,
        "max_ticks": MAX_TICKS,
        "quota": QUOTA,
        "chunk": CHUNK,
        "sensing_window": SENSING_WINDOW,
        "detection_radius": DETECTION_RADIUS,
        "seed_count": SEED_COUNT,
        "seed_protocol": {
            "generator": seed_protocol["generator"],
            "bound": "2**53",
            "encoding": "decimal ASCII, one per line, LF endings with a trailing LF, in UTF-8, generation order",
            "commitment": "SHA-256 hex of the encoded bytes",
            "execution_identity": seed_protocol["execution_identity"]["form"],
        },
        "forbidden_request_overrides": list(FORBIDDEN_REQUEST_OVERRIDES),
        "conditions": [dataclasses.asdict(c) for c in CONDITIONS],
        "arms": {arm: list(pair) for arm, pair in ARMS.items()},
        "members": {member: dict(values) for member, values in family.MEMBERS.items()},
        "registered_encoding": [[parameter, registered, manifest]
                                for (parameter, registered), manifest in family.REGISTERED_ENCODING.items()],
        "opponents": list(family.OPPONENTS),
        "fixed_members": list(family.FIXED_MEMBERS),
        "a8": list(family.A8),
        "phase_sensitive": list(decision.PHASE_SENSITIVE),
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
        "parent_freeze": parent_freeze(),
        "census": census_inputs(),
        "seat_strata_inputs": seat_strata_inputs(),
        "matches_per_condition": matches_per_condition(),
        "matches_total": matches_total(),
    }


def structural_digest() -> str:
    canonical = json.dumps(structural_definition(), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def matrix_id() -> str:
    return MATRIX_ID_PREFIX + STRUCTURAL_DIGEST[:12]


#: Every Ruleset field fixed across the four conditions (PR8 Sec 2.2), as the engine names it.
FIXED_POLICY_FIELDS: dict[str, Any] = {
    "scheduler_mode": "chunked",
    "scheduler_chunk_size": CHUNK,
    "scheduler_rotate_start": True,
    "core_placement": "seeded",
    "capture_hold_ticks": 1,
    "initial_anchor_placement": "core_base",
    "scheduler_pass_order": "forward",
}


def verify_ruleset_registry() -> None:
    """Each condition resolves to its registered policy; each treatment differs from its
    parent only in ``sensing_mode`` (and its identity); the final identifiers are the
    transcription's; the quota is the engine default the forbidden overrides keep."""
    problems: list[str] = []
    registered = {c["id"]: c for c in _registration["conditions"]}
    if [c.condition_id for c in CONDITIONS] != list(registered):
        problems.append(f"conditions {[c.condition_id for c in CONDITIONS]} != registered {list(registered)}")
    policies = {c.condition_id: resolve_ruleset_policy(c.ruleset_id) for c in CONDITIONS}
    for item in CONDITIONS:
        entry = registered.get(item.condition_id, {})
        expected_entry = (item.ruleset_id, item.parent, item.arm, item.role, item.sensing_mode)
        actual_entry = (entry.get("ruleset_id"), entry.get("parent"), entry.get("arm"), entry.get("role"),
                        entry.get("sensing_mode"))
        if actual_entry != expected_entry:
            problems.append(f"{item.condition_id}: transcription {actual_entry} != {expected_entry}")
        policy = policies[item.condition_id]
        actual = (policy.sensing_mode, policy.sensing_window, policy.disruption_slot_limit, policy.detection_radius)
        expected = (item.sensing_mode, item.sensing_window, item.disruption_slot_limit, item.detection_radius)
        if actual != expected:
            problems.append(f"{item.condition_id}: {actual} != registered {expected}")
        fixed = {name: getattr(policy, name) for name in FIXED_POLICY_FIELDS}
        if fixed != FIXED_POLICY_FIELDS:
            problems.append(f"{item.condition_id}: fixed fields {fixed} != {FIXED_POLICY_FIELDS}")
        if item.parent is not None:
            parent = policies[item.parent]
            differing = sorted(
                f.name for f in dataclasses.fields(policy) if getattr(policy, f.name) != getattr(parent, f.name)
            )
            if differing != ["ruleset_id", "sensing_mode"]:
                problems.append(f"{item.condition_id} differs from {item.parent} in {differing}")
    if Config().instr_per_tick != QUOTA:
        problems.append(f"the engine's default quota {Config().instr_per_tick} != {QUOTA}")
    if problems:
        raise MatrixDefinitionError("E8 Ruleset registry check failed: " + "; ".join(problems))


def verify_frozen_matrix() -> None:
    """Fail closed if the structure drifted from its frozen digest, the registry changed,
    the count is not the registered one, or the census is empty (PR8 Sec 12)."""
    actual = structural_digest()
    if actual != STRUCTURAL_DIGEST:
        raise MatrixDefinitionError(
            f"E8 structural digest {actual} does not match the frozen STRUCTURAL_DIGEST {STRUCTURAL_DIGEST}; "
            "the experiment definition changed."
        )
    registered_total = _registration["fields"]["cells_total"]
    if matches_total() != registered_total:
        raise MatrixDefinitionError(f"E8 matrix count {matches_total()} != the registered {registered_total}")
    census = census_inputs()
    if not census["primary"] or census["primary"] != census["twin"]:
        raise MatrixDefinitionError(f"E8 census {census['primary']} (primary) / {census['twin']} (twin): "
                                    "an empty or role-dependent census halts before seeds (PR8 Sec 12)")
    verify_ruleset_registry()
