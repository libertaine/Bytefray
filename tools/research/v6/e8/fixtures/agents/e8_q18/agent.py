"""V6 E8 family: the one policy source every package shares.

A transcription of docs/research/v6/V6_E8_ACTIVE_SPATIAL_SENSING_IMPLEMENTATION_PLAN.md
Sec 5 (the registered semantics are
docs/research/v6/V6_E8_ACTIVE_SPATIAL_SENSING_PREREGISTRATION.md Sec 2.5 and 3,
revision 5). The posture, verification-READ, core-cursor and adoption
semantics are the frozen E6 family's, as corrected by E6's amendment 1, and
are carried over from that source unchanged. Every package's ``agent.py`` is
this file, byte for byte; a package is nothing but its manifest's parameter
defaults, delivered on ``context.parameters``:

* ``acquire``: ``none``, ``spatial-fast``, ``spatial-paced`` or ``ownership``;
* ``reacquire``: ``none`` (the registration's "not applicable"), ``once``,
  ``repeat`` or ``adaptive``;
* ``posture``: ``attack``, ``guard`` or ``paint``;
* ``evade``: ``off`` or ``on-hit``;
* ``processes``: 1, or 2 for a sensor (share 1/4) and a striker (3/4);
* ``stress``: the tick- and callback-keyed own-core check.

The condition is read from ``context.sensing_window``: ``None`` is passive
visibility (the known set is the current visible set), an integer is active
sensing (the known set is what applied SENSE results returned). No SENSE is
ever returned when ``sensing_window`` is ``None``.

One instance serves every process of its entrant, so knowledge is
entrant-wide. Randomness comes only from ``context.rng``: at reset, the
direction sigma and then the paint side, and nothing else; in play, tau when a
re-acquisition search starts, and sigma_e then m at each evasion. There is no
other state and no clock.

Research-only; never a product starter agent.
"""

from __future__ import annotations

from typing import Any

from battle_engine.agent_api import (
    ActionKindV2,
    AgentAction,
    MatchContextV2,
    ObservationV2,
    ProcessDeclaration,
)

# --- E6's constants, unchanged ----------------------------------------------
CORE_BEACON = 0xCE  # a core cell's value; the value every repair writes
MARK = 0x01  # the value of every other write: disruption, core attack, paint
CORE_SIZE = 8
MAX_STRIDE = 64  # the largest MOVE
PROBE_STRIDE = 8  # one probe per core-sized window
PROBE_SPAN = 64  # verification reads a + 1 + 8k, k = -8..8: [a - 63, a + 65] around a last-known anchor
MIN_CORE_SEPARATION = 64
READ_ARC = 49  # the READ search: own_core_base + sigma * (64 + 8m), m = 0..48
# Unverified adoption is allowed only before the opponent could have acted:
# at the tick-1 first callback of the entrant scheduled to move first (Seat A
# under every E6 and E8 Ruleset: chunk 2, start rotated by (tick - 1) mod 2).
FIRST_TICK = 1
FIRST_MOVER_SEAT = "A"
SENSOR_SHARE, STRIKER_SHARE = 0.25, 0.75

# --- E8's registered constants (PR8 Sec 2.5 and 3.2) ------------------------
QUOTA = 8  # offers per entrant per tick: EVADE8's hit inference (ii)
DISCOVERY_OFFSET = 91  # c_k = own_core_base + sigma * (91 + 55k)
DISCOVERY_STEP = 55
DISCOVERY_WINDOWS = 7  # k = 0..6, then the traversal restarts at k = 0
REACQUIRE_OFFSET = 46  # the re-acquisition centers a, a + tau * 46, a - tau * 46
EVADE_MIN, EVADE_MAX = 8, 64  # m on [8, 64]
ADAPT_K = 2  # consecutive confirming verification observations before ADAPT8 stops verifying
REACQUIRING = ("repeat", "adaptive")


