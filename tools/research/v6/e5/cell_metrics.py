"""Replay-derived E5 per-cell metrics: directed base parity (BP) and the
decoupling-gate quantities.

docs/research/v6/V6_E5_DESIGN_REVIEW_REVISION_1.md Sec R2 (E5-D) and Sec R5
(O-BP). Reads one canonical replay -- never writes it and needs no new replay
field -- together with that cell's E3 telemetry and E4 metrics, and derives:

* **BP, directed base parity** (O-BP, Sec R5.2). For victim seat ``v``,
  ``o_v(t)`` is 1 iff ``v`` owns its own core cell 0 (the cell at its recorded
  ``pc``, never its anchor) after tick ``t``'s writes -- the instant capture
  evaluation reads. ``P_A``/``P_B`` are the both-alive ticks (every entrant
  alive in the tick-``t`` snapshot: E4 ``cell_metrics``'s rule, unchanged)
  whose first mover is Seat A / Seat B. With at least ``MIN_TICKS_PER_PARITY``
  (E4's 10) of each, the cell is DEFINED and, in exact fractions,

      BP_A = mean(o_A over P_B) - mean(o_A over P_A)
      BP_B = mean(o_B over P_A) - mean(o_B over P_B)

  (positive favours the victim's second-mover role); otherwise it is
  DECIDED_EARLY. Ticks are never pooled across cells.
* **The E5-D quantities** (Sec R2). D-1: every tick-0 anchor's offset from
  its entrant's ``pc``. D-2: hostile writes to the tick-0 anchor of a victim
  process that has not moved at any earlier tick boundary *and* to a cell of
  that victim's core. D-3 (DUAL): hostile writes to a cell of a live victim's
  core that is also that victim process's anchor at the tick's start or end
  boundary -- a MOVE is atomic, so the two boundary anchors contain every
  position the process held during the tick and D-3 is a conservative
  superset of the true DUAL count. D-4: tick boundaries at which a process sits
  on its own entrant's core. Per directed pair, D-5's input: D-2-type writes by
  the attacker to the victim's cell 0.
* **Mechanism description** (review Sec J): anchor hits on unmoved processes,
  hits in a tick in which the victim moved (ambiguous), hostile core-0 writes,
  the attacker's per-tick coverage of the victim's core, and the first tick of
  hostile core or anchor contact.

Everything the reconstruction shares with E4 is cross-checked: the both-alive
ticks by first mover must equal E4 ``cell_metrics``'s, and each entrant's final
own-core count must equal capture analyzer v2's. A disagreement is reported,
never smoothed over. No reused analyzer is copied or modified.
"""

from __future__ import annotations

from collections.abc import Mapping
from fractions import Fraction
from pathlib import Path
from typing import Any

from battle_engine.replay import ReplayHeader, TickSnapshot, iter_replay
from battle_engine.ruleset_policy import resolve_ruleset_policy

from tools.research.v6.e2.capture_analyzer import _addresses, first_mover_seat
from tools.research.v6.e4.cell_metrics import MIN_TICKS_PER_PARITY, exact_text

E5_CELL_METRICS_VERSION = 1

DEFINED = "DEFINED"
DECIDED_EARLY = "DECIDED_EARLY"


def _fraction_text(value: Fraction | None) -> str | None:
    return None if value is None else exact_text(value)


def parity_value(owned_second: int, second: int, owned_first: int, first: int) -> Fraction:
    """O-BP for one victim: its base-ownership share on the ticks it moves second
    minus its share on the ticks it moves first (exact)."""
    return Fraction(owned_second, second) - Fraction(owned_first, first)


