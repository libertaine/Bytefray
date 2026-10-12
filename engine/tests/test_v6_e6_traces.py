"""V6 E6: trace capture, binding, compression, retention and the compact
telemetry extractor (implementation plan Sec 6).

Every match here is played by scripted test agents (``hunter`` below), never
by an E6 family member, and no outcome is asserted: the tests concern only
what is captured and how faithfully.
"""

from __future__ import annotations

import gzip
import hashlib
import json
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest
from battle_engine.agent_evaluation import EvaluationRequest, EvaluationService

from tools.research.v6.e6 import telemetry, traces
from tools.research.v6.e6.telemetry import ROW_FIELDS, TelemetryError, TickZero, extract
from tools.research.v6.e6.traces import (
    SUBSET_SEED_POSITIONS,
    TRACE_RETENTION_LIMIT_BYTES,
    TraceBindingError,
    TraceRecord,
)

SENSING = "bytefray-rules-6-research-sensing-r32"
CONTROL = "bytefray-rules-6-research-scale"
TICKS = 40

HUNTER = """\
from battle_engine.agent_api import ActionKindV2, AgentAction, ProcessDeclaration


class Agent:
    def reset(self, context):
        self.direction = 1 if context.rng.random() < 0.5 else -1
        self.half = context.arena_size // 2
        self.target = None
        self.offset = 0

    def declare_processes(self):
        return [ProcessDeclaration("p", self.half, 1.0)]

    def act(self, observation):
        visible = observation.visible_enemy_anchor_addresses
        if visible:
            self.target = visible[0]
        if self.target is not None:
            address = self.target + self.offset % 8
            self.offset += 1
            return AgentAction(ActionKindV2.WRITE, address, 1)
        return AgentAction(ActionKindV2.MOVE, 64 * self.direction)


def create_agent():
    return Agent()
"""


def _field(root: Path, ruleset_id: str, seeds: tuple[int, ...] = (1, 2)) -> tuple[Path, Path]:
    env = root / "env"
    for name in ("hunter_a", "hunter_b"):
        directory = env / "agents" / name
        if not directory.exists():
            directory.mkdir(parents=True)
            (directory / "agent.yaml").write_text(json.dumps({
                "name": name, "kind": "python", "api_version": 2, "entrypoint": "agent.py:create_agent",
                "version": "1.0.0"}), encoding="utf-8")
            (directory / "agent.py").write_text(HUNTER, encoding="utf-8")
    field = root / ruleset_id
    EvaluationService().run(EvaluationRequest(
        candidate_id="hunter_a", opponent_ids=["hunter_b"], seeds=seeds, ticks=TICKS, arena_size=512,
        ruleset_id=ruleset_id, output_dir=field / "arena_512" / "00-hunter_a", data_root=env))
    return field, env


@pytest.fixture(scope="module")
def traced(tmp_path_factory: pytest.TempPathFactory) -> dict[str, tuple[Path, list[TraceRecord]]]:
    root = tmp_path_factory.mktemp("e6-traces")
    out: dict[str, tuple[Path, list[TraceRecord]]] = {}
    for ruleset_id in (SENSING, CONTROL):
        field, env = _field(root, ruleset_id)
        out[ruleset_id] = (field, traces.trace_field(field, data_root=env, ticks=TICKS, arena_size=512,
                                                     expected_cells=4))
    return out


