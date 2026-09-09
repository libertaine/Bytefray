"""R4 archetype C -- objective-capable defender (RESEARCH ONLY).

Not a starter, not a shipped example, not a member of the canonical V4
population. See ``tools/research/v5/agents/README.md``.

Strategic identity: actually defend the objective. R3 Section C.1 corrected
Phase 0's description of the bundled ``v4_local_defender``: with a declared
reach of 2 its patrol offset cycles ``1, 0, 1, 0``, so it writes exactly
**two** addresses for the whole match and never inspects or repairs the
other six cells of its own core. Phase 0's "infinite repair equilibrium"
was therefore never a repair race across eight cells.

This agent is what that description claimed the bundled defender was: it
stations itself so that all eight of its own core cells are inside ordinary
reach, READs them in rotation to learn which ones an opponent has taken,
and repairs what it finds lost, prioritising repair over patrol.

It is deliberately *not* a strong attacker. Its only offensive path is
opportunistic and local: an enemy anchor inside reach is written (which
disrupts it for D=1 and applies real pressure), and if its own core is
currently intact it will spend spare actions pressing a region around that
contact, which is a genuine legal path from contact to core damage. It
never searches, so against an opponent that never comes to it, it does
nothing offensive at all. That is the archetype's retained weakness.

Legal-information sources (Agent API v2 only): ``own_core_base`` and
``own_core_size`` -- ITS OWN core, exactly the fields the bundled
``v4_local_defender`` and ``v4_defender_scout`` already read;
``previous_read_value``/``previous_read_owner``/``previous_action_applied``
from its own READ actions; the ordinary ``visible_enemy_anchor_addresses``
sensor channel; ``self_anchor``; ``self_reach``; and
``context.arena_size``/``context.agent_id``. It never receives an enemy
core coordinate, the R2 oracle, process integrity, or any ownership map
beyond what its own READs return one cell at a time.
"""

from battle_engine.agent_api import (
    ActionKindV2,
    AgentAction,
    MatchContextV2,
    ObservationV2,
    ProcessDeclaration,
)

# How long a contact stays actionable for the opportunistic counter-attack.
COUNTER_MEMORY_TICKS = 40

# Inspection duty cycle: READs of its own core guaranteed per tick, out of
# the Q=8 entrant quota. Half the budget covers all eight cells every two
# ticks while leaving half for repair, disruption and counter-pressure.
#
# This constant exists because the first draft of this agent did not have
# one and failed its own archetype on development seeds: with an enemy
# anchor inside reach it disrupted on every single action, never inspected,
# and therefore never repaired -- reproducing exactly the defect R3
# Section C.1 identified in the bundled ``v4_local_defender``, which
# abandons its patrol whenever an enemy is within reach. A defender that
# can be made to stop defending simply by standing next to it is not an
# objective-capable defender, so inspection is now a reserved duty rather
# than something offence can starve.
INSPECTIONS_PER_TICK = 4


