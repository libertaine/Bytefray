"""PA-7: per-cell mechanics from the stored callback rows, and per-unit mechanism tables.

Rows are E6's compact telemetry (``tools/research/v6/e6/telemetry.py``
``ROW_FIELDS``), one per callback in execution order, each verified against
its pinned ``rows_sha256`` before use (``corpus.Corpus.rows``). Definitions:

* **callbacks in a tick**: rows of that entrant in that tick. A tick with
  none is one in which the entrant was offered no callback, which for a
  single-process entrant means it was suppressed for every offer;
* **first detection**: the entrant's first row with a non-empty visible set;
* **first callback after the rival's detection**: the entrant's first row in
  a tick later than the rival's first-detection tick;
* **ADAPT's check** (plan P-4): an ADAPT row at callback index 1 that READs a
  cell of its own core; it finds damage when the owner read back is not
  ADAPT's own seat. Its cell is the read address minus the core base;
* **ADAPT's evasion**: the MOVE ADAPT makes at the callback right after a
  check that found damage (fixture ``agent.py:370-373``), which separates
  evasion from the fast-search MOVEs of its tick-17 hunt;
* **off-core MOVE**: an applied MOVE that takes the anchor from a cell of the
  entrant's own core to a cell outside it (the telemetry definition).

Only rows are read. ``WINDOW`` bounds the per-tick callback scan.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from tools.research.v6 import experiment_harness as harness
from tools.research.v6.e6 import family
from tools.research.v6.e6.telemetry import ROW_FIELDS
from tools.research.v6.e6_audit.corpus import CONDITIONS, Corpus

WINDOW = 12
CORE_SIZE = 8
#: ADAPT's no-contact switch tick (PR O-6): its hunt, and any search MOVE, starts at tick 17.
HUNT_SWITCH_TICK = 16
COL = {name: index for index, name in enumerate(ROW_FIELDS)}


@dataclass(frozen=True)
class Check:
    tick: int
    cell: int
    damaged: bool


@dataclass(frozen=True)
class CellMechanics:
    """What the rows show about one cell, per seat."""

    seats: Mapping[str, str]  # seat -> member
    result: str  # the winning seat, "tie" or "other"
    termination: str
    ticks_run: int
    saw_first: str | None  # seat
    first_detection: Mapping[str, int | None]
    callbacks: Mapping[str, Mapping[int, int]]  # seat -> tick -> callbacks, ticks 1..WINDOW
    first_callback_after_rival_detection: Mapping[str, int | None]
    silent_ticks_after_rival_detection: Mapping[str, tuple[int, ...]]
    first_off_core_move: Mapping[str, int | None]
    checks: Mapping[str, tuple[Check, ...]]  # ADAPT seats only
    evasion: Mapping[str, int | None]  # ADAPT seats only
    #: ADAPT MOVEs before its tick-17 hunt that are not the evasion. The fixture can
    #: move before tick 17 only to evade, so any count here falsifies the definition.
    unclassified_early_moves: Mapping[str, int]  # ADAPT seats only


def _in_core(address: int, base: int, arena: int) -> bool:
    return (address - base) % arena < CORE_SIZE


def cell_mechanics(cell: Mapping[str, Any], summary: Mapping[str, Any], rows: Sequence[Sequence[Any]]) -> CellMechanics:
    seat_ids = {"A": str(cell["seat_a_id"]), "B": str(cell["seat_b_id"])}
    seats = {seat: family.PACKAGES[pid][0] for seat, pid in seat_ids.items()}
    arena = int(summary["arena"])
    base = {seat: int(summary["core_base"][seat]) for seat in seats}
    rival = {"A": "B", "B": "A"}
    ticks_run = int(cell["ticks_run"])
    last = min(ticks_run, WINDOW)
    callbacks: dict[str, Counter[int]] = {seat: Counter() for seat in seats}
    first_detection: dict[str, int | None] = {seat: None for seat in seats}
    first_detection_order: dict[str, int | None] = {seat: None for seat in seats}
    first_off_core: dict[str, int | None] = {seat: None for seat in seats}
    checks: dict[str, list[Check]] = {seat: [] for seat in seats if seats[seat] == "ADAPT"}
    evasion: dict[str, int | None] = {seat: None for seat in checks}
    early_moves: dict[str, int] = {seat: 0 for seat in checks}
    previous_damaged: dict[str, bool] = {seat: False for seat in checks}
    ticks_with_rows: dict[str, set[int]] = {seat: set() for seat in seats}
    for order, row in enumerate(rows):
        tick, seat = int(row[COL["tick"]]), str(row[COL["entrant"]])
        kind, status = row[COL["kind"]], row[COL["status"]]
        ticks_with_rows[seat].add(tick)
        if tick <= WINDOW:
            callbacks[seat][tick] += 1
        if row[COL["visible"]] and first_detection[seat] is None:
            first_detection[seat], first_detection_order[seat] = tick, order
        applied = status == "APPLIED"
        if (kind == "move" and applied and first_off_core[seat] is None
                and _in_core(int(row[COL["anchor"]]), base[seat], arena)
                and not _in_core(int(row[COL["address"]]), base[seat], arena)):
            first_off_core[seat] = tick
        if seat in checks:
            is_check = (row[COL["index"]] == 1 and kind == "read" and applied
                        and _in_core(int(row[COL["address"]]), base[seat], arena))
            if kind == "move" and previous_damaged[seat] and evasion[seat] is None:
                evasion[seat] = tick
            elif kind == "move" and tick <= HUNT_SWITCH_TICK:
                early_moves[seat] += 1
            if is_check:
                damaged = row[COL["read_owner"]] != seat
                checks[seat].append(Check(tick, (int(row[COL["address"]]) - base[seat]) % arena, damaged))
                previous_damaged[seat] = damaged
            else:
                previous_damaged[seat] = False
    after: dict[str, int | None] = {}
    silent: dict[str, tuple[int, ...]] = {}
    for seat in seats:
        detected = first_detection[rival[seat]]
        if detected is None:
            after[seat], silent[seat] = None, ()
            continue
        later = sorted(t for t in ticks_with_rows[seat] if t > detected)
        after[seat] = later[0] if later else None
        silent[seat] = tuple(t for t in range(detected + 1, last + 1) if callbacks[seat][t] == 0)
    detected_orders = {seat: o for seat, o in first_detection_order.items() if o is not None}
    saw_first = min(detected_orders, key=lambda seat: detected_orders[seat]) if detected_orders else None
    return CellMechanics(
        seats=seats, result=harness.cell_seat_result(cell), termination=str(cell["termination_reason"]),
        ticks_run=ticks_run, saw_first=saw_first, first_detection=first_detection,
        callbacks={seat: {t: callbacks[seat][t] for t in range(1, last + 1)} for seat in seats},
        first_callback_after_rival_detection=after, silent_ticks_after_rival_detection=silent,
        first_off_core_move=first_off_core, checks={seat: tuple(c) for seat, c in checks.items()}, evasion=evasion,
        unclassified_early_moves=early_moves,
    )


# ---------------------------------------------------------------------------
# Selecting a unit's cells, and tabulating them by the first member's seat
# ---------------------------------------------------------------------------


def unit_cells(corpus: Corpus, condition: str, unit: str) -> list[tuple[str, dict[str, Any]]]:
    """The cells of a frozen unit in one condition, as (field, cell). Mirrors use candidate-first
    cells, as ``mirror_seat_metrics`` does (the other orientation is a relabeling, D-7)."""

    field_id, first, second = unit.split("|")
    out: list[tuple[str, dict[str, Any]]] = []
    for cell in corpus.cells[condition][field_id]:
        if field_id == "F1":
            belongs = {str(cell["seat_a_id"]), str(cell["seat_b_id"])} == {first, second}
        else:
            belongs = ((cell["subject_id"], cell["opponent_id"]) == (first, second)
                       and cell.get("orientation") == harness.ORIENTATION_CANDIDATE_FIRST)
        if belongs:
            out.append((field_id, cell))
    return out


def mechanics_for(corpus: Corpus, condition: str, unit: str) -> list[tuple[str, dict[str, Any], CellMechanics]]:
    """(first member's seat, cell, mechanics) for every cell of ``unit`` in ``condition``."""

    first_pid = unit.split("|")[1]
    out = []
    for field_id, cell in unit_cells(corpus, condition, unit):
        rows = corpus.rows(condition, field_id, str(cell["schedule_id"]))
        mech = cell_mechanics(cell, corpus.summaries[condition][field_id][str(cell["schedule_id"])]["summary"], rows)
        x_seat = "A" if str(cell["seat_a_id"]) == first_pid else "B"
        out.append((x_seat, cell, mech))
    return out


def _hist(values: Iterable[Any]) -> dict[str, int]:
    counter = Counter("none" if v is None else str(v) for v in values)
    return dict(sorted(counter.items(), key=lambda item: (item[0] == "none", len(item[0]), item[0])))


def unit_table(entries: Sequence[tuple[str, dict[str, Any], CellMechanics]]) -> dict[str, Any]:
    """The mechanism table of one unit in one condition, by the first member's seat (X)."""

    table: dict[str, Any] = {}
    for x_seat in ("A", "B"):
        rows = [(cell, m) for seat, cell, m in entries if seat == x_seat]
        if not rows:
            continue
        y_seat = "B" if x_seat == "A" else "A"
        outcome = Counter("X" if m.result == x_seat else ("Y" if m.result == y_seat else m.result) for _c, m in rows)
        block: dict[str, Any] = {
            "cells": len(rows),
            "outcome_for_X": {k: outcome.get(k, 0) for k in ("X", "tie", "Y", "other")},
            "termination": _hist(m.termination for _c, m in rows),
            "decision_tick_of_X_wins": _hist(m.ticks_run for _c, m in rows if m.result == x_seat),
            "decision_tick_of_Y_wins": _hist(m.ticks_run for _c, m in rows if m.result == y_seat),
            "saw_first": _hist({x_seat: "X", y_seat: "Y", None: None}[m.saw_first] for _c, m in rows),
            "first_detection": {"X": _hist(m.first_detection[x_seat] for _c, m in rows),
                                "Y": _hist(m.first_detection[y_seat] for _c, m in rows)},
            "first_callback_after_rival_detection": {
                "X": _hist(m.first_callback_after_rival_detection[x_seat] for _c, m in rows),
                "Y": _hist(m.first_callback_after_rival_detection[y_seat] for _c, m in rows)},
            "cells_with_silent_ticks_after_rival_detection": {
                "X": sum(bool(m.silent_ticks_after_rival_detection[x_seat]) for _c, m in rows),
                "Y": sum(bool(m.silent_ticks_after_rival_detection[y_seat]) for _c, m in rows)},
            "first_off_core_move": {"X": _hist(m.first_off_core_move[x_seat] for _c, m in rows),
                                    "Y": _hist(m.first_off_core_move[y_seat] for _c, m in rows)},
        }
        for role, seat in (("X", x_seat), ("Y", y_seat)):
            adapt_rows = [(c, m) for c, m in rows if seat in m.evasion]
            if not adapt_rows:
                continue
            first_checks = []
            for _c, m in adapt_rows:
                after = m.first_callback_after_rival_detection[seat]
                check = next((ch for ch in m.checks[seat] if after is not None and ch.tick >= after), None)
                first_checks.append(None if check is None else f"t{check.tick}:cell{check.cell}:{'damage' if check.damaged else 'own'}")
            block[f"adapt_{role}"] = {
                "first_check_after_contact": _hist(first_checks),
                "evasion_tick": _hist(m.evasion[seat] for _c, m in adapt_rows),
                "unclassified_early_moves": sum(m.unclassified_early_moves[seat] for _c, m in adapt_rows),
                "outcome_for_X_by_evasion": {
                    "evaded": _hist("X" if m.result == x_seat else ("Y" if m.result == y_seat else m.result)
                                    for _c, m in adapt_rows if m.evasion[seat] is not None),
                    "not_evaded": _hist("X" if m.result == x_seat else ("Y" if m.result == y_seat else m.result)
                                        for _c, m in adapt_rows if m.evasion[seat] is None),
                },
            }
        table[f"X@{x_seat}"] = block
    return table


def unit_tables(corpus: Corpus, units: Sequence[str]) -> dict[str, dict[str, Any]]:
    from tools.research.v6.e6_audit import seat

    return {seat.label(unit): {condition: unit_table(mechanics_for(corpus, condition, unit)) for condition in CONDITIONS}
            for unit in units}
