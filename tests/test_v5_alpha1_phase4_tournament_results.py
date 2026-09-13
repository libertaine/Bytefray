"""V5 Alpha 1 Phase 4: Tournament Results, Tournament History, and post-run navigation."""

from __future__ import annotations

import os
from pathlib import Path
from types import SimpleNamespace

import pytest

ARENA = 512
NAMES = {"runner": "Runner Bot", "writer": "Writer Bot", "seeker": "Seeker Bot"}


def _make_app():
    pytest.importorskip("PySide6")
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication

    return QApplication.instance() or QApplication([])


class _Modals:
    """Records every QMessageBox static call so none can block an offscreen run."""

    def __init__(self, monkeypatch) -> None:
        from PySide6.QtWidgets import QMessageBox

        self.calls: list[tuple[str, tuple]] = []
        for name in ("warning", "information", "critical", "question"):
            monkeypatch.setattr(QMessageBox, name, staticmethod(self._recorder(name)))

    def _recorder(self, name):
        def record(*args, **_kwargs):
            self.calls.append((name, args))

        return record

    def of(self, name):
        return [args for kind, args in self.calls if kind == name]


class _Abort(BaseException):
    """Escapes TournamentService's per-match ``except Exception``, like a killed process."""


class _FailSecondMatch:
    def __init__(self, exception: BaseException) -> None:
        from battle_engine.match_service import NativeMatchService

        self._real = NativeMatchService()
        self._exception = exception
        self.calls = 0

    def run(self, request):
        self.calls += 1
        if self.calls == 2:
            raise self._exception
        return self._real.run(request)


class _NullSignal:
    def connect(self, *_args, **_kwargs):
        pass


def _run_tournament(output_dir: Path, match_service=None):
    from battle_engine.builtins import build_agent
    from battle_engine.config import Config
    from battle_engine.match_service import MatchEntrant
    from battle_engine.tournament_service import TournamentRequest, TournamentService

    names = ("runner", "writer", "seeker")
    spacing = ARENA // len(names)
    entrants = tuple(
        MatchEntrant(name, NAMES[name], index * spacing, build_agent(name, index * spacing))
        for index, name in enumerate(names)
    )
    return TournamentService(match_service).run(
        TournamentRequest(
            entrants=entrants,
            config=Config(arena_size=ARENA, instr_per_tick=4),
            rounds=1,
            max_ticks=120,
            output_dir=output_dir,
            seed=7,
        )
    )


def _table_text(table):
    return [
        [table.item(row, column).text() for column in range(table.columnCount())]
        for row in range(table.rowCount())
    ]


def _designer(monkeypatch, tmp_path):
    _make_app()
    monkeypatch.setenv("BYTEFRAY_ROOT", str(tmp_path / "data"))
    from app.agent_designer import AgentDesigner

    return AgentDesigner()


def _fake_tournament_dialog(defaults: list, agent_ids: set[str]):
    from app.services.designer_workflows import agent_identifier

    class _Dialog:
        def __init__(self, rows, default_output, parent=None):
            defaults.append(default_output)
            self._rows = rows
            self._output = default_output
            self.rounds = SimpleNamespace(value=lambda: 1)
            self.seed = SimpleNamespace(value=lambda: 7)

        def exec(self):
            return 1

        def selected_rows(self):
            return tuple(row for row in self._rows if agent_identifier(row) in agent_ids)

        def output_path(self):
            return self._output

    return _Dialog


