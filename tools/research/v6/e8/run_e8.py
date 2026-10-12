"""The V6 E8 runner: the registered order of events as an unlock chain (phase I8-5).

docs/research/v6/V6_E8_ACTIVE_SPATIAL_SENSING_PREREGISTRATION.md (PR8) Sec 9,
11 and 12; implementation plan Sec 8. Defines the E8 matrix (``matrix.py``)
and never executes it implicitly. Every command after ``plan`` needs the
committed analysis freeze, and each later step needs the records of the steps
before it:

1. ``plan``: a structural dry run. It counts every cell of every condition and
   field with the real evaluation planner, using placeholder seed values (the
   positions 1..32), and classifies every planned match with the pre-match
   gate. Executes nothing.
2. ``generate-seeds --confirm-seed-generation`` (I8-6, separately
   authorized): only with the analysis freeze committed and loading, its seed
   block PENDING, no matrix cell anywhere, a clean tree and the qualified
   engine. Writes the private list and puts the commitment and the execution
   identity, and nothing else, into the freeze record, for the operator to
   commit before the first cell.
3. ``execute CONDITION FIELD --confirm-matrix-execution`` (Q8 and T8,
   separately authorized). **Before anything is written:** the freeze loads;
   the committed seed list matches; the execution identity recomputes; D8-9
   passes; ``family_freeze.verify_engine_source`` holds (the engine the family
   was qualified on); the tooling and engine equal the frozen ones on a clean
   tree; and ``compatibility.require_compatible`` passes for **every planned
   match** of the field. A treatment needs ``--confirm-treatment-execution``
   and a PASS control qualification, strata included, named by the freeze
   record. The packages are then copied, checked against the family freeze's
   fingerprints, and gated again as copied; the field runs; every cell is
   re-executed traced, **with the pre-match gate immediately before each
   traced match**; and the rows and descriptive telemetry are extracted.
4. ``qualify`` (Q8): controls only. D8-6 (the parent goldens re-run, and the
   control provenance), CQ8-1 to CQ8-5, and the control-side clauses D8-1
   presence, D8-7, D8-8, D8-11 to D8-15. The record's digest goes into the
   freeze record; it carries the committed seat strata (CQ8-5).
5. ``treatment-gates CONDITION``: E8-D's clauses on a treatment.
6. ``analyze``: the frozen gameplay analysis of both arms and the companion.
   It may run while the seeds are hidden, and it issues no interpretation.
7. ``reveal SEEDS_FILE``: D8-10.
8. ``interpret``: only after D8-10. E8-D's final status, then the registered
   interpretation and disposition of the primary arm, and the companion.

Every printed or saved output before the reveal passes the value-based seed
filter (PR8 Sec 9, step 6). Every control-phase command first checks that no
treatment artifact exists. A failed precondition raises before any match
artifact exists.
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

from tools.research.v6.e3.gates import cell_key, load_cells
from tools.research.v6.e6 import describe
from tools.research.v6.e8 import (
    analyze_e8,
    compatibility,
    decision,
    discipline,
    family,
    family_freeze,
    gates,
    matrix,
    seed_protocol,
    telemetry,
    traces,
)
from tools.research.v6.e8.analysis_freeze import (
    FREEZE_RECORD_PATH,
    PENDING,
    AnalysisFreezeError,
    git_text,
    load_freeze,
    verify_execution_source,
)
from tools.research.v6.experiment_harness import (
    REPO_ROOT,
    ResearchExperimentConfig,
    experiment_pairs,
    plan_evaluation_requests,
    run_experiment,
)

E8_RUNNER_VERSION = 1
DEFAULT_RUN_ROOT = REPO_ROOT / "runs" / "research_v6_e8"
PLACEHOLDER_SEEDS: tuple[int, ...] = tuple(range(1, matrix.SEED_COUNT + 1))
QUALIFICATION_RECORD = "qualification.json"
ANALYSIS_RECORD = "e8_analysis.json"
D8_10_RECORD = "d8_10.json"
INTERPRETATION_RECORD = "e8_interpretation.json"
SIZE_RECORD = "trace_size.json"
TELEMETRY_NAME = "telemetry.jsonl"
PARENT_FREEZE_TEST = matrix.PARENT_FREEZE["test"]


class E8ConfigurationError(RuntimeError):
    """An E8 step would not match the frozen experiment, or runs out of the registered order."""


class TreatmentExposureError(RuntimeError):
    """A treatment artifact exists where only controls may."""


# ---------------------------------------------------------------------------
# Layout and records
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


def write_json(path: Path, payload: Any) -> str:
    data = (json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n").encode("utf-8")
    traces.write_atomically(path, data)
    return hashlib.sha256(data).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise E8ConfigurationError(f"STOP: required record {path} does not exist")
    value: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return value


# ---------------------------------------------------------------------------
# Plan, requests and the pre-match gate
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
        provenance_extra={**provenance, "e8_condition": condition_id, "e8_field": field_id,
                          "e8_runner_version": E8_RUNNER_VERSION},
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
        raise E8ConfigurationError("E8 request check failed: " + "; ".join(problems))


def planned_matches(field_id: str) -> list[tuple[str, str]]:
    """Every match of a field, as (seat A package, seat B package), one per orientation of each pair."""
    field = matrix.field(field_id)
    out: list[tuple[str, str]] = []
    for first, second in field.pairs:
        out.append((first, second))
        if field.both_orientations:
            out.append((second, first))
    return out


def gate_every_match(field_id: str, ruleset_id: str, package_root: Path) -> int:
    """PR8 Sec 13: the pre-match gate for every planned match of a field (each seed's match loads the
    same two packages, so one call per pairing and orientation covers it). Returns the matches gated."""
    gated = 0
    for seat_a, seat_b in planned_matches(field_id):
        compatibility.require_compatible([package_root / seat_a, package_root / seat_b], ruleset_id)
        gated += matrix.SEED_COUNT
    return gated


def dry_run_plan(condition_id: str, field_id: str, seed_list: Sequence[int] = PLACEHOLDER_SEEDS) -> dict[str, Any]:
    field = matrix.field(field_id)
    condition = matrix.condition(condition_id)
    with tempfile.TemporaryDirectory(prefix="e8-plan-") as tmp:
        config = experiment_config(condition_id, field_id, run_root=Path(tmp), seed_list=seed_list, provenance={},
                                   output_dir=Path(tmp) / "out")
        if experiment_pairs(config) != field.pairs:
            raise E8ConfigurationError(f"{field_id}: planned pairs differ from the frozen field")
        family.prepare_data_root(Path(tmp) / "env", field.agents)
        gated = gate_every_match(field_id, condition.ruleset_id, Path(tmp) / "env" / "agents")
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
    return {"condition": condition_id, "field": field_id, "planned_cells": cells, "gated_matches": gated,
            "expected_cells": field.expected_matches, "rulesets": sorted(rulesets),
            "consistent": cells == gated == field.expected_matches and rulesets == {condition.ruleset_id}}


def plan_report() -> dict[str, Any]:
    matrix.verify_frozen_matrix()
    rows = [dry_run_plan(c.condition_id, f.field_id) for c in matrix.CONDITIONS for f in matrix.FIELDS]
    total = sum(row["planned_cells"] for row in rows)
    return {"structural_matrix_id": matrix.matrix_id(), "structural_digest": matrix.STRUCTURAL_DIGEST,
            "placeholder_seeds": True, "rows": rows, "planned_total": total,
            "expected_total": matrix.matches_total(),
            "all_consistent": all(row["consistent"] for row in rows) and total == matrix.matches_total() == 16_896}


# ---------------------------------------------------------------------------
# I8-6: seeds (separately authorized)
# ---------------------------------------------------------------------------


def generate_seeds(*, confirm: bool, run_root: Path = DEFAULT_RUN_ROOT, freeze_path: Path = FREEZE_RECORD_PATH,
                   seeds_path: Path = seed_protocol.PRIVATE_SEEDS_PATH) -> dict[str, Any]:
    if not confirm:
        raise E8ConfigurationError("Refusing to generate seeds: pass --confirm-seed-generation (I8-6 authorization).")
    record = load_freeze(freeze_path)
    if record.get("seed_commitment") != PENDING:
        raise E8ConfigurationError("STOP: the freeze record already carries a seed commitment.")
    if any_matrix_cell(run_root):
        raise E8ConfigurationError("STOP: a matrix cell exists before the seed commitment.")
    if git_text("status", "--porcelain"):
        raise E8ConfigurationError("STOP: seeds are generated only from a clean tree.")
    family_freeze.verify_engine_source(family_freeze.load_freeze())
    seed_list = seed_protocol.generate()
    commitment = seed_protocol.write_private(seed_list, seeds_path)
    block = dict(seed_protocol.committed_record(
        commitment, matrix.STRUCTURAL_DIGEST, datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        git_text("rev-parse", "HEAD")))
    record["seed_commitment"] = block
    freeze_path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    return block


def committed_seeds(record: dict[str, Any], seeds_path: Path = seed_protocol.PRIVATE_SEEDS_PATH) -> tuple[list[int], dict[str, Any]]:
    block = record.get("seed_commitment") or {}
    if block == PENDING or "seed_commitment" not in block:
        raise E8ConfigurationError("STOP: no seed commitment in the freeze record; no matrix cell may run.")
    if seed_protocol.execution_identity(matrix.STRUCTURAL_DIGEST, block["seed_commitment"]) != block["execution_matrix_identity"]:
        raise E8ConfigurationError("STOP: the execution matrix identity does not recompute.")
    try:
        return seed_protocol.load_private(block["seed_commitment"], seeds_path), block
    except (OSError, seed_protocol.SeedProtocolError) as exc:
        raise E8ConfigurationError(f"STOP: the private seed list is missing or does not match: {exc}") from None


def seed_guard(record: dict[str, Any], seeds_path: Path = seed_protocol.PRIVATE_SEEDS_PATH) -> seed_protocol.SeedGuard | None:
    """The value-based filter, once seeds exist; None before any seed exists."""
    if (record.get("seed_commitment") or PENDING) == PENDING:
        return None
    seed_list, _ = committed_seeds(record, seeds_path)
    return seed_protocol.SeedGuard(seed_list)


# ---------------------------------------------------------------------------
# Q8 and T8: execution (separately authorized)
# ---------------------------------------------------------------------------


def require_control_qualification(record: dict[str, Any], run_root: Path) -> dict[str, Any]:
    block = record.get("control_qualification") or {}
    if block.get("status") != "PASS":
        raise E8ConfigurationError("STOP: no PASS control qualification in the freeze record.")
    path = records_root(run_root) / QUALIFICATION_RECORD
    if hashlib.sha256(path.read_bytes()).hexdigest() != block.get("record_sha256"):
        raise E8ConfigurationError("STOP: the qualification record differs from the one the freeze record names.")
    if not read_json(path).get("CQ8-5", {}).get("strata"):
        raise E8ConfigurationError("STOP: the seat strata (CQ8-5) are not committed in the qualification record.")
    return block


def preconditions(condition_id: str, field_id: str, *, record: dict[str, Any]) -> int:
    """Every check that must hold before a field may write anything. Returns the matches gated."""
    matrix.verify_frozen_matrix()
    if not discipline.passes(family.FIXTURE_DIR / pid for pid in family.PACKAGES):
        raise E8ConfigurationError("STOP: D8-9 discipline fails.")
    family_freeze.verify_engine_source(family_freeze.load_freeze())
    verify_execution_source(record)
    return gate_every_match(field_id, matrix.condition(condition_id).ruleset_id, family.FIXTURE_DIR)


def copy_packages(env: Path, field_id: str, ruleset_id: str) -> int:
    """Copy the field's packages, check them against the family freeze, and gate every match as copied."""
    field = matrix.field(field_id)
    family.prepare_data_root(env, field.agents)
    frozen = family_freeze.load_freeze()["body"]["packages"]
    for pid in field.agents:
        for name in ("agent.py", "agent.yaml"):
            digest = hashlib.sha256((env / "agents" / pid / name).read_bytes().replace(b"\r\n", b"\n")).hexdigest()
            if digest != frozen[pid][name.replace(".", "_") + "_sha256"]:
                raise E8ConfigurationError(f"STOP: the copied {pid}/{name} differs from the family freeze")
    return gate_every_match(field_id, ruleset_id, env / "agents")


