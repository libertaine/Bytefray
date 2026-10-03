"""V6 E8: the frozen analysis on designed synthetic tables (PR8 Sec 4 to 8; phase I8-5).

No match runs here. Each case is a synthetic F1/F2 cell table (``_e8_scripted_matrix``)
built from an outcome rule whose registered statuses are known in advance:

* **the cycle**: member i beats the next five members in registered order and
  loses to the other five, whatever the seat. No member and no A8 member is
  universal, LURK8 beats RUSH8 against some opponents, and every pairing is
  seat-neutral.
* overrides of the cycle that make a member universal, make re-acquisition
  pay against EVADE8 (or never pay), force early captures, seat-determine
  the pairings, or stall the matches.

The analyzer must read each case's registered statuses exactly, its payoffs
must equal an independent computation and E6's PR6 functions, and its seat
decomposition must equal E4's own metrics. Nothing registered is restated
here except as the expected answer.
"""

from __future__ import annotations

import json
from fractions import Fraction
from typing import Any

import pytest
from _e8_scripted_matrix import SYNTHETIC_SEEDS, synthetic_condition

from tools.research.v6.e3.gates import cell_key
from tools.research.v6.e6 import payoff as pr6
from tools.research.v6.e8 import analyze_e8, decision, family, payoff, telemetry
from tools.research.v6.e8.traces import ABSENT

MEMBERS = decision.MEMBERS
Outcome = tuple[str, int, str | None]


def cycle(overrides: dict[tuple[str, str], str] | None = None, *, ticks: int = 50,
          seat_a_always: bool = False, stall: bool = False):  # type: ignore[no-untyped-def]
    """The cyclic table; ``overrides`` maps (winner, loser) to the winning member for that pairing."""
    table = overrides or {}

    def outcome(a: str, b: str, seed: int) -> Outcome:
        if stall:
            return "tie", 1000, None
        if seat_a_always and a != b:
            return "A", ticks, "B"
        winner = table.get((a, b)) or table.get((b, a))
        if winner is None:
            if a == b:
                winner = b  # a mirror: the twin in Seat B wins
            else:
                winner = a if (MEMBERS.index(b) - MEMBERS.index(a)) % 11 in range(1, 6) else b
        result = "A" if winner == a and a != b else "B"
        return result, ticks, "B" if result == "A" else "A"
    return outcome


@pytest.fixture(scope="module")
def base() -> dict[str, Any]:
    control = synthetic_condition("C8", cycle(), verifications=lambda opp, seed: 4 if opp == "EVADE8" else 1)
    treatment = synthetic_condition("T8", cycle(), verifications=lambda opp, seed: 4 if opp == "EVADE8" else 1)
    return analyze_e8.analyze_arm(control, treatment, seeds=SYNTHETIC_SEEDS)


# ---------------------------------------------------------------------------
# Payoffs
# ---------------------------------------------------------------------------


def _seat_value(result: str) -> Fraction:
    return {"A": Fraction(1), "B": Fraction(0), "tie": Fraction(1, 2)}[result]


def test_payoffs_equal_an_independent_computation_and_pr6s_functions() -> None:
    rule = cycle({("RUSH8", "GREED8"): "GREED8"})
    condition = synthetic_condition("T8", rule)
    table = payoff.member_table(condition.f1, member_of=analyze_e8.member_of(), seeds=SYNTHETIC_SEEDS)
    point = payoff.reading(table)
    for i in MEMBERS:
        for j in MEMBERS:
            if i == j:
                assert point.u[(i, j)] == Fraction(1, 2)
                continue
            per_seed = [(_seat_value(rule(i, j, s)[0]) + 1 - _seat_value(rule(j, i, s)[0])) / 2 for s in SYNTHETIC_SEEDS]
            assert point.u[(i, j)] == sum(per_seed, Fraction(0)) / len(per_seed)
    assert point.u == pr6.payoffs(table)
    assert point.br == pr6.best_responses(point.u, candidates=decision.PI_F, opponents=decision.PI,
                                          epsilon=Fraction(1, 16))
    assert point.mixed["RUSH8"] == sum((point.u[("RUSH8", j)] for j in MEMBERS), Fraction(0)) / 11
    assert point.delta_r["EVADE8"] == point.u[("REACQ8", "EVADE8")] - point.u[("RUSH8", "EVADE8")]


