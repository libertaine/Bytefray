"""The frozen E8 gameplay analysis (PR8 Sec 4 to 8; phase I8-5).

docs/research/v6/V6_E8_ACTIVE_SPATIAL_SENSING_PREREGISTRATION.md (PR8). One arm
is a (control, treatment) pair: the primary arm C8 -> T8 and the companion
C8L -> T8L, both computed by **the same code** (PR8 Sec 6.6). From each
condition's harness cells (F1 and F2), each F1 cell's replay-derived hostile
core contact, and each cell's descriptive telemetry, ``analyze_arm``
computes, without E8-D:

* H8-SUB and H8-PAR (P_none), H8-CHANNEL (Q_none), H8-LESS (L8),
  H8-REPEAT (Delta^R over the frozen census), H8-FL, H8-TAX, H8-SEAT with
  PF8-4 (the two seat layers, from one jointly drawn seed multiset per
  resample), PF8-1 to PF8-5, and KC8-1 to KC8-6;
* O-VERIF's V(j), the allocation-variation check, and H8-ADAPT when, and
  only when, it is interpretable (PR8 Sec 7.3);
* the registered reporting: the payoff tables (Sec 6.4), the phase-sensitive
  stratum, decisive-tick parity and the mechanism tables (Sec 6.3), and the
  descriptive telemetry (Sec 6.5).

**Every status, reading, label and order comes from ``decision``** (phase
I8-0), which reads the frozen transcription. This module supplies only the
predicates' inputs. ``interpret`` combines E8-D with these statuses, and
only after the reveal and D8-10 (PR8 Sec 9, step 7); ``control_against_
control`` is CQ8-4.

**Seat metrics.** E4's ``pairing_seat_metrics`` and ``mirror_seat_metrics``
key cells by seed, so they cannot take a resampled multiset. Every resample
uses the post-hoc audit's per-seed decomposition
(``tools/research/v6/e6_audit/seat.py``), which computes the same GSB and
SDom with multiplicity; at the point estimate each unit's values are checked
against E4's own, and any difference fails closed.

Every ratio is an exact ``Fraction``; JSON carries it as ``"n/d"``.
"""

from __future__ import annotations

import json
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any

from tools.research.v6.e3.analyze_e3 import outcome_class
from tools.research.v6.e3.gates import cell_key
from tools.research.v6.e4.analyze_e4 import (
    is_capture,
    make_field_run,
    mirror_seat_metrics,
    pairing_seat_metrics,
)
from tools.research.v6.e4.cell_metrics import parse_exact
from tools.research.v6.e6.analyze_e6 import hostile_core_contact as e6_hostile_core_contact
from tools.research.v6.e6_audit import seat as pa_seat
from tools.research.v6.e8 import decision, family, payoff, telemetry
from tools.research.v6.experiment_harness import (
    ORIENTATION_CANDIDATE_FIRST,
    SEAT_A,
    SEAT_B,
    TICK_LIMIT_REASON,
    cell_seat_result,
    cell_seats,
)

E8_ANALYSIS_VERSION = 1
FORCED_LINE_TICK: int = decision.REGISTRATION["operationalizations"]["O-EARLY"]["forced_line_tick_max"]
PF_SHIFT: Fraction = Fraction(1, 10)  # PF8-1 and PF8-2: a rise of at least 1/10 (PR8 Sec 6.1)
CHANNEL_DIFFERENCE: tuple[str, ...] = tuple(
    decision.REGISTRATION["member_semantics"]["channel_difference"][key]["text"]
    for key in ("passive", "c8_consequence", "active", "standing"))

Cell = Mapping[str, Any]


class AnalysisError(RuntimeError):
    """The cells do not support a registered quantity, or a cross-check disagrees."""


def text(value: Fraction | None) -> str | None:
    return None if value is None else f"{value.numerator}/{value.denominator}"


def hostile_core_contact(replay_path: Path) -> bool:
    """O-CONTACT (PR8 Sec 4): E6's replay reading, unchanged -- some entrant writes a cell of the opponent's core."""
    return e6_hostile_core_contact(replay_path)


def member_of() -> dict[str, str]:
    return {pid: member for pid, (member, _role) in family.PACKAGES.items()}


def census() -> tuple[str, ...]:
    """The frozen census, from the primary packages' manifests (PR8 Sec 3.5; the family freeze)."""
    return family.census("primary")


