"""Tournament Results/History presentation, derived from real ``TournamentService`` runs."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from battle_engine.builtins import build_agent
from battle_engine.config import Config
from battle_engine.core import NOP, enc
from battle_engine.match_service import MatchEntrant, NativeMatchService
from battle_engine.result_model import read_result
from battle_engine.tournament_service import (
    TournamentConfigurationError,
    TournamentRequest,
    TournamentService,
)

from app.services.tournament_results import (
    NOT_COMPLETED_REPLAY_TEXT,
    REPLAY_CHANGED,
    REPLAY_MISSING,
    REPLAY_READY,
    TournamentResultsError,
    check_match_replay,
    describe_tournament_not_run,
    discover_tournaments,
    headline_text,
    history_status_text,
    history_top_standing_text,
    match_result_text,
    new_tournament_output_directory,
    read_tournament_results,
    replay_column_text,
    status_text,
    tournament_state_signature,
    tournaments_root,
)

ARENA = 512


class _Abort(BaseException):
    """Escapes TournamentService's per-match ``except Exception``, like a killed process."""


class _FailSecondMatch:
    def __init__(self, exception: BaseException) -> None:
        self._real = NativeMatchService()
        self._exception = exception
        self.calls = 0

    def run(self, request):
        self.calls += 1
        if self.calls == 2:
            raise self._exception
        return self._real.run(request)


def _builtin_entrants(*names: str) -> tuple[MatchEntrant, ...]:
    spacing = ARENA // len(names)
    return tuple(
        MatchEntrant(name, f"{name.title()} Bot", index * spacing, build_agent(name, index * spacing))
        for index, name in enumerate(names)
    )


def _request(output_dir: Path, **changes) -> TournamentRequest:
    values = {
        "entrants": _builtin_entrants("runner", "writer", "seeker"),
        "config": Config(arena_size=ARENA, instr_per_tick=4),
        "rounds": 1,
        "max_ticks": 120,
        "output_dir": output_dir,
        "seed": 7,
    }
    values.update(changes)
    return TournamentRequest(**values)


def test_finished_tournament_presents_canonical_winner_standings_and_matches(tmp_path):
    service_result = TournamentService().run(_request(tmp_path))
    assert [(row.agent_id, row.wins) for row in service_result.standings] == [
        ("seeker", 2),
        ("runner", 0),
        ("writer", 0),
    ]

    results = read_tournament_results(tmp_path)

    assert results.finished
    assert results.tournament_id == service_result.tournament_id
    assert [
        (row.agent_id, row.played, row.wins, row.losses, row.ties, row.score_total)
        for row in results.standings
    ] == [
        (row.agent_id, row.played, row.wins, row.losses, row.ties, row.score_total)
        for row in service_result.standings
    ]
    assert [row.name for row in results.standings] == ["Seeker Bot", "Runner Bot", "Writer Bot"]
    assert [row.name for row in results.leaders] == ["Seeker Bot"]
    assert headline_text(results) == "Winner: Seeker Bot"
    assert status_text(results) == "Complete: 3 of 3 matches completed."
    assert results.ruleset_ids == ("bytefray-rules-1",)
    assert [
        (row.number, row.round_number, row.entrant_ids, row.seed, row.status)
        for row in results.matches
    ] == [
        (number, match.round_number, match.entrant_ids, match.seed, match.status)
        for number, match in enumerate(service_result.matches, start=1)
    ]
    for row, match in zip(results.matches, service_result.matches, strict=True):
        envelope = read_result(match.artifact_dir / "result.json")
        assert row.winner == envelope.winner
        assert row.replay_path == (match.artifact_dir / "replay.jsonl").resolve()
        assert row.replay_sha256 == envelope.replay.sha256
        assert check_match_replay(row) == REPLAY_READY
    assert [match_result_text(row) for row in results.matches] == [
        "Tie",
        "Seeker Bot won",
        "Seeker Bot won",
    ]


def test_entrants_level_on_wins_and_score_share_a_rank(tmp_path):
    service_result = TournamentService().run(_request(tmp_path))
    runner, writer = service_result.standings[1], service_result.standings[2]
    assert (runner.wins, runner.score_total) == (writer.wins, writer.score_total)

    results = read_tournament_results(tmp_path)

    assert [(row.rank, row.agent_id) for row in results.standings] == [
        (1, "seeker"),
        (2, "runner"),
        (2, "writer"),
    ]


def test_top_tie_is_reported_as_a_tie_not_resolved_by_agent_id(tmp_path):
    entrants = tuple(
        MatchEntrant(chr(65 + index), f"Agent {index}", index * 32, enc(NOP)) for index in range(3)
    )
    service_result = TournamentService().run(
        _request(
            tmp_path,
            entrants=entrants,
            config=Config(arena_size=128, instr_per_tick=1),
            max_ticks=2,
        )
    )
    assert len({(row.wins, row.score_total) for row in service_result.standings}) == 1

    results = read_tournament_results(tmp_path)

    assert [row.rank for row in results.standings] == [1, 1, 1]
    assert headline_text(results) == "Tied for first: Agent 0, Agent 1, Agent 2"