def execute(condition_id: str, field_id: str, *, confirm: bool = False, confirm_treatment: bool = False,
            workers: int = 1, run_root: Path = DEFAULT_RUN_ROOT, freeze_path: Path = FREEZE_RECORD_PATH,
            seeds_path: Path = seed_protocol.PRIVATE_SEEDS_PATH) -> dict[str, Any]:
    if not confirm:
        raise E8ConfigurationError("Refusing to execute: pass --confirm-matrix-execution.")
    condition = matrix.condition(condition_id)
    if condition.role == matrix.TREATMENT and not confirm_treatment:
        raise E8ConfigurationError(f"Refusing to execute treatment {condition_id}: it needs separate authorization "
                                   "(--confirm-treatment-execution) and the full unlock chain.")
    record = load_freeze(freeze_path)
    seed_list, block = committed_seeds(record, seeds_path)
    if condition.role == matrix.TREATMENT:
        require_control_qualification(record, run_root)
    else:
        assert_no_treatment_artifacts(run_root)
    gated = preconditions(condition_id, field_id, record=record)
    field = matrix.field(field_id)
    provenance = {"e8_structural_matrix_id": matrix.matrix_id(), "e8_structural_digest": matrix.STRUCTURAL_DIGEST,
                  "e8_execution_matrix_id": block["execution_matrix_identity"],
                  "e8_seed_commitment": block["seed_commitment"], "e8_analysis_freeze_id": record["freeze_id"],
                  "e8_family_freeze_id": family_freeze.load_freeze()["identity"]}
    config = experiment_config(condition_id, field_id, run_root=run_root, seed_list=seed_list,
                               provenance=provenance, workers=workers)
    assert config.output_dir is not None
    if config.output_dir.exists():
        raise E8ConfigurationError(f"{config.output_dir} already exists; an E8 field is never re-run in place.")
    copy_packages(config.output_dir / "env", field_id, condition.ruleset_id)
    result = run_experiment(config, request_guard=lambda requests: check_requests(
        requests, condition_id, field_id, seed_list=seed_list))
    cells = sum(len(block_["cells"]) for block_ in result["conditions"])
    if cells != field.expected_matches:
        raise E8ConfigurationError(f"{condition_id}/{field_id}: {cells} cells ran, {field.expected_matches} expected")
    records = traces.trace_field(config.output_dir, data_root=config.output_dir / "env", ticks=field.max_ticks,
                                 arena_size=matrix.ARENA_SIZE, expected_cells=field.expected_matches)
    traces.rows_field(config.output_dir, records, arena=matrix.ARENA_SIZE)
    write_telemetry(config.output_dir, records, active=condition.sensing_mode == "active")
    verify_execution_source(load_freeze(freeze_path))
    family_freeze.verify_engine_source(family_freeze.load_freeze())
    size_path = records_root(run_root) / SIZE_RECORD
    if not size_path.exists():
        write_json(size_path, {"measured_on": [condition_id, field_id],
                               **traces.size_report(records, matrix_cells=matrix.matches_total())})
    return {"condition": condition_id, "field": field_id, "cells": cells, "traced": len(records),
            "gated_matches": gated}


