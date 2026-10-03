"""Thin V6 E4 runner over the consolidated experiment harness.

Defines -- and never automatically executes -- the frozen E4 matrix
(``matrix.py``): conditions C-E4 / T-E4 / C-E4K1 / T-E4K1, fields F1 / F2 /
F2-P / F4, seeds 1..32, per-field orientations, arena 512, 1000 ticks (F2-P:
1001).

Subcommands (``python -m tools.research.v6.e4.run_e4 ...``):

* ``plan`` (default): dry run. Builds every evaluation request of every
  condition and field, checks it, and counts the cells with the real
  evaluation planner (15,232). Executes nothing.
* ``execute CONDITION FIELD --confirm-matrix-execution``: runs one
  condition/field. Every condition needs the committed analysis freeze, a
  clean tree and the frozen engine and tooling source. A treatment (T-E4,
  T-E4K1) also needs ``--confirm-treatment-execution`` and the whole unlock
  chain (``treatment_unlock``).
* ``telemetry CORPUS``: E4 telemetry (E3 telemetry plus E4 metrics) for a
  control (``C-E4``, ``C-E4K1``) or a historical parent corpus
  (``historical-T-E3``, ``historical-T-E3K1``, the E4-field cells only).
* ``reproduce``: the parent reproduction gate (every re-run control field
  against the preserved T-E3 / T-E3K1 cells), the E3 continuity check and the
  twin-mirror relabel gate on the controls.
* ``qualify``: the analyzer qualification on control data only, including a
  second, independent telemetry pass that must reproduce every row.
* ``populations``: freezes the control populations, contest classes, mirror
  seed units, baselines and the control-vs-control census.
* ``manipulation``: the G.4' manipulation gate. ``d9``: the D9' real-fixture gate.
* ``unlock``: reports whether a treatment may run. Executes nothing.
* ``treatment-telemetry``, ``treatment-gates`` and ``analyze``: after a
  separately authorized treatment run only; each needs the full unlock chain.

Every control-phase command first checks that no treatment artifact exists
under the run root and stops if one does.
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

from tools.research.v6.e3 import telemetry as e3_telemetry
from tools.research.v6.e3.entrants import fingerprints, prepare_data_root
from tools.research.v6.e3.gates import (
    PARENT_RECORD_NAME,
    load_cells,
    require_parent_reproduction,
    write_parent_record,
)
from tools.research.v6.e4 import contest_classes, d9_gate, manipulation_gate, matrix, populations
from tools.research.v6.e4.analysis_freeze import (
    FREEZE_RECORD_PATH,
    AnalysisFreezeError,
    git_text,
    load_freeze,
    verify_execution_source,
)
from tools.research.v6.e4.analyze_e4 import (
    E4_ANALYSIS_VERSION,
    FieldRun,
    evaluate_hypotheses,
    make_field_run,
)
from tools.research.v6.e4.gates import (
    TreatmentGateError,
    compare_parent_subset,
    corpus_integrity,
    e3_continuity,
    field_keys,
    field_orientations,
    manipulation_checks,
    record_sha256,
    relabel_gate,
    require_d9_prime,
    require_relabel,
)
from tools.research.v6.e4.preregistration import load_preregistration, preregistration_digest
from tools.research.v6.e4.telemetry import (
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

E4_RUNNER_VERSION = 1
DEFAULT_RUN_ROOT = REPO_ROOT / "runs" / "research_v6_e4"
HISTORICAL_RUN_ROOT = REPO_ROOT / "runs" / "research_v6_e3"
QUALIFICATION_RECORD_NAME = "analyzer_qualification.json"
QUALIFICATION_VERSION = 1
HISTORICAL_CORPORA: dict[str, str] = {f"historical-{c}": c for c in matrix.HISTORICAL_PARENT.values()}


class E4ConfigurationError(RuntimeError):
    """An E4 run would not match the frozen experiment definition."""


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
    """The preserved E3 corpus a re-run control reproduces (C-E4 <- T-E3, C-E4K1 <- T-E3K1)."""
    return root / matrix.HISTORICAL_MATRIX_ID / matrix.HISTORICAL_PARENT[condition_id] / field_id


def frozen_e3_telemetry_file(historical_condition: str, field_id: str, root: Path = HISTORICAL_RUN_ROOT) -> Path:
    """E3 freeze v1's frozen telemetry of one historical treatment field."""
    return (root / matrix.HISTORICAL_MATRIX_ID / "freezes" / matrix.HISTORICAL_FREEZE_ID / "telemetry"
            / historical_condition / f"{field_id}.jsonl")


