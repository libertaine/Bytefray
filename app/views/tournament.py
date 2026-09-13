"""Tournament dialogs for the Designer: launch, results, and history."""

from __future__ import annotations

import time
from pathlib import Path

from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from app.services.tournament_results import (
    NO_TOURNAMENT_HISTORY_TEXT,
    REPLAY_CHANGED,
    REPLAY_CHANGED_BODY,
    REPLAY_CHANGED_TEXT,
    REPLAY_CHANGED_TITLE,
    REPLAY_MISSING_TEXT,
    REPLAY_READY,
    REPLAY_UNAVAILABLE_TEXT,
    MatchRow,
    TournamentHistoryEntry,
    TournamentResults,
    TournamentResultsError,
    check_match_replay,
    discover_tournaments,
    entrants_text,
    format_score,
    headline_text,
    history_status_text,
    history_top_standing_text,
    match_detail_lines,
    match_result_text,
    match_title,
    matches_text,
    read_tournament_results,
    replay_column_text,
    ruleset_text,
    status_text,
    tournaments_root,
)

STANDING_COLUMNS = ("Rank", "Entrant", "Agent ID", "Played", "Wins", "Losses", "Ties", "Score")
MATCH_COLUMNS = ("#", "Round", "Match", "Result", "Seed", "Replay")
HISTORY_COLUMNS = (
    "Last Updated",
    "Status",
    "Top Standing",
    "Entrants",
    "Matches Completed",
    "Folder",
)
SELECT_MATCH_TEXT = "Select a match to view its replay."
OPENING_REPLAY_TEXT = "Opening replay in Replay Viewer…"
_MATCH_REPLAY_COLUMN = MATCH_COLUMNS.index("Replay")


