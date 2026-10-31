"""Test-only fixture opponents and a small match harness.

The fixtures have explicitly stated behaviour and live only in tests: they
are written into ``tmp_path`` and are never installed or discoverable. The
harness runs one real match under Active Sensing and parses its replay and
agent trace, so assertions read evidence out of an actual execution.
"""

from __future__ import annotations

import json
from pathlib import Path

from battle_engine.agents import agent_spec_from_dir
from battle_engine.config import Config
from battle_engine.match_service import MatchEntrant, MatchRequest, NativeMatchService
from battle_engine.replay import MatchResult, iter_replay
from battle_engine.rules import BYTEFRAY_RULESET_V6_ALPHA1_ID

ARENA_SIZE = 512
CORE_SIZE = 8
QUOTA = 8


# --------------------------------------------------------------------------
# Fixtures: test-only opponents with explicitly stated behaviour.
# --------------------------------------------------------------------------

#: Stands still and never writes. A vulnerable, perfectly static objective:
#: whatever a starter takes from its core stays taken, so a capture here is
#: a capture the starter earned by covering the region, not one the fixture
#: handed over by forgetting to repair.
IDLE_TARGET_SOURCE = """
from battle_engine.agent_api import ActionKindV2, AgentAction, ProcessDeclaration


class IdleTarget:
    def reset(self, context):
        self.context = context

    def declare_processes(self):
        return [ProcessDeclaration(id="idle", reach=1, share=1.0)]

    def act(self, observation):
        return AgentAction(kind=ActionKindV2.MOVE, operand=0)


def create_agent():
    return IdleTarget()
"""

#: Walks forward three cells per action and never writes. A moving contact:
#: an agent with no memory has to re-acquire it every action, and an agent
#: with memory has to notice the memory going stale.
DRIFTING_TARGET_SOURCE = """
from battle_engine.agent_api import ActionKindV2, AgentAction, ProcessDeclaration


class DriftingTarget:
    def reset(self, context):
        self.context = context

    def declare_processes(self):
        return [ProcessDeclaration(id="drifter", reach=1, share=1.0)]

    def act(self, observation):
        return AgentAction(kind=ActionKindV2.MOVE, operand=3)


def create_agent():
    return DriftingTarget()
"""

#: Applies real, recurring pressure to a defender's core: it closes on the
#: nearest visible enemy anchor and then cycles writes over exactly four
#: addresses bracketing it -- offsets -3, -2, +2, +3.
#:
#: Two deliberate limits make this a *measuring instrument* rather than an
#: opponent. It touches at most four cells, so it can never capture an
#: eight-cell core and the match cannot end before detection and repair have
#: been observed many times over; and it never writes offset 0, the anchor
#: itself, so it never disrupts the defender. What is left is a clean,
#: sustained damage/repair contest, which is the mechanic under test.
#:
#: It uses only ``ObservationV2``. It is not told where the defender's core
#: is; it simply presses the ground the defender is standing on.
CORE_PRESSER_SOURCE = """
from battle_engine.agent_api import ActionKindV2, AgentAction, ProcessDeclaration

PRESS_OFFSETS = (-3, -2, 2, 3)


class CorePresser:
    def reset(self, context):
        self.context = context
        self.arena = context.arena_size
        self.cursor = 0

    def declare_processes(self):
        return [ProcessDeclaration(id="presser", reach=12, share=1.0)]

    def act(self, observation):
        visible = observation.visible_enemy_anchor_addresses
        if not visible:
            return AgentAction(kind=ActionKindV2.MOVE, operand=observation.self_reach)
        target = min(visible, key=lambda a: (self._distance(a, observation.self_anchor), a))
        if self._distance(target, observation.self_anchor) > observation.self_reach - 4:
            return AgentAction(kind=ActionKindV2.MOVE, operand=self._delta(target, observation.self_anchor))
        for _ in range(len(PRESS_OFFSETS)):
            offset = PRESS_OFFSETS[self.cursor % len(PRESS_OFFSETS)]
            self.cursor += 1
            address = (target + offset) % self.arena
            if self._distance(address, observation.self_anchor) <= observation.self_reach:
                return AgentAction(kind=ActionKindV2.WRITE, operand=address, value=0x11)
        return AgentAction(kind=ActionKindV2.MOVE, operand=0)

    def _distance(self, a, b):
        delta = abs((a - b) % self.arena)
        return min(delta, self.arena - delta)

    def _delta(self, target, anchor):
        forward = (target - anchor) % self.arena
        backward = forward - self.arena
        chosen = backward if abs(backward) < abs(forward) else forward
        return max(-64, min(64, chosen))


def create_agent():
    return CorePresser()
"""

