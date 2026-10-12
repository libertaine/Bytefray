"""V6 E5 analysis (Revision 1 Sec R2, R4-R6; ``preregistration.json``).

Pure functions over loaded field runs: the harness cell records of one
condition/field and each cell's E5 telemetry (E3 action/parity telemetry, E4
cell metrics and E5 cell metrics). Nothing here executes a match or reads a
treatment artifact by itself; ``run_e5`` decides what may be loaded.

* **Directed units** (O-BP-UNIT, Sec R5.3). A round-robin ordered matchup
  (field, Seat-A agent, Seat-B agent) has two directed units, one per victim
  seat. A twin mirror is one unit, observed on its candidate-first cells,
  whose per-seed value is the mean of its two victims' BP; both directed
  values are kept descriptively.
* **Unit BP** (Sec R5.3). The exact median of the DEFINED cell values;
  DECIDED-EARLY when there are none or fewer than half (E4's rule).
* **Bands and transitions** (Sec R5.4, R5.5). Five exact bands, closed away
  from neutral; nine transition classes in a fixed precedence that
  partitions every unit.
* **Contest classes** (Sec R5.6). SWEEP-BACKED, ANCHOR-ONLY or
  MIXED-INFERENCE from the attacker's sweep role and its frozen control
  core-inference audit, never from BP.
* **Census and hypotheses** (Sec R5.7, review Sec K). E5-H1 and E5-H2 over the
  primary arm's SWEEP-BACKED P-BASE units; E5-H3 over P-PAR-E5 with E4's FMA
  transitions; E5-H4, E5-H5 and the pathology flags.
* **Interpretation** (Sec R6, O-INTERPRETATION-E5). A total mapping from
  (E5-D, E5-H1, E5-H2) to exactly one outcome, with every combination the
  frozen census makes impossible failing closed as an invariant violation.
"""

from __future__ import annotations

import statistics
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from fractions import Fraction
from typing import Any

from tools.research.v6 import experiment_harness as harness
from tools.research.v6.e3.analyze_e3 import outcome_class
from tools.research.v6.e3.gates import D9_VICTIMS
from tools.research.v6.e4 import analyze_e4
from tools.research.v6.e4 import contest_classes as e4_contest_classes
from tools.research.v6.e4.analyze_e4 import (
    NEITHER,
    NOT_EVALUABLE,
    REFUTED,
    SUPPORTED,
    FieldRun,
    is_capture,
    is_tick_limit,
    unit_agents,
    unit_kind,
    units,
)
from tools.research.v6.e4.cell_metrics import exact_text, parse_exact
from tools.research.v6.e5 import matrix
from tools.research.v6.e5.cell_metrics import DEFINED

E5_ANALYSIS_VERSION = 1

# ---------------------------------------------------------------------------
# Bands (Sec R5.4)
# ---------------------------------------------------------------------------

SECOND_STRONG = "second-strong"
SECOND_MODERATE = "second-moderate"
NEUTRAL = "neutral"
FIRST_MODERATE = "first-moderate"
FIRST_STRONG = "first-strong"
BANDS: tuple[str, ...] = (FIRST_STRONG, FIRST_MODERATE, NEUTRAL, SECOND_MODERATE, SECOND_STRONG)
BAND_MODERATE = Fraction(1, 3)
BAND_STRONG = Fraction(2, 3)
SECOND_SIDE = "second"
FIRST_SIDE = "first"
BOUNDARY_PROXIMITY = Fraction(1, 50)
BAND_EDGES: tuple[Fraction, ...] = (-BAND_STRONG, -BAND_MODERATE, BAND_MODERATE, BAND_STRONG)


def bp_band(value: Fraction) -> str:
    """second-strong BP >= 2/3; second-moderate 1/3 <= BP < 2/3; neutral |BP| < 1/3;
    first-moderate -2/3 < BP <= -1/3; first-strong BP <= -2/3 (exact)."""
    if value >= BAND_STRONG:
        return SECOND_STRONG
    if value >= BAND_MODERATE:
        return SECOND_MODERATE
    if value > -BAND_MODERATE:
        return NEUTRAL
    if value > -BAND_STRONG:
        return FIRST_MODERATE
    return FIRST_STRONG


