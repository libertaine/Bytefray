"""V6 E8: ADAPT8's freeze tests (PR8 Sec 3.2 and R-8; plan Sec 5.6), engine-level.

docs/research/v6/V6_E8_ACTIVE_SPATIAL_SENSING_PREREGISTRATION.md Sec 3.2
registers these cases, run before the freeze:

* ADAPT8 in Seat A and in Seat B;
* against a scripted static opponent and a scripted responsive evader;
* under both parents (and both channels: all four conditions);
* with hits placed at every chunk position of both seat orders, so that every
  suppression pattern of the post-hoc audit's Sec 8 is exercised;
* with ticks in which ADAPT8 itself receives no callback.

They assert the count of consecutive confirming verification observations,
that an unobserved tick neither advances nor resets it, the reset on observed
relocation, and the switch at the second consecutive confirmation. Never an
outcome.

**The oracle.** :func:`_oracle` re-derives the count from the trace alone --
the actions, the returned ``sensed_anchors`` and visible sets, the ticks and
callback indexes -- by the registered rule, sharing no code with the policy.
At every ADAPT8 callback the policy's own count, switch and classification of
its SENSE actions must equal the oracle's. The opponent (``_opponent``) is
scripted: a decoy anchor ADAPT8 finds, static or evading responsively, and a
second process ADAPT8 never finds. Without hits it never disrupts ADAPT8,
which is Appendix A.4's scenario.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from _e8_family_engine_harness import (
    ACTIVE_RULESETS,
    ARENA,
    C8,
    C8L,
    SEATS,
    T8,
    T8L,
    WHOLE_TICK,
    Plan,
    Played,
    callbacks_by_tick,
    distance,
    play,
    sigma_of,
    with_index,
)

from tools.research.v6.e8.family import package_id

WINDOW = 27
K = 2
#: PA Sec 8's positions: the opponent's offer k (the start of each of its chunks), in ticks ADAPT8
#: moves first and in ticks the opponent moves first.
PATTERNS = [None] + [(parity, k) for parity in ("adapt-first", "opponent-first") for k in (0, 2, 4, 6)]


def _pattern_id(pattern: tuple[str, int] | None) -> str:
    return "no-hits" if pattern is None else f"{pattern[0]}-offer{pattern[1]}"


def _other(seat: str) -> str:
    return "B" if seat == "A" else "A"


def _parity_ticks(mover: str, first: int, last: int) -> list[int]:
    return [t for t in range(first, last + 1) if (t % 2 == 1) == (mover == "A")]


def _opponent(seat: str, kind: str, pattern: tuple[str, int] | None) -> Plan:
    """The scripted opponent: a decoy anchor ADAPT8 finds, static or evading responsively, and a second
    process ADAPT8 never finds, which repairs the opponent's core (so whole-tick denial does not end the
    match within the test) and makes the scheduled hits at the opponent's exact offers. Without hits it
    never disrupts ADAPT8: Appendix A.4's scenario."""

    sigma = sigma_of(7, seat)
    # The evader's moves cycle +30 and -50 along ADAPT8's direction: no evasion returns it to an
    # address ADAPT8 saw before (with alternating +-30, two verifications can both find it at one
    # address, its relocations unobserved), and it never drifts toward the second process.
    evade = (30 * sigma, -50 * sigma) if kind == "evader" else ()
    hits: dict[tuple[int, int], None] = {}
    if pattern is not None:
        parity, k = pattern
        mover = seat if parity == "adapt-first" else _other(seat)
        hits = {(t, k + 1): None for t in _parity_ticks(mover, 2, 14)}
    return Plan(hits=hits, evade=evade, repair=8, processes=2, away=64 * sigma)


#: The opponent's core base lies 146 cells along ADAPT8's direction: in discovery window c_1 under
#: active, and two sweeps away under passive. ADAPT8 therefore first disrupts it in its second chunk of
#: tick 1, after the opponent's first chunk, so a responsive evader can answer from tick 2.
GAP = 146


def _starts(seat: str) -> tuple[int, int]:
    base = 100
    starts = (base, (base + sigma_of(7, seat) * GAP) % ARENA)
    return starts if seat == "A" else (starts[1], starts[0])


def _oracle(decisions: list[dict[str, Any]], *, active: bool) -> list[tuple[int, bool, str | None]]:
    """(count, switched, SENSE class) after each ADAPT8 callback, by the registered rule, from the trace alone."""

    out: list[tuple[int, bool, str | None]] = []
    known: list[int] = []
    tracked: list[int] = []
    count, switched, discovered = 0, False, False
    search: int | None = None  # windows of a search still to sense
    previous: tuple[dict[str, Any], str | None] | None = None
    for index, record in with_index(decisions):
        observation, action = record["observation"], record["action"]
        if active and previous is not None and previous[0]["action"]["kind"] == "sense":
            prior, prior_class = previous
            result = prior["applied_result"]["sensed_anchors"]
            assert observation["previous_sense_anchors"] == result  # D8-13's reflection, used as the delivery
            target = prior["action"]["operand"] % ARENA
            gone = [x for x in known if distance(x, target) <= WINDOW and x not in result]
            lowest = known[0] if known else None
            known = sorted((set(known) - set(gone)) | set(result))
            discovered = discovered or bool(result)
            if not switched:
                if prior_class == "verify":
                    count = count + 1 if target in result else 0  # a confirmation, or a found relocation
                elif lowest is not None and lowest in gone:
                    count = 0
                if count >= K:
                    switched, search = True, None
            if not switched:
                if result:
                    search = None  # replaced
                elif prior_class == "verify" and gone:
                    search = 2  # missing, nothing returned: the second and third windows
                elif prior_class == "search":
                    search = None if search == 1 else (search or 1) - 1
        if not active:
            visible = observation["visible_enemy_anchor_addresses"]
            if not switched and tracked:
                a = tracked[0]
                if a not in visible:
                    count = 0  # an observed relocation, at any callback
                elif index == 1:
                    count += 1  # the visible set at the first offer of the tick confirms a
                if count >= K:
                    switched = True
            tracked = visible
        sense_class = None
        if action["kind"] == "sense":
            assert active
            if search is not None:
                sense_class = "search"
            elif index == 1 and not switched and discovered and known:
                sense_class = "verify"
                assert action["operand"] == known[0]  # KU-8: centered on the lowest known address
            else:
                assert not known  # otherwise only discovery senses
                sense_class = "discover"
        out.append((count, switched, sense_class))
        previous = (record, sense_class)
    return out


