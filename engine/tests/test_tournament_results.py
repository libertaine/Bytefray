"""Tournament Results/History presentation, derived from real ``TournamentService`` runs.

V6 Phase 2B.12 (docs/research/v6/V6_PHASE2B12_SCOPE_C_RUNTIME_RETIREMENT.md)
retired VM/blob execution: this file's real subject is the presentation
layer (``app.services.tournament_results``), not the VM builtins it used
to drive ``TournamentService`` with. The three bundled VM starters
(``runner``/``writer``/``seeker``, whose relative strength under Ruleset 1
gave a deterministic 2-0 winner and a tied last place) are replaced with
three small Agent API v2 fixtures engineered for the identical deterministic
shape under the retained control: one agent survives every tick
(``_SURVIVOR_SOURCE``) and two immediately forfeit on their first action
(``_FORFEIT_SOURCE``), so the survivor wins both its matches and the two
forfeiters tie each other for last -- verified directly against a real
tournament run, not assumed.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from battle_engine.agents import resolve_agent
from battle_engine.config import Config
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

_SURVIVOR_SOURCE = """
from battle_engine.agent_api import ActionKindV2, AgentAction, ProcessDeclaration

class Agent:
    def reset(self, context):
        pass

    def declare_processes(self):
        return [ProcessDeclaration("main", 1, 1.0)]

    def act(self, observation):
        return AgentAction(ActionKindV2.READ, observation.self_anchor)

def create_agent():
    return Agent()
"""

# Raises on its very first act() call, forfeiting immediately -- a real,
# reproducible loss under bytefray-rules-4's alive-ticks/score-based winner
# resolution, mirroring what a VM `runner`/`writer` builtin used to lose to
# `seeker` by. Deliberately distinct from a HALT: this exercises the same
# "user code forfeits" path every real agent failure takes.
_FORFEIT_SOURCE = """
from battle_engine.agent_api import ProcessDeclaration

class Agent:
    def reset(self, context):
        pass

    def declare_processes(self):
        return [ProcessDeclaration("main", 1, 1.0)]

    def act(self, observation):
        raise RuntimeError("always forfeits")

def create_agent():
    return Agent()
"""

_FIXTURE_SOURCES = {
    "survivor": _SURVIVOR_SOURCE,
    "forfeit_a": _FORFEIT_SOURCE,
    "forfeit_b": _FORFEIT_SOURCE,
}


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


def _write_fixture_agents(data_root: Path) -> None:
    for name, source in _FIXTURE_SOURCES.items():
        directory = data_root / "agents" / name
        if directory.exists():
            continue
        directory.mkdir(parents=True)
        (directory / "agent.yaml").write_text(
            json.dumps(
                {
                    "kind": "python",
                    "api_version": 2,
                    "entrypoint": "agent.py:create_agent",
                    "name": name,
                    "display": name.replace("_", " ").title(),
                    "version": "1.0",
                }
            ),
            encoding="utf-8",
        )
        (directory / "agent.py").write_text(source, encoding="utf-8")


def _python_entrants(data_root: Path, *names: str) -> tuple[MatchEntrant, ...]:
    _write_fixture_agents(data_root)
    spacing = ARENA // len(names)
    return tuple(
        MatchEntrant.python(
            name, name.replace("_", " ").title() + " Bot", index * spacing,
            resolve_agent(data_root, name),
        )
        for index, name in enumerate(names)
    )


def _request(output_dir: Path, *, data_root: Path | None = None, **changes) -> TournamentRequest:
    root = data_root or output_dir
    values = {
        "entrants": _python_entrants(root, "survivor", "forfeit_a", "forfeit_b"),
        "config": Config(arena_size=ARENA, instr_per_tick=8),
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
        ("survivor", 2),
        ("forfeit_a", 0),
        ("forfeit_b", 0),
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
    assert [row.name for row in results.standings] == [
        "Survivor Bot",
        "Forfeit A Bot",
        "Forfeit B Bot",
    ]
    assert [row.name for row in results.leaders] == ["Survivor Bot"]
    assert headline_text(results) == "Winner: Survivor Bot"
    assert status_text(results) == "Complete: 3 of 3 matches completed."
    assert results.ruleset_ids == ("bytefray-rules-4",)
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
        "Survivor Bot won",
        "Survivor Bot won",
        "Tie",
    ]


def test_entrants_level_on_wins_and_score_share_a_rank(tmp_path):
    service_result = TournamentService().run(_request(tmp_path))
    forfeit_a, forfeit_b = service_result.standings[1], service_result.standings[2]
    assert (forfeit_a.wins, forfeit_a.score_total) == (forfeit_b.wins, forfeit_b.score_total)

    results = read_tournament_results(tmp_path)

    assert [(row.rank, row.agent_id) for row in results.standings] == [
        (1, "survivor"),
        (2, "forfeit_a"),
        (2, "forfeit_b"),
    ]


def test_top_tie_is_reported_as_a_tie_not_resolved_by_agent_id(tmp_path):
    _write_fixture_agents(tmp_path)
    entrants = tuple(
        MatchEntrant.python(
            f"survivor_{index}", f"Agent {index}", index * (ARENA // 3),
            resolve_agent(tmp_path, "survivor"),
        )
        for index in range(3)
    )
    service_result = TournamentService().run(
        _request(
            tmp_path,
            entrants=entrants,
            config=Config(arena_size=ARENA, instr_per_tick=8),
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
    assert failed.entrant_ids == ("survivor", "forfeit_b")
    assert match_result_text(failed) == "Failed"
    assert failed.error_message == "backend broke"
    assert failed.replay_path is None
    assert failed.replay_unavailable_reason == NOT_COMPLETED_REPLAY_TEXT
    assert headline_text(results) == "Leader: Survivor Bot"
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
    assert reread[1].winner == "survivor"
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
                    "division": "python",
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
                    "division": "python",
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
    TournamentService().run(_request(root / "older", data_root=data_root))
    with pytest.raises(_Abort):
        TournamentService(_FailSecondMatch(_Abort())).run(
            _request(root / "stopped", data_root=data_root)
        )
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
    assert stopped.entrant_ids == ("survivor", "forfeit_a")
    assert stopped.leader_ids == ()
    assert history_status_text(stopped) == "Did not finish"
    assert history_top_standing_text(stopped) == "—"
    assert (older.finished, older.match_count, older.completed_count) == (True, 3, 3)
    assert older.entrant_ids == ("survivor", "forfeit_a", "forfeit_b")
    assert older.leader_ids == ("survivor",)
    assert history_status_text(older) == "Complete"
    assert history_top_standing_text(older) == "survivor"


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
