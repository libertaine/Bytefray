"""The frozen E3 control populations and control baseline (design review Sec J, Sec M rule 6).

Computed from the new controls only, after they pass parent reproduction and
before any treatment exists:

* per arm (primary: C-E2; companion: C-RS) and field, the exposed, stalemate
  and hit-free cell identities (``analyze_e3.populations``);
* per arm, every hypothesis quantity evaluated on the control
  (``analyze_e3.control_baseline``), including the control residual table the
  Sec M rule 4 comparison needs.

The record is committed as ``control_populations.json``; its SHA-256 is
entered in the analysis freeze record's ``control_qualification`` block, and
before any treatment runs it must still recompute exactly from the control
corpus. It is never recomputed from treatment data.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from tools.research.v6.e3 import matrix
from tools.research.v6.e3.analyze_e3 import FieldRun, control_baseline, populations

POPULATIONS_PATH = Path(__file__).with_name("control_populations.json")
POPULATIONS_SCHEMA = "bytefray.v6.e3.control_populations"
POPULATIONS_VERSION = 1
ARM_CONTROLS: dict[str, str] = {matrix.PRIMARY_ARM: "C-E2", matrix.COMPANION_ARM: "C-RS"}


class PopulationsError(RuntimeError):
    """The frozen control populations are missing, altered or no longer recompute."""


def build_record(
    *,
    freeze_id: str,
    preregistration_sha256: str,
    prereg: Mapping[str, Any],
    arms: Mapping[str, Mapping[str, FieldRun]],
) -> dict[str, Any]:
    """``arms[arm][field]``: the arm's control runs, every field."""
    body: dict[str, Any] = {}
    for arm, runs in arms.items():
        if set(runs) != set(matrix.FIELD_IDS):
            raise PopulationsError(f"{arm}: control runs for {sorted(runs)}, need {list(matrix.FIELD_IDS)}")
        frozen = populations(runs)
        body[arm] = {
            "control": ARM_CONTROLS[arm],
            "populations": frozen,
            "baseline": control_baseline(runs, frozen, prereg),
        }
    return {
        "schema": POPULATIONS_SCHEMA,
        "version": POPULATIONS_VERSION,
        "status": "frozen from control data before any treatment data exists",
        "matrix_id": matrix.matrix_id(),
        "freeze_id": freeze_id,
        "preregistration_sha256": preregistration_sha256,
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
    if set(record.get("arms") or {}) != set(ARM_CONTROLS):
        problems.append("arms")
    if problems:
        raise PopulationsError("Frozen control populations do not hold: " + "; ".join(problems))
    return record


def require_recomputes(record: Mapping[str, Any], recomputed: Mapping[str, Any]) -> None:
    """The frozen populations and baseline must equal a fresh computation from the controls."""
    differing = [
        f"{arm}.{part}"
        for arm in ARM_CONTROLS
        for part in ("populations", "baseline")
        if json.loads(json.dumps(record["arms"][arm][part])) != json.loads(json.dumps(recomputed["arms"][arm][part]))
    ]
    if differing:
        raise PopulationsError(f"Frozen control populations no longer recompute from the controls: {differing}")
