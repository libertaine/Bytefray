"""E8-D's clauses and control qualification CQ8 (PR8 Sec 5.1, 5.2 and 12; phase I8-5).

docs/research/v6/V6_E8_ACTIVE_SPATIAL_SENSING_PREREGISTRATION.md (PR8). Every
gate reads no gameplay outcome and returns a report whose ``status`` is PASS
or FAIL; a FAIL is a hard stop (PR8 Sec 12). A gate that checked nothing
FAILs: an empty gate is never a pass.

Each cell's rows (``traces.extract``) are read once, and every per-cell
clause is checked in that one pass (``check_cell``):

* **D8-1** (T8, T8L): ``rederive.rederive_cell`` re-derives every SENSE's
  status and tuple. **Presence** (all four conditions): ``sensed_anchors`` is
  on every SENSE record and no other, a list when applied and ``null``
  otherwise.
* **D8-2** (T8, T8L): every traced visible set is empty.
* **D8-4** (T8, T8L): at most 8 callbacks per entrant and tick, and the
  re-derivation aligns, so every SENSE occupies exactly one offer.
* **D8-5** (T8, T8L): the replay's byte write log equals the traced applied
  WRITEs, byte for byte and in order, and the re-derivation finds no position
  change or suppression a SENSE could explain.
* **D8-8** (all four): no WRITE to a cell of the opponent's core in ticks 1-2
  before the writer's entrant has had an information event. An event is a
  visible set or a delivered SENSE tuple holding an opponent anchor, or a
  delivered READ result showing an opponent-owned cell of its core. Each
  counts from the row whose observation delivers it, the first point at
  which the agent can know it.
* **D8-12** (all four): a schema-2 trace bound to the cell, and a
  ``decision_v2`` record for every callback the re-derivation predicts.
* **D8-13** (all four for presence, T8 and T8L for the reflection): the
  process's next callback after a SENSE record, on whatever tick, carries
  ``previous_sense_anchors`` equal to its ``sensed_anchors``; no other
  callback carries it.
* **D8-14** (all four): every status is ``APPLIED`` or
  ``REJECTED_OUT_OF_REACH``.
* **D8-15** (all four): every reset record carries ``sensing_window`` = 27
  under T8 and T8L, and omits it under C8 and C8L.

The cross-cell clauses: **D8-3** (LURK8 and GREED8 matched pairs), **D8-7**
(tick-0 distances, controls), **D8-11** (mirror relabeling), and CQ8-1 and
CQ8-2. D8-6 is the parent goldens, D8-9 ``discipline.py`` and D8-10
``seed_protocol.d8_10``. CQ8-3 is the family freeze, CQ8-4 ``analyze_e8`` with
``decision.control_against_control``, and CQ8-5 the strata
(``analyze_e8.seat_strata``).
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from tools.research.v6.e4.gates import tick_lines
from tools.research.v6.e6.rederive import circular_distance
from tools.research.v6.e8 import decision, family, matrix, rederive, traces
from tools.research.v6.e8.traces import ABSENT, COLUMN, TraceRecord
from tools.research.v6.experiment_harness import (
    ORIENTATION_CANDIDATE_FIRST,
    ORIENTATION_OPPONENT_FIRST,
    cell_seat_result,
    cell_seats,
)

GATES_VERSION = 1
PASS, FAIL = decision.PASS, decision.FAIL
SAMPLE_LIMIT = 10
ORDINARY_STATUSES = frozenset({"APPLIED", "REJECTED_OUT_OF_REACH"})
QUOTA = matrix.QUOTA
EARLY_TICKS = (1, 2)
#: CQ8-2's twin pairs: (the member compared, the twin, the twin's trigger).
CQ8_2_PAIRS: tuple[tuple[str, str, str], ...] = (("RUSH8", "REACQ8", "re-acquisition trigger"),
                                                 ("GUARD8", "EVADE8", "inferred hit"))
_C = COLUMN

Cell = Mapping[str, Any]
Row = Sequence[Any]


def _report(name: str, checked: int, failures: Sequence[Mapping[str, Any]], **extra: Any) -> dict[str, Any]:
    status = PASS if checked > 0 and not failures else FAIL
    return {"gate": name, "gates_version": GATES_VERSION, "checked": checked, "failures": len(failures),
            "failure_samples": list(failures[:SAMPLE_LIMIT]), "status": status, **extra}


def member_of(package: str) -> str | None:
    """A package's member, or None for a package outside the family (scripted test agents only)."""
    slot = family.PACKAGES.get(package)
    return None if slot is None else slot[0]


