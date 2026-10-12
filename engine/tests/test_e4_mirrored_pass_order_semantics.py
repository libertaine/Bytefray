"""V6 E4 mirrored pass order: exact scheduler sequences, the pass-order
properties P1-P6, G.5'/D9' immunity, and named mechanical characterizations.

docs/research/v6/V6_E4_ORDER_VS_EVALUATION_TIMING_DESIGN_REVIEW.md Sec F, J and
L; docs/research/v6/V6_E4_MIRRORED_PASS_ORDER_REGISTRATION.md. Under
``RulesetPolicy.scheduler_pass_order == "mirrored"`` the scheduler walks the
(rotated) entrant sequence in reverse in every pass ``p`` with ``2p >= P``
(``P = ceil(Q / chunk)``); ``"forward"`` is the historical order, proven
byte-identical by ``test_v6_e4_parent_byte_identity.py``. Notation: ``F`` is
the tick's first mover, ``L`` the other entrant.

* **Scheduler sequences** drive ``scheduler.run_chunked_quota`` directly and
  assert every offered (entrant, slot) sequence by value -- rotation on and
  off, one to three entrants, chunk 1 to chunk >= Q, dead and forfeiting
  entrants. The forward path is checked against a verbatim copy of the pre-E4
  function over a configuration grid.
* **P1-P5** are checked through each Ruleset's own
  ``RulesetPolicy.run_scheduler`` (the wiring), and the scheduled order
  through a directly constructed ``ProcessMatchController`` (the runtime).
* **P6 / G.4'** is proven by exhaustive enumeration of every jam in one
  tick, with the victim in each scheduler position.
* **G.5' / D9'** plays K=2 guards against adversarial jammers, including a
  guard that satisfies only the theorem's premise.
* **Mechanic characterizations** run the tracked E2/E3 research fixtures end
  to end at seed 42 (outside matrix seeds 1-32) under the historical T-E3
  parent and the E4 primary treatment, and assert named traces from the
  canonical replay alone. They pin *mechanics* (review Sec L) -- never a
  rate, a balance outcome or an E4 conclusion.
"""

from __future__ import annotations

import itertools
import math
import random
from collections import Counter
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest
from battle_engine.agent_api import ActionKindV2, AgentAction, ObservationV2
from battle_engine.agents import resolve_agent
from battle_engine.config import Config
from battle_engine.match_service import MatchEntrant, MatchRequest, NativeMatchService
from battle_engine.placement import resolve_direct_match_starts
from battle_engine.process_runtime import (
    ProcessEntrantSpec,
    ProcessInstance,
    ProcessMatchController,
    ProcessRole,
)
from battle_engine.replay import KillDeathEvent, TickSnapshot, iter_replay
from battle_engine.ruleset_policy import (
    BYTEFRAY_RULESET_V6_RESEARCH_CAPTURE_HOLD_K2_DISRUPTION_SLOT1_ID,
    BYTEFRAY_RULESET_V6_RESEARCH_CAPTURE_HOLD_K2_DISRUPTION_SLOT1_MIRRORED_PASSES_ID,
    BYTEFRAY_RULESET_V6_RESEARCH_DISRUPTION_SLOT1_ID,
    BYTEFRAY_RULESET_V6_RESEARCH_DISRUPTION_SLOT1_MIRRORED_PASSES_ID,
    RULESET_V6_RESEARCH_CAPTURE_HOLD_K2_DISRUPTION_SLOT1,
    RULESET_V6_RESEARCH_CAPTURE_HOLD_K2_DISRUPTION_SLOT1_MIRRORED_PASSES,
    RULESET_V6_RESEARCH_DISRUPTION_SLOT1,
    RULESET_V6_RESEARCH_DISRUPTION_SLOT1_MIRRORED_PASSES,
    RulesetPolicy,
)
from battle_engine.scheduler import run_chunked_quota

from tools.research.v6.e3.entrants import prepare_data_root

PRIMARY = RULESET_V6_RESEARCH_CAPTURE_HOLD_K2_DISRUPTION_SLOT1_MIRRORED_PASSES
COMPANION = RULESET_V6_RESEARCH_DISRUPTION_SLOT1_MIRRORED_PASSES
T_E3 = RULESET_V6_RESEARCH_CAPTURE_HOLD_K2_DISRUPTION_SLOT1
T_E3K1 = RULESET_V6_RESEARCH_DISRUPTION_SLOT1
TREATMENTS = (PRIMARY, COMPANION)
PARENT = {PRIMARY: T_E3, COMPANION: T_E3K1}

QUOTA = 8
OFFERS = tuple(range(QUOTA))


def _policy_id(policy: RulesetPolicy) -> str:
    return policy.ruleset_id


def test_policies_under_test() -> None:
    for treatment, parent in PARENT.items():
        assert (parent.scheduler_pass_order, treatment.scheduler_pass_order) == ("forward", "mirrored")
        for policy in (treatment, parent):
            assert (policy.scheduler_mode, policy.scheduler_chunk_size, policy.scheduler_rotate_start) == (
                "chunked",
                2,
                True,
            )
            assert policy.disruption_slot_limit == 1
    assert (PRIMARY.capture_hold_ticks, COMPANION.capture_hold_ticks) == (2, 1)


# ---------------------------------------------------------------------------
# Scheduler: exact offer sequences
# ---------------------------------------------------------------------------


@dataclass
class _Entrant:
    name: str
    alive: bool = True


Offer = tuple[str, int]


