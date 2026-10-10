"""V6 E3 analysis (design review Sec J, Sec K, Sec M; ``preregistration.json``).

Pure functions over loaded field runs: the harness cell records of one
condition/field and each cell's E3 telemetry (``action_parity``, which carries
capture analyzer v2's telemetry). Nothing here executes a match or reads a
treatment artifact by itself; ``run_e3`` decides what may be loaded.

* **Populations** (Sec J, O-EXPOSED, O-STALEMATE): exposed, stalemate and
  hit-free cells of a control.
* **PM-1 / PM-2** summaries over a cell set: scoreable and NOT_SCOREABLE
  counts, cell-weighted medians of PD and FMS, direction counts, and the
  phase-lock categories including NO_ZERO_CORE_TICKS.
* **PM-3** paired outcome transitions over {A win, B win, tick-limit tie,
  mutual elimination} with distinct-transition counts.
* **PM-4** SDI and mirror seat bias, and the 1000/1001 mirror claim check
  (TICK_LIMIT_PARITY_DEPENDENT).
* **MC-1 / MC-2** summaries by mover role, entrant and pairing.
* **Residuals** under Sec M rule 4 (floor, dominance, control comparison).
* **D0-D9** criterion values and SUPPORTED / REFUTED / NEITHER, with evidence
  labels; the verdicts themselves are read under the interpretation table.
"""

from __future__ import annotations

import statistics
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from fractions import Fraction
from typing import Any

from tools.research.v6 import experiment_harness as harness
from tools.research.v6.e3 import matrix
from tools.research.v6.e3.gates import D9_VICTIMS, cell_key

E3_ANALYSIS_VERSION = 1

SUPPORTED = "SUPPORTED"
REFUTED = "REFUTED"
NEITHER = "NEITHER"
NOT_EVALUABLE = "NOT_EVALUABLE"
STOP = "STOP"
TICK_LIMIT_PARITY_DEPENDENT = "TICK_LIMIT_PARITY_DEPENDENT"
PARITY_ROBUST = "AGREES_AT_1000_AND_1001"

A_WIN = "A_win"
B_WIN = "B_win"
TICK_LIMIT_TIE = "tick_limit_tie"
MUTUAL_ELIMINATION = "mutual_elimination"
OTHER = "other"
OUTCOME_CLASSES = (A_WIN, B_WIN, TICK_LIMIT_TIE, MUTUAL_ELIMINATION, OTHER)

Cell = Mapping[str, Any]
Row = Mapping[str, Any]


@dataclass(frozen=True)
class FieldRun:
    """One condition/field: harness cells and E3 telemetry rows, both by cell key."""

    condition_id: str
    field_id: str
    cells: Mapping[str, Cell]
    telemetry: Mapping[str, Row]

    def t(self, key: str) -> Mapping[str, Any]:
        row = self.telemetry.get(key) or {}
        if "telemetry" not in row:
            raise ValueError(f"{self.condition_id}/{self.field_id} {key}: no telemetry ({row.get('error')})")
        telemetry: Mapping[str, Any] = row["telemetry"]
        return telemetry


def make_field_run(condition_id: str, field_id: str, cells: Iterable[Cell], telemetry: Mapping[str, Row]) -> FieldRun:
    return FieldRun(condition_id, field_id, {cell_key(cell): cell for cell in cells}, dict(telemetry))


def evidence(n_distinct: int) -> dict[str, Any]:
    return {
        "n_distinct": n_distinct,
        "evidence": harness.evidence_label(n_distinct),
        "rate_claim_eligible": n_distinct >= harness.MIN_DISTINCT_FOR_RATE_CLAIM,
    }


def _share(numerator: int, denominator: int) -> float | None:
    return None if denominator == 0 else numerator / denominator


def _at_least(numerator: int, denominator: int, threshold: float) -> bool:
    return denominator > 0 and Fraction(numerator, denominator) >= Fraction(str(threshold))


def _median(values: Sequence[float]) -> float | None:
    return None if not values else round(float(statistics.median(values)), 6)


# ---------------------------------------------------------------------------
# Outcome classes and populations
# ---------------------------------------------------------------------------


def outcome_class(cell: Cell) -> str:
    """PM-3 / O-OUTCOME-CLASS."""
    result = harness.cell_seat_result(cell)
    if result == harness.SEAT_A:
        return A_WIN
    if result == harness.SEAT_B:
        return B_WIN
    if result == harness.TIE:
        return TICK_LIMIT_TIE if cell.get("termination_reason") == harness.TICK_LIMIT_REASON else MUTUAL_ELIMINATION
    return OTHER


def exposed_keys(run: FieldRun) -> list[str]:
    return sorted(key for key in run.cells if run.t(key)["exposed"])


