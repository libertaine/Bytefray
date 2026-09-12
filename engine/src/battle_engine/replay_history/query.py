"""Typed query, cursor, and row contracts for the Replay History index.

Callers describe *what* they want with :class:`HistoryQuery` and page through
results with :class:`HistoryCursor`. No SQL fragment, column name, or table
name crosses this boundary, so a GUI layer never composes a statement and no
user-supplied value can reach the database as anything but a bound parameter.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime

from .models import (
    EntryHealth,
    HistoryEntrant,
    HistoryOccurrence,
    OccurrenceIdentitySource,
    OutcomeState,
    ReplayState,
    ResultHealth,
    TimestampConfidence,
    WorkflowSource,
)

DEFAULT_PAGE_SIZE = 500
MAX_PAGE_SIZE = 5000


@dataclass(frozen=True)
class HistoryQuery:
    """One composed history filter.

    Every field is optional; ``None`` (or an empty sequence) means "do not
    constrain this dimension". All values are bound as SQL parameters.
    """

    #: Case-insensitive substring over entrant display names and agent IDs.
    entrant_text: str | None = None
    #: Exact recorded/recovered ruleset IDs. ``None`` inside the tuple matches
    #: rows with no ruleset identity at all (unknown or not applicable).
    ruleset_ids: Sequence[str | None] | None = None
    #: Narrow an unrecorded ruleset further: ``"not_applicable"`` vs
    #: ``"unknown"`` vs ``"recorded"``/``"recovered"``.
    ruleset_confidences: Sequence[str] | None = None
    #: Coarse outcome classes (winner / tie / unknown).
    outcome_states: Sequence[OutcomeState] | None = None
    #: One exact winner value as recorded by ``result.json``.
    winner: str | None = None
    #: Inclusive lower bound on the effective history timestamp.
    start: datetime | None = None
    #: Inclusive upper bound on the effective history timestamp.
    end: datetime | None = None
    #: Exact integer seed.
    seed: int | None = None
    #: Normalized producer categories.
    workflows: Sequence[WorkflowSource] | None = None
    #: Current replay capability states.
    replay_states: Sequence[ReplayState] | None = None
    #: Overall row health, covering the invalid/degraded cases.
    entry_healths: Sequence[EntryHealth] | None = None
    #: Deterministic match identity; several occurrences may share one.
    match_id: str | None = None
    #: Authoritative ``battle2.result`` v2 occurrence UUID.
    occurrence_id: str | None = None

    @property
    def has_date_bound(self) -> bool:
        return self.start is not None or self.end is not None


@dataclass(frozen=True, order=True)
class HistoryCursor:
    """Opaque keyset position in the default ordering.

    Carries exactly the ordering tuple ``(timestamp_known, effective
    timestamp, location_id)``. It is an internal typed value, deliberately not
    a serialized web-style token: Phase 7C passes the object it received
    straight back to fetch the following page.
    """

    timestamp_known: int
    effective_timestamp_ns: int
    location_id: str


@dataclass(frozen=True)
class HistoryRow:
    """Compact per-row projection for a history table."""

    location_id: str
    occurrence_key: str
    occurrence_id: str | None
    occurrence_source: OccurrenceIdentitySource
    match_id: str | None
    effective_timestamp: str | None
    effective_timestamp_ns: int
    timestamp_known: bool
    timestamp_confidence: TimestampConfidence
    entrant_summary: str
    entrant_count: int
    winner: str | None
    outcome_state: OutcomeState
    ruleset_id: str | None
    ruleset_confidence: str
    seed: int | None
    workflow: WorkflowSource
    durable_location: bool
    duplicate_occurrence_location: bool
    replay_state: ReplayState
    result_health: ResultHealth
    entry_health: EntryHealth
    diagnostic_category: str | None
    diagnostic_message: str | None

    @property
    def cursor(self) -> HistoryCursor:
        return HistoryCursor(
            timestamp_known=1 if self.timestamp_known else 0,
            effective_timestamp_ns=self.effective_timestamp_ns,
            location_id=self.location_id,
        )


@dataclass(frozen=True)
class HistoryPage:
    """One keyset page of history rows."""

    rows: tuple[HistoryRow, ...]
    next_cursor: HistoryCursor | None
    has_more: bool
    page_size: int

    def __len__(self) -> int:
        return len(self.rows)


@dataclass(frozen=True)
class HistoryDetail:
    """Full normalized detail for one selected occurrence.

    ``occurrence`` is the same model discovery produced; the extra fields are
    the current, re-resolved filesystem view a detail panel needs. No replay
    playback, digest verification, or agent execution happens here.
    """

    occurrence: HistoryOccurrence
    duplicate_occurrence_location: bool
    result_path: str | None
    replay_path: str | None
    first_seen_at: str | None

    @property
    def entrants(self) -> tuple[HistoryEntrant, ...]:
        return self.occurrence.entrants


@dataclass(frozen=True)
class ReplayResolution:
    """Click-time replay availability answer for one occurrence.

    Re-resolves the referenced replay under its own result directory with the
    canonical containment discipline and re-checks the filesystem, because a
    cached row is never authority for opening a file. Digest verification is
    an explicit, separate Phase 7D step; the recorded expectation is exposed
    here so that step needs no second read of ``result.json``.
    """

    location_id: str
    state: ReplayState
    path: str | None
    expected_sha256: str | None
    replay_id: str | None
    diagnostic: str | None = None

    @property
    def available(self) -> bool:
        return self.state is ReplayState.AVAILABLE and self.path is not None


@dataclass(frozen=True)
class ScanCounts:
    """Filesystem-visit accounting shared by rebuild and reconcile reports."""

    directories_visited: int = 0
    files_visited: int = 0
    result_candidates: int = 0
    replay_only_candidates: int = 0
    valid_entries: int = 0
    degraded_entries: int = 0
    incomplete_entries: int = 0
    invalid_entries: int = 0
    inaccessible_paths: int = 0
    unreadable_directories: int = 0
    replay_available: int = 0
    replay_missing: int = 0
    replay_not_produced: int = 0


@dataclass(frozen=True)
class RebuildSummary:
    """Outcome of a full index rebuild."""

    scanned: int = 0
    inserted: int = 0
    counts: ScanCounts = field(default_factory=ScanCounts)
    duration_seconds: float = 0.0
    generation: int = 0
    committed: bool = False
    diagnostics: tuple[str, ...] = ()


@dataclass(frozen=True)
class ReconcileSummary:
    """Outcome of one incremental reconciliation pass."""

    added: int = 0
    updated: int = 0
    replaced: int = 0
    unchanged: int = 0
    removed: int = 0
    retained_inaccessible: int = 0
    counts: ScanCounts = field(default_factory=ScanCounts)
    duration_seconds: float = 0.0
    generation: int = 0
    committed: bool = False
    scan_complete: bool = True
    diagnostics: tuple[str, ...] = ()


__all__ = [
    "DEFAULT_PAGE_SIZE",
    "MAX_PAGE_SIZE",
    "HistoryCursor",
    "HistoryDetail",
    "HistoryPage",
    "HistoryQuery",
    "HistoryRow",
    "RebuildSummary",
    "ReconcileSummary",
    "ReplayResolution",
    "ScanCounts",
]
