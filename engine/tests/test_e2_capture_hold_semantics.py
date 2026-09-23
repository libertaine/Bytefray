"""V6 E2 capture-hold semantics (design review Sec J.3) and mechanic
characterizations (Sec J.4).

docs/research/v6/V6_E2_CAPTURE_HOLD_DESIGN_REVIEW.md Sec C specifies the
``capture_hold_ticks`` (K) state machine; this module proves each clause by
running real matches and asserting whole per-tick sequences by value.

* Sec J.3 tests drive a directly constructed ``ProcessMatchController``
  under ``RULESET_V6_RESEARCH_CAPTURE_HOLD_K2`` with scripted entrants whose
  every action is fixed per tick. Streak progress is deliberately never
  serialized (review Sec K), so a recording replay sink reads each
  entrant's live ``core_zero_streak``/``core_zero_onset_capturer`` at the
  point every tick is published -- after capture evaluation and scoring,
  before termination -- alongside that tick's real replay record (events,
  score, memory diffs, per-entrant ``cpu_used``). The engine is not
  instrumented or patched.
* Sec J.4 characterizations run the review's Sec D traces end to end
  through ``NativeMatchService`` with real Agent API v2 agents at seed 42,
  arena 512, and assert them from the canonical replay alone: capture
  progress is derived from the replay's memory diffs exactly as the review's
  Sec K analyzer would derive it. These pin *mechanics*, never a desired
  balance outcome.
"""

from __future__ import annotations

import textwrap
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest
from battle_engine.agent_api import ActionKindV2, AgentAction, ObservationV2
from battle_engine.agents import resolve_agent
from battle_engine.config import Config
from battle_engine.match_service import MatchEntrant, MatchRequest, NativeMatchService
from battle_engine.placement import resolve_direct_match_starts
from battle_engine.process_runtime import (
    EntrantState,
    ProcessEntrantSpec,
    ProcessInstance,
    ProcessMatchController,
    ProcessRole,
)
from battle_engine.python_runtime import apply_core_capture
from battle_engine.replay import (
    KillDeathEvent,
    MatchResult,
    ReplayHeader,
    RuntimeEvent,
    TickSnapshot,
    iter_replay,
)
from battle_engine.ruleset_policy import (
    BYTEFRAY_RULESET_V6_RESEARCH_CAPTURE_HOLD_K2_ID,
    RULESET_V4,
    RULESET_V6_RESEARCH_CAPTURE_HOLD_K2,
    RULESET_V6_RESEARCH_SCALE,
    RulesetPolicy,
)
from battle_engine.scoring import ScoringPolicy
from battle_engine.statistics import StatisticsCollector
from battle_engine.vm import VM

E2 = RULESET_V6_RESEARCH_CAPTURE_HOLD_K2

# ---------------------------------------------------------------------------
# Sec J.3 harness: scripted entrants on a directly constructed controller
# ---------------------------------------------------------------------------

ARENA = 512
QUOTA = 8
# Core bases, and process anchors placed away from every core so that core
# writes never disrupt anyone: these tests isolate the capture state machine
# from disruption (Sec J.4 below covers the two together).
CORE = {"A": 100, "B": 300}
ANCHOR = {"A": 40, "B": 440}


def _cells(base: int) -> list[int]:
    return [(base + offset) % ARENA for offset in range(8)]


def _w(address: int) -> AgentAction:
    return AgentAction(ActionKindV2.WRITE, operand=address, value=1)


# An action with no ownership effect, used for every unscripted slot.
_IDLE = AgentAction(ActionKindV2.READ, operand=0)
# Scripted in place of an action: the callback raises, and the runtime
# forfeits the entrant at exactly that slot.
_FORFEIT = "forfeit"

Script = Mapping[int, Sequence[AgentAction | str]]


def _scripted(script: Script) -> Callable[..., AgentAction]:
    """Return the entrant's scripted actions for each tick, in slot order."""

    def logic(obs: ObservationV2, local: dict[str, Any]) -> AgentAction:
        if local.get("tick") != obs.current_tick:
            local["tick"] = obs.current_tick
            local["index"] = 0
        actions = script.get(obs.current_tick, ())
        index = local["index"]
        local["index"] = index + 1
        action = actions[index] if index < len(actions) else _IDLE
        if action == _FORFEIT:
            raise RuntimeError("scripted forfeit")
        assert isinstance(action, AgentAction)
        return action

    return logic


@dataclass(frozen=True)
class EntrantTick:
    alive: bool
    owned: int
    streak: int
    onset: str | None
    termination: str | None


@dataclass(frozen=True)
class TickRecord:
    tick: int
    entrants: dict[str, EntrantTick]
    score: dict[str, float]
    events: tuple[dict[str, Any], ...]
    # Every byte written this tick, in execution order: (address, owner).
    writes: tuple[tuple[int, str | None], ...]
    cpu: dict[str, int]


