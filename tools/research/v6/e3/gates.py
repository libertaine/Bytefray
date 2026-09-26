"""V6 E3 qualification and treatment gates (design review Sec N).

Reads artifacts only; executes nothing.

* **Parent reproduction** (Sec N step 6, hard stop 2). A new control and the
  preserved E2 corpus it must reproduce run under the *same* Ruleset id, so
  nothing is excused: every harness cell field, ``match_id`` and
  ``result_id``, the whole ``result.json`` apart from its per-execution
  occurrence metadata, the replay bytes (SHA-256), and the E3 telemetry
  (capture and executed actions) must be identical cell for cell.
* **Fresh-control integrity** for fields with no historical counterpart
  (F2-P, F4): the frozen cell set, completed cells with artifacts, provenance
  and fingerprints (E2's ``corpus_integrity``, reused unchanged), clean
  telemetry, and -- for F2-P -- the identity of every tick up to tick 1000
  with the same condition's F2 replay (no fixture reads the tick limit).
* **Prefix gate** (hard stop 6), for the future treatment: a treatment
  replay must equal its control through the control's first disruptive hit,
  and a hit-free control cell must be reproduced entirely.
* **Manipulation checks** (MC-1, hard stops 5, 7, 8) and the **D9 stop
  check** (hard stop 9), for the future treatment.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

PARENT_RECORD_NAME = "parent_reproduction.json"
PARENT_GATE_VERSION = 1

# Per-execution occurrence metadata: the only result.json keys a reproduction
# may change (the parent byte-identity freeze makes the same exception).
RESULT_OCCURRENCE_KEYS: tuple[str, ...] = ("completed_at", "occurrence_id")
# Identity keys a different Ruleset id is required to change (treatment vs control).
RUN_IDENTITY_KEYS: tuple[str, ...] = ("match_id", "result_id", "ruleset_id", "replay_id")
CELL_FIELDS: tuple[str, ...] = (
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
    "match_id",
    "result_id",
    "error_code",
)
# Telemetry keys that name where an artifact lives, not what it contains.
TELEMETRY_LOCATION_KEYS: tuple[str, ...] = ("replay",)

D9_VICTIMS: frozenset[str] = frozenset(
    {"e2_repair_guard", "e2_repair_guard_twin", "e2_disrupt_guard", "e2_disrupt_guard_twin"}
)


class ParentReproductionError(RuntimeError):
    """The new controls did not reproduce their historical parents."""


class TreatmentGateError(RuntimeError):
    """A treatment replay failed a hard-stop gate."""


class D9StopError(TreatmentGateError):
    """A capture completion against a repair or disrupt guard under T-E3 (a theorem violation)."""


# ---------------------------------------------------------------------------
# Cells and artifacts
# ---------------------------------------------------------------------------


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_cells(root: Path) -> list[dict[str, Any]]:
    data = _load_json(root / "experiment_result.json")
    return [cell for condition in data["conditions"] for cell in condition["cells"]]


def cell_key(cell: Mapping[str, Any]) -> str:
    """``subject|opponent|seed|orientation`` -- a cell's identity within one field."""
    return f"{cell['subject_id']}|{cell['opponent_id']}|{cell['seed']}|{cell['orientation']}"


def index_cells(cells: Iterable[Mapping[str, Any]]) -> dict[str, Mapping[str, Any]]:
    """Cells by identity; a repeated identity is kept apart by occurrence (``#n``)."""
    seen: Counter[str] = Counter()
    out: dict[str, Mapping[str, Any]] = {}
    for cell in cells:
        base = cell_key(cell)
        out[base if seen[base] == 0 else f"{base}#{seen[base]}"] = cell
        seen[base] += 1
    return out


