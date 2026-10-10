"""V6 E8: the context and observation fields, the worker boundary and real traces (phase I8-2).

docs/research/v6/V6_E8_ACTIVE_SPATIAL_SENSING_PREREGISTRATION.md (PR8) Sec 2.3
and 10, and the implementation plan Sec 4.3. ``MatchContextV2.sensing_window``
and ``ObservationV2.previous_sense_anchors`` are additive and last, with a
``None`` default, like E6's ``detection_radius``: not an Agent API version
change. Under T8 and T8L both executors hand the agent ``27`` and deliver a
SENSE's result at its next callback; under every other Ruleset, and in a
validation dry run, the window is ``None``. The real development-test path
(``agent_test.test_agent``, the one the E8 harness uses) writes reset records
without the window under the controls and with ``27`` under the treatments.

The agents here are scripted test agents that report through their declared
process ID or their next action's operand; none is an E8 family member, and no
outcome is asserted.
"""

from __future__ import annotations

import json
import random
from dataclasses import FrozenInstanceError, fields
from pathlib import Path

import pytest
from _e8_sensing_harness import e8_keys_in, presence_problems, trace_records
from _hang_safety import hang_safety_timeout
from battle_engine import agent_test
from battle_engine.agent_api import MatchContextV2, ObservationV2
from battle_engine.agent_test import DevelopmentTestOutcome
from battle_engine.agent_trace import TRACE_SCHEMA_VERSION_V2, TraceHeader, TraceWriter
from battle_engine.agent_validation import build_validation_context, build_validation_observation
from battle_engine.agent_worker import AgentWorkerHandle, WorkerCallStatus
from battle_engine.agents import resolve_agent
from battle_engine.config import Config
from battle_engine.match_service import MatchEntrant
from battle_engine.process_runtime import ProcessMatchController
from battle_engine.ruleset_policy import (
    _RULESET_POLICIES,
    BYTEFRAY_RULESET_V6_RESEARCH_DISRUPTION_SLOT1_SENSING_ACTIVE_W27_ID,
    BYTEFRAY_RULESET_V6_RESEARCH_DISRUPTION_SLOT1_SENSING_R32_ID,
    BYTEFRAY_RULESET_V6_RESEARCH_SENSING_ACTIVE_W27_ID,
    BYTEFRAY_RULESET_V6_RESEARCH_SENSING_R32_ID,
    RulesetPolicy,
    resolve_ruleset_policy,
)

E8_IDS = (BYTEFRAY_RULESET_V6_RESEARCH_SENSING_ACTIVE_W27_ID,
          BYTEFRAY_RULESET_V6_RESEARCH_DISRUPTION_SLOT1_SENSING_ACTIVE_W27_ID)
CONTROL_IDS = (BYTEFRAY_RULESET_V6_RESEARCH_SENSING_R32_ID, BYTEFRAY_RULESET_V6_RESEARCH_DISRUPTION_SLOT1_SENSING_R32_ID)
WORKER_TIMEOUT = 30.0

REPORTER_SOURCE = """\
from battle_engine.agent_api import ActionKindV2, AgentAction, ProcessDeclaration


class Agent:
    def reset(self, context):
        window = context.sensing_window
        assert window is None or (type(window) is int and window == 27), window
        self.label = f"w{window}"

    def declare_processes(self):
        return [ProcessDeclaration(self.label, 16, 1.0)]

    def act(self, observation):
        assert observation.previous_sense_anchors is None
        return AgentAction(ActionKindV2.READ, observation.own_core_base)


def create_agent():
    return Agent()
"""

# Senses toward the enemy anchor once, then echoes what it was delivered as the
# next action's operand: READ the first reported anchor, or READ 400 (an address
# out of reach) if nothing arrived. The trace's action operand is then proof of
# what crossed the executor.
ECHO_SOURCE = """\
from battle_engine.agent_api import ActionKindV2, AgentAction, ProcessDeclaration


class Agent:
    def reset(self, context):
        self.window = context.sensing_window
        self.calls = 0
        self.echoed = []

    def declare_processes(self):
        return [ProcessDeclaration("p", 64, 1.0)]

    def act(self, observation):
        self.calls += 1
        if self.calls == 1:
            return AgentAction(ActionKindV2.SENSE, 20)
        if self.calls == 2:
            seen = observation.previous_sense_anchors
            assert seen is None or type(seen) is tuple
            return AgentAction(ActionKindV2.READ, seen[0] if seen else 400)
        if self.calls == 3:
            return AgentAction(ActionKindV2.SENSE, 300)
        if self.calls == 4:
            seen = observation.previous_sense_anchors
            return AgentAction(ActionKindV2.READ, 401 if seen is None else 402 + len(seen))
        return AgentAction(ActionKindV2.READ, observation.self_anchor)


def create_agent():
    return Agent()
"""

