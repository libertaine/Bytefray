"""The frozen E6 gameplay analysis (pre-registration Sec 4-8, 10.3).

One arm is a (control, treatment) pair: the primary arm is C-E6 -> T-E6 and
the companion C-E6L -> T-E6L, both computed by the same code (PR Sec 6.8).
From the harness cells of both conditions (F1 and F2), each F1 cell's
replay-derived hostile core contact, and nothing else, ``analyze_arm``
computes:

* E6-H1T and E6-H1C (O-BR, O-BOOT), E6-H2 (O-CONTRAST), E6-H0 (A and B over
  the paired F1 cells) and E6-H3 (FL);
* PF-1 to PF-4, KC-1 to KC-5, and the Sec 6.4 payoff tables, each entry with
  its n_distinct and stability;
* the Sec 6.7 ADAPT reading, which is secondary and never an input to a row
  or a kill.

E6-D (the gates plus D-6) is not computed here. ``interpretation.interpret``
combines it with these statuses, and only after the seed reveal (PR Sec 9,
step 7). ``companion_reading`` implements PR Sec 6.8, and
``control_against_control`` the readings PR Sec 10.3 requires before any
treatment exists.

Every ratio and threshold is an exact ``Fraction``; JSON carries it as
``"n/d"`` text.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any

from battle_engine.replay import ReplayHeader, TickSnapshot, iter_replay

from tools.research.v6.e3.analyze_e3 import outcome_class
from tools.research.v6.e3.gates import cell_key
from tools.research.v6.e4.analyze_e4 import (
    is_capture,
    make_field_run,
    mirror_seat_metrics,
    pairing_seat_metrics,
)
from tools.research.v6.e4.cell_metrics import parse_exact
from tools.research.v6.e6 import family, payoff
from tools.research.v6.e6.interpretation import NEITHER, REFUTED, SUPPORTED, kc1_label
from tools.research.v6.experiment_harness import TICK_LIMIT_REASON, cell_seats

E6_ANALYSIS_VERSION = 1
NINE_TENTHS = Fraction(9, 10)
TWO_THIRDS = Fraction(2, 3)
ONE_TENTH = Fraction(1, 10)
FORCED_LINE_TICK = 3
ATTACKERS: tuple[str, ...] = ("RUSH", "PACED", "SPLIT", "STEALTH", "LURK")
DEFENDERS: tuple[str, ...] = ("GUARD", "EVADER")
CORE_SIZE = 8

Cell = Mapping[str, Any]


def text(value: Fraction | None) -> str | None:
    return None if value is None else f"{value.numerator}/{value.denominator}"


def member_of() -> dict[str, str]:
    return {pid: member for pid, (member, _role) in family.PACKAGES.items()}


# ---------------------------------------------------------------------------
# Inputs
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ConditionData:
    """One condition's harness cells and each F1 cell's hostile core contact (by cell key)."""

    condition_id: str
    f1: tuple[Cell, ...]
    f2: tuple[Cell, ...]
    contact: Mapping[str, bool]


def hostile_core_contact(replay_path: Path) -> bool:
    """O-CONTACT: some entrant writes a cell of the opponent's core (replay memory diffs; tick-0 cores)."""
    cores: dict[str, set[int]] = {}
    arena: int | None = None
    for record in iter_replay(replay_path):
        if isinstance(record, ReplayHeader):
            arena = record.config.arena_size
            continue
        if not isinstance(record, TickSnapshot):
            continue
        if arena is None:
            raise ValueError(f"{replay_path}: tick record before the header")
        if record.tick == 0:
            cores = {agent.agent_id: {(agent.pc + i) % arena for i in range(CORE_SIZE)} for agent in record.agents}
            continue
        for diff in record.memory_diffs:
            if diff.owner is None:
                continue
            for i in range(diff.length):
                address = (diff.address + i) % arena
                for owner, cells in cores.items():
                    if owner != diff.owner and address in cells:
                        return True
    return False


# ---------------------------------------------------------------------------
# Hypotheses
# ---------------------------------------------------------------------------


