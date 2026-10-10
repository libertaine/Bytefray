"""D8-1: independent re-derivation of every SENSE's result (PR8 Sec 5.1; phase I8-5).

docs/research/v6/V6_E8_ACTIVE_SPATIAL_SENSING_PREREGISTRATION.md (PR8) D8-1:
"Every applied SENSE's authoritative tuple (Sec 10) equals the set of live
enemy anchor positions within <= 27 of t at execution. That set is re-derived
independently from the trace's ordered action stream: tick-0 anchors, the
normalized results of every MOVE, and disruption hits under the condition's
lambda."

Nothing here calls the engine. The scheduler is E6's D-1 re-derivation
(``tools/research/v6/e6/rederive.py``), reused for its offer order and quota
rules, which E6 qualified over 11,520 cells:

* **Offers.** Chunked, chunk 2, quota 8, the entrant order rotated by
  ``(tick - 1) mod 2``, forward pass order. A dead entrant gets no offer.
* **Eligibility and quotas.** Largest remainder over the unsuppressed
  processes' normalized shares, round robin from a match-scoped cursor.
* **Suppression.** An applied WRITE at a process's anchor, by another
  entrant, suppresses it for the rest of the tick; under lambda = 1 it is
  also released once its entrant has had one offer.
* **Positions.** Tick-0 anchors from the replay; a MOVE's operand is clamped
  to +/-64 and applied literally, and must equal the traced address.

E8 adds the SENSE rules of PR8 Sec 2.3, re-implemented from the registration:

* **Reach.** A SENSE at *t* is applied if and only if the circular distance
  from *t* mod 512 to the acting process's anchor is at most its declared
  reach; otherwise its status is ``REJECTED_OUT_OF_REACH``. The traced
  ``normalized_address`` must be *t* mod 512.
* **Result.** The ascending tuple of distinct positions of the processes of
  every other live entrant within the window of *t*, the comparison
  inclusive. The window is the one the reset records carry (D8-15), so the
  re-derivation uses exactly the recorded value.
* **No effect.** A SENSE changes no position and suppresses nothing; it
  occupies exactly one offer (D8-4), so any extra or missing callback after
  one fails the alignment.
* **Visibility.** Under ``"active"`` every predicted visible set is empty
  (D8-2). Under ``"passive"`` it is E6's rule, radius min(reach, 32); the
  passive branch exists so the simulator can be checked on the controls.

Every predicted callback must be the trace's next row (same tick, entrant and
process); any disagreement fails the cell.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from fractions import Fraction
from typing import Any

from tools.research.v6.e6.rederive import circular_distance, largest_remainder_quotas, offer_order
from tools.research.v6.e8.traces import ABSENT, COLUMN

REDERIVE_VERSION = 1
MAX_MOVE = 64
PASSIVE_RADIUS = 32
FORFEIT_STATUSES = frozenset({"EXCEPTION", "REJECTED_INVALID"})
SAMPLE_LIMIT = 10
_C = COLUMN


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


@dataclass(frozen=True)
class CellCheck:
    callbacks: int
    senses_applied: int
    senses_refused: int
    alignment_failures: int
    move_mismatches: int
    visibility_mismatches: int
    status_mismatches: int
    sensing_mismatches: int
    samples: tuple[dict[str, Any], ...]

    @property
    def passed(self) -> bool:
        return (self.alignment_failures, self.move_mismatches, self.visibility_mismatches, self.status_mismatches,
                self.sensing_mismatches) == (0, 0, 0, 0, 0)


def _normalized_shares(declared: Sequence[Sequence[Any]]) -> list[Fraction]:
    shares = [Fraction(str(item[2])) for item in declared]
    total = sum(shares, Fraction(0))
    return [share / total for share in shares]


def configured_window(summary: Mapping[str, Any]) -> int | None:
    """The window every reset record carries: 27 under active, None if every record omits it.

    Anything else -- a mix, an explicit null, two values -- is refused: D8-15
    fails on it, and the re-derivation cannot proceed from it.
    """
    values = [value for windows in summary["reset_windows"].values() for value in windows]
    if values and all(value == ABSENT for value in values):
        return None
    if values and all(isinstance(value, int) and not isinstance(value, bool) for value in values) \
            and len(set(values)) == 1:
        return int(values[0])
    raise ValueError(f"no single configured sensing window in the reset records: {summary['reset_windows']}")


def rederive_cell(rows: Sequence[Sequence[Any]], summary: Mapping[str, Any], *, ticks_run: int, arena: int,
                  slot_limit: int | None) -> CellCheck:
    """Re-derive one cell's callbacks, positions, visible sets and SENSE results from its rows."""

    window = configured_window(summary)
    names = sorted(summary["core_base"])
    entrants: dict[str, _Entrant] = {}
    for name in names:
        declared = summary["declarations"][name]
        anchors = summary["tick0_anchors"][name]
        processes = [_Process(name, str(item[0]), int(item[1]), share, int(anchors[str(item[0])]))
                     for item, share in zip(declared, _normalized_shares(declared), strict=True)]
        entrants[name] = _Entrant(name, processes)

    def suppressed(p: _Process, tick: int) -> bool:
        if not tick < p.disrupted_until:
            return False
        return slot_limit is None or p.slots_left > 0

    samples: list[dict[str, Any]] = []
    counts = dict.fromkeys(("callbacks", "applied", "refused", "alignment", "move", "visibility", "status",
                            "sensing"), 0)

    def fail(kind: str, **detail: Any) -> None:
        counts[kind] += 1
        if len(samples) < SAMPLE_LIMIT:
            samples.append({"kind": kind, **detail})

    def check() -> CellCheck:
        return CellCheck(counts["callbacks"], counts["applied"], counts["refused"], counts["alignment"],
                         counts["move"], counts["visibility"], counts["status"], counts["sensing"], tuple(samples))

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
                    fail("alignment", expected=list(expected), row=None if row is None else list(row[:3]))
                    return check()
                cursor += 1
                counts["callbacks"] += 1
                entrant.used[chosen.pid] += 1
                if row[_C["anchor"]] != chosen.position:
                    fail("move", tick=tick, entrant=name, process=chosen.pid, predicted_anchor=chosen.position,
                         traced_anchor=row[_C["anchor"]])
                    chosen.position = row[_C["anchor"]]
                enemies = [p for other in entrants.values() if other.name != name and other.alive
                           for p in other.processes]
                if window is None:
                    observers = [p for p in entrant.processes if not suppressed(p, tick)]
                    predicted_visible = sorted({e.position for e in enemies if any(
                        circular_distance(o.position, e.position, arena) <= min(o.reach, PASSIVE_RADIUS)
                        for o in observers)})
                else:
                    predicted_visible = []
                if sorted(row[_C["visible"]]) != predicted_visible:
                    fail("visibility", tick=tick, entrant=name, process=chosen.pid, predicted=predicted_visible,
                         traced=list(row[_C["visible"]]))
                kind, status = row[_C["kind"]], row[_C["status"]]
                if status in FORFEIT_STATUSES:
                    entrant.alive = False
                elif kind == "sense":
                    target = int(row[_C["operand"]]) % arena
                    reached = circular_distance(target, chosen.position, arena) <= chosen.reach
                    predicted_status = "APPLIED" if reached else "REJECTED_OUT_OF_REACH"
                    # PR8 Sec 10 registers normalized_address = t mod 512 for an applied
                    # SENSE only; a refusal's address is not registered.
                    if window is None or status != predicted_status or (reached and row[_C["address"]] != target):
                        fail("status", tick=tick, entrant=name, process=chosen.pid, status=status,
                             predicted=predicted_status if window is not None else "no SENSE without a window",
                             address=row[_C["address"]], target=target)
                    elif reached:
                        counts["applied"] += 1
                        predicted = sorted({e.position for e in enemies
                                            if circular_distance(e.position, target, arena) <= window})
                        if row[_C["sensed"]] != predicted:
                            fail("sensing", tick=tick, entrant=name, process=chosen.pid, target=target,
                                 predicted=predicted, traced=row[_C["sensed"]])
                    else:
                        counts["refused"] += 1
                        if row[_C["sensed"]] is not None:
                            fail("sensing", tick=tick, entrant=name, process=chosen.pid, target=target,
                                 predicted=None, traced=row[_C["sensed"]])
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
        fail("alignment", expected="end of trace", row=list(rows[cursor][:3]))
    return check()