def cells_by_schedule(cells: Iterable[Cell]) -> dict[str, Cell]:
    table: dict[str, Cell] = {}
    for cell in cells:
        if cell["schedule_id"] in table:
            raise ValueError(f"duplicate schedule_id {cell['schedule_id']}")
        table[cell["schedule_id"]] = cell
    return table


# ---------------------------------------------------------------------------
# Per-cell clauses
# ---------------------------------------------------------------------------


def presence_sensed(rows: Sequence[Row]) -> list[dict[str, Any]]:
    """D8-1's presence: ``sensed_anchors`` on every SENSE record and no other, mapped by status."""
    out: list[dict[str, Any]] = []
    for order, row in enumerate(rows):
        sensed, kind, status = row[_C["sensed"]], row[_C["kind"]], row[_C["status"]]
        if kind != "sense":
            if sensed != ABSENT:
                out.append({"order": order, "reason": "sensed_anchors on a non-SENSE record"})
        elif sensed == ABSENT:
            out.append({"order": order, "reason": "a SENSE record without sensed_anchors"})
        elif status == "APPLIED" and not isinstance(sensed, list):
            out.append({"order": order, "reason": "an applied SENSE whose sensed_anchors is not a list"})
        elif status != "APPLIED" and sensed is not None:
            out.append({"order": order, "reason": f"a {status} SENSE whose sensed_anchors is not null"})
    return out


def delivery(rows: Sequence[Row]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], int]:
    """D8-13: (presence failures, reflection failures, obligations met).

    A delivery obligation falls on exactly one callback: the same process's
    next callback after a SENSE record, applied or refused, on whatever tick.
    """
    presence: list[dict[str, Any]] = []
    reflection: list[dict[str, Any]] = []
    owed: dict[tuple[str, str], Any] = {}
    met = 0
    for order, row in enumerate(rows):
        key = (row[_C["entrant"]], row[_C["process"]])
        delivered = row[_C["delivered"]]
        if key in owed:
            expected = owed.pop(key)
            if delivered == ABSENT:
                presence.append({"order": order, "reason": "a delivery obligation without previous_sense_anchors"})
            else:
                met += 1
                if delivered != expected:
                    reflection.append({"order": order, "expected": expected, "delivered": delivered})
        elif delivered != ABSENT:
            presence.append({"order": order, "reason": "previous_sense_anchors without a delivery obligation"})
        if row[_C["kind"]] == "sense":
            owed[key] = None if row[_C["sensed"]] == ABSENT else row[_C["sensed"]]
    return presence, reflection, met


def statuses(rows: Sequence[Row]) -> list[dict[str, Any]]:
    """D8-14: every status is APPLIED or REJECTED_OUT_OF_REACH; any other, or none, fails."""
    return [{"order": order, "status": row[_C["status"]]} for order, row in enumerate(rows)
            if row[_C["status"]] not in ORDINARY_STATUSES]


def window_fidelity(summary: Mapping[str, Any], *, active: bool) -> list[dict[str, Any]]:
    """D8-15: 27, explicitly, on every T8/T8L reset record; absent from every C8/C8L one."""
    out: list[dict[str, Any]] = []
    for entrant, windows in sorted(summary["reset_windows"].items()):
        if not windows:
            out.append({"entrant": entrant, "reason": "no reset record"})
        for value in windows:
            if active and not (isinstance(value, int) and not isinstance(value, bool)
                               and value == matrix.SENSING_WINDOW):
                out.append({"entrant": entrant, "window": value, "reason": "not 27 under an active Ruleset"})
            if not active and value != ABSENT:
                out.append({"entrant": entrant, "window": value, "reason": "present under a passive Ruleset"})
    return out


def callbacks_per_tick(rows: Sequence[Row]) -> list[dict[str, Any]]:
    """D8-4's count: no entrant has more than its quota of callbacks in a tick."""
    counts = Counter((row[_C["tick"]], row[_C["entrant"]]) for row in rows)
    return [{"tick": tick, "entrant": entrant, "callbacks": n} for (tick, entrant), n in sorted(counts.items())
            if n > QUOTA]


