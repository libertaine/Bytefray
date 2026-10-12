"""E4 analysis: units, transition classes, census, P-PAR, seat metrics, E4-H0 .. E4-H8,
D9' and the interpretation reading (design review Sec M, Sec N, Sec P).

Synthetic cell records and telemetry rows exercise every branch by value; the
real-corpus path is covered by ``test_v6_e4_pipeline.py``.
"""

from __future__ import annotations

from collections.abc import Iterable
from fractions import Fraction
from typing import Any

import pytest

from tools.research.v6.e4 import analyze_e4 as a
from tools.research.v6.e4 import contest_classes, matrix
from tools.research.v6.e4.cell_metrics import exact_text
from tools.research.v6.e4.preregistration import load_preregistration

TABLE = contest_classes.load_table()
PREREG = load_preregistration()


# ---------------------------------------------------------------------------
# Synthetic runs
# ---------------------------------------------------------------------------


def _cell(subject: str, opponent: str, seed: int, orientation: str, *, winner_seat: str | None = None,
          reason: str = "tick_limit", ticks: int = 1000, capture: bool = False, variant: int = 0) -> dict[str, Any]:
    seat_a, seat_b = (subject, opponent) if orientation == "candidate_first" else (opponent, subject)
    if winner_seat is None:
        outcome = "tie"
    else:
        winner = seat_a if winner_seat == "A" else seat_b
        outcome = "win" if winner == subject else "loss"
    loser = "B" if winner_seat == "A" else "A"
    return {
        "subject_id": subject, "opponent_id": opponent, "seed": seed, "orientation": orientation,
        "outcome": outcome, "termination_reason": reason, "ticks_run": ticks, "status": "completed",
        "score_subject": 1000.0 + variant, "score_opponent": 1000.0, "territory_subject": 1.0, "territory_opponent": 1.0,
        "entrant_terminations": {loser: "core_captured"} if capture and winner_seat else {},
    }


def _row(fma: Fraction | None, *, swings: int = 20, fms: float | None = 0.5, exposed: bool = True,
         completions: Iterable[dict[str, Any]] = ()) -> dict[str, Any]:
    return {"telemetry": {
        "e3": {"parity": {"status": "SCORED" if swings >= 10 else "NOT_SCOREABLE", "swing_ticks": swings,
                          "scoreable": swings >= 10, "fms": fms if swings >= 10 else None},
               "exposed": exposed, "completions": list(completions)},
        "e4": {"fma": {"status": "DEFINED", "exact": exact_text(fma)} if fma is not None else {"status": "DECIDED_EARLY"},
               "fps": {"value": None}},
    }}


def _run(field_id: str, cells: list[tuple[dict[str, Any], dict[str, Any]]], condition: str = "C") -> a.FieldRun:
    return a.make_field_run(condition, field_id, [c for c, _ in cells],
                            {f"{c['subject_id']}|{c['opponent_id']}|{c['seed']}|{c['orientation']}": r for c, r in cells})


def _pairing_cells(first: str, second: str, fma: Fraction | None, seeds: int = 4, **cell: Any) -> list[tuple]:
    return [(_cell(first, second, s, o, **cell), _row(fma)) for s in range(1, seeds + 1)
            for o in ("candidate_first", "opponent_first")]


# ---------------------------------------------------------------------------
# Transitions and census
# ---------------------------------------------------------------------------


def _summary(band: str | None) -> dict[str, Any]:
    return {"status": "DECIDED-EARLY" if band is None else "DEFINED", "band": band}


