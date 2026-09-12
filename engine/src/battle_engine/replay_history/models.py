"""Qt-free domain model for one Replay History match occurrence.

Phase 6 selected a *hybrid artifact-backed match occurrence* as the history
object (``docs/research/v5/V5_REPLAY_HISTORY_PHASE6_ARCHITECTURE.md`` Sec C):
a valid ``result.json`` normally anchors the row, replay availability is a
capability of that occurrence rather than its identity, and a canonical
replay with no result still becomes a degraded entry.

Three identity concepts are kept deliberately separate and must not be
collapsed:

``match_id``
    Deterministic semantic match identity. Independent reruns of the same
    inputs legitimately share it, so it is never a row-uniqueness key.
``occurrence_id``
    One actual execution. Authoritative only for ``battle2.result`` v2; v1
    artifacts have none and receive a clearly-marked synthetic key instead
    (see :func:`synthetic_occurrence_key`).
``location_id``
    Index-local identity of one discovered artifact directory. It is a
    cache primary key, never displayed as if it were a persisted UUID.
"""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

# Bounded diagnostic text: a malformed artifact must never be able to push an
# unbounded parser message (or its own file content) into the cache.
MAX_DIAGNOSTIC_LENGTH = 300


class ResultHealth(str, Enum):
    """State of the ``result.json`` that anchors an occurrence."""

    VALID = "valid"
    MALFORMED = "malformed"
    UNSUPPORTED = "unsupported"
    INACCESSIBLE = "inaccessible"
    MISSING = "missing"


class ReplayState(str, Enum):
    """Current capability state of an occurrence's replay artifact.

    ``NOT_PRODUCED`` is the intentional-absence case (a pMARS/Redcode result
    records ``replay: null``); it is deliberately distinct from ``MISSING``,
    which means a replay was referenced and is not on disk right now.
    ``UNCHECKED`` exists for rows whose replay state could not be observed at
    all, so a future refresh can resolve it rather than a reader having to
    guess which of the other states applies.
    """

    AVAILABLE = "available"
    MISSING = "missing"
    NOT_PRODUCED = "not_produced"
    INVALID = "invalid"
    INACCESSIBLE = "inaccessible"
    UNCHECKED = "unchecked"


class EntryHealth(str, Enum):
    """Overall health of one history row.

    ``HEALTHY``
        A valid result whose replay is available or was never produced.
    ``DEGRADED``
        A valid result whose replay is referenced but missing, invalid, or
        unreadable. The match facts are complete; playback is not available.
    ``INCOMPLETE``
        No ``result.json`` at this location (replay-only). The primary
        metadata authority is absent, so outcome fields may be unknown.
    ``INVALID``
        The result exists but could not be interpreted.
    """

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    INCOMPLETE = "incomplete"
    INVALID = "invalid"


class TimestampConfidence(str, Enum):
    """Provenance of an occurrence's effective history timestamp (Phase 6 F)."""

    RECORDED = "recorded"
    DIRECTORY_INFERRED = "directory_inferred"
    FILESYSTEM_FALLBACK = "filesystem_fallback"
    UNKNOWN = "unknown"


class OccurrenceIdentitySource(str, Enum):
    """Whether an occurrence key is artifact truth or a cache-local surrogate."""

    RECORDED = "recorded"
    SYNTHETIC_LOCATION = "synthetic_location"


class OutcomeState(str, Enum):
    """Coarse, filterable outcome class for one occurrence."""

    WINNER = "winner"
    TIE = "tie"
    UNKNOWN = "unknown"


class WorkflowSource(str, Enum):
    """Normalized producer classification derived from run-tree location.

    These are stable internal identifiers for filtering and storage. Display
    labels belong to the presentation layer, not to the index.
    """

    DESIGNER = "designer"
    DEVELOPMENT = "development"
    TOURNAMENT = "tournament"
    EVALUATION = "evaluation"
    CLI_LATEST = "cli_latest"
    OTHER_RUN = "other_run"
    UNKNOWN = "unknown"


