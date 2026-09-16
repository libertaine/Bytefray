"""Regression coverage for canonical LF-only replay JSONL serialization.

``write_replay`` is the sole production seam that produces the persisted
``replay.jsonl`` artifact (see ``match_service._finalize_native_artifacts``).
Historically it opened the destination in text mode without pinning
``newline``, so Python's universal-newline translation silently rewrote
every ``\n`` to the host line separator on write -- ``\r\n`` on Windows.
That made byte-identical, semantically-identical replays hash differently
across platforms even though gameplay was fully deterministic. These tests
pin the writer's own newline contract at the byte level so the guarantee
does not silently regress, and they exercise the real production writer
rather than re-implementing serialization in the test.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from battle_engine.replay import (
    AgentState,
    KillDeathEvent,
    MatchConfiguration,
    MatchResult,
    MemoryDiff,
    ProcessState,
    ReplayHeader,
    TickSnapshot,
    iter_replay,
    write_replay,
)


def _sample_records() -> list[object]:
    return [
        ReplayHeader(
            MatchConfiguration(128, 4, 602, "score", {"alive": 1.5}),
            {"A": "v5_dual_team", "B": "v4_quorum"},
            replay_id="replay_1",
            match_id="match_1",
            result_id="result_1",
            schema_version=4,
        ),
        TickSnapshot(
            1,
            agents=(AgentState("A", 12, region=(0, 20)),),
            processes=(ProcessState("scout", "A", 37, True, 8),),
            score={"A": 1.0, "B": 0.0},
            memory_diffs=(MemoryDiff(30, 3, "A", (0xAA, 0xBB)),),
            events=(KillDeathEvent("kill", "B", "A"),),
            schema_version=4,
        ),
        MatchResult(
            "A",
            "score_fallback",
            1,
            {"A": 1.0, "B": 0.0},
            processes=(ProcessState("scout", "A", 37, True, 8),),
            schema_version=4,
        ),
    ]


def test_write_replay_contains_no_crlf_at_the_byte_level(tmp_path: Path) -> None:
    replay_path = tmp_path / "replay.jsonl"
    write_replay(replay_path, _sample_records())

    raw = replay_path.read_bytes()

    assert b"\r\n" not in raw
    assert b"\r" not in raw
    assert b"\n" in raw


def test_write_replay_terminates_every_record_with_a_bare_lf(tmp_path: Path) -> None:
    replay_path = tmp_path / "replay.jsonl"
    write_replay(replay_path, _sample_records())

    raw = replay_path.read_bytes()
    lines = raw.split(b"\n")

    # One trailing empty element from the final terminator, preserved as
    # existing behavior: every record is followed by "\n", including the
    # last one, so the file itself ends with a newline.
    assert lines[-1] == b""
    assert len(lines) - 1 == len(_sample_records())
    for line in lines[:-1]:
        assert line  # no blank lines between records
        assert not line.endswith(b"\r")


def test_write_replay_preserves_semantic_record_content(tmp_path: Path) -> None:
    records = _sample_records()
    replay_path = tmp_path / "replay.jsonl"
    write_replay(replay_path, records)

    assert list(iter_replay(replay_path)) == records


def test_write_replay_pins_lf_in_the_writer_itself_not_via_host_default(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The writer must declare its own newline contract explicitly.

    This is a stronger guarantee than "the bytes happen to come out as LF
    on this platform": it asserts that ``write_replay`` opens its output
    with an explicit ``newline="\n"`` (disabling universal-newline
    translation) and explicit UTF-8 encoding, so the behavior does not
    depend on the host OS's line-ending default -- and would still fail
    this test on Linux if the ``newline`` argument were ever dropped.
    """

    replay_path = tmp_path / "replay.jsonl"
    captured: dict[str, object] = {}
    original_open = Path.open

    def spy_open(self: Path, *args: object, **kwargs: object) -> object:
        if self == replay_path:
            captured["newline"] = kwargs.get("newline")
            captured["encoding"] = kwargs.get("encoding")
        return original_open(self, *args, **kwargs)

    monkeypatch.setattr(Path, "open", spy_open)

    write_replay(replay_path, _sample_records())

    assert captured == {"newline": "\n", "encoding": "utf-8"}


def test_write_replay_lf_bytes_are_stable_across_repeated_writes(tmp_path: Path) -> None:
    records = _sample_records()
    first_path = tmp_path / "first.jsonl"
    second_path = tmp_path / "second.jsonl"

    write_replay(first_path, records)
    write_replay(second_path, records)

    assert first_path.read_bytes() == second_path.read_bytes()
