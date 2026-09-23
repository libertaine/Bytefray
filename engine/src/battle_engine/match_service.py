"""Application service for resolved native Bytefray matches.

The service owns homogeneous Python-agent routing, execution, and
partial-artifact cleanup. Agent discovery, CLI parsing, and external result
persistence remain outside this native boundary.

V6 Phase 2B.12 retired VM/blob execution and Agent API v1 execution
(docs/research/v6/V6_PHASE2B12_SCOPE_C_RUNTIME_RETIREMENT.md): this module
used to route a homogeneous match to one of three dispatch arms (VM,
unsupervised/supervised Agent API v1 Python, or the Agent API v2 process
controller); only the process-controller arm remains reachable now, since
``resolve_ruleset_policy`` accepts only ``bytefray-rules-4``.
"""

from __future__ import annotations

import hashlib
import os
import tempfile
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass, field, replace
from pathlib import Path
from types import MappingProxyType
from typing import Any, cast

from battle_engine.agent_trace import (
    TRACE_SCHEMA_VERSION_V2,
    TraceHeader,
    TraceWriter,
)
from battle_engine.config import Config
from battle_engine.entrant_identity import EntrantIdentity
from battle_engine.process_runtime import ProcessMatchController
from battle_engine.project_info import get_project_info
from battle_engine.python_runtime import (
    PythonEntrantInitializationError,
    RuntimeDiagnostic,
    TerminationReason,
    core_addresses,
    derive_agent_seed,
)
from battle_engine.replay import (
    MatchResult as ReplayMatchResult,
)
from battle_engine.replay import (
    ReplayHeader,
    RuntimeKind,
    iter_replay,
    write_replay,
)
from battle_engine.result_model import SCHEMA_VERSION as RESULT_SCHEMA_VERSION
from battle_engine.result_model import (
    ReplayReference,
    ResultEnvelope,
    generate_occurrence_id,
    stable_id,
    utc_completed_at,
    write_json_atomic,
)
from battle_engine.results import WINNER_TIE_SENTINEL
from battle_engine.ruleset_policy import (
    BYTEFRAY_RULESET_V4_ID,
    BYTEFRAY_RULESET_V6_RESEARCH_CAPTURE_HOLD_K2_DISRUPTION_SLOT1_ID,
    BYTEFRAY_RULESET_V6_RESEARCH_CAPTURE_HOLD_K2_ID,
    BYTEFRAY_RULESET_V6_RESEARCH_DISRUPTION_SLOT1_ID,
    BYTEFRAY_RULESET_V6_RESEARCH_SCALE_ID,
    BYTEFRAY_RULESET_V6_RESEARCH_SCALE_MOVE_ID,
    BYTEFRAY_RULESET_V6_RESEARCH_SCALE_MOVE_PROPORTIONAL_ID,
    RulesetPolicy,
    resolve_ruleset_policy,
)
from battle_engine.telemetry import JSONLSink


@dataclass(frozen=True, init=False)
class MatchEntrant:
    """Explicitly typed resolved entrant for one native execution path.

    Composes the entrant's :class:`~battle_engine.entrant_identity.
    EntrantIdentity` (who) with this match's resolved participation data --
    ``start``/``kind``/``python_spec`` (how this entrant
    participates in *this* match) -- rather than storing ``agent_id``/
    ``name`` as independent fields. See
    ``docs/archive/v1/V1_5_PHASE5_ENTRANT_IDENTITY_EXECUTION_STATE.md``. ``agent_id``/
    ``name`` remain read-only compatibility properties so the many call
    sites across the engine, CLI, tournament service, and tests that
    construct or read them are unaffected.
    """

    identity: EntrantIdentity
    start: int
    kind: str = "python"
    python_spec: Any | None = None
    #: This entrant's fully resolved agent parameters (V5 Alpha 1 Phase D),
    #: already validated by ``agent_parameters.resolve_parameters`` before a
    #: request is built. Empty for every entrant that declares no parameter
    #: schema and is given no overrides -- which is every entrant that
    #: existed before Phase D, and why every historical ``match_id`` is
    #: unaffected (see ``canonical_match_id``).
    #:
    #: Carried on the request rather than resolved inside the runtime so
    #: that an invalid parameter fails before any agent code is imported or
    #: executed.
    #:
    #: ``field(default_factory=...)`` rather than a bare ``= MappingProxyType({})``
    #: class attribute (Phase F3): this class sets ``init=False`` and never
    #: lets the dataclass-generated ``__init__`` read this default (the
    #: hand-written ``__init__`` below always calls ``object.__setattr__``
    #: itself), but ``dataclasses`` still inspects every field's default
    #: while building the class, regardless of ``init``. Python 3.11
    #: generalized that check from "is this a list/dict/set" to "is this
    #: unhashable", and a ``mappingproxy`` is unhashable, so a bare mutable
    #: default here raised ``ValueError: mutable default ... for field
    #: parameters is not allowed`` on import under Python 3.11 -- before any
    #: match ever ran. ``NativeAgentResult.metadata`` and
    #: ``agent_api.MatchContextV2.parameters`` already use this same
    #: ``default_factory`` form for an identical empty-mapping default.
    parameters: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))

    def __init__(
        self,
        agent_id: str,
        name: str,
        start: int,
        kind: str = "python",
        python_spec: Any | None = None,
        parameters: Mapping[str, Any] | None = None,
    ) -> None:
        object.__setattr__(self, "identity", EntrantIdentity(agent_id=agent_id, name=name))
        object.__setattr__(self, "start", start)
        object.__setattr__(self, "kind", kind)
        object.__setattr__(self, "python_spec", python_spec)
        object.__setattr__(
            self, "parameters", MappingProxyType(dict(parameters or {}))
        )

    @property
    def agent_id(self) -> str:
        return self.identity.agent_id

    @property
    def name(self) -> str:
        return self.identity.name

    @classmethod
    def python(
        cls,
        agent_id: str,
        name: str,
        start: int,
        spec: Any,
        parameters: Mapping[str, Any] | None = None,
    ) -> MatchEntrant:
        return cls(agent_id, name, start, "python", spec, parameters)


