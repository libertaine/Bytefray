from __future__ import annotations

import dataclasses
from pathlib import Path

import pytest
from _agent_trace_v2_fixtures import decision, standard_decisions, write_trace_v2
from battle_engine.agent_trace import (
    ABSENT,
    CallbackKey,
    DecisionRecord,
    ResetRecord,
    TraceAction,
    TraceDiagnostic,
    TraceDocument,
    TraceDocumentV2,
    TraceFormatError,
    TraceHeader,
    TraceObservation,
    TraceVersionError,
    TraceWriter,
    callback_keys,
    first_divergence,
    first_divergence_v2,
    read_any_trace,
    read_trace,
    read_trace_v2,
    trace_schema_version,
)


def _write_sample(path: Path, *, action_value: int = 165) -> None:
    with TraceWriter(path) as writer:
        writer.write_header(
            TraceHeader(match_seed=1337, agents={"A": "a", "B": "b"}, supervised=True, agent_call_timeout=5.0)
        )
        writer.write_reset(ResetRecord(agent_id="A", wall_time_ms=1.5, diagnostic=None))
        writer.write_decision(
            DecisionRecord(
                tick=1,
                agent_id="A",
                action_slot=0,
                wall_time_ms=0.2,
                observation=TraceObservation(
                    tick=1, agent_id="A", pc=0, register_a=0, register_p=0,
                    zero_flag=False, last_read=None, alive=True,
                ),
                action=TraceAction(kind="write", operand=10, value=action_value),
                diagnostic=None,
            )
        )


def test_round_trip_write_then_read(tmp_path: Path) -> None:
    path = tmp_path / "trace.jsonl"
    _write_sample(path)

    document = read_trace(path)

    assert document.header.match_seed == 1337
    assert document.header.agents == {"A": "a", "B": "b"}
    assert document.header.supervised is True
    assert document.header.agent_call_timeout == 5.0
    assert len(document.resets) == 1
    assert len(document.decisions) == 1
    decision = document.decisions[0]
    assert decision.tick == 1
    assert decision.agent_id == "A"
    assert decision.action == TraceAction(kind="write", operand=10, value=165)
    assert decision.diagnostic is None


def test_writer_flushes_each_line_immediately(tmp_path: Path) -> None:
    path = tmp_path / "trace.jsonl"
    writer = TraceWriter(path)
    writer.write_header(TraceHeader(match_seed=1, agents={}, supervised=False))
    # No close() yet -- a reader opening the file now must already see the
    # header, proving each write is flushed rather than buffered until close.
    lines = path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    writer.close()


def test_decision_with_diagnostic_has_no_action(tmp_path: Path) -> None:
    path = tmp_path / "trace.jsonl"
    with TraceWriter(path) as writer:
        writer.write_header(TraceHeader(match_seed=1, agents={"A": "a"}, supervised=True, agent_call_timeout=5.0))
        writer.write_decision(
            DecisionRecord(
                tick=3,
                agent_id="A",
                action_slot=0,
                wall_time_ms=5000.0,
                observation=TraceObservation(
                    tick=3, agent_id="A", pc=0, register_a=0, register_p=0,
                    zero_flag=False, last_read=None, alive=True,
                ),
                action=None,
                diagnostic=TraceDiagnostic(
                    code="agent_action_timeout", stage="action",
                    message="Python agent A act() did not return within 5s.",
                    agent_id="A", slot=0, tick=3, action_slot=0,
                ),
            )
        )

    document = read_trace(path)
    decision = document.decisions[0]
    assert decision.action is None
    assert decision.diagnostic is not None
    assert decision.diagnostic.code == "agent_action_timeout"
    assert document.failures() == (decision,)


def test_missing_header_raises_trace_format_error(tmp_path: Path) -> None:
    path = tmp_path / "trace.jsonl"
    path.write_text('{"record_type": "reset", "agent_id": "A", "wall_time_ms": 1.0}\n', encoding="utf-8")

    with pytest.raises(TraceFormatError, match="missing header"):
        read_trace(path)


