from __future__ import annotations

"""Bytefray V5 Alpha 1 — Phase B Engine Hygiene & Isolation Tests.

Validates the complete removal and isolation of rejected R1/R2 experimental
mechanics (finite process mortality, objective-target oracle, and experimental
rulesets) from the production engine while verifying stable V4 behavior, passive
replay compatibility, and 5.0.0a1 version transition.
"""

import re
from importlib.metadata import version as distribution_version
from pathlib import Path
from typing import Any

import pytest
from battle_engine.agent_api import (
    ActionKindV2,
    AgentAction,
    AgentV2,
    MatchContextV2,
    ObservationV2,
    ProcessDeclaration,
)
from battle_engine.config import Config, Weights
from battle_engine.match_service import MatchEntrant, MatchRequest
from battle_engine.process_runtime import (
    ProcessEntrantSpec,
    ProcessInstance,
    ProcessMatchController,
    ProcessRole,
)
from battle_engine.replay import ProcessState, _process_from_dict, _process_to_dict
from battle_engine.rules import (
    BYTEFRAY_RULESET_V4_ID,
)
from battle_engine.ruleset_policy import (
    PROCESS_RULESET_IDS,
    RULESET_V4,
    UnknownRulesetError,
    resolve_omitted_ruleset_for_agents,
    resolve_ruleset_policy,
)

ROOT = Path(__file__).resolve().parents[2]


class MinimalSitterAgent:
    api_version = 2

    def declare_processes(self) -> list[ProcessDeclaration]:
        return [ProcessDeclaration(id="p1", reach=10, share=1.0)]

    def reset(self, context: MatchContextV2) -> None:
        pass

    def act(self, obs: ObservationV2) -> AgentAction:
        return AgentAction(ActionKindV2.READ, 0)


def create_agent() -> AgentV2:
    return MinimalSitterAgent()


def test_rejected_rulesets_not_recognized_in_production() -> None:
    """R1 and R2 experimental rulesets must not resolve as valid rulesets."""
    rejected_ids = [
        "bytefray-rules-5-r1-alpha1",
        "bytefray-rules-5-r2-alpha1",
        "bytefray-rules-5",
    ]
    for r_id in rejected_ids:
        with pytest.raises(UnknownRulesetError):
            resolve_ruleset_policy(r_id)
        assert r_id not in PROCESS_RULESET_IDS


def test_stable_v4_ruleset_functional_and_default() -> None:
    """Stable bytefray-rules-4 resolves correctly and is registered."""
    policy = resolve_ruleset_policy(BYTEFRAY_RULESET_V4_ID)
    assert policy is RULESET_V4
    assert BYTEFRAY_RULESET_V4_ID in PROCESS_RULESET_IDS

    # Omitted ruleset resolves to stable V4 ID for API v2 entrants
    assert resolve_omitted_ruleset_for_agents(None, [{"kind": "python", "api_version": 2}]) == BYTEFRAY_RULESET_V4_ID


def test_match_request_rejects_experimental_kwargs() -> None:
    """MatchRequest must not have or accept process_integrity or objective_target_oracle."""
    config = Config(seed=42, arena_size=256, instr_per_tick=8)
    entrants = (
        MatchEntrant.python("A", "a", 0, None),
        MatchEntrant.python("B", "b", 64, None),
    )

    with pytest.raises(TypeError, match="unexpected keyword argument 'process_integrity'"):
        MatchRequest(
            config=config,
            entrants=entrants,
            max_ticks=10,
            process_integrity=8,  # type: ignore[call-arg]
        )

    with pytest.raises(TypeError, match="unexpected keyword argument 'objective_target_oracle'"):
        MatchRequest(
            config=config,
            entrants=entrants,
            max_ticks=10,
            objective_target_oracle=True,  # type: ignore[call-arg]
        )