def _status(point: bool, stab: Fraction, point_against: bool, stab_against: Fraction) -> str:
    if point and stab >= NINE_TENTHS:
        return SUPPORTED
    if point_against and stab_against >= NINE_TENTHS:
        return REFUTED
    return NEITHER


def _predicates(members: Sequence[str]) -> dict[str, payoff.Predicate]:
    """Every stability PR Sec 5.3 and 6.4 report, over one resample."""
    fixed = [m for m in members if m in family.FIXED_MEMBERS]
    out: dict[str, payoff.Predicate] = {
        "P_none": lambda r: r.p_none,
        "not P_none": lambda r: not r.p_none,
        "P_win": lambda r: r.p_win,
        "P_never": lambda r: r.p_never,
    }
    for i in fixed:
        out[f"universal:{i}"] = lambda r, i=i: i in r.universal
        for j in members:
            out[f"br:{i}:{j}"] = lambda r, i=i, j=j: i in r.br[j]
    for lo, hi in payoff.LOWER_INFORMATION:
        for j in members:
            out[f"delta_win:{lo}:{hi}:{j}"] = lambda r, lo=lo, hi=hi, j=j: r.delta[(lo, hi, j)] >= payoff.EPSILON
            out[f"delta_never:{lo}:{hi}:{j}"] = lambda r, lo=lo, hi=hi, j=j: r.delta[(lo, hi, j)] <= 0
    return out


@dataclass(frozen=True)
class ConditionReading:
    table: payoff.ValueTable
    point: payoff.Reading
    stab: Mapping[str, Fraction]
    adapt_br: Mapping[str, frozenset[str]]


def read_condition(cells: Iterable[Cell], *, seeds: Sequence[int],
                   draws: Sequence[Sequence[int]] | None = None) -> ConditionReading:
    members = family.OPPONENTS
    table = payoff.value_table(cells, member_of=member_of(), members=members, seeds=seeds)
    candidates, opponents = family.FIXED_MEMBERS, family.OPPONENTS
    point = payoff.reading(table, candidates=candidates, opponents=opponents)
    stab = payoff.stabilities(table, _predicates(members), candidates=candidates, opponents=opponents, draws=draws)
    adapt_br = payoff.best_responses(point.u, candidates=(*candidates, "ADAPT"), opponents=opponents)
    return ConditionReading(table, point, stab, adapt_br)


def h1(reading: ConditionReading) -> str:
    p = reading.point.p_none
    return _status(p, reading.stab["P_none"], not p, reading.stab["not P_none"])


def h2(reading: ConditionReading) -> str:
    return _status(reading.point.p_win, reading.stab["P_win"], reading.point.p_never, reading.stab["P_never"])


def h0(control_f1: Iterable[Cell], treatment_f1: Iterable[Cell]) -> dict[str, Any]:
    """E6-H0: A over the paired F1 cells, B over the cells A counts."""
    control = {cell_key(cell): cell for cell in control_f1}
    treatment = {cell_key(cell): cell for cell in treatment_f1}
    if set(control) != set(treatment) or not control:
        raise payoff.PayoffDataError("E6-H0: the F1 cells of the two conditions do not pair")
    same = [key for key in control if outcome_class(control[key]) == outcome_class(treatment[key])]
    later = [key for key in same if int(treatment[key]["ticks_run"]) >= int(control[key]["ticks_run"])]
    a = Fraction(len(same), len(control))
    b = Fraction(len(later), len(same)) if same else None
    if a >= NINE_TENTHS and b is not None and b >= NINE_TENTHS:
        status = SUPPORTED
    elif a <= TWO_THIRDS:
        status = REFUTED
    else:
        status = NEITHER
    return {"status": status, "paired": len(control), "same_class": len(same), "not_earlier": len(later),
            "A": text(a), "B": text(b)}


def _seat_of(cell: Cell, package: str) -> str:
    seat_a, seat_b = cell_seats(cell)
    if package == seat_a:
        return "A"
    if package == seat_b:
        return "B"
    raise ValueError(f"{package} is not in cell {cell.get('schedule_id')}")


