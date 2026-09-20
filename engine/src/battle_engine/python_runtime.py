"""Restricted deterministic runtime for homogeneous Python-agent matches."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from battle_engine.agent_api import (
    AGENT_API_VERSION,
    AgentValidationError,
)
from battle_engine.agent_trace import (
    TraceDiagnostic,
)
from battle_engine.ruleset_policy import (
    BYTEFRAY_RULESET_V2_ALPHA1_ID,
    BYTEFRAY_RULESET_V2_ALPHA11_ID,
    BYTEFRAY_RULESET_V2_ID,
    BYTEFRAY_RULESET_V3_ALPHA1_ID,
    BYTEFRAY_RULESET_V4_ALPHA1_ID,
    TerminationReason,
)
from battle_engine.scoring import ScoreMap, ScoringPolicy
from battle_engine.statistics import StatisticsCollector, StatisticsMap
from battle_engine.vm import VM

# v2.0.0-alpha.1 "Vulnerable Core" (docs/V2_0_ALPHA_ARCHITECTURE.md Sec 6,
# docs/V2_0_ALPHA1_EVALUATION.md): each Python entrant's core is a
# fixed-size window of ``CORE_SIZE`` bytes anchored at its own original
# spawn address (``entrant.start % arena_size``), using ordinary
# ``pos % arena_size`` wrap -- the same addressing every other arena access
# in this engine already uses (``vm.py``'s ``_rd32``/``_wr8``). Deliberately
# NOT derived from the entrant's program size, write count, or any other
# entrant-controlled property (that would reward padding/footprint
# inflation with survivability -- see the governing task's Phase 3).
#
# 8 was chosen, not computed: Python entrants load no code into the arena
# at all (unlike the VM path, which has a real per-entrant code footprint
# to reason about -- see ``VM.load_code``), so there is no existing
# "footprint" to size a core against in the first place. Against the
# default ``Config.arena_size == 4096``, 8 cells is small enough (0.2% of
# the arena) that a core is a genuine localized target an opponent must
# actually find and fully overwrite -- not a proxy for general territorial
# dominance -- while still being more than one cell, so a single incidental
# write passing through can't trivially end a match by accident. It is a
# fixed module constant, not threaded through ``Config``, per the governing
# task's instruction not to make it configurable for this alpha.
CORE_SIZE = 8

# v2.0.0-alpha.11 "Consistent Core Observability"
# (docs/V2_0_ALPHA11_RULESET_V2_CANDIDATE_RESOLUTION.md).
#
# The defect this closes, stated precisely: under
# ``bytefray-rules-2-alpha1``, ``seed_core_ownership`` establishes a core's
# initial ownership by writing the byte value ``0`` -- which is exactly what
# untouched arena already contains (docs/RULES.md: "The arena starts filled
# with byte 0"). Ownership is engine-internal and unreadable by any entrant,
# so *content* is the only channel through which a core can be observed at
# all. The consequence, measured across alpha.10's 976-match corpus: an
# entrant that never writes into its own core is literally invisible to
# every non-privileged searcher (0% capture rate against ``claimer``/
# ``hunter``), while an entrant that *defends* its core becomes detectable
# precisely because it defended (12-28% capture rate against the two
# defenders). Defending was informationally self-punishing and blind
# expansion bought invisibility for free.
#
# ``CORE_BEACON_BYTE`` is the public, fixed constant a core's own cells hold
# instead. It is Ruleset knowledge on exactly the same footing as
# ``CORE_SIZE`` already is (``core_defender``/``reactive_core_defender``/
# ``core_tracker`` all already hardcode ``8`` on that basis) -- not
# privileged information about any specific opponent, and deliberately not
# keyed to any reference agent: no agent needs to recognize this particular
# value to benefit, since every existing content-based searcher keys on
# "non-zero and not my own signature", which any non-zero beacon satisfies.
#
# ``0xCE`` was chosen, not computed: it must be non-zero (a zero beacon is
# the defect itself) and must differ from every signature byte used by any
# bundled starter or reference agent -- ``0x99`` (adaptive), ``0xC1``
# (claimer), ``0xE3`` (hunter), ``0xC2`` (strider), ``0x2C`` (wanderer),
# ``0xD3`` (core_defender), ``0x5E`` (core_seeker), ``0xA5`` (core_tracker),
# ``0xC7`` (reactive_core_defender) -- so that no agent is accidentally
# blinded to beacons by its own ``value != self.signature`` self-filter and
# no agent's ordinary territory is mistaken for a core.
CORE_BEACON_BYTE = 0xCE

# The historical alpha.1 seeding content: ownership without an observable
# footprint. Retained explicitly (rather than as a bare literal) so the
# alpha.1-vs-alpha.11 difference is a named, greppable Ruleset property.
CORE_SEED_BYTE_ALPHA1 = 0x00

# Which Ruleset identities carry which Python-only mechanic. Finite,
# explicit sets -- never a prefix or naming-convention check, for the same
# fail-closed reason ``ruleset_policy._RULESET_POLICIES`` is finite.
#
# ``BYTEFRAY_RULESET_V2_ID`` ("bytefray-rules-2", v2.0.0-beta1's permanent
# identity) carries both mechanics, identically to
# ``BYTEFRAY_RULESET_V2_ALPHA11_ID``: beta1 promotes alpha.11's
# evidence-backed candidate semantics as-is (see
# docs/V2_0_ALPHA11_RULESET_V2_CANDIDATE_RESOLUTION.md Sec 25-26 and
# docs/V2_0_BETA1_PLAN.md), sharing this exact implementation rather than
# duplicating it -- the two identities are distinguished by registration and
# persistence (``ruleset_policy.py``), not by behavior.
VULNERABLE_CORE_RULESET_IDS: frozenset[str] = frozenset(
    {
        BYTEFRAY_RULESET_V2_ALPHA1_ID,
        BYTEFRAY_RULESET_V2_ALPHA11_ID,
        BYTEFRAY_RULESET_V2_ID,
        # v3 Phase 2: the locality experiment changes *addressing*, nothing
        # else. Core vulnerability and core observability are inherited from
        # Ruleset v2 unchanged so the two ecologies stay comparable -- a
        # locality result that differed because the core mechanic also
        # differed would answer no question Phase 2 asks.
        BYTEFRAY_RULESET_V3_ALPHA1_ID,
        # v4 research: the interleaved scheduler experiment changes *scheduling*,
        # nothing else. Inherits vulnerable and observable core from Ruleset v2.
        BYTEFRAY_RULESET_V4_ALPHA1_ID,
    }
)

# OBSERVABLE_CORE_RULESET_IDS / has_observable_core / core_seed_byte /
# maintain_core_beacons ("Consistent Core Observability", v2.0.0-alpha.11)
# were removed by V6 Phase 2B.12
# (docs/research/v6/V6_PHASE2B12_SCOPE_C_RUNTIME_RETIREMENT.md): every
# member of that table was also a member of VULNERABLE_CORE_RULESET_IDS
# above, and -- confirmed by re-checking every call site against current
# source, correcting Phase 2B.8's original assumption that the two tables
# were an inseparable pair (T-9) -- neither the table nor the three
# functions had any historical-reader consumer; their only call sites were
# the now-removed ``PythonEntrantController``/``SupervisedPythonEntrantController``.
# ``VULNERABLE_CORE_RULESET_IDS``/``has_vulnerable_core`` remain: they ARE
# consulted by a reader (``client/src/battle_client/replay_status.py``) to
# derive historical per-entrant core-integrity status for display.
# ``CORE_BEACON_BYTE``/``CORE_SEED_BYTE_ALPHA1`` remain too, as plain
# historical-value constants several tests still pin directly.


# ---------------------------------------------------------------------------
# v3 research Phase 2's experimental bounded-locality mechanic (a Python
# entrant confined to a single arena locus with a bounded read/write/move
# reach) was retired from executable registration -- along with its only
# executable identity, ``bytefray-rules-3-alpha1`` -- by V6 Phase 2B.9
# (docs/research/v6/V6_PHASE2B9_SCOPE_A_RULESET_RETIREMENT.md), which removed
# this section's implementation as dead code. The design rationale and full
# experimental history remain in docs/V3_PHASE2_LOCALITY_FEASIBILITY.md and
# docs/archive/v3/; ``ActionKind.MOVE``/``LOCAL_READ``/``LOCAL_WRITE``,
# ``MatchContext.locality_reach``, and ``Observation.locus`` (all in
# ``agent_api.py``) are retained unconditionally for historical replay/trace
# deserialization. Their retired execution validator is not retained here.
# ---------------------------------------------------------------------------


def has_vulnerable_core(ruleset_id: str) -> bool:
    """Whether ``ruleset_id``'s Python semantics include core capture."""

    return ruleset_id in VULNERABLE_CORE_RULESET_IDS


