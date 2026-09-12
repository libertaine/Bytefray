"""Focused coverage for the Qt-free Replay History discovery/index backend.

Every test builds its own temporary run tree and its own temporary cache
database, so the real user data root and the repository's own ``runs/`` corpus
are never touched, and no persistent cache is ever created.
"""

from __future__ import annotations

import builtins
import json
import os
import sqlite3
import sys
import uuid
from collections.abc import Iterator
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest
from battle_engine.replay_history import (
    CACHE_SCHEMA_VERSION,
    DEFAULT_PAGE_SIZE,
    ArtifactScanner,
    DiagnosticCategory,
    EntryHealth,
    HistoryQuery,
    OccurrenceIdentitySource,
    OutcomeState,
    ReplayHistoryService,
    ReplayIntegrityStatus,
    ReplayState,
    ResultHealth,
    ScanScope,
    TimestampConfidence,
    WorkflowSource,
    classify_workflow,
    default_cache_path,
    default_runs_root,
    directory_timestamp,
    location_id,
    synthetic_occurrence_key,
)
from battle_engine.replay_history.index import HistoryIndex

# ---------------------------------------------------------------------------
# fixtures / helpers
# ---------------------------------------------------------------------------

V2_COMPLETED_AT = "2026-09-11T19:54:50.985486Z"


def _result_payload(
    *,
    schema_version: int = 2,
    match_id: str = "match_aaaaaaaaaaaaaaaaaaaaaaaa",
    result_id: str = "result_aaaaaaaaaaaaaaaaaaaaaa",
    occurrence_id: str | None = None,
    completed_at: str | None = V2_COMPLETED_AT,
    product_version: str | None = "5.0.0a1",
    winner: str = "B",
    seed: int = 4242,
    ruleset_id: str | None = "bytefray-rules-4",
    mode: str = "b2",
    replay_filename: str | None = "replay.jsonl",
    entrants: tuple[tuple[str, str], ...] = (("A", "Alpha"), ("B", "Beta")),
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "schema": "battle2.result",
        "schema_version": schema_version,
        "result_id": result_id,
        "match_id": match_id,
        "mode": mode,
        "status": "completed",
        "winner": winner,
        "termination_reason": "tick_limit",
        "ticks": 10,
        "score": {agent_id: 1.0 for agent_id, _ in entrants},
        "entrants": [
            {
                "agent_id": agent_id,
                "name": name,
                "metadata": {
                    "kind": "python",
                    "api_version": 2,
                    "agent_version": "1.0.0",
                    "source_sha256": f"sha-{agent_id}",
                    "parameters": {"reach": 4},
                },
            }
            for agent_id, name in entrants
        ],
        "reproducibility": {
            "seed": seed,
            "arena_size": 512,
            "tick_limit": 1000,
            "action_budget": 8,
            "win_mode": "score_fallback",
            "entrant_order": [agent_id for agent_id, _ in entrants],
        },
        "replay": (
            None
            if replay_filename is None
            else {
                "replay_id": match_id,
                "sha256": "0" * 64,
                "filename": replay_filename,
            }
        ),
        "backend": None,
        "ruleset_id": ruleset_id,
    }
    if schema_version == 2:
        payload["occurrence_id"] = occurrence_id or str(uuid.uuid4())
        payload["completed_at"] = completed_at
        payload["product_version"] = product_version
    return payload


