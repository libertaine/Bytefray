"""Circular byte-addressed shared arena extracted from the v0.1 core.

V6 Phase 2B.12 retired VM/blob execution
(docs/research/v6/V6_PHASE2B12_SCOPE_C_RUNTIME_RETIREMENT.md), removing
this module's instruction-execution machinery (``load_code``, ``step``,
and the ``battle_engine.instructions`` opcode dependency they were the
module's only consumers of). ``VM`` itself is retained as the shared,
Ruleset-agnostic arena/ownership primitive
(``process_runtime.ProcessMatchController`` uses ``arena``, ``writer``,
``ownership_counts``, ``_wr8``, and ``clear_tick_diffs`` directly) --
nothing about the arena's addressing, ownership accounting, or tick-diff
recording is VM-specific; only *how bytes got written* (a VM program's own
opcode execution vs. an Agent API v2 process's declared actions) differed.
"""

from __future__ import annotations

# The historical "no-op" fill byte VM programs used to pad an empty arena.
# Retained as a plain literal (rather than importing it from the now-removed
# ``instructions`` module) purely so a freshly constructed arena's initial
# content is unchanged from before -- no code reads this as an opcode any
# longer.
_ARENA_FILL_BYTE = 0


class VM:
    def __init__(self, arena_size: int):
        self.arena = bytearray([_ARENA_FILL_BYTE] * arena_size)
        self.writer: list[str | None] = [None] * arena_size
        # Authoritative aggregate of ``writer``. Every ownership mutation,
        # including wrapped/overlapping initial loads and Python Agent API
        # writes, converges through ``_wr8`` and updates this map in O(1).
        self.ownership_counts: dict[str, int] = {}
        # (start_address, length, owner, values) -- ``values`` holds the
        # actual byte written at each address in the run, in order, so a
        # replay consumer can reconstruct arena content, not just ownership.
        self.tick_diffs: list[tuple[int, int, str | None, list[int]]] = []

    def clear_tick_diffs(self) -> None:
        self.tick_diffs.clear()

    def _rd32(self, pos: int) -> int:
        m = len(self.arena)
        p = pos % m
        return (
            self.arena[p]
            | (self.arena[(p + 1) % m] << 8)
            | (self.arena[(p + 2) % m] << 16)
            | (self.arena[(p + 3) % m] << 24)
        )

    def _wr8(self, pos: int, val: int, owner: str | None) -> None:
        m = len(self.arena)
        i = pos % m
        byte_value = val & 0xFF
        previous_owner = self.writer[i]
        if previous_owner != owner:
            if previous_owner is not None:
                previous_count = self.ownership_counts[previous_owner] - 1
                if previous_count:
                    self.ownership_counts[previous_owner] = previous_count
                else:
                    del self.ownership_counts[previous_owner]
            if owner is not None:
                self.ownership_counts[owner] = self.ownership_counts.get(owner, 0) + 1
        self.arena[i] = byte_value
        self.writer[i] = owner
        if (
            self.tick_diffs
            and self.tick_diffs[-1][0] + self.tick_diffs[-1][1] == i
            and self.tick_diffs[-1][2] == owner
        ):
            a, length, previous_owner, values = self.tick_diffs[-1]
            values.append(byte_value)
            self.tick_diffs[-1] = (a, length + 1, previous_owner, values)
        else:
            self.tick_diffs.append((i, 1, owner, [byte_value]))