def _historical_run_chunked_quota(
    states: Iterable[_Entrant],
    quota: int,
    execute_slot: Callable[[_Entrant, int], None],
    *,
    chunk_size: int = 1,
    rotate_start: bool = False,
    tick: int = 1,
) -> None:
    """``scheduler.run_chunked_quota`` exactly as it was before E4 (``b144e1d``).

    The forward-path oracle: every ``"forward"`` Ruleset must still schedule
    exactly this.
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
        for state in state_order:
            if not state.alive:
                continue
            for slot in range(start_slot, end_slot):
                if not state.alive:
                    break
                execute_slot(state, slot)


def _offers(
    names: str,
    *,
    quota: int = QUOTA,
    chunk: int = 2,
    rotate: bool = True,
    tick: int = 1,
    mirror: bool | None = False,
    dead: str = "",
    forfeit: Iterable[Offer] = (),
    scheduler: Callable[..., None] = run_chunked_quota,
) -> list[Offer]:
    """Every (entrant, slot) offer of one tick, in order.

    ``mirror=None`` omits the keyword entirely (the historical call). An
    entrant in ``forfeit`` dies during that offer, after acting -- the
    runtime's mid-tick forfeit.
    """

    states = [_Entrant(name, name not in dead) for name in names]
    dies = set(forfeit)
    calls: list[Offer] = []

    def execute(state: _Entrant, slot: int) -> None:
        calls.append((state.name, slot))
        if (state.name, slot) in dies:
            state.alive = False

    kwargs: dict[str, Any] = {"chunk_size": chunk, "rotate_start": rotate, "tick": tick}
    if mirror is not None:
        kwargs["mirror_second_half"] = mirror
    scheduler(states, quota, execute, **kwargs)
    return calls


def _seq(text: str) -> list[Offer]:
    return [(token[0], int(token[1:])) for token in text.split()]


def _roles(offers: Sequence[Offer], first: str) -> str:
    return "".join("F" if name == first else "L" for name, _ in offers)


# Two entrants, Q = 8, chunk 2, rotation on. Ticks 3 and 4 repeat ticks 1 and 2.
FORWARD = {
    1: "A0 A1 B0 B1 A2 A3 B2 B3 A4 A5 B4 B5 A6 A7 B6 B7",
    2: "B0 B1 A0 A1 B2 B3 A2 A3 B4 B5 A4 A5 B6 B7 A6 A7",
}
MIRRORED = {
    1: "A0 A1 B0 B1 A2 A3 B2 B3 B4 B5 A4 A5 B6 B7 A6 A7",
    2: "B0 B1 A0 A1 B2 B3 A2 A3 A4 A5 B4 B5 A6 A7 B6 B7",
}
FORWARD_ROLES = "FFLLFFLLFFLLFFLL"
MIRRORED_ROLES = "FFLLFFLLLLFFLLFF"  # F L F L | L F L F by chunk


def _parity(tick: int) -> int:
    return 1 if tick % 2 else 2


@pytest.mark.parametrize("tick", [1, 2, 3, 4])
def test_two_entrants_with_rotation_exact_offer_sequences(tick: int) -> None:
    first = "AB"[(tick - 1) % 2]
    forward = _offers("AB", tick=tick)
    mirrored = _offers("AB", tick=tick, mirror=True)
    assert forward == _seq(FORWARD[_parity(tick)])
    assert mirrored == _seq(MIRRORED[_parity(tick)])
    assert _roles(forward, first) == FORWARD_ROLES
    assert _roles(mirrored, first) == MIRRORED_ROLES


@pytest.mark.parametrize("tick", [1, 2, 3, 4])
def test_two_entrants_without_rotation_keep_seat_a_first_every_tick(tick: int) -> None:
    assert _offers("AB", tick=tick, rotate=False) == _seq(FORWARD[1])
    mirrored = _offers("AB", tick=tick, rotate=False, mirror=True)
    assert mirrored == _seq(MIRRORED[1])
    # Without rotation Seat A opens *and* closes every mirrored tick: the final
    # chunk would sit on one seat for the whole match, which is why the E4
    # Rulesets keep rotation (review Sec F).
    assert mirrored[:2] == [("A", 0), ("A", 1)]
    assert mirrored[-2:] == [("A", 6), ("A", 7)]


@pytest.mark.parametrize("chunk", [1, 2, 3, 8, 10])
@pytest.mark.parametrize("tick", [1, 2, 3])
def test_a_single_entrant_is_unaffected_by_mirroring(chunk: int, tick: int) -> None:
    expected = [("A", slot) for slot in OFFERS]
    for rotate in (True, False):
        assert _offers("A", chunk=chunk, tick=tick, rotate=rotate) == expected
        assert _offers("A", chunk=chunk, tick=tick, rotate=rotate, mirror=True) == expected


FORWARD_3 = {
    1: "A0 A1 B0 B1 C0 C1 A2 A3 B2 B3 C2 C3 A4 A5 B4 B5 C4 C5 A6 A7 B6 B7 C6 C7",
    2: "B0 B1 C0 C1 A0 A1 B2 B3 C2 C3 A2 A3 B4 B5 C4 C5 A4 A5 B6 B7 C6 C7 A6 A7",
    3: "C0 C1 A0 A1 B0 B1 C2 C3 A2 A3 B2 B3 C4 C5 A4 A5 B4 B5 C6 C7 A6 A7 B6 B7",
}
MIRRORED_3 = {
    1: "A0 A1 B0 B1 C0 C1 A2 A3 B2 B3 C2 C3 C4 C5 B4 B5 A4 A5 C6 C7 B6 B7 A6 A7",
    2: "B0 B1 C0 C1 A0 A1 B2 B3 C2 C3 A2 A3 A4 A5 C4 C5 B4 B5 A6 A7 C6 C7 B6 B7",
    3: "C0 C1 A0 A1 B0 B1 C2 C3 A2 A3 B2 B3 B4 B5 A4 A5 C4 C5 B6 B7 A6 A7 C6 C7",
}


@pytest.mark.parametrize("tick", [1, 2, 3, 4])
def test_three_entrants_reverse_the_whole_rotated_order(tick: int) -> None:
    # With two entrants, reversing the rotated order equals rotating it by one
    # more; only three or more entrants tell a reversal from a rotation.
    phase = (tick - 1) % 3 + 1
    first = "ABC"[(tick - 1) % 3]
    assert _offers("ABC", tick=tick) == _seq(FORWARD_3[phase])
    mirrored = _offers("ABC", tick=tick, mirror=True)
    assert mirrored == _seq(MIRRORED_3[phase])
    # The first mover opens the tick and owns its final chunk.
    assert mirrored[0][0] == first == mirrored[-1][0]


@pytest.mark.parametrize("tick", [1, 2, 3])
def test_three_entrants_without_rotation(tick: int) -> None:
    assert _offers("ABC", tick=tick, rotate=False) == _seq(FORWARD_3[1])
    assert _offers("ABC", tick=tick, rotate=False, mirror=True) == _seq(MIRRORED_3[1])


def test_chunk_one_mirrors_the_second_half_of_eight_single_offer_passes() -> None:
    assert _offers("AB", chunk=1) == _seq("A0 B0 A1 B1 A2 B2 A3 B3 A4 B4 A5 B5 A6 B6 A7 B7")
    assert _offers("AB", chunk=1, mirror=True) == _seq("A0 B0 A1 B1 A2 B2 A3 B3 B4 A4 B5 A5 B6 A6 B7 A7")
    assert _offers("AB", chunk=1, tick=2, mirror=True) == _seq(
        "B0 A0 B1 A1 B2 A2 B3 A3 A4 B4 A5 B5 A6 B6 A7 B7"
    )


@pytest.mark.parametrize("chunk", [8, 10])
def test_a_single_pass_has_no_second_half_to_mirror(chunk: int) -> None:
    for tick, text in (
        (1, "A0 A1 A2 A3 A4 A5 A6 A7 B0 B1 B2 B3 B4 B5 B6 B7"),
        (2, "B0 B1 B2 B3 B4 B5 B6 B7 A0 A1 A2 A3 A4 A5 A6 A7"),
    ):
        assert _offers("AB", chunk=chunk, tick=tick, mirror=True) == _offers("AB", chunk=chunk, tick=tick)
        assert _offers("AB", chunk=chunk, tick=tick, mirror=True) == _seq(text)


def test_odd_pass_counts_and_partial_chunks() -> None:
    # Chunk 3, Q 8: P = 3 passes (slots 0-2, 3-5, 6-7); 2p >= 3 holds only for
    # p = 2, so an odd pass count reverses the later floor(P / 2) passes.
    assert _offers("AB", chunk=3, mirror=True) == _seq("A0 A1 A2 B0 B1 B2 A3 A4 A5 B3 B4 B5 B6 B7 A6 A7")
    # Q 7, chunk 2: P = 4 passes, the last holding a single slot.
    assert _offers("AB", quota=7, mirror=True) == _seq("A0 A1 B0 B1 A2 A3 B2 B3 B4 B5 A4 A5 B6 A6")


def test_dead_entrants_are_skipped_in_every_pass() -> None:
    assert _offers("AB", dead="B", mirror=True) == _seq("A0 A1 A2 A3 A4 A5 A6 A7")
    assert _offers("AB", dead="A", mirror=True) == _seq("B0 B1 B2 B3 B4 B5 B6 B7")
    assert _offers("AB", dead="AB", mirror=True) == []
    assert _offers("ABC", dead="B", mirror=True) == _seq("A0 A1 C0 C1 A2 A3 C2 C3 C4 C5 A4 A5 C6 C7 A6 A7")
    # Rotation still counts a dead entrant's seat: tick 2 starts from B, so C opens.
    assert _offers("ABC", dead="B", tick=2, mirror=True) == _seq(
        "C0 C1 A0 A1 C2 C3 A2 A3 A4 A5 C4 C5 A6 A7 C6 C7"
    )


def test_a_forfeiting_entrant_receives_no_further_offer() -> None:
    # B forfeits during B4 -- its first offer of the reversed third pass --
    # so B5 is never offered and B is skipped for the rest of the tick.
    assert _offers("AB", mirror=True, forfeit=[("B", 4)]) == _seq("A0 A1 B0 B1 A2 A3 B2 B3 B4 A4 A5 A6 A7")
    assert _offers("AB", mirror=True, forfeit=[("B", 5)]) == _seq("A0 A1 B0 B1 A2 A3 B2 B3 B4 B5 A4 A5 A6 A7")
    assert _offers("AB", forfeit=[("B", 4)]) == _seq("A0 A1 B0 B1 A2 A3 B2 B3 A4 A5 B4 A6 A7")
    assert _offers("AB", mirror=True, forfeit=[("A", 0)]) == _seq("A0 B0 B1 B2 B3 B4 B5 B6 B7")
    assert _offers("ABC", mirror=True, forfeit=[("C", 4)]) == _seq(
        "A0 A1 B0 B1 C0 C1 A2 A3 B2 B3 C2 C3 C4 B4 B5 A4 A5 B6 B7 A6 A7"
    )


def test_no_offers_without_entrants_or_quota() -> None:
    assert _offers("", mirror=True) == []
    assert _offers("AB", quota=0, mirror=True) == []


GRID = [
    {"names": names, "quota": quota, "chunk": chunk, "rotate": rotate, "tick": tick, "dead": dead, "forfeit": forfeit}
    for names in ("A", "AB", "ABC", "ABCD")
    for quota in (0, 1, 7, 8, 9)
    for chunk in (0, 1, 2, 3, 8, 10)
    for rotate in (True, False)
    for tick in (1, 2, 3, 4, 5)
    for dead, forfeit in (("", ()), (names[-1], ()), ("", ((names[0], 3),)))
]


def test_forward_is_exactly_the_historical_scheduler() -> None:
    # Omitting the flag and passing False both schedule exactly what the
    # pre-E4 function did, for every configuration in the grid.
    for config in GRID:
        historical = _offers(**config, mirror=None, scheduler=_historical_run_chunked_quota)
        assert _offers(**config, mirror=None) == historical, config
        assert _offers(**config, mirror=False) == historical, config


def test_mirroring_only_reorders_the_later_passes() -> None:
    for config in GRID:
        forward = _offers(**config)
        mirrored = _offers(**config, mirror=True)
        # The same offers: each entrant keeps its own slots, in the same order.
        assert Counter(mirrored) == Counter(forward), config
        for name in config["names"]:
            own = [slot for entrant, slot in mirrored if entrant == name]
            assert own == [slot for entrant, slot in forward if entrant == name], config
            assert own == sorted(own), config
        # The first ceil(P / 2) passes are unchanged, so is the first mover.
        chunk = max(1, config["chunk"])
        passes = math.ceil(config["quota"] / chunk)
        boundary = math.ceil(passes / 2) * chunk
        prefix = [offer for offer in forward if offer[1] < boundary]
        assert mirrored[: len(prefix)] == prefix == forward[: len(prefix)], config


# ---------------------------------------------------------------------------
# P1-P5 through each Ruleset's own run_scheduler
# ---------------------------------------------------------------------------


def _policy_offers(policy: RulesetPolicy, tick: int, names: str = "AB") -> list[Offer]:
    states = [_Entrant(name) for name in names]
    calls: list[Offer] = []
    policy.run_scheduler(states, QUOTA, lambda state, slot: calls.append((state.name, slot)), tick=tick)
    return calls


@pytest.mark.parametrize("policy", TREATMENTS, ids=_policy_id)
def test_each_e4_ruleset_schedules_mirrored_and_its_parent_forward(policy: RulesetPolicy) -> None:
    for tick in range(1, 5):
        assert _policy_offers(policy, tick) == _seq(MIRRORED[_parity(tick)])
        assert _policy_offers(PARENT[policy], tick) == _seq(FORWARD[_parity(tick)])


@pytest.mark.parametrize("policy", TREATMENTS, ids=_policy_id)
def test_p1_opportunity_every_live_entrant_gets_eight_offers_in_slot_order(policy: RulesetPolicy) -> None:
    for tick in range(1, 9):
        offers = _policy_offers(policy, tick)
        for name in "AB":
            assert [slot for entrant, slot in offers if entrant == name] == list(OFFERS)


@pytest.mark.parametrize("policy", TREATMENTS, ids=_policy_id)
def test_p2_rotation_the_first_mover_is_seat_tick_minus_one_mod_two(policy: RulesetPolicy) -> None:
    for tick in range(1, 9):
        first = "AB"[(tick - 1) % 2]
        assert _policy_offers(policy, tick)[0][0] == first
        assert _policy_offers(PARENT[policy], tick)[0][0] == first


@pytest.mark.parametrize("policy", TREATMENTS, ids=_policy_id)
def test_p3_the_first_mover_owns_the_final_chunk_only_under_the_treatment(policy: RulesetPolicy) -> None:
    for tick in range(1, 9):
        first, second = ("A", "B") if tick % 2 else ("B", "A")
        assert _policy_offers(policy, tick)[-2:] == [(first, 6), (first, 7)]
        assert _policy_offers(PARENT[policy], tick)[-2:] == [(second, 6), (second, 7)]


def _response_profile(offers: Sequence[Offer], first: str) -> tuple[str, ...]:
    """Per pass (four offers), which role acts second in it."""

    return tuple("F" if offers[4 * p + 2][0] == first else "L" for p in range(len(offers) // 4))


@pytest.mark.parametrize("policy", TREATMENTS, ids=_policy_id)
def test_p4_response_balance(policy: RulesetPolicy) -> None:
    for tick in range(1, 9):
        first = "AB"[(tick - 1) % 2]
        assert _response_profile(_policy_offers(policy, tick), first) == ("L", "L", "F", "F")
        assert _response_profile(_policy_offers(PARENT[policy], tick), first) == ("L", "L", "L", "L")


def _stream(policy: RulesetPolicy, ticks: int) -> list[str]:
    return [name for tick in range(1, ticks + 1) for name, _ in _policy_offers(policy, tick)]


def _runs_starting_in(stream: Sequence[str], start: int, stop: int) -> Counter[int]:
    """Lengths of the maximal same-entrant runs that start in ``stream[start:stop]``."""

    lengths: Counter[int] = Counter()
    index = 0
    while index < len(stream):
        end = index
        while end + 1 < len(stream) and stream[end + 1] == stream[index]:
            end += 1
        if start <= index < stop:
            lengths[end - index + 1] += 1
        index = end + 1
    return lengths


@pytest.mark.parametrize("policy", TREATMENTS, ids=_policy_id)
def test_p5_the_mirrored_stream_is_the_stock_stream_shifted_by_four_chunks(policy: RulesetPolicy) -> None:
    """A characterization of the manipulation, not a claim of gameplay
    equivalence: the tick boundary -- the evaluation instant, the per-tick
    quota reset and every tick-scoped rule -- moves with the shift (review
    Sec E.1)."""

    ticks = 12
    per_tick = 2 * QUOTA
    stock = _stream(PARENT[policy], ticks)
    mirrored = _stream(policy, ticks)
    # Same total actions and the same per-entrant quota in every tick.
    for stream in (stock, mirrored):
        assert len(stream) == ticks * per_tick
        for tick in range(ticks):
            assert Counter(stream[tick * per_tick : (tick + 1) * per_tick]) == {"A": QUOTA, "B": QUOTA}
    # The interior of the mirrored stream is the stock stream shifted by four
    # chunks (eight actions) -- and by no other shift within a two-tick period.
    shift = 4 * 2
    assert mirrored[: len(mirrored) - shift] == stock[shift:]
    window = len(mirrored) - 2 * per_tick
    assert [s for s in range(2 * per_tick) if mirrored[:window] == stock[s : s + window]] == [shift]
    assert mirrored != stock
    # Same run structure and alternation count in every interior tick: one
    # 4-action run and six 2-action runs start in each tick (the stock one
    # straddles the tick boundary, the mirrored one sits mid-tick), and the
    # entrant changes 7 times from each tick's actions to the next action.
    for stream in (stock, mirrored):
        for tick in range(1, ticks - 1):
            start, stop = tick * per_tick, (tick + 1) * per_tick
            assert _runs_starting_in(stream, start, stop) == {2: 6, 4: 1}
            assert sum(stream[i] != stream[i + 1] for i in range(start, stop)) == 7


# ---------------------------------------------------------------------------
# Runtime harness: scripted entrants on a directly constructed controller
# ---------------------------------------------------------------------------

ARENA = 512
CORE = {"A": 100, "B": 300}
J_ANCHOR = 40
V_ANCHOR = 440


def _w(address: int) -> AgentAction:
    return AgentAction(ActionKindV2.WRITE, operand=address % ARENA, value=1)


_IDLE = AgentAction(ActionKindV2.READ, operand=0)


@dataclass(frozen=True)
class Proc:
    pid: str
    anchor: int
    share: int
    reach: int = ARENA // 2


Brain = Callable[[ProcessMatchController, ObservationV2, int, str], AgentAction]


def _scripted(script: Mapping[tuple[int, int], AgentAction]) -> Brain:
    def brain(_c: ProcessMatchController, obs: ObservationV2, slot: int, _pid: str) -> AgentAction:
        return script.get((obs.current_tick, slot), _IDLE)

    return brain


def _hits(*offers: tuple[int, int], target: int = V_ANCHOR) -> Brain:
    return _scripted({offer: _w(target) for offer in offers})


@dataclass(frozen=True)
class Call:
    tick: int
    seat: str
    slot: int
    process: str
    action: AgentAction


@dataclass(frozen=True)
class TickRecord:
    tick: int
    cpu: dict[str, int]
    disrupted: dict[tuple[str, str], bool]
    owned: dict[str, int]
    streak: dict[str, int]
    alive: dict[str, bool]


class _Recorder:
    """A replay sink that also snapshots live core ownership and capture streaks."""

    def __init__(self, controller: ProcessMatchController) -> None:
        self.controller = controller
        self.ticks: list[TickRecord] = []

    def emit(self, record: dict[str, Any]) -> None:
        if "config" in record or record["tick"] == 0:
            return
        writer = self.controller.vm.writer
        states = self.controller.states
        self.ticks.append(
            TickRecord(
                tick=record["tick"],
                cpu={agent["id"]: agent["cpu_used"] for agent in record["agents"]},
                disrupted={
                    (process["entrant_id"], process["process_id"]): process["disrupted"]
                    for process in record["processes"]
                },
                owned={
                    st.agent_id: sum(1 for cell in st.core_cells if writer[cell] == st.agent_id) for st in states
                },
                streak={st.agent_id: st.core_zero_streak for st in states},
                alive={st.agent_id: st.alive for st in states},
            )
        )

    def close(self) -> None:
        return None


@dataclass(frozen=True)
class Played:
    calls: list[Call]
    ticks: list[TickRecord]
    controller: ProcessMatchController

    def taken_by(self, seat: str, tick: int) -> list[str | None]:
        """Per offer slot: the process that acted, or ``None`` if the offer was forfeited."""

        by_slot = {call.slot: call.process for call in self.calls if (call.tick, call.seat) == (tick, seat)}
        return [by_slot.get(slot) for slot in OFFERS]

    def process(self, seat: str, pid: str) -> ProcessInstance:
        spec = next(spec for spec in self.controller.entrant_specs if spec.agent_id == seat)
        return next(process for process in spec.processes if process.process_id == pid)


def _play(
    processes: Mapping[str, Sequence[Proc]],
    brains: Mapping[str, Brain],
    *,
    policy: RulesetPolicy,
    max_ticks: int = 1,
    cores: Mapping[str, int] = CORE,
) -> Played:
    """Play a scripted match; Seat A moves first on tick 1 (then rotation)."""

    calls: list[Call] = []
    holder: dict[str, ProcessMatchController] = {}

    def executor(seat: str, pid: str) -> Callable[[ObservationV2, int], AgentAction]:
        def run(obs: ObservationV2, slot: int) -> AgentAction:
            action = brains.get(seat, _scripted({}))(holder["controller"], obs, slot, pid)
            calls.append(Call(obs.current_tick, seat, slot, pid, action))
            return action

        return run

    specs = [
        ProcessEntrantSpec(
            agent_id=seat,
            name=f"seat-{seat}",
            processes=[
                ProcessInstance(
                    proc.pid,
                    ProcessRole.GENERALIST,
                    initial_position=proc.anchor,
                    reach=proc.reach,
                    quota_share=proc.share,
                    logic=lambda _obs, _state: _IDLE,
                    executor=executor(seat, proc.pid),
                )
                for proc in processes[seat]
            ],
            start=cores[seat],
        )
        for seat in ("A", "B")
    ]
    controller = ProcessMatchController(
        Config(seed=1, arena_size=ARENA, instr_per_tick=QUOTA), specs, max_ticks, ruleset_policy=policy
    )
    holder["controller"] = controller
    recorder = _Recorder(controller)
    controller.run(recorder)
    return Played(calls, recorder.ticks, controller)


SINGLE = (Proc("p", V_ANCHOR, QUOTA),)
P = "p"
Q = "q"


def _jammer_vs(victim: Sequence[Proc], jammer: Brain, *, policy: RulesetPolicy, max_ticks: int = 1) -> Played:
    """Seat A is a one-process jammer; Seat B is the victim (second mover on tick 1)."""

    return _play({"A": (Proc("j", J_ANCHOR, QUOTA),), "B": victim}, {"A": jammer}, policy=policy, max_ticks=max_ticks)


@pytest.mark.parametrize("policy", [*TREATMENTS, *PARENT.values()], ids=_policy_id)
def test_runtime_offers_follow_the_rulesets_pass_order(policy: RulesetPolicy) -> None:
    # The review's Sec R hard-stop sequence: the controller offers the
    # scheduler's slots to each entrant, and with idle entrants every offer
    # executes, so the scripted calls are the scheduled sequence itself.
    played = _play({"A": (Proc("p", J_ANCHOR, QUOTA),), "B": SINGLE}, {}, policy=policy, max_ticks=4)
    mirrored = policy.scheduler_pass_order == "mirrored"
    for tick in range(1, 5):
        calls = [(call.seat, call.slot) for call in played.calls if call.tick == tick]
        assert calls == _seq((MIRRORED if mirrored else FORWARD)[_parity(tick)])
        assert _roles(calls, "AB"[(tick - 1) % 2]) == (MIRRORED_ROLES if mirrored else FORWARD_ROLES)
    assert [tick.cpu for tick in played.ticks] == [{"A": 8, "B": 8}] * 4


# ---------------------------------------------------------------------------
# Everything outside the scheduler is unchanged
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("policy", TREATMENTS, ids=_policy_id)
def test_the_one_tick_disruption_window_is_unchanged(policy: RulesetPolicy) -> None:
    assert _jammer_vs(SINGLE, _hits(), policy=policy).controller.disruption_duration == 1


@pytest.mark.parametrize("policy", TREATMENTS, ids=_policy_id)
def test_an_opening_pass_hit_suppresses_the_same_offer_as_under_the_parent(policy: RulesetPolicy) -> None:
    for current in (policy, PARENT[policy]):
        played = _jammer_vs(SINGLE, _hits((1, 0)), policy=current)
        assert played.taken_by("B", 1) == [None, P, P, P, P, P, P, P]
        assert played.ticks[0].cpu == {"A": 8, "B": 7}


@pytest.mark.parametrize("policy", TREATMENTS, ids=_policy_id)
def test_a_hit_still_costs_the_victims_next_own_offer_which_the_order_now_places_later(
    policy: RulesetPolicy,
) -> None:
    # A hit at A4. Forward: A4 A5 | B4 B5 -- B4 is the victim's next offer.
    # Mirrored: B4 B5 | A4 A5 | B6 B7 -- the victim already acted in the
    # third pass, so the hit costs B6. The per-offer rule is unchanged.
    parent = _jammer_vs(SINGLE, _hits((1, 4)), policy=PARENT[policy])
    assert parent.taken_by("B", 1) == [P, P, P, P, None, P, P, P]
    treatment = _jammer_vs(SINGLE, _hits((1, 4)), policy=policy)
    assert treatment.taken_by("B", 1) == [P, P, P, P, P, P, None, P]
    assert parent.ticks[0].cpu == treatment.ticks[0].cpu == {"A": 8, "B": 7}


@pytest.mark.parametrize("hit_slot", [6, 7])
@pytest.mark.parametrize("policy", TREATMENTS, ids=_policy_id)
def test_a_hit_after_the_second_movers_final_offer_does_not_carry_into_the_next_tick(
    policy: RulesetPolicy, hit_slot: int
) -> None:
    # Under the mirrored order the first mover's final chunk follows the
    # second mover's: A6/A7 land after B7 on tick 1.
    played = _jammer_vs(SINGLE, _hits((1, hit_slot)), policy=policy, max_ticks=2)
    assert played.taken_by("B", 1) == [P] * 8
    assert played.taken_by("B", 2) == [P] * 8
    assert [tick.disrupted[("B", P)] for tick in played.ticks] == [True, False]
    assert played.process("B", P).disruption_slots_left == 1


@pytest.mark.parametrize("policy", TREATMENTS, ids=_policy_id)
def test_process_round_robin_and_quota_redistribution_are_unchanged(policy: RulesetPolicy) -> None:
    # p (share 6) and q (share 2) at different anchors. Unhit, q stops at its
    # own share of two actions, under either order.
    victim = (Proc(P, V_ANCHOR, 6), Proc(Q, V_ANCHOR + 10, 2))
    for current in (policy, PARENT[policy]):
        assert _jammer_vs(victim, _hits(), policy=current).taken_by("B", 1) == [P, Q, P, Q, P, P, P, P]
    # p is hit at A4, after q has used its share: while p is suppressed the
    # whole quota is redistributed to q, which takes a third action. The hit
    # lands before B4 under the forward order and before B6 under the
    # mirrored order -- the victim's next own offer in each.
    assert _jammer_vs(victim, _hits((1, 4)), policy=PARENT[policy]).taken_by("B", 1) == [P, Q, P, Q, Q, P, P, P]
    assert _jammer_vs(victim, _hits((1, 4)), policy=policy).taken_by("B", 1) == [P, Q, P, Q, P, P, Q, P]


# ---------------------------------------------------------------------------
# P6 / G.4': the action bound, by exhaustive enumeration
# ---------------------------------------------------------------------------
#
# As in E3's G.4 proof: a tick's suppression state never depends on an
# earlier tick, so one tick in each scheduler position covers every tick. The
# victim idles; enumerating every sequence of eight jammer choices from {each
# victim anchor, a harmless action} is every legal jam.

VICTIM_LAYOUTS: dict[str, tuple[Proc, ...]] = {
    "single-process": SINGLE,
    "co-located": (Proc("v0", V_ANCHOR, 4), Proc("v1", V_ANCHOR, 4)),
    "spread": (Proc("v0", V_ANCHOR, 4), Proc("v1", V_ANCHOR + 10, 4)),
}


def _victim_actions(
    policy: RulesetPolicy, victim: Sequence[Proc], jam: Sequence[AgentAction], *, victim_first: bool
) -> int:
    def process(pid: str, anchor: int, share: int, script: Sequence[AgentAction] | None) -> ProcessInstance:
        def act(_obs: ObservationV2, slot: int) -> AgentAction:
            return _IDLE if script is None else script[slot]

        return ProcessInstance(
            pid,
            ProcessRole.GENERALIST,
            initial_position=anchor,
            reach=ARENA // 2,
            quota_share=share,
            logic=lambda _obs, _state: _IDLE,
            executor=act,
        )

    victim_spec = ProcessEntrantSpec(
        agent_id="V",
        name="victim",
        processes=[process(proc.pid, proc.anchor, proc.share, None) for proc in victim],
        start=CORE["B"],
    )
    jammer_spec = ProcessEntrantSpec(
        agent_id="J", name="jammer", processes=[process("j", J_ANCHOR, QUOTA, jam)], start=CORE["A"]
    )
    controller = ProcessMatchController(
        Config(seed=1, arena_size=ARENA, instr_per_tick=QUOTA),
        [victim_spec, jammer_spec] if victim_first else [jammer_spec, victim_spec],
        1,
        ruleset_policy=policy,
    )
    controller.run()
    victim_state = next(state for state in controller.states if state.agent_id == "V")
    assert victim_state.alive
    return victim_state.cpu_used


def _all_jams(victim: Sequence[Proc]) -> list[tuple[AgentAction, ...]]:
    options = [_w(anchor) for anchor in sorted({proc.anchor for proc in victim})] + [_IDLE]
    return list(itertools.product(options, repeat=QUOTA))


@pytest.mark.parametrize("layout", VICTIM_LAYOUTS)
@pytest.mark.parametrize("policy", TREATMENTS, ids=_policy_id)
def test_g4_prime_every_legal_jam_leaves_five_actions_in_both_roles(policy: RulesetPolicy, layout: str) -> None:
    victim = VICTIM_LAYOUTS[layout]
    jams = _all_jams(victim)
    minimum: dict[tuple[str, bool], int] = {}
    for label, current in (("treatment", policy), ("parent", PARENT[policy])):
        for victim_first in (True, False):
            actions = [_victim_actions(current, victim, jam, victim_first=victim_first) for jam in jams]
            # A zero-action live tick is impossible under either order.
            assert 0 not in actions, (label, victim_first)
            minimum[(label, victim_first)] = min(actions)
    # The bound is tight (some jam attains it): 5 in both roles under the
    # mirrored order, while the stock parent keeps (5, 4).
    assert (minimum[("treatment", True)], minimum[("treatment", False)]) == (5, 5)
    assert (minimum[("parent", True)], minimum[("parent", False)]) == (5, 4)


@pytest.mark.parametrize("policy", TREATMENTS, ids=_policy_id)
def test_g4_prime_the_full_jam_attains_the_bound_offer_by_offer(policy: RulesetPolicy) -> None:
    # The jammer writes the victim's anchor with every action. Tick 1 (victim
    # second): B loses B0, B2 and B6, but its contiguous B4 B5 run in the
    # reversed third pass loses nothing. Tick 2 (victim first): B loses B2,
    # B4 and B6 -- the same as under the parent.
    jam = _hits(*((tick, slot) for tick in (1, 2) for slot in OFFERS))
    treatment = _jammer_vs(SINGLE, jam, policy=policy, max_ticks=2)
    assert treatment.taken_by("B", 1) == [None, P, None, P, P, P, None, P]
    assert treatment.taken_by("B", 2) == [P, P, None, P, None, P, None, P]
    assert [tick.cpu["B"] for tick in treatment.ticks] == [5, 5]
    parent = _jammer_vs(SINGLE, jam, policy=PARENT[policy], max_ticks=2)
    assert parent.taken_by("B", 1) == [None, P, None, P, None, P, None, P]
    assert parent.taken_by("B", 2) == [P, P, None, P, None, P, None, P]
    assert [tick.cpu["B"] for tick in parent.ticks] == [4, 5]


@pytest.mark.parametrize("policy", TREATMENTS, ids=_policy_id)
def test_g4_prime_bound_under_natural_rotation(policy: RulesetPolicy) -> None:
    jammer = _hits(*((tick, slot) for tick in range(1, 7) for slot in OFFERS))
    assert [tick.cpu["B"] for tick in _jammer_vs(SINGLE, jammer, policy=policy, max_ticks=6).ticks] == [5] * 6
    assert [tick.cpu["B"] for tick in _jammer_vs(SINGLE, jammer, policy=PARENT[policy], max_ticks=6).ticks] == [
        4,
        5,
    ] * 3


# ---------------------------------------------------------------------------
# G.5' / D9': K = 2 immunity under the mirrored order
# ---------------------------------------------------------------------------
#
# Review Sec J, P7: an entrant whose final executed action on each of its
# *first-mover* ticks writes its own core owns at least one core cell at each
# such evaluation. Under the mirrored order the first mover's final chunk is
# the last of the tick and at most one of its two offers can be suppressed,
# so that final action always happens and nothing acts after it. Its zero
# evaluations can therefore fall only on its second-mover ticks, which are
# never consecutive, so with K = 2 it is never captured. (Under the stock
# order the protected ticks are the second-mover ticks instead: E3's G.5.)

G_CORE = CORE["B"]
G_CELLS = tuple(G_CORE + offset for offset in range(8))
G5_TICKS = 24


def _repair_guard() -> Brain:
    cursor = {"next": 0}

    def brain(_c: ProcessMatchController, _obs: ObservationV2, _slot: int, _pid: str) -> AgentAction:
        target = G_CELLS[cursor["next"] % 8]
        cursor["next"] += 1
        return _w(target)

    return brain


def _disrupt_first_guard() -> Brain:
    done: dict[str, Any] = {"tick": None, "targets": set()}

    def brain(_c: ProcessMatchController, obs: ObservationV2, _slot: int, _pid: str) -> AgentAction:
        if done["tick"] != obs.current_tick:
            done["tick"], done["targets"] = obs.current_tick, set()
        for target in (*obs.visible_enemy_anchor_addresses, *G_CELLS):
            if target not in done["targets"]:
                done["targets"].add(target)
                return _w(target)
        return _IDLE

    return brain


GUARDS: dict[str, Callable[[], Brain]] = {
    "repair-guard": _repair_guard,
    "disrupt-first-guard": _disrupt_first_guard,
}


def _greedy_jammer(guard_seat: str) -> Brain:
    """Omniscient: re-disrupt the guard whenever it could act, otherwise erase its core."""

    def brain(c: ProcessMatchController, obs: ObservationV2, _slot: int, _pid: str) -> AgentAction:
        spec = next(spec for spec in c.entrant_specs if spec.agent_id == guard_seat)
        (guard,) = spec.processes
        if not c._is_suppressed(guard, obs.current_tick):
            return _w(G_CORE)
        owned = [cell for cell in G_CELLS if c.vm.writer[cell] == guard_seat]
        return _w(owned[0] if owned else G_CORE)

    return brain


def _eraser(guard_seat: str) -> Brain:
    """Omniscient: erase the guard's owned core cells, anchor last (hitting it also disrupts)."""

    def brain(c: ProcessMatchController, _obs: ObservationV2, _slot: int, _pid: str) -> AgentAction:
        owned = [cell for cell in G_CELLS if c.vm.writer[cell] == guard_seat]
        return _w(owned[-1] if owned else G_CORE)

    return brain