@pytest.mark.gui
def test_results_dialog_shows_winner_standings_and_matches_from_canonical_artifacts(
    monkeypatch, tmp_path
):
    _make_app()
    modals = _Modals(monkeypatch)
    from app.services.tournament_results import format_score, read_tournament_results
    from app.views.tournament import TournamentResultsDialog

    service_result = _run_tournament(tmp_path / "cup")
    assert [(row.agent_id, row.wins) for row in service_result.standings] == [
        ("seeker", 2),
        ("runner", 0),
        ("writer", 0),
    ]
    dialog = TournamentResultsDialog(read_tournament_results(tmp_path / "cup"))
    try:
        assert dialog.headlineLabel.text() == "Winner: Seeker Bot"
        assert dialog.statusLabel.text() == "Complete: 3 of 3 matches completed."
        assert dialog.rulesetLabel.text() == "Ruleset v1"
        assert dialog.entrantsLabel.text() == "3 (VM)"
        assert dialog.matchesLabel.text() == "3 of 3 matches completed"
        assert dialog.outputFolderLabel.text() == str((tmp_path / "cup").resolve())
        assert dialog.tabs.currentIndex() == 0
        assert dialog.standingsNotice.isHidden()
        assert _table_text(dialog.standingsTable) == [
            [
                str(rank),
                NAMES[row.agent_id],
                row.agent_id,
                str(row.played),
                str(row.wins),
                str(row.losses),
                str(row.ties),
                format_score(row.score_total),
            ]
            for rank, row in zip((1, 2, 2), service_result.standings, strict=True)
        ]
        seeds = [str(match.seed) for match in service_result.matches]
        assert _table_text(dialog.matchesTable) == [
            ["1", "1", "Runner Bot vs Writer Bot", "Tie", seeds[0], "Available"],
            ["2", "1", "Runner Bot vs Seeker Bot", "Seeker Bot won", seeds[1], "Available"],
            ["3", "1", "Writer Bot vs Seeker Bot", "Seeker Bot won", seeds[2], "Available"],
        ]
    finally:
        dialog.deleteLater()
    assert modals.calls == []


@pytest.mark.gui
def test_completed_run_opens_results_and_view_replay_uses_the_designer_viewer_launch(
    monkeypatch, tmp_path
):
    designer = _designer(monkeypatch, tmp_path)
    modals = _Modals(monkeypatch)
    try:
        from app.views.tournament import TournamentResultsDialog

        output = designer.data_root / "runs" / "tournaments" / "cup"
        designer._tournament_output = output
        designer._tournament_state_before = None
        designer._tournament_stderr = ""
        designer._log_target = designer.advanced
        service_result = _run_tournament(output)

        launched = []
        monkeypatch.setattr(
            "app.agent_designer.open_pygame_client_direct",
            lambda root, path: launched.append((root, path)),
        )
        shown = []

        def _drive(dialog):
            shown.append(dialog.headlineLabel.text())
            dialog.tabs.setCurrentIndex(1)
            dialog.matchesTable.selectRow(1)
            assert dialog.viewReplayButton.isEnabled()
            dialog.viewReplayButton.click()
            shown.append(dialog.replayStatusLabel.text())
            return 0

        monkeypatch.setattr(TournamentResultsDialog, "exec", _drive)

        designer._present_tournament_result(0)

        assert shown == ["Winner: Seeker Bot", "Opening replay in Replay Viewer…"]
        expected = (service_result.matches[1].artifact_dir / "replay.jsonl").resolve()
        assert launched == [(designer.data_root, expected)]
    finally:
        designer.deleteLater()
    assert modals.calls == []


@pytest.mark.gui
def test_unavailable_replay_is_explained_and_never_launched(monkeypatch, tmp_path):
    _make_app()
    modals = _Modals(monkeypatch)
    from app.services.tournament_results import read_tournament_results
    from app.views.tournament import TournamentResultsDialog

    service_result = _run_tournament(tmp_path / "cup")
    (service_result.matches[1].artifact_dir / "replay.jsonl").unlink()
    dialog = TournamentResultsDialog(read_tournament_results(tmp_path / "cup"))
    emitted = []
    dialog.openReplayRequested.connect(lambda path: emitted.append(path))
    try:
        assert dialog.matchesTable.item(1, 5).text() == "Replay unavailable"
        dialog.matchesTable.selectRow(1)
        assert not dialog.viewReplayButton.isEnabled()
        assert dialog.replayStatusLabel.text() == "Replay unavailable: The replay file is missing."

        dialog.matchesTable.selectRow(2)
        assert dialog.viewReplayButton.isEnabled()
        (service_result.matches[2].artifact_dir / "replay.jsonl").unlink()
        dialog.viewReplayButton.click()

        assert emitted == []
        assert dialog.matchesTable.item(2, 5).text() == "Replay unavailable"
        assert not dialog.viewReplayButton.isEnabled()
        assert dialog.replayStatusLabel.text() == "Replay unavailable: The replay file is missing."
    finally:
        dialog.deleteLater()
    assert modals.calls == []


