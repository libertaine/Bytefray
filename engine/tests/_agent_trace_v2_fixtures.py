"""Hand-built ``bytefray.agent_trace`` schema-2 records for Agent Lab tests.

Written through the real :class:`~battle_engine.agent_trace.TraceWriter`, so
absent sensing fields are omitted exactly as the match runtime omits them.
Real-match coverage lives in ``test_agent_inspect.py``; these fixtures cover the
cases a short starter match cannot produce on demand (rejections, exceptions,
reordered or missing callbacks).
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from battle_engine.agent_trace import (
    ABSENT,
    TRACE_SCHEMA_VERSION_V2,
    Absent,
    BindingRecord,
    DecisionRecordV2,
    DeclarationRecord,
    ResetRecord,
    TraceActionV2,
    TraceDiagnostic,
    TraceHeader,
    TraceObservationV2,
    TraceResultV2,
    TraceWriter,
)


def decision(
    tick: int,
    agent_id: str = "A",
    process_id: str = "main",
    *,
    kind: str | None = "read",
    operand: int | None = 0,
    value: int | None = None,
    status: str | None = "APPLIED",
    read_value: int | None = None,
    read_owner: str | None = None,
    sensed: tuple[int, ...] | None | Absent = ABSENT,
    previous_sense: tuple[int, ...] | None | Absent = ABSENT,
    previous_read_value: int | None = None,
    visible: tuple[int, ...] = (),
    diagnostic: TraceDiagnostic | None = None,
    wall_time_ms: float = 0.25,
) -> DecisionRecordV2:
    return DecisionRecordV2(
        agent_id=agent_id,
        process_id=process_id,
        wall_time_ms=wall_time_ms,
        observation=TraceObservationV2(
            current_tick=tick,
            last_callback_tick=max(tick - 1, 0),
            previous_action_tick=max(tick - 1, 0),
            self_process_id=process_id,
            self_anchor=100,
            self_reach=128,
            own_core_base=100,
            own_core_size=8,
            visible_enemy_anchor_addresses=visible,
            previous_action_applied=tick > 1,
            previous_read_value=previous_read_value,
            previous_read_owner=None,
            previous_sense_anchors=previous_sense,
        ),
        action=None if kind is None else TraceActionV2(kind=kind, operand=operand, value=value),
        applied_result=None
        if status is None
        else TraceResultV2(
            status=status,
            normalized_address=operand,
            read_value=read_value,
            read_owner=read_owner,
            sensed_anchors=sensed,
        ),
        diagnostic=diagnostic,
    )


def standard_decisions() -> list[DecisionRecordV2]:
    """Three ticks, two entrants, two callbacks per process per tick."""

    records = []
    for tick in (1, 2, 3):
        for agent_id in ("A", "B"):
            for occurrence in (1, 2):
                records.append(decision(tick, agent_id, operand=tick * 10 + occurrence))
    return records


def write_trace_v2(
    path: Path,
    decisions: Iterable[DecisionRecordV2],
    *,
    declarations: Iterable[tuple[str, str]] = (("A", "main"), ("B", "main")),
    reset_diagnostic: TraceDiagnostic | None = None,
    binding: bool = True,
) -> Path:
    with TraceWriter(path) as writer:
        writer.write_header(
            TraceHeader(
                match_seed=1337,
                agents={"A": "alpha", "B": "bravo"},
                supervised=True,
                agent_call_timeout=5.0,
                schema_version=TRACE_SCHEMA_VERSION_V2,
            )
        )
        for agent_id in ("A", "B"):
            writer.write_reset(
                ResetRecord(
                    agent_id=agent_id,
                    wall_time_ms=1.0,
                    diagnostic=reset_diagnostic if agent_id == "A" else None,
                    sensing_window=27,
                )
            )
        for agent_id, process_id in declarations:
            writer.write_declaration(
                DeclarationRecord(agent_id=agent_id, process_id=process_id, reach=128, share=1.0)
            )
        for record in decisions:
            writer.write_decision_v2(record)
        if binding:
            writer.write_binding(
                BindingRecord(
                    match_id="match_fixture",
                    replay_sha256="ab" * 32,
                    ruleset_id="bytefray-rules-6-alpha1",
                    entrant_identities=("A", "B"),
                )
            )
    return path
