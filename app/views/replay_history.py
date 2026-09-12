"""Replay History browser (V5 Phase 7C, extended in Phase 7D).

Brings the Qt-free ``battle_engine.replay_history`` service (Phase 7B) into the
Agent Designer as **Tools → Replay History…**: a modeless, virtualized browser
over every completed match Bytefray has written, filtered and paged entirely by
the backend.

Three invariants hold this module together.

**The GUI thread never owns the history database.**
:class:`ReplayHistoryMaintenanceWorker` and :class:`ReplayHistoryReadWorker`
construct, use, and close separate services inside their own ``QThread``.
Nothing but immutable
DTOs -- rows, details, summaries, strings -- crosses back. The window holds no
service, no connection, and no cursor, and every service call it needs is a
queued signal, never a direct call.

**No history semantics are re-decided here.** The UI issues no SQL, opens no
``result.json`` or replay, computes no identity, and re-derives no health or
timestamp fallback; ``app.services.replay_history_presentation`` formats
already-normalized backend answers and nothing more. Phase 7B's typed service
is the only door.

**A late answer never overwrites a newer question.** Every page, detail, and
Open Replay request carries a generation/request counter; a response whose
counter is stale is dropped rather than applied, so a slow query -- or a slow
replay preflight -- for a state the user has already moved past cannot
repopulate the table, or launch a Viewer, behind them.

Phase 7D adds the two remaining user actions the Phase 6 architecture
approved: **Open Replay** and **Copy Seed**. Both still run every filesystem
touch (``resolve_replay``, digest verification) on the worker thread; Open
Replay only ever hands the existing ``app.services.engine_commands.
open_pygame_client_direct`` a path this module has itself verified, and
launches it directly on the GUI thread exactly like every other Viewer launch
in this application (it is a non-blocking ``Popen`` call, not a filesystem
read). ``Re-run Match`` remains explicitly out of scope -- Phase 6 deferred it
because exact execution provenance is not guaranteed, and nothing here
reconstructs a match command.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from battle_engine.paths import get_data_root
from battle_engine.replay_history import (
    DEFAULT_PAGE_SIZE,
    HistoryCursor,
    HistoryDetail,
    HistoryQuery,
    HistoryRow,
    ReplayHistoryService,
    ReplayIntegrityCheck,
    ReplayIntegrityStatus,
    ReplayResolution,
    ReplayState,
)
from PySide6.QtCore import (
    QAbstractTableModel,
    QEvent,
    QEventLoop,
    QModelIndex,
    QObject,
    Qt,
    QThread,
    QTimer,
    Signal,
    Slot,
)
from PySide6.QtGui import QGuiApplication, QKeyEvent
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSplitter,
    QStackedWidget,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from app.services.engine_commands import open_pygame_client_direct
from app.services.replay_history_presentation import (
    CHECKING_REPLAY_TEXT,
    COPY_SEED_TOOLTIP,
    EMPTY_ERROR_TITLE,
    EMPTY_FILTERED_BODY,
    EMPTY_FILTERED_TITLE,
    EMPTY_NO_HISTORY_BODY,
    EMPTY_NO_HISTORY_TITLE,
    EMPTY_PREPARING_BODY,
    EMPTY_PREPARING_TITLE,
    HISTORY_COLUMNS,
    LOOSE_NON_DURABLE_NOTE,
    OPEN_REPLAY_TOOLTIP,
    REPLAY_FILTER_ANY,
    REPLAY_FILTER_CHOICES,
    REPLAY_MISMATCH_BODY,
    REPLAY_MISMATCH_TITLE,
    REPLAY_NO_LONGER_AVAILABLE_TEXT,
    REPLAY_OPENED_TEXT,
    RESULT_FILTER_ANY,
    RESULT_FILTER_CHOICES,
    RULESET_FILTER_ANY,
    SOURCE_FILTER_ANY,
    SOURCE_FILTER_CHOICES,
    DetailSection,
    HistoryFilterState,
    build_detail_sections,
    copy_seed_enabled,
    day_bounds,
    describe_cache_state,
    describe_count,
    describe_incomplete_scan,
    describe_open_replay_check_failure,
    describe_progress,
    describe_refresh,
    describe_replay_open_failure,
    describe_seed_copied,
    health_marker,
    is_non_durable,
    non_durable_note,
    open_replay_enabled,
    parse_seed_text,
    row_accessible_text,
    row_text,
    row_tooltip,
    ruleset_filter_choices,
)

#: Entrant/seed text settles before a query is issued. 300 ms sits inside the
#: 250-400 ms band Phase 7C specified and is comfortably longer than the
#: 66 ms worst-case backend query, so ordinary typing produces one request.
FILTER_DEBOUNCE_MS = 300

#: Progress callbacks arrive every 1,000 scanned artifacts. Coalescing them to
#: one repaint per interval keeps a long rebuild from spending the GUI thread
#: on status text it will immediately overwrite.
PROGRESS_THROTTLE_MS = 120

# ----------------------------------------------------------------------
# Worker payloads
#
# Plain frozen values. Everything that crosses the thread boundary is one of
# these; no service, connection, cursor, or live model object ever does.
# ----------------------------------------------------------------------


@dataclass(frozen=True)
class OpenResult:
    message: str
    is_empty: bool
    rebuilding: bool
    persistent: bool = True


@dataclass(frozen=True)
class PageResult:
    generation: int
    rows: tuple[HistoryRow, ...]
    next_cursor: HistoryCursor | None
    has_more: bool
    total: int
    #: First page of a query (replace the model) versus a continuation (append).
    reset: bool


@dataclass(frozen=True)
class DetailResult:
    generation: int
    location_id: str
    detail: HistoryDetail | None


@dataclass(frozen=True)
class RefreshResult:
    message: str
    cancelled: bool
    incomplete_message: str


@dataclass(frozen=True)
class WorkerError:
    operation: str
    message: str
    generation: int | None = None


@dataclass(frozen=True)
class ReplayOpenResult:
    """Click-time Open Replay preflight outcome (Phase 7D).

    ``request_id`` is compared against the window's own counter so a late
    answer for a superseded request can never launch a Viewer -- the same
    generation discipline every other worker response already uses.
    ``integrity`` is ``None`` only when ``resolution`` itself was not
    ``available``: there is nothing to digest-check without a resolved path.
    """

    request_id: int
    location_id: str
    resolution: ReplayResolution
    integrity: ReplayIntegrityCheck | None


# ----------------------------------------------------------------------
# Worker
# ----------------------------------------------------------------------


class _HistoryQueryWorker(QObject):
    """Owns ``ReplayHistoryService`` on a ``QThread``; speaks only in DTOs.

    Every slot here runs on the worker thread. The service is created in
    :meth:`start` -- *not* in ``__init__`` -- because the object is constructed
    on the GUI thread and moved, and SQLite connections belong to the thread
    that will use them.
    """

    opened = Signal(object)
    pageReady = Signal(object)
    detailReady = Signal(object)
    progressed = Signal(str)
    refreshFinished = Signal(object)
    rulesetFacetsReady = Signal(object)
    replayResolved = Signal(object)
    failed = Signal(object)
    closed = Signal()
    _read_only = True

    def __init__(
        self,
        *,
        data_root: Path | None = None,
        runs_root: Path | None = None,
        cache_path: Path | None = None,
    ) -> None:
        super().__init__()
        self._data_root = data_root
        self._runs_root = runs_root
        self._cache_path = cache_path
        self._service: ReplayHistoryService | None = None
        # Set from the GUI thread and read here. A queued "cancel" signal would
        # be useless: it would sit in this thread's event queue *behind* the
        # very refresh it is meant to interrupt. A shared flag is the only
        # mechanism that reaches a running call, and it is exactly the shape
        # the backend's ``cancel_check`` expects.
        self._cancel = threading.Event()
        self._stopping = threading.Event()
        self._progress_timer: float = 0.0

    # -- lifecycle -----------------------------------------------------

    @Slot()
    def start(self) -> None:
        """Open the service on this thread and report what the cache looked like."""
        if self._stopping.is_set() or self._service is not None:
            return
        try:
            self._service = ReplayHistoryService.open(
                data_root=self._data_root,
                runs_root=self._runs_root,
                cache_path=self._cache_path,
                read_only=self._read_only,
            )
        # A worker exception must become a UI state, never an unhandled
        # raise inside the event loop.
        except Exception as exc:
            self.failed.emit(WorkerError("reader_open" if self._read_only else "open", str(exc)))
            return
        report = self._service.cache_report
        self.opened.emit(
            OpenResult(
                message=describe_cache_state(
                    report.created and report.rebuild_reason in (None, "new_cache", "in_memory_cache"),
                    report.rebuild_required, report.persistent
                ),
                is_empty=self._service.is_empty(),
                rebuilding=report.rebuild_required,
                persistent=report.persistent,
            )
        )

    @Slot()
    def shutdown(self) -> None:
        """Close the service and stop this thread's event loop.

        Quitting the thread from inside the worker keeps the close path
        independent of GUI event delivery. The GUI pumps timers and painting
        while awaiting completion, then joins the finished thread.
        """

        self._close_service()
        self.closed.emit()
        thread = QThread.currentThread()
        if thread is not None:
            thread.quit()

    def _close_service(self) -> None:
        service, self._service = self._service, None
        if service is None:
            return
        try:
            service.close()
        except Exception as exc:  # closing must not raise on the shutdown path
            self.failed.emit(WorkerError("close", str(exc)))

    def requestCancel(self) -> None:
        """Ask the in-flight refresh to stop. Safe to call from the GUI thread."""

        self._cancel.set()

    def requestStop(self) -> None:
        self._stopping.set()
        self._cancel.set()

    def clearCancel(self) -> None:
        self._cancel.clear()

    @property
    def cancelled(self) -> bool:
        return self._cancel.is_set()

    # -- queries -------------------------------------------------------

    @Slot(object, object, int, bool)
    def fetchPage(
        self,
        query: HistoryQuery,
        cursor: HistoryCursor | None,
        generation: int,
        reset: bool,
    ) -> None:
        """One keyset page, plus the matching total when this is a first page.

        ``count()`` is skipped for continuations: the total cannot have changed
        between pages of one unchanged query, and on the measured corpus it is
        the more expensive of the two calls.
        """

        service = self._service
        if service is None or self._stopping.is_set():
            return
        try:
            if reset:
                page, total = service.fetch_page_with_count(query, limit=DEFAULT_PAGE_SIZE)
            else:
                page = service.fetch_page(query, cursor=cursor, limit=DEFAULT_PAGE_SIZE)
                total = -1
        except Exception as exc:  # becomes a UI state, not a crash
            self.failed.emit(WorkerError("query", str(exc), generation))
            return
        self.pageReady.emit(
            PageResult(
                generation=generation,
                rows=page.rows,
                next_cursor=page.next_cursor,
                has_more=page.has_more,
                total=total,
                reset=reset,
            )
        )

    @Slot(str, int)
    def fetchDetail(self, location_id: str, generation: int) -> None:
        service = self._service
        if service is None or self._stopping.is_set():
            return
        try:
            detail = service.fetch_detail(location_id)
        except Exception as exc:
            self.failed.emit(WorkerError("detail", str(exc), generation))
            return
        self.detailReady.emit(DetailResult(generation, location_id, detail))

    @Slot(str, int)
    def openReplay(self, location_id: str, request_id: int) -> None:
        """Click-time preflight for Open Replay: resolve, then digest-verify.

        Both steps are backend calls that read the filesystem (and, for
        verification, the full replay bytes), so both belong here on the
        worker thread -- never on the GUI thread, and never trusting the
        cached row state the button decision was made from. The window
        launches the Viewer itself once this returns; nothing here starts a
        process.
        """

        service = self._service
        if service is None or self._stopping.is_set():
            return
        try:
            resolution = service.resolve_replay(location_id)
            integrity = service.verify_replay_integrity(resolution) if resolution.available else None
        except Exception as exc:
            self.failed.emit(WorkerError("open_replay", str(exc), request_id))
            return
        self.replayResolved.emit(ReplayOpenResult(request_id, location_id, resolution, integrity))

    @Slot()
    def fetchRulesetFacets(self) -> None:
        service = self._service
        if service is None or self._stopping.is_set():
            return
        try:
            facets = service.ruleset_facets()
        except Exception as exc:
            self.failed.emit(WorkerError("facets", str(exc)))
            return
        self.rulesetFacetsReady.emit(facets)

class ReplayHistoryReadWorker(_HistoryQueryWorker):
    """Read-only service and connection, owned entirely by the query thread."""


class ReplayHistoryMaintenanceWorker(_HistoryQueryWorker):
    """Own initialization, recovery and refresh on the maintenance thread.

    Shared query slots are used only for the existing session-only fallback,
    whose private in-memory cache cannot be opened by a second connection.
    """

    _read_only = False

    @Slot()
    def refresh(self) -> None:
        """Reconcile (or rebuild) the index, reporting progress and honouring cancel.

        A cancelled refresh is not an error: the backend rolls its transaction
        back, the previous generation stays committed, and the rows already on
        screen stay valid.
        """

        service = self._service
        if service is None:
            return
        # Deliberately does *not* clear the cancel flag. A cancel (or a
        # shutdown) raised while this slot was still queued behind an earlier
        # request must survive to be seen here; clearing on entry would discard
        # it and run the whole scan anyway. The requester owns the flag's
        # lifetime and clears it when it asks for a new refresh.
        self._progress_timer = 0.0
        try:
            summary = service.refresh(
                progress=self._emit_progress,
                cancel_check=self._cancel.is_set,
            )
        except Exception as exc:
            self.failed.emit(WorkerError("refresh", str(exc)))
            return
        cancelled = not summary.committed
        self.refreshFinished.emit(
            RefreshResult(
                message=describe_refresh(summary),
                cancelled=cancelled,
                incomplete_message="" if cancelled else describe_incomplete_scan(summary),
            )
        )

    def _emit_progress(self, phase: str, seen: int) -> None:
        """Throttle backend progress into at most one status update per interval."""

        now = _monotonic_ms()
        if now - self._progress_timer < PROGRESS_THROTTLE_MS:
            return
        self._progress_timer = now
        self.progressed.emit(describe_progress(phase, seen))


def _monotonic_ms() -> float:
    import time

    return time.monotonic() * 1000.0


# ----------------------------------------------------------------------
# Table model
# ----------------------------------------------------------------------


class ReplayHistoryTableModel(QAbstractTableModel):
    """Virtualized model over loaded history pages.

    Holds presentation DTOs (``HistoryRow``) and never a database row, a
    cursor, or a widget per occurrence. Rows arrive 500 at a time; Qt's own
    ``canFetchMore``/``fetchMore`` protocol asks for the next page as the view
    approaches the end, and the request is served asynchronously -- this model
    signals that more are wanted and inserts them when the worker answers.
    """

    moreRequested = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._rows: list[HistoryRow] = []
        self._has_more = False
        self._fetch_pending = False

    # -- Qt model interface -------------------------------------------

    def rowCount(self, parent: QModelIndex | None = None) -> int:
        if parent is not None and parent.isValid():
            return 0
        return len(self._rows)

    def columnCount(self, parent: QModelIndex | None = None) -> int:
        if parent is not None and parent.isValid():
            return 0
        return len(HISTORY_COLUMNS)

    def headerData(
        self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole
    ) -> Any:
        if orientation is not Qt.Horizontal or not 0 <= section < len(HISTORY_COLUMNS):
            return None
        if role in (Qt.DisplayRole, Qt.AccessibleTextRole):
            return HISTORY_COLUMNS[section].title
        return None

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        if not index.isValid() or not 0 <= index.row() < len(self._rows):
            return None
        row = self._rows[index.row()]
        column = HISTORY_COLUMNS[index.column()]

        if role == Qt.DisplayRole:
            text = row_text(row, column.key)
            if index.column() == 0:
                # Health reaches the user as a character in the leading cell,
                # never as color alone.
                marker = health_marker(row)
                return f"{marker} {text}" if marker else text
            return text
        if role == Qt.ToolTipRole:
            return row_tooltip(row, column.key) or None
        if role == Qt.AccessibleTextRole:
            return row_accessible_text(row) if index.column() == 0 else row_text(row, column.key)
        if role == Qt.TextAlignmentRole and column.key in ("seed",):
            return int(Qt.AlignRight | Qt.AlignVCenter)
        return None

    def canFetchMore(self, parent: QModelIndex | None = None) -> bool:
        if parent is not None and parent.isValid():
            return False
        return self._has_more and not self._fetch_pending

    def fetchMore(self, parent: QModelIndex | None = None) -> None:
        if parent is not None and parent.isValid():
            return
        if not self._has_more or self._fetch_pending:
            return
        self._fetch_pending = True
        self.moreRequested.emit()

    # -- population ----------------------------------------------------

    def resetRows(self, rows: tuple[HistoryRow, ...], has_more: bool) -> None:
        self.beginResetModel()
        self._rows = list(rows)
        self._has_more = has_more
        self._fetch_pending = False
        self.endResetModel()

    def appendRows(self, rows: tuple[HistoryRow, ...], has_more: bool) -> None:
        self._fetch_pending = False
        if rows:
            first = len(self._rows)
            self.beginInsertRows(QModelIndex(), first, first + len(rows) - 1)
            self._rows.extend(rows)
            self.endInsertRows()
        self._has_more = has_more

    def suspendFetching(self) -> None:
        """Stop offering more rows until the next first page lands.

        Called when a new query is issued. Between that moment and the reply,
        the model still holds the *previous* query's rows, so leaving
        ``canFetchMore`` true invites the view to ask for a continuation that
        no longer has a valid cursor -- a request that would simply be dropped,
        leaving a view scrolled to the bottom stuck until the user scrolled
        again. ``resetRows`` restores the real value from the reply.
        """

        self._has_more = False
        self._fetch_pending = False

    def rowAt(self, position: int) -> HistoryRow | None:
        if 0 <= position < len(self._rows):
            return self._rows[position]
        return None

    def positionOf(self, location_id: str) -> int:
        for position, row in enumerate(self._rows):
            if row.location_id == location_id:
                return position
        return -1

    @property
    def loadedCount(self) -> int:
        return len(self._rows)

    @property
    def hasMore(self) -> bool:
        return self._has_more


# ----------------------------------------------------------------------
# Detail pane
# ----------------------------------------------------------------------


class ReplayHistoryDetailPane(QScrollArea):
    """Grouped presentation of one occurrence's normalized metadata."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWidgetResizable(True)
        # Long values (a diagnostic, a configuration line) wrap instead of
        # pushing a horizontal scrollbar under the whole pane.
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setAccessibleName("Match details")
        self._body = QWidget()
        self._layout = QVBoxLayout(self._body)
        self._layout.setContentsMargins(8, 8, 8, 8)
        self._layout.setSpacing(8)
        self._placeholder = QLabel("Select a match to see its details.")
        self._placeholder.setWordWrap(True)
        self._layout.addWidget(self._placeholder)
        self._layout.addStretch(1)
        self.setWidget(self._body)
        self._show_advanced = False
        self._sections: tuple[DetailSection, ...] = ()

    def setShowAdvanced(self, show: bool) -> None:
        self._show_advanced = show
        self._render()

    def showMessage(self, message: str) -> None:
        self._sections = ()
        self._placeholder.setText(message)
        self._render()

    def setSections(self, sections: tuple[DetailSection, ...]) -> None:
        self._sections = sections
        self._render()

    def _render(self) -> None:
        while self._layout.count():
            item = self._layout.takeAt(0)
            widget = item.widget()
            if widget is not None and widget is not self._placeholder:
                # Unparent *before* scheduling deletion. Taking an item out of
                # a layout does not unparent its widget, and ``deleteLater``
                # only runs on the next event-loop pass -- so without this the
                # previous selection's groups stay children of the body widget
                # and keep painting underneath the new ones. Found by looking
                # at the rendered window, not by reading the code.
                widget.setParent(None)
                widget.deleteLater()

        if not self._sections:
            self._placeholder.setVisible(True)
            self._layout.addWidget(self._placeholder)
            self._layout.addStretch(1)
            return

        self._placeholder.setVisible(False)
        for section in self._sections:
            if section.advanced and not self._show_advanced:
                continue
            self._layout.addWidget(_section_group(section))
        self._layout.addStretch(1)


