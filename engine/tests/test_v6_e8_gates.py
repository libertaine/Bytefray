"""V6 E8: E8-D's clauses, the D8-1 re-derivation and control qualification (PR8 Sec 5.1, 5.2; phase I8-5).

Real artifacts first: scripted, non-family agents play through the real
evaluation path under all four conditions, and every clause must hold on
their traces. Then every planted violation the implementation plan names
(Sec 3.5) must fail its clause. No family member plays, no matrix cell
exists, and no outcome is asserted.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest
from _e8_scripted_matrix import scripted_field

from tools.research.v6.e8 import decision, family, gates, matrix, rederive, traces
from tools.research.v6.e8.traces import ABSENT, COLUMN

C = COLUMN
TICKS = 40
Fields = dict[str, tuple[Path, Path, list[traces.TraceRecord], dict[str, dict[str, Any]]]]


@pytest.fixture(scope="module")
def fields(tmp_path_factory: pytest.TempPathFactory) -> Fields:
    root = tmp_path_factory.mktemp("e8-gates")
    return {c.condition_id: scripted_field(root, c.ruleset_id, seeds=(1, 2, 3), ticks=TICKS)
            for c in matrix.CONDITIONS}


def _material(fields: Fields, condition_id: str, index: int = 0) -> tuple[list[list[Any]], dict[str, Any],
                                                                          traces.TraceRecord, dict[str, Any]]:
    field, _, records, cells = fields[condition_id]
    record = records[index]
    summary = next(line["summary"] for line in traces.read_summaries(field) if line["schedule_id"] == record.schedule_id)
    return traces.read_rows(field, record), summary, record, cells[record.schedule_id]


def _check(fields: Fields, condition_id: str, *, rows: list[list[Any]] | None = None,
           summary: dict[str, Any] | None = None, index: int = 0) -> gates.CellResult:
    base_rows, base_summary, record, cell = _material(fields, condition_id, index)
    return gates.check_cell(base_rows if rows is None else rows, base_summary if summary is None else summary,
                            record, cell, condition=matrix.condition(condition_id))


def _chunk(result: gates.CellResult, condition_id: str = "T8") -> gates.FieldChecks:
    return gates.FieldChecks(Path("."), condition_id, "F1", [result], expected_cells=1, completed_cells=1)


def _first(rows: list[list[Any]], predicate: Any) -> int:
    return next(i for i, row in enumerate(rows) if predicate(row))


# ---------------------------------------------------------------------------
# Every clause holds on real scripted traces
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("condition_id", ["C8", "T8", "C8L", "T8L"])
def test_every_per_cell_clause_holds_on_real_scripted_traces(fields: Fields, condition_id: str) -> None:
    field, _, _, cells = fields[condition_id]
    checks = [gates.check_field(field, cells.values(), condition_id=condition_id, field_id="F1", expected_cells=6)]
    active = matrix.condition(condition_id).sensing_mode == "active"
    reports = {name: getattr(gates, name.lower().replace("-", "_"))(checks)
               for name in ("D8-1", "D8-8", "D8-12", "D8-13", "D8-14", "D8-15")}
    if active:
        reports.update({name: getattr(gates, name.lower().replace("-", "_"))(checks)
                        for name in ("D8-2", "D8-4", "D8-5")})
        # The re-derivation reached applied SENSEs and refusals, and every obligation was met.
        assert reports["D8-1"]["applied_senses_rederived"] > 0 and reports["D8-1"]["refused_senses_rederived"] > 0
        assert reports["D8-13"]["deliveries_checked"] > 0
    else:
        assert gates.cq8_1(checks)["status"] == "PASS"
    assert all(report["status"] == "PASS" for report in reports.values()), {
        name: report for name, report in reports.items() if report["status"] != "PASS"}
    for result in checks[0].results:
        assert result.rederived is not None and result.rederived.passed and result.rederived.callbacks > 0


def test_the_rederivation_aligns_under_both_parents_and_both_channels(fields: Fields) -> None:
    for condition_id in ("C8", "T8", "C8L", "T8L"):
        rows, summary, _, cell = _material(fields, condition_id)
        check = rederive.rederive_cell(rows, summary, ticks_run=int(cell["ticks_run"]), arena=512,
                                       slot_limit=matrix.condition(condition_id).disruption_slot_limit)
        assert check.passed and check.callbacks == len(rows)


def test_an_empty_gate_never_passes() -> None:
    assert gates.d8_14([])["status"] == "FAIL"
    assert gates.d8_2([gates.FieldChecks(Path("."), "T8", "F1", [], 0, 0)])["status"] == "FAIL"


# ---------------------------------------------------------------------------
# D8-1: exactness and presence
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("condition_id", ["T8", "T8L"])
def test_d8_1_a_planted_tuple_fails(fields: Fields, condition_id: str) -> None:
    rows, *_ = _material(fields, condition_id)
    rows = copy.deepcopy(rows)
    i = _first(rows, lambda r: r[C["kind"]] == "sense" and r[C["status"]] == "APPLIED")
    rows[i][C["sensed"]] = sorted({*rows[i][C["sensed"]], 3})
    report = gates.d8_1([_chunk(_check(fields, condition_id, rows=rows), condition_id)])
    assert report["status"] == "FAIL"
    assert report["failure_samples"][0]["rederived"]["sensing"] >= 1


def test_d8_1_a_dropped_field_fails(fields: Fields) -> None:
    rows = copy.deepcopy(_material(fields, "T8")[0])
    i = _first(rows, lambda r: r[C["kind"]] == "sense" and r[C["status"]] == "APPLIED")
    rows[i][C["sensed"]] = ABSENT
    result = _check(fields, "T8", rows=rows)
    assert [item["reason"] for item in result.presence_sensed] == ["a SENSE record without sensed_anchors"]
    assert gates.d8_1([_chunk(result)])["status"] == "FAIL"


@pytest.mark.parametrize("condition_id", ["C8", "T8"])
def test_d8_1_a_stray_field_fails_under_every_condition(fields: Fields, condition_id: str) -> None:
    rows = copy.deepcopy(_material(fields, condition_id)[0])
    i = _first(rows, lambda r: r[C["kind"]] != "sense")
    rows[i][C["sensed"]] = []
    result = _check(fields, condition_id, rows=rows)
    assert [item["reason"] for item in result.presence_sensed] == ["sensed_anchors on a non-SENSE record"]
    assert gates.d8_1([_chunk(result, condition_id)])["status"] == "FAIL"


def test_d8_1_a_refusal_with_a_list_and_an_applied_null_both_fail(fields: Fields) -> None:
    rows = copy.deepcopy(_material(fields, "T8")[0])
    refused = _first(rows, lambda r: r[C["kind"]] == "sense" and r[C["status"]] == "REJECTED_OUT_OF_REACH")
    applied = _first(rows, lambda r: r[C["kind"]] == "sense" and r[C["status"]] == "APPLIED")
    rows[refused][C["sensed"]] = []
    rows[applied][C["sensed"]] = None
    reasons = sorted(item["reason"] for item in _check(fields, "T8", rows=rows).presence_sensed)
    assert reasons == ["a REJECTED_OUT_OF_REACH SENSE whose sensed_anchors is not null",
                       "an applied SENSE whose sensed_anchors is not a list"]


def test_d8_1_a_status_the_reach_contradicts_fails(fields: Fields) -> None:
    rows = copy.deepcopy(_material(fields, "T8")[0])
    i = _first(rows, lambda r: r[C["kind"]] == "sense" and r[C["status"]] == "REJECTED_OUT_OF_REACH")
    rows[i][C["status"]], rows[i][C["sensed"]] = "APPLIED", []
    rows[i][C["address"]] = rows[i][C["operand"]] % 512
    check = _check(fields, "T8", rows=rows).rederived
    assert check is not None and check.status_mismatches == 1


# ---------------------------------------------------------------------------
# D8-2, D8-4, D8-5
# ---------------------------------------------------------------------------


def test_d8_2_a_planted_visible_leak_fails(fields: Fields) -> None:
    rows = copy.deepcopy(_material(fields, "T8")[0])
    rows[5][C["visible"]] = [300]
    result = _check(fields, "T8", rows=rows)
    assert result.visible == 1 and gates.d8_2([_chunk(result)])["status"] == "FAIL"


def test_d8_4_an_extra_uncharged_offer_after_a_sense_fails(fields: Fields) -> None:
    rows = copy.deepcopy(_material(fields, "T8")[0])
    i = _first(rows, lambda r: r[C["kind"]] == "sense")
    rows.insert(i + 1, copy.deepcopy(rows[i]))
    result = _check(fields, "T8", rows=rows)
    assert result.rederived is not None and result.rederived.alignment_failures == 1
    assert gates.d8_4([_chunk(result)])["status"] == "FAIL"


def test_d8_4_more_than_eight_callbacks_in_a_tick_fails() -> None:
    rows = [[1, "A", "p", n, 0, 256, [], True, None, None, ABSENT, "sense", 0, None, "APPLIED", 0, None, None, []]
            for n in range(1, 10)]
    assert gates.callbacks_per_tick(rows) == [{"tick": 1, "entrant": "A", "callbacks": 9}]


def test_d8_5_a_write_the_replay_does_not_show_fails(fields: Fields) -> None:
    rows = copy.deepcopy(_material(fields, "T8")[0])
    i = _first(rows, lambda r: r[C["kind"]] == "write" and r[C["status"]] == "APPLIED")
    rows[i][C["value"]] = (rows[i][C["value"]] or 0) + 1
    result = _check(fields, "T8", rows=rows)
    assert not result.write_log_equal and gates.d8_5([_chunk(result)])["status"] == "FAIL"


def test_d8_5_a_position_a_sense_would_have_changed_fails(fields: Fields) -> None:
    rows = copy.deepcopy(_material(fields, "T8")[0])
    i = _first(rows, lambda r: r[C["kind"]] == "sense")
    j = next(k for k in range(i + 1, len(rows)) if rows[k][C["entrant"]] == rows[i][C["entrant"]])
    rows[j][C["anchor"]] = (rows[j][C["anchor"]] + 1) % 512
    result = _check(fields, "T8", rows=rows)
    assert result.rederived is not None and result.rederived.move_mismatches >= 1
    assert gates.d8_5([_chunk(result)])["status"] == "FAIL"


# ---------------------------------------------------------------------------
# D8-13 and D8-14
# ---------------------------------------------------------------------------


def _owed(rows: list[list[Any]]) -> int:
    i = _first(rows, lambda r: r[C["kind"]] == "sense")
    entrant, process = rows[i][C["entrant"]], rows[i][C["process"]]
    return next(k for k in range(i + 1, len(rows)) if (rows[k][C["entrant"]], rows[k][C["process"]]) == (entrant, process))


def test_d8_13_a_planted_mismatch_fails(fields: Fields) -> None:
    rows = copy.deepcopy(_material(fields, "T8")[0])
    j = _owed(rows)
    rows[j][C["delivered"]] = [*(rows[j][C["delivered"]] or []), 1]
    result = _check(fields, "T8", rows=rows)
    assert len(result.delivery_reflection) == 1 and gates.d8_13([_chunk(result)])["status"] == "FAIL"


def test_d8_13_a_dropped_reflection_fails(fields: Fields) -> None:
    rows = copy.deepcopy(_material(fields, "T8")[0])
    rows[_owed(rows)][C["delivered"]] = ABSENT
    result = _check(fields, "T8", rows=rows)
    assert [i["reason"] for i in result.delivery_presence] == ["a delivery obligation without previous_sense_anchors"]
    assert gates.d8_13([_chunk(result)])["status"] == "FAIL"


@pytest.mark.parametrize("condition_id", ["C8", "T8"])
def test_d8_13_a_stray_field_fails_under_every_condition(fields: Fields, condition_id: str) -> None:
    rows = copy.deepcopy(_material(fields, condition_id)[0])
    rows[0][C["delivered"]] = None  # the first callback can owe nothing
    result = _check(fields, condition_id, rows=rows)
    assert [i["reason"] for i in result.delivery_presence] == ["previous_sense_anchors without a delivery obligation"]
    assert gates.d8_13([_chunk(result, condition_id)])["status"] == "FAIL"


def test_d8_13_a_refused_sense_is_reflected_as_null(fields: Fields) -> None:
    rows = _material(fields, "T8")[0]
    refusals = [i for i, r in enumerate(rows) if r[C["kind"]] == "sense" and r[C["status"]] != "APPLIED"]
    assert refusals
    presence, reflection, met = gates.delivery(rows)
    assert presence == reflection == [] and met > 0


@pytest.mark.parametrize("status", ["REJECTED_INVALID", "EXCEPTION", "SOMETHING_NEW", None])
def test_d8_14_every_other_status_and_a_missing_one_fail(fields: Fields, status: str | None) -> None:
    rows = copy.deepcopy(_material(fields, "T8")[0])
    rows[3][C["status"]] = status
    result = _check(fields, "T8", rows=rows)
    assert result.statuses == [{"order": 3, "status": status}]
    assert gates.d8_14([_chunk(result)])["status"] == "FAIL"


# ---------------------------------------------------------------------------
# D8-15
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(("condition_id", "windows", "reason"), [
    ("T8", {"A": [26], "B": [27]}, "not 27 under an active Ruleset"),
    ("T8", {"A": [ABSENT], "B": [27]}, "not 27 under an active Ruleset"),
    ("T8", {"A": [None], "B": [27]}, "not 27 under an active Ruleset"),
    ("C8", {"A": [None], "B": [ABSENT]}, "present under a passive Ruleset"),
    ("C8", {"A": [27], "B": [ABSENT]}, "present under a passive Ruleset"),
    ("T8", {"A": [], "B": [27]}, "no reset record"),
])
def test_d8_15_wrong_missing_and_explicit_null_windows_fail(fields: Fields, condition_id: str,
                                                            windows: dict[str, list[Any]], reason: str) -> None:
    summary = copy.deepcopy(_material(fields, condition_id)[1])
    summary["reset_windows"] = windows
    result = _check(fields, condition_id, summary=summary)
    assert [item["reason"] for item in result.windows] == [reason]
    assert gates.d8_15([_chunk(result, condition_id)])["status"] == "FAIL"


def test_the_rederivation_uses_exactly_the_recorded_window(fields: Fields) -> None:
    rows, summary, _, cell = _material(fields, "T8")
    narrower = copy.deepcopy(summary)
    narrower["reset_windows"] = {"A": [20], "B": [20]}
    found = [r for r in rows if r[C["kind"]] == "sense" and r[C["sensed"]]]
    assert found  # at least one SENSE found an anchor, so a narrower window changes some tuple or not
    check = rederive.rederive_cell(rows, narrower, ticks_run=int(cell["ticks_run"]), arena=512, slot_limit=None)
    wide = rederive.rederive_cell(rows, summary, ticks_run=int(cell["ticks_run"]), arena=512, slot_limit=None)
    assert wide.passed
    assert rederive.configured_window(narrower) == 20 and check.senses_applied == wide.senses_applied
    with pytest.raises(ValueError):
        rederive.configured_window({"reset_windows": {"A": [27], "B": [ABSENT]}})


# ---------------------------------------------------------------------------
# D8-7, D8-8, D8-11, D8-12
# ---------------------------------------------------------------------------


def test_d8_7_tick_zero_distances() -> None:
    far = {"schedule_id": "x", "summary": {"tick0_anchors": {"A": {"p": 100}, "B": {"p": 200}}}}
    near = {"schedule_id": "y", "summary": {"tick0_anchors": {"A": {"p": 100}, "B": {"p": 132}}}}
    wrap = {"schedule_id": "z", "summary": {"tick0_anchors": {"A": {"p": 5}, "B": {"p": 500}}}}
    assert gates.d8_7([far])["status"] == "PASS" and gates.d8_7([far])["closest_distance"] == 100
    assert gates.d8_7([far, near])["status"] == "FAIL"
    assert gates.d8_7([wrap])["status"] == "FAIL"  # 17 cells across the wrap


def test_d8_8_a_planted_early_blind_strike_fails() -> None:
    core = {"A": 100, "B": 300}
    informed = [[1, "A", "p", 1, 100, 256, [300], False, None, None, ABSENT, "write", 301, 1, "APPLIED", 301, None, None,
                 ABSENT]]
    blind = [[1, "A", "p", 1, 100, 256, [], False, None, None, ABSENT, "write", 301, 1, "APPLIED", 301, None, None,
              ABSENT]]
    sensed = [[1, "A", "p", 1, 100, 256, [], False, None, None, ABSENT, "sense", 300, None, "APPLIED", 300, None, None,
               [300]],
              [1, "A", "p", 2, 100, 256, [], True, None, None, [300], "write", 301, 1, "APPLIED", 301, None, None, ABSENT]]
    assert gates.early_blind_strikes(informed, core, arena=512) == ([], 1)
    assert gates.early_blind_strikes(sensed, core, arena=512) == ([], 1)
    failures, writes = gates.early_blind_strikes(blind, core, arena=512)
    assert writes == 1 and failures == [{"order": 0, "tick": 1, "entrant": "A", "address": 301}]
    late = [[3, "A", "p", 1, 100, 256, [], False, None, None, ABSENT, "write", 301, 1, "APPLIED", 301, None, None, ABSENT]]
    assert gates.early_blind_strikes(late, core, arena=512) == ([], 0)  # tick 3 is outside D8-8


def test_d8_8_a_sense_result_counts_only_from_its_delivery() -> None:
    core = {"A": 100, "B": 300}
    # The SENSE finds the core's anchor, but the next row is the entrant's other process: not yet delivered.
    rows = [[1, "A", "s", 1, 100, 256, [], False, None, None, ABSENT, "sense", 300, None, "APPLIED", 300, None, None,
             [300]],
            [1, "A", "t", 2, 110, 256, [], False, None, None, ABSENT, "write", 301, 1, "APPLIED", 301, None, None, ABSENT]]
    failures, _ = gates.early_blind_strikes(rows, core, arena=512)
    assert len(failures) == 1


def _mirror(tmp_path: Path, fields: Fields, *, same: bool) -> dict[str, Any]:
    field, _, records, _ = fields["C8"]
    replay = (field / records[0].replay).read_text(encoding="utf-8")
    primary, twin = family.package_id("RUSH8"), family.package_id("RUSH8", "twin")
    lines = replay.splitlines()
    k = next(i for i, line in enumerate(lines) if json.loads(line).get("record_type") == "tick"
             and json.loads(line)["tick"] == 2)
    changed = json.loads(lines[k])
    changed["memory_diffs"].append({"addr": 9, "len": 1, "owner": "B", "values": [1]})
    altered = "\n".join([*lines[:k], json.dumps(changed), *lines[k + 1:]]) + "\n"
    cells = []
    for orientation, outcome in (("candidate_first", "win"), ("opponent_first", "loss")):
        directory = tmp_path / orientation
        directory.mkdir()
        text = replay if same or orientation == "candidate_first" else altered
        (directory / "replay.jsonl").write_text(text, encoding="utf-8")
        cells.append({"subject_id": primary, "opponent_id": twin, "seed": 1, "orientation": orientation,
                      "outcome": outcome, "artifact_dir": orientation})
    return {"cells": cells}


@pytest.mark.parametrize("same", [True, False])
def test_d8_11_mirror_relabeling(fields: Fields, tmp_path: Path, same: bool) -> None:
    built = _mirror(tmp_path, fields, same=same)
    report = gates.d8_11(tmp_path, built["cells"], expected_units=1)
    assert report["status"] == ("PASS" if same else "FAIL")
    assert gates.d8_11(tmp_path, built["cells"][:1], expected_units=1)["status"] == "FAIL"


def test_d8_12_a_missing_or_mis_bound_trace_or_a_lost_record_fails(fields: Fields) -> None:
    good = _check(fields, "T8")
    assert gates.d8_12([_chunk(good)])["status"] == "PASS"
    short = gates.FieldChecks(Path("."), "T8", "F1", [good], expected_cells=2, completed_cells=2)
    assert gates.d8_12([short])["status"] == "FAIL"
    summary = copy.deepcopy(_material(fields, "T8")[1])
    summary["bindings"][0]["replay_sha256"] = "0" * 64
    assert gates.d8_12([_chunk(_check(fields, "T8", summary=summary))])["status"] == "FAIL"
    rows = copy.deepcopy(_material(fields, "T8")[0])
    del rows[7]
    assert gates.d8_12([_chunk(_check(fields, "T8", rows=rows))])["status"] == "FAIL"


# ---------------------------------------------------------------------------
# D8-3 and CQ8
# ---------------------------------------------------------------------------


def _d8_3_cells(seeds: list[int]) -> tuple[list[dict[str, Any]], list[gates.CellResult]]:
    cells, results = [], []
    for opponent in decision.MEMBERS:
        if opponent in ("LURK8", "GREED8"):
            continue
        for member in ("LURK8", "GREED8"):
            for seed in seeds:
                for orientation in ("candidate_first", "opponent_first"):
                    sid = f"{member}|{opponent}|{seed}|{orientation}"
                    cells.append({"schedule_id": sid, "subject_id": family.package_id(member),
                                  "opponent_id": family.package_id(opponent), "seed": seed, "orientation": orientation})
                    seat = "A" if orientation == "candidate_first" else "B"
                    results.append(gates.CellResult(sid, True, None, [], [], [], 0, [], [], [], 0, True, [], 0, True, 0,
                                                    {f"d8_3:{seat}": f"{opponent}|{seed}|{seat}"}))
    return cells, results


def test_d8_3_equal_streams_pass_and_a_divergence_or_missing_cell_fails() -> None:
    seeds = list(range(100, 132))
    cells, results = _d8_3_cells(seeds)
    chunk = gates.FieldChecks(Path("."), "T8", "F1", results, len(results), len(results))
    report = gates.d8_3([chunk], cells, seeds=seeds)
    assert report["status"] == "PASS" and report["checked"] == 576
    diverged = copy.deepcopy(results)
    diverged[0].streams = {key: "different" for key in diverged[0].streams}
    assert gates.d8_3([gates.FieldChecks(Path("."), "T8", "F1", diverged, 1, 1)], cells, seeds=seeds)["status"] == "FAIL"
    assert gates.d8_3([gates.FieldChecks(Path("."), "T8", "F1", results[1:], 1, 1)], cells, seeds=seeds)["status"] == "FAIL"


def test_d8_3_an_absent_field_differs_from_a_null_one() -> None:
    row = [1, "A", "p", 1, 0, 256, [], True, None, None, ABSENT, "write", 1, 1, "APPLIED", 1, None, None, ABSENT]
    nulled = copy.deepcopy(row)
    nulled[C["delivered"]] = None
    assert gates.stream_digest([row], "A", gates.D8_3_FIELDS) != gates.stream_digest([nulled], "A", gates.D8_3_FIELDS)


def test_cq8_1_a_control_sense_record_fails(fields: Fields) -> None:
    rows = copy.deepcopy(_material(fields, "C8")[0])
    rows[2][C["kind"]], rows[2][C["sensed"]] = "sense", []
    result = _check(fields, "C8", rows=rows)
    assert gates.cq8_1([_chunk(result, "C8")])["status"] == "FAIL"


def test_cq8_2_triggers() -> None:
    def row(tick: int, visible: list[int]) -> list[Any]:
        return [tick, "A", "p", 1, 0, 256, visible, True, None, None, ABSENT, "write", 1, 1, "APPLIED", 1, None, None,
                ABSENT]
    rows = [row(1, []), row(1, [300]), row(1, [300]), row(2, [310])]
    assert gates.reacquisition_trigger(rows, "A") == 3  # 300 tracked, then missing
    assert gates.reacquisition_trigger(rows[:3], "A") is None
    hits = [row(1, [])] * 8 + [row(2, [])] * 5 + [row(3, [])]
    assert gates.inferred_hit(hits, "A") == 13  # tick 2 had fewer than 8 callbacks
    gap = [row(1, [])] * 8 + [row(3, [])]
    assert gates.inferred_hit(gap, "A") == 8  # tick 2 had none
    assert gates.inferred_hit([row(1, [])] * 8 + [row(2, [])], "A") is None  # never at the match's first callback


def test_cq8_2_compares_the_twins_before_the_trigger(fields: Fields) -> None:
    field, _, records, _ = fields["C8"]
    record = records[0]
    rows = traces.read_rows(field, record)
    trigger = 10
    chunk = gates.FieldChecks(field, "C8", "F1", [], 1, 1,
                              twin_prefixes={("REACQ8", "LURK8", "A", 1): {
                                  "trigger": trigger, "prefix": gates.stream_digest(rows, "A", gates.ACTION_FIELDS,
                                                                                    until=trigger)}},
                              compared_records={("RUSH8", "LURK8", "A", 1): record})
    assert gates.cq8_2([chunk])["status"] == "PASS"
    chunk.twin_prefixes[("REACQ8", "LURK8", "A", 1)]["trigger"] = 11
    assert gates.cq8_2([chunk])["status"] == "FAIL"
    chunk.compared_records.clear()
    assert gates.cq8_2([chunk])["status"] == "FAIL"


# ---------------------------------------------------------------------------
# E8-D
# ---------------------------------------------------------------------------


def test_e8_d_passes_only_when_every_clause_passes() -> None:
    clauses = {f"D8-{n}": "PASS" for n in range(1, 16)}
    assert gates.e8_d(clauses)["status"] == "PASS"
    for n in range(1, 16):
        failed = {**clauses, f"D8-{n}": "FAIL"}
        assert gates.e8_d(failed)["status"] == "FAIL"
    with pytest.raises(ValueError):
        gates.e8_d({k: v for k, v in clauses.items() if k != "D8-10"})
    with pytest.raises(ValueError):
        gates.e8_d({**clauses, "D8-3": "NEITHER"})


def test_gate_reports_are_json_and_cap_their_samples(fields: Fields) -> None:
    rows = copy.deepcopy(_material(fields, "T8")[0])
    for row in rows[:20]:
        row[C["status"]] = "EXCEPTION"
    report = gates.d8_14([_chunk(_check(fields, "T8", rows=rows))])
    assert report["failures"] == 20 and len(report["failure_samples"]) == gates.SAMPLE_LIMIT
    json.dumps(report)