@pytest.mark.parametrize(("control", "treatment", "expected"), [
    ("strong-last", "neutral", a.NEUTRALIZED),
    ("moderate-last", "neutral", a.NEUTRALIZED),
    ("strong-last", "moderate-first", a.FOLLOWS_FINAL),
    ("moderate-last", "strong-first", a.FOLLOWS_FINAL),
    ("strong-last", "strong-last", a.STAYS),
    ("moderate-last", "moderate-last", a.STAYS),
    ("strong-last", "moderate-last", a.WEAKENED),
    ("moderate-last", "strong-last", a.STRENGTHENED),
    ("neutral", "moderate-last", a.NEW),
    ("neutral", "strong-first", a.NEW),
    ("neutral", "neutral", a.UNCHANGED_NEUTRAL),
    ("moderate-first", "neutral", a.FIRST_SIDE_CONTROL),
    ("strong-first", "strong-last", a.FIRST_SIDE_CONTROL),
    ("strong-first", "strong-first", a.FIRST_SIDE_CONTROL),
    (None, "neutral", a.DECIDED_EARLY_CLASS),
    ("strong-last", None, a.DECIDED_EARLY_CLASS),
])
def test_transition_classes_partition_in_the_registered_precedence(control: str | None, treatment: str | None,
                                                                   expected: str) -> None:
    assert a.transition_class(_summary(control), _summary(treatment)) == expected


@pytest.mark.parametrize("band", ["strong-last", "moderate-last", "neutral", "moderate-first", "strong-first", None])
def test_a_control_against_itself_is_always_an_identity_class(band: str | None) -> None:
    assert a.transition_class(_summary(band), _summary(band)) in a.IDENTITY_CLASSES


def test_the_census_counts_units_not_cells() -> None:
    rows = [{"transition": a.STAYS, "n_distinct": 1, "rate_claim_eligible": False},
            {"transition": a.STAYS, "n_distinct": 9, "rate_claim_eligible": True},
            {"transition": a.NEUTRALIZED, "n_distinct": 1, "rate_claim_eligible": False}]
    census = a.census(rows)
    assert census["units"] == 3 and census["classes"][a.STAYS] == 2 and census["classes"][a.NEUTRALIZED] == 1
    assert (census["rate_claim_eligible_units"], census["deterministic_characterizations"]) == (1, 2)
    assert set(census["classes"]) == set(a.TRANSITION_CLASSES)
    bad = a.control_census({"u": {"unit": "u", "transition": a.NEUTRALIZED}})
    assert bad["status"] == "FAIL" and bad["non_identity_units"] == ["u"]


# ---------------------------------------------------------------------------
# Units, the matchup median and P-PAR
# ---------------------------------------------------------------------------


def test_round_robin_pairs_give_two_ordered_matchups_and_mirrors_one_seed_unit() -> None:
    f1 = _run("F1", _pairing_cells("e2_sniper", "e2_disrupt_guard", Fraction(-2)))
    assert list(a.units(f1)) == ["F1|e2_disrupt_guard|e2_sniper", "F1|e2_sniper|e2_disrupt_guard"]
    f2 = _run("F2", _pairing_cells("e2_sniper", "e2_sniper_twin", Fraction(0)))
    units = a.units(f2)
    # The duplicate orientation is the relabel gate only: one unit, candidate-first cells, one per seed.
    assert list(units) == ["F2|e2_sniper|e2_sniper_twin"]
    assert [k.split("|")[3] for k in units["F2|e2_sniper|e2_sniper_twin"]] == ["candidate_first"] * 4
    f4 = _run("F4", _pairing_cells("e3_jam_sniper", "e3_jam_sniper_twin", Fraction(0)))
    assert list(a.units(f4)) == ["F4|e3_jam_sniper|e3_jam_sniper_twin"]


