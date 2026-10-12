"""V6 E5 qualification and treatment gates (review Sec L; Revision 1 Sec R2).

Reads artifacts only; executes nothing.

* **Parent reproduction.** A re-run control and the preserved E4 control
  corpus it must reproduce (C-E5 <- C-E4, C-E5K1 <- C-E4K1) run under the same
  Ruleset id, so nothing is excused. E4's frozen comparison is reused
  unchanged (every harness cell field including ``match_id`` and
  ``result_id``, ``result.json`` minus occurrence metadata, the replay bytes,
  the E3 telemetry and the E4 metrics on both copies); the E5 metrics are then
  compared on both copies too.
* **E5-D, treatment side** (Revision 1 Sec R2). Per treatment cell: D-1 every
  tick-0 anchor is ``pc - 1`` (spawn mode ``before_core``); D-2 no hostile
  write to a still-unmoved default anchor is a core write; D-3 DUAL = 0; D-4
  no process on its own core. Per ANCHOR-ONLY P-BASE unit: D-5 no D-2-type
  write by the attacker to the victim's cell 0. The control side of D-5 and
  D-6 is frozen with the populations.
* **Manipulation checks** (G.4 and the analyzer cross-checks) reuse E4's
  ``manipulation_checks`` with forward passes; the **relabel gate** and
  **corpus integrity** are E4's, unchanged; **D9** is the G.5 stop.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

from tools.research.v6.e3.gates import D9_VICTIMS
from tools.research.v6.e4 import gates as e4_gates
from tools.research.v6.e5 import matrix

record_sha256 = e4_gates.record_sha256
corpus_integrity = e4_gates.corpus_integrity
relabel_gate = e4_gates.relabel_gate
require_relabel = e4_gates.require_relabel
field_keys = e4_gates.field_keys


class TreatmentGateError(RuntimeError):
    """A treatment corpus failed a hard-stop gate."""


class DecouplingGateError(TreatmentGateError):
    """E5-D failed: the treatment or the classification is defective (STOP)."""


class D9StopError(TreatmentGateError):
    """A capture completion against a repair or disrupt guard under T-E5 (a theorem violation)."""


def field_orientations(field_id: str) -> tuple[str, ...]:
    return e4_gates.ORIENTATIONS if matrix.field(field_id).both_orientations else ("candidate_first",)


def compare_parent_subset(
    new_root: Path,
    historical_root: Path,
    *,
    new_rows: Mapping[str, Mapping[str, Any]],
    historical_rows: Mapping[str, Mapping[str, Any]],
    sample_limit: int = 10,
) -> dict[str, Any]:
    """E4's strict parent comparison, plus the E5 metrics on both copies."""
    result = e4_gates.compare_parent_subset(new_root, historical_root, new_rows=new_rows,
                                            historical_rows=historical_rows, sample_limit=sample_limit)
    differing = sorted(
        key for key, row in new_rows.items()
        if "telemetry" not in row or "telemetry" not in (historical_rows.get(key) or {})
        or row["telemetry"]["e5"] != historical_rows[key]["telemetry"]["e5"]
    )
    if differing:
        reasons = dict(result["mismatch_reasons"])
        reasons["e5_metrics"] = len(differing)
        result.update({"mismatch_count": result["mismatch_count"] + len(differing),
                       "mismatch_reasons": dict(sorted(reasons.items())),
                       "status": "FAIL"})
        result["mismatch_samples"] = (result["mismatch_samples"] + [
            {"cell": key, "reason": "e5_metrics"} for key in differing])[:sample_limit]
    result["compared"] = [*result["compared"], "E5 BP and decoupling metrics on both copies"]
    return result


# ---------------------------------------------------------------------------
# E5-D, treatment side
# ---------------------------------------------------------------------------

D_CELL_CLAUSES: tuple[str, ...] = ("D-1", "D-2", "D-3", "D-4")


