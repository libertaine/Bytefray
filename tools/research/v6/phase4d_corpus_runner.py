"""V6 Phase 4D proportional movement study -- corpus runner.

Runs the frozen V6-Bench-8 field through the real production evaluation
harness (``battle_engine.evaluation_service.EvaluationService``) under the
V6 Phase 4D proportional movement research Ruleset
(``bytefray-rules-6-research-scale-move-proportional``), producing genuine,
fully-provenanced evaluation artifacts -- never hand-built fixtures.

A full round-robin field cannot be expressed as a single ``EvaluationRequest``
(that type is one candidate vs. N opponents, a star topology); this module
decomposes an 8-agent round robin into exactly the triangular sequence of
"star" requests that reproduces every unordered pair exactly once:

    for i, candidate in enumerate(field):
        opponents = field[i + 1:]

For N=8 this yields 7+6+5+4+3+2+1 = 28 requests whose union is exactly the
28 unordered pairs specified -- each request covers its own opponents x seeds
x both-orientations cells, so no separate matrix-building code is needed;
``EvaluationService``/``EvaluationRequest`` generate the exact seeded-placement
methodology matrix used everywhere else in this Ruleset's evaluation, byte for byte.

Usage:
    python -m tools.research.v6.phase4d_corpus_runner fingerprints
    python -m tools.research.v6.phase4d_corpus_runner smoke
    python -m tools.research.v6.phase4d_corpus_runner equivalence
    python -m tools.research.v6.phase4d_corpus_runner sweep --arena-size 512
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "engine" / "src"))

from battle_engine.agent_revisions import (
    agent_revision_fingerprint,
    agent_revision_id,
)
from battle_engine.agents import resolve_agent
from battle_engine.evaluation_contracts import STANDARD_V4_SEEDS
from battle_engine.evaluation_service import EvaluationRequest, EvaluationService
from battle_engine.paths import get_data_root
from battle_engine.ruleset_policy import (
    BYTEFRAY_RULESET_V6_RESEARCH_SCALE_ID,
    BYTEFRAY_RULESET_V6_RESEARCH_SCALE_MOVE_PROPORTIONAL_ID,
)

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

# Task Section 18 Smoke Gate: mobile agents with clearly different authored

# movement patterns plus one stationary agent
SMOKE_FIELD: tuple[str, ...] = (
    "v5_scout_striker",
    "v5_dual_team",
    "v4_claimer",
    "nemesis_alpha2",
)


TICKS = 1000
ARENA_SIZES: tuple[int, ...] = (512, 1024, 4096, 16384, 65536)

RUNS_ROOT = REPO_ROOT / "runs" / "research_v6_phase4d"
PHASE4B_ROOT = REPO_ROOT / "runs" / "research_v6_phase4b"
PHASE4C_ROOT = REPO_ROOT / "runs" / "research_v6_phase4c"


def _output_dir(*parts: str) -> Path:
    path = RUNS_ROOT.joinpath(*parts)
    path.mkdir(parents=True, exist_ok=True)
    return path


def verify_and_fingerprint_field(field: tuple[str, ...], data_root: Path | None = None) -> dict[str, dict[str, str]]:
    root = data_root if data_root is not None else get_data_root()
    out: dict[str, dict[str, str]] = {}
    for name in field:
        spec = resolve_agent(root, name)
        fingerprint = agent_revision_fingerprint(spec.dir)
        if fingerprint is None:
            raise RuntimeError(f"agent {name!r} at {spec.dir} has no computable revision fingerprint")
        out[name] = {
            "path": str(spec.dir),
            "kind": spec.kind,
            "api_version": str(spec.api_version),
            "fingerprint": fingerprint,
            "agent_revision_id": agent_revision_id(fingerprint),
        }
    return out


def _triangular_pair_requests(
    field: tuple[str, ...],
    *,
    ruleset_id: str,
    arena_size: int | None,
    seeds: tuple[int, ...],
    ticks: int,
    output_root: Path,
    workers: int,
) -> list[EvaluationRequest]:
    requests: list[EvaluationRequest] = []
    for i, candidate in enumerate(field):
        opponents = field[i + 1 :]
        if not opponents:
            continue
        requests.append(
            EvaluationRequest(
                candidate_id=candidate,
                opponent_ids=opponents,
                seeds=seeds,
                output_dir=output_root / f"{i:02d}-{candidate}",
                ticks=ticks,
                ruleset_id=ruleset_id,
                arena_size=arena_size,
                both_orientations=True,
                resume=True,
                workers=workers,
            )
        )
    return requests


def run_round_robin(
    field: tuple[str, ...],
    *,
    ruleset_id: str,
    arena_size: int | None,
    seeds: tuple[int, ...],
    ticks: int,
    output_root: Path,
    workers: int = 1,
) -> dict:
    requests = _triangular_pair_requests(
        field,
        ruleset_id=ruleset_id,
        arena_size=arena_size,
        seeds=seeds,
        ticks=ticks,
        output_root=output_root,
        workers=workers,
    )
    started = time.monotonic()
    per_request: list[dict] = []
    total_cells = 0
    for request in requests:
        service = EvaluationService()
        result = service.run(request)
        total_cells += len(result.cells)
        per_request.append(
            {
                "candidate_id": request.candidate_id,
                "opponent_ids": list(request.opponent_ids),
                "evaluation_id": result.evaluation_id,
                "cells": len(result.cells),
                "completed": sum(1 for c in result.cells if c.status == "completed"),
                "output_dir": str(request.output_dir),
            }
        )
    elapsed = time.monotonic() - started
    return {
        "ruleset_id": ruleset_id,
        "arena_size": arena_size,
        "seeds": list(seeds),
        "ticks": ticks,
        "field": list(field),
        "total_matches": total_cells,
        "wall_clock_seconds": elapsed,
        "requests": per_request,
    }


def cmd_fingerprints(args: argparse.Namespace) -> None:
    out = verify_and_fingerprint_field(V6_BENCH_8)
    _output_dir().mkdir(parents=True, exist_ok=True)
    path = RUNS_ROOT / "v6_bench_8_fingerprints.json"
    path.write_text(json.dumps(out, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(out, indent=2, sort_keys=True))
    print(f"\nwritten: {path}")

    # Verify against Phase 4B fingerprints if present
    p4b_fp_path = PHASE4B_ROOT / "v6_bench_8_fingerprints.json"
    if p4b_fp_path.exists():
        p4b_fps = json.loads(p4b_fp_path.read_text(encoding="utf-8"))
        drift = []
        for name in V6_BENCH_8:
            if out[name]["fingerprint"] != p4b_fps.get(name, {}).get("fingerprint"):
                drift.append(name)
        if drift:
            print(f"WARNING: source drift detected against Phase 4B in agents: {drift}")
        else:
            print("Verified: 0 source drift against Phase 4B benchmark fingerprints.")


def cmd_smoke(args: argparse.Namespace) -> None:
    summary = {"conditions": []}
    for arena_size in (512, 65536):
        output_root = _output_dir("smoke", f"a{arena_size}")
        result = run_round_robin(
            SMOKE_FIELD,
            ruleset_id=BYTEFRAY_RULESET_V6_RESEARCH_SCALE_MOVE_PROPORTIONAL_ID,
            arena_size=arena_size,
            seeds=(1, 2),
            ticks=TICKS,
            output_root=output_root,
        )
        summary["conditions"].append(result)
        print(
            f"[smoke] arena={arena_size}: "
            f"{result['total_matches']} matches in {result['wall_clock_seconds']:.2f}s "
            f"({result['wall_clock_seconds'] / max(result['total_matches'], 1):.3f}s/match)"
        )
    path = RUNS_ROOT / "smoke_summary.json"
    path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    print(f"\nwritten: {path}")


def cmd_equivalence(args: argparse.Namespace) -> None:
    """Run V6-Bench-8 at A=512 under BOTH research-scale (Phase 4B control)
    and research-scale-move-proportional (Phase 4D candidate) -- the direct live
    evidence for the equivalence gate."""
    results = {}
    for ruleset_id, label in (
        (BYTEFRAY_RULESET_V6_RESEARCH_SCALE_ID, "research-scale"),
        (BYTEFRAY_RULESET_V6_RESEARCH_SCALE_MOVE_PROPORTIONAL_ID, "research-scale-move-proportional"),
    ):
        output_root = _output_dir("equivalence", label)
        result = run_round_robin(
            V6_BENCH_8,
            ruleset_id=ruleset_id,
            arena_size=512,
            seeds=STANDARD_V4_SEEDS,
            ticks=TICKS,
            output_root=output_root,
            workers=args.workers,
        )
        results[label] = result
        print(
            f"[equivalence] {label}: {result['total_matches']} matches in "
            f"{result['wall_clock_seconds']:.2f}s"
        )
    path = RUNS_ROOT / "equivalence_summary.json"
    path.write_text(json.dumps(results, indent=2, sort_keys=True), encoding="utf-8")
    print(f"\nwritten: {path}")


def cmd_sweep(args: argparse.Namespace) -> None:
    if not args.all and args.arena_size is None:
        raise ValueError("Must specify either --arena-size or --all")
    arenas = ARENA_SIZES if args.all else [args.arena_size]
    for a in arenas:
        output_root = _output_dir("sweep", f"a{a}")
        result = run_round_robin(
            V6_BENCH_8,
            ruleset_id=BYTEFRAY_RULESET_V6_RESEARCH_SCALE_MOVE_PROPORTIONAL_ID,
            arena_size=a,
            seeds=STANDARD_V4_SEEDS,
            ticks=TICKS,
            output_root=output_root,
            workers=args.workers,
        )
        path = RUNS_ROOT / "sweep" / f"a{a}_summary.json"
        path.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
        print(
            f"[sweep] arena={a}: {result['total_matches']} matches in "
            f"{result['wall_clock_seconds']:.2f}s"
        )
        print(f"written: {path}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("fingerprints").set_defaults(func=cmd_fingerprints)
    sub.add_parser("smoke").set_defaults(func=cmd_smoke)

    equiv_parser = sub.add_parser("equivalence")
    equiv_parser.add_argument("--workers", type=int, default=1)
    equiv_parser.set_defaults(func=cmd_equivalence)

    sweep_parser = sub.add_parser("sweep")
    sweep_parser.add_argument("--arena-size", type=int, choices=ARENA_SIZES)
    sweep_parser.add_argument("--all", action="store_true")
    sweep_parser.add_argument("--workers", type=int, default=1)
    sweep_parser.set_defaults(func=cmd_sweep)

    args = parser.parse_args(argv)
    args.func(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
