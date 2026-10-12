"""V6 E5 tests added after the first mutation-testing round.

Each test closes a mutation that the first round showed was caught only
because the analysis freeze's own drift check refused the edited file, never
by a behavioural test. They exercise the frozen tooling without changing it;
the freeze pins no test file.

* BP is DEFINED from exactly 10 both-alive ticks of each parity, and DUAL
  counts a hit on a process that moved onto its own core (not only hits on
  unmoved default anchors).
* The one-field Ruleset difference catches a drift outside the registered
  (K, lambda, pass order, spawn) parameters.
* O-MIN-SB is computed, not only obeyed: ``build_record`` marks fewer than 6
  SWEEP-BACKED units HALT, and evaluates control against control with E5-D FAIL.
* The control-side E5-D clauses (D-5, D-6, the inference sanity check) are
  checked cell by cell.
* E5-H1/H2 keep DECIDED-EARLY units in the denominator, and MIXED-INFERENCE
  units never enter the SWEEP-BACKED census.
* ``interpret`` fails closed on an overlapping table by itself, without relying
  on the loader.
* ``execute`` refuses before touching the freeze; the unlock compares every
  control record's SHA-256; the D9 gate needs its whole-tick sensitivity capture.
"""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from battle_engine.agents import resolve_agent
from battle_engine.config import Config
from battle_engine.match_service import MatchEntrant, MatchRequest, NativeMatchService
from battle_engine.placement import resolve_direct_match_starts

from tools.research.v6.e3.entrants import prepare_data_root
from tools.research.v6.e5 import analyze_e5 as a
from tools.research.v6.e5 import matrix, populations, run_e5
from tools.research.v6.e5 import nonmatrix_gates as g
from tools.research.v6.e5 import preregistration as p
from tools.research.v6.e5.cell_metrics import DECIDED_EARLY, DEFINED
from tools.research.v6.e5.telemetry import analyze_cell

PREREG = p.load_preregistration()
CRITERIA = {item["id"]: item["criterion"] for item in PREREG["hypotheses"]}

# ---------------------------------------------------------------------------
# Cell metrics: the DECIDED_EARLY boundary and a non-default DUAL write
# ---------------------------------------------------------------------------

SEED = 7  # outside the matrix seeds 1..32
PARENT = matrix.condition(matrix.PRIMARY_CONTROL).ruleset_id
TREATMENT = matrix.condition(matrix.PRIMARY_TREATMENT).ruleset_id


def _run(root: Path, ruleset_id: str, names: tuple[str, str], ticks: int,
         starts: tuple[int, ...] | None = None) -> dict[str, Any]:
    if starts is None:
        starts = tuple(resolve_direct_match_starts(ruleset_id=ruleset_id, arena_size=512, entrant_count=2,
                                                   supplied_starts=[None, None], seed=SEED))
    out = root / "cell"
    out.mkdir(parents=True, exist_ok=True)
    NativeMatchService().run(MatchRequest(
        config=Config(seed=SEED, arena_size=512, instr_per_tick=8),
        entrants=tuple(MatchEntrant.python(seat, name, start, resolve_agent(root, name))
                       for seat, name, start in zip("AB", names, starts, strict=True)),
        max_ticks=ticks, replay_path=out / "replay.jsonl", verbose=False, ruleset_id=ruleset_id))
    return analyze_cell(out)["e5"]


@pytest.mark.parametrize(("ticks", "both_alive", "status"), [
    (20, {"A": 10, "B": 10}, DEFINED), (19, {"A": 10, "B": 9}, DECIDED_EARLY)])
def test_bp_is_defined_from_exactly_ten_both_alive_ticks_per_parity(
    tmp_path: Path, ticks: int, both_alive: dict[str, int], status: str
) -> None:
    prepare_data_root(tmp_path, ["e2_sniper", "e2_min_guard"])
    e5 = _run(tmp_path, PARENT, ("e2_sniper", "e2_min_guard"), ticks)
    assert e5["both_alive_ticks_by_first_mover"] == both_alive
    assert all(e5["bp"][seat]["status"] == status for seat in "AB")


_MOVER = '''from battle_engine.agent_api import ActionKindV2, AgentAction, ProcessDeclaration


class Agent:
    def reset(self, context):
        self.arena = context.arena_size
        self.moved = False

    def declare_processes(self):
        return [ProcessDeclaration(id="p", reach=self.arena // 2, share=1.0)]

    def act(self, obs):
        if not self.moved:
            self.moved = True
            return AgentAction(ActionKindV2.MOVE, operand=1)
        return AgentAction(ActionKindV2.READ, operand=obs.own_core_base)


def create_agent():
    return Agent()
'''
_HITTER = '''from battle_engine.agent_api import ActionKindV2, AgentAction, ProcessDeclaration


class Agent:
    def reset(self, context):
        self.arena = context.arena_size

    def declare_processes(self):
        return [ProcessDeclaration(id="p", reach=self.arena // 2, share=1.0)]

    def act(self, obs):
        anchors = obs.visible_enemy_anchor_addresses
        if anchors:
            return AgentAction(ActionKindV2.WRITE, operand=anchors[0], value=1)
        return AgentAction(ActionKindV2.READ, operand=obs.own_core_base)


def create_agent():
    return Agent()
'''


