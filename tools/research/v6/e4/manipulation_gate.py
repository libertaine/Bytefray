"""The G.4' manipulation gate (design review Sec J P1-P6, Sec R hard stop 5).

Before any treatment is authorized, the frozen manipulation checks are proven
on controlled, non-matrix scenarios under both mirrored Rulesets (T-E4, T-E4K1),
with their forward parents (C-E4, C-E4K1) as the sensitivity check:

1. **Offer sequence.** Two idle scripted entrants on a directly constructed
   ``ProcessMatchController`` for ticks 1-4: every offer executes, so the
   recorded (seat, slot) calls are the scheduled sequence. Mirrored: chunk
   owners ``FFLLFFLLLLFFLLFF`` with each entrant's slots 0..7 in order; forward:
   ``FFLLFFLLFFLLFFLL``.
2. **G.4' bound.** Every jam over a victim's anchors in one tick -- a
   single-process, a co-located and a spread victim, in both scheduler
   positions: the minimum executed actions is exactly (5, 5) under the
   mirrored order, never 0; the forward parents give (5, 4).
3. **Real fixture.** The tracked ``e3_jam_sniper`` against each of the nine
   E4 agents and its twin at seed 42 (outside the matrix seeds), 1000 ticks:
   the treatment manipulation checks (``gates.manipulation_checks``) pass
   under the mirrored Rulesets and the G.4' clause fails under the forward
   parents, where a jammed second mover can fall to 4 actions.

No scenario is a matrix cell.
"""

from __future__ import annotations

import itertools
import json
import tempfile
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

from battle_engine.agent_api import ActionKindV2, AgentAction, ObservationV2
from battle_engine.agents import resolve_agent
from battle_engine.config import Config
from battle_engine.match_service import MatchEntrant, MatchRequest, NativeMatchService
from battle_engine.placement import resolve_direct_match_starts
from battle_engine.process_runtime import (
    ProcessEntrantSpec,
    ProcessInstance,
    ProcessMatchController,
    ProcessRole,
)
from battle_engine.ruleset_policy import resolve_ruleset_policy

from tools.research.v6.e3.entrants import JAM_SNIPER, JAM_SNIPER_TWIN, prepare_data_root
from tools.research.v6.e4 import matrix
from tools.research.v6.e4.gates import G4_PRIME_MIN, manipulation_checks
from tools.research.v6.e4.telemetry import analyze_cell

MANIPULATION_GATE_VERSION = 1
MANIPULATION_RECORD_NAME = "manipulation_gate.json"
MIRRORED_ROLES = "FFLLFFLLLLFFLLFF"
FORWARD_ROLES = "FFLLFFLLFFLLFFLL"
FIXTURE_SEED = 42
FIXTURE_TICKS = 1000
ARENA = matrix.ARENA_SIZE
QUOTA = matrix.QUOTA
_CORES = {"A": 100, "B": 300}
_JAM_ANCHOR = 40
_VICTIM_ANCHOR = 440
_IDLE = AgentAction(ActionKindV2.READ, operand=0)
VICTIM_LAYOUTS: dict[str, tuple[tuple[str, int, int], ...]] = {
    "single-process": (("p", _VICTIM_ANCHOR, QUOTA),),
    "co-located": (("v0", _VICTIM_ANCHOR, 4), ("v1", _VICTIM_ANCHOR, 4)),
    "spread": (("v0", _VICTIM_ANCHOR, 4), ("v1", _VICTIM_ANCHOR + 10, 4)),
}


class ManipulationGateError(RuntimeError):
    """The G.4' manipulation gate has not passed."""


def _process(pid: str, anchor: int, share: int, act: Callable[[ObservationV2, int], AgentAction]) -> ProcessInstance:
    return ProcessInstance(pid, ProcessRole.GENERALIST, initial_position=anchor, reach=ARENA // 2, quota_share=share,
                           logic=lambda _obs, _state: _IDLE, executor=act)