@dataclass(frozen=True)
class MatchRequest:
    """Complete input required to execute one homogeneous native match.

    ``trace_path`` and ``agent_call_timeout`` are Agent Lab's two
    independently optional development-time additions
    (``docs/specs/agent_lab.md`` §4). Both default to ``None`` -- the
    "normal match path" (``bytefray run``/tournament) never sets either
    unless a caller opts in, so an ordinary invocation runs through the
    current :class:`~battle_engine.process_runtime.ProcessMatchController`
    path without per-call timeout supervision.
    ``bytefray run --trace PATH`` is the one normal-path caller that sets
    ``trace_path`` explicitly (Alpha3 follow-up Phase 1); omitting
    ``--trace`` leaves it ``None`` exactly as before.

    ``ruleset_id`` remains an explicit selector and provenance input.
    ``None`` now resolves to the sole executable identity,
    ``BYTEFRAY_RULESET_V4_ID``. The resolved identity is threaded into the
    canonical match/result identity and replay/result metadata.
    """

    config: Config
    entrants: tuple[MatchEntrant, ...]
    max_ticks: int
    replay_path: Path
    verbose: bool = True
    trace_path: Path | None = None
    agent_call_timeout: float | None = None
    ruleset_id: str | None = None
    # v3 research Phase 2's experimental bounded-locality reach. Always
    # ignored: V6 Phase 2B.9 retired every Ruleset identity that supported
    # bounded-locality addressing (docs/research/v6/
    # V6_PHASE2B9_SCOPE_A_RULESET_RETIREMENT.md), so no ``ruleset_id`` this
    # field could accompany ever resolves to one. Kept, rather than removed,
    # so existing callers need no change and a future locality-capable
    # Ruleset has one obvious field to reconnect (see
    # ``_resolve_locality_reach``, which always returns ``None`` now).
    locality_reach: int | None = None
    scheduler_chunk_size: int | None = None
    scheduler_rotate_start: bool | None = None



@dataclass(frozen=True)
class NativeAgentResult:
    """Persistence-neutral final state and statistics for one entrant."""

    agent_id: str
    name: str
    alive: bool
    score: int | float
    alive_ticks: int
    kills: int
    deaths: int
    cpu_total: int
    mem_writes: int
    territory_last: int
    territory_max: int
    territory_avg: float
    territory_pct_last: float
    territory_pct_max: float
    territory_pct_avg: float
    diagnostic: RuntimeDiagnostic | None = None
    termination_reason: str | None = None
    metadata: Mapping[str, Any] = field(
        default_factory=lambda: MappingProxyType({})
    )

    def as_legacy_statistics(self) -> dict[str, object]:
        """Return the v0.2 CLI agent-statistics shape during migration."""

        return {
            "name": self.name,
            "alive": self.alive,
            "score": self.score,
            "alive_ticks": self.alive_ticks,
            "kills": self.kills,
            "deaths": self.deaths,
            "cpu_total": self.cpu_total,
            "mem_writes": self.mem_writes,
            "territory_last": self.territory_last,
            "territory_max": self.territory_max,
            "territory_avg": self.territory_avg,
            "territory_pct_last": self.territory_pct_last,
            "territory_pct_max": self.territory_pct_max,
            "territory_pct_avg": self.territory_pct_avg,
        }


@dataclass(frozen=True)
class NativeMatchResult:
    """Canonical internal result of one Agent API v2 process match."""

    winner: str
    ticks_run: int
    score: Mapping[str, int | float]
    agents: tuple[NativeAgentResult, ...]
    replay_path: Path
    termination_reason: TerminationReason
    result_id: str = ""
    match_id: str = ""
    replay_sha256: str = ""
    result_path: Path | None = None

    @property
    def agents_by_id(self) -> Mapping[str, NativeAgentResult]:
        return MappingProxyType({agent.agent_id: agent for agent in self.agents})


class UnsupportedMatchCompositionError(ValueError):
    """Native matches must be homogeneous until mixed scheduling is defined."""

    # Preserve the Phase 3a exception attribute for callers while using the
    # normalized Phase 3b diagnostic code internally.
    code = "native_match_composition_unsupported"

    def __init__(self, message: str):
        super().__init__(message)
        self.diagnostic = RuntimeDiagnostic(
            code="unsupported_match_composition",
            stage="configuration",
            message=message,
        )


class PythonMatchExecutionError(RuntimeError):
    """A Python match failed outside an entrant's controlled forfeit path."""

    def __init__(self, diagnostic: RuntimeDiagnostic):
        super().__init__(diagnostic.message)
        self.diagnostic = diagnostic


class RulesetRuntimeUnsupportedError(ValueError):
    """A match's entrant runtime kind(s) are not supported by its requested Ruleset.

    Distinct from :class:`UnsupportedMatchCompositionError`: that error
    rejects non-uniform entrant composition regardless of which Ruleset was
    requested, and is checked first. This error rejects an otherwise-
    homogeneous composition whose single runtime kind the *requested
    Ruleset* itself does not support. V6 Phase 2B.12 retired VM/blob
    execution entirely, so ``bytefray-rules-4`` -- the sole remaining
    Ruleset -- is the only ``ruleset_id`` this can ever be raised for now,
    and only for a non-Python entrant kind, which no Ruleset executes any
    longer. Raised by ``NativeMatchService.run`` before any entrant
    executes and before any replay/result artifact is written.
    """

    code = "ruleset_runtime_unsupported"

    def __init__(self, ruleset_id: str, unsupported_kinds: Iterable[str]):
        kinds = ", ".join(sorted(unsupported_kinds))
        message = (
            f"Ruleset {ruleset_id!r} does not support runtime kind(s): {kinds}. "
            "Only Agent API v2 (process) Python agents are executable."
        )
        super().__init__(message)
        self.ruleset_id = ruleset_id
        self.unsupported_kinds = tuple(sorted(unsupported_kinds))
        self.diagnostic = RuntimeDiagnostic(
            code=self.code,
            stage="configuration",
            message=message,
        )