def artifact_dir(root: Path, cell: Mapping[str, Any]) -> Path:
    return root / str(cell["artifact_dir"])


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def result_without_occurrence(result: Mapping[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in result.items() if key not in RESULT_OCCURRENCE_KEYS}


def comparable_telemetry(telemetry: Mapping[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in telemetry.items() if key not in TELEMETRY_LOCATION_KEYS}


def telemetry_digest(telemetry: Mapping[str, Any]) -> str:
    canonical = json.dumps(comparable_telemetry(telemetry), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Parent reproduction
# ---------------------------------------------------------------------------


def compare_parent_reproduction(
    new_root: Path,
    historical_root: Path,
    *,
    new_telemetry: Mapping[str, Mapping[str, Any]],
    historical_telemetry: Mapping[str, Mapping[str, Any]],
    sample_limit: int = 10,
) -> dict[str, Any]:
    """Deep, strict comparison of one field of a new control with its historical parent.

    ``*_telemetry`` map a cell identity to its E3 telemetry record (``telemetry``
    or ``error``); both sides must have clean telemetry, and equal.
    """
    new = index_cells(load_cells(new_root))
    old = index_cells(load_cells(historical_root))
    reasons: Counter[str] = Counter()
    samples: list[dict[str, Any]] = []

    def fail(key: str, reason: str, detail: Any = None) -> None:
        reasons[reason] += 1
        if len(samples) < sample_limit:
            samples.append({"cell": key, "reason": reason, "detail": detail})

    matched = sorted(set(new) & set(old))
    for key in matched:
        a, b = new[key], old[key]
        differing = [name for name in CELL_FIELDS if a.get(name) != b.get(name)]
        if differing:
            fail(key, "cell_fields", differing)
            continue
        if a.get("artifact_dir") is None or b.get("artifact_dir") is None:
            fail(key, "missing_artifacts")
            continue
        dir_a, dir_b = artifact_dir(new_root, a), artifact_dir(historical_root, b)
        if result_without_occurrence(_load_json(dir_a / "result.json")) != result_without_occurrence(
            _load_json(dir_b / "result.json")
        ):
            fail(key, "result_json")
            continue
        if file_sha256(dir_a / "replay.jsonl") != file_sha256(dir_b / "replay.jsonl"):
            fail(key, "replay_bytes")
            continue
        row_a, row_b = new_telemetry.get(key) or {}, historical_telemetry.get(key) or {}
        if "telemetry" not in row_a or "telemetry" not in row_b:
            fail(key, "telemetry_missing_or_failed", [row_a.get("error"), row_b.get("error")])
            continue
        if comparable_telemetry(row_a["telemetry"]) != comparable_telemetry(row_b["telemetry"]):
            fail(key, "telemetry")
    for key in sorted(set(new) - set(old)):
        fail(key, "missing_in_historical")
    for key in sorted(set(old) - set(new)):
        fail(key, "missing_in_new")
    ok = bool(matched) and not reasons
    return {
        "cells_compared": len(matched),
        "new_cells": len(new),
        "historical_cells": len(old),
        "mismatch_count": sum(reasons.values()),
        "mismatch_reasons": dict(sorted(reasons.items())),
        "mismatch_samples": samples,
        "compared": ["cell fields incl. match_id and result_id", "result.json minus occurrence metadata",
                     "replay SHA-256", "E3 action/parity and capture telemetry"],
        "status": "PASS" if ok else "FAIL",
    }


def write_parent_record(
    path: Path,
    *,
    matrix_id: str,
    freeze_id: str,
    reproduction: Mapping[str, Mapping[str, Mapping[str, Any]]],
    fresh: Mapping[str, Mapping[str, Mapping[str, Any]]],
    expected_matches: Mapping[str, Mapping[str, int]],
    sample: bool,
    provenance: Mapping[str, Any],
) -> dict[str, Any]:
    """Persist the parent-reproduction verdict. A sample record can never unlock a treatment.

    ``reproduction[condition][field]``: historical comparisons; ``fresh[condition][field]``:
    integrity of fields with no historical counterpart; ``expected_matches[condition][field]``.
    """
    counted = {
        condition: {
            field_id: (reproduction.get(condition, {}).get(field_id) or fresh.get(condition, {}).get(field_id) or {})
            for field_id in fields
        }
        for condition, fields in expected_matches.items()
    }
    complete = not sample and all(
        report.get("cells_compared") == expected_matches[condition][field_id]
        for condition, fields in counted.items()
        for field_id, report in fields.items()
    )
    reports = [r for block in (reproduction, fresh) for fields in block.values() for r in fields.values()]
    passed = bool(reports) and all(report.get("status") == "PASS" for report in reports)
    record = {
        "gate_version": PARENT_GATE_VERSION,
        "matrix_id": matrix_id,
        "freeze_id": freeze_id,
        "sample": sample,
        "reproduction": {c: dict(f) for c, f in reproduction.items()},
        "fresh": {c: dict(f) for c, f in fresh.items()},
        "expected_matches": {c: dict(f) for c, f in expected_matches.items()},
        "complete": complete,
        "status": "PASS" if passed else "FAIL",
        "unlocks_treatment": passed and complete,
        "provenance": dict(provenance),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, indent=2, sort_keys=True), encoding="utf-8")
    return record


def require_parent_reproduction(
    record_path: Path,
    *,
    matrix_id: str,
    freeze_id: str,
    expected_matches: Mapping[str, Mapping[str, int]],
) -> dict[str, Any]:
    """Fail closed unless a complete, passing, non-sample parent reproduction exists
    for this matrix and analysis freeze, covering every control field."""
    if not record_path.is_file():
        raise ParentReproductionError(f"No parent reproduction record at {record_path}; run the controls' gate first.")
    record: dict[str, Any] = _load_json(record_path)
    problems: list[str] = []
    if record.get("matrix_id") != matrix_id:
        problems.append(f"matrix_id {record.get('matrix_id')!r} != {matrix_id!r}")
    if record.get("freeze_id") != freeze_id:
        problems.append(f"freeze_id {record.get('freeze_id')!r} != {freeze_id!r}")
    if record.get("sample") is not False:
        problems.append("the gate was run on a sample, not the full control matrix")
    if record.get("status") != "PASS" or record.get("complete") is not True:
        problems.append(f"status {record.get('status')!r}, complete {record.get('complete')!r}")
    for condition, fields in expected_matches.items():
        for field_id, count in fields.items():
            report = ((record.get("reproduction") or {}).get(condition) or {}).get(field_id) or (
                (record.get("fresh") or {}).get(condition) or {}
            ).get(field_id)
            if report is None:
                problems.append(f"{condition}/{field_id} was not checked")
            elif report.get("status") != "PASS" or report.get("cells_compared") != count:
                problems.append(
                    f"{condition}/{field_id}: status {report.get('status')!r}, "
                    f"{report.get('cells_compared')} of {count} cells"
                )
    if problems:
        raise ParentReproductionError("Parent reproduction does not permit treatment: " + "; ".join(problems))
    return record


# ---------------------------------------------------------------------------
# Raw replay records and tick prefixes
# ---------------------------------------------------------------------------


def replay_records(path: Path) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any] | None]:
    """``(header, ticks, result)`` as raw JSON records."""
    header: dict[str, Any] | None = None
    ticks: list[dict[str, Any]] = []
    result: dict[str, Any] | None = None
    with path.open("r", encoding="utf-8") as handle:
        for raw in handle:
            if not raw.strip():
                continue
            record = json.loads(raw)
            kind = record.get("record_type")
            if kind == "header":
                header = record
            elif kind == "tick":
                ticks.append(record)
            elif kind == "result":
                result = record
    if header is None:
        raise ValueError(f"{path}: replay has no header record")
    return header, ticks, result


