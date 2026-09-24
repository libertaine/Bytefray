"""The E4 analysis freeze identity (design review Sec Q, Sec R step 6).

The matrix identity and the analysis identity are kept apart. The freeze pins
the pre-registration, the contest classes, the E4 analyzer, capture analyzer
v2 (against E2 freeze v2) and E3 action/parity analyzer v1 and every other
reused E3 file (against E3 freeze v1), every tooling file, the tooling commit,
the engine tree, the E4 parent freeze and the E3 parent provenance, and fails
closed on any drift.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.research.v6.e3 import analysis_freeze as e3_freeze
from tools.research.v6.e4 import analysis_freeze, matrix, run_e4
from tools.research.v6.e4.preregistration import preregistration_digest


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
    assert identity["matrix_id"] == matrix.matrix_id() and identity["matches_total"] == 15232
    assert identity["preregistration_sha256"] == preregistration_digest()
    assert identity["contest_classes_sha256"] == matrix.contest_classes.CONTEST_CLASSES_SHA256
    e3_identity = json.loads((analysis_freeze.REPO_ROOT / analysis_freeze.E3_FREEZE_FILE).read_text(encoding="utf-8"))
    e3_pins = e3_identity["identity"]
    assert identity["capture_analyzer_sha256"] == e3_pins["capture_analyzer_sha256"]
    assert identity["action_parity_sha256"] == e3_pins["action_parity_sha256"]
    assert (identity["capture_analyzer_version"], identity["action_parity_version"]) == (2, 1)
    assert identity["reused_e3_freeze_id"] == "v6-e3-freeze-v1-506811e78ad8"
    assert identity["capture_analyzer_e2_freeze_id"] == "v6-e2-freeze-v2-db6458596d82"
    assert set(identity["tooling_sha256"]) == set(analysis_freeze.TOOLING_FILES)
    for path in analysis_freeze.REUSED_E3_FILES:
        assert identity["tooling_sha256"][path] == e3_pins["tooling_sha256"][path], path
    assert identity["parent_freeze"] == {"commit": "b144e1d", "matches": 96,
                                         "path": "engine/tests/test_v6_e4_parent_byte_identity.py"}
    assert identity["historical_parent"]["freeze_id"] == "v6-e3-freeze-v1-506811e78ad8"
    assert identity["historical_parent"]["generation"]["engine_tree"] == "67b73c9ae7d40209ef68e9512a58c5adfef0ac2f"


def test_the_freeze_identity_is_not_the_matrix_identity() -> None:
    record = analysis_freeze.build_freeze_record(_identity())
    assert record["freeze_id"].startswith("v6-e4-freeze-v1-")
    assert record["freeze_id"] != matrix.matrix_id() and record["identity"]["matrix_id"] == matrix.matrix_id()
    assert record["control_qualification"] == {"status": "PENDING"}


def test_a_record_loads_and_any_tooling_drift_fails_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = _record(tmp_path)
    assert analysis_freeze.load_freeze(path)["freeze_id"].startswith("v6-e4-freeze-v1-")
    real = analysis_freeze.file_sha256

    def drifted(relative: str, *args: object) -> str:
        return "0" * 64 if relative == analysis_freeze.ANALYSIS_FILE else real(relative)

    monkeypatch.setattr(analysis_freeze, "file_sha256", drifted)
    with pytest.raises(analysis_freeze.AnalysisFreezeError, match="analyze_e4|e4_analysis_sha256"):
        analysis_freeze.load_freeze(path)


def test_a_reused_e3_file_that_drifts_fails_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    real = analysis_freeze.file_sha256

    def drifted(relative: str, *args: object) -> str:
        return "0" * 64 if relative == analysis_freeze.ACTION_PARITY_FILE else real(relative)

    monkeypatch.setattr(analysis_freeze, "file_sha256", drifted)
    with pytest.raises(analysis_freeze.AnalysisFreezeError, match="reused E3 files"):
        analysis_freeze.check_reused_unchanged()


def test_capture_analyzer_v2_is_checked_against_e2s_pin(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def changed() -> None:
        raise e3_freeze.AnalysisFreezeError("capture analyzer changed")

    monkeypatch.setattr(e3_freeze, "check_capture_analyzer_unchanged", changed)
    with pytest.raises(analysis_freeze.AnalysisFreezeError, match="capture analyzer"):
        analysis_freeze.check_reused_unchanged()


def test_a_tampered_record_fails_closed(tmp_path: Path) -> None:
    path = _record(tmp_path)
    record = json.loads(path.read_text(encoding="utf-8"))
    record["identity"]["preregistration_sha256"] = "0" * 64
    path.write_text(json.dumps(record), encoding="utf-8")
    with pytest.raises(analysis_freeze.AnalysisFreezeError, match="digest or id"):
        analysis_freeze.load_freeze(path)


def test_execution_needs_the_frozen_engine_tree(tmp_path: Path) -> None:
    record = analysis_freeze.build_freeze_record({**_identity(), "match_generation_tree": "0" * 40})
    with pytest.raises(analysis_freeze.AnalysisFreezeError, match="engine/src tree"):
        analysis_freeze.verify_execution_source(record)


def test_the_unlock_needs_a_passing_control_qualification(tmp_path: Path) -> None:
    with pytest.raises(analysis_freeze.AnalysisFreezeError, match="not PASS"):
        run_e4.treatment_unlock(tmp_path, freeze_path=_record(tmp_path))
    with pytest.raises(analysis_freeze.AnalysisFreezeError, match="missing or differs"):
        run_e4.treatment_unlock(tmp_path, freeze_path=_record(tmp_path, status="PASS", records={}))


# ---------------------------------------------------------------------------
# The committed freeze
# ---------------------------------------------------------------------------

FREEZE_ID = "v6-e4-freeze-v1-101a941f5e30"
TOOLING_SOURCE_SHA = "108d08d358611c073731ae1b1020b91da8c907fb"
# engine/src of the qualified E4 implementation (107e077), unchanged since.
ENGINE_TREE = "940a27bcf8c62268eb15210cc30c28cae4d33e50"


def test_the_committed_freeze_holds() -> None:
    record = analysis_freeze.load_freeze()
    assert record["freeze_id"] == FREEZE_ID
    assert record["status"] == "frozen before any T-E4 or T-E4K1 matrix data exists"
    identity = record["identity"]
    assert (identity["tooling_source_sha"], identity["match_generation_tree"]) == (TOOLING_SOURCE_SHA, ENGINE_TREE)
    assert analysis_freeze.git_text("rev-parse", "107e077:engine/src") == ENGINE_TREE
    assert identity["matrix_id"] == "v6-e4-matrix-v1-fc29d575dd25"
