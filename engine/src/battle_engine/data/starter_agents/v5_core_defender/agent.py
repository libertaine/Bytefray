"""Bytefray V5 starter -- Core Defender.

THE LESSON: you can only defend what you actually look at.

An entrant dies when it owns none of its own core cells, so a defender's
real job is to notice cells it has lost and take them back.  Noticing
requires READ: the engine reports the value and the *owner* of the cell
this process read last, and an owner that is not us is proof that
something was taken.

The trap this agent is written to avoid: the bundled ``v4_local_defender``
abandons its patrol the moment an enemy comes within reach, so an opponent
that simply stands next to it can make it stop defending altogether.  Here,
inspection is a RESERVED DUTY -- a fixed number of actions every tick that
offence is not allowed to spend.  A defender that can be talked out of
defending is not a defender.

WHAT THIS AGENT IS ALLOWED TO KNOW
    ``own_core_base`` and ``own_core_size`` describe OUR OWN core, and the
    engine hands them to every agent.  There is no equivalent for the
    opponent's core, which is exactly why this agent is a defender and not
    an attacker.  Everything else comes from its own READs and from the
    ordinary ``visible_enemy_anchor_addresses`` sensor channel.

ITS ONE PARAMETER
    ``agent.yaml`` declares ``inspections_per_tick``, the size of that
    reserved duty, and the engine hands its resolved value to ``reset`` on
    ``context.parameters``.  It is the whole lesson expressed as a number:
    set it to 0 and the agent keeps refreshing cells but can no longer tell
    which ones it has actually lost.  See docs/AGENT_API_V2.md.
"""

from battle_engine.agent_api import (
    ActionKindV2,
    AgentAction,
    MatchContextV2,
    ObservationV2,
    ProcessDeclaration,
)

# Wide enough that a single station covers every cell of our core plus a
# little ground around it (it must be at least half a core width, or the
# far end of our own core would be unreachable), narrow enough that we are
# not pretending to be an attacker.
DEFENDER_REACH = 12

SIGNATURE = 0xDF

# Actions per tick reserved for inspecting our own core.  The entrant quota
# is 8 actions per tick, so half the budget re-reads all eight cells every
# two ticks and the other half stays free for repair and disruption.
INSPECTIONS_PER_TICK = 4

MAX_MOVE_DELTA = 64


class CoreDefenderAgent:
    """One process: stand over the core, inspect it, repair what is lost."""

    def reset(self, context: MatchContextV2) -> None:
        self.context = context
        self.arena = context.arena_size
        self.signature = SIGNATURE
        # Already validated and coerced against the schema in agent.yaml;
        # the fallback is that schema's own declared default.
        self.inspections_per_tick = int(
            context.parameters.get("inspections_per_tick", INSPECTIONS_PER_TICK)
        )
        self.repair_queue: list[int] = []
        self.inspect_cursor = 0
        self.pending_read: int | None = None
        self.tick_marker = -1
        self.inspect_budget = self.inspections_per_tick

    def declare_processes(self) -> list[ProcessDeclaration]:
        return [
            ProcessDeclaration(
                id="defender", reach=self._reach(DEFENDER_REACH), share=1.0
            )
        ]

    def act(self, observation: ObservationV2) -> AgentAction:
        self._read_feedback(observation)
        self._refresh_budget(observation.current_tick)

        core_size = max(1, observation.own_core_size)
        base = observation.own_core_base % self.arena
        station = (base + core_size // 2) % self.arena

        # 0. Stand in the middle of the core.  Processes start at the core
        #    base, which is one end of it, so the first thing this agent
        #    ever does is walk to the centre -- from there the furthest
        #    cell is only half a core away and everything is comfortably
        #    inside DEFENDER_REACH.  Nothing else below works from the
        #    wrong place, so this comes first.
        if observation.self_anchor != station:
            return self._move_toward(observation, station)

        # 1. Repair a cell we have proof we lost.  Every cell in enemy
        #    hands is direct progress toward our own death.
        while self.repair_queue:
            address = self.repair_queue.pop(0)
            if self._within_reach(observation, address):
                return self._claim(address)

        # 2. Reserved inspection.  Offence may use whatever actions this
        #    leaves over, but may never consume the inspection budget.
        if self.inspect_budget > 0:
            self.inspect_budget -= 1
            address = (base + self.inspect_cursor % core_size) % self.arena
            self.inspect_cursor += 1
            if self._within_reach(observation, address):
                # Remember which cell we asked about: the answer arrives on
                # our *next* action as previous_read_value / previous_read_owner.
                self.pending_read = address
                return AgentAction(kind=ActionKindV2.READ, operand=address)

        # 3. Push an intruder off. A write onto a live enemy anchor
        #    disrupts that process for a tick, which is the cheapest
        #    defensive action stable V4 offers.
        for address in sorted(set(observation.visible_enemy_anchor_addresses)):
            if self._within_reach(observation, address):
                return self._claim(address)

        # 4. Idle: refresh a core cell anyway.  Inspection only samples the
        #    core a few cells per tick, so blind refreshing covers the gap
        #    between one READ of a cell and the next.  Every write in this
        #    file is reach-checked first; an out-of-reach write is rejected
        #    by the engine and the wasted action still counts against us.
        for _ in range(core_size):
            address = (base + self.inspect_cursor % core_size) % self.arena
            self.inspect_cursor += 1
            if self._within_reach(observation, address):
                return self._claim(address)

        # Our own core is somehow out of reach: get back to the station.
        return self._move_toward(observation, station)

    # -- reading our own core --------------------------------------------

    def _read_feedback(self, observation: ObservationV2) -> None:
        """Turn the answer to our last READ into a repair job, if needed."""

        address = self.pending_read
        self.pending_read = None
        if address is None or not observation.previous_action_applied:
            return
        # ``previous_read_owner`` is the entrant that wrote the cell last.
        # Anything that is not us means the cell has been taken.
        taken = observation.previous_read_owner != self.context.agent_id
        if taken and address not in self.repair_queue:
            self.repair_queue.append(address)

    def _refresh_budget(self, tick: int) -> None:
        if tick != self.tick_marker:
            self.tick_marker = tick
            self.inspect_budget = self.inspections_per_tick

    # -- geometry --------------------------------------------------------

    def _claim(self, address: int) -> AgentAction:
        return AgentAction(
            kind=ActionKindV2.WRITE, operand=address, value=self.signature
        )

    def _move_toward(self, observation: ObservationV2, target: int) -> AgentAction:
        return AgentAction(
            kind=ActionKindV2.MOVE,
            operand=self._clamp(self._shortest_delta(target, observation.self_anchor)),
        )

    def _within_reach(self, observation: ObservationV2, address: int) -> bool:
        return self._distance(observation.self_anchor, address) <= observation.self_reach

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
        return max(-MAX_MOVE_DELTA, min(MAX_MOVE_DELTA, delta))


def create_agent() -> CoreDefenderAgent:
    return CoreDefenderAgent()
