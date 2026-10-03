"""E6-D clause D-1: independent re-derivation of every callback's visible set.

docs/research/v6/V6_E6_PRICED_SENSING_PREREGISTRATION.md Sec 5.1 (D-1):
"At every callback of every treatment cell, the traced
``visible_enemy_anchor_addresses`` equals the set of live enemy anchors
within min(reach, 32) of some unsuppressed friendly process. That set is
re-derived independently from the trace's ordered action stream: tick-0
anchors, the normalized results of every MOVE, and disruption hits under
the condition's lambda."

Nothing here calls the engine. The documented rules are re-implemented
from their specifications (RULES_V4 and ``RulesetPolicy``), and each is
cross-checked against the trace wherever the trace records it:

* **Offers.** Chunked, chunk 2, quota 8, the entrant order rotated by
  ``(tick - 1) mod 2``, forward pass order. A dead entrant gets no offer.
* **Eligibility and quotas.** At each offer an entrant's unsuppressed
  processes share the quota of 8 by largest remainder (ties by process id)
  in proportion to their normalized declared shares. Selection is round
  robin from a match-scoped cursor over declaration order, among processes
  still under their quota. An offer with no selectable process produces no
  callback.
* **Suppression.** A hit (an applied WRITE at a process's current anchor, by
  another entrant) suppresses that process for the rest of the tick. With
  lambda = 1 it is also released once its own entrant has had one offer:
  the processes suppressed when an offer begins each use one suppressed
  offer, however the offer ends. A later hit resets the count; it never
  adds to it.
* **Positions.** Tick-0 anchors come from the replay. A MOVE's operand is
  clamped to +/-64 and applied literally, and the result must equal the
  trace's normalized address.
* **Visibility.** ``{enemy anchor : some unsuppressed friendly process is
  within min(reach, d)}``, circular distance, inclusive. Enemy anchors of a
  dead entrant are excluded.

Every predicted callback must be the trace's next row (same tick, entrant
and process); any disagreement fails the cell.
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from fractions import Fraction
from typing import Any

from tools.research.v6.e6.telemetry import ROW_FIELDS

REDERIVE_VERSION = 1
QUOTA = 8
CHUNK = 2
MAX_MOVE = 64
FORFEIT_STATUSES = frozenset({"EXCEPTION", "REJECTED_INVALID"})
SAMPLE_LIMIT = 10
_C = {name: index for index, name in enumerate(ROW_FIELDS)}


@dataclass
class _Process:
    entrant: str
    pid: str
    reach: int
    share: Fraction
    position: int
    disrupted_until: int = 0
    slots_left: int = 0


@dataclass
class _Entrant:
    name: str
    processes: list[_Process]
    cursor: int = 0
    alive: bool = True
    used: dict[str, int] = field(default_factory=dict)


def circular_distance(a: int, b: int, arena: int) -> int:
    d = (a - b) % arena
    return min(d, arena - d)


def offer_order(tick: int, entrants: Sequence[str], *, quota: int = QUOTA, chunk: int = CHUNK) -> Iterator[str]:
    """The entrant of every offer of one tick, in order (chunked, rotated, forward)."""
    offset = (tick - 1) % len(entrants)
    order = list(entrants[offset:]) + list(entrants[:offset])
    passes = (quota + chunk - 1) // chunk
    for p in range(passes):
        for entrant in order:
            for _slot in range(p * chunk, min((p + 1) * chunk, quota)):
                yield entrant


def largest_remainder_quotas(eligible: Sequence[_Process], quota: int = QUOTA) -> dict[str, int]:
    total = sum((p.share for p in eligible), Fraction(0))
    if not eligible or total <= 0:
        return {}
    allocation = {p.pid: int((quota * p.share) // total) for p in eligible}
    spare = quota - sum(allocation.values())
    for p in sorted(eligible, key=lambda p: (-((quota * p.share) % total), p.pid))[:spare]:
        allocation[p.pid] += 1
    return allocation


def _normalized_shares(declared: Sequence[Sequence[Any]]) -> list[Fraction]:
    shares = [Fraction(str(item[2])) for item in declared]
    total = sum(shares, Fraction(0))
    return [share / total for share in shares]


@dataclass(frozen=True)
class CellCheck:
    callbacks: int
    visibility_mismatches: int
    alignment_failures: int
    move_mismatches: int
    samples: tuple[dict[str, Any], ...]

    @property
    def passed(self) -> bool:
        return (self.visibility_mismatches, self.alignment_failures, self.move_mismatches) == (0, 0, 0)


def rederive_cell(rows: Sequence[Sequence[Any]], summary: Mapping[str, Any], *, ticks_run: int, arena: int,
                  detection_radius: int | None, slot_limit: int | None) -> CellCheck:
    """Re-derive one cell's visible sets from its rows and compare them with the trace."""

    names = sorted(summary["core_base"])
    entrants: dict[str, _Entrant] = {}
    for name in names:
        declared = summary["declarations"][name]
        shares = _normalized_shares(declared)
        anchors = summary["tick0_anchors"][name]
        processes = [_Process(name, str(item[0]), int(item[1]), share, int(anchors[str(item[0])]))
                     for item, share in zip(declared, shares, strict=True)]
        entrants[name] = _Entrant(name, processes)

    def suppressed(p: _Process, tick: int) -> bool:
        if not tick < p.disrupted_until:
            return False
        return slot_limit is None or p.slots_left > 0

    def radius(p: _Process) -> int:
        return p.reach if detection_radius is None else min(p.reach, detection_radius)

    samples: list[dict[str, Any]] = []
    counts = {"callbacks": 0, "visibility": 0, "alignment": 0, "move": 0}

    def fail(kind: str, **detail: Any) -> None:
        counts[kind] += 1
        if len(samples) < SAMPLE_LIMIT:
            samples.append({"kind": kind, **detail})

    cursor = 0
    for tick in range(1, ticks_run + 1):
        for entrant in entrants.values():
            entrant.used = {p.pid: 0 for p in entrant.processes}
        for name in offer_order(tick, names):
            entrant = entrants[name]
            if not entrant.alive:
                continue
            held = [p for p in entrant.processes if suppressed(p, tick)]
            eligible = [p for p in entrant.processes if not suppressed(p, tick)]
            quotas = largest_remainder_quotas(eligible)
            chosen: _Process | None = None
            count = len(entrant.processes)
            for offset in range(count):
                index = (entrant.cursor + offset) % count
                candidate = entrant.processes[index]
                if entrant.used[candidate.pid] < quotas.get(candidate.pid, 0):
                    chosen = candidate
                    entrant.cursor = (index + 1) % count
                    break
            if chosen is not None:
                row = rows[cursor] if cursor < len(rows) else None
                expected = (tick, name, chosen.pid)
                if row is None or (row[_C["tick"]], row[_C["entrant"]], row[_C["process"]]) != expected:
                    fail("alignment", expected=list(expected), row=None if row is None else list(row[:4]))
                    return CellCheck(counts["callbacks"], counts["visibility"], counts["alignment"], counts["move"],
                                     tuple(samples))
                cursor += 1
                counts["callbacks"] += 1
                entrant.used[chosen.pid] += 1
                observers = [p for p in entrant.processes if not suppressed(p, tick)]
                enemies = [p for other in entrants.values() if other.name != name and other.alive
                           for p in other.processes]
                predicted = sorted({e.position for e in enemies
                                    if any(circular_distance(o.position, e.position, arena) <= radius(o)
                                           for o in observers)})
                traced = sorted(row[_C["visible"]])
                if predicted != traced:
                    fail("visibility", tick=tick, entrant=name, process=chosen.pid, predicted=predicted,
                         traced=traced)
                if row[_C["anchor"]] != chosen.position:
                    fail("move", tick=tick, entrant=name, process=chosen.pid, predicted_anchor=chosen.position,
                         traced_anchor=row[_C["anchor"]])
                    chosen.position = row[_C["anchor"]]
                kind, status = row[_C["kind"]], row[_C["status"]]
                if status in FORFEIT_STATUSES:
                    entrant.alive = False
                elif status == "APPLIED" and kind == "move":
                    operand = row[_C["operand"]] or 0
                    moved = (chosen.position + max(-MAX_MOVE, min(MAX_MOVE, operand))) % arena
                    if moved != row[_C["address"]]:
                        fail("move", tick=tick, entrant=name, process=chosen.pid, predicted_move=moved,
                             traced_move=row[_C["address"]])
                    chosen.position = moved
                elif status == "APPLIED" and kind == "write":
                    target = row[_C["address"]]
                    for other in entrants.values():
                        if other.name == name or not other.alive:
                            continue
                        for victim in other.processes:
                            if victim.position == target:
                                victim.disrupted_until = tick + 1
                                if slot_limit is not None:
                                    victim.slots_left = slot_limit
            if slot_limit is not None:
                for p in held:
                    p.slots_left -= 1
    if cursor != len(rows):
        fail("alignment", expected="end of trace", row=list(rows[cursor][:4]))
    return CellCheck(counts["callbacks"], counts["visibility"], counts["alignment"], counts["move"], tuple(samples))
