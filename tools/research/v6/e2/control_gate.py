"""C-V4 / C-RS structural-control equivalence gate (design review Sec I.1, Sec I.5 rule 3).

C-RS (``bytefray-rules-6-research-scale``) is E2's direct parent and must be
behaviourally identical to C-V4 (``bytefray-rules-4``) at arena 512 over
the defined experimental fields. The gate compares two harness runs cell by
cell -- placement, winner, outcome, decision tick, scores, territory,
termination reasons -- then each cell's ``result.json`` and full canonical
replay, ignoring only the identity fields a different Ruleset id is
required to change (``ruleset_id``, ``match_id``, ``result_id``,
``replay_id``, replay digest, timestamps, occurrence ids).

Any mismatch fails the gate, and a failed or missing gate blocks every
T-E2 execution and interpretation (``require_control_gate``). Reads
artifacts only; executes nothing.
"""

from __future__ import annotations

import json
from collections import Counter
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

GATE_RECORD_NAME = "control_gate.json"
GATE_VERSION = 1

_CELL_FIELDS = (
    "subject_start",
    "opponent_start",
    "seat_a_id",
    "seat_b_id",
    "status",
    "outcome",
    "winner_id",
    "winner_seat",
    "ticks_run",
    "termination_reason",
    "score_subject",
    "score_opponent",
    "territory_subject",
    "territory_opponent",
    "entrant_terminations",
)
_RESULT_IDENTITY_KEYS = ("match_id", "result_id", "ruleset_id", "completed_at", "occurrence_id")
_REPLAY_IDENTITY_KEYS = ("replay_id", "match_id", "result_id", "ruleset_id")


class ControlGateError(RuntimeError):
    """The structural-control gate has not passed; T-E2 must not run or be interpreted."""


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _null_result_identity(result: Mapping[str, Any]) -> dict[str, Any]:
    out = {key: value for key, value in result.items() if key not in _RESULT_IDENTITY_KEYS}
    replay = dict(out.get("replay") or {})
    replay.pop("replay_id", None)
    replay.pop("sha256", None)
    out["replay"] = replay
    return out


def _replay_lines(path: Path) -> list[dict[str, Any]]:
    lines = []
    with path.open("r", encoding="utf-8") as handle:
        for raw in handle:
            if raw.strip():
                record = json.loads(raw)
                for key in _REPLAY_IDENTITY_KEYS:
                    record.pop(key, None)
                lines.append(record)
    return lines


def _index_cells(cells: Sequence[Mapping[str, Any]]) -> dict[tuple[Any, ...], Mapping[str, Any]]:
    seen: Counter[tuple[Any, ...]] = Counter()
    out: dict[tuple[Any, ...], Mapping[str, Any]] = {}
    for cell in cells:
        base = (cell["subject_id"], cell["opponent_id"], cell["seed"], cell["orientation"])
        out[(*base, seen[base])] = cell
        seen[base] += 1
    return out


def _experiment_cells(root: Path) -> list[Mapping[str, Any]]:
    data = _load_json(root / "experiment_result.json")
    return [cell for condition in data["conditions"] for cell in condition["cells"]]


def compare_control_runs(
    v4_root: Path, rs_root: Path, *, deep_replay: bool = True, sample_limit: int = 10
) -> dict[str, Any]:
    """Compare one field's C-V4 and C-RS harness outputs cell by cell."""
    v4 = _index_cells(_experiment_cells(v4_root))
    rs = _index_cells(_experiment_cells(rs_root))
    mismatches: list[dict[str, Any]] = []
    for key in sorted(set(v4) & set(rs), key=repr):
        a, b = v4[key], rs[key]
        differing = [name for name in _CELL_FIELDS if a.get(name) != b.get(name)]
        if differing:
            mismatches.append({"cell": list(key), "reason": "cell_fields", "fields": differing})
            continue
        if a.get("artifact_dir") is None or b.get("artifact_dir") is None:
            mismatches.append({"cell": list(key), "reason": "missing_artifacts"})
            continue
        dir_a, dir_b = v4_root / str(a["artifact_dir"]), rs_root / str(b["artifact_dir"])
        if _null_result_identity(_load_json(dir_a / "result.json")) != _null_result_identity(
            _load_json(dir_b / "result.json")
        ):
            mismatches.append({"cell": list(key), "reason": "result_json"})
            continue
        if deep_replay and _replay_lines(dir_a / "replay.jsonl") != _replay_lines(dir_b / "replay.jsonl"):
            mismatches.append({"cell": list(key), "reason": "replay_stream"})
    missing_rs = sorted(set(v4) - set(rs), key=repr)
    missing_v4 = sorted(set(rs) - set(v4), key=repr)
    ok = not mismatches and not missing_rs and not missing_v4 and bool(v4)
    return {
        "cells_compared": len(set(v4) & set(rs)),
        "v4_cells": len(v4),
        "rs_cells": len(rs),
        "missing_in_rs": len(missing_rs),
        "missing_in_v4": len(missing_v4),
        "mismatch_count": len(mismatches),
        "mismatch_samples": mismatches[:sample_limit],
        "deep_replay": deep_replay,
        "status": "PASS" if ok else "FAIL",
    }


def write_gate_record(
    path: Path,
    *,
    matrix_id: str,
    fields: Mapping[str, Mapping[str, Any]],
    expected_matches: Mapping[str, int],
    sample: bool,
    provenance: Mapping[str, Any],
) -> dict[str, Any]:
    """Persist the gate verdict. A sample gate can never unlock T-E2."""
    complete = not sample and all(
        fields.get(field_id, {}).get("cells_compared") == count
        for field_id, count in expected_matches.items()
    )
    passed = bool(fields) and all(report["status"] == "PASS" for report in fields.values())
    record = {
        "gate_version": GATE_VERSION,
        "matrix_id": matrix_id,
        "sample": sample,
        "fields": dict(fields),
        "expected_matches": dict(expected_matches),
        "complete": complete,
        "status": "PASS" if passed else "FAIL",
        "unlocks_treatment": passed and complete,
        "provenance": dict(provenance),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, indent=2, sort_keys=True), encoding="utf-8")
    return record


def require_control_gate(
    record_path: Path, *, matrix_id: str, expected_matches: Mapping[str, int]
) -> dict[str, Any]:
    """Fail closed unless a complete, passing gate exists for this exact matrix."""
    if not record_path.is_file():
        raise ControlGateError(f"No control gate record at {record_path}; run the C-V4/C-RS gate first.")
    record: dict[str, Any] = _load_json(record_path)
    problems = []
    if record.get("matrix_id") != matrix_id:
        problems.append(f"matrix_id {record.get('matrix_id')!r} != {matrix_id!r}")
    if record.get("sample"):
        problems.append("the gate was run on a sample, not the full control matrix")
    if record.get("status") != "PASS":
        problems.append(f"gate status is {record.get('status')!r}")
    for field_id, count in expected_matches.items():
        report = (record.get("fields") or {}).get(field_id)
        if report is None:
            problems.append(f"field {field_id} was not compared")
        elif report.get("status") != "PASS" or report.get("cells_compared") != count:
            problems.append(
                f"field {field_id}: status {report.get('status')!r}, "
                f"{report.get('cells_compared')} of {count} cells compared"
            )
    if problems:
        raise ControlGateError("Control gate does not permit T-E2: " + "; ".join(problems))
    return record
