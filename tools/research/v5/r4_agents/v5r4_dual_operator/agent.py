"""R4 archetype D -- balanced generalist (RESEARCH ONLY).

Not a starter, not a shipped example, not a member of the canonical V4
population. See ``tools/research/v5/agents/README.md``.

Strategic identity: do several things adequately and none of them
exceptionally. Two declared processes split the Q=8 entrant quota evenly:

* ``raider`` (reach 32) -- moves toward remembered contacts and applies a
  region sweep around the contact address itself. Note what it does *not*
  do: unlike archetype A it forms no core-base hypothesis, and unlike
  archetype B it gathers no READ ownership evidence. It attacks where the
  enemy *is*, widened to a region. That is a real conversion path and a
  deliberately weaker one.
* ``keeper`` (reach 12) -- blind-repairs its own core by rewriting each of
  its own cells in rotation. It spends no actions on READ inspection, so it
  is cheaper and less informed than archetype C's warden: it cannot tell a
  cell it still owns from one it has lost, and simply refreshes all of them.

The result is an entrant with genuine movement, genuine contact handling,
genuine regional offence and genuine defence, at roughly half the intensity
of the specialists in each dimension -- and with only four actions per tick
available to each half.

Legal-information sources (Agent API v2 only): ``self_process_id`` for role
dispatch; the ordinary ``visible_enemy_anchor_addresses`` sensor channel;
its OWN ``own_core_base``/``own_core_size``; ``self_anchor``;
``self_reach``; ``context.arena_size``. It performs no READs, so it never
consults ``previous_read_owner``. No enemy core coordinate, no oracle, no
privileged engine state, no hard-coded opponent start address.

Because Bytefray v4 selects among an entrant's own processes round-robin
with a match-scoped cursor, the two roles interleave across ticks rather
than executing in a fixed within-tick order; both roles are written to be
correct regardless of which of them is called first.
"""

from battle_engine.agent_api import (
    ActionKindV2,
    AgentAction,
    MatchContextV2,
    ObservationV2,
    ProcessDeclaration,
)

# Contact memory for the raider. Shorter than archetype A's, so this agent
# gives up on a stale target sooner and returns to searching.
CONTACT_MEMORY_TICKS = 120


class DualOperatorAgent:
    """Two roles sharing one quota: a regional raider and a blind keeper."""

    def reset(self, context: MatchContextV2) -> None:
        self.context = context
        self.arena = context.arena_size

        self.last_contact: int | None = None
        self.last_contact_tick = -1
        self.raid_cursor = 0
        self.keep_cursor = 0

    def declare_processes(self) -> list[ProcessDeclaration]:
        return [
            ProcessDeclaration(id="raider", reach=self._reach(32), share=0.5),
            ProcessDeclaration(id="keeper", reach=self._reach(12), share=0.5),
        ]

    def act(self, observation: ObservationV2) -> AgentAction:
        self._observe(observation)
        if observation.self_process_id == "keeper":
            return self._act_keeper(observation)
        return self._act_raider(observation)

    # -- roles -----------------------------------------------------------

    def _act_raider(self, obs: ObservationV2) -> AgentAction:
        target = self._active_contact(obs.current_tick)
        if target is None:
            return AgentAction(
                kind=ActionKindV2.MOVE, operand=self._clamp(max(1, obs.self_reach))
            )

        core_size = max(1, obs.own_core_size)
        if not self._within_reach(obs, target):
            return self._move_toward(obs, target)

        # A region sweep centred on the contact: a window two core-widths
        # wide, so the enemy core is covered whichever side of the contact
        # address it lies on. No knowledge of where the core actually is.
        span = 2 * core_size
        index = self.raid_cursor % span
        self.raid_cursor += 1
        offset = index - core_size
        address = (target + offset) % self.arena
        if not self._within_reach(obs, address):
            return self._move_toward(obs, target)
        return AgentAction(kind=ActionKindV2.WRITE, operand=address, value=0xD0)

    def _act_keeper(self, obs: ObservationV2) -> AgentAction:
        core_size = max(1, obs.own_core_size)
        base = obs.own_core_base % self.arena
        station = (base + core_size // 2) % self.arena

        if not self._region_in_reach(obs, base, core_size):
            return self._move_toward(obs, station)

        # Disrupt an enemy standing inside the defended region first.
        for address in sorted(set(obs.visible_enemy_anchor_addresses)):
            if self._within_reach(obs, address):
                return AgentAction(
                    kind=ActionKindV2.WRITE, operand=address, value=0xD1
                )

        offset = self.keep_cursor % core_size
        self.keep_cursor += 1
        address = (base + offset) % self.arena
        return AgentAction(kind=ActionKindV2.WRITE, operand=address, value=0xD1)

    # -- observation -----------------------------------------------------

    def _observe(self, obs: ObservationV2) -> None:
        visible = sorted(set(obs.visible_enemy_anchor_addresses))
        if not visible:
            return
        self.last_contact = min(
            visible, key=lambda a: (self._distance(a, obs.self_anchor), a)
        )
        self.last_contact_tick = obs.current_tick

    def _active_contact(self, tick: int) -> int | None:
        if self.last_contact is None:
            return None
        if tick - self.last_contact_tick > CONTACT_MEMORY_TICKS:
            return None
        return self.last_contact

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
    return DualOperatorAgent()