def early_blind_strikes(rows: Sequence[Row], core_base: Mapping[str, int], *, arena: int) -> tuple[list[dict[str, Any]], int]:
    """D8-8: (uninformed WRITEs to the opponent's core in ticks 1-2, all such WRITEs)."""
    entrants = sorted(core_base)
    rival = {entrants[0]: entrants[1], entrants[1]: entrants[0]}
    informed = dict.fromkeys(entrants, False)
    last: dict[tuple[str, str], Row] = {}
    failures: list[dict[str, Any]] = []
    writes = 0
    for order, row in enumerate(rows):
        entrant, key = row[_C["entrant"]], (row[_C["entrant"]], row[_C["process"]])
        opponent = rival[entrant]
        previous = last.get(key)
        delivered = row[_C["delivered"]]
        read_back = (previous is not None and previous[_C["kind"]] == "read" and previous[_C["status"]] == "APPLIED"
                     and traces.in_core(previous[_C["address"]], core_base[opponent], arena)
                     and previous[_C["read_owner"]] == opponent)
        if row[_C["visible"]] or (isinstance(delivered, list) and delivered) or read_back:
            informed[entrant] = True
        if (row[_C["kind"]] == "write" and row[_C["status"]] == "APPLIED" and row[_C["tick"]] in EARLY_TICKS
                and traces.in_core(row[_C["address"]], core_base[opponent], arena)):
            writes += 1
            if not informed[entrant]:
                failures.append({"order": order, "tick": row[_C["tick"]], "entrant": entrant,
                                 "address": row[_C["address"]]})
        last[key] = row
    return failures, writes


@dataclass
class CellResult:
    """Every per-cell clause for one cell; empty lists mean the clause holds for it."""

    schedule_id: str
    active: bool
    rederived: rederive.CellCheck | None
    presence_sensed: list[dict[str, Any]]
    delivery_presence: list[dict[str, Any]]
    delivery_reflection: list[dict[str, Any]]
    deliveries: int
    statuses: list[dict[str, Any]]
    windows: list[dict[str, Any]]
    over_quota: list[dict[str, Any]]
    visible: int
    write_log_equal: bool
    early: list[dict[str, Any]]
    early_writes: int
    binding_equal: bool
    sense_records: int
    streams: dict[str, str] = field(default_factory=dict)


def _projection(row: Row, fields: Sequence[str]) -> list[Any]:
    return [row[_C[name]] for name in fields]


#: D8-3's compared fields: the action and the observation's information fields.
D8_3_FIELDS: tuple[str, ...] = ("kind", "operand", "value", "visible", "delivered", "read_value_prev",
                                "read_owner_prev")
#: CQ8-2's compared fields: the action stream.
ACTION_FIELDS: tuple[str, ...] = ("kind", "operand", "value")


def stream_digest(rows: Sequence[Row], entrant: str, fields: Sequence[str], *, until: int | None = None) -> str:
    """The SHA-256 of one entrant's projected rows, in order, before its ``until``-th callback (0-based)."""
    mine = [_projection(row, fields) for row in rows if row[_C["entrant"]] == entrant]
    if until is not None:
        mine = mine[:until]
    return hashlib.sha256(json.dumps(mine, separators=(",", ":")).encode("utf-8")).hexdigest()


def reacquisition_trigger(rows: Sequence[Row], entrant: str) -> int | None:
    """CQ8-2: the 0-based index, among ``entrant``'s callbacks, of the first at which an address of its
    previous callback's visible set is absent from this one's (a tracked address becomes missing)."""
    tracked: list[int] | None = None
    index = 0
    for row in rows:
        if row[_C["entrant"]] != entrant:
            continue
        visible = list(row[_C["visible"]])
        if tracked is not None and any(address not in visible for address in tracked):
            return index
        tracked = visible
        index += 1
    return None


