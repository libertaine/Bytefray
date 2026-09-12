"""V5 Phase 7C -- the Qt half of the Replay History browser.

Covers ``ReplayHistoryWorker`` (thread ownership, lifecycle, cancellation,
error capture), ``ReplayHistoryTableModel`` (headers, cell formatting, lazy
keyset paging, reset semantics), ``ReplayHistoryWindow`` (filters, debounce,
stale-response suppression, detail selection, empty/error states, shutdown),
and ``AgentDesigner`` wiring (the Tools action opens the browser, reuses it,
and joins its worker on Designer shutdown).

The invariant most of these tests exist to defend:

> The GUI thread never constructs, uses, or closes the Replay History
> ``ReplayHistoryService``.

It is asserted mechanically, not by inspection: the fake service records the
thread identity of every call it receives, and the tests compare those against
the GUI thread. A future change that "simplifies" a call back onto the GUI
thread fails here rather than shipping as an intermittent freeze.

Marked ``gui`` like the other Designer tests: excluded from the default
headless run and exercised by the dedicated display-backed workflow.
"""

from __future__ import annotations

import os
import threading
import time
from dataclasses import dataclass
from typing import Any, ClassVar

import pytest


def _make_app():
    pytest.importorskip("PySide6")
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication

    return QApplication.instance() or QApplication([])


# ----------------------------------------------------------------------
# Fake backend
#
# A stand-in for ReplayHistoryService with the same public shape. It records
# which thread every call arrived on, and lets a test hold a refresh open so
# cancellation and shutdown can be exercised deterministically.
# ----------------------------------------------------------------------


@dataclass
class _CacheReport:
    path: str = "fake"
    created: bool = False
    rebuild_required: bool = False
    rebuild_reason: str | None = None
    persistent: bool = True
    recovered_from: str | None = None


class _FakeService:
    instances: ClassVar[list[_FakeService]] = []
    #: Set to raise from ``open`` and exercise the startup-failure path.
    open_error: str | None = None
    #: Rows the fake index returns, newest first.
    corpus: ClassVar[list[Any]] = []
    #: Held open by a test to keep a refresh running.
    refresh_gate: threading.Event | None = None
    refresh_error: str | None = None
    query_error: str | None = None
    #: Held open by a test to keep an Open Replay preflight in flight.
    resolve_gate: threading.Event | None = None
    resolve_error: str | None = None
    #: location_id -> ReplayResolution / ReplayIntegrityCheck override, for
    #: tests that need a specific click-time outcome (missing, mismatch, …).
    #: A location absent from these maps gets a plain AVAILABLE/VERIFIED
    #: answer built from its own row, matching a healthy real backend.
    resolve_overrides: ClassVar[dict[str, Any]] = {}
    integrity_overrides: ClassVar[dict[str, Any]] = {}
    resolve_calls: ClassVar[list[str]] = []

    def __init__(self) -> None:
        self.threads: dict[str, int] = {}
        self.closed = False
        self.cancel_observed = False
        self.refresh_calls = 0
        self.cache_report = _CacheReport()
        _FakeService.instances.append(self)

    @classmethod
    def open(cls, **_kwargs: Any) -> _FakeService:
        if cls.open_error:
            raise RuntimeError(cls.open_error)
        service = cls()
        service.read_only = _kwargs.get("read_only", False)
        service.threads["open"] = threading.get_ident()
        return service

    # -- queries -------------------------------------------------------

    def is_empty(self) -> bool:
        return not _FakeService.corpus

    def fetch_page(self, query=None, *, cursor=None, limit=500):
        from battle_engine.replay_history import HistoryPage

        self.threads["fetch_page"] = threading.get_ident()
        if _FakeService.query_error:
            raise RuntimeError(_FakeService.query_error)
        rows = _filtered(query)
        start = 0 if cursor is None else _index_of(rows, cursor.location_id) + 1
        window = rows[start : start + limit]
        has_more = start + limit < len(rows)
        return HistoryPage(
            rows=tuple(window),
            next_cursor=window[-1].cursor if (has_more and window) else None,
            has_more=has_more,
            page_size=limit,
        )

    def count(self, query=None) -> int:
        self.threads["count"] = threading.get_ident()
        return len(_filtered(query))

    def fetch_page_with_count(self, query=None, *, limit=500):
        return self.fetch_page(query, limit=limit), self.count(query)

    def fetch_detail(self, location_id: str):
        from battle_engine.replay_history import HistoryDetail

        self.threads["fetch_detail"] = threading.get_ident()
        for row in _FakeService.corpus:
            if row.location_id == location_id:
                return HistoryDetail(
                    occurrence=_occurrence_for(row),
                    duplicate_occurrence_location=False,
                    result_path="/runs/x/result.json",
                    replay_path=None,
                    first_seen_at="2026-09-11T00:00:00Z",
                )
        return None

    def ruleset_facets(self):
        from battle_engine.replay_history import RulesetFacet

        self.threads["ruleset_facets"] = threading.get_ident()
        return (RulesetFacet("bytefray-rules-2", "recorded", len(_FakeService.corpus)),)

    # -- refresh -------------------------------------------------------

    def refresh(self, *, force_rebuild=False, progress=None, cancel_check=None):
        self.threads["refresh"] = threading.get_ident()
        self.refresh_calls += 1
        if _FakeService.refresh_error:
            raise RuntimeError(_FakeService.refresh_error)
        gate = _FakeService.refresh_gate
        if gate is not None:
            deadline = time.monotonic() + 10.0
            while not gate.is_set() and time.monotonic() < deadline:
                if progress is not None:
                    progress("reconcile", 1000)
                if cancel_check is not None and cancel_check():
                    self.cancel_observed = True
                    return _Summary(committed=False)
                time.sleep(0.01)
        if progress is not None:
            progress("reconcile", 2000)
        return _Summary(committed=True, added=1)

    def close(self) -> None:
        self.threads["close"] = threading.get_ident()
        self.closed = True

    # -- Phase 7D: Open Replay preflight --------------------------------

    def resolve_replay(self, location_id: str):
        from battle_engine.replay_history import ReplayResolution, ReplayState

        self.threads["resolve_replay"] = threading.get_ident()
        _FakeService.resolve_calls.append(location_id)
        gate = _FakeService.resolve_gate
        if gate is not None:
            gate.wait(10.0)
        if _FakeService.resolve_error:
            raise RuntimeError(_FakeService.resolve_error)
        if location_id in _FakeService.resolve_overrides:
            return _FakeService.resolve_overrides[location_id]
        return ReplayResolution(
            location_id=location_id,
            state=ReplayState.AVAILABLE,
            path=f"/runs/{location_id}/replay.jsonl",
            expected_sha256="a" * 64,
            replay_id=location_id,
        )

    def verify_replay_integrity(self, resolution):
        from battle_engine.replay_history import ReplayIntegrityCheck, ReplayIntegrityStatus

        self.threads["verify_replay_integrity"] = threading.get_ident()
        override = _FakeService.integrity_overrides.get(resolution.location_id)
        if override is not None:
            return override
        return ReplayIntegrityCheck(
            status=ReplayIntegrityStatus.VERIFIED, digest=resolution.expected_sha256
        )


@dataclass
class _Summary:
    committed: bool = True
    added: int = 0
    updated: int = 0
    replaced: int = 0
    removed: int = 0
    scan_complete: bool = True


def _index_of(rows, location_id: str) -> int:
    for position, row in enumerate(rows):
        if row.location_id == location_id:
            return position
    return -1


def _filtered(query):
    """Only the dimensions these tests assert on; the real filtering is 7B's."""

    rows = list(_FakeService.corpus)
    if query is None:
        return rows
    if query.entrant_text:
        needle = query.entrant_text.lower()
        rows = [row for row in rows if needle in row.entrant_summary.lower()]
    if query.seed is not None:
        rows = [row for row in rows if row.seed == query.seed]
    if query.replay_states is not None:
        allowed = set(query.replay_states)
        rows = [row for row in rows if row.replay_state in allowed]
    return rows


