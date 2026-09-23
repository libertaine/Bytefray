"""V6 E2 analysis freeze v2 and control-data requalification.

* The freeze identity (``analysis_freeze.py``) keeps the matrix identity and
  pins the whole analysis instrument: pre-registration digest, capture
  analyzer version and digest, the digest of every analysis-tooling file, the
  tooling source commit and the control corpus's match-generation source.
  Loading a freeze record fails closed on any drift.
* Requalification (``requalification.py``) is proven on real, tiny C-V4 and
  C-RS harness runs that include seed 23, whose Seat-A core wraps the arena
  end -- the geometry the version-1 analyzer could not process.
* T-E2 unlocks only through the chain: committed freeze -> gate recorded under
  that freeze -> requalification recorded under that freeze -> execution
  source check.

Nothing here runs a T-E2 match.
"""

from __future__ import annotations

import json
import re
import shutil
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest
from battle_engine.replay import TickSnapshot, iter_replay
from battle_engine.ruleset_policy import (
    BYTEFRAY_RULESET_V4_ID,
    BYTEFRAY_RULESET_V6_RESEARCH_SCALE_ID,
)

from tools.research.v6.e2 import matrix
from tools.research.v6.e2.analysis_freeze import (
    CAPTURE_ANALYZER_FILE,
    CONTROL_SOURCE_SHA,
    TOOLING_FILES,
    AnalysisFreezeError,
    build_freeze_record,
    file_sha256,
    freeze_id,
    identity_inputs,
    load_freeze,
)
from tools.research.v6.e2.capture_analyzer import CAPTURE_ANALYZER_VERSION
from tools.research.v6.e2.control_gate import GATE_RECORD_NAME, ControlGateError, write_gate_record
from tools.research.v6.e2.preregistration import PREREGISTRATION_SHA256
from tools.research.v6.e2.requalification import (
    REQUALIFICATION_RECORD_NAME,
    RequalificationError,
    analyzer_requalification,
    corpus_integrity,
    require_requalification,
    write_requalification_record,
)
from tools.research.v6.e2.run_e2 import execute, freeze_root, treatment_unlock
from tools.research.v6.experiment_harness import REPO_ROOT, ResearchExperimentConfig, run_experiment

EXPECTED = {f.field_id: f.expected_matches for f in matrix.FIELDS}


def _identity(**changes: Any) -> dict[str, Any]:
    identity = identity_inputs(tooling_source_sha="a" * 40, match_generation_tree="b" * 40)
    identity.update(changes)
    return identity


def _write_freeze(path: Path, identity: dict[str, Any] | None = None) -> dict[str, Any]:
    record = build_freeze_record(identity or _identity(), {})
    path.write_text(json.dumps(record), encoding="utf-8")
    return record


# ---------------------------------------------------------------------------
# Freeze identity
# ---------------------------------------------------------------------------


def test_freeze_identity_keeps_the_matrix_identity_and_pins_the_instrument() -> None:
    identity = _identity()
    assert identity["matrix_id"] == matrix.matrix_id() == "v6-e2-matrix-v1-9048907fdc3b"
    assert identity["matrix_digest"] == matrix.E2_MATRIX_DIGEST
    assert identity["preregistration_sha256"] == PREREGISTRATION_SHA256
    assert identity["capture_analyzer_version"] == CAPTURE_ANALYZER_VERSION == 2
    assert identity["capture_analyzer_sha256"] == file_sha256(CAPTURE_ANALYZER_FILE)
    assert identity["tooling_sha256"][CAPTURE_ANALYZER_FILE] == identity["capture_analyzer_sha256"]
    assert identity["control_source_sha"] == CONTROL_SOURCE_SHA == "062feeb28d84c8da0af3f41716e3b5468e0b3eed"
    assert re.fullmatch(r"v6-e2-freeze-v2-[0-9a-f]{12}", freeze_id(identity))
    # Every input is load-bearing: the tooling commit, for example, changes the id.
    assert freeze_id(_identity(tooling_source_sha="c" * 40)) != freeze_id(identity)


def test_every_e2_tooling_file_is_inside_the_freeze() -> None:
    e2_dir = REPO_ROOT / "tools" / "research" / "v6" / "e2"
    tooling = {
        path.relative_to(REPO_ROOT).as_posix()
        for path in [*e2_dir.glob("*.py"), e2_dir / "preregistration.json"]
    }
    assert tooling <= set(TOOLING_FILES)
    assert "tools/research/v6/experiment_harness.py" in TOOLING_FILES
    assert set(_identity()["tooling_sha256"]) == set(TOOLING_FILES)