def write_telemetry(field_root: Path, records: Sequence[traces.TraceRecord], *, active: bool) -> Path:
    summaries = {line["schedule_id"]: line["summary"] for line in traces.read_summaries(field_root)}
    lines = []
    for record in records:
        members = {"A": family.PACKAGES[record.seat_a][0], "B": family.PACKAGES[record.seat_b][0]}
        lines.append({"schedule_id": record.schedule_id, "telemetry": telemetry.cell_telemetry(
            traces.read_rows(field_root, record), summaries[record.schedule_id], members=members, active=active)})
    lines.sort(key=lambda line: line["schedule_id"])
    path = field_root / traces.TRACES_DIR / TELEMETRY_NAME
    traces.write_atomically(path, b"".join(json.dumps(line, sort_keys=True).encode("utf-8") + b"\n" for line in lines))
    return path


def read_telemetry(field_root: Path) -> dict[str, dict[str, Any]]:
    path = field_root / traces.TRACES_DIR / TELEMETRY_NAME
    return {line["schedule_id"]: line["telemetry"]
            for line in (json.loads(raw) for raw in path.read_text(encoding="utf-8").splitlines() if raw)}


# ---------------------------------------------------------------------------
# Loading a run
# ---------------------------------------------------------------------------


def field_cells(run_root: Path, condition_id: str, field_id: str) -> list[dict[str, Any]]:
    return load_cells(condition_root(run_root, condition_id, field_id))