def test_malformed_json_line_raises_trace_format_error(tmp_path: Path) -> None:
    path = tmp_path / "trace.jsonl"
    path.write_text(
        '{"schema": "bytefray.agent_trace", "schema_version": 1, "record_type": "header", '
        '"match_seed": 1, "agents": {}, "supervised": false}\n'
        "{not valid json\n",
        encoding="utf-8",
    )

    with pytest.raises(TraceFormatError, match="invalid JSON"):
        read_trace(path)


def test_unknown_record_type_raises_trace_format_error(tmp_path: Path) -> None:
    path = tmp_path / "trace.jsonl"
    path.write_text(
        '{"schema": "bytefray.agent_trace", "schema_version": 1, "record_type": "header", '
        '"match_seed": 1, "agents": {}, "supervised": false}\n'
        '{"record_type": "mystery"}\n',
        encoding="utf-8",
    )

    with pytest.raises(TraceFormatError, match="unknown record_type"):
        read_trace(path)


def test_unsupported_schema_version_raises_trace_format_error(tmp_path: Path) -> None:
    path = tmp_path / "trace.jsonl"
    path.write_text(
        '{"schema": "bytefray.agent_trace", "schema_version": 99, "record_type": "header", '
        '"match_seed": 1, "agents": {}, "supervised": false}\n',
        encoding="utf-8",
    )

    with pytest.raises(TraceFormatError, match="schema version"):
        read_trace(path)


def test_truncated_final_line_raises_actionable_trace_format_error(tmp_path: Path) -> None:
    """Documents the deliberate durability/tolerance decision for a trace
    that was interrupted mid-write (e.g. the writing process was killed):
    TraceWriter's flush-per-record discipline means a genuinely truncated
    file always ends with a syntactically incomplete trailing fragment,
    never a torn earlier record (see TraceWriter's docstring). read_trace
    treats that trailing fragment as a hard, precisely-located parse
    error rather than silently dropping it -- a loud "corrupt at line N"
    is more useful for a debugging artifact than quietly losing data the
    author might have needed. This is the chosen alternative to silent
    truncation tolerance; if that decision changes, this test should
    change with it.
    """

    path = tmp_path / "trace.jsonl"
    path.write_text(
        '{"schema": "bytefray.agent_trace", "schema_version": 1, "record_type": "header", '
        '"match_seed": 1, "agents": {}, "supervised": false}\n'
        '{"record_type": "decision", "tick": 3, "agent_id": "A", "action_sl',  # cut mid-write
        encoding="utf-8",
    )

    with pytest.raises(TraceFormatError, match=r"trace\.jsonl:2.*invalid JSON"):
        read_trace(path)


def test_missing_required_field_raises_trace_format_error(tmp_path: Path) -> None:
    path = tmp_path / "trace.jsonl"
    path.write_text(
        '{"schema": "bytefray.agent_trace", "schema_version": 1, "record_type": "header", '
        '"match_seed": 1, "agents": {}, "supervised": false}\n'
        '{"record_type": "decision", "tick": 1, "agent_id": "A"}\n',
        encoding="utf-8",
    )

    with pytest.raises(TraceFormatError, match="missing required field"):
        read_trace(path)


def test_nonexistent_file_raises_trace_format_error(tmp_path: Path) -> None:
    with pytest.raises(TraceFormatError, match="not found"):
        read_trace(tmp_path / "does_not_exist.jsonl")


def test_tick_range_and_query_helpers(tmp_path: Path) -> None:
    path = tmp_path / "trace.jsonl"
    with TraceWriter(path) as writer:
        writer.write_header(TraceHeader(match_seed=1, agents={"A": "a", "B": "b"}, supervised=False))
        for tick in (1, 2, 3):
            for agent_id in ("A", "B"):
                writer.write_decision(
                    DecisionRecord(
                        tick=tick, agent_id=agent_id, action_slot=0, wall_time_ms=0.1,
                        observation=TraceObservation(
                            tick=tick, agent_id=agent_id, pc=0, register_a=0, register_p=0,
                            zero_flag=False, last_read=None, alive=True,
                        ),
                        action=TraceAction(kind="nop"),
                        diagnostic=None,
                    )
                )

    document = read_trace(path)
    assert document.tick_range() == (1, 3)
    assert len(document.for_tick(2)) == 2
    assert len(document.for_agent("A")) == 3
    assert len(document.around_tick(2, 1)) == 6  # ticks 1-3, both agents