def band_side(band: str) -> str | None:
    if band in (SECOND_STRONG, SECOND_MODERATE):
        return SECOND_SIDE
    if band in (FIRST_STRONG, FIRST_MODERATE):
        return FIRST_SIDE
    if band == NEUTRAL:
        return None
    raise ValueError(f"unknown BP band {band!r}")


def band_strength(band: str) -> int:
    if band in (SECOND_STRONG, FIRST_STRONG):
        return 2
    if band in (SECOND_MODERATE, FIRST_MODERATE):
        return 1
    if band == NEUTRAL:
        return 0
    raise ValueError(f"unknown BP band {band!r}")


def near_boundary(value: Fraction) -> bool:
    return any(abs(value - edge) <= BOUNDARY_PROXIMITY for edge in BAND_EDGES)


# ---------------------------------------------------------------------------
# Transition classes (Sec R5.5)
# ---------------------------------------------------------------------------

DECIDED_EARLY_CLASS = "DECIDED-EARLY"
FIRST_SIDE_CONTROL = "FIRST-SIDE-CONTROL"
UNCHANGED_NEUTRAL = "UNCHANGED-NEUTRAL"
NEW = "NEW"
NEUTRALIZED = "NEUTRALIZED"
FLIPPED = "FLIPPED"
STAYS = "STAYS"
WEAKENED = "WEAKENED"
STRENGTHENED = "STRENGTHENED"
# The registered precedence (Sec R5.5): the order a unit is tested in.
TRANSITION_CLASSES: tuple[str, ...] = (
    DECIDED_EARLY_CLASS, FIRST_SIDE_CONTROL, UNCHANGED_NEUTRAL, NEW, NEUTRALIZED, FLIPPED, STAYS, WEAKENED,
    STRENGTHENED,
)
# O-CONTROL-CENSUS: the only classes a control compared with itself may produce.
IDENTITY_CLASSES: frozenset[str] = frozenset({DECIDED_EARLY_CLASS, FIRST_SIDE_CONTROL, UNCHANGED_NEUTRAL, STAYS})
H1_CLASSES: tuple[str, ...] = (NEUTRALIZED, WEAKENED, FLIPPED)
H2_CLASSES: tuple[str, ...] = (STAYS, STRENGTHENED)


def transition_class(control: Mapping[str, Any], treatment: Mapping[str, Any]) -> str:
    """Sec R5.5, in the registered precedence; a partition of every unit."""
    if control["status"] != DEFINED or treatment["status"] != DEFINED:
        return DECIDED_EARLY_CLASS
    c_band, t_band = control["band"], treatment["band"]
    c_side, t_side = band_side(c_band), band_side(t_band)
    if c_side == FIRST_SIDE:
        return FIRST_SIDE_CONTROL
    if c_side is None:
        return UNCHANGED_NEUTRAL if t_side is None else NEW
    # control side second
    if t_side is None:
        return NEUTRALIZED
    if t_side == FIRST_SIDE:
        return FLIPPED
    if t_band == c_band:
        return STAYS
    return WEAKENED if band_strength(t_band) < band_strength(c_band) else STRENGTHENED


# ---------------------------------------------------------------------------
# Directed units and unit BP (Sec R5.3)
# ---------------------------------------------------------------------------

SEAT_A_VICTIM = "A"
SEAT_B_VICTIM = "B"
MIRROR_VICTIMS = "AB"


def directed_units(run: FieldRun) -> dict[str, dict[str, Any]]:
    """Directed unit name -> (matchup unit, victim, cell keys). A round-robin
    matchup gives two directed units, a twin mirror one (O-BP-UNIT)."""
    out: dict[str, dict[str, Any]] = {}
    for name, keys in units(run).items():
        field_id, seat_a, seat_b = unit_agents(name)
        kind = unit_kind(seat_a, seat_b)
        victims = (MIRROR_VICTIMS,) if kind == analyze_e4.MIRROR else (SEAT_A_VICTIM, SEAT_B_VICTIM)
        for victim in victims:
            out[f"{name}|{victim}"] = {"matchup": name, "field": field_id, "seat_a": seat_a, "seat_b": seat_b,
                                       "kind": kind, "victim": victim, "keys": list(keys)}
    return out


