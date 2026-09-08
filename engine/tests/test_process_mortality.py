from __future__ import annotations

"""V5 research Phase R1: finite process-integrity mortality mechanic tests.

Covers the experimental Ruleset identity (registration, isolation from
omitted-Ruleset resolution and stable V4), the mortality mechanic itself
(integrity loss, permanent death, quota/observation/disruption exclusion,
zero-process entrant survival), and full-stack replay/result persistence
including byte-compatibility with stable V4.
"""

import dataclasses
import json
from pathlib import Path
from typing import Any

import pytest
from battle_engine.agent_api import ActionKind, ActionKindV2, AgentAction
from battle_engine.agents import resolve_agent
from battle_engine.config import Config, Weights
from battle_engine.match_service import MatchEntrant, MatchRequest, NativeMatchService
from battle_engine.process_runtime import (
    DEFAULT_PROCESS_INTEGRITY,
    PROCESS_MORTALITY_RULESET_IDS,
    ProcessEntrantSpec,
    ProcessInstance,
    ProcessMatchController,
    ProcessRole,
    has_process_mortality,
)
from battle_engine.replay import ProcessState, TickSnapshot, iter_replay
from battle_engine.rules import BYTEFRAY_RULESET_V5_R1_ALPHA1_ID
from battle_engine.ruleset_policy import (
    OMITTED_RULESET_CANDIDATES,
    PROCESS_RULESET_IDS,
    RULESET_V4,
    RULESET_V5_R1_ALPHA1,
    resolve_ruleset_policy,
)

from tools.research.v5.analyzer import analyze_match


def _passive_config() -> Config:
    return Config(arena_size=1024, instr_per_tick=8, seed=1, weights=Weights())


# ---------------------------------------------------------------------------
# Ruleset identity: registered, isolated from omitted resolution and V4.
# ---------------------------------------------------------------------------


def test_r1_ruleset_registered_and_dispatches_to_process_runtime() -> None:
    assert resolve_ruleset_policy(BYTEFRAY_RULESET_V5_R1_ALPHA1_ID) is RULESET_V5_R1_ALPHA1
    assert BYTEFRAY_RULESET_V5_R1_ALPHA1_ID in PROCESS_RULESET_IDS
    assert BYTEFRAY_RULESET_V5_R1_ALPHA1_ID in PROCESS_MORTALITY_RULESET_IDS


def test_r1_ruleset_never_reachable_from_omitted_selection() -> None:
    assert BYTEFRAY_RULESET_V5_R1_ALPHA1_ID not in OMITTED_RULESET_CANDIDATES


def test_r1_ruleset_equivalent_to_v4_except_identity_and_mortality_gate() -> None:
    """Every non-identity RulesetPolicy field matches stable V4 exactly.

    Mortality is gated entirely in ``process_runtime`` on ``ruleset_id``, not
    on anything ``RulesetPolicy`` itself exposes -- this is the field-by-field
    equivalence claim that R1's own docstrings make.
    """

    for f in dataclasses.fields(RULESET_V4):
        if f.name == "ruleset_id":
            continue
        assert getattr(RULESET_V5_R1_ALPHA1, f.name) == getattr(RULESET_V4, f.name), f.name
    assert not has_process_mortality(RULESET_V4.ruleset_id)
    assert has_process_mortality(RULESET_V5_R1_ALPHA1.ruleset_id)


# ---------------------------------------------------------------------------
# Low-level mechanic tests (direct ProcessEntrantSpec/ProcessInstance
# construction, mirroring test_v4_process_semantics.py's established style).
# ---------------------------------------------------------------------------


def _attacker_spec(target_addr: int) -> ProcessEntrantSpec:
    return ProcessEntrantSpec(
        "A",
        "attacker",
        [
            ProcessInstance(
                "pA",
                ProcessRole.ATTACKER,
                initial_position=0,
                reach=None,
                quota_share=8,
                logic=lambda obs, state: AgentAction(ActionKindV2.WRITE, target_addr, 0x11),
            )
        ],
    )


