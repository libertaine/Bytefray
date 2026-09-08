from __future__ import annotations

"""Focused unit tests for Bytefray V5 research analyzer and corpus runner."""

import json
from pathlib import Path

import pytest
from battle_engine.agents import resolve_agent
from battle_engine.config import Config
from battle_engine.match_service import MatchEntrant, MatchRequest, NativeMatchService
from battle_engine.placement import resolve_direct_match_starts
from battle_engine.replay import ReplayFormatError
from battle_engine.ruleset_policy import BYTEFRAY_RULESET_V4_ID

from tools.research.v5.analyzer import analyze_match
from tools.research.v5.corpus_runner import build_corpus_manifest

NOP_AGENT_CODE = """
from battle_engine.agent_api import AgentV2, ObservationV2, AgentAction, ActionKindV2, MatchContextV2, ProcessDeclaration

class NopV2:
    api_version = 2
    def declare_processes(self):
        return [ProcessDeclaration(id="p1", reach=10, share=1.0)]
    def reset(self, context: MatchContextV2):
        pass
    def act(self, obs: ObservationV2) -> AgentAction:
        return AgentAction(ActionKindV2.READ, 0)

def create_agent() -> AgentV2:
    return NopV2()
"""

ACTIVE_AGENT_CODE = """
from battle_engine.agent_api import AgentV2, ObservationV2, AgentAction, ActionKindV2, MatchContextV2, ProcessDeclaration

class ActiveV2:
    api_version = 2
    def declare_processes(self):
        return [ProcessDeclaration(id="p1", reach=30, share=1.0)]
    def reset(self, context: MatchContextV2):
        self.tick = 0
    def act(self, obs: ObservationV2) -> AgentAction:
        self.tick += 1
        # alternate between move and write
        if self.tick % 2 == 0:
            return AgentAction(ActionKindV2.WRITE, operand=obs.self_anchor + 1, value=0x42)
        return AgentAction(ActionKindV2.MOVE, operand=2)

def create_agent() -> AgentV2:
    return ActiveV2()
"""


def _setup_agent(tmp_path: Path, name: str, source: str) -> Path:
    agent_dir = tmp_path / "agents" / name
    agent_dir.mkdir(parents=True, exist_ok=True)
    (agent_dir / "agent.py").write_text(source, encoding="utf-8")
    (agent_dir / "agent.yaml").write_text(
        f"name: {name}\ndescription: Test agent\nversion: '1.0'\napi_version: 2\n",
        encoding="utf-8",
    )
    return agent_dir


def _run_test_match(
    tmp_path: Path,
    agent_a_name: str,
    agent_b_name: str,
    *,
    ticks: int = 10,
    seed: int = 42,
    with_trace: bool = False,
) -> tuple[Path, Path, Path | None]:
    replay_path = tmp_path / f"{agent_a_name}_{agent_b_name}" / "replay.jsonl"
    replay_path.parent.mkdir(parents=True, exist_ok=True)
    trace_path = (replay_path.parent / "trace.jsonl") if with_trace else None

    spec_a = resolve_agent(tmp_path, agent_a_name)
    spec_b = resolve_agent(tmp_path, agent_b_name)

    starts = resolve_direct_match_starts(
        ruleset_id=BYTEFRAY_RULESET_V4_ID,
        arena_size=512,
        entrant_count=2,
        supplied_starts=[None, None],
        seed=seed,
    )
    entrants = (
        MatchEntrant.python("A", agent_a_name, starts[0], spec_a),
        MatchEntrant.python("B", agent_b_name, starts[1], spec_b),
    )
    req = MatchRequest(
        config=Config(seed=seed, arena_size=512, instr_per_tick=8),
        entrants=entrants,
        max_ticks=ticks,
        replay_path=replay_path,
        trace_path=trace_path,
        verbose=False,
        ruleset_id=BYTEFRAY_RULESET_V4_ID,
    )
    res = NativeMatchService().run(req)
    assert res.result_path is not None
    return replay_path, res.result_path, trace_path