@pytest.mark.parametrize("pattern", PATTERNS, ids=_pattern_id)
@pytest.mark.parametrize("opponent", ["static", "evader"])
@pytest.mark.parametrize("seat", SEATS)
@pytest.mark.parametrize("ruleset_id", [C8, C8L, T8, T8L])
def test_adapt8_freeze(tmp_path: Path, ruleset_id: str, seat: str, opponent: str,
                       pattern: tuple[str, int] | None) -> None:
    active = ruleset_id in ACTIVE_RULESETS
    played: Played = play(tmp_path, ruleset_id, *(
        (package_id("ADAPT8"), _opponent(seat, opponent, pattern)) if seat == "A"
        else (_opponent(seat, opponent, pattern), package_id("ADAPT8"))), starts=_starts(seat), ticks=16)
    decisions = played.decisions(seat)
    snaps = played.snaps[seat]
    assert len(decisions) == len(snaps)
    expected = _oracle(decisions, active=active)

    # The policy's count, switch and SENSE classes equal the registered rule's, at every callback.
    for (count, switched, sense_class), snap in zip(expected, snaps, strict=True):
        assert (snap.adapt_count, snap.switched) == (count, switched)
        if sense_class is not None:
            assert snap.purpose == sense_class
    # The switch comes exactly at the second consecutive confirmation, and is permanent: as once,
    # with no verification and no search afterwards.
    switch = next((i for i, (_c, s, _k) in enumerate(expected) if s), None)
    if switch is not None:
        assert expected[switch][0] == K and expected[switch - 1][0] == K - 1
        assert all(s.purpose not in ("verify", "search") and s.search_address is None for s in snaps[switch + 1:])
    counts = [c for c, _s, _k in expected]

    # The preconditions, from the real run.
    by_tick = callbacks_by_tick(played.records, seat)
    if pattern is not None:
        parity, k = pattern
        mover = seat if parity == "adapt-first" else _other(seat)
        last = max(by_tick)
        hit_ticks = [t for t in _parity_ticks(mover, 4, 13) if t < last]
        # PA Sec 8: a hit at the opponent's offer k. The second process is never disrupted, so its offers
        # are exact. A hit after ADAPT8's last offer of a tick costs it nothing: the disruption ends with
        # the tick. Under whole-tick ADAPT8 then receives k + 2 callbacks in a tick it moves first (8 when
        # k = 6) and k in a tick it moves second; under lambda = 1 it loses exactly one offer (none when
        # k = 6 in a tick it moves first). (Under passive, ADAPT8's own search can park its anchor on the
        # opponent's core cell 0, the missing anchor's last address, where the opponent's core repairs hit
        # it too: such a tick can only lose more callbacks.)
        if ruleset_id in WHOLE_TICK:
            predicted = min(8, k + 2) if parity == "adapt-first" else k
        else:
            predicted = 8 if parity == "adapt-first" and k == 6 else 7
        observed = [by_tick.get(t, 0) for t in hit_ticks]
        assert predicted in observed
        assert all(value <= predicted for value in observed)
    ticks = [r["observation"]["current_tick"] for r in decisions]
    gaps = [i for i in range(len(ticks) - 1) if ticks[i + 1] > ticks[i] + 1]  # unobserved ticks follow i
    if ruleset_id in WHOLE_TICK and pattern == ("opponent-first", 0):
        # Ticks with no ADAPT8 callback at all, crossed with a nonzero count before the switch: the
        # oracle (which ignores them) and the policy agree there, so they neither advanced nor reset it.
        assert [i for i in gaps if counts[i] == 1 and (switch is None or i < switch)]
    if opponent == "static" and pattern is None:
        assert switch is not None  # a static opponent is confirmed twice in a row
    if opponent == "evader" and pattern is None:
        resets = [i for i in range(1, len(counts)) if counts[i - 1] >= 1 and counts[i] == 0]
        assert resets  # an observed relocation reset the count


def test_the_freeze_matrix_covers_every_registered_case() -> None:
    assert len(PATTERNS) == 9 and _pattern_id(None) == "no-hits"
    assert {p[0] for p in PATTERNS if p} == {"adapt-first", "opponent-first"}
    assert {p[1] for p in PATTERNS if p} == {0, 2, 4, 6}
