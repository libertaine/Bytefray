"""V6 Phase 4B raw arena-scaling study -- post-hoc analysis.

Reads the evaluation artifacts ``phase4b_corpus_runner.py`` already wrote
(``runs/research_v6_phase4b/{equivalence,sweep}/...``) and computes the
aggregate/pairwise/interaction/transitivity/action-density metrics
docs/research/v6/V6_PHASE4B_ARENA_SCALING_STUDY.md reports.

Research-only, isolated from gameplay runtime, deterministic: reads
already-written artifacts, executes nothing, never mutates a result.

Tier 1 metrics (outcome, score, territory, kills/deaths, ticks, termination
reason) are read directly from each cell's persisted ``result.json``. Tier 2
metrics are derived from each match's own ``replay.jsonl`` by a single
forward pass per match:

  * ``first_contact_tick`` -- earliest tick at which any pair of opposing
    processes' anchors are within their combined reach (the exact inverse
    of the Phase 4A "Disjoint Non-Interaction" stagnation criterion).
  * ``first_hostile_write_tick`` -- earliest tick a WRITE changes a cell's
    owner away from a *different* entrant's prior ownership (a full
    linear ownership reconstruction, replaying memory_diffs in order, not
    a single-field lookup -- Phase 4A.1's own feasibility note).
  * ``unique_addresses_written`` per entrant -- distinct addresses that
    entrant's writes ever touched.
  * ``max_zero_mutation_run`` -- longest consecutive-tick run with no
    memory_diffs at all, and whether it reaches the Phase 4A formal
    stagnation window (W=100).

Circular displacement, spatial dispersion, and periodic-loop detection are
NOT computed by this pass (out of scope for this session's time budget);
the study document says so explicitly rather than presenting partial Tier 2
coverage as complete.
"""

from __future__ import annotations

import json
import math
import statistics
from collections import defaultdict
from itertools import combinations
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
RUNS_ROOT = REPO_ROOT / "runs" / "research_v6_phase4b"

