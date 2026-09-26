"""Shared worker-failure diagnostic mapping for supervised Python calls.

V6 Phase 2B.12 retired Agent API v1 execution
(docs/research/v6/V6_PHASE2B12_SCOPE_C_RUNTIME_RETIREMENT.md), removing
this module's ``SupervisedPythonEntrantController`` (the Agent API v1
whole-match-lifetime worker-subprocess controller) and its
``_NullAgentInstance`` placeholder -- both execution-only and unreachable
once no Ruleset can dispatch to Agent API v1. Phase 2B.11's audit corrected
an earlier phase's assumption that this whole module was wholly dead: the
retained control's own worker path (``process_runtime.py``) and Agent
Validation (``agent_validation.py``, which supervises a single dry-run
``load``/``reset``/``act`` call independent of ``SupervisedPythonEntrantController``)
both still import :func:`diagnostic_for_worker_result`, so this module
stays -- narrowed to exactly that shared diagnostic-mapping seam.
"""

from __future__ import annotations

from typing import Any

from battle_engine.agent_worker import WorkerCallResult, WorkerCallStatus
from battle_engine.python_runtime import (
    RuntimeDiagnostic,
    diagnose_action_timeout,
    diagnose_load_timeout,
    diagnose_reset_timeout,
    diagnose_worker_exited,
    diagnose_worker_protocol_error,
)


def _diagnostic_from_payload(payload: dict[str, Any] | None) -> RuntimeDiagnostic:
    data = (payload or {}).get("diagnostic") or {}
    return RuntimeDiagnostic(
        code=data.get("code", "agent_worker_protocol_error"),
        stage=data.get("stage", "internal"),
        message=data.get("message", "Worker reported a failure with no diagnostic detail."),
        agent_id=data.get("agent_id"),
        slot=data.get("slot"),
        exception_type=data.get("exception_type"),
        tick=data.get("tick"),
        action_slot=data.get("action_slot"),
    )


def diagnostic_for_worker_result(
    result: WorkerCallResult,
    *,
    agent_id: str,
    slot: int,
    stage: str,
    timeout: float,
    exit_code: int | None,
    tick: int | None = None,
    action_slot: int | None = None,
) -> RuntimeDiagnostic:
    """Map one non-OK :class:`WorkerCallResult` to the matching diagnostic.

    Shared by :mod:`battle_engine.process_runtime` (the retained control's
    own worker path) and :mod:`battle_engine.agent_validation` (a single
    supervised dry-run call), so both report identical codes/messages for
    the same underlying worker failure -- the same "reuse-enabling
    extraction" pattern ``diagnose_load_failure``/``diagnose_reset_failure``
    already established for the unsupervised path (see
    ``docs/specs/agent_validation.md`` §2).
    """

    if result.status is WorkerCallStatus.FAILED:
        return _diagnostic_from_payload(result.payload)
    if result.status is WorkerCallStatus.TIMEOUT:
        if stage == "load":
            return diagnose_load_timeout(agent_id=agent_id, slot=slot, timeout=timeout)
        if stage == "reset":
            return diagnose_reset_timeout(agent_id=agent_id, slot=slot, timeout=timeout)
        return diagnose_action_timeout(
            agent_id=agent_id, slot=slot, tick=tick or 0, action_slot=action_slot or 0, timeout=timeout
        )
    if result.status is WorkerCallStatus.EXITED:
        return diagnose_worker_exited(
            agent_id=agent_id, slot=slot, stage=stage, tick=tick, action_slot=action_slot,
            exit_code=exit_code,
        )
    detail = str((result.payload or {}).get("raw", "unparseable response"))
    return diagnose_worker_protocol_error(
        agent_id=agent_id, slot=slot, stage=stage, detail=detail, tick=tick, action_slot=action_slot
    )


__all__ = ["diagnostic_for_worker_result"]
