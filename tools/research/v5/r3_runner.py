"""R3B paired execution harness: bundled attacker vs research region sweeper.

Every arm below runs under the permanent stable Ruleset ``bytefray-rules-4``
with no experimental Ruleset, no R1 process mortality and no R2 objective
oracle. The only thing that varies across arms is *which agent occupies the
attacking seat*; seed, slot order, arena size, max ticks, opponent and
opponent revision are held identical, and seat placement is agent-identity
independent by construction (``placement.seeded_seat_starts`` draws from
seed/arena/entrant-count only), so substituting the agent keeps the layout
fixed and swaps only the occupant.

    baseline        the bundled v4_concentrated_attacker (re-run fresh)
    point_control   v5r3_point_control -- behavioural clone of the baseline
    sweeper         v5r3_region_sweeper -- THE experimental arm
    sweeper_mobile  v5r3_region_sweeper_mobile -- secondary variant

The ``point_control`` arm exists to prove the paired construction itself is
clean: its replay's gameplay tick stream must be byte-identical to the
baseline's, so any sweeper-versus-baseline difference is attributable to the
sweep rather than to the research agent directory, the alternate spec
resolution path, or an accidental transcription change.

Like ``r1_runner.py``/``r2_runner.py``, this module reuses
``corpus_runner.run_single_match`` rather than re-implementing match
invocation, so Phase 0, R1, R2 and R3 all share one match-execution seam.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from battle_engine.agent_revisions import agent_revision_fingerprint
from battle_engine.agents import AgentSpec, agent_spec_from_dir
from battle_engine.ruleset_policy import BYTEFRAY_RULESET_V4_ID

from tools.research.v5.analyzer import analyze_match
from tools.research.v5.corpus_runner import (
    STANDARD_V4_ARENA_SIZE,
    STANDARD_V4_MAX_TICKS,
    run_single_match,
)
from tools.research.v5.r3_selection import (
    R3_BASELINE_ATTACKER,
    select_r3b_diagnostic_subset,
)

RESEARCH_AGENTS_DIR = Path(__file__).resolve().parent / "agents"

# (arm label, agent name that replaces the baseline attacker in its seat).
# ``None`` means "leave the bundled baseline in place" -- the control arm.
ARMS: tuple[tuple[str, str | None], ...] = (
    ("baseline", None),
    ("point_control", "v5r3_point_control"),
    ("sweeper", "v5r3_region_sweeper"),
    ("sweeper_mobile", "v5r3_region_sweeper_mobile"),
)

# R3C broad-validation corpus, declared before execution (R3 charter
# Section 18). Phase 0's own agent population, seeds, arena and tick limit,
# with both slot orders enumerated explicitly.
R3C_OPPONENTS: tuple[str, ...] = (
    "v4_claimer",
    "v4_concentrated_attacker",
    "v4_defender_scout",
    "v4_local_defender",
    "v4_quorum",
    "v4_scout",
)
R3C_SEEDS: tuple[int, ...] = (1, 2, 3, 4, 5, 6, 7, 8)
R3C_SEATS: tuple[str, ...] = ("A", "B")


def load_research_agent_specs() -> dict[str, AgentSpec]:
    """Resolve every research-only agent directly from ``agents/`` here.

    Deliberately not ``battle_engine.agents.resolve_agent``: these agents
    are kept out of the writable ``agents/`` catalog precisely so no
    product code path can reach them (see ``agents/README.md``).
    """

    specs: dict[str, AgentSpec] = {}
    for child in sorted(RESEARCH_AGENTS_DIR.iterdir()):
        if not child.is_dir():
            continue
        spec = agent_spec_from_dir(child)
        if spec is not None:
            specs[spec.name] = spec
    return specs


def replay_digests(replay_path: Path) -> dict[str, str]:
    """SHA-256 of the whole replay and of its gameplay tick stream alone.

    The header and terminal result records legitimately carry agent names,
    source fingerprints and derived match/result ids, so two runs that play
    out identically with different agents in a seat differ there and only
    there. ``tick_stream_sha256`` is therefore the comparison that answers
    "was the gameplay identical?".
    """

    whole = hashlib.sha256()
    ticks = hashlib.sha256()
    with open(replay_path, "rb") as handle:
        for raw in handle:
            if not raw.strip():
                continue
            whole.update(raw)
            if json.loads(raw).get("record_type") == "tick":
                ticks.update(raw)
    return {"replay_sha256": whole.hexdigest(), "tick_stream_sha256": ticks.hexdigest()}


def substitution_seat(agent_a: str, agent_b: str) -> str | None:
    """Which seat the experimental substitution replaces.

    Pre-declared rule: the first seat in seat order (A, then B) holding the
    baseline attacker. In the attacker self-play negative control both seats
    hold it, and this rule substitutes seat A only, leaving the bundled
    baseline as the opponent so the arm stays a paired comparison rather
    than a mirror match of two research agents.

    R3C supplies the seat explicitly instead (``pairing["substitution_seat"]``)
    because its corpus enumerates both slot orders deliberately, including
    the self-play cell where seat A and seat B are genuinely different
    experiments rather than the same match twice.
    """

    if agent_a == R3_BASELINE_ATTACKER:
        return "A"
    if agent_b == R3_BASELINE_ATTACKER:
        return "B"
    return None


def build_r3c_pairings(
    opponents: tuple[str, ...] = R3C_OPPONENTS,
    seeds: tuple[int, ...] = R3C_SEEDS,
    seats: tuple[str, ...] = R3C_SEATS,
) -> list[dict[str, Any]]:
    """The R3C broad corpus, declared before execution.

    One cell per (opponent, seed, attacker seat): the baseline attacker
    plays every canonical V4 opponent at every Phase 0 seed in both slot
    orders, and each cell is then re-run with the research agent in that
    same seat. Slot order is enumerated rather than assumed symmetric
    because stable V4's chunked scheduler rotates its starting entrant
    (``RULESET_V4.scheduler_rotate_start``), so seat A and seat B are not
    interchangeable. The self-play cell is kept in both orders for the same
    reason: substituting seat A and substituting seat B are different
    experiments against an unchanged bundled opponent.

    Seeds, arena size, max ticks and the opponent set are Phase 0's, reused
    rather than re-chosen, and are fixed here before any R3C result exists.
    """

    pairings: list[dict[str, Any]] = []
    for opponent in opponents:
        for seed in seeds:
            for seat in seats:
                agent_a = R3_BASELINE_ATTACKER if seat == "A" else opponent
                agent_b = opponent if seat == "A" else R3_BASELINE_ATTACKER
                pairings.append(
                    {
                        "category": f"r3c_{opponent}_seat{seat}",
                        "match_label": f"{agent_a}__vs__{agent_b}__seed_{seed}__seat_{seat}",
                        "agent_a": agent_a,
                        "agent_b": agent_b,
                        "seed": seed,
                        "substitution_seat": seat,
                    }
                )
    return pairings


def run_r3b(
    data_root: Path,
    output_root: Path,
    *,
    pairings: list[dict[str, Any]],
    arms: tuple[tuple[str, str | None], ...] = ARMS,
    arena_size: int = STANDARD_V4_ARENA_SIZE,
    max_ticks: int = STANDARD_V4_MAX_TICKS,
) -> dict[str, dict[str, Any]]:
    """Run every pairing across every applicable arm; ``{label: {arm: analysis}}``."""

    output_root.mkdir(parents=True, exist_ok=True)
    research_specs = load_research_agent_specs()
    results: dict[str, dict[str, Any]] = {}
    start = time.perf_counter()
    done = 0

    for row in pairings:
        label = row["match_label"]
        agent_a = row["agent_a"]
        agent_b = row["agent_b"]
        seed = int(row["seed"])
        seat = row.get("substitution_seat") or substitution_seat(agent_a, agent_b)
        arm_results: dict[str, Any] = {}

        for arm, substitute in arms:
            if substitute is not None and seat is None:
                # A comparator matchup with no baseline attacker in it: the
                # substitution is undefined, so only the control arm runs.
                continue
            run_a = substitute if (substitute and seat == "A") else agent_a
            run_b = substitute if (substitute and seat == "B") else agent_b

            replay_path, result_path, _ = run_single_match(
                data_root,
                run_a,
                run_b,
                seed,
                output_root / label / f"arm_{arm}",
                arena_size=arena_size,
                max_ticks=max_ticks,
                ruleset_id=BYTEFRAY_RULESET_V4_ID,
                with_trace=False,
                agent_specs=research_specs,
            )
            analysis = analyze_match(replay_path, result_path)
            analysis.update(
                match_label=label,
                category=row.get("category", ""),
                agent_a=run_a,
                agent_b=run_b,
                baseline_agent_a=agent_a,
                baseline_agent_b=agent_b,
                seed=seed,
                arm=arm,
                substitution_seat=seat,
                **replay_digests(replay_path),
            )
            arm_results[arm] = analysis
            done += 1
            print(
                f"  [{done}] {label} arm {arm} ({run_a} vs {run_b}) "
                f"({time.perf_counter() - start:.1f}s)"
            )

        results[label] = arm_results

    return results


def clone_control_report(results: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    """Per-match baseline-versus-clone gameplay equivalence verdicts."""

    report: list[dict[str, Any]] = []
    for label, arms in sorted(results.items()):
        baseline = arms.get("baseline")
        clone = arms.get("point_control")
        if baseline is None or clone is None:
            continue
        report.append(
            {
                "match_label": label,
                "baseline_tick_stream_sha256": baseline["tick_stream_sha256"],
                "clone_tick_stream_sha256": clone["tick_stream_sha256"],
                "tick_stream_identical": (
                    baseline["tick_stream_sha256"] == clone["tick_stream_sha256"]
                ),
                "winner_identical": baseline["winner"] == clone["winner"],
                "ticks_identical": baseline["actual_ticks"] == clone["actual_ticks"],
            }
        )
    return report


def instrument_liveness_report(results: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    """Guard against reporting a null produced by an inert instrument.

    A sweeper arm's gameplay tick stream must DIFFER from its baseline
    wherever the substitution actually occurred and contact was made; a
    matchup where it does not differ is one where the sweep never activated,
    which is a finding about contact rather than about conversion.
    """

    report: list[dict[str, Any]] = []
    for label, arms in sorted(results.items()):
        baseline = arms.get("baseline")
        if baseline is None:
            continue
        for arm in ("sweeper", "sweeper_mobile"):
            candidate = arms.get(arm)
            if candidate is None:
                continue
            report.append(
                {
                    "match_label": label,
                    "arm": arm,
                    "tick_stream_differs_from_baseline": (
                        candidate["tick_stream_sha256"] != baseline["tick_stream_sha256"]
                    ),
                    "baseline_had_contact": (
                        baseline["first_geometric_contact_tick"] is not None
                    ),
                }
            )
    return report


def build_manifest(
    selected: dict[str, dict[str, Any]],
    results: dict[str, dict[str, Any]],
    data_root: Path,
    *,
    pairings: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Assemble the reproducible R3B record: inputs, fingerprints, controls, results."""

    fingerprints: dict[str, str] = {}
    bundled = {
        "v4_claimer",
        "v4_concentrated_attacker",
        "v4_defender_scout",
        "v4_local_defender",
        "v4_quorum",
        "v4_scout",
    }
    for name in sorted(bundled):
        agent_dir = data_root / "agents" / name
        if agent_dir.is_dir():
            fingerprints[name] = agent_revision_fingerprint(agent_dir)
    for child in sorted(RESEARCH_AGENTS_DIR.iterdir()):
        if child.is_dir():
            fingerprints[child.name] = agent_revision_fingerprint(child)

    return {
        "ruleset_id": BYTEFRAY_RULESET_V4_ID,
        "arena_size": STANDARD_V4_ARENA_SIZE,
        "max_ticks": STANDARD_V4_MAX_TICKS,
        "instr_per_tick": 8,
        "process_mortality": False,
        "objective_target_oracle": False,
        "baseline_attacker": R3_BASELINE_ATTACKER,
        "arms": [arm for arm, _ in ARMS],
        "agent_fingerprints": fingerprints,
        "corpus": {
            category: {
                "match_label": row["match_label"],
                "agent_a": row["agent_a"],
                "agent_b": row["agent_b"],
                "seed": int(row["seed"]),
                "substitution_seat": substitution_seat(row["agent_a"], row["agent_b"]),
                "phase0_winner": row["winner"],
                "phase0_ticks": row["actual_ticks"],
            }
            for category, row in selected.items()
        },
        "pairings": [
            {
                "category": row.get("category", ""),
                "match_label": row["match_label"],
                "agent_a": row["agent_a"],
                "agent_b": row["agent_b"],
                "seed": int(row["seed"]),
                "substitution_seat": (
                    row.get("substitution_seat")
                    or substitution_seat(row["agent_a"], row["agent_b"])
                ),
            }
            for row in (pairings or [])
        ],
        "clone_control": clone_control_report(results),
        "instrument_liveness": instrument_liveness_report(results),
        "results": results,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a V5 research R3 paired corpus.")
    parser.add_argument("--data-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--stage", choices=("r3b", "r3c"), default="r3b")
    parser.add_argument(
        "--stage1-metrics",
        type=Path,
        default=REPO_ROOT / "runs" / "v5_phase0_corpus" / "stage1_metrics.jsonl",
    )
    args = parser.parse_args()

    if args.stage == "r3b":
        output = args.output or REPO_ROOT / "runs" / "v5_r3_diagnostic"
        selected = select_r3b_diagnostic_subset(args.stage1_metrics)
        pairings = [
            {
                "category": category,
                "match_label": row["match_label"],
                "agent_a": row["agent_a"],
                "agent_b": row["agent_b"],
                "seed": int(row["seed"]),
            }
            for category, row in selected.items()
        ]
        manifest_name = "r3b_manifest.json"
    else:
        output = args.output or REPO_ROOT / "runs" / "v5_r3_broad"
        pairings = build_r3c_pairings()
        selected = {}
        manifest_name = "r3c_manifest.json"

    print(f"{args.stage.upper()}: {len(pairings)} matchups x up to {len(ARMS)} arms")
    results = run_r3b(args.data_root, output, pairings=pairings)
    manifest = build_manifest(selected, results, args.data_root, pairings=pairings)

    output.mkdir(parents=True, exist_ok=True)
    manifest_path = output / manifest_name
    with open(manifest_path, "w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2, sort_keys=True)
    print(f"\nWrote {manifest_path}")

    clone = manifest["clone_control"]
    identical = sum(1 for row in clone if row["tick_stream_identical"])
    print(
        f"\nClone control (baseline vs point_control gameplay tick stream): "
        f"{identical}/{len(clone)} byte-identical"
    )
    for row in clone:
        if not row["tick_stream_identical"]:
            print(f"  *** DIFFERS: {row['match_label']}")


if __name__ == "__main__":
    main()
