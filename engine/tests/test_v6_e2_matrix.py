"""The frozen V6 E2 experiment definition, pre-registration, runner guards and
C-V4 / C-RS control gate (design review Sec H, Sec I).

Nothing here runs the E2 matrix or any T-E2 match. The control-gate tests run
tiny C-V4 and C-RS harness experiments only.
"""

from __future__ import annotations

import json
import re
import shutil
from dataclasses import replace
from itertools import combinations, product
from pathlib import Path

import pytest
from battle_engine.evaluation_contracts import STANDARD_V4_SEEDS
from battle_engine.ruleset_policy import (
    BYTEFRAY_RULESET_V4_ID,
    BYTEFRAY_RULESET_V6_RESEARCH_CAPTURE_HOLD_K2_ID,
    BYTEFRAY_RULESET_V6_RESEARCH_SCALE_ID,
    resolve_ruleset_policy,
)

from tools.research.v6.e2 import matrix
from tools.research.v6.e2.analysis_freeze import (
    AnalysisFreezeError,
    build_freeze_record,
    identity_inputs,
)
from tools.research.v6.e2.control_gate import (
    ControlGateError,
    compare_control_runs,
    require_control_gate,
    write_gate_record,
)
from tools.research.v6.e2.preregistration import (
    PREREGISTRATION_PATH,
    REQUIRED_HYPOTHESES,
    load_preregistration,
)
from tools.research.v6.e2.run_e2 import (
    E2ConfigurationError,
    check_requests,
    dry_run_plan,
    execute,
    experiment_config,
)
from tools.research.v6.experiment_harness import (
    REPO_ROOT,
    ResearchExperimentConfig,
    experiment_pairs,
    plan_evaluation_requests,
    run_experiment,
)

REVIEW = REPO_ROOT / "docs" / "research" / "v6" / "V6_E2_CAPTURE_HOLD_DESIGN_REVIEW.md"


# ---------------------------------------------------------------------------
# Frozen definition
# ---------------------------------------------------------------------------


def test_fields_and_expected_match_counts() -> None:
    assert [(f.field_id, len(f.pairs), f.expected_matches) for f in matrix.FIELDS] == [
        ("F1", 45, 2880),
        ("F2", 10, 640),
        ("F3", 25, 1600),
    ]
    assert matrix.matches_per_condition() == 5120
    assert matrix.matches_total() == 15360
    assert matrix.F1.pairs == tuple(combinations(matrix.E2_AGENTS, 2))
    assert matrix.F2.pairs == tuple((a, f"{a}_twin") for a in matrix.E2_AGENTS)
    assert matrix.F3.pairs == tuple(product(matrix.F3_EXPERIMENTAL, matrix.F3_REFERENCE))
    # F3 is cross pairs only, and neither F2 nor F3 feeds the primary ratings.
    assert not set(matrix.F3_REFERENCE) & set(matrix.F1.agents)
    assert [f.rated_as_primary for f in matrix.FIELDS] == [True, False, False]


def test_seeds_arena_ticks_orientations_and_conditions_are_frozen() -> None:
    assert matrix.SEEDS == tuple(range(1, 33))
    assert matrix.SEEDS != tuple(STANDARD_V4_SEEDS)
    assert (matrix.ARENA_SIZE, matrix.MAX_TICKS, matrix.BOTH_ORIENTATIONS) == (512, 1000, True)
    assert [(c.condition_id, c.ruleset_id) for c in matrix.CONDITIONS] == [
        ("C-V4", BYTEFRAY_RULESET_V4_ID),
        ("C-RS", BYTEFRAY_RULESET_V6_RESEARCH_SCALE_ID),
        ("T-E2", BYTEFRAY_RULESET_V6_RESEARCH_CAPTURE_HOLD_K2_ID),
    ]
    # No K = 3 arm in the primary experiment.
    assert [resolve_ruleset_policy(c.ruleset_id).capture_hold_ticks for c in matrix.CONDITIONS] == [1, 1, 2]
    assert matrix.FORBIDDEN_REQUEST_OVERRIDES == (
        "scheduler_chunk_size",
        "scheduler_rotate_start",
        "kill_weight",
        "instr_per_tick",
    )