class DiagnosticCategory(str, Enum):
    """Bounded, stable classification of why an artifact is not fully usable."""

    RESULT_UNREADABLE = "result_unreadable"
    RESULT_TOO_LARGE = "result_too_large"
    RESULT_MALFORMED_JSON = "result_malformed_json"
    RESULT_INVALID_ROOT = "result_invalid_root"
    RESULT_UNSUPPORTED_SCHEMA = "result_unsupported_schema"
    RESULT_UNSUPPORTED_VERSION = "result_unsupported_version"
    RESULT_INVALID_FIELDS = "result_invalid_fields"
    RESULT_MISSING = "result_missing"
    REPLAY_MISSING = "replay_missing"
    REPLAY_UNREADABLE = "replay_unreadable"
    REPLAY_REFERENCE_UNSAFE = "replay_reference_unsafe"
    REPLAY_HEADER_UNREADABLE = "replay_header_unreadable"
    DIRECTORY_UNREADABLE = "directory_unreadable"
    LOOSE_SLOT_OVERWRITTEN = "loose_slot_overwritten"


# Namespace prefixes. Both are deliberately un-UUID-like so a synthetic value
# can never be mistaken for an authoritative ``result.json`` ``occurrence_id``.
LOCATION_ID_PREFIX = "loc"
SYNTHETIC_OCCURRENCE_PREFIX = "legacy-location"


def _location_digest(root_identity: str, relative_directory: str) -> str:
    payload = f"{root_identity}\x00{relative_directory}".encode()
    return hashlib.sha256(payload).hexdigest()[:24]


def location_id(root_identity: str, relative_directory: str) -> str:
    """Cache-local primary key for one discovered artifact directory.

    One run directory holds at most one occurrence under every canonical
    Bytefray layout, so the *directory* rather than a particular artifact file
    is the stable location. That keeps a row continuous when its
    ``result.json`` is deleted and only the replay remains.
    """

    return f"{LOCATION_ID_PREFIX}_{_location_digest(root_identity, relative_directory)}"


def synthetic_occurrence_key(root_identity: str, relative_directory: str) -> str:
    """Non-authoritative occurrence key for an artifact with no recorded UUID.

    Deterministic for the same discovered location, distinct from both
    ``match_id`` and ``location_id``'s own namespace, and never written back to
    any artifact. Two identical ``battle2.result`` v1 reruns stored in separate
    directories therefore remain two separate occurrences, which is exactly the
    fact ``match_id`` cannot express.
    """

    digest = _location_digest(root_identity, relative_directory)
    return f"{SYNTHETIC_OCCURRENCE_PREFIX}_{digest}"


def bounded_diagnostic(message: object, limit: int = MAX_DIAGNOSTIC_LENGTH) -> str:
    """Collapse and truncate an arbitrary error string for safe storage."""

    collapsed = " ".join(str(message).split())
    if len(collapsed) <= limit:
        return collapsed
    return collapsed[: limit - 1] + "…"


@dataclass(frozen=True)
class ArtifactFingerprint:
    """Cheap change-detection facts for one artifact file.

    This is a cache-invalidation hint, not an integrity claim -- digest
    verification stays an explicit, separate operation at the playback
    boundary (Phase 6 L/Y).
    """

    relative_path: str | None = None
    exists: bool = False
    size: int | None = None
    mtime_ns: int | None = None

    @property
    def signature(self) -> tuple[str | None, bool, int | None, int | None]:
        return (self.relative_path, self.exists, self.size, self.mtime_ns)


@dataclass(frozen=True)
class HistoryEntrant:
    """One ordered entrant as recorded by the anchoring artifact."""

    ordinal: int
    agent_id: str | None = None
    display_name: str | None = None
    runtime_kind: str | None = None
    api_version: int | None = None
    agent_version: str | None = None
    content_hash: str | None = None
    parameters: Mapping[str, Any] | None = None

    @property
    def label(self) -> str:
        return self.display_name or self.agent_id or "Unknown"

    def search_terms(self) -> tuple[str, ...]:
        return tuple(
            value.lower()
            for value in (self.display_name, self.agent_id)
            if isinstance(value, str) and value
        )


