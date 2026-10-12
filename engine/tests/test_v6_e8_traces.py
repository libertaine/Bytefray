"""V6 E8: trace capture, binding, storage and the callback rows (PR8 Sec 10, D8-12; phase I8-5).

Every match is played by scripted, non-family agents (``_e8_scripted_matrix.SCOUT``)
through the real evaluation path, at infrastructure seeds and short tick
limits. No family member plays, and no outcome is asserted: the tests concern
what is captured, how faithfully, and in which form.
"""

from __future__ import annotations

import gzip
import hashlib
import json
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest
from _e8_scripted_matrix import scripted_field, write_package

from tools.research.v6.e8 import compatibility, matrix, traces
from tools.research.v6.e8.traces import ABSENT, COLUMN, TraceBindingError, TraceFormatError

C = COLUMN
TICKS = 40


@pytest.fixture(scope="module")
def fields(tmp_path_factory: pytest.TempPathFactory) -> dict[str, tuple[Path, Path, list[traces.TraceRecord], dict]]:
    root = tmp_path_factory.mktemp("e8-traces")
    return {c.condition_id: scripted_field(root, c.ruleset_id, ticks=TICKS) for c in matrix.CONDITIONS}


def _rows(field: Path, records: list[traces.TraceRecord]) -> list[list[list[Any]]]:
    return [traces.read_rows(field, record) for record in records]


# ---------------------------------------------------------------------------
# Capture, binding and storage
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("condition_id", ["C8", "T8", "C8L", "T8L"])
def test_every_completed_cell_is_traced_bound_and_stored_as_lf(fields: dict, condition_id: str) -> None:
    field, _, records, _ = fields[condition_id]
    cells = {cell.schedule_id: cell for cell in traces.completed_cells(field)}
    assert len(records) == len(cells) == 4
    assert traces.read_index(field) == records
    ruleset_id = matrix.condition(condition_id).ruleset_id
    for record in records:
        cell = cells[record.schedule_id]
        assert (record.match_id, record.result_id, record.ruleset_id) == (cell.match_id, cell.result_id, ruleset_id)
        assert record.replay_sha256 == hashlib.sha256(cell.replay_path.read_bytes()).hexdigest()
        stored = traces.stored_trace_path(field, record)
        raw = gzip.decompress(stored.read_bytes())
        assert b"\r" not in raw  # P8-13: stored with LF line endings
        assert (len(raw), hashlib.sha256(raw).hexdigest(), stored.stat().st_size) == (
            record.trace_bytes, record.trace_sha256, record.gz_bytes)
        assert record.raw_line_endings in ("CRLF", "LF")
        binding = traces.binding_of(traces.iter_trace(stored))
        assert (binding["match_id"], binding["replay_sha256"], binding["ruleset_id"]) == (
            record.match_id, record.replay_sha256, ruleset_id)
        header = next(traces.iter_trace(stored))
        assert (header["schema"], header["schema_version"]) == ("bytefray.agent_trace", 2)


def test_storage_normalizes_line_endings_and_is_deterministic(tmp_path: Path) -> None:
    source = tmp_path / "trace.jsonl"
    source.write_bytes(b'{"a": 1}\r\n{"b": 2}\r\n')
    first, second = tmp_path / "1" / "t.gz", tmp_path / "2" / "t.gz"
    stored = traces.store_trace(source, first)
    traces.store_trace(source, second)
    assert first.read_bytes() == second.read_bytes()
    assert gzip.decompress(first.read_bytes()) == b'{"a": 1}\n{"b": 2}\n'
    assert stored == traces.StoredTrace(hashlib.sha256(b'{"a": 1}\n{"b": 2}\n').hexdigest(), 18,
                                        first.stat().st_size, "CRLF")
    assert traces.line_endings(b"a\nb\n") == "LF" and traces.line_endings(b"a\r\nb\n") == "mixed"
    assert not list(first.parent.glob("*.tmp"))


def _cell(field: Path) -> traces.CellRef:
    return traces.completed_cells(field)[0]


