"""Regression tests for the V6 experiment-harness analysis defects HD-1, HD-2,
HD-3 and HD-6 (docs/research/v6/V6_E2_CAPTURE_HOLD_DESIGN_REVIEW.md Sec I.4).

Each defect was demonstrated by the design review against the pre-E2
harness; each test below fails on that harness and passes on the remediated
one. The inputs are synthetic outcome records -- the analyzer's own input
shape -- because these are properties of the statistics, not of any match;
the capture telemetry that feeds the E2 analysis is tested against real
replays in test_v6_e2_capture_analyzer.py.
"""

from __future__ import annotations

from itertools import combinations
from typing import Any

import pytest

from tools.research.v6.experiment_harness import (
    FRAGILE_EDGE_MARGIN,
    analyze_experiment_condition,
    analyze_mirror_condition,
    bootstrap_residual_intervals,
    bootstrap_rmsr_over_distinct_trajectories,
    compute_directed_3_cycles,
    compute_pairwise_record,
    count_distinct_trajectories,
    decision_tick_summary,
    distinct_pairwise_evidence,
    fit_bradley_terry,
    outcome_transitions,
    seat_determination_index,
    trajectory_key,
)

ORIENTATIONS = ("candidate_first", "opponent_first")


def cell(
    subject: str,
    opponent: str,
    seed: int,
    orientation: str,
    result: str,
    *,
    ticks: int = 1,
    reason: str | None = None,
    scores: tuple[float, float] = (6.0, 0.0),
) -> dict[str, Any]:
    """One outcome record. ``result`` is the winning *seat* ("A"/"B") or "tie";
    ``scores`` are (winner, loser) or, for a tie, (seat A, seat B)."""
    seat_a, seat_b = (subject, opponent) if orientation == "candidate_first" else (opponent, subject)
    if result == "tie":
        outcome = "tie"
        score = {seat_a: scores[0], seat_b: scores[1]}
    else:
        winner = seat_a if result == "A" else seat_b
        loser = seat_b if result == "A" else seat_a
        outcome = "win" if winner == subject else "loss"
        score = {winner: scores[0], loser: scores[1]}
    return {
        "subject_id": subject,
        "opponent_id": opponent,
        "seed": seed,
        "orientation": orientation,
        "status": "completed",
        "outcome": outcome,
        "ticks_run": ticks,
        "termination_reason": reason
        or ("tick_limit" if ticks >= 1000 else "all_agents_dead" if result == "tie" else "last_agent_standing"),
        "score_subject": score[subject],
        "score_opponent": score[opponent],
        "territory_subject": 1.5,
        "territory_opponent": 1.5,
    }


def seat_a_always_wins(field: tuple[str, ...], seeds: range) -> list[dict[str, Any]]:
    return [
        cell(a, b, seed, orientation, "A")
        for a, b in combinations(field, 2)
        for seed in seeds
        for orientation in ORIENTATIONS
    ]


# ---------------------------------------------------------------------------
# HD-1: seat-blind analysis
# ---------------------------------------------------------------------------


