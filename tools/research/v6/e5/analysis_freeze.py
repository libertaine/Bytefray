"""The frozen E5 analysis identity (freeze v1).

Two identities are kept apart (the E2-E4 convention). The matrix identity
(``matrix.py``) says which matches the experiment runs; the freeze identity
says which complete instrument interprets them. It carries:

* the matrix id and digest and the pre-registration SHA-256;
* the E5 analyzer (cell metrics and analysis) versions and digests;
* capture analyzer v2, E3 action/parity analyzer v1 and E4 cell metrics v1,
  and every other reused E3/E4 file, each checked on every load against E4
  analysis freeze v1's pin (which itself checks E3's and E2's);
* the SHA-256 of every analysis-tooling file, reused or new;
* the Git commit those files were qualified at and the engine source tree that
  generates the matches;
* the E5 parent byte-identity freeze and the historical E4 parent provenance.

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
from tools.research.v6.e3.action_parity import E3_ACTION_PARITY_VERSION
from tools.research.v6.e4 import analysis_freeze as e4_freeze
from tools.research.v6.e4.cell_metrics import E4_CELL_METRICS_VERSION
from tools.research.v6.e5 import matrix
from tools.research.v6.e5.analyze_e5 import E5_ANALYSIS_VERSION
from tools.research.v6.e5.cell_metrics import E5_CELL_METRICS_VERSION
from tools.research.v6.e5.preregistration import preregistration_digest
from tools.research.v6.experiment_harness import REPO_ROOT

FREEZE_VERSION = 1
FREEZE_SCHEMA = "bytefray.v6.e5.analysis_freeze"
FREEZE_RECORD_PATH = Path(__file__).with_name("analysis_freeze.json")

E4_FREEZE_FILE = "tools/research/v6/e4/analysis_freeze.json"
CELL_METRICS_FILE = "tools/research/v6/e5/cell_metrics.py"
ANALYSIS_FILE = "tools/research/v6/e5/analyze_e5.py"
# E3/E4 files E5 imports unchanged; each must still equal E4 freeze v1's pin.
REUSED_FILES: tuple[str, ...] = (
    "tools/research/v6/experiment_harness.py",
    e4_freeze.CAPTURE_ANALYZER_FILE,
    "tools/research/v6/e2/matrix.py",
    "tools/research/v6/e2/requalification.py",
    e4_freeze.ACTION_PARITY_FILE,
    "tools/research/v6/e3/analysis_freeze.py",
    "tools/research/v6/e3/analyze_e3.py",
    "tools/research/v6/e3/d9_gate.py",
    "tools/research/v6/e3/entrants.py",
    "tools/research/v6/e3/gates.py",
    "tools/research/v6/e3/matrix.py",
    "tools/research/v6/e3/populations.py",
    "tools/research/v6/e4/analysis_freeze.py",
    "tools/research/v6/e4/analyze_e4.py",
    "tools/research/v6/e4/cell_metrics.py",
    "tools/research/v6/e4/contest_classes.json",
    "tools/research/v6/e4/contest_classes.py",
    "tools/research/v6/e4/gates.py",
    "tools/research/v6/e4/matrix.py",
    "tools/research/v6/e4/populations.py",
    "tools/research/v6/e4/preregistration.json",
    "tools/research/v6/e4/preregistration.py",
    "tools/research/v6/e4/telemetry.py",
)
E5_FILES: tuple[str, ...] = (
    "tools/research/v6/e5/analysis_freeze.py",
    ANALYSIS_FILE,
    CELL_METRICS_FILE,
    "tools/research/v6/e5/gates.py",
    "tools/research/v6/e5/matrix.py",
    "tools/research/v6/e5/nonmatrix_gates.py",
    "tools/research/v6/e5/populations.py",
    "tools/research/v6/e5/preregistration.json",
    "tools/research/v6/e5/preregistration.py",
    "tools/research/v6/e5/run_e5.py",
    "tools/research/v6/e5/telemetry.py",
)
# E4's committed control populations (P-PAR-E5's source) are data, pinned by E4's freeze.
E4_POPULATIONS_FILE = "tools/research/v6/e4/control_populations.json"
TOOLING_FILES: tuple[str, ...] = (*REUSED_FILES, E4_POPULATIONS_FILE, *E5_FILES)
MATCH_GENERATION_PATH = e4_freeze.MATCH_GENERATION_PATH


class AnalysisFreezeError(RuntimeError):
    """The E5 analysis instrument does not match its frozen identity."""


file_sha256 = e4_freeze.file_sha256
git_text = e4_freeze.git_text


def e4_freeze_record(repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    record: dict[str, Any] = json.loads((repo_root / E4_FREEZE_FILE).read_text(encoding="utf-8"))
    return record


def check_reused_unchanged() -> None:
    """E4's own reuse check (capture analyzer v2 and every E3 file it pins), then every
    reused file and E4's control populations against E4 freeze v1's pins."""
    try:
        e4_freeze.check_reused_unchanged()
    except e4_freeze.AnalysisFreezeError as exc:
        raise AnalysisFreezeError(str(exc)) from None
    record = e4_freeze_record()
    pinned = record["identity"]["tooling_sha256"]
    changed = sorted(path for path in REUSED_FILES if file_sha256(path) != pinned.get(path))
    if changed:
        raise AnalysisFreezeError(f"reused files differ from E4 freeze {record['freeze_id']}: {changed}")
    populations = (record.get("control_qualification") or {}).get("populations") or {}
    if file_sha256(E4_POPULATIONS_FILE) != populations.get("sha256"):
        raise AnalysisFreezeError(f"{E4_POPULATIONS_FILE} differs from E4 freeze {record['freeze_id']}'s pin")


def identity_inputs(*, tooling_source_sha: str, match_generation_tree: str) -> dict[str, Any]:
    """The inputs the freeze identity is a digest of, read from the live checkout."""
    e4_record = e4_freeze_record()
    return {
        "freeze_version": FREEZE_VERSION,
        "matrix_id": matrix.matrix_id(),
        "matrix_digest": matrix.E5_MATRIX_DIGEST,
        "matches_total": matrix.matches_total(),
        "preregistration_sha256": preregistration_digest(),
        "e5_analysis_version": E5_ANALYSIS_VERSION,
        "e5_analysis_sha256": file_sha256(ANALYSIS_FILE),
        "e5_cell_metrics_version": E5_CELL_METRICS_VERSION,
        "e5_cell_metrics_sha256": file_sha256(CELL_METRICS_FILE),
        "e4_cell_metrics_version": E4_CELL_METRICS_VERSION,
        "action_parity_version": E3_ACTION_PARITY_VERSION,
        "capture_analyzer_version": CAPTURE_ANALYZER_VERSION,
        "reused_e4_freeze_id": e4_record["freeze_id"],
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
    return f"v6-e5-freeze-v{identity['freeze_version']}-{freeze_digest(identity)[:12]}"


def build_freeze_record(identity: dict[str, Any], control_qualification: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "schema": FREEZE_SCHEMA,
        "status": "frozen before any T-E5 or T-E5K1 matrix data exists",
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
        raise AnalysisFreezeError(f"No E5 analysis freeze record at {path}; freeze the analysis first.")
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
        raise AnalysisFreezeError("E5 analysis freeze does not hold: " + "; ".join(problems))
    return record


def verify_execution_source(record: dict[str, Any]) -> None:
    """Before any E5 match runs: a clean tree, engine source identical to the frozen
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
        raise AnalysisFreezeError("E5 execution source check failed: " + "; ".join(problems))
