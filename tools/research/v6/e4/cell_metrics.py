"""Replay-derived E4 per-cell metrics: FMA and FPS (design review Sec M.2).

Reads one canonical replay -- never writes it and needs no new replay field --
together with that cell's E3 telemetry (``action_parity.analyze_actions``,
which carries capture analyzer v2's telemetry), and derives:

* **FMA, first-mover core advantage.** ``b(t)`` is Seat A's own-core cells
  minus Seat B's at the end of tick ``t``, rebuilt from the replay's
  ownership. Over ticks at whose end both entrants are alive,
  ``FMA = 1/2 (mean of b over A-first ticks - mean of b over B-first ticks)``,
  in cells, in ``[-8, 8]``, positive when each entrant does better on the
  ticks it moves first. It is computed exactly (a rational) and needs no
  swing, so a static cell has a defined FMA. With fewer than 10 both-alive
  ticks of either parity the cell is ``DECIDED_EARLY`` -- counted, never
  dropped.
* **FPS, final-chunk-owner share.** The share of swing ticks (PM-1's
  definition) whose balance change favours the entrant owning that tick's
  final chunk. Ownership is read from the Ruleset registry: the replay's
  Ruleset policy runs its own scheduler for the tick with both entrants live,
  and the last offer's entrant is the owner. Scored only with at least 10
  swing ticks, like FMS. Under the forward order FPS = 1 - FMS and under the
  mirrored order FPS = FMS; both identities are checked per cell.

The per-tick ownership is not exposed by the reused analyzers, so it is
rebuilt here with capture analyzer v2's own address helper and then
cross-checked against both: the swing count, the first-mover-favouring
swings and the both-alive tick count must equal E3 PM-1's, and each entrant's
final owned count and zero-core evaluations (split by who moved first) must
equal capture analyzer v2's. Any difference is reported as a reconstruction
disagreement, never smoothed over. Neither reused analyzer is copied or
modified.
"""

from __future__ import annotations

from collections.abc import Mapping
from fractions import Fraction
from pathlib import Path
from typing import Any

from battle_engine.replay import ReplayHeader, RuntimeEvent, TickSnapshot, iter_replay
from battle_engine.ruleset_policy import RulesetPolicy, resolve_ruleset_policy

from tools.research.v6.e2.capture_analyzer import _addresses, first_mover_seat
from tools.research.v6.e3.action_parity import MIN_SCOREABLE_SWINGS, NOT_SCOREABLE

E4_CELL_METRICS_VERSION = 1

# Sec M.2: FMA needs at least this many both-alive ticks of each parity.
MIN_TICKS_PER_PARITY = 10
DEFINED = "DEFINED"
DECIDED_EARLY = "DECIDED_EARLY"
SCORED = "SCORED"

# Sec M.2 bands, fixed a priori from the integer resolution of core ownership.
STRONG_FIRST = "strong-first"
MODERATE_FIRST = "moderate-first"
NEUTRAL = "neutral"
MODERATE_LAST = "moderate-last"
STRONG_LAST = "strong-last"
BANDS: tuple[str, ...] = (STRONG_FIRST, MODERATE_FIRST, NEUTRAL, MODERATE_LAST, STRONG_LAST)
BAND_STRONG = Fraction(3, 2)
BAND_MODERATE = Fraction(1, 2)
FIRST_SIDE = "first"
LAST_SIDE = "last"


def fma_band(value: Fraction) -> str:
    """Sec M.2: strong-first FMA >= 1.5; moderate-first 0.5 <= FMA < 1.5;
    neutral |FMA| < 0.5; moderate-last -1.5 < FMA <= -0.5; strong-last FMA <= -1.5."""
    if value >= BAND_STRONG:
        return STRONG_FIRST
    if value >= BAND_MODERATE:
        return MODERATE_FIRST
    if value > -BAND_MODERATE:
        return NEUTRAL
    if value > -BAND_STRONG:
        return MODERATE_LAST
    return STRONG_LAST


def band_side(band: str) -> str | None:
    """``first`` / ``last`` for a non-neutral band, ``None`` for neutral."""
    if band in (STRONG_FIRST, MODERATE_FIRST):
        return FIRST_SIDE
    if band in (STRONG_LAST, MODERATE_LAST):
        return LAST_SIDE
    return None


