"""The V6 E6 runner: the registered order of events as an unlock chain.

Defines the E6 matrix (``matrix.py``) and never executes it implicitly.
Every command after ``plan`` needs the committed analysis freeze
(``analysis_freeze_v2.json``), and each later step needs the records of the
steps before it (PR Sec 9, step 7, and Sec 11):

1. ``plan``: a structural dry run. It counts every cell of every
   condition and field with the real evaluation planner, using placeholder
   seed values (the positions 1..32), since no seed exists yet. Executes
   nothing.
2. ``generate-seeds --confirm-seed-generation`` (I-7, separately
   authorized): only with the freeze committed, its seed block PENDING and
   no matrix cell anywhere. Writes the private list and puts the commitment
   and the execution matrix identity (and nothing else) into the freeze
   record, for the operator to commit before the first cell.
3. ``execute CONDITION FIELD --confirm-matrix-execution`` (Q and T,
   separately authorized): the committed seed commitment, a private list
   that matches it, the recomputed execution identity, a clean tree with the
   frozen engine and tooling, D-5, and for a treatment
   ``--confirm-treatment-execution`` plus a PASS control qualification in the
   freeze record (Checkpoint B). Runs the field through the harness, then
   the bound trace pass (``traces.py``) and the compact telemetry.
4. ``qualify``: controls only. D-3 (control provenance and the parent
   byte-identity freeze re-run), CQ-1, D-2 and D-7 on the controls,
   control-against-control (PR Sec 10.3) for both arms, and the Sec 6.3
   trace-size rule. The record's digest goes into the freeze record.
5. ``treatment-gates CONDITION``: D-1, D-2, D-4 and D-7.
6. ``analyze``: the frozen gameplay analysis of both arms. It may run while
   the seeds are hidden, and it issues no interpretation.
7. ``reveal SEEDS_FILE``: D-6 against the commitment, the execution
   identity and every cell's recorded seed.
8. ``interpret``: only after a PASS or FAIL D-6. E6-D's final status, then
   the registered row, qualifier and disposition of the primary arm, and the
   companion reading. A failed D-6 makes the disposition VOID.

Every control-phase command first checks that no treatment artifact exists.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from collections.abc import Sequence
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from battle_engine.evaluation_planning import build_matrix
from battle_engine.evaluation_service import EvaluationRequest, EvaluationService

from tools.research.v6.e3.gates import load_cells
from tools.research.v6.e6 import (
    analyze_e6,
    describe,
    discipline,
    family,
    gates,
    interpretation,
    matrix,
    seeds,
    telemetry,
    traces,
)
from tools.research.v6.e6.analysis_freeze import (
    FREEZE_RECORD_PATH,
    PENDING,
    AnalysisFreezeError,
    git_text,
    load_freeze,
    verify_execution_source,
)
from tools.research.v6.e6.preregistration import load_preregistration, preregistration_digest
from tools.research.v6.experiment_harness import (
    REPO_ROOT,
    ResearchExperimentConfig,
    experiment_pairs,
    plan_evaluation_requests,
    run_experiment,
)

E6_RUNNER_VERSION = 1
DEFAULT_RUN_ROOT = REPO_ROOT / "runs" / "research_v6_e6"
PLACEHOLDER_SEEDS: tuple[int, ...] = tuple(range(1, matrix.SEED_COUNT + 1))
QUALIFICATION_RECORD = "qualification.json"
ANALYSIS_RECORD = "e6_analysis.json"
D6_RECORD = "d6.json"
INTERPRETATION_RECORD = "e6_interpretation.json"
SIZE_RECORD = "trace_size.json"
PARENT_FREEZE_TEST = "engine/tests/test_v6_e6_parent_byte_identity.py"


class E6ConfigurationError(RuntimeError):
    """An E6 step would not match the frozen experiment, or runs out of the registered order."""


class TreatmentExposureError(RuntimeError):
    """A treatment artifact exists where only controls may."""


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------


def matrix_root(run_root: Path) -> Path:
    return run_root / matrix.matrix_id()


def condition_root(run_root: Path, condition_id: str, field_id: str) -> Path:
    return matrix_root(run_root) / condition_id / field_id


def records_root(run_root: Path) -> Path:
    return matrix_root(run_root) / "records"


def treatment_artifacts(run_root: Path) -> list[str]:
    base = matrix_root(run_root)
    found = [str(base / c) for c in matrix.TREATMENT_CONDITIONS if (base / c).exists()]
    found += [str(p) for p in records_root(run_root).glob("treatment_gates_*")]
    return sorted(found)


def assert_no_treatment_artifacts(run_root: Path) -> None:
    found = treatment_artifacts(run_root)
    if found:
        raise TreatmentExposureError(f"STOP: treatment artifacts exist: {found}")


def any_matrix_cell(run_root: Path) -> bool:
    base = matrix_root(run_root)
    return any((base / c.condition_id).exists() for c in matrix.CONDITIONS)


def _write_json(path: Path, payload: Any) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")
    path.write_bytes(data)
    return hashlib.sha256(data).hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise E6ConfigurationError(f"STOP: required record {path} does not exist")
    value: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return value


# ---------------------------------------------------------------------------
# Plan and requests
# ---------------------------------------------------------------------------


def experiment_config(condition_id: str, field_id: str, *, run_root: Path, seed_list: Sequence[int],
                      provenance: dict[str, Any], workers: int = 1, output_dir: Path | None = None
                      ) -> ResearchExperimentConfig:
    condition = matrix.condition(condition_id)
    field = matrix.field(field_id)
    return ResearchExperimentConfig(
        experiment_id=f"{matrix.matrix_id()}-{condition_id}-{field_id}",
        ruleset_id=condition.ruleset_id,
        arena_sizes=(matrix.ARENA_SIZE,),
        field=field.agents,
        seeds=tuple(seed_list),
        ticks=field.max_ticks,
        both_orientations=field.both_orientations,
        output_dir=output_dir or condition_root(run_root, condition_id, field_id),
        workers=workers,
        pairs=None if field.pairing == "triangular" else field.pairs,
        provenance_extra={**provenance, "e6_condition": condition_id, "e6_field": field_id,
                          "e6_runner_version": E6_RUNNER_VERSION},
    )


def check_requests(requests: Sequence[EvaluationRequest], condition_id: str, field_id: str, *,
                   seed_list: Sequence[int]) -> None:
    condition, field = matrix.condition(condition_id), matrix.field(field_id)
    problems: list[str] = []
    for request in requests:
        for name in matrix.FORBIDDEN_REQUEST_OVERRIDES:
            if getattr(request, name) is not None:
                problems.append(f"{request.candidate_id}: forbidden override {name}")
        expected = {"ruleset_id": condition.ruleset_id, "arena_size": matrix.ARENA_SIZE, "ticks": field.max_ticks,
                    "seeds": tuple(seed_list), "both_orientations": field.both_orientations}
        for name, value in expected.items():
            if getattr(request, name) != value:
                problems.append(f"{request.candidate_id}: {name}={getattr(request, name)!r} != {value!r}")
    if problems:
        raise E6ConfigurationError("E6 request check failed: " + "; ".join(problems))


def dry_run_plan(condition_id: str, field_id: str, seed_list: Sequence[int] = PLACEHOLDER_SEEDS) -> dict[str, Any]:
    field = matrix.field(field_id)
    with tempfile.TemporaryDirectory(prefix="e6-plan-") as tmp:
        config = experiment_config(condition_id, field_id, run_root=Path(tmp), seed_list=seed_list, provenance={},
                                   output_dir=Path(tmp) / "out")
        if experiment_pairs(config) != field.pairs:
            raise E6ConfigurationError(f"{field_id}: planned pairs differ from the frozen field")
        family.prepare_data_root(Path(tmp) / "env", field.agents)
        requests = plan_evaluation_requests(config, matrix.ARENA_SIZE, Path(tmp) / "plan", Path(tmp) / "env")
        check_requests(requests, condition_id, field_id, seed_list=seed_list)
        service = EvaluationService()
        cells = 0
        rulesets: set[str] = set()
        for request in requests:
            specs, evaluation_id = service.preflight(
                candidate_id=request.candidate_id, opponent_ids=request.opponent_ids, seeds=request.seeds,
                ticks=request.ticks, data_root=request.data_root, both_orientations=request.both_orientations,
                ruleset_id=request.ruleset_id, arena_size=request.arena_size)
            planned = build_matrix(request, evaluation_id, specs, None, request.resolved_rules_compatibility_id,
                                   request.resolved_arena_alignment_mode)
            cells += len(planned)
            rulesets.update(cell.rules_compatibility_id for cell in planned)
    return {"condition": condition_id, "field": field_id, "planned_cells": cells,
            "expected_cells": field.expected_matches, "rulesets": sorted(rulesets),
            "consistent": cells == field.expected_matches and rulesets == {matrix.condition(condition_id).ruleset_id}}


def plan_report() -> dict[str, Any]:
    matrix.verify_frozen_matrix()
    load_preregistration()
    rows = [dry_run_plan(c.condition_id, f.field_id) for c in matrix.CONDITIONS for f in matrix.FIELDS]
    total = sum(row["planned_cells"] for row in rows)
    return {"structural_matrix_id": matrix.matrix_id(), "structural_digest": matrix.STRUCTURAL_DIGEST,
            "preregistration_sha256": preregistration_digest(), "placeholder_seeds": True, "rows": rows,
            "planned_total": total, "expected_total": matrix.matches_total(),
            "all_consistent": all(row["consistent"] for row in rows) and total == matrix.matches_total() == 11_520}


# ---------------------------------------------------------------------------
# I-7: seeds (separately authorized)
# ---------------------------------------------------------------------------


def generate_seeds(*, confirm: bool, run_root: Path = DEFAULT_RUN_ROOT, freeze_path: Path = FREEZE_RECORD_PATH,
                   seeds_path: Path = seeds.PRIVATE_SEEDS_PATH) -> dict[str, Any]:
    if not confirm:
        raise E6ConfigurationError("Refusing to generate seeds: pass --confirm-seed-generation (I-7 authorization).")
    record = load_freeze(freeze_path)
    if record.get("seed_commitment") != PENDING:
        raise E6ConfigurationError("STOP: the freeze record already carries a seed commitment.")
    if any_matrix_cell(run_root):
        raise E6ConfigurationError("STOP: a matrix cell exists before the seed commitment.")
    if git_text("status", "--porcelain"):
        raise E6ConfigurationError("STOP: seeds are generated only from a clean tree.")
    seed_list = seeds.generate()
    commitment = seeds.write_private(seed_list, seeds_path)
    block = dict(seeds.committed_record(
        commitment, matrix.STRUCTURAL_DIGEST, datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        git_text("rev-parse", "HEAD")))
    record["seed_commitment"] = block
    freeze_path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return block


def committed_seeds(record: dict[str, Any], seeds_path: Path = seeds.PRIVATE_SEEDS_PATH) -> tuple[list[int], dict[str, Any]]:
    block = record.get("seed_commitment") or {}
    if block == PENDING or "seed_commitment" not in block:
        raise E6ConfigurationError("STOP: no seed commitment in the freeze record; no matrix cell may run.")
    if matrix.execution_identity(block["seed_commitment"]) != block["execution_matrix_identity"]:
        raise E6ConfigurationError("STOP: the execution matrix identity does not recompute.")
    try:
        return seeds.load_private(block["seed_commitment"], seeds_path), block
    except (OSError, seeds.SeedProtocolError) as exc:
        raise E6ConfigurationError(f"STOP: the private seed list is missing or does not match: {exc}") from None


# ---------------------------------------------------------------------------
# Q / T: execution (separately authorized)
# ---------------------------------------------------------------------------


def require_control_qualification(record: dict[str, Any], run_root: Path) -> dict[str, Any]:
    block = record.get("control_qualification") or {}
    if block.get("status") != "PASS":
        raise E6ConfigurationError("STOP: no PASS control qualification in the freeze record (Checkpoint B).")
    path = records_root(run_root) / QUALIFICATION_RECORD
    if hashlib.sha256(path.read_bytes()).hexdigest() != block.get("record_sha256"):
        raise E6ConfigurationError("STOP: the qualification record differs from the one the freeze record names.")
    return block


def execute(condition_id: str, field_id: str, *, confirm: bool = False, confirm_treatment: bool = False,
            workers: int = 1, run_root: Path = DEFAULT_RUN_ROOT, freeze_path: Path = FREEZE_RECORD_PATH,
            seeds_path: Path = seeds.PRIVATE_SEEDS_PATH) -> dict[str, Any]:
    if not confirm:
        raise E6ConfigurationError("Refusing to execute: pass --confirm-matrix-execution.")
    condition = matrix.condition(condition_id)
    if condition.role == matrix.TREATMENT and not confirm_treatment:
        raise E6ConfigurationError(f"Refusing to execute treatment {condition_id}: it needs separate authorization "
                                   "(--confirm-treatment-execution) and the full unlock chain.")
    record = load_freeze(freeze_path)
    seed_list, block = committed_seeds(record, seeds_path)
    if condition.role == matrix.TREATMENT:
        require_control_qualification(record, run_root)
    else:
        assert_no_treatment_artifacts(run_root)
    matrix.verify_frozen_matrix()
    load_preregistration()
    if not discipline.passes(family.FIXTURE_DIR / pid for pid in family.PACKAGES):
        raise E6ConfigurationError("STOP: D-5 discipline fails.")
    verify_execution_source(record)
    field = matrix.field(field_id)
    provenance = {"e6_structural_matrix_id": matrix.matrix_id(), "e6_structural_digest": matrix.STRUCTURAL_DIGEST,
                  "e6_execution_matrix_id": block["execution_matrix_identity"],
                  "e6_seed_commitment": block["seed_commitment"], "e6_freeze_id": record["freeze_id"],
                  "e6_preregistration_sha256": preregistration_digest()}
    config = experiment_config(condition_id, field_id, run_root=run_root, seed_list=seed_list,
                               provenance=provenance, workers=workers)
    assert config.output_dir is not None
    if config.output_dir.exists():
        raise E6ConfigurationError(f"{config.output_dir} already exists; an E6 cell set is never re-run in place.")
    family.prepare_data_root(config.output_dir / "env", field.agents)
    result = run_experiment(config, request_guard=lambda requests: check_requests(
        requests, condition_id, field_id, seed_list=seed_list))
    cells = sum(len(block_["cells"]) for block_ in result["conditions"])
    if cells != field.expected_matches:
        raise E6ConfigurationError(f"{condition_id}/{field_id}: {cells} cells ran, {field.expected_matches} expected")
    records = traces.trace_field(config.output_dir, data_root=config.output_dir / "env", ticks=field.max_ticks,
                                 arena_size=matrix.ARENA_SIZE, expected_cells=field.expected_matches)
    telemetry.telemetry_field(config.output_dir, records, arena=matrix.ARENA_SIZE)
    verify_execution_source(load_freeze(freeze_path))
    size = traces.size_report(records, matrix_cells=matrix.matches_total())
    size_path = records_root(run_root) / SIZE_RECORD
    if not size_path.exists():
        _write_json(size_path, {"measured_on": [condition_id, field_id], **size})
    return {"condition": condition_id, "field": field_id, "cells": cells, "traced": len(records),
            "output_dir": str(config.output_dir)}


# ---------------------------------------------------------------------------
# Loading a run
# ---------------------------------------------------------------------------


def field_cells(run_root: Path, condition_id: str, field_id: str) -> list[dict[str, Any]]:
    return load_cells(condition_root(run_root, condition_id, field_id))


def condition_data(run_root: Path, condition_id: str) -> analyze_e6.ConditionData:
    f1_root = condition_root(run_root, condition_id, "F1")
    f1 = field_cells(run_root, condition_id, "F1")
    contact = {analyze_e6.cell_key(cell): analyze_e6.hostile_core_contact(f1_root / str(cell["artifact_dir"])
                                                                         / "replay.jsonl") for cell in f1}
    return analyze_e6.ConditionData(condition_id, tuple(f1), tuple(field_cells(run_root, condition_id, "F2")), contact)


def provenance(run_root: Path, condition_id: str, field_id: str) -> dict[str, Any]:
    return _read_json(condition_root(run_root, condition_id, field_id) / "provenance.json")


# ---------------------------------------------------------------------------
# Q: control qualification
# ---------------------------------------------------------------------------


def _parent_freeze_passes() -> bool:
    proc = subprocess.run([sys.executable, "-m", "pytest", "-q", "--no-header", "-p", "no:cacheprovider",
                           PARENT_FREEZE_TEST], cwd=REPO_ROOT, capture_output=True, text=True, check=False)
    return proc.returncode == 0


def qualify(*, run_root: Path = DEFAULT_RUN_ROOT, freeze_path: Path = FREEZE_RECORD_PATH,
            seeds_path: Path = seeds.PRIVATE_SEEDS_PATH) -> dict[str, Any]:
    assert_no_treatment_artifacts(run_root)
    record = load_freeze(freeze_path)
    seed_list, block = committed_seeds(record, seeds_path)
    report: dict[str, Any] = {"freeze_id": record["freeze_id"], "execution_matrix_id": block["execution_matrix_identity"]}
    d3: list[str] = []
    for condition_id in matrix.CONTROL_CONDITIONS:
        for field in matrix.FIELDS:
            prov = provenance(run_root, condition_id, field.field_id)
            if prov.get("ruleset_id") != matrix.condition(condition_id).ruleset_id:
                d3.append(f"{condition_id}/{field.field_id}: Ruleset {prov.get('ruleset_id')}")
            if prov.get("e6_execution_matrix_id") != block["execution_matrix_identity"] or \
                    prov.get("e6_seed_commitment") != block["seed_commitment"] or \
                    prov.get("e6_structural_matrix_id") != matrix.matrix_id():
                d3.append(f"{condition_id}/{field.field_id}: provenance lacks the matrix identities or commitment")
            if prov.get("git_dirty") is not False:
                d3.append(f"{condition_id}/{field.field_id}: executed from a dirty tree")
    report["D-3"] = {"parent_freeze_passes": _parent_freeze_passes(), "provenance_problems": d3}
    report["D-3"]["status"] = "PASS" if report["D-3"]["parent_freeze_passes"] and not d3 else "FAIL"
    for condition_id in matrix.CONTROL_CONDITIONS:
        f1_root = condition_root(run_root, condition_id, "F1")
        f2_root = condition_root(run_root, condition_id, "F2")
        summaries_f1, summaries_f2 = telemetry.read_summaries(f1_root), telemetry.read_summaries(f2_root)
        report[condition_id] = {
            "CQ-1": gates.cq1_search_inertness(summaries_f1),
            "D-2": gates.d2_initial_invisibility([*summaries_f1, *summaries_f2], arena=matrix.ARENA_SIZE),
            "D-7": gates.d7_mirror_relabeling(f2_root, field_cells(run_root, condition_id, "F2"),
                                              expected_units=len(matrix.F2.pairs) * matrix.SEED_COUNT),
        }
    for arm, (control_id, _) in matrix.ARMS.items():
        control = condition_data(run_root, control_id)
        result = analyze_e6.analyze_arm(control, control, seeds=seed_list)
        report[f"control_against_control:{arm}"] = analyze_e6.control_against_control(result)
    report["trace_size"] = _read_json(records_root(run_root) / SIZE_RECORD)
    statuses = [report["D-3"]["status"]]
    for condition_id in matrix.CONTROL_CONDITIONS:
        statuses += [report[condition_id][name]["status"] for name in ("CQ-1", "D-2", "D-7")]
    statuses += [report[f"control_against_control:{arm}"]["status"] for arm in matrix.ARMS]
    report["status"] = "PASS" if all(status == "PASS" for status in statuses) else "FAIL"
    digest = _write_json(records_root(run_root) / QUALIFICATION_RECORD, report)
    return {"status": report["status"], "record_sha256": digest}


# ---------------------------------------------------------------------------
# T: treatment gates, analysis, reveal and interpretation
# ---------------------------------------------------------------------------


def treatment_gates(condition_id: str, *, run_root: Path = DEFAULT_RUN_ROOT,
                    freeze_path: Path = FREEZE_RECORD_PATH) -> dict[str, Any]:
    condition = matrix.condition(condition_id)
    if condition.role != matrix.TREATMENT:
        raise E6ConfigurationError(f"{condition_id} is not a treatment")
    record = load_freeze(freeze_path)
    require_control_qualification(record, run_root)
    report: dict[str, Any] = {"condition": condition_id, "freeze_id": record["freeze_id"]}
    all_summaries: list[dict[str, Any]] = []
    for field in matrix.FIELDS:
        root = condition_root(run_root, condition_id, field.field_id)
        cells = {cell["schedule_id"]: cell for cell in field_cells(run_root, condition_id, field.field_id)}
        report[f"D-1:{field.field_id}"] = gates.d1_visibility(
            root, traces.read_index(root), cells, arena=matrix.ARENA_SIZE,
            slot_limit=condition.disruption_slot_limit, detection_radius=matrix.DETECTION_RADIUS)
        all_summaries += telemetry.read_summaries(root)
    report["D-2"] = gates.d2_initial_invisibility(all_summaries, arena=matrix.ARENA_SIZE)
    report["D-4"] = gates.d4_no_early_blind_strike(all_summaries)
    report["D-7"] = gates.d7_mirror_relabeling(condition_root(run_root, condition_id, "F2"),
                                               field_cells(run_root, condition_id, "F2"),
                                               expected_units=len(matrix.F2.pairs) * matrix.SEED_COUNT)
    report["status"] = "PASS" if all(value["status"] == "PASS" for key, value in report.items()
                                     if key.startswith("D-")) else "FAIL"
    _write_json(records_root(run_root) / f"treatment_gates_{condition_id}.json", report)
    return report


def analyze(*, run_root: Path = DEFAULT_RUN_ROOT, freeze_path: Path = FREEZE_RECORD_PATH,
            seeds_path: Path = seeds.PRIVATE_SEEDS_PATH) -> dict[str, Any]:
    """The frozen gameplay analysis. May run while seeds are hidden; issues no interpretation."""
    record = load_freeze(freeze_path)
    require_control_qualification(record, run_root)
    seed_list, _ = committed_seeds(record, seeds_path)
    for condition_id in matrix.TREATMENT_CONDITIONS:
        _read_json(records_root(run_root) / f"treatment_gates_{condition_id}.json")
    arms = {}
    for arm, (control_id, treatment_id) in matrix.ARMS.items():
        control, treatment = condition_data(run_root, control_id), condition_data(run_root, treatment_id)
        arms[arm] = analyze_e6.analyze_arm(control, treatment, seeds=seed_list)
    descriptive = {
        condition_id: {
            "alternation": describe.alternation(condition_root(run_root, condition_id, "F1"),
                                                field_cells(run_root, condition_id, "F1")),
            "seat_and_parity": describe.seat_and_parity(
                telemetry.read_summaries(condition_root(run_root, condition_id, "F1"))),
        }
        for c in matrix.CONDITIONS for condition_id in (c.condition_id,)
    }
    payload = {"freeze_id": record["freeze_id"], "arms": arms,
               "companion": analyze_e6.companion_reading(arms[matrix.PRIMARY_ARM], arms[matrix.COMPANION_ARM]),
               "descriptive": descriptive, "interpretation": "withheld until D-6 (PR Sec 9, step 7)"}
    _write_json(records_root(run_root) / ANALYSIS_RECORD, payload)
    return payload


def all_cell_seeds(run_root: Path) -> list[int]:
    return [int(cell["seed"]) for c in matrix.CONDITIONS for f in matrix.FIELDS
            for cell in field_cells(run_root, c.condition_id, f.field_id)]


def reveal(revealed_path: Path, *, run_root: Path = DEFAULT_RUN_ROOT,
           freeze_path: Path = FREEZE_RECORD_PATH) -> dict[str, Any]:
    record = load_freeze(freeze_path)
    _read_json(records_root(run_root) / ANALYSIS_RECORD)
    block = record.get("seed_commitment") or {}
    if block == PENDING:
        raise E6ConfigurationError("STOP: nothing was committed, so nothing can be revealed.")
    report = seeds.d6(revealed_path.read_bytes(), committed=block["seed_commitment"],
                      structural_digest=matrix.STRUCTURAL_DIGEST,
                      committed_execution_identity=block["execution_matrix_identity"],
                      cell_seeds=all_cell_seeds(run_root))
    _write_json(records_root(run_root) / D6_RECORD, report)
    return report


def e6d_status(run_root: Path) -> dict[str, Any]:
    """E6-D's final status: D-1..D-7, with D-3 from qualification and D-5 re-checked statically."""
    records = records_root(run_root)
    qualification = _read_json(records / QUALIFICATION_RECORD)
    d6 = _read_json(records / D6_RECORD)
    treatment = [_read_json(records / f"treatment_gates_{c}.json") for c in matrix.TREATMENT_CONDITIONS]
    clauses = {
        "D-1": all(t[f"D-1:{f.field_id}"]["status"] == "PASS" for t in treatment for f in matrix.FIELDS),
        "D-2": all(t["D-2"]["status"] == "PASS" for t in treatment),
        "D-3": qualification["D-3"]["status"] == "PASS",
        "D-4": all(t["D-4"]["status"] == "PASS" for t in treatment),
        "D-5": discipline.passes(family.FIXTURE_DIR / pid for pid in family.PACKAGES),
        "D-6": d6["status"] == "PASS",
        "D-7": all(t["D-7"]["status"] == "PASS" for t in treatment),
    }
    return {"clauses": clauses, "status": interpretation.PASS if all(clauses.values()) else interpretation.FAIL}