class _Recorder:
    """A replay sink that also snapshots live entrant capture state."""

    def __init__(self) -> None:
        self.controller: ProcessMatchController | None = None
        self.ticks: list[TickRecord] = []

    def emit(self, record: dict[str, Any]) -> None:
        if "config" in record or record["tick"] == 0:
            return
        controller = self.controller
        assert controller is not None
        writer = controller.vm.writer
        self.ticks.append(
            TickRecord(
                tick=record["tick"],
                entrants={
                    state.agent_id: EntrantTick(
                        alive=state.alive,
                        owned=sum(1 for cell in state.core_cells if writer[cell] == state.agent_id),
                        streak=state.core_zero_streak,
                        onset=state.core_zero_onset_capturer,
                        termination=state.entrant_termination,
                    )
                    for state in controller.states
                },
                score=dict(record["score"]),
                events=tuple(dict(event) for event in record["events"]),
                writes=tuple(
                    ((diff["addr"] + offset) % ARENA, diff["owner"])
                    for diff in record["memory_diffs"]
                    for offset in range(diff["len"])
                ),
                cpu={agent["id"]: agent["cpu_used"] for agent in record["agents"]},
            )
        )

    def close(self) -> None:
        return None


@dataclass(frozen=True)
class Played:
    summary: dict[str, Any]
    ticks: list[TickRecord]
    controller: ProcessMatchController

    def streaks(self, agent_id: str) -> list[int]:
        return [record.entrants[agent_id].streak for record in self.ticks]

    def owned(self, agent_id: str) -> list[int]:
        return [record.entrants[agent_id].owned for record in self.ticks]

    def events(self) -> list[tuple[int, dict[str, Any]]]:
        return [(record.tick, event) for record in self.ticks for event in record.events]


def _play(
    scripts: Mapping[str, Script],
    *,
    max_ticks: int,
    policy: RulesetPolicy = E2,
) -> Played:
    specs = [
        ProcessEntrantSpec(
            agent_id=seat,
            name=f"seat-{seat}",
            processes=[
                ProcessInstance(
                    "p",
                    ProcessRole.GENERALIST,
                    initial_position=ANCHOR[seat],
                    reach=ARENA // 2,
                    quota_share=QUOTA,
                    logic=_scripted(scripts.get(seat, {})),
                )
            ],
            start=CORE[seat],
        )
        for seat in ("A", "B")
    ]
    controller = ProcessMatchController(
        Config(seed=1, arena_size=ARENA, instr_per_tick=QUOTA),
        specs,
        max_ticks,
        ruleset_policy=policy,
    )
    recorder = _Recorder()
    recorder.controller = controller
    summary = controller.run(recorder)
    return Played(summary, recorder.ticks, controller)


def _zero(enemy: str) -> list[AgentAction]:
    """Eight writes: every cell of ``enemy``'s core, ascending."""

    return [_w(cell) for cell in _cells(CORE[enemy])]


def _kill(victim: str, by: str) -> dict[str, Any]:
    return {"type": "kill", "victim": victim, "by": by}


def _outcome(played: Played) -> tuple[str, str, int]:
    return (played.summary["winner"], played.summary["reason"], played.summary["ticks_run"])


# ---------------------------------------------------------------------------
# Sec J.3 semantic tests
# ---------------------------------------------------------------------------


def test_e2_policy_under_test_holds_for_two_ticks() -> None:
    assert E2.capture_hold_ticks == 2


def test_first_zero_evaluation_is_onset_not_capture() -> None:
    played = _play({"A": {1: _zero("B")}}, max_ticks=1)

    (tick1,) = played.ticks
    # Precondition: A's eight writes really took every B core cell this tick.
    assert tick1.writes == tuple((cell, "A") for cell in _cells(CORE["B"]))
    assert tick1.entrants == {
        "A": EntrantTick(alive=True, owned=8, streak=0, onset=None, termination=None),
        "B": EntrantTick(alive=True, owned=0, streak=1, onset="A", termination=None),
    }
    assert tick1.events == ()
    # The capture-threatened entrant is alive, so it scores its alive point.
    assert tick1.score == {"A": 1.0, "B": 1.0}
    assert _outcome(played) == ("tie", "tick_limit", 1)


@pytest.mark.parametrize("restored", [1, 4, 8], ids=["one-cell", "partial-core", "full-core"])
def test_any_positive_ownership_fully_recovers(restored: int) -> None:
    played = _play(
        {
            "A": {1: _zero("B")},
            "B": {2: [_w(cell) for cell in _cells(CORE["B"])[:restored]]},
        },
        max_ticks=2,
    )

    assert played.owned("B") == [0, restored]
    assert played.streaks("B") == [1, 0]
    assert [record.entrants["B"].onset for record in played.ticks] == ["A", None]
    assert all(record.entrants["B"].alive for record in played.ticks)
    assert played.events() == []
    assert _outcome(played) == ("tie", "tick_limit", 2)


