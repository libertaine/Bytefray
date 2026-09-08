"""Deterministic V4 Baseline Corpus Runner for Bytefray V5 Research.

Executes Stage 1 (broad replay corpus) and Stage 2 (diagnostic trace subset)
against stable `bytefray-rules-4` using canonical V4 agents.
Extracts Layer A, B, and C metrics and outputs machine-readable JSON/CSV and markdown summaries.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from battle_engine.agent_revisions import agent_revision_fingerprint
from battle_engine.agents import resolve_agent
from battle_engine.config import Config
from battle_engine.match_service import MatchEntrant, MatchRequest, NativeMatchService
from battle_engine.placement import resolve_direct_match_starts

from tools.research.v5.analyzer import analyze_match

CANONICAL_V4_AGENTS = (
    "v4_claimer",
    "v4_concentrated_attacker",
    "v4_defender_scout",
    "v4_local_defender",
    "v4_quorum",
    "v4_scout",
)

STANDARD_V4_SEEDS = (1, 2, 3, 4, 5, 6, 7, 8)
STANDARD_V4_ARENA_SIZE = 512
STANDARD_V4_MAX_TICKS = 1000
RULESET_V4_STABLE = "bytefray-rules-4"


def run_single_match(
    data_root: Path,
    agent_a_name: str,
    agent_b_name: str,
    seed: int,
    output_dir: Path,
    *,
    arena_size: int = STANDARD_V4_ARENA_SIZE,
    max_ticks: int = STANDARD_V4_MAX_TICKS,
    ruleset_id: str = RULESET_V4_STABLE,
    with_trace: bool = False,
    process_integrity: int | None = None,
) -> tuple[Path, Path, Path | None]:
    """Execute one match and return (replay_path, result_path, trace_path).

    ``process_integrity`` is V5 research Phase R1's experimental parameter
    (see ``battle_engine.process_runtime.has_process_mortality``). Ignored
    entirely unless ``ruleset_id`` is a mortality Ruleset, so every existing
    caller of this function (Phase 0's stable-V4 corpus) is unaffected.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    replay_path = output_dir / "replay.jsonl"
    trace_path = (output_dir / "trace.jsonl") if with_trace else None

    spec_a = resolve_agent(data_root, agent_a_name)
    spec_b = resolve_agent(data_root, agent_b_name)

    starts = resolve_direct_match_starts(
        ruleset_id=ruleset_id,
        arena_size=arena_size,
        entrant_count=2,
        supplied_starts=[None, None],
        seed=seed,
    )
    entrants = (
        MatchEntrant.python("A", agent_a_name, starts[0], spec_a),
        MatchEntrant.python("B", agent_b_name, starts[1], spec_b),
    )
    request = MatchRequest(
        config=Config(seed=seed, arena_size=arena_size, instr_per_tick=8),
        entrants=entrants,
        max_ticks=max_ticks,
        replay_path=replay_path,
        trace_path=trace_path,
        verbose=False,
        ruleset_id=ruleset_id,
        process_integrity=process_integrity,
    )
    result = NativeMatchService().run(request)
    assert result.result_path is not None
    return replay_path, result.result_path, trace_path


def build_corpus_manifest(
    data_root: Path,
    agents: tuple[str, ...],
    seeds: tuple[int, ...],
    arena_size: int,
    max_ticks: int,
    ruleset_id: str,
) -> dict[str, Any]:
    """Generate deterministic manifest describing corpus parameters and agent fingerprints."""
    agent_manifests = {}
    for name in agents:
        agent_dir = data_root / "agents" / name
        fp = agent_revision_fingerprint(agent_dir)
        agent_manifests[name] = {
            "fingerprint": fp,
            "path": f"agents/{name}",
        }

    return {
        "ruleset_id": ruleset_id,
        "arena_size": arena_size,
        "max_ticks": max_ticks,
        "seeds": list(seeds),
        "agents": list(agents),
        "agent_metadata": agent_manifests,
        "total_pairings": len(agents) * len(agents),
        "total_matches": len(agents) * len(agents) * len(seeds),
    }


def execute_corpus(
    data_root: Path,
    output_root: Path,
    *,
    agents: tuple[str, ...] = CANONICAL_V4_AGENTS,
    seeds: tuple[int, ...] = STANDARD_V4_SEEDS,
    arena_size: int = STANDARD_V4_ARENA_SIZE,
    max_ticks: int = STANDARD_V4_MAX_TICKS,
    ruleset_id: str = RULESET_V4_STABLE,
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    """Run Stage 1 broad corpus and Stage 2 diagnostic trace subset."""
    stage1_dir = output_root / "stage1_replays"
    stage2_dir = output_root / "stage2_traces"
    stage1_dir.mkdir(parents=True, exist_ok=True)
    stage2_dir.mkdir(parents=True, exist_ok=True)

    manifest = build_corpus_manifest(data_root, agents, seeds, arena_size, max_ticks, ruleset_id)
    with open(output_root / "manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, sort_keys=True)

    stage1_metrics: list[dict[str, Any]] = []
    total = len(agents) * len(agents) * len(seeds)
    idx = 0
    t0 = time.perf_counter()

    print(f"Starting Stage 1: Running {total} baseline matches ({len(agents)} agents x {len(seeds)} seeds)...")

    for agent_a in agents:
        for agent_b in agents:
            pair_label = f"{agent_a}__vs__{agent_b}"
            for seed in seeds:
                idx += 1
                match_label = f"{pair_label}__seed_{seed}"
                match_out = stage1_dir / match_label
                replay_path, result_path, _ = run_single_match(
                    data_root, agent_a, agent_b, seed, match_out,
                    arena_size=arena_size, max_ticks=max_ticks, ruleset_id=ruleset_id,
                    with_trace=False
                )
                m = analyze_match(replay_path, result_path)
                m["match_label"] = match_label
                m["agent_a"] = agent_a
                m["agent_b"] = agent_b
                stage1_metrics.append(m)
                if idx % 36 == 0 or idx == total:
                    elapsed = time.perf_counter() - t0
                    print(f"  Completed {idx}/{total} matches ({elapsed:.1f}s, {idx/max(0.1, elapsed):.1f} match/s)...")

    # Save Stage 1 metrics JSONL
    with open(output_root / "stage1_metrics.jsonl", "w", encoding="utf-8") as f:
        for m in stage1_metrics:
            f.write(json.dumps(m, sort_keys=True) + "\n")

    # Select Stage 2 diagnostic trace subset based on machine criteria:
    # 1. Shortest decisive match
    # 2. Longest decisive match
    # 3. High combat writes with low conversion (active stagnation)
    # 4. Quietest match (lowest combat writes)
    # 5. Highest disruption hits
    # 6. Representative Quorum match
    # 7. Concentrated Attacker vs Local Defender (attrition siege)
    # 8. Decisive Scout or Defender Scout knockout
    print("\nSelecting Stage 2 Diagnostic Trace Subset...")

    decisive_matches = [m for m in stage1_metrics if not m["is_tie"] and not m["is_timeout"]]
    timeout_matches = [m for m in stage1_metrics if m["is_timeout"]]

    selected_labels: dict[str, str] = {}

    if decisive_matches:
        shortest = min(decisive_matches, key=lambda m: m["actual_ticks"])
        selected_labels[shortest["match_label"]] = f"Shortest decisive knockout ({shortest['actual_ticks']} ticks, winner: {shortest['winner']})"
        longest_decisive = max(decisive_matches, key=lambda m: m["actual_ticks"])
        selected_labels[longest_decisive["match_label"]] = f"Longest decisive conversion ({longest_decisive['actual_ticks']} ticks, winner: {longest_decisive['winner']})"

    # High combat active stagnation
    stagnant_matches = [m for m in timeout_matches if m["stagnation_ticks"] > 500]
    if stagnant_matches:
        most_active_stagnant = max(stagnant_matches, key=lambda m: sum(m["total_combat_writes"].values()))
        selected_labels[most_active_stagnant["match_label"]] = f"Max combat active stagnation ({sum(most_active_stagnant['total_combat_writes'].values())} combat writes, 0 conversion)"

    # Quietest match
    quietest = min(stage1_metrics, key=lambda m: sum(m["total_combat_writes"].values()))
    selected_labels[quietest["match_label"]] = f"Passive / lowest combat interaction ({sum(quietest['total_combat_writes'].values())} combat writes)"

    # Highest disruption match
    max_disrupt = max(stage1_metrics, key=lambda m: sum(m["total_disruptions_received"].values()))
    selected_labels[max_disrupt["match_label"]] = f"Max disruption combat ({sum(max_disrupt['total_disruptions_received'].values())} disruptions)"

    # Quorum vs Concentrated Attacker
    quorum_matches = [m for m in stage1_metrics if "v4_quorum" in (m["agent_a"], m["agent_b"]) and m["agent_a"] != m["agent_b"]]
    if quorum_matches:
        selected_labels[quorum_matches[0]["match_label"]] = f"Quorum multi-process coordinated match ({quorum_matches[0]['agent_a']} vs {quorum_matches[0]['agent_b']})"

    # Concentrated Attacker vs Local Defender
    siege_matches = [m for m in stage1_metrics if (m["agent_a"] == "v4_concentrated_attacker" and m["agent_b"] == "v4_local_defender")]
    if siege_matches:
        selected_labels[siege_matches[0]["match_label"]] = "Attacker vs Local Defender siege attrition"

    # Self play
    self_play = [m for m in stage1_metrics if m["agent_a"] == m["agent_b"] and m["agent_a"] == "v4_quorum"]
    if self_play:
        selected_labels[self_play[0]["match_label"]] = "Quorum self-play control"

    print(f"Running Stage 2: {len(selected_labels)} trace-enabled diagnostic matches...")
    stage2_metrics: list[dict[str, Any]] = []

    for label, reason in selected_labels.items():
        base_match = next(m for m in stage1_metrics if m["match_label"] == label)
        agent_a = base_match["agent_a"]
        agent_b = base_match["agent_b"]
        seed = base_match["seed"]
        match_out = stage2_dir / label
        replay_path, result_path, trace_path = run_single_match(
            data_root, agent_a, agent_b, seed, match_out,
            arena_size=arena_size, max_ticks=max_ticks, ruleset_id=ruleset_id,
            with_trace=True
        )
        m2 = analyze_match(replay_path, result_path, trace_path)
        m2["match_label"] = label
        m2["agent_a"] = agent_a
        m2["agent_b"] = agent_b
        m2["selection_reason"] = reason
        stage2_metrics.append(m2)
        print(f"  [Trace] {label}: {reason}")

    with open(output_root / "stage2_trace_metrics.jsonl", "w", encoding="utf-8") as f:
        for m in stage2_metrics:
            f.write(json.dumps(m, sort_keys=True) + "\n")

    return manifest, stage1_metrics, stage2_metrics


def generate_aggregate_report(
    manifest: dict[str, Any],
    stage1_metrics: list[dict[str, Any]],
    stage2_metrics: list[dict[str, Any]],
) -> dict[str, Any]:
    """Compute aggregate statistical summary across all matches."""
    total_matches = len(stage1_metrics)
    decisive_matches = [m for m in stage1_metrics if not m["is_tie"] and not m["is_timeout"]]
    timeout_matches = [m for m in stage1_metrics if m["is_timeout"]]
    tie_matches = [m for m in stage1_metrics if m["is_tie"]]

    durations = [m["actual_ticks"] for m in stage1_metrics]
    avg_duration = sum(durations) / len(durations) if durations else 0

    stagnation_ticks_list = [m["stagnation_ticks"] for m in stage1_metrics]
    avg_stagnation = sum(stagnation_ticks_list) / len(stagnation_ticks_list) if stagnation_ticks_list else 0

    combat_writes_list = [sum(m["total_combat_writes"].values()) for m in stage1_metrics]
    avg_combat_writes = sum(combat_writes_list) / len(combat_writes_list) if combat_writes_list else 0

    core_damage_list = [sum(m["core_damage_dealt"].values()) for m in stage1_metrics]
    avg_core_damage = sum(core_damage_list) / len(core_damage_list) if core_damage_list else 0

    # Per-agent win/loss/tie records
    agent_records: dict[str, dict[str, int]] = defaultdict(lambda: {"wins": 0, "losses": 0, "ties": 0, "matches": 0})
    for m in stage1_metrics:
        a = m["agent_a"]
        b = m["agent_b"]
        agent_records[a]["matches"] += 1
        agent_records[b]["matches"] += 1
        winner_entrant = m["winner"]
        if winner_entrant == "A":
            agent_records[a]["wins"] += 1
            agent_records[b]["losses"] += 1
        elif winner_entrant == "B":
            agent_records[b]["wins"] += 1
            agent_records[a]["losses"] += 1
        else:
            agent_records[a]["ties"] += 1
            agent_records[b]["ties"] += 1

    # Matchup matrix
    matrix: dict[str, dict[str, dict[str, int]]] = defaultdict(lambda: defaultdict(lambda: {"wins_a": 0, "wins_b": 0, "ties": 0}))
    for m in stage1_metrics:
        a = m["agent_a"]
        b = m["agent_b"]
        w = m["winner"]
        if w == "A":
            matrix[a][b]["wins_a"] += 1
        elif w == "B":
            matrix[a][b]["wins_b"] += 1
        else:
            matrix[a][b]["ties"] += 1

    # Trace diagnostics
    trace_rejected_reach = sum(sum(m["trace_rejected_out_of_reach"].values()) for m in stage2_metrics)
    trace_sightings = sum(sum(m["trace_sensor_sightings"].values()) for m in stage2_metrics)
    trace_applied = sum(sum(m["trace_applied_actions"].values()) for m in stage2_metrics)

    return {
        "total_matches": total_matches,
        "decisive_count": len(decisive_matches),
        "decisive_pct": round(len(decisive_matches) * 100.0 / total_matches, 2),
        "timeout_count": len(timeout_matches),
        "timeout_pct": round(len(timeout_matches) * 100.0 / total_matches, 2),
        "tie_count": len(tie_matches),
        "tie_pct": round(len(tie_matches) * 100.0 / total_matches, 2),
        "avg_duration": round(avg_duration, 1),
        "avg_stagnation_ticks": round(avg_stagnation, 1),
        "avg_combat_writes": round(avg_combat_writes, 1),
        "avg_core_damage_dealt": round(avg_core_damage, 1),
        "agent_records": dict(agent_records),
        "matchup_matrix": {a: dict(row) for a, row in matrix.items()},
        "trace_summary": {
            "matches_analyzed": len(stage2_metrics),
            "total_applied_actions": trace_applied,
            "total_rejected_reach": trace_rejected_reach,
            "total_sensor_sightings": trace_sightings,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run V4 Baseline Research Corpus.")
    parser.add_argument("--output", type=Path, default=REPO_ROOT / "runs" / "v5_phase0_corpus", help="Output directory")
    args = parser.parse_args()

    manifest, s1_metrics, s2_metrics = execute_corpus(REPO_ROOT, args.output)
    report = generate_aggregate_report(manifest, s1_metrics, s2_metrics)

    with open(args.output / "aggregate_summary.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, sort_keys=True)

    print("\n=== Corpus Execution Completed ===")
    print(f"Total Matches: {report['total_matches']}")
    print(f"Decisive: {report['decisive_count']} ({report['decisive_pct']}%)")
    print(f"Timeouts: {report['timeout_count']} ({report['timeout_pct']}%)")
    print(f"Ties: {report['tie_count']} ({report['tie_pct']}%)")
    print(f"Average Duration: {report['avg_duration']} ticks")
    print(f"Average Combat Writes: {report['avg_combat_writes']}")
    print(f"Average Stagnation: {report['avg_stagnation_ticks']} ticks")


if __name__ == "__main__":
    main()
