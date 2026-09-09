"""R4 archetype E -- territory / exploration strategy (RESEARCH ONLY).

Not a starter, not a shipped example, not a member of the canonical V4
population. See ``tools/research/v5/agents/README.md``.

Strategic identity: play the *other* victory route on purpose. Stable V4
resolves a tick-limit match by comparing territory among living entrants
(Phase 0 Section 4), and Phase 0 observed that no bundled agent ever
strategically converted territory into anything. This archetype exists to
test whether a non-rush, space-controlling strategy can still express the
game's primary objective when contact eventually happens -- the question
R4 charter Section 6E poses.

Behaviour in two modes:

* **Expand** (default) -- claim ground. It writes a contiguous block of
  cells around its anchor, then strides on and claims the next block, so
  its owned territory grows as a broad swathe rather than the single
  wandering trail the bundled ``v4_claimer`` leaves behind (``v4_claimer``
  alternates one MOVE and one WRITE at its own anchor with reach 1).
* **Press** (on contact) -- for a bounded number of ticks it abandons
  expansion and sweeps a region around the contact address, then returns to
  expanding whether or not the press succeeded.

The bounded press is the deliberate archetype weakness: this agent will
walk away from a siege it is winning because holding ground is what it is
built to do. It has a real, legal conversion path from contact to core
damage, but a strictly worse one than the dedicated attackers -- it forms
no core hypothesis, gathers no ownership evidence, and does not persist.

Legal-information sources (Agent API v2 only): the ordinary
``visible_enemy_anchor_addresses`` sensor channel; its OWN
``own_core_base``/``own_core_size``; ``self_anchor``; ``self_reach``;
``current_tick``; ``context.arena_size``. No READs, no enemy core
coordinate, no oracle, no privileged engine state, no hard-coded opponent
start address.
"""

from battle_engine.agent_api import (
    ActionKindV2,
    AgentAction,
    MatchContextV2,
    ObservationV2,
    ProcessDeclaration,
)

# Ticks of sustained pressure after a contact before returning to expansion.
PRESS_TICKS = 60

# Cells claimed at each stop before striding on to the next block.
CLAIM_BLOCK = 9


class TerritoryExpanderAgent:
    """Broad territorial claimer with a bounded conversion mode."""

    def reset(self, context: MatchContextV2) -> None:
        self.context = context
        self.arena = context.arena_size
        self.signature = 0xE7

        self.claim_index = 0
        self.press_until = -1
        self.press_target: int | None = None
        self.press_cursor = 0

    def declare_processes(self) -> list[ProcessDeclaration]:
        return [ProcessDeclaration(id="expander", reach=self._reach(16), share=1.0)]

    def act(self, observation: ObservationV2) -> AgentAction:
        self._observe(observation)

        if (
            self.press_target is not None
            and observation.current_tick <= self.press_until
        ):
            action = self._press(observation)
            if action is not None:
                return action

        return self._expand(observation)

    # -- modes -----------------------------------------------------------

    def _press(self, obs: ObservationV2) -> AgentAction | None:
        target = self.press_target
        if target is None:
            return None
        if not self._within_reach(obs, target):
            return self._move_toward(obs, target)

        core_size = max(1, obs.own_core_size)
        span = 2 * core_size
        index = self.press_cursor % span
        self.press_cursor += 1
        address = (target + index - core_size) % self.arena
        if not self._within_reach(obs, address):
            return self._move_toward(obs, target)
        return AgentAction(
            kind=ActionKindV2.WRITE, operand=address, value=self.signature
        )

    def _expand(self, obs: ObservationV2) -> AgentAction:
        """Claim a contiguous block, then stride to the next one."""

        position = self.claim_index % (CLAIM_BLOCK + 1)
        self.claim_index += 1
        if position == CLAIM_BLOCK:
            return AgentAction(
                kind=ActionKindV2.MOVE,
                operand=self._clamp(max(1, obs.self_reach) * 2),
            )
        offset = position - CLAIM_BLOCK // 2
        address = (obs.self_anchor + offset) % self.arena
        if not self._within_reach(obs, address):
            address = obs.self_anchor % self.arena
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
        if self.press_target != nearest or obs.current_tick > self.press_until:
            self.press_cursor = 0
        self.press_target = nearest
        self.press_until = obs.current_tick + PRESS_TICKS

    # -- geometry --------------------------------------------------------

    def _move_toward(self, obs: ObservationV2, target: int) -> AgentAction:
        return AgentAction(
            kind=ActionKindV2.MOVE,
            operand=self._clamp(self._shortest_delta(target, obs.self_anchor)),
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
    return TerritoryExpanderAgent()