class CoreWardenAgent:
    """Single-process warden: inspect, repair, and hold its own eight cells."""

    def reset(self, context: MatchContextV2) -> None:
        self.context = context
        self.arena = context.arena_size
        self.signature = 0xCD

        self.repair_queue: list[int] = []
        self.inspect_cursor = 0
        self.pending_read: int | None = None
        self.last_contact: int | None = None
        self.last_contact_tick = -1
        self.counter_cursor = 0
        self.perimeter_cursor = 0
        self.tick_marker = -1
        self.inspect_budget = INSPECTIONS_PER_TICK

    def declare_processes(self) -> list[ProcessDeclaration]:
        return [ProcessDeclaration(id="warden", reach=self._reach(12), share=1.0)]

    def act(self, observation: ObservationV2) -> AgentAction:
        self._consume_read_feedback(observation)
        self._begin_tick(observation.current_tick)
        self._observe(observation)

        core_size = max(1, observation.own_core_size)
        base = observation.own_core_base % self.arena
        station = (base + core_size // 2) % self.arena

        # Hold the station from which the whole core is inspectable and
        # repairable. Everything else is subordinate to this.
        if not self._region_in_reach(observation, base, core_size):
            return self._move_toward(observation, station)

        # 1. Repair what is known to be lost. Highest priority: a cell the
        #    opponent holds is direct progress toward this entrant's death.
        while self.repair_queue:
            address = self.repair_queue.pop(0)
            if self._within_reach(observation, address):
                return AgentAction(
                    kind=ActionKindV2.WRITE, operand=address, value=self.signature
                )

        # 2. Reserved inspection duty. Offence may use the actions this
        #    leaves over, but may never consume the inspection budget --
        #    that is the difference between this agent and the bundled
        #    two-address patroller.
        if self.inspect_budget > 0:
            self.inspect_budget -= 1
            offset = self.inspect_cursor % core_size
            self.inspect_cursor += 1
            address = (base + offset) % self.arena
            if self._within_reach(observation, address):
                self.pending_read = address
                return AgentAction(kind=ActionKindV2.READ, operand=address)

        # 3. Disrupt an enemy standing inside reach. A write onto a live
        #    anchor disrupts it for D=1, which is the cheapest defensive
        #    action available in stable V4.
        for address in sorted(set(observation.visible_enemy_anchor_addresses)):
            if self._within_reach(observation, address):
                return AgentAction(
                    kind=ActionKindV2.WRITE, operand=address, value=self.signature
                )

        # 4. Opportunistic pressure: with a remembered contact nearby, press
        #    a region around it rather than idling. This is the archetype's
        #    only path from contact to enemy core damage.
        contact = self.last_contact
        if (
            contact is not None
            and observation.current_tick - self.last_contact_tick <= COUNTER_MEMORY_TICKS
        ):
            offset = self.counter_cursor % core_size
            self.counter_cursor += 1
            address = (contact + offset) % self.arena
            if self._within_reach(observation, address):
                return AgentAction(
                    kind=ActionKindV2.WRITE, operand=address, value=self.signature
                )

        # 5. Nothing to repair and nobody to fight: hold ground around the
        #    objective. Claiming the perimeter inside reach denies an
        #    approaching opponent free adjacent territory and is the only
        #    thing this agent ever does with an otherwise idle action.
        return AgentAction(
            kind=ActionKindV2.WRITE,
            operand=self._next_perimeter_cell(observation, base, core_size),
            value=self.signature,
        )

    def _begin_tick(self, tick: int) -> None:
        if tick == self.tick_marker:
            return
        self.tick_marker = tick
        self.inspect_budget = INSPECTIONS_PER_TICK

    def _next_perimeter_cell(
        self, obs: ObservationV2, base: int, core_size: int
    ) -> int:
        """Cycle outward through reachable cells bracketing the core."""

        span = max(1, obs.self_reach)
        index = self.perimeter_cursor % (2 * span)
        self.perimeter_cursor += 1
        if index < span:
            address = (base - 1 - index) % self.arena
        else:
            address = (base + core_size + (index - span)) % self.arena
        if self._within_reach(obs, address):
            return address
        return (base + (index % core_size)) % self.arena

    # -- observation -----------------------------------------------------

    def _observe(self, obs: ObservationV2) -> None:
        visible = sorted(set(obs.visible_enemy_anchor_addresses))
        if not visible:
            return
        self.last_contact = min(
            visible, key=lambda a: (self._distance(a, obs.self_anchor), a)
        )
        self.last_contact_tick = obs.current_tick

    def _consume_read_feedback(self, obs: ObservationV2) -> None:
        probe = self.pending_read
        self.pending_read = None
        if probe is None or not obs.previous_action_applied:
            return
        owner = obs.previous_read_owner
        if owner != self.context.agent_id and probe not in self.repair_queue:
            self.repair_queue.append(probe)

    # -- geometry --------------------------------------------------------

    def _move_toward(self, obs: ObservationV2, target: int) -> AgentAction:
        return AgentAction(
            kind=ActionKindV2.MOVE,
            operand=self._clamp(self._shortest_delta(target, obs.self_anchor)),
        )

    def _region_in_reach(self, obs: ObservationV2, base: int, core_size: int) -> bool:
        return all(
            self._within_reach(obs, (base + i) % self.arena) for i in range(core_size)
        )

    def _within_reach(self, obs: ObservationV2, address: int) -> bool:
        return self._distance(obs.self_anchor, address) <= obs.self_reach

    def _distance(self, a: int, b: int) -> int:
        delta = abs((a - b) % self.arena)
        return min(delta, self.arena - delta)

    def _shortest_delta(self, target: int, anchor: int) -> int:
        forward = (target - anchor) % self.arena
        backward = forward - self.arena
        return backward if abs(backward) < abs(forward) else forward

    def _reach(self, desired: int) -> int:
        return max(1, min(desired, self.arena - 1))

    @staticmethod
    def _clamp(delta: int) -> int:
        return max(-64, min(64, delta))


def create_agent():
    return CoreWardenAgent()