# ---------------------------------------------------------------------------
# Inputs
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ConditionData:
    """One condition: its harness cells, each F1 cell's contact, and each cell's telemetry by schedule id."""

    condition_id: str
    f1: tuple[Cell, ...]
    f2: tuple[Cell, ...]
    contact: Mapping[str, bool]
    telemetry: Mapping[str, Mapping[str, Mapping[str, Any]]]


@dataclass(frozen=True)
class ConditionReading:
    table: payoff.ValueTable
    point: payoff.Reading
    counts: Mapping[str, int]


def read_condition(cells: Iterable[Cell], *, seeds: Sequence[int], census_members: Sequence[str],
                   draws: Sequence[Sequence[int]] = decision.DRAWS) -> ConditionReading:
    table = payoff.member_table(cells, member_of=member_of(), seeds=seeds)
    point = payoff.reading(table)
    counts = payoff.stability_counts(table, payoff.registered_predicates(census_members), draws)
    return ConditionReading(table, point, counts)


# ---------------------------------------------------------------------------
# Hypotheses
# ---------------------------------------------------------------------------


def h8_choice(reading: ConditionReading) -> str:
    """H8-SUB on T8, and H8-PAR on C8: P_none, refuted by not P_none."""
    return decision.complement_status(reading.point.p_none, reading.counts["P_none"])


def h8_channel(reading: ConditionReading) -> str:
    return decision.complement_status(reading.point.q_none, reading.counts["Q_none"])


def h8_less(reading: ConditionReading) -> str:
    return decision.bootstrap_status(reading.point.p_win, reading.counts["P_win"],
                                     reading.point.p_never, reading.counts["P_never"])


def h8_repeat(reading: ConditionReading, census_members: Sequence[str]) -> str:
    if not census_members:
        return decision.repeat_status(census_members)
    return decision.repeat_status(census_members, reading.point.repeat_for(census_members),
                                  reading.counts["repeat_for"], reading.point.repeat_against(census_members),
                                  reading.counts["repeat_against"])


def h8_adapt_status(reading: ConditionReading) -> str:
    return decision.bootstrap_status(reading.point.adapt_for, reading.counts["adapt_for"],
                                     reading.point.adapt_against, reading.counts["adapt_against"])


def tax(control_f1: Iterable[Cell], treatment_f1: Iterable[Cell]) -> dict[str, Any]:
    """H8-TAX: A over the paired F1 cells, B over exactly the cells A counts (PR6 Sec 5.3's E6-H0)."""
    control = {cell_key(cell): cell for cell in control_f1}
    treatment = {cell_key(cell): cell for cell in treatment_f1}
    if set(control) != set(treatment) or not control:
        raise AnalysisError("H8-TAX: the F1 cells of the two conditions do not pair")
    same = [key for key in control if outcome_class(control[key]) == outcome_class(treatment[key])]
    later = [key for key in same if int(treatment[key]["ticks_run"]) >= int(control[key]["ticks_run"])]
    a = Fraction(len(same), len(control))
    b = Fraction(len(later), len(same)) if same else None
    return {"status": decision.tax_status(a, b), "paired": len(control), "same_class": len(same),
            "not_earlier": len(later), "A": text(a), "B": text(b), "_a": a, "_b": b}


def _seat_of(cell: Cell, package: str) -> str:
    seat_a, seat_b = cell_seats(cell)
    if package == seat_a:
        return SEAT_A
    if package == seat_b:
        return SEAT_B
    raise AnalysisError(f"{package} is not in cell {cell.get('schedule_id')}")


def captured(cell: Cell, package: str) -> bool:
    return (cell.get("entrant_terminations") or {}).get(_seat_of(cell, package)) == "core_captured"


def forced_line_capture(cell: Cell, defender_package: str) -> bool:
    """O-EARLY: a capture of the defender at a tick <= 3."""
    return captured(cell, defender_package) and int(cell["ticks_run"]) <= FORCED_LINE_TICK


def _pair_cells(f1: Iterable[Cell]) -> dict[frozenset[str], list[Cell]]:
    names = member_of()
    out: dict[frozenset[str], list[Cell]] = {}
    for cell in f1:
        out.setdefault(frozenset(names[p] for p in cell_seats(cell)), []).append(cell)
    return out


