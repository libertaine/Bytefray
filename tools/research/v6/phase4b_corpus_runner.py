"""V6 Phase 4B raw arena-scaling study -- corpus runner.

Runs the frozen V6-Bench-8 field through the real production evaluation
harness (``battle_engine.evaluation_service.EvaluationService``) under the
V6 Phase 4B variable-arena research Ruleset (``bytefray-rules-6-research-
scale``), producing genuine, fully-provenanced evaluation artifacts -- never
hand-built fixtures.

A full round-robin field cannot be expressed as a single ``EvaluationRequest``
(that type is one candidate vs. N opponents, a star topology); this module
decomposes an 8-agent round robin into exactly the triangular sequence of
"star" requests that reproduces every unordered pair exactly once:

    for i, candidate in enumerate(field):
        opponents = field[i + 1:]

For N=8 this yields 7+6+5+4+3+2+1 = 28 requests whose union is exactly the
28 unordered pairs Sec 16 of the governing task specifies -- each request
covers its own opponents x seeds x both-orientations cells, so no separate
matrix-building code is needed; ``EvaluationService``/``EvaluationRequest``
generate the exact seeded-placement methodology matrix used everywhere else
in this Ruleset's evaluation, byte for byte.

Usage (see the module-level ``if __name__ == "__main__"`` block for exact
invocations):

    python -m tools.research.v6.phase4b_corpus_runner fingerprints
    python -m tools.research.v6.phase4b_corpus_runner equivalence
    python -m tools.research.v6.phase4b_corpus_runner smoke
    python -m tools.research.v6.phase4b_corpus_runner sweep --arena-size 512
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
    BYTEFRAY_RULESET_V4_ID,
    BYTEFRAY_RULESET_V6_RESEARCH_SCALE_ID,
)

# The frozen V6-Bench-8 field (V6_PHASE4_GAMEPLAY_RESEARCH_METHODOLOGY.md
# Sec 3.3), in the exact repository agent-directory names verified present
# under <data-root>/agents/ before any run below executes.
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

# Tier-1 smoke roster (task Sec 17): 3 strategically distinct archetypes --
# adversarial global sniper, territorial expander, reactive defender.
SMOKE_FIELD: tuple[str, ...] = ("Octave", "v4_claimer", "v5_core_defender")

TICKS = 1000
ARENA_SIZES: tuple[int, ...] = (512, 1024, 4096, 16384, 65536)

RUNS_ROOT = REPO_ROOT / "runs" / "research_v6_phase4b"


def _output_dir(*parts: str) -> Path:
    path = RUNS_ROOT.joinpath(*parts)
    path.mkdir(parents=True, exist_ok=True)
    return path


def verify_and_fingerprint_field(field: tuple[str, ...], data_root: Path | None = None) -> dict[str, dict[str, str]]:
    """Verify every field agent resolves and executes, and record its
    content-addressed revision fingerprint/id (task Sec 15)."""

    root = data_root if data_root is not None else get_data_root()
    out: dict[str, dict[str, str]] = {}
    for name in field:
        spec = resolve_agent(root, name)  # raises if not discoverable/loadable
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
    """Run one full round-robin condition; return a summary dict.

    Returns per-request evaluation ids, matches planned/executed, wall
    clock, and (for a small sample) replay sizes -- never mutates gameplay
    code, never edits results by hand.
    """

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


def cmd_smoke(args: argparse.Namespace) -> None:
    summary = {"conditions": []}
    for arena_size in (512, 65536):
        output_root = _output_dir("smoke", f"a{arena_size}")
        result = run_round_robin(
            SMOKE_FIELD,
            ruleset_id=BYTEFRAY_RULESET_V6_RESEARCH_SCALE_ID,
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
    """Run the full V6-Bench-8 field at A=512 under BOTH stable v4 and the
    research Ruleset -- the direct live evidence for the Sec 13 equivalence
    gate (never a hand-built fixture)."""

    results = {}
    for ruleset_id, label in (
        (BYTEFRAY_RULESET_V4_ID, "v4"),
        (BYTEFRAY_RULESET_V6_RESEARCH_SCALE_ID, "research-scale"),
    ):
        output_root = _output_dir("equivalence", label)
        result = run_round_robin(
            V6_BENCH_8,
            ruleset_id=ruleset_id,
            arena_size=512 if ruleset_id == BYTEFRAY_RULESET_V6_RESEARCH_SCALE_ID else None,
            seeds=STANDARD_V4_SEEDS,
            ticks=TICKS,
            output_root=output_root,
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
    output_root = _output_dir("sweep", f"a{args.arena_size}")
    result = run_round_robin(
        V6_BENCH_8,
        ruleset_id=BYTEFRAY_RULESET_V6_RESEARCH_SCALE_ID,
        arena_size=args.arena_size,
        seeds=STANDARD_V4_SEEDS,
        ticks=TICKS,
        output_root=output_root,
        workers=args.workers,
    )
    path = RUNS_ROOT / "sweep" / f"a{args.arena_size}_summary.json"
    path.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(
        f"[sweep] arena={args.arena_size}: {result['total_matches']} matches in "
        f"{result['wall_clock_seconds']:.2f}s"
    )
    print(f"written: {path}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("fingerprints").set_defaults(func=cmd_fingerprints)
    sub.add_parser("smoke").set_defaults(func=cmd_smoke)
    sub.add_parser("equivalence").set_defaults(func=cmd_equivalence)

    sweep_parser = sub.add_parser("sweep")
    sweep_parser.add_argument("--arena-size", type=int, required=True, choices=ARENA_SIZES)
    sweep_parser.add_argument("--workers", type=int, default=1)
    sweep_parser.set_defaults(func=cmd_sweep)

    args = parser.parse_args(argv)
    args.func(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