def test_the_registered_sets_and_contrasts_come_from_the_transcription() -> None:
    assert payoff.L8 == (("LURK8", "RUSH8"), ("PACED8", "RUSH8"))
    assert (payoff.REPEAT, payoff.ONCE, payoff.EPSILON) == ("REACQ8", "RUSH8", Fraction(1, 16))
    assert analyze_e8.FORCED_LINE_TICK == 3


# ---------------------------------------------------------------------------
# The cycle: the registered statuses
# ---------------------------------------------------------------------------


def test_the_cycle_reads_as_registered(base: dict[str, Any]) -> None:
    h = base["hypotheses"]
    assert (h["H8-SUB"], h["H8-PAR"], h["H8-CHANNEL"], h["H8-LESS"]) == ("SUPPORTED",) * 4
    assert h["H8-REPEAT"] == "REFUTED"  # REACQ8 and RUSH8 both lose to EVADE8: Delta^R = 0
    assert (h["H8-FL"], h["H8-TAX"], h["H8-SEAT"]) == ("REFUTED", "SUPPORTED", "REFUTED")
    assert base["census"] == ["EVADE8"] and base["fired"] == []
    assert base["universal"] == [] and base["universal_a8"] == []
    assert base["H8-TAX"]["A"] == base["H8-TAX"]["B"] == "1/1"
    assert base["payoff"]["treatment"]["stab_P_none"] == 1000


def test_h8_adapt_is_not_interpretable_without_a_supported_repeat(base: dict[str, Any]) -> None:
    adapt = base["H8-ADAPT"]
    assert adapt["interpretable"] is False and adapt["status"] is None
    assert adapt["allocation_check"] is True  # 4 verifications against EVADE8 against 1 against the rest
    assert adapt["V"]["EVADE8"] == "4/1" and adapt["V"]["GUARD8"] == "1/1"
    assert adapt["static_set"] == list(decision.static_set(("EVADE8",)))


def test_the_public_result_is_json() -> None:
    condition = synthetic_condition("C8", cycle())
    result = analyze_e8.analyze_arm(condition, condition, seeds=SYNTHETIC_SEEDS)
    text = json.dumps(analyze_e8.public(result), sort_keys=True)
    assert "_seat_results" not in text and "_tax" not in text


# ---------------------------------------------------------------------------
# Designed overrides
# ---------------------------------------------------------------------------


def _beats_all(member: str) -> dict[tuple[str, str], str]:
    return {(member, other): member for other in MEMBERS if other != member}


def _arm(treatment_rule, control_rule=None, **kwargs: Any) -> dict[str, Any]:  # type: ignore[no-untyped-def]
    control = synthetic_condition("C8", control_rule or cycle(), **kwargs)
    treatment = synthetic_condition("T8", treatment_rule, **kwargs)
    return analyze_e8.analyze_arm(control, treatment, seeds=SYNTHETIC_SEEDS)


def test_a_universal_searcher_is_a_search_race_and_a_channel_race() -> None:
    result = _arm(cycle(_beats_all("RUSH8")))
    h = result["hypotheses"]
    assert (h["H8-SUB"], h["H8-CHANNEL"]) == ("REFUTED", "REFUTED")
    assert result["universal"] == ["RUSH8"] and result["universal_a8"] == ["RUSH8"]
    kills = result["kill_criteria"]
    assert kills["KC8-1"] == {"fires": True, "label": {"label": "search race", "members": ["RUSH8"]},
                              "detail": None}
    assert kills["KC8-6"]["label"] == {"label": "channel race", "members": ["RUSH8"]}
    assert kills["KC8-2"]["fires"] is False
    assert {"KC8-1", "KC8-6"} <= set(result["fired"])


def test_a_universal_greed_member_is_greed_dominance() -> None:
    result = _arm(cycle(_beats_all("GREED8")))
    assert result["hypotheses"]["H8-SUB"] == "REFUTED"
    assert result["kill_criteria"]["KC8-1"]["label"] == {"label": "greed dominance", "members": ["GREED8"]}
    assert result["kill_criteria"]["KC8-2"]["fires"] is True
    assert result["hypotheses"]["H8-CHANNEL"] == "SUPPORTED"  # GREED8 is not in A8


