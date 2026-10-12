"""The frozen V6 E3 experiment definition, pre-registration and runner guards
(design review Sec J, Sec K, Sec L, Sec M, Sec N).

Nothing here runs an E3 matrix cell or any treatment match; the dry-run test
plans cells with the real evaluation planner and executes nothing.
"""

from __future__ import annotations

import dataclasses
import json
import re
import shutil
from itertools import combinations
from pathlib import Path

import pytest
from battle_engine.ruleset_policy import resolve_ruleset_policy

from tools.research.v6.e2 import matrix as e2_matrix
from tools.research.v6.e3 import matrix, run_e3
from tools.research.v6.e3.preregistration import (
    PREREGISTRATION_PATH,
    REQUIRED_HYPOTHESES,
    PreregistrationError,
    load_preregistration,
)
from tools.research.v6.experiment_harness import REPO_ROOT, plan_evaluation_requests

REVIEW = REPO_ROOT / "docs" / "research" / "v6" / "V6_E3_SLOT_LIMITED_DISRUPTION_DESIGN_REVIEW.md"
REVIEW_SHA256 = "c0d0f711942a2d73b0e4d02fe5b4b1e85334142a9560515c3c6c2b221d1a6b18"


# ---------------------------------------------------------------------------
# Frozen definition
# ---------------------------------------------------------------------------


def test_fields_and_expected_match_counts() -> None:
    assert [(f.field_id, len(f.pairs), f.max_ticks, f.expected_matches) for f in matrix.FIELDS] == [
        ("F1", 45, 1000, 2880),
        ("F2", 10, 1000, 640),
        ("F2-P", 10, 1001, 640),
        ("F4", 11, 1000, 704),
    ]
    assert matrix.matches_per_condition() == 4864
    assert matrix.matches_total() == 19456
    # F1 and F2 are E2's fields, unchanged; F2-P is F2 at 1001 ticks.
    assert matrix.F1.pairs == e2_matrix.F1.pairs == tuple(combinations(e2_matrix.E2_AGENTS, 2))
    assert matrix.F1.agents == e2_matrix.F1.agents and matrix.F1.pairing == "triangular"
    assert matrix.F2.pairs == e2_matrix.F2.pairs == matrix.F2P.pairs
    assert matrix.F4.pairs == (*((matrix.F4.agents[0], a) for a in e2_matrix.E2_AGENTS),
                               ("e3_jam_sniper", "e3_jam_sniper_twin"))
    # F3 (historical reference agents) is dropped.
    assert "F3" not in matrix.FIELD_IDS
    assert not set(e2_matrix.F3_REFERENCE) & {a for f in matrix.FIELDS for a in f.agents}
    assert matrix.STANDARD_FIELDS == ("F1", "F2", "F4")


def test_seeds_arena_orientations_and_overrides_are_frozen() -> None:
    assert matrix.SEEDS == tuple(range(1, 33))
    assert (matrix.ARENA_SIZE, matrix.MAX_TICKS, matrix.PARITY_MAX_TICKS, matrix.QUOTA) == (512, 1000, 1001, 8)
    assert matrix.BOTH_ORIENTATIONS is True
    assert matrix.FORBIDDEN_REQUEST_OVERRIDES == (
        "scheduler_chunk_size", "scheduler_rotate_start", "kill_weight", "instr_per_tick")


def test_four_conditions_each_treatment_one_field_from_its_parent() -> None:
    assert [(c.condition_id, c.ruleset_id, c.role, c.arm, c.parent, c.capture_hold_ticks, c.disruption_slot_limit)
            for c in matrix.CONDITIONS] == [
        ("C-E2", "bytefray-rules-6-research-capture-hold-k2", "control", "primary", None, 2, None),
        ("T-E3", "bytefray-rules-6-research-capture-hold-k2-disruption-slot1", "treatment", "primary", "C-E2", 2, 1),
        ("C-RS", "bytefray-rules-6-research-scale", "control", "companion", None, 1, None),
        ("T-E3K1", "bytefray-rules-6-research-disruption-slot1", "treatment", "companion", "C-RS", 1, 1),
    ]
    matrix.verify_ruleset_registry()
    for item in matrix.CONDITIONS:
        policy = resolve_ruleset_policy(item.ruleset_id)
        assert (policy.scheduler_chunk_size, policy.scheduler_rotate_start) == (2, True)