def test_a_changed_replay_fails_the_binding(tmp_path: Path) -> None:
    field, env, _, _ = scripted_field(tmp_path, matrix.condition("T8").ruleset_id, ticks=TICKS)
    cell = _cell(field)
    cell.replay_path.write_bytes(cell.replay_path.read_bytes() + b"\n")
    with pytest.raises(TraceBindingError, match="replay_sha256"):
        traces.trace_cell(cell, field_root=field, data_root=env, ticks=TICKS, arena_size=512, scratch=tmp_path / "s")


@pytest.mark.parametrize("name", ["match_id", "result_id"])
def test_a_changed_identity_fails_the_binding(tmp_path: Path, name: str) -> None:
    field, env, _, _ = scripted_field(tmp_path, matrix.condition("C8").ruleset_id, ticks=TICKS)
    cell = replace(_cell(field), **{name: "0" * 64})
    with pytest.raises(TraceBindingError, match=name):
        traces.trace_cell(cell, field_root=field, data_root=env, ticks=TICKS, arena_size=512, scratch=tmp_path / "s")


def test_a_different_tick_limit_fails_the_binding(tmp_path: Path) -> None:
    field, env, _, _ = scripted_field(tmp_path, matrix.condition("T8L").ruleset_id, ticks=TICKS)
    with pytest.raises(TraceBindingError):
        traces.trace_cell(_cell(field), field_root=field, data_root=env, ticks=TICKS - 1, arena_size=512,
                          scratch=tmp_path / "s")


def test_a_missing_cell_fails_the_field_count(tmp_path: Path) -> None:
    field, env, _, _ = scripted_field(tmp_path, matrix.condition("C8").ruleset_id, ticks=TICKS)
    with pytest.raises(TraceBindingError, match="5 expected"):
        traces.trace_field(field, data_root=env, ticks=TICKS, arena_size=512, expected_cells=5)


def test_the_pre_match_gate_refuses_before_the_traced_match_exists(tmp_path: Path) -> None:
    # An ungated SENSE package: its guard reads another name, so D8-9 classes it ungated.
    field, env, _, _ = scripted_field(tmp_path, matrix.condition("C8").ruleset_id, ticks=TICKS)
    cell = _cell(field)
    traces.trace_path_for(field, cell).unlink()  # the fixture's own trace of this cell
    source = (env / "agents" / "scout_a" / "agent.py").read_text(encoding="utf-8")
    write_package(env, "scout_a", source.replace("self.sensing_window", "self.window"))
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    with pytest.raises(compatibility.IncompatiblePairing, match="scout_a"):
        traces.trace_cell(cell, field_root=field, data_root=env, ticks=TICKS, arena_size=512, scratch=scratch)
    assert not any(scratch.iterdir())  # no run directory, so no match artifact
    assert not traces.trace_path_for(field, cell).exists()


# ---------------------------------------------------------------------------
# The rows: presence and the write log
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("condition_id", ["C8", "C8L"])
def test_under_the_controls_every_e8_field_is_absent(fields: dict, condition_id: str) -> None:
    field, _, records, _ = fields[condition_id]
    for rows in _rows(field, records):
        assert rows and {row[C["kind"]] for row in rows} <= {"move", "write"}
        assert all(row[C["sensed"]] == ABSENT and row[C["delivered"]] == ABSENT for row in rows)
    for line in traces.read_summaries(field):
        assert line["summary"]["reset_windows"] == {"A": [ABSENT], "B": [ABSENT]}


@pytest.mark.parametrize("condition_id", ["T8", "T8L"])
def test_under_the_treatments_presence_follows_the_registered_rules(fields: dict, condition_id: str) -> None:
    field, _, records, _ = fields[condition_id]
    statuses: set[tuple[str, str]] = set()
    for rows in _rows(field, records):
        last: dict[tuple[str, str], list[Any]] = {}
        for row in rows:
            key = (row[C["entrant"]], row[C["process"]])
            previous = last.get(key)
            if previous is not None and previous[C["kind"]] == "sense":
                assert row[C["delivered"]] == previous[C["sensed"]]  # the reflection, null included
            else:
                assert row[C["delivered"]] == ABSENT
            if row[C["kind"]] == "sense":
                statuses.add((row[C["status"]], "list" if isinstance(row[C["sensed"]], list) else repr(row[C["sensed"]])))
            else:
                assert row[C["sensed"]] == ABSENT
            last[key] = row
    # Both an applied SENSE (a list, possibly empty) and an out-of-reach refusal (null) occur.
    assert statuses == {("APPLIED", "list"), ("REJECTED_OUT_OF_REACH", "None")}
    for line in traces.read_summaries(field):
        assert line["summary"]["reset_windows"] == {"A": [27], "B": [27]}