def _write_run(
    runs_root: Path,
    relative: str,
    *,
    with_replay: bool = True,
    replay_body: str | None = None,
    **kwargs: Any,
) -> Path:
    directory = runs_root / relative
    directory.mkdir(parents=True, exist_ok=True)
    payload = _result_payload(**kwargs)
    (directory / "result.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    if with_replay and payload["replay"] is not None:
        target = directory / str(payload["replay"]["filename"])
        target.write_text(replay_body or _replay_header_line(payload), encoding="utf-8")
    return directory


def _replay_header_line(payload: dict[str, Any]) -> str:
    header = {
        "schema": "battle2.replay",
        "schema_version": 4,
        "record_type": "header",
        "config": {
            "arena_size": 512,
            "instr_per_tick": 8,
            "seed": payload["reproducibility"]["seed"],
            "win_mode": "score_fallback",
            "weights": {},
        },
        "agents": {agent["agent_id"]: agent["name"] for agent in payload["entrants"]},
        "replay_id": payload["match_id"],
        "match_id": payload["match_id"],
        "result_id": payload["result_id"],
        "runtime_kind": "python",
        "reproducibility": payload["reproducibility"],
        "entrants": payload["entrants"],
        "ruleset_id": payload["ruleset_id"],
    }
    return json.dumps(header) + "\n"


@pytest.fixture()
def tree(tmp_path: Path) -> Path:
    (tmp_path / "runs").mkdir()
    return tmp_path


def _service(root: Path, **kwargs: Any) -> ReplayHistoryService:
    return ReplayHistoryService.open(
        data_root=root, cache_path=root / "cache" / "index.sqlite3", **kwargs
    )


def _snapshot(root: Path) -> dict[str, tuple[int, int, bytes]]:
    snapshot: dict[str, tuple[int, int, bytes]] = {}
    for path in sorted(root.rglob("*")):
        if path.is_file():
            stat = path.stat()
            snapshot[str(path.relative_to(root))] = (
                stat.st_size,
                stat.st_mtime_ns,
                path.read_bytes(),
            )
    return snapshot


def _all_rows(service: ReplayHistoryService, query: HistoryQuery | None = None) -> list[Any]:
    rows: list[Any] = []
    cursor = None
    while True:
        page = service.fetch_page(query, cursor=cursor, limit=DEFAULT_PAGE_SIZE)
        rows.extend(page.rows)
        if not page.has_more or page.next_cursor is None:
            return rows
        cursor = page.next_cursor


def _row_for(service: ReplayHistoryService, relative: str) -> Any:
    target = location_id(service._identity, relative)
    for row in _all_rows(service):
        if row.location_id == target:
            return row
    return None


# ---------------------------------------------------------------------------
# Gate 1 -- domain model, identity, timestamps, cache schema
# ---------------------------------------------------------------------------


def test_headless_import_never_pulls_in_qt_or_pygame() -> None:
    before = {name for name in sys.modules if "PySide6" in name or name == "pygame"}
    import battle_engine.replay_history
    import battle_engine.replay_history.discovery
    import battle_engine.replay_history.index
    import battle_engine.replay_history.service  # noqa: F401

    after = {name for name in sys.modules if "PySide6" in name or name == "pygame"}
    assert after == before


def test_v2_occurrence_identity_is_authoritative(tree: Path) -> None:
    occurrence = "11111111-2222-3333-4444-555555555555"
    _write_run(tree / "runs", "_designer/20260911-120000-aaaaaaaa", occurrence_id=occurrence)
    with _service(tree) as service:
        service.refresh()
        row = _all_rows(service)[0]
    assert row.occurrence_id == occurrence
    assert row.occurrence_key == occurrence
    assert row.occurrence_source is OccurrenceIdentitySource.RECORDED
    assert row.timestamp_confidence is TimestampConfidence.RECORDED
    assert row.effective_timestamp == V2_COMPLETED_AT


def test_v1_result_gets_synthetic_non_authoritative_identity(tree: Path) -> None:
    _write_run(tree / "runs", "_designer/20260911-120000-aaaaaaaa", schema_version=1)
    with _service(tree) as service:
        service.refresh()
        row = _all_rows(service)[0]
    assert row.occurrence_id is None
    assert row.occurrence_source is OccurrenceIdentitySource.SYNTHETIC_LOCATION
    assert row.occurrence_key.startswith("legacy-location_")
    # Deliberately not UUID-shaped, and deliberately not the match id.
    with pytest.raises(ValueError, match="badly formed"):
        uuid.UUID(row.occurrence_key)
    assert row.occurrence_key != row.match_id


def test_synthetic_occurrence_key_is_deterministic_and_location_scoped() -> None:
    first = synthetic_occurrence_key("root", "a/b")
    assert first == synthetic_occurrence_key("root", "a/b")
    assert first != synthetic_occurrence_key("root", "a/c")
    assert first != synthetic_occurrence_key("other-root", "a/b")
    assert first != location_id("root", "a/b")


def test_identical_v1_reruns_in_separate_directories_stay_separate(tree: Path) -> None:
    for relative in ("other/run-1", "other/run-2"):
        _write_run(tree / "runs", relative, schema_version=1, match_id="match_shared")
    with _service(tree) as service:
        service.refresh()
        rows = _all_rows(service)
    assert len(rows) == 2
    assert {row.match_id for row in rows} == {"match_shared"}
    assert len({row.occurrence_key for row in rows}) == 2
    assert not any(row.duplicate_occurrence_location for row in rows)


def test_designer_directory_timestamp_is_used_when_no_recorded_value(tree: Path) -> None:
    _write_run(tree / "runs", "_designer/20260101-101112-deadbeef", schema_version=1)
    with _service(tree) as service:
        service.refresh()
        row = _all_rows(service)[0]
    assert row.timestamp_confidence is TimestampConfidence.DIRECTORY_INFERRED
    assert row.effective_timestamp == "2026-01-01T10:11:12.000000Z"


def test_development_directory_timestamp_is_used_when_no_recorded_value(tree: Path) -> None:
    _write_run(
        tree / "runs",
        "agents_test/my-agent/20260202T030405123456-abcd1234-vs-runner",
        schema_version=1,
    )
    with _service(tree) as service:
        service.refresh()
        row = _all_rows(service)[0]
    assert row.timestamp_confidence is TimestampConfidence.DIRECTORY_INFERRED
    assert row.effective_timestamp == "2026-02-02T03:04:05.123456Z"
    assert row.workflow is WorkflowSource.DEVELOPMENT


def test_filesystem_mtime_is_the_last_labelled_fallback(tree: Path) -> None:
    _write_run(tree / "runs", "other/no-stamp", schema_version=1)
    with _service(tree) as service:
        service.refresh()
        row = _all_rows(service)[0]
    assert row.timestamp_confidence is TimestampConfidence.FILESYSTEM_FALLBACK
    assert row.timestamp_known is True
    assert row.effective_timestamp is not None


def test_recorded_timestamp_beats_both_fallbacks(tree: Path) -> None:
    # A v2 artifact in a timestamp-bearing directory: the recorded value wins
    # and the directory name is never allowed to override artifact truth.
    _write_run(tree / "runs", "_designer/20200101-000000-aaaaaaaa")
    with _service(tree) as service:
        service.refresh()
        row = _all_rows(service)[0]
    assert row.effective_timestamp == V2_COMPLETED_AT
    assert row.timestamp_confidence is TimestampConfidence.RECORDED


def test_directory_timestamp_rejects_unparseable_names() -> None:
    assert directory_timestamp(WorkflowSource.DESIGNER, "_designer/not-a-stamp") is None
    assert directory_timestamp(WorkflowSource.OTHER_RUN, "other/20260101-101112-x") is None


@pytest.mark.parametrize(
    ("relative", "expected", "durable"),
    [
        ("_designer/run", WorkflowSource.DESIGNER, True),
        ("agents_test/agent/run", WorkflowSource.DEVELOPMENT, True),
        ("tournaments/cup/matches/0001", WorkflowSource.TOURNAMENT, True),
        ("evaluations/eval-1/matches/0001", WorkflowSource.EVALUATION, True),
        ("_loose", WorkflowSource.CLI_LATEST, False),
        ("research_v3/whatever", WorkflowSource.OTHER_RUN, True),
        ("research_v3/tournaments/cup", WorkflowSource.TOURNAMENT, True),
        ("", WorkflowSource.UNKNOWN, True),
    ],
)
def test_workflow_classification(
    relative: str, expected: WorkflowSource, durable: bool
) -> None:
    assert classify_workflow(relative) == (expected, durable)


def test_cache_is_created_with_the_expected_schema_version(tree: Path) -> None:
    cache = tree / "cache" / "index.sqlite3"
    with _service(tree) as service:
        service.refresh()
    connection = sqlite3.connect(cache)
    try:
        assert connection.execute("PRAGMA user_version").fetchone()[0] == CACHE_SCHEMA_VERSION
        stored = dict(connection.execute("SELECT key, value FROM cache_metadata"))
    finally:
        connection.close()
    assert stored["cache_schema_version"] == str(CACHE_SCHEMA_VERSION)
    assert stored["root_identity"] == (tree / "runs").resolve().as_posix()


def test_cache_schema_mismatch_triggers_rebuild(tree: Path) -> None:
    _write_run(tree / "runs", "other/run-1")
    cache = tree / "cache" / "index.sqlite3"
    with _service(tree) as service:
        service.refresh()
        assert service.row_count() == 1
    connection = sqlite3.connect(cache)
    connection.execute(f"PRAGMA user_version = {CACHE_SCHEMA_VERSION + 99}")
    connection.close()
    with _service(tree) as service:
        assert service.cache_report.rebuild_required
        assert service.cache_report.rebuild_reason == "cache_schema_version_mismatch"
        assert service.is_empty()
        service.refresh()
        assert service.row_count() == 1


def test_cache_root_identity_mismatch_triggers_rebuild(tree: Path) -> None:
    cache = tree / "cache" / "index.sqlite3"
    with _service(tree) as service:
        service.refresh()
    connection = sqlite3.connect(cache)
    connection.execute(
        "INSERT OR REPLACE INTO cache_metadata (key, value) VALUES ('root_identity', 'elsewhere')"
    )
    connection.commit()
    connection.close()
    with _service(tree) as service:
        assert service.cache_report.rebuild_reason == "root_identity_mismatch"


def test_default_cache_path_is_outside_every_run_directory(tmp_path: Path) -> None:
    cache = default_cache_path(tmp_path)
    assert cache.parent.parent.name == "cache"
    assert "runs" not in cache.parts
    assert not cache.exists()


def test_default_runs_root_uses_the_configured_data_root(tmp_path: Path) -> None:
    assert default_runs_root(tmp_path) == (tmp_path / "runs").resolve()


def test_discovery_never_modifies_artifacts(tree: Path) -> None:
    runs = tree / "runs"
    _write_run(runs, "_designer/20260911-120000-aaaaaaaa")
    _write_run(runs, "other/v1", schema_version=1)
    (runs / "other" / "broken").mkdir(parents=True)
    (runs / "other" / "broken" / "result.json").write_text("{not json", encoding="utf-8")
    before = _snapshot(runs)
    with _service(tree) as service:
        service.refresh()
        service.refresh()
        for row in _all_rows(service):
            service.fetch_detail(row.location_id)
            service.resolve_replay(row.location_id)
    assert _snapshot(runs) == before


# ---------------------------------------------------------------------------
# Gate 2 -- discovery and normalization
# ---------------------------------------------------------------------------


def test_result_only_entry_is_kept_when_replay_is_missing(tree: Path) -> None:
    _write_run(tree / "runs", "other/no-replay", with_replay=False)
    with _service(tree) as service:
        service.refresh()
        row = _all_rows(service)[0]
        resolution = service.resolve_replay(row.location_id)
    assert row.result_health is ResultHealth.VALID
    assert row.replay_state is ReplayState.MISSING
    assert row.entry_health is EntryHealth.DEGRADED
    assert row.winner == "B"
    assert resolution.available is False


def test_null_replay_reference_is_not_produced_rather_than_missing(tree: Path) -> None:
    _write_run(
        tree / "runs",
        "other/pmars",
        replay_filename=None,
        mode="redcode94",
        ruleset_id=None,
        schema_version=1,
    )
    with _service(tree) as service:
        service.refresh()
        row = _all_rows(service)[0]
        resolution = service.resolve_replay(row.location_id)
    assert row.replay_state is ReplayState.NOT_PRODUCED
    assert row.entry_health is EntryHealth.HEALTHY
    assert row.ruleset_confidence == "not_applicable"
    assert resolution.state is ReplayState.NOT_PRODUCED
    assert resolution.path is None


def test_one_malformed_result_never_aborts_sibling_discovery(tree: Path) -> None:
    runs = tree / "runs"
    _write_run(runs, "other/good-1")
    _write_run(runs, "other/good-2")
    (runs / "other" / "bad").mkdir(parents=True)
    (runs / "other" / "bad" / "result.json").write_text("{ this is not json", encoding="utf-8")
    with _service(tree) as service:
        summary = service.refresh()
        rows = _all_rows(service)
        bad = _row_for(service, "other/bad")
    assert len(rows) == 3
    assert summary.counts.invalid_entries == 1
    assert bad.result_health is ResultHealth.MALFORMED
    assert bad.entry_health is EntryHealth.INVALID
    assert bad.diagnostic_category == DiagnosticCategory.RESULT_MALFORMED_JSON.value
    assert bad.diagnostic_message


def test_json_root_that_is_not_an_object_is_classified(tree: Path) -> None:
    runs = tree / "runs"
    (runs / "other" / "list").mkdir(parents=True)
    (runs / "other" / "list" / "result.json").write_text("[1, 2, 3]", encoding="utf-8")
    with _service(tree) as service:
        service.refresh()
        row = _all_rows(service)[0]
    assert row.diagnostic_category == DiagnosticCategory.RESULT_INVALID_ROOT.value


def test_unsupported_future_schema_version_is_distinct_from_malformed(tree: Path) -> None:
    runs = tree / "runs"
    payload = _result_payload()
    payload["schema_version"] = 999
    (runs / "other" / "future").mkdir(parents=True)
    (runs / "other" / "future" / "result.json").write_text(
        json.dumps(payload), encoding="utf-8"
    )
    with _service(tree) as service:
        service.refresh()
        row = _all_rows(service)[0]
    assert row.result_health is ResultHealth.UNSUPPORTED
    assert row.diagnostic_category == DiagnosticCategory.RESULT_UNSUPPORTED_VERSION.value
    # The location is preserved so a later Bytefray can reinterpret it.
    detail = None
    with _service(tree) as service:
        detail = service.fetch_detail(row.location_id)
    assert detail is not None
    assert detail.result_path is not None


def test_foreign_schema_identifier_is_unsupported_not_malformed(tree: Path) -> None:
    runs = tree / "runs"
    (runs / "other" / "foreign").mkdir(parents=True)
    (runs / "other" / "foreign" / "result.json").write_text(
        json.dumps({"schema": "something.else", "schema_version": 1}), encoding="utf-8"
    )
    with _service(tree) as service:
        service.refresh()
        row = _all_rows(service)[0]
    assert row.result_health is ResultHealth.UNSUPPORTED
    assert row.diagnostic_category == DiagnosticCategory.RESULT_UNSUPPORTED_SCHEMA.value


def test_invalid_v2_metadata_is_malformed_not_unsupported(tree: Path) -> None:
    runs = tree / "runs"
    payload = _result_payload(occurrence_id="not-a-uuid")
    (runs / "other" / "bad-uuid").mkdir(parents=True)
    (runs / "other" / "bad-uuid" / "result.json").write_text(
        json.dumps(payload), encoding="utf-8"
    )
    with _service(tree) as service:
        service.refresh()
        row = _all_rows(service)[0]
    assert row.result_health is ResultHealth.MALFORMED
    assert row.diagnostic_category == DiagnosticCategory.RESULT_INVALID_FIELDS.value


def test_unreadable_result_is_inaccessible_not_malformed(
    tree: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runs = tree / "runs"
    _write_run(runs, "other/locked")
    target = str((runs / "other" / "locked" / "result.json").resolve())
    real_open = builtins.open

    def guarded(file: Any, *args: Any, **kwargs: Any) -> Any:
        if str(file) == target:
            raise PermissionError(13, "simulated permission denial")
        return real_open(file, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", guarded)
    with _service(tree) as service:
        summary = service.refresh()
        row = _all_rows(service)[0]
    assert row.result_health is ResultHealth.INACCESSIBLE
    assert row.diagnostic_category == DiagnosticCategory.RESULT_UNREADABLE.value
    assert summary.counts.inaccessible_paths == 1


def test_oversized_result_is_bounded_rather_than_read(tree: Path) -> None:
    runs = tree / "runs"
    (runs / "other" / "huge").mkdir(parents=True)
    padded = _result_payload()
    padded["padding"] = "x" * (5 * 1024 * 1024)
    (runs / "other" / "huge" / "result.json").write_text(json.dumps(padded), encoding="utf-8")
    with _service(tree) as service:
        service.refresh()
        row = _all_rows(service)[0]
    assert row.diagnostic_category == DiagnosticCategory.RESULT_TOO_LARGE.value
    assert row.entry_health is EntryHealth.INVALID
    assert len(row.diagnostic_message) < 400


def test_replay_only_location_is_a_degraded_entry(tree: Path) -> None:
    runs = tree / "runs"
    directory = runs / "other" / "orphan"
    directory.mkdir(parents=True)
    payload = _result_payload(match_id="match_orphan", schema_version=1)
    (directory / "replay.jsonl").write_text(_replay_header_line(payload), encoding="utf-8")
    with _service(tree) as service:
        service.refresh()
        row = _all_rows(service)[0]
        detail = service.fetch_detail(row.location_id)
    assert row.result_health is ResultHealth.MISSING
    assert row.entry_health is EntryHealth.INCOMPLETE
    assert row.replay_state is ReplayState.AVAILABLE
    assert row.match_id == "match_orphan"
    assert row.outcome_state is OutcomeState.UNKNOWN
    assert row.occurrence_source is OccurrenceIdentitySource.SYNTHETIC_LOCATION
    assert detail is not None
    assert detail.occurrence.replay_schema_version == 4
    assert detail.occurrence.seed == 4242


def test_replay_only_with_unreadable_header_still_produces_a_row(tree: Path) -> None:
    runs = tree / "runs"
    directory = runs / "other" / "orphan-bad"
    directory.mkdir(parents=True)
    (directory / "replay.jsonl").write_text("not a replay record\n", encoding="utf-8")
    with _service(tree) as service:
        service.refresh()
        row = _all_rows(service)[0]
    assert row.result_health is ResultHealth.MISSING
    assert row.diagnostic_category == DiagnosticCategory.REPLAY_HEADER_UNREADABLE.value


def test_replay_reference_escaping_its_run_directory_is_rejected(tree: Path) -> None:
    runs = tree / "runs"
    _write_run(runs, "other/escape", replay_filename="../../secrets.jsonl", with_replay=False)
    (runs.parent / "secrets.jsonl").write_text("{}", encoding="utf-8")
    with _service(tree) as service:
        service.refresh()
        row = _all_rows(service)[0]
        resolution = service.resolve_replay(row.location_id)
    assert row.replay_state is ReplayState.INVALID
    assert row.diagnostic_category == DiagnosticCategory.REPLAY_REFERENCE_UNSAFE.value
    assert resolution.path is None


def test_absolute_replay_reference_is_rejected(tree: Path) -> None:
    runs = tree / "runs"
    outside = tree / "outside.jsonl"
    outside.write_text("{}", encoding="utf-8")
    _write_run(runs, "other/abs", replay_filename=str(outside), with_replay=False)
    with _service(tree) as service:
        service.refresh()
        row = _all_rows(service)[0]
    assert row.replay_state is ReplayState.INVALID


def test_loose_slot_is_indexed_as_a_non_durable_cli_latest_occurrence(tree: Path) -> None:
    _write_run(tree / "runs", "_loose")
    with _service(tree) as service:
        service.refresh()
        row = _all_rows(service)[0]
    assert row.workflow is WorkflowSource.CLI_LATEST
    assert row.durable_location is False
    assert row.entry_health is EntryHealth.HEALTHY
    assert row.diagnostic_category == DiagnosticCategory.LOOSE_SLOT_OVERWRITTEN.value


def test_copied_v2_occurrence_is_flagged_but_never_collapsed(tree: Path) -> None:
    runs = tree / "runs"
    occurrence = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
    _write_run(runs, "other/original", occurrence_id=occurrence)
    _write_run(runs, "other/copy", occurrence_id=occurrence)
    _write_run(runs, "other/unrelated")
    with _service(tree) as service:
        service.refresh()
        rows = _all_rows(service)
    flagged = [row for row in rows if row.duplicate_occurrence_location]
    assert len(rows) == 3
    assert len(flagged) == 2
    assert {row.occurrence_id for row in flagged} == {occurrence}


def test_same_match_id_with_different_occurrences_is_not_a_duplicate(tree: Path) -> None:
    runs = tree / "runs"
    _write_run(runs, "other/run-a", match_id="match_same")
    _write_run(runs, "other/run-b", match_id="match_same")
    with _service(tree) as service:
        service.refresh()
        rows = _all_rows(service)
    assert len(rows) == 2
    assert not any(row.duplicate_occurrence_location for row in rows)
    assert len({row.occurrence_id for row in rows}) == 2


def test_discovery_reports_scan_accounting(tree: Path) -> None:
    runs = tree / "runs"
    _write_run(runs, "other/one")
    _write_run(runs, "other/two", with_replay=False)
    with _service(tree) as service:
        summary = service.refresh()
    counts = summary.counts
    assert counts.result_candidates == 2
    assert counts.valid_entries == 1
    assert counts.degraded_entries == 1
    assert counts.replay_available == 1
    assert counts.replay_missing == 1
    assert counts.directories_visited >= 3
    assert summary.duration_seconds >= 0.0


def test_scanner_tolerates_a_missing_run_root(tmp_path: Path) -> None:
    scanner = ArtifactScanner(tmp_path / "does-not-exist")
    assert list(scanner.iter_candidates()) == []


# ---------------------------------------------------------------------------
# Gate 3 -- full rebuild and recovery
# ---------------------------------------------------------------------------


def _semantic(rows: list[Any]) -> set[tuple[Any, ...]]:
    return {
        (
            row.occurrence_key,
            row.match_id,
            row.effective_timestamp,
            row.timestamp_confidence,
            row.entrant_summary,
            row.winner,
            row.ruleset_id,
            row.seed,
            row.workflow,
            row.replay_state,
            row.entry_health,
        )
        for row in rows
    }


def test_cache_deletion_and_rebuild_reproduces_equivalent_rows(tree: Path) -> None:
    runs = tree / "runs"
    _write_run(runs, "_designer/20260911-120000-aaaaaaaa")
    _write_run(runs, "other/v1", schema_version=1)
    _write_run(runs, "other/no-replay", with_replay=False)
    cache = tree / "cache" / "index.sqlite3"
    with _service(tree) as service:
        service.refresh()
        first = _semantic(_all_rows(service))
    assert cache.exists()
    for sidecar in (cache, Path(str(cache) + "-wal"), Path(str(cache) + "-shm")):
        sidecar.unlink(missing_ok=True)
    with _service(tree) as service:
        assert service.cache_report.rebuild_required
        service.refresh()
        second = _semantic(_all_rows(service))
    assert first == second
    assert len(first) == 3


def test_corrupt_cache_is_discarded_and_rebuilt(tree: Path) -> None:
    runs = tree / "runs"
    _write_run(runs, "other/run-1")
    cache = tree / "cache" / "index.sqlite3"
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_bytes(b"this is definitely not a sqlite database" * 64)
    before = _snapshot(runs)
    with _service(tree) as service:
        assert service.cache_report.rebuild_required
        assert service.cache_report.recovered_from
        service.refresh()
        assert service.row_count() == 1
    assert _snapshot(runs) == before


def test_failed_rebuild_leaves_the_previous_generation_intact(
    tree: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runs = tree / "runs"
    _write_run(runs, "other/run-1")
    _write_run(runs, "other/run-2")
    with _service(tree) as service:
        service.refresh()
        good = _semantic(_all_rows(service))
        good_generation = service.generation

    calls = {"n": 0}
    real_normalize = ArtifactScanner.normalize

    def exploding(self: ArtifactScanner, candidate: Any) -> Any:
        calls["n"] += 1
        if calls["n"] == 2:
            raise OSError("deterministic mid-rebuild failure")
        return real_normalize(self, candidate)

    monkeypatch.setattr(ArtifactScanner, "normalize", exploding)
    with _service(tree) as service:
        with pytest.raises(OSError, match="deterministic mid-rebuild failure"):
            service.rebuild()
        assert _semantic(_all_rows(service)) == good
        assert service.generation == good_generation


def test_cancelled_rebuild_commits_nothing(tree: Path) -> None:
    runs = tree / "runs"
    for index in range(600):
        _write_run(runs, f"other/run-{index:04d}", with_replay=False)
    with _service(tree) as service:
        summary = service.rebuild(cancel_check=lambda: True)
        assert summary.committed is False
        assert service.is_empty()


def test_rebuild_from_an_empty_corpus_is_a_clean_empty_index(tree: Path) -> None:
    with _service(tree) as service:
        summary = service.refresh()
        assert summary.committed is True
        assert service.row_count() == 0
        page = service.fetch_page()
    assert page.rows == ()
    assert page.next_cursor is None
    assert page.has_more is False


def test_rebuild_never_writes_beneath_the_run_tree(tree: Path) -> None:
    runs = tree / "runs"
    _write_run(runs, "other/run-1")
    _write_run(runs, "other/run-2", schema_version=1)
    before = _snapshot(runs)
    with _service(tree) as service:
        service.rebuild()
        service.rebuild()
    assert _snapshot(runs) == before
    assert not (runs / "cache").exists()


# ---------------------------------------------------------------------------
# Gate 4 -- incremental reconciliation
# ---------------------------------------------------------------------------


def test_reconcile_adds_only_the_new_artifact(tree: Path) -> None:
    runs = tree / "runs"
    _write_run(runs, "other/run-1")
    with _service(tree) as service:
        service.refresh()
    _write_run(runs, "other/run-2")
    with _service(tree) as service:
        summary = service.reconcile()
    assert summary.added == 1
    assert summary.unchanged == 1
    assert summary.updated == 0
    assert summary.removed == 0


def test_reconcile_reparses_a_changed_result_and_drops_stale_fields(tree: Path) -> None:
    runs = tree / "runs"
    occurrence = "11111111-1111-1111-1111-111111111111"
    _write_run(runs, "other/run-1", occurrence_id=occurrence, winner="A", seed=1)
    with _service(tree) as service:
        service.refresh()
    _write_run(
        runs,
        "other/run-1",
        occurrence_id=occurrence,
        winner="B",
        seed=99,
        completed_at="2027-01-02T03:04:05.000000Z",
    )
    os.utime(runs / "other" / "run-1" / "result.json", ns=(2_000_000_000 * 10**9,) * 2)
    with _service(tree) as service:
        summary = service.reconcile()
        row = _all_rows(service)[0]
    assert summary.updated == 1
    assert summary.replaced == 0
    assert row.winner == "B"
    assert row.seed == 99
    assert row.effective_timestamp == "2027-01-02T03:04:05.000000Z"


def test_a_different_occurrence_at_the_same_path_replaces_the_row(tree: Path) -> None:
    runs = tree / "runs"
    _write_run(runs, "other/run-1", occurrence_id="11111111-1111-1111-1111-111111111111")
    with _service(tree) as service:
        service.refresh()
    _write_run(runs, "other/run-1", occurrence_id="22222222-2222-2222-2222-222222222222")
    os.utime(runs / "other" / "run-1" / "result.json", ns=(2_000_000_000 * 10**9,) * 2)
    with _service(tree) as service:
        summary = service.reconcile()
        rows = _all_rows(service)
    assert summary.replaced == 1
    assert summary.updated == 0
    assert len(rows) == 1
    assert rows[0].occurrence_id == "22222222-2222-2222-2222-222222222222"


def test_reconcile_removes_a_deleted_run_directory(tree: Path) -> None:
    runs = tree / "runs"
    _write_run(runs, "other/run-1")
    _write_run(runs, "other/run-2")
    with _service(tree) as service:
        service.refresh()
        assert service.row_count() == 2
    for path in sorted((runs / "other" / "run-2").iterdir()):
        path.unlink()
    (runs / "other" / "run-2").rmdir()
    with _service(tree) as service:
        summary = service.reconcile()
        assert summary.removed == 1
        assert service.row_count() == 1


def test_deleted_result_with_surviving_replay_becomes_replay_only(tree: Path) -> None:
    runs = tree / "runs"
    _write_run(runs, "other/run-1")
    with _service(tree) as service:
        service.refresh()
        assert _all_rows(service)[0].entry_health is EntryHealth.HEALTHY
    (runs / "other" / "run-1" / "result.json").unlink()
    with _service(tree) as service:
        summary = service.reconcile()
        row = _all_rows(service)[0]
    assert summary.removed == 0
    assert summary.replaced + summary.updated == 1
    assert row.result_health is ResultHealth.MISSING
    assert row.entry_health is EntryHealth.INCOMPLETE
    assert row.replay_state is ReplayState.AVAILABLE


def test_deleted_replay_keeps_the_row_and_marks_it_missing(tree: Path) -> None:
    runs = tree / "runs"
    _write_run(runs, "other/run-1")
    with _service(tree) as service:
        service.refresh()
    (runs / "other" / "run-1" / "replay.jsonl").unlink()
    with _service(tree) as service:
        summary = service.reconcile()
        row = _all_rows(service)[0]
        resolution = service.resolve_replay(row.location_id)
    assert summary.removed == 0
    assert summary.updated == 1
    assert row.replay_state is ReplayState.MISSING
    assert row.entry_health is EntryHealth.DEGRADED
    assert row.winner == "B"
    assert resolution.available is False


def test_moved_v1_artifact_is_a_delete_plus_add(tree: Path) -> None:
    runs = tree / "runs"
    _write_run(runs, "other/before", schema_version=1)
    with _service(tree) as service:
        service.refresh()
        original = _all_rows(service)[0].occurrence_key
    (runs / "other" / "before").rename(runs / "other" / "after")
    with _service(tree) as service:
        summary = service.reconcile()
        rows = _all_rows(service)
    assert summary.added == 1
    assert summary.removed == 1
    assert len(rows) == 1
    assert rows[0].occurrence_key != original


def test_moved_v2_artifact_keeps_its_authoritative_occurrence_identity(tree: Path) -> None:
    runs = tree / "runs"
    occurrence = "33333333-3333-3333-3333-333333333333"
    _write_run(runs, "other/before", occurrence_id=occurrence)
    with _service(tree) as service:
        service.refresh()
    (runs / "other" / "before").rename(runs / "other" / "after")
    with _service(tree) as service:
        summary = service.reconcile()
        rows = _all_rows(service)
    assert summary.added == 1
    assert summary.removed == 1
    assert [row.occurrence_id for row in rows] == [occurrence]


def _walk_denying(relative_target: str) -> Any:
    """A walker that mimics a directory whose listing fails at scan time."""

    real_walk = os.walk

    def walker(top: str, onerror: Any = None, followlinks: bool = False) -> Iterator[Any]:
        target = os.path.join(top, *relative_target.split("/"))
        parent = os.path.dirname(target)
        basename = os.path.basename(target)
        for dirpath, dirnames, filenames in real_walk(
            top, onerror=onerror, followlinks=followlinks
        ):
            if os.path.normcase(dirpath) == os.path.normcase(parent) and basename in dirnames:
                dirnames.remove(basename)
                error = PermissionError(13, "simulated directory denial")
                error.filename = target
                if onerror is not None:
                    onerror(error)
            yield dirpath, dirnames, filenames

    return walker


def test_an_inaccessible_subtree_never_causes_a_false_deletion(
    tree: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runs = tree / "runs"
    _write_run(runs, "other/visible")
    _write_run(runs, "restricted/hidden-1")
    _write_run(runs, "restricted/hidden-2")
    with _service(tree) as service:
        service.refresh()
        assert service.row_count() == 3

    monkeypatch.setattr(
        "battle_engine.replay_history.discovery.os.walk", _walk_denying("restricted")
    )
    with _service(tree) as service:
        summary = service.reconcile()
        assert summary.removed == 0
        assert summary.retained_inaccessible == 2
        assert summary.scan_complete is False
        assert summary.diagnostics
        assert service.row_count() == 3


def test_scan_scope_distinguishes_deleted_from_unreachable() -> None:
    scope = ScanScope(root_enumerated=True)
    scope.record_enumerated("")
    scope.record_enumerated("other")
    scope.record_failure("restricted")
    # A directory under a fully enumerated parent that was not seen is gone.
    assert scope.is_definitively_absent("other/gone") is True
    # A directory under a subtree whose listing failed is merely unreachable.
    assert scope.is_definitively_absent("restricted/hidden") is False
    # A run root that could not be enumerated at all proves nothing.
    unknown = ScanScope()
    assert unknown.is_definitively_absent("anything") is False


def test_failed_reconcile_rolls_back_and_keeps_the_prior_generation(
    tree: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runs = tree / "runs"
    _write_run(runs, "other/run-1")
    with _service(tree) as service:
        service.refresh()
        baseline = _semantic(_all_rows(service))
        generation = service.generation
    _write_run(runs, "other/run-2")

    real_normalize = ArtifactScanner.normalize

    def exploding(self: ArtifactScanner, candidate: Any) -> Any:
        if candidate.relative_directory.endswith("run-2"):
            raise OSError("deterministic reconcile failure")
        return real_normalize(self, candidate)

    monkeypatch.setattr(ArtifactScanner, "normalize", exploding)
    with _service(tree) as service:
        with pytest.raises(OSError, match="deterministic reconcile failure"):
            service.reconcile()
        assert _semantic(_all_rows(service)) == baseline
        assert service.generation == generation


def test_unchanged_detection_does_not_reparse(
    tree: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runs = tree / "runs"
    for index in range(5):
        _write_run(runs, f"other/run-{index}")
    with _service(tree) as service:
        service.refresh()

    calls = {"n": 0}
    real_normalize = ArtifactScanner.normalize

    def counting(self: ArtifactScanner, candidate: Any) -> Any:
        calls["n"] += 1
        return real_normalize(self, candidate)

    monkeypatch.setattr(ArtifactScanner, "normalize", counting)
    with _service(tree) as service:
        summary = service.reconcile()
    assert summary.unchanged == 5
    assert calls["n"] == 0


# ---------------------------------------------------------------------------
# Gate 5 -- query, filter, ordering, paging, detail
# ---------------------------------------------------------------------------


@pytest.fixture()
def populated(tmp_path: Path) -> Iterator[ReplayHistoryService]:
    runs = tmp_path / "runs"
    runs.mkdir()
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    _write_run(
        runs,
        "_designer/20260101-000000-aaaaaaaa",
        occurrence_id="00000000-0000-0000-0000-000000000001",
        completed_at=(base + timedelta(days=1)).isoformat().replace("+00:00", "Z"),
        winner="B",
        seed=11,
        ruleset_id="bytefray-rules-4",
        entrants=(("A", "Alpha Wolf"), ("B", "Beta Ray")),
        match_id="match_designer",
    )
    _write_run(
        runs,
        "tournaments/cup/matches/0001",
        occurrence_id="00000000-0000-0000-0000-000000000002",
        completed_at=(base + timedelta(days=2)).isoformat().replace("+00:00", "Z"),
        winner="tie",
        seed=22,
        ruleset_id="bytefray-rules-1",
        entrants=(("A", "Gamma"), ("B", "Delta")),
        match_id="match_tournament",
        with_replay=False,
    )
    _write_run(
        runs,
        "evaluations/eval-1/matches/0001",
        occurrence_id="00000000-0000-0000-0000-000000000003",
        completed_at=(base + timedelta(days=3)).isoformat().replace("+00:00", "Z"),
        winner="A",
        seed=33,
        ruleset_id=None,
        mode="redcode94",
        replay_filename=None,
        entrants=(("A", "Epsilon"), ("B", "Zeta")),
        match_id="match_eval",
    )
    (runs / "other" / "broken").mkdir(parents=True)
    (runs / "other" / "broken" / "result.json").write_text("{oops", encoding="utf-8")
    service = ReplayHistoryService.open(
        data_root=tmp_path, cache_path=tmp_path / "cache" / "index.sqlite3"
    )
    service.refresh()
    yield service
    service.close()


def test_default_ordering_is_newest_first_with_unknowns_last(populated: Any) -> None:
    rows = _all_rows(populated)
    recorded = [row for row in rows if row.match_id is not None]
    assert [row.match_id for row in recorded] == [
        "match_eval",
        "match_tournament",
        "match_designer",
    ]
    ordering = [
        (not row.timestamp_known, -row.effective_timestamp_ns, row.location_id) for row in rows
    ]
    assert ordering == sorted(ordering)


def test_entrant_search_is_case_insensitive_substring(populated: Any) -> None:
    assert populated.count(HistoryQuery(entrant_text="alpha")) == 1
    assert populated.count(HistoryQuery(entrant_text="ALPHA")) == 1
    assert populated.count(HistoryQuery(entrant_text="lph")) == 1
    assert populated.count(HistoryQuery(entrant_text="ray")) == 1
    # Matches either entrant of a multi-entrant row, once.
    assert populated.count(HistoryQuery(entrant_text="a")) >= 1
    assert populated.count(HistoryQuery(entrant_text="nobody")) == 0


def test_entrant_search_treats_wildcards_as_literal_text(populated: Any) -> None:
    assert populated.count(HistoryQuery(entrant_text="%")) == 0
    assert populated.count(HistoryQuery(entrant_text="_")) == 0
    assert populated.count(HistoryQuery(entrant_text="'; DROP TABLE occurrence; --")) == 0
    # The table is unharmed: a filter value is data, never statement text.
    assert populated.count() == 4


def test_ruleset_filter_supports_historical_ids_and_unrecorded_rows(populated: Any) -> None:
    assert populated.count(HistoryQuery(ruleset_ids=["bytefray-rules-1"])) == 1
    assert populated.count(HistoryQuery(ruleset_ids=["bytefray-rules-4"])) == 1
    assert (
        populated.count(HistoryQuery(ruleset_ids=["bytefray-rules-1", "bytefray-rules-4"])) == 2
    )
    assert populated.count(HistoryQuery(ruleset_ids=[None])) == 2
    assert populated.count(HistoryQuery(ruleset_confidences=["not_applicable"])) == 1
    assert populated.count(HistoryQuery(ruleset_ids=[])) == 0


def test_result_filter_covers_winner_tie_and_unknown(populated: Any) -> None:
    assert populated.count(HistoryQuery(outcome_states=[OutcomeState.TIE])) == 1
    assert populated.count(HistoryQuery(outcome_states=[OutcomeState.WINNER])) == 2
    assert populated.count(HistoryQuery(outcome_states=[OutcomeState.UNKNOWN])) == 1
    assert populated.count(HistoryQuery(winner="tie")) == 1
    assert populated.count(HistoryQuery(entry_healths=[EntryHealth.INVALID])) == 1


def test_date_range_filters_and_excludes_unknown_dates(populated: Any) -> None:
    start = datetime(2026, 1, 2, tzinfo=timezone.utc)
    end = datetime(2026, 1, 3, 12, tzinfo=timezone.utc)
    assert populated.count(HistoryQuery(start=start, end=end)) == 2
    assert populated.count(HistoryQuery(start=datetime(2030, 1, 1, tzinfo=timezone.utc))) == 0
    # The malformed row has a filesystem-fallback date, so it is comparable;
    # a genuinely unknown date is excluded while a bound is active.
    assert populated.count(HistoryQuery(end=datetime(2020, 1, 1, tzinfo=timezone.utc))) == 0


def test_exact_seed_filter(populated: Any) -> None:
    assert populated.count(HistoryQuery(seed=22)) == 1
    assert populated.count(HistoryQuery(seed=999)) == 0


def test_workflow_filter_uses_stable_internal_identifiers(populated: Any) -> None:
    assert populated.count(HistoryQuery(workflows=[WorkflowSource.TOURNAMENT])) == 1
    assert (
        populated.count(
            HistoryQuery(workflows=[WorkflowSource.TOURNAMENT, WorkflowSource.EVALUATION])
        )
        == 2
    )


def test_replay_state_filter(populated: Any) -> None:
    assert populated.count(HistoryQuery(replay_states=[ReplayState.AVAILABLE])) == 1
    assert populated.count(HistoryQuery(replay_states=[ReplayState.MISSING])) == 1
    assert populated.count(HistoryQuery(replay_states=[ReplayState.NOT_PRODUCED])) == 1


def test_combined_filters_compose(populated: Any) -> None:
    query = HistoryQuery(
        entrant_text="gamma",
        workflows=[WorkflowSource.TOURNAMENT],
        outcome_states=[OutcomeState.TIE],
        seed=22,
    )
    rows = _all_rows(populated, query)
    assert [row.match_id for row in rows] == ["match_tournament"]
    assert populated.count(HistoryQuery(entrant_text="gamma", seed=11)) == 0


def test_match_id_filter_groups_deterministic_reruns(populated: Any) -> None:
    assert populated.count(HistoryQuery(match_id="match_eval")) == 1
    assert populated.count(HistoryQuery(occurrence_id="00000000-0000-0000-0000-000000000002")) == 1


def test_detail_retrieval_exposes_the_full_normalized_record(populated: Any) -> None:
    row = next(row for row in _all_rows(populated) if row.match_id == "match_designer")
    detail = populated.fetch_detail(row.location_id)
    assert detail is not None
    occurrence = detail.occurrence
    assert occurrence.product_version == "5.0.0a1"
    assert occurrence.result_schema_version == 2
    assert occurrence.termination_reason == "tick_limit"
    assert occurrence.ticks == 10
    assert occurrence.score == {"A": 1.0, "B": 1.0}
    assert occurrence.configuration["arena_size"] == 512
    assert [entrant.display_name for entrant in detail.entrants] == ["Alpha Wolf", "Beta Ray"]
    assert detail.entrants[0].content_hash == "sha-A"
    assert detail.entrants[0].api_version == 2
    assert detail.entrants[0].parameters == {"reach": 4}
    assert detail.result_path is not None and detail.result_path.endswith("result.json")
    assert detail.replay_path is not None
    assert occurrence.result_fingerprint.size is not None
    assert detail.first_seen_at


def test_detail_for_an_unknown_location_is_none(populated: Any) -> None:
    assert populated.fetch_detail("loc_does_not_exist") is None
    resolution = populated.resolve_replay("loc_does_not_exist")
    assert resolution.state is ReplayState.UNCHECKED


def test_keyset_paging_is_stable_across_more_than_one_page(tmp_path: Path) -> None:
    runs = tmp_path / "runs"
    runs.mkdir()
    total = 1_205
    shared = "2026-05-05T05:05:05.000000Z"
    for index in range(total):
        # Deliberately repeat one timestamp across many rows so the ordering's
        # tie-breaker, not the clock, is what makes paging stable.
        completed = shared if index % 3 == 0 else (
            datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(seconds=index)
        ).isoformat().replace("+00:00", "Z")
        _write_run(
            runs,
            f"other/run-{index:05d}",
            completed_at=completed,
            with_replay=False,
            match_id=f"match_{index:05d}",
        )
    service = ReplayHistoryService.open(
        data_root=tmp_path, cache_path=tmp_path / "cache" / "index.sqlite3"
    )
    try:
        service.refresh()
        assert service.count() == total
        pages = []
        cursor = None
        while True:
            page = service.fetch_page(cursor=cursor)
            pages.append(page)
            if not page.has_more or page.next_cursor is None:
                break
            cursor = page.next_cursor
        assert [len(page) for page in pages] == [500, 500, 205]
        seen = [row.location_id for page in pages for row in page.rows]
        assert len(seen) == total
        assert len(set(seen)) == total
        ordering = [
            (not row.timestamp_known, -row.effective_timestamp_ns, row.location_id)
            for page in pages
            for row in page.rows
        ]
        assert ordering == sorted(ordering)
        # The same cursor replayed against an unchanged index is deterministic.
        repeat = service.fetch_page(cursor=pages[0].next_cursor)
        assert [row.location_id for row in repeat.rows] == [
            row.location_id for row in pages[1].rows
        ]
    finally:
        service.close()


def test_page_size_is_bounded_and_at_least_one(tree: Path) -> None:
    _write_run(tree / "runs", "other/run-1")
    with _service(tree) as service:
        service.refresh()
        assert len(service.fetch_page(limit=0).rows) == 1
        assert service.fetch_page(limit=10_000).page_size <= 5000


def test_in_memory_service_needs_no_persistent_cache(tree: Path) -> None:
    _write_run(tree / "runs", "other/run-1")
    service = ReplayHistoryService.open(data_root=tree, in_memory=True)
    try:
        service.refresh()
        assert service.row_count() == 1
        assert service.cache_report.persistent is False
    finally:
        service.close()
    assert not (tree / "cache").exists()


def test_index_open_rejects_nothing_but_still_reports_size(tree: Path) -> None:
    index = HistoryIndex.open(None, root_identity="test-root")
    try:
        assert index.database_size_bytes() >= 0
        assert index.is_empty()
        assert index.generation() == 0
    finally:
        index.close()


# ---------------------------------------------------------------------------
# Gate 6 -- historical compatibility and real produced artifacts
# ---------------------------------------------------------------------------


def _run_real_match(destination: Path, *, seed: int = 73) -> None:
    """Produce genuine current artifacts through the production writer."""

    from battle_engine.builtins import build_agent
    from battle_engine.config import Config, Weights
    from battle_engine.match_service import MatchEntrant, MatchRequest, NativeMatchService

    config = Config(
        arena_size=128,
        instr_per_tick=4,
        seed=seed,
        win_mode="score_fallback",
        weights=Weights(alive=0.25, kill=3.5, territory=0.5, territory_bucket=16),
    )
    entrants = (
        MatchEntrant("A", "writer", 0, build_agent("writer", 0, offset=80, byte=0x99)),
        MatchEntrant("B", "runner", 64, build_agent("runner", 64)),
    )
    destination.mkdir(parents=True, exist_ok=True)
    NativeMatchService().run(
        MatchRequest(config, entrants, 5, destination / "replay.jsonl", False)
    )


def test_real_native_artifacts_index_as_distinct_v2_occurrences(tree: Path) -> None:
    """Two byte-identical reruns are one match but two history occurrences."""

    from battle_engine.result_model import read_result, verify_replay_digest

    runs = tree / "runs"
    _run_real_match(runs / "_designer" / "20260911-120000-aaaaaaaa")
    _run_real_match(runs / "_designer" / "20260911-120500-bbbbbbbb")
    before = _snapshot(runs)

    with _service(tree) as service:
        summary = service.refresh()
        rows = _all_rows(service)
        resolutions = [service.resolve_replay(row.location_id) for row in rows]
        details = [service.fetch_detail(row.location_id) for row in rows]

    assert summary.counts.valid_entries == 2
    assert len(rows) == 2
    assert len({row.match_id for row in rows}) == 1
    assert len({row.occurrence_id for row in rows}) == 2
    assert all(row.occurrence_source is OccurrenceIdentitySource.RECORDED for row in rows)
    assert all(row.timestamp_confidence is TimestampConfidence.RECORDED for row in rows)
    assert all(row.entry_health is EntryHealth.HEALTHY for row in rows)
    assert all(row.replay_state is ReplayState.AVAILABLE for row in rows)
    assert not any(row.duplicate_occurrence_location for row in rows)
    assert {detail.occurrence.result_schema_version for detail in details} == {2}
    assert all(detail.occurrence.product_version for detail in details)

    # The recorded digest the service hands on really does verify, and the
    # resolved path is the artifact the production writer produced.
    for resolution in resolutions:
        assert resolution.available
        envelope = read_result(Path(resolution.path).with_name("result.json"))
        assert verify_replay_digest(envelope, resolution.path) == resolution.expected_sha256

    # Indexing a real corpus leaves it byte-for-byte unchanged.
    assert _snapshot(runs) == before


def test_mixed_era_corpus_needs_no_migration_and_survives_a_cache_rebuild(
    tree: Path,
) -> None:
    runs = tree / "runs"
    shared_occurrence = "44444444-4444-4444-4444-444444444444"
    _run_real_match(runs / "_designer" / "20260911-120000-aaaaaaaa")
    _write_run(runs, "other/v1-legacy", schema_version=1, ruleset_id="bytefray-rules-1")
    _write_run(
        runs,
        "other/v1-rerun",
        schema_version=1,
        ruleset_id="bytefray-rules-1",
        match_id="match_aaaaaaaaaaaaaaaaaaaaaaaa",
    )
    _write_run(runs, "other/v2-copy-a", occurrence_id=shared_occurrence)
    _write_run(runs, "other/v2-copy-b", occurrence_id=shared_occurrence)
    _write_run(runs, "other/no-replay", with_replay=False)
    _write_run(
        runs,
        "other/pmars",
        schema_version=1,
        mode="redcode94",
        ruleset_id=None,
        replay_filename=None,
    )
    (runs / "other" / "corrupt").mkdir(parents=True)
    (runs / "other" / "corrupt" / "result.json").write_text("{broken", encoding="utf-8")
    orphan = runs / "other" / "replay-only"
    orphan.mkdir(parents=True)
    (orphan / "replay.jsonl").write_text(
        _replay_header_line(_result_payload(schema_version=1)), encoding="utf-8"
    )
    before = _snapshot(runs)

    with _service(tree) as service:
        service.refresh()
        first = _semantic(_all_rows(service))
        healths = {
            health: service.count(HistoryQuery(entry_healths=[health]))
            for health in EntryHealth
        }
        schemas = {
            detail.occurrence.result_schema_version
            for detail in (
                service.fetch_detail(row.location_id) for row in _all_rows(service)
            )
        }
        duplicates = [row for row in _all_rows(service) if row.duplicate_occurrence_location]
        rulesets = {row.ruleset_id for row in _all_rows(service)}

    assert healths == {
        EntryHealth.HEALTHY: 6,
        EntryHealth.DEGRADED: 1,
        EntryHealth.INCOMPLETE: 1,
        EntryHealth.INVALID: 1,
    }
    assert schemas == {1, 2, None}
    assert len(duplicates) == 2
    assert "bytefray-rules-1" in rulesets
    assert "bytefray-rules-4" in rulesets

    # Deleting the derived cache loses no history and changes no semantics.
    for suffix in ("", "-wal", "-shm"):
        Path(str(tree / "cache" / "index.sqlite3") + suffix).unlink(missing_ok=True)
    with _service(tree) as service:
        service.refresh()
        second = _semantic(_all_rows(service))
    assert first == second
    assert _snapshot(runs) == before


def test_filter_values_are_bound_parameters_not_statement_text(populated: Any) -> None:
    hostile = "bytefray-rules-1'; DROP TABLE occurrence; --"
    assert populated.count(HistoryQuery(ruleset_ids=[hostile])) == 0
    assert populated.count(HistoryQuery(winner="' OR 1=1 --")) == 0
    assert populated.count(HistoryQuery(match_id='"; DELETE FROM occurrence_entrant; --')) == 0
    assert populated.count(HistoryQuery(ruleset_confidences=["recorded'--"])) == 0
    assert populated.count() == 4
    assert populated.fetch_detail("loc_'; DROP TABLE occurrence; --") is None
    assert populated.count() == 4


def test_discovery_imports_no_agent_module_and_runs_no_agent_code(tree: Path) -> None:
    """An artifact naming an agent module must never cause it to be imported."""

    runs = tree / "runs"
    directory = runs / "other" / "hostile"
    directory.mkdir(parents=True)
    payload = _result_payload(schema_version=1)
    payload["entrants"][0]["metadata"]["entry_point"] = "sitecustomize.py:create_agent"
    payload["entrants"][0]["metadata"]["source_path"] = str(tree / "evil_agent.py")
    (directory / "result.json").write_text(json.dumps(payload), encoding="utf-8")
    (tree / "evil_agent.py").write_text(
        "raise AssertionError('discovery must never import an agent')", encoding="utf-8"
    )
    baseline = set(sys.modules)
    with _service(tree) as service:
        service.refresh()
        row = _all_rows(service)[0]
        service.fetch_detail(row.location_id)
    assert "evil_agent" not in sys.modules
    assert set(sys.modules) - baseline == set()
    assert row.result_health is ResultHealth.VALID


def test_a_vanished_run_root_retains_every_row_rather_than_emptying_history(
    tree: Path,
) -> None:
    """An unmounted or renamed data root is not a confirmed deletion."""

    runs = tree / "runs"
    _write_run(runs, "other/run-1")
    _write_run(runs, "other/run-2")
    with _service(tree) as service:
        service.refresh()
        assert service.row_count() == 2
    runs.rename(tree / "runs-moved-away")
    with _service(tree) as service:
        summary = service.reconcile()
        assert summary.removed == 0
        assert summary.retained_inaccessible == 2
        assert service.row_count() == 2
    # Restoring the root reconciles back to unchanged, with no churn.
    (tree / "runs-moved-away").rename(runs)
    with _service(tree) as service:
        summary = service.reconcile()
        assert summary.unchanged == 2
        assert summary.removed == 0


def test_an_emptied_run_root_really_does_remove_its_rows(tree: Path) -> None:
    """The conservative deletion rule must still delete what is truly gone."""

    runs = tree / "runs"
    _write_run(runs, "other/run-1")
    with _service(tree) as service:
        service.refresh()
        assert service.row_count() == 1
    for path in sorted((runs / "other" / "run-1").iterdir()):
        path.unlink()
    (runs / "other" / "run-1").rmdir()
    (runs / "other").rmdir()
    with _service(tree) as service:
        summary = service.reconcile()
        assert summary.removed == 1
        assert summary.retained_inaccessible == 0
        assert service.row_count() == 0


# ---------------------------------------------------------------------------
# Gate 7 -- Phase 7D: click-time digest preflight (verify_replay_integrity)
# ---------------------------------------------------------------------------


def test_verify_replay_integrity_verifies_a_real_produced_replay(tree: Path) -> None:
    """A genuine current artifact's digest really does match at click time."""

    runs = tree / "runs"
    _run_real_match(runs / "_designer" / "20260911-120000-aaaaaaaa")
    with _service(tree) as service:
        service.refresh()
        row = _all_rows(service)[0]
        resolution = service.resolve_replay(row.location_id)
        assert resolution.available
        assert resolution.expected_sha256 is not None
        check = service.verify_replay_integrity(resolution)
    assert check.status is ReplayIntegrityStatus.VERIFIED
    assert check.digest == resolution.expected_sha256
    assert check.diagnostic is None


def test_verify_replay_integrity_detects_a_changed_replay(tree: Path) -> None:
    """A replay edited after indexing must block, not silently pass, the preflight."""

    runs = tree / "runs"
    _run_real_match(runs / "_designer" / "20260911-120000-aaaaaaaa")
    with _service(tree) as service:
        service.refresh()
        row = _all_rows(service)[0]
        resolution = service.resolve_replay(row.location_id)
        assert resolution.available
        # Tamper with the replay bytes without touching result.json's
        # recorded digest -- exactly the "changed replay" race Phase 7D
        # must catch rather than trust the cached AVAILABLE state.
        Path(resolution.path).write_bytes(
            Path(resolution.path).read_bytes() + b"\ntampered\n"
        )
        check = service.verify_replay_integrity(resolution)
    assert check.status is ReplayIntegrityStatus.MISMATCH
    assert check.diagnostic is not None
    assert "mismatch" in check.diagnostic.lower()


def test_verify_replay_integrity_accepts_a_legacy_replay_with_no_recorded_digest(
    tree: Path,
) -> None:
    """A replay-only entry has nothing to compare against and must not be flagged."""

    runs = tree / "runs"
    _write_run(runs, "other/replay-only")
    (runs / "other" / "replay-only" / "result.json").unlink()
    with _service(tree) as service:
        service.refresh()
        row = _all_rows(service)[0]
        resolution = service.resolve_replay(row.location_id)
        assert resolution.available
        assert resolution.expected_sha256 is None
        check = service.verify_replay_integrity(resolution)
    assert check.status is ReplayIntegrityStatus.UNVERIFIED_LEGACY
    assert check.diagnostic is None


def test_verify_replay_integrity_reports_unreadable_for_a_file_that_vanished_after_resolve(
    tree: Path,
) -> None:
    """The resolve-to-launch race: gone between resolution and the digest read."""

    runs = tree / "runs"
    _run_real_match(runs / "_designer" / "20260911-120000-aaaaaaaa")
    with _service(tree) as service:
        service.refresh()
        row = _all_rows(service)[0]
        resolution = service.resolve_replay(row.location_id)
        assert resolution.available
        Path(resolution.path).unlink()
        check = service.verify_replay_integrity(resolution)
    assert check.status is ReplayIntegrityStatus.UNREADABLE
    assert check.diagnostic is not None


def test_verify_replay_integrity_is_defensive_about_an_unavailable_resolution(
    tree: Path,
) -> None:
    """Callers must be able to pass a non-available resolution without a crash."""

    with _service(tree) as service:
        service.refresh()
        resolution = service.resolve_replay("does_not_exist")
        assert not resolution.available
        check = service.verify_replay_integrity(resolution)
    assert check.status is ReplayIntegrityStatus.UNREADABLE
    assert check.digest is None
