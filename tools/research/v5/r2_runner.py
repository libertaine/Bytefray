"""R2B/R2C paired execution harness: the four-arm target-persistence design.

For each diagnostic match (reusing ``r1_selection.py`` verbatim, so R2's
corpus is exactly R1's corpus rather than a fresh, potentially more
favorable one), runs the same agents/seed/arena/max_ticks pairing under all
four arms of the R2 causal design and analyzes every run with the
``tools.research.v5.analyzer`` R2 follow-through metrics:

    A  stable bytefray-rules-4                      mortality OFF, oracle OFF
    B  bytefray-rules-5-r2-alpha1 + oracle          mortality OFF, oracle ON
    C  bytefray-rules-5-r1-alpha1 H=H*              mortality ON,  oracle OFF
    D  bytefray-rules-5-r1-alpha1 H=H* + oracle     mortality ON,  oracle ON

Arm C is bit-for-bit R1's mortality configuration (the oracle option leaves
R1's semantics untouched when disabled), so R2's own run doubles as an R1
regression check -- see ``--verify-r1`` in the R2 report's Section H.

Like ``r1_runner.py``, this module reuses ``corpus_runner.run_single_match``
rather than re-implementing match invocation, so Phase 0, R1, and R2 all
share one match-execution seam.
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

from battle_engine.rules import (
    BYTEFRAY_RULESET_V5_R1_ALPHA1_ID,
    BYTEFRAY_RULESET_V5_R2_ALPHA1_ID,
)
from battle_engine.ruleset_policy import BYTEFRAY_RULESET_V4_ID

from tools.research.v5.analyzer import analyze_match
from tools.research.v5.corpus_runner import (
    STANDARD_V4_ARENA_SIZE,
    STANDARD_V4_MAX_TICKS,
    run_single_match,
)
from tools.research.v5.r1_selection import select_r1b_diagnostic_subset
from tools.research.v5.r2_selection import select_r2_mortality_h

# The four arms, in the order the R2 report's tables present them. Each entry
# is (arm, ruleset_id, mortality_on, oracle_on).
ARMS: tuple[tuple[str, str, bool, bool], ...] = (
    ("A", BYTEFRAY_RULESET_V4_ID, False, False),
    ("B", BYTEFRAY_RULESET_V5_R2_ALPHA1_ID, False, True),
    ("C", BYTEFRAY_RULESET_V5_R1_ALPHA1_ID, True, False),
    ("D", BYTEFRAY_RULESET_V5_R1_ALPHA1_ID, True, True),
)


def run_four_arm(
    data_root: Path,
    output_root: Path,
    *,
    pairings: list[dict[str, Any]],
    mortality_h: int,
    arms: tuple[tuple[str, str, bool, bool], ...] = ARMS,
    arena_size: int = STANDARD_V4_ARENA_SIZE,
    max_ticks: int = STANDARD_V4_MAX_TICKS,
) -> dict[str, dict[str, Any]]:
    """Run every pairing across every arm; return ``{label: {arm: analysis}}``."""

    output_root.mkdir(parents=True, exist_ok=True)
    results: dict[str, dict[str, Any]] = {}
    start = time.perf_counter()
    total = len(pairings) * len(arms)
    done = 0

    for row in pairings:
        label = row["match_label"]
        agent_a = row["agent_a"]
        agent_b = row["agent_b"]
        seed = int(row["seed"])
        arm_results: dict[str, Any] = {}

        for arm, ruleset_id, mortality_on, oracle_on in arms:
            replay_path, result_path, _ = run_single_match(
                data_root,
                agent_a,
                agent_b,
                seed,
                output_root / label / f"arm_{arm}",
                arena_size=arena_size,
                max_ticks=max_ticks,
                ruleset_id=ruleset_id,
                process_integrity=mortality_h if mortality_on else None,
                objective_target_oracle=oracle_on,
                with_trace=False,
            )
            analysis = analyze_match(replay_path, result_path)
            analysis.update(
                match_label=label,
                agent_a=agent_a,
                agent_b=agent_b,
                category=row.get("category", ""),
                arm=arm,
                mortality=mortality_on,
                oracle=oracle_on,
            )
            arm_results[arm] = analysis
            done += 1
            print(
                f"  [{done}/{total}] {label} arm {arm} "
                f"(mortality={mortality_on}, oracle={oracle_on}) "
                f"({time.perf_counter() - start:.1f}s)"
            )

        results[label] = arm_results

    return results


def run_r2b_diagnostic(
    data_root: Path,
    output_root: Path,
    *,
    stage1_metrics_path: Path,
    r1b_manifest_path: Path,
    arena_size: int = STANDARD_V4_ARENA_SIZE,
    max_ticks: int = STANDARD_V4_MAX_TICKS,
) -> dict[str, Any]:
    """Run the R2B diagnostic corpus: R1's exact match set, four arms each."""

    selection = select_r1b_diagnostic_subset(stage1_metrics_path)
    h_record = select_r2_mortality_h(r1b_manifest_path)
    mortality_h = int(h_record["selected_h"])

    pairings = [
        {
            "match_label": row["match_label"],
            "agent_a": row["agent_a"],
            "agent_b": row["agent_b"],
            "seed": int(row["seed"]),
            "category": category,
        }
        for category, row in selection.items()
    ]

    results = run_four_arm(
        data_root,
        output_root,
        pairings=pairings,
        mortality_h=mortality_h,
        arena_size=arena_size,
        max_ticks=max_ticks,
    )

    return {
        "stage": "R2B",
        "mortality_h_selection": h_record,
        "mortality_h": mortality_h,
        "arms": [
            {"arm": a, "ruleset_id": r, "mortality": m, "oracle": o}
            for a, r, m, o in ARMS
        ],
        "selection": {row["category"]: row["match_label"] for row in pairings},
        "pairings": pairings,
        "arena_size": arena_size,
        "max_ticks": max_ticks,
        "results": results,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the R2B four-arm diagnostic corpus.")
    parser.add_argument(
        "--output", type=Path, default=REPO_ROOT / "runs" / "v5_r2_diagnostic"
    )
    parser.add_argument(
        "--stage1-metrics",
        type=Path,
        default=REPO_ROOT / "runs" / "v5_phase0_corpus" / "stage1_metrics.jsonl",
    )
    parser.add_argument(
        "--r1b-manifest",
        type=Path,
        default=REPO_ROOT / "runs" / "v5_r1_diagnostic" / "r1b_manifest.json",
    )
    args = parser.parse_args()

    manifest = run_r2b_diagnostic(
        REPO_ROOT,
        args.output,
        stage1_metrics_path=args.stage1_metrics,
        r1b_manifest_path=args.r1b_manifest,
    )
    args.output.mkdir(parents=True, exist_ok=True)
    with open(args.output / "r2b_manifest.json", "w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2, sort_keys=True)
    print(f"\nWrote {args.output / 'r2b_manifest.json'}")


if __name__ == "__main__":
    main()