def test_first_divergence_none_for_identical_traces(tmp_path: Path) -> None:
    path_a = tmp_path / "a.jsonl"
    path_b = tmp_path / "b.jsonl"
    _write_sample(path_a)
    _write_sample(path_b)

    assert first_divergence(read_trace(path_a), read_trace(path_b)) is None


def test_first_divergence_finds_differing_action(tmp_path: Path) -> None:
    path_a = tmp_path / "a.jsonl"
    path_b = tmp_path / "b.jsonl"
    _write_sample(path_a, action_value=165)
    _write_sample(path_b, action_value=200)

    divergence = first_divergence(read_trace(path_a), read_trace(path_b))

    assert divergence is not None
    assert divergence.tick == 1
    assert divergence.agent_id == "A"
    assert divergence.reason == "action/diagnostic differ"
    assert divergence.record_a is not None and divergence.record_a.action is not None
    assert divergence.record_a.action.value == 165
    assert divergence.record_b is not None and divergence.record_b.action is not None
    assert divergence.record_b.action.value == 200


def test_first_divergence_ignores_wall_time_only_differences(tmp_path: Path) -> None:
    """Divergence semantics audit (continuation-phase item 11): two traces
    that recorded the identical decision but took different wall-clock
    time to get there must never be reported as behaviorally diverged --
    ``wall_time_ms`` is timing noise, not a behavioral fact, and
    ``first_divergence`` only compares ``action``/``diagnostic``.
    """

    path_a = tmp_path / "a.jsonl"
    path_b = tmp_path / "b.jsonl"
    with TraceWriter(path_a) as writer:
        writer.write_header(TraceHeader(match_seed=1, agents={"A": "a"}, supervised=True, agent_call_timeout=5.0))
        writer.write_decision(
            DecisionRecord(
                tick=1, agent_id="A", action_slot=0, wall_time_ms=0.05,
                observation=TraceObservation(
                    tick=1, agent_id="A", pc=0, register_a=0, register_p=0,
                    zero_flag=False, last_read=None, alive=True,
                ),
                action=TraceAction(kind="nop"), diagnostic=None,
            )
        )
    with TraceWriter(path_b) as writer:
        writer.write_header(TraceHeader(match_seed=1, agents={"A": "a"}, supervised=True, agent_call_timeout=5.0))
        writer.write_decision(
            DecisionRecord(
                tick=1, agent_id="A", action_slot=0, wall_time_ms=4321.9,
                observation=TraceObservation(
                    tick=1, agent_id="A", pc=0, register_a=0, register_p=0,
                    zero_flag=False, last_read=None, alive=True,
                ),
                action=TraceAction(kind="nop"), diagnostic=None,
            )
        )

    assert first_divergence(read_trace(path_a), read_trace(path_b)) is None


