"""E8 descriptive telemetry: O-ACQ, O-REACQ, O-VERIF and the mechanism tables (phase I8-5).

docs/research/v6/V6_E8_ACTIVE_SPATIAL_SENSING_PREREGISTRATION.md (PR8) Sec 4,
6.3 and 6.5. **Every quantity here is descriptive and never an input to a
hypothesis, a row or a kill**, with one registered exception: O-VERIF's V(j)
enters the allocation-variation check of Sec 7.3, which only decides whether
H8-ADAPT is interpretable.

Each value is read from one cell's callback rows (``traces.extract``) and its
summary, never from the family's own source: the knowledge reconstruction
below re-implements the registered rules from PR8 Sec 2.5 and 3.2, as the
I8-3 ADAPT8 freeze-test oracle does. Definitions:

* **Information.** Under ``"active"`` an entrant learns a SENSE result at the
  acting process's next callback, its delivery (``previous_sense_anchors``).
  Under ``"passive"`` the known set is the callback's visible set.
* **O-ACQ** (Sec 4), per entrant: the first-discovery tick, meaning the first
  delivered SENSE result or visible set holding an enemy anchor; SENSE actions
  before and after first discovery; READ probes, meaning applied READs
  outside the entrant's own core; and whether it discovered at all.
* **Knowledge** (KU-1 to KU-9), for the members that re-acquire (``reacquire``
  ``repeat`` or ``adaptive``): a SENSE result updates knowledge only inside
  its window; an address inside it and absent from the result becomes
  missing; under passive a tracked address absent from the visible set
  becomes missing; a missing address is replaced by the nearest returned
  address, the lower on a tie.
* **O-REACQ** (Sec 4): a re-acquisition event is a result that replaces a
  missing address with a different one. Its cause is **evasion** if the
  opponent applied a MOVE between the row at which the missing address was
  last known and the replacing row; **own movement** if only the member
  itself moved in that interval; **neither** otherwise.
* **O-VERIF** (Sec 4), for ADAPT8: a verification is a SENSE at the entrant's
  first callback of a tick, after first discovery, with an address known and
  no search in progress, before ADAPT8 switches (PR8 Sec 3.2). Under passive,
  ADAPT8 has no verification action; its verification observations (the
  visible set at a tick's first callback, with a tracked address, before the
  switch) are counted instead. V(j) (``verification_v``) is the median over
  the seeds of the per-seed mean of the two orientations, with the exact
  median of E4 and E5 (``statistics.median`` over Fractions).
* **Mechanism tables** (Sec 6.3), per entrant: callbacks per tick; hits
  received (an opponent's applied WRITE at one of the entrant's anchors);
  hits inferred by EVADE8's rule; evasions (applied MOVEs by a member with
  ``evade`` on-hit); SENSE actions before and after first discovery; and
  re-acquisition events by cause.
"""

from __future__ import annotations

import statistics
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from fractions import Fraction
from itertools import pairwise
from typing import Any

from tools.research.v6.e6.rederive import circular_distance
from tools.research.v6.e8 import family, matrix, traces
from tools.research.v6.e8.traces import COLUMN

TELEMETRY_VERSION = 1
WINDOW = matrix.SENSING_WINDOW
ADAPT_K = 2
QUOTA = matrix.QUOTA
_C = COLUMN

Row = Sequence[Any]


def nearest(address: int, returned: Sequence[int], arena: int) -> int:
    """KU-7: the returned address at minimum circular distance, the lower on a tie."""
    return min(returned, key=lambda r: (circular_distance(r, address, arena), r))


