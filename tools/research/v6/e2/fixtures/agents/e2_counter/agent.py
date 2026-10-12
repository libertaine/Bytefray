"""E2 Counterattacker (research fixture ``e2_counter``).

Design review Sec G.2, archetype 4. Paints a frontier outward from its own
core (alternating sides; the first side drawn once from ``context.rng``)
until it detects that it was attacked, then switches permanently to sniper
mode and never repairs: each visible enemy anchor once per tick, then every
enemy core cell not yet written this tick.

Attack detection uses only the public Agent API: its single process got no
callback on the previous tick (``last_callback_tick < current_tick - 1``),
i.e. it was disrupted for that whole tick.

Enemy core base (Sec G.1): adopted at the first callback in which every
visible enemy anchor is at one address, and never revised.

Purpose: races and mutual threats. Research-only; never a product starter.
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
        self.attacked = False
        self.enemy_core: int | None = None
        self.tick = -1
        self.done: set[int] = set()

    def reset(self, context: MatchContextV2) -> None:
        self.arena = context.arena_size
        self.first_side = context.rng.choice((1, -1))
        self.strokes = 0
        self.depth = {1: 0, -1: 0}
        self.attacked = False
        self.enemy_core = None
        self.tick = -1
        self.done = set()

    def declare_processes(self) -> list[ProcessDeclaration]:
        return [ProcessDeclaration(id="counter", reach=self.arena // 2, share=1.0)]

    def paint_target(self, obs: ObservationV2) -> int:
        side = self.first_side if self.strokes % 2 == 0 else -self.first_side
        self.strokes += 1
        depth = self.depth[side]
        self.depth[side] = depth + 1
        if side > 0:
            return (obs.own_core_base + obs.own_core_size + depth) % self.arena
        return (obs.own_core_base - 1 - depth) % self.arena

    def act(self, obs: ObservationV2) -> AgentAction:
        anchors = obs.visible_enemy_anchor_addresses
        if self.enemy_core is None and len(anchors) == 1:
            self.enemy_core = anchors[0]
        if obs.current_tick > 1 and obs.last_callback_tick < obs.current_tick - 1:
            self.attacked = True
        if not self.attacked:
            return AgentAction(ActionKindV2.WRITE, operand=self.paint_target(obs), value=1)
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
