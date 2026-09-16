"""Bytefray V5 starter -- Scout Striker.

THE LESSON: search, remember, then strike.

A process senses only as far as its declared reach, so on a 512-cell arena
an agent that never moves usually never meets anybody.  This agent spends
its early actions crossing ground, and the moment it legitimately detects
an enemy it writes that address into a small memory and switches from
searching to attacking.  The memory is what makes it a *hunter* rather
than a drifter: it can keep pressing a contact for a while even after the
contact slips back out of sensor range.

WHAT THIS AGENT IS ALLOWED TO KNOW
    Only ``ObservationV2``.  A contact exists for this agent because one
    of its own processes was close enough to sense it -- there is no map,
    no enemy core address, and no way to ask where the opponent started.
    When the memory goes stale the agent genuinely does not know where the
    enemy is any more, and goes back to searching.

HOW IT DIFFERS FROM ``v5_region_attacker``
    The region attacker holds station beside whatever it can currently
    see and keeps no memory at all.  This agent declares a much larger
    reach, crosses the arena in deliberate strides, remembers a contact
    for a bounded number of ticks, and scans its strike window from the
    low address upward rather than expanding outward from the centre.

ITS TWO PARAMETERS
    ``agent.yaml`` declares the two numbers this strategy is actually
    built out of -- how long a sighting stays worth attacking
    (``contact_memory_ticks``) and how far each search step moves
    (``search_stride_divisor``) -- and the engine hands their resolved
    values to ``reset`` on ``context.parameters``.  The defaults are
    exactly the constants below.  See docs/AGENT_API_V2.md.
"""

from battle_engine.agent_api import (
    ActionKindV2,
    AgentAction,
    MatchContextV2,
    ObservationV2,
    ProcessDeclaration,
)

# A large reach so searching and striking do not fight each other: with a
# small reach, moving far enough to cover a wide strike window pushes the
# target out of sensor range and the agent loses it.
STRIKER_REACH = 40

SIGNATURE = 0x5B

# How long a remembered contact stays worth attacking.  Long enough to
# finish pressing a region, short enough that the agent gives up on a
# vanished opponent and resumes searching rather than bombarding empty
# ground for the rest of the match.
CONTACT_MEMORY_TICKS = 60

# Divides the search stride.  1 means one full reach per action, so
# consecutive actions sense adjacent, non-overlapping bands.
SEARCH_STRIDE_DIVISOR = 1

MAX_MOVE_DELTA = 64


class ScoutStrikerAgent:
    """One process that searches the arena, then strikes what it found."""

    def reset(self, context: MatchContextV2) -> None:
        self.context = context
        self.arena = context.arena_size
        self.signature = SIGNATURE
        # Parameters arrive already validated and coerced against the schema
        # in agent.yaml; the fallbacks are that schema's own declared
        # defaults, so this file behaves identically with or without one.
        self.contact_memory_ticks = int(
            context.parameters.get("contact_memory_ticks", CONTACT_MEMORY_TICKS)
        )
        self.search_stride_divisor = int(
            context.parameters.get("search_stride_divisor", SEARCH_STRIDE_DIVISOR)
        )
        # Three small pieces of state: what we last saw, when we saw it,
        # and how far through the strike window we are.
        self.last_contact: int | None = None
        self.last_contact_tick = -1
        self.strike_cursor = 0

    def declare_processes(self) -> list[ProcessDeclaration]:
        return [
            ProcessDeclaration(
                id="striker", reach=self._reach(STRIKER_REACH), share=1.0
            )
        ]

    def act(self, observation: ObservationV2) -> AgentAction:
        self._remember_contact(observation)
        target = self._remembered_contact(observation.current_tick)

        # SEARCH: nothing known, so cover new ground.  A stride of one full
        # reach means consecutive actions sense adjacent, non-overlapping
        # bands, and always in the same direction so the search is a
        # predictable lap of the arena rather than a random walk.  Dividing
        # the stride trades ground covered for a second look at each band.
        if target is None:
            return AgentAction(
                kind=ActionKindV2.MOVE,
                operand=self._clamp(self._search_stride(observation)),
            )

        # APPROACH: close until the whole strike window is inside reach,
        # not merely until the contact is touchable.  An agent that stops
        # at maximum range can only ever write the near half of its own
        # window -- the far half stays out of reach for the whole match.
        if self._distance(target, observation.self_anchor) > self._press_margin(
            observation
        ):
            return self._move_toward(observation, target)

        # STRIKE.
        return AgentAction(
            kind=ActionKindV2.WRITE,
            operand=self._next_strike_address(observation, target),
            value=self.signature,
        )

    def _search_stride(self, observation: ObservationV2) -> int:
        """How far one search step moves, always at least one cell."""

        return max(1, observation.self_reach // self.search_stride_divisor)

    # -- memory ----------------------------------------------------------

    def _remember_contact(self, observation: ObservationV2) -> None:
        """Record the nearest thing we can currently see, with its tick."""

        visible = observation.visible_enemy_anchor_addresses
        if not visible:
            return
        self.last_contact = min(
            visible, key=lambda a: (self._distance(a, observation.self_anchor), a)
        )
        self.last_contact_tick = observation.current_tick

    def _remembered_contact(self, tick: int) -> int | None:
        """The remembered contact, or ``None`` once it has gone stale."""

        if self.last_contact is None:
            return None
        if tick - self.last_contact_tick > self.contact_memory_ticks:
            return None
        return self.last_contact

    # -- the strike window -----------------------------------------------

    def _press_margin(self, observation: ObservationV2) -> int:
        """How far from the contact we may sit and still cover the window.

        The window reaches one core width either side of the contact, so an
        anchor this close to it can legally write every address in it.
        """

        return max(0, observation.self_reach - max(1, observation.own_core_size))

    def _next_strike_address(self, observation: ObservationV2, target: int) -> int:
        """Scan a window two core widths wide, low address to high.

        ``own_core_size`` is OUR core's width -- the engine never tells an
        attacker the enemy's.  Using it here assumes the opponent is built
        the same way we are, which is a guess about the rules rather than
        secret knowledge, and it keeps a bare ``8`` out of the source.  The
        window starts one core width *below* the contact so it still covers
        the enemy core when the contact sits at the core's far end.

        Addresses outside our reach are skipped, never written: the engine
        rejects an out-of-reach write and the wasted action still counts.
        """

        core_size = max(1, observation.own_core_size)
        span = 2 * core_size
        for _ in range(span):
            offset = (self.strike_cursor % span) - core_size
            self.strike_cursor += 1
            address = (target + offset) % self.arena
            if self._within_reach(observation, address):
                return address
        return target % self.arena

    # -- geometry --------------------------------------------------------

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


def create_agent() -> ScoutStrikerAgent:
    return ScoutStrikerAgent()
