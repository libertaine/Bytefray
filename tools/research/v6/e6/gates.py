"""E6 gates: D-1, D-2, D-4 and D-7 of E6-D, and control qualification CQ-1.

docs/research/v6/V6_E6_PRICED_SENSING_PREREGISTRATION.md Sec 5.1-5.2. Each
gate reads no gameplay outcome and returns a report with ``status`` PASS or
FAIL. A FAIL is a hard stop (PR Sec 11). D-3 is the parent byte-identity
freeze and the control provenance, D-5 is ``discipline.py``, and D-6 is
``seeds.py``.

* **D-1 visibility** (Ruleset invariant): ``rederive.rederive_cell`` over
  every treatment cell.
* **D-2 initial invisibility** (Ruleset invariant): at tick 0, every
  opposing default-spawn anchor is more than 32 from every family sensor
  (from the replay's tick-0 snapshot).
* **D-4 no early blind strike** (family characterization): in ticks 1-2 no
  WRITE to a cell of the opponent's core comes before its entrant has had
  an information event.
* **D-7 mirror relabeling** (Ruleset invariant): both orientations of every
  twin mirror seed have byte-identical replay tick records, compared with
  E4's ``tick_lines``, unchanged, and the same winning seat. Mirrors are
  paired by the family table, since E6 package IDs are opaque and carry no
  ``_twin`` suffix.
* **CQ-1 search inertness** (control qualification): members that differ
  only in ``search`` produce identical callback streams in every matched
  control cell (same opponent, seed and orientation).
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from itertools import combinations
from pathlib import Path
from typing import Any

from tools.research.v6.e4.gates import tick_lines
from tools.research.v6.e6 import family, rederive, telemetry
from tools.research.v6.e6.traces import TraceRecord
from tools.research.v6.experiment_harness import (
    ORIENTATION_CANDIDATE_FIRST,
    ORIENTATION_OPPONENT_FIRST,
    cell_seat_result,
)

GATES_VERSION = 1
PASS = "PASS"
FAIL = "FAIL"
DETECTION_RADIUS = 32
SAMPLE_LIMIT = 10
#: Plan Sec 5.2 / PR Sec 5.2: the members that differ from each other only in ``search``.
SEARCH_VARIANTS: tuple[str, ...] = ("RUSH", "PACED", "STEALTH", "LURK")

Cell = Mapping[str, Any]


def _report(name: str, checked: int, failures: Sequence[Mapping[str, Any]], **extra: Any) -> dict[str, Any]:
    status = PASS if checked > 0 and not failures else FAIL
    return {"gate": name, "gates_version": GATES_VERSION, "checked": checked, "failures": len(failures),
            "failure_samples": list(failures[:SAMPLE_LIMIT]), "status": status, **extra}


def cells_by_schedule(cells: Iterable[Cell]) -> dict[str, Cell]:
    table: dict[str, Cell] = {}
    for cell in cells:
        if cell["schedule_id"] in table:
            raise ValueError(f"duplicate schedule_id {cell['schedule_id']}")
        table[cell["schedule_id"]] = cell
    return table


# ---------------------------------------------------------------------------
# D-1, D-2, D-4 (treatment cells)
# ---------------------------------------------------------------------------


def d1_visibility(field_root: Path, records: Sequence[TraceRecord], cells: Mapping[str, Cell], *,
                  arena: int, slot_limit: int | None, detection_radius: int = DETECTION_RADIUS) -> dict[str, Any]:
    summaries = {line["schedule_id"]: line["summary"] for line in telemetry.read_summaries(field_root)}
    failures: list[dict[str, Any]] = []
    callbacks = 0
    for record in records:
        check = rederive.rederive_cell(
            telemetry.read_callbacks(field_root, record), summaries[record.schedule_id],
            ticks_run=int(cells[record.schedule_id]["ticks_run"]), arena=arena,
            detection_radius=detection_radius, slot_limit=slot_limit)
        callbacks += check.callbacks
        if not check.passed:
            failures.append({"schedule_id": record.schedule_id, "visibility": check.visibility_mismatches,
                             "alignment": check.alignment_failures, "move": check.move_mismatches,
                             "samples": list(check.samples[:3])})
    return _report("D-1", len(records), failures, callbacks=callbacks,
                   rederive_version=rederive.REDERIVE_VERSION)


def d2_initial_invisibility(summaries: Sequence[Mapping[str, Any]], *, arena: int,
                            detection_radius: int = DETECTION_RADIUS) -> dict[str, Any]:
    failures: list[dict[str, Any]] = []
    closest: int | None = None
    for line in summaries:
        anchors = line["summary"]["tick0_anchors"]
        entrants = sorted(anchors)
        for friendly in entrants:
            for enemy in entrants:
                if enemy == friendly:
                    continue
                for sensor in anchors[friendly].values():
                    for target in anchors[enemy].values():
                        distance = rederive.circular_distance(sensor, target, arena)
                        closest = distance if closest is None else min(closest, distance)
                        if distance <= detection_radius:
                            failures.append({"schedule_id": line["schedule_id"], "sensor": sensor,
                                             "target": target, "distance": distance})
    return _report("D-2", len(summaries), failures, closest_distance=closest)


def d4_no_early_blind_strike(summaries: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    failures = [
        {"schedule_id": line["schedule_id"], **write}
        for line in summaries
        for write in line["summary"]["d4_writes"]
        if not write["informed"]
    ]
    writes = sum(len(line["summary"]["d4_writes"]) for line in summaries)
    return _report("D-4", len(summaries), failures, early_core_writes=writes)


# ---------------------------------------------------------------------------
# D-7 (F2 cells, every condition)
# ---------------------------------------------------------------------------


def mirror_sides(cells: Iterable[Cell]) -> dict[tuple[str, int], dict[str, Cell]]:
    """``(primary package, seed) -> {orientation: cell}`` for every twin-mirror cell."""
    out: dict[tuple[str, int], dict[str, Cell]] = {}
    for cell in cells:
        subject, opponent = str(cell["subject_id"]), str(cell["opponent_id"])
        member, role = family.PACKAGES[subject]
        if role != "primary" or family.PACKAGES[opponent] != (member, "twin"):
            continue
        out.setdefault((subject, int(cell["seed"])), {})[str(cell["orientation"])] = cell
    return out


def d7_mirror_relabeling(field_root: Path, cells: Iterable[Cell], *, expected_units: int) -> dict[str, Any]:
    sides = mirror_sides(cells)
    failures: list[dict[str, Any]] = []
    for (primary, seed), pair in sorted(sides.items()):
        first, second = pair.get(ORIENTATION_CANDIDATE_FIRST), pair.get(ORIENTATION_OPPONENT_FIRST)
        if first is None or second is None:
            failures.append({"mirror": primary, "seed": seed, "reason": "orientation missing"})
            continue
        same_ticks = tick_lines(field_root / str(first["artifact_dir"]) / "replay.jsonl") == tick_lines(
            field_root / str(second["artifact_dir"]) / "replay.jsonl")
        same_seat = cell_seat_result(first) == cell_seat_result(second)
        if not (same_ticks and same_seat):
            failures.append({"mirror": primary, "seed": seed, "reason": "tick records" if not same_ticks else "seat"})
    if len(sides) != expected_units:
        failures.append({"reason": f"{len(sides)} mirror seeds, {expected_units} expected"})
    return _report("D-7", len(sides), failures)


# ---------------------------------------------------------------------------
# CQ-1 (control cells)
# ---------------------------------------------------------------------------


def _stream_index(summaries: Iterable[Mapping[str, Any]]) -> dict[tuple[str, str, int], str]:
    """(seat A member, seat B member, seed) -> the cell's canonical callback-rows digest."""
    index: dict[tuple[str, str, int], str] = {}
    for line in summaries:
        key = (family.PACKAGES[line["seat_a"]][0], family.PACKAGES[line["seat_b"]][0], int(line["seed"]))
        if key in index:
            raise ValueError(f"duplicate control cell {key}")
        index[key] = line["rows_sha256"]
    return index


def cq1_search_inertness(summaries: Sequence[Mapping[str, Any]], *,
                         opponents: Sequence[str] = family.OPPONENTS,
                         variants: Sequence[str] = SEARCH_VARIANTS) -> dict[str, Any]:
    """Every matched control cell of two search variants has identical callback rows.

    Rows are compared through the SHA-256 of their canonical bytes
    (``telemetry.rows_bytes``), which is equal exactly when the streams are.
    """

    index = _stream_index(summaries)
    seeds = sorted({seed for _, _, seed in index})
    failures: list[dict[str, Any]] = []
    comparisons = 0
    for x, y in combinations(variants, 2):
        for opponent in opponents:
            if opponent in (x, y):
                continue
            for seed in seeds:
                for left, right in (((x, opponent, seed), (y, opponent, seed)),
                                    ((opponent, x, seed), (opponent, y, seed))):
                    comparisons += 1
                    if left not in index or right not in index:
                        failures.append({"cells": [list(left), list(right)], "reason": "cell missing"})
                    elif index[left] != index[right]:
                        failures.append({"cells": [list(left), list(right)], "reason": "callback streams differ"})
    return _report("CQ-1", comparisons, failures)