def condition_data(run_root: Path, condition_id: str) -> analyze_e8.ConditionData:
    f1_root = condition_root(run_root, condition_id, "F1")
    f1 = field_cells(run_root, condition_id, "F1")
    f2 = field_cells(run_root, condition_id, "F2")
    contact = {cell_key(cell): analyze_e8.hostile_core_contact(f1_root / str(cell["artifact_dir"]) / "replay.jsonl")
               for cell in f1}
    telemetry_rows = {**read_telemetry(f1_root), **read_telemetry(condition_root(run_root, condition_id, "F2"))}
    return analyze_e8.ConditionData(condition_id, tuple(f1), tuple(f2), contact, telemetry_rows)


def field_checks(run_root: Path, condition_id: str) -> list[gates.FieldChecks]:
    return [gates.check_field(condition_root(run_root, condition_id, f.field_id),
                              field_cells(run_root, condition_id, f.field_id), condition_id=condition_id,
                              field_id=f.field_id, expected_cells=f.expected_matches) for f in matrix.FIELDS]


def provenance(run_root: Path, condition_id: str, field_id: str) -> dict[str, Any]:
    return read_json(condition_root(run_root, condition_id, field_id) / "provenance.json")


# ---------------------------------------------------------------------------
# Q8: control qualification
# ---------------------------------------------------------------------------


