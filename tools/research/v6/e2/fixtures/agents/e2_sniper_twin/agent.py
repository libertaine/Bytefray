"""E2 Global Sniper (research fixture ``e2_sniper``).

Design review Sec G.2, archetype 1. Every tick: write each visible enemy
anchor once (disruption), then every enemy core cell not yet written this
tick. Never repairs and never paints. Global reach.

Enemy core base (Sec G.1): adopted at the first callback in which every
visible enemy anchor is at one address -- the enemy still occupies a single
location -- and never revised. Until then the agent only disrupts.

Purpose: does E2 only delay the dominant attack? Research-only; never a
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
        self.enemy_core: int | None = None
        self.tick = -1
        self.done: set[int] = set()

    def reset(self, context: MatchContextV2) -> None:
        self.arena = context.arena_size
        self.enemy_core = None
        self.tick = -1
        self.done = set()

    def declare_processes(self) -> list[ProcessDeclaration]:
        return [ProcessDeclaration(id="sniper", reach=self.arena // 2, share=1.0)]

    def act(self, obs: ObservationV2) -> AgentAction:
        anchors = obs.visible_enemy_anchor_addresses
        if self.enemy_core is None and len(anchors) == 1:
            self.enemy_core = anchors[0]
        if obs.current_tick != self.tick:
            self.tick = obs.current_tick
            self.done = set()
        targets = list(anchors)
        if self.enemy_core is not None:
            targets += [(self.enemy_core + i) % self.arena for i in range(obs.own_core_size)]
        for target in targets:
            if target not in self.done:
                self.done.add(target)
                return AgentAction(ActionKindV2.WRITE, operand=target, value=1)
        return AgentAction(ActionKindV2.READ, operand=obs.own_core_base)


def create_agent() -> Agent:
    return Agent()
