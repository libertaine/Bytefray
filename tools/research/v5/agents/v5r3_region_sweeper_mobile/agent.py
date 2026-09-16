"""R3 secondary variant: the region sweep, with repositioning.

RESEARCH-ONLY. Not a starter, not a shipped example, not part of the
canonical V4 population. See ``tools/research/v5/agents/README.md``.

``v5r3_region_sweeper`` changes address selection and nothing else, which
makes it the strictest possible paired comparison against the bundled
``v4_concentrated_attacker`` -- but it also inherits the baseline's movement
policy, which stops moving the instant the target is within reach. Its
coverage is therefore capped at the ``2 * reach + 1`` addresses that happen
to surround wherever the approach left the anchor, and whether that window
covers a whole 8-cell core is an accident of approach geometry rather than a
property of region sweeping.

This variant isolates that confound. It runs the identical sweep order, but
when the next sweep address is out of reach it MOVEs toward that address
instead of skipping it:

    sweeper:         skip the unreachable offset, write a reachable one.
    mobile sweeper:  spend this action moving toward the unreachable offset,
                     and write it on a later action.

The move uses the baseline's own formula --
``min(abs(delta), self_reach) * sign(delta)`` -- aimed at the sweep address
rather than at the target. This costs actions: every reposition consumes one
of the entrant's ordinary Q=8 slots and produces no write, so this agent has
strictly *fewer* writes available than either the baseline or the primary
sweeper. It gains no engine capability, no extra actions, no reach bypass,
and no privileged information; it is an ordinary legal Agent API v2 entrant
under stable ``bytefray-rules-4``.

Distinguishing "region sweeping converts contact into capture" from "region
sweeping plus the movement needed to realise it converts contact into
capture" is the entire reason this second agent exists. Its result is
reported separately from the primary sweeper's throughout
docs/research/v5/V5_R3_AGENT_COMPETENCE.md and is never merged into it.
"""

from battle_engine.agent_api import (
    ActionKindV2,
    AgentAction,
    MatchContextV2,
    ObservationV2,
    ProcessDeclaration,
)


class MobileRegionSweeperAgent:
    def reset(self, context: MatchContextV2) -> None:
        self.context = context
        self.signature = 0xAA
        self.sweep_cursor = 0

    def declare_processes(self) -> list[ProcessDeclaration]:
        return [ProcessDeclaration(id="attacker", reach=4, share=1.0)]

    def act(self, observation: ObservationV2) -> AgentAction:
        if observation.visible_enemy_anchor_addresses:
            target = observation.visible_enemy_anchor_addresses[0]
            diff = self._shortest_delta(target, observation.self_anchor)

            if abs(diff) <= observation.self_reach:
                offsets = self._sweep_offsets(observation.self_reach)
                offset = offsets[self.sweep_cursor % len(offsets)]
                address = (target + offset) % self.context.arena_size
                sweep_delta = self._shortest_delta(address, observation.self_anchor)
                if abs(sweep_delta) <= observation.self_reach:
                    self.sweep_cursor += 1
                    return AgentAction(
                        kind=ActionKindV2.WRITE,
                        operand=address,
                        value=self.signature,
                    )
                # Reposition toward the sweep address. The cursor is
                # deliberately NOT advanced: the same offset is retried once
                # the anchor can legally reach it, so no sweep address is
                # ever silently dropped.
                move_dist = min(abs(sweep_delta), observation.self_reach) * (
                    1 if sweep_delta > 0 else -1
                )
                return AgentAction(kind=ActionKindV2.MOVE, operand=move_dist)

            move_dist = min(abs(diff), observation.self_reach) * (
                1 if diff > 0 else -1
            )
            return AgentAction(kind=ActionKindV2.MOVE, operand=move_dist)

        return AgentAction(kind=ActionKindV2.MOVE, operand=observation.self_reach)

    def _sweep_offsets(self, reach: int) -> list[int]:
        envelope = 2 * max(0, reach)
        offsets = [0]
        for step in range(1, envelope + 1):
            offsets.append(step)
            offsets.append(-step)
        return offsets

    def _shortest_delta(self, target: int, anchor: int) -> int:
        diff = target - anchor
        half = self.context.arena_size // 2
        if diff > half:
            diff -= self.context.arena_size
        elif diff < -half:
            diff += self.context.arena_size
        return diff


def create_agent():
    return MobileRegionSweeperAgent()
