"""The E3 analysis freeze identity (kept apart from the matrix identity) and the
treatment unlock chain."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from tools.research.v6.e2 import analysis_freeze as e2_freeze
from tools.research.v6.e3 import analysis_freeze as freeze
from tools.research.v6.e3 import matrix, run_e3
from tools.research.v6.e3.action_parity import E3_ACTION_PARITY_VERSION
from tools.research.v6.e3.preregistration import preregistration_digest
from tools.research.v6.experiment_harness import REPO_ROOT


def _identity() -> dict:
    return freeze.identity_inputs(tooling_source_sha="a" * 40, match_generation_tree="b" * 40)


def test_freeze_identity_carries_the_matrix_identity_and_pins_the_instrument() -> None:
    identity = _identity()
    assert identity["matrix_id"] == matrix.matrix_id() and identity["matrix_digest"] == matrix.E3_MATRIX_DIGEST
    assert identity["matches_total"] == 19456
    assert identity["preregistration_sha256"] == preregistration_digest()
    assert identity["action_parity_version"] == E3_ACTION_PARITY_VERSION
    assert identity["action_parity_sha256"] == freeze.file_sha256(freeze.ACTION_PARITY_FILE)
    # Capture analyzer v2, byte-identical to the one E2's freeze v2 pinned.
    e2 = json.loads((REPO_ROOT / freeze.E2_FREEZE_FILE).read_text(encoding="utf-8"))
    assert identity["capture_analyzer_version"] == 2
    assert identity["capture_analyzer_sha256"] == e2["identity"]["capture_analyzer_sha256"]
    assert identity["capture_analyzer_e2_freeze_id"] == e2["freeze_id"] == "v6-e2-freeze-v2-db6458596d82"
    record = freeze.build_freeze_record(identity)
    assert record["freeze_id"].startswith("v6-e3-freeze-v1-") and record["freeze_id"] != matrix.matrix_id()
    assert record["control_qualification"] == {"status": "PENDING"}


def test_every_e3_tooling_file_and_every_reused_e2_module_is_inside_the_freeze() -> None:
    e3 = REPO_ROOT / "tools" / "research" / "v6" / "e3"
    derived = {"analysis_freeze.json", "control_populations.json"}
    live = {
        path.relative_to(REPO_ROOT).as_posix()
        for path in e3.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts and path.suffix in (".py", ".json", ".yaml")
        and path.name not in derived
    }
    assert live <= set(freeze.TOOLING_FILES)
    for reused in ("tools/research/v6/experiment_harness.py", "tools/research/v6/e2/capture_analyzer.py",
                   "tools/research/v6/e2/matrix.py", "tools/research/v6/e2/requalification.py"):
        assert reused in freeze.TOOLING_FILES
    # E3 never edits the E2 instrument: E2's committed freeze v2 still holds.
    e2_freeze.load_freeze()


def test_freeze_record_fails_closed_on_any_drift(tmp_path: Path) -> None:
    path = tmp_path / "analysis_freeze.json"
    record = freeze.build_freeze_record(_identity())
    path.write_text(json.dumps(record), encoding="utf-8")
    assert freeze.load_freeze(path)["freeze_id"] == record["freeze_id"]
    for mutate in (
        lambda r: r.__setitem__("freeze_digest", "0" * 64),
        lambda r: r["identity"].__setitem__("matrix_id", "v6-e3-matrix-v1-000000000000"),
        lambda r: r["identity"].__setitem__("preregistration_sha256", "0" * 64),
        lambda r: r["identity"]["tooling_sha256"].__setitem__(freeze.ACTION_PARITY_FILE, "0" * 64),
        lambda r: r["identity"].__setitem__("capture_analyzer_sha256", "0" * 64),
    ):
        tampered = json.loads(json.dumps(record))
        mutate(tampered)
        if tampered["freeze_digest"] != "0" * 64:
            tampered = freeze.build_freeze_record(tampered["identity"])
        path.write_text(json.dumps(tampered), encoding="utf-8")
        with pytest.raises(freeze.AnalysisFreezeError):
            freeze.load_freeze(path)


def test_a_changed_capture_analyzer_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    freeze.check_capture_analyzer_unchanged()
    monkeypatch.setattr(freeze, "file_sha256", lambda _path, repo_root=REPO_ROOT: "0" * 64)
    with pytest.raises(freeze.AnalysisFreezeError, match="capture analyzer"):
        freeze.check_capture_analyzer_unchanged()


def test_treatment_unlock_needs_a_committed_freeze_and_a_passing_control_qualification(tmp_path: Path) -> None:
    with pytest.raises(freeze.AnalysisFreezeError, match="No E3 analysis freeze"):
        run_e3.treatment_unlock(tmp_path, freeze_path=tmp_path / "missing.json")
    path = tmp_path / "analysis_freeze.json"
    path.write_text(json.dumps(freeze.build_freeze_record(_identity())), encoding="utf-8")
    with pytest.raises(freeze.AnalysisFreezeError, match="control qualification"):
        run_e3.treatment_unlock(tmp_path, freeze_path=path)
    qualified = freeze.build_freeze_record(_identity(), {"status": "PASS", "records": {}, "populations": {}})
    path.write_text(json.dumps(qualified), encoding="utf-8")
    with pytest.raises(freeze.AnalysisFreezeError, match="missing or differs"):
        run_e3.treatment_unlock(tmp_path, freeze_path=path)


def test_execution_source_check_needs_a_clean_tree_and_the_frozen_engine(monkeypatch: pytest.MonkeyPatch) -> None:
    if not (REPO_ROOT / ".git").exists():
        pytest.skip("not a git checkout")
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, capture_output=True, text=True,
                          check=True).stdout.strip()
    record = freeze.build_freeze_record(freeze.identity_inputs(tooling_source_sha=head, match_generation_tree="0" * 40))
    with pytest.raises(freeze.AnalysisFreezeError, match="engine/src tree"):
        freeze.verify_execution_source(record)


FROZEN_ID = "v6-e3-freeze-v1-506811e78ad8"
TOOLING_SOURCE_SHA = "d1f69b98c6721e08d7d3eba6bc7989c9de07a4dd"
# engine/src of 75ed578, the qualified E3 implementation.
MATCH_GENERATION_TREE = "67b73c9ae7d40209ef68e9512a58c5adfef0ac2f"


def test_committed_freeze_v1_holds_against_the_live_tooling() -> None:
    record = freeze.load_freeze()
    identity = record["identity"]
    assert record["freeze_id"] == FROZEN_ID and record["freeze_id"] != matrix.matrix_id()
    assert identity["matrix_id"] == "v6-e3-matrix-v1-634132ec3c15"
    assert identity["tooling_source_sha"] == TOOLING_SOURCE_SHA
    assert identity["match_generation_tree"] == MATCH_GENERATION_TREE
    if not (REPO_ROOT / ".git").exists():
        pytest.skip("not a git checkout")
    # Every tooling file is byte-identical to its content at the tooling commit.
    for path, digest in identity["tooling_sha256"].items():
        committed = subprocess.run(["git", "show", f"{TOOLING_SOURCE_SHA}:{path}"], cwd=REPO_ROOT,
                                   capture_output=True, check=True).stdout
        assert freeze._sha256(committed) == digest, path
    tree = subprocess.run(["git", "rev-parse", f"{TOOLING_SOURCE_SHA}:engine/src"], cwd=REPO_ROOT,
                          capture_output=True, text=True, check=True).stdout.strip()
    assert tree == MATCH_GENERATION_TREE


def test_committed_control_qualification_pins_the_frozen_populations() -> None:
    from tools.research.v6.e3 import populations

    record = freeze.load_freeze()
    qualification = record["control_qualification"]
    assert qualification["status"] == "PASS"
    assert set(qualification["records"]) == set(run_e3.CONTROL_RECORDS)
    frozen = populations.load_record(populations.POPULATIONS_PATH, freeze_id=FROZEN_ID,
                                     expected_sha256=qualification["populations"]["sha256"])
    primary = frozen["arms"]["primary"]
    counts = {f: {k: len(v) for k, v in keys.items()} for f, keys in primary["populations"].items()}
    # Review Sec J: the stalemate population reproduces 610 F1 + 64 F2; 64 F2 cells are hit-free.
    assert (counts["F1"]["stalemate"], counts["F2"]["stalemate"], counts["F2"]["hit_free"]) == (610, 64, 64)
    assert counts["F1"]["exposed"] == 2880 and counts["F4"]["exposed"] == 704
    assert primary["baseline"]["D2_registered_units_reproduced"] is True
    # The companion control (K = 1) has no recovery, so no stalemate.
    assert all(len(keys["stalemate"]) == 0 for keys in frozen["arms"]["companion"]["populations"].values())
