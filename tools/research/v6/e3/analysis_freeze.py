"""The frozen E3 analysis identity (freeze v1).

Two identities are kept apart (the E2 convention). The matrix identity
(``matrix.py``) says which matches the experiment runs. The freeze identity
says which complete instrument interprets them: it carries the matrix id and
digest, the pre-registration digest, the E3 action/parity analyzer's version
and digest, the E3 analysis version, capture analyzer v2's version and digest
together with the E2 analysis freeze it was frozen under, the SHA-256 of every
analysis-tooling file, the Git commit those files were qualified at, and the
engine source tree that generates the matches. Repairing analysis tooling
changes the freeze identity, never the matrix identity.

``analysis_freeze.json`` is the committed freeze record. Loading it fails
closed unless its digest recomputes, every live input still equals the
record, and capture analyzer v2 is still byte-identical to the one E2's
freeze v2 pinned. Its ``control_qualification`` block (outside the identity
digest) is added after the controls pass, and names the gate records and the
frozen control populations the treatment unlock requires.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from tools.research.v6.e2.capture_analyzer import CAPTURE_ANALYZER_VERSION
from tools.research.v6.e3 import matrix
from tools.research.v6.e3.action_parity import E3_ACTION_PARITY_VERSION
from tools.research.v6.e3.analyze_e3 import E3_ANALYSIS_VERSION
from tools.research.v6.e3.preregistration import preregistration_digest
from tools.research.v6.experiment_harness import REPO_ROOT

FREEZE_VERSION = 1
FREEZE_SCHEMA = "bytefray.v6.e3.analysis_freeze"
FREEZE_RECORD_PATH = Path(__file__).with_name("analysis_freeze.json")

CAPTURE_ANALYZER_FILE = "tools/research/v6/e2/capture_analyzer.py"
E2_FREEZE_FILE = "tools/research/v6/e2/analysis_freeze.json"
ACTION_PARITY_FILE = "tools/research/v6/e3/action_parity.py"
# The complete analysis instrument: every file whose content can change how an
# E3 match is planned, resolved, checked, gated or interpreted, including the
# E2 modules E3 reuses unchanged. The freeze record and the frozen control
# populations are derived records outside this digest.
TOOLING_FILES: tuple[str, ...] = (
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
    "tools/research/v6/e3/preregistration.json",
    "tools/research/v6/e3/preregistration.py",
    "tools/research/v6/e3/run_e3.py",
    "tools/research/v6/e3/telemetry.py",
    "tools/research/v6/e3/fixtures/agents/e3_jam_sniper/agent.py",
    "tools/research/v6/e3/fixtures/agents/e3_jam_sniper/agent.yaml",
    "tools/research/v6/e3/fixtures/agents/e3_jam_sniper_twin/agent.py",
    "tools/research/v6/e3/fixtures/agents/e3_jam_sniper_twin/agent.yaml",
)
MATCH_GENERATION_PATH = "engine/src"


class AnalysisFreezeError(RuntimeError):
    """The E3 analysis instrument does not match its frozen identity."""


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data.replace(b"\r\n", b"\n")).hexdigest()


def file_sha256(relative: str, repo_root: Path = REPO_ROOT) -> str:
    """SHA-256 of a repository file with line endings normalized to LF."""
    return _sha256((repo_root / relative).read_bytes())


def _git(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=REPO_ROOT)


def git_text(*args: str) -> str:
    return _git(*args).decode("utf-8").strip()


def e2_capture_analyzer_identity(repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    """Capture analyzer v2 as E2's committed freeze v2 pinned it."""
    record = json.loads((repo_root / E2_FREEZE_FILE).read_text(encoding="utf-8"))
    identity = record["identity"]
    return {
        "e2_freeze_id": record["freeze_id"],
        "capture_analyzer_version": identity["capture_analyzer_version"],
        "capture_analyzer_sha256": identity["capture_analyzer_sha256"],
    }


