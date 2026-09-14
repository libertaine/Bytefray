"""Qt-free reading of a tournament's canonical artifacts for the Designer's results views."""

from __future__ import annotations

import json
import time
import uuid
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from battle_engine.replay_integrity import (
    ReplayPreflightFailure,
    ReplayPreflightResult,
    preflight_result_replay,
)
from battle_engine.result_model import ResultEnvelope, read_result
from battle_engine.tournament_service import SCHEMA_NAME, SCHEMA_VERSION

from app.services import replay_integrity as replay_integrity_service
from app.services.designer_workflows import RUNTIME_LABELS
from app.services.replay_history_presentation import ruleset_label

TOURNAMENT_STATE_FILENAME = "tournament.json"
MATCH_COMPLETED = "completed"

NO_TOURNAMENT_HISTORY_TEXT = (
    "No tournament results have been recorded yet. Run a tournament to create results."
)
REPLAY_AVAILABLE_TEXT = "Available"
REPLAY_UNAVAILABLE_TEXT = "Replay unavailable"
REPLAY_CHANGED_TITLE = replay_integrity_service.REPLAY_CHANGED_TITLE
REPLAY_CHANGED_BODY = replay_integrity_service.REPLAY_CHANGED_BODY
NOT_COMPLETED_REPLAY_TEXT = "This match did not complete, so it has no replay."
REPLAY_MISSING_TEXT = "The replay file is missing."
REPLAY_CHANGED_TEXT = "The replay file has changed since the match was recorded."

REPLAY_READY = "ready"
REPLAY_MISSING = "missing"
REPLAY_CHANGED = "changed"

_STATUS_LABELS = {
    "completed": "Completed",
    "failed": "Failed",
    "rejected": "Rejected",
    "corrupted": "Corrupted",
}


class TournamentResultsError(ValueError):
    """A tournament folder's results cannot be shown; the message is user-facing."""


@dataclass(frozen=True)
class StandingRow:
    rank: int
    agent_id: str
    name: str
    played: int
    wins: int
    losses: int
    ties: int
    score_total: float


@dataclass(frozen=True)
class MatchRow:
    number: int
    round_number: int
    entrant_ids: tuple[str, ...]
    entrant_names: tuple[str, ...]
    seed: int
    status: str
    artifact_dir: Path | None
    error_message: str | None = None
    winner: str | None = None
    termination_reason: str | None = None
    ticks: int | None = None
    ruleset_id: str | None = None
    result_path: Path | None = None
    replay_path: Path | None = None
    replay_sha256: str | None = None
    replay_unavailable_reason: str | None = None
    recorded_result_id: str | None = None

    def name_of(self, agent_id: str) -> str:
        for entrant_id, name in zip(self.entrant_ids, self.entrant_names, strict=True):
            if entrant_id == agent_id:
                return name
        return agent_id


@dataclass(frozen=True)
class TournamentResults:
    output_dir: Path
    tournament_id: str
    division: str
    finished: bool
    standings: tuple[StandingRow, ...]
    matches: tuple[MatchRow, ...]
    ruleset_ids: tuple[str, ...]

    @property
    def state_path(self) -> Path:
        return self.output_dir / TOURNAMENT_STATE_FILENAME

    @property
    def completed_count(self) -> int:
        return sum(1 for match in self.matches if match.status == MATCH_COMPLETED)

    @property
    def not_completed_count(self) -> int:
        return len(self.matches) - self.completed_count

    @property
    def leaders(self) -> tuple[StandingRow, ...]:
        if not self.finished or self.completed_count == 0:
            return ()
        return tuple(row for row in self.standings if row.rank == 1)


@dataclass(frozen=True)
class TournamentHistoryEntry:
    output_dir: Path
    updated_at: float
    finished: bool = False
    match_count: int = 0
    completed_count: int = 0
    entrant_ids: tuple[str, ...] = ()
    leader_ids: tuple[str, ...] = ()
    error: str | None = None


@dataclass(frozen=True)
class _MatchRecord:
    round_number: int
    entrant_ids: tuple[str, ...]
    seed: int
    status: str
    artifact_dir: str
    result_id: str | None
    error_message: str | None


@dataclass(frozen=True)
class _StandingRecord:
    agent_id: str
    played: int
    wins: int
    losses: int
    ties: int
    score_total: float