def cell_metrics(replay_path: Path | str, e3: Mapping[str, Any], e4: Mapping[str, Any]) -> dict[str, Any]:
    """E5 metrics for one two-entrant replay, cross-checked against its E3
    telemetry ``e3`` and its E4 metrics ``e4``."""
    replay_path = Path(replay_path)
    header: ReplayHeader | None = None
    ticks: list[TickSnapshot] = []
    for record in iter_replay(replay_path):
        if isinstance(record, ReplayHeader):
            header = record
        elif isinstance(record, TickSnapshot):
            ticks.append(record)
    if header is None or not ticks or ticks[0].tick != 0 or header.ruleset_id is None:
        raise ValueError(f"{replay_path}: not a canonical replay (header with ruleset_id and tick 0 required)")
    policy = resolve_ruleset_policy(header.ruleset_id)
    arena = header.config.arena_size
    seats = [agent.agent_id for agent in ticks[0].agents]
    if len(seats) != 2:
        raise ValueError(f"{replay_path}: E5 metrics need exactly two entrants, found {len(seats)}")
    other = {seats[0]: seats[1], seats[1]: seats[0]}

    # Cores: the tick-0 seeding diffs, as the contiguous run at each recorded pc
    # (E4 cell_metrics's rule). Core cell 0 is the cell at pc.
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
    core_sets = {seat: set(cells) for seat, cells in cores.items()}
    base = {seat: cells[0] for seat, cells in cores.items()}

    # D-1: tick-0 anchors and their offsets from pc.
    spawn: dict[tuple[str, str], int] = {(p.entrant_id, p.process_id): p.anchor for p in ticks[0].processes}
    spawn_offsets = sorted({(anchor - base[entrant]) % arena for (entrant, _), anchor in spawn.items()})
    unmoved: dict[tuple[str, str], bool] = dict.fromkeys(spawn, True)

    def own_core_occupancy(snapshot: TickSnapshot) -> int:
        return sum(1 for p in snapshot.processes if p.anchor in core_sets[p.entrant_id])

    occupancy = own_core_occupancy(ticks[0])
    both_alive = [0, 0]  # by first-mover seat index, as E4
    # base_owned[seat][first_index]: ticks of that parity at whose end ``seat`` owns its base.
    base_owned = {seat: [0, 0] for seat in seats}
    dual = default_dual = 0
    per_pair: dict[str, dict[str, int]] = {
        f"{x}->{other[x]}": {"unmoved_anchor_hits": 0, "ambiguous_anchor_hits": 0, "core0_writes": 0,
                             "default_anchor_core0_writes": 0, "dual_writes": 0}
        for x in seats
    }
    coverage: dict[str, list[int]] = {f"{x}->{other[x]}": [0, 0] for x in seats}  # [sum, both-alive ticks]
    first_contact: dict[str, int | None] = {f"{x}->{other[x]}": None for x in seats}
    alive_prev = {agent.agent_id: agent.alive for agent in ticks[0].agents}
    anchors_prev = {(p.entrant_id, p.process_id): p.anchor for p in ticks[0].processes}

    for snapshot in ticks[1:]:
        tick = snapshot.tick
        first = first_mover_seat(tick, len(seats), policy.scheduler_rotate_start)
        anchors_now = {(p.entrant_id, p.process_id): p.anchor for p in snapshot.processes}
        written: dict[str, set[int]] = {seat: set() for seat in seats}
        for diff in snapshot.memory_diffs:
            for address in _addresses(diff.address, diff.length, arena):
                owners[address] = diff.owner
                writer = diff.owner
                if writer not in other:
                    continue
                victim = other[writer]
                pair = f"{writer}->{victim}"
                if not alive_prev.get(victim, False):
                    continue
                in_core = address in core_sets[victim]
                if in_core:
                    written[writer].add(address)
                if address == base[victim]:
                    per_pair[pair]["core0_writes"] += 1
                hit_dual = hit_default = False
                for key, before in anchors_prev.items():
                    if key[0] != victim:
                        continue
                    after = anchors_now.get(key, before)
                    if address not in (before, after):
                        continue
                    if before == after:
                        if unmoved[key]:
                            per_pair[pair]["unmoved_anchor_hits"] += 1
                    else:
                        per_pair[pair]["ambiguous_anchor_hits"] += 1
                    if in_core:
                        hit_dual = True
                        if unmoved[key] and address == spawn[key] == before:
                            hit_default = True
                if hit_dual:
                    dual += 1
                    per_pair[pair]["dual_writes"] += 1
                if hit_default:
                    default_dual += 1
                    if address == base[victim]:
                        per_pair[pair]["default_anchor_core0_writes"] += 1
                if first_contact[pair] is None and (in_core or hit_dual or any(
                        address in (anchors_prev[k], anchors_now.get(k, anchors_prev[k]))
                        for k in anchors_prev if k[0] == victim)):
                    first_contact[pair] = tick
        alive = {agent.agent_id: agent.alive for agent in snapshot.agents}
        if all(alive.get(seat, False) for seat in seats):
            both_alive[first] += 1
            for seat in seats:
                if owners.get(base[seat]) == seat:
                    base_owned[seat][first] += 1
            for writer in seats:
                pair = f"{writer}->{other[writer]}"
                coverage[pair][0] += len(written[writer])
                coverage[pair][1] += 1
        occupancy += own_core_occupancy(snapshot)
        for key, anchor in anchors_now.items():
            if anchor != spawn.get(key):
                unmoved[key] = False
        anchors_prev = anchors_now
        alive_prev = alive

    index = {seat: i for i, seat in enumerate(seats)}
    defined = both_alive[0] >= MIN_TICKS_PER_PARITY and both_alive[1] >= MIN_TICKS_PER_PARITY
    bp: dict[str, dict[str, Any]] = {}
    for seat in seats:
        own, opp = index[seat], 1 - index[seat]
        if defined:
            # The victim moves second on the ticks whose first mover is the other seat.
            value = parity_value(base_owned[seat][opp], both_alive[opp], base_owned[seat][own], both_alive[own])
            bp[seat] = {"status": DEFINED, "exact": exact_text(value), "value": round(float(value), 9)}
        else:
            bp[seat] = {"status": DECIDED_EARLY, "exact": None, "value": None}
        bp[seat]["base_owned_by_first_mover"] = {seats[0]: base_owned[seat][0], seats[1]: base_owned[seat][1]}

    problems: list[str] = []
    e4_both_alive = e4.get("both_alive_ticks_by_first_mover") or {}
    if e4_both_alive != {seats[0]: both_alive[0], seats[1]: both_alive[1]}:
        problems.append(f"both-alive ticks {both_alive} != E4 {e4_both_alive}")
    for seat in seats:
        final_owned = sum(1 for address in cores[seat] if owners.get(address) == seat)
        if e3["seats"][seat]["capture"]["final_owned"] != final_owned:
            problems.append(f"{seat}: final owned {final_owned} != capture analyzer v2")
    spawn_mode = ("core_base" if spawn_offsets == [0] else "before_core" if spawn_offsets == [arena - 1]
                  else "other")
    return {
        "e5_cell_metrics_version": E5_CELL_METRICS_VERSION,
        "ruleset_id": header.ruleset_id,
        "initial_anchor_placement": policy.initial_anchor_placement,
        "core_base": base,
        "bp": bp,
        "both_alive_ticks_by_first_mover": {seats[0]: both_alive[0], seats[1]: both_alive[1]},
        "d_gate": {
            "spawn_offsets": spawn_offsets,
            "spawn_mode": spawn_mode,
            "default_dual_writes": default_dual,
            "dual_writes": dual,
            "own_core_occupancy": occupancy,
        },
        "directed": {
            pair: {
                **counts,
                "coverage_mean": _fraction_text(
                    Fraction(coverage[pair][0], coverage[pair][1]) if coverage[pair][1] else None),
                "first_contact_tick": first_contact[pair],
            }
            for pair, counts in per_pair.items()
        },
        "checks": {"reconstruction_agrees": not problems, "problems": problems, "ok": not problems},
    }