def _chunk_jammer(_guard_seat: str) -> Brain:
    """Disrupt with the first action of every chunk, erase core cells with the second."""

    def brain(_c: ProcessMatchController, obs: ObservationV2, slot: int, _pid: str) -> AgentAction:
        if slot % 2 == 0:
            return _w(G_CORE)
        return _w(G_CELLS[(obs.current_tick + slot) % 8])

    return brain


def _random_jammer(seed: int) -> Brain:
    rng = random.Random(seed)
    options = [_w(cell) for cell in G_CELLS] + [_IDLE]

    def brain(_c: ProcessMatchController, _obs: ObservationV2, _slot: int, _pid: str) -> AgentAction:
        return rng.choice(options)

    return brain


def _g5_jammers(guard_seat: str) -> list[Brain]:
    return [_greedy_jammer(guard_seat), _eraser(guard_seat), _chunk_jammer(guard_seat)] + [
        _random_jammer(seed) for seed in range(20)
    ]


def _guard_match(
    policy: RulesetPolicy, guard: Brain, jammer: Brain, *, guard_first: bool, ticks: int = G5_TICKS
) -> tuple[Played, str]:
    guard_seat = "A" if guard_first else "B"
    jammer_seat = "B" if guard_first else "A"
    played = _play(
        {guard_seat: (Proc("g", G_CORE, QUOTA),), jammer_seat: (Proc("j", J_ANCHOR, QUOTA),)},
        {guard_seat: guard, jammer_seat: jammer},
        policy=policy,
        max_ticks=ticks,
        cores={guard_seat: G_CORE, jammer_seat: CORE["A"]},
    )
    return played, guard_seat


