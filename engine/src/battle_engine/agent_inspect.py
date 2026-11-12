"""``bytefray agents inspect``/``bytefray agents diverge`` — trace inspection CLI.

Parses an already-written ``bytefray.agent_trace`` file
(:mod:`battle_engine.agent_trace`) and answers the questions Agent Lab
exists to answer: what did an agent see and do on a given tick, why did a
call fail, and where did two runs first disagree. Executes **no agent
code** -- this module only reads JSONL already produced by a prior
``agents test``/``agents validate`` run, so unlike those two tools it
needs no timeout and no worker subprocess. See
``docs/specs/agent_lab.md`` §9/§10.

Schema 1 (Agent API v1 ``decision`` records) and schema 2 (Agent API v2
``declaration``/``decision_v2``/``binding`` records) are both read, each with
its own reader and its own formatting; :func:`load_trace` dispatches on the
header's ``schema_version`` and never converts one schema into the other.
Schema-1 output is unchanged.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, fields
from pathlib import Path

from battle_engine.agent_trace import (
    ABSENT,
    AnyTraceDocument,
    CallbackKey,
    DecisionRecord,
    DecisionRecordV2,
    Divergence,
    DivergenceV2,
    ResetRecord,
    TraceDocument,
    TraceDocumentV2,
    TraceFormatError,
    TraceObservationV2,
    TraceResultV2,
    TraceVersionError,
    callback_keys,
    first_divergence,
    first_divergence_v2,
    read_any_trace,
)


class TraceInspectionError(RuntimeError):
    """A tool-level failure (missing/unreadable/malformed trace); exit 2."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def resolve_trace_path(value: str) -> Path:
    """Accept either a run directory (containing ``trace.jsonl``) or a direct file path."""

    path = Path(value).expanduser()
    if path.is_dir():
        candidate = path / "trace.jsonl"
        if not candidate.is_file():
            raise TraceInspectionError(
                "trace_file_missing", f"No trace.jsonl found under directory: {path}"
            )
        return candidate
    if path.is_file():
        return path
    raise TraceInspectionError("trace_file_missing", f"Trace path not found: {path}")


def load_trace(value: str) -> AnyTraceDocument:
    """Load a schema-1 or schema-2 trace, dispatching on its header's ``schema_version``."""

    path = resolve_trace_path(value)
    try:
        return read_any_trace(path)
    except TraceVersionError as exc:
        raise TraceInspectionError("trace_schema_unsupported", str(exc)) from exc
    except TraceFormatError as exc:
        raise TraceInspectionError("trace_format_invalid", str(exc)) from exc


def _schema_version(document: AnyTraceDocument) -> int:
    return 2 if isinstance(document, TraceDocumentV2) else 1


def _format_observation(record: DecisionRecord) -> list[str]:
    observation = record.observation
    return [
        f"  observation.pc: {observation.pc}",
        f"  observation.register_a: {observation.register_a}",
        f"  observation.register_p: {observation.register_p}",
        f"  observation.zero_flag: {observation.zero_flag}",
        f"  observation.last_read: {observation.last_read}",
        f"  observation.alive: {observation.alive}",
    ]


def _format_decision(record: DecisionRecord) -> str:
    lines = [
        f"tick: {record.tick}",
        f"agent: {record.agent_id}",
        f"action_slot: {record.action_slot}",
        f"wall_time_ms: {record.wall_time_ms:.3f}",
        *_format_observation(record),
    ]
    if record.action is not None:
        lines.append(
            f"  action: {record.action.kind} operand={record.action.operand} value={record.action.value}"
        )
    if record.diagnostic is not None:
        diagnostic = record.diagnostic
        lines.append(f"  diagnostic.code: {diagnostic.code}")
        lines.append(f"  diagnostic.stage: {diagnostic.stage}")
        lines.append(f"  diagnostic.message: {diagnostic.message}")
    return "\n".join(lines)


def _format_reset(record: ResetRecord) -> str:
    lines = [
        f"reset agent: {record.agent_id}",
        f"wall_time_ms: {record.wall_time_ms:.3f}",
    ]
    if record.diagnostic is not None:
        diagnostic = record.diagnostic
        lines.append(f"  diagnostic.code: {diagnostic.code}")
        lines.append(f"  diagnostic.stage: {diagnostic.stage}")
        lines.append(f"  diagnostic.message: {diagnostic.message}")
    return "\n".join(lines)


