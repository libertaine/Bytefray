"""E6 compact telemetry: one row per callback, and a summary per cell (I-4).

docs/research/v6/V6_E6_PRICED_SENSING_IMPLEMENTATION_PLAN.md Sec 6.4. The
extractor reads a cell's trace (``traces.py``) and keeps only its
deterministic content, never ``wall_time_ms``:

* **Callback rows**, in execution order, as fixed-width lists (``ROW_FIELDS``).
  They are stored gzip-compressed for every cell, whatever happens to the
  raw trace, and are the input to D-1's independent re-derivation.
* **A cell summary**: each entrant's core base, tick-0 process anchors
  (both read from the cell's replay, since an entrant can be captured
  before its first callback) and declared processes;
  first detection (with its callback index), which entrant saw first, and
  first applied MOVE; pre-detection MOVEs, probe READs and off-core MOVEs;
  information events by tick; and D-4's inputs,
  every tick-1-2 WRITE to a cell of the opponent's core with whether its
  entrant had had an information event before it.

Definitions (pre-registration Sec 4.11 and D-4; design review Sec G.2):

* an **information event** of an entrant is a callback whose visible set
  is non-empty, or a READ of a cell of the opponent's core that returns
  the opponent as owner. A visible set counts from its own callback (the
  observation precedes the action); a READ's result counts from the next
  row;
* a **pre-detection MOVE** comes before the entrant's first non-empty
  visible set;
* a **probe READ** reads a cell outside the entrant's own core;
* an **off-core MOVE** takes the acting process's anchor from a cell of
  its own core to a cell outside it.

Every quantity is descriptive (O-DETECT) or a gate input. None is an
outcome measure.
"""

from __future__ import annotations

import gzip
import hashlib
import io
import json
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from battle_engine.replay import TickSnapshot, iter_replay

from tools.research.v6.e6.traces import (
    TRACE_NAME,
    TRACES_DIR,
    TraceRecord,
    iter_trace,
)

TELEMETRY_VERSION = 1
CALLBACKS_NAME = "callbacks.jsonl.gz"
SUMMARIES_NAME = "summaries.jsonl"
CORE_SIZE = 8
D4_TICKS = (1, 2)

#: The columns of one callback row.
ROW_FIELDS: tuple[str, ...] = (
    "tick",          # observation.current_tick
    "entrant",       # the acting entrant (its seat label)
    "process",       # the acting process
    "index",         # the entrant's callback index within the tick, from 1
    "anchor",        # the acting process's anchor before the action
    "visible",       # the visible set the observation carried
    "kind",          # read / write / move, or None if no action was returned
    "operand",
    "value",
    "status",        # APPLIED, REJECTED_OUT_OF_REACH, REJECTED_INVALID or EXCEPTION
    "address",       # the normalized address (a MOVE's new anchor)
    "read_value",
    "read_owner",
)
_COLUMN = {name: index for index, name in enumerate(ROW_FIELDS)}


class TelemetryError(RuntimeError):
    """A trace cannot be reduced to telemetry consistently."""


@dataclass(frozen=True)
class Extraction:
    rows: list[list[Any]]
    summary: dict[str, Any]


def _in_core(address: int, base: int, arena: int) -> bool:
    return (address - base) % arena < CORE_SIZE


@dataclass(frozen=True)
class TickZero:
    """The initialized state, from the replay's tick-0 snapshot."""

    core_base: Mapping[str, int]  # entrant -> core base (its recorded pc)
    anchors: Mapping[str, Mapping[str, int]]  # entrant -> process -> anchor


def tick_zero(replay_path: Path) -> TickZero:
    for record in iter_replay(replay_path):
        if isinstance(record, TickSnapshot) and record.tick == 0:
            anchors: dict[str, dict[str, int]] = {}
            for process in record.processes:
                anchors.setdefault(process.entrant_id, {})[process.process_id] = process.anchor
            return TickZero(core_base={agent.agent_id: agent.pc for agent in record.agents}, anchors=anchors)
    raise TelemetryError(f"{replay_path}: no tick-0 snapshot")


