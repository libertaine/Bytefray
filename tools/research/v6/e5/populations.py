"""The frozen E5 control populations (Revision 1 Sec R5.6; preregistration O-P-BASE,
O-CONTEST-E5, O-P-PAR-E5, O-MIN-SB).

Computed from the re-run controls only, after they pass parent reproduction
and before any treatment exists, per arm (primary: C-E5; companion: C-E5K1):

* every directed unit's control BP summary and contest class;
* P-BASE (control BP >= 1/3) with its SWEEP-BACKED / ANCHOR-ONLY /
  MIXED-INFERENCE split, and the O-MIN-SB check (>= 6 SWEEP-BACKED units in
  the primary arm), which halts the experiment before treatment if it fails;
* the control-against-control census, which must be all identity classes;
* the control-side E5-D clauses: D-5 (every ANCHOR-ONLY P-BASE unit's
  anchor-induced core-0 contact exists in every DEFINED control cell) and D-6
  (DUAL > 0 in every cell with a hostile hit on an unmoved anchor); and the
  inference sanity check (every audited inference in control is correct);

and, once, P-PAR-E5: E4's frozen primary-arm P-PAR restricted to the E5 field.

The record is committed as ``control_populations.json``; its SHA-256 is
entered in the analysis freeze record's ``control_qualification`` block, and
before any treatment runs it must still recompute exactly from the control
corpus. It is never recomputed from treatment data.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from tools.research.v6.e4 import analysis_freeze as e4_freeze
from tools.research.v6.e4 import contest_classes as e4_contest_classes
from tools.research.v6.e4 import populations as e4_populations
from tools.research.v6.e4.analyze_e4 import FieldRun
from tools.research.v6.e5 import matrix
from tools.research.v6.e5.analyze_e5 import (
    ANCHOR_ONLY,
    CONTEST_CLASSES,
    SWEEP_BACKED,
    control_census,
    directed_units,
    evaluate_hypotheses,
    p_base,
    unit_rows,
)
from tools.research.v6.e5.cell_metrics import DEFINED
from tools.research.v6.e5.preregistration import MIN_SWEEP_BACKED_UNITS, load_preregistration

POPULATIONS_PATH = Path(__file__).with_name("control_populations.json")
POPULATIONS_SCHEMA = "bytefray.v6.e5.control_populations"
POPULATIONS_VERSION = 1

# O-P-PAR-E5: E4's committed populations record, pinned by E4 analysis freeze v1.
E4_POPULATIONS_PATH = e4_populations.POPULATIONS_PATH
E4_POPULATIONS_SHA256 = "56a8c1090b27929cb8b33fc861f385dacb8898d86e673ee6a42505e8eeef06c5"
E4_FREEZE_ID = matrix.HISTORICAL_FREEZE_ID


class PopulationsError(RuntimeError):
    """The frozen control populations are missing, altered, halted or no longer recompute."""


def p_par_e5() -> dict[str, Any]:
    """O-P-PAR-E5: E4's frozen primary-arm P-PAR units whose agents are both in the E5 field."""
    pinned = e4_freeze.load_freeze()["control_qualification"]["populations"]["sha256"]
    if pinned != E4_POPULATIONS_SHA256:
        raise PopulationsError(f"E4 freeze pins populations {pinned}, not {E4_POPULATIONS_SHA256}")
    record = e4_populations.load_record(E4_POPULATIONS_PATH, freeze_id=E4_FREEZE_ID,
                                        expected_sha256=E4_POPULATIONS_SHA256)
    frozen = list(record["arms"]["primary"]["p_par"])
    units = sorted(name for name in frozen
                   if all(matrix.primary_name(agent) in matrix.E5_AGENTS for agent in name.split("|")[1:]))
    return {
        "source": {"path": "tools/research/v6/e4/control_populations.json", "sha256": E4_POPULATIONS_SHA256,
                   "e4_freeze_id": E4_FREEZE_ID, "arm": "primary"},
        "e4_p_par_units": len(frozen),
        "units": units,
        "count": len(units),
    }


def _attacker(victim: str) -> str:
    return "B" if victim == "A" else "A"


def control_d_clauses(run: FieldRun, rows: Mapping[str, Mapping[str, Any]], p_base_units: list[str],
                      classes: Mapping[str, str]) -> dict[str, Any]:
    """D-5 (control side), D-6 and the inference sanity check over one control field."""
    d5_failures: list[str] = []
    for name in p_base_units:
        row = rows[name]
        if row["field"] != run.field_id or classes[name] != ANCHOR_ONLY:
            continue
        victims = ("A", "B") if row["victim"] == "AB" else (row["victim"],)
        for key in row["cells"]:
            e5 = run.row(key)["e5"]
            for victim in victims:
                if e5["bp"][victim]["status"] != DEFINED:
                    continue
                pair = f"{_attacker(victim)}->{victim}"
                if e5["directed"][pair]["default_anchor_core0_writes"] < 1:
                    d5_failures.append(f"{name}:{key}:{pair}")
    d6_failures = []
    incorrect_inferences = []
    for key in sorted(run.cells):
        telemetry = run.row(key)
        e5 = telemetry["e5"]
        hits = sum(item["unmoved_anchor_hits"] for item in e5["directed"].values())
        if hits > 0 and e5["d_gate"]["dual_writes"] <= 0:
            d6_failures.append(key)
        for seat in ("A", "B"):
            audit = telemetry["e3"]["seats"][seat]["capture"]["core_inference"]
            if audit is not None and audit["status"] == "inferred" and audit["correct"] is not True:
                incorrect_inferences.append(f"{key}:{seat}")
    return {"d5_control_failures": d5_failures, "d6_failures": d6_failures,
            "incorrect_control_inferences": incorrect_inferences}