# Senses only when the context offers a window, on a mix of targets: some
# within reach of an enemy anchor or not, some out of reach.
GATED_SOURCE = """\
from battle_engine.agent_api import ActionKindV2, AgentAction, ProcessDeclaration


class Agent:
    def reset(self, context):
        self.window = context.sensing_window
        self.calls = 0

    def declare_processes(self):
        return [ProcessDeclaration("p", 64, 1.0)]

    def act(self, observation):
        self.calls += 1
        if self.window is not None and self.calls % 3:
            return AgentAction(ActionKindV2.SENSE, observation.self_anchor + 25 * (self.calls % 4))
        return AgentAction(ActionKindV2.MOVE, 16)


def create_agent():
    return Agent()
"""


def _write(root: Path, name: str, source: str) -> None:
    agent_dir = root / "agents" / name
    agent_dir.mkdir(parents=True, exist_ok=True)
    (agent_dir / "agent.yaml").write_text(json.dumps({
        "name": name, "kind": "python", "api_version": 2, "entrypoint": "agent.py:create_agent", "version": "1.0.0",
    }), encoding="utf-8")
    (agent_dir / "agent.py").write_text(source, encoding="utf-8")


def _loaded_match(root: Path, policy: RulesetPolicy, sources: tuple[str, str], starts: tuple[int, int], *,
                  worker: bool, ticks: int = 2) -> tuple[ProcessMatchController, list[dict]]:
    for seat, source in zip(("a", "b"), sources, strict=True):
        _write(root, f"agent_{seat}", source)
    path = root / "trace.jsonl"
    writer = TraceWriter(path)
    writer.write_header(TraceHeader(match_seed=3, agents={"A": "agent_a", "B": "agent_b"}, supervised=worker,
                                    schema_version=TRACE_SCHEMA_VERSION_V2))
    with hang_safety_timeout(120):
        controller = ProcessMatchController.from_python_entrants(
            Config(seed=3, arena_size=512, instr_per_tick=8),
            (MatchEntrant.python("A", "agent_a", starts[0], resolve_agent(root, "agent_a")),
             MatchEntrant.python("B", "agent_b", starts[1], resolve_agent(root, "agent_b"))), ticks,
            ruleset_policy=policy, agent_call_timeout=WORKER_TIMEOUT if worker else None, trace_writer=writer)
        try:
            controller.run()
        finally:
            controller.close()
            writer.close()
    return controller, trace_records(path)


# ---------------------------------------------------------------------------
# The fields
# ---------------------------------------------------------------------------


def test_the_context_field_is_additive_last_and_defaults_to_none() -> None:
    names = [field.name for field in fields(MatchContextV2)]
    assert names[-2:] == ["detection_radius", "sensing_window"]
    context = MatchContextV2(agent_id="A", seed=1, arena_size=512, tick_limit=10, rng=random.Random(1))
    assert context.sensing_window is None
    with pytest.raises(FrozenInstanceError):
        context.sensing_window = 27  # type: ignore[misc]


def test_the_observation_field_is_additive_last_and_defaults_to_none() -> None:
    assert [field.name for field in fields(ObservationV2)][-1] == "previous_sense_anchors"
    observation = ObservationV2(current_tick=1, last_callback_tick=0, previous_action_tick=0, self_process_id="p",
                                self_anchor=0, self_reach=1, own_core_base=0, own_core_size=8,
                                visible_enemy_anchor_addresses=(), previous_action_applied=False,
                                previous_read_value=None, previous_read_owner=None)
    assert observation.previous_sense_anchors is None


def test_a_validation_dry_run_has_no_window() -> None:
    from battle_engine.agent_api import ProcessDeclaration

    assert build_validation_context().sensing_window is None
    assert build_validation_observation(declaration=ProcessDeclaration("p", 8, 1.0)).previous_sense_anchors is None


# ---------------------------------------------------------------------------
# Delivery under both executors
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("worker", [False, True], ids=["direct", "worker"])
@pytest.mark.parametrize("ruleset_id", sorted(_RULESET_POLICIES))
def test_every_registered_ruleset_delivers_its_own_window(tmp_path: Path, ruleset_id: str, worker: bool) -> None:
    policy = resolve_ruleset_policy(ruleset_id)
    active_ids = {*E8_IDS, "bytefray-rules-6-alpha1"}
    expected = "w27" if ruleset_id in active_ids else "wNone"
    controller, records = _loaded_match(tmp_path, policy, (REPORTER_SOURCE, REPORTER_SOURCE), (0, 256),
                                        worker=worker, ticks=1)
    assert [spec.processes[0].process_id for spec in controller.entrant_specs] == [expected, expected]
    resets = [r for r in records if r["record_type"] == "reset"]
    assert len(resets) == 2
    for reset in resets:
        assert reset.get("sensing_window", "<absent>") == (27 if ruleset_id in active_ids else "<absent>")


