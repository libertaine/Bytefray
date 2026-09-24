"""Unit coverage for the executable Ruleset policies (stable v4, plus the V6
Phase 4B variable-arena research identity registered alongside it)."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, dataclass, replace

import pytest
from battle_engine.ruleset_policy import (
    BYTEFRAY_RULESET_V2_ALPHA1_ID,
    BYTEFRAY_RULESET_V2_ALPHA11_ID,
    BYTEFRAY_RULESET_V2_ID,
    BYTEFRAY_RULESET_V3_ALPHA1_ID,
    BYTEFRAY_RULESET_V4_ALPHA1_ID,
    BYTEFRAY_RULESET_V4_ALPHA2_ID,
    BYTEFRAY_RULESET_V4_ID,
    BYTEFRAY_RULESET_V6_RESEARCH_CAPTURE_HOLD_K2_DISRUPTION_SLOT1_ID,
    BYTEFRAY_RULESET_V6_RESEARCH_CAPTURE_HOLD_K2_DISRUPTION_SLOT1_MIRRORED_PASSES_ID,
    BYTEFRAY_RULESET_V6_RESEARCH_CAPTURE_HOLD_K2_ID,
    BYTEFRAY_RULESET_V6_RESEARCH_DISRUPTION_SLOT1_ID,
    BYTEFRAY_RULESET_V6_RESEARCH_DISRUPTION_SLOT1_MIRRORED_PASSES_ID,
    BYTEFRAY_RULESET_V6_RESEARCH_SCALE_ID,
    BYTEFRAY_RULESET_V6_RESEARCH_SCALE_MOVE_ID,
    BYTEFRAY_RULESET_V6_RESEARCH_SCALE_MOVE_PROPORTIONAL_ID,
    OMITTED_RULESET_CANDIDATES,
    PROCESS_RULESET_IDS,
    RULESET_V4,
    RULESET_V6_RESEARCH_SCALE,
    RULESET_V6_RESEARCH_SCALE_MOVE,
    RULESET_V6_RESEARCH_SCALE_MOVE_PROPORTIONAL,
    NoCompatibleRulesetError,
    RulesetPolicy,
    TerminationDecision,
    TerminationReason,
    UnknownRulesetError,
    agent_supported_by_ruleset,
    resolve_omitted_ruleset_for_agents,
    resolve_omitted_ruleset_id,
    resolve_ruleset_policy,
)


@dataclass
class _FakeState:
    name: str
    alive: bool = True


def _python(api_version: object = 2, agent_id: str = "probe") -> dict[str, object]:
    return {"agent_id": agent_id, "kind": "python", "api_version": api_version}


def test_stable_v4_is_the_only_automatic_policy() -> None:
    assert resolve_ruleset_policy(BYTEFRAY_RULESET_V4_ID) is RULESET_V4
    assert OMITTED_RULESET_CANDIDATES == (BYTEFRAY_RULESET_V4_ID,)
    assert resolve_omitted_ruleset_for_agents(None, [_python()]) == BYTEFRAY_RULESET_V4_ID


def test_v6_research_scale_is_registered_but_never_automatic() -> None:
    # V6 Phase 4B: registered and executable (both are members of
    # PROCESS_RULESET_IDS), but never what an omitted --ruleset selection
    # resolves to -- an explicit roster must name it by hand.
    assert resolve_ruleset_policy(BYTEFRAY_RULESET_V6_RESEARCH_SCALE_ID) is RULESET_V6_RESEARCH_SCALE
    assert BYTEFRAY_RULESET_V6_RESEARCH_SCALE_ID not in OMITTED_RULESET_CANDIDATES
    assert PROCESS_RULESET_IDS == frozenset(
        {
            BYTEFRAY_RULESET_V4_ID,
            BYTEFRAY_RULESET_V6_RESEARCH_SCALE_ID,
            BYTEFRAY_RULESET_V6_RESEARCH_SCALE_MOVE_ID,
            BYTEFRAY_RULESET_V6_RESEARCH_SCALE_MOVE_PROPORTIONAL_ID,
            # V6 E2: the capture-hold research identity, registered by the
            # same explicit-entry pattern (never automatic either -- see
            # test_ruleset_v6_research_capture_hold.py).
            BYTEFRAY_RULESET_V6_RESEARCH_CAPTURE_HOLD_K2_ID,
            # V6 E3: the two slot-limited disruption research identities,
            # registered the same way (never automatic either -- see
            # test_ruleset_v6_research_disruption_slot.py).
            BYTEFRAY_RULESET_V6_RESEARCH_CAPTURE_HOLD_K2_DISRUPTION_SLOT1_ID,
            BYTEFRAY_RULESET_V6_RESEARCH_DISRUPTION_SLOT1_ID,
            # V6 E4: the two mirrored-pass-order research identities,
            # registered the same way (never automatic either -- see
            # test_ruleset_v6_research_mirrored_passes.py).
            BYTEFRAY_RULESET_V6_RESEARCH_CAPTURE_HOLD_K2_DISRUPTION_SLOT1_MIRRORED_PASSES_ID,
            BYTEFRAY_RULESET_V6_RESEARCH_DISRUPTION_SLOT1_MIRRORED_PASSES_ID,
        }
    )
    assert resolve_omitted_ruleset_for_agents(None, [_python()]) != BYTEFRAY_RULESET_V6_RESEARCH_SCALE_ID


def test_v6_research_scale_move_is_registered_but_never_automatic() -> None:
    # V6 Phase 4C: registered and executable, but never what an omitted
    # --ruleset selection resolves to -- requires explicit name.
    assert resolve_ruleset_policy(BYTEFRAY_RULESET_V6_RESEARCH_SCALE_MOVE_ID) is RULESET_V6_RESEARCH_SCALE_MOVE
    assert BYTEFRAY_RULESET_V6_RESEARCH_SCALE_MOVE_ID not in OMITTED_RULESET_CANDIDATES
    assert resolve_omitted_ruleset_for_agents(None, [_python()]) != BYTEFRAY_RULESET_V6_RESEARCH_SCALE_MOVE_ID


def test_v6_research_scale_move_proportional_is_registered_but_never_automatic() -> None:
    # V6 Phase 4D: registered and executable, but never what an omitted
    # --ruleset selection resolves to -- requires explicit name.
    assert (
        resolve_ruleset_policy(BYTEFRAY_RULESET_V6_RESEARCH_SCALE_MOVE_PROPORTIONAL_ID)
        is RULESET_V6_RESEARCH_SCALE_MOVE_PROPORTIONAL
    )
    assert BYTEFRAY_RULESET_V6_RESEARCH_SCALE_MOVE_PROPORTIONAL_ID not in OMITTED_RULESET_CANDIDATES
    assert (
        resolve_omitted_ruleset_for_agents(None, [_python()])
        != BYTEFRAY_RULESET_V6_RESEARCH_SCALE_MOVE_PROPORTIONAL_ID
    )


def test_v6_research_scale_matches_stable_v4_fields_except_id() -> None:
    # The research Ruleset is a deliberate independent literal copy of
    # RULESET_V4 (never a live `dataclasses.replace(RULESET_V4, ...)`
    # reference -- see RULESET_V6_RESEARCH_SCALE's own docstring). This is
    # the permanent regression guard that the two stay field-for-field
    # equal (ruleset_id aside) even though they are maintained as two
    # separate object literals.
    assert replace(RULESET_V6_RESEARCH_SCALE, ruleset_id=RULESET_V4.ruleset_id) == RULESET_V4


def test_v6_research_scale_move_matches_research_scale_except_id_and_movement() -> None:
    # V6 Phase 4C: matches raw research-scale in every gameplay field except
    # movement stride normalization.
    assert replace(
        RULESET_V6_RESEARCH_SCALE_MOVE,
        ruleset_id=RULESET_V6_RESEARCH_SCALE.ruleset_id,
        movement_stride="fixed_64",
    ) == RULESET_V6_RESEARCH_SCALE
    assert RULESET_V6_RESEARCH_SCALE_MOVE.movement_stride == "scale_normalized"
    assert RULESET_V6_RESEARCH_SCALE_MOVE.movement_displacement == "literal"
    assert RULESET_V6_RESEARCH_SCALE.movement_stride == "fixed_64"
    assert RULESET_V6_RESEARCH_SCALE.movement_displacement == "literal"
    assert RULESET_V4.movement_stride == "fixed_64"
    assert RULESET_V4.movement_displacement == "literal"


def test_v6_research_scale_move_proportional_matches_research_scale_except_id_and_movement() -> None:
    # V6 Phase 4D: matches raw research-scale in every gameplay field except
    # proportional movement displacement transform.
    assert replace(
        RULESET_V6_RESEARCH_SCALE_MOVE_PROPORTIONAL,
        ruleset_id=RULESET_V6_RESEARCH_SCALE.ruleset_id,
        movement_displacement="literal",
    ) == RULESET_V6_RESEARCH_SCALE
    assert RULESET_V6_RESEARCH_SCALE_MOVE_PROPORTIONAL.movement_stride == "fixed_64"
    assert (
        RULESET_V6_RESEARCH_SCALE_MOVE_PROPORTIONAL.movement_displacement
        == "scale_from_512"
    )


def test_stable_v4_fields_remain_pinned() -> None:
    assert RULESET_V4.supported_runtime_kinds == frozenset({"python"})
    assert RULESET_V4.supported_python_api_versions == frozenset({2})
    assert (
        RULESET_V4.scheduler_mode,
        RULESET_V4.scheduler_chunk_size,
        RULESET_V4.scheduler_rotate_start,
        RULESET_V4.core_placement,
        RULESET_V4.process_selection,
        RULESET_V4.movement_stride,
        RULESET_V4.movement_displacement,
    ) == ("chunked", 2, True, "seeded", "round_robin", "fixed_64", "literal")


def test_movement_stride_resolution_and_bounds() -> None:
    arenas = [64, 256, 512, 1024, 4096, 16384, 65536]
    # Stable v4: always 64
    for a in arenas:
        assert RULESET_V4.resolve_max_move_delta(a) == 64

    # Raw-scale research control (Phase 4B): always 64
    for a in arenas:
        assert RULESET_V6_RESEARCH_SCALE.resolve_max_move_delta(a) == 64

    # Movement-normalized research (Phase 4C): max(64, floor(A / 8))
    # Anchor invariant: A=512 -> 64
    assert RULESET_V6_RESEARCH_SCALE_MOVE.resolve_max_move_delta(512) == 64
    # Scaled values:
    assert RULESET_V6_RESEARCH_SCALE_MOVE.resolve_max_move_delta(1024) == 128
    assert RULESET_V6_RESEARCH_SCALE_MOVE.resolve_max_move_delta(4096) == 512
    assert RULESET_V6_RESEARCH_SCALE_MOVE.resolve_max_move_delta(16384) == 2048
    assert RULESET_V6_RESEARCH_SCALE_MOVE.resolve_max_move_delta(65536) == 8192
    # Floor behavior below 512:
    assert RULESET_V6_RESEARCH_SCALE_MOVE.resolve_max_move_delta(64) == 64
    assert RULESET_V6_RESEARCH_SCALE_MOVE.resolve_max_move_delta(256) == 64


@pytest.mark.parametrize(
    "retired_id",
    [
        "bytefray-rules-1",
        BYTEFRAY_RULESET_V2_ALPHA1_ID,
        BYTEFRAY_RULESET_V2_ALPHA11_ID,
        BYTEFRAY_RULESET_V2_ID,
        BYTEFRAY_RULESET_V3_ALPHA1_ID,
        BYTEFRAY_RULESET_V4_ALPHA1_ID,
        BYTEFRAY_RULESET_V4_ALPHA2_ID,
    ],
)
def test_retired_rulesets_fail_closed(retired_id: str) -> None:
    with pytest.raises(UnknownRulesetError) as caught:
        resolve_ruleset_policy(retired_id)
    assert caught.value.ruleset_id == retired_id


@pytest.mark.parametrize("unknown_id", ["", "unknown", "bytefray-rules-99"])
def test_unknown_rulesets_fail_closed(unknown_id: str) -> None:
    with pytest.raises(UnknownRulesetError):
        resolve_ruleset_policy(unknown_id)


@pytest.mark.parametrize(
    "agent",
    [
        _python(1),
        _python(None),
        _python(True),
        {"kind": "builtin", "api_version": None},
        {"kind": "blob", "api_version": None},
        {"kind": "vm", "api_version": None},
        {"kind": "unknown", "api_version": 2},
    ],
)
def test_retired_runtime_metadata_never_resolves_automatically(agent: dict[str, object]) -> None:
    with pytest.raises(NoCompatibleRulesetError):
        resolve_omitted_ruleset_for_agents(None, [agent])


def test_empty_and_mixed_rosters_fail_closed() -> None:
    with pytest.raises(NoCompatibleRulesetError):
        resolve_omitted_ruleset_for_agents(None, [])
    with pytest.raises(NoCompatibleRulesetError):
        resolve_omitted_ruleset_for_agents(None, [_python(2), _python(1, "legacy")])


def test_explicit_selection_is_passthrough_not_implicit_registration() -> None:
    assert resolve_omitted_ruleset_for_agents(BYTEFRAY_RULESET_V2_ID, [_python()]) == (
        BYTEFRAY_RULESET_V2_ID
    )
    with pytest.raises(UnknownRulesetError):
        resolve_ruleset_policy(BYTEFRAY_RULESET_V2_ID)


def test_kind_only_compatibility_surface_projects_python_as_api_v2() -> None:
    assert resolve_omitted_ruleset_id(None, {"python"}) == BYTEFRAY_RULESET_V4_ID
    for kinds in (set(), {"vm"}, {"builtin"}, {"blob"}, {"python", "vm"}):
        with pytest.raises(NoCompatibleRulesetError):
            resolve_omitted_ruleset_id(None, kinds)


def test_agent_support_is_metadata_only_and_current_only() -> None:
    assert agent_supported_by_ruleset(_python(), BYTEFRAY_RULESET_V4_ID)
    assert not agent_supported_by_ruleset(_python(1), BYTEFRAY_RULESET_V4_ID)
    assert not agent_supported_by_ruleset(_python(), BYTEFRAY_RULESET_V2_ID)


def test_scheduler_is_round_robin_with_two_slot_chunks() -> None:
    states = [_FakeState("A"), _FakeState("B"), _FakeState("C")]
    calls: list[str] = []
    RULESET_V4.run_scheduler(
        states, 3, lambda state, slot: calls.append(f"{state.name}{slot}"), tick=1
    )
    assert calls == ["A0", "A1", "B0", "B1", "C0", "C1", "A2", "B2", "C2"]


@pytest.mark.parametrize(
    ("alive_count", "tick", "expected"),
    [
        (3, 1, TerminationDecision(False, None)),
        (1, 1, TerminationDecision(True, TerminationReason.LAST_AGENT_STANDING)),
        (0, 1, TerminationDecision(True, TerminationReason.ALL_AGENTS_DEAD)),
        (2, 10, TerminationDecision(True, TerminationReason.TICK_LIMIT)),
        (1, 10, TerminationDecision(True, TerminationReason.LAST_AGENT_STANDING)),
    ],
)
def test_termination_semantics_are_preserved(
    alive_count: int, tick: int, expected: TerminationDecision
) -> None:
    assert RULESET_V4.resolve_termination(
        alive_count=alive_count, tick=tick, max_ticks=10
    ) == expected


def test_policy_and_decision_are_immutable() -> None:
    with pytest.raises(FrozenInstanceError):
        RULESET_V4.ruleset_id = "tampered"  # type: ignore[misc]
    decision = RULESET_V4.resolve_termination(alive_count=2, tick=1, max_ticks=10)
    with pytest.raises(FrozenInstanceError):
        decision.terminated = True  # type: ignore[misc]


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("core_placement", "invented"),
        ("process_selection", "invented"),
        ("movement_stride", "invented"),
        ("movement_displacement", "invented"),
    ],
)
def test_policy_rejects_unknown_semantic_modes(field: str, value: str) -> None:
    with pytest.raises(ValueError):
        RulesetPolicy("probe", **{field: value})


def test_movement_displacement_resolution_and_proportionality() -> None:
    arenas = [512, 1024, 4096, 16384, 65536]
    operands = [0, 1, -1, 2, -2, 40, -40, 64, -64]

    # Literal policies: stable v4, Phase 4B raw-scale, Phase 4C scale-move
    # Always return requested delta unchanged
    for a in arenas:
        for op in operands:
            assert RULESET_V4.resolve_movement_displacement(op, a) == op
            assert RULESET_V6_RESEARCH_SCALE.resolve_movement_displacement(op, a) == op
            assert RULESET_V6_RESEARCH_SCALE_MOVE.resolve_movement_displacement(op, a) == op

    # Proportional policy (Phase 4D):
    # Anchor invariant: at A=512, actual_delta == requested_delta exactly
    for op in operands:
        assert (
            RULESET_V6_RESEARCH_SCALE_MOVE_PROPORTIONAL.resolve_movement_displacement(
                op, 512
            )
            == op
        )

    # Scaling factors:
    # 512: 1x, 1024: 2x, 4096: 8x, 16384: 32x, 65536: 128x
    expected_factors = {
        512: 1,
        1024: 2,
        4096: 8,
        16384: 32,
        65536: 128,
    }
    for a, factor in expected_factors.items():
        for op in operands:
            actual = RULESET_V6_RESEARCH_SCALE_MOVE_PROPORTIONAL.resolve_movement_displacement(
                op, a
            )
            expected = op * factor
            assert actual == expected
            # Sign symmetry: actual(-op) == -actual(op)
            neg_actual = RULESET_V6_RESEARCH_SCALE_MOVE_PROPORTIONAL.resolve_movement_displacement(
                -op, a
            )
            assert neg_actual == -actual