def core_addresses(core_start: int, arena_size: int) -> tuple[int, ...]:
    """Every address in one entrant's core region, using ordinary arena wrap."""

    start = core_start % arena_size
    return tuple((start + offset) % arena_size for offset in range(CORE_SIZE))


def _attribute_core_capture(
    state: Any,
    core_addrs: tuple[int, ...],
    before_owners: tuple[str | None, ...],
    vm: VM,
) -> str | None:
    """Find which entrant's write caused ``state`` to lose its last core cell.

    Replays this tick's ``vm.tick_diffs`` (already in true execution order --
    entrants act in fixed scheduled order, so diffs are appended in the
    order writes actually happened) restricted to addresses inside
    ``core_addrs``, starting from ``before_owners`` (this entrant's core
    ownership before any of this tick's actions ran). Returns the ``owner``
    of the one diff that makes ``state``'s core-owned count drop from one
    to zero -- unambiguous by construction, since only one write can be
    "the write that took the last cell" once diffs are replayed in their
    real order. Returns ``None`` if ``state`` already owned zero core cells
    before this tick's actions ran (an edge case with no single attributable
    cause this tick, e.g. two entrants spawned with overlapping cores).

    ``state`` is duck-typed (an ``Any``, not ``PythonEntrantState``): its
    only caller is now ``process_runtime.ProcessMatchController``, whose own
    ``EntrantState`` carries the same ``agent_id`` attribute this function
    reads. V6 Phase 2B.12 removed ``PythonEntrantState`` and its sole
    producer, the Agent API v1 controllers, alongside Agent API v1
    execution; this shared core-capture logic stayed, since the retained
    control (``bytefray-rules-4``) still uses it (see
    ``process_runtime.py``'s own ``apply_core_capture`` call).
    """

    core_set = set(core_addrs)
    local_owner: dict[int, str | None] = dict(zip(core_addrs, before_owners, strict=True))
    remaining = sum(1 for owner in local_owner.values() if owner == state.agent_id)
    if remaining == 0:
        return None
    for start, length, owner, _values in vm.tick_diffs:
        for offset in range(length):
            address = (start + offset) % len(vm.arena)
            if address not in core_set:
                continue
            previous = local_owner[address]
            if previous == owner:
                continue
            local_owner[address] = owner
            if previous == state.agent_id:
                remaining -= 1
                if remaining == 0:
                    return owner
    return None  # pragma: no cover - unreachable given the caller's own invariant


