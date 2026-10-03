"""V6 E8: the analysis freeze identity, v1 (phase I8-5).

The record pins the complete instrument at the tooling commit: the
structural matrix, family and pre-registration freeze identities; the
analyzer, gate, re-derivation, telemetry, trace, runner and seed tooling;
every reused E2 to E6 file; every E8 qualification test file; the engine
source the family was qualified on; and the conventions I8-5 fixed. It
recomputes from the live checkout, every pinned file equals its content at
the tooling commit, and any drift fails closed. The seed and control blocks
sit outside the identity and are filled only by later, separately authorized
steps; these tests accept either their PENDING state or a well-formed block,
so that they stay true after I8-6 and Q8.
"""

from __future__ import annotations

import copy
import hashlib
import json
import subprocess
from pathlib import Path

import pytest

from tools.research.v6.e8 import analysis_freeze, family_freeze, matrix, seed_protocol

ROOT = Path(__file__).resolve().parents[2]
IDENTITY = "v6-e8-analysis-v1-52e09e5fb422"
TOOLING_COMMIT = "6d3930a"


def _stored() -> dict:
    return json.loads(analysis_freeze.FREEZE_RECORD_PATH.read_text(encoding="utf-8"))


def _git_digest(commit: str, path: str) -> str:
    content = subprocess.run(["git", "show", f"{commit}:{path}"], cwd=ROOT, capture_output=True, check=True).stdout
    return hashlib.sha256(content.replace(b"\r\n", b"\n")).hexdigest()


def test_the_freeze_loads_and_its_identity_is_pinned() -> None:
    record = analysis_freeze.load_freeze()
    assert record["freeze_id"] == IDENTITY == analysis_freeze.freeze_id(record["identity"])
    assert record["identity"]["tooling_source_sha"] == TOOLING_COMMIT
    assert record["schema"] == "bytefray.v6.e8.analysis_freeze"


def test_it_carries_every_earlier_identity() -> None:
    identity = _stored()["identity"]
    assert identity["structural_matrix_id"] == "v6-e8-matrix-v1-e0d322b597da" == matrix.matrix_id()
    assert identity["structural_digest"] == matrix.STRUCTURAL_DIGEST and identity["matches_total"] == 16_896
    assert identity["family_freeze"]["identity"] == "v6-e8-family-v1-981fc8b12beb"
    assert identity["preregistration_freeze"]["identity"] == "v6-e8-prereg-v4-0166cdc0b37a"
    assert identity["engine_source"] == dict(family_freeze.load_freeze()["body"]["engine_source"])
    assert identity["parent_freeze"]["commits"] == ["3f3f709", "2cfd4e8"]


def test_every_pinned_file_equals_its_content_at_the_tooling_commit() -> None:
    identity = _stored()["identity"]
    assert set(identity["tooling_sha256"]) == set(analysis_freeze.E8_FILES)
    assert set(identity["reused_sha256"]) == set(analysis_freeze.REUSED_FILES)
    assert set(identity["qualification_sha256"]) == set(analysis_freeze.QUALIFICATION_FILES)
    for key in ("tooling_sha256", "reused_sha256", "qualification_sha256"):
        for path, digest in identity[key].items():
            assert _git_digest(identity["tooling_source_sha"], path) == digest, path


def test_the_instrument_covers_the_runner_gates_analyzer_and_seed_tooling() -> None:
    tooling = set(_stored()["identity"]["tooling_sha256"])
    for name in ("run_e8.py", "gates.py", "analyze_e8.py", "seed_protocol.py", "rederive.py", "telemetry.py", "traces.py",
                 "payoff.py", "decision.py", "family_freeze.json", "preregistration.json"):
        assert f"tools/research/v6/e8/{name}" in tooling, name
    assert _stored()["identity"]["versions"] == analysis_freeze.versions()


def test_the_conventions_are_recorded_inside_the_identity() -> None:
    conventions = _stored()["identity"]["conventions"]
    assert set(conventions) == set(analysis_freeze.CONVENTIONS)
    assert "immediately before every traced re-execution" in conventions["pre_match_gate"]
    assert "before any cell runs" in conventions["engine_source"]


def test_the_seed_and_control_blocks_are_pending_or_well_formed() -> None:
    record = _stored()
    seed_block, control_block = record["seed_commitment"], record["control_qualification"]
    analysis_freeze.check_seed_block(seed_block)
    analysis_freeze.check_control_block(control_block)
    if seed_block != analysis_freeze.PENDING:
        assert set(seed_block) == analysis_freeze.SEED_BLOCK_KEYS
        assert seed_protocol.execution_identity(matrix.STRUCTURAL_DIGEST, seed_block["seed_commitment"]) == \
            seed_block["execution_matrix_identity"]


def test_a_seed_block_with_anything_more_or_a_wrong_identity_is_refused() -> None:
    commitment = "c" * 64
    good = dict(seed_protocol.committed_record(commitment, matrix.STRUCTURAL_DIGEST, "t", "0" * 40))
    analysis_freeze.check_seed_block(good)
    with pytest.raises(analysis_freeze.AnalysisFreezeError):
        analysis_freeze.check_seed_block({**good, "seeds": [1, 2]})
    with pytest.raises(analysis_freeze.AnalysisFreezeError):
        analysis_freeze.check_seed_block({**good, "execution_matrix_identity": "v6-e8-exec-v1-000000000000"})
    with pytest.raises(analysis_freeze.AnalysisFreezeError):
        analysis_freeze.check_control_block({"status": "PASS"})


def test_a_tampered_record_fails_to_load(tmp_path: Path) -> None:
    changed = copy.deepcopy(_stored())
    changed["identity"]["conventions"]["P8-11"] = "a subset"
    path = tmp_path / "analysis_freeze.json"
    path.write_text(json.dumps(changed), encoding="utf-8")
    with pytest.raises(analysis_freeze.AnalysisFreezeError, match="does not recompute"):
        analysis_freeze.load_freeze(path)


def test_a_re_signed_tampered_record_still_fails_to_load(tmp_path: Path) -> None:
    changed = copy.deepcopy(_stored())
    changed["identity"]["tooling_sha256"]["tools/research/v6/e8/gates.py"] = "0" * 64
    changed["freeze_digest"] = analysis_freeze.freeze_digest(changed["identity"])
    changed["freeze_id"] = analysis_freeze.freeze_id(changed["identity"])
    path = tmp_path / "analysis_freeze.json"
    path.write_text(json.dumps(changed), encoding="utf-8")
    with pytest.raises(analysis_freeze.AnalysisFreezeError, match="gates.py"):
        analysis_freeze.load_freeze(path)


def test_a_record_naming_another_engine_than_the_familys_fails(tmp_path: Path) -> None:
    changed = copy.deepcopy(_stored())
    changed["identity"]["engine_source"] = {**changed["identity"]["engine_source"], "sha256": "0" * 64}
    changed["freeze_digest"] = analysis_freeze.freeze_digest(changed["identity"])
    changed["freeze_id"] = analysis_freeze.freeze_id(changed["identity"])
    path = tmp_path / "analysis_freeze.json"
    path.write_text(json.dumps(changed), encoding="utf-8")
    with pytest.raises(analysis_freeze.AnalysisFreezeError, match="engine"):
        analysis_freeze.load_freeze(path)


def test_a_missing_record_fails_closed(tmp_path: Path) -> None:
    with pytest.raises(analysis_freeze.AnalysisFreezeError, match="freeze the analysis first"):
        analysis_freeze.load_freeze(tmp_path / "absent.json")
