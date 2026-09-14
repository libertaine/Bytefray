"""Qt-free user-facing policy for result-associated replay preflight."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from battle_engine.replay_integrity import ReplayPreflightFailure, ResultReplayRequest

REPLAY_UNAVAILABLE_TITLE = "Replay Unavailable"
REPLAY_CHANGED_TITLE = "Replay Changed"
REPLAY_CHANGED_BODY = (
    "This replay no longer matches the match result it belongs to. It may have been "
    "modified or replaced, so Bytefray has not opened it."
)


@dataclass(frozen=True)
class ReplayFailureMessage:
    title: str
    body: str


def result_replay_request(
    result_path: Path,
    *,
    artifact_root: Path | None = None,
    expected_result_id: str | None = None,
    expected_match_id: str | None = None,
) -> ResultReplayRequest:
    """Build the one request shape shared by every result-backed GUI path."""

    path = Path(result_path)
    return ResultReplayRequest(
        result_path=path,
        artifact_root=path.parent if artifact_root is None else Path(artifact_root),
        expected_result_id=expected_result_id,
        expected_match_id=expected_match_id,
    )


def replay_failure_message(
    reason: ReplayPreflightFailure | None,
) -> ReplayFailureMessage:
    """Map structured preflight failures to concise, traceback-free GUI text."""

    if reason is ReplayPreflightFailure.REPLAY_CHANGED:
        return ReplayFailureMessage(REPLAY_CHANGED_TITLE, REPLAY_CHANGED_BODY)
    if reason in {
        ReplayPreflightFailure.RESULT_ASSOCIATION_MISMATCH,
        ReplayPreflightFailure.REPLAY_IDENTITY_MISMATCH,
    }:
        return ReplayFailureMessage(
            REPLAY_UNAVAILABLE_TITLE,
            "This replay is no longer associated with the selected result, so "
            "Bytefray has not opened it.",
        )
    if reason is ReplayPreflightFailure.REPLAY_MISSING:
        return ReplayFailureMessage(
            REPLAY_UNAVAILABLE_TITLE,
            "The replay file is missing or is no longer available. Bytefray has not "
            "opened it.",
        )
    if reason in {
        ReplayPreflightFailure.RESULT_UNAVAILABLE,
        ReplayPreflightFailure.RESULT_PATH_UNSAFE,
    }:
        return ReplayFailureMessage(
            REPLAY_UNAVAILABLE_TITLE,
            "The result needed to verify this replay is missing, unreadable, or in an "
            "unexpected location. Bytefray has not opened the replay.",
        )
    if reason in {
        ReplayPreflightFailure.REPLAY_REFERENCE_MISSING,
        ReplayPreflightFailure.REPLAY_REFERENCE_MALFORMED,
        ReplayPreflightFailure.REPLAY_PATH_UNSAFE,
    }:
        return ReplayFailureMessage(
            REPLAY_UNAVAILABLE_TITLE,
            "The selected result does not contain a safe, valid replay reference. "
            "Bytefray has not opened the replay.",
        )
    return ReplayFailureMessage(
        REPLAY_UNAVAILABLE_TITLE,
        "The replay could not be read and verified. Bytefray has not opened it.",
    )


__all__ = [
    "REPLAY_CHANGED_BODY",
    "REPLAY_CHANGED_TITLE",
    "REPLAY_UNAVAILABLE_TITLE",
    "ReplayFailureMessage",
    "replay_failure_message",
    "result_replay_request",
]