def apply_core_capture(
    states: list[Any],
    vm: VM,
    pre_tick_core_owners: Mapping[str, tuple[str | None, ...]],
    scoring: ScoringPolicy,
    score: ScoreMap,
    statistics_collector: StatisticsCollector,
    statistics: StatisticsMap,
    events: list[dict[str, Any]],
) -> None:
    """bytefray-rules-2-alpha1: kill any living entrant now core-captured.

    An entrant is core-captured when it owns zero cells of its own fixed
    ``CORE_SIZE`` core region (Phase 4's semantic definition -- deliberately
    "owns zero", not "one opponent owns all of it", so the rule stays
    well-defined if Bytefray ever supports more than two entrants). Checked
    once per tick, after all of this tick's actions have executed and
    before scoring/termination -- so a captured entrant receives no
    alive/territory score for the tick it dies on, exactly like an
    ordinary Python ``HALT``, and no hidden extra turn. Kill credit goes to
    whichever entrant's ``WRITE`` caused the final defender-owned core cell
    to change owner this tick, when :func:`_attribute_core_capture` can
    determine it unambiguously; otherwise this is recorded as an
    unattributed death, exactly like an ordinary unattributed Python
    forfeit/halt.
    """

    for state in states:
        if not state.alive:
            continue
        addrs = core_addresses(state.core_start, len(vm.arena))
        owned_now = sum(1 for address in addrs if vm.writer[address] == state.agent_id)
        if owned_now > 0:
            continue
        before = pre_tick_core_owners.get(state.agent_id, ())
        # ``before`` is only ever absent-or-mis-sized if this entrant somehow
        # reached this point without a pre-tick snapshot (an invariant
        # violation, not a real match state -- every state alive at tick
        # start is snapshotted before any of that tick's actions run); guard
        # defensively rather than let ``_attribute_core_capture``'s
        # ``zip(..., strict=True)`` raise on a length mismatch.
        killer = (
            _attribute_core_capture(state, addrs, before, vm)
            if len(before) == len(addrs)
            else None
        )
        state.alive = False
        state.entrant_termination = "core_captured"
        if killer is not None and killer != state.agent_id:
            scoring.score_kill(score, killer)
            statistics_collector.record_death(statistics, state.agent_id, killer)
            events.append({"type": "kill", "victim": state.agent_id, "by": killer})
        else:
            statistics_collector.record_death(statistics, state.agent_id)
            events.append({"type": "death", "victim": state.agent_id})