def telemetry_file(run_root: Path, freeze_id: str, corpus: str, field_id: str) -> Path:
    return freeze_root(run_root, freeze_id) / "telemetry" / corpus / f"{field_id}.jsonl"


def treatment_artifacts(run_root: Path) -> list[str]:
    base = run_root / matrix.matrix_id()
    found = [str(base / c) for c in matrix.TREATMENT_CONDITIONS if (base / c).exists()]
    records = base / "freezes"
    if records.is_dir():
        found += [str(p) for p in records.glob("*/telemetry/T-*") if p.exists()]
    return sorted(found)


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
    workers: int = 1,
    freeze_id: str | None = None,
    output_dir: Path | None = None,
    seeds: Sequence[int] | None = None,
) -> ResearchExperimentConfig:
    condition = matrix.condition(condition_id)
    field = matrix.field(field_id)
    return ResearchExperimentConfig(
        experiment_id=f"{matrix.matrix_id()}-{condition_id}-{field_id}",
        ruleset_id=condition.ruleset_id,
        arena_sizes=(matrix.ARENA_SIZE,),
        field=field.agents,
        seeds=tuple(seeds) if seeds is not None else matrix.SEEDS,
        ticks=field.max_ticks,
        both_orientations=field.both_orientations,
        output_dir=output_dir or condition_root(run_root, condition_id, field_id),
        workers=workers,
        pairs=None if field.pairing == "triangular" else field.pairs,
        provenance_extra={
            "e4_matrix_id": matrix.matrix_id(),
            "e4_matrix_digest": matrix.E4_MATRIX_DIGEST,
            "e4_preregistration_sha256": preregistration_digest(),
            "e4_runner_version": E4_RUNNER_VERSION,
            "e4_condition": condition_id,
            "e4_field": field_id,
            "e4_freeze_id": freeze_id,
        },
    )


def check_requests(requests: Sequence[EvaluationRequest], condition_id: str, field_id: str, *,
                   seeds: Sequence[int] = matrix.SEEDS) -> None:
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
            "both_orientations": field.both_orientations,
        }
        for name, value in expected.items():
            if getattr(request, name) != value:
                problems.append(f"{request.candidate_id}: {name}={getattr(request, name)!r} != {value!r}")
    if problems:
        raise E4ConfigurationError("E4 request check failed: " + "; ".join(problems))


def verify_agent_fingerprints(agents: Sequence[str]) -> dict[str, str]:
    live = fingerprints(agents)
    drift = {name: (matrix.AGENT_FINGERPRINTS.get(name), live[name]) for name in agents
             if matrix.AGENT_FINGERPRINTS.get(name) != live[name]}
    if drift:
        raise E4ConfigurationError(f"E4 agent fingerprints differ from the frozen definition: {drift}")
    return live


def verify_frozen_definition() -> dict[str, Any]:
    matrix.verify_frozen_matrix()
    return load_preregistration()


def dry_run_plan(condition_id: str, field_id: str) -> dict[str, Any]:
    """Plan one condition/field and count its cells with the real evaluation planner."""
    field = matrix.field(field_id)
    with tempfile.TemporaryDirectory(prefix="e4-plan-") as tmp:
        config = experiment_config(condition_id, field_id, output_dir=Path(tmp) / "out")
        if experiment_pairs(config) != field.pairs:
            raise E4ConfigurationError(f"{field_id}: planned pairs differ from the frozen field")
        data_root = prepare_data_root(Path(tmp) / "env", config.field)
        requests = plan_evaluation_requests(config, matrix.ARENA_SIZE, Path(tmp) / "plan", data_root)
        check_requests(requests, condition_id, field_id)
        service = EvaluationService()
        cells = 0
        rulesets: set[str] = set()
        orientations: set[str] = set()
        seeds: set[int] = set()
        for request in requests:
            specs, evaluation_id = service.preflight(
                candidate_id=request.candidate_id, opponent_ids=request.opponent_ids, seeds=request.seeds,
                ticks=request.ticks, data_root=request.data_root, both_orientations=request.both_orientations,
                ruleset_id=request.ruleset_id, arena_size=request.arena_size,
            )
            planned = build_matrix(request, evaluation_id, specs, None, request.resolved_rules_compatibility_id,
                                   request.resolved_arena_alignment_mode)
            cells += len(planned)
            rulesets.update(cell.rules_compatibility_id for cell in planned)
            orientations.update(cell.orientation for cell in planned)
            seeds.update(cell.seed for cell in planned)
    return {
        "condition": condition_id, "field": field_id, "requests": len(requests), "pairs": len(field.pairs),
        "planned_cells": cells, "expected_cells": field.expected_matches, "rulesets": sorted(rulesets),
        "orientations": sorted(orientations), "seeds": len(seeds), "ticks": field.max_ticks,
        "consistent": cells == field.expected_matches and rulesets == {matrix.condition(condition_id).ruleset_id}
        and len(orientations) == field.orientations and seeds == set(matrix.SEEDS),
    }


