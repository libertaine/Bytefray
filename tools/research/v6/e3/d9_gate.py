"""The D9 real-fixture gate (E3 tooling phase; design review Sec G.5, Sec J D9).

G.5: with ``disruption_slot_limit = 1``, K = 2 and the rotating first mover,
an entrant whose final executed action on every tick in which it moves
second repairs its own core can never be at zero core at two consecutive
end-of-tick evaluations, so it can never be captured. The implementation
phase proved this with scripted guards. This gate checks it on the real,
tracked ``e2_repair_guard`` and ``e2_disrupt_guard``, under the primary
treatment Ruleset, before any treatment matrix cell is run.

Each scenario loads the guard exactly as a match does -- through
``ProcessMatchController.from_python_entrants``, the engine's own Agent API
v2 loading path -- and seats it against a *scripted adversary*: a host
fixture is loaded in the other seat and its process executor is replaced by
an adversarial jammer. No adversary is a matrix entrant, so no matrix cell is
exposed; the seeds are outside the matrix's 1..32. The adversaries:

* ``omniscient``: reads the controller -- re-disrupt the guard whenever its
  next offer is not already suppressed, otherwise erase an owned guard core
  cell (the implementation tests' strongest jammer);
* ``anchor``: every action writes the guard's anchor;
* ``alternating``: even own actions in a tick hit the anchor, odd ones erase
  guard core cells, continuing across ticks;
* ``random-<n>``: a seeded choice among the guard's core cells and a no-op.

The disrupt guard's G.5 condition needs at most three enemy locations; every
adversary here has one.

Each canonical replay is read back with capture analyzer v2 and the E3
action/parity analyzer. The gate requires zero capture completions against the
guard, a maximum zero-core streak of 1, the G.4 bound, no zero-action live
tick, every zero-core evaluation on the guard's own first-mover ticks, and
clean analyzer cross-checks. As a sensitivity check, the same scenarios under
the whole-tick parent (``bytefray-rules-6-research-capture-hold-k2``) must
capture the repair guard in at least one scenario -- so the gate can see a
capture when there is one.
"""

from __future__ import annotations

import json
import random
import tempfile
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from battle_engine.agent_api import ActionKindV2, AgentAction, ObservationV2
from battle_engine.agents import resolve_agent
from battle_engine.config import Config
from battle_engine.match_service import (
    MatchEntrant,
    MatchRequest,
    _build_process_result,
    _finalize_native_artifacts,
)
from battle_engine.placement import resolve_direct_match_starts
from battle_engine.process_runtime import ProcessMatchController
from battle_engine.ruleset_policy import resolve_ruleset_policy
from battle_engine.telemetry import JSONLSink

from tools.research.v6.e3 import matrix
from tools.research.v6.e3.action_parity import analyze_actions
from tools.research.v6.e3.entrants import prepare_data_root

D9_GATE_VERSION = 1
D9_RECORD_NAME = "d9_real_fixture_gate.json"
GUARDS: tuple[str, ...] = ("e2_repair_guard", "e2_disrupt_guard")
# The adversary seat is hosted by a tracked single-process, global-reach
# fixture whose executor is replaced; its own logic never runs.
ADVERSARY_HOST = "e2_sniper"
SEEDS: tuple[int, ...] = (42, 1001, 1002)
TICKS = 1000
RANDOM_ADVERSARIES = 8
PRIMARY_ID = matrix.condition(matrix.PRIMARY_TREATMENT).ruleset_id
WHOLE_TICK_ID = matrix.condition(matrix.PRIMARY_CONTROL).ruleset_id

Brain = Callable[[ProcessMatchController, ObservationV2], AgentAction]


class D9GateError(RuntimeError):
    """The D9 real-fixture gate has not passed."""


def _write(address: int, arena: int) -> AgentAction:
    return AgentAction(ActionKindV2.WRITE, operand=address % arena, value=1)


