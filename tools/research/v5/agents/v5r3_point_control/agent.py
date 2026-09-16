"""R3 point-control clone of the bundled ``v4_concentrated_attacker``.

RESEARCH-ONLY. Not a starter, not a shipped example, not part of the
canonical V4 population. See ``tools/research/v5/agents/README.md``.

This file exists for exactly one purpose: to prove that R3's paired
construction is clean. It reproduces ``v4_concentrated_attacker``'s decision
logic statement-for-statement, so that

    bundled v4_concentrated_attacker  vs  <opponent>
    v5r3_point_control                vs  <same opponent, same seed/slot>

produce identical gameplay. Any difference between the bundled baseline and
``v5r3_region_sweeper`` can then be attributed to the sweep itself rather
than to the research agent directory, the alternate loader path, or an
accidental transcription change (docs/research/v5/V5_R3_AGENT_COMPETENCE.md
Section G).

The only intentional differences from the bundled source are the class name
and this docstring. In particular ``declare_processes`` (one process,
``reach=4``, ``share=1.0``), the target channel
(``visible_enemy_anchor_addresses[0]``), the wrap-aware delta arithmetic,
the approach MOVE formula, the no-contact drift MOVE, and the written
signature byte ``0xAA`` are all copied verbatim.
"""

from battle_engine.agent_api import (
    ActionKindV2,
    AgentAction,
    MatchContextV2,
    ObservationV2,
    ProcessDeclaration,
)


class PointControlAgent:
    def reset(self, context: MatchContextV2) -> None:
        self.context = context
        self.signature = 0xAA

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
                    operand=target,
                    value=self.signature,
                )
            move_dist = min(abs(diff), observation.self_reach) * (
                1 if diff > 0 else -1
            )
            return AgentAction(kind=ActionKindV2.MOVE, operand=move_dist)

        return AgentAction(kind=ActionKindV2.MOVE, operand=observation.self_reach)


def create_agent():
    return PointControlAgent()
