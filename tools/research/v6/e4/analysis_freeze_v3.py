"""The E4 analysis identity v3: freeze v2's instrument plus pre-registration v3.

Freeze v2 (``analysis_freeze_v2.json``, ``v6-e4-freeze-v2-68d262a0dbd1``) is kept
exactly as committed and still holds, and through it freeze v1
(``v6-e4-freeze-v1-101a941f5e30``), the measurement instrument and its control
qualification. Pre-registration v3 changes only how the interpretation table
is read (O-INTERPRETATION-3: H2 takes precedence over the standalone
"¬H1 ∧ H3" row, with a combined H2 + H3 outcome), so freeze v3 is freeze v2
plus that reading. Its identity carries:

* freeze v2's id and digest and the SHA-256 of its committed record, and the
  same for freeze v1;
* the measurement tooling, whose SHA-256s must equal freeze v1's pins, and
  the v2 interpretation files, whose SHA-256s must equal freeze v2's pins;
* the SHA-256 of pre-registration v1 and of the v2 and v3 amendments;
* the SHA-256 of the v3 interpretation files, the commit they were qualified
  at, and the engine source tree (freeze v1's, unchanged).

The matrix identity does not change. ``run_e4`` produces every measurement
record under freeze v1's id, as registered. ``interpret`` reads run_e4's
analysis record under freeze v3: it requires every treatment cell set and the
analysis to have been produced, from a clean tree, at a commit that already
held this freeze v3 record, and writes the O-INTERPRETATION-3 reading (with
the v2 and v1 readings inside it) under ``freezes/<freeze v3 id>/``.

Subcommands (``python -m tools.research.v6.e4.analysis_freeze_v3 ...``):
``verify`` (read-only: freezes v3, v2 and v1 hold, and the v1 treatment unlock
passes; ``--execution`` adds the execution-source checks) and ``interpret``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from tools.research.v6.e4 import analysis_freeze, analysis_freeze_v2, matrix, run_e4
from tools.research.v6.e4.analysis_freeze import (
    AnalysisFreezeError,
    file_sha256,
    freeze_digest,
    freeze_id,
    git_text,
)
from tools.research.v6.e4.analyze_e4 import E4_ANALYSIS_VERSION, read_interpretation
from tools.research.v6.e4.gates import record_sha256
from tools.research.v6.e4.preregistration import preregistration_digest
from tools.research.v6.e4.preregistration_v2 import preregistration_v2_digest
from tools.research.v6.e4.preregistration_v3 import (
    AMENDMENT_ID,
    load_preregistration_v3,
    preregistration_v3_digest,
    read_interpretation_v3,
)
from tools.research.v6.experiment_harness import REPO_ROOT, get_git_provenance

FREEZE_VERSION = 3
FREEZE_SCHEMA = analysis_freeze.FREEZE_SCHEMA
FREEZE_RECORD_PATH = Path(__file__).with_name("analysis_freeze_v3.json")
FREEZE_RECORD_FILE = "tools/research/v6/e4/analysis_freeze_v3.json"
BASE_FREEZE_FILE = analysis_freeze_v2.FREEZE_RECORD_FILE
ROOT_FREEZE_FILE = analysis_freeze_v2.BASE_FREEZE_FILE
INTERPRETATION_FILES: tuple[str, ...] = (
    "tools/research/v6/e4/analysis_freeze_v3.py",
    "tools/research/v6/e4/preregistration_v3.json",
    "tools/research/v6/e4/preregistration_v3.py",
)
INTERPRETATION_RECORD_NAME = "interpretation_v3.json"
INTERPRETATION_SCHEMA = "bytefray.v6.e4.interpretation_v3"


def _pin(record: dict[str, Any], path: str) -> dict[str, Any]:
    return {"freeze_id": record["freeze_id"], "freeze_digest": record["freeze_digest"], "path": path,
            "sha256": file_sha256(path)}


def identity_inputs(*, tooling_source_sha: str, match_generation_tree: str) -> dict[str, Any]:
    """The inputs the freeze v3 identity is a digest of, read from the live checkout.
    Freezes v2 and v1 must hold first."""
    base = analysis_freeze_v2.load_freeze_v2()
    root = analysis_freeze.load_freeze()
    return {
        "freeze_version": FREEZE_VERSION,
        "amendment": AMENDMENT_ID,
        "base_freeze": _pin(base, BASE_FREEZE_FILE),
        "root_freeze": _pin(root, ROOT_FREEZE_FILE),
        "matrix_id": matrix.matrix_id(),
        "matrix_digest": matrix.E4_MATRIX_DIGEST,
        "matches_total": matrix.matches_total(),
        "preregistration_sha256": preregistration_digest(),
        "preregistration_v2_sha256": preregistration_v2_digest(),
        "preregistration_v3_sha256": preregistration_v3_digest(),
        "measurement_tooling_sha256": {path: file_sha256(path) for path in analysis_freeze.TOOLING_FILES},
        "prior_interpretation_tooling_sha256": {path: file_sha256(path)
                                                for path in analysis_freeze_v2.INTERPRETATION_FILES},
        "interpretation_tooling_sha256": {path: file_sha256(path) for path in INTERPRETATION_FILES},
        "tooling_source_sha": tooling_source_sha,
        "match_generation_path": analysis_freeze.MATCH_GENERATION_PATH,
        "match_generation_tree": match_generation_tree,
    }


def build_freeze_record(identity: dict[str, Any]) -> dict[str, Any]:
    """A freeze v3 record. Its control qualification is freeze v1's, pinned through the
    v2 and v1 records' SHA-256s, since no measurement input changed."""
    root_id = identity["root_freeze"]["freeze_id"]
    return {
        "schema": FREEZE_SCHEMA,
        "status": "frozen before any T-E4 or T-E4K1 matrix data exists",
        "freeze_id": freeze_id(identity),
        "freeze_digest": freeze_digest(identity),
        "identity": identity,
        "control_qualification": {
            "status": "INHERITED",
            "from": root_id,
            "note": (f"Freeze v3 changes no measurement input, so {root_id}'s control qualification applies "
                     "unchanged; run_e4's treatment unlock re-verifies it under that freeze."),
        },
    }