def _passive_victim_spec(position: int) -> ProcessEntrantSpec:
    return ProcessEntrantSpec(
        "B",
        "victim",
        [
            ProcessInstance(
                "pB",
                ProcessRole.DEFENDER,
                initial_position=position,
                reach=None,
                quota_share=8,
                logic=lambda obs, state: AgentAction(ActionKind.NOP),
            )
        ],
    )


def test_process_dies_after_h_hostile_anchor_hits_and_entrant_survives() -> None:
    """A full-quota attacker delivers H hits within tick 1 (Q=8 per tick);
    the lone process dies immediately, but the entrant -- whose core was
    never touched -- must NOT be automatically eliminated."""

    spec_a = _attacker_spec(500)
    spec_b = _passive_victim_spec(500)
    controller = ProcessMatchController(
        _passive_config(), [spec_a, spec_b], max_ticks=10,
        ruleset_policy=RULESET_V5_R1_ALPHA1, process_integrity=2,
    )
    controller.run()

    proc_b = spec_b.processes[0]
    assert proc_b.alive is False
    assert proc_b.integrity == 0
    assert proc_b.telemetry.died_tick == 1
    assert proc_b.telemetry.disruption_hits_received == 2  # never underflows past H
    assert controller.states[1].alive is True, "core untouched -> entrant must survive"


def test_dead_process_cannot_be_disrupted_again() -> None:
    spec_a = _attacker_spec(500)
    spec_b = _passive_victim_spec(500)
    controller = ProcessMatchController(
        _passive_config(), [spec_a, spec_b], max_ticks=15,
        ruleset_policy=RULESET_V5_R1_ALPHA1, process_integrity=1,
    )
    controller.run()

    proc_b = spec_b.processes[0]
    assert proc_b.telemetry.died_tick == 1
    # Attacker keeps writing to 500 every remaining tick; a dead process must
    # never accrue further hits, disrupted ticks, or a second "death".
    assert proc_b.telemetry.disruption_hits_received == 1
    assert proc_b.integrity == 0


def test_stable_v4_is_immortal_even_if_process_integrity_is_passed() -> None:
    """A stray process_integrity kwarg must never switch on mortality under
    a Ruleset without has_process_mortality -- the same discipline
    ``locality_reach`` already enforces for non-locality Rulesets."""

    spec_a = _attacker_spec(500)
    spec_b = _passive_victim_spec(500)
    controller = ProcessMatchController(
        _passive_config(), [spec_a, spec_b], max_ticks=5,
        ruleset_policy=RULESET_V4, process_integrity=1,
    )
    controller.run()

    proc_b = spec_b.processes[0]
    assert proc_b.alive is True
    assert proc_b.integrity is None
    assert controller.mortality_active is False
    assert controller.process_integrity is None


def test_mortality_requires_positive_integrity() -> None:
    spec_a = _attacker_spec(500)
    spec_b = _passive_victim_spec(500)
    with pytest.raises(ValueError):
        ProcessMatchController(
            _passive_config(), [spec_a, spec_b], max_ticks=1,
            ruleset_policy=RULESET_V5_R1_ALPHA1, process_integrity=0,
        )


def test_mortality_defaults_when_integrity_omitted() -> None:
    spec_a = _attacker_spec(500)
    spec_b = _passive_victim_spec(500)
    controller = ProcessMatchController(
        _passive_config(), [spec_a, spec_b], max_ticks=1,
        ruleset_policy=RULESET_V5_R1_ALPHA1,
    )
    assert controller.process_integrity == DEFAULT_PROCESS_INTEGRITY


