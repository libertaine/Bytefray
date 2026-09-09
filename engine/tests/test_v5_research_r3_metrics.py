from __future__ import annotations

"""V5 research Phase R3: attack-geometry metric tests.

R3 asks whether an attacker's writes COVER A REGION or merely repeat one
point, so its analyzer must separate three situations that Phase 0's
activity counters conflate:

    A  one core cell struck a hundred times      -> lots of writes, no spread
    B  eight different core cells struck         -> real spread
    C  four cells taken, repaired, four more     -> full cumulative spread,
                                                    but never more than half
                                                    the core lost at once

Distinguishing A from B is what the whole R3 hypothesis rests on;
distinguishing B from C is what stops "eight distinct cells were damaged"
from being misreported as "the core was nearly captured". Every assertion
below is derived from a replay a real deterministic match produced -- never
from a hand-built record -- and asserts exact values rather than mere
non-emptiness.

Every match here runs under the permanent stable Ruleset ``bytefray-rules-4``
with no process mortality and no objective-target oracle, which is also R3's
own experimental condition.
"""

from pathlib import Path
from typing import Any

from battle_engine.agents import resolve_agent
from battle_engine.config import Config
from battle_engine.match_service import MatchEntrant, MatchRequest, NativeMatchService
from battle_engine.ruleset_policy import BYTEFRAY_RULESET_V4_ID

from tools.research.v5.analyzer import analyze_match

# Both entrants below use an explicit start address, so the victim's core is
# exactly [VICTIM_START, VICTIM_START + 8) and its sole process anchors there
# and never moves. The attacker therefore reads the victim's core base
# directly out of ``visible_enemy_anchor_addresses[0]`` -- an ordinary live
# anchor sighting, not an oracle -- which is what makes these scenarios
# scriptable without hard-coding an address into the agent.
ATTACKER_START = 0
VICTIM_START = 40
ARENA_SIZE = 512
MAX_TICKS = 30

# Writes exactly one address forever: the victim's anchor. The written byte
# alternates so a repeat write to the same address always produces an
# observable memory diff rather than being silently identical.
POINT_ATTACKER_CODE = """
from battle_engine.agent_api import AgentV2, ObservationV2, AgentAction, ActionKindV2, MatchContextV2, ProcessDeclaration

class PointAttacker:
    api_version = 2
    def declare_processes(self):
        return [ProcessDeclaration(id="attacker", reach=60, share=1.0)]
    def reset(self, context: MatchContextV2):
        self.flip = 0
    def act(self, obs: ObservationV2) -> AgentAction:
        if obs.visible_enemy_anchor_addresses:
            self.flip = 1 - self.flip
            return AgentAction(ActionKindV2.WRITE, operand=obs.visible_enemy_anchor_addresses[0], value=0x40 + self.flip)
        return AgentAction(ActionKindV2.READ, 0)

def create_agent() -> AgentV2:
    return PointAttacker()
"""

# Writes T, T+1, ... T+7 in rotation: eight distinct addresses around the
# same legally acquired contact.
REGION_ATTACKER_CODE = """
from battle_engine.agent_api import AgentV2, ObservationV2, AgentAction, ActionKindV2, MatchContextV2, ProcessDeclaration

class RegionAttacker:
    api_version = 2
    def declare_processes(self):
        return [ProcessDeclaration(id="attacker", reach=60, share=1.0)]
    def reset(self, context: MatchContextV2):
        self.arena = context.arena_size
        self.cursor = 0
    def act(self, obs: ObservationV2) -> AgentAction:
        if obs.visible_enemy_anchor_addresses:
            target = obs.visible_enemy_anchor_addresses[0]
            address = (target + self.cursor % 8) % self.arena
            self.cursor += 1
            return AgentAction(ActionKindV2.WRITE, operand=address, value=0x51)
        return AgentAction(ActionKindV2.READ, 0)

def create_agent() -> AgentV2:
    return RegionAttacker()
"""

# Takes cells T+0..T+3 on tick 1, stops so the victim can repair, then takes
# T+4..T+7 on tick 3. Cumulative coverage reaches all eight cells; the
# simultaneous deficit never exceeds four.
SPLIT_ATTACKER_CODE = """
from battle_engine.agent_api import AgentV2, ObservationV2, AgentAction, ActionKindV2, MatchContextV2, ProcessDeclaration

class SplitAttacker:
    api_version = 2
    def declare_processes(self):
        return [ProcessDeclaration(id="attacker", reach=60, share=1.0)]
    def reset(self, context: MatchContextV2):
        self.arena = context.arena_size
        self.first_wave = 0
        self.second_wave = 0
    def act(self, obs: ObservationV2) -> AgentAction:
        if not obs.visible_enemy_anchor_addresses:
            return AgentAction(ActionKindV2.READ, 0)
        target = obs.visible_enemy_anchor_addresses[0]
        if obs.current_tick == 1 and self.first_wave < 4:
            address = (target + self.first_wave) % self.arena
            self.first_wave += 1
            return AgentAction(ActionKindV2.WRITE, operand=address, value=0x61)
        if obs.current_tick == 3 and self.second_wave < 4:
            address = (target + 4 + self.second_wave) % self.arena
            self.second_wave += 1
            return AgentAction(ActionKindV2.WRITE, operand=address, value=0x62)
        return AgentAction(ActionKindV2.READ, 0)

def create_agent() -> AgentV2:
    return SplitAttacker()
"""

