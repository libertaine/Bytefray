"""Thin V6 E2 runner over the consolidated experiment harness.

Defines -- and never automatically executes -- the frozen E2 matrix
(``matrix.py``): conditions C-V4 / C-RS / T-E2, fields F1 / F2 / F3, seeds
1..32, both orientations, 1000 ticks, arena 512.

Subcommands (``python -m tools.research.v6.e2.run_e2 ...``):

* ``plan`` (default): dry run. Builds every evaluation request, checks it,
  and counts the cells with the real evaluation planner. Executes nothing.
* ``execute CONDITION FIELD --confirm-matrix-execution``: runs one
  condition/field through ``experiment_harness.run_experiment``. T-E2
  refuses to start unless ``treatment_unlock`` passes (below).
* ``gate``: compares completed C-V4 and C-RS runs cell by cell and writes
  the gate record (under the current analysis freeze, unless ``--sample``).
* ``requalify``: requalifies the current analysis freeze on the preserved
  control corpus (``requalification.py``) and re-runs the full control gate,
  writing both records under ``<matrix id>/freezes/<freeze id>/``.
* ``--sample``: the control-gate qualification sample (every pairing of the
  matrix, seeds ``SAMPLE_SEEDS`` only), written under its own root. A
  sample gate can never unlock T-E2, and T-E2 has no sample mode.

Fail-closed guards on every execution: the frozen matrix and pre-registration
digests; the live fingerprints of every agent; and, on the exact requests
about to run, the four forbidden overrides (``scheduler_chunk_size``,
``scheduler_rotate_start``, ``kill_weight``, ``instr_per_tick``) all None,
plus the frozen Ruleset, arena, tick limit, seeds and orientations.

T-E2 additionally needs (``treatment_unlock``) a committed analysis freeze that
still matches the live tooling (``analysis_freeze.py``), and a complete passing
control gate and requalification, both recorded under that freeze; and, just
before it runs, a clean tree whose engine source is the one that generated the
reused controls.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from battle_engine.evaluation_planning import build_matrix
from battle_engine.evaluation_service import EvaluationRequest, EvaluationService

from tools.research.v6.e2 import matrix
from tools.research.v6.e2.analysis_freeze import (
    FREEZE_RECORD_PATH,
    current_freeze,
    load_freeze,
    verify_execution_source,
)
from tools.research.v6.e2.control_gate import (
    GATE_RECORD_NAME,
    compare_control_runs,
    require_control_gate,
    write_gate_record,
)
from tools.research.v6.e2.preregistration import load_preregistration, preregistration_digest
from tools.research.v6.e2.requalification import (
    REQUALIFICATION_RECORD_NAME,
    analyzer_requalification,
    corpus_integrity,
    require_requalification,
    write_requalification_record,
)
from tools.research.v6.experiment_harness import (
    REPO_ROOT,
    ResearchExperimentConfig,
    experiment_pairs,
    fingerprint_corpus,
    get_git_provenance,
    plan_evaluation_requests,
    prepare_benchmark_data_root,
    run_experiment,
)

E2_RUNNER_VERSION = 2
DEFAULT_RUN_ROOT = REPO_ROOT / "runs" / "research_v6_e2"
DEFAULT_SAMPLE_ROOT = REPO_ROOT / "runs" / "research_v6_e2_gate_sample"
# Control-gate qualification sample: every pairing, two seeds.
SAMPLE_SEEDS: tuple[int, ...] = (1, 17)


class E2ConfigurationError(RuntimeError):
    """An E2 run would not match the frozen experiment definition."""


def condition_root(run_root: Path, condition_id: str, field_id: str) -> Path:
    return run_root / matrix.matrix_id() / condition_id / field_id


def freeze_root(run_root: Path, freeze_id: str) -> Path:
    """Where the gate and requalification records of one analysis freeze live."""
    return run_root / matrix.matrix_id() / "freezes" / freeze_id


def _expected_matches() -> dict[str, int]:
    return {f.field_id: f.expected_matches for f in matrix.FIELDS}


def experiment_config(
    condition_id: str,
    field_id: str,
    *,
    run_root: Path = DEFAULT_RUN_ROOT,
    sample: bool = False,
    workers: int = 1,
    freeze_id: str | None = None,
) -> ResearchExperimentConfig:
    condition = matrix.condition(condition_id)
    field = matrix.field(field_id)
    if sample and condition_id == matrix.TREATMENT_CONDITION:
        raise E2ConfigurationError("T-E2 has no sample mode; the sample exists only to qualify the gate.")
    seeds = SAMPLE_SEEDS if sample else matrix.SEEDS
    return ResearchExperimentConfig(
        experiment_id=f"{matrix.matrix_id()}-{condition_id}-{field_id}{'-sample' if sample else ''}",
        ruleset_id=condition.ruleset_id,
        arena_sizes=(matrix.ARENA_SIZE,),
        field=field.agents,
        seeds=seeds,
        ticks=matrix.MAX_TICKS,
        both_orientations=matrix.BOTH_ORIENTATIONS,
        output_dir=condition_root(run_root, condition_id, field_id),
        workers=workers,
        pairs=None if field.pairing == "triangular" else field.pairs,
        provenance_extra={
            "e2_matrix_id": matrix.matrix_id(),
            "e2_matrix_digest": matrix.E2_MATRIX_DIGEST,
            "e2_preregistration_sha256": preregistration_digest(),
            "e2_runner_version": E2_RUNNER_VERSION,
            "e2_condition": condition_id,
            "e2_field": field_id,
            "e2_sample": sample,
            "e2_freeze_id": freeze_id,
        },
    )


def check_requests(
    requests: Sequence[EvaluationRequest], condition_id: str, *, seeds: Sequence[int]
) -> None:
    """Fail closed unless every request matches the frozen definition exactly."""
    condition = matrix.condition(condition_id)
    problems: list[str] = []
    for request in requests:
        for name in matrix.FORBIDDEN_REQUEST_OVERRIDES:
            value = getattr(request, name)
            if value is not None:
                problems.append(f"{request.candidate_id}: forbidden override {name}={value!r}")
        expected = {
            "ruleset_id": condition.ruleset_id,
            "arena_size": matrix.ARENA_SIZE,
            "ticks": matrix.MAX_TICKS,
            "seeds": tuple(seeds),
            "both_orientations": matrix.BOTH_ORIENTATIONS,
        }
        for name, value in expected.items():
            if getattr(request, name) != value:
                problems.append(f"{request.candidate_id}: {name}={getattr(request, name)!r} != {value!r}")
    if problems:
        raise E2ConfigurationError("E2 request check failed: " + "; ".join(problems))


def verify_agent_fingerprints(agents: Sequence[str]) -> dict[str, str]:
    live = {name: record["fingerprint"] for name, record in fingerprint_corpus(agents).items()}
    drift = {
        name: (matrix.AGENT_FINGERPRINTS.get(name), live[name])
        for name in agents
        if matrix.AGENT_FINGERPRINTS.get(name) != live[name]
    }
    if drift:
        raise E2ConfigurationError(f"E2 agent fingerprints differ from the frozen definition: {drift}")
    return live


def verify_frozen_definition() -> None:
    matrix.verify_frozen_matrix()
    load_preregistration()


def dry_run_plan(condition_id: str, field_id: str, *, sample: bool = False) -> dict[str, Any]:
    """Plan one condition/field and count its cells with the real evaluation planner."""
    config = experiment_config(condition_id, field_id, sample=sample)
    field = matrix.field(field_id)
    if experiment_pairs(config) != field.pairs:
        raise E2ConfigurationError(f"{field_id}: planned pairs differ from the frozen field")
    with tempfile.TemporaryDirectory(prefix="e2-plan-") as tmp:
        data_root = prepare_benchmark_data_root(Path(tmp) / "env", config.field)
        requests = plan_evaluation_requests(config, matrix.ARENA_SIZE, Path(tmp) / "plan", data_root)
        check_requests(requests, condition_id, seeds=config.seeds)
        service = EvaluationService()
        cells = 0
        rulesets: set[str] = set()
        seeds: set[int] = set()
        orientations: set[str] = set()
        for request in requests:
            specs, evaluation_id = service.preflight(
                candidate_id=request.candidate_id,
                opponent_ids=request.opponent_ids,
                seeds=request.seeds,
                ticks=request.ticks,
                data_root=request.data_root,
                both_orientations=request.both_orientations,
                ruleset_id=request.ruleset_id,
                arena_size=request.arena_size,
            )
            planned = build_matrix(
                request,
                evaluation_id,
                specs,
                None,
                request.resolved_rules_compatibility_id,
                request.resolved_arena_alignment_mode,
            )
            cells += len(planned)
            rulesets.update(cell.rules_compatibility_id for cell in planned)
            seeds.update(cell.seed for cell in planned)
            orientations.update(cell.orientation for cell in planned)
    expected = len(field.pairs) * len(config.seeds) * (2 if config.both_orientations else 1)
    return {
        "condition": condition_id,
        "field": field_id,
        "sample": sample,
        "requests": len(requests),
        "pairs": len(field.pairs),
        "seeds": list(config.seeds),
        "planned_cells": cells,
        "expected_cells": expected,
        "rulesets": sorted(rulesets),
        "orientations": sorted(orientations),
        "planned_seed_set": sorted(seeds),
        "consistent": cells == expected and rulesets == {matrix.condition(condition_id).ruleset_id},
    }


def treatment_unlock(run_root: Path, *, freeze_path: Path = FREEZE_RECORD_PATH) -> dict[str, Any]:
    """Fail closed unless T-E2 may run and be interpreted: a committed analysis
    freeze that matches the live tooling, and a complete passing control gate
    and requalification recorded under that same freeze."""
    freeze = load_freeze(freeze_path)
    records = freeze_root(run_root, freeze["freeze_id"])
    gate = require_control_gate(
        records / GATE_RECORD_NAME,
        matrix_id=matrix.matrix_id(),
        expected_matches=_expected_matches(),
        freeze_id=freeze["freeze_id"],
    )
    requalification = require_requalification(
        records / REQUALIFICATION_RECORD_NAME,
        freeze_id=freeze["freeze_id"],
        expected_matches=_expected_matches(),
    )
    return {"freeze": freeze, "gate": gate, "requalification": requalification}


def execute(
    condition_id: str,
    field_id: str,
    *,
    run_root: Path | None = None,
    confirm: bool = False,
    sample: bool = False,
    workers: int = 1,
    freeze_path: Path = FREEZE_RECORD_PATH,
) -> dict[str, Any]:
    """Run one condition/field. Never called implicitly; requires ``confirm``."""
    if not confirm:
        raise E2ConfigurationError("Refusing to execute: pass confirm=True / --confirm-matrix-execution.")
    root = run_root or (DEFAULT_SAMPLE_ROOT if sample else DEFAULT_RUN_ROOT)
    verify_frozen_definition()
    field = matrix.field(field_id)
    freeze_id = None
    if condition_id == matrix.TREATMENT_CONDITION:
        unlock = treatment_unlock(root, freeze_path=freeze_path)
        verify_execution_source(unlock["freeze"])
        freeze_id = unlock["freeze"]["freeze_id"]
    verify_agent_fingerprints(field.agents)
    config = experiment_config(
        condition_id, field_id, run_root=root, sample=sample, workers=workers, freeze_id=freeze_id
    )
    result = run_experiment(
        config,
        request_guard=lambda requests: check_requests(requests, condition_id, seeds=config.seeds),
    )
    cells = sum(len(condition["cells"]) for condition in result["conditions"])
    expected = len(field.pairs) * len(config.seeds) * 2
    if cells != expected:
        raise E2ConfigurationError(f"{condition_id}/{field_id}: {cells} cells ran, {expected} expected")
    return {"condition": condition_id, "field": field_id, "cells": cells, "output_dir": str(config.output_dir)}


def _compare_controls(root: Path) -> dict[str, dict[str, Any]]:
    v4_id, rs_id = matrix.CONTROL_GATE_CONDITIONS
    fields = {}
    for field in matrix.FIELDS:
        v4_root = condition_root(root, v4_id, field.field_id)
        rs_root = condition_root(root, rs_id, field.field_id)
        if not (v4_root / "experiment_result.json").is_file() or not (
            rs_root / "experiment_result.json"
        ).is_file():
            fields[field.field_id] = {"status": "FAIL", "reason": "control run missing", "cells_compared": 0}
            continue
        fields[field.field_id] = compare_control_runs(v4_root, rs_root)
    return fields


def run_control_gate(
    *, run_root: Path | None = None, sample: bool = False, freeze_path: Path = FREEZE_RECORD_PATH
) -> dict[str, Any]:
    """Compare C-V4 and C-RS for every field and persist the gate record.

    A full gate is recorded under the current analysis freeze; a sample gate
    keeps its own location and can never unlock T-E2.
    """
    root = run_root or (DEFAULT_SAMPLE_ROOT if sample else DEFAULT_RUN_ROOT)
    seeds = SAMPLE_SEEDS if sample else matrix.SEEDS
    freeze_id = None if sample else current_freeze(freeze_path)["freeze_id"]
    path = (
        root / matrix.matrix_id() / GATE_RECORD_NAME
        if freeze_id is None
        else freeze_root(root, freeze_id) / GATE_RECORD_NAME
    )
    return write_gate_record(
        path,
        matrix_id=matrix.matrix_id(),
        fields=_compare_controls(root),
        expected_matches={f.field_id: len(f.pairs) * len(seeds) * 2 for f in matrix.FIELDS},
        sample=sample,
        provenance={**get_git_provenance(), "e2_runner_version": E2_RUNNER_VERSION},
        freeze_id=freeze_id,
    )


def run_requalification(
    *, run_root: Path | None = None, freeze_path: Path = FREEZE_RECORD_PATH, workers: int = 1
) -> dict[str, Any]:
    """Requalify the current analysis freeze on the preserved C-V4 / C-RS corpus.

    Checks every control run's integrity and provenance, runs the capture
    analyzer over every control replay, and re-runs the full control gate;
    writes the gate and requalification records under the freeze. Executes no
    match and reads no T-E2 artifact.
    """
    root = run_root or DEFAULT_RUN_ROOT
    verify_frozen_definition()
    freeze = current_freeze(freeze_path)
    identity = freeze["identity"]
    records = freeze_root(root, freeze["freeze_id"])
    integrity: dict[str, dict[str, Any]] = {}
    fields: dict[str, dict[str, Any]] = {}
    v4_id, rs_id = matrix.CONTROL_GATE_CONDITIONS
    for field in matrix.FIELDS:
        for condition_id in (v4_id, rs_id):
            condition = matrix.condition(condition_id)
            integrity[f"{condition_id}/{field.field_id}"] = corpus_integrity(
                condition_root(root, condition_id, field.field_id),
                ruleset_id=condition.ruleset_id,
                pairs=field.pairs,
                seeds=matrix.SEEDS,
                provenance={
                    "git_sha": identity["control_source_sha"],
                    "git_dirty": False,
                    "ruleset_id": condition.ruleset_id,
                    "e2_matrix_id": matrix.matrix_id(),
                    "e2_matrix_digest": matrix.E2_MATRIX_DIGEST,
                    "e2_preregistration_sha256": preregistration_digest(),
                    "e2_condition": condition_id,
                    "e2_field": field.field_id,
                    "e2_sample": False,
                },
                fingerprints={name: matrix.AGENT_FINGERPRINTS[name] for name in field.agents},
            )
        fields[field.field_id] = analyzer_requalification(
            condition_root(root, v4_id, field.field_id),
            condition_root(root, rs_id, field.field_id),
            workers=workers,
        )
    provenance = {**get_git_provenance(), "e2_runner_version": E2_RUNNER_VERSION, "workers": workers}
    gate = write_gate_record(
        records / GATE_RECORD_NAME,
        matrix_id=matrix.matrix_id(),
        fields=_compare_controls(root),
        expected_matches=_expected_matches(),
        sample=False,
        provenance=provenance,
        freeze_id=freeze["freeze_id"],
    )
    requalification = write_requalification_record(
        records / REQUALIFICATION_RECORD_NAME,
        freeze_id=freeze["freeze_id"],
        matrix_id=matrix.matrix_id(),
        fields=fields,
        integrity=integrity,
        expected_matches=_expected_matches(),
        provenance=provenance,
    )
    return {"freeze_id": freeze["freeze_id"], "gate": gate, "requalification": requalification}


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="run_e2", description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command")
    plan = sub.add_parser("plan", help="dry run: count every planned cell (default)")
    plan.add_argument("--sample", action="store_true")
    run = sub.add_parser("execute", help="run one condition/field")
    run.add_argument("condition", choices=[c.condition_id for c in matrix.CONDITIONS])
    run.add_argument("field", choices=[f.field_id for f in matrix.FIELDS])
    run.add_argument("--confirm-matrix-execution", action="store_true")
    run.add_argument("--sample", action="store_true")
    run.add_argument("--workers", type=int, default=1)
    run.add_argument("--run-root", type=Path)
    gate = sub.add_parser("gate", help="compare C-V4 and C-RS and write the gate record")
    gate.add_argument("--sample", action="store_true")
    gate.add_argument("--run-root", type=Path)
    requalify = sub.add_parser("requalify", help="requalify the analysis freeze on the control corpus")
    requalify.add_argument("--run-root", type=Path)
    requalify.add_argument("--workers", type=int, default=1)
    args = parser.parse_args(argv)

    if args.command in (None, "plan"):
        sample = bool(getattr(args, "sample", False))
        verify_frozen_definition()
        conditions = [
            c.condition_id
            for c in matrix.CONDITIONS
            if not (sample and c.condition_id == matrix.TREATMENT_CONDITION)
        ]
        rows = [dry_run_plan(c, f.field_id, sample=sample) for c in conditions for f in matrix.FIELDS]
        report = {
            "matrix_id": matrix.matrix_id(),
            "matrix_digest": matrix.E2_MATRIX_DIGEST,
            "preregistration_sha256": preregistration_digest(),
            "rows": rows,
            "planned_total": sum(row["planned_cells"] for row in rows),
            "all_consistent": all(row["consistent"] for row in rows),
        }
        print(json.dumps(report, indent=2))
        return 0 if report["all_consistent"] else 1
    if args.command == "execute":
        print(
            json.dumps(
                execute(
                    args.condition,
                    args.field,
                    run_root=args.run_root,
                    confirm=args.confirm_matrix_execution,
                    sample=args.sample,
                    workers=args.workers,
                ),
                indent=2,
            )
        )
        return 0
    if args.command == "requalify":
        result = run_requalification(run_root=args.run_root, workers=args.workers)
        print(json.dumps(result, indent=2))
        passed = result["gate"]["status"] == "PASS" and result["requalification"]["status"] == "PASS"
        return 0 if passed else 1
    record = run_control_gate(run_root=args.run_root, sample=args.sample)
    print(json.dumps(record, indent=2))
    return 0 if record["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