def _occurrence_for(row):
    from battle_engine.replay_history import (
        ArtifactFingerprint,
        HistoryEntrant,
        HistoryOccurrence,
    )

    return HistoryOccurrence(
        location_id=row.location_id,
        occurrence_key=row.occurrence_key,
        occurrence_source=row.occurrence_source,
        occurrence_id=row.occurrence_id,
        effective_timestamp=row.effective_timestamp,
        effective_timestamp_ns=row.effective_timestamp_ns,
        timestamp_known=row.timestamp_known,
        timestamp_confidence=row.timestamp_confidence,
        entrants=(HistoryEntrant(ordinal=0, display_name="Alpha"),),
        ruleset_id=row.ruleset_id,
        ruleset_confidence=row.ruleset_confidence,
        seed=row.seed,
        workflow=row.workflow,
        durable_location=row.durable_location,
        winner=row.winner,
        outcome_state=row.outcome_state,
        replay_state=row.replay_state,
        result_health=row.result_health,
        entry_health=row.entry_health,
        result_fingerprint=ArtifactFingerprint(),
        replay_fingerprint=ArtifactFingerprint(),
    )


def _row(index: int, **overrides: Any):
    from battle_engine.replay_history import (
        EntryHealth,
        HistoryRow,
        OccurrenceIdentitySource,
        OutcomeState,
        ReplayState,
        ResultHealth,
        TimestampConfidence,
        WorkflowSource,
    )

    base: dict[str, Any] = {
        "location_id": f"loc_{index:04d}",
        "occurrence_key": f"legacy-location_{index:04d}",
        "occurrence_id": None,
        "occurrence_source": OccurrenceIdentitySource.SYNTHETIC_LOCATION,
        "match_id": None,
        "effective_timestamp": "2026-09-11T12:00:00Z",
        "effective_timestamp_ns": 1_789_000_000_000_000_000 - index * 1_000_000_000,
        "timestamp_known": True,
        "timestamp_confidence": TimestampConfidence.RECORDED,
        "entrant_summary": f"Alpha{index} vs Beta{index}",
        "entrant_count": 2,
        "winner": "Beta",
        "outcome_state": OutcomeState.WINNER,
        "ruleset_id": "bytefray-rules-2",
        "ruleset_confidence": "recorded",
        "seed": 1000 + index,
        "workflow": WorkflowSource.DESIGNER,
        "durable_location": True,
        "duplicate_occurrence_location": False,
        "replay_state": ReplayState.AVAILABLE,
        "result_health": ResultHealth.VALID,
        "entry_health": EntryHealth.HEALTHY,
        "diagnostic_category": None,
        "diagnostic_message": None,
    }
    base.update(overrides)
    return HistoryRow(**base)


# ----------------------------------------------------------------------
# Harness
# ----------------------------------------------------------------------


@pytest.fixture()
def history_env(monkeypatch):
    """A Replay History window backed by the fake service, plus a pump helper."""

    app = _make_app()
    from app.views import replay_history as module

    _FakeService.instances = []
    _FakeService.open_error = None
    _FakeService.refresh_gate = None
    _FakeService.refresh_error = None
    _FakeService.query_error = None
    _FakeService.resolve_gate = None
    _FakeService.resolve_error = None
    _FakeService.resolve_overrides = {}
    _FakeService.integrity_overrides = {}
    _FakeService.resolve_calls = []
    _FakeService.corpus = [_row(index) for index in range(1200)]
    monkeypatch.setattr(module, "ReplayHistoryService", _FakeService)

    windows: list[Any] = []

    def pump(seconds: float = 0.2) -> None:
        deadline = time.perf_counter() + seconds
        while time.perf_counter() < deadline:
            app.processEvents()
            time.sleep(0.002)

    def until(predicate, timeout: float = 10.0) -> bool:
        deadline = time.perf_counter() + timeout
        while time.perf_counter() < deadline:
            app.processEvents()
            if predicate():
                return True
            time.sleep(0.002)
        return False

    def make_window(**kwargs: Any):
        window = module.ReplayHistoryWindow(**kwargs)
        windows.append(window)
        window.show()
        return window

    class Env:
        pass

    env = Env()
    env.app = app
    env.module = module
    env.pump = pump
    env.until = until
    env.make_window = make_window
    env.gui_thread = threading.get_ident()
    yield env

    for window in windows:
        window.shutdownWorker()
        window.close()
    pump(0.05)


def _opened(env, **kwargs):
    """A window whose first page has arrived and whose refresh has settled."""

    window = env.make_window(**kwargs)
    assert env.until(lambda: window.model.loadedCount > 0), "first page never arrived"
    assert env.until(lambda: not window._refreshing), "refresh never settled"
    return window


# ----------------------------------------------------------------------
# Thread ownership
# ----------------------------------------------------------------------


@pytest.mark.gui
def test_service_is_constructed_on_the_worker_thread_not_the_gui_thread(history_env) -> None:
    window = _opened(history_env)
    service = _FakeService.instances[0]
    assert service.threads["open"] != history_env.gui_thread
    # The worker object's affinity is the dedicated history thread, and the
    # service was opened from inside it rather than handed in from outside.
    assert window._worker.thread() is window._thread
    assert window._thread is not window.thread()
    reader = _FakeService.instances[1]
    assert reader.read_only and not service.read_only
    assert reader.threads["open"] == reader.threads["fetch_page"]
    assert reader.threads["open"] != service.threads["open"]


@pytest.mark.gui
def test_every_service_call_happens_off_the_gui_thread(history_env) -> None:
    """Page, count, detail, facet and refresh calls all land on the worker."""

    window = _opened(history_env)
    window.table.selectRow(0)
    history_env.until(lambda: window.detailPane._sections != ())
    service = _FakeService.instances[1]
    for operation in ("open", "fetch_page", "count", "fetch_detail", "ruleset_facets"):
        assert operation in service.threads, f"{operation} was never called"
        assert service.threads[operation] != history_env.gui_thread, (
            f"{operation} ran on the GUI thread"
        )
    assert len({service.threads[key] for key in service.threads}) == 1
    writer = _FakeService.instances[0]
    assert writer.threads["refresh"] == writer.threads["open"]
    assert "refresh" not in service.threads
    assert "fetch_page" not in writer.threads


@pytest.mark.gui
def test_window_holds_no_service_reference(history_env) -> None:
    window = _opened(history_env)
    assert not hasattr(window, "_service")
    assert getattr(window, "service", None) is None


@pytest.mark.gui
def test_only_dtos_cross_back_to_the_gui_thread(history_env) -> None:
    from battle_engine.replay_history import HistoryRow

    window = _opened(history_env)
    row = window.model.rowAt(0)
    assert isinstance(row, HistoryRow)
    assert not hasattr(row, "execute") and not hasattr(row, "cursor_factory")


# ----------------------------------------------------------------------
# Lifecycle
# ----------------------------------------------------------------------


@pytest.mark.gui
def test_open_then_immediate_close_leaves_no_running_thread(history_env) -> None:
    window = history_env.make_window()
    window.close()
    assert not window._thread.isRunning()


@pytest.mark.gui
def test_close_during_refresh_cancels_and_joins_cleanly(history_env) -> None:
    gate = threading.Event()
    _FakeService.refresh_gate = gate
    window = history_env.make_window()
    assert history_env.until(lambda: window._refreshing)
    window.close()
    assert not window._thread.isRunning()
    service = _FakeService.instances[0]
    assert service.cancel_observed, "the refresh never saw the cancellation request"
    assert service.closed
    gate.set()


@pytest.mark.gui
def test_service_is_closed_on_the_worker_thread(history_env) -> None:
    window = _opened(history_env)
    window.close()
    service = _FakeService.instances[0]
    assert service.closed
    assert service.threads["close"] != history_env.gui_thread
    assert service.threads["close"] == service.threads["open"]


@pytest.mark.gui
def test_shutdown_is_idempotent(history_env) -> None:
    window = _opened(history_env)
    window.shutdownWorker()
    window.shutdownWorker()
    window.close()
    assert not window._thread.isRunning()