def extract(records: Iterable[Mapping[str, Any]], *, arena: int, start: TickZero) -> Extraction:
    """Reduce one trace's records to callback rows and a cell summary."""

    rows: list[list[Any]] = []
    header: Mapping[str, Any] | None = None
    binding: Mapping[str, Any] | None = None
    declarations: dict[str, list[list[Any]]] = {}
    core = dict(start.core_base)
    tick_of: dict[str, int] = {}
    index_of: dict[str, int] = {}
    for record in records:
        kind = record.get("record_type")
        if kind == "header":
            header = record
        elif kind == "binding":
            binding = record
        elif kind == "declaration":
            declarations.setdefault(record["agent_id"], []).append(
                [record["process_id"], record["reach"], record["share"]])
        elif kind == "decision_v2":
            observation = record["observation"]
            entrant = record["agent_id"]
            tick = observation["current_tick"]
            base = observation["own_core_base"]
            if core.get(entrant) != base:
                raise TelemetryError(f"{entrant}: observed own_core_base {base}, replay core base {core.get(entrant)}")
            if tick_of.get(entrant) != tick:
                tick_of[entrant] = tick
                index_of[entrant] = 0
            index_of[entrant] += 1
            action = record.get("action") or {}
            result = record.get("applied_result") or {}
            rows.append([
                tick, entrant, record["process_id"], index_of[entrant], observation["self_anchor"],
                list(observation["visible_enemy_anchor_addresses"]), action.get("kind"), action.get("operand"),
                action.get("value"), result.get("status"), result.get("normalized_address"),
                result.get("read_value"), result.get("read_owner"),
            ])
    if header is None:
        raise TelemetryError("trace has no header record")
    summary = summarize(rows, arena=arena, core=core, declarations=declarations, header=header, binding=binding)
    summary["tick0_anchors"] = {entrant: dict(sorted(start.anchors.get(entrant, {}).items()))
                                for entrant in sorted(core)}
    return Extraction(rows=rows, summary=summary)


def summarize(rows: Sequence[Sequence[Any]], *, arena: int, core: Mapping[str, int],
              declarations: Mapping[str, Sequence[Sequence[Any]]], header: Mapping[str, Any],
              binding: Mapping[str, Any] | None) -> dict[str, Any]:
    entrants = sorted(core)
    if len(entrants) != 2:
        raise TelemetryError(f"expected two entrants, found {entrants}")
    opponent = {entrants[0]: entrants[1], entrants[1]: entrants[0]}
    column = _COLUMN
    first_detection: dict[str, list[int] | None] = {e: None for e in entrants}
    first_detection_callback: dict[str, int | None] = {e: None for e in entrants}
    first_move: dict[str, list[int] | None] = {e: None for e in entrants}
    first_information: dict[str, list[int] | None] = {e: None for e in entrants}
    informed = {e: False for e in entrants}
    pre_detection_moves = Counter[str]()
    probe_reads = Counter[str]()
    off_core_moves = Counter[str]()
    information_ticks: dict[str, Counter[int]] = {e: Counter() for e in entrants}
    d4_writes: list[dict[str, Any]] = []
    for order, row in enumerate(rows):
        tick, entrant = row[column["tick"]], row[column["entrant"]]
        kind, status = row[column["kind"]], row[column["status"]]
        address = row[column["address"]]
        rival = opponent[entrant]
        if row[column["visible"]]:
            information_ticks[entrant][tick] += 1
            informed[entrant] = True
            if first_detection[entrant] is None:
                first_detection[entrant] = [tick, order]
                first_detection_callback[entrant] = row[column["index"]]
            if first_information[entrant] is None:
                first_information[entrant] = [tick, order]
        applied = status == "APPLIED"
        if kind == "move" and applied:
            if first_move[entrant] is None:
                first_move[entrant] = [tick, order]
            if first_detection[entrant] is None:
                pre_detection_moves[entrant] += 1
            if _in_core(row[column["anchor"]], core[entrant], arena) and not _in_core(address, core[entrant], arena):
                off_core_moves[entrant] += 1
        elif kind == "read" and applied:
            if not _in_core(address, core[entrant], arena):
                probe_reads[entrant] += 1
        elif kind == "write" and applied and tick in D4_TICKS and _in_core(address, core[rival], arena):
            d4_writes.append({"order": order, "tick": tick, "entrant": entrant, "address": address,
                              "informed": informed[entrant]})
        # A READ's result is information from the next row on.
        if (kind == "read" and applied and _in_core(address, core[rival], arena)
                and row[column["read_owner"]] == rival):
            information_ticks[entrant][tick] += 1
            informed[entrant] = True
            if first_information[entrant] is None:
                first_information[entrant] = [tick, order]
    detected = {e: first_detection[e] for e in entrants if first_detection[e] is not None}
    saw_first = min(detected, key=lambda e: detected[e][1]) if detected else None  # type: ignore[index]
    return {
        "telemetry_version": TELEMETRY_VERSION,
        "arena": arena,
        "agents": dict(header.get("agents") or {}),
        "binding": None if binding is None else {"match_id": binding.get("match_id"),
                                                 "replay_sha256": binding.get("replay_sha256")},
        "callbacks": len(rows),
        "core_base": {e: core[e] for e in entrants},
        "declarations": {e: [list(item) for item in declarations.get(e, ())] for e in entrants},
        "first_detection": first_detection,
        "first_detection_callback": first_detection_callback,
        "first_move": first_move,
        "first_information": first_information,
        "saw_first": saw_first,
        "pre_detection_moves": {e: pre_detection_moves[e] for e in entrants},
        "probe_reads": {e: probe_reads[e] for e in entrants},
        "off_core_moves": {e: off_core_moves[e] for e in entrants},
        "information_ticks": {e: sorted([t, n] for t, n in information_ticks[e].items()) for e in entrants},
        "d4_writes": d4_writes,
    }


