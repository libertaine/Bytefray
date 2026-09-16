"""R4 archetype B -- mobile reconnaissance attacker (RESEARCH ONLY).

Not a starter, not a shipped example, not a member of the canonical V4
population. See ``tools/research/v5/agents/README.md``.

Strategic identity: search first, then convert. This entrant actively
crosses the arena looking for an opponent, and its target acquisition is
deliberately *different in kind* from archetype A's: where
``v5r4_siege_regional`` infers a core base from the address at which an
enemy anchor was first sighted, this agent builds its target from
**READ-derived ownership evidence** -- it probes addresses, records which
ones report an enemy owner, and strikes the longest contiguous run of
enemy-held cells it has found. That is a slower, costlier, but more general
acquisition path: it works against an opponent that was never sighted at
its own core base, and it degrades gracefully when the evidence is thin.

This agent is NOT R3's ``v5r3_region_sweeper_mobile``. R3 Section M.5
measured that variant as materially worse than the bundled baseline
(5-39-52, its own core captured three times as often), and Section K.2
diagnosed why: it repositioned out of sensor range, lost its target, and
drifted, because ``reach`` is simultaneously the write radius and the sensor
radius and that agent had no memory. The two deliberate design responses
here, both fixed before any evaluation seed was run, are (1) a large
declared reach so search and strike do not fight each other, and (2)
persistent contact/ownership memory so losing sight of a target does not
erase knowledge of it.

Archetype-consistent weakness, retained deliberately: it spends a large
fraction of its Q=8 budget on movement and probing rather than on writes,
so it applies pressure late and holds it thinly. It never repairs its own
core.

Legal-information sources (Agent API v2 only): the ordinary
``visible_enemy_anchor_addresses`` sensor channel; ``previous_read_owner``
and ``previous_action_applied`` from its own READ actions; its OWN
``own_core_base``/``own_core_size``; ``self_anchor``; ``self_reach``; and
``context.arena_size``/``context.agent_id``. No enemy core coordinate, no
oracle, no privileged engine state, no hard-coded opponent start address.
"""

from battle_engine.agent_api import (
    ActionKindV2,
    AgentAction,
    MatchContextV2,
    ObservationV2,
    ProcessDeclaration,
)

# How long READ-derived ownership evidence stays actionable. Ownership can
# change under the agent's feet, so evidence expires rather than accumulating
# forever into a stale map.
EVIDENCE_MEMORY_TICKS = 300

# Probe budget: one reconnaissance READ per this many actions while a strike
# target is already established, so the agent keeps refining its picture
# without abandoning pressure.
PROBE_EVERY = 6