def offer_sequence(ruleset_id: str, ticks: int = 4) -> dict[str, Any]:
    """Part 1: the scheduled (seat, slot) calls of idle scripted entrants, by tick."""
    calls: list[tuple[int, str, int]] = []

    def recorder(seat: str) -> Callable[[ObservationV2, int], AgentAction]:
        def act(obs: ObservationV2, slot: int) -> AgentAction:
            calls.append((obs.current_tick, seat, slot))
            return _IDLE

        return act

    specs = [ProcessEntrantSpec(agent_id=seat, name=f"seat-{seat}", processes=[_process("p", anchor, QUOTA, recorder(seat))],
                                start=_CORES[seat])
             for seat, anchor in (("A", _JAM_ANCHOR), ("B", _VICTIM_ANCHOR))]
    controller = ProcessMatchController(Config(seed=1, arena_size=ARENA, instr_per_tick=QUOTA), specs, ticks,
                                        ruleset_policy=resolve_ruleset_policy(ruleset_id))
    controller.run()
    per_tick = {}
    for tick in range(1, ticks + 1):
        rows = [(seat, slot) for t, seat, slot in calls if t == tick]
        first = "AB"[(tick - 1) % 2]
        per_tick[tick] = {
            "roles": "".join("F" if seat == first else "L" for seat, _ in rows),
            "slots_in_order": all([slot for s, slot in rows if s == seat] == list(range(QUOTA)) for seat in "AB"),
        }
    return {"ruleset_id": ruleset_id, "ticks": per_tick}


def _victim_actions(ruleset_id: str, layout: Sequence[tuple[str, int, int]], jam: Sequence[AgentAction],
                    *, victim_first: bool) -> int:
    victim = ProcessEntrantSpec(agent_id="V", name="victim", start=_CORES["B"],
                                processes=[_process(pid, anchor, share, lambda _obs, _slot: _IDLE)
                                           for pid, anchor, share in layout])
    jammer = ProcessEntrantSpec(agent_id="J", name="jammer", start=_CORES["A"],
                                processes=[_process("j", _JAM_ANCHOR, QUOTA, lambda _obs, slot: jam[slot])])
    controller = ProcessMatchController(Config(seed=1, arena_size=ARENA, instr_per_tick=QUOTA),
                                        [victim, jammer] if victim_first else [jammer, victim], 1,
                                        ruleset_policy=resolve_ruleset_policy(ruleset_id))
    controller.run()
    state = next(state for state in controller.states if state.agent_id == "V")
    if not state.alive:
        raise ManipulationGateError("a jammed victim died in a one-tick scenario")
    return int(state.cpu_used)


def jam_bound(ruleset_id: str) -> dict[str, Any]:
    """Part 2: the minimum executed actions over every jam, per layout and position."""
    out: dict[str, Any] = {}
    for name, layout in VICTIM_LAYOUTS.items():
        options = [AgentAction(ActionKindV2.WRITE, operand=anchor, value=1)
                   for anchor in sorted({anchor for _, anchor, _ in layout})] + [_IDLE]
        jams = list(itertools.product(options, repeat=QUOTA))
        row = {}
        for victim_first, role in ((True, "first"), (False, "second")):
            actions = [_victim_actions(ruleset_id, layout, jam, victim_first=victim_first) for jam in jams]
            row[role] = {"min": min(actions), "zero_occurs": 0 in actions, "jams": len(jams)}
        out[name] = row
    return {"ruleset_id": ruleset_id, "layouts": out,
            "minimum": {role: min(row[role]["min"] for row in out.values()) for role in ("first", "second")},
            "zero_occurs": any(row[role]["zero_occurs"] for row in out.values() for role in ("first", "second"))}


