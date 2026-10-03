"""The E3 pipeline on real control corpora: telemetry, populations, the control
baseline, the criteria, and the qualification gates.

A small C-E2 control sample (seed 1, every pairing of every field) is run
through the frozen harness exactly as ``run_e3`` runs a field; nothing runs
under a treatment Ruleset except the non-matrix, scripted-opponent scenario
that checks the prefix gate's premise (``d9_gate.run_hosted_match``).
"""

from __future__ import annotations

import dataclasses
import json
import shutil
from pathlib import Path
from typing import Any

import pytest
from battle_engine.agent_api import ActionKindV2, AgentAction

from tools.research.v6.e3 import analyze_e3 as a
from tools.research.v6.e3 import matrix, run_e3
from tools.research.v6.e3.d9_gate import run_hosted_match
from tools.research.v6.e3.entrants import prepare_data_root
from tools.research.v6.e3.gates import (
    ParentReproductionError,
    compare_parent_reproduction,
    load_cells,
    parity_replicate_prefix,
    prefix_gate,
    prefix_gate_cell,
    require_parent_reproduction,
    write_parent_record,
)
from tools.research.v6.e3.preregistration import load_preregistration
from tools.research.v6.e3.telemetry import (
    compute_telemetry,
    read_rows,
    row_digests,
    summarize,
    write_rows,
)

SEEDS = (1,)


def _run_field(root: Path, condition_id: str, field_id: str) -> Path:
    config = run_e3.experiment_config(condition_id, field_id, sample=True, output_dir=root / condition_id / field_id)
    config = dataclasses.replace(config, seeds=SEEDS)
    run_e3._run(config, condition_id, field_id)
    assert config.output_dir is not None
    return config.output_dir


@pytest.fixture(scope="module")
def control(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Any]:
    root = tmp_path_factory.mktemp("e3-control")
    roots = {f: _run_field(root, "C-E2", f) for f in matrix.FIELD_IDS}
    rows = {f: compute_telemetry(r) for f, r in roots.items()}
    runs = {f: a.make_field_run("C-E2", f, load_cells(roots[f]), rows[f]) for f in matrix.FIELD_IDS}
    again = _run_field(tmp_path_factory.mktemp("e3-again"), "C-E2", "F2")
    return {"roots": roots, "rows": rows, "runs": runs, "f2_again": again, "f2_again_rows": compute_telemetry(again)}


def test_control_telemetry_is_clean_and_repeatable(control: dict[str, Any], tmp_path: Path) -> None:
    for field_id, rows in control["rows"].items():
        summary = summarize(rows)
        assert summary["clean"] and summary["analyzed"] == summary["cells"] == matrix.field(field_id).expected_matches // 32
        assert (summary["analyzer_failures"], summary["cpu_statistics_mismatches"],
                summary["capture_engine_disagreements"], summary["ownership_reconstruction_disagreements"]) == (0, 0, 0, 0)
        # Entrants that are never zeroed are categorised, never scored as phase-lock 0.
        assert summary["phase_lock_categories"]["NO_ZERO_CORE_TICKS"] > 0
    # A second, independent pass reproduces every row; the file round-trips.
    assert row_digests(compute_telemetry(control["roots"]["F4"])) == row_digests(control["rows"]["F4"])
    write_rows(tmp_path / "f4.jsonl", control["rows"]["F4"], corpus={"corpus": "C-E2", "field": "F4"})
    assert row_digests(read_rows(tmp_path / "f4.jsonl")[1]) == row_digests(control["rows"]["F4"])


def test_populations_are_defined_from_the_control(control: dict[str, Any]) -> None:
    frozen = a.populations(control["runs"])
    # The pure repair guards never hit each other: F2's (and F2-P's) only hit-free mirror.
    mirror = "e2_repair_guard|e2_repair_guard_twin|1"
    for field_id in ("F2", "F2-P"):
        assert frozen[field_id]["hit_free"] == [f"{mirror}|candidate_first", f"{mirror}|opponent_first"]
        assert set(frozen[field_id]["exposed"]) == set(control["runs"][field_id].cells) - set(frozen[field_id]["hit_free"])
    # Every F1 cell contains a hit and is exposed (review Sec B).
    assert frozen["F1"]["hit_free"] == [] and len(frozen["F1"]["exposed"]) == 90
    for field_id, keys in frozen.items():
        for key in keys["stalemate"]:
            cell = control["runs"][field_id].cells[key]
            assert cell["termination_reason"] == "tick_limit"
            assert any(s["capture"]["recoveries"] for s in control["runs"][field_id].t(key)["seats"].values())
    assert frozen["F1"]["stalemate"]


