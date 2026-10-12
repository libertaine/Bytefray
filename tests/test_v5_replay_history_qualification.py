"""Phase 7E: actual artifacts/cache through the two-worker History window."""
from __future__ import annotations

import json
import threading
import time
from pathlib import Path

import pytest
from battle_engine.replay_history import ReplayHistoryService, ReplayState

from engine.tests.test_replay_history import (
    _replay_header_line,
    _result_payload,
    _run_real_match,
    _snapshot,
    _walk_denying,
    _write_run,
)

pytestmark = pytest.mark.gui


@pytest.fixture
def browser(tmp_path):
    from test_v5_replay_history_browser import _make_app

    from app.views.replay_history import ReplayHistoryWindow

    application = _make_app()
    windows = []

    def until(predicate, timeout=10):
        deadline = time.perf_counter() + timeout
        while time.perf_counter() < deadline:
            application.processEvents()
            if predicate():
                return
            time.sleep(.001)
        pytest.fail("History operation did not complete")

    def make():
        window = ReplayHistoryWindow(data_root=tmp_path)
        windows.append(window)
        window.show()
        return window

    yield make, until
    for window in windows:
        window.close()
    application.processEvents()


def test_large_seed_history_refresh_filter_and_clipboard_through_browser(browser, tmp_path):
    from PySide6.QtGui import QGuiApplication

    runs = tmp_path / "runs"
    seeds = (42, -(2**63), 2**63 - 1, -(2**63) - 1, 2**63, 2**64 - 1)
    for index, seed in enumerate(seeds):
        _write_run(runs, f"seed-{index}", seed=seed)
    before = _snapshot(runs)
    make, until = browser
    window = make()
    until(lambda: window._reader_ready and not window._refreshing and window.model.loadedCount == 6)
    assert {row.seed for row in window.model._rows} == set(seeds)
    position = next(i for i, row in enumerate(window.model._rows) if row.seed == 2**64 - 1)
    window.table.selectRow(position)
    until(lambda: window.copySeedButton.isEnabled())
    window.copySeedButton.click()
    assert QGuiApplication.clipboard().text() == str(2**64 - 1)
    window.seedEdit.setText(str(2**64 - 1))
    until(lambda: window.model.loadedCount == 1 and window.model._rows[0].seed == 2**64 - 1)
    window.refresh()
    until(lambda: not window._refreshing and window.model.loadedCount == 1)
    assert _snapshot(runs) == before



@pytest.mark.parametrize(
    ("start_day", "end_day", "matches"),
    (
        ((1752, 9, 14), None, 2),
        (None, (1752, 9, 14), 0),
        ((2026, 9, 11), (2026, 9, 11), 2),
        ((2262, 4, 12), None, 0),
        (None, (2262, 4, 11), 2),
        ((2500, 1, 1), None, 0),
        (None, (2500, 1, 1), 2),
        ((9999, 12, 31), None, 0),
        (None, (9999, 12, 31), 2),
        ((2500, 1, 1), (1752, 9, 14), 0),
    ),
)
def test_date_filter_range_through_real_history_window(
    browser, tmp_path, start_day, end_day, matches,
):
    from PySide6.QtCore import QDate
    from PySide6.QtGui import QGuiApplication

    runs = tmp_path / "runs"
    _write_run(runs, "ordinary", seed=42)
    _write_run(runs, "large", seed=2**64 - 1)
    before = _snapshot(runs)
    make, until = browser
    window = make()
    until(lambda: window._reader_ready and not window._refreshing and window._total == 2)
    errors = []
    pages = []
    window._reader.failed.connect(errors.append)
    window._reader.pageReady.connect(pages.append)
    prior = window._generation
    for day, date_widget, checkbox in (
        (start_day, window.fromDate, window.fromCheck),
        (end_day, window.toDate, window.toCheck),
    ):
        if day is not None:
            date_widget.setDate(QDate(*day))
            assert date_widget.date() == QDate(*day)
            checkbox.setChecked(True)
    until(lambda: window._generation > prior and bool(pages)
          and pages[-1].generation == window._generation
          and window._total == pages[-1].total
          and window.model.loadedCount == len(pages[-1].rows))
    assert not errors
    assert window._total == matches
    assert window.model.loadedCount == matches

    # Date filtering composes with exact large-seed matching and clipboard behavior.
    window.seedEdit.setText(str(2**64 - 1))
    prior = window._generation
    until(lambda: window._generation > prior and pages[-1].generation == window._generation
          and window._total == pages[-1].total)
    assert window._total == (1 if matches else 0)
    if matches:
        window.table.selectRow(0)
        until(lambda: window.copySeedButton.isEnabled())
        window.copySeedButton.click()
        assert QGuiApplication.clipboard().text() == str(2**64 - 1)
    window.clearFilters()
    until(lambda: pages[-1].generation == window._generation and window._total == 2)
    assert not errors
    assert _snapshot(runs) == before


