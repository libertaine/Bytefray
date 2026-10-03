"""V6 E5 gates: E5-D (treatment side), the parent comparison's E5 extension, the
populations' hard stops, and the non-matrix gate helpers.

Every gate is shown to *fail* on the input it guards against, not merely to
pass on good input.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest
from battle_engine.ruleset_policy import RulesetPolicy

from tools.research.v6.e5 import gates, nonmatrix_gates, populations


def _row(**gate: Any) -> dict[str, Any]:
    d_gate = {"spawn_mode": "before_core", "default_dual_writes": 0, "dual_writes": 0, "own_core_occupancy": 0}
    d_gate.update(gate)
    return {"telemetry": {"e5": {"d_gate": d_gate, "checks": {"ok": True},
                                 "directed": {"A->B": {"default_anchor_core0_writes": 0},
                                              "B->A": {"default_anchor_core0_writes": 0}}}}}


def test_decoupling_cell_checks_pass_a_clean_treatment() -> None:
    assert gates.decoupling_cell_checks({"k1": _row(), "k2": _row()})["status"] == "PASS"


@pytest.mark.parametrize(("change", "clause"), [
    ({"spawn_mode": "core_base"}, "D-1"), ({"spawn_mode": "other"}, "D-1"),
    ({"default_dual_writes": 1}, "D-2"), ({"dual_writes": 1}, "D-3"), ({"own_core_occupancy": 2}, "D-4"),
])
def test_each_decoupling_clause_fails_on_its_violation(change: dict[str, Any], clause: str) -> None:
    report = gates.decoupling_cell_checks({"k1": _row(), "k2": _row(**change)})
    assert report["status"] == "FAIL" and report["violations"] == {clause: 1}


def test_an_analyzer_failure_fails_decoupling_and_an_empty_field_is_not_a_pass() -> None:
    assert gates.decoupling_cell_checks({"k1": {"error": "boom"}})["status"] == "FAIL"
    assert gates.decoupling_cell_checks({})["status"] == "FAIL"


def test_the_contest_check_catches_anchor_induced_contact_in_an_anchor_only_unit() -> None:
    units = {"F1|x|y|B": {"field": "F1", "victim": "B", "cells": ["k1"]},
             "F2|m|m_twin|AB": {"field": "F2", "victim": "AB", "cells": ["k2"]},
             "F1|s|g|B": {"field": "F1", "victim": "B", "cells": ["k1"]}}
    classes = {"F1|x|y|B": "ANCHOR-ONLY", "F2|m|m_twin|AB": "ANCHOR-ONLY", "F1|s|g|B": "SWEEP-BACKED"}
    rows = {"F1": {"k1": _row()}, "F2": {"k2": _row()}}
    ok = gates.decoupling_contest_check(rows, units, list(units), classes)
    assert (ok["status"], ok["anchor_only_directed_cells"]) == ("PASS", 3)
    bad = copy.deepcopy(rows)
    bad["F2"]["k2"]["telemetry"]["e5"]["directed"]["B->A"]["default_anchor_core0_writes"] = 1
    assert gates.decoupling_contest_check(bad, units, list(units), classes)["failure_count"] == 1
    # A SWEEP-BACKED unit is never checked by D-5.
    assert gates.decoupling_contest_check(rows, units, ["F1|s|g|B"], classes)["status"] == "FAIL"


def test_require_decoupling_and_d9_stop() -> None:
    gates.require_decoupling({"status": "PASS"})
    with pytest.raises(gates.DecouplingGateError):
        gates.require_decoupling({"status": "FAIL"})
    gates.require_d9("T-E5", [])
    gates.require_d9("T-E5K1", [{"victim_name": "e2_repair_guard"}])  # the companion is never a stop
    with pytest.raises(gates.D9StopError):
        gates.require_d9("T-E5", [{"victim_name": "e2_repair_guard"}])


def test_the_parent_comparison_also_compares_e5_metrics(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(gates.e4_gates, "compare_parent_subset", lambda *a, **k: {
        "cells_compared": 1, "mismatch_count": 0, "mismatch_reasons": {}, "mismatch_samples": [],
        "compared": ["base"], "status": "PASS"})
    same = {"k": {"telemetry": {"e5": {"bp": 1}}}}
    assert gates.compare_parent_subset(tmp_path, tmp_path, new_rows=same, historical_rows=same)["status"] == "PASS"
    other = {"k": {"telemetry": {"e5": {"bp": 2}}}}
    result = gates.compare_parent_subset(tmp_path, tmp_path, new_rows=same, historical_rows=other)
    assert result["status"] == "FAIL" and result["mismatch_reasons"] == {"e5_metrics": 1}


# ---------------------------------------------------------------------------
# Populations' hard stops
# ---------------------------------------------------------------------------


def _record(sb: int, **overrides: Any) -> dict[str, Any]:
    arm = {"control_census": {"status": "PASS"},
           "control_d_clauses": {name: {"status": "PASS", "count": 0}
                                 for name in ("d5_control_failures", "d6_failures", "incorrect_control_inferences")}}
    record = {"arms": {"primary": copy.deepcopy(arm), "companion": copy.deepcopy(arm)},
              "min_sweep_backed": {"required": 6, "primary_arm": sb, "status": "PASS" if sb >= 6 else "HALT"},
              "control_vs_control_hypotheses": {"statuses": {"E5-H1": "REFUTED", "E5-H2": "SUPPORTED"},
                                                "interpretation": "STOP"}}
    record.update(overrides)
    return record


def test_populations_ready_with_six_sweep_backed_units() -> None:
    populations.require_ready(_record(6))


def test_fewer_than_six_sweep_backed_units_halts_before_treatment() -> None:
    with pytest.raises(populations.PopulationsError, match="HALT: 5 SWEEP-BACKED"):
        populations.require_ready(_record(5))


@pytest.mark.parametrize("clause", ["d5_control_failures", "d6_failures", "incorrect_control_inferences"])
def test_a_control_side_clause_failure_stops(clause: str) -> None:
    record = _record(8)
    record["arms"]["companion"]["control_d_clauses"][clause] = {"status": "FAIL", "count": 1}
    with pytest.raises(populations.PopulationsError, match=clause):
        populations.require_ready(record)


def test_a_non_identity_control_census_stops() -> None:
    record = _record(8)
    record["arms"]["primary"]["control_census"]["status"] = "FAIL"
    with pytest.raises(populations.PopulationsError, match="census"):
        populations.require_ready(record)


@pytest.mark.parametrize("cvc", [
    {},
    {"statuses": {"E5-H1": "REFUTED", "E5-H2": "SUPPORTED"}, "interpretation": "R-H2"},
    {"statuses": {"E5-H1": "NEITHER", "E5-H2": "SUPPORTED"}, "interpretation": "STOP"},
])
def test_the_control_against_itself_must_read_as_the_null_caught_by_e5_d(cvc: dict[str, Any]) -> None:
    # Review AF-11: a no-effect treatment reads H2 SUPPORTED; only E5-D (which
    # control data always fails) keeps it from reading R-H2.
    with pytest.raises(populations.PopulationsError, match="global-null"):
        populations.require_ready(_record(8, control_vs_control_hypotheses=cvc))


def test_frozen_populations_must_recompute() -> None:
    record = {"p_par_e5": {"units": ["u"]}, "arms": {"a": 1}, "min_sweep_backed": {"primary_arm": 6},
              "control_vs_control_hypotheses": {"interpretation": "STOP"}}
    populations.require_recomputes(record, json.loads(json.dumps(record)))
    with pytest.raises(populations.PopulationsError, match="arms"):
        populations.require_recomputes(record, {**record, "arms": {"a": 2}})


# ---------------------------------------------------------------------------
# Non-matrix gate helpers
# ---------------------------------------------------------------------------

SOURCE = (
    "class Agent:\n"
    "    def act(self, obs: ObservationV2) -> AgentAction:\n"
    "        anchors = obs.visible_enemy_anchor_addresses\n"
    "        if self.enemy_core is None and len(anchors) == 1:\n"
    "            self.enemy_core = anchors[0]\n"
)


def test_the_offset_aware_copy_changes_only_the_core_adoption() -> None:
    aware = nonmatrix_gates.offset_aware_source(SOURCE)
    assert "self.enemy_core = (anchors[0] - self._own_off) % self.arena" in aware
    assert "self._own_off = (obs.self_anchor - obs.own_core_base) % self.arena" in aware
    assert aware.replace(nonmatrix_gates._OFFSET, "").replace(
        nonmatrix_gates._ADOPT_AWARE, nonmatrix_gates._ADOPT) == SOURCE
    with pytest.raises(nonmatrix_gates.NonMatrixGateError):
        nonmatrix_gates.offset_aware_source(SOURCE + SOURCE)


def test_every_inferring_fixture_source_accepts_the_transformation() -> None:
    root = Path(__file__).resolve().parents[2] / "tools" / "research" / "v6" / "e2" / "fixtures" / "agents"
    for name in ("e2_sniper", "e2_min_guard", "e2_spread_sniper", "e2_spread_defender"):
        nonmatrix_gates.offset_aware_source((root / name / "agent.py").read_text(encoding="utf-8"))


def test_the_inertness_pairings_cover_every_inferring_pairing() -> None:
    pairings = nonmatrix_gates.inertness_pairings()
    assert len(pairings) == 18 * 2 + 4
    assert all(nonmatrix_gates.inferring(a) or nonmatrix_gates.inferring(b) for a, b in pairings)


def test_non_matrix_gates_refuse_matrix_seeds() -> None:
    for runner in (nonmatrix_gates.run_inertness, nonmatrix_gates.run_observation, nonmatrix_gates.run_d9):
        with pytest.raises(nonmatrix_gates.NonMatrixGateError, match="matrix seeds"):
            runner(seeds=(3,))


def test_the_spawn_patch_is_scoped_and_restores_the_resolver() -> None:
    before = RulesetPolicy(ruleset_id="t", initial_anchor_placement="before_core")
    base = RulesetPolicy(ruleset_id="t")
    with nonmatrix_gates.spawn_offset_patch(2):
        assert before.resolve_initial_anchor(100, 512) == 98
        assert base.resolve_initial_anchor(100, 512) == 100
    assert before.resolve_initial_anchor(100, 512) == 99


def test_the_observation_delta_accepts_only_the_minus_one_shift() -> None:
    parent = {"self_anchor": 100, "visible_enemy_anchor_addresses": (0, 300), "own_core_base": 100, "tick": 1}
    shifted = {**parent, "self_anchor": 99, "visible_enemy_anchor_addresses": (299, 511)}
    assert nonmatrix_gates.observation_delta_ok(parent, shifted)
    assert not nonmatrix_gates.observation_delta_ok(parent, parent)
    assert not nonmatrix_gates.observation_delta_ok(parent, {**shifted, "own_core_base": 99})
    assert not nonmatrix_gates.observation_delta_ok(parent, shifted, shift=2)


def test_a_gate_record_must_pass_under_the_same_freeze(tmp_path: Path) -> None:
    path = tmp_path / "gate.json"
    nonmatrix_gates.write_record(path, {"status": "PASS"}, freeze_id="f1", provenance={})
    nonmatrix_gates.require_gate(path, freeze_id="f1")
    with pytest.raises(nonmatrix_gates.NonMatrixGateError):
        nonmatrix_gates.require_gate(path, freeze_id="f2")
    nonmatrix_gates.write_record(path, {"status": "FAIL"}, freeze_id="f1", provenance={})
    with pytest.raises(nonmatrix_gates.NonMatrixGateError):
        nonmatrix_gates.require_gate(path, freeze_id="f1")