def _idle(obs: ObservationV2) -> AgentAction:
    return AgentAction(ActionKindV2.READ, operand=obs.own_core_base)


@dataclass
class _Target:
    """The guard, seen from the adversary's controller."""

    seat: str
    core: tuple[int, ...]
    arena: int


def _omniscient(target: _Target) -> Brain:
    def brain(controller: ProcessMatchController, obs: ObservationV2) -> AgentAction:
        spec = next(spec for spec in controller.entrant_specs if spec.agent_id == target.seat)
        if any(not controller._is_suppressed(p, obs.current_tick) for p in spec.processes):
            anchors = obs.visible_enemy_anchor_addresses
            return _write(anchors[0], target.arena) if anchors else _idle(obs)
        owned = [cell for cell in target.core if controller.vm.writer[cell] == target.seat]
        return _write(owned[0] if owned else target.core[0], target.arena)

    return brain


def _anchor(_target: _Target) -> Brain:
    def brain(_controller: ProcessMatchController, obs: ObservationV2) -> AgentAction:
        anchors = obs.visible_enemy_anchor_addresses
        return _write(anchors[0], _target.arena) if anchors else _idle(obs)

    return brain


def _alternating(target: _Target) -> Brain:
    state = {"tick": -1, "count": 0, "cursor": 0}

    def brain(_controller: ProcessMatchController, obs: ObservationV2) -> AgentAction:
        if obs.current_tick != state["tick"]:
            state["tick"], state["count"] = obs.current_tick, 0
        jam = state["count"] % 2 == 0
        state["count"] += 1
        anchors = obs.visible_enemy_anchor_addresses
        if jam and anchors:
            return _write(anchors[0], target.arena)
        state["cursor"] += 1
        return _write(target.core[state["cursor"] % len(target.core)], target.arena)

    return brain


def _random(seed: int) -> Callable[[_Target], Brain]:
    def make(target: _Target) -> Brain:
        rng = random.Random(seed)
        options: list[int | None] = [*target.core, None]

        def brain(_controller: ProcessMatchController, obs: ObservationV2) -> AgentAction:
            choice = rng.choice(options)
            return _idle(obs) if choice is None else _write(choice, target.arena)

        return brain

    return make


ADVERSARIES: dict[str, Callable[[_Target], Brain]] = {
    "omniscient": _omniscient,
    "anchor": _anchor,
    "alternating": _alternating,
    **{f"random-{n}": _random(n) for n in range(RANDOM_ADVERSARIES)},
}


def run_hosted_match(
    data_root: Path,
    out_dir: Path,
    *,
    ruleset_id: str,
    seat_names: dict[str, str],
    scripted_seat: str,
    brain: Brain,
    seed: int,
    ticks: int,
) -> Path:
    """One canonical match in which ``scripted_seat``'s process executor is
    replaced by ``brain``; the other seat is a real fixture, loaded and run
    exactly as a match runs it. Returns the canonical replay path (its
    ``result.json`` is written beside it by the engine's own finalization)."""
    arena = matrix.ARENA_SIZE
    starts = resolve_direct_match_starts(
        ruleset_id=ruleset_id, arena_size=arena, entrant_count=2, supplied_starts=[None, None], seed=seed
    )
    entrants = tuple(
        MatchEntrant.python(seat, seat_names[seat], start, resolve_agent(data_root, seat_names[seat]))
        for seat, start in zip(("A", "B"), starts, strict=True)
    )
    config = Config(seed=seed, arena_size=arena, instr_per_tick=matrix.QUOTA)
    controller = ProcessMatchController.from_python_entrants(
        config, entrants, ticks, ruleset_policy=resolve_ruleset_policy(ruleset_id)
    )
    try:
        scripted = next(spec for spec in controller.entrant_specs if spec.agent_id == scripted_seat)
        for process in scripted.processes:
            process.executor = lambda obs, _slot: brain(controller, obs)
        out_dir.mkdir(parents=True, exist_ok=True)
        replay = out_dir / "replay.jsonl"
        raw = out_dir / "raw.jsonl"
        sink = JSONLSink(str(raw))
        try:
            summary = controller.run(sink)
        finally:
            sink.close()
        # The engine's own finalization, exactly as NativeMatchService does it:
        # the canonical replay header and result.json come from the same code.
        request = MatchRequest(
            config=config, entrants=entrants, max_ticks=ticks, replay_path=replay, verbose=False,
            ruleset_id=ruleset_id,
        )
        _finalize_native_artifacts(request, _build_process_result(controller, summary, config, raw),
                                   final_replay_path=replay)
    finally:
        controller.close()
    return replay


