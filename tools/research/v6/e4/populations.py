"""The frozen E4 control populations and control baseline (design review Sec N, Sec R step 7).

Computed from the re-run controls only, after they pass parent reproduction
and before any treatment exists, per arm (primary: C-E4; companion: C-E4K1):

* every unit's control FMA summary, band and contest class, and the mirror
  seed units (O-UNIT, O-MATCHUP-MEDIAN, O-CONTEST);
* P-PAR (O-P-PAR), by contest class;
* the exposed F1 cells, their non-capture subset and their tick-limit count
  (the H4-H6 baselines, O-EXPOSED, O-CAPTURE);
* the control seat metrics and mirror claims (O-SEAT-METRICS, O-MIRROR-CLAIM);
* the control-vs-control census (O-CONTROL-CENSUS), which must be all
  identity classes, and every hypothesis evaluated control against itself.

and, once, P-STALE (O-P-STALE): E3's frozen stalemate cells within the E4 field.

The record is committed as ``control_populations.json``; its SHA-256 is
entered in the analysis freeze record's ``control_qualification`` block, and
before any treatment runs it must still recompute exactly from the control
corpus. It is never recomputed from treatment data.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from tools.research.v6.e3 import populations as e3_populations
from tools.research.v6.e4 import contest_classes, matrix
from tools.research.v6.e4.analyze_e4 import (
    FieldRun,
    control_census,
    evaluate_hypotheses,
    exposed_keys,
    is_capture,
    is_tick_limit,
    mirror_parity,
    p_par,
    seat_units,
    unit_rows,
    units,
)

POPULATIONS_PATH = Path(__file__).with_name("control_populations.json")
POPULATIONS_SCHEMA = "bytefray.v6.e4.control_populations"
POPULATIONS_VERSION = 1

# O-P-STALE: E3's committed populations record, pinned by E3 freeze v1.
E3_POPULATIONS_PATH = e3_populations.POPULATIONS_PATH
E3_POPULATIONS_SHA256 = "878754a2c961062f822ecae2bd55c143a8e84ace4b5c3a8125cbb9e44ff2cb95"
E3_FREEZE_ID = matrix.HISTORICAL_FREEZE_ID
P_STALE_FIELDS: tuple[str, ...] = ("F1", "F2", "F4")


class PopulationsError(RuntimeError):
    """The frozen control populations are missing, altered or no longer recompute."""


def p_stale(field_keys: Mapping[str, Sequence[str]]) -> dict[str, Any]:
    """O-P-STALE: E3's primary-arm stalemate cells whose cells exist in the E4 field."""
    record = e3_populations.load_record(E3_POPULATIONS_PATH, freeze_id=E3_FREEZE_ID,
                                        expected_sha256=E3_POPULATIONS_SHA256)
    frozen = record["arms"][matrix.PRIMARY_ARM]["populations"]
    cells = {
        field_id: sorted(key for key in frozen[field_id]["stalemate"] if key in set(field_keys[field_id]))
        for field_id in P_STALE_FIELDS
    }
    return {
        "source": {"path": "tools/research/v6/e3/control_populations.json", "sha256": E3_POPULATIONS_SHA256,
                   "e3_freeze_id": E3_FREEZE_ID, "arm": matrix.PRIMARY_ARM},
        "e3_stalemate_cells": {field_id: len(frozen[field_id]["stalemate"]) for field_id in P_STALE_FIELDS},
        "cells": cells,
        "count": sum(len(keys) for keys in cells.values()),
    }


def arm_baseline(runs: Mapping[str, FieldRun], table: Mapping[str, Any]) -> dict[str, Any]:
    """Everything one arm's control freezes (see the module docstring)."""
    if set(runs) != set(matrix.FIELD_IDS):
        raise PopulationsError(f"control runs for {sorted(runs)}, need {list(matrix.FIELD_IDS)}")
    rows = unit_rows(runs, None, table)
    members = p_par(rows)
    f1 = runs["F1"]
    exposed = exposed_keys(f1)
    return {
        "units": rows,
        "p_par": members,
        "p_par_by_class": {cls: [name for name in members if rows[name]["contest_class"] == cls]
                           for cls in contest_classes.CLASSES},
        "mirror_seed_units": {f.field_id: {name: keys for name, keys in units(runs[f.field_id]).items()
                                           if rows[name]["kind"] == "mirror"}
                              for f in matrix.FIELDS},
        "exposed_f1": exposed,
        "non_capture_exposed_f1": [k for k in exposed if not is_capture(f1.cells[k])],
        "exposed_f1_tick_limit": sum(1 for k in exposed if is_tick_limit(f1.cells[k])),
        "seat_metrics": {field_id: seat_units(runs[field_id]) for field_id in matrix.FIELD_IDS},
        "mirror_claims": mirror_parity(runs["F2"], runs["F2-P"]),
        "counts": {
            "units": len(rows),
            "p_par": len(members),
            "decided_early_units": sum(1 for row in rows.values() if row["control"]["status"] == "DECIDED-EARLY"),
            "exposed_f1": len(exposed),
        },
    }