@pytest.mark.gui
def test_reopening_creates_a_fresh_worker_and_service(history_env) -> None:
    first = _opened(history_env)
    first.close()
    second = _opened(history_env)
    assert len(_FakeService.instances) == 4
    assert all(service.closed for service in _FakeService.instances[:2])
    assert all(not service.closed for service in _FakeService.instances[2:])
    second.close()


@pytest.mark.gui
def test_service_open_failure_becomes_a_visible_state_not_a_crash(history_env) -> None:
    _FakeService.open_error = "cache directory is not writable"
    window = history_env.make_window()
    assert history_env.until(lambda: window.stack.currentWidget() is window.messagePage)
    assert "unavailable" in window.messagePage.titleLabel.text().lower()
    assert "not writable" in window.messagePage.bodyLabel.text()
    assert not window.refreshButton.isEnabled()
    window.close()


@pytest.mark.gui
def test_refresh_failure_keeps_existing_rows_visible(history_env) -> None:
    window = _opened(history_env)
    loaded = window.model.loadedCount
    _FakeService.refresh_error = "the run folder vanished"
    window.refresh()
    assert history_env.until(lambda: not window._refreshing)
    assert window.model.loadedCount == loaded
    assert "could not be updated" in window.statusLabel.text()


@pytest.mark.gui
def test_query_failure_keeps_the_previous_rows(history_env) -> None:
    window = _opened(history_env)
    loaded = window.model.loadedCount
    _FakeService.query_error = "database is locked"
    window.searchEdit.setText("Alpha7")
    assert history_env.until(lambda: "could not be updated" in window.statusLabel.text())
    assert window.model.loadedCount == loaded


# ----------------------------------------------------------------------
# Cached-first startup and first-run
# ----------------------------------------------------------------------


@pytest.mark.gui
def test_cached_rows_appear_before_reconciliation_finishes(history_env) -> None:
    """The whole point of the cached-first flow: rows, then the scan."""

    gate = threading.Event()
    _FakeService.refresh_gate = gate
    window = history_env.make_window()
    assert history_env.until(lambda: window.model.loadedCount > 0)
    assert window._refreshing, "rows arrived only after the refresh completed"
    assert window.stack.currentWidget() is window.table
    gate.set()
    assert history_env.until(lambda: not window._refreshing)


@pytest.mark.gui
def test_first_run_with_no_cache_shows_a_preparing_state_not_an_empty_error(
    history_env,
) -> None:
    _FakeService.corpus = []
    gate = threading.Event()
    _FakeService.refresh_gate = gate
    window = history_env.make_window()
    assert history_env.until(lambda: window.stack.currentWidget() is window.messagePage)
    title = window.messagePage.titleLabel.text().lower()
    assert "preparing" in title or "no match history" in title
    gate.set()


@pytest.mark.gui
def test_construction_does_no_backend_work_on_the_gui_thread(history_env) -> None:
    """Showing the window must not wait on the index."""

    gate = threading.Event()
    _FakeService.refresh_gate = gate
    started = time.perf_counter()
    window = history_env.make_window()
    assert (time.perf_counter() - started) < 1.0
    gate.set()
    assert history_env.until(lambda: not window._refreshing)


# ----------------------------------------------------------------------
# Table model
# ----------------------------------------------------------------------


@pytest.mark.gui
def test_model_headers_are_the_mvp_columns(history_env) -> None:
    from PySide6.QtCore import Qt

    window = _opened(history_env)
    headers = [
        window.model.headerData(column, Qt.Horizontal, Qt.DisplayRole)
        for column in range(window.model.columnCount())
    ]
    assert headers == ["Date", "Entrants", "Result", "Ruleset", "Seed", "Source", "Replay"]


@pytest.mark.gui
def test_model_renders_row_cells_from_backend_values(history_env) -> None:
    from PySide6.QtCore import Qt

    window = _opened(history_env)
    cells = [
        window.model.data(window.model.index(0, column), Qt.DisplayRole)
        for column in range(7)
    ]
    assert cells[1] == "Alpha0 vs Beta0"
    assert cells[2] == "Beta"
    assert cells[3] == "Ruleset v2"
    assert cells[4] == "1000"
    assert cells[5] == "Designer"
    assert cells[6] == "Available"


@pytest.mark.gui
def test_authoritative_and_approximate_dates_are_visibly_distinct(history_env) -> None:
    from battle_engine.replay_history import TimestampConfidence
    from PySide6.QtCore import Qt

    _FakeService.corpus = [
        _row(0, timestamp_confidence=TimestampConfidence.RECORDED),
        _row(1, timestamp_confidence=TimestampConfidence.FILESYSTEM_FALLBACK),
        _row(2, timestamp_known=False, effective_timestamp_ns=0),
    ]
    window = _opened(history_env)
    dates = [
        window.model.data(window.model.index(index, 0), Qt.DisplayRole) for index in range(3)
    ]
    assert not dates[0].startswith("≈")
    assert dates[1].startswith("≈")
    assert dates[2] == "Unknown"


@pytest.mark.gui
def test_degraded_row_carries_a_text_marker_and_stays_browsable(history_env) -> None:
    from battle_engine.replay_history import EntryHealth, ReplayState
    from PySide6.QtCore import Qt

    _FakeService.corpus = [
        _row(0, entry_health=EntryHealth.DEGRADED, replay_state=ReplayState.MISSING),
        _row(1),
    ]
    window = _opened(history_env)
    first = window.model.data(window.model.index(0, 0), Qt.DisplayRole)
    assert first.startswith("!")
    assert window.model.data(window.model.index(0, 6), Qt.DisplayRole) == "Missing"
    # One degraded artifact must not turn the browser into an error state.
    assert window.stack.currentWidget() is window.table
    assert window.model.rowCount() == 2


@pytest.mark.gui
def test_loose_row_tooltip_marks_it_non_durable(history_env) -> None:
    from battle_engine.replay_history import WorkflowSource
    from PySide6.QtCore import Qt

    _FakeService.corpus = [
        _row(0, workflow=WorkflowSource.CLI_LATEST, durable_location=False)
    ]
    window = _opened(history_env)
    tooltip = window.model.data(window.model.index(0, 0), Qt.ToolTipRole)
    assert "overwritten" in tooltip.lower()
    assert window.model.data(window.model.index(0, 5), Qt.DisplayRole) == "CLI Latest"


@pytest.mark.gui
def test_model_exposes_accessible_text_for_screen_readers(history_env) -> None:
    from PySide6.QtCore import Qt

    window = _opened(history_env)
    spoken = window.model.data(window.model.index(0, 0), Qt.AccessibleTextRole)
    assert "Alpha0 vs Beta0" in spoken
    assert "Replay available" in spoken


@pytest.mark.gui
def test_lazy_paging_appends_a_page_rather_than_loading_everything(history_env) -> None:
    window = _opened(history_env)
    assert window.model.loadedCount == 500, "the first page must not load the whole corpus"
    assert window.model.hasMore
    window.model.fetchMore()
    assert history_env.until(lambda: window.model.loadedCount == 1000)
    window.model.fetchMore()
    assert history_env.until(lambda: window.model.loadedCount == 1200)
    assert not window.model.hasMore


@pytest.mark.gui
def test_paging_uses_the_backend_cursor_not_an_offset(history_env) -> None:
    window = _opened(history_env)
    first_page_last = window.model.rowAt(499)
    window.model.fetchMore()
    assert history_env.until(lambda: window.model.loadedCount > 500)
    # Continuation starts strictly after the previous page's cursor row.
    assert window.model.rowAt(500).location_id != first_page_last.location_id
    assert window._next_cursor is not None


@pytest.mark.gui
def test_changing_a_query_resets_rather_than_appends(history_env) -> None:
    window = _opened(history_env)
    window.model.fetchMore()
    assert history_env.until(lambda: window.model.loadedCount == 1000)
    window.searchEdit.setText("Alpha7 ")
    assert history_env.until(lambda: window.model.loadedCount < 1000)
    assert window.model.loadedCount >= 1