def _agent(root: Path, name: str, source: str) -> None:
    folder = root / "agents" / name
    folder.mkdir(parents=True)
    (folder / "agent.py").write_text(source, encoding="utf-8")
    (folder / "agent.yaml").write_text(
        f"name: {name}\ndisplay: {name}\ndescription: test-only\nkind: python\napi_version: 2\n"
        "entrypoint: agent.py:create_agent\nversion: \"1.0.0\"\n", encoding="utf-8")


def test_dual_counts_a_hit_on_a_process_that_moved_onto_its_own_core(tmp_path: Path) -> None:
    # Revision 1 Sec R3: movement is unrestricted. Under before_core, A's process
    # spawns at pc - 1 and MOVEs +1 onto its own core cell 0; B writes every
    # visible enemy anchor, so each write both disrupts A's process and flips A's
    # core cell -- a DUAL write that is not a default-anchor write. Only the
    # manipulation quantities are read (blindness).
    _agent(tmp_path, "t_mover", _MOVER)
    _agent(tmp_path, "t_hitter", _HITTER)
    e5 = _run(tmp_path, TREATMENT, ("t_mover", "t_hitter"), 20, starts=(100, 300))
    gate = e5["d_gate"]
    assert gate["spawn_mode"] == "before_core" and gate["default_dual_writes"] == 0
    assert gate["dual_writes"] > 0 and gate["own_core_occupancy"] > 0


# ---------------------------------------------------------------------------
# The one-field Ruleset difference, beyond the registered parameters
# ---------------------------------------------------------------------------