# ---------------------------------------------------------------------------
# Capture and binding
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("ruleset_id", [SENSING, CONTROL])
def test_every_completed_cell_is_traced_and_bound_to_its_evaluation(
    traced: dict[str, tuple[Path, list[TraceRecord]]], ruleset_id: str
) -> None:
    field, records = traced[ruleset_id]
    cells = {cell.schedule_id: cell for cell in traces.completed_cells(field)}
    assert len(records) == len(cells) == 4
    assert traces.read_index(field) == records
    for record in records:
        cell = cells[record.schedule_id]
        assert (record.match_id, record.result_id) == (cell.match_id, cell.result_id)
        assert record.replay_sha256 == hashlib.sha256(cell.replay_path.read_bytes()).hexdigest()
        assert (field / record.replay) == cell.replay_path
        assert (record.seat_a, record.seat_b) == cell.seats
        path = traces.trace_path_for(field, cell)
        raw = gzip.decompress(path.read_bytes())
        assert (len(raw), hashlib.sha256(raw).hexdigest(), path.stat().st_size) == (
            record.trace_bytes, record.trace_sha256, record.gz_bytes)
        # The trace's own binding record names the same match and replay.
        (binding,) = [r for r in traces.iter_trace(path) if r["record_type"] == "binding"]
        assert (binding["match_id"], binding["replay_sha256"]) == (record.match_id, record.replay_sha256)
        assert binding["ruleset_id"] == ruleset_id


def test_orientation_decides_the_seats(traced: dict[str, tuple[Path, list[TraceRecord]]]) -> None:
    field, _ = traced[SENSING]
    orientations = {(cell.orientation, cell.seats) for cell in traces.completed_cells(field)}
    assert orientations == {("candidate_first", ("hunter_a", "hunter_b")),
                            ("opponent_first", ("hunter_b", "hunter_a"))}


def test_a_changed_replay_fails_the_binding(tmp_path: Path) -> None:
    field, env = _field(tmp_path, SENSING, seeds=(1,))
    cell = traces.completed_cells(field)[0]
    cell.replay_path.write_bytes(cell.replay_path.read_bytes() + b"\n")
    with pytest.raises(TraceBindingError, match="replay_sha256"):
        traces.trace_cell(cell, field_root=field, data_root=env, ticks=TICKS, arena_size=512, scratch=tmp_path / "s")
    assert not traces.trace_path_for(field, cell).exists()


@pytest.mark.parametrize("name", ["match_id", "result_id"])
def test_a_changed_identity_fails_the_binding(tmp_path: Path, name: str) -> None:
    field, env = _field(tmp_path, SENSING, seeds=(1,))
    cell = replace(traces.completed_cells(field)[0], **{name: "tampered"})
    with pytest.raises(TraceBindingError, match=name):
        traces.trace_cell(cell, field_root=field, data_root=env, ticks=TICKS, arena_size=512, scratch=tmp_path / "s")


def test_a_different_tick_limit_fails_the_binding(tmp_path: Path) -> None:
    field, env = _field(tmp_path, SENSING, seeds=(2,))
    cell = traces.completed_cells(field)[0]
    with pytest.raises(TraceBindingError):
        traces.trace_cell(cell, field_root=field, data_root=env, ticks=TICKS - 1, arena_size=512,
                          scratch=tmp_path / "s")


def test_a_missing_cell_fails_the_field_count(tmp_path: Path) -> None:
    field, env = _field(tmp_path, SENSING, seeds=(1,))
    with pytest.raises(TraceBindingError, match="expected"):
        traces.trace_field(field, data_root=env, ticks=TICKS, arena_size=512, expected_cells=3)


def test_compression_is_atomic_and_deterministic(tmp_path: Path) -> None:
    source = tmp_path / "trace.jsonl"
    source.write_bytes(b'{"record_type": "header"}\n' * 1000)
    first, second = tmp_path / "a" / "t.gz", tmp_path / "b" / "t.gz"
    assert traces.gzip_atomically(source, first) == first.stat().st_size
    traces.gzip_atomically(source, second)
    assert first.read_bytes() == second.read_bytes()
    assert gzip.decompress(first.read_bytes()) == source.read_bytes()
    assert sorted(p.name for p in first.parent.iterdir()) == ["t.gz"]  # no temporary left behind


# ---------------------------------------------------------------------------
# Size accounting and the retention rule (plan Sec 6.3)
# ---------------------------------------------------------------------------