def play_scenario(
    data_root: Path,
    out_dir: Path,
    *,
    ruleset_id: str,
    guard: str,
    guard_seat: str,
    adversary: str,
    seed: int,
    ticks: int = TICKS,
) -> dict[str, Any]:
    """One guard-vs-adversary match; returns the analyzers' reading of its replay."""
    arena = matrix.ARENA_SIZE
    adversary_seat = "B" if guard_seat == "A" else "A"
    starts = resolve_direct_match_starts(
        ruleset_id=ruleset_id, arena_size=arena, entrant_count=2, supplied_starts=[None, None], seed=seed
    )
    guard_start = starts[0 if guard_seat == "A" else 1]
    target = _Target(guard_seat, tuple((guard_start + i) % arena for i in range(8)), arena)
    replay = run_hosted_match(
        data_root, out_dir, ruleset_id=ruleset_id, seat_names={guard_seat: guard, adversary_seat: ADVERSARY_HOST},
        scripted_seat=adversary_seat, brain=ADVERSARIES[adversary](target), seed=seed, ticks=ticks,
    )
    telemetry = analyze_actions(replay, names_inferring_core=())
    seat = telemetry["seats"][guard_seat]
    other = telemetry["seats"][adversary_seat]
    zero_first = seat["capture"]["zero_ticks_opponent_first"]
    return {
        "ruleset_id": ruleset_id,
        "guard": guard,
        "guard_seat": guard_seat,
        "adversary": adversary,
        "seed": seed,
        "ticks": telemetry["ticks"],
        "guard_alive_at_end": telemetry["ticks"] == ticks and seat["capture"]["termination"] is None,
        "guard_completions": seat["capture"]["completions"],
        "guard_max_streak": seat["capture"]["max_streak"],
        "guard_zero_core_evaluations": seat["phase_lock"]["zero_core_evaluations"],
        "guard_zero_ticks_on_opponent_first": zero_first,
        "guard_min_actions": {role: seat["roles"][role]["min_executed_alive_throughout"] for role in ("first", "second")},
        "g4_violations": seat["g4_violations"] + other["g4_violations"],
        "zero_action_live_ticks": seat["zero_action_live_ticks"] + other["zero_action_live_ticks"],
        "checks_ok": telemetry["checks"]["ok"],
        "problems": telemetry["checks"]["problems"],
    }


def scenario_ok(row: dict[str, Any]) -> bool:
    """G.5 on one primary-treatment scenario."""
    return (
        row["checks_ok"]
        and row["guard_completions"] == 0
        and row["guard_max_streak"] <= 1
        and row["guard_alive_at_end"]
        and row["g4_violations"] == 0
        and row["zero_action_live_ticks"] == 0
        and row["guard_zero_ticks_on_opponent_first"] == 0
    )


