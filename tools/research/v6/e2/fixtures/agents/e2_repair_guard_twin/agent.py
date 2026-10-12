"""E2 Pure Repair Guard (research fixture ``e2_repair_guard``).

Design review Sec G.2, archetype 2a. Every action rewrites one of its own
core cells, cycling through the core across the whole match. Never disrupts,
never attacks, never paints. Global reach (declared, never used to target).

Purpose: distinguish E2's nominal executable window (Sec D.4) from
meaningful defense -- the H0 control for defense. Research-only; never a
product starter agent.
"""

from __future__ import annotations

from battle_engine.agent_api import (
    ActionKindV2,
    AgentAction,
    MatchContextV2,
    ObservationV2,
    ProcessDeclaration,
)


class Agent:
    def __init__(self) -> None:
        self.arena = 0
        self.cursor = 0

    def reset(self, context: MatchContextV2) -> None:
        self.arena = context.arena_size
        self.cursor = 0

    def declare_processes(self) -> list[ProcessDeclaration]:
        return [ProcessDeclaration(id="guard", reach=self.arena // 2, share=1.0)]

    def act(self, obs: ObservationV2) -> AgentAction:
        target = (obs.own_core_base + self.cursor) % self.arena
        self.cursor = (self.cursor + 1) % obs.own_core_size
        return AgentAction(ActionKindV2.WRITE, operand=target, value=1)


def create_agent() -> Agent:
    return Agent()