@pytest.mark.gui
def test_fetch_more_is_suspended_while_a_new_first_page_is_in_flight(history_env) -> None:
    """A continuation with no valid cursor must not be silently dropped."""

    window = _opened(history_env)
    window._requestFirstPage()
    assert not window.model.canFetchMore()
    assert history_env.until(lambda: window.model.hasMore)


# ----------------------------------------------------------------------
# Filters
# ----------------------------------------------------------------------


@pytest.mark.gui
def test_entrant_search_is_debounced_into_one_query(history_env) -> None:
    window = _opened(history_env)
    before = window._generation
    for text in ("A", "Al", "Alp", "Alph", "Alpha", "Alpha7"):
        window.searchEdit.setText(text)
        history_env.pump(0.02)
    assert history_env.until(lambda: not window._debounce.isActive() and window._total < 1200)
    assert window._generation - before == 1, "each keystroke issued its own query"


@pytest.mark.gui
def test_empty_search_clears_the_filter(history_env) -> None:
    window = _opened(history_env)
    window.searchEdit.setText("Alpha7")
    assert history_env.until(lambda: window._total < 1200)
    window.searchEdit.setText("")
    assert history_env.until(lambda: window._total == 1200)


@pytest.mark.gui
def test_each_filter_control_reaches_the_backend_query(history_env) -> None:
    from battle_engine.replay_history import ReplayState, WorkflowSource

    window = _opened(history_env)
    window.searchEdit.setText("Alpha1")
    window.seedEdit.setText("1001")
    window.sourceCombo.setCurrentIndex(window.sourceCombo.findData(WorkflowSource.DESIGNER.value))
    window.replayCombo.setCurrentIndex(window.replayCombo.findData(ReplayState.AVAILABLE.value))
    window.resultCombo.setCurrentIndex(window.resultCombo.findData("tie"))
    window.fromCheck.setChecked(True)
    window.toCheck.setChecked(True)
    assert history_env.until(lambda: not window._debounce.isActive())
    history_env.pump(0.2)
    query = window._query
    assert query.entrant_text == "Alpha1"
    assert query.seed == 1001
    assert query.workflows == (WorkflowSource.DESIGNER,)
    assert query.replay_states == (ReplayState.AVAILABLE,)
    assert query.outcome_states is not None
    assert query.start is not None and query.end is not None


@pytest.mark.gui
def test_partial_seed_input_marks_the_field_without_a_dialog(history_env) -> None:
    window = _opened(history_env)
    window.seedEdit.setText("12x")
    history_env.pump(0.4)
    assert window.seedEdit.toolTip()
    assert window._query.seed is None
    window.seedEdit.setText("1001")
    assert history_env.until(lambda: window._query.seed == 1001)
    assert window.seedEdit.toolTip() == ""


@pytest.mark.gui
def test_clear_filters_resets_every_control_and_reloads(history_env) -> None:
    window = _opened(history_env)
    window.searchEdit.setText("Alpha7")
    window.seedEdit.setText("1007")
    window.fromCheck.setChecked(True)
    assert history_env.until(lambda: window._total < 1200)

    window.clearFilters()
    assert history_env.until(lambda: window._total == 1200)
    assert window.searchEdit.text() == ""
    assert window.seedEdit.text() == ""
    assert not window.fromCheck.isChecked()
    assert not window.fromDate.isEnabled()
    assert window._filters.is_unfiltered


@pytest.mark.gui
def test_clear_filters_does_not_disturb_unrelated_ui_state(history_env) -> None:
    window = _opened(history_env)
    window.advancedCheck.setChecked(True)
    sizes = window._splitter.sizes()
    window.searchEdit.setText("Alpha7")
    assert history_env.until(lambda: window._total < 1200)
    window.clearFilters()
    history_env.pump(0.3)
    assert window.advancedCheck.isChecked()
    assert window._splitter.sizes() == sizes


@pytest.mark.gui
def test_filtered_empty_result_offers_clear_filters(history_env) -> None:
    window = _opened(history_env)
    window.searchEdit.setText("no-such-agent-anywhere")
    assert history_env.until(lambda: window.stack.currentWidget() is window.messagePage)
    assert "filters" in window.messagePage.titleLabel.text().lower()
    assert window.messagePage.clearButton.isVisible()


@pytest.mark.gui
def test_a_stale_page_response_cannot_overwrite_newer_rows(history_env) -> None:
    """The generation guard, exercised directly."""

    from app.views.replay_history import PageResult

    window = _opened(history_env)
    stale = PageResult(
        generation=window._generation - 1,
        rows=(_row(9999),),
        next_cursor=None,
        has_more=False,
        total=1,
        reset=True,
    )
    before = window.model.loadedCount
    window._onPageReady(stale)
    assert window.model.loadedCount == before
    assert window._total != 1


# ----------------------------------------------------------------------
# Details
# ----------------------------------------------------------------------


@pytest.mark.gui
def test_selecting_a_row_populates_the_detail_pane_asynchronously(history_env) -> None:
    window = _opened(history_env)
    window.table.selectRow(2)
    assert history_env.until(lambda: window.detailPane._sections != ())
    titles = [section.title for section in window.detailPane._sections]
    assert "Match" in titles and "Entrants" in titles


@pytest.mark.gui
def test_advanced_sections_are_hidden_until_requested(history_env) -> None:
    window = _opened(history_env)
    window.table.selectRow(0)
    assert history_env.until(lambda: window.detailPane._sections != ())
    rendered = _group_titles(window.detailPane)
    assert "Identity details" not in rendered
    window.advancedCheck.setChecked(True)
    history_env.pump(0.1)
    assert "Identity details" in _group_titles(window.detailPane)


def _group_titles(pane) -> set[str]:
    from PySide6.QtWidgets import QGroupBox

    return {
        child.accessibleName()
        for child in pane.findChildren(QGroupBox)
        if child.isVisibleTo(pane)
    }


@pytest.mark.gui
def test_reselecting_rows_does_not_accumulate_stale_detail_widgets(history_env) -> None:
    """Regression: the detail pane painted every previous selection underneath.

    Taking a widget out of a layout does not unparent it, and ``deleteLater``
    only runs on the next event-loop pass, so each new selection stacked its
    groups on top of the last one -- overlapping, unreadable text. Only a look
    at the rendered window showed it; the section list was always correct.
    """

    from PySide6.QtWidgets import QGroupBox

    window = _opened(history_env)
    for row in range(4):
        window.table.selectRow(row)
        assert history_env.until(lambda: window.detailPane._sections != ())
        history_env.pump(0.05)

    groups = [
        child
        for child in window.detailPane.findChildren(QGroupBox)
        if child.parent() is not None and child.isVisibleTo(window.detailPane)
    ]
    titles = [group.title() for group in groups]
    assert len(titles) == len(set(titles)), f"duplicate detail groups rendered: {titles}"
    assert len(titles) == 4, titles  # Match, Entrants, Result, Replay


@pytest.mark.gui
def test_clearing_the_selection_empties_the_detail_pane(history_env) -> None:
    from PySide6.QtWidgets import QGroupBox

    window = _opened(history_env)
    window.table.selectRow(0)
    assert history_env.until(lambda: window.detailPane._sections != ())
    window.searchEdit.setText("no-such-agent-anywhere")
    assert history_env.until(lambda: window.stack.currentWidget() is window.messagePage)
    history_env.pump(0.1)
    visible = [
        child
        for child in window.detailPane.findChildren(QGroupBox)
        if child.parent() is not None and child.isVisibleTo(window.detailPane)
    ]
    assert visible == [], "the previous match's details survived the filter change"


@pytest.mark.gui
def test_a_late_detail_response_for_another_row_is_ignored(history_env) -> None:
    from app.views.replay_history import DetailResult

    window = _opened(history_env)
    window.table.selectRow(0)
    assert history_env.until(lambda: window.detailPane._sections != ())
    current = window.detailPane._sections

    other = _FakeService.instances[0].fetch_detail("loc_0005")
    window._onDetailReady(
        DetailResult(generation=window._detail_generation, location_id="loc_0005", detail=other)
    )
    assert window.detailPane._sections is current


