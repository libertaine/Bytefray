"""Deterministic R3B diagnostic-corpus selection from the Phase 0 corpus.

R3 asks whether Phase 0's conversion deficit is a property of stable V4
mechanics or of the bundled V4 agent population
(docs/research/v5/V5_R3_AGENT_COMPETENCE.md). The experiment substitutes a
research-only region-sweeping variant for one bundled attacker and changes
nothing else, so R3's corpus -- unlike R1's and R2's, which could use any
matchup because they changed the *Ruleset* -- must consist of matchups the
baseline attacker actually plays in.

The selection rule below is therefore R1's six-category shape re-pointed at
the attacker-involved subset of the same frozen Phase 0 corpus
(``runs/v5_phase0_corpus/stage1_metrics.jsonl``), plus two matches added by
explicit name rather than by tuning a metric to reproduce them. It is a pure
function of the corpus data, declared before execution, and never re-tuned
against R3's own results (standing research-integrity rule: a selection rule
must not be discovered against the result it is meant to evaluate).

Selection is deliberately NOT re-derived from R1's ``r1_selection`` module:
four of R1's seven matches contain no ``v4_concentrated_attacker`` at all,
so reusing that set verbatim would have produced four matchups in which the
experimental substitution is a no-op.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

# The bundled agent R3 substitutes for. Selected in Section D of the R3
# report; imported here so the selection rule and the experiment cannot
# drift apart.
R3_BASELINE_ATTACKER = "v4_concentrated_attacker"

# The behavioural comparator. Not an experimental arm: Quorum is the one
# bundled agent that already sweeps a region around a target, so R2 flagged
# it as the population's existence proof that region-capable attack is legal
# under stable V4. It is run as a plain stable-V4 match on identical ground
# (same opponent, seed and slot order as the named reference case).
R3_COMPARATOR_AGENT = "v4_quorum"


def _tie_break_key(m: dict[str, Any]) -> tuple[str, str, int]:
    return (m["agent_a"], m["agent_b"], int(m["seed"]))


def _best(candidates: list[dict[str, Any]], metric: Any, *, reverse: bool) -> dict[str, Any]:
    ordered = sorted(
        candidates,
        key=lambda m: (metric(m), _tie_break_key(m)),
        reverse=reverse,
    )
    return ordered[0]


def select_r3b_diagnostic_subset(stage1_metrics_path: Path) -> dict[str, dict[str, Any]]:
    """Return ``{category: match_metrics_dict}`` for R3B's diagnostic corpus.

    Every value is one row of Phase 0's ``stage1_metrics.jsonl`` (an
    ``analyze_match`` dict plus ``match_label``/``agent_a``/``agent_b``), so
    seed, slot order, arena size, max ticks and opponent revisions are reused
    exactly rather than re-chosen. A match claimed by an earlier category is
    never re-claimed by a later one.
    """

    rows: list[dict[str, Any]] = []
    with open(stage1_metrics_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))

    attacker_rows = [
        m for m in rows if R3_BASELINE_ATTACKER in (m["agent_a"], m["agent_b"])
    ]
    attacker_timeouts = [m for m in attacker_rows if m["is_timeout"]]
    attacker_decisive = [
        m for m in attacker_rows if not m["is_tie"] and not m["is_timeout"]
    ]

    selected: dict[str, dict[str, Any]] = {}
    used_labels: set[str] = set()

    def claim_by_name(category: str, agent_a: str, agent_b: str, seed: int) -> None:
        matches = [
            m
            for m in rows
            if m["agent_a"] == agent_a
            and m["agent_b"] == agent_b
            and int(m["seed"]) == seed
            and m["match_label"] not in used_labels
        ]
        if matches:
            selected[category] = matches[0]
            used_labels.add(matches[0]["match_label"])

    def claim(category: str, pool: list[dict[str, Any]], metric: Any, *, reverse: bool) -> None:
        remaining = [m for m in pool if m["match_label"] not in used_labels]
        if not remaining:
            return
        chosen = _best(remaining, metric, reverse=reverse)
        selected[category] = chosen
        used_labels.add(chosen["match_label"])

    # 1. The named reference case, claimed FIRST so the machine rules below
    # cannot consume it. Phase 0 Section 10 Case 7, R1 Section G.2 and R2
    # Section I all name this exact matchup/seed as the flagship
    # siege-versus-repair-turtle failure; R3 keeps it for continuity rather
    # than because a metric ranks it first.
    claim_by_name(
        "named_reference_siege_vs_turtle", R3_BASELINE_ATTACKER, "v4_local_defender", 1
    )

    # 2. Highest core interaction that still failed to convert: among
    # attacker-involved timeouts, maximum total hostile core-targeting
    # writes.
    claim(
        "conversion_failure_high_activity",
        attacker_timeouts,
        lambda m: sum(m["core_attack_writes"].values()),
        reverse=True,
    )

    # 3. Disruption-heavy contact with offensive writes: among
    # attacker-involved timeouts, maximum total disruptions received.
    claim(
        "disruption_heavy",
        attacker_timeouts,
        lambda m: sum(m["total_disruptions_received"].values()),
        reverse=True,
    )

    # 4. Slow but eventually decisive: longest attacker-involved decisive
    # match -- conversion happens, but only after a long grind.
    claim(
        "slow_eventual_conversion",
        attacker_decisive,
        lambda m: m["actual_ticks"],
        reverse=True,
    )

    # 5. Healthy control: fastest attacker-involved decisive match. Stable V4
    # already converts here, so the sweeper must not break it.
    claim(
        "healthy_decisive",
        attacker_decisive,
        lambda m: m["actual_ticks"],
        reverse=False,
    )

    # 6. Negative control: the quietest attacker-involved match. A sweeper
    # cannot prove anything where no target is ever acquired, and must not
    # "improve" a no-contact match -- doing so would mean it had gained
    # search ability, not conversion ability.
    claim(
        "passive_no_contact",
        attacker_rows,
        lambda m: sum(m["total_combat_writes"].values()),
        reverse=False,
    )

    # 7. Quorum comparator, by explicit name: the same opponent, seed and
    # slot order as the named reference case, with the one bundled
    # region-capable agent in the attacking slot. Not an experimental arm.
    claim_by_name("quorum_comparator", R3_COMPARATOR_AGENT, "v4_local_defender", 1)

    return selected


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Select the R3B diagnostic corpus.")
    parser.add_argument(
        "--stage1-metrics",
        type=Path,
        default=Path("runs/v5_phase0_corpus/stage1_metrics.jsonl"),
    )
    args = parser.parse_args()

    selected = select_r3b_diagnostic_subset(args.stage1_metrics)
    print(f"{'category':36s} {'agent_a':26s} {'agent_b':26s} seed  outcome")
    for category, row in selected.items():
        outcome = (
            "tie"
            if row["is_tie"]
            else f"{row['winner']} wins"
        )
        print(
            f"{category:36s} {row['agent_a']:26s} {row['agent_b']:26s} "
            f"{int(row['seed']):4d}  {outcome} @{row['actual_ticks']}t"
        )


if __name__ == "__main__":
    main()