@pytest.mark.parametrize("day", ((2026, 3, 8), (2026, 11, 1), (2026, 9, 11)))
def test_designer_date_bounds_preserve_ordinary_local_day(browser, tmp_path, day):
    from PySide6.QtCore import QDate

    from app.services.replay_history_presentation import day_bounds

    _write_run(tmp_path / "runs", "ordinary")
    make, until = browser
    window = make()
    until(lambda: window._reader_ready and not window._refreshing)
    window.fromDate.setDate(QDate(*day))
    window.toDate.setDate(QDate(*day))
    window.fromCheck.setChecked(True)
    window.toCheck.setChecked(True)
    filters = window._currentFilters()
    assert (filters.start_date, filters.end_date) == day_bounds(*day)



@pytest.mark.parametrize("date_parts", (None, (2026, 2, 29)))
def test_designer_date_bound_rejects_invalid_calendar_dates(date_parts):
    from PySide6.QtCore import QDate

    from app.views.replay_history import _local_date_bound

    date = QDate() if date_parts is None else QDate(*date_parts)
    with pytest.raises(ValueError, match="Invalid history filter date"):
        _local_date_bound(date, end=False)
    with pytest.raises(ValueError, match="Invalid history filter date"):
        _local_date_bound(date, end=True)


def test_designer_date_bound_rejects_unresolved_qt_calendar(monkeypatch):
    from PySide6.QtCore import QDate, QDateTime

    from app.views import replay_history as view

    def unsupported_day(*_args):
        raise OSError("isolated Windows calendar conversion failure")

    monkeypatch.setattr(view, "day_bounds", unsupported_day)
    monkeypatch.setattr(view, "QDateTime", lambda *_args: QDateTime())
    for end in (False, True):
        with pytest.raises(ValueError, match="could not be resolved"):
            view._local_date_bound(QDate(9999, 12, 31), end=end)



def test_designer_rejected_calendar_keeps_query_and_reports_error(browser, tmp_path, monkeypatch):
    from PySide6.QtCore import QDate, QDateTime

    from app.views import replay_history as view

    _write_run(tmp_path / "runs", "ordinary")
    make, until = browser
    window = make()
    until(lambda: window._reader_ready and not window._refreshing and window._total == 1)
    prior_query = window._query
    requests = []
    window.pageRequested.connect(lambda *args: requests.append(args))

    def unsupported_day(*_args):
        raise OSError("isolated Windows calendar conversion failure")

    with monkeypatch.context() as patch:
        patch.setattr(view, "day_bounds", unsupported_day)
        patch.setattr(view, "QDateTime", lambda *_args: QDateTime())
        window.fromDate.setDate(QDate(9999, 12, 31))
        window.fromCheck.setChecked(True)
        assert "could not be resolved" in window.statusLabel.text()
        assert window._query == prior_query
        assert not requests
        assert window._total == 1
    # The same valid date resolves and filters normally once calendar conversion works.
    window._applyFilters()
    until(lambda: window._total == 0)
    assert requests