def fixture_checks(ruleset_id: str, work: Path, *, mirrored: bool) -> dict[str, Any]:
    """Part 3: the jam sniper against every E4 agent and its twin at seed 42."""
    opponents = [*matrix.E4_AGENTS, JAM_SNIPER_TWIN]
    data_root = prepare_data_root(work / "env", [JAM_SNIPER, *opponents])
    rows: dict[str, dict[str, Any]] = {}
    for opponent in opponents:
        starts = resolve_direct_match_starts(ruleset_id=ruleset_id, arena_size=ARENA, entrant_count=2,
                                             supplied_starts=[None, None], seed=FIXTURE_SEED)
        out = work / "runs" / ruleset_id / opponent
        out.mkdir(parents=True, exist_ok=True)
        NativeMatchService().run(MatchRequest(
            config=Config(seed=FIXTURE_SEED, arena_size=ARENA, instr_per_tick=QUOTA),
            entrants=(MatchEntrant.python("A", JAM_SNIPER, starts[0], resolve_agent(data_root, JAM_SNIPER)),
                      MatchEntrant.python("B", opponent, starts[1], resolve_agent(data_root, opponent))),
            max_ticks=FIXTURE_TICKS, replay_path=out / "replay.jsonl", verbose=False, ruleset_id=ruleset_id))
        rows[f"{JAM_SNIPER}|{opponent}"] = {"key": opponent, "telemetry": analyze_cell(out)}
    report = manipulation_checks(rows, mirrored=True)
    report["second_mover_min"] = min(
        (seat["roles"]["second"]["min_executed_alive_throughout"] for row in rows.values()
         for seat in row["telemetry"]["e3"]["seats"].values()
         if seat["roles"]["second"]["min_executed_alive_throughout"] is not None), default=None)
    report["ruleset_id"] = ruleset_id
    report["expected_mirrored"] = mirrored
    return report


def run_gate(work_dir: Path | None = None) -> dict[str, Any]:
    pairs = [(matrix.condition(t).ruleset_id, matrix.condition(matrix.condition(t).parent or "").ruleset_id)
             for t in matrix.TREATMENT_CONDITIONS]
    with tempfile.TemporaryDirectory(prefix="e4-g4-") as tmp:
        base = Path(work_dir) if work_dir is not None else Path(tmp)
        rows = []
        for treatment, parent in pairs:
            sequences = {rid: offer_sequence(rid) for rid in (treatment, parent)}
            bounds = {rid: jam_bound(rid) for rid in (treatment, parent)}
            fixtures = {treatment: fixture_checks(treatment, base / "t", mirrored=True),
                        parent: fixture_checks(parent, base / "p", mirrored=False)}
            t_seq, p_seq = sequences[treatment]["ticks"], sequences[parent]["ticks"]
            checks = {
                "treatment_sequence": all(row["roles"] == MIRRORED_ROLES and row["slots_in_order"] for row in t_seq.values()),
                "parent_sequence": all(row["roles"] == FORWARD_ROLES and row["slots_in_order"] for row in p_seq.values()),
                "treatment_g4_prime": bounds[treatment]["minimum"] == {"first": G4_PRIME_MIN, "second": G4_PRIME_MIN}
                and not bounds[treatment]["zero_occurs"],
                "parent_g4": bounds[parent]["minimum"] == {"first": 5, "second": 4} and not bounds[parent]["zero_occurs"],
                "treatment_fixture_checks": fixtures[treatment]["status"] == "PASS"
                and fixtures[treatment]["second_mover_min"] == G4_PRIME_MIN,
                "parent_fixture_sensitivity": fixtures[parent]["violations"].get("g4_prime_violation", 0) > 0,
            }
            rows.append({"treatment": treatment, "parent": parent, "sequences": sequences, "bounds": bounds,
                         "fixtures": fixtures, "checks": checks, "status": "PASS" if all(checks.values()) else "FAIL"})
    return {"manipulation_gate_version": MANIPULATION_GATE_VERSION, "fixture_seed": FIXTURE_SEED,
            "fixture_ticks": FIXTURE_TICKS, "arms": rows,
            "status": "PASS" if rows and all(row["status"] == "PASS" for row in rows) else "FAIL"}


def write_record(path: Path, record: dict[str, Any], *, freeze_id: str, provenance: dict[str, Any]) -> dict[str, Any]:
    full = {**record, "freeze_id": freeze_id, "provenance": provenance}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(full, indent=2, sort_keys=True), encoding="utf-8")
    return full


def require_gate(path: Path, *, freeze_id: str) -> dict[str, Any]:
    if not path.is_file():
        raise ManipulationGateError(f"No G.4' manipulation gate record at {path}.")
    record: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    if record.get("freeze_id") != freeze_id or record.get("status") != "PASS" or len(record.get("arms") or []) != 2:
        raise ManipulationGateError("The G.4' manipulation gate does not permit treatment.")
    return record