def test_committed_freeze_v2_holds_against_the_live_tooling() -> None:
    # Fails if any analysis-tooling file, the analyzer version, the matrix or
    # the pre-registration changes without a new freeze.
    record = load_freeze()
    assert record["freeze_id"] == "v6-e2-freeze-v2-db6458596d82"
    identity = record["identity"]
    assert (identity["matrix_id"], identity["capture_analyzer_version"]) == ("v6-e2-matrix-v1-9048907fdc3b", 2)
    assert identity["tooling_source_sha"] == "d584ea986be36c748d01c2fbbce36f68cb11a227"
    assert identity["control_source_sha"] == CONTROL_SOURCE_SHA
    requalification = record["requalification"]
    assert (
        requalification["status"],
        requalification["control_replays_analyzed"],
        requalification["analyzer_failures"],
        requalification["engine_disagreements"],
        requalification["attribution_mismatches"],
        requalification["telemetry_differences_c_v4_vs_c_rs"],
        requalification["control_gate_cells_compared"],
        requalification["control_gate_mismatches"],
    ) == ("PASS", 10240, 0, 0, 0, 0, 5120, 0)


def test_freeze_record_fails_closed_on_any_drift(tmp_path: Path) -> None:
    path = tmp_path / "freeze.json"
    record = _write_freeze(path)
    assert load_freeze(path)["freeze_id"] == record["freeze_id"]

    with pytest.raises(AnalysisFreezeError, match="No analysis freeze record"):
        load_freeze(tmp_path / "missing.json")

    tampered = json.loads(path.read_text(encoding="utf-8"))
    tampered["identity"]["tooling_source_sha"] = "c" * 40
    path.write_text(json.dumps(tampered), encoding="utf-8")
    with pytest.raises(AnalysisFreezeError, match="does not recompute"):
        load_freeze(path)

    stale = _identity()
    stale["tooling_sha256"] = {**stale["tooling_sha256"], CAPTURE_ANALYZER_FILE: "0" * 64}
    _write_freeze(path, stale)
    with pytest.raises(AnalysisFreezeError, match=re.escape(f"tooling files changed since the freeze: ['{CAPTURE_ANALYZER_FILE}']")):
        load_freeze(path)

    for change, message in (
        ({"capture_analyzer_version": 1}, "capture_analyzer_version 1 != live 2"),
        ({"matrix_id": "v6-e2-matrix-v2-000000000000"}, "matrix_id"),
        ({"preregistration_sha256": "0" * 64}, "preregistration_sha256"),
        ({"control_source_sha": "0" * 40}, "control_source_sha"),
    ):
        _write_freeze(path, _identity(**change))
        with pytest.raises(AnalysisFreezeError, match=message):
            load_freeze(path)


# ---------------------------------------------------------------------------
# Requalification on real control runs (seed 23 wraps Seat A's core)
# ---------------------------------------------------------------------------

AGENTS = ("v4_probe", "v4_probe_twin", "e2_sniper", "e2_disrupt_guard")
PAIRS = (("v4_probe", "v4_probe_twin"), ("e2_sniper", "e2_disrupt_guard"))
SEEDS = (1, 23)


@pytest.fixture(scope="module")
def controls(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, Path]:
    root = tmp_path_factory.mktemp("e2-requalify")
    base = ResearchExperimentConfig(
        experiment_id="requalify-check", field=AGENTS, pairs=PAIRS, seeds=SEEDS, ticks=40
    )
    for ruleset_id, name in ((BYTEFRAY_RULESET_V4_ID, "C-V4"), (BYTEFRAY_RULESET_V6_RESEARCH_SCALE_ID, "C-RS")):
        run_experiment(
            replace(base, ruleset_id=ruleset_id, output_dir=root / name, provenance_extra={"e2_condition": name})
        )
    return root / "C-V4", root / "C-RS"


def _cells(root: Path) -> list[dict[str, Any]]:
    data = json.loads((root / "experiment_result.json").read_text(encoding="utf-8"))
    return [cell for condition in data["conditions"] for cell in condition["cells"]]


def _tick0_diffs(replay: Path) -> list[tuple[int, int, str | None]]:
    (tick0,) = [r for r in iter_replay(replay) if isinstance(r, TickSnapshot) and r.tick == 0]
    return [(d.address, d.length, d.owner) for d in tick0.memory_diffs]


