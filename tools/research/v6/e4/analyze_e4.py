"""V6 E4 analysis (design review Sec M, Sec N, Sec P; ``preregistration.json``).

Pure functions over loaded field runs: the harness cell records of one
condition/field and each cell's E4 telemetry (E3 action/parity telemetry plus
the E4 cell metrics). Nothing here executes a match or reads a treatment
artifact by itself; ``run_e4`` decides what may be loaded.

* **Units** (Sec M.3, O-UNIT): an ordered matchup (field, Seat-A agent,
  Seat-B agent) for round-robin pairs; for a twin mirror, one unit per mirror
  whose observations are its seeds (the candidate-first cell of each seed; the
  duplicate orientation is only the relabel gate).
* **FMA per unit** (O-MATCHUP-MEDIAN): the median of the defined cell FMAs,
  exact; ``DECIDED-EARLY`` when fewer than half of the unit's cells have one.
* **Transition classes** (Sec M.2, O-TRANSITION): control band -> treatment
  band, a partition in a registered precedence.
* **Census** (Sec P rule 2): counts of unit characterizations, each carrying
  its n_distinct of (C key, T key) transitions (Sec P rule 1).
* **Seat metrics** (Sec M.1, O-SEAT-METRICS) for round-robin pairings and
  mirrors, and the mirror claims at 1000 and 1001 ticks (O-MIRROR-CLAIM).
* **E4-H0 .. E4-H8 and D9'** and the mechanical reading of the
  interpretation table (O-STATUS, O-INTERPRETATION).
"""

from __future__ import annotations

import statistics
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from fractions import Fraction
from typing import Any

from tools.research.v6 import experiment_harness as harness
from tools.research.v6.e3.analyze_e3 import outcome_class
from tools.research.v6.e3.gates import D9_VICTIMS, cell_key
from tools.research.v6.e4 import contest_classes, matrix
from tools.research.v6.e4.cell_metrics import (
    DEFINED,
    FIRST_SIDE,
    NEUTRAL,
    band_side,
    band_strength,
    exact_text,
    fma_band,
    parse_exact,
)

E4_ANALYSIS_VERSION = 1

SUPPORTED = "SUPPORTED"
REFUTED = "REFUTED"
NEITHER = "NEITHER"
NOT_EVALUABLE = "NOT_EVALUABLE"
STOP = "STOP"
HOLDS = "HOLDS"
TICK_LIMIT_PARITY_DEPENDENT = "TICK_LIMIT_PARITY_DEPENDENT"
PARITY_ROBUST = "AGREES_AT_1000_AND_1001"

# Sec M.2 transition classes (matchup level, control -> treatment, on FMA bands).
NEUTRALIZED = "NEUTRALIZED"
FOLLOWS_FINAL = "FOLLOWS-FINAL"
STAYS = "STAYS"
WEAKENED = "WEAKENED"
STRENGTHENED = "STRENGTHENED"
NEW = "NEW"
UNCHANGED_NEUTRAL = "UNCHANGED-NEUTRAL"
FIRST_SIDE_CONTROL = "FIRST-SIDE-CONTROL"
DECIDED_EARLY_CLASS = "DECIDED-EARLY"
TRANSITION_CLASSES: tuple[str, ...] = (
    NEUTRALIZED, FOLLOWS_FINAL, STAYS, WEAKENED, STRENGTHENED, NEW, UNCHANGED_NEUTRAL, FIRST_SIDE_CONTROL,
    DECIDED_EARLY_CLASS,
)
# O-CONTROL-CENSUS: the only classes a control compared with itself may produce.
IDENTITY_CLASSES: frozenset[str] = frozenset({STAYS, UNCHANGED_NEUTRAL, FIRST_SIDE_CONTROL, DECIDED_EARLY_CLASS})

MATCHUP = "matchup"
MIRROR = "mirror"

# O-MIRROR-CLAIM thresholds: E2/E3's seat-determination level (0.9) for a
# seat-dominant claim, H7's SCD level (0.5) for a seed-conditioned claim.
SEAT_DOMINANT_MIN = Fraction(9, 10)
SEED_CONDITIONED_MIN = Fraction(1, 2)

Cell = Mapping[str, Any]
Row = Mapping[str, Any]