class ReconStrikerAgent:
    """Mobile searcher whose strike target comes from READ ownership evidence."""

    def reset(self, context: MatchContextV2) -> None:
        self.context = context
        self.arena = context.arena_size
        self.signature = 0x7B

        # address -> tick it was last observed to be enemy-held
        self.enemy_cells: dict[int, int] = {}
        self.last_contact: int | None = None
        self.last_contact_tick = -1

        self.pending_read: int | None = None
        self.actions_since_probe = 0
        self.probe_spread = 0
        self.sweep_cursor = 0
        self.search_cursor = 0

    def declare_processes(self) -> list[ProcessDeclaration]:
        return [ProcessDeclaration(id="striker", reach=self._reach(40), share=1.0)]

    def act(self, observation: ObservationV2) -> AgentAction:
        self._consume_read_feedback(observation)
        self._observe(observation)
        self._expire(observation.current_tick)
        self.actions_since_probe += 1

        core_size = max(1, observation.own_core_size)
        base = self._strike_base(core_size)

        if base is None:
            return self._reconnoitre(observation)

        station = (base + core_size // 2) % self.arena
        if not self._region_in_reach(observation, base, core_size):
            return self._move_toward(observation, station)

        # Keep refining the ownership picture while under way.
        if self.actions_since_probe >= PROBE_EVERY:
            probe = self._next_probe(base, core_size)
            if self._within_reach(observation, probe):
                self.actions_since_probe = 0
                self.pending_read = probe
                return AgentAction(kind=ActionKindV2.READ, operand=probe)

        offset = self.sweep_cursor % core_size
        self.sweep_cursor += 1
        address = (base + offset) % self.arena
        if not self._within_reach(observation, address):
            return self._move_toward(observation, station)
        return AgentAction(
            kind=ActionKindV2.WRITE, operand=address, value=self.signature
        )

    # -- observation -----------------------------------------------------

    def _observe(self, obs: ObservationV2) -> None:
        visible = sorted(set(obs.visible_enemy_anchor_addresses))
        if not visible:
            return
        nearest = min(
            visible, key=lambda a: (self._distance(a, obs.self_anchor), a)
        )
        self.last_contact = nearest
        self.last_contact_tick = obs.current_tick
        # A live anchor is standing on a cell; that is ownership evidence of
        # exactly the same kind a READ would return, obtained for free.
        for address in visible:
            self.enemy_cells[address] = obs.current_tick

    def _consume_read_feedback(self, obs: ObservationV2) -> None:
        probe = self.pending_read
        self.pending_read = None
        if probe is None or not obs.previous_action_applied:
            return
        owner = obs.previous_read_owner
        if owner is not None and owner != self.context.agent_id:
            self.enemy_cells[probe % self.arena] = obs.current_tick
        else:
            self.enemy_cells.pop(probe % self.arena, None)

    def _expire(self, tick: int) -> None:
        stale = [
            address
            for address, seen in self.enemy_cells.items()
            if tick - seen > EVIDENCE_MEMORY_TICKS
        ]
        for address in stale:
            del self.enemy_cells[address]

    # -- target selection ------------------------------------------------

    def _strike_base(self, core_size: int) -> int | None:
        """Base of the longest contiguous run of known enemy-held cells.

        Ties are broken on the most recent evidence and then on the lowest
        address, so selection is a pure deterministic function of the
        evidence set and never depends on dict or set iteration order.
        """

        if not self.enemy_cells:
            return None
        known = sorted(self.enemy_cells)
        best: tuple[int, int, int] | None = None
        best_start: int | None = None
        for start in known:
            if (start - 1) % self.arena in self.enemy_cells:
                continue  # not the start of a run
            length = 0
            recency = -1
            while length < core_size:
                address = (start + length) % self.arena
                seen = self.enemy_cells.get(address)
                if seen is None:
                    break
                recency = max(recency, seen)
                length += 1
            candidate = (length, recency, -start)
            if best is None or candidate > best:
                best = candidate
                best_start = start
        if best is None or best_start is None:
            # Every known cell sits inside a wrapped run; fall back to the
            # lowest known address, which is still deterministic.
            return known[0]
        # A run shorter than the core is still the best evidence available,
        # but the strike window is anchored so the run sits inside it.
        return best_start % self.arena

    def _next_probe(self, base: int, core_size: int) -> int:
        """Walk outward from the strike window looking for more enemy cells."""

        self.probe_spread = (self.probe_spread + 1) % (2 * core_size)
        if self.probe_spread < core_size:
            return (base - 1 - self.probe_spread) % self.arena
        return (base + core_size + (self.probe_spread - core_size)) % self.arena

    # -- search ----------------------------------------------------------

    def _reconnoitre(self, obs: ObservationV2) -> AgentAction:
        """Cross the arena in reach-sized strides, probing as it goes.

        Alternating MOVE and READ is what makes this archetype a genuine
        searcher rather than a drifter: the READ turns a position it has
        merely passed through into ownership evidence it can act on later.
        """

        remembered = self.last_contact
        if (
            remembered is not None
            and obs.current_tick - self.last_contact_tick <= EVIDENCE_MEMORY_TICKS
            and not self._within_reach(obs, remembered)
        ):
            return self._move_toward(obs, remembered)

        self.search_cursor += 1
        if self.search_cursor % 3 == 0:
            probe = (obs.self_anchor + obs.self_reach) % self.arena
            if self._within_reach(obs, probe):
                self.pending_read = probe
                return AgentAction(kind=ActionKindV2.READ, operand=probe)
        return AgentAction(
            kind=ActionKindV2.MOVE, operand=self._clamp(max(1, obs.self_reach))
        )

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
    return ReconStrikerAgent()