def test_agent_order_is_the_design_review_sec_g_table() -> None:
    text = REVIEW.read_text(encoding="utf-8")
    section = text[text.index("### G.2 Agents") : text.index("## H. Hypotheses")]
    rows = re.findall(r"^\| `([a-z0-9_]+)` \|", section, flags=re.MULTILINE)
    assert tuple(rows) == matrix.E2_AGENTS


def test_matrix_definition_is_frozen() -> None:
    assert matrix.matrix_digest() == matrix.E2_MATRIX_DIGEST
    matrix.verify_frozen_matrix()
    assert matrix.matrix_id() == f"v6-e2-matrix-v1-{matrix.E2_MATRIX_DIGEST[:12]}"


# ---------------------------------------------------------------------------
# Pre-registration: verbatim, frozen, fail-closed
# ---------------------------------------------------------------------------


def _clean(markdown: str) -> str:
    return markdown.replace("**", "").replace("`", "").strip()


def test_hypotheses_are_the_design_review_sec_h_table_verbatim() -> None:
    data = load_preregistration()
    text = REVIEW.read_text(encoding="utf-8")
    section = text[text.index("## H. Hypotheses") : text.index("## I. Experiment Matrix")]
    table = [line for line in section.splitlines() if line.startswith("| **H")]
    assert len(table) == len(REQUIRED_HYPOTHESES)
    for line, item in zip(table, data["hypotheses"], strict=True):
        label, statement, supporting, refuting, prior = [_clean(c) for c in line.strip().strip("|").split("|")]
        assert label == f"{item['id']} {item['name']}"
        assert (statement, supporting, refuting, prior) == (
            item["statement"],
            item["supporting_evidence"],
            item["refuting_evidence"],
            item["probe_prior"],
        )
    rules_block = text[text.index("### I.5 Interpretation rules") : text.index("## J. Test Plan")]
    rules = [_clean(line.split(". ", 1)[1]) for line in rules_block.splitlines() if re.match(r"^\d\. ", line)]
    assert rules == data["interpretation_rules"]
    negative = next(line for line in section.splitlines() if line.startswith("**Negative-result rule"))
    assert _clean(negative).endswith(data["negative_result_rule"])
    for label, key in (
        ("Seat-determination index (SDI).", "sdi"),
        ("Mirror seat bias.", "mirror_seat_bias"),
        ("Recovery rate.", "recovery_rate"),
        ("Phase-lock.", "phase_lock"),
        ("Effective sample size.", "effective_sample_size"),
    ):
        line = next(line for line in text.splitlines() if f"**{label}**" in line)
        assert _clean(line).lstrip("- ").removeprefix(label).strip() == data["definitions"][key]


def test_thresholds_are_the_registered_numbers() -> None:
    data = {item["id"]: item for item in load_preregistration()["hypotheses"]}
    assert data["H0"]["thresholds"] == {"winner_kept_share_min": 0.9, "decision_tick_delta": 1}
    assert data["H3a"]["thresholds"] == {"recoveries_per_tick_min": 0.5}
    assert data["H3b"]["thresholds"] == {"phase_lock_min": 0.95, "near_half_tolerance": 0.05}
    assert data["H3c"]["thresholds"] == {"sdi_seat_determined": 0.9}
    assert data["H3d"]["thresholds"] == {"losses_max": 0, "tie_rate_min": 0.5}
    assert data["H3g"]["thresholds"] == {"onsets_min": 10, "completions_max": 0}


def test_changing_a_preregistered_criterion_fails_closed(tmp_path: Path) -> None:
    tampered = tmp_path / "preregistration.json"
    text = PREREGISTRATION_PATH.read_text(encoding="utf-8")
    tampered.write_text(text.replace('"winner_kept_share_min": 0.9', '"winner_kept_share_min": 0.85'), encoding="utf-8")
    with pytest.raises(RuntimeError, match="pre-registration changed"):
        load_preregistration(tampered)


