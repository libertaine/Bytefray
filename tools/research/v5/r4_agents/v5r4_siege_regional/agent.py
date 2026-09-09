"""R4 archetype A -- regional pressure attacker (RESEARCH ONLY).

Not a starter, not a shipped example, not a member of the canonical V4
population. See ``tools/research/v5/agents/README.md``.

Strategic identity: a siege engine. It converts a *discovered contact* into
sustained, simultaneous, multi-address pressure across a whole core-width
region, rather than hammering the single address it was handed (the defect
R3 measured in five of the six bundled agents).

Why this is a competence control and not an optimisation: the agent has no
defence whatsoever. It never inspects, repairs, or returns to its own core,
so it is highly vulnerable to being captured itself. Its one strength is
conversion after contact; its search is the bundled attacker's naive drift.

Legal-information sources (Agent API v2 only -- ordinary observation fields
any bundled entrant also receives):

* ``visible_enemy_anchor_addresses`` -- the ordinary entrant-wide sensor
  fusion channel every bundled V4 agent already reads.
* ``previous_read_owner`` -- the ordinary result of its own READ actions,
  used to *verify* a hypothesis rather than to discover hidden state. The
  bundled ``v4_quorum`` reads this same channel.
* ``own_core_size`` -- its OWN core width, used as the (public, symmetric)
  width a core has in this game. The bundled ``v4_quorum`` hard-codes the
  same constant as ``_CORE_ORDER``.
* ``self_anchor``, ``self_reach``, ``context.arena_size``.

It never receives an enemy core coordinate, the R2 objective oracle, process
integrity, opponent RNG state, an ownership map, extra actions, extra reach,
or a hard-coded opponent start address.

The core-base hypothesis is an *inference from a legal observation*, not
privileged data: every process begins the match at its entrant's own core
base (``process_runtime``: ``if p.position is None: p.position = start``),
so the first address at which an enemy is ever seen is evidence about where
that enemy's core is. It is only evidence -- an enemy first seen after it
has already moved yields a wrong hypothesis, which is why this agent spends
actions on READ verification and re-acquires when the evidence contradicts
it. The bundled ``v4_quorum`` performs exactly this inference
(``core_candidates[address] = 100`` at first contact).
"""

from battle_engine.agent_api import (
    ActionKindV2,
    AgentAction,
    MatchContextV2,
    ObservationV2,
    ProcessDeclaration,
)

# Ticks a remembered contact stays actionable after it was last seen. Target
# memory is the property R3 identified as missing from the bundled attackers
# (Section K.2: reach couples sensing to striking, so an agent that moves to
# strike a wider region loses sight of what it is striking).
CONTACT_MEMORY_TICKS = 200

# One verification READ every this many strike actions. Cheap enough not to
# blunt the siege, frequent enough to notice a wrong hypothesis.
VERIFY_EVERY = 24


class SiegeRegionalAgent:
    """Single-process regional siege: hypothesise a core, then saturate it."""

    def reset(self, context: MatchContextV2) -> None:
        self.context = context
        self.arena = context.arena_size
        self.signature = 0x51

        self.base_hypothesis: int | None = None
        self.last_contact_tick = -1
        self.cell_cursor = 0
        self.strikes_since_verify = 0
        self.pending_read: int | None = None
        self.failed_verifications = 0

    def declare_processes(self) -> list[ProcessDeclaration]:
        return [ProcessDeclaration(id="siege", reach=self._reach(24), share=1.0)]

    def act(self, observation: ObservationV2) -> AgentAction:
        self._consume_read_feedback(observation)
        self._observe(observation)

        base = self._active_hypothesis(observation.current_tick)
        if base is None:
            return self._search(observation)

        core_size = max(1, observation.own_core_size)
        station = (base + core_size // 2) % self.arena

        # Stand where the whole hypothesised core is inside ordinary reach,
        # so every cell of it can be rewritten within a single tick.
        if not self._region_in_reach(observation, base, core_size):
            return self._move_toward(observation, station)

        if self.strikes_since_verify >= VERIFY_EVERY:
            self.strikes_since_verify = 0
            probe = (base + (self.cell_cursor % core_size)) % self.arena
            if self._within_reach(observation, probe):
                self.pending_read = probe
                return AgentAction(kind=ActionKindV2.READ, operand=probe)

        offset = self.cell_cursor % core_size
        self.cell_cursor += 1
        self.strikes_since_verify += 1
        address = (base + offset) % self.arena
        if not self._within_reach(observation, address):
            return self._move_toward(observation, station)
        return AgentAction(
            kind=ActionKindV2.WRITE, operand=address, value=self.signature
        )

    # -- observation -----------------------------------------------------

    def _observe(self, obs: ObservationV2) -> None:
        visible = obs.visible_enemy_anchor_addresses
        if not visible:
            return
        nearest = min(
            sorted(set(visible)),
            key=lambda a: (self._distance(a, obs.self_anchor), a),
        )
        self.last_contact_tick = obs.current_tick
        if self.base_hypothesis is None:
            self.base_hypothesis = nearest

    def _consume_read_feedback(self, obs: ObservationV2) -> None:
        probe = self.pending_read
        self.pending_read = None
        if probe is None or not obs.previous_action_applied:
            return
        owner = obs.previous_read_owner
        if owner is not None and owner != self.context.agent_id:
            self.failed_verifications = 0
            return
        # The hypothesised region is not enemy-held. Two consecutive
        # disagreements retire the hypothesis and force re-acquisition.
        self.failed_verifications += 1
        if self.failed_verifications >= 2:
            self.failed_verifications = 0
            self.base_hypothesis = None

    def _active_hypothesis(self, tick: int) -> int | None:
        if self.base_hypothesis is None:
            return None
        if tick - self.last_contact_tick > CONTACT_MEMORY_TICKS:
            return None
        return self.base_hypothesis

    # -- movement --------------------------------------------------------

    def _search(self, obs: ObservationV2) -> AgentAction:
        return AgentAction(
            kind=ActionKindV2.MOVE,
            operand=self._clamp(max(1, obs.self_reach)),
        )

    def _move_toward(self, obs: ObservationV2, target: int) -> AgentAction:
        return AgentAction(
            kind=ActionKindV2.MOVE,
            operand=self._clamp(self._shortest_delta(target, obs.self_anchor)),
        )

    # -- geometry --------------------------------------------------------

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
    return SiegeRegionalAgent()
