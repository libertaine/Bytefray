"""Unit coverage for the sole executable Ruleset policy after Scope C."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, dataclass

import pytest
from battle_engine.ruleset_policy import (
    BYTEFRAY_RULESET_V2_ALPHA1_ID,
    BYTEFRAY_RULESET_V2_ALPHA11_ID,
    BYTEFRAY_RULESET_V2_ID,
    BYTEFRAY_RULESET_V3_ALPHA1_ID,
    BYTEFRAY_RULESET_V4_ALPHA1_ID,
    BYTEFRAY_RULESET_V4_ALPHA2_ID,
    BYTEFRAY_RULESET_V4_ID,
    OMITTED_RULESET_CANDIDATES,
    PROCESS_RULESET_IDS,
    RULESET_V4,
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


def test_stable_v4_is_the_only_registered_and_automatic_policy() -> None:
    assert resolve_ruleset_policy(BYTEFRAY_RULESET_V4_ID) is RULESET_V4
    assert OMITTED_RULESET_CANDIDATES == (BYTEFRAY_RULESET_V4_ID,)
    assert PROCESS_RULESET_IDS == frozenset({BYTEFRAY_RULESET_V4_ID})
    assert resolve_omitted_ruleset_for_agents(None, [_python()]) == BYTEFRAY_RULESET_V4_ID


def test_stable_v4_fields_remain_pinned() -> None:
    assert RULESET_V4.supported_runtime_kinds == frozenset({"python"})
    assert RULESET_V4.supported_python_api_versions == frozenset({2})
    assert (
        RULESET_V4.scheduler_mode,
        RULESET_V4.scheduler_chunk_size,
        RULESET_V4.scheduler_rotate_start,
        RULESET_V4.core_placement,
        RULESET_V4.process_selection,
    ) == ("chunked", 2, True, "seeded", "round_robin")


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
    [("core_placement", "invented"), ("process_selection", "invented")],
)
def test_policy_rejects_unknown_semantic_modes(field: str, value: str) -> None:
    with pytest.raises(ValueError):
        RulesetPolicy("probe", **{field: value})
