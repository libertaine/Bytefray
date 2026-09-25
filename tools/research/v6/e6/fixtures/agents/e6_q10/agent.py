"""V6 E6 matched family: the one policy source every package shares.

A transcription of docs/research/v6/V6_E6_PRICED_SENSING_IMPLEMENTATION_PLAN.md
Sec 5.2 (the design is docs/research/v6/V6_PRICED_SENSING_DESIGN_REVIEW.md
Sec I). Every package's ``agent.py`` is this file, byte for byte; a package is
nothing but its manifest's parameter defaults, delivered on
``context.parameters``:

* ``search``: ``none``, ``fast``, ``paced`` or ``read``;
* ``posture``: ``attack``, ``guard`` or ``paint``;
* ``evade``: whether the first callback MOVEs the anchor off the core;
* ``processes``: 1, or 2 for a sensor (share 1/4) and a striker (3/4);
* ``adaptive``: the fixed ADAPT transition table, overriding the rest.

One instance serves every process of its entrant, so knowledge is
entrant-wide. Randomness comes only from ``context.rng``, drawn at reset in a
fixed order by every package: the search direction, the paint side, the
evade sign, the evade magnitude. There is no other state and no clock.

Research-only; never a product starter agent.
"""

from __future__ import annotations

from battle_engine.agent_api import (
    ActionKindV2,
    AgentAction,
    MatchContextV2,
    ObservationV2,
    ProcessDeclaration,
)

CORE_BEACON = 0xCE  # a core cell's value; the value a repair writes
MARK = 0x01  # the value of every other write: disruption, core attack, paint
CORE_SIZE = 8
MAX_STRIDE = 64  # the largest MOVE
PROBE_STRIDE = 8  # one probe per core-sized window
PROBE_SPAN = 64  # verification reads [a - 64, a + 64] around a last-known anchor
MIN_CORE_SEPARATION = 64
READ_ARC = 49  # read search: own_core_base + dir * (64 + 8m), m = 0..48
EVADE_MIN, EVADE_MAX = 8, 64
ADAPT_HOLD_TICKS = 8
ADAPT_SWITCH_TICK = 16
SENSOR_SHARE, STRIKER_SHARE = 0.25, 0.75