def fl(treatment_f1: Iterable[Cell], *, seed_count: int) -> dict[str, Any]:
    """H8-FL over FL(a, d), each over the 64 F1 matches of a against d."""
    by_pair = _pair_cells(treatment_f1)
    values: dict[tuple[str, str], Fraction] = {}
    for attacker in decision.ATTACKERS:
        for defender in decision.DEFENDERS:
            cells = by_pair.get(frozenset((attacker, defender)), [])
            if len(cells) != 2 * seed_count:
                raise AnalysisError(f"H8-FL: {attacker} v {defender} has {len(cells)} F1 matches, not {2 * seed_count}")
            defender_package = family.package_id(defender)
            values[(attacker, defender)] = Fraction(sum(forced_line_capture(c, defender_package) for c in cells),
                                                    len(cells))
    return {"status": decision.fl_status(values),
            "FL": {a: {d: text(values[(a, d)]) for d in decision.DEFENDERS} for a in decision.ATTACKERS},
            "min_over_defenders": {a: text(min(values[(a, d)] for d in decision.DEFENDERS))
                                   for a in decision.ATTACKERS}}


# ---------------------------------------------------------------------------
# The seat criterion (Sec 6.2) and its strata (Sec 6.3)
# ---------------------------------------------------------------------------

SeatResults = Mapping[decision.SeatUnit, Sequence[Any]]


def seat_results(condition: ConditionData, *, seeds: Sequence[int]) -> dict[decision.SeatUnit, list[Any]]:
    """Per unit, the per-seed seat results in seed-list order: a pairing's (X in A, Y in A) results,
    and a mirror's candidate-first result."""
    position = {seed: k for k, seed in enumerate(seeds)}
    names = member_of()
    pair_results: dict[tuple[str, str], list[Any]] = {}
    for cell in condition.f1:
        seat_a, seat_b = cell_seats(cell)
        row = pair_results.setdefault((names[seat_a], names[seat_b]), [None] * len(seeds))
        row[position[int(cell["seed"])]] = cell_seat_result(cell)
    mirror_results: dict[str, list[Any]] = {}
    for cell in condition.f2:
        subject, opponent = str(cell["subject_id"]), str(cell["opponent_id"])
        member, role = family.PACKAGES[subject]
        if role == "primary" and family.PACKAGES[opponent] == (member, "twin") \
                and cell.get("orientation") == ORIENTATION_CANDIDATE_FIRST:
            row = mirror_results.setdefault(member, [None] * len(seeds))
            row[position[int(cell["seed"])]] = cell_seat_result(cell)
    out: dict[decision.SeatUnit, list[Any]] = {}
    for unit in decision.SEAT_UNITS:
        if unit[0] == "pairing":
            x, y = unit[1], unit[2]
            first, second = pair_results.get((x, y)), pair_results.get((y, x))
            if first is None or second is None or None in first or None in second:
                raise AnalysisError(f"seat unit {unit}: a pairing orientation or seed is missing")
            out[unit] = list(zip(first, second, strict=True))
        else:
            results = mirror_results.get(unit[1])
            if results is None or None in results:
                raise AnalysisError(f"seat unit {unit}: a mirror seed is missing")
            out[unit] = list(results)
    return out


def unit_metrics(unit: decision.SeatUnit, results: Sequence[Any],
                 positions: Sequence[int] | None = None) -> tuple[Fraction, Fraction]:
    """(SDom, GSB) of one unit over a seed-position multiset (all seeds by default)."""
    drawn = list(results) if positions is None else [results[k] for k in positions]
    if unit[0] == "pairing":
        gsb, sdom = pa_seat.pairing_metrics(drawn)
    else:
        gsb, sdom = pa_seat.mirror_metrics(drawn)
    return sdom, gsb