def parent_goldens_pass() -> bool:
    proc = subprocess.run([sys.executable, "-m", "pytest", "-q", "--no-header", "-p", "no:cacheprovider",
                           PARENT_FREEZE_TEST], cwd=REPO_ROOT, capture_output=True, text=True, check=False)
    return proc.returncode == 0


def control_clauses(run_root: Path, condition_id: str, checks: Sequence[gates.FieldChecks]) -> dict[str, Any]:
    """The E8-D clauses evaluated on a control: D8-1 presence, D8-7, D8-8, D8-11 to D8-15."""
    summaries = [*traces.read_summaries(condition_root(run_root, condition_id, "F1")),
                 *traces.read_summaries(condition_root(run_root, condition_id, "F2"))]
    return {
        "D8-1": gates.d8_1(checks),
        "D8-7": gates.d8_7(summaries),
        "D8-8": gates.d8_8(checks),
        "D8-11": gates.d8_11(condition_root(run_root, condition_id, "F2"), field_cells(run_root, condition_id, "F2"),
                             expected_units=len(matrix.F2.pairs) * matrix.SEED_COUNT),
        "D8-12": gates.d8_12(checks),
        "D8-13": gates.d8_13(checks),
        "D8-14": gates.d8_14(checks),
        "D8-15": gates.d8_15(checks),
    }