def inferred_hit(rows: Sequence[Row], entrant: str) -> int | None:
    """CQ8-2: the 0-based index of ``entrant``'s first callback at which EVADE8's rule infers a hit:
    at a first callback of a tick, a whole tick passed with no callback, or the most recent tick
    with any callback had fewer than 8; never at the first callback of the match (P8-5)."""
    previous_tick: int | None = None
    previous_count = 0
    current_tick: int | None = None
    count = 0
    index = 0
    for row in rows:
        if row[_C["entrant"]] != entrant:
            continue
        tick = row[_C["tick"]]
        if tick != current_tick:
            if current_tick is not None:
                previous_tick, previous_count = current_tick, count
            current_tick, count = tick, 0
            if previous_tick is not None and (tick > previous_tick + 1 or previous_count < QUOTA):
                return index
        count += 1
        index += 1
    return None


def check_cell(rows: Sequence[Row], summary: Mapping[str, Any], record: TraceRecord, cell: Cell, *,
               condition: matrix.Condition, arena: int = matrix.ARENA_SIZE) -> CellResult:
    """Every per-cell clause for one cell, from its rows, summary, trace record and harness cell."""
    active = condition.sensing_mode == "active"
    windows = window_fidelity(summary, active=active)
    rederived: rederive.CellCheck | None
    try:
        rederived = rederive.rederive_cell(rows, summary, ticks_run=int(cell["ticks_run"]), arena=arena,
                                           slot_limit=condition.disruption_slot_limit)
    except ValueError:
        rederived = None  # no single configured window: D8-15 already fails, and D8-1 cannot run
    presence, reflection, met = delivery(rows)
    early, early_writes = early_blind_strikes(rows, summary["core_base"], arena=arena)
    seat_a, seat_b = cell_seats(cell)
    streams: dict[str, str] = {}
    for seat, package in (("A", seat_a), ("B", seat_b)):
        member = member_of(package)
        if member in ("LURK8", "GREED8"):
            streams[f"d8_3:{seat}"] = stream_digest(rows, seat, D8_3_FIELDS)
        for _compared, twin, _ in CQ8_2_PAIRS:
            if member == twin:
                trigger = reacquisition_trigger(rows, seat) if twin == "REACQ8" else inferred_hit(rows, seat)
                streams[f"trigger:{seat}"] = json.dumps(trigger)
                streams[f"prefix:{seat}"] = stream_digest(rows, seat, ACTION_FIELDS, until=trigger)
    return CellResult(
        schedule_id=record.schedule_id,
        active=active,
        rederived=rederived,
        presence_sensed=presence_sensed(rows),
        delivery_presence=presence,
        delivery_reflection=reflection,
        deliveries=met,
        statuses=statuses(rows),
        windows=windows,
        over_quota=callbacks_per_tick(rows),
        visible=sum(1 for row in rows if row[_C["visible"]]),
        write_log_equal=(len(traces.trace_write_log(rows)) == summary["replay_writes"]
                         and traces.write_log_digest(traces.trace_write_log(rows))
                         == summary["replay_write_log_sha256"]),
        early=early,
        early_writes=early_writes,
        binding_equal=summary["bindings"] == [{"match_id": record.match_id, "replay_sha256": record.replay_sha256,
                                                "ruleset_id": record.ruleset_id}],
        sense_records=sum(1 for row in rows if row[_C["kind"]] == "sense"),
        streams=streams,
    )


# ---------------------------------------------------------------------------
# Field-level aggregation of the per-cell clauses
# ---------------------------------------------------------------------------

#: (member, opponent member, the member's seat, seed)
StreamKey = tuple[str, str, str, int]


@dataclass
class FieldChecks:
    field_root: Path
    condition_id: str
    field_id: str
    results: list[CellResult]
    expected_cells: int
    completed_cells: int
    #: CQ8-2: each twin's trigger index and its action-stream prefix before it.
    twin_prefixes: dict[StreamKey, dict[str, Any]] = field(default_factory=dict)
    #: CQ8-2: the trace record of each compared member's cell, re-read once the twin's trigger is known.
    compared_records: dict[StreamKey, TraceRecord] = field(default_factory=dict)


