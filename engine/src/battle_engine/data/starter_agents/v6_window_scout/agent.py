"""Bytefray V6 starter -- Window Scout.

THE LESSON: Incomplete information -> SENSE -> Delayed anonymous receipt -> Informed MOVE.

Under Bytefray Ruleset v6 (bytefray-rules-6-alpha1), passive visibility is empty.
To locate opponent anchors, an agent must spend an action executing SENSE(target)
within its declared reach. The engine samples opponent anchors within the sensing
window (half-width 27), but the result is not delivered immediately.

Instead, the sampled anonymous anchor addresses arrive on the NEXT eligible
callback for that process in observation.previous_sense_anchors.
Window Scout then uses this delivered historical sample to make an informed,
bounded MOVE toward the contact, followed by in-reach WRITE operations.

WHAT THIS AGENT IS ALLOWED TO KNOW
    Only ObservationV2. Window Scout never accesses seed coordinates, future
    events, or omniscient world state. Contacts are remembered historical samples
    delivered through official engine channels.
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

SCOUT_REACH = 128
DEFAULT_SEARCH_INTERVAL = 4
DEFAULT_MOVE_STEP = 64
DEFAULT_SEARCH_OFFSET = 91
SIGNATURE_VALUE = 0x42


class WindowScoutAgent(AgentV2):
    """Teaching agent demonstrating the complete active sensing lifecycle."""

    def __init__(self) -> None:
        self.arena: int = 512
        self.sensing_window: int | None = None
        self.search_interval: int = DEFAULT_SEARCH_INTERVAL
        self.move_step: int = DEFAULT_MOVE_STEP
        self.search_offset: int = DEFAULT_SEARCH_OFFSET
        self.eligible_callbacks: int = 0
        self.pending_sense: bool = False
        self.pending_sense_target: int | None = None
        self.remembered_contacts: list[int] = []
        self.active_target: int | None = None
        self.has_moved_to_target: bool = False

    def reset(self, context: MatchContextV2) -> None:
        self.arena = context.arena_size
        self.sensing_window = context.sensing_window
        params = getattr(context, "parameters", {}) or {}
        self.search_interval = int(params.get("search_interval", DEFAULT_SEARCH_INTERVAL))
        self.move_step = int(params.get("move_step", DEFAULT_MOVE_STEP))
        self.search_offset = int(params.get("search_offset", DEFAULT_SEARCH_OFFSET))
        self.eligible_callbacks = 0
        self.pending_sense = False
        self.pending_sense_target = None
        self.remembered_contacts = []
        self.active_target = None
        self.has_moved_to_target = False

    def declare_processes(self) -> list[ProcessDeclaration]:
        return [
            ProcessDeclaration(
                id="main",
                reach=SCOUT_REACH,
                share=1.0,
            )
        ]

    def act(self, observation: ObservationV2) -> AgentAction:
        self.eligible_callbacks += 1

        # Check for receipt delivered from a previous SENSE action
        if observation.previous_sense_anchors is not None:
            self.pending_sense = False
            self.pending_sense_target = None
            if observation.previous_sense_anchors:
                # Retain sorted unique anonymous contacts
                self.remembered_contacts = list(observation.previous_sense_anchors)
                self.active_target = self.remembered_contacts[0]
                self.has_moved_to_target = False
            else:
                self.remembered_contacts = []
                self.active_target = None
                self.has_moved_to_target = False

        # If we have an active remembered target
        if self.active_target is not None:
            target = self.active_target
            if not self.has_moved_to_target:
                # Informed MOVE toward delivered contact
                self.has_moved_to_target = True
                delta = self._shortest_delta(target, observation.self_anchor)
                clamped_delta = self._clamp(delta, self.move_step)
                return AgentAction(ActionKindV2.MOVE, operand=clamped_delta)
            else:
                # After moving toward target, execute in-reach WRITE and resume search cadence
                if self._within_reach(observation, target):
                    self.active_target = None
                    return AgentAction(ActionKindV2.WRITE, operand=target, value=SIGNATURE_VALUE)
                else:
                    delta = self._shortest_delta(target, observation.self_anchor)
                    clamped_delta = self._clamp(delta, self.move_step)
                    return AgentAction(ActionKindV2.MOVE, operand=clamped_delta)

        # Scheduled active sensing check
        if self.sensing_window is not None:
            # Sense on callback 1, or when cadence triggers and not currently waiting for a pending result
            should_scan = (
                self.eligible_callbacks == 1
                or (
                    self.eligible_callbacks % self.search_interval == 1
                    and not self.pending_sense
                )
            )
            if should_scan and not self.pending_sense:
                scan_target = (observation.self_anchor + self.search_offset) % self.arena
                if self._within_reach(observation, scan_target):
                    self.pending_sense = True
                    self.pending_sense_target = scan_target
                    return AgentAction(ActionKindV2.SENSE, operand=scan_target)

        # Fallback legal action: READ own core
        return AgentAction(ActionKindV2.READ, operand=observation.own_core_base)

    def _within_reach(self, observation: ObservationV2, address: int) -> bool:
        return self._circular_distance(observation.self_anchor, address) <= observation.self_reach

    def _circular_distance(self, a: int, b: int) -> int:
        delta = abs((a - b) % self.arena)
        return min(delta, self.arena - delta)

    def _shortest_delta(self, target: int, anchor: int) -> int:
        forward = (target - anchor) % self.arena
        backward = forward - self.arena
        return backward if abs(backward) < abs(forward) else forward

    @staticmethod
    def _clamp(delta: int, max_step: int) -> int:
        return max(-max_step, min(max_step, delta))


def create_agent() -> WindowScoutAgent:
    return WindowScoutAgent()
