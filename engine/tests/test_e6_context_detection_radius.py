"""V6 E6: ``MatchContextV2.detection_radius`` -- the public sensing radius.

docs/research/v6/V6_E6_PRICED_SENSING_IMPLEMENTATION_PLAN.md Sec 3.4 and Sec 4
("Context"); design review Sec M, decision 3 (the radius is public). The
field is additive and last, with a ``None`` default, exactly like
``parameters``: not an Agent API version change. Under an E6 treatment both
the direct and the worker executor hand the agent ``32``; under every other
Ruleset, and in a validation dry run, ``None``.

The reporting agent below encodes what its ``reset()`` received into its
declared process ID, which the controller then holds; no match outcome is
involved.
"""

from __future__ import annotations

import json
import random
from dataclasses import FrozenInstanceError, fields
from pathlib import Path
from types import MappingProxyType

import pytest
from _hang_safety import hang_safety_timeout
from battle_engine.agent_api import MatchContextV2
from battle_engine.agent_validation import build_validation_context
from battle_engine.agent_worker import AgentWorkerHandle, WorkerCallStatus
from battle_engine.agents import resolve_agent
from battle_engine.config import Config
from battle_engine.match_service import MatchEntrant, MatchRequest, NativeMatchService
from battle_engine.process_runtime import ProcessMatchController
from battle_engine.replay import TickSnapshot, iter_replay
from battle_engine.ruleset_policy import (
    _RULESET_POLICIES,
    BYTEFRAY_RULESET_V6_RESEARCH_DISRUPTION_SLOT1_SENSING_R32_ID,
    BYTEFRAY_RULESET_V6_RESEARCH_SENSING_R32_ID,
    RulesetPolicy,
    resolve_ruleset_policy,
)

E6_IDS = (BYTEFRAY_RULESET_V6_RESEARCH_SENSING_R32_ID, BYTEFRAY_RULESET_V6_RESEARCH_DISRUPTION_SLOT1_SENSING_R32_ID)
WORKER_TIMEOUT = 30.0

REPORTER_SOURCE = """\
from battle_engine.agent_api import ActionKindV2, AgentAction, ProcessDeclaration


class Agent:
    def reset(self, context):
        radius = context.detection_radius
        assert radius is None or (type(radius) is int and radius >= 1), radius
        self.label = f"r{radius}"

    def declare_processes(self):
        return [ProcessDeclaration(self.label, 16, 1.0)]

    def act(self, observation):
        return AgentAction(ActionKindV2.READ, observation.own_core_base)


def create_agent():
    return Agent()
"""


def _write_reporter(root: Path, name: str = "reporter") -> None:
    agent_dir = root / "agents" / name
    agent_dir.mkdir(parents=True, exist_ok=True)
    (agent_dir / "agent.yaml").write_text(json.dumps({
        "name": name, "kind": "python", "api_version": 2, "entrypoint": "agent.py:create_agent", "version": "1.0.0",
    }), encoding="utf-8")
    (agent_dir / "agent.py").write_text(REPORTER_SOURCE, encoding="utf-8")


def _entrants(root: Path) -> tuple[MatchEntrant, ...]:
    _write_reporter(root, "reporter_a")
    _write_reporter(root, "reporter_b")
    return (MatchEntrant.python("A", "reporter_a", 0, resolve_agent(root, "reporter_a")),
            MatchEntrant.python("B", "reporter_b", 256, resolve_agent(root, "reporter_b")))


def _delivered(root: Path, policy: RulesetPolicy, *, worker: bool) -> list[str]:
    """What each entrant's reset() received, as the process IDs it declared."""

    with hang_safety_timeout(120):
        controller = ProcessMatchController.from_python_entrants(
            Config(seed=3, arena_size=512, instr_per_tick=8), _entrants(root), 5, ruleset_policy=policy,
            agent_call_timeout=WORKER_TIMEOUT if worker else None)
        try:
            return [spec.processes[0].process_id for spec in controller.entrant_specs]
        finally:
            controller.close()


# ---------------------------------------------------------------------------
# The field
# ---------------------------------------------------------------------------


