"""Qualification-only observations and real-engine scripted histories."""

from __future__ import annotations

import json
import random
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import pytest
from _e8_family_engine_harness import T8, Plan, play, sigma_of
from battle_engine import process_runtime
from battle_engine.agent_api import ActionKindV2, MatchContextV2, ObservationV2

from tools.research.v6.e9.packages import package
from tools.research.v6.e9.policy import Agent, Variant


def context(seat: str = "A") -> MatchContextV2:
    return MatchContextV2(seat, 0, 512, 1000, random.Random(0), sensing_window=27)


def make(variant: Variant | None = None, seat: str = "A") -> Agent:
    agent = Agent(variant)
    agent.reset(context(seat))
    return agent


def observation(tick: int, *, previous_tick: int = 0, anchors: tuple[int, ...] | None = None,
                applied: bool = True, value: int | None = None, owner: str | None = None) -> ObservationV2:
    return ObservationV2(tick, previous_tick, previous_tick, "main", 100, 256, 100, 8,
                         (), applied, value, owner, anchors)


def start(agent: Agent, target: int = 191) -> None:
    first = agent.act(observation(1))
    assert first.kind == ActionKindV2.SENSE
    assert agent.pending["main"][0] == "discover"
    agent.act(observation(1, previous_tick=1, anchors=(target,)))
    assert agent.discovered and agent.activation_epoch == 0


@dataclass
class Capture:
    obs: ObservationV2
    action: Any
    index: int
    search_before: tuple
    search_after: tuple
    mode: int
    purpose: str | None
    known: tuple[int, ...]


def engine_history(tmp_path: Path, seat: str, configuration: str, plan: Plan,
                   *, ticks: int = 24, distance: int = 91) -> tuple[Any, Agent, list[Capture]]:
    fixture = package(tmp_path / "fixtures", "e9_focal", configuration)
    captured: list[Capture] = []
    focal: list[Agent] = []
    original = process_runtime.load_python_agent

    def load(spec: Any) -> Any:
        loaded = original(spec)
        instance = loaded.instance
        if isinstance(instance, Agent):
            focal.append(instance)
            act = instance.act

            def logged(obs: ObservationV2) -> Any:
                before = (instance.search_address, tuple(instance.search_centers), instance.search_next)
                action = act(obs)
                pending = instance.pending.get("main")
                captured.append(Capture(obs, action, instance.callback_index, before,
                    (instance.search_address, tuple(instance.search_centers), instance.search_next),
                    int(instance.selector.mode), pending[0] if pending else None, tuple(instance.known)))
                return action

            instance.act = logged
        return loaded

    own = 100
    enemy = (own + sigma_of(7, seat) * distance) % 512
    starts = (own, enemy) if seat == "A" else (enemy, own)
    entrants = (fixture, plan) if seat == "A" else (plan, fixture)
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(process_runtime, "load_python_agent", load)
        played = play(tmp_path / "legal", T8, *entrants, starts=starts, seed=7, ticks=ticks)
    assert len(focal) == 1 and captured
    decisions = played.decisions(seat)
    assert len(decisions) == len(captured)
    assert {d["applied_result"]["status"] for d in decisions} == {"APPLIED"}
    assert '"forfeit"' not in played.replay
    # This diagnostic artifact contains no outcome or comparative payoff.
    (tmp_path / "qualification.json").write_text(json.dumps({
        "scope": "scripted capability qualification", "seat": seat,
        "ruleset": T8, "requested_ticks": ticks,
        "diagnostics": focal[0].diagnostics(),
        "callbacks": [asdict(c) for c in captured],
    }, default=lambda value: value.value, indent=2) + "\n", encoding="utf-8")
    return played, focal[0], captured