def test_the_matchup_median_is_exact_and_needs_half_the_cells() -> None:
    values = [Fraction(-2), Fraction(-1), Fraction(0), None]
    cells = [(_cell("e2_sniper", "e2_min_guard", s, "candidate_first"), _row(v)) for s, v in enumerate(values, 1)]
    run = _run("F1", cells)
    summary = a.fma_summary(run, sorted(run.cells))
    assert (summary["status"], summary["median_exact"], summary["band"], summary["decided_early_cells"]) == (
        "DEFINED", "-1/1", "moderate-last", 1)
    early = _run("F1", [(c, _row(None if i < 3 else Fraction(-2))) for i, (c, _) in enumerate(cells)])
    assert a.fma_summary(early, sorted(early.cells))["status"] == a.DECIDED_EARLY_CLASS
    even = _run("F1", [(c, _row(v)) for (c, _), v in zip(cells, [Fraction(-1), Fraction(0), Fraction(0),
                                                                    Fraction(1, 2)], strict=True)])
    assert a.fma_summary(even, sorted(even.cells))["median_exact"] == "0/1"


def test_p_par_takes_non_neutral_standard_units_only() -> None:
    rows = {
        "F1|x|y": {"field": "F1", "control": {"status": "DEFINED", "band": "strong-last"}},
        "F1|y|x": {"field": "F1", "control": {"status": "DEFINED", "band": "neutral"}},
        "F2|m|m_twin": {"field": "F2", "control": {"status": "DEFINED", "band": "moderate-first"}},
        "F2-P|m|m_twin": {"field": "F2-P", "control": {"status": "DEFINED", "band": "strong-last"}},
        "F4|j|x": {"field": "F4", "control": {"status": "DEFINED", "band": "strong-last"}},
        "F1|e|f": {"field": "F1", "control": {"status": "DECIDED-EARLY", "band": None}},
    }
    # F2-P and F4 are their own strata and never enter P-PAR (Sec P rule 6).
    assert a.p_par(rows) == ["F1|x|y", "F2|m|m_twin"]


def test_duplicated_seed_trajectories_are_one_distinct_transition() -> None:
    control = {f: _run(f, []) for f in matrix.FIELD_IDS}
    control["F1"] = _run("F1", _pairing_cells("e2_sniper", "e2_disrupt_guard", Fraction(-2), seeds=8))
    treatment = dict(control)
    treatment["F1"] = _run("F1", _pairing_cells("e2_sniper", "e2_disrupt_guard", Fraction(0), seeds=8), "T")
    rows = a.unit_rows(control, treatment, TABLE, fields=("F1",))
    row = rows["F1|e2_sniper|e2_disrupt_guard"]
    assert row["transition"] == a.NEUTRALIZED and row["contest_class"] == "MULTI-PASS"
    assert (row["n_distinct"], row["evidence"], row["rate_claim_eligible"]) == (1, "deterministic_characterization",
                                                                                 False)


# ---------------------------------------------------------------------------
# Seat metrics (Sec M.1)
# ---------------------------------------------------------------------------


def test_pairing_seat_metrics_follow_sec_m1() -> None:
    # Seeds 1-2: Seat A wins both orientations; seed 3: Seat B both; seed 4: X wins both (entrant-consistent).
    cells = []
    for seed, (w_xy, w_yx) in enumerate([("A", "A"), ("A", "A"), ("B", "B"), ("A", "B")], 1):
        cells.append((_cell("e2_sniper", "e2_min_guard", seed, "candidate_first", winner_seat=w_xy, variant=seed),
                      _row(Fraction(0))))
        cells.append((_cell("e2_sniper", "e2_min_guard", seed, "opponent_first", winner_seat=w_yx, variant=seed),
                      _row(Fraction(0))))
    m = a.pairing_seat_metrics(_run("F1", cells), "e2_sniper", "e2_min_guard")
    assert m["sdi"] == 0.75  # DSC on seeds 1-3
    assert m["ec"] == 0.25  # the same entrant won both orientations on seed 4 only
    assert m["os"] == 0.75
    assert m["gsb"] == 0.25  # (5 A wins - 3 B wins) / 8
    assert m["p_a"] == round(2 / 3, 6) and m["sb"] == round(1 / 3, 6)
    assert m["exact"]["sdom"] == "1/4" and m["exact"]["scd"] == "1/2"  # SDI*SB and SDI*(1-SB)