STAGNATION_WINDOW = 100  # Phase 4A Sec 7.2's W
DOMINANCE_THRESHOLD = 0.55  # Phase 4A Sec 8.2's practical (non-statistical) cut


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _iter_replay_lines(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        for raw in handle:
            raw = raw.strip()
            if raw:
                yield json.loads(raw)


def _circular_distance(a: int, b: int, arena_size: int) -> int:
    delta = abs(a - b) % arena_size
    return min(delta, arena_size - delta)


def analyze_replay_tier2(replay_path: Path, arena_size: int) -> dict[str, Any]:
    first_contact_tick: int | None = None
    first_hostile_write_tick: int | None = None
    unique_addresses: dict[str, set[int]] = defaultdict(set)
    cell_owner: dict[int, str] = {}
    zero_run = 0
    max_zero_run = 0
    tick_count = 0

    lines = _iter_replay_lines(replay_path)
    next(lines)  # header

    for record in lines:
        if record.get("record_type") != "tick":
            continue  # terminal MatchResult record
        tick = record["tick"]
        tick_count += 1
        diffs = record.get("memory_diffs") or []

        if diffs:
            zero_run = 0
        else:
            zero_run += 1
            max_zero_run = max(max_zero_run, zero_run)

        for diff in diffs:
            owner = diff.get("owner")
            if owner is None:
                continue
            addr = diff["address"]
            length = diff["length"]
            addresses = [(addr + offset) % arena_size for offset in range(length)]
            unique_addresses[owner].update(addresses)
            for address in addresses:
                previous = cell_owner.get(address)
                if previous is not None and previous != owner and first_hostile_write_tick is None:
                    first_hostile_write_tick = tick
                cell_owner[address] = owner

        if first_contact_tick is None:
            processes = record.get("processes") or []
            by_entrant: dict[str, list[tuple[int, int]]] = defaultdict(list)
            for proc in processes:
                by_entrant[proc["entrant_id"]].append((proc["anchor"], proc["reach"]))
            entrants = list(by_entrant)
            for e_a, e_b in combinations(entrants, 2):
                found = False
                for anchor_a, reach_a in by_entrant[e_a]:
                    for anchor_b, reach_b in by_entrant[e_b]:
                        if _circular_distance(anchor_a, anchor_b, arena_size) <= reach_a + reach_b:
                            found = True
                            break
                    if found:
                        break
                if found:
                    first_contact_tick = tick
                    break

    max_zero_run = max(max_zero_run, zero_run)
    return {
        "first_contact_tick": first_contact_tick,
        "first_hostile_write_tick": first_hostile_write_tick,
        "unique_addresses_written": {k: len(v) for k, v in unique_addresses.items()},
        "max_zero_mutation_run": max_zero_run,
        "reached_formal_stagnation_window": max_zero_run >= STAGNATION_WINDOW,
        "replay_tick_count": tick_count,
    }


def load_condition_cells(root: Path, *, with_tier2: bool) -> list[dict[str, Any]]:
    """Every completed cell under one round-robin condition directory, with
    its Tier 1 result fields (and, if requested, Tier 2 replay-derived
    fields) attached."""

    cells: list[dict[str, Any]] = []
    for request_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        evaluation = _load_json(request_dir / "evaluation.json")
        arena_size = evaluation["effective_conditions"]["arena_size"]
        for cell in evaluation["cells"]:
            if cell["status"] != "completed":
                continue
            match_dir = request_dir / cell["artifact_dir"]
            result = _load_json(match_dir / "result.json")
            record = {
                "subject_id": cell["subject_id"],
                "opponent_id": cell["opponent_id"],
                "seed": cell["seed"],
                "orientation": cell["orientation"],
                "outcome": cell["outcome"],
                "ticks_run": cell["ticks_run"],
                "score_subject": cell["score_subject"],
                "score_opponent": cell["score_opponent"],
                "territory_subject": cell["territory_subject"],
                "territory_opponent": cell["territory_opponent"],
                "termination_reason": result["termination_reason"],
                "winner": result["winner"],
                "arena_size": arena_size,
                "entrants": result["entrants"],
            }
            if with_tier2:
                record["tier2"] = analyze_replay_tier2(match_dir / "replay.jsonl", arena_size)
            cells.append(record)
    return cells


# ---------------------------------------------------------------------------
# Aggregate / pairwise / transitivity analysis
# ---------------------------------------------------------------------------


def pairwise_win_rates(cells: list[dict[str, Any]], field: list[str]) -> dict[tuple[str, str], float]:
    """win_rate[(i, j)] = i's win rate against j, pooled over seed+orientation."""

    wins: dict[tuple[str, str], int] = defaultdict(int)
    totals: dict[tuple[str, str], int] = defaultdict(int)
    for cell in cells:
        a, b = cell["subject_id"], cell["opponent_id"]
        outcome = cell["outcome"]
        if outcome not in ("win", "loss", "tie"):
            continue
        totals[(a, b)] += 1
        totals[(b, a)] += 1
        if outcome == "win":
            wins[(a, b)] += 1
        elif outcome == "loss":
            wins[(b, a)] += 1
        else:
            wins[(a, b)] += 0.5
            wins[(b, a)] += 0.5
    rates: dict[tuple[str, str], float] = {}
    for i in field:
        for j in field:
            if i == j:
                continue
            total = totals.get((i, j), 0)
            rates[(i, j)] = wins.get((i, j), 0) / total if total else float("nan")
    return rates


def aggregate_ordering(cells: list[dict[str, Any]], field: list[str]) -> list[tuple[str, float, int]]:
    wins: dict[str, float] = defaultdict(float)
    matches: dict[str, int] = defaultdict(int)
    for cell in cells:
        a, b = cell["subject_id"], cell["opponent_id"]
        outcome = cell["outcome"]
        if outcome not in ("win", "loss", "tie"):
            continue
        matches[a] += 1
        matches[b] += 1
        if outcome == "win":
            wins[a] += 1
        elif outcome == "loss":
            wins[b] += 1
        else:
            wins[a] += 0.5
            wins[b] += 0.5
    ordering = [
        (agent, (wins[agent] / matches[agent] if matches[agent] else 0.0), matches[agent])
        for agent in field
    ]
    ordering.sort(key=lambda row: row[1], reverse=True)
    return ordering


def dominance_edges(rates: dict[tuple[str, str], float], field: list[str]) -> list[tuple[str, str]]:
    edges = []
    for i in field:
        for j in field:
            if i == j:
                continue
            r = rates.get((i, j), float("nan"))
            if not math.isnan(r) and r > DOMINANCE_THRESHOLD:
                edges.append((i, j))
    return edges


def count_directed_3_cycles(edges: list[tuple[str, str]]) -> int:
    edge_set = set(edges)
    count = 0
    nodes = sorted({n for edge in edges for n in edge})
    for i, j, k in combinations(nodes, 3):
        for a, b, c in ((i, j, k), (i, k, j), (j, i, k)):
            forward = (a, b) in edge_set and (b, c) in edge_set and (c, a) in edge_set
            backward = (a, c) in edge_set and (c, b) in edge_set and (b, a) in edge_set
            if forward or backward:
                count += 1
                break
    return count


def opponent_conditioned_variance(rates: dict[tuple[str, str], float], field: list[str]) -> dict[str, float]:
    out = {}
    for agent in field:
        values = [
            rates[(agent, opp)]
            for opp in field
            if opp != agent and not math.isnan(rates[(agent, opp)])
        ]
        out[agent] = statistics.pvariance(values) if len(values) > 1 else 0.0
    return out


def spearman_rho(rank_a: dict[str, int], rank_b: dict[str, int], field: list[str]) -> float:
    n = len(field)
    if n < 2:
        return float("nan")
    d2 = sum((rank_a[a] - rank_b[a]) ** 2 for a in field)
    return 1 - (6 * d2) / (n * (n**2 - 1))


def action_density(arena_size: int, instr_per_tick: int = 8, ticks: int = 1000) -> float:
    return (instr_per_tick * ticks) / arena_size


def summarize_condition(cells: list[dict[str, Any]], field: list[str], arena_size: int) -> dict[str, Any]:
    rates = pairwise_win_rates(cells, field)
    ordering = aggregate_ordering(cells, field)
    edges = dominance_edges(rates, field)
    cycles = count_directed_3_cycles(edges)
    variance = opponent_conditioned_variance(rates, field)

    ticks_list = [c["ticks_run"] for c in cells]
    timeouts = sum(1 for c in cells if c["termination_reason"] == "tick_limit")
    wins = sum(1 for c in cells if c["outcome"] == "win")
    losses = sum(1 for c in cells if c["outcome"] == "loss")
    ties = sum(1 for c in cells if c["outcome"] == "tie")
    termination_breakdown: dict[str, int] = defaultdict(int)
    for c in cells:
        termination_breakdown[c["termination_reason"]] += 1

    tier2_present = cells and "tier2" in cells[0]
    tier2_summary = None
    if tier2_present:
        contact_ticks = [c["tier2"]["first_contact_tick"] for c in cells if c["tier2"]["first_contact_tick"] is not None]
        never_contact = sum(1 for c in cells if c["tier2"]["first_contact_tick"] is None)
        hostile_ticks = [
            c["tier2"]["first_hostile_write_tick"] for c in cells if c["tier2"]["first_hostile_write_tick"] is not None
        ]
        stagnated = sum(1 for c in cells if c["tier2"]["reached_formal_stagnation_window"])
        tier2_summary = {
            "mean_first_contact_tick": statistics.fmean(contact_ticks) if contact_ticks else None,
            "median_first_contact_tick": statistics.median(contact_ticks) if contact_ticks else None,
            "matches_never_in_contact": never_contact,
            "matches_never_in_contact_rate": never_contact / len(cells) if cells else None,
            "mean_first_hostile_write_tick": statistics.fmean(hostile_ticks) if hostile_ticks else None,
            "matches_with_no_hostile_write": len(cells) - len(hostile_ticks),
            "matches_reaching_formal_stagnation_window": stagnated,
            "stagnation_rate": stagnated / len(cells) if cells else None,
        }

    return {
        "arena_size": arena_size,
        "action_density_S": action_density(arena_size),
        "matches": len(cells),
        "wins": wins,
        "losses": losses,
        "ties": ties,
        "timeouts": timeouts,
        "timeout_rate": timeouts / len(cells) if cells else None,
        "mean_ticks_run": statistics.fmean(ticks_list) if ticks_list else None,
        "median_ticks_run": statistics.median(ticks_list) if ticks_list else None,
        "termination_breakdown": dict(termination_breakdown),
        "ordering": [{"agent": a, "win_rate": w, "matches": m} for a, w, m in ordering],
        "pairwise_win_rates": {f"{i}_vs_{j}": r for (i, j), r in rates.items()},
        "dominance_edges": [f"{i}->{j}" for i, j in edges],
        "directed_3_cycles": cycles,
        "opponent_conditioned_variance": variance,
        "tier2": tier2_summary,
    }


FIELD = (
    "Octave",
    "nemesis_alpha2",
    "v5_scout_striker",
    "v5_region_attacker",
    "v5_dual_team",
    "v4_claimer",
    "v5_core_defender",
    "v4_local_defender",
)


def main() -> int:
    conditions = {
        512: RUNS_ROOT / "equivalence" / "research-scale",
        1024: RUNS_ROOT / "sweep" / "a1024",
        4096: RUNS_ROOT / "sweep" / "a4096",
        16384: RUNS_ROOT / "sweep" / "a16384",
        65536: RUNS_ROOT / "sweep" / "a65536",
    }

    summaries: dict[int, dict[str, Any]] = {}
    for arena_size, root in conditions.items():
        print(f"analyzing arena={arena_size} ...")
        cells = load_condition_cells(root, with_tier2=True)
        summaries[arena_size] = summarize_condition(cells, list(FIELD), arena_size)

    # Rank comparison against A=512.
    base_rank = {row["agent"]: i for i, row in enumerate(summaries[512]["ordering"])}
    for arena_size, summary in summaries.items():
        rank = {row["agent"]: i for i, row in enumerate(summary["ordering"])}
        summary["spearman_rho_vs_a512"] = spearman_rho(base_rank, rank, list(FIELD))

    out_path = RUNS_ROOT / "phase4b_analysis.json"
    out_path.write_text(json.dumps(summaries, indent=2, default=str), encoding="utf-8")
    print(f"written: {out_path}")

    for arena_size, summary in summaries.items():
        print(f"\n=== arena {arena_size} (S={summary['action_density_S']:.4f}) ===")
        print(f"  matches={summary['matches']} timeouts={summary['timeouts']} ({summary['timeout_rate']:.1%})")
        print(f"  mean_ticks={summary['mean_ticks_run']:.1f} median_ticks={summary['median_ticks_run']}")
        print(f"  3-cycles={summary['directed_3_cycles']} dominance_edges={len(summary['dominance_edges'])}")
        print(f"  spearman_rho_vs_a512={summary['spearman_rho_vs_a512']:.3f}")
        print("  ranking:", ", ".join(f"{r['agent']}={r['win_rate']:.2f}" for r in summary["ordering"]))
        if summary["tier2"]:
            t2 = summary["tier2"]
            print(
                f"  tier2: mean_first_contact={t2['mean_first_contact_tick']} "
                f"never_contact_rate={t2['matches_never_in_contact_rate']:.1%} "
                f"stagnation_rate={t2['stagnation_rate']:.1%}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