def test_control_baseline_and_identity_evaluation_on_real_data(control: dict[str, Any]) -> None:
    prereg = load_preregistration()
    frozen = a.populations(control["runs"])
    baseline = a.control_baseline(control["runs"], frozen, prereg)
    units = {(u["field"], tuple(u["pairing"])) for u in baseline["D2_seat_determined_units"]}
    registered = {(u["field"], tuple(u["pairing"])) for h in prereg["hypotheses"] if h["id"] == "D2"
                  for u in h["criterion"]["units"]}
    assert registered <= units
    # Under the whole-tick parent the stalemates are first-mover locked (E2 H3b).
    assert baseline["parity_stalemate"]["median_fms"] == 1.0 and baseline["parity_stalemate"]["median_pd"] == 1.0
    assert baseline["D3_repair_guard_capture_losses"]
    assert baseline["D9_guard_completions"] > 0
    assert baseline["actions_standard"]["exclusive_share"] > 0.5
    out = a.evaluate_hypotheses(control["runs"], control["runs"], frozen, prereg,
                                control_residuals=baseline["residuals_f1"])
    assert out["D0"]["transitions"]["unchanged_share"] == 1.0 and out["D2"]["status"] == a.REFUTED
    assert out["D7"]["rise"] == 0.0 and out["D3"]["status"] == a.REFUTED
    # The D9 check is live on real completions: the control's guards *are* captured.
    assert out["D9"]["status"] == a.STOP and out["D9"]["primary_completions"] == baseline["D9_guard_completions"]
    assert out["residuals_secondary"]["seat_a"]["counting"] == []


# ---------------------------------------------------------------------------
# Parent reproduction
# ---------------------------------------------------------------------------


def _copy(root: Path, tmp: Path) -> Path:
    target = tmp / "copy"
    shutil.copytree(root, target)
    return target


def _first_replay(root: Path) -> Path:
    return root / str(load_cells(root)[0]["artifact_dir"]) / "replay.jsonl"


def test_identical_controls_reproduce(control: dict[str, Any]) -> None:
    report = compare_parent_reproduction(control["f2_again"], control["roots"]["F2"],
                                         new_telemetry=control["f2_again_rows"], historical_telemetry=control["rows"]["F2"])
    assert (report["status"], report["cells_compared"], report["mismatch_count"]) == ("PASS", 20, 0)


def test_reproduction_fails_on_replay_bytes(control: dict[str, Any], tmp_path: Path) -> None:
    copy = _copy(control["f2_again"], tmp_path)
    replay = _first_replay(copy)
    replay.write_bytes(replay.read_bytes() + b"\n")
    report = compare_parent_reproduction(copy, control["roots"]["F2"], new_telemetry=control["f2_again_rows"],
                                         historical_telemetry=control["rows"]["F2"])
    assert report["status"] == "FAIL" and report["mismatch_reasons"] == {"replay_bytes": 1}


def test_reproduction_fails_on_result_identity_and_missing_cells(control: dict[str, Any], tmp_path: Path) -> None:
    copy = _copy(control["f2_again"], tmp_path)
    result = _first_replay(copy).with_name("result.json")
    data = json.loads(result.read_text(encoding="utf-8"))
    data["score"] = {k: v + 1 for k, v in data["score"].items()}
    result.write_text(json.dumps(data), encoding="utf-8")
    experiment = json.loads((copy / "experiment_result.json").read_text(encoding="utf-8"))
    experiment["conditions"][0]["cells"].pop()
    (copy / "experiment_result.json").write_text(json.dumps(experiment), encoding="utf-8")
    report = compare_parent_reproduction(copy, control["roots"]["F2"], new_telemetry=control["f2_again_rows"],
                                         historical_telemetry=control["rows"]["F2"])
    assert report["mismatch_reasons"] == {"missing_in_new": 1, "result_json": 1}


