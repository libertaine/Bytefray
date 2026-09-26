"""Replay-derived E3 action and parity telemetry (design review Sec K).

Reads one canonical replay and its ``result.json`` -- never writes either and
needs no new replay field -- and derives, for a two-entrant match:

* **MC-1, executed actions.** Each tick snapshot's per-entrant ``cpu_used``
  is the number of actions the entrant executed in that tick. Every entrant
  alive at the end of the previous tick is offered ``Q`` actions (the
  header's ``instr_per_tick``) and is the tick's first or second mover by
  the Ruleset's chunked scheduler with start rotation (seat ``(t - 1) mod 2``
  moves first). The sum of ``cpu_used`` must equal ``result.json``
  ``statistics.cpu_total``; a mismatch is reported, never smoothed over.
* **Lost offers and exposure.** An entrant that was offered actions in a
  tick and did not forfeit in it lost ``Q - executed`` offers. For entrants
  whose processes all have positive shares that is exactly the offers lost
  to disruption (review Sec C). A match is *exposed* if some entrant lost an
  offer in some tick.
* **MC-2, Action Denial Fraction.** ``(Q - executed) / Q`` for an entrant
  alive at the end of the tick that did not forfeit in it, kept separately
  for first and second movers.
* **G.4 manipulation check.** Entrant-ticks, alive throughout and without a
  forfeit, that executed fewer than 5 actions as first mover or fewer than 4
  as second mover; zero-action ticks of such entrants; exclusive ticks (both
  entrants alive at the end of the tick, one executed nothing). These hold
  by construction under ``disruption_slot_limit = 1``: they are gates, not
  findings.
* **PM-1, two-sided parity dependence.** Core balance ``b(t)`` is Seat A's
  owned own-core cells minus Seat B's at the end of tick ``t``, from the
  replay's ownership. A *swing tick* is a tick at whose end both entrants are
  alive and ``b(t) != b(t - 1)``; it favours the tick's first mover when the
  change is in the first mover's direction. ``FMS`` is the share of swing
  ticks that favour the first mover, scored only with at least 10 swing
  ticks (otherwise ``NOT_SCOREABLE``, reported, never dropped), and
  ``PD = |2 FMS - 1|`` with its direction kept.
* **PM-2, capture phase-lock.** Taken unchanged from the frozen E2 capture
  analyzer (version 2), per entrant, with an explicit category: an entrant
  with no zero-core evaluation is ``NO_ZERO_CORE_TICKS`` -- never a
  phase-lock of 0 -- otherwise ``PHASE_LOCK_AVAILABLE`` with the two-sided
  reading ``|2 PL - 1|`` and its direction.
* **First disruptive hit.** The first tick in which any process carries the
  replay's ``disrupted`` flag ("hit during this tick"), for the treatment
  prefix gate.

Capture telemetry itself is never re-derived here: onsets, recoveries,
completions and phase-lock come from ``capture_analyzer.analyze_replay``,
which is imported unchanged. The core balance needs per-tick ownership, which
the capture analyzer does not expose, so it is rebuilt from the same replay
records with the capture analyzer's own address helper and then
cross-checked against it: every entrant's zero-core evaluation ticks and
final owned count must equal the capture analyzer's, or the replay is
reported as a capture-analyzer disagreement.

Research-only; imports no runtime internals beyond the replay reader and the
Ruleset registry.
"""

from __future__ import annotations

import json
import sys
from collections.abc import Collection, Mapping, Sequence
from pathlib import Path
from typing import Any

from battle_engine.replay import (
    MatchResult,
    ReplayHeader,
    RuntimeEvent,
    TickSnapshot,
    iter_replay,
)
from battle_engine.ruleset_policy import resolve_ruleset_policy

from tools.research.v6.e2.capture_analyzer import (
    CAPTURE_ANALYZER_VERSION,
    _addresses,
    analyze_replay,
    first_mover_seat,
)

E3_ACTION_PARITY_VERSION = 1

