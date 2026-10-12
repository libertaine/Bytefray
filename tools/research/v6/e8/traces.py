"""E8 traces: capture, binding, storage and the callback rows (phase I8-5).

docs/research/v6/V6_E8_ACTIVE_SPATIAL_SENSING_PREREGISTRATION.md (PR8) Sec 10
and D8-12; implementation plan Sec 6. **The analysis reads sensing facts only
from the registered trace fields** (PR8 Sec 10), so every one of the 16,896
cells needs a ``bytefray.agent_trace`` schema-2 trace.

**Capture is E6's bound re-execution** (``tools/research/v6/e6/traces.py``,
approved at E6's Checkpoint A). Evaluation cells run through
``EvaluationService``, whose cells are untraced by identity. The trace pass
re-executes each completed cell through the same ``agent_test.test_agent``
call ``execute_cell`` makes, with ``trace=True`` and a scratch run directory,
and accepts the trace only if the run reproduces the evaluated cell: the same
replay bytes, ``match_id`` and ``result_id``. The trace's own
``BindingRecord.replay_sha256`` must equal the cell's replay digest (D8-12).
Any difference raises ``TraceBindingError``, a hard stop.

**The pre-match compatibility gate** (PR8 Sec 13) runs immediately before
every traced re-execution: ``compatibility.require_compatible`` classifies
the two packages the match will load, and refuses before the run directory
exists, so a refusal leaves no match artifact.

**Storage (plan decision P8-11, fixed here before any seed).** Every cell's
trace is kept, gzip-compressed (mtime 0, no name), and moved into place
atomically. D8-12 forbids dropping any cell's trace, so there is no retention
subset; ``size_report`` measures the projection, which is recorded.

**Line endings (plan decision P8-13, fixed here).** The engine writes traces in
text mode, so on Windows they carry CRLF. Each trace is stored with its line
endings normalized to LF, the form the replays and the I8-1 goldens use, and
``trace_sha256`` is the SHA-256 of those LF bytes. The raw form observed is
recorded. A trace carries ``wall_time_ms``, so it is never byte-reproducible:
the binding is to the replay, not to the trace bytes.

**The callback rows** (``extract``) are one fixed-width row per
``decision_v2`` record, in execution order. The three E8 fields keep their
registered presence: a field that is absent from its record is the string
``"absent"`` in the row, distinct from ``null`` (PR8 Sec 10, Revision 4).
"""

from __future__ import annotations

import gzip
import hashlib
import io
import json
import os
import shutil
import tempfile
from collections.abc import Iterable, Iterator, Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from battle_engine.agent_test import DevelopmentTestOutcome, test_agent
from battle_engine.replay import TickSnapshot, iter_replay

from tools.research.v6.e6.traces import CellRef, completed_cells, trace_path_for
from tools.research.v6.e8 import compatibility

TRACES_VERSION = 1
TRACE_INDEX_VERSION = 1
TRACE_NAME = "trace.jsonl.gz"
TRACES_DIR = "traces"
TRACE_INDEX_NAME = "trace_index.json"
ROWS_NAME = "rows.jsonl.gz"
SUMMARIES_NAME = "summaries.jsonl"
ABSENT = "absent"
TRACE_SCHEMA = "bytefray.agent_trace"
TRACE_SCHEMA_VERSION = 2
CORE_SIZE = 8

__all__ = ["CellRef", "completed_cells", "trace_path_for"]  # re-exported from E6, unchanged

#: The columns of one callback row.
ROW_FIELDS: tuple[str, ...] = (
    "tick",          # observation.current_tick
    "entrant",       # the acting entrant (its seat label)
    "process",       # the acting process
    "index",         # the entrant's callback index within the tick, from 1
    "anchor",        # observation.self_anchor
    "reach",         # observation.self_reach
    "visible",       # observation.visible_enemy_anchor_addresses
    "applied_prev",  # observation.previous_action_applied
    "read_value_prev",  # observation.previous_read_value
    "read_owner_prev",  # observation.previous_read_owner
    "delivered",     # observation.previous_sense_anchors: a list, null, or "absent"
    "kind",          # action.kind, or null when the record carries no action
    "operand",
    "value",
    "status",        # applied_result.status, or null when the record carries no result
    "address",       # applied_result.normalized_address
    "read_value",
    "read_owner",
    "sensed",        # applied_result.sensed_anchors: a list, null, or "absent"
)
COLUMN: Mapping[str, int] = {name: index for index, name in enumerate(ROW_FIELDS)}