def test_the_field_is_additive_last_and_defaults_to_none() -> None:
    names = [field.name for field in fields(MatchContextV2)]
    assert names == ["agent_id", "seed", "arena_size", "tick_limit", "rng", "parameters", "detection_radius"]
    # Keyword construction without it -- every agent and tool written before
    # E6 -- is unaffected.
    context = MatchContextV2(agent_id="A", seed=1, arena_size=512, tick_limit=10, rng=random.Random(1))
    assert context.detection_radius is None
    assert context.parameters == MappingProxyType({})
    assert MatchContextV2(agent_id="A", seed=1, arena_size=512, tick_limit=10, rng=random.Random(1),
                          detection_radius=32).detection_radius == 32
    with pytest.raises(FrozenInstanceError):
        context.detection_radius = 32  # type: ignore[misc]


def test_a_validation_dry_run_has_no_radius() -> None:
    assert build_validation_context().detection_radius is None


# ---------------------------------------------------------------------------
# Delivery under both executors
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("worker", [False, True], ids=["direct", "worker"])
@pytest.mark.parametrize("ruleset_id", sorted(_RULESET_POLICIES))
def test_every_registered_ruleset_delivers_its_own_radius(tmp_path: Path, ruleset_id: str, worker: bool) -> None:
    policy = resolve_ruleset_policy(ruleset_id)
    expected = "r32" if ruleset_id in E6_IDS else "rNone"
    assert policy.detection_radius == (32 if ruleset_id in E6_IDS else None)
    assert _delivered(tmp_path, policy, worker=worker) == [expected, expected]


@pytest.mark.parametrize("worker", [False, True], ids=["direct", "worker"])
@pytest.mark.parametrize("radius", [1, 7, 255])
def test_the_delivered_value_is_the_policys_not_a_constant(tmp_path: Path, radius: int, worker: bool) -> None:
    policy = RulesetPolicy(ruleset_id="test-only", scheduler_mode="chunked", scheduler_chunk_size=2,
                           scheduler_rotate_start=True, core_placement="seeded", process_selection="round_robin",
                           detection_radius=radius)
    assert _delivered(tmp_path, policy, worker=worker) == [f"r{radius}", f"r{radius}"]


def test_a_worker_reset_without_the_key_delivers_none(tmp_path: Path) -> None:
    # The wire key is additive and read back through .get(): a reset request
    # that predates it resets the agent with None.
    _write_reporter(tmp_path)
    handle = AgentWorkerHandle(agent_id="A", slot=0)
    with hang_safety_timeout(60):
        try:
            handle.start()
            assert handle.load(resolve_agent(tmp_path, "reporter"), timeout=WORKER_TIMEOUT).status is WorkerCallStatus.OK
            reset = handle._call({"cmd": "reset", "match_seed": 1, "api_version": 2, "arena_size": 512,
                                  "tick_limit": 5, "action_budget": 8}, timeout=WORKER_TIMEOUT)
            assert reset.status is WorkerCallStatus.OK
            declared = handle.declare_processes(timeout=WORKER_TIMEOUT)
            assert declared.status is WorkerCallStatus.OK and declared.payload is not None
            assert [item["id"] for item in declared.payload["declarations"]] == ["rNone"]
            # ...and the handle sends it when given one.
            assert handle.reset(match_seed=1, api_version=2, arena_size=512, tick_limit=5, action_budget=8,
                                timeout=WORKER_TIMEOUT, detection_radius=32).status is WorkerCallStatus.OK
            declared = handle.declare_processes(timeout=WORKER_TIMEOUT)
            assert declared.payload is not None
            assert [item["id"] for item in declared.payload["declarations"]] == ["r32"]
        finally:
            handle.close()


@pytest.mark.parametrize("supervised", [False, True], ids=["direct", "worker"])
@pytest.mark.parametrize("ruleset_id", E6_IDS)
def test_a_native_match_under_a_treatment_delivers_32(tmp_path: Path, ruleset_id: str, supervised: bool) -> None:
    replay = tmp_path / "run" / "replay.jsonl"
    with hang_safety_timeout(120):
        NativeMatchService().run(MatchRequest(
            config=Config(seed=3, arena_size=512, instr_per_tick=8), entrants=_entrants(tmp_path), max_ticks=2,
            replay_path=replay, verbose=False, ruleset_id=ruleset_id,
            agent_call_timeout=WORKER_TIMEOUT if supervised else None))
    tick0 = next(record for record in iter_replay(replay) if isinstance(record, TickSnapshot))
    assert {process.process_id for process in tick0.processes} == {"r32"}