def candidate_record() -> dict[str, Any]:
    """The would-be freeze v3 of the current clean checkout, before a record is committed."""
    if git_text("status", "--porcelain"):
        raise AnalysisFreezeError("A candidate analysis freeze needs a clean tracked tree.")
    return build_freeze_record(identity_inputs(
        tooling_source_sha=git_text("rev-parse", "HEAD"),
        match_generation_tree=git_text("rev-parse", f"HEAD:{analysis_freeze.MATCH_GENERATION_PATH}"),
    ))


def load_freeze_v3(path: Path = FREEZE_RECORD_PATH) -> dict[str, Any]:
    """The committed freeze v3 record. Fails closed unless freezes v2 and v1 hold, their
    records are the pinned ones, every measurement file equals v1's pin, every v2
    interpretation file equals v2's pin, and every live input still equals the record."""
    if not path.is_file():
        raise AnalysisFreezeError(f"No E4 analysis freeze v3 record at {path}; freeze it first.")
    load_preregistration_v3()
    record: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    identity = record.get("identity") or {}
    problems: list[str] = []
    if record.get("schema") != FREEZE_SCHEMA:
        problems.append(f"schema {record.get('schema')!r}")
    if record.get("freeze_digest") != freeze_digest(identity) or record.get("freeze_id") != freeze_id(identity):
        problems.append("the record's digest or id does not recompute from its identity")
    if identity.get("freeze_version") != FREEZE_VERSION:
        problems.append(f"freeze_version {identity.get('freeze_version')!r} != {FREEZE_VERSION}")
    else:
        live = identity_inputs(tooling_source_sha=str(identity.get("tooling_source_sha")),
                               match_generation_tree=str(identity.get("match_generation_tree")))
        for key, value in live.items():
            recorded = identity.get(key)
            if isinstance(value, dict) and key.endswith("tooling_sha256"):
                recorded = recorded or {}
                changed = sorted(p for p in set(value) | set(recorded) if value.get(p) != recorded.get(p))
                if changed:
                    problems.append(f"{key}: files changed since the freeze: {changed}")
            elif recorded != value:
                problems.append(f"{key} {recorded!r} != live {value!r}")
        base = analysis_freeze_v2.load_freeze_v2()
        root = analysis_freeze.load_freeze()
        if identity.get("measurement_tooling_sha256") != root["identity"]["tooling_sha256"]:
            problems.append("the measurement tooling differs from freeze v1's pins")
        if identity.get("prior_interpretation_tooling_sha256") != base["identity"]["interpretation_tooling_sha256"]:
            problems.append("the v2 interpretation files differ from freeze v2's pins")
        if identity.get("match_generation_tree") != root["identity"]["match_generation_tree"]:
            problems.append("the match-generation tree differs from freeze v1's")
        if (root.get("control_qualification") or {}).get("status") != "PASS":
            problems.append("freeze v1's control qualification is not PASS")
    if problems:
        raise AnalysisFreezeError("E4 analysis freeze v3 does not hold: " + "; ".join(problems))
    return record


