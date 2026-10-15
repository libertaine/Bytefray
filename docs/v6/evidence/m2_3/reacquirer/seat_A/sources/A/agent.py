"""Roaming Reacquirer: hold an old contact, pay to rescan it, pay to search again.

SENSE, wait READ, MOVE and WRITE each spend an ordinary opportunity. A scan
receipt is an anonymous historical sample delivered at this process's next
callback, never a live position, identity or notification. An applied rescan
that omits a remembered address records only that the address was absent in
that newer sample; a later contact is a new anonymous contact, not the same
process. The policy never uses placement seeds or fixture knowledge.
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

SEARCH = "SEARCH"
HOLD = "HOLD"
SEARCH_AFTER_ABSENCE = "SEARCH_AFTER_ABSENCE"
RESPONSE = "RESPONSE"
RESPONSE_VALUE = 0x52


class RoamingReacquirerAgent(AgentV2):
    def reset(self, context: MatchContextV2) -> None:
        self.arena = context.arena_size
        self.sensing_window = context.sensing_window
        self.search_offset = int(context.parameters.get("search_offset", 91))
        self.move_step = min(int(context.parameters.get("move_step", 64)), 64)
        self.rescan_wait = int(context.parameters.get("rescan_wait", 3))
        self.callbacks = 0
        self.mode = SEARCH
        self.target: int | None = None
        self.wait = 0
        # The SENSE awaiting its receipt at the next callback: (purpose, center).
        self.pending: tuple[str, int] | None = None
        # Delivered samples keep their original sample tick: no TTL or refresh.
        self.samples: list[tuple[int, int, tuple[int, ...]]] = []
        # Entrant-side findings, e.g. ("absent_in_newer_sample", address).
        self.findings: list[tuple[str, int]] = []
        self.fallbacks = 0

    def declare_processes(self) -> list[ProcessDeclaration]:
        return [ProcessDeclaration(id="main", reach=128, share=1.0)]

    def act(self, observation: ObservationV2) -> AgentAction:
        self.callbacks += 1
        pending, self.pending = self.pending, None  # Consume the request exactly once.
        if pending is None:
            # The previous action was not a SENSE, so nothing here is a receipt.
            if self.mode == HOLD:
                return self._hold(observation)
            if self.mode == RESPONSE:
                return self._respond(observation)
            return self._search(observation)
        purpose, center = pending
        sample = observation.previous_sense_anchors
        if observation.previous_action_applied is not True or sample is None:
            # Refused, null or absent feedback: nothing new is learned and no
            # absence is inferred. A refused rescan resumes plain discovery.
            if purpose == "rescan":
                self.target = None
                self.mode = SEARCH
            return self._search(observation)
        receipt = tuple(sample)
        self.samples.append((observation.previous_action_tick, center, receipt))
        if purpose == "rescan":
            if center in receipt:
                return self._hold(observation, restart=True)
            self.findings.append(("absent_in_newer_sample", center))
            self.target = None
            self.mode = SEARCH_AFTER_ABSENCE
            return AgentAction(ActionKindV2.MOVE, operand=self.move_step)
        if not receipt:
            # An applied empty search: no target exists and no contact was lost.
            return AgentAction(ActionKindV2.MOVE, operand=self.move_step)
        self.target = min(receipt)
        if self.mode == SEARCH:
            return self._hold(observation, restart=True)
        self.findings.append(("new_anonymous_contact", self.target))
        return self._respond(observation)

    def _hold(self, observation: ObservationV2, *, restart: bool = False) -> AgentAction:
        self.mode = HOLD
        if restart:
            self.wait = self.rescan_wait
        if self.wait > 0:
            self.wait -= 1
            return AgentAction(ActionKindV2.READ, operand=self._local_read(observation))
        target = self.target
        if target is not None and self.sensing_window is not None and self._in_reach(observation, target):
            self.pending = ("rescan", target)
            return AgentAction(ActionKindV2.SENSE, operand=target)
        # An illegal rescan center resumes discovery; it proves no absence.
        self.target = None
        self.mode = SEARCH
        return self._search(observation)

    def _respond(self, observation: ObservationV2) -> AgentAction:
        target = self.target
        if target is None:
            self.mode = SEARCH
            return self._search(observation)
        if self._in_reach(observation, target):
            self.mode = HOLD
            self.wait = self.rescan_wait  # The wait READs start next callback.
            return AgentAction(ActionKindV2.WRITE, operand=target, value=RESPONSE_VALUE)
        self.mode = RESPONSE
        forward = (target - observation.self_anchor) % self.arena
        backward = self.arena - forward
        step = min(self.move_step, forward, backward)
        return AgentAction(ActionKindV2.MOVE, operand=step if forward <= backward else -step)

    def _search(self, observation: ObservationV2) -> AgentAction:
        center = (observation.self_anchor + self.search_offset) % self.arena
        if self.sensing_window is not None and self._in_reach(observation, center):
            self.pending = ("search", center)
            return AgentAction(ActionKindV2.SENSE, operand=center)
        # Legal fallback; it is never counted as a scan, MOVE or response.
        self.fallbacks += 1
        if self._in_reach(observation, observation.own_core_base):
            return AgentAction(ActionKindV2.READ, operand=observation.own_core_base)
        return AgentAction(ActionKindV2.MOVE, operand=0)

    def _local_read(self, observation: ObservationV2) -> int:
        if self._in_reach(observation, observation.own_core_base):
            return observation.own_core_base
        return observation.self_anchor

    def _in_reach(self, observation: ObservationV2, address: int) -> bool:
        delta = (address - observation.self_anchor) % self.arena
        return min(delta, self.arena - delta) <= observation.self_reach


def create_agent() -> RoamingReacquirerAgent:
    return RoamingReacquirerAgent()