def _moves_first(tick: int, seat: str) -> bool:
    return "AB"[(tick - 1) % 2] == seat


def _assert_mirrored_immunity(played: Played, guard_seat: str, *, ticks: int = G5_TICKS) -> None:
    assert [tick.tick for tick in played.ticks] == list(range(1, ticks + 1))
    assert all(tick.alive[guard_seat] for tick in played.ticks)
    assert max(tick.streak[guard_seat] for tick in played.ticks) <= 1
    for tick in played.ticks:
        if _moves_first(tick.tick, guard_seat):
            # The premise, observed: the guard took the tick's final offer,
            # with an own-core write, and so ends the tick owning core.
            last = [call for call in played.calls if call.tick == tick.tick][-1]
            assert (last.seat, last.slot) == (guard_seat, QUOTA - 1)
            assert last.action.kind is ActionKindV2.WRITE and last.action.operand in G_CELLS
            # So any zero evaluation falls on a second-mover tick.
            assert tick.owned[guard_seat] >= 1


@pytest.mark.parametrize("guard_first", [True, False])
@pytest.mark.parametrize("guard", GUARDS)
def test_g5_prime_guards_never_accumulate_two_consecutive_zero_evaluations(guard: str, guard_first: bool) -> None:
    guard_seat = "A" if guard_first else "B"
    min_owned = QUOTA
    for jammer in _g5_jammers(guard_seat):
        played, seat = _guard_match(PRIMARY, GUARDS[guard](), jammer, guard_first=guard_first)
        _assert_mirrored_immunity(played, seat)
        min_owned = min(min_owned, *(tick.owned[seat] for tick in played.ticks))
    # These adversaries press both guards down to a single cell but never to
    # zero under the mirrored order; the premise-only guard below is the
    # non-vacuous case.
    assert min_owned == 1