def _cell_bp(e5: Mapping[str, Any], seat: str) -> Fraction | None:
    reading = e5["bp"][seat]
    return parse_exact(reading["exact"]) if reading["status"] == DEFINED else None


def cell_value(e5: Mapping[str, Any], victim: str) -> Fraction | None:
    """One cell's value for a directed unit: its victim's BP, or for a mirror the
    mean of both victims' BP (both are DEFINED together)."""
    if victim == MIRROR_VICTIMS:
        a, b = _cell_bp(e5, "A"), _cell_bp(e5, "B")
        if (a is None) != (b is None):
            raise ValueError("a mirror cell has one DEFINED and one DECIDED_EARLY victim BP")
        return None if a is None or b is None else (a + b) / 2
    return _cell_bp(e5, victim)


def median_summary(values: Sequence[Fraction | None]) -> dict[str, Any]:
    """E4's unit rule: DECIDED-EARLY with no DEFINED value or fewer than half; else
    the exact median of the DEFINED values, and its band."""
    defined = [v for v in values if v is not None]
    cells = len(values)
    if not defined or 2 * len(defined) < cells:
        return {"cells": cells, "defined": len(defined), "status": DECIDED_EARLY_CLASS, "median_exact": None,
                "median": None, "band": None, "side": None, "near_boundary": False}
    median = Fraction(statistics.median(defined))
    band = bp_band(median)
    return {"cells": cells, "defined": len(defined), "status": DEFINED, "median_exact": exact_text(median),
            "median": round(float(median), 6), "band": band, "side": band_side(band),
            "near_boundary": near_boundary(median)}


def bp_summary(run: FieldRun, keys: Sequence[str], victim: str) -> dict[str, Any]:
    summary = median_summary([cell_value(run.row(key)["e5"], victim) for key in keys])
    if victim == MIRROR_VICTIMS:
        # O-1: the two directed victim values, kept descriptively.
        summary["directed"] = {
            seat: median_summary([_cell_bp(run.row(key)["e5"], seat) for key in keys]) for seat in ("A", "B")
        }
    return summary


# ---------------------------------------------------------------------------
# Contest classes (Sec R5.6)
# ---------------------------------------------------------------------------

SWEEP_BACKED = "SWEEP-BACKED"
ANCHOR_ONLY = "ANCHOR-ONLY"
MIXED_INFERENCE = "MIXED-INFERENCE"
CONTEST_CLASSES: tuple[str, ...] = (SWEEP_BACKED, ANCHOR_ONLY, MIXED_INFERENCE)
INFERRED = "inferred"
NOT_INFERRED = "not_inferred"


def _attacker(seat: str) -> str:
    return "B" if seat == "A" else "A"


def directed_class(run: FieldRun, keys: Sequence[str], attacker_seat: str, attacker_name: str) -> str:
    """SB iff the attacker has the sweep role and inferred the victim's core
    correctly in every control cell; AO iff it has no sweep role or never
    inferred it; MIXED-INFERENCE otherwise."""
    audits = [run.e3(key)["seats"][attacker_seat]["capture"]["core_inference"] for key in keys]
    sweeps = matrix.sweeps(attacker_name)
    if sweeps and audits and all(a is not None and a["status"] == INFERRED and a["correct"] is True for a in audits):
        return SWEEP_BACKED
    if not sweeps or all(a is None or a["status"] == NOT_INFERRED for a in audits):
        return ANCHOR_ONLY
    return MIXED_INFERENCE


def unit_class(run: FieldRun, unit: Mapping[str, Any]) -> str:
    keys = unit["keys"]
    names = {"A": unit["seat_a"], "B": unit["seat_b"]}
    if unit["victim"] == MIRROR_VICTIMS:
        both = {directed_class(run, keys, seat, names[seat]) for seat in ("A", "B")}
        return both.pop() if len(both) == 1 else MIXED_INFERENCE
    attacker = _attacker(unit["victim"])
    return directed_class(run, keys, attacker, names[attacker])


# ---------------------------------------------------------------------------
# Unit rows, P-BASE and the census
# ---------------------------------------------------------------------------


def evidence(n_distinct: int) -> dict[str, Any]:
    return analyze_e4.evidence(n_distinct)


