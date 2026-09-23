"""HD-5: the replay-derived E2 capture analyzer (tools/research/v6/e2/capture_analyzer.py).

Every test runs real matches through ``NativeMatchService`` and analyzes the
canonical replay. Preconditions are asserted from the replay itself (the
engine's own events, ticks and diffs) before the analyzer's telemetry is
asserted by value. Scripted agents are test-only; the Sec D mechanics use the
tracked E2 research fixtures at seed 42, arena 512 (review Sec D.1 geometry:
Seat A's core at 485, Seat B's at 203).
"""

from __future__ import annotations

import json
import textwrap
from pathlib import Path
from typing import Any

import pytest
from battle_engine.agents import resolve_agent
from battle_engine.config import Config
from battle_engine.match_service import MatchEntrant, MatchRequest, NativeMatchService
from battle_engine.placement import resolve_direct_match_starts
from battle_engine.replay import KillDeathEvent, MatchResult, TickSnapshot, iter_replay
from battle_engine.ruleset_policy import (
    BYTEFRAY_RULESET_V4_ID,
    BYTEFRAY_RULESET_V6_RESEARCH_CAPTURE_HOLD_K2_ID,
)

from tools.research.v6.e2.capture_analyzer import analyze_replay, first_mover_seat
from tools.research.v6.e2.matrix import CORE_INFERRING_AGENTS
from tools.research.v6.experiment_harness import E2_FIXTURE_SOURCE_DIR, prepare_benchmark_data_root

E2_ID = BYTEFRAY_RULESET_V6_RESEARCH_CAPTURE_HOLD_K2_ID
SEED = 42
A_CORE, B_CORE = 485, 203

_PRELUDE = """\
from battle_engine.agent_api import ActionKindV2, AgentAction, ProcessDeclaration


def write(address):
    return AgentAction(ActionKindV2.WRITE, operand=address, value=1)


def idle(obs):
    return AgentAction(ActionKindV2.READ, operand=obs.own_core_base)


class Scripted:
    def reset(self, context):
        self.arena = context.arena_size
        self.enemy = None
        self.tick = None
        self.index = 0

    def declare_processes(self):
        return [ProcessDeclaration(id="p", reach=self.arena // 2, share=1.0)]

    def act(self, obs):
        if self.enemy is None and obs.visible_enemy_anchor_addresses:
            self.enemy = obs.visible_enemy_anchor_addresses[0]
        if obs.current_tick != self.tick:
            self.tick, self.index = obs.current_tick, 0
        index, self.index = self.index, self.index + 1
        return self.step(obs, obs.current_tick, index) or idle(obs)
"""

SCRIPTS = {
    # Tick 1: all eight enemy core cells. Ticks 3 and 5: retake the enemy core base.
    "streak_attacker": """
class Agent(Scripted):
    def step(self, obs, tick, index):
        if tick == 1 and index < 8:
            return write((self.enemy + index) % self.arena)
        if tick in (3, 5) and index == 0:
            return write(self.enemy)
        return None
""",
    # Ticks 2 and 4: rewrite exactly one own core cell (its base). Tick 6: nothing.
    "streak_victim": """
class Agent(Scripted):
    def step(self, obs, tick, index):
        if tick in (2, 4) and index == 0:
            return write(obs.own_core_base)
        return None
""",
    # Tick 1: the enemy core base last, so the victim is disrupted only at the very end.
    "transit_attacker": """
class Agent(Scripted):
    def step(self, obs, tick, index):
        if tick == 1 and index < 8:
            return write((self.enemy + (index + 1) % 8) % self.arena)
        return None
""",
    # Tick 1: step off the core first, then rewrite one core cell in the final chunk.
    "transit_victim": """
class Agent(Scripted):
    def step(self, obs, tick, index):
        if tick == 1 and index == 0:
            return AgentAction(ActionKindV2.MOVE, operand=40)
        if tick == 1 and index == 6:
            return write(obs.own_core_base + 1)
        return None
""",
}


def _install_scripts(root: Path) -> None:
    for name, body in SCRIPTS.items():
        agent_dir = root / "agents" / name
        agent_dir.mkdir(parents=True)
        (agent_dir / "agent.yaml").write_bytes(
            (
                f'{{"name": "{name}", "kind": "python", "api_version": 2, '
                '"entrypoint": "agent.py:create_agent", "version": "1.0.0"}\n'
            ).encode()
        )
        source = _PRELUDE + textwrap.dedent(body) + "\n\ndef create_agent():\n    return Agent()\n"
        (agent_dir / "agent.py").write_bytes(source.encode())


@pytest.fixture(scope="module")
def data_root(tmp_path_factory: pytest.TempPathFactory) -> Path:
    root = tmp_path_factory.mktemp("e2-capture")
    names = sorted(p.name for p in E2_FIXTURE_SOURCE_DIR.iterdir() if (p / "agent.yaml").is_file())
    prepare_benchmark_data_root(root, names)
    _install_scripts(root)
    return root