def test_no_seat_consistent_seed_gives_zero_sdom_and_scd() -> None:
    cells = [(_cell("e2_sniper", "e2_min_guard", 1, o), _row(Fraction(0))) for o in ("candidate_first", "opponent_first")]
    m = a.pairing_seat_metrics(_run("F1", cells), "e2_sniper", "e2_min_guard")
    assert (m["sdi"], m["p_a"], m["sb"], m["sdom"], m["scd"]) == (0.0, None, None, 0.0, 0.0)


def test_mirror_metrics_use_the_seed_as_the_unit() -> None:
    # The Sec M.1 example: 32/32 decisive, p_A = 19/32 -> SB 0.1875, SDom 0.1875, SCD 0.8125.
    cells = []
    for seed in range(1, 33):
        seat = "A" if seed <= 19 else "B"
        for o in ("candidate_first", "opponent_first"):
            cells.append((_cell("e2_guarded_painter", "e2_guarded_painter_twin", seed, o, winner_seat=seat,
                                reason="last_agent_standing", capture=True, variant=seed), _row(Fraction(-1))))
    m = a.mirror_seat_metrics(_run("F2", cells), "e2_guarded_painter", "e2_guarded_painter_twin")
    assert (m["decisive_share"], m["a_seeds"], m["b_seeds"], m["gsb"]) == (1.0, 19, 13, 0.1875)
    assert (m["p_a"], m["sb"], m["sdom"], m["scd"]) == (0.59375, 0.1875, 0.1875, 0.8125)
    assert m["claim"] == ["seed_conditioned", None]
    assert m["n_distinct"] == 32


def test_mirror_claims_and_the_1000_1001_check() -> None:
    dominant = {"exact": {"sdom": "19/20", "scd": "1/20"}, "p_a": 0.975}
    assert a.mirror_claim(dominant) == ("seat_dominant", "A")
    assert a.mirror_claim({"exact": {"sdom": "0/1", "scd": "0/1"}, "p_a": None}) == ("not_seat_determined", None)


# ---------------------------------------------------------------------------
# Hypotheses (Sec N) and interpretation
# ---------------------------------------------------------------------------


def _hypothesis_setup(multi_t: str, opening_t: str, *, primary_change: bool = False, companion_change: bool = True,
                      capture_rise: bool = False) -> dict[str, Any]:
    """Two P-PAR units -- a MULTI-PASS sweep and an OPENING-ONLY contest -- with chosen treatment bands."""
    values = {"strong-last": Fraction(-2), "moderate-last": Fraction(-1), "neutral": Fraction(0),
              "moderate-first": Fraction(1), "strong-first": Fraction(2)}

    def f1(multi: Fraction, opening: Fraction, cond: str, *, change: bool = False, cap: bool = False) -> a.FieldRun:
        cells = []
        for seed in (1, 2):
            for o in ("candidate_first", "opponent_first"):
                cells.append((_cell("e2_sniper", "e2_disrupt_guard", seed, o,
                                    winner_seat="A" if change else None, capture=change,
                                    reason="last_agent_standing" if change else "tick_limit"), _row(multi)))
                cells.append((_cell("e2_sniper", "e2_min_guard", seed, o, winner_seat="B" if cap else None,
                                    capture=cap, reason="last_agent_standing" if cap else "tick_limit"), _row(opening)))
        return _run("F1", cells, cond)

    mirrors = []
    for seed in range(1, 11):
        for o in ("candidate_first", "opponent_first"):
            mirrors.append((_cell("e2_min_guard", "e2_min_guard_twin", seed, o), _row(Fraction(0))))
    empty = {f: _run(f, []) for f in ("F4",)}
    f2 = _run("F2", mirrors)
    f2p = _run("F2-P", [(c, r) for c, r in mirrors if c["orientation"] == "candidate_first"])
    control = {"F1": f1(Fraction(-2), Fraction(-2), "C"), "F2": f2, "F2-P": f2p, **empty}
    treatment = {"F1": f1(values[multi_t], values[opening_t], "T", change=primary_change, cap=capture_rise),
                 "F2": f2, "F2-P": f2p, **empty}
    companion_t = {"F1": f1(values[multi_t], values[opening_t], "T", change=companion_change), "F2": f2, "F2-P": f2p,
                   **empty}
    frozen = {}
    for arm, runs in (("primary", control), ("companion", control)):
        rows = a.unit_rows(runs, None, TABLE, fields=("F1", "F2"))
        frozen[arm] = {"p_par": a.p_par(rows), "exposed_f1": a.exposed_keys(runs["F1"])}
    arms = {"primary": {"control": control, "treatment": treatment},
            "companion": {"control": control, "treatment": companion_t}}
    return {"arms": arms, "frozen": frozen}


