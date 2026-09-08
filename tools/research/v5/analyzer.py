"""Deterministic Match and Corpus Analyzer for Bytefray V5 Research.

Consumes Replay Schema 4, result summaries, and optional trace.jsonl artifacts.
Extracts Layer A (outcomes), Layer B (process economy), and Layer C (strategic conversion)
metrics without modifying simulation execution or source replays.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from battle_engine.replay import (
    MatchResult,
    ReplayFormatError,
    ReplayHeader,
    TickSnapshot,
    iter_replay,
)


def _circular_dist(a: int, b: int, arena_size: int) -> int:
    d = abs(a - b)
    return min(d, arena_size - d)


@dataclass(frozen=True)
class MatchAnalysis:
    # Layer A: Outcomes
    match_id: str
    ruleset_id: str
    arena_size: int
    seed: int | None
    max_ticks: int
    actual_ticks: int
    winner: str
    win_mode: str
    result_reason: str
    is_timeout: bool
    is_tie: bool
    entrant_order: tuple[str, ...]
    agent_names: dict[str, str]
    final_scores: dict[str, float]
    territory_pct_final: dict[str, float]

    # Layer B: Process economy
    declared_process_count: dict[str, int]
    process_ids_by_entrant: dict[str, list[str]]
    total_disruptions_received: dict[str, int]
    total_disrupted_ticks: dict[str, int]
    distinct_disrupted_ticks: dict[str, int]
    max_displacement_from_core: dict[str, int]

    # Layer C: Strategic activity and conversion.
    #
    # R1 measurement-refinement note (docs/research/v5/
    # V5_R1_PROCESS_MORTALITY.md Section C): ``core_health_series``,
    # ``final_core_health``, ``core_damage_dealt``, and
    # ``core_damage_events`` are Phase 0's ORIGINAL activity-layer metrics,
    # kept byte-identical in name and computation for backward compatibility.
    # They count cumulative victim-to-attacker cell OWNERSHIP-FLIP EVENTS,
    # not true simultaneous ownership. Because they never increment back up
    # on repair, a single cell that is damaged and repaired repeatedly is
    # counted as repeated "damage" even though the victim's actual
    # simultaneous deficit returns to 0 after every repair -- exactly the
    # transient-vs-durable conflation R1 was chartered to resolve. Use
    # ``core_owned_cells_series``/``core_deficit_series`` and their derived
    # fields below for true durable-pressure analysis; treat the legacy
    # fields in this block as an *activity* signal only.
    core_base_by_entrant: dict[str, int]
    core_health_series: dict[str, list[int]]  # core health (0..8) per tick
    final_core_health: dict[str, int]
    core_damage_dealt: dict[str, int]  # cells damaged on enemy core
    core_damage_events: list[dict[str, Any]]
    time_to_first_core_damage: int | None
    max_no_progress_interval: int
    stagnation_ticks: int  # ticks in intervals >= 50 ticks with 0 core progress
    active_stagnation_ticks: int
    passive_stagnation_ticks: int
    total_combat_writes: dict[str, int]
    core_attack_writes: dict[str, int]
    anchor_blast_writes: dict[str, int]
    territory_combat_writes: dict[str, int]
    combat_conversion_rate: dict[str, float]
    progress_density_per_100t: dict[str, float]
    lead_changes: int

    # R1 State/Progress Layer: true simultaneous core ownership, reconstructed
    # from live cell-ownership state (a set that gains cells back on repair),
    # never a monotonic loss counter. ``core_owned_cells_series[e][t]`` is
    # exactly ``len({c in e's 8 core cells : vm.writer[c] == e})`` at tick
    # ``t``; ``core_deficit_series[e][t] == 8 - core_owned_cells_series[e][t]``.
    core_owned_cells_series: dict[str, list[int]]
    core_deficit_series: dict[str, list[int]]
    max_core_deficit: dict[str, int]
    final_core_deficit: dict[str, int]
    core_deficit_area: dict[str, int]  # sum of core deficit over ticks
    full_core_return_count: dict[str, int]  # returns to 8/8 after damage
    repair_latencies_ticks: dict[str, list[int]]  # ticks-to-full-repair, per repair completed
    longest_damaged_interval_ticks: dict[str, int]  # longest run with deficit > 0
    deficit_ever_reached_full: dict[str, bool]  # True iff owned_cells ever hit 0
    core_capture_outcome: dict[str, str]  # "captured" | "survived"

    # R1 Process Metrics Layer: derived from replay ``ProcessState.alive``
    # (V5 research Phase R1's additive per-tick field -- always ``True`` and
    # constant under every non-mortality Ruleset, so these fields degenerate
    # to "no deaths, no extinction" for every Phase 0 / stable-V4 match).
    live_process_count_series: dict[str, list[int]]
    process_deaths: dict[str, int]
    process_death_events: list[dict[str, Any]]  # [{tick, entrant_id, process_id}]
    process_extinction_tick: dict[str, int | None]
    mutual_process_extinction: bool
    entrant_zero_process_ticks: dict[str, int]
    entrant_ever_alive_with_zero_processes: dict[str, bool]
    ticks_first_process_death_to_own_core_capture: dict[str, int | None]
    ticks_full_extinction_to_own_core_capture: dict[str, int | None]

    # Trace Layer (Optional)
    trace_available: bool
    trace_applied_actions: dict[str, int]
    trace_rejected_out_of_reach: dict[str, int]
    trace_rejected_invalid: dict[str, int]
    trace_sensor_sightings: dict[str, int]
    trace_avg_latency_ms: dict[str, float]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def analyze_match(
    replay_path: Path,
    result_path: Path | None = None,
    trace_path: Path | None = None,
) -> dict[str, Any]:
    """Analyze one completed match from replay and optional trace artifacts."""
    if not replay_path.is_file():
        raise FileNotFoundError(f"Replay not found: {replay_path}")

    header: ReplayHeader | None = None
    terminal_result: MatchResult | None = None
    ticks: list[TickSnapshot] = []

    for item in iter_replay(replay_path):
        if isinstance(item, ReplayHeader):
            header = item
        elif isinstance(item, TickSnapshot):
            ticks.append(item)
        elif isinstance(item, MatchResult):
            terminal_result = item

    if header is None:
        raise ReplayFormatError(f"Replay missing header: {replay_path}")

    arena_size = header.config.arena_size
    ruleset_id = header.ruleset_id or "bytefray-rules-4"
    seed = header.config.seed

    # Read result.json if present
    result_data: dict[str, Any] = {}
    if result_path is not None and result_path.is_file():
        try:
            with open(result_path, "r", encoding="utf-8") as f:
                result_data = json.load(f)
        except Exception:
            result_data = {}
    elif replay_path.with_name("result.json").is_file():
        try:
            with open(replay_path.with_name("result.json"), "r", encoding="utf-8") as f:
                result_data = json.load(f)
        except Exception:
            result_data = {}

    # Extract entrant identities and core positions from tick 0
    if not ticks:
        raise ReplayFormatError(f"Replay contains no ticks: {replay_path}")

    tick0 = ticks[0]
    entrants: list[str] = [a.agent_id for a in tick0.agents]
    agent_names: dict[str, str] = {}
    core_base: dict[str, int] = {}
    core_cells: dict[str, set[int]] = {}

    # Populate names from result_data if available
    summary_agents = result_data.get("agents", [])
    if isinstance(summary_agents, list):
        for sa in summary_agents:
            if isinstance(sa, dict) and "id" in sa:
                agent_names[sa["id"]] = sa.get("name", sa["id"])

    for a in tick0.agents:
        if a.agent_id not in agent_names:
            agent_names[a.agent_id] = a.agent_id
        start_addr = a.region[0] if a.region is not None else (a.pc if isinstance(a.pc, int) else 0)
        core_base[a.agent_id] = start_addr
        core_cells[a.agent_id] = {(start_addr + i) % arena_size for i in range(8)}

    # Trace processes at tick 0
    process_ids: dict[str, list[str]] = {e: [] for e in entrants}
    declared_count: dict[str, int] = {e: 0 for e in entrants}
    for p in tick0.processes:
        if p.entrant_id in process_ids:
            process_ids[p.entrant_id].append(p.process_id)
            declared_count[p.entrant_id] += 1

    # Disruption and process metrics
    disruptions_received: dict[str, int] = {e: 0 for e in entrants}
    disrupted_ticks_total: dict[str, int] = {e: 0 for e in entrants}
    distinct_disrupted_ticks_set: dict[str, set[int]] = {e: set() for e in entrants}
    max_displacement: dict[str, int] = {e: 0 for e in entrants}

    # Core health tracking: initially 8 for each entrant
    core_health_series: dict[str, list[int]] = {e: [8] for e in entrants}
    current_health: dict[str, int] = {e: 8 for e in entrants}
    core_damage_events: list[dict[str, Any]] = []
    core_damage_dealt: dict[str, int] = {e: 0 for e in entrants}

    total_combat_writes: dict[str, int] = {e: 0 for e in entrants}
    core_attack_writes: dict[str, int] = {e: 0 for e in entrants}
    anchor_blast_writes: dict[str, int] = {e: 0 for e in entrants}
    territory_combat_writes: dict[str, int] = {e: 0 for e in entrants}

    # Track cell owners for territory combat detection
    cell_owners: dict[int, str] = {}
    for e in entrants:
        for c in core_cells[e]:
            cell_owners[c] = e

    time_to_first_damage: int | None = None
    no_progress_streak = 0
    max_no_progress = 0
    stagnation_ticks = 0
    active_stagnation_ticks = 0
    passive_stagnation_ticks = 0
    lead_changes = 0
    prev_leader: str | None = None

    # Track process anchor locations per tick
    prev_disrupted_status: dict[tuple[str, str], bool] = {}

    # R1 State/Progress Layer: true simultaneous ownership, re-derived from
    # ``cell_owners`` (already the ground truth end-of-tick ownership map)
    # every tick rather than accumulated as a one-way loss counter, so a
    # repaired cell is reflected as owned again the very tick it is
    # reclaimed. See MatchAnalysis's field docstring for why this differs
    # from the legacy ``core_health_series``.
    core_owned_cells_series: dict[str, list[int]] = {e: [8] for e in entrants}
    core_deficit_series: dict[str, list[int]] = {e: [0] for e in entrants}
    max_core_deficit: dict[str, int] = {e: 0 for e in entrants}
    core_deficit_area: dict[str, int] = {e: 0 for e in entrants}
    full_core_return_count: dict[str, int] = {e: 0 for e in entrants}
    repair_latencies_ticks: dict[str, list[int]] = {e: [] for e in entrants}
    longest_damaged_interval_ticks: dict[str, int] = {e: 0 for e in entrants}
    current_damaged_run: dict[str, int] = {e: 0 for e in entrants}
    deficit_ever_reached_full: dict[str, bool] = {e: False for e in entrants}
    own_core_captured_tick: dict[str, int | None] = {e: None for e in entrants}

    # R1 Process Metrics Layer: derived from ``ProcessState.alive`` per tick.
    live_process_count_series: dict[str, list[int]] = {
        e: [declared_count[e]] for e in entrants
    }
    process_deaths: dict[str, int] = {e: 0 for e in entrants}
    process_death_events: list[dict[str, Any]] = []
    process_extinction_tick: dict[str, int | None] = {e: None for e in entrants}
    entrant_zero_process_ticks: dict[str, int] = {e: 0 for e in entrants}
    first_process_death_tick: dict[str, int | None] = {e: None for e in entrants}
    prev_process_alive: dict[tuple[str, str], bool] = {
        (p.entrant_id, p.process_id): True
        for p in tick0.processes
        if p.entrant_id in entrants
    }

    # R1 fix: true ownership must expand each diff's full [address, address
    # + length) run, not just its start address, otherwise a repair/capture
    # folded into the middle of a same-tick merged run-length diff (see
    # ``replay.MemoryDiff.length``) is silently missed. The legacy
    # ``cell_owners`` dict above is deliberately left untouched by this fix
    # (it drives ``core_health_series``/``core_damage_dealt``, which must
    # stay byte-identical to Phase 0's published computation for
    # continuity); this is a separate, correctly range-aware ownership map
    # used only by the new true-ownership fields below.
    true_cell_owners: dict[int, str] = dict(cell_owners)

    for t_idx, snap in enumerate(ticks[1:], start=1):
        tick_num = snap.tick
        damage_this_tick = False
        combat_writes_this_tick = 0

        # Update process anchor displacements and disruptions
        current_anchors_by_cell: dict[int, list[tuple[str, str]]] = defaultdict(list)
        for p in snap.processes:
            e_id = p.entrant_id
            if e_id in entrants and p.anchor is not None:
                current_anchors_by_cell[p.anchor].append((e_id, p.process_id))
                base = core_base.get(e_id, 0)
                disp = _circular_dist(p.anchor, base, arena_size)
                max_displacement[e_id] = max(max_displacement[e_id], disp)

            if p.disrupted:
                disrupted_ticks_total[e_id] += 1
                distinct_disrupted_ticks_set[e_id].add(tick_num)
                # Count new disruption transition
                prev_st = prev_disrupted_status.get((e_id, p.process_id), False)
                if not prev_st:
                    disruptions_received[e_id] += 1
            prev_disrupted_status[(e_id, p.process_id)] = p.disrupted

        # Analyze memory diffs for combat and core progress
        for diff in snap.memory_diffs:
            addr = diff.address
            writer = diff.owner
            if not writer or writer not in entrants:
                continue

            old_owner = cell_owners.get(addr)
            cell_owners[addr] = writer
            for offset in range(max(1, diff.length)):
                true_cell_owners[(addr + offset) % arena_size] = writer

            # Check if targeting enemy core
            for victim in entrants:
                if victim == writer:
                    continue
                if addr in core_cells[victim]:
                    core_attack_writes[writer] += 1
                    total_combat_writes[writer] += 1
                    combat_writes_this_tick += 1
                    if old_owner == victim:
                        # Core damage dealt!
                        current_health[victim] = max(0, current_health[victim] - 1)
                        core_damage_dealt[writer] += 1
                        damage_this_tick = True
                        if time_to_first_damage is None:
                            time_to_first_damage = tick_num
                        core_damage_events.append({
                            "tick": tick_num,
                            "attacker": writer,
                            "victim": victim,
                            "address": addr,
                            "new_health": current_health[victim],
                        })
                elif old_owner and old_owner != writer:
                    # Overwriting enemy territory
                    territory_combat_writes[writer] += 1
                    total_combat_writes[writer] += 1
                    combat_writes_this_tick += 1

            # Check if targeting enemy anchor cell (anchor blast / disruption attempt)
            for (anc_eid, anc_pid) in current_anchors_by_cell.get(addr, []):
                if anc_eid != writer:
                    anchor_blast_writes[writer] += 1
                    total_combat_writes[writer] += 1
                    combat_writes_this_tick += 1

        for e in entrants:
            core_health_series[e].append(current_health[e])

        # R1 State/Progress Layer: true simultaneous ownership, re-derived
        # from ``cell_owners`` (already updated above for every diff this
        # tick, including an owner's own repair write) rather than
        # accumulated as a one-way loss counter.
        for e in entrants:
            owned_now = sum(1 for c in core_cells[e] if true_cell_owners.get(c) == e)
            core_owned_cells_series[e].append(owned_now)
            deficit = 8 - owned_now
            core_deficit_series[e].append(deficit)
            max_core_deficit[e] = max(max_core_deficit[e], deficit)
            core_deficit_area[e] += deficit
            if owned_now == 0:
                deficit_ever_reached_full[e] = True
                if own_core_captured_tick[e] is None:
                    own_core_captured_tick[e] = tick_num
            if deficit > 0:
                current_damaged_run[e] += 1
                longest_damaged_interval_ticks[e] = max(
                    longest_damaged_interval_ticks[e], current_damaged_run[e]
                )
            else:
                if current_damaged_run[e] > 0:
                    repair_latencies_ticks[e].append(current_damaged_run[e])
                    full_core_return_count[e] += 1
                current_damaged_run[e] = 0

        # R1 Process Metrics Layer: live count and death-transition detection.
        live_count_this_tick: dict[str, int] = {e: 0 for e in entrants}
        for p in snap.processes:
            e_id = p.entrant_id
            if e_id not in entrants:
                continue
            if p.alive:
                live_count_this_tick[e_id] += 1
            key = (e_id, p.process_id)
            was_alive = prev_process_alive.get(key, True)
            if was_alive and not p.alive:
                process_deaths[e_id] += 1
                process_death_events.append(
                    {"tick": tick_num, "entrant_id": e_id, "process_id": p.process_id}
                )
                if first_process_death_tick[e_id] is None:
                    first_process_death_tick[e_id] = tick_num
            prev_process_alive[key] = p.alive
        for e in entrants:
            live_process_count_series[e].append(live_count_this_tick[e])
            if live_count_this_tick[e] == 0 and process_extinction_tick[e] is None:
                process_extinction_tick[e] = tick_num
            entrant_alive_this_tick = next(
                (a.alive for a in snap.agents if a.agent_id == e), True
            )
            if entrant_alive_this_tick and live_count_this_tick[e] == 0:
                entrant_zero_process_ticks[e] += 1

        if damage_this_tick:
            no_progress_streak = 0
        else:
            no_progress_streak += 1
            max_no_progress = max(max_no_progress, no_progress_streak)
            if no_progress_streak >= 50:
                stagnation_ticks += 1
                if combat_writes_this_tick > 0:
                    active_stagnation_ticks += 1
                else:
                    passive_stagnation_ticks += 1

        # Track lead changes in core damage
        scores_damage = [core_damage_dealt[e] for e in entrants]
        if max(scores_damage) > 0 and len(entrants) == 2:
            current_leader = entrants[0] if scores_damage[0] > scores_damage[1] else (entrants[1] if scores_damage[1] > scores_damage[0] else None)
            if current_leader and prev_leader and current_leader != prev_leader:
                lead_changes += 1
            if current_leader:
                prev_leader = current_leader

    actual_ticks = len(ticks) - 1
    max_ticks = header.config.arena_size if header.config.instr_per_tick == 0 else 1000
    if result_data.get("ticks") is not None:
        actual_ticks = int(result_data["ticks"])

    # Winner and reason from result_data or terminal_result
    winner = "tie"
    win_mode = header.config.win_mode
    reason = "tick_limit"
    if terminal_result is not None:
        winner = terminal_result.winner
        reason = getattr(terminal_result, "reason", "tick_limit") or "tick_limit"
    if result_data:
        winner = result_data.get("winner", winner)
        reason = result_data.get("termination_reason", result_data.get("reason", reason))

    is_timeout = (reason == "tick_limit")
    is_tie = (winner == "tie" or not winner)

    # Scores
    final_scores: dict[str, float] = {}
    if terminal_result is not None and terminal_result.score:
        final_scores = {k: float(v) for k, v in terminal_result.score.items()}
    elif "score" in result_data and isinstance(result_data["score"], dict):
        final_scores = {k: float(v) for k, v in result_data["score"].items()}
    else:
        last_snap = ticks[-1]
        final_scores = {k: float(v) for k, v in last_snap.score.items()}

    # Territory pct
    territory_pct: dict[str, float] = {}
    for sa in summary_agents:
        if isinstance(sa, dict) and "id" in sa:
            territory_pct[sa["id"]] = float(sa.get("territory_pct_last", 0.0))

    # Derived rates
    combat_conv_rate: dict[str, float] = {}
    prog_density: dict[str, float] = {}
    for e in entrants:
        cw = total_combat_writes[e]
        cd = core_damage_dealt[e]
        combat_conv_rate[e] = round(cd / max(1, cw), 4)
        prog_density[e] = round(cd / max(1.0, actual_ticks / 100.0), 3)

    # R1 State/Progress and Process Metrics: final/derived aggregates.
    final_core_deficit: dict[str, int] = {e: core_deficit_series[e][-1] for e in entrants}
    core_capture_outcome: dict[str, str] = {
        e: ("captured" if core_owned_cells_series[e][-1] == 0 else "survived") for e in entrants
    }
    mutual_process_extinction = bool(entrants) and all(
        process_extinction_tick[e] is not None for e in entrants
    )
    entrant_ever_alive_with_zero_processes: dict[str, bool] = {
        e: entrant_zero_process_ticks[e] > 0 for e in entrants
    }
    ticks_first_process_death_to_own_core_capture: dict[str, int | None] = {}
    ticks_full_extinction_to_own_core_capture: dict[str, int | None] = {}
    for e in entrants:
        captured_tick = own_core_captured_tick[e]
        death_tick = first_process_death_tick[e]
        extinction_tick = process_extinction_tick[e]
        ticks_first_process_death_to_own_core_capture[e] = (
            captured_tick - death_tick
            if captured_tick is not None and death_tick is not None and captured_tick >= death_tick
            else None
        )
        ticks_full_extinction_to_own_core_capture[e] = (
            captured_tick - extinction_tick
            if captured_tick is not None
            and extinction_tick is not None
            and captured_tick >= extinction_tick
            else None
        )

    # Optional Trace Analysis
    trace_applied: dict[str, int] = {e: 0 for e in entrants}
    trace_rejected_reach: dict[str, int] = {e: 0 for e in entrants}
    trace_rejected_inv: dict[str, int] = {e: 0 for e in entrants}
    trace_sensor_sightings: dict[str, int] = {e: 0 for e in entrants}
    trace_latencies: dict[str, list[float]] = {e: [] for e in entrants}
    trace_found = False

    effective_trace = trace_path or replay_path.with_name("trace.jsonl")
    if effective_trace.is_file():
        try:
            with open(effective_trace, "r", encoding="utf-8") as tf:
                for line in tf:
                    if not line.strip():
                        continue
                    rec = json.loads(line)
                    agent_id = rec.get("agent_id")
                    if agent_id not in entrants:
                        continue
                    trace_found = True
                    applied_res = rec.get("applied_result") or {}
                    st = applied_res.get("status")
                    if st == "APPLIED":
                        trace_applied[agent_id] += 1
                    elif st == "REJECTED_OUT_OF_REACH":
                        trace_rejected_reach[agent_id] += 1
                    elif st in ("REJECTED_INVALID", "EXCEPTION"):
                        trace_rejected_inv[agent_id] += 1

                    obs = rec.get("observation") or {}
                    vis = obs.get("visible_enemy_anchor_addresses", [])
                    if vis:
                        trace_sensor_sightings[agent_id] += 1

                    wall_time = rec.get("wall_time_ms")
                    if wall_time is not None:
                        trace_latencies[agent_id].append(float(wall_time))
        except Exception:
            trace_found = False

    trace_avg_latency = {
        e: (round(sum(trace_latencies[e]) / len(trace_latencies[e]), 3) if trace_latencies[e] else 0.0)
        for e in entrants
    }

    analysis = MatchAnalysis(
        match_id=result_data.get("match_id", replay_path.stem),
        ruleset_id=ruleset_id,
        arena_size=arena_size,
        seed=seed,
        max_ticks=max_ticks,
        actual_ticks=actual_ticks,
        winner=winner,
        win_mode=win_mode,
        result_reason=reason,
        is_timeout=is_timeout,
        is_tie=is_tie,
        entrant_order=tuple(entrants),
        agent_names=agent_names,
        final_scores=final_scores,
        territory_pct_final=territory_pct,
        declared_process_count=declared_count,
        process_ids_by_entrant=process_ids,
        total_disruptions_received=disruptions_received,
        total_disrupted_ticks=disrupted_ticks_total,
        distinct_disrupted_ticks={e: len(s) for e, s in distinct_disrupted_ticks_set.items()},
        max_displacement_from_core=max_displacement,
        core_base_by_entrant=core_base,
        core_health_series=core_health_series,
        final_core_health={e: current_health[e] for e in entrants},
        core_damage_dealt=core_damage_dealt,
        core_damage_events=core_damage_events,
        time_to_first_core_damage=time_to_first_damage,
        max_no_progress_interval=max_no_progress,
        stagnation_ticks=stagnation_ticks,
        active_stagnation_ticks=active_stagnation_ticks,
        passive_stagnation_ticks=passive_stagnation_ticks,
        total_combat_writes=total_combat_writes,
        core_attack_writes=core_attack_writes,
        anchor_blast_writes=anchor_blast_writes,
        territory_combat_writes=territory_combat_writes,
        combat_conversion_rate=combat_conv_rate,
        progress_density_per_100t=prog_density,
        lead_changes=lead_changes,
        core_owned_cells_series=core_owned_cells_series,
        core_deficit_series=core_deficit_series,
        max_core_deficit=max_core_deficit,
        final_core_deficit=final_core_deficit,
        core_deficit_area=core_deficit_area,
        full_core_return_count=full_core_return_count,
        repair_latencies_ticks=repair_latencies_ticks,
        longest_damaged_interval_ticks=longest_damaged_interval_ticks,
        deficit_ever_reached_full=deficit_ever_reached_full,
        core_capture_outcome=core_capture_outcome,
        live_process_count_series=live_process_count_series,
        process_deaths=process_deaths,
        process_death_events=process_death_events,
        process_extinction_tick=process_extinction_tick,
        mutual_process_extinction=mutual_process_extinction,
        entrant_zero_process_ticks=entrant_zero_process_ticks,
        entrant_ever_alive_with_zero_processes=entrant_ever_alive_with_zero_processes,
        ticks_first_process_death_to_own_core_capture=ticks_first_process_death_to_own_core_capture,
        ticks_full_extinction_to_own_core_capture=ticks_full_extinction_to_own_core_capture,
        trace_available=trace_found,
        trace_applied_actions=trace_applied,
        trace_rejected_out_of_reach=trace_rejected_reach,
        trace_rejected_invalid=trace_rejected_inv,
        trace_sensor_sightings=trace_sensor_sightings,
        trace_avg_latency_ms=trace_avg_latency,
    )
    return analysis.to_dict()


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze Bytefray V4/V5 replay and trace.")
    parser.add_argument("replay", type=Path, help="Path to replay.jsonl")
    parser.add_argument("--result", type=Path, default=None, help="Path to result.json (optional)")
    parser.add_argument("--trace", type=Path, default=None, help="Path to trace.jsonl (optional)")
    parser.add_argument("--json", action="store_true", help="Output machine-readable JSON")
    args = parser.parse_args()

    metrics = analyze_match(args.replay, args.result, args.trace)
    if args.json:
        print(json.dumps(metrics, indent=2, sort_keys=True))
    else:
        print(f"Match: {metrics['match_id']} | Winner: {metrics['winner']} ({metrics['result_reason']}) | Ticks: {metrics['actual_ticks']}")
        print(f"Entrants: {metrics['entrant_order']}")
        print(f"Core Health Final: {metrics['final_core_health']}")
        print(f"Core Damage Dealt: {metrics['core_damage_dealt']}")
        print(f"Combat Writes: {metrics['total_combat_writes']}")
        print(f"Conversion Rate: {metrics['combat_conversion_rate']}")
        print(f"Stagnation Ticks: {metrics['stagnation_ticks']} (active: {metrics['active_stagnation_ticks']}, passive: {metrics['passive_stagnation_ticks']})")


if __name__ == "__main__":
    main()