def test_hd1_seat_a_always_winning_field_is_reported_as_seat_determined() -> None:
    field = ("w", "x", "y", "z")
    cells = seat_a_always_wins(field, range(1, 33))
    analysis = analyze_experiment_condition(cells, field)

    # Precondition, and the exact failure the review demonstrated: the
    # seat-pooled view alone looks like a perfectly balanced field.
    pooled = analysis["tables"]["pooled"]
    assert pooled["bradley_terry"]["ratings"] == dict.fromkeys(field, 1500.0)
    assert pooled["rmsr"] == 0.0
    assert pooled["cycle_count"] == 0

    # The headline is now seat-conditioned and shows the pathology.
    pathology = analysis["seat_pathology"]
    assert pathology["all_pairings_seat_determined"] is True
    assert pathology["seat_determined_share"] == 1.0
    assert (pathology["seat_a_win_rate"], pathology["seat_b_win_rate"]) == (1.0, 0.0)
    assert pathology["max_abs_seat_bias"] == 1.0
    assert [p["entrants"] for p in pathology["seat_determined_pairings"]] == [
        list(pair) for pair in combinations(field, 2)
    ]
    for matchup in analysis["matchups"]:
        assert matchup["sdi"]["sdi"] == 1.0
        assert matchup["sdi"]["favoured_seat"] == "A"
        assert matchup["seat_bias"] == 1.0
        # 32 seeds, one behaviour: a characterization, not a 32-sample rate.
        assert matchup["sdi"]["n_seed_pairs"] == 32
        assert matchup["sdi"]["n_distinct"] == 1
        assert matchup["sdi"]["evidence"] == "deterministic_characterization"
        for entrant in matchup["entrants"]:
            sides = matchup["by_entrant"][entrant]
            assert (sides["seat_a"]["p_win"], sides["seat_b"]["p_win"]) == (1.0, 0.0)
            assert sides["seat_a"]["n_runs"] == sides["seat_b"]["n_runs"] == 32
            assert sides["seat_a"]["n_distinct"] == sides["seat_b"]["n_distinct"] == 1

    # The per-seat tables are opposite total orders, so neither is a
    # balanced field, and the pooled view says it is subordinate.
    seat_a, seat_b = analysis["tables"]["seat_a"], analysis["tables"]["seat_b"]
    assert seat_a["bradley_terry"]["components"] == [["w"], ["x"], ["y"], ["z"]]
    assert seat_b["bradley_terry"]["components"] == [["z"], ["y"], ["x"], ["w"]]
    assert seat_a["ratings_authoritative"] is seat_b["ratings_authoritative"] is False
    assert pooled["subordinate"] is True
    assert "SDI >= 0.9" in pooled["warning"]
    assert "6 pairing(s)" in pooled["warning"]


def test_hd1_sdi_matches_the_preregistered_definition() -> None:
    # Seeds 1-3: Seat A wins both orientations; seed 4: Seat B wins both;
    # seed 5: the first-listed entrant wins both (not seat-determined).
    cells = []
    for seed in (1, 2, 3):
        cells += [cell("p", "q", seed, o, "A", ticks=seed) for o in ORIENTATIONS]
    cells += [cell("p", "q", 4, o, "B", ticks=9) for o in ORIENTATIONS]
    cells += [cell("p", "q", 5, "candidate_first", "A", ticks=7), cell("p", "q", 5, "opponent_first", "B", ticks=7)]
    sdi = seat_determination_index(cells)

    # Five distinct seed trajectories (ticks differ): 3 A-determined,
    # 1 B-determined, 1 not.
    assert sdi["n_distinct"] == 5
    assert (sdi["sdi"], sdi["sdi_seat_a"], sdi["sdi_seat_b"]) == (0.8, 0.6, 0.2)
    assert sdi["favoured_seat"] == "A"
    assert sdi["seat_determined"] is False

    # Duplicating seed 1's trajectory under 20 more seeds changes the
    # seed-weighted descriptive value but not the registered SDI.
    duplicated = cells + [cell("p", "q", seed, o, "A", ticks=1) for seed in range(10, 30) for o in ORIENTATIONS]
    again = seat_determination_index(duplicated)
    assert (again["sdi"], again["sdi_seat_a"], again["sdi_seat_b"], again["n_distinct"]) == (0.8, 0.6, 0.2, 5)
    assert again["seed_weighted_descriptive"]["sdi"] != sdi["seed_weighted_descriptive"]["sdi"]


def test_hd1_seat_determination_toward_seat_b_is_detected() -> None:
    cells = [cell("p", "q", seed, o, "B") for seed in range(1, 9) for o in ORIENTATIONS]
    sdi = seat_determination_index(cells)
    assert (sdi["sdi"], sdi["favoured_seat"], sdi["seat_determined"]) == (1.0, "B", True)