def check_against_e4(condition: ConditionData, results: SeatResults) -> None:
    """At the point estimate, the per-seed decomposition must equal E4's own seat metrics, unit by unit."""
    f1 = make_field_run(condition.condition_id, "F1", condition.f1, {})
    f2 = make_field_run(condition.condition_id, "F2", condition.f2, {})
    for unit in decision.SEAT_UNITS:
        if unit[0] == "pairing":
            e4 = pairing_seat_metrics(f1, family.package_id(unit[1]), family.package_id(unit[2]))
        else:
            e4 = mirror_seat_metrics(f2, family.package_id(unit[1]), family.package_id(unit[1], "twin"))
        expected = (parse_exact(e4["exact"]["sdom"]), parse_exact(e4["exact"]["gsb"]))
        if unit_metrics(unit, results[unit]) != expected:
            raise AnalysisError(f"{condition.condition_id} {unit}: the seat decomposition {unit_metrics(unit, results[unit])} "
                                f"differs from E4's {expected}")


def seat_source(results: Mapping[str, SeatResults]) -> decision.SeatSource:
    def source(condition_id: str, unit: decision.SeatUnit, positions: tuple[int, ...] | None) -> tuple[Fraction, Fraction]:
        return unit_metrics(unit, results[condition_id][unit], positions)
    return source


def delta_g_draws(results: Mapping[str, SeatResults], *, control: str, treatment: str,
                  units: Sequence[decision.SeatUnit] = decision.SEAT_UNITS,
                  draws: Sequence[tuple[int, ...]] = decision.DRAWS) -> list[Fraction]:
    """ΔG in every registered draw, each from one jointly drawn seed multiset (for CQ8-4 and the strata)."""
    source = seat_source(results)
    out = []
    for positions in draws:
        c = {u: source(control, u, positions)[1] for u in units}
        t = {u: source(treatment, u, positions)[1] for u in units}
        out.append(decision.delta_g(c, t, units))
    return out


def phase_sensitive(unit: decision.SeatUnit) -> bool:
    return bool(set(unit[1:]) & set(decision.PHASE_SENSITIVE))


def unit_name(unit: decision.SeatUnit) -> str:
    return "|".join(unit)


def stratum_report(results: Mapping[str, SeatResults], *, control: str, treatment: str,
                   units: Sequence[decision.SeatUnit]) -> dict[str, Any]:
    """ΔG over one stratum of units: the point value and the registered quantiles (descriptive)."""
    if not units:
        return {"units": 0, "delta_g": None, "quantiles": None}
    source = seat_source(results)
    point = decision.delta_g({u: source(control, u, None)[1] for u in units},
                             {u: source(treatment, u, None)[1] for u in units}, units)
    samples = delta_g_draws(results, control=control, treatment=treatment, units=units)
    return {"units": len(units), "delta_g": text(point),
            "quantiles": {q: text(decision.quantile(samples, q)) for q in decision.QUANTILES}}


def seat_strata(results: SeatResults) -> dict[str, list[str]]:
    """CQ8-5: the C8-neutral and C8-non-neutral units, by O-NEUTRAL at the control's point estimate."""
    neutral = [unit_name(u) for u in decision.SEAT_UNITS if decision.neutral(*unit_metrics(u, results[u]))]
    return {"neutral": neutral,
            "non_neutral": [unit_name(u) for u in decision.SEAT_UNITS if unit_name(u) not in neutral]}


def decisive_parity(condition: ConditionData) -> dict[str, dict[str, int]]:
    """Sec 6.3: each unit's decisive outcomes by the parity of the decisive (final) tick and the winning seat."""
    names = member_of()
    out: dict[str, Counter[str]] = {}
    for cell in condition.f1:
        result = cell_seat_result(cell)
        if result not in (SEAT_A, SEAT_B):
            continue
        members = sorted((names[p] for p in cell_seats(cell)), key=decision.MEMBERS.index)
        key = unit_name(("pairing", *members))
        parity = "odd" if int(cell["ticks_run"]) % 2 else "even"
        out.setdefault(key, Counter())[f"{parity}:{result}"] += 1
    for cell in condition.f2:
        result = cell_seat_result(cell)
        if result not in (SEAT_A, SEAT_B) or cell.get("orientation") != ORIENTATION_CANDIDATE_FIRST:
            continue
        key = unit_name(("mirror", names[str(cell["subject_id"])]))
        parity = "odd" if int(cell["ticks_run"]) % 2 else "even"
        out.setdefault(key, Counter())[f"{parity}:{result}"] += 1
    return {key: dict(sorted(counter.items())) for key, counter in sorted(out.items())}


# ---------------------------------------------------------------------------
# Pathology flags, telemetry, mechanism tables
# ---------------------------------------------------------------------------


