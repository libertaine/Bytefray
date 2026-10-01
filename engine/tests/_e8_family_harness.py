"""Shared helpers for the V6 E8 family tests (phase I8-3).

The policy object is driven with constructed ``ObservationV2`` sequences
(``make``, ``obs``), as E6's family tests were. Nothing here plays a match;
the engine-level tests live in ``test_v6_e8_family_engine.py``.
"""

from __future__ import annotations

import importlib.util
import random
from collections.abc import Mapping
from types import MappingProxyType, ModuleType
from typing import Any

from battle_engine.agent_api import ActionKindV2, AgentAction, MatchContextV2, ObservationV2

from tools.research.v6.e8.family import FIXTURE_DIR, MEMBERS, resolved_parameters

ARENA = 512
BASE = 100
BEACON = 0xCE
WINDOW = 27
PASSIVE, ACTIVE = "passive", "active"
MODES = (PASSIVE, ACTIVE)


def load_policy(pid: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(f"e8_family_policy_{pid}", FIXTURE_DIR / pid / "agent.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


POLICY = load_policy("e8_q01")


def make(member: str | None = None, *, mode: str = PASSIVE, seat: str = "A", rng_seed: int = 0,
         module: ModuleType = POLICY, parameters: Mapping[str, Any] | None = None,
         rng: random.Random | None = None) -> Any:
    """A reset family agent: ``member``'s parameters (or ``parameters``) under ``mode``."""

    agent = module.create_agent()
    values = dict(parameters if parameters is not None else MEMBERS[member or "GREED8"])
    agent.reset(MatchContextV2(agent_id=seat, seed=0, arena_size=ARENA, tick_limit=1000,
                               rng=rng if rng is not None else random.Random(rng_seed),
                               parameters=MappingProxyType(values), detection_radius=32,
                               sensing_window=WINDOW if mode == ACTIVE else None))
    return agent


def with_params(member: str, **changes: Any) -> dict[str, Any]:
    """``member``'s parameters with ``changes``: a synthetic setting, never a family member."""

    return {**MEMBERS[member], **changes}


def obs(tick: int, *, pid: str = "main", anchor: int = BASE, visible: tuple[int, ...] = (), applied: bool = True,
        value: int | None = None, owner: str | None = None,
        sensed: tuple[int, ...] | None = None) -> ObservationV2:
    return ObservationV2(current_tick=tick, last_callback_tick=0, previous_action_tick=0, self_process_id=pid,
                         self_anchor=anchor, self_reach=ARENA // 2, own_core_base=BASE, own_core_size=8,
                         visible_enemy_anchor_addresses=visible, previous_action_applied=applied,
                         previous_read_value=value, previous_read_owner=owner, previous_sense_anchors=sensed)


def hit(tick: int, **kwargs: Any) -> ObservationV2:
    """The previous READ returned an intact enemy core beacon."""
    return obs(tick, value=BEACON, owner="B", **kwargs)


def miss(tick: int, **kwargs: Any) -> ObservationV2:
    return obs(tick, value=0, owner=None, **kwargs)


def own_write(owner: str, tick: int, **kwargs: Any) -> ObservationV2:
    """The previous READ returned a cell holding ``owner``'s own write."""
    return obs(tick, value=1, owner=owner, **kwargs)


def move(delta: int) -> AgentAction:
    return AgentAction(ActionKindV2.MOVE, operand=delta)


def read(address: int) -> AgentAction:
    return AgentAction(ActionKindV2.READ, operand=address % ARENA)


def write(address: int, value: int = 1) -> AgentAction:
    return AgentAction(ActionKindV2.WRITE, operand=address % ARENA, value=value)


def sense(target: int) -> AgentAction:
    return AgentAction(ActionKindV2.SENSE, operand=target % ARENA)


def center(k: int, sigma: int, base: int = BASE) -> int:
    """The registered discovery center c_k = (own_core_base + sigma * (91 + 55k)) mod 512."""
    return (base + sigma * (91 + 55 * k)) % ARENA


def dist(a: int, b: int) -> int:
    d = (a - b) % ARENA
    return min(d, ARENA - d)


def reset_draws(rng_seed: int) -> tuple[int, int]:
    """The two reset draws, in their fixed order (P8-1): sigma, then the paint side."""
    rng = random.Random(rng_seed)
    return (-1, 1)[rng.randrange(2)], rng.randrange(2)


def seed_with(*, sigma: int | None = None, side: int | None = None, tau: int | None = None,
              evasions: tuple[tuple[int, int], ...] | None = None) -> int:
    """The first rng seed whose draws have the requested values.

    ``tau`` is the first play draw after reset (a search start); ``evasions``
    the first (sign, magnitude) play draws.
    """

    for candidate in range(100_000):
        rng = random.Random(candidate)
        s, p = (-1, 1)[rng.randrange(2)], rng.randrange(2)
        if sigma not in (None, s) or side not in (None, p):
            continue
        if tau is not None and (-1, 1)[rng.randrange(2)] != tau:
            continue
        if evasions is not None:
            got = tuple(((-1, 1)[rng.randrange(2)], rng.randint(8, 64)) for _ in evasions)
            if got != evasions:
                continue
        return candidate
    raise AssertionError("no such seed")


def paint_sequence(side: int, count: int, base: int = BASE) -> list[int]:
    cells = []
    for k in range(count):
        pair, second = divmod(k, 2)
        up, down = base + 8 + pair, base - 1 - pair
        cells.append((up if (side == 0) != bool(second) else down) % ARENA)
    return cells


def frozen(pid: str) -> dict[str, Any]:
    return resolved_parameters(pid)