def arm_record(runs: Mapping[str, FieldRun]) -> dict[str, Any]:
    """One arm's control populations, from its control runs alone."""
    rows = unit_rows(runs, runs)
    base = p_base(rows)
    classes = {name: rows[name]["contest_class"] for name in base}
    counts = Counter(classes.values())
    clauses = [control_d_clauses(runs[f], rows, base, classes) for f in matrix.FIELD_IDS]
    d_clauses = {name: sorted(item for clause in clauses for item in clause[name])
                 for name in ("d5_control_failures", "d6_failures", "incorrect_control_inferences")}
    census = control_census(rows)
    return {
        "units": {name: {k: v for k, v in row.items() if k not in ("treatment", "transition")}
                  for name, row in sorted(rows.items())},
        "directed_unit_count": sum(len(directed_units(runs[f])) for f in matrix.FIELD_IDS),
        "p_base": base,
        "contest_classes": dict(sorted(classes.items())),
        "counts": {"p_base": len(base), **{cls: counts.get(cls, 0) for cls in CONTEST_CLASSES}},
        "control_census": {k: v for k, v in census.items() if k != "near_boundary_units"},
        "control_d_clauses": {name: {"failures": items[:20], "count": len(items),
                                     "status": "PASS" if not items else "FAIL"} for name, items in d_clauses.items()},
    }


def build_record(*, freeze_id: str, preregistration_sha256: str, arms: Mapping[str, Mapping[str, FieldRun]]
                 ) -> dict[str, Any]:
    record_arms = {arm: arm_record(runs) for arm, runs in arms.items()}
    sb = record_arms[matrix.PRIMARY_ARM]["counts"][SWEEP_BACKED]
    record: dict[str, Any] = {
        "schema": POPULATIONS_SCHEMA,
        "version": POPULATIONS_VERSION,
        "matrix_id": matrix.matrix_id(),
        "freeze_id": freeze_id,
        "preregistration_sha256": preregistration_sha256,
        "p_par_e5": p_par_e5(),
        "arms": record_arms,
        "min_sweep_backed": {"required": MIN_SWEEP_BACKED_UNITS, "primary_arm": sb,
                             "status": "PASS" if sb >= MIN_SWEEP_BACKED_UNITS else "HALT"},
    }
    # Every hypothesis evaluated control against itself (E4's convention). E5-D
    # necessarily fails on control data (the spawn is on the core), so the
    # global-null signature -- H2 SUPPORTED, H1 REFUTED -- reads STOP, never R-H2
    # (review AF-11): the decoupling gate is what discriminates it.
    if sb:
        cvc = evaluate_hypotheses({arm: {"control": runs, "treatment": runs} for arm, runs in arms.items()},
                                  record, load_preregistration(), e4_contest_classes.load_table(), d_status="FAIL")
        record["control_vs_control_hypotheses"] = {
            "e5_d": "FAIL (control data: the spawn is on the core by construction)",
            "statuses": {h: cvc[h]["status"] for h in ("E5-H1", "E5-H2", "E5-H3", "E5-H4", "E5-H5")},
            "interpretation": cvc["interpretation"]["outcome"],
            "pathology_raised": [name for name, flag in cvc["pathology"].items() if flag["raised"]],
            "d9_completions": cvc["D9"]["t_e5_completions"],
        }
    return record


def canonical_bytes(record: Mapping[str, Any]) -> bytes:
    return (json.dumps(record, indent=2, sort_keys=True) + "\n").encode("utf-8")


def record_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def write_record(path: Path, record: Mapping[str, Any]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_bytes(record))
    return record_sha256(path)


def load_record(path: Path, *, freeze_id: str, expected_sha256: str | None) -> dict[str, Any]:
    """The committed populations record; fails closed unless it is the one the freeze names."""
    if not path.is_file():
        raise PopulationsError(f"No frozen E5 control populations at {path}.")
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
    if problems:
        raise PopulationsError(f"{path}: " + "; ".join(problems))
    return record


def require_recomputes(record: Mapping[str, Any], recomputed: Mapping[str, Any]) -> None:
    def norm(value: Any) -> Any:
        return json.loads(json.dumps(value, sort_keys=True))

    differing = [part for part in ("p_par_e5", "arms", "min_sweep_backed", "control_vs_control_hypotheses")
                 if norm(record[part]) != norm(recomputed[part])]
    if differing:
        raise PopulationsError(f"Frozen E5 control populations no longer recompute from the controls: {differing}")


def require_ready(record: Mapping[str, Any]) -> None:
    """Hard stops before treatment: the control census, the control-side E5-D clauses,
    correct control inferences, and O-MIN-SB."""
    problems = []
    for arm, body in record["arms"].items():
        if body["control_census"]["status"] != "PASS":
            problems.append(f"{arm}: control-vs-control census not 100% identity classes")
        for name, clause in body["control_d_clauses"].items():
            if clause["status"] != "PASS":
                problems.append(f"{arm}: {name} ({clause['count']})")
    cvc = record.get("control_vs_control_hypotheses") or {}
    if cvc.get("interpretation") != "STOP" or cvc.get("statuses", {}).get("E5-H1") != "REFUTED"             or cvc.get("statuses", {}).get("E5-H2") != "SUPPORTED":
        problems.append(f"control-vs-control hypotheses are not the global-null signature read as STOP: {cvc}")
    if record["min_sweep_backed"]["status"] != "PASS":
        problems.append(
            f"HALT: {record['min_sweep_backed']['primary_arm']} SWEEP-BACKED P-BASE units in the primary arm, "
            f"fewer than the required {record['min_sweep_backed']['required']} (O-MIN-SB); reassess the design")
    if problems:
        raise PopulationsError("STOP before treatment: " + "; ".join(problems))
