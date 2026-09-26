"""E6 payoffs, best responses, universality, contrasts and the bootstrap.

docs/research/v6/V6_E6_PRICED_SENSING_PREREGISTRATION.md Sec 4.1-4.6, exactly:

* **O-VALUE.** A match is worth 1 to the winning seat, 0 to the losing seat,
  and 1/2 to each in a tie (a tick-limit tie or mutual elimination), read
  from the harness's ``cell_seat_result``. A cell with no outcome ("other")
  is an integrity failure, never a value.
* **O-PAYOFF.** ``p_s(i, j)`` is the mean of i's value over the two F1
  orientations at seed s; ``u(i, j)`` is the mean of ``p_s`` over the seeds;
  ``u(i, i) = 1/2`` by definition.
* **O-BR.** ``BR_eps(j) = {i in Pi_F : u(i, j) >= max_k u(k, j) - eps}``,
  ``eps = 1/16``, the comparison closed. ``i`` is universal iff it is in
  every ``BR_eps(j)``, ``j`` in Pi. ``P_none``: no member of Pi_F is universal.
* **O-CONTRAST.** ``Delta_j(lo, hi) = u(lo, j) - u(hi, j)`` over
  ``L = {(LURK, RUSH), (PACED, RUSH)}``. ``P_win``: some ``Delta_j >= eps``.
  ``P_never``: every ``Delta_j <= 0``.
* **O-BOOT.** 1000 resamples; each is 32 draws with replacement from the
  ordered seed list (``rng.randrange(32)``, positions, ``random.Random(42)``,
  E2's draw form), applied jointly to every cell. ``stab(P)`` is the
  fraction of resamples in which P holds.

All arithmetic is exact (``Fraction``). Package IDs are mapped to members by
the caller; this module sees member names only.
"""

from __future__ import annotations

import random
from collections.abc import Callable, Hashable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from fractions import Fraction
from typing import Any

from tools.research.v6.experiment_harness import (
    SEAT_A,
    SEAT_B,
    TIE,
    cell_seat_result,
    cell_seats,
    trajectory_key,
)

EPSILON = Fraction(1, 16)
BOOTSTRAP_RESAMPLES = 1000
BOOTSTRAP_SEED = 42
STABILITY_MIN = Fraction(9, 10)
HALF = Fraction(1, 2)
LOWER_INFORMATION: tuple[tuple[str, str], ...] = (("LURK", "RUSH"), ("PACED", "RUSH"))


class PayoffDataError(ValueError):
    """The cells do not form a complete, well-defined F1 value table."""


def seat_a_value(cell: Mapping[str, Any]) -> Fraction:
    """O-VALUE for the entrant in Seat A."""

    result = cell_seat_result(cell)
    if result == SEAT_A:
        return Fraction(1)
    if result == SEAT_B:
        return Fraction(0)
    if result == TIE:
        return HALF
    raise PayoffDataError(f"cell {cell.get('schedule_id')} has no match outcome ({result!r})")


@dataclass(frozen=True)
class ValueTable:
    """One condition's F1: Seat A's value in every (A, B, seed position) match.

    ``values[(a, b)][k]`` is the value of member ``a`` in Seat A against
    member ``b`` in Seat B at the k-th seed of ``seeds``;
    ``trajectories[(a, b)][k]`` is that match's harness ``trajectory_key``.
    """

    members: tuple[str, ...]
    seeds: tuple[int, ...]
    values: Mapping[tuple[str, str], tuple[Fraction, ...]]
    trajectories: Mapping[tuple[str, str], tuple[Hashable, ...]]


def value_table(cells: Iterable[Mapping[str, Any]], *, member_of: Mapping[str, str],
                members: Sequence[str], seeds: Sequence[int]) -> ValueTable:
    """Build and completeness-check the F1 value table from harness cells."""

    position = {seed: index for index, seed in enumerate(seeds)}
    if len(position) != len(seeds):
        raise PayoffDataError("repeated seed in the ordered seed list")
    slots: dict[tuple[str, str], list[Any]] = {}
    paths: dict[tuple[str, str], list[Any]] = {}
    for cell in cells:
        package_a, package_b = cell_seats(cell)
        pair = (member_of[package_a], member_of[package_b])
        if pair[0] == pair[1]:
            raise PayoffDataError(f"F1 holds a mirror cell {cell.get('schedule_id')}")
        seed = int(cell["seed"])
        if seed not in position:
            raise PayoffDataError(f"cell seed {seed} is not in the ordered seed list")
        row = slots.setdefault(pair, [None] * len(seeds))
        path = paths.setdefault(pair, [None] * len(seeds))
        if row[position[seed]] is not None:
            raise PayoffDataError(f"duplicate F1 cell {pair} at seed {seed}")
        row[position[seed]] = seat_a_value(cell)
        path[position[seed]] = trajectory_key(cell)
    expected = {(a, b) for a in members for b in members if a != b}
    if set(slots) != expected:
        raise PayoffDataError(f"F1 ordered pairs differ from the members: missing {sorted(expected - set(slots))}, "
                              f"extra {sorted(set(slots) - expected)}")
    for pair, row in slots.items():
        if any(value is None for value in row):
            raise PayoffDataError(f"F1 pair {pair} lacks a seed")
    return ValueTable(tuple(members), tuple(seeds), {k: tuple(v) for k, v in slots.items()},
                      {k: tuple(v) for k, v in paths.items()})