def test_completion_is_credited_to_the_onset_capturer() -> None:
    played = _play({"A": {1: _zero("B")}}, max_ticks=5)

    tick1, tick2 = played.ticks
    assert tick1.entrants["B"] == EntrantTick(
        alive=True, owned=0, streak=1, onset="A", termination=None
    )
    # Completion tick: nobody writes anything, and B began the tick already
    # owning zero core cells -- the exact state in which re-attributing from
    # this tick's diffs would find no capturer (review Sec C.5).
    assert tick2.writes == ()
    assert tick2.entrants["B"] == EntrantTick(
        alive=False, owned=0, streak=2, onset="A", termination="core_captured"
    )
    assert tick2.events == (_kill("B", "A"),)
    # +5 kill to the onset capturer only at completion; no alive score for
    # the captured entrant on its completion tick.
    assert [record.score for record in played.ticks] == [
        {"A": 1.0, "B": 1.0},
        {"A": 7.0, "B": 1.0},
    ]
    assert played.controller.statistics["A"]["kills"] == 1
    assert played.controller.statistics["B"]["deaths"] == 1
    assert _outcome(played) == ("A", "last_agent_standing", 2)


def test_interrupted_streak_captures_only_on_the_final_evaluation() -> None:
    # Ownership at successive evaluations: 0, +, 0, +, 0, 0.
    played = _play(
        {
            "A": {1: _zero("B"), 3: [_w(CORE["B"])], 5: [_w(CORE["B"])]},
            "B": {2: [_w(CORE["B"])], 4: [_w(CORE["B"])]},
        },
        max_ticks=10,
    )

    assert played.owned("B") == [0, 1, 0, 1, 0, 0]
    assert played.streaks("B") == [1, 0, 1, 0, 1, 2]
    assert [record.entrants["B"].onset for record in played.ticks] == [
        "A", None, "A", None, "A", "A",
    ]
    assert [record.entrants["B"].alive for record in played.ticks] == [
        True, True, True, True, True, False,
    ]
    assert played.events() == [(6, _kill("B", "A"))]
    assert _outcome(played) == ("A", "last_agent_standing", 6)


def test_zero_and_recovery_within_one_tick_is_invisible() -> None:
    # Tick 1 slot order is A,A,B,B,...; A's final chunk precedes B's final
    # chunk, in which B rewrites two of its own cells.
    played = _play(
        {"A": {1: _zero("B")}, "B": {1: [_IDLE] * 6 + [_w(300), _w(301)]}},
        max_ticks=1,
    )

    (tick1,) = played.ticks
    assert tick1.writes == tuple((cell, "A") for cell in _cells(CORE["B"])) + (
        (300, "B"),
        (301, "B"),
    )
    # Precondition: B's core really was at zero mid-tick.
    owners = dict.fromkeys(_cells(CORE["B"]), "B")
    running = []
    for address, owner in tick1.writes:
        owners[address] = owner
        running.append(sum(1 for value in owners.values() if value == "B"))
    assert min(running) == 0 and running[-1] == 2
    assert tick1.entrants["B"] == EntrantTick(
        alive=True, owned=2, streak=0, onset=None, termination=None
    )
    assert tick1.events == ()


@pytest.mark.parametrize("seat_a_writes", ["ascending", "descending"])
def test_simultaneous_completion_is_all_agents_dead_tie_in_either_seat_order(
    seat_a_writes: str,
) -> None:
    # Two behaviorally different attackers (different write orders), each
    # zeroing the other's core on tick 1; swapping which one sits in Seat A
    # must not change who completes.
    def attack(enemy: str, direction: str) -> list[AgentAction]:
        cells = _cells(CORE[enemy])
        return [_w(cell) for cell in (cells if direction == "ascending" else cells[::-1])]

    other = "descending" if seat_a_writes == "ascending" else "ascending"
    played = _play(
        {"A": {1: attack("B", seat_a_writes)}, "B": {1: attack("A", other)}},
        max_ticks=5,
    )

    tick1, tick2 = played.ticks
    assert tick1.entrants == {
        "A": EntrantTick(alive=True, owned=0, streak=1, onset="B", termination=None),
        "B": EntrantTick(alive=True, owned=0, streak=1, onset="A", termination=None),
    }
    assert tick2.entrants == {
        "A": EntrantTick(alive=False, owned=0, streak=2, onset="B", termination="core_captured"),
        "B": EntrantTick(alive=False, owned=0, streak=2, onset="A", termination="core_captured"),
    }
    # Both completions in one evaluation; events in seat order.
    assert tick2.events == (_kill("A", "B"), _kill("B", "A"))
    assert tick2.score == {"A": 6.0, "B": 6.0}
    assert _outcome(played) == ("tie", "all_agents_dead", 2)