def test_first_divergence_finds_action_vs_diagnostic(tmp_path: Path) -> None:
    """One trace succeeded (an action) where the other failed (a
    diagnostic) at the same (tick, agent, slot) key -- this must be
    reported as a divergence even though both records are otherwise
    well-formed and present."""

    path_a = tmp_path / "a.jsonl"
    path_b = tmp_path / "b.jsonl"
    with TraceWriter(path_a) as writer:
        writer.write_header(TraceHeader(match_seed=1, agents={"A": "a"}, supervised=True, agent_call_timeout=5.0))
        writer.write_decision(
            DecisionRecord(
                tick=1, agent_id="A", action_slot=0, wall_time_ms=0.1,
                observation=TraceObservation(
                    tick=1, agent_id="A", pc=0, register_a=0, register_p=0,
                    zero_flag=False, last_read=None, alive=True,
                ),
                action=TraceAction(kind="nop"), diagnostic=None,
            )
        )
    with TraceWriter(path_b) as writer:
        writer.write_header(TraceHeader(match_seed=1, agents={"A": "a"}, supervised=True, agent_call_timeout=5.0))
        writer.write_decision(
            DecisionRecord(
                tick=1, agent_id="A", action_slot=0, wall_time_ms=5000.0,
                observation=TraceObservation(
                    tick=1, agent_id="A", pc=0, register_a=0, register_p=0,
                    zero_flag=False, last_read=None, alive=True,
                ),
                action=None,
                diagnostic=TraceDiagnostic(
                    code="agent_action_timeout", stage="action",
                    message="Python agent A act() did not return within 5s.",
                ),
            )
        )

    divergence = first_divergence(read_trace(path_a), read_trace(path_b))

    assert divergence is not None
    assert divergence.tick == 1
    assert divergence.reason == "action/diagnostic differ"
    assert divergence.record_a is not None and divergence.record_a.action is not None
    assert divergence.record_b is not None and divergence.record_b.diagnostic is not None


def test_first_divergence_ignores_header_agent_metadata_differences(tmp_path: Path) -> None:
    """Header metadata (agent display names, supervised flag, timeout) is
    run configuration, not a behavioral fact about decisions -- two traces
    with different header agent names but identical decisions must not be
    reported as diverged.
    """

    path_a = tmp_path / "a.jsonl"
    path_b = tmp_path / "b.jsonl"
    with TraceWriter(path_a) as writer:
        writer.write_header(
            TraceHeader(match_seed=1, agents={"A": "my_agent"}, supervised=True, agent_call_timeout=5.0)
        )
        writer.write_decision(
            DecisionRecord(
                tick=1, agent_id="A", action_slot=0, wall_time_ms=0.1,
                observation=TraceObservation(
                    tick=1, agent_id="A", pc=0, register_a=0, register_p=0,
                    zero_flag=False, last_read=None, alive=True,
                ),
                action=TraceAction(kind="nop"), diagnostic=None,
            )
        )
    with TraceWriter(path_b) as writer:
        writer.write_header(
            TraceHeader(match_seed=99, agents={"A": "a_completely_different_name"}, supervised=False)
        )
        writer.write_decision(
            DecisionRecord(
                tick=1, agent_id="A", action_slot=0, wall_time_ms=0.1,
                observation=TraceObservation(
                    tick=1, agent_id="A", pc=0, register_a=0, register_p=0,
                    zero_flag=False, last_read=None, alive=True,
                ),
                action=TraceAction(kind="nop"), diagnostic=None,
            )
        )

    assert first_divergence(read_trace(path_a), read_trace(path_b)) is None


def test_first_divergence_reports_length_mismatch(tmp_path: Path) -> None:
    path_a = tmp_path / "a.jsonl"
    path_b = tmp_path / "b.jsonl"
    with TraceWriter(path_a) as writer:
        writer.write_header(TraceHeader(match_seed=1, agents={"A": "a"}, supervised=False))
        for tick in (1, 2):
            writer.write_decision(
                DecisionRecord(
                    tick=tick, agent_id="A", action_slot=0, wall_time_ms=0.1,
                    observation=TraceObservation(
                        tick=tick, agent_id="A", pc=0, register_a=0, register_p=0,
                        zero_flag=False, last_read=None, alive=True,
                    ),
                    action=TraceAction(kind="nop"), diagnostic=None,
                )
            )
    with TraceWriter(path_b) as writer:
        writer.write_header(TraceHeader(match_seed=1, agents={"A": "a"}, supervised=False))
        writer.write_decision(
            DecisionRecord(
                tick=1, agent_id="A", action_slot=0, wall_time_ms=0.1,
                observation=TraceObservation(
                    tick=1, agent_id="A", pc=0, register_a=0, register_p=0,
                    zero_flag=False, last_read=None, alive=True,
                ),
                action=TraceAction(kind="nop"), diagnostic=None,
            )
        )

    divergence = first_divergence(read_trace(path_a), read_trace(path_b))

    assert divergence is not None
    assert divergence.tick == 2
    assert divergence.reason == "one trace is missing this decision"
    assert divergence.record_a is not None
    assert divergence.record_b is None


