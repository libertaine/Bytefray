"""The frozen E6 analysis identity (freeze v2).

Two identities are kept apart, the E2-E5 convention. The matrix identities
(``matrix.py``: structural, and then execution once seeds exist) say which
matches the experiment runs. The freeze identity says which complete
instrument interprets them. It carries:

* the structural matrix identity and digest, and the pre-registration
  SHA-256;
* the E6 analyzer, gate, re-derivation, telemetry and trace-index versions;
* the SHA-256 of every E6 tooling file, the family fingerprint record
  included;
* every reused E2-E5 analyzer file, each checked on every load against E5
  analysis freeze v1's pin (which itself checks E4's, E3's and E2's);
* the Git commit the tooling was qualified at, and the engine source tree
  that generates the matches;
* the I-0 parent byte-identity freeze (D-3);
* the freeze it supersedes, and what a trace re-execution is (below).

Freeze v2 follows amendment 1
(docs/research/v6/V6_E6_AMENDMENT_1_FAMILY_CORRECTIONS.md), which corrected
the family policy before any seed existed. ``analysis_freeze_v2.json`` is the
committed, operative record; loading it fails closed unless its digest
recomputes and every live input still equals the record. Freeze v1's record,
``analysis_freeze.json``, is kept byte for byte as a superseded pre-exposure
freeze: it never received seeds or data, and it no longer loads.

**Trace re-executions are reproductions, not observations.** The matrix has
11,520 registered cells. Each completed cell is re-executed at most once with
tracing on, and that trace is accepted only if the re-execution reproduces the
evaluated cell (replay SHA-256, ``match_id`` and ``result_id``); any
difference stops the experiment. A reproduction's telemetry describes the one
registered cell it reproduces. It never enters a payoff, bootstrap, outcome or
rate denominator as a cell of its own.
Two blocks sit outside the identity digest and are filled only by later,
separately authorized steps:

* ``seed_commitment``: the seed commitment and the execution matrix
  identity, and nothing else about the seeds (PR Sec 9, step 5). Added at
  I-7, before the first matrix cell.
* ``control_qualification``: the qualification record, added after the
  controls pass (Q). The treatment unlock requires it.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from tools.research.v6.e5 import analysis_freeze as e5_freeze
from tools.research.v6.e6 import matrix
from tools.research.v6.e6.analyze_e6 import E6_ANALYSIS_VERSION
from tools.research.v6.e6.gates import GATES_VERSION
from tools.research.v6.e6.preregistration import preregistration_digest
from tools.research.v6.e6.rederive import REDERIVE_VERSION
from tools.research.v6.e6.telemetry import TELEMETRY_VERSION
from tools.research.v6.e6.traces import TRACE_INDEX_VERSION
from tools.research.v6.experiment_harness import REPO_ROOT

FREEZE_VERSION = 2
FREEZE_SCHEMA = "bytefray.v6.e6.analysis_freeze"
FREEZE_RECORD_PATH = Path(__file__).with_name("analysis_freeze_v2.json")
#: Freeze v1, superseded by amendment 1 before any seed existed; kept byte for byte.
SUPERSEDED_RECORD = "tools/research/v6/e6/analysis_freeze.json"
SUPERSEDED_FREEZE_ID = "v6-e6-freeze-v1-428033032ce2"
AMENDMENT_PATH = "docs/research/v6/V6_E6_AMENDMENT_1_FAMILY_CORRECTIONS.md"
MATCH_GENERATION_PATH = "engine/src"

# E2-E5 files E6 imports unchanged; each must equal E5 freeze v1's pin.
REUSED_FILES: tuple[str, ...] = (
    "tools/research/v6/experiment_harness.py",
    "tools/research/v6/e2/capture_analyzer.py",
    "tools/research/v6/e2/matrix.py",
    "tools/research/v6/e3/action_parity.py",
    "tools/research/v6/e3/analyze_e3.py",
    "tools/research/v6/e3/gates.py",
    "tools/research/v6/e3/matrix.py",
    "tools/research/v6/e4/analyze_e4.py",
    "tools/research/v6/e4/cell_metrics.py",
    "tools/research/v6/e4/gates.py",
    "tools/research/v6/e4/matrix.py",
    "tools/research/v6/e5/analysis_freeze.py",
)
E6_FILES: tuple[str, ...] = (
    "tools/research/v6/e6/analysis_freeze.py",
    "tools/research/v6/e6/analyze_e6.py",
    "tools/research/v6/e6/describe.py",
    "tools/research/v6/e6/discipline.py",
    "tools/research/v6/e6/family.py",
    "tools/research/v6/e6/family_fingerprints.json",
    "tools/research/v6/e6/gates.py",
    "tools/research/v6/e6/interpretation.py",
    "tools/research/v6/e6/matrix.py",
    "tools/research/v6/e6/payoff.py",
    "tools/research/v6/e6/preregistration.json",
    "tools/research/v6/e6/preregistration.py",
    "tools/research/v6/e6/rederive.py",
    "tools/research/v6/e6/run_e6.py",
    "tools/research/v6/e6/seeds.py",
    "tools/research/v6/e6/telemetry.py",
    "tools/research/v6/e6/traces.py",
)
TOOLING_FILES: tuple[str, ...] = (*REUSED_FILES, *E6_FILES)
PENDING = {"status": "PENDING"}
SEED_BLOCK_KEYS = frozenset({"seed_commitment", "execution_matrix_identity", "generated_at_utc", "tool_commit"})


class AnalysisFreezeError(RuntimeError):
    """The E6 analysis instrument, or its record, does not match its frozen identity."""


file_sha256 = e5_freeze.file_sha256
git_text = e5_freeze.git_text


def e5_freeze_record(repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    record: dict[str, Any] = json.loads(e5_freeze.FREEZE_RECORD_PATH.read_text(encoding="utf-8"))
    return record


def check_reused_unchanged() -> None:
    """E5's own reuse chain, then every E6-reused file against E5 freeze v1's pins."""
    try:
        e5_freeze.check_reused_unchanged()
    except e5_freeze.AnalysisFreezeError as exc:
        raise AnalysisFreezeError(str(exc)) from None
    record = e5_freeze_record()
    pinned = record["identity"]["tooling_sha256"]
    changed = sorted(path for path in REUSED_FILES if file_sha256(path) != pinned.get(path))
    if changed:
        raise AnalysisFreezeError(f"reused files differ from E5 freeze {record['freeze_id']}: {changed}")


def superseded() -> dict[str, Any]:
    """The freeze this one replaces: its id, its record's SHA-256, its matrix, and why."""
    return {
        "freeze_id": SUPERSEDED_FREEZE_ID,
        "record": SUPERSEDED_RECORD,
        "record_sha256": file_sha256(SUPERSEDED_RECORD),
        "structural_matrix_id": matrix.SUPERSEDED_STRUCTURAL_MATRIX["id"],
        "reason": AMENDMENT_PATH,
    }


