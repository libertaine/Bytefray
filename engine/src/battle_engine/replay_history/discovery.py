"""Filesystem discovery and normalization for Replay History.

Walks ``<data-root>/runs`` once, recognizing only the exact canonical artifact
names, and converts each discovered location into one normalized
:class:`~battle_engine.replay_history.models.HistoryOccurrence`.

Three rules shape everything here:

* **Artifacts are untrusted input.** No agent module is imported or executed,
  no path embedded in artifact metadata is followed outside its own run
  directory, reads are size-bounded, and every failure becomes a health-coded
  row instead of an exception that aborts sibling discovery.
* **``result.json`` is the metadata authority.** A replay is parsed only when
  there is no result to answer from, and then only its first header line.
* **Nothing beneath ``runs`` is written.** Discovery is strictly read-only.
"""

from __future__ import annotations

import json
import os
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from pathlib import Path, PureWindowsPath
from typing import Any

from battle_engine.paths import contained_path, get_data_root
from battle_engine.replay import ReplayFormatError, deserialize_record, resolve_replay_ruleset
from battle_engine.replay import ReplayHeader as ReplayHeaderRecord
from battle_engine.result_model import (
    SCHEMA_NAME as RESULT_SCHEMA_NAME,
)
from battle_engine.result_model import (
    SUPPORTED_SCHEMA_VERSIONS,
    ResultEnvelope,
    resolve_result_ruleset,
    result_from_mapping,
)

from .models import (
    ArtifactFingerprint,
    DiagnosticCategory,
    HistoryEntrant,
    HistoryOccurrence,
    OccurrenceIdentitySource,
    OutcomeState,
    ReplayState,
    ResultHealth,
    TimestampConfidence,
    WorkflowSource,
    bounded_diagnostic,
    classify_entry_health,
    location_id,
    synthetic_occurrence_key,
)
from .query import ScanCounts

RESULT_FILENAME = "result.json"
REPLAY_FILENAME = "replay.jsonl"

# Generous relative to every real artifact shape (Phase 6 Y): a current
# ``result.json`` is single-digit kilobytes and a replay header line is far
# smaller. An artifact past either limit becomes a health-coded row rather
# than an unbounded read.
MAX_RESULT_BYTES = 4 * 1024 * 1024
MAX_REPLAY_HEADER_BYTES = 1024 * 1024

# Slack added to a stat-derived read size so a result that grew slightly
# between the walk's stat and the read is still parsed rather than truncated
# into a false "malformed" row. The hard limit above still wins.
_READ_SLACK = 64 * 1024

# Run-tree subdirectories whose producer is known from the layout itself.
_DESIGNER_DIR = "_designer"
_DEVELOPMENT_DIR = "agents_test"
_TOURNAMENT_DIR = "tournaments"
_EVALUATION_DIR = "evaluations"
_LOOSE_DIR = "_loose"

_TIE_WINNER = "tie"


@dataclass
class ScanScope:
    """Which parts of the run tree this pass actually managed to inspect.

    Reconciliation must never read a permission error as "the user deleted
    54,000 matches". A stored row may only be removed when the directory that
    held it was successfully enumerated, or when a fully enumerated ancestor
    proves the directory itself is gone.
    """

    root_enumerated: bool = False
    enumerated: set[str] = field(default_factory=set)
    failed: set[str] = field(default_factory=set)

    def record_enumerated(self, relative_directory: str) -> None:
        self.enumerated.add(relative_directory)

    def record_failure(self, relative_directory: str) -> None:
        self.failed.add(relative_directory)

    def is_definitively_absent(self, relative_directory: str) -> bool:
        """Whether an indexed location is proven gone rather than unreachable."""

        if not self.root_enumerated:
            return False
        if relative_directory in self.failed:
            return False
        if relative_directory in self.enumerated:
            return True
        # The directory was not visited. Walk up: if every ancestor between the
        # nearest successfully enumerated one and this directory was reachable,
        # the parent listing proves the directory no longer exists.
        parts = [part for part in relative_directory.split("/") if part]
        for depth in range(len(parts), 0, -1):
            ancestor = "/".join(parts[:depth])
            if ancestor in self.failed:
                return False
            if ancestor in self.enumerated:
                return True
        return "" in self.enumerated and "" not in self.failed


