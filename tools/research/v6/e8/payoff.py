"""E8 payoffs, best responses, universality and contrasts (PR8 Sec 4 and 5.3; phase I8-5).

docs/research/v6/V6_E8_ACTIVE_SPATIAL_SENSING_PREREGISTRATION.md (PR8) Sec 4
reuses PR6 Sec 4 unchanged, with E8's sets. The PR6 functions are E6's
``tools/research/v6/e6/payoff.py``, imported unchanged, each given E8's
members, sets and epsilon explicitly (none of E6's member-named defaults is
used):

* **O-VALUE and O-PAYOFF** (``value_table``, ``per_seed_table``,
  ``payoffs``): a match is worth 1, 1/2 or 0 to Seat A; ``p_s(i, j)`` is i's
  mean over the two F1 orientations at seed s; ``u(i, j)`` the mean over the
  seeds; ``u(i, i) = 1/2``.
* **O-BR** (``best_responses``, ``universal``): BR_eps(j) over Pi_F, and
  universality over every j in Pi; P_none.

E8 adds, from the registered definitions (PR8 Sec 5.3):

* **BR^A_eps(j)** over A8 and its universal members; **Q_none**;
* **L8** = {(LURK8, RUSH8), (PACED8, RUSH8)}, Delta_j(lo, hi), P_win and
  P_never, exactly as PR6 Sec 4.6;
* **Delta^R_Y** = u(REACQ8, Y) - u(RUSH8, Y), reported for every Y in Pi and
  evaluated over the census;
* **U(i)**, the mean over j in Pi of u(i, j).

Every value is exact (``Fraction``). The registered sets, epsilon and the
O-BOOT draws come from the frozen transcription (``decision``), never from
this file.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from fractions import Fraction
from typing import Any

from tools.research.v6.e6 import payoff as pr6
from tools.research.v6.e8 import decision

EPSILON: Fraction = decision.EPSILON
L8: tuple[tuple[str, str], ...] = tuple(
    (lo, hi) for lo, hi in decision.REGISTRATION["definitions"]["L8"]["pairs"])
REPEAT, ONCE = (decision.REGISTRATION["census"]["contrast"][key] for key in ("repeat", "once"))
ADAPT = "ADAPT8"
GREED = "GREED8"

ValueTable = pr6.ValueTable
PayoffDataError = pr6.PayoffDataError
value_table = pr6.value_table
per_seed_table = pr6.per_seed_table
n_distinct = pr6.n_distinct


@dataclass(frozen=True)
class Reading:
    """Every registered payoff quantity at one set of seed positions."""

    u: Mapping[tuple[str, str], Fraction]
    br: Mapping[str, frozenset[str]]
    universal: frozenset[str]
    br_a: Mapping[str, frozenset[str]]
    universal_a8: frozenset[str]
    delta: Mapping[tuple[str, str, str], Fraction]
    delta_r: Mapping[str, Fraction]
    mixed: Mapping[str, Fraction]

    @property
    def p_none(self) -> bool:
        return not self.universal

    @property
    def q_none(self) -> bool:
        return not self.universal_a8

    @property
    def p_win(self) -> bool:
        return pr6.p_win(self.delta, EPSILON)

    @property
    def p_never(self) -> bool:
        return pr6.p_never(self.delta)

    def repeat_for(self, census: Sequence[str]) -> bool:
        """H8-REPEAT's supporting predicate: some Y in the census has Delta^R_Y >= eps."""
        return any(self.delta_r[y] >= EPSILON for y in census)

    def repeat_against(self, census: Sequence[str]) -> bool:
        """H8-REPEAT's refuting predicate: every Y in the census has Delta^R_Y <= 0."""
        return all(self.delta_r[y] <= 0 for y in census)

    @property
    def best_fixed(self) -> Fraction:
        return max(self.mixed[ONCE], self.mixed[REPEAT])

    @property
    def adapt_for(self) -> bool:
        """H8-ADAPT's supporting predicate: U(ADAPT8) >= max(U(RUSH8), U(REACQ8))."""
        return self.mixed[ADAPT] >= self.best_fixed

    @property
    def adapt_against(self) -> bool:
        """H8-ADAPT's refuting predicate: U(ADAPT8) <= max(U(RUSH8), U(REACQ8)) - eps."""
        return self.mixed[ADAPT] <= self.best_fixed - EPSILON


def reading(table: ValueTable, *, positions: Sequence[int] | None = None,
            seed_payoffs: pr6.PerSeed | None = None) -> Reading:
    u = pr6.payoffs(table, positions, seed_payoffs=seed_payoffs)
    br = pr6.best_responses(u, candidates=decision.PI_F, opponents=decision.PI, epsilon=EPSILON)
    br_a = pr6.best_responses(u, candidates=decision.A8, opponents=decision.PI, epsilon=EPSILON)
    return Reading(
        u=u,
        br=br,
        universal=pr6.universal(br, candidates=decision.PI_F),
        br_a=br_a,
        universal_a8=pr6.universal(br_a, candidates=decision.A8),
        delta=pr6.deltas(u, opponents=decision.PI, contrasts=L8),
        delta_r={y: u[(REPEAT, y)] - u[(ONCE, y)] for y in decision.PI},
        mixed={i: sum((u[(i, j)] for j in decision.PI), Fraction(0)) / len(decision.PI) for i in decision.PI},
    )


Predicate = Callable[[Reading], bool]