def test_requalification_passes_identical_controls_including_a_wrapped_core(controls: tuple[Path, Path]) -> None:
    v4, rs = controls
    # Precondition: seed 23 really seeds Seat A's core across the arena end.
    seed_23 = [c for c in _cells(v4) if c["seed"] == 23]
    assert len(seed_23) == 4
    for cell in seed_23:
        assert _tick0_diffs(v4 / cell["artifact_dir"] / "replay.jsonl")[:2] == [(506, 6, "A"), (0, 2, "A")]

    report = analyzer_requalification(v4, rs)
    assert report["status"] == "PASS"
    for side in report["conditions"].values():
        assert (side["cells"], side["analyzed"], side["failures"]) == (8, 8, 0)
        assert (side["engine_disagreements"], side["attribution_mismatch_matches"]) == (0, 0)
        assert side["capture_analyzer_versions"] == [2]
        assert side["completions"] > 0
    assert report["telemetry_equivalence"] == {
        "cells_compared": 8,
        "unmatched": 0,
        "differences": 0,
        "difference_samples": [],
    }


def _tampered_copy(rs: Path, tmp_path: Path, seed: int, tick: int, edit: Any) -> Path:
    """A copy of the C-RS run with one tick of one replay (the sniper as Seat A) edited."""
    target = tmp_path / "C-RS-copy"
    shutil.copytree(rs, target)
    (cell,) = [
        c
        for c in _cells(target)
        if c["seed"] == seed and c["subject_id"] == "e2_sniper" and c["orientation"] == "candidate_first"
    ]
    # Precondition: the V4 forced line -- the sniper captures Seat B on tick 1.
    assert (cell["winner_id"], cell["ticks_run"]) == ("e2_sniper", 1)
    replay = target / cell["artifact_dir"] / "replay.jsonl"
    lines = replay.read_text(encoding="utf-8").splitlines()
    index = next(i for i, line in enumerate(lines) if json.loads(line).get("tick") == tick)
    snapshot = json.loads(lines[index])
    edit(snapshot)
    lines[index] = json.dumps(snapshot)
    replay.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return target


def test_requalification_fails_on_an_analyzer_failure(controls: tuple[Path, Path], tmp_path: Path) -> None:
    v4, rs = controls

    def shift_seat_a_pc(tick0: dict[str, Any]) -> None:
        assert tick0["agents"][0]["pc"] == 506
        tick0["agents"][0]["pc"] = 507

    report = analyzer_requalification(v4, _tampered_copy(rs, tmp_path, 23, 0, shift_seat_a_pc))
    side = report["conditions"]["C-RS"]
    assert (report["status"], side["failures"], side["analyzed"], side["failed_seeds"]) == ("FAIL", 1, 7, [23])
    assert "not the contiguous run" in side["failure_samples"][0]["error"]
    assert report["conditions"]["C-V4"]["failures"] == 0


def test_requalification_fails_on_engine_disagreement_and_telemetry_difference(
    controls: tuple[Path, Path], tmp_path: Path
) -> None:
    v4, rs = controls

    def keep_seat_b_core(tick1: dict[str, Any]) -> None:
        # Credit every tick-1 write to B: the replay then shows B keeping its
        # core while the engine's own record still says B was captured.
        assert {diff["owner"] for diff in tick1["memory_diffs"]} == {"A"}
        for diff in tick1["memory_diffs"]:
            diff["owner"] = "B"

    report = analyzer_requalification(v4, _tampered_copy(rs, tmp_path, 1, 1, keep_seat_b_core))
    side = report["conditions"]["C-RS"]
    assert (report["status"], side["failures"], side["engine_disagreements"]) == ("FAIL", 0, 1)
    assert report["conditions"]["C-V4"]["engine_disagreements"] == 0
    assert report["telemetry_equivalence"]["differences"] == 1


def test_corpus_integrity_checks_cells_artifacts_and_provenance(controls: tuple[Path, Path]) -> None:
    v4, _ = controls
    recorded = json.loads((v4 / "provenance.json").read_text(encoding="utf-8"))
    fingerprints = {name: matrix.AGENT_FINGERPRINTS[name] for name in AGENTS}
    expected = {"git_sha": recorded["git_sha"], "git_dirty": recorded["git_dirty"], "e2_condition": "C-V4"}

    def check(**changes: Any) -> dict[str, Any]:
        args: dict[str, Any] = {
            "ruleset_id": BYTEFRAY_RULESET_V4_ID,
            "pairs": PAIRS,
            "seeds": SEEDS,
            "provenance": expected,
            "fingerprints": fingerprints,
        }
        args.update(changes)
        return corpus_integrity(v4, **args)

    report = check()
    assert (report["status"], report["cells"], report["expected_cells"], report["match_dirs_on_disk"]) == (
        "PASS",
        8,
        8,
        8,
    )
    for change, message in (
        ({"seeds": (1, 23, 24)}, "4 missing cells"),
        ({"ruleset_id": BYTEFRAY_RULESET_V6_RESEARCH_SCALE_ID}, "8 result.json files carry another Ruleset"),
        ({"provenance": {**expected, "git_dirty": not recorded["git_dirty"]}}, "provenance git_dirty"),
        ({"provenance": {**expected, "git_sha": "0" * 40}}, "provenance git_sha"),
        ({"fingerprints": {**fingerprints, "e2_sniper": "0" * 64}}, "fingerprints differ"),
    ):
        report = check(**change)
        assert report["status"] == "FAIL"
        assert any(message in problem for problem in report["problems"]), (message, report["problems"])