@dataclass(frozen=True)
class FieldRun:
    """One condition/field: harness cells and E4 telemetry rows, both by cell key."""

    condition_id: str
    field_id: str
    cells: Mapping[str, Cell]
    telemetry: Mapping[str, Row]

    def row(self, key: str) -> Mapping[str, Any]:
        row = self.telemetry.get(key) or {}
        if "telemetry" not in row:
            raise ValueError(f"{self.condition_id}/{self.field_id} {key}: no telemetry ({row.get('error')})")
        telemetry: Mapping[str, Any] = row["telemetry"]
        return telemetry

    def e3(self, key: str) -> Mapping[str, Any]:
        value: Mapping[str, Any] = self.row(key)["e3"]
        return value

    def e4(self, key: str) -> Mapping[str, Any]:
        value: Mapping[str, Any] = self.row(key)["e4"]
        return value


def make_field_run(condition_id: str, field_id: str, cells: Iterable[Cell], telemetry: Mapping[str, Row]) -> FieldRun:
    return FieldRun(condition_id, field_id, {cell_key(cell): cell for cell in cells}, dict(telemetry))


def _fraction(numerator: int, denominator: int) -> Fraction | None:
    return None if denominator == 0 else Fraction(numerator, denominator)


def _float(value: Fraction | None) -> float | None:
    return None if value is None else round(float(value), 6)


def evidence(n_distinct: int) -> dict[str, Any]:
    return {
        "n_distinct": n_distinct,
        "evidence": harness.evidence_label(n_distinct),
        "rate_claim_eligible": n_distinct >= harness.MIN_DISTINCT_FOR_RATE_CLAIM,
    }


# ---------------------------------------------------------------------------
# Units
# ---------------------------------------------------------------------------


def is_twin_pair(first: str, second: str) -> bool:
    return second == matrix.twin_of(first) or first == matrix.twin_of(second)


def _seed(cell: Cell) -> int:
    return int(cell["seed"])


def unit_key(field_id: str, seat_a: str, seat_b: str) -> str:
    return f"{field_id}|{seat_a}|{seat_b}"


def unit_kind(seat_a: str, seat_b: str) -> str:
    return MIRROR if is_twin_pair(seat_a, seat_b) else MATCHUP


def units(run: FieldRun) -> dict[str, list[str]]:
    """Unit key -> its cell keys in seed order (O-UNIT).

    A round-robin pairing gives two ordered matchups (one per orientation); a
    twin mirror gives one unit of its candidate-first cells."""
    out: dict[str, list[tuple[int, str]]] = {}
    for key, cell in run.cells.items():
        subject, opponent = str(cell["subject_id"]), str(cell["opponent_id"])
        if is_twin_pair(subject, opponent):
            if cell.get("orientation") != harness.ORIENTATION_CANDIDATE_FIRST:
                continue
            name = unit_key(run.field_id, subject, opponent)
        else:
            seat_a, seat_b = harness.cell_seats(cell)
            name = unit_key(run.field_id, seat_a, seat_b)
        out.setdefault(name, []).append((_seed(cell), key))
    return {name: [key for _, key in sorted(rows)] for name, rows in sorted(out.items())}


def unit_agents(name: str) -> tuple[str, str, str]:
    field_id, seat_a, seat_b = name.split("|")
    return field_id, seat_a, seat_b


# ---------------------------------------------------------------------------
# FMA per unit and transitions
# ---------------------------------------------------------------------------


def fma_summary(run: FieldRun, keys: Sequence[str]) -> dict[str, Any]:
    """O-MATCHUP-MEDIAN: the unit's median cell FMA, or DECIDED-EARLY."""
    values: list[Fraction] = []
    for key in keys:
        fma = run.e4(key)["fma"]
        if fma["status"] == DEFINED:
            values.append(parse_exact(fma["exact"]))
    cells = len(keys)
    if not values or 2 * len(values) < cells:
        return {"cells": cells, "defined": len(values), "decided_early_cells": cells - len(values),
                "status": DECIDED_EARLY_CLASS, "median": None, "median_exact": None, "band": None, "side": None}
    median = Fraction(statistics.median(values))
    band = fma_band(median)
    return {"cells": cells, "defined": len(values), "decided_early_cells": cells - len(values), "status": DEFINED,
            "median": round(float(median), 6), "median_exact": exact_text(median), "band": band,
            "side": band_side(band)}


