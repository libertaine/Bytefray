"""Bytefray V6 M1-2: Window Scout Teaching Demonstration Test Suite.

Validates the Window Scout starter agent, Stationary Opponent fixture,
the sensing demonstration runner, determinism, capability preflight,
delayed-receipt boundaries, and strict negative research isolation.
"""

from __future__ import annotations

import builtins
import hashlib
import json
import random
import shutil
import tempfile
from pathlib import Path
from typing import Any

import pytest
from battle_engine.agent_api import (
    ActionKindV2,
    MatchContextV2,
    ObservationV2,
)
from battle_engine.agent_capabilities import (
    AgentCapabilityMismatchError,
    parse_required_capabilities,
)
from battle_engine.agents import agent_spec_from_dir
from battle_engine.config import Config
from battle_engine.data.starter_agents.v6_window_scout.agent import (
    WindowScoutAgent,
)
from battle_engine.data.starter_agents.v6_window_scout.agent import (
    create_agent as create_window_scout,
)
from battle_engine.data.teaching_fixtures.v6_stationary_opponent.agent import (
    StationaryOpponentAgent,
)
from battle_engine.data.teaching_fixtures.v6_stationary_opponent.agent import (
    create_agent as create_stationary_opponent,
)
from battle_engine.match_service import (
    MatchEntrant,
    MatchRequest,
    NativeMatchService,
)
from battle_engine.rules import (
    BYTEFRAY_RULESET_V6_ALPHA1_ID,
    BYTEFRAY_RULESET_V6_RESEARCH_SCALE_ID,
)
from battle_engine.sensing_demo import (
    STATIONARY_OPPONENT_FIXTURE_NAME,
    WINDOW_SCOUT_STARTER_NAME,
    resolve_teaching_agent_dir,
    run_sensing_demo,
    validate_output_directory,
    validate_sensing_demo_artifacts,
)
from battle_engine.starters import (
    CURRENT_STARTER_DIGESTS,
    STARTER_AGENT_NAMES,
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_starter_manifest_and_metadata() -> None:
    """Verify v6_window_scout manifest declarations and parameter schema."""
    scout_dir = resolve_teaching_agent_dir(WINDOW_SCOUT_STARTER_NAME)
    spec = agent_spec_from_dir(scout_dir)
    assert spec is not None
    assert spec.name == WINDOW_SCOUT_STARTER_NAME
    assert spec.kind == "python"
    assert spec.api_version == 2
    assert spec.entry_point == "agent.py:create_agent"

    manifest = spec.manifest
    assert manifest["capabilities"] == {"version": 1, "required": ["sense"]}
    assert parse_required_capabilities(manifest) == frozenset({"sense"})

    # Parameter declarations
    params = manifest.get("parameters", {})
    assert "search_interval" in params
    assert params["search_interval"]["type"] == "integer"
    assert params["search_interval"]["default"] == 4
    assert params["search_interval"]["minimum"] == 1
    assert params["search_interval"]["maximum"] == 16

    assert "move_step" in params
    assert params["move_step"]["type"] == "integer"
    assert params["move_step"]["default"] == 64
    assert params["move_step"]["minimum"] == 1
    assert params["move_step"]["maximum"] == 64

    # Presets
    presets = manifest.get("presets", {})
    assert "standard" in presets
    assert presets["standard"]["values"] == {
        "search_interval": 4,
        "move_step": 64,
    }


def test_teaching_fixture_manifest_and_metadata() -> None:
    """Verify v6_stationary_opponent manifest declarations."""
    opponent_dir = resolve_teaching_agent_dir(STATIONARY_OPPONENT_FIXTURE_NAME)
    spec = agent_spec_from_dir(opponent_dir)
    assert spec is not None
    assert spec.name == STATIONARY_OPPONENT_FIXTURE_NAME
    assert spec.kind == "python"
    assert spec.api_version == 2
    assert spec.entry_point == "agent.py:create_agent"

    manifest = spec.manifest
    assert parse_required_capabilities(manifest) == frozenset()


def test_window_scout_agent_logic_and_parameters() -> None:
    """Verify WindowScoutAgent initialization, reset, and process declaration."""
    agent = create_window_scout()
    assert isinstance(agent, WindowScoutAgent)

    procs = agent.declare_processes()
    assert len(procs) == 1
    assert procs[0].id == "main"
    assert procs[0].reach == 128
    assert procs[0].share == 1.0

    # Reset with custom parameters
    context = MatchContextV2(
        agent_id="A",
        seed=0,
        arena_size=512,
        tick_limit=100,
        rng=random.Random(0),
        parameters={"search_interval": 2, "move_step": 32, "search_offset": 50},
        sensing_window=27,
    )
    agent.reset(context)
    assert agent.search_interval == 2
    assert agent.move_step == 32
    assert agent.search_offset == 50
    assert agent.sensing_window == 27


def test_stationary_opponent_agent_logic() -> None:
    """Verify StationaryOpponentAgent always READs own core."""
    agent = create_stationary_opponent()
    assert isinstance(agent, StationaryOpponentAgent)

    procs = agent.declare_processes()
    assert len(procs) == 1
    assert procs[0].id == "main"

    context = MatchContextV2(
        agent_id="B",
        seed=0,
        arena_size=512,
        tick_limit=100,
        rng=random.Random(0),
    )
    agent.reset(context)

    obs = ObservationV2(
        current_tick=1,
        last_callback_tick=0,
        previous_action_tick=0,
        self_process_id="main",
        self_anchor=91,
        self_reach=128,
        own_core_base=91,
        own_core_size=8,
        visible_enemy_anchor_addresses=(),
        previous_action_applied=True,
        previous_read_value=None,
        previous_read_owner=None,
    )
    action = agent.act(obs)
    assert action.kind is ActionKindV2.READ
    assert action.operand == 91


def test_capability_preflight_rejection_under_a_passive_ruleset(tmp_path: Path) -> None:
    """Verify capability preflight fails closed before match execution under a passive Ruleset."""
    scout_dir = resolve_teaching_agent_dir(WINDOW_SCOUT_STARTER_NAME)
    opponent_dir = resolve_teaching_agent_dir(STATIONARY_OPPONENT_FIXTURE_NAME)
    scout_spec = agent_spec_from_dir(scout_dir)
    opponent_spec = agent_spec_from_dir(opponent_dir)
    assert scout_spec is not None and opponent_spec is not None

    replay_path = tmp_path / "replay.jsonl"
    trace_path = tmp_path / "trace.jsonl"

    request = MatchRequest(
        config=Config(arena_size=512, instr_per_tick=8, seed=0),
        entrants=(
            MatchEntrant.python("A", "scout", 0, scout_spec),
            MatchEntrant.python("B", "opponent", 91, opponent_spec),
        ),
        max_ticks=10,
        replay_path=replay_path,
        trace_path=trace_path,
        ruleset_id=BYTEFRAY_RULESET_V6_RESEARCH_SCALE_ID,
    )

    with pytest.raises(AgentCapabilityMismatchError) as exc_info:
        NativeMatchService().run(request)

    assert "sense" in str(exc_info.value)
    # Crucial preflight property: files must NOT be created on rejection
    assert not replay_path.exists()
    assert not trace_path.exists()


def test_window_scout_authoritative_teaching_exchange(tmp_path: Path) -> None:
    """Verify full sequence: SENSE(91) -> receipt (91,) -> MOVE(+64) -> WRITE(91)."""
    scout_dir = resolve_teaching_agent_dir(WINDOW_SCOUT_STARTER_NAME)
    opponent_dir = resolve_teaching_agent_dir(STATIONARY_OPPONENT_FIXTURE_NAME)
    scout_spec = agent_spec_from_dir(scout_dir)
    opponent_spec = agent_spec_from_dir(opponent_dir)
    assert scout_spec is not None and opponent_spec is not None

    replay_path = tmp_path / "replay.jsonl"
    trace_path = tmp_path / "trace.jsonl"

    request = MatchRequest(
        config=Config(arena_size=512, instr_per_tick=8, seed=0),
        entrants=(
            MatchEntrant.python(
                "A",
                "scout",
                0,
                scout_spec,
                parameters={"search_interval": 4, "move_step": 64},
            ),
            MatchEntrant.python("B", "opponent", 91, opponent_spec),
        ),
        max_ticks=15,
        replay_path=replay_path,
        trace_path=trace_path,
        ruleset_id=BYTEFRAY_RULESET_V6_ALPHA1_ID,
    )

    result = NativeMatchService().run(request)
    assert result.ticks_run > 0
    assert trace_path.is_file()

    lines = [json.loads(line) for line in trace_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    scout_decisions = [
        record for record in lines
        if record.get("record_type") == "decision_v2" and record.get("agent_id") == "A"
    ]
    assert len(scout_decisions) >= 3

    # Callback 1: SENSE 91
    cb1 = scout_decisions[0]
    cb1_obs = cb1["observation"]
    assert cb1_obs["visible_enemy_anchor_addresses"] == []
    assert cb1_obs.get("previous_sense_anchors") is None
    assert cb1["action"]["kind"] == "sense"
    assert cb1["action"]["operand"] == 91
    assert cb1["applied_result"]["status"] == "APPLIED"
    assert cb1["applied_result"]["sensed_anchors"] == [91]

    # Callback 2: delayed receipt arrived, MOVE +64
    cb2 = scout_decisions[1]
    cb2_obs = cb2["observation"]
    assert cb2_obs["previous_sense_anchors"] == [91]
    assert cb2["action"]["kind"] == "move"
    assert cb2["action"]["operand"] == 64
    assert cb2["applied_result"]["status"] == "APPLIED"

    # Callback 3: now at anchor 64, target 91 is dist 27 (in-reach WRITE)
    cb3 = scout_decisions[2]
    cb3_obs = cb3["observation"]
    assert cb3_obs["self_anchor"] == 64
    assert "previous_sense_anchors" not in cb3_obs
    assert cb3["action"]["kind"] == "write"
    assert cb3["action"]["operand"] == 91
    assert cb3["applied_result"]["status"] == "APPLIED"


def test_sensing_demo_runner_artifacts_and_provenance(tmp_path: Path) -> None:
    """Verify run_sensing_demo creates demo.json with valid schema and hashes."""
    output_dir = tmp_path / "sensing_demo"
    demo_result = run_sensing_demo(output_dir, ticks=10, seed=0)

    assert demo_result.is_verified is True
    assert demo_result.demo_path.is_file()
    assert demo_result.replay_path.is_file()
    assert demo_result.trace_path.is_file()
    assert demo_result.result_path.is_file()

    payload = json.loads(demo_result.demo_path.read_text(encoding="utf-8"))
    assert payload["schema"] == "bytefray.sensing_demo"
    assert payload["schema_version"] == 1
    assert payload["provenance"] == "product_teaching_demo"
    assert payload["declared_product_fixture"] is True
    assert payload["ruleset_id"] == BYTEFRAY_RULESET_V6_ALPHA1_ID
    assert payload["status"] == "reproducible"

    # Verify sha256 checksums in demo.json match files on disk
    artifacts = payload["artifacts"]
    assert artifacts["replay"]["sha256"] == _sha256(demo_result.replay_path)
    assert artifacts["trace"]["sha256"] == _sha256(demo_result.trace_path)
    assert artifacts["result"]["sha256"] == _sha256(demo_result.result_path)

    # Entrants revision capture and loaded runtime fingerprints
    entrants = payload["entrants"]
    assert len(entrants) == 2
    for e in entrants:
        assert e["capture_complete"] is True
        assert len(e["revision_id"]) > 0
        assert len(e["full_tree_digest"]) == 64
        assert len(e["python_subset_fingerprint"]) == 64
        assert e["loaded_initial_fingerprint"] == e["python_subset_fingerprint"]
        assert e["loaded_final_fingerprint"] == e["python_subset_fingerprint"]
        assert e["drift_detected"] is False

    # Teaching exchange
    exchange = payload["teaching_exchange"]
    assert exchange["sequence_verified"] is True
    assert len(exchange["steps"]) == 4


def test_deterministic_reproducibility(tmp_path: Path) -> None:
    """Verify identical fixture inputs yield bit-identical replay and trace."""
    run1 = tmp_path / "run1"
    run2 = tmp_path / "run2"

    res1 = run_sensing_demo(run1, ticks=12, seed=42)
    res2 = run_sensing_demo(run2, ticks=12, seed=42)

    assert res1.is_verified is True
    assert res2.is_verified is True

    # Replay is bit-identical
    assert _sha256(res1.replay_path) == _sha256(res2.replay_path)

    # Trace is identical once wall-clock timings are stripped
    def _clean_trace(p: Path) -> list[dict[str, Any]]:
        records = []
        for line in p.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            r.pop("wall_time_ms", None)
            if r.get("record_type") == "header":
                r.pop("supervised", None)
                r.pop("agent_call_timeout", None)
            records.append(r)
        return records

    assert _clean_trace(res1.trace_path) == _clean_trace(res2.trace_path)
    assert res1.match_result.match_id == res2.match_result.match_id
    assert res1.match_result.result_id == res2.match_result.result_id


def test_delayed_receipt_with_intermediate_opponent_movement(tmp_path: Path) -> None:
    """Boundary test: SENSE samples anchor at scan time; opponent moves before next callback.

    Agent A reads core, then senses 91.
    Agent B moves +8 before A's next chunk.
    A's next callback still receives [91], while omniscient truth has B at 99.
    """
    agent_dir_a = tmp_path / "agent_a"
    agent_dir_b = tmp_path / "agent_b"
    agent_dir_a.mkdir()
    agent_dir_b.mkdir()

    source_a = (
        "from battle_engine.agent_api import AgentAction, ActionKindV2, ProcessDeclaration, AgentV2\n"
        "class DelayedReceiverAgent(AgentV2):\n"
        "    def __init__(self):\n"
        "        self.calls = 0\n"
        "    def declare_processes(self):\n"
        "        return [ProcessDeclaration(id='main', reach=128, share=1.0)]\n"
        "    def act(self, obs):\n"
        "        self.calls += 1\n"
        "        if self.calls == 1:\n"
        "            return AgentAction(ActionKindV2.READ, operand=obs.own_core_base)\n"
        "        if self.calls == 2:\n"
        "            return AgentAction(ActionKindV2.SENSE, operand=91)\n"
        "        return AgentAction(ActionKindV2.READ, operand=obs.own_core_base)\n"
        "def create_agent():\n"
        "    return DelayedReceiverAgent()\n"
    )
    (agent_dir_a / "agent.py").write_text(source_a, encoding="utf-8")
    (agent_dir_a / "agent.yaml").write_text(json.dumps({
        "name": "receiver",
        "kind": "python",
        "api_version": 2,
        "entrypoint": "agent.py:create_agent",
        "capabilities": {"version": 1, "required": ["sense"]},
    }), encoding="utf-8")
    spec_a = agent_spec_from_dir(agent_dir_a)
    assert spec_a is not None

    source_b = (
        "from battle_engine.agent_api import AgentAction, ActionKindV2, ProcessDeclaration, AgentV2\n"
        "class MovingOpponentAgent(AgentV2):\n"
        "    def __init__(self):\n"
        "        self.calls = 0\n"
        "    def declare_processes(self):\n"
        "        return [ProcessDeclaration(id='main', reach=128, share=1.0)]\n"
        "    def act(self, obs):\n"
        "        self.calls += 1\n"
        "        if self.calls == 1:\n"
        "            return AgentAction(ActionKindV2.MOVE, operand=8)\n"
        "        return AgentAction(ActionKindV2.READ, operand=obs.own_core_base)\n"
        "def create_agent():\n"
        "    return MovingOpponentAgent()\n"
    )
    (agent_dir_b / "agent.py").write_text(source_b, encoding="utf-8")
    (agent_dir_b / "agent.yaml").write_text(json.dumps({
        "name": "mover",
        "kind": "python",
        "api_version": 2,
        "entrypoint": "agent.py:create_agent",
    }), encoding="utf-8")
    spec_b = agent_spec_from_dir(agent_dir_b)
    assert spec_b is not None

    trace_path = tmp_path / "trace.jsonl"
    request = MatchRequest(
        config=Config(arena_size=512, instr_per_tick=8, seed=0),
        entrants=(
            MatchEntrant.python("A", "receiver", 0, spec_a),
            MatchEntrant.python("B", "mover", 91, spec_b),
        ),
        max_ticks=5,
        replay_path=tmp_path / "replay.jsonl",
        trace_path=trace_path,
        ruleset_id=BYTEFRAY_RULESET_V6_ALPHA1_ID,
    )

    result = NativeMatchService().run(request)
    assert result.ticks_run > 0
    assert trace_path.is_file()

    lines = [json.loads(line) for line in trace_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    decisions = [r for r in lines if r.get("record_type") == "decision_v2"]

    a_decisions = [r for r in decisions if r["agent_id"] == "A"]
    b_decisions = [r for r in decisions if r["agent_id"] == "B"]

    # A callback 2: requested SENSE(91) when B was at 91
    assert a_decisions[1]["action"]["kind"] == "sense"
    assert a_decisions[1]["action"]["operand"] == 91
    assert a_decisions[1]["applied_result"]["sensed_anchors"] == [91]

    # B callback 1: moved +8 to anchor 99
    assert b_decisions[0]["action"]["kind"] == "move"
    assert b_decisions[0]["action"]["operand"] == 8
    assert b_decisions[0]["applied_result"]["normalized_address"] == 99

    # A callback 3: received delayed sample [91]
    assert a_decisions[2]["observation"]["previous_sense_anchors"] == [91]
    # Omniscient visibility is empty
    assert a_decisions[2]["observation"]["visible_enemy_anchor_addresses"] == []


def test_negative_research_isolation(monkeypatch) -> None:
    """Verify demo and starter execution never touch research infrastructure."""
    original_import = builtins.__import__

    def guarded_import(name: str, *args: Any, **kwargs: Any) -> Any:
        assert not name.startswith("tools.research"), f"Unpermitted research import: {name}"
        assert "e8" not in name.lower() or "battle_engine" in name, f"Unpermitted E8 reference: {name}"
        assert "e9" not in name.lower() or "battle_engine" in name, f"Unpermitted E9 reference: {name}"
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guarded_import)

    # Resolve starter and fixture
    scout_dir = resolve_teaching_agent_dir(WINDOW_SCOUT_STARTER_NAME)
    opponent_dir = resolve_teaching_agent_dir(STATIONARY_OPPONENT_FIXTURE_NAME)
    assert scout_dir.is_dir()
    assert opponent_dir.is_dir()

    # Instantiate agents
    scout = create_window_scout()
    opponent = create_stationary_opponent()
    assert scout is not None
    assert opponent is not None


def test_starter_registry_invariants() -> None:
    """Verify v6_window_scout is registered in starters.py with valid digest."""
    assert "v6_window_scout" in STARTER_AGENT_NAMES
    assert "v6_window_scout" in CURRENT_STARTER_DIGESTS
    # The Classic retirement left exactly the three Active Sensing starters.
    assert STARTER_AGENT_NAMES == ("v6_window_scout", "v6_watchful_keeper", "v6_roaming_reacquirer")


def test_sensing_action_cost_and_quota_consumption(tmp_path: Path) -> None:
    """Verify AC2 price: SENSE consumes 1 action, causes no world mutation or movement, and respects Q=8."""
    agent_dir_a = tmp_path / "agent_a"
    agent_dir_b = tmp_path / "agent_b"
    agent_dir_a.mkdir()
    agent_dir_b.mkdir()

    source_a = (
        "from battle_engine.agent_api import AgentAction, ActionKindV2, ProcessDeclaration, AgentV2\n"
        "class SenserAgent(AgentV2):\n"
        "    def __init__(self):\n"
        "        self.calls = 0\n"
        "    def declare_processes(self):\n"
        "        return [ProcessDeclaration(id='main', reach=128, share=1.0)]\n"
        "    def act(self, obs):\n"
        "        self.calls += 1\n"
        "        return AgentAction(ActionKindV2.SENSE, operand=91)\n"
        "def create_agent():\n"
        "    return SenserAgent()\n"
    )
    (agent_dir_a / "agent.py").write_text(source_a, encoding="utf-8")
    (agent_dir_a / "agent.yaml").write_text(json.dumps({
        "name": "senser",
        "kind": "python",
        "api_version": 2,
        "entrypoint": "agent.py:create_agent",
        "capabilities": {"version": 1, "required": ["sense"]},
    }), encoding="utf-8")
    spec_a = agent_spec_from_dir(agent_dir_a)
    assert spec_a is not None

    source_b = (
        "from battle_engine.agent_api import AgentAction, ActionKindV2, ProcessDeclaration, AgentV2\n"
        "class CoreReaderAgent(AgentV2):\n"
        "    def declare_processes(self):\n"
        "        return [ProcessDeclaration(id='main', reach=128, share=1.0)]\n"
        "    def act(self, obs):\n"
        "        return AgentAction(ActionKindV2.READ, operand=obs.own_core_base)\n"
        "def create_agent():\n"
        "    return CoreReaderAgent()\n"
    )
    (agent_dir_b / "agent.py").write_text(source_b, encoding="utf-8")
    (agent_dir_b / "agent.yaml").write_text(json.dumps({
        "name": "reader",
        "kind": "python",
        "api_version": 2,
        "entrypoint": "agent.py:create_agent",
    }), encoding="utf-8")
    spec_b = agent_spec_from_dir(agent_dir_b)
    assert spec_b is not None

    trace_path = tmp_path / "trace.jsonl"
    replay_path = tmp_path / "replay.jsonl"
    request = MatchRequest(
        config=Config(arena_size=512, instr_per_tick=8, seed=0),
        entrants=(
            MatchEntrant.python("A", "senser", 0, spec_a),
            MatchEntrant.python("B", "reader", 91, spec_b),
        ),
        max_ticks=1,
        replay_path=replay_path,
        trace_path=trace_path,
        ruleset_id=BYTEFRAY_RULESET_V6_ALPHA1_ID,
    )

    result = NativeMatchService().run(request)
    assert result.ticks_run == 1
    assert trace_path.is_file()

    lines = [json.loads(line) for line in trace_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    decisions = [r for r in lines if r.get("record_type") == "decision_v2"]
    a_decisions = [r for r in decisions if r["agent_id"] == "A"]

    # Budget is Q=8: single-process entrant A executes exactly 8 decisions in 1 tick, no 9th action
    assert len(a_decisions) == 8

    # Each decision was SENSE, status APPLIED
    for d in a_decisions:
        assert d["action"]["kind"] == "sense"
        assert d["action"]["operand"] == 91
        assert d["applied_result"]["status"] == "APPLIED"
        # Anchor remained at 0 (sensing does not move)
        assert d["observation"]["self_anchor"] == 0

    # Agent A only owns its initial 8-cell core (sensing awards no territory)
    a_agent = next(a for a in result.agents if a.agent_id == "A")
    assert a_agent.territory_last == 8
    # Agent A mem_writes is 0 (sensing causes no world mutation)
    assert a_agent.mem_writes == 0


def test_window_scout_multi_cadence_resumption() -> None:
    """Verify Window Scout clears target after WRITE and resumes periodic sensing cadence."""
    agent = create_window_scout()
    context = MatchContextV2(
        agent_id="A",
        seed=0,
        arena_size=512,
        tick_limit=100,
        rng=random.Random(0),
        parameters={"search_interval": 4, "move_step": 64},
        sensing_window=27,
    )
    agent.reset(context)

    # Callback 1: initial scan
    obs1 = ObservationV2(
        current_tick=1, last_callback_tick=0, previous_action_tick=0,
        self_process_id="main", self_anchor=0, self_reach=128,
        own_core_base=0, own_core_size=8, visible_enemy_anchor_addresses=(),
        previous_action_applied=True, previous_read_value=None, previous_read_owner=None,
    )
    act1 = agent.act(obs1)
    assert act1.kind is ActionKindV2.SENSE
    assert act1.operand == 91

    # Callback 2: receipt delivered -> MOVE(+64)
    obs2 = ObservationV2(
        current_tick=1, last_callback_tick=1, previous_action_tick=1,
        self_process_id="main", self_anchor=0, self_reach=128,
        own_core_base=0, own_core_size=8, visible_enemy_anchor_addresses=(),
        previous_action_applied=True, previous_read_value=None, previous_read_owner=None,
        previous_sense_anchors=(91,),
    )
    act2 = agent.act(obs2)
    assert act2.kind is ActionKindV2.MOVE
    assert act2.operand == 64

    # Callback 3: now at 64 -> in-reach WRITE(91)
    obs3 = ObservationV2(
        current_tick=1, last_callback_tick=1, previous_action_tick=1,
        self_process_id="main", self_anchor=64, self_reach=128,
        own_core_base=0, own_core_size=8, visible_enemy_anchor_addresses=(),
        previous_action_applied=True, previous_read_value=None, previous_read_owner=None,
    )
    act3 = agent.act(obs3)
    assert act3.kind is ActionKindV2.WRITE
    assert act3.operand == 91
    # Crucial: target is cleared
    assert agent.active_target is None

    # Callback 4: cadence not yet due (4 % 4 == 0) -> fallback READ own core
    obs4 = ObservationV2(
        current_tick=1, last_callback_tick=1, previous_action_tick=1,
        self_process_id="main", self_anchor=64, self_reach=128,
        own_core_base=0, own_core_size=8, visible_enemy_anchor_addresses=(),
        previous_action_applied=True, previous_read_value=None, previous_read_owner=None,
    )
    act4 = agent.act(obs4)
    assert act4.kind is ActionKindV2.READ
    assert act4.operand == 0

    # Callback 5: cadence triggers (5 % 4 == 1) -> SENSE again at new anchor relative offset
    obs5 = ObservationV2(
        current_tick=1, last_callback_tick=1, previous_action_tick=1,
        self_process_id="main", self_anchor=64, self_reach=128,
        own_core_base=0, own_core_size=8, visible_enemy_anchor_addresses=(),
        previous_action_applied=True, previous_read_value=None, previous_read_owner=None,
    )
    act5 = agent.act(obs5)
    assert act5.kind is ActionKindV2.SENSE
    assert act5.operand == (64 + 91) % 512


def test_out_of_reach_sense_rejection_and_cost(tmp_path: Path) -> None:
    """Verify SENSE beyond reach consumes 1 action and produces rejected trace outcome."""
    agent_dir_a = tmp_path / "agent_a"
    agent_dir_b = tmp_path / "agent_b"
    agent_dir_a.mkdir()
    agent_dir_b.mkdir()

    source_a = (
        "from battle_engine.agent_api import AgentAction, ActionKindV2, ProcessDeclaration, AgentV2\n"
        "class OutOfReachSenser(AgentV2):\n"
        "    def __init__(self):\n"
        "        self.calls = 0\n"
        "    def declare_processes(self):\n"
        "        return [ProcessDeclaration(id='main', reach=128, share=1.0)]\n"
        "    def act(self, obs):\n"
        "        self.calls += 1\n"
        "        if self.calls == 1:\n"
        "            # Target 300 from anchor 0 is distance 212 > 128 (out of reach)\n"
        "            return AgentAction(ActionKindV2.SENSE, operand=300)\n"
        "        return AgentAction(ActionKindV2.READ, operand=obs.own_core_base)\n"
        "def create_agent():\n"
        "    return OutOfReachSenser()\n"
    )
    (agent_dir_a / "agent.py").write_text(source_a, encoding="utf-8")
    (agent_dir_a / "agent.yaml").write_text(json.dumps({
        "name": "oor_senser",
        "kind": "python",
        "api_version": 2,
        "entrypoint": "agent.py:create_agent",
        "capabilities": {"version": 1, "required": ["sense"]},
    }), encoding="utf-8")
    spec_a = agent_spec_from_dir(agent_dir_a)
    assert spec_a is not None

    source_b = (
        "from battle_engine.agent_api import AgentAction, ActionKindV2, ProcessDeclaration, AgentV2\n"
        "class StationaryB(AgentV2):\n"
        "    def declare_processes(self):\n"
        "        return [ProcessDeclaration(id='main', reach=128, share=1.0)]\n"
        "    def act(self, obs):\n"
        "        return AgentAction(ActionKindV2.READ, operand=obs.own_core_base)\n"
        "def create_agent():\n"
        "    return StationaryB()\n"
    )
    (agent_dir_b / "agent.py").write_text(source_b, encoding="utf-8")
    (agent_dir_b / "agent.yaml").write_text(json.dumps({
        "name": "stat_b",
        "kind": "python",
        "api_version": 2,
        "entrypoint": "agent.py:create_agent",
    }), encoding="utf-8")
    spec_b = agent_spec_from_dir(agent_dir_b)
    assert spec_b is not None

    trace_path = tmp_path / "trace.jsonl"
    request = MatchRequest(
        config=Config(arena_size=512, instr_per_tick=8, seed=0),
        entrants=(
            MatchEntrant.python("A", "oor_senser", 0, spec_a),
            MatchEntrant.python("B", "stat_b", 91, spec_b),
        ),
        max_ticks=2,
        replay_path=tmp_path / "replay.jsonl",
        trace_path=trace_path,
        ruleset_id=BYTEFRAY_RULESET_V6_ALPHA1_ID,
    )

    NativeMatchService().run(request)
    assert trace_path.is_file()

    lines = [json.loads(line) for line in trace_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    a_decisions = [r for r in lines if r.get("record_type") == "decision_v2" and r.get("agent_id") == "A"]

    cb1 = a_decisions[0]
    assert cb1["action"]["kind"] == "sense"
    assert cb1["action"]["operand"] == 300
    assert cb1["applied_result"]["status"] == "REJECTED_OUT_OF_REACH"
    assert cb1["applied_result"].get("sensed_anchors") is None

    # Next callback receives None/false reflection
    cb2 = a_decisions[1]
    assert cb2["observation"].get("previous_sense_anchors") is None
    assert cb2["observation"].get("previous_action_applied") is False


def test_demo_runner_rejects_drifted_or_incomplete_capture(tmp_path: Path, monkeypatch) -> None:
    """Verify demo runner marks demo unverified if capture is incomplete or drift occurs."""
    import battle_engine.sensing_demo as demo_mod
    original_walk = demo_mod.walk_agent_files

    def incomplete_walk(agent_dir):
        res = original_walk(agent_dir)
        # Simulate omission making complete=False
        from battle_engine.agent_revisions import AgentFileWalkResult, OmittedAgentPath
        omitted = (OmittedAgentPath("stray.tmp", "unreadable", None),)
        return AgentFileWalkResult(entries=res.entries, omitted=omitted)

    monkeypatch.setattr(demo_mod, "walk_agent_files", incomplete_walk)

    output_dir = tmp_path / "incomplete_demo"
    demo_result = run_sensing_demo(output_dir, ticks=5, seed=0)
    assert demo_result.is_verified is False

    payload = json.loads(demo_result.demo_path.read_text(encoding="utf-8"))
    assert payload["status"] == "unverified"


def test_window_scout_behavior_when_opponent_at_different_location_and_window_empty(tmp_path: Path) -> None:
    """Verify Window Scout's SENSE is independent of opponent position; handles empty scan correctly.

    Contract Boundary 1:
    - Opponent is at anchor 200 (outside sensing window [64..118] around 91).
    - Window Scout at 0 still requests SENSE(91) on callback 1 (proves scan target is determined
      by declared teaching behavior, not hidden opponent position).
    - Engine evaluates window and yields empty contact set [].
    - Callback 2 delivers previous_sense_anchors = [].
    - Window Scout does NOT move to 91; it executes legal fallback READ on own core.
    - Cadence resumes on callback 5, requesting SENSE(91).
    - When Window Scout starts at anchor 100, callback 1 requests SENSE(191), confirming
      (self_anchor + search_offset) % arena calculation with zero opponent coupling.
    """
    scout_dir = resolve_teaching_agent_dir(WINDOW_SCOUT_STARTER_NAME)
    opponent_dir = resolve_teaching_agent_dir(STATIONARY_OPPONENT_FIXTURE_NAME)
    scout_spec = agent_spec_from_dir(scout_dir)
    opponent_spec = agent_spec_from_dir(opponent_dir)
    assert scout_spec is not None and opponent_spec is not None

    trace_path = tmp_path / "trace.jsonl"
    request = MatchRequest(
        config=Config(arena_size=512, instr_per_tick=8, seed=0),
        entrants=(
            MatchEntrant.python("A", "scout", 0, scout_spec),
            MatchEntrant.python("B", "opponent", 200, opponent_spec),
        ),
        max_ticks=5,
        replay_path=tmp_path / "replay.jsonl",
        trace_path=trace_path,
        ruleset_id=BYTEFRAY_RULESET_V6_ALPHA1_ID,
    )

    result = NativeMatchService().run(request)
    assert result.ticks_run > 0
    assert trace_path.is_file()

    lines = [json.loads(line) for line in trace_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    a_decisions = [r for r in lines if r.get("record_type") == "decision_v2" and r.get("agent_id") == "A"]
    assert len(a_decisions) >= 5

    # Callback 1: SENSE(91) requested despite opponent at 200
    cb1 = a_decisions[0]
    assert cb1["action"]["kind"] == "sense"
    assert cb1["action"]["operand"] == 91
    assert cb1["applied_result"]["status"] == "APPLIED"
    assert cb1["applied_result"]["sensed_anchors"] == []  # Empty window

    # Callback 2: delivered empty receipt []; does NOT move; executes fallback READ(0)
    cb2 = a_decisions[1]
    assert cb2["observation"]["previous_sense_anchors"] == []
    assert cb2["action"]["kind"] == "read"
    assert cb2["action"]["operand"] == 0
    assert cb2["observation"]["self_anchor"] == 0

    # Callback 3: fallback READ(0)
    cb3 = a_decisions[2]
    assert cb3["action"]["kind"] == "read"
    assert cb3["action"]["operand"] == 0

    # Callback 4: fallback READ(0)
    cb4 = a_decisions[3]
    assert cb4["action"]["kind"] == "read"
    assert cb4["action"]["operand"] == 0

    # Callback 5: cadence triggers (5 % 4 == 1); SENSE(91) requested again
    cb5 = a_decisions[4]
    assert cb5["action"]["kind"] == "sense"
    assert cb5["action"]["operand"] == 91

    # Secondary check: Non-zero start anchor (100) calculates (100 + 91) = 191
    trace_path_100 = tmp_path / "trace_100.jsonl"
    request_100 = MatchRequest(
        config=Config(arena_size=512, instr_per_tick=8, seed=0),
        entrants=(
            MatchEntrant.python("A", "scout", 100, scout_spec),
            MatchEntrant.python("B", "opponent", 300, opponent_spec),
        ),
        max_ticks=2,
        replay_path=tmp_path / "replay_100.jsonl",
        trace_path=trace_path_100,
        ruleset_id=BYTEFRAY_RULESET_V6_ALPHA1_ID,
    )
    NativeMatchService().run(request_100)
    lines_100 = [json.loads(line) for line in trace_path_100.read_text(encoding="utf-8").splitlines() if line.strip()]
    a_100_decisions = [r for r in lines_100 if r.get("record_type") == "decision_v2" and r.get("agent_id") == "A"]
    assert a_100_decisions[0]["action"]["kind"] == "sense"
    assert a_100_decisions[0]["action"]["operand"] == 191  # (100 + 91) % 512
    assert a_100_decisions[0]["applied_result"]["sensed_anchors"] == []  # Empty window at 191 when opponent at 300
    # Callback 2 receives empty receipt, executes fallback READ(100) on own core
    assert a_100_decisions[1]["observation"]["previous_sense_anchors"] == []
    assert a_100_decisions[1]["action"]["kind"] == "read"
    assert a_100_decisions[1]["action"]["operand"] == 100


def test_demonstration_artifacts_contain_and_validate_provenance(tmp_path: Path) -> None:
    """Verify demonstration artifacts contain and validate required provenance and digests.

    Contract Boundary 2:
    - demo.json contains schema bytefray.sensing_demo v1.
    - provenance == 'product_teaching_demo'.
    - declared_product_fixture is True.
    - ruleset_id matches bytefray-rules-6-alpha1.
    - SHA-256 digests for replay, trace, and result match disk files.
    - validate_sensing_demo_artifacts() verifies valid runs and catches accidental
      corruption, payload inconsistency, malformed JSON payloads, non-dict entries,
      invalid types, or path traversal (note: mutable sidecars detect inconsistency
      and disk corruption, not cryptographic tamper-proofing).
    """
    output_dir = tmp_path / "valid_demo"
    res = run_sensing_demo(output_dir, ticks=10, seed=0)
    assert res.is_verified is True
    assert validate_sensing_demo_artifacts(output_dir) is True
    assert validate_sensing_demo_artifacts(res.demo_path) is True

    payload = json.loads(res.demo_path.read_text(encoding="utf-8"))
    assert payload["provenance"] == "product_teaching_demo"
    assert payload["declared_product_fixture"] is True

    # Corruption / inconsistency test 1: corrupt replay artifact byte
    corrupt_dir = tmp_path / "corrupt_replay"
    shutil.copytree(output_dir, corrupt_dir)
    (corrupt_dir / "replay.jsonl").write_bytes(b'{"corrupted": true}\n')
    assert validate_sensing_demo_artifacts(corrupt_dir) is False

    # Corruption / inconsistency test 2: corrupt trace artifact byte
    corrupt_trace_dir = tmp_path / "corrupt_trace"
    shutil.copytree(output_dir, corrupt_trace_dir)
    (corrupt_trace_dir / "trace.jsonl").write_bytes(b'{"corrupted": true}\n')
    assert validate_sensing_demo_artifacts(corrupt_trace_dir) is False

    # Corruption / inconsistency test 3: corrupt result artifact byte
    corrupt_res_dir = tmp_path / "corrupt_result"
    shutil.copytree(output_dir, corrupt_res_dir)
    (corrupt_res_dir / "result.json").write_bytes(b'{"corrupted": true}\n')
    assert validate_sensing_demo_artifacts(corrupt_res_dir) is False

    # Corruption / inconsistency test 4: alter provenance identifier
    bad_prov_dir = tmp_path / "bad_prov"
    shutil.copytree(output_dir, bad_prov_dir)
    bad_prov_payload = json.loads((bad_prov_dir / "demo.json").read_text(encoding="utf-8"))
    bad_prov_payload["provenance"] = "unauthorized_demo"
    (bad_prov_dir / "demo.json").write_text(json.dumps(bad_prov_payload), encoding="utf-8")
    assert validate_sensing_demo_artifacts(bad_prov_dir) is False

    # Corruption / inconsistency test 5: clear declared_product_fixture flag
    no_fix_dir = tmp_path / "no_fixture"
    shutil.copytree(output_dir, no_fix_dir)
    no_fix_payload = json.loads((no_fix_dir / "demo.json").read_text(encoding="utf-8"))
    no_fix_payload["declared_product_fixture"] = False
    (no_fix_dir / "demo.json").write_text(json.dumps(no_fix_payload), encoding="utf-8")
    assert validate_sensing_demo_artifacts(no_fix_dir) is False

    # Corruption / inconsistency test 6: malformed JSON payload (list instead of dict)
    list_payload_dir = tmp_path / "list_payload"
    list_payload_dir.mkdir()
    (list_payload_dir / "demo.json").write_text("[]", encoding="utf-8")
    assert validate_sensing_demo_artifacts(list_payload_dir) is False

    # Corruption / inconsistency test 7: malformed result entry (non-dict value)
    bad_result_entry_dir = tmp_path / "bad_result_entry"
    shutil.copytree(output_dir, bad_result_entry_dir)
    bad_res_payload = json.loads((bad_result_entry_dir / "demo.json").read_text(encoding="utf-8"))
    bad_res_payload["artifacts"]["result"] = "not_a_dict"
    (bad_result_entry_dir / "demo.json").write_text(json.dumps(bad_res_payload), encoding="utf-8")
    assert validate_sensing_demo_artifacts(bad_result_entry_dir) is False

    # Corruption / inconsistency test 8: non-string filename or traversal filename
    bad_filename_dir = tmp_path / "bad_filename"
    shutil.copytree(output_dir, bad_filename_dir)
    bad_fn_payload = json.loads((bad_filename_dir / "demo.json").read_text(encoding="utf-8"))
    bad_fn_payload["artifacts"]["replay"]["filename"] = 123
    (bad_filename_dir / "demo.json").write_text(json.dumps(bad_fn_payload), encoding="utf-8")
    assert validate_sensing_demo_artifacts(bad_filename_dir) is False

    traversal_dir = tmp_path / "traversal_filename"
    shutil.copytree(output_dir, traversal_dir)
    trav_payload = json.loads((traversal_dir / "demo.json").read_text(encoding="utf-8"))
    trav_payload["artifacts"]["replay"]["filename"] = "../replay.jsonl"
    (traversal_dir / "demo.json").write_text(json.dumps(trav_payload), encoding="utf-8")
    assert validate_sensing_demo_artifacts(traversal_dir) is False


def test_research_isolation_and_unauthorized_output_paths(tmp_path: Path, monkeypatch) -> None:
    """Verify research isolation beyond import blocking: paths, seeds, G, and authority events.

    Contract Boundary 3 (Phase 0 Condition C-2, AC11):
    - Rejects unauthorized output paths: tools/research, docs/research, private research
      namespaces (e9, research_*), repository source/doc trees, bare root runs,
      arbitrary external paths outside product directories, and empty/whitespace paths.
    - Rejects attempts to overwrite non-demonstration artifacts.
    - Resolves and rejects symlinks / junctions into protected directories.
    - Permits legitimate temporary test directories and authorized runs/ product paths.
    - Full demonstration execution under guarded import touches no research code.
    - Demo produces no private E9 seeds, consumes no G, and emits no research authority events
      in demo metadata, traces, or replays.
    """
    # 1. Output directory isolation: reject research paths, protected trees, and invalid paths
    unauthorized_paths = (
        Path("tools/research/v6/e9/unauthorized_run"),
        Path("docs/research/v6/unauthorized_run"),
        Path("tools/research"),
        Path("runs/research_v6_e8/leak"),
        Path("runs/research_v3_phase1/leak"),
        Path("runs/e9_capability/leak"),
        Path("runs/v5_r4_lineage/leak"),
        Path("runs/v2_0_alpha1_evaluation/leak"),
        Path("runs/evaluations/leak"),
        Path("runs/agents_test/leak"),
        Path("runs/_loose/leak"),
        Path("engine/src/battle_engine"),
        Path("_legacy"),
        Path("runs"),
        Path(".pytest-tmp"),
        Path(tempfile.gettempdir()),
        Path("C:/Windows/System32"),
        Path.cwd().parent / "unauthorized_external_destination",
        tmp_path / "research_v6_e9_leak",
        tmp_path / ".pytest_e9_leak",
        "",
        "   ",
    )
    for unauth_path in unauthorized_paths:
        with pytest.raises(ValueError, match="Unauthorized output path"):
            validate_output_directory(unauth_path)

        with pytest.raises(ValueError, match="Unauthorized output path"):
            run_sensing_demo(unauth_path, ticks=2)

    # 2. Overwrite protection: reject existing directories or ancestors with non-demonstration files
    foreign_dir = tmp_path / "foreign_data"
    foreign_dir.mkdir()
    (foreign_dir / "unrelated.txt").write_text("protected content", encoding="utf-8")
    with pytest.raises(ValueError, match="Unauthorized output path.*non-demonstration"):
        validate_output_directory(foreign_dir)

    # Overwrite protection for ancestor directory under runs/
    mock_runs = tmp_path / "runs"
    mock_ancestor = mock_runs / "existing_parent"
    mock_ancestor.mkdir(parents=True)
    (mock_ancestor / "protected_file.json").write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="ancestor directory contains non-demonstration"):
        validate_output_directory(mock_ancestor / "child", resource_root=tmp_path)

    # 3. Symlink / junction resolution into protected research directory
    target_protected = Path("tools/research").resolve()
    junction_dir = tmp_path / "junction_to_research"
    has_link = False
    try:
        import _winapi

        _winapi.CreateJunction(str(target_protected), str(junction_dir))
        has_link = True
    except (ImportError, OSError, AttributeError):
        try:
            junction_dir.symlink_to(target_protected, target_is_directory=True)
            has_link = True
        except OSError:
            has_link = False

    if has_link:
        try:
            with pytest.raises(ValueError, match="Unauthorized output path"):
                validate_output_directory(junction_dir)
        finally:
            try:
                junction_dir.rmdir()
            except OSError:
                pass

    # 4. Legitimate pytest temporary-directory and product runs/ behavior succeeds
    legit_test_dir = tmp_path / "legit_demo_output"
    assert validate_output_directory(legit_test_dir) == legit_test_dir.resolve()
    legit_runs_dir = tmp_path / "runs" / "legit_runs_output"
    assert validate_output_directory(legit_runs_dir, resource_root=tmp_path) == legit_runs_dir.resolve()

    # 5. Strict runtime execution isolation under guarded import
    original_import = builtins.__import__

    def guarded_import(name: str, *args: Any, **kwargs: Any) -> Any:
        assert not name.startswith("tools.research"), f"Unpermitted research import: {name}"
        assert "e8" not in name.lower() or "battle_engine" in name, f"Unpermitted E8 reference: {name}"
        assert "e9" not in name.lower() or "battle_engine" in name, f"Unpermitted E9 reference: {name}"
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guarded_import)

    safe_dir = tmp_path / "safe_isolated_demo"
    demo_result = run_sensing_demo(safe_dir, ticks=10, seed=0)
    assert demo_result.is_verified is True

    # 6. Verify produced artifacts contain no research authority events or G consumption records
    demo_payload = json.loads(demo_result.demo_path.read_text(encoding="utf-8"))
    demo_text = json.dumps(demo_payload)
    replay_text = demo_result.replay_path.read_text(encoding="utf-8")
    trace_text = demo_result.trace_path.read_text(encoding="utf-8")
    result_text = demo_result.result_path.read_text(encoding="utf-8")

    for text_artifact in (demo_text, replay_text, trace_text, result_text):
        assert "authority_event" not in text_artifact
        assert "consume_generation" not in text_artifact
        assert "protocol_freeze" not in text_artifact
        assert "tools/research" not in text_artifact
        assert "docs/research" not in text_artifact
        assert ".pytest_e9_" not in text_artifact
        assert "research_v6_e9_" not in text_artifact
