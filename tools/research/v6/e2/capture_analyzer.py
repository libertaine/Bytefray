"""Replay-derived E2 capture telemetry (design review Sec K; harness defect HD-5).

Reads one canonical schema-4 replay -- never writes it and needs no new
replay field -- and rebuilds, for every entrant, the capture state machine
the runtime applies (review Sec C.2):

* ownership: the tick-0 seeding diffs, then every tick's memory diffs in
  execution order (each diff records its writer);
* each entrant's core: the contiguous run of its seeded cells starting at
  its recorded ``pc`` (the core base), modulo the arena, cross-checked
  against its tick-0 seeding diffs -- two diffs when the core wraps the
  arena end (analyzer version 2; version 1 assumed one diff per core and
  raised on every wrapped core);
* the hold length K: the header's ``ruleset_id`` resolved through the
  executable Ruleset registry (``capture_hold_ticks``);
* the first mover of each tick: the same policy's chunked scheduler with
  start rotation, i.e. seat ``(tick - 1) % entrants``.

Definitions, one capture evaluation per live entrant per tick:

* an entrant is *evaluated* at tick ``t`` if it was alive at the end of
  ``t - 1`` and did not forfeit during ``t`` (forfeit is never a capture);
* *zero-core evaluation*: it owns none of its core cells at that evaluation;
* *onset*: a zero-core evaluation that begins a new streak -- the previous
  evaluation was positive (or there was none). Onsets are never inferred
  from kill events;
* *recovery*: a positive evaluation directly after a zero streak;
* *completion*: the evaluation at which the streak reaches K (capture);
* *phase-lock*: the share of an entrant's zero-core evaluations that fall on
  ticks where its opponent moves first.

Every derived completion is cross-checked against the replay's own
``kill``/``death`` events and entrant termination reasons, and the onset
capturer is re-derived independently (the writer that removed the entrant's
last owned core cell during the onset tick) and compared with the kill
event's ``killer``. Any disagreement is reported, never smoothed over.

Research-only; imports no runtime internals beyond the replay reader and
the Ruleset registry.
"""

from __future__ import annotations

import json
import sys
from collections.abc import Collection, Mapping, Sequence
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from battle_engine.replay import (
    KillDeathEvent,
    MatchResult,
    ReplayHeader,
    RuntimeEvent,
    TickSnapshot,
    iter_replay,
)
from battle_engine.ruleset_policy import resolve_ruleset_policy

CAPTURE_ANALYZER_VERSION = 2


@dataclass
class CoreInference:
    """Audit of the E2 fixtures' legal enemy-core inference (review Sec G.1).

    The inferring fixtures adopt, at their first callback in which every
    visible enemy anchor is at one address, that address as the enemy core
    base. With global reach every live enemy process is visible, so the
    replay's per-tick anchors determine what the agent could see, except
    inside a tick in which the enemy moved (the replay stores anchors only at
    tick boundaries). Enemy location sets that are multi-location at both
    boundaries of a tick are taken not to pass through a single location
    within it; this holds for every E2 fixture, whose movers move once.

    ``status``: ``inferred`` (exact), ``ambiguous`` (the replay cannot tell
    whether the agent adopted one of ``possible_bases``), or
    ``not_inferred``. ``correct`` is True when every base the agent could
    have adopted is the enemy's true core base, False if any is not, and
    None when no base could have been adopted.
    """

    status: str
    inferred_base: int | None
    inference_tick: int | None
    possible_bases: list[int]
    enemy_core_base: int
    correct: bool | None