FIXTURE_SOURCES = {
    "fixture_idle_target": IDLE_TARGET_SOURCE,
    "fixture_drifting_target": DRIFTING_TARGET_SOURCE,
    "fixture_core_presser": CORE_PRESSER_SOURCE,
}


def _write_fixture(root: Path, name: str) -> None:
    agent_dir = root / "agents" / name
    agent_dir.mkdir(parents=True, exist_ok=True)
    agent_dir.joinpath("agent.yaml").write_text(
        json.dumps(
            {
                "name": name,
                "display": name,
                "kind": "python",
                "api_version": 2,
                "entrypoint": "agent.py:create_agent",
                "version": "1.0.0",
            }
        ),
        encoding="utf-8",
    )
    agent_dir.joinpath("agent.py").write_text(FIXTURE_SOURCES[name], encoding="utf-8")


# --------------------------------------------------------------------------
# Match harness
# --------------------------------------------------------------------------


def _fixture_spec(root: Path, name: str):
    _write_fixture(root, name)
    spec = agent_spec_from_dir(root / "agents" / name)
    assert spec is not None, name
    return spec


class Match:
    """One completed match, with its replay and trace parsed."""

    def __init__(self, replay_path: Path, trace_path: Path, starts: tuple[int, int]):
        self.starts = starts
        self.records = list(iter_replay(replay_path))
        self.result = next(r for r in self.records if isinstance(r, MatchResult))
        self.trace = [
            json.loads(line)
            for line in trace_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

    def decisions(self, slot: str) -> list[dict]:
        return [
            record
            for record in self.trace
            if record.get("record_type") == "decision_v2"
            and record.get("agent_id") == slot
        ]

    def declarations(self, slot: str) -> list[dict]:
        return [
            record
            for record in self.trace
            if record.get("record_type") == "declaration"
            and record.get("agent_id") == slot
        ]

    def statuses(self, slot: str) -> set[str]:
        return {(d.get("applied_result") or {}).get("status") for d in self.decisions(slot)}

    def action_kinds(self, slot: str) -> set[str]:
        return {(d.get("action") or {}).get("kind") for d in self.decisions(slot)}

    def written_addresses(self, slot: str) -> set[int]:
        return {
            (d["action"]["operand"]) % ARENA_SIZE
            for d in self.decisions(slot)
            if d["action"]["kind"] == "write"
        }

    def core_cells(self, slot: str) -> set[int]:
        """The eight cells of one entrant's core, from its known start."""

        base = self.starts[0] if slot == "A" else self.starts[1]
        return {(base + i) % ARENA_SIZE for i in range(CORE_SIZE)}

    def termination(self, slot: str) -> str | None:
        return next(a.termination_reason for a in self.result.agents if a.agent_id == slot)

    def captured(self, slot: str) -> bool:
        return self.termination(slot) == "core_captured"


def run_match(
    tmp_path: Path,
    label: str,
    a_spec,
    b_spec,
    *,
    starts: tuple[int, int],
    seed: int,
    ticks: int,
) -> Match:
    replay_path = tmp_path / label / "replay.jsonl"
    trace_path = tmp_path / label / "trace.jsonl"
    request = MatchRequest(
        config=Config(seed=seed, arena_size=ARENA_SIZE, instr_per_tick=QUOTA),
        entrants=(
            MatchEntrant.python("A", a_spec.name, starts[0], a_spec),
            MatchEntrant.python("B", b_spec.name, starts[1], b_spec),
        ),
        max_ticks=ticks,
        replay_path=replay_path,
        trace_path=trace_path,
        verbose=False,
        ruleset_id=BYTEFRAY_RULESET_V6_ALPHA1_ID,
    )
    NativeMatchService().run(request)
    return Match(replay_path, trace_path, starts)


def gameplay_digest(match: Match) -> str:
    """Everything the agents did, with wall-clock timing excluded.

    Trace records carry ``wall_time_ms`` and the replay header carries
    generation timestamps, so raw file bytes differ between two identical
    runs. Determinism is a property of the decisions and the resulting
    arena, which is what this hashes.
    """

    import hashlib

    digest = hashlib.sha256()
    for record in match.trace:
        kind = record.get("record_type")
        if kind == "decision_v2":
            digest.update(
                json.dumps(
                    [
                        record["agent_id"],
                        record["process_id"],
                        record["action"],
                        record["observation"],
                        record["applied_result"],
                    ],
                    sort_keys=True,
                ).encode("utf-8")
            )
        elif kind == "declaration":
            digest.update(
                json.dumps(
                    [record["agent_id"], record["process_id"], record["reach"], record["share"]],
                    sort_keys=True,
                ).encode("utf-8")
            )
    return digest.hexdigest()