def trace_verification() -> dict[str, Any]:
    """What a bound trace re-execution is, in the frozen instrument."""
    return {
        "registered_matrix_cells": matrix.matches_total(),
        "trace_reproductions_at_most": matrix.matches_total(),
        "accepted_only_if_equal": ["replay_sha256", "match_id", "result_id"],
        "on_difference": "stop",
        "reproductions_are_observations": False,
        "never_enter": ["payoff", "bootstrap", "outcome", "rate denominators"],
    }


def identity_inputs(*, tooling_source_sha: str, match_generation_tree: str) -> dict[str, Any]:
    return {
        "freeze_version": FREEZE_VERSION,
        "structural_matrix_id": matrix.matrix_id(),
        "structural_digest": matrix.STRUCTURAL_DIGEST,
        "matches_total": matrix.matches_total(),
        "preregistration_sha256": preregistration_digest(),
        "e6_analysis_version": E6_ANALYSIS_VERSION,
        "e6_gates_version": GATES_VERSION,
        "e6_rederive_version": REDERIVE_VERSION,
        "e6_telemetry_version": TELEMETRY_VERSION,
        "e6_trace_index_version": TRACE_INDEX_VERSION,
        "reused_e5_freeze_id": e5_freeze_record()["freeze_id"],
        "tooling_sha256": {path: file_sha256(path) for path in TOOLING_FILES},
        "tooling_source_sha": tooling_source_sha,
        "match_generation_path": MATCH_GENERATION_PATH,
        "match_generation_tree": match_generation_tree,
        "parent_freeze": dict(sorted(matrix.PARENT_FREEZE.items())),
        "supersedes": superseded(),
        "trace_verification": trace_verification(),
    }