def _share(cells: Sequence[Cell], predicate: Any) -> Fraction:
    if not cells:
        raise AnalysisError("an empty field")
    return Fraction(sum(1 for cell in cells if predicate(cell)), len(cells))


def pathology(control: ConditionData, treatment: ConditionData) -> dict[str, Any]:
    """PF8-1 to PF8-3 on F1 (PF8-4 and PF8-5 come from the seat layers)."""
    c1, t1 = list(control.f1), list(treatment.f1)
    stall_c = _share(c1, lambda cell: cell.get("termination_reason") == TICK_LIMIT_REASON)
    stall_t = _share(t1, lambda cell: cell.get("termination_reason") == TICK_LIMIT_REASON)
    loss_c = _share(c1, lambda cell: not control.contact[cell_key(cell)])
    loss_t = _share(t1, lambda cell: not treatment.contact[cell_key(cell)])
    immune: list[str] = []
    for member in decision.PI_F:
        package = family.package_id(member)
        in_c = [cell for cell in c1 if package in cell_seats(cell)]
        in_t = [cell for cell in t1 if package in cell_seats(cell)]
        if any(captured(cell, package) for cell in in_c) and not any(captured(cell, package) for cell in in_t):
            immune.append(member)
    return {
        "PF8-1": {"raised": stall_t - stall_c >= PF_SHIFT, "control": text(stall_c), "treatment": text(stall_t)},
        "PF8-2": {"raised": loss_t - loss_c >= PF_SHIFT, "control": text(loss_c), "treatment": text(loss_t)},
        "PF8-3": {"raised": bool(immune), "members": immune},
    }


def _seat_member(cell: Cell, seat: str) -> str:
    seat_a, seat_b = cell_seats(cell)
    return member_of()[seat_a if seat == SEAT_A else seat_b]


def verification(condition: ConditionData, *, seeds: Sequence[int],
                 opponents: Sequence[str] = decision.PI) -> dict[str, Fraction]:
    """O-VERIF: V(j) for every opponent j of ADAPT8, from its F1 cells' telemetry.

    Under active the count is ADAPT8's verification SENSEs; under passive its
    verification observations (the module docstring of ``telemetry``)."""
    per: dict[str, dict[int, list[int]]] = {}
    for cell in condition.f1:
        for seat, rival in ((SEAT_A, SEAT_B), (SEAT_B, SEAT_A)):
            if _seat_member(cell, seat) != "ADAPT8":
                continue
            stats = condition.telemetry[str(cell["schedule_id"])][seat]
            count = stats["verifications"] + stats["verification_observations"]
            per.setdefault(_seat_member(cell, rival), {}).setdefault(int(cell["seed"]), []).append(count)
    out: dict[str, Fraction] = {}
    for j in opponents:
        if j == "ADAPT8":
            continue
        by_seed = per.get(j, {})
        if set(by_seed) != set(seeds):
            raise AnalysisError(f"O-VERIF: ADAPT8 v {j} lacks a seed")
        out[j] = telemetry.verification_v(by_seed)
    return out


def acquisition(condition: ConditionData) -> dict[str, Any]:
    """O-ACQ, O-REACQ and the mechanism quantities, by member over the F1 cells (descriptive)."""
    by_member: dict[str, Counter[str]] = {}
    no_discovery: Counter[str] = Counter()
    reacq: dict[str, Counter[str]] = {}
    for cell in condition.f1:
        stats = condition.telemetry[str(cell["schedule_id"])]
        members = {seat: _seat_member(cell, seat) for seat in (SEAT_A, SEAT_B)}
        if not any(stats[seat]["discovered"] for seat in members):
            no_discovery["|".join(sorted(members.values(), key=decision.MEMBERS.index))] += 1
        for seat, member in members.items():
            entry = stats[seat]
            total = by_member.setdefault(member, Counter())
            total["entrant_matches"] += 1
            total["discovered"] += bool(entry["discovered"])
            for name in ("senses_before_discovery", "senses_after_discovery", "read_probes", "hits_received",
                         "hits_inferred", "evasions", "verifications", "verification_observations", "callbacks",
                         "ticks_with_callbacks"):
                total[name] += int(entry[name])
            reacq.setdefault(member, Counter()).update(entry["reacquisitions"])
    return {"by_member": {m: dict(sorted(c.items())) for m, c in sorted(by_member.items())},
            "no_discovery_by_pairing": dict(sorted(no_discovery.items())),
            "reacquisitions_by_cause": {m: dict(sorted(c.items())) for m, c in sorted(reacq.items())}}