def test_matrix_definition_is_frozen() -> None:
    assert matrix.matrix_digest() == matrix.E3_MATRIX_DIGEST
    assert matrix.matrix_id() == f"v6-e3-matrix-v1-{matrix.E3_MATRIX_DIGEST[:12]}"
    matrix.verify_frozen_matrix()
    definition = matrix.matrix_definition()
    assert definition["matches_total"] == 19456
    assert definition["historical_parent"] == {"matrix_id": e2_matrix.matrix_id(),
                                               "conditions": {"C-E2": "T-E2", "C-RS": "C-RS"}}
    # The twenty reused E2 fingerprints are E2's frozen ones.
    for name in (*e2_matrix.E2_AGENTS, *e2_matrix.E2_TWINS):
        assert matrix.AGENT_FINGERPRINTS[name] == e2_matrix.AGENT_FINGERPRINTS[name]


def test_any_definition_change_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(matrix, "SEEDS", tuple(range(1, 32)))
    with pytest.raises(matrix.MatrixDefinitionError, match="digest"):
        matrix.verify_frozen_matrix()


def test_one_field_count_change_changes_the_digest(monkeypatch: pytest.MonkeyPatch) -> None:
    shorter = dataclasses.replace(matrix.F4, pairs=matrix.F4.pairs[:-1])
    monkeypatch.setattr(matrix, "FIELDS", (matrix.F1, matrix.F2, matrix.F2P, shorter))
    assert matrix.matches_total() != 19456
    with pytest.raises(matrix.MatrixDefinitionError):
        matrix.verify_frozen_matrix()


def test_registry_drift_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    drifted = dataclasses.replace(matrix.CONDITIONS[1], disruption_slot_limit=2)
    monkeypatch.setattr(matrix, "CONDITIONS", (matrix.CONDITIONS[0], drifted, *matrix.CONDITIONS[2:]))
    with pytest.raises(matrix.MatrixDefinitionError, match="T-E3"):
        matrix.verify_ruleset_registry()


def test_fingerprint_drift_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    run_e3.verify_agent_fingerprints(list(matrix.F4.agents))
    drifted = dict(matrix.AGENT_FINGERPRINTS, e3_jam_sniper="0" * 64)
    monkeypatch.setattr(matrix, "AGENT_FINGERPRINTS", drifted)
    with pytest.raises(run_e3.E3ConfigurationError, match="fingerprints"):
        run_e3.verify_agent_fingerprints(list(matrix.F4.agents))


# ---------------------------------------------------------------------------
# Pre-registration: verbatim against the design review
# ---------------------------------------------------------------------------


def _clean(text: str) -> str:
    # Markdown emphasis (** and *) and code spans are formatting, not wording.
    return re.sub(r"\s+", " ", text.replace("*", "").replace("`", "")).strip()


def _section(start: str, end: str) -> str:
    text = REVIEW.read_text(encoding="utf-8")
    return text[text.index(start) : text.index(end, text.index(start))]


def _items(block: str) -> list[str]:
    """Top-level list items (``-`` or ``1.``), each joined with its nested items."""
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
            rows.append([_clean(cell) for cell in line.strip().strip("|").split("|")])
    return rows[1:]


def test_the_design_review_is_the_preserved_one() -> None:
    import hashlib

    assert hashlib.sha256(REVIEW.read_bytes()).hexdigest() == REVIEW_SHA256


def test_hypotheses_are_the_design_review_sec_j_table_verbatim() -> None:
    prereg = load_preregistration()
    rows = _table_rows(_section("| ID ", "**Pre-registered interpretation:**"))
    assert [row[0] for row in rows] == list(REQUIRED_HYPOTHESES)
    for row, item in zip(rows, prereg["hypotheses"], strict=True):
        assert [item["id"], item["statement"], item["supported_if"], item["refuted_if"], item["probe_prior"]] == row


