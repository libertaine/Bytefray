from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from battle_engine.result_model import (
    SCHEMA_NAME,
    SCHEMA_VERSION,
    SCHEMA_VERSION_V1,
    SCHEMA_VERSION_V2,
    SUPPORTED_SCHEMA_VERSIONS,
    ReplayReference,
    ResultEnvelope,
    generate_occurrence_id,
    read_result,
    stable_id,
    utc_completed_at,
    write_json_atomic,
)

V1_FIXTURE = Path(__file__).parent / "fixtures" / "result" / "battle2_result_v1.json"
OCCURRENCE_ID = "12345678-1234-4abc-8def-1234567890ab"
COMPLETED_AT = "2026-09-11T19:42:31.123456Z"
PRODUCT_VERSION = "5.0.0a1"


def _v2_envelope() -> ResultEnvelope:
    return ResultEnvelope(
        result_id="result_v2",
        match_id="match_v2",
        mode="b2",
        winner="A",
        termination_reason="last_agent_standing",
        ticks=4,
        score={"A": 5, "B": 0},
        entrants=(
            {
                "agent_id": "A",
                "name": "alpha",
                "metadata": {
                    "api_version": 2,
                    "parameters": {"scan_radius": 8},
                    "source_sha256": "a" * 64,
                },
            },
            {"agent_id": "B", "name": "beta", "metadata": {}},
        ),
        reproducibility={"seed": 7, "arena_size": 64},
        replay=ReplayReference("match_v2", "c" * 64, "replay.jsonl"),
        ruleset_id="bytefray-rules-4",
        occurrence_id=OCCURRENCE_ID,
        completed_at=COMPLETED_AT,
        product_version=PRODUCT_VERSION,
        schema_version=SCHEMA_VERSION,
    )


def test_battle2_result_v1_round_trip_and_stable_ids(tmp_path):
    identity = {"mode": "b2", "seed": 7, "entrants": ["A", "B"]}
    match_id = stable_id("match", identity)
    envelope = ResultEnvelope(
        result_id=stable_id("result", {"match_id": match_id, "winner": "A"}),
        match_id=match_id,
        mode="b2",
        winner="A",
        termination_reason="last_agent_standing",
        ticks=4,
        score={"A": 5, "B": 0},
        replay=ReplayReference(match_id, "a" * 64, "replay.jsonl"),
    )
    path = tmp_path / "result.json"
    write_json_atomic(path, envelope.as_dict())

    assert read_result(path) == envelope
    assert stable_id("match", identity) == match_id
    assert json.loads(path.read_text())["schema"] == "battle2.result"


def test_released_v1_fixture_reads_without_fabricating_v2_metadata():
    original = V1_FIXTURE.read_bytes()

    envelope = read_result(V1_FIXTURE)

    assert envelope.schema_version == SCHEMA_VERSION_V1
    assert envelope.occurrence_id is None
    assert envelope.completed_at is None
    assert envelope.product_version is None
    assert envelope.match_id == "match_legacy_v1"
    assert envelope.reproducibility["seed"] == 7
    assert envelope.winner == "A"
    assert V1_FIXTURE.read_bytes() == original


def test_result_v2_round_trip_preserves_occurrence_metadata(tmp_path):
    envelope = _v2_envelope()
    path = tmp_path / "result.json"

    write_json_atomic(path, envelope.as_dict())

    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["schema"] == SCHEMA_NAME == "battle2.result"
    assert payload["schema_version"] == SCHEMA_VERSION == SCHEMA_VERSION_V2 == 2
    assert payload["occurrence_id"] == OCCURRENCE_ID
    assert payload["completed_at"] == COMPLETED_AT
    assert payload["product_version"] == PRODUCT_VERSION
    assert payload["match_id"] == "match_v2"
    assert payload["reproducibility"]["seed"] == 7
    assert payload["entrants"][0]["metadata"]["parameters"] == {"scan_radius": 8}
    assert read_result(path) == envelope


