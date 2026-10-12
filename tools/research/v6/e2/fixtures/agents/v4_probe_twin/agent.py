"""V4 exploit probe (E2 research fixture ``v4_probe``).

Design review Sec G.2: an exact copy of ``CompetentGlobalSniperProbe`` from
``engine/tests/test_v4_exploit_characterization.py`` -- global reach, and
every write targets ``visible_enemy_anchor_addresses[0] + step`` with
``step`` cycling 0-7 across the whole match. It keeps no inferred enemy core
base; it re-reads the first visible anchor on every callback.

Purpose: continuity with the frozen V4 exploit characterization.
Research-only; never a product starter agent.
"""

from __future__ import annotations

from battle_engine.agent_api import (
    ActionKindV2,
    AgentAction,
    MatchContextV2,
    ObservationV2,
    ProcessDeclaration,
)


class CompetentGlobalSniperProbe:
    def __init__(self) -> None:
        self.context: MatchContextV2 | None = None
        self.write_step = 0

    def reset(self, context: MatchContextV2) -> None:
        self.context = context
        self.write_step = 0

    def declare_processes(self) -> list[ProcessDeclaration]:
        assert self.context is not None
        reach = self.context.arena_size // 2
        return [ProcessDeclaration(id="sniper", reach=reach, share=1.0)]

    def act(self, obs: ObservationV2) -> AgentAction:
        assert self.context is not None
        if not obs.visible_enemy_anchor_addresses:
            return AgentAction(ActionKindV2.READ, operand=0)

        enemy_core_base = obs.visible_enemy_anchor_addresses[0]
        target_cell = (enemy_core_base + self.write_step) % self.context.arena_size
        self.write_step = (self.write_step + 1) % 8
        return AgentAction(ActionKindV2.WRITE, operand=target_cell, value=1)


def create_agent() -> CompetentGlobalSniperProbe:
    return CompetentGlobalSniperProbe()