@dataclass(frozen=True)
class RuntimeDiagnostic:
    """Structured failure detail kept separate from winner resolution."""

    code: str
    stage: str
    message: str
    agent_id: str | None = None
    slot: int | None = None
    exception_type: str | None = None
    tick: int | None = None
    action_slot: int | None = None


def _safe_message(value: object, *, limit: int = 240) -> str:
    """Normalize callback text for concise diagnostics and deterministic replay."""

    message = " ".join(str(value).split())
    return message[:limit] if message else "No error message was provided."


class PythonEntrantInitializationError(ValueError):
    """A Python entrant could not be reset before tick zero."""

    code = "agent_initialization_failed"

    def __init__(self, diagnostic: RuntimeDiagnostic):
        super().__init__(diagnostic.message)
        self.diagnostic = diagnostic


class InvalidPythonActionError(ValueError):
    """An ``act`` result is not one valid Phase 3a operation."""


def diagnose_load_failure(
    exc: AgentValidationError, *, agent_id: str, slot: int = 0
) -> RuntimeDiagnostic:
    """Build the stable diagnostic for a load-stage failure.

    Shared by a real match's initialization path and Agent API validation
    (``battle_engine.agent_validation``), so the two report the identical
    code/stage/message for the same underlying ``load_python_agent`` failure.
    """

    return RuntimeDiagnostic(
        code=exc.code,
        stage="load",
        message=_safe_message(exc),
        agent_id=agent_id,
        slot=slot,
        exception_type=type(exc).__name__,
    )


def diagnose_reset_failure(
    exc: Exception, *, agent_id: str, slot: int = 0
) -> RuntimeDiagnostic:
    """Build the stable diagnostic for a reset-stage failure.

    Shared by a real match's initialization path and Agent API validation.
    """

    return RuntimeDiagnostic(
        code="agent_reset_failed",
        stage="reset",
        message=(
            f"Python agent {agent_id} reset failed: "
            f"{type(exc).__name__}: {_safe_message(exc)}"
        ),
        agent_id=agent_id,
        slot=slot,
        exception_type=type(exc).__name__,
    )


def diagnose_action_exception(
    exc: Exception, *, agent_id: str, slot: int = 0, tick: int, action_slot: int
) -> RuntimeDiagnostic:
    """Build the stable diagnostic for an ``act()``-stage exception.

    Shared by a real match's forfeit path and Agent API validation.
    """

    return RuntimeDiagnostic(
        code="agent_action_failed",
        stage="action",
        message=(
            f"Python agent {agent_id} act failed: "
            f"{type(exc).__name__}: {_safe_message(exc)}"
        ),
        agent_id=agent_id,
        slot=slot,
        exception_type=type(exc).__name__,
        tick=tick,
        action_slot=action_slot,
    )


def diagnose_invalid_action(
    exc: InvalidPythonActionError,
    *,
    agent_id: str,
    slot: int = 0,
    tick: int,
    action_slot: int,
) -> RuntimeDiagnostic:
    """Build the stable diagnostic for an ``act()``-stage invalid-action rejection.

    Shared by a real match's forfeit path and Agent API validation.
    """

    return RuntimeDiagnostic(
        code="agent_action_invalid",
        stage="action",
        message=(
            f"Python agent {agent_id} returned an invalid action: {_safe_message(exc)}"
        ),
        agent_id=agent_id,
        slot=slot,
        exception_type=type(exc).__name__,
        tick=tick,
        action_slot=action_slot,
    )


def diagnose_load_timeout(*, agent_id: str, slot: int, timeout: float) -> RuntimeDiagnostic:
    """Build the diagnostic for a supervised worker that did not finish loading in time.

    See ``docs/specs/agent_lab.md`` §7 -- development-time hang
    containment, not a security sandbox.
    """

    return RuntimeDiagnostic(
        code="agent_load_timeout",
        stage="load",
        message=f"Python agent {agent_id} did not finish loading within {timeout:g}s.",
        agent_id=agent_id,
        slot=slot,
    )