def _premise_only_guard(guard_seat: str) -> Brain:
    """Satisfies exactly the G.5' premise and nothing more.

    On its first-mover ticks its offer 7 -- under the mirrored order the
    tick's final offer, which a hit can never suppress -- repairs one own-core
    cell. Every other offer idles.
    """

    def brain(_c: ProcessMatchController, obs: ObservationV2, slot: int, _pid: str) -> AgentAction:
        if _moves_first(obs.current_tick, guard_seat) and slot == QUOTA - 1:
            return _w(G_CELLS[obs.current_tick % 8])
        return _IDLE

    return brain


@pytest.mark.parametrize("guard_first", [True, False])
def test_g5_prime_holds_non_vacuously_for_a_guard_that_only_satisfies_its_premise(guard_first: bool) -> None:
    guard_seat = "A" if guard_first else "B"
    played, seat = _guard_match(PRIMARY, _premise_only_guard(guard_seat), _eraser(guard_seat), guard_first=guard_first)
    _assert_mirrored_immunity(played, seat)
    # At zero core after *every* second-mover tick, one cell after every
    # first-mover tick: onset, recovery, onset, ... and never a capture.
    assert [tick.owned[seat] for tick in played.ticks] == [
        1 if _moves_first(tick.tick, seat) else 0 for tick in played.ticks
    ]
    assert [tick.streak[seat] for tick in played.ticks] == [
        0 if _moves_first(tick.tick, seat) else 1 for tick in played.ticks
    ]


