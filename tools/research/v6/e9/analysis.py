"""Exact paired seed-block estimands and guarded simultaneous uncertainty."""

from __future__ import annotations

import hashlib
from collections import Counter
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN, Decimal, localcontext
from fractions import Fraction

from .protocol import IntegrityError

GUARD = Fraction(1, 20)
MARGIN = Fraction(1, 10)


def positions(protocol_digest: str, instrument_digest: str, n: int) -> Iterator[int]:
    if n < 1 or any(len(d) != 64 or any(c not in "0123456789abcdef" for c in d)
                    for d in (protocol_digest, instrument_digest)):
        raise IntegrityError("invalid deterministic analysis randomization inputs")
    material = ("bytefray-e9-analysis-bootstrap-v1\n" + protocol_digest + "\n"
                + instrument_digest + "\n").encode()
    key = hashlib.sha256(material).digest()
    limit = (1 << 64) // n * n
    for counter in range(1 << 64):
        value = int.from_bytes(hashlib.sha256(key + counter.to_bytes(8, "big")).digest()[:8],
                               "big")
        if value < limit:
            yield value % n
    raise IntegrityError("analysis counter exhausted")


@dataclass(frozen=True)
class Interval:
    low: Fraction
    high: Fraction

    def __post_init__(self) -> None:
        if (not isinstance(self.low, Fraction) or not isinstance(self.high, Fraction)
                or self.low > self.high):
            raise IntegrityError("invalid exact interval")

    @property
    def status(self) -> str:
        return "SUPPORTED" if self.low >= MARGIN else (
            "REFUTED" if self.high < MARGIN else "UNRESOLVED")


def difference(treatment: Interval, comparators: Sequence[Interval]) -> Interval:
    if not comparators:
        raise IntegrityError("empty comparator set")
    return Interval(treatment.low - max(row.high for row in comparators),
                    treatment.high - max(row.low for row in comparators))


def tied_maxima(means: Mapping[str, Fraction], members: Sequence[str]) -> tuple[str, ...]:
    best = max(means[m] for m in members)
    return tuple(sorted(m for m in members if means[m] == best))


@dataclass(frozen=True)
class Uncertainty:
    means: dict[str, Fraction]
    bands: dict[str, Interval]
    half_width: Fraction
    bootstrap_envelope: Fraction
    comparator_changes: int
    resampled_quantity_ranges: dict[str, tuple[Fraction, Fraction]]


def uncertainty(block_scores: Mapping[str, Sequence[int]], *, protocol_digest: str,
                instrument_digest: str, resamples: int = 20_000,
                order_statistic: int = 19_000,
                comparator_groups: Sequence[Sequence[str]] = (),
                derived_contrasts: Mapping[str, tuple[str, Sequence[str]]] | None = None) -> Uncertainty:
    """Scores are sums of 22 doubled payoffs: integer 0..44 per seed block.

    The pure kernel supports small independent qualification fixtures. The
    registered entry point enforces the frozen N, row set and resample count.
    """
    rows = dict(block_scores)
    sizes = {len(v) for v in rows.values()}
    if (not rows or len(sizes) != 1 or next(iter(sizes)) < 1
            or not 1 <= order_statistic <= resamples
            or any(type(v) is not int or not 0 <= v <= 44 for row in rows.values() for v in row)):
        raise IntegrityError("invalid complete integer seed-block vectors")
    n = next(iter(sizes))
    denominator = 44 * n
    totals = {name: sum(row) for name, row in rows.items()}
    means = {name: Fraction(total, denominator) for name, total in totals.items()}
    draws = positions(protocol_digest, instrument_digest, n)
    errors: list[int] = []
    changes = 0
    ranges: dict[str, tuple[int, int]] = {}
    observed = [tied_maxima(means, group) for group in comparator_groups]
    for _ in range(resamples):
        selected = tuple(next(draws) for _ in range(n))
        sampled = {name: sum(row[i] for i in selected) for name, row in rows.items()}
        errors.append(max(abs(sampled[name] - total) for name, total in totals.items()))
        for group, initial in zip(comparator_groups, observed):
            maximum = max(sampled[name] for name in group)
            ties = tuple(sorted(name for name in group if sampled[name] == maximum))
            changes += ties != initial
        for label, (focal, group) in (derived_contrasts or {}).items():
            value = sampled[focal] - max(sampled[m] for m in group)
            low, high = ranges.get(label, (value, value))
            ranges[label] = min(low, value), max(high, value)
    errors.sort()
    c = Fraction(errors[order_statistic - 1], denominator)
    r = max(GUARD, c)
    bands = {name: Interval(max(Fraction(0), mean - r), min(Fraction(1), mean + r))
             for name, mean in means.items()}
    return Uncertainty(means, bands, r, c, changes,
                       {label: (Fraction(lo, denominator), Fraction(hi, denominator))
                        for label, (lo, hi) in ranges.items()})


def registered_uncertainty(block_scores: Mapping[str, Sequence[int]], protocol: dict,
                           instrument_digest: str, protocol_digest: str) -> Uncertainty:
    if (set(block_scores) != set(protocol["physical_rows"])
            or any(len(row) != 1412 for row in block_scores.values())):
        raise IntegrityError("analysis requires all 29 rows at all 1,412 seed positions")
    aliases = protocol["logical_aliases"]
    groups = [tuple(dict.fromkeys(aliases.get(m, m) for m in protocol["groups"][g]))
              for g in ("F", "S", "H")]
    derived = {g: ("A", tuple(aliases.get(m, m) for m in members))
               for g, members in protocol["groups"].items()}
    for q in protocol["groups"]["S"]:
        derived[q + "-F"] = q, groups[0]
        derived["A-" + q] = "A", (q,)
    return uncertainty(block_scores, protocol_digest=protocol_digest,
                       instrument_digest=instrument_digest, comparator_groups=groups,
                       derived_contrasts=derived)


def contrasts(result: Uncertainty, protocol: dict) -> dict:
    aliases = protocol["logical_aliases"]
    bands = {**result.bands, **{alias: result.bands[row] for alias, row in aliases.items()}}
    means = {**result.means, **{alias: result.means[row] for alias, row in aliases.items()}}
    gaps = {g: difference(bands["A"], [bands[m] for m in members])
            for g, members in protocol["groups"].items()}
    reproducing = tuple(q for q in protocol["groups"]["S"]
                        if difference(bands[q], [bands[f] for f in protocol["groups"]["F"]]).low
                        >= MARGIN and difference(bands["A"], [bands[q]]).high <= MARGIN)
    return {"gaps": gaps, "point_gaps": {g: means["A"] - max(means[m] for m in members)
                                         for g, members in protocol["groups"].items()},
            "ties": {g: tied_maxima(means, members) for g, members in protocol["groups"].items()},
            "timing_reproducing": reproducing,
            "timing_qualifier": bool(reproducing and gaps["F"].status == "SUPPORTED"
                                      and gaps["D"].status == "SUPPORTED")}


def decimal_display(value: Fraction) -> str:
    with localcontext() as context:
        context.prec = max(40, len(str(abs(value.numerator))) + len(str(value.denominator)) + 10)
        return str((Decimal(value.numerator) / Decimal(value.denominator)).quantize(
            Decimal("0.000001"), rounding=ROUND_HALF_EVEN))


def distinct_trajectories(digests: Sequence[str]) -> dict[str, int]:
    counts = Counter(digests)
    return {"cells": len(digests), "distinct": len(counts),
            "duplicate_cells": sum(n - 1 for n in counts.values())}