# ---------------------------------------------------------------------------
# Runner: what actually runs matches the frozen definition
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("condition_id", ["C-V4", "C-RS", "T-E2"])
@pytest.mark.parametrize("field_id", ["F1", "F2", "F3"])
def test_planned_requests_match_the_frozen_definition(tmp_path: Path, condition_id: str, field_id: str) -> None:
    field = matrix.field(field_id)
    config = experiment_config(condition_id, field_id, run_root=tmp_path)
    assert (config.seeds, config.ticks, config.arena_sizes, config.both_orientations) == (
        matrix.SEEDS,
        1000,
        (512,),
        True,
    )
    assert experiment_pairs(config) == field.pairs
    requests = plan_evaluation_requests(config, 512, tmp_path / "plan", tmp_path / "env")
    check_requests(requests, condition_id, seeds=matrix.SEEDS)
    for request in requests:
        assert [getattr(request, name) for name in matrix.FORBIDDEN_REQUEST_OVERRIDES] == [None] * 4
        assert request.ruleset_id == matrix.condition(condition_id).ruleset_id
    assert sum(len(r.opponent_ids) for r in requests) * 32 * 2 == field.expected_matches
    extra = config.provenance_extra
    assert (extra["e2_matrix_id"], extra["e2_condition"], extra["e2_field"], extra["e2_sample"]) == (
        matrix.matrix_id(),
        condition_id,
        field_id,
        False,
    )


@pytest.mark.parametrize(
    ("override", "value"),
    [("scheduler_chunk_size", 3), ("scheduler_rotate_start", False), ("kill_weight", 5.0), ("instr_per_tick", 16)],
)
def test_any_forbidden_override_fails_closed(tmp_path: Path, override: str, value: object) -> None:
    config = experiment_config("C-RS", "F2", run_root=tmp_path)
    requests = plan_evaluation_requests(config, 512, tmp_path / "plan", tmp_path / "env")
    tampered = (replace(requests[0], **{override: value}), *requests[1:])
    with pytest.raises(E2ConfigurationError, match=f"forbidden override {override}"):
        check_requests(tampered, "C-RS", seeds=matrix.SEEDS)


@pytest.mark.parametrize(
    "change",
    [
        {"ruleset_id": BYTEFRAY_RULESET_V4_ID},
        {"arena_size": 4096},
        {"ticks": 300},
        {"seeds": tuple(STANDARD_V4_SEEDS)},
        {"both_orientations": False},
    ],
)
def test_frozen_setting_drift_fails_closed(tmp_path: Path, change: dict[str, object]) -> None:
    config = experiment_config("T-E2", "F1", run_root=tmp_path)
    requests = plan_evaluation_requests(config, 512, tmp_path / "plan", tmp_path / "env")
    with pytest.raises(E2ConfigurationError):
        check_requests((replace(requests[0], **change), *requests[1:]), "T-E2", seeds=matrix.SEEDS)


def test_request_guard_aborts_before_anything_is_written_or_run(tmp_path: Path) -> None:
    config = replace(experiment_config("C-RS", "F2", run_root=tmp_path), scheduler_chunk_size=3)
    with pytest.raises(E2ConfigurationError):
        run_experiment(config, request_guard=lambda r: check_requests(r, "C-RS", seeds=config.seeds))
    assert list(tmp_path.iterdir()) == []


def test_execute_never_runs_without_explicit_confirmation(tmp_path: Path) -> None:
    with pytest.raises(E2ConfigurationError, match="confirm"):
        execute("C-RS", "F2", run_root=tmp_path)
    assert list(tmp_path.iterdir()) == []


def test_treatment_refuses_without_a_freeze_and_a_complete_passing_control_gate(tmp_path: Path) -> None:
    runs = tmp_path / "runs"
    with pytest.raises(AnalysisFreezeError, match="No analysis freeze record"):
        execute("T-E2", "F1", run_root=runs, confirm=True, freeze_path=tmp_path / "missing.json")
    freeze = tmp_path / "freeze.json"
    identity = identity_inputs(tooling_source_sha="a" * 40, match_generation_tree="b" * 40)
    freeze.write_text(json.dumps(build_freeze_record(identity, {})), encoding="utf-8")
    with pytest.raises(ControlGateError, match="No control gate record"):
        execute("T-E2", "F1", run_root=runs, confirm=True, freeze_path=freeze)
    assert not runs.exists()
    with pytest.raises(E2ConfigurationError, match="no sample mode"):
        experiment_config("T-E2", "F1", sample=True)