def plan_report() -> dict[str, Any]:
    verify_frozen_definition()
    rows = [dry_run_plan(c.condition_id, f.field_id) for c in matrix.CONDITIONS for f in matrix.FIELDS]
    planned = sum(row["planned_cells"] for row in rows)
    return {
        "matrix_id": matrix.matrix_id(),
        "matrix_digest": matrix.E4_MATRIX_DIGEST,
        "preregistration_sha256": preregistration_digest(),
        "contest_classes_sha256": contest_classes.CONTEST_CLASSES_SHA256,
        "rows": rows,
        "planned_total": planned,
        "expected_total": matrix.matches_total(),
        "all_consistent": all(row["consistent"] for row in rows) and planned == matrix.matches_total() == 15232,
    }


# ---------------------------------------------------------------------------
# Execution
# ---------------------------------------------------------------------------


def _run(config: ResearchExperimentConfig, condition_id: str, field_id: str) -> dict[str, Any]:
    """Guard the planned requests, seed the E3 fixtures, then run the harness."""
    assert config.output_dir is not None
    with tempfile.TemporaryDirectory(prefix="e4-guard-") as tmp:
        planned = plan_evaluation_requests(config, matrix.ARENA_SIZE, Path(tmp), Path(tmp) / "env")
        check_requests(planned, condition_id, field_id, seeds=config.seeds)
    prepare_data_root(config.output_dir / "env", config.field)
    result = run_experiment(
        config, request_guard=lambda requests: check_requests(requests, condition_id, field_id, seeds=config.seeds)
    )
    cells = sum(len(block["cells"]) for block in result["conditions"])
    field = matrix.field(field_id)
    expected = len(field.pairs) * len(config.seeds) * field.orientations
    if cells != expected:
        raise E4ConfigurationError(f"{condition_id}/{field_id}: {cells} cells ran, {expected} expected")
    return {"condition": condition_id, "field": field_id, "cells": cells, "output_dir": str(config.output_dir)}


def execute(condition_id: str, field_id: str, *, run_root: Path | None = None, confirm: bool = False,
            confirm_treatment: bool = False, workers: int = 1, freeze_path: Path = FREEZE_RECORD_PATH) -> dict[str, Any]:
    """Run one condition/field. Never called implicitly."""
    if not confirm:
        raise E4ConfigurationError("Refusing to execute: pass confirm=True / --confirm-matrix-execution.")
    condition = matrix.condition(condition_id)
    if condition.role == matrix.TREATMENT and not confirm_treatment:
        raise E4ConfigurationError(
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
        raise E4ConfigurationError(f"{config.output_dir} already exists; an E4 cell set is never re-run in place.")
    summary = _run(config, condition_id, field_id)
    verify_execution_source(load_freeze(freeze_path))
    return summary


# ---------------------------------------------------------------------------
# Telemetry, parent reproduction and analyzer qualification (control data only)
# ---------------------------------------------------------------------------


def corpus_roots(corpus: str, run_root: Path) -> dict[str, Path]:
    if corpus in matrix.CONTROL_CONDITIONS:
        return {f.field_id: condition_root(run_root, corpus, f.field_id) for f in matrix.FIELDS}
    if corpus in HISTORICAL_CORPORA:
        historical = HISTORICAL_CORPORA[corpus]
        return {f.field_id: HISTORICAL_RUN_ROOT / matrix.HISTORICAL_MATRIX_ID / historical / f.historical_field
                for f in matrix.FIELDS}
    raise E4ConfigurationError(f"Unknown or non-control corpus {corpus!r}.")


def corpus_keys(corpus: str, field_id: str, run_root: Path) -> set[str] | None:
    """A historical corpus is analyzed on the E4-field cells only (the matching control's cells)."""
    if corpus in HISTORICAL_CORPORA:
        control = next(c for c, h in matrix.HISTORICAL_PARENT.items() if h == HISTORICAL_CORPORA[corpus])
        return field_keys(condition_root(run_root, control, field_id))
    return None


def write_corpus_telemetry(corpus: str, *, run_root: Path | None = None, workers: int = 1,
                           freeze_path: Path = FREEZE_RECORD_PATH) -> dict[str, Any]:
    root = run_root or DEFAULT_RUN_ROOT
    assert_no_treatment_artifacts(root)
    freeze = load_freeze(freeze_path)
    out = {}
    for field_id, source in corpus_roots(corpus, root).items():
        rows = compute_telemetry(source, workers=workers, keys=corpus_keys(corpus, field_id, root))
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
        "e4_matrix_id": matrix.matrix_id(),
        "e4_matrix_digest": matrix.E4_MATRIX_DIGEST,
        "e4_preregistration_sha256": preregistration_digest(),
        "e4_condition": condition_id,
        "e4_field": field_id,
        "e4_freeze_id": freeze_id,
    }


