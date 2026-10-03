"""Thin V6 E3 runner over the consolidated experiment harness.

Defines -- and never automatically executes -- the frozen E3 matrix
(``matrix.py``): conditions C-E2 / T-E3 / C-RS / T-E3K1, fields F1 / F2 /
F2-P / F4, seeds 1..32, both orientations, arena 512, 1000 ticks (F2-P: 1001).

Subcommands (``python -m tools.research.v6.e3.run_e3 ...``):

* ``plan`` (default): dry run. Builds every evaluation request of every
  condition and field, checks it, and counts the cells with the real
  evaluation planner. Executes nothing.
* ``execute CONDITION FIELD --confirm-matrix-execution``: runs one
  condition/field. Every condition needs the committed analysis freeze, a
  clean tree and the frozen engine source. A treatment (T-E3, T-E3K1) also
  needs ``--confirm-treatment-execution`` and the whole unlock chain
  (``treatment_unlock``); it has no sample mode.
* ``telemetry CORPUS``: computes E3 telemetry for a control corpus (``C-E2``,
  ``C-RS``) or a historical parent corpus (``historical-T-E2``,
  ``historical-C-RS``) and writes it under the freeze's record directory.
* ``reproduce``: the parent reproduction gate (new C-E2 / C-RS against the
  preserved E2 corpora, F1 and F2) and fresh-control integrity (every control
  field; F2-P against F2; a determinism re-run of F2-P and F4 sample cells).
* ``qualify``: the analyzer qualification on control data only, including a
  second, independent telemetry pass that must reproduce every row.
* ``populations``: freezes the control populations and control baseline.
* ``d9``: the D9 real-fixture gate.
* ``unlock``: reports whether a treatment may run. Executes nothing.
* ``treatment-telemetry CONDITION``, ``treatment-gates CONDITION`` and
  ``analyze``: after a separately authorized treatment run, its telemetry,
  its hard-stop gates (integrity, the prefix gate, the manipulation checks
  and, for T-E3, the D9 stop), and the frozen analysis. Each needs the full
  unlock chain.

Every control-phase command first checks that no treatment artifact exists
under the run root and stops if one does.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from battle_engine.evaluation_planning import build_matrix
from battle_engine.evaluation_service import EvaluationRequest, EvaluationService

from tools.research.v6.e2 import matrix as e2_matrix
from tools.research.v6.e2.requalification import corpus_integrity
from tools.research.v6.e3 import d9_gate, matrix, populations
from tools.research.v6.e3.analysis_freeze import (
    FREEZE_RECORD_PATH,
    AnalysisFreezeError,
    git_text,
    load_freeze,
    verify_execution_source,
)
from tools.research.v6.e3.analyze_e3 import (
    E3_ANALYSIS_VERSION,
    FieldRun,
    evaluate_hypotheses,
    make_field_run,
)
from tools.research.v6.e3.entrants import fingerprints, prepare_data_root
from tools.research.v6.e3.gates import (
    PARENT_RECORD_NAME,
    TreatmentGateError,
    artifact_dir,
    compare_parent_reproduction,
    d9_completions,
    file_sha256,
    index_cells,
    load_cells,
    manipulation_checks,
    parity_replicate_prefix,
    prefix_gate,
    require_d9,
    require_parent_reproduction,
    result_without_occurrence,
    write_parent_record,
)
from tools.research.v6.e3.preregistration import load_preregistration, preregistration_digest
from tools.research.v6.e3.telemetry import (
    compute_telemetry,
    read_rows,
    row_digests,
    summarize,
    write_rows,
)
from tools.research.v6.experiment_harness import (
    REPO_ROOT,
    ResearchExperimentConfig,
    experiment_pairs,
    get_git_provenance,
    plan_evaluation_requests,
    run_experiment,
)

E3_RUNNER_VERSION = 1
DEFAULT_RUN_ROOT = REPO_ROOT / "runs" / "research_v6_e3"
HISTORICAL_RUN_ROOT = REPO_ROOT / "runs" / "research_v6_e2"
# Qualification samples (every pairing of a field, these seeds only). A
# sample can never unlock a treatment.
SAMPLE_SEEDS: tuple[int, ...] = (1, 17)
QUALIFICATION_RECORD_NAME = "analyzer_qualification.json"
QUALIFICATION_VERSION = 1
HISTORICAL_CORPORA: dict[str, tuple[str, tuple[str, ...]]] = {
    "historical-T-E2": ("T-E2", tuple(f.field_id for f in e2_matrix.FIELDS)),
    "historical-C-RS": ("C-RS", tuple(f.field_id for f in e2_matrix.FIELDS)),
}


class E3ConfigurationError(RuntimeError):
    """An E3 run would not match the frozen experiment definition."""


class TreatmentExposureError(RuntimeError):
    """A treatment artifact exists where only controls may."""


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------


def condition_root(run_root: Path, condition_id: str, field_id: str) -> Path:
    return run_root / matrix.matrix_id() / condition_id / field_id


def freeze_root(run_root: Path, freeze_id: str) -> Path:
    """Where the gate, qualification and telemetry records of one analysis freeze live."""
    return run_root / matrix.matrix_id() / "freezes" / freeze_id


def historical_root(condition_id: str, field_id: str, root: Path = HISTORICAL_RUN_ROOT) -> Path:
    """The preserved E2 corpus a new control reproduces (``C-E2`` <- T-E2, ``C-RS`` <- C-RS)."""
    return root / matrix.HISTORICAL_MATRIX_ID / matrix.HISTORICAL_PARENT[condition_id] / field_id


def telemetry_file(run_root: Path, freeze_id: str, corpus: str, field_id: str) -> Path:
    return freeze_root(run_root, freeze_id) / "telemetry" / corpus / f"{field_id}.jsonl"


def treatment_artifacts(run_root: Path) -> list[str]:
    base = run_root / matrix.matrix_id()
    return sorted(str(base / c) for c in matrix.TREATMENT_CONDITIONS if (base / c).exists())


def assert_no_treatment_artifacts(run_root: Path) -> None:
    found = treatment_artifacts(run_root)
    if found:
        raise TreatmentExposureError(f"STOP: treatment artifacts exist: {found}")


# ---------------------------------------------------------------------------
# Planning and request checks
# ---------------------------------------------------------------------------


def experiment_config(
    condition_id: str,
    field_id: str,
    *,
    run_root: Path = DEFAULT_RUN_ROOT,
    sample: bool = False,
    workers: int = 1,
    freeze_id: str | None = None,
    output_dir: Path | None = None,
) -> ResearchExperimentConfig:
    condition = matrix.condition(condition_id)
    field = matrix.field(field_id)
    if sample and condition.role == matrix.TREATMENT:
        raise E3ConfigurationError("A treatment has no sample mode; samples exist only to qualify control tooling.")
    return ResearchExperimentConfig(
        experiment_id=f"{matrix.matrix_id()}-{condition_id}-{field_id}{'-sample' if sample else ''}",
        ruleset_id=condition.ruleset_id,
        arena_sizes=(matrix.ARENA_SIZE,),
        field=field.agents,
        seeds=SAMPLE_SEEDS if sample else matrix.SEEDS,
        ticks=field.max_ticks,
        both_orientations=matrix.BOTH_ORIENTATIONS,
        output_dir=output_dir or condition_root(run_root, condition_id, field_id),
        workers=workers,
        pairs=None if field.pairing == "triangular" else field.pairs,
        provenance_extra={
            "e3_matrix_id": matrix.matrix_id(),
            "e3_matrix_digest": matrix.E3_MATRIX_DIGEST,
            "e3_preregistration_sha256": preregistration_digest(),
            "e3_runner_version": E3_RUNNER_VERSION,
            "e3_condition": condition_id,
            "e3_field": field_id,
            "e3_sample": sample,
            "e3_freeze_id": freeze_id,
        },
    )


def check_requests(
    requests: Sequence[EvaluationRequest], condition_id: str, field_id: str, *, seeds: Sequence[int]
) -> None:
    """Fail closed unless every request matches the frozen definition exactly."""
    condition = matrix.condition(condition_id)
    field = matrix.field(field_id)
    problems: list[str] = []
    for request in requests:
        for name in matrix.FORBIDDEN_REQUEST_OVERRIDES:
            value = getattr(request, name)
            if value is not None:
                problems.append(f"{request.candidate_id}: forbidden override {name}={value!r}")
        expected = {
            "ruleset_id": condition.ruleset_id,
            "arena_size": matrix.ARENA_SIZE,
            "ticks": field.max_ticks,
            "seeds": tuple(seeds),
            "both_orientations": matrix.BOTH_ORIENTATIONS,
        }
        for name, value in expected.items():
            if getattr(request, name) != value:
                problems.append(f"{request.candidate_id}: {name}={getattr(request, name)!r} != {value!r}")
    if problems:
        raise E3ConfigurationError("E3 request check failed: " + "; ".join(problems))


def verify_agent_fingerprints(agents: Sequence[str]) -> dict[str, str]:
    live = fingerprints(agents)
    drift = {
        name: (matrix.AGENT_FINGERPRINTS.get(name), live[name])
        for name in agents
        if matrix.AGENT_FINGERPRINTS.get(name) != live[name]
    }
    if drift:
        raise E3ConfigurationError(f"E3 agent fingerprints differ from the frozen definition: {drift}")
    return live


def verify_frozen_definition() -> dict[str, Any]:
    matrix.verify_frozen_matrix()
    return load_preregistration()


def dry_run_plan(condition_id: str, field_id: str, *, sample: bool = False) -> dict[str, Any]:
    """Plan one condition/field and count its cells with the real evaluation planner."""
    field = matrix.field(field_id)
    with tempfile.TemporaryDirectory(prefix="e3-plan-") as tmp:
        config = experiment_config(condition_id, field_id, sample=sample, output_dir=Path(tmp) / "out")
        if experiment_pairs(config) != field.pairs:
            raise E3ConfigurationError(f"{field_id}: planned pairs differ from the frozen field")
        data_root = prepare_data_root(Path(tmp) / "env", config.field)
        requests = plan_evaluation_requests(config, matrix.ARENA_SIZE, Path(tmp) / "plan", data_root)
        check_requests(requests, condition_id, field_id, seeds=config.seeds)
        service = EvaluationService()
        cells = 0
        rulesets: set[str] = set()
        ticks: set[int] = set()
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
            ticks.add(request.ticks)
    expected = len(field.pairs) * len(config.seeds) * (2 if config.both_orientations else 1)
    return {
        "condition": condition_id,
        "field": field_id,
        "sample": sample,
        "requests": len(requests),
        "pairs": len(field.pairs),
        "planned_cells": cells,
        "expected_cells": expected,
        "rulesets": sorted(rulesets),
        "ticks": sorted(ticks),
        "orientations": sorted(orientations),
        "planned_seed_set": sorted(seeds),
        "consistent": cells == expected
        and rulesets == {matrix.condition(condition_id).ruleset_id}
        and ticks == {field.max_ticks},
    }


def plan_report() -> dict[str, Any]:
    verify_frozen_definition()
    rows = [dry_run_plan(c.condition_id, f.field_id) for c in matrix.CONDITIONS for f in matrix.FIELDS]
    return {
        "matrix_id": matrix.matrix_id(),
        "matrix_digest": matrix.E3_MATRIX_DIGEST,
        "preregistration_sha256": preregistration_digest(),
        "rows": rows,
        "planned_total": sum(row["planned_cells"] for row in rows),
        "expected_total": matrix.matches_total(),
        "all_consistent": all(row["consistent"] for row in rows) and sum(r["planned_cells"] for r in rows)
        == matrix.matches_total(),
    }


# ---------------------------------------------------------------------------
# Execution
# ---------------------------------------------------------------------------


def _run(config: ResearchExperimentConfig, condition_id: str, field_id: str) -> dict[str, Any]:
    """Guard the planned requests, seed the E3 fixtures, then run the harness."""
    assert config.output_dir is not None
    with tempfile.TemporaryDirectory(prefix="e3-guard-") as tmp:
        planned = plan_evaluation_requests(config, matrix.ARENA_SIZE, Path(tmp), Path(tmp) / "env")
        check_requests(planned, condition_id, field_id, seeds=config.seeds)
    prepare_data_root(config.output_dir / "env", config.field)
    result = run_experiment(
        config, request_guard=lambda requests: check_requests(requests, condition_id, field_id, seeds=config.seeds)
    )
    cells = sum(len(block["cells"]) for block in result["conditions"])
    expected = len(matrix.field(field_id).pairs) * len(config.seeds) * 2
    if cells != expected:
        raise E3ConfigurationError(f"{condition_id}/{field_id}: {cells} cells ran, {expected} expected")
    return {"condition": condition_id, "field": field_id, "cells": cells, "output_dir": str(config.output_dir)}


def execute(
    condition_id: str,
    field_id: str,
    *,
    run_root: Path | None = None,
    confirm: bool = False,
    confirm_treatment: bool = False,
    workers: int = 1,
    freeze_path: Path = FREEZE_RECORD_PATH,
) -> dict[str, Any]:
    """Run one condition/field. Never called implicitly."""
    if not confirm:
        raise E3ConfigurationError("Refusing to execute: pass confirm=True / --confirm-matrix-execution.")
    condition = matrix.condition(condition_id)
    if condition.role == matrix.TREATMENT and not confirm_treatment:
        raise E3ConfigurationError(
            f"Refusing to execute treatment {condition_id}: it needs separate authorization "
            "(confirm_treatment=True / --confirm-treatment-execution) and the full unlock chain."
        )
    root = run_root or DEFAULT_RUN_ROOT
    verify_frozen_definition()
    freeze = load_freeze(freeze_path)
    if condition.role == matrix.TREATMENT:
        treatment_unlock(root, freeze_path=freeze_path)
    else:
        assert_no_treatment_artifacts(root)
    verify_execution_source(freeze)
    field = matrix.field(field_id)
    verify_agent_fingerprints(field.agents)
    config = experiment_config(condition_id, field_id, run_root=root, workers=workers, freeze_id=freeze["freeze_id"])
    assert config.output_dir is not None
    if config.output_dir.exists():
        raise E3ConfigurationError(f"{config.output_dir} already exists; an E3 cell set is never re-run in place.")
    summary = _run(config, condition_id, field_id)
    # Hard stop 10: the source must not have changed, and the tree must still
    # be clean, when the run ends.
    verify_execution_source(load_freeze(freeze_path))
    return summary


# ---------------------------------------------------------------------------
# Telemetry, parent reproduction and analyzer qualification (control data only)
# ---------------------------------------------------------------------------


def corpus_roots(corpus: str, run_root: Path) -> dict[str, Path]:
    if corpus in matrix.CONTROL_CONDITIONS:
        return {f.field_id: condition_root(run_root, corpus, f.field_id) for f in matrix.FIELDS}
    if corpus in HISTORICAL_CORPORA:
        condition, fields = HISTORICAL_CORPORA[corpus]
        return {f: HISTORICAL_RUN_ROOT / matrix.HISTORICAL_MATRIX_ID / condition / f for f in fields}
    raise E3ConfigurationError(f"Unknown or non-control corpus {corpus!r}.")


def write_corpus_telemetry(corpus: str, *, run_root: Path | None = None, workers: int = 1,
                           freeze_path: Path = FREEZE_RECORD_PATH) -> dict[str, Any]:
    root = run_root or DEFAULT_RUN_ROOT
    assert_no_treatment_artifacts(root)
    freeze = load_freeze(freeze_path)
    out = {}
    for field_id, source in corpus_roots(corpus, root).items():
        rows = compute_telemetry(source, workers=workers)
        write_rows(telemetry_file(root, freeze["freeze_id"], corpus, field_id), rows,
                   corpus={"corpus": corpus, "field": field_id, "root": str(source)})
        out[field_id] = summarize(rows)
    return out


def _rows(run_root: Path, freeze_id: str, corpus: str, field_id: str) -> dict[str, dict[str, Any]]:
    return read_rows(telemetry_file(run_root, freeze_id, corpus, field_id))[1]


def _integrity_provenance(condition_id: str, field_id: str, freeze_id: str) -> dict[str, Any]:
    return {
        "git_dirty": False,
        "ruleset_id": matrix.condition(condition_id).ruleset_id,
        "e3_matrix_id": matrix.matrix_id(),
        "e3_matrix_digest": matrix.E3_MATRIX_DIGEST,
        "e3_preregistration_sha256": preregistration_digest(),
        "e3_condition": condition_id,
        "e3_field": field_id,
        "e3_sample": False,
        "e3_freeze_id": freeze_id,
    }


def _rerun_check(condition_id: str, field_id: str, main_root: Path, scratch: Path) -> dict[str, Any]:
    """Re-execute the sample seeds of one fresh field and require byte-identical replays."""
    config = experiment_config(condition_id, field_id, sample=True, output_dir=scratch / condition_id / field_id)
    if config.output_dir is not None and config.output_dir.exists():
        shutil.rmtree(config.output_dir)
    _run(config, condition_id, field_id)
    assert config.output_dir is not None
    rerun, main = index_cells(load_cells(config.output_dir)), index_cells(load_cells(main_root))
    differing = []
    for key, cell in sorted(rerun.items()):
        other = main.get(key)
        if other is None:
            differing.append({"cell": key, "reason": "missing in main corpus"})
            continue
        a, b = artifact_dir(config.output_dir, cell), artifact_dir(main_root, other)
        if file_sha256(a / "replay.jsonl") != file_sha256(b / "replay.jsonl") or result_without_occurrence(
            json.loads((a / "result.json").read_text(encoding="utf-8"))
        ) != result_without_occurrence(json.loads((b / "result.json").read_text(encoding="utf-8"))):
            differing.append({"cell": key, "reason": "replay or result differs"})
    return {"seeds": list(SAMPLE_SEEDS), "cells": len(rerun), "differing": len(differing), "samples": differing[:10],
            "status": "PASS" if rerun and not differing else "FAIL"}


def fresh_integrity(condition_id: str, field_id: str, *, run_root: Path, freeze: dict[str, Any],
                    scratch: Path) -> dict[str, Any]:
    root = condition_root(run_root, condition_id, field_id)
    field = matrix.field(field_id)
    freeze_id = freeze["freeze_id"]
    integrity = corpus_integrity(
        root,
        ruleset_id=matrix.condition(condition_id).ruleset_id,
        pairs=field.pairs,
        seeds=matrix.SEEDS,
        provenance=_integrity_provenance(condition_id, field_id, freeze_id),
        fingerprints={name: matrix.AGENT_FINGERPRINTS[name] for name in field.agents},
    )
    sha = integrity.get("git_sha")
    generation_tree = None if sha is None else git_text("rev-parse", f"{sha}:{freeze['identity']['match_generation_path']}")
    source_ok = generation_tree == freeze["identity"]["match_generation_tree"]
    rows = _rows(run_root, freeze_id, condition_id, field_id)
    clean = summarize(rows)
    report: dict[str, Any] = {
        "cells_compared": len(index_cells(load_cells(root))),
        "integrity": integrity,
        "generation_tree": generation_tree,
        "generation_source_ok": source_ok,
        "telemetry": clean,
    }
    checks = [integrity["status"] == "PASS", source_ok, clean["clean"], clean["analyzed"] == field.expected_matches]
    if field_id == "F2-P":
        main = index_cells(load_cells(condition_root(run_root, condition_id, "F2")))
        replicate = index_cells(load_cells(root))
        failures = []
        for key, cell in sorted(replicate.items()):
            other = main.get(key)
            row = None if other is None else parity_replicate_prefix(
                artifact_dir(condition_root(run_root, condition_id, "F2"), other) / "replay.jsonl",
                artifact_dir(root, cell) / "replay.jsonl",
                tick_limit=matrix.MAX_TICKS,
            )
            if row is None or not row["ok"]:
                failures.append({"cell": key, **(row or {"problems": ["missing in F2"]})})
        report["prefix_against_f2"] = {"cells": len(replicate), "failures": len(failures), "samples": failures[:10]}
        checks.append(not failures)
    if field.historical_field is None:
        report["rerun"] = _rerun_check(condition_id, field_id, root, scratch)
        checks.append(report["rerun"]["status"] == "PASS")
    report["status"] = "PASS" if all(checks) else "FAIL"
    return report


def reproduce(*, run_root: Path | None = None, freeze_path: Path = FREEZE_RECORD_PATH) -> dict[str, Any]:
    """The parent reproduction gate plus fresh-control integrity, recorded under the freeze."""
    root = run_root or DEFAULT_RUN_ROOT
    assert_no_treatment_artifacts(root)
    verify_frozen_definition()
    freeze = load_freeze(freeze_path)
    freeze_id = freeze["freeze_id"]
    reproduction: dict[str, dict[str, Any]] = {}
    fresh: dict[str, dict[str, Any]] = {}
    with tempfile.TemporaryDirectory(prefix="e3-rerun-") as tmp:
        for condition_id in matrix.CONTROL_CONDITIONS:
            historical_corpus = f"historical-{matrix.HISTORICAL_PARENT[condition_id]}"
            reproduction[condition_id] = {}
            fresh[condition_id] = {}
            for field in matrix.FIELDS:
                block = fresh_integrity(condition_id, field.field_id, run_root=root, freeze=freeze, scratch=Path(tmp))
                if field.historical_field is None:
                    fresh[condition_id][field.field_id] = block
                    continue
                comparison = compare_parent_reproduction(
                    condition_root(root, condition_id, field.field_id),
                    historical_root(condition_id, field.historical_field),
                    new_telemetry=_rows(root, freeze_id, condition_id, field.field_id),
                    historical_telemetry=_rows(root, freeze_id, historical_corpus, field.historical_field),
                )
                comparison["integrity"] = block
                if block["status"] != "PASS":
                    comparison["status"] = "FAIL"
                reproduction[condition_id][field.field_id] = comparison
    return write_parent_record(
        freeze_root(root, freeze_id) / PARENT_RECORD_NAME,
        matrix_id=matrix.matrix_id(),
        freeze_id=freeze_id,
        reproduction=reproduction,
        fresh=fresh,
        expected_matches=_expected_matches(),
        sample=False,
        provenance={**get_git_provenance(), "e3_runner_version": E3_RUNNER_VERSION},
    )


def _expected_matches() -> dict[str, dict[str, int]]:
    return {c: {f.field_id: f.expected_matches for f in matrix.FIELDS} for c in matrix.CONTROL_CONDITIONS}


def _qualification_corpora() -> dict[str, tuple[str, ...]]:
    return {
        **{c: matrix.FIELD_IDS for c in matrix.CONTROL_CONDITIONS},
        **{name: fields for name, (_, fields) in HISTORICAL_CORPORA.items()},
    }


def qualify(*, run_root: Path | None = None, workers: int = 1, freeze_path: Path = FREEZE_RECORD_PATH) -> dict[str, Any]:
    """Analyzer qualification on control data only: every stored telemetry row clean,
    and an independent second pass reproducing every row."""
    root = run_root or DEFAULT_RUN_ROOT
    assert_no_treatment_artifacts(root)
    freeze = load_freeze(freeze_path)
    freeze_id = freeze["freeze_id"]
    corpora: dict[str, dict[str, Any]] = {}
    for corpus, fields in _qualification_corpora().items():
        sources = corpus_roots(corpus, root)
        for field_id in fields:
            stored = _rows(root, freeze_id, corpus, field_id)
            second = compute_telemetry(sources[field_id], workers=workers)
            first_digests, second_digests = row_digests(stored), row_digests(second)
            differing = sorted(k for k in set(first_digests) | set(second_digests)
                               if first_digests.get(k) != second_digests.get(k))
            corpora[f"{corpus}/{field_id}"] = {
                **summarize(stored),
                "telemetry_sha256": populations.record_sha256(telemetry_file(root, freeze_id, corpus, field_id)),
                "expected_cells": len(index_cells(load_cells(sources[field_id]))),
                "repeatability": {"cells": len(second), "differing": len(differing), "samples": differing[:10]},
            }
    totals = {
        name: sum(report[name] for report in corpora.values())
        for name in ("analyzed", "analyzer_failures", "cpu_statistics_mismatches", "ownership_reconstruction_disagreements",
                     "capture_engine_disagreements", "capture_attribution_mismatches")
    }
    totals["repeatability_differences"] = sum(r["repeatability"]["differing"] for r in corpora.values())
    complete = all(r["analyzed"] + r["analyzer_failures"] == r["expected_cells"] == r["cells"] for r in corpora.values())
    passed = complete and all(r["clean"] for r in corpora.values()) and totals["repeatability_differences"] == 0
    record = {
        "qualification_version": QUALIFICATION_VERSION,
        "matrix_id": matrix.matrix_id(),
        "freeze_id": freeze_id,
        "note": "Control data only: no T-E3 or T-E3K1 match exists.",
        "corpora": corpora,
        "totals": totals,
        "complete": complete,
        "status": "PASS" if passed else "FAIL",
        "provenance": {**get_git_provenance(), "workers": workers},
    }
    path = freeze_root(root, freeze_id) / QUALIFICATION_RECORD_NAME
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, indent=2, sort_keys=True), encoding="utf-8")
    return record


def require_qualification(path: Path, *, freeze_id: str) -> dict[str, Any]:
    if not path.is_file():
        raise E3ConfigurationError(f"No analyzer qualification record at {path}.")
    record: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    expected = {f"{c}/{f}" for c, fields in _qualification_corpora().items() for f in fields}
    if (record.get("freeze_id") != freeze_id or record.get("status") != "PASS" or record.get("complete") is not True
            or set(record.get("corpora") or {}) != expected):
        raise E3ConfigurationError("Analyzer qualification does not permit treatment.")
    return record


# ---------------------------------------------------------------------------
# Populations, the D9 gate and the treatment unlock
# ---------------------------------------------------------------------------


def control_runs(condition_id: str, *, run_root: Path, freeze_id: str) -> dict[str, FieldRun]:
    return {
        f.field_id: make_field_run(
            condition_id,
            f.field_id,
            load_cells(condition_root(run_root, condition_id, f.field_id)),
            _rows(run_root, freeze_id, condition_id, f.field_id),
        )
        for f in matrix.FIELDS
    }


def compute_populations(*, run_root: Path, freeze_id: str) -> dict[str, Any]:
    return populations.build_record(
        freeze_id=freeze_id,
        preregistration_sha256=preregistration_digest(),
        prereg=load_preregistration(),
        arms={arm: control_runs(control, run_root=run_root, freeze_id=freeze_id)
              for arm, control in populations.ARM_CONTROLS.items()},
    )


def freeze_populations(*, run_root: Path | None = None, freeze_path: Path = FREEZE_RECORD_PATH,
                       out_path: Path = populations.POPULATIONS_PATH) -> dict[str, Any]:
    root = run_root or DEFAULT_RUN_ROOT
    assert_no_treatment_artifacts(root)
    freeze = load_freeze(freeze_path)
    record = compute_populations(run_root=root, freeze_id=freeze["freeze_id"])
    sha = populations.write_record(out_path, record)
    populations.write_record(freeze_root(root, freeze["freeze_id"]) / out_path.name, record)
    return {"path": str(out_path), "sha256": sha,
            "counts": {arm: body["baseline"]["population_counts"] for arm, body in record["arms"].items()}}


def run_d9(*, run_root: Path | None = None, freeze_path: Path = FREEZE_RECORD_PATH) -> dict[str, Any]:
    root = run_root or DEFAULT_RUN_ROOT
    assert_no_treatment_artifacts(root)
    freeze = load_freeze(freeze_path)
    record = d9_gate.run_gate()
    return d9_gate.write_record(freeze_root(root, freeze["freeze_id"]) / d9_gate.D9_RECORD_NAME, record,
                                freeze_id=freeze["freeze_id"], provenance=get_git_provenance())


CONTROL_RECORDS: tuple[str, ...] = (PARENT_RECORD_NAME, QUALIFICATION_RECORD_NAME, d9_gate.D9_RECORD_NAME)


def treatment_unlock(run_root: Path, *, freeze_path: Path = FREEZE_RECORD_PATH,
                     populations_path: Path = populations.POPULATIONS_PATH) -> dict[str, Any]:
    """Fail closed unless a treatment may run: the committed freeze holds, its
    control qualification names passing, complete, non-sample records whose
    bytes are unchanged, and the frozen populations still recompute from the
    control corpus."""
    freeze = load_freeze(freeze_path)
    freeze_id = freeze["freeze_id"]
    qualification = freeze.get("control_qualification") or {}
    if qualification.get("status") != "PASS":
        raise AnalysisFreezeError(f"The freeze's control qualification is {qualification.get('status')!r}, not PASS.")
    records = freeze_root(run_root, freeze_id)
    for name in CONTROL_RECORDS:
        pinned = (qualification.get("records") or {}).get(name) or {}
        path = records / name
        if not path.is_file() or populations.record_sha256(path) != pinned.get("sha256"):
            raise AnalysisFreezeError(f"Control record {name} is missing or differs from the committed freeze.")
    parent = require_parent_reproduction(records / PARENT_RECORD_NAME, matrix_id=matrix.matrix_id(),
                                         freeze_id=freeze_id, expected_matches=_expected_matches())
    analyzer = require_qualification(records / QUALIFICATION_RECORD_NAME, freeze_id=freeze_id)
    d9 = d9_gate.require_d9_gate(records / d9_gate.D9_RECORD_NAME, freeze_id=freeze_id)
    for corpus in matrix.CONTROL_CONDITIONS:
        for field_id in matrix.FIELD_IDS:
            pinned_sha = analyzer["corpora"][f"{corpus}/{field_id}"]["telemetry_sha256"]
            if populations.record_sha256(telemetry_file(run_root, freeze_id, corpus, field_id)) != pinned_sha:
                raise AnalysisFreezeError(f"Telemetry {corpus}/{field_id} differs from the qualified file.")
    frozen = populations.load_record(populations_path, freeze_id=freeze_id,
                                     expected_sha256=(qualification.get("populations") or {}).get("sha256"))
    populations.require_recomputes(frozen, compute_populations(run_root=run_root, freeze_id=freeze_id))
    return {"freeze": freeze, "parent": parent, "analyzer": analyzer, "d9": d9, "populations": frozen}


# ---------------------------------------------------------------------------
# Treatment side (after separately authorized execution only)
# ---------------------------------------------------------------------------

ANALYSIS_RECORD_NAME = "e3_analysis.json"


def treatment_gate_record_name(condition_id: str) -> str:
    return f"treatment_gates_{condition_id}.json"


def write_treatment_telemetry(condition_id: str, *, run_root: Path | None = None, workers: int = 1,
                              freeze_path: Path = FREEZE_RECORD_PATH) -> dict[str, Any]:
    """Telemetry for an executed treatment, behind the full unlock chain."""
    if matrix.condition(condition_id).role != matrix.TREATMENT:
        raise E3ConfigurationError(f"{condition_id} is not a treatment.")
    root = run_root or DEFAULT_RUN_ROOT
    freeze_id = treatment_unlock(root, freeze_path=freeze_path)["freeze"]["freeze_id"]
    out = {}
    for f in matrix.FIELDS:
        source = condition_root(root, condition_id, f.field_id)
        rows = compute_telemetry(source, workers=workers)
        write_rows(telemetry_file(root, freeze_id, condition_id, f.field_id), rows,
                   corpus={"corpus": condition_id, "field": f.field_id, "root": str(source)})
        out[f.field_id] = summarize(rows)
    return out


def treatment_gate_report(
    condition_id: str,
    *,
    control_roots: dict[str, Path],
    treatment_roots: dict[str, Path],
    rows: dict[str, dict[str, dict[str, Any]]],
    frozen: dict[str, dict[str, list[str]]],
    integrity: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Hard stops 5-9 for one treatment, field by field: integrity, the prefix
    gate against its parent control, the manipulation checks under
    ``disruption_slot_limit = 1``, and the D9 completions (a stop for T-E3)."""
    fields: dict[str, Any] = {}
    completions: list[dict[str, Any]] = []
    for field_id in matrix.FIELD_IDS:
        found = d9_completions(rows[field_id])
        completions += [{"field": field_id, **row} for row in found]
        report: dict[str, Any] = {
            "prefix": prefix_gate(control_roots[field_id], treatment_roots[field_id],
                                  frozen_hit_free=frozen[field_id]["hit_free"]),
            "manipulation": manipulation_checks(rows[field_id], slot_limited=True),
            "d9_completions": len(found),
        }
        if integrity is not None:
            report["integrity"] = integrity[field_id]
        checks = [report["prefix"]["status"] == "PASS", report["manipulation"]["status"] == "PASS"]
        checks.append(integrity is None or integrity[field_id]["status"] == "PASS")
        report["status"] = "PASS" if all(checks) else "FAIL"
        fields[field_id] = report
    d9_stop = condition_id == matrix.PRIMARY_TREATMENT and bool(completions)
    return {
        "condition": condition_id,
        "parent": matrix.condition(condition_id).parent,
        "fields": fields,
        "d9_completions": completions[:20],
        "d9_completion_count": len(completions),
        "d9_stop": d9_stop,
        "status": "PASS" if all(r["status"] == "PASS" for r in fields.values()) and not d9_stop else "FAIL",
    }