def qualify(*, run_root: Path = DEFAULT_RUN_ROOT, freeze_path: Path = FREEZE_RECORD_PATH,
            seeds_path: Path = seed_protocol.PRIVATE_SEEDS_PATH) -> dict[str, Any]:
    assert_no_treatment_artifacts(run_root)
    record = load_freeze(freeze_path)
    seed_list, block = committed_seeds(record, seeds_path)
    report: dict[str, Any] = {"freeze_id": record["freeze_id"], "execution_matrix_id": block["execution_matrix_identity"]}
    provenance_problems: list[str] = []
    for condition_id in matrix.CONTROL_CONDITIONS:
        for field in matrix.FIELDS:
            prov = provenance(run_root, condition_id, field.field_id)
            if prov.get("ruleset_id") != matrix.condition(condition_id).ruleset_id:
                provenance_problems.append(f"{condition_id}/{field.field_id}: Ruleset {prov.get('ruleset_id')}")
            if prov.get("e8_execution_matrix_id") != block["execution_matrix_identity"] or \
                    prov.get("e8_seed_commitment") != block["seed_commitment"] or \
                    prov.get("e8_structural_matrix_id") != matrix.matrix_id():
                provenance_problems.append(f"{condition_id}/{field.field_id}: provenance lacks the identities")
            if prov.get("git_dirty") is not False:
                provenance_problems.append(f"{condition_id}/{field.field_id}: executed from a dirty tree")
    goldens = parent_goldens_pass()
    report["D8-6"] = {"parent_goldens_pass": goldens, "provenance_problems": provenance_problems,
                      "status": decision.PASS if goldens and not provenance_problems else decision.FAIL}
    all_checks: list[gates.FieldChecks] = []
    for condition_id in matrix.CONTROL_CONDITIONS:
        checks = field_checks(run_root, condition_id)
        all_checks += checks
        report[condition_id] = control_clauses(run_root, condition_id, checks)
    report["CQ8-1"] = gates.cq8_1(all_checks)
    report["CQ8-2"] = gates.cq8_2([c for c in all_checks if c.field_id == "F1"])
    frozen_family = family_freeze.load_freeze()
    frozen_census = frozen_family["body"]["census"]["primary"]
    report["CQ8-3"] = {"family_freeze_id": frozen_family["identity"], "census": list(frozen_census),
                       "status": decision.PASS if frozen_census else decision.FAIL}
    for arm, (control_id, _) in matrix.ARMS.items():
        control = condition_data(run_root, control_id)
        result = analyze_e8.analyze_arm(control, control, seeds=seed_list)
        report[f"CQ8-4:{arm}"] = analyze_e8.control_against_control(result)
    primary_control = condition_data(run_root, matrix.ARMS[matrix.PRIMARY_ARM][0])
    report["CQ8-5"] = {"strata": analyze_e8.seat_strata(analyze_e8.seat_results(primary_control, seeds=seed_list)),
                       "computed_on": matrix.ARMS[matrix.PRIMARY_ARM][0], "status": decision.PASS}
    report["trace_size"] = read_json(records_root(run_root) / SIZE_RECORD)
    statuses = [report["D8-6"]["status"], report["CQ8-1"]["status"], report["CQ8-2"]["status"],
                report["CQ8-3"]["status"], report["CQ8-5"]["status"]]
    statuses += [report[f"CQ8-4:{arm}"]["status"] for arm in matrix.ARMS]
    statuses += [clause["status"] for condition_id in matrix.CONTROL_CONDITIONS
                 for clause in report[condition_id].values()]
    report["status"] = decision.PASS if all(status == decision.PASS for status in statuses) else decision.FAIL
    digest = write_json(records_root(run_root) / QUALIFICATION_RECORD, report)
    return {"status": report["status"], "record_sha256": digest}


# ---------------------------------------------------------------------------
# T8: treatment gates, analysis, reveal and interpretation
# ---------------------------------------------------------------------------


