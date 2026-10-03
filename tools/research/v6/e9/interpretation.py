"""The frozen ordered decision table; behavior, payoff and H stay separate."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from .protocol import IntegrityError


@dataclass(frozen=True)
class Classification:
    priority: int
    primary: str
    qualifiers: tuple[str, ...]
    historical: str
    broader_fixed_superiority: bool


def classify(*, integrity: bool, realized_revisions: int, realized_positions: int,
             seat_positions: Mapping[str, int], statuses: Mapping[str, str],
             severe_constraints: tuple[str, ...] = (), timing_reproduced: bool = False
             ) -> Classification:
    if type(integrity) is not bool:
        raise IntegrityError("integrity predicate is not explicit")
    if not integrity:
        return Classification(1, "NOT EVALUABLE", (), "NOT EVALUABLE", False)
    if (set(statuses) != {"F", "D", "S", "H"}
            or any(s not in {"SUPPORTED", "REFUTED", "UNRESOLVED"} for s in statuses.values())
            or set(seat_positions) != {"A", "B"}
            or any(type(n) is not int or n < 0 for n in
                   (realized_revisions, realized_positions, *seat_positions.values()))
            or any(n > realized_positions for n in seat_positions.values())
            or realized_positions > realized_revisions
            or realized_positions > sum(seat_positions.values())):
        raise IntegrityError("inconsistent classification inputs")
    behavior = realized_positions >= 2 and all(n >= 1 for n in seat_positions.values())
    refuted = any(statuses[g] == "REFUTED" for g in ("F", "D", "S"))
    supported = all(statuses[g] == "SUPPORTED" for g in ("F", "D", "S"))
    qualifiers = list(severe_constraints)
    if realized_revisions == 0:
        priority, label = 2, "REFUTED bounded benefit claim"
        qualifiers.append("No realized observation-driven action revision in the registered sample")
    elif not behavior:
        priority, label = 3, "NOT EVALUABLE"
        qualifiers.append("Positive realization, insufficient registered replication or seat coverage")
    elif refuted:
        priority, label = 4, "REFUTED bounded benefit claim"
        qualifiers.extend(f"{g} practical benefit refuted" for g in ("F", "D", "S")
                          if statuses[g] == "REFUTED")
    elif not supported:
        priority, label = 5, "Behavior demonstrated; benefit NEITHER"
    elif severe_constraints:
        priority, label = 6, "Behavior demonstrated; benefit NEITHER"
        qualifiers.append("Payoff gates pass; registered interaction constraint blocks aggregate attribution")
    else:
        priority, label = 7, "SUPPORTED beneficial adaptation"
    if timing_reproduced:
        if statuses["F"] != "SUPPORTED" or statuses["D"] != "SUPPORTED":
            raise IntegrityError("timing qualifier requires supported fixed and disabled benefit")
        qualifiers.append("timing explanation unresolved")
    if statuses["S"] == "UNRESOLVED":
        qualifiers.append("schedule exclusion unresolved")
    historical = {"SUPPORTED": "Practical superiority over the declared historical nonadaptive set established",
                  "REFUTED": "Specified historical practical superiority refuted",
                  "UNRESOLVED": "Historical practical superiority unresolved"}[statuses["H"]]
    return Classification(priority, label, tuple(qualifiers), historical,
                          priority == 7 and statuses["H"] == "SUPPORTED")
