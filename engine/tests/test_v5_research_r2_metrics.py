from __future__ import annotations

"""V5 research Phase R2: post-extinction follow-through metric tests.

These are the measurements R2's central question rests on -- "after a
defender's last process dies, does the attacker resume pressure on the
actual victory objective?" -- so every assertion below is derived from a
replay a real match actually produced, never from hand-built records, and
asserts exact values rather than mere non-emptiness.

The scenario is deliberately the smallest faithful reproduction of R1's
pathology: a hunter that acts only on the target-address channel, and a
victim whose sole process dies to the hunter's first hostile anchor hit.
With the oracle off this reproduces R1's stall; with it on it must not.
"""

import json
from pathlib import Path

from battle_engine.agents import resolve_agent
from battle_engine.config import Config
from battle_engine.match_service import MatchEntrant, MatchRequest, NativeMatchService
from battle_engine.rules import BYTEFRAY_RULESET_V5_R1_ALPHA1_ID

from tools.research.v5.analyzer import analyze_match

# Writes only where the target-address channel points, exactly like every
# bundled V4 attacker; alternates the written byte so a repeat write to the
# same address always produces an observable memory diff.
HUNTER_AGENT_CODE = """
from battle_engine.agent_api import AgentV2, ObservationV2, AgentAction, ActionKindV2, MatchContextV2, ProcessDeclaration

class HunterV2:
    api_version = 2
    def declare_processes(self):
        return [ProcessDeclaration(id="hunter", reach=50, share=1.0)]
    def reset(self, context: MatchContextV2):
        self.flip = 0
    def act(self, obs: ObservationV2) -> AgentAction:
        if obs.visible_enemy_anchor_addresses:
            self.flip = 1 - self.flip
            return AgentAction(
                ActionKindV2.WRITE,
                operand=obs.visible_enemy_anchor_addresses[0],
                value=0x40 + self.flip,
            )
        return AgentAction(ActionKindV2.READ, 0)

def create_agent() -> AgentV2:
    return HunterV2()
"""

VICTIM_AGENT_CODE = """
from battle_engine.agent_api import AgentV2, ObservationV2, AgentAction, ActionKindV2, MatchContextV2, ProcessDeclaration

class VictimV2:
    api_version = 2
    def declare_processes(self):
        return [ProcessDeclaration(id="sitter", reach=1, share=1.0)]
    def reset(self, context: MatchContextV2):
        pass
    def act(self, obs: ObservationV2) -> AgentAction:
        return AgentAction(ActionKindV2.READ, 0)

def create_agent() -> AgentV2:
    return VictimV2()
"""

HUNTER_START = 0
VICTIM_START = 20  # inside the hunter's reach=50, so its writes actually apply
MAX_TICKS = 40


def _setup_agent(tmp_path: Path, name: str, source: str) -> None:
    agent_dir = tmp_path / "agents" / name
    agent_dir.mkdir(parents=True, exist_ok=True)
    (agent_dir / "agent.py").write_text(source, encoding="utf-8")
    (agent_dir / "agent.yaml").write_text(
        f"name: {name}\ndescription: Test agent\nversion: '1.0'\napi_version: 2\n",
        encoding="utf-8",
    )


def _run(
    tmp_path: Path,
    *,
    ruleset_id: str,
    oracle: bool,
    process_integrity: int | None,
    label: str,
) -> dict:
    _setup_agent(tmp_path, "hunter", HUNTER_AGENT_CODE)
    _setup_agent(tmp_path, "victim", VICTIM_AGENT_CODE)
    entrants = (
        MatchEntrant.python("A", "hunter", HUNTER_START, resolve_agent(tmp_path, "hunter")),
        MatchEntrant.python("B", "victim", VICTIM_START, resolve_agent(tmp_path, "victim")),
    )
    replay_path = tmp_path / label / "replay.jsonl"
    request = MatchRequest(
        config=Config(seed=3, arena_size=512, instr_per_tick=8),
        entrants=entrants,
        max_ticks=MAX_TICKS,
        replay_path=replay_path,
        verbose=False,
        ruleset_id=ruleset_id,
        process_integrity=process_integrity,
        objective_target_oracle=oracle,
    )
    result = NativeMatchService().run(request)
    assert result.result_path is not None
    return analyze_match(replay_path, result.result_path)