def _without(record: Mapping[str, Any] | None, keys: Iterable[str]) -> dict[str, Any] | None:
    if record is None:
        return None
    dropped = set(keys)
    return {key: value for key, value in record.items() if key not in dropped}


def static_header(header: Mapping[str, Any], *, drop_tick_limit: bool = False) -> dict[str, Any]:
    """The header without identity keys or end-of-match entrant data."""
    out = _without(header, (*RUN_IDENTITY_KEYS, "entrants")) or {}
    out["entrants"] = [
        {key: entrant.get(key) for key in ("agent_id", "name", "metadata")}
        for entrant in header.get("entrants") or ()
    ]
    if drop_tick_limit:
        out["reproducibility"] = _without(out.get("reproducibility") or {}, ("tick_limit",))
    return out


def first_hit_tick(ticks: Sequence[Mapping[str, Any]]) -> int | None:
    """The first tick in which any process carries the replay's ``disrupted`` flag."""
    for record in ticks:
        if any(process.get("disrupted") for process in record.get("processes") or ()):
            return int(record["tick"])
    return None


def first_tick_difference(
    a: Sequence[Mapping[str, Any]], b: Sequence[Mapping[str, Any]], *, through: int | None = None
) -> int | None:
    """The first tick (<= ``through``) whose records differ or is missing on one side."""
    by_a = {int(record["tick"]): record for record in a}
    by_b = {int(record["tick"]): record for record in b}
    last = max(max(by_a, default=-1), max(by_b, default=-1)) if through is None else through
    for tick in range(last + 1):
        if by_a.get(tick) != by_b.get(tick):
            return tick
    return None