@dataclass(frozen=True)
class _TournamentState:
    tournament_id: str
    division: str
    matches: tuple[_MatchRecord, ...]
    standings: tuple[_StandingRecord, ...]

    @property
    def finished(self) -> bool:
        # TournamentService writes standings only once the whole schedule has run.
        return bool(self.standings)

    @property
    def completed_count(self) -> int:
        return sum(1 for match in self.matches if match.status == MATCH_COMPLETED)


def _text(value: object) -> str:
    if not isinstance(value, str):
        raise TypeError(f"expected text, got {type(value).__name__}")
    return value


def _optional_text(value: object) -> str | None:
    return None if value is None else _text(value)


def _integer(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"expected an integer, got {type(value).__name__}")
    return value


def _number(value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"expected a number, got {type(value).__name__}")
    return float(value)


def _objects(value: object) -> list[Mapping[str, Any]]:
    if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
        raise TypeError("expected a list of objects")
    return value


def _match_record(item: Mapping[str, Any]) -> _MatchRecord:
    entrant_ids = item["entrant_ids"]
    if not isinstance(entrant_ids, list):
        raise TypeError("expected a list of entrant IDs")
    return _MatchRecord(
        round_number=_integer(item["round_number"]),
        entrant_ids=tuple(_text(value) for value in entrant_ids),
        seed=_integer(item["seed"]),
        status=_text(item["status"]),
        artifact_dir=_text(item["artifact_dir"]),
        result_id=_optional_text(item.get("result_id")),
        error_message=_optional_text(item.get("error_message")),
    )


def _standing_record(item: Mapping[str, Any]) -> _StandingRecord:
    return _StandingRecord(
        agent_id=_text(item["agent_id"]),
        played=_integer(item["played"]),
        wins=_integer(item["wins"]),
        losses=_integer(item["losses"]),
        ties=_integer(item["ties"]),
        score_total=_number(item["score_total"]),
    )


def _load_state(directory: Path) -> _TournamentState:
    state_path = directory / TOURNAMENT_STATE_FILENAME
    if not state_path.is_file():
        raise TournamentResultsError(f"No tournament results were found in {directory}.")
    try:
        data = json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise TournamentResultsError(
            f"The tournament results file could not be read: {exc}"
        ) from exc
    if (
        not isinstance(data, dict)
        or data.get("schema") != SCHEMA_NAME
        or data.get("schema_version") != SCHEMA_VERSION
    ):
        raise TournamentResultsError(
            f"{state_path} is not a supported Bytefray tournament results file."
        )
    try:
        return _TournamentState(
            tournament_id=_text(data["tournament_id"]),
            division=_text(data["division"]),
            matches=tuple(_match_record(item) for item in _objects(data["matches"])),
            standings=tuple(_standing_record(item) for item in _objects(data["standings"])),
        )
    except (KeyError, TypeError) as exc:
        raise TournamentResultsError(
            f"The tournament results file is damaged ({exc}): {state_path}"
        ) from exc


def _competition_ranks(standings: Sequence[_StandingRecord]) -> tuple[int, ...]:
    # Level wins and score share a rank; the service's agent-ID tiebreak only fixes row order.
    ranks: list[int] = []
    previous: tuple[int, float] | None = None
    for position, row in enumerate(standings, start=1):
        key = (row.wins, row.score_total)
        ranks.append(ranks[-1] if key == previous else position)
        previous = key
    return tuple(ranks)


def _match_directory(tournament_dir: Path, recorded: str) -> Path | None:
    # Recorded with the writing platform's separator; normalize so any platform can read it.
    candidate = (tournament_dir / recorded.replace("\\", "/")).resolve()
    if candidate == tournament_dir or not candidate.is_relative_to(tournament_dir):
        return None
    return candidate


def _read_match_result(
    record: _MatchRecord, match_dir: Path | None
) -> tuple[ResultEnvelope | None, str | None]:
    if record.status != MATCH_COMPLETED:
        return None, None
    if match_dir is None:
        return None, "This match's folder is outside the tournament folder."
    try:
        envelope = read_result(match_dir / "result.json")
    except (OSError, ValueError, KeyError, TypeError):
        return None, "This match's result file is missing or could not be read."
    if record.result_id is not None and envelope.result_id != record.result_id:
        return None, "This match's result file does not match the tournament record."
    return envelope, None