def _record(seed: int, gz: int, raw: int = 10) -> TraceRecord:
    return TraceRecord(schedule_id=f"cell-{seed}", request="00-x", artifact=f"m{seed}", seed=seed, seat_a="a",
                       seat_b="b", replay="r", replay_sha256="0", match_id="m", result_id="r", trace_sha256="0",
                       trace_bytes=raw, gz_bytes=gz)


def test_the_retention_threshold_is_forty_gigabytes_exclusive() -> None:
    assert TRACE_RETENTION_LIMIT_BYTES == 40 * 10**9
    assert traces.retention_rule(40 * 10**9) == "all"
    assert traces.retention_rule(40 * 10**9 + 1) == "subset"


def test_the_projection_scales_the_measured_mean_to_the_matrix() -> None:
    report = traces.size_report([_record(1, 3_000_000, 24_000_000), _record(2, 5_000_000, 40_000_000)],
                                matrix_cells=11_520)
    assert report["projected_gz_bytes"] == 8_000_000 * 11_520 // 2 == 46_080_000_000
    assert report["mean_gz_bytes"] == 4_000_000
    assert report["compression_ratio"] == 8
    assert report["retention"] == "subset"
    # 3 MB a cell projects to 34.56 GB: every raw trace is kept.
    assert traces.size_report([_record(1, 3_000_000)], matrix_cells=11_520)["retention"] == "all"
    with pytest.raises(ValueError):
        traces.size_report([], matrix_cells=11_520)


def test_the_subset_is_seed_positions_one_to_four_of_the_ordered_list() -> None:
    assert SUBSET_SEED_POSITIONS == (1, 2, 3, 4)
    ordered = [907, 13, 55, 2, 71, 4]
    assert [traces.retained(seed, ordered, "subset") for seed in ordered] == [True, True, True, True, False, False]
    assert all(traces.retained(seed, ordered, "all") for seed in ordered)
    with pytest.raises(ValueError):
        traces.retained(907, ordered, "none")


def test_retention_deletes_only_the_traces_the_rule_drops(tmp_path: Path) -> None:
    records = [_record(seed, 1) for seed in (5, 6, 7, 8, 9)]
    for record in records:
        path = tmp_path / traces.TRACES_DIR / record.request / record.artifact / traces.TRACE_NAME
        path.parent.mkdir(parents=True)
        path.write_bytes(b"x")
    removed = traces.apply_retention(tmp_path, records, [5, 6, 7, 8, 9], "subset")
    assert removed == ["cell-9"]
    kept = sorted(p.parent.name for p in (tmp_path / traces.TRACES_DIR).rglob(traces.TRACE_NAME))
    assert kept == ["m5", "m6", "m7", "m8"]


# ---------------------------------------------------------------------------
# The extractor on synthetic traces
# ---------------------------------------------------------------------------

BASE = {"A": 100, "B": 300}


def _decision(entrant: str, tick: int, kind: str | None, operand: int | None = None, *, anchor: int | None = None,
              visible: tuple[int, ...] = (), status: str = "APPLIED", address: int | None = None,
              read: tuple[int, str | None] | None = None, process: str = "p") -> dict[str, Any]:
    return {
        "record_type": "decision_v2", "agent_id": entrant, "process_id": process, "wall_time_ms": 1.0,
        "observation": {"current_tick": tick, "own_core_base": BASE[entrant],
                        "self_anchor": BASE[entrant] if anchor is None else anchor,
                        "visible_enemy_anchor_addresses": list(visible)},
        "action": None if kind is None else {"kind": kind, "operand": operand, "value": 1 if kind == "write" else None},
        "applied_result": {"status": status, "normalized_address": operand if address is None else address,
                           "read_value": None if read is None else read[0],
                           "read_owner": None if read is None else read[1]},
        "diagnostic": None,
    }


HEADER = {"record_type": "header", "agents": {"A": "x", "B": "y"}, "match_seed": 1}
START = TickZero(core_base=BASE, anchors={"A": {"p": 100}, "B": {"p": 300}})