# ---------------------------------------------------------------------------
# Records and the T-E2 unlock chain
# ---------------------------------------------------------------------------


def _passing_fields(counts: dict[str, int] = EXPECTED) -> dict[str, dict[str, Any]]:
    return {
        fid: {"status": "PASS", "conditions": {"C-V4": {"analyzed": n}, "C-RS": {"analyzed": n}}}
        for fid, n in counts.items()
    }


def _write_requalification(path: Path, fid: str, **changes: Any) -> None:
    args: dict[str, Any] = {
        "freeze_id": fid,
        "matrix_id": matrix.matrix_id(),
        "fields": _passing_fields(),
        "integrity": {"C-V4/F1": {"status": "PASS"}},
        "expected_matches": EXPECTED,
        "provenance": {},
    }
    args.update(changes)
    write_requalification_record(path, **args)


def test_requalification_record_rules(tmp_path: Path) -> None:
    path = tmp_path / REQUALIFICATION_RECORD_NAME
    with pytest.raises(RequalificationError, match="No analyzer requalification record"):
        require_requalification(path, freeze_id="f", expected_matches=EXPECTED)
    _write_requalification(path, "f")
    assert require_requalification(path, freeze_id="f", expected_matches=EXPECTED)["replays_analyzed"] == 10240
    for changes, message in (
        ({"freeze_id": "g"}, "freeze_id"),
        ({"fields": _passing_fields({**EXPECTED, "F3": 1550})}, "F3"),
        ({"integrity": {"C-RS/F2": {"status": "FAIL"}}}, "status 'FAIL'"),
        ({"fields": {**_passing_fields(), "F1": {**_passing_fields()["F1"], "status": "FAIL"}}}, "F1"),
    ):
        _write_requalification(path, "f", **changes)
        with pytest.raises(RequalificationError, match=message):
            require_requalification(path, freeze_id="f", expected_matches=EXPECTED)


def _write_gate(path: Path, fid: str | None) -> None:
    write_gate_record(
        path,
        matrix_id=matrix.matrix_id(),
        fields={f: {"status": "PASS", "cells_compared": n} for f, n in EXPECTED.items()},
        expected_matches=EXPECTED,
        sample=False,
        provenance={},
        freeze_id=fid,
    )


def test_treatment_unlocks_only_through_the_whole_freeze_chain(tmp_path: Path) -> None:
    runs, freeze_path = tmp_path / "runs", tmp_path / "freeze.json"
    with pytest.raises(AnalysisFreezeError, match="No analysis freeze record"):
        treatment_unlock(runs, freeze_path=freeze_path)
    fid = _write_freeze(freeze_path)["freeze_id"]
    records = freeze_root(runs, fid)
    assert records == runs / matrix.matrix_id() / "freezes" / fid

    # A freeze-v1 gate at the matrix root is never consulted.
    _write_gate(runs / matrix.matrix_id() / GATE_RECORD_NAME, None)
    with pytest.raises(ControlGateError, match="No control gate record"):
        treatment_unlock(runs, freeze_path=freeze_path)
    _write_gate(records / GATE_RECORD_NAME, "v6-e2-freeze-v2-000000000000")
    with pytest.raises(ControlGateError, match="freeze_id"):
        treatment_unlock(runs, freeze_path=freeze_path)
    _write_gate(records / GATE_RECORD_NAME, fid)
    with pytest.raises(RequalificationError, match="No analyzer requalification record"):
        treatment_unlock(runs, freeze_path=freeze_path)
    _write_requalification(records / REQUALIFICATION_RECORD_NAME, fid)
    unlock = treatment_unlock(runs, freeze_path=freeze_path)
    assert (unlock["freeze"]["freeze_id"], unlock["gate"]["freeze_id"], unlock["requalification"]["freeze_id"]) == (
        fid,
        fid,
        fid,
    )

    # Unlocked on paper, T-E2 still checks its execution source before any
    # match: this test freeze names a tree and commit that do not exist.
    with pytest.raises(AnalysisFreezeError, match="T-E2 execution source check failed"):
        execute("T-E2", "F2", run_root=runs, confirm=True, freeze_path=freeze_path)
    assert not (runs / matrix.matrix_id() / "T-E2").exists()