# PM-1 (review Sec K): FMS is scored only with at least this many swing ticks.
MIN_SCOREABLE_SWINGS = 10
# Review Sec J threshold rationale: PD >= 0.9 is strong parity dependence
# ("at most 5% of swings go against the dominant parity"), PD <= 0.5 weak.
STRONG_PD = 0.9
WEAK_PD = 0.5
# Review Sec G.4 (lambda = 1, Q = 8, chunk 2, two entrants, positive shares).
G4_FIRST_MOVER_MIN = 5
G4_SECOND_MOVER_MIN = 4

NOT_SCOREABLE = "NOT_SCOREABLE"
NO_ZERO_CORE_TICKS = "NO_ZERO_CORE_TICKS"
PHASE_LOCK_AVAILABLE = "PHASE_LOCK_AVAILABLE"
FIRST = "first"
SECOND = "second"
ROLES = (FIRST, SECOND)


def parity_direction(fms: float | None, pd: float | None) -> str:
    """The PM-1 direction label of one scored match."""
    if fms is None or pd is None:
        return "not_scoreable"
    if pd <= WEAK_PD:
        return "neutral_weak"
    lean = "first_mover" if fms > 0.5 else "last_mover"
    return f"{lean}_dominated" if pd >= STRONG_PD else f"{lean}_leaning"


def parity_score(swings: int, favouring_first: int) -> dict[str, Any]:
    """PM-1 for one match from its swing count and first-mover-favouring swings."""
    if swings < MIN_SCOREABLE_SWINGS:
        return {
            "swing_ticks": swings,
            "first_mover_favoring": favouring_first,
            "scoreable": False,
            "status": NOT_SCOREABLE,
            "fms": None,
            "pd": None,
            "direction": parity_direction(None, None),
        }
    fms = round(favouring_first / swings, 6)
    pd = round(abs(2 * fms - 1), 6)
    return {
        "swing_ticks": swings,
        "first_mover_favoring": favouring_first,
        "scoreable": True,
        "status": "SCORED",
        "fms": fms,
        "pd": pd,
        "direction": parity_direction(fms, pd),
    }


def phase_lock_reading(entrant: Mapping[str, Any]) -> dict[str, Any]:
    """PM-2 for one entrant of a capture-analyzer record."""
    zero = int(entrant["zero_core_evaluations"])
    if zero == 0:
        return {"category": NO_ZERO_CORE_TICKS, "zero_core_evaluations": 0, "phase_lock": None,
                "two_sided": None, "direction": None}
    lock = float(entrant["phase_lock"])
    return {
        "category": PHASE_LOCK_AVAILABLE,
        "zero_core_evaluations": zero,
        "phase_lock": lock,
        "two_sided": round(abs(2 * lock - 1), 6),
        "direction": "opponent_first" if lock > 0.5 else "own_first" if lock < 0.5 else "balanced",
    }


def _role_summary() -> dict[str, Any]:
    return {"entrant_ticks": 0, "offered": 0, "executed": 0, "histogram": [0] * 9,
            "min_executed_alive_throughout": None, "adf_n": 0, "adf_sum": 0.0}


def _load_result(path: Path) -> dict[str, Any]:
    data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return data