def test_completion_set_does_not_depend_on_evaluation_order() -> None:
    # Direct evaluation: two entrants, both one zero-evaluation into a
    # streak, both still at zero. Presenting them in either order completes
    # both; the order only changes the order events are appended.
    def fresh() -> tuple[VM, list[EntrantState]]:
        vm = VM(ARENA)
        states = []
        for seat, enemy in (("A", "B"), ("B", "A")):
            cells = tuple(_cells(CORE[seat]))
            for cell in cells:
                vm._wr8(cell, 1, owner=enemy)
            states.append(
                EntrantState(
                    agent_id=seat,
                    slot=len(states),
                    core_base=CORE[seat],
                    core_size=8,
                    core_cells=cells,
                    core_zero_streak=1,
                    core_zero_onset_capturer=enemy,
                )
            )
        vm.clear_tick_diffs()
        return vm, states

    outcomes = []
    for reverse in (False, True):
        vm, states = fresh()
        ordered = states[::-1] if reverse else states
        events: list[dict[str, Any]] = []
        score = {"A": 0.0, "B": 0.0}
        collector = StatisticsCollector()
        statistics: dict[str, Any] = {}
        for state in states:
            collector.initialize_agent(statistics, state.agent_id)
        apply_core_capture(
            ordered,
            vm,
            {state.agent_id: (None,) * 8 for state in states},
            ScoringPolicy(Config().weights),
            score,
            collector,
            statistics,
            events,
            hold_ticks=2,
        )
        outcomes.append(
            (
                {state.agent_id: (state.alive, state.entrant_termination) for state in states},
                score,
                sorted(event["victim"] for event in events),
            )
        )
        assert [event["victim"] for event in events] == [state.agent_id for state in ordered]
    assert outcomes[0] == outcomes[1] == (
        {"A": (False, "core_captured"), "B": (False, "core_captured")},
        {"A": 5.0, "B": 5.0},
        ["A", "B"],
    )


def test_staggered_completion_leaves_a_zero_core_winner() -> None:
    played = _play(
        {"B": {1: _zero("A")}, "A": {2: _zero("B")}},
        max_ticks=5,
    )

    tick1, tick2 = played.ticks
    assert tick1.entrants["A"] == EntrantTick(
        alive=True, owned=0, streak=1, onset="B", termination=None
    )
    assert tick2.entrants == {
        "A": EntrantTick(alive=False, owned=0, streak=2, onset="B", termination="core_captured"),
        # B survives while itself at zero: an onset, not a capture.
        "B": EntrantTick(alive=True, owned=0, streak=1, onset="A", termination=None),
    }
    assert tick2.events == (_kill("A", "B"),)
    assert tick2.score == {"A": 1.0, "B": 7.0}
    assert _outcome(played) == ("B", "last_agent_standing", 2)


def test_forfeit_during_a_streak_is_a_forfeit_not_a_capture() -> None:
    played = _play({"A": {1: _zero("B")}, "B": {2: [_FORFEIT]}}, max_ticks=5)

    tick1, tick2 = played.ticks
    assert tick1.entrants["B"].streak == 1
    # B forfeits on its first tick-2 callback; the streak it carried is
    # never evaluated again.
    assert tick2.entrants["B"] == EntrantTick(
        alive=False, owned=0, streak=1, onset="A", termination="forfeit"
    )
    assert [event["type"] for event in tick2.events] == ["forfeit"]
    assert tick2.events[0]["victim"] == "B"
    assert tick2.events[0]["tick"] == 2
    assert tick2.score == {"A": 2.0, "B": 1.0}
    assert played.controller.statistics["A"]["kills"] == 0
    assert _outcome(played) == ("A", "last_agent_standing", 2)


def test_opponent_forfeit_while_self_completes_is_all_agents_dead_tie() -> None:
    # A is zeroed by B on tick 1 (onset). On tick 2 B forfeits at its first
    # callback and A, still at zero, completes: both are dead (review Sec
    # C.3). Kill credit follows Sec C.2 literally -- the onset capturer B,
    # even though it has since forfeited -- exactly as V4 already credits a
    # capturer that forfeits later in the same capture tick.
    played = _play({"B": {1: _zero("A"), 2: [_FORFEIT]}}, max_ticks=5)

    tick1, tick2 = played.ticks
    assert tick1.entrants["A"].streak == 1
    assert tick2.entrants == {
        "A": EntrantTick(alive=False, owned=0, streak=2, onset="B", termination="core_captured"),
        "B": EntrantTick(alive=False, owned=8, streak=0, onset=None, termination="forfeit"),
    }
    assert [(event["type"], event["victim"]) for event in tick2.events] == [
        ("forfeit", "B"),
        ("kill", "A"),
    ]
    assert tick2.events[1] == _kill("A", "B")
    assert tick2.score == {"A": 1.0, "B": 6.0}
    assert _outcome(played) == ("tie", "all_agents_dead", 2)