def check_field(field_root: Path, cells: Iterable[Cell], *, condition_id: str, field_id: str,
                expected_cells: int) -> FieldChecks:
    """Read every traced cell of one condition/field once and check every per-cell clause."""
    condition = matrix.condition(condition_id)
    by_schedule = cells_by_schedule(cells)
    summaries = {line["schedule_id"]: line["summary"] for line in traces.read_summaries(field_root)}
    records = traces.read_index(field_root)
    out = FieldChecks(field_root, condition_id, field_id, [], expected_cells,
                      len(traces.completed_cells(field_root)))
    for record in records:
        rows = traces.read_rows(field_root, record)
        cell = by_schedule[record.schedule_id]
        result = check_cell(rows, summaries[record.schedule_id], record, cell, condition=condition)
        out.results.append(result)
        if condition.role == matrix.CONTROL and field_id == "F1":
            seat_a, seat_b = cell_seats(cell)
            members = {"A": member_of(seat_a), "B": member_of(seat_b)}
            for seat, rival in (("A", "B"), ("B", "A")):
                key = (members[seat], members[rival], seat, int(cell["seed"]))
                for compared, twin, _ in CQ8_2_PAIRS:
                    if members[seat] == twin:
                        out.twin_prefixes[key] = {"trigger": json.loads(result.streams[f"trigger:{seat}"]),
                                                  "prefix": result.streams[f"prefix:{seat}"]}
                    elif members[seat] == compared:
                        out.compared_records[key] = record
    return out


def _flatten(checks: Sequence[FieldChecks], attribute: str) -> list[dict[str, Any]]:
    return [{"cell": result.schedule_id, **item} for chunk in checks for result in chunk.results
            for item in getattr(result, attribute)]


def d8_1(checks: Sequence[FieldChecks]) -> dict[str, Any]:
    """Exactness on T8/T8L (re-derivation), presence on all four conditions."""
    failures: list[dict[str, Any]] = []
    applied = refused = 0
    for chunk in checks:
        for result in chunk.results:
            if result.active:
                check = result.rederived
                if check is None or not check.passed:
                    failures.append({"cell": result.schedule_id, "rederived": None if check is None else {
                        "alignment": check.alignment_failures, "status": check.status_mismatches,
                        "sensing": check.sensing_mismatches, "move": check.move_mismatches,
                        "samples": list(check.samples[:3])}})
                else:
                    applied += check.senses_applied
                    refused += check.senses_refused
    failures += _flatten(checks, "presence_sensed")
    cells = sum(len(chunk.results) for chunk in checks)
    return _report("D8-1", cells, failures, applied_senses_rederived=applied, refused_senses_rederived=refused,
                   rederive_version=rederive.REDERIVE_VERSION)


def d8_2(checks: Sequence[FieldChecks]) -> dict[str, Any]:
    failures = [{"cell": r.schedule_id, "visible_callbacks": r.visible} for c in checks for r in c.results
                if r.active and r.visible]
    return _report("D8-2", sum(1 for c in checks for r in c.results if r.active), failures)


def d8_4(checks: Sequence[FieldChecks]) -> dict[str, Any]:
    failures = [{"cell": r.schedule_id, "over_quota": r.over_quota[:3],
                 "aligned": r.rederived is not None and r.rederived.alignment_failures == 0}
                for c in checks for r in c.results
                if r.active and (r.over_quota or r.rederived is None or r.rederived.alignment_failures)]
    senses = sum(r.sense_records for c in checks for r in c.results)
    return _report("D8-4", sum(1 for c in checks for r in c.results if r.active), failures, sense_records=senses)


def d8_5(checks: Sequence[FieldChecks]) -> dict[str, Any]:
    failures = [{"cell": r.schedule_id, "write_log_equal": r.write_log_equal,
                 "positions": None if r.rederived is None else r.rederived.move_mismatches}
                for c in checks for r in c.results
                if r.active and (not r.write_log_equal or r.rederived is None or r.rederived.move_mismatches)]
    return _report("D8-5", sum(1 for c in checks for r in c.results if r.active), failures)


def d8_8(checks: Sequence[FieldChecks]) -> dict[str, Any]:
    failures = _flatten(checks, "early")
    writes = sum(r.early_writes for c in checks for r in c.results)
    return _report("D8-8", sum(len(c.results) for c in checks), failures, early_core_writes=writes)


