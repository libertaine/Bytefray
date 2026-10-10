"""Control-data requalification of the E2 analysis instrument (freeze v2).

Before any T-E2 match may run under a new analysis freeze, the preserved
C-V4 / C-RS corpus is re-checked with the new instrument -- on control data
only, so no treatment outcome can influence it:

* corpus integrity: the exact frozen cell set, every cell completed with its
  artifacts, no stray executions on disk, and provenance from the control
  source commit with a clean tree, the frozen digests and fingerprints;
* the capture analyzer on every control replay: no failure, no disagreement
  with the engine's own capture record, and every completion attributed to
  its onset capturer;
* telemetry equivalence: each C-V4 cell's telemetry equals its C-RS twin's,
  apart from the replay path and the Ruleset id.

The C-V4 / C-RS control gate itself is re-run by
``control_gate.compare_control_runs``. Reads artifacts only; executes nothing.
"""

from __future__ import annotations

import json
from collections import Counter
from collections.abc import Mapping, Sequence
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any

from tools.research.v6.e2 import matrix
from tools.research.v6.e2.capture_analyzer import CAPTURE_ANALYZER_VERSION, analyze_replay

REQUALIFICATION_RECORD_NAME = "analyzer_requalification.json"
REQUALIFICATION_VERSION = 1
ORIENTATIONS = ("candidate_first", "opponent_first")
# Telemetry fields a different Ruleset id (and artifact location) must change.
_TELEMETRY_IDENTITY_KEYS = ("replay", "ruleset_id")


class RequalificationError(RuntimeError):
    """The analysis instrument has not been requalified on the control corpus."""


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _cells(root: Path) -> list[dict[str, Any]]:
    data = _load(root / "experiment_result.json")
    return [cell for condition in data["conditions"] for cell in condition["cells"]]


def _key(cell: Mapping[str, Any]) -> tuple[Any, ...]:
    return (cell["subject_id"], cell["opponent_id"], cell["seed"], cell["orientation"])


def corpus_integrity(
    root: Path,
    *,
    ruleset_id: str,
    pairs: Sequence[tuple[str, str]],
    seeds: Sequence[int],
    provenance: Mapping[str, Any],
    fingerprints: Mapping[str, str],
) -> dict[str, Any]:
    """Check one preserved condition/field run against what it must contain.

    ``provenance`` lists the values its ``provenance.json`` must hold (Git SHA,
    clean flag, matrix and pre-registration digests, ...), ``fingerprints``
    the frozen agent fingerprints.
    """
    problems: list[str] = []
    data = _load(root / "experiment_result.json")
    recorded = _load(root / "provenance.json")
    if data.get("provenance") != recorded:
        problems.append("experiment_result provenance differs from provenance.json")
    cells = _cells(root)
    keys = Counter(_key(cell) for cell in cells)
    expected = {(a, b, seed, o) for a, b in pairs for seed in seeds for o in ORIENTATIONS}
    duplicated = sorted(key for key, count in keys.items() if count > 1)
    missing, extra = sorted(expected - set(keys)), sorted(set(keys) - expected)
    for label, rows in (("duplicate", duplicated), ("missing", missing), ("unexpected", extra)):
        if rows:
            problems.append(f"{len(rows)} {label} cells, e.g. {rows[:3]}")
    incomplete = [
        _key(c) for c in cells if c.get("status") != "completed" or c.get("error_code")
        or c.get("outcome") not in ("win", "loss", "tie")
    ]
    if incomplete:
        problems.append(f"{len(incomplete)} cells without a completed outcome, e.g. {incomplete[:3]}")
    recorded_dirs: set[Path] = set()
    wrong_ruleset = 0
    for cell in cells:
        directory = (root / str(cell.get("artifact_dir"))).resolve()
        recorded_dirs.add(directory)
        if not (directory / "result.json").is_file() or not (directory / "replay.jsonl").is_file():
            problems.append(f"missing artifacts for {_key(cell)}")
        elif _load(directory / "result.json").get("ruleset_id") != ruleset_id:
            wrong_ruleset += 1
    if wrong_ruleset:
        problems.append(f"{wrong_ruleset} result.json files carry another Ruleset")
    on_disk = {p.resolve() for p in root.glob("arena_*/*/matches/*") if p.is_dir()}
    if on_disk != recorded_dirs:
        problems.append(f"{len(on_disk)} match directories on disk, {len(recorded_dirs)} recorded")
    for name, value in provenance.items():
        if recorded.get(name) != value:
            problems.append(f"provenance {name}={recorded.get(name)!r} != {value!r}")
    live = {name: row["fingerprint"] for name, row in (recorded.get("agent_fingerprints") or {}).items()}
    if live != dict(fingerprints):
        problems.append("agent fingerprints differ from the frozen definition")
    return {
        "cells": len(cells),
        "expected_cells": len(expected),
        "match_dirs_on_disk": len(on_disk),
        "git_sha": recorded.get("git_sha"),
        "git_dirty": recorded.get("git_dirty"),
        "problems": problems,
        "status": "PASS" if not problems else "FAIL",
    }


