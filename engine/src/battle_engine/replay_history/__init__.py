"""Qt-free Replay History discovery, normalization, and index service.

Phase 7B of the V5 Replay History work (see
``docs/research/v5/V5_REPLAY_HISTORY_PHASE7B_DISCOVERY_INDEX.md``). The public
entry point is :class:`ReplayHistoryService`: open it against a data root,
call :meth:`~ReplayHistoryService.refresh`, then page and filter with typed
:class:`HistoryQuery` values.

This package depends only on ``battle_engine.{paths,replay,result_model,rules}``
and the Python standard library. It must never import Qt, pygame, or Designer
code -- ``test_replay_history.py`` enforces that -- and it never executes or
imports agent code, writes to any run artifact, or treats the SQLite cache as
authoritative.
"""

from __future__ import annotations

from .discovery import (
    MAX_REPLAY_HEADER_BYTES,
    MAX_RESULT_BYTES,
    REPLAY_FILENAME,
    RESULT_FILENAME,
    ArtifactCandidate,
    ArtifactScanner,
    ScanScope,
    classify_workflow,
    default_runs_root,
    directory_timestamp,
    root_identity,
)
from .index import (
    CACHE_SCHEMA_VERSION,
    EXTRACTOR_VERSION,
    CacheOpenReport,
    HistoryIndex,
    StoredSignature,
    default_cache_path,
    remove_cache_files,
)
from .models import (
    ArtifactFingerprint,
    DiagnosticCategory,
    EntryHealth,
    HistoryEntrant,
    HistoryOccurrence,
    OccurrenceIdentitySource,
    OutcomeState,
    ReplayState,
    ResultHealth,
    TimestampConfidence,
    WorkflowSource,
    classify_entry_health,
    location_id,
    synthetic_occurrence_key,
)
from .query import (
    DEFAULT_PAGE_SIZE,
    HistoryCursor,
    HistoryDetail,
    HistoryPage,
    HistoryQuery,
    HistoryRow,
    RebuildSummary,
    ReconcileSummary,
    ReplayIntegrityCheck,
    ReplayIntegrityStatus,
    ReplayResolution,
    RulesetFacet,
    ScanCounts,
)
from .service import HistoryRefreshCancelled, ReplayHistoryService

__all__ = [
    "CACHE_SCHEMA_VERSION",
    "DEFAULT_PAGE_SIZE",
    "EXTRACTOR_VERSION",
    "MAX_REPLAY_HEADER_BYTES",
    "MAX_RESULT_BYTES",
    "REPLAY_FILENAME",
    "RESULT_FILENAME",
    "ArtifactCandidate",
    "ArtifactFingerprint",
    "ArtifactScanner",
    "CacheOpenReport",
    "DiagnosticCategory",
    "EntryHealth",
    "HistoryCursor",
    "HistoryDetail",
    "HistoryEntrant",
    "HistoryIndex",
    "HistoryOccurrence",
    "HistoryPage",
    "HistoryQuery",
    "HistoryRefreshCancelled",
    "HistoryRow",
    "OccurrenceIdentitySource",
    "OutcomeState",
    "RebuildSummary",
    "ReconcileSummary",
    "ReplayHistoryService",
    "ReplayIntegrityCheck",
    "ReplayIntegrityStatus",
    "ReplayResolution",
    "ReplayState",
    "ResultHealth",
    "RulesetFacet",
    "ScanCounts",
    "ScanScope",
    "StoredSignature",
    "TimestampConfidence",
    "WorkflowSource",
    "classify_entry_health",
    "classify_workflow",
    "default_cache_path",
    "default_runs_root",
    "directory_timestamp",
    "location_id",
    "remove_cache_files",
    "root_identity",
    "synthetic_occurrence_key",
]