def band_strength(band: str) -> int:
    """0 neutral, 1 moderate, 2 strong."""
    return 2 if band in (STRONG_FIRST, STRONG_LAST) else 1 if band in (MODERATE_FIRST, MODERATE_LAST) else 0


def exact_text(value: Fraction) -> str:
    return f"{value.numerator}/{value.denominator}"


def parse_exact(text: str) -> Fraction:
    numerator, denominator = text.split("/")
    return Fraction(int(numerator), int(denominator))


class _Seat:
    def __init__(self, index: int) -> None:
        self.index = index
        self.alive = True


def final_chunk_owner(policy: RulesetPolicy, quota: int, tick: int) -> int:
    """Seat index (0 = A) of the entrant owning ``tick``'s final chunk with both
    entrants live, read from the Ruleset's own scheduler (the registry's pass order)."""
    order: list[int] = []
    policy.run_scheduler([_Seat(0), _Seat(1)], quota, lambda state, _slot: order.append(state.index), tick=tick)
    if not order:
        raise ValueError(f"{policy.ruleset_id}: the scheduler offered nothing at tick {tick}")
    return order[-1]


def cell_metrics(replay_path: Path | str, e3: Mapping[str, Any]) -> dict[str, Any]:
    """E4 metrics for one two-entrant replay, cross-checked against its E3 telemetry ``e3``."""
    replay_path = Path(replay_path)
    header: ReplayHeader | None = None
    ticks: list[TickSnapshot] = []
    for record in iter_replay(replay_path):
        if isinstance(record, ReplayHeader):
            header = record
        elif isinstance(record, TickSnapshot):
            ticks.append(record)
    if header is None or not ticks or ticks[0].tick != 0 or header.ruleset_id is None:
        raise ValueError(f"{replay_path}: not a canonical replay (header with ruleset_id and tick 0 required)")
    policy = resolve_ruleset_policy(header.ruleset_id)
    if policy.scheduler_mode != "chunked":
        raise ValueError(f"{replay_path}: unsupported scheduler mode {policy.scheduler_mode!r}")
    arena = header.config.arena_size
    quota = int(header.config.instr_per_tick)
    seats = [agent.agent_id for agent in ticks[0].agents]
    if len(seats) != 2:
        raise ValueError(f"{replay_path}: E4 metrics need exactly two entrants, found {len(seats)}")

    # Cores: the tick-0 seeding diffs, as the contiguous run at each recorded pc.
    owners: dict[int, str | None] = {}
    seeded: dict[str, list[int]] = {}
    for diff in ticks[0].memory_diffs:
        cells = _addresses(diff.address, diff.length, arena)
        for address in cells:
            owners[address] = diff.owner
        if diff.owner in seats:
            seeded.setdefault(diff.owner, []).extend(cells)
    cores: dict[str, list[int]] = {}
    for agent in ticks[0].agents:
        cells = seeded.get(agent.agent_id, [])
        core = _addresses(agent.pc, len(cells), arena) if isinstance(agent.pc, int) else []
        if not cells or set(core) != set(cells) or len(set(cells)) != len(cells):
            raise ValueError(f"{replay_path}: seeded core of {agent.agent_id!r} is not the contiguous run at its pc")
        cores[agent.agent_id] = core

    def owned(seat: str) -> int:
        return sum(1 for address in cores[seat] if owners.get(address) == seat)

    both_alive = [0, 0]  # by first-mover seat index
    balance_sum = [0, 0]
    swings = favouring_first = favouring_final = 0
    final_roles: set[str] = set()
    zero = {seat: {"own_first": 0, "opponent_first": 0} for seat in seats}
    alive_prev = {agent.agent_id: agent.alive for agent in ticks[0].agents}
    balance_prev = owned(seats[0]) - owned(seats[1])
    for snapshot in ticks[1:]:
        tick = snapshot.tick
        first = first_mover_seat(tick, len(seats), policy.scheduler_rotate_start)
        for diff in snapshot.memory_diffs:
            for address in _addresses(diff.address, diff.length, arena):
                owners[address] = diff.owner
        alive = {agent.agent_id: agent.alive for agent in snapshot.agents}
        forfeited = {
            event.victim for event in snapshot.events if isinstance(event, RuntimeEvent) and event.event_type == "forfeit"
        }
        for index, seat in enumerate(seats):
            if alive_prev.get(seat, False) and seat not in forfeited and owned(seat) == 0:
                zero[seat]["own_first" if index == first else "opponent_first"] += 1
        balance = owned(seats[0]) - owned(seats[1])
        if all(alive.get(seat, False) for seat in seats):
            both_alive[first] += 1
            balance_sum[first] += balance
            owner = final_chunk_owner(policy, quota, tick)
            final_roles.add("first" if owner == first else "second")
            change = balance - balance_prev
            if change:
                swings += 1
                if (change > 0) == (first == 0):
                    favouring_first += 1
                if (change > 0) == (owner == 0):
                    favouring_final += 1
        balance_prev = balance
        alive_prev = alive

    if both_alive[0] >= MIN_TICKS_PER_PARITY and both_alive[1] >= MIN_TICKS_PER_PARITY:
        value = Fraction(balance_sum[0] * both_alive[1] - balance_sum[1] * both_alive[0], 2 * both_alive[0] * both_alive[1])
        fma: dict[str, Any] = {"status": DEFINED, "value": round(float(value), 9), "exact": exact_text(value),
                               "band": fma_band(value)}
    else:
        fma = {"status": DECIDED_EARLY, "value": None, "exact": None, "band": None}
    if swings >= MIN_SCOREABLE_SWINGS:
        fps: dict[str, Any] = {"status": SCORED, "value": round(favouring_final / swings, 6)}
    else:
        fps = {"status": NOT_SCOREABLE, "value": None}
    fps.update({"swing_ticks": swings, "final_owner_favoring": favouring_final})

    problems: list[str] = []
    parity = e3["parity"]
    if (parity["swing_ticks"], parity["first_mover_favoring"]) != (swings, favouring_first):
        problems.append(f"swings {(swings, favouring_first)} != E3 PM-1 {(parity['swing_ticks'], parity['first_mover_favoring'])}")
    if e3["both_alive_ticks"] != sum(both_alive):
        problems.append(f"both-alive ticks {sum(both_alive)} != E3 {e3['both_alive_ticks']}")
    for seat in seats:
        capture = e3["seats"][seat]["capture"]
        if capture["final_owned"] != owned(seat):
            problems.append(f"{seat}: final owned {owned(seat)} != capture analyzer v2 {capture['final_owned']}")
        expected = {"own_first": capture["zero_ticks_own_first"], "opponent_first": capture["zero_ticks_opponent_first"]}
        if zero[seat] != expected:
            problems.append(f"{seat}: zero-core evaluations {zero[seat]} != capture analyzer v2 {expected}")
    reconstruction_agrees = not problems
    if len(final_roles) > 1:
        problems.append(f"final-chunk owner role varies across ticks: {sorted(final_roles)}")
    mirrored = policy.scheduler_pass_order == "mirrored"
    expected_role = "first" if mirrored else "second"
    if final_roles and final_roles != {expected_role}:
        problems.append(f"final-chunk owner {sorted(final_roles)} != {expected_role} for pass order {policy.scheduler_pass_order!r}")
    identity = favouring_final == (favouring_first if mirrored else swings - favouring_first)
    if not identity:
        problems.append("FPS identity (forward: 1 - FMS; mirrored: FMS) does not hold")
    return {
        "e4_cell_metrics_version": E4_CELL_METRICS_VERSION,
        "ruleset_id": header.ruleset_id,
        "scheduler_pass_order": policy.scheduler_pass_order,
        "final_chunk_owner_role": min(final_roles) if len(final_roles) == 1 else None,
        "both_alive_ticks_by_first_mover": {seats[0]: both_alive[0], seats[1]: both_alive[1]},
        "balance_sum_by_first_mover": {seats[0]: balance_sum[0], seats[1]: balance_sum[1]},
        "fma": fma,
        "fps": fps,
        "swing_ticks": swings,
        "first_mover_favoring": favouring_first,
        "zero_core_evaluations": zero,
        "checks": {
            "reconstruction_agrees": reconstruction_agrees,
            "fps_identity_holds": identity,
            "problems": problems,
            "ok": not problems,
        },
    }