@dataclass
class EntrantCapture:
    agent_id: str
    name: str | None
    seat_index: int
    core_base: int
    core_size: int
    evaluations: int = 0
    zero_core_ticks: list[int] = field(default_factory=list)
    onset_ticks: list[int] = field(default_factory=list)
    onset_capturers: list[str | None] = field(default_factory=list)
    recovery_ticks: list[int] = field(default_factory=list)
    completion_tick: int | None = None
    max_streak: int = 0
    final_streak: int = 0
    final_owned: int = 0
    alive_at_end: bool = True
    termination: str | None = None
    zero_ticks_opponent_first: int = 0
    zero_ticks_own_first: int = 0
    onsets_opponent_first: int = 0
    onsets_own_first: int = 0
    max_locations: int = 1
    enemy_core_writes: int = 0
    core_inference: CoreInference | None = None

    @property
    def onsets(self) -> int:
        return len(self.onset_ticks)

    @property
    def recoveries(self) -> int:
        return len(self.recovery_ticks)

    @property
    def completions(self) -> int:
        return 0 if self.completion_tick is None else 1

    @property
    def zero_core_evaluations(self) -> int:
        return len(self.zero_core_ticks)

    @property
    def phase_lock(self) -> float | None:
        zero = self.zero_core_evaluations
        return None if zero == 0 else round(self.zero_ticks_opponent_first / zero, 6)

    @property
    def recovery_rate(self) -> float | None:
        return None if not self.onset_ticks else round(self.recoveries / self.onsets, 6)

    @property
    def first_onset_tick(self) -> int | None:
        return self.onset_ticks[0] if self.onset_ticks else None

    @property
    def capture_threatened_at_end(self) -> bool:
        return self.alive_at_end and self.final_streak >= 1

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data.update(
            {
                "onsets": self.onsets,
                "recoveries": self.recoveries,
                "completions": self.completions,
                "zero_core_evaluations": self.zero_core_evaluations,
                "phase_lock": self.phase_lock,
                "recovery_rate": self.recovery_rate,
                "first_onset_tick": self.first_onset_tick,
                "capture_threatened_at_end": self.capture_threatened_at_end,
            }
        )
        return data


def first_mover_seat(tick: int, entrant_count: int, rotate_start: bool) -> int:
    """Seat index acting first at ``tick`` under the chunked scheduler."""
    if rotate_start and entrant_count > 1:
        return (tick - 1) % entrant_count
    return 0


def _addresses(diff_address: int, length: int, arena: int) -> list[int]:
    return [(diff_address + offset) % arena for offset in range(length)]


def _onset_capturer(
    victim: str,
    core: Sequence[int],
    before: Mapping[int, str | None],
    writes: Sequence[tuple[int, str | None]],
) -> str | None:
    """Independent re-derivation of the runtime's capture attribution.

    Replays this tick's writes over the victim's core from its pre-tick
    ownership and returns the writer of the write that removed its last
    owned cell; ``None`` if it owned no core cell before the tick.
    """
    core_set = set(core)
    local = {address: before.get(address) for address in core}
    remaining = sum(1 for owner in local.values() if owner == victim)
    if remaining == 0:
        return None
    for address, owner in writes:
        if address not in core_set or local[address] == owner:
            continue
        previous = local[address]
        local[address] = owner
        if previous == victim:
            remaining -= 1
            if remaining == 0:
                return owner
    return None


def _audit_inference(
    seat: int,
    enemy_core_base: int,
    boundaries: Sequence[frozenset[int]],
    cpu: Sequence[int],
    first_movers: Sequence[int],
) -> CoreInference:
    """``boundaries[t]``: enemy anchor set at the end of tick ``t`` (``t = 0``: spawn)."""

    def verdict(status: str, bases: list[int], tick: int | None) -> CoreInference:
        return CoreInference(
            status=status,
            inferred_base=bases[0] if status == "inferred" else None,
            inference_tick=tick,
            possible_bases=bases,
            enemy_core_base=enemy_core_base,
            correct=None if not bases else all(base == enemy_core_base for base in bases),
        )

    for tick in range(1, len(boundaries)):
        if cpu[tick] <= 0:
            continue
        before, after = boundaries[tick - 1], boundaries[tick]
        if first_movers[tick] == seat:
            if len(before) == 1:
                return verdict("inferred", sorted(before), tick)
            if after != before and len(after) == 1:
                return verdict("ambiguous", sorted(after), tick)
            continue
        if before == after:
            if len(before) == 1:
                return verdict("inferred", sorted(before), tick)
            continue
        singles = sorted({next(iter(s)) for s in (before, after) if len(s) == 1})
        if singles:
            return verdict("ambiguous", singles, tick)
    return verdict("not_inferred", [], None)