class RulesetAgentUnsupportedError(ValueError):
    """An entrant's runtime/API metadata is incompatible with its Ruleset."""

    code = "ruleset_agent_unsupported"

    def __init__(
        self,
        ruleset_id: str,
        unsupported_agents: Iterable[tuple[str, str, int | None]],
    ) -> None:
        agents = tuple(unsupported_agents)
        details = ", ".join(
            f"{agent_id} ({kind}, Agent API {api_version!r})"
            for agent_id, kind, api_version in agents
        )
        message = (
            f"Ruleset {ruleset_id!r} does not support entrant metadata: {details}."
        )
        super().__init__(message)
        self.ruleset_id = ruleset_id
        self.unsupported_agents = agents
        self.diagnostic = RuntimeDiagnostic(
            code=self.code,
            stage="configuration",
            message=message,
        )


class OverlappingCoreError(ValueError):
    """Two or more entrants' guarded-Ruleset cores overlap.

    RC2's engine-side fail-closed guard for v2.0.0-rc1's release-blocking
    defect, originally written for the then-permanent ``bytefray-rules-2``
    identity and now protecting ``bytefray-rules-4`` (see
    :data:`_CORE_PLACEMENT_GUARDED_RULESET_IDS`): every entrant's
    ``CORE_SIZE``-wide core window (``python_runtime.core_addresses``, using
    ordinary modular arena wraparound) must be disjoint from every other
    entrant's. Raised by ``NativeMatchService.run`` before any entrant
    executes and before any replay/result artifact is written, so this is
    the one authoritative gate every caller -- CLI, Designer, tests, and any
    future programmatic ``MatchRequest`` construction -- passes through,
    regardless of whether the overlapping starts arrived explicitly or via
    placement defaults.
    """

    code = "ruleset_v2_overlapping_cores"

    def __init__(self, ruleset_id: str, overlapping_pairs: Iterable[tuple[str, str]]):
        pairs = tuple(overlapping_pairs)
        described = ", ".join(f"{a} and {b}" for a, b in pairs)
        message = (
            f"Ruleset {ruleset_id!r} requires non-overlapping entrant cores; "
            f"entrants {described} overlap at their configured starts."
        )
        super().__init__(message)
        self.ruleset_id = ruleset_id
        self.overlapping_pairs = pairs
        self.diagnostic = RuntimeDiagnostic(
            code=self.code,
            stage="configuration",
            message=message,
        )


# Which Ruleset identities reject overlapping entrant cores before
# execution. ``bytefray-rules-2`` was the permanent product identity the
# RC2 guard was originally written for. The historical vulnerable-core
# alpha identities were deliberately excluded even while still executable:
# their frozen execution semantics were never touched by this guard.
#
# V6 Phase 2B.9 removed ``bytefray-rules-3-alpha1`` from this set: it was
# added because the locality mechanic inherited this identical
# vulnerable-core mechanic, but locality's only executable identity was
# retired from execution, so the membership was dead.
#
# V6 Phase 2B.10 Scope B removed ``bytefray-rules-4-alpha1``/``-alpha2``
# from this set for the identical reason: this table gates a pre-execution
# guard on entrant placement for a match *about to run* -- it is never
# consulted by any historical reader (unlike ``VULNERABLE_CORE_RULESET_IDS``/
# ``OBSERVABLE_CORE_RULESET_IDS`` in ``python_runtime.py``, whose membership
# for both alphas is retained because replay/result readers do consult
# them) -- so retiring both alphas' executable registration made their
# membership here dead.
#
# V6 Phase 2B.12 Scope C removed ``bytefray-rules-2`` itself alongside its
# executable registration (docs/research/v6/
# V6_PHASE2B12_SCOPE_C_RUNTIME_RETIREMENT.md): the guard it was written for
# can no longer execute at all. ``bytefray-rules-4`` keeps the guard: it
# shares alpha2's exact seeded-placement gameplay, and a behavioral
# divergence here (silently allowing overlapping cores under the stable
# identity) would be exactly the kind of gameplay difference the promotion
# must not introduce.
_CORE_PLACEMENT_GUARDED_RULESET_IDS: frozenset[str] = frozenset(
    {
        BYTEFRAY_RULESET_V4_ID,
        # V6 Phase 4B: the variable-arena research Ruleset shares
        # `core_placement="seeded"` and the same vulnerable-core semantics
        # as stable v4 (it executes on the identical Agent API v2 process
        # runtime), so an overlapping-core request must fail closed for it
        # exactly as it does for stable v4, never silently seed core
        # ownership in entrant order at an unusual arena size.
        BYTEFRAY_RULESET_V6_RESEARCH_SCALE_ID,
        # V6 Phase 4C: movement-normalized research Ruleset also shares
        # seeded placement and vulnerable-core semantics.
        BYTEFRAY_RULESET_V6_RESEARCH_SCALE_MOVE_ID,
        # V6 Phase 4D: proportional-movement research Ruleset also shares
        # seeded placement and vulnerable-core semantics.
        BYTEFRAY_RULESET_V6_RESEARCH_SCALE_MOVE_PROPORTIONAL_ID,
        # V6 E2: the capture-hold research Ruleset shares seeded placement
        # with its research-scale control, and core capture is exactly what
        # it varies -- overlapping cores must fail closed here too, never
        # seed core ownership in entrant order.
        BYTEFRAY_RULESET_V6_RESEARCH_CAPTURE_HOLD_K2_ID,
        # V6 E3: both slot-limited disruption research Rulesets share seeded
        # placement and vulnerable-core semantics with their parents.
        BYTEFRAY_RULESET_V6_RESEARCH_CAPTURE_HOLD_K2_DISRUPTION_SLOT1_ID,
        BYTEFRAY_RULESET_V6_RESEARCH_DISRUPTION_SLOT1_ID,
    }
)



