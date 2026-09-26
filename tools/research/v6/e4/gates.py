"""V6 E4 qualification and treatment gates (design review Sec Q, Sec R).

Reads artifacts only; executes nothing.

* **Parent reproduction** (Sec Q, hard stop 2). A re-run control and the
  preserved E3 treatment corpus it must reproduce (C-E4 <- T-E3, C-E4K1 <-
  T-E3K1) run under the same Ruleset id, so nothing is excused. The E4 field
  is a subset of E3's (no ``e2_counter``; F2-P in one orientation), so the
  comparison covers exactly the E4 cells: every harness cell field including
  ``match_id`` and ``result_id``, the whole ``result.json`` apart from its
  per-execution occurrence metadata, the replay bytes (SHA-256), the E3
  telemetry (capture and action/parity), and the E4 metrics computed on both
  copies. E3's per-cell comparison helpers are reused unchanged.
* **E3 continuity** (Sec Q): the E3 telemetry the E4 analyzer computes on a
  re-run control must equal E3's frozen telemetry cell for cell.
* **Relabel gate** (hard stop 9): a twin mirror's two orientations must have
  byte-identical replay tick records and the same winning seat.
* **Manipulation checks** (hard stops 5 and 6) and the **D9' stop check**
  (hard stop 8), for the future treatment.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

from tools.research.v6 import experiment_harness as harness
from tools.research.v6.e2.requalification import ORIENTATIONS, _cells, _key, _load
from tools.research.v6.e3.gates import (
    CELL_FIELDS,
    artifact_dir,
    comparable_telemetry,
    file_sha256,
    index_cells,
    load_cells,
    result_without_occurrence,
)
from tools.research.v6.e4 import matrix

RELABEL_GATE_VERSION = 1
G4_PRIME_MIN = 5


class ParentReproductionError(RuntimeError):
    """The re-run controls did not reproduce their historical parents."""


class RelabelGateError(RuntimeError):
    """A twin-mirror orientation pair is not a pure relabelling."""


class TreatmentGateError(RuntimeError):
    """A treatment corpus failed a hard-stop gate."""


class D9PrimeStopError(TreatmentGateError):
    """A capture completion against a repair or disrupt guard under T-E4 (a theorem violation)."""


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def field_keys(root: Path) -> set[str]:
    return set(index_cells(load_cells(root)))


# ---------------------------------------------------------------------------
# Parent reproduction and E3 continuity
# ---------------------------------------------------------------------------


def compare_parent_subset(
    new_root: Path,
    historical_root: Path,
    *,
    new_rows: Mapping[str, Mapping[str, Any]],
    historical_rows: Mapping[str, Mapping[str, Any]],
    sample_limit: int = 10,
) -> dict[str, Any]:
    """Deep, strict comparison of one field of a re-run control with the E4-field
    cells of its historical parent. ``*_rows`` are E4 telemetry rows by cell key."""
    new = index_cells(load_cells(new_root))
    old = index_cells(load_cells(historical_root))
    reasons: Counter[str] = Counter()
    samples: list[dict[str, Any]] = []

    def fail(key: str, reason: str, detail: Any = None) -> None:
        reasons[reason] += 1
        if len(samples) < sample_limit:
            samples.append({"cell": key, "reason": reason, "detail": detail})

    for key in sorted(new):
        a, b = new[key], old.get(key)
        if b is None:
            fail(key, "missing_in_historical")
            continue
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
        row_a, row_b = new_rows.get(key) or {}, historical_rows.get(key) or {}
        if "telemetry" not in row_a or "telemetry" not in row_b:
            fail(key, "telemetry_missing_or_failed", [row_a.get("error"), row_b.get("error")])
            continue
        if comparable_telemetry(row_a["telemetry"]["e3"]) != comparable_telemetry(row_b["telemetry"]["e3"]):
            fail(key, "e3_telemetry")
            continue
        if row_a["telemetry"]["e4"] != row_b["telemetry"]["e4"]:
            fail(key, "e4_metrics")
    ok = bool(new) and not reasons
    return {
        "cells_compared": len(new),
        "historical_cells_in_parent_field": len(old),
        "mismatch_count": sum(reasons.values()),
        "mismatch_reasons": dict(sorted(reasons.items())),
        "mismatch_samples": samples,
        "compared": ["cell fields incl. match_id and result_id", "result.json minus occurrence metadata",
                     "replay SHA-256", "E3 action/parity and capture telemetry", "E4 FMA/FPS metrics on both copies"],
        "status": "PASS" if ok else "FAIL",
    }


def e3_continuity(
    new_rows: Mapping[str, Mapping[str, Any]],
    frozen_e3_rows: Mapping[str, Mapping[str, Any]],
    *,
    sample_limit: int = 10,
) -> dict[str, Any]:
    """The E3 telemetry of every re-run control cell equals E3's frozen telemetry row."""
    differing: list[str] = []
    missing: list[str] = []
    for key, row in sorted(new_rows.items()):
        frozen = frozen_e3_rows.get(key)
        if frozen is None or "telemetry" not in frozen or "telemetry" not in row:
            missing.append(key)
        elif comparable_telemetry(row["telemetry"]["e3"]) != comparable_telemetry(frozen["telemetry"]):
            differing.append(key)
    ok = bool(new_rows) and not differing and not missing
    return {"cells": len(new_rows), "differing": len(differing), "missing": len(missing),
            "samples": (differing + missing)[:sample_limit], "status": "PASS" if ok else "FAIL"}