def transition_class(control: Mapping[str, Any], treatment: Mapping[str, Any]) -> str:
    """Sec M.2 classes in the O-TRANSITION precedence, so they partition the units."""
    if control["status"] == DECIDED_EARLY_CLASS or treatment["status"] == DECIDED_EARLY_CLASS:
        return DECIDED_EARLY_CLASS
    c_band, t_band = control["band"], treatment["band"]
    c_side, t_side = band_side(c_band), band_side(t_band)
    if c_side == FIRST_SIDE:
        return FIRST_SIDE_CONTROL
    if c_side is None:
        return UNCHANGED_NEUTRAL if t_band == NEUTRAL else NEW
    # control last-side
    if t_band == NEUTRAL:
        return NEUTRALIZED
    if t_side == FIRST_SIDE:
        return FOLLOWS_FINAL
    if t_band == c_band:
        return STAYS
    return WEAKENED if band_strength(t_band) < band_strength(c_band) else STRENGTHENED


def _median_float(values: Sequence[float]) -> float | None:
    return None if not values else round(float(statistics.median(values)), 6)


def unit_rows(
    control: Mapping[str, FieldRun],
    treatment: Mapping[str, FieldRun] | None,
    table: Mapping[str, Any],
    fields: Sequence[str] = matrix.FIELD_IDS,
) -> dict[str, dict[str, Any]]:
    """Every unit of the given fields: its contest class, control (and treatment)
    FMA summary, transition, FPS and PM-1 medians, and evidence. With no
    treatment, the control is summarized alone."""
    out: dict[str, dict[str, Any]] = {}
    for field_id in fields:
        c_run = control[field_id]
        t_run = treatment[field_id] if treatment is not None else None
        for name, keys in units(c_run).items():
            _, seat_a, seat_b = unit_agents(name)
            c_summary = fma_summary(c_run, keys)
            row: dict[str, Any] = {
                "unit": name,
                "field": field_id,
                "kind": unit_kind(seat_a, seat_b),
                "seat_a": seat_a,
                "seat_b": seat_b,
                "contest_class": contest_classes.class_of(table, field_id, seat_a, seat_b),
                "cells": list(keys),
                "control": {**c_summary, **_pm1(c_run, keys)},
            }
            if t_run is None:
                row["n_distinct_control"] = len({harness.trajectory_key(c_run.cells[k]) for k in keys})
            else:
                missing = [k for k in keys if k not in t_run.cells]
                if missing:
                    raise ValueError(f"{name}: treatment lacks cells {missing[:3]}")
                t_summary = fma_summary(t_run, keys)
                row["treatment"] = {**t_summary, **_pm1(t_run, keys)}
                row["transition"] = transition_class(c_summary, t_summary)
                row.update(evidence(len({(harness.trajectory_key(c_run.cells[k]), harness.trajectory_key(t_run.cells[k]))
                                         for k in keys})))
            out[name] = row
    return out


def _pm1(run: FieldRun, keys: Sequence[str]) -> dict[str, Any]:
    """Continuity readings per unit: PM-1 (E3, unchanged) and FPS medians, swing counts."""
    fms, fps, swings = [], [], []
    statuses: Counter[str] = Counter()
    for key in keys:
        parity = run.e3(key)["parity"]
        statuses[parity["status"]] += 1
        swings.append(parity["swing_ticks"])
        if parity["scoreable"]:
            fms.append(parity["fms"])
        e4 = run.e4(key)
        if e4["fps"]["value"] is not None:
            fps.append(e4["fps"]["value"])
    return {"pm1_status": dict(sorted(statuses.items())), "median_fms": _median_float(fms),
            "median_fps": _median_float(fps), "median_swing_ticks": _median_float(swings)}