def _evaluate(**kwargs: Any) -> dict[str, Any]:
    setup = _hypothesis_setup(**kwargs)
    return a.evaluate_hypotheses(setup["arms"], setup["frozen"], PREREG, TABLE)


def _statuses(result: dict[str, Any]) -> dict[str, str]:
    return dict(result["interpretation_inputs"])


def test_p_par_here_is_one_multi_pass_and_one_opening_unit_per_orientation() -> None:
    setup = _hypothesis_setup(multi_t="neutral", opening_t="strong-last")
    assert setup["frozen"]["primary"]["p_par"] == [
        "F1|e2_disrupt_guard|e2_sniper", "F1|e2_min_guard|e2_sniper",
        "F1|e2_sniper|e2_disrupt_guard", "F1|e2_sniper|e2_min_guard"]


def test_h1_h3_not_h2_is_the_two_mechanism_row() -> None:
    result = _evaluate(multi_t="neutral", opening_t="strong-last")
    s = _statuses(result)
    assert (s["E4-H1"], s["E4-H2"], s["E4-H3"], s["E4-H0"]) == ("SUPPORTED", "REFUTED", "SUPPORTED", "REFUTED")
    assert result["interpretation"]["applies"][0] == "H1 ∧ H3 ∧ ¬H2"
    assert result["E4-H1"]["multi_pass_neutralized_or_weakened"]["share_exact"] == "1/1"


def test_h2_follows_the_final_chunk() -> None:
    s = _statuses(_evaluate(multi_t="moderate-first", opening_t="strong-last"))
    assert (s["E4-H1"], s["E4-H2"]) == ("REFUTED", "SUPPORTED")
    assert "H2" in _evaluate(multi_t="moderate-first", opening_t="strong-last")["interpretation"]["applies"]


def test_h0_no_structural_effect_and_the_none_row() -> None:
    result = _evaluate(multi_t="strong-last", opening_t="strong-last")
    s = _statuses(result)
    assert (s["E4-H0"], s["E4-H1"], s["E4-H3"]) == ("SUPPORTED", "REFUTED", "SUPPORTED")
    assert "H0" in result["interpretation"]["applies"] and "¬H1 ∧ H3" in result["interpretation"]["applies"]
    weak = _evaluate(multi_t="moderate-last", opening_t="moderate-last")
    assert _statuses(weak)["E4-H3"] == "REFUTED" and _statuses(weak)["E4-H1"] == "SUPPORTED"
    # H1 supported but H3 refuted and H2 refuted: the second row.
    assert weak["interpretation"]["applies"][0] == "H1 ∧ ¬H3 ∧ ¬H2"


def test_neither_satisfies_neither_side_so_no_row_applies() -> None:
    # The MULTI-PASS units are neutralized, but the OPENING-ONLY ones follow the final chunk,
    # so overall FOLLOWS-FINAL is 1/2 > 1/10: H1 is NEITHER, which satisfies no row.
    result = _evaluate(multi_t="neutral", opening_t="moderate-first")
    s = _statuses(result)
    assert s["E4-H3"] == "REFUTED" and s["E4-H1"] == "NEITHER"
    assert result["interpretation"]["applies"] == ["none"]


