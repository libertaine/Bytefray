"""The E3 action/parity analyzer (design review Sec K: PM-1, PM-2, MC-1, MC-2).

The metric definitions are exercised as pure functions; the wiring is
asserted on real canonical replays of *control* Rulesets only (the E2 parent
and research-scale) at seed 42, outside the matrix seeds, with values that
follow exactly from the known whole-tick mechanics.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest
from battle_engine.agents import resolve_agent
from battle_engine.config import Config
from battle_engine.match_service import MatchEntrant, MatchRequest, NativeMatchService
from battle_engine.placement import resolve_direct_match_starts

from tools.research.v6.e3 import entrants, matrix
from tools.research.v6.e3.action_parity import (
    MIN_SCOREABLE_SWINGS,
    NO_ZERO_CORE_TICKS,
    NOT_SCOREABLE,
    PHASE_LOCK_AVAILABLE,
    analyze_actions,
    parity_direction,
    parity_score,
    phase_lock_reading,
)
from tools.research.v6.e3.gates import manipulation_checks

E2_PARENT = matrix.condition("C-E2").ruleset_id
RS_PARENT = matrix.condition("C-RS").ruleset_id


# ---------------------------------------------------------------------------
# PM-1 / PM-2 definitions
# ---------------------------------------------------------------------------


def test_fms_is_scored_only_from_ten_swing_ticks_and_never_dropped() -> None:
    assert MIN_SCOREABLE_SWINGS == 10
    nine = parity_score(9, 9)
    assert (nine["scoreable"], nine["status"], nine["fms"], nine["pd"]) == (False, NOT_SCOREABLE, None, None)
    assert (nine["swing_ticks"], nine["first_mover_favoring"]) == (9, 9)
    ten = parity_score(10, 10)
    assert (ten["scoreable"], ten["fms"], ten["pd"], ten["direction"]) == (True, 1.0, 1.0, "first_mover_dominated")


@pytest.mark.parametrize(
    ("favouring", "fms", "pd", "direction"),
    [
        (20, 1.0, 1.0, "first_mover_dominated"),
        (19, 0.95, 0.9, "first_mover_dominated"),
        (17, 0.85, 0.7, "first_mover_leaning"),
        (15, 0.75, 0.5, "neutral_weak"),
        (10, 0.5, 0.0, "neutral_weak"),
        (5, 0.25, 0.5, "neutral_weak"),
        (3, 0.15, 0.7, "last_mover_leaning"),
        (1, 0.05, 0.9, "last_mover_dominated"),
        (0, 0.0, 1.0, "last_mover_dominated"),
    ],
)
def test_parity_dependence_is_two_sided(favouring: int, fms: float, pd: float, direction: str) -> None:
    # FMS ~ 0 is a strong *last*-mover lock (PD ~ 1), never "unlocked".
    score = parity_score(20, favouring)
    assert (score["fms"], score["pd"], score["direction"]) == (fms, pd, direction)
    assert parity_direction(None, None) == "not_scoreable"


def test_no_zero_core_ticks_is_a_category_never_a_phase_lock_of_zero() -> None:
    none = phase_lock_reading({"zero_core_evaluations": 0, "phase_lock": None})
    assert none == {"category": NO_ZERO_CORE_TICKS, "zero_core_evaluations": 0, "phase_lock": None,
                    "two_sided": None, "direction": None}
    own = phase_lock_reading({"zero_core_evaluations": 125, "phase_lock": 0.0})
    assert (own["category"], own["phase_lock"], own["two_sided"], own["direction"]) == (
        PHASE_LOCK_AVAILABLE, 0.0, 1.0, "own_first")
    opponent = phase_lock_reading({"zero_core_evaluations": 500, "phase_lock": 1.0})
    assert (opponent["two_sided"], opponent["direction"]) == (1.0, "opponent_first")


# ---------------------------------------------------------------------------
# Real control replays
# ---------------------------------------------------------------------------


def _match(root: Path, ruleset_id: str, seat_a: str, seat_b: str, ticks: int) -> Path:
    entrants.prepare_data_root(root, [seat_a, seat_b])
    starts = resolve_direct_match_starts(
        ruleset_id=ruleset_id, arena_size=512, entrant_count=2, supplied_starts=[None, None], seed=42
    )
    replay = root / "match" / "replay.jsonl"
    replay.parent.mkdir(parents=True)
    NativeMatchService().run(MatchRequest(
        config=Config(seed=42, arena_size=512, instr_per_tick=8),
        entrants=(MatchEntrant.python("A", seat_a, starts[0], resolve_agent(root, seat_a)),
                  MatchEntrant.python("B", seat_b, starts[1], resolve_agent(root, seat_b))),
        max_ticks=ticks, replay_path=replay, verbose=False, ruleset_id=ruleset_id))
    return replay


@pytest.fixture(scope="module")
def whole_tick_stalemate(tmp_path_factory: pytest.TempPathFactory) -> Path:
    # E2 Sec D.5: the sniper and the disrupt guard own alternate ticks outright.
    return _match(tmp_path_factory.mktemp("stalemate"), E2_PARENT, "e2_sniper", "e2_disrupt_guard", 30)


def test_whole_tick_stalemate_is_first_mover_dominated_and_fully_exclusive(whole_tick_stalemate: Path) -> None:
    t = analyze_actions(whole_tick_stalemate)
    assert (t["ruleset_id"], t["disruption_slot_limit"], t["hold_ticks"], t["quota"], t["ticks"]) == (
        E2_PARENT, None, 2, 8, 30)
    assert t["checks"] == {"cpu_statistics_match": True, "capture_reconstruction_agrees": True,
                           "capture_consistent_with_engine": True, "capture_attribution_ok": True,
                           "problems": [], "ok": True}
    # MC-1: every tick exclusive -- the first mover executes 8, the second 0.
    assert (t["both_alive_ticks"], t["exclusive_ticks"]) == (30, 30)
    for seat in ("A", "B"):
        row = t["seats"][seat]
        assert (row["cpu_total_replay"], row["cpu_total_result"]) == (120, 120)
        first, second = row["roles"]["first"], row["roles"]["second"]
        assert (first["entrant_ticks"], first["executed"], first["min_executed_alive_throughout"]) == (15, 120, 8)
        assert (second["entrant_ticks"], second["executed"], second["min_executed_alive_throughout"]) == (15, 0, 0)
        assert first["histogram"] == [0] * 8 + [15] and second["histogram"] == [15] + [0] * 8
        # MC-2: ADF 0 as first mover, 1 as second mover.
        assert (first["adf_n"], first["adf_sum"], second["adf_n"], second["adf_sum"]) == (15, 0.0, 15, 15.0)
        assert (row["zero_action_live_ticks"], row["g4_violations"], row["lost_offers"]) == (15, 15, 120)
    # PM-1: every tick is a swing, and each favours the tick's first mover.
    assert t["parity"] == {"swing_ticks": 30, "first_mover_favoring": 30, "scoreable": True, "status": "SCORED",
                           "fms": 1.0, "pd": 1.0, "direction": "first_mover_dominated"}
    # PM-2: the guard's zero-core ticks all fall on the sniper's first-mover
    # ticks; the sniper is never at zero core -- a category, not a lock of 0.
    assert t["seats"]["B"]["phase_lock"] == {"category": PHASE_LOCK_AVAILABLE, "zero_core_evaluations": 15,
                                             "phase_lock": 1.0, "two_sided": 1.0, "direction": "opponent_first"}
    assert t["seats"]["A"]["phase_lock"]["category"] == NO_ZERO_CORE_TICKS
    # Zeroed on the 15 odd (sniper-first) ticks, recovered on the 15 even ticks.
    assert t["seats"]["B"]["capture"]["recoveries"] == 15 and t["completions"] == []
    assert (t["exposed"], t["first_lost_offer_tick"], t["first_hit_tick"], t["hit_ticks"]) == (True, 1, 1, 30)


def test_forced_line_is_exposed_through_the_captured_entrant(tmp_path: Path) -> None:
    # K = 1: Seat A's first write silences the probe twin for the whole tick and
    # captures it at the end of tick 1. The victim was live during the tick,
    # so its eight lost offers make the cell exposed; it is not alive at the
    # tick end, so it has no ADF entry.
    t = analyze_actions(_match(tmp_path, RS_PARENT, "v4_probe", "v4_probe_twin", 1000))
    assert (t["ticks"], t["winner"], t["termination_reason"]) == (1, "A", "last_agent_standing")
    assert (t["exposed"], t["first_lost_offer_tick"], t["seats"]["B"]["lost_offers"]) == (True, 1, 8)
    assert t["seats"]["B"]["roles"]["second"]["adf_n"] == 0
    assert t["parity"]["status"] == NOT_SCOREABLE and t["parity"]["swing_ticks"] == 0
    assert t["completions"] == [{"victim": "B", "victim_name": "v4_probe_twin", "tick": 1, "capturer": "A"}]
    assert t["checks"]["ok"]


def test_hit_free_mirror_loses_no_offer(tmp_path: Path) -> None:
    # Pure repair guards never write an enemy cell: no hit, no lost offer.
    t = analyze_actions(_match(tmp_path, E2_PARENT, "e2_repair_guard", "e2_repair_guard_twin", 20))
    assert (t["first_hit_tick"], t["hit_ticks"], t["exposed"], t["exclusive_ticks"]) == (None, 0, False, 0)
    assert all(t["seats"][s]["lost_offers"] == 0 for s in ("A", "B"))
    assert all(t["seats"][s]["phase_lock"]["category"] == NO_ZERO_CORE_TICKS for s in ("A", "B"))
    assert t["parity"]["status"] == NOT_SCOREABLE


def test_cpu_used_cross_check_detects_a_statistics_mismatch(whole_tick_stalemate: Path, tmp_path: Path) -> None:
    copy = tmp_path / "copy"
    shutil.copytree(whole_tick_stalemate.parent, copy)
    result = json.loads((copy / "result.json").read_text(encoding="utf-8"))
    result["entrants"][0]["statistics"]["cpu_total"] += 1
    (copy / "result.json").write_text(json.dumps(result), encoding="utf-8")
    t = analyze_actions(copy / "replay.jsonl")
    assert t["checks"]["cpu_statistics_match"] is False and t["checks"]["ok"] is False
    assert "cpu_used" in t["checks"]["problems"][0]
    gate = manipulation_checks({"cell": {"telemetry": t}}, slot_limited=False)
    assert (gate["status"], gate["violations"]) == ("FAIL", {"cpu_used_mismatch": 1})


def test_whole_tick_replay_fails_the_slot_limited_manipulation_checks(whole_tick_stalemate: Path) -> None:
    t = analyze_actions(whole_tick_stalemate)
    assert manipulation_checks({"cell": {"telemetry": t}}, slot_limited=False)["status"] == "PASS"
    gate = manipulation_checks({"cell": {"telemetry": t}}, slot_limited=True)
    assert gate["violations"] == {"exclusive_tick": 1, "g4_violation": 1, "zero_action_live_tick": 1}
