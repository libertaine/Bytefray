"""The V6 E2 analysis pipeline (tools/research/v6/e2/analyze_e2.py).

* The pre-registered hypothesis metrics are checked on a small hand-built
  C-V4 / C-RS / T-E2 scenario: these tests pin the metric *logic* against the
  operationalizations in preregistration.json. (The capture telemetry those
  metrics consume is proven from real replays in
  test_v6_e2_capture_analyzer.py.)
* ``analyze_matrix`` is run on real control artifacts to prove it refuses to
  analyze T-E2 without an analysis freeze and a complete, passing control
  gate recorded under it.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from battle_engine.ruleset_policy import BYTEFRAY_RULESET_V4_ID

from tools.research.v6.e2 import matrix
from tools.research.v6.e2.analysis_freeze import build_freeze_record, identity_inputs
from tools.research.v6.e2.analyze_e2 import (
    FieldRun,
    analyze_matrix,
    hypothesis_metrics,
    summarize_capture,
)
from tools.research.v6.e2.preregistration import load_preregistration
from tools.research.v6.e2.run_e2 import condition_root
from tools.research.v6.experiment_harness import ResearchExperimentConfig, run_experiment

S, D, G = "e2_sniper", "e2_disrupt_guard", "e2_guarded_painter"
ORIENTATIONS = ("candidate_first", "opponent_first")


def _cell(a: str, b: str, seed: int, orientation: str, result: str, ticks: int) -> dict[str, Any]:
    seat_a, seat_b = (a, b) if orientation == "candidate_first" else (b, a)
    winner = {"A": seat_a, "B": seat_b}.get(result)
    return {
        "subject_id": a,
        "opponent_id": b,
        "seed": seed,
        "orientation": orientation,
        "status": "completed",
        "outcome": "tie" if winner is None else ("win" if winner == a else "loss"),
        "ticks_run": ticks,
        "termination_reason": "tick_limit" if ticks == 1000 else "last_agent_standing",
        "score_subject": 1.0,
        "score_opponent": 1.0,
        "territory_subject": 1.0,
        "territory_opponent": 1.0,
    }


def _entrant(name: str, *, onsets: int = 0, recoveries: int = 0, zero: int = 0, captured: bool = False) -> dict[str, Any]:
    return {
        "name": name,
        "onsets": onsets,
        "recoveries": recoveries,
        "completions": 1 if captured else 0,
        "zero_core_evaluations": zero,
        "zero_ticks_opponent_first": zero,
        "onsets_opponent_first": onsets,
        "max_streak": 2 if captured else min(zero, 1),
        "capture_threatened_at_end": False,
        "max_locations": 1,
        "enemy_core_writes": 0,
        "core_inference": None,
        "termination": "core_captured" if captured else None,
        "phase_lock": 1.0 if zero else None,
        "first_onset_tick": 1 if onsets else None,
    }


def _telemetry(cell: dict[str, Any], a: dict[str, Any], b: dict[str, Any], *, zero_winner: bool = False) -> dict[str, Any]:
    return {
        "consistent_with_engine": True,
        "attributions": [],
        "winner_at_zero_core": zero_winner,
        "completions": a["completions"] + b["completions"],
        "entrants": {"A": a, "B": b},
    }


def _scenario() -> dict[tuple[str, str], FieldRun]:
    """V4: Seat A kills on tick 1 in every cell. E2: sniper vs disrupt guard
    alternates to the tick limit (500 onsets, 500 recoveries); the sniper
    mirror is won by Seat A at tick 2 at zero core; the guarded-painter
    mirror flips to Seat B."""
    v4_f1, e2_f1, v4_f2, e2_f2 = [], [], [], []
    for seed in (1, 2):
        for o in ORIENTATIONS:
            v4_f1.append(_cell(S, D, seed, o, "A", 1))
            e2_f1.append(_cell(S, D, seed, o, "tie", 1000))
            v4_f2 += [_cell(S, f"{S}_twin", seed, o, "A", 1), _cell(G, f"{G}_twin", seed, o, "A", 90)]
            e2_f2 += [_cell(S, f"{S}_twin", seed, o, "A", 2), _cell(G, f"{G}_twin", seed, o, "B", 1000)]

    def telemetry(cells: list[dict[str, Any]], treatment: bool) -> list[dict[str, Any] | None]:
        out: list[dict[str, Any] | None] = []
        for c in cells:
            a, b = (c["subject_id"], c["opponent_id"]) if c["orientation"] == "candidate_first" else (c["opponent_id"], c["subject_id"])
            if not treatment:
                out.append(_telemetry(c, _entrant(a), _entrant(b, onsets=1, zero=1, captured=True)))
            elif D in (a, b):
                ea = _entrant(a, onsets=500, recoveries=500, zero=500) if a == D else _entrant(a)
                eb = _entrant(b, onsets=500, recoveries=500, zero=500) if b == D else _entrant(b)
                out.append(_telemetry(c, ea, eb))
            elif c["ticks_run"] == 2:
                out.append(_telemetry(c, _entrant(a, onsets=1, zero=1), _entrant(b, onsets=1, zero=2, captured=True), zero_winner=True))
            else:
                out.append(_telemetry(c, _entrant(a), _entrant(b)))
        return out

    return {
        ("C-V4", "F1"): FieldRun("C-V4", "F1", v4_f1, telemetry(v4_f1, False), {}),
        ("C-RS", "F1"): FieldRun("C-RS", "F1", v4_f1, telemetry(v4_f1, False), {}),
        ("T-E2", "F1"): FieldRun("T-E2", "F1", e2_f1, telemetry(e2_f1, True), {}),
        ("C-V4", "F2"): FieldRun("C-V4", "F2", v4_f2, telemetry(v4_f2, False), {}),
        ("T-E2", "F2"): FieldRun("T-E2", "F2", e2_f2, telemetry(e2_f2, True), {}),
    }


def test_hypothesis_metrics_follow_the_preregistered_operationalizations() -> None:
    metrics = hypothesis_metrics(_scenario(), load_preregistration())

    # H0: none of the 4 V4-decisive cells keeps its winner one tick later.
    assert metrics["h0.winner_kept_one_tick_later_rate"] == {"value": 0.0, "control_decisive": 4, "threshold": 0.9}
    assert metrics["h0.sdi_changed_pairings"]["changed"] == 1
    (row,) = metrics["h0.sdi_changed_pairings"]["rows"]
    assert (row["entrants"], row["sdi_v4"], row["sdi_e2"]) == ([S, D], 1.0, 0.0)
    assert metrics["h0.mirror_bias_changed"]["changed"] == 1  # guarded painter +1 -> -1; sniper unchanged
    assert metrics["h0.defender_recovery_rates"][D] == {"recovery_rate": 1.0, "onsets": 2000, "approximately_zero": False}
    survived = metrics["h0.defender_survives_sniper_in_v4_lost_orientation"]
    assert survived["count"] == 2 and {r["orientation"] for r in survived["rows"]} == {"candidate_first"}

    # H1: every disrupt-guard match recovers and survives.
    assert metrics["h1.recovery_then_survival_matches"][D] == {"matches": 4, "count": 4, "n_distinct": 2}
    assert metrics["h1.defender_recovery_rate_vs_sniper"][D]["recovery_rate"] == 1.0

    # H3a / H3b / H3g on F1: four tick-limit stalemates at exactly 1 recovery per 2 ticks.
    assert metrics["h3a.tick_limit_fraction_treatment"]["fraction"] == 1.0
    assert metrics["h3a.tick_limit_fraction_control"]["fraction"] == 0.0
    dense = metrics["h3a.tick_limit_matches_with_recovery_density"]["F1"]
    assert (dense["count"], dense["of_tick_limit_matches"], dense["n_distinct"]) == (4, 4, 2)
    lock = metrics["h3b.phase_lock_by_entrant_in_stalemates"]["F1"]
    assert (lock["stalemated_matches"], lock["entrants"], lock["at_least_0_95"], lock["near_one_half"]) == (4, 4, 4, 0)
    assert metrics["h3g.onset_without_completion_matches"]["F1"]["count"] == 4

    # H3c: the guarded-painter mirror flips from Seat A to Seat B.
    assert metrics["h3c.new_seat_determination"] == []
    (flip,) = metrics["h3c.favoured_seat_flips"]
    assert (flip["cell"], flip["favoured_v4"], flip["favoured_e2"]) == (["F2", G, f"{G}_twin"], "A", "B")

    # H3d: the disrupt guard never loses and only draws in this scenario.
    assert metrics["h3d.unbeaten_mostly_drawing_defenders"][D]["meets"] is True

    # H3f: the sniper mirror's decisive wins are all won at zero core.
    assert metrics["h3f.zero_core_decisive_win_share"]["F2"] == {
        "zero_core_decisive_wins": 4,
        "decisive_wins": 4,
        "share": 1.0,
    }

    # H2: every seat table here is deterministic, so no residual can count.
    assert metrics["h2.significant_residuals_seat_a"]["significant"] == []
    assert metrics["h2.significant_residuals_seat_b"]["eligible_pairings"] == 0
    assert metrics["h2.tradeoff_triples"] == []

    prereg_metrics = {m.split(".")[0] + "." + m.split(".")[1] for h in load_preregistration()["hypotheses"] for m in h["metrics"]}
    assert prereg_metrics <= set(metrics)


def test_capture_summary_aggregates_per_agent() -> None:
    run = _scenario()[("T-E2", "F1")]
    summary = summarize_capture(run.cells, run.telemetry)
    guard = summary["per_agent"][D]
    assert (guard["matches"], guard["onsets"], guard["recoveries"], guard["phase_lock"]) == (4, 2000, 2000, 1.0)
    assert summary["analyzer_engine_inconsistencies"] == 0 and summary["decisive_wins"] == 0


def test_analysis_refuses_to_interpret_treatment_without_a_passing_gate(tmp_path: Path) -> None:
    control = condition_root(tmp_path, "C-V4", "F2")
    run_experiment(
        ResearchExperimentConfig(
            experiment_id="analysis-gate",
            ruleset_id=BYTEFRAY_RULESET_V4_ID,
            field=("v4_probe", "v4_probe_twin"),
            pairs=(("v4_probe", "v4_probe_twin"),),
            seeds=(1,),
            ticks=20,
            output_dir=control,
        )
    )
    # A T-E2 result directory exists (a copied file, never executed), but no gate does.
    treatment = condition_root(tmp_path, "T-E2", "F2")
    treatment.mkdir(parents=True)
    shutil.copy(control / "experiment_result.json", treatment / "experiment_result.json")

    # Without an analysis freeze, T-E2 is blocked before any gate is looked for.
    unfrozen = analyze_matrix(tmp_path, freeze_path=tmp_path / "missing.json")
    assert unfrozen["control_gate"]["status"] == "BLOCKED"
    assert "No analysis freeze record" in unfrozen["control_gate"]["reason"]
    assert unfrozen["analysis_freeze"] is None and unfrozen["hypothesis_metrics"] is None

    freeze = tmp_path / "freeze.json"
    identity = identity_inputs(tooling_source_sha="a" * 40, match_generation_tree="b" * 40)
    freeze.write_text(json.dumps(build_freeze_record(identity, {})), encoding="utf-8")
    report = analyze_matrix(tmp_path, freeze_path=freeze)
    assert report["control_gate"]["status"] == "BLOCKED"
    assert "No control gate record" in report["control_gate"]["reason"]
    assert list(report["fields"]) == ["C-V4/F2"]
    assert report["transitions"] == {} and report["hypothesis_metrics"] is None
    mirror = report["fields"]["C-V4/F2"]
    assert mirror["outcomes"]["mirrors"][0]["mirror_seat_bias"] == 1.0
    # The real replays were analyzed and agree with the engine.
    assert mirror["capture"]["matches_with_telemetry"] == 2
    assert mirror["capture"]["analyzer_engine_inconsistencies"] == 0
    assert report["matrix_id"] == matrix.matrix_id()
    json.dumps(report, default=str)