@pytest.mark.gui
def test_detail_for_a_vanished_row_explains_itself(history_env) -> None:
    from app.views.replay_history import DetailResult

    window = _opened(history_env)
    window.table.selectRow(0)
    assert history_env.until(lambda: window.detailPane._sections != ())
    window._onDetailReady(
        DetailResult(
            generation=window._detail_generation,
            location_id=window._selected_location,
            detail=None,
        )
    )
    assert "no longer" in window.detailPane._placeholder.text().lower()


@pytest.mark.gui
def test_loose_selection_shows_the_non_durable_notice(history_env) -> None:
    from battle_engine.replay_history import WorkflowSource

    _FakeService.corpus = [_row(0, workflow=WorkflowSource.CLI_LATEST, durable_location=False)]
    window = _opened(history_env)
    window.table.selectRow(0)
    assert history_env.until(lambda: window.looseLabel.isVisible())
    assert "overwritten" in window.looseLabel.text().lower()


# ----------------------------------------------------------------------
# Refresh, progress, cancellation
# ----------------------------------------------------------------------


@pytest.mark.gui
def test_refresh_reports_progress_and_offers_cancel(history_env) -> None:
    gate = threading.Event()
    _FakeService.refresh_gate = gate
    window = history_env.make_window()
    assert history_env.until(lambda: window._refreshing)
    assert window.cancelButton.isVisible()
    assert window.progressBar.isVisible()
    assert not window.refreshButton.isEnabled()
    assert history_env.until(lambda: "scanned" in window.statusLabel.text())
    gate.set()
    assert history_env.until(lambda: not window._refreshing)
    assert not window.cancelButton.isVisible()
    assert window.refreshButton.isEnabled()


@pytest.mark.gui
def test_cancel_reaches_the_service_and_preserves_rows(history_env) -> None:
    window = _opened(history_env)
    loaded = window.model.loadedCount
    gate = threading.Event()
    _FakeService.refresh_gate = gate
    window.refresh()
    assert history_env.until(lambda: window._refreshing)
    window.cancelRefresh()
    assert history_env.until(lambda: not window._refreshing)
    service = _FakeService.instances[0]
    assert service.cancel_observed
    assert not service.closed, "cancellation must not tear the service down"
    assert window.model.loadedCount == loaded
    assert "cancelled" in window.statusLabel.text().lower()
    gate.set()


@pytest.mark.gui
def test_cancelled_refresh_is_not_presented_as_an_error(history_env) -> None:
    window = _opened(history_env)
    gate = threading.Event()
    _FakeService.refresh_gate = gate
    window.refresh()
    assert history_env.until(lambda: window._refreshing)
    window.cancelRefresh()
    assert history_env.until(lambda: not window._refreshing)
    status = window.statusLabel.text().lower()
    assert "error" not in status and "failed" not in status
    assert window.stack.currentWidget() is window.table
    gate.set()


@pytest.mark.gui
def test_refresh_preserves_filters_and_selection(history_env) -> None:
    window = _opened(history_env)
    window.searchEdit.setText("Alpha7")
    assert history_env.until(lambda: window._total < 1200 and not window._debounce.isActive())
    filtered_total = window._total
    window.table.selectRow(0)
    assert history_env.until(lambda: window._selected_location is not None)
    selected = window._selected_location

    window.refresh()
    assert history_env.until(lambda: not window._refreshing)
    assert history_env.until(lambda: window._total == filtered_total)
    assert window.searchEdit.text() == "Alpha7"
    assert window._selected_location == selected


@pytest.mark.gui
def test_refresh_summary_is_reported(history_env) -> None:
    window = _opened(history_env)
    window.refresh()
    assert history_env.until(lambda: not window._refreshing)
    assert history_env.until(lambda: "added" in window.statusLabel.text().lower())


@pytest.mark.gui
def test_refresh_summary_survives_the_requery_that_follows_it(history_env) -> None:
    """Regression: the summary used to be overwritten by the new row count.

    A refresh completes, then re-queries; when that page landed it rewrote the
    status line, so "History refreshed -- 1 added" was visible for a few
    milliseconds and then gone.
    """

    window = _opened(history_env)
    window.refresh()
    assert history_env.until(lambda: not window._refreshing)
    assert history_env.until(lambda: "matches" in window.statusLabel.text().lower())
    history_env.pump(0.3)
    status = window.statusLabel.text().lower()
    assert "added" in status, "the refresh summary was overwritten by the row count"
    assert "matches" in status, "the row count was lost"


@pytest.mark.gui
def test_a_new_filter_retires_the_previous_refresh_summary(history_env) -> None:
    window = _opened(history_env)
    window.refresh()
    assert history_env.until(lambda: "added" in window.statusLabel.text().lower())
    window.searchEdit.setText("Alpha7")
    assert history_env.until(lambda: window._total < 1200)
    history_env.pump(0.2)
    assert "added" not in window.statusLabel.text().lower()


@pytest.mark.gui
def test_a_cancel_raised_while_refresh_is_still_queued_is_not_lost(history_env) -> None:
    """Regression: ``refresh`` used to clear the cancel flag on entry.

    Cancellation and shutdown both set the flag from the GUI thread while the
    refresh slot may still be sitting in the worker's queue behind an earlier
    request. Clearing it on entry discarded exactly that case, so closing the
    window during startup ran a whole corpus scan before the close completed.
    The requester owns the flag; the operation must only read it.
    """

    _FakeService.refresh_gate = threading.Event()  # never set: refresh must be cancelled out
    worker = history_env.module.ReplayHistoryMaintenanceWorker()
    worker.start()
    worker.requestCancel()
    worker.refresh()
    service = _FakeService.instances[0]
    assert service.cancel_observed, "the refresh cleared the pending cancellation"
    assert not service.closed
    worker.shutdown()
    assert service.closed


@pytest.mark.gui
def test_refresh_does_not_blank_the_table(history_env) -> None:
    window = _opened(history_env)
    gate = threading.Event()
    _FakeService.refresh_gate = gate
    window.refresh()
    assert history_env.until(lambda: window._refreshing)
    history_env.pump(0.2)
    assert window.model.loadedCount > 0
    assert window.stack.currentWidget() is window.table
    gate.set()


# ----------------------------------------------------------------------
# Keyboard / accessibility
# ----------------------------------------------------------------------


@pytest.mark.gui
def test_filter_controls_have_accessible_names_and_buddies(history_env) -> None:
    window = _opened(history_env)
    for widget in (
        window.searchEdit,
        window.seedEdit,
        window.rulesetCombo,
        window.resultCombo,
        window.sourceCombo,
        window.replayCombo,
        window.fromDate,
        window.toDate,
        window.refreshButton,
        window.cancelButton,
        window.table,
        window.statusLabel,
        window.progressBar,
    ):
        assert widget.accessibleName(), f"{widget} has no accessible name"


@pytest.mark.gui
def test_table_supports_keyboard_row_navigation(history_env) -> None:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QAbstractItemView

    window = _opened(history_env)
    assert window.table.selectionBehavior() == QAbstractItemView.SelectRows
    assert window.table.focusPolicy() != Qt.NoFocus
    window.table.selectRow(0)
    window.table.selectRow(1)
    assert window.table.currentIndex().row() == 1


@pytest.mark.gui
def test_open_replay_and_copy_seed_exist_but_rerun_never_does(history_env) -> None:
    """Phase 7D adds Open Replay / Copy Seed; Re-run Match stays explicitly out of scope.

    Supersedes 7C's ``test_no_playback_action_is_offered_in_this_phase``, which
    pinned the opposite fact for the phase that had not implemented them yet.
    """

    from PySide6.QtWidgets import QPushButton

    window = _opened(history_env)
    labels = {button.text().lower().replace("&", "") for button in window.findChildren(QPushButton)}
    assert any("open replay" in label for label in labels)
    assert any("copy seed" in label for label in labels)
    assert not any("re-run" in label or "rerun" in label for label in labels)


