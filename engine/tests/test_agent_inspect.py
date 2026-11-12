from __future__ import annotations

import dataclasses
import shutil
from pathlib import Path

import pytest
from _agent_trace_v2_fixtures import decision, standard_decisions, write_trace_v2
from battle_engine.agent_inspect import diverge_main, inspect_main
from battle_engine.agent_test import DevelopmentTestOutcome
from battle_engine.agent_test import test_agent as run_development_test
from battle_engine.agent_trace import (
    DecisionRecord,
    ResetRecord,
    TraceAction,
    TraceDiagnostic,
    TraceHeader,
    TraceObservation,
    TraceWriter,
)
from battle_engine.starters import ensure_starter_agents


def _write_trace(path: Path, *, failing_tick: int | None = None) -> None:
    with TraceWriter(path) as writer:
        writer.write_header(
            TraceHeader(match_seed=1337, agents={"A": "agent_a", "B": "agent_b"}, supervised=True, agent_call_timeout=5.0)
        )
        writer.write_reset(ResetRecord(agent_id="A", wall_time_ms=1.0, diagnostic=None))
        writer.write_reset(ResetRecord(agent_id="B", wall_time_ms=1.0, diagnostic=None))
        for tick in range(1, 6):
            for agent_id in ("A", "B"):
                diagnostic = None
                action: TraceAction | None = TraceAction(kind="nop")
                if failing_tick is not None and tick == failing_tick and agent_id == "A":
                    action = None
                    diagnostic = TraceDiagnostic(
                        code="agent_action_timeout", stage="action",
                        message="Python agent A act() did not return within 1.0s.",
                        agent_id="A", slot=0, tick=tick, action_slot=0,
                    )
                writer.write_decision(
                    DecisionRecord(
                        tick=tick, agent_id=agent_id, action_slot=0, wall_time_ms=0.1,
                        observation=TraceObservation(
                            tick=tick, agent_id=agent_id, pc=0, register_a=0, register_p=0,
                            zero_flag=False, last_read=None, alive=True,
                        ),
                        action=action, diagnostic=diagnostic,
                    )
                )


def test_inspect_summary(tmp_path: Path, capsys) -> None:
    trace_path = tmp_path / "trace.jsonl"
    _write_trace(trace_path)

    exit_code = inspect_main([str(trace_path)])

    assert exit_code == 0
    out = capsys.readouterr().out
    assert "schema: bytefray.agent_trace v1" in out
    assert "decisions: 10" in out
    assert "failures: 0" in out


def test_inspect_accepts_run_directory(tmp_path: Path, capsys) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    _write_trace(run_dir / "trace.jsonl")

    exit_code = inspect_main([str(run_dir)])

    assert exit_code == 0
    assert "schema: bytefray.agent_trace" in capsys.readouterr().out


def test_inspect_tick_shows_both_agents(tmp_path: Path, capsys) -> None:
    trace_path = tmp_path / "trace.jsonl"
    _write_trace(trace_path)

    exit_code = inspect_main([str(trace_path), "--tick", "3"])

    out = capsys.readouterr().out
    assert exit_code == 0
    assert out.count("tick: 3") == 2
    assert "agent: A" in out
    assert "agent: B" in out


def test_inspect_tick_and_agent_filters_to_one_decision(tmp_path: Path, capsys) -> None:
    trace_path = tmp_path / "trace.jsonl"
    _write_trace(trace_path)

    exit_code = inspect_main([str(trace_path), "--tick", "3", "--agent", "A"])

    out = capsys.readouterr().out
    assert exit_code == 0
    assert out.count("tick: 3") == 1
    assert "agent: A" in out
    assert "agent: B" not in out


def test_inspect_around_window(tmp_path: Path, capsys) -> None:
    trace_path = tmp_path / "trace.jsonl"
    _write_trace(trace_path)

    exit_code = inspect_main([str(trace_path), "--around", "3", "--window", "1"])

    out = capsys.readouterr().out
    assert exit_code == 0
    for tick in (2, 3, 4):
        assert f"tick: {tick}" in out
    assert "tick: 1" not in out
    assert "tick: 5" not in out