class TraceBindingError(RuntimeError):
    """A traced re-execution did not reproduce its evaluation cell, or a trace is not bound to it."""


class TraceFormatError(RuntimeError):
    """A trace cannot be reduced to rows consistently."""


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def line_endings(data: bytes) -> str:
    crlf = data.count(b"\r\n")
    lf = data.count(b"\n")
    if crlf == 0:
        return "LF"
    return "CRLF" if crlf == lf else "mixed"


def _gzip_bytes(data: bytes, *, level: int = 6) -> bytes:
    buffer = io.BytesIO()
    with gzip.GzipFile(filename="", mode="wb", fileobj=buffer, mtime=0, compresslevel=level) as packed:
        packed.write(data)
    return buffer.getvalue()


def write_atomically(target: Path, data: bytes) -> int:
    """Write ``data`` to ``target`` via a temporary file in the same directory; return its size."""
    target.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{target.name}.", suffix=".tmp", dir=target.parent)
    os.close(descriptor)
    try:
        Path(temporary).write_bytes(data)
        os.replace(temporary, target)
    except BaseException:
        Path(temporary).unlink(missing_ok=True)
        raise
    return target.stat().st_size


@dataclass(frozen=True)
class StoredTrace:
    lf_sha256: str
    lf_bytes: int
    gz_bytes: int
    raw_line_endings: str


def store_trace(source: Path, target: Path) -> StoredTrace:
    """P8-13: normalize the line endings to LF, then store gzip-compressed and atomically."""
    raw = source.read_bytes()
    normalized = raw.replace(b"\r\n", b"\n")
    gz_bytes = write_atomically(target, _gzip_bytes(normalized))
    return StoredTrace(hashlib.sha256(normalized).hexdigest(), len(normalized), gz_bytes, line_endings(raw))


@dataclass(frozen=True)
class TraceRecord:
    schedule_id: str
    request: str
    artifact: str
    seed: int
    seat_a: str
    seat_b: str
    ruleset_id: str
    replay: str  # the evaluated cell's replay, relative to the field root (POSIX)
    replay_sha256: str
    match_id: str
    result_id: str
    trace_sha256: str  # over the stored, LF-normalized bytes
    trace_bytes: int
    gz_bytes: int
    raw_line_endings: str


def iter_trace(path: Path) -> Iterator[dict[str, Any]]:
    """The records of one (gzip-compressed) trace, in file order."""
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as handle:  # type: ignore[operator]
        for line in handle:
            if line.strip():
                yield json.loads(line)


def binding_of(records: Iterable[Mapping[str, Any]]) -> Mapping[str, Any]:
    found = [record for record in records if record.get("record_type") == "binding"]
    if len(found) != 1:
        raise TraceBindingError(f"a trace needs exactly one binding record, found {len(found)}")
    return found[0]


