"""Independent functional contract oracle; imports no production E9 logic.

Literal numbers are the approved specification's constants, intentionally
not imported from the implementation being checked. No payoff computation.
"""

from __future__ import annotations

from typing import NamedTuple


class Expected(NamedTuple):
    mode: int = 1
    c: int = 0
    target: int | None = None
    request: bool = False
    changes: int = 0
    last_revision: int = 0


def advance(state: Expected, epoch: int, tick: int,
            observations: tuple[tuple[int, int, bool], ...], *, disabled: bool = False) -> Expected:
    """Each observation is (issued_tick, target, target_present)."""
    mode, run, contact, demand, count, last = state
    for issue, address, found in observations:
        if issue > tick:
            raise ValueError("future snapshot")
        if issue < tick - 1:
            continue
        if found and not demand:
            run = min(2, run + 1) if contact == address else 1
            contact = address
        if not found:
            run, contact, demand = 0, None, True
    if demand and mode == 1:
        demand, run, contact = False, 0, None
    destination = {True: 1, False: mode}[mode == 4 and demand]
    if mode == 1 and run == 2:
        destination = 4
    permitted = not disabled and count < 4 and epoch >= last + 2
    if permitted and destination != mode:
        return Expected(destination, 0, None, False, count + 1, epoch)
    return Expected(mode, run, contact, demand, count, last)


def schedule_command(initial: int, edges: tuple[int, ...], moment: int,
                     epoch: int, state: Expected) -> Expected:
    intended = initial if len([v for v in edges if v <= moment]) % 2 == 0 else 5 - initial
    if state.mode == intended or epoch < state.last_revision + 2 or state.changes >= 4:
        return state
    return Expected(intended, 0, None, False, state.changes + 1, epoch)


def canonical_identities() -> set[tuple[str, int, tuple[int, ...]]]:
    """Enumerate boundary shapes independently of the production grid loop."""
    result: set[tuple[str, int, tuple[int, ...]]] = {("constant", 1, ()), ("constant", 4, ())}
    for initial in (1, 4):
        for start in (2, 4, 8, 16, 32, 64, 128, 256, 512):
            for dwell_after in (2, 3, 4, 8):
                for dwell_back in (2, 3, 4, 8):
                    edges = (start, start + dwell_after, start + dwell_after + dwell_back,
                             start + 2 * dwell_after + dwell_back)
                    for length in (1, 2, 3, 4):
                        for clock in ("wall", "opportunity"):
                            result.add((clock, initial, edges[:length]))
    return result
