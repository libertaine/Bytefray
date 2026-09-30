"""PA-3: the exact cell-level decomposition of the four conditions.

Every E6 cell key (field, subject, opponent, orientation, seed) was played in
all four conditions with identical seat geometry and seat assignment, and the
engine is deterministic. So the four seat results of a key are exact
counterfactuals of one another. Each key is classified by the partition of
the four conditions into equal results:

* ``invariant``: all four equal;
* ``sensing_only``: equal within {C-E6, C-E6L} and within {T-E6, T-E6L}, and
  different between them;
* ``disruption_only``: equal within {C-E6, T-E6} and within {C-E6L, T-E6L},
  and different between them;
* ``interaction``: anything else, where the effect of one factor depends on
  the other. Sub-labelled by the one condition that differs when the other
  three agree (``odd:<condition>``), as ``diagonal`` when {C-E6, T-E6L}
  agree against {T-E6, C-E6L}, and as ``other`` otherwise.

The classification is exhaustive and mutually exclusive over every possible
four-tuple (a unit test enumerates them all).
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from typing import Any

from tools.research.v6 import experiment_harness as harness
from tools.research.v6.e6_audit import seat
from tools.research.v6.e6_audit.corpus import CONDITIONS, FIELDS

INVARIANT = "invariant"
SENSING_ONLY = "sensing_only"
DISRUPTION_ONLY = "disruption_only"
INTERACTION = "interaction"
CLASSES = (INVARIANT, SENSING_ONLY, DISRUPTION_ONLY, INTERACTION)


def classify(results: Mapping[str, str]) -> tuple[str, str | None]:
    """The class, and the interaction sub-label, of one key's four seat results."""

    c, t, cl, tl = (results[condition] for condition in CONDITIONS)  # C-E6, T-E6, C-E6L, T-E6L
    if c == t == cl == tl:
        return INVARIANT, None
    if c == cl and t == tl:
        return SENSING_ONLY, None
    if c == t and cl == tl:
        return DISRUPTION_ONLY, None
    by_condition = dict(zip(CONDITIONS, (c, t, cl, tl), strict=True))
    for odd in CONDITIONS:
        others = {value for condition, value in by_condition.items() if condition != odd}
        if len(others) == 1:
            return INTERACTION, f"odd:{odd}"
    if c == tl and t == cl:
        return INTERACTION, "diagonal"
    return INTERACTION, "other"


def cell_key(field_id: str, cell: Mapping[str, Any]) -> tuple[str, str, str, str, int]:
    return (field_id, str(cell["subject_id"]), str(cell["opponent_id"]), str(cell["orientation"]), int(cell["seed"]))


def unit_of(key: tuple[str, str, str, str, int]) -> str:
    """The frozen seat-metric unit a cell key belongs to (``F1|<pid>|<pid>`` in family order)."""

    field_id, subject, opponent, _orientation, _seed = key
    order = {pid: index for index, pid in enumerate(seat_units_order())}
    first, second = sorted((subject, opponent), key=lambda pid: order[pid])
    if field_id == "F2":
        return f"F2|{first}|{second}"
    return f"F1|{first}|{second}"


def seat_units_order() -> list[str]:
    """Package ids in the order the unit keys use them: primaries in family order, then twins."""

    order: list[str] = []
    for unit in seat.unit_keys():
        for pid in unit.split("|")[1:]:
            if pid not in order:
                order.append(pid)
    return order


def decompose(cells: Mapping[str, Mapping[str, Sequence[Mapping[str, Any]]]]) -> dict[str, Any]:
    """Classify every cell key; counts overall, per field, per unit and per interaction sub-label."""

    table: dict[tuple[str, str, str, str, int], dict[str, str]] = {}
    for condition in CONDITIONS:
        for field_id in FIELDS:
            for cell in cells[condition][field_id]:
                table.setdefault(cell_key(field_id, cell), {})[condition] = harness.cell_seat_result(cell)
    incomplete = [key for key, row in table.items() if set(row) != set(CONDITIONS)]
    if incomplete:
        raise ValueError(f"{len(incomplete)} cell keys lack a condition, e.g. {incomplete[0]}")
    overall: Counter[str] = Counter()
    by_field: dict[str, Counter[str]] = {field_id: Counter() for field_id in FIELDS}
    sublabels: Counter[str] = Counter()
    by_unit: dict[str, Counter[str]] = {}
    for key, row in table.items():
        cls, sub = classify(row)
        overall[cls] += 1
        by_field[key[0]][cls] += 1
        if sub is not None:
            sublabels[sub] += 1
        by_unit.setdefault(unit_of(key), Counter())[cls if sub is None else f"{cls}:{sub}"] += 1
    return {
        "keys": len(table),
        "overall": {cls: overall.get(cls, 0) for cls in CLASSES},
        "by_field": {field_id: {cls: counter.get(cls, 0) for cls in CLASSES} for field_id, counter in by_field.items()},
        "interaction_sublabels": dict(sorted(sublabels.items())),
        "by_unit": {seat.label(unit): dict(sorted(counter.items())) for unit, counter in sorted(by_unit.items())},
    }