def _validate_v2_core_placement(
    ruleset_policy: RulesetPolicy,
    entrants: tuple[MatchEntrant, ...],
    arena_size: int,
) -> None:
    """Fail closed before execution if a guarded Ruleset's cores overlap.

    Scoped to exactly :data:`_CORE_PLACEMENT_GUARDED_RULESET_IDS` -- today
    only ``bytefray-rules-4`` -- the RC2 guard this function implements
    (see :class:`OverlappingCoreError`). Every other Ruleset identity is
    unaffected: this function returns immediately for them, exactly as it
    did not exist before this fix.
    """

    if ruleset_policy.ruleset_id not in _CORE_PLACEMENT_GUARDED_RULESET_IDS:
        return

    windows = [
        (entrant.agent_id, frozenset(core_addresses(entrant.start, arena_size)))
        for entrant in entrants
    ]
    overlapping_pairs = [
        (agent_a, agent_b)
        for index, (agent_a, cells_a) in enumerate(windows)
        for agent_b, cells_b in windows[index + 1 :]
        if cells_a & cells_b
    ]
    if overlapping_pairs:
        raise OverlappingCoreError(ruleset_policy.ruleset_id, overlapping_pairs)


def _resolve_locality_reach(request: MatchRequest) -> int | None:
    """The bounded reach ``request`` actually executes/executed under.

    Always ``None``: V6 Phase 2B.9 retired every Ruleset identity that
    supported bounded-locality addressing. Kept as a stable named seam
    (mirroring :func:`_resolve_ruleset_id`'s discipline) rather than
    inlining ``None`` at each call site, so a future locality-capable
    Ruleset has one obvious place to restore this resolution.
    """

    return None


def _reproducibility(request: MatchRequest) -> dict[str, Any]:
    """The per-match configuration block both identity and artifacts use.

    One source for :func:`canonical_match_id` and
    :func:`_finalize_native_artifacts`, which previously repeated the
    identical literal -- the same discipline :func:`_resolve_ruleset_id`
    already applies to the Ruleset identity, so the hashed and the persisted
    configuration can never drift apart.

    ``locality_reach`` appears only for a locality Ruleset. Omitted (not
    written as null) otherwise, so every Ruleset-v1/v2 ``match_id``,
    ``result_id``, ``replay_id``, and persisted ``reproducibility`` block is
    byte-identical to one computed before Phase 2 -- the same gating
    discipline the Python ``start`` key already uses in
    :func:`canonical_match_id`.
    """

    payload: dict[str, Any] = {
        "seed": request.config.seed,
        "arena_size": request.config.arena_size,
        "tick_limit": request.max_ticks,
        "action_budget": request.config.instr_per_tick,
        "win_mode": request.config.win_mode,
        "weights": asdict(request.config.weights),
        "entrant_order": [entrant.agent_id for entrant in request.entrants],
    }
    resolved_reach = _resolve_locality_reach(request)
    if resolved_reach is not None:
        payload["locality_reach"] = resolved_reach
    return payload


def _resolve_ruleset_id(request: MatchRequest) -> str:
    """Return the Ruleset identity ``request`` actually executes/executed under.

    The one place this resolution is computed -- ``NativeMatchService.run``
    (dispatch), ``canonical_match_id`` (identity hashing), and
    ``_finalize_native_artifacts`` (persisted ``ruleset_id`` fields) all
    call this instead of each independently repeating ``request.ruleset_id
    or BYTEFRAY_RULESET_V4_ID``, so the dispatched, hashed, and persisted
    identity can never drift apart for the same request.

    V6 Phase 2B.12 re-pointed the omitted-``ruleset_id`` default from the
    retired ``BYTEFRAY_RULESET_ID`` (bytefray-rules-1) to the retained
    control ``BYTEFRAY_RULESET_V4_ID`` (trap F-1,
    docs/research/v6/V6_PHASE2B12_SCOPE_C_RUNTIME_RETIREMENT.md). This
    deliberately changes ``match_id``/``result_id``/``replay_id`` for every
    caller that constructs a ``MatchRequest`` without an explicit
    ``ruleset_id`` -- an intended, recorded consequence, not an oversight;
    see the completion report's identity-derivation section.
    """

    return request.ruleset_id or BYTEFRAY_RULESET_V4_ID


def _effective_ruleset_policy(request: MatchRequest) -> RulesetPolicy:
    """Return the :class:`RulesetPolicy` ``request`` actually executes under.

    The one place a request's scheduler research override
    (``scheduler_chunk_size``/``scheduler_rotate_start``) is folded onto the
    resolved base policy -- both :meth:`NativeMatchService.run` (dispatch)
    and :func:`canonical_match_id` (identity hashing) call this instead of
    each independently repeating the override ``replace()``, so the policy
    that actually schedules entrants and the policy whose semantics are
    hashed into ``match_id`` can never drift apart for the same request.

    Gated on the override fields' non-default values, exactly like
    ``canonical_match_id``'s own ``locality_reach``/``start``/``parameters``
    gates: an ordinary request (the override omitted, as every caller before
    this override existed and every caller since that does not opt in still
    does) resolves the identical, untouched base policy it always has, so no
    historical ``match_id`` changes.
    """

    policy = resolve_ruleset_policy(_resolve_ruleset_id(request))
    kwargs: dict[str, Any] = {}
    if request.scheduler_chunk_size is not None:
        kwargs["scheduler_chunk_size"] = request.scheduler_chunk_size
    if request.scheduler_rotate_start is not None:
        kwargs["scheduler_rotate_start"] = request.scheduler_rotate_start
    if kwargs:
        policy = replace(policy, **kwargs)
    return policy


def _effective_winner(raw_winner: str) -> str:
    """Map ``resolve_winner``'s "no winner" empty string to a display value.

    ``raw_winner`` is always already ``results.resolve_winner``'s own output
    (see ``ProcessMatchController.run``), which already applies every
    win-mode-specific rule -- there is nothing left for this function to
    recompute. It exists only to give ``NativeMatchResult`` and
    ``result.json`` a stable, non-empty display value for "no single winner",
    since both currently type ``winner`` as a required string rather than
    ``str | None`` (see ``_finalize_native_artifacts`` for the canonical
    replay's terminal record, which uses ``None`` instead).
    """

    return raw_winner or WINNER_TIE_SENTINEL