def trace_cell(cell: CellRef, *, field_root: Path, data_root: Path, ticks: int, arena_size: int,
               scratch: Path) -> TraceRecord:
    """Gate, re-execute one completed cell with tracing, bind the trace to it, and store it."""

    seat_a, seat_b = cell.seats
    start_a, start_b = cell.starts
    # PR8 Sec 13: refused before the match; nothing has been written yet.
    compatibility.require_compatible([data_root / "agents" / seat_a, data_root / "agents" / seat_b],
                                     cell.rules_compatibility_id)
    run_dir = scratch / f"{cell.request_dir.name}-{cell.artifact_dir.name}"
    if run_dir.exists():
        shutil.rmtree(run_dir)
    try:
        # The arguments evaluation_cell_execution.execute_cell passes for a
        # matrix cell (every override None), except trace and run_dir.
        outcome = test_agent(
            seat_a, opponent=seat_b, seed=cell.seed, ticks=ticks, timeout=None, trace=True, run_dir=run_dir,
            data_root=data_root, ruleset_id=cell.rules_compatibility_id, agent_start=start_a,
            opponent_start=start_b, arena_size=arena_size, instr_per_tick=None, locality_reach=None,
            kill_weight=None, scheduler_chunk_size=None, scheduler_rotate_start=None,
        )
        if not isinstance(outcome, DevelopmentTestOutcome) or outcome.trace_path is None:
            raise TraceBindingError(f"{cell.schedule_id}: the traced re-execution did not complete")
        result = outcome.match_result
        evaluated_sha = _sha256_file(cell.replay_path)
        mismatches = {
            name: (expected, got)
            for name, expected, got in (
                ("replay_sha256", evaluated_sha, _sha256_file(run_dir / "replay.jsonl")),
                ("match_id", cell.match_id, result.match_id),
                ("result_id", cell.result_id, result.result_id),
            )
            if expected != got
        }
        if mismatches:
            raise TraceBindingError(f"{cell.schedule_id}: traced run differs from the evaluated cell: {mismatches}")
        binding = binding_of(iter_trace(outcome.trace_path))
        if (binding.get("replay_sha256"), binding.get("match_id")) != (evaluated_sha, cell.match_id):
            raise TraceBindingError(f"{cell.schedule_id}: the trace's binding record names another match")
        stored = store_trace(outcome.trace_path, trace_path_for(field_root, cell))
        return TraceRecord(
            schedule_id=cell.schedule_id, request=cell.request_dir.name, artifact=cell.artifact_dir.name,
            seed=cell.seed, seat_a=seat_a, seat_b=seat_b, ruleset_id=cell.rules_compatibility_id,
            replay=cell.replay_path.relative_to(field_root).as_posix(), replay_sha256=evaluated_sha,
            match_id=cell.match_id, result_id=cell.result_id, trace_sha256=stored.lf_sha256,
            trace_bytes=stored.lf_bytes, gz_bytes=stored.gz_bytes, raw_line_endings=stored.raw_line_endings,
        )
    finally:
        shutil.rmtree(run_dir, ignore_errors=True)


def trace_field(field_root: Path, *, data_root: Path, ticks: int, arena_size: int,
                expected_cells: int | None = None) -> list[TraceRecord]:
    """Trace every completed cell of one condition/field, store its rows, and write the index."""

    cells = completed_cells(field_root)
    if expected_cells is not None and len(cells) != expected_cells:
        raise TraceBindingError(f"{field_root}: {len(cells)} completed cells, {expected_cells} expected")
    records: list[TraceRecord] = []
    with tempfile.TemporaryDirectory(prefix="e8-trace-") as scratch:
        for cell in cells:
            records.append(trace_cell(cell, field_root=field_root, data_root=data_root, ticks=ticks,
                                      arena_size=arena_size, scratch=Path(scratch)))
    write_index(field_root, records)
    return records