# ---------------------------------------------------------------------------
# Version-aware reading and schema-2 divergence (issue #10)
# ---------------------------------------------------------------------------

_V1_HEADER = (
    '{"schema": "bytefray.agent_trace", "schema_version": 1, "record_type": "header", '
    '"match_seed": 1, "agents": {"A": "a"}, "supervised": false}\n'
)
_V2_HEADER = _V1_HEADER.replace('"schema_version": 1', '"schema_version": 2')


def test_read_any_trace_dispatches_schema_1_to_the_v1_reader(tmp_path: Path) -> None:
    path = tmp_path / "trace.jsonl"
    _write_sample(path)

    document = read_any_trace(path)

    assert isinstance(document, TraceDocument)
    assert document == read_trace(path)
    assert trace_schema_version(path) == 1


def test_read_any_trace_dispatches_schema_2_to_the_v2_reader(tmp_path: Path) -> None:
    path = write_trace_v2(tmp_path / "trace.jsonl", standard_decisions())

    document = read_any_trace(path)

    assert isinstance(document, TraceDocumentV2)
    assert document == read_trace_v2(path)
    assert trace_schema_version(path) == 2


def test_header_without_version_keeps_the_historical_schema_1_default(tmp_path: Path) -> None:
    path = tmp_path / "trace.jsonl"
    path.write_text(
        '{"record_type": "header", "match_seed": 1, "agents": {}, "supervised": false}\n',
        encoding="utf-8",
    )

    assert isinstance(read_any_trace(path), TraceDocument)


@pytest.mark.parametrize("version", [0, 3, 99, -1])
def test_unsupported_schema_version_raises_version_error(tmp_path: Path, version: int) -> None:
    path = tmp_path / "trace.jsonl"
    path.write_text(
        _V1_HEADER.replace('"schema_version": 1', f'"schema_version": {version}'), encoding="utf-8"
    )

    with pytest.raises(TraceVersionError, match=r"supported: 1, 2"):
        read_any_trace(path)


@pytest.mark.parametrize(
    ("content", "message"),
    [
        ("", "missing header"),
        ("\n\n", "missing header"),
        ("not json\n", "invalid JSON"),
        ("[1, 2]\n", "must be a JSON object"),
        (
            '{"record_type": "reset", "agent_id": "A", "wall_time_ms": 1.0}\n' + _V1_HEADER,
            "missing header",
        ),
        (_V1_HEADER.replace('"bytefray.agent_trace"', '"other.trace"'), "unsupported trace schema"),
        (_V1_HEADER.replace('"schema_version": 1', '"schema_version": "2"'), "must be an integer"),
        (_V1_HEADER.replace('"schema_version": 1', '"schema_version": true'), "must be an integer"),
        (_V1_HEADER.replace('"schema_version": 1', '"schema_version": 2.0'), "must be an integer"),
        (_V1_HEADER.replace('"supervised": false', '"supervised": false, "agent_call_timeout": "5"'),
         "'agent_call_timeout' must be a number"),
    ],
)
def test_malformed_headers_are_rejected(tmp_path: Path, content: str, message: str) -> None:
    path = tmp_path / "trace.jsonl"
    path.write_text(content, encoding="utf-8")

    with pytest.raises(TraceFormatError, match=message) as excinfo:
        read_any_trace(path)
    assert not isinstance(excinfo.value, TraceVersionError)


