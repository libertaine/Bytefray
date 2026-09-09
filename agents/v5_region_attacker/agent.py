"""Bytefray V5 starter -- Regional Attacker.

THE LESSON: the objective is a REGION, not a point.

An entrant in Bytefray dies when it owns *none* of the cells of its own
core.  One cell is not enough, and one cell is exactly what you get if you
pick an enemy address and write to it forever -- the classic beginner
mistake.  This agent is the smallest complete example of the fix: once it
can legally see an enemy, it walks a bounded sweep of addresses around
that contact instead of hammering a single one.

WHAT THIS AGENT IS ALLOWED TO KNOW
    Everything it uses arrives through ``ObservationV2``:
    ``visible_enemy_anchor_addresses`` (where enemy processes are, but only
    while one of our processes is close enough to sense them),
    ``self_anchor``/``self_reach`` (where we are and how far we can act),
    and ``own_core_size`` (the width of OUR core).

    It is never told where the enemy core is, how wide it is, or which
    cells it owns.  That is why the sweep is centred on a *contact* rather
    than on an enemy core address: a contact is something we legitimately
    observed, an enemy core coordinate is something we would have to
    cheat to obtain.

WHY THE SWEEP IS AS WIDE AS OUR OWN CORE
    We need a width for the region to press, and the only width the engine
    hands us is ``own_core_size``.  Assuming the opponent is built like us
    is an honest guess a human player would also make -- and it keeps a
    bare literal ``8`` out of this file, so the agent still behaves
    sensibly if the core width ever changes.
"""

from battle_engine.agent_api import (
    ActionKindV2,
    AgentAction,
    MatchContextV2,
    ObservationV2,
    ProcessDeclaration,
)

# Reach is both our write radius and our sensor radius, so it is a real
# trade-off rather than a free parameter: wider reach covers more of the
# region in one place, narrower reach makes contact rarer.  16 comfortably
# covers a core-width sweep on either side of a contact.
ATTACKER_REACH = 16

# The byte we stamp on every cell we take.  Cells are owned by whoever
# wrote them last, so any value works; a distinct one just makes replays
# easy to read.
SIGNATURE = 0xA5

# The engine clamps a MOVE to this many cells per action; saying so here
# keeps the code honest about what actually happens.
MAX_MOVE_DELTA = 64


class RegionAttackerAgent:
    """One process: approach the nearest contact, then sweep around it."""

    def reset(self, context: MatchContextV2) -> None:
        self.context = context
        self.arena = context.arena_size
        self.signature = SIGNATURE
        # The only state this agent keeps: how far along the sweep we are.
        # It never resets, so the sweep keeps rotating over the region
        # instead of restarting at the centre on every new contact.
        self.sweep_cursor = 0

    def declare_processes(self) -> list[ProcessDeclaration]:
        return [
            ProcessDeclaration(
                id="attacker", reach=self._reach(ATTACKER_REACH), share=1.0
            )
        ]

    def act(self, observation: ObservationV2) -> AgentAction:
        target = self._nearest_contact(observation)

        # Nothing in sensor range: drift forward a reach-width at a time so
        # the sensor sweeps fresh ground with every action.
        if target is None:
            return AgentAction(
                kind=ActionKindV2.MOVE,
                operand=self._clamp(max(1, observation.self_reach)),
            )

        # Close until the WHOLE region we mean to press is inside reach --
        # not merely until the contact itself is touchable.  Stopping at
        # maximum range is the classic mistake: from there the far half of
        # the region is still out of reach, the sweep quietly skips it, and
        # the opponent keeps the cells we never manage to write.  Leaving a
        # core width of margin makes every address of the sweep legal.
        if self._distance(target, observation.self_anchor) > self._press_margin(
            observation
        ):
            return self._move_toward(observation, target)

        return AgentAction(
            kind=ActionKindV2.WRITE,
            operand=self._next_sweep_address(observation, target),
            value=self.signature,
        )

    # -- the sweep -------------------------------------------------------

    def _press_margin(self, observation: ObservationV2) -> int:
        """How far from the contact we may sit and still cover the region.

        The sweep runs one core width either side of the contact, so an
        anchor within ``reach - core_size`` of it can legally write every
        address in that window.  ATTACKER_REACH is comfortably more than a
        core width, which is what makes this margin positive.
        """

        return max(0, observation.self_reach - max(1, observation.own_core_size))

    def _sweep_offsets(self, core_size: int) -> list[int]:
        """Offsets from the contact, in the order we press them.

        0, +1, -1, +2, -2, ... out to one core width on each side, so the
        region grows outward from the contact and covers the opponent's
        core whichever side of the contact it happens to lie on.
        """

        offsets = [0]
        for step in range(1, core_size + 1):
            offsets.append(step)
            offsets.append(-step)
        return offsets

    def _next_sweep_address(self, observation: ObservationV2, target: int) -> int:
        """Advance the sweep to the next address we can legally write.

        An address further than our reach is skipped rather than written:
        the engine would reject it, and the rejection would still cost the
        action.  Offset 0 is the contact itself, which we already know is
        in reach, so this always finds an address.
        """

        offsets = self._sweep_offsets(max(1, observation.own_core_size))
        for _ in range(len(offsets)):
            offset = offsets[self.sweep_cursor % len(offsets)]
            self.sweep_cursor += 1
            address = (target + offset) % self.arena
            if self._within_reach(observation, address):
                return address
        return target % self.arena

    # -- geometry --------------------------------------------------------

    def _nearest_contact(self, observation: ObservationV2) -> int | None:
        """The closest visible enemy anchor, or ``None`` if we see nobody.

        ``visible_enemy_anchor_addresses`` is sorted by address, not by
        distance, so picking element 0 would sometimes chase the far one.
        The address itself breaks ties so the choice stays deterministic.
        """

        visible = observation.visible_enemy_anchor_addresses
        if not visible:
            return None
        return min(
            visible, key=lambda a: (self._distance(a, observation.self_anchor), a)
        )

    def _move_toward(self, observation: ObservationV2, target: int) -> AgentAction:
        return AgentAction(
            kind=ActionKindV2.MOVE,
            operand=self._clamp(self._shortest_delta(target, observation.self_anchor)),
        )

    def _within_reach(self, observation: ObservationV2, address: int) -> bool:
        return self._distance(observation.self_anchor, address) <= observation.self_reach

    def _distance(self, a: int, b: int) -> int:
        """Circular distance -- the arena wraps, so 1 and arena-1 are close."""

        delta = abs((a - b) % self.arena)
        return min(delta, self.arena - delta)

    def _shortest_delta(self, target: int, anchor: int) -> int:
        forward = (target - anchor) % self.arena
        backward = forward - self.arena
        return backward if abs(backward) < abs(forward) else forward

    def _reach(self, desired: int) -> int:
        """Reach must be an integer in [1, arena_size - 1]."""

        return max(1, min(desired, self.arena - 1))

    @staticmethod
    def _clamp(delta: int) -> int:
        return max(-MAX_MOVE_DELTA, min(MAX_MOVE_DELTA, delta))


def create_agent() -> RegionAttackerAgent:
    return RegionAttackerAgent()
