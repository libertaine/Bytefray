"""Agent compatibility for Agent Designer matches.

Active Sensing (``bytefray-rules-6-alpha1``) is Bytefray's only Ruleset, so
the Designer offers no Ruleset control. Every Designer launch still names
:data:`DESIGNER_RULESET_ID` explicitly -- a launch never depends on the
engine's omitted-Ruleset resolution -- and every surface filters agents
through the engine's own compatibility predicate, which still rejects a
non-Agent-API-v2 agent before a match starts.
"""

from __future__ import annotations

from collections.abc import Iterable

from battle_engine.rules import BYTEFRAY_RULESET_V6_ALPHA1_ID
from battle_engine.ruleset_policy import agent_supported_by_ruleset

#: The Ruleset every Designer match, development test and evaluation runs under.
DESIGNER_RULESET_ID = BYTEFRAY_RULESET_V6_ALPHA1_ID

#: Shown where a surface has no agent it can run, paired with disabled
#: execution rather than a launch the engine would reject.
NO_COMPATIBLE_AGENTS_EXPLANATION = (
    "No compatible agents were found. Only Agent API v2 (process) Python "
    "agents can run; create or import one, then refresh."
)

#: Shown when an agent that is selected cannot run.
INCOMPATIBLE_SELECTION_EXPLANATION = (
    "The selected agents cannot run together. Only Agent API v2 (process) "
    "Python agents can run; select agents that satisfy that."
)


def agents_supported(metadata: Iterable[object]) -> bool:
    """Does the Designer's Ruleset support *every* selected entrant's metadata?

    ``metadata`` is one entry per *selected* entrant, in any projection the
    engine's :func:`~battle_engine.ruleset_policy.agent_supported_by_ruleset`
    accepts (an ``AgentRow.meta`` mapping, an ``AgentSpec``). ``None``
    entries mean "this selector has nothing selected yet" and impose no
    constraint; an empty selection is likewise unconstrained.
    """

    return all(
        agent_supported_by_ruleset(item, DESIGNER_RULESET_ID)
        for item in metadata
        if item is not None
    )


def agent_row_metadata(row: object) -> object:
    """The compatibility metadata carried by one catalog row.

    An unreadable row projects to an empty mapping rather than ``None`` on
    purpose: ``None`` means "nothing is selected here" and is unconstrained,
    while a row that *is* selected but carries no usable metadata must fail
    closed, exactly as :func:`agent_row_supported` does.
    """

    metadata = getattr(row, "meta", None)
    return metadata if isinstance(metadata, dict) else {}


def agent_row_supported(row: object) -> bool:
    """Project a catalog row through the engine's canonical predicate."""

    metadata = getattr(row, "meta", None)
    return isinstance(metadata, dict) and agent_supported_by_ruleset(
        metadata, DESIGNER_RULESET_ID
    )


def validate_designer_agent_rows(rows: Iterable[object]) -> None:
    """Reject stale/programmatic Designer launches with incompatible agents."""

    incompatible = [
        str(getattr(row, "agent_id", "") or getattr(row, "name", "<unknown>"))
        for row in rows
        if not agent_row_supported(row)
    ]
    if incompatible:
        names = ", ".join(incompatible)
        raise ValueError(
            f"Ruleset {DESIGNER_RULESET_ID} does not support the selected agents: "
            f"{names}. Only Agent API v2 (process) Python agents are executable."
        )