def test_h4_masking_needs_the_companion_to_change_and_the_primary_not_to() -> None:
    assert _statuses(_evaluate(multi_t="neutral", opening_t="strong-last"))["E4-H4"] == "SUPPORTED"
    assert _statuses(_evaluate(multi_t="neutral", opening_t="strong-last", primary_change=True))["E4-H4"] == "NEITHER"
    assert _statuses(_evaluate(multi_t="neutral", opening_t="strong-last", companion_change=False))["E4-H4"] == "REFUTED"


def test_h5_and_h6_flags() -> None:
    result = _evaluate(multi_t="neutral", opening_t="strong-last", capture_rise=True)
    s = _statuses(result)
    assert s["E4-H5"] == "SUPPORTED" and result["E4-H5"]["control_non_capture_exposed_f1"]["share_exact"] == "1/2"
    assert s["E4-H6"] == "REFUTED"
    assert "H5, H6, H8" in result["interpretation"]["applies"]
    assert result["E4-H6"]["static_neutralization"]["share_exact"] == "0/1"


def test_h7_and_h8_read_the_treatment_mirrors() -> None:
    result = _evaluate(multi_t="neutral", opening_t="strong-last")
    # Ties everywhere: no seat-dependent unit at all, and no 1000/1001 disagreement.
    assert _statuses(result)["E4-H7"] == "REFUTED" and _statuses(result)["E4-H8"] == "REFUTED"
    assert result["E4-H8"]["mirrors"][0]["label"] == a.PARITY_ROBUST


def test_a_1000_1001_claim_disagreement_is_flagged() -> None:
    # Seat A wins every seed at 1000 ticks (seat-dominant A); every seed is a tie at 1001.
    at_1000 = _run("F2", [(_cell("e2_min_guard", "e2_min_guard_twin", s, "candidate_first", winner_seat="A",
                                 reason="last_agent_standing", capture=True), _row(Fraction(0))) for s in range(1, 9)])
    at_1001 = _run("F2-P", [(_cell("e2_min_guard", "e2_min_guard_twin", s, "candidate_first", ticks=1001),
                             _row(Fraction(0))) for s in range(1, 9)])
    (row,) = a.mirror_parity(at_1000, at_1001)
    assert (row["claim_1000"], row["claim_1001"]) == (["seat_dominant", "A"], ["not_seat_determined", None])
    assert row["label"] == a.TICK_LIMIT_PARITY_DEPENDENT


def test_d9_prime_is_a_stop_not_a_result() -> None:
    setup = _hypothesis_setup(multi_t="neutral", opening_t="strong-last")
    treatment = setup["arms"]["primary"]["treatment"]
    key = next(iter(treatment["F1"].telemetry))
    treatment["F1"].telemetry[key]["telemetry"]["e3"]["completions"].append(  # type: ignore[index]
        {"victim": "B", "victim_name": "e2_disrupt_guard", "tick": 9, "capturer": "A"})
    result = a.evaluate_hypotheses(setup["arms"], setup["frozen"], PREREG, TABLE)
    assert result["D9-PRIME"]["status"] == a.STOP and result["D9-PRIME"]["t_e4_completions"] == 1
    assert result["interpretation"]["applies"] == [] and "D9'" in result["interpretation"]["stop"]


def test_the_control_against_itself_is_all_identity_classes() -> None:
    setup = _hypothesis_setup(multi_t="neutral", opening_t="strong-last")
    control = setup["arms"]["primary"]["control"]
    census = a.control_census(a.unit_rows(control, control, TABLE, fields=("F1", "F2")))
    assert census["status"] == "PASS" and census["classes"][a.STAYS] == 4