def control_integrity(condition_id: str, field_id: str, *, run_root: Path, freeze: dict[str, Any]) -> dict[str, Any]:
    root = condition_root(run_root, condition_id, field_id)
    field = matrix.field(field_id)
    freeze_id = freeze["freeze_id"]
    integrity = corpus_integrity(
        root, ruleset_id=matrix.condition(condition_id).ruleset_id, pairs=field.pairs, seeds=matrix.SEEDS,
        provenance=_integrity_provenance(condition_id, field_id, freeze_id),
        fingerprints={name: matrix.AGENT_FINGERPRINTS[name] for name in field.agents},
        orientations=field_orientations(field_id),
    )
    sha = integrity.get("git_sha")
    tree = None if sha is None else git_text("rev-parse", f"{sha}:{freeze['identity']['match_generation_path']}")
    return {"integrity": integrity, "generation_tree": tree,
            "generation_source_ok": tree == freeze["identity"]["match_generation_tree"],
            "status": "PASS" if integrity["status"] == "PASS" and tree == freeze["identity"]["match_generation_tree"]
            else "FAIL"}


RELABEL_FIELDS: tuple[str, ...] = ("F2", "F4")


def reproduce(*, run_root: Path | None = None, freeze_path: Path = FREEZE_RECORD_PATH) -> dict[str, Any]:
    """The parent reproduction gate, E3 continuity and the relabel gate, recorded under the freeze."""
    root = run_root or DEFAULT_RUN_ROOT
    assert_no_treatment_artifacts(root)
    verify_frozen_definition()
    freeze = load_freeze(freeze_path)
    freeze_id = freeze["freeze_id"]
    reproduction: dict[str, dict[str, Any]] = {}
    for condition_id, historical in matrix.HISTORICAL_PARENT.items():
        reproduction[condition_id] = {}
        for field in matrix.FIELDS:
            new_rows = _rows(root, freeze_id, condition_id, field.field_id)
            comparison = compare_parent_subset(
                condition_root(root, condition_id, field.field_id),
                historical_root(condition_id, field.historical_field),
                new_rows=new_rows,
                historical_rows=_rows(root, freeze_id, f"historical-{historical}", field.field_id),
            )
            comparison["continuity"] = e3_continuity(
                new_rows, e3_telemetry.read_rows(frozen_e3_telemetry_file(historical, field.historical_field))[1])
            comparison["integrity"] = control_integrity(condition_id, field.field_id, run_root=root, freeze=freeze)
            comparison["clean_telemetry"] = summarize(new_rows)["clean"]
            if field.field_id in RELABEL_FIELDS:
                comparison["relabel"] = relabel_gate(condition_root(root, condition_id, field.field_id))
            checks = [comparison["continuity"]["status"], comparison["integrity"]["status"],
                      "PASS" if comparison["clean_telemetry"] else "FAIL", comparison.get("relabel", {}).get("status", "PASS")]
            if any(status != "PASS" for status in checks):
                comparison["status"] = "FAIL"
            reproduction[condition_id][field.field_id] = comparison
    return write_parent_record(
        freeze_root(root, freeze_id) / PARENT_RECORD_NAME, matrix_id=matrix.matrix_id(), freeze_id=freeze_id,
        reproduction=reproduction, fresh={}, expected_matches=_expected_matches(), sample=False,
        provenance={**get_git_provenance(), "e4_runner_version": E4_RUNNER_VERSION},
    )


def _expected_matches() -> dict[str, dict[str, int]]:
    return {c: {f.field_id: f.expected_matches for f in matrix.FIELDS} for c in matrix.CONTROL_CONDITIONS}


def _qualification_corpora() -> tuple[str, ...]:
    return (*matrix.CONTROL_CONDITIONS, *HISTORICAL_CORPORA)


