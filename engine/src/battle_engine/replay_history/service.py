"""Synchronous, Qt-free Replay History backend service.

This is the whole surface Phase 7C consumes. It owns the run-tree scan, the
disposable SQLite cache, and the typed query API; a UI layer never issues SQL,
never touches the filesystem layout, and never needs to know that SQLite is
the storage engine at all.

Nothing here imports Qt, starts a thread, or launches a process. The service
is deliberately synchronous so it can be driven from a worker thread by 7C,
tested headlessly, and benchmarked directly.
"""

from __future__ import annotations

import os
import time
from collections import Counter
from collections.abc import Callable, Iterator
from datetime import datetime, timezone
from pathlib import Path

from battle_engine.paths import contained_path, get_data_root
from battle_engine.result_model import ReplayIntegrityError, verify_replay_digest_value

from .discovery import (
    ArtifactCandidate,
    ArtifactScanner,
    default_runs_root,
    root_identity,
)
from .index import (
    META_GENERATION,
    META_LAST_REFRESH,
    CacheOpenReport,
    HistoryIndex,
    StoredSignature,
    artifact_relative_path,
    default_cache_path,
)
from .models import (
    ArtifactFingerprint,
    EntryHealth,
    HistoryOccurrence,
    ReplayState,
    ResultHealth,
)
from .query import (
    DEFAULT_PAGE_SIZE,
    HistoryCursor,
    HistoryDetail,
    HistoryPage,
    HistoryQuery,
    RebuildSummary,
    ReconcileSummary,
    ReplayIntegrityCheck,
    ReplayIntegrityStatus,
    ReplayResolution,
    RulesetFacet,
)

ProgressCallback = Callable[[str, int], None]
CancelCheck = Callable[[], bool]


class HistoryRefreshCancelled(RuntimeError):
    """A refresh was cancelled cooperatively; nothing was committed."""


def _classify(occurrence: HistoryOccurrence, tally: Counter[str]) -> None:
    if occurrence.entry_health is EntryHealth.HEALTHY:
        tally["valid"] += 1
    elif occurrence.entry_health is EntryHealth.DEGRADED:
        tally["degraded"] += 1
    elif occurrence.entry_health is EntryHealth.INCOMPLETE:
        tally["incomplete"] += 1
    else:
        tally["invalid"] += 1
    if occurrence.result_health is ResultHealth.INACCESSIBLE:
        tally["inaccessible"] += 1
    if occurrence.replay_state is ReplayState.AVAILABLE:
        tally["replay_available"] += 1
    elif occurrence.replay_state is ReplayState.MISSING:
        tally["replay_missing"] += 1
    elif occurrence.replay_state is ReplayState.NOT_PRODUCED:
        tally["replay_not_produced"] += 1