def test_v4_already_credits_a_capturer_that_forfeits_later_in_the_capture_tick() -> None:
    # The V4 precedent the E2 case above is consistent with: B takes A's
    # last four core cells on tick 2 and then forfeits in the same tick.
    # V4 captures A at that tick's end and credits B, although B is dead.
    played = _play(
        {"B": {1: _zero("A")[:4], 2: [*_zero("A")[4:], _FORFEIT]}},
        max_ticks=5,
        policy=RULESET_V4,
    )

    tick1, tick2 = played.ticks
    assert tick1.entrants["A"].owned == 4
    assert tick2.writes == tuple((cell, "B") for cell in _cells(CORE["A"])[4:])
    assert [(event["type"], event["victim"]) for event in tick2.events] == [
        ("forfeit", "B"),
        ("kill", "A"),
    ]
    assert tick2.events[1] == _kill("A", "B")
    assert tick2.score == {"A": 1.0, "B": 6.0}
    assert _outcome(played) == ("tie", "all_agents_dead", 2)


def test_tick_limit_at_streak_one_survives_and_score_decides() -> None:
    # B paints 56 non-core cells over ticks 1-7 (64 owned: one territory
    # point on tick 7); A zeroes B's core on the final tick 8. B ends the
    # match alive, capture-threatened, and ahead on score -- no extra rule
    # penalizes it (review Sec C.6).
    paint = list(range(360, 416))
    played = _play(
        {
            "B": {tick: [_w(cell) for cell in paint[(tick - 1) * 8 : tick * 8]] for tick in range(1, 8)},
            "A": {8: _zero("B")},
        },
        max_ticks=8,
    )

    assert played.streaks("B") == [0, 0, 0, 0, 0, 0, 0, 1]
    assert played.ticks[-1].entrants["B"] == EntrantTick(
        alive=True, owned=0, streak=1, onset="A", termination=None
    )
    assert played.events() == []
    assert played.ticks[-1].score == {"A": 8.0, "B": 9.0}
    assert _outcome(played) == ("B", "tick_limit", 8)


@pytest.mark.parametrize(
    "policy", [RULESET_V4, RULESET_V6_RESEARCH_SCALE], ids=lambda policy: policy.ruleset_id
)
def test_k1_capture_is_immediate_and_attributed_from_its_own_tick(policy: RulesetPolicy) -> None:
    assert policy.capture_hold_ticks == 1
    played = _play({"A": {1: _zero("B")}}, max_ticks=5, policy=policy)

    (tick1,) = played.ticks
    assert tick1.entrants["B"] == EntrantTick(
        alive=False, owned=0, streak=1, onset="A", termination="core_captured"
    )
    assert tick1.events == (_kill("B", "A"),)
    assert tick1.score == {"A": 6.0, "B": 0.0}
    assert _outcome(played) == ("A", "last_agent_standing", 1)


@pytest.mark.parametrize("hold", [1, 2, 3])
def test_hold_length_is_generic_not_special_cased(hold: int) -> None:
    # The runtime reads only ``capture_hold_ticks``; an unregistered test
    # policy with K=3 completes on the third consecutive zero evaluation.
    policy = RulesetPolicy(
        ruleset_id=f"test-only-capture-hold-{hold}",
        scheduler_mode="chunked",
        scheduler_chunk_size=2,
        scheduler_rotate_start=True,
        core_placement="seeded",
        process_selection="round_robin",
        capture_hold_ticks=hold,
    )
    played = _play({"A": {1: _zero("B")}}, max_ticks=10, policy=policy)

    assert played.streaks("B") == list(range(1, hold + 1))
    assert played.events() == [(hold, _kill("B", "A"))]
    assert _outcome(played) == ("A", "last_agent_standing", hold)


# ---------------------------------------------------------------------------
# Sec J.4 mechanic characterizations: the review's Sec D traces, end to end
# ---------------------------------------------------------------------------

SEED = 42

_AGENT_PRELUDE = """\
from battle_engine.agent_api import ActionKindV2, AgentAction, ProcessDeclaration


def write(address):
    return AgentAction(ActionKindV2.WRITE, operand=address, value=1)


def idle(observation):
    return AgentAction(ActionKindV2.READ, operand=observation.own_core_base)
"""