def _build_process_result(
    controller: ProcessMatchController,
    summary: Mapping[str, Any],
    config: Config,
    replay_path: Path,
    entrant_parameters: Mapping[str, Mapping[str, Any]] | None = None,
) -> NativeMatchResult:
    """Convert the canonical v4 controller state into the native result model."""

    arena_size = config.arena_size
    parameters_by_agent = entrant_parameters or {}
    specs = {spec.agent_id: spec for spec in controller.entrant_specs}
    results: list[NativeAgentResult] = []
    for state in controller.states:
        resolved_parameters = parameters_by_agent.get(state.agent_id) or {}
        statistics = controller.statistics[state.agent_id]
        territory_sum = int(statistics.get("territory_sum", 0) or 0)
        territory_last = int(statistics.get("territory_last", 0) or 0)
        territory_max = int(statistics.get("territory_max", 0) or 0)
        territory_avg = territory_sum / max(1, int(summary["ticks_run"]))
        spec = specs[state.agent_id]
        results.append(
            NativeAgentResult(
                agent_id=state.agent_id,
                name=spec.name,
                alive=state.alive,
                score=controller.score.get(state.agent_id, 0),
                alive_ticks=int(statistics.get("alive_ticks", 0) or 0),
                kills=int(statistics.get("kills", 0) or 0),
                deaths=0 if state.alive else 1,
                cpu_total=int(statistics.get("total_cpu", 0) or 0),
                mem_writes=int(statistics.get("total_mem_writes", 0) or 0),
                territory_last=territory_last,
                territory_max=territory_max,
                territory_avg=territory_avg,
                territory_pct_last=(
                    territory_last * 100.0 / arena_size if arena_size else 0.0
                ),
                territory_pct_max=(
                    territory_max * 100.0 / arena_size if arena_size else 0.0
                ),
                territory_pct_avg=(
                    territory_avg * 100.0 / arena_size if arena_size else 0.0
                ),
                diagnostic=state.diagnostic,
                termination_reason=state.entrant_termination,
                metadata=MappingProxyType(
                    {
                        "kind": "python",
                        "slot": state.slot,
                        "derived_seed": spec.derived_seed,
                        "source_sha256": spec.source_digest,
                        "api_version": spec.api_version,
                        "agent_version": spec.agent_version,
                        "entry_point": spec.entry_point,
                        "local_source_fingerprint": spec.local_source_fingerprint,
                        "local_source_fingerprint_final": (
                            spec.local_source_fingerprint_final
                        ),
                        "processes": [
                            {
                                "process_id": process.process_id,
                                "reach": process.reach,
                                "share": float(process.quota_share),
                            }
                            for process in spec.processes
                        ],
                        # V5 Alpha 1 Phase D: the concrete resolved parameter
                        # values this entrant actually ran with -- what a
                        # reader needs to reproduce the match. The authoring
                        # *schema* (types, bounds, descriptions, presets)
                        # stays with the agent package and is deliberately
                        # never copied into an artifact.
                        #
                        # Purely additive to this already free-form metadata
                        # dict, on the same seam `entry_point`, the two
                        # fingerprints and `processes` use, and omitted
                        # entirely when empty -- so no pre-Phase-D
                        # `result.json`, and therefore no `result_id`,
                        # changes, and the replay schema needs no bump.
                        **(
                            {"parameters": dict(resolved_parameters)}
                            if resolved_parameters
                            else {}
                        ),
                    }
                ),
            )
        )
    return NativeMatchResult(
        winner=str(summary["winner"]),
        ticks_run=int(summary["ticks_run"]),
        score=MappingProxyType(dict(controller.score)),
        agents=tuple(results),
        replay_path=replay_path,
        termination_reason=TerminationReason(str(summary["reason"])),
    )


def _remove_python_artifacts(replay_path: Path, summary_path: Path) -> None:
    """Remove outputs that could otherwise be mistaken for this match's success."""

    for path in (replay_path, summary_path, replay_path.with_name("result.json")):
        try:
            path.unlink(missing_ok=True)
        except OSError as exc:
            raise PythonMatchExecutionError(
                RuntimeDiagnostic(
                    code="artifact_write_failed",
                    stage="artifact",
                    message=f"Could not clear Python match artifact {path.name}: {exc}",
                    exception_type=type(exc).__name__,
                )
            ) from exc


def _open_trace_writer(request: MatchRequest, *, schema_version: int) -> TraceWriter | None:
    if request.trace_path is None:
        return None
    writer = TraceWriter(request.trace_path)
    writer.write_header(
        TraceHeader(
            match_seed=request.config.seed,
            agents={entrant.agent_id: entrant.name for entrant in request.entrants},
            supervised=request.agent_call_timeout is not None,
            agent_call_timeout=request.agent_call_timeout,
            schema_version=schema_version,
        )
    )
    return writer





def _run_v4_process_match(
    request: MatchRequest,
    replay_path: Path,
    summary_path: Path,
    trace_writer: TraceWriter | None,
    ruleset_policy: RulesetPolicy,
) -> NativeMatchResult:
    """Execute Ruleset v4 through the canonical spatial-process controller."""
    controller: ProcessMatchController | None = None
    temporary_path: Path | None = None
    sink: JSONLSink | None = None
    try:
        controller = ProcessMatchController.from_python_entrants(
            request.config,
            request.entrants,
            request.max_ticks,
            ruleset_policy=ruleset_policy,
            agent_call_timeout=request.agent_call_timeout,
            trace_writer=trace_writer,
        )
        replay_path.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{replay_path.name}.", suffix=".tmp", dir=replay_path.parent
        )
        os.close(descriptor)
        temporary_path = Path(temporary_name)
        sink = JSONLSink(str(temporary_path))
        try:
            summary = controller.run(sink, verbose=request.verbose)
        finally:
            sink.close()
            sink = None
        recorded_path = temporary_path
        temporary_path = None
        
        return _build_process_result(
            controller,
            summary,
            request.config,
            recorded_path,
            entrant_parameters={
                entrant.agent_id: entrant.parameters
                for entrant in request.entrants
                if entrant.parameters
            },
        )
    except PythonEntrantInitializationError:
        _remove_python_artifacts(replay_path, summary_path)
        raise
    except OSError as exc:
        raise PythonMatchExecutionError(
            RuntimeDiagnostic(
                code="artifact_write_failed",
                stage="artifact",
                message=f"V4 replay could not be written: {type(exc).__name__}: {exc}",
                exception_type=type(exc).__name__,
            )
        ) from exc
    except PythonMatchExecutionError:
        raise
    except Exception as exc:
        raise PythonMatchExecutionError(
            RuntimeDiagnostic(
                code="engine_failed",
                stage="execution",
                message=f"V4 match engine failed: {type(exc).__name__}: {exc}",
                exception_type=type(exc).__name__,
            )
        ) from exc
    finally:
        if sink is not None:
            try:
                sink.close()
            except OSError:
                pass
        if controller is not None:
            controller.close()
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def _identity_safe_diagnostic(diagnostic: Any) -> dict[str, Any] | None:
    """Strip human-readable exception text before it enters an identity hash.

    ``message`` is built from ``str(exception)`` (see
    ``python_runtime._safe_message``) and can embed nondeterministic content
    -- a default object ``repr`` carries an ``id()``-based memory address,
    for instance. Two runs of the literal same match (same seed, same
    code) that both hit the same failure could then get different
    ``result_id``s, defeating dedup/index use cases for exactly the matches
    most worth comparing. The full message is unaffected everywhere else:
    it remains in ``result.json``'s and the replay's human-readable
    ``entrants``, only the ``result_id`` hash input excludes it.
    """

    if diagnostic is None:
        return None
    return {key: value for key, value in diagnostic.items() if key != "message"}