def prefix_gate_cell(control_replay: Path, treatment_replay: Path) -> dict[str, Any]:
    """Hard stop 6 for one matched cell: identical through the control's first hit,
    or identical entirely when the control has no hit."""
    c_header, c_ticks, c_result = replay_records(control_replay)
    t_header, t_ticks, t_result = replay_records(treatment_replay)
    hit = first_hit_tick(c_ticks)
    problems: list[str] = []
    if static_header(c_header) != static_header(t_header):
        problems.append("static header differs")
    if hit is None:
        difference = first_tick_difference(c_ticks, t_ticks)
        if difference is not None:
            problems.append(f"hit-free control differs at tick {difference}")
        if _without(c_result, RUN_IDENTITY_KEYS) != _without(t_result, RUN_IDENTITY_KEYS):
            problems.append("hit-free control result differs")
        if [e.get("statistics") for e in c_header.get("entrants") or ()] != [
            e.get("statistics") for e in t_header.get("entrants") or ()
        ]:
            problems.append("hit-free control entrant statistics differ")
    else:
        difference = first_tick_difference(c_ticks, t_ticks, through=hit - 1)
        if difference is not None:
            problems.append(f"differs at tick {difference}, before the control's first hit at tick {hit}")
    return {"first_hit_tick": hit, "hit_free": hit is None, "ok": not problems, "problems": problems}


def prefix_gate(
    control_root: Path,
    treatment_root: Path,
    *,
    frozen_hit_free: Iterable[str],
    sample_limit: int = 10,
) -> dict[str, Any]:
    """Hard stop 6 over one field: every matched cell passes, and the control's
    hit-free cells are exactly the frozen ones."""
    control = index_cells(load_cells(control_root))
    treatment = index_cells(load_cells(treatment_root))
    failures: list[dict[str, Any]] = []
    hit_free: list[str] = []
    for key in sorted(set(control) & set(treatment)):
        row = prefix_gate_cell(
            artifact_dir(control_root, control[key]) / "replay.jsonl",
            artifact_dir(treatment_root, treatment[key]) / "replay.jsonl",
        )
        if row["hit_free"]:
            hit_free.append(key)
        if not row["ok"]:
            failures.append({"cell": key, **row})
    frozen = sorted(frozen_hit_free)
    unmatched = sorted(set(control) ^ set(treatment))
    ok = not failures and not unmatched and sorted(hit_free) == frozen and bool(control)
    return {
        "cells_compared": len(set(control) & set(treatment)),
        "unmatched": len(unmatched),
        "hit_free_cells": len(hit_free),
        "hit_free_matches_frozen": sorted(hit_free) == frozen,
        "failures": len(failures),
        "failure_samples": failures[:sample_limit],
        "status": "PASS" if ok else "FAIL",
    }