def treatment_gates(condition_id: str, *, run_root: Path = DEFAULT_RUN_ROOT,
                    freeze_path: Path = FREEZE_RECORD_PATH, seeds_path: Path = seed_protocol.PRIVATE_SEEDS_PATH) -> dict[str, Any]:
    condition = matrix.condition(condition_id)
    if condition.role != matrix.TREATMENT:
        raise E8ConfigurationError(f"{condition_id} is not a treatment")
    record = load_freeze(freeze_path)
    require_control_qualification(record, run_root)
    seed_list, _ = committed_seeds(record, seeds_path)
    checks = field_checks(run_root, condition_id)
    f1_cells = field_cells(run_root, condition_id, "F1")
    report: dict[str, Any] = {
        "condition": condition_id, "freeze_id": record["freeze_id"],
        "D8-1": gates.d8_1(checks), "D8-2": gates.d8_2(checks), "D8-3": gates.d8_3(checks, f1_cells, seeds=seed_list),
        "D8-4": gates.d8_4(checks), "D8-5": gates.d8_5(checks), "D8-8": gates.d8_8(checks),
        "D8-11": gates.d8_11(condition_root(run_root, condition_id, "F2"), field_cells(run_root, condition_id, "F2"),
                             expected_units=len(matrix.F2.pairs) * matrix.SEED_COUNT),
        "D8-12": gates.d8_12(checks), "D8-13": gates.d8_13(checks), "D8-14": gates.d8_14(checks),
        "D8-15": gates.d8_15(checks),
    }
    report["status"] = decision.PASS if all(value["status"] == decision.PASS for key, value in report.items()
                                            if key.startswith("D8-")) else decision.FAIL
    write_json(records_root(run_root) / f"treatment_gates_{condition_id}.json", report)
    return report


def analyze(*, run_root: Path = DEFAULT_RUN_ROOT, freeze_path: Path = FREEZE_RECORD_PATH,
            seeds_path: Path = seed_protocol.PRIVATE_SEEDS_PATH) -> dict[str, Any]:
    """The frozen gameplay analysis. May run while seeds are hidden; issues no interpretation."""
    record = load_freeze(freeze_path)
    require_control_qualification(record, run_root)
    seed_list, _ = committed_seeds(record, seeds_path)
    for condition_id in matrix.TREATMENT_CONDITIONS:
        read_json(records_root(run_root) / f"treatment_gates_{condition_id}.json")
    arms = {}
    for arm, (control_id, treatment_id) in matrix.ARMS.items():
        arms[arm] = analyze_e8.analyze_arm(condition_data(run_root, control_id),
                                           condition_data(run_root, treatment_id), seeds=seed_list)
    # PR8 Sec 6.5: E4's cell metrics, FMA and FPS, for every F1 cell of all four conditions (descriptive).
    descriptive = {c.condition_id: describe.alternation(condition_root(run_root, c.condition_id, "F1"),
                                                        field_cells(run_root, c.condition_id, "F1"))
                   for c in matrix.CONDITIONS}
    payload = {"freeze_id": record["freeze_id"], "arms": {arm: analyze_e8.public(r) for arm, r in arms.items()},
               "companion": analyze_e8.companion_reading(arms[matrix.PRIMARY_ARM], arms[matrix.COMPANION_ARM]),
               "alternation": descriptive, "interpretation": "withheld until D8-10 (PR8 Sec 9, step 7)"}
    write_json(records_root(run_root) / ANALYSIS_RECORD, payload)
    return payload


def all_cell_seeds(run_root: Path) -> list[int]:
    return [int(cell["seed"]) for c in matrix.CONDITIONS for f in matrix.FIELDS
            for cell in field_cells(run_root, c.condition_id, f.field_id)]


def reveal(revealed_path: Path, *, run_root: Path = DEFAULT_RUN_ROOT,
           freeze_path: Path = FREEZE_RECORD_PATH) -> dict[str, Any]:
    record = load_freeze(freeze_path)
    read_json(records_root(run_root) / ANALYSIS_RECORD)
    block = record.get("seed_commitment") or {}
    if block == PENDING:
        raise E8ConfigurationError("STOP: nothing was committed, so nothing can be revealed.")
    report = seed_protocol.d8_10(revealed_path.read_bytes(), committed=block["seed_commitment"],
                         structural_digest=matrix.STRUCTURAL_DIGEST,
                         committed_execution_identity=block["execution_matrix_identity"],
                         cell_seeds=all_cell_seeds(run_root))
    write_json(records_root(run_root) / D8_10_RECORD, report)
    return report