def freeze_digest(identity: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(identity, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def freeze_id(identity: dict[str, Any]) -> str:
    return f"v6-e6-freeze-v{identity['freeze_version']}-{freeze_digest(identity)[:12]}"


def build_freeze_record(identity: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema": FREEZE_SCHEMA,
        "status": "frozen before any E6 seed or matrix cell exists",
        "freeze_id": freeze_id(identity),
        "freeze_digest": freeze_digest(identity),
        "identity": identity,
        "seed_commitment": dict(PENDING),
        "control_qualification": dict(PENDING),
    }


def candidate_record() -> dict[str, Any]:
    """The would-be freeze of the current clean checkout, before a record is committed."""
    if git_text("status", "--porcelain"):
        raise AnalysisFreezeError("A candidate analysis freeze needs a clean tracked tree.")
    check_reused_unchanged()
    return build_freeze_record(identity_inputs(
        tooling_source_sha=git_text("rev-parse", "HEAD"),
        match_generation_tree=git_text("rev-parse", f"HEAD:{MATCH_GENERATION_PATH}"),
    ))


def check_seed_block(block: dict[str, Any]) -> None:
    """The seed block is PENDING, or exactly the four permitted facts, with a recomputing identity."""
    if block == PENDING:
        return
    if set(block) != SEED_BLOCK_KEYS:
        raise AnalysisFreezeError(f"seed block carries {sorted(block)}, not exactly {sorted(SEED_BLOCK_KEYS)}")
    if matrix.execution_identity(block["seed_commitment"]) != block["execution_matrix_identity"]:
        raise AnalysisFreezeError("the execution matrix identity does not recompute from the seed commitment")


def load_freeze(path: Path = FREEZE_RECORD_PATH) -> dict[str, Any]:
    """The committed freeze record; fails closed on any drift from the live checkout."""
    if not path.is_file():
        raise AnalysisFreezeError(f"No E6 analysis freeze record at {path}; freeze the analysis first.")
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
        live = identity_inputs(tooling_source_sha=str(identity.get("tooling_source_sha")),
                               match_generation_tree=str(identity.get("match_generation_tree")))
        for key, value in live.items():
            if key == "tooling_sha256":
                recorded = identity.get(key) or {}
                changed = sorted(p for p in set(value) | set(recorded) if value.get(p) != recorded.get(p))
                if changed:
                    problems.append(f"tooling files changed since the freeze: {changed}")
            elif identity.get(key) != value:
                problems.append(f"{key} {identity.get(key)!r} != live {value!r}")
    if problems:
        raise AnalysisFreezeError("E6 analysis freeze does not hold: " + "; ".join(problems))
    check_seed_block(record.get("seed_commitment") or {})
    return record


def verify_execution_source(record: dict[str, Any]) -> None:
    """Before any E6 match runs: a clean tree, engine source identical to the frozen
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
        raise AnalysisFreezeError("E6 execution source check failed: " + "; ".join(problems))
