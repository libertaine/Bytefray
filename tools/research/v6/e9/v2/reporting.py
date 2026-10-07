"""Preserved scientific kernels and the amended historical-integrity override."""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from fractions import Fraction
from pathlib import Path
from typing import Any

from .records import BASE, IntegrityError, integer, make_record, strict_json, write_once


def rational(value: Any) -> Fraction:
    if type(value) is Fraction:
        return value
    if type(value) is str:
        try:
            result = Fraction(value)
        except (ValueError, ZeroDivisionError) as e:
            raise IntegrityError("invalid exact rational") from e
        if value != f"{result.numerator}/{result.denominator}":
            raise IntegrityError("reduced rational string required")
        return result
    raise IntegrityError("exact rational input required")


def row_intervals(means: Mapping[str, Fraction], envelope: Fraction) -> dict[str, tuple[Fraction, Fraction]]:
    envelope = rational(envelope)
    r = max(Fraction(1, 20), envelope)
    if envelope < 0 or not means:
        raise IntegrityError("nonempty rows and nonnegative envelope required")
    out = {}
    for name, mean in means.items():
        m = rational(mean)
        if not 0 <= m <= 1:
            raise IntegrityError("payoff mean out of bounds")
        out[name] = max(Fraction(0), m - r), min(Fraction(1), m + r)
    return out


def contrast_interval(treatment: tuple[Fraction, Fraction],
                      comparators: Sequence[tuple[Fraction, Fraction]]) -> tuple[Fraction, Fraction]:
    if not comparators:
        raise IntegrityError("comparator set cannot be empty")
    for low, high in (treatment, *comparators):
        if rational(low) > rational(high):
            raise IntegrityError("interval endpoints reversed")
    return (treatment[0] - max(c[1] for c in comparators),
            treatment[1] - max(c[0] for c in comparators))


def contrast_status(low: Fraction, high: Fraction) -> str:
    low, high = rational(low), rational(high)
    if low > high:
        raise IntegrityError("interval endpoints reversed")
    return "SUPPORTED" if low >= Fraction(1, 10) else (
        "REFUTED" if high < Fraction(1, 10) else "UNRESOLVED")


def timing_reproduced(schedule_fixed_lower: Fraction, adaptive_schedule_upper: Fraction) -> bool:
    return rational(schedule_fixed_lower) >= Fraction(1, 10) and rational(
        adaptive_schedule_upper) <= Fraction(1, 10)