@pytest.mark.gui
def test_changed_replay_warns_and_is_not_opened(monkeypatch, tmp_path):
    _make_app()
    modals = _Modals(monkeypatch)
    from app.services.tournament_results import read_tournament_results
    from app.views.tournament import TournamentResultsDialog

    service_result = _run_tournament(tmp_path / "cup")
    dialog = TournamentResultsDialog(read_tournament_results(tmp_path / "cup"))
    emitted = []
    dialog.openReplayRequested.connect(lambda path: emitted.append(path))
    try:
        dialog.matchesTable.selectRow(0)
        with (service_result.matches[0].artifact_dir / "replay.jsonl").open("ab") as stream:
            stream.write(b"\n")
        dialog.viewReplayButton.click()

        assert emitted == []
        assert [args[1] for args in modals.of("warning")] == ["Replay Changed"]
        assert dialog.replayStatusLabel.text() == (
            "Replay unavailable: The replay file has changed since the match was recorded."
        )
        assert not dialog.viewReplayButton.isEnabled()
    finally:
        dialog.deleteLater()
    assert len(modals.calls) == 1


@pytest.mark.gui
def test_stopped_tournament_results_claim_no_winner(monkeypatch, tmp_path):
    _make_app()
    modals = _Modals(monkeypatch)
    from battle_engine.tournament_service import derive_match_seed

    from app.services.tournament_results import read_tournament_results
    from app.views.tournament import TournamentResultsDialog

    with pytest.raises(_Abort):
        _run_tournament(tmp_path / "cup", _FailSecondMatch(_Abort()))
    dialog = TournamentResultsDialog(read_tournament_results(tmp_path / "cup"))
    try:
        assert dialog.headlineLabel.text() == "No winner: the tournament did not finish."
        assert dialog.entrantsLabel.text() == "Not recorded (VM; the tournament did not finish)"
        assert not dialog.standingsNotice.isHidden()
        assert dialog.standingsTable.rowCount() == 0
        assert dialog.tabs.currentIndex() == 1
        seed = str(derive_match_seed(7, 1, "runner", "writer"))
        assert _table_text(dialog.matchesTable) == [
            ["1", "1", "Runner Bot vs Writer Bot", "Tie", seed, "Available"]
        ]
    finally:
        dialog.deleteLater()
    assert modals.calls == []


@pytest.mark.gui
def test_run_that_records_nothing_never_presents_earlier_results(monkeypatch, tmp_path):
    designer = _designer(monkeypatch, tmp_path)
    modals = _Modals(monkeypatch)
    try:
        from app.services.tournament_results import tournament_state_signature

        output = designer.data_root / "runs" / "tournaments" / "cup"
        _run_tournament(output)
        constructed = []
        monkeypatch.setattr(
            "app.agent_designer.TournamentResultsDialog",
            lambda *args, **kwargs: constructed.append(args),
        )
        designer._log_target = designer.advanced
        designer._tournament_output = output
        designer._tournament_state_before = tournament_state_signature(output)
        designer._tournament_stderr = (
            "ERROR: Existing tournament state does not match this request.\n"
        )

        designer._present_tournament_result(2)

        warnings = modals.of("warning")
        assert constructed == []
        assert [args[1] for args in warnings] == ["Tournament Did Not Run"]
        assert "Existing tournament state does not match this request." in warnings[0][2]
        assert "already contains results from an earlier tournament" in warnings[0][2]

        designer._tournament_output = designer.data_root / "runs" / "tournaments" / "never"
        designer._tournament_state_before = None
        designer._tournament_stderr = "ERROR: Agent 'ghost' is not an executable agent.\n"

        designer._present_tournament_result(2)

        warnings = modals.of("warning")
        assert constructed == []
        assert len(warnings) == 2
        assert "Agent 'ghost'" in warnings[1][2]
        assert "earlier tournament" not in warnings[1][2]
    finally:
        designer.deleteLater()
    assert len(modals.calls) == 2


@pytest.mark.gui
def test_each_tournament_launch_proposes_a_fresh_output_folder(monkeypatch, tmp_path):
    designer = _designer(monkeypatch, tmp_path)
    modals = _Modals(monkeypatch)
    try:
        from app.services.tournament_results import tournaments_root

        defaults: list[Path] = []
        commands = []

        class _Proc:
            def start(self):
                pass

        def _start_process(command, env, working_directory, *, label):
            commands.append((command, label))
            return _Proc()

        monkeypatch.setattr(
            "app.agent_designer.TournamentDialog",
            _fake_tournament_dialog(defaults, {"runner", "writer"}),
        )
        monkeypatch.setattr(designer, "_start_process", _start_process)

        designer._on_tournament()
        designer._on_tournament()

        assert defaults[0] != defaults[1]
        assert {path.parent for path in defaults} == {tournaments_root(designer.data_root)}
        assert designer._tournament_output == defaults[1]
        assert designer._tournament_state_before is None
        assert [label for _, label in commands] == ["Tournament", "Tournament"]
        assert commands[1][0][-2:] == ["--output", str(defaults[1])]
    finally:
        designer.deleteLater()
    assert modals.calls == []


