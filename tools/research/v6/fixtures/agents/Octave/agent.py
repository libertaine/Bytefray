"""Octave -- an Agent API v2 entrant built around one idea: own all eight.

Design summary
--------------

Ruleset v4 eliminates an entrant the moment it owns **zero** of the eight
cells of its own core, checked once per tick after every action in that tick
has run. Partial damage is worth nothing. So the whole agent is organised
around producing, on a single tick, a complete eight-cell capture of an
address window it has *proved* belongs to the opponent.

Four facts about the public contract drive every design choice here:

1. ``reach`` is declared per process in ``[1, arena_size - 1]``, costs
   nothing, and the maximum circular distance in the arena is
   ``arena_size // 2``. A process declaring that reach can READ or WRITE any
   address in the arena from wherever it stands, and can sense any enemy
   anchor. Octave declares it on every process by default and consequently
   never spends an action on travel. ``process_reach`` exists as a parameter
   so this can be dialled back for a fair fight -- see the README.

2. ``previous_read_owner`` is the one legal channel that identifies ground as
   enemy-held. Before an opponent writes anything, the only cells it owns are
   the eight of its own core -- the engine establishes that ownership at
   match start. A READ returning a foreign owner is therefore evidence, not a
   guess, and a core is eight *contiguous* cells, so a stride-``core_size``
   sweep cannot step over one.

3. Every process of an entrant starts co-located at that entrant's own core
   base. The first sighting of a match is therefore the best available
   estimate of where the opponent's core is, and the search is ordered
   outward from it rather than blindly.

4. Disruption is per *address*: a legal enemy WRITE suppresses every process
   anchored on that exact cell for the rest of the tick. Quota lost by a
   suppressed process is redistributed to its eligible siblings, so an
   entrant only truly loses actions when **all** of its processes are
   suppressed. That cuts both ways, and Octave plays both sides of it:

   * it disperses its own processes to distinct addresses off its own core,
     so no single enemy write can silence the entrant;
   * it hoists core cells that coincide with a visible enemy anchor to the
     front of its strike order, so a defender standing on its own core is
     suppressed early in the tick it dies on.

Architecture
------------

Processes are **not** given fixed roles. They exist to provide distinct
anchors (see 4 above) and they all share one reach, one world model and one
per-tick priority cascade. Whichever process is handed the next action slot
takes the next-highest-priority task. That guarantees the most valuable work
gets the earliest slots of a tick, which fixed roles cannot do: a role-bound
process has to wait its turn even when its job is the least urgent thing on
the board.

Knowledge is kept as one address -> owner map built only from READ results.
There is no inference from sightings into ownership: a sighting tells you
where a *worker* stands, which is not where a core is, and conflating the two
is what makes an agent bombard empty ground.

Determinism: ``context.rng`` only, no wall clock, no module-global
randomness, every set sorted before iteration.
"""

from __future__ import annotations

from math import gcd

from battle_engine.agent_api import (
    ActionKindV2,
    AgentAction,
    MatchContextV2,
    ObservationV2,
    ProcessDeclaration,
)

# Signature bytes. Content is never load-bearing -- ownership is what the
# rules score and kill on -- but distinct values make a replay readable.
STRIKE_BYTE = 0x8E
REPAIR_BYTE = 0xA1
CLAIM_BYTE = 0x5C

DEFAULT_PROCESS_COUNT = 4
DEFAULT_GUARD_ACTIONS = 2
DEFAULT_DISPERSE_SPAN = 48
DEFAULT_SIGHTING_WINDOW = 2