def test_process_match_controller_rejects_experimental_kwargs() -> None:
    """ProcessMatchController must not accept process_integrity or objective_target_oracle."""
    config = Config(seed=42, arena_size=256, instr_per_tick=8, weights=Weights())
    specs = [
        ProcessEntrantSpec("A", "a", [
            ProcessInstance("pA", ProcessRole.GENERALIST, 0, 10, 8, lambda o, s: AgentAction(ActionKindV2.READ, 0))
        ], start=0),
        ProcessEntrantSpec("B", "b", [
            ProcessInstance("pB", ProcessRole.GENERALIST, 64, 10, 8, lambda o, s: AgentAction(ActionKindV2.READ, 0))
        ], start=64),
    ]

    with pytest.raises(TypeError):
        ProcessMatchController.from_python_entrants(  # type: ignore[call-arg]
            config, (), 10, process_integrity=8
        )

    with pytest.raises(TypeError):
        ProcessMatchController.from_python_entrants(  # type: ignore[call-arg]
            config, (), 10, objective_target_oracle=True
        )

    # Direct controller instances must not have experimental attributes
    controller = ProcessMatchController(config, specs, max_ticks=10)
    assert not hasattr(controller, "mortality_active")
    assert not hasattr(controller, "oracle_active")
    assert not hasattr(controller, "process_integrity")
    assert not hasattr(specs[0].processes[0], "integrity")
    assert not hasattr(specs[0].processes[0].telemetry, "died_tick")


def test_no_oracle_leak_in_visible_enemy_anchor_addresses() -> None:
    """Enemy core base is never appended or leaked into visible_enemy_anchor_addresses."""
    # A is at 0 with reach 5. B's core is at 100, B's process is at 100 (out of reach).
    # visible_enemy_anchor_addresses must be completely empty!
    seen_addresses: list[tuple[int, ...]] = []

    def observer_logic(obs: ObservationV2, state: dict[str, Any]) -> AgentAction:
        seen_addresses.append(obs.visible_enemy_anchor_addresses)
        return AgentAction(ActionKindV2.READ, 0)

    spec_a = ProcessEntrantSpec("A", "a", [
        ProcessInstance("pA", ProcessRole.SCOUT, 0, reach=5, quota_share=8, logic=observer_logic)
    ], start=0)
    spec_b = ProcessEntrantSpec("B", "b", [
        ProcessInstance("pB", ProcessRole.DEFENDER, 100, reach=5, quota_share=8,
                        logic=lambda o, s: AgentAction(ActionKindV2.READ, 0))
    ], start=100)

    config = Config(seed=1, arena_size=256, instr_per_tick=8, weights=Weights())
    controller = ProcessMatchController(config, [spec_a, spec_b], max_ticks=2)
    controller.run()

    assert len(seen_addresses) > 0
    for seen in seen_addresses:
        # Core base 100 must NOT appear in visible_enemy_anchor_addresses!
        assert 100 not in seen
        assert seen == ()


def test_replay_serialization_canonical_fields_only() -> None:
    """Replay process records only serialize the 5 canonical fields:
    process_id, entrant_id, anchor, disrupted, reach."""
    state = ProcessState(
        process_id="proc1",
        entrant_id="agentA",
        anchor=42,
        disrupted=False,
        reach=10,
        alive=False,  # even if set on dataclass
        integrity=3,   # even if set on dataclass
    )
    payload = _process_to_dict(state)
    assert set(payload.keys()) == {"process_id", "entrant_id", "anchor", "disrupted", "reach"}
    assert "alive" not in payload
    assert "integrity" not in payload


def test_replay_deserialization_passive_compatibility() -> None:
    """Replay reader tolerates historical replays containing alive or integrity fields."""
    legacy_payload = {
        "process_id": "proc1",
        "entrant_id": "agentA",
        "anchor": 42,
        "disrupted": True,
        "reach": 10,
        "alive": False,
        "integrity": 1,
    }
    state = _process_from_dict(legacy_payload)
    assert state.process_id == "proc1"
    assert state.entrant_id == "agentA"
    assert state.anchor == 42
    assert state.disrupted is True
    assert state.reach == 10
    assert state.alive is False
    assert state.integrity == 1


def test_version_transition_5_0_0a1() -> None:
    """Project version is 5.0.0a1 across pyproject.toml, installer.iss, and package metadata."""
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    installer = (ROOT / "tools" / "installer.iss").read_text(encoding="utf-8")

    proj_match = re.search(r'^version = "([^"]+)"$', pyproject, re.MULTILINE)
    app_match = re.search(r'^#define AppVersion "([^"]+)"$', installer, re.MULTILINE)
    tag_match = re.search(r'^#define ReleaseTag "([^"]+)"$', installer, re.MULTILINE)

    assert proj_match is not None
    assert app_match is not None
    assert tag_match is not None

    assert proj_match.group(1) == "5.0.0a1"
    assert app_match.group(1) == "5.0.0a1"
    assert tag_match.group(1) == "5.0.0a1"
    assert distribution_version("bytefray") == "5.0.0a1"
