"""Canonical ``battle2.result`` models, serialization, and compatibility."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
import uuid
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from battle_engine.rules import BYTEFRAY_RULESET_ID, RulesetProvenance

SCHEMA_NAME = "battle2.result"
# ``battle2.result`` is retained as an established compatibility identifier,
# not introduced as a new product-facing name. Released artifacts from v0.3.0
# through V5 Alpha 1 already use it; changing only the v2 writer to
# ``bytefray.result`` would split one continuing result contract into two
# schema families. New, unrelated public artifact contracts should use the
# Bytefray product name instead.
SCHEMA_VERSION_V1 = 1
SCHEMA_VERSION_V2 = 2
SCHEMA_VERSION = SCHEMA_VERSION_V2
SUPPORTED_SCHEMA_VERSIONS = (SCHEMA_VERSION_V1, SCHEMA_VERSION_V2)


def generate_occurrence_id() -> str:
    """Return a new opaque identity for one completed match execution."""

    return str(uuid.uuid4())


def utc_completed_at() -> str:
    """Return the canonical UTC completion timestamp for a new result."""

    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace(
        "+00:00", "Z"
    )


def _validate_occurrence_id(value: object) -> str:
    if not isinstance(value, str):
        raise ValueError(
            "battle2.result v2 occurrence_id must be a canonical UUID string"
        )
    try:
        parsed = uuid.UUID(value)
    except (AttributeError, ValueError) as exc:
        raise ValueError(
            "battle2.result v2 occurrence_id must be a canonical UUID string"
        ) from exc
    if str(parsed) != value:
        raise ValueError(
            "battle2.result v2 occurrence_id must be a canonical UUID string"
        )
    return value


def _validate_completed_at(value: object) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(
            "battle2.result v2 completed_at must be a timezone-aware UTC ISO-8601 string"
        )
    candidate = f"{value[:-1]}+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError as exc:
        raise ValueError(
            "battle2.result v2 completed_at must be a timezone-aware UTC ISO-8601 string"
        ) from exc
    if parsed.tzinfo is None or parsed.utcoffset() != timedelta(0):
        raise ValueError(
            "battle2.result v2 completed_at must be a timezone-aware UTC ISO-8601 string"
        )
    return value


def _validate_product_version(value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("battle2.result v2 product_version must be a non-empty string")
    return value


def canonical_json(value: Mapping[str, Any]) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def stable_id(prefix: str, value: Mapping[str, Any]) -> str:
    return f"{prefix}_{hashlib.sha256(canonical_json(value)).hexdigest()[:24]}"


@dataclass(frozen=True)
class ReplayReference:
    replay_id: str
    sha256: str
    filename: str


@dataclass(frozen=True)
class ResultEnvelope:
    result_id: str
    match_id: str
    mode: str
    winner: str
    termination_reason: str
    ticks: int
    score: Mapping[str, int | float] = field(default_factory=dict)
    entrants: tuple[Mapping[str, Any], ...] = ()
    reproducibility: Mapping[str, Any] = field(default_factory=dict)
    replay: ReplayReference | None = None
    backend: Mapping[str, Any] | None = None
    # v0.10 Phase 4: the Bytefray gameplay Ruleset identity this match
    # actually executed under (``battle_engine.rules.BYTEFRAY_RULESET_ID``
    # for a current native VM/Python match). Additive to battle2.result v1
    # -- unknown keys have always been tolerated by every released reader
    # (see docs/RESULT_SCHEMA.md), so no schema bump was required. ``None``
    # for a pMARS/redcode94 result (Bytefray Ruleset v1 is never applicable
    # to Redcode execution -- see docs/RULES.md) and for any result written
    # before this field existed; use :func:`resolve_result_ruleset` to
    # recover a confidence-qualified answer for the latter case rather than
    # treating an absent field as "unknown gameplay" by itself.
    ruleset_id: str | None = None
    # V5 Replay History Phase 7A: occurrence metadata is deliberately
    # excluded from deterministic match/result/replay identity. Historical
    # v1 envelopes leave all three values as ``None``.
    occurrence_id: str | None = None
    completed_at: str | None = None
    product_version: str | None = None
    # Defaults to v1 so existing programmatic construction of a historical
    # envelope remains source-compatible. Production match writers select
    # the current schema explicitly and provide its required metadata.
    schema_version: int = SCHEMA_VERSION_V1

    def __post_init__(self) -> None:
        if (
            type(self.schema_version) is not int
            or self.schema_version not in SUPPORTED_SCHEMA_VERSIONS
        ):
            raise ValueError(
                f"unsupported {SCHEMA_NAME} schema version {self.schema_version!r}; "
                f"supported versions are {SUPPORTED_SCHEMA_VERSIONS}"
            )
        if self.schema_version == SCHEMA_VERSION_V2:
            _validate_occurrence_id(self.occurrence_id)
            _validate_completed_at(self.completed_at)
            _validate_product_version(self.product_version)
        elif any(
            value is not None
            for value in (self.occurrence_id, self.completed_at, self.product_version)
        ):
            raise ValueError("battle2.result v1 cannot carry v2 occurrence metadata")

    def as_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "schema": SCHEMA_NAME,
            "schema_version": self.schema_version,
            "result_id": self.result_id,
            "match_id": self.match_id,
            "mode": self.mode,
            "status": "completed",
            "winner": self.winner,
            "termination_reason": self.termination_reason,
            "ticks": self.ticks,
            "score": dict(self.score),
            "entrants": [dict(entrant) for entrant in self.entrants],
            "reproducibility": dict(self.reproducibility),
            "replay": (
                None
                if self.replay is None
                else {
                    "replay_id": self.replay.replay_id,
                    "sha256": self.replay.sha256,
                    "filename": self.replay.filename,
                }
            ),
            "backend": None if self.backend is None else dict(self.backend),
            "ruleset_id": self.ruleset_id,
        }
        if self.schema_version == SCHEMA_VERSION_V2:
            payload.update(
                {
                    "occurrence_id": self.occurrence_id,
                    "completed_at": self.completed_at,
                    "product_version": self.product_version,
                }
            )
        return payload


def write_json_atomic(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(json.dumps(value, indent=2, sort_keys=True).encode("utf-8"))
            stream.write(b"\n")
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def read_result(path: str | Path) -> ResultEnvelope:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("battle2.result JSON root must be an object")
    if data.get("schema") != SCHEMA_NAME:
        raise ValueError(f"unsupported result schema identifier {data.get('schema')!r}")
    schema_version = data.get("schema_version")
    if type(schema_version) is not int or schema_version not in SUPPORTED_SCHEMA_VERSIONS:
        raise ValueError(
            f"unsupported {SCHEMA_NAME} schema version {schema_version!r}; "
            f"supported versions are {SUPPORTED_SCHEMA_VERSIONS}"
        )
    occurrence_id: str | None = None
    completed_at: str | None = None
    product_version: str | None = None
    if schema_version == SCHEMA_VERSION_V2:
        occurrence_id = _validate_occurrence_id(data.get("occurrence_id"))
        completed_at = _validate_completed_at(data.get("completed_at"))
        product_version = _validate_product_version(data.get("product_version"))
    replay = data.get("replay")
    return ResultEnvelope(
        result_id=data["result_id"],
        match_id=data["match_id"],
        mode=data["mode"],
        winner=data["winner"],
        termination_reason=data["termination_reason"],
        ticks=int(data["ticks"]),
        score=data.get("score", {}),
        entrants=tuple(data.get("entrants", ())),
        reproducibility=data.get("reproducibility", {}),
        replay=(
            None
            if replay is None
            else ReplayReference(replay["replay_id"], replay["sha256"], replay["filename"])
        ),
        backend=data.get("backend"),
        ruleset_id=data.get("ruleset_id"),
        occurrence_id=occurrence_id,
        completed_at=completed_at,
        product_version=product_version,
        schema_version=schema_version,
    )


# Native mode discriminators (``ResultEnvelope.mode``) for which a missing
# ``ruleset_id`` can be safely recovered as ``BYTEFRAY_RULESET_ID`` -- see
# docs/RULES.md's historical source-stability evidence, which covers the VM
# and Python runtimes identically across the entire ``battle2.result`` v1
# lifetime (the schema itself did not exist before v0.3.0, so there is no
# older, unproven era of "b2"-mode results to worry about).
_NATIVE_RECOVERABLE_MODES = frozenset({"b2"})


def resolve_result_ruleset(envelope: ResultEnvelope) -> RulesetProvenance:
    """Attribute a confidence-qualified Ruleset identity to one result.

    * ``ruleset_id`` present -> ``"recorded"`` with that exact value.
    * ``ruleset_id`` absent, native (``mode == "b2"``) -> ``"recovered"``
      ``BYTEFRAY_RULESET_ID`` (VM and Python alike -- see docs/RULES.md).
    * ``ruleset_id`` absent, pMARS (``mode == "redcode94"``) ->
      ``"not_applicable"``: Redcode/pMARS execution never runs under
      Bytefray Ruleset v1 and must never be stamped with it.
    * anything else (an unrecognized/corrupt ``mode``) -> ``"unknown"``.
    """

    if envelope.ruleset_id is not None:
        return RulesetProvenance(envelope.ruleset_id, "recorded")
    if envelope.mode == "redcode94":
        return RulesetProvenance(None, "not_applicable")
    if envelope.mode in _NATIVE_RECOVERABLE_MODES:
        return RulesetProvenance(BYTEFRAY_RULESET_ID, "recovered")
    return RulesetProvenance(None, "unknown")


class ReplayIntegrityError(ValueError):
    """A result's referenced replay is missing, unreadable, or digest-mismatched.

    Raised only by explicit verification calls (``verify_replay_digest``,
    ``verify_result_replay``) -- ``read_result`` itself never verifies the
    referenced replay, so reading historical results stays unaffected by
    this check unless a caller opts in at a canonical-artifact boundary.
    """

    def __init__(self, message: str, *, code: str):
        super().__init__(message)
        self.code = code


def verify_replay_digest(result: ResultEnvelope, replay_path: str | Path) -> str:
    """Verify ``replay_path`` matches the digest recorded on ``result``.

    Returns the recomputed digest on success. Raises ``ReplayIntegrityError``
    (with a stable ``code``) if the result has no replay reference, the file
    is missing or unreadable, or its digest does not match.
    """

    if result.replay is None:
        raise ReplayIntegrityError(
            "Result has no replay reference to verify (e.g. a pMARS match).",
            code="replay_reference_missing",
        )
    path = Path(replay_path)
    if not path.is_file():
        raise ReplayIntegrityError(
            f"Referenced replay file does not exist: {path}",
            code="replay_file_missing",
        )
    try:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as exc:
        raise ReplayIntegrityError(
            f"Referenced replay file could not be read: {path}: {exc}",
            code="replay_file_unreadable",
        ) from exc
    if digest != result.replay.sha256:
        raise ReplayIntegrityError(
            f"Replay digest mismatch for {path}: "
            f"expected {result.replay.sha256}, got {digest}",
            code="replay_digest_mismatch",
        )
    return digest


def verify_result_replay(path: str | Path) -> str:
    """Read a ``result.json`` at ``path`` and verify its replay's digest.

    The replay is resolved relative to ``path``'s parent directory, matching
    how ``ReplayReference.filename`` is always a bare, portable filename
    rather than an absolute path (see ``ReplayReference``).
    """

    result_path = Path(path)
    envelope = read_result(result_path)
    if envelope.replay is None:
        raise ReplayIntegrityError(
            "Result has no replay reference to verify (e.g. a pMARS match).",
            code="replay_reference_missing",
        )
    return verify_replay_digest(envelope, result_path.parent / envelope.replay.filename)