# ----------------------------------------------------------------------
# Phase 7D: Open Replay / Copy Seed
# ----------------------------------------------------------------------


def _select(window, location_id: str) -> None:
    position = window.model.positionOf(location_id)
    assert position >= 0, f"{location_id} is not loaded"
    window.table.selectRow(position)


@pytest.mark.gui
def test_open_replay_disabled_with_no_selection(history_env) -> None:
    window = _opened(history_env)
    assert not window.openReplayButton.isEnabled()
    assert not window.copySeedButton.isEnabled()


@pytest.mark.gui
@pytest.mark.parametrize(
    "state_name,expected_enabled",
    [
        ("AVAILABLE", True),
        ("MISSING", False),
        ("NOT_PRODUCED", False),
        ("INVALID", False),
        ("INACCESSIBLE", False),
        ("UNCHECKED", False),
    ],
)
def test_open_replay_button_reflects_the_selected_rows_cached_replay_state(
    history_env, state_name, expected_enabled
) -> None:
    from battle_engine.replay_history import ReplayState

    _FakeService.corpus[0] = _row(0, replay_state=getattr(ReplayState, state_name))
    window = _opened(history_env)
    _select(window, "loc_0000")
    assert window.openReplayButton.isEnabled() is expected_enabled


@pytest.mark.gui
def test_copy_seed_disabled_when_the_row_has_no_seed(history_env) -> None:
    _FakeService.corpus[0] = _row(0, seed=None)
    window = _opened(history_env)
    _select(window, "loc_0000")
    assert not window.copySeedButton.isEnabled()
    assert window.openReplayButton.isEnabled()  # independent of Copy Seed


@pytest.mark.gui
def test_copy_seed_enabled_for_a_concrete_seed_including_zero(history_env) -> None:
    _FakeService.corpus[0] = _row(0, seed=0)
    window = _opened(history_env)
    _select(window, "loc_0000")
    assert window.copySeedButton.isEnabled()


@pytest.mark.gui
def test_copy_seed_copies_the_exact_integer_and_gives_feedback(history_env) -> None:
    from PySide6.QtGui import QGuiApplication

    _FakeService.corpus[0] = _row(0, seed=184293)
    window = _opened(history_env)
    _select(window, "loc_0000")
    window.copySeedButton.click()
    assert QGuiApplication.clipboard().text() == "184293"
    assert "184293" in window.clipboardStatusLabel.text()


@pytest.mark.gui
def test_open_replay_launches_through_the_canonical_viewer_helper(history_env, monkeypatch) -> None:
    """Pins Phase 7D Sec 17/41: History must hand off through the existing
    launcher and never build or spawn a command of its own."""

    from pathlib import Path

    calls = []
    monkeypatch.setattr(
        history_env.module,
        "open_pygame_client_direct",
        lambda data_root, replay_path: calls.append((data_root, replay_path)),
    )
    window = _opened(history_env)
    _select(window, "loc_0000")
    window.openReplayButton.click()
    assert history_env.until(lambda: len(calls) == 1)
    data_root, replay_path = calls[0]
    assert data_root == window._data_root
    assert Path(replay_path) == Path("/runs/loc_0000/replay.jsonl")
    assert "Opened" in window.actionStatusLabel.text()


@pytest.mark.gui
def test_open_replay_shows_checking_status_while_the_preflight_is_pending(history_env) -> None:
    gate = threading.Event()
    _FakeService.resolve_gate = gate
    window = _opened(history_env)
    _select(window, "loc_0000")
    window.openReplayButton.click()
    assert history_env.until(lambda: "checking" in window.actionStatusLabel.text().lower())
    assert not window.openReplayButton.isEnabled()
    gate.set()
    history_env.until(lambda: window.openReplayButton.isEnabled())


@pytest.mark.gui
def test_duplicate_open_replay_clicks_trigger_only_one_preflight(history_env) -> None:
    gate = threading.Event()
    _FakeService.resolve_gate = gate
    window = _opened(history_env)
    _select(window, "loc_0000")
    window.openReplayButton.click()
    history_env.until(lambda: len(_FakeService.resolve_calls) >= 1)
    # The button disables itself synchronously on the first click; further
    # activation attempts (button, Enter, double-click) share one guard.
    window.openReplayButton.click()
    window._activateOpenReplay()
    history_env.pump(0.05)
    gate.set()
    history_env.until(lambda: not window._open_pending)
    assert _FakeService.resolve_calls == ["loc_0000"]


@pytest.mark.gui
def test_open_replay_reports_a_replay_that_went_missing_after_indexing(history_env) -> None:
    from battle_engine.replay_history import ReplayResolution, ReplayState

    _FakeService.resolve_overrides["loc_0000"] = ReplayResolution(
        location_id="loc_0000",
        state=ReplayState.MISSING,
        path=None,
        expected_sha256=None,
        replay_id=None,
        diagnostic="gone",
    )
    window = _opened(history_env)
    _select(window, "loc_0000")
    window.openReplayButton.click()
    assert history_env.until(
        lambda: window.actionStatusLabel.text() == "Replay file is no longer available."
    )


@pytest.mark.gui
def test_open_replay_blocks_launch_on_digest_mismatch_and_explains_why(
    history_env, monkeypatch
) -> None:
    from battle_engine.replay_history import ReplayIntegrityCheck, ReplayIntegrityStatus

    _FakeService.integrity_overrides["loc_0000"] = ReplayIntegrityCheck(
        status=ReplayIntegrityStatus.MISMATCH, diagnostic="digest mismatch"
    )
    launched = []
    monkeypatch.setattr(
        history_env.module,
        "open_pygame_client_direct",
        lambda *a, **k: launched.append(a),
    )
    warned = []
    monkeypatch.setattr(
        history_env.module.QMessageBox,
        "warning",
        staticmethod(lambda *a, **k: warned.append(a) or None),
    )
    window = _opened(history_env)
    _select(window, "loc_0000")
    window.openReplayButton.click()
    assert history_env.until(lambda: len(warned) == 1)
    assert not launched
    # No silent "open anyway" bypass exists in this phase.
    assert not hasattr(window, "openAnywayButton")


@pytest.mark.gui
def test_open_replay_allows_a_legacy_replay_with_no_recorded_digest(history_env, monkeypatch) -> None:
    from battle_engine.replay_history import ReplayIntegrityCheck, ReplayIntegrityStatus

    _FakeService.integrity_overrides["loc_0000"] = ReplayIntegrityCheck(
        status=ReplayIntegrityStatus.UNVERIFIED_LEGACY
    )
    calls = []
    monkeypatch.setattr(
        history_env.module, "open_pygame_client_direct", lambda *a: calls.append(a)
    )
    window = _opened(history_env)
    _select(window, "loc_0000")
    window.openReplayButton.click()
    assert history_env.until(lambda: len(calls) == 1)


@pytest.mark.gui
def test_open_replay_handles_the_file_vanishing_during_verification(history_env, monkeypatch) -> None:
    from battle_engine.replay_history import ReplayIntegrityCheck, ReplayIntegrityStatus

    _FakeService.integrity_overrides["loc_0000"] = ReplayIntegrityCheck(
        status=ReplayIntegrityStatus.UNREADABLE, diagnostic="vanished"
    )
    calls = []
    monkeypatch.setattr(
        history_env.module, "open_pygame_client_direct", lambda *a: calls.append(a)
    )
    window = _opened(history_env)
    _select(window, "loc_0000")
    window.openReplayButton.click()
    assert history_env.until(
        lambda: window.actionStatusLabel.text() == "Replay file is no longer available."
    )
    assert not calls


@pytest.mark.gui
def test_open_replay_reports_launcher_failure_without_crashing(history_env, monkeypatch) -> None:
    def _raise(*_a, **_k):
        raise OSError("no such executable")

    monkeypatch.setattr(history_env.module, "open_pygame_client_direct", _raise)
    critical = []
    monkeypatch.setattr(
        history_env.module.QMessageBox,
        "critical",
        staticmethod(lambda *a, **k: critical.append(a) or None),
    )
    window = _opened(history_env)
    _select(window, "loc_0000")
    window.openReplayButton.click()
    assert history_env.until(lambda: len(critical) == 1)
    assert "Replay Launch Failed" in critical[0]