def analyze_replay(
    replay_path: Path | str,
    *,
    names_inferring_core: Collection[str] = (),
) -> dict[str, Any]:
    """Capture telemetry for one replay.

    ``names_inferring_core``: entrant (agent) names whose fixture follows the
    single-location core-inference contract; they get a ``core_inference``
    audit.
    """
    header: ReplayHeader | None = None
    ticks: list[TickSnapshot] = []
    result: MatchResult | None = None
    for record in iter_replay(replay_path):
        if isinstance(record, ReplayHeader):
            header = record
        elif isinstance(record, TickSnapshot):
            ticks.append(record)
        elif isinstance(record, MatchResult):
            result = record
    if header is None or not ticks or ticks[0].tick != 0:
        raise ValueError(f"{replay_path}: not a canonical replay (header and tick 0 required)")
    if header.ruleset_id is None:
        raise ValueError(f"{replay_path}: replay header carries no ruleset_id")
    policy = resolve_ruleset_policy(header.ruleset_id)
    if policy.scheduler_mode != "chunked":
        raise ValueError(f"{replay_path}: unsupported scheduler mode {policy.scheduler_mode!r}")
    hold = policy.capture_hold_ticks
    arena = header.config.arena_size

    seats = [agent.agent_id for agent in ticks[0].agents]
    seat_of = {agent_id: index for index, agent_id in enumerate(seats)}
    names = {
        str(entrant.get("agent_id")): entrant.get("name")
        for entrant in header.entrants
        if isinstance(entrant, Mapping)
    }

    owners: dict[int, str | None] = {}
    seeded: dict[str, list[int]] = {}
    for diff in ticks[0].memory_diffs:
        cells = _addresses(diff.address, diff.length, arena)
        for address in cells:
            owners[address] = diff.owner
        if diff.owner in seat_of:
            seeded.setdefault(diff.owner, []).extend(cells)
    # A core that wraps the arena end is seeded as more than one diff, so the
    # core is rebuilt from the recorded start address and checked against the
    # union of its seeding cells, independent of diff order.
    cores: dict[str, list[int]] = {}
    for agent in ticks[0].agents:
        cells = seeded.get(agent.agent_id, [])
        core = _addresses(agent.pc, len(cells), arena) if isinstance(agent.pc, int) else []
        if not cells or len(set(cells)) != len(cells) or set(core) != set(cells):
            raise ValueError(
                f"{replay_path}: seeded core of {agent.agent_id!r} is not the contiguous run "
                "starting at its recorded pc"
            )
        cores[agent.agent_id] = core

    entrants = {
        agent_id: EntrantCapture(
            agent_id=agent_id,
            name=names.get(agent_id),
            seat_index=seat_of[agent_id],
            core_base=cores[agent_id][0],
            core_size=len(cores[agent_id]),
        )
        for agent_id in seats
    }
    count = len(seats)
    streak = dict.fromkeys(seats, 0)
    capturer: dict[str, str | None] = dict.fromkeys(seats)
    alive_prev = {agent.agent_id: agent.alive for agent in ticks[0].agents}
    derived_completions: dict[int, list[tuple[str, str | None]]] = {}
    event_completions: dict[int, list[tuple[str, str | None, str]]] = {}
    termination_at: dict[str, tuple[int, str | None]] = {}

    def anchors_of(snapshot: TickSnapshot, agent_id: str) -> frozenset[int]:
        return frozenset(p.anchor for p in snapshot.processes if p.entrant_id == agent_id)

    boundaries = {agent_id: [anchors_of(ticks[0], agent_id)] for agent_id in seats}
    cpu = {agent_id: [0] for agent_id in seats}
    first_movers = [0]
    for agent_id in seats:
        entrants[agent_id].max_locations = len(boundaries[agent_id][0])

    for snapshot in ticks[1:]:
        tick = snapshot.tick
        first = first_mover_seat(tick, count, policy.scheduler_rotate_start)
        first_movers.append(first)
        before = {address: owners.get(address) for core in cores.values() for address in core}
        writes: list[tuple[int, str | None]] = []
        for diff in snapshot.memory_diffs:
            for address in _addresses(diff.address, diff.length, arena):
                writes.append((address, diff.owner))
                owners[address] = diff.owner
        for address, owner in writes:
            if owner in entrants:
                for other, core in cores.items():
                    if other != owner and address in core:
                        entrants[owner].enemy_core_writes += 1
        forfeited = {
            event.victim
            for event in snapshot.events
            if isinstance(event, RuntimeEvent) and event.event_type == "forfeit"
        }
        for event in snapshot.events:
            if isinstance(event, KillDeathEvent):
                event_completions.setdefault(tick, []).append(
                    (event.victim, event.killer, event.event_type)
                )

        for agent_id in seats:
            state = entrants[agent_id]
            if not alive_prev.get(agent_id, False) or agent_id in forfeited:
                continue
            state.evaluations += 1
            owned = sum(1 for address in cores[agent_id] if owners.get(address) == agent_id)
            opponent_first = first != state.seat_index
            if owned >= 1:
                if streak[agent_id] > 0:
                    state.recovery_ticks.append(tick)
                streak[agent_id] = 0
                capturer[agent_id] = None
                continue
            if streak[agent_id] == 0:
                capturer[agent_id] = _onset_capturer(agent_id, cores[agent_id], before, writes)
                state.onset_ticks.append(tick)
                state.onset_capturers.append(capturer[agent_id])
                if opponent_first:
                    state.onsets_opponent_first += 1
                else:
                    state.onsets_own_first += 1
            streak[agent_id] += 1
            state.max_streak = max(state.max_streak, streak[agent_id])
            state.zero_core_ticks.append(tick)
            if opponent_first:
                state.zero_ticks_opponent_first += 1
            else:
                state.zero_ticks_own_first += 1
            if streak[agent_id] >= hold:
                state.completion_tick = tick
                derived_completions.setdefault(tick, []).append((agent_id, capturer[agent_id]))

        for agent in snapshot.agents:
            if alive_prev.get(agent.agent_id, False) and not agent.alive:
                termination_at[agent.agent_id] = (tick, agent.termination_reason)
            cpu.setdefault(agent.agent_id, [0]).append(agent.cpu_used)
        alive_prev = {agent.agent_id: agent.alive for agent in snapshot.agents}
        for agent_id in seats:
            anchors = anchors_of(snapshot, agent_id)
            boundaries[agent_id].append(anchors)
            entrants[agent_id].max_locations = max(entrants[agent_id].max_locations, len(anchors))

    for agent_id in seats:
        state = entrants[agent_id]
        state.final_streak = streak[agent_id]
        state.alive_at_end = alive_prev.get(agent_id, False)
        state.termination = termination_at.get(agent_id, (None, None))[1]
        state.final_owned = sum(1 for address in cores[agent_id] if owners.get(address) == agent_id)
        if state.name in names_inferring_core and count == 2:
            enemy = seats[1 - state.seat_index]
            state.core_inference = _audit_inference(
                state.seat_index,
                cores[enemy][0],
                boundaries[enemy],
                cpu[agent_id],
                first_movers,
            )

    # Cross-check every derived completion against the replay's own record.
    mismatches: list[dict[str, Any]] = []
    captured_by_engine = {
        agent_id: tick for agent_id, (tick, reason) in termination_at.items() if reason == "core_captured"
    }
    derived_by_entrant = {
        victim: (tick, killer)
        for tick, rows in derived_completions.items()
        for victim, killer in rows
    }
    for agent_id in seats:
        derived = derived_by_entrant.get(agent_id)
        engine_tick = captured_by_engine.get(agent_id)
        if (derived[0] if derived else None) != engine_tick:
            mismatches.append(
                {"entrant": agent_id, "derived_completion": derived, "engine_capture_tick": engine_tick}
            )
    attributions: list[dict[str, Any]] = []
    for tick, rows in sorted(derived_completions.items()):
        events = {victim: (killer, kind) for victim, killer, kind in event_completions.get(tick, [])}
        for victim, derived_killer in rows:
            killer, kind = events.get(victim, (None, None))
            attributions.append(
                {
                    "victim": victim,
                    "tick": tick,
                    "event": kind,
                    "event_killer": killer,
                    "onset_capturer": derived_killer,
                    "attributed": kind == "kill" and killer is not None,
                    "matches_onset": killer == derived_killer,
                }
            )
            if kind is None:
                mismatches.append({"entrant": victim, "tick": tick, "problem": "no kill/death event"})

    winner = result.winner if result is not None else None
    winner_state = entrants.get(winner) if winner is not None else None
    return {
        "capture_analyzer_version": CAPTURE_ANALYZER_VERSION,
        "replay": str(replay_path),
        "ruleset_id": header.ruleset_id,
        "hold_ticks": hold,
        "scheduler_rotate_start": policy.scheduler_rotate_start,
        "arena_size": arena,
        "ticks": ticks[-1].tick,
        "winner": winner,
        "termination_reason": result.termination_reason if result is not None else None,
        "winner_at_zero_core": None if winner_state is None else winner_state.final_owned == 0,
        "completions": len(derived_by_entrant),
        "all_completions_attributed": all(row["attributed"] for row in attributions),
        "attribution_matches_onset": all(row["matches_onset"] for row in attributions),
        "attributions": attributions,
        "consistent_with_engine": not mismatches,
        "mismatches": mismatches,
        "entrants": {agent_id: entrants[agent_id].to_dict() for agent_id in seats},
    }


def main(argv: Sequence[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args:
        print("usage: python -m tools.research.v6.e2.capture_analyzer REPLAY [REPLAY ...]")
        return 2
    for path in args:
        print(json.dumps(analyze_replay(path), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