@dataclass(frozen=True)
class ArtifactCandidate:
    """One discovered artifact directory, before any parsing happens."""

    location_id: str
    relative_directory: str
    directory: str
    has_result: bool
    has_canonical_replay: bool
    result_fingerprint: ArtifactFingerprint


def default_runs_root(data_root: Path | None = None) -> Path:
    """The canonical run tree to index: ``<resolved data root>/runs``."""

    root = get_data_root() if data_root is None else Path(data_root)
    return root.expanduser().resolve() / "runs"


def root_identity(runs_root: Path) -> str:
    """Stable identity of the indexed scan root, stored in the cache."""

    return Path(runs_root).as_posix()


def classify_workflow(relative_directory: str) -> tuple[WorkflowSource, bool]:
    """Map a run-relative directory to a normalized source and durability.

    Returns ``(workflow, durable)``. ``durable`` is ``False`` only for the
    plain CLI's single overwrite-prone ``runs/_loose`` slot. Classification is
    deliberately structural: an unrecognized subtree becomes ``OTHER_RUN``
    rather than a guess, and the run root itself becomes ``UNKNOWN``.
    """

    parts = [part for part in relative_directory.split("/") if part]
    if not parts:
        return WorkflowSource.UNKNOWN, True
    head = parts[0]
    if head == _DESIGNER_DIR:
        return WorkflowSource.DESIGNER, True
    if head == _DEVELOPMENT_DIR:
        return WorkflowSource.DEVELOPMENT, True
    if head == _TOURNAMENT_DIR:
        return WorkflowSource.TOURNAMENT, True
    if head == _EVALUATION_DIR:
        return WorkflowSource.EVALUATION, True
    if head == _LOOSE_DIR:
        return WorkflowSource.CLI_LATEST, False
    # Research and custom output trees beneath ``runs`` hold real completed
    # matches; Phase 6 H requires indexing them rather than letting today's
    # folder names define what counts as history. A nested tournament or
    # evaluation directory is still recognized by its own marker segment.
    if _TOURNAMENT_DIR in parts:
        return WorkflowSource.TOURNAMENT, True
    if _EVALUATION_DIR in parts:
        return WorkflowSource.EVALUATION, True
    return WorkflowSource.OTHER_RUN, True


def directory_timestamp(workflow: WorkflowSource, relative_directory: str) -> datetime | None:
    """Recover a trustworthy UTC instant encoded in a known run-directory name.

    Only the two layouts that actually encode one are parsed:
    ``runs/_designer/<YYYYMMDD-HHMMSS>-<suffix>`` and
    ``runs/agents_test/<agent>/<YYYYMMDDTHHMMSS%f>-<suffix>``. Both writers
    format UTC. Any other shape returns ``None`` rather than guessing.
    """

    parts = [part for part in relative_directory.split("/") if part]
    if workflow is WorkflowSource.DESIGNER and len(parts) == 2:
        return _parse_stamp(parts[1][:15], "%Y%m%d-%H%M%S")
    if workflow is WorkflowSource.DEVELOPMENT and len(parts) == 3:
        return _parse_stamp(parts[2][:21], "%Y%m%dT%H%M%S%f")
    return None


def _parse_stamp(value: str, pattern: str) -> datetime | None:
    try:
        return datetime.strptime(value, pattern).replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _epoch_ns(moment: datetime) -> int:
    return int(moment.timestamp() * 1_000_000_000)


def _iso(moment: datetime) -> str:
    return moment.astimezone(timezone.utc).isoformat(timespec="microseconds").replace(
        "+00:00", "Z"
    )


def _parse_completed_at(value: str) -> datetime | None:
    candidate = f"{value[:-1]}+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=timezone.utc)