def classify_report(*, integrity: bool, realized_positions: int, seat_a_positions: int,
                    seat_b_positions: int, statuses: Mapping[str, str],
                    severe_constraints: tuple[str, ...] = (), historical_integrity: str = "INTACT",
                    gates_valid: bool = False, claim_profile: str = "C-LIMITED",
                    realized_revisions: int | None = None, timing_reproduction: bool = False
                    ) -> dict[str, Any]:
    from tools.research.v6.e9.interpretation import classify
    from tools.research.v6.e9.protocol import IntegrityError as V1Error
    if type(gates_valid) is not bool or claim_profile != "C-LIMITED":
        raise IntegrityError("frozen profile and explicit gates required")
    integer(realized_positions, 0, 1412)
    integer(seat_a_positions, 0, 1412)
    integer(seat_b_positions, 0, 1412)
    valid_history = {"INTACT", "HOLD_PENDING_ADJUDICATION", "HISTORICAL_OVERLAP",
                     "UNRESOLVED_HISTORICAL_INTEGRITY", "CANCELLED_PRECOLLECTION"}
    if historical_integrity not in valid_history:
        raise IntegrityError("unknown historical integrity")
    try:
        scientific = classify(integrity=integrity,
                              realized_revisions=realized_positions if realized_revisions is None
                              else realized_revisions, realized_positions=realized_positions,
                              seat_positions={"A": seat_a_positions, "B": seat_b_positions},
                              statuses=statuses, severe_constraints=severe_constraints,
                              timing_reproduced=timing_reproduction)
    except V1Error as e:
        raise IntegrityError(str(e)) from e
    contract = strict_json((BASE / "amended_rule_contract_v2_proposed_02.json").read_bytes())
    eligible = scientific.priority == 7 and historical_integrity == "INTACT" and gates_valid
    effective = scientific.primary
    if historical_integrity == "HOLD_PENDING_ADJUDICATION":
        effective = "INTEGRITY_HOLD_PENDING_ADJUDICATION"
    elif historical_integrity in ("HISTORICAL_OVERLAP", "UNRESOLVED_HISTORICAL_INTEGRITY"):
        effective = "NOT EVALUABLE"
    elif historical_integrity == "CANCELLED_PRECOLLECTION":
        effective = "NOT PRODUCED"
    return {
        "scientific_priority_row": None if historical_integrity == "CANCELLED_PRECOLLECTION"
        else scientific.priority,
        "scientific_classification": None if historical_integrity == "CANCELLED_PRECOLLECTION"
        else scientific.primary,
        "historical_integrity": historical_integrity, "effective_registered_status": effective,
        "requirement_C_eligible": eligible,
        "requirement_C": "ESTABLISHED in the registered bounded scope with permanent historical non-reuse limitation"
        if eligible else "NOT ESTABLISHED",
        "F_D_S_H_statuses": dict(statuses) if integrity else dict.fromkeys(statuses, "NOT EVALUABLE"),
        "historical_superiority": scientific.historical, "qualifiers": list(scientific.qualifiers),
        "historical_coverage": "NOT ESTABLISHED",
        "permanent_limitation": contract["exact_interpretation"]["permanent_limitation_text"],
    }


def evaluate_constraints(evidence: Mapping, protocol: dict, *, n: int = 1412) -> dict:
    """Pure synthetic fixture adapter to the exact preserved four-constraint kernel."""
    from tools.research.v6.e9.constraints import evaluate
    from tools.research.v6.e9.protocol import IntegrityError as V1Error
    integer(n, 1, 1412)
    for item in evidence.values():
        if type(item) is not dict:
            raise IntegrityError("complete per-cell diagnostics required")
        integer(item.get("payoff_doubled"), 0, 2)
        if item.get("terminal") not in {"tick_limit", "last_agent_standing", "all_agents_dead"}:
            raise IntegrityError("unknown authoritative terminal class")
        for key in ("pressure", "captures"):
            if type(item.get(key)) is not dict or set(item[key]) != {"A", "B"}:
                raise IntegrityError("both victim directions required")
            if any(type(v) is not bool for v in item[key].values()):
                raise IntegrityError("explicit pressure/capture predicates required")
    try:
        return evaluate(evidence, protocol, n=n)
    except V1Error as e:
        raise IntegrityError(str(e)) from e


def seal_final(path: Path, body: dict) -> str:
    """Seal complete machine evidence first; caller must hold finalization authority.

    This low-level serializer never publishes prose or grants promotion authority.
    """
    record = make_record("F", body)
    counts = body["counts"]
    if type(counts) is not dict or not {"physical_cells", "started_attempts", "failed_attempts",
                                         "realized_revisions", "realized_positions",
                                         "seat_positions"} <= counts.keys():
        raise IntegrityError("complete result/attempt/incidence denominators required")
    for name in ("physical_cells", "started_attempts", "failed_attempts", "realized_revisions",
                 "realized_positions"):
        integer(counts[name])
    if body["requirement_C_eligible"] and (counts["physical_cells"] != 900856
            or body["scientific_priority_row"] != 7 or body["historical_integrity"] != "INTACT"):
        raise IntegrityError("incomplete/invalid row cannot establish Requirement C")
    # PG-R9: historical integrity takes precedence; separate fields must agree.
    history = body["historical_integrity"]
    effective = {"HOLD_PENDING_ADJUDICATION": "INTEGRITY_HOLD_PENDING_ADJUDICATION",
                 "HISTORICAL_OVERLAP": "NOT EVALUABLE", "UNRESOLVED_HISTORICAL_INTEGRITY": "NOT EVALUABLE",
                 "CANCELLED_PRECOLLECTION": "NOT PRODUCED"}.get(history, body["scientific_classification"])
    established = "ESTABLISHED in the registered bounded scope with permanent historical non-reuse limitation"
    if (body["effective_registered_status"] != effective
            or body["requirement_C"] != (established if body["requirement_C_eligible"] else "NOT ESTABLISHED")
            or (history == "CANCELLED_PRECOLLECTION") != (body["scientific_priority_row"] is None)
            or history == "CANCELLED_PRECOLLECTION" and body["scientific_classification"] is not None):
        raise IntegrityError("final record fields contradict historical-integrity precedence")
    row = body["scientific_priority_row"]
    if row is not None and reproduce_row(body) != row:
        raise IntegrityError("scientific row, label and contrast statuses do not reproduce the frozen table")
    return write_once(path, record)