def d8_12(checks: Sequence[FieldChecks]) -> dict[str, Any]:
    failures: list[dict[str, Any]] = []
    for chunk in checks:
        traced = len(chunk.results)
        if not (traced == chunk.completed_cells == chunk.expected_cells):
            failures.append({"field": f"{chunk.condition_id}/{chunk.field_id}", "traced": traced,
                             "completed": chunk.completed_cells, "expected": chunk.expected_cells})
        for result in chunk.results:
            aligned = result.rederived is not None and result.rederived.alignment_failures == 0
            if not (result.binding_equal and aligned):
                failures.append({"cell": result.schedule_id, "binding": result.binding_equal, "aligned": aligned})
    return _report("D8-12", sum(len(c.results) for c in checks), failures)


def d8_13(checks: Sequence[FieldChecks]) -> dict[str, Any]:
    failures = _flatten(checks, "delivery_presence")
    failures += [{"cell": r.schedule_id, **item} for c in checks for r in c.results if r.active
                 for item in r.delivery_reflection]
    deliveries = sum(r.deliveries for c in checks for r in c.results)
    return _report("D8-13", sum(len(c.results) for c in checks), failures, deliveries_checked=deliveries)


def d8_14(checks: Sequence[FieldChecks]) -> dict[str, Any]:
    return _report("D8-14", sum(len(c.results) for c in checks), _flatten(checks, "statuses"))


def d8_15(checks: Sequence[FieldChecks]) -> dict[str, Any]:
    return _report("D8-15", sum(len(c.results) for c in checks), _flatten(checks, "windows"))


# ---------------------------------------------------------------------------
# Cross-cell clauses
# ---------------------------------------------------------------------------


def d8_3(checks: Sequence[FieldChecks], cells: Iterable[Cell], *, seeds: Sequence[int]) -> dict[str, Any]:
    """LURK8 and GREED8, the same opponent, seat and seed: equal action and information streams.

    ``seeds`` is the ordered seed list; D8-3's matched pairs are by seed position.
    """
    streams: dict[tuple[str, str, str, int], str] = {}
    by_schedule = {r.schedule_id: r for c in checks for r in c.results}
    for cell in cells:
        result = by_schedule.get(cell["schedule_id"])
        if result is None:
            continue
        seat_a, seat_b = cell_seats(cell)
        members = {"A": member_of(seat_a), "B": member_of(seat_b)}
        for seat, rival in (("A", "B"), ("B", "A")):
            if members[seat] in ("LURK8", "GREED8") and f"d8_3:{seat}" in result.streams:
                streams[(members[seat], members[rival], seat, int(cell["seed"]))] = result.streams[f"d8_3:{seat}"]
    failures: list[dict[str, Any]] = []
    pairs = decision.d8_3_matched_pairs()
    for pair in pairs:
        if pair.seed_position >= len(seeds):
            failures.append({"pair": [pair.opponent, pair.seat, pair.seed_position], "reason": "seed missing"})
            continue
        seed = seeds[pair.seed_position]
        lurk, greed = streams.get(("LURK8", pair.opponent, pair.seat, seed)), streams.get(
            ("GREED8", pair.opponent, pair.seat, seed))
        if lurk is None or greed is None:
            failures.append({"pair": [pair.opponent, pair.seat, pair.seed_position], "reason": "cell missing"})
        elif lurk != greed:
            failures.append({"pair": [pair.opponent, pair.seat, pair.seed_position], "reason": "streams differ"})
    return _report("D8-3", len(pairs), failures)


def d8_7(summaries: Sequence[Mapping[str, Any]], *, arena: int = matrix.ARENA_SIZE,
         radius: int = matrix.DETECTION_RADIUS) -> dict[str, Any]:
    """Under C8 and C8L, every opposing tick-0 anchor is more than 32 from every family process."""
    failures: list[dict[str, Any]] = []
    closest: int | None = None
    for line in summaries:
        anchors = line["summary"]["tick0_anchors"]
        for friendly in sorted(anchors):
            for enemy in sorted(anchors):
                if enemy == friendly:
                    continue
                for sensor in anchors[friendly].values():
                    for target in anchors[enemy].values():
                        distance = circular_distance(sensor, target, arena)
                        closest = distance if closest is None else min(closest, distance)
                        if distance <= radius:
                            failures.append({"cell": line["schedule_id"], "distance": distance})
    return _report("D8-7", len(summaries), failures, closest_distance=closest)