# Sec D agent brains (review Appendix P), each with global reach.
AGENT_SOURCES = {
    # CompetentGlobalSniperProbe (test_v4_exploit_characterization.py).
    "probe": """
class Agent:
    def reset(self, context):
        self.context = context
        self.step = 0

    def declare_processes(self):
        return [ProcessDeclaration(id="sniper", reach=self.context.arena_size // 2, share=1.0)]

    def act(self, obs):
        if not obs.visible_enemy_anchor_addresses:
            return idle(obs)
        target = (obs.visible_enemy_anchor_addresses[0] + self.step) % self.context.arena_size
        self.step = (self.step + 1) % 8
        return write(target)
""",
    # Global Sniper: each visible anchor once per tick, then every enemy
    # core cell not yet written this tick. Never repairs.
    "sniper": """
class Agent:
    def reset(self, context):
        self.context = context
        self.enemy_core = None
        self.tick = None
        self.done = set()

    def declare_processes(self):
        return [ProcessDeclaration(id="sniper", reach=self.context.arena_size // 2, share=1.0)]

    def act(self, obs):
        anchors = obs.visible_enemy_anchor_addresses
        if self.enemy_core is None and anchors:
            self.enemy_core = anchors[0]
        if obs.current_tick != self.tick:
            self.tick = obs.current_tick
            self.done = set()
        targets = list(anchors)
        if self.enemy_core is not None:
            targets += [(self.enemy_core + i) % self.context.arena_size for i in range(8)]
        for target in targets:
            if target not in self.done:
                self.done.add(target)
                return write(target)
        return idle(obs)
""",
    # Pure repair guard: rewrite its own core cells, cycling. Never disrupts.
    "repair_guard": """
class Agent:
    def reset(self, context):
        self.context = context
        self.cursor = 0

    def declare_processes(self):
        return [ProcessDeclaration(id="guard", reach=self.context.arena_size // 2, share=1.0)]

    def act(self, obs):
        target = (obs.own_core_base + self.cursor) % self.context.arena_size
        self.cursor = (self.cursor + 1) % 8
        return write(target)
""",
    # Disrupt-first guard: each visible enemy anchor once per tick, then
    # its own core cells not yet written this tick.
    "disrupt_guard": """
class Agent:
    def reset(self, context):
        self.context = context
        self.tick = None
        self.done = set()

    def declare_processes(self):
        return [ProcessDeclaration(id="guard", reach=self.context.arena_size // 2, share=1.0)]

    def act(self, obs):
        if obs.current_tick != self.tick:
            self.tick = obs.current_tick
            self.done = set()
        own = [(obs.own_core_base + i) % self.context.arena_size for i in range(8)]
        for target in list(obs.visible_enemy_anchor_addresses) + own:
            if target not in self.done:
                self.done.add(target)
                return write(target)
        return idle(obs)
""",
    # Spread sniper: three processes; on tick 1 p1/p2 MOVE +40/-40 once
    # (fixed offsets, as in the review's probe), otherwise every process
    # disrupts each visible anchor once per tick, then attacks the core.
    "spread_sniper": """
class Agent:
    def reset(self, context):
        self.context = context
        self.enemy_core = None
        self.tick = None
        self.done = set()
        self.moved = set()

    def declare_processes(self):
        reach = self.context.arena_size // 2
        return [
            ProcessDeclaration(id="p0", reach=reach, share=0.375),
            ProcessDeclaration(id="p1", reach=reach, share=0.375),
            ProcessDeclaration(id="p2", reach=reach, share=0.25),
        ]

    def act(self, obs):
        anchors = obs.visible_enemy_anchor_addresses
        if self.enemy_core is None and anchors:
            self.enemy_core = anchors[0]
        if obs.current_tick != self.tick:
            self.tick = obs.current_tick
            self.done = set()
        offset = {"p1": 40, "p2": -40}.get(obs.self_process_id)
        if offset is not None and obs.self_process_id not in self.moved:
            self.moved.add(obs.self_process_id)
            return AgentAction(ActionKindV2.MOVE, operand=offset)
        targets = list(anchors)
        if self.enemy_core is not None:
            targets += [(self.enemy_core + i) % self.context.arena_size for i in range(8)]
        for target in targets:
            if target not in self.done:
                self.done.add(target)
                return write(target)
        return idle(obs)
""",
}


def _install(root: Path, name: str) -> None:
    agent_dir = root / "agents" / name
    if agent_dir.exists():
        return
    agent_dir.mkdir(parents=True)
    (agent_dir / "agent.yaml").write_bytes(
        (
            f'{{"name": "{name}", "kind": "python", "api_version": 2, '
            '"entrypoint": "agent.py:create_agent", "version": "1.0.0"}\n'
        ).encode()
    )
    source = _AGENT_PRELUDE + textwrap.dedent(AGENT_SOURCES[name.split("__")[0]])
    source += "\n\ndef create_agent():\n    return Agent()\n"
    (agent_dir / "agent.py").write_bytes(source.encode())


