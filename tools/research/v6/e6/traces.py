"""E6 trace capture: callback-level traces for every matrix cell (I-4).

docs/research/v6/V6_E6_PRICED_SENSING_PREREGISTRATION.md Sec 6.6 and design
review condition C-4 require callback-level telemetry for every control and
treatment cell. Implementation plan Sec 6.1 said the runner would set
``MatchRequest.trace_path`` for each cell, but evaluation cells run through
``EvaluationService`` -> ``evaluation_cell_execution.execute_cell`` ->
``agent_test.test_agent(trace=False)``. ``trace=False`` is fixed there, and
``tracing: "untraced"`` is part of every evaluation's identity, so no
evaluation request can ask for a trace.

The tooling-only route taken instead, which touches no engine file:

1. The matrix runs through the unchanged ``EvaluationService`` path, exactly
   as E2-E5 did.
2. The trace pass re-executes each completed cell through the same
   ``agent_test.test_agent`` call, with the same arguments that
   ``execute_cell`` passes, except ``trace=True`` and a scratch ``run_dir``.
3. It accepts the trace only if that run reproduces the evaluation cell
   exactly: the same replay bytes (SHA-256), ``match_id`` and ``result_id``.
   Any difference raises ``TraceBindingError``, a hard stop.

The traced run is therefore provably the evaluated match, and tracing is
known not to perturb a match (the I-0 recording checked traced against
untraced runs byte for byte).

Traces carry ``wall_time_ms``, so they are never byte-reproducible (plan
Sec 6.2); the binding is to the replay, not to the trace bytes. Each trace
is gzip-compressed (mtime 0, no name) and moved into place atomically.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import os
import shutil
import tempfile
from collections.abc import Iterable, Iterator, Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from battle_engine.agent_test import DevelopmentTestOutcome, test_agent
from battle_engine.evaluation_contracts import ORIENTATION_OPPONENT_FIRST

TRACE_NAME = "trace.jsonl.gz"
TRACES_DIR = "traces"
TRACE_INDEX_NAME = "trace_index.json"
TRACE_INDEX_VERSION = 1

#: Plan Sec 6.3: if the projected compressed total for the whole matrix is
#: above this, raw traces are kept only for the registered subset.
TRACE_RETENTION_LIMIT_BYTES = 40 * 10**9
#: The registered subset: cells whose seed sits at positions 1-4 of the
#: ordered seed list.
SUBSET_SEED_POSITIONS = (1, 2, 3, 4)


class TraceBindingError(RuntimeError):
    """A traced re-execution did not reproduce its evaluation cell."""


@dataclass(frozen=True)
class CellRef:
    """One completed evaluation cell, as its ``evaluation.json`` records it."""

    request_dir: Path
    schedule_id: str
    subject_id: str
    opponent_id: str
    orientation: str
    seed: int
    subject_start: int
    opponent_start: int
    rules_compatibility_id: str
    artifact_dir: Path
    match_id: str
    result_id: str

    @property
    def seats(self) -> tuple[str, str]:
        """(seat A package, seat B package)."""
        if self.orientation == ORIENTATION_OPPONENT_FIRST:
            return self.opponent_id, self.subject_id
        return self.subject_id, self.opponent_id

    @property
    def starts(self) -> tuple[int, int]:
        """(seat A start, seat B start)."""
        if self.orientation == ORIENTATION_OPPONENT_FIRST:
            return self.opponent_start, self.subject_start
        return self.subject_start, self.opponent_start

    @property
    def replay_path(self) -> Path:
        return self.artifact_dir / "replay.jsonl"


def _relative(path_text: str) -> Path:
    # evaluation.json stores artifact_dir with the writing platform's separator.
    return Path(*path_text.replace("\\", "/").split("/"))


def completed_cells(field_root: Path) -> list[CellRef]:
    """Every completed cell of one condition/field run, in request then matrix order."""

    cells: list[CellRef] = []
    for state in sorted(field_root.glob("arena_*/*/evaluation.json")):
        request_dir = state.parent
        data = json.loads(state.read_text(encoding="utf-8"))
        for cell in data["cells"]:
            if cell["status"] != "completed":
                continue
            cells.append(CellRef(
                request_dir=request_dir,
                schedule_id=cell["schedule_id"],
                subject_id=cell["subject_id"],
                opponent_id=cell["opponent_id"],
                orientation=cell["orientation"],
                seed=int(cell["seed"]),
                subject_start=int(cell["subject_start"]),
                opponent_start=int(cell["opponent_start"]),
                rules_compatibility_id=cell["rules_compatibility_id"],
                artifact_dir=request_dir / _relative(cell["artifact_dir"]),
                match_id=cell["match_id"],
                result_id=cell["result_id"],
            ))
    return cells


def trace_path_for(field_root: Path, cell: CellRef) -> Path:
    """Where a cell's trace lives: a tree parallel to the evaluation artifacts."""
    return field_root / TRACES_DIR / cell.request_dir.name / cell.artifact_dir.name / TRACE_NAME


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def gzip_atomically(source: Path, target: Path) -> int:
    """Compress ``source`` into ``target`` via a temporary file; return the compressed size."""

    target.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{target.name}.", suffix=".tmp", dir=target.parent)
    os.close(descriptor)
    try:
        with (
            source.open("rb") as raw,
            open(temporary, "wb") as out,
            gzip.GzipFile(filename="", mode="wb", fileobj=out, mtime=0, compresslevel=6) as packed,
        ):
            shutil.copyfileobj(raw, packed, 1 << 20)
        os.replace(temporary, target)
    except BaseException:
        Path(temporary).unlink(missing_ok=True)
        raise
    return target.stat().st_size