@pytest.mark.parametrize("condition_id", ["C8", "T8", "C8L", "T8L"])
def test_the_replay_write_log_equals_the_traced_writes(fields: dict, condition_id: str) -> None:
    field, _, records, _ = fields[condition_id]
    summaries = {line["schedule_id"]: line["summary"] for line in traces.read_summaries(field)}
    writes = 0
    for record, rows in zip(records, _rows(field, records), strict=True):
        log = traces.trace_write_log(rows)
        _, replay_log = traces.replay_facts(field / record.replay)
        assert log == [list(item) for item in replay_log]
        assert traces.write_log_digest(log) == summaries[record.schedule_id]["replay_write_log_sha256"]
        writes += len(log)
    assert writes > 0


def _trace_records(field: Path, record: traces.TraceRecord) -> list[dict[str, Any]]:
    return list(traces.iter_trace(traces.stored_trace_path(field, record)))


def _extract(field: Path, record: traces.TraceRecord, records: list[dict[str, Any]]) -> traces.Extraction:
    start, log = traces.replay_facts(field / record.replay)
    return traces.extract(records, arena=512, start=start, replay_log=log)


def test_extraction_refuses_a_trace_without_a_header_or_of_another_schema(fields: dict) -> None:
    field, _, records, _ = fields["T8"]
    original = _trace_records(field, records[0])
    with pytest.raises(TraceFormatError, match="no header"):
        _extract(field, records[0], original[1:])
    wrong = json.loads(json.dumps(original))
    wrong[0]["schema_version"] = 1
    with pytest.raises(TraceFormatError, match="schema-2"):
        _extract(field, records[0], wrong)


def test_extraction_refuses_an_observation_that_disagrees_with_the_replay(fields: dict) -> None:
    field, _, records, _ = fields["C8"]
    changed = json.loads(json.dumps(_trace_records(field, records[0])))
    next(r for r in changed if r["record_type"] == "decision_v2")["observation"]["own_core_base"] += 1
    with pytest.raises(TraceFormatError, match="own_core_base"):
        _extract(field, records[0], changed)


def test_extraction_refuses_a_malformed_sense_field(fields: dict) -> None:
    field, _, records, _ = fields["T8"]
    changed = json.loads(json.dumps(_trace_records(field, records[0])))
    sense = next(r for r in changed if r["record_type"] == "decision_v2" and (r.get("action") or {}).get("kind") == "sense")
    sense["applied_result"]["sensed_anchors"] = 5
    with pytest.raises(TraceFormatError, match="sensed_anchors"):
        _extract(field, records[0], changed)


def test_a_planted_extra_write_changes_the_replay_write_log(fields: dict, tmp_path: Path) -> None:
    field, _, records, _ = fields["T8"]
    lines = (field / records[0].replay).read_text(encoding="utf-8").splitlines()
    index = next(i for i, line in enumerate(lines) if json.loads(line).get("record_type") == "tick"
                 and json.loads(line)["tick"] == 1)
    tick = json.loads(lines[index])
    tick["memory_diffs"].append({"addr": 7, "len": 1, "owner": "A", "values": [1]})
    lines[index] = json.dumps(tick)
    planted = tmp_path / "replay.jsonl"
    planted.write_text("\n".join(lines) + "\n", encoding="utf-8")
    assert traces.replay_facts(planted)[1] != traces.replay_facts(field / records[0].replay)[1]


def test_the_size_report_projects_and_keeps_every_trace(fields: dict) -> None:
    _, _, records, _ = fields["T8"]
    report = traces.size_report(records, matrix_cells=matrix.matches_total())
    assert report["cells_measured"] == 4 and report["matrix_cells"] == 16_896
    assert report["projected_gz_bytes"] == sum(r.gz_bytes for r in records) * 16_896 // 4
    assert report["retention"] == "every cell (D8-12)"
    with pytest.raises(ValueError):
        traces.size_report([], matrix_cells=1)