ROW_LABELS = {1: "NOT EVALUABLE", 2: "REFUTED bounded benefit claim", 3: "NOT EVALUABLE",
              4: "REFUTED bounded benefit claim", 5: "Behavior demonstrated; benefit NEITHER",
              6: "Behavior demonstrated; benefit NEITHER", 7: "SUPPORTED beneficial adaptation"}
# Registered interaction-constraint flags as the inherited constraint kernel names them.
SEVERE_PREFIXES = ("stall/", "immunity/", "phase/")
SEAT_DEPENDENCE = "seat dependence"
TIMING_QUALIFIER = "timing explanation unresolved"


def reproduce_row(body: dict) -> int:
    """Re-derive the priority row from F's own inputs by the frozen ordered table.

    I, Z, B, the F/D/S gates and the severe constraints come from the recorded
    statuses, counts and qualifiers, never from the stored row or label. The
    inherited classification kernel must then reproduce every qualifier exactly.
    """
    statuses, counts, qualifiers = body["F_D_S_H_statuses"], body["counts"], body["qualifiers"]
    seats = counts["seat_positions"]
    if (type(qualifiers) is not list or any(type(q) is not str for q in qualifiers)
            or type(seats) is not dict or set(seats) != {"A", "B"}
            or any(type(n) is not int or n < 0 for n in seats.values())):
        raise IntegrityError("F lacks explicit qualifiers or seat realization counts")
    integrity = any(value != "NOT EVALUABLE" for value in statuses.values())
    if integrity and "NOT EVALUABLE" in statuses.values():
        raise IntegrityError("partially evaluable F/D/S/H statuses")
    gates = [statuses[g] for g in ("F", "D", "S")]
    severe = tuple(q for q in qualifiers if q.startswith(SEVERE_PREFIXES) or q == SEAT_DEPENDENCE)
    behavior = counts["realized_positions"] >= 2 and all(n >= 1 for n in seats.values())
    if not integrity:
        row = 1
    elif counts["realized_revisions"] == 0:
        row = 2
    elif not behavior:
        row = 3
    elif "REFUTED" in gates:
        row = 4
    elif any(gate != "SUPPORTED" for gate in gates):
        row = 5
    elif severe:
        row = 6
    else:
        row = 7
    from tools.research.v6.e9.interpretation import classify
    from tools.research.v6.e9.protocol import IntegrityError as V1Error
    try:
        kernel = classify(integrity=integrity, realized_revisions=counts["realized_revisions"],
                          realized_positions=counts["realized_positions"], seat_positions=seats,
                          statuses=statuses, severe_constraints=severe,
                          timing_reproduced=integrity and TIMING_QUALIFIER in qualifiers)
    except V1Error as e:
        raise IntegrityError(str(e)) from e
    if (kernel.priority != row or body["scientific_classification"] != ROW_LABELS[row]
            or kernel.primary != ROW_LABELS[row] or list(kernel.qualifiers) != qualifiers
            or kernel.historical != body["historical_superiority"]):
        raise IntegrityError("F inputs do not reproduce the frozen table row, label, qualifiers or H text")
    return row
