"""Prospective seat, stall, pressure/capture and phase interpretation constraints."""

from __future__ import annotations

from collections.abc import Mapping
from fractions import Fraction
from typing import Any

from .protocol import IntegrityError

Key = tuple[str, str, int, str]


def evaluate(evidence: Mapping[Key, dict[str, Any]], protocol: dict[str, Any], *, n: int = 1412
             ) -> dict[str, Any]:
    """The registered caller supplies a verified complete rectangle.

    A smaller N is accepted only by this pure fixture kernel. Exposed seed
    positions are always counted as a set, never as callback observations.
    """
    aliases = protocol["logical_aliases"]
    fixed = protocol["groups"]["F"]
    opponents = tuple(protocol["historical_members"])
    strata = {f"{opp}/{seat}": [(opp, pos, seat) for pos in range(1, n + 1)]
              for opp in opponents for seat in ("A", "B")}
    strata.update({f"opponent/{opp}": [(opp, pos, seat) for pos in range(1, n + 1)
                                      for seat in ("A", "B")] for opp in opponents})
    strata.update({f"seat/{seat}": [(opp, pos, seat) for opp in opponents
                                   for pos in range(1, n + 1)] for seat in ("A", "B")})
    strata["aggregate"] = [(opp, pos, seat) for opp in opponents for pos in range(1, n + 1)
                           for seat in ("A", "B")]

    def item(row: str, coordinates: tuple[str, int, str]) -> dict[str, Any]:
        opp, position, seat = coordinates
        try:
            return evidence[(aliases.get(row, row), opp, position, seat)]
        except KeyError:
            raise IntegrityError("constraint input is an incomplete paired rectangle") from None

    severe: set[str] = set()
    output: dict[str, Any] = {}
    seat_gaps: dict[str, Fraction] = {}
    for name, coordinates in strata.items():
        denominator = 2 * len(coordinates)
        means = {row: Fraction(sum(item(row, coord)["payoff_doubled"] for coord in coordinates),
                               denominator) for row in ("A", *fixed)}
        maximum = max(means[f] for f in fixed)
        ties = tuple(sorted(f for f in fixed if means[f] == maximum))
        gap = means["A"] - maximum
        tau = Fraction(sum(item("A", c)["terminal"] == "tick_limit" for c in coordinates),
                       len(coordinates))
        nonlimit = {f: Fraction(sum(item("A", c)["payoff_doubled"] - item(f, c)["payoff_doubled"]
                                   for c in coordinates if item("A", c)["terminal"] != "tick_limit"),
                              denominator) for f in ties}
        stall = tau >= Fraction(1, 2) and gap >= Fraction(1, 10) and any(v <= 0 for v in nonlimit.values())
        if stall:
            severe.add(f"stall/{name}")
        output[name] = {"means": means, "strongest_fixed_ties": ties, "gap": gap,
                        "tick_limit_fraction": tau, "nonlimit_contribution_full_denominator": nonlimit,
                        "stall_warning": tau >= Fraction(1, 2), "severe_stall": stall}
        if name.startswith("seat/"):
            seat_gaps[name[-1]] = gap
        if name.startswith(("seat/", "opponent/")) or name == "aggregate":
            continue
        immunity: dict[str, Any] = {}
        for direction in ("focal", "opponent"):
            exposed = [c for c in coordinates if item("A", c)["pressure"][
                c[2] if direction == "focal" else ("B" if c[2] == "A" else "A")]]
            positions = {c[1] for c in exposed}

            def victim(c: tuple[str, int, str], direction: str = direction) -> str:
                return c[2] if direction == "focal" else ("B" if c[2] == "A" else "A")

            a_captures = sum(item("A", c)["captures"][victim(c)] for c in exposed)
            stalled = sum(item("A", c)["terminal"] == "tick_limit" for c in exposed)
            f_captures = {f: sum(item(f, c)["captures"][victim(c)] for c in exposed) for f in fixed}
            qualified = len(positions) >= 30
            pattern = (qualified and a_captures == 0 and 2 * stalled >= len(exposed)
                       and any(2 * v >= len(exposed) for v in f_captures.values()))
            if pattern:
                severe.add(f"immunity/{name}/{direction}")
            immunity[direction] = {"exposed_positions": len(positions), "a_captures": a_captures,
                                   "fixed_captures": f_captures, "severe": pattern,
                                   "exposure_status": "sufficient" if qualified else "insufficient exposure"}
        phase_counts = {p: sum((item("A", c).get("behavior") or {}).get("phase_differences", {}).get(str(p), 0)
                               for c in coordinates) for p in (1, 2, 3)}
        exposures = {p: {c[1] for c in coordinates if p in (item("A", c).get("behavior") or {}).get(
            "phase_exposure", [])} for p in (1, 2, 3)}
        phase_details: list[dict[str, Any]] = []
        for f in ties:
            positive = sum(max(0, item("A", c)["payoff_doubled"] - item(f, c)["payoff_doubled"])
                           for c in coordinates)
            for phase in (1, 2, 3):
                only = [c for c in coordinates if {p for p in (1, 2, 3) if (
                    item("A", c).get("behavior") or {}).get("phase_differences", {}).get(str(p), 0)} == {phase}]
                contributing = [c for c in only if item("A", c)["payoff_doubled"] > item(f, c)["payoff_doubled"]]
                contribution = sum(item("A", c)["payoff_doubled"] - item(f, c)["payoff_doubled"] for c in contributing)
                concentrated = (sum(phase_counts.values()) > 0 and positive > 0 and gap >= Fraction(1, 10)
                                and 100 * phase_counts[phase] >= 95 * sum(phase_counts.values())
                                and 100 * contribution >= 95 * positive)
                exposure_ok = (len({c[1] for c in contributing}) >= 30
                               and all(len(exposures[p]) >= 30 for p in (1, 2, 3) if p != phase))
                if concentrated and exposure_ok:
                    severe.add(f"phase/{name}/{f}/{phase}")
                phase_details.append({"fixed": f, "phase": phase, "positive_contribution_doubled": contribution,
                                      "positive_total_doubled": positive,
                                      "contributing_positions": len({c[1] for c in contributing}),
                                      "severe": concentrated and exposure_ok,
                                      "scope_restriction": concentrated and not exposure_ok})
        output[name].update({"immunity": immunity, "phase_counts": phase_counts,
                             "phase_exposed_positions": {p: len(v) for p, v in exposures.items()},
                             "phase_details": phase_details})
    seat_severe = ((seat_gaps["A"] >= Fraction(1, 10) and seat_gaps["B"] <= Fraction(-1, 10))
                   or (seat_gaps["B"] >= Fraction(1, 10) and seat_gaps["A"] <= Fraction(-1, 10)))
    if seat_severe:
        severe.add("seat dependence")
    return {"severe": tuple(sorted(severe)), "strata": output,
            "severe_seat_dependence": seat_severe}
