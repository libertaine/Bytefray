"""E2 Guarded Painter (research fixture ``e2_guarded_painter``).

Design review Sec G.2, archetype 3b. Every tick: write each visible enemy
anchor once (disruption), rewrite exactly one of its own core cells (its core
base), then paint the next cells of a frontier that grows outward from its
own core, alternating sides; which side goes first is drawn once from
``context.rng``. Never attacks the enemy core deliberately. Global reach.

Purpose: the H2 defensive opportunity cost, and the exploratory Seat-B
mirror inversion (H3c). Research-only; never a product starter agent.
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
        self.first_side = 1
        self.strokes = 0
        self.depth = {1: 0, -1: 0}
        self.tick = -1
        self.done: set[int] = set()

    def reset(self, context: MatchContextV2) -> None:
        self.arena = context.arena_size
        self.first_side = context.rng.choice((1, -1))
        self.strokes = 0
        self.depth = {1: 0, -1: 0}
        self.tick = -1
        self.done = set()

    def declare_processes(self) -> list[ProcessDeclaration]:
        return [ProcessDeclaration(id="painter", reach=self.arena // 2, share=1.0)]

    def paint_target(self, obs: ObservationV2) -> int:
        side = self.first_side if self.strokes % 2 == 0 else -self.first_side
        self.strokes += 1
        depth = self.depth[side]
        self.depth[side] = depth + 1
        if side > 0:
            return (obs.own_core_base + obs.own_core_size + depth) % self.arena
        return (obs.own_core_base - 1 - depth) % self.arena

    def act(self, obs: ObservationV2) -> AgentAction:
        if obs.current_tick != self.tick:
            self.tick = obs.current_tick
            self.done = set()
        for target in [*obs.visible_enemy_anchor_addresses, obs.own_core_base % self.arena]:
            if target not in self.done:
                self.done.add(target)
                return AgentAction(ActionKindV2.WRITE, operand=target, value=1)
        return AgentAction(ActionKindV2.WRITE, operand=self.paint_target(obs), value=1)


def create_agent() -> Agent:
    return Agent()
