"""The engine-level harness for the V6 E8 family behavior tests (phase I8-3).

A family package plays a **scripted, non-family** opponent through the real
match path (``NativeMatchService``, package loading, the condition's Ruleset,
a schema-2 trace), with explicit core starts so each scenario's geometry is
exact. The family instance is captured in-process (by wrapping the
module-level ``load_python_agent`` the runtime calls) so a test can compare
the policy's own state at every callback with what the trace shows. Nothing
here records or asserts an outcome (PR8 Sec 3.2; SYN6 Sec H, item 4).

A scripted opponent is a ``Plan``: per-tick MOVEs, scheduled WRITEs (hits),
an optional responsive evasion, and an optional cyclic own-core repair. A hit
whose address is ``None`` writes the family entrant's current anchor, which
the harness tracks from the family's own observations and MOVEs: an
omniscient, test-only targeting aid for placing hits at exact offers.
"""

from __future__ import annotations

import json
import random
import shutil
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest
from battle_engine import process_runtime
from battle_engine.agent_api import ActionKindV2, AgentAction, ObservationV2
from battle_engine.agent_parameters import resolve_parameters
from battle_engine.agents import resolve_agent
from battle_engine.config import Config
from battle_engine.match_service import MatchEntrant, MatchRequest, NativeMatchService
from battle_engine.placement import resolve_direct_match_starts
from battle_engine.python_runtime import derive_agent_seed
from battle_engine.ruleset_policy import (
    BYTEFRAY_RULESET_V6_RESEARCH_DISRUPTION_SLOT1_SENSING_ACTIVE_W27_ID,
    BYTEFRAY_RULESET_V6_RESEARCH_DISRUPTION_SLOT1_SENSING_R32_ID,
    BYTEFRAY_RULESET_V6_RESEARCH_SENSING_ACTIVE_W27_ID,
    BYTEFRAY_RULESET_V6_RESEARCH_SENSING_R32_ID,
)

from tools.research.v6.e8 import compatibility
from tools.research.v6.e8.family import PACKAGES, prepare_data_root

ARENA = 512
C8, T8 = BYTEFRAY_RULESET_V6_RESEARCH_SENSING_R32_ID, BYTEFRAY_RULESET_V6_RESEARCH_SENSING_ACTIVE_W27_ID
C8L = BYTEFRAY_RULESET_V6_RESEARCH_DISRUPTION_SLOT1_SENSING_R32_ID
T8L = BYTEFRAY_RULESET_V6_RESEARCH_DISRUPTION_SLOT1_SENSING_ACTIVE_W27_ID
CONDITIONS = {"C8": C8, "T8": T8, "C8L": C8L, "T8L": T8L}
ACTIVE_RULESETS = (T8, T8L)
WHOLE_TICK = (C8, T8)
SEATS = ("A", "B")

SCRIPT = '''
class Agent:
    target = None  # () -> address: injected by the test harness when a hit names no address

    def reset(self, context):
        self.me = context.agent_id
        self.damaged = False
        self.decoy_anchor = None
        self.watched_tick = 0
        self.tick = 0
        self.n = 0
        self.cursor = 0
        self.evasions = 0
        self.away_left = 2 if PLAN["processes"] == 2 else 0
        # The evading process's own callback counts (EVADE8's rule, per process).
        self.own_tick = {}
        self.own_count = {}
        self.own_previous = {}

    def declare_processes(self):
        if PLAN["processes"] == 2:
            return [ProcessDeclaration("decoy", 256, 0.5), ProcessDeclaration("hitter", 256, 0.5)]
        return [ProcessDeclaration("p", 256, 1.0)]

    def act(self, obs):
        if obs.current_tick != self.tick:
            self.tick, self.n = obs.current_tick, 0
        self.n += 1
        t, n, pid = obs.current_tick, self.n, obs.self_process_id
        first_of_tick = self.own_tick.get(pid) != t
        if first_of_tick:
            if pid in self.own_tick:
                self.own_previous[pid] = (self.own_tick[pid], self.own_count[pid])
            self.own_tick[pid], self.own_count[pid] = t, 0
        self.own_count[pid] += 1
        if pid == "hitter" and obs.previous_read_value is not None and obs.previous_read_owner not in (None, self.me):
            self.damaged = True  # the decoy's anchor cell was overwritten: the decoy was hit
        if pid != "hitter":
            self.decoy_anchor = obs.self_anchor
        if pid == "hitter" and self.away_left:
            self.away_left -= 1
            return AgentAction(ActionKindV2.MOVE, PLAN["away"])
        if pid != "hitter" and (t, self.own_count[pid]) in PLAN["moves"]:
            return AgentAction(ActionKindV2.MOVE, PLAN["moves"][(t, self.own_count[pid])])
        if (t, n) in PLAN["hits"]:
            address = PLAN["hits"][(t, n)]
            return AgentAction(ActionKindV2.WRITE, self.target() if address is None else address, 1)
        if PLAN["evade"] and pid != "hitter" and first_of_tick and not self.away_left:
            # Unlike EVADE8 (P8-5), a first callback after tick 1 counts as a hit: tick 1 was missed.
            previous_tick, previous_count = self.own_previous.get(pid, (0, PLAN["quota"]))
            if t > previous_tick + 1 or previous_count < PLAN["quota"] or self.damaged:
                self.damaged = False
                delta = PLAN["evade"][self.evasions % len(PLAN["evade"])]
                self.evasions += 1
                return AgentAction(ActionKindV2.MOVE, delta)
        if PLAN["evade"] and pid == "hitter" and self.decoy_anchor is not None and self.watched_tick != t:
            # The second process watches the decoy's anchor cell once a tick: under lambda = 1 the offer a
            # hit costs the decoy is rebalanced to this process, so the decoy's own count cannot show it.
            self.watched_tick = t
            return AgentAction(ActionKindV2.READ, self.decoy_anchor)
        if PLAN["repair"]:
            cell = obs.own_core_base + self.cursor
            self.cursor = (self.cursor + 1) % PLAN["repair"]
            return AgentAction(ActionKindV2.WRITE, cell, 0xCE)
        return AgentAction(ActionKindV2.READ, obs.own_core_base)


def create_agent():
    return Agent()
'''