@pytest.mark.gui
def test_output_folder_commands_open_the_tournament_folder(monkeypatch, tmp_path):
    designer = _designer(monkeypatch, tmp_path)
    modals = _Modals(monkeypatch)
    try:
        from PySide6.QtGui import QDesktopServices

        from app.services.tournament_results import read_tournament_results
        from app.views.tournament import TournamentResultsDialog

        opened = []
        monkeypatch.setattr(
            QDesktopServices,
            "openUrl",
            staticmethod(lambda url: opened.append(Path(url.toLocalFile()).resolve())),
        )
        output = designer.data_root / "runs" / "tournaments" / "cup"
        _run_tournament(output)
        designer._tournament_output = output

        designer.openOutputFolderAction.trigger()
        dialog = TournamentResultsDialog(read_tournament_results(output))
        dialog.openFolderButton.click()
        dialog.deleteLater()

        assert opened == [output.resolve(), output.resolve()]
    finally:
        designer.deleteLater()
    assert modals.calls == []


@pytest.mark.gui
def test_tournament_history_empty_state_explains_how_results_are_created(monkeypatch, tmp_path):
    _make_app()
    modals = _Modals(monkeypatch)
    from app.views.tournament import TournamentHistoryDialog

    dialog = TournamentHistoryDialog(tmp_path / "data")
    try:
        assert dialog.emptyLabel.text() == (
            "No tournament results have been recorded yet. Run a tournament to create results."
        )
        assert not dialog.emptyLabel.isHidden()
        assert dialog.table.isHidden()
        assert not dialog.viewResultsButton.isEnabled()
    finally:
        dialog.deleteLater()
    assert modals.calls == []


@pytest.mark.gui
def test_tournament_history_reopens_saved_results_and_their_replays(monkeypatch, tmp_path):
    _make_app()
    modals = _Modals(monkeypatch)
    from app.services.tournament_results import tournaments_root
    from app.views.tournament import TournamentHistoryDialog, TournamentResultsDialog

    data_root = tmp_path / "data"
    root = tournaments_root(data_root)
    finished = _run_tournament(root / "finished")
    with pytest.raises(_Abort):
        _run_tournament(root / "stopped", _FailSecondMatch(_Abort()))
    (root / "damaged").mkdir()
    (root / "damaged" / "tournament.json").write_text("{", encoding="utf-8")
    os.utime(root / "finished" / "tournament.json", (3_000_000, 3_000_000))
    os.utime(root / "stopped" / "tournament.json", (2_000_000, 2_000_000))
    os.utime(root / "damaged" / "tournament.json", (1_000_000, 1_000_000))

    shown = []

    def _drive(dialog):
        shown.append(dialog.headlineLabel.text())
        dialog.matchesTable.selectRow(2)
        dialog.viewReplayButton.click()
        return 0

    monkeypatch.setattr(TournamentResultsDialog, "exec", _drive)
    dialog = TournamentHistoryDialog(data_root)
    emitted = []
    dialog.openReplayRequested.connect(lambda path: emitted.append(path))
    try:
        assert [row[1:] for row in _table_text(dialog.table)] == [
            ["Complete", "seeker", "seeker, runner, writer", "3 of 3", "finished"],
            ["Did not finish", "—", "runner, writer", "1 of 1", "stopped"],
            ["Unreadable", "—", "—", "—", "damaged"],
        ]
        assert dialog.emptyLabel.isHidden()
        assert dialog.viewResultsButton.isEnabled()

        dialog.viewResultsButton.click()
        assert shown == ["Winner: Seeker Bot"]
        assert emitted == [(finished.matches[2].artifact_dir / "replay.jsonl").resolve()]

        dialog.table.selectRow(1)
        dialog.viewResultsButton.click()
        assert shown[-1] == "No winner: the tournament did not finish."
        assert len(emitted) == 1

        dialog.table.selectRow(2)
        assert not dialog.viewResultsButton.isEnabled()
        assert dialog.statusLabel.text().startswith(
            "These results cannot be shown: The tournament results file could not be read"
        )
    finally:
        dialog.deleteLater()
    assert modals.calls == []