def qualify(*, run_root: Path | None = None, workers: int = 1, freeze_path: Path = FREEZE_RECORD_PATH) -> dict[str, Any]:
    """Analyzer qualification on control data only: every stored row clean, and an
    independent second pass reproducing every row."""
    root = run_root or DEFAULT_RUN_ROOT
    assert_no_treatment_artifacts(root)
    freeze = load_freeze(freeze_path)
    freeze_id = freeze["freeze_id"]
    corpora: dict[str, dict[str, Any]] = {}
    for corpus in _qualification_corpora():
        sources = corpus_roots(corpus, root)
        for field in matrix.FIELDS:
            stored = _rows(root, freeze_id, corpus, field.field_id)
            second = compute_telemetry(sources[field.field_id], workers=workers,
                                       keys=corpus_keys(corpus, field.field_id, root))
            first_digests, second_digests = row_digests(stored), row_digests(second)
            differing = sorted(k for k in set(first_digests) | set(second_digests)
                               if first_digests.get(k) != second_digests.get(k))
            corpora[f"{corpus}/{field.field_id}"] = {
                **summarize(stored),
                "telemetry_sha256": record_sha256(telemetry_file(root, freeze_id, corpus, field.field_id)),
                "expected_cells": field.expected_matches,
                "repeatability": {"cells": len(second), "differing": len(differing), "samples": differing[:10]},
            }
    names = ("analyzed", "analyzer_failures", "cpu_statistics_mismatches", "ownership_reconstruction_disagreements",
             "capture_engine_disagreements", "capture_attribution_mismatches", "e4_reconstruction_disagreements",
             "e4_fps_identity_failures", "e4_check_failures", "decided_early_cells", "static_defined_cells")
    totals = {name: sum(report[name] for report in corpora.values()) for name in names}
    totals["repeatability_differences"] = sum(r["repeatability"]["differing"] for r in corpora.values())
    complete = all(r["analyzed"] + r["analyzer_failures"] == r["expected_cells"] == r["cells"] for r in corpora.values())
    passed = complete and all(r["clean"] for r in corpora.values()) and totals["repeatability_differences"] == 0
    record = {
        "qualification_version": QUALIFICATION_VERSION, "matrix_id": matrix.matrix_id(), "freeze_id": freeze_id,
        "note": "Control data only: no T-E4 or T-E4K1 match exists.", "corpora": corpora, "totals": totals,
        "complete": complete, "status": "PASS" if passed else "FAIL",
        "provenance": {**get_git_provenance(), "workers": workers},
    }
    path = freeze_root(root, freeze_id) / QUALIFICATION_RECORD_NAME
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, indent=2, sort_keys=True), encoding="utf-8")
    return record


def require_qualification(path: Path, *, freeze_id: str) -> dict[str, Any]:
    if not path.is_file():
        raise E4ConfigurationError(f"No analyzer qualification record at {path}.")
    record: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    expected = {f"{c}/{f}" for c in _qualification_corpora() for f in matrix.FIELD_IDS}
    if (record.get("freeze_id") != freeze_id or record.get("status") != "PASS" or record.get("complete") is not True
            or set(record.get("corpora") or {}) != expected):
        raise E4ConfigurationError("Analyzer qualification does not permit treatment.")
    return record


# ---------------------------------------------------------------------------
# Populations, the gates and the treatment unlock
# ---------------------------------------------------------------------------


def condition_runs(condition_id: str, *, run_root: Path, freeze_id: str) -> dict[str, FieldRun]:
    return {
        f.field_id: make_field_run(condition_id, f.field_id, load_cells(condition_root(run_root, condition_id, f.field_id)),
                                   _rows(run_root, freeze_id, condition_id, f.field_id))
        for f in matrix.FIELDS
    }


def compute_populations(*, run_root: Path, freeze_id: str) -> dict[str, Any]:
    return populations.build_record(
        freeze_id=freeze_id, preregistration_sha256=preregistration_digest(), prereg=load_preregistration(),
        arms={arm: condition_runs(control, run_root=run_root, freeze_id=freeze_id)
              for arm, control in matrix.ARM_CONTROLS.items()},
    )


