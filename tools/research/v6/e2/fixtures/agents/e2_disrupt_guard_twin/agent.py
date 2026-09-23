"""E2 Disrupt-First Guard (research fixture ``e2_disrupt_guard``).

Design review Sec G.2, archetype 2b. Every tick: write each visible enemy
anchor once (disruption), then each of its own core cells not yet written
this tick (repair). Never attacks the enemy core, never paints. Global reach.

Purpose: the canonical H1 defender (Sec D.5), and the H3a/H3b stalemate
probe. Research-only; never a product starter agent.
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
        self.tick = -1
        self.done: set[int] = set()

    def reset(self, context: MatchContextV2) -> None:
        self.arena = context.arena_size
        self.tick = -1
        self.done = set()

    def declare_processes(self) -> list[ProcessDeclaration]:
        return [ProcessDeclaration(id="guard", reach=self.arena // 2, share=1.0)]

    def act(self, obs: ObservationV2) -> AgentAction:
        if obs.current_tick != self.tick:
            self.tick = obs.current_tick
            self.done = set()
        own = [(obs.own_core_base + i) % self.arena for i in range(obs.own_core_size)]
        for target in list(obs.visible_enemy_anchor_addresses) + own:
            if target not in self.done:
                self.done.add(target)
                return AgentAction(ActionKindV2.WRITE, operand=target, value=1)
        return AgentAction(ActionKindV2.READ, operand=obs.own_core_base)


def create_agent() -> Agent:
    return Agent()