def _replay_location(
    envelope: ResultEnvelope, match_dir: Path
) -> tuple[Path | None, str | None, str | None]:
    reference = envelope.replay
    if reference is None:
        return None, None, "This match's result does not reference a replay."
    filename = reference.filename
    if (
        not isinstance(filename, str)
        or filename in {"", ".", ".."}
        or Path(filename).name != filename
    ):
        return None, None, "This match's replay is not stored in its match folder."
    path = match_dir / filename
    if not path.is_file():
        return None, None, REPLAY_MISSING_TEXT
    return path, str(reference.sha256), None


def _entrant_names(envelopes: Sequence[ResultEnvelope]) -> dict[str, str]:
    names: dict[str, str] = {}
    for envelope in envelopes:
        for entrant in envelope.entrants:
            if not isinstance(entrant, Mapping):
                continue
            agent_id, name = entrant.get("agent_id"), entrant.get("name")
            if isinstance(agent_id, str) and isinstance(name, str) and name.strip():
                names.setdefault(agent_id, name)
    return names


def read_tournament_results(output_dir: Path) -> TournamentResults:
    """Read one tournament folder; raises ``TournamentResultsError`` if it cannot be shown."""

    directory = Path(output_dir).expanduser().resolve()
    state = _load_state(directory)
    loaded = []
    for record in state.matches:
        match_dir = _match_directory(directory, record.artifact_dir)
        envelope, problem = _read_match_result(record, match_dir)
        loaded.append((record, match_dir, envelope, problem))
    names = _entrant_names([envelope for _, _, envelope, _ in loaded if envelope is not None])

    matches = []
    for number, (record, match_dir, envelope, problem) in enumerate(loaded, start=1):
        row = MatchRow(
            number=number,
            round_number=record.round_number,
            entrant_ids=record.entrant_ids,
            entrant_names=tuple(names.get(agent_id, agent_id) for agent_id in record.entrant_ids),
            seed=record.seed,
            status=record.status,
            artifact_dir=match_dir,
        )
        if record.status != MATCH_COMPLETED:
            row = replace(
                row,
                error_message=record.error_message,
                replay_unavailable_reason=NOT_COMPLETED_REPLAY_TEXT,
            )
        elif envelope is None or match_dir is None:
            row = replace(row, replay_unavailable_reason=problem)
        else:
            replay_path, replay_sha256, replay_problem = _replay_location(envelope, match_dir)
            row = replace(
                row,
                winner=str(envelope.winner),
                termination_reason=envelope.termination_reason,
                ticks=envelope.ticks,
                ruleset_id=envelope.ruleset_id,
                result_path=match_dir / "result.json",
                replay_path=replay_path,
                replay_sha256=replay_sha256,
                replay_unavailable_reason=replay_problem,
                recorded_result_id=record.result_id,
            )
        matches.append(row)

    standings = tuple(
        StandingRow(
            rank=rank,
            agent_id=row.agent_id,
            name=names.get(row.agent_id, row.agent_id),
            played=row.played,
            wins=row.wins,
            losses=row.losses,
            ties=row.ties,
            score_total=row.score_total,
        )
        for rank, row in zip(_competition_ranks(state.standings), state.standings, strict=True)
    )
    ruleset_ids = tuple(sorted({match.ruleset_id for match in matches if match.ruleset_id}))
    return TournamentResults(
        output_dir=directory,
        tournament_id=state.tournament_id,
        division=state.division,
        finished=state.finished,
        standings=standings,
        matches=tuple(matches),
        ruleset_ids=ruleset_ids,
    )


def preflight_match_replay(match: MatchRow) -> ReplayPreflightResult:
    """Reread and verify a tournament match's canonical result and replay."""

    if match.result_path is None or match.artifact_dir is None:
        return ReplayPreflightResult(
            failure=ReplayPreflightFailure.RESULT_UNAVAILABLE,
            diagnostic="The tournament match has no readable canonical result.",
        )
    return preflight_result_replay(
        replay_integrity_service.result_replay_request(
            match.result_path,
            artifact_root=match.artifact_dir,
            expected_result_id=match.recorded_result_id,
        )
    )