def test_control_gate_record_rules(tmp_path: Path) -> None:
    expected = {f.field_id: f.expected_matches for f in matrix.FIELDS}
    full = {fid: {"status": "PASS", "cells_compared": n} for fid, n in expected.items()}
    path = tmp_path / "gate.json"

    def write(**kwargs: object) -> None:
        args = {"matrix_id": matrix.matrix_id(), "fields": full, "expected_matches": expected, "sample": False, "provenance": {}}
        args.update(kwargs)
        write_gate_record(path, **args)  # type: ignore[arg-type]

    def check() -> dict[str, object]:
        return require_control_gate(path, matrix_id=matrix.matrix_id(), expected_matches=expected)

    write()
    assert check()["unlocks_treatment"] is True
    for bad, message in (
        ({"sample": True}, "sample"),
        ({"matrix_id": "v6-e2-matrix-v1-000000000000"}, "matrix_id"),
        ({"fields": {**full, "F2": {"status": "FAIL", "cells_compared": 640}}}, "F2"),
        ({"fields": {**full, "F3": {"status": "PASS", "cells_compared": 50}}}, "50 of 1600"),
        ({"fields": {k: v for k, v in full.items() if k != "F1"}}, "F1 was not compared"),
    ):
        write(**bad)
        with pytest.raises(ControlGateError, match=message):
            check()

    # A gate recorded under one analysis freeze never unlocks another.
    write(freeze_id="v6-e2-freeze-v2-aaaaaaaaaaaa")
    assert require_control_gate(
        path, matrix_id=matrix.matrix_id(), expected_matches=expected, freeze_id="v6-e2-freeze-v2-aaaaaaaaaaaa"
    )["unlocks_treatment"]
    for other in ("v6-e2-freeze-v2-bbbbbbbbbbbb", None):
        write(freeze_id=other)
        with pytest.raises(ControlGateError, match="freeze_id"):
            require_control_gate(
                path, matrix_id=matrix.matrix_id(), expected_matches=expected, freeze_id="v6-e2-freeze-v2-aaaaaaaaaaaa"
            )


def test_dry_run_counts_every_cell_with_the_real_planner_and_runs_nothing(tmp_path: Path) -> None:
    rows = [dry_run_plan(c.condition_id, f.field_id) for c in matrix.CONDITIONS for f in matrix.FIELDS]
    assert all(row["consistent"] for row in rows)
    assert [row["planned_cells"] for row in rows] == [2880, 640, 1600] * 3
    assert sum(row["planned_cells"] for row in rows) == 15360
    for row, condition in zip(rows, [c for c in matrix.CONDITIONS for _ in matrix.FIELDS], strict=True):
        assert row["rulesets"] == [condition.ruleset_id]
        assert row["orientations"] == ["candidate_first", "opponent_first"]
        assert row["planned_seed_set"] == list(range(1, 33))
    sample = dry_run_plan("C-V4", "F1", sample=True)
    assert (sample["planned_cells"], sample["planned_seed_set"]) == (45 * 2 * 2, [1, 17])


# ---------------------------------------------------------------------------
# C-V4 / C-RS control gate on real artifacts (no T-E2 execution)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def control_runs(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, Path]:
    root = tmp_path_factory.mktemp("e2-gate")
    base = ResearchExperimentConfig(
        experiment_id="gate-check",
        field=("v4_probe", "v4_probe_twin", "e2_sniper", "e2_disrupt_guard"),
        pairs=(("v4_probe", "v4_probe_twin"), ("e2_sniper", "e2_disrupt_guard")),
        seeds=(1,),
        ticks=40,
    )
    for ruleset_id, name in ((BYTEFRAY_RULESET_V4_ID, "v4"), (BYTEFRAY_RULESET_V6_RESEARCH_SCALE_ID, "rs")):
        run_experiment(replace(base, ruleset_id=ruleset_id, output_dir=root / name))
    return root / "v4", root / "rs"