@dataclass
class EntrantTelemetry:
    member: str
    callbacks: int = 0
    ticks_with_callbacks: int = 0
    first_discovery_tick: int | None = None
    senses_before_discovery: int = 0
    senses_after_discovery: int = 0
    read_probes: int = 0
    hits_received: int = 0
    hits_inferred: int = 0
    evasions: int = 0
    verifications: int = 0
    verification_observations: int = 0
    reacquisitions: Counter[str] = field(default_factory=Counter)

    def as_dict(self) -> dict[str, Any]:
        return {
            "member": self.member, "callbacks": self.callbacks, "ticks_with_callbacks": self.ticks_with_callbacks,
            "callbacks_per_tick": (None if not self.ticks_with_callbacks
                                   else f"{Fraction(self.callbacks, self.ticks_with_callbacks)}"),
            "first_discovery_tick": self.first_discovery_tick, "discovered": self.first_discovery_tick is not None,
            "senses_before_discovery": self.senses_before_discovery,
            "senses_after_discovery": self.senses_after_discovery, "read_probes": self.read_probes,
            "hits_received": self.hits_received, "hits_inferred": self.hits_inferred, "evasions": self.evasions,
            "verifications": self.verifications, "verification_observations": self.verification_observations,
            "reacquisitions": dict(sorted(self.reacquisitions.items())),
        }


class _Knowledge:
    """One re-acquiring entrant's registered knowledge, reconstructed from the trace alone."""

    def __init__(self, *, adaptive: bool, arena: int) -> None:
        self.adaptive, self.arena = adaptive, arena
        self.known: list[int] = []
        self.tracked: list[int] = []
        self.missing: dict[int, int] = {}  # missing address -> the row at which it was last known
        self.last_known: dict[int, int] = {}
        self.discovered = False
        self.switched = False
        self.count = 0
        self.search: int | None = None  # windows of an active search still to sense

    def _replace(self, returned: Sequence[int], order: int) -> list[tuple[int, int, int]]:
        """Every missing address replaced by its nearest returned one: (missing, replacement, last known row)."""
        events = [(address, nearest(address, returned, self.arena), since)
                  for address, since in sorted(self.missing.items())]
        self.missing = {}
        for _, replacement, _ in events:
            self.last_known[replacement] = order
        return events

    def active_result(self, result: Sequence[int], target: int, purpose: str | None,
                      order: int) -> list[tuple[int, int, int]]:
        gone = [x for x in self.known if circular_distance(x, target, self.arena) <= WINDOW and x not in result]
        lowest = self.known[0] if self.known else None
        self.known = sorted((set(self.known) - set(gone)) | set(result))
        for address in result:
            self.last_known[address] = order
        self.discovered = self.discovered or bool(result)
        if self.adaptive and not self.switched:
            if purpose == "verify":
                self.count = self.count + 1 if target in result else 0
            elif lowest is not None and lowest in gone:
                self.count = 0
            if self.count >= ADAPT_K:
                self.switched, self.search, self.missing = True, None, {}
                return []
        if self.switched:
            return []
        for address in gone:
            self.missing.setdefault(address, self.last_known.get(address, order))
        events: list[tuple[int, int, int]] = []
        if result:
            events = self._replace(result, order)
            self.search = None
        elif purpose == "verify" and gone:
            self.search = 2
        elif purpose == "search":
            self.search = None if self.search in (None, 1) else self.search - 1
            if self.search is None:
                self.missing = {}  # exhausted: the address is unknown
        return events

    def classify(self, index: int) -> str:
        if self.search is not None and not self.switched:
            return "search"
        if index == 1 and not self.switched and self.discovered and self.known:
            return "verify"
        return "discover"

    def passive_view(self, visible: Sequence[int], index: int, order: int) -> tuple[list[tuple[int, int, int]], bool]:
        """(re-acquisition events, whether this callback is a verification observation)."""
        observation = False
        if not self.switched and self.tracked:
            a = self.tracked[0]
            if self.adaptive:
                if a not in visible:
                    self.count = 0
                elif index == 1:
                    self.count += 1
                    observation = True
                if self.count >= ADAPT_K:
                    self.switched, self.missing = True, {}
        for address in visible:
            self.last_known[address] = order
        events: list[tuple[int, int, int]] = []
        if not self.switched:
            for address in self.tracked:
                if address not in visible:
                    self.missing.setdefault(address, self.last_known.get(address, order))
            if visible and self.missing:
                events = self._replace(list(visible), order)
        self.tracked = list(visible)
        self.known = list(visible)
        return events, observation