def test_interpretation_table_and_threshold_rationale_are_verbatim() -> None:
    prereg = load_preregistration()
    rows = _table_rows(_section("| Result ", "**A clean negative is reachable.**"))
    assert [[r["result"], r["conclusion"]] for r in prereg["interpretation"]] == rows
    assert prereg["clean_negative"] == "A clean negative is reachable."
    rationale = _items(_section("**Threshold rationale:**", "## K."))
    tail = "Per your standing rule that discovery and test stay separate, none of these thresholds was derived from probe or corpus outcomes."
    assert prereg["threshold_rationale"] == [*rationale, tail]


def test_populations_metrics_evidence_rules_and_hard_stops_are_verbatim() -> None:
    prereg = load_preregistration()
    populations = _items(_section("Populations are defined in C-E2", "| ID "))
    assert [prereg["populations"]["exposed"], prereg["populations"]["stalemate"]] == populations
    metrics = _items(_section("**Primary**", "**Secondary.**"))
    assert [prereg["metrics"][k] for k in ("PM-1", "PM-2", "PM-3", "PM-4", "MC-1", "MC-2")] == metrics
    assert prereg["metrics"]["secondary"] == _clean(_section("**Secondary.**", "**Telemetry.**"))
    assert _items(_section("## M.", "## N.")) == prereg["evidence_rules"]
    assert _items(_section("**Hard stops", "## O.")) == prereg["hard_stops"]


def test_criteria_carry_the_registered_numbers() -> None:
    criteria = {h["id"]: h["criterion"] for h in load_preregistration()["hypotheses"]}
    assert criteria["D0"]["unchanged_share_min"] == 0.9
    assert (criteria["D1"]["median_pd_max"], criteria["D1"]["refuted_median_pd_min"]) == (0.5, 0.9)
    assert criteria["D2"]["sdi_seat_determined"] == 0.9 and criteria["D2"]["fall_share_min"] == 0.5
    assert len(criteria["D2"]["units"]) == 6
    assert criteria["D3"]["non_loss_share_min"] == 0.5
    assert (criteria["D4"]["median_fms_min"], criteria["D4"]["refuted_median_fms_max"]) == (0.9, 0.5)
    assert criteria["D5"]["rise_min"] == 0.1 and len(criteria["D5"]["stacked"]) == 8
    assert criteria["D6"]["guards"] == ["e2_repair_guard", "e2_disrupt_guard", "e2_min_guard"]
    assert criteria["D7"]["rise_min"] == 0.1
    assert (criteria["D8"]["median_pd_min"], criteria["D8"]["median_fms_max"], criteria["D8"]["refuted_median_pd_max"]) \
        == (0.9, 0.1, 0.5)
    assert criteria["D9"]["t_e3_completions_max"] == 0 and criteria["D9"]["t_e3k1_completions_min"] == 1
    stats = load_preregistration()["statistics"]
    assert stats["min_distinct_for_rate_claim"] == 8 and stats["fms_min_swings"] == 10
    assert stats["residual"] == {"bootstrap_resamples": 1000, "bootstrap_seed": 42, "interval": 0.95,
                                 "abs_residual_min": 0.125, "control_must_not_count": True,
                                 "dominance_is_not_residual_evidence": True}


def test_changing_a_preregistered_criterion_fails_closed(tmp_path: Path) -> None:
    copy = tmp_path / "preregistration.json"
    shutil.copy(PREREGISTRATION_PATH, copy)
    data = json.loads(copy.read_text(encoding="utf-8"))
    data["hypotheses"][1]["criterion"]["median_pd_max"] = 0.6
    copy.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    with pytest.raises(PreregistrationError, match="digest"):
        load_preregistration(copy)


# ---------------------------------------------------------------------------
# Runner guards (nothing executes)
# ---------------------------------------------------------------------------


def _requests(tmp_path: Path, condition_id: str, field_id: str, **changes: object) -> tuple:
    config = run_e3.experiment_config(condition_id, field_id, output_dir=tmp_path / "out")
    config = dataclasses.replace(config, **changes)  # type: ignore[arg-type]
    return plan_evaluation_requests(config, matrix.ARENA_SIZE, tmp_path / "plan", tmp_path / "env"), config