def test_result_v2_serialization_repeat_is_stable(tmp_path):
    envelope = _v2_envelope()
    first = tmp_path / "first.json"
    second = tmp_path / "second.json"

    write_json_atomic(first, envelope.as_dict())
    write_json_atomic(second, envelope.as_dict())

    first_payload = json.loads(first.read_text(encoding="utf-8"))
    second_payload = json.loads(second.read_text(encoding="utf-8"))
    assert first_payload == second_payload
    assert first_payload["occurrence_id"] == OCCURRENCE_ID
    assert first_payload["completed_at"] == COMPLETED_AT


def test_result_v2_tolerates_unknown_fields(tmp_path):
    payload = _v2_envelope().as_dict()
    payload["future_metadata"] = {"safe": True}
    path = tmp_path / "result.json"
    write_json_atomic(path, payload)

    assert read_result(path) == _v2_envelope()


def test_result_reader_rejects_new_schema_family_name(tmp_path):
    payload = _v2_envelope().as_dict()
    payload["schema"] = "bytefray.result"
    path = tmp_path / "result.json"
    write_json_atomic(path, payload)

    with pytest.raises(ValueError, match="unsupported result schema identifier"):
        read_result(path)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    (
        ("occurrence_id", None, "occurrence_id"),
        ("occurrence_id", "not-a-uuid", "occurrence_id"),
        ("occurrence_id", OCCURRENCE_ID.upper(), "occurrence_id"),
        ("completed_at", None, "completed_at"),
        ("completed_at", "not-a-time", "completed_at"),
        ("completed_at", "2026-09-11T19:42:31.123456", "completed_at"),
        ("completed_at", "2026-09-11T19:42:31.123456-04:00", "completed_at"),
        ("product_version", None, "product_version"),
        ("product_version", "   ", "product_version"),
    ),
)
def test_result_v2_rejects_missing_or_malformed_metadata(
    tmp_path, field, value, message
):
    payload = _v2_envelope().as_dict()
    if value is None:
        payload.pop(field)
    else:
        payload[field] = value
    path = tmp_path / "result.json"
    write_json_atomic(path, payload)

    with pytest.raises(ValueError, match=message):
        read_result(path)


@pytest.mark.parametrize("schema_version", (None, "2", True, 3))
def test_result_reader_rejects_malformed_or_unsupported_versions(
    tmp_path, schema_version
):
    payload = _v2_envelope().as_dict()
    if schema_version is None:
        payload.pop("schema_version")
    else:
        payload["schema_version"] = schema_version
    path = tmp_path / "result.json"
    write_json_atomic(path, payload)

    with pytest.raises(ValueError, match="schema version"):
        read_result(path)


def test_result_v1_tolerates_unknown_fields_and_keeps_new_metadata_unknown(tmp_path):
    payload = json.loads(V1_FIXTURE.read_text(encoding="utf-8"))
    payload["future_metadata"] = {"safe": True}
    path = tmp_path / "result.json"
    write_json_atomic(path, payload)

    envelope = read_result(path)
    assert envelope.schema_version == SCHEMA_VERSION_V1
    assert (envelope.occurrence_id, envelope.completed_at, envelope.product_version) == (
        None,
        None,
        None,
    )


def test_occurrence_and_completion_factories_emit_canonical_values():
    occurrence_id = generate_occurrence_id()
    completed_at = utc_completed_at()

    assert str(uuid.UUID(occurrence_id)) == occurrence_id
    assert completed_at.endswith("Z")
    parsed = datetime.fromisoformat(f"{completed_at[:-1]}+00:00")
    assert parsed.utcoffset() == timedelta(0)
    assert SUPPORTED_SCHEMA_VERSIONS == (1, 2)


def test_result_replay_digest_detects_content_change(tmp_path):
    replay = tmp_path / "replay.jsonl"
    replay.write_bytes(b"first\n")
    first = hashlib.sha256(replay.read_bytes()).hexdigest()
    replay.write_bytes(b"second\n")
    assert hashlib.sha256(replay.read_bytes()).hexdigest() != first
