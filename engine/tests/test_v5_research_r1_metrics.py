from __future__ import annotations

"""V5 research Phase R1: analyzer measurement-refinement tests.

Proves the distinction Section 4 of the R1 charter requires: a repeated
damage -> repair -> damage -> repair cycle on one core cell must not be
misreported by the true simultaneous-deficit metrics as steadily
accumulating progress toward capture, even though the legacy Phase 0
activity counters (kept for backward compatibility) do accumulate
monotonically. Also covers the new process-economy metrics (deaths,
extinction, zero-process-while-alive) derived from real mortality-enabled
matches, using the same low-level ProcessEntrantSpec construction style as
engine/tests/test_v4_process_semantics.py and test_process_mortality.py.
"""

from pathlib import Path
from typing import Any

from battle_engine.agent_api import ActionKind, ActionKindV2, AgentAction, ObservationV2
from battle_engine.config import Config, Weights
from battle_engine.process_runtime import (
    ProcessEntrantSpec,
    ProcessInstance,
    ProcessMatchController,
    ProcessRole,
)
from battle_engine.ruleset_policy import RULESET_V5_R1_ALPHA1
from battle_engine.telemetry import JSONLSink

from tools.research.v5.analyzer import analyze_match


def _run_low_level(specs: list[ProcessEntrantSpec], *, tmp_path: Path, max_ticks: int, **controller_kwargs: Any) -> Path:
    config = Config(arena_size=1024, instr_per_tick=8, seed=1, weights=Weights())
    controller = ProcessMatchController(config, specs, max_ticks=max_ticks, **controller_kwargs)
    replay_path = tmp_path / "replay.jsonl"
    sink = JSONLSink(str(replay_path))
    controller.run(sink)
    sink.close()
    return replay_path