def replay_preflight_state(outcome: ReplayPreflightResult) -> str:
    if outcome.verified:
        return REPLAY_READY
    if outcome.failure in {
        ReplayPreflightFailure.RESULT_ASSOCIATION_MISMATCH,
        ReplayPreflightFailure.REPLAY_REFERENCE_MALFORMED,
        ReplayPreflightFailure.REPLAY_PATH_UNSAFE,
        ReplayPreflightFailure.REPLAY_CHANGED,
        ReplayPreflightFailure.REPLAY_INVALID,
        ReplayPreflightFailure.REPLAY_IDENTITY_MISMATCH,
    }:
        return REPLAY_CHANGED
    return REPLAY_MISSING


def replay_preflight_unavailable_reason(outcome: ReplayPreflightResult) -> str:
    """Concise inline reason for a non-mismatch Tournament preflight failure."""

    if outcome.failure is ReplayPreflightFailure.REPLAY_MISSING:
        return REPLAY_MISSING_TEXT
    if outcome.failure in {
        ReplayPreflightFailure.RESULT_UNAVAILABLE,
        ReplayPreflightFailure.RESULT_PATH_UNSAFE,
    }:
        return "The match result needed to verify this replay is missing or unreadable."
    if outcome.failure in {
        ReplayPreflightFailure.REPLAY_REFERENCE_MISSING,
        ReplayPreflightFailure.REPLAY_REFERENCE_MALFORMED,
        ReplayPreflightFailure.REPLAY_PATH_UNSAFE,
    }:
        return "The match result no longer contains a safe, valid replay reference."
    return "The replay could not be read and verified."


def check_match_replay(match: MatchRow) -> str:
    """Compatibility status wrapper around the canonical click-time preflight."""

    return replay_preflight_state(preflight_match_replay(match))


def _match_count_text(count: int) -> str:
    return "1 match" if count == 1 else f"{count} matches"


def headline_text(results: TournamentResults) -> str:
    if not results.finished:
        return "No winner: the tournament did not finish."
    if results.completed_count == 0:
        return "No winner: no matches completed."
    leaders = results.leaders
    names = ", ".join(row.name for row in leaders)
    if len(leaders) > 1:
        return f"Tied for first: {names}"
    if results.not_completed_count:
        return f"Leader: {names}"
    return f"Winner: {names}"


def status_text(results: TournamentResults) -> str:
    total = len(results.matches)
    if not results.finished:
        return (
            f"This tournament stopped after {_match_count_text(total)} "
            f"({results.completed_count} completed). Final standings were not recorded."
        )
    if results.not_completed_count:
        return (
            f"Finished, but {results.not_completed_count} of {_match_count_text(total)} "
            "did not complete. Standings count completed matches only."
        )
    return f"Complete: {results.completed_count} of {_match_count_text(total)} completed."


def ruleset_text(results: TournamentResults) -> str:
    if not results.ruleset_ids:
        return "Unknown (no readable match results)"
    return ", ".join(ruleset_label(ruleset_id, "recorded") for ruleset_id in results.ruleset_ids)


def entrants_text(results: TournamentResults) -> str:
    runtime = RUNTIME_LABELS.get(results.division, results.division)
    if not results.finished:
        return f"Not recorded ({runtime}; the tournament did not finish)"
    return f"{len(results.standings)} ({runtime})"


def matches_text(results: TournamentResults) -> str:
    return f"{results.completed_count} of {_match_count_text(len(results.matches))} completed"


def format_score(value: float) -> str:
    if float(value).is_integer():
        return str(int(value))
    return f"{value:.3f}".rstrip("0").rstrip(".")


def match_title(match: MatchRow) -> str:
    return " vs ".join(match.entrant_names)


def match_result_text(match: MatchRow) -> str:
    if match.status != MATCH_COMPLETED:
        return _STATUS_LABELS.get(match.status, match.status.title())
    if match.winner is None:
        return "Result unavailable"
    # Same rule as TournamentService standings: a winner that is not an entrant counts as a tie.
    if match.winner not in match.entrant_ids:
        return "Tie"
    return f"{match.name_of(match.winner)} won"


def replay_column_text(match: MatchRow) -> str:
    return REPLAY_AVAILABLE_TEXT if match.replay_path is not None else REPLAY_UNAVAILABLE_TEXT