class Agent:
    def __init__(self) -> None:
        self.arena = 0
        self.me = ""
        self.acquire = "none"
        self.reacquire = "none"
        self.posture = "paint"
        self.evade = "off"
        self.processes = 1
        self.stress = False
        self.sensing_window: int | None = None
        self.rng: Any = None
        self.direction = 1  # sigma
        self.paint_side = 0
        self._forget()

    def _forget(self) -> None:
        # --- E6's knowledge and cursors (entrant-wide) ----------------------
        self.last_known: tuple[int, int] | None = None  # (anchor address, tick set)
        self.enemy_core: int | None = None
        # Per-tick bookkeeping: the callback index is 1-based, entrant-wide,
        # and restarts when current_tick changes.
        self.tick = -1
        self.callback_index = 0
        self.written: set[int] = set()
        self.first_callback = True
        # Every address at which this entrant has written a known enemy anchor.
        self.anchor_writes: set[int] = set()
        # Core verification: a READ window around the last-known anchor, then
        # the contiguous run of enemy beacons through the first hit, scanned
        # down and then up.
        self.window: list[int] = []
        self.window_center: int | None = None
        self.run_low: int | None = None
        self.run_high: int | None = None
        self.run_down = True
        self.below_is_written_anchor = False
        # The READ or SENSE each process is waiting to see the result of:
        # process id -> (purpose, address).
        self.pending: dict[str, tuple[str, int]] = {}
        self.core_cursor = 0
        self.read_m = 0
        self.paint_k = 0
        self.guard_cursor = 0
        # --- E8's knowledge (PR8 Sec 2.5 and 3.2) ---------------------------
        # The known set: under passive, this callback's visible set; under
        # active, the remembered results of applied SENSE actions.
        self.known: tuple[int, ...] = ()
        # Passive only: the visible set at the entrant's previous callback.
        self.tracked: tuple[int, ...] = ()
        # Missing addresses awaiting re-acquisition, ascending (KU-6), and the
        # last replacement map {missing: replacement} (KU-7).
        self.missing: list[int] = []
        self.replacements: dict[int, int] = {}
        self.discovery_k = 0
        self.discovered = False
        # The re-acquisition search in progress: its missing address a, its
        # remaining centers, and the index of the next one.
        self.search_address: int | None = None
        self.search_centers: list[int] = []
        self.search_next = 0
        # ADAPT8.
        self.adapt_count = 0
        self.switched = False
        # EVADE8: the tick of the entrant's most recent earlier callback, and
        # how many callbacks it received in that tick.
        self.previous_tick: int | None = None
        self.previous_tick_callbacks = 0
        # STRESS8: the own-core cell its next action must repair.
        self.repair_cell: int | None = None

    # ------------------------------------------------------------------ API

    def reset(self, context: MatchContextV2) -> None:
        self.arena = context.arena_size
        self.me = context.agent_id
        parameters = context.parameters
        self.acquire = str(parameters.get("acquire", "none"))
        self.reacquire = str(parameters.get("reacquire", "none"))
        self.posture = str(parameters.get("posture", "paint"))
        self.evade = str(parameters.get("evade", "off"))
        self.processes = int(parameters.get("processes", 1))
        self.stress = bool(parameters.get("stress", False))
        self.sensing_window = context.sensing_window
        self.rng = context.rng
        self.direction = (-1, 1)[context.rng.randrange(2)]
        self.paint_side = context.rng.randrange(2)
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
        # 1. Tick bookkeeping.
        if obs.current_tick != self.tick:
            if not self.first_callback:
                self.previous_tick = self.tick
                self.previous_tick_callbacks = self.callback_index
            self.tick = obs.current_tick
            self.callback_index = 0
            self.written = set()
        self.callback_index += 1
        # 2. The previous action's result, for this process.
        self._absorb(obs)
        # 3. Observation.
        self._observe(obs)
        # 4. The action.
        action = self._choose(obs)
        self.first_callback = False
        return action

    # ------------------------------------------------------------ knowledge

    def _distance(self, a: int, b: int) -> int:
        d = (a - b) % self.arena
        return min(d, self.arena - d)

    def _nearest(self, address: int, candidates: tuple[int, ...]) -> int:
        """KU-7: the candidate at minimum circular distance from ``address``, the lower on a tie."""

        return min(candidates, key=lambda candidate: (self._distance(candidate, address), candidate))

    def _reacquiring(self) -> bool:
        return self.reacquire in REACQUIRING and not self.switched

    def _is_enemy_core_cell(self, obs: ObservationV2) -> bool:
        return (
            obs.previous_action_applied
            and obs.previous_read_value == CORE_BEACON
            and obs.previous_read_owner is not None
            and obs.previous_read_owner != self.me
        )

    def _absorb(self, obs: ObservationV2) -> None:
        """Take in the result of this process's previous READ or SENSE, if it was one."""

        waiting = self.pending.pop(obs.self_process_id, None)
        if waiting is None:
            return
        purpose, address = waiting
        if purpose == "check":
            # STRESS8: an owner other than itself obliges a repair.
            if obs.previous_read_owner != self.me:
                self.repair_cell = address
            return
        if purpose in ("discover", "verify", "search"):
            self._sensed(obs, purpose, address)
            return
        # A READ, exactly as the E6 family: verification, probe or scan.
        hit = self._is_enemy_core_cell(obs)
        if self.enemy_core is not None:
            return
        if purpose in ("verify-read", "probe"):
            if hit and self.run_low is None:
                self.run_low = self.run_high = address
                self.run_down = True
        elif purpose == "scan":
            self._extend_run(obs, address, hit)

    def _sensed(self, obs: ObservationV2, purpose: str, target: int) -> None:
        """An applied SENSE's result: KU-1 to KU-4, then KU-7, the search and ADAPT8's count."""

        result = obs.previous_sense_anchors
        if result is None or self.sensing_window is None:
            # A refused SENSE changes nothing (PR8 Sec 3.2): knowledge is
            # unchanged, and the window it was to sense is sensed next instead.
            # (Unreachable: every process declares reach arena // 2, the
            # largest circular distance.)
            if purpose == "discover":
                self.discovery_k = (self.discovery_k - 1) % DISCOVERY_WINDOWS
            elif purpose == "search" and self.search_address is not None:
                self.search_next -= 1
            return
        before = self.known
        # KU-1, KU-3: a known address inside the sensed window and absent from
        # the result becomes missing. KU-4: one outside it is unchanged.
        # KU-2: every returned address becomes known.
        gone = [x for x in before if self._distance(x, target) <= self.sensing_window and x not in result]
        self.known = tuple(sorted({x for x in before if x not in gone} | set(result)))
        if result:
            self.discovered = True
            self.discovery_k = 0  # the discovery traversal stops; a later one starts at k = 0
        if self.reacquire == "adaptive" and not self.switched:
            if purpose == "verify":
                # The verification observation: it confirms a, or finds it missing.
                self.adapt_count = self.adapt_count + 1 if target in result else 0
            elif before and before[0] in gone:
                self.adapt_count = 0  # a found missing at another callback
            if self.adapt_count >= ADAPT_K:
                self._switch()
        self._lose(gone, result)
        if (
            purpose == "search"
            and self.search_address is not None
            and self.search_next == len(self.search_centers)
        ):
            # The last window was empty too: a is unknown.
            self._exhausted()

    def _lose(self, gone: list[int], returned: tuple[int, ...]) -> None:
        """Missing addresses (KU-3, KU-5), their replacements (KU-7) and the search they start (RP-3)."""

        if not self._reacquiring():
            self.missing = []
            return
        missing = sorted(set(self.missing) | set(gone))
        if returned:
            # Every missing address is replaced by the returned address nearest
            # it, and a search in progress ends.
            replaced = list(missing)
            if self.search_address is not None:
                replaced.append(self.search_address)
                self._end_search()
            if replaced:
                self.replacements = {m: self._nearest(m, returned) for m in sorted(replaced)}
            missing = []
        self.missing = missing
        if self.missing and self.search_address is None:
            self._start_search()

    def _start_search(self) -> None:
        """RP-3: search for the lowest missing address (KU-6); tau is drawn now (P8-2)."""

        a = self.missing.pop(0)
        tau = (-1, 1)[self.rng.randrange(2)]
        if self.sensing_window is not None:
            # The verification window at a has been sensed: the next two remain.
            centers = [a + tau * REACQUIRE_OFFSET, a - tau * REACQUIRE_OFFSET]
        else:
            centers = [a, a + tau * REACQUIRE_OFFSET, a - tau * REACQUIRE_OFFSET]
        self.search_address = a
        self.search_centers = [center % self.arena for center in centers]
        self.search_next = 0

    def _end_search(self) -> None:
        self.search_address = None
        self.search_centers = []
        self.search_next = 0

    def _exhausted(self) -> None:
        """The search sequence is exhausted: a is unknown; the next missing address is serviced."""

        self._end_search()
        if self.missing and self._reacquiring():
            self._start_search()

    def _switch(self) -> None:
        """ADAPT8, at its second consecutive confirmation: as ``once`` for the rest of the match."""

        self.switched = True
        self.missing = []
        self._end_search()

    def _run_length(self) -> int:
        assert self.run_low is not None and self.run_high is not None
        return (self.run_high - self.run_low) % self.arena + 1

    def _end_run(self, base: int | None) -> None:
        self.enemy_core = base
        self.run_low = None
        self.run_high = None
        self.below_is_written_anchor = False

    def _extend_run(self, obs: ObservationV2, address: int, hit: bool) -> None:
        """Grow the run of enemy beacons by one scanned cell; confirm the core, or give up on it.

        Eight contiguous enemy beacons are the core, and the lowest is its
        base. Seven are the core only when the cell just below them is an
        enemy anchor this entrant has itself overwritten (so it cannot be
        read): that anchor stands in for core cell 0. Anything else leaves
        the core unconfirmed, and verification continues.
        """

        assert self.run_low is not None and self.run_high is not None
        if hit:
            if self.run_down:
                self.run_low = address
            else:
                self.run_high = address
            if self._run_length() == CORE_SIZE:
                self._end_run(self.run_low)
            return
        if self.run_down:
            self.run_down = False
            self.below_is_written_anchor = (
                address in self.anchor_writes
                and obs.previous_action_applied
                and obs.previous_read_owner == self.me
            )
            return
        if self._run_length() == CORE_SIZE - 1 and self.below_is_written_anchor:
            self._end_run((self.run_low - 1) % self.arena)
        else:
            self._end_run(None)

    def _observe(self, obs: ObservationV2) -> None:
        if self.sensing_window is None:
            # Passive: the known set is the visible set. A tracked address
            # absent from it becomes missing (KU-5).
            visible = tuple(obs.visible_enemy_anchor_addresses)
            gone = [x for x in self.tracked if x not in visible]
            if self.reacquire == "adaptive" and not self.switched and self.tracked:
                a = self.tracked[0]
                if a not in visible:
                    self.adapt_count = 0  # an observed relocation
                elif self.callback_index == 1:
                    # The verification observation: the visible set at the
                    # first offer of the tick confirms the lowest tracked address.
                    self.adapt_count += 1
                if self.adapt_count >= ADAPT_K:
                    self._switch()
            self.known = visible
            self._lose(gone, visible)
            self.tracked = visible
        if self.known:
            self.last_known = (self.known[0], obs.current_tick)
        # Unverified adoption (E6 amendment 1, C-1), on the known set: only at
        # the first mover's tick-1 first callback, and only for a single known
        # address that cannot lie in its own core's exclusion zone.
        if (
            self.first_callback
            and obs.current_tick == FIRST_TICK
            and self.me == FIRST_MOVER_SEAT
            and self.enemy_core is None
            and len(self.known) == 1
            and self._distance(self.known[0], obs.own_core_base) >= MIN_CORE_SEPARATION
        ):
            self.enemy_core = self.known[0]

    def _acquisition_eligible(self) -> bool:
        """No enemy anchor is known, and the entrant has not confirmed the enemy core (Revision 3)."""

        return not self.known and self.enemy_core is None

    def _hit_inferred(self, obs: ObservationV2) -> bool:
        """EVADE8, at its first callback of a tick: (i) a whole tick without a callback, or
        (ii) fewer than 8 callbacks in the most recent tick in which it received any.
        Never at the first callback of the match (P8-5)."""

        if self.previous_tick is None:
            return False
        return obs.current_tick > self.previous_tick + 1 or self.previous_tick_callbacks < QUOTA

    # -------------------------------------------------------------- actions

    def _write(self, address: int, value: int = MARK) -> AgentAction:
        address %= self.arena
        self.written.add(address)
        return AgentAction(ActionKindV2.WRITE, operand=address, value=value)

    def _read(self, obs: ObservationV2, purpose: str, address: int) -> AgentAction:
        address %= self.arena
        self.pending[obs.self_process_id] = (purpose, address)
        return AgentAction(ActionKindV2.READ, operand=address)

    def _sense(self, obs: ObservationV2, purpose: str, target: int) -> AgentAction:
        if self.sensing_window is not None:
            target %= self.arena
            self.pending[obs.self_process_id] = (purpose, target)
            return AgentAction(ActionKindV2.SENSE, operand=target)
        raise RuntimeError("no SENSE without a sensing window")

    def _move(self, delta: int) -> AgentAction:
        return AgentAction(ActionKindV2.MOVE, operand=delta)

    def _move_toward(self, obs: ObservationV2, center: int) -> AgentAction:
        """The shortest signed circular displacement to ``center``, at most 64 (P8-3)."""

        delta = (center - obs.self_anchor) % self.arena
        if delta > self.arena // 2:
            delta -= self.arena
        return self._move(max(-MAX_STRIDE, min(MAX_STRIDE, delta)))

    def _disrupt(self, anchor: int) -> AgentAction:
        self.anchor_writes.add(anchor % self.arena)
        return self._write(anchor)

    def _unwritten_anchor(self) -> int | None:
        for address in self.known:
            if address not in self.written:
                return address
        return None

    def _paint(self, obs: ObservationV2) -> AgentAction:
        """Paint outward from the own core, alternating sides."""

        pair, second = divmod(self.paint_k % (2 * (self.arena // 2 - CORE_SIZE // 2)), 2)
        self.paint_k += 1
        up = obs.own_core_base + CORE_SIZE + pair
        down = obs.own_core_base - 1 - pair
        first_up = self.paint_side == 0
        return self._write(up if first_up != bool(second) else down)

    def _discover(self, obs: ObservationV2) -> AgentAction:
        """The spatial discovery step: E6's MOVE sweep under passive, the SENSE traversal under active."""

        if self.sensing_window is not None:
            k = self.discovery_k
            self.discovery_k = (k + 1) % DISCOVERY_WINDOWS
            return self._sense(obs, "discover", obs.own_core_base + self.direction * (DISCOVERY_OFFSET + DISCOVERY_STEP * k))
        return self._move(MAX_STRIDE * self.direction)

    def _acquisition(self, obs: ObservationV2) -> AgentAction | None:
        """The acquisition step, once it is eligible; ``None`` when ``acquire`` is ``none``."""

        if self.acquire == "spatial-fast":
            return self._discover(obs)
        if self.acquire == "spatial-paced":
            if self.callback_index % 2 == 1:
                return self._discover(obs)
            return self._paint(obs)
        if self.acquire == "ownership":
            m = self.read_m
            self.read_m = (m + 1) % READ_ARC
            return self._read(obs, "probe", obs.own_core_base + self.direction * (MIN_CORE_SEPARATION + PROBE_STRIDE * m))
        return None

    def _verification_read(self, obs: ObservationV2) -> AgentAction | None:
        if self.run_low is not None:
            assert self.run_high is not None
            return self._read(obs, "scan", self.run_low - 1 if self.run_down else self.run_high + 1)
        if self.last_known is None:
            return None
        center = self.last_known[0]
        if center != self.window_center:
            # The stride-8 lattice through the cell one past the anchor, so a
            # disruption of an anchor on core cell 0 never erases the one
            # sampled core cell.
            self.window_center = center
            self.window = [center + 1]
            for step in range(PROBE_STRIDE, PROBE_SPAN + 1, PROBE_STRIDE):
                self.window += [center + 1 - step, center + 1 + step]
        if not self.window:
            # The window held no enemy core cell: forget the anchor.
            self.last_known = None
            self.window_center = None
            return None
        return self._read(obs, "verify-read", self.window.pop(0))

    def _search_step(self, obs: ObservationV2) -> AgentAction | None:
        """The next action of the re-acquisition search in progress (RP-1, RP-2)."""

        if self.sensing_window is not None:
            center = self.search_centers[self.search_next]
            self.search_next += 1
            return self._sense(obs, "search", center)
        # Passive: MOVE toward each center in order; a center is reached when
        # the anchor equals it. Reaching the last one with nothing visible
        # exhausts the search.
        while self.search_address is not None:
            while self.search_next < len(self.search_centers) and obs.self_anchor == self.search_centers[self.search_next]:
                self.search_next += 1
            if self.search_next < len(self.search_centers):
                return self._move_toward(obs, self.search_centers[self.search_next])
            self._exhausted()
        return None

    def _attack(self, obs: ObservationV2, acquire: bool) -> AgentAction:
        anchor = self._unwritten_anchor()
        if anchor is not None:
            return self._disrupt(anchor)
        if self.enemy_core is not None:
            # A cyclic cursor over the core, carried across ticks and advanced
            # only past the cell written, skipping cells written this tick.
            for step in range(CORE_SIZE):
                index = (self.core_cursor + step) % CORE_SIZE
                cell = (self.enemy_core + index) % self.arena
                if cell not in self.written:
                    self.core_cursor = (index + 1) % CORE_SIZE
                    return self._write(cell)
        else:
            verification = self._verification_read(obs)
            if verification is not None:
                return verification
        if acquire and self._acquisition_eligible():
            action = self._acquisition(obs)
            if action is not None:
                return action
        return self._paint(obs)

    def _guard(self, obs: ObservationV2) -> AgentAction:
        anchor = self._unwritten_anchor()
        if anchor is not None:
            return self._disrupt(anchor)
        if self._acquisition_eligible():
            action = self._acquisition(obs)
            if action is not None:
                return action
        cell = obs.own_core_base + self.guard_cursor
        self.guard_cursor = (self.guard_cursor + 1) % CORE_SIZE
        return self._write(cell, CORE_BEACON)

    def _sensor(self, obs: ObservationV2) -> AgentAction:
        if self._acquisition_eligible():
            action = self._acquisition(obs)
            if action is not None:
                return action
        anchor = self._unwritten_anchor()
        if anchor is not None:
            return self._disrupt(anchor)
        return self._paint(obs)

    def _choose(self, obs: ObservationV2) -> AgentAction:
        # 4.1 Member-level steps.
        if self.evade == "on-hit" and self.callback_index == 1 and self._hit_inferred(obs):
            sign = (-1, 1)[self.rng.randrange(2)]
            magnitude = self.rng.randint(EVADE_MIN, EVADE_MAX)
            return self._move(sign * magnitude)
        if self.stress:
            if self.callback_index == 1:
                self.repair_cell = None  # a stale obligation is dropped (P8-6)
                return self._read(obs, "check", obs.own_core_base + (obs.current_tick - 1) % CORE_SIZE)
            if self.repair_cell is not None:
                cell, self.repair_cell = self.repair_cell, None
                return self._write(cell, CORE_BEACON)
        # 4.2 A re-acquisition search in progress takes precedence over the posture steps.
        if self.search_address is not None and self._reacquiring():
            action = self._search_step(obs)
            if action is not None:
                return action
        # 4.3 Verification, under active: the first callback of a tick after
        # first discovery, with an address known and no search in progress,
        # centered on the lowest known address (KU-8).
        if (
            self.sensing_window is not None
            and self._reacquiring()
            and self.callback_index == 1
            and self.discovered
            and self.known
            and self.search_address is None
        ):
            return self._sense(obs, "verify", self.known[0])
        # 4.4 The posture steps.
        if self.processes == 2:
            if obs.self_process_id == "sensor":
                return self._sensor(obs)
            return self._attack(obs, acquire=False)
        if self.posture == "attack":
            return self._attack(obs, acquire=True)
        if self.posture == "guard":
            return self._guard(obs)
        return self._paint(obs)


def create_agent() -> Agent:
    return Agent()