def test_inspect_failures_only(tmp_path: Path, capsys) -> None:
    trace_path = tmp_path / "trace.jsonl"
    _write_trace(trace_path, failing_tick=3)

    exit_code = inspect_main([str(trace_path), "--failures"])

    out = capsys.readouterr().out
    assert exit_code == 0
    assert "agent_action_timeout" in out
    assert out.count("diagnostic.code:") == 1


def test_inspect_missing_file_exits_2(tmp_path: Path, capsys) -> None:
    exit_code = inspect_main([str(tmp_path / "nope")])

    assert exit_code == 2
    err = capsys.readouterr().err
    assert "code: trace_file_missing" in err


def test_inspect_malformed_trace_exits_2(tmp_path: Path, capsys) -> None:
    trace_path = tmp_path / "trace.jsonl"
    trace_path.write_text("not json\n", encoding="utf-8")

    exit_code = inspect_main([str(trace_path)])

    assert exit_code == 2
    err = capsys.readouterr().err
    assert "code: trace_format_invalid" in err


def test_diverge_identical_traces_reports_no_divergence(tmp_path: Path, capsys) -> None:
    trace_a = tmp_path / "a.jsonl"
    trace_b = tmp_path / "b.jsonl"
    _write_trace(trace_a)
    _write_trace(trace_b)

    exit_code = diverge_main([str(trace_a), str(trace_b)])

    out = capsys.readouterr().out
    assert exit_code == 0
    assert "status: identical" in out


def test_diverge_differing_traces_reports_first_divergence(tmp_path: Path, capsys) -> None:
    trace_a = tmp_path / "a.jsonl"
    trace_b = tmp_path / "b.jsonl"
    _write_trace(trace_a)
    _write_trace(trace_b, failing_tick=2)

    exit_code = diverge_main([str(trace_a), str(trace_b)])

    out = capsys.readouterr().out
    assert exit_code == 0
    assert "status: diverged" in out
    assert "tick: 2" in out
    assert "agent: A" in out


def test_diverge_missing_file_exits_2(tmp_path: Path, capsys) -> None:
    trace_a = tmp_path / "a.jsonl"
    _write_trace(trace_a)

    exit_code = diverge_main([str(trace_a), str(tmp_path / "nope")])

    assert exit_code == 2
    assert "code: trace_file_missing" in capsys.readouterr().err


# ---------------------------------------------------------------------------
# Schema 1: exact output characterization (unchanged by schema-2 support)
# ---------------------------------------------------------------------------


def test_schema_1_summary_and_decision_output_is_unchanged(tmp_path: Path, capsys) -> None:
    trace_path = tmp_path / "trace.jsonl"
    _write_trace(trace_path, failing_tick=2)

    assert inspect_main([str(trace_path)]) == 0
    assert capsys.readouterr().out == (
        f"trace: {trace_path}\n"
        "schema: bytefray.agent_trace v1\n"
        "match_seed: 1337\n"
        "supervised: True\n"
        "agent_call_timeout: 5\n"
        "agents: A=agent_a, B=agent_b\n"
        "ticks: 1-5\n"
        "decisions: 10\n"
        "resets: 2\n"
        "failures: 1\n"
        "  tick 2 A: agent_action_timeout\n"
    )

    assert inspect_main([str(trace_path), "--tick", "4", "--agent", "B"]) == 0
    assert capsys.readouterr().out == (
        "tick: 4\n"
        "agent: B\n"
        "action_slot: 0\n"
        "wall_time_ms: 0.100\n"
        "  observation.pc: 0\n"
        "  observation.register_a: 0\n"
        "  observation.register_p: 0\n"
        "  observation.zero_flag: False\n"
        "  observation.last_read: None\n"
        "  observation.alive: True\n"
        "  action: nop operand=None value=None\n"
    )


def test_process_filter_on_a_schema_1_trace_is_a_controlled_error(tmp_path: Path, capsys) -> None:
    trace_path = tmp_path / "trace.jsonl"
    _write_trace(trace_path)

    exit_code = inspect_main([str(trace_path), "--process", "main"])

    assert exit_code == 2
    err = capsys.readouterr().err
    assert "code: trace_option_unsupported" in err
    assert "schema 1" in err