def test_reproduction_fails_on_telemetry(control: dict[str, Any]) -> None:
    rows = json.loads(json.dumps(control["f2_again_rows"]))
    key = min(rows)
    rows[key]["telemetry"]["exclusive_ticks"] += 1
    report = compare_parent_reproduction(control["f2_again"], control["roots"]["F2"], new_telemetry=rows,
                                         historical_telemetry=control["rows"]["F2"])
    assert report["mismatch_reasons"] == {"telemetry": 1}


def test_only_a_complete_non_sample_record_permits_treatment(tmp_path: Path) -> None:
    expected = {"C-E2": {"F1": 2}, "C-RS": {"F1": 2}}
    passing = {"status": "PASS", "cells_compared": 2}
    args = {"matrix_id": matrix.matrix_id(), "freeze_id": "v6-e3-freeze-v1-x", "expected_matches": expected}
    path = tmp_path / "parent.json"
    write_parent_record(path, reproduction={"C-E2": {"F1": passing}, "C-RS": {"F1": passing}}, fresh={},
                        sample=True, provenance={}, matrix_id=args["matrix_id"], freeze_id=args["freeze_id"],
                        expected_matches=expected)
    with pytest.raises(ParentReproductionError, match="sample"):
        require_parent_reproduction(path, **args)  # type: ignore[arg-type]
    write_parent_record(path, reproduction={"C-E2": {"F1": passing}, "C-RS": {"F1": {"status": "PASS", "cells_compared": 1}}},
                        fresh={}, sample=False, provenance={}, matrix_id=args["matrix_id"], freeze_id=args["freeze_id"],
                        expected_matches=expected)
    with pytest.raises(ParentReproductionError, match="complete|1 of 2"):
        require_parent_reproduction(path, **args)  # type: ignore[arg-type]
    write_parent_record(path, reproduction={"C-E2": {"F1": passing}, "C-RS": {"F1": passing}}, fresh={},
                        sample=False, provenance={}, matrix_id=args["matrix_id"], freeze_id=args["freeze_id"],
                        expected_matches=expected)
    assert require_parent_reproduction(path, **args)["unlocks_treatment"] is True  # type: ignore[arg-type]
    with pytest.raises(ParentReproductionError, match="freeze_id"):
        require_parent_reproduction(path, matrix_id=matrix.matrix_id(), freeze_id="other", expected_matches=expected)


# ---------------------------------------------------------------------------
# F2-P against F2, and the treatment prefix gate
# ---------------------------------------------------------------------------


def test_parity_replicate_equals_f2_through_tick_1000(control: dict[str, Any]) -> None:
    f2 = {c["subject_id"] + c["orientation"]: c for c in load_cells(control["roots"]["F2"])}
    f2p = load_cells(control["roots"]["F2-P"])
    assert len(f2p) == 20
    lengths = set()
    for cell in f2p:
        other = f2[cell["subject_id"] + cell["orientation"]]
        row = parity_replicate_prefix(control["roots"]["F2"] / other["artifact_dir"] / "replay.jsonl",
                                      control["roots"]["F2-P"] / cell["artifact_dir"] / "replay.jsonl", tick_limit=1000)
        assert row["ok"], row
        lengths.add(row["compared_through"])
    assert 1000 in lengths  # the tick-limit mirrors are compared across all 1000 ticks


def _rewrite_tick(replay: Path, tick: int) -> None:
    lines = replay.read_text(encoding="utf-8").splitlines()
    for index, line in enumerate(lines):
        record = json.loads(line)
        if record.get("record_type") == "tick" and record["tick"] == tick:
            record["score"] = {k: v + 100 for k, v in record["score"].items()}
            lines[index] = json.dumps(record)
    replay.write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_prefix_gate_on_the_control_side(control: dict[str, Any], tmp_path: Path) -> None:
    root = control["roots"]["F2"]
    frozen = a.populations(control["runs"])["F2"]["hit_free"]
    same = prefix_gate(root, root, frozen_hit_free=frozen)
    assert (same["status"], same["cells_compared"], same["hit_free_cells"]) == ("PASS", 20, 2)
    assert prefix_gate(root, root, frozen_hit_free=frozen[:1])["status"] == "FAIL"
    cells = {c["subject_id"] + "|" + c["orientation"]: c for c in load_cells(root)}
    probe = cells["v4_probe|candidate_first"]
    hit_free = cells["e2_repair_guard|candidate_first"]
    # A change after the control's first hit is allowed; before it, or anywhere
    # in a hit-free cell, it is a hard stop.
    after = _copy(root, tmp_path / "after")
    _rewrite_tick(after / probe["artifact_dir"] / "replay.jsonl", 1)
    assert prefix_gate_cell(root / probe["artifact_dir"] / "replay.jsonl",
                            after / probe["artifact_dir"] / "replay.jsonl")["ok"] is True
    before = _copy(root, tmp_path / "before")
    _rewrite_tick(before / probe["artifact_dir"] / "replay.jsonl", 0)
    row = prefix_gate_cell(root / probe["artifact_dir"] / "replay.jsonl", before / probe["artifact_dir"] / "replay.jsonl")
    assert row["ok"] is False and row["first_hit_tick"] == 1
    free = _copy(root, tmp_path / "free")
    _rewrite_tick(free / hit_free["artifact_dir"] / "replay.jsonl", 900)
    assert prefix_gate(root, free, frozen_hit_free=frozen)["failures"] == 1


