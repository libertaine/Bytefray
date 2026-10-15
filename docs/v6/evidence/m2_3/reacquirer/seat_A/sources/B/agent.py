"""Declared product fixture. Constants are setup inputs, never Reacquirer knowledge."""

from battle_engine.agent_api import ActionKindV2, AgentAction, AgentV2, ProcessDeclaration


class RelocatingOpponent(AgentV2):
    def reset(self, context):
        self.callbacks = 0

    def declare_processes(self):
        return [ProcessDeclaration(id="main", reach=128, share=1.0)]

    def act(self, observation):
        # Relocation depends only on this fixture's own eligible callback count.
        self.callbacks += 1
        if self.callbacks == 4:
            return AgentAction(ActionKindV2.MOVE, operand=64)
        return AgentAction(ActionKindV2.READ, operand=observation.own_core_base)


def create_agent():
    return RelocatingOpponent()
