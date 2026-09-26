"""V6 E2 analysis pipeline (design review Sec I.3; pre-registration ``preregistration.json``).

For each condition and field it composes the consolidated harness analysis
(seat-conditioned outcomes, SDI, mirror seat bias, per-seat and pooled
rating tables, decisive-only decision ticks) with replay-derived capture
telemetry (``capture_analyzer``). Across conditions it builds the
C-V4 -> T-E2 transition tables and computes every pre-registered hypothesis
metric exactly as ``preregistration.json`` operationalizes it.

It computes metrics and criterion values; it does not declare hypothesis
verdicts -- those are read under the Sec I.5 interpretation rules. T-E2 is
never analyzed unless a complete, passing C-V4 / C-RS control gate exists
for the same frozen matrix (Sec I.5 rule 3), recorded -- together with a
passing control-data requalification -- under the committed analysis freeze
(``analysis_freeze.py``).
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from itertools import product
from pathlib import Path
from typing import Any

from tools.research.v6 import experiment_harness as harness
from tools.research.v6.e2 import matrix
from tools.research.v6.e2.analysis_freeze import FREEZE_RECORD_PATH, AnalysisFreezeError
from tools.research.v6.e2.capture_analyzer import CAPTURE_ANALYZER_VERSION, analyze_replay
from tools.research.v6.e2.control_gate import ControlGateError
from tools.research.v6.e2.preregistration import load_preregistration, preregistration_digest
from tools.research.v6.e2.requalification import RequalificationError
from tools.research.v6.e2.run_e2 import DEFAULT_RUN_ROOT, condition_root, treatment_unlock

E2_ANALYSIS_VERSION = 2

Cell = Mapping[str, Any]
Telemetry = Mapping[str, Any]


@dataclass(frozen=True)
class FieldRun:
    condition_id: str
    field_id: str
    cells: list[Cell]
    telemetry: list[Telemetry | None]
    provenance: Mapping[str, Any]


def load_field_run(
    root: Path, condition_id: str, field_id: str, *, with_telemetry: bool = True
) -> FieldRun:
    data = json.loads((root / "experiment_result.json").read_text(encoding="utf-8"))
    cells = [cell for condition in data["conditions"] for cell in condition["cells"]]
    telemetry: list[Telemetry | None] = []
    for cell in cells:
        replay = root / str(cell.get("artifact_dir")) / "replay.jsonl"
        if with_telemetry and cell.get("artifact_dir") and replay.is_file():
            telemetry.append(analyze_replay(replay, names_inferring_core=matrix.CORE_INFERRING_AGENTS))
        else:
            telemetry.append(None)
    return FieldRun(condition_id, field_id, cells, telemetry, data.get("provenance", {}))


def entrant_capture(cell: Cell, telemetry: Telemetry | None, name: str) -> Mapping[str, Any] | None:
    if telemetry is None:
        return None
    seat_a, seat_b = harness.cell_seats(cell)
    seat = "A" if name == seat_a else "B" if name == seat_b else None
    return None if seat is None else telemetry["entrants"].get(seat)


# ---------------------------------------------------------------------------
# Capture telemetry summaries (HD-5)
# ---------------------------------------------------------------------------


def summarize_capture(cells: Sequence[Cell], telemetry: Sequence[Telemetry | None]) -> dict[str, Any]:
    per_agent: dict[str, dict[str, Any]] = {}
    inconsistent = unattributed = zero_core_decisive = decisive = with_telemetry = 0
    for cell, record in zip(cells, telemetry, strict=True):
        if record is None:
            continue
        with_telemetry += 1
        inconsistent += 0 if record["consistent_with_engine"] else 1
        unattributed += sum(1 for row in record["attributions"] if not row["attributed"])
        if harness.cell_winner(cell) is not None and cell.get("termination_reason") != harness.TICK_LIMIT_REASON:
            decisive += 1
            zero_core_decisive += 1 if record["winner_at_zero_core"] else 0
        for name in harness.cell_seats(cell):
            entrant = entrant_capture(cell, record, name)
            if entrant is None:
                continue
            row = per_agent.setdefault(
                name,
                {
                    "matches": 0,
                    "onsets": 0,
                    "recoveries": 0,
                    "completions": 0,
                    "zero_core_evaluations": 0,
                    "zero_ticks_opponent_first": 0,
                    "onsets_opponent_first": 0,
                    "matches_with_onset": 0,
                    "max_streak": 0,
                    "capture_threatened_at_end": 0,
                    "max_locations": 1,
                    "enemy_core_writes": 0,
                    "core_inference": Counter(),
                    "core_inference_incorrect": 0,
                },
            )
            row["matches"] += 1
            for key in ("onsets", "recoveries", "completions", "zero_core_evaluations"):
                row[key] += entrant[key]
            row["zero_ticks_opponent_first"] += entrant["zero_ticks_opponent_first"]
            row["onsets_opponent_first"] += entrant["onsets_opponent_first"]
            row["matches_with_onset"] += 1 if entrant["onsets"] else 0
            row["max_streak"] = max(row["max_streak"], entrant["max_streak"])
            row["capture_threatened_at_end"] += 1 if entrant["capture_threatened_at_end"] else 0
            row["max_locations"] = max(row["max_locations"], entrant["max_locations"])
            row["enemy_core_writes"] += entrant["enemy_core_writes"]
            inference = entrant.get("core_inference")
            if inference is not None:
                row["core_inference"][inference["status"]] += 1
                row["core_inference_incorrect"] += 1 if inference["correct"] is False else 0
    for row in per_agent.values():
        row["recovery_rate"] = harness._ratio(row["recoveries"], row["onsets"])
        row["phase_lock"] = harness._ratio(row["zero_ticks_opponent_first"], row["zero_core_evaluations"])
        row["core_inference"] = dict(sorted(row["core_inference"].items()))
    return {
        "capture_analyzer_version": CAPTURE_ANALYZER_VERSION,
        "matches_with_telemetry": with_telemetry,
        "analyzer_engine_inconsistencies": inconsistent,
        "unattributed_completions": unattributed,
        "decisive_wins": decisive,
        "zero_core_decisive_wins": zero_core_decisive,
        "zero_core_decisive_win_share": harness._ratio(zero_core_decisive, decisive),
        "per_agent": dict(sorted(per_agent.items())),
    }


def analyze_field_run(run: FieldRun) -> dict[str, Any]:
    field = matrix.field(run.field_id)
    if field.field_id == "F2":
        outcome = harness.analyze_mirror_condition(run.cells, field.pairs)
    else:
        outcome = harness.analyze_experiment_condition(
            run.cells, field.agents, tick_limit=matrix.MAX_TICKS
        )
    return {
        "condition": run.condition_id,
        "field": run.field_id,
        "rated_as_primary": field.rated_as_primary,
        "outcomes": outcome,
        "decision_ticks": harness.decision_tick_summary(run.cells, tick_limit=matrix.MAX_TICKS),
        "capture": summarize_capture(run.cells, run.telemetry),
    }


# ---------------------------------------------------------------------------
# Pre-registered hypothesis metrics (no verdicts)
# ---------------------------------------------------------------------------


def _matched(control: Sequence[Cell], treatment: Sequence[Cell]) -> list[tuple[Cell, Cell]]:
    def index(cells: Sequence[Cell]) -> dict[tuple[Any, ...], Cell]:
        seen: Counter[tuple[Any, ...]] = Counter()
        out: dict[tuple[Any, ...], Cell] = {}
        for cell in cells:
            base = (cell["subject_id"], cell["opponent_id"], cell.get("seed"), harness._orientation(cell))
            out[(*base, seen[base])] = cell
            seen[base] += 1
        return out

    a, b = index(control), index(treatment)
    return [(a[key], b[key]) for key in sorted(set(a) & set(b), key=repr)]


def _involving(cells: Iterable[Cell], x: str, y: str | None = None) -> list[Cell]:
    out = []
    for cell in cells:
        names = {str(cell["subject_id"]), str(cell["opponent_id"])}
        if x in names and (y is None or y in names):
            out.append(cell)
    return out


def _seat_rows(cells: Sequence[Cell], entrant: str, opponent: str) -> dict[str, dict[str, Any]]:
    subset = _involving(cells, entrant, opponent)
    return {
        "seat_a": harness._seat_side(subset, entrant, harness.SEAT_A),
        "seat_b": harness._seat_side(subset, entrant, harness.SEAT_B),
    }


def _lost(cell: Cell, name: str) -> bool:
    winner = harness.cell_winner(cell)
    return winner is not None and winner != name


def _pairs_with_capture(
    cells: Sequence[Cell], telemetry: Sequence[Telemetry | None]
) -> list[tuple[Cell, Telemetry]]:
    return [(c, t) for c, t in zip(cells, telemetry, strict=True) if t is not None]


def hypothesis_metrics(
    runs: Mapping[tuple[str, str], FieldRun], prereg: Mapping[str, Any]
) -> dict[str, Any]:
    """Every metric named in the pre-registration, computed from matrix runs.

    ``runs`` maps ``(condition_id, field_id)`` to loaded runs; C-V4, C-RS and
    T-E2 are needed for F1, and C-V4 and T-E2 for F2.
    """
    roles = prereg["agent_roles"]
    tol = next(o["tolerance"] for o in prereg["operationalizations"] if o["id"] == "O-TOL")
    sniper = roles["the_sniper"]
    defenders = roles["defenders"]
    v4_f1, rs_f1, e2_f1 = runs[("C-V4", "F1")], runs[("C-RS", "F1")], runs[("T-E2", "F1")]
    v4_f2, e2_f2 = runs[("C-V4", "F2")], runs[("T-E2", "F2")]
    f1 = matrix.field("F1")
    out: dict[str, Any] = {}

    # ---- H0 ----
    transitions = harness.outcome_transitions(v4_f1.cells, e2_f1.cells)
    out["h0.winner_kept_one_tick_later_rate"] = {
        "value": transitions["winner_kept_one_tick_later_rate"],
        "control_decisive": transitions["control_decisive"],
        "threshold": 0.9,
    }
    out["h0.winner_kept_rate"] = {"value": transitions["winner_kept_rate"]}
    v4_matchups = {tuple(m["entrants"]): m for m in harness.seat_conditioned_matchups(v4_f1.cells, f1.agents)}
    e2_matchups = {tuple(m["entrants"]): m for m in harness.seat_conditioned_matchups(e2_f1.cells, f1.agents)}
    sdi_rows = []
    for key, before in v4_matchups.items():
        after = e2_matchups.get(key)
        if after is None:
            continue
        a, b = before["sdi"]["sdi"], after["sdi"]["sdi"]
        changed = None if a is None or b is None else abs(b - a) > tol
        sdi_rows.append({"entrants": list(key), "sdi_v4": a, "sdi_e2": b, "changed": changed,
                         "n_distinct_v4": before["sdi"]["n_distinct"], "n_distinct_e2": after["sdi"]["n_distinct"]})
    out["h0.sdi_changed_pairings"] = {"changed": sum(1 for r in sdi_rows if r["changed"]),
                                      "measured": sum(1 for r in sdi_rows if r["changed"] is not None),
                                      "tolerance": tol, "rows": sdi_rows}
    mirror_v4 = harness.analyze_mirror_condition(v4_f2.cells, matrix.F2.pairs)["mirrors"]
    mirror_e2 = harness.analyze_mirror_condition(e2_f2.cells, matrix.F2.pairs)["mirrors"]
    mirror_rows = []
    for before, after in zip(mirror_v4, mirror_e2, strict=True):
        a, b = before["mirror_seat_bias"], after["mirror_seat_bias"]
        mirror_rows.append({"primary": before["primary"], "bias_v4": a, "bias_e2": b,
                            "changed": None if a is None or b is None else abs(b - a) > tol,
                            "sdi_v4": before["sdi"], "sdi_e2": after["sdi"],
                            "n_distinct_v4": before["n_distinct"], "n_distinct_e2": after["n_distinct"]})
    out["h0.mirror_bias_changed"] = {"changed": sum(1 for r in mirror_rows if r["changed"]),
                                     "measured": sum(1 for r in mirror_rows if r["changed"] is not None),
                                     "tolerance": tol, "rows": mirror_rows}
    capture_e2 = summarize_capture(e2_f1.cells, e2_f1.telemetry)["per_agent"]
    out["h0.defender_recovery_rates"] = {
        name: {"recovery_rate": rate, "onsets": capture_e2.get(name, {}).get("onsets", 0),
               "approximately_zero": None if rate is None else rate <= tol}
        for name in defenders
        for rate in (capture_e2.get(name, {}).get("recovery_rate"),)
    }
    survivals = []
    for v4_cell, e2_cell in _matched(_involving(v4_f1.cells, sniper), _involving(e2_f1.cells, sniper)):
        for name in harness.cell_seats(v4_cell):
            if name in defenders and _lost(v4_cell, name) and not _lost(e2_cell, name):
                survivals.append({"defender": name, "seed": v4_cell.get("seed"),
                                  "orientation": harness._orientation(v4_cell),
                                  "v4": harness.cell_seat_result(v4_cell), "e2": harness.cell_seat_result(e2_cell)})
    out["h0.defender_survives_sniper_in_v4_lost_orientation"] = {
        "count": len(survivals), "rows": survivals,
        "n_distinct": len({(r["defender"], r["orientation"], r["e2"]) for r in survivals}),
    }

    # ---- H1 ----
    survive_rows: dict[str, dict[str, Any]] = {}
    for cell, record in _pairs_with_capture(e2_f1.cells, e2_f1.telemetry):
        for name in harness.cell_seats(cell):
            if name not in defenders:
                continue
            entrant = entrant_capture(cell, record, name)
            if entrant is None:
                continue
            row = survive_rows.setdefault(name, {"matches": 0, "recovery_then_survival": 0, "keys": set()})
            row["matches"] += 1
            if entrant["recoveries"] >= 1 and entrant["termination"] != "core_captured":
                row["recovery_then_survival"] += 1
                row["keys"].add(harness.trajectory_key(cell))
    out["h1.recovery_then_survival_matches"] = {
        name: {"matches": row["matches"], "count": row["recovery_then_survival"], "n_distinct": len(row["keys"])}
        for name, row in sorted(survive_rows.items())
    }
    flips: Counter[str] = Counter()
    for v4_cell, e2_cell in _matched(v4_f1.cells, e2_f1.cells):
        for name in harness.cell_seats(v4_cell):
            if name in defenders and _lost(v4_cell, name) and not _lost(e2_cell, name):
                flips[name] += 1
    out["h1.v4_lost_orientation_now_tie_or_win"] = dict(sorted(flips.items()))
    vs_sniper: dict[str, list[int]] = {}
    for cell, record in _pairs_with_capture(e2_f1.cells, e2_f1.telemetry):
        names = harness.cell_seats(cell)
        if sniper not in names:
            continue
        for name in names:
            entrant = entrant_capture(cell, record, name)
            if name in defenders and entrant is not None:
                tally = vs_sniper.setdefault(name, [0, 0])
                tally[0] += entrant["recoveries"]
                tally[1] += entrant["onsets"]
    out["h1.defender_recovery_rate_vs_sniper"] = {
        name: {"recoveries": r, "onsets": o, "recovery_rate": rate,
               "approximately_zero": None if rate is None else rate <= tol}
        for name, (r, o) in sorted(vs_sniper.items())
        for rate in (harness._ratio(r, o),)
    }

    # ---- H2 ----
    significance = next(o for o in prereg["operationalizations"] if o["id"] == "O-H2-SIGNIFICANCE")
    for seat, orientation in (("seat_a", "candidate_first"), ("seat_b", "opponent_first")):
        subset = [c for c in e2_f1.cells if harness._orientation(c) == orientation]
        intervals = harness.bootstrap_residual_intervals(
            subset, f1.agents,
            n_bootstraps=significance["bootstrap_resamples"],
            seed=significance["bootstrap_seed"],
            interval=significance["interval"],
        )
        out[f"h2.significant_residuals_{seat}"] = {
            "significant": intervals["significant"],
            "eligible_pairings": sum(1 for row in intervals["residuals"].values() if row["eligible"]),
            "residuals": intervals["residuals"],
        }
        table = harness.analyze_outcome_table(subset, f1.agents, label=seat)
        out[f"h2.robust_cycles_{seat}"] = {
            "robust": [c for c in table["cycles"] if not c["fragile"]],
            "fragile": [c for c in table["cycles"] if c["fragile"]],
        }
    triples = []
    for d, n, s in product(defenders, roles["non_attackers"], roles["core_attackers"]):
        if len({d, n, s}) < 3:
            continue
        n_vs_d = _involving(e2_f1.cells, n, d)
        n_rows = _seat_rows(e2_f1.cells, n, d)
        n_score_wins = {
            seat: sum(1 for c in n_vs_d
                      if harness.cell_seats(c)[0 if seat == "seat_a" else 1] == n
                      and harness.cell_winner(c) == n
                      and c.get("termination_reason") == harness.TICK_LIMIT_REASON)
            for seat in ("seat_a", "seat_b")
        }
        s_rows = _seat_rows(e2_f1.cells, s, n)
        d_rows = _seat_rows(e2_f1.cells, d, s)
        ok = all(
            n_rows[seat]["n_runs"] > 0
            and n_score_wins[seat] * 2 > n_rows[seat]["n_runs"]
            and s_rows[seat]["wins"] * 2 > s_rows[seat]["n_runs"] > 0
            and (d_rows[seat]["wins"] + d_rows[seat]["ties"]) * 2 > d_rows[seat]["n_runs"] > 0
            for seat in ("seat_a", "seat_b")
        )
        if ok:
            triples.append({"defender": d, "non_attacker": n, "attacker": s,
                            "n_distinct": {"n_vs_d": harness.count_distinct_trajectories(n_vs_d),
                                           "s_vs_n": harness.count_distinct_trajectories(_involving(e2_f1.cells, s, n)),
                                           "d_vs_s": harness.count_distinct_trajectories(_involving(e2_f1.cells, d, s))}})
    out["h2.tradeoff_triples"] = triples

    # ---- H3a / H3b / H3f / H3g (F1 primary; F2 for Sec I.5 consistency) ----
    out["h3a.tick_limit_fraction_treatment"] = harness.decision_tick_summary(
        e2_f1.cells, tick_limit=matrix.MAX_TICKS)["tick_limit"]
    out["h3a.tick_limit_fraction_control"] = harness.decision_tick_summary(
        rs_f1.cells, tick_limit=matrix.MAX_TICKS)["tick_limit"]
    for metric in ("h3a.tick_limit_matches_with_recovery_density", "h3b.phase_lock_by_entrant_in_stalemates",
                   "h3g.onset_without_completion_matches", "h3f.zero_core_decisive_win_share"):
        out[metric] = {}
    for field_id, run in (("F1", e2_f1), ("F2", e2_f2)):
        stalemates: list[Cell] = []
        dense = span_dense = 0
        dense_keys: set[tuple[Any, ...]] = set()
        phase_rows: list[dict[str, Any]] = []
        onset_only = 0
        onset_only_keys: set[tuple[Any, ...]] = set()
        for cell, record in _pairs_with_capture(run.cells, run.telemetry):
            entrants = list(record["entrants"].values())
            if max(e["onsets"] for e in entrants) >= 10 and record["completions"] == 0:
                onset_only += 1
                onset_only_keys.add(harness.trajectory_key(cell))
            if cell.get("termination_reason") != harness.TICK_LIMIT_REASON:
                continue
            ticks = int(cell["ticks_run"])
            density = max(e["recoveries"] / ticks for e in entrants)
            if density >= 0.5:
                dense += 1
                dense_keys.add(harness.trajectory_key(cell))
            span = [e["recoveries"] / (ticks - e["first_onset_tick"] + 1) for e in entrants if e["onsets"]]
            span_dense += 1 if span and max(span) >= 0.5 else 0
            if any(e["recoveries"] >= 1 for e in entrants):
                stalemates.append(cell)
                for e in entrants:
                    if e["zero_core_evaluations"] >= 1:
                        phase_rows.append({"entrant": e["name"], "phase_lock": e["phase_lock"],
                                           "zero_core_evaluations": e["zero_core_evaluations"]})
        limit_total = sum(1 for c in run.cells if c.get("termination_reason") == harness.TICK_LIMIT_REASON)
        out["h3a.tick_limit_matches_with_recovery_density"][field_id] = {
            "count": dense, "of_tick_limit_matches": limit_total,
            "share": harness._ratio(dense, limit_total), "n_distinct": len(dense_keys), "threshold": 0.5,
            "descriptive_from_first_onset_count": span_dense}
        out["h3b.phase_lock_by_entrant_in_stalemates"][field_id] = {
            "stalemated_matches": len(stalemates),
            "n_distinct": harness.count_distinct_trajectories(stalemates),
            "entrants": len(phase_rows),
            "at_least_0_95": sum(1 for r in phase_rows if r["phase_lock"] >= 0.95),
            "near_one_half": sum(1 for r in phase_rows if abs(r["phase_lock"] - 0.5) <= tol),
        }
        out["h3g.onset_without_completion_matches"][field_id] = {
            "count": onset_only, "of": len(run.cells), "n_distinct": len(onset_only_keys)}
        capture = summarize_capture(run.cells, run.telemetry)
        out["h3f.zero_core_decisive_win_share"][field_id] = {
            "zero_core_decisive_wins": capture["zero_core_decisive_wins"],
            "decisive_wins": capture["decisive_wins"],
            "share": capture["zero_core_decisive_win_share"],
        }

    # ---- H3c ----
    new_rows, flip_rows = [], []
    comparisons = [(("F1",) + tuple(k), v4_matchups[k]["sdi"], e2_matchups[k]["sdi"])
                   for k in v4_matchups if k in e2_matchups]
    comparisons += [(("F2", b["primary"], b["twin"]), b["sdi"], a["sdi"])
                    for b, a in zip(mirror_v4, mirror_e2, strict=True)]
    for key, before, after in comparisons:
        if after["sdi"] is not None and after["sdi"] >= 0.9 and (before["sdi"] is None or before["sdi"] < 0.9):
            new_rows.append({"cell": list(key), "sdi_v4": before["sdi"], "sdi_e2": after["sdi"],
                             "favoured_e2": after["favoured_seat"], "n_distinct_e2": after["n_distinct"]})
        seats = {before["favoured_seat"], after["favoured_seat"]}
        if seats == {"A", "B"} and (before["sdi"] or 0) > 0 and (after["sdi"] or 0) > 0:
            flip_rows.append({"cell": list(key), "favoured_v4": before["favoured_seat"],
                              "favoured_e2": after["favoured_seat"], "sdi_v4": before["sdi"], "sdi_e2": after["sdi"]})
    out["h3c.new_seat_determination"] = new_rows
    out["h3c.favoured_seat_flips"] = flip_rows

    # ---- H3d ----
    rows_3d = {}
    for name in defenders:
        subset = _involving(e2_f1.cells, name)
        wins = sum(1 for c in subset if harness.cell_winner(c) == name)
        ties = sum(1 for c in subset if harness.cell_seat_result(c) == harness.TIE)
        losses = sum(1 for c in subset if _lost(c, name))
        tie_rate = harness._ratio(ties, len(subset))
        rows_3d[name] = {"matches": len(subset), "wins": wins, "ties": ties, "losses": losses,
                         "tie_rate": tie_rate, "n_distinct": harness.count_distinct_trajectories(subset),
                         "meets": losses == 0 and tie_rate is not None and tie_rate >= 0.5}
    out["h3d.unbeaten_mostly_drawing_defenders"] = rows_3d

    # ---- H3e ----
    capture_all = summarize_capture(e2_f1.cells, e2_f1.telemetry)["per_agent"]
    rows_3e = []
    for m, s in product(roles["multi_location"], roles["stacked"]):
        seat_rows = _seat_rows(e2_f1.cells, m, s)
        rows_3e.append({
            "multi_location": m, "stacked": s,
            "p_win_seat_a": seat_rows["seat_a"]["p_win"], "p_win_seat_b": seat_rows["seat_b"]["p_win"],
            "n_distinct_seat_a": seat_rows["seat_a"]["n_distinct"],
            "n_distinct_seat_b": seat_rows["seat_b"]["n_distinct"],
            "beats_in_both_seats": all((seat_rows[k]["p_win"] or 0.0) > 0.5 for k in ("seat_a", "seat_b")),
        })
    out["h3e.multi_location_vs_stacked"] = {
        "observed_max_locations": {m: capture_all.get(m, {}).get("max_locations") for m in roles["multi_location"]},
        "rows": rows_3e,
        "beats_every_stacked": {
            m: all(r["beats_in_both_seats"] for r in rows_3e if r["multi_location"] == m)
            for m in roles["multi_location"]
        },
    }
    return out


def analyze_matrix(
    run_root: Path = DEFAULT_RUN_ROOT, *, freeze_path: Path = FREEZE_RECORD_PATH
) -> dict[str, Any]:
    """Analyze every completed condition/field; T-E2 only behind ``run_e2.treatment_unlock``
    (a committed analysis freeze, and a passing gate and requalification under it)."""
    matrix.verify_frozen_matrix()
    prereg = load_preregistration()
    try:
        unlock = treatment_unlock(run_root, freeze_path=freeze_path)
        gate, freeze, gate_error = unlock["gate"], unlock["freeze"], None
    except (AnalysisFreezeError, ControlGateError, RequalificationError) as exc:
        gate, freeze, gate_error = None, None, str(exc)
    runs: dict[tuple[str, str], FieldRun] = {}
    for cond in matrix.CONDITIONS:
        if cond.condition_id == matrix.TREATMENT_CONDITION and gate is None:
            continue
        for fld in matrix.FIELDS:
            root = condition_root(run_root, cond.condition_id, fld.field_id)
            if (root / "experiment_result.json").is_file():
                runs[(cond.condition_id, fld.field_id)] = load_field_run(root, cond.condition_id, fld.field_id)
    required = [(c, f) for c in ("C-V4", "C-RS", "T-E2") for f in ("F1",)] + [("C-V4", "F2"), ("T-E2", "F2")]
    return {
        "e2_analysis_version": E2_ANALYSIS_VERSION,
        "harness_analyzer_version": harness.ANALYZER_VERSION,
        "capture_analyzer_version": CAPTURE_ANALYZER_VERSION,
        "matrix_id": matrix.matrix_id(),
        "preregistration_sha256": preregistration_digest(),
        "control_gate": gate if gate is not None else {"status": "BLOCKED", "reason": gate_error},
        "analysis_freeze": None if freeze is None else {
            "freeze_id": freeze["freeze_id"],
            "freeze_digest": freeze["freeze_digest"],
            "identity": freeze["identity"],
        },
        "fields": {f"{c}/{f}": analyze_field_run(run) for (c, f), run in sorted(runs.items())},
        "transitions": {
            fld.field_id: harness.outcome_transitions(
                runs[("C-V4", fld.field_id)].cells, runs[("T-E2", fld.field_id)].cells
            )
            for fld in matrix.FIELDS
            if ("C-V4", fld.field_id) in runs and ("T-E2", fld.field_id) in runs
        },
        "hypothesis_metrics": (
            hypothesis_metrics(runs, prereg) if all(key in runs for key in required) else None
        ),
        "provenance": harness.get_git_provenance(),
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="analyze_e2", description=__doc__.splitlines()[0])
    parser.add_argument("--run-root", type=Path, default=DEFAULT_RUN_ROOT)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    report = analyze_matrix(args.run_root)
    text = json.dumps(report, indent=2, sort_keys=True, default=str)
    if args.out:
        args.out.write_text(text, encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