def test_hd4_mirror_seat_bias_is_reported_per_mirror_and_never_rated() -> None:
    cells = [cell("m", "m_twin", seed, o, "A") for seed in range(1, 33) for o in ORIENTATIONS]
    cells += [cell("n", "n_twin", seed, o, "tie", ticks=1000, scores=(3.0, 3.0)) for seed in range(1, 33) for o in ORIENTATIONS]
    report = analyze_mirror_condition(cells, [("m", "m_twin"), ("n", "n_twin")])

    m, n = report["mirrors"]
    assert (m["seat_a_wins"], m["seat_b_wins"], m["ties"], m["n_runs"]) == (64, 0, 0, 64)
    assert (m["seat_a_win_rate"], m["seat_b_win_rate"], m["mirror_seat_bias"]) == (1.0, 0.0, 1.0)
    # One trajectory per orientation (seat ids are part of the key).
    assert m["n_distinct"] == 2 and m["evidence"] == "limited_distinct_trajectories"
    assert m["sdi"]["sdi"] == 1.0 and m["sdi"]["favoured_seat"] == "A"
    assert (n["mirror_seat_bias"], n["sdi"]["sdi"], n["sdi"]["favoured_seat"]) == (0.0, 0.0, "none")
    assert report["seat_determined_mirrors"] == ["m"]
    assert report["max_abs_mirror_seat_bias"] == 1.0
    assert "ratings" not in report and "tables" not in report


# ---------------------------------------------------------------------------
# HD-2: seeds are not automatically independent
# ---------------------------------------------------------------------------


def test_hd2_thirty_two_identical_seeds_are_one_distinct_trajectory() -> None:
    cells = [cell("p", "q", seed, "candidate_first", "A", ticks=2) for seed in range(1, 33)]
    assert count_distinct_trajectories(cells) == 1
    analysis = analyze_experiment_condition(cells, ("p", "q"))
    assert analysis["effective_sample"] == {
        "n_runs": 32,
        "n_seeds": 32,
        "n_distinct": 1,
        "evidence": "deterministic_characterization",
    }
    record = compute_pairwise_record(cells, ("p", "q"))
    assert (record[("p", "q")]["played"], record[("p", "q")]["n_distinct"]) == (32, 1)
    wins, games = distinct_pairwise_evidence(cells, ("p", "q"))
    assert (wins[("p", "q")], games[("p", "q")]) == (1.0, 1)


def test_hd2_genuinely_different_trajectories_are_counted() -> None:
    cells = [cell("p", "q", seed, "candidate_first", "A", ticks=2 + seed % 3) for seed in range(1, 33)]
    cells += [cell("p", "q", 40, "candidate_first", "B", ticks=2)]
    # Same ticks, different final scores: still distinct.
    cells += [cell("p", "q", 41, "candidate_first", "A", ticks=2, scores=(7.0, 1.0))]
    assert count_distinct_trajectories(cells) == 5
    # The same outcome in the other orientation is a different trajectory.
    assert trajectory_key(cell("p", "q", 1, "candidate_first", "A")) != trajectory_key(
        cell("p", "q", 1, "opponent_first", "B")
    )
    # Seeds and start addresses are not part of the key.
    moved = dict(cell("p", "q", 1, "candidate_first", "A"), seed=99, subject_start=5, opponent_start=300)
    assert trajectory_key(moved) == trajectory_key(cell("p", "q", 1, "candidate_first", "A"))


def test_hd2_bootstrap_on_deterministic_data_is_not_estimable() -> None:
    field = ("w", "x", "y")
    cells = seat_a_always_wins(field, range(1, 33))
    for subset in (
        [c for c in cells if c["orientation"] == "candidate_first"],
        [c for c in cells if c["orientation"] == "opponent_first"],
    ):
        result = bootstrap_rmsr_over_distinct_trajectories(subset, field, n_bootstraps=50)
        assert result["status"] == "not_estimable_deterministic"
        assert result["se"] is None
        assert result["n_distinct"] == 3


def _varied_field() -> list[dict[str, Any]]:
    """Three entrants; every pairing has several distinct trajectories with outcome variation."""
    cells = []
    plan = {("w", "x"): "AABAB", ("w", "y"): "AAABT", ("x", "y"): "ABBTA"}
    for (a, b), results in plan.items():
        for index, result in enumerate(results):
            cells.append(cell(a, b, index + 1, "candidate_first", "tie" if result == "T" else result, ticks=10 + index, scores=(5.0, 5.0) if result == "T" else (6.0, 0.0)))
    return cells