def _print_summary(document: TraceDocument) -> None:
    header = document.header
    print(f"trace: {document.path}")
    print(f"schema: {header.schema} v{header.schema_version}")
    print(f"match_seed: {header.match_seed}")
    print(f"supervised: {header.supervised}")
    if header.agent_call_timeout is not None:
        print(f"agent_call_timeout: {header.agent_call_timeout:g}")
    print(f"agents: {', '.join(f'{slot}={name}' for slot, name in sorted(header.agents.items()))}")
    tick_range = document.tick_range()
    if tick_range is None:
        print("ticks: none")
    else:
        print(f"ticks: {tick_range[0]}-{tick_range[1]}")
    print(f"decisions: {len(document.decisions)}")
    print(f"resets: {len(document.resets)}")
    failures = document.failures()
    print(f"failures: {len(failures)}")
    for record in failures:
        if isinstance(record, ResetRecord):
            assert record.diagnostic is not None
            print(f"  reset {record.agent_id}: {record.diagnostic.code}")
        else:
            assert record.diagnostic is not None
            print(f"  tick {record.tick} {record.agent_id}: {record.diagnostic.code}")


def _filtered_decisions(
    document: TraceDocument,
    *,
    tick: int | None,
    around: int | None,
    window: int,
    agent: str | None,
    failures_only: bool,
) -> list[DecisionRecord]:
    if tick is not None:
        records: list[DecisionRecord] = list(document.for_tick(tick))
    elif around is not None:
        records = list(document.around_tick(around, window))
    else:
        records = list(document.decisions)
    if agent is not None:
        records = [r for r in records if r.agent_id == agent]
    if failures_only:
        records = [r for r in records if r.diagnostic is not None]
    return records


# ---------------------------------------------------------------------------
# Schema 2 (Agent API v2)
# ---------------------------------------------------------------------------

_APPLIED = "APPLIED"


def _render(value: object) -> str:
    """Render a V2 field so absent, ``None`` and an empty tuple stay distinguishable."""

    if value is ABSENT:
        return "(absent)"
    if isinstance(value, tuple):
        return "[" + ", ".join(str(item) for item in value) + "]"
    return str(value)


def is_failure_v2(record: DecisionRecordV2) -> bool:
    """A V2 callback that carries a diagnostic or whose action was not applied."""

    if record.diagnostic is not None:
        return True
    return record.applied_result is not None and record.applied_result.status != _APPLIED


def _failure_label_v2(record: DecisionRecordV2) -> str:
    status = record.applied_result.status if record.applied_result is not None else None
    if record.diagnostic is None:
        return str(status)
    return record.diagnostic.code if status is None else f"{record.diagnostic.code} ({status})"


def _format_decision_v2(record: DecisionRecordV2, key: CallbackKey | None = None) -> str:
    """Format one ``decision_v2`` callback; ``key`` adds its per-tick callback number."""

    observation = record.observation
    lines = [
        f"tick: {observation.current_tick}",
        f"agent: {record.agent_id}",
        f"process: {record.process_id}",
    ]
    if key is not None:
        lines.append(f"callback: {key.occurrence}")
    lines.append(f"wall_time_ms: {record.wall_time_ms:.3f}")
    lines += [
        f"  observation.{field.name}: {_render(getattr(observation, field.name))}"
        for field in fields(TraceObservationV2)
    ]
    if record.action is None:
        lines.append("  action: none")
    else:
        action = record.action
        lines.append(f"  action: {action.kind} operand={action.operand} value={action.value}")
    if record.applied_result is None:
        lines.append("  applied: none")
    else:
        result = record.applied_result
        lines += [
            f"  applied.{field.name}: {_render(getattr(result, field.name))}"
            for field in fields(TraceResultV2)
        ]
    if record.diagnostic is not None:
        diagnostic = record.diagnostic
        lines.append(f"  diagnostic.code: {diagnostic.code}")
        lines.append(f"  diagnostic.stage: {diagnostic.stage}")
        lines.append(f"  diagnostic.message: {diagnostic.message}")
    return "\n".join(lines)


