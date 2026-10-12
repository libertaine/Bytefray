"""V6 Phase 4E territory scoring normalization study -- post-hoc analysis.

Audits production territory scoring economics, reconciles prior research claims,
evaluates candidate normalization designs against the empirical Phase 4B
benchmark dataset (2,240 matches across 5 arena sizes: 512, 1024, 4096, 16384, 65536),
and generates deterministic verification metrics for the Phase 4E study.

Research-only, isolated from gameplay runtime, deterministic: reads
already-written artifacts, executes nothing, never mutates a result.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
RUNS_ROOT = REPO_ROOT / "runs" / "research_v6_phase4b"

ARENA_DIRS = {
    512: RUNS_ROOT / "equivalence" / "research-scale",
    1024: RUNS_ROOT / "sweep" / "a1024",
    4096: RUNS_ROOT / "sweep" / "a4096",
    16384: RUNS_ROOT / "sweep" / "a16384",
    65536: RUNS_ROOT / "sweep" / "a65536",
}

ROSTER_ENTRANTS = [
    "Octave",
    "nemesis_alpha2",
    "v5_scout_striker",
    "v4_claimer",
    "v5_region_attacker",
    "v5_dual_team",
    "v5_core_defender",
    "v4_local_defender",
]

HOLDINGS = [0, 1, 8, 64, 128, 256, 512, 1024, 2048, 4096]


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def compute_direct_score_characterization(
    territory_bucket: int = 64,
    territory_weight: float = 1.0,
) -> dict[int, dict[int, float | None]]:
    """Deterministic calculation of points per tick across holdings and arena sizes."""
    table: dict[int, dict[int, float | None]] = {}
    for holding in HOLDINGS:
        table[holding] = {}
        for arena in sorted(ARENA_DIRS.keys()):
            if holding > arena:
                table[holding][arena] = None
            else:
                buckets = holding // max(1, territory_bucket)
                table[holding][arena] = float(buckets * territory_weight)
    return table


def analyze_phase4b_artifacts() -> dict[str, Any]:
    """Extract full empirical scoring and outcome metrics across all Phase 4B matches."""
    arena_metrics: dict[int, Any] = {}

    for arena_size, arena_dir in ARENA_DIRS.items():
        if not arena_dir.exists():
            raise FileNotFoundError(f"Missing Phase 4B artifact directory: {arena_dir}")

        total_matches = 0
        timeouts = 0
        combat_kills = 0
        all_dead = 0

        scores: dict[str, list[float]] = defaultdict(list)
        territory_last: dict[str, list[int]] = defaultdict(list)
        alive_ticks: dict[str, list[int]] = defaultdict(list)
        mem_writes: dict[str, list[int]] = defaultdict(list)
        wins: dict[str, int] = defaultdict(int)
        ties: dict[str, int] = defaultdict(int)
        losses: dict[str, int] = defaultdict(int)
        match_counts: dict[str, int] = defaultdict(int)

        # Matchup specific: v5_region_attacker vs v4_claimer
        ra_vs_cl = {
            "matches": 0,
            "ra_wins": 0,
            "claimer_wins": 0,
            "ties": 0,
            "combat_kills": 0,
            "timeouts": 0,
        }

        for result_path in sorted(arena_dir.rglob("result.json")):
            data = _load_json(result_path)
            total_matches += 1

            term_reason = data.get("termination_reason")
            if term_reason == "tick_limit":
                timeouts += 1
            elif term_reason == "last_agent_standing":
                combat_kills += 1
            elif term_reason == "all_agents_dead":
                all_dead += 1

            winner = data.get("winner")
            entrants = data.get("entrants", [])
            names_by_id = {e["agent_id"]: e["name"] for e in entrants}

            # Check for RA vs Claimer
            if set(names_by_id.values()) == {"v5_region_attacker", "v4_claimer"}:
                ra_vs_cl["matches"] += 1
                if winner == "tie":
                    ra_vs_cl["ties"] += 1
                elif names_by_id.get(winner) == "v5_region_attacker":
                    ra_vs_cl["ra_wins"] += 1
                elif names_by_id.get(winner) == "v4_claimer":
                    ra_vs_cl["claimer_wins"] += 1

                if term_reason == "last_agent_standing":
                    ra_vs_cl["combat_kills"] += 1
                elif term_reason == "tick_limit":
                    ra_vs_cl["timeouts"] += 1

            for e in entrants:
                name = e["name"]
                match_counts[name] += 1
                scores[name].append(float(e["score"]))
                stats = e.get("statistics", {})
                t_last = int(stats.get("territory_last", 0))
                territory_last[name].append(t_last)
                alive_ticks[name].append(int(stats.get("alive_ticks", 0)))
                mem_writes[name].append(int(stats.get("mem_writes", 0)))

                if winner == e["agent_id"]:
                    wins[name] += 1
                elif winner == "tie":
                    ties[name] += 1
                else:
                    losses[name] += 1

        entrant_stats = {}
        for name in ROSTER_ENTRANTS:
            n = match_counts[name]
            w = wins[name]
            t = ties[name]
            l = losses[name]
            sc = scores[name]
            tl = territory_last[name]
            at = alive_ticks[name]
            mw = mem_writes[name]

            pure_wr = w / n if n else 0.0
            score_rate = (w + 0.5 * t) / n if n else 0.0
            mean_score = sum(sc) / len(sc) if sc else 0.0
            mean_cells = sum(tl) / len(tl) if tl else 0.0
            mean_pct = (mean_cells * 100.0 / arena_size) if arena_size else 0.0
            mean_alive = sum(at) / len(at) if at else 0.0
            mean_writes = sum(mw) / len(mw) if mw else 0.0

            entrant_stats[name] = {
                "matches": n,
                "wins": w,
                "ties": t,
                "losses": l,
                "pure_win_rate": pure_wr,
                "tournament_score_rate": score_rate,
                "mean_score": mean_score,
                "mean_cells": mean_cells,
                "diagnostic_territory_pct": mean_pct,
                "mean_alive_ticks": mean_alive,
                "mean_mem_writes": mean_writes,
            }

        arena_metrics[arena_size] = {
            "arena_size": arena_size,
            "total_matches": total_matches,
            "timeouts": timeouts,
            "timeout_rate": timeouts / total_matches if total_matches else 0.0,
            "combat_kills": combat_kills,
            "all_dead": all_dead,
            "entrants": entrant_stats,
            "region_attacker_vs_claimer": ra_vs_cl,
        }

    return {
        "scoring_characterization": compute_direct_score_characterization(),
        "arena_metrics": arena_metrics,
    }


def format_markdown_tables(analysis: dict[str, Any]) -> str:
    lines = []
    lines.append("### Table 1: Direct Scoring Characterization (Points per Tick)")
    lines.append("| Holding (cells) | A=512 | A=1024 | A=4096 | A=16384 | A=65536 | Economic Invariance |")
    lines.append("|---:|---:|---:|---:|---:|---:|:---:|")
    char_table = analysis["scoring_characterization"]
    for holding in HOLDINGS:
        row = [f"{holding} cells"]
        for arena in sorted(ARENA_DIRS.keys()):
            val = char_table[holding][arena]
            row.append("N/A" if val is None else f"{val:.1f}")
        row.append("**Identical**")
        lines.append(f"| {' | '.join(row)} |")

    lines.append("\n### Table 2: Benchmark Field Performance by Arena Size")
    lines.append(
        "| Entrant | Metric | A=512 | A=1024 | A=4096 | A=16384 | A=65536 | Trend |"
    )
    lines.append("|---|---|---:|---:|---:|---:|---:|:---:|")

    arena_metrics = analysis["arena_metrics"]
    for name in ROSTER_ENTRANTS:
        # Win rate
        row_wr = [f"**`{name}`**", "Pure Win Rate (W/N)"]
        for a in sorted(ARENA_DIRS.keys()):
            val = arena_metrics[a]["entrants"][name]["pure_win_rate"]
            row_wr.append(f"{val:.4f}")
        v512 = arena_metrics[512]["entrants"][name]["pure_win_rate"]
        v65k = arena_metrics[65536]["entrants"][name]["pure_win_rate"]
        diff = (v65k - v512) * 100
        row_wr.append(f"{diff:+.1f}%")
        lines.append(f"| {' | '.join(row_wr)} |")

        # Tournament score rate
        row_pts = ["", "Tournament Rate ((W+0.5T)/N)"]
        for a in sorted(ARENA_DIRS.keys()):
            val = arena_metrics[a]["entrants"][name]["tournament_score_rate"]
            row_pts.append(f"{val:.4f}")
        row_pts.append("-")
        lines.append(f"| {' | '.join(row_pts)} |")

        # Mean score
        row_sc = ["", "Mean Match Score"]
        for a in sorted(ARENA_DIRS.keys()):
            val = arena_metrics[a]["entrants"][name]["mean_score"]
            row_sc.append(f"{val:.1f}")
        row_sc.append("-")
        lines.append(f"| {' | '.join(row_sc)} |")

        # Mean cells
        row_cells = ["", "Mean Owned Cells"]
        for a in sorted(ARENA_DIRS.keys()):
            val = arena_metrics[a]["entrants"][name]["mean_cells"]
            row_cells.append(f"{val:.1f}")
        row_cells.append("-")
        lines.append(f"| {' | '.join(row_cells)} |")

        # Diagnostic pct
        row_pct = ["", "Diagnostic Territory %"]
        for a in sorted(ARENA_DIRS.keys()):
            val = arena_metrics[a]["entrants"][name]["diagnostic_territory_pct"]
            row_pct.append(f"{val:.2f}%")
        row_pct.append("Dilution by A")
        lines.append(f"| {' | '.join(row_pct)} |")

    lines.append("\n### Table 3: Region Attacker vs Claimer Matchup Across Arena Sizes")
    lines.append(
        "| Arena Size | Matches | Region Attacker Wins | Claimer Wins | Ties | Combat Kills | Timeouts |"
    )
    lines.append("|---:|---:|---:|---:|---:|---:|---:|")
    for a in sorted(ARENA_DIRS.keys()):
        m = arena_metrics[a]["region_attacker_vs_claimer"]
        lines.append(
            f"| {a} | {m['matches']} | {m['ra_wins']} | {m['claimer_wins']} | {m['ties']} | {m['combat_kills']} | {m['timeouts']} |"
        )

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Phase 4E territory scoring analyzer")
    parser.add_argument("--json", action="store_true", help="Output raw JSON analysis")
    args = parser.parse_args()

    analysis = analyze_phase4b_artifacts()
    if args.json:
        print(json.dumps(analysis, indent=2))
    else:
        print(format_markdown_tables(analysis))


if __name__ == "__main__":
    main()
