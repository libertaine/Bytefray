"""Frozen V6 E3 experiment definition (design review Sec F, Sec L, Sec N).

Pure data plus pure functions: the four conditions (two controls, each the
one-field parent of one treatment), the four fields, the seeds,
orientations, per-field tick limits and arena, the request overrides that
must stay unset, the tracked-agent fingerprints every run must reproduce,
and the historical E2 corpora the new controls must reproduce. Nothing in
this module executes a match.

* **Conditions.** C-E2 (``bytefray-rules-6-research-capture-hold-k2``,
  K = 2, whole-tick disruption) is the parent of the primary treatment T-E3
  (K = 2, ``disruption_slot_limit = 1``). C-RS
  (``bytefray-rules-6-research-scale``, K = 1) is the parent of the
  companion T-E3K1 (K = 1, ``disruption_slot_limit = 1``).
* **Fields.** F1 is E2's round robin of the ten E2 agents, unchanged; F2 is
  E2's ten mirrors; F2-P is F2 at 1001 ticks, so the tick-limit tick has the
  other parity (review Sec L); F4 is the E3 jam sniper against the ten E2
  agents plus the jam mirror. E2's F3 (historical reference agents) is
  dropped: it is not causal for this question.

``E3_MATRIX_DIGEST`` is the SHA-256 of the canonical definition. It is pinned
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
    BYTEFRAY_RULESET_V6_RESEARCH_CAPTURE_HOLD_K2_ID,
    BYTEFRAY_RULESET_V6_RESEARCH_DISRUPTION_SLOT1_ID,
    BYTEFRAY_RULESET_V6_RESEARCH_SCALE_ID,
    resolve_ruleset_policy,
)

from tools.research.v6.e2 import matrix as e2_matrix
from tools.research.v6.e3.entrants import JAM_SNIPER, JAM_SNIPER_TWIN

E3_MATRIX_VERSION = 1

ARENA_SIZE = 512
MAX_TICKS = 1000
# F2-P: the tick-limit tick is a first-mover tick of the other seat (Sec L).
PARITY_MAX_TICKS = 1001
# Explicit 1..32 -- never the harness's eight-seed STANDARD_V4_SEEDS default.
SEEDS: tuple[int, ...] = tuple(range(1, 33))
BOTH_ORIENTATIONS = True
# Nominal action offers per live entrant per tick (Ruleset Q).
QUOTA = 8

# Request-level overrides that would make "exactly one gameplay field
# differs" false (review Sec L, Sec N hard stop 4). Every E3 evaluation
# request must leave all four as None.
FORBIDDEN_REQUEST_OVERRIDES: tuple[str, ...] = e2_matrix.FORBIDDEN_REQUEST_OVERRIDES

E2_AGENTS: tuple[str, ...] = e2_matrix.E2_AGENTS
E2_TWINS: tuple[str, ...] = e2_matrix.E2_TWINS
twin_of = e2_matrix.twin_of

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
    # A treatment's one-field parent (its control); None for a control.
    parent: str | None
    # The Ruleset parameters this condition must resolve to.
    capture_hold_ticks: int
    disruption_slot_limit: int | None


CONDITIONS: tuple[Condition, ...] = (
    Condition("C-E2", BYTEFRAY_RULESET_V6_RESEARCH_CAPTURE_HOLD_K2_ID, CONTROL, PRIMARY_ARM, None, 2, None),
    Condition(
        "T-E3",
        BYTEFRAY_RULESET_V6_RESEARCH_CAPTURE_HOLD_K2_DISRUPTION_SLOT1_ID,
        TREATMENT,
        PRIMARY_ARM,
        "C-E2",
        2,
        1,
    ),
    Condition("C-RS", BYTEFRAY_RULESET_V6_RESEARCH_SCALE_ID, CONTROL, COMPANION_ARM, None, 1, None),
    Condition(
        "T-E3K1", BYTEFRAY_RULESET_V6_RESEARCH_DISRUPTION_SLOT1_ID, TREATMENT, COMPANION_ARM, "C-RS", 1, 1
    ),
)
CONTROL_CONDITIONS: tuple[str, ...] = tuple(c.condition_id for c in CONDITIONS if c.role == CONTROL)
TREATMENT_CONDITIONS: tuple[str, ...] = tuple(c.condition_id for c in CONDITIONS if c.role == TREATMENT)
PRIMARY_TREATMENT = "T-E3"
PRIMARY_CONTROL = "C-E2"

STANDARD = "standard"
TICK_PARITY_REPLICATE = "tick_parity_replicate"


@dataclass(frozen=True)
class Field:
    field_id: str
    role: str
    agents: tuple[str, ...]
    pairs: tuple[tuple[str, str], ...]
    pairing: str
    max_ticks: int
    # "standard" fields form the pre-registered populations; the tick-parity
    # replicate is reported as its own stratum and never pooled (Sec M.7).
    stratum: str
    # The E2 field whose preserved corpus the new controls must reproduce.
    historical_field: str | None

    @property
    def expected_matches(self) -> int:
        return len(self.pairs) * len(SEEDS) * (2 if BOTH_ORIENTATIONS else 1)


_MIRROR_AGENTS = tuple(name for agent in E2_AGENTS for name in (agent, twin_of(agent)))
_MIRROR_PAIRS = tuple((agent, twin_of(agent)) for agent in E2_AGENTS)

F1 = Field(
    field_id="F1",
    role="primary: the E2 F1 triangular round robin of the ten E2 agents, unchanged",
    agents=E2_AGENTS,
    pairs=tuple(combinations(E2_AGENTS, 2)),
    pairing="triangular",
    max_ticks=MAX_TICKS,
    stratum=STANDARD,
    historical_field="F1",
)
F2 = Field(
    field_id="F2",
    role="mirrors: the ten E2 agent/twin mirrors",
    agents=_MIRROR_AGENTS,
    pairs=_MIRROR_PAIRS,
    pairing="explicit",
    max_ticks=MAX_TICKS,
    stratum=STANDARD,
    historical_field="F2",
)
F2P = Field(
    field_id="F2-P",
    role="tick-limit parity replicate: F2 at 1001 ticks",
    agents=_MIRROR_AGENTS,
    pairs=_MIRROR_PAIRS,
    pairing="explicit",
    max_ticks=PARITY_MAX_TICKS,
    stratum=TICK_PARITY_REPLICATE,
    historical_field=None,
)
F4 = Field(
    field_id="F4",
    role="jammer: e3_jam_sniper against the ten E2 agents, plus the jam mirror",
    agents=(JAM_SNIPER, *E2_AGENTS, JAM_SNIPER_TWIN),
    pairs=tuple((JAM_SNIPER, agent) for agent in E2_AGENTS) + ((JAM_SNIPER, JAM_SNIPER_TWIN),),
    pairing="explicit",
    max_ticks=MAX_TICKS,
    stratum=STANDARD,
    historical_field=None,
)
FIELDS: tuple[Field, ...] = (F1, F2, F2P, F4)
FIELD_IDS: tuple[str, ...] = tuple(f.field_id for f in FIELDS)
STANDARD_FIELDS: tuple[str, ...] = tuple(f.field_id for f in FIELDS if f.stratum == STANDARD)

# The preserved E2 corpus each new control must reproduce, cell for cell, in
# the fields that have a historical counterpart (Sec N step 6).
HISTORICAL_MATRIX_ID = e2_matrix.matrix_id()
HISTORICAL_PARENT: dict[str, str] = {"C-E2": "T-E2", "C-RS": "C-RS"}

# Content fingerprints (agent_revisions.agent_revision_fingerprint) of every
# agent the matrix runs, resolved from tracked sources. The twenty E2 values
# are E2's frozen ones; a run whose live fingerprints differ fails closed.
AGENT_FINGERPRINTS: dict[str, str] = {
    **{name: e2_matrix.AGENT_FINGERPRINTS[name] for name in (*E2_AGENTS, *E2_TWINS)},
    JAM_SNIPER: "f92c056e271ce16492119fd57edf7ce10985f3aef88636228f8c7434a1a7ad8e",
    JAM_SNIPER_TWIN: "6035dd549edf49bbd0a62f5713a797fc268e2edb9e20a7b9e96d71dc159a31e2",
}

# Fixtures that follow the single-location enemy-core inference contract;
# the capture analyzer audits their inference.
CORE_INFERRING_AGENTS: frozenset[str] = e2_matrix.CORE_INFERRING_AGENTS | {JAM_SNIPER, JAM_SNIPER_TWIN}

E3_MATRIX_DIGEST = "634132ec3c15549b8032b7414c2a0f649ff2e3a754f592c5c2a71090b37215e8"


class MatrixDefinitionError(RuntimeError):
    """The live E3 definition or Ruleset registry differs from the frozen experiment."""


def condition(condition_id: str) -> Condition:
    for item in CONDITIONS:
        if item.condition_id == condition_id:
            return item
    raise KeyError(f"unknown E3 condition {condition_id!r}")


def field(field_id: str) -> Field:
    for item in FIELDS:
        if item.field_id == field_id:
            return item
    raise KeyError(f"unknown E3 field {field_id!r}")


def matches_per_condition() -> int:
    return sum(item.expected_matches for item in FIELDS)


def matches_total() -> int:
    return matches_per_condition() * len(CONDITIONS)


def matrix_definition() -> dict[str, Any]:
    """The canonical, JSON-serializable experiment definition."""
    return {
        "matrix_version": E3_MATRIX_VERSION,
        "arena_size": ARENA_SIZE,
        "seeds": list(SEEDS),
        "both_orientations": BOTH_ORIENTATIONS,
        "quota": QUOTA,
        "forbidden_request_overrides": list(FORBIDDEN_REQUEST_OVERRIDES),
        "conditions": [
            {
                "condition_id": c.condition_id,
                "ruleset_id": c.ruleset_id,
                "role": c.role,
                "arm": c.arm,
                "parent": c.parent,
                "capture_hold_ticks": c.capture_hold_ticks,
                "disruption_slot_limit": c.disruption_slot_limit,
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
                "stratum": f.stratum,
                "historical_field": f.historical_field,
                "expected_matches": f.expected_matches,
            }
            for f in FIELDS
        ],
        "dropped_fields": ["F3"],
        "historical_parent": {"matrix_id": HISTORICAL_MATRIX_ID, "conditions": dict(sorted(HISTORICAL_PARENT.items()))},
        "agent_fingerprints": dict(sorted(AGENT_FINGERPRINTS.items())),
        "core_inferring_agents": sorted(CORE_INFERRING_AGENTS),
        "matches_per_condition": matches_per_condition(),
        "matches_total": matches_total(),
    }


def matrix_digest() -> str:
    canonical = json.dumps(matrix_definition(), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def matrix_id() -> str:
    return f"v6-e3-matrix-v{E3_MATRIX_VERSION}-{E3_MATRIX_DIGEST[:12]}"


def verify_ruleset_registry() -> None:
    """Each condition's Ruleset resolves to its registered parameters, and each
    treatment differs from its parent only in ``disruption_slot_limit`` (and
    its identity)."""
    problems: list[str] = []
    policies = {c.condition_id: resolve_ruleset_policy(c.ruleset_id) for c in CONDITIONS}
    for item in CONDITIONS:
        policy = policies[item.condition_id]
        actual = (policy.capture_hold_ticks, policy.disruption_slot_limit)
        if actual != (item.capture_hold_ticks, item.disruption_slot_limit):
            problems.append(f"{item.condition_id}: (K, lambda) {actual} != registered "
                            f"{(item.capture_hold_ticks, item.disruption_slot_limit)}")
        if item.parent is not None:
            parent = policies[item.parent]
            differing = sorted(
                f.name for f in dataclasses.fields(policy) if getattr(policy, f.name) != getattr(parent, f.name)
            )
            if differing != ["disruption_slot_limit", "ruleset_id"]:
                problems.append(f"{item.condition_id} differs from {item.parent} in {differing}")
    if problems:
        raise MatrixDefinitionError("E3 Ruleset registry check failed: " + "; ".join(problems))


def verify_frozen_matrix() -> None:
    """Fail closed if the definition drifted from its frozen digest or the
    Ruleset registry no longer matches the registered conditions."""
    actual = matrix_digest()
    if actual != E3_MATRIX_DIGEST:
        raise MatrixDefinitionError(
            f"E3 matrix definition digest {actual} does not match the frozen "
            f"E3_MATRIX_DIGEST {E3_MATRIX_DIGEST}; the experiment definition changed."
        )
    verify_ruleset_registry()