def canonical_match_id(
    request: MatchRequest,
    *,
    frozen_source_digests: Mapping[str, str] | None = None,
) -> str:
    """Derive canonical match identity entirely from request inputs.

    Includes ``BYTEFRAY_RULESET_ID`` as a first-class identity axis, sibling
    to ``reproducibility``/``entrants`` (v0.10 Phase 4) -- never folded into
    ``reproducibility``, which is specifically about per-match
    *configuration*, not gameplay identity (see docs/RULES.md's
    "Configuration values are not Ruleset identity"). Two otherwise-identical
    execution inputs must never collide under one ``match_id`` if they ran
    under different declared gameplay semantics.

    This is a deliberate, one-time native-ID transition: because exactly one
    Ruleset has ever existed, adding it to this payload changes the
    `match_id`/`result_id`/`replay_id` a v0.10+ build computes for the same
    logical inputs relative to a pre-v0.10 build -- see
    docs/RESULT_SCHEMA.md's "Identity recipe" and docs/COMPATIBILITY.md for
    the full rationale and the resume-compatibility consequence.

    ``frozen_source_digests`` (V6 research-integrity hardening): an optional
    ``agent_id -> source SHA-256`` snapshot a caller already froze *before*
    execution began (see ``process_runtime.ProcessMatchController.
    from_python_entrants``, which hashes each entrant's loaded source once,
    before ticking starts). When an entrant's ``agent_id`` is present here,
    its digest is used verbatim instead of this function re-reading
    ``spec.source_path`` from disk. Omitted (the default) for every
    pre-execution caller -- request planning, resume verification,
    tournament scheduling -- which have no execution to freeze against and
    must keep reading each entrant's *current* on-disk source exactly as
    before. Supplying it for an *already-executed* match closes a TOCTOU
    window: without it, a source file edited between execution start and
    this call could make the persisted ``match_id`` describe different code
    than what actually ran, even though ``result.json``'s own per-agent
    ``source_sha256`` (also frozen at load time) correctly describes it.
    """

    entrant_identities = []
    for slot, entrant in enumerate(request.entrants):
        spec = entrant.python_spec
        source = getattr(spec, "source_path", None)
        api_version = getattr(spec, "api_version", None) or 2
        frozen_digest = (
            frozen_source_digests.get(entrant.agent_id)
            if frozen_source_digests is not None
            else None
        )
        source_sha256 = (
            frozen_digest
            if frozen_digest is not None
            else (
                hashlib.sha256(source.read_bytes()).hexdigest()
                if isinstance(source, Path) and source.is_file()
                else ""
            )
        )
        metadata = {
            "kind": "python",
            "slot": slot,
            "derived_seed": derive_agent_seed(
                request.config.seed, slot, entrant.agent_id, api_version
            ),
            "source_sha256": source_sha256,
            "api_version": api_version,
            "agent_version": getattr(spec, "version", None),
        }
        # A Python entrant's start address is a gameplay-relevant identity
        # input. It is gated on non-default to preserve historical start=0
        # identities; see docs/COMPATIBILITY.md's placement note.
        if entrant.start != 0:
            metadata["start"] = entrant.start
        # Resolved parameters are gameplay-relevant identity input. The key
        # is gated on non-empty for compatibility and sorted for stability.
        if entrant.parameters:
            metadata["parameters"] = {
                key: entrant.parameters[key] for key in sorted(entrant.parameters)
            }
        entrant_identities.append(
            {"agent_id": entrant.agent_id, "name": entrant.name, "metadata": metadata}
        )
    reproducibility = _reproducibility(request)
    payload: dict[str, Any] = {
        "mode": "b2",
        "ruleset_id": _resolve_ruleset_id(request),
        "reproducibility": reproducibility,
        "entrants": entrant_identities,
    }
    # Gameplay scheduler semantics (V6 research-integrity hardening): gated
    # on the same non-default condition ``_effective_ruleset_policy`` uses,
    # so an ordinary request -- the override omitted, as every match ever
    # run before this override existed and every one since that does not
    # opt in still is -- gets a byte-identical payload and therefore an
    # unchanged historical ``match_id``. A request that *does* override
    # scheduler semantics folds the resolved effective policy's scheduling
    # fields in directly, so two otherwise-identical requests that actually
    # schedule entrants differently can never collide on ``match_id``.
    if request.scheduler_chunk_size is not None or request.scheduler_rotate_start is not None:
        effective_policy = _effective_ruleset_policy(request)
        payload["scheduler"] = {
            "mode": effective_policy.scheduler_mode,
            "chunk_size": effective_policy.scheduler_chunk_size,
            "rotate_start": effective_policy.scheduler_rotate_start,
        }
    return stable_id("match", payload)