def mixed_corpus(root: Path):
    runs = root / "runs"
    _run_real_match(runs / "healthy")
    _write_run(runs, "_designer/20250911-120000-aaaaaaaa", schema_version=1)
    _write_run(runs, "v1-fallback", schema_version=1)
    _write_run(runs, "v2-rerun-a")
    _write_run(runs, "v2-rerun-b")
    copied = "44444444-4444-4444-4444-444444444444"
    _write_run(runs, "copied-a", occurrence_id=copied)
    _write_run(runs, "copied-b", occurrence_id=copied)
    _write_run(runs, "missing", with_replay=False)
    _write_run(runs, "not-produced", schema_version=1, replay_filename=None, mode="redcode94", ruleset_id=None)
    _write_run(runs, "digest-mismatch")
    _write_run(runs, "_loose")
    for name, contents in (("malformed", "{broken"), ("unsupported", json.dumps({"schema": "battle2.result", "schema_version": 999}))):
        directory = runs / name
        directory.mkdir(parents=True)
        (directory / "result.json").write_text(contents, encoding="utf-8")
    for name, contents in (("replay-only", _replay_header_line(_result_payload(schema_version=1))), ("invalid-replay", "not a replay")):
        directory = runs / name
        directory.mkdir(parents=True)
        (directory / "replay.jsonl").write_text(contents, encoding="utf-8")
    return runs


@pytest.mark.parametrize("damage", ["absent", "deleted", "corrupt", "incompatible"])
def test_cache_preparation_and_recovery_through_browser(browser, tmp_path, monkeypatch, damage):
    from app.views import replay_history as view

    runs = mixed_corpus(tmp_path)
    before = _snapshot(runs)
    make, until = browser
    if damage != "absent":
        first = make()
        until(lambda: first._reader_ready and not first._refreshing and first.model.loadedCount == 15)
        first.close()
        cache = tmp_path / "cache/replay_history/index-v1.sqlite3"
        if damage == "deleted":
            cache.unlink()
        elif damage == "corrupt":
            cache.write_bytes(b"disposable broken cache")
        else:
            import sqlite3
            connection = sqlite3.connect(cache)
            try:
                connection.execute("PRAGMA user_version = 987")
            finally:
                connection.close()

    entered, release = threading.Event(), threading.Event()
    original = ReplayHistoryService._finish_generation

    def finish(self, generation):
        entered.set()
        assert release.wait(5)
        original(self, generation)

    monkeypatch.setattr(ReplayHistoryService, "_finish_generation", finish)
    window = make()
    try:
        until(entered.is_set)
        assert "Preparing" in window.messagePage.titleLabel.text()
        assert not window._reader_ready
        assert not window.openReplayButton.isEnabled()
    finally:
        release.set()
    until(lambda: window._reader_ready and window.model.loadedCount == 15 and not window._refreshing)
    launched = []
    monkeypatch.setattr(view, "open_pygame_client_direct", lambda *args: launched.append(args))
    monkeypatch.setattr(view.QMessageBox, "warning", lambda *args: None)
    details = {}
    for position, row in enumerate(window.model._rows):
        window.table.selectRow(position)
        until(lambda: bool(window.detailPane._sections))
        assert window.openReplayButton.isEnabled() == (row.replay_state is ReplayState.AVAILABLE)
        date = window.model.data(window.model.index(position, 0))
        assert ("≈" in date) == (row.timestamp_confidence.value in ("directory_inferred", "filesystem_fallback"))
        text = str(window.detailPane._sections)
        if row.occurrence_id is None:
            assert "synthetic" in text.lower()
        window.advancedCheck.setChecked(True)
        # Use normalized detail paths already delivered by the backend.
        details[row.location_id] = text
    assert sum(row.duplicate_occurrence_location for row in window.model._rows) == 2
    assert len({row.location_id for row in window.model._rows}) == 15
    assert _snapshot(runs) == before
    assert details