def _fingerprint(relative_path: str, absolute_path: str) -> ArtifactFingerprint:
    try:
        stat = os.stat(absolute_path)
    except OSError:
        return ArtifactFingerprint(relative_path=relative_path, exists=False)
    return ArtifactFingerprint(
        relative_path=relative_path,
        exists=True,
        size=stat.st_size,
        mtime_ns=stat.st_mtime_ns,
    )


def is_simple_relative_name(value: str) -> bool:
    """Whether a recorded replay filename is a plain name inside its own run.

    The canonical writer always records a bare, portable filename. This cheap
    string check rejects absolute, drive-qualified, separator-bearing, and
    dot-segment references without a ``resolve()`` syscall per artifact; the
    full containment discipline (:func:`battle_engine.paths.contained_path`,
    which also rejects symlink escapes) is applied to anything more complex
    and again before any path is handed onward for playback.
    """

    if not value or value in (".", ".."):
        return False
    if "/" in value or "\\" in value:
        return False
    return not (os.path.isabs(value) or PureWindowsPath(value).drive)


class ArtifactScanner:
    """One read-only pass over the canonical run tree."""

    def __init__(self, runs_root: Path | str, *, identity: str | None = None) -> None:
        self.runs_root = Path(runs_root)
        self._root_str = str(self.runs_root)
        self._prefix_length = len(self._root_str) + 1
        self.identity = root_identity(self.runs_root) if identity is None else identity
        self.scope = ScanScope()
        self.directories_visited = 0
        self.files_visited = 0
        self.result_candidates = 0
        self.replay_only_candidates = 0
        self.unreadable_directories: list[str] = []

    # -- walking -------------------------------------------------------

    def _relative(self, dirpath: str) -> str:
        if len(dirpath) <= self._prefix_length - 1:
            return ""
        return dirpath[self._prefix_length :].replace(os.sep, "/")

    def _on_error(self, error: OSError) -> None:
        name = getattr(error, "filename", None)
        relative = self._relative(str(name)) if isinstance(name, str) else ""
        self.scope.record_failure(relative)
        if len(self.unreadable_directories) < 50:
            self.unreadable_directories.append(bounded_diagnostic(f"{name}: {error}"))

    def iter_candidates(self) -> Iterator[ArtifactCandidate]:
        """Yield every artifact directory beneath the run root, once."""

        if not self.runs_root.is_dir():
            return
        for dirpath, _dirnames, filenames in os.walk(
            self._root_str, onerror=self._on_error, followlinks=False
        ):
            self.directories_visited += 1
            self.files_visited += len(filenames)
            relative = self._relative(dirpath)
            self.scope.record_enumerated(relative)
            if relative == "":
                self.scope.root_enumerated = True
            has_result = RESULT_FILENAME in filenames
            has_replay = REPLAY_FILENAME in filenames
            if not has_result and not has_replay:
                continue
            if has_result:
                self.result_candidates += 1
                fingerprint = _fingerprint(
                    _join_relative(relative, RESULT_FILENAME),
                    os.path.join(dirpath, RESULT_FILENAME),
                )
            else:
                self.replay_only_candidates += 1
                fingerprint = ArtifactFingerprint(
                    relative_path=_join_relative(relative, RESULT_FILENAME), exists=False
                )
            yield ArtifactCandidate(
                location_id=location_id(self.identity, relative),
                relative_directory=relative,
                directory=dirpath,
                has_result=has_result,
                has_canonical_replay=has_replay,
                result_fingerprint=fingerprint,
            )

    # -- normalization -------------------------------------------------

    def normalize(self, candidate: ArtifactCandidate) -> HistoryOccurrence:
        """Turn one candidate into a complete, health-coded occurrence."""

        workflow, durable = classify_workflow(candidate.relative_directory)
        if candidate.has_result:
            return self._normalize_result_entry(candidate, workflow, durable)
        return self._normalize_replay_only_entry(candidate, workflow, durable)

    # -- result-anchored -----------------------------------------------

    def _normalize_result_entry(
        self, candidate: ArtifactCandidate, workflow: WorkflowSource, durable: bool
    ) -> HistoryOccurrence:
        envelope, health, category, message = self._read_result(candidate)
        if envelope is None:
            return self._invalid_result_occurrence(
                candidate, workflow, durable, health, category, message
            )

        replay_state, replay_fingerprint, replay_category, replay_message = self._resolve_replay(
            candidate, envelope
        )
        occurrence_id = envelope.occurrence_id
        if occurrence_id is not None:
            occurrence_key = occurrence_id
            occurrence_source = OccurrenceIdentitySource.RECORDED
        else:
            occurrence_key = synthetic_occurrence_key(
                self.identity, candidate.relative_directory
            )
            occurrence_source = OccurrenceIdentitySource.SYNTHETIC_LOCATION

        timestamp, timestamp_ns, confidence = self._effective_timestamp(
            completed_at=envelope.completed_at,
            workflow=workflow,
            relative_directory=candidate.relative_directory,
            fallback_mtime_ns=candidate.result_fingerprint.mtime_ns,
        )
        ruleset = resolve_result_ruleset(envelope)
        reproducibility = dict(envelope.reproducibility or {})
        category_final = replay_category
        message_final = replay_message
        if not durable:
            category_final = category_final or DiagnosticCategory.LOOSE_SLOT_OVERWRITTEN
            message_final = message_final or (
                "The plain CLI default slot keeps only its most recent run; "
                "an overwritten match cannot be recovered."
            )
        return HistoryOccurrence(
            location_id=candidate.location_id,
            occurrence_key=occurrence_key,
            occurrence_source=occurrence_source,
            occurrence_id=occurrence_id,
            match_id=envelope.match_id,
            result_id=envelope.result_id,
            effective_timestamp=timestamp,
            effective_timestamp_ns=timestamp_ns,
            timestamp_known=confidence is not TimestampConfidence.UNKNOWN,
            timestamp_confidence=confidence,
            completed_at=envelope.completed_at,
            entrants=_entrants_from_result(envelope.entrants),
            ruleset_id=ruleset.value,
            ruleset_confidence=ruleset.confidence,
            seed=_as_optional_int(reproducibility.get("seed")),
            mode=envelope.mode,
            configuration=reproducibility,
            workflow=workflow,
            durable_location=durable,
            winner=envelope.winner,
            outcome_state=_outcome_state(envelope.winner),
            score=dict(envelope.score or {}),
            termination_reason=envelope.termination_reason,
            ticks=_as_optional_int(envelope.ticks),
            relative_directory=candidate.relative_directory,
            result_fingerprint=candidate.result_fingerprint,
            replay_fingerprint=replay_fingerprint,
            replay_state=replay_state,
            replay_sha256=None if envelope.replay is None else envelope.replay.sha256,
            replay_id=None if envelope.replay is None else envelope.replay.replay_id,
            result_health=ResultHealth.VALID,
            entry_health=classify_entry_health(ResultHealth.VALID, replay_state),
            diagnostic_category=category_final,
            diagnostic_message=message_final,
            result_schema_version=envelope.schema_version,
            product_version=envelope.product_version,
        )

    def _read_result(
        self, candidate: ArtifactCandidate
    ) -> tuple[ResultEnvelope | None, ResultHealth, DiagnosticCategory | None, str | None]:
        path = os.path.join(candidate.directory, RESULT_FILENAME)
        size = candidate.result_fingerprint.size
        if size is not None and size > MAX_RESULT_BYTES:
            return (
                None,
                ResultHealth.MALFORMED,
                DiagnosticCategory.RESULT_TOO_LARGE,
                f"result.json is {size} bytes, above the {MAX_RESULT_BYTES}-byte scan limit",
            )
        # Read a bounded amount, sized from the stat taken during the walk plus
        # a slack window for a file still being written. Asking a buffered
        # reader for the full 4 MiB limit makes it preallocate that buffer for
        # every artifact, which measured about 0.54 ms of pure overhead per
        # result -- roughly 24 s across the 53k-result corpus -- while reading
        # the same few kilobytes.
        limit = MAX_RESULT_BYTES if size is None else min(size + _READ_SLACK, MAX_RESULT_BYTES)
        try:
            with open(path, "rb") as stream:
                raw = stream.read(limit + 1)
        except OSError as exc:
            return (
                None,
                ResultHealth.INACCESSIBLE,
                DiagnosticCategory.RESULT_UNREADABLE,
                bounded_diagnostic(exc),
            )
        if len(raw) > MAX_RESULT_BYTES:
            return (
                None,
                ResultHealth.MALFORMED,
                DiagnosticCategory.RESULT_TOO_LARGE,
                f"result.json exceeds the {MAX_RESULT_BYTES}-byte scan limit",
            )
        try:
            data = json.loads(raw)
        except ValueError as exc:
            return (
                None,
                ResultHealth.MALFORMED,
                DiagnosticCategory.RESULT_MALFORMED_JSON,
                bounded_diagnostic(exc),
            )
        if not isinstance(data, dict):
            return (
                None,
                ResultHealth.MALFORMED,
                DiagnosticCategory.RESULT_INVALID_ROOT,
                f"JSON root is a {type(data).__name__}, not an object",
            )
        if data.get("schema") != RESULT_SCHEMA_NAME:
            return (
                None,
                ResultHealth.UNSUPPORTED,
                DiagnosticCategory.RESULT_UNSUPPORTED_SCHEMA,
                bounded_diagnostic(
                    f"schema {data.get('schema')!r} is not a {RESULT_SCHEMA_NAME} artifact"
                ),
            )
        version = data.get("schema_version")
        if type(version) is not int or version not in SUPPORTED_SCHEMA_VERSIONS:
            # Distinct from malformed JSON on purpose: a newer Bytefray can
            # rebuild this row without the file changing at all.
            return (
                None,
                ResultHealth.UNSUPPORTED,
                DiagnosticCategory.RESULT_UNSUPPORTED_VERSION,
                bounded_diagnostic(f"unsupported {RESULT_SCHEMA_NAME} version {version!r}"),
            )
        try:
            envelope = result_from_mapping(data)
        except (ValueError, KeyError, TypeError) as exc:
            return (
                None,
                ResultHealth.MALFORMED,
                DiagnosticCategory.RESULT_INVALID_FIELDS,
                bounded_diagnostic(exc),
            )
        return envelope, ResultHealth.VALID, None, None

    def _invalid_result_occurrence(
        self,
        candidate: ArtifactCandidate,
        workflow: WorkflowSource,
        durable: bool,
        health: ResultHealth,
        category: DiagnosticCategory | None,
        message: str | None,
    ) -> HistoryOccurrence:
        """A row that preserves location/diagnostic context for a bad artifact.

        The row is retained rather than dropped so the user can see *where* the
        problem is, and so an upgraded reader can reinterpret it later. No
        outcome or identity field is invented from the filesystem.
        """

        replay_relative = _join_relative(candidate.relative_directory, REPLAY_FILENAME)
        replay_fingerprint = (
            _fingerprint(replay_relative, os.path.join(candidate.directory, REPLAY_FILENAME))
            if candidate.has_canonical_replay
            else ArtifactFingerprint(relative_path=None, exists=False)
        )
        replay_state = (
            ReplayState.AVAILABLE if replay_fingerprint.exists else ReplayState.UNCHECKED
        )
        timestamp, timestamp_ns, confidence = self._effective_timestamp(
            completed_at=None,
            workflow=workflow,
            relative_directory=candidate.relative_directory,
            fallback_mtime_ns=candidate.result_fingerprint.mtime_ns
            or replay_fingerprint.mtime_ns,
        )
        return HistoryOccurrence(
            location_id=candidate.location_id,
            occurrence_key=synthetic_occurrence_key(
                self.identity, candidate.relative_directory
            ),
            occurrence_source=OccurrenceIdentitySource.SYNTHETIC_LOCATION,
            effective_timestamp=timestamp,
            effective_timestamp_ns=timestamp_ns,
            timestamp_known=confidence is not TimestampConfidence.UNKNOWN,
            timestamp_confidence=confidence,
            workflow=workflow,
            durable_location=durable,
            relative_directory=candidate.relative_directory,
            result_fingerprint=candidate.result_fingerprint,
            replay_fingerprint=replay_fingerprint,
            replay_state=replay_state,
            result_health=health,
            entry_health=classify_entry_health(health, replay_state),
            diagnostic_category=category,
            diagnostic_message=message,
        )

    def _resolve_replay(
        self, candidate: ArtifactCandidate, envelope: ResultEnvelope
    ) -> tuple[ReplayState, ArtifactFingerprint, DiagnosticCategory | None, str | None]:
        if envelope.replay is None:
            # pMARS/Redcode and any other workflow that legitimately produces
            # no native replay. Intentional absence, not a missing file.
            return (
                ReplayState.NOT_PRODUCED,
                ArtifactFingerprint(relative_path=None, exists=False),
                None,
                None,
            )
        filename = envelope.replay.filename
        if not isinstance(filename, str) or not filename:
            return (
                ReplayState.INVALID,
                ArtifactFingerprint(relative_path=None, exists=False),
                DiagnosticCategory.REPLAY_REFERENCE_UNSAFE,
                "result.json records an empty replay filename",
            )
        if is_simple_relative_name(filename):
            relative = _join_relative(candidate.relative_directory, filename)
            absolute = os.path.join(candidate.directory, filename)
        else:
            resolved = contained_path(Path(candidate.directory), filename)
            if resolved is None:
                return (
                    ReplayState.INVALID,
                    ArtifactFingerprint(relative_path=None, exists=False),
                    DiagnosticCategory.REPLAY_REFERENCE_UNSAFE,
                    bounded_diagnostic(
                        f"replay reference {filename!r} escapes its own run directory"
                    ),
                )
            absolute = str(resolved)
            relative = _join_relative(
                candidate.relative_directory, filename.replace("\\", "/")
            )
        fingerprint = _fingerprint(relative, absolute)
        if fingerprint.exists:
            return ReplayState.AVAILABLE, fingerprint, None, None
        return (
            ReplayState.MISSING,
            fingerprint,
            DiagnosticCategory.REPLAY_MISSING,
            bounded_diagnostic(f"referenced replay {filename!r} is not present"),
        )

    # -- replay-only ---------------------------------------------------

    def _normalize_replay_only_entry(
        self, candidate: ArtifactCandidate, workflow: WorkflowSource, durable: bool
    ) -> HistoryOccurrence:
        """A canonical replay with no ``result.json`` beside it.

        Found in the same single walk at no extra directory cost, so no second
        recursive pass over the corpus is needed. Only the first header record
        is read; the terminal outcome record is deliberately not searched for,
        because that would mean streaming every replay in the tree. The row is
        therefore always ``INCOMPLETE``: outcome, score, and termination stay
        unknown until a caller asks for something more expensive.
        """

        relative = _join_relative(candidate.relative_directory, REPLAY_FILENAME)
        absolute = os.path.join(candidate.directory, REPLAY_FILENAME)
        fingerprint = _fingerprint(relative, absolute)
        header, category, message = self._read_replay_header(absolute, fingerprint)
        timestamp, timestamp_ns, confidence = self._effective_timestamp(
            completed_at=None,
            workflow=workflow,
            relative_directory=candidate.relative_directory,
            fallback_mtime_ns=fingerprint.mtime_ns,
        )
        state = ReplayState.AVAILABLE if fingerprint.exists else ReplayState.MISSING
        if category is DiagnosticCategory.REPLAY_UNREADABLE:
            state = ReplayState.INACCESSIBLE
        occurrence = HistoryOccurrence(
            location_id=candidate.location_id,
            occurrence_key=synthetic_occurrence_key(
                self.identity, candidate.relative_directory
            ),
            occurrence_source=OccurrenceIdentitySource.SYNTHETIC_LOCATION,
            effective_timestamp=timestamp,
            effective_timestamp_ns=timestamp_ns,
            timestamp_known=confidence is not TimestampConfidence.UNKNOWN,
            timestamp_confidence=confidence,
            workflow=workflow,
            durable_location=durable,
            relative_directory=candidate.relative_directory,
            result_fingerprint=ArtifactFingerprint(
                relative_path=candidate.result_fingerprint.relative_path, exists=False
            ),
            replay_fingerprint=fingerprint,
            replay_state=state,
            result_health=ResultHealth.MISSING,
            entry_health=classify_entry_health(ResultHealth.MISSING, state),
            diagnostic_category=category or DiagnosticCategory.RESULT_MISSING,
            diagnostic_message=message
            or "No result.json at this location; metadata is limited to the replay header.",
        )
        if header is None:
            return occurrence
        ruleset = resolve_replay_ruleset(header)
        config = _replay_configuration(header)
        return replace(
            occurrence,
            match_id=header.match_id,
            result_id=header.result_id,
            replay_id=header.replay_id,
            entrants=_entrants_from_replay(header),
            ruleset_id=ruleset.value,
            ruleset_confidence=ruleset.confidence,
            seed=_as_optional_int(config.get("seed")),
            configuration=config,
            replay_schema_version=header.schema_version,
        )

    def _read_replay_header(
        self, absolute: str, fingerprint: ArtifactFingerprint
    ) -> tuple[ReplayHeaderRecord | None, DiagnosticCategory | None, str | None]:
        if not fingerprint.exists:
            return None, DiagnosticCategory.REPLAY_MISSING, "replay.jsonl disappeared during scan"
        try:
            with open(absolute, "rb") as stream:
                line = stream.readline(MAX_REPLAY_HEADER_BYTES + 1)
        except OSError as exc:
            return None, DiagnosticCategory.REPLAY_UNREADABLE, bounded_diagnostic(exc)
        if len(line) > MAX_REPLAY_HEADER_BYTES:
            return (
                None,
                DiagnosticCategory.REPLAY_HEADER_UNREADABLE,
                f"replay header line exceeds the {MAX_REPLAY_HEADER_BYTES}-byte scan limit",
            )
        try:
            record = deserialize_record(line.decode("utf-8"))
        except (ReplayFormatError, ValueError, KeyError, TypeError) as exc:
            return None, DiagnosticCategory.REPLAY_HEADER_UNREADABLE, bounded_diagnostic(exc)
        if not isinstance(record, ReplayHeaderRecord):
            return (
                None,
                DiagnosticCategory.REPLAY_HEADER_UNREADABLE,
                "first replay record is not a header",
            )
        return record, None, None

    # -- shared --------------------------------------------------------

    def _effective_timestamp(
        self,
        *,
        completed_at: str | None,
        workflow: WorkflowSource,
        relative_directory: str,
        fallback_mtime_ns: int | None,
    ) -> tuple[str | None, int, TimestampConfidence]:
        """Phase 6 F's fallback chain, with its confidence preserved.

        A fallback value is never promoted to authoritative completion time:
        it is stored alongside the confidence that produced it so the UI can
        mark it approximate and the detail panel can say where it came from.
        """

        if completed_at:
            parsed = _parse_completed_at(completed_at)
            if parsed is not None:
                return completed_at, _epoch_ns(parsed), TimestampConfidence.RECORDED
        inferred = directory_timestamp(workflow, relative_directory)
        if inferred is not None:
            return _iso(inferred), _epoch_ns(inferred), TimestampConfidence.DIRECTORY_INFERRED
        if fallback_mtime_ns is not None:
            moment = datetime.fromtimestamp(fallback_mtime_ns / 1_000_000_000, tz=timezone.utc)
            return _iso(moment), fallback_mtime_ns, TimestampConfidence.FILESYSTEM_FALLBACK
        return None, 0, TimestampConfidence.UNKNOWN

    def counts(self, occurrence_tally: Mapping[str, int]) -> ScanCounts:
        return ScanCounts(
            directories_visited=self.directories_visited,
            files_visited=self.files_visited,
            result_candidates=self.result_candidates,
            replay_only_candidates=self.replay_only_candidates,
            valid_entries=occurrence_tally.get("valid", 0),
            degraded_entries=occurrence_tally.get("degraded", 0),
            incomplete_entries=occurrence_tally.get("incomplete", 0),
            invalid_entries=occurrence_tally.get("invalid", 0),
            inaccessible_paths=occurrence_tally.get("inaccessible", 0),
            unreadable_directories=len(self.unreadable_directories),
            replay_available=occurrence_tally.get("replay_available", 0),
            replay_missing=occurrence_tally.get("replay_missing", 0),
            replay_not_produced=occurrence_tally.get("replay_not_produced", 0),
        )