class OctaveAgent:
    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def reset(self, context: MatchContextV2) -> None:
        self.ctx = context
        self.arena = context.arena_size
        self.me = context.agent_id

        params = context.parameters or {}
        self.process_count = max(1, min(8, int(params.get("process_count", DEFAULT_PROCESS_COUNT))))
        # 0 means "as far as the arena goes": the greatest circular distance
        # between two cells is arena_size // 2, so that reach makes every
        # address reachable. A literal default could not say this -- it would
        # be silently short on a larger arena than the one it was written for.
        declared_reach = int(params.get("process_reach", 0))
        self.reach = self._legal_reach(
            self.arena // 2 if declared_reach <= 0 else declared_reach
        )
        self.guard_actions = max(0, min(8, int(params.get("guard_actions", DEFAULT_GUARD_ACTIONS))))
        self.disperse_span = max(0, int(params.get("disperse_span", DEFAULT_DISPERSE_SPAN)))
        self.sighting_window = max(0, int(params.get("sighting_window", DEFAULT_SIGHTING_WINDOW)))
        self.claim_territory = bool(params.get("claim_territory", True))
        self.burst_on_last_mover_only = bool(
            params.get("burst_on_last_mover_only", True)
        )
        self.burst_retries = max(1, int(params.get("burst_retries", 2)))

        # --- world model -------------------------------------------------
        # One map, built only from READ feedback: address -> owner id or None.
        self.owner_of: dict[int, str | None] = {}
        self.target_base: int | None = None
        self.target_owner: str | None = None
        self.burst_failures: dict[int, int] = {}
        self.burst_completed_tick = -1
        self.written: set[int] = set()

        # --- search ------------------------------------------------------
        self.search_centre: int | None = None
        self.search_cursor = 0
        self.search_exhausted = False
        self.probe_queue: list[int] = []
        self.queued: set[int] = set()

        # --- per-tick bookkeeping ---------------------------------------
        self.tick = -1
        self.quota = 8                                # learned, not assumed
        self.actions_this_tick = 0
        self.strike_queue: list[int] = []
        self.guard_cursor = 0
        self.claim_cursor = 0

        # --- per-process state ------------------------------------------
        self.pending_read: dict[str, int] = {}
        self.anchors: dict[str, int] = {}
        self.disperse_target: dict[str, int] = {}
        self.under_pressure_until = -1
        self.suppressed_this_tick: set[int] = set()

        # Seat index, for the scheduling-parity rule below. agent_id is
        # the entrant's slot letter; entrant_count starts at the minimum
        # consistent with our own slot and is raised if a READ ever
        # reveals a third owner.
        self.seat_index = max(0, ord(self.me[0]) - ord("A")) if self.me else 0
        self.entrant_count = max(2, self.seat_index + 1)

        # Seed-derived so two Octaves on one seed do not sweep in lockstep.
        # context.rng is the only legal source of randomness in a v2 entrant.
        self.search_jitter = context.rng.randrange(max(1, self.arena))
        self.claim_stride = self._coprime_stride(self.arena, 97)

    def declare_processes(self) -> list[ProcessDeclaration]:
        """Equal shares across ``process_count`` identical processes.

        Shares are validated as an *exact* total of 1.0, and the engine reads
        them as exact rationals, so the usual advice -- write ``s`` and
        ``1.0 - s`` rather than two literals -- only actually holds for two
        processes. With three, ``1/3 + 1/3 + (1.0 - 2/3)`` does not sum to one
        in binary floating point and the roster is rejected before the match
        starts. Three equal shares have no exact binary representation at all.

        So the split is done in integers over a power-of-two denominator and
        converted at the end. Every ``weight / 1024`` is exactly representable
        because the denominator is a power of two, and the weights sum to
        1024 by construction, so the total is exactly 1.0 for any count.

        Equal shares matter beyond arithmetic: ``Q = 8`` is allocated by
        largest-remainder rounding and handed out in rotation, so ``n`` equal
        processes each get a guaranteed slice and the roster stays balanced
        when one of them is suppressed. The processes are identical on
        purpose -- they are anchors, not roles.
        """
        count = self.process_count
        denominator = 1 << 10
        quotient, remainder = divmod(denominator, count)
        weights = [quotient + (1 if index < remainder else 0) for index in range(count)]
        return [
            ProcessDeclaration(id=f"p{index}", reach=self.reach, share=weight / denominator)
            for index, weight in enumerate(weights)
        ]

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    def act(self, observation: ObservationV2) -> AgentAction:
        self._begin_tick(observation)
        self._ingest_feedback(observation)
        self._ingest_sightings(observation)

        self.anchors[observation.self_process_id] = observation.self_anchor
        self.actions_this_tick += 1
        remaining_after_this = max(0, self.quota - self.actions_this_tick)

        # 1. Kill. A confirmed window outranks everything: partial damage
        #    scores nothing, so a burst that gets interrupted is wasted.
        if self.strike_queue:
            return self._strike(observation)

        # 2. Get out from under a single enemy write, while still stacked.
        disperse = self._disperse(observation)
        if disperse is not None:
            return disperse

        # 3. Reserve the tail of the tick for our own core. Placed here so
        #    the refresh lands as late in the tick as the schedule allows,
        #    which is the only part of a tick an opponent cannot answer.
        if remaining_after_this < self._guard_budget(observation):
            return self._guard(observation)

        # 3b. On a tick we cannot finish on, spend the budget denying the
        #     opponent theirs: a WRITE on a live anchor suppresses every
        #     process standing there for the rest of the tick.
        suppress = self._suppress(observation)
        if suppress is not None:
            return suppress

        # 4. Resolve a candidate window into an exact core base.
        if self.probe_queue:
            return self._probe(observation, self._next_queued())

        # 4b. A target that has already survived a burst has not earned the
        #     whole budget. Keep one action a tick on the sweep, so a window
        #     that turns out to be wrong cannot starve the search that would
        #     replace it -- the failure mode where an agent looks busy for
        #     four hundred ticks and never learns anything.
        if (
            self.target_base is not None
            and self.burst_failures.get(self.target_base, 0) > 0
            and not self.search_exhausted
        ):
            return self._search(observation)

        # 5. Sweep for enemy-owned ground.
        if not self.search_exhausted:
            return self._search(observation)

        return self._claim(observation)

    # ------------------------------------------------------------------
    # Tick boundary
    # ------------------------------------------------------------------

    def _begin_tick(self, obs: ObservationV2) -> None:
        if obs.current_tick == self.tick:
            return
        if self.tick >= 0:
            self.quota = max(self.quota, self.actions_this_tick)
        self._note_burst_outcome(obs)
        self.tick = obs.current_tick
        self.actions_this_tick = 0
        self.suppressed_this_tick = set()
        self.strike_queue = self._build_strike_queue(obs)

    def _build_strike_queue(self, obs: ObservationV2) -> list[int]:
        """This tick's eight addresses, ordered for maximum effect.

        Cells that coincide with a live enemy anchor go first: that WRITE
        claims the cell *and* suppresses every enemy process standing on it
        for the rest of the tick -- exactly the budget the opponent would
        otherwise spend taking the other seven back.

        The remainder is rotated by tick so no single cell is systematically
        written first, and therefore systematically the easiest to reclaim.
        """
        if self.target_base is None:
            return []
        if self.burst_on_last_mover_only and not self._is_last_mover(obs.current_tick):
            return []

        size = max(1, obs.own_core_size)
        cells = [(self.target_base + offset) % self.arena for offset in range(size)]
        visible = set(obs.visible_enemy_anchor_addresses)

        on_anchor = [cell for cell in cells if cell in visible]
        rest = [cell for cell in cells if cell not in visible]
        if rest:
            shift = (obs.current_tick * 3) % len(rest)
            rest = rest[shift:] + rest[:shift]
        return on_anchor + rest

    # ------------------------------------------------------------------
    # Observation intake
    # ------------------------------------------------------------------

    def _ingest_feedback(self, obs: ObservationV2) -> None:
        """Consume the delayed READ result belonging to this process."""
        # A callback gap means this process missed a tick, which under
        # Ruleset v4 can only mean an enemy WRITE landed on its anchor.
        if 0 <= obs.last_callback_tick < obs.current_tick - 1:
            self.under_pressure_until = max(self.under_pressure_until, obs.current_tick + 2)

        address = self.pending_read.pop(obs.self_process_id, None)
        if address is None or not obs.previous_action_applied:
            return

        # Ownership evidence is only trustworthy before we contaminate it.
        # Our own WRITE makes us the owner of that cell, so a later read of a
        # struck cell reports us and the window it belonged to can never be
        # re-derived. Keep the first, uncontaminated observation instead: a
        # core cell belongs to its entrant from match start, so the earliest
        # reading is the true one.
        if address not in self.written:
            self.owner_of[address] = obs.previous_read_owner
        owner = self.owner_of.get(address)

        # Every read changes the map, and a read that comes back unowned is
        # as informative as one that comes back enemy-held -- it is what rules
        # a window out. So re-rank on any result, not only on a foreign owner;
        # ranking on foreign owners alone means the reads that disprove a
        # window never get the chance to.
        if owner is None or owner == self.me:
            if self.target_base is None:
                self._choose_target(obs)
            return
        self.entrant_count = max(self.entrant_count, ord(owner[0]) - ord("A") + 1)
        if self.search_centre is None:
            # The sweep is defined as offsets from its centre, so moving
            # the centre invalidates the cursor counted against the old
            # one. Restart it rather than resume at a meaningless offset.
            self.search_centre = address
            self.search_cursor = 0
            self.search_exhausted = False
        if self.target_base is None:
            self._choose_target(obs)


    def _ingest_sightings(self, obs: ObservationV2) -> None:
        sightings = obs.visible_enemy_anchor_addresses
        if not sightings:
            return

        # Pressure: an enemy anchor on or beside our own core.
        size = max(1, obs.own_core_size)
        for address in sightings:
            if self._core_distance(obs.own_core_base, size, address) <= size * 2:
                self.under_pressure_until = max(self.under_pressure_until, obs.current_tick + 2)

        if self.target_base is not None or self.search_centre is not None:
            return
        if obs.current_tick > self.sighting_window:
            return

        # Every process starts co-located at its entrant's own core base, so
        # an early sighting is the closest thing to a free bearing on the
        # objective this API offers. But by the time we are first called some
        # of those processes may already have deployed, and there is no field
        # that says which is which.
        #
        # READ settles it. A worker that has deployed is standing on ground
        # nobody has written, which reads back as no owner; a worker still at
        # home is standing on a cell of its own core, which reads back as
        # owned by it. So probe every early sighting -- a handful of reads --
        # and let the one that comes back enemy-owned anchor the sweep.
        #
        # Picking among sightings by address instead would be a bug: the
        # arena is circular, so "lowest address" is not "nearest" and a
        # sighting either side of the wrap would win it by accident.
        for address in sorted(sightings)[:8]:
            self._queue_probe(address)

    # ------------------------------------------------------------------
    # Core-window resolution
    # ------------------------------------------------------------------

    def _note_burst_outcome(self, obs: ObservationV2) -> None:
        """A completed burst the opponent walked away from is disproof.

        With two entrants, still being called on the tick after a full
        eight-cell burst means the opponent was not eliminated by it -- so
        either it defended, or that window was never its core. Either way the
        window has failed to do the one thing it was chosen for, and after
        ``burst_retries`` failures it is struck off and the search resumes.
        This is the only way to recover from a window that looked perfect and
        was not, and without it a wrong lock is permanent.
        """
        if self.entrant_count != 2 or self.target_base is None:
            return
        if self.burst_completed_tick != obs.current_tick - 1:
            return
        base = self.target_base
        self.burst_failures[base] = self.burst_failures.get(base, 0) + 1
        self.burst_completed_tick = -1
        if self.burst_failures[base] >= self.burst_retries:
            self.target_base = None
            self.target_owner = None
            self._choose_target(obs)

    def _choose_target(self, obs: ObservationV2) -> None:
        """Rank every window the ownership map has not ruled out, and take the best.

        A core occupies ``[base, base + core_size - 1]``. Early in a match the
        only cells an opponent owns are its core, so a run of owned cells is
        the core exactly; later its own writes blur the edges, and insisting
        on a proven edge means never committing at all. So windows are ranked
        rather than filtered:

        * a window containing a cell **known** to belong to someone else is
          eliminated outright -- that is disproof, not weak evidence;
        * otherwise it scores on how many of its cells are proven enemy-held,
          then on how many of its two edges are proven *not*, which is what
          separates a real core from the middle of a larger scribble;
        * windows a burst has already failed against sink to the bottom.

        Only a fully proven window is committed to. Anything less queues the
        specific reads that would finish the proof, which is cheaper than a
        wasted burst and far cheaper than a blanket sweep.
        """
        size = max(1, obs.own_core_size)
        owners = {
            cell_owner
            for cell_owner in self.owner_of.values()
            if cell_owner is not None and cell_owner != self.me
        }
        best: tuple[tuple[int, int, int, int], str, int] | None = None
        for owner in sorted(owners):
            held = sorted(
                address for address, who in self.owner_of.items() if who == owner
            )
            seen: set[int] = set()
            for cell in held:
                for back in range(size):
                    base = (cell - back) % self.arena
                    if base in seen:
                        continue
                    seen.add(base)
                    window = [(base + offset) % self.arena for offset in range(size)]
                    # A cell we have read is evidence either way. An unowned
                    # cell disqualifies the window just as firmly as one held
                    # by somebody else: a core cell is owned by its entrant
                    # from match start, so a core can never contain blank
                    # ground. Only a cell we have *not* read is neutral.
                    read = [(address in self.owner_of, self.owner_of.get(address))
                            for address in window]
                    if any(seen and who != owner for seen, who in read):
                        continue
                    proven = sum(1 for seen, who in read if seen and who == owner)
                    edges = 0
                    for edge in ((base - 1) % self.arena, (base + size) % self.arena):
                        who = self.owner_of.get(edge, owner)
                        if who != owner:
                            edges += 1
                    rank = (
                        -self.burst_failures.get(base, 0),
                        proven,
                        edges,
                        -base,
                    )
                    if best is None or rank > best[0]:
                        best = (rank, owner, base)

        if best is None:
            return
        _, owner, base = best
        window = [(base + offset) % self.arena for offset in range(size)]
        edges = ((base - 1) % self.arena, (base + size) % self.arena)

        # Commit only to a window that is proven on all `size` cells *and*
        # bounded on both sides. A core is exactly `size` owned cells with
        # something else either side; a patch of ground the opponent merely
        # happens to have written over usually is not. Reading the two edge
        # cells is two actions against a whole wasted burst, so the reads win
        # -- unless the sweep has run out of arena to look at, in which case
        # the best proven window is the best there will ever be.
        # The edge test costs two reads and is worth them only once a cheap
        # commit has actually misfired. Until then the first fully proven
        # window is almost always the core -- before an opponent writes
        # anything, the only cells it owns are its core -- and paying for
        # rigour up front just hands it eighty ticks it did not earn.
        strict = bool(self.burst_failures) and not self.search_exhausted
        pending = [a for a in window if a not in self.owner_of]
        if not pending and strict:
            pending = [a for a in edges if a not in self.owner_of]
        if pending:
            for address in pending:
                self._queue_probe(address)
            return
        if strict and any(self.owner_of.get(edge) == owner for edge in edges):
            return

        self.target_base = base
        self.target_owner = owner
        self.strike_queue = self._build_strike_queue(obs)

    def _queue_probe(self, address: int) -> None:
        address %= self.arena
        if address in self.queued or address in self.owner_of:
            return
        self.queued.add(address)
        self.probe_queue.append(address)

    def _next_queued(self) -> int:
        address = self.probe_queue.pop(0)
        self.queued.discard(address)
        return address

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def _strike(self, obs: ObservationV2) -> AgentAction:
        address = self.strike_queue.pop(0)
        if not self.strike_queue:
            self.burst_completed_tick = obs.current_tick
        if not self._within_reach(obs, address):
            return self._move_toward(obs, address)
        self.written.add(address)
        return AgentAction(kind=ActionKindV2.WRITE, operand=address, value=STRIKE_BYTE)

    def _probe(self, obs: ObservationV2, address: int) -> AgentAction:
        if not self._within_reach(obs, address):
            return self._move_toward(obs, address)
        self.pending_read[obs.self_process_id] = address
        return AgentAction(kind=ActionKindV2.READ, operand=address)

    def _search(self, obs: ObservationV2) -> AgentAction:
        """Stride-``core_size`` READ sweep, expanding outward from the bearing.

        A core is ``core_size`` contiguous cells, so sampling every
        ``core_size``-th address lands inside one after at most
        ``arena_size / core_size`` reads -- it cannot be stepped over. The
        order (centre, +stride, -stride, +2*stride, ...) means the cheapest
        reads are spent nearest the only bearing we have, while the guarantee
        still covers the whole arena if that bearing was wrong.
        """
        stride = max(1, obs.own_core_size)
        centre = self.search_centre
        if centre is None:
            centre = (obs.own_core_base + self.search_jitter) % self.arena
        limit = self.arena // stride + 2

        while self.search_cursor < limit * 2:
            index = self.search_cursor
            self.search_cursor += 1
            rung = (index + 1) // 2
            sign = 1 if index % 2 == 0 else -1
            address = (centre + sign * rung * stride) % self.arena
            if address not in self.owner_of:
                return self._probe(obs, address)

        self.search_exhausted = True
        return self._claim(obs)

    def _guard(self, obs: ObservationV2) -> AgentAction:
        """Reassert ownership of our own core, as late in the tick as possible.

        Elimination needs *all eight* cells foreign at the end of a tick, so a
        refresh landing after the opponent's last write of that cell is worth
        an entire life. Blind refresh rather than READ-then-repair: a WRITE
        makes ownership true where a READ only reports it, and at this point
        in the cascade there is no budget left to do both.
        """
        size = max(1, obs.own_core_size)
        address = (obs.own_core_base + self.guard_cursor % size) % self.arena
        self.guard_cursor += 1
        if not self._within_reach(obs, address):
            return self._move_toward(obs, address)
        self.written.add(address)
        return AgentAction(kind=ActionKindV2.WRITE, operand=address, value=REPAIR_BYTE)

    def _claim(self, obs: ObservationV2) -> AgentAction:
        """Spare-action territory claim -- the score-fallback tiebreaker."""
        if not self.claim_territory:
            return self._guard(obs)
        address = (obs.own_core_base + self.claim_cursor * self.claim_stride) % self.arena
        self.claim_cursor += 1
        if not self._within_reach(obs, address):
            return self._guard(obs)
        self.written.add(address)
        return AgentAction(kind=ActionKindV2.WRITE, operand=address, value=CLAIM_BYTE)

    def _disperse(self, obs: ObservationV2) -> AgentAction | None:
        """Move off a shared address so one enemy write cannot silence us.

        Every process starts co-located at our own core base, which is both
        the address an opponent is most likely to write and the one place
        where an attack on our core doubles as a disruption of the whole
        roster. Dispersal is lazy -- it costs an action, so it is only spent
        while this process still shares its address with a sibling.
        """
        if self.disperse_span <= 0 or self.process_count <= 1:
            return None

        pid = obs.self_process_id
        target = self.disperse_target.get(pid)
        if target is None:
            index = int(pid[1:]) if pid[1:].isdigit() else 0
            size = max(1, obs.own_core_size)
            sign = -1 if index % 2 else 1
            step = size + 1 + (index // 2) * max(1, self.disperse_span // 2)
            target = (obs.own_core_base + sign * step) % self.arena
            self.disperse_target[pid] = target

        if obs.self_anchor == target:
            return None
        shared = any(
            other_pid != pid and other_anchor == obs.self_anchor
            for other_pid, other_anchor in sorted(self.anchors.items())
        )
        if not shared and obs.current_tick > 1:
            return None
        return self._move_toward(obs, target)

    def _is_last_mover(self, tick: int) -> bool:
        """Whether this entrant takes the final chunk of ``tick``.

        Ruleset v4 schedules entrants in K=2 chunks with the starting seat
        rotating by tick against immutable original seat order: the order for
        a tick is ``states[offset:] + states[:offset]`` with
        ``offset = (tick - 1) % n``, so the last entrant to act is the one at
        index ``(offset - 1) % n`` -- that is, ``(tick - 2) % n``.

        This matters because the capture check runs at the end of the tick.
        Writes made in the final chunk are the only ones an opponent has no
        remaining action to answer, so a burst launched on any other tick is
        one the defender is still entitled to undo.
        """
        count = max(2, self.entrant_count)
        return (tick - 2) % count == self.seat_index % count

    def _suppress(self, obs: ObservationV2) -> AgentAction | None:
        """Write a live enemy anchor we have not already hit this tick."""
        if self.target_base is None:
            return None
        pending = [
            address
            for address in obs.visible_enemy_anchor_addresses
            if address not in self.suppressed_this_tick
        ]
        if not pending:
            return None
        address = min(pending, key=lambda a: (self._distance(a, obs.self_anchor), a))
        if not self._within_reach(obs, address):
            return None
        self.suppressed_this_tick.add(address)
        self.written.add(address)
        return AgentAction(kind=ActionKindV2.WRITE, operand=address, value=STRIKE_BYTE)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _guard_budget(self, obs: ObservationV2) -> int:
        budget = self.guard_actions
        if obs.current_tick <= self.under_pressure_until:
            budget += 1
        return min(self.quota, budget)

    def _core_distance(self, base: int, size: int, address: int) -> int:
        offset = (address - base) % self.arena
        if offset < size:
            return 0
        return min(offset - size + 1, (base - address) % self.arena)

    def _legal_reach(self, desired: int) -> int:
        return max(1, min(desired, self.arena - 1))

    def _within_reach(self, obs: ObservationV2, address: int) -> bool:
        return self._distance(obs.self_anchor, address % self.arena) <= obs.self_reach

    def _distance(self, a: int, b: int) -> int:
        delta = abs((a - b) % self.arena)
        return min(delta, self.arena - delta)

    def _shortest_delta(self, target: int, anchor: int) -> int:
        forward = (target - anchor) % self.arena
        backward = forward - self.arena
        return backward if abs(backward) < abs(forward) else forward

    def _move_toward(self, obs: ObservationV2, target: int) -> AgentAction:
        delta = self._shortest_delta(target % self.arena, obs.self_anchor)
        return AgentAction(kind=ActionKindV2.MOVE, operand=max(-64, min(64, delta)))

    @staticmethod
    def _coprime_stride(arena_size: int, preferred: int) -> int:
        for candidate in range(preferred, 0, -1):
            if gcd(candidate, arena_size) == 1:
                return candidate
        return 1


def create_agent() -> OctaveAgent:
    return OctaveAgent()