@pytest.mark.parametrize("condition_id", [c.condition_id for c in matrix.CONDITIONS])
@pytest.mark.parametrize("field_id", matrix.FIELD_IDS)
def test_planned_requests_match_the_frozen_definition(tmp_path: Path, condition_id: str, field_id: str) -> None:
    requests, config = _requests(tmp_path, condition_id, field_id)
    run_e3.check_requests(requests, condition_id, field_id, seeds=config.seeds)
    assert {r.ticks for r in requests} == {matrix.field(field_id).max_ticks}
    assert {r.ruleset_id for r in requests} == {matrix.condition(condition_id).ruleset_id}


@pytest.mark.parametrize(
    ("override", "value"),
    [("scheduler_chunk_size", 1), ("scheduler_rotate_start", False), ("kill_weight", 1.0), ("instr_per_tick", 4)],
)
def test_any_request_override_fails_closed(tmp_path: Path, override: str, value: object) -> None:
    requests, config = _requests(tmp_path, "T-E3", "F1")
    tampered = [dataclasses.replace(r, **{override: value}) for r in requests]
    with pytest.raises(run_e3.E3ConfigurationError, match="forbidden override"):
        run_e3.check_requests(tampered, "T-E3", "F1", seeds=config.seeds)


@pytest.mark.parametrize("change", [{"ticks": 1000}, {"seeds": tuple(range(1, 32))}, {"arena_sizes": (1024,)},
                                    {"both_orientations": False}])
def test_frozen_setting_drift_fails_closed(tmp_path: Path, change: dict[str, object]) -> None:
    config = run_e3.experiment_config("C-E2", "F2-P", output_dir=tmp_path / "out")
    config = dataclasses.replace(config, **change)  # type: ignore[arg-type]
    arena = config.arena_sizes[0]
    requests = plan_evaluation_requests(config, arena, tmp_path / "plan", tmp_path / "env")
    with pytest.raises(run_e3.E3ConfigurationError):
        run_e3.check_requests(requests, "C-E2", "F2-P", seeds=matrix.SEEDS)


def test_execute_never_runs_without_explicit_confirmation(tmp_path: Path) -> None:
    with pytest.raises(run_e3.E3ConfigurationError, match="confirm"):
        run_e3.execute("C-E2", "F1", run_root=tmp_path)
    assert not tmp_path.joinpath(matrix.matrix_id()).exists()


@pytest.mark.parametrize("condition_id", ["T-E3", "T-E3K1"])
def test_treatment_needs_separate_authorization_and_the_unlock_chain(tmp_path: Path, condition_id: str) -> None:
    with pytest.raises(run_e3.E3ConfigurationError, match="separate authorization"):
        run_e3.execute(condition_id, "F1", run_root=tmp_path, confirm=True)
    # Even with both confirmations, no committed freeze and control qualification -> no run.
    with pytest.raises(Exception, match="freeze|qualification|record"):
        run_e3.execute(condition_id, "F1", run_root=tmp_path, confirm=True, confirm_treatment=True,
                       freeze_path=tmp_path / "missing.json")
    assert not tmp_path.joinpath(matrix.matrix_id()).exists()
    with pytest.raises(run_e3.E3ConfigurationError, match="sample"):
        run_e3.experiment_config(condition_id, "F1", sample=True)


def test_treatment_artifacts_stop_every_control_phase_command(tmp_path: Path) -> None:
    run_e3.assert_no_treatment_artifacts(tmp_path)
    (tmp_path / matrix.matrix_id() / "T-E3K1").mkdir(parents=True)
    with pytest.raises(run_e3.TreatmentExposureError, match="STOP"):
        run_e3.assert_no_treatment_artifacts(tmp_path)
    for command in (run_e3.reproduce, run_e3.qualify, run_e3.freeze_populations, run_e3.run_d9):
        with pytest.raises(run_e3.TreatmentExposureError):
            command(run_root=tmp_path)  # type: ignore[operator]
    with pytest.raises(run_e3.TreatmentExposureError):
        run_e3.write_corpus_telemetry("C-E2", run_root=tmp_path)


def test_dry_run_counts_one_field_with_the_real_planner_and_runs_nothing() -> None:
    row = run_e3.dry_run_plan("T-E3", "F2-P")
    assert (row["planned_cells"], row["expected_cells"], row["ticks"], row["consistent"]) == (640, 640, [1001], True)
    assert row["rulesets"] == ["bytefray-rules-6-research-capture-hold-k2-disruption-slot1"]
    assert row["planned_seed_set"] == list(range(1, 33))
