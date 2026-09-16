"""Deterministic R1B diagnostic-subset selection from the Phase 0 corpus.

Section 9 of docs/research/v5/V5_R1_PROCESS_MORTALITY.md requires the R1B
diagnostic subset to be selected machine-deterministically from Phase 0's
288-match Stage 1 corpus (``runs/v5_phase0_corpus/stage1_metrics.jsonl``),
covering six representative categories, rather than hand-picked only from
favorable examples. This module implements that selection rule as a pure
function of the corpus data so the exact same six matches are reproducible
by anyone re-running it against the same corpus file.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _tie_break_key(m: dict[str, Any]) -> tuple[str, str, int]:
    return (m["agent_a"], m["agent_b"], int(m["seed"]))


def _best(
    candidates: list[dict[str, Any]],
    metric: Any,
    *,
    reverse: bool,
) -> dict[str, Any]:
    """Deterministically pick the extreme of ``metric``, ties broken by
    (agent_a, agent_b, seed) so selection never depends on input file order."""

    ordered = sorted(
        candidates,
        key=lambda m: (metric(m), _tie_break_key(m)),
        reverse=reverse,
    )
    return ordered[0]


def select_r1b_diagnostic_subset(stage1_metrics_path: Path) -> dict[str, dict[str, Any]]:
    """Return ``{category: match_metrics_dict}`` for the six R1B categories.

    Categories (docs/research/v5/V5_R1_PROCESS_MORTALITY.md Section 9):
    repair_churn, disruption_churn, passive_stagnation, healthy_decisive,
    multi_process_coordination, slow_eventual_conversion. Each value is one
    row from ``stage1_metrics.jsonl`` (a Phase 0 ``analyze_match`` dict plus
    ``match_label``/``agent_a``/``agent_b``). A category already claimed by
    an earlier (higher-priority) category in this list is never re-selected
    for a later one -- the six diagnostic matches are always distinct.
    """

    rows: list[dict[str, Any]] = []
    with open(stage1_metrics_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))

    timeout_rows = [m for m in rows if m["is_timeout"]]
    decisive_rows = [m for m in rows if not m["is_tie"] and not m["is_timeout"]]

    selected: dict[str, dict[str, Any]] = {}
    used_labels: set[str] = set()

    def claim(category: str, pool: list[dict[str, Any]], metric: Any, *, reverse: bool) -> None:
        remaining = [m for m in pool if m["match_label"] not in used_labels]
        if not remaining:
            return
        chosen = _best(remaining, metric, reverse=reverse)
        selected[category] = chosen
        used_labels.add(chosen["match_label"])

    # 1. Repair churn: among timeouts, maximum total hostile core-targeting
    # writes (the concentrated-attacker/local-defender siege pattern).
    claim(
        "repair_churn",
        timeout_rows,
        lambda m: sum(m["core_attack_writes"].values()),
        reverse=True,
    )

    # 2. Disruption churn: among timeouts, maximum total disruptions
    # received (the ping-pong mutual-disruption pattern).
    claim(
        "disruption_churn",
        timeout_rows,
        lambda m: sum(m["total_disruptions_received"].values()),
        reverse=True,
    )

    # 3. Passive stagnation / no-contact: minimum total combat writes over
    # the whole corpus -- a negative control mortality should not "solve".
    claim(
        "passive_stagnation",
        rows,
        lambda m: sum(m["total_combat_writes"].values()),
        reverse=False,
    )

    # 4. Healthy decisive control: fastest outright core-capture knockout.
    claim(
        "healthy_decisive",
        decisive_rows,
        lambda m: m["actual_ticks"],
        reverse=False,
    )

    # 5. Multi-process coordination control: prefer Quorum self-play (both
    # sides multi-process); fall back to any Quorum-involved match.
    quorum_self_play = [
        m for m in rows if m["agent_a"] == "v4_quorum" and m["agent_b"] == "v4_quorum"
    ]
    quorum_any = [
        m for m in rows if "v4_quorum" in (m["agent_a"], m["agent_b"])
    ]
    claim(
        "multi_process_coordination",
        quorum_self_play or quorum_any,
        lambda m: 0,
        reverse=False,
    )

    # 6. Slow but eventually meaningful conversion: longest decisive
    # (non-tie, non-timeout) match -- reaches the objective, but only late.
    claim(
        "slow_eventual_conversion",
        decisive_rows,
        lambda m: m["actual_ticks"],
        reverse=True,
    )

    # 7. Named reference case (NOT part of the six machine-selected
    # categories above -- added by name, not by re-tuning a metric formula
    # to reproduce it, per the research-integrity rule against discovering
    # a threshold/selection rule against the very result it evaluates).
    # docs/research/v5/V5_R1_PROCESS_MORTALITY.md Section 9 names
    # concentrated_attacker vs local_defender explicitly as Phase 0's
    # flagship one-sided siege/repair-turtle case (Case 7). Pre-declared
    # ``core_attack_writes`` aggregate sum -- the natural first reading of
    # "high core interaction" -- happens to rank defender_scout self-play
    # above it (both sides attack symmetrically, roughly doubling the
    # aggregate versus this matchup's one-sided pressure), so it is not
    # picked by the ``repair_churn`` rule above. Included here by explicit
    # name instead, seed 1 (the corpus's first seed, an arbitrary but fixed
    # tie-break), so the specific matchup the charter calls out is still
    # tested without distorting the six-category selection rule to force it
    # to the top.
    reference_candidates = [
        m
        for m in rows
        if m["agent_a"] == "v4_concentrated_attacker"
        and m["agent_b"] == "v4_local_defender"
        and int(m["seed"]) == 1
    ]
    if reference_candidates:
        selected["named_reference_siege_vs_turtle"] = reference_candidates[0]

    return selected


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Select the R1B diagnostic subset.")
    parser.add_argument(
        "--stage1-metrics",
        type=Path,
        default=Path(__file__).resolve().parents[3] / "runs" / "v5_phase0_corpus" / "stage1_metrics.jsonl",
    )
    args = parser.parse_args()

    subset = select_r1b_diagnostic_subset(args.stage1_metrics)
    for category, m in subset.items():
        print(
            f"{category}: {m['match_label']} "
            f"(agent_a={m['agent_a']}, agent_b={m['agent_b']}, seed={m['seed']}, "
            f"ticks={m['actual_ticks']}, is_tie={m['is_tie']}, is_timeout={m['is_timeout']})"
        )


if __name__ == "__main__":
    main()