def build_record(
    *,
    freeze_id: str,
    preregistration_sha256: str,
    prereg: Mapping[str, Any],
    arms: Mapping[str, Mapping[str, FieldRun]],
) -> dict[str, Any]:
    """``arms[arm][field]``: the arm's control runs, every field."""
    table = contest_classes.load_table()
    body: dict[str, Any] = {arm: {"control": matrix.ARM_CONTROLS[arm], **arm_baseline(runs, table)}
                            for arm, runs in arms.items()}
    # O-CONTROL-CENSUS: each control against itself, with the hypotheses read the same way.
    for arm, runs in arms.items():
        body[arm]["control_census"] = control_census(unit_rows(runs, runs, table))
    self_arms = {arm: {"control": runs, "treatment": runs} for arm, runs in arms.items()}
    hypotheses = evaluate_hypotheses(self_arms, body, prereg, table)
    body[matrix.PRIMARY_ARM]["control_vs_control_hypotheses"] = {
        key: {k: v for k, v in value.items() if k != "units"} if isinstance(value, dict) else value
        for key, value in hypotheses.items() if key != "units"
    }
    primary_runs = arms[matrix.PRIMARY_ARM]
    return {
        "schema": POPULATIONS_SCHEMA,
        "version": POPULATIONS_VERSION,
        "status": "frozen from control data before any treatment data exists",
        "matrix_id": matrix.matrix_id(),
        "freeze_id": freeze_id,
        "preregistration_sha256": preregistration_sha256,
        "contest_classes_sha256": contest_classes.CONTEST_CLASSES_SHA256,
        "p_stale": p_stale({f: list(primary_runs[f].cells) for f in P_STALE_FIELDS}),
        "arms": body,
    }


def canonical_bytes(record: Mapping[str, Any]) -> bytes:
    return (json.dumps(record, indent=1, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def record_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def write_record(path: Path, record: Mapping[str, Any]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_bytes(record))
    return record_sha256(path)


def load_record(path: Path, *, freeze_id: str, expected_sha256: str | None) -> dict[str, Any]:
    """The committed populations record; fails closed unless it is the one the freeze names."""
    if not path.is_file():
        raise PopulationsError(f"No frozen control populations at {path}.")
    if expected_sha256 is not None and record_sha256(path) != expected_sha256:
        raise PopulationsError(f"{path} SHA-256 {record_sha256(path)} != the freeze's {expected_sha256}")
    record: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    problems = []
    if record.get("schema") != POPULATIONS_SCHEMA or record.get("version") != POPULATIONS_VERSION:
        problems.append("schema")
    if record.get("matrix_id") != matrix.matrix_id():
        problems.append(f"matrix_id {record.get('matrix_id')!r}")
    if record.get("freeze_id") != freeze_id:
        problems.append(f"freeze_id {record.get('freeze_id')!r} != {freeze_id!r}")
    if record.get("contest_classes_sha256") != contest_classes.CONTEST_CLASSES_SHA256:
        problems.append("contest classes")
    if set(record.get("arms") or {}) != set(matrix.ARM_CONTROLS):
        problems.append("arms")
    if problems:
        raise PopulationsError("Frozen control populations do not hold: " + "; ".join(problems))
    return record


def require_recomputes(record: Mapping[str, Any], recomputed: Mapping[str, Any]) -> None:
    """The frozen populations and baseline must equal a fresh computation from the controls."""
    def norm(value: Any) -> Any:
        return json.loads(json.dumps(value, sort_keys=True))

    differing = [part for part in ("p_stale", "arms") if norm(record[part]) != norm(recomputed[part])]
    if differing:
        raise PopulationsError(f"Frozen control populations no longer recompute from the controls: {differing}")


def require_control_census(record: Mapping[str, Any]) -> None:
    """Hard stop 11: the control-vs-control census must be 100% identity classes in both arms."""
    failing = [arm for arm, body in record["arms"].items() if body["control_census"]["status"] != "PASS"]
    if failing:
        raise PopulationsError(f"STOP: the control-vs-control census is not 100% unchanged in {failing}.")