@pytest.mark.gui
def test_tournament_history_opens_a_tournament_saved_elsewhere(monkeypatch, tmp_path):
    _make_app()
    modals = _Modals(monkeypatch)
    from app.views import tournament as view

    custom = tmp_path / "elsewhere"
    _run_tournament(custom)
    choices = [str(custom), str(tmp_path)]
    monkeypatch.setattr(
        view.QFileDialog,
        "getExistingDirectory",
        staticmethod(lambda *args, **kwargs: choices.pop(0)),
    )
    shown = []
    monkeypatch.setattr(
        view.TournamentResultsDialog,
        "exec",
        lambda dialog: shown.append(dialog.headlineLabel.text()) or 0,
    )
    dialog = view.TournamentHistoryDialog(tmp_path / "data")
    try:
        dialog.browseButton.click()
        assert shown == ["Winner: Seeker Bot"]

        dialog.browseButton.click()
        assert shown == ["Winner: Seeker Bot"]
        assert dialog.statusLabel.text().startswith("No tournament results were found in")
    finally:
        dialog.deleteLater()
    assert modals.calls == []


@pytest.mark.gui
def test_history_menu_contains_tournament_history_with_preserved_wiring(monkeypatch, tmp_path):
    designer = _designer(monkeypatch, tmp_path)
    try:
        tools = next(
            action.menu()
            for action in designer.menuBar().actions()
            if action.menu() is not None and action.menu().title() == "Tools"
        )
        history = next(
            action.menu()
            for action in designer.menuBar().actions()
            if action.menu() is not None and action.menu().title() == "History"
        )
        assert [action.text() for action in tools.actions()] == ["Run Tournament…"]
        actions = history.actions()
        assert [action.text() for action in actions] == [
            "Replay History…",
            "Tournament History…",
            "Evaluation History…",
        ]

        created = []

        class _History:
            def __init__(self, data_root, parent=None):
                created.append(data_root)
                self.openReplayRequested = SimpleNamespace(connect=created.append)

            def exec(self):
                created.append("exec")
                return 0

        monkeypatch.setattr("app.agent_designer.TournamentHistoryDialog", _History)
        next(action for action in actions if action.text() == "Tournament History…").trigger()

        assert created == [designer.data_root, designer._on_evaluation_open_replay, "exec"]
    finally:
        designer.deleteLater()


@pytest.mark.gui
def test_stopping_a_tournament_is_logged_as_a_tournament(monkeypatch, tmp_path):
    designer = _designer(monkeypatch, tmp_path)
    try:
        logged = []
        monkeypatch.setattr(designer.advanced, "appendLog", lambda text: logged.append(text))
        designer._active_workflow = "tournament"
        designer._log_target = designer.advanced

        designer._on_stop_run()

        assert logged == ["[Tournament] stopped.\n"]
    finally:
        designer.deleteLater()


@pytest.mark.gui
def test_designer_runs_a_real_tournament_and_opens_its_results(monkeypatch, tmp_path):
    designer = _designer(monkeypatch, tmp_path)
    modals = _Modals(monkeypatch)
    from PySide6.QtCore import QEventLoop, QTimer

    from app.services.tournament_results import (
        REPLAY_READY,
        check_match_replay,
        read_tournament_results,
        tournaments_root,
    )

    shown = []

    class _Results:
        def __init__(self, results, parent=None):
            shown.append(results)
            self.openReplayRequested = _NullSignal()

        def exec(self):
            return 0

    monkeypatch.setattr(
        "app.agent_designer.TournamentDialog", _fake_tournament_dialog([], {"runner", "writer"})
    )
    monkeypatch.setattr("app.agent_designer.TournamentResultsDialog", _Results)
    loop = QEventLoop()
    timer = QTimer()
    timer.setSingleShot(True)
    timer.timeout.connect(loop.quit)
    finished = []

    def _on_finished(*_args):
        finished.append(True)
        loop.quit()

    try:
        designer._on_tournament()
        process = designer._proc
        assert process is not None
        process.finished.connect(_on_finished)
        timer.start(120_000)
        loop.exec()

        assert finished, "the tournament subprocess did not finish within 120 seconds"
        assert len(shown) == 1
        results = shown[0]
        assert results == read_tournament_results(designer._tournament_output)
        assert results.output_dir.parent == tournaments_root(designer.data_root)
        assert results.finished
        assert results.completed_count == 1
        assert {row.agent_id for row in results.standings} == {"runner", "writer"}
        assert check_match_replay(results.matches[0]) == REPLAY_READY
    finally:
        timer.stop()
        designer._dispose_process()
        designer.deleteLater()
    assert modals.calls == []