def unit_rows(
    control: Mapping[str, FieldRun],
    treatment: Mapping[str, FieldRun] | None,
    fields: Sequence[str] = matrix.FIELD_IDS,
) -> dict[str, dict[str, Any]]:
    """Every directed unit: its contest class (from the control), control (and
    treatment) BP summary, transition and evidence. With no treatment, the
    control is summarized alone."""
    out: dict[str, dict[str, Any]] = {}
    e4_table = e4_contest_classes.load_table()
    for field_id in fields:
        c_run = control[field_id]
        t_run = treatment[field_id] if treatment is not None else None
        for name, unit in directed_units(c_run).items():
            keys = unit["keys"]
            c_summary = bp_summary(c_run, keys, unit["victim"])
            row: dict[str, Any] = {
                "unit": name, **{k: unit[k] for k in ("matchup", "field", "seat_a", "seat_b", "kind", "victim")},
                "contest_class": unit_class(c_run, unit),
                # Review Sec I: E4's a-priori unit class, a descriptive secondary stratum only.
                "e4_contest_class": e4_contest_classes.class_of(e4_table, field_id, unit["seat_a"], unit["seat_b"]),
                "cells": list(keys), "control": c_summary,
            }
            if t_run is None:
                row["n_distinct_control"] = len({harness.trajectory_key(c_run.cells[k]) for k in keys})
            else:
                missing = [k for k in keys if k not in t_run.cells]
                if missing:
                    raise ValueError(f"{name}: treatment lacks cells {missing[:3]}")
                t_summary = bp_summary(t_run, keys, unit["victim"])
                row["treatment"] = t_summary
                row["transition"] = transition_class(c_summary, t_summary)
                row.update(evidence(len({(harness.trajectory_key(c_run.cells[k]), harness.trajectory_key(t_run.cells[k]))
                                         for k in keys})))
            out[name] = row
    return out


def p_base(control_rows: Mapping[str, Mapping[str, Any]]) -> list[str]:
    """O-P-BASE: directed units whose control unit is DEFINED with side second (BP_C >= 1/3)."""
    return sorted(name for name, row in control_rows.items()
                  if row["control"]["status"] == DEFINED and row["control"]["side"] == SECOND_SIDE)


