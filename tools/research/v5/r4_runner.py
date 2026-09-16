"""R4 execution harness: competence qualification, then population evaluation.

Two stages, deliberately separated by a freeze point (R4 charter Section 10):

``--stage qualification``
    Runs every candidate against the bundled qualification fixtures on
    **development seeds only** (101-108) and scores each candidate against an
    archetype-appropriate competence gate. Nothing here may use an evaluation
    seed, and nothing here decides a gameplay result.

``--stage evaluation``
    Runs the frozen population's complete ordered round-robin on **Phase 0's
    evaluation seeds** (1-8): 6 x 6 ordered pairings x 8 seeds = 288 matches,
    arena 512, max_ticks 1000, ``bytefray-rules-4``, self-play included,
    matching Phase 0's canonical corpus shape exactly.

Every match runs through ``corpus_runner.run_single_match`` -- the same
match-execution seam Phase 0, R1, R2 and R3 all use -- and every analysis
through ``analyzer.analyze_match``. R4 creates no parallel analyzer and no
experimental Ruleset; ``process_integrity`` and ``objective_target_oracle``
are left at their defaults, so neither R1 mortality nor the R2 oracle is
requested, and stable ``bytefray-rules-4`` could not honour them anyway.
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

from battle_engine.ruleset_policy import BYTEFRAY_RULESET_V4_ID

from tools.research.v5.analyzer import analyze_match
from tools.research.v5.corpus_runner import run_single_match
from tools.research.v5.r4_population import (
    ARENA_SIZE,
    DEVELOPMENT_SEEDS,
    EVALUATION_SEEDS,
    MAX_TICKS,
    QUALIFICATION_FIXTURES,
    R4_POPULATION,
    R4_POPULATION_IDS,
    build_population_manifest,
    load_research_agent_specs,
    population_fingerprints,
)

# Candidates that must pass the competence gate before the population is
# frozen. ``v4_quorum`` is a retained bundled agent whose behaviour R3 already
# characterised from source and measured across 96 matches, but it is put
# through the same fixtures anyway so the admission record is uniform.
R4_CANDIDATES: tuple[str, ...] = R4_POPULATION_IDS


def replay_digests(replay_path: Path) -> dict[str, str]:
    """SHA-256 of the whole replay and of its gameplay tick stream alone."""

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


def _seat_view(analysis: dict[str, Any], seat: str) -> dict[str, Any]:
    """Re-express one match analysis from the point of view of one seat."""

    me = seat
    opp = "B" if seat == "A" else "A"
    winner = analysis["winner"]
    return {
        "result": "win" if winner == me else ("loss" if winner == opp else "tie"),
        "ticks": analysis["actual_ticks"],
        "is_timeout": analysis["is_timeout"],
        "is_tie": analysis["is_tie"],
        "captured_opponent": analysis["core_capture_outcome"].get(opp) == "captured",
        "own_core_captured": analysis["core_capture_outcome"].get(me) == "captured",
        "made_contact": analysis["first_contact_tick_by_entrant"].get(me) is not None,
        "first_contact_tick": analysis["first_contact_tick_by_entrant"].get(me),
        "writes_expanded": analysis["writes_expanded"].get(me, 0),
        "unique_write_addresses": analysis["unique_write_addresses"].get(me, 0),
        "hostile_writes": analysis["hostile_writes_expanded"].get(me, 0),
        "unique_hostile_addresses": analysis["unique_hostile_write_addresses"].get(me, 0),
        "enemy_core_writes": analysis["enemy_core_writes_expanded"].get(me, 0),
        "enemy_core_cells_targeted": analysis["unique_enemy_core_cells_targeted"].get(me, 0),
        "enemy_core_cells_damaged": analysis["unique_enemy_core_cells_damaged"].get(me, 0),
        "max_deficit_inflicted": analysis["max_core_deficit"].get(opp, 0),
        "deficit_area_inflicted": analysis["core_deficit_area"].get(opp, 0),
        "max_deficit_suffered": analysis["max_core_deficit"].get(me, 0),
        "own_core_cells_written": analysis["distinct_own_core_cells_written"].get(me, 0),
        "own_core_cells_lost": analysis["distinct_own_core_cells_ever_lost"].get(me, 0),
        "max_displacement": analysis["max_displacement_from_core"].get(me, 0),
        "disruptions_received": analysis["total_disruptions_received"].get(me, 0),
        "attack_episodes": analysis["attack_episodes"].get(me, 0),
        "max_cells_per_episode": analysis["max_distinct_core_cells_per_attack_episode"].get(me, 0),
        "ticks_contact_to_first_core_damage": analysis[
            "ticks_contact_to_first_core_damage"
        ].get(me),
        "process_count": analysis["declared_process_count"].get(me, 0),
    }


def run_pair(
    data_root: Path,
    agent_a: str,
    agent_b: str,
    seed: int,
    out_dir: Path,
    specs: dict[str, Any],
) -> dict[str, Any]:
    """Execute one match and return its full analysis plus replay digests."""

    replay_path, result_path, _ = run_single_match(
        data_root,
        agent_a,
        agent_b,
        seed,
        out_dir,
        arena_size=ARENA_SIZE,
        max_ticks=MAX_TICKS,
        ruleset_id=BYTEFRAY_RULESET_V4_ID,
        with_trace=False,
        agent_specs=specs,
    )
    analysis = analyze_match(replay_path, result_path)
    analysis.update(
        agent_a=agent_a, agent_b=agent_b, seed=seed, **replay_digests(replay_path)
    )
    return analysis


# -- Stage R4B: competence qualification (development seeds only) ---------


def run_qualification(
    data_root: Path,
    output_root: Path,
    *,
    candidates: tuple[str, ...] = R4_CANDIDATES,
    fixtures: tuple[str, ...] = QUALIFICATION_FIXTURES,
    seeds: tuple[int, ...] = DEVELOPMENT_SEEDS,
) -> dict[str, Any]:
    """Every candidate against every fixture, both slot orders, dev seeds."""

    assert not (set(seeds) & set(EVALUATION_SEEDS)), (
        "qualification must never touch an evaluation seed"
    )
    output_root.mkdir(parents=True, exist_ok=True)
    specs = load_research_agent_specs()
    per_candidate: dict[str, list[dict[str, Any]]] = {c: [] for c in candidates}
    start = time.perf_counter()
    done = 0

    for candidate in candidates:
        for fixture in fixtures:
            for seed in seeds:
                for seat in ("A", "B"):
                    a = candidate if seat == "A" else fixture
                    b = fixture if seat == "A" else candidate
                    label = f"{candidate}__vs__{fixture}__seed_{seed}__seat_{seat}"
                    analysis = run_pair(
                        data_root, a, b, seed, output_root / label, specs
                    )
                    row = _seat_view(analysis, seat)
                    row.update(
                        candidate=candidate, fixture=fixture, seed=seed, seat=seat,
                        match_label=label,
                    )
                    per_candidate[candidate].append(row)
                    done += 1
        print(
            f"  qualified {candidate}: {done} runs "
            f"({time.perf_counter() - start:.1f}s)"
        )

    return {
        "stage": "R4B qualification",
        "seeds": list(seeds),
        "seed_class": "development",
        "fixtures": list(fixtures),
        "ruleset_id": BYTEFRAY_RULESET_V4_ID,
        "arena_size": ARENA_SIZE,
        "max_ticks": MAX_TICKS,
        "runs": per_candidate,
        "verdicts": {c: competence_verdict(c, per_candidate[c]) for c in candidates},
    }


def competence_verdict(candidate: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Score one candidate against its archetype-appropriate gate.

    R4 charter Section 12: the gate is never "must win". It is "the intended
    strategy demonstrably functions under stable V4". Each archetype is
    measured on the criteria that make sense for it, not forced through one
    identical metric.
    """

    archetype = next(
        m["archetype"] for m in R4_POPULATION if m["identifier"] == candidate
    )
    n = len(rows)
    contact = [r for r in rows if r["made_contact"]]
    checks: dict[str, dict[str, Any]] = {}

    def check(name: str, passed: bool, observed: Any, requirement: str) -> None:
        checks[name] = {
            "passed": bool(passed),
            "observed": observed,
            "requirement": requirement,
        }

    made_contact = len(contact)
    captures = sum(1 for r in rows if r["captured_opponent"])
    multi_addr = sum(1 for r in contact if r["unique_hostile_addresses"] > 1)
    multi_cell = sum(1 for r in contact if r["enemy_core_cells_damaged"] >= 2)
    max_cells = max((r["enemy_core_cells_damaged"] for r in rows), default=0)
    moved = sum(1 for r in rows if r["max_displacement"] > 0)
    mean_disp = sum(r["max_displacement"] for r in rows) / max(1, n)
    own_cover = max((r["own_core_cells_written"] for r in rows), default=0)
    mean_own_cover = sum(r["own_core_cells_written"] for r in rows) / max(1, n)
    mean_uniq_writes = sum(r["unique_write_addresses"] for r in rows) / max(1, n)

    offensive = archetype.startswith(("A", "B", "D", "F"))
    defensive = archetype.startswith(("C", "D", "F"))
    mobile = archetype.startswith(("B", "E"))
    territorial = archetype.startswith("E")

    check(
        "acquires_legal_contact",
        made_contact > 0,
        f"{made_contact}/{n} runs made contact",
        "at least one development run establishes legal enemy contact",
    )

    if offensive:
        check(
            "multi_address_pressure",
            multi_addr > 0,
            f"{multi_addr}/{len(contact)} contact runs wrote >1 hostile address",
            "regional attack produces more than one useful hostile address",
        )
        check(
            "multi_core_cell_pressure",
            multi_cell > 0,
            f"{multi_cell}/{len(contact)} contact runs damaged >=2 core cells; "
            f"max {max_cells}",
            "demonstrates at least some multi-core-cell pressure",
        )
        check(
            "real_core_capture",
            captures > 0,
            f"{captures}/{n} runs achieved an outright core capture",
            "achieves a real core capture in at least one legal non-contrived run",
        )

    if mobile:
        check(
            "actually_moves",
            moved == n and mean_disp > ARENA_SIZE / 16,
            f"{moved}/{n} runs displaced; mean max displacement {mean_disp:.1f}",
            "moves in every run and builds a real search footprint",
        )

    if archetype.startswith("B"):
        check(
            "contact_to_attack_transition",
            sum(
                1
                for r in contact
                if r["ticks_contact_to_first_core_damage"] is not None
            )
            > 0,
            f"{sum(1 for r in contact if r['ticks_contact_to_first_core_damage'] is not None)}"
            f"/{len(contact)} contact runs converted contact into core damage",
            "transitions from contact to meaningful attack",
        )

    if defensive:
        check(
            "defends_objective_region",
            own_cover > 2,
            f"max {own_cover} distinct own core cells written; "
            f"mean {mean_own_cover:.2f} (bundled v4_local_defender: 2)",
            "interacts with more of its own core than the bundled two-address behaviour",
        )
        # A defender that stops defending the moment an opponent stands next
        # to it is not objective-capable. Measured on the runs where it
        # actually came under pressure, not on the population average: the
        # first draft of the warden passed the coverage check above on one
        # fixture while repairing nothing at all in the three others.
        pressured = [r for r in rows if r["own_core_cells_lost"] > 0]
        repaired = [r for r in pressured if r["own_core_cells_written"] > 0]
        check(
            "responds_to_pressure",
            len(pressured) == 0 or len(repaired) * 2 >= len(pressured),
            f"repaired own core in {len(repaired)}/{len(pressured)} runs "
            "where it lost at least one own core cell",
            "repairs its objective region in the majority of runs where it is damaged",
        )

    if territorial:
        check(
            "spatial_spread",
            mean_uniq_writes > 32,
            f"mean {mean_uniq_writes:.1f} unique write addresses per run",
            "demonstrates meaningful spatial spread",
        )
        check(
            "legal_conversion_path_after_contact",
            sum(1 for r in contact if r["enemy_core_writes"] > 0) > 0,
            f"{sum(1 for r in contact if r['enemy_core_writes'] > 0)}/{len(contact)} "
            "contact runs produced enemy-core writes",
            "still possesses a legal path to core attack after contact",
        )

    if archetype.startswith("F"):
        check(
            "multi_process_roles_active",
            all(r["process_count"] == 6 for r in rows),
            f"declared process count {sorted({r['process_count'] for r in rows})}",
            "declared multi-process configuration is present in every run",
        )

    return {
        "candidate": candidate,
        "archetype": archetype,
        "runs": n,
        "admitted": all(c["passed"] for c in checks.values()),
        "checks": checks,
        "summary": {
            "contact_runs": made_contact,
            "captures": captures,
            "max_enemy_core_cells_damaged": max_cells,
            "mean_max_displacement": round(mean_disp, 1),
            "max_own_core_cells_written": own_cover,
            "mean_unique_write_addresses": round(mean_uniq_writes, 1),
        },
    }