@dataclass(frozen=True)
class Plan:
    """A scripted, non-family opponent."""

    #: The decoy's (or single process's) MOVEs: tick (its first callback of the tick) or (tick, its k-th).
    moves: Mapping[int | tuple[int, int], int] = field(default_factory=dict)
    hits: Mapping[tuple[int, int], int | None] = field(default_factory=dict)  # (tick, n-th callback) -> address
    #: A responsive evasion on each inferred hit: the MOVE deltas, cycled. Empty: never evades.
    evade: tuple[int, ...] = ()
    repair: int = 0  # cyclic own-core repair over this many cells, else READ its own core base
    #: 2: a "decoy" anchor that the family can know (it makes the moves and evasions) and a "hitter"
    #: that first MOVEs ``away`` twice -- out of the family's view and sensing windows -- so the family
    #: never disrupts it, and then makes the scheduled hits at the entrant's exact offers. The decoy
    #: evades only once the hitter has left, so the family's search never crosses the hitter in transit.
    processes: int = 1
    away: int = 64

    def source(self) -> str:
        moves = {key if isinstance(key, tuple) else (key, 1): delta for key, delta in self.moves.items()}
        plan = {"moves": moves, "hits": dict(self.hits), "evade": self.evade, "repair": self.repair,
                "processes": self.processes, "away": self.away, "quota": 8 // self.processes}
        return ("from battle_engine.agent_api import ActionKindV2, AgentAction, ProcessDeclaration\n\n"
                f"PLAN = {plan!r}\n" + SCRIPT)


IDLE = Plan()
STATIC = Plan(repair=8)


@dataclass(frozen=True)
class Snap:
    """The family policy's state right after one of its callbacks."""

    obs: ObservationV2
    action: AgentAction
    index: int
    purpose: str | None
    known: tuple[int, ...]
    missing: tuple[int, ...]
    search_address: int | None
    discovered: bool
    adapt_count: int
    switched: bool
    enemy_core: int | None


@dataclass
class Played:
    records: list[dict[str, Any]]
    starts: tuple[int, int]
    snaps: dict[str, list[Snap]]
    agents: dict[str, Any]
    replay: str
    seed: int

    def decisions(self, seat: str | None = None) -> list[dict[str, Any]]:
        return [r for r in self.records if r.get("record_type") == "decision_v2"
                and (seat is None or r["agent_id"] == seat)]

    def stream(self, seat: str) -> list[tuple[Any, ...]]:
        """A seat's decision records without wall time: comparable across matches."""
        return [(r["process_id"], r["observation"], r.get("action"), r["applied_result"]) for r in
                self.decisions(seat)]


def distance(a: int, b: int) -> int:
    d = (a - b) % ARENA
    return min(d, ARENA - d)


def sigma_of(seed: int, seat: str) -> int:
    """The family agent's reset draw sigma for ``seat`` at match seed ``seed`` (slot = seat order)."""
    return (-1, 1)[random.Random(derive_agent_seed(seed, SEATS.index(seat), seat, 2)).randrange(2)]


def agent_stream(seed: int, seat: str) -> random.Random:
    """A fresh copy of the family agent's stream for ``seat``."""
    return random.Random(derive_agent_seed(seed, SEATS.index(seat), seat, 2))


Entrant = str | Plan | Path


def play(tmp_path: Path, ruleset_id: str, a: Entrant, b: Entrant, *, starts: tuple[int, int] | None = None,
         seed: int = 7, ticks: int = 12) -> Played:
    """One traced match: each seat is an E8 family package ID (instrumented), a scripted
    ``Plan``, or another package directory (copied in, not instrumented)."""

    tmp_path.mkdir(parents=True, exist_ok=True)
    seats = {"A": a, "B": b}
    if starts is None:
        starts = tuple(resolve_direct_match_starts(ruleset_id=ruleset_id, arena_size=ARENA, entrant_count=2,
                                                   supplied_starts=[None, None], seed=seed))  # type: ignore[assignment]
    assert starts is not None
    names = {}
    for seat, who in seats.items():
        if isinstance(who, str):
            assert who in PACKAGES
            prepare_data_root(tmp_path, [who])
            names[seat] = who
        elif isinstance(who, Path):
            shutil.copytree(who, tmp_path / "agents" / who.name, dirs_exist_ok=True,
                            ignore=shutil.ignore_patterns("__pycache__"))
            names[seat] = who.name
        else:
            package = tmp_path / "agents" / f"scripted_{seat.lower()}"
            package.mkdir(parents=True, exist_ok=True)
            (package / "agent.yaml").write_text(json.dumps({"name": package.name, "kind": "python", "api_version": 2,
                                                            "entrypoint": "agent.py:create_agent",
                                                            "version": "1.0.0"}))
            (package / "agent.py").write_text(who.source())
            names[seat] = package.name
    # The pre-match compatibility gate, as the E8 runner will call it.
    compatibility.require_compatible([tmp_path / "agents" / name for name in names.values()], ruleset_id)

    snaps: dict[str, list[Snap]] = {}
    agents: dict[str, Any] = {}
    positions = {seat: start for seat, start in zip(SEATS, starts, strict=True)}
    family_seat = {names[seat]: seat for seat in SEATS if isinstance(seats[seat], str)}
    scripted_seat = {names[seat]: seat for seat in SEATS if isinstance(seats[seat], Plan)}
    original = process_runtime.load_python_agent

    def capturing(spec: Any) -> Any:
        loaded = original(spec)
        instance = loaded.instance
        name = spec.dir.name
        if name in family_seat:
            seat = family_seat[name]
            log = snaps.setdefault(seat, [])
            act: Callable[[ObservationV2], AgentAction] = instance.act

            def logged(observation: ObservationV2, *, _seat: str = seat, _log: list[Snap] = log,
                       _act: Callable[[ObservationV2], AgentAction] = act, _agent: Any = instance) -> AgentAction:
                action = _act(observation)
                pending = _agent.pending.get(observation.self_process_id)
                _log.append(Snap(observation, action, _agent.callback_index,
                                 pending[0] if pending and action.kind in (ActionKindV2.READ, ActionKindV2.SENSE)
                                 else None,
                                 tuple(_agent.known), tuple(_agent.missing), _agent.search_address,
                                 _agent.discovered, _agent.adapt_count, _agent.switched, _agent.enemy_core))
                if action.kind is ActionKindV2.MOVE:
                    positions[_seat] = (observation.self_anchor + max(-64, min(64, action.operand))) % ARENA
                else:
                    positions[_seat] = observation.self_anchor
                return action

            instance.act = logged
            agents[seat] = instance
        elif name in scripted_seat:
            other = "B" if scripted_seat[name] == "A" else "A"
            instance.target = lambda _other=other: positions[_other]
        return loaded

    entrants = []
    for seat, start in zip(SEATS, starts, strict=True):
        spec = resolve_agent(tmp_path, names[seat])
        parameters = resolve_parameters(spec.parameter_schema) if not isinstance(seats[seat], Plan) else None
        entrants.append(MatchEntrant.python(seat, names[seat], start, spec, parameters)
                        if parameters is not None else MatchEntrant.python(seat, names[seat], start, spec))
    trace = tmp_path / "trace.jsonl"
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(process_runtime, "load_python_agent", capturing)
        NativeMatchService().run(MatchRequest(
            config=Config(seed=seed, arena_size=ARENA, instr_per_tick=8), entrants=tuple(entrants), max_ticks=ticks,
            replay_path=tmp_path / "run" / "replay.jsonl", verbose=False, ruleset_id=ruleset_id, trace_path=trace))
    records = [json.loads(line) for line in trace.read_text(encoding="utf-8").splitlines()]
    replay = (tmp_path / "run" / "replay.jsonl").read_text(encoding="utf-8")
    return Played(records, (starts[0], starts[1]), snaps, agents, replay, seed)


def callbacks_by_tick(records: list[dict[str, Any]], seat: str) -> dict[int, int]:
    counts: dict[int, int] = {}
    for record in records:
        if record.get("record_type") == "decision_v2" and record["agent_id"] == seat:
            tick = record["observation"]["current_tick"]
            counts[tick] = counts.get(tick, 0) + 1
    return counts


def with_index(decisions: list[dict[str, Any]]) -> list[tuple[int, dict[str, Any]]]:
    """Each decision of one entrant with its callback index (1-based within its tick)."""

    out, tick, index = [], None, 0
    for record in decisions:
        current = record["observation"]["current_tick"]
        index = index + 1 if current == tick else 1
        tick = current
        out.append((index, record))
    return out