def test_failed_match_is_listed_and_the_top_standing_is_called_a_leader(tmp_path):
    service_result = TournamentService(_FailSecondMatch(RuntimeError("backend broke"))).run(
        _request(tmp_path)
    )
    assert [match.status for match in service_result.matches] == [
        "completed",
        "failed",
        "completed",
    ]

    results = read_tournament_results(tmp_path)

    assert results.finished
    assert results.not_completed_count == 1
    failed = results.matches[1]
    assert failed.entrant_ids == ("runner", "seeker")
    assert match_result_text(failed) == "Failed"
    assert failed.error_message == "backend broke"
    assert failed.replay_path is None
    assert failed.replay_unavailable_reason == NOT_COMPLETED_REPLAY_TEXT
    assert headline_text(results) == "Leader: Seeker Bot"
    assert status_text(results) == (
        "Finished, but 1 of 3 matches did not complete. Standings count completed matches only."
    )


def test_interrupted_tournament_is_not_presented_as_finished(tmp_path):
    with pytest.raises(_Abort):
        TournamentService(_FailSecondMatch(_Abort())).run(_request(tmp_path))
    state = json.loads((tmp_path / "tournament.json").read_text(encoding="utf-8"))
    assert [match["status"] for match in state["matches"]] == ["completed"]
    assert state["standings"] == []

    results = read_tournament_results(tmp_path)

    assert not results.finished
    assert results.standings == ()
    assert results.leaders == ()
    assert headline_text(results) == "No winner: the tournament did not finish."
    assert status_text(results) == (
        "This tournament stopped after 1 match (1 completed). Final standings were not recorded."
    )
    assert check_match_replay(results.matches[0]) == REPLAY_READY


def test_no_completed_matches_means_no_winner(tmp_path):
    class _AlwaysFails:
        def run(self, request):
            raise RuntimeError("backend broke")

    TournamentService(_AlwaysFails()).run(_request(tmp_path))

    results = read_tournament_results(tmp_path)

    assert results.finished
    assert results.completed_count == 0
    assert results.leaders == ()
    assert results.ruleset_ids == ()
    assert headline_text(results) == "No winner: no matches completed."


def test_missing_and_changed_replays_are_detected_before_opening(tmp_path):
    TournamentService().run(_request(tmp_path))
    first, second, third = read_tournament_results(tmp_path).matches
    second.replay_path.unlink()
    with third.replay_path.open("ab") as stream:
        stream.write(b"\n")

    assert check_match_replay(first) == REPLAY_READY
    assert check_match_replay(second) == REPLAY_MISSING
    assert check_match_replay(third) == REPLAY_CHANGED

    reread = read_tournament_results(tmp_path).matches
    assert reread[1].replay_path is None
    assert reread[1].replay_unavailable_reason == "The replay file is missing."
    assert reread[1].winner == "seeker"
    assert [replay_column_text(row) for row in reread] == [
        "Available",
        "Replay unavailable",
        "Available",
    ]


def test_result_identity_and_replay_reference_are_rechecked_after_results_load(tmp_path):
    TournamentService().run(_request(tmp_path))
    first, second, _ = read_tournament_results(tmp_path).matches
    first_result = json.loads(first.result_path.read_text(encoding="utf-8"))
    first_result["result_id"] = "replaced_result"
    first.result_path.write_text(json.dumps(first_result), encoding="utf-8")

    second_result = json.loads(second.result_path.read_text(encoding="utf-8"))
    second_result["replay"]["filename"] = "../outside.jsonl"
    second.result_path.write_text(json.dumps(second_result), encoding="utf-8")

    assert check_match_replay(first) == REPLAY_CHANGED
    assert check_match_replay(second) == REPLAY_CHANGED


def test_result_file_that_does_not_match_the_tournament_record_is_not_trusted(tmp_path):
    service_result = TournamentService().run(_request(tmp_path))
    first_dir = service_result.matches[0].artifact_dir
    second_dir = service_result.matches[1].artifact_dir
    (second_dir / "result.json").write_bytes((first_dir / "result.json").read_bytes())

    row = read_tournament_results(tmp_path).matches[1]

    assert row.status == "completed"
    assert row.winner is None
    assert match_result_text(row) == "Result unavailable"
    assert row.replay_path is None
    assert row.replay_unavailable_reason == (
        "This match's result file does not match the tournament record."
    )