def stalemate_keys(run: FieldRun) -> list[str]:
    return sorted(
        key
        for key, cell in run.cells.items()
        if cell.get("termination_reason") == harness.TICK_LIMIT_REASON
        and any(seat["capture"]["recoveries"] >= 1 for seat in run.t(key)["seats"].values())
    )


def hit_free_keys(run: FieldRun) -> list[str]:
    return sorted(key for key in run.cells if run.t(key)["first_hit_tick"] is None)


def populations(runs: Mapping[str, FieldRun]) -> dict[str, dict[str, list[str]]]:
    """Exposed, stalemate and hit-free cell identities of one control, per field."""
    return {
        field_id: {"exposed": exposed_keys(run), "stalemate": stalemate_keys(run), "hit_free": hit_free_keys(run)}
        for field_id, run in runs.items()
    }


def population_cells(
    frozen: Mapping[str, Mapping[str, Sequence[str]]], population: str, fields: Sequence[str]
) -> list[tuple[str, str]]:
    """``(field, key)`` pairs of one frozen population over the given fields."""
    return [(field_id, key) for field_id in fields for key in frozen[field_id][population]]


# ---------------------------------------------------------------------------
# PM-1 / PM-2
# ---------------------------------------------------------------------------


def _distinct(
    items: Iterable[tuple[str, str]],
    runs: Mapping[str, FieldRun],
    control: Mapping[str, FieldRun] | None,
) -> int:
    keys = set()
    for field_id, key in items:
        t_key = harness.trajectory_key(runs[field_id].cells[key])
        c_key = harness.trajectory_key(control[field_id].cells[key]) if control is not None else None
        keys.add((field_id, c_key, t_key))
    return len(keys)


def parity_summary(
    runs: Mapping[str, FieldRun],
    items: Sequence[tuple[str, str]],
    *,
    control: Mapping[str, FieldRun] | None = None,
) -> dict[str, Any]:
    """PM-1 over a cell set of one condition (O-FMS, O-PARITY-MEDIANS).

    With ``control`` given, n_distinct counts distinct (C key, T key) transitions.
    """
    scored = [(f, k, runs[f].t(k)["parity"]) for f, k in items]
    scoreable = [(f, k, p) for f, k, p in scored if p["scoreable"]]
    directions = Counter(p["direction"] for _, _, p in scored)
    distinct_rows = {
        (f, harness.trajectory_key(runs[f].cells[k]),
         harness.trajectory_key(control[f].cells[k]) if control is not None else None, p["fms"])
        for f, k, p in scoreable
    }
    return {
        "cells": len(items),
        "scoreable": len(scoreable),
        "not_scoreable": len(items) - len(scoreable),
        "median_pd": _median([p["pd"] for _, _, p in scoreable]),
        "median_fms": _median([p["fms"] for _, _, p in scoreable]),
        "directions": dict(sorted(directions.items())),
        **evidence(_distinct([(f, k) for f, k, _ in scoreable], runs, control)),
        "descriptive_distinct_row_median_pd": _median([abs(2 * fms - 1) for *_, fms in distinct_rows]),
        "descriptive_distinct_row_median_fms": _median([fms for *_, fms in distinct_rows]),
    }


def phase_lock_summary(runs: Mapping[str, FieldRun], items: Sequence[tuple[str, str]]) -> dict[str, Any]:
    """PM-2 over the entrants of a cell set (O-PHASE-LOCK)."""
    categories: Counter[str] = Counter()
    directions: Counter[str] = Counter()
    two_sided: list[float] = []
    for field_id, key in items:
        for seat in runs[field_id].t(key)["seats"].values():
            reading = seat["phase_lock"]
            categories[reading["category"]] += 1
            if reading["direction"] is not None:
                directions[reading["direction"]] += 1
                two_sided.append(reading["two_sided"])
    return {
        "entrants": sum(categories.values()),
        "categories": dict(sorted(categories.items())),
        "directions": dict(sorted(directions.items())),
        "median_two_sided_lock": _median(two_sided),
        # |2 PL - 1| >= 0.9 is PL >= 0.95 or PL <= 0.05: E2's H3b lock, read two-sided.
        "locked_two_sided_0_9": sum(1 for value in two_sided if value >= 0.9),
    }


# ---------------------------------------------------------------------------
# PM-3
# ---------------------------------------------------------------------------


