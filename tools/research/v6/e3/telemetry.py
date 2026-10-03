"""Per-cell E3 telemetry for a whole condition/field corpus.

Runs ``action_parity.analyze_actions`` (which runs capture analyzer v2) over
every cell of one harness run, in a process pool, and keeps the rows by cell
identity. A row is ``{"key", "telemetry"}`` or ``{"key", "error"}``: an
analyzer failure is recorded, never skipped. Rows can be written to a JSONL
file (one header line, then one row per cell, sorted) so the gates and the
analysis read one computed instrument output; ``row_digests`` gives a
location-independent digest per cell for repeatability checks.
"""

from __future__ import annotations

import json
from collections import Counter
from collections.abc import Mapping
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any

from tools.research.v6.e2.capture_analyzer import CAPTURE_ANALYZER_VERSION
from tools.research.v6.e3 import matrix
from tools.research.v6.e3.action_parity import E3_ACTION_PARITY_VERSION, analyze_actions
from tools.research.v6.e3.gates import artifact_dir, index_cells, load_cells, telemetry_digest

TELEMETRY_SCHEMA = "bytefray.v6.e3.telemetry"
TELEMETRY_FILE_VERSION = 1

Rows = dict[str, dict[str, Any]]


def _analyze(job: tuple[str, str]) -> dict[str, Any]:
    key, directory = job
    try:
        telemetry = analyze_actions(
            Path(directory) / "replay.jsonl",
            Path(directory) / "result.json",
            names_inferring_core=matrix.CORE_INFERRING_AGENTS,
        )
    except Exception as exc:
        return {"key": key, "error": f"{type(exc).__name__}: {exc}"}
    return {"key": key, "telemetry": telemetry}


def compute_telemetry(root: Path, *, workers: int = 1) -> Rows:
    """Telemetry rows for every cell of one harness run, by cell identity."""
    cells = index_cells(load_cells(root))
    jobs = [(key, str(artifact_dir(root, cell))) for key, cell in sorted(cells.items())]
    if workers <= 1:
        rows = [_analyze(job) for job in jobs]
    else:
        with ProcessPoolExecutor(max_workers=workers) as pool:
            rows = list(pool.map(_analyze, jobs, chunksize=16))
    return {row["key"]: row for row in rows}


def row_digests(rows: Mapping[str, Mapping[str, Any]]) -> dict[str, str]:
    """A location-independent digest of each row (an error row digests its message)."""
    return {
        key: telemetry_digest(row["telemetry"]) if "telemetry" in row else f"error:{row.get('error')}"
        for key, row in rows.items()
    }


def summarize(rows: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    """Qualification counts over one corpus's rows."""
    counts: Counter[str] = Counter()
    categories: Counter[str] = Counter()
    parity: Counter[str] = Counter()
    failures = []
    for key, row in sorted(rows.items()):
        telemetry = row.get("telemetry")
        if telemetry is None:
            counts["analyzer_failures"] += 1
            failures.append({"cell": key, "error": row.get("error")})
            continue
        checks = telemetry["checks"]
        counts["analyzed"] += 1
        counts["cpu_statistics_mismatches"] += 0 if checks["cpu_statistics_match"] else 1
        counts["ownership_reconstruction_disagreements"] += 0 if checks["capture_reconstruction_agrees"] else 1
        counts["capture_engine_disagreements"] += 0 if checks["capture_consistent_with_engine"] else 1
        counts["capture_attribution_mismatches"] += 0 if checks["capture_attribution_ok"] else 1
        counts["exposed_cells"] += 1 if telemetry["exposed"] else 0
        counts["hit_free_cells"] += 1 if telemetry["first_hit_tick"] is None else 0
        counts["completions"] += len(telemetry["completions"])
        parity[telemetry["parity"]["status"]] += 1
        for seat in telemetry["seats"].values():
            categories[seat["phase_lock"]["category"]] += 1
            counts["zero_action_live_ticks"] += seat["zero_action_live_ticks"]
            counts["g4_violations"] += seat["g4_violations"]
        counts["exclusive_ticks"] += telemetry["exclusive_ticks"]
        counts["both_alive_ticks"] += telemetry["both_alive_ticks"]
    return {
        "cells": len(rows),
        **{name: counts[name] for name in (
            "analyzed", "analyzer_failures", "cpu_statistics_mismatches", "ownership_reconstruction_disagreements",
            "capture_engine_disagreements", "capture_attribution_mismatches", "exposed_cells", "hit_free_cells",
            "completions", "zero_action_live_ticks", "g4_violations", "exclusive_ticks", "both_alive_ticks")},
        "phase_lock_categories": dict(sorted(categories.items())),
        "parity_status": dict(sorted(parity.items())),
        "failure_samples": failures[:10],
        "clean": counts["analyzer_failures"] == 0
        and counts["cpu_statistics_mismatches"] == 0
        and counts["ownership_reconstruction_disagreements"] == 0
        and counts["capture_engine_disagreements"] == 0
        and counts["capture_attribution_mismatches"] == 0,
    }


def write_rows(path: Path, rows: Mapping[str, Mapping[str, Any]], *, corpus: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    header = {
        "schema": TELEMETRY_SCHEMA,
        "version": TELEMETRY_FILE_VERSION,
        "e3_action_parity_version": E3_ACTION_PARITY_VERSION,
        "capture_analyzer_version": CAPTURE_ANALYZER_VERSION,
        "corpus": dict(corpus),
        "cells": len(rows),
    }
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(header, sort_keys=True) + "\n")
        for key in sorted(rows):
            handle.write(json.dumps(rows[key], sort_keys=True) + "\n")


def read_rows(path: Path) -> tuple[dict[str, Any], Rows]:
    with path.open("r", encoding="utf-8") as handle:
        header: dict[str, Any] = json.loads(handle.readline())
        if header.get("schema") != TELEMETRY_SCHEMA or header.get("version") != TELEMETRY_FILE_VERSION:
            raise ValueError(f"{path}: not an E3 telemetry file")
        if (header.get("e3_action_parity_version"), header.get("capture_analyzer_version")) != (
            E3_ACTION_PARITY_VERSION, CAPTURE_ANALYZER_VERSION
        ):
            raise ValueError(f"{path}: written by another analyzer version")
        rows = {}
        for raw in handle:
            if raw.strip():
                row = json.loads(raw)
                rows[row["key"]] = row
    if len(rows) != header.get("cells"):
        raise ValueError(f"{path}: {len(rows)} rows, header says {header.get('cells')}")
    return header, rows
