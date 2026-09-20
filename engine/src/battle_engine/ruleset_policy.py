"""Executable Ruleset policy and fail-closed resolver.

``rules.py`` is the frozen, dependency-free record of Ruleset *identity*
(``BYTEFRAY_RULESET_ID`` and its historical-alias/provenance vocabulary),
deliberately kept free of anything executable so it can sit underneath the
runtime, artifact, and evaluation layers without risk of an import cycle
(see its own module docstring). This module is the next layer up: it pairs
that identity with the *executable* Ruleset semantics that, as of v1.5
Phase 4, have a single shared implementation -- entrant scheduling (all
Rulesets dispatch through ``battle_engine.scheduler.run_chunked_quota`` via
:meth:`RulesetPolicy.run_scheduler`; sequential-mode Rulesets supply a
``chunk_size`` equal to the entrant quota with no start rotation, which
preserves the original declaration/seat-order sequential-turn behavior that
``run_sequential_quota`` -- still exported, unchanged, and directly tested,
just no longer on this dispatch path -- used to provide directly) and match
termination decision/reason (``RulesetPolicy.resolve_termination``) -- and
provides one fail-closed resolver from a Ruleset ID string to its policy.

This is deliberately a thin seam, not a Ruleset framework. Exactly one
Ruleset is executable (stable Ruleset v4); the resolver exists so runtime construction
has one obvious place to obtain Ruleset-owned scheduling/termination
semantics instead of duplicating them per runtime, and so an unrecognized
Ruleset ID fails before any gameplay executes rather than silently running
as a retired or unknown identity. Scoring, statistics, and winner resolution are not yet
Ruleset-policy-owned -- see ``docs/archive/v1/V1_5_PHASE4_TERMINATION_POLICY.md`` for
what remains outside this seam and why.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from enum import Enum
from typing import ClassVar

from battle_engine.rules import (
    BYTEFRAY_RULESET_V4_ALPHA1_ID,
    BYTEFRAY_RULESET_V4_ALPHA2_ID,
    BYTEFRAY_RULESET_V4_ID,
)
from battle_engine.scheduler import StateT, run_chunked_quota


class TerminationReason(str, Enum):

    """Why a completed Ruleset-v1 match stopped.

    A ``str`` subclass so its ``.value`` -- the persisted/serialized form
    used in ``result.json`` and the golden corpus -- is exactly its member
    name's lowercase spelling; this representation predates Phase 4 and is
    unchanged by it (see ``docs/archive/v1/V1_5_PHASE4_TERMINATION_POLICY.md``'s
    "Reason representation").
    """

    LAST_AGENT_STANDING = "last_agent_standing"
    ALL_AGENTS_DEAD = "all_agents_dead"
    TICK_LIMIT = "tick_limit"


@dataclass(frozen=True)
class TerminationDecision:
    """Whether a Ruleset-v1 match has ended, and why.

    ``reason`` is ``None`` exactly when ``terminated`` is ``False`` -- the
    match should continue and there is nothing to report yet.
    """

    terminated: bool
    reason: TerminationReason | None


@dataclass(frozen=True)
class RulesetPolicy:
    """One Ruleset's executable policy: identity, scheduler, and termination.

    Immutable and intentionally narrow -- it exposes only what current
    runtime code actually routes through it (scheduling, the termination
    decision/reason, and -- as of Beta1 Phase 2 -- which entrant runtime
    kinds this Ruleset supports executing). It has no knowledge of
    persistence, replay/result schemas, or evaluation; those remain the
    concern of the callers that hold a ``RulesetPolicy``, not of the policy
    itself.

    ``supported_runtime_kinds``: ``None`` means a policy imposes no runtime-kind
    restriction; a non-``None`` frozenset is exhaustive. The sole registered
    policy is explicitly Python-only and supports only Agent API v2. Retired
    identities have no policy objects here; their constants and provenance
    remain solely for historical artifact recognition.
    """

    ruleset_id: str
    supported_runtime_kinds: frozenset[str] | None = None
    supported_python_api_versions: frozenset[int] | None = None
    scheduler_mode: str = "sequential"
    scheduler_chunk_size: int | None = None
    scheduler_rotate_start: bool = False
    core_placement: str = "zero"
    process_selection: str = "priority"

    #: Every value :attr:`core_placement` may take. ``"zero"`` is every
    #: Ruleset whose omitted start addresses historically defaulted to the
    #: literal 0 (Ruleset v1 and the frozen v2/v3 alpha identities);
    #: ``"seat_spread"`` is the evenly-spaced seat layout the RC2 placement
    #: fix introduced for the permanent Ruleset v2 identity and every
    #: Ruleset since; ``"seeded"`` is v4 alpha2's seed-derived,
    #: minimum-separated placement.
    CORE_PLACEMENT_MODES: ClassVar[frozenset[str]] = frozenset(
        {"zero", "seat_spread", "seeded"}
    )
    #: Every value :attr:`process_selection` may take. ``"priority"`` is
    #: Alpha1's frozen "always resume scanning from the first declared
    #: process" rule; ``"round_robin"`` is Alpha2's order-independent
    #: rotation. Only process Rulesets (Agent API v2) read this at all.
    PROCESS_SELECTION_MODES: ClassVar[frozenset[str]] = frozenset(
        {"priority", "round_robin"}
    )

    def __post_init__(self) -> None:
        if self.core_placement not in self.CORE_PLACEMENT_MODES:
            raise ValueError(
                f"unknown core_placement {self.core_placement!r} for Ruleset "
                f"{self.ruleset_id!r}; expected one of "
                f"{sorted(self.CORE_PLACEMENT_MODES)!r}"
            )
        if self.process_selection not in self.PROCESS_SELECTION_MODES:
            raise ValueError(
                f"unknown process_selection {self.process_selection!r} for "
                f"Ruleset {self.ruleset_id!r}; expected one of "
                f"{sorted(self.PROCESS_SELECTION_MODES)!r}"
            )

    def unsupported_runtime_kinds(self, kinds: Iterable[str]) -> frozenset[str]:
        """Return which of ``kinds`` this Ruleset does not support executing.

        The authoritative Ruleset/runtime-kind compatibility check (Beta1
        Phase 2): callers -- currently only
        :class:`~battle_engine.match_service.NativeMatchService` -- pass the
        resolved entrant runtime-kind set for one match request and reject
        before any entrant executes if this returns non-empty. Returns an
        empty ``frozenset`` whenever :attr:`supported_runtime_kinds` is
        ``None`` (no restriction) or every requested kind is already
        supported.
        """

        if self.supported_runtime_kinds is None:
            return frozenset()
        return frozenset(kinds) - self.supported_runtime_kinds

    def supports_agent(self, *, kind: str, api_version: int | None = None) -> bool:
        """Return whether one discovered agent can execute under this Ruleset.

        Discovery uses ``builtin``/``blob`` for VM-backed agents while match
        execution uses ``vm``.  Those spellings are normalized here so every
        caller reaches the same runtime/API decision.  Python metadata without
        an explicit integer API version fails closed, matching the loader.
        Unknown runtime kinds fail closed as well.
        """

        runtime_kind = _canonical_runtime_kind(kind)
        if runtime_kind is None or self.unsupported_runtime_kinds({runtime_kind}):
            return False
        if runtime_kind != "python" or self.supported_python_api_versions is None:
            return True
        if isinstance(api_version, bool) or not isinstance(api_version, int):
            return False
        return api_version in self.supported_python_api_versions

    def run_scheduler(
        self,
        states: Iterable[StateT],
        quota: int,
        execute_slot: Callable[[StateT, int], None],
        *,
        tick: int = 1,
    ) -> None:
        """Run this Ruleset's entrant scheduler.

        Dispatches to :func:`battle_engine.scheduler.run_chunked_quota`.
        """

        chunk_size = quota if self.scheduler_mode == "sequential" else (self.scheduler_chunk_size or 1)
        run_chunked_quota(
            states,
            quota,
            execute_slot,
            chunk_size=chunk_size,
            rotate_start=self.scheduler_rotate_start,
            tick=tick,
        )



    def resolve_termination(
        self,
        *,
        alive_count: int,
        tick: int,
        max_ticks: int,
    ) -> TerminationDecision:
        """Decide whether a Ruleset-v1 match has ended, and why.

        Ruleset v1's termination rule, identical across VM, unsupervised
        Python, and supervised Python: no entrants alive ends the match as
        :attr:`TerminationReason.ALL_AGENTS_DEAD`; exactly one alive ends it
        as :attr:`TerminationReason.LAST_AGENT_STANDING`; otherwise reaching
        the configured tick limit ends it as
        :attr:`TerminationReason.TICK_LIMIT`. Alive-count-based conditions
        take precedence over the tick limit -- a match that reaches the
        limit with zero or one entrant alive is reported as
        ``ALL_AGENTS_DEAD``/``LAST_AGENT_STANDING``, never ``TICK_LIMIT``.

        This is the whole of Ruleset-v1's termination semantic: it takes no
        runtime-kind, entrant-state, or lifecycle information beyond these
        three integers, and is called both mid-match (to decide whether a
        runtime should keep ticking, using only ``.terminated``) and once a
        match has already stopped (to obtain the final ``.reason``) -- see
        ``docs/archive/v1/V1_5_PHASE4_TERMINATION_POLICY.md`` for exactly where each
        runtime calls this.
        """

        if alive_count == 0:
            return TerminationDecision(True, TerminationReason.ALL_AGENTS_DEAD)
        if alive_count == 1:
            return TerminationDecision(True, TerminationReason.LAST_AGENT_STANDING)
        if tick >= max_ticks:
            return TerminationDecision(True, TerminationReason.TICK_LIMIT)
        return TerminationDecision(False, None)


# Ruleset v1 -- the original VM/blob-and-Agent-API-v1 identity (see
# docs/RULES.md). Retired from executable registration by V6 Phase 2B.12
# Scope C (docs/research/v6/V6_PHASE2B12_SCOPE_C_RUNTIME_RETIREMENT.md),
# alongside Agent API v1 and VM/blob execution entirely: it was the only
# registered Ruleset that ever executed a VM/blob entrant. The ID constant
# (``rules.BYTEFRAY_RULESET_ID``, still ``"bytefray-rules-1"``) is kept --
# unlike the removed ``RulesetPolicy`` object -- because historical
# artifacts recorded under it (including the 673 in this repository's own
# corpus that carry no explicit ``ruleset_id`` and are recovered as this
# identity, see ``result_model.resolve_result_ruleset``/``replay.
# resolve_replay_ruleset``) must remain readable, attributable, and
# replayable indefinitely. ``resolve_ruleset_policy`` now raises
# ``UnknownRulesetError`` for it, like any other unregistered ID.


# v2.0.0-alpha.1's experimental identity (see
# docs/V2_0_ALPHA_ARCHITECTURE.md Sec 6/7). Closed research, retired from
# executable registration by V6 Phase 2B.9
# (docs/research/v6/V6_PHASE2B9_SCOPE_A_RULESET_RETIREMENT.md): it was never
# selectable from any CLI, Designer, or evaluation-preset surface, and its
# only reachable path was the low-level Python API. The ID constant is kept
# -- unlike the removed ``RulesetPolicy`` object -- because historical
# artifacts recorded under it must remain readable, attributable, and
# replayable indefinitely (see ``rules.py``'s alias/provenance module
# docstring and ``VULNERABLE_CORE_RULESET_IDS``/``OBSERVABLE_CORE_RULESET_IDS``
# in ``python_runtime.py``, whose membership for this ID is retained for
# exactly that reason). ``resolve_ruleset_policy`` now raises
# ``UnknownRulesetError`` for it, like any other unregistered ID.
BYTEFRAY_RULESET_V2_ALPHA1_ID = "bytefray-rules-2-alpha1"


# v2.0.0-alpha.11's experimental identity (see
# docs/V2_0_ALPHA11_RULESET_V2_CANDIDATE_RESOLUTION.md). Closed research,
# retired from executable registration by V6 Phase 2B.9 for the same reason
# and under the same terms as ``bytefray-rules-2-alpha1`` immediately above.
# Its evidence-backed semantics were promoted into the permanent
# ``bytefray-rules-2`` identity below at v2.0.0-beta1; that promotion proof
# now lives as a frozen-golden characterization of ``bytefray-rules-2``
# rather than a live comparison against this identity -- see
# ``engine/tests/test_ruleset_v2_promotion_equivalence.py``'s module
# docstring for the conversion and its provenance.
BYTEFRAY_RULESET_V2_ALPHA11_ID = "bytefray-rules-2-alpha11"


# v2.0.0-beta1's permanent identity (see docs/V2_0_BETA1_PLAN.md and
# docs/V2_0_ALPHA11_RULESET_V2_CANDIDATE_RESOLUTION.md Sec 25-26). Retired
# from executable registration by V6 Phase 2B.12 Scope C
# (docs/research/v6/V6_PHASE2B12_SCOPE_C_RUNTIME_RETIREMENT.md), alongside
# Agent API v1 execution entirely: this was the current gameplay contract
# for every Agent API v1 Python roster, and 58% of this repository's own
# historical artifact corpus was recorded under it. The ID constant is kept
# -- unlike the removed ``RulesetPolicy`` object -- because those historical
# artifacts must remain readable, attributable, and replayable
# indefinitely. ``resolve_ruleset_policy`` now raises
# ``UnknownRulesetError`` for it, like any other unregistered ID. Its
# promotion proof from ``bytefray-rules-2-alpha11`` -- the frozen-golden
# characterization Phase 2B.9 converted -- was deliberately deleted by
# Phase 2B.12 rather than kept, since once neither side of that comparison
# executes at all, a frozen-vs-frozen digest no longer detects any live
# drift; the historical evidence survives in Git history and in Phase
# 2B.9's own report.
BYTEFRAY_RULESET_V2_ID = "bytefray-rules-2"


# v3 research Phase 2's experimental bounded-locality identity (see
# docs/V3_PHASE2_LOCALITY_FEASIBILITY.md and
# docs/research/v6/V6_PHASE2B7_RULESET3_ALPHA1_DISPOSITION.md). Closed
# research -- Phase 2B.7 found no stable Ruleset 3 was ever built on it, and
# V6 Phase 2B.9 retired it from executable registration on the same terms as
# the two Ruleset-2 alphas above: never selectable from any CLI, Designer,
# or evaluation-preset surface; reachable only through the low-level Python
# API. The ID constant is kept for historical artifact recognition (this
# checkout's corpus alone has 6,984 recorded results under it, all of which
# remain readable and replayable); the locality gameplay mechanic itself
# (``battle_engine.python_runtime``'s locus/reach machinery, gated
# exclusively on this ID) was removed as dead code by Phase 2B.9, since this
# was its only executable identity.
BYTEFRAY_RULESET_V3_ALPHA1_ID = "bytefray-rules-3-alpha1"


# v4 research: K=2 chunked round-robin with deterministic rotating start.
# R0/R0b/R0c selected this policy as the scheduler research closure.
#
# ``bytefray-rules-4-alpha1``'s ``RulesetPolicy`` object (``core_placement=
# "seat_spread"``, ``process_selection="priority"``) and
# ``bytefray-rules-4-alpha2``'s (identical except ``core_placement=
# "seeded"``, ``process_selection="round_robin"`` -- the two gameplay
# semantics the Phase 4 controlled gameplay study produced evidence for,
# docs/archive/v4/V4_ALPHA2_PHASE4_GAMEPLAY_STUDY.md Sections F2/G,
# docs/V4_ALPHA2_DESIGN.md) were both retired from executable registration
# by V6 Phase 2B.10 Scope B
# (docs/research/v6/V6_PHASE2B10_SCOPE_B_V4_ALPHA_RETIREMENT.md), following
# the same pattern and terms Phase 2B.9 used for the three Class-1
# identities above: both were reachable from the CLI, Designer, and
# evaluation surfaces (unlike those three), but no unique gameplay code was
# deleted -- ``process_runtime.py`` contains zero Ruleset-identity
# branching, so each alpha's entire behavioral difference from the stable
# control below was its two policy-field values, now gone with the
# objects. Both ID constants are kept -- unlike the removed
# ``RulesetPolicy`` objects -- because historical artifacts recorded under
# them (respectively 24% and under 0.1% of this repository's own corpus at
# the time of the V6 Phase 2B.8 audit) must remain readable, attributable,
# and replayable indefinitely. Alpha1's membership in
# ``VULNERABLE_CORE_RULESET_IDS``/``OBSERVABLE_CORE_RULESET_IDS``
# (``python_runtime.py``) is retained for exactly that reason (T-9); alpha2
# was never a member of either. ``resolve_ruleset_policy`` now raises
# ``UnknownRulesetError`` for both, like any other unregistered ID.
#
# Alpha2's fields were promoted verbatim into the permanent
# ``bytefray-rules-4`` identity below at v4.0.0-rc1 Phase 2; that
# promotion's release-blocking behavioral proof -- originally a live
# two-identity comparison against alpha2 -- now lives as a frozen-golden
# characterization of ``bytefray-rules-4`` (task Sec 3), since alpha2 can
# no longer be executed to produce a live comparison value. See
# ``engine/tests/test_v4_stable_ruleset_equivalence.py``'s module docstring
# for the conversion and its provenance, and
# ``engine/tests/test_v4_historical_immutability.py``'s frozen fixtures for
# alpha1's permanent identity/isolation regression coverage.

# v4.0.0-rc1 Phase 2: the permanent stable identity (see
# docs/research/v4/V4_RC1_PHASE2_STABLE_CONTRACT_PROMOTION.md and
# BYTEFRAY_RULESET_V4_ID's own docstring in rules.py for the promotion
# rationale). Every field below is deliberately the same as
# ``bytefray-rules-4-alpha2``'s retired ``RulesetPolicy`` object used to be
# (frozen-golden-verified equal, not merely documented -- see
# ``test_v4_stable_ruleset_equivalence.py``): this is one semantic
# implementation (battle_engine.scheduler.run_chunked_quota,
# battle_engine.python_runtime's seeded placement/round-robin process
# selection, all gated on `core_placement`/`process_selection`/
# `scheduler_*`, never on `ruleset_id` itself), exactly the shape the
# alpha11 -> permanent-v2 promotion already established (now preserved as
# a frozen-golden characterization since V6 Phase 2B.9 retired the alpha11
# policy object -- see
# ``engine/tests/test_ruleset_v2_promotion_equivalence.py``).
RULESET_V4 = RulesetPolicy(
    ruleset_id=BYTEFRAY_RULESET_V4_ID,
    supported_runtime_kinds=frozenset({"python"}),
    supported_python_api_versions=frozenset({2}),
    scheduler_mode="chunked",
    scheduler_chunk_size=2,
    scheduler_rotate_start=True,
    core_placement="seeded",
    process_selection="round_robin",
)


# Which Ruleset identities execute on the Agent API v2 process runtime
# (``battle_engine.process_runtime.ProcessMatchController``). A finite, explicit set for the
# same reason ``_RULESET_POLICIES`` is a finite table -- and the one place
# ``match_service`` asks the question, so adding a future process Ruleset
# never means hunting down scattered ``== BYTEFRAY_RULESET_V4_ID``
# comparisons.
#
# V6 Phase 2B.10 Scope B removed ``bytefray-rules-4-alpha1``/``-alpha2``
# from this set alongside their executable registration: this table gates
# runtime *dispatch* (and, via ``match_service.py:1212``, replay schema
# selection) for a match about to execute, so it is execution-only,
# unlike the two core-status tables in ``python_runtime.py``.
PROCESS_RULESET_IDS: frozenset[str] = frozenset(
    {
        BYTEFRAY_RULESET_V4_ID,
    }
)


class UnknownRulesetError(LookupError):
    """A Ruleset ID has no known policy.

    Raised by :func:`resolve_ruleset_policy` for any ID not present in
    :data:`_RULESET_POLICIES`. Deliberately fails closed: an unrecognized
    Ruleset ID -- including a plausible-looking but unregistered future
    identity, or a retired one such as ``bytefray-rules-1``/``-2`` -- must
    never silently resolve to the current control.
    """

    def __init__(self, ruleset_id: str):
        super().__init__(f"Unknown Ruleset ID: {ruleset_id!r}")
        self.ruleset_id = ruleset_id


# A finite, explicit table -- not a naming-convention check -- for the same
# reason ``rules._RULESET_ALIASES`` is finite (see that module's docstring).
# This table is deliberately *not* the same table: it governs which Ruleset
# ID a runtime may currently *execute* under, which is a different question
# from which ID a persisted artifact may be *attributed* to. A historical
# artifact identity alias is not evidence that runtime dispatch should
# execute the aliased ID as today's Ruleset v1 -- see
# ``docs/archive/v1/V1_5_PHASE3_RULESET_POLICY_DISPATCH.md``'s "Resolver design".
#
# ``bytefray-rules-2`` is registered under its own explicit key, never
# aliased to or from ``bytefray-rules-1`` (``rules.py``'s
# ``_RULESET_ALIASES`` gets no entry for it -- see that table's own
# docstring).
#
# V6 Phase 2B.9 removed three closed-research entries this table used to
# carry -- ``bytefray-rules-2-alpha1``, ``bytefray-rules-2-alpha11``, and
# ``bytefray-rules-3-alpha1`` (docs/research/v6/V6_PHASE2B9_SCOPE_A_RULESET_RETIREMENT.md).
# V6 Phase 2B.10 Scope B removed two more -- ``bytefray-rules-4-alpha1`` and
# ``bytefray-rules-4-alpha2`` (docs/research/v6/V6_PHASE2B10_SCOPE_B_V4_ALPHA_RETIREMENT.md).
# V6 Phase 2B.12 Scope C removed the final two -- ``bytefray-rules-1`` and
# ``bytefray-rules-2`` -- retiring Agent API v1 and VM/blob execution
# entirely (docs/research/v6/V6_PHASE2B12_SCOPE_C_RUNTIME_RETIREMENT.md).
# None of these seven was ever selectable from any product surface after
# its own retirement phase; each ID constant is retained above for
# historical-artifact recognition, but ``resolve_ruleset_policy`` now
# raises ``UnknownRulesetError`` for all seven like any other unregistered
# ID. Do not re-add them here, and never map them to ``bytefray-rules-4``
# elsewhere in this module -- historical recognition and executable
# registration are deliberately separate concerns (see ``rules.py``'s
# alias-table docstring). ``bytefray-rules-4`` is now the sole executable
# entry.
_RULESET_POLICIES: Mapping[str, RulesetPolicy] = {
    RULESET_V4.ruleset_id: RULESET_V4,
}


def _canonical_runtime_kind(kind: str) -> str | None:
    if kind == "python":
        return "python"
    if kind in {"vm", "builtin", "blob"}:
        return "vm"
    return None


def _agent_runtime_metadata(agent: object) -> tuple[object, object]:
    """Read the two authoritative compatibility fields off one agent projection."""

    if isinstance(agent, Mapping):
        return agent.get("kind"), agent.get("api_version")
    return getattr(agent, "kind", None), getattr(agent, "api_version", None)


def agent_supported_by_ruleset(agent: object, ruleset_id: str) -> bool:
    """Return whether discovered agent metadata is valid for ``ruleset_id``.

    ``agent`` may be an :class:`~battle_engine.agents.AgentSpec`, a manifest
    mapping, or another metadata projection exposing ``kind`` and
    ``api_version`` attributes.  Ruleset identity and those authoritative
    fields are the complete decision input; agent IDs and display names are
    deliberately ignored.
    """

    kind, api_version = _agent_runtime_metadata(agent)
    if not isinstance(kind, str):
        return False
    if api_version is not None and (isinstance(api_version, bool) or not isinstance(api_version, int)):
        return False
    try:
        policy = resolve_ruleset_policy(ruleset_id)
    except UnknownRulesetError:
        return False
    return policy.supports_agent(kind=kind, api_version=api_version)


def _describe_agent(agent: object) -> str:
    """Name one agent the way ``RulesetAgentUnsupportedError`` already does."""

    kind, api_version = _agent_runtime_metadata(agent)
    if isinstance(agent, Mapping):
        name = agent.get("agent_id") or agent.get("name")
    else:
        name = getattr(agent, "agent_id", None) or getattr(agent, "name", None)
    detail = str(kind) if isinstance(kind, str) else "unknown runtime"
    if kind == "python":
        detail = f"{detail}, Agent API {api_version!r}"
    return f"{name} ({detail})" if name else f"({detail})"


class NoCompatibleRulesetError(ValueError):
    """No registered Ruleset supports an omitted-Ruleset request's whole roster.

    Raised by :func:`resolve_omitted_ruleset_for_agents` instead of guessing
    a Ruleset that a downstream
    :class:`~battle_engine.match_service.RulesetAgentUnsupportedError` would
    immediately reject. The incompatibility is already knowable from
    discovered metadata at resolution time -- for example an Agent API v1
    entrant paired with an Agent API v2 one, which no single Ruleset
    executes -- so resolution fails closed and says so, rather than
    selecting one entrant's Ruleset and letting the other entrant discover
    the mismatch later.

    Deliberately a ``ValueError`` carrying a ``code``/``diagnostic``, the
    same shape the CLI configuration-error handlers established in the
    Phase 1 remediation already present cleanly (``ERROR: <message>``,
    exit 2, no traceback).
    """

    code = "ruleset_resolution_failed"

    def __init__(self, agents: Iterable[object]) -> None:
        roster = tuple(agents)
        if not roster:
            # V6 Phase 2B.12 (trap F-2): an empty roster used to resolve
            # silently to the retired bytefray-rules-1. There is no
            # Ruleset-independent reason to prefer one identity over
            # another for zero entrants, and a retired identity is strictly
            # worse than an explicit failure, so this now fails closed too.
            message = (
                "No Bytefray Ruleset can be resolved for an empty entrant "
                "roster; select a compatible roster, or pass an explicit "
                "Ruleset to override automatic selection."
            )
        else:
            details = ", ".join(_describe_agent(agent) for agent in roster)
            message = (
                "No Bytefray Ruleset supports this match's entrants together: "
                f"{details}. Entrants must share one compatible runtime kind and "
                "Agent API version; select a compatible roster, or pass an "
                "explicit Ruleset to override automatic selection."
            )
        super().__init__(message)
        self.agents = roster
        self.message = message


# Which Rulesets an omitted selection may resolve to, in product-preference
# order. A finite, explicit tuple for the same reason ``_RULESET_POLICIES``
# is a finite table: automatic resolution must never wander into an
# experimental identity that a user did not ask for by name.
#
# V6 Phase 2B.12 (docs/research/v6/V6_PHASE2B12_SCOPE_C_RUNTIME_RETIREMENT.md)
# narrowed this from ``(rules-2, rules-4, rules-1)`` to its single remaining
# member: Agent API v1 and VM/blob execution are retired, so no roster can
# ever resolve to ``bytefray-rules-2`` or ``bytefray-rules-1`` here again --
# an Agent-API-v1 or VM/blob roster now fails closed with
# :class:`NoCompatibleRulesetError` instead (see
# :func:`resolve_omitted_ruleset_for_agents`). Kept as a tuple, not
# collapsed to a bare constant, so a future Ruleset (``bytefray-rules-6``)
# has one obvious place to be added -- see the V5-research constraint below,
# which still applies unchanged.
#
# V5 research constraint (pre-Phase-0 baseline remediation), preserved: an
# experimental Ruleset must require *explicit* selection: it must not be
# added to this tuple, and must never become what an existing Agent API v2
# roster receives when the Ruleset is omitted. Stable ``bytefray-rules-4``
# is the immutable scientific control the V5/V6 research programs measure
# against, so silently reassigning the omitted-selection slot to an
# experimental identity would contaminate every comparison made against it.
OMITTED_RULESET_CANDIDATES: tuple[str, ...] = (BYTEFRAY_RULESET_V4_ID,)


def resolve_omitted_ruleset_for_agents(
    requested_ruleset_id: str | None,
    agents: Iterable[object],
    *,
    candidates: Iterable[str] = OMITTED_RULESET_CANDIDATES,
) -> str:
    """Resolve one product entry point's optional Ruleset from agent metadata.

    The API-aware successor to :func:`resolve_omitted_ruleset_id`: instead of
    asking only "is every entrant Python?", this asks the authoritative
    compatibility question -- "does this candidate Ruleset support *every*
    selected entrant's runtime kind **and** Agent API version?" -- through
    the same :func:`agent_supported_by_ruleset` predicate
    ``NativeMatchService`` and Agent Designer use. That is what lets an
    Agent API v2 roster reach ``bytefray-rules-4`` (the permanent stable
    identity, as of ``v4.0.0-rc1`` Phase 2 -- earlier product history saw
    this same seam resolve to ``bytefray-rules-4-alpha1`` and then
    ``bytefray-rules-4-alpha2`` in turn, entirely by walking
    :data:`OMITTED_RULESET_CANDIDATES`, never by a change here) automatically.
    An Agent API v1 or VM/blob roster raises :class:`NoCompatibleRulesetError`
    (V6 Phase 2B.12 retired both from execution), with no internal Ruleset
    identity ever spelled out by hand.

    ``agents`` is the resolved entrant metadata for *this* request -- any
    projection :func:`agent_supported_by_ruleset` accepts (an ``AgentSpec``,
    a manifest mapping, a catalog row's metadata). An empty roster now fails
    closed with :class:`NoCompatibleRulesetError` too (V6 Phase 2B.12, trap
    F-2): there is nothing to derive a Ruleset from, and no Ruleset should
    be preferred over any other for zero entrants.

    An explicit ``requested_ruleset_id`` is always returned unchanged --
    this function never validates, corrects, or overrides a user's own
    selection, including one a downstream compatibility check will go on to
    reject. Only an omitted Ruleset is resolved here.

    Raises :class:`NoCompatibleRulesetError` when no candidate supports the
    whole roster, rather than guessing (see that class).
    """

    if requested_ruleset_id is not None:
        return requested_ruleset_id
    roster = tuple(agents)
    if not roster:
        raise NoCompatibleRulesetError(roster)
    for candidate in candidates:
        if all(agent_supported_by_ruleset(agent, candidate) for agent in roster):
            return candidate
    raise NoCompatibleRulesetError(roster)



def resolve_ruleset_policy(ruleset_id: str) -> RulesetPolicy:
    """Return the executable policy for ``ruleset_id``, or fail closed.

    Only the exact, explicitly registered identities in
    :data:`_RULESET_POLICIES` resolve. Historical aliases, prefix matches,
    and "latest Ruleset" fallbacks are all deliberately unsupported here --
    an unrecognized ``ruleset_id`` raises :class:`UnknownRulesetError`
    rather than executing as Ruleset v1 or any other registered identity.
    """

    try:
        return _RULESET_POLICIES[ruleset_id]
    except KeyError:
        raise UnknownRulesetError(ruleset_id) from None


# Which entrant runtime kinds :func:`resolve_omitted_ruleset_id` treats as
# "Python-only". A closed, explicit set -- not "everything except vm" --
# matching this module's own preference for finite tables over open-ended
# checks (see ``_RULESET_POLICIES``'s docstring).
_PYTHON_ONLY_KINDS: frozenset[str] = frozenset({"python"})


def resolve_omitted_ruleset_id(
    requested_ruleset_id: str | None, runtime_kinds: Iterable[str]
) -> str:
    """Resolve an optional ``--ruleset`` from entrant runtime kinds alone.

    Retained as a thin, kind-only compatibility surface for out-of-tree
    callers -- every in-tree product entry point calls the API-aware
    :func:`resolve_omitted_ruleset_for_agents` directly, since a runtime
    kind alone has not been enough information to resolve a Ruleset since
    Agent API v2 was introduced. This function delegates to that same
    resolver rather than repeating its candidate walk, so this surface can
    never drift from it.

    ``requested_ruleset_id`` is ``None`` for "the caller omitted --ruleset"
    and any other value for "the caller explicitly selected this Ruleset".
    An explicit selection is always returned unchanged -- this function
    never validates, corrects, or overrides one. Only an omitted Ruleset is
    ever resolved here.

    ``runtime_kinds`` is the resolved entrant ``kind`` set for this specific
    request. V6 Phase 2B.12 retired Agent API v1 and VM/blob execution
    (trap F-3, docs/research/v6/V6_PHASE2B12_SCOPE_C_RUNTIME_RETIREMENT.md):
    a bare runtime kind carries no Agent API version, so Python is now
    projected as Agent API v2 -- the only Agent API generation any Ruleset
    still executes -- rather than the historical v1 projection. An empty,
    VM-only, or mixed kind set now raises :class:`NoCompatibleRulesetError`
    instead of silently falling back to the retired ``bytefray-rules-1``:
    this function used to swallow that exception and return a retired
    identity for every such input, which was strictly worse than the clean
    failure ``NativeMatchService``/callers already handle everywhere else.
    """

    if requested_ruleset_id is not None:
        return requested_ruleset_id
    kinds = frozenset(runtime_kinds)
    projected = [
        {"kind": kind, "api_version": 2 if kind in _PYTHON_ONLY_KINDS else None}
        for kind in sorted(kinds)
    ]
    return resolve_omitted_ruleset_for_agents(None, projected)


__all__ = [
    "BYTEFRAY_RULESET_V2_ALPHA1_ID",
    "BYTEFRAY_RULESET_V2_ALPHA11_ID",
    "BYTEFRAY_RULESET_V2_ID",
    "BYTEFRAY_RULESET_V3_ALPHA1_ID",
    "BYTEFRAY_RULESET_V4_ALPHA1_ID",
    "BYTEFRAY_RULESET_V4_ALPHA2_ID",
    "BYTEFRAY_RULESET_V4_ID",
    "OMITTED_RULESET_CANDIDATES",
    "PROCESS_RULESET_IDS",
    "RULESET_V4",
    "NoCompatibleRulesetError",
    "RulesetPolicy",
    "TerminationDecision",
    "TerminationReason",
    "UnknownRulesetError",
    "agent_supported_by_ruleset",
    "resolve_omitted_ruleset_for_agents",
    "resolve_omitted_ruleset_id",
    "resolve_ruleset_policy",
]