def test_no_fallback_between_schema_readers(tmp_path: Path) -> None:
    v1_record = (
        '{"record_type": "decision", "tick": 1, "agent_id": "A", "action_slot": 0, '
        '"wall_time_ms": 0.1, "observation": {"tick": 1, "agent_id": "A", "pc": 0, '
        '"register_a": 0, "register_p": 0, "zero_flag": false, "alive": true}}\n'
    )
    v2_header_with_v1_record = tmp_path / "v2.jsonl"
    v2_header_with_v1_record.write_text(_V2_HEADER + v1_record, encoding="utf-8")
    with pytest.raises(TraceFormatError, match="unexpected V1 'decision' record"):
        read_any_trace(v2_header_with_v1_record)

    v2_path = write_trace_v2(tmp_path / "real_v2.jsonl", standard_decisions()[:1])
    v2_lines = v2_path.read_text(encoding="utf-8").splitlines()
    v1_header_with_v2_records = tmp_path / "v1.jsonl"
    v1_header_with_v2_records.write_text(_V1_HEADER + "\n".join(v2_lines[1:]) + "\n", encoding="utf-8")
    with pytest.raises(TraceFormatError, match="unknown record_type"):
        read_any_trace(v1_header_with_v2_records)


@pytest.mark.parametrize(
    ("record", "message"),
    [
        ('{"record_type": "binding", "replay_sha256": "x"}\n', "malformed schema-1 trace record"),
        (
            (
                '{"record_type": "decision", "tick": "3", "agent_id": "A", "action_slot": 0, '
                '"wall_time_ms": 0.1, "observation": {"tick": 1, "agent_id": "A", "pc": 0, '
                '"register_a": 0, "register_p": 0, "zero_flag": false, "alive": true}}\n'
            ),
            "'tick' and 'action_slot' must be integers",
        ),
    ],
)
def test_malformed_schema_1_records_raise_trace_format_error(
    tmp_path: Path, record: str, message: str
) -> None:
    path = tmp_path / "trace.jsonl"
    path.write_text(_V1_HEADER + record, encoding="utf-8")

    with pytest.raises(TraceFormatError, match=message):
        read_any_trace(path)


@pytest.mark.parametrize(
    ("needle", "replacement", "message"),
    [
        ('"current_tick": 1', '"current_tick": "1"', "current_tick' must be an integer"),
        (
            '"visible_enemy_anchor_addresses": []',
            '"visible_enemy_anchor_addresses": "12"',
            "visible_enemy_anchor_addresses' must be integers",
        ),
        (
            '"process_id": "main", "record_type": "decision_v2"',
            '"process_id": 7, "record_type": "decision_v2"',
            "'agent_id' and 'process_id' must be strings",
        ),
        ('"wall_time_ms": 0.25', '"wall_time_ms": "slow"', "malformed schema-2 trace record"),
        ('"sensing_window": 27', '"sensing_window": "wide"', "'sensing_window' must be an integer or null"),
        ('"status": "APPLIED"', '"statuz": "APPLIED"', "missing required field 'status'"),
        ('"replay_sha256"', '"replay_sha"', "missing required field 'replay_sha256'"),
        ('"entrant_identities": ["A", "B"]', '"entrant_identities": [1, 2]', "binding fields must be strings"),
        ('"ruleset_id": "bytefray-rules-6-alpha1"', '"ruleset_id": 6', "binding fields must be strings"),
        ('"agents": {"A": "alpha", "B": "bravo"}', '"agents": [[1, "a"], ["b", "c"]]', "'agents' must map"),
        ('"agents": {"A": "alpha", "B": "bravo"}', '"agents": {"A": 5}', "'agents' must map"),
    ],
)
def test_malformed_schema_2_records_raise_trace_format_error(
    tmp_path: Path, needle: str, replacement: str, message: str
) -> None:
    path = write_trace_v2(tmp_path / "trace.jsonl", standard_decisions()[:1])
    good = path.read_text(encoding="utf-8")
    assert needle in good
    path.write_text(good.replace(needle, replacement, 1), encoding="utf-8")

    with pytest.raises(TraceFormatError, match=message):
        read_any_trace(path)


def test_deeply_nested_json_is_a_trace_format_error(tmp_path: Path) -> None:
    nested = "[" * 100_000 + "]" * 100_000
    as_header = tmp_path / "header.jsonl"
    as_header.write_text(nested + "\n", encoding="utf-8")
    as_record = tmp_path / "record.jsonl"
    as_record.write_text(_V2_HEADER + nested + "\n", encoding="utf-8")

    for path in (as_header, as_record):
        with pytest.raises(TraceFormatError):
            read_any_trace(path)