def test_a_worker_reset_without_the_key_delivers_none(tmp_path: Path) -> None:
    _write(tmp_path, "reporter", REPORTER_SOURCE)
    handle = AgentWorkerHandle(agent_id="A", slot=0)
    with hang_safety_timeout(60):
        try:
            handle.start()
            assert handle.load(resolve_agent(tmp_path, "reporter"), timeout=WORKER_TIMEOUT).status is WorkerCallStatus.OK
            reset = handle._call({"cmd": "reset", "match_seed": 1, "api_version": 2, "arena_size": 512,
                                  "tick_limit": 5, "action_budget": 8}, timeout=WORKER_TIMEOUT)
            assert reset.status is WorkerCallStatus.OK
            declared = handle.declare_processes(timeout=WORKER_TIMEOUT)
            assert declared.payload is not None and [i["id"] for i in declared.payload["declarations"]] == ["wNone"]
            assert handle.reset(match_seed=1, api_version=2, arena_size=512, tick_limit=5, action_budget=8,
                                timeout=WORKER_TIMEOUT, sensing_window=27).status is WorkerCallStatus.OK
            declared = handle.declare_processes(timeout=WORKER_TIMEOUT)
            assert declared.payload is not None and [i["id"] for i in declared.payload["declarations"]] == ["w27"]
        finally:
            handle.close()


@pytest.mark.parametrize("worker", [False, True], ids=["direct", "worker"])
@pytest.mark.parametrize("ruleset_id", E8_IDS)
def test_a_sense_result_crosses_either_executor(tmp_path: Path, ruleset_id: str, worker: bool) -> None:
    # A's process is at 0 (reach 64), B's at 40. SENSE at 20 finds B's anchor;
    # SENSE at 300 is out of reach. The echoes prove what reached the agent: an
    # anchor tuple, then None after the refusal.
    _, records = _loaded_match(tmp_path, resolve_ruleset_policy(ruleset_id), (ECHO_SOURCE, REPORTER_SOURCE),
                               (0, 40), worker=worker)
    a = [r for r in records if r["record_type"] == "decision_v2" and r["agent_id"] == "A"]
    assert a[0]["applied_result"]["sensed_anchors"] == [40]
    assert a[1]["observation"]["previous_sense_anchors"] == [40]
    assert a[1]["action"] == {"kind": "read", "operand": 40, "value": None}  # delivered as the tuple (40,)
    assert a[2]["applied_result"] == {"status": "REJECTED_OUT_OF_REACH", "normalized_address": None,
                                      "read_value": None, "read_owner": None, "sensed_anchors": None}
    assert a[3]["observation"]["previous_sense_anchors"] is None
    assert a[3]["action"]["operand"] == 401  # delivered as None
    assert presence_problems(records, active=True) == []


# ---------------------------------------------------------------------------
# The development-test path (agent_test.test_agent), as the E8 harness will run it
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("ruleset_id", [*CONTROL_IDS, *E8_IDS])
def test_a_development_test_trace_follows_the_presence_contract(tmp_path: Path, ruleset_id: str) -> None:
    _write(tmp_path, "gated_a", GATED_SOURCE)
    _write(tmp_path, "gated_b", GATED_SOURCE)
    with hang_safety_timeout(120):
        outcome = agent_test.test_agent(
            "gated_a", opponent="gated_b", seed=1, ticks=30, timeout=None, trace=True, run_dir=tmp_path / "cell",
            data_root=tmp_path, ruleset_id=ruleset_id, agent_start=None, opponent_start=None, arena_size=512,
            instr_per_tick=None, locality_reach=None, kill_weight=None, scheduler_chunk_size=None,
            scheduler_rotate_start=None)
    assert isinstance(outcome, DevelopmentTestOutcome) and outcome.trace_path is not None
    records = trace_records(outcome.trace_path)
    active = ruleset_id in E8_IDS
    assert presence_problems(records, active=active) == []
    kinds = [r["record_type"] for r in records]
    assert kinds[0] == "header" and kinds[-1] == "binding" and kinds.count("reset") == 2
    if active:
        results = [r["applied_result"] for r in records if r["record_type"] == "decision_v2"
                   and (r["action"] or {}).get("kind") == "sense"]
        assert {result["status"] for result in results} == {"APPLIED", "REJECTED_OUT_OF_REACH"}
        assert any(result["sensed_anchors"] == [] for result in results)
    else:
        assert e8_keys_in(outcome.trace_path.read_text(encoding="utf-8").splitlines()) == []
