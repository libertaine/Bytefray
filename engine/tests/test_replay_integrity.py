"""Canonical click-time preflight for result-associated replay opening."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import pytest
from battle_engine.replay import MatchConfiguration, ReplayHeader, write_replay
from battle_engine.replay_integrity import (
    ReplayPreflightFailure,
    ResultReplayRequest,
    preflight_result_replay,
)
from battle_engine.result_model import ReplayReference, ResultEnvelope, write_json_atomic


def _artifacts(
    directory: Path,
    *,
    replay_id: str = "replay_one",
    match_id: str = "match_one",
    result_id: str = "result_one",
    ruleset_id: str | None = "bytefray-rules-4",
    replay_schema_version: int = 4,
) -> tuple[Path, Path]:
    directory.mkdir(parents=True, exist_ok=True)
    replay_path = directory / "replay.jsonl"
    write_replay(
        replay_path,
        [
            ReplayHeader(
                MatchConfiguration(64),
                replay_id=replay_id,
                match_id=match_id,
                result_id=result_id,
                ruleset_id=ruleset_id,
                schema_version=replay_schema_version,
            )
        ],
    )
    digest = hashlib.sha256(replay_path.read_bytes()).hexdigest()
    result_path = directory / "result.json"
    write_json_atomic(
        result_path,
        ResultEnvelope(
            result_id=result_id,
            match_id=match_id,
            mode="b2",
            winner="A",
            termination_reason="elimination",
            ticks=1,
            replay=ReplayReference(replay_id, digest, replay_path.name),
            ruleset_id=ruleset_id,
        ).as_dict(),
    )
    return result_path, replay_path


def _request(result_path: Path, **changes: object) -> ResultReplayRequest:
    values = {
        "result_path": result_path,
        "artifact_root": result_path.parent,
        "expected_result_id": "result_one",
        "expected_match_id": "match_one",
    }
    values.update(changes)
    return ResultReplayRequest(**values)  # type: ignore[arg-type]


def test_valid_result_replay_returns_the_exact_verified_path(tmp_path: Path) -> None:
    result_path, replay_path = _artifacts(tmp_path / "match")

    outcome = preflight_result_replay(_request(result_path))

    assert outcome.verified
    assert outcome.replay_path == replay_path.resolve()
    assert outcome.failure is None


def test_missing_replay_after_an_earlier_valid_check_is_refused(tmp_path: Path) -> None:
    result_path, replay_path = _artifacts(tmp_path / "match")
    request = _request(result_path)
    assert preflight_result_replay(request).verified

    replay_path.unlink()

    outcome = preflight_result_replay(request)
    assert outcome.failure is ReplayPreflightFailure.REPLAY_MISSING


def test_changed_replay_is_refused_without_repairing_artifacts(tmp_path: Path) -> None:
    result_path, replay_path = _artifacts(tmp_path / "match")
    result_before = result_path.read_bytes()
    replay_path.write_bytes(replay_path.read_bytes() + b"\n")
    replay_before = replay_path.read_bytes()

    outcome = preflight_result_replay(_request(result_path))

    assert outcome.failure is ReplayPreflightFailure.REPLAY_CHANGED
    assert result_path.read_bytes() == result_before
    assert replay_path.read_bytes() == replay_before


def test_replaced_valid_replay_is_rejected_by_the_recorded_digest(tmp_path: Path) -> None:
    result_path, replay_path = _artifacts(tmp_path / "selected")
    _, other_replay = _artifacts(
        tmp_path / "other",
        replay_id="replay_other",
        match_id="match_other",
        result_id="result_other",
    )
    replay_path.write_bytes(other_replay.read_bytes())

    outcome = preflight_result_replay(_request(result_path))

    assert outcome.failure is ReplayPreflightFailure.REPLAY_CHANGED


def test_replay_identity_is_checked_independently_of_digest(tmp_path: Path) -> None:
    result_path, replay_path = _artifacts(tmp_path / "selected")
    _, other_replay = _artifacts(
        tmp_path / "other",
        replay_id="replay_other",
        match_id="match_other",
        result_id="result_other",
    )
    replay_path.write_bytes(other_replay.read_bytes())
    data = json.loads(result_path.read_text(encoding="utf-8"))
    data["replay"]["sha256"] = hashlib.sha256(replay_path.read_bytes()).hexdigest()
    result_path.write_text(json.dumps(data), encoding="utf-8")

    outcome = preflight_result_replay(_request(result_path))

    assert outcome.failure is ReplayPreflightFailure.REPLAY_IDENTITY_MISMATCH
    assert "replay_id" in (outcome.diagnostic or "")


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        ("replay_id", "wrong_replay"),
        ("match_id", "wrong_match"),
        ("result_id", "wrong_result"),
        ("ruleset_id", "bytefray-rules-4-alpha1"),
    ],
)
def test_each_replay_header_identity_is_independently_enforced(
    tmp_path: Path, field: str, replacement: str
) -> None:
    result_path, replay_path = _artifacts(tmp_path / "match")
    header = json.loads(replay_path.read_text(encoding="utf-8"))
    header[field] = replacement
    replay_path.write_text(json.dumps(header) + "\n", encoding="utf-8")
    result = json.loads(result_path.read_text(encoding="utf-8"))
    result["replay"]["sha256"] = hashlib.sha256(replay_path.read_bytes()).hexdigest()
    result_path.write_text(json.dumps(result), encoding="utf-8")

    outcome = preflight_result_replay(_request(result_path))

    assert outcome.failure is ReplayPreflightFailure.REPLAY_IDENTITY_MISMATCH
    assert field in (outcome.diagnostic or "")


def test_historical_v1_result_and_v3_replay_without_ruleset_fields_remain_valid(
    tmp_path: Path,
) -> None:
    result_path, _ = _artifacts(
        tmp_path / "historical",
        ruleset_id=None,
        replay_schema_version=3,
    )
    result = json.loads(result_path.read_text(encoding="utf-8"))
    result.pop("ruleset_id")
    result_path.write_text(json.dumps(result), encoding="utf-8")

    outcome = preflight_result_replay(_request(result_path))

    assert outcome.verified


def test_parent_result_identity_is_rechecked_at_click_time(tmp_path: Path) -> None:
    result_path, _ = _artifacts(tmp_path / "match")

    outcome = preflight_result_replay(
        _request(result_path, expected_result_id="different_result")
    )

    assert outcome.failure is ReplayPreflightFailure.RESULT_ASSOCIATION_MISMATCH


@pytest.mark.parametrize("filename", ["../outside.jsonl", "C:/outside/replay.jsonl"])
def test_unsafe_replay_reference_is_rejected(tmp_path: Path, filename: str) -> None:
    result_path, _ = _artifacts(tmp_path / "match")
    data = json.loads(result_path.read_text(encoding="utf-8"))
    data["replay"]["filename"] = filename
    result_path.write_text(json.dumps(data), encoding="utf-8")

    outcome = preflight_result_replay(_request(result_path))

    assert outcome.failure is ReplayPreflightFailure.REPLAY_PATH_UNSAFE


def test_result_itself_must_remain_inside_the_expected_artifact_root(tmp_path: Path) -> None:
    result_path, _ = _artifacts(tmp_path / "outside")

    outcome = preflight_result_replay(
        _request(result_path, artifact_root=tmp_path / "expected")
    )

    assert outcome.failure is ReplayPreflightFailure.RESULT_PATH_UNSAFE


def test_replay_symlink_escape_is_rejected_where_supported(tmp_path: Path) -> None:
    result_path, replay_path = _artifacts(tmp_path / "match")
    outside = tmp_path / "outside.jsonl"
    outside.write_bytes(replay_path.read_bytes())
    replay_path.unlink()
    try:
        os.symlink(outside, replay_path)
    except OSError as exc:
        pytest.skip(f"creating a test symlink is unavailable: {exc}")

    outcome = preflight_result_replay(_request(result_path))

    assert outcome.failure is ReplayPreflightFailure.REPLAY_PATH_UNSAFE


def test_malformed_reference_and_unreadable_result_fail_structurally(tmp_path: Path) -> None:
    result_path, _ = _artifacts(tmp_path / "match")
    data = json.loads(result_path.read_text(encoding="utf-8"))
    data["replay"]["sha256"] = "not-a-digest"
    result_path.write_text(json.dumps(data), encoding="utf-8")
    assert (
        preflight_result_replay(_request(result_path)).failure
        is ReplayPreflightFailure.REPLAY_REFERENCE_MALFORMED
    )

    result_path.write_text("not json", encoding="utf-8")
    assert (
        preflight_result_replay(_request(result_path)).failure
        is ReplayPreflightFailure.RESULT_UNAVAILABLE
    )
