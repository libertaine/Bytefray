"""Per-cell E4 telemetry for a whole condition/field corpus.

For every cell of one harness run, computes the E3 telemetry with
``action_parity.analyze_actions`` (which runs capture analyzer v2), unchanged,
and the E4 metrics with ``cell_metrics.cell_metrics``, which is cross-checked
against it. A row is ``{"key", "telemetry": {"e3": ..., "e4": ...}}`` or
``{"key", "error"}``: an analyzer failure is recorded, never skipped. Rows are
written as JSONL (one header line, then one row per cell, sorted) so the gates
and the analysis read one computed instrument output; ``row_digests`` gives a
location-independent digest per cell for repeatability checks.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from collections.abc import Mapping
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any

from tools.research.v6.e2.capture_analyzer import CAPTURE_ANALYZER_VERSION
from tools.research.v6.e3.action_parity import E3_ACTION_PARITY_VERSION, analyze_actions
from tools.research.v6.e3.gates import artifact_dir, comparable_telemetry, index_cells, load_cells
from tools.research.v6.e4 import matrix
from tools.research.v6.e4.cell_metrics import DECIDED_EARLY, E4_CELL_METRICS_VERSION, cell_metrics

TELEMETRY_SCHEMA = "bytefray.v6.e4.telemetry"
TELEMETRY_FILE_VERSION = 1

Rows = dict[str, dict[str, Any]]


def analyze_cell(directory: Path) -> dict[str, Any]:
    """The E3 and E4 telemetry of one cell directory (``replay.jsonl`` + ``result.json``)."""
    e3 = analyze_actions(
        directory / "replay.jsonl", directory / "result.json", names_inferring_core=matrix.CORE_INFERRING_AGENTS
    )
    return {"e3": e3, "e4": cell_metrics(directory / "replay.jsonl", e3)}


def _analyze(job: tuple[str, str]) -> dict[str, Any]:
    key, directory = job
    try:
        return {"key": key, "telemetry": analyze_cell(Path(directory))}
    except Exception as exc:
        return {"key": key, "error": f"{type(exc).__name__}: {exc}"}


def compute_telemetry(root: Path, *, workers: int = 1, keys: set[str] | None = None) -> Rows:
    """Telemetry rows for every cell of one harness run (or the given subset), by cell identity."""
    cells = index_cells(load_cells(root))
    jobs = [(key, str(artifact_dir(root, cell))) for key, cell in sorted(cells.items()) if keys is None or key in keys]
    if workers <= 1:
        rows = [_analyze(job) for job in jobs]
    else:
        with ProcessPoolExecutor(max_workers=workers) as pool:
            rows = list(pool.map(_analyze, jobs, chunksize=16))
    return {row["key"]: row for row in rows}


def row_digest(row: Mapping[str, Any]) -> str:
    """Location-independent digest of one row (an error row digests its message)."""
    telemetry = row.get("telemetry")
    if telemetry is None:
        return f"error:{row.get('error')}"
    canonical = json.dumps({"e3": comparable_telemetry(telemetry["e3"]), "e4": telemetry["e4"]},
                           sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def row_digests(rows: Mapping[str, Mapping[str, Any]]) -> dict[str, str]:
    return {key: row_digest(row) for key, row in rows.items()}


def summarize(rows: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    """Qualification counts over one corpus's rows."""
    counts: Counter[str] = Counter()
    fma: Counter[str] = Counter()
    fps: Counter[str] = Counter()
    parity: Counter[str] = Counter()
    failures = []
    for key, row in sorted(rows.items()):
        telemetry = row.get("telemetry")
        if telemetry is None:
            counts["analyzer_failures"] += 1
            failures.append({"cell": key, "error": row.get("error")})
            continue
        e3, e4 = telemetry["e3"], telemetry["e4"]
        checks = e3["checks"]
        counts["analyzed"] += 1
        counts["cpu_statistics_mismatches"] += 0 if checks["cpu_statistics_match"] else 1
        counts["ownership_reconstruction_disagreements"] += 0 if checks["capture_reconstruction_agrees"] else 1
        counts["capture_engine_disagreements"] += 0 if checks["capture_consistent_with_engine"] else 1
        counts["capture_attribution_mismatches"] += 0 if checks["capture_attribution_ok"] else 1
        counts["e4_reconstruction_disagreements"] += 0 if e4["checks"]["reconstruction_agrees"] else 1
        counts["e4_fps_identity_failures"] += 0 if e4["checks"]["fps_identity_holds"] else 1
        counts["e4_check_failures"] += 0 if e4["checks"]["ok"] else 1
        counts["exposed_cells"] += 1 if e3["exposed"] else 0
        counts["completions"] += len(e3["completions"])
        counts["zero_action_live_ticks"] += sum(seat["zero_action_live_ticks"] for seat in e3["seats"].values())
        counts["exclusive_ticks"] += e3["exclusive_ticks"]
        counts["decided_early_cells"] += 1 if e4["fma"]["status"] == DECIDED_EARLY else 0
        counts["static_defined_cells"] += 1 if e4["fma"]["status"] != DECIDED_EARLY and e4["swing_ticks"] == 0 else 0
        fma[str(e4["fma"]["band"] or e4["fma"]["status"])] += 1
        fps[e4["fps"]["status"]] += 1
        parity[e3["parity"]["status"]] += 1
    return {
        "cells": len(rows),
        **{name: counts[name] for name in (
            "analyzed", "analyzer_failures", "cpu_statistics_mismatches", "ownership_reconstruction_disagreements",
            "capture_engine_disagreements", "capture_attribution_mismatches", "e4_reconstruction_disagreements",
            "e4_fps_identity_failures", "e4_check_failures", "exposed_cells", "completions",
            "zero_action_live_ticks", "exclusive_ticks", "decided_early_cells", "static_defined_cells")},
        "fma_bands": dict(sorted(fma.items())),
        "fps_status": dict(sorted(fps.items())),
        "parity_status": dict(sorted(parity.items())),
        "failure_samples": failures[:10],
        "clean": all(counts[name] == 0 for name in (
            "analyzer_failures", "cpu_statistics_mismatches", "ownership_reconstruction_disagreements",
            "capture_engine_disagreements", "capture_attribution_mismatches", "e4_check_failures")),
    }


def write_rows(path: Path, rows: Mapping[str, Mapping[str, Any]], *, corpus: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    header = {
        "schema": TELEMETRY_SCHEMA,
        "version": TELEMETRY_FILE_VERSION,
        "e3_action_parity_version": E3_ACTION_PARITY_VERSION,
        "capture_analyzer_version": CAPTURE_ANALYZER_VERSION,
        "e4_cell_metrics_version": E4_CELL_METRICS_VERSION,
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
            raise ValueError(f"{path}: not an E4 telemetry file")
        versions = (header.get("e3_action_parity_version"), header.get("capture_analyzer_version"),
                    header.get("e4_cell_metrics_version"))
        if versions != (E3_ACTION_PARITY_VERSION, CAPTURE_ANALYZER_VERSION, E4_CELL_METRICS_VERSION):
            raise ValueError(f"{path}: written by another analyzer version {versions}")
        rows = {}
        for raw in handle:
            if raw.strip():
                row = json.loads(raw)
                rows[row["key"]] = row
    if len(rows) != header.get("cells"):
        raise ValueError(f"{path}: {len(rows)} rows, header says {header.get('cells')}")
    return header, rows