def cell_telemetry(rows: Sequence[Row], summary: Mapping[str, Any], *, members: Mapping[str, str],
                   active: bool, arena: int = matrix.ARENA_SIZE) -> dict[str, dict[str, Any]]:
    """Every descriptive quantity of one cell, per seat. ``members`` maps each seat to its member."""

    core = summary["core_base"]
    seats = sorted(core)
    rival = {seats[0]: seats[1], seats[1]: seats[0]}
    out = {seat: EntrantTelemetry(members[seat]) for seat in seats}
    reacquiring = {seat: family.MEMBERS[members[seat]]["reacquire"] in ("repeat", "adaptive") for seat in seats}
    knowledge = {seat: _Knowledge(adaptive=family.MEMBERS[members[seat]]["reacquire"] == "adaptive", arena=arena)
                 for seat in seats}
    evading = {seat: family.MEMBERS[members[seat]]["evade"] == "on-hit" for seat in seats}
    anchors: dict[str, Counter[int]] = {seat: Counter(summary["tick0_anchors"][seat].values()) for seat in seats}
    moves: dict[str, list[int]] = {seat: [] for seat in seats}  # row orders of applied MOVEs
    last_row: dict[tuple[str, str], tuple[Row, str | None]] = {}
    tick_counts: dict[str, Counter[int]] = {seat: Counter() for seat in seats}
    for order, row in enumerate(rows):
        seat, key = row[_C["entrant"]], (row[_C["entrant"]], row[_C["process"]])
        tick, index = row[_C["tick"]], row[_C["index"]]
        stats, mind = out[seat], knowledge[seat]
        stats.callbacks += 1
        tick_counts[seat][tick] += 1
        visible = list(row[_C["visible"]])
        delivered = row[_C["delivered"]]
        previous = last_row.get(key)
        events: list[tuple[int, int, int]] = []
        if active and previous is not None and previous[0][_C["kind"]] == "sense" and isinstance(delivered, list):
            target = int(previous[0][_C["operand"]]) % arena
            if reacquiring[seat]:
                events = mind.active_result(delivered, target, previous[1], order)
            elif delivered:
                mind.discovered = True
        if not active and reacquiring[seat]:
            events, observed = mind.passive_view(visible, index, order)
            stats.verification_observations += observed
        informed = bool(visible) or (isinstance(delivered, list) and bool(delivered))
        if informed and stats.first_discovery_tick is None:
            stats.first_discovery_tick = tick
        for missing, replacement, since in events:
            if replacement == missing:
                continue
            rival_moved = any(since <= moved < order for moved in moves[rival[seat]])
            own_moved = any(since <= moved < order for moved in moves[seat])
            stats.reacquisitions["evasion" if rival_moved else "own movement" if own_moved else "neither"] += 1
        kind, status = row[_C["kind"]], row[_C["status"]]
        purpose: str | None = None
        if kind == "sense":
            if stats.first_discovery_tick is None:
                stats.senses_before_discovery += 1
            else:
                stats.senses_after_discovery += 1
            if reacquiring[seat]:
                purpose = mind.classify(index)
                if purpose == "verify" and mind.adaptive:
                    stats.verifications += 1
        elif kind == "read" and status == "APPLIED" and not traces.in_core(row[_C["address"]], core[seat], arena):
            stats.read_probes += 1
        elif kind == "move" and status == "APPLIED":
            moves[seat].append(order)
            anchors[seat][row[_C["anchor"]]] -= 1
            anchors[seat][row[_C["address"]]] += 1
            if evading[seat]:
                stats.evasions += 1
        elif kind == "write" and status == "APPLIED" and anchors[rival[seat]][row[_C["address"]]] > 0:
            out[rival[seat]].hits_received += 1
        last_row[key] = (row, purpose)
    for seat in seats:
        ticks = sorted(tick_counts[seat])
        out[seat].ticks_with_callbacks = len(ticks)
        out[seat].hits_inferred = sum(
            1 for previous, current in pairwise(ticks)
            if current > previous + 1 or tick_counts[seat][previous] < QUOTA)
    return {seat: stats.as_dict() for seat, stats in out.items()}


def verification_v(per_seed: Mapping[int, Sequence[int]]) -> Fraction:
    """V(j): the exact median over the seeds of ADAPT8's mean verification count over the two orientations."""
    if not per_seed or any(len(counts) != 2 for counts in per_seed.values()):
        raise ValueError("V(j) needs both orientations at every seed")
    return Fraction(statistics.median(Fraction(sum(counts), 2) for counts in per_seed.values()))