def interpret(*, run_root: Path = DEFAULT_RUN_ROOT, freeze_path: Path = FREEZE_RECORD_PATH) -> dict[str, Any]:
    load_freeze(freeze_path)
    analysis = _read_json(records_root(run_root) / ANALYSIS_RECORD)
    _read_json(records_root(run_root) / D6_RECORD)  # the reveal comes first
    e6d = e6d_status(run_root)
    primary = analysis["arms"][matrix.PRIMARY_ARM]
    hypotheses = primary["hypotheses"]
    reading = interpretation.interpret(e6d=e6d["status"], h1t=hypotheses["E6-H1T"], h1c=hypotheses["E6-H1C"],
                                       h2=hypotheses["E6-H2"], h0=hypotheses["E6-H0"], fired=primary["fired"])
    payload = {"E6-D": e6d, "primary": reading,
               "recorded_alongside": {"E6-H3": hypotheses["E6-H3"],
                                      "pathology": {k: v["raised"] for k, v in primary["pathology"].items()},
                                      "companion": analysis["companion"]}}
    _write_json(records_root(run_root) / INTERPRETATION_RECORD, payload)
    return payload


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m tools.research.v6.e6.run_e6")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("plan")
    seeds_parser = sub.add_parser("generate-seeds")
    seeds_parser.add_argument("--confirm-seed-generation", action="store_true")
    execute_parser = sub.add_parser("execute")
    execute_parser.add_argument("condition", choices=[c.condition_id for c in matrix.CONDITIONS])
    execute_parser.add_argument("field", choices=[f.field_id for f in matrix.FIELDS])
    execute_parser.add_argument("--confirm-matrix-execution", action="store_true")
    execute_parser.add_argument("--confirm-treatment-execution", action="store_true")
    execute_parser.add_argument("--workers", type=int, default=1)
    sub.add_parser("qualify")
    gates_parser = sub.add_parser("treatment-gates")
    gates_parser.add_argument("condition", choices=list(matrix.TREATMENT_CONDITIONS))
    sub.add_parser("analyze")
    reveal_parser = sub.add_parser("reveal")
    reveal_parser.add_argument("seeds_file", type=Path)
    sub.add_parser("interpret")
    args = parser.parse_args(argv)
    command = args.command or "plan"
    try:
        if command == "plan":
            result: Any = plan_report()
        elif command == "generate-seeds":
            result = generate_seeds(confirm=args.confirm_seed_generation)
        elif command == "execute":
            result = execute(args.condition, args.field, confirm=args.confirm_matrix_execution,
                             confirm_treatment=args.confirm_treatment_execution, workers=args.workers)
        elif command == "qualify":
            result = qualify()
        elif command == "treatment-gates":
            result = treatment_gates(args.condition)
        elif command == "analyze":
            result = analyze()
        elif command == "reveal":
            result = reveal(args.seeds_file)
        else:
            result = interpret()
    except (E6ConfigurationError, TreatmentExposureError, AnalysisFreezeError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