def treatment_gates(condition_id: str, *, run_root: Path | None = None,
                    freeze_path: Path = FREEZE_RECORD_PATH) -> dict[str, Any]:
    """Run and record one treatment's hard-stop gates; raise on any failure."""
    root = run_root or DEFAULT_RUN_ROOT
    unlock = treatment_unlock(root, freeze_path=freeze_path)
    freeze_id = unlock["freeze"]["freeze_id"]
    condition = matrix.condition(condition_id)
    if condition.parent is None:
        raise E3ConfigurationError(f"{condition_id} is not a treatment.")
    frozen = unlock["populations"]["arms"][condition.arm]["populations"]
    integrity = {
        f.field_id: corpus_integrity(
            condition_root(root, condition_id, f.field_id), ruleset_id=condition.ruleset_id, pairs=f.pairs,
            seeds=matrix.SEEDS, provenance=_integrity_provenance(condition_id, f.field_id, freeze_id),
            fingerprints={name: matrix.AGENT_FINGERPRINTS[name] for name in f.agents})
        for f in matrix.FIELDS
    }
    record = treatment_gate_report(
        condition_id,
        control_roots={f: condition_root(root, condition.parent, f) for f in matrix.FIELD_IDS},
        treatment_roots={f: condition_root(root, condition_id, f) for f in matrix.FIELD_IDS},
        rows={f: _rows(root, freeze_id, condition_id, f) for f in matrix.FIELD_IDS},
        frozen=frozen,
        integrity=integrity,
    )
    record.update({"freeze_id": freeze_id, "provenance": get_git_provenance()})
    path = freeze_root(root, freeze_id) / treatment_gate_record_name(condition_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, indent=2, sort_keys=True), encoding="utf-8")
    require_d9(condition_id, record["d9_completions"], primary_treatment=matrix.PRIMARY_TREATMENT)
    if record["status"] != "PASS":
        raise TreatmentGateError(f"STOP: {condition_id} failed its treatment gates; see {path}.")
    return record