def e8d_status(run_root: Path) -> dict[str, Any]:
    """E8-D's final status, D8-1 to D8-15: each clause from its record, D8-9 re-checked statically."""
    records = records_root(run_root)
    qualification = read_json(records / QUALIFICATION_RECORD)
    d8_10 = read_json(records / D8_10_RECORD)
    treatment = [read_json(records / f"treatment_gates_{c}.json") for c in matrix.TREATMENT_CONDITIONS]
    controls = [qualification[c] for c in matrix.CONTROL_CONDITIONS]

    def passes(name: str, *, controls_too: bool) -> bool:
        reports = [t[name] for t in treatment] + ([c[name] for c in controls] if controls_too else [])
        return all(r["status"] == decision.PASS for r in reports)

    clauses = {
        "D8-1": passes("D8-1", controls_too=True), "D8-2": passes("D8-2", controls_too=False),
        "D8-3": passes("D8-3", controls_too=False), "D8-4": passes("D8-4", controls_too=False),
        "D8-5": passes("D8-5", controls_too=False), "D8-6": qualification["D8-6"]["status"] == decision.PASS,
        "D8-7": all(c["D8-7"]["status"] == decision.PASS for c in controls),
        "D8-8": passes("D8-8", controls_too=True),
        "D8-9": discipline.passes(family.FIXTURE_DIR / pid for pid in family.PACKAGES),
        "D8-10": d8_10["status"] == decision.PASS,
        "D8-11": passes("D8-11", controls_too=True), "D8-12": passes("D8-12", controls_too=True),
        "D8-13": passes("D8-13", controls_too=True), "D8-14": passes("D8-14", controls_too=True),
        "D8-15": passes("D8-15", controls_too=True),
    }
    return gates.e8_d({name: decision.PASS if held else decision.FAIL for name, held in clauses.items()})


def interpret(*, run_root: Path = DEFAULT_RUN_ROOT, freeze_path: Path = FREEZE_RECORD_PATH) -> dict[str, Any]:
    load_freeze(freeze_path)
    analysis = read_json(records_root(run_root) / ANALYSIS_RECORD)
    read_json(records_root(run_root) / D8_10_RECORD)  # the reveal comes first
    e8d = e8d_status(run_root)
    primary = analysis["arms"][matrix.PRIMARY_ARM]
    payload = {"E8-D": e8d, "primary": analyze_e8.interpret(e8_d=e8d["status"], primary=primary),
               "companion": analysis["companion"]}
    write_json(records_root(run_root) / INTERPRETATION_RECORD, payload)
    return payload


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def guarded(text: str, *, freeze_path: Path = FREEZE_RECORD_PATH, run_root: Path = DEFAULT_RUN_ROOT,
            seeds_path: Path = seed_protocol.PRIVATE_SEEDS_PATH) -> str:
    """PR8 Sec 9, step 6: before the reveal, an output passes the value-based seed filter.

    The record is read as committed, not re-verified: the filter must work even
    when the instrument has drifted, which is exactly when an error is printed.
    """
    if (records_root(run_root) / D8_10_RECORD).exists():
        return text
    if not freeze_path.is_file():
        return text  # no freeze record, so no seed can exist
    record = json.loads(freeze_path.read_text(encoding="utf-8"))
    if (record.get("seed_commitment") or PENDING) == PENDING:
        return text
    try:
        guard = seed_guard(record, seeds_path)
    except E8ConfigurationError:
        return "[withheld: a seed commitment exists but the private list cannot be loaded to filter this output]"
    return text if guard is None else guard.redact(text)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m tools.research.v6.e8.run_e8")
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
    except (E8ConfigurationError, TreatmentExposureError, AnalysisFreezeError, compatibility.IncompatiblePairing,
            family_freeze.FreezeError) as exc:
        print(guarded(str(exc)), file=sys.stderr)
        return 2
    print(guarded(json.dumps(result, indent=2, sort_keys=True, default=str)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
