"""E3 Jam Sniper (research fixture ``e3_jam_sniper``).

E3 design review Sec L and Sec O-4: every E2 fixture hits each enemy anchor
at most once per tick, so without this agent repeated finite suppression
inside one tick -- the maximal-denial regime, and with it D6 -- is never
exercised. It is a diagnostic stressor, not a competitor.

Within each tick it alternates by its own action count in that tick. Even
actions (0, 2, 4, 6) write a visible enemy anchor, a disruptive hit;
successive hits in a tick cycle through the visible anchors. Odd actions
(1, 3, 5, 7) write the next enemy core cell. That core cursor continues
across ticks over core offsets 1 .. size-1; offset 0, the core base where
every enemy spawns, is covered by the hits. A hit with no visible anchor
becomes a core write, and a core write before the core is known becomes a
hit; with neither it reads its own core base, which has no effect.

Enemy core base (the E2 Sec G.1 contract): adopted at the first callback in
which every visible enemy anchor is at one address, and never revised.

One global-reach process, fully deterministic. Research-only; never a
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
        self.actions = 0
        self.hits = 0
        self.cursor = 0

    def reset(self, context: MatchContextV2) -> None:
        self.arena = context.arena_size
        self.enemy_core = None
        self.tick = -1
        self.actions = 0
        self.hits = 0
        self.cursor = 0

    def declare_processes(self) -> list[ProcessDeclaration]:
        return [ProcessDeclaration(id="jammer", reach=self.arena // 2, share=1.0)]

    def act(self, obs: ObservationV2) -> AgentAction:
        anchors = obs.visible_enemy_anchor_addresses
        if self.enemy_core is None and len(anchors) == 1:
            self.enemy_core = anchors[0]
        if obs.current_tick != self.tick:
            self.tick = obs.current_tick
            self.actions = 0
            self.hits = 0
        jam = self.actions % 2 == 0
        self.actions += 1
        if anchors and (jam or self.enemy_core is None):
            target = anchors[self.hits % len(anchors)]
            self.hits += 1
            return AgentAction(ActionKindV2.WRITE, operand=target, value=1)
        if self.enemy_core is not None:
            size = obs.own_core_size
            offset = 1 + self.cursor % (size - 1) if size > 1 else 0
            self.cursor += 1
            return AgentAction(ActionKindV2.WRITE, operand=(self.enemy_core + offset) % self.arena, value=1)
        return AgentAction(ActionKindV2.READ, operand=obs.own_core_base)


def create_agent() -> Agent:
    return Agent()