def analysis_report(
    *,
    runs: dict[str, dict[str, FieldRun]],
    frozen: dict[str, Any],
    prereg: dict[str, Any],
) -> dict[str, Any]:
    """The frozen analysis: the primary arm (D0-D9, with T-E3K1 for D9's
    companion clause) and the companion arm's readings (O-COMPANION)."""
    arms = frozen["arms"]
    primary = evaluate_hypotheses(
        runs["C-E2"], runs["T-E3"], arms[matrix.PRIMARY_ARM]["populations"], prereg,
        control_residuals=arms[matrix.PRIMARY_ARM]["baseline"]["residuals_f1"],
        companion_treatment=runs["T-E3K1"], arm=matrix.PRIMARY_ARM,
    )
    companion = evaluate_hypotheses(
        runs["C-RS"], runs["T-E3K1"], arms[matrix.COMPANION_ARM]["populations"], prereg,
        control_residuals=arms[matrix.COMPANION_ARM]["baseline"]["residuals_f1"], arm=matrix.COMPANION_ARM,
    )
    return {
        "e3_analysis_version": E3_ANALYSIS_VERSION,
        "matrix_id": matrix.matrix_id(),
        "preregistration_sha256": preregistration_digest(),
        "primary": primary,
        "companion": companion,
        "interpretation": prereg["interpretation"],
        "note": "Criterion statuses only; verdicts are read under the pre-registered interpretation table.",
    }