def _section_group(section: DetailSection) -> QGroupBox:
    group = QGroupBox(section.title)
    group.setAccessibleName(f"{section.title} details")
    form = QFormLayout(group)
    form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
    form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
    for note in section.notes:
        note_label = QLabel(note)
        note_label.setWordWrap(True)
        note_label.setAccessibleName("Note")
        form.addRow(note_label)
    for entry in section.fields:
        value = QLabel(entry.value)
        value.setWordWrap(True)
        value.setTextInteractionFlags(Qt.TextSelectableByMouse)
        value.setAccessibleName(entry.label)
        if entry.tooltip:
            value.setToolTip(entry.tooltip)
            value.setAccessibleDescription(entry.tooltip)
        form.addRow(f"{entry.label}:", value)
    return group


# ----------------------------------------------------------------------
# Window
# ----------------------------------------------------------------------


class ReplayHistoryWindow(QDialog):
    """Modeless Replay History browser.

    Modeless because browsing history alongside the Designer is the point;
    the Designer keeps a single instance and raises it rather than opening a
    second window onto the same index.
    """

    #: Emitted once this browser has closed and joined its worker. The owner
    #: uses it to drop its reference immediately rather than waiting for Qt's
    #: deferred deletion, so a reopen can never raise an already-shut-down
    #: window whose worker is gone and whose Refresh is permanently disabled.
    windowClosed = Signal()

    #: Requests to the worker. Connected across the thread boundary, so Qt
    #: queues them and the window never touches the service itself.
    pageRequested = Signal(object, object, int, bool)
    detailRequested = Signal(str, int)
    refreshRequested = Signal()
    facetsRequested = Signal()
    openReplayRequested = Signal(str, int)
    shutdownRequested = Signal()
    readerStartRequested = Signal()
    readerShutdownRequested = Signal()

    def __init__(
        self,
        *,
        data_root: Path | None = None,
        runs_root: Path | None = None,
        cache_path: Path | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Replay History")
        # Wide enough that the six fixed columns plus a readable Entrants
        # column and the detail pane all fit without horizontal scrolling at a
        # practical desktop resolution. Resizable, and both panes scale.
        self.resize(1360, 780)
        self.setSizeGripEnabled(True)

        # Resolved the same way ReplayHistoryService.open() resolves it, for
        # the same reason: the Designer always passes a concrete data_root
        # today, but a None default must still hand the Viewer a real path.
        self._data_root = data_root if data_root is not None else get_data_root()

        self._generation = 0
        self._detail_generation = 0
        self._filters = HistoryFilterState()
        self._query: HistoryQuery = self._filters.to_query()
        self._next_cursor: HistoryCursor | None = None
        self._total = 0
        self._selected_location: str | None = None
        self._selected_replay_state: ReplayState | None = None
        self._selected_seed: int | None = None
        self._pending_reselect: str | None = None
        self._refreshing = False
        self._shutdown_started = False
        self._initial_query_sent = False
        self._reader_ready = False
        self._reader_start_pending = False
        self._persistent = True
        # Open Replay is a single in-flight operation: a request commits to
        # launching *that* occurrence when it resolves (Phase 7D Sec 11), and
        # no second request is accepted until it does, so a rapid double
        # click/Enter/button combination can never fire two preflights.
        self._open_request_id = 0
        self._open_pending = False
        # What the last completed refresh did. Held across the re-query that
        # follows it, so the summary does not vanish the instant the new first
        # page lands; cleared when the user asks a new question.
        self._status_note = ""

        self._buildUi()

        self._thread = QThread(self)
        self._thread.setObjectName("bytefray-history-maintenance")
        self._worker = ReplayHistoryMaintenanceWorker(
            data_root=data_root, runs_root=runs_root, cache_path=cache_path
        )
        self._worker.moveToThread(self._thread)
        self._reader_thread = QThread(self)
        self._reader_thread.setObjectName("bytefray-history-reader")
        self._reader = ReplayHistoryReadWorker(
            data_root=data_root, runs_root=runs_root, cache_path=cache_path
        )
        self._reader.moveToThread(self._reader_thread)
        self._connectWorker()
        self._thread.finished.connect(self._worker.deleteLater)
        self._reader_thread.finished.connect(self._reader.deleteLater)
        self._thread.started.connect(self._worker.start)
        self._reader_thread.start()
        self._thread.start()

    # -- construction --------------------------------------------------

    def _buildUi(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        layout.addWidget(self._buildFilterArea())
        layout.addLayout(self._buildStatusArea())

        self._splitter = QSplitter(Qt.Horizontal)
        self._splitter.addWidget(self._buildTableArea())
        self._splitter.addWidget(self._buildDetailArea())
        self._splitter.setStretchFactor(0, 3)
        self._splitter.setStretchFactor(1, 2)
        # Explicit initial sizes: stretch factors alone left the table too
        # narrow for Entrants to receive any leftover width at all, which
        # collapsed the one column with unbounded content to the smallest on
        # screen. Found by inspecting the rendered window, not by reading it.
        self._splitter.setSizes([940, 400])
        layout.addWidget(self._splitter, 1)

        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(self.close)
        buttons.accepted.connect(self.close)
        layout.addWidget(buttons)

    def _buildFilterArea(self) -> QWidget:
        box = QGroupBox("Filters")
        grid = QGridLayout(box)
        grid.setHorizontalSpacing(10)

        searchLabel = QLabel("&Search entrants:")
        self.searchEdit = QLineEdit()
        self.searchEdit.setPlaceholderText("Agent name or ID")
        self.searchEdit.setClearButtonEnabled(True)
        self.searchEdit.setAccessibleName("Entrant search")
        searchLabel.setBuddy(self.searchEdit)
        grid.addWidget(searchLabel, 0, 0)
        grid.addWidget(self.searchEdit, 0, 1)

        rulesetLabel = QLabel("&Ruleset:")
        self.rulesetCombo = QComboBox()
        self.rulesetCombo.addItem("All Rulesets", RULESET_FILTER_ANY)
        self.rulesetCombo.setAccessibleName("Ruleset filter")
        rulesetLabel.setBuddy(self.rulesetCombo)
        grid.addWidget(rulesetLabel, 0, 2)
        grid.addWidget(self.rulesetCombo, 0, 3)

        resultLabel = QLabel("Res&ult:")
        self.resultCombo = _combo(RESULT_FILTER_CHOICES, "Result filter")
        resultLabel.setBuddy(self.resultCombo)
        grid.addWidget(resultLabel, 0, 4)
        grid.addWidget(self.resultCombo, 0, 5)

        sourceLabel = QLabel("S&ource:")
        self.sourceCombo = _combo(SOURCE_FILTER_CHOICES, "Source filter")
        sourceLabel.setBuddy(self.sourceCombo)
        grid.addWidget(sourceLabel, 1, 0)
        grid.addWidget(self.sourceCombo, 1, 1)

        replayLabel = QLabel("Re&play:")
        self.replayCombo = _combo(REPLAY_FILTER_CHOICES, "Replay state filter")
        replayLabel.setBuddy(self.replayCombo)
        grid.addWidget(replayLabel, 1, 2)
        grid.addWidget(self.replayCombo, 1, 3)

        seedLabel = QLabel("See&d:")
        self.seedEdit = QLineEdit()
        self.seedEdit.setPlaceholderText("Exact seed")
        self.seedEdit.setClearButtonEnabled(True)
        self.seedEdit.setAccessibleName("Seed filter")
        seedLabel.setBuddy(self.seedEdit)
        grid.addWidget(seedLabel, 1, 4)
        grid.addWidget(self.seedEdit, 1, 5)

        dateRow = QHBoxLayout()
        self.fromCheck = QCheckBox("Fro&m:")
        self.fromCheck.setAccessibleName("Enable start date filter")
        self.fromDate = QDateEdit()
        self.fromDate.setCalendarPopup(True)
        self.fromDate.setEnabled(False)
        self.fromDate.setAccessibleName("Start date")
        self.toCheck = QCheckBox("&To:")
        self.toCheck.setAccessibleName("Enable end date filter")
        self.toDate = QDateEdit()
        self.toDate.setCalendarPopup(True)
        self.toDate.setEnabled(False)
        self.toDate.setAccessibleName("End date")
        dateRow.addWidget(self.fromCheck)
        dateRow.addWidget(self.fromDate)
        dateRow.addSpacing(12)
        dateRow.addWidget(self.toCheck)
        dateRow.addWidget(self.toDate)
        dateRow.addStretch(1)

        self.clearFiltersButton = QPushButton("&Clear Filters")
        self.clearFiltersButton.setAccessibleName("Clear all filters")
        dateRow.addWidget(self.clearFiltersButton)
        grid.addLayout(dateRow, 2, 0, 1, 6)
        grid.setColumnStretch(1, 3)
        grid.setColumnStretch(3, 2)
        grid.setColumnStretch(5, 2)

        self._debounce = QTimer(self)
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(FILTER_DEBOUNCE_MS)
        self._debounce.timeout.connect(self._applyFilters)

        self.searchEdit.textChanged.connect(self._scheduleFilterApply)
        self.seedEdit.textChanged.connect(self._onSeedTextChanged)
        for combo in (self.rulesetCombo, self.resultCombo, self.sourceCombo, self.replayCombo):
            combo.currentIndexChanged.connect(self._applyFilters)
        self.fromCheck.toggled.connect(self.fromDate.setEnabled)
        self.toCheck.toggled.connect(self.toDate.setEnabled)
        for control in (self.fromCheck, self.toCheck):
            control.toggled.connect(self._applyFilters)
        for control in (self.fromDate, self.toDate):
            control.dateChanged.connect(self._applyFilters)
        self.clearFiltersButton.clicked.connect(self.clearFilters)
        return box

    def _buildStatusArea(self) -> QHBoxLayout:
        row = QHBoxLayout()
        self.statusLabel = QLabel("Opening Replay History…")
        self.statusLabel.setAccessibleName("Replay History status")
        self.progressBar = QProgressBar()
        self.progressBar.setRange(0, 0)  # indeterminate: the backend reports
        self.progressBar.setMaximumWidth(180)  # artifacts seen, not a total
        self.progressBar.setVisible(False)
        self.progressBar.setAccessibleName("History refresh progress")
        self.refreshButton = QPushButton("&Refresh")
        self.refreshButton.setAccessibleName("Refresh history")
        self.refreshButton.setToolTip("Check the runs folder for new or changed matches.")
        self.refreshButton.setEnabled(False)
        self.cancelButton = QPushButton("Cancel")
        self.cancelButton.setAccessibleName("Cancel history refresh")
        self.cancelButton.setVisible(False)
        row.addWidget(self.statusLabel, 1)
        row.addWidget(self.progressBar)
        row.addWidget(self.cancelButton)
        row.addWidget(self.refreshButton)
        self.refreshButton.clicked.connect(self.refresh)
        self.cancelButton.clicked.connect(self.cancelRefresh)
        return row

    def _buildTableArea(self) -> QWidget:
        self.stack = QStackedWidget()

        self.table = QTableView()
        self.model = ReplayHistoryTableModel(self)
        self.table.setModel(self.model)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(False)  # backend ordering is fixed (Phase 6 O)
        self.table.setWordWrap(False)
        self.table.verticalHeader().setVisible(False)
        self.table.setAccessibleName("Match history")
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setStretchLastSection(False)
        header.setMinimumSectionSize(60)
        for position, column in enumerate(HISTORY_COLUMNS):
            self.table.setColumnWidth(position, column.width)
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # Entrants absorbs slack
        self.stack.addWidget(self.table)

        self.messagePage = _MessagePage()
        self.stack.addWidget(self.messagePage)

        self.model.moreRequested.connect(self._requestNextPage)
        selection = self.table.selectionModel()
        if selection is not None:
            selection.currentRowChanged.connect(self._onRowChanged)
        self.table.doubleClicked.connect(self._onTableDoubleClicked)
        # Enter/Return activates Open Replay only while the *table* has
        # focus, scoped by installing the filter on the table widget itself
        # -- a filter field's own Enter handling (there is none today, but
        # nothing here should ever intercept it) is a different QObject and
        # never reaches this filter.
        self.table.installEventFilter(self)
        return self.stack

    def _buildDetailArea(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self.looseLabel = QLabel(LOOSE_NON_DURABLE_NOTE)
        self.looseLabel.setWordWrap(True)
        self.looseLabel.setVisible(False)
        self.looseLabel.setAccessibleName("History durability notice")
        layout.addWidget(self.looseLabel)

        self.detailPane = ReplayHistoryDetailPane()
        layout.addWidget(self.detailPane, 1)

        actionRow = QHBoxLayout()
        self.openReplayButton = QPushButton("&Open Replay")
        self.openReplayButton.setAccessibleName("Open Replay")
        self.openReplayButton.setToolTip(OPEN_REPLAY_TOOLTIP)
        self.openReplayButton.setEnabled(False)
        self.openReplayButton.clicked.connect(self._activateOpenReplay)
        self.copySeedButton = QPushButton("Cop&y Seed")
        self.copySeedButton.setAccessibleName("Copy Seed")
        self.copySeedButton.setToolTip(COPY_SEED_TOOLTIP)
        self.copySeedButton.setEnabled(False)
        self.copySeedButton.clicked.connect(self._onCopySeedClicked)
        actionRow.addWidget(self.openReplayButton)
        actionRow.addWidget(self.copySeedButton)
        actionRow.addStretch(1)
        layout.addLayout(actionRow)

        self.actionStatusLabel = QLabel("")
        self.actionStatusLabel.setWordWrap(True)
        self.actionStatusLabel.setAccessibleName("Replay action status")
        layout.addWidget(self.actionStatusLabel)
        self.clipboardStatusLabel = QLabel("")
        self.clipboardStatusLabel.setWordWrap(True)
        self.clipboardStatusLabel.setAccessibleName("Clipboard action status")
        self.clipboardStatusLabel.setVisible(False)
        layout.addWidget(self.clipboardStatusLabel)

        self.advancedCheck = QCheckBox("Show technical &details")
        self.advancedCheck.setAccessibleName("Show technical details")
        self.advancedCheck.toggled.connect(self.detailPane.setShowAdvanced)
        layout.addWidget(self.advancedCheck)
        return panel

    def _connectWorker(self) -> None:
        self._connectQueries(self._reader)
        self.refreshRequested.connect(self._worker.refresh)
        self.shutdownRequested.connect(self._worker.shutdown)
        self.readerStartRequested.connect(self._reader.start)
        self.readerShutdownRequested.connect(self._reader.shutdown)
        self._worker.opened.connect(self._onOpened)
        self._reader.opened.connect(self._onReaderOpened)
        self._worker.progressed.connect(self._onProgress)
        self._worker.refreshFinished.connect(self._onRefreshFinished)
        for worker in (self._reader, self._worker):
            worker.pageReady.connect(self._onPageReady)
            worker.detailReady.connect(self._onDetailReady)
            worker.rulesetFacetsReady.connect(self._onRulesetFacets)
            worker.replayResolved.connect(self._onReplayResolved)
            worker.failed.connect(self._onFailed)

    def _connectQueries(self, worker: _HistoryQueryWorker) -> None:
        self.pageRequested.connect(worker.fetchPage)
        self.detailRequested.connect(worker.fetchDetail)
        self.facetsRequested.connect(worker.fetchRulesetFacets)
        self.openReplayRequested.connect(worker.openReplay)

    # -- worker requests -----------------------------------------------
    #
    # Requests leave as signals, which Qt delivers to the worker thread as
    # queued invocations carrying the Python DTOs untouched. The window never
    # calls a service method and never calls a worker slot directly -- the one
    # exception is ``requestCancel``, a thread-safe flag precisely because it
    # has to overtake a call that is already running.

    def _requestFirstPage(self) -> None:
        self._generation += 1
        self._next_cursor = None
        self.model.suspendFetching()
        if not self._reader_ready or self._shutdown_started:
            return
        self.pageRequested.emit(self._query, None, self._generation, True)

    @Slot()
    def _requestNextPage(self) -> None:
        if self._next_cursor is None:
            self.model.suspendFetching()
            return
        self.pageRequested.emit(self._query, self._next_cursor, self._generation, False)

    def refresh(self) -> None:
        """Reconcile in the worker, keeping the current rows and filters visible."""

        if self._refreshing or self._shutdown_started:
            return
        self._status_note = ""
        self._worker.clearCancel()
        self._setRefreshing(True)
        self.statusLabel.setText("Checking for new matches…")
        self.refreshRequested.emit()

    def cancelRefresh(self) -> None:
        if not self._refreshing:
            return
        self.cancelButton.setEnabled(False)
        self.statusLabel.setText("Cancelling…")
        self._worker.requestCancel()

    # -- worker responses ----------------------------------------------

    @Slot(object)
    def _onOpened(self, result: OpenResult) -> None:
        if self._shutdown_started:
            return
        self._persistent = result.persistent
        self.refreshButton.setEnabled(True)
        if result.is_empty:
            self._showMessage(EMPTY_PREPARING_TITLE, EMPTY_PREPARING_BODY)
        self.statusLabel.setText(result.message)
        if not result.persistent:
            self.pageRequested.disconnect(self._reader.fetchPage)
            self.detailRequested.disconnect(self._reader.fetchDetail)
            self.facetsRequested.disconnect(self._reader.fetchRulesetFacets)
            self.openReplayRequested.disconnect(self._reader.openReplay)
            self._connectQueries(self._worker)
            self._onReaderOpened(result)
        elif not result.rebuilding:
            self._startReader()
        self._worker.clearCancel()
        self._setRefreshing(True)
        self.refreshRequested.emit()

    def _startReader(self) -> None:
        if self._reader_ready or self._reader_start_pending or self._shutdown_started:
            return
        self._reader_start_pending = True
        self.readerStartRequested.emit()

    @Slot(object)
    def _onReaderOpened(self, _result: OpenResult) -> None:
        if self._shutdown_started:
            return
        self._reader_ready = True
        self._reader_start_pending = False
        self._initial_query_sent = True
        self._requestFirstPage()
        self.facetsRequested.emit()

    @Slot(object)
    def _onPageReady(self, result: PageResult) -> None:
        if self._shutdown_started or result.generation != self._generation:
            return  # a newer query has already been asked; this answer is stale
        self._next_cursor = result.next_cursor
        if result.reset:
            self._total = result.total
            self.model.resetRows(result.rows, result.has_more)
            self._restoreSelection()
        else:
            self.model.appendRows(result.rows, result.has_more)
        self._updateCounts()

    @Slot(object)
    def _onDetailReady(self, result: DetailResult) -> None:
        if self._shutdown_started or result.generation != self._detail_generation:
            return
        if result.location_id != self._selected_location:
            return
        if result.detail is None:
            self._selected_replay_state = None
            self._updateActionState()
            self.detailPane.showMessage(
                "This match is no longer in the history index. Refresh to update the list."
            )
            self.looseLabel.setVisible(False)
            return
        self.detailPane.setSections(build_detail_sections(result.detail))
        note = non_durable_note(result.detail)
        self.looseLabel.setText(note or LOOSE_NON_DURABLE_NOTE)
        self.looseLabel.setVisible(bool(note))

    @Slot(str)
    def _onProgress(self, message: str) -> None:
        if self._shutdown_started:
            return
        self.statusLabel.setText(message)

    @Slot(object)
    def _onRefreshFinished(self, result: RefreshResult) -> None:
        if self._shutdown_started:
            return
        self._setRefreshing(False)
        message = "Refresh cancelled." if result.cancelled else result.message
        if result.incomplete_message:
            message = f"{message}  {result.incomplete_message}"
        self._status_note = message
        self.statusLabel.setText(message)
        if not self._reader_ready and self._persistent:
            # The writer has finished preparing the cache, even if its first
            # population was cancelled. The last committed snapshot is usable.
            self._startReader()
            return
        if result.cancelled:
            # Nothing was committed, so the rows on screen are still exactly
            # what the index holds. Re-querying would only churn the table.
            self._updateCounts()
            return
        self._pending_reselect = self._selected_location
        self._requestFirstPage()
        self.facetsRequested.emit()

    @Slot(object)
    def _onRulesetFacets(self, facets: Any) -> None:
        if self._shutdown_started:
            return
        choices = ruleset_filter_choices(facets)
        current = self.rulesetCombo.currentData()
        blocked = self.rulesetCombo.blockSignals(True)
        self.rulesetCombo.clear()
        for choice in choices:
            self.rulesetCombo.addItem(choice.label, choice.value)
        position = self.rulesetCombo.findData(current)
        self.rulesetCombo.setCurrentIndex(max(0, position))
        self.rulesetCombo.blockSignals(blocked)

    @Slot(object)
    def _onFailed(self, error: WorkerError) -> None:
        """Turn a worker exception into a visible state, never an unhandled raise."""

        if self._shutdown_started:
            return
        current = {"query": self._generation, "detail": self._detail_generation,
                   "open_replay": self._open_request_id}.get(error.operation)
        if error.generation is not None and error.generation != current:
            return
        if error.operation in ("open", "refresh"):
            self._setRefreshing(False)
        if error.operation in ("open", "reader_open"):
            self._showMessage(
                EMPTY_ERROR_TITLE,
                f"Replay History could not be opened.\n\n{error.message}",
            )
            self.refreshButton.setEnabled(False)
            self.statusLabel.setText(EMPTY_ERROR_TITLE)
            return
        if error.operation == "detail":
            self.detailPane.showMessage(f"These match details could not be read.\n\n{error.message}")
            return
        if error.operation == "open_replay":
            self._open_pending = False
            self._updateActionState()
            self.actionStatusLabel.setText(describe_open_replay_check_failure(error.message))
            return
        # Query/refresh/facet failures keep whatever is already on screen: a
        # transient read problem must not throw away a usable list.
        self._status_note = f"History could not be updated — {error.message}"
        self.statusLabel.setText(self._status_note)

    # -- filters -------------------------------------------------------

    @Slot()
    def _scheduleFilterApply(self) -> None:
        self._debounce.start()

    @Slot(str)
    def _onSeedTextChanged(self, text: str) -> None:
        """Mark an unparseable seed inline; never interrupt typing with a dialog."""

        _value, valid = parse_seed_text(text)
        self.seedEdit.setToolTip("" if valid else "Enter a whole number, or leave empty.")
        self.seedEdit.setAccessibleDescription(
            "" if valid else "Invalid seed; enter a whole number."
        )
        self._scheduleFilterApply()

    @Slot()
    def _applyFilters(self) -> None:
        self._debounce.stop()
        filters = self._currentFilters()
        if filters == self._filters and self._initial_query_sent:
            return
        self._filters = filters
        self._query = filters.to_query()
        if not self._initial_query_sent:
            return
        self._pending_reselect = None
        self._status_note = ""
        self._clearSelection()
        self._requestFirstPage()

    def _currentFilters(self) -> HistoryFilterState:
        start = end = None
        if self.fromCheck.isChecked():
            date = self.fromDate.date()
            start = day_bounds(date.year(), date.month(), date.day())[0]
        if self.toCheck.isChecked():
            date = self.toDate.date()
            end = day_bounds(date.year(), date.month(), date.day())[1]
        return HistoryFilterState(
            entrant_text=self.searchEdit.text(),
            ruleset_value=str(self.rulesetCombo.currentData() or RULESET_FILTER_ANY),
            result_value=str(self.resultCombo.currentData() or RESULT_FILTER_ANY),
            source_value=str(self.sourceCombo.currentData() or SOURCE_FILTER_ANY),
            replay_value=str(self.replayCombo.currentData() or REPLAY_FILTER_ANY),
            seed_text=self.seedEdit.text(),
            start_date=start,
            end_date=end,
        )

    def clearFilters(self) -> None:
        """Reset every filter control and reload the first page. Nothing else moves."""

        widgets = (
            self.searchEdit,
            self.seedEdit,
            self.rulesetCombo,
            self.resultCombo,
            self.sourceCombo,
            self.replayCombo,
            self.fromCheck,
            self.toCheck,
        )
        blocked = [widget.blockSignals(True) for widget in widgets]
        try:
            self.searchEdit.clear()
            self.seedEdit.clear()
            for combo in (
                self.rulesetCombo,
                self.resultCombo,
                self.sourceCombo,
                self.replayCombo,
            ):
                combo.setCurrentIndex(0)
            self.fromCheck.setChecked(False)
            self.toCheck.setChecked(False)
        finally:
            for widget, previous in zip(widgets, blocked, strict=True):
                widget.blockSignals(previous)
        self.fromDate.setEnabled(False)
        self.toDate.setEnabled(False)
        self.seedEdit.setToolTip("")
        self._applyFilters()

    # -- selection -----------------------------------------------------

    @Slot(QModelIndex, QModelIndex)
    def _onRowChanged(self, current: QModelIndex, _previous: QModelIndex) -> None:
        row = self.model.rowAt(current.row()) if current.isValid() else None
        if row is None:
            self._clearSelection()
            return
        self._selected_location = row.location_id
        self._selected_replay_state = row.replay_state
        self._selected_seed = row.seed
        self.looseLabel.setVisible(is_non_durable(row))
        self._updateActionState()
        self._detail_generation += 1
        self.detailPane.showMessage(
            "Loading match details (waiting for the history refresh to finish)…"
            if self._refreshing and not self._persistent
            else "Loading match details…"
        )
        self.detailRequested.emit(row.location_id, self._detail_generation)

    def _clearSelection(self) -> None:
        self._selected_location = None
        self._selected_replay_state = None
        self._selected_seed = None
        self._detail_generation += 1
        self.looseLabel.setVisible(False)
        self._updateActionState()
        self.detailPane.showMessage("Select a match to see its details.")

    # -- replay actions (Phase 7D): Open Replay / Copy Seed -------------

    def _updateActionState(self) -> None:
        """Re-derive both action buttons from the current selection alone.

        Called on every selection change and again when a pending Open
        Replay request completes, since the completion must not leave the
        button disabled forever if the user has since selected a different,
        independently eligible row.
        """

        has_selection = self._selected_location is not None and not self._shutdown_started
        can_open = (
            has_selection
            and not self._open_pending
            and self._selected_replay_state is not None
            and open_replay_enabled(self._selected_replay_state)
        )
        self.openReplayButton.setEnabled(can_open)
        self.copySeedButton.setEnabled(has_selection and copy_seed_enabled(self._selected_seed))
        self.copySeedButton.setToolTip(
            COPY_SEED_TOOLTIP if has_selection and copy_seed_enabled(self._selected_seed)
            else "Select a match with a recorded seed. " + COPY_SEED_TOOLTIP
        )
        if not can_open and not self._open_pending:
            self.openReplayButton.setToolTip(
                "Select a match with an available replay."
                if not has_selection else "This match has no available replay. Refresh after restoring it."
            )
        else:
            self.openReplayButton.setToolTip(OPEN_REPLAY_TOOLTIP)

    @Slot(QModelIndex)
    def _onTableDoubleClicked(self, index: QModelIndex) -> None:
        if not index.isValid():
            return
        self._activateOpenReplay()

    def eventFilter(self, watched: QObject, event: Any) -> bool:
        """Enter/Return on the table activates Open Replay when eligible.

        Scoped to ``self.table`` by only installing this filter there, so a
        filter field's own Enter handling is never touched -- a different
        widget's key events never reach this filter at all.
        """

        if (
            watched is self.table
            and event.type() == QEvent.KeyPress
            and isinstance(event, QKeyEvent)
            and event.key() in (Qt.Key_Return, Qt.Key_Enter)
        ):
            if self.openReplayButton.isEnabled():
                self._activateOpenReplay()
                return True
            return False
        return super().eventFilter(watched, event)

    @Slot()
    def _activateOpenReplay(self) -> None:
        """The one Open Replay entry point shared by the button, Enter, and double-click.

        Commits to resolving/verifying exactly the currently selected
        occurrence. Only one request is ever in flight (Section 11): while
        ``_open_pending`` is set neither the button, Enter, nor a
        double-click can start a second one, which is what makes "duplicate
        clicks" safe without needing per-source debouncing.
        """

        if self._open_pending or self._shutdown_started:
            return
        location = self._selected_location
        if location is None or self._selected_replay_state is None:
            return
        if not open_replay_enabled(self._selected_replay_state):
            return
        self._open_pending = True
        self._open_request_id += 1
        self.openReplayButton.setEnabled(False)
        self.actionStatusLabel.setText(CHECKING_REPLAY_TEXT)
        self.openReplayRequested.emit(location, self._open_request_id)

    @Slot(object)
    def _onReplayResolved(self, result: ReplayOpenResult) -> None:
        if result.request_id != self._open_request_id:
            return  # superseded by a newer request; this answer is stale
        self._open_pending = False
        if self._shutdown_started:
            # The window is already tearing down; a Viewer must never launch
            # behind it, and there is no UI left to update meaningfully.
            return
        self._updateActionState()
        resolution = result.resolution
        if not resolution.available or resolution.path is None:
            if result.location_id == self._selected_location:
                self._selected_replay_state = resolution.state
                self._updateActionState()
            self.actionStatusLabel.setText(describe_replay_open_failure(resolution))
            return
        integrity = result.integrity
        if integrity is not None and integrity.status is ReplayIntegrityStatus.MISMATCH:
            if result.location_id == self._selected_location:
                self._selected_replay_state = ReplayState.INVALID
                self._updateActionState()
            self.actionStatusLabel.setText(REPLAY_NO_LONGER_AVAILABLE_TEXT)
            QMessageBox.warning(self, REPLAY_MISMATCH_TITLE, REPLAY_MISMATCH_BODY)
            return
        if integrity is not None and integrity.status is ReplayIntegrityStatus.UNREADABLE:
            if result.location_id == self._selected_location:
                self._selected_replay_state = ReplayState.INACCESSIBLE
                self._updateActionState()
            self.actionStatusLabel.setText(REPLAY_NO_LONGER_AVAILABLE_TEXT)
            return
        # VERIFIED or UNVERIFIED_LEGACY: reuse the exact existing Viewer
        # handoff (Phase 6 Sec R) rather than any second launch path.
        try:
            open_pygame_client_direct(self._data_root, Path(resolution.path))
        except (FileNotFoundError, OSError) as exc:
            QMessageBox.critical(self, "Replay Launch Failed", str(exc))
            return
        self.actionStatusLabel.setText(REPLAY_OPENED_TEXT)

    @Slot()
    def _onCopySeedClicked(self) -> None:
        seed = self._selected_seed
        if seed is None or self._shutdown_started:
            return
        clipboard = QGuiApplication.clipboard()
        if clipboard is not None:
            clipboard.setText(str(seed))
        self.clipboardStatusLabel.setText(describe_seed_copied(seed))
        self.clipboardStatusLabel.setVisible(True)

    def _restoreSelection(self) -> None:
        """Keep the user on the same occurrence across a refresh where possible."""

        target = self._pending_reselect or self._selected_location
        self._pending_reselect = None
        if target is None:
            return
        position = self.model.positionOf(target)
        if position < 0:
            self._clearSelection()
            return
        self.table.selectRow(position)

    # -- presentation state --------------------------------------------

    def _setRefreshing(self, active: bool) -> None:
        self._refreshing = active
        self.progressBar.setVisible(active)
        self.cancelButton.setVisible(active)
        self.cancelButton.setEnabled(active)
        self.refreshButton.setEnabled(not active and not self._shutdown_started)

    def _updateCounts(self) -> None:
        loaded = self.model.loadedCount
        total = max(self._total, loaded)
        counts = describe_count(loaded, total)
        if loaded == 0:
            if not self._reader_ready and self._refreshing:
                self._showMessage(EMPTY_PREPARING_TITLE, EMPTY_PREPARING_BODY)
            elif self._filters.is_unfiltered:
                self._showMessage(EMPTY_NO_HISTORY_TITLE, EMPTY_NO_HISTORY_BODY)
            else:
                self._showMessage(
                    EMPTY_FILTERED_TITLE, EMPTY_FILTERED_BODY, offer_clear=True
                )
        else:
            self.stack.setCurrentWidget(self.table)
        if not self._refreshing:
            note = self._status_note
            self.statusLabel.setText(f"{note}  {counts}" if note else counts)

    def _showMessage(self, title: str, body: str, *, offer_clear: bool = False) -> None:
        self.messagePage.setMessage(title, body)
        self.messagePage.setClearVisible(offer_clear)
        if offer_clear:
            self.messagePage.connectClear(self.clearFilters)
        self.stack.setCurrentWidget(self.messagePage)

    # -- shutdown ------------------------------------------------------

    def closeEvent(self, event: Any) -> None:
        """Cancel, close the service on the worker thread, then join it.

        Order matters and is the whole reason this is not a one-liner: the
        cancel flag reaches a running scan immediately, the queued
        ``shutdown`` closes SQLite on the thread that opened it, and only then
        does the thread's event loop stop. A local event loop keeps timers and
        painting alive during shutdown; the final join follows completion.
        ``terminate()`` is never used because it would abandon an open
        database connection mid-transaction.
        """

        self.shutdownWorker()
        self.windowClosed.emit()
        event.accept()

    def reject(self) -> None:
        """Escape must take the same worker shutdown path as the Close button."""
        self.close()

    def shutdownWorker(self) -> None:
        if self._shutdown_started:
            return
        self._shutdown_started = True
        self._debounce.stop()
        self.refreshButton.setEnabled(False)
        self.cancelButton.setEnabled(False)
        # A queued Open Replay preflight may still be running; _onReplayResolved
        # checks _shutdown_started and will not launch a Viewer for it, but the
        # button is disabled too so a click cannot start a new one during
        # teardown.
        self.openReplayButton.setEnabled(False)
        self.copySeedButton.setEnabled(False)
        self._generation += 1
        self._detail_generation += 1
        self._reader.requestStop()
        self._worker.requestStop()
        # Keep painting/timers alive while owning threads finish. Shutdown
        # guards reject late DTOs and launches; no running QThread is destroyed.
        # Close the reader first so the writer can checkpoint on last close.
        for thread, shutdown in (
            (self._reader_thread, self.readerShutdownRequested),
            (self._thread, self.shutdownRequested),
        ):
            shutdown.emit()
            if thread.isRunning():
                loop = QEventLoop()
                thread.finished.connect(loop.quit)
                if thread.isRunning():
                    loop.exec(QEventLoop.ExcludeUserInputEvents)
                thread.finished.disconnect(loop.quit)
                thread.wait()


class _MessagePage(QWidget):
    """Empty/error state: a title, an explanation, and at most one action."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.addStretch(1)
        self.titleLabel = QLabel("")
        self.titleLabel.setAlignment(Qt.AlignCenter)
        self.titleLabel.setAccessibleName("History state")
        self.bodyLabel = QLabel("")
        self.bodyLabel.setAlignment(Qt.AlignCenter)
        self.bodyLabel.setWordWrap(True)
        self.clearButton = QPushButton("Clear Filters")
        self.clearButton.setVisible(False)
        row = QHBoxLayout()
        row.addStretch(1)
        row.addWidget(self.clearButton)
        row.addStretch(1)
        layout.addWidget(self.titleLabel)
        layout.addWidget(self.bodyLabel)
        layout.addLayout(row)
        layout.addStretch(1)
        self._connected = False

    def setMessage(self, title: str, body: str) -> None:
        self.titleLabel.setText(title)
        self.bodyLabel.setText(body)

    def setClearVisible(self, visible: bool) -> None:
        self.clearButton.setVisible(visible)

    def connectClear(self, handler: Any) -> None:
        if self._connected:
            return
        self.clearButton.clicked.connect(handler)
        self._connected = True


def _combo(choices: tuple[tuple[str, str], ...], accessible_name: str) -> QComboBox:
    combo = QComboBox()
    for value, label in choices:
        combo.addItem(label, value)
    combo.setAccessibleName(accessible_name)
    return combo


__all__ = [
    "FILTER_DEBOUNCE_MS",
    "DetailResult",
    "OpenResult",
    "PageResult",
    "RefreshResult",
    "ReplayHistoryDetailPane",
    "ReplayHistoryMaintenanceWorker",
    "ReplayHistoryReadWorker",
    "ReplayHistoryTableModel",
    "ReplayHistoryWindow",
    "ReplayOpenResult",
    "WorkerError",
]