def analyze_actions(
    replay_path: Path | str,
    result_path: Path | str | None = None,
    *,
    names_inferring_core: Collection[str] = (),
) -> dict[str, Any]:
    """E3 action and parity telemetry for one two-entrant replay."""
    replay_path = Path(replay_path)
    result_file = Path(result_path) if result_path is not None else replay_path.with_name("result.json")
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
    arena = header.config.arena_size
    quota = int(header.config.instr_per_tick)
    seats = [agent.agent_id for agent in ticks[0].agents]
    if len(seats) != 2:
        raise ValueError(f"{replay_path}: E3 telemetry needs exactly two entrants, found {len(seats)}")
    names = {
        str(entrant.get("agent_id")): entrant.get("name")
        for entrant in header.entrants
        if isinstance(entrant, Mapping)
    }

    # Cores: rebuilt as the capture analyzer does (tick-0 seeding diffs, the
    # contiguous run from each entrant's recorded pc), then cross-checked.
    owners: dict[int, str | None] = {}
    seeded: dict[str, list[int]] = {}
    for diff in ticks[0].memory_diffs:
        cells = _addresses(diff.address, diff.length, arena)
        for address in cells:
            owners[address] = diff.owner
        if diff.owner in seats:
            seeded.setdefault(diff.owner, []).extend(cells)
    cores: dict[str, list[int]] = {}
    for agent in ticks[0].agents:
        cells = seeded.get(agent.agent_id, [])
        core = _addresses(agent.pc, len(cells), arena) if isinstance(agent.pc, int) else []
        if not cells or set(core) != set(cells) or len(set(cells)) != len(cells):
            raise ValueError(f"{replay_path}: seeded core of {agent.agent_id!r} is not the contiguous run at its pc")
        cores[agent.agent_id] = core

    def owned(agent_id: str) -> int:
        return sum(1 for address in cores[agent_id] if owners.get(address) == agent_id)

    roles = {seat: {role: _role_summary() for role in ROLES} for seat in seats}
    cpu_total = dict.fromkeys(seats, 0)
    zero_action_live = dict.fromkeys(seats, 0)
    g4_violations = dict.fromkeys(seats, 0)
    lost_offers = dict.fromkeys(seats, 0)
    zero_ticks: dict[str, list[int]] = {seat: [] for seat in seats}
    alive_prev = {agent.agent_id: agent.alive for agent in ticks[0].agents}
    balance_prev = owned(seats[0]) - owned(seats[1])
    both_alive = exclusive = swings = favouring_first = 0
    lost_offer_ticks = hit_ticks = 0
    first_lost_offer_tick: int | None = None
    first_hit_tick: int | None = None

    for snapshot in ticks[1:]:
        tick = snapshot.tick
        first = first_mover_seat(tick, len(seats), policy.scheduler_rotate_start)
        for diff in snapshot.memory_diffs:
            for address in _addresses(diff.address, diff.length, arena):
                owners[address] = diff.owner
        alive = {agent.agent_id: agent.alive for agent in snapshot.agents}
        cpu = {agent.agent_id: int(agent.cpu_used) for agent in snapshot.agents}
        forfeited = {
            event.victim
            for event in snapshot.events
            if isinstance(event, RuntimeEvent) and event.event_type == "forfeit"
        }
        if any(process.disrupted for process in snapshot.processes):
            hit_ticks += 1
            if first_hit_tick is None:
                first_hit_tick = tick
        tick_lost = False
        for index, seat in enumerate(seats):
            cpu_total[seat] += cpu.get(seat, 0)
            if not alive_prev.get(seat, False) or seat in forfeited:
                continue
            executed = cpu.get(seat, 0)
            lost = quota - executed
            if lost < 0:
                raise ValueError(f"{replay_path}: {seat} executed {executed} > Q={quota} at tick {tick}")
            if owned(seat) == 0:
                zero_ticks[seat].append(tick)
            if lost:
                lost_offers[seat] += lost
                tick_lost = True
            summary = roles[seat][FIRST if index == first else SECOND]
            summary["entrant_ticks"] += 1
            summary["offered"] += quota
            summary["executed"] += executed
            if alive.get(seat, False):
                summary["histogram"][min(executed, 8)] += 1
                summary["adf_n"] += 1
                summary["adf_sum"] += lost / quota
                floor = summary["min_executed_alive_throughout"]
                summary["min_executed_alive_throughout"] = executed if floor is None else min(floor, executed)
                if executed == 0:
                    zero_action_live[seat] += 1
                if executed < (G4_FIRST_MOVER_MIN if index == first else G4_SECOND_MOVER_MIN):
                    g4_violations[seat] += 1
        if tick_lost:
            lost_offer_ticks += 1
            if first_lost_offer_tick is None:
                first_lost_offer_tick = tick
        balance = owned(seats[0]) - owned(seats[1])
        if all(alive.get(seat, False) for seat in seats):
            both_alive += 1
            if any(cpu.get(seat, 0) == 0 for seat in seats):
                exclusive += 1
            change = balance - balance_prev
            if change:
                swings += 1
                if (change > 0) == (first == 0):
                    favouring_first += 1
        balance_prev = balance
        alive_prev = alive

    capture = analyze_replay(replay_path, names_inferring_core=names_inferring_core)
    problems: list[str] = []
    result_json = _load_result(result_file)
    statistics = {
        str(entrant.get("agent_id")): (entrant.get("statistics") or {}).get("cpu_total")
        for entrant in result_json.get("entrants") or ()
        if isinstance(entrant, Mapping)
    }
    cpu_match = all(statistics.get(seat) == cpu_total[seat] for seat in seats)
    if not cpu_match:
        problems.append(f"sum of cpu_used {cpu_total} != result.json cpu_total {statistics}")
    reconstruction_agrees = True
    for seat in seats:
        entrant = capture["entrants"][seat]
        if list(entrant["zero_core_ticks"]) != zero_ticks[seat] or int(entrant["final_owned"]) != owned(seat):
            reconstruction_agrees = False
            problems.append(f"{seat}: ownership reconstruction disagrees with capture analyzer v2")
    if not capture["consistent_with_engine"]:
        problems.append("capture analyzer v2 disagrees with the engine's capture record")
    attribution_ok = bool(capture["all_completions_attributed"] and capture["attribution_matches_onset"])
    if not attribution_ok:
        problems.append("capture analyzer v2 attribution mismatch")

    seat_rows: dict[str, Any] = {}
    for index, seat in enumerate(seats):
        entrant = capture["entrants"][seat]
        seat_rows[seat] = {
            "name": names.get(seat),
            "seat_index": index,
            "cpu_total_replay": cpu_total[seat],
            "cpu_total_result": statistics.get(seat),
            "roles": roles[seat],
            "zero_action_live_ticks": zero_action_live[seat],
            "g4_violations": g4_violations[seat],
            "lost_offers": lost_offers[seat],
            "phase_lock": phase_lock_reading(entrant),
            "capture": {
                "onsets": entrant["onsets"],
                "recoveries": entrant["recoveries"],
                "completions": entrant["completions"],
                "completion_tick": entrant["completion_tick"],
                "max_streak": entrant["max_streak"],
                "zero_ticks_opponent_first": entrant["zero_ticks_opponent_first"],
                "zero_ticks_own_first": entrant["zero_ticks_own_first"],
                "final_owned": entrant["final_owned"],
                "termination": entrant["termination"],
                "max_locations": entrant["max_locations"],
                "core_inference": entrant["core_inference"],
            },
        }
    return {
        "e3_action_parity_version": E3_ACTION_PARITY_VERSION,
        "capture_analyzer_version": CAPTURE_ANALYZER_VERSION,
        "replay": str(replay_path),
        "ruleset_id": header.ruleset_id,
        "disruption_slot_limit": policy.disruption_slot_limit,
        "hold_ticks": policy.capture_hold_ticks,
        "scheduler_rotate_start": policy.scheduler_rotate_start,
        "quota": quota,
        "ticks": ticks[-1].tick,
        "winner": result.winner if result is not None else None,
        "termination_reason": result.termination_reason if result is not None else None,
        "seats": seat_rows,
        "both_alive_ticks": both_alive,
        "exclusive_ticks": exclusive,
        "exposed": first_lost_offer_tick is not None,
        "first_lost_offer_tick": first_lost_offer_tick,
        "lost_offer_ticks": lost_offer_ticks,
        "first_hit_tick": first_hit_tick,
        "hit_ticks": hit_ticks,
        "parity": parity_score(swings, favouring_first),
        "completions": [
            {"victim": row["victim"], "victim_name": names.get(row["victim"]), "tick": row["tick"],
             "capturer": row["onset_capturer"]}
            for row in capture["attributions"]
        ],
        "winner_at_zero_core": capture["winner_at_zero_core"],
        "checks": {
            "cpu_statistics_match": cpu_match,
            "capture_reconstruction_agrees": reconstruction_agrees,
            "capture_consistent_with_engine": bool(capture["consistent_with_engine"]),
            "capture_attribution_ok": attribution_ok,
            "problems": problems,
            "ok": not problems,
        },
    }


def main(argv: Sequence[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args:
        print("usage: python -m tools.research.v6.e3.action_parity REPLAY [REPLAY ...]")
        return 2
    for path in args:
        print(json.dumps(analyze_actions(path), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