def freeze_populations(*, run_root: Path | None = None, freeze_path: Path = FREEZE_RECORD_PATH,
                       out_path: Path = populations.POPULATIONS_PATH) -> dict[str, Any]:
    root = run_root or DEFAULT_RUN_ROOT
    assert_no_treatment_artifacts(root)
    freeze = load_freeze(freeze_path)
    record = compute_populations(run_root=root, freeze_id=freeze["freeze_id"])
    populations.require_control_census(record)
    sha = populations.write_record(out_path, record)
    populations.write_record(freeze_root(root, freeze["freeze_id"]) / out_path.name, record)
    return {"path": str(out_path), "sha256": sha,
            "counts": {arm: body["counts"] for arm, body in record["arms"].items()},
            "control_census": {arm: body["control_census"]["status"] for arm, body in record["arms"].items()},
            "p_stale": record["p_stale"]["count"]}


def run_manipulation(*, run_root: Path | None = None, freeze_path: Path = FREEZE_RECORD_PATH) -> dict[str, Any]:
    root = run_root or DEFAULT_RUN_ROOT
    assert_no_treatment_artifacts(root)
    freeze = load_freeze(freeze_path)
    return manipulation_gate.write_record(
        freeze_root(root, freeze["freeze_id"]) / manipulation_gate.MANIPULATION_RECORD_NAME, manipulation_gate.run_gate(),
        freeze_id=freeze["freeze_id"], provenance=get_git_provenance())


def run_d9(*, run_root: Path | None = None, freeze_path: Path = FREEZE_RECORD_PATH) -> dict[str, Any]:
    root = run_root or DEFAULT_RUN_ROOT
    assert_no_treatment_artifacts(root)
    freeze = load_freeze(freeze_path)
    return d9_gate.write_record(freeze_root(root, freeze["freeze_id"]) / d9_gate.D9_PRIME_RECORD_NAME, d9_gate.run_gate(),
                                freeze_id=freeze["freeze_id"], provenance=get_git_provenance())


CONTROL_RECORDS: tuple[str, ...] = (PARENT_RECORD_NAME, QUALIFICATION_RECORD_NAME,
                                    manipulation_gate.MANIPULATION_RECORD_NAME, d9_gate.D9_PRIME_RECORD_NAME)


def treatment_unlock(run_root: Path, *, freeze_path: Path = FREEZE_RECORD_PATH,
                     populations_path: Path = populations.POPULATIONS_PATH) -> dict[str, Any]:
    """Fail closed unless a treatment may run: the committed freeze holds, its control
    qualification names passing, complete records whose bytes are unchanged, and the
    frozen populations still recompute from the control corpus with a 100% identity census."""
    freeze = load_freeze(freeze_path)
    freeze_id = freeze["freeze_id"]
    qualification = freeze.get("control_qualification") or {}
    if qualification.get("status") != "PASS":
        raise AnalysisFreezeError(f"The freeze's control qualification is {qualification.get('status')!r}, not PASS.")
    records = freeze_root(run_root, freeze_id)
    for name in CONTROL_RECORDS:
        pinned = (qualification.get("records") or {}).get(name) or {}
        path = records / name
        if not path.is_file() or record_sha256(path) != pinned.get("sha256"):
            raise AnalysisFreezeError(f"Control record {name} is missing or differs from the committed freeze.")
    parent = require_parent_reproduction(records / PARENT_RECORD_NAME, matrix_id=matrix.matrix_id(),
                                         freeze_id=freeze_id, expected_matches=_expected_matches())
    require_relabel({f"{c}/{f}": parent["reproduction"][c][f]["relabel"]
                     for c in matrix.CONTROL_CONDITIONS for f in RELABEL_FIELDS})
    analyzer = require_qualification(records / QUALIFICATION_RECORD_NAME, freeze_id=freeze_id)
    manipulation = manipulation_gate.require_gate(records / manipulation_gate.MANIPULATION_RECORD_NAME, freeze_id=freeze_id)
    d9 = d9_gate.require_gate(records / d9_gate.D9_PRIME_RECORD_NAME, freeze_id=freeze_id)
    for corpus in matrix.CONTROL_CONDITIONS:
        for field_id in matrix.FIELD_IDS:
            pinned_sha = analyzer["corpora"][f"{corpus}/{field_id}"]["telemetry_sha256"]
            if record_sha256(telemetry_file(run_root, freeze_id, corpus, field_id)) != pinned_sha:
                raise AnalysisFreezeError(f"Telemetry {corpus}/{field_id} differs from the qualified file.")
    frozen = populations.load_record(populations_path, freeze_id=freeze_id,
                                     expected_sha256=(qualification.get("populations") or {}).get("sha256"))
    populations.require_control_census(frozen)
    populations.require_recomputes(frozen, compute_populations(run_root=run_root, freeze_id=freeze_id))
    return {"freeze": freeze, "parent": parent, "analyzer": analyzer, "manipulation": manipulation, "d9": d9,
            "populations": frozen}


