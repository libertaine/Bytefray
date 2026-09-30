"""PA-2: E4's seat metrics over a seed multiset, and their identity with the frozen values.

The frozen ``analyze_e4.pairing_seat_metrics`` and ``mirror_seat_metrics``
key cells by unique seed, so they cannot take a resampled multiset. These
functions compute the same GSB and SDom from per-seed seat results with
multiplicity, by the same definitions:

* **pairing** {X, Y}: per seed, the seat results of X-in-Seat-A and of
  Y-in-Seat-A. GSB = (Seat A wins - Seat B wins) / (2 s). SDI is the share of
  seeds whose two orientations are won by the same seat; among those, p_A is
  the share won by Seat A, SB = |2 p_A - 1|, and SDom = SDI x SB (0 if no such
  seed).
* **mirror**: per seed, the candidate-first cell's seat result.
  GSB = (A - B) / s; SDom = (decisive share) x |2 p_A - 1| over decisive seeds.

Neutral means SDom < 9/10 and |GSB| <= 1/10 (E6 PR Sec 6.1, PF-4).
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from fractions import Fraction
from typing import Any

from tools.research.v6 import experiment_harness as harness
from tools.research.v6.e6 import family

SEAT_A, SEAT_B = harness.SEAT_A, harness.SEAT_B
NINE_TENTHS = Fraction(9, 10)
ONE_TENTH = Fraction(1, 10)

PairingResults = Sequence[tuple[str, str]]
MirrorResults = Sequence[str]


def pairing_metrics(results: PairingResults) -> tuple[Fraction, Fraction]:
    """(GSB, SDom) of a pairing from per-seed (X-in-A result, Y-in-A result)."""

    s = len(results)
    if s == 0:
        raise ValueError("a pairing needs at least one seed")
    a = sum((first == SEAT_A) + (second == SEAT_A) for first, second in results)
    b = sum((first == SEAT_B) + (second == SEAT_B) for first, second in results)
    consistent = [first for first, second in results if first == second and first in (SEAT_A, SEAT_B)]
    if consistent:
        p_a = Fraction(sum(result == SEAT_A for result in consistent), len(consistent))
        sdom = Fraction(len(consistent), s) * abs(2 * p_a - 1)
    else:
        sdom = Fraction(0)
    return Fraction(a - b, 2 * s), sdom


def mirror_metrics(results: MirrorResults) -> tuple[Fraction, Fraction]:
    """(GSB, SDom) of a twin mirror from per-seed candidate-first seat results."""

    s = len(results)
    if s == 0:
        raise ValueError("a mirror needs at least one seed")
    a = sum(result == SEAT_A for result in results)
    b = sum(result == SEAT_B for result in results)
    decisive = a + b
    sdom = Fraction(0) if decisive == 0 else Fraction(decisive, s) * abs(2 * Fraction(a, decisive) - 1)
    return Fraction(a - b, s), sdom


def decisive_share_pairing(results: PairingResults) -> Fraction:
    return Fraction(sum((first in (SEAT_A, SEAT_B)) + (second in (SEAT_A, SEAT_B)) for first, second in results),
                    2 * len(results))


def decisive_share_mirror(results: MirrorResults) -> Fraction:
    return Fraction(sum(result in (SEAT_A, SEAT_B) for result in results), len(results))


def neutral(gsb: Fraction, sdom: Fraction) -> bool:
    return sdom < NINE_TENTHS and abs(gsb) <= ONE_TENTH


# ---------------------------------------------------------------------------
# The 45 frozen units, in the frozen analysis's own key format
# ---------------------------------------------------------------------------


def unit_keys() -> list[str]:
    """``F1|<pid>|<pid>`` for the 36 pairings, then ``F2|<primary>|<twin>`` for the 9 mirrors
    (``analyze_e6.seat_metric_units``)."""

    primaries = [family.package_id(member) for member in family.OPPONENTS]
    keys = [f"F1|{first}|{second}" for index, first in enumerate(primaries) for second in primaries[index + 1:]]
    keys += [f"F2|{family.package_id(member)}|{family.package_id(member, 'twin')}" for member in family.OPPONENTS]
    return keys


def members_of(unit: str) -> tuple[str, str]:
    _field, first, second = unit.split("|")
    return family.PACKAGES[first][0], family.PACKAGES[second][0]


def label(unit: str) -> str:
    """``F1|PACED|ADAPT`` style, as E6-R names units."""

    field_id = unit.split("|")[0]
    first, second = members_of(unit)
    return f"{field_id}|{first}|{second}"


def contains_adapt(unit: str) -> bool:
    return "ADAPT" in members_of(unit)


def per_seed_results(cells: Mapping[str, Sequence[Mapping[str, Any]]], seeds: Sequence[int]) -> dict[str, list[Any]]:
    """Each unit's per-seed seat results, in the order of ``seeds`` (the revealed list)."""

    f1: dict[tuple[str, str, int], str] = {}
    for cell in cells["F1"]:
        seat_a, seat_b = harness.cell_seats(cell)
        f1[(seat_a, seat_b, int(cell["seed"]))] = harness.cell_seat_result(cell)
    f2: dict[tuple[str, str, int], str] = {}
    for cell in cells["F2"]:
        if cell.get("orientation") == harness.ORIENTATION_CANDIDATE_FIRST:
            f2[(str(cell["subject_id"]), str(cell["opponent_id"]), int(cell["seed"]))] = harness.cell_seat_result(cell)
    out: dict[str, list[Any]] = {}
    for unit in unit_keys():
        field_id, first, second = unit.split("|")
        if field_id == "F1":
            out[unit] = [(f1[(first, second, seed)], f1[(second, first, seed)]) for seed in seeds]
        else:
            out[unit] = [f2[(first, second, seed)] for seed in seeds]
    return out


