"""V6 Consolidated Research Experiment Harness & Analysis (Phases 7, 8, 9).

Provides a single reusable research runner, provenance recorder, and analyzer
abstraction for V6 research protocols.

Key guarantees:
1. Benchmark corpus reproducibility: resolves benchmark agents from tracked repository fixtures
   (tools/research/v6/fixtures/agents, battle_engine/data/starter_agents, tracked agents).
2. Provenance recording: every experiment records Git SHA, dirty status, ruleset ID, harness ID,
   benchmark fingerprints, and runtime environment.
3. Unified runner: runs configurable round-robin / pairwise experiments across arena sizes,
   seeds, and orientations; tracks decisive wins, losses, ties, seat-conditioned results,
   termination reasons, and decision ticks.
4. Defensible metrics (replaces misleading σ²_opp):
   - Computes global 1D entrant ratings/win-rates under a transitive baseline.
   - Measures matchup residuals R_{ij} = W_{ij} - Ŵ_{ij} to detect matchup-specific effects.
   - Reports upset reversals and intransitive 3-cycles explicitly.
   - Separates decisive outcomes from ties.
   - Aggregates over seeds honestly without treating deterministic duplicates as independent trials.
"""

from __future__ import annotations

import json
import math
import platform
import shutil
import subprocess
import time
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]

from battle_engine.agent_api import AgentManifestError
from battle_engine.agent_revisions import (
    agent_revision_fingerprint,
    agent_revision_id,
)
from battle_engine.agents import AgentSpec, agent_spec_from_dir, resolve_agent
from battle_engine.evaluation_contracts import STANDARD_V4_SEEDS
from battle_engine.evaluation_service import EvaluationRequest, EvaluationService
from battle_engine.ruleset_policy import (
    BYTEFRAY_RULESET_V4_ID,
)

# Canonical V6 benchmark corpus
V6_BENCH_8: tuple[str, ...] = (
    "Octave",
    "nemesis_alpha2",
    "v5_scout_striker",
    "v5_region_attacker",
    "v5_dual_team",
    "v4_claimer",
    "v5_core_defender",
    "v4_local_defender",
)

TRACKED_BENCHMARK_SOURCE_DIRS: tuple[Path, ...] = (
    REPO_ROOT / "tools" / "research" / "v6" / "fixtures" / "agents",
    REPO_ROOT / "engine" / "src" / "battle_engine" / "data" / "starter_agents",
)