def run(root: Path, seat_a: str, seat_b: str, *, ruleset_id: str = E2_ID, max_ticks: int = 200) -> Path:
    starts = resolve_direct_match_starts(
        ruleset_id=ruleset_id, arena_size=512, entrant_count=2, supplied_starts=[None, None], seed=SEED
    )
    assert starts == (A_CORE, B_CORE)
    replay = root / "runs" / ruleset_id / f"{seat_a}-vs-{seat_b}-{max_ticks}" / "replay.jsonl"
    replay.parent.mkdir(parents=True)
    NativeMatchService().run(
        MatchRequest(
            config=Config(seed=SEED, arena_size=512, instr_per_tick=8),
            entrants=(
                MatchEntrant.python("A", seat_a, starts[0], resolve_agent(root, seat_a)),
                MatchEntrant.python("B", seat_b, starts[1], resolve_agent(root, seat_b)),
            ),
            max_ticks=max_ticks,
            replay_path=replay,
            verbose=False,
            ruleset_id=ruleset_id,
        )
    )
    return replay


def engine_record(replay: Path) -> tuple[MatchResult, list[tuple[int, str, str, str | None]]]:
    """The engine's own result and capture events, straight from the replay."""
    result: MatchResult | None = None
    events: list[tuple[int, str, str, str | None]] = []
    for record in iter_replay(replay):
        if isinstance(record, TickSnapshot):
            events += [
                (record.tick, e.event_type, e.victim, e.killer)
                for e in record.events
                if isinstance(e, KillDeathEvent)
            ]
        elif isinstance(record, MatchResult):
            result = record
    assert result is not None
    return result, events


def test_first_mover_parity_follows_the_rotating_chunked_scheduler() -> None:
    assert [first_mover_seat(t, 2, True) for t in range(1, 7)] == [0, 1, 0, 1, 0, 1]
    assert [first_mover_seat(t, 2, False) for t in range(1, 4)] == [0, 0, 0]


def test_scripted_interrupted_streak_counts_onsets_recoveries_and_one_completion(data_root: Path) -> None:
    replay = run(data_root, "streak_attacker", "streak_victim")
    result, events = engine_record(replay)
    # Precondition from the engine: B is captured at tick 6, credited to A.
    assert (result.winner, result.ticks, result.termination_reason) == ("A", 6, "last_agent_standing")
    assert events == [(6, "kill", "B", "A")]

    telemetry = analyze_replay(replay)
    victim = telemetry["entrants"]["B"]
    # Ownership at successive evaluations: 0, +, 0, +, 0, 0.
    assert victim["onset_ticks"] == [1, 3, 5]
    assert victim["recovery_ticks"] == [2, 4]
    assert victim["completion_tick"] == 6
    assert (victim["onsets"], victim["recoveries"], victim["completions"]) == (3, 2, 1)
    assert victim["zero_core_ticks"] == [1, 3, 5, 6]
    assert victim["max_streak"] == 2
    assert victim["evaluations"] == 6
    # Ticks 1, 3, 5 are Seat-A-first (the opponent's); tick 6 is B's own.
    assert (victim["zero_ticks_opponent_first"], victim["zero_ticks_own_first"]) == (3, 1)
    assert victim["phase_lock"] == 0.75
    assert (victim["onsets_opponent_first"], victim["onsets_own_first"]) == (3, 0)
    assert victim["recovery_rate"] == round(2 / 3, 6)
    assert victim["onset_capturers"] == ["A", "A", "A"]
    assert (victim["termination"], victim["alive_at_end"]) == ("core_captured", False)
    attacker = telemetry["entrants"]["A"]
    assert (attacker["onsets"], attacker["zero_core_ticks"], attacker["final_owned"]) == (0, [], 8)
    # Never at zero, so never recovering: a positive evaluation is a
    # recovery only directly after a zero streak.
    assert (attacker["recovery_ticks"], attacker["recovery_rate"], attacker["evaluations"]) == ([], None, 6)
    assert telemetry["hold_ticks"] == 2
    assert telemetry["attributions"] == [
        {
            "victim": "B",
            "tick": 6,
            "event": "kill",
            "event_killer": "A",
            "onset_capturer": "A",
            "attributed": True,
            "matches_onset": True,
        }
    ]
    assert telemetry["consistent_with_engine"] is True
    assert telemetry["winner_at_zero_core"] is False