def mechanism_table(condition: ConditionData, unit: decision.SeatUnit) -> list[dict[str, Any]]:
    """Sec 6.3: the per-cell mechanics of one unit's cells."""
    names = member_of()
    rows = []
    cells = condition.f1 if unit[0] == "pairing" else condition.f2
    for cell in cells:
        members = frozenset(names[p] for p in cell_seats(cell))
        if (unit[0] == "pairing" and members == frozenset(unit[1:])) or (unit[0] == "mirror"
                                                                         and members == {unit[1]}):
            rows.append({"schedule_id": cell["schedule_id"], "seats": {s: _seat_member(cell, s) for s in "AB"},
                         "telemetry": condition.telemetry[str(cell["schedule_id"])]})
    return rows


# ---------------------------------------------------------------------------
# One arm
# ---------------------------------------------------------------------------


def analyze_arm(control: ConditionData, treatment: ConditionData, *, seeds: Sequence[int],
                census_members: Sequence[str] | None = None,
                draws: Sequence[tuple[int, ...]] = decision.DRAWS) -> dict[str, Any]:
    """Every registered quantity of one arm (PR8 Sec 5 to 6), without E8-D and without interpretation."""
    census_members = tuple(census() if census_members is None else census_members)
    read_t = read_condition(treatment.f1, seeds=seeds, census_members=census_members, draws=draws)
    read_c = read_condition(control.f1, seeds=seeds, census_members=census_members, draws=draws)
    sub, par, channel, less = h8_choice(read_t), h8_choice(read_c), h8_channel(read_t), h8_less(read_t)
    repeat = h8_repeat(read_t, census_members)
    tax_result = tax(control.f1, treatment.f1)
    fl_result = fl(treatment.f1, seed_count=len(seeds))
    results = {control.condition_id: seat_results(control, seeds=seeds),
               treatment.condition_id: seat_results(treatment, seeds=seeds)}
    check_against_e4(control, results[control.condition_id])
    check_against_e4(treatment, results[treatment.condition_id])
    layers = decision.seat_layers(seat_source(results), control=control.condition_id,
                                  treatment=treatment.condition_id, draws=draws)
    pf = pathology(control, treatment)
    pf["PF8-4"] = {"raised": layers.pf8_4_raised, "units": [unit_name(u) for u in layers.flagged]}
    pf["PF8-5"] = {"raised": layers.h8_seat == decision.SUPPORTED}
    v = verification(treatment, seeds=seeds)
    check = decision.allocation_check(v, census_members) if census_members else None
    adapt_raw = h8_adapt_status(read_t)
    preconditions = decision.REGISTRATION["interpretation"]["adapt"]["preconditions"]
    interpretable = bool(census_members) and sub == preconditions["H8-SUB"] and repeat == preconditions["H8-REPEAT"] \
        and check is preconditions["allocation_variation_check"]
    adapt = adapt_raw if interpretable else None
    kills = decision.kill_criteria(
        h8_sub=sub, universal=read_t.point.universal, greed_universal_count=read_t.counts["universal:GREED8"],
        pf8_1=pf["PF8-1"]["raised"], pf8_2=pf["PF8-2"]["raised"], h8_fl=fl_result["status"],
        pf8_4=layers.pf8_4_raised, h8_seat=layers.h8_seat, h8_channel=channel,
        universal_a8=read_t.point.universal_a8,
        seat_detail={"delta_g": text(layers.delta_g),
                     "flagged": [{"unit": unit_name(u), "phase_sensitive": phase_sensitive(u)}
                                 for u in layers.flagged]})
    strata_units = {
        "containing_phase_sensitive": [u for u in decision.SEAT_UNITS if phase_sensitive(u)],
        "not_containing_phase_sensitive": [u for u in decision.SEAT_UNITS if not phase_sensitive(u)],
    }
    mechanism_units = sorted(set(layers.flagged) | {("mirror", y) for y in census_members}
                             | {u for u in decision.SEAT_UNITS if u[0] == "pairing" and set(u[1:]) & set(census_members)})
    hypotheses = {"H8-SUB": sub, "H8-PAR": par, "H8-CHANNEL": channel, "H8-LESS": less, "H8-REPEAT": repeat,
                  "H8-FL": fl_result["status"], "H8-TAX": tax_result["status"], "H8-SEAT": layers.h8_seat}
    return {
        "analysis_version": E8_ANALYSIS_VERSION,
        "control": control.condition_id,
        "treatment": treatment.condition_id,
        "census": list(census_members),
        "hypotheses": hypotheses,
        "H8-ADAPT": {"interpretable": interpretable, "status": adapt,
                     "allocation_check": check, "V": {j: text(value) for j, value in v.items()},
                     "static_set": list(decision.static_set(census_members)) if census_members else None},
        "H8-TAX": {k: value for k, value in tax_result.items() if not k.startswith("_")},
        "H8-FL": fl_result,
        "seat": {
            "delta_g": text(layers.delta_g), "positive_count": layers.delta_g_positive_count,
            "nonpositive_count": layers.delta_g_nonpositive_count,
            "quantiles": {q: text(value) for q, value in layers.quantiles.items()},
            "flagged": [unit_name(u) for u in layers.flagged],
            "unit_stability": {unit_name(u): count for u, count in layers.unit_stability.items()},
            "units": {
                cond: {unit_name(u): {"sdom": text(unit_metrics(u, results[cond][u])[0]),
                                      "gsb": text(unit_metrics(u, results[cond][u])[1])}
                       for u in decision.SEAT_UNITS}
                for cond in (control.condition_id, treatment.condition_id)},
            "strata": {name: stratum_report(results, control=control.condition_id,
                                            treatment=treatment.condition_id, units=units)
                       for name, units in strata_units.items()},
            "decisive_parity": {cond.condition_id: decisive_parity(cond) for cond in (control, treatment)},
        },
        "pathology": pf,
        "kill_criteria": {name: {"fires": kill.fires,
                                 "label": None if kill.label is None else {"label": kill.label.label,
                                                                           "members": list(kill.label.members)},
                                 "detail": None if kill.detail is None else json.loads(json.dumps(dict(kill.detail)))}
                          for name, kill in kills.items()},
        "fired": [name for name, kill in kills.items() if kill.fires],
        "universal": sorted(read_t.point.universal, key=decision.MEMBERS.index),
        "universal_a8": sorted(read_t.point.universal_a8, key=decision.MEMBERS.index),
        "payoff": {"treatment": payoff.tables(read_t.table, read_t.point, read_t.counts),
                   "control": payoff.tables(read_c.table, read_c.point, read_c.counts)},
        "decided_by_capture": {"control": text(_share(list(control.f1), is_capture)),
                               "treatment": text(_share(list(treatment.f1), is_capture))},
        "telemetry": {"control": acquisition(control), "treatment": acquisition(treatment),
                      "verification_control": {j: text(value) for j, value in verification(control, seeds=seeds).items()}},
        "mechanism_tables": {unit_name(u): {"control": mechanism_table(control, u),
                                            "treatment": mechanism_table(treatment, u)} for u in mechanism_units},
        "channel_difference": list(CHANNEL_DIFFERENCE),
        "_seat_results": results,
        "_tax": (tax_result["_a"], tax_result["_b"]),
    }