@pytest.mark.parametrize("guard_first", [True, False])
def test_g5_prime_is_specific_to_the_mirrored_order_and_to_the_hold(guard_first: bool) -> None:
    guard_seat = "A" if guard_first else "B"
    # The stock parent (forward, K = 2): the same guard's final offer on its
    # first-mover ticks is followed by the jammer's final chunk, so it is at
    # zero on both parities and captured at tick 2.
    parent, seat = _guard_match(T_E3, _premise_only_guard(guard_seat), _eraser(guard_seat), guard_first=guard_first)
    assert [tick.tick for tick in parent.ticks] == [1, 2]
    assert [tick.owned[seat] for tick in parent.ticks] == [0, 0]
    assert [tick.streak[seat] for tick in parent.ticks] == [1, 2]
    assert parent.ticks[-1].alive[seat] is False
    # The K = 1 companion (mirrored): no hold, so the first zero -- the
    # guard's first second-mover tick -- is a capture (review Sec H, H4).
    companion, seat = _guard_match(
        COMPANION, _premise_only_guard(guard_seat), _eraser(guard_seat), guard_first=guard_first
    )
    captured_at = 2 if guard_first else 1
    assert [tick.tick for tick in companion.ticks] == list(range(1, captured_at + 1))
    assert companion.ticks[-1].alive[seat] is False
    assert companion.ticks[-1].owned[seat] == 0


