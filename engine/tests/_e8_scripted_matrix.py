"""Shared fixtures for the V6 E8 I8-5 tests: scripted fields and a synthetic matrix.

Nothing here plays one family member against another, and no family package
plays at all.

* **Scripted fields** (``scripted_field``): two scripted, non-family agents
  (``SCOUT``, gated by ``sensing_window``) play through the real evaluation
  path, ``EvaluationService``, under any registered Ruleset, at infrastructure
  seeds and short tick limits, and are then traced and reduced to rows by the
  E8 trace tooling. Their artifacts are real; they are never matrix cells.
* **A synthetic matrix** (``synthetic_condition``): harness-shaped F1 and F2
  cell records for the eleven members' packages, at synthetic seeds, with
  outcomes from a deterministic function the test chooses. No match runs.
  These qualify the analyzer on designed tables whose registered statuses are
  known in advance.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any

from battle_engine.agent_evaluation import EvaluationRequest, EvaluationService
from battle_engine.evaluation_contracts import (
    ORIENTATION_CANDIDATE_FIRST,
    ORIENTATION_OPPONENT_FIRST,
)

from tools.research.v6.e8 import analyze_e8, family, matrix, traces

ARENA = 512

#: A scripted agent: SENSE under an active Ruleset (behind the registered context guard), MOVE
#: otherwise, and a WRITE at the last enemy anchor it learned of on every third callback.
SCOUT = '''\
from battle_engine.agent_api import ActionKindV2, AgentAction, ProcessDeclaration


class Agent:
    def reset(self, context):
        self.sensing_window = context.sensing_window
        self.k = 0
        self.found = None

    def declare_processes(self):
        return [ProcessDeclaration("p", REACH, 1.0)]

    def act(self, observation):
        self.k += 1
        sensed = observation.previous_sense_anchors
        if sensed:
            self.found = sensed[0]
        if observation.visible_enemy_anchor_addresses:
            self.found = observation.visible_enemy_anchor_addresses[0]
        if self.found is not None and self.k % 3 == 0:
            return AgentAction(ActionKindV2.WRITE, self.found, 1)
        if self.sensing_window is not None:
            return AgentAction(ActionKindV2.SENSE, observation.self_anchor + 55 * self.k)
        return AgentAction(ActionKindV2.MOVE, 64)


def create_agent():
    return Agent()
'''


def write_package(env: Path, name: str, source: str) -> Path:
    directory = env / "agents" / name
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "agent.yaml").write_text(json.dumps({
        "name": name, "kind": "python", "api_version": 2, "entrypoint": "agent.py:create_agent",
        "version": "1.0.0"}), encoding="utf-8")
    (directory / "agent.py").write_text(source, encoding="utf-8")
    return directory


def scout(env: Path, name: str, reach: int) -> Path:
    return write_package(env, name, SCOUT.replace("REACH", str(reach)))


def scripted_field(root: Path, ruleset_id: str, *, seeds: Sequence[int] = (1, 2), ticks: int = 40,
                   reaches: tuple[int, int] = (256, 100)) -> tuple[Path, Path, list[traces.TraceRecord],
                                                                   dict[str, dict[str, Any]]]:
    """Two scouts through the evaluation path, traced and reduced to rows: (field, env, records, cells)."""
    env = root / "env"
    if not (env / "agents" / "scout_a").exists():
        scout(env, "scout_a", reaches[0])
        scout(env, "scout_b", reaches[1])
    field = root / ruleset_id
    EvaluationService().run(EvaluationRequest(
        candidate_id="scout_a", opponent_ids=["scout_b"], seeds=tuple(seeds), ticks=ticks, arena_size=ARENA,
        ruleset_id=ruleset_id, output_dir=field / "arena_512" / "00-scout_a", data_root=env))
    records = traces.trace_field(field, data_root=env, ticks=ticks, arena_size=ARENA,
                                 expected_cells=2 * len(seeds))
    traces.rows_field(field, records, arena=ARENA)
    state = json.loads((field / "arena_512" / "00-scout_a" / "evaluation.json").read_text(encoding="utf-8"))
    cells = {cell["schedule_id"]: cell for cell in state["cells"]}
    return field, env, records, cells


# ---------------------------------------------------------------------------
# The synthetic matrix
# ---------------------------------------------------------------------------

SYNTHETIC_SEEDS: tuple[int, ...] = tuple(range(1001, 1001 + matrix.SEED_COUNT))
#: (seat A member, seat B member, seed) -> (winning seat "A"/"B" or "tie", final tick, captured seat or None)
Outcome = Callable[[str, str, int], tuple[str, int, str | None]]


def default_outcome(a: str, b: str, seed: int) -> tuple[str, int, str | None]:
    """A deterministic, seed-varied outcome with every result kind."""
    digest = hashlib.sha256(f"{a}|{b}|{seed}".encode()).digest()
    result = ("A", "B", "tie")[digest[0] % 3]
    ticks = 1000 if result == "tie" else 2 + digest[1] % 300
    return result, ticks, None if result == "tie" else ("B" if result == "A" else "A")


def _cell(subject: str, opponent: str, seed: int, orientation: str, outcome: Outcome) -> dict[str, Any]:
    seat_a, seat_b = (subject, opponent) if orientation == ORIENTATION_CANDIDATE_FIRST else (opponent, subject)
    member = {pid: m for pid, (m, _) in family.PACKAGES.items()}
    result, ticks, captured = outcome(member[seat_a], member[seat_b], seed)
    winner = {"A": seat_a, "B": seat_b}.get(result)
    terminations = {"A": None, "B": None}
    if captured is not None:
        terminations[captured] = "core_captured"
    return {
        "schedule_id": hashlib.sha256(f"{subject}|{opponent}|{seed}|{orientation}".encode()).hexdigest()[:16],
        "subject_id": subject, "opponent_id": opponent, "seed": seed, "orientation": orientation,
        "status": "completed", "outcome": "tie" if winner is None else ("win" if winner == subject else "loss"),
        "ticks_run": ticks, "termination_reason": "tick_limit" if result == "tie" else "completed",
        "entrant_terminations": terminations, "artifact_dir": f"synthetic/{seed}/{subject}/{orientation}",
        "seat_a_id": seat_a, "seat_b_id": seat_b,
    }


def synthetic_cells(outcome: Outcome = default_outcome, seeds: Sequence[int] = SYNTHETIC_SEEDS
                    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    f1 = [_cell(subject, opponent, seed, orientation, outcome)
          for subject, opponent in matrix.F1.pairs for seed in seeds
          for orientation in (ORIENTATION_CANDIDATE_FIRST, ORIENTATION_OPPONENT_FIRST)]
    f2 = [_cell(subject, opponent, seed, orientation, outcome)
          for subject, opponent in matrix.F2.pairs for seed in seeds
          for orientation in (ORIENTATION_CANDIDATE_FIRST, ORIENTATION_OPPONENT_FIRST)]
    return f1, f2


def seat_telemetry(member: str, *, verifications: int = 0, discovered: bool = True) -> dict[str, Any]:
    return {"member": member, "callbacks": 8, "ticks_with_callbacks": 1, "callbacks_per_tick": "8",
            "first_discovery_tick": 1 if discovered else None, "discovered": discovered,
            "senses_before_discovery": 1, "senses_after_discovery": 0, "read_probes": 0, "hits_received": 0,
            "hits_inferred": 0, "evasions": 0, "verifications": verifications, "verification_observations": 0,
            "reacquisitions": {}}


def synthetic_condition(condition_id: str, outcome: Outcome = default_outcome, *,
                        verifications: Callable[[str, int], int] | None = None,
                        contact: Callable[[dict[str, Any]], bool] | None = None,
                        seeds: Sequence[int] = SYNTHETIC_SEEDS) -> analyze_e8.ConditionData:
    """One synthetic condition: its cells, contacts and telemetry. ``verifications(opponent, seed)``
    gives ADAPT8's verification count in each cell."""
    f1, f2 = synthetic_cells(outcome, seeds)
    member = {pid: m for pid, (m, _) in family.PACKAGES.items()}
    tele: dict[str, Mapping[str, Mapping[str, Any]]] = {}
    for cell in [*f1, *f2]:
        seat_a, seat_b = cell["seat_a_id"], cell["seat_b_id"]
        rows = {}
        for seat, package, rival in (("A", seat_a, seat_b), ("B", seat_b, seat_a)):
            count = verifications(member[rival], int(cell["seed"])) if (
                verifications is not None and member[package] == "ADAPT8") else 0
            rows[seat] = seat_telemetry(member[package], verifications=count)
        tele[cell["schedule_id"]] = rows
    from tools.research.v6.e3.gates import cell_key

    return analyze_e8.ConditionData(condition_id, tuple(f1), tuple(f2),
                                    {cell_key(c): (True if contact is None else contact(c)) for c in f1}, tele)
