"""Product-facing Ruleset choices for Agent Designer direct matches."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from battle_engine.ruleset_policy import (
    BYTEFRAY_RULESET_V4_ID,
    UnknownRulesetError,
    agent_supported_by_ruleset,
    resolve_ruleset_policy,
)


@dataclass(frozen=True)
class DesignerRulesetOption:
    ruleset_id: str
    label: str


# v4.0.0-rc1 Phase 2: the permanent stable identity (see
# docs/research/v4/V4_RC1_PHASE2_STABLE_CONTRACT_PROMOTION.md), gameplay-
# identical to alpha2. V6 Phase 2B.10 Scope B removed the alpha1/alpha2
# options that used to sit alongside this one (see
# docs/research/v6/V6_PHASE2B10_SCOPE_B_V4_ALPHA_RETIREMENT.md); V6 Phase
# 2B.12 removed ``RULESET_V1_OPTION``/``RULESET_V2_OPTION`` the same way,
# retiring Agent API v1 and VM/blob execution entirely
# (docs/research/v6/V6_PHASE2B12_SCOPE_C_RUNTIME_RETIREMENT.md). This is now
# the only Ruleset option any Designer surface offers, so the "(Agent API
# v2)" qualifier no longer distinguishes it from anything.
RULESET_V4_OPTION = DesignerRulesetOption(
    BYTEFRAY_RULESET_V4_ID, "Ruleset v4 — Current / Recommended"
)

# V5 Alpha 1 Phase 1: the Designer's canonical new-session/fresh-state
# Ruleset selection. Before any agent is known (a freshly constructed
# Simple/Advanced/Development combo, before ``setAgents``/a real selection
# ever runs), ``populate_ruleset_combo`` selects this identity rather than
# leaving Qt's incidental "item 0" default -- which, since ``RULESET_V2_
# OPTION`` is listed first in every option tuple below for unrelated
# compatibility-ordering reasons (see ``DESIGNER_RULESET_OPTIONS``'s own
# docstring), silently made an Agent API v1 ruleset look like the
# recommended V5 experience. ``bytefray-rules-4`` is the permanent stable
# process-agent identity and, per docs/research/v5/
# V5_ALPHA1_CONSOLIDATION_AND_PLAN.md's "default cleanly to stable V4" and
# docs/research/v5/V5_ALPHA1_MAINTENANCE_PHASE4_RELEASE_SURFACE_AUDIT.md's
# "V5 ordinary API-v2 default", is the already-documented canonical V5
# default -- this only wires the Designer up to actually start there. This
# only changes the *pre-agent-selection* default: once a real agent or
# roster is known, ``sync_ruleset_choices_for_metadata`` (Development,
# Evaluation) or Simple/Advanced's own Ruleset-first filtering takes over
# exactly as before, using the same unchanged product-preference order.
DEFAULT_DESIGNER_RULESET_ID = BYTEFRAY_RULESET_V4_ID

# V6 Phase 2B.12 narrowed every Designer Ruleset surface to the single
# retained control (docs/research/v6/V6_PHASE2B12_SCOPE_C_RUNTIME_RETIREMENT.md):
# Agent API v1 and VM/blob execution are retired, so ``bytefray-rules-4`` is
# the only Ruleset any of them can offer. Kept as separate tuples (rather
# than collapsed into one shared constant) so a future Ruleset 6 has three
# obvious, independently-decidable places to be added back, mirroring the
# pre-2B.12 precedent these replace.
SIMPLE_RULESET_OPTIONS = (RULESET_V4_OPTION,)
EVALUATION_RULESET_OPTIONS = (RULESET_V4_OPTION,)
DESIGNER_RULESET_OPTIONS = (RULESET_V4_OPTION,)

RULESET_DESCRIPTION = (
    "Ruleset v4 is Bytefray's current, permanent process-agent gameplay "
    "contract and requires Agent API v2; it places entrant cores from the "
    "match seed and rotates action slots between an entrant's own "
    "processes."
)


def ruleset_supports_runtime_kinds(ruleset_id: str, kinds: set[str]) -> bool:
    """Project the engine policy's authoritative *runtime-kind* compatibility.

    Deliberately answers only half the compatibility question: with a
    single retained Ruleset, every Designer surface that decides which
    Rulesets to *offer* uses :func:`ruleset_supports_agent_metadata`
    instead, which also checks Agent API version. This remains for the
    launch guard in ``validate_designer_ruleset``, where the runtime kind
    genuinely is the whole question -- it is what rejects a VM/blob agent
    (no longer executable under any Ruleset) before a match launches.
    """
    try:
        policy = resolve_ruleset_policy(ruleset_id)
    except UnknownRulesetError:
        return False
    return not policy.unsupported_runtime_kinds(kinds)


def ruleset_supports_agent_metadata(
    ruleset_id: str, metadata: Iterable[object]
) -> bool:
    """Does ``ruleset_id`` support *every* selected entrant's metadata?

    The single question every Designer surface asks about Ruleset
    compatibility, delegating to the engine's own
    :func:`~battle_engine.ruleset_policy.agent_supported_by_ruleset`
    predicate -- the same one ``NativeMatchService`` enforces before a match
    executes -- so the GUI cannot present a Ruleset the engine would then
    reject, and cannot drift from it as Rulesets are added.

    ``metadata`` is one entry per *selected* entrant, in any projection that
    predicate accepts (an ``AgentRow.meta`` mapping, an ``AgentSpec``).
    ``None`` entries mean "this selector has nothing selected yet" and
    impose no constraint; an empty selection is likewise unconstrained,
    since there is nothing for a Ruleset to be incompatible with. Anything
    genuinely selected but unreadable fails closed, exactly as
    :func:`agent_row_supported_by_ruleset` already does.
    """

    selected = [item for item in metadata if item is not None]
    return all(agent_supported_by_ruleset(item, ruleset_id) for item in selected)


def best_designer_ruleset_for_agents(
    metadata: Iterable[object],
    options: Iterable[DesignerRulesetOption] = DESIGNER_RULESET_OPTIONS,
) -> str | None:
    """The first product-preferred Ruleset supporting every selected entrant.

    Returns ``None`` when no offered Ruleset supports the selection, which
    is a real state a Designer surface must show (and disable execution
    for) rather than paper over with an incompatible fallback.
    """

    selected = tuple(metadata)
    for option in options:
        if ruleset_supports_agent_metadata(option.ruleset_id, selected):
            return option.ruleset_id
    return None


def agent_row_metadata(row: object) -> object:
    """The compatibility metadata carried by one catalog row.

    An unreadable row projects to an empty mapping rather than ``None`` on
    purpose: ``None`` means "nothing is selected here" and is unconstrained,
    while a row that *is* selected but carries no usable metadata must fail
    closed, exactly as :func:`agent_row_supported_by_ruleset` already makes
    it.
    """

    metadata = getattr(row, "meta", None)
    return metadata if isinstance(metadata, dict) else {}


def validate_designer_ruleset(ruleset_id: str, kinds: set[str]) -> None:
    """Keep programmatic launch callers behind the engine policy boundary."""
    if not ruleset_supports_runtime_kinds(ruleset_id, kinds):
        kinds_text = ", ".join(sorted(kinds)) or "selected"
        raise ValueError(
            f"Ruleset {ruleset_id} does not support {kinds_text} entrants. "
            "Only Agent API v2 (process) Python agents are executable."
        )


def agent_row_supported_by_ruleset(row: object, ruleset_id: str) -> bool:
    """Project a catalog row through the engine's canonical predicate."""

    metadata = getattr(row, "meta", None)
    return isinstance(metadata, dict) and agent_supported_by_ruleset(
        metadata, ruleset_id
    )


def validate_designer_agent_rows(
    ruleset_id: str, rows: Iterable[object]
) -> None:
    """Reject stale/programmatic Designer launches with incompatible agents."""

    selected = tuple(rows)
    incompatible = [
        str(getattr(row, "agent_id", "") or getattr(row, "name", "<unknown>"))
        for row in selected
        if not agent_row_supported_by_ruleset(row, ruleset_id)
    ]
    if incompatible:
        names = ", ".join(incompatible)
        raise ValueError(
            f"Ruleset {ruleset_id} does not support the selected agent metadata: "
            f"{names}."
        )