def _analyze(path: str) -> dict[str, Any]:
    try:
        return {"telemetry": analyze_replay(path, names_inferring_core=matrix.CORE_INFERRING_AGENTS)}
    except Exception as exc:
        return {"error": f"{type(exc).__name__}: {exc}"}


def _telemetry(root: Path, cells: Sequence[Mapping[str, Any]], workers: int) -> list[dict[str, Any]]:
    paths = [str(root / str(cell["artifact_dir"]) / "replay.jsonl") for cell in cells]
    if workers <= 1:
        return [_analyze(path) for path in paths]
    with ProcessPoolExecutor(max_workers=workers) as pool:
        return list(pool.map(_analyze, paths, chunksize=16))


def _index(cells: Sequence[Mapping[str, Any]]) -> dict[tuple[Any, ...], int]:
    seen: Counter[tuple[Any, ...]] = Counter()
    out: dict[tuple[Any, ...], int] = {}
    for position, cell in enumerate(cells):
        base = _key(cell)
        out[(*base, seen[base])] = position
        seen[base] += 1
    return out


def _comparable(telemetry: Mapping[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in telemetry.items() if key not in _TELEMETRY_IDENTITY_KEYS}


def analyzer_requalification(
    v4_root: Path, rs_root: Path, *, workers: int = 1, sample_limit: int = 10
) -> dict[str, Any]:
    """Run the capture analyzer over one field's C-V4 and C-RS replays."""
    sides: dict[str, dict[str, Any]] = {}
    telemetry: dict[str, list[dict[str, Any]]] = {}
    cells: dict[str, list[dict[str, Any]]] = {}
    for label, root in (("C-V4", v4_root), ("C-RS", rs_root)):
        cells[label] = _cells(root)
        telemetry[label] = _telemetry(root, cells[label], workers)
        failures = [
            {"cell": list(_key(cell)), "error": row["error"]}
            for cell, row in zip(cells[label], telemetry[label], strict=True)
            if "error" in row
        ]
        analyzed = [row["telemetry"] for row in telemetry[label] if "telemetry" in row]
        sides[label] = {
            "cells": len(cells[label]),
            "analyzed": len(analyzed),
            "failures": len(failures),
            "failure_samples": failures[:sample_limit],
            "failed_seeds": sorted({row["cell"][2] for row in failures}),
            "engine_disagreements": sum(1 for t in analyzed if not t["consistent_with_engine"]),
            "unattributed_completion_matches": sum(1 for t in analyzed if not t["all_completions_attributed"]),
            "attribution_mismatch_matches": sum(1 for t in analyzed if not t["attribution_matches_onset"]),
            "completions": sum(t["completions"] for t in analyzed),
            "capture_analyzer_versions": sorted({t["capture_analyzer_version"] for t in analyzed}),
        }
    v4_index, rs_index = _index(cells["C-V4"]), _index(cells["C-RS"])
    matched = sorted(set(v4_index) & set(rs_index), key=repr)
    differences = []
    for key in matched:
        a, b = telemetry["C-V4"][v4_index[key]], telemetry["C-RS"][rs_index[key]]
        if "telemetry" in a and "telemetry" in b and _comparable(a["telemetry"]) != _comparable(b["telemetry"]):
            differences.append(list(key))
    equivalence = {
        "cells_compared": len(matched),
        "unmatched": len(set(v4_index) ^ set(rs_index)),
        "differences": len(differences),
        "difference_samples": differences[:sample_limit],
    }
    ok = (
        bool(matched)
        and equivalence["unmatched"] == 0
        and equivalence["differences"] == 0
        and all(
            side["analyzed"] == side["cells"]
            and side["engine_disagreements"] == 0
            and side["unattributed_completion_matches"] == 0
            and side["attribution_mismatch_matches"] == 0
            for side in sides.values()
        )
    )
    return {
        "capture_analyzer_version": CAPTURE_ANALYZER_VERSION,
        "conditions": sides,
        "telemetry_equivalence": equivalence,
        "status": "PASS" if ok else "FAIL",
    }


def write_requalification_record(
    path: Path,
    *,
    freeze_id: str,
    matrix_id: str,
    fields: Mapping[str, Mapping[str, Any]],
    integrity: Mapping[str, Mapping[str, Any]],
    expected_matches: Mapping[str, int],
    provenance: Mapping[str, Any],
) -> dict[str, Any]:
    """Persist the requalification verdict for one analysis freeze."""
    complete = all(
        all(side["analyzed"] == count for side in (fields.get(fid) or {}).get("conditions", {}).values())
        and len((fields.get(fid) or {}).get("conditions", {})) == 2
        for fid, count in expected_matches.items()
    )
    passed = (
        bool(fields)
        and all(report["status"] == "PASS" for report in fields.values())
        and bool(integrity)
        and all(report["status"] == "PASS" for report in integrity.values())
    )
    record = {
        "requalification_version": REQUALIFICATION_VERSION,
        "freeze_id": freeze_id,
        "matrix_id": matrix_id,
        "capture_analyzer_version": CAPTURE_ANALYZER_VERSION,
        "fields": dict(fields),
        "integrity": dict(integrity),
        "expected_matches": dict(expected_matches),
        "replays_analyzed": sum(
            side["analyzed"] for report in fields.values() for side in report["conditions"].values()
        ),
        "complete": complete,
        "status": "PASS" if passed and complete else "FAIL",
        "provenance": dict(provenance),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, indent=2, sort_keys=True), encoding="utf-8")
    return record


def require_requalification(
    record_path: Path, *, freeze_id: str, expected_matches: Mapping[str, int]
) -> dict[str, Any]:
    """Fail closed unless this exact freeze passed a complete control-data requalification."""
    if not record_path.is_file():
        raise RequalificationError(
            f"No analyzer requalification record at {record_path}; requalify on the control corpus first."
        )
    record: dict[str, Any] = _load(record_path)
    problems = []
    if record.get("freeze_id") != freeze_id:
        problems.append(f"freeze_id {record.get('freeze_id')!r} != {freeze_id!r}")
    if record.get("status") != "PASS" or not record.get("complete"):
        problems.append(f"status {record.get('status')!r}, complete {record.get('complete')!r}")
    for field_id, count in expected_matches.items():
        report = (record.get("fields") or {}).get(field_id) or {}
        analyzed = [side.get("analyzed") for side in (report.get("conditions") or {}).values()]
        if report.get("status") != "PASS" or analyzed != [count, count]:
            problems.append(f"field {field_id}: status {report.get('status')!r}, analyzed {analyzed} of {count} each")
    if problems:
        raise RequalificationError("Analyzer requalification does not permit T-E2: " + "; ".join(problems))
    return record