def test_artifact_changes_and_inaccessible_scope_through_ui(browser, tmp_path, monkeypatch):
    from battle_engine.replay_history import discovery

    make, until = browser
    runs = tmp_path / "runs"
    directory = _write_run(runs, "protected/one")
    window = make()
    until(lambda: window._reader_ready and not window._refreshing and window.model.loadedCount == 1)
    with monkeypatch.context() as patch:
        patch.setattr(discovery.os, "walk", _walk_denying("protected"))
        window.refresh()
        until(lambda: not window._refreshing)
        assert window.model.loadedCount == 1
    (directory / "replay.jsonl").unlink()
    window.refresh()
    until(lambda: not window._refreshing and window.model._rows[0].replay_state is ReplayState.MISSING)
    window.table.selectRow(0)
    assert not window.openReplayButton.isEnabled()
    (directory / "result.json").unlink()
    directory.rmdir()
    window.refresh()
    until(lambda: not window._refreshing and window.model.loadedCount == 0)


def test_real_replay_handoff_integrity_and_legacy_policy(browser, tmp_path, monkeypatch):
    from app.views import replay_history as view

    runs = mixed_corpus(tmp_path)
    before = _snapshot(runs)
    make, until = browser
    window = make()
    until(lambda: window.model.loadedCount == 15 and not window._refreshing)
    launches, warnings = [], []
    monkeypatch.setattr(view, "open_pygame_client_direct", lambda *args: launches.append(args))
    monkeypatch.setattr(view.QMessageBox, "warning", lambda *args: warnings.append(args))
    with ReplayHistoryService.open(data_root=tmp_path, read_only=True) as reader:
        locations = {
            reader.fetch_detail(row.location_id).occurrence.relative_directory: row.location_id
            for row in reader.fetch_page().rows
        }
    for relative, expected_launches in (("healthy", 1), ("digest-mismatch", 1), ("replay-only", 2)):
        window.table.selectRow(window.model.positionOf(locations[relative]))
        window._activateOpenReplay()
        until(lambda: not window._open_pending)
        assert len(launches) == expected_launches
    assert len(warnings) == 1
    assert launches[0][1] == runs / "healthy/replay.jsonl"
    assert launches[1][1] == runs / "replay-only/replay.jsonl"
    assert _snapshot(runs) == before


def test_session_only_cache_retains_existing_fallback_without_second_database(browser, tmp_path, monkeypatch):
    make, until = browser
    _write_run(tmp_path / "runs", "one")
    original = ReplayHistoryService.open.__func__
    calls = []

    def open_service(cls, **kwargs):
        calls.append(kwargs.get("read_only"))
        kwargs["in_memory"] = True
        return original(cls, **kwargs)

    monkeypatch.setattr(ReplayHistoryService, "open", classmethod(open_service))
    window = make()
    until(lambda: window.model.loadedCount == 1 and not window._refreshing)
    assert not window._persistent
    assert calls == [False]
    assert not (tmp_path / "cache").exists()
    window.table.selectRow(0)
    until(lambda: bool(window.detailPane._sections))


def test_cancelled_reconcile_preserves_committed_rows_and_next_refresh_succeeds(browser, tmp_path, monkeypatch):
    make, until = browser
    _write_run(tmp_path / "runs", "old")
    window = make()
    until(lambda: window.model.loadedCount == 1 and not window._refreshing)
    _write_run(tmp_path / "runs", "new")
    entered, release = threading.Event(), threading.Event()
    original = ReplayHistoryService._reconciled

    def reconciled(service, *args, **kwargs):
        entered.set()
        assert release.wait(5)
        yield from original(service, *args, **kwargs)

    with monkeypatch.context() as patch:
        patch.setattr(ReplayHistoryService, "_reconciled", reconciled)
        window.refresh()
        try:
            until(entered.is_set)
            window.table.selectRow(0)
            until(lambda: bool(window.detailPane._sections))
            assert window._refreshing and window.model.loadedCount == 1
            window.cancelRefresh()
        finally:
            release.set()
        until(lambda: not window._refreshing)
    assert "cancelled" in window.statusLabel.text().lower()
    assert window.model.loadedCount == 1
    window.refresh()
    until(lambda: not window._refreshing and window.model.loadedCount == 2)