def parity_replicate_prefix(f2_replay: Path, f2p_replay: Path, *, tick_limit: int) -> dict[str, Any]:
    """F2-P against F2 under one condition: identical through tick ``tick_limit`` (and
    entirely, apart from the tick limit, when F2 ended before it)."""
    a_header, a_ticks, a_result = replay_records(f2_replay)
    b_header, b_ticks, b_result = replay_records(f2p_replay)
    problems: list[str] = []
    if static_header(a_header, drop_tick_limit=True) != static_header(b_header, drop_tick_limit=True):
        problems.append("static header differs beyond the tick limit")
    f2_ticks = int(a_ticks[-1]["tick"]) if a_ticks else 0
    through = min(f2_ticks, tick_limit)
    difference = first_tick_difference(a_ticks, b_ticks, through=through)
    if difference is not None:
        problems.append(f"differs at tick {difference}")
    if f2_ticks < tick_limit and _without(a_result, RUN_IDENTITY_KEYS) != _without(b_result, RUN_IDENTITY_KEYS):
        problems.append("F2 ended before the tick limit but the F2-P result differs")
    return {"compared_through": through, "ok": not problems, "problems": problems}


# ---------------------------------------------------------------------------
# Treatment manipulation checks and the D9 stop check
# ---------------------------------------------------------------------------


def manipulation_checks(rows: Mapping[str, Mapping[str, Any]], *, slot_limited: bool) -> dict[str, Any]:
    """MC-1 / hard stops 5, 7 and 8 over one field's telemetry rows.

    Always required: clean telemetry, the cpu_used cross-check and capture
    agreement. Under ``slot_limited`` (lambda = 1) also: no zero-action live
    tick, no exclusive tick and no G.4 violation.
    """
    counts: Counter[str] = Counter()
    samples: list[dict[str, Any]] = []
    for key, row in sorted(rows.items()):
        telemetry = row.get("telemetry")
        found: list[str] = []
        if telemetry is None:
            found.append("analyzer_failure")
        else:
            checks = telemetry["checks"]
            if not checks["cpu_statistics_match"]:
                found.append("cpu_used_mismatch")
            if not (checks["capture_reconstruction_agrees"] and checks["capture_consistent_with_engine"]
                    and checks["capture_attribution_ok"]):
                found.append("capture_disagreement")
            if slot_limited:
                seats = telemetry["seats"].values()
                if any(seat["zero_action_live_ticks"] for seat in seats):
                    found.append("zero_action_live_tick")
                if telemetry["exclusive_ticks"]:
                    found.append("exclusive_tick")
                if any(seat["g4_violations"] for seat in seats):
                    found.append("g4_violation")
        for name in found:
            counts[name] += 1
        if found and len(samples) < 10:
            samples.append({"cell": key, "failed": found})
    return {
        "cells": len(rows),
        "slot_limited": slot_limited,
        "violations": dict(sorted(counts.items())),
        "violation_samples": samples,
        "status": "PASS" if rows and not counts else "FAIL",
    }


def d9_completions(rows: Mapping[str, Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Every capture completion whose victim is a repair or disrupt guard (or twin)."""
    out = []
    for key, row in sorted(rows.items()):
        telemetry = row.get("telemetry")
        if telemetry is None:
            continue
        for completion in telemetry["completions"]:
            if completion["victim_name"] in D9_VICTIMS:
                out.append({"cell": key, **completion})
    return out


def require_d9(condition_id: str, completions: Sequence[Mapping[str, Any]], *, primary_treatment: str) -> None:
    """Hard stop 9: a D9 violation in the primary treatment is an implementation defect."""
    if condition_id == primary_treatment and completions:
        raise D9StopError(
            f"D9 violation under {condition_id}: {len(completions)} capture completion(s) against a repair or "
            f"disrupt guard, e.g. {list(completions)[:3]}. G.5 is a theorem; STOP and re-qualify the implementation."
        )