def _format_reset_v2(record: ResetRecord) -> str:
    return f"{_format_reset(record)}\nsensing_window: {_render(record.sensing_window)}"


@dataclass(frozen=True)
class DecisionView:
    """A version-neutral index entry over one decision record.

    Holds the original, unconverted record; only the fields every view needs
    for filtering (tick, entrant, process, failure) are lifted out. Shared by
    the CLI and the Designer's Trace Inspector.
    """

    record: DecisionRecord | DecisionRecordV2
    tick: int
    agent_id: str
    process_id: str | None
    key: CallbackKey | None
    failure: bool

    def format(self) -> str:
        if isinstance(self.record, DecisionRecordV2):
            return _format_decision_v2(self.record, self.key)
        return _format_decision(self.record)


def decision_views(document: AnyTraceDocument) -> tuple[DecisionView, ...]:
    """One :class:`DecisionView` per decision record, in trace append order."""

    if isinstance(document, TraceDocumentV2):
        decisions = document.decisions
        return tuple(
            DecisionView(
                record=record,
                tick=record.observation.current_tick,
                agent_id=record.agent_id,
                process_id=record.process_id,
                key=key,
                failure=is_failure_v2(record),
            )
            for record, key in zip(decisions, callback_keys(decisions), strict=True)
        )
    return tuple(
        DecisionView(
            record=record,
            tick=record.tick,
            agent_id=record.agent_id,
            process_id=None,
            key=None,
            failure=record.diagnostic is not None,
        )
        for record in document.decisions
    )


def format_reset(document: AnyTraceDocument, record: ResetRecord) -> str:
    """Format a reset record in its trace's schema convention."""

    if isinstance(document, TraceDocumentV2):
        return _format_reset_v2(record)
    return _format_reset(record)


def trace_tick_range(views: tuple[DecisionView, ...]) -> tuple[int, int] | None:
    ticks = [view.tick for view in views]
    return (min(ticks), max(ticks)) if ticks else None


def _print_summary_v2(document: TraceDocumentV2, views: tuple[DecisionView, ...]) -> None:
    header = document.header
    print(f"trace: {document.path}")
    print(f"schema: {header.schema} v{header.schema_version}")
    print(f"match_seed: {header.match_seed}")
    print(f"supervised: {header.supervised}")
    if header.agent_call_timeout is not None:
        print(f"agent_call_timeout: {header.agent_call_timeout:g}")
    print(f"agents: {', '.join(f'{slot}={name}' for slot, name in sorted(header.agents.items()))}")
    binding = document.binding
    if binding is None:
        print("ruleset: not recorded (no binding record)")
        print("replay_binding: none")
    else:
        print(f"ruleset: {binding.ruleset_id}")
        print("replay_binding: present (not verified; inspect does not read the replay)")
        print(f"  match_id: {binding.match_id}")
        print(f"  replay_sha256: {binding.replay_sha256}")
        print(f"  entrant_identities: {', '.join(binding.entrant_identities)}")
    tick_range = trace_tick_range(views)
    if tick_range is None:
        print("ticks: none")
    else:
        print(f"ticks: {tick_range[0]}-{tick_range[1]}")
    print(f"decisions: {len(views)}")
    declarations = document.declarations
    print(f"processes: {len(declarations)}")
    for declaration in declarations:
        print(
            f"  {declaration.agent_id}/{declaration.process_id}: "
            f"reach={declaration.reach} share={declaration.share:g}"
        )
    resets = document.resets
    print(f"resets: {len(resets)}")
    for reset in resets:
        print(f"  reset {reset.agent_id}: sensing_window={_render(reset.sensing_window)}")
    failed_resets = [r for r in resets if r.diagnostic is not None]
    failed_views = [v for v in views if v.failure]
    print(f"failures: {len(failed_resets) + len(failed_views)}")
    for reset in failed_resets:
        assert reset.diagnostic is not None
        print(f"  reset {reset.agent_id}: {reset.diagnostic.code}")
    for view in failed_views:
        assert isinstance(view.record, DecisionRecordV2) and view.key is not None
        print(
            f"  tick {view.tick} {view.agent_id}/{view.process_id} "
            f"callback {view.key.occurrence}: {_failure_label_v2(view.record)}"
        )