@pytest.mark.gui
def test_resolve_and_verify_calls_happen_off_the_gui_thread(history_env) -> None:
    window = _opened(history_env)
    _select(window, "loc_0000")
    window.openReplayButton.click()
    history_env.until(lambda: "Opened" in window.actionStatusLabel.text())
    service = _FakeService.instances[1]
    for operation in ("resolve_replay", "verify_replay_integrity"):
        assert operation in service.threads
        assert service.threads[operation] != history_env.gui_thread


@pytest.mark.gui
def test_a_stale_open_replay_response_is_dropped_not_launched(history_env, monkeypatch) -> None:
    """A response whose request id no longer matches must never launch a Viewer.

    The real in-flight worker call is held on a gate for the whole test so it
    cannot race the manually-injected stale answer: without that, the fake's
    genuine (fast, ungated) reply could resolve and launch before this test
    ever gets to simulate staleness, which would not be testing this guard at
    all.
    """

    from battle_engine.replay_history import ReplayState

    from app.views.replay_history import (
        ReplayIntegrityCheck,
        ReplayIntegrityStatus,
        ReplayOpenResult,
        ReplayResolution,
    )

    calls = []
    monkeypatch.setattr(
        history_env.module, "open_pygame_client_direct", lambda *a: calls.append(a)
    )
    gate = threading.Event()
    _FakeService.resolve_gate = gate
    window = _opened(history_env)
    _select(window, "loc_0000")
    window.openReplayButton.click()
    assert history_env.until(lambda: len(_FakeService.resolve_calls) == 1)

    # Simulate a newer request having superseded this one (e.g. the window's
    # own counter having moved on) before the worker's real answer arrives.
    window._open_request_id += 1
    window._open_pending = False
    stale = ReplayOpenResult(
        request_id=window._open_request_id - 1,
        location_id="loc_0000",
        resolution=ReplayResolution(
            location_id="loc_0000",
            state=ReplayState.AVAILABLE,
            path="/runs/loc_0000/replay.jsonl",
            expected_sha256="a" * 64,
            replay_id="loc_0000",
        ),
        integrity=ReplayIntegrityCheck(status=ReplayIntegrityStatus.VERIFIED, digest="a" * 64),
    )
    window._onReplayResolved(stale)
    history_env.pump(0.05)
    assert not calls

    # The real worker answer, once released, is now equally stale and must
    # not launch either.
    gate.set()
    history_env.pump(0.2)
    assert not calls


@pytest.mark.gui
def test_closing_the_window_during_a_pending_preflight_never_launches_afterward(
    history_env, monkeypatch
) -> None:
    """``close()`` blocks (``shutdownWorker`` joins the thread), so the gate
    is released from a background timer rather than after ``close()``
    returns -- otherwise the worker's queued shutdown could never be
    processed and the join would hang for the fake's full gate timeout."""

    calls = []
    monkeypatch.setattr(
        history_env.module, "open_pygame_client_direct", lambda *a: calls.append(a)
    )
    gate = threading.Event()
    _FakeService.resolve_gate = gate
    window = _opened(history_env)
    _select(window, "loc_0000")
    window.openReplayButton.click()
    assert history_env.until(lambda: len(_FakeService.resolve_calls) == 1)

    threading.Timer(0.05, gate.set).start()
    window.close()
    assert not window.isVisible()
    history_env.pump(0.2)
    assert not calls, "a Viewer launched after the owning window had already shut down"
    assert not window._thread.isRunning()


@pytest.mark.gui
def test_double_click_activates_open_replay_for_a_playable_row(history_env, monkeypatch) -> None:
    calls = []
    monkeypatch.setattr(
        history_env.module, "open_pygame_client_direct", lambda *a: calls.append(a)
    )
    window = _opened(history_env)
    position = window.model.positionOf("loc_0000")
    window.table.selectRow(position)
    window._onTableDoubleClicked(window.model.index(position, 0))
    assert history_env.until(lambda: len(calls) == 1)


@pytest.mark.gui
def test_double_click_on_an_unplayable_row_does_not_launch_or_raise_a_dialog(
    history_env, monkeypatch
) -> None:
    from battle_engine.replay_history import ReplayState

    calls = []
    monkeypatch.setattr(
        history_env.module, "open_pygame_client_direct", lambda *a: calls.append(a)
    )
    critical = []
    monkeypatch.setattr(
        history_env.module.QMessageBox,
        "critical",
        staticmethod(lambda *a, **k: critical.append(a) or None),
    )
    _FakeService.corpus[0] = _row(0, replay_state=ReplayState.MISSING)
    window = _opened(history_env)
    position = window.model.positionOf("loc_0000")
    window.table.selectRow(position)
    window._onTableDoubleClicked(window.model.index(position, 0))
    history_env.pump(0.05)
    assert not calls
    assert not critical


@pytest.mark.gui
def test_enter_activates_open_replay_only_while_the_table_has_focus(history_env, monkeypatch) -> None:
    from PySide6.QtCore import QEvent, Qt
    from PySide6.QtGui import QKeyEvent
    from PySide6.QtWidgets import QApplication

    calls = []
    monkeypatch.setattr(
        history_env.module, "open_pygame_client_direct", lambda *a: calls.append(a)
    )
    window = _opened(history_env)
    _select(window, "loc_0000")
    event = QKeyEvent(QEvent.KeyPress, Qt.Key_Return, Qt.NoModifier)
    QApplication.sendEvent(window.table, event)
    assert history_env.until(lambda: len(calls) == 1)

    # The same key on the entrant search field must never be intercepted.
    calls.clear()
    other = QKeyEvent(QEvent.KeyPress, Qt.Key_Return, Qt.NoModifier)
    QApplication.sendEvent(window.searchEdit, other)
    history_env.pump(0.05)
    assert not calls


@pytest.mark.gui
def test_button_enter_and_double_click_share_one_activation_path(history_env, monkeypatch) -> None:
    """Pins Phase 7D Sec 8/43: every entry point must call the same handler."""

    from PySide6.QtCore import QEvent, Qt
    from PySide6.QtGui import QKeyEvent
    from PySide6.QtWidgets import QApplication

    activations = []
    monkeypatch.setattr(
        history_env.module.ReplayHistoryWindow,
        "_activateOpenReplay",
        lambda self: activations.append(True),
    )
    window = _opened(history_env)
    _select(window, "loc_0000")

    window.openReplayButton.click()
    position = window.model.positionOf("loc_0000")
    window._onTableDoubleClicked(window.model.index(position, 0))
    event = QKeyEvent(QEvent.KeyPress, Qt.Key_Return, Qt.NoModifier)
    QApplication.sendEvent(window.table, event)

    assert len(activations) == 3


# ----------------------------------------------------------------------
# Designer integration
# ----------------------------------------------------------------------


def _designer(monkeypatch, tmp_path):
    _make_app()
    monkeypatch.setenv("BYTEFRAY_ROOT", str(tmp_path))
    from app.agent_designer import AgentDesigner

    return AgentDesigner()


@pytest.mark.gui
def test_tools_menu_contains_replay_history(monkeypatch, tmp_path) -> None:
    designer = _designer(monkeypatch, tmp_path)
    try:
        tools = next(
            menu
            for menu in designer.menuBar().findChildren(type(designer.menuBar().addMenu("x")))
            if menu.title() == "Tools"
        )
        labels = [action.text() for action in tools.actions()]
        assert "Replay History…" in labels
        assert "Evaluation History…" in labels, "the existing Tools entries must not move"
    finally:
        designer.close()


@pytest.mark.gui
def test_designer_action_opens_a_modeless_browser(monkeypatch, tmp_path) -> None:
    designer = _designer(monkeypatch, tmp_path)
    try:
        designer._on_replay_history()
        window = designer._replay_history
        assert window is not None
        assert window.isVisible()
        assert not window.isModal(), "History must not block the Designer"
        window.shutdownWorker()
    finally:
        designer.close()