@dataclass(frozen=True)
class HistoryOccurrence:
    """One fully normalized Replay History occurrence.

    This is the single model produced by discovery and persisted by the index.
    Presentation strings are deliberately absent: enums and typed values are
    stored, and the GUI layer owns their display form.
    """

    # --- identity -----------------------------------------------------
    location_id: str
    occurrence_key: str
    occurrence_source: OccurrenceIdentitySource
    occurrence_id: str | None = None
    match_id: str | None = None
    result_id: str | None = None

    # --- time ---------------------------------------------------------
    effective_timestamp: str | None = None
    effective_timestamp_ns: int = 0
    timestamp_known: bool = False
    timestamp_confidence: TimestampConfidence = TimestampConfidence.UNKNOWN
    completed_at: str | None = None

    # --- entrants -----------------------------------------------------
    entrants: tuple[HistoryEntrant, ...] = ()

    # --- match --------------------------------------------------------
    ruleset_id: str | None = None
    ruleset_confidence: str = "unknown"
    seed: int | None = None
    mode: str | None = None
    configuration: Mapping[str, Any] = field(default_factory=dict)
    workflow: WorkflowSource = WorkflowSource.UNKNOWN
    durable_location: bool = True

    # --- outcome ------------------------------------------------------
    winner: str | None = None
    outcome_state: OutcomeState = OutcomeState.UNKNOWN
    score: Mapping[str, Any] = field(default_factory=dict)
    termination_reason: str | None = None
    ticks: int | None = None

    # --- artifact state ----------------------------------------------
    relative_directory: str = ""
    result_fingerprint: ArtifactFingerprint = ArtifactFingerprint()
    replay_fingerprint: ArtifactFingerprint = ArtifactFingerprint()
    replay_state: ReplayState = ReplayState.UNCHECKED
    replay_sha256: str | None = None
    replay_id: str | None = None
    result_health: ResultHealth = ResultHealth.MISSING
    entry_health: EntryHealth = EntryHealth.INVALID
    diagnostic_category: DiagnosticCategory | None = None
    diagnostic_message: str | None = None

    # --- versioning ---------------------------------------------------
    result_schema_version: int | None = None
    product_version: str | None = None
    replay_schema_version: int | None = None

    @property
    def entrant_count(self) -> int:
        return len(self.entrants)

    @property
    def entrant_summary(self) -> str:
        if not self.entrants:
            return ""
        return " vs ".join(entrant.label for entrant in self.entrants)

    @property
    def entrant_search(self) -> str:
        """Newline-joined lowercase entrant terms used by the search filter.

        Denormalized onto the occurrence row so a case-insensitive substring
        search is one single-table scan rather than a correlated subquery over
        the entrant child table; the structured child rows remain the source
        for detail display.
        """

        terms: list[str] = []
        for entrant in self.entrants:
            terms.extend(entrant.search_terms())
        return "\n".join(terms)


def classify_entry_health(result_health: ResultHealth, replay_state: ReplayState) -> EntryHealth:
    """Derive the single overall row health from its two component states."""

    if result_health is ResultHealth.VALID:
        if replay_state in (ReplayState.AVAILABLE, ReplayState.NOT_PRODUCED):
            return EntryHealth.HEALTHY
        return EntryHealth.DEGRADED
    if result_health is ResultHealth.MISSING:
        return EntryHealth.INCOMPLETE
    return EntryHealth.INVALID


__all__ = [
    "LOCATION_ID_PREFIX",
    "MAX_DIAGNOSTIC_LENGTH",
    "SYNTHETIC_OCCURRENCE_PREFIX",
    "ArtifactFingerprint",
    "DiagnosticCategory",
    "EntryHealth",
    "HistoryEntrant",
    "HistoryOccurrence",
    "OccurrenceIdentitySource",
    "OutcomeState",
    "ReplayState",
    "ResultHealth",
    "TimestampConfidence",
    "WorkflowSource",
    "bounded_diagnostic",
    "classify_entry_health",
    "location_id",
    "synthetic_occurrence_key",
]