def transitions(
    control: Mapping[str, FieldRun],
    treatment: Mapping[str, FieldRun],
    items: Sequence[tuple[str, str]],
) -> dict[str, Any]:
    """Paired C -> T outcome-class transitions over a cell set (O-UNIT)."""
    table = {c: dict.fromkeys(OUTCOME_CLASSES, 0) for c in OUTCOME_CLASSES}
    unmatched = 0
    unchanged = 0
    rows: dict[tuple[Any, ...], bool] = {}
    for field_id, key in items:
        before = control[field_id].cells.get(key)
        after = treatment[field_id].cells.get(key)
        if before is None or after is None:
            unmatched += 1
            continue
        a, b = outcome_class(before), outcome_class(after)
        table[a][b] += 1
        unchanged += 1 if a == b else 0
        rows[(field_id, harness.trajectory_key(before), harness.trajectory_key(after))] = a == b
    matched = len(items) - unmatched
    return {
        "cells": len(items),
        "matched": matched,
        "unmatched": unmatched,
        "matrix": table,
        "unchanged": unchanged,
        "unchanged_share": _share(unchanged, matched),
        **evidence(len(rows)),
        "descriptive_distinct_unchanged_share": _share(sum(rows.values()), len(rows)),
    }


# ---------------------------------------------------------------------------
# PM-4
# ---------------------------------------------------------------------------


def _claim(sdi: Mapping[str, Any]) -> tuple[str, str | None]:
    if sdi.get("sdi") is not None and sdi["sdi"] >= harness.SEAT_DETERMINED_SDI:
        return "seat_determined", sdi.get("favoured_seat")
    return "not_seat_determined", None


def pairing_units(run: FieldRun) -> dict[tuple[str, str], dict[str, Any]]:
    """SDI and seat bias per pairing of one field (F2 / F2-P: per mirror)."""
    field = matrix.field(run.field_id)
    cells = list(run.cells.values())
    if field.field_id in ("F2", "F2-P"):
        return {
            (m["primary"], m["twin"]): {"sdi": m["sdi"], "seat_bias": m["mirror_seat_bias"], "n_distinct": m["n_distinct"]}
            for m in harness.analyze_mirror_condition(cells, field.pairs)["mirrors"]
        }
    return {
        (m["entrants"][0], m["entrants"][1]): {"sdi": m["sdi"], "seat_bias": m["seat_bias"], "n_distinct": m["n_distinct"]}
        for m in harness.seat_conditioned_matchups(cells, field.agents)
    }


def seat_determined_units(runs: Mapping[str, FieldRun], fields: Sequence[str]) -> list[dict[str, Any]]:
    out = []
    for field_id in fields:
        for pairing, unit in pairing_units(runs[field_id]).items():
            status, favoured = _claim(unit["sdi"])
            if status == "seat_determined":
                out.append({"field": field_id, "pairing": list(pairing), "sdi": unit["sdi"]["sdi"],
                            "favoured_seat": favoured, "n_distinct": unit["sdi"]["n_distinct"]})
    return out


def mirror_parity(run_1000: FieldRun, run_1001: FieldRun) -> list[dict[str, Any]]:
    """O-MIRROR-PARITY: each mirror's claim at 1000 (F2) and 1001 (F2-P) ticks."""
    at_1000, at_1001 = pairing_units(run_1000), pairing_units(run_1001)
    rows = []
    for pairing in at_1000:
        a, b = at_1000[pairing], at_1001[pairing]
        claim_a, claim_b = _claim(a["sdi"]), _claim(b["sdi"])
        rows.append({
            "mirror": list(pairing),
            "claim_1000": list(claim_a),
            "claim_1001": list(claim_b),
            "sdi_1000": a["sdi"]["sdi"],
            "sdi_1001": b["sdi"]["sdi"],
            "seat_bias_1000": a["seat_bias"],
            "seat_bias_1001": b["seat_bias"],
            "n_distinct_1000": a["sdi"]["n_distinct"],
            "n_distinct_1001": b["sdi"]["n_distinct"],
            "label": PARITY_ROBUST if claim_a == claim_b else TICK_LIMIT_PARITY_DEPENDENT,
        })
    return rows


def pm4_paired(control: Mapping[str, FieldRun], treatment: Mapping[str, FieldRun]) -> dict[str, Any]:
    """PM-4: every unit's SDI and seat bias under C and T, per field, and the
    1000/1001 mirror claims under both conditions."""
    fields: dict[str, list[dict[str, Any]]] = {}
    for field_id in matrix.FIELD_IDS:
        before, after = pairing_units(control[field_id]), pairing_units(treatment[field_id])
        fields[field_id] = [
            {
                "pairing": list(pairing),
                "sdi_control": before[pairing]["sdi"]["sdi"],
                "sdi_treatment": after[pairing]["sdi"]["sdi"] if pairing in after else None,
                "claim_control": list(_claim(before[pairing]["sdi"])),
                "claim_treatment": list(_claim(after[pairing]["sdi"])) if pairing in after else None,
                "seat_bias_control": before[pairing]["seat_bias"],
                "seat_bias_treatment": after[pairing]["seat_bias"] if pairing in after else None,
                "n_distinct_control": before[pairing]["sdi"]["n_distinct"],
                "n_distinct_treatment": after[pairing]["sdi"]["n_distinct"] if pairing in after else None,
            }
            for pairing in before
        ]
    return {
        "fields": fields,
        "mirror_parity": {"control": mirror_parity(control["F2"], control["F2-P"]),
                          "treatment": mirror_parity(treatment["F2"], treatment["F2-P"])},
    }