@dataclass(frozen=True)
class ReplayTick:
    tick: int
    owned: dict[str, int]
    alive: dict[str, bool]
    cpu: dict[str, int]
    writes: tuple[tuple[int, str | None], ...]
    events: tuple[tuple[str, str, str | None], ...]
    anchors: dict[tuple[str, str], int]


@dataclass(frozen=True)
class ReplayRun:
    replay_path: Path
    cores: dict[str, int]
    ticks: list[ReplayTick]
    result: MatchResult

    def owned(self, seat: str) -> list[int]:
        return [tick.owned[seat] for tick in self.ticks]

    def streaks(self, seat: str) -> list[int]:
        """Capture progress derived from replay ownership (review Sec K)."""

        streak, out = 0, []
        for tick in self.ticks:
            streak = streak + 1 if tick.owned[seat] == 0 else 0
            out.append(streak)
        return out


def _run_e2(root: Path, seat_a: str, seat_b: str, *, max_ticks: int) -> ReplayRun:
    for name in (seat_a, seat_b):
        _install(root, name)
    starts = resolve_direct_match_starts(
        ruleset_id=BYTEFRAY_RULESET_V6_RESEARCH_CAPTURE_HOLD_K2_ID,
        arena_size=ARENA,
        entrant_count=2,
        supplied_starts=[None, None],
        seed=SEED,
    )
    replay_path = root / "runs" / f"{seat_a}-vs-{seat_b}" / "replay.jsonl"
    replay_path.parent.mkdir(parents=True)
    NativeMatchService().run(
        MatchRequest(
            config=Config(seed=SEED, arena_size=ARENA, instr_per_tick=QUOTA),
            entrants=(
                MatchEntrant.python("A", seat_a, starts[0], resolve_agent(root, seat_a)),
                MatchEntrant.python("B", seat_b, starts[1], resolve_agent(root, seat_b)),
            ),
            max_ticks=max_ticks,
            replay_path=replay_path,
            verbose=False,
            ruleset_id=BYTEFRAY_RULESET_V6_RESEARCH_CAPTURE_HOLD_K2_ID,
        )
    )
    cores = {"A": starts[0], "B": starts[1]}
    owners: dict[int, str | None] = {}
    ticks: list[ReplayTick] = []
    result: MatchResult | None = None
    for record in iter_replay(replay_path):
        if isinstance(record, ReplayHeader):
            assert record.ruleset_id == BYTEFRAY_RULESET_V6_RESEARCH_CAPTURE_HOLD_K2_ID
        elif isinstance(record, TickSnapshot):
            writes = tuple(
                ((diff.address + offset) % ARENA, diff.owner)
                for diff in record.memory_diffs
                for offset in range(diff.length)
            )
            for address, owner in writes:
                owners[address] = owner
            if record.tick == 0:
                continue
            ticks.append(
                ReplayTick(
                    tick=record.tick,
                    owned={
                        seat: sum(
                            1
                            for offset in range(8)
                            if owners.get((base + offset) % ARENA) == seat
                        )
                        for seat, base in cores.items()
                    },
                    alive={agent.agent_id: agent.alive for agent in record.agents},
                    cpu={agent.agent_id: agent.cpu_used for agent in record.agents},
                    writes=writes,
                    events=tuple(
                        (event.event_type, event.victim, event.killer)
                        if isinstance(event, KillDeathEvent)
                        else (event.event_type, event.victim, None)
                        for event in record.events
                        if isinstance(event, (KillDeathEvent, RuntimeEvent))
                    ),
                    anchors={
                        (process.entrant_id, process.process_id): process.anchor
                        for process in record.processes
                    },
                )
            )
        elif isinstance(record, MatchResult):
            result = record
    assert result is not None
    return ReplayRun(replay_path, cores, ticks, result)


def _core_writes(base: int, owner: str) -> tuple[tuple[int, str], ...]:
    return tuple(((base + offset) % ARENA, owner) for offset in range(8))


def test_characterization_geometry_is_the_reviewed_seed_42_layout() -> None:
    # Review Sec D.1: A's core at 485, B's at 203.
    assert resolve_direct_match_starts(
        ruleset_id=BYTEFRAY_RULESET_V6_RESEARCH_CAPTURE_HOLD_K2_ID,
        arena_size=ARENA,
        entrant_count=2,
        supplied_starts=[None, None],
        seed=SEED,
    ) == (485, 203)