def _extract(*decisions: dict[str, Any]) -> telemetry.Extraction:
    return extract([HEADER, *decisions], arena=512, start=START)


def test_rows_follow_execution_order_with_a_per_entrant_callback_index() -> None:
    result = _extract(_decision("A", 1, "move", 64, address=164), _decision("A", 1, "read", 5),
                      _decision("B", 1, "read", 5), _decision("A", 2, "read", 5), _decision("A", 2, "read", 6))
    column = ROW_FIELDS.index("index")
    assert [(row[0], row[1], row[column]) for row in result.rows] == [
        (1, "A", 1), (1, "A", 2), (1, "B", 1), (2, "A", 1), (2, "A", 2)]
    assert len(ROW_FIELDS) == len(result.rows[0]) == 13
    assert "wall_time_ms" not in json.dumps(result.rows)


def test_detection_moves_and_reads_are_classified() -> None:
    result = _extract(
        _decision("A", 1, "move", 64, address=164),                   # off-core, pre-detection
        _decision("A", 1, "move", 64, anchor=164, address=228),       # pre-detection, already off-core
        _decision("B", 1, "read", 305),                               # own core: not a probe
        _decision("B", 1, "read", 90),                                # probe
        _decision("A", 2, "move", -1, anchor=228, visible=(300,), address=227),  # after detection
        _decision("A", 2, "move", 4, anchor=103, visible=(300,), address=107),   # stays on core
        _decision("A", 2, "move", 64, status="REJECTED_OUT_OF_REACH", address=None),
    )
    summary = result.summary
    assert summary["pre_detection_moves"] == {"A": 2, "B": 0}
    assert summary["off_core_moves"] == {"A": 1, "B": 0}
    assert summary["probe_reads"] == {"A": 0, "B": 1}
    assert summary["first_detection"] == {"A": [2, 4], "B": None}
    assert summary["saw_first"] == "A"
    assert summary["core_base"] == BASE


def test_a_read_of_the_opponents_core_is_information_from_the_next_row() -> None:
    result = _extract(
        _decision("A", 1, "read", 302, read=(0xCE, "B")),   # information: counts from the next row
        _decision("A", 1, "read", 303, read=(0xCE, "A")),   # own write there: not information
        _decision("A", 1, "read", 90, read=(0xCE, "B")),    # not a core cell of B
    )
    assert result.summary["first_information"] == {"A": [1, 0], "B": None}
    assert result.summary["first_detection"] == {"A": None, "B": None}
    assert result.summary["information_ticks"] == {"A": [[1, 1]], "B": []}


def test_d4_writes_record_whether_information_came_first() -> None:
    result = _extract(
        _decision("A", 1, "write", 301),                                 # blind: not informed
        _decision("B", 1, "write", 100, visible=(100,)),                 # sees A's anchor at this callback
        _decision("A", 1, "read", 302, read=(0xCE, "B")),
        _decision("A", 2, "write", 303),                                 # informed by the READ above
        _decision("A", 3, "write", 304),                                 # tick 3: outside D-4's window
        _decision("A", 2, "write", 200),                                 # not a core cell of B
    )
    assert result.summary["d4_writes"] == [
        {"order": 0, "tick": 1, "entrant": "A", "address": 301, "informed": False},
        {"order": 1, "tick": 1, "entrant": "B", "address": 100, "informed": True},
        {"order": 3, "tick": 2, "entrant": "A", "address": 303, "informed": True},
    ]


def test_an_entrant_captured_before_its_first_callback_is_still_summarized() -> None:
    result = _extract(*[_decision("A", 1, "write", 300 + i, visible=(300,)) for i in range(8)])
    assert result.summary["core_base"] == BASE
    assert result.summary["tick0_anchors"] == {"A": {"p": 100}, "B": {"p": 300}}
    assert result.summary["first_detection"] == {"A": [1, 0], "B": None}
    assert result.summary["callbacks"] == 8