def per_seed(table: ValueTable, i: str, j: str, k: int) -> Fraction:
    """p_s(i, j) at seed position k: i's mean value over the two orientations."""
    return (table.values[(i, j)][k] + (1 - table.values[(j, i)][k])) / 2


PerSeed = Mapping[tuple[str, str], tuple[Fraction, ...]]


def per_seed_table(table: ValueTable) -> dict[tuple[str, str], tuple[Fraction, ...]]:
    """p_s(i, j) for every ordered pair of distinct members and every seed position."""
    return {
        (i, j): tuple(per_seed(table, i, j, k) for k in range(len(table.seeds)))
        for i in table.members for j in table.members if i != j
    }


def payoffs(table: ValueTable, positions: Sequence[int] | None = None, *,
            seed_payoffs: PerSeed | None = None) -> dict[tuple[str, str], Fraction]:
    """u(i, j) for every ordered pair of members, over ``positions`` (all seeds by default)."""

    p = seed_payoffs if seed_payoffs is not None else per_seed_table(table)
    drawn = range(len(table.seeds)) if positions is None else positions
    count = len(drawn)
    u: dict[tuple[str, str], Fraction] = {}
    for i in table.members:
        for j in table.members:
            u[(i, j)] = HALF if i == j else sum((p[(i, j)][k] for k in drawn), Fraction(0)) / count
    return u


def best_responses(u: Mapping[tuple[str, str], Fraction], *, candidates: Sequence[str],
                   opponents: Sequence[str], epsilon: Fraction = EPSILON) -> dict[str, frozenset[str]]:
    out: dict[str, frozenset[str]] = {}
    for j in opponents:
        best = max(u[(k, j)] for k in candidates)
        out[j] = frozenset(i for i in candidates if u[(i, j)] >= best - epsilon)
    return out


def universal(br: Mapping[str, frozenset[str]], *, candidates: Sequence[str]) -> frozenset[str]:
    return frozenset(i for i in candidates if all(i in members for members in br.values()))


def deltas(u: Mapping[tuple[str, str], Fraction], *, opponents: Sequence[str],
           contrasts: Sequence[tuple[str, str]] = LOWER_INFORMATION) -> dict[tuple[str, str, str], Fraction]:
    return {(lo, hi, j): u[(lo, j)] - u[(hi, j)] for lo, hi in contrasts for j in opponents}


def p_win(delta: Mapping[Any, Fraction], epsilon: Fraction = EPSILON) -> bool:
    return any(value >= epsilon for value in delta.values())


def p_never(delta: Mapping[Any, Fraction]) -> bool:
    return all(value <= 0 for value in delta.values())


def resample_positions(seed_count: int, *, resamples: int = BOOTSTRAP_RESAMPLES,
                       seed: int = BOOTSTRAP_SEED) -> list[tuple[int, ...]]:
    """The O-BOOT draws: seed positions, jointly applied to every cell."""
    rng = random.Random(seed)
    return [tuple(rng.randrange(seed_count) for _ in range(seed_count)) for _ in range(resamples)]


@dataclass(frozen=True)
class Reading:
    """Every O-BR / O-CONTRAST quantity at one set of seed positions."""

    u: Mapping[tuple[str, str], Fraction]
    br: Mapping[str, frozenset[str]]
    universal: frozenset[str]
    delta: Mapping[tuple[str, str, str], Fraction]

    @property
    def p_none(self) -> bool:
        return not self.universal

    @property
    def p_win(self) -> bool:
        return p_win(self.delta)

    @property
    def p_never(self) -> bool:
        return p_never(self.delta)


def reading(table: ValueTable, *, candidates: Sequence[str], opponents: Sequence[str],
            positions: Sequence[int] | None = None, seed_payoffs: PerSeed | None = None) -> Reading:
    u = payoffs(table, positions, seed_payoffs=seed_payoffs)
    br = best_responses(u, candidates=candidates, opponents=opponents)
    return Reading(u=u, br=br, universal=universal(br, candidates=candidates),
                   delta=deltas(u, opponents=opponents))


Predicate = Callable[[Reading], bool]


def stabilities(table: ValueTable, predicates: Mapping[str, Predicate], *, candidates: Sequence[str],
                opponents: Sequence[str], draws: Sequence[Sequence[int]] | None = None) -> dict[str, Fraction]:
    """stab(P) for each named predicate over the O-BOOT resamples."""

    samples = draws if draws is not None else resample_positions(len(table.seeds))
    seed_payoffs = per_seed_table(table)
    counts = dict.fromkeys(predicates, 0)
    for positions in samples:
        sample = reading(table, candidates=candidates, opponents=opponents, positions=positions,
                         seed_payoffs=seed_payoffs)
        for name, predicate in predicates.items():
            counts[name] += bool(predicate(sample))
    return {name: Fraction(count, len(samples)) for name, count in counts.items()}


def n_distinct(table: ValueTable, i: str, j: str) -> int:
    """Distinct trajectories among the 64 F1 matches of i against j (both orientations)."""
    if i == j:
        return 0
    return len(set(table.trajectories[(i, j)]) | set(table.trajectories[(j, i)]))