def census(rows: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    items = list(rows)
    classes = Counter(row["transition"] for row in items)
    return {
        "units": len(items),
        "classes": {name: classes.get(name, 0) for name in TRANSITION_CLASSES},
        "rate_claim_eligible_units": sum(1 for row in items if row.get("rate_claim_eligible")),
        "deterministic_characterizations": sum(1 for row in items if row.get("n_distinct") == 1),
        "near_boundary_units": sorted(row["unit"] for row in items
                                      if row["control"]["near_boundary"] or row["treatment"]["near_boundary"]),
    }


def control_census(rows: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    """O-CONTROL-CENSUS: a control compared with itself; every unit must be an identity class."""
    items = list(rows.values())
    non_identity = [row["unit"] for row in items if row["transition"] not in IDENTITY_CLASSES]
    return {**census(items), "non_identity_units": non_identity,
            "status": "PASS" if items and not non_identity else "FAIL"}


# ---------------------------------------------------------------------------
# Statuses, the census criteria and the interpretation (Sec R5.7, R6)
# ---------------------------------------------------------------------------

STATUSES: tuple[str, ...] = (SUPPORTED, REFUTED, NEITHER, NOT_EVALUABLE)
D_PASS = "PASS"
D_FAIL = "FAIL"


class InterpretationInvariantError(RuntimeError):
    """A combination the frozen census makes impossible reached the interpretation (fail closed)."""


def status_of(value: Fraction | None, supported_min: Fraction, refuted_max: Fraction) -> str:
    """O-STATUS-E5: SUPPORTED iff value >= supported_min; REFUTED iff value <= refuted_max;
    NEITHER otherwise; NOT_EVALUABLE with no units. NEITHER never stands for REFUTED."""
    if value is None:
        return NOT_EVALUABLE
    if value >= supported_min:
        return SUPPORTED
    if value <= refuted_max:
        return REFUTED
    return NEITHER


def _share(count: int, total: int) -> dict[str, Any]:
    value = None if total == 0 else Fraction(count, total)
    return {"count": count, "of": total, "share": None if value is None else round(float(value), 6),
            "share_exact": None if value is None else exact_text(value)}


def census_hypotheses(rows: Sequence[Mapping[str, Any]], criteria: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    """E5-H1 and E5-H2 over the SB P-BASE units (DECIDED-EARLY in the denominator)."""
    n = len(rows)
    h1 = sum(1 for row in rows if row["transition"] in H1_CLASSES)
    h2 = sum(1 for row in rows if row["transition"] in H2_CLASSES)
    de = sum(1 for row in rows if row["transition"] == DECIDED_EARLY_CLASS)
    other = n - h1 - h2 - de
    if other:
        raise InterpretationInvariantError(
            f"{other} SB P-BASE unit(s) have a transition outside H1, H2 and DECIDED-EARLY; P-BASE is side-second "
            "by construction, so this is an analyzer defect")
    c1, c2 = criteria["E5-H1"], criteria["E5-H2"]
    v1 = None if n == 0 else Fraction(h1, n)
    v2 = None if n == 0 else Fraction(h2, n)
    return {
        "units": n,
        "E5-H1": {**_share(h1, n), "classes": list(H1_CLASSES),
                  "split": {cls: sum(1 for row in rows if row["transition"] == cls) for cls in H1_CLASSES},
                  "status": status_of(v1, Fraction(c1["supported_min"]), Fraction(c1["refuted_max"]))},
        "E5-H2": {**_share(h2, n), "classes": list(H2_CLASSES),
                  "status": status_of(v2, Fraction(c2["supported_min"]), Fraction(c2["refuted_max"]))},
        "decided_early": _share(de, n),
    }


def interpretation_rows(prereg: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    rows: list[Mapping[str, Any]] = prereg["interpretation"]["rows"]
    return rows


def interpret(d_status: str, h1: str, h2: str, prereg: Mapping[str, Any]) -> dict[str, Any]:
    """O-INTERPRETATION-E5: exactly one outcome for (E5-D, E5-H1, E5-H2), or an
    invariant violation. The registered rows are tried in order; a combination
    listed as impossible, or matched by no row or by more than one, fails closed."""
    if d_status not in (D_PASS, D_FAIL) or h1 not in STATUSES or h2 not in STATUSES:
        raise InterpretationInvariantError(f"unknown input ({d_status!r}, {h1!r}, {h2!r})")
    table = prereg["interpretation"]
    pair = [h1, h2]
    for impossible in table["impossible"]:
        if impossible["e5_d"] in (d_status, "*") and pair in impossible["combinations"]:
            raise InterpretationInvariantError(
                f"({d_status}, H1 {h1}, H2 {h2}) is impossible under the frozen census: {impossible['reason']}")
    matched = [row for row in table["rows"] if row["e5_d"] == d_status and pair in row["combinations"]]
    if len(matched) != 1:
        raise InterpretationInvariantError(
            f"({d_status}, H1 {h1}, H2 {h2}) matches {len(matched)} registered rows; the table must be total")
    row = matched[0]
    return {"outcome": row["id"], "reading": row["reading"], "inputs": {"E5-D": d_status, "E5-H1": h1, "E5-H2": h2}}


# ---------------------------------------------------------------------------
# E5-H3 (continuity), E5-H4/H5, pathology flags and D9
# ---------------------------------------------------------------------------


def outcome_change(control: FieldRun, treatment: FieldRun, keys: Sequence[str]) -> dict[str, Any]:
    changed = sum(1 for k in keys if outcome_class(control.cells[k]) != outcome_class(treatment.cells[k]))
    distinct = {(harness.trajectory_key(control.cells[k]), harness.trajectory_key(treatment.cells[k])) for k in keys}
    return {**_share(changed, len(keys)), **evidence(len(distinct))}


def d9_completions(run: FieldRun) -> list[dict[str, Any]]:
    out = []
    for key in sorted(run.cells):
        for completion in run.e3(key)["completions"]:
            if completion["victim_name"] in D9_VICTIMS:
                out.append({"field": run.field_id, "cell": key, **completion})
    return out


def _no_core_contact(run: FieldRun, key: str) -> bool:
    directed = run.row(key)["e5"]["directed"]
    return all(item["coverage_mean"] in (None, "0/1") for item in directed.values())


def pathology_flags(control: FieldRun, treatment: FieldRun, criteria: Mapping[str, Any]) -> dict[str, Any]:
    """PF-1 .. PF-5 over the primary arm's F1 cells (review Sec K, preregistration O-PATHOLOGY)."""
    keys = sorted(control.cells)
    flag = Fraction(criteria["flag_min"])
    non_capture = [k for k in keys if not is_capture(control.cells[k])]
    capture = [k for k in keys if is_capture(control.cells[k])]
    became_capture = sum(1 for k in non_capture if is_capture(treatment.cells[k]))
    lost_capture = sum(1 for k in capture if not is_capture(treatment.cells[k]))
    tl_c = sum(1 for k in keys if is_tick_limit(control.cells[k]))
    tl_t = sum(1 for k in keys if is_tick_limit(treatment.cells[k]))
    nc_c = sum(1 for k in keys if _no_core_contact(control, k))
    nc_t = sum(1 for k in keys if _no_core_contact(treatment, k))

    def raised(count: int, total: int) -> bool:
        return total > 0 and Fraction(count, total) >= flag

    def rise(after: int, before: int, total: int) -> bool:
        return total > 0 and Fraction(after - before, total) >= flag

    c_seat = analyze_e4.seat_units(control)
    t_seat = analyze_e4.seat_units(treatment)
    gsb_max = Fraction(criteria["seat_abs_gsb_max"])
    sdom_min = Fraction(criteria["seat_sdom_min"])
    new_seat = sorted(
        name for name, m in t_seat.items()
        if name in c_seat and (
            (parse_exact(m["exact"]["sdom"]) >= sdom_min > parse_exact(c_seat[name]["exact"]["sdom"]))
            or (abs(parse_exact(m["exact"]["gsb"])) > gsb_max >= abs(parse_exact(c_seat[name]["exact"]["gsb"]))))
    )
    return {
        "PF-1": {"control_non_capture_become_captures": _share(became_capture, len(non_capture)),
                 "raised": raised(became_capture, len(non_capture))},
        "PF-2": {"tick_limit_control": _share(tl_c, len(keys)), "tick_limit_treatment": _share(tl_t, len(keys)),
                 "raised": rise(tl_t, tl_c, len(keys))},
        "PF-3": {"control_captures_become_non_captures": _share(lost_capture, len(capture)),
                 "raised": raised(lost_capture, len(capture))},
        "PF-4": {"no_core_contact_control": _share(nc_c, len(keys)), "no_core_contact_treatment": _share(nc_t, len(keys)),
                 "raised": rise(nc_t, nc_c, len(keys))},
        "PF-5": {"newly_seat_dominant_or_biased": new_seat, "raised": bool(new_seat)},
    }


def _thresholds(criterion: Mapping[str, Any], name: str) -> Fraction:
    return Fraction(str(criterion[name]))


def evaluate_hypotheses(
    arms: Mapping[str, Mapping[str, Mapping[str, FieldRun]]],
    frozen_record: Mapping[str, Any],
    prereg: Mapping[str, Any],
    e4_table: Mapping[str, Any],
    *,
    d_status: str,
) -> dict[str, Any]:
    """E5-H1 .. E5-H5, the pathology flags, D9 and the interpretation.

    ``arms[arm]`` is ``{"control": runs, "treatment": runs}`` by field;
    ``frozen_record`` is the frozen control-populations record (its ``arms``
    and ``p_par_e5``); ``d_status`` is the treatment gates' E5-D verdict."""
    frozen = frozen_record["arms"]
    criteria = {item["id"]: item["criterion"] for item in prereg["hypotheses"]}
    primary = arms[matrix.PRIMARY_ARM]
    companion = arms[matrix.COMPANION_ARM]
    rows = unit_rows(primary["control"], primary["treatment"])
    frozen_primary = frozen[matrix.PRIMARY_ARM]
    sb = [rows[name] for name in frozen_primary["p_base"]
          if frozen_primary["contest_classes"][name] == SWEEP_BACKED]
    ao = [rows[name] for name in frozen_primary["p_base"]
          if frozen_primary["contest_classes"][name] == ANCHOR_ONLY]
    for name in frozen_primary["p_base"]:
        if rows[name]["contest_class"] != frozen_primary["contest_classes"][name]:
            raise InterpretationInvariantError(f"{name}: contest class no longer recomputes from the control")
    out: dict[str, Any] = census_hypotheses(sb, criteria)
    out["sweep_backed_census"] = census(sb)
    out["sweep_backed_by_e4_class"] = {  # descriptive secondary stratum (review Sec I)
        cls: census([row for row in sb if row["e4_contest_class"] == cls]) for cls in e4_contest_classes.CLASSES}
    out["anchor_only_census"] = census(ao)
    out["mixed_inference_units"] = sorted(name for name in frozen_primary["p_base"]
                                          if frozen_primary["contest_classes"][name] == MIXED_INFERENCE)
    # Companion: the same census, a companion reading only (never a verdict).
    k_rows = unit_rows(companion["control"], companion["treatment"])
    frozen_companion = frozen[matrix.COMPANION_ARM]
    out["companion_sweep_backed_census"] = census(
        [k_rows[n] for n in frozen_companion["p_base"] if frozen_companion["contest_classes"][n] == SWEEP_BACKED])
    # E5-H3: E4 FMA transitions over P-PAR-E5 (continuity only).
    c3 = criteria["E5-H3"]
    e4_rows = analyze_e4.unit_rows(primary["control"], primary["treatment"], e4_table, fields=matrix.FIELD_IDS)
    ppar = [e4_rows[name] for name in frozen_record["p_par_e5"]["units"]]
    unchanged = sum(1 for row in ppar if row["transition"] in (analyze_e4.STAYS, analyze_e4.UNCHANGED_NEUTRAL))
    share_ok = len(ppar) > 0 and Fraction(unchanged, len(ppar)) >= _thresholds(c3, "supported_min")
    out["E5-H3"] = {**_share(unchanged, len(ppar)), "population": "P-PAR-E5",
                    "classes": dict(Counter(row["transition"] for row in ppar)),
                    "status": NOT_EVALUABLE if not ppar else (SUPPORTED if share_ok else REFUTED)}
    # E5-H4 / E5-H5 over every F1 cell.
    c4, c5 = criteria["E5-H4"], criteria["E5-H5"]
    p_keys = sorted(primary["control"]["F1"].cells)
    k_keys = sorted(companion["control"]["F1"].cells)
    p_change = outcome_change(primary["control"]["F1"], primary["treatment"]["F1"], p_keys)
    k_change = outcome_change(companion["control"]["F1"], companion["treatment"]["F1"], k_keys)
    p_share = None if not p_keys else Fraction(p_change["count"], p_change["of"])
    k_share = None if not k_keys else Fraction(k_change["count"], k_change["of"])
    out["E5-H4"] = {"primary": p_change, "status": status_of(
        p_share, _thresholds(c4, "supported_min"), _thresholds(c4, "refuted_max"))}
    diff = None if p_share is None or k_share is None else abs(k_share - p_share)
    out["E5-H5"] = {"primary": p_change, "companion": k_change,
                    "abs_difference": None if diff is None else exact_text(diff),
                    "status": status_of(diff, _thresholds(c5, "supported_min"), _thresholds(c5, "refuted_max"))}
    out["pathology"] = pathology_flags(primary["control"]["F1"], primary["treatment"]["F1"], criteria["PATHOLOGY"])
    completions = [c for f in matrix.FIELD_IDS for c in d9_completions(primary["treatment"][f])]
    out["D9"] = {"t_e5_completions": len(completions), "samples": completions[:10],
                 "t_e5k1_completions_reported": sum(len(d9_completions(companion["treatment"][f]))
                                                    for f in matrix.FIELD_IDS)}
    out["units"] = rows
    out["interpretation_inputs"] = {"E5-D": d_status, "E5-H1": out["E5-H1"]["status"], "E5-H2": out["E5-H2"]["status"]}
    out["interpretation"] = interpret(d_status, out["E5-H1"]["status"], out["E5-H2"]["status"], prereg)
    out["recorded"] = {h: out[h]["status"] for h in ("E5-H3", "E5-H4", "E5-H5")} | {
        name: flag["raised"] for name, flag in out["pathology"].items()}
    return out