def test_same_script_under_v4_is_an_immediate_k1_capture(data_root: Path) -> None:
    replay = run(data_root, "streak_attacker", "streak_victim", ruleset_id=BYTEFRAY_RULESET_V4_ID)
    result, events = engine_record(replay)
    assert (result.winner, result.ticks) == ("A", 1)
    assert events == [(1, "kill", "B", "A")]
    victim = analyze_replay(replay)["entrants"]["B"]
    assert (victim["onset_ticks"], victim["completion_tick"], victim["zero_core_ticks"]) == ([1], 1, [1])
    assert analyze_replay(replay)["hold_ticks"] == 1


def test_zero_core_within_a_tick_is_not_an_onset(data_root: Path) -> None:
    replay = run(data_root, "transit_attacker", "transit_victim", max_ticks=1)
    (tick1,) = [r for r in iter_replay(replay) if isinstance(r, TickSnapshot) and r.tick == 1]
    writes = [
        ((diff.address + offset) % 512, diff.owner)
        for diff in tick1.memory_diffs
        for offset in range(diff.length)
    ]
    # Precondition: B's core really reached zero mid-tick, and ended the tick owning one cell.
    owners = dict.fromkeys(range(B_CORE, B_CORE + 8), "B")
    running = []
    for address, owner in writes:
        if address in owners:
            owners[address] = owner
            running.append(sum(1 for value in owners.values() if value == "B"))
    assert min(running) == 0 and running[-1] == 1

    victim = analyze_replay(replay)["entrants"]["B"]
    assert (victim["onsets"], victim["zero_core_ticks"], victim["final_owned"]) == (0, [], 1)
    assert victim["recovery_ticks"] == []


def test_d3_probe_mirror_zero_core_winner(data_root: Path) -> None:
    replay = run(data_root, "v4_probe", "v4_probe_twin")
    result, events = engine_record(replay)
    assert (result.winner, result.ticks) == ("A", 2) and events == [(2, "kill", "B", "A")]
    telemetry = analyze_replay(replay)
    a, b = telemetry["entrants"]["A"], telemetry["entrants"]["B"]
    assert (b["onset_ticks"], b["completion_tick"], b["zero_core_ticks"]) == ([1], 2, [1, 2])
    assert (a["onset_ticks"], a["zero_core_ticks"], a["final_owned"]) == ([2], [2], 0)
    # Each onset fell on the opponent's first-mover tick.
    assert (a["onsets_opponent_first"], b["onsets_opponent_first"]) == (1, 1)
    assert a["capture_threatened_at_end"] is True and a["alive_at_end"] is True
    assert telemetry["winner_at_zero_core"] is True
    assert telemetry["all_completions_attributed"] and telemetry["attribution_matches_onset"]
    assert telemetry["consistent_with_engine"] is True


def test_d4_sniper_vs_pure_repair_guard_has_no_recovery(data_root: Path) -> None:
    replay = run(data_root, "e2_sniper", "e2_repair_guard")
    result, _ = engine_record(replay)
    assert (result.winner, result.ticks) == ("A", 2)
    b = analyze_replay(replay)["entrants"]["B"]
    assert (b["onset_ticks"], b["recovery_ticks"], b["completion_tick"]) == ([1], [], 2)


def test_d5_sniper_vs_disrupt_guard_alternation_is_fully_phase_locked(data_root: Path) -> None:
    replay = run(data_root, "e2_sniper", "e2_disrupt_guard", max_ticks=8)
    result, events = engine_record(replay)
    assert (result.winner, result.termination_reason, events) == (None, "tick_limit", [])
    telemetry = analyze_replay(replay, names_inferring_core=CORE_INFERRING_AGENTS)
    b = telemetry["entrants"]["B"]
    assert b["onset_ticks"] == b["zero_core_ticks"] == [1, 3, 5, 7]
    assert b["recovery_ticks"] == [2, 4, 6, 8]
    assert (b["completions"], b["max_streak"], b["phase_lock"]) == (0, 1, 1.0)
    assert b["capture_threatened_at_end"] is False
    a = telemetry["entrants"]["A"]
    assert (a["zero_core_ticks"], a["onset_ticks"], a["recovery_ticks"]) == ([], [], [])
    assert telemetry["completions"] == 0 and telemetry["attributions"] == []


def test_d6_spread_sniper_onset_on_the_defenders_own_first_mover_tick(data_root: Path) -> None:
    replay = run(data_root, "e2_spread_sniper", "e2_disrupt_guard")
    result, events = engine_record(replay)
    assert (result.winner, result.ticks) == ("A", 3) and events == [(3, "kill", "B", "A")]
    telemetry = analyze_replay(replay)
    a, b = telemetry["entrants"]["A"], telemetry["entrants"]["B"]
    assert a["max_locations"] == 3 and b["max_locations"] == 1
    assert (b["onset_ticks"], b["completion_tick"]) == ([2], 3)
    assert (b["onsets_own_first"], b["onsets_opponent_first"]) == (1, 0)