# -- Stage R4C: evaluation corpus (Phase 0's seeds, frozen population) ----


def build_evaluation_pairings(
    population: tuple[str, ...] = R4_POPULATION_IDS,
    seeds: tuple[int, ...] = EVALUATION_SEEDS,
) -> list[dict[str, Any]]:
    """Phase 0's corpus shape: full ordered round-robin including self-play."""

    pairings = []
    for agent_a in population:
        for agent_b in population:
            for seed in seeds:
                pairings.append(
                    {
                        "match_label": f"{agent_a}__vs__{agent_b}__seed_{seed}",
                        "agent_a": agent_a,
                        "agent_b": agent_b,
                        "seed": seed,
                    }
                )
    return pairings


def run_evaluation(
    data_root: Path,
    output_root: Path,
    *,
    pairings: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Execute the frozen R4 evaluation corpus."""

    rows = pairings if pairings is not None else build_evaluation_pairings()
    output_root.mkdir(parents=True, exist_ok=True)
    specs = load_research_agent_specs()
    metrics: list[dict[str, Any]] = []
    start = time.perf_counter()

    for index, row in enumerate(rows, start=1):
        analysis = run_pair(
            data_root,
            row["agent_a"],
            row["agent_b"],
            row["seed"],
            output_root / row["match_label"],
            specs,
        )
        analysis["match_label"] = row["match_label"]
        metrics.append(analysis)
        if index % 36 == 0 or index == len(rows):
            elapsed = time.perf_counter() - start
            print(
                f"  {index}/{len(rows)} matches ({elapsed:.1f}s, "
                f"{index / max(0.1, elapsed):.1f}/s)"
            )

    with open(output_root / "r4_evaluation_metrics.jsonl", "w", encoding="utf-8") as f:
        f.writelines(json.dumps(m, sort_keys=True) + "\n" for m in metrics)
    return {"total_matches": len(metrics), "metrics_path": str(output_root)}


def main() -> None:
    parser = argparse.ArgumentParser(description="Run V5 Phase R4 stages.")
    parser.add_argument(
        "--stage", choices=("manifest", "qualification", "evaluation"), required=True
    )
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    if args.stage == "manifest":
        out = args.output or REPO_ROOT / "runs" / "v5_r4_population"
        out.mkdir(parents=True, exist_ok=True)
        manifest = build_population_manifest()
        path = out / "r4_population_manifest.json"
        path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
        print(f"Wrote {path}")
        for entrant in manifest["entrants"]:
            print(
                f"  {entrant['identifier']:26s} {entrant['archetype'][:44]:46s} "
                f"procs={entrant['process_count']} fp={entrant['source_fingerprint'][:12]}"
            )
        return

    if args.stage == "qualification":
        out = args.output or REPO_ROOT / "runs" / "v5_r4_qualification"
        report = run_qualification(REPO_ROOT, out)
        (out / "r4_qualification.json").write_text(
            json.dumps(report, indent=2, sort_keys=True), encoding="utf-8"
        )
        print("\n=== R4B qualification verdicts (development seeds only) ===")
        for candidate, verdict in report["verdicts"].items():
            flag = "ADMIT" if verdict["admitted"] else "REJECT"
            print(f"  [{flag}] {candidate:26s} {verdict['archetype']}")
            for name, check in sorted(verdict["checks"].items()):
                mark = "ok " if check["passed"] else "FAIL"
                print(f"        {mark} {name:36s} {check['observed']}")
        return

    out = args.output or REPO_ROOT / "runs" / "v5_r4_evaluation"
    print(
        "Frozen population fingerprints:\n"
        + "\n".join(
            f"  {k:26s} {v}" for k, v in sorted(population_fingerprints().items())
        )
    )
    summary = run_evaluation(REPO_ROOT, out)
    print(f"\nR4C evaluation complete: {summary['total_matches']} matches")


if __name__ == "__main__":
    main()
