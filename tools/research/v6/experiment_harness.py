"""V6 Consolidated Research Experiment Harness & Analysis (Phases 7, 8, 9; E2 remediation).

Provides a single reusable research runner, provenance recorder, and analyzer
abstraction for V6 research protocols.

Key guarantees:
1. Benchmark corpus reproducibility: resolves benchmark agents from tracked repository fixtures
   (tools/research/v6/fixtures/agents, tools/research/v6/e2/fixtures/agents,
   battle_engine/data/starter_agents), never from the ignored runtime ``agents/`` catalogue.
2. Provenance recording: every experiment records Git SHA, dirty status, ruleset ID, harness
   ID/version, analyzer version, benchmark fingerprints, seeds, arena, pairs, and runtime
   environment, plus any caller-supplied frozen-definition identifiers.
3. Unified runner: runs a triangular round robin over a field, or an explicit list of ordered
   (candidate, opponent) pairs (mirror twins, cross-field references), across arena sizes,
   seeds and orientations. Each cell records who held each seat.
4. Analysis, remediated for the V6 E2 design review's harness defects (review Sec I.4):
   - HD-1: seat-conditioned results are first-class -- per-seat win rates, the pre-registered
     Seat-Determination Index (SDI), mirror seat bias, and separate Seat-A / Seat-B tables.
     Pooled metrics are kept but explicitly subordinate.
   - HD-2: seeds are not assumed independent. Trajectories are deduplicated; every output
     carries ``n_runs`` / ``n_seeds`` / ``n_distinct``; the rating model and the bootstrap use
     the distinct trajectory as the unit of evidence.
   - HD-3: Bradley-Terry is fitted to a tolerance with an iteration cap and reports its
     convergence state; separable (blowout) data is decomposed into strongly connected
     components instead of being given unstable finite ratings.
   - HD-4: explicit pairs make true mirror cells (agent vs twin fixture) possible.
   - HD-6: decision ticks are summarized for decisive matches only; tick-limit matches are
     reported separately.
   - HD-7: the E2 fixture directory is a tracked benchmark source.
"""

from __future__ import annotations

import json
import math
import platform
import random
import shutil
import statistics
import subprocess
import time
from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from dataclasses import field as dataclass_field
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path
from typing import Any

from battle_engine.agent_api import AgentManifestError
from battle_engine.agent_revisions import (
    agent_revision_fingerprint,
    agent_revision_id,
)
from battle_engine.agents import AgentSpec, agent_spec_from_dir, resolve_agent
from battle_engine.evaluation_contracts import (
    ORIENTATION_CANDIDATE_FIRST,
    ORIENTATION_OPPONENT_FIRST,
    STANDARD_V4_SEEDS,
)
from battle_engine.evaluation_service import EvaluationRequest, EvaluationService
from battle_engine.ruleset_policy import (
    BYTEFRAY_RULESET_V4_ID,
)

REPO_ROOT = Path(__file__).resolve().parents[3]

HARNESS_ID = "bytefray-v6-experiment-harness"
# 2: explicit pairs, seat-annotated cell records, request guard (E2 remediation).
HARNESS_VERSION = 2
# 2: seat-conditioned analysis, distinct-trajectory evidence, convergent
# Bradley-Terry, decisive-only decision ticks (E2 remediation HD-1..HD-6).
ANALYZER_VERSION = 2

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

V6_FIXTURE_SOURCE_DIR = REPO_ROOT / "tools" / "research" / "v6" / "fixtures" / "agents"
E2_FIXTURE_SOURCE_DIR = REPO_ROOT / "tools" / "research" / "v6" / "e2" / "fixtures" / "agents"
STARTER_AGENT_SOURCE_DIR = REPO_ROOT / "engine" / "src" / "battle_engine" / "data" / "starter_agents"