def test_analyzer_deterministic_output(tmp_path: Path) -> None:
    _setup_agent(tmp_path, "active_a", ACTIVE_AGENT_CODE)
    _setup_agent(tmp_path, "active_b", ACTIVE_AGENT_CODE)

    replay, result, _ = _run_test_match(tmp_path, "active_a", "active_b", ticks=15)

    m1 = analyze_match(replay, result)
    m2 = analyze_match(replay, result)

    assert json.dumps(m1, sort_keys=True) == json.dumps(m2, sort_keys=True)
    assert m1["arena_size"] == 512
    assert m1["ruleset_id"] == BYTEFRAY_RULESET_V4_ID
    assert m1["actual_ticks"] == 15


def test_analyzer_stable_entrant_ordering(tmp_path: Path) -> None:
    _setup_agent(tmp_path, "ag_one", NOP_AGENT_CODE)
    _setup_agent(tmp_path, "ag_two", ACTIVE_AGENT_CODE)

    replay, result, _ = _run_test_match(tmp_path, "ag_one", "ag_two", ticks=5)
    m = analyze_match(replay, result)

    assert m["entrant_order"] == ("A", "B")
    assert "A" in m["declared_process_count"]
    assert "B" in m["declared_process_count"]


def test_analyzer_replay_without_trace(tmp_path: Path) -> None:
    _setup_agent(tmp_path, "nop_a", NOP_AGENT_CODE)
    _setup_agent(tmp_path, "nop_b", NOP_AGENT_CODE)

    replay, result, _ = _run_test_match(tmp_path, "nop_a", "nop_b", ticks=8, with_trace=False)
    m = analyze_match(replay, result, trace_path=None)

    assert m["trace_available"] is False
    assert m["trace_applied_actions"] == {"A": 0, "B": 0}
    assert m["actual_ticks"] == 8
    assert m["final_core_health"] == {"A": 8, "B": 8}


def test_analyzer_replay_with_trace(tmp_path: Path) -> None:
    _setup_agent(tmp_path, "act_a", ACTIVE_AGENT_CODE)
    _setup_agent(tmp_path, "act_b", ACTIVE_AGENT_CODE)

    replay, result, trace = _run_test_match(tmp_path, "act_a", "act_b", ticks=10, with_trace=True)
    assert trace is not None and trace.is_file()

    m = analyze_match(replay, result, trace_path=trace)

    assert m["trace_available"] is True
    assert m["trace_applied_actions"]["A"] > 0
    assert m["trace_applied_actions"]["B"] > 0
    assert isinstance(m["trace_avg_latency_ms"]["A"], float)


def test_analyzer_malformed_input(tmp_path: Path) -> None:
    non_existent = tmp_path / "does_not_exist.jsonl"
    with pytest.raises(FileNotFoundError):
        analyze_match(non_existent)

    empty_file = tmp_path / "empty.jsonl"
    empty_file.write_text("", encoding="utf-8")
    with pytest.raises(ReplayFormatError):
        analyze_match(empty_file)


def test_analyzer_zero_event_no_progress(tmp_path: Path) -> None:
    _setup_agent(tmp_path, "idle_a", NOP_AGENT_CODE)
    _setup_agent(tmp_path, "idle_b", NOP_AGENT_CODE)

    replay, result, _ = _run_test_match(tmp_path, "idle_a", "idle_b", ticks=20)
    m = analyze_match(replay, result)

    assert m["core_damage_dealt"] == {"A": 0, "B": 0}
    assert m["core_attack_writes"] == {"A": 0, "B": 0}
    assert m["combat_conversion_rate"] == {"A": 0.0, "B": 0.0}
    assert m["time_to_first_core_damage"] is None


def test_corpus_manifest_deterministic_identity(tmp_path: Path) -> None:
    _setup_agent(tmp_path, "v4_claimer", NOP_AGENT_CODE)
    _setup_agent(tmp_path, "v4_scout", ACTIVE_AGENT_CODE)

    m1 = build_corpus_manifest(
        tmp_path,
        agents=("v4_claimer", "v4_scout"),
        seeds=(1, 2),
        arena_size=512,
        max_ticks=1000,
        ruleset_id=BYTEFRAY_RULESET_V4_ID,
    )
    m2 = build_corpus_manifest(
        tmp_path,
        agents=("v4_claimer", "v4_scout"),
        seeds=(1, 2),
        arena_size=512,
        max_ticks=1000,
        ruleset_id=BYTEFRAY_RULESET_V4_ID,
    )

    assert json.dumps(m1, sort_keys=True) == json.dumps(m2, sort_keys=True)
    assert m1["total_matches"] == 8  # 2 x 2 x 2