def public(result: Mapping[str, Any]) -> dict[str, Any]:
    """An arm's result without its private working values (which hold no seed but are not reported)."""
    return {key: value for key, value in result.items() if not key.startswith("_")}


def statuses(result: Mapping[str, Any]) -> dict[str, str]:
    """Every registered status of one arm, H8-ADAPT's included where it has one."""
    out = dict(result["hypotheses"])
    if result["H8-ADAPT"]["status"] is not None:
        out["H8-ADAPT"] = result["H8-ADAPT"]["status"]
    return out


def control_against_control(result: Mapping[str, Any]) -> dict[str, Any]:
    """CQ8-4, with the control in the treatment slot (``decision.control_against_control``)."""
    hypotheses = result["hypotheses"]
    a, b = result["_tax"]
    control_id, treatment_id = result["control"], result["treatment"]
    if control_id != treatment_id:
        raise AnalysisError("CQ8-4 needs the control in the treatment slot")
    draws = delta_g_draws(result["_seat_results"], control=control_id, treatment=treatment_id)
    checks = decision.control_against_control(
        h8_sub=hypotheses["H8-SUB"], h8_par=hypotheses["H8-PAR"], h8_tax=hypotheses["H8-TAX"], a=a, b=b,
        pf8_raised={name: bool(result["pathology"][name]["raised"]) for name in ("PF8-1", "PF8-2", "PF8-3", "PF8-4")},
        flagged_units=len(result["seat"]["flagged"]), h8_seat=hypotheses["H8-SEAT"],
        delta_g_point=Fraction(result["seat"]["delta_g"]), delta_g_draws=draws,
        row=decision.row_for(decision.PASS, hypotheses["H8-SUB"], hypotheses["H8-PAR"]))
    return {"checks": {name: bool(value) for name, value in checks.items() if name != "PASS"},
            "status": decision.PASS if checks["PASS"] else decision.FAIL}