def census(rows: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Sec P rule 2: counts of unit characterizations, with their evidence labels."""
    items = list(rows)
    classes = Counter(row["transition"] for row in items)
    return {
        "units": len(items),
        "classes": {name: classes.get(name, 0) for name in TRANSITION_CLASSES},
        "rate_claim_eligible_units": sum(1 for row in items if row.get("rate_claim_eligible")),
        "deterministic_characterizations": sum(1 for row in items if row.get("n_distinct") == 1),
    }


def control_census(rows: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    """O-CONTROL-CENSUS: a control compared with itself; every unit must be an identity class."""
    items = list(rows.values())
    non_identity = [row["unit"] for row in items if row["transition"] not in IDENTITY_CLASSES]
    return {**census(items), "non_identity_units": non_identity,
            "status": "PASS" if items and not non_identity else "FAIL"}


def p_par(control_rows: Mapping[str, Mapping[str, Any]]) -> list[str]:
    """O-P-PAR: standard-field units whose control median FMA band is non-neutral."""
    return sorted(
        name for name, row in control_rows.items()
        if row["field"] in matrix.STANDARD_FIELDS and row["control"]["status"] == DEFINED
        and row["control"]["band"] != NEUTRAL
    )


# ---------------------------------------------------------------------------
# Seat metrics (Sec M.1)
# ---------------------------------------------------------------------------


def _entrant_winner(cell: Cell) -> str | None:
    return harness.cell_winner(cell)


def pairing_seat_metrics(run: FieldRun, first: str, second: str) -> dict[str, Any]:
    """O-SEAT-METRICS for one round-robin pairing {X, Y}: XY puts X in Seat A."""
    xy: dict[int, Cell] = {}
    yx: dict[int, Cell] = {}
    for cell in run.cells.values():
        seat_a, seat_b = harness.cell_seats(cell)
        if (seat_a, seat_b) == (first, second):
            xy[_seed(cell)] = cell
        elif (seat_a, seat_b) == (second, first):
            yx[_seed(cell)] = cell
    seeds = sorted(set(xy) & set(yx))
    if not seeds or set(xy) != set(yx):
        raise ValueError(f"{run.field_id} {first} v {second}: orientations do not pair by seed")
    dsc = ec = os_ = consistent = consistent_a = a_wins = b_wins = 0
    for seed in seeds:
        w_xy, w_yx = harness.cell_seat_result(xy[seed]), harness.cell_seat_result(yx[seed])
        e_xy, e_yx = _entrant_winner(xy[seed]), _entrant_winner(yx[seed])
        a_wins += (w_xy == harness.SEAT_A) + (w_yx == harness.SEAT_A)
        b_wins += (w_xy == harness.SEAT_B) + (w_yx == harness.SEAT_B)
        if w_xy == w_yx and w_xy in (harness.SEAT_A, harness.SEAT_B):
            dsc += 1
            consistent += 1
            consistent_a += w_xy == harness.SEAT_A
        if e_xy == e_yx and e_xy is not None:
            ec += 1
        if e_xy != e_yx:
            os_ += 1
    s = len(seeds)
    sdi = Fraction(dsc, s)
    p_a = _fraction(consistent_a, consistent)
    sb = None if p_a is None else abs(2 * p_a - 1)
    sdom = Fraction(0) if sb is None else sdi * sb
    scd = Fraction(0) if sb is None else sdi * (1 - sb)
    legacy = harness.seat_determination_index([*xy.values(), *yx.values()])
    return {
        "kind": MATCHUP,
        "pairing": [first, second],
        "seeds": s,
        "sdi": _float(sdi),
        "ec": _float(Fraction(ec, s)),
        "os": _float(Fraction(os_, s)),
        "gsb": _float(Fraction(a_wins - b_wins, 2 * s)),
        "p_a": _float(p_a),
        "sb": _float(sb),
        "sdom": _float(sdom),
        "scd": _float(scd),
        "exact": {"sdi": exact_text(sdi), "gsb": exact_text(Fraction(a_wins - b_wins, 2 * s)),
                  "sdom": exact_text(sdom), "scd": exact_text(scd)},
        "legacy_sdi": legacy["sdi"],
        **evidence(legacy["n_distinct"]),
    }


def mirror_seat_metrics(run: FieldRun, primary: str, twin: str) -> dict[str, Any]:
    """O-SEAT-METRICS for one twin mirror: the unit is the seed (candidate-first cells)."""
    cells = {
        _seed(cell): cell for cell in run.cells.values()
        if (cell["subject_id"], cell["opponent_id"]) == (primary, twin)
        and cell.get("orientation") == harness.ORIENTATION_CANDIDATE_FIRST
    }
    seeds = sorted(cells)
    if not seeds:
        raise ValueError(f"{run.field_id}: no candidate-first cells for the {primary} mirror")
    results = [harness.cell_seat_result(cells[seed]) for seed in seeds]
    a_wins, b_wins = results.count(harness.SEAT_A), results.count(harness.SEAT_B)
    decisive = a_wins + b_wins
    s = len(seeds)
    share = Fraction(decisive, s)
    p_a = _fraction(a_wins, decisive)
    sb = None if p_a is None else abs(2 * p_a - 1)
    sdom = Fraction(0) if sb is None else share * sb
    scd = Fraction(0) if sb is None else share * (1 - sb)
    metrics = {
        "kind": MIRROR,
        "pairing": [primary, twin],
        "seeds": s,
        "decisive_share": _float(share),
        "gsb": _float(Fraction(a_wins - b_wins, s)),
        "p_a": _float(p_a),
        "sb": _float(sb),
        "sdom": _float(sdom),
        "scd": _float(scd),
        "a_seeds": a_wins,
        "b_seeds": b_wins,
        "exact": {"gsb": exact_text(Fraction(a_wins - b_wins, s)), "sdom": exact_text(sdom),
                  "scd": exact_text(scd)},
        **evidence(len({harness.trajectory_key(cells[seed]) for seed in seeds})),
    }
    metrics["claim"] = list(mirror_claim(metrics))
    return metrics


def mirror_claim(metrics: Mapping[str, Any]) -> tuple[str, str | None]:
    """O-MIRROR-CLAIM: seat-dominant (with its seat), seed-conditioned, or neither."""
    sdom, scd = parse_exact(metrics["exact"]["sdom"]), parse_exact(metrics["exact"]["scd"])
    if sdom >= SEAT_DOMINANT_MIN:
        p_a = metrics["p_a"]
        return "seat_dominant", ("A" if p_a is not None and p_a > 0.5 else "B")
    if scd >= SEED_CONDITIONED_MIN:
        return "seed_conditioned", None
    return "not_seat_determined", None


def present_pairs(run: FieldRun) -> list[tuple[str, str]]:
    """The field's frozen pairs that have cells in this run (all of them in a complete,
    integrity-checked corpus)."""
    seen = {(str(cell["subject_id"]), str(cell["opponent_id"])) for cell in run.cells.values()}
    return [pair for pair in matrix.field(run.field_id).pairs if pair in seen]


def seat_units(run: FieldRun) -> dict[str, dict[str, Any]]:
    """Seat metrics for every pairing of one field (mirrors by seed)."""
    out: dict[str, dict[str, Any]] = {}
    for first, second in present_pairs(run):
        if is_twin_pair(first, second):
            out[f"{run.field_id}|{first}|{second}"] = mirror_seat_metrics(run, first, second)
        elif run.field_id != "F2-P":
            out[f"{run.field_id}|{first}|{second}"] = pairing_seat_metrics(run, first, second)
    return out


def mirror_parity(run_1000: FieldRun, run_1001: FieldRun) -> list[dict[str, Any]]:
    """O-MIRROR-CLAIM / H8: each mirror's claim at 1000 (F2) and 1001 (F2-P) ticks."""
    rows = []
    for primary, twin in present_pairs(run_1000):
        a = mirror_seat_metrics(run_1000, primary, twin)
        b = mirror_seat_metrics(run_1001, primary, twin)
        rows.append({
            "mirror": [primary, twin],
            "claim_1000": a["claim"],
            "claim_1001": b["claim"],
            "gsb_1000": a["gsb"],
            "gsb_1001": b["gsb"],
            "label": PARITY_ROBUST if a["claim"] == b["claim"] else TICK_LIMIT_PARITY_DEPENDENT,
        })
    return rows