def _join_relative(relative_directory: str, name: str) -> str:
    return f"{relative_directory}/{name}" if relative_directory else name


def _as_optional_int(value: object) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    return value


def _outcome_state(winner: object) -> OutcomeState:
    if not isinstance(winner, str) or not winner:
        return OutcomeState.UNKNOWN
    return OutcomeState.TIE if winner == _TIE_WINNER else OutcomeState.WINNER


def _entrants_from_result(entrants: Sequence[Mapping[str, Any]]) -> tuple[HistoryEntrant, ...]:
    adapted: list[HistoryEntrant] = []
    for ordinal, entrant in enumerate(entrants):
        if not isinstance(entrant, Mapping):
            continue
        metadata = entrant.get("metadata")
        metadata = metadata if isinstance(metadata, Mapping) else {}
        parameters = metadata.get("parameters")
        adapted.append(
            HistoryEntrant(
                ordinal=ordinal,
                agent_id=_as_optional_str(entrant.get("agent_id")),
                display_name=_as_optional_str(entrant.get("name")),
                runtime_kind=_as_optional_str(metadata.get("kind")),
                api_version=_as_optional_int(metadata.get("api_version")),
                agent_version=_as_optional_str(metadata.get("agent_version")),
                content_hash=_as_optional_str(
                    metadata.get("source_sha256") or metadata.get("code_sha256")
                ),
                parameters=parameters if isinstance(parameters, Mapping) else None,
            )
        )
    return tuple(adapted)