# ---------------------------------------------------------------------------
# MC-1 / MC-2
# ---------------------------------------------------------------------------


def _add_role(total: dict[str, Any], role: Mapping[str, Any]) -> None:
    for name in ("entrant_ticks", "offered", "executed", "adf_n"):
        total[name] += role[name]
    total["adf_sum"] += role["adf_sum"]
    total["histogram"] = [x + y for x, y in zip(total["histogram"], role["histogram"], strict=True)]
    if role["min_executed_alive_throughout"] is not None:
        floor = total["min_executed_alive_throughout"]
        value = role["min_executed_alive_throughout"]
        total["min_executed_alive_throughout"] = value if floor is None else min(floor, value)


def _empty_role() -> dict[str, Any]:
    return {"entrant_ticks": 0, "offered": 0, "executed": 0, "adf_n": 0, "adf_sum": 0.0,
            "histogram": [0] * 9, "min_executed_alive_throughout": None}


def _finish_role(total: Mapping[str, Any]) -> dict[str, Any]:
    alive_ticks = sum(total["histogram"])
    return {
        **total,
        "adf_sum": round(total["adf_sum"], 6),
        "mean_adf": None if not total["adf_n"] else round(total["adf_sum"] / total["adf_n"], 6),
        "mean_executed_alive_at_end": None
        if not alive_ticks
        else round(sum(i * n for i, n in enumerate(total["histogram"])) / alive_ticks, 6),
    }


def action_summary(runs: Mapping[str, FieldRun], items: Sequence[tuple[str, str]]) -> dict[str, Any]:
    """MC-1 / MC-2 over a cell set: by role, by entrant (agent name) and by pairing."""
    roles = {role: _empty_role() for role in ("first", "second")}
    by_entrant: dict[str, dict[str, dict[str, Any]]] = {}
    by_pairing: dict[str, dict[str, Any]] = {}
    both = exclusive = zero_action = g4 = cpu_mismatch = exposed = 0
    for field_id, key in items:
        cell = runs[field_id].cells[key]
        t = runs[field_id].t(key)
        both += t["both_alive_ticks"]
        exclusive += t["exclusive_ticks"]
        exposed += 1 if t["exposed"] else 0
        cpu_mismatch += 0 if t["checks"]["cpu_statistics_match"] else 1
        pairing = f"{cell['subject_id']}|{cell['opponent_id']}"
        pair_row = by_pairing.setdefault(pairing, {"adf_n": 0, "adf_sum": 0.0})
        for seat in t["seats"].values():
            zero_action += seat["zero_action_live_ticks"]
            g4 += seat["g4_violations"]
            entrant = by_entrant.setdefault(str(seat["name"]), {role: _empty_role() for role in roles})
            for role, total in roles.items():
                _add_role(total, seat["roles"][role])
                _add_role(entrant[role], seat["roles"][role])
                pair_row["adf_n"] += seat["roles"][role]["adf_n"]
                pair_row["adf_sum"] += seat["roles"][role]["adf_sum"]
    return {
        "cells": len(items),
        "exposed_cells": exposed,
        "both_alive_ticks": both,
        "exclusive_ticks": exclusive,
        "exclusive_share": None if not both else round(exclusive / both, 6),
        "zero_action_live_ticks": zero_action,
        "g4_violations": g4,
        "cpu_statistics_mismatches": cpu_mismatch,
        "roles": {role: _finish_role(total) for role, total in roles.items()},
        "by_entrant": {
            name: {role: _finish_role(total) for role, total in rows.items()} for name, rows in sorted(by_entrant.items())
        },
        "by_pairing": {
            pairing: {"adf_n": row["adf_n"], "mean_adf": None if not row["adf_n"] else round(row["adf_sum"] / row["adf_n"], 6)}
            for pairing, row in sorted(by_pairing.items())
        },
    }


# ---------------------------------------------------------------------------
# Residuals (Sec M rule 4, O-RESIDUAL)
# ---------------------------------------------------------------------------

SEAT_TABLES = (("seat_a", harness.ORIENTATION_CANDIDATE_FIRST), ("seat_b", harness.ORIENTATION_OPPONENT_FIRST))