def test_match_folders_resolve_only_inside_the_tournament_folder(tmp_path):
    TournamentService().run(_request(tmp_path))
    state_path = tmp_path / "tournament.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    recorded = state["matches"][0]["artifact_dir"]
    state["matches"][0]["artifact_dir"] = recorded.replace("/", "\\")
    state["matches"][1]["artifact_dir"] = "../outside"
    state_path.write_text(json.dumps(state), encoding="utf-8")

    rows = read_tournament_results(tmp_path).matches

    expected = (tmp_path / recorded.replace("\\", "/") / "replay.jsonl").resolve()
    assert rows[0].replay_path == expected
    assert rows[1].artifact_dir is None
    assert rows[1].replay_path is None
    assert rows[1].replay_unavailable_reason == (
        "This match's folder is outside the tournament folder."
    )


_VALID_HEADER = {"schema": "battle2.tournament", "schema_version": 1}


@pytest.mark.parametrize(
    ("content", "message"),
    [
        (None, "No tournament results were found"),
        ("{not json", "could not be read"),
        (json.dumps({"schema": "battle2.result", "schema_version": 1}), "not a supported"),
        (json.dumps({**_VALID_HEADER, "schema_version": 2}), "not a supported"),
        (
            json.dumps(
                {
                    **_VALID_HEADER,
                    "tournament_id": "t",
                    "division": "vm",
                    "matches": "oops",
                    "standings": [],
                }
            ),
            "damaged",
        ),
        (
            json.dumps(
                {
                    **_VALID_HEADER,
                    "tournament_id": "t",
                    "division": "vm",
                    "matches": [{"status": "completed"}],
                    "standings": [],
                }
            ),
            "damaged",
        ),
    ],
)
def test_missing_unsupported_or_damaged_state_fails_cleanly(tmp_path, content, message):
    if content is not None:
        (tmp_path / "tournament.json").write_text(content, encoding="utf-8")

    with pytest.raises(TournamentResultsError, match=message):
        read_tournament_results(tmp_path)


def test_tournament_history_lists_saved_tournaments_newest_first(tmp_path):
    data_root = tmp_path / "data"
    assert discover_tournaments(data_root) == ()
    root = tournaments_root(data_root)
    TournamentService().run(_request(root / "older"))
    with pytest.raises(_Abort):
        TournamentService(_FailSecondMatch(_Abort())).run(_request(root / "stopped"))
    (root / "not-a-tournament").mkdir()
    (root / "damaged").mkdir()
    (root / "damaged" / "tournament.json").write_text("{", encoding="utf-8")
    os.utime(root / "older" / "tournament.json", (1_000_000, 1_000_000))
    os.utime(root / "stopped" / "tournament.json", (2_000_000, 2_000_000))
    os.utime(root / "damaged" / "tournament.json", (3_000_000, 3_000_000))

    entries = discover_tournaments(data_root)

    assert [entry.output_dir.name for entry in entries] == ["damaged", "stopped", "older"]
    damaged, stopped, older = entries
    assert "could not be read" in damaged.error
    assert history_status_text(damaged) == "Unreadable"
    assert (stopped.finished, stopped.match_count, stopped.completed_count) == (False, 1, 1)
    assert stopped.entrant_ids == ("runner", "writer")
    assert stopped.leader_ids == ()
    assert history_status_text(stopped) == "Did not finish"
    assert history_top_standing_text(stopped) == "—"
    assert (older.finished, older.match_count, older.completed_count) == (True, 3, 3)
    assert older.entrant_ids == ("seeker", "runner", "writer")
    assert older.leader_ids == ("seeker",)
    assert history_status_text(older) == "Complete"
    assert history_top_standing_text(older) == "seeker"


def test_state_signature_changes_only_when_the_service_writes_state(tmp_path):
    assert tournament_state_signature(tmp_path) is None
    request = _request(tmp_path)
    TournamentService().run(request)
    written = tournament_state_signature(tmp_path)
    assert written is not None

    with pytest.raises(TournamentConfigurationError, match="does not match"):
        TournamentService().run(_request(tmp_path, rounds=2))
    assert tournament_state_signature(tmp_path) == written

    TournamentService().run(request)
    assert tournament_state_signature(tmp_path) != written


def test_not_run_message_gives_the_reason_and_protects_earlier_results():
    stderr = "WARNING: starter\nERROR: Existing tournament state does not match this request.\n"

    text = describe_tournament_not_run(2, stderr, had_earlier_results=True)

    assert text.startswith("Bytefray could not run this tournament")
    assert "ERROR: Existing tournament state does not match this request." in text
    assert "already contains results from an earlier tournament" in text
    assert "Exit code 2" in text
    assert "earlier tournament" not in describe_tournament_not_run(
        2, "", had_earlier_results=False
    )


def test_designer_default_output_is_a_fresh_folder_under_runs_tournaments(tmp_path):
    first = new_tournament_output_directory(tmp_path)
    second = new_tournament_output_directory(tmp_path)

    assert first != second
    assert first.parent == second.parent == tournaments_root(tmp_path)
    assert first.name.startswith("designer-")
    assert not first.exists()