def identity_inputs(*, tooling_source_sha: str, match_generation_tree: str) -> dict[str, Any]:
    """The inputs the freeze identity is a digest of, read from the live checkout."""
    return {
        "freeze_version": FREEZE_VERSION,
        "matrix_id": matrix.matrix_id(),
        "matrix_digest": matrix.E3_MATRIX_DIGEST,
        "matches_total": matrix.matches_total(),
        "preregistration_sha256": preregistration_digest(),
        "action_parity_version": E3_ACTION_PARITY_VERSION,
        "action_parity_sha256": file_sha256(ACTION_PARITY_FILE),
        "analysis_version": E3_ANALYSIS_VERSION,
        "capture_analyzer_version": CAPTURE_ANALYZER_VERSION,
        "capture_analyzer_sha256": file_sha256(CAPTURE_ANALYZER_FILE),
        "capture_analyzer_e2_freeze_id": e2_capture_analyzer_identity()["e2_freeze_id"],
        "tooling_sha256": {path: file_sha256(path) for path in TOOLING_FILES},
        "tooling_source_sha": tooling_source_sha,
        "match_generation_path": MATCH_GENERATION_PATH,
        "match_generation_tree": match_generation_tree,
    }


def freeze_digest(identity: dict[str, Any]) -> str:
    canonical = json.dumps(identity, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def freeze_id(identity: dict[str, Any]) -> str:
    return f"v6-e3-freeze-v{identity['freeze_version']}-{freeze_digest(identity)[:12]}"


def build_freeze_record(identity: dict[str, Any], control_qualification: dict[str, Any] | None = None) -> dict[str, Any]:
    """A freeze record; ``control_qualification`` summarizes control-data evidence
    and is outside the identity digest."""
    return {
        "schema": FREEZE_SCHEMA,
        "status": "frozen before any T-E3 or T-E3K1 matrix data exists",
        "freeze_id": freeze_id(identity),
        "freeze_digest": freeze_digest(identity),
        "identity": identity,
        "control_qualification": control_qualification or {"status": "PENDING"},
    }


def candidate_identity() -> dict[str, Any]:
    """The would-be freeze of the current clean checkout, before a record is committed."""
    if git_text("status", "--porcelain"):
        raise AnalysisFreezeError("A candidate analysis freeze needs a clean tracked tree.")
    identity = identity_inputs(
        tooling_source_sha=git_text("rev-parse", "HEAD"),
        match_generation_tree=git_text("rev-parse", f"HEAD:{MATCH_GENERATION_PATH}"),
    )
    return build_freeze_record(identity)


def check_capture_analyzer_unchanged() -> None:
    pinned = e2_capture_analyzer_identity()
    live = (CAPTURE_ANALYZER_VERSION, file_sha256(CAPTURE_ANALYZER_FILE))
    if live != (pinned["capture_analyzer_version"], pinned["capture_analyzer_sha256"]):
        raise AnalysisFreezeError(
            f"capture analyzer {live} is not E2 freeze {pinned['e2_freeze_id']}'s "
            f"{(pinned['capture_analyzer_version'], pinned['capture_analyzer_sha256'])}"
        )


def load_freeze(path: Path = FREEZE_RECORD_PATH) -> dict[str, Any]:
    """The committed freeze record; fails closed on any drift from the live checkout."""
    if not path.is_file():
        raise AnalysisFreezeError(f"No E3 analysis freeze record at {path}; freeze the analysis first.")
    check_capture_analyzer_unchanged()
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
        raise AnalysisFreezeError("E3 analysis freeze does not hold: " + "; ".join(problems))
    return record


def verify_execution_source(record: dict[str, Any]) -> None:
    """Before any E3 match runs: a clean tree, engine source identical to the
    frozen match-generation tree, and every tooling file identical to its
    content at the commit the freeze was qualified at."""
    identity = record["identity"]
    problems: list[str] = []
    if git_text("status", "--porcelain"):
        problems.append("the tracked tree is not clean")
    live_tree = git_text("rev-parse", f"HEAD:{identity['match_generation_path']}")
    if live_tree != identity["match_generation_tree"]:
        problems.append(
            f"{identity['match_generation_path']} tree {live_tree} differs from the frozen "
            f"{identity['match_generation_tree']}"
        )
    for path, digest in sorted(identity["tooling_sha256"].items()):
        try:
            committed = _sha256(_git("show", f"{identity['tooling_source_sha']}:{path}"))
        except subprocess.CalledProcessError:
            committed = None
        if committed != digest:
            problems.append(f"{path} at {identity['tooling_source_sha']} differs from the freeze")
    if problems:
        raise AnalysisFreezeError("E3 execution source check failed: " + "; ".join(problems))