# ---------------------------------------------------------------------------
# Storage
# ---------------------------------------------------------------------------


def rows_bytes(rows: Sequence[Sequence[Any]]) -> bytes:
    """The canonical uncompressed form of a cell's rows (one JSON list per line, LF)."""
    return b"".join(json.dumps(list(row), separators=(",", ":")).encode("utf-8") + b"\n" for row in rows)


def _gzip_bytes(data: bytes) -> bytes:
    buffer = io.BytesIO()
    with gzip.GzipFile(filename="", mode="wb", fileobj=buffer, mtime=0, compresslevel=9) as packed:
        packed.write(data)
    return buffer.getvalue()


def cell_dir(field_root: Path, record: TraceRecord) -> Path:
    return field_root / TRACES_DIR / record.request / record.artifact


def telemetry_cell(field_root: Path, record: TraceRecord, *, arena: int) -> dict[str, Any]:
    """Extract one cell's telemetry from its trace, store the rows, and return its summary line."""

    directory = cell_dir(field_root, record)
    extraction = extract(iter_trace(directory / TRACE_NAME), arena=arena,
                         start=tick_zero(field_root / record.replay))
    bound = extraction.summary["binding"]
    if bound != {"match_id": record.match_id, "replay_sha256": record.replay_sha256}:
        raise TelemetryError(f"{record.schedule_id}: the trace's own binding record {bound} differs from its cell")
    data = rows_bytes(extraction.rows)
    (directory / CALLBACKS_NAME).write_bytes(_gzip_bytes(data))
    return {
        "schedule_id": record.schedule_id,
        "seed": record.seed,
        "seat_a": record.seat_a,
        "seat_b": record.seat_b,
        "match_id": record.match_id,
        "rows_sha256": hashlib.sha256(data).hexdigest(),
        "summary": extraction.summary,
    }


def telemetry_field(field_root: Path, records: Sequence[TraceRecord], *, arena: int) -> Path:
    """Telemetry for every traced cell of one field, and the field's summaries file."""

    lines = [telemetry_cell(field_root, record, arena=arena) for record in records]
    lines.sort(key=lambda line: line["schedule_id"])
    path = field_root / TRACES_DIR / SUMMARIES_NAME
    path.write_bytes(b"".join(json.dumps(line, sort_keys=True, separators=(",", ":")).encode("utf-8") + b"\n"
                              for line in lines))
    return path


def read_summaries(field_root: Path) -> list[dict[str, Any]]:
    path = field_root / TRACES_DIR / SUMMARIES_NAME
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def read_callbacks(field_root: Path, record: TraceRecord) -> list[list[Any]]:
    data = gzip.decompress((cell_dir(field_root, record) / CALLBACKS_NAME).read_bytes())
    return [json.loads(line) for line in data.decode("utf-8").splitlines() if line]


def summaries_digest(field_root: Path) -> str:
    return hashlib.sha256((field_root / TRACES_DIR / SUMMARIES_NAME).read_bytes()).hexdigest()
