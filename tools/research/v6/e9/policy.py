"""New research policies sharing a pinned, separately copied E8 executor."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from types import MappingProxyType, SimpleNamespace
from typing import Any

from battle_engine.agent_api import ActionKindV2, AgentAction, MatchContextV2, ObservationV2

from .selectors import Adaptive, Mode, Receipt, Schedule, Scheduled, diagnostic
from .tactics import Agent as Tactics


@dataclass(frozen=True)
class Variant:
    kind: str = "adaptive"
    mode: Mode = Mode.DENSE
    schedule: Schedule | None = None

    def __post_init__(self) -> None:
        if self.kind not in ("adaptive", "fixed", "disabled", "schedule"):
            raise ValueError("unknown E9 policy variant")
        if self.kind == "adaptive" and self.mode != Mode.DENSE:
            raise ValueError("adaptive starts DENSE")
        if (self.kind == "schedule") != (self.schedule is not None):
            raise ValueError("schedule configuration mismatch")
        if self.mode not in tuple(Mode):
            raise ValueError("invalid allocation")


@dataclass(frozen=True)
class Pending:
    process: str
    target: int
    tick: int


def receipt(pending: Pending | None, observation: ObservationV2) -> Receipt | None:
    if pending is None:
        return None
    if pending.process != observation.self_process_id or pending.tick != observation.previous_action_tick:
        raise ValueError("verification feedback does not belong to pending action")
    anchors = observation.previous_sense_anchors
    if not observation.previous_action_applied:
        if anchors is not None:
            raise ValueError("refused verification has a result")
        return None
    if anchors is None or tuple(sorted(set(anchors))) != anchors or any(not 0 <= a < 512 for a in anchors):
        raise ValueError("malformed applied verification result")
    return Receipt(pending.target, pending.tick, pending.target in anchors)


class Agent(Tactics):
    def __init__(self, variant: Variant | None = None) -> None:
        super().__init__()
        self.variant = variant if variant is not None else Variant()
        self._reset_selector()

    def _reset_selector(self) -> None:
        if self.variant.schedule is not None:
            self.selector: Any = Scheduled(self.variant.schedule)
        else:
            self.selector = Adaptive(disabled=self.variant.kind != "adaptive", mode=self.variant.mode)
        self.epoch = -1
        self.activation_epoch: int | None = None
        self.activation_tick: int | None = None
        self.verification: Pending | None = None
        self.receipts: list[Receipt] = []
        self._diagnostics: list[dict] = []

    def reset(self, context: MatchContextV2) -> None:
        if context.sensing_window != 27 or context.arena_size != 512:
            raise ValueError("E9 qualification policy requires the E8 active environment")
        mode = self.variant.schedule.initial if self.variant.schedule else self.variant.mode
        # A narrow reset view exposes exactly what the copied tactics use;
        # seed, identity metadata and arbitrary caller parameters are absent.
        view = SimpleNamespace(agent_id=context.agent_id, arena_size=context.arena_size,
            sensing_window=context.sensing_window, rng=context.rng,
            parameters=MappingProxyType({"acquire": "spatial-fast", "reacquire": "once" if mode == Mode.OFF
                else "repeat", "posture": "attack", "evade": "off", "processes": 1, "stress": False}))
        super().reset(view)  # type: ignore[arg-type]
        self._reset_selector()

    def act(self, obs: ObservationV2) -> AgentAction:
        if obs.self_process_id != "main":
            raise ValueError("unexpected focal process")
        if obs.current_tick != self.tick:
            if obs.current_tick < self.tick:
                raise ValueError("callbacks moved backwards")
            if not self.first_callback:
                self.previous_tick = self.tick
                self.previous_tick_callbacks = self.callback_index
            self.tick, self.callback_index, self.written = obs.current_tick, 0, set()
            self.epoch += 1
        self.callback_index += 1
        event = receipt(self.verification, obs)
        self.verification = None
        self._absorb(obs)
        self._observe(obs)
        if self.discovered and self.activation_epoch is None:
            self.activation_epoch, self.activation_tick = self.epoch, obs.current_tick
            if isinstance(self.selector, Adaptive):
                self.selector.activate()
        if event is not None:
            self.receipts.append(event)
        if self.callback_index == 1 and self.activation_epoch is not None:
            r = self.epoch - self.activation_epoch
            if isinstance(self.selector, Scheduled):
                assert self.activation_tick is not None
                decision = self.selector.boundary(r, obs.current_tick, obs.current_tick - self.activation_tick)
            else:
                decision = self.selector.boundary(r, obs.current_tick, tuple(self.receipts))
            self._diagnostics.append(diagnostic(decision))
            self.receipts.clear()
        action = self._choose(obs)
        pending = self.pending.get("main")
        if action.kind == ActionKindV2.SENSE and pending is not None and pending[0] == "verify":
            self.verification = Pending("main", pending[1], obs.current_tick)
        self.first_callback = False
        return action

    def _choose(self, obs: ObservationV2) -> AgentAction:
        if self.search_address is not None and self._reacquiring():
            action = self._search_step(obs)
            if action is not None:
                return action
        mode = self.selector.mode
        if (mode != Mode.OFF and self.callback_index == 1 and self.discovered and self.known
                and self.search_address is None):
            assert self.activation_epoch is not None
            if (self.epoch - self.activation_epoch) % int(mode) == 0:
                return self._sense(obs, "verify", self.known[0])
        return self._attack(obs, acquire=True)

    def diagnostics(self) -> list[dict]:
        return deepcopy(self._diagnostics)


def create_agent() -> Agent:
    return Agent()