@pytest.mark.parametrize("version", [3, 0])
def test_inspect_unsupported_schema_version_exits_2_with_actionable_code(
    tmp_path: Path, capsys, version: int
) -> None:
    trace_path = tmp_path / "trace.jsonl"
    trace_path.write_text(
        f'{{"schema": "bytefray.agent_trace", "schema_version": {version}, "record_type": "header", '
        '"match_seed": 1, "agents": {}, "supervised": false}\n',
        encoding="utf-8",
    )

    assert inspect_main([str(trace_path)]) == 2
    err = capsys.readouterr().err
    assert "code: trace_schema_unsupported" in err
    assert "supported: 1, 2" in err

    assert diverge_main([str(trace_path), str(trace_path)]) == 2
    assert "code: trace_schema_unsupported" in capsys.readouterr().err


# ---------------------------------------------------------------------------
# Schema 2: fixtures
# ---------------------------------------------------------------------------


def test_v2_summary_reports_binding_processes_resets_and_failures(tmp_path: Path, capsys) -> None:
    records = standard_decisions()
    records[2] = decision(1, "B", kind="write", operand=900, status="REJECTED_OUT_OF_REACH")
    records[5] = decision(  # tick 2, A/main, second callback
        2, "A", status="EXCEPTION",
        diagnostic=TraceDiagnostic(code="agent_action_exception", stage="action", message="boom"),
    )
    trace_path = write_trace_v2(
        tmp_path / "trace.jsonl",
        records,
        declarations=(("A", "main"), ("A", "scout"), ("B", "main")),
        reset_diagnostic=TraceDiagnostic(code="agent_reset_slow", stage="reset", message="slow"),
    )

    assert inspect_main([str(trace_path)]) == 0
    assert capsys.readouterr().out == (
        f"trace: {trace_path}\n"
        "schema: bytefray.agent_trace v2\n"
        "match_seed: 1337\n"
        "supervised: True\n"
        "agent_call_timeout: 5\n"
        "agents: A=alpha, B=bravo\n"
        "ruleset: bytefray-rules-6-alpha1\n"
        "replay_binding: present (not verified; inspect does not read the replay)\n"
        "  match_id: match_fixture\n"
        f"  replay_sha256: {'ab' * 32}\n"
        "  entrant_identities: A, B\n"
        "ticks: 1-3\n"
        "decisions: 12\n"
        "processes: 3\n"
        "  A/main: reach=128 share=1\n"
        "  A/scout: reach=128 share=1\n"
        "  B/main: reach=128 share=1\n"
        "resets: 2\n"
        "  reset A: sensing_window=27\n"
        "  reset B: sensing_window=27\n"
        "failures: 3\n"
        "  reset A: agent_reset_slow\n"
        "  tick 1 B/main callback 1: REJECTED_OUT_OF_REACH\n"
        "  tick 2 A/main callback 2: agent_action_exception (EXCEPTION)\n"
    )


def test_v2_summary_without_binding_does_not_claim_a_ruleset(tmp_path: Path, capsys) -> None:
    trace_path = write_trace_v2(tmp_path / "trace.jsonl", [], binding=False)

    assert inspect_main([str(trace_path)]) == 0
    out = capsys.readouterr().out
    assert "ruleset: not recorded (no binding record)" in out
    assert "replay_binding: none" in out
    assert "ticks: none" in out
    assert "decisions: 0" in out


def test_v2_decision_output_shows_process_callbacks_and_read_feedback(tmp_path: Path, capsys) -> None:
    records = [
        decision(1, "A", operand=40, read_value=7, read_owner="B"),
        decision(1, "A", operand=41, previous_read_value=7, visible=(300, 600)),
    ]
    trace_path = write_trace_v2(tmp_path / "trace.jsonl", records)

    assert inspect_main([str(trace_path), "--tick", "1"]) == 0
    out = capsys.readouterr().out
    first, second = out.rstrip("\n").split("\n\n")
    assert first.splitlines()[:4] == ["tick: 1", "agent: A", "process: main", "callback: 1"]
    assert "  action: read operand=40 value=None" in first
    assert "  applied.status: APPLIED" in first
    assert "  applied.read_value: 7" in first
    assert "  applied.read_owner: B" in first
    assert "callback: 2" in second
    assert "  observation.previous_read_value: 7" in second
    assert "  observation.visible_enemy_anchor_addresses: [300, 600]" in second