def metrics(unit: str, results: Sequence[Any], positions: Iterable[int] | None = None) -> tuple[Fraction, Fraction]:
    """(GSB, SDom) of ``unit`` over the seed positions given (all, in order, by default)."""

    chosen = list(results) if positions is None else [results[p] for p in positions]
    return pairing_metrics(chosen) if unit.startswith("F1|") else mirror_metrics(chosen)


def decisive_share(unit: str, results: Sequence[Any]) -> Fraction:
    return decisive_share_pairing(results) if unit.startswith("F1|") else decisive_share_mirror(results)


def identity_check(results: Mapping[str, Mapping[str, Sequence[Any]]], frozen: Mapping[str, Any]) -> dict[str, Any]:
    """PA-2: every (unit, condition) GSB and SDom against ``e6_analysis.json``."""

    arms = {"C-E6": ("primary", "control"), "T-E6": ("primary", "treatment"),
            "C-E6L": ("companion", "control"), "T-E6L": ("companion", "treatment")}
    mismatches: list[dict[str, str]] = []
    compared = 0
    for condition, (arm, slot) in arms.items():
        frozen_units = frozen["arms"][arm]["seat_metrics"][slot]
        if set(frozen_units) != set(unit_keys()):
            raise ValueError(f"{condition}: the frozen unit set differs from the 45 frozen units")
        for unit in unit_keys():
            gsb, sdom = metrics(unit, results[condition][unit])
            pinned = frozen_units[unit]["exact"]
            compared += 1
            if gsb != Fraction(pinned["gsb"]) or sdom != Fraction(pinned["sdom"]):
                mismatches.append({"condition": condition, "unit": label(unit),
                                   "gsb": f"{gsb}", "sdom": f"{sdom}",
                                   "frozen_gsb": pinned["gsb"], "frozen_sdom": pinned["sdom"]})
    return {"compared": compared, "mismatches": mismatches, "status": "PASS" if not mismatches and compared == 180 else "FAIL"}
