"""Bytefray V6 teaching fixture opponent -- Stationary Core Reader.

Stays at its anchor and legally READs its own core at every callback.
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


class StationaryOpponentAgent(AgentV2):
    """Stationary opponent that remains at its anchor by reading its own core."""

    def __init__(self) -> None:
        self.arena: int = 512

    def reset(self, context: MatchContextV2) -> None:
        self.arena = context.arena_size

    def declare_processes(self) -> list[ProcessDeclaration]:
        return [
            ProcessDeclaration(
                id="main",
                reach=128,
                share=1.0,
            )
        ]

    def act(self, observation: ObservationV2) -> AgentAction:
        return AgentAction(ActionKindV2.READ, operand=observation.own_core_base)


def create_agent() -> StationaryOpponentAgent:
    return StationaryOpponentAgent()