def test_designer_shutdown_with_both_history_operations_active(browser, tmp_path, monkeypatch):
    from PySide6.QtCore import QTimer
    from test_v5_replay_history_browser import _designer

    from app.views import replay_history as view

    _run_real_match(tmp_path / "runs/healthy")
    _, until = browser
    designer = _designer(monkeypatch, tmp_path)
    launches = []
    monkeypatch.setattr(view, "open_pygame_client_direct", lambda *args: launches.append(args))
    release = threading.Event()
    try:
        designer._on_replay_history()
        window = designer._replay_history
        until(lambda: window._reader_ready and window.model.loadedCount == 1 and not window._refreshing)
        window.table.selectRow(0)
        writer_entered, reader_entered = threading.Event(), threading.Event()
        original_finish = ReplayHistoryService._finish_generation
        original_resolve = ReplayHistoryService.resolve_replay

        def finish(service, generation):
            writer_entered.set()
            assert release.wait(5)
            original_finish(service, generation)

        def resolve(service, location):
            reader_entered.set()
            assert release.wait(5)
            return original_resolve(service, location)

        monkeypatch.setattr(ReplayHistoryService, "_finish_generation", finish)
        monkeypatch.setattr(ReplayHistoryService, "resolve_replay", resolve)
        window.refresh()
        until(writer_entered.is_set)
        window._activateOpenReplay()
        until(reader_entered.is_set)
        QTimer.singleShot(20, release.set)
        designer.close()
        assert not window._reader_thread.isRunning() and not window._thread.isRunning()
        assert not launches
    finally:
        release.set()
        designer.close()


def test_repeated_concurrent_close_reopen_preserves_ownership(browser, tmp_path, monkeypatch):
    from PySide6.QtCore import QTimer

    from app.views import replay_history as view

    _run_real_match(tmp_path / "runs/healthy")
    make, until = browser
    services, launches = [], []
    original_open = ReplayHistoryService.open.__func__

    def instrumented_open(cls, **kwargs):
        service = original_open(cls, **kwargs)
        owner = threading.get_ident()
        record = {"owner": owner, "connection": id(service._index.connection), "closed": False}
        services.append(record)
        original_close = service.close

        def close():
            assert threading.get_ident() == owner
            original_close()
            record["closed"] = True

        service.close = close
        return service

    monkeypatch.setattr(ReplayHistoryService, "open", classmethod(instrumented_open))
    monkeypatch.setattr(view, "open_pygame_client_direct", lambda *args: launches.append(args))
    for cycle in range(12):
        window = make()
        until(lambda window=window: window._reader_ready and window.model.loadedCount == 1 and not window._refreshing)
        window.table.selectRow(0)
        until(lambda window=window: bool(window.detailPane._sections))
        window._onCopySeedClicked()
        writer_entered, reader_entered, release = threading.Event(), threading.Event(), threading.Event()
        original_finish = ReplayHistoryService._finish_generation
        original_resolve = ReplayHistoryService.resolve_replay

        def finish(service, generation, writer_entered=writer_entered, release=release, original_finish=original_finish):
            writer_entered.set()
            assert release.wait(5)
            original_finish(service, generation)

        def resolve(service, location, reader_entered=reader_entered, release=release, original_resolve=original_resolve):
            reader_entered.set()
            assert release.wait(5)
            return original_resolve(service, location)

        with monkeypatch.context() as patch:
            patch.setattr(ReplayHistoryService, "_finish_generation", finish)
            patch.setattr(ReplayHistoryService, "resolve_replay", resolve)
            window.refresh()
            until(writer_entered.is_set)
            window._activateOpenReplay()
            until(reader_entered.is_set)
            # This GUI timer must fire even while close is joining the workers.
            QTimer.singleShot(20, release.set)
            window.close()
        assert not window._thread.isRunning() and not window._reader_thread.isRunning()
        assert all(record["closed"] for record in services), services
        latest = services[-2:]
        assert latest[0]["owner"] != latest[1]["owner"]
        assert latest[0]["connection"] != latest[1]["connection"]
        assert len(services) == 2 * (cycle + 1)
        assert not launches