def companion_reading(primary: Mapping[str, Any], companion: Mapping[str, Any]) -> dict[str, Any]:
    reading = decision.companion_reading(
        primary["hypotheses"], companion["hypotheses"],
        {name: kill["fires"] for name, kill in primary["kill_criteria"].items()},
        {name: kill["fires"] for name, kill in companion["kill_criteria"].items()})
    return {"agrees": reading.agrees, "differences": list(reading.differences),
            "expectation": decision.REGISTRATION["companion"]["expectation"]["text"]
            if isinstance(decision.REGISTRATION["companion"]["expectation"], Mapping)
            else decision.REGISTRATION["companion"]["expectation"],
            "standing": "a status comparison, never a verdict"}


def interpret(*, e8_d: str, primary: Mapping[str, Any]) -> dict[str, Any]:
    """The registered interpretation of the primary arm (PR8 Sec 7 and 8). Only after D8-10."""
    hypotheses = primary["hypotheses"]
    row = decision.row_for(e8_d, hypotheses["H8-SUB"], hypotheses["H8-PAR"])
    core = decision.core_answer(e8_d=e8_d, h8_sub=hypotheses["H8-SUB"], h8_channel=hypotheses["H8-CHANNEL"],
                                h8_repeat=hypotheses["H8-REPEAT"])
    fired = [name for name in primary["fired"] if e8_d == decision.PASS]
    disposition = decision.disposition(e8_d=e8_d, fired=fired, row=row, h8_less=hypotheses["H8-LESS"], core=core)
    out: dict[str, Any] = {"E8-D": e8_d, "row": row.row_id, "reading": row.reading, "core_answer": core.outcome,
                           "core_scope_sentence": core.scope_sentence, "disposition": disposition}
    if e8_d == decision.FAIL:
        out["note"] = "STOP: no gameplay reading (PR8 Sec 7.1)."
        return out
    census_members = primary["census"]
    qualifiers = decision.qualifiers(row, h8_channel=hypotheses["H8-CHANNEL"], h8_less=hypotheses["H8-LESS"],
                                     h8_tax=hypotheses["H8-TAX"], universal_a8=primary["universal_a8"])
    repeat = decision.repeat_reading(hypotheses["H8-REPEAT"], census_members)
    adapt = decision.adapt_reading(h8_sub=hypotheses["H8-SUB"], h8_repeat=hypotheses["H8-REPEAT"],
                                   check=primary["H8-ADAPT"]["allocation_check"],
                                   h8_adapt=primary["H8-ADAPT"]["status"], census=census_members)
    out.update({
        "qualifiers": [{"hypothesis": q.hypothesis, "status": q.status, "text": q.text, "naming": q.naming,
                        "label": None if q.label is None else {"label": q.label.label, "members": list(q.label.members)}}
                       for q in qualifiers],
        "repeat": {"status": repeat.status, "text": repeat.text, "scope_sentence": repeat.scope_sentence},
        "adapt": {"interpretable": adapt.interpretable, "status": adapt.status, "text": adapt.text, "note": adapt.note},
        "fired": fired,
        "channel_difference": list(CHANNEL_DIFFERENCE),
        "recorded_alongside": {"H8-FL": hypotheses["H8-FL"], "H8-TAX": hypotheses["H8-TAX"],
                               "pathology": {k: v["raised"] for k, v in primary["pathology"].items()}},
    })
    return out
