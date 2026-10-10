"""Ruleset scheduler primitives retained by the stable v4 process runtime.

The sequential helper preserves the original scheduler contract for direct
characterization, while stable Ruleset v4 dispatches through the chunked
quota helper. Both operate on generic live execution states and callbacks;
retired VM and Agent API v1 controllers are not runtime consumers.

It answers only: which execution state receives the next execution
opportunity, in what order, how many opportunities per tick, and when to
stop offering more because the state died. It has no opinion on what an
"execution opportunity" does -- that is entirely up to each runtime's
``execute_slot`` callback (currently an Agent API v2 process action). It does not know about scoring,
statistics, replay, termination, or which runtime it is scheduling.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Protocol, TypeVar


class _LivenessCheckable(Protocol):
    alive: bool


StateT = TypeVar("StateT", bound=_LivenessCheckable)


def run_sequential_quota(
    states: Iterable[StateT],
    quota: int,
    execute_slot: Callable[[StateT, int], None],
) -> None:
    """Give each live state in ``states``, in order, up to ``quota`` turns.

    For each state, in iteration order: skip it entirely if it is already
    not alive. Otherwise call ``execute_slot(state, slot)`` once per
    ``slot`` in ``range(quota)``, checking ``state.alive`` again before
    each call and stopping -- without calling ``execute_slot`` again --
    the moment it becomes false. A state that dies partway through its
    quota receives no further opportunities that tick; later states are
    unaffected and still receive their own full quota.
    """

    for state in states:
        if not state.alive:
            continue
        for slot in range(quota):
            if not state.alive:
                break
            execute_slot(state, slot)


def run_chunked_quota(
    states: Iterable[StateT],
    quota: int,
    execute_slot: Callable[[StateT, int], None],
    *,
    chunk_size: int = 1,
    rotate_start: bool = False,
    tick: int = 1,
    mirror_second_half: bool = False,
) -> None:
    """Give each live state in ``states`` up to ``quota`` turns in chunked round-robin order.

    - If ``chunk_size >= quota`` and ``not rotate_start``: equivalent to sequential block execution.
    - If ``chunk_size == 1`` and ``not rotate_start``: equivalent to single-action round-robin interleaving.
    - If ``1 < chunk_size < quota``: each live entrant executes ``min(chunk_size, remaining)`` actions per pass.
    - If ``rotate_start`` is True: for each tick, the entrant sequence is cyclically rotated by
      ``(tick - 1) % len(states)`` so each entrant takes turns being the first mover in the tick.
    - If ``mirror_second_half`` is True (V6 E4 mirrored pass order,
      docs/research/v6/V6_E4_ORDER_VS_EVALUATION_TIMING_DESIGN_REVIEW.md Sec J): with
      ``P = ceil(quota / chunk_size)`` passes, each pass ``p`` with ``2 * p >= P`` walks the
      (rotated) entrant sequence in reverse. The first mover, each entrant's own slot numbering
      (``0 .. quota - 1``, one chunk per pass, in order) and the liveness checks are unchanged;
      only which entrant goes first *within* the later passes changes. With a single pass it has
      no effect. ``False`` -- every Ruleset unless it states otherwise -- is the historical order.
    """

    state_list = list(states)
    n_states = len(state_list)
    if n_states == 0 or quota <= 0:

        return

    if rotate_start and n_states > 1:
        offset = (tick - 1) % n_states
        state_order = state_list[offset:] + state_list[:offset]
    else:
        state_order = state_list

    effective_chunk = max(1, chunk_size)
    num_passes = (quota + effective_chunk - 1) // effective_chunk
    for p in range(num_passes):
        start_slot = p * effective_chunk
        end_slot = min((p + 1) * effective_chunk, quota)
        pass_order = state_order[::-1] if mirror_second_half and 2 * p >= num_passes else state_order
        for state in pass_order:
            if not state.alive:
                continue
            for slot in range(start_slot, end_slot):
                if not state.alive:
                    break
                execute_slot(state, slot)


def run_interleaved_quota(
    states: Iterable[StateT],
    quota: int,
    execute_slot: Callable[[StateT, int], None],
) -> None:
    """Give each live state in ``states`` up to ``quota`` turns in round-robin interleaved order.

    For each slot in ``range(quota)``, each live entrant in ``states`` executes one action,
    skipping states that are not alive.
    """

    run_chunked_quota(states, quota, execute_slot, chunk_size=1)


__all__ = ["run_chunked_quota", "run_interleaved_quota", "run_sequential_quota"]
