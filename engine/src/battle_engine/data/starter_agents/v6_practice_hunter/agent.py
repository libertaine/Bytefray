"""Bytefray V6 practice opponent -- Practice Hunter.

A PRACTICE OPPONENT, NOT A TEACHING AGENT. The three teaching starters each
show one Active Sensing mechanic against controlled fixtures; none of them
plays to win. Practice Hunter does: it searches, attacks what it finds and
repairs its own core, so that a development test, a first match or a
Spectator viewing shows a real contest. It makes no balance claim and is not
tuned to be strong; it is a fixed, readable sparring partner.

HOW IT PLAYS (two processes sharing this object's memory)
    hunter (reach 128, three quarters of the actions)
        SEARCH  SENSE windows ahead of and behind its anchor, then MOVE one
                step around the ring, turning back after each full lap (so an
                opponent roaming the same way cannot stay out of range). Once
                a sensed contact turns out to be away from its core, SEARCH
                also READs the cells it passes, at a stride of 8.
        PROBE   On a delivered contact, MOVE close to it, then READ the
                contact and cells around it at a stride of 8 (any 8-cell core
                there must show up). If the opponent owns the contact cell
                itself, the 8 cells from it are written in turn for a few
                rounds (a process starts on its core base); any other cell
                the opponent owns is taken over with a band of WRITEs.
        CONFIRM When the probes run out, SENSE the contact again: a fresh
                contact starts a new probe round; an empty receipt returns
                it to SEARCH.
    keeper (reach 32, one quarter of the actions)
        Stays at its own core, READs the core cells in turn and rewrites any
        cell another entrant owns.

WHAT THIS AGENT IS ALLOWED TO KNOW
    Only ObservationV2 and MatchContextV2, exactly like any user agent. It
    probes only around a contact a SENSE receipt delivered, and attacks only
    cells a READ reported as owned by another entrant. It never reads
    placement seeds, the RNG, the opponent's identity or any engine state.
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

HUNTER = "hunter"
KEEPER = "keeper"
HUNTER_REACH = 128
KEEPER_REACH = 32
HUNTER_SHARE = 0.75
#: Where SEARCH senses, relative to the hunter's anchor; then one MOVE.
SEARCH_OFFSETS = (55, 110, -55, -110)
SEARCH_STEP = 64
#: PROBE reads every PROBE_STRIDE cells out to PROBE_RADIUS around a contact,
#: nearest first. A stride no wider than a core cannot step over one.
PROBE_STRIDE = 8
PROBE_RADIUS = 64
#: Close until every probe address is inside reach.
APPROACH_LIMIT = HUNTER_REACH - PROBE_RADIUS
#: Cells written on each side of an opponent-owned cell: enough to cover any
#: 8-cell core that contains it.
TAKEOVER_SPAN = 7
#: A process starts on its core base, so an opponent-owned cell at the contact
#: itself suggests the core is the 8 cells from the contact. Those 8 are then
#: written in turn this many times before the contact is sensed again.
SIEGE_ROUNDS = 6
ATTACK_VALUE = 0x50
REPAIR_VALUE = 0x52


class PracticeHunterAgent(AgentV2):
    """A small competitive opponent: search, probe, take over; keep the core."""

    def reset(self, context: MatchContextV2) -> None:
        self.arena = context.arena_size
        self.agent_id = context.agent_id
        self.sensing_window = context.sensing_window
        self.search_plan: list[tuple[ActionKindV2, int]] = []
        self.search_moves = 0
        self.sweeping = False
        self.round_took = False
        self.fruitless: set[int] = set()
        self.contact: int | None = None
        self.probes: list[int] = []
        self.writes: list[int] = []
        self.hunter_previous: AgentAction | None = None
        self.keeper_cursor = 0
        self.keeper_previous: AgentAction | None = None

    def declare_processes(self) -> list[ProcessDeclaration]:
        return [
            ProcessDeclaration(id=HUNTER, reach=HUNTER_REACH, share=HUNTER_SHARE),
            ProcessDeclaration(id=KEEPER, reach=KEEPER_REACH, share=1.0 - HUNTER_SHARE),
        ]

    def act(self, observation: ObservationV2) -> AgentAction:
        if observation.self_process_id == KEEPER:
            return self._keep(observation)
        previous, self.hunter_previous = self.hunter_previous, None
        action = self._hunt(observation, previous)
        self.hunter_previous = action
        return action

    # -- hunter ---------------------------------------------------------
    def _hunt(self, observation: ObservationV2, previous: AgentAction | None) -> AgentAction:
        own_core = self._own_core(observation)
        receipt = observation.previous_sense_anchors
        confirming = self.contact is not None and not self.probes and not self.writes
        if receipt is not None and self.contact is not None and confirming and not self.round_took:
            # A whole probe round around this contact found no opponent cell, so
            # its core lies elsewhere (it moved away from it). Leave that anchor
            # alone and, from now on, READ the cells SEARCH passes as well.
            self.sweeping = True
            self.fruitless.add(self.contact)
            self.contact = None
            receipt = tuple(anchor for anchor in receipt if anchor not in self.fruitless)
        fresh = tuple(anchor for anchor in receipt or () if anchor not in self.fruitless)
        if fresh:
            self.contact = min(fresh, key=lambda anchor: self._distance(anchor, observation.self_anchor))
            self.probes = self._probe_addresses(self.contact, own_core)
            self.round_took = False
        elif receipt is not None and confirming:
            self.contact = None  # The confirming scan found nobody: search again.
        if (
            previous is not None
            and previous.kind == ActionKindV2.READ
            and observation.previous_action_applied is True
            and observation.previous_read_owner not in (None, self.agent_id)
            and previous.operand is not None
            and previous.operand not in own_core
        ):
            taken = previous.operand
            if taken == self.contact:
                size = max(1, observation.own_core_size)
                band = [(taken + offset) % self.arena for offset in range(size)] * SIEGE_ROUNDS
            else:
                band = [(taken + offset) % self.arena for offset in range(-TAKEOVER_SPAN, TAKEOVER_SPAN + 1)]
            self.writes = [address for address in band if address not in own_core] + self.writes
            self.round_took = True
            if self.contact is None:
                self.contact = taken  # Found while sweeping: take it over, then search on.

        contact = self.contact
        if contact is not None:
            delta = self._delta(contact, observation.self_anchor)
            if abs(delta) > APPROACH_LIMIT:
                return AgentAction(ActionKindV2.MOVE, operand=self._clamp(delta))
            while self.writes:
                address = self.writes.pop(0)
                if self._in_reach(observation, address):
                    return AgentAction(ActionKindV2.WRITE, operand=address, value=ATTACK_VALUE)
            while self.probes:
                address = self.probes.pop(0)
                if self._in_reach(observation, address):
                    return AgentAction(ActionKindV2.READ, operand=address)
            return AgentAction(ActionKindV2.SENSE, operand=contact)

        if self.sensing_window is None:  # Not an Active Sensing match: stay legal.
            return AgentAction(ActionKindV2.READ, operand=observation.own_core_base)
        if not self.search_plan:
            self.search_plan = self._search_cycle()
        kind, offset = self.search_plan.pop(0)
        if kind == ActionKindV2.MOVE:
            return AgentAction(ActionKindV2.MOVE, operand=offset)
        address = (observation.self_anchor + offset) % self.arena
        if kind == ActionKindV2.READ and address in own_core:
            return AgentAction(ActionKindV2.SENSE, operand=(observation.self_anchor + SEARCH_OFFSETS[0]) % self.arena)
        return AgentAction(kind, operand=address)

    def _search_cycle(self) -> list[tuple[ActionKindV2, int]]:
        """One SEARCH step: the SENSE windows, the sweep READs if sweeping, one MOVE."""

        lap = max(1, -(-self.arena // SEARCH_STEP))
        direction = 1 if (self.search_moves // lap) % 2 == 0 else -1
        self.search_moves += 1
        plan = [(ActionKindV2.SENSE, offset) for offset in SEARCH_OFFSETS]
        if self.sweeping:
            plan += [(ActionKindV2.READ, offset) for offset in range(-SEARCH_STEP // 2, SEARCH_STEP // 2, PROBE_STRIDE)]
        return plan + [(ActionKindV2.MOVE, direction * SEARCH_STEP)]

    def _probe_addresses(self, contact: int, own_core: tuple[int, ...]) -> list[int]:
        offsets = sorted(range(-PROBE_RADIUS, PROBE_RADIUS + 1, PROBE_STRIDE), key=abs)
        return [address for address in ((contact + offset) % self.arena for offset in offsets)
                if address not in own_core]

    # -- keeper ---------------------------------------------------------
    def _keep(self, observation: ObservationV2) -> AgentAction:
        core = self._own_core(observation)
        previous, self.keeper_previous = self.keeper_previous, None
        action: AgentAction | None = None
        if (
            previous is not None
            and previous.kind == ActionKindV2.READ
            and observation.previous_action_applied is True
            and observation.previous_read_owner not in (None, self.agent_id)
            and previous.operand is not None
            and self._in_reach(observation, previous.operand)
        ):
            action = AgentAction(ActionKindV2.WRITE, operand=previous.operand, value=REPAIR_VALUE)
        if action is None:
            action = AgentAction(ActionKindV2.READ, operand=core[self.keeper_cursor % len(core)])
            self.keeper_cursor += 1
        self.keeper_previous = action
        return action

    # -- geometry -------------------------------------------------------
    def _own_core(self, observation: ObservationV2) -> tuple[int, ...]:
        size = max(1, observation.own_core_size)
        return tuple((observation.own_core_base + i) % self.arena for i in range(size))

    def _in_reach(self, observation: ObservationV2, address: int) -> bool:
        return self._distance(address, observation.self_anchor) <= observation.self_reach

    def _distance(self, a: int, b: int) -> int:
        delta = (a - b) % self.arena
        return min(delta, self.arena - delta)

    def _delta(self, target: int, anchor: int) -> int:
        forward = (target - anchor) % self.arena
        backward = forward - self.arena
        return backward if abs(backward) < abs(forward) else forward

    @staticmethod
    def _clamp(delta: int) -> int:
        return max(-SEARCH_STEP, min(SEARCH_STEP, delta))


def create_agent() -> PracticeHunterAgent:
    return PracticeHunterAgent()