def test_post_extinction_pressure_is_zero_without_the_oracle(tmp_path: Path) -> None:
    """R1's pathology, reproduced as a measured fact: the victim's process
    dies, the victim survives with an intact core, and the attacker lands
    nothing on the objective for the rest of the match."""

    m = _run(
        tmp_path, ruleset_id=BYTEFRAY_RULESET_V5_R1_ALPHA1_ID,
        oracle=False, process_integrity=1, label="no_oracle",
    )

    # Precondition: the pathology's setup actually occurred in this match.
    extinction_tick = m["process_extinction_tick"]["B"]
    assert extinction_tick == 1, "victim's sole process must die on tick 1"
    assert m["core_capture_outcome"]["B"] == "survived"
    # Zero-process ticks are counted inclusively from the extinction tick.
    assert m["entrant_zero_process_ticks"]["B"] == MAX_TICKS - extinction_tick + 1

    # The finding itself: across 40 ticks the attacker lands exactly one core
    # write -- the tick-1 hit that killed the process -- and nothing after.
    assert m["core_attack_writes"]["A"] == 1
    assert m["post_extinction_core_attack_writes"]["B"] == 0
    assert m["post_extinction_core_ownership_losses"]["B"] == 0
    assert m["ticks_extinction_to_first_core_attack"]["B"] is None
    assert m["target_loss_interval_ticks"]["B"] is None
    assert m["attacker_resumes_objective_pressure"]["B"] is False


def test_post_extinction_pressure_resumes_with_the_oracle(tmp_path: Path) -> None:
    """The R2 hypothesis, measured: same match, same H, oracle on -- the
    attacker re-acquires the objective and keeps hitting it."""

    m = _run(
        tmp_path, ruleset_id=BYTEFRAY_RULESET_V5_R1_ALPHA1_ID,
        oracle=True, process_integrity=1, label="oracle",
    )

    extinction_tick = m["process_extinction_tick"]["B"]
    assert extinction_tick == 1, "victim's sole process must still die on tick 1"
    assert m["core_capture_outcome"]["B"] == "survived"

    # Pressure resumes on the very next tick, and never stops: the hunter
    # spends its entire Q=8 budget on the objective for every remaining tick.
    assert m["ticks_extinction_to_first_core_attack"]["B"] == 1
    assert m["attacker_resumes_objective_pressure"]["B"] is True
    expected_writes = (MAX_TICKS - extinction_tick) * 8
    assert m["post_extinction_core_attack_writes"]["B"] == expected_writes

    # R2's central limitation, asserted rather than assumed: 312 restored
    # core-targeting writes buy exactly ZERO further progress. The oracle
    # names one cell; the attacker takes it on the extinction tick itself and
    # then re-writes a cell it already owns for the remaining 39 ticks. No
    # ownership changes hands after extinction at all, so the "meaningful
    # attack" interval is undefined even though pressure plainly resumed.
    assert m["post_extinction_core_ownership_losses"]["B"] == 0
    assert m["target_loss_interval_ticks"]["B"] is None
    assert m["core_damage_dealt"]["A"] == 1
    assert m["max_core_deficit"]["B"] == 1
    assert m["core_capture_outcome"]["B"] == "survived"


def test_r2_follow_through_fields_stay_inert_under_stable_v4(tmp_path: Path) -> None:
    """No process ever dies under stable V4, so every R2 field degenerates
    to "nothing to report" -- the same discipline R1's fields already keep."""

    m = _run(
        tmp_path, ruleset_id="bytefray-rules-4",
        oracle=True, process_integrity=None, label="v4",
    )

    assert m["process_extinction_tick"] == {"A": None, "B": None}
    assert m["post_extinction_core_attack_writes"] == {"A": 0, "B": 0}
    assert m["post_extinction_core_ownership_losses"] == {"A": 0, "B": 0}
    assert m["ticks_extinction_to_first_core_attack"] == {"A": None, "B": None}
    assert m["target_loss_interval_ticks"] == {"A": None, "B": None}
    assert m["attacker_resumes_objective_pressure"] == {"A": False, "B": False}


def test_r2_follow_through_metrics_are_deterministic(tmp_path: Path) -> None:
    first = _run(
        tmp_path, ruleset_id=BYTEFRAY_RULESET_V5_R1_ALPHA1_ID,
        oracle=True, process_integrity=1, label="det1",
    )
    second = _run(
        tmp_path, ruleset_id=BYTEFRAY_RULESET_V5_R1_ALPHA1_ID,
        oracle=True, process_integrity=1, label="det2",
    )
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)