def test_v2_absent_null_and_empty_sensing_fields_render_distinctly(tmp_path: Path, capsys) -> None:
    records = [
        decision(1, kind="sense", sensed=()),
        decision(1, kind="sense", previous_sense=(), sensed=None, status="REJECTED_OUT_OF_REACH"),
        decision(1, kind="sense", previous_sense=None, sensed=(12, 30)),
        decision(1, kind="read", previous_sense=(12, 30)),
    ]
    trace_path = write_trace_v2(tmp_path / "trace.jsonl", records)

    assert inspect_main([str(trace_path), "--agent", "A"]) == 0
    blocks = capsys.readouterr().out.rstrip("\n").split("\n\n")
    sensed = [line for block in blocks for line in block.splitlines() if "applied.sensed_anchors" in line]
    reflected = [
        line for block in blocks for line in block.splitlines() if "previous_sense_anchors" in line
    ]
    assert sensed == [
        "  applied.sensed_anchors: []",
        "  applied.sensed_anchors: None",
        "  applied.sensed_anchors: [12, 30]",
        "  applied.sensed_anchors: (absent)",
    ]
    assert reflected == [
        "  observation.previous_sense_anchors: (absent)",
        "  observation.previous_sense_anchors: []",
        "  observation.previous_sense_anchors: None",
        "  observation.previous_sense_anchors: [12, 30]",
    ]


def test_v2_missing_action_and_result_render_as_none(tmp_path: Path, capsys) -> None:
    trace_path = write_trace_v2(
        tmp_path / "trace.jsonl",
        [
            decision(
                1, kind=None, status=None,
                diagnostic=TraceDiagnostic(code="agent_action_timeout", stage="action", message="late"),
            )
        ],
    )

    assert inspect_main([str(trace_path), "--failures"]) == 0
    out = capsys.readouterr().out
    assert "  action: none" in out
    assert "  applied: none" in out
    assert "  diagnostic.code: agent_action_timeout" in out
    assert "  diagnostic.message: late" in out


def test_v2_filters_by_tick_window_agent_and_process(tmp_path: Path, capsys) -> None:
    records = [
        *standard_decisions(),
        decision(2, "A", "scout"),
        decision(2, "A", "scout"),
        decision(3, "B", "scout"),
    ]
    trace_path = write_trace_v2(
        tmp_path / "trace.jsonl",
        records,
        declarations=(("A", "main"), ("A", "scout"), ("B", "main"), ("B", "scout")),
    )

    def blocks(*args: str) -> list[str]:
        assert inspect_main([str(trace_path), *args]) == 0
        return capsys.readouterr().out.rstrip("\n").split("\n\n")

    assert len(blocks("--tick", "2")) == 6
    assert len(blocks("--tick", "2", "--agent", "A")) == 4
    scout = blocks("--tick", "2", "--agent", "A", "--process", "scout")
    assert len(scout) == 2
    assert all("process: scout" in block for block in scout)
    assert "callback: 1" in scout[0]
    assert "callback: 2" in scout[1]
    assert len(blocks("--process", "scout")) == 3
    assert len(blocks("--around", "1", "--window", "0", "--agent", "B")) == 2
    window = blocks("--around", "3", "--window", "1", "--process", "scout")
    assert [block.splitlines()[0] for block in window] == ["tick: 2", "tick: 2", "tick: 3"]
    assert blocks("--tick", "9") == ["no matching decisions"]


def test_v2_failures_include_rejections_diagnostics_and_failed_resets(tmp_path: Path, capsys) -> None:
    records = [
        decision(1, "A"),
        decision(1, "A", kind="write", status="REJECTED_OUT_OF_REACH"),
        decision(
            2, "B", status="REJECTED_INVALID",
            diagnostic=TraceDiagnostic(code="agent_action_invalid", stage="action", message="bad"),
        ),
    ]
    trace_path = write_trace_v2(
        tmp_path / "trace.jsonl",
        records,
        reset_diagnostic=TraceDiagnostic(code="agent_reset_slow", stage="reset", message="slow"),
    )

    assert inspect_main([str(trace_path), "--failures"]) == 0
    out = capsys.readouterr().out
    assert out.count("\n\n") == 2
    assert "reset agent: A" in out and "sensing_window: 27" in out
    assert "applied.status: REJECTED_OUT_OF_REACH" in out
    assert "diagnostic.code: agent_action_invalid" in out

    def block_starts(text: str) -> list[str]:
        return [line for line in text.splitlines() if line.startswith(("tick: ", "reset agent: "))]

    assert inspect_main([str(trace_path), "--failures", "--agent", "B"]) == 0
    assert block_starts(capsys.readouterr().out) == ["tick: 2"]

    assert inspect_main([str(trace_path), "--failures", "--tick", "1"]) == 0
    assert block_starts(capsys.readouterr().out) == ["tick: 1"]

    clean = write_trace_v2(tmp_path / "clean.jsonl", standard_decisions())
    assert inspect_main([str(clean), "--failures"]) == 0
    assert capsys.readouterr().out == "no failures recorded\n"


