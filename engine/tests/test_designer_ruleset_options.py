"""Agent Designer's agent-compatibility checks for its one Ruleset.

The Designer offers no Ruleset control: every workflow launches under
``DESIGNER_RULESET_ID`` (Active Sensing). What remains is the compatibility
question it must answer exactly as the engine does, for every selected
entrant, before a launch.
"""

from __future__ import annotations

import pytest
from battle_engine.rules import BYTEFRAY_RULESET_V6_ALPHA1_ID
from battle_engine.ruleset_policy import (
    OMITTED_RULESET_CANDIDATES,
    PRODUCT_RULESET_IDS,
    agent_supported_by_ruleset,
)

from app.services.agent_catalog import AgentRow
from app.services.ruleset_options import (
    DESIGNER_RULESET_ID,
    agent_row_metadata,
    agent_row_supported,
    agents_supported,
    validate_designer_agent_rows,
)

_API_V1 = {"kind": "python", "api_version": 1}
_API_V2 = {"kind": "python", "api_version": 2}
_SENSING = {"kind": "python", "api_version": 2, "capabilities": {"version": 1, "required": ["sense"]}}
_VM = {"kind": "builtin"}
_UNVERSIONED = {"kind": "python"}


def test_designer_launches_under_the_one_product_ruleset() -> None:
    assert DESIGNER_RULESET_ID == BYTEFRAY_RULESET_V6_ALPHA1_ID
    assert PRODUCT_RULESET_IDS == {DESIGNER_RULESET_ID}
    # The Designer and an omitted CLI --ruleset agree.
    assert OMITTED_RULESET_CANDIDATES == (DESIGNER_RULESET_ID,)


@pytest.mark.parametrize(
    "metadata", [_API_V1, _API_V2, _SENSING, _VM, _UNVERSIONED, {"kind": "blob"}, {}]
)
def test_designer_compatibility_always_agrees_with_engine_policy(metadata: dict[str, object]) -> None:
    """The anti-drift guard: the Designer never answers "can this agent run?"
    differently from the engine that will execute the match."""

    assert agents_supported([metadata]) is agent_supported_by_ruleset(metadata, DESIGNER_RULESET_ID)


@pytest.mark.parametrize(
    ("metadata", "compatible"),
    [(_API_V1, False), (_API_V2, True), (_SENSING, True), (_VM, False), (_UNVERSIONED, False)],
)
def test_only_api_v2_python_agents_can_run(metadata: dict[str, object], compatible: bool) -> None:
    assert agents_supported([metadata]) is compatible


def test_compatibility_is_evaluated_across_the_whole_selected_roster() -> None:
    """One incompatible entrant disqualifies the whole match."""

    assert agents_supported([_API_V2, _SENSING])
    assert not agents_supported([_API_V2, _API_V1])
    assert not agents_supported([_SENSING, _VM])


def test_unselected_slots_impose_no_constraint_but_selected_ones_fail_closed() -> None:
    assert agents_supported([])
    assert agents_supported([None, None])
    assert agents_supported([_API_V2, None])
    # A row that *is* selected but carries unusable metadata fails closed.
    assert not agents_supported([{}])


def test_catalog_rows_and_launch_validation_include_agent_api() -> None:
    api_v1 = AgentRow("legacy", "/agents/legacy", None, _API_V1)
    api_v2 = AgentRow("process", "/agents/process", None, _API_V2)
    vm = AgentRow("runner", "/agents/runner", None, _VM)

    assert agent_row_supported(api_v2)
    assert not agent_row_supported(api_v1)
    assert not agent_row_supported(vm)
    assert not agent_row_supported(object())

    validate_designer_agent_rows((api_v2, api_v2))
    with pytest.raises(ValueError, match="selected agents: legacy") as caught:
        validate_designer_agent_rows((api_v1, api_v2))
    assert "Only Agent API v2" in str(caught.value)


def test_row_metadata_projection_fails_closed_but_is_distinct_from_no_selection() -> None:
    row = AgentRow("proc", "/agents/proc", None, _API_V2)
    assert agent_row_metadata(row) == _API_V2
    # An unreadable row projects to an empty mapping (fails closed), never to
    # None, which would read as "nothing selected" and impose no constraint.
    assert agent_row_metadata(object()) == {}