def test_hd2_duplicate_seeds_do_not_change_confidence_estimates() -> None:
    field = ("w", "x", "y")
    base = _varied_field()
    # Re-run one trajectory of every pairing under 30 extra seeds each.
    duplicated = list(base) + [
        dict(c, seed=seed) for c in base if c["ticks_run"] == 10 for seed in range(100, 130)
    ]
    assert count_distinct_trajectories(duplicated) == count_distinct_trajectories(base) == 15

    first = bootstrap_rmsr_over_distinct_trajectories(base, field, n_bootstraps=100)
    second = bootstrap_rmsr_over_distinct_trajectories(duplicated, field, n_bootstraps=100)
    assert first["status"] == "estimated" and first["se"] is not None and first["se"] > 0
    assert first == second

    intervals_first = bootstrap_residual_intervals(base, field, n_bootstraps=100)
    intervals_second = bootstrap_residual_intervals(duplicated, field, n_bootstraps=100)
    assert intervals_first == intervals_second
    wins_a, games_a = distinct_pairwise_evidence(base, field)
    wins_b, games_b = distinct_pairwise_evidence(duplicated, field)
    assert (wins_a, games_a) == (wins_b, games_b)
    assert fit_bradley_terry(wins_a, games_a, field) == fit_bradley_terry(wins_b, games_b, field)


def test_hd2_residuals_below_eight_distinct_trajectories_never_count_as_significant() -> None:
    # A rock-paper-scissors cycle. Pairings with 8 distinct trajectories
    # (ticks vary) are eligible; the same cycle on 2 trajectories is not.
    def cycle(n: int) -> list[dict[str, Any]]:
        return [
            cell(a, b, k, "candidate_first", "A", ticks=10 + k)
            for a, b in (("r", "s"), ("s", "p"), ("p", "r"))
            for k in range(n)
        ]

    wide = bootstrap_residual_intervals(cycle(8), ("r", "s", "p"), n_bootstraps=200)
    narrow = bootstrap_residual_intervals(cycle(2), ("r", "s", "p"), n_bootstraps=200)
    assert wide["significant"] == ["r_vs_s", "r_vs_p", "s_vs_p"]
    assert all(row["eligible"] and abs(row["residual"]) == 0.5 for row in wide["residuals"].values())
    assert narrow["significant"] == []
    assert all(not row["eligible"] and row["evidence"] == "limited_distinct_trajectories" for row in narrow["residuals"].values())


# ---------------------------------------------------------------------------
# HD-3: Bradley-Terry convergence
# ---------------------------------------------------------------------------


def _evidence(results: dict[tuple[str, str], tuple[float, int]]) -> tuple[dict[tuple[str, str], float], dict[tuple[str, str], int]]:
    wins: dict[tuple[str, str], float] = {}
    games: dict[tuple[str, str], int] = {}
    for (a, b), (won, n) in results.items():
        wins[(a, b)], wins[(b, a)] = won, n - won
        games[(a, b)] = games[(b, a)] = n
    return wins, games


def test_hd3_balanced_field_converges_quickly_to_equal_ratings() -> None:
    field = ("a", "b", "c", "d")
    wins, games = _evidence({pair: (1.0, 2) for pair in combinations(field, 2)})
    fit = fit_bradley_terry(wins, games, field)
    assert fit.converged and fit.authoritative and not fit.separable
    assert fit.iterations <= 5
    assert fit.ratings == dict.fromkeys(field, 1500.0)


def test_hd3_ordinary_transitive_ladder_converges_to_stable_ordered_ratings() -> None:
    field = ("a", "b", "c", "d")
    wins, games = _evidence({pair: (3.0, 4) for pair in combinations(field, 2)})
    fits = [fit_bradley_terry(wins, games, field, max_iterations=cap) for cap in (50, 500, 5000, 100_000)]
    assert all(fit.converged and fit.authoritative for fit in fits)
    assert len({tuple(sorted(fit.ratings.items())) for fit in fits}) == 1
    ratings = fits[-1].ratings
    assert ratings["a"] > ratings["b"] > ratings["c"] > ratings["d"]
    assert fits[-1].to_dict()["ratings"] == ratings