def test_callback_keys_number_repeated_process_callbacks_within_a_tick() -> None:
    records = (
        decision(1, "A"),
        decision(1, "A"),
        decision(1, "B"),
        decision(1, "A", "scout"),
        decision(1, "A"),
        decision(2, "A"),
    )

    assert callback_keys(records) == (
        CallbackKey(1, "A", "main", 1),
        CallbackKey(1, "A", "main", 2),
        CallbackKey(1, "B", "main", 1),
        CallbackKey(1, "A", "scout", 1),
        CallbackKey(1, "A", "main", 3),
        CallbackKey(2, "A", "main", 1),
    )


def _divergence(tmp_path: Path, decisions_a, decisions_b):
    path_a = write_trace_v2(tmp_path / "a.jsonl", decisions_a)
    path_b = write_trace_v2(tmp_path / "b.jsonl", decisions_b)
    document_a, document_b = read_any_trace(path_a), read_any_trace(path_b)
    assert isinstance(document_a, TraceDocumentV2) and isinstance(document_b, TraceDocumentV2)
    return first_divergence_v2(document_a, document_b)


def test_v2_identical_traces_have_no_divergence(tmp_path: Path) -> None:
    assert _divergence(tmp_path, standard_decisions(), standard_decisions()) is None


def test_v2_changed_action_reports_its_exact_callback(tmp_path: Path) -> None:
    changed = standard_decisions()
    action = changed[6].action
    assert action is not None
    changed[6] = dataclasses.replace(changed[6], action=dataclasses.replace(action, operand=999))

    divergence = _divergence(tmp_path, standard_decisions(), changed)

    assert divergence is not None
    assert divergence.position == 7
    assert divergence.key_a == divergence.key_b == CallbackKey(2, "B", "main", 1)
    assert divergence.fields == ("action",)
    assert divergence.reason == "action differs"


def test_v2_changed_applied_result_is_detected(tmp_path: Path) -> None:
    changed = standard_decisions()
    result = changed[3].applied_result
    assert result is not None
    changed[3] = dataclasses.replace(
        changed[3], applied_result=dataclasses.replace(result, status="REJECTED_OUT_OF_REACH")
    )

    divergence = _divergence(tmp_path, standard_decisions(), changed)

    assert divergence is not None
    assert divergence.position == 4
    assert divergence.fields == ("applied_result",)


def test_v2_second_callback_of_a_process_in_one_tick_is_compared_separately(tmp_path: Path) -> None:
    changed = standard_decisions()
    result = changed[1].applied_result
    assert result is not None
    changed[1] = dataclasses.replace(changed[1], applied_result=dataclasses.replace(result, read_value=42))

    divergence = _divergence(tmp_path, standard_decisions(), changed)

    assert divergence is not None
    assert divergence.position == 2
    assert divergence.key_a == CallbackKey(1, "A", "main", 2)


def test_v2_missing_callback_is_detected(tmp_path: Path) -> None:
    shorter = standard_decisions()
    del shorter[3]  # tick 1, B/main, second callback

    divergence = _divergence(tmp_path, standard_decisions(), shorter)

    assert divergence is not None
    assert divergence.position == 4
    assert divergence.key_a == CallbackKey(1, "B", "main", 2)
    assert divergence.key_b == CallbackKey(2, "A", "main", 1)
    assert divergence.reason == "callback missing from trace b"
    assert divergence.fields == ()


def test_v2_callback_missing_mid_tick_is_found_at_its_position(tmp_path: Path) -> None:
    # Dropping a process's first callback in a tick renumbers its later ones,
    # so the gap shows up as a content difference at the right position.
    shorter = standard_decisions()
    del shorter[0]  # tick 1, A/main, callback 1 (of 2)

    divergence = _divergence(tmp_path, standard_decisions(), shorter)

    assert divergence is not None
    assert divergence.position == 1
    assert divergence.key_a == divergence.key_b == CallbackKey(1, "A", "main", 1)
    assert divergence.record_a is not None and divergence.record_b is not None
    assert divergence.record_b == standard_decisions()[1]
    assert "action" in divergence.fields