def test_v2_diverge_reports_identical_and_first_changed_callback(tmp_path: Path, capsys) -> None:
    trace_a = write_trace_v2(tmp_path / "a.jsonl", standard_decisions())
    trace_b = write_trace_v2(tmp_path / "b.jsonl", standard_decisions())

    assert diverge_main([str(trace_a), str(trace_b)]) == 0
    out = capsys.readouterr().out
    assert "status: identical" in out
    assert "all 12 callbacks agree" in out

    changed = standard_decisions()
    action = changed[1].action
    assert action is not None
    changed[1] = dataclasses.replace(changed[1], action=dataclasses.replace(action, kind="sense"))
    trace_c = write_trace_v2(tmp_path / "c.jsonl", changed)

    assert diverge_main([str(trace_a), str(trace_c)]) == 0
    out = capsys.readouterr().out
    assert "status: diverged" in out
    assert "position: 2" in out
    assert "callback_a: tick=1 agent=A process=main callback=2" in out
    assert "callback_b: tick=1 agent=A process=main callback=2" in out
    assert "reason: action differs" in out
    assert "  action: read operand=12 value=None" in out
    assert "  action: sense operand=12 value=None" in out


def test_v2_diverge_reports_a_shorter_trace(tmp_path: Path, capsys) -> None:
    trace_a = write_trace_v2(tmp_path / "a.jsonl", standard_decisions())
    trace_b = write_trace_v2(tmp_path / "b.jsonl", standard_decisions()[:-1])

    assert diverge_main([str(trace_a), str(trace_b)]) == 0
    out = capsys.readouterr().out
    assert "position: 12" in out
    assert "callback_b: none (trace b ends after 11 callbacks)" in out
    assert "--- trace b: no callback at this position ---" in out


def test_diverge_refuses_to_compare_schema_1_with_schema_2(tmp_path: Path, capsys) -> None:
    v1 = tmp_path / "v1.jsonl"
    _write_trace(v1)
    v2 = write_trace_v2(tmp_path / "v2.jsonl", standard_decisions())

    for pair in ([v1, v2], [v2, v1]):
        assert diverge_main([str(p) for p in pair]) == 2
        captured = capsys.readouterr()
        assert captured.out == ""
        assert "code: trace_schema_mismatch" in captured.err


def test_v2_diverge_malformed_trace_exits_2(tmp_path: Path, capsys) -> None:
    good = write_trace_v2(tmp_path / "a.jsonl", standard_decisions())
    bad = tmp_path / "b.jsonl"
    bad.write_text(
        good.read_text(encoding="utf-8").replace('"current_tick": 2', '"current_tick": null', 1),
        encoding="utf-8",
    )

    assert diverge_main([str(good), str(bad)]) == 2
    assert "code: trace_format_invalid" in capsys.readouterr().err