# Never acts offensively and never repairs.
PASSIVE_VICTIM_CODE = """
from battle_engine.agent_api import AgentV2, ObservationV2, AgentAction, ActionKindV2, MatchContextV2, ProcessDeclaration

class PassiveVictim:
    api_version = 2
    def declare_processes(self):
        return [ProcessDeclaration(id="sitter", reach=8, share=1.0)]
    def reset(self, context: MatchContextV2):
        pass
    def act(self, obs: ObservationV2) -> AgentAction:
        return AgentAction(ActionKindV2.READ, obs.self_anchor)

def create_agent() -> AgentV2:
    return PassiveVictim()
"""

# Repairs every one of its own eight core cells, but only on tick 2 -- so the
# damage/repair/damage cycle Case C needs is fully deterministic rather than
# a race against the attacker inside one tick.
REPAIRING_VICTIM_CODE = """
from battle_engine.agent_api import AgentV2, ObservationV2, AgentAction, ActionKindV2, MatchContextV2, ProcessDeclaration

class RepairingVictim:
    api_version = 2
    def declare_processes(self):
        return [ProcessDeclaration(id="repairer", reach=8, share=1.0)]
    def reset(self, context: MatchContextV2):
        self.arena = context.arena_size
        self.repaired = 0
    def act(self, obs: ObservationV2) -> AgentAction:
        if obs.current_tick == 2 and self.repaired < 8:
            address = (obs.own_core_base + self.repaired) % self.arena
            self.repaired += 1
            return AgentAction(ActionKindV2.WRITE, operand=address, value=0xCE)
        return AgentAction(ActionKindV2.READ, obs.self_anchor)

def create_agent() -> AgentV2:
    return RepairingVictim()
"""


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
    attacker: str,
    attacker_code: str,
    victim: str,
    victim_code: str,
    label: str,
    max_ticks: int = MAX_TICKS,
) -> dict[str, Any]:
    _setup_agent(tmp_path, attacker, attacker_code)
    _setup_agent(tmp_path, victim, victim_code)
    entrants = (
        MatchEntrant.python("A", attacker, ATTACKER_START, resolve_agent(tmp_path, attacker)),
        MatchEntrant.python("B", victim, VICTIM_START, resolve_agent(tmp_path, victim)),
    )
    replay_path = tmp_path / label / "replay.jsonl"
    request = MatchRequest(
        config=Config(seed=5, arena_size=ARENA_SIZE, instr_per_tick=8),
        entrants=entrants,
        max_ticks=max_ticks,
        replay_path=replay_path,
        verbose=False,
        ruleset_id=BYTEFRAY_RULESET_V4_ID,
    )
    result = NativeMatchService().run(request)
    assert result.result_path is not None
    return analyze_match(replay_path, result.result_path)


def test_case_a_repeated_point_attack_is_many_writes_and_one_cell(tmp_path: Path) -> None:
    """Case A: the same core cell struck over and over.

    This is the bundled ``v4_concentrated_attacker``'s shape, and the exact
    situation Phase 0's activity counters flatter: hundreds of writes and
    hundreds of ownership-flip *events*, all against a single cell, with the
    victim never closer than 7/8 of its core to elimination.
    """

    m = _run(
        tmp_path,
        attacker="r3_point_attacker",
        attacker_code=POINT_ATTACKER_CODE,
        victim="r3_passive_victim",
        victim_code=PASSIVE_VICTIM_CODE,
        label="case_a",
    )

    # Lots of activity...
    assert m["enemy_core_writes_expanded"]["A"] > 100
    assert m["writes_expanded"]["A"] == m["enemy_core_writes_expanded"]["A"]
    # ...spread over exactly one address.
    assert m["unique_write_addresses"]["A"] == 1
    assert m["unique_enemy_core_cells_targeted"]["A"] == 1
    assert m["unique_enemy_core_cells_damaged"]["A"] == 1
    # The victim loses exactly one cell and is never in danger.
    assert m["distinct_own_core_cells_ever_lost"]["B"] == 1
    assert m["max_core_deficit"]["B"] == 1
    assert m["core_capture_outcome"]["B"] == "survived"
    assert m["tick_2_distinct_own_core_cells_lost"]["B"] is None
    assert m["tick_4_distinct_own_core_cells_lost"]["B"] is None
    assert m["tick_8_distinct_own_core_cells_lost"]["B"] is None
    assert m["first_full_core_deficit_tick"]["B"] is None
    # Exactly one uninterrupted attack episode, covering one cell.
    assert m["attack_episodes"]["A"] == 1
    assert m["max_distinct_core_cells_per_attack_episode"]["A"] == 1


