"""Frozen V6 E2 experiment definition (design review Sec G and Sec I).

Pure data plus pure functions: the three conditions, the three fields, the
seeds, orientations, tick limit and arena, the request overrides that must
stay unset, and the tracked-agent fingerprints every run must reproduce.
Nothing in this module executes a match.

``E2_MATRIX_DIGEST`` is the SHA-256 of the canonical definition. It is pinned
here and by the test suite, so any edit to the definition is a deliberate,
visible re-freeze -- and must never happen after T-E2 data exists.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from itertools import combinations, product
from typing import Any

from battle_engine.ruleset_policy import (
    BYTEFRAY_RULESET_V4_ID,
    BYTEFRAY_RULESET_V6_RESEARCH_CAPTURE_HOLD_K2_ID,
    BYTEFRAY_RULESET_V6_RESEARCH_SCALE_ID,
)

E2_MATRIX_VERSION = 1

ARENA_SIZE = 512
MAX_TICKS = 1000
# Explicit 1..32 -- never the harness's eight-seed STANDARD_V4_SEEDS default.
SEEDS: tuple[int, ...] = tuple(range(1, 33))
BOTH_ORIENTATIONS = True

# Request-level overrides that would make "exactly one gameplay field
# differs" false (review Sec A.2 item 4, Sec E.3). Every E2 evaluation
# request must leave all four as None.
FORBIDDEN_REQUEST_OVERRIDES: tuple[str, ...] = (
    "scheduler_chunk_size",
    "scheduler_rotate_start",
    "kill_weight",
    "instr_per_tick",
)

TWIN_SUFFIX = "_twin"


@dataclass(frozen=True)
class Condition:
    condition_id: str
    ruleset_id: str
    role: str


CONDITIONS: tuple[Condition, ...] = (
    Condition("C-V4", BYTEFRAY_RULESET_V4_ID, "historical control"),
    Condition("C-RS", BYTEFRAY_RULESET_V6_RESEARCH_SCALE_ID, "structural parent / control"),
    Condition("T-E2", BYTEFRAY_RULESET_V6_RESEARCH_CAPTURE_HOLD_K2_ID, "treatment"),
)
CONTROL_GATE_CONDITIONS: tuple[str, str] = ("C-V4", "C-RS")
TREATMENT_CONDITION = "T-E2"

# Review Sec G.2, in its table order.
E2_AGENTS: tuple[str, ...] = (
    "v4_probe",
    "e2_sniper",
    "e2_repair_guard",
    "e2_disrupt_guard",
    "e2_min_guard",
    "e2_greedy_painter",
    "e2_guarded_painter",
    "e2_counter",
    "e2_spread_sniper",
    "e2_spread_defender",
)


def twin_of(agent: str) -> str:
    return f"{agent}{TWIN_SUFFIX}"


E2_TWINS: tuple[str, ...] = tuple(twin_of(agent) for agent in E2_AGENTS)

F3_EXPERIMENTAL: tuple[str, ...] = (
    "v4_probe",
    "e2_sniper",
    "e2_disrupt_guard",
    "e2_spread_defender",
    "e2_guarded_painter",
)
F3_REFERENCE: tuple[str, ...] = (
    "Octave",
    "nemesis_alpha2",
    "v5_core_defender",
    "v4_claimer",
    "v5_scout_striker",
)


@dataclass(frozen=True)
class Field:
    field_id: str
    role: str
    agents: tuple[str, ...]
    pairs: tuple[tuple[str, str], ...]
    pairing: str
    # Only F1 feeds the primary rating tables; F2 and F3 never do.
    rated_as_primary: bool

    @property
    def expected_matches(self) -> int:
        return len(self.pairs) * len(SEEDS) * (2 if BOTH_ORIENTATIONS else 1)


F1 = Field(
    field_id="F1",
    role="primary: triangular round robin of the ten Sec G agents",
    agents=E2_AGENTS,
    pairs=tuple(combinations(E2_AGENTS, 2)),
    pairing="triangular",
    rated_as_primary=True,
)
F2 = Field(
    field_id="F2",
    role="mirrors: each Sec G agent against its byte-identical twin",
    agents=tuple(name for agent in E2_AGENTS for name in (agent, twin_of(agent))),
    pairs=tuple((agent, twin_of(agent)) for agent in E2_AGENTS),
    pairing="explicit",
    rated_as_primary=False,
)
F3 = Field(
    field_id="F3",
    role="secondary reference: experimental subset x tracked historical agents, cross pairs only",
    agents=F3_EXPERIMENTAL + F3_REFERENCE,
    pairs=tuple(product(F3_EXPERIMENTAL, F3_REFERENCE)),
    pairing="explicit",
    rated_as_primary=False,
)
FIELDS: tuple[Field, ...] = (F1, F2, F3)

# Content fingerprints (agent_revisions.agent_revision_fingerprint) of every
# agent the matrix runs, resolved from tracked sources. A run whose live
# fingerprints differ fails closed.
AGENT_FINGERPRINTS: dict[str, str] = {
    "v4_probe": "b82bc724f25806b05936bf1d720c22c04461a535adaede6c29f1de0049f29481",
    "e2_sniper": "eecafc0cae4f34e3e9cbc8b75a0eab6e27297dc7b90d45086e22a7478ecc8362",
    "e2_repair_guard": "c105311e7e3ad91a9a4bb9d93926fd980aa50ce535c0fd2709faffb3b7cd5554",
    "e2_disrupt_guard": "11ae6de4490e3c7cf6a208103d6d7625a636ea64a05a56630d3758f53dbd643c",
    "e2_min_guard": "e99f2245378aa5a21cfa49016ad7908ad521746ce93d1796b4426034f2ab768b",
    "e2_greedy_painter": "cafd8340920d0ebdf4d602bd0a797958f9e4d8ed5528a5c0f0f476dc463a70ed",
    "e2_guarded_painter": "2b1ccd067cdba08e8691e3eab0125bb8188162f74cae6df42087b10cc46e7abf",
    "e2_counter": "fce2b5969bd2332e0b527cd63ace7973104710a98d85bb51225b0a497fcaeb79",
    "e2_spread_sniper": "f44b4dd24635903559a61d7bcf1cadb58074db2b153a28742e274bbcb5d52995",
    "e2_spread_defender": "95a115243ecc9980cffc6517af1e0f72fc24890c42b2578812eea42f832930c0",
    "v4_probe_twin": "aafd37631d00860f5d141b977342828648f51e183ff91d9b3ce623af88713ef6",
    "e2_sniper_twin": "f93b3a0375b894c2b754ee0e55f9512f60295f9c67c794096a9baa5f352c1ffa",
    "e2_repair_guard_twin": "a980718222abcbed2e53700d1b9a3075124025ec0436514cebf355fec94a8b85",
    "e2_disrupt_guard_twin": "c7e26b0d0d949c46f103c2fe37ab042e642b8fe8b24bbc4f729e36547c654773",
    "e2_min_guard_twin": "3a82910b46177ba129c0ddd9247903120d6aaa45b0e95d307fa634e50861007d",
    "e2_greedy_painter_twin": "0765e65a42923f526fac9b24c73a834c9f6832e5b658dbaefc84bfefec4e6780",
    "e2_guarded_painter_twin": "8eb24d11b0e56d8df8c944a62209bfc89a8cc61adb59fef3037d9c015d896438",
    "e2_counter_twin": "ba5e8d9f773b13eb294fa048659404e532dde9472249be8ebe4eedda4bb9f1eb",
    "e2_spread_sniper_twin": "816f193b16b2b40d016b515f0e28be77cc93456f730d24b4f82f1fef96679979",
    "e2_spread_defender_twin": "a5d65adacf515e94e0d0ecc36149710f136a882ead94d3ab489073eda480a09b",
    "Octave": "e87080cce9d3d8a7eeff9afe4d289eb5754bdd42eaaf1e783802631e4d2b7730",
    "nemesis_alpha2": "6d5a8492b34a77cbbbe795152370ed20c65f2c55da20dc96a35f5d28c3b44f5c",
    "v5_core_defender": "2a47c0386ff88d58b810eef97a1f093a89050d5ba3a5ae52a31c56eb2de0cc95",
    "v4_claimer": "342d5a20df20c0154774fbbbd643256e1afbc593b9d735ddb831388cfeebc952",
    "v5_scout_striker": "290e02004291abd77967bc43e549e07eddad9851915ddd9f5edc2fd5e0de0ac1",
}

# Fixtures that follow the single-location enemy-core inference contract
# (review Sec G.1); the capture analyzer audits their inference.
CORE_INFERRING_AGENTS: frozenset[str] = frozenset(
    name
    for agent in ("e2_sniper", "e2_min_guard", "e2_counter", "e2_spread_sniper", "e2_spread_defender")
    for name in (agent, twin_of(agent))
)

E2_MATRIX_DIGEST = "9048907fdc3b09edf82d5da323bf3659b8b2ff158d50c72043257560497427e0"


def condition(condition_id: str) -> Condition:
    for item in CONDITIONS:
        if item.condition_id == condition_id:
            return item
    raise KeyError(f"unknown E2 condition {condition_id!r}")


def field(field_id: str) -> Field:
    for item in FIELDS:
        if item.field_id == field_id:
            return item
    raise KeyError(f"unknown E2 field {field_id!r}")


def matches_per_condition() -> int:
    return sum(item.expected_matches for item in FIELDS)


def matches_total() -> int:
    return matches_per_condition() * len(CONDITIONS)


def matrix_definition() -> dict[str, Any]:
    """The canonical, JSON-serializable experiment definition."""
    return {
        "matrix_version": E2_MATRIX_VERSION,
        "arena_size": ARENA_SIZE,
        "max_ticks": MAX_TICKS,
        "seeds": list(SEEDS),
        "both_orientations": BOTH_ORIENTATIONS,
        "forbidden_request_overrides": list(FORBIDDEN_REQUEST_OVERRIDES),
        "conditions": [
            {"condition_id": c.condition_id, "ruleset_id": c.ruleset_id, "role": c.role}
            for c in CONDITIONS
        ],
        "control_gate": list(CONTROL_GATE_CONDITIONS),
        "treatment": TREATMENT_CONDITION,
        "fields": [
            {
                "field_id": f.field_id,
                "role": f.role,
                "pairing": f.pairing,
                "agents": list(f.agents),
                "pairs": [list(pair) for pair in f.pairs],
                "rated_as_primary": f.rated_as_primary,
                "expected_matches": f.expected_matches,
            }
            for f in FIELDS
        ],
        "agent_fingerprints": dict(sorted(AGENT_FINGERPRINTS.items())),
        "core_inferring_agents": sorted(CORE_INFERRING_AGENTS),
    }


def matrix_digest() -> str:
    canonical = json.dumps(matrix_definition(), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def matrix_id() -> str:
    return f"v6-e2-matrix-v{E2_MATRIX_VERSION}-{E2_MATRIX_DIGEST[:12]}"


def verify_frozen_matrix() -> None:
    """Fail closed if the definition drifted from its frozen digest."""
    actual = matrix_digest()
    if actual != E2_MATRIX_DIGEST:
        raise RuntimeError(
            f"E2 matrix definition digest {actual} does not match the frozen "
            f"E2_MATRIX_DIGEST {E2_MATRIX_DIGEST}; the experiment definition changed."
        )