# ---------------------------------------------------------------------------
# Treatment side (after separately authorized execution only)
# ---------------------------------------------------------------------------

ANALYSIS_RECORD_NAME = "e4_analysis.json"


def treatment_gate_record_name(condition_id: str) -> str:
    return f"treatment_gates_{condition_id}.json"


def write_treatment_telemetry(condition_id: str, *, run_root: Path | None = None, workers: int = 1,
                              freeze_path: Path = FREEZE_RECORD_PATH) -> dict[str, Any]:
    if matrix.condition(condition_id).role != matrix.TREATMENT:
        raise E4ConfigurationError(f"{condition_id} is not a treatment.")
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


def treatment_gate_report(condition_id: str, *, treatment_roots: dict[str, Path],
                          rows: dict[str, dict[str, dict[str, Any]]],
                          integrity: dict[str, dict[str, Any]] | None = None) -> dict[str, Any]:
    """Hard stops 5-9 for one treatment: integrity, the G.4' manipulation checks,
    the relabel gate and, for T-E4, the D9' stop."""
    fields: dict[str, Any] = {}
    completions: list[dict[str, Any]] = []
    victims = {"e2_repair_guard", "e2_repair_guard_twin", "e2_disrupt_guard", "e2_disrupt_guard_twin"}
    for field_id in matrix.FIELD_IDS:
        found = [{"field": field_id, "cell": key, **c} for key, row in sorted(rows[field_id].items())
                 if "telemetry" in row for c in row["telemetry"]["e3"]["completions"] if c["victim_name"] in victims]
        completions += found
        report: dict[str, Any] = {"manipulation": manipulation_checks(rows[field_id], mirrored=True),
                                  "d9_completions": len(found)}
        if field_id in RELABEL_FIELDS:
            report["relabel"] = relabel_gate(treatment_roots[field_id])
        if integrity is not None:
            report["integrity"] = integrity[field_id]
        checks = [report["manipulation"]["status"], report.get("relabel", {}).get("status", "PASS"),
                  (integrity or {}).get(field_id, {}).get("status", "PASS")]
        report["status"] = "PASS" if all(status == "PASS" for status in checks) else "FAIL"
        fields[field_id] = report
    d9_stop = condition_id == matrix.PRIMARY_TREATMENT and bool(completions)
    return {"condition": condition_id, "parent": matrix.condition(condition_id).parent, "fields": fields,
            "d9_completions": completions[:20], "d9_completion_count": len(completions), "d9_stop": d9_stop,
            "status": "PASS" if all(r["status"] == "PASS" for r in fields.values()) and not d9_stop else "FAIL"}


def treatment_gates(condition_id: str, *, run_root: Path | None = None,
                    freeze_path: Path = FREEZE_RECORD_PATH) -> dict[str, Any]:
    root = run_root or DEFAULT_RUN_ROOT
    unlock = treatment_unlock(root, freeze_path=freeze_path)
    freeze_id = unlock["freeze"]["freeze_id"]
    condition = matrix.condition(condition_id)
    if condition.parent is None:
        raise E4ConfigurationError(f"{condition_id} is not a treatment.")
    integrity = {f.field_id: corpus_integrity(
        condition_root(root, condition_id, f.field_id), ruleset_id=condition.ruleset_id, pairs=f.pairs,
        seeds=matrix.SEEDS, provenance=_integrity_provenance(condition_id, f.field_id, freeze_id),
        fingerprints={name: matrix.AGENT_FINGERPRINTS[name] for name in f.agents},
        orientations=field_orientations(f.field_id)) for f in matrix.FIELDS}
    record = treatment_gate_report(
        condition_id, treatment_roots={f: condition_root(root, condition_id, f) for f in matrix.FIELD_IDS},
        rows={f: _rows(root, freeze_id, condition_id, f) for f in matrix.FIELD_IDS}, integrity=integrity)
    record.update({"freeze_id": freeze_id, "provenance": get_git_provenance()})
    path = freeze_root(root, freeze_id) / treatment_gate_record_name(condition_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, indent=2, sort_keys=True), encoding="utf-8")
    require_d9_prime(condition_id, record["d9_completions"])
    if record["status"] != "PASS":
        raise TreatmentGateError(f"STOP: {condition_id} failed its treatment gates; see {path}.")
    return record