def test_a_drift_outside_the_registered_parameters_breaks_the_one_field_difference(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = matrix.resolve_ruleset_policy

    def drifted(ruleset_id: str) -> Any:
        policy = original(ruleset_id)
        if ruleset_id == matrix.condition("T-E5").ruleset_id:
            return dataclasses.replace(policy, scheduler_chunk_size=4)  # not in (K, lambda, order, spawn)
        return policy

    monkeypatch.setattr(matrix, "resolve_ruleset_policy", drifted)
    with pytest.raises(matrix.MatrixDefinitionError, match="differs from C-E5"):
        matrix.verify_ruleset_registry()


# ---------------------------------------------------------------------------
# O-MIN-SB and the control-vs-control evaluation, as build_record computes them
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(("sb", "status"), [(5, "HALT"), (6, "PASS"), (7, "PASS")])
def test_build_record_computes_the_minimum_sweep_backed_halt(
    monkeypatch: pytest.MonkeyPatch, sb: int, status: str
) -> None:
    seen: list[str] = []

    def fake_evaluate(arms: Any, record: Any, prereg: Any, table: Any, *, d_status: str) -> dict[str, Any]:
        seen.append(d_status)
        return {**{h: {"status": "REFUTED"} for h in ("E5-H1", "E5-H3", "E5-H4", "E5-H5")},
                "E5-H2": {"status": "SUPPORTED"}, "interpretation": {"outcome": "STOP"}, "pathology": {},
                "D9": {"t_e5_completions": 0}}

    monkeypatch.setattr(populations, "arm_record", lambda runs: {"counts": {a.SWEEP_BACKED: sb}})
    monkeypatch.setattr(populations, "p_par_e5", lambda: {"units": [], "count": 0})
    monkeypatch.setattr(populations, "evaluate_hypotheses", fake_evaluate)
    record = populations.build_record(freeze_id="f", preregistration_sha256="s",
                                      arms={"primary": {}, "companion": {}})
    assert record["min_sweep_backed"] == {"required": 6, "primary_arm": sb, "status": status}
    # Control against itself is evaluated with E5-D FAIL: the spawn is on the core.
    assert seen == ["FAIL"]


# ---------------------------------------------------------------------------
# Control-side E5-D clauses (D-5 control, D-6, the inference sanity check)
# ---------------------------------------------------------------------------


class _Field:
    def __init__(self, rows: dict[str, dict[str, Any]]) -> None:
        self.field_id = "F1"
        self.rows = rows
        self.cells: dict[str, dict[str, Any]] = {key: {} for key in rows}

    def row(self, key: str) -> dict[str, Any]:
        return self.rows[key]


def _telemetry(*, contact: int = 1, hits: int = 0, dual: int = 0, status: str = DEFINED,
               audit: dict[str, Any] | None = None) -> dict[str, Any]:
    directed = {pair: {"default_anchor_core0_writes": contact, "unmoved_anchor_hits": hits}
                for pair in ("A->B", "B->A")}
    return {"e5": {"bp": {s: {"status": status} for s in "AB"}, "directed": directed,
                   "d_gate": {"dual_writes": dual}},
            "e3": {"seats": {s: {"capture": {"core_inference": audit}} for s in "AB"}}}


UNIT = "F1|x|y|A"
UNIT_ROWS = {UNIT: {"field": "F1", "victim": "A", "cells": ["1"]}}


@pytest.mark.parametrize(("cls", "telemetry", "failures"), [
    (a.ANCHOR_ONLY, _telemetry(contact=0), [f"{UNIT}:1:B->A"]),
    (a.ANCHOR_ONLY, _telemetry(contact=1), []),
    (a.ANCHOR_ONLY, _telemetry(contact=0, status="DECIDED_EARLY"), []),  # only DEFINED cells are required
    (a.SWEEP_BACKED, _telemetry(contact=0), []),  # D-5 concerns ANCHOR-ONLY units only
])
def test_control_d5_needs_anchor_induced_contact_in_every_defined_anchor_only_cell(
    cls: str, telemetry: dict[str, Any], failures: list[str]
) -> None:
    out = populations.control_d_clauses(_Field({"1": telemetry}), UNIT_ROWS, [UNIT], {UNIT: cls})  # type: ignore[arg-type]
    assert out["d5_control_failures"] == failures


@pytest.mark.parametrize(("hits", "dual", "failing"), [(1, 0, ["1"]), (1, 1, []), (0, 0, [])])
def test_d6_needs_a_dual_write_wherever_an_unmoved_anchor_is_hit(hits: int, dual: int, failing: list[str]) -> None:
    out = populations.control_d_clauses(_Field({"1": _telemetry(hits=hits, dual=dual)}), {}, [], {})  # type: ignore[arg-type]
    assert out["d6_failures"] == failing


@pytest.mark.parametrize(("audit", "flagged"), [
    ({"status": "inferred", "correct": False}, ["1:A", "1:B"]),
    ({"status": "inferred", "correct": True}, []),
    ({"status": "not_inferred", "correct": None}, []),
    (None, []),
])
def test_an_incorrect_control_inference_is_flagged(audit: dict[str, Any] | None, flagged: list[str]) -> None:
    out = populations.control_d_clauses(_Field({"1": _telemetry(audit=audit)}), {}, [], {})  # type: ignore[arg-type]
    assert out["incorrect_control_inferences"] == flagged


# ---------------------------------------------------------------------------
# The census: the DECIDED-EARLY denominator and the SWEEP-BACKED population
# ---------------------------------------------------------------------------


def _rows(**classes: int) -> list[dict[str, Any]]:
    return [{"transition": name.replace("_", "-")} for name, count in classes.items() for _ in range(count)]


def test_decided_early_units_stay_in_the_hypothesis_denominator() -> None:
    # 3 STAYS of 5 (2 DECIDED-EARLY) is 3/5: NEITHER. Dropping DECIDED-EARLY
    # would read 3/3 and SUPPORT E5-H2.
    out = a.census_hypotheses(_rows(STAYS=3, DECIDED_EARLY=2), CRITERIA)
    assert (out["E5-H2"]["share_exact"], out["E5-H2"]["status"]) == ("3/5", "NEITHER")


def _unit(name: str, transition: str, cls: str) -> dict[str, Any]:
    return {"unit": name, "transition": transition, "contest_class": cls, "e4_contest_class": "OPENING-ONLY",
            "control": {"near_boundary": False}, "treatment": {"near_boundary": False}, "n_distinct": 1}


def test_mixed_inference_units_never_enter_the_sweep_backed_census(monkeypatch: pytest.MonkeyPatch) -> None:
    units = {"sb1": _unit("sb1", a.STAYS, a.SWEEP_BACKED), "sb2": _unit("sb2", a.STAYS, a.SWEEP_BACKED),
             "sb3": _unit("sb3", a.STAYS, a.SWEEP_BACKED), "mx": _unit("mx", a.NEUTRALIZED, a.MIXED_INFERENCE),
             "ao": _unit("ao", a.NEUTRALIZED, a.ANCHOR_ONLY)}
    monkeypatch.setattr(a, "unit_rows", lambda control, treatment: units)
    monkeypatch.setattr(a.analyze_e4, "unit_rows", lambda *args, **kwargs: {})
    monkeypatch.setattr(a, "outcome_change", lambda c, t, keys: {"count": 0, "of": 0})
    monkeypatch.setattr(a, "pathology_flags", lambda c, t, crit: {})
    monkeypatch.setattr(a, "d9_completions", lambda run: [])
    field = SimpleNamespace(cells={})
    runs = {f: field for f in ("F1", "F2")}
    arm = {"control": runs, "treatment": runs}
    frozen_arm = {"p_base": sorted(units), "contest_classes": {n: u["contest_class"] for n, u in units.items()}}
    frozen = {"arms": {"primary": frozen_arm, "companion": frozen_arm}, "p_par_e5": {"units": []}}
    out = a.evaluate_hypotheses({"primary": arm, "companion": arm}, frozen, PREREG, {},  # type: ignore[dict-item]
                                d_status="PASS")
    assert (out["E5-H1"]["of"], out["E5-H2"]["count"]) == (3, 3)
    assert out["mixed_inference_units"] == ["mx"]
    assert out["interpretation"]["outcome"] == "R-H2"  # a counted MIXED unit would make it R-H2-PRIME


# ---------------------------------------------------------------------------
# interpret fails closed on an overlapping table by itself
# ---------------------------------------------------------------------------


def test_interpret_never_resolves_an_overlap_by_row_order() -> None:
    prereg = json.loads(json.dumps(PREREG))
    prereg["interpretation"]["rows"][1]["combinations"].append(["NEITHER", "SUPPORTED"])
    with pytest.raises(a.InterpretationInvariantError, match="matches 2 registered rows"):
        a.interpret("PASS", "NEITHER", "SUPPORTED", prereg)


# ---------------------------------------------------------------------------
# The runner's refusals and the unlock's record check
# ---------------------------------------------------------------------------


class _Reached(Exception):
    """Raised by a stub standing in for the first step after the refusals."""


def test_execute_refuses_before_reading_the_freeze(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    def reached() -> None:
        raise _Reached

    monkeypatch.setattr(run_e5, "verify_frozen_definition", reached)
    with pytest.raises(run_e5.E5ConfigurationError, match="Refusing to execute"):
        run_e5.execute("C-E5", "F1", run_root=tmp_path)
    for treatment in ("T-E5", "T-E5K1"):
        with pytest.raises(run_e5.E5ConfigurationError, match="separate authorization"):
            run_e5.execute(treatment, "F1", run_root=tmp_path, confirm=True)
    with pytest.raises(_Reached):  # a confirmed control gets past the refusals
        run_e5.execute("C-E5", "F1", run_root=tmp_path, confirm=True)


def test_the_unlock_compares_every_control_record_sha(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    records = run_e5.freeze_root(tmp_path, "f")
    records.mkdir(parents=True)
    pins = {}
    for name in run_e5.CONTROL_RECORDS:
        (records / name).write_text(json.dumps({"name": name}), encoding="utf-8")
        pins[name] = {"sha256": run_e5.record_sha256(records / name)}
    freeze = {"freeze_id": "f", "control_qualification": {"status": "PASS", "records": pins}}
    monkeypatch.setattr(run_e5, "load_freeze", lambda path: freeze)

    def reached(*args: Any, **kwargs: Any) -> None:
        raise _Reached

    monkeypatch.setattr(run_e5, "require_parent_reproduction", reached)
    with pytest.raises(_Reached):  # unchanged records pass the SHA check
        run_e5.treatment_unlock(tmp_path)
    (records / run_e5.CONTROL_RECORDS[-1]).write_text(json.dumps({"name": "edited"}), encoding="utf-8")
    with pytest.raises(run_e5.AnalysisFreezeError, match="missing or differs"):
        run_e5.treatment_unlock(tmp_path)


# ---------------------------------------------------------------------------
# D9: the whole-tick sensitivity capture is required
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(("sensitivity_completions", "status"), [(1, "PASS"), (0, "FAIL")])
def test_the_d9_gate_needs_its_whole_tick_sensitivity_capture(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, sensitivity_completions: int, status: str
) -> None:
    monkeypatch.setattr(g, "prepare_data_root", lambda dest, names: dest)

    def play(data_root: Path, run_dir: Path, *, ruleset_id: str, guard: str, **kwargs: Any) -> dict[str, Any]:
        whole_tick = ruleset_id != g.PRIMARY_ID
        return {"guard": guard, "guard_completions": sensitivity_completions if whole_tick else 0}

    monkeypatch.setattr(g.e3_d9, "play_scenario", play)
    monkeypatch.setattr(g.e3_d9, "scenario_ok", lambda row: True)
    record = g.run_d9(tmp_path, seeds=(101,), adversaries=(next(iter(g.e3_d9.ADVERSARIES)),))
    assert record["status"] == status
