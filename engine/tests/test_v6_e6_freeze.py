"""V6 E6: the committed analysis freeze record and the runner steps that need it.

Implementation plan Sec 2 (I-6) and Sec 8-9; pre-registration Sec 9-11.
The record must load against the live checkout, and name every E6 tooling
file. Its seed block is PENDING, or exactly the four permitted facts. Every
runner step that needs the record must refuse to run out of order. The I-7
path is exercised only on a temporary copy, with ``seeds.generate``
replaced by a fixed test list: no real seed is ever drawn here.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

import pytest

from tools.research.v6.e6 import analysis_freeze, matrix, run_e6, seeds
from tools.research.v6.e6.analysis_freeze import FREEZE_RECORD_PATH, PENDING
from tools.research.v6.experiment_harness import REPO_ROOT

E6_DIR = REPO_ROOT / "tools" / "research" / "v6" / "e6"
TEST_SEEDS = [(7919 * k * k + 104729 * k + 13) % seeds.SEED_BOUND for k in range(1, 33)]


def _record() -> dict[str, Any]:
    return json.loads(FREEZE_RECORD_PATH.read_text(encoding="utf-8"))


def test_the_record_loads_against_the_live_checkout() -> None:
    record = analysis_freeze.load_freeze()
    identity = record["identity"]
    assert record["freeze_id"] == analysis_freeze.freeze_id(identity)
    assert record["freeze_id"].startswith("v6-e6-freeze-v1-")
    assert identity["structural_matrix_id"] == matrix.matrix_id()
    assert identity["structural_digest"] == matrix.STRUCTURAL_DIGEST
    assert identity["matches_total"] == 11_520
    assert identity["parent_freeze"] == matrix.PARENT_FREEZE


def test_the_record_names_every_e6_tooling_file() -> None:
    listed = set(analysis_freeze.E6_FILES)
    on_disk = {f"tools/research/v6/e6/{path.name}" for path in E6_DIR.glob("*.py")}
    assert on_disk <= listed
    assert {"tools/research/v6/e6/preregistration.json", "tools/research/v6/e6/family_fingerprints.json"} <= listed
    assert "tools/research/v6/e6/analysis_freeze.json" not in listed  # the record is never its own input


def test_every_pinned_file_equals_its_content_at_the_tooling_commit() -> None:
    identity = _record()["identity"]
    for path, digest in identity["tooling_sha256"].items():
        committed = subprocess.check_output(["git", "show", f"{identity['tooling_source_sha']}:{path}"],
                                            cwd=REPO_ROOT).replace(b"\r\n", b"\n")
        assert hashlib.sha256(committed).hexdigest() == digest, path


def test_the_seed_block_is_pending_or_exactly_the_permitted_facts() -> None:
    record = _record()
    block = record["seed_commitment"]
    analysis_freeze.check_seed_block(block)
    assert block == PENDING or set(block) == analysis_freeze.SEED_BLOCK_KEYS
    with pytest.raises(analysis_freeze.AnalysisFreezeError):
        analysis_freeze.check_seed_block({**_block(), "seeds": TEST_SEEDS})
    with pytest.raises(analysis_freeze.AnalysisFreezeError):
        analysis_freeze.check_seed_block({**_block(), "execution_matrix_identity": "v6-e6-exec-v1-000000000000"})


def test_no_seed_list_is_tracked() -> None:
    tracked = subprocess.check_output(["git", "ls-files"], cwd=REPO_ROOT, text=True).splitlines()
    assert not [path for path in tracked if "seeds.private" in path]
    assert subprocess.run(["git", "check-ignore", "-q", "runs/research_v6_e6/seeds.private.txt"], cwd=REPO_ROOT,
                          check=False).returncode == 0


def test_a_tampered_record_fails_to_load(tmp_path: Path) -> None:
    record = _record()
    record["identity"]["matches_total"] = 11_519
    path = tmp_path / "analysis_freeze.json"
    path.write_text(json.dumps(record), encoding="utf-8")
    with pytest.raises(analysis_freeze.AnalysisFreezeError):
        analysis_freeze.load_freeze(path)


# ---------------------------------------------------------------------------
# Runner steps that need the record: every one refuses out of order
# ---------------------------------------------------------------------------


def _block(commitment: str | None = None) -> dict[str, str]:
    commitment = commitment or seeds.commitment(TEST_SEEDS)
    return dict(seeds.committed_record(commitment, matrix.STRUCTURAL_DIGEST, "2026-09-25T00:00:00Z", "0" * 40))


def _pending_copy(tmp_path: Path) -> Path:
    record = _record()
    record["seed_commitment"] = dict(PENDING)
    record["control_qualification"] = dict(PENDING)
    path = tmp_path / "analysis_freeze.json"
    path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def test_no_control_cell_runs_before_the_seed_commitment(tmp_path: Path) -> None:
    freeze = _pending_copy(tmp_path)
    with pytest.raises(run_e6.E6ConfigurationError, match="no seed commitment"):
        run_e6.execute("C-E6", "F1", confirm=True, run_root=tmp_path / "runs", freeze_path=freeze,
                       seeds_path=tmp_path / "seeds.private.txt")
    assert not (tmp_path / "runs").exists()


def test_no_treatment_cell_runs_before_a_pass_qualification(tmp_path: Path) -> None:
    freeze = _pending_copy(tmp_path)
    record = json.loads(freeze.read_text(encoding="utf-8"))
    record["seed_commitment"] = _block()
    freeze.write_text(json.dumps(record), encoding="utf-8")
    private = tmp_path / "seeds.private.txt"
    seeds.write_private(TEST_SEEDS, private)
    with pytest.raises(run_e6.E6ConfigurationError, match="Checkpoint B"):
        run_e6.execute("T-E6", "F1", confirm=True, confirm_treatment=True, run_root=tmp_path / "runs",
                       freeze_path=freeze, seeds_path=private)
    assert not (tmp_path / "runs").exists()


def test_analysis_reveal_and_interpretation_refuse_out_of_order(tmp_path: Path) -> None:
    freeze = _pending_copy(tmp_path)
    runs = tmp_path / "runs"
    with pytest.raises(run_e6.E6ConfigurationError, match="Checkpoint B"):
        run_e6.analyze(run_root=runs, freeze_path=freeze)
    with pytest.raises(run_e6.E6ConfigurationError, match="required record"):
        run_e6.reveal(tmp_path / "seeds.txt", run_root=runs, freeze_path=freeze)
    with pytest.raises(run_e6.E6ConfigurationError, match="required record"):
        run_e6.interpret(run_root=runs, freeze_path=freeze)
    run_e6._write_json(run_e6.records_root(runs) / run_e6.ANALYSIS_RECORD, {"arms": {}})
    with pytest.raises(run_e6.E6ConfigurationError, match="nothing was committed"):
        run_e6.reveal(tmp_path / "seeds.txt", run_root=runs, freeze_path=freeze)
    with pytest.raises(run_e6.E6ConfigurationError, match="required record"):
        run_e6.interpret(run_root=runs, freeze_path=freeze)  # no D-6 yet


def test_the_i7_step_writes_only_the_permitted_facts(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Exercised with a fixed test list: seeds.generate is replaced, so no real seed is drawn.
    freeze = _pending_copy(tmp_path)
    private = tmp_path / "seeds.private.txt"
    monkeypatch.setattr(run_e6.seeds, "generate", lambda: list(TEST_SEEDS))
    monkeypatch.setattr(run_e6, "git_text", lambda *args: "" if args[0] == "status" else "f" * 40)
    block = run_e6.generate_seeds(confirm=True, run_root=tmp_path / "runs", freeze_path=freeze, seeds_path=private)
    assert set(block) == analysis_freeze.SEED_BLOCK_KEYS
    assert block["seed_commitment"] == seeds.commitment(TEST_SEEDS)
    assert block["execution_matrix_identity"] == matrix.execution_identity(block["seed_commitment"])
    written = json.loads(freeze.read_text(encoding="utf-8"))
    assert written["seed_commitment"] == block
    assert json.dumps(TEST_SEEDS[0]) not in json.dumps(written)  # no seed value in the record
    assert seeds.load_private(block["seed_commitment"], private) == TEST_SEEDS
    analysis_freeze.load_freeze(freeze)  # the record still loads
    with pytest.raises(run_e6.E6ConfigurationError, match="already carries"):
        run_e6.generate_seeds(confirm=True, run_root=tmp_path / "runs", freeze_path=freeze, seeds_path=private)


def test_the_i7_step_refuses_once_a_cell_exists(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    freeze = _pending_copy(tmp_path)
    run_e6.condition_root(tmp_path / "runs", "C-E6", "F1").mkdir(parents=True)
    monkeypatch.setattr(run_e6.seeds, "generate", lambda: list(TEST_SEEDS))
    monkeypatch.setattr(run_e6, "git_text", lambda *args: "" if args[0] == "status" else "f" * 40)
    with pytest.raises(run_e6.E6ConfigurationError, match="matrix cell exists"):
        run_e6.generate_seeds(confirm=True, run_root=tmp_path / "runs", freeze_path=freeze,
                              seeds_path=tmp_path / "seeds.private.txt")
    assert not (tmp_path / "seeds.private.txt").exists()