@dataclass(frozen=True)
class TraceRecord:
    schedule_id: str
    request: str
    artifact: str
    seed: int
    seat_a: str
    seat_b: str
    replay: str  # the evaluated cell's replay, relative to the field root (POSIX)
    replay_sha256: str
    match_id: str
    result_id: str
    trace_sha256: str
    trace_bytes: int
    gz_bytes: int


def trace_cell(
    cell: CellRef,
    *,
    field_root: Path,
    data_root: Path,
    ticks: int,
    arena_size: int,
    scratch: Path,
) -> TraceRecord:
    """Re-execute one completed cell with tracing and bind the trace to it."""

    seat_a, seat_b = cell.seats
    start_a, start_b = cell.starts
    run_dir = scratch / f"{cell.request_dir.name}-{cell.artifact_dir.name}"
    if run_dir.exists():
        shutil.rmtree(run_dir)
    try:
        # The arguments evaluation_cell_execution.execute_cell passes for an
        # E6 cell (every override None), except trace and run_dir.
        outcome = test_agent(
            seat_a,
            opponent=seat_b,
            seed=cell.seed,
            ticks=ticks,
            timeout=None,
            trace=True,
            run_dir=run_dir,
            data_root=data_root,
            ruleset_id=cell.rules_compatibility_id,
            agent_start=start_a,
            opponent_start=start_b,
            arena_size=arena_size,
            instr_per_tick=None,
            locality_reach=None,
            kill_weight=None,
            scheduler_chunk_size=None,
            scheduler_rotate_start=None,
        )
        if not isinstance(outcome, DevelopmentTestOutcome) or outcome.trace_path is None:
            raise TraceBindingError(f"{cell.schedule_id}: the traced re-execution did not complete")
        result = outcome.match_result
        evaluated_sha = _sha256_file(cell.replay_path)
        traced_sha = _sha256_file(run_dir / "replay.jsonl")
        mismatches = {
            name: (expected, got)
            for name, expected, got in (
                ("replay_sha256", evaluated_sha, traced_sha),
                ("match_id", cell.match_id, result.match_id),
                ("result_id", cell.result_id, result.result_id),
            )
            if expected != got
        }
        if mismatches:
            raise TraceBindingError(f"{cell.schedule_id}: traced run differs from the evaluated cell: {mismatches}")
        target = trace_path_for(field_root, cell)
        trace_sha = _sha256_file(outcome.trace_path)
        trace_bytes = outcome.trace_path.stat().st_size
        gz_bytes = gzip_atomically(outcome.trace_path, target)
        return TraceRecord(
            schedule_id=cell.schedule_id,
            request=cell.request_dir.name,
            artifact=cell.artifact_dir.name,
            seed=cell.seed,
            seat_a=seat_a,
            seat_b=seat_b,
            replay=cell.replay_path.relative_to(field_root).as_posix(),
            replay_sha256=evaluated_sha,
            match_id=cell.match_id,
            result_id=cell.result_id,
            trace_sha256=trace_sha,
            trace_bytes=trace_bytes,
            gz_bytes=gz_bytes,
        )
    finally:
        shutil.rmtree(run_dir, ignore_errors=True)