class ReplayHistoryService:
    """Open/rebuild/refresh/query facade over the Replay History index."""

    def __init__(self, index: HistoryIndex, runs_root: Path, identity: str) -> None:
        self._index = index
        self._runs_root = runs_root
        self._identity = identity

    # ------------------------------------------------------------------
    # lifecycle
    # ------------------------------------------------------------------

    @classmethod
    def open(
        cls,
        *,
        data_root: Path | str | None = None,
        runs_root: Path | str | None = None,
        cache_path: Path | str | None = None,
        in_memory: bool = False,
        read_only: bool = False,
    ) -> ReplayHistoryService:
        """Open the service against a run tree and its disposable cache.

        Defaults follow the established Bytefray path helpers: the run tree is
        ``<data root>/runs`` and the cache is
        ``<data root>/cache/replay_history/index-v1.sqlite3``. Tests and
        benchmarks pass explicit temporary locations so no real user cache is
        ever created.
        """

        resolved_data_root = (
            get_data_root() if data_root is None else Path(data_root).expanduser().resolve()
        )
        resolved_runs = (
            default_runs_root(resolved_data_root)
            if runs_root is None
            else Path(runs_root).expanduser().resolve()
        )
        identity = root_identity(resolved_runs)
        if in_memory:
            target: Path | None = None
        elif cache_path is None:
            target = default_cache_path(resolved_data_root)
        else:
            target = Path(cache_path).expanduser().resolve()
        if read_only:
            if target is None:
                raise ValueError("A read-only history service needs an existing persistent cache.")
            index = HistoryIndex.open_read_only(target, root_identity=identity)
        else:
            index = HistoryIndex.open(target, root_identity=identity)
        return cls(index, resolved_runs, identity)

    def close(self) -> None:
        self._index.close()

    def __enter__(self) -> ReplayHistoryService:  # noqa: PYI034 -- typing.Self needs 3.11+; runtime floor is 3.10
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()

    @property
    def runs_root(self) -> Path:
        return self._runs_root

    @property
    def cache_report(self) -> CacheOpenReport:
        return self._index.open_report

    @property
    def generation(self) -> int:
        return self._index.generation()

    def is_empty(self) -> bool:
        return self._index.is_empty()

    def row_count(self) -> int:
        return self._index.row_count()

    def cache_size_bytes(self) -> int:
        return self._index.database_size_bytes()

    # ------------------------------------------------------------------
    # refresh
    # ------------------------------------------------------------------

    def refresh(
        self,
        *,
        force_rebuild: bool = False,
        progress: ProgressCallback | None = None,
        cancel_check: CancelCheck | None = None,
    ) -> RebuildSummary | ReconcileSummary:
        """The single call a UI needs: rebuild when required, else reconcile.

        A cache that was just created, recovered from corruption, or
        invalidated by a version/root mismatch is rebuilt; anything else is
        reconciled incrementally.
        """

        self._require_writer()
        if force_rebuild or self.generation == 0:
            return self.rebuild(progress=progress, cancel_check=cancel_check)
        return self.reconcile(progress=progress, cancel_check=cancel_check)

    def _require_writer(self) -> None:
        if self._index.read_only:
            raise PermissionError("A read-only history service cannot refresh or rebuild its cache.")

    def rebuild(
        self,
        *,
        progress: ProgressCallback | None = None,
        cancel_check: CancelCheck | None = None,
    ) -> RebuildSummary:
        """Discard and rebuild the whole index inside one transaction.

        Table contents are replaced transactionally rather than by swapping
        files: a cross-platform rename of an open SQLite database (and its WAL
        sidecars) is not reliably atomic, and assuming otherwise is exactly the
        class of mistake the starter-refresh work had to correct. If anything
        fails -- including cooperative cancellation -- the transaction rolls
        back and the previously committed index remains usable.
        """

        self._require_writer()
        started = time.perf_counter()
        scanner = ArtifactScanner(self._runs_root, identity=self._identity)
        tally: Counter[str] = Counter()
        generation = self._index.generation() + 1
        inserted = 0
        try:
            with self._index.write_transaction():
                if cancel_check is not None and cancel_check():
                    raise HistoryRefreshCancelled("rebuild")
                self._index.clear()
                self._index.drop_secondary_indexes()
                inserted = self._index.write_occurrences(
                    self._normalized(scanner, tally, progress, cancel_check, "rebuild"),
                    generation=generation,
                    prune_entrants=False,
                )
                self._index.create_indexes()
                self._index.refresh_duplicate_flags()
                if cancel_check is not None and cancel_check():
                    raise HistoryRefreshCancelled("rebuild")
                self._finish_generation(generation)
        except HistoryRefreshCancelled:
            return RebuildSummary(
                counts=scanner.counts(tally),
                duration_seconds=time.perf_counter() - started,
                generation=self._index.generation(),
                committed=False,
                diagnostics=("refresh cancelled before commit",),
            )
        return RebuildSummary(
            scanned=scanner.result_candidates + scanner.replay_only_candidates,
            inserted=inserted,
            counts=scanner.counts(tally),
            duration_seconds=time.perf_counter() - started,
            generation=generation,
            committed=True,
            diagnostics=tuple(scanner.unreadable_directories),
        )

    def reconcile(
        self,
        *,
        progress: ProgressCallback | None = None,
        cancel_check: CancelCheck | None = None,
    ) -> ReconcileSummary:
        """Apply only what changed since the last committed generation."""
        self._require_writer()

        started = time.perf_counter()
        scanner = ArtifactScanner(self._runs_root, identity=self._identity)
        tally: Counter[str] = Counter()
        stored = self._index.stored_signatures()
        first_seen = {key: value.first_seen_at for key, value in stored.items()}
        generation = self._index.generation() + 1
        state = _ReconcileState()
        try:
            with self._index.write_transaction():
                if cancel_check is not None and cancel_check():
                    raise HistoryRefreshCancelled("reconcile")
                self._index.write_occurrences(
                    self._reconciled(
                        scanner, stored, first_seen, state, tally, progress, cancel_check
                    ),
                    generation=generation,
                    first_seen=first_seen,
                )
                if state.unchanged_ids:
                    self._index.mark_seen(state.unchanged_ids, generation)
                removed, retained = self._sweep_deleted(scanner, stored, state)
                self._index.refresh_duplicate_flags()
                if cancel_check is not None and cancel_check():
                    raise HistoryRefreshCancelled("reconcile")
                self._finish_generation(generation)
        except HistoryRefreshCancelled:
            return ReconcileSummary(
                counts=scanner.counts(tally),
                duration_seconds=time.perf_counter() - started,
                generation=self._index.generation(),
                committed=False,
                scan_complete=False,
                diagnostics=("refresh cancelled before commit",),
            )
        return ReconcileSummary(
            added=state.added,
            updated=state.updated,
            replaced=state.replaced,
            unchanged=len(state.unchanged_ids),
            removed=removed,
            retained_inaccessible=retained,
            counts=scanner.counts(tally),
            duration_seconds=time.perf_counter() - started,
            generation=generation,
            committed=True,
            scan_complete=not scanner.unreadable_directories,
            diagnostics=tuple(scanner.unreadable_directories),
        )

    # -- internal refresh helpers --------------------------------------

    def _finish_generation(self, generation: int) -> None:
        self._index.set_metadata(META_GENERATION, str(generation))
        self._index.set_metadata(META_LAST_REFRESH, _utc_now())

    def _normalized(
        self,
        scanner: ArtifactScanner,
        tally: Counter[str],
        progress: ProgressCallback | None,
        cancel_check: CancelCheck | None,
        phase: str,
    ) -> Iterator[HistoryOccurrence]:
        for seen, candidate in enumerate(scanner.iter_candidates(), 1):
            if cancel_check is not None and seen % 256 == 0 and cancel_check():
                raise HistoryRefreshCancelled(phase)
            occurrence = scanner.normalize(candidate)
            _classify(occurrence, tally)
            if progress is not None and seen % 1000 == 0:
                progress(phase, seen)
            yield occurrence

    def _reconciled(
        self,
        scanner: ArtifactScanner,
        stored: dict[str, StoredSignature],
        first_seen: dict[str, str],
        state: _ReconcileState,
        tally: Counter[str],
        progress: ProgressCallback | None,
        cancel_check: CancelCheck | None,
    ) -> Iterator[HistoryOccurrence]:
        """Yield only the occurrences that actually need rewriting.

        ``first_seen`` is the writer's lookup of preserved first-seen stamps.
        A replaced location is dropped from it *before* its occurrence is
        yielded, so the writer -- which reads the entry immediately after
        resuming this generator -- sees the removal. Keep that order.
        """

        for seen, candidate in enumerate(scanner.iter_candidates(), 1):
            if cancel_check is not None and seen % 256 == 0 and cancel_check():
                raise HistoryRefreshCancelled("reconcile")
            if progress is not None and seen % 1000 == 0:
                progress("reconcile", seen)
            prior = stored.get(candidate.location_id)
            state.seen_ids.add(candidate.location_id)
            if prior is not None and self._is_unchanged(candidate, prior):
                state.unchanged_ids.append(candidate.location_id)
                continue
            occurrence = scanner.normalize(candidate)
            _classify(occurrence, tally)
            if prior is None:
                state.added += 1
            elif prior.occurrence_key != occurrence.occurrence_key:
                # A different occurrence now lives at this location. That is a
                # replacement of the artifact, not a mutation of the same
                # execution, so the row starts fresh rather than inheriting the
                # previous occurrence's first-seen history.
                state.replaced += 1
                first_seen.pop(candidate.location_id, None)
            else:
                state.updated += 1
            yield occurrence

    def _is_unchanged(self, candidate: ArtifactCandidate, prior: StoredSignature) -> bool:
        """Cheap change detection: path, size, and nanosecond mtime only.

        No digest is computed and no replay bytes are read. The cache is an
        invalidation index, not a cryptographic integrity database; real
        integrity checking stays an explicit verification step.
        """

        fingerprint = candidate.result_fingerprint
        if (prior.result_exists, prior.result_size, prior.result_mtime_ns) != (
            fingerprint.exists,
            fingerprint.size,
            fingerprint.mtime_ns,
        ):
            return False
        if prior.replay_filename is None:
            # The indexed result recorded no usable replay reference. An
            # unchanged result proves that reference is still what it was, so
            # there is no file to stat.
            return not prior.replay_exists
        relative = artifact_relative_path(prior.relative_directory, prior.replay_filename)
        current = self._stat_relative(str(relative))
        return (current.exists, current.size, current.mtime_ns) == (
            prior.replay_exists,
            prior.replay_size,
            prior.replay_mtime_ns,
        )

    def _stat_relative(self, relative: str) -> ArtifactFingerprint:
        absolute = os.path.join(str(self._runs_root), relative.replace("/", os.sep))
        try:
            stat = os.stat(absolute)
        except OSError:
            return ArtifactFingerprint(relative_path=relative, exists=False)
        return ArtifactFingerprint(
            relative_path=relative, exists=True, size=stat.st_size, mtime_ns=stat.st_mtime_ns
        )

    def _sweep_deleted(
        self,
        scanner: ArtifactScanner,
        stored: dict[str, StoredSignature],
        state: _ReconcileState,
    ) -> tuple[int, int]:
        """Remove rows proven gone; keep rows under an uninspected subtree.

        A permission error, an unmounted share, or an interrupted walk must
        never be read as a mass deletion, so a row survives unless the scan
        actually proved its directory no longer exists.
        """

        removable: list[str] = []
        retained = 0
        for key, signature in stored.items():
            if key in state.seen_ids:
                continue
            if scanner.scope.is_definitively_absent(signature.relative_directory):
                removable.append(key)
            else:
                retained += 1
        removed = self._index.delete_locations(removable) if removable else 0
        return removed, retained

    # ------------------------------------------------------------------
    # queries
    # ------------------------------------------------------------------

    def fetch_page(
        self,
        query: HistoryQuery | None = None,
        *,
        cursor: HistoryCursor | None = None,
        limit: int = DEFAULT_PAGE_SIZE,
    ) -> HistoryPage:
        """One keyset page, newest effective timestamp first."""

        return self._index.fetch_page(query, cursor=cursor, limit=limit)

    def count(self, query: HistoryQuery | None = None) -> int:
        """Total rows matching ``query`` across every page."""

        return self._index.count(query)

    def fetch_page_with_count(
        self, query: HistoryQuery | None = None, *, limit: int = DEFAULT_PAGE_SIZE
    ) -> tuple[HistoryPage, int]:
        """First page and matching total from one committed generation."""
        with self._index.read_snapshot():
            return self.fetch_page(query, limit=limit), self.count(query)

    def ruleset_facets(self) -> tuple[RulesetFacet, ...]:
        """Distinct indexed ruleset identities, most common first.

        The one query a filter control needs to offer the Rulesets history
        actually contains rather than the Rulesets the current product
        happens to offer for new matches.
        """

        return self._index.ruleset_facets()

    def fetch_detail(self, location_id: str) -> HistoryDetail | None:
        """Full normalized detail for one row, with current absolute paths."""

        detail = self._index.fetch_detail(location_id)
        if detail is None:
            return None
        occurrence = detail.occurrence
        result_path = self._absolute_artifact(occurrence.result_fingerprint.relative_path)
        replay_path = self._absolute_artifact(occurrence.replay_fingerprint.relative_path)
        return HistoryDetail(
            occurrence=occurrence,
            duplicate_occurrence_location=detail.duplicate_occurrence_location,
            result_path=result_path,
            replay_path=replay_path,
            first_seen_at=detail.first_seen_at,
        )

    def resolve_replay(self, location_id: str) -> ReplayResolution:
        """Re-check one occurrence's replay before anything is opened.

        The cached path is never trusted on its own: it is re-resolved under
        the indexed run root with the canonical containment discipline (which
        rejects traversal, drive-qualified, and symlink escapes) and then
        re-checked on disk. Digest verification and the Viewer handoff belong
        to Phase 7D; the recorded expectation is returned here so that step
        needs no second read of ``result.json``.
        """

        detail = self._index.fetch_detail(location_id)
        if detail is None:
            return ReplayResolution(
                location_id=location_id,
                state=ReplayState.UNCHECKED,
                path=None,
                expected_sha256=None,
                replay_id=None,
                diagnostic="No indexed occurrence with that location id.",
            )
        occurrence = detail.occurrence
        relative = occurrence.replay_fingerprint.relative_path
        if occurrence.replay_state is ReplayState.NOT_PRODUCED or relative is None:
            return ReplayResolution(
                location_id=location_id,
                state=occurrence.replay_state,
                path=None,
                expected_sha256=occurrence.replay_sha256,
                replay_id=occurrence.replay_id,
                diagnostic=occurrence.diagnostic_message,
            )
        resolved = contained_path(self._runs_root, relative)
        if resolved is None:
            return ReplayResolution(
                location_id=location_id,
                state=ReplayState.INVALID,
                path=None,
                expected_sha256=occurrence.replay_sha256,
                replay_id=occurrence.replay_id,
                diagnostic="Replay path does not resolve inside the indexed run tree.",
            )
        try:
            present = resolved.is_file()
        except OSError as exc:
            return ReplayResolution(
                location_id=location_id,
                state=ReplayState.INACCESSIBLE,
                path=None,
                expected_sha256=occurrence.replay_sha256,
                replay_id=occurrence.replay_id,
                diagnostic=str(exc),
            )
        if not present:
            return ReplayResolution(
                location_id=location_id,
                state=ReplayState.MISSING,
                path=None,
                expected_sha256=occurrence.replay_sha256,
                replay_id=occurrence.replay_id,
                diagnostic="The referenced replay is no longer on disk.",
            )
        return ReplayResolution(
            location_id=location_id,
            state=ReplayState.AVAILABLE,
            path=str(resolved),
            expected_sha256=occurrence.replay_sha256,
            replay_id=occurrence.replay_id,
        )

    def verify_replay_integrity(self, resolution: ReplayResolution) -> ReplayIntegrityCheck:
        """Digest-preflight a resolved replay immediately before Viewer handoff.

        Takes the :class:`ReplayResolution` returned by :meth:`resolve_replay`
        -- never a second read of ``result.json`` -- and reads the resolved
        file's actual bytes to compare against the digest recorded when it
        was indexed:

        * no recorded digest (a historical result predating that field):
          ``UNVERIFIED_LEGACY``, not an error -- ``resolve_replay`` has
          already proven the file exists and is contained;
        * bytes match: ``VERIFIED``;
        * bytes differ: ``MISMATCH`` -- the file changed since it was
          indexed, and Phase 7D's launch policy blocks it;
        * the file vanished or became unreadable between ``resolve_replay``
          and this call: ``UNREADABLE``, not a crash.

        Callers must only invoke this for a resolution that already reports
        :attr:`ReplayResolution.available`; anything else has no path to
        read and returns ``UNREADABLE`` defensively rather than raising.
        """

        if not resolution.available or resolution.path is None:
            return ReplayIntegrityCheck(
                status=ReplayIntegrityStatus.UNREADABLE,
                diagnostic="No resolved replay path to verify.",
            )
        if resolution.expected_sha256 is None:
            return ReplayIntegrityCheck(status=ReplayIntegrityStatus.UNVERIFIED_LEGACY)
        try:
            digest = verify_replay_digest_value(resolution.expected_sha256, resolution.path)
        except ReplayIntegrityError as exc:
            status = (
                ReplayIntegrityStatus.MISMATCH
                if exc.code == "replay_digest_mismatch"
                else ReplayIntegrityStatus.UNREADABLE
            )
            return ReplayIntegrityCheck(status=status, diagnostic=str(exc))
        return ReplayIntegrityCheck(status=ReplayIntegrityStatus.VERIFIED, digest=digest)

    def _absolute_artifact(self, relative: str | None) -> str | None:
        if not relative:
            return None
        resolved = contained_path(self._runs_root, relative)
        return None if resolved is None else str(resolved)


class _ReconcileState:
    """Per-pass mutable accounting for :meth:`ReplayHistoryService.reconcile`."""

    def __init__(self) -> None:
        self.seen_ids: set[str] = set()
        self.unchanged_ids: list[str] = []
        self.added = 0
        self.updated = 0
        self.replaced = 0


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


__all__ = [
    "CancelCheck",
    "HistoryRefreshCancelled",
    "ProgressCallback",
    "ReplayHistoryService",
]