# ---------------------------------------------------------------------------
# Mechanic characterizations with the tracked fixtures (seed 42, review Sec L)
# ---------------------------------------------------------------------------

SEED = 42
T_E3_ID = BYTEFRAY_RULESET_V6_RESEARCH_CAPTURE_HOLD_K2_DISRUPTION_SLOT1_ID
T_E4_ID = BYTEFRAY_RULESET_V6_RESEARCH_CAPTURE_HOLD_K2_DISRUPTION_SLOT1_MIRRORED_PASSES_ID
T_E3K1_ID = BYTEFRAY_RULESET_V6_RESEARCH_DISRUPTION_SLOT1_ID
T_E4K1_ID = BYTEFRAY_RULESET_V6_RESEARCH_DISRUPTION_SLOT1_MIRRORED_PASSES_ID
# Seed 42: Seat A's core at 485, Seat B's at 203; every single-process
# fixture anchors on its own core base.
A_CORE, B_CORE = 485, 203
SEATS = ("A", "B")


@dataclass(frozen=True)
class FixtureTick:
    tick: int
    cpu: dict[str, int]
    alive: dict[str, bool]
    owned: dict[str, int]
    # The lowest own-core count each seat reached at any write point in the tick.
    low: dict[str, int]
    bases: dict[str, str | None]
    writes: tuple[tuple[int, str | None], ...]
    kills: tuple[tuple[str, str | None], ...]


def _run_fixtures(root: Path, ruleset_id: str, seat_a: str, seat_b: str) -> list[FixtureTick]:
    """Run one fixture match at seed 42; element 0 is the tick-0 baseline."""

    prepare_data_root(root, [seat_a, seat_b])
    starts = resolve_direct_match_starts(
        ruleset_id=ruleset_id, arena_size=ARENA, entrant_count=2, supplied_starts=[None, None], seed=SEED
    )
    assert starts == (A_CORE, B_CORE)
    replay_path = root / "runs" / f"{ruleset_id}-{seat_a}-vs-{seat_b}" / "replay.jsonl"
    replay_path.parent.mkdir(parents=True)
    NativeMatchService().run(
        MatchRequest(
            config=Config(seed=SEED, arena_size=ARENA, instr_per_tick=QUOTA),
            entrants=(
                MatchEntrant.python("A", seat_a, starts[0], resolve_agent(root, seat_a)),
                MatchEntrant.python("B", seat_b, starts[1], resolve_agent(root, seat_b)),
            ),
            max_ticks=1000,
            replay_path=replay_path,
            verbose=False,
            ruleset_id=ruleset_id,
        )
    )
    cores = {"A": [(A_CORE + offset) % ARENA for offset in range(8)], "B": [(B_CORE + offset) % ARENA for offset in range(8)]}
    owners: dict[int, str | None] = {}

    def owned(seat: str) -> int:
        return sum(1 for cell in cores[seat] if owners.get(cell) == seat)

    ticks: list[FixtureTick] = []
    for record in iter_replay(replay_path):
        if not isinstance(record, TickSnapshot):
            continue
        writes = tuple(
            ((diff.address + offset) % ARENA, diff.owner)
            for diff in record.memory_diffs
            for offset in range(diff.length)
        )
        low = {seat: owned(seat) for seat in SEATS}
        for address, owner in writes:
            owners[address] = owner
            if record.tick > 0:
                low = {seat: min(low[seat], owned(seat)) for seat in SEATS}
        ticks.append(
            FixtureTick(
                tick=record.tick,
                cpu={agent.agent_id: agent.cpu_used for agent in record.agents},
                alive={agent.agent_id: agent.alive for agent in record.agents},
                owned={seat: owned(seat) for seat in SEATS},
                low=low,
                bases={"A": owners.get(A_CORE), "B": owners.get(B_CORE)},
                writes=writes,
                kills=tuple(
                    (event.victim, event.killer) for event in record.events if isinstance(event, KillDeathEvent)
                ),
            )
        )
    assert ticks[0].tick == 0 and ticks[0].owned == {"A": 8, "B": 8}
    return ticks


def _pm1(ticks: Sequence[FixtureTick]) -> tuple[int, int]:
    """(swing ticks, swings favouring the tick's first mover): E3's PM-1 definition.

    ``b(t)`` is Seat A's own-core cells minus Seat B's at the end of tick
    ``t``, starting from the tick-0 baseline; a swing is a both-alive tick
    with ``b(t) != b(t - 1)``.
    """

    swings = favouring_first = 0
    for previous, tick in itertools.pairwise(ticks):
        change = (tick.owned["A"] - tick.owned["B"]) - (previous.owned["A"] - previous.owned["B"])
        if tick.alive["A"] and tick.alive["B"] and change:
            swings += 1
            favouring_first += (change > 0) == ((tick.tick - 1) % 2 == 0)
    return swings, favouring_first


def _pair(root: Path, seat_a: str, seat_b: str) -> tuple[list[FixtureTick], list[FixtureTick]]:
    """(historical T-E3 control, E4 primary treatment) for one pairing."""

    return (
        _run_fixtures(root / "control", T_E3_ID, seat_a, seat_b),
        _run_fixtures(root / "treatment", T_E4_ID, seat_a, seat_b),
    )