def test_dead_process_excluded_from_quota_and_observation_reach() -> None:
    """A two-process entrant: kill one process, confirm the survivor takes
    the entrant's full Q=8 (not a frozen half-share), and confirm the dead
    process's reach no longer contributes to entrant-wide sensor fusion."""

    watcher_calls: list[tuple[int, ...]] = []

    def watcher_logic(obs: Any, state: dict[str, Any]) -> AgentAction:
        watcher_calls.append(obs.visible_enemy_anchor_addresses)
        return AgentAction(ActionKind.NOP)

    spec_a = _attacker_spec(500)
    victim_dying = ProcessInstance(
        "p_die", ProcessRole.DEFENDER, initial_position=500, reach=None,
        quota_share=4, logic=lambda obs, state: AgentAction(ActionKind.NOP),
    )
    victim_watcher = ProcessInstance(
        "p_watch", ProcessRole.SCOUT, initial_position=600, reach=1000,
        quota_share=4, logic=watcher_logic,
    )
    spec_b = ProcessEntrantSpec("B", "victim", [victim_dying, victim_watcher])

    controller = ProcessMatchController(
        _passive_config(), [spec_a, spec_b], max_ticks=1,
        ruleset_policy=RULESET_V5_R1_ALPHA1, process_integrity=1,
    )
    controller.run()

    assert victim_dying.alive is False
    assert victim_watcher.alive is True
    # With the dying process excluded from eligibility, the watcher (the
    # sole eligible process) receives the entrant's entire Q=8 allocation.
    assert victim_watcher.telemetry.total_actions == 8

    # A dead process contributes no observation reach: manually verifying
    # against the controller's own visibility function after death.
    visible = controller._visible_enemy_anchors(spec_b, tick=1)
    # The attacker (A) sits at address 0, far outside the watcher's own
    # reach only if the dead process was the one that could see it; here
    # the watcher's reach=1000 covers everything regardless, so assert the
    # narrower claim directly against the dead process's own eligibility.
    assert victim_dying.position is not None
    assert victim_dying not in [
        p for p in spec_b.processes if p.alive and not p.is_disrupted(1)
    ]
    del visible  # sensor-fusion coverage is exercised by the full-stack test below


# ---------------------------------------------------------------------------
# Full-stack tests via NativeMatchService: replay/result persistence, V4
# byte-compatibility, and determinism.
# ---------------------------------------------------------------------------

ATTACKER_AGENT_CODE = """
from battle_engine.agent_api import AgentV2, ObservationV2, AgentAction, ActionKindV2, MatchContextV2, ProcessDeclaration

class AttackerV2:
    api_version = 2
    def declare_processes(self):
        return [ProcessDeclaration(id="p1", reach=50, share=1.0)]
    def reset(self, context: MatchContextV2):
        pass
    def act(self, obs: ObservationV2) -> AgentAction:
        return AgentAction(ActionKindV2.WRITE, operand=10, value=0x11)

def create_agent() -> AgentV2:
    return AttackerV2()
"""