def captured(cell: Cell, package: str) -> bool:
    return (cell.get("entrant_terminations") or {}).get(_seat_of(cell, package)) == "core_captured"


def forced_line_capture(cell: Cell, defender_package: str) -> bool:
    """O-EARLY: the match ends by the core capture of the defender at a tick <= 3."""
    return captured(cell, defender_package) and int(cell["ticks_run"]) <= FORCED_LINE_TICK


def h3(treatment_f1: Iterable[Cell], *, seed_count: int) -> dict[str, Any]:
    """E6-H3 over FL(a, d): each attacker-defender pair has 2 x seed_count F1 matches (64 in the matrix)."""
    names = member_of()
    by_pair: dict[tuple[str, ...], list[Cell]] = {}
    for cell in treatment_f1:
        by_pair.setdefault(tuple(sorted(names[p] for p in cell_seats(cell))), []).append(cell)
    fl: dict[str, dict[str, str | None]] = {}
    minima: dict[str, Fraction] = {}
    for attacker in ATTACKERS:
        values: dict[str, Fraction] = {}
        for defender in DEFENDERS:
            cells = by_pair.get(tuple(sorted((attacker, defender))), [])
            if len(cells) != 2 * seed_count:
                raise payoff.PayoffDataError(
                    f"E6-H3: {attacker} v {defender} has {len(cells)} F1 matches, not {2 * seed_count}")
            defender_package = family.package_id(defender)
            hits = sum(forced_line_capture(cell, defender_package) for cell in cells)
            values[defender] = Fraction(hits, len(cells))
        fl[attacker] = {defender: text(value) for defender, value in values.items()}
        minima[attacker] = min(values.values())
    if any(value >= NINE_TENTHS for value in minima.values()):
        status = SUPPORTED
    elif all(value <= ONE_TENTH for value in minima.values()):
        status = REFUTED
    else:
        status = NEITHER
    return {"status": status, "FL": fl, "min_over_defenders": {a: text(v) for a, v in minima.items()}}


# ---------------------------------------------------------------------------
# Pathology flags and kill criteria
# ---------------------------------------------------------------------------


def _share(cells: Sequence[Cell], predicate: Any) -> Fraction:
    if not cells:
        raise payoff.PayoffDataError("empty field")
    return Fraction(sum(1 for cell in cells if predicate(cell)), len(cells))


def seat_metric_units(condition: ConditionData) -> dict[str, dict[str, Any]]:
    """E4's seat metrics for every F1 pairing and F2 mirror (packages by name)."""
    f1 = make_field_run(condition.condition_id, "F1", condition.f1, {})
    f2 = make_field_run(condition.condition_id, "F2", condition.f2, {})
    units: dict[str, dict[str, Any]] = {}
    primaries = [family.package_id(member) for member in family.OPPONENTS]
    for index, first in enumerate(primaries):
        for second in primaries[index + 1:]:
            units[f"F1|{first}|{second}"] = pairing_seat_metrics(f1, first, second)
    for member in family.OPPONENTS:
        primary, twin = family.package_id(member), family.package_id(member, "twin")
        units[f"F2|{primary}|{twin}"] = mirror_seat_metrics(f2, primary, twin)
    return units


def _seat_neutral(metrics: Mapping[str, Any]) -> bool:
    return (parse_exact(metrics["exact"]["sdom"]) < NINE_TENTHS
            and abs(parse_exact(metrics["exact"]["gsb"])) <= ONE_TENTH)


