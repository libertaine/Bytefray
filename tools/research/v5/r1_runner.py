"""R1B/R1C paired execution harness: stable V4 control vs mortality variants.

For each selected diagnostic match (see ``r1_selection.py``), re-runs the
exact same agents/seed/arena/max_ticks pairing under stable
``bytefray-rules-4`` (the control) and under the R1 experimental Ruleset
(``bytefray-rules-5-r1-alpha1``) at each requested finite integrity value H,
then analyzes every run with the upgraded ``tools.research.v5.analyzer`` and
writes one aggregate JSON manifest per stage.

This module intentionally reuses ``corpus_runner.run_single_match`` (the
same match-execution seam Phase 0 used) rather than re-implementing match
invocation, so R1 and Phase 0 share one code path for actually running a
match.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from battle_engine.rules import BYTEFRAY_RULESET_V5_R1_ALPHA1_ID
from battle_engine.ruleset_policy import BYTEFRAY_RULESET_V4_ID

from tools.research.v5.analyzer import analyze_match
from tools.research.v5.corpus_runner import (
    STANDARD_V4_ARENA_SIZE,
    STANDARD_V4_MAX_TICKS,
    run_single_match,
)
from tools.research.v5.r1_selection import select_r1b_diagnostic_subset

DEFAULT_H_VALUES: tuple[int, ...] = (8, 4, 2, 1)


def run_paired_diagnostic(
    data_root: Path,
    output_root: Path,
    *,
    stage1_metrics_path: Path,
    h_values: tuple[int, ...] = DEFAULT_H_VALUES,
    arena_size: int = STANDARD_V4_ARENA_SIZE,
    max_ticks: int = STANDARD_V4_MAX_TICKS,
) -> dict[str, Any]:
    """Run the R1B diagnostic subset paired across the control and every H.

    Returns a manifest: ``{selection: {...}, results: {label: {variant:
    analyzer_dict}}}`` where ``variant`` is ``"control"`` or ``f"H{h}"``.
    """

    selection = select_r1b_diagnostic_subset(stage1_metrics_path)
    output_root.mkdir(parents=True, exist_ok=True)

    results: dict[str, dict[str, Any]] = {}
    t0 = time.perf_counter()
    total_variants = len(selection) * (1 + len(h_values))
    done = 0

    for category, row in selection.items():
        label = row["match_label"]
        agent_a = row["agent_a"]
        agent_b = row["agent_b"]
        seed = int(row["seed"])
        label_dir = output_root / label
        variant_results: dict[str, Any] = {}

        # Control: fresh re-run under current code, stable bytefray-rules-4.
        control_dir = label_dir / "control"
        replay_path, result_path, _ = run_single_match(
            data_root, agent_a, agent_b, seed, control_dir,
            arena_size=arena_size, max_ticks=max_ticks,
            ruleset_id=BYTEFRAY_RULESET_V4_ID, with_trace=False,
        )
        m = analyze_match(replay_path, result_path)
        m.update(match_label=label, agent_a=agent_a, agent_b=agent_b, category=category, variant="control")
        variant_results["control"] = m
        done += 1
        print(f"  [{done}/{total_variants}] {label} control done ({time.perf_counter() - t0:.1f}s)")

        for h in h_values:
            variant_dir = label_dir / f"H{h}"
            replay_path, result_path, _ = run_single_match(
                data_root, agent_a, agent_b, seed, variant_dir,
                arena_size=arena_size, max_ticks=max_ticks,
                ruleset_id=BYTEFRAY_RULESET_V5_R1_ALPHA1_ID,
                process_integrity=h, with_trace=False,
            )
            m = analyze_match(replay_path, result_path)
            m.update(match_label=label, agent_a=agent_a, agent_b=agent_b, category=category, variant=f"H{h}")
            variant_results[f"H{h}"] = m
            done += 1
            print(f"  [{done}/{total_variants}] {label} H={h} done ({time.perf_counter() - t0:.1f}s)")

        results[label] = variant_results

    manifest = {
        "selection": {cat: row["match_label"] for cat, row in selection.items()},
        "h_values": list(h_values),
        "arena_size": arena_size,
        "max_ticks": max_ticks,
        "results": results,
    }
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the R1B paired diagnostic corpus.")
    parser.add_argument("--output", type=Path, default=REPO_ROOT / "runs" / "v5_r1_diagnostic")
    parser.add_argument(
        "--stage1-metrics",
        type=Path,
        default=REPO_ROOT / "runs" / "v5_phase0_corpus" / "stage1_metrics.jsonl",
    )
    parser.add_argument("--h-values", type=int, nargs="+", default=list(DEFAULT_H_VALUES))
    args = parser.parse_args()

    manifest = run_paired_diagnostic(
        REPO_ROOT, args.output,
        stage1_metrics_path=args.stage1_metrics,
        h_values=tuple(args.h_values),
    )
    with open(args.output / "r1b_manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, sort_keys=True)
    print(f"\nWrote {args.output / 'r1b_manifest.json'}")


if __name__ == "__main__":
    main()
