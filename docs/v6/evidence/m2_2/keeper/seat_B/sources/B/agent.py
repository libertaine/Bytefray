"""Watchful Keeper: delivered ownership supports repair; old scans support one attempt.

READ, SENSE and WRITE each spend an ordinary opportunity. A scan is an anonymous
historical sample, never a live target, hit report or enemy core identification.
The policy stays at its own observed core and never uses placement seeds.
"""

from __future__ import annotations

from battle_engine.agent_api import (
    ActionKindV2,
    AgentAction,
    AgentV2,
    MatchContextV2,
    ObservationV2,
    ProcessDeclaration,
)


class WatchfulKeeperAgent(AgentV2):
    def reset(self, context: MatchContextV2) -> None:
        self.arena = context.arena_size
        self.agent_id = context.agent_id
        self.sensing_window = context.sensing_window
        self.scan_interval = int(context.parameters.get("scan_interval", 4))
        self.perimeter_offset = int(context.parameters.get("perimeter_offset", 27))
        self.callbacks = 0
        self.core_cursor = 0
        self.previous_action: AgentAction | None = None
        # Retain delivered samples, including empty samples, without refreshing
        # them or reusing them as a standing instruction to attack.
        self.sample_history: list[tuple[int, tuple[int, ...]]] = []

    def declare_processes(self) -> list[ProcessDeclaration]:
        return [ProcessDeclaration(id="main", reach=128, share=1.0)]

    def _in_reach(self, observation: ObservationV2, address: int) -> bool:
        delta = (address - observation.self_anchor) % self.arena
        return min(delta, self.arena - delta) <= observation.self_reach

    def act(self, observation: ObservationV2) -> AgentAction:
        self.callbacks += 1
        previous = self.previous_action
        self.previous_action = None  # Consume the preceding action exactly once.
        core = tuple((observation.own_core_base + i) % self.arena for i in range(8))
        action = None
        if previous is not None and observation.previous_action_applied is True:
            if (
                previous.kind == ActionKindV2.READ
                and previous.operand in core
                and observation.previous_read_value is not None
                and observation.previous_read_owner != self.agent_id
                and self._in_reach(observation, previous.operand)
            ):
                action = AgentAction(ActionKindV2.WRITE, operand=previous.operand, value=0x4B)
            elif previous.kind == ActionKindV2.SENSE:
                sample = observation.previous_sense_anchors
                if sample is not None:
                    self.sample_history.append((self.callbacks, tuple(sample)))
                    legal = sorted(a for a in sample if self._in_reach(observation, a))
                    if legal:
                        action = AgentAction(ActionKindV2.WRITE, operand=legal[0], value=0x4B)
        if action is None and self.callbacks % self.scan_interval == 0:
            center = (observation.own_core_base + self.perimeter_offset) % self.arena
            if self.sensing_window is not None and self._in_reach(observation, center):
                action = AgentAction(ActionKindV2.SENSE, operand=center)
        if action is None:
            action = AgentAction(ActionKindV2.READ, operand=core[self.core_cursor])
            self.core_cursor = (self.core_cursor + 1) % 8
        self.previous_action = action
        return action


def create_agent() -> WatchfulKeeperAgent:
    return WatchfulKeeperAgent()
