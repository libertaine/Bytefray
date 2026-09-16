"""Click-time integrity preflight for a replay referenced by a canonical result."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from string import hexdigits

from battle_engine.paths import contained_path
from battle_engine.replay import ReplayHeader, iter_replay
from battle_engine.result_model import (
    ReplayIntegrityError,
    read_result,
    verify_replay_digest,
)


class ReplayPreflightFailure(str, Enum):
    """Stable, presentation-neutral reasons a result replay cannot be trusted."""

    RESULT_UNAVAILABLE = "result_unavailable"
    RESULT_PATH_UNSAFE = "result_path_unsafe"
    RESULT_ASSOCIATION_MISMATCH = "result_association_mismatch"
    REPLAY_REFERENCE_MISSING = "replay_reference_missing"
    REPLAY_REFERENCE_MALFORMED = "replay_reference_malformed"
    REPLAY_PATH_UNSAFE = "replay_path_unsafe"
    REPLAY_MISSING = "replay_missing"
    REPLAY_UNREADABLE = "replay_unreadable"
    REPLAY_CHANGED = "replay_changed"
    REPLAY_INVALID = "replay_invalid"
    REPLAY_IDENTITY_MISMATCH = "replay_identity_mismatch"


@dataclass(frozen=True)
class ResultReplayRequest:
    """The canonical context needed to authorize one replay launch.

    ``artifact_root`` is the outer directory the selected result is expected
    to remain beneath. The replay itself is constrained more tightly to the
    current result's own parent directory.
    """

    result_path: Path
    artifact_root: Path
    expected_result_id: str | None = None
    expected_match_id: str | None = None


@dataclass(frozen=True)
class ReplayPreflightResult:
    """A verified path or a structured failure safe for UI classification."""

    replay_path: Path | None = None
    failure: ReplayPreflightFailure | None = None
    diagnostic: str | None = None

    @property
    def verified(self) -> bool:
        return self.replay_path is not None and self.failure is None


def _failure(
    reason: ReplayPreflightFailure, diagnostic: str
) -> ReplayPreflightResult:
    return ReplayPreflightResult(failure=reason, diagnostic=diagnostic)


def _contained_result_path(request: ResultReplayRequest) -> Path | None:
    try:
        root = Path(request.artifact_root).expanduser().resolve()
        result_path = Path(request.result_path).expanduser().resolve()
        result_path.relative_to(root)
    except (OSError, RuntimeError, ValueError):
        return None
    return result_path


def _valid_digest(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in hexdigits for character in value)
    )


def preflight_result_replay(request: ResultReplayRequest) -> ReplayPreflightResult:
    """Verify a result-associated replay immediately before viewer launch.

    The function is Qt-free and non-mutating. It rereads both canonical
    artifacts on every call; a presentation or history row loaded earlier is
    locator/identity context, never authorization to open stale bytes.
    """

    result_path = _contained_result_path(request)
    if result_path is None:
        return _failure(
            ReplayPreflightFailure.RESULT_PATH_UNSAFE,
            "The selected result resolves outside its expected artifact directory.",
        )
    try:
        envelope = read_result(result_path)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        return _failure(
            ReplayPreflightFailure.RESULT_UNAVAILABLE,
            f"The selected result could not be read: {exc}",
        )

    if (
        request.expected_result_id is not None
        and envelope.result_id != request.expected_result_id
    ):
        return _failure(
            ReplayPreflightFailure.RESULT_ASSOCIATION_MISMATCH,
            "The selected result_id no longer matches its parent record.",
        )
    if (
        request.expected_match_id is not None
        and envelope.match_id != request.expected_match_id
    ):
        return _failure(
            ReplayPreflightFailure.RESULT_ASSOCIATION_MISMATCH,
            "The selected match_id no longer matches its parent record.",
        )

    reference = envelope.replay
    if reference is None:
        return _failure(
            ReplayPreflightFailure.REPLAY_REFERENCE_MISSING,
            "The selected result does not reference a replay.",
        )
    if (
        not isinstance(reference.filename, str)
        or not reference.filename.strip()
        or not isinstance(reference.replay_id, str)
        or not reference.replay_id
        or not _valid_digest(reference.sha256)
    ):
        return _failure(
            ReplayPreflightFailure.REPLAY_REFERENCE_MALFORMED,
            "The selected result has a malformed replay reference.",
        )

    replay_path = contained_path(result_path.parent, reference.filename)
    if replay_path is None:
        return _failure(
            ReplayPreflightFailure.REPLAY_PATH_UNSAFE,
            "The result's replay filename resolves outside its artifact directory.",
        )
    try:
        verify_replay_digest(envelope, replay_path)
    except ReplayIntegrityError as exc:
        reasons = {
            "replay_file_missing": ReplayPreflightFailure.REPLAY_MISSING,
            "replay_file_unreadable": ReplayPreflightFailure.REPLAY_UNREADABLE,
            "replay_digest_mismatch": ReplayPreflightFailure.REPLAY_CHANGED,
        }
        return _failure(
            reasons.get(exc.code, ReplayPreflightFailure.REPLAY_REFERENCE_MISSING),
            str(exc),
        )

    try:
        header = next(
            (record for record in iter_replay(replay_path) if isinstance(record, ReplayHeader)),
            None,
        )
    except OSError as exc:
        return _failure(
            ReplayPreflightFailure.REPLAY_UNREADABLE,
            f"The replay header could not be read: {exc}",
        )
    except ValueError as exc:
        return _failure(
            ReplayPreflightFailure.REPLAY_INVALID,
            f"The replay header is invalid: {exc}",
        )
    if header is None:
        return _failure(
            ReplayPreflightFailure.REPLAY_INVALID,
            "The replay has no header.",
        )

    mismatches = tuple(
        label
        for label, actual, expected in (
            ("replay_id", header.replay_id, reference.replay_id),
            ("match_id", header.match_id, envelope.match_id),
            ("result_id", header.result_id, envelope.result_id),
            ("ruleset_id", header.ruleset_id, envelope.ruleset_id),
        )
        if actual != expected
    )
    if mismatches:
        return _failure(
            ReplayPreflightFailure.REPLAY_IDENTITY_MISMATCH,
            "Replay header identity does not match the result: " + ", ".join(mismatches),
        )
    return ReplayPreflightResult(replay_path=replay_path)


__all__ = [
    "ReplayPreflightFailure",
    "ReplayPreflightResult",
    "ResultReplayRequest",
    "preflight_result_replay",
]