def test_lurk8_alone_universal_in_a8_is_information_dominated() -> None:
    rule = cycle({**{("LURK8", m): "LURK8" for m in decision.A8 if m != "LURK8"}})
    result = _arm(rule)
    # LURK8 beats every other A8 member, and against STRESS8 every A8 member loses: it is in every BR^A(j).
    assert result["universal_a8"] == ["LURK8"] and result["hypotheses"]["H8-CHANNEL"] == "REFUTED"
    assert result["kill_criteria"]["KC8-6"]["label"] == {"label": "information dominated", "members": ["LURK8"]}


def test_re_acquisition_that_pays_against_the_census_supports_h8_repeat() -> None:
    result = _arm(cycle({("REACQ8", "EVADE8"): "REACQ8"}),
                  verifications=lambda opp, seed: 4 if opp == "EVADE8" else 1)
    assert result["hypotheses"]["H8-REPEAT"] == "SUPPORTED"
    assert result["payoff"]["treatment"]["delta_r"]["EVADE8"]["delta_r"] == "1/1"
    adapt = result["H8-ADAPT"]
    assert adapt["interpretable"] is True and adapt["status"] in decision.STATUSES


def test_h8_adapt_reads_the_mixed_field() -> None:
    better = cycle({("REACQ8", "EVADE8"): "REACQ8", **_beats_all("ADAPT8")})
    result = _arm(better, verifications=lambda opp, seed: 4 if opp == "EVADE8" else 1)
    assert result["H8-ADAPT"]["status"] == "SUPPORTED"
    worse = cycle({("REACQ8", "EVADE8"): "REACQ8", **{("ADAPT8", m): m for m in MEMBERS if m != "ADAPT8"}})
    result = _arm(worse, verifications=lambda opp, seed: 4 if opp == "EVADE8" else 1)
    assert result["H8-ADAPT"]["status"] == "REFUTED"
    no_check = _arm(better, verifications=lambda opp, seed: 1)
    assert no_check["H8-ADAPT"]["allocation_check"] is False
    assert (no_check["H8-ADAPT"]["interpretable"], no_check["H8-ADAPT"]["status"]) == (False, None)


def test_forced_lines_against_every_defender_support_h8_fl() -> None:
    def rule(a: str, b: str, seed: int) -> Outcome:
        if a == "RUSH8" and b in decision.DEFENDERS:
            return "A", 2, "B"
        if b == "RUSH8" and a in decision.DEFENDERS:
            return "B", 2, "A"
        return cycle()(a, b, seed)
    result = _arm(rule)
    assert result["hypotheses"]["H8-FL"] == "SUPPORTED"
    assert result["H8-FL"]["min_over_defenders"]["RUSH8"] == "1/1"
    assert result["kill_criteria"]["KC8-4"]["fires"] is True


def test_seat_determined_pairings_raise_pf8_4_and_h8_seat() -> None:
    result = _arm(cycle(seat_a_always=True))
    assert result["pathology"]["PF8-4"]["raised"] is True
    assert len(result["pathology"]["PF8-4"]["units"]) == 55
    assert result["hypotheses"]["H8-SEAT"] == "SUPPORTED" and result["pathology"]["PF8-5"]["raised"] is True
    assert result["seat"]["delta_g"] == "5/6"  # 55 units from |GSB| 0 to 1, 11 mirrors unchanged
    kc5 = result["kill_criteria"]["KC8-5"]
    assert kc5["fires"] is True and kc5["detail"]["layers"] == ["unit", "family"]
    strata = result["seat"]["strata"]
    assert strata["containing_phase_sensitive"]["units"] + strata["not_containing_phase_sensitive"]["units"] == 66


def test_stalling_and_lost_contact_raise_pf8_1_and_pf8_2() -> None:
    stalled = synthetic_condition("T8", cycle(stall=True), contact=lambda cell: False)
    control = synthetic_condition("C8", cycle())
    result = analyze_e8.analyze_arm(control, stalled, seeds=SYNTHETIC_SEEDS)
    assert result["pathology"]["PF8-1"]["raised"] and result["pathology"]["PF8-2"]["raised"]
    assert result["pathology"]["PF8-3"]["raised"]  # captured under C8, never under T8
    assert result["kill_criteria"]["KC8-3"]["fires"] is True
    assert result["hypotheses"]["H8-TAX"] == "REFUTED"  # every outcome class changed: A = 0