def analyze(*, run_root: Path | None = None, freeze_path: Path = FREEZE_RECORD_PATH) -> dict[str, Any]:
    """Run the frozen analysis once both treatments passed their gates."""
    root = run_root or DEFAULT_RUN_ROOT
    unlock = treatment_unlock(root, freeze_path=freeze_path)
    freeze_id = unlock["freeze"]["freeze_id"]
    for condition_id in matrix.TREATMENT_CONDITIONS:
        path = freeze_root(root, freeze_id) / treatment_gate_record_name(condition_id)
        gate = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
        if gate.get("status") != "PASS" or gate.get("freeze_id") != freeze_id:
            raise TreatmentGateError(f"{condition_id} has no passing treatment gate record under {freeze_id}.")
    runs = {c.condition_id: control_runs(c.condition_id, run_root=root, freeze_id=freeze_id) for c in matrix.CONDITIONS}
    record = analysis_report(runs=runs, frozen=unlock["populations"], prereg=load_preregistration())
    record.update({"freeze_id": freeze_id, "provenance": get_git_provenance()})
    path = freeze_root(root, freeze_id) / ANALYSIS_RECORD_NAME
    path.write_text(json.dumps(record, indent=2, sort_keys=True, default=str), encoding="utf-8")
    return record


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="run_e3", description=(__doc__ or "").splitlines()[0])
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("plan", help="dry run: count every planned cell (default)")
    run = sub.add_parser("execute", help="run one condition/field")
    run.add_argument("condition", choices=[c.condition_id for c in matrix.CONDITIONS])
    run.add_argument("field", choices=list(matrix.FIELD_IDS))
    run.add_argument("--confirm-matrix-execution", action="store_true")
    run.add_argument("--confirm-treatment-execution", action="store_true")
    run.add_argument("--workers", type=int, default=1)
    run.add_argument("--run-root", type=Path)
    tele = sub.add_parser("telemetry", help="E3 telemetry for a control or historical parent corpus")
    tele.add_argument("corpus", choices=[*matrix.CONTROL_CONDITIONS, *HISTORICAL_CORPORA])
    tele.add_argument("--workers", type=int, default=1)
    tele.add_argument("--run-root", type=Path)
    for name, text in (("reproduce", "parent reproduction and fresh-control integrity"),
                       ("populations", "freeze the control populations and baseline"),
                       ("d9", "the D9 real-fixture gate"),
                       ("unlock", "report whether a treatment may run (executes nothing)")):
        item = sub.add_parser(name, help=text)
        item.add_argument("--run-root", type=Path)
    qual = sub.add_parser("qualify", help="analyzer qualification on control data")
    qual.add_argument("--workers", type=int, default=1)
    qual.add_argument("--run-root", type=Path)
    t_tele = sub.add_parser("treatment-telemetry", help="telemetry for an executed treatment (unlock required)")
    t_tele.add_argument("condition", choices=list(matrix.TREATMENT_CONDITIONS))
    t_tele.add_argument("--workers", type=int, default=1)
    t_tele.add_argument("--run-root", type=Path)
    t_gate = sub.add_parser("treatment-gates", help="a treatment's hard-stop gates (unlock required)")
    t_gate.add_argument("condition", choices=list(matrix.TREATMENT_CONDITIONS))
    t_gate.add_argument("--run-root", type=Path)
    final = sub.add_parser("analyze", help="the frozen analysis (both treatments' gates must pass)")
    final.add_argument("--run-root", type=Path)
    args = parser.parse_args(argv)

    def emit(value: Any) -> None:
        print(json.dumps(value, indent=2, sort_keys=True, default=str))

    if args.command in (None, "plan"):
        report = plan_report()
        emit(report)
        return 0 if report["all_consistent"] else 1
    if args.command == "execute":
        emit(execute(args.condition, args.field, run_root=args.run_root, confirm=args.confirm_matrix_execution,
                     confirm_treatment=args.confirm_treatment_execution, workers=args.workers))
        return 0
    if args.command == "telemetry":
        summary = write_corpus_telemetry(args.corpus, run_root=args.run_root, workers=args.workers)
        emit(summary)
        return 0 if all(row["clean"] for row in summary.values()) else 1
    if args.command == "reproduce":
        record = reproduce(run_root=args.run_root)
        emit({k: v for k, v in record.items() if k not in ("reproduction", "fresh")} | {
            "fields": {f"{c}/{f}": r["status"] for block in ("reproduction", "fresh")
                       for c, fields in record[block].items() for f, r in fields.items()}})
        return 0 if record["status"] == "PASS" and record["complete"] else 1
    if args.command == "qualify":
        record = qualify(run_root=args.run_root, workers=args.workers)
        emit({k: v for k, v in record.items() if k != "corpora"})
        return 0 if record["status"] == "PASS" else 1
    if args.command == "populations":
        emit(freeze_populations(run_root=args.run_root))
        return 0
    if args.command == "d9":
        record = run_d9(run_root=args.run_root)
        emit({k: v for k, v in record.items() if k != "scenarios"})
        return 0 if record["status"] == "PASS" else 1
    if args.command == "treatment-telemetry":
        treated = write_treatment_telemetry(args.condition, run_root=args.run_root, workers=args.workers)
        emit(treated)
        return 0 if all(row["clean"] for row in treated.values()) else 1
    if args.command == "treatment-gates":
        record = treatment_gates(args.condition, run_root=args.run_root)
        emit({k: v for k, v in record.items() if k != "fields"})
        return 0
    if args.command == "analyze":
        record = analyze(run_root=args.run_root)
        emit({"freeze_id": record["freeze_id"], "primary": record["primary"]["interpretation_inputs"],
              "companion": record["companion"]["interpretation_inputs"]})
        return 0
    try:
        treatment_unlock(args.run_root or DEFAULT_RUN_ROOT)
    except Exception as exc:
        emit({"unlocked": False, "reason": f"{type(exc).__name__}: {exc}"})
        return 1
    emit({"unlocked": True})
    return 0


if __name__ == "__main__":
    sys.exit(main())
