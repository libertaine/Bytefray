"""E2 Spread Sniper (research fixture ``e2_spread_sniper``).

Design review Sec G.2, archetype 1'. Three processes. ``p1`` and ``p2`` each
``MOVE`` once, on their first callback, by offsets drawn from
``context.rng`` with magnitude in [16, 64] and opposite signs (so the three
locations are distinct). Every other action: write each visible enemy anchor
once per tick (disruption), then every enemy core cell not yet written this
tick. Never repairs. Global reach.

Enemy core base (Sec G.1): adopted at the first callback in which every
visible enemy anchor is at one address, and never revised.

Purpose: does location count close the defensive response window (Sec D.6,
H3e)? Research-only; never a product starter agent.
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
        self.offsets: dict[str, int] = {}
        self.moved: set[str] = set()
        self.enemy_core: int | None = None
        self.tick = -1
        self.done: set[int] = set()

    def reset(self, context: MatchContextV2) -> None:
        self.arena = context.arena_size
        sign = context.rng.choice((1, -1))
        self.offsets = {
            "p1": sign * context.rng.randint(16, 64),
            "p2": -sign * context.rng.randint(16, 64),
        }
        self.moved = set()
        self.enemy_core = None
        self.tick = -1
        self.done = set()

    def declare_processes(self) -> list[ProcessDeclaration]:
        reach = self.arena // 2
        return [
            ProcessDeclaration(id="p0", reach=reach, share=0.375),
            ProcessDeclaration(id="p1", reach=reach, share=0.375),
            ProcessDeclaration(id="p2", reach=reach, share=0.25),
        ]

    def act(self, obs: ObservationV2) -> AgentAction:
        anchors = obs.visible_enemy_anchor_addresses
        if self.enemy_core is None and len(anchors) == 1:
            self.enemy_core = anchors[0]
        if obs.current_tick != self.tick:
            self.tick = obs.current_tick
            self.done = set()
        process = obs.self_process_id
        if process in self.offsets and process not in self.moved:
            self.moved.add(process)
            return AgentAction(ActionKindV2.MOVE, operand=self.offsets[process])
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