def _committed_sha256(commit: str, path: str) -> str | None:
    try:
        data = subprocess.check_output(["git", "show", f"{commit}:{path}"], cwd=REPO_ROOT,
                                       stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        return None
    return hashlib.sha256(data.replace(b"\r\n", b"\n")).hexdigest()


def verify_execution_source_v3(record: dict[str, Any]) -> None:
    """Freeze v2's execution-source check (which includes freeze v1's), plus every v3
    interpretation file equal to its content at the commit freeze v3 was qualified at."""
    analysis_freeze_v2.verify_execution_source_v2(analysis_freeze_v2.load_freeze_v2())
    identity = record["identity"]
    changed = [path for path, digest in sorted(identity["interpretation_tooling_sha256"].items())
               if _committed_sha256(identity["tooling_source_sha"], path) != digest]
    if changed:
        raise AnalysisFreezeError(f"E4 freeze v3 execution source check failed: {changed} differ at "
                                  f"{identity['tooling_source_sha']}")


def held_at(commit: str, path: Path = FREEZE_RECORD_PATH) -> bool:
    """Whether ``commit`` already held this freeze v3 record, byte for byte."""
    return _committed_sha256(commit, FREEZE_RECORD_FILE) == record_sha256(path)


def _require_generated_under(provenance: dict[str, Any], what: str, record_path: Path) -> None:
    sha = str(provenance.get("git_sha"))
    if provenance.get("git_dirty") is not False or not held_at(sha, record_path):
        raise AnalysisFreezeError(f"{what} was not produced from a clean tree at a commit holding freeze v3 "
                                  f"(git_sha {sha}, git_dirty {provenance.get('git_dirty')!r}).")


def interpret(*, run_root: Path | None = None, record_path: Path = FREEZE_RECORD_PATH) -> dict[str, Any]:
    """The O-INTERPRETATION-3 reading of run_e4's frozen analysis record."""
    root = run_root or run_e4.DEFAULT_RUN_ROOT
    freeze = load_freeze_v3(record_path)
    measurement_id = freeze["identity"]["root_freeze"]["freeze_id"]
    for condition_id in matrix.TREATMENT_CONDITIONS:
        for field_id in matrix.FIELD_IDS:
            provenance_path = run_e4.condition_root(root, condition_id, field_id) / "provenance.json"
            if not provenance_path.is_file():
                raise AnalysisFreezeError(f"No treatment provenance at {provenance_path}.")
            provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
            if provenance.get("e4_freeze_id") != measurement_id:
                raise AnalysisFreezeError(f"{condition_id}/{field_id} ran under {provenance.get('e4_freeze_id')!r}, "
                                          f"not {measurement_id}.")
            _require_generated_under(provenance, f"{condition_id}/{field_id}", record_path)
    analysis_path = run_e4.freeze_root(root, measurement_id) / run_e4.ANALYSIS_RECORD_NAME
    if not analysis_path.is_file():
        raise AnalysisFreezeError(f"No E4 analysis record at {analysis_path}; run run_e4 analyze first.")
    analysis = json.loads(analysis_path.read_text(encoding="utf-8"))
    expected = {"freeze_id": measurement_id, "matrix_id": matrix.matrix_id(),
                "e4_analysis_version": E4_ANALYSIS_VERSION,
                "preregistration_sha256": freeze["identity"]["preregistration_sha256"]}
    wrong = {key: analysis.get(key) for key, value in expected.items() if analysis.get(key) != value}
    if wrong:
        raise AnalysisFreezeError(f"The analysis record is not freeze v1's: {wrong}")
    _require_generated_under(analysis.get("provenance") or {}, "The analysis record", record_path)
    prereg = load_preregistration_v3()
    inputs = analysis["result"]["interpretation_inputs"]
    if read_interpretation(inputs, prereg["v1"]) != analysis["result"]["interpretation"]:
        raise AnalysisFreezeError("The analysis record's v1 reading does not recompute from its inputs.")
    identity = freeze["identity"]
    record = {
        "schema": INTERPRETATION_SCHEMA,
        "freeze_id": freeze["freeze_id"],
        "base_freeze_id": identity["base_freeze"]["freeze_id"],
        "measurement_freeze_id": measurement_id,
        "matrix_id": matrix.matrix_id(),
        "preregistration_sha256": identity["preregistration_sha256"],
        "preregistration_v2_sha256": identity["preregistration_v2_sha256"],
        "preregistration_v3_sha256": identity["preregistration_v3_sha256"],
        "analysis_record": {"path": str(analysis_path.relative_to(root)), "sha256": record_sha256(analysis_path)},
        "interpretation_inputs": inputs,
        "reading": read_interpretation_v3(inputs, prereg),
        "provenance": get_git_provenance(),
    }
    out = run_e4.freeze_root(root, freeze["freeze_id"]) / INTERPRETATION_RECORD_NAME
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(record, indent=2, sort_keys=True, ensure_ascii=False), encoding="utf-8")
    return record


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="analysis_freeze_v3", description=(__doc__ or "").splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    verify = sub.add_parser("verify", help="freezes v3, v2 and v1 hold and the v1 unlock passes (read-only)")
    verify.add_argument("--execution", action="store_true", help="also run the execution-source checks")
    verify.add_argument("--run-root", type=Path)
    reading = sub.add_parser("interpret", help="the O-INTERPRETATION-3 reading of run_e4's analysis record")
    reading.add_argument("--run-root", type=Path)
    args = parser.parse_args(argv)
    root = args.run_root or run_e4.DEFAULT_RUN_ROOT
    if args.command == "verify":
        record = load_freeze_v3()
        run_e4.treatment_unlock(root)
        if args.execution:
            verify_execution_source_v3(record)
        identity = record["identity"]
        print(json.dumps({"freeze_id": record["freeze_id"], "base_freeze_id": identity["base_freeze"]["freeze_id"],
                          "root_freeze_id": identity["root_freeze"]["freeze_id"], "holds": True, "unlocked": True,
                          "execution_source": "PASS" if args.execution else None,
                          "treatment_artifacts": run_e4.treatment_artifacts(root)}, indent=2, sort_keys=True))
        return 0
    record = interpret(run_root=args.run_root)
    print(json.dumps({"freeze_id": record["freeze_id"], "inputs": record["interpretation_inputs"],
                      "reading": record["reading"]}, indent=2, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