def _entrants_from_replay(header: ReplayHeaderRecord) -> tuple[HistoryEntrant, ...]:
    if header.entrants:
        return _entrants_from_result(list(header.entrants))
    # Pre-v3 headers carry only an ``agents`` id -> name mapping.
    return tuple(
        HistoryEntrant(
            ordinal=ordinal,
            agent_id=_as_optional_str(agent_id),
            display_name=_as_optional_str(name),
        )
        for ordinal, (agent_id, name) in enumerate(sorted((header.agents or {}).items()))
    )


def _replay_configuration(header: ReplayHeaderRecord) -> dict[str, Any]:
    config = dict(header.reproducibility or {})
    if "seed" not in config:
        config["seed"] = header.config.seed
    config.setdefault("arena_size", header.config.arena_size)
    config.setdefault("win_mode", header.config.win_mode)
    return config


def _as_optional_str(value: object) -> str | None:
    return value if isinstance(value, str) and value else None


__all__ = [
    "MAX_REPLAY_HEADER_BYTES",
    "MAX_RESULT_BYTES",
    "REPLAY_FILENAME",
    "RESULT_FILENAME",
    "ArtifactCandidate",
    "ArtifactScanner",
    "ScanScope",
    "classify_workflow",
    "default_runs_root",
    "directory_timestamp",
    "is_simple_relative_name",
    "root_identity",
]