def test_case_b_sequential_region_attack_covers_eight_distinct_cells(tmp_path: Path) -> None:
    """Case B: eight different core cells struck, against a victim that
    never repairs.

    Coverage is what changes versus Case A -- eight distinct cells rather
    than one -- and because nothing ever restores the victim's ownership,
    that cumulative coverage does become a simultaneous 8/8 deficit and a
    real capture. The capture is asserted from the engine's own recorded
    outcome, not inferred from the coverage count; Case C is the companion
    that proves coverage alone never implies it.
    """

    m = _run(
        tmp_path,
        attacker="r3_region_attacker",
        attacker_code=REGION_ATTACKER_CODE,
        victim="r3_passive_victim",
        victim_code=PASSIVE_VICTIM_CODE,
        label="case_b",
    )

    assert m["unique_enemy_core_cells_targeted"]["A"] == 8
    assert m["unique_enemy_core_cells_damaged"]["A"] == 8
    assert m["distinct_own_core_cells_ever_lost"]["B"] == 8
    # Milestones are ordered and all reached.
    first_hit = m["first_own_core_hit_tick"]["B"]
    assert first_hit is not None
    for key in (
        "tick_2_distinct_own_core_cells_lost",
        "tick_4_distinct_own_core_cells_lost",
        "tick_8_distinct_own_core_cells_lost",
    ):
        assert m[key]["B"] is not None
    assert (
        first_hit
        <= m["tick_2_distinct_own_core_cells_lost"]["B"]
        <= m["tick_4_distinct_own_core_cells_lost"]["B"]
        <= m["tick_8_distinct_own_core_cells_lost"]["B"]
    )
    # An undefended victim does get captured, and the engine says so.
    assert m["max_core_deficit"]["B"] == 8
    assert m["core_capture_outcome"]["B"] == "captured"
    assert m["first_full_core_deficit_tick"]["B"] is not None
    assert m["full_core_return_count"]["B"] == 0
    assert m["ticks_first_core_hit_to_core_capture"]["B"] is not None


def test_case_c_damage_and_repair_never_claims_capture_from_coverage(tmp_path: Path) -> None:
    """Case C: four cells taken, repaired, then four more.

    This is the measurement R3's whole comparison depends on. Cumulative
    coverage reaches all eight cells -- identical to Case B on that metric
    alone -- while the victim is never more than half-damaged at any instant
    and is never at risk. Reporting "8 distinct core cells damaged" as
    progress toward capture would be exactly wrong here.
    """

    m = _run(
        tmp_path,
        attacker="r3_split_attacker",
        attacker_code=SPLIT_ATTACKER_CODE,
        victim="r3_repairing_victim",
        victim_code=REPAIRING_VICTIM_CODE,
        label="case_c",
    )

    # Cumulative coverage: all eight, same as Case B.
    assert m["unique_enemy_core_cells_damaged"]["A"] == 8
    assert m["distinct_own_core_cells_ever_lost"]["B"] == 8
    assert m["tick_8_distinct_own_core_cells_lost"]["B"] is not None
    # Simultaneous deficit: never more than four, and it returned to full.
    assert m["max_core_deficit"]["B"] == 4
    assert m["core_capture_outcome"]["B"] == "survived"
    assert m["first_full_core_deficit_tick"]["B"] is None
    assert m["ticks_first_core_hit_to_core_capture"]["B"] is None
    assert m["full_core_return_count"]["B"] == 1
    # Two separate waves of pressure, each covering four cells.
    assert m["attack_episodes"]["A"] == 2
    assert m["max_distinct_core_cells_per_attack_episode"]["A"] == 4


def test_run_expansion_counts_merged_adjacent_writes_separately(tmp_path: Path) -> None:
    """A sweeping attacker's writes must not be undercounted by replay's
    run-length merging.

    ``vm._wr8`` merges adjacent same-owner writes issued back-to-back within
    one tick into a single ``MemoryDiff`` with ``length > 1``. Phase 0's
    ``core_attack_writes`` reads only ``diff.address``, so it counts a
    contiguous T, T+1, T+2 sweep as ONE write while counting a T, T, T point
    barrage as three -- a bias pointing directly against R3's hypothesis.
    The R3 counters expand the run, so they must exceed the legacy counter
    for exactly this agent.
    """

    m = _run(
        tmp_path,
        attacker="r3_region_attacker",
        attacker_code=REGION_ATTACKER_CODE,
        victim="r3_passive_victim",
        victim_code=PASSIVE_VICTIM_CODE,
        label="run_expansion",
    )

    assert m["enemy_core_writes_expanded"]["A"] > m["core_attack_writes"]["A"]
    # Every one of this agent's writes lands inside the victim's core, so
    # the expanded core counter must account for all of them.
    assert m["enemy_core_writes_expanded"]["A"] == m["writes_expanded"]["A"]