def _inspect_v2(document: TraceDocumentV2, args: argparse.Namespace) -> int:
    views = decision_views(document)
    if (
        args.tick is None
        and args.around is None
        and not args.failures
        and args.agent is None
        and args.process is None
    ):
        _print_summary_v2(document, views)
        return 0

    selected = list(views)
    if args.tick is not None:
        selected = [v for v in selected if v.tick == args.tick]
    elif args.around is not None:
        low, high = args.around - args.window, args.around + args.window
        selected = [v for v in selected if low <= v.tick <= high]
    if args.agent is not None:
        selected = [v for v in selected if v.agent_id == args.agent]
    if args.process is not None:
        selected = [v for v in selected if v.process_id == args.process]
    if args.failures:
        selected = [v for v in selected if v.failure]

    if args.failures and args.tick is None and args.around is None:
        blocks = [
            _format_reset_v2(r)
            for r in document.resets
            if r.diagnostic is not None and (args.agent is None or r.agent_id == args.agent)
        ]
        blocks += [v.format() for v in selected]
        print("\n\n".join(blocks) if blocks else "no failures recorded")
        return 0

    if not selected:
        print("no matching decisions")
        return 0
    print("\n\n".join(v.format() for v in selected))
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bytefray agents inspect",
        description=(
            "Inspect a bytefray.agent_trace development trace (schema 1 or 2): show "
            "a summary, one tick's decisions, decisions around a tick, or only "
            "failures. Executes no agent code."
        ),
    )
    parser.add_argument("run", help="run directory (containing trace.jsonl) or a direct trace path")
    parser.add_argument("--tick", type=int, default=None, help="show decisions at exactly this tick")
    parser.add_argument(
        "--around", type=int, default=None, help="show decisions within --window ticks of this tick"
    )
    parser.add_argument("--window", type=int, default=5, help="tick window for --around (default: 5)")
    parser.add_argument("--agent", default=None, help="restrict to one agent id/slot")
    parser.add_argument(
        "--process",
        default=None,
        help=(
            "schema-2 traces only: restrict decisions to one process id (combine with "
            "--agent); failed resets belong to an entrant, not a process, so --failures "
            "still lists them unless --agent narrows them"
        ),
    )
    parser.add_argument(
        "--failures",
        action="store_true",
        help=(
            "show only decisions/resets carrying a diagnostic (schema 2: also "
            "callbacks whose action was not APPLIED)"
        ),
    )
    return parser


def _print_tool_error(code: str, message: str) -> int:
    print("status: error", file=sys.stderr)
    print(f"code: {code}", file=sys.stderr)
    print(f"error: {message}", file=sys.stderr)
    return 2


def inspect_main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        loaded = load_trace(args.run)
    except TraceInspectionError as exc:
        return _print_tool_error(exc.code, exc.message)

    if isinstance(loaded, TraceDocumentV2):
        return _inspect_v2(loaded, args)
    document = loaded
    if args.process is not None:
        return _print_tool_error(
            "trace_option_unsupported",
            f"--process applies only to schema-2 traces; {document.path} is schema 1, "
            "whose decisions have no process identity (use --agent)",
        )

    if args.tick is None and args.around is None and not args.failures and args.agent is None:
        _print_summary(document)
        return 0

    if args.failures and args.tick is None and args.around is None:
        blocks = [_format_reset(r) for r in document.resets if r.diagnostic is not None]
        blocks += [
            _format_decision(r)
            for r in document.decisions
            if r.diagnostic is not None and (args.agent is None or r.agent_id == args.agent)
        ]
        if not blocks:
            print("no failures recorded")
        else:
            print("\n\n".join(blocks))
        return 0

    records = _filtered_decisions(
        document,
        tick=args.tick,
        around=args.around,
        window=args.window,
        agent=args.agent,
        failures_only=args.failures,
    )
    if not records:
        print("no matching decisions")
        return 0
    print("\n\n".join(_format_decision(r) for r in records))
    return 0