def pathology(control: ConditionData, treatment: ConditionData) -> dict[str, Any]:
    c1, t1 = list(control.f1), list(treatment.f1)
    tick_limit_c = _share(c1, lambda cell: cell.get("termination_reason") == TICK_LIMIT_REASON)
    tick_limit_t = _share(t1, lambda cell: cell.get("termination_reason") == TICK_LIMIT_REASON)
    no_contact_c = _share(c1, lambda cell: not control.contact[cell_key(cell)])
    no_contact_t = _share(t1, lambda cell: not treatment.contact[cell_key(cell)])
    names = member_of()
    immune: list[str] = []
    for member in family.FIXED_MEMBERS:
        package = family.package_id(member)
        in_c = [cell for cell in c1 if package in cell_seats(cell)]
        in_t = [cell for cell in t1 if package in cell_seats(cell)]
        if any(captured(cell, package) for cell in in_c) and not any(captured(cell, package) for cell in in_t):
            immune.append(member)
    units_c, units_t = seat_metric_units(control), seat_metric_units(treatment)
    seat_artifacts = sorted(
        unit for unit in units_c
        if _seat_neutral(units_c[unit]) and not _seat_neutral(units_t[unit])
    )
    return {
        "PF-1": {"raised": tick_limit_t - tick_limit_c >= ONE_TENTH, "control": text(tick_limit_c),
                 "treatment": text(tick_limit_t)},
        "PF-2": {"raised": no_contact_t - no_contact_c >= ONE_TENTH, "control": text(no_contact_c),
                 "treatment": text(no_contact_t)},
        "PF-3": {"raised": bool(immune), "members": immune},
        "PF-4": {"raised": bool(seat_artifacts), "units": [
            "|".join([unit.split("|")[0], *(names[p] for p in unit.split("|")[1:])]) for unit in seat_artifacts]},
        "seat_metrics": {"control": units_c, "treatment": units_t},
    }


def kill_criteria(*, h1t: str, treatment: ConditionReading, pf: Mapping[str, Any], h3_status: str) -> dict[str, Any]:
    universal = treatment.point.universal
    kc1 = h1t == REFUTED
    search_of = {member: str(values["search"]) for member, values in family.MEMBERS.items()}
    greed_universal = "GREED" in universal
    kc2 = greed_universal and treatment.stab["universal:GREED"] >= NINE_TENTHS
    return {
        "KC-1": {"fires": kc1, "label": kc1_label(universal, search_of) if kc1 else None},
        "KC-2": {"fires": kc2, "greed_universal": greed_universal,
                 "stab": text(treatment.stab["universal:GREED"])},
        "KC-3": {"fires": pf["PF-1"]["raised"] or pf["PF-2"]["raised"]},
        "KC-4": {"fires": h3_status == SUPPORTED},
        "KC-5": {"fires": pf["PF-4"]["raised"]},
    }


def fired(kills: Mapping[str, Mapping[str, Any]]) -> list[str]:
    return [name for name, kill in kills.items() if kill["fires"]]


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------


def payoff_tables(reading: ConditionReading) -> dict[str, Any]:
    """PR Sec 6.4: u with n_distinct, BR sets, universal members and Deltas, each with its stability."""
    members = family.OPPONENTS
    u = reading.point.u
    return {
        "u": {i: {j: {"u": text(u[(i, j)]), "n_distinct": payoff.n_distinct(reading.table, i, j)}
                  for j in members} for i in members},
        "br": {j: {"members": sorted(reading.point.br[j]),
                   "stab": {i: text(reading.stab[f"br:{i}:{j}"]) for i in family.FIXED_MEMBERS}}
               for j in members},
        "universal": sorted(reading.point.universal),
        "universal_stab": {i: text(reading.stab[f"universal:{i}"]) for i in family.FIXED_MEMBERS},
        "delta": {f"{lo}-{hi}": {j: {"delta": text(reading.point.delta[(lo, hi, j)]),
                                     "stab_ge_eps": text(reading.stab[f"delta_win:{lo}:{hi}:{j}"]),
                                     "stab_le_0": text(reading.stab[f"delta_never:{lo}:{hi}:{j}"])}
                                 for j in members}
                  for lo, hi in payoff.LOWER_INFORMATION},
        "P_none": reading.point.p_none, "stab_P_none": text(reading.stab["P_none"]),
        "P_win": reading.point.p_win, "stab_P_win": text(reading.stab["P_win"]),
        "P_never": reading.point.p_never, "stab_P_never": text(reading.stab["P_never"]),
    }