def test_hd3_separable_blowout_reports_components_not_unstable_ratings() -> None:
    field = tuple("abcdefg")
    wins, games = _evidence({pair: (4.0, 4) for pair in combinations(field, 2)})
    fits = [fit_bradley_terry(wins, games, field, max_iterations=cap) for cap in (50, 500, 5000)]
    # The review's evidence: this data gave G = 945.9 / 580.2 / 410.6 at
    # 50 / 500 / 5000 fixed iterations. Now every cap gives the same
    # answer, and it says the MLE does not exist.
    assert len({fit.components for fit in fits}) == 1
    fit = fits[0]
    assert fit.separable and not fit.authoritative and fit.converged
    assert fit.components == tuple((name,) for name in field)
    view = fit.to_dict()
    assert view["ratings"] is None and view["within_component_ratings"] == []
    assert fit.expected("a", "g") == 1.0 and fit.expected("g", "a") == 0.0


def test_hd3_near_separable_data_flags_non_convergence_instead_of_drifting() -> None:
    field = tuple("abcdefg")
    results = {pair: (4.0, 4) for pair in combinations(field, 2)}
    results[("a", "g")] = (3.5, 4)  # one tie keeps the field strongly connected
    wins, games = _evidence(results)
    early = fit_bradley_terry(wins, games, field, max_iterations=50)
    later = fit_bradley_terry(wins, games, field, max_iterations=500)
    full = fit_bradley_terry(wins, games, field, max_iterations=5000)
    default = fit_bradley_terry(wins, games, field)
    assert not early.converged and not early.authoritative and early.iterations == 50
    assert not later.converged
    assert full.converged and full.authoritative and full.iterations < 5000
    assert full.ratings == default.ratings
    assert early.ratings != full.ratings  # exactly the values that must not pass as final


def test_hd3_fit_is_deterministic_and_order_independent() -> None:
    field = ("a", "b", "c")
    results = {("a", "b"): (2.0, 3), ("a", "c"): (1.5, 3), ("b", "c"): (1.0, 3)}
    wins, games = _evidence(results)
    reversed_wins = dict(reversed(list(wins.items())))
    assert fit_bradley_terry(wins, games, field) == fit_bradley_terry(reversed_wins, games, field)


def test_hd3_residuals_stay_interpretable_on_separable_data() -> None:
    # A perfectly transitive blowout has RMSR 0; the pooled cycle stays high.
    transitive = [cell(a, b, 1, "candidate_first", "A") for a, b in combinations(("a", "b", "c"), 2)]
    cyclic = [cell(a, b, 1, "candidate_first", "A") for a, b in (("r", "s"), ("s", "p"), ("p", "r"))]
    t = analyze_experiment_condition(transitive, ("a", "b", "c"))["tables"]["seat_a"]
    c = analyze_experiment_condition(cyclic, ("r", "s", "p"))["tables"]["seat_a"]
    assert t["rmsr"] == 0.0 and t["cycle_count"] == 0 and t["upset_reversals"] == []
    assert c["rmsr"] == 0.5 and c["robust_cycle_count"] == 1


# ---------------------------------------------------------------------------
# Cycles: margins and fragility (review Sec I.3)
# ---------------------------------------------------------------------------


def test_cycles_list_edge_margins_and_flag_fragile_edges() -> None:
    field = ("r", "s", "p")
    wins, games = _evidence({("r", "s"): (11.0, 20), ("s", "p"): (20.0, 20), ("p", "r"): (20.0, 20)})
    (fragile,) = compute_directed_3_cycles(wins, games, field)
    assert fragile["cycle"] == ["r", "s", "p"]
    assert [edge["margin"] for edge in fragile["edges"]] == [0.05, 0.5, 0.5]
    assert fragile["min_margin"] == FRAGILE_EDGE_MARGIN and fragile["fragile"] is True
    wins, games = _evidence({("r", "s"): (12.0, 20), ("s", "p"): (20.0, 20), ("p", "r"): (20.0, 20)})
    (robust,) = compute_directed_3_cycles(wins, games, field)
    assert robust["fragile"] is False
    # A tie edge (exactly 0.5) is not a directed edge.
    wins, games = _evidence({("r", "s"): (10.0, 20), ("s", "p"): (20.0, 20), ("p", "r"): (20.0, 20)})
    assert compute_directed_3_cycles(wins, games, field) == []


