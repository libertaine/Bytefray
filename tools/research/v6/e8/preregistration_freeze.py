"""The E8 pre-registration freeze identity (phase I8-0).

It pins, at the tooling commit, the artifacts that together form E8's
registration before any engine, agent, family, seed or matrix work exists:

* the markdown pre-registration, revision 2 (the authoritative wording);
* its transcription, ``preregistration.json``;
* the loader and the registered decision logic;
* their transcription, totality and invariant tests;
* the implementation plan.

It also pins what these fix without data: the 1,000 registered O-BOOT draws
(by digest) and the predicted census.

The identity is ``v6-e8-prereg-v1-<first 12 hex of the record digest>``, where
the digest is the SHA-256 of the canonical JSON of the record's body (sorted
keys, compact separators, UTF-8). File digests normalize CRLF to LF.

Loading fails closed unless the record's digest and identity recompute, every
pinned file still has its pinned digest, the transcription is the one the
loader pins, and the draws and census recompute. Later identities (the
structural matrix at I8-4, the analysis freeze at I8-5, the execution
identity at I8-6) carry this one; none exists yet, and no seed exists.
"""

from __future__ import annotations

import hashlib
import json
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from tools.research.v6.e8 import decision, preregistration

FREEZE_PATH = Path(__file__).with_name("preregistration_freeze.json")
SCHEMA = "bytefray.v6.e8.preregistration_freeze"
IDENTITY_PREFIX = "v6-e8-prereg-v1-"
ROOT = preregistration.REPOSITORY_ROOT

PINNED_FILES: tuple[str, ...] = (
    "docs/research/v6/V6_E8_ACTIVE_SPATIAL_SENSING_PREREGISTRATION.md",
    "tools/research/v6/e8/preregistration.json",
    "tools/research/v6/e8/__init__.py",
    "tools/research/v6/e8/preregistration.py",
    "tools/research/v6/e8/decision.py",
    "engine/tests/test_v6_e8_preregistration.py",
    "engine/tests/test_v6_e8_decision.py",
    "docs/research/v6/V6_E8_ACTIVE_SPATIAL_SENSING_IMPLEMENTATION_PLAN.md",
)


class FreezeError(RuntimeError):
    """The pre-registration freeze record does not recompute, or a pinned artifact changed."""


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def record_digest(body: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical(body)).hexdigest()


def identity(digest: str) -> str:
    return IDENTITY_PREFIX + digest[:12]


def draws_digest() -> str:
    """SHA-256 of the registered draws, one draw per line, positions separated by spaces, LF-terminated."""
    lines = "".join(" ".join(str(position) for position in draw) + "\n" for draw in decision.DRAWS)
    return hashlib.sha256(lines.encode("ascii")).hexdigest()


def body(tooling_commit: str) -> dict[str, Any]:
    """The record's body, recomputed from the live checkout."""
    registration = decision.REGISTRATION
    authority = registration["authority"]
    return {
        "experiment": "E8",
        "phase": "I8-0",
        "preregistration": {
            "document": authority["document"],
            "revision": authority["revision"],
            "registration_commit": authority["registration_commit"],
            "sha256": authority["document_sha256"],
            "historical": [dict(entry) for entry in authority["history"]],
        },
        "transcription": {"path": "tools/research/v6/e8/preregistration.json",
                          "sha256": preregistration.PREREGISTRATION_SHA256},
        "tooling_commit": tooling_commit,
        "files": {path: preregistration.file_digest(ROOT / path) for path in PINNED_FILES},
        "registered_draws": {"resamples": decision.RESAMPLES, "draws_per_resample": decision.SEED_COUNT,
                             "rng": registration["operationalizations"]["O-BOOT"]["rng"], "sha256": draws_digest()},
        "census_prediction": list(decision.census()),
        "later_identities": {
            "structural_matrix": "v6-e8-matrix-v1-<12 hex>, at I8-4",
            "analysis": "v6-e8-analysis-v1-<12 hex>, at I8-5",
            "execution": "v6-e8-exec-v1-<12 hex>, at I8-6",
        },
        "seeds": "none exist",
    }


def record(tooling_commit: str) -> dict[str, Any]:
    content = body(tooling_commit)
    digest = record_digest(content)
    return {"schema": SCHEMA, "version": 1, "identity": identity(digest), "digest": digest, "body": content}


def load_freeze(path: Path = FREEZE_PATH) -> Mapping[str, Any]:
    """The frozen record, deeply immutable; fails closed on any drift."""
    stored = preregistration.parse(path.read_text(encoding="utf-8"))
    problems: list[str] = []
    if stored.get("schema") != SCHEMA or stored.get("version") != 1:
        problems.append("not an E8 pre-registration freeze record, version 1")
    digest = record_digest(stored["body"])
    if digest != stored["digest"]:
        problems.append(f"the record's body digest {digest} is not the stored {stored['digest']}")
    if identity(stored["digest"]) != stored["identity"]:
        problems.append(f"the identity {stored['identity']} does not follow from the digest")
    live = body(stored["body"]["tooling_commit"])
    for key in sorted(set(live) | set(stored["body"])):
        if live.get(key) != stored["body"].get(key):
            problems.append(f"{key}: live {live.get(key)!r} != frozen {stored['body'].get(key)!r}")
    if problems:
        raise FreezeError("E8 pre-registration freeze: " + "; ".join(problems))
    frozen: Mapping[str, Any] = preregistration.freeze(stored)
    return frozen


if __name__ == "__main__":  # pragma: no cover - the one-time write, at I8-0
    if len(sys.argv) != 3 or sys.argv[1] != "--write":
        raise SystemExit("usage: python -m tools.research.v6.e8.preregistration_freeze --write <tooling commit>")
    if FREEZE_PATH.exists():
        raise SystemExit(f"{FREEZE_PATH} exists; a freeze is written once")
    FREEZE_PATH.write_text(json.dumps(record(sys.argv[2]), ensure_ascii=False, indent=2) + "\n", encoding="utf-8",
                           newline="\n")
    print(json.loads(FREEZE_PATH.read_text(encoding="utf-8"))["identity"])
