"""Pure-function remnants of the retired v2.0.0-beta2 Phase 1 Ruleset-v2 1v1
evaluation methodology suite (formerly ``test_agent_evaluation_v2_methodology.py``).

V6 Phase 2B.12 (docs/research/v6/V6_PHASE2B12_SCOPE_C_RUNTIME_RETIREMENT.md)
retired Ruleset v1 and v2 execution entirely: bytefray-rules-4 is the only
Ruleset that can create a new evaluation artifact, so the deleted file's
~40 real-``EvaluationService``-execution tests (v1/v2 methodology matrix
generation, placement/seed/order identity, capture evidence, resume,
comparison) tested subjects that can no longer occur for a new evaluation
and were deleted outright rather than frozen, matching the charter's
Scope-C precedent for the two retired ruleset-equivalence test files. This
file keeps the handful of tests that were genuinely pure functions of
``standard_placements()``/``is_ruleset_v2_methodology()`` -- neither
executes a match, and both remain live (the second still classifies
historical artifacts correctly; the first is still called by the
comparison-report display path for a historical v2-methodology artifact).
"""

from __future__ import annotations

from battle_engine.agent_evaluation import (
    BYTEFRAY_RULESET_ID,
    BYTEFRAY_RULESET_V2_ID,
    is_ruleset_v2_methodology,
    standard_placements,
)
from battle_engine.config import Config


def test_standard_placements_generates_three_deterministic_conditions():
    placements = standard_placements(4096)
    assert [p.placement_id for p in placements] == ["opposed", "quarter", "opposed-shifted"]
    assert placements == standard_placements(4096)  # deterministic, no RNG


def test_standard_placements_starts_are_valid_for_default_arena():
    arena_size = Config().arena_size
    for placement in standard_placements(arena_size):
        assert 0 <= placement.subject_start < arena_size
        assert 0 <= placement.opponent_start < arena_size


def test_standard_placements_cores_never_overlap():
    from battle_engine.python_runtime import CORE_SIZE, core_addresses

    arena_size = Config().arena_size
    for placement in standard_placements(arena_size):
        subject_cells = set(core_addresses(placement.subject_start, arena_size))
        opponent_cells = set(core_addresses(placement.opponent_start, arena_size))
        assert len(subject_cells) == CORE_SIZE
        assert not (subject_cells & opponent_cells)


def test_is_ruleset_v2_methodology_excludes_alpha_identities():
    assert is_ruleset_v2_methodology(BYTEFRAY_RULESET_V2_ID) is True
    assert is_ruleset_v2_methodology(BYTEFRAY_RULESET_ID) is False
    assert is_ruleset_v2_methodology("bytefray-rules-2-alpha11") is False