def stability_counts(table: ValueTable, predicates: Mapping[str, Predicate],
                     draws: Sequence[Sequence[int]] = decision.DRAWS) -> dict[str, int]:
    """For each named predicate, the number of the 1,000 registered draws in which it holds."""
    if len(draws) != decision.RESAMPLES:
        raise ValueError(f"{len(draws)} draws, not the registered {decision.RESAMPLES}")
    seed_payoffs = per_seed_table(table)
    counts = dict.fromkeys(predicates, 0)
    for positions in draws:
        sample = reading(table, positions=positions, seed_payoffs=seed_payoffs)
        for name, predicate in predicates.items():
            counts[name] += bool(predicate(sample))
    return counts


def registered_predicates(census: Sequence[str]) -> dict[str, Predicate]:
    """Every predicate whose stability a registered status or report needs (PR8 Sec 5.3, 6.4, 8)."""
    out: dict[str, Predicate] = {
        "P_none": lambda r: r.p_none,
        "Q_none": lambda r: r.q_none,
        "P_win": lambda r: r.p_win,
        "P_never": lambda r: r.p_never,
        "adapt_for": lambda r: r.adapt_for,
        "adapt_against": lambda r: r.adapt_against,
        f"universal:{GREED}": lambda r: GREED in r.universal,
    }
    if census:
        out["repeat_for"] = lambda r: r.repeat_for(census)
        out["repeat_against"] = lambda r: r.repeat_against(census)
    for i in decision.PI_F:
        out[f"universal:{i}"] = lambda r, i=i: i in r.universal
        for j in decision.PI:
            out[f"br:{i}:{j}"] = lambda r, i=i, j=j: i in r.br[j]
    for i in decision.A8:
        out[f"universal_a8:{i}"] = lambda r, i=i: i in r.universal_a8
        for j in decision.PI:
            out[f"br_a:{i}:{j}"] = lambda r, i=i, j=j: i in r.br_a[j]
    for lo, hi in L8:
        for j in decision.PI:
            out[f"delta_win:{lo}:{hi}:{j}"] = lambda r, lo=lo, hi=hi, j=j: r.delta[(lo, hi, j)] >= EPSILON
            out[f"delta_never:{lo}:{hi}:{j}"] = lambda r, lo=lo, hi=hi, j=j: r.delta[(lo, hi, j)] <= 0
    for y in decision.PI:
        out[f"delta_r_ge_eps:{y}"] = lambda r, y=y: r.delta_r[y] >= EPSILON
        out[f"delta_r_le_0:{y}"] = lambda r, y=y: r.delta_r[y] <= 0
    return out


def text(value: Fraction | None) -> str | None:
    return None if value is None else f"{value.numerator}/{value.denominator}"


def tables(table: ValueTable, point: Reading, counts: Mapping[str, int]) -> dict[str, Any]:
    """PR8 Sec 6.4: u with n_distinct, every BR and BR^A set, the universal members, every Delta_j over
    L8, every Delta^R_Y and U(i), each with its stability (a count of the 1,000 draws)."""
    members = decision.PI
    return {
        "u": {i: {j: {"u": text(point.u[(i, j)]), "n_distinct": n_distinct(table, i, j)} for j in members}
              for i in members},
        "br": {j: {"members": sorted(point.br[j]), "stab": {i: counts[f"br:{i}:{j}"] for i in decision.PI_F}}
               for j in members},
        "br_a": {j: {"members": sorted(point.br_a[j]), "stab": {i: counts[f"br_a:{i}:{j}"] for i in decision.A8}}
                 for j in members},
        "universal": sorted(point.universal),
        "universal_stab": {i: counts[f"universal:{i}"] for i in decision.PI_F},
        "universal_a8": sorted(point.universal_a8),
        "universal_a8_stab": {i: counts[f"universal_a8:{i}"] for i in decision.A8},
        "delta": {f"{lo}-{hi}": {j: {"delta": text(point.delta[(lo, hi, j)]),
                                     "stab_ge_eps": counts[f"delta_win:{lo}:{hi}:{j}"],
                                     "stab_le_0": counts[f"delta_never:{lo}:{hi}:{j}"]} for j in members}
                  for lo, hi in L8},
        "delta_r": {y: {"delta_r": text(point.delta_r[y]), "stab_ge_eps": counts[f"delta_r_ge_eps:{y}"],
                        "stab_le_0": counts[f"delta_r_le_0:{y}"]} for y in members},
        "mixed": {i: text(point.mixed[i]) for i in members},
        "adapt": {"U_adapt": text(point.mixed[ADAPT]), "best_fixed": text(point.best_fixed),
                  "for": point.adapt_for, "stab_for": counts["adapt_for"],
                  "against": point.adapt_against, "stab_against": counts["adapt_against"]},
        "P_none": point.p_none, "stab_P_none": counts["P_none"],
        "Q_none": point.q_none, "stab_Q_none": counts["Q_none"],
        "P_win": point.p_win, "stab_P_win": counts["P_win"],
        "P_never": point.p_never, "stab_P_never": counts["P_never"],
        "resamples": decision.RESAMPLES,
    }


def member_table(cells: Iterable[Mapping[str, Any]], *, member_of: Mapping[str, str],
                 seeds: Sequence[int]) -> ValueTable:
    """The F1 value table over E8's members, in registered order."""
    return value_table(cells, member_of=member_of, members=decision.MEMBERS, seeds=seeds)