def _diverge_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bytefray agents diverge",
        description=(
            "Compare two bytefray.agent_trace files of the same schema version and "
            "report the first decision (schema 1) or callback (schema 2) at which "
            "they disagree. Executes no agent code."
        ),
    )
    parser.add_argument("run_a", help="first run directory or trace path")
    parser.add_argument("run_b", help="second run directory or trace path")
    return parser


def _print_divergence(divergence: Divergence) -> None:
    print(f"tick: {divergence.tick}")
    print(f"agent: {divergence.agent_id}")
    print(f"reason: {divergence.reason}")
    if divergence.record_a is not None:
        print("--- trace a ---")
        print(_format_decision(divergence.record_a))
    else:
        print("--- trace a: no decision at this key ---")
    if divergence.record_b is not None:
        print("--- trace b ---")
        print(_format_decision(divergence.record_b))
    else:
        print("--- trace b: no decision at this key ---")


def _describe_key(key: CallbackKey | None, trace: str, count: int) -> str:
    if key is None:
        return f"none (trace {trace} ends after {count} callbacks)"
    return (
        f"tick={key.tick} agent={key.agent_id} process={key.process_id} "
        f"callback={key.occurrence}"
    )


def _print_divergence_v2(
    document_a: TraceDocumentV2, document_b: TraceDocumentV2, divergence: DivergenceV2
) -> None:
    print("status: diverged")
    print(f"trace_a: {document_a.path}")
    print(f"trace_b: {document_b.path}")
    print(f"position: {divergence.position}")
    print(f"callback_a: {_describe_key(divergence.key_a, 'a', len(document_a.decisions))}")
    print(f"callback_b: {_describe_key(divergence.key_b, 'b', len(document_b.decisions))}")
    print(f"reason: {divergence.reason}")
    if divergence.record_a is not None:
        print("--- trace a ---")
        print(_format_decision_v2(divergence.record_a, divergence.key_a))
    else:
        print("--- trace a: no callback at this position ---")
    if divergence.record_b is not None:
        print("--- trace b ---")
        print(_format_decision_v2(divergence.record_b, divergence.key_b))
    else:
        print("--- trace b: no callback at this position ---")


def _diverge_v2(document_a: TraceDocumentV2, document_b: TraceDocumentV2) -> int:
    divergence = first_divergence_v2(document_a, document_b)
    if divergence is None:
        print("status: identical")
        print(f"trace_a: {document_a.path}")
        print(f"trace_b: {document_b.path}")
        print(
            f"No divergence found: all {len(document_a.decisions)} callbacks agree "
            "in identity, order and compared content."
        )
        return 0
    _print_divergence_v2(document_a, document_b, divergence)
    return 0


def diverge_main(argv: list[str] | None = None) -> int:
    args = _diverge_parser().parse_args(argv)
    try:
        loaded_a = load_trace(args.run_a)
        loaded_b = load_trace(args.run_b)
    except TraceInspectionError as exc:
        return _print_tool_error(exc.code, exc.message)

    version_a, version_b = _schema_version(loaded_a), _schema_version(loaded_b)
    if version_a != version_b:
        return _print_tool_error(
            "trace_schema_mismatch",
            f"cannot compare a schema-{version_a} trace ({loaded_a.path}) with a "
            f"schema-{version_b} trace ({loaded_b.path}); diverge compares two traces "
            "of the same schema version",
        )
    if isinstance(loaded_a, TraceDocumentV2) and isinstance(loaded_b, TraceDocumentV2):
        return _diverge_v2(loaded_a, loaded_b)
    assert isinstance(loaded_a, TraceDocument) and isinstance(loaded_b, TraceDocument)
    document_a, document_b = loaded_a, loaded_b

    divergence = first_divergence(document_a, document_b)
    if divergence is None:
        print("status: identical")
        print(f"trace_a: {document_a.path}")
        print(f"trace_b: {document_b.path}")
        print("No divergence found: every matched decision agrees.")
        return 0

    print("status: diverged")
    print(f"trace_a: {document_a.path}")
    print(f"trace_b: {document_b.path}")
    _print_divergence(divergence)
    return 0


__all__ = [
    "DecisionView",
    "decision_views",
    "diverge_main",
    "format_reset",
    "inspect_main",
    "is_failure_v2",
    "load_trace",
    "resolve_trace_path",
    "trace_tick_range",
]