# ---------------------------------------------------------------------------
# Seat metrics, CQ8-4, CQ8-5
# ---------------------------------------------------------------------------


def test_the_seat_decomposition_equals_e4_and_a_corruption_is_refused() -> None:
    condition = synthetic_condition("C8")  # the default outcome: every result kind, seed-varied
    results = analyze_e8.seat_results(condition, seeds=SYNTHETIC_SEEDS)
    analyze_e8.check_against_e4(condition, results)
    unit = ("pairing", "RUSH8", "REACQ8")
    corrupted = {**results, unit: [("A", "A")] * len(SYNTHETIC_SEEDS)}
    with pytest.raises(analyze_e8.AnalysisError, match="differs from E4"):
        analyze_e8.check_against_e4(condition, corrupted)


def test_cq8_4_passes_with_the_control_in_the_treatment_slot() -> None:
    condition = synthetic_condition("C8")
    result = analyze_e8.analyze_arm(condition, condition, seeds=SYNTHETIC_SEEDS)
    report = analyze_e8.control_against_control(result)
    assert report["status"] == "PASS" and all(report["checks"].values())
    differing = _arm(cycle(_beats_all("RUSH8")))
    with pytest.raises(analyze_e8.AnalysisError):
        analyze_e8.control_against_control(differing)


def test_cq8_5_partitions_the_66_units_by_o_neutral(base: dict[str, Any]) -> None:
    condition = synthetic_condition("C8", cycle())
    strata = analyze_e8.seat_strata(analyze_e8.seat_results(condition, seeds=SYNTHETIC_SEEDS))
    assert len(strata["neutral"]) == 55 and len(strata["non_neutral"]) == 11  # the mirrors are seat B
    assert all(unit.startswith("mirror|") for unit in strata["non_neutral"])


def test_decisive_tick_parity() -> None:
    condition = synthetic_condition("C8", cycle(ticks=51))
    parity = analyze_e8.decisive_parity(condition)
    assert parity["pairing|RUSH8|REACQ8"] == {"odd:A": 32, "odd:B": 32}


# ---------------------------------------------------------------------------
# Interpretation and the companion
# ---------------------------------------------------------------------------


def test_interpretation_after_a_pass(base: dict[str, Any]) -> None:
    reading = analyze_e8.interpret(e8_d="PASS", primary=analyze_e8.public(base))
    assert reading["row"] == "R8-PRESERVES" and reading["core_answer"] == "NO"  # H8-REPEAT is REFUTED
    assert reading["disposition"] == decision.NOT_ESTABLISHED
    assert [q["hypothesis"] for q in reading["qualifiers"]] == ["H8-CHANNEL", "H8-LESS"]
    assert reading["repeat"]["scope_sentence"] == decision.SCOPE_SENTENCE
    assert reading["adapt"]["status"] == decision.NOT_INTERPRETABLE
    assert reading["channel_difference"] == list(analyze_e8.CHANNEL_DIFFERENCE)


def test_a_failed_gate_voids_every_reading(base: dict[str, Any]) -> None:
    reading = analyze_e8.interpret(e8_d="FAIL", primary=analyze_e8.public(base))
    assert (reading["row"], reading["core_answer"], reading["disposition"]) == ("STOP", "NOT EVALUABLE", "VOID")
    assert "qualifiers" not in reading


def test_a_kill_makes_the_disposition_reject() -> None:
    result = analyze_e8.public(_arm(cycle(_beats_all("RUSH8"))))
    reading = analyze_e8.interpret(e8_d="PASS", primary=result)
    assert reading["disposition"] == decision.REJECT and "KC8-1" in reading["fired"]


def test_the_companion_reading(base: dict[str, Any]) -> None:
    same = analyze_e8.companion_reading(base, base)
    assert same["agrees"] is True and same["differences"] == []
    other = _arm(cycle(_beats_all("RUSH8")))
    differs = analyze_e8.companion_reading(base, other)
    assert differs["agrees"] is False and any(d.startswith("H8-SUB") for d in differs["differences"])
    assert differs["standing"] == "a status comparison, never a verdict"


# ---------------------------------------------------------------------------
# Telemetry: the knowledge reconstruction and O-VERIF
# ---------------------------------------------------------------------------


