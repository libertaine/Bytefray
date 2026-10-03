"""The frozen V6 E4 experiment definition, contest classes, pre-registration and
runner guards (design review Sec D.1, Sec M, Sec N, Sec O, Sec P, Sec Q, Sec R).

Nothing here runs an E4 matrix cell or any treatment match; the dry-run test
plans cells with the real evaluation planner and executes nothing.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import re
import shutil
from itertools import combinations
from pathlib import Path

import pytest
from battle_engine.ruleset_policy import resolve_ruleset_policy

from tools.research.v6.e3 import matrix as e3_matrix
from tools.research.v6.e4 import contest_classes, matrix, run_e4
from tools.research.v6.e4.preregistration import (
    PREREGISTRATION_PATH,
    REQUIRED_HYPOTHESES,
    PreregistrationError,
    load_preregistration,
)
from tools.research.v6.experiment_harness import REPO_ROOT, plan_evaluation_requests

REVIEW = REPO_ROOT / "docs" / "research" / "v6" / "V6_E4_ORDER_VS_EVALUATION_TIMING_DESIGN_REVIEW.md"
REVIEW_SHA256 = "5d9290c0cf5ebbd85d80956e504f9cd3f1f7e1e1ef9a811dae7e2fec87990cc0"
E4_AGENTS = ("v4_probe", "e2_sniper", "e2_repair_guard", "e2_disrupt_guard", "e2_min_guard", "e2_greedy_painter",
             "e2_guarded_painter", "e2_spread_sniper", "e2_spread_defender")


# ---------------------------------------------------------------------------
# Frozen definition
# ---------------------------------------------------------------------------


def test_fields_and_expected_match_counts() -> None:
    assert [(f.field_id, len(f.pairs), f.orientations, f.max_ticks, f.expected_matches) for f in matrix.FIELDS] == [
        ("F1", 36, 2, 1000, 2304),
        ("F2", 9, 2, 1000, 576),
        ("F2-P", 9, 1, 1001, 288),
        ("F4", 10, 2, 1000, 640),
    ]
    assert matrix.matches_per_condition() == 3808
    assert matrix.matches_total() == 15232
    assert 2 * matrix.matches_per_condition() == 7616  # the primary study (C-E4 + T-E4)


def test_the_field_is_the_e2_set_minus_e2_counter() -> None:
    # Sec S-9: excluded on a source proof (lambda = 1 makes it the greedy painter), never re-added.
    assert matrix.EXCLUDED_AGENTS == ("e2_counter",)
    assert matrix.E4_AGENTS == E4_AGENTS
    assert set(e3_matrix.E2_AGENTS) - set(matrix.E4_AGENTS) == {"e2_counter"}
    for field in matrix.FIELDS:
        assert not any("counter" in agent for agent in field.agents), field.field_id
    assert matrix.F1.pairs == tuple(combinations(E4_AGENTS, 2))
    assert matrix.F2.pairs == matrix.F2P.pairs == tuple((a, f"{a}_twin") for a in E4_AGENTS)
    assert matrix.F4.pairs == (*(("e3_jam_sniper", a) for a in E4_AGENTS), ("e3_jam_sniper", "e3_jam_sniper_twin"))


def test_strata_are_never_pooled() -> None:
    assert matrix.STANDARD_FIELDS == ("F1", "F2")
    assert (matrix.F2P.stratum, matrix.F4.stratum) == (matrix.TICK_PARITY_REPLICATE, matrix.JAMMER)
    assert matrix.MIRROR_FIELDS == ("F2", "F2-P")


def test_seeds_arena_ticks_orientations_and_overrides_are_frozen() -> None:
    assert matrix.SEEDS == tuple(range(1, 33))
    assert (matrix.ARENA_SIZE, matrix.MAX_TICKS, matrix.PARITY_MAX_TICKS, matrix.QUOTA) == (512, 1000, 1001, 8)
    assert [f.both_orientations for f in matrix.FIELDS] == [True, True, False, True]
    assert matrix.FORBIDDEN_REQUEST_OVERRIDES == (
        "scheduler_chunk_size", "scheduler_rotate_start", "kill_weight", "instr_per_tick")


def test_four_conditions_each_treatment_one_field_from_its_parent() -> None:
    table = {c.condition_id: (c.ruleset_id, c.role, c.arm, c.parent, c.capture_hold_ticks, c.disruption_slot_limit,
                              c.scheduler_pass_order, c.historical_condition) for c in matrix.CONDITIONS}
    assert table == {
        "C-E4": ("bytefray-rules-6-research-capture-hold-k2-disruption-slot1", "control", "primary", None, 2, 1,
                 "forward", "T-E3"),
        "T-E4": ("bytefray-rules-6-research-capture-hold-k2-disruption-slot1-mirrored-passes", "treatment", "primary",
                 "C-E4", 2, 1, "mirrored", None),
        "C-E4K1": ("bytefray-rules-6-research-disruption-slot1", "control", "companion", None, 1, 1, "forward",
                   "T-E3K1"),
        "T-E4K1": ("bytefray-rules-6-research-disruption-slot1-mirrored-passes", "treatment", "companion", "C-E4K1",
                   1, 1, "mirrored", None),
    }
    matrix.verify_ruleset_registry()
    for c in matrix.CONDITIONS:
        assert resolve_ruleset_policy(c.ruleset_id).scheduler_pass_order == c.scheduler_pass_order


def test_historical_parent_provenance_is_recorded_and_never_renamed() -> None:
    definition = matrix.matrix_definition()
    assert definition["historical_parent"] == {
        "matrix_id": "v6-e3-matrix-v1-634132ec3c15",
        "matrix_digest": e3_matrix.E3_MATRIX_DIGEST,
        "freeze_id": "v6-e3-freeze-v1-506811e78ad8",
        "generation": {"engine_tree": "67b73c9ae7d40209ef68e9512a58c5adfef0ac2f",
                       "source_commit": "6f0fd3f3fb7fc6203daba5b9e049b4a4e58e801e"},
        "conditions": {"C-E4": "T-E3", "C-E4K1": "T-E3K1"},
    }
    assert e3_matrix.matrix_id() == "v6-e3-matrix-v1-634132ec3c15"
    assert definition["parent_freeze"] == {"commit": "b144e1d", "matches": 96,
                                           "path": "engine/tests/test_v6_e4_parent_byte_identity.py"}


def test_fingerprints_are_e3s_frozen_values_for_the_e4_roster() -> None:
    roster = {*E4_AGENTS, *(f"{a}_twin" for a in E4_AGENTS), "e3_jam_sniper", "e3_jam_sniper_twin"}
    assert set(matrix.AGENT_FINGERPRINTS) == roster
    assert all(matrix.AGENT_FINGERPRINTS[n] == e3_matrix.AGENT_FINGERPRINTS[n] for n in roster)
    assert run_e4.verify_agent_fingerprints(sorted(roster)) == matrix.AGENT_FINGERPRINTS


def test_matrix_definition_is_frozen() -> None:
    assert matrix.matrix_digest() == matrix.E4_MATRIX_DIGEST
    assert matrix.matrix_id() == f"v6-e4-matrix-v1-{matrix.E4_MATRIX_DIGEST[:12]}"
    definition = matrix.matrix_definition()
    assert definition["contest_classes_sha256"] == contest_classes.CONTEST_CLASSES_SHA256
    assert definition["matches_total"] == 15232
    matrix.verify_frozen_matrix()


def test_any_definition_change_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(matrix, "SEEDS", tuple(range(1, 32)))
    with pytest.raises(matrix.MatrixDefinitionError, match="digest"):
        matrix.verify_frozen_matrix()


def test_one_agent_reintroduced_changes_the_digest(monkeypatch: pytest.MonkeyPatch) -> None:
    with_counter = (*E4_AGENTS, "e2_counter")
    monkeypatch.setattr(matrix, "F1", dataclasses.replace(matrix.F1, agents=with_counter,
                                                          pairs=tuple(combinations(with_counter, 2))))
    monkeypatch.setattr(matrix, "FIELDS", (matrix.F1, matrix.F2, matrix.F2P, matrix.F4))
    assert matrix.matrix_digest() != matrix.E4_MATRIX_DIGEST
    with pytest.raises(matrix.MatrixDefinitionError):
        matrix.verify_frozen_matrix()


def test_registry_drift_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    drifted = dataclasses.replace(matrix.condition("T-E4"), scheduler_pass_order="forward")
    monkeypatch.setattr(matrix, "CONDITIONS", tuple(drifted if c.condition_id == "T-E4" else c
                                                    for c in matrix.CONDITIONS))
    with pytest.raises(matrix.MatrixDefinitionError, match="T-E4"):
        matrix.verify_ruleset_registry()


def test_fingerprint_drift_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(matrix, "AGENT_FINGERPRINTS", dict(matrix.AGENT_FINGERPRINTS, e3_jam_sniper="0" * 64))
    with pytest.raises(run_e4.E4ConfigurationError, match="fingerprints"):
        run_e4.verify_agent_fingerprints(list(matrix.F4.agents))


# ---------------------------------------------------------------------------
# Contest classes (a priori, from Sec D.1 source roles)
# ---------------------------------------------------------------------------


def test_contest_class_table_is_frozen_and_derives_from_the_source_roles() -> None:
    table = contest_classes.load_table()
    assert contest_classes.table_sha256() == contest_classes.CONTEST_CLASSES_SHA256
    assert table == contest_classes.build_table(matrix.contest_class_fields())
    assert {f: len(rows) for f, rows in table["classes"].items()} == {"F1": 36, "F2": 9, "F2-P": 9, "F4": 10}


def test_contest_classes_match_every_pairing_the_review_classifies() -> None:
    # Sec D.2 and Sec L name these pairings' mechanisms; the source-role derivation agrees.
    named = {
        ("e2_sniper", "e2_disrupt_guard"): "MULTI-PASS",
        ("v4_probe", "e2_disrupt_guard"): "MULTI-PASS",
        ("e2_repair_guard", "e2_sniper"): "MULTI-PASS",
        ("e2_sniper", "e2_min_guard"): "OPENING-ONLY",
        ("e2_sniper", "e2_spread_defender"): "OPENING-ONLY",
        ("e2_guarded_painter", "e2_min_guard"): "OPENING-ONLY",
        ("e2_guarded_painter", "e2_guarded_painter_twin"): "OPENING-ONLY",
        ("e2_repair_guard", "e2_guarded_painter"): "OPENING-ONLY",
        ("e2_disrupt_guard", "e2_disrupt_guard_twin"): "OPENING-ONLY",
        ("e2_greedy_painter", "e2_disrupt_guard"): "INCIDENTAL",
        ("e2_greedy_painter", "e2_min_guard"): "INCIDENTAL",
    }
    for (a, b), expected in named.items():
        assert contest_classes.classify(a, b) == contest_classes.classify(b, a) == expected, (a, b)
    table = contest_classes.load_table()
    assert contest_classes.class_of(table, "F1", "e2_disrupt_guard", "e2_sniper") == "MULTI-PASS"
    assert contest_classes.class_of(table, "F4", "e3_jam_sniper", "e2_min_guard") == "OPENING-ONLY"


def test_contest_class_is_a_function_of_source_roles_alone() -> None:
    # The classifier takes two agent names and nothing else: no outcome can reach it.
    import inspect

    assert list(inspect.signature(contest_classes.classify).parameters) == ["first", "second"]
    assert contest_classes.roles_of("e2_sniper_twin") == contest_classes.roles_of("e2_sniper")


def test_an_edited_contest_class_fails_closed(tmp_path: Path) -> None:
    copy = tmp_path / "contest_classes.json"
    table = json.loads(contest_classes.CONTEST_CLASSES_PATH.read_text(encoding="utf-8"))
    table["classes"]["F1"]["e2_sniper|e2_disrupt_guard"] = "OPENING-ONLY"
    copy.write_bytes(contest_classes.canonical_bytes(table))
    with pytest.raises(contest_classes.ContestClassError, match="SHA-256"):
        contest_classes.load_table(copy)
    with pytest.raises(contest_classes.ContestClassError, match="derive"):
        contest_classes.load_table(copy, expected_sha256=contest_classes.table_sha256(copy))


# ---------------------------------------------------------------------------
# Pre-registration: verbatim against the design review
# ---------------------------------------------------------------------------


def _clean(text: str) -> str:
    # Markdown emphasis (** and *), code spans and pipe escapes are formatting, not wording.
    return re.sub(r"\s+", " ", text.replace("\\|", "|").replace("*", "").replace("`", "")).strip()


def _section(start: str, end: str) -> str:
    text = REVIEW.read_text(encoding="utf-8")
    return text[text.index(start) : text.index(end, text.index(start))]


def _items(block: str) -> list[str]:
    items: list[str] = []
    for line in block.splitlines():
        if re.match(r"^(- |\d+\. )", line):
            items.append(re.sub(r"^(- |\d+\. )", "", line))
        elif re.match(r"^\s+- ", line) and items:
            items[-1] += " " + re.sub(r"^\s+- ", "", line)
    return [_clean(item) for item in items]


def _table_rows(block: str) -> list[list[str]]:
    rows = []
    for line in block.splitlines():
        if line.startswith("|") and not re.match(r"^\|\s*-", line):
            rows.append([_clean(cell) for cell in re.split(r"(?<!\\)\|", line.strip())[1:-1]])
    return rows[1:]


def test_the_design_review_is_the_preserved_one() -> None:
    assert hashlib.sha256(REVIEW.read_bytes()).hexdigest() == REVIEW_SHA256


def test_hypotheses_are_the_design_review_sec_n_table_verbatim() -> None:
    prereg = load_preregistration()
    rows = _table_rows(_section("| ID ", "**Pre-registered interpretation.**"))
    assert [row[0] for row in rows] == [*REQUIRED_HYPOTHESES[:-1], "D9′"]
    for row, item in zip(rows, prereg["hypotheses"], strict=True):
        assert [item["review_id"], item["statement"], item["supported_if"], item["refuted_if"],
                item["probe_prior"]] == row


def test_interpretation_table_and_threshold_rationale_are_verbatim() -> None:
    prereg = load_preregistration()
    rows = _table_rows(_section("| Result ", "**Threshold rationale.**"))
    assert [[r["result"], r["conclusion"]] for r in prereg["interpretation"]] == rows
    assert prereg["interpretation_note"] == 'Pre-registered interpretation. "A clean negative is reachable" (H0).'
    assert prereg["threshold_rationale"] == _items(_section("**Threshold rationale.**", "---"))


def test_populations_metrics_evidence_rules_and_hard_stops_are_verbatim() -> None:
    prereg = load_preregistration()
    assert prereg["populations"]["items"] == _items(_section("**Populations**", "| ID "))
    metrics = prereg["metrics"]
    assert [[m["metric"], m["definition"]] for m in metrics["seat_metrics"]] == _table_rows(
        _section("| Metric | Definition |", "**Twin mirrors.**"))
    assert metrics["twin_mirrors"] == _items(_section("**Twin mirrors.**", "Relabel identity is a gate"))
    assert metrics["parity"] == _items(_section("### M.2 Parity metrics", "| Class | Definition |"))
    assert [[t["class"], t["definition"]] for t in metrics["transition_classes"]] == _table_rows(
        _section("| Class | Definition |", "### M.3"))
    assert metrics["weighting"] == _items(_section("### M.3 Weighting", "---"))
    assert prereg["evidence_rules"] == _items(_section("## P. Evidence Rules", "---"))
    assert prereg["hard_stops"] == _items(_section("**Hard stops**", "There is **no prefix gate**"))
    assert len(prereg["evidence_rules"]) == 8 and len(prereg["hard_stops"]) == 12


def test_criteria_carry_the_registered_numbers() -> None:
    criteria = {h["id"]: h["criterion"] for h in load_preregistration()["hypotheses"]}
    assert criteria["E4-H0"]["stays_or_unchanged_neutral_min"] == "0.90"
    assert criteria["E4-H0"]["requires"] == {"E4-H1": "REFUTED"}
    assert (criteria["E4-H1"]["multi_pass_neutralized_or_weakened_min"], criteria["E4-H1"]["follows_final_overall_max"],
            criteria["E4-H1"]["refuted_multi_pass_neutralized_or_weakened_max"]) == ("2/3", "1/10", "1/10")
    assert (criteria["E4-H2"]["multi_pass_follows_final_min"],
            criteria["E4-H2"]["refuted_multi_pass_follows_final_max"]) == ("2/3", "1/10")
    assert (criteria["E4-H3"]["opening_only_stays_min"], criteria["E4-H3"]["refuted_opening_only_stays_max"]) == (
        "2/3", "1/10")
    assert (criteria["E4-H4"]["companion_change_share_min"], criteria["E4-H4"]["primary_change_share_max"],
            criteria["E4-H4"]["refuted_companion_change_share_max"]) == ("0.10", "0.02", "0.02")
    assert criteria["E4-H5"]["become_captures_min"] == "0.10"
    assert (criteria["E4-H6"]["tick_limit_rise_min"], criteria["E4-H6"]["static_swing_ticks_below"]) == ("0.10", 10)
    assert (criteria["E4-H7"]["abs_gsb_max"], criteria["E4-H7"]["scd_min"], criteria["E4-H7"]["n_distinct_min"]) == (
        "0.10", "0.5", 8)
    assert criteria["D9-PRIME"] == {"condition": "T-E4", "completions_against_guards_max": 0, "hard_stop": True}
    stats = load_preregistration()["statistics"]
    assert (stats["min_distinct_for_rate_claim"], stats["fma_min_both_alive_ticks_per_parity"],
            stats["fms_fps_min_swings"]) == (8, 10, 10)
    assert stats["fma_bands"] == {"strong_first_min": "3/2", "moderate_first_min": "1/2", "neutral_abs_below": "1/2",
                                  "moderate_last_max": "-1/2", "strong_last_max": "-3/2"}


def test_interpretation_rules_are_the_literal_reading() -> None:
    rules = {row["result"]: row["rule"] for row in load_preregistration()["interpretation"]}
    assert rules["H1 ∧ H3 ∧ ¬H2"] == {"kind": "all", "requires": {
        "E4-H1": "SUPPORTED", "E4-H3": "SUPPORTED", "E4-H2": "REFUTED"}}
    assert rules["¬H1 ∧ H3"] == {"kind": "all", "requires": {"E4-H1": "REFUTED", "E4-H3": "SUPPORTED"}}
    assert rules["H5, H6, H8"] == {"kind": "any_supported", "hypotheses": ["E4-H5", "E4-H6", "E4-H8"]}
    assert rules["none"] == {"kind": "none"}


def test_changing_a_preregistered_criterion_fails_closed(tmp_path: Path) -> None:
    copy = tmp_path / "preregistration.json"
    shutil.copy(PREREGISTRATION_PATH, copy)
    data = json.loads(copy.read_text(encoding="utf-8"))
    data["hypotheses"][1]["criterion"]["multi_pass_neutralized_or_weakened_min"] = "1/2"
    copy.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    with pytest.raises(PreregistrationError, match="digest"):
        load_preregistration(copy)


# ---------------------------------------------------------------------------
# Runner guards (nothing executes)
# ---------------------------------------------------------------------------


def _requests(tmp_path: Path, condition_id: str, field_id: str, **changes: object) -> tuple:
    config = run_e4.experiment_config(condition_id, field_id, output_dir=tmp_path / "out")
    config = dataclasses.replace(config, **changes)  # type: ignore[arg-type]
    return plan_evaluation_requests(config, matrix.ARENA_SIZE, tmp_path / "plan", tmp_path / "env"), config


@pytest.mark.parametrize("condition_id", [c.condition_id for c in matrix.CONDITIONS])
@pytest.mark.parametrize("field_id", matrix.FIELD_IDS)
def test_planned_requests_match_the_frozen_definition(tmp_path: Path, condition_id: str, field_id: str) -> None:
    requests, _ = _requests(tmp_path, condition_id, field_id)
    run_e4.check_requests(requests, condition_id, field_id)
    field = matrix.field(field_id)
    assert {r.ticks for r in requests} == {field.max_ticks}
    assert {r.both_orientations for r in requests} == {field.both_orientations}
    assert {r.ruleset_id for r in requests} == {matrix.condition(condition_id).ruleset_id}


@pytest.mark.parametrize(
    ("override", "value"),
    [("scheduler_chunk_size", 1), ("scheduler_rotate_start", False), ("kill_weight", 1.0), ("instr_per_tick", 4)],
)
def test_any_request_override_fails_closed(tmp_path: Path, override: str, value: object) -> None:
    requests, _ = _requests(tmp_path, "C-E4", "F1")
    tampered = [dataclasses.replace(r, **{override: value}) for r in requests]
    with pytest.raises(run_e4.E4ConfigurationError, match="forbidden override"):
        run_e4.check_requests(tampered, "C-E4", "F1")


@pytest.mark.parametrize("change", [{"ticks": 1000}, {"seeds": tuple(range(1, 32))}, {"arena_sizes": (1024,)},
                                    {"both_orientations": True}])
def test_frozen_setting_drift_fails_closed(tmp_path: Path, change: dict[str, object]) -> None:
    config = run_e4.experiment_config("C-E4", "F2-P", output_dir=tmp_path / "out")
    config = dataclasses.replace(config, **change)  # type: ignore[arg-type]
    requests = plan_evaluation_requests(config, config.arena_sizes[0], tmp_path / "plan", tmp_path / "env")
    with pytest.raises(run_e4.E4ConfigurationError):
        run_e4.check_requests(requests, "C-E4", "F2-P")


def test_execute_never_runs_without_explicit_confirmation(tmp_path: Path) -> None:
    with pytest.raises(run_e4.E4ConfigurationError, match="confirm"):
        run_e4.execute("C-E4", "F1", run_root=tmp_path)
    assert not tmp_path.joinpath(matrix.matrix_id()).exists()


@pytest.mark.parametrize("condition_id", ["T-E4", "T-E4K1"])
def test_treatment_needs_separate_authorization_and_the_unlock_chain(tmp_path: Path, condition_id: str) -> None:
    with pytest.raises(run_e4.E4ConfigurationError, match="separate authorization"):
        run_e4.execute(condition_id, "F1", run_root=tmp_path, confirm=True)
    # Even with both confirmations, no committed freeze and control qualification -> no run.
    with pytest.raises(Exception, match="freeze|qualification|record"):
        run_e4.execute(condition_id, "F1", run_root=tmp_path, confirm=True, confirm_treatment=True,
                       freeze_path=tmp_path / "missing.json")
    assert not tmp_path.joinpath(matrix.matrix_id()).exists()


def test_treatment_artifacts_stop_every_control_phase_command(tmp_path: Path) -> None:
    run_e4.assert_no_treatment_artifacts(tmp_path)
    (tmp_path / matrix.matrix_id() / "T-E4K1").mkdir(parents=True)
    with pytest.raises(run_e4.TreatmentExposureError, match="STOP"):
        run_e4.assert_no_treatment_artifacts(tmp_path)
    for command in (run_e4.reproduce, run_e4.qualify, run_e4.freeze_populations, run_e4.run_d9,
                    run_e4.run_manipulation):
        with pytest.raises(run_e4.TreatmentExposureError):
            command(run_root=tmp_path)  # type: ignore[operator]
    with pytest.raises(run_e4.TreatmentExposureError):
        run_e4.write_corpus_telemetry("C-E4", run_root=tmp_path)


def test_treatment_telemetry_is_also_a_treatment_artifact(tmp_path: Path) -> None:
    (tmp_path / matrix.matrix_id() / "freezes" / "some-freeze" / "telemetry" / "T-E4").mkdir(parents=True)
    with pytest.raises(run_e4.TreatmentExposureError):
        run_e4.assert_no_treatment_artifacts(tmp_path)


def test_dry_run_counts_one_field_with_the_real_planner_and_runs_nothing() -> None:
    row = run_e4.dry_run_plan("T-E4", "F2-P")
    assert (row["planned_cells"], row["expected_cells"], row["ticks"], row["consistent"]) == (288, 288, 1001, True)
    assert row["orientations"] == ["candidate_first"] and row["seeds"] == 32
    assert row["rulesets"] == ["bytefray-rules-6-research-capture-hold-k2-disruption-slot1-mirrored-passes"]
