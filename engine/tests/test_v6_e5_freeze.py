"""The E5 analysis freeze identity (review Sec O step 7; Revision 1).

The matrix identity and the analysis identity are kept apart. The freeze pins
the pre-registration, the E5 analyzer and cell metrics, every reused E3/E4
file (against E4 analysis freeze v1's pins, which in turn check E3's and
E2's), every tooling file, the tooling commit, the engine tree, the E5 parent
freeze and the historical E4 control provenance, and fails closed on any
drift.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.research.v6.e4 import analysis_freeze as e4_freeze
from tools.research.v6.e5 import analysis_freeze, matrix, populations, run_e5
from tools.research.v6.e5.preregistration import preregistration_digest


def _identity() -> dict:
    return analysis_freeze.identity_inputs(
        tooling_source_sha=analysis_freeze.git_text("rev-parse", "HEAD"),
        match_generation_tree=analysis_freeze.git_text("rev-parse", "HEAD:engine/src"),
    )


def _record(tmp_path: Path, **qualification: object) -> Path:
    path = tmp_path / "analysis_freeze.json"
    record = analysis_freeze.build_freeze_record(_identity(), dict(qualification) or None)
    path.write_text(json.dumps(record, indent=2, sort_keys=True), encoding="utf-8")
    return path


def test_the_identity_pins_the_whole_instrument() -> None:
    identity = _identity()
    assert identity["matrix_id"] == matrix.matrix_id() and identity["matches_total"] == 7168
    assert identity["preregistration_sha256"] == preregistration_digest()
    assert identity["reused_e4_freeze_id"] == "v6-e4-freeze-v1-101a941f5e30"
    e4_pins = analysis_freeze.e4_freeze_record()["identity"]["tooling_sha256"]
    assert set(identity["tooling_sha256"]) == set(analysis_freeze.TOOLING_FILES)
    for path in analysis_freeze.REUSED_FILES:
        assert identity["tooling_sha256"][path] == e4_pins[path], path
    assert identity["parent_freeze"] == {"commit": "8f6717d", "matches": 96,
                                         "path": "engine/tests/test_v6_e5_parent_byte_identity.py"}
    assert identity["historical_parent"]["freeze_id"] == "v6-e4-freeze-v1-101a941f5e30"
    assert identity["historical_parent"]["generation"]["engine_tree"] == "940a27bcf8c62268eb15210cc30c28cae4d33e50"


def test_the_freeze_identity_is_not_the_matrix_identity() -> None:
    record = analysis_freeze.build_freeze_record(_identity())
    assert record["freeze_id"].startswith("v6-e5-freeze-v1-")
    assert record["freeze_id"] != matrix.matrix_id() and record["identity"]["matrix_id"] == matrix.matrix_id()
    assert record["control_qualification"] == {"status": "PENDING"}


def test_a_record_loads_and_any_tooling_drift_fails_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = _record(tmp_path)
    assert analysis_freeze.load_freeze(path)["freeze_id"].startswith("v6-e5-freeze-v1-")
    real = analysis_freeze.file_sha256

    def drifted(relative: str, *args: object) -> str:
        return "0" * 64 if relative == analysis_freeze.ANALYSIS_FILE else real(relative)

    monkeypatch.setattr(analysis_freeze, "file_sha256", drifted)
    with pytest.raises(analysis_freeze.AnalysisFreezeError, match="analyze_e5|e5_analysis_sha256"):
        analysis_freeze.load_freeze(path)


def test_a_reused_file_that_drifts_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    real = analysis_freeze.file_sha256

    def drifted(relative: str, *args: object) -> str:
        return "0" * 64 if relative == "tools/research/v6/e4/cell_metrics.py" else real(relative)

    monkeypatch.setattr(analysis_freeze, "file_sha256", drifted)
    with pytest.raises(analysis_freeze.AnalysisFreezeError, match="reused files"):
        analysis_freeze.check_reused_unchanged()


def test_e4s_own_reuse_check_runs_first(monkeypatch: pytest.MonkeyPatch) -> None:
    def changed() -> None:
        raise e4_freeze.AnalysisFreezeError("reused E3 files differ")

    monkeypatch.setattr(e4_freeze, "check_reused_unchanged", changed)
    with pytest.raises(analysis_freeze.AnalysisFreezeError, match="reused E3 files"):
        analysis_freeze.check_reused_unchanged()


def test_a_tampered_record_fails_closed(tmp_path: Path) -> None:
    path = _record(tmp_path)
    record = json.loads(path.read_text(encoding="utf-8"))
    record["identity"]["preregistration_sha256"] = "0" * 64
    path.write_text(json.dumps(record), encoding="utf-8")
    with pytest.raises(analysis_freeze.AnalysisFreezeError, match="digest or id"):
        analysis_freeze.load_freeze(path)


def test_execution_needs_the_frozen_engine_tree() -> None:
    record = analysis_freeze.build_freeze_record({**_identity(), "match_generation_tree": "0" * 40})
    with pytest.raises(analysis_freeze.AnalysisFreezeError, match="engine/src tree"):
        analysis_freeze.verify_execution_source(record)


def test_the_unlock_needs_a_passing_control_qualification(tmp_path: Path) -> None:
    with pytest.raises(analysis_freeze.AnalysisFreezeError, match="not PASS"):
        run_e5.treatment_unlock(tmp_path, freeze_path=_record(tmp_path))
    with pytest.raises(analysis_freeze.AnalysisFreezeError, match="missing or differs"):
        run_e5.treatment_unlock(tmp_path, freeze_path=_record(tmp_path, status="PASS", records={}))


# ---------------------------------------------------------------------------
# The committed freeze
# ---------------------------------------------------------------------------

FREEZE_ID = "v6-e5-freeze-v1-5ba12be258c8"
TOOLING_SOURCE_SHA = "76c1d625c83c39cf353e28db37ca2d756bd53d55"
# engine/src of the E5 Ruleset implementation (e0a1b02), unchanged since.
ENGINE_TREE = "da3f9ac2b5268cbe5bbcfa4701ea076554598d35"


def test_the_committed_freeze_holds() -> None:
    record = analysis_freeze.load_freeze()
    assert record["freeze_id"] == FREEZE_ID
    assert record["status"] == "frozen before any T-E5 or T-E5K1 matrix data exists"
    identity = record["identity"]
    assert (identity["tooling_source_sha"], identity["match_generation_tree"]) == (TOOLING_SOURCE_SHA, ENGINE_TREE)
    assert analysis_freeze.git_text("rev-parse", "e0a1b02:engine/src") == ENGINE_TREE
    assert identity["matrix_id"] == "v6-e5-matrix-v1-ef7fa327ea81"


# The commit both controls were generated at (clean tree), after the freeze commit.
CONTROL_SOURCE_SHA = "a6d11167b1ae957ff382b35a7ebef947c234ebb8"
POPULATIONS_SHA256 = "1cf96a2e48b4c4bcc95d011b2289963a24fed92a555d5ad927de636b718e1737"
PRIMARY_SWEEP_BACKED = [
    "F1|e2_disrupt_guard|e2_min_guard|A", "F1|e2_disrupt_guard|e2_sniper|A", "F1|e2_guarded_painter|e2_min_guard|A",
    "F1|e2_guarded_painter|e2_sniper|A", "F1|e2_min_guard|e2_disrupt_guard|B", "F1|e2_min_guard|e2_guarded_painter|B",
    "F1|e2_min_guard|e2_repair_guard|B", "F1|e2_min_guard|e2_sniper|A", "F1|e2_min_guard|e2_spread_defender|B",
    "F1|e2_sniper|e2_disrupt_guard|B", "F1|e2_sniper|e2_guarded_painter|B", "F1|e2_sniper|e2_min_guard|B",
    "F1|e2_sniper|e2_repair_guard|B", "F1|e2_sniper|e2_spread_defender|B", "F1|e2_spread_defender|e2_repair_guard|B",
    "F1|e2_spread_sniper|e2_repair_guard|B", "F2|e2_min_guard|e2_min_guard_twin|AB",
]
MIXED = ["F1|e2_spread_defender|e2_min_guard|A", "F1|e2_spread_defender|e2_sniper|A"]


def test_the_committed_control_qualification_pins_the_frozen_populations() -> None:
    record = analysis_freeze.load_freeze()
    qualification = record["control_qualification"]
    assert qualification["status"] == "PASS"
    assert set(qualification["records"]) == set(run_e5.CONTROL_RECORDS)
    # Both controls: every field, generated after the freeze commit with a clean tree.
    assert qualification["controls"] == {condition: {"generated_at": [[CONTROL_SOURCE_SHA, False, FREEZE_ID]],
                                                     "cells": 1792} for condition in matrix.CONTROL_CONDITIONS}
    assert analysis_freeze.git_text("rev-parse", f"{CONTROL_SOURCE_SHA}:engine/src") == ENGINE_TREE
    assert qualification["populations"]["sha256"] == POPULATIONS_SHA256
    frozen = populations.load_record(populations.POPULATIONS_PATH, freeze_id=FREEZE_ID,
                                     expected_sha256=POPULATIONS_SHA256)
    populations.require_ready(frozen)
    primary, companion = frozen["arms"]["primary"], frozen["arms"]["companion"]
    assert primary["counts"] == {"p_base": 34, "SWEEP-BACKED": 17, "ANCHOR-ONLY": 15, "MIXED-INFERENCE": 2}
    assert companion["counts"] == {"p_base": 32, "SWEEP-BACKED": 15, "ANCHOR-ONLY": 15, "MIXED-INFERENCE": 2}
    assert sorted(n for n, c in primary["contest_classes"].items() if c == "SWEEP-BACKED") == PRIMARY_SWEEP_BACKED
    assert sorted(n for n, c in primary["contest_classes"].items() if c == "MIXED-INFERENCE") == MIXED
    assert frozen["min_sweep_backed"] == {"required": 6, "primary_arm": 17, "status": "PASS"}
    assert (frozen["p_par_e5"]["count"], frozen["p_par_e5"]["e4_p_par_units"]) == (28, 32)
    # Control against itself: 100% identity classes, and the global null reads STOP.
    assert primary["control_census"]["classes"]["STAYS"] == 34
    assert frozen["control_vs_control_hypotheses"]["statuses"] == {
        "E5-H1": "REFUTED", "E5-H2": "SUPPORTED", "E5-H3": "SUPPORTED", "E5-H4": "REFUTED", "E5-H5": "REFUTED"}
    assert frozen["control_vs_control_hypotheses"]["interpretation"] == "STOP"