def residual_table(cells: Sequence[Cell], agents: Sequence[str], rule: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    """Per seat table: every residual with its interval, dominance flag and whether it
    counts by the rule's own conditions (n_distinct, CI, floor, not dominance)."""
    out: dict[str, dict[str, Any]] = {}
    for seat, orientation in SEAT_TABLES:
        subset = [c for c in cells if harness._orientation(c) == orientation]
        intervals = harness.bootstrap_residual_intervals(
            subset, agents, n_bootstraps=rule["bootstrap_resamples"], seed=rule["bootstrap_seed"], interval=rule["interval"]
        )
        outcomes = harness._distinct_outcomes_by_pair(subset, agents)
        rows = {}
        for name, row in intervals["residuals"].items():
            winners = outcomes.get((row["entrants"][0], row["entrants"][1]), [])
            dominance = len(set(winners)) == 1 and winners[0] is not None
            counts = bool(row["significant"]) and abs(row["residual"]) >= rule["abs_residual_min"] and not dominance
            rows[name] = {**row, "dominance": dominance, "counts": counts}
        out[seat] = rows
    return out


def residual_evidence(
    control: Mapping[str, Mapping[str, Any]], treatment: Mapping[str, Mapping[str, Any]]
) -> dict[str, Any]:
    """A treatment residual counts only if it counts and the same pairing's control residual does not."""
    out: dict[str, Any] = {}
    for seat, _ in SEAT_TABLES:
        counting = []
        for name, row in sorted(treatment[seat].items()):
            control_counts = bool((control.get(seat) or {}).get(name, {}).get("counts"))
            if row["counts"] and not control_counts:
                counting.append(name)
        out[seat] = {
            "counting": counting,
            "treatment_counts_before_control_comparison": sorted(n for n, r in treatment[seat].items() if r["counts"]),
            "control_counting": sorted(n for n, r in (control.get(seat) or {}).items() if r["counts"]),
            "dominance": sorted(n for n, r in treatment[seat].items() if r["dominance"]),
        }
    return out


# ---------------------------------------------------------------------------
# Named cell sets (D3, D5, D6, D9)
# ---------------------------------------------------------------------------


def _seat_of(cell: Cell, name: str) -> str | None:
    seat_a, seat_b = harness.cell_seats(cell)
    return "A" if name == seat_a else "B" if name == seat_b else None


def repair_guard_capture_losses(run: FieldRun, criterion: Mapping[str, Any]) -> list[str]:
    """O-D3: F1 cells in which the repair guard is core-captured by one of the named attackers."""
    defender, attackers = criterion["defender"], set(criterion["attackers"])
    out = []
    for key, cell in run.cells.items():
        names = set(harness.cell_seats(cell))
        seat = _seat_of(cell, defender)
        if seat is None or not (names - {defender}) & attackers:
            continue
        if (cell.get("entrant_terminations") or {}).get(seat) == "core_captured":
            out.append(key)
    return sorted(out)


def win_or_draw_rates(run: FieldRun, criterion: Mapping[str, Any], keys: Iterable[str] | None = None) -> dict[str, Any]:
    """O-D5: pooled spread-agent win-or-draw rate against the stacked agents, per seat."""
    allowed = None if keys is None else set(keys)
    spread, stacked = set(criterion["spread"]), set(criterion["stacked"])
    out: dict[str, Any] = {}
    for seat in ("A", "B"):
        cells_n = win_or_draw = 0
        per_agent: dict[str, list[int]] = {}
        for key, cell in run.cells.items():
            if allowed is not None and key not in allowed:
                continue
            seat_a, seat_b = harness.cell_seats(cell)
            agent, other = (seat_a, seat_b) if seat == "A" else (seat_b, seat_a)
            if agent not in spread or other not in stacked:
                continue
            good = harness.cell_winner(cell) in (agent, None) and harness.cell_seat_result(cell) != harness.OTHER
            cells_n += 1
            win_or_draw += 1 if good else 0
            tally = per_agent.setdefault(agent, [0, 0])
            tally[0] += 1 if good else 0
            tally[1] += 1
        out[f"seat_{seat.lower()}"] = {
            "cells": cells_n,
            "win_or_draw": win_or_draw,
            "rate": _share(win_or_draw, cells_n),
            "per_agent_descriptive": {name: _share(w, n) for name, (w, n) in sorted(per_agent.items())},
        }
    return out


def jammer_decisive_wins(run: FieldRun, criterion: Mapping[str, Any], keys: Iterable[str] | None = None) -> dict[str, Any]:
    """O-D6: the jam sniper's decisive wins against each guard, per jam-sniper seat."""
    allowed = None if keys is None else set(keys)
    jammer = criterion["jammer"]
    out: dict[str, Any] = {}
    for guard in criterion["guards"]:
        row = {}
        for seat in ("A", "B"):
            cells = [
                cell for key, cell in run.cells.items()
                if (allowed is None or key in allowed)
                and set(harness.cell_seats(cell)) == {jammer, guard}
                and _seat_of(cell, jammer) == seat
            ]
            wins = sum(
                1 for cell in cells
                if harness.cell_winner(cell) == jammer and cell.get("termination_reason") != harness.TICK_LIMIT_REASON
            )
            row[f"seat_{seat.lower()}"] = {"cells": len(cells), "decisive_wins": wins, "share": _share(wins, len(cells)),
                                           **evidence(harness.count_distinct_trajectories(cells))}
        out[guard] = row
    return out


def guard_completions(runs: Mapping[str, FieldRun]) -> list[dict[str, Any]]:
    """O-D9: capture completions against the repair and disrupt guards (and twins)."""
    out = []
    for field_id, run in runs.items():
        for key in sorted(run.cells):
            for completion in run.t(key)["completions"]:
                if completion["victim_name"] in D9_VICTIMS:
                    out.append({"field": field_id, "cell": key, **completion})
    return out


# ---------------------------------------------------------------------------
# Control baseline (Sec M rule 6) and hypothesis criteria
# ---------------------------------------------------------------------------


def control_baseline(
    control: Mapping[str, FieldRun], frozen: Mapping[str, Mapping[str, Sequence[str]]], prereg: Mapping[str, Any]
) -> dict[str, Any]:
    """Every hypothesis quantity computed on one control, before any treatment exists."""
    criteria = {item["id"]: item["criterion"] for item in prereg["hypotheses"]}
    standard = list(matrix.STANDARD_FIELDS)
    exposed = population_cells(frozen, "exposed", standard)
    stalemate = population_cells(frozen, "stalemate", standard)
    exposed_f1 = population_cells(frozen, "exposed", ["F1"])
    rule = prereg["statistics"]["residual"]
    units_found = seat_determined_units(control, ["F1", "F2"])
    registered = [{"field": u["field"], "pairing": u["pairing"]} for u in criteria["D2"]["units"]]
    return {
        "population_counts": {
            field_id: {name: len(keys) for name, keys in rows.items()} | {"cells": len(control[field_id].cells)}
            for field_id, rows in frozen.items()
        },
        "D0_outcome_classes_exposed": dict(sorted(Counter(
            outcome_class(control[f].cells[k]) for f, k in exposed).items())),
        "parity_stalemate": parity_summary(control, stalemate),
        "parity_exposed_secondary": parity_summary(control, exposed),
        "parity_by_field_stalemate": {f: parity_summary(control, population_cells(frozen, "stalemate", [f]))
                                      for f in matrix.FIELD_IDS},
        "phase_lock_stalemate": phase_lock_summary(control, stalemate),
        "D2_seat_determined_units": units_found,
        "D2_registered_units_reproduced": sorted((u["field"], tuple(u["pairing"])) for u in registered)
        == sorted((u["field"], tuple(u["pairing"])) for u in units_found),
        "D2_f4_seat_determined_units": seat_determined_units(control, ["F4"]),
        "mirror_parity": mirror_parity(control["F2"], control["F2-P"]),
        "D3_repair_guard_capture_losses": repair_guard_capture_losses(control["F1"], criteria["D3"]),
        "D5_win_or_draw": win_or_draw_rates(control["F1"], criteria["D5"]),
        "D6_jammer_decisive_wins": jammer_decisive_wins(control["F4"], criteria["D6"]),
        "D7_exposed_f1_tick_limit_share": _share(
            sum(1 for f, k in exposed_f1 if control[f].cells[k].get("termination_reason") == harness.TICK_LIMIT_REASON),
            len(exposed_f1),
        ),
        "D9_guard_completions": len(guard_completions(control)),
        "residuals_f1": residual_table(list(control["F1"].cells.values()), matrix.F1.agents, rule),
        "actions_standard": action_summary(control, [(f, k) for f in standard for k in sorted(control[f].cells)]),
        "actions_by_field": {f: action_summary(control, [(f, k) for k in sorted(control[f].cells)])
                             for f in matrix.FIELD_IDS},
    }


def _status(supported: bool, refuted: bool) -> str:
    return SUPPORTED if supported else REFUTED if refuted else NEITHER


def evaluate_hypotheses(
    control: Mapping[str, FieldRun],
    treatment: Mapping[str, FieldRun],
    frozen: Mapping[str, Mapping[str, Sequence[str]]],
    prereg: Mapping[str, Any],
    *,
    control_residuals: Mapping[str, Mapping[str, Any]] | None = None,
    companion_treatment: Mapping[str, FieldRun] | None = None,
    arm: str = matrix.PRIMARY_ARM,
) -> dict[str, Any]:
    """D0-D9 criterion values and statuses for one arm (O-STATUS, O-COMPANION).

    ``frozen``: the arm's frozen populations. ``control_residuals``: the
    frozen control residual table (recomputed from ``control`` if omitted).
    ``companion_treatment``: T-E3K1 runs, for D9's companion clause of the
    primary arm. For the companion arm (``arm="companion"``) D9 is not a
    criterion of its own -- its completions are reported, and they feed the
    primary arm's D9 -- so a completion there is never a stop.
    """
    criteria = {item["id"]: item["criterion"] for item in prereg["hypotheses"]}
    standard = list(matrix.STANDARD_FIELDS)
    exposed = population_cells(frozen, "exposed", standard)
    stalemate = population_cells(frozen, "stalemate", standard)
    out: dict[str, Any] = {}

    # D2 first: D0 and D4 depend on it.
    c2 = criteria["D2"]
    unit_rows = []
    for unit in c2["units"]:
        pairing = (unit["pairing"][0], unit["pairing"][1])
        before = pairing_units(control[unit["field"]]).get(pairing)
        after = pairing_units(treatment[unit["field"]]).get(pairing)
        sdi_after = None if after is None else after["sdi"]["sdi"]
        unit_rows.append({
            **unit,
            "sdi_control": None if before is None else before["sdi"]["sdi"],
            "sdi_treatment": sdi_after,
            "falls": sdi_after is not None and sdi_after < c2["sdi_seat_determined"],
            "n_distinct_treatment": None if after is None else after["sdi"]["n_distinct"],
        })
    new_units = []
    for field_id in ("F1", "F2"):
        before_units, after_units = pairing_units(control[field_id]), pairing_units(treatment[field_id])
        for pairing, after in after_units.items():
            before = before_units.get(pairing)
            was = before is not None and _claim(before["sdi"])[0] == "seat_determined"
            if not was and _claim(after["sdi"])[0] == "seat_determined":
                new_units.append({"field": field_id, "pairing": list(pairing), "sdi": after["sdi"]["sdi"]})
    parity_rows = mirror_parity(treatment["F2"], treatment["F2-P"])
    falls = sum(1 for row in unit_rows if row["falls"])
    agree = all(row["label"] == PARITY_ROBUST for row in parity_rows)
    d2_supported = _at_least(falls, len(unit_rows), c2["fall_share_min"]) and not new_units and agree
    out["D2"] = {
        "status": _status(d2_supported, falls == 0),
        "units": unit_rows,
        "units_falling": falls,
        "new_units": new_units,
        "mirror_parity_treatment": parity_rows,
        "mirror_parity_agrees": agree,
        "f4_stratum_treatment": seat_determined_units(treatment, ["F4"]),
    }

    c0 = criteria["D0"]
    d0_items = population_cells(frozen, "exposed", c0["fields"])
    moves = transitions(control, treatment, d0_items)
    share_ok = _at_least(moves["unchanged"], moves["matched"], c0["unchanged_share_min"])
    out["D0"] = {
        "status": NOT_EVALUABLE if not moves["matched"] else _status(
            share_ok and out["D2"]["status"] == REFUTED, not share_ok),
        "transitions": moves,
    }

    parity_t = parity_summary(treatment, stalemate, control=control)
    pd, fms = parity_t["median_pd"], parity_t["median_fms"]
    c1, c4, c8 = criteria["D1"], criteria["D4"], criteria["D8"]
    no_parity = pd is None or fms is None
    out["D1"] = {"status": NOT_EVALUABLE if no_parity else _status(pd <= c1["median_pd_max"], pd >= c1["refuted_median_pd_min"]),
                 "parity": parity_t}
    out["D4"] = {"status": NOT_EVALUABLE if no_parity else _status(
        fms >= c4["median_fms_min"] and out["D2"]["status"] == REFUTED, fms <= c4["refuted_median_fms_max"]),
        "median_fms": fms, "d2_status": out["D2"]["status"]}
    out["D8"] = {"status": NOT_EVALUABLE if no_parity else _status(
        pd >= c8["median_pd_min"] and fms <= c8["median_fms_max"], pd <= c8["refuted_median_pd_max"]),
        "median_pd": pd, "median_fms": fms}
    out["parity_secondary_exposed"] = parity_summary(treatment, exposed, control=control)
    out["phase_lock_stalemate"] = {"control": phase_lock_summary(control, stalemate),
                                   "treatment": phase_lock_summary(treatment, stalemate)}

    c3 = criteria["D3"]
    exposed_f1 = set(frozen["F1"]["exposed"])
    losses_all = repair_guard_capture_losses(control["F1"], c3)
    losses = [key for key in losses_all if key in exposed_f1]
    non_losses = [
        key for key in losses
        if harness.cell_winner(treatment["F1"].cells[key]) in (c3["defender"], None)
        and harness.cell_seat_result(treatment["F1"].cells[key]) != harness.OTHER
    ]
    out["D3"] = {
        "status": NOT_EVALUABLE if not losses else _status(
            _at_least(len(non_losses), len(losses), c3["non_loss_share_min"]), not non_losses),
        "control_capture_losses": len(losses),
        "excluded_not_exposed": len(losses_all) - len(losses),
        "non_losses": len(non_losses),
        "share": _share(len(non_losses), len(losses)),
        **evidence(_distinct([("F1", k) for k in losses], treatment, control)),
    }

    c5 = criteria["D5"]
    before5 = win_or_draw_rates(control["F1"], c5, exposed_f1)
    after5 = win_or_draw_rates(treatment["F1"], c5, exposed_f1)
    exact = {
        seat: None if not before5[seat]["cells"] or not after5[seat]["cells"]
        else Fraction(after5[seat]["win_or_draw"], after5[seat]["cells"])
        - Fraction(before5[seat]["win_or_draw"], before5[seat]["cells"])
        for seat in ("seat_a", "seat_b")
    }
    rise = all(d is not None and d >= Fraction(str(c5["rise_min"])) for d in exact.values())
    fall = all(d is not None and d < 0 for d in exact.values())
    out["D5"] = {"status": NOT_EVALUABLE if None in exact.values() else _status(rise, fall),
                 "control": before5, "treatment": after5,
                 "deltas": {seat: None if d is None else round(float(d), 6) for seat, d in exact.items()}}

    c6 = criteria["D6"]
    exposed_f4 = set(frozen["F4"]["exposed"])
    before6 = jammer_decisive_wins(control["F4"], c6, exposed_f4)
    after6 = jammer_decisive_wins(treatment["F4"], c6, exposed_f4)
    threshold6 = Fraction(str(c6["decisive_win_share_greater_than"]))
    beaten = [
        guard for guard, seats in after6.items()
        if all(row["cells"] > 0 and Fraction(row["decisive_wins"], row["cells"]) > threshold6 for row in seats.values())
    ]
    any_win = any(row["decisive_wins"] for seats in after6.values() for row in seats.values())
    out["D6"] = {"status": _status(bool(beaten), not any_win), "beaten_in_both_seats": beaten,
                 "control": before6, "treatment": after6}

    c7 = criteria["D7"]
    d7_items = population_cells(frozen, "exposed", c7["fields"])

    def limit_count(runs: Mapping[str, FieldRun]) -> int:
        return sum(1 for f, k in d7_items if runs[f].cells[k].get("termination_reason") == harness.TICK_LIMIT_REASON)

    before7, after7 = limit_count(control), limit_count(treatment)
    rise7 = None if not d7_items else Fraction(after7 - before7, len(d7_items))
    out["D7"] = {
        "status": NOT_EVALUABLE if rise7 is None else _status(rise7 >= Fraction(str(c7["rise_min"])), True),
        "cells": len(d7_items),
        "control_tick_limit": before7,
        "treatment_tick_limit": after7,
        "control_share": _share(before7, len(d7_items)),
        "treatment_share": _share(after7, len(d7_items)),
        "rise": None if rise7 is None else round(float(rise7), 6),
        **evidence(_distinct(d7_items, treatment, control)),
    }

    c9 = criteria["D9"]
    if arm == matrix.COMPANION_ARM:
        own = guard_completions(treatment)
        out["D9"] = {"status": "REPORTED_TO_PRIMARY", "companion_completions": len(own), "samples": own[:10]}
    else:
        primary = guard_completions(treatment)
        companion = None if companion_treatment is None else guard_completions(companion_treatment)
        if len(primary) > c9["t_e3_completions_max"]:
            status9 = STOP
        elif companion is None:
            status9 = NOT_EVALUABLE
        else:
            status9 = _status(len(companion) >= c9["t_e3k1_completions_min"], len(companion) == 0)
        out["D9"] = {"status": status9, "primary_completions": len(primary), "primary_samples": primary[:10],
                     "companion_completions": None if companion is None else len(companion)}

    rule = prereg["statistics"]["residual"]
    before_r = control_residuals if control_residuals is not None else residual_table(
        list(control["F1"].cells.values()), matrix.F1.agents, rule)
    after_r = residual_table(list(treatment["F1"].cells.values()), matrix.F1.agents, rule)
    out["residuals_secondary"] = residual_evidence(before_r, after_r)
    out["pm4"] = pm4_paired(control, treatment)
    out["transitions_by_field"] = {
        f: transitions(control, treatment, [(f, k) for k in sorted(control[f].cells)]) for f in matrix.FIELD_IDS
    }
    out["actions_treatment"] = {f: action_summary(treatment, [(f, k) for k in sorted(treatment[f].cells)])
                                for f in matrix.FIELD_IDS}
    out["interpretation_inputs"] = {h: out[h]["status"] for h in ("D0", "D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8", "D9")}
    return out
