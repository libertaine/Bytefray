"""PA-4 to PA-6: the interaction estimands, their O-BOOT stabilities, and the fixed strata.

Notation (design review Sec 6.1). For unit u, G_u(s, d) is its GSB under
sensing s (0 none, 1 radius 32) and disruption d (0 whole tick, 1 lambda 1).

* Delta_u(d) = |G_u(1, d)| - |G_u(0, d)|  (the sensing effect under d)
* I_u = Delta_u(0) - Delta_u(1)            (the unit interaction)
* I_all = the mean of I_u over all 45 frozen units (primary description)
* I_common_neutral = the mean over U*, the units neutral under both controls
* L(d) = the share of U* non-neutral under treatment (1, d); I_flag = L(0) - L(1)

Every value is exact (``Fraction``). Stabilities use the registered O-BOOT
draws (``payoff.resample_positions``: ``random.Random(42)``, 1000 x 32
positions), applied jointly to every unit and every condition. They are
reported against the 9/10 decision convention, never as a verdict.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from fractions import Fraction
from typing import Any

from tools.research.v6.e6 import payoff
from tools.research.v6.e6_audit import seat
from tools.research.v6.e6_audit.corpus import CONDITIONS

CONVENTION = Fraction(9, 10)
PRIMARY_ARM = ("C-E6", "T-E6")
COMPANION_ARM = ("C-E6L", "T-E6L")
CONTROLS = ("C-E6", "C-E6L")

Results = Mapping[str, Mapping[str, Sequence[Any]]]  # condition -> unit -> per-seed results
Values = dict[str, dict[str, tuple[Fraction, Fraction]]]  # condition -> unit -> (GSB, SDom)


def text(value: Fraction | None) -> str | None:
    return None if value is None else f"{value.numerator}/{value.denominator}"


def values_at(results: Results, positions: Sequence[int] | None = None) -> Values:
    return {condition: {unit: seat.metrics(unit, results[condition][unit], positions) for unit in seat.unit_keys()}
            for condition in CONDITIONS}


def unit_interaction(values: Values, unit: str) -> Fraction:
    g = {condition: values[condition][unit][0] for condition in CONDITIONS}
    return (abs(g["T-E6"]) - abs(g["C-E6"])) - (abs(g["T-E6L"]) - abs(g["C-E6L"]))


def signed_interaction(values: Values, unit: str) -> Fraction:
    g = {condition: values[condition][unit][0] for condition in CONDITIONS}
    return (g["T-E6"] - g["C-E6"]) - (g["T-E6L"] - g["C-E6L"])


def is_neutral(values: Values, condition: str, unit: str) -> bool:
    return seat.neutral(*values[condition][unit])


# ---------------------------------------------------------------------------
# The fixed sets, from the controls alone
# ---------------------------------------------------------------------------


def baseline_strata(values: Values) -> dict[str, list[str]]:
    """Design review Sec 6.1: each unit's stratum by its neutrality under the two controls only."""

    strata: dict[str, list[str]] = {"neutral_both": [], "neutral_one": [], "neutral_neither": []}
    for unit in seat.unit_keys():
        count = sum(is_neutral(values, control, unit) for control in CONTROLS)
        strata[{2: "neutral_both", 1: "neutral_one", 0: "neutral_neither"}[count]].append(unit)
    return strata


def unit_sets(point: Values) -> dict[str, list[str]]:
    """Every unit set an estimand is taken over, fixed from the identity (point) controls and the
    unit names, before any treatment value enters (PA-6)."""

    strata = baseline_strata(point)
    everything = seat.unit_keys()
    common = strata["neutral_both"]
    return {
        "all": everything,
        "common_neutral": common,
        "all_adapt": [u for u in everything if seat.contains_adapt(u)],
        "all_non_adapt": [u for u in everything if not seat.contains_adapt(u)],
        "all_pairings": [u for u in everything if u.startswith("F1|")],
        "all_mirrors": [u for u in everything if u.startswith("F2|")],
        "common_neutral_adapt": [u for u in common if seat.contains_adapt(u)],
        "common_neutral_non_adapt": [u for u in common if not seat.contains_adapt(u)],
        "stratum_neutral_both": strata["neutral_both"],
        "stratum_neutral_one": strata["neutral_one"],
        "stratum_neutral_neither": strata["neutral_neither"],
    }


def mean_interaction(values: Values, units: Sequence[str]) -> Fraction:
    if not units:
        raise ValueError("an interaction mean needs at least one unit")
    return sum((unit_interaction(values, unit) for unit in units), Fraction(0)) / len(units)


def flag_form(values: Values, common: Sequence[str]) -> tuple[Fraction, Fraction, Fraction]:
    """(L(0), L(1), I_flag) over the common-neutral set."""

    n = len(common)
    l0 = Fraction(sum(not is_neutral(values, "T-E6", unit) for unit in common), n)
    l1 = Fraction(sum(not is_neutral(values, "T-E6L", unit) for unit in common), n)
    return l0, l1, l0 - l1