# ---------------------------------------------------------------------------
# Cell sets for H4-H6 and D9'
# ---------------------------------------------------------------------------


def exposed_keys(run: FieldRun) -> list[str]:
    """O-EXPOSED: cells in which a live entrant lost an offer (E3's exposure)."""
    return sorted(key for key in run.cells if run.e3(key)["exposed"])


def is_capture(cell: Cell) -> bool:
    """O-CAPTURE: some entrant's termination is a core capture."""
    return "core_captured" in (cell.get("entrant_terminations") or {}).values()


def is_tick_limit(cell: Cell) -> bool:
    return cell.get("termination_reason") == harness.TICK_LIMIT_REASON


def multi_pass_keys(run: FieldRun, keys: Iterable[str], table: Mapping[str, Any]) -> list[str]:
    out = []
    for key in keys:
        cell = run.cells[key]
        if contest_classes.class_of(table, run.field_id, str(cell["subject_id"]), str(cell["opponent_id"])) == \
                contest_classes.MULTI_PASS:
            out.append(key)
    return sorted(out)


def outcome_change(control: FieldRun, treatment: FieldRun, keys: Sequence[str]) -> dict[str, Any]:
    changed = sum(1 for k in keys if outcome_class(control.cells[k]) != outcome_class(treatment.cells[k]))
    distinct = {(harness.trajectory_key(control.cells[k]), harness.trajectory_key(treatment.cells[k])) for k in keys}
    share = _fraction(changed, len(keys))
    return {"cells": len(keys), "changed": changed, "share": _float(share),
            "share_exact": None if share is None else exact_text(share), **evidence(len(distinct))}