def test_control_gate_passes_behaviourally_identical_controls(control_runs: tuple[Path, Path]) -> None:
    v4, rs = control_runs
    # Precondition: two different Rulesets really ran.
    v4_cells = json.loads((v4 / "experiment_result.json").read_text(encoding="utf-8"))["conditions"][0]["cells"]
    rs_cells = json.loads((rs / "experiment_result.json").read_text(encoding="utf-8"))["conditions"][0]["cells"]
    ruleset_ids = {
        json.loads((root / c["artifact_dir"] / "result.json").read_text(encoding="utf-8"))["ruleset_id"]
        for root, cells in ((v4, v4_cells), (rs, rs_cells))
        for c in cells
    }
    assert ruleset_ids == {BYTEFRAY_RULESET_V4_ID, BYTEFRAY_RULESET_V6_RESEARCH_SCALE_ID}
    assert {c["match_id"] for c in v4_cells}.isdisjoint({c["match_id"] for c in rs_cells})
    report = compare_control_runs(v4, rs)
    assert (report["status"], report["cells_compared"], report["mismatch_count"]) == ("PASS", 4, 0)


def _copy(rs: Path, tmp_path: Path) -> tuple[Path, list[dict[str, object]]]:
    target = tmp_path / "rs-copy"
    shutil.copytree(rs, target)
    cells = json.loads((target / "experiment_result.json").read_text(encoding="utf-8"))["conditions"][0]["cells"]
    return target, cells


def test_control_gate_fails_on_a_score_difference(control_runs: tuple[Path, Path], tmp_path: Path) -> None:
    v4, rs = control_runs
    target, cells = _copy(rs, tmp_path)
    result_path = target / str(cells[0]["artifact_dir"]) / "result.json"
    result = json.loads(result_path.read_text(encoding="utf-8"))
    result["score"] = {key: value + 1 for key, value in result["score"].items()}
    result_path.write_text(json.dumps(result), encoding="utf-8")
    report = compare_control_runs(v4, target)
    assert report["status"] == "FAIL"
    assert [m["reason"] for m in report["mismatch_samples"]] == ["result_json"]


def test_control_gate_fails_on_a_replay_difference(control_runs: tuple[Path, Path], tmp_path: Path) -> None:
    v4, rs = control_runs
    target, cells = _copy(rs, tmp_path)
    replay_path = target / str(cells[1]["artifact_dir"]) / "replay.jsonl"
    lines = replay_path.read_text(encoding="utf-8").splitlines()
    tick = json.loads(lines[2])
    tick["processes"][0]["anchor"] = (tick["processes"][0]["anchor"] + 1) % 512
    lines[2] = json.dumps(tick)
    replay_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    report = compare_control_runs(v4, target)
    assert report["status"] == "FAIL"
    assert [m["reason"] for m in report["mismatch_samples"]] == ["replay_stream"]


def test_control_gate_fails_on_an_outcome_or_a_missing_cell(control_runs: tuple[Path, Path], tmp_path: Path) -> None:
    v4, rs = control_runs
    target, _ = _copy(rs, tmp_path)
    data = json.loads((target / "experiment_result.json").read_text(encoding="utf-8"))
    data["conditions"][0]["cells"][0]["ticks_run"] += 1
    (target / "experiment_result.json").write_text(json.dumps(data), encoding="utf-8")
    report = compare_control_runs(v4, target)
    assert report["status"] == "FAIL" and report["mismatch_samples"][0]["fields"] == ["ticks_run"]
    del data["conditions"][0]["cells"][3]
    data["conditions"][0]["cells"][0]["ticks_run"] -= 1
    (target / "experiment_result.json").write_text(json.dumps(data), encoding="utf-8")
    report = compare_control_runs(v4, target)
    assert (report["status"], report["missing_in_rs"], report["mismatch_count"]) == ("FAIL", 1, 0)