def run_gate(
    work_dir: Path | None = None,
    *,
    seeds: Sequence[int] = SEEDS,
    ticks: int = TICKS,
    adversaries: Sequence[str] = tuple(ADVERSARIES),
) -> dict[str, Any]:
    """Every guard x seat x adversary x seed, under the primary treatment and the whole-tick parent."""
    if set(seeds) & set(matrix.SEEDS):
        raise D9GateError("D9 real-fixture scenarios must not use matrix seeds (1..32).")
    with tempfile.TemporaryDirectory(prefix="e3-d9-") as tmp:
        base = Path(work_dir) if work_dir is not None else Path(tmp)
        data_root = prepare_data_root(base / "env", [*GUARDS, ADVERSARY_HOST])
        rows: dict[str, list[dict[str, Any]]] = {PRIMARY_ID: [], WHOLE_TICK_ID: []}
        for ruleset_id, scenarios in rows.items():
            for guard in GUARDS:
                for guard_seat in ("A", "B"):
                    for adversary in adversaries:
                        for seed in seeds:
                            tag = f"{ruleset_id}/{guard}-{guard_seat}-{adversary}-{seed}"
                            scenarios.append(play_scenario(
                                data_root, base / "runs" / tag, ruleset_id=ruleset_id, guard=guard,
                                guard_seat=guard_seat, adversary=adversary, seed=seed, ticks=ticks))
    primary = rows[PRIMARY_ID]
    parent = rows[WHOLE_TICK_ID]
    failures = [row for row in primary if not scenario_ok(row)]
    parent_repair_captures = sum(
        1 for row in parent if row["guard"] == "e2_repair_guard" and row["guard_completions"] > 0
    )
    parent_clean = all(row["checks_ok"] for row in parent)
    passed = bool(primary) and not failures and parent_repair_captures > 0 and parent_clean
    return {
        "d9_gate_version": D9_GATE_VERSION,
        "primary_ruleset": PRIMARY_ID,
        "sensitivity_ruleset": WHOLE_TICK_ID,
        "guards": list(GUARDS),
        "adversary_host": ADVERSARY_HOST,
        "adversaries": list(adversaries),
        "seeds": list(seeds),
        "ticks": ticks,
        "primary_scenarios": len(primary),
        "primary_guard_completions": sum(row["guard_completions"] for row in primary),
        "primary_max_guard_streak": max((row["guard_max_streak"] for row in primary), default=None),
        "primary_min_guard_actions": {
            role: min((row["guard_min_actions"][role] for row in primary if row["guard_min_actions"][role] is not None),
                      default=None)
            for role in ("first", "second")
        },
        "primary_guard_zero_core_evaluations": sum(row["guard_zero_core_evaluations"] for row in primary),
        "primary_failures": failures[:10],
        "primary_failure_count": len(failures),
        "sensitivity_scenarios": len(parent),
        "sensitivity_repair_guard_captured_scenarios": parent_repair_captures,
        "sensitivity_disrupt_guard_captured_scenarios": sum(
            1 for row in parent if row["guard"] == "e2_disrupt_guard" and row["guard_completions"] > 0),
        "status": "PASS" if passed else "FAIL",
        "scenarios": {"primary": primary, "sensitivity": parent},
    }


def write_record(path: Path, record: dict[str, Any], *, freeze_id: str, provenance: dict[str, Any]) -> dict[str, Any]:
    full = {**record, "freeze_id": freeze_id, "provenance": provenance}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(full, indent=2, sort_keys=True), encoding="utf-8")
    return full


def require_d9_gate(path: Path, *, freeze_id: str) -> dict[str, Any]:
    if not path.is_file():
        raise D9GateError(f"No D9 real-fixture gate record at {path}.")
    record: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    problems = []
    if record.get("freeze_id") != freeze_id:
        problems.append(f"freeze_id {record.get('freeze_id')!r} != {freeze_id!r}")
    if record.get("status") != "PASS":
        problems.append(f"status {record.get('status')!r}")
    if record.get("seeds") != list(SEEDS) or record.get("ticks") != TICKS or record.get("adversaries") != list(ADVERSARIES):
        problems.append("the record is not the full registered gate (seeds, ticks, adversaries)")
    if problems:
        raise D9GateError("D9 real-fixture gate does not permit treatment: " + "; ".join(problems))
    return record