def d9_completions(run: FieldRun) -> list[dict[str, Any]]:
    """Capture completions whose victim is a repair or disrupt guard (or twin)."""
    out = []
    for key in sorted(run.cells):
        for completion in run.e3(key)["completions"]:
            if completion["victim_name"] in D9_VICTIMS:
                out.append({"field": run.field_id, "cell": key, **completion})
    return out


# ---------------------------------------------------------------------------
# Hypotheses and interpretation
# ---------------------------------------------------------------------------


def _share(count: int, total: int) -> dict[str, Any]:
    value = _fraction(count, total)
    return {"count": count, "of": total, "share": _float(value), "share_exact": None if value is None else exact_text(value)}


def _ge(count: int, total: int, threshold: Fraction) -> bool:
    return total > 0 and Fraction(count, total) >= threshold


def _le(count: int, total: int, threshold: Fraction) -> bool:
    return total > 0 and Fraction(count, total) <= threshold


def _status(total: int, supported: bool, refuted: bool) -> str:
    if total == 0:
        return NOT_EVALUABLE
    if supported:
        return SUPPORTED
    if refuted:
        return REFUTED
    return NEITHER


def _thresholds(criterion: Mapping[str, Any], name: str) -> Fraction:
    return Fraction(str(criterion[name]))