def mirror_sides(cells: Iterable[Cell]) -> dict[tuple[str, int], dict[str, Cell]]:
    """``(primary package, seed) -> {orientation: cell}`` for every twin-mirror cell (by the family table)."""
    out: dict[tuple[str, int], dict[str, Cell]] = {}
    for cell in cells:
        subject, opponent = str(cell["subject_id"]), str(cell["opponent_id"])
        member, role = family.PACKAGES[subject]
        if role != "primary" or family.PACKAGES[opponent] != (member, "twin"):
            continue
        out.setdefault((subject, int(cell["seed"])), {})[str(cell["orientation"])] = cell
    return out


def d8_11(field_root: Path, cells: Iterable[Cell], *, expected_units: int) -> dict[str, Any]:
    """Both orientations of every twin mirror seed: byte-identical replay tick records, the same winning seat."""
    sides = mirror_sides(cells)
    failures: list[dict[str, Any]] = []
    for (primary, seed), pair in sorted(sides.items()):
        first, second = pair.get(ORIENTATION_CANDIDATE_FIRST), pair.get(ORIENTATION_OPPONENT_FIRST)
        if first is None or second is None:
            failures.append({"mirror": member_of(primary), "reason": "orientation missing"})
            continue
        same_ticks = tick_lines(field_root / str(first["artifact_dir"]) / "replay.jsonl") == tick_lines(
            field_root / str(second["artifact_dir"]) / "replay.jsonl")
        same_seat = cell_seat_result(first) == cell_seat_result(second)
        if not (same_ticks and same_seat):
            failures.append({"mirror": member_of(primary), "reason": "tick records" if not same_ticks else "seat"})
    if len(sides) != expected_units:
        failures.append({"reason": f"{len(sides)} mirror seeds, {expected_units} expected"})
    return _report("D8-11", len(sides), failures)


def cq8_1(checks: Sequence[FieldChecks]) -> dict[str, Any]:
    """Zero SENSE records in every control trace, and D8-14 on the controls."""
    failures = [{"cell": r.schedule_id, "sense_records": r.sense_records} for c in checks for r in c.results
                if r.sense_records]
    failures += _flatten(checks, "statuses")
    return _report("CQ8-1", sum(len(c.results) for c in checks), failures)


def cq8_2(checks: Sequence[FieldChecks]) -> dict[str, Any]:
    """RUSH8 = REACQ8 before REACQ8's first trigger; GUARD8 = EVADE8 before EVADE8's first inferred hit.

    Every matched control F1 cell: the same opponent (neither of the pair), seat and seed.
    """
    failures: list[dict[str, Any]] = []
    comparisons = 0
    for chunk in checks:
        for compared, twin, trigger_name in CQ8_2_PAIRS:
            twins = {key: entry for key, entry in chunk.twin_prefixes.items() if key[0] == twin}
            for (_, opponent, seat, seed), entry in sorted(twins.items()):
                if opponent in (compared, twin):
                    continue
                comparisons += 1
                record = chunk.compared_records.get((compared, opponent, seat, seed))
                if record is None:
                    failures.append({"pair": [compared, twin], "opponent": opponent, "seat": seat,
                                     "reason": "the compared cell is missing"})
                    continue
                rows = traces.read_rows(chunk.field_root, record)
                if stream_digest(rows, seat, ACTION_FIELDS, until=entry["trigger"]) != entry["prefix"]:
                    failures.append({"pair": [compared, twin], "opponent": opponent, "seat": seat,
                                     trigger_name: entry["trigger"],
                                     "reason": "the action streams differ before the trigger"})
    return _report("CQ8-2", comparisons, failures)


def e8_d(clauses: Mapping[str, str]) -> dict[str, Any]:
    """E8-D = PASS if and only if every clause passes; final only once D8-10 is in."""
    registered = [f"D8-{n}" for n in range(1, 16)]
    if set(clauses) != set(registered):
        raise ValueError(f"E8-D needs exactly {registered}, got {sorted(clauses)}")
    if any(value not in (PASS, FAIL) for value in clauses.values()):
        raise ValueError(f"a clause status outside PASS/FAIL: {dict(clauses)}")
    status = PASS if all(clauses[name] == PASS for name in registered) else FAIL
    return {"clauses": {name: clauses[name] for name in registered}, "status": status}