def get_git_provenance(repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    """Capture authoritative source version and tree status."""
    try:
        sha = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True, cwd=repo_root
        ).strip()
    except Exception:
        sha = "unknown"

    try:
        status = subprocess.check_output(
            ["git", "status", "--porcelain"], text=True, cwd=repo_root
        ).strip()
        is_dirty = len(status) > 0
    except Exception:
        is_dirty = True

    return {
        "git_sha": sha,
        "git_dirty": is_dirty,
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "timestamp_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }


def find_tracked_agent_source(name: str) -> Path | None:
    """Find agent in tracked repository locations."""
    for base in TRACKED_BENCHMARK_SOURCE_DIRS:
        agent_dir = base / name
        if agent_dir.is_dir():
            try:
                spec = agent_spec_from_dir(agent_dir)
                if spec is not None:
                    return agent_dir
            except AgentManifestError:
                continue
    return None


def prepare_benchmark_data_root(dest_root: Path, field: Sequence[str]) -> Path:
    """Copy tracked benchmark agents into dest_root/agents so evaluation runs self-contained."""
    agents_dir = dest_root / "agents"
    agents_dir.mkdir(parents=True, exist_ok=True)
    for name in field:
        target = agents_dir / name
        if target.exists():
            continue
        source = find_tracked_agent_source(name)
        if source is None:
            raise FileNotFoundError(
                f"Tracked benchmark agent {name!r} not found in {TRACKED_BENCHMARK_SOURCE_DIRS}"
            )
        shutil.copytree(source, target)
    return dest_root


def fingerprint_corpus(field: Sequence[str], data_root: Path | None = None) -> dict[str, dict[str, str]]:
    """Record content-addressed revision fingerprints for all entrants in corpus."""
    out: dict[str, dict[str, str]] = {}
    for name in field:
        spec: AgentSpec | None = None
        if data_root is not None:
            spec = resolve_agent(data_root, name)
            source_dir = spec.dir
        else:
            source = find_tracked_agent_source(name)
            if source is None:
                raise FileNotFoundError(f"Agent {name!r} not found in tracked benchmark sources")
            source_dir = source
            spec = agent_spec_from_dir(source_dir)

        fingerprint = agent_revision_fingerprint(source_dir)
        if fingerprint is None:
            raise RuntimeError(f"Agent {name!r} has no computable revision fingerprint")
        out[name] = {
            "path": str(source_dir),
            "kind": spec.kind if spec else "unknown",
            "api_version": str(spec.api_version) if spec else "unknown",
            "fingerprint": fingerprint,
            "agent_revision_id": agent_revision_id(fingerprint),
        }
    return out


@dataclass(frozen=True)
class ResearchExperimentConfig:
    experiment_id: str
    ruleset_id: str = BYTEFRAY_RULESET_V4_ID
    arena_sizes: tuple[int, ...] = (512,)
    field: tuple[str, ...] = V6_BENCH_8
    seeds: tuple[int, ...] = STANDARD_V4_SEEDS
    ticks: int = 1000
    both_orientations: bool = True
    output_dir: Path | None = None
    workers: int = 1
    scheduler_chunk_size: int | None = None
    scheduler_rotate_start: bool | None = None


def run_experiment(config: ResearchExperimentConfig) -> dict[str, Any]:
    """Execute a complete research protocol condition and return structured data with provenance."""
    out_dir = config.output_dir or (REPO_ROOT / "runs" / config.experiment_id)
    out_dir.mkdir(parents=True, exist_ok=True)

    data_root = prepare_benchmark_data_root(out_dir / "env", config.field)
    agent_fingerprints = fingerprint_corpus(config.field, data_root)
    provenance = get_git_provenance()
    provenance.update(
        {
            "experiment_id": config.experiment_id,
            "ruleset_id": config.ruleset_id,
            "agent_fingerprints": agent_fingerprints,
            "config": {
                "arena_sizes": list(config.arena_sizes),
                "seeds": list(config.seeds),
                "ticks": config.ticks,
                "both_orientations": config.both_orientations,
                "field": list(config.field),
            },
        }
    )

    (out_dir / "provenance.json").write_text(
        json.dumps(provenance, indent=2, sort_keys=True), encoding="utf-8"
    )

    conditions_results: list[dict[str, Any]] = []

    for arena_size in config.arena_sizes:
        cond_dir = out_dir / f"arena_{arena_size}"
        cond_dir.mkdir(parents=True, exist_ok=True)

        cells_data: list[dict[str, Any]] = []
        started = time.monotonic()

        # Triangular sequence of evaluation requests covering all pairs
        for i, candidate in enumerate(config.field):
            opponents = config.field[i + 1 :]
            if not opponents:
                continue

            req = EvaluationRequest(
                candidate_id=candidate,
                opponent_ids=opponents,
                seeds=config.seeds,
                output_dir=cond_dir / f"{i:02d}-{candidate}",
                ticks=config.ticks,
                ruleset_id=config.ruleset_id,
                arena_size=arena_size,
                both_orientations=config.both_orientations,
                data_root=data_root,
                resume=True,
                workers=config.workers,
                scheduler_chunk_size=config.scheduler_chunk_size,
                scheduler_rotate_start=config.scheduler_rotate_start,
            )

            service = EvaluationService()
            eval_result = service.run(req)

            for cell in eval_result.cells:
                term_reason = getattr(cell, "error_code", None)
                if not term_reason and cell.artifact_dir:
                    res_file = cell.artifact_dir / "result.json"
                    if res_file.is_file():
                        try:
                            res_json = json.loads(res_file.read_text(encoding="utf-8"))
                            term_reason = res_json.get("termination_reason")
                        except Exception:
                            pass
                if not term_reason:
                    term_reason = (
                        "tick_limit"
                        if (cell.ticks_run is not None and cell.ticks_run >= config.ticks)
                        else "completed"
                    )

                # Cell details
                cells_data.append(
                    {
                        "schedule_id": cell.schedule_id,
                        "subject_role": cell.subject_role,
                        "subject_id": cell.subject_id,
                        "opponent_id": cell.opponent_id,
                        "seed": cell.seed,
                        "orientation": cell.orientation,
                        "status": cell.status,
                        "outcome": cell.outcome,
                        "ticks_run": cell.ticks_run,
                        "score_subject": cell.score_subject,
                        "score_opponent": cell.score_opponent,
                        "territory_subject": cell.territory_subject,
                        "territory_opponent": cell.territory_opponent,
                        "termination_reason": term_reason,
                    }
                )

        wall_clock = time.monotonic() - started
        condition_record = {
            "arena_size": arena_size,
            "wall_clock_seconds": wall_clock,
            "cells": cells_data,
        }
        conditions_results.append(condition_record)

    full_result = {
        "provenance": provenance,
        "conditions": conditions_results,
    }
    (out_dir / "experiment_result.json").write_text(
        json.dumps(full_result, indent=2, sort_keys=True), encoding="utf-8"
    )
    return full_result


# ---------------------------------------------------------------------------
# Defensible Metrics & Analysis (Phase 9)
# ---------------------------------------------------------------------------


def compute_pairwise_record(
    cells: Sequence[dict[str, Any]], field: Sequence[str]
) -> dict[tuple[str, str], dict[str, Any]]:
    """Compute decisive wins, losses, ties, seat-conditioned stats, and per-seed
    matchup records for each ordered pair (A, B).
    """
    table: dict[tuple[str, str], dict[str, Any]] = {
        (a, b): {
            "wins": 0,
            "losses": 0,
            "ties": 0,
            "played": 0,
            "seat_a_wins": 0,
            "seat_b_wins": 0,
            "seeds": {},
        }
        for a in field
        for b in field
        if a != b
    }

    for c in cells:
        subj = c["subject_id"]
        opp = c["opponent_id"]
        outcome = c.get("outcome")
        seed = c.get("seed", 0)
        if (subj, opp) not in table:
            continue

        rec = table[(subj, opp)]
        opp_rec = table[(opp, subj)]
        rec["played"] += 1
        opp_rec["played"] += 1

        if seed not in rec["seeds"]:
            rec["seeds"][seed] = {"wins": 0, "losses": 0, "ties": 0, "played": 0}
        if seed not in opp_rec["seeds"]:
            opp_rec["seeds"][seed] = {"wins": 0, "losses": 0, "ties": 0, "played": 0}

        rec["seeds"][seed]["played"] += 1
        opp_rec["seeds"][seed]["played"] += 1

        is_subject_seat_a = c.get("orientation") != "opponent_first"

        if outcome == "win":
            rec["wins"] += 1
            opp_rec["losses"] += 1
            rec["seeds"][seed]["wins"] += 1
            opp_rec["seeds"][seed]["losses"] += 1
            if is_subject_seat_a:
                rec["seat_a_wins"] += 1
            else:
                rec["seat_b_wins"] += 1
        elif outcome == "loss":
            rec["losses"] += 1
            opp_rec["wins"] += 1
            rec["seeds"][seed]["losses"] += 1
            opp_rec["seeds"][seed]["wins"] += 1
            if is_subject_seat_a:
                opp_rec["seat_b_wins"] += 1
            else:
                opp_rec["seat_a_wins"] += 1
        elif outcome == "tie":
            rec["ties"] += 1
            opp_rec["ties"] += 1
            rec["seeds"][seed]["ties"] += 1
            opp_rec["seeds"][seed]["ties"] += 1

    return table


def _seed_aggregated_winrate(rec: dict[str, Any]) -> float:
    """Aggregate honestly over unique seeds: computes win rate per distinct seed,
    then averages across seeds so deterministic duplicate seeds never inflate effective sample size.
    """
    seeds = rec.get("seeds", {})
    if seeds:
        seed_rates = [
            (s_rec["wins"] + 0.5 * s_rec["ties"]) / s_rec["played"]
            for s_rec in seeds.values()
            if s_rec["played"] > 0
        ]
        return sum(seed_rates) / len(seed_rates) if seed_rates else 0.5
    played = rec.get("played", 0)
    return (rec.get("wins", 0) + 0.5 * rec.get("ties", 0)) / played if played > 0 else 0.5


def fit_bradley_terry_ratings(
    pairwise: dict[tuple[str, str], dict[str, Any]],
    field: Sequence[str],
    iterations: int = 50,
) -> tuple[dict[str, float], dict[str, float]]:
    """Fit a single global transitive Bradley-Terry model.

    Produces:
    - latent positive strength parameters p_i (normalized so sum(p_i) = 1.0)
    - standard Elo-scale ratings r_i = 1500 + 400 * log10(p_i / (1/N))

    Under this model, the expected win rate of entrant i against entrant j is:
        Ŵ_{ij} = p_i / (p_i + p_j) = 1 / (1 + 10^((r_j - r_i)/400))

    Uses iterative scaling with Laplace smoothing (0.5 pseudo-win per matchup)
    to guarantee finite ratings and robust convergence even in deterministic blowout scenarios.
    """
    n_field = len(field)
    if n_field == 0:
        return {}, {}
    p = {name: 1.0 / n_field for name in field}

    pairwise_w: dict[tuple[str, str], float] = {}
    pairwise_n: dict[tuple[str, str], float] = {}
    for a in field:
        for b in field:
            if a == b:
                continue
            rec = pairwise.get((a, b), {})
            w_rate = _seed_aggregated_winrate(rec)
            seeds = rec.get("seeds", {})
            n_eff = float(len(seeds)) if seeds else (float(rec.get("played", 0)) if rec.get("played", 0) > 0 else 1.0)
            pairwise_w[(a, b)] = w_rate * n_eff
            pairwise_n[(a, b)] = n_eff

    smoothing = 0.01
    for _ in range(iterations):
        p_next: dict[str, float] = {}
        for a in field:
            w_a = 0.0
            denom = 0.0
            for b in field:
                if a == b:
                    continue
                w = pairwise_w.get((a, b), 0.0) + smoothing
                n = pairwise_n.get((a, b), 0.0) + 2 * smoothing
                w_a += w
                denom += n / (p[a] + p[b])
            p_next[a] = w_a / denom if denom > 0 else p[a]
        scale = sum(p_next.values())
        if scale > 0:
            p = {k: v / scale for k, v in p_next.items()}

    avg_p = 1.0 / n_field
    ratings: dict[str, float] = {}
    for name in field:
        ratio = max(1e-6, p[name] / avg_p)
        ratings[name] = round(1500.0 + 400.0 * math.log10(ratio), 2)

    return p, ratings


def compute_global_ratings(
    pairwise: dict[tuple[str, str], dict[str, Any]], field: Sequence[str]
) -> dict[str, float]:
    """Fit a single global empirical rating for each entrant under the Bradley-Terry model."""
    _, ratings = fit_bradley_terry_ratings(pairwise, field)
    return ratings


def compute_matchup_residuals(
    pairwise: dict[tuple[str, str], dict[str, Any]],
    field: Sequence[str],
    strengths: dict[str, float],
) -> dict[str, Any]:
    """Measure matchup residuals from the global 1D transitive model.

    Under Bradley-Terry:
        Expected win rate Ŵ_{ij} = p_i / (p_i + p_j)
    Residual:
        R_{ij} = W_{ij} - Ŵ_{ij}
    Root Mean Square Residual (RMSR) measures the overall departure from transitivity.
    For purely transitive rankings, RMSR ≈ 0; for cyclic counterplay, RMSR is high.
    """
    residuals: dict[str, float] = {}
    squared_errors: list[float] = []

    for a in field:
        for b in field:
            if a >= b:
                continue
            rec = pairwise.get((a, b), {})
            played = rec.get("played", 0)
            if played == 0:
                continue
            observed = _seed_aggregated_winrate(rec)
            p_a = strengths.get(a, 1.0)
            p_b = strengths.get(b, 1.0)
            expected = p_a / (p_a + p_b) if (p_a + p_b) > 0 else 0.5
            diff = observed - expected
            residuals[f"{a}_vs_{b}"] = round(diff, 4)
            squared_errors.append(diff**2)

    rmsr = math.sqrt(sum(squared_errors) / len(squared_errors)) if squared_errors else 0.0
    return {
        "residuals": residuals,
        "rmsr": round(rmsr, 4),
    }


def compute_upset_reversals(
    pairwise: dict[tuple[str, str], dict[str, Any]],
    field: Sequence[str],
    ratings: dict[str, float],
    elo_threshold: float = 20.0,
) -> list[dict[str, Any]]:
    """Identify genuine upsets/reversals: cases where entrant j beats entrant i head-to-head
    despite entrant i having a significantly higher global rating (rating_i - rating_j > elo_threshold).
    """
    reversals = []
    for a in field:
        for b in field:
            if a >= b:
                continue
            higher, lower = (a, b) if ratings.get(a, 1500.0) >= ratings.get(b, 1500.0) else (b, a)
            rec = pairwise.get((lower, higher), {})
            played = rec.get("played", 0)
            if played == 0:
                continue
            lower_winrate = _seed_aggregated_winrate(rec)
            higher_rating = ratings.get(higher, 1500.0)
            lower_rating = ratings.get(lower, 1500.0)
            if lower_winrate > 0.5 and (higher_rating - lower_rating) > elo_threshold:
                reversals.append(
                    {
                        "underdog": lower,
                        "favorite": higher,
                        "underdog_rating": lower_rating,
                        "favorite_rating": higher_rating,
                        "underdog_winrate": round(lower_winrate, 3),
                        "head_to_head": f"{rec.get('wins', 0)}-{rec.get('losses', 0)}-{rec.get('ties', 0)}",
                    }
                )
    return reversals


def compute_intransitive_3_cycles(
    pairwise: dict[tuple[str, str], dict[str, Any]],
    field: Sequence[str],
    dominance_threshold: float = 0.55,
) -> list[tuple[str, str, str]]:
    """Detect directed 3-cycles A -> B -> C -> A where win rate exceeds dominance_threshold."""
    edges: set[tuple[str, str]] = set()
    for (a, b), rec in pairwise.items():
        played = rec.get("played", 0)
        if played == 0:
            continue
        rate = _seed_aggregated_winrate(rec)
        if rate > dominance_threshold:
            edges.add((a, b))

    cycles: list[tuple[str, str, str]] = []
    for a, b, c in combinations(field, 3):
        for x, y, z in ((a, b, c), (a, c, b)):
            if (x, y) in edges and (y, z) in edges and (z, x) in edges:
                cycles.append((x, y, z))
    return cycles


def bootstrap_rmsr_over_seeds(
    cells: Sequence[dict[str, Any]],
    field: Sequence[str],
    n_bootstraps: int = 100,
) -> float:
    """Bootstrap resample over distinct seeds to compute standard error of RMSR
    without pretending deterministic duplicate matches are independent evidence.
    """
    distinct_seeds: list[int] = sorted(
        {int(c["seed"]) for c in cells if c.get("seed") is not None}
    )
    if len(distinct_seeds) < 2:
        return 0.0

    # Group cells by seed
    by_seed: dict[Any, list[dict[str, Any]]] = {}
    for c in cells:
        s = c.get("seed")
        by_seed.setdefault(s, []).append(c)

    import random

    rng = random.Random(42)
    boot_rmsrs: list[float] = []

    for _ in range(n_bootstraps):
        sampled_seeds = [rng.choice(distinct_seeds) for _ in range(len(distinct_seeds))]
        sampled_cells: list[dict[str, Any]] = []
        for s in sampled_seeds:
            sampled_cells.extend(by_seed.get(s, []))

        pairwise = compute_pairwise_record(sampled_cells, field)
        strengths, _ = fit_bradley_terry_ratings(pairwise, field, iterations=25)
        res_info = compute_matchup_residuals(pairwise, field, strengths)
        boot_rmsrs.append(res_info["rmsr"])

    mean_rmsr = sum(boot_rmsrs) / len(boot_rmsrs)
    var = sum((r - mean_rmsr) ** 2 for r in boot_rmsrs) / max(1, len(boot_rmsrs) - 1)
    return round(math.sqrt(var), 4)


def analyze_experiment_condition(cells: Sequence[dict[str, Any]], field: Sequence[str]) -> dict[str, Any]:
    """Run comprehensive analysis on one condition, computing defensible metrics."""
    pairwise = compute_pairwise_record(cells, field)
    strengths, ratings = fit_bradley_terry_ratings(pairwise, field)
    residuals_info = compute_matchup_residuals(pairwise, field, strengths)
    upsets = compute_upset_reversals(pairwise, field, ratings)
    cycles = compute_intransitive_3_cycles(pairwise, field)
    boot_std = bootstrap_rmsr_over_seeds(cells, field)

    total_matches = len(cells)
    decisive_wins = sum(1 for c in cells if c.get("outcome") == "win")
    ties = sum(1 for c in cells if c.get("outcome") == "tie")
    tie_rate = ties / total_matches if total_matches > 0 else 0.0

    ticks = [c["ticks_run"] for c in cells if c.get("ticks_run") is not None]
    median_tick = sorted(ticks)[len(ticks) // 2] if ticks else 0

    return {
        "total_cells": total_matches,
        "decisive_wins": decisive_wins,
        "ties": ties,
        "tie_rate": round(tie_rate, 4),
        "median_decision_tick": median_tick,
        "global_ratings": ratings,
        "bradley_terry_strengths": strengths,
        "matchup_rmsr": residuals_info["rmsr"],
        "matchup_residuals": residuals_info["residuals"],
        "rmsr_bootstrap_std": boot_std,
        "upset_reversals": upsets,
        "intransitive_3_cycles": cycles,
        "intransitive_cycle_count": len(cycles),
    }