def test_v2_extra_trailing_callbacks_are_reported(tmp_path: Path) -> None:
    longer = [*standard_decisions(), decision(4, "A")]

    divergence = _divergence(tmp_path, standard_decisions(), longer)

    assert divergence is not None
    assert divergence.position == 13
    assert divergence.key_a is None and divergence.record_a is None
    assert divergence.key_b == CallbackKey(4, "A", "main", 1)
    assert divergence.reason == "trace a ends after 12 callbacks; trace b continues"


def test_v2_different_process_id_is_an_identity_divergence(tmp_path: Path) -> None:
    renamed = [
        dataclasses.replace(d, process_id="scout") if d.agent_id == "B" else d
        for d in standard_decisions()
    ]

    divergence = _divergence(tmp_path, standard_decisions(), renamed)

    assert divergence is not None
    assert divergence.position == 3
    assert divergence.key_b == CallbackKey(1, "B", "scout", 1)
    assert divergence.reason == "callback identity differs"


def test_v2_reordered_callbacks_are_an_order_divergence(tmp_path: Path) -> None:
    reordered = standard_decisions()
    reordered[0:4] = [reordered[2], reordered[3], reordered[0], reordered[1]]

    divergence = _divergence(tmp_path, standard_decisions(), reordered)

    assert divergence is not None
    assert divergence.position == 1
    assert divergence.reason == "callback order differs"


def test_v2_timing_and_diagnostic_message_are_not_compared(tmp_path: Path) -> None:
    def failing(message: str, wall: float):
        return decision(
            4,
            "A",
            kind="write",
            status="REJECTED_INVALID",
            wall_time_ms=wall,
            diagnostic=TraceDiagnostic(
                code="agent_action_invalid", stage="action", message=message,
                agent_id="A", slot=0, exception_type="ValueError", tick=4, action_slot=0,
            ),
        )

    a = [dataclasses.replace(d, wall_time_ms=0.01) for d in standard_decisions()]
    b = [dataclasses.replace(d, wall_time_ms=99.0) for d in standard_decisions()]
    a.append(failing("bad value at C:\\host\\a.py", 0.1))
    b.append(failing("bad value at /home/b.py", 5.0))

    assert _divergence(tmp_path, a, b) is None


def test_v2_stable_diagnostic_fields_are_compared(tmp_path: Path) -> None:
    def failing(code: str):
        return decision(
            2, "A", status="EXCEPTION",
            diagnostic=TraceDiagnostic(code=code, stage="action", message="m"),
        )

    divergence = _divergence(tmp_path, [failing("agent_action_timeout")], [failing("agent_action_exception")])

    assert divergence is not None
    assert divergence.fields == ("diagnostic",)


@pytest.mark.parametrize(
    ("sensed_a", "sensed_b"),
    [((), None), ((), ABSENT), (None, ABSENT), ((), (5,))],
)
def test_v2_absent_null_and_empty_sensing_results_are_distinct(tmp_path: Path, sensed_a, sensed_b) -> None:
    divergence = _divergence(
        tmp_path,
        [decision(1, kind="sense", sensed=sensed_a)],
        [decision(1, kind="sense", sensed=sensed_b)],
    )

    assert divergence is not None
    assert divergence.fields == ("applied_result",)


@pytest.mark.parametrize(
    ("reflection_a", "reflection_b"),
    [((), None), ((), ABSENT), (None, ABSENT)],
)
def test_v2_sense_reflection_absent_null_and_empty_are_distinct(
    tmp_path: Path, reflection_a, reflection_b
) -> None:
    divergence = _divergence(
        tmp_path,
        [decision(2, previous_sense=reflection_a)],
        [decision(2, previous_sense=reflection_b)],
    )

    assert divergence is not None
    assert divergence.fields == ("observation",)