def test_an_observation_that_disagrees_with_the_replay_core_is_rejected() -> None:
    bad = _decision("A", 1, "read", 5)
    bad["observation"]["own_core_base"] = 101
    with pytest.raises(TelemetryError, match="own_core_base"):
        _extract(bad)


def test_a_trace_without_a_header_is_rejected() -> None:
    with pytest.raises(TelemetryError, match="header"):
        extract([_decision("A", 1, "read", 5)], arena=512, start=START)


# ---------------------------------------------------------------------------
# The extractor on real traces
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("ruleset_id", [SENSING, CONTROL])
def test_field_telemetry_is_deterministic_and_complete(
    traced: dict[str, tuple[Path, list[TraceRecord]]], ruleset_id: str
) -> None:
    field, records = traced[ruleset_id]
    telemetry.telemetry_field(field, records, arena=512)
    digest = telemetry.summaries_digest(field)
    stored = {record.schedule_id: telemetry.read_callbacks(field, record) for record in records}
    telemetry.telemetry_field(field, records, arena=512)
    assert telemetry.summaries_digest(field) == digest
    lines = telemetry.read_summaries(field)
    assert [line["schedule_id"] for line in lines] == sorted(record.schedule_id for record in records)
    for record, line in zip(sorted(records, key=lambda r: r.schedule_id), lines, strict=True):
        rows = telemetry.read_callbacks(field, record)
        assert rows == stored[record.schedule_id]
        assert line["rows_sha256"] == hashlib.sha256(telemetry.rows_bytes(rows)).hexdigest()
        decisions = [r for r in traces.iter_trace(traces.trace_path_for(field, _cell(field, record)))
                     if r["record_type"] == "decision_v2"]
        assert len(rows) == len(decisions) == line["summary"]["callbacks"]
        assert line["summary"]["binding"] == {"match_id": record.match_id, "replay_sha256": record.replay_sha256}
        assert line["summary"]["declarations"] == {"A": [["p", 256, 1.0]], "B": [["p", 256, 1.0]]}


def _cell(field: Path, record: TraceRecord) -> traces.CellRef:
    (cell,) = [cell for cell in traces.completed_cells(field) if cell.schedule_id == record.schedule_id]
    return cell


@pytest.mark.parametrize("name", ["match_id", "replay_sha256"])
def test_a_trace_whose_binding_record_disagrees_with_its_cell_is_rejected(
    traced: dict[str, tuple[Path, list[TraceRecord]]], name: str
) -> None:
    field, records = traced[SENSING]
    with pytest.raises(TelemetryError, match="binding"):
        telemetry.telemetry_cell(field, replace(records[0], **{name: "tampered"}), arena=512)


def test_the_control_shows_every_anchor_from_the_first_callback(
    traced: dict[str, tuple[Path, list[TraceRecord]]]
) -> None:
    # Under the parent (reach 256) both hunters see each other at their
    # first callback; the summaries record it. A mechanical property of the
    # scripted agents, not an outcome.
    field, records = traced[CONTROL]
    telemetry.telemetry_field(field, records, arena=512)
    for line in telemetry.read_summaries(field):
        first = line["summary"]["first_detection"]
        assert all(value is not None and value[0] == 1 for value in first.values() if value is not None)
        assert line["summary"]["pre_detection_moves"] == {"A": 0, "B": 0}


def test_telemetry_survives_retention_of_the_raw_trace(traced: dict[str, tuple[Path, list[TraceRecord]]]) -> None:
    field, records = traced[SENSING]
    telemetry.telemetry_field(field, records, arena=512)
    before = {record.schedule_id: telemetry.read_callbacks(field, record) for record in records}
    removed = traces.apply_retention(field, records, [2, 1], "subset")
    assert removed == []  # both seeds sit in positions 1-4
    for record in records:
        assert telemetry.read_callbacks(field, record) == before[record.schedule_id]
