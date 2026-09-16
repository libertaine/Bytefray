"""R3's experimental agent: ``v4_concentrated_attacker`` + a region sweep.

RESEARCH-ONLY. Not a starter, not a shipped example, not part of the
canonical V4 population. See ``tools/research/v5/agents/README.md``.

This agent is the single experimental object of V5 research Phase R3
(docs/research/v5/V5_R3_AGENT_COMPETENCE.md). It runs under the permanent
stable Ruleset ``bytefray-rules-4`` with no engine modification, no process
mortality, and no R2 objective oracle.

The behavioural delta versus the bundled ``v4_concentrated_attacker``
(reproduced verbatim in ``v5r3_point_control``) is exactly one thing:

    baseline:  when the target T is within reach, WRITE(T) -- every time,
               forever, so a thousand ticks of contact flip at most one cell.

    sweeper:   when the target T is within reach, WRITE(T + offset), where
               ``offset`` walks a deterministic expanding local sweep
               0, +1, -1, +2, -2, +3, -3, ... around T.

Everything else is preserved from the baseline: API version, process count,
process id, declared reach, quota share, target acquisition channel
(``visible_enemy_anchor_addresses[0]``), target-selection priority, target
lifetime (none -- the target is re-read from the observation on every single
action, exactly as the baseline does; this agent keeps no contact memory),
wrap-aware delta arithmetic, the approach MOVE formula, the no-contact drift
MOVE, the written signature byte, and RNG usage (neither uses ``context.rng``).

Legality, explicitly (Section F of the R3 report):

* Every action is one ordinary legal Agent API v2 action; the agent never
  gains extra actions. Each ``act()`` call still returns exactly one action,
  so its action budget is the ordinary Q=8 entrant quota.
* Ordinary reach is obeyed rather than bypassed: a sweep offset whose
  address is not within ``observation.self_reach`` of the current anchor is
  skipped, never written. The agent therefore also never wastes a quota slot
  on a write the engine would reject as out of reach.
* The agent reads only ``ObservationV2`` fields any bundled entrant reads.
  It never learns an enemy's ``core_base``, core cells, memory, ownership
  map, process list, or any engine state. ``own_core_base``/``own_core_size``
  describe *its own* core (the baseline's siblings ``v4_local_defender`` and
  ``v4_defender_scout`` both read them); this agent does not read them at all.
* The sweep is centred on a legally acquired contact address, not on any
  enemy core coordinate, and its shape is fixed before any target is known.

Why the sweep envelope is ``2 * reach`` and not 8: the agent writes only
while its anchor is within ``reach`` of T, and the engine applies a write
only when the address is within ``reach`` of the anchor. So no address
further than ``2 * reach`` from T can ever be legally written from a
qualifying anchor -- the envelope is derived from the engine's reach rule
alone. With the baseline's declared ``reach=4`` that is 17 candidate
addresses, which is larger than the 8-cell victory core by coincidence of
the baseline's own declaration, not by design: the pattern is a generic
region sweep around a contact and contains no knowledge of the core's size,
base, or existence (R3 charter Section 9).
"""

from battle_engine.agent_api import (
    ActionKindV2,
    AgentAction,
    MatchContextV2,
    ObservationV2,
    ProcessDeclaration,
)


class RegionSweeperAgent:
    def reset(self, context: MatchContextV2) -> None:
        self.context = context
        self.signature = 0xAA
        # The one piece of state the baseline does not have: a monotonically
        # advancing cursor into the sweep order. Deliberately not a target
        # memory -- it is never keyed to, reset by, or compared against any
        # target address, so the agent's target lifetime is still the
        # baseline's (re-read from the observation, every action).
        self.sweep_cursor = 0

    def declare_processes(self) -> list[ProcessDeclaration]:
        return [ProcessDeclaration(id="attacker", reach=4, share=1.0)]

    def act(self, observation: ObservationV2) -> AgentAction:
        if observation.visible_enemy_anchor_addresses:
            target = observation.visible_enemy_anchor_addresses[0]
            diff = target - observation.self_anchor
            half = self.context.arena_size // 2
            if diff > half:
                diff -= self.context.arena_size
            elif diff < -half:
                diff += self.context.arena_size

            if abs(diff) <= observation.self_reach:
                return AgentAction(
                    kind=ActionKindV2.WRITE,
                    operand=self._next_sweep_address(observation, target),
                    value=self.signature,
                )
            move_dist = min(abs(diff), observation.self_reach) * (
                1 if diff > 0 else -1
            )
            return AgentAction(kind=ActionKindV2.MOVE, operand=move_dist)

        return AgentAction(kind=ActionKindV2.MOVE, operand=observation.self_reach)

    def _sweep_offsets(self, reach: int) -> list[int]:
        """The deterministic expanding sweep order: 0, +1, -1, +2, -2, ...

        Bounded at ``2 * reach`` because the engine can never apply a write
        further than ``reach`` from the anchor, and this agent only writes
        while the anchor is within ``reach`` of the target.
        """

        envelope = 2 * max(0, reach)
        offsets = [0]
        for step in range(1, envelope + 1):
            offsets.append(step)
            offsets.append(-step)
        return offsets

    def _next_sweep_address(self, observation: ObservationV2, target: int) -> int:
        """Advance the sweep to the next address that is legally writable now.

        Offsets whose address lies outside ordinary reach are consumed and
        skipped rather than written, so the sweep never issues an action the
        engine would reject (which would silently cost a quota slot and make
        the paired comparison unfair to the sweeper). Offset 0 -- the exact
        address the baseline would have written -- is always within reach at
        this point, so the scan always terminates on a real address.
        """

        offsets = self._sweep_offsets(observation.self_reach)
        arena = self.context.arena_size
        for _ in range(len(offsets)):
            offset = offsets[self.sweep_cursor % len(offsets)]
            self.sweep_cursor += 1
            address = (target + offset) % arena
            if self._distance(address, observation.self_anchor) <= observation.self_reach:
                return address
        return target % arena

    def _distance(self, a: int, b: int) -> int:
        delta = abs((a - b) % self.context.arena_size)
        return min(delta, self.context.arena_size - delta)


def create_agent():
    return RegionSweeperAgent()
