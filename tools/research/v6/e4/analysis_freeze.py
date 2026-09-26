"""The frozen E4 analysis identity (freeze v1).

Two identities are kept apart (the E2/E3 convention). The matrix identity
(``matrix.py``) says which matches the experiment runs. The freeze identity
says which complete instrument interprets them. It carries:

* the matrix id and digest, the contest-class table SHA-256 and the
  pre-registration SHA-256;
* the E4 analyzer (cell metrics and analysis) versions and digests;
* capture analyzer v2's version and digest, checked on every load against the
  E2 analysis freeze v2 that pinned it;
* E3 action/parity analyzer v1's version and digest, and every other reused E3
  file, checked on every load against E3 analysis freeze v1's record;
* the SHA-256 of every analysis-tooling file, reused or new;
* the Git commit those files were qualified at and the engine source tree that
  generates the matches;
* the E4 parent byte-identity freeze and the historical E3 parent provenance.

Repairing analysis tooling changes the freeze identity, never the matrix
identity. ``analysis_freeze.json`` is the committed record; loading it fails
closed unless its digest recomputes and every live input still equals the
record. Its ``control_qualification`` block (outside the identity digest) is
added after the controls pass, and names the gate records and the frozen
control populations the treatment unlock requires.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from tools.research.v6.e2.capture_analyzer import CAPTURE_ANALYZER_VERSION
from tools.research.v6.e3 import analysis_freeze as e3_freeze
from tools.research.v6.e3.action_parity import E3_ACTION_PARITY_VERSION
from tools.research.v6.e4 import contest_classes, matrix
from tools.research.v6.e4.analyze_e4 import E4_ANALYSIS_VERSION
from tools.research.v6.e4.cell_metrics import E4_CELL_METRICS_VERSION
from tools.research.v6.e4.preregistration import preregistration_digest
from tools.research.v6.experiment_harness import REPO_ROOT

FREEZE_VERSION = 1
FREEZE_SCHEMA = "bytefray.v6.e4.analysis_freeze"
FREEZE_RECORD_PATH = Path(__file__).with_name("analysis_freeze.json")

CAPTURE_ANALYZER_FILE = e3_freeze.CAPTURE_ANALYZER_FILE
ACTION_PARITY_FILE = e3_freeze.ACTION_PARITY_FILE
CELL_METRICS_FILE = "tools/research/v6/e4/cell_metrics.py"
ANALYSIS_FILE = "tools/research/v6/e4/analyze_e4.py"
E3_FREEZE_FILE = "tools/research/v6/e3/analysis_freeze.json"
# E3 files E4 imports unchanged; each must still equal E3 freeze v1's pin.
REUSED_E3_FILES: tuple[str, ...] = (
    "tools/research/v6/experiment_harness.py",
    CAPTURE_ANALYZER_FILE,
    "tools/research/v6/e2/matrix.py",
    "tools/research/v6/e2/requalification.py",
    ACTION_PARITY_FILE,
    "tools/research/v6/e3/analysis_freeze.py",
    "tools/research/v6/e3/analyze_e3.py",
    "tools/research/v6/e3/d9_gate.py",
    "tools/research/v6/e3/entrants.py",
    "tools/research/v6/e3/gates.py",
    "tools/research/v6/e3/matrix.py",
    "tools/research/v6/e3/populations.py",
    "tools/research/v6/e3/fixtures/agents/e3_jam_sniper/agent.py",
    "tools/research/v6/e3/fixtures/agents/e3_jam_sniper/agent.yaml",
    "tools/research/v6/e3/fixtures/agents/e3_jam_sniper_twin/agent.py",
    "tools/research/v6/e3/fixtures/agents/e3_jam_sniper_twin/agent.yaml",
)
E4_FILES: tuple[str, ...] = (
    "tools/research/v6/e4/analysis_freeze.py",
    ANALYSIS_FILE,
    CELL_METRICS_FILE,
    "tools/research/v6/e4/contest_classes.json",
    "tools/research/v6/e4/contest_classes.py",
    "tools/research/v6/e4/d9_gate.py",
    "tools/research/v6/e4/gates.py",
    "tools/research/v6/e4/manipulation_gate.py",
    "tools/research/v6/e4/matrix.py",
    "tools/research/v6/e4/populations.py",
    "tools/research/v6/e4/preregistration.json",
    "tools/research/v6/e4/preregistration.py",
    "tools/research/v6/e4/run_e4.py",
    "tools/research/v6/e4/telemetry.py",
)
# E3's committed control populations (P-STALE's source) are data, pinned by E3's freeze.
E3_POPULATIONS_FILE = "tools/research/v6/e3/control_populations.json"
TOOLING_FILES: tuple[str, ...] = (*REUSED_E3_FILES, E3_POPULATIONS_FILE, *E4_FILES)
MATCH_GENERATION_PATH = e3_freeze.MATCH_GENERATION_PATH


class AnalysisFreezeError(RuntimeError):
    """The E4 analysis instrument does not match its frozen identity."""


file_sha256 = e3_freeze.file_sha256
git_text = e3_freeze.git_text


def e3_freeze_identity(repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    record: dict[str, Any] = json.loads((repo_root / E3_FREEZE_FILE).read_text(encoding="utf-8"))
    return record


def check_reused_unchanged() -> None:
    """Capture analyzer v2 still equals E2 freeze v2's pin; every reused E3 file (and
    E3's control populations) still equals E3 freeze v1's pin."""
    try:
        e3_freeze.check_capture_analyzer_unchanged()
    except e3_freeze.AnalysisFreezeError as exc:
        raise AnalysisFreezeError(str(exc)) from None
    record = e3_freeze_identity()
    pinned = record["identity"]["tooling_sha256"]
    changed = sorted(path for path in REUSED_E3_FILES if file_sha256(path) != pinned[path])
    if changed:
        raise AnalysisFreezeError(f"reused E3 files differ from E3 freeze {record['freeze_id']}: {changed}")
    populations = (record.get("control_qualification") or {}).get("populations") or {}
    if file_sha256(E3_POPULATIONS_FILE) != populations.get("sha256"):
        raise AnalysisFreezeError(f"{E3_POPULATIONS_FILE} differs from E3 freeze {record['freeze_id']}'s pin")


def identity_inputs(*, tooling_source_sha: str, match_generation_tree: str) -> dict[str, Any]:
    """The inputs the freeze identity is a digest of, read from the live checkout."""
    e3_record = e3_freeze_identity()
    return {
        "freeze_version": FREEZE_VERSION,
        "matrix_id": matrix.matrix_id(),
        "matrix_digest": matrix.E4_MATRIX_DIGEST,
        "matches_total": matrix.matches_total(),
        "contest_classes_sha256": contest_classes.CONTEST_CLASSES_SHA256,
        "preregistration_sha256": preregistration_digest(),
        "e4_analysis_version": E4_ANALYSIS_VERSION,
        "e4_analysis_sha256": file_sha256(ANALYSIS_FILE),
        "e4_cell_metrics_version": E4_CELL_METRICS_VERSION,
        "e4_cell_metrics_sha256": file_sha256(CELL_METRICS_FILE),
        "action_parity_version": E3_ACTION_PARITY_VERSION,
        "action_parity_sha256": file_sha256(ACTION_PARITY_FILE),
        "capture_analyzer_version": CAPTURE_ANALYZER_VERSION,
        "capture_analyzer_sha256": file_sha256(CAPTURE_ANALYZER_FILE),
        "capture_analyzer_e2_freeze_id": e3_freeze.e2_capture_analyzer_identity()["e2_freeze_id"],
        "reused_e3_freeze_id": e3_record["freeze_id"],
        "tooling_sha256": {path: file_sha256(path) for path in TOOLING_FILES},
        "tooling_source_sha": tooling_source_sha,
        "match_generation_path": MATCH_GENERATION_PATH,
        "match_generation_tree": match_generation_tree,
        "parent_freeze": dict(sorted(matrix.PARENT_FREEZE.items())),
        "historical_parent": {
            "matrix_id": matrix.HISTORICAL_MATRIX_ID,
            "matrix_digest": matrix.HISTORICAL_MATRIX_DIGEST,
            "freeze_id": matrix.HISTORICAL_FREEZE_ID,
            "generation": dict(sorted(matrix.HISTORICAL_GENERATION.items())),
            "conditions": dict(sorted(matrix.HISTORICAL_PARENT.items())),
        },
    }


def freeze_digest(identity: dict[str, Any]) -> str:
    canonical = json.dumps(identity, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def freeze_id(identity: dict[str, Any]) -> str:
    return f"v6-e4-freeze-v{identity['freeze_version']}-{freeze_digest(identity)[:12]}"


def build_freeze_record(identity: dict[str, Any], control_qualification: dict[str, Any] | None = None) -> dict[str, Any]:
    """A freeze record; ``control_qualification`` summarizes control-data evidence
    and is outside the identity digest."""
    return {
        "schema": FREEZE_SCHEMA,
        "status": "frozen before any T-E4 or T-E4K1 matrix data exists",
        "freeze_id": freeze_id(identity),
        "freeze_digest": freeze_digest(identity),
        "identity": identity,
        "control_qualification": control_qualification or {"status": "PENDING"},
    }


def candidate_identity() -> dict[str, Any]:
    """The would-be freeze of the current clean checkout, before a record is committed."""
    if git_text("status", "--porcelain"):
        raise AnalysisFreezeError("A candidate analysis freeze needs a clean tracked tree.")
    check_reused_unchanged()
    identity = identity_inputs(
        tooling_source_sha=git_text("rev-parse", "HEAD"),
        match_generation_tree=git_text("rev-parse", f"HEAD:{MATCH_GENERATION_PATH}"),
    )
    return build_freeze_record(identity)


def load_freeze(path: Path = FREEZE_RECORD_PATH) -> dict[str, Any]:
    """The committed freeze record; fails closed on any drift from the live checkout."""
    if not path.is_file():
        raise AnalysisFreezeError(f"No E4 analysis freeze record at {path}; freeze the analysis first.")
    check_reused_unchanged()
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
        live = identity_inputs(
            tooling_source_sha=str(identity.get("tooling_source_sha")),
            match_generation_tree=str(identity.get("match_generation_tree")),
        )
        for key, value in live.items():
            if key == "tooling_sha256":
                recorded = identity.get(key) or {}
                changed = sorted(p for p in set(value) | set(recorded) if value.get(p) != recorded.get(p))
                if changed:
                    problems.append(f"tooling files changed since the freeze: {changed}")
            elif identity.get(key) != value:
                problems.append(f"{key} {identity.get(key)!r} != live {value!r}")
    if problems:
        raise AnalysisFreezeError("E4 analysis freeze does not hold: " + "; ".join(problems))
    return record


def verify_execution_source(record: dict[str, Any]) -> None:
    """Before any E4 match runs: a clean tree, engine source identical to the frozen
    match-generation tree, and every tooling file identical to its content at the
    commit the freeze was qualified at."""
    identity = record["identity"]
    problems: list[str] = []
    if git_text("status", "--porcelain"):
        problems.append("the tracked tree is not clean")
    live_tree = git_text("rev-parse", f"HEAD:{identity['match_generation_path']}")
    if live_tree != identity["match_generation_tree"]:
        problems.append(f"{identity['match_generation_path']} tree {live_tree} differs from the frozen "
                        f"{identity['match_generation_tree']}")
    for path, digest in sorted(identity["tooling_sha256"].items()):
        try:
            committed = hashlib.sha256(
                subprocess.check_output(["git", "show", f"{identity['tooling_source_sha']}:{path}"], cwd=REPO_ROOT)
                .replace(b"\r\n", b"\n")).hexdigest()
        except subprocess.CalledProcessError:
            committed = None
        if committed != digest:
            problems.append(f"{path} at {identity['tooling_source_sha']} differs from the freeze")
    if problems:
        raise AnalysisFreezeError("E4 execution source check failed: " + "; ".join(problems))