def test_v2_malformed_binding_exits_2_before_any_summary_output(tmp_path: Path, capsys) -> None:
    good = write_trace_v2(tmp_path / "a.jsonl", standard_decisions())
    bad = tmp_path / "b.jsonl"
    bad.write_text(
        good.read_text(encoding="utf-8").replace(
            '"entrant_identities": ["A", "B"]', '"entrant_identities": [1, 2]'
        ),
        encoding="utf-8",
    )

    assert inspect_main([str(bad)]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "code: trace_format_invalid" in captured.err


# ---------------------------------------------------------------------------
# Schema 2: real V6 starter matches (end-to-end product regression)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def v6_starter_runs(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Path]:
    """Run directories of real five-tick Active Sensing matches between two V6 starters."""

    root = tmp_path_factory.mktemp("agent_lab_v6")
    ensure_starter_agents(data_root=root)

    def run(label: str, *, seed: int = 1337, ticks: int = 5) -> Path:
        outcome = run_development_test(
            "v6_window_scout",
            opponent="v6_watchful_keeper",
            seed=seed,
            ticks=ticks,
            data_root=root,
            run_dir=root / "runs" / label,
        )
        assert isinstance(outcome, DevelopmentTestOutcome)
        assert outcome.trace_path is not None
        return outcome.trace_path.parent

    return {
        "base": run("base"),
        "repeat": run("repeat"),
        "other_seed": run("other_seed", seed=4242),
        "longer": run("longer", ticks=6),
    }


def test_real_v6_trace_is_schema_2_and_inspectable(v6_starter_runs, capsys) -> None:
    run_dir = v6_starter_runs["base"]
    header = (run_dir / "trace.jsonl").read_text(encoding="utf-8").splitlines()[0]
    assert '"schema_version": 2' in header

    for target in (run_dir, run_dir / "trace.jsonl"):
        assert inspect_main([str(target)]) == 0
        out = capsys.readouterr().out
        assert "schema: bytefray.agent_trace v2" in out
        assert "ruleset: bytefray-rules-6-alpha1" in out
        assert "agents: A=v6_window_scout, B=v6_watchful_keeper" in out
        assert "ticks: 1-5" in out
        assert "processes: 2" in out
        assert "  reset A: sensing_window=27" in out
        assert "failures: 0" in out


def test_real_v6_trace_can_be_queried_at_one_tick(v6_starter_runs, capsys) -> None:
    run_dir = v6_starter_runs["base"]

    assert inspect_main([str(run_dir), "--tick", "3", "--agent", "A", "--process", "main"]) == 0
    blocks = capsys.readouterr().out.rstrip("\n").split("\n\n")
    assert blocks
    for number, block in enumerate(blocks, start=1):
        assert block.startswith(f"tick: 3\nagent: A\nprocess: main\ncallback: {number}\n")
    joined = "\n".join(blocks)
    assert "applied.sensed_anchors:" in joined
    assert "applied.status: APPLIED" in joined


def test_real_v6_identical_runs_do_not_diverge(v6_starter_runs, capsys) -> None:
    # Two separate executions with the same seed: host timings differ, decisions do not.
    base, repeat = v6_starter_runs["base"], v6_starter_runs["repeat"]

    assert diverge_main([str(base), str(repeat / "trace.jsonl")]) == 0
    assert "status: identical" in capsys.readouterr().out


def test_real_v6_runs_with_different_seeds_diverge(v6_starter_runs, capsys) -> None:
    assert diverge_main([str(v6_starter_runs["base"]), str(v6_starter_runs["other_seed"])]) == 0
    out = capsys.readouterr().out
    assert "status: diverged" in out
    assert "position: 1" in out
    assert "reason: observation" in out


def test_real_v6_longer_run_diverges_where_the_shorter_trace_ends(v6_starter_runs, capsys) -> None:
    assert diverge_main([str(v6_starter_runs["base"]), str(v6_starter_runs["longer"])]) == 0
    out = capsys.readouterr().out
    assert "status: diverged" in out
    assert "callback_a: none (trace a ends after" in out
    assert "callback_b: tick=6 " in out


def test_real_v6_trace_edited_in_one_callback_diverges_there(
    v6_starter_runs, tmp_path: Path, capsys
) -> None:
    source = v6_starter_runs["base"] / "trace.jsonl"
    lines = source.read_text(encoding="utf-8").splitlines()
    decision_lines = [i for i, line in enumerate(lines) if '"record_type": "decision_v2"' in line]
    target = decision_lines[20]
    assert '"status": "APPLIED"' in lines[target]
    lines[target] = lines[target].replace('"status": "APPLIED"', '"status": "REJECTED_OUT_OF_REACH"')
    edited = tmp_path / "edited.jsonl"
    edited.write_text("\n".join(lines) + "\n", encoding="utf-8")
    copied = tmp_path / "copied"
    copied.mkdir()
    shutil.copyfile(source, copied / "trace.jsonl")

    assert diverge_main([str(copied), str(edited)]) == 0
    out = capsys.readouterr().out
    assert "position: 21" in out
    assert "reason: applied_result differs" in out