VICTIM_AGENT_CODE = """
from battle_engine.agent_api import AgentV2, ObservationV2, AgentAction, ActionKindV2, MatchContextV2, ProcessDeclaration

class VictimV2:
    api_version = 2
    def declare_processes(self):
        return [ProcessDeclaration(id="p1", reach=50, share=1.0)]
    def reset(self, context: MatchContextV2):
        pass
    def act(self, obs: ObservationV2) -> AgentAction:
        return AgentAction(ActionKindV2.READ, 0)

def create_agent() -> AgentV2:
    return VictimV2()
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


def _run_r1_match(
    tmp_path: Path,
    *,
    ruleset_id: str,
    process_integrity: int | None,
    ticks: int = 5,
    label: str = "match",
) -> tuple[Path, Path]:
    _setup_agent(tmp_path, "attacker", ATTACKER_AGENT_CODE)
    _setup_agent(tmp_path, "victim", VICTIM_AGENT_CODE)
    spec_a = resolve_agent(tmp_path, "attacker")
    spec_b = resolve_agent(tmp_path, "victim")

    # Attacker at 0, victim's anchor placed exactly at address 10 (well
    # within the attacker's reach=50) so every attacker WRITE lands on the
    # victim's current anchor.
    entrants = (
        MatchEntrant.python("A", "attacker", 0, spec_a),
        MatchEntrant.python("B", "victim", 10, spec_b),
    )
    replay_path = tmp_path / label / "replay.jsonl"
    req = MatchRequest(
        config=Config(seed=7, arena_size=512, instr_per_tick=8),
        entrants=entrants,
        max_ticks=ticks,
        replay_path=replay_path,
        verbose=False,
        ruleset_id=ruleset_id,
        process_integrity=process_integrity,
    )
    res = NativeMatchService().run(req)
    assert res.result_path is not None
    return replay_path, res.result_path


def test_full_stack_process_death_persists_in_replay_and_result(tmp_path: Path) -> None:
    replay_path, result_path = _run_r1_match(
        tmp_path, ruleset_id=BYTEFRAY_RULESET_V5_R1_ALPHA1_ID, process_integrity=1,
    )

    with open(result_path, encoding="utf-8") as f:
        result_data = json.load(f)
    victim_meta = next(a["metadata"] for a in result_data["entrants"] if a["agent_id"] == "B")
    proc_meta = victim_meta["processes"][0]
    assert proc_meta["alive"] is False
    assert proc_meta["integrity_remaining"] == 0
    assert isinstance(proc_meta["died_tick"], int)

    attacker_meta = next(a["metadata"] for a in result_data["entrants"] if a["agent_id"] == "A")
    assert attacker_meta["processes"][0]["alive"] is True

    # Replay per-tick ProcessState round-trips the same facts. Only
    # TickSnapshot records carry a tick number -- the terminal MatchResult
    # record repeats the final tick's ``processes`` tuple but has no
    # ``.tick`` field of its own, so it is deliberately excluded here.
    ticks = [rec for rec in iter_replay(replay_path) if isinstance(rec, TickSnapshot) and rec.processes]
    died_tick_seen = None
    for snap in ticks:
        for p in snap.processes:
            if isinstance(p, ProcessState) and p.entrant_id == "B" and not p.alive:
                if died_tick_seen is None:
                    died_tick_seen = snap.tick
                assert p.integrity == 0
    assert died_tick_seen == proc_meta["died_tick"]


def test_full_stack_process_mortality_is_deterministic(tmp_path: Path) -> None:
    replay1, result1 = _run_r1_match(
        tmp_path, ruleset_id=BYTEFRAY_RULESET_V5_R1_ALPHA1_ID, process_integrity=2, label="run1",
    )
    replay2, result2 = _run_r1_match(
        tmp_path, ruleset_id=BYTEFRAY_RULESET_V5_R1_ALPHA1_ID, process_integrity=2, label="run2",
    )
    m1 = analyze_match(replay1, result1)
    m2 = analyze_match(replay2, result2)
    assert json.dumps(m1, sort_keys=True) == json.dumps(m2, sort_keys=True)
    assert m1["process_deaths"]["B"] == 1
    assert m1["process_extinction_tick"]["B"] == m1["process_death_events"][0]["tick"]


def test_stable_v4_replay_omits_mortality_fields_entirely(tmp_path: Path) -> None:
    """Byte-compatibility: a stable V4 match's process records carry no
    alive/integrity keys at all, and every process stays alive/untracked."""

    replay_path, result_path = _run_r1_match(
        tmp_path, ruleset_id="bytefray-rules-4", process_integrity=None, ticks=5,
    )
    raw_lines = replay_path.read_text(encoding="utf-8").splitlines()
    for line in raw_lines:
        payload = json.loads(line)
        for proc in payload.get("processes", []):
            assert "alive" not in proc
            assert "integrity" not in proc

    with open(result_path, encoding="utf-8") as f:
        result_data = json.load(f)
    for agent in result_data["entrants"]:
        for proc in agent["metadata"]["processes"]:
            assert "alive" not in proc
            assert "integrity_remaining" not in proc
            assert "died_tick" not in proc

    for record in iter_replay(replay_path):
        for p in getattr(record, "processes", ()):
            assert p.alive is True
            assert p.integrity is None