def test_d3_probe_mirror_is_delayed_to_tick_2_and_won_at_zero_core(tmp_path: Path) -> None:
    run = _run_e2(tmp_path, "probe", "probe__twin", max_ticks=200)

    assert [tick.tick for tick in run.ticks] == [1, 2]
    tick1, tick2 = run.ticks
    # Tick 1 is exactly V4's forced line: A's first write disrupts B, whose
    # eight slot offers are all forfeited.
    assert tick1.writes == _core_writes(203, "A")
    assert tick1.cpu == {"A": 8, "B": 0}
    assert tick1.events == ()
    # Tick 2: B moves first, with its disruption expired, and strikes A's
    # core; now A's eight offers are all forfeited.
    assert tick2.writes == _core_writes(485, "B")
    assert tick2.cpu == {"A": 0, "B": 8}
    assert run.owned("A") == [8, 0]
    assert run.owned("B") == [0, 0]
    assert run.streaks("A") == [0, 1]
    assert run.streaks("B") == [1, 2]
    assert tick2.alive == {"A": True, "B": False}
    assert tick2.events == (("kill", "B", "A"),)
    assert (run.result.winner, run.result.ticks, run.result.termination_reason) == (
        "A",
        2,
        "last_agent_standing",
    )
    assert dict(run.result.score) == {"A": 7.0, "B": 1.0}


def test_d4_sniper_vs_pure_repair_guard_window_is_nominal(tmp_path: Path) -> None:
    run = _run_e2(tmp_path, "sniper", "repair_guard", max_ticks=200)

    tick1, tick2 = run.ticks
    assert tick1.writes == _core_writes(203, "A")
    assert tick1.cpu == {"A": 8, "B": 0}
    # B's two first-mover repairs land, then A retakes both -- the retake of
    # 203 disrupts B, whose remaining six offers are forfeited.
    assert tick2.writes == ((203, "B"), (204, "B")) + _core_writes(203, "A")
    assert tick2.cpu == {"A": 8, "B": 2}
    assert run.owned("B") == [0, 0]
    assert tick2.events == (("kill", "B", "A"),)
    assert (run.result.winner, run.result.ticks, run.result.termination_reason) == (
        "A",
        2,
        "last_agent_standing",
    )


def test_d5_sniper_vs_disrupt_guard_alternates_with_scheduler_parity(tmp_path: Path) -> None:
    run = _run_e2(tmp_path, "sniper", "disrupt_guard", max_ticks=8)

    assert [tick.tick for tick in run.ticks] == list(range(1, 9))
    # B is at zero on every attacker-first (odd) tick and recovered on every
    # defender-first (even) tick.
    assert run.owned("B") == [0, 7, 0, 7, 0, 7, 0, 7]
    assert run.streaks("B") == [1, 0, 1, 0, 1, 0, 1, 0]
    assert all(tick.alive == {"A": True, "B": True} for tick in run.ticks)
    assert all(tick.events == () for tick in run.ticks)
    for tick in run.ticks:
        if tick.tick % 2:
            assert tick.cpu == {"A": 8, "B": 0}
            assert tick.writes == _core_writes(203, "A")
        else:
            assert tick.cpu == {"A": 0, "B": 8}
            # Disrupt A's single location first, then repair seven cells.
            assert tick.writes == ((485, "B"),) + _core_writes(203, "B")[:7]
    assert (run.result.winner, run.result.termination_reason) == (None, "tick_limit")


def test_d6_spread_sniper_vs_disrupt_guard_closes_the_window(tmp_path: Path) -> None:
    run = _run_e2(tmp_path, "spread_sniper", "disrupt_guard", max_ticks=200)

    tick1, tick2, tick3 = run.ticks
    # Tick 1: p0 disrupts B, p1/p2 spread to 13 and 445, then five core
    # writes -- B keeps two cells, so there is no onset.
    assert tick1.writes == tuple((cell, "A") for cell in range(203, 209))
    assert {pid: tick1.anchors[("A", pid)] for pid in ("p0", "p1", "p2")} == {
        "p0": 485,
        "p1": 13,
        "p2": 445,
    }
    assert tick1.cpu == {"A": 8, "B": 0}
    # Tick 2 (B first): B's two-action chunk disrupts two of A's three
    # locations; A's surviving p0 retakes the whole core and disrupts B.
    assert tick2.writes == ((13, "B"), (445, "B")) + _core_writes(203, "A")
    assert tick2.cpu == {"A": 8, "B": 2}
    assert run.owned("B") == [2, 0, 0]
    assert run.streaks("B") == [0, 1, 2]
    assert tick2.events == ()
    # Tick 3 (A first): B never acts, and completes.
    assert tick3.cpu == {"A": 8, "B": 0}
    assert tick3.events == (("kill", "B", "A"),)
    assert (run.result.winner, run.result.ticks, run.result.termination_reason) == (
        "A",
        3,
        "last_agent_standing",
    )