@pytest.mark.gui
def test_reactivating_the_action_reuses_the_existing_browser(monkeypatch, tmp_path) -> None:
    designer = _designer(monkeypatch, tmp_path)
    try:
        designer._on_replay_history()
        first = designer._replay_history
        designer._on_replay_history()
        assert designer._replay_history is first, "a second History window was opened"
        first.shutdownWorker()
    finally:
        designer.close()


@pytest.mark.gui
def test_closing_the_browser_leaves_the_designer_usable(monkeypatch, tmp_path) -> None:
    _make_app()
    designer = _designer(monkeypatch, tmp_path)
    try:
        designer._on_replay_history()
        window = designer._replay_history
        window.close()
        assert not window._thread.isRunning()
        assert designer.isEnabled()
        # A new one can still be opened afterwards.
        designer._on_replay_history()
        assert designer._replay_history is not None
        designer._replay_history.shutdownWorker()
    finally:
        designer.close()


@pytest.mark.gui
def test_closing_the_browser_immediately_frees_the_designer_slot(monkeypatch, tmp_path) -> None:
    """The reference must drop on close, not on Qt's deferred deletion.

    Otherwise a reopen in the same event-loop turn would raise a window whose
    worker is already joined -- visible as an empty browser with a permanently
    disabled Refresh.
    """

    designer = _designer(monkeypatch, tmp_path)
    try:
        designer._on_replay_history()
        window = designer._replay_history
        window.close()
        assert designer._replay_history is None
        designer._on_replay_history()
        assert designer._replay_history is not None
        assert designer._replay_history is not window
        designer._replay_history.shutdownWorker()
    finally:
        designer.close()


@pytest.mark.gui
def test_designer_shutdown_joins_the_history_worker(monkeypatch, tmp_path) -> None:
    designer = _designer(monkeypatch, tmp_path)
    designer._on_replay_history()
    window = designer._replay_history
    assert window is not None
    designer.close()
    assert not window._thread.isRunning()
    assert not window._reader_thread.isRunning()


@pytest.mark.gui
def test_queries_and_preflight_complete_while_maintenance_is_blocked(history_env, monkeypatch):
    window = _opened(history_env)
    window.table.selectRow(0)
    assert history_env.until(lambda: bool(window.detailPane._sections))
    gate = threading.Event()
    _FakeService.refresh_gate = gate
    writer = _FakeService.instances[0]
    previous = writer.refresh_calls
    window.refresh()
    assert history_env.until(lambda: writer.refresh_calls > previous)
    launched = []
    monkeypatch.setattr(history_env.module, "open_pygame_client_direct", lambda *args: launched.append(args))
    window._activateOpenReplay()
    window.searchEdit.setText("Alpha5")
    window._applyFilters()
    assert history_env.until(lambda: window.model.loadedCount == 111)
    window.table.selectRow(0)
    assert history_env.until(lambda: bool(window.detailPane._sections) and bool(launched))
    assert window._refreshing and not gate.is_set()
    gate.set()


@pytest.mark.gui
def test_delayed_replay_completion_preserves_newer_clipboard_feedback(history_env, monkeypatch):
    window = _opened(history_env)
    window.table.selectRow(0)
    gate = threading.Event()
    _FakeService.resolve_gate = gate
    monkeypatch.setattr(history_env.module, "open_pygame_client_direct", lambda *args: None)
    window._activateOpenReplay()
    assert history_env.until(lambda: bool(_FakeService.resolve_calls))
    window._onCopySeedClicked()
    message = window.clipboardStatusLabel.text()
    assert "1000" in message
    assert "checking" in window.actionStatusLabel.text().lower()
    gate.set()
    assert history_env.until(lambda: not window._open_pending)
    assert "Opened" in window.actionStatusLabel.text()
    assert window.clipboardStatusLabel.text() == message
    window._onCopySeedClicked()
    assert "Opened" in window.actionStatusLabel.text()


@pytest.mark.gui
def test_query_failure_during_refresh_does_not_enable_second_writer(history_env):
    window = _opened(history_env)
    _FakeService.refresh_gate = threading.Event()
    window.refresh()
    assert history_env.until(lambda: window._refreshing)
    window._onFailed(history_env.module.WorkerError("query", "controlled", window._generation))
    assert window._refreshing and not window.refreshButton.isEnabled()


@pytest.mark.gui
def test_stale_errors_and_post_shutdown_responses_are_ignored(history_env):
    window = _opened(history_env)
    message = window.statusLabel.text()
    window._onFailed(history_env.module.WorkerError("query", "stale", window._generation - 1))
    assert window.statusLabel.text() == message
    window.close()
    window._onFailed(history_env.module.WorkerError("open_replay", "late"))
    window._onProgress("late progress")
    assert not window.openReplayButton.isEnabled()
    assert window.statusLabel.text() == message


@pytest.mark.gui
def test_escape_closes_both_worker_threads(history_env):
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest

    window = _opened(history_env)
    QTest.keyClick(window, Qt.Key_Escape)
    assert not window.isVisible()
    assert not window._thread.isRunning()
    assert not window._reader_thread.isRunning()
    assert all(service.closed for service in _FakeService.instances)


@pytest.mark.gui
def test_fast_refresh_does_not_open_reader_twice(history_env, monkeypatch):
    original = _FakeService.open.__func__
    entered, release = threading.Event(), threading.Event()

    def open_service(cls, **kwargs):
        if kwargs.get("read_only"):
            entered.set()
            assert release.wait(5)
        return original(cls, **kwargs)

    monkeypatch.setattr(_FakeService, "open", classmethod(open_service))
    window = history_env.make_window()
    try:
        assert history_env.until(lambda: entered.is_set() and not window._refreshing)
        assert window._reader_start_pending
    finally:
        release.set()
    assert history_env.until(lambda: window.model.loadedCount > 0)
    history_env.pump(.05)
    window.close()
    assert len(_FakeService.instances) == 2
    assert all(service.closed for service in _FakeService.instances)


@pytest.mark.gui
def test_keyboard_navigation_action_tab_order_and_filter_focus(history_env, monkeypatch):
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest

    window = _opened(history_env)
    window.table.selectRow(0)
    window.table.setFocus()
    QTest.keyClick(window.table, Qt.Key_Down)
    assert window._selected_location == "loc_0001"
    reached = set()
    for _ in range(50):
        focus = history_env.app.focusWidget()
        if focus is not None:
            reached.add(focus.accessibleName())
        QTest.keyClick(window, Qt.Key_Tab)
    assert {"Open Replay", "Copy Seed"} <= reached
    window.copySeedButton.setFocus()
    QTest.keyClick(window.copySeedButton, Qt.Key_Space)
    assert history_env.app.clipboard().text() == "1001"
    launches = []
    monkeypatch.setattr(history_env.module, "open_pygame_client_direct", lambda *args: launches.append(args))
    window.table.setFocus()
    QTest.keyClick(window.table, Qt.Key_Return)
    assert history_env.until(lambda: bool(launches))
    window.searchEdit.setFocus()
    window.searchEdit.setText("Alpha1")
    window._applyFilters()
    assert history_env.until(lambda: window.model.loadedCount == 311)
    assert history_env.app.focusWidget() is window.searchEdit
    window.clearFilters()
    assert history_env.until(lambda: window.model.loadedCount == 500)
    assert history_env.app.focusWidget() is window.searchEdit


@pytest.mark.gui
def test_history_action_is_available_without_an_active_agent(monkeypatch, tmp_path) -> None:
    designer = _designer(monkeypatch, tmp_path)
    try:
        tools = next(
            menu
            for menu in designer.menuBar().findChildren(type(designer.menuBar().addMenu("x")))
            if menu.title() == "Tools"
        )
        action = next(a for a in tools.actions() if a.text() == "Replay History…")
        assert action.isEnabled()
    finally:
        designer.close()
