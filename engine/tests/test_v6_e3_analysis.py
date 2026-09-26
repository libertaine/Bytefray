"""E3 hypothesis criteria and evidence rules (design review Sec J, Sec M; ``preregistration.json``).

The criteria are pure functions of harness cell records and telemetry rows,
so each branch is exercised on small constructed inputs whose expected
status follows directly from the frozen criterion; the same functions run on
real control corpora in ``test_v6_e3_pipeline.py``.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

import pytest

from tools.research.v6.e3 import analyze_e3 as a
from tools.research.v6.e3 import matrix
from tools.research.v6.e3.action_parity import parity_score
from tools.research.v6.e3.gates import D9StopError, d9_completions, require_d9
from tools.research.v6.e3.preregistration import load_preregistration

PREREG = load_preregistration()
CF, OF = "candidate_first", "opponent_first"


def cell(subject: str, opponent: str, seed: int, orientation: str, *, seat_winner: str | None,
         reason: str = "last_agent_standing", ticks: int = 5, variant: int = 0) -> dict[str, Any]:
    """A harness cell record. ``seat_winner``: "A", "B" or None (tie)."""
    seat_a, seat_b = (subject, opponent) if orientation == CF else (opponent, subject)
    winner = None if seat_winner is None else (seat_a if seat_winner == "A" else seat_b)
    outcome = "tie" if winner is None else "win" if winner == subject else "loss"
    return {"subject_id": subject, "opponent_id": opponent, "seed": seed, "orientation": orientation,
            "outcome": outcome, "status": "completed", "ticks_run": ticks, "termination_reason": reason,
            "score_subject": float(variant), "score_opponent": 0.0, "territory_subject": 0, "territory_opponent": 0,
            "entrant_terminations": {}, "seat_a_id": "A", "seat_b_id": "B"}


def telemetry(*, exposed: bool = True, fms_favouring: int | None = None, swings: int = 20,
              recoveries: int = 0, first_hit: int | None = 1, completions: Iterable[str] = (),
              names: tuple[str, str] = ("x", "y")) -> dict[str, Any]:
    parity = parity_score(swings if fms_favouring is not None else 0, fms_favouring or 0)
    role = {"entrant_ticks": 1, "offered": 8, "executed": 8, "histogram": [0] * 8 + [1],
            "min_executed_alive_throughout": 8, "adf_n": 1, "adf_sum": 0.0}
    return {
        "exposed": exposed,
        "first_hit_tick": first_hit,
        "parity": parity,
        "both_alive_ticks": 1,
        "exclusive_ticks": 0,
        "checks": {"cpu_statistics_match": True},
        "seats": {
            seat: {"name": name, "capture": {"recoveries": recoveries if seat == "B" else 0},
                   "phase_lock": {"category": "NO_ZERO_CORE_TICKS", "two_sided": None, "direction": None},
                   "zero_action_live_ticks": 0, "g4_violations": 0, "roles": {"first": role, "second": role}}
            for seat, name in zip(("A", "B"), names, strict=True)
        },
        "completions": [{"victim": "B", "victim_name": victim, "tick": 3, "capturer": "A"} for victim in completions],
    }


def run(field_id: str, rows: list[tuple[dict[str, Any], dict[str, Any]]], condition: str = "C") -> a.FieldRun:
    cells = [c for c, _ in rows]
    return a.make_field_run(condition, field_id, cells,
                            {f"{c['subject_id']}|{c['opponent_id']}|{c['seed']}|{c['orientation']}": {"telemetry": t}
                             for c, t in rows})


# ---------------------------------------------------------------------------
# PM-3 outcome classes and O-UNIT
# ---------------------------------------------------------------------------


def test_outcome_classes() -> None:
    assert a.outcome_class(cell("p", "q", 1, CF, seat_winner="A")) == a.A_WIN
    assert a.outcome_class(cell("p", "q", 1, OF, seat_winner="A")) == a.A_WIN
    assert a.outcome_class(cell("p", "q", 1, OF, seat_winner="B", reason="tick_limit", ticks=1000)) == a.B_WIN
    assert a.outcome_class(cell("p", "q", 1, CF, seat_winner=None, reason="tick_limit", ticks=1000)) == a.TICK_LIMIT_TIE
    assert a.outcome_class(cell("p", "q", 1, CF, seat_winner=None, reason="all_agents_dead")) == a.MUTUAL_ELIMINATION


def test_duplicated_seed_trajectories_are_one_distinct_transition() -> None:
    before = run("F1", [(cell("p", "q", s, CF, seat_winner="A"), telemetry()) for s in range(1, 33)])
    after = run("F1", [(cell("p", "q", s, CF, seat_winner=None, reason="tick_limit", ticks=1000), telemetry())
                       for s in range(1, 33)])
    items = [("F1", k) for k in before.cells]
    moves = a.transitions({"F1": before}, {"F1": after}, items)
    assert (moves["matched"], moves["unchanged"], moves["n_distinct"]) == (32, 0, 1)
    assert moves["evidence"] == "deterministic_characterization" and moves["rate_claim_eligible"] is False
    assert moves["matrix"][a.A_WIN][a.TICK_LIMIT_TIE] == 32


# ---------------------------------------------------------------------------
# PM-1 medians (O-PARITY-MEDIANS)
# ---------------------------------------------------------------------------


def test_parity_medians_exclude_but_count_not_scoreable_cells() -> None:
    rows = [(cell("p", "q", s, CF, seat_winner=None, reason="tick_limit", ticks=1000, variant=s),
             telemetry(fms_favouring=0)) for s in range(1, 6)]
    rows.append((cell("p", "q", 6, CF, seat_winner=None, reason="tick_limit", ticks=1000, variant=6),
                 telemetry(fms_favouring=20, swings=9)))
    runs = {"F1": run("F1", rows)}
    summary = a.parity_summary(runs, [("F1", k) for k in runs["F1"].cells])
    assert (summary["cells"], summary["scoreable"], summary["not_scoreable"]) == (6, 5, 1)
    assert (summary["median_pd"], summary["median_fms"]) == (1.0, 0.0)
    assert summary["directions"] == {"last_mover_dominated": 5, "not_scoreable": 1}
    assert summary["n_distinct"] == 5


# ---------------------------------------------------------------------------
# Full criterion evaluation on a constructed arm
# ---------------------------------------------------------------------------

UNITS = [("F1", ("v4_probe", "e2_sniper")), ("F1", ("v4_probe", "e2_spread_sniper")),
         ("F1", ("e2_sniper", "e2_spread_sniper")), ("F2", ("v4_probe", "v4_probe_twin")),
         ("F2", ("e2_sniper", "e2_sniper_twin")), ("F2", ("e2_guarded_painter", "e2_guarded_painter_twin"))]


def pairing(a_: str, b_: str, *, determined: bool, seeds: Iterable[int] = range(1, 3),
            reason: str = "last_agent_standing", tel: dict[str, Any] | None = None) -> list[tuple[dict, dict]]:
    """Both orientations per seed: Seat A wins both (seat-determined) or the subject wins both (not)."""
    out = []
    for s in seeds:
        for orientation in (CF, OF):
            winner = "A" if determined else ("A" if orientation == CF else "B")
            ticks = 1000 if reason == "tick_limit" else 5
            out.append((cell(a_, b_, s, orientation, seat_winner=winner, reason=reason, ticks=ticks),
                        dict(tel or telemetry())))
    return out


def arm(*, units_determined: bool, f2p_determined: bool | None = None, stalemate_favouring: int = 20,
        repair_loses: bool = True, spread: str = "win", jam_wins: bool = False,
        guard_completions: Iterable[str] = (), tick_limit_f1: bool = False) -> dict[str, a.FieldRun]:
    f1: list[tuple[dict, dict]] = []
    for field_id, (x, y) in UNITS:
        if field_id == "F1":
            f1 += pairing(x, y, determined=units_determined)
    # D1/D4/D8 stalemate cells (tick limit, recovery, scoreable FMS).
    stale = telemetry(fms_favouring=stalemate_favouring, recoveries=3)
    f1 += pairing("e2_disrupt_guard", "e2_min_guard", determined=False, reason="tick_limit", tel=stale)
    # D3: repair guard captured by the sniper (control) or not (treatment).
    for s in (1, 2):
        for orientation in (CF, OF):
            c = cell("e2_sniper", "e2_repair_guard", s, orientation,
                     seat_winner=("A" if orientation == CF else "B") if repair_loses else None,
                     reason="last_agent_standing" if repair_loses else "tick_limit", ticks=2 if repair_loses else 1000)
            guard_seat = "B" if orientation == CF else "A"
            if repair_loses:
                c["entrant_terminations"] = {guard_seat: "core_captured"}
            f1.append((c, telemetry(completions=list(guard_completions))))
    # D5: spread sniper against the stacked counter, both seats.
    for s in (1, 2):
        for orientation in (CF, OF):
            spread_seat = "B" if orientation == CF else "A"
            other_seat = "A" if spread_seat == "B" else "B"
            winner = {"win": spread_seat, "loss": other_seat, "draw": None}[spread]
            f1.append((cell("e2_counter", "e2_spread_sniper", s, orientation, seat_winner=winner,
                            reason="tick_limit" if winner is None else "last_agent_standing",
                            ticks=1000 if winner is None else 5), telemetry()))
    if tick_limit_f1:
        f1 = [(dict(c, termination_reason="tick_limit", outcome="tie", ticks_run=1000), t) for c, t in f1]
    f2: list[tuple[dict, dict]] = []
    f2p: list[tuple[dict, dict]] = []
    for field_id, (x, y) in UNITS:
        if field_id == "F2":
            f2 += pairing(x, y, determined=units_determined)
            f2p += pairing(x, y, determined=units_determined if f2p_determined is None else f2p_determined)
    f4: list[tuple[dict, dict]] = []
    for guard in ("e2_repair_guard", "e2_disrupt_guard", "e2_min_guard"):
        for s in (1, 2):
            for orientation in (CF, OF):
                winner = ("A" if orientation == CF else "B") if jam_wins and guard == "e2_min_guard" else None
                f4.append((cell("e3_jam_sniper", guard, s, orientation, seat_winner=winner,
                                reason="last_agent_standing" if winner else "tick_limit",
                                ticks=9 if winner else 1000), telemetry()))
    return {"F1": run("F1", f1), "F2": run("F2", f2), "F2-P": run("F2-P", f2p), "F4": run("F4", f4)}


def frozen_populations(control: dict[str, a.FieldRun]) -> dict[str, dict[str, list[str]]]:
    return a.populations(control)


def evaluate(control: dict[str, a.FieldRun], treatment: dict[str, a.FieldRun], **kw: Any) -> dict[str, Any]:
    empty = {"seat_a": {}, "seat_b": {}}
    return a.evaluate_hypotheses(control, treatment, frozen_populations(control), PREREG,
                                 control_residuals=kw.pop("control_residuals", empty), **kw)


@pytest.fixture(autouse=True)
def _no_bootstrap(monkeypatch: pytest.MonkeyPatch) -> None:
    # The residual table is a separate, secondary reading (tested below); keep
    # the constructed-arm evaluations from bootstrapping a toy field.
    monkeypatch.setattr(a, "residual_table", lambda *_args, **_kw: {"seat_a": {}, "seat_b": {}})


def test_identity_treatment_leaves_every_outcome_and_refutes_seat_change() -> None:
    control = arm(units_determined=True)
    out = evaluate(control, control)
    assert out["D0"]["transitions"]["unchanged_share"] == 1.0
    assert out["D2"]["status"] == a.REFUTED and out["D2"]["units_falling"] == 0
    assert out["D0"]["status"] == a.SUPPORTED  # unchanged in >= 0.90 and D2 refuted
    assert out["D1"]["status"] == a.REFUTED and out["D4"]["status"] == a.SUPPORTED
    assert out["D7"]["status"] == a.REFUTED and out["D7"]["rise"] == 0.0


def test_d2_supported_needs_falls_no_new_unit_and_1000_1001_agreement() -> None:
    control = arm(units_determined=True)
    out = evaluate(control, arm(units_determined=False))
    assert (out["D2"]["units_falling"], out["D2"]["new_units"], out["D2"]["mirror_parity_agrees"]) == (6, [], True)
    assert out["D2"]["status"] == a.SUPPORTED
    assert out["D0"]["status"] == a.REFUTED  # outcomes changed (< 0.90)
    # The same falls, but the mirrors are seat-determined at 1001 only.
    parity = evaluate(control, arm(units_determined=False, f2p_determined=True))
    labels = {tuple(r["mirror"]): r["label"] for r in parity["D2"]["mirror_parity_treatment"]}
    assert labels[("v4_probe", "v4_probe_twin")] == a.TICK_LIMIT_PARITY_DEPENDENT
    assert parity["D2"]["mirror_parity_agrees"] is False and parity["D2"]["status"] == a.NEITHER


def test_d2_new_seat_determined_unit_blocks_support() -> None:
    control = arm(units_determined=False)
    out = evaluate(control, arm(units_determined=True))
    assert out["D2"]["units_falling"] == 0 and len(out["D2"]["new_units"]) == 6
    assert out["D2"]["status"] == a.REFUTED


@pytest.mark.parametrize(("favouring", "d1", "d4", "d8"), [
    (0, a.REFUTED, a.REFUTED, a.SUPPORTED),     # last-mover lock: PD 1.0, FMS 0.0
    (20, a.REFUTED, a.NEITHER, a.NEITHER),      # first-mover lock, D2 not refuted here
    (10, a.SUPPORTED, a.REFUTED, a.REFUTED),    # neutral: PD 0.0
    (17, a.NEITHER, a.NEITHER, a.NEITHER),      # PD 0.7
])
def test_parity_criteria_are_two_sided(favouring: int, d1: str, d4: str, d8: str) -> None:
    control = arm(units_determined=True)
    out = evaluate(control, arm(units_determined=False, stalemate_favouring=favouring))
    assert out["D2"]["status"] == a.SUPPORTED
    assert (out["D1"]["status"], out["D4"]["status"], out["D8"]["status"]) == (d1, d4, d8)
    # Seeds collapse within an orientation; the two orientations are distinct trajectories.
    assert out["D1"]["parity"]["cells"] == 4 and out["D1"]["parity"]["n_distinct"] == 2


def test_d3_repair_guard_losses_becoming_non_losses() -> None:
    control = arm(units_determined=True)
    out = evaluate(control, arm(units_determined=True, repair_loses=False))
    assert (out["D3"]["control_capture_losses"], out["D3"]["non_losses"], out["D3"]["status"]) == (4, 4, a.SUPPORTED)
    same = evaluate(control, control)
    assert (same["D3"]["non_losses"], same["D3"]["status"]) == (0, a.REFUTED)


def test_d5_win_or_draw_rise_in_both_seat_tables() -> None:
    # Pooled over every stacked opponent: here the counter (varied) and the
    # probe and sniper units, where Seat A always wins (4 of the spread
    # sniper's 6 Seat-A cells, none of its 6 Seat-B cells).
    lost = arm(units_determined=True, spread="loss")
    out = evaluate(lost, arm(units_determined=True, spread="draw"))
    assert (out["D5"]["control"]["seat_a"]["win_or_draw"], out["D5"]["control"]["seat_a"]["cells"]) == (4, 6)
    assert (out["D5"]["treatment"]["seat_a"]["win_or_draw"], out["D5"]["treatment"]["seat_b"]["win_or_draw"]) == (6, 2)
    assert out["D5"]["deltas"] == {"seat_a": 0.333333, "seat_b": 0.333333} and out["D5"]["status"] == a.SUPPORTED
    # Wins turned into draws leave win-or-draw unchanged: neither.
    same = evaluate(arm(units_determined=True), arm(units_determined=True, spread="draw"))
    assert same["D5"]["deltas"] == {"seat_a": 0.0, "seat_b": 0.0} and same["D5"]["status"] == a.NEITHER
    fell = evaluate(arm(units_determined=True), lost)
    assert fell["D5"]["deltas"] == {"seat_a": -0.333333, "seat_b": -0.333333} and fell["D5"]["status"] == a.REFUTED


def test_d6_decisive_jammer_wins_in_both_seats() -> None:
    control = arm(units_determined=True)
    out = evaluate(control, arm(units_determined=True, jam_wins=True))
    assert out["D6"]["beaten_in_both_seats"] == ["e2_min_guard"] and out["D6"]["status"] == a.SUPPORTED
    assert evaluate(control, control)["D6"]["status"] == a.REFUTED


def test_d7_tick_limit_rise_in_exposed_f1() -> None:
    control = arm(units_determined=True)
    out = evaluate(control, arm(units_determined=True, tick_limit_f1=True))
    assert out["D7"]["rise"] >= 0.1 and out["D7"]["status"] == a.SUPPORTED


def test_d9_primary_violation_is_a_stop_and_companion_decides_support() -> None:
    control = arm(units_determined=True)
    stop = evaluate(control, arm(units_determined=True, guard_completions=["e2_repair_guard"]))
    assert stop["D9"]["status"] == a.STOP and stop["D9"]["primary_completions"] == 4
    clean = arm(units_determined=True, repair_loses=False)
    assert evaluate(control, clean)["D9"]["status"] == a.NOT_EVALUABLE
    companion = arm(units_determined=True, guard_completions=["e2_disrupt_guard_twin"])
    assert evaluate(control, clean, companion_treatment=companion)["D9"]["status"] == a.SUPPORTED
    assert evaluate(control, clean, companion_treatment=clean)["D9"]["status"] == a.REFUTED


def test_d9_stop_check_raises_only_for_the_primary_treatment() -> None:
    rows = {"k": {"telemetry": telemetry(completions=["e2_repair_guard_twin", "e2_min_guard"])}}
    completions = d9_completions(rows)
    assert [c["victim_name"] for c in completions] == ["e2_repair_guard_twin"]
    with pytest.raises(D9StopError, match="STOP"):
        require_d9("T-E3", completions, primary_treatment=matrix.PRIMARY_TREATMENT)
    require_d9("T-E3K1", completions, primary_treatment=matrix.PRIMARY_TREATMENT)
    require_d9("T-E3", [], primary_treatment=matrix.PRIMARY_TREATMENT)


# ---------------------------------------------------------------------------
# Sec M rule 4: residuals
# ---------------------------------------------------------------------------


def _row(residual: float, *, significant: bool = True, dominance: bool = False, n: int = 8) -> dict[str, Any]:
    counts = significant and abs(residual) >= 0.125 and not dominance and n >= 8
    return {"residual": residual, "significant": significant, "dominance": dominance, "n_distinct": n, "counts": counts}


def test_residual_counts_only_above_the_floor_without_a_counting_control() -> None:
    treatment = {"seat_a": {"p_vs_q": _row(0.2), "p_vs_r": _row(0.05), "q_vs_r": _row(0.3)},
                 "seat_b": {"p_vs_q": _row(-0.4, dominance=True)}}
    control = {"seat_a": {"q_vs_r": _row(0.25)}, "seat_b": {}}
    out = a.residual_evidence(control, treatment)
    # p_vs_r: below |R| >= 1/8. q_vs_r: the control residual also counts.
    assert out["seat_a"]["counting"] == ["p_vs_q"]
    assert out["seat_a"]["control_counting"] == ["q_vs_r"]
    assert out["seat_b"]["counting"] == [] and out["seat_b"]["dominance"] == ["p_vs_q"]


def test_residual_table_marks_dominance_and_applies_the_floor(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.undo()
    from tools.research.v6 import experiment_harness as harness

    intervals = {"residuals": {
        "p_vs_q": {"entrants": ["p", "q"], "residual": 0.2, "significant": True},
        "p_vs_r": {"entrants": ["p", "r"], "residual": 0.1, "significant": True},
        "q_vs_r": {"entrants": ["q", "r"], "residual": 0.3, "significant": True},
    }}
    monkeypatch.setattr(harness, "bootstrap_residual_intervals", lambda *_a, **_k: intervals)
    monkeypatch.setattr(harness, "_distinct_outcomes_by_pair",
                        lambda *_a, **_k: {("p", "q"): ["p", None], ("p", "r"): ["p", "r"], ("q", "r"): ["q", "q"]})
    table = a.residual_table([], ["p", "q", "r"], PREREG["statistics"]["residual"])
    assert {k: (r["dominance"], r["counts"]) for k, r in table["seat_a"].items()} == {
        "p_vs_q": (False, True), "p_vs_r": (False, False), "q_vs_r": (True, False)}