# ---------------------------------------------------------------------------
# Inferred enemy core base: the audit against the agents' real internal state
# ---------------------------------------------------------------------------

_RECORDER = '''\
import importlib.util
import json
from pathlib import Path

_spec = importlib.util.spec_from_file_location("{module}", r"{source}")
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)
_LOG = Path(r"{log}")


class Recording(_module.Agent):
    def act(self, obs):
        before = self.enemy_core
        action = super().act(obs)
        if before is None and self.enemy_core is not None:
            with _LOG.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps([obs.current_tick, self.enemy_core]) + "\\n")
        return action


def create_agent():
    return Recording()
'''


def _recording_agent(root: Path, fixture: str) -> tuple[str, Path]:
    """A test-only wrapper that logs when the real fixture adopts its enemy core base."""
    name = f"rec_{fixture}"
    agent_dir = root / "agents" / name
    log = root / "logs" / f"{name}.jsonl"
    if not agent_dir.exists():
        agent_dir.mkdir(parents=True)
        log.parent.mkdir(parents=True, exist_ok=True)
        (agent_dir / "agent.yaml").write_bytes(
            (
                f'{{"name": "{name}", "kind": "python", "api_version": 2, '
                '"entrypoint": "agent.py:create_agent", "version": "1.0.0"}\n'
            ).encode()
        )
        source = E2_FIXTURE_SOURCE_DIR / fixture / "agent.py"
        (agent_dir / "agent.py").write_bytes(
            _RECORDER.format(module=f"fixture_{fixture}", source=source, log=log).encode()
        )
    log.write_text("", encoding="utf-8")
    return name, log


@pytest.mark.parametrize(
    ("seat_a", "seat_b", "audited", "expected_status", "expected_log"),
    [
        ("e2_sniper", "e2_greedy_painter", "A", "inferred", [[1, B_CORE]]),
        ("e2_greedy_painter", "e2_sniper", "B", "inferred", [[1, A_CORE]]),
        ("e2_greedy_painter", "e2_counter", "B", "inferred", [[1, A_CORE]]),
        ("e2_spread_sniper", "e2_sniper", "B", "not_inferred", []),
        ("e2_spread_sniper", "e2_min_guard", "B", "not_inferred", []),
        ("e2_disrupt_guard", "e2_spread_defender", "B", "inferred", [[2, A_CORE]]),
    ],
)
def test_core_inference_audit_matches_the_agents_actual_inference(
    data_root: Path,
    seat_a: str,
    seat_b: str,
    audited: str,
    expected_status: str,
    expected_log: list[list[int]],
) -> None:
    fixture = seat_a if audited == "A" else seat_b
    recorder, log = _recording_agent(data_root, fixture)
    names = (recorder, seat_b) if audited == "A" else (seat_a, recorder)
    replay = run(data_root, *names, max_ticks=30)

    actual = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]
    assert actual == expected_log
    telemetry = analyze_replay(replay, names_inferring_core={recorder})
    audit = telemetry["entrants"][audited]["core_inference"]
    assert audit["status"] == expected_status
    if actual:
        ((tick, base),) = actual
        assert (audit["inference_tick"], audit["inferred_base"], audit["correct"]) == (tick, base, True)
        assert audit["enemy_core_base"] == base
    else:
        assert (audit["inferred_base"], audit["correct"]) == (None, None)


def test_core_inference_audit_reports_ambiguity_it_cannot_resolve(data_root: Path) -> None:
    # The spread defender moves twice before Seat B's first callback in
    # tick 1; the replay stores anchors only at tick boundaries, so it cannot
    # show whether B saw one location or three. It must say so -- and every
    # base B could have adopted is still A's true core.
    recorder, log = _recording_agent(data_root, "e2_sniper")
    replay = run(data_root, "e2_spread_defender", recorder, max_ticks=30)
    assert log.read_text(encoding="utf-8") == ""  # the agent itself never inferred
    audit = analyze_replay(replay, names_inferring_core={recorder})["entrants"]["B"]["core_inference"]
    assert audit == {
        "status": "ambiguous",
        "inferred_base": None,
        "inference_tick": 1,
        "possible_bases": [A_CORE],
        "enemy_core_base": A_CORE,
        "correct": True,
    }


def test_analyzer_rejects_a_replay_without_a_ruleset_identity(tmp_path: Path, data_root: Path) -> None:
    replay = run(data_root, "e2_sniper", "e2_repair_guard", max_ticks=3)
    lines = replay.read_text(encoding="utf-8").splitlines()
    header: dict[str, Any] = json.loads(lines[0])
    header.pop("ruleset_id")
    broken = tmp_path / "replay.jsonl"
    broken.write_text("\n".join([json.dumps(header), *lines[1:]]) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="ruleset_id"):
        analyze_replay(broken)