def match_detail_lines(match: MatchRow) -> tuple[str, ...]:
    entrants = " vs ".join(
        name if name == agent_id else f"{name} [{agent_id}]"
        for agent_id, name in zip(match.entrant_ids, match.entrant_names, strict=True)
    )
    lines = [
        f"Match {match.number} (round {match.round_number})",
        f"Entrants: {entrants}",
        f"Result: {match_result_text(match)}",
    ]
    if match.termination_reason is not None and match.ticks is not None:
        lines.append(f"Ended: {match.termination_reason} after {match.ticks} ticks")
    if match.ruleset_id:
        lines.append(f"Ruleset: {ruleset_label(match.ruleset_id, 'recorded')}")
    lines.append(f"Seed: {match.seed}")
    if match.artifact_dir is not None:
        lines.append(f"Match folder: {match.artifact_dir}")
    if match.replay_path is not None:
        lines.append(f"Replay: {match.replay_path}")
    else:
        lines.append(f"{REPLAY_UNAVAILABLE_TEXT}: {match.replay_unavailable_reason}")
    if match.error_message:
        lines.append(f"Details: {match.error_message}")
    return tuple(lines)


def tournaments_root(data_root: Path) -> Path:
    return Path(data_root).expanduser().resolve() / "runs" / "tournaments"


def discover_tournaments(data_root: Path) -> tuple[TournamentHistoryEntry, ...]:
    """Tournament folders directly beneath ``runs/tournaments``, most recently updated first."""

    try:
        children = sorted(tournaments_root(data_root).iterdir())
    except OSError:
        return ()
    entries: list[TournamentHistoryEntry] = []
    for child in children:
        try:
            updated_at = (child / TOURNAMENT_STATE_FILENAME).stat().st_mtime
        except OSError:
            continue
        try:
            state = _load_state(child)
        except TournamentResultsError as exc:
            entries.append(TournamentHistoryEntry(child, updated_at, error=str(exc)))
            continue
        if state.finished:
            entrant_ids = tuple(row.agent_id for row in state.standings)
        else:
            entrant_ids = tuple(
                dict.fromkeys(agent_id for match in state.matches for agent_id in match.entrant_ids)
            )
        leader_ids: tuple[str, ...] = ()
        if state.finished and state.completed_count:
            leader_ids = tuple(
                row.agent_id
                for rank, row in zip(
                    _competition_ranks(state.standings), state.standings, strict=True
                )
                if rank == 1
            )
        entries.append(
            TournamentHistoryEntry(
                output_dir=child,
                updated_at=updated_at,
                finished=state.finished,
                match_count=len(state.matches),
                completed_count=state.completed_count,
                entrant_ids=entrant_ids,
                leader_ids=leader_ids,
            )
        )
    entries.sort(key=lambda entry: -entry.updated_at)
    return tuple(entries)


def completion_label(finished: bool, match_count: int, completed_count: int) -> str:
    if not finished:
        return "Did not finish"
    if completed_count < match_count:
        return "Finished with errors"
    return "Complete"


def history_status_text(entry: TournamentHistoryEntry) -> str:
    if entry.error is not None:
        return "Unreadable"
    return completion_label(entry.finished, entry.match_count, entry.completed_count)


def history_top_standing_text(entry: TournamentHistoryEntry) -> str:
    if not entry.leader_ids:
        return "—"
    if len(entry.leader_ids) > 1:
        return "Tied: " + ", ".join(entry.leader_ids)
    return entry.leader_ids[0]


def new_tournament_output_directory(data_root: Path) -> Path:
    stamp = time.strftime("%Y%m%d-%H%M%S", time.gmtime())
    return tournaments_root(data_root) / f"designer-{stamp}-{uuid.uuid4().hex[:8]}"


def tournament_state_signature(output_dir: Path) -> tuple[int, int, int] | None:
    """Identity of ``tournament.json``; every service write atomically replaces the file."""

    try:
        stat = (Path(output_dir) / TOURNAMENT_STATE_FILENAME).stat()
    except OSError:
        return None
    return (stat.st_ino, stat.st_mtime_ns, stat.st_size)


def describe_tournament_not_run(exit_code: int, stderr: str, *, had_earlier_results: bool) -> str:
    parts = ["Bytefray could not run this tournament, so no new results were recorded."]
    reason_lines = [line for line in stderr.strip().splitlines() if line.strip()]
    if reason_lines:
        parts.append("\n".join(reason_lines[-5:])[-600:])
    if had_earlier_results:
        parts.append(
            "The output folder already contains results from an earlier tournament, which "
            "were left unchanged. To run a different tournament, choose a new output folder."
        )
    parts.append(f"Exit code {exit_code}. See the Advanced tab log for details.")
    return "\n\n".join(parts)