def _row(tick: int, index: int, entrant: str, kind: str, operand: int, *, delivered: Any = ABSENT,
         sensed: Any = ABSENT, visible: list[int] | None = None, anchor: int = 100, status: str = "APPLIED") -> list[Any]:
    address = operand % 512
    return [tick, entrant, "main", index, anchor, 256, visible or [], True, None, None, delivered, kind, operand,
            1 if kind == "write" else None, status, address, None, None, sensed]


def _summary() -> dict[str, Any]:
    return {"core_base": {"A": 100, "B": 300}, "tick0_anchors": {"A": {"main": 100}, "B": {"main": 300}}}


def test_adapt8s_verifications_and_a_relocation_are_reconstructed_from_the_trace() -> None:
    rows = [
        _row(1, 1, "A", "sense", 191, sensed=[]),              # discovery c_0: nothing
        _row(1, 2, "A", "sense", 246, delivered=[], sensed=[300]),  # c_1 finds 300
        _row(1, 3, "A", "write", 300, delivered=[300]),        # delivered: discovery
        _row(2, 1, "A", "sense", 300, sensed=[300]),           # verification
        _row(2, 2, "A", "write", 300, delivered=[300]),        # confirmed: count 1
        _row(2, 1, "B", "move", 20, anchor=300),               # the opponent evades to 320
        _row(3, 1, "A", "sense", 300, sensed=[320]),           # verification: 300 missing, 320 returned
        _row(3, 2, "A", "write", 320, delivered=[320]),        # replaced: a re-acquisition, by evasion
    ]
    stats = telemetry.cell_telemetry(rows, _summary(), members={"A": "ADAPT8", "B": "EVADE8"}, active=True)
    assert stats["A"]["verifications"] == 2
    assert stats["A"]["first_discovery_tick"] == 1
    assert (stats["A"]["senses_before_discovery"], stats["A"]["senses_after_discovery"]) == (2, 2)
    assert stats["A"]["reacquisitions"] == {"evasion": 1}
    assert stats["B"]["evasions"] == 1 and stats["A"]["hits_received"] == 0


def test_a_once_member_never_counts_verifications_or_reacquisitions() -> None:
    rows = [_row(1, 1, "A", "sense", 191, sensed=[300]), _row(1, 2, "A", "write", 300, delivered=[300]),
            _row(2, 1, "A", "sense", 300, sensed=[320]), _row(2, 2, "A", "write", 320, delivered=[320])]
    stats = telemetry.cell_telemetry(rows, _summary(), members={"A": "RUSH8", "B": "GUARD8"}, active=True)
    assert stats["A"]["verifications"] == 0 and stats["A"]["reacquisitions"] == {}
    assert stats["B"]["hits_received"] == 1  # RUSH8's WRITE at 300, GUARD8's anchor


def test_passive_verification_observations_and_a_re_sighting() -> None:
    rows = [
        _row(1, 1, "A", "move", 64, visible=[]),
        _row(1, 2, "A", "write", 300, visible=[300]),
        _row(2, 1, "A", "write", 300, visible=[300]),          # an observation: count 1
        _row(2, 2, "A", "move", 64, visible=[]),               # 300 lost, nothing visible: missing
        _row(3, 1, "A", "write", 330, visible=[330]),          # re-sighted elsewhere: a re-acquisition
    ]
    stats = telemetry.cell_telemetry(rows, _summary(), members={"A": "ADAPT8", "B": "GUARD8"}, active=False)
    assert stats["A"]["verification_observations"] == 1
    assert stats["A"]["reacquisitions"] == {"own movement": 1}


def test_v_is_the_exact_median_of_the_per_seed_means() -> None:
    per_seed = {s: [s % 4, 0] for s in range(32)}
    assert telemetry.verification_v(per_seed) == Fraction(3, 4)  # 0, 1/2, 1, 3/2, eight each: (1/2 + 1) / 2
    with pytest.raises(ValueError):
        telemetry.verification_v({1: [1]})


def test_family_members_map_to_packages_in_the_synthetic_table() -> None:
    condition = synthetic_condition("C8")
    keys = {cell_key(c) for c in condition.f1}
    assert len(keys) == 3520 and len(condition.f2) == 704
    assert {family.PACKAGES[c["subject_id"]][1] for c in condition.f2} == {"primary"}