def test_prefix_gate_premise_on_real_slot_limited_and_whole_tick_replays(tmp_path: Path) -> None:
    # A non-matrix scenario (a real repair guard against an idle scripted seat)
    # has no hit, so the slot-limited treatment reproduces the whole-tick
    # parent entirely, apart from identity.
    data_root = prepare_data_root(tmp_path / "env", ["e2_repair_guard", "e2_sniper"])
    idle = AgentAction(ActionKindV2.READ, operand=0)
    replays = {
        ruleset: run_hosted_match(data_root, tmp_path / ruleset, ruleset_id=matrix.condition(ruleset).ruleset_id,
                                  seat_names={"A": "e2_repair_guard", "B": "e2_sniper"}, scripted_seat="B",
                                  brain=lambda _c, _o: idle, seed=42, ticks=300)
        for ruleset in ("C-E2", "T-E3")
    }
    row = prefix_gate_cell(replays["C-E2"], replays["T-E3"])
    assert (row["hit_free"], row["ok"], row["problems"]) == (True, True, [])


# ---------------------------------------------------------------------------
# Treatment-side gates and the frozen analysis, on control-as-treatment data
# ---------------------------------------------------------------------------


def test_treatment_gates_stop_a_whole_tick_corpus_presented_as_a_treatment(control: dict[str, Any]) -> None:
    frozen = a.populations(control["runs"])
    report = run_e3.treatment_gate_report(
        "T-E3", control_roots=control["roots"], treatment_roots=control["roots"], rows=control["rows"], frozen=frozen)
    # The prefix gate passes (identical replays), but whole-tick replays fail
    # the lambda = 1 manipulation checks, and the control's real guard
    # captures are a D9 stop for T-E3.
    assert all(f["prefix"]["status"] == "PASS" for f in report["fields"].values())
    assert report["fields"]["F1"]["manipulation"]["violations"]["exclusive_tick"] > 0
    assert report["d9_stop"] is True and report["status"] == "FAIL"
    companion = run_e3.treatment_gate_report(
        "T-E3K1", control_roots=control["roots"], treatment_roots=control["roots"], rows=control["rows"], frozen=frozen)
    assert companion["d9_stop"] is False and companion["d9_completion_count"] == report["d9_completion_count"]


def test_frozen_analysis_runs_both_arms(control: dict[str, Any]) -> None:
    from tools.research.v6.e3 import populations

    prereg = load_preregistration()
    record = populations.build_record(freeze_id="v6-e3-freeze-v1-x", preregistration_sha256="x", prereg=prereg,
                                      arms={"primary": control["runs"], "companion": control["runs"]})
    runs = {c: control["runs"] for c in ("C-E2", "T-E3", "C-RS", "T-E3K1")}
    out = run_e3.analysis_report(runs=runs, frozen=record, prereg=prereg)
    assert out["primary"]["D9"]["status"] == a.STOP
    assert out["companion"]["D9"]["status"] == "REPORTED_TO_PRIMARY"
    assert out["companion"]["D9"]["companion_completions"] == out["primary"]["D9"]["primary_completions"]
    assert set(out["primary"]["pm4"]["fields"]) == set(matrix.FIELD_IDS)
    assert all(r["sdi_control"] == r["sdi_treatment"] for r in out["primary"]["pm4"]["fields"]["F1"])
    assert out["interpretation"] == prereg["interpretation"]
