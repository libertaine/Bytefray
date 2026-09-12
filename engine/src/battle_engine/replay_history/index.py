"""Rebuildable SQLite metadata cache for Replay History.

The database is *derived, disposable state*. Match and replay artifacts remain
the only authority for history facts; deleting this file must never delete,
rewrite, or invalidate a single run artifact, and a rebuild from the same
corpus must reproduce the same semantic rows.

Only Python's standard-library ``sqlite3`` is used -- no dependency is added.
Every value that originates in an artifact (or in a caller's filter) is bound
as a SQL parameter; statement text is assembled exclusively from module-level
constants and ``?`` placeholders.
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterable, Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

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
)
from .query import (
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
    HistoryCursor,
    HistoryDetail,
    HistoryPage,
    HistoryQuery,
    HistoryRow,
)

# Cache schema version. Deliberately independent of ``battle2.result``'s
# schema version, the replay schema version, and the Bytefray product version:
# every column here is a derived projection that may evolve on its own
# schedule. A mismatch drops and rebuilds -- there is no user data to migrate.
CACHE_SCHEMA_VERSION = 1

# Bumped when the *interpretation* of artifacts or the shape of the cached
# projection changes without changing the table definitions. A product-version
# change alone never invalidates the cache (Phase 6 V).
EXTRACTOR_VERSION = 1

CACHE_DIRECTORY_NAME = "replay_history"
CACHE_FILE_NAME = "index-v1.sqlite3"

META_CACHE_SCHEMA_VERSION = "cache_schema_version"
META_EXTRACTOR_VERSION = "extractor_version"
META_ROOT_IDENTITY = "root_identity"
META_GENERATION = "generation"
META_LAST_REFRESH = "last_refresh_completed_at"

_OCCURRENCE_COLUMNS: tuple[str, ...] = (
    "location_id",
    "relative_directory",
    "occurrence_key",
    "occurrence_id",
    "occurrence_source",
    "match_id",
    "result_id",
    "timestamp_known",
    "effective_timestamp_ns",
    "effective_timestamp",
    "timestamp_confidence",
    "completed_at",
    "entrant_count",
    "entrant_summary",
    "entrant_search",
    "winner",
    "outcome_state",
    "score_json",
    "termination_reason",
    "ticks",
    "ruleset_id",
    "ruleset_confidence",
    "seed",
    "mode",
    "configuration_json",
    "workflow",
    "durable_location",
    "result_exists",
    "result_size",
    "result_mtime_ns",
    "replay_filename",
    "replay_exists",
    "replay_size",
    "replay_mtime_ns",
    "replay_state",
    "replay_sha256",
    "replay_id",
    "result_health",
    "entry_health",
    "diagnostic_category",
    "diagnostic_message",
    "result_schema_version",
    "product_version",
    "replay_schema_version",
    "duplicate_occurrence_location",
    "first_seen_at",
    "last_seen_generation",
)

_ENTRANT_COLUMNS: tuple[str, ...] = (
    "location_id",
    "ordinal",
    "agent_id",
    "display_name",
    "runtime_kind",
    "api_version",
    "agent_version",
    "content_hash",
    "parameters_json",
)

_SCHEMA_STATEMENTS: tuple[str, ...] = (
    """
    CREATE TABLE IF NOT EXISTS cache_metadata (
        key   TEXT PRIMARY KEY,
        value TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS occurrence (
        location_id                   TEXT PRIMARY KEY,
        relative_directory            TEXT NOT NULL,
        occurrence_key                TEXT NOT NULL,
        occurrence_id                 TEXT,
        occurrence_source             TEXT NOT NULL,
        match_id                      TEXT,
        result_id                     TEXT,
        timestamp_known               INTEGER NOT NULL,
        effective_timestamp_ns        INTEGER NOT NULL,
        effective_timestamp           TEXT,
        timestamp_confidence          TEXT NOT NULL,
        completed_at                  TEXT,
        entrant_count                 INTEGER NOT NULL,
        entrant_summary               TEXT NOT NULL,
        entrant_search                TEXT NOT NULL,
        winner                        TEXT,
        outcome_state                 TEXT NOT NULL,
        score_json                    TEXT,
        termination_reason            TEXT,
        ticks                         INTEGER,
        ruleset_id                    TEXT,
        ruleset_confidence            TEXT NOT NULL,
        seed                          INTEGER,
        mode                          TEXT,
        configuration_json            TEXT,
        workflow                      TEXT NOT NULL,
        durable_location              INTEGER NOT NULL,
        result_exists                 INTEGER NOT NULL,
        result_size                   INTEGER,
        result_mtime_ns               INTEGER,
        replay_filename               TEXT,
        replay_exists                 INTEGER NOT NULL,
        replay_size                   INTEGER,
        replay_mtime_ns               INTEGER,
        replay_state                  TEXT NOT NULL,
        replay_sha256                 TEXT,
        replay_id                     TEXT,
        result_health                 TEXT NOT NULL,
        entry_health                  TEXT NOT NULL,
        diagnostic_category           TEXT,
        diagnostic_message            TEXT,
        result_schema_version         INTEGER,
        product_version               TEXT,
        replay_schema_version         INTEGER,
        duplicate_occurrence_location INTEGER NOT NULL DEFAULT 0,
        first_seen_at                 TEXT NOT NULL,
        last_seen_generation          INTEGER NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS occurrence_entrant (
        location_id     TEXT NOT NULL
                        REFERENCES occurrence(location_id) ON DELETE CASCADE,
        ordinal         INTEGER NOT NULL,
        agent_id        TEXT,
        display_name    TEXT,
        runtime_kind    TEXT,
        api_version     INTEGER,
        agent_version   TEXT,
        content_hash    TEXT,
        parameters_json TEXT,
        PRIMARY KEY (location_id, ordinal)
    )
    """,
)

# Every index is justified by one clause of the Phase 6 query contract; see
# the Phase 7B report's tuning section for the measurements behind this set.
_INDEX_STATEMENTS: dict[str, str] = {
    # Default ordering / keyset paging. Mixed sort direction is declared on the
    # index itself so the planner can walk it without a sort step.
    "idx_occurrence_order": (
        "CREATE INDEX IF NOT EXISTS idx_occurrence_order "
        "ON occurrence(timestamp_known DESC, effective_timestamp_ns DESC, location_id ASC)"
    ),
    "idx_occurrence_key": (
        "CREATE INDEX IF NOT EXISTS idx_occurrence_key ON occurrence(occurrence_key)"
    ),
    "idx_occurrence_match": (
        "CREATE INDEX IF NOT EXISTS idx_occurrence_match ON occurrence(match_id)"
    ),
    "idx_occurrence_ruleset": (
        "CREATE INDEX IF NOT EXISTS idx_occurrence_ruleset ON occurrence(ruleset_id)"
    ),
    "idx_occurrence_seed": (
        "CREATE INDEX IF NOT EXISTS idx_occurrence_seed ON occurrence(seed)"
    ),
    "idx_occurrence_workflow": (
        "CREATE INDEX IF NOT EXISTS idx_occurrence_workflow ON occurrence(workflow)"
    ),
    "idx_occurrence_replay_state": (
        "CREATE INDEX IF NOT EXISTS idx_occurrence_replay_state ON occurrence(replay_state)"
    ),
    "idx_occurrence_winner": (
        "CREATE INDEX IF NOT EXISTS idx_occurrence_winner ON occurrence(winner)"
    ),
    "idx_occurrence_health": (
        "CREATE INDEX IF NOT EXISTS idx_occurrence_health ON occurrence(entry_health)"
    ),
}

_INSERT_OCCURRENCE = (
    "INSERT OR REPLACE INTO occurrence ("
    + ", ".join(_OCCURRENCE_COLUMNS)
    + ") VALUES ("
    + ", ".join("?" * len(_OCCURRENCE_COLUMNS))
    + ")"
)

_INSERT_ENTRANT = (
    "INSERT OR REPLACE INTO occurrence_entrant ("
    + ", ".join(_ENTRANT_COLUMNS)
    + ") VALUES ("
    + ", ".join("?" * len(_ENTRANT_COLUMNS))
    + ")"
)

_SELECT_ROW_COLUMNS = (
    "location_id, occurrence_key, occurrence_id, occurrence_source, match_id, "
    "effective_timestamp, effective_timestamp_ns, timestamp_known, timestamp_confidence, "
    "entrant_summary, entrant_count, winner, outcome_state, ruleset_id, ruleset_confidence, "
    "seed, workflow, durable_location, duplicate_occurrence_location, replay_state, "
    "result_health, entry_health, diagnostic_category, diagnostic_message"
)

_ORDER_BY = (
    " ORDER BY timestamp_known DESC, effective_timestamp_ns DESC, location_id ASC"
)

# Keyset predicate for the ordering above: strictly "after" the cursor tuple in
# (DESC, DESC, ASC) lexicographic order. Written as a fixed literal so no query
# text is ever assembled from caller-supplied data.
_KEYSET_PREDICATE = (
    "(timestamp_known < ? OR "
    "(timestamp_known = ? AND effective_timestamp_ns < ?) OR "
    "(timestamp_known = ? AND effective_timestamp_ns = ? AND location_id > ?))"
)


@dataclass(frozen=True)
class CacheOpenReport:
    """What happened while opening the cache, for service-level reporting."""

    path: str
    created: bool
    rebuild_required: bool
    rebuild_reason: str | None
    persistent: bool
    recovered_from: str | None = None


@dataclass(frozen=True, slots=True)
class StoredSignature:
    """Reconciliation fingerprint of one already-indexed location.

    Holds only what change detection actually compares -- existence, size, and
    nanosecond mtime, plus the replay's own filename. Artifact paths are
    derived from ``relative_directory`` instead of being stored again per row:
    one pass over the measured 53k corpus keeps every one of these objects in
    memory at once, so two redundant ~150-character path strings each would
    cost tens of megabytes for no added information.
    """

    location_id: str
    relative_directory: str
    occurrence_key: str
    first_seen_at: str
    result_exists: bool
    result_size: int | None
    result_mtime_ns: int | None
    replay_filename: str | None
    replay_exists: bool
    replay_size: int | None
    replay_mtime_ns: int | None


def default_cache_path(data_root: Path) -> Path:
    """Canonical cache location beneath the resolved Bytefray data root.

    Kept out of every individual run directory and classified as application
    cache rather than user match data (Phase 6 V).
    """

    return Path(data_root).expanduser().resolve() / "cache" / CACHE_DIRECTORY_NAME / CACHE_FILE_NAME


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def _json_or_none(value: Mapping[str, Any] | None) -> str | None:
    if not value:
        return None
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"))
    except (TypeError, ValueError):
        return None


def _mapping_from_json(value: object) -> dict[str, Any]:
    if not isinstance(value, str) or not value:
        return {}
    try:
        parsed = json.loads(value)
    except ValueError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _escape_like(value: str) -> str:
    """Escape LIKE wildcards so a literal ``%``/``_`` stays literal."""

    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


class HistoryIndex:
    """Storage primitives for the Replay History occurrence cache."""

    def __init__(self, connection: sqlite3.Connection, report: CacheOpenReport) -> None:
        self._connection = connection
        self._report = report

    # ------------------------------------------------------------------
    # lifecycle
    # ------------------------------------------------------------------

    @property
    def open_report(self) -> CacheOpenReport:
        return self._report

    @property
    def connection(self) -> sqlite3.Connection:
        return self._connection

    @classmethod
    def open(cls, path: Path | str | None, *, root_identity: str) -> HistoryIndex:
        """Open (creating or rebuilding as needed) the cache at ``path``.

        ``path`` of ``None`` opens a private in-memory cache, which is what
        tests and a disk-failure fallback use. A cache whose schema/extractor
        version or indexed root identity does not match is dropped and
        recreated rather than migrated: every column is derived state.
        """

        if path is None:
            connection = cls._connect(None)
            cls._create_schema(connection)
            cls._write_identity(connection, root_identity)
            report = CacheOpenReport(
                path=":memory:",
                created=True,
                rebuild_required=True,
                rebuild_reason="in_memory_cache",
                persistent=False,
            )
            return cls(connection, report)

        target = Path(path)
        try:
            connection = cls._connect(target)
            # The stored version must be read *before* the idempotent schema
            # creation writes the current one, or an unsupported cache would
            # silently relabel itself as current instead of rebuilding.
            stored_version = int(connection.execute("PRAGMA user_version").fetchone()[0])
            populated = (
                connection.execute(
                    "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'occurrence'"
                ).fetchone()
                is not None
            )
        except (sqlite3.DatabaseError, OSError) as exc:
            # A damaged or unusable *derived* cache is discarded, never
            # repaired in place, and never allowed to hide real history.
            return cls._recover(target, root_identity, f"{type(exc).__name__}: {exc}")

        if populated and stored_version != CACHE_SCHEMA_VERSION:
            connection.close()
            return cls._recover(
                target, root_identity, None, reason="cache_schema_version_mismatch"
            )

        try:
            cls._create_schema(connection)
            mismatch = None if not populated else cls._identity_mismatch(connection, root_identity)
        except (sqlite3.DatabaseError, OSError) as exc:
            connection.close()
            return cls._recover(target, root_identity, f"{type(exc).__name__}: {exc}")

        if mismatch is not None:
            connection.close()
            return cls._recover(target, root_identity, None, reason=mismatch)

        if not populated:
            cls._write_identity(connection, root_identity)
        report = CacheOpenReport(
            path=str(target),
            created=not populated,
            rebuild_required=not populated,
            rebuild_reason="new_cache" if not populated else None,
            persistent=True,
        )
        return cls(connection, report)

    @classmethod
    def _recover(
        cls,
        target: Path,
        root_identity: str,
        recovered_from: str | None,
        *,
        reason: str | None = None,
    ) -> HistoryIndex:
        removed = remove_cache_files(target)
        if not removed:
            # Deletion blocked (an open handle or a hostile ACL). Fall back to
            # a session-only in-memory cache so history still works; the caller
            # is told persistence failed rather than being handed a silent lie.
            connection = cls._connect(None)
            cls._create_schema(connection)
            cls._write_identity(connection, root_identity)
            return cls(
                connection,
                CacheOpenReport(
                    path=":memory:",
                    created=True,
                    rebuild_required=True,
                    rebuild_reason=reason or "cache_unusable",
                    persistent=False,
                    recovered_from=recovered_from,
                ),
            )
        connection = cls._connect(target)
        cls._create_schema(connection)
        cls._write_identity(connection, root_identity)
        return cls(
            connection,
            CacheOpenReport(
                path=str(target),
                created=True,
                rebuild_required=True,
                rebuild_reason=reason or "cache_recovered",
                persistent=True,
                recovered_from=recovered_from,
            ),
        )

    @staticmethod
    def _connect(target: Path | None) -> sqlite3.Connection:
        if target is None:
            connection = sqlite3.connect(":memory:", isolation_level=None)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            connection = sqlite3.connect(str(target), isolation_level=None, timeout=5.0)
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 5000")
        if target is not None:
            # WAL keeps readers on the last committed generation while one
            # refresh writer commits a new one. A filesystem that refuses WAL
            # (some network shares) simply stays on the default journal; this
            # cache is disposable either way, so that is a degradation, not a
            # failure.
            try:
                connection.execute("PRAGMA journal_mode = WAL")
            except sqlite3.DatabaseError:
                pass
            connection.execute("PRAGMA synchronous = NORMAL")
        return connection

    @staticmethod
    def _create_schema(connection: sqlite3.Connection) -> None:
        for statement in _SCHEMA_STATEMENTS:
            connection.execute(statement)
        for statement in _INDEX_STATEMENTS.values():
            connection.execute(statement)
        connection.execute(f"PRAGMA user_version = {int(CACHE_SCHEMA_VERSION)}")

    @staticmethod
    def _write_identity(connection: sqlite3.Connection, root_identity: str) -> None:
        rows = (
            (META_CACHE_SCHEMA_VERSION, str(CACHE_SCHEMA_VERSION)),
            (META_EXTRACTOR_VERSION, str(EXTRACTOR_VERSION)),
            (META_ROOT_IDENTITY, root_identity),
        )
        connection.executemany(
            "INSERT OR REPLACE INTO cache_metadata (key, value) VALUES (?, ?)", rows
        )

    @classmethod
    def _identity_mismatch(
        cls, connection: sqlite3.Connection, root_identity: str
    ) -> str | None:
        """Return a rebuild reason, or ``None`` when the cache is usable."""

        stored = {
            key: value
            for key, value in connection.execute("SELECT key, value FROM cache_metadata")
        }
        if not stored:
            cls._write_identity(connection, root_identity)
            return None
        if stored.get(META_CACHE_SCHEMA_VERSION) != str(CACHE_SCHEMA_VERSION):
            return "cache_schema_version_mismatch"
        if stored.get(META_EXTRACTOR_VERSION) != str(EXTRACTOR_VERSION):
            return "extractor_version_mismatch"
        if stored.get(META_ROOT_IDENTITY) != root_identity:
            return "root_identity_mismatch"
        return None

    def close(self) -> None:
        try:
            self._connection.close()
        except sqlite3.Error:
            pass

    # ------------------------------------------------------------------
    # transactions and metadata
    # ------------------------------------------------------------------

    @contextmanager
    def write_transaction(self) -> Iterator[sqlite3.Connection]:
        """One all-or-nothing writer transaction.

        ``BEGIN IMMEDIATE`` claims the single writer slot up front, so a second
        refreshing process fails fast against the busy timeout instead of
        discovering the conflict after a whole corpus walk. A failure inside
        the block rolls back, leaving the previously committed generation
        exactly as it was.
        """

        self._connection.execute("BEGIN IMMEDIATE")
        try:
            yield self._connection
        except BaseException:
            self._connection.execute("ROLLBACK")
            raise
        self._connection.execute("COMMIT")

    def metadata(self, key: str, default: str | None = None) -> str | None:
        row = self._connection.execute(
            "SELECT value FROM cache_metadata WHERE key = ?", (key,)
        ).fetchone()
        return default if row is None else str(row[0])

    def set_metadata(self, key: str, value: str) -> None:
        self._connection.execute(
            "INSERT OR REPLACE INTO cache_metadata (key, value) VALUES (?, ?)", (key, value)
        )

    def generation(self) -> int:
        raw = self.metadata(META_GENERATION, "0")
        try:
            return int(raw or 0)
        except ValueError:
            return 0

    def is_empty(self) -> bool:
        row = self._connection.execute("SELECT 1 FROM occurrence LIMIT 1").fetchone()
        return row is None

    def row_count(self) -> int:
        return int(self._connection.execute("SELECT COUNT(*) FROM occurrence").fetchone()[0])

    def database_size_bytes(self) -> int:
        page_count = int(self._connection.execute("PRAGMA page_count").fetchone()[0])
        page_size = int(self._connection.execute("PRAGMA page_size").fetchone()[0])
        return page_count * page_size

    # ------------------------------------------------------------------
    # writes
    # ------------------------------------------------------------------

    def clear(self) -> None:
        self._connection.execute("DELETE FROM occurrence_entrant")
        self._connection.execute("DELETE FROM occurrence")

    def drop_secondary_indexes(self) -> None:
        """Remove every non-ordering index ahead of a bulk load.

        SQLite maintains each index per inserted row; rebuilding them once at
        the end of a full rebuild measured about 6 s faster across the 53k
        corpus than maintaining them incrementally (25.2 s + 0.6 s versus
        31.3 s). DDL is transactional here, so an aborted rebuild rolls the
        indexes back along with the rows.
        """

        for name in _INDEX_STATEMENTS:
            if name != "idx_occurrence_order":
                self._connection.execute(f"DROP INDEX IF EXISTS {name}")

    def create_indexes(self) -> None:
        """(Re)create the full index set after a bulk load."""

        for statement in _INDEX_STATEMENTS.values():
            self._connection.execute(statement)

    def write_occurrences(
        self,
        occurrences: Iterable[HistoryOccurrence],
        *,
        generation: int,
        first_seen: Mapping[str, str] | None = None,
        batch_size: int = 1000,
        prune_entrants: bool = True,
    ) -> int:
        """Insert/replace occurrences, streaming so no full corpus is held.

        ``prune_entrants`` may be disabled by a caller that has just emptied
        the tables (a full rebuild), where the per-batch child-row delete can
        only ever match nothing.
        """

        now = _utc_now_iso()
        pending_rows: list[tuple[Any, ...]] = []
        pending_entrants: list[tuple[Any, ...]] = []
        pending_ids: list[str] = []
        written = 0
        for occurrence in occurrences:
            seen_at = now if first_seen is None else first_seen.get(occurrence.location_id, now)
            pending_rows.append(_occurrence_row(occurrence, generation, seen_at))
            pending_ids.append(occurrence.location_id)
            pending_entrants.extend(_entrant_rows(occurrence))
            written += 1
            if len(pending_rows) >= batch_size:
                self._flush(pending_ids, pending_rows, pending_entrants, prune_entrants)
                pending_rows, pending_entrants, pending_ids = [], [], []
        if pending_rows:
            self._flush(pending_ids, pending_rows, pending_entrants, prune_entrants)
        return written

    def _flush(
        self,
        location_ids: Sequence[str],
        rows: Sequence[tuple[Any, ...]],
        entrants: Sequence[tuple[Any, ...]],
        prune_entrants: bool = True,
    ) -> None:
        # Replacing a row must not leave its previous entrant children behind:
        # the new entrant list may be shorter than the old one.
        if prune_entrants:
            self._delete_entrants(location_ids)
        self._connection.executemany(_INSERT_OCCURRENCE, rows)
        if entrants:
            self._connection.executemany(_INSERT_ENTRANT, entrants)

    def _delete_entrants(self, location_ids: Sequence[str]) -> None:
        for chunk in _chunked(location_ids, 400):
            statement = (
                "DELETE FROM occurrence_entrant WHERE location_id IN ("
                + ", ".join("?" * len(chunk))
                + ")"
            )
            self._connection.execute(statement, tuple(chunk))

    def delete_locations(self, location_ids: Sequence[str]) -> int:
        removed = 0
        for chunk in _chunked(location_ids, 400):
            placeholders = ", ".join("?" * len(chunk))
            self._connection.execute(
                "DELETE FROM occurrence_entrant WHERE location_id IN (" + placeholders + ")",
                tuple(chunk),
            )
            cursor = self._connection.execute(
                "DELETE FROM occurrence WHERE location_id IN (" + placeholders + ")",
                tuple(chunk),
            )
            removed += max(0, cursor.rowcount)
        return removed

    def mark_seen(self, location_ids: Sequence[str], generation: int) -> None:
        for chunk in _chunked(location_ids, 400):
            statement = (
                "UPDATE occurrence SET last_seen_generation = ? WHERE location_id IN ("
                + ", ".join("?" * len(chunk))
                + ")"
            )
            self._connection.execute(statement, (generation, *chunk))

    def refresh_duplicate_flags(self) -> int:
        """Recompute the copied-occurrence marker over the whole table.

        Only *authoritative* v2 occurrence UUIDs can indicate a copied
        occurrence. Synthetic legacy keys are location-derived and therefore
        unique by construction, and an equal ``match_id`` is a legitimate
        deterministic rerun, never a duplicate. Rows are marked, never merged
        or deleted.
        """

        self._connection.execute(
            "UPDATE occurrence SET duplicate_occurrence_location = 0 "
            "WHERE duplicate_occurrence_location <> 0"
        )
        cursor = self._connection.execute(
            "UPDATE occurrence SET duplicate_occurrence_location = 1 "
            "WHERE occurrence_source = ? AND occurrence_key IN ("
            "  SELECT occurrence_key FROM occurrence WHERE occurrence_source = ?"
            "  GROUP BY occurrence_key HAVING COUNT(*) > 1)",
            (
                OccurrenceIdentitySource.RECORDED.value,
                OccurrenceIdentitySource.RECORDED.value,
            ),
        )
        return max(0, cursor.rowcount)

    # ------------------------------------------------------------------
    # reads
    # ------------------------------------------------------------------

    def stored_signatures(self) -> dict[str, StoredSignature]:
        """Every indexed location's change-detection fingerprint."""

        statement = (
            "SELECT location_id, relative_directory, occurrence_key, first_seen_at, "
            "result_exists, result_size, result_mtime_ns, "
            "replay_filename, replay_exists, replay_size, replay_mtime_ns "
            "FROM occurrence"
        )
        signatures: dict[str, StoredSignature] = {}
        for row in self._connection.execute(statement):
            signatures[str(row[0])] = StoredSignature(
                location_id=str(row[0]),
                relative_directory=str(row[1]),
                occurrence_key=str(row[2]),
                first_seen_at=str(row[3]),
                result_exists=bool(row[4]),
                result_size=row[5],
                result_mtime_ns=row[6],
                replay_filename=row[7],
                replay_exists=bool(row[8]),
                replay_size=row[9],
                replay_mtime_ns=row[10],
            )
        return signatures

    def first_seen_map(self, location_ids: Sequence[str]) -> dict[str, str]:
        found: dict[str, str] = {}
        for chunk in _chunked(location_ids, 400):
            statement = (
                "SELECT location_id, first_seen_at FROM occurrence WHERE location_id IN ("
                + ", ".join("?" * len(chunk))
                + ")"
            )
            for row in self._connection.execute(statement, tuple(chunk)):
                found[str(row[0])] = str(row[1])
        return found

    def fetch_page(
        self,
        query: HistoryQuery | None = None,
        *,
        cursor: HistoryCursor | None = None,
        limit: int = DEFAULT_PAGE_SIZE,
    ) -> HistoryPage:
        effective = query or HistoryQuery()
        size = max(1, min(int(limit), MAX_PAGE_SIZE))
        clauses, params = _filter_clauses(effective)
        if cursor is not None:
            clauses.append(_KEYSET_PREDICATE)
            params.extend(
                (
                    cursor.timestamp_known,
                    cursor.timestamp_known,
                    cursor.effective_timestamp_ns,
                    cursor.timestamp_known,
                    cursor.effective_timestamp_ns,
                    cursor.location_id,
                )
            )
        statement = "SELECT " + _SELECT_ROW_COLUMNS + " FROM occurrence"
        if clauses:
            statement += " WHERE " + " AND ".join(clauses)
        statement += _ORDER_BY + " LIMIT ?"
        params.append(size + 1)
        raw = self._connection.execute(statement, tuple(params)).fetchall()
        has_more = len(raw) > size
        rows = tuple(_history_row(item) for item in raw[:size])
        next_cursor = rows[-1].cursor if (has_more and rows) else None
        return HistoryPage(
            rows=rows, next_cursor=next_cursor, has_more=has_more, page_size=size
        )

    def count(self, query: HistoryQuery | None = None) -> int:
        clauses, params = _filter_clauses(query or HistoryQuery())
        statement = "SELECT COUNT(*) FROM occurrence"
        if clauses:
            statement += " WHERE " + " AND ".join(clauses)
        return int(self._connection.execute(statement, tuple(params)).fetchone()[0])

    def fetch_detail(self, location_id: str) -> HistoryDetail | None:
        statement = "SELECT " + ", ".join(_OCCURRENCE_COLUMNS) + (
            " FROM occurrence WHERE location_id = ?"
        )
        row = self._connection.execute(statement, (location_id,)).fetchone()
        if row is None:
            return None
        entrant_rows = self._connection.execute(
            "SELECT " + ", ".join(_ENTRANT_COLUMNS[1:]) + " FROM occurrence_entrant "
            "WHERE location_id = ? ORDER BY ordinal ASC",
            (location_id,),
        ).fetchall()
        occurrence = _occurrence_from_row(row, entrant_rows)
        values = dict(zip(_OCCURRENCE_COLUMNS, row, strict=True))
        return HistoryDetail(
            occurrence=occurrence,
            duplicate_occurrence_location=bool(values["duplicate_occurrence_location"]),
            result_path=None,
            replay_path=None,
            first_seen_at=str(values["first_seen_at"]),
        )


# ----------------------------------------------------------------------
# row mapping helpers
# ----------------------------------------------------------------------


RESULT_ARTIFACT_NAME = "result.json"


def result_relative_path(relative_directory: str) -> str:
    """The run-relative ``result.json`` path for one indexed directory.

    Derived rather than stored: discovery only ever anchors a row on the exact
    canonical name, so persisting the full path as well would duplicate
    ``relative_directory`` in every row (about 8 MB across the measured 53k
    corpus) and create a second copy that could drift from it.
    """

    return (
        f"{relative_directory}/{RESULT_ARTIFACT_NAME}"
        if relative_directory
        else RESULT_ARTIFACT_NAME
    )


def artifact_relative_path(relative_directory: str, filename: object) -> str | None:
    """Rejoin a stored artifact filename with its run-relative directory."""

    if not isinstance(filename, str) or not filename:
        return None
    return f"{relative_directory}/{filename}" if relative_directory else filename


def _artifact_filename(relative_directory: str, relative_path: str | None) -> str | None:
    """The directory-relative tail of an artifact path, for compact storage."""

    if not relative_path:
        return None
    prefix = f"{relative_directory}/"
    if relative_directory and relative_path.startswith(prefix):
        return relative_path[len(prefix) :]
    return relative_path


def _chunked(values: Sequence[str], size: int) -> Iterator[Sequence[str]]:
    for start in range(0, len(values), size):
        yield values[start : start + size]


def _occurrence_row(
    occurrence: HistoryOccurrence, generation: int, first_seen_at: str
) -> tuple[Any, ...]:
    result = occurrence.result_fingerprint
    replay = occurrence.replay_fingerprint
    return (
        occurrence.location_id,
        occurrence.relative_directory,
        occurrence.occurrence_key,
        occurrence.occurrence_id,
        occurrence.occurrence_source.value,
        occurrence.match_id,
        occurrence.result_id,
        1 if occurrence.timestamp_known else 0,
        int(occurrence.effective_timestamp_ns),
        occurrence.effective_timestamp,
        occurrence.timestamp_confidence.value,
        occurrence.completed_at,
        occurrence.entrant_count,
        occurrence.entrant_summary,
        occurrence.entrant_search,
        occurrence.winner,
        occurrence.outcome_state.value,
        _json_or_none(occurrence.score),
        occurrence.termination_reason,
        occurrence.ticks,
        occurrence.ruleset_id,
        occurrence.ruleset_confidence,
        occurrence.seed,
        occurrence.mode,
        _json_or_none(occurrence.configuration),
        occurrence.workflow.value,
        1 if occurrence.durable_location else 0,
        1 if result.exists else 0,
        result.size,
        result.mtime_ns,
        _artifact_filename(occurrence.relative_directory, replay.relative_path),
        1 if replay.exists else 0,
        replay.size,
        replay.mtime_ns,
        occurrence.replay_state.value,
        occurrence.replay_sha256,
        occurrence.replay_id,
        occurrence.result_health.value,
        occurrence.entry_health.value,
        None if occurrence.diagnostic_category is None else occurrence.diagnostic_category.value,
        occurrence.diagnostic_message,
        occurrence.result_schema_version,
        occurrence.product_version,
        occurrence.replay_schema_version,
        0,
        first_seen_at,
        generation,
    )


def _entrant_rows(occurrence: HistoryOccurrence) -> list[tuple[Any, ...]]:
    return [
        (
            occurrence.location_id,
            entrant.ordinal,
            entrant.agent_id,
            entrant.display_name,
            entrant.runtime_kind,
            entrant.api_version,
            entrant.agent_version,
            entrant.content_hash,
            _json_or_none(entrant.parameters),
        )
        for entrant in occurrence.entrants
    ]


def _history_row(row: Sequence[Any]) -> HistoryRow:
    return HistoryRow(
        location_id=str(row[0]),
        occurrence_key=str(row[1]),
        occurrence_id=row[2],
        occurrence_source=OccurrenceIdentitySource(row[3]),
        match_id=row[4],
        effective_timestamp=row[5],
        effective_timestamp_ns=int(row[6]),
        timestamp_known=bool(row[7]),
        timestamp_confidence=TimestampConfidence(row[8]),
        entrant_summary=str(row[9]),
        entrant_count=int(row[10]),
        winner=row[11],
        outcome_state=OutcomeState(row[12]),
        ruleset_id=row[13],
        ruleset_confidence=str(row[14]),
        seed=row[15],
        workflow=WorkflowSource(row[16]),
        durable_location=bool(row[17]),
        duplicate_occurrence_location=bool(row[18]),
        replay_state=ReplayState(row[19]),
        result_health=ResultHealth(row[20]),
        entry_health=EntryHealth(row[21]),
        diagnostic_category=row[22],
        diagnostic_message=row[23],
    )


def _occurrence_from_row(
    row: Sequence[Any], entrant_rows: Sequence[Sequence[Any]]
) -> HistoryOccurrence:
    values = dict(zip(_OCCURRENCE_COLUMNS, row, strict=True))
    entrants = tuple(
        HistoryEntrant(
            ordinal=int(item[0]),
            agent_id=item[1],
            display_name=item[2],
            runtime_kind=item[3],
            api_version=item[4],
            agent_version=item[5],
            content_hash=item[6],
            parameters=_mapping_from_json(item[7]) or None,
        )
        for item in entrant_rows
    )
    diagnostic_category = values["diagnostic_category"]
    return HistoryOccurrence(
        location_id=str(values["location_id"]),
        occurrence_key=str(values["occurrence_key"]),
        occurrence_source=OccurrenceIdentitySource(values["occurrence_source"]),
        occurrence_id=values["occurrence_id"],
        match_id=values["match_id"],
        result_id=values["result_id"],
        effective_timestamp=values["effective_timestamp"],
        effective_timestamp_ns=int(values["effective_timestamp_ns"]),
        timestamp_known=bool(values["timestamp_known"]),
        timestamp_confidence=TimestampConfidence(values["timestamp_confidence"]),
        completed_at=values["completed_at"],
        entrants=entrants,
        ruleset_id=values["ruleset_id"],
        ruleset_confidence=str(values["ruleset_confidence"]),
        seed=values["seed"],
        mode=values["mode"],
        configuration=_mapping_from_json(values["configuration_json"]),
        workflow=WorkflowSource(values["workflow"]),
        durable_location=bool(values["durable_location"]),
        winner=values["winner"],
        outcome_state=OutcomeState(values["outcome_state"]),
        score=_mapping_from_json(values["score_json"]),
        termination_reason=values["termination_reason"],
        ticks=values["ticks"],
        relative_directory=str(values["relative_directory"]),
        result_fingerprint=ArtifactFingerprint(
            relative_path=result_relative_path(str(values["relative_directory"])),
            exists=bool(values["result_exists"]),
            size=values["result_size"],
            mtime_ns=values["result_mtime_ns"],
        ),
        replay_fingerprint=ArtifactFingerprint(
            relative_path=artifact_relative_path(
                str(values["relative_directory"]), values["replay_filename"]
            ),
            exists=bool(values["replay_exists"]),
            size=values["replay_size"],
            mtime_ns=values["replay_mtime_ns"],
        ),
        replay_state=ReplayState(values["replay_state"]),
        replay_sha256=values["replay_sha256"],
        replay_id=values["replay_id"],
        result_health=ResultHealth(values["result_health"]),
        entry_health=EntryHealth(values["entry_health"]),
        diagnostic_category=(
            None if diagnostic_category is None else DiagnosticCategory(diagnostic_category)
        ),
        diagnostic_message=values["diagnostic_message"],
        result_schema_version=values["result_schema_version"],
        product_version=values["product_version"],
        replay_schema_version=values["replay_schema_version"],
    )


def _epoch_ns(value: datetime) -> int:
    moment = value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)
    return int(moment.timestamp() * 1_000_000_000)


def _filter_clauses(query: HistoryQuery) -> tuple[list[str], list[Any]]:
    """Translate a typed query into static clause text plus bound parameters."""

    clauses: list[str] = []
    params: list[Any] = []

    if query.entrant_text:
        clauses.append("entrant_search LIKE ? ESCAPE '\\'")
        params.append(f"%{_escape_like(query.entrant_text.lower())}%")

    if query.ruleset_ids is not None:
        values = list(query.ruleset_ids)
        concrete = [value for value in values if value is not None]
        parts: list[str] = []
        if concrete:
            parts.append("ruleset_id IN (" + ", ".join("?" * len(concrete)) + ")")
            params.extend(concrete)
        if len(concrete) != len(values):
            parts.append("ruleset_id IS NULL")
        clauses.append("(" + " OR ".join(parts) + ")" if parts else "0")

    if query.ruleset_confidences is not None:
        values = list(query.ruleset_confidences)
        if values:
            clauses.append("ruleset_confidence IN (" + ", ".join("?" * len(values)) + ")")
            params.extend(values)
        else:
            clauses.append("0")

    if query.outcome_states is not None:
        states = [state.value for state in query.outcome_states]
        if states:
            clauses.append("outcome_state IN (" + ", ".join("?" * len(states)) + ")")
            params.extend(states)
        else:
            clauses.append("0")

    if query.winner is not None:
        clauses.append("winner = ?")
        params.append(query.winner)

    if query.has_date_bound:
        # An unknown date is not comparable to a range bound, so a row with no
        # usable timestamp is excluded only while a range is active.
        clauses.append("timestamp_known = 1")
    if query.start is not None:
        clauses.append("effective_timestamp_ns >= ?")
        params.append(_epoch_ns(query.start))
    if query.end is not None:
        clauses.append("effective_timestamp_ns <= ?")
        params.append(_epoch_ns(query.end))

    if query.seed is not None:
        clauses.append("seed = ?")
        params.append(int(query.seed))

    if query.workflows is not None:
        values = [workflow.value for workflow in query.workflows]
        if values:
            clauses.append("workflow IN (" + ", ".join("?" * len(values)) + ")")
            params.extend(values)
        else:
            clauses.append("0")

    if query.replay_states is not None:
        values = [state.value for state in query.replay_states]
        if values:
            clauses.append("replay_state IN (" + ", ".join("?" * len(values)) + ")")
            params.extend(values)
        else:
            clauses.append("0")

    if query.entry_healths is not None:
        values = [health.value for health in query.entry_healths]
        if values:
            clauses.append("entry_health IN (" + ", ".join("?" * len(values)) + ")")
            params.extend(values)
        else:
            clauses.append("0")

    if query.match_id is not None:
        clauses.append("match_id = ?")
        params.append(query.match_id)

    if query.occurrence_id is not None:
        clauses.append("occurrence_id = ?")
        params.append(query.occurrence_id)

    return clauses, params


def remove_cache_files(target: Path) -> bool:
    """Delete a cache database and its journal sidecars. ``False`` if blocked."""

    removed = True
    for candidate in (
        target,
        target.with_name(target.name + "-wal"),
        target.with_name(target.name + "-shm"),
        target.with_name(target.name + "-journal"),
    ):
        try:
            candidate.unlink(missing_ok=True)
        except OSError:
            removed = False
    return removed


__all__ = [
    "CACHE_DIRECTORY_NAME",
    "CACHE_FILE_NAME",
    "CACHE_SCHEMA_VERSION",
    "EXTRACTOR_VERSION",
    "RESULT_ARTIFACT_NAME",
    "CacheOpenReport",
    "HistoryIndex",
    "StoredSignature",
    "artifact_relative_path",
    "default_cache_path",
    "remove_cache_files",
    "result_relative_path",
]