def write_index(field_root: Path, records: Sequence[TraceRecord]) -> Path:
    path = field_root / TRACES_DIR / TRACE_INDEX_NAME
    payload = {"version": TRACE_INDEX_VERSION, "records": [asdict(record) for record in records]}
    write_atomically(path, (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8"))
    return path


def read_index(field_root: Path) -> list[TraceRecord]:
    data = json.loads((field_root / TRACES_DIR / TRACE_INDEX_NAME).read_text(encoding="utf-8"))
    if data.get("version") != TRACE_INDEX_VERSION:
        raise TraceFormatError(f"unknown trace index version {data.get('version')!r}")
    return [TraceRecord(**record) for record in data["records"]]


def cell_dir(field_root: Path, record: TraceRecord) -> Path:
    return field_root / TRACES_DIR / record.request / record.artifact


def stored_trace_path(field_root: Path, record: TraceRecord) -> Path:
    return cell_dir(field_root, record) / TRACE_NAME


def size_report(records: Iterable[TraceRecord], *, matrix_cells: int) -> dict[str, Any]:
    """P8-11: the measured sizes and their projection to the whole matrix. Nothing is dropped."""
    rows = list(records)
    if not rows:
        raise ValueError("no trace records to project from")
    raw = sum(record.trace_bytes for record in rows)
    packed = sum(record.gz_bytes for record in rows)
    return {
        "cells_measured": len(rows),
        "lf_bytes": raw,
        "gz_bytes": packed,
        "max_gz_bytes": max(record.gz_bytes for record in rows),
        "compression_ratio": raw / packed if packed else None,
        "matrix_cells": matrix_cells,
        "projected_gz_bytes": packed * matrix_cells // len(rows),
        "retention": "every cell (D8-12)",
        "raw_line_endings": sorted({record.raw_line_endings for record in rows}),
    }


# ---------------------------------------------------------------------------
# The callback rows and the cell summary
# ---------------------------------------------------------------------------


def _optional(mapping: Mapping[str, Any], key: str) -> Any:
    """A presence-aware field: its value (a list or null), or ``"absent"`` if the key is missing."""
    if key not in mapping:
        return ABSENT
    value = mapping[key]
    if value is not None and not isinstance(value, list):
        raise TraceFormatError(f"{key} must be a list or null, not {value!r}")
    return value


@dataclass(frozen=True)
class TickZero:
    """The initialized state, from the replay's tick-0 snapshot."""

    core_base: Mapping[str, int]
    anchors: Mapping[str, Mapping[str, int]]


def replay_facts(replay_path: Path) -> tuple[TickZero, list[list[Any]]]:
    """The tick-0 state, and the replay's write log: every byte written, as [tick, address, owner, value],
    in execution order (the engine records each write in order and merges adjacent runs)."""
    zero: TickZero | None = None
    log: list[list[Any]] = []
    for record in iter_replay(replay_path):
        if not isinstance(record, TickSnapshot):
            continue
        if record.tick == 0:
            anchors: dict[str, dict[str, int]] = {}
            for process in record.processes:
                anchors.setdefault(process.entrant_id, {})[process.process_id] = process.anchor
            zero = TickZero({agent.agent_id: agent.pc for agent in record.agents}, anchors)
            continue
        for diff in record.memory_diffs:
            if len(diff.values) != diff.length:
                raise TraceFormatError(f"{replay_path}: a diff of length {diff.length} carries {len(diff.values)} values")
            for offset, value in enumerate(diff.values):
                log.append([record.tick, diff.address + offset, diff.owner, value])
    if zero is None:
        raise TraceFormatError(f"{replay_path}: no tick-0 snapshot")
    return zero, log


def write_log_digest(log: Sequence[Sequence[Any]]) -> str:
    return hashlib.sha256(json.dumps([list(item) for item in log], separators=(",", ":")).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class Extraction:
    rows: list[list[Any]]
    summary: dict[str, Any]


def extract(records: Iterable[Mapping[str, Any]], *, arena: int, start: TickZero,
            replay_log: Sequence[Sequence[Any]]) -> Extraction:
    """Reduce one trace's records to callback rows and a cell summary (no outcome is read)."""

    rows: list[list[Any]] = []
    header: Mapping[str, Any] | None = None
    bindings: list[Mapping[str, Any]] = []
    declarations: dict[str, list[list[Any]]] = {}
    resets: dict[str, list[Any]] = {}
    other_types: list[str] = []
    tick_of: dict[str, int] = {}
    index_of: dict[str, int] = {}
    for record in records:
        kind = record.get("record_type")
        if kind == "header":
            header = record
        elif kind == "binding":
            bindings.append(record)
        elif kind == "declaration":
            declarations.setdefault(record["agent_id"], []).append(
                [record["process_id"], record["reach"], record["share"]])
        elif kind == "reset":
            resets.setdefault(record["agent_id"], []).append(record.get("sensing_window", ABSENT))
        elif kind == "decision_v2":
            observation = record["observation"]
            entrant = record["agent_id"]
            tick = observation["current_tick"]
            if start.core_base.get(entrant) != observation["own_core_base"]:
                raise TraceFormatError(f"{entrant}: observed own_core_base {observation['own_core_base']}, "
                                       f"replay core base {start.core_base.get(entrant)}")
            if tick_of.get(entrant) != tick:
                tick_of[entrant], index_of[entrant] = tick, 0
            index_of[entrant] += 1
            action = record.get("action")
            result = record.get("applied_result")
            rows.append([
                tick, entrant, record["process_id"], index_of[entrant], observation["self_anchor"],
                observation["self_reach"], list(observation["visible_enemy_anchor_addresses"]),
                observation["previous_action_applied"], observation["previous_read_value"],
                observation["previous_read_owner"], _optional(observation, "previous_sense_anchors"),
                None if action is None else action.get("kind"), None if action is None else action.get("operand"),
                None if action is None else action.get("value"), None if result is None else result.get("status"),
                None if result is None else result.get("normalized_address"),
                None if result is None else result.get("read_value"),
                None if result is None else result.get("read_owner"),
                ABSENT if result is None else _optional(result, "sensed_anchors"),
            ])
        else:
            other_types.append(str(kind))
    if header is None:
        raise TraceFormatError("trace has no header record")
    if (header.get("schema"), header.get("schema_version")) != (TRACE_SCHEMA, TRACE_SCHEMA_VERSION):
        raise TraceFormatError(f"not a {TRACE_SCHEMA} schema-{TRACE_SCHEMA_VERSION} trace")
    entrants = sorted(start.core_base)
    summary = {
        "traces_version": TRACES_VERSION,
        "arena": arena,
        "agents": dict(header.get("agents") or {}),
        "bindings": [{"match_id": b.get("match_id"), "replay_sha256": b.get("replay_sha256"),
                      "ruleset_id": b.get("ruleset_id")} for b in bindings],
        "other_record_types": other_types,
        "callbacks": len(rows),
        "core_base": {e: start.core_base[e] for e in entrants},
        "tick0_anchors": {e: dict(sorted(start.anchors.get(e, {}).items())) for e in entrants},
        "declarations": {e: [list(item) for item in declarations.get(e, ())] for e in entrants},
        "reset_windows": {e: resets.get(e, []) for e in entrants},
        "replay_writes": len(replay_log),
        "replay_write_log_sha256": write_log_digest(replay_log),
    }
    return Extraction(rows=rows, summary=summary)


def trace_write_log(rows: Sequence[Sequence[Any]]) -> list[list[Any]]:
    """The traced applied WRITEs as a byte write log, [tick, address, entrant, value & 0xFF], in order."""
    c = COLUMN
    return [[row[c["tick"]], row[c["address"]], row[c["entrant"]], (row[c["value"]] or 0) & 0xFF]
            for row in rows if row[c["kind"]] == "write" and row[c["status"]] == "APPLIED"]


def rows_bytes(rows: Sequence[Sequence[Any]]) -> bytes:
    """The canonical uncompressed form of a cell's rows (one JSON list per line, LF)."""
    return b"".join(json.dumps(list(row), separators=(",", ":")).encode("utf-8") + b"\n" for row in rows)


def rows_cell(field_root: Path, record: TraceRecord, *, arena: int) -> dict[str, Any]:
    """Extract one cell's rows and summary from its stored trace and replay; store the rows."""

    directory = cell_dir(field_root, record)
    start, replay_log = replay_facts(field_root / record.replay)
    extraction = extract(iter_trace(directory / TRACE_NAME), arena=arena, start=start, replay_log=replay_log)
    bound = extraction.summary["bindings"]
    if bound != [{"match_id": record.match_id, "replay_sha256": record.replay_sha256,
                  "ruleset_id": record.ruleset_id}]:
        raise TraceBindingError(f"{record.schedule_id}: the trace's binding record {bound} differs from its cell")
    data = rows_bytes(extraction.rows)
    write_atomically(directory / ROWS_NAME, _gzip_bytes(data, level=9))
    return {
        "schedule_id": record.schedule_id,
        "seed": record.seed,
        "seat_a": record.seat_a,
        "seat_b": record.seat_b,
        "match_id": record.match_id,
        "rows_sha256": hashlib.sha256(data).hexdigest(),
        "summary": extraction.summary,
    }


def rows_field(field_root: Path, records: Sequence[TraceRecord], *, arena: int) -> Path:
    """Rows for every traced cell of one field, and the field's summaries file."""
    lines = sorted((rows_cell(field_root, record, arena=arena) for record in records),
                   key=lambda line: line["schedule_id"])
    path = field_root / TRACES_DIR / SUMMARIES_NAME
    write_atomically(path, b"".join(json.dumps(line, sort_keys=True, separators=(",", ":")).encode("utf-8") + b"\n"
                                    for line in lines))
    return path


def read_summaries(field_root: Path) -> list[dict[str, Any]]:
    path = field_root / TRACES_DIR / SUMMARIES_NAME
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def read_rows(field_root: Path, record: TraceRecord) -> list[list[Any]]:
    data = gzip.decompress((cell_dir(field_root, record) / ROWS_NAME).read_bytes())
    return [json.loads(line) for line in data.decode("utf-8").splitlines() if line]


def in_core(address: int, base: int, arena: int) -> bool:
    return (address - base) % arena < CORE_SIZE