def adapt_reading(reading: ConditionReading) -> dict[str, Any]:
    """PR Sec 6.7 (secondary; never an input to a row or a kill)."""
    u = reading.point.u
    return {j: {"u_adapt_minus_u_j": text(u[("ADAPT", j)] - u[(j, "ADAPT")]),
                "adapt_in_br": "ADAPT" in reading.adapt_br[j]}
            for j in family.FIXED_MEMBERS}


def analyze_arm(control: ConditionData, treatment: ConditionData, *, seeds: Sequence[int],
                draws: Sequence[Sequence[int]] | None = None) -> dict[str, Any]:
    """Every registered quantity of one arm (PR Sec 5-6), without E6-D."""
    read_t = read_condition(treatment.f1, seeds=seeds, draws=draws)
    read_c = read_condition(control.f1, seeds=seeds, draws=draws)
    h1t, h1c, h2t = h1(read_t), h1(read_c), h2(read_t)
    h0_result = h0(control.f1, treatment.f1)
    h3_result = h3(treatment.f1, seed_count=len(seeds))
    pf = pathology(control, treatment)
    kills = kill_criteria(h1t=h1t, treatment=read_t, pf=pf, h3_status=h3_result["status"])
    return {
        "analysis_version": E6_ANALYSIS_VERSION,
        "control": control.condition_id,
        "treatment": treatment.condition_id,
        "hypotheses": {"E6-H1T": h1t, "E6-H1C": h1c, "E6-H2": h2t, "E6-H0": h0_result["status"],
                       "E6-H3": h3_result["status"]},
        "E6-H0": h0_result,
        "E6-H3": h3_result,
        "pathology": {name: value for name, value in pf.items() if name != "seat_metrics"},
        "seat_metrics": pf["seat_metrics"],
        "kill_criteria": kills,
        "fired": fired(kills),
        "payoff": {"treatment": payoff_tables(read_t), "control": payoff_tables(read_c)},
        # PR Sec 4.7, descriptive: the share of F1 matches decided by capture.
        "decided_by_capture": {"control": text(_share(list(control.f1), is_capture)),
                               "treatment": text(_share(list(treatment.f1), is_capture))},
        "adapt": {"treatment": adapt_reading(read_t), "control": adapt_reading(read_c)},
    }


def companion_reading(primary: Mapping[str, Any], companion: Mapping[str, Any]) -> dict[str, Any]:
    """PR Sec 6.8: agrees with the primary, or the list of what differs. Never a verdict."""
    differences: list[str] = []
    for name in ("E6-H1T", "E6-H2", "E6-H3"):
        if primary["hypotheses"][name] != companion["hypotheses"][name]:
            differences.append(f"{name}: {primary['hypotheses'][name]} (primary) vs "
                               f"{companion['hypotheses'][name]} (companion)")
    for name in primary["kill_criteria"]:
        first, second = primary["kill_criteria"][name]["fires"], companion["kill_criteria"][name]["fires"]
        if first != second:
            differences.append(f"{name}: {'fires' if first else 'does not fire'} (primary) vs "
                               f"{'fires' if second else 'does not fire'} (companion)")
    return {"reading": "agrees with the primary" if not differences else "differs", "differences": differences}


def control_against_control(result: Mapping[str, Any]) -> dict[str, Any]:
    """PR Sec 10.3 with a control in the treatment slot: H0 SUPPORTED with A = B = 1, H2
    REFUTED, no PF raised, and E6-H1T equal to E6-H1C."""
    checks = {
        "E6-H0 SUPPORTED": result["hypotheses"]["E6-H0"] == SUPPORTED,
        "A = 1": result["E6-H0"]["A"] == "1/1",
        "B = 1": result["E6-H0"]["B"] == "1/1",
        "E6-H2 REFUTED": result["hypotheses"]["E6-H2"] == REFUTED,
        "no PF raised": not any(flag["raised"] for flag in result["pathology"].values()),
        "E6-H1T = E6-H1C": result["hypotheses"]["E6-H1T"] == result["hypotheses"]["E6-H1C"],
    }
    return {"checks": checks, "status": "PASS" if all(checks.values()) else "FAIL"}