def corpus_integrity(
    root: Path,
    *,
    ruleset_id: str,
    pairs: Sequence[tuple[str, str]],
    seeds: Sequence[int],
    orientations: Sequence[str],
    provenance: Mapping[str, Any],
    fingerprints: Mapping[str, str],
) -> dict[str, Any]:
    """E2's ``requalification.corpus_integrity`` checks, with the field's own orientation set.

    The E2 function is frozen and always expects both orientations; E4's F2-P runs
    one. Every check is otherwise the E2 one, using its own helpers: the exact cell
    set with no duplicates or extras, every cell completed with its artifacts and the
    condition's Ruleset, on-disk match directories equal to the recorded cells, the
    recorded provenance and the frozen fingerprints."""
    unknown = sorted(set(orientations) - set(ORIENTATIONS))
    if unknown:
        raise ValueError(f"unknown orientations {unknown}")
    problems: list[str] = []
    data = _load(root / "experiment_result.json")
    recorded = _load(root / "provenance.json")
    if data.get("provenance") != recorded:
        problems.append("experiment_result provenance differs from provenance.json")
    cells = _cells(root)
    keys = Counter(_key(cell) for cell in cells)
    expected = {(a, b, seed, o) for a, b in pairs for seed in seeds for o in orientations}
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


def field_orientations(field_id: str) -> tuple[str, ...]:
    return ORIENTATIONS if matrix.field(field_id).both_orientations else (harness.ORIENTATION_CANDIDATE_FIRST,)


# ---------------------------------------------------------------------------
# Relabel gate
# ---------------------------------------------------------------------------


def tick_lines(replay: Path) -> list[str]:
    """The raw ``tick`` records of one replay, byte for byte."""
    lines = []
    with replay.open("r", encoding="utf-8") as handle:
        for raw in handle:
            if raw.strip() and json.loads(raw).get("record_type") == "tick":
                lines.append(raw.rstrip("\n"))
    return lines


def mirror_pairs(root: Path) -> dict[tuple[str, int], dict[str, Mapping[str, Any]]]:
    """``(primary, seed) -> {orientation: cell}`` for every twin-mirror cell of one field."""
    out: dict[tuple[str, int], dict[str, Mapping[str, Any]]] = {}
    for cell in load_cells(root):
        subject, opponent = str(cell["subject_id"]), str(cell["opponent_id"])
        if opponent == matrix.twin_of(subject):
            out.setdefault((subject, int(cell["seed"])), {})[str(cell["orientation"])] = cell
    return out