def _finalize_native_artifacts(
    request: MatchRequest,
    result: NativeMatchResult,
    *,
    final_replay_path: Path | None = None,
) -> NativeMatchResult:
    # ``result`` exists only after execution has reached a final outcome.
    # Capture occurrence metadata once at that boundary, before replay/result
    # serialization begins, so it describes this execution rather than either
    # file write. Re-serializing the envelope below cannot regenerate it.
    occurrence_id = generate_occurrence_id()
    completed_at = utc_completed_at()
    product_version = get_project_info().version
    source_replay_path = result.replay_path
    publish_path = final_replay_path or source_replay_path
    reproducibility = _reproducibility(request)
    entrants = [
        {
            "agent_id": agent.agent_id,
            "name": agent.name,
            "alive": agent.alive,
            "score": agent.score,
            "termination_reason": agent.termination_reason,
            "diagnostic": (
                None if agent.diagnostic is None else asdict(agent.diagnostic)
            ),
            "statistics": agent.as_legacy_statistics(),
            "metadata": dict(agent.metadata),
        }
        for agent in result.agents
    ]
    # V6 research-integrity hardening: each entrant's source digest was
    # already frozen before this match ticked once (``ProcessEntrantSpec.
    # source_digest`` inside ``from_python_entrants``) and is carried here
    # verbatim as ``metadata["source_sha256"]`` -- reuse it rather than
    # letting ``canonical_match_id`` re-read ``spec.source_path`` from disk
    # a second time now that execution has already finished. Without this,
    # a source edit landing between execution start and this finalize call
    # could mint a ``match_id`` describing different code than what the
    # entrant metadata/replay above already (correctly) attribute to it.
    frozen_source_digests = {
        agent.agent_id: agent.metadata["source_sha256"]
        for agent in result.agents
        if isinstance(agent.metadata.get("source_sha256"), str) and agent.metadata["source_sha256"]
    }
    match_id = canonical_match_id(request, frozen_source_digests=frozen_source_digests)
    result_identity_entrants = [
        {**entrant, "diagnostic": _identity_safe_diagnostic(entrant["diagnostic"])}
        for entrant in entrants
    ]
    result_id = stable_id(
        "result",
        {
            "match_id": match_id,
            "winner": result.winner,
            "termination_reason": result.termination_reason.value,
            "ticks": result.ticks_run,
            "score": dict(result.score),
            "entrants": result_identity_entrants,
        },
    )

    # Every native match is homogeneous by the time it reaches this point
    # (NativeMatchService.run rejects mixed composition before execution),
    # so one discriminator on the header describes every entrant. The cast
    # is safe because that same validation already restricts `kind` to
    # exactly "python" before a request can reach this function.
    runtime_kind = cast(RuntimeKind, request.entrants[0].kind)
    resolved_ruleset_id = _resolve_ruleset_id(request)

    # Schema 4 is the process-agent replay shape. V6 Phase 2B.12 retired
    # every non-process Ruleset (bytefray-rules-1/-2, schema 3's only
    # writers), so this is now the only schema any current match writes --
    # see docs/research/v6/V6_PHASE2B12_SCOPE_C_RUNTIME_RETIREMENT.md.
    # ``replay.SUPPORTED_SCHEMA_VERSIONS`` still reads schema 3 (and 2) for
    # historical artifacts; only the writer's own selection collapses here.
    replay_schema_version = 4
    header: ReplayHeader | None = None
    ticks: list[Any] = []
    for record in iter_replay(source_replay_path):
        if isinstance(record, ReplayHeader):
            header = replace(
                record,
                replay_id=match_id,
                match_id=match_id,
                result_id=result_id,
                runtime_kind=runtime_kind,
                reproducibility=reproducibility,
                entrants=tuple(entrants),
                ruleset_id=resolved_ruleset_id,
                schema_version=replay_schema_version,
            )
        else:
            ticks.append(replace(record, schema_version=replay_schema_version))
    if header is None:
        raise PythonMatchExecutionError(
            RuntimeDiagnostic(
                code="artifact_write_failed",
                stage="artifact",
                message="Recorded replay is missing its header record.",
            )
        )

    termination_by_agent = {
        agent.agent_id: agent.termination_reason for agent in result.agents
    }
    final_agents = (
        tuple(
            replace(
                agent_state,
                termination_reason=termination_by_agent.get(agent_state.agent_id),
            )
            for agent_state in ticks[-1].agents
        )
        if ticks
        else ()
    )
    replay_winner = None if result.winner == WINNER_TIE_SENTINEL else result.winner
    terminal = ReplayMatchResult(
        winner=replay_winner,
        win_mode=request.config.win_mode,
        ticks=result.ticks_run,
        score=dict(result.score),
        agents=final_agents,
        replay_id=match_id,
        match_id=match_id,
        result_id=result_id,
        termination_reason=result.termination_reason.value,
        entrants=tuple(entrants),
        processes=(ticks[-1].processes if ticks else ()),
        schema_version=replay_schema_version,
    )

    publish_path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{publish_path.name}.", suffix=".canonical.tmp", dir=publish_path.parent
    )
    os.close(descriptor)
    temporary = Path(temporary_name)
    result_path = publish_path.with_name("result.json")
    complete = False
    try:
        write_replay(temporary, [header, *ticks, terminal])
        temporary.replace(publish_path)
        replay_digest = hashlib.sha256(publish_path.read_bytes()).hexdigest()
        envelope = ResultEnvelope(
            result_id=result_id,
            match_id=match_id,
            mode="b2",
            winner=result.winner,
            termination_reason=result.termination_reason.value,
            ticks=result.ticks_run,
            score=result.score,
            entrants=tuple(entrants),
            reproducibility=reproducibility,
            replay=ReplayReference(match_id, replay_digest, publish_path.name),
            ruleset_id=resolved_ruleset_id,
            occurrence_id=occurrence_id,
            completed_at=completed_at,
            product_version=product_version,
            schema_version=RESULT_SCHEMA_VERSION,
        )
        write_json_atomic(result_path, envelope.as_dict())
        complete = True
        return replace(
            result,
            replay_path=publish_path,
            result_id=result_id,
            match_id=match_id,
            replay_sha256=replay_digest,
            result_path=result_path,
        )
    finally:
        temporary.unlink(missing_ok=True)
        if source_replay_path != publish_path:
            source_replay_path.unlink(missing_ok=True)
        if not complete:
            publish_path.unlink(missing_ok=True)
            result_path.unlink(missing_ok=True)
            publish_path.with_name("summary.json").unlink(missing_ok=True)