def test_damage_repair_cycle_does_not_misreport_as_accumulating_progress(tmp_path: Path) -> None:
    """Attacker damages address 500 (victim B's first core cell) on ticks
    where phase==1, victim repairs it on ticks where phase==0. Legacy
    ``final_core_health`` decrements every damage phase and never recovers
    (looks like sustained near-catastrophic damage); the true
    ``core_deficit_series`` must show the deficit returning to 0 after every
    repair, and ``max_core_deficit`` must stay at 1 -- never more than the
    single contested cell was ever simultaneously undefended."""

    def attacker_logic(obs: ObservationV2, state: dict[str, Any]) -> AgentAction:
        phase = ((obs.current_tick - 1) // 2) % 2
        if phase == 1:
            return AgentAction(ActionKindV2.WRITE, 500, 0x11)
        return AgentAction(ActionKind.NOP)

    def victim_logic(obs: ObservationV2, state: dict[str, Any]) -> AgentAction:
        phase = ((obs.current_tick - 1) // 2) % 2
        if phase == 0:
            return AgentAction(ActionKindV2.WRITE, 500, 0xCE)
        return AgentAction(ActionKind.NOP)

    spec_a = ProcessEntrantSpec("A", "attacker", [
        ProcessInstance("pA", ProcessRole.ATTACKER, initial_position=0, reach=None, quota_share=8, logic=attacker_logic)
    ])
    spec_b = ProcessEntrantSpec("B", "victim", [
        ProcessInstance("pB", ProcessRole.DEFENDER, initial_position=500, reach=None, quota_share=8, logic=victim_logic)
    ], start=500)

    replay_path = _run_low_level([spec_a, spec_b], tmp_path=tmp_path, max_ticks=16)
    m = analyze_match(replay_path)

    # Legacy activity counter: monotonic, looks like the defender lost half
    # its core and never recovered a single cell.
    assert m["final_core_health"]["B"] == 4
    assert m["core_health_series"]["B"] == [8, 8, 8, 7, 7, 7, 7, 6, 6, 6, 6, 5, 5, 5, 5, 4, 4]

    # True state/progress layer: the simultaneous deficit never exceeds 1,
    # and returns to 0 after each of the 3 completed repairs.
    assert m["max_core_deficit"]["B"] == 1
    assert m["core_deficit_series"]["B"] == [0, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1]
    assert m["full_core_return_count"]["B"] == 3
    assert m["repair_latencies_ticks"]["B"] == [2, 2, 2]
    assert m["longest_damaged_interval_ticks"]["B"] == 2
    assert m["deficit_ever_reached_full"]["B"] is False
    assert m["core_capture_outcome"]["B"] == "survived"

    # Untouched entrant A shows no deficit activity at all.
    assert m["max_core_deficit"]["A"] == 0
    assert m["core_capture_outcome"]["A"] == "survived"


def test_true_ownership_expands_merged_run_length_diffs(tmp_path: Path) -> None:
    """A single-tick write run that captures two ADJACENT core cells can be
    coalesced by the VM into one ``MemoryDiff`` whose ``length`` covers both
    addresses (see ``battle_engine.replay.MemoryDiff.length``). The true
    ownership tracker must expand that full [address, address+length) run,
    not just its start address, or a repair/capture folded into the middle
    of a merged diff is silently missed -- exactly the bug a real R1B
    Quorum-vs-Quorum match exposed (docs/research/v5/
    V5_R1_PROCESS_MORTALITY.md Section C)."""

    def attacker_logic(obs: ObservationV2, state: dict[str, Any]) -> AgentAction:
        state["i"] = state.get("i", 0) + 1
        target = 506 if state["i"] % 2 == 1 else 507
        return AgentAction(ActionKindV2.WRITE, target, 0x11)

    spec_a = ProcessEntrantSpec("A", "attacker", [
        ProcessInstance("pA", ProcessRole.ATTACKER, initial_position=0, reach=None, quota_share=8, logic=attacker_logic)
    ])
    spec_b = ProcessEntrantSpec("B", "victim", [
        ProcessInstance("pB", ProcessRole.DEFENDER, initial_position=500, reach=None, quota_share=8,
                         logic=lambda obs, state: AgentAction(ActionKind.NOP))
    ], start=500)

    replay_path = _run_low_level([spec_a, spec_b], tmp_path=tmp_path, max_ticks=1)
    m = analyze_match(replay_path)

    # Confirm the VM actually merged this into a run-length diff, so the
    # test exercises the exact condition it claims to.
    import json
    lines = [json.loads(line) for line in replay_path.read_text(encoding="utf-8").splitlines()]
    tick1_diffs = next(rec["memory_diffs"] for rec in lines if rec.get("tick") == 1)
    assert any(d["len"] >= 2 for d in tick1_diffs), "test setup must produce a merged run-length diff"

    # Both cells 506 and 507 must be reflected as lost, not just the run's
    # start address.
    assert m["core_owned_cells_series"]["B"][-1] == 6
    assert m["core_deficit_series"]["B"][-1] == 2


def test_process_death_metrics_from_a_real_mortality_match(tmp_path: Path) -> None:
    """A full-quota attacker kills B's lone process within tick 1 (H=1);
    B's core is never targeted, so B must survive with zero live processes
    -- the exact pathology R1 Section 6 requires be recorded explicitly."""

    spec_a = ProcessEntrantSpec("A", "attacker", [
        ProcessInstance("pA", ProcessRole.ATTACKER, initial_position=0, reach=None, quota_share=8,
                         logic=lambda obs, state: AgentAction(ActionKindV2.WRITE, 500, 0x11))
    ])
    spec_b = ProcessEntrantSpec("B", "victim", [
        ProcessInstance("pB", ProcessRole.DEFENDER, initial_position=500, reach=None, quota_share=8,
                         logic=lambda obs, state: AgentAction(ActionKind.NOP))
    ], start=500)

    replay_path = _run_low_level(
        [spec_a, spec_b], tmp_path=tmp_path, max_ticks=10,
        ruleset_policy=RULESET_V5_R1_ALPHA1, process_integrity=1,
    )
    m = analyze_match(replay_path)

    assert m["process_deaths"] == {"A": 0, "B": 1}
    assert m["process_death_events"] == [{"tick": 1, "entrant_id": "B", "process_id": "pB"}]
    assert m["process_extinction_tick"]["B"] == 1
    assert m["process_extinction_tick"]["A"] is None
    assert m["mutual_process_extinction"] is False
    assert m["live_process_count_series"]["B"] == [1] + [0] * 10
    # B's core was never touched, so it stays alive with zero processes --
    # the "alive entrant + intact core + zero processes" pathology.
    assert m["entrant_zero_process_ticks"]["B"] == 10
    assert m["entrant_ever_alive_with_zero_processes"]["B"] is True
    assert m["entrant_ever_alive_with_zero_processes"]["A"] is False
    assert m["core_capture_outcome"]["B"] == "survived"
    assert m["ticks_full_extinction_to_own_core_capture"]["B"] is None


def test_symmetric_mutual_attack_produces_asymmetric_kill_by_schedule_order(tmp_path: Path) -> None:
    """Two single-process entrants that simultaneously target each other's
    anchors under H=1: this does NOT produce mutual extinction. The
    chunked round-robin scheduler (docs/research/v5/
    V5_R1_PROCESS_MORTALITY.md Section K) executes A's full chunk before
    B's, so A kills B before B's process ever gets to act -- a genuine,
    order-dependent first-mover advantage under extreme (low-H) mortality
    that R1's failure-mode analysis must report, not an analyzer defect."""

    spec_a = ProcessEntrantSpec("A", "attacker", [
        ProcessInstance("pA", ProcessRole.ATTACKER, initial_position=0, reach=None, quota_share=8,
                         logic=lambda obs, state: AgentAction(ActionKindV2.WRITE, 500, 0x11))
    ])
    spec_b = ProcessEntrantSpec("B", "counter_attacker", [
        ProcessInstance("pB", ProcessRole.ATTACKER, initial_position=500, reach=None, quota_share=8,
                         logic=lambda obs, state: AgentAction(ActionKindV2.WRITE, 0, 0x11))
    ], start=500)

    replay_path = _run_low_level(
        [spec_a, spec_b], tmp_path=tmp_path, max_ticks=5,
        ruleset_policy=RULESET_V5_R1_ALPHA1, process_integrity=1,
    )
    m = analyze_match(replay_path)

    assert m["process_deaths"] == {"A": 0, "B": 1}
    assert m["mutual_process_extinction"] is False
    assert m["entrant_ever_alive_with_zero_processes"] == {"A": False, "B": True}
    assert m["core_capture_outcome"] == {"A": "survived", "B": "survived"}


def test_mutual_process_extinction_detected(tmp_path: Path) -> None:
    """A third bystander entrant kills both A's and B's lone process within
    the same tick by alternating its target address every call (its local
    state counter, not the shared match tick, drives the alternation) --
    decoupling each kill from the other's turn order and producing genuine
    simultaneous mutual extinction for both A and B."""

    def bystander_logic(obs: ObservationV2, state: dict[str, Any]) -> AgentAction:
        state["i"] = state.get("i", 0) + 1
        target = 0 if state["i"] % 2 == 1 else 500
        return AgentAction(ActionKindV2.WRITE, target, 0x11)

    spec_a = ProcessEntrantSpec("A", "quiet_a", [
        ProcessInstance("pA", ProcessRole.DEFENDER, initial_position=0, reach=None, quota_share=8,
                         logic=lambda obs, state: AgentAction(ActionKind.NOP))
    ])
    spec_b = ProcessEntrantSpec("B", "quiet_b", [
        ProcessInstance("pB", ProcessRole.DEFENDER, initial_position=500, reach=None, quota_share=8,
                         logic=lambda obs, state: AgentAction(ActionKind.NOP))
    ], start=500)
    spec_c = ProcessEntrantSpec("C", "bystander", [
        ProcessInstance("pC", ProcessRole.ATTACKER, initial_position=250, reach=None, quota_share=8,
                         logic=bystander_logic)
    ], start=250)

    replay_path = _run_low_level(
        [spec_a, spec_b, spec_c], tmp_path=tmp_path, max_ticks=3,
        ruleset_policy=RULESET_V5_R1_ALPHA1, process_integrity=4,
    )
    m = analyze_match(replay_path)

    assert m["process_deaths"]["A"] == 1
    assert m["process_deaths"]["B"] == 1
    assert m["process_extinction_tick"]["A"] == 1
    assert m["process_extinction_tick"]["B"] == 1
    assert m["entrant_ever_alive_with_zero_processes"]["A"] is True
    assert m["entrant_ever_alive_with_zero_processes"]["B"] is True
    assert m["core_capture_outcome"]["A"] == "survived"
    assert m["core_capture_outcome"]["B"] == "survived"


def test_analyzer_deterministic_with_r1_fields(tmp_path: Path) -> None:
    spec_a = ProcessEntrantSpec("A", "attacker", [
        ProcessInstance("pA", ProcessRole.ATTACKER, initial_position=0, reach=None, quota_share=8,
                         logic=lambda obs, state: AgentAction(ActionKindV2.WRITE, 500, 0x11))
    ])
    spec_b = ProcessEntrantSpec("B", "victim", [
        ProcessInstance("pB", ProcessRole.DEFENDER, initial_position=500, reach=None, quota_share=8,
                         logic=lambda obs, state: AgentAction(ActionKind.NOP))
    ], start=500)
    replay_path = _run_low_level(
        [spec_a, spec_b], tmp_path=tmp_path, max_ticks=8,
        ruleset_policy=RULESET_V5_R1_ALPHA1, process_integrity=3,
    )
    import json
    m1 = analyze_match(replay_path)
    m2 = analyze_match(replay_path)
    assert json.dumps(m1, sort_keys=True) == json.dumps(m2, sort_keys=True)
