"""Declared product fixture. Constants are setup inputs, never Keeper knowledge."""

from battle_engine.agent_api import ActionKindV2, AgentAction, AgentV2, ProcessDeclaration


class EncroachingOpponent(AgentV2):
    def reset(self, context):
        self.callbacks = 0

    def declare_processes(self):
        return [ProcessDeclaration(id="main", reach=128, share=1.0)]

    def act(self, observation):
        self.callbacks += 1
        if self.callbacks == 1:
            return AgentAction(ActionKindV2.MOVE, operand=-64)
        if self.callbacks == 2:
            return AgentAction(ActionKindV2.WRITE, operand=1, value=0x45)
        return AgentAction(ActionKindV2.READ, operand=observation.own_core_base)


def create_agent():
    return EncroachingOpponent()