class TournamentDialog(QDialog):
    def __init__(self, rows, default_output: Path, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Run Tournament")
        self._rows = tuple(rows)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Select at least two agents from one runtime kind."))
        self.agents = QListWidget()
        self.agents.setSelectionMode(QAbstractItemView.ExtendedSelection)
        for index, row in enumerate(self._rows):
            item = QListWidgetItem(f"{row.name} ({row.meta.get('kind', 'vm')})")
            item.setData(Qt.UserRole, index)
            self.agents.addItem(item)
        layout.addWidget(self.agents)

        form = QFormLayout()
        self.rounds = QSpinBox()
        self.rounds.setRange(1, 1000)
        self.rounds.setValue(1)
        self.seed = QSpinBox()
        self.seed.setRange(0, 2_147_483_647)
        self.seed.setValue(1337)
        output_row = QHBoxLayout()
        self.output = QLineEdit(str(default_output))
        choose = QPushButton("Choose…")
        choose.clicked.connect(self._choose_output)
        output_row.addWidget(self.output, 1)
        output_row.addWidget(choose)
        form.addRow("Rounds", self.rounds)
        form.addRow("Seed", self.seed)
        form.addRow("Output", output_row)
        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText("Run")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.resize(560, 430)

    def selected_rows(self):
        return tuple(self._rows[item.data(Qt.UserRole)] for item in self.agents.selectedItems())

    def output_path(self) -> Path:
        return Path(self.output.text())

    def _choose_output(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Tournament Output", self.output.text())
        if path:
            self.output.setText(path)


def _read_only_table(columns: tuple[str, ...]) -> QTableWidget:
    table = QTableWidget(0, len(columns))
    table.setHorizontalHeaderLabels(list(columns))
    table.setEditTriggers(QAbstractItemView.NoEditTriggers)
    table.setSelectionBehavior(QAbstractItemView.SelectRows)
    table.setSelectionMode(QAbstractItemView.SingleSelection)
    table.verticalHeader().setVisible(False)
    table.setAlternatingRowColors(True)
    table.horizontalHeader().setStretchLastSection(True)
    return table


def _cell(text: str, *, numeric: bool = False) -> QTableWidgetItem:
    item = QTableWidgetItem(text)
    item.setToolTip(text)
    if numeric:
        item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
    return item


def _selected_row(table: QTableWidget) -> int | None:
    rows = {item.row() for item in table.selectedItems()}
    return rows.pop() if len(rows) == 1 else None


class TournamentResultsDialog(QDialog):
    """Read-only results for one tournament; replays open through ``openReplayRequested``."""

    openReplayRequested = Signal(Path)

    def __init__(self, results: TournamentResults, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._results = results
        self._replay_problems: dict[int, str] = {}
        self.setWindowTitle("Tournament Results")
        self.resize(860, 620)
        layout = QVBoxLayout(self)

        self.headlineLabel = QLabel(headline_text(results))
        font = self.headlineLabel.font()
        if font.pointSizeF() > 0:
            font.setPointSizeF(font.pointSizeF() * 1.4)
        font.setBold(True)
        self.headlineLabel.setFont(font)
        self.headlineLabel.setWordWrap(True)
        self.headlineLabel.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(self.headlineLabel)

        self.statusLabel = QLabel(status_text(results))
        self.statusLabel.setWordWrap(True)
        layout.addWidget(self.statusLabel)

        facts = QFormLayout()
        self.rulesetLabel = QLabel(ruleset_text(results))
        self.entrantsLabel = QLabel(entrants_text(results))
        self.matchesLabel = QLabel(matches_text(results))
        facts.addRow("Ruleset:", self.rulesetLabel)
        facts.addRow("Entrants:", self.entrantsLabel)
        facts.addRow("Matches:", self.matchesLabel)
        folder_row = QHBoxLayout()
        self.outputFolderLabel = QLabel(str(results.output_dir))
        self.outputFolderLabel.setWordWrap(True)
        self.outputFolderLabel.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.openFolderButton = QPushButton("Open Output Folder")
        folder_row.addWidget(self.outputFolderLabel, 1)
        folder_row.addWidget(self.openFolderButton)
        facts.addRow("Output folder:", folder_row)
        layout.addLayout(facts)

        self.tabs = QTabWidget()
        standings_page = QWidget()
        standings_layout = QVBoxLayout(standings_page)
        self.standingsNotice = QLabel(
            "Final standings were not recorded because the tournament did not finish. "
            "Matches that were played are listed under Matches."
        )
        self.standingsNotice.setWordWrap(True)
        self.standingsNotice.setVisible(not results.finished)
        self.standingsTable = _read_only_table(STANDING_COLUMNS)
        standings_layout.addWidget(self.standingsNotice)
        standings_layout.addWidget(self.standingsTable, 1)
        self.tabs.addTab(standings_page, "Standings")

        matches_page = QWidget()
        matches_layout = QVBoxLayout(matches_page)
        self.matchesTable = _read_only_table(MATCH_COLUMNS)
        self.matchDetail = QPlainTextEdit()
        self.matchDetail.setReadOnly(True)
        replay_row = QHBoxLayout()
        self.viewReplayButton = QPushButton("View Replay")
        self.viewReplayButton.setEnabled(False)
        self.replayStatusLabel = QLabel(SELECT_MATCH_TEXT)
        self.replayStatusLabel.setWordWrap(True)
        replay_row.addWidget(self.viewReplayButton)
        replay_row.addWidget(self.replayStatusLabel, 1)
        matches_layout.addWidget(self.matchesTable, 2)
        matches_layout.addWidget(self.matchDetail, 1)
        matches_layout.addLayout(replay_row)
        self.tabs.addTab(matches_page, "Matches")
        layout.addWidget(self.tabs, 1)
        if not results.finished:
            self.tabs.setCurrentIndex(1)

        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self._populate_standings()
        self._populate_matches()
        self.matchesTable.itemSelectionChanged.connect(self._on_match_selection_changed)
        self.matchesTable.cellDoubleClicked.connect(self._on_match_double_clicked)
        self.viewReplayButton.clicked.connect(self._on_view_replay)
        self.openFolderButton.clicked.connect(self._on_open_output_folder)

    def _populate_standings(self) -> None:
        table = self.standingsTable
        table.setRowCount(len(self._results.standings))
        for index, row in enumerate(self._results.standings):
            values = (
                (str(row.rank), True),
                (row.name, False),
                (row.agent_id, False),
                (str(row.played), True),
                (str(row.wins), True),
                (str(row.losses), True),
                (str(row.ties), True),
                (format_score(row.score_total), True),
            )
            for column, (text, numeric) in enumerate(values):
                table.setItem(index, column, _cell(text, numeric=numeric))
        table.resizeColumnsToContents()

    def _populate_matches(self) -> None:
        table = self.matchesTable
        table.setRowCount(len(self._results.matches))
        for index, match in enumerate(self._results.matches):
            values = (
                (str(match.number), True),
                (str(match.round_number), True),
                (match_title(match), False),
                (match_result_text(match), False),
                (str(match.seed), True),
                (replay_column_text(match), False),
            )
            for column, (text, numeric) in enumerate(values):
                table.setItem(index, column, _cell(text, numeric=numeric))
        table.resizeColumnsToContents()

    def _selected_match(self) -> MatchRow | None:
        index = _selected_row(self.matchesTable)
        return None if index is None else self._results.matches[index]

    def _replay_problem(self, match: MatchRow) -> str | None:
        if match.number in self._replay_problems:
            return self._replay_problems[match.number]
        if match.replay_path is None:
            return match.replay_unavailable_reason or REPLAY_MISSING_TEXT
        return None

    def _on_match_selection_changed(self) -> None:
        match = self._selected_match()
        if match is None:
            self.matchDetail.setPlainText("")
            self.viewReplayButton.setEnabled(False)
            self.viewReplayButton.setToolTip("")
            self.replayStatusLabel.setText(SELECT_MATCH_TEXT)
            return
        self.matchDetail.setPlainText("\n".join(match_detail_lines(match)))
        self._update_replay_action(match)

    def _update_replay_action(self, match: MatchRow) -> None:
        problem = self._replay_problem(match)
        self.viewReplayButton.setEnabled(problem is None)
        if problem is None:
            self.viewReplayButton.setToolTip("Open this match's replay in Replay Viewer.")
            self.replayStatusLabel.setText("")
            return
        text = f"{REPLAY_UNAVAILABLE_TEXT}: {problem}"
        self.viewReplayButton.setToolTip(text)
        self.replayStatusLabel.setText(text)

    def _on_match_double_clicked(self, _row: int, _column: int) -> None:
        if self.viewReplayButton.isEnabled():
            self._on_view_replay()

    def _on_view_replay(self) -> None:
        match = self._selected_match()
        if match is None or match.replay_path is None or self._replay_problem(match) is not None:
            return
        state = check_match_replay(match)
        if state == REPLAY_READY:
            self.replayStatusLabel.setText(OPENING_REPLAY_TEXT)
            self.openReplayRequested.emit(match.replay_path)
            return
        if state == REPLAY_CHANGED:
            self._mark_replay_problem(match, REPLAY_CHANGED_TEXT)
            QMessageBox.warning(self, REPLAY_CHANGED_TITLE, REPLAY_CHANGED_BODY)
            return
        self._mark_replay_problem(match, REPLAY_MISSING_TEXT)

    def _mark_replay_problem(self, match: MatchRow, reason: str) -> None:
        self._replay_problems[match.number] = reason
        item = self.matchesTable.item(match.number - 1, _MATCH_REPLAY_COLUMN)
        if item is not None:
            item.setText(REPLAY_UNAVAILABLE_TEXT)
            item.setToolTip(reason)
        self._update_replay_action(match)

    def _on_open_output_folder(self) -> None:
        directory = self._results.output_dir
        if not directory.is_dir():
            self.outputFolderLabel.setText(f"{directory} (this folder no longer exists)")
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(directory)))


class TournamentHistoryDialog(QDialog):
    """Tournaments saved beneath ``runs/tournaments``, each reopening its results."""

    openReplayRequested = Signal(Path)

    def __init__(self, data_root: Path, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._data_root = Path(data_root)
        self._entries: tuple[TournamentHistoryEntry, ...] = ()
        self.setWindowTitle("Tournament History")
        self.resize(900, 480)
        layout = QVBoxLayout(self)

        self.locationLabel = QLabel(
            f"Tournaments saved in: {tournaments_root(self._data_root)}"
        )
        self.locationLabel.setWordWrap(True)
        self.locationLabel.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(self.locationLabel)

        self.emptyLabel = QLabel(NO_TOURNAMENT_HISTORY_TEXT)
        self.emptyLabel.setWordWrap(True)
        layout.addWidget(self.emptyLabel)

        self.table = _read_only_table(HISTORY_COLUMNS)
        layout.addWidget(self.table, 1)

        self.statusLabel = QLabel("")
        self.statusLabel.setWordWrap(True)
        layout.addWidget(self.statusLabel)

        actions = QHBoxLayout()
        self.viewResultsButton = QPushButton("View Results")
        self.viewResultsButton.setEnabled(False)
        self.browseButton = QPushButton("Open Tournament Folder…")
        self.browseButton.setToolTip("View results from a tournament saved in another folder.")
        self.refreshButton = QPushButton("Refresh")
        actions.addWidget(self.viewResultsButton)
        actions.addWidget(self.browseButton)
        actions.addStretch(1)
        actions.addWidget(self.refreshButton)
        layout.addLayout(actions)

        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        self.table.cellDoubleClicked.connect(self._on_row_double_clicked)
        self.viewResultsButton.clicked.connect(self._on_view_results)
        self.browseButton.clicked.connect(self._on_browse)
        self.refreshButton.clicked.connect(self.refresh)
        self.refresh()

    def refresh(self) -> None:
        self._entries = discover_tournaments(self._data_root)
        self.table.clearSelection()
        self.table.setRowCount(len(self._entries))
        for index, entry in enumerate(self._entries):
            values = (
                time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(entry.updated_at)),
                history_status_text(entry),
                history_top_standing_text(entry),
                ", ".join(entry.entrant_ids) or "—",
                "—" if entry.error else f"{entry.completed_count} of {entry.match_count}",
                entry.output_dir.name,
            )
            for column, text in enumerate(values):
                self.table.setItem(index, column, _cell(text))
        self.table.resizeColumnsToContents()
        has_entries = bool(self._entries)
        self.emptyLabel.setVisible(not has_entries)
        self.table.setVisible(has_entries)
        self.statusLabel.setText("")
        self.viewResultsButton.setEnabled(False)
        if has_entries:
            self.table.selectRow(0)

    def _selected_entry(self) -> TournamentHistoryEntry | None:
        index = _selected_row(self.table)
        return None if index is None else self._entries[index]

    def _on_selection_changed(self) -> None:
        entry = self._selected_entry()
        if entry is None:
            self.viewResultsButton.setEnabled(False)
            self.statusLabel.setText("")
            return
        self.viewResultsButton.setEnabled(entry.error is None)
        self.statusLabel.setText(
            "" if entry.error is None else f"These results cannot be shown: {entry.error}"
        )

    def _on_row_double_clicked(self, _row: int, _column: int) -> None:
        if self.viewResultsButton.isEnabled():
            self._on_view_results()

    def _on_view_results(self) -> None:
        entry = self._selected_entry()
        if entry is None or entry.error is not None:
            return
        self._show_results(entry.output_dir)

    def _on_browse(self) -> None:
        root = tournaments_root(self._data_root)
        start = root if root.is_dir() else self._data_root
        path = QFileDialog.getExistingDirectory(self, "Open Tournament Folder", str(start))
        if path:
            self._show_results(Path(path))

    def _show_results(self, directory: Path) -> None:
        try:
            results = read_tournament_results(directory)
        except TournamentResultsError as exc:
            self.statusLabel.setText(str(exc))
            return
        self.statusLabel.setText("")
        dialog = TournamentResultsDialog(results, parent=self)
        dialog.openReplayRequested.connect(self.openReplayRequested.emit)
        dialog.exec()


__all__ = ["TournamentDialog", "TournamentHistoryDialog", "TournamentResultsDialog"]