def decoupling_cell_checks(rows: Mapping[str, Mapping[str, Any]], *, sample_limit: int = 10) -> dict[str, Any]:
    """D-1 .. D-4 over one treatment field's E5 telemetry rows."""
    counts: Counter[str] = Counter()
    samples: list[dict[str, Any]] = []
    for key, row in sorted(rows.items()):
        telemetry = row.get("telemetry")
        found: list[str] = []
        if telemetry is None:
            found.append("analyzer_failure")
        else:
            gate = telemetry["e5"]["d_gate"]
            if gate["spawn_mode"] != matrix.BEFORE_CORE:
                found.append("D-1")
            if gate["default_dual_writes"] != 0:
                found.append("D-2")
            if gate["dual_writes"] != 0:
                found.append("D-3")
            if gate["own_core_occupancy"] != 0:
                found.append("D-4")
        for name in found:
            counts[name] += 1
        if found and len(samples) < sample_limit:
            samples.append({"cell": key, "failed": found})
    return {"cells": len(rows), "violations": dict(sorted(counts.items())), "violation_samples": samples,
            "status": "PASS" if rows and not counts else "FAIL"}


def _attacker(victim: str) -> str:
    return "B" if victim == "A" else "A"


def decoupling_contest_check(
    treatment_rows: Mapping[str, Mapping[str, Mapping[str, Any]]],
    frozen_units: Mapping[str, Mapping[str, Any]],
    p_base: Sequence[str],
    classes: Mapping[str, str],
) -> dict[str, Any]:
    """D-5, treatment side: every ANCHOR-ONLY P-BASE unit has no D-2-type write by
    its attacker to its victim's cell 0 in any treatment cell."""
    failures: list[str] = []
    checked = 0
    for name in p_base:
        if classes[name] != "ANCHOR-ONLY":
            continue
        unit = frozen_units[name]
        victims = ("A", "B") if unit["victim"] == "AB" else (unit["victim"],)
        for key in unit["cells"]:
            row = treatment_rows[unit["field"]].get(key) or {}
            if "telemetry" not in row:
                failures.append(f"{name}:{key}:missing")
                continue
            for victim in victims:
                checked += 1
                if row["telemetry"]["e5"]["directed"][f"{_attacker(victim)}->{victim}"]["default_anchor_core0_writes"]:
                    failures.append(f"{name}:{key}:{victim}")
    return {"anchor_only_directed_cells": checked, "failures": failures[:20], "failure_count": len(failures),
            "status": "PASS" if checked and not failures else "FAIL"}


def require_decoupling(report: Mapping[str, Any]) -> None:
    if report.get("status") != "PASS":
        raise DecouplingGateError(f"STOP: E5-D failed: {report}")


# ---------------------------------------------------------------------------
# Manipulation checks and D9
# ---------------------------------------------------------------------------


def manipulation_checks(rows: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    """E4's hard stops 5-7 with forward passes: clean telemetry, the cpu_used
    cross-check, capture agreement, the E4 reconstruction, no zero-action live
    tick, no exclusive tick and no G.4 violation. E5 metrics' own cross-checks too."""
    report = e4_gates.manipulation_checks(rows, mirrored=False)
    e5_failures = sorted(key for key, row in rows.items()
                         if "telemetry" in row and not row["telemetry"]["e5"]["checks"]["ok"])
    if e5_failures:
        report["violations"] = {**report["violations"], "e5_check_failure": len(e5_failures)}
        report["status"] = "FAIL"
    return report


def d9_completions(rows: Mapping[str, Mapping[str, Any]], field_id: str) -> list[dict[str, Any]]:
    return [{"field": field_id, "cell": key, **completion} for key, row in sorted(rows.items())
            if "telemetry" in row for completion in row["telemetry"]["e3"]["completions"]
            if completion["victim_name"] in D9_VICTIMS]


def require_d9(condition_id: str, completions: Iterable[Mapping[str, Any]]) -> None:
    found = list(completions)
    if condition_id == matrix.PRIMARY_TREATMENT and found:
        raise D9StopError(
            f"D9 violation under {condition_id}: {len(found)} capture completion(s) against a repair or disrupt "
            f"guard, e.g. {found[:3]}. G.5 is a theorem; STOP and re-qualify the implementation."
        )