def analyze(*, run_root: Path | None = None, freeze_path: Path = FREEZE_RECORD_PATH) -> dict[str, Any]:
    """The frozen analysis, once both treatments passed their gates."""
    root = run_root or DEFAULT_RUN_ROOT
    unlock = treatment_unlock(root, freeze_path=freeze_path)
    freeze_id = unlock["freeze"]["freeze_id"]
    for condition_id in matrix.TREATMENT_CONDITIONS:
        path = freeze_root(root, freeze_id) / treatment_gate_record_name(condition_id)
        gate = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
        if gate.get("status") != "PASS" or gate.get("freeze_id") != freeze_id:
            raise TreatmentGateError(f"{condition_id} has no passing treatment gate record under {freeze_id}.")
    runs = {c.condition_id: condition_runs(c.condition_id, run_root=root, freeze_id=freeze_id) for c in matrix.CONDITIONS}
    arms = {arm: {"control": runs[matrix.ARM_CONTROLS[arm]], "treatment": runs[matrix.ARM_TREATMENTS[arm]]}
            for arm in matrix.ARM_CONTROLS}
    result = evaluate_hypotheses(arms, unlock["populations"]["arms"], load_preregistration(), contest_classes.load_table())
    record = {"e4_analysis_version": E4_ANALYSIS_VERSION, "matrix_id": matrix.matrix_id(), "freeze_id": freeze_id,
              "preregistration_sha256": preregistration_digest(), "result": result, "provenance": get_git_provenance()}
    path = freeze_root(root, freeze_id) / ANALYSIS_RECORD_NAME
    path.write_text(json.dumps(record, indent=2, sort_keys=True, default=str), encoding="utf-8")
    return record


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="run_e4", description=(__doc__ or "").splitlines()[0])
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("plan", help="dry run: count every planned cell (default)")
    run = sub.add_parser("execute", help="run one condition/field")
    run.add_argument("condition", choices=[c.condition_id for c in matrix.CONDITIONS])
    run.add_argument("field", choices=list(matrix.FIELD_IDS))
    run.add_argument("--confirm-matrix-execution", action="store_true")
    run.add_argument("--confirm-treatment-execution", action="store_true")
    run.add_argument("--workers", type=int, default=1)
    run.add_argument("--run-root", type=Path)
    tele = sub.add_parser("telemetry", help="E4 telemetry for a control or historical parent corpus")
    tele.add_argument("corpus", choices=[*matrix.CONTROL_CONDITIONS, *HISTORICAL_CORPORA])
    tele.add_argument("--workers", type=int, default=1)
    tele.add_argument("--run-root", type=Path)
    for name, text in (("reproduce", "parent reproduction, E3 continuity and the relabel gate"),
                       ("populations", "freeze the control populations, baseline and census"),
                       ("manipulation", "the G.4' manipulation gate"),
                       ("d9", "the D9' real-fixture gate"),
                       ("unlock", "report whether a treatment may run (executes nothing)")):
        item = sub.add_parser(name, help=text)
        item.add_argument("--run-root", type=Path)
    qual = sub.add_parser("qualify", help="analyzer qualification on control data")
    qual.add_argument("--workers", type=int, default=1)
    qual.add_argument("--run-root", type=Path)
    for name in ("treatment-telemetry", "treatment-gates"):
        item = sub.add_parser(name, help=f"{name} (unlock required; after authorized treatment execution only)")
        item.add_argument("condition", choices=list(matrix.TREATMENT_CONDITIONS))
        item.add_argument("--workers", type=int, default=1)
        item.add_argument("--run-root", type=Path)
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
        emit({k: v for k, v in record.items() if k != "reproduction"} | {
            "fields": {f"{c}/{f}": r["status"] for c, fields in record["reproduction"].items() for f, r in fields.items()}})
        return 0 if record["status"] == "PASS" and record["complete"] else 1
    if args.command == "qualify":
        record = qualify(run_root=args.run_root, workers=args.workers)
        emit({k: v for k, v in record.items() if k != "corpora"})
        return 0 if record["status"] == "PASS" else 1
    if args.command == "populations":
        emit(freeze_populations(run_root=args.run_root))
        return 0
    if args.command == "manipulation":
        record = run_manipulation(run_root=args.run_root)
        emit({"status": record["status"], "arms": [{k: v for k, v in arm.items() if k in ("treatment", "checks", "status")}
                                                   for arm in record["arms"]]})
        return 0 if record["status"] == "PASS" else 1
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
        emit({"freeze_id": record["freeze_id"], "inputs": record["result"]["interpretation_inputs"],
              "interpretation": record["result"]["interpretation"]})
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
