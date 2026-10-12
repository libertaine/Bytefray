"""V6 E8 phase I8-1: the two E8 parents reproduce their pre-E8 goldens (D8-6).

``tools/research/v6/e8/parent_goldens.json`` was recorded by
``tools/research/v6/e8/parent_goldens.py`` against the engine before any E8
engine, API or trace change. C8 (``research-sensing-r32``, whole-tick) and C8L
(``research-disruption-slot1-sensing-r32``, λ = 1) must keep reproducing every
case byte for byte while active sensing is off:

* the replay's bytes, and the trace's bytes with only ``wall_time_ms`` masked;
* each trace record type's bytes, and each entrant's D8-3 comparison surface;
* ``result_id``, ``match_id`` and the outcome.

The tests also show that the record's definition is the tool's (scenarios,
golden seeds, parents, fixtures), that the tool that generated it is the
committed one, that the goldens exercise what the E8 engine change could
disturb, and that every compared fact actually detects a change, including an
optional field serialized as ``null``. A mismatch here is an implementation
defect in the passive path, never something to re-bless.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from collections.abc import Callable, Iterator
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

from tools.research.v6.e8 import parent_goldens as goldens

ROOT = Path(__file__).resolve().parents[2]
RECORD: dict[str, Any] = goldens.load_record()
CASES: list[dict[str, Any]] = RECORD["cases"]


def _label(case: dict[str, Any]) -> str:
    return goldens.case_label(case["condition"], case["scenario"], case["seat_a"], case["seat_b"], case["seed"])


def _lf_sha(content: bytes) -> str:
    return hashlib.sha256(content.replace(b"\r\n", b"\n")).hexdigest()


# ---------------------------------------------------------------------------
# The record
# ---------------------------------------------------------------------------


def test_the_record_pins_the_declared_matrix() -> None:
    assert RECORD["phase"] == "I8-1" and RECORD["clause"] == "D8-6"
    assert [(c["condition"], c["scenario"], c["seat_a"], c["seat_b"], c["seed"]) for c in CASES] == [
        (condition, scenario.name, seat_a, seat_b, seed) for condition, scenario, seat_a, seat_b, seed in goldens.cases()]
    assert len(CASES) == len(goldens.PARENTS) * len(goldens.SCENARIOS) * 2 * len(goldens.GOLDEN_SEEDS) == 72
    assert {c["condition"]: c["ruleset_id"] for c in CASES} == dict(goldens.PARENTS)


def test_the_definition_is_the_tools() -> None:
    recorded, live = RECORD["definition"], goldens.definition()
    for key in ("arena_size", "max_ticks", "quota", "golden_seeds", "scenarios", "orientations", "fixtures", "masked",
                "trace_line_endings"):
        assert recorded[key] == live[key], key
    assert goldens.PARENTS == {"C8": "bytefray-rules-6-research-sensing-r32",
                               "C8L": "bytefray-rules-6-research-disruption-slot1-sensing-r32"}


def test_the_parent_rulesets_keep_every_recorded_field() -> None:
    # Only the fields recorded at I8-1 are compared, so an additive, defaulted field (I8-2's
    # ``sensing_mode``) does not fail this check; its passive default is I8-2's own test.
    for condition, parent in RECORD["definition"]["parents"].items():
        assert parent["ruleset_id"] == goldens.PARENTS[condition]
        live = goldens.ruleset_snapshot(parent["ruleset_id"])
        assert {name: live.get(name, "<absent>") for name in parent["policy"]} == parent["policy"], condition
    assert RECORD["definition"]["parents"]["C8"]["policy"]["disruption_slot_limit"] is None
    assert RECORD["definition"]["parents"]["C8L"]["policy"]["disruption_slot_limit"] == 1
    assert {p["policy"]["detection_radius"] for p in RECORD["definition"]["parents"].values()} == {32}


def test_the_fixtures_are_the_recorded_tracked_sources() -> None:
    assert sorted(RECORD["definition"]["fixtures"]) == list(goldens.package_names())
    for name, files in RECORD["definition"]["fixtures"].items():
        assert goldens.fixture_fingerprint(name) == files, name
        assert set(files) == {"agent.py", "agent.yaml"}, name


def test_the_record_was_generated_by_the_committed_tool() -> None:
    provenance = RECORD["provenance"]
    committed = subprocess.run(["git", "show", f"{provenance['source_commit']}:{provenance['tool']}"], cwd=ROOT,
                               capture_output=True, check=True).stdout
    assert _lf_sha(committed) == provenance["tool_sha256"] == _lf_sha((ROOT / provenance["tool"]).read_bytes())
    engine_tree = subprocess.run(["git", "rev-parse", f"{provenance['source_commit']}:engine/src"], cwd=ROOT,
                                 capture_output=True, text=True, check=True).stdout.strip()
    assert engine_tree == provenance["engine_tree"]


def test_the_golden_seeds_are_infrastructure_not_experiment_seeds() -> None:
    seeds = RECORD["definition"]["golden_seeds"]
    assert seeds["values"] == list(goldens.GOLDEN_SEEDS) == [1, 2, 3]
    assert "not the E8 experiment seed set" in seeds["standing"]
    assert not list((ROOT / "tools" / "research" / "v6" / "e8").glob("seeds*"))
    assert "structural_matrix" not in json.dumps(RECORD)


def test_no_e8_mechanic_appears_in_the_goldens() -> None:
    for case in CASES:
        golden = case["golden"]
        assert set(golden["coverage"]["action_kinds"]) <= {"read", "write", "move"}, _label(case)
        assert golden["unknown_record_types"] == [], _label(case)


def test_the_goldens_exercise_what_the_e8_engine_change_could_disturb() -> None:
    for condition in goldens.PARENTS:
        rows = [case["golden"] for case in CASES if case["condition"] == condition]
        kinds = {kind for row in rows for kind in row["coverage"]["action_kinds"]}
        assert kinds == {"read", "write", "move"}, condition
        assert any(row["coverage"]["visible_decisions"] for row in rows), condition
        assert any(row["coverage"]["short_ticks"] for row in rows), condition
        assert any(set(row["coverage"]["first_movers"]) == {"A", "B"} for row in rows), condition
        assert {(case["seat_a"], case["seat_b"]) for case in CASES if case["condition"] == condition} == {
            pair for s in goldens.SCENARIOS for pair in ((s.first, s.second), (s.second, s.first))}, condition
        assert any(row["reason"] == "tick_limit" and row["ticks"] == goldens.MAX_TICKS for row in rows), condition
        assert any(row["reason"] == "last_agent_standing" for row in rows), condition
    # The two disruption durations differ in kind: whole-tick loses whole ticks, λ = 1 never does.
    assert any(case["golden"]["coverage"]["skipped_ticks"] for case in CASES if case["condition"] == "C8")
    assert not any(case["golden"]["coverage"]["skipped_ticks"] for case in CASES if case["condition"] == "C8L")


# ---------------------------------------------------------------------------
# Byte identity
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("case", CASES, ids=_label)
def test_parent_reproduces_its_pre_e8_golden(tmp_path: Path, case: dict[str, Any]) -> None:
    observed = goldens.describe(goldens.run_case(tmp_path, case["ruleset_id"], case["seat_a"], case["seat_b"],
                                                 case["seed"]))
    assert goldens.compare(case["golden"], observed) == []


@pytest.mark.parametrize("condition", list(goldens.PARENTS))
def test_tracing_does_not_change_the_match(tmp_path: Path, condition: str) -> None:
    case = next(c for c in CASES if c["condition"] == condition and c["golden"]["coverage"]["action_kinds"].get("read"))
    traced = goldens.run_case(tmp_path / "t", case["ruleset_id"], case["seat_a"], case["seat_b"], case["seed"])
    untraced = goldens.run_case(tmp_path / "u", case["ruleset_id"], case["seat_a"], case["seat_b"], case["seed"],
                                traced=False)
    assert untraced.trace_path is None
    assert traced.replay_path.read_bytes() == untraced.replay_path.read_bytes()
    assert (traced.result_id, traced.match_id) == (untraced.result_id, untraced.match_id)


def test_recording_is_deterministic(tmp_path: Path) -> None:
    case = CASES[0]
    first = goldens.describe(goldens.run_case(tmp_path / "1", case["ruleset_id"], case["seat_a"], case["seat_b"],
                                              case["seed"]))
    second = goldens.describe(goldens.run_case(tmp_path / "2", case["ruleset_id"], case["seat_a"], case["seat_b"],
                                               case["seed"]))
    assert first == second == case["golden"]


# ---------------------------------------------------------------------------
# Every compared fact detects a change
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def reference(tmp_path_factory: pytest.TempPathFactory) -> Iterator[tuple[goldens.Artifacts, dict[str, Any]]]:
    case = next(c for c in CASES if c["condition"] == "C8" and c["scenario"] == "rush-vs-guard")
    root = tmp_path_factory.mktemp("reference")
    artifacts = goldens.run_case(root, case["ruleset_id"], case["seat_a"], case["seat_b"], case["seed"])
    description = goldens.describe(artifacts)
    assert goldens.compare(case["golden"], description) == []
    yield artifacts, description


def _mutated(artifacts: goldens.Artifacts, target: Path, *, trace: Callable[[list[str]], list[str]] | None = None,
             replay: Callable[[bytes], bytes] | None = None) -> goldens.Artifacts:
    target.mkdir(parents=True, exist_ok=True)
    replay_path, trace_path = target / "replay.jsonl", target / "trace.jsonl"
    shutil.copyfile(artifacts.replay_path, replay_path)
    assert artifacts.trace_path is not None
    shutil.copyfile(artifacts.trace_path, trace_path)
    if replay is not None:
        replay_path.write_bytes(replay(replay_path.read_bytes()))
    if trace is not None:
        lines = trace_path.read_bytes().decode("utf-8").split("\n")[:-1]
        trace_path.write_bytes(("\n".join(trace(lines)) + "\n").encode("utf-8"))
    return replace(artifacts, replay_path=replay_path, trace_path=trace_path)


def _edit_records(record_type: str, edit: Callable[[dict[str, Any]], None], *, first_only: bool = False
                  ) -> Callable[[list[str]], list[str]]:
    """Re-serialize matching trace records after ``edit``, exactly as the engine serializes them."""

    def apply(lines: list[str]) -> list[str]:
        out, done = [], False
        for line in lines:
            record = json.loads(line)
            if record.get("record_type") == record_type and not (first_only and done):
                edit(record)
                line, done = json.dumps(record, sort_keys=True), True
            out.append(line)
        return out

    return apply


def _changed_keys(reference: tuple[goldens.Artifacts, dict[str, Any]], mutated: goldens.Artifacts) -> set[str]:
    _, description = reference
    return {problem.split(":", 1)[0] for problem in goldens.compare(description, goldens.describe(mutated))}


def test_a_null_field_added_to_reset_records_is_detected(tmp_path: Path, reference: Any) -> None:
    # The case the research lead named: an optional field serialized as ``null`` while inactive.
    mutated = _mutated(reference[0], tmp_path, trace=_edit_records("reset", lambda r: r.update(sensing_window=None)))
    assert {"trace_sha256", "trace_record_sha256"} <= _changed_keys(reference, mutated)


def test_a_null_observation_field_is_detected_in_the_d8_3_surface(tmp_path: Path, reference: Any) -> None:
    mutated = _mutated(reference[0], tmp_path, trace=_edit_records(
        "decision_v2", lambda r: r["observation"].update(previous_sense_anchors=None)))
    assert {"trace_sha256", "trace_record_sha256", "d8_3_surface_sha256"} <= _changed_keys(reference, mutated)


def test_a_null_result_field_is_detected(tmp_path: Path, reference: Any) -> None:
    mutated = _mutated(reference[0], tmp_path, trace=_edit_records(
        "decision_v2", lambda r: r["applied_result"].update(sensed_anchors=None)))
    assert {"trace_sha256", "trace_record_sha256"} <= _changed_keys(reference, mutated)


def test_a_changed_action_is_detected(tmp_path: Path, reference: Any) -> None:
    mutated = _mutated(reference[0], tmp_path, trace=_edit_records(
        "decision_v2", lambda r: r["action"].update(operand=r["action"]["operand"] + 1), first_only=True))
    assert {"trace_sha256", "trace_record_sha256", "d8_3_surface_sha256"} <= _changed_keys(reference, mutated)


def test_changed_key_order_is_detected(tmp_path: Path, reference: Any) -> None:
    def reorder(lines: list[str]) -> list[str]:
        record = json.loads(lines[1])
        return [lines[0], json.dumps(dict(reversed(list(record.items())))), *lines[2:]]

    assert "trace_sha256" in _changed_keys(reference, _mutated(reference[0], tmp_path, trace=reorder))


def test_a_dropped_or_added_record_is_detected(tmp_path: Path, reference: Any) -> None:
    dropped = _mutated(reference[0], tmp_path / "dropped", trace=lambda lines: lines[:-2] + lines[-1:])
    assert {"trace_sha256", "trace_lines"} <= _changed_keys(reference, dropped)
    added = _mutated(reference[0], tmp_path / "added",
                     trace=lambda lines: [*lines, json.dumps({"record_type": "sense_probe"}, sort_keys=True)])
    assert {"trace_sha256", "trace_lines", "unknown_record_types"} <= _changed_keys(reference, added)


def test_a_changed_binding_is_detected(tmp_path: Path, reference: Any) -> None:
    mutated = _mutated(reference[0], tmp_path, trace=_edit_records("binding", lambda r: r.update(replay_sha256="0" * 64)))
    assert {"trace_sha256", "trace_record_sha256"} <= _changed_keys(reference, mutated)


def test_a_changed_replay_byte_is_detected(tmp_path: Path, reference: Any) -> None:
    mutated = _mutated(reference[0], tmp_path, replay=lambda data: data[:-2] + bytes([data[-2] ^ 1]) + data[-1:])
    assert _changed_keys(reference, mutated) == {"replay_sha256"}


@pytest.mark.parametrize(("field", "value"), [
    ("result_id", "result_000000000000000000000000"), ("match_id", "match_000000000000000000000000"),
    ("winner", "Z"), ("ticks", 999), ("reason", "other"),
])
def test_a_changed_result_fact_is_detected(tmp_path: Path, reference: Any, field: str, value: Any) -> None:
    mutated = replace(_mutated(reference[0], tmp_path), **{field: value})
    assert _changed_keys(reference, mutated) == {field}


def test_line_endings_alone_are_normalized_by_design(tmp_path: Path, reference: Any) -> None:
    lf = _mutated(reference[0], tmp_path / "lf", trace=lambda lines: [line.rstrip("\r") for line in lines])
    crlf = _mutated(reference[0], tmp_path / "crlf", trace=lambda lines: [line.rstrip("\r") + "\r" for line in lines])
    assert _changed_keys(reference, lf) == _changed_keys(reference, crlf) == set()


def test_wall_time_alone_is_masked_by_design(tmp_path: Path, reference: Any) -> None:
    def retime(record: dict[str, Any]) -> None:
        if "wall_time_ms" in record:
            record["wall_time_ms"] = 123.456

    mutated = _mutated(reference[0], tmp_path, trace=lambda lines: _edit_records("reset", retime)(
        _edit_records("decision_v2", retime)(lines)))
    assert _changed_keys(reference, mutated) == set()


def test_a_tampered_golden_is_detected(reference: Any) -> None:
    _, description = reference
    for key in description:
        tampered = {**description, key: "tampered"}
        assert [problem.split(":", 1)[0] for problem in goldens.compare(tampered, description)] == [key]