def trace_field(
    field_root: Path,
    *,
    data_root: Path,
    ticks: int,
    arena_size: int,
    expected_cells: int | None = None,
) -> list[TraceRecord]:
    """Trace every completed cell of one condition/field and write the index."""

    cells = completed_cells(field_root)
    if expected_cells is not None and len(cells) != expected_cells:
        raise TraceBindingError(f"{field_root}: {len(cells)} completed cells, {expected_cells} expected")
    records: list[TraceRecord] = []
    with tempfile.TemporaryDirectory(prefix="e6-trace-") as scratch:
        for cell in cells:
            records.append(trace_cell(cell, field_root=field_root, data_root=data_root, ticks=ticks,
                                      arena_size=arena_size, scratch=Path(scratch)))
    write_index(field_root, records)
    return records


def write_index(field_root: Path, records: Sequence[TraceRecord]) -> Path:
    path = field_root / TRACES_DIR / TRACE_INDEX_NAME
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"version": TRACE_INDEX_VERSION, "records": [asdict(record) for record in records]}
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def read_index(field_root: Path) -> list[TraceRecord]:
    data = json.loads((field_root / TRACES_DIR / TRACE_INDEX_NAME).read_text(encoding="utf-8"))
    if data.get("version") != TRACE_INDEX_VERSION:
        raise ValueError(f"unknown trace index version {data.get('version')!r}")
    return [TraceRecord(**record) for record in data["records"]]


def iter_trace(path: Path) -> Iterator[dict[str, Any]]:
    """The records of one (gzip-compressed) trace, in file order."""

    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as handle:  # type: ignore[operator]
        for line in handle:
            if line.strip():
                yield json.loads(line)


# ---------------------------------------------------------------------------
# Size accounting and the retention rule (plan Sec 6.3), fixed before any data
# ---------------------------------------------------------------------------


def size_report(records: Iterable[TraceRecord], *, matrix_cells: int) -> dict[str, Any]:
    """Measured sizes and the projection to the whole matrix."""

    rows = list(records)
    if not rows:
        raise ValueError("no trace records to project from")
    raw = sum(record.trace_bytes for record in rows)
    packed = sum(record.gz_bytes for record in rows)
    projected = packed * matrix_cells // len(rows)
    return {
        "cells_measured": len(rows),
        "raw_bytes": raw,
        "gz_bytes": packed,
        "mean_raw_bytes": raw / len(rows),
        "mean_gz_bytes": packed / len(rows),
        "compression_ratio": raw / packed if packed else None,
        "matrix_cells": matrix_cells,
        "projected_gz_bytes": projected,
        "limit_bytes": TRACE_RETENTION_LIMIT_BYTES,
        "retention": retention_rule(projected),
    }


def retention_rule(projected_gz_bytes: int) -> str:
    """``"all"`` keeps every raw trace; ``"subset"`` keeps only seed positions 1-4."""
    return "subset" if projected_gz_bytes > TRACE_RETENTION_LIMIT_BYTES else "all"


def retained(seed: int, ordered_seeds: Sequence[int], rule: str) -> bool:
    """Whether a cell's raw trace is kept under ``rule`` (its compact telemetry always is)."""

    if rule == "all":
        return True
    if rule != "subset":
        raise ValueError(f"unknown retention rule {rule!r}")
    positions = {value: index for index, value in enumerate(ordered_seeds, start=1)}
    return positions[seed] in SUBSET_SEED_POSITIONS


def apply_retention(field_root: Path, records: Sequence[TraceRecord], ordered_seeds: Sequence[int],
                    rule: str) -> list[str]:
    """Delete the raw traces ``rule`` does not keep; return the deleted cells' schedule IDs."""

    removed: list[str] = []
    for record in records:
        if retained(record.seed, ordered_seeds, rule):
            continue
        path = field_root / TRACES_DIR / record.request / record.artifact / TRACE_NAME
        if path.exists():
            path.unlink()
            removed.append(record.schedule_id)
    return removed


def records_by_schedule(records: Iterable[TraceRecord]) -> Mapping[str, TraceRecord]:
    table: dict[str, TraceRecord] = {}
    for record in records:
        if record.schedule_id in table:
            raise ValueError(f"duplicate trace record {record.schedule_id}")
        table[record.schedule_id] = record
    return table