# ---------------------------------------------------------------------------
# HD-6: decision ticks
# ---------------------------------------------------------------------------


def test_hd6_tick_limit_matches_do_not_enter_the_decisive_median() -> None:
    decisive = [cell("p", "q", seed, "candidate_first", "A", ticks=t) for seed, t in ((1, 2), (2, 3), (3, 5))]
    mutual = [cell("p", "q", 4, "candidate_first", "tie", ticks=40, scores=(5.0, 5.0))]
    limit = [
        cell("p", "q", 100 + i, "candidate_first", "tie" if i % 2 else "B", ticks=1000, scores=(9.0, 9.0) if i % 2 else (9.0, 8.0))
        for i in range(100)
    ]
    alone = decision_tick_summary(decisive)
    mixed = decision_tick_summary(decisive + mutual + limit, tick_limit=1000)

    assert (alone["decisive"]["median"], alone["decisive"]["q1"], alone["decisive"]["q3"]) == (3.0, 2.5, 4.0)
    assert mixed["decisive"] == alone["decisive"]
    assert mixed["decisive"]["n_runs"] == 3 and mixed["decisive"]["n_distinct"] == 3
    assert mixed["mutual_elimination"]["n_runs"] == 1 and mixed["mutual_elimination"]["median"] == 40.0
    tick_limit = mixed["tick_limit"]
    assert (tick_limit["n_runs"], tick_limit["fraction"], tick_limit["lengths"]) == (100, round(100 / 104, 6), [1000])
    assert (tick_limit["seat_b_score_wins"], tick_limit["ties"], tick_limit["seat_a_score_wins"]) == (50, 50, 0)
    assert tick_limit["n_distinct"] == 2
    # A score win at the tick limit is not a decision at tick 1000.
    assert 1000 not in (mixed["decisive"]["min"], mixed["decisive"]["max"])


def test_hd6_condition_analysis_reports_decisive_ticks_separately() -> None:
    cells = [cell("p", "q", s, "candidate_first", "A", ticks=4) for s in range(1, 5)]
    cells += [cell("p", "q", s, "candidate_first", "tie", ticks=1000, scores=(3.0, 3.0)) for s in range(5, 50)]
    ticks = analyze_experiment_condition(cells, ("p", "q"), tick_limit=1000)["decision_ticks"]
    assert ticks["decisive"]["median"] == 4.0
    assert ticks["tick_limit"]["n_runs"] == 45


# ---------------------------------------------------------------------------
# Cross-condition transitions (V4 -> E2 tables)
# ---------------------------------------------------------------------------


def test_outcome_transitions_match_cells_and_count_one_tick_delays() -> None:
    control = [cell("p", "q", s, o, "A", ticks=1) for s in (1, 2, 3) for o in ORIENTATIONS]
    treatment = [cell("p", "q", 1, o, "A", ticks=2) for o in ORIENTATIONS]
    treatment += [cell("p", "q", 2, o, "A", ticks=5) for o in ORIENTATIONS]
    treatment += [cell("p", "q", 3, o, "tie", ticks=1000, scores=(4.0, 4.0)) for o in ORIENTATIONS]
    result = outcome_transitions(control, treatment)
    assert result["matched_cells"] == 6 and result["unmatched_control"] == result["unmatched_treatment"] == 0
    assert result["matrix"]["A"] == {"A": 4, "B": 0, "tie": 2, "other": 0}
    assert (result["control_decisive"], result["winner_kept"], result["winner_kept_one_tick_later"]) == (6, 4, 2)
    assert result["winner_kept_one_tick_later_rate"] == round(2 / 6, 6)


@pytest.mark.parametrize("field", [("a", "b"), ("a", "b", "c")])
def test_pooled_metrics_are_kept(field: tuple[str, ...]) -> None:
    cells = seat_a_always_wins(field, range(1, 3))
    tables = analyze_experiment_condition(cells, field)["tables"]
    assert set(tables) == {"seat_a", "seat_b", "pooled"}
    assert {"rmsr", "cycles", "upset_reversals", "bradley_terry", "matchup_residuals"} <= set(tables["pooled"])