def pf4_units(values: Values, arm: tuple[str, str], units: Sequence[str] | None = None) -> list[str]:
    """E6 PF-4 for one arm: units neutral under its control and not under its treatment
    (over ``units``, all 45 by default)."""

    control, treatment = arm
    return [unit for unit in (seat.unit_keys() if units is None else units)
            if is_neutral(values, control, unit) and not is_neutral(values, treatment, unit)]


def reading(values: Values, sets: Mapping[str, Sequence[str]]) -> dict[str, Any]:
    """Every estimand at one set of values (the point estimate, or one resample)."""

    l0, l1, i_flag = flag_form(values, sets["common_neutral"])
    means = {name: mean_interaction(values, units) for name, units in sets.items() if units}
    return {
        "I_all": means["all"],
        "I_common_neutral": means["common_neutral"],
        "means": means,
        "L0": l0, "L1": l1, "I_flag": i_flag,
        "pf4_primary": pf4_units(values, PRIMARY_ARM),
        "pf4_companion": pf4_units(values, COMPANION_ARM),
        "pf4_primary_non_adapt": pf4_units(values, PRIMARY_ARM, sets["all_non_adapt"]),
        "pf4_companion_non_adapt": pf4_units(values, COMPANION_ARM, sets["all_non_adapt"]),
    }


def _joint_key(primary: bool, companion: bool) -> str:
    return f"primary={'raised' if primary else 'not'},companion={'raised' if companion else 'not'}"


# ---------------------------------------------------------------------------
# Stabilities over the registered O-BOOT draws
# ---------------------------------------------------------------------------


def draws(seed_count: int) -> list[tuple[int, ...]]:
    return payoff.resample_positions(seed_count)


def _share(count: int, total: int) -> Fraction:
    return Fraction(count, total)


def bootstrap(results: Results, sets: Mapping[str, Sequence[str]], positions_list: Sequence[Sequence[int]],
              *, tracked: Sequence[str]) -> dict[str, Any]:
    """Stabilities of each estimand, PF-4 per arm and jointly, per-unit crossings, and the
    resampled distribution of each tracked unit's signed interaction and treatment GSB."""

    total = len(positions_list)
    positive: Counter[str] = Counter()
    raised = Counter[str]()
    joint = Counter[str]()
    joint_non_adapt = Counter[str]()
    crossings = {"primary": Counter[str](), "companion": Counter[str]()}
    unit_signed: dict[str, list[Fraction]] = {unit: [] for unit in tracked}
    unit_exceeds = {unit: Counter[str]() for unit in tracked}
    for positions in positions_list:
        values = values_at(results, positions)
        r = reading(values, sets)
        for name, value in r["means"].items():
            positive[f"{name}>0"] += value > 0
        positive["I_flag>0"] += r["I_flag"] > 0
        primary, companion = bool(r["pf4_primary"]), bool(r["pf4_companion"])
        raised["primary"] += primary
        raised["companion"] += companion
        joint[_joint_key(primary, companion)] += 1
        primary_na, companion_na = bool(r["pf4_primary_non_adapt"]), bool(r["pf4_companion_non_adapt"])
        raised["primary_non_adapt"] += primary_na
        raised["companion_non_adapt"] += companion_na
        joint_non_adapt[_joint_key(primary_na, companion_na)] += 1
        for unit in r["pf4_primary"]:
            crossings["primary"][seat.label(unit)] += 1
        for unit in r["pf4_companion"]:
            crossings["companion"][seat.label(unit)] += 1
        for unit in tracked:
            unit_signed[unit].append(signed_interaction(values, unit))
            for condition in ("T-E6", "T-E6L"):
                unit_exceeds[unit][condition] += abs(values[condition][unit][0]) > seat.ONE_TENTH
    quantile: Callable[[list[Fraction], float], Fraction] = lambda xs, q: sorted(xs)[int(q * (len(xs) - 1) + 0.5)]
    return {
        "resamples": total,
        "positive": {name: text(_share(count, total)) for name, count in sorted(positive.items())},
        "pf4_raised": {arm: text(_share(count, total)) for arm, count in sorted(raised.items())},
        "pf4_joint": {pattern: count for pattern, count in sorted(joint.items())},
        "pf4_joint_non_adapt": {pattern: count for pattern, count in sorted(joint_non_adapt.items())},
        "pf4_crossings": {arm: dict(sorted(counter.items(), key=lambda item: (-item[1], item[0])))
                          for arm, counter in crossings.items()},
        "tracked_units": {
            seat.label(unit): {
                "signed_interaction_quantiles": {q: text(quantile(unit_signed[unit], float(q)))
                                                 for q in ("0.025", "0.5", "0.975")},
                "signed_interaction_positive": text(_share(sum(v > 0 for v in unit_signed[unit]), total)),
                "abs_gsb_above_one_tenth": {c: text(_share(n, total)) for c, n in sorted(unit_exceeds[unit].items())},
            }
            for unit in tracked
        },
    }


def meets_convention(share_text: str | None) -> bool:
    """Whether a stability reaches the 9/10 research-program decision convention (never a verdict)."""

    return share_text is not None and Fraction(share_text) >= CONVENTION
