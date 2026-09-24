"""The E4 control pipeline on a real control sample (design review Sec Q, Sec R).

A two-seed C-E4 sample of every field runs through the E4 runner's own guarded
harness path into a temporary directory, then through telemetry, the parent
reproduction comparator, E3 continuity, the relabel gate, both integrity checks,
the populations and control-vs-control census, and the treatment gates -- each
with a tamper case. No treatment Ruleset runs a matrix cell here.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

import pytest

from tools.research.v6.e2.requalification import corpus_integrity as e2_corpus_integrity
from tools.research.v6.e3 import telemetry as e3_telemetry
from tools.research.v6.e3.gates import artifact_dir, index_cells, load_cells
from tools.research.v6.e4 import gates, matrix, populations, run_e4
from tools.research.v6.e4.analyze_e4 import make_field_run
from tools.research.v6.e4.preregistration import load_preregistration, preregistration_digest
from tools.research.v6.e4.telemetry import compute_telemetry, summarize

SEEDS = (1, 2)
HISTORICAL = run_e4.HISTORICAL_RUN_ROOT / matrix.HISTORICAL_MATRIX_ID
needs_corpus = pytest.mark.skipif(not (HISTORICAL / "T-E3" / "F2-P").is_dir(),
                                  reason="the preserved E3 treatment corpus is not present (git-ignored runs/)")


@pytest.fixture(scope="module")
def sample(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Any]:
    root = tmp_path_factory.mktemp("e4-sample")
    roots, rows = {}, {}
    for field in matrix.FIELDS:
        config = run_e4.experiment_config("C-E4", field.field_id, output_dir=root / field.field_id, seeds=SEEDS,
                                          workers=4)
        run_e4._run(config, "C-E4", field.field_id)
        roots[field.field_id] = root / field.field_id
        rows[field.field_id] = compute_telemetry(root / field.field_id, workers=4)
    return {"root": root, "roots": roots, "rows": rows}


def test_the_sample_ran_the_frozen_cells_and_its_telemetry_is_clean(sample: dict[str, Any]) -> None:
    counts = {f: len(index_cells(load_cells(r))) for f, r in sample["roots"].items()}
    assert counts == {"F1": 144, "F2": 36, "F2-P": 18, "F4": 40}
    orientations = {c["orientation"] for c in load_cells(sample["roots"]["F2-P"])}
    assert orientations == {"candidate_first"}
    for field_id, rows in sample["rows"].items():
        report = summarize(rows)
        assert report["clean"] and report["analyzed"] == counts[field_id], field_id
        assert report["e4_fps_identity_failures"] == report["e4_reconstruction_disagreements"] == 0


def test_parent_comparison_accepts_a_byte_identical_copy_and_catches_tampering(
    sample: dict[str, Any], tmp_path: Path
) -> None:
    source = sample["roots"]["F2"]
    rows = sample["rows"]["F2"]
    copy = tmp_path / "copy"
    shutil.copytree(source, copy)
    report = gates.compare_parent_subset(source, copy, new_rows=rows, historical_rows=rows)
    assert (report["status"], report["cells_compared"], report["mismatch_count"]) == ("PASS", 36, 0)

    cells = index_cells(load_cells(copy))
    first = artifact_dir(copy, cells[min(cells)])
    (first / "replay.jsonl").write_bytes((first / "replay.jsonl").read_bytes() + b"\n")
    second = artifact_dir(copy, cells[sorted(cells)[1]])
    result = json.loads((second / "result.json").read_text(encoding="utf-8"))
    result["winner"] = "tampered"
    (second / "result.json").write_text(json.dumps(result), encoding="utf-8")
    third = sorted(cells)[2]
    tampered_rows = json.loads(json.dumps(rows))
    tampered_rows[third]["telemetry"]["e4"]["fma"]["exact"] = "99/1"
    report = gates.compare_parent_subset(source, copy, new_rows=rows, historical_rows=tampered_rows)
    assert report["status"] == "FAIL"
    assert report["mismatch_reasons"] == {"e4_metrics": 1, "replay_bytes": 1, "result_json": 1}


@needs_corpus
def test_the_sample_reproduces_the_preserved_t_e3_cells(sample: dict[str, Any]) -> None:
    for field in matrix.FIELDS:
        keys = set(sample["rows"][field.field_id])
        historical_root = HISTORICAL / "T-E3" / field.historical_field
        historical_rows = compute_telemetry(historical_root, workers=4, keys=keys)
        report = gates.compare_parent_subset(sample["roots"][field.field_id], historical_root,
                                             new_rows=sample["rows"][field.field_id], historical_rows=historical_rows)
        assert (report["status"], report["cells_compared"]) == ("PASS", len(keys)), field.field_id
        frozen = e3_telemetry.read_rows(run_e4.frozen_e3_telemetry_file("T-E3", field.historical_field))[1]
        continuity = gates.e3_continuity(sample["rows"][field.field_id], frozen)
        assert (continuity["status"], continuity["differing"]) == ("PASS", 0), field.field_id


def test_e3_continuity_detects_a_changed_or_missing_row(sample: dict[str, Any]) -> None:
    rows = sample["rows"]["F4"]
    frozen = {key: {"key": key, "telemetry": row["telemetry"]["e3"]} for key, row in rows.items()}
    assert gates.e3_continuity(rows, frozen)["status"] == "PASS"
    changed = json.loads(json.dumps(frozen))
    key = min(changed)
    changed[key]["telemetry"]["both_alive_ticks"] += 1
    del changed[sorted(changed)[1]]
    report = gates.e3_continuity(rows, changed)
    assert (report["status"], report["differing"], report["missing"]) == ("FAIL", 1, 1)


def test_the_relabel_gate_passes_twin_mirrors_and_fails_a_changed_tick(sample: dict[str, Any], tmp_path: Path) -> None:
    report = gates.relabel_gate(sample["roots"]["F2"])
    assert (report["status"], report["pairs"], report["failures"]) == ("PASS", 18, 0)
    f4 = gates.relabel_gate(sample["roots"]["F4"])
    assert (f4["status"], f4["pairs"]) == ("PASS", 2)  # the jam mirror, two seeds
    copy = tmp_path / "f2"
    shutil.copytree(sample["roots"]["F2"], copy)
    cell = next(c for c in load_cells(copy) if c["orientation"] == "opponent_first")
    replay = artifact_dir(copy, cell) / "replay.jsonl"
    lines = replay.read_text(encoding="utf-8").splitlines(keepends=True)
    index = next(i for i, line in enumerate(lines) if json.loads(line).get("record_type") == "tick")
    record = json.loads(lines[index])
    record["score"] = {key: value + 1 for key, value in record["score"].items()}
    lines[index] = json.dumps(record) + "\n"
    replay.write_text("".join(lines), encoding="utf-8")
    report = gates.relabel_gate(copy)
    assert (report["status"], report["failures"]) == ("FAIL", 1)
    with pytest.raises(gates.RelabelGateError, match="STOP"):
        gates.require_relabel({"F2": report})


def test_e4_integrity_is_e2s_check_with_the_fields_own_orientations(sample: dict[str, Any]) -> None:
    fingerprints = {name: matrix.AGENT_FINGERPRINTS[name] for name in matrix.F1.agents}
    e4 = gates.corpus_integrity(sample["roots"]["F1"], ruleset_id=matrix.condition("C-E4").ruleset_id,
                                pairs=matrix.F1.pairs, seeds=SEEDS, orientations=gates.field_orientations("F1"),
                                provenance={}, fingerprints=fingerprints)
    e2 = e2_corpus_integrity(sample["roots"]["F1"], ruleset_id=matrix.condition("C-E4").ruleset_id,
                             pairs=matrix.F1.pairs, seeds=SEEDS, provenance={}, fingerprints=fingerprints)
    assert e4 == e2 and e4["status"] == "PASS"
    mirrors = {name: matrix.AGENT_FINGERPRINTS[name] for name in matrix.F2P.agents}
    one = gates.corpus_integrity(sample["roots"]["F2-P"], ruleset_id=matrix.condition("C-E4").ruleset_id,
                                 pairs=matrix.F2P.pairs, seeds=SEEDS, orientations=gates.field_orientations("F2-P"),
                                 provenance={}, fingerprints=mirrors)
    assert one["status"] == "PASS" and one["expected_cells"] == 18
    # E2's frozen check always expects both orientations, so it would misreport F2-P.
    two = e2_corpus_integrity(sample["roots"]["F2-P"], ruleset_id=matrix.condition("C-E4").ruleset_id,
                              pairs=matrix.F2P.pairs, seeds=SEEDS, provenance={}, fingerprints=mirrors)
    assert two["status"] == "FAIL" and "18 missing cells" in two["problems"][0]


def _runs(sample: dict[str, Any]) -> dict[str, Any]:
    return {f: make_field_run("C-E4", f, load_cells(sample["roots"][f]), sample["rows"][f]) for f in matrix.FIELD_IDS}


def test_populations_and_the_control_census_on_the_sample(sample: dict[str, Any]) -> None:
    runs = _runs(sample)
    # Structural check: both arms fed the same C-E4 sample.
    record = populations.build_record(freeze_id="test-freeze", preregistration_sha256=preregistration_digest(),
                                      prereg=load_preregistration(), arms={"primary": runs, "companion": runs})
    for arm in ("primary", "companion"):
        body = record["arms"][arm]
        assert body["control_census"]["status"] == "PASS" and not body["control_census"]["non_identity_units"]
        assert body["counts"]["units"] == 72 + 9 + 9 + 19
        assert set(body["p_par"]) <= {name for name in body["units"] if name.split("|")[0] in ("F1", "F2")}
        assert list(body["mirror_seed_units"]["F2"]) == [f"F2|{a}|{a}_twin" for a in sorted(matrix.E4_AGENTS)]
    statuses = record["arms"]["primary"]["control_vs_control_hypotheses"]["interpretation_inputs"]
    assert statuses["D9-PRIME"] == "HOLDS"
    for name in ("E4-H1", "E4-H2"):
        assert statuses[name] in ("REFUTED", "NOT_EVALUABLE")
    assert record["p_stale"]["source"]["sha256"] == populations.E3_POPULATIONS_SHA256
    populations.require_control_census(record)
    populations.require_recomputes(record, json.loads(json.dumps(record)))
    changed = json.loads(json.dumps(record))
    changed["arms"]["primary"]["p_par"] = []
    with pytest.raises(populations.PopulationsError, match="recompute"):
        populations.require_recomputes(changed, record)


def test_treatment_gates_stop_a_forward_corpus_presented_as_the_treatment(sample: dict[str, Any]) -> None:
    report = run_e4.treatment_gate_report("T-E4", treatment_roots=sample["roots"], rows=sample["rows"])
    assert report["status"] == "FAIL"
    f1 = report["fields"]["F1"]["manipulation"]
    # Forward order: the second mover owns the final chunk, and a jammed second mover can fall to 4 actions.
    assert f1["violations"].get("final_chunk_owner", 0) > 0
    assert report["fields"]["F4"]["manipulation"]["violations"].get("g4_prime_violation", 0) > 0
    assert report["fields"]["F2"]["relabel"]["status"] == "PASS"


def test_the_d9_prime_stop_raises_only_for_the_primary_treatment() -> None:
    completion = [{"cell": "x", "victim_name": "e2_repair_guard", "tick": 5}]
    with pytest.raises(gates.D9PrimeStopError, match="G.5'"):
        gates.require_d9_prime("T-E4", completion)
    gates.require_d9_prime("T-E4K1", completion)
    gates.require_d9_prime("T-E4", [])