def test_sniper_vs_disrupt_guard_settles_after_the_first_tick(tmp_path: Path) -> None:
    control, treatment = _pair(tmp_path, "e2_sniper", "e2_disrupt_guard")
    # Review Sec L-1. Tick 1 fights one cell pair per pass; passes 1-2 are
    # identical, and passes 3-4 run in the mirrored order.
    assert control[1].writes == (
        (203, "A"), (204, "A"), (485, "B"), (205, "A"), (203, "B"), (204, "B"),
        (206, "A"), (207, "A"), (205, "B"), (206, "B"), (208, "A"), (209, "A"),
        (207, "B"), (208, "B"),
    )  # fmt: skip
    assert treatment[1].writes == (
        (203, "A"), (204, "A"), (485, "B"), (205, "A"), (203, "B"), (204, "B"),
        (205, "B"), (206, "B"), (206, "A"), (207, "A"), (207, "B"), (208, "B"),
        (208, "A"), (209, "A"),
    )  # fmt: skip
    # Control: the second mover wins every pass, so the guard's core ends
    # 7, 3, 7, 3, ... -- 999 swings, none favouring the first mover.
    assert [tick.owned["B"] for tick in control[1:5]] == [7, 3, 7, 3]
    assert _pm1(control) == (999, 0)
    # Treatment: the passes split 2/2 and the guard's end-of-tick core is a
    # constant 5 from tick 1 -- the single swing is the initial one.
    assert {tick.owned["B"] for tick in treatment[1:]} == {5}
    assert {tick.owned["A"] for tick in treatment[1:]} == {7}
    assert _pm1(treatment) == (1, 1)
    for ticks in (control, treatment):
        assert len(ticks) == 1001 and all(tick.alive == {"A": True, "B": True} for tick in ticks)
        assert all(tick.cpu == {"A": 7, "B": 7} for tick in ticks[1:])
        # No zero-core evaluation, at the end of any tick or inside one.
        assert min(min(tick.low.values()) for tick in ticks[1:]) > 0


def test_sniper_vs_repair_guard_zero_core_ticks_leave_the_guards_first_mover_ticks(tmp_path: Path) -> None:
    control, treatment = _pair(tmp_path, "e2_sniper", "e2_repair_guard")
    # Review Sec L-2: under the stock order the guard (Seat B, first mover on
    # even ticks) ends 125 of its own first-mover ticks at zero core -- the
    # G.5 alternation of onset and recovery; under the mirrored order, none.
    zero = [tick.tick for tick in control[1:] if tick.owned["B"] == 0]
    assert len(zero) == 125 and zero[:3] == [8, 16, 24]
    assert all(tick % 2 == 0 for tick in zero)
    assert [tick.tick for tick in treatment[1:] if tick.owned["B"] == 0] == []
    for ticks in (control, treatment):
        assert len(ticks) == 1001 and not any(tick.kills for tick in ticks)
    # Without the hold, that zero is a capture at tick 8 under the stock
    # order, and never happens under the mirrored order (review Sec L-2, H4).
    k1_control = _run_fixtures(tmp_path / "k1-control", T_E3K1_ID, "e2_sniper", "e2_repair_guard")
    k1_treatment = _run_fixtures(tmp_path / "k1-treatment", T_E4K1_ID, "e2_sniper", "e2_repair_guard")
    assert (k1_control[-1].tick, k1_control[-1].kills) == (8, (("B", "A"),))
    assert len(k1_treatment) == 1001 and not any(tick.kills for tick in k1_treatment)


def test_guarded_painter_mirror_keeps_the_second_movers_opening_privilege(tmp_path: Path) -> None:
    # Review Sec L-3, the internal negative control.
    control, treatment = _pair(tmp_path, "e2_guarded_painter", "e2_guarded_painter_twin")
    # Passes 1-2 of tick 1 are identical: F hits L's base and repairs its own;
    # L, one offer down, hits F's base; F, one offer down, paints; L repairs
    # its base and paints. Only passes 3-4 are reordered.
    opening = ((203, "A"), (485, "A"), (485, "B"), (484, "A"), (203, "B"), (202, "B"))
    assert control[1].writes[:6] == treatment[1].writes[:6] == opening
    assert control[1].writes[6:] != treatment[1].writes[6:]
    for ticks in (control, treatment):
        # The second mover owns both base cells at the end of every tick up
        # to the capture onset (tick 92), under both orders ...
        for tick in ticks[1:92]:
            second = "B" if tick.tick % 2 else "A"
            assert tick.bases == {"A": second, "B": second}, tick.tick
        # ... and every swing favours the second mover -- which, under the
        # treatment, is no longer the final-chunk owner.
        assert _pm1(ticks) == (92, 0)
        # Seat B captures Seat A at tick 93 in both orders.
        assert (ticks[-1].tick, ticks[-1].kills) == (93, (("A", "B"),))


def test_jam_sniper_vs_min_guard_is_still_captured_at_tick_four(tmp_path: Path) -> None:
    control, treatment = _pair(tmp_path, "e3_jam_sniper", "e2_min_guard")
    for ticks in (control, treatment):
        assert [tick.owned["B"] for tick in ticks[1:]] == [4, 1, 0, 0]
        assert (ticks[-1].tick, ticks[-1].kills) == (4, (("B", "A"),))
    # G.4' on real agents: the jam costs the min guard four offers as the
    # stock second mover, never more than three under the mirrored order.
    assert [tick.cpu["B"] for tick in control[1:]] == [4, 5, 4, 5]
    assert [tick.cpu["B"] for tick in treatment[1:]] == [5, 5, 5, 5]


def test_probe_mirror_is_still_a_mutual_elimination_at_tick_three(tmp_path: Path) -> None:
    control, treatment = _pair(tmp_path, "v4_probe", "v4_probe_twin")
    for ticks in (control, treatment):
        assert [tick.owned for tick in ticks[1:]] == [{"A": 1, "B": 1}, {"A": 0, "B": 0}, {"A": 0, "B": 0}]
        assert (ticks[-1].tick, ticks[-1].kills) == (3, (("A", "B"), ("B", "A")))
        assert ticks[-1].alive == {"A": False, "B": False}


def test_spread_sniper_vs_disrupt_guard_reaches_zero_only_inside_ticks(tmp_path: Path) -> None:
    # Review Sec L-6: the guard's core is at zero at some point inside 998 of
    # the 1000 ticks, yet ends every tick holding at least four cells --
    # capture is still judged once, at the end of the tick.
    control, treatment = _pair(tmp_path, "e2_spread_sniper", "e2_disrupt_guard")
    for ticks in (control, treatment):
        assert sum(tick.low["B"] == 0 for tick in ticks[1:]) == 998
        assert [tick.owned["B"] for tick in ticks[1:]] == [6] + [4] * 999
        assert len(ticks) == 1001 and not any(tick.kills for tick in ticks)


@pytest.mark.parametrize(
    ("seats", "swings"),
    [(("e2_sniper", "e2_min_guard"), 999), (("e2_disrupt_guard", "e2_disrupt_guard_twin"), 1000)],
    ids=["sniper-vs-min-guard", "disrupt-guard-mirror"],
)
def test_opening_pass_contests_end_every_tick_the_same_under_both_orders(
    tmp_path: Path, seats: tuple[str, str], swings: int
) -> None:
    # Review Sec L-7: the only contested cells are the bases, fought in the
    # opening passes, so the end-of-tick core state is identical tick by tick
    # and every swing favours the second mover under both orders.
    control, treatment = _pair(tmp_path, *seats)
    assert [tick.owned for tick in control] == [tick.owned for tick in treatment]
    assert _pm1(control) == _pm1(treatment) == (swings, 0)