def test_r3_metrics_are_deterministic_across_runs(tmp_path: Path) -> None:
    """Identical inputs must produce identical R3 metrics."""

    first = _run(
        tmp_path / "run1",
        attacker="r3_region_attacker",
        attacker_code=REGION_ATTACKER_CODE,
        victim="r3_repairing_victim",
        victim_code=REPAIRING_VICTIM_CODE,
        label="determinism",
    )
    second = _run(
        tmp_path / "run2",
        attacker="r3_region_attacker",
        attacker_code=REGION_ATTACKER_CODE,
        victim="r3_repairing_victim",
        victim_code=REPAIRING_VICTIM_CODE,
        label="determinism",
    )

    r3_fields = (
        "writes_expanded",
        "unique_write_addresses",
        "hostile_writes_expanded",
        "unique_hostile_write_addresses",
        "enemy_core_writes_expanded",
        "unique_enemy_core_cells_targeted",
        "unique_enemy_core_cells_damaged",
        "attack_episodes",
        "max_distinct_core_cells_per_attack_episode",
        "mean_distinct_core_cells_per_attack_episode",
        "distinct_own_core_cells_ever_lost",
        "first_own_core_hit_tick",
        "tick_2_distinct_own_core_cells_lost",
        "tick_4_distinct_own_core_cells_lost",
        "tick_8_distinct_own_core_cells_lost",
        "first_full_core_deficit_tick",
        "ticks_first_core_hit_to_core_capture",
        "first_contact_tick_by_entrant",
        "first_geometric_contact_tick",
        "ticks_contact_to_first_core_damage",
        "visible_target_changes",
    )
    for field in r3_fields:
        assert first[field] == second[field], field


def test_r3_fields_are_inert_when_no_contact_occurs(tmp_path: Path) -> None:
    """With no contact there is no geometry to report, and every R3 field
    must degenerate cleanly rather than emitting a spurious zero-tick."""

    m = _run(
        tmp_path,
        attacker="r3_point_attacker",
        attacker_code=POINT_ATTACKER_CODE,
        victim="r3_passive_victim",
        victim_code=PASSIVE_VICTIM_CODE,
        label="no_contact",
        max_ticks=4,
    )
    # Force the no-contact condition by checking the far-apart variant
    # instead: re-run with the victim outside the attacker's reach.
    entrants_far = _run_far(tmp_path)
    assert entrants_far["first_geometric_contact_tick"] is None
    assert entrants_far["writes_expanded"] == {"A": 0, "B": 0}
    assert entrants_far["unique_enemy_core_cells_targeted"] == {"A": 0, "B": 0}
    assert entrants_far["attack_episodes"] == {"A": 0, "B": 0}
    assert entrants_far["visible_target_changes"] == {"A": 0, "B": 0}
    assert entrants_far["first_own_core_hit_tick"] == {"A": None, "B": None}
    # And the contact case really did make contact, so the assertion above
    # is a genuine no-contact result rather than a broken harness.
    assert m["first_geometric_contact_tick"] is not None


def _run_far(tmp_path: Path) -> dict[str, Any]:
    """Same two agents, placed beyond one another's reach."""

    _setup_agent(tmp_path, "r3_point_attacker", POINT_ATTACKER_CODE)
    _setup_agent(tmp_path, "r3_passive_victim", PASSIVE_VICTIM_CODE)
    entrants = (
        MatchEntrant.python(
            "A", "r3_point_attacker", 0, resolve_agent(tmp_path, "r3_point_attacker")
        ),
        MatchEntrant.python(
            "B", "r3_passive_victim", 256, resolve_agent(tmp_path, "r3_passive_victim")
        ),
    )
    replay_path = tmp_path / "far" / "replay.jsonl"
    request = MatchRequest(
        config=Config(seed=5, arena_size=ARENA_SIZE, instr_per_tick=8),
        entrants=entrants,
        max_ticks=MAX_TICKS,
        replay_path=replay_path,
        verbose=False,
        ruleset_id=BYTEFRAY_RULESET_V4_ID,
    )
    result = NativeMatchService().run(request)
    assert result.result_path is not None
    return analyze_match(replay_path, result.result_path)