class NativeMatchService:
    """Route homogeneous Python-agent entrants through the process controller.

    V6 Phase 2B.12 retired VM/blob execution and Agent API v1 execution
    (docs/research/v6/V6_PHASE2B12_SCOPE_C_RUNTIME_RETIREMENT.md): every
    entrant this service accepts must now be a Python (Agent API v2)
    entrant with a resolved ``python_spec``, and ``resolve_ruleset_policy``
    accepts only ``bytefray-rules-4``, so the three-way runtime dispatch
    this method used to perform (VM / Agent API v1 Python / Agent API v2
    process) has collapsed to the one remaining arm.
    """

    def run(self, request: MatchRequest) -> NativeMatchResult:
        kinds = {entrant.kind for entrant in request.entrants}
        if not request.entrants or kinds != {"python"}:
            values = ", ".join(sorted(kinds)) or "none"
            raise UnsupportedMatchCompositionError(
                f"Native matches must contain only Python entrants; received: {values}."
            )
        if any(entrant.python_spec is None for entrant in request.entrants):
            raise UnsupportedMatchCompositionError(
                "Every Python entrant requires a resolved Python AgentSpec."
            )
        ids = [entrant.agent_id for entrant in request.entrants]
        if len(set(ids)) != len(ids):
            raise UnsupportedMatchCompositionError(
                f"Entrant IDs must be unique; received: {ids}."
            )

        # Resolved once here -- the one boundary where a homogeneous native
        # match's Ruleset execution semantics (entrant scheduling and match
        # termination decision/reason, as of v1.5 Phase 4) are dispatched --
        # and threaded through to whichever runtime executes, rather than
        # each runtime resolving it itself. ``request.ruleset_id`` selects
        # the Ruleset (v2.0.0-alpha.1 additive selector); ``None`` resolves
        # to the retained control ``BYTEFRAY_RULESET_V4_ID`` exactly as
        # every caller that omits it does. ``resolve_ruleset_policy`` fails
        # closed for any unrecognized or retired ID instead of silently
        # executing under a different identity. ``_effective_ruleset_policy``
        # folds in the scheduler research override, if any -- the same
        # resolution ``canonical_match_id`` uses, so the policy that
        # schedules entrants here and the policy whose semantics are hashed
        # into this match's identity can never drift apart (V6 research-
        # integrity hardening).
        ruleset_policy = _effective_ruleset_policy(request)

        # Beta1 Phase 2's authoritative runtime-compatibility boundary:
        # ``kinds`` (already validated as homogeneous above) and
        # ``ruleset_policy`` (just resolved) are both in scope here and
        # nowhere else upstream of a runtime actually executing -- every
        # production caller (``bytefray run``/``agents test``/``tournament``,
        # and anything built on them) inherits this check without
        # duplicating it. Fires before either runtime is invoked and before
        # any replay/result artifact exists at ``replay_path``.
        unsupported_kinds = ruleset_policy.unsupported_runtime_kinds(kinds)
        if unsupported_kinds:
            raise RulesetRuntimeUnsupportedError(ruleset_policy.ruleset_id, unsupported_kinds)

        unsupported_agents = []
        for entrant in request.entrants:
            api_version = getattr(entrant.python_spec, "api_version", None)
            if not ruleset_policy.supports_agent(
                kind=entrant.kind, api_version=api_version
            ):
                unsupported_agents.append(
                    (entrant.agent_id, entrant.kind, api_version)
                )
        if unsupported_agents:
            raise RulesetAgentUnsupportedError(
                ruleset_policy.ruleset_id, unsupported_agents
            )

        # RC2 fail-closed guard (v2.0.0-rc1's release-blocking defect,
        # inherited by the stable v4 control -- see
        # ``_CORE_PLACEMENT_GUARDED_RULESET_IDS``): an invalid guarded-
        # Ruleset request whose entrants' vulnerable cores overlap must
        # never silently seed core ownership in entrant order and eliminate
        # an earlier entrant before its first action. Fires here -- after
        # composition/runtime-kind validation, before the runtime is
        # invoked and before any replay/result artifact exists at
        # ``replay_path`` -- for every caller, not only ones that went
        # through CLI/Designer default-placement resolution.
        _validate_v2_core_placement(ruleset_policy, request.entrants, request.config.arena_size)

        replay_path = request.replay_path.resolve()
        summary_path = replay_path.with_name("summary.json")
        _remove_python_artifacts(replay_path, summary_path)
        trace_writer = _open_trace_writer(request, schema_version=TRACE_SCHEMA_VERSION_V2)
        try:
            recorded = _run_v4_process_match(
                request, replay_path, summary_path, trace_writer, ruleset_policy
            )
            try:
                final = _finalize_native_artifacts(
                    request, recorded, final_replay_path=replay_path
                )
                if trace_writer is not None:
                    import hashlib

                    from battle_engine.agent_trace import BindingRecord
                    sha = hashlib.sha256(replay_path.read_bytes()).hexdigest()
                    # V6 research-integrity hardening: reuse the match_id
                    # `_finalize_native_artifacts` already froze above,
                    # rather than a third independent `canonical_match_id`
                    # call re-reading entrant source from disk -- the same
                    # TOCTOU window that call's own frozen-digest fix closes.
                    trace_writer.write_binding(BindingRecord(
                        match_id=final.match_id,
                        ruleset_id=ruleset_policy.ruleset_id,
                        entrant_identities=tuple(e.agent_id for e in request.entrants),
                        replay_sha256=sha,
                    ))
                return final
            finally:
                recorded.replay_path.unlink(missing_ok=True)
        finally:
            if trace_writer is not None:
                trace_writer.close()


__all__ = [
    "MatchEntrant",
    "MatchRequest",
    "NativeAgentResult",
    "NativeMatchResult",
    "NativeMatchService",
    "OverlappingCoreError",
    "PythonMatchExecutionError",
    "RulesetAgentUnsupportedError",
    "RulesetRuntimeUnsupportedError",
    "RuntimeDiagnostic",
    "UnsupportedMatchCompositionError",
    "canonical_match_id",
]