class Agent:
    def __init__(self) -> None:
        self.arena = 0
        self.me = ""
        self.search = "none"
        self.posture = "paint"
        self.evade = False
        self.processes = 1
        self.adaptive = False
        self.direction = 1
        self.paint_side = 0
        self.evade_sign = 1
        self.evade_magnitude = EVADE_MIN
        self._forget()

    def _forget(self) -> None:
        # Knowledge (entrant-wide).
        self.last_known: tuple[int, int] | None = None  # (anchor address, tick seen)
        self.enemy_core: int | None = None
        self.info_event = False
        # Per-tick bookkeeping.
        self.tick = -1
        self.callback_index = 0
        self.written: set[int] = set()
        self.first_callback = True
        # Core verification: a READ window around the last-known anchor, then
        # a downward scan from the first hit.
        self.window: list[int] = []
        self.window_center: int | None = None
        self.scan_top: int | None = None
        self.scan_last_hit: int | None = None
        # The READ each process is waiting to see the result of.
        self.pending: dict[str, tuple[str, int]] = {}
        # Cursors.
        self.read_m = 0
        self.paint_k = 0
        self.guard_cursor = 0
        self.evaded = False
        # ADAPT.
        self.mode = "paint"
        self.last_visible_tick: int | None = None
        self.last_damage_tick: int | None = None
        self.pending_evade = False

    # ------------------------------------------------------------------ API

    def reset(self, context: MatchContextV2) -> None:
        self.arena = context.arena_size
        self.me = context.agent_id
        parameters = context.parameters
        self.search = str(parameters.get("search", "none"))
        self.posture = str(parameters.get("posture", "paint"))
        self.evade = bool(parameters.get("evade", False))
        self.processes = int(parameters.get("processes", 1))
        self.adaptive = bool(parameters.get("adaptive", False))
        rng = context.rng
        self.direction = (-1, 1)[rng.randrange(2)]
        self.paint_side = rng.randrange(2)
        self.evade_sign = (-1, 1)[rng.randrange(2)]
        self.evade_magnitude = rng.randint(EVADE_MIN, EVADE_MAX)
        self._forget()

    def declare_processes(self) -> list[ProcessDeclaration]:
        reach = self.arena // 2
        if self.processes == 2:
            return [
                ProcessDeclaration(id="sensor", reach=reach, share=SENSOR_SHARE),
                ProcessDeclaration(id="striker", reach=reach, share=STRIKER_SHARE),
            ]
        return [ProcessDeclaration(id="main", reach=reach, share=1.0)]

    def act(self, obs: ObservationV2) -> AgentAction:
        if obs.current_tick != self.tick:
            self.tick = obs.current_tick
            self.callback_index = 0
            self.written = set()
        self.callback_index += 1
        self._absorb(obs)
        self._observe(obs)
        action = self._choose(obs)
        self.first_callback = False
        return action

    # ------------------------------------------------------------ knowledge

    def _distance(self, a: int, b: int) -> int:
        d = (a - b) % self.arena
        return min(d, self.arena - d)

    def _is_enemy_core_cell(self, obs: ObservationV2) -> bool:
        return (
            obs.previous_action_applied
            and obs.previous_read_value == CORE_BEACON
            and obs.previous_read_owner is not None
            and obs.previous_read_owner != self.me
        )

    def _absorb(self, obs: ObservationV2) -> None:
        """Take in the result of this process's previous READ, if it was one."""

        waiting = self.pending.pop(obs.self_process_id, None)
        if waiting is None:
            return
        kind, address = waiting
        if kind == "check":
            if obs.previous_read_owner != self.me:
                self.last_damage_tick = obs.current_tick
                if not self.evaded:
                    self.pending_evade = True
            return
        hit = self._is_enemy_core_cell(obs)
        if hit:
            self.info_event = True
        if self.enemy_core is not None:
            return
        if kind in ("verify", "probe"):
            if hit:
                self.scan_top = address
                self.scan_last_hit = address
        elif kind == "scan":
            assert self.scan_top is not None and self.scan_last_hit is not None
            if hit and (self.scan_top - address) % self.arena < CORE_SIZE - 1:
                self.scan_last_hit = address
            else:
                self.enemy_core = address if hit else self.scan_last_hit
                self.scan_top = None
                self.scan_last_hit = None

    def _observe(self, obs: ObservationV2) -> None:
        visible = obs.visible_enemy_anchor_addresses
        if visible:
            self.last_known = (visible[0], obs.current_tick)
            self.info_event = True
            self.last_visible_tick = obs.current_tick
        # Unverified adoption (the E2-E5 fixture convention): only at the
        # entrant's first callback, only for a single visible address that
        # cannot lie in its own core's exclusion zone.
        if (
            self.first_callback
            and self.enemy_core is None
            and len(visible) == 1
            and self._distance(visible[0], obs.own_core_base) >= MIN_CORE_SEPARATION
        ):
            self.enemy_core = visible[0]

    def _search_needed(self, obs: ObservationV2) -> bool:
        return (
            not obs.visible_enemy_anchor_addresses
            and self.last_known is None
            and self.enemy_core is None
            and self.scan_top is None
        )

    # -------------------------------------------------------------- actions

    def _write(self, address: int, value: int = MARK) -> AgentAction:
        address %= self.arena
        self.written.add(address)
        return AgentAction(ActionKindV2.WRITE, operand=address, value=value)

    def _read(self, obs: ObservationV2, kind: str, address: int) -> AgentAction:
        address %= self.arena
        self.pending[obs.self_process_id] = (kind, address)
        return AgentAction(ActionKindV2.READ, operand=address)

    def _move(self, delta: int) -> AgentAction:
        return AgentAction(ActionKindV2.MOVE, operand=delta)

    def _unwritten_anchor(self, obs: ObservationV2) -> int | None:
        for address in obs.visible_enemy_anchor_addresses:
            if address not in self.written:
                return address
        return None

    def _idle(self, obs: ObservationV2) -> AgentAction:
        """Paint outward from the own core, alternating sides."""

        pair, second = divmod(self.paint_k % (2 * (self.arena // 2 - CORE_SIZE // 2)), 2)
        self.paint_k += 1
        up = obs.own_core_base + CORE_SIZE + pair
        down = obs.own_core_base - 1 - pair
        first_up = self.paint_side == 0
        return self._write(up if first_up != bool(second) else down)

    def _search(self, obs: ObservationV2, search: str) -> AgentAction:
        if search == "fast":
            return self._move(MAX_STRIDE * self.direction)
        if search == "paced":
            if self.callback_index % 2 == 1:
                return self._move(MAX_STRIDE * self.direction)
            return self._idle(obs)
        if search == "read":
            m = self.read_m
            self.read_m = (m + 1) % READ_ARC
            return self._read(obs, "probe", obs.own_core_base + self.direction * (MIN_CORE_SEPARATION + PROBE_STRIDE * m))
        return self._idle(obs)

    def _verification_read(self, obs: ObservationV2) -> AgentAction | None:
        if self.scan_last_hit is not None:
            return self._read(obs, "scan", self.scan_last_hit - 1)
        if self.last_known is None:
            return None
        center = self.last_known[0]
        if center != self.window_center:
            self.window_center = center
            self.window = [center]
            for step in range(PROBE_STRIDE, PROBE_SPAN + 1, PROBE_STRIDE):
                self.window += [center - step, center + step]
        if not self.window:
            # The window held no enemy core cell: forget the anchor.
            self.last_known = None
            self.window_center = None
            return None
        return self._read(obs, "verify", self.window.pop(0))

    def _attack(self, obs: ObservationV2, search: str) -> AgentAction:
        anchor = self._unwritten_anchor(obs)
        if anchor is not None:
            return self._write(anchor)
        if self.enemy_core is not None:
            for i in range(CORE_SIZE):
                cell = (self.enemy_core + i) % self.arena
                if cell not in self.written:
                    return self._write(cell)
        else:
            verification = self._verification_read(obs)
            if verification is not None:
                return verification
        if search != "none" and self._search_needed(obs):
            return self._search(obs, search)
        return self._idle(obs)

    def _guard(self, obs: ObservationV2) -> AgentAction:
        anchor = self._unwritten_anchor(obs)
        if anchor is not None:
            return self._write(anchor)
        cell = obs.own_core_base + self.guard_cursor
        self.guard_cursor = (self.guard_cursor + 1) % CORE_SIZE
        return self._write(cell, CORE_BEACON)

    def _sensor(self, obs: ObservationV2) -> AgentAction:
        if self._search_needed(obs):
            return self._search(obs, self.search)
        anchor = self._unwritten_anchor(obs)
        if anchor is not None:
            return self._write(anchor)
        return self._idle(obs)

    def _adapt(self, obs: ObservationV2) -> AgentAction:
        tick = obs.current_tick
        if self.mode != "hunt" and tick > ADAPT_SWITCH_TICK and not self.info_event and self.last_damage_tick is None:
            self.mode = "hunt"
        if self.mode == "hunt":
            return self._attack(obs, "fast")
        if self.callback_index == 1:
            return self._read(obs, "check", obs.own_core_base + (tick - 1) % CORE_SIZE)
        if self.pending_evade:
            self.pending_evade = False
            self.evaded = True
            return self._move(self.evade_sign * self.evade_magnitude)
        guarding = (self.last_visible_tick is not None and tick < self.last_visible_tick + ADAPT_HOLD_TICKS) or (
            self.last_damage_tick is not None and tick < self.last_damage_tick + ADAPT_HOLD_TICKS
        )
        self.mode = "guard" if guarding else "paint"
        return self._guard(obs) if guarding else self._idle(obs)

    def _choose(self, obs: ObservationV2) -> AgentAction:
        if self.evade and not self.evaded:
            self.evaded = True
            return self._move(self.evade_sign * self.evade_magnitude)
        if self.adaptive:
            return self._adapt(obs)
        if self.processes == 2:
            if obs.self_process_id == "sensor":
                return self._sensor(obs)
            return self._attack(obs, "none")
        if self.posture == "attack":
            return self._attack(obs, self.search)
        if self.posture == "guard":
            return self._guard(obs)
        return self._idle(obs)


def create_agent() -> Agent:
    return Agent()