def evaluate_hypotheses(
    arms: Mapping[str, Mapping[str, Mapping[str, FieldRun]]],
    frozen: Mapping[str, Any],
    prereg: Mapping[str, Any],
    table: Mapping[str, Any],
) -> dict[str, Any]:
    """E4-H0 .. E4-H8 and D9' (O-STATUS).

    ``arms[arm]`` is ``{"control": runs, "treatment": runs}`` by field;
    ``frozen`` is the frozen control-populations record's ``arms`` block."""
    criteria = {item["id"]: item["criterion"] for item in prereg["hypotheses"]}
    primary = arms[matrix.PRIMARY_ARM]
    companion = arms.get(matrix.COMPANION_ARM)
    rows = unit_rows(primary["control"], primary["treatment"], table)
    ppar = list(frozen[matrix.PRIMARY_ARM]["p_par"])
    ppar_rows = [rows[name] for name in ppar]
    by_class = {cls: [row for row in ppar_rows if row["contest_class"] == cls] for cls in contest_classes.CLASSES}
    multi, opening = by_class[contest_classes.MULTI_PASS], by_class[contest_classes.OPENING_ONLY]

    def count(items: Sequence[Mapping[str, Any]], *classes: str) -> int:
        return sum(1 for row in items if row["transition"] in classes)

    out: dict[str, Any] = {}
    # H1
    c1 = criteria["E4-H1"]
    nw, ff_all = count(multi, NEUTRALIZED, WEAKENED), count(ppar_rows, FOLLOWS_FINAL)
    out["E4-H1"] = {
        "multi_pass_neutralized_or_weakened": _share(nw, len(multi)),
        "p_par_follows_final": _share(ff_all, len(ppar_rows)),
        "status": _status(len(multi),
                          _ge(nw, len(multi), _thresholds(c1, "multi_pass_neutralized_or_weakened_min"))
                          and _le(ff_all, len(ppar_rows), _thresholds(c1, "follows_final_overall_max")),
                          _le(nw, len(multi), _thresholds(c1, "refuted_multi_pass_neutralized_or_weakened_max"))),
    }
    # H2
    c2 = criteria["E4-H2"]
    ff_mp = count(multi, FOLLOWS_FINAL)
    out["E4-H2"] = {
        "multi_pass_follows_final": _share(ff_mp, len(multi)),
        "status": _status(len(multi), _ge(ff_mp, len(multi), _thresholds(c2, "multi_pass_follows_final_min")),
                          _le(ff_mp, len(multi), _thresholds(c2, "refuted_multi_pass_follows_final_max"))),
    }
    # H3
    c3 = criteria["E4-H3"]
    stays = count(opening, STAYS)
    out["E4-H3"] = {
        "opening_only_stays": _share(stays, len(opening)),
        "status": _status(len(opening), _ge(stays, len(opening), _thresholds(c3, "opening_only_stays_min")),
                          _le(stays, len(opening), _thresholds(c3, "refuted_opening_only_stays_max"))),
    }
    # H0 (after H1: it requires H1 refuted)
    c0 = criteria["E4-H0"]
    unchanged = count(ppar_rows, STAYS, UNCHANGED_NEUTRAL)
    share_ok = _ge(unchanged, len(ppar_rows), _thresholds(c0, "stays_or_unchanged_neutral_min"))
    out["E4-H0"] = {
        "p_par_stays_or_unchanged_neutral": _share(unchanged, len(ppar_rows)),
        "requires_h1": out["E4-H1"]["status"],
        "status": _status(len(ppar_rows), share_ok and out["E4-H1"]["status"] == REFUTED, not share_ok),
    }
    for key in ("E4-H0", "E4-H1", "E4-H2", "E4-H3"):
        out[key]["population"] = "P-PAR"
    out["p_par_census"] = {"all": census(ppar_rows), **{cls: census(items) for cls, items in by_class.items()}}

    # H4-H6: exposed F1 cells, frozen from each arm's control.
    p_ctrl, p_trt = primary["control"]["F1"], primary["treatment"]["F1"]
    p_exposed = list(frozen[matrix.PRIMARY_ARM]["exposed_f1"])
    p_multi = multi_pass_keys(p_ctrl, p_exposed, table)
    c4 = criteria["E4-H4"]
    primary_change = outcome_change(p_ctrl, p_trt, p_multi)
    if companion is not None:
        k_ctrl, k_trt = companion["control"]["F1"], companion["treatment"]["F1"]
        k_multi = multi_pass_keys(k_ctrl, list(frozen[matrix.COMPANION_ARM]["exposed_f1"]), table)
        companion_change = outcome_change(k_ctrl, k_trt, k_multi)
        comp_n, comp_c = companion_change["cells"], companion_change["changed"]
        h4_status = _status(
            comp_n,
            _ge(comp_c, comp_n, _thresholds(c4, "companion_change_share_min"))
            and _le(primary_change["changed"], primary_change["cells"], _thresholds(c4, "primary_change_share_max")),
            _le(comp_c, comp_n, _thresholds(c4, "refuted_companion_change_share_max")),
        )
    else:
        companion_change, h4_status = None, NOT_EVALUABLE
    out["E4-H4"] = {"primary": primary_change, "companion": companion_change, "status": h4_status}
    c5 = criteria["E4-H5"]
    non_capture = [k for k in p_exposed if not is_capture(p_ctrl.cells[k])]
    became = sum(1 for k in non_capture if is_capture(p_trt.cells[k]))
    out["E4-H5"] = {
        "control_non_capture_exposed_f1": _share(became, len(non_capture)),
        **evidence(len({(harness.trajectory_key(p_ctrl.cells[k]), harness.trajectory_key(p_trt.cells[k]))
                        for k in non_capture})),
        "status": _status(len(non_capture), _ge(became, len(non_capture), _thresholds(c5, "become_captures_min")),
                          not _ge(became, len(non_capture), _thresholds(c5, "become_captures_min"))),
    }
    c6 = criteria["E4-H6"]
    tl_c = sum(1 for k in p_exposed if is_tick_limit(p_ctrl.cells[k]))
    tl_t = sum(1 for k in p_exposed if is_tick_limit(p_trt.cells[k]))
    rise = _fraction(tl_t - tl_c, len(p_exposed))
    neutralized = [row for row in rows.values() if row["transition"] == NEUTRALIZED]
    static = sum(1 for row in neutralized
                 if row["treatment"]["median_swing_ticks"] is not None
                 and row["treatment"]["median_swing_ticks"] < c6["static_swing_ticks_below"])
    out["E4-H6"] = {
        "exposed_f1_tick_limit_share_control": _share(tl_c, len(p_exposed)),
        "exposed_f1_tick_limit_share_treatment": _share(tl_t, len(p_exposed)),
        "rise": _float(rise),
        "static_neutralization": _share(static, len(neutralized)),
        "status": _status(len(p_exposed), rise is not None and rise >= _thresholds(c6, "tick_limit_rise_min"),
                          rise is not None and rise < _thresholds(c6, "tick_limit_rise_min")),
    }
    # H7: T-E4 seat units in F1 and F2.
    c7 = criteria["E4-H7"]
    seat = {**seat_units(primary["treatment"]["F1"]), **seat_units(primary["treatment"]["F2"])}
    gsb_ok = all(abs(parse_exact(m["exact"]["gsb"])) <= _thresholds(c7, "abs_gsb_max") for m in seat.values())
    scd_units = [name for name, m in seat.items() if parse_exact(m["exact"]["scd"]) >= _thresholds(c7, "scd_min")]
    scd_rate = [name for name in scd_units if seat[name]["n_distinct"] >= c7["n_distinct_min"]]
    out["E4-H7"] = {
        "units": len(seat),
        "complete": len(seat) == len(matrix.F1.pairs) + len(matrix.F2.pairs),
        "max_abs_gsb": max((abs(m["gsb"]) for m in seat.values()), default=None),
        "all_abs_gsb_within": gsb_ok,
        "scd_units": scd_units,
        "scd_units_rate_eligible": scd_rate,
        "status": _status(len(seat), gsb_ok and bool(scd_rate), not scd_units),
    }
    # H8
    parity_rows = mirror_parity(primary["treatment"]["F2"], primary["treatment"]["F2-P"])
    dependent = [row["mirror"] for row in parity_rows if row["label"] == TICK_LIMIT_PARITY_DEPENDENT]
    out["E4-H8"] = {"mirrors": parity_rows, "parity_dependent": dependent,
                    "complete": len(parity_rows) == len(matrix.F2.pairs),
                    "status": _status(len(parity_rows), bool(dependent), not dependent)}
    # D9'
    completions = [c for f in matrix.FIELD_IDS for c in d9_completions(primary["treatment"][f])]
    companion_completions = (
        [c for f in matrix.FIELD_IDS for c in d9_completions(companion["treatment"][f])] if companion else None
    )
    out["D9-PRIME"] = {
        "t_e4_completions": len(completions),
        "t_e4_completion_samples": completions[:10],
        "t_e4k1_completions_reported": None if companion_completions is None else len(companion_completions),
        "status": HOLDS if not completions else STOP,
    }
    out["units"] = rows
    out["interpretation_inputs"] = {h: out[h]["status"] for h in (
        "E4-H0", "E4-H1", "E4-H2", "E4-H3", "E4-H4", "E4-H5", "E4-H6", "E4-H7", "E4-H8", "D9-PRIME")}
    out["interpretation"] = read_interpretation(out["interpretation_inputs"], prereg)
    return out


def read_interpretation(statuses: Mapping[str, str], prereg: Mapping[str, Any]) -> dict[str, Any]:
    """O-INTERPRETATION: a row applies when each named hypothesis has its required status
    (plain: SUPPORTED; negated: REFUTED). The pathology row applies when any of its
    hypotheses is SUPPORTED; the "none" row when no main row applies."""
    if statuses.get("D9-PRIME") == STOP:
        return {"applies": [], "stop": "D9' violated: an implementation/experiment failure, not a gameplay result."}
    applies = []
    for row in prereg["interpretation"]:
        rule = row["rule"]
        if rule["kind"] == "all":
            if all(statuses.get(h) == status for h, status in rule["requires"].items()):
                applies.append(row["result"])
        elif rule["kind"] == "any_supported" and any(statuses.get(h) == SUPPORTED for h in rule["hypotheses"]):
            applies.append(row["result"])
    main = [row["result"] for row in prereg["interpretation"] if row["rule"]["kind"] == "all"]
    if not any(result in applies for result in main):
        applies.append(next(row["result"] for row in prereg["interpretation"] if row["rule"]["kind"] == "none"))
    return {"applies": applies, "stop": None}