def relabel_gate(root: Path, *, sample_limit: int = 10) -> dict[str, Any]:
    """O-RELABEL over one field: both orientations of every mirror seed have
    byte-identical tick records and the same winning seat."""
    failures: list[dict[str, Any]] = []
    pairs = mirror_pairs(root)
    for (primary, seed), sides in sorted(pairs.items()):
        first = sides.get(harness.ORIENTATION_CANDIDATE_FIRST)
        second = sides.get(harness.ORIENTATION_OPPONENT_FIRST)
        if first is None or second is None:
            failures.append({"mirror": primary, "seed": seed, "reason": "orientation missing"})
            continue
        same_ticks = tick_lines(artifact_dir(root, first) / "replay.jsonl") == tick_lines(
            artifact_dir(root, second) / "replay.jsonl")
        same_seat = harness.cell_seat_result(first) == harness.cell_seat_result(second)
        if not (same_ticks and same_seat):
            failures.append({"mirror": primary, "seed": seed, "reason": "tick records" if not same_ticks else "seat"})
    ok = bool(pairs) and not failures
    return {"gate_version": RELABEL_GATE_VERSION, "pairs": len(pairs), "failures": len(failures),
            "failure_samples": failures[:sample_limit], "status": "PASS" if ok else "FAIL"}


def require_relabel(reports: Mapping[str, Mapping[str, Any]]) -> None:
    failed = sorted(name for name, report in reports.items() if report.get("status") != "PASS")
    if failed:
        raise RelabelGateError(f"STOP: the twin-mirror relabel identity fails in {failed}; no mirror metric is computed.")


# ---------------------------------------------------------------------------
# Treatment manipulation checks and the D9' stop check
# ---------------------------------------------------------------------------


def manipulation_checks(rows: Mapping[str, Mapping[str, Any]], *, mirrored: bool) -> dict[str, Any]:
    """O-G4-PRIME / hard stops 5-7 over one field's E4 telemetry rows.

    Always: clean telemetry, the cpu_used cross-check, capture agreement, the
    E4 reconstruction, no zero-action live tick and no exclusive tick (lambda =
    1). Under ``mirrored``: every entrant alive throughout a tick executes at
    least 5 actions in both roles, and the final chunk belongs to the first mover."""
    counts: Counter[str] = Counter()
    samples: list[dict[str, Any]] = []
    for key, row in sorted(rows.items()):
        telemetry = row.get("telemetry")
        found: list[str] = []
        if telemetry is None:
            found.append("analyzer_failure")
        else:
            e3, e4 = telemetry["e3"], telemetry["e4"]
            checks = e3["checks"]
            if not checks["cpu_statistics_match"]:
                found.append("cpu_used_mismatch")
            if not (checks["capture_reconstruction_agrees"] and checks["capture_consistent_with_engine"]
                    and checks["capture_attribution_ok"]):
                found.append("capture_disagreement")
            if not e4["checks"]["ok"]:
                found.append("e4_check_failure")
            seats = e3["seats"].values()
            if any(seat["zero_action_live_ticks"] for seat in seats):
                found.append("zero_action_live_tick")
            if e3["exclusive_ticks"]:
                found.append("exclusive_tick")
            if any(seat["g4_violations"] for seat in seats):
                found.append("g4_violation")
            if mirrored:
                minimum = [seat["roles"][role]["min_executed_alive_throughout"] for seat in seats
                           for role in ("first", "second")]
                if any(value is not None and value < G4_PRIME_MIN for value in minimum):
                    found.append("g4_prime_violation")
                if e4["final_chunk_owner_role"] not in (None, "first"):
                    found.append("final_chunk_owner")
        for name in found:
            counts[name] += 1
        if found and len(samples) < 10:
            samples.append({"cell": key, "failed": found})
    return {"cells": len(rows), "mirrored": mirrored, "violations": dict(sorted(counts.items())),
            "violation_samples": samples, "status": "PASS" if rows and not counts else "FAIL"}


def require_d9_prime(condition_id: str, completions: Iterable[Mapping[str, Any]]) -> None:
    """Hard stop 8: a D9' violation in the primary treatment is an implementation defect."""
    found = list(completions)
    if condition_id == matrix.PRIMARY_TREATMENT and found:
        raise D9PrimeStopError(
            f"D9' violation under {condition_id}: {len(found)} capture completion(s) against a repair or disrupt "
            f"guard, e.g. {found[:3]}. G.5' is a theorem; STOP and re-qualify the implementation."
        )


def record_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