def diagnose_reset_timeout(*, agent_id: str, slot: int, timeout: float) -> RuntimeDiagnostic:
    """Build the diagnostic for a supervised worker whose ``reset()`` did not return in time."""

    return RuntimeDiagnostic(
        code="agent_reset_timeout",
        stage="reset",
        message=f"Python agent {agent_id} reset() did not return within {timeout:g}s.",
        agent_id=agent_id,
        slot=slot,
    )


def diagnose_action_timeout(
    *, agent_id: str, slot: int, tick: int, action_slot: int, timeout: float
) -> RuntimeDiagnostic:
    """Build the diagnostic for a supervised worker whose ``act()`` did not return in time."""

    return RuntimeDiagnostic(
        code="agent_action_timeout",
        stage="action",
        message=f"Python agent {agent_id} act() did not return within {timeout:g}s.",
        agent_id=agent_id,
        slot=slot,
        tick=tick,
        action_slot=action_slot,
    )


def diagnose_worker_exited(
    *,
    agent_id: str,
    slot: int,
    stage: str,
    tick: int | None = None,
    action_slot: int | None = None,
    exit_code: int | None = None,
) -> RuntimeDiagnostic:
    """Build the diagnostic for a supervised worker process that exited unexpectedly."""

    suffix = f" (exit code {exit_code})" if exit_code is not None else " (exit code unknown)"
    return RuntimeDiagnostic(
        code="agent_worker_exited",
        stage=stage,
        message=(
            f"Python agent {agent_id}'s supervised worker process exited unexpectedly "
            f"during {stage}{suffix}."
        ),
        agent_id=agent_id,
        slot=slot,
        exception_type="WorkerExited",
        tick=tick,
        action_slot=action_slot,
    )


def diagnose_worker_protocol_error(
    *,
    agent_id: str,
    slot: int,
    stage: str,
    detail: str,
    tick: int | None = None,
    action_slot: int | None = None,
) -> RuntimeDiagnostic:
    """Build the diagnostic for a supervised worker response that could not be parsed."""

    return RuntimeDiagnostic(
        code="agent_worker_protocol_error",
        stage=stage,
        message=(
            f"Python agent {agent_id}'s supervised worker sent an unexpected response "
            f"during {stage}: {detail}"
        ),
        agent_id=agent_id,
        slot=slot,
        exception_type="WorkerProtocolError",
        tick=tick,
        action_slot=action_slot,
    )


def _to_trace_diagnostic(diagnostic: RuntimeDiagnostic | None) -> TraceDiagnostic | None:
    if diagnostic is None:
        return None
    return TraceDiagnostic(
        code=diagnostic.code,
        stage=diagnostic.stage,
        message=diagnostic.message,
        agent_id=diagnostic.agent_id,
        slot=diagnostic.slot,
        exception_type=diagnostic.exception_type,
        tick=diagnostic.tick,
        action_slot=diagnostic.action_slot,
    )


def derive_agent_seed(
    match_seed: int, slot: int, agent_id: str, api_version: int = AGENT_API_VERSION
) -> int:
    """Derive one stable independent RNG seed without Python's randomized hash."""

    material = f"battle2-python-v1\0{match_seed}\0{slot}\0{agent_id}\0{api_version}"
    digest = hashlib.sha256(material.encode("utf-8")).digest()
    return int.from_bytes(digest[:16], "big")


__all__ = [
    "CORE_BEACON_BYTE",
    "CORE_SEED_BYTE_ALPHA1",
    "CORE_SIZE",
    "VULNERABLE_CORE_RULESET_IDS",
    "InvalidPythonActionError",
    "PythonEntrantInitializationError",
    "RuntimeDiagnostic",
    "TerminationReason",
    "apply_core_capture",
    "core_addresses",
    "derive_agent_seed",
    "diagnose_action_exception",
    "diagnose_action_timeout",
    "diagnose_invalid_action",
    "diagnose_load_failure",
    "diagnose_load_timeout",
    "diagnose_reset_failure",
    "diagnose_reset_timeout",
    "diagnose_worker_exited",
    "diagnose_worker_protocol_error",
    "has_vulnerable_core",
]
