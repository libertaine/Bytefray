"""The frozen E8 analysis identity, v1 (phase I8-5).

docs/research/v6/V6_E8_ACTIVE_SPATIAL_SENSING_PREREGISTRATION.md (PR8) Sec 9 and
11, rule 7; implementation plan Sec 6 and 8. Two identities are kept apart,
the E2 to E6 convention. The matrix identities (``matrix.py``: structural, and
then execution once seeds exist) say which matches the experiment runs. This
freeze identity says which complete instrument runs and interprets them. Its
digest covers:

* the structural matrix identity and digest, the family freeze identity and
  record digest (I8-4), and the pre-registration freeze identity and record
  digest (I8-0), each of which must still load;
* the analyzer, gate, re-derivation, telemetry, trace and runner versions;
* the SHA-256 of every E8 tooling file (the runner, gates, analyzer, seed
  tooling, re-derivation, telemetry and traces among them) and of every reused
  E2 to E6 file;
* the SHA-256 of every E8 qualification test file, I8-0 to I8-5;
* the engine source the family was qualified on, which must equal the family
  freeze's;
* the commit the tooling was qualified at, the I8-1 parent freeze, and the
  conventions I8-5 fixed before any seed (``CONVENTIONS``).

The identity is ``v6-e8-analysis-v1-<first 12 hex of the digest>``. Loading
fails closed unless the digest and identity recompute and every live input
still equals the record.

Two blocks sit outside the identity digest and are filled only by later,
separately authorized steps:

* ``seed_commitment``: the seed commitment and the execution matrix identity,
  and nothing else about the seeds (PR8 Sec 9, step 5). Added at I8-6, before
  the first matrix cell.
* ``control_qualification``: the Q8 record's status and digest. The treatment
  unlock requires it.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from tools.research.v6.e8 import family_freeze, matrix, preregistration
from tools.research.v6.e8 import preregistration_freeze as prereg_freeze

FREEZE_VERSION = 1
FREEZE_SCHEMA = "bytefray.v6.e8.analysis_freeze"
IDENTITY_PREFIX = "v6-e8-analysis-v1-"
FREEZE_RECORD_PATH = Path(__file__).with_name("analysis_freeze.json")
ROOT = preregistration.REPOSITORY_ROOT
PENDING = {"status": "PENDING"}
SEED_BLOCK_KEYS = frozenset({"seed_commitment", "execution_matrix_identity", "generated_at_utc", "tool_commit"})
CONTROL_BLOCK_KEYS = frozenset({"status", "record_sha256"})

#: The E8 tooling the instrument consists of (the records it reads included).
E8_FILES: tuple[str, ...] = (
    "tools/research/v6/e8/__init__.py",
    "tools/research/v6/e8/analysis_freeze.py",
    "tools/research/v6/e8/analyze_e8.py",
    "tools/research/v6/e8/compatibility.py",
    "tools/research/v6/e8/decision.py",
    "tools/research/v6/e8/discipline.py",
    "tools/research/v6/e8/family.py",
    "tools/research/v6/e8/family_fingerprints.json",
    "tools/research/v6/e8/family_freeze.json",
    "tools/research/v6/e8/family_freeze.py",
    "tools/research/v6/e8/gates.py",
    "tools/research/v6/e8/matrix.py",
    "tools/research/v6/e8/parent_goldens.json",
    "tools/research/v6/e8/parent_goldens.py",
    "tools/research/v6/e8/payoff.py",
    "tools/research/v6/e8/preregistration.json",
    "tools/research/v6/e8/preregistration.py",
    "tools/research/v6/e8/preregistration_freeze.py",
    "tools/research/v6/e8/preregistration_freeze_v4.json",
    "tools/research/v6/e8/rederive.py",
    "tools/research/v6/e8/run_e8.py",
    "tools/research/v6/e8/seed_protocol.py",
    "tools/research/v6/e8/telemetry.py",
    "tools/research/v6/e8/traces.py",
)
#: Every E2 to E6 file E8 imports, directly or through another reused module, unchanged.
REUSED_FILES: tuple[str, ...] = (
    "tools/research/v6/experiment_harness.py",
    "tools/research/v6/e2/matrix.py",
    "tools/research/v6/e3/action_parity.py",
    "tools/research/v6/e3/analyze_e3.py",
    "tools/research/v6/e3/gates.py",
    "tools/research/v6/e4/analyze_e4.py",
    "tools/research/v6/e4/cell_metrics.py",
    "tools/research/v6/e4/gates.py",
    "tools/research/v6/e6/analyze_e6.py",
    "tools/research/v6/e6/describe.py",
    "tools/research/v6/e6/discipline.py",
    "tools/research/v6/e6/family.py",
    "tools/research/v6/e6/interpretation.py",
    "tools/research/v6/e6/payoff.py",
    "tools/research/v6/e6/rederive.py",
    "tools/research/v6/e6/telemetry.py",
    "tools/research/v6/e6/traces.py",
    "tools/research/v6/e6_audit/seat.py",
)
#: Every E8 qualification test file and harness, I8-0 to I8-5.
QUALIFICATION_FILES: tuple[str, ...] = (
    "engine/tests/_e8_family_engine_harness.py",
    "engine/tests/_e8_family_harness.py",
    "engine/tests/_e8_scripted_matrix.py",
    "engine/tests/_e8_sensing_harness.py",
    "engine/tests/test_ruleset_v6_research_sensing_active.py",
    "engine/tests/test_v6_e8_adapt8_freeze.py",
    "engine/tests/test_v6_e8_analysis.py",
    "engine/tests/test_v6_e8_decision.py",
    "engine/tests/test_v6_e8_family.py",
    "engine/tests/test_v6_e8_family_engine.py",
    "engine/tests/test_v6_e8_family_fixed_details.py",
    "engine/tests/test_v6_e8_family_freeze.py",
    "engine/tests/test_v6_e8_family_policy.py",
    "engine/tests/test_v6_e8_gates.py",
    "engine/tests/test_v6_e8_matrix.py",
    "engine/tests/test_v6_e8_parent_byte_identity.py",
    "engine/tests/test_v6_e8_preregistration.py",
    "engine/tests/test_v6_e8_preregistration_freeze.py",
    "engine/tests/test_v6_e8_runner.py",
    "engine/tests/test_v6_e8_seed_protocol.py",
    "engine/tests/test_v6_e8_sensing_context.py",
    "engine/tests/test_v6_e8_sensing_semantics.py",
    "engine/tests/test_v6_e8_traces.py",
)
#: The implementation details I8-5 fixed before any seed, recorded inside the identity.
CONVENTIONS: dict[str, str] = {
    "trace_capture": "a bound re-execution of every completed cell through agent_test.test_agent with trace=True, "
                     "accepted only if the replay bytes, match_id and result_id reproduce the evaluated cell and "
                     "the trace's BindingRecord names that replay (E6's approved route)",
    "pre_match_gate": "compatibility.require_compatible on every planned pairing and orientation of a field before "
                      "anything is written, on the copied packages before the field runs, and immediately before "
                      "every traced re-execution",
    "engine_source": "family_freeze.verify_engine_source before any cell runs, and again after a field",
    "P8-11": "every cell's trace is kept, gzip-compressed; no retention subset (D8-12)",
    "P8-13": "traces are stored with CRLF normalized to LF; trace_sha256 is over the LF bytes; the raw form is recorded",
    "D8-8_information": "a visible set, a delivered SENSE tuple or a delivered READ result showing an opponent-owned "
                        "core cell counts from the row whose observation delivers it",
    "D8-5_write_log": "the replay's per-tick diffs expanded to byte writes equal the traced applied WRITEs, in order",
    "O-VERIF_median": "the exact median over the seeds (statistics.median over Fractions, E4 and E5's convention)",
    "seat_resampling": "E6 post-hoc audit seat.pairing_metrics and seat.mirror_metrics per resample, checked "
                       "against E4's seat metrics at the point estimate",
    "seed_filter": "every output before the reveal is redacted by seed value (seed_protocol.SeedGuard)",
}


class AnalysisFreezeError(RuntimeError):
    """The E8 analysis instrument, or its record, does not match its frozen identity."""


def file_sha256(path: str) -> str:
    return preregistration.file_digest(ROOT / path)


def git_text(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def versions() -> dict[str, int]:
    from tools.research.v6.e8 import analyze_e8, gates, rederive, run_e8, telemetry, traces

    return {"analysis": analyze_e8.E8_ANALYSIS_VERSION, "gates": gates.GATES_VERSION,
            "rederive": rederive.REDERIVE_VERSION, "telemetry": telemetry.TELEMETRY_VERSION,
            "traces": traces.TRACES_VERSION, "trace_index": traces.TRACE_INDEX_VERSION,
            "runner": run_e8.E8_RUNNER_VERSION}


def identity_inputs(*, tooling_source_sha: str) -> dict[str, Any]:
    family = family_freeze.load_freeze()
    prereg = prereg_freeze.load_freeze()
    return {
        "freeze_version": FREEZE_VERSION,
        "structural_matrix_id": matrix.matrix_id(),
        "structural_digest": matrix.STRUCTURAL_DIGEST,
        "matches_total": matrix.matches_total(),
        "family_freeze": {"identity": family["identity"], "record_sha256": file_sha256(
            "tools/research/v6/e8/family_freeze.json")},
        "preregistration_freeze": {"identity": prereg["identity"], "record_sha256": file_sha256(
            "tools/research/v6/e8/preregistration_freeze_v4.json")},
        "versions": versions(),
        "tooling_sha256": {path: file_sha256(path) for path in E8_FILES},
        "reused_sha256": {path: file_sha256(path) for path in REUSED_FILES},
        "qualification_sha256": {path: file_sha256(path) for path in QUALIFICATION_FILES},
        "engine_source": family_freeze.engine_source(),
        "tooling_source_sha": tooling_source_sha,
        "parent_freeze": matrix.parent_freeze(),
        "conventions": dict(CONVENTIONS),
    }


def freeze_digest(identity: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(identity, sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=False).encode("utf-8")).hexdigest()


def freeze_id(identity: dict[str, Any]) -> str:
    return IDENTITY_PREFIX + freeze_digest(identity)[:12]


def build_freeze_record(identity: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema": FREEZE_SCHEMA,
        "status": "frozen before any E8 seed or matrix cell exists",
        "freeze_id": freeze_id(identity),
        "freeze_digest": freeze_digest(identity),
        "identity": identity,
        "seed_commitment": dict(PENDING),
        "control_qualification": dict(PENDING),
    }


def check_seed_block(block: dict[str, Any]) -> None:
    """The seed block is PENDING, or exactly the four permitted facts, with a recomputing identity."""
    if block == PENDING:
        return
    if set(block) != SEED_BLOCK_KEYS:
        raise AnalysisFreezeError(f"seed block carries {sorted(block)}, not exactly {sorted(SEED_BLOCK_KEYS)}")
    from tools.research.v6.e8 import seed_protocol

    if seed_protocol.execution_identity(matrix.STRUCTURAL_DIGEST, block["seed_commitment"]) != block["execution_matrix_identity"]:
        raise AnalysisFreezeError("the execution matrix identity does not recompute from the seed commitment")


def check_control_block(block: dict[str, Any]) -> None:
    if block == PENDING:
        return
    if set(block) != CONTROL_BLOCK_KEYS or block["status"] not in ("PASS", "FAIL"):
        raise AnalysisFreezeError(f"control qualification block {sorted(block)} is not {sorted(CONTROL_BLOCK_KEYS)}")


def load_freeze(path: Path = FREEZE_RECORD_PATH) -> dict[str, Any]:
    """The committed freeze record; fails closed on any drift from the live checkout."""
    if not path.is_file():
        raise AnalysisFreezeError(f"No E8 analysis freeze record at {path}; freeze the analysis first (I8-5).")
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
        try:
            live = identity_inputs(tooling_source_sha=str(identity.get("tooling_source_sha")))
        except (family_freeze.FreezeError, prereg_freeze.FreezeError, matrix.MatrixDefinitionError) as exc:
            raise AnalysisFreezeError(f"E8 analysis freeze: an earlier freeze no longer holds: {exc}") from None
        for key, value in live.items():
            if key in ("tooling_sha256", "reused_sha256", "qualification_sha256"):
                recorded = identity.get(key) or {}
                changed = sorted(p for p in set(value) | set(recorded) if value.get(p) != recorded.get(p))
                if changed:
                    problems.append(f"{key}: files changed since the freeze: {changed}")
            elif identity.get(key) != value:
                problems.append(f"{key}: {identity.get(key)!r} != live {value!r}")
        family_engine = family_freeze.load_freeze()["body"]["engine_source"]
        if identity.get("engine_source") != dict(family_engine):
            problems.append("the frozen engine source is not the one the family was qualified on")
    if problems:
        raise AnalysisFreezeError("E8 analysis freeze does not hold: " + "; ".join(problems))
    try:
        check_seed_block(record.get("seed_commitment") or {})
        check_control_block(record.get("control_qualification") or {})
    except Exception as exc:  # the seed tooling's own errors included
        raise AnalysisFreezeError(f"E8 analysis freeze: {exc}") from None
    matrix.verify_frozen_matrix()
    return record


def verify_execution_source(record: dict[str, Any]) -> None:
    """Before any E8 match runs: a clean tree, the qualified engine, and every pinned tooling and reused
    file identical to its content at the commit the freeze was qualified at."""
    identity = record["identity"]
    problems: list[str] = []
    if git_text("status", "--porcelain"):
        problems.append("the tracked tree is not clean")
    if family_freeze.engine_source() != identity["engine_source"]:
        problems.append("the engine source differs from the frozen one")
    for key in ("tooling_sha256", "reused_sha256"):
        for path, digest in sorted(identity[key].items()):
            try:
                content = subprocess.check_output(["git", "show", f"{identity['tooling_source_sha']}:{path}"], cwd=ROOT)
                committed = hashlib.sha256(content.replace(b"\r\n", b"\n")).hexdigest()
            except subprocess.CalledProcessError:
                committed = None
            if committed != digest:
                problems.append(f"{path} at {identity['tooling_source_sha']} differs from the freeze")
    if problems:
        raise AnalysisFreezeError("E8 execution source check failed: " + "; ".join(problems))


if __name__ == "__main__":  # pragma: no cover - the one-time write, at I8-5
    if len(sys.argv) != 3 or sys.argv[1] != "--write":
        raise SystemExit("usage: python -m tools.research.v6.e8.analysis_freeze --write <tooling commit>")
    if FREEZE_RECORD_PATH.exists():
        raise SystemExit(f"{FREEZE_RECORD_PATH} exists; a freeze is written once")
    if git_text("status", "--porcelain"):
        raise SystemExit("an analysis freeze is written from a clean tree")
    record = build_freeze_record(identity_inputs(tooling_source_sha=sys.argv[2]))
    FREEZE_RECORD_PATH.write_text(json.dumps(record, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
                                  encoding="utf-8", newline="\n")
    print(record["freeze_id"])