TRACKED_BENCHMARK_SOURCE_DIRS: tuple[Path, ...] = (
    V6_FIXTURE_SOURCE_DIR,
    E2_FIXTURE_SOURCE_DIR,
    STARTER_AGENT_SOURCE_DIR,
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
    # HD-4: explicit ordered (candidate, opponent) pairs, e.g. an agent and
    # its mirror twin. ``None`` keeps the historical triangular round robin
    # over ``field`` (every unordered pair once, in field order).
    pairs: tuple[tuple[str, str], ...] | None = None
    # Frozen-definition identifiers (matrix id, condition, field, ...)
    # recorded verbatim at the top level of provenance.json.
    provenance_extra: Mapping[str, Any] = dataclass_field(default_factory=dict)


def experiment_pairs(config: ResearchExperimentConfig) -> tuple[tuple[str, str], ...]:
    """The ordered (candidate, opponent) pairs an experiment runs.

    Explicit pairs must name field members, never pair an entrant with
    itself (a mirror needs a distinct twin fixture), and never repeat an
    unordered pair.
    """
    if config.pairs is None:
        return tuple(combinations(config.field, 2))
    members = set(config.field)
    seen: set[frozenset[str]] = set()
    for candidate, opponent in config.pairs:
        if candidate == opponent:
            raise ValueError(
                f"Pair ({candidate!r}, {opponent!r}) plays an entrant against itself; "
                "a mirror cell needs a distinct twin fixture."
            )
        if candidate not in members or opponent not in members:
            raise ValueError(f"Pair ({candidate!r}, {opponent!r}) names an agent outside the field.")
        key = frozenset((candidate, opponent))
        if key in seen:
            raise ValueError(f"Pair ({candidate!r}, {opponent!r}) is listed more than once.")
        seen.add(key)
    return tuple(config.pairs)


def plan_evaluation_requests(
    config: ResearchExperimentConfig,
    arena_size: int,
    condition_dir: Path,
    data_root: Path,
) -> tuple[EvaluationRequest, ...]:
    """Build (without executing) the evaluation requests one arena condition runs.

    Pairs are grouped by candidate in first-appearance order; for the
    triangular round robin this reproduces the historical one-request-per-
    candidate layout and directory names exactly.
    """
    grouped: dict[str, list[str]] = {}
    for candidate, opponent in experiment_pairs(config):
        grouped.setdefault(candidate, []).append(opponent)
    return tuple(
        EvaluationRequest(
            candidate_id=candidate,
            opponent_ids=tuple(opponents),
            seeds=config.seeds,
            output_dir=condition_dir / f"{index:02d}-{candidate}",
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
        for index, (candidate, opponents) in enumerate(grouped.items())
    )


RequestGuard = Callable[[Sequence[EvaluationRequest]], None]


def _read_result_json(artifact_dir: Path | None) -> dict[str, Any] | None:
    if artifact_dir is None:
        return None
    path = artifact_dir / "result.json"
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def _cell_record(cell: Any, request: EvaluationRequest, out_dir: Path, ticks: int) -> dict[str, Any]:
    artifact_dir: Path | None = cell.artifact_dir
    if artifact_dir is not None and not artifact_dir.is_absolute():
        artifact_dir = request.output_dir / artifact_dir
    result_json = _read_result_json(artifact_dir)

    term_reason = getattr(cell, "error_code", None)
    if not term_reason and result_json is not None:
        term_reason = result_json.get("termination_reason")
    if not term_reason:
        term_reason = (
            "tick_limit"
            if (cell.ticks_run is not None and cell.ticks_run >= ticks)
            else "completed"
        )

    subject_first = cell.orientation != ORIENTATION_OPPONENT_FIRST
    seat_a, seat_b = (
        (cell.subject_id, cell.opponent_id) if subject_first else (cell.opponent_id, cell.subject_id)
    )
    winner_id = (
        cell.subject_id if cell.outcome == "win" else cell.opponent_id if cell.outcome == "loss" else None
    )
    entrant_terminations: dict[str, Any] = {}
    if result_json is not None:
        for entrant in result_json.get("entrants") or ():
            if isinstance(entrant, dict) and entrant.get("agent_id") is not None:
                entrant_terminations[str(entrant["agent_id"])] = entrant.get("termination_reason")
    artifact_rel: str | None = None
    if artifact_dir is not None:
        try:
            artifact_rel = artifact_dir.resolve().relative_to(out_dir.resolve()).as_posix()
        except ValueError:
            artifact_rel = artifact_dir.as_posix()

    return {
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
        "seat_a_id": seat_a,
        "seat_b_id": seat_b,
        "winner_id": winner_id,
        "winner_seat": (
            None if winner_id is None else ("A" if winner_id == seat_a else "B")
        ),
        "entrant_terminations": entrant_terminations,
        "subject_start": cell.subject_start,
        "opponent_start": cell.opponent_start,
        "match_id": cell.match_id,
        "result_id": cell.result_id,
        "error_code": cell.error_code,
        "artifact_dir": artifact_rel,
    }


def run_experiment(
    config: ResearchExperimentConfig,
    *,
    request_guard: RequestGuard | None = None,
) -> dict[str, Any]:
    """Execute a complete research protocol condition and return structured data with provenance.

    Every evaluation request is planned before anything is written or
    executed; ``request_guard`` (if given) sees exactly the requests that
    will run and may raise to abort the experiment fail-closed.
    """
    out_dir = config.output_dir or (REPO_ROOT / "runs" / config.experiment_id)
    data_root = out_dir / "env"
    pairs = experiment_pairs(config)
    plans = [
        (
            arena_size,
            out_dir / f"arena_{arena_size}",
            plan_evaluation_requests(config, arena_size, out_dir / f"arena_{arena_size}", data_root),
        )
        for arena_size in config.arena_sizes
    ]
    if request_guard is not None:
        request_guard(tuple(request for _, _, requests in plans for request in requests))

    out_dir.mkdir(parents=True, exist_ok=True)
    prepare_benchmark_data_root(data_root, config.field)
    agent_fingerprints = fingerprint_corpus(config.field, data_root)
    provenance = get_git_provenance()
    provenance.update(
        {
            "experiment_id": config.experiment_id,
            "harness_id": HARNESS_ID,
            "harness_version": HARNESS_VERSION,
            "analyzer_version": ANALYZER_VERSION,
            "ruleset_id": config.ruleset_id,
            "agent_fingerprints": agent_fingerprints,
            "config": {
                "arena_sizes": list(config.arena_sizes),
                "seeds": list(config.seeds),
                "ticks": config.ticks,
                "both_orientations": config.both_orientations,
                "field": list(config.field),
                "pairing": "triangular" if config.pairs is None else "explicit",
                "pairs": [list(pair) for pair in pairs],
                "scheduler_chunk_size": config.scheduler_chunk_size,
                "scheduler_rotate_start": config.scheduler_rotate_start,
                "workers": config.workers,
            },
        }
    )
    collisions = sorted(set(config.provenance_extra) & set(provenance))
    if collisions:
        raise ValueError(f"provenance_extra would overwrite harness provenance keys: {collisions}")
    provenance.update(dict(config.provenance_extra))

    (out_dir / "provenance.json").write_text(
        json.dumps(provenance, indent=2, sort_keys=True), encoding="utf-8"
    )

    conditions_results: list[dict[str, Any]] = []

    for arena_size, cond_dir, requests in plans:
        cond_dir.mkdir(parents=True, exist_ok=True)

        cells_data: list[dict[str, Any]] = []
        started = time.monotonic()

        for req in requests:
            service = EvaluationService()
            eval_result = service.run(req)
            for cell in eval_result.cells:
                cells_data.append(_cell_record(cell, req, out_dir, config.ticks))

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
# Analysis vocabulary
# ---------------------------------------------------------------------------

SEAT_A = "A"
SEAT_B = "B"
TIE = "tie"
OTHER = "other"
TICK_LIMIT_REASON = "tick_limit"

# Design review Sec I.5 rule 2: any rate claim needs at least this many
# distinct trajectories; below it a result is a characterization.
MIN_DISTINCT_FOR_RATE_CLAIM = 8
# Design review Sec H (H3c): a pair or mirror is seat-determined at SDI >= 0.9.
SEAT_DETERMINED_SDI = 0.9
# Design review Sec I.3: a cycle edge within +/-0.05 of 0.5 is fragile.
FRAGILE_EDGE_MARGIN = 0.05
# Upset detection gap, carried over unchanged from the Phase 9 harness.
UPSET_RATING_GAP = 20.0

BT_TOLERANCE = 1e-10
BT_MAX_ITERATIONS = 100_000


def _orientation(cell: Mapping[str, Any]) -> str:
    return str(cell.get("orientation") or ORIENTATION_CANDIDATE_FIRST)


def cell_seats(cell: Mapping[str, Any]) -> tuple[str, str]:
    """``(seat_a_entrant, seat_b_entrant)`` for one cell."""
    subject, opponent = str(cell["subject_id"]), str(cell["opponent_id"])
    if _orientation(cell) == ORIENTATION_OPPONENT_FIRST:
        return opponent, subject
    return subject, opponent


def cell_winner(cell: Mapping[str, Any]) -> str | None:
    """The winning entrant's id, or ``None`` for a tie or a non-outcome."""
    outcome = cell.get("outcome")
    if outcome == "win":
        return str(cell["subject_id"])
    if outcome == "loss":
        return str(cell["opponent_id"])
    return None


def cell_seat_result(cell: Mapping[str, Any]) -> str:
    """``"A"`` / ``"B"`` (winning seat), ``"tie"``, or ``"other"`` (no match outcome)."""
    outcome = cell.get("outcome")
    if outcome == "tie":
        return TIE
    winner = cell_winner(cell)
    if winner is None:
        return OTHER
    return SEAT_A if winner == cell_seats(cell)[0] else SEAT_B


def _number(value: Any) -> float | None:
    if value is None:
        return None
    return round(float(value), 9)


def trajectory_key(cell: Mapping[str, Any]) -> tuple[Any, ...]:
    """HD-2: the outcome-level identity of one match trajectory.

    The design review's fields (winner, ticks, termination reason, final
    scores) are expressed in seat terms together with who held each seat, so
    the two orientations of one pairing can never merge. Final territory,
    the per-entrant termination reasons and the non-outcome status are
    added: all are stable deterministic outputs, and each separates
    trajectories the review's fields alone could merge (for example, a
    capture versus a forfeit at the same tick with equal scores).

    Seeds, start addresses, ids and hashes are deliberately excluded: a
    placement-invariant deterministic pairing must collapse to one
    trajectory, and a replay/result hash would split equivalent trajectories
    on metadata. Merging can only ever under-count distinct behaviour, so
    ``n_distinct`` is a conservative effective sample size.
    """
    seat_a, seat_b = cell_seats(cell)
    subject_is_a = seat_a == str(cell["subject_id"])
    score_s, score_o = _number(cell.get("score_subject")), _number(cell.get("score_opponent"))
    terr_s, terr_o = _number(cell.get("territory_subject")), _number(cell.get("territory_opponent"))
    terminations = cell.get("entrant_terminations") or {}
    return (
        seat_a,
        seat_b,
        cell_seat_result(cell),
        cell.get("ticks_run"),
        cell.get("termination_reason"),
        score_s if subject_is_a else score_o,
        score_o if subject_is_a else score_s,
        terr_s if subject_is_a else terr_o,
        terr_o if subject_is_a else terr_s,
        tuple(sorted((str(k), v) for k, v in terminations.items())),
        cell.get("status"),
        cell.get("outcome") if cell_seat_result(cell) == OTHER else None,
    )


def count_distinct_trajectories(cells: Sequence[Mapping[str, Any]]) -> int:
    return len({trajectory_key(cell) for cell in cells})


def evidence_label(n_distinct: int) -> str:
    """How a result derived from ``n_distinct`` trajectories may be described."""
    if n_distinct <= 0:
        return "no_data"
    if n_distinct == 1:
        return "deterministic_characterization"
    if n_distinct < MIN_DISTINCT_FOR_RATE_CLAIM:
        return "limited_distinct_trajectories"
    return "rate_claim_eligible"


def effective_sample(cells: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    n_distinct = count_distinct_trajectories(cells)
    return {
        "n_runs": len(cells),
        "n_seeds": len({cell.get("seed") for cell in cells}),
        "n_distinct": n_distinct,
        "evidence": evidence_label(n_distinct),
    }


def _ratio(numerator: float, denominator: float) -> float | None:
    return None if denominator == 0 else round(numerator / denominator, 6)


def _field_order(field: Sequence[str]) -> dict[str, int]:
    return {name: index for index, name in enumerate(field)}


def _pair_groups(
    cells: Sequence[Mapping[str, Any]], field: Sequence[str]
) -> list[tuple[tuple[str, str], list[Mapping[str, Any]]]]:
    """Cells grouped by unordered pairing, ordered by field position.

    Each pairing is labelled ``(first, second)`` in field order; entrants
    outside ``field`` are ignored.
    """
    order = _field_order(field)
    groups: dict[tuple[str, str], list[Mapping[str, Any]]] = {}
    for cell in cells:
        a, b = str(cell["subject_id"]), str(cell["opponent_id"])
        if a not in order or b not in order or a == b:
            continue
        key = (a, b) if order[a] < order[b] else (b, a)
        groups.setdefault(key, []).append(cell)
    return sorted(groups.items(), key=lambda item: (order[item[0][0]], order[item[0][1]]))


# ---------------------------------------------------------------------------
# HD-1: seat-conditioned outcomes, SDI, mirror seat bias
# ---------------------------------------------------------------------------


def _seat_side(cells: Sequence[Mapping[str, Any]], entrant: str, seat: str) -> dict[str, Any]:
    index = 0 if seat == SEAT_A else 1
    subset = [cell for cell in cells if cell_seats(cell)[index] == entrant]
    wins = sum(1 for cell in subset if cell_winner(cell) == entrant)
    ties = sum(1 for cell in subset if cell_seat_result(cell) == TIE)
    other = sum(1 for cell in subset if cell_seat_result(cell) == OTHER)
    losses = len(subset) - wins - ties - other
    return {
        **effective_sample(subset),
        "wins": wins,
        "losses": losses,
        "ties": ties,
        "other": other,
        "p_win": _ratio(wins, len(subset)),
        "p_loss": _ratio(losses, len(subset)),
        "p_tie": _ratio(ties, len(subset)),
        "p_win_decisive": _ratio(wins, wins + losses),
    }


def seat_determination_index(cells: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """The pre-registered Seat-Determination Index for one pairing (review Sec H).

    For each seed, pair the two orientations: the seed is seat-determined if
    the Seat-A entrant wins in both orientations, or the Seat-B entrant wins
    in both. The pairing's SDI is the mean of that indicator over its
    *distinct* seed-level trajectories (the orientation pair of trajectory
    keys), so duplicated deterministic seeds count once. A seed-weighted
    mean is also returned, labelled descriptive. Repeated (seed, orientation)
    cells are paired by occurrence order.
    """
    occurrences: Counter[tuple[Any, str]] = Counter()
    by_seed: dict[tuple[Any, int], dict[str, Mapping[str, Any]]] = {}
    for cell in cells:
        orientation = _orientation(cell)
        occurrence = occurrences[(cell.get("seed"), orientation)]
        occurrences[(cell.get("seed"), orientation)] += 1
        by_seed.setdefault((cell.get("seed"), occurrence), {})[orientation] = cell

    paired: list[tuple[tuple[Any, ...], bool, bool]] = []
    incomplete = 0
    for _, sides in sorted(by_seed.items(), key=lambda item: (str(item[0][0]), item[0][1])):
        first = sides.get(ORIENTATION_CANDIDATE_FIRST)
        second = sides.get(ORIENTATION_OPPONENT_FIRST)
        if first is None or second is None:
            incomplete += 1
            continue
        results = (cell_seat_result(first), cell_seat_result(second))
        paired.append(
            (
                (trajectory_key(first), trajectory_key(second)),
                results == (SEAT_A, SEAT_A),
                results == (SEAT_B, SEAT_B),
            )
        )

    distinct: dict[tuple[Any, ...], tuple[bool, bool]] = {}
    for key, determined_a, determined_b in paired:
        distinct[key] = (determined_a, determined_b)

    def _summary(rows: Sequence[tuple[bool, bool]]) -> tuple[float | None, float | None, float | None]:
        if not rows:
            return None, None, None
        share_a = sum(1 for a, _ in rows if a) / len(rows)
        share_b = sum(1 for _, b in rows if b) / len(rows)
        return round(share_a + share_b, 6), round(share_a, 6), round(share_b, 6)

    sdi, sdi_a, sdi_b = _summary(list(distinct.values()))
    seed_sdi, seed_a, seed_b = _summary([(a, b) for _, a, b in paired])
    if sdi is None:
        favoured: str | None = None
    elif sdi_a is not None and sdi_b is not None and sdi_a > sdi_b:
        favoured = SEAT_A
    elif sdi_a is not None and sdi_b is not None and sdi_b > sdi_a:
        favoured = SEAT_B
    else:
        favoured = "none" if sdi == 0 else "balanced"
    return {
        "sdi": sdi,
        "sdi_seat_a": sdi_a,
        "sdi_seat_b": sdi_b,
        "favoured_seat": favoured,
        "seat_determined": sdi is not None and sdi >= SEAT_DETERMINED_SDI,
        "n_seed_pairs": len(paired),
        "n_distinct": len(distinct),
        "evidence": evidence_label(len(distinct)),
        "incomplete_seed_pairs": incomplete,
        "seed_weighted_descriptive": {"sdi": seed_sdi, "sdi_seat_a": seed_a, "sdi_seat_b": seed_b},
    }


def _tick_distribution(cells: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    ticks = sorted(int(cell["ticks_run"]) for cell in cells)
    summary: dict[str, Any] = effective_sample(cells)
    if not ticks:
        summary.update({"median": None, "q1": None, "q3": None, "iqr": None, "min": None, "max": None})
        return summary
    if len(ticks) == 1:
        q1 = q3 = float(ticks[0])
    else:
        q1, _, q3 = statistics.quantiles(ticks, n=4, method="inclusive")
    summary.update(
        {
            "median": float(statistics.median(ticks)),
            "q1": float(q1),
            "q3": float(q3),
            "iqr": float(q3 - q1),
            "min": ticks[0],
            "max": ticks[-1],
        }
    )
    return summary


def decision_tick_summary(
    cells: Sequence[Mapping[str, Any]], *, tick_limit: int | None = None
) -> dict[str, Any]:
    """HD-6: decisive decision ticks, never pooled with tick-limit matches.

    * ``decisive``: a winner, and the match ended before the tick limit.
    * ``mutual_elimination``: a tie that ended before the tick limit
      (``all_agents_dead``); a real decision tick, but not a decisive one.
    * ``tick_limit``: every match that ran to the limit (score-fallback wins
      and draws alike). Its length is reported, never read as a decision.
    """
    decisive: list[Mapping[str, Any]] = []
    mutual: list[Mapping[str, Any]] = []
    limit: list[Mapping[str, Any]] = []
    unclassified = 0
    for cell in cells:
        result = cell_seat_result(cell)
        ticks = cell.get("ticks_run")
        if result == OTHER or ticks is None:
            unclassified += 1
            continue
        reason = cell.get("termination_reason")
        if reason == TICK_LIMIT_REASON or (
            reason is None and tick_limit is not None and ticks >= tick_limit
        ):
            limit.append(cell)
        elif result == TIE:
            mutual.append(cell)
        else:
            decisive.append(cell)
    classified = len(decisive) + len(mutual) + len(limit)
    return {
        "decisive": _tick_distribution(decisive),
        "mutual_elimination": _tick_distribution(mutual),
        "tick_limit": {
            **effective_sample(limit),
            "fraction": _ratio(len(limit), classified),
            "lengths": sorted({int(cell["ticks_run"]) for cell in limit}),
            "seat_a_score_wins": sum(1 for cell in limit if cell_seat_result(cell) == SEAT_A),
            "seat_b_score_wins": sum(1 for cell in limit if cell_seat_result(cell) == SEAT_B),
            "ties": sum(1 for cell in limit if cell_seat_result(cell) == TIE),
        },
        "unclassified": unclassified,
        "n_runs": len(cells),
    }


def matchup_summary(cells: Sequence[Mapping[str, Any]], first: str, second: str) -> dict[str, Any]:
    """Seat-conditioned record for one pairing (HD-1, HD-2, HD-6)."""
    seat_results = Counter(cell_seat_result(cell) for cell in cells)
    n_runs = len(cells)
    rate_a = _ratio(seat_results[SEAT_A], n_runs)
    rate_b = _ratio(seat_results[SEAT_B], n_runs)
    return {
        "entrants": [first, second],
        **effective_sample(cells),
        "seat_a_wins": seat_results[SEAT_A],
        "seat_b_wins": seat_results[SEAT_B],
        "ties": seat_results[TIE],
        "other": seat_results[OTHER],
        "seat_a_win_rate": rate_a,
        "seat_b_win_rate": rate_b,
        "tie_rate": _ratio(seat_results[TIE], n_runs),
        "seat_bias": None if rate_a is None or rate_b is None else round(rate_a - rate_b, 6),
        "by_entrant": {
            entrant: {
                "seat_a": _seat_side(cells, entrant, SEAT_A),
                "seat_b": _seat_side(cells, entrant, SEAT_B),
            }
            for entrant in (first, second)
        },
        "sdi": seat_determination_index(cells),
        "decision_ticks": decision_tick_summary(cells),
    }


def seat_conditioned_matchups(
    cells: Sequence[Mapping[str, Any]], field: Sequence[str]
) -> list[dict[str, Any]]:
    return [matchup_summary(group, first, second) for (first, second), group in _pair_groups(cells, field)]


def summarize_seat_pathology(
    matchups: Sequence[Mapping[str, Any]], cells: Sequence[Mapping[str, Any]]
) -> dict[str, Any]:
    """The headline HD-1 view: how much of the field is decided by seat."""
    seat_results = Counter(cell_seat_result(cell) for cell in cells)
    determined = [
        {
            "entrants": matchup["entrants"],
            "sdi": matchup["sdi"]["sdi"],
            "favoured_seat": matchup["sdi"]["favoured_seat"],
            "n_distinct": matchup["sdi"]["n_distinct"],
            "evidence": matchup["sdi"]["evidence"],
        }
        for matchup in matchups
        if matchup["sdi"]["seat_determined"]
    ]
    biases = [abs(m["seat_bias"]) for m in matchups if m["seat_bias"] is not None]
    measured = [m for m in matchups if m["sdi"]["sdi"] is not None]
    return {
        "n_pairings": len(matchups),
        "n_pairings_with_sdi": len(measured),
        "seat_determined_pairings": determined,
        "seat_determined_share": _ratio(len(determined), len(measured)),
        "all_pairings_seat_determined": bool(measured) and len(determined) == len(measured),
        "max_abs_seat_bias": max(biases) if biases else None,
        "seat_a_win_rate": _ratio(seat_results[SEAT_A], len(cells)),
        "seat_b_win_rate": _ratio(seat_results[SEAT_B], len(cells)),
        "tie_rate": _ratio(seat_results[TIE], len(cells)),
    }


def analyze_mirror_condition(
    cells: Sequence[Mapping[str, Any]], mirror_pairs: Sequence[tuple[str, str]]
) -> dict[str, Any]:
    """HD-4: one record per agent/twin mirror, reported apart from any rating table.

    Mirror seat bias (review Sec H) is the Seat-A win rate minus the Seat-B
    win rate over the mirror's runs.
    """
    mirrors = []
    for primary, twin in mirror_pairs:
        subset = [
            cell
            for cell in cells
            if {str(cell["subject_id"]), str(cell["opponent_id"])} == {primary, twin}
        ]
        summary = matchup_summary(subset, primary, twin)
        mirrors.append(
            {
                "primary": primary,
                "twin": twin,
                "n_runs": summary["n_runs"],
                "n_seeds": summary["n_seeds"],
                "n_distinct": summary["n_distinct"],
                "evidence": summary["evidence"],
                "seat_a_wins": summary["seat_a_wins"],
                "seat_b_wins": summary["seat_b_wins"],
                "ties": summary["ties"],
                "other": summary["other"],
                "seat_a_win_rate": summary["seat_a_win_rate"],
                "seat_b_win_rate": summary["seat_b_win_rate"],
                "mirror_seat_bias": summary["seat_bias"],
                "sdi": summary["sdi"],
                "decision_ticks": summary["decision_ticks"],
            }
        )
    biases = [abs(m["mirror_seat_bias"]) for m in mirrors if m["mirror_seat_bias"] is not None]
    return {
        "analyzer_version": ANALYZER_VERSION,
        "mirrors": mirrors,
        "max_abs_mirror_seat_bias": max(biases) if biases else None,
        "seat_determined_mirrors": [
            m["primary"] for m in mirrors if m["sdi"]["seat_determined"]
        ],
        "note": "Mirror cells are reported on their own and never pooled into field ratings.",
    }


# ---------------------------------------------------------------------------
# Descriptive ordered-pair record (Phase 9 shape, extended)
# ---------------------------------------------------------------------------


def compute_pairwise_record(
    cells: Sequence[dict[str, Any]], field: Sequence[str]
) -> dict[tuple[str, str], dict[str, Any]]:
    """Per ordered pair ``(a, b)``, from ``a``'s perspective: wins, losses,
    ties, per-seat splits, per-seed records, and distinct trajectories.

    Counts are match counts (descriptive). ``n_distinct`` is the number of
    distinct trajectories behind them (HD-2).
    """
    table: dict[tuple[str, str], dict[str, Any]] = {
        (a, b): {
            "wins": 0,
            "losses": 0,
            "ties": 0,
            "played": 0,
            "seat_a_played": 0,
            "seat_b_played": 0,
            "seat_a_wins": 0,
            "seat_b_wins": 0,
            "seeds": {},
            "n_distinct": 0,
        }
        for a in field
        for b in field
        if a != b
    }
    distinct: dict[tuple[str, str], set[tuple[Any, ...]]] = {}

    for c in cells:
        subj = c["subject_id"]
        opp = c["opponent_id"]
        if (subj, opp) not in table:
            continue
        seat_a, _ = cell_seats(c)
        result = cell_seat_result(c)
        winner = cell_winner(c)
        key = trajectory_key(c)
        seed = c.get("seed", 0)
        for me, other in ((subj, opp), (opp, subj)):
            rec = table[(me, other)]
            distinct.setdefault((me, other), set()).add(key)
            seed_rec = rec["seeds"].setdefault(seed, {"wins": 0, "losses": 0, "ties": 0, "played": 0})
            rec["played"] += 1
            seed_rec["played"] += 1
            in_seat_a = seat_a == me
            rec["seat_a_played" if in_seat_a else "seat_b_played"] += 1
            if result == TIE:
                rec["ties"] += 1
                seed_rec["ties"] += 1
            elif winner == me:
                rec["wins"] += 1
                seed_rec["wins"] += 1
                rec["seat_a_wins" if in_seat_a else "seat_b_wins"] += 1
            elif winner == other:
                rec["losses"] += 1
                seed_rec["losses"] += 1

    for pair, keys in distinct.items():
        table[pair]["n_distinct"] = len(keys)
    return table


# ---------------------------------------------------------------------------
# Rating model: distinct-trajectory evidence, convergent Bradley-Terry (HD-2, HD-3)
# ---------------------------------------------------------------------------


def distinct_pairwise_evidence(
    cells: Sequence[Mapping[str, Any]], field: Sequence[str]
) -> tuple[dict[tuple[str, str], float], dict[tuple[str, str], int]]:
    """``(wins, games)`` with the distinct trajectory as the unit of evidence.

    For each pairing, every distinct trajectory with a match outcome counts
    once: a win is 1 point to the winner, a tie 0.5 to each. Duplicated
    seeds therefore never add weight, and ``games[(a, b)]`` is the pairing's
    distinct-trajectory count. Match-weighted frequencies stay available in
    the descriptive records.
    """
    wins: dict[tuple[str, str], float] = {}
    games: dict[tuple[str, str], int] = {}
    for (a, b), group in _pair_groups(cells, field):
        outcomes: dict[tuple[Any, ...], str | None] = {}
        for cell in group:
            if cell_seat_result(cell) == OTHER:
                continue
            outcomes[trajectory_key(cell)] = cell_winner(cell)
        if not outcomes:
            continue
        points_a = sum(1.0 if w == a else 0.5 if w is None else 0.0 for w in outcomes.values())
        wins[(a, b)] = points_a
        wins[(b, a)] = len(outcomes) - points_a
        games[(a, b)] = games[(b, a)] = len(outcomes)
    return wins, games


@dataclass(frozen=True)
class BradleyTerryFit:
    """A Bradley-Terry fit with explicit convergence and separability state.

    The win graph (edge ``i -> j`` when ``i`` took any point from ``j``) is
    split into strongly connected components. The maximum-likelihood fit
    exists exactly when there is one component (Ford's condition); otherwise
    the data is separable, the MLE puts the components infinitely far apart,
    and only within-component ratings are finite. ``components`` lists them
    strongest first; ``expected`` returns the limiting 1.0 / 0.0 across
    components. Ratings are on the Elo scale, centred at 1500 within each
    component, and are comparable only inside one component.
    """

    field: tuple[str, ...]
    strengths: dict[str, float]
    ratings: dict[str, float]
    components: tuple[tuple[str, ...], ...]
    dominates: frozenset[tuple[int, int]]
    converged: bool
    iterations: int
    max_log_change: float
    tolerance: float
    max_iterations: int

    @property
    def separable(self) -> bool:
        return len(self.components) > 1

    @property
    def authoritative(self) -> bool:
        """Finite, converged ratings on one common scale."""
        return self.converged and not self.separable

    def component_index(self, name: str) -> int:
        for index, members in enumerate(self.components):
            if name in members:
                return index
        raise KeyError(name)

    def expected(self, a: str, b: str) -> float | None:
        ca, cb = self.component_index(a), self.component_index(b)
        if ca == cb:
            pa, pb = self.strengths[a], self.strengths[b]
            return pa / (pa + pb)
        if (ca, cb) in self.dominates:
            return 1.0
        if (cb, ca) in self.dominates:
            return 0.0
        return None

    def to_dict(self) -> dict[str, Any]:
        """Serializable view. A separable fit publishes no global ratings --
        only the component ordering and ratings inside multi-member
        components -- so equal-looking numbers can never be read across
        components."""
        return {
            "converged": self.converged,
            "iterations": self.iterations,
            "max_log_change": self.max_log_change,
            "tolerance": self.tolerance,
            "max_iterations": self.max_iterations,
            "separable": self.separable,
            "authoritative": self.authoritative,
            "components": [list(members) for members in self.components],
            "ratings": None if self.separable else dict(self.ratings),
            "within_component_ratings": [
                {name: self.ratings[name] for name in members}
                for members in self.components
                if len(members) > 1
            ]
            if self.separable
            else None,
        }


def _strongly_connected_components(
    field: Sequence[str], edges: Mapping[str, Sequence[str]]
) -> list[tuple[str, ...]]:
    """Tarjan's algorithm; deterministic in field order."""
    index_of: dict[str, int] = {}
    low: dict[str, int] = {}
    on_stack: set[str] = set()
    stack: list[str] = []
    components: list[tuple[str, ...]] = []
    order = _field_order(field)
    counter = 0

    def visit(node: str) -> None:
        nonlocal counter
        index_of[node] = low[node] = counter
        counter += 1
        stack.append(node)
        on_stack.add(node)
        for succ in edges.get(node, ()):
            if succ not in index_of:
                visit(succ)
                low[node] = min(low[node], low[succ])
            elif succ in on_stack:
                low[node] = min(low[node], index_of[succ])
        if low[node] == index_of[node]:
            members = []
            while True:
                top = stack.pop()
                on_stack.discard(top)
                members.append(top)
                if top == node:
                    break
            components.append(tuple(sorted(members, key=order.__getitem__)))

    for name in field:
        if name not in index_of:
            visit(name)
    return components


def _fit_component(
    members: Sequence[str],
    wins: Mapping[tuple[str, str], float],
    games: Mapping[tuple[str, str], int],
    tolerance: float,
    max_iterations: int,
) -> tuple[dict[str, float], bool, int, float]:
    """Minorization-maximization (Hunter 2004) inside one strongly connected component."""
    if len(members) == 1:
        return {members[0]: 1.0}, True, 0, 0.0
    totals = {i: sum(wins.get((i, j), 0.0) for j in members if j != i) for i in members}
    opponents = {
        i: [(j, games[(i, j)]) for j in members if j != i and games.get((i, j), 0) > 0]
        for i in members
    }
    log_p = dict.fromkeys(members, 0.0)
    change = math.inf
    for iteration in range(1, max_iterations + 1):
        p = {i: math.exp(v) for i, v in log_p.items()}
        updated = {
            i: math.log(totals[i]) - math.log(sum(n / (p[i] + p[j]) for j, n in opponents[i]))
            for i in members
        }
        centre = sum(updated.values()) / len(updated)
        updated = {i: v - centre for i, v in updated.items()}
        change = max(abs(updated[i] - log_p[i]) for i in members)
        log_p = updated
        if change < tolerance:
            return {i: math.exp(v) for i, v in log_p.items()}, True, iteration, change
    return {i: math.exp(v) for i, v in log_p.items()}, False, max_iterations, change


def fit_bradley_terry(
    wins: Mapping[tuple[str, str], float],
    games: Mapping[tuple[str, str], int],
    field: Sequence[str],
    *,
    tolerance: float = BT_TOLERANCE,
    max_iterations: int = BT_MAX_ITERATIONS,
) -> BradleyTerryFit:
    """HD-3: a tolerance-based, capped, deterministic Bradley-Terry fit.

    No pseudo-count regularization is needed: separable data is handled
    exactly by the component decomposition, so every fitted rating is a
    finite within-component maximum-likelihood estimate.
    """
    names = tuple(field)
    order = _field_order(names)
    edges = {
        a: [b for b in names if b != a and wins.get((a, b), 0.0) > 0.0] for a in names
    }
    raw_components = _strongly_connected_components(names, edges)
    component_of = {name: index for index, members in enumerate(raw_components) for name in members}
    successors: dict[int, set[int]] = {index: set() for index in range(len(raw_components))}
    for a in names:
        for b in edges[a]:
            if component_of[a] != component_of[b]:
                successors[component_of[a]].add(component_of[b])

    reach: dict[int, set[int]] = {}
    for start, direct in successors.items():
        seen: set[int] = set()
        frontier = list(direct)
        while frontier:
            node = frontier.pop()
            if node not in seen:
                seen.add(node)
                frontier.extend(successors[node])
        reach[start] = seen

    # Strongest first: more components dominated, then field order.
    ranked = sorted(
        range(len(raw_components)),
        key=lambda c: (-len(reach[c]), min(order[m] for m in raw_components[c])),
    )
    position = {old: new for new, old in enumerate(ranked)}
    components = tuple(raw_components[c] for c in ranked)
    dominates = frozenset(
        (position[c], position[d]) for c in reach for d in reach[c]
    )

    strengths: dict[str, float] = {}
    converged = True
    iterations = 0
    max_change = 0.0
    for members in components:
        fitted, ok, used, change = _fit_component(members, wins, games, tolerance, max_iterations)
        strengths.update(fitted)
        converged = converged and ok
        iterations = max(iterations, used)
        max_change = max(max_change, change)

    ratings = {
        name: round(1500.0 + 400.0 * math.log10(strengths[name]), 2) for name in names
    }
    return BradleyTerryFit(
        field=names,
        strengths={name: strengths[name] for name in names},
        ratings=ratings,
        components=components,
        dominates=dominates,
        converged=converged,
        iterations=iterations,
        max_log_change=max_change,
        tolerance=tolerance,
        max_iterations=max_iterations,
    )


def compute_matchup_residuals(
    wins: Mapping[tuple[str, str], float],
    games: Mapping[tuple[str, str], int],
    field: Sequence[str],
    fit: BradleyTerryFit,
) -> dict[str, Any]:
    """Residuals from the one-dimensional transitive model.

    ``R_ij = W_ij - W_hat_ij`` with ``W_ij`` the distinct-trajectory win
    rate and ``W_hat_ij`` the fitted (or, across components, limiting)
    expectation. RMSR summarizes departure from transitivity; a perfectly
    transitive field has RMSR 0 whether or not it is separable.
    """
    residuals: dict[str, float] = {}
    unmodelled: list[str] = []
    squared: list[float] = []
    for i, a in enumerate(field):
        for b in field[i + 1 :]:
            n = games.get((a, b), 0)
            if n == 0:
                continue
            expected = fit.expected(a, b)
            if expected is None:
                unmodelled.append(f"{a}_vs_{b}")
                continue
            diff = wins[(a, b)] / n - expected
            residuals[f"{a}_vs_{b}"] = round(diff, 6)
            squared.append(diff**2)
    rmsr = math.sqrt(sum(squared) / len(squared)) if squared else 0.0
    return {"residuals": residuals, "rmsr": round(rmsr, 6), "unmodelled_pairs": unmodelled}


def compute_upset_reversals(
    wins: Mapping[tuple[str, str], float],
    games: Mapping[tuple[str, str], int],
    field: Sequence[str],
    fit: BradleyTerryFit,
    rating_gap: float = UPSET_RATING_GAP,
) -> list[dict[str, Any]]:
    """Lower-rated entrant beats a higher-rated one head to head (same component only).

    Across components no upset is possible: the stronger component took
    every point.
    """
    reversals = []
    for i, a in enumerate(field):
        for b in field[i + 1 :]:
            n = games.get((a, b), 0)
            if n == 0 or fit.component_index(a) != fit.component_index(b):
                continue
            higher, lower = (a, b) if fit.ratings[a] >= fit.ratings[b] else (b, a)
            lower_rate = wins[(lower, higher)] / n
            gap = fit.ratings[higher] - fit.ratings[lower]
            if lower_rate > 0.5 and gap > rating_gap:
                reversals.append(
                    {
                        "underdog": lower,
                        "favorite": higher,
                        "underdog_rating": fit.ratings[lower],
                        "favorite_rating": fit.ratings[higher],
                        "underdog_winrate": round(lower_rate, 6),
                        "n_distinct": n,
                    }
                )
    return reversals


def compute_directed_3_cycles(
    wins: Mapping[tuple[str, str], float],
    games: Mapping[tuple[str, str], int],
    field: Sequence[str],
) -> list[dict[str, Any]]:
    """Directed 3-cycles ``x -> y -> z -> x`` with every edge's margin (review Sec I.3).

    An edge is any strict majority (distinct-trajectory win rate > 0.5). A
    cycle is ``fragile`` when any edge lies within +/-``FRAGILE_EDGE_MARGIN``
    of 0.5.
    """
    def rate(a: str, b: str) -> float | None:
        n = games.get((a, b), 0)
        return None if n == 0 else wins[(a, b)] / n

    cycles = []
    for a, b, c in combinations(field, 3):
        for x, y, z in ((a, b, c), (a, c, b)):
            edges = [(x, y), (y, z), (z, x)]
            rates = [rate(u, v) for u, v in edges]
            if all(r is not None and r > 0.5 for r in rates):
                margins = [round(float(r) - 0.5, 6) for r in rates if r is not None]
                cycles.append(
                    {
                        "cycle": [x, y, z],
                        "edges": [
                            {
                                "winner": u,
                                "loser": v,
                                "rate": round(float(r), 6),
                                "margin": m,
                                "n_distinct": games[(u, v)],
                            }
                            for (u, v), r, m in zip(edges, rates, margins, strict=True)
                            if r is not None
                        ],
                        "min_margin": min(margins),
                        "fragile": min(margins) <= FRAGILE_EDGE_MARGIN,
                    }
                )
    return cycles


def compute_intransitive_3_cycles(
    cells: Sequence[Mapping[str, Any]],
    field: Sequence[str],
    dominance_threshold: float = 0.55,
) -> list[tuple[str, str, str]]:
    """Phase 9 compatibility view: cycles whose every edge exceeds ``dominance_threshold``."""
    wins, games = distinct_pairwise_evidence(cells, field)
    return [
        (cycle["cycle"][0], cycle["cycle"][1], cycle["cycle"][2])
        for cycle in compute_directed_3_cycles(wins, games, field)
        if all(edge["rate"] > dominance_threshold for edge in cycle["edges"])
    ]


def _distinct_outcomes_by_pair(
    cells: Sequence[Mapping[str, Any]], field: Sequence[str]
) -> dict[tuple[str, str], list[str | None]]:
    """Per pairing (field order), the winner of each distinct trajectory, in a canonical order."""
    trajectories: dict[tuple[str, str], list[str | None]] = {}
    for pair, group in _pair_groups(cells, field):
        outcomes: dict[tuple[Any, ...], str | None] = {}
        for cell in group:
            if cell_seat_result(cell) != OTHER:
                outcomes[trajectory_key(cell)] = cell_winner(cell)
        if outcomes:
            ordered = sorted(outcomes.items(), key=lambda item: repr(item[0]))
            trajectories[pair] = [winner for _, winner in ordered]
    return trajectories


def _resample_evidence(
    trajectories: Mapping[tuple[str, str], Sequence[str | None]], rng: random.Random
) -> tuple[dict[tuple[str, str], float], dict[tuple[str, str], int]]:
    """One stratified bootstrap draw: each pairing's distinct trajectories, with replacement."""
    wins: dict[tuple[str, str], float] = {}
    games: dict[tuple[str, str], int] = {}
    for (a, b), outcomes in trajectories.items():
        drawn = [outcomes[rng.randrange(len(outcomes))] for _ in outcomes]
        points_a = sum(1.0 if w == a else 0.5 if w is None else 0.0 for w in drawn)
        wins[(a, b)], wins[(b, a)] = points_a, len(drawn) - points_a
        games[(a, b)] = games[(b, a)] = len(drawn)
    return wins, games


def _bootstrap_base(
    trajectories: Mapping[tuple[str, str], Sequence[str | None]], n_bootstraps: int, seed: int
) -> dict[str, Any]:
    return {
        "n_bootstraps": n_bootstraps,
        "seed": seed,
        "n_pairings": len(trajectories),
        "n_pairings_with_outcome_variation": sum(
            1 for outcomes in trajectories.values() if len(set(outcomes)) > 1
        ),
        "n_distinct": sum(len(outcomes) for outcomes in trajectories.values()),
    }


def bootstrap_rmsr_over_distinct_trajectories(
    cells: Sequence[Mapping[str, Any]],
    field: Sequence[str],
    n_bootstraps: int = 200,
    seed: int = 42,
) -> dict[str, Any]:
    """HD-2: bootstrap standard error of RMSR, resampling distinct trajectories.

    Each pairing's distinct trajectories are resampled with replacement
    (stratified by pairing), so a duplicated seed never adds an observation
    and never narrows the estimate. When no pairing has more than one
    distinct outcome the data is deterministic and the standard error is
    reported as not estimable rather than as zero.
    """
    trajectories = _distinct_outcomes_by_pair(cells, field)
    base = _bootstrap_base(trajectories, n_bootstraps, seed)
    if base["n_pairings_with_outcome_variation"] == 0:
        return {**base, "status": "not_estimable_deterministic", "se": None}
    rng = random.Random(seed)
    samples = []
    for _ in range(n_bootstraps):
        wins, games = _resample_evidence(trajectories, rng)
        fit = fit_bradley_terry(wins, games, field)
        samples.append(float(compute_matchup_residuals(wins, games, field, fit)["rmsr"]))
    return {**base, "status": "estimated", "se": round(statistics.stdev(samples), 6)}


def _percentile(values: Sequence[float], q: float) -> float:
    ordered = sorted(values)
    position = q * (len(ordered) - 1)
    low = math.floor(position)
    high = min(low + 1, len(ordered) - 1)
    return ordered[low] + (ordered[high] - ordered[low]) * (position - low)


def bootstrap_residual_intervals(
    cells: Sequence[Mapping[str, Any]],
    field: Sequence[str],
    *,
    n_bootstraps: int = 1000,
    seed: int = 42,
    interval: float = 0.95,
) -> dict[str, Any]:
    """Percentile intervals for every residual, resampling distinct trajectories.

    A residual is ``significant`` only if its pairing has at least
    ``MIN_DISTINCT_FOR_RATE_CLAIM`` distinct trajectories (review Sec I.5
    rule 2) and its interval excludes 0; pairings below that are
    characterizations, reported but never counted.
    """
    trajectories = _distinct_outcomes_by_pair(cells, field)
    wins, games = distinct_pairwise_evidence(cells, field)
    fit = fit_bradley_terry(wins, games, field)
    point = compute_matchup_residuals(wins, games, field, fit)["residuals"]
    samples: dict[str, list[float]] = {key: [] for key in point}
    rng = random.Random(seed)
    for _ in range(n_bootstraps):
        boot_wins, boot_games = _resample_evidence(trajectories, rng)
        boot_fit = fit_bradley_terry(boot_wins, boot_games, field)
        boot = compute_matchup_residuals(boot_wins, boot_games, field, boot_fit)["residuals"]
        for key in point:
            if key in boot:
                samples[key].append(boot[key])
    tail = (1.0 - interval) / 2.0
    residuals = {}
    for i, a in enumerate(field):
        for b in field[i + 1 :]:
            key = f"{a}_vs_{b}"
            if key not in point:
                continue
            n = games[(a, b)]
            low = _percentile(samples[key], tail) if samples[key] else None
            high = _percentile(samples[key], 1.0 - tail) if samples[key] else None
            eligible = n >= MIN_DISTINCT_FOR_RATE_CLAIM
            residuals[key] = {
                "entrants": [a, b],
                "residual": point[key],
                "n_distinct": n,
                "evidence": evidence_label(n),
                "low": None if low is None else round(low, 6),
                "high": None if high is None else round(high, 6),
                "eligible": eligible,
                "significant": bool(
                    eligible and low is not None and high is not None and (low > 0 or high < 0)
                ),
            }
    return {
        **_bootstrap_base(trajectories, n_bootstraps, seed),
        "interval": interval,
        "residuals": residuals,
        "significant": [key for key, row in residuals.items() if row["significant"]],
    }


def analyze_outcome_table(
    cells: Sequence[Mapping[str, Any]], field: Sequence[str], *, label: str
) -> dict[str, Any]:
    """Rating model, residuals, upsets and cycles for one outcome table."""
    wins, games = distinct_pairwise_evidence(cells, field)
    fit = fit_bradley_terry(wins, games, field)
    residuals = compute_matchup_residuals(wins, games, field, fit)
    cycles = compute_directed_3_cycles(wins, games, field)
    return {
        "table": label,
        **effective_sample(cells),
        "bradley_terry": fit.to_dict(),
        "ratings_authoritative": fit.authoritative,
        "matchup_residuals": residuals["residuals"],
        "unmodelled_pairs": residuals["unmodelled_pairs"],
        "rmsr": residuals["rmsr"],
        "upset_reversals": compute_upset_reversals(wins, games, field, fit),
        "cycles": cycles,
        "cycle_count": len(cycles),
        "robust_cycle_count": sum(1 for cycle in cycles if not cycle["fragile"]),
        "fragile_cycle_count": sum(1 for cycle in cycles if cycle["fragile"]),
        "edge_rates": {
            f"{a}_vs_{b}": {
                "rate": round(wins[(a, b)] / games[(a, b)], 6),
                "n_distinct": games[(a, b)],
            }
            for i, a in enumerate(field)
            for b in field[i + 1 :]
            if games.get((a, b), 0) > 0
        },
    }


def analyze_experiment_condition(
    cells: Sequence[Mapping[str, Any]],
    field: Sequence[str],
    *,
    tick_limit: int | None = None,
    n_bootstraps: int = 200,
    bootstrap_seed: int = 42,
) -> dict[str, Any]:
    """Analyze one condition; seat-conditioned results lead, pooled results follow.

    * ``seat_pathology`` / ``matchups``: seat-conditioned outcomes, SDI and
      seat bias for every pairing (HD-1).
    * ``tables.seat_a`` / ``tables.seat_b``: the rating model fitted
      separately to the ``candidate_first`` cells (the pairing's first-listed
      entrant holds Seat A) and the ``opponent_first`` cells (it holds Seat
      B). A structural claim needs support in both (review Sec I.5).
    * ``tables.pooled``: the Phase 9 seat-pooled view, kept for
      comparability but marked subordinate; it averages seat effects away
      and says so when any pairing is seat-determined.
    """
    matchups = seat_conditioned_matchups(cells, field)
    pathology = summarize_seat_pathology(matchups, cells)
    by_orientation = {
        "seat_a": [c for c in cells if _orientation(c) == ORIENTATION_CANDIDATE_FIRST],
        "seat_b": [c for c in cells if _orientation(c) == ORIENTATION_OPPONENT_FIRST],
        "pooled": list(cells),
    }
    tables = {}
    for name, subset in by_orientation.items():
        table = analyze_outcome_table(subset, field, label=name)
        table["rmsr_bootstrap"] = bootstrap_rmsr_over_distinct_trajectories(
            subset, field, n_bootstraps=n_bootstraps, seed=bootstrap_seed
        )
        tables[name] = table
    tables["pooled"]["subordinate"] = True
    tables["pooled"]["warning"] = (
        "Seat-pooled view: averages Seat A and Seat B together and can hide seat "
        f"determination; {len(pathology['seat_determined_pairings'])} pairing(s) here have "
        f"SDI >= {SEAT_DETERMINED_SDI}. Read the seat-conditioned results first."
        if pathology["seat_determined_pairings"]
        else "Seat-pooled view: subordinate to the seat-conditioned results."
    )
    seat_results = Counter(cell_seat_result(cell) for cell in cells)
    return {
        "analyzer_version": ANALYZER_VERSION,
        "total_cells": len(cells),
        "effective_sample": effective_sample(cells),
        "outcomes": {
            "seat_a_wins": seat_results[SEAT_A],
            "seat_b_wins": seat_results[SEAT_B],
            "ties": seat_results[TIE],
            "other": seat_results[OTHER],
        },
        "seat_pathology": pathology,
        "matchups": matchups,
        "decision_ticks": decision_tick_summary(cells, tick_limit=tick_limit),
        "termination_reasons": dict(
            sorted(Counter(str(c.get("termination_reason")) for c in cells).items())
        ),
        "tables": tables,
    }


def outcome_transitions(
    control_cells: Sequence[Mapping[str, Any]],
    treatment_cells: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Cell-by-cell control -> treatment transitions over {A, B, tie, other}.

    Cells are matched on (subject, opponent, seed, orientation, occurrence).
    Also counts, among control decisive cells (a winner before the tick
    limit), how many keep the same winning entrant under treatment and how
    many keep it with a decision exactly one tick later.
    """

    def index(cells: Sequence[Mapping[str, Any]]) -> dict[tuple[Any, ...], Mapping[str, Any]]:
        seen: Counter[tuple[Any, ...]] = Counter()
        out: dict[tuple[Any, ...], Mapping[str, Any]] = {}
        for cell in cells:
            base = (cell["subject_id"], cell["opponent_id"], cell.get("seed"), _orientation(cell))
            out[(*base, seen[base])] = cell
            seen[base] += 1
        return out

    control, treatment = index(control_cells), index(treatment_cells)
    matched = sorted(set(control) & set(treatment), key=repr)
    labels = (SEAT_A, SEAT_B, TIE, OTHER)
    matrix = {c: dict.fromkeys(labels, 0) for c in labels}
    decisive = kept = kept_plus_one = 0
    for key in matched:
        before, after = control[key], treatment[key]
        matrix[cell_seat_result(before)][cell_seat_result(after)] += 1
        if cell_winner(before) is not None and before.get("termination_reason") != TICK_LIMIT_REASON:
            decisive += 1
            if (
                cell_winner(after) == cell_winner(before)
                and after.get("termination_reason") != TICK_LIMIT_REASON
            ):
                kept += 1
                if after.get("ticks_run") == (before.get("ticks_run") or 0) + 1:
                    kept_plus_one += 1
    return {
        "matched_cells": len(matched),
        "unmatched_control": len(set(control) - set(treatment)),
        "unmatched_treatment": len(set(treatment) - set(control)),
        "matrix": matrix,
        "n_distinct_transitions": len(
            {(trajectory_key(control[k]), trajectory_key(treatment[k])) for k in matched}
        ),
        "control_decisive": decisive,
        "winner_kept": kept,
        "winner_kept_one_tick_later": kept_plus_one,
        "winner_kept_rate": _ratio(kept, decisive),
        "winner_kept_one_tick_later_rate": _ratio(kept_plus_one, decisive),
    }
