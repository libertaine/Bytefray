"""E4 per-cell metrics: FMA, FPS and their cross-checks (design review Sec M.2).

Real canonical replays of the tracked fixtures at seed 42 (outside the matrix
seeds 1..32), under the historical T-E3 Ruleset (C-E4's) and the mirrored T-E4
Ruleset. The sniper v disrupt guard trace is review Sec L-1: under the forward
order the guard's end-of-tick core alternates 7 (A-first ticks) and 3 (B-first
ticks) while the sniper keeps 7, so b(t) = 0 and 4 and FMA = 1/2 (0 - 4) = -2;
under the mirrored order it is a static 7 v 5, so FMA = 1/2 (2 - 2) = 0 with a
single swing. No matrix cell runs here.
"""

from __future__ import annotations

import copy
from fractions import Fraction
from pathlib import Path

import pytest
from battle_engine.agents import resolve_agent
from battle_engine.config import Config
from battle_engine.match_service import MatchEntrant, MatchRequest, NativeMatchService
from battle_engine.placement import resolve_direct_match_starts
from battle_engine.ruleset_policy import resolve_ruleset_policy

from tools.research.v6.e3.action_parity import analyze_actions
from tools.research.v6.e3.entrants import prepare_data_root
from tools.research.v6.e4 import matrix
from tools.research.v6.e4.cell_metrics import (
    DECIDED_EARLY,
    DEFINED,
    MODERATE_FIRST,
    MODERATE_LAST,
    NEUTRAL,
    SCORED,
    STRONG_FIRST,
    STRONG_LAST,
    cell_metrics,
    final_chunk_owner,
    fma_band,
    parse_exact,
)
from tools.research.v6.e4.telemetry import analyze_cell

C_E4 = matrix.condition("C-E4").ruleset_id
T_E4 = matrix.condition("T-E4").ruleset_id
SEED = 42


def _match(root: Path, ruleset_id: str, seat_a: str, seat_b: str, ticks: int = 1000) -> Path:
    prepare_data_root(root, [seat_a, seat_b])
    starts = resolve_direct_match_starts(ruleset_id=ruleset_id, arena_size=512, entrant_count=2,
                                         supplied_starts=[None, None], seed=SEED)
    out = root / "runs" / f"{seat_a}-vs-{seat_b}"
    out.mkdir(parents=True)
    NativeMatchService().run(MatchRequest(
        config=Config(seed=SEED, arena_size=512, instr_per_tick=8),
        entrants=(MatchEntrant.python("A", seat_a, starts[0], resolve_agent(root, seat_a)),
                  MatchEntrant.python("B", seat_b, starts[1], resolve_agent(root, seat_b))),
        max_ticks=ticks, replay_path=out / "replay.jsonl", verbose=False, ruleset_id=ruleset_id))
    return out


def test_fma_band_boundaries_follow_the_registered_inequalities() -> None:
    cases = {
        Fraction(3, 2): STRONG_FIRST, Fraction(149, 100): MODERATE_FIRST, Fraction(1, 2): MODERATE_FIRST,
        Fraction(49, 100): NEUTRAL, Fraction(0): NEUTRAL, Fraction(-49, 100): NEUTRAL,
        Fraction(-1, 2): MODERATE_LAST, Fraction(-149, 100): MODERATE_LAST, Fraction(-3, 2): STRONG_LAST,
        Fraction(8): STRONG_FIRST, Fraction(-8): STRONG_LAST,
    }
    assert {value: fma_band(value) for value in cases} == cases


@pytest.mark.parametrize(("ruleset_id", "role"), [(C_E4, 1), (T_E4, 0)], ids=["forward", "mirrored"])
def test_the_final_chunk_owner_is_read_from_the_registry(ruleset_id: str, role: int) -> None:
    # role 1: the second mover owns the final chunk; role 0: the first mover does.
    policy = resolve_ruleset_policy(ruleset_id)
    for tick in range(1, 9):
        first = (tick - 1) % 2
        assert final_chunk_owner(policy, 8, tick) == (first if role == 0 else 1 - first)


def test_forward_sweep_is_a_strong_last_mover_lock(tmp_path: Path) -> None:
    out = _match(tmp_path, C_E4, "e2_sniper", "e2_disrupt_guard")
    e3 = analyze_actions(out / "replay.jsonl", out / "result.json", names_inferring_core=matrix.CORE_INFERRING_AGENTS)
    metrics = cell_metrics(out / "replay.jsonl", e3)
    assert metrics["checks"] == {"reconstruction_agrees": True, "fps_identity_holds": True, "problems": [], "ok": True}
    assert metrics["both_alive_ticks_by_first_mover"] == {"A": 500, "B": 500}
    assert metrics["balance_sum_by_first_mover"] == {"A": 0, "B": 2000}
    assert metrics["fma"] == {"status": DEFINED, "value": -2.0, "exact": "-2/1", "band": STRONG_LAST}
    # Every one of the 999 swings favours the second mover, which owns the final chunk.
    assert (metrics["swing_ticks"], metrics["first_mover_favoring"]) == (999, 0)
    assert metrics["fps"] == {"status": SCORED, "value": 1.0, "swing_ticks": 999, "final_owner_favoring": 999}
    assert metrics["final_chunk_owner_role"] == "second"
    assert e3["parity"]["fms"] == 0.0


def test_mirrored_sweep_is_static_and_its_fma_is_defined_without_swings(tmp_path: Path) -> None:
    out = _match(tmp_path, T_E4, "e2_sniper", "e2_disrupt_guard")
    row = analyze_cell(out)
    metrics = row["e4"]
    assert metrics["checks"]["ok"]
    assert metrics["balance_sum_by_first_mover"] == {"A": 1000, "B": 1000}
    # Static neutralization is scored through FMA, never dropped (Sec P rule 3).
    assert metrics["fma"] == {"status": DEFINED, "value": 0.0, "exact": "0/1", "band": NEUTRAL}
    assert metrics["swing_ticks"] == 1
    assert metrics["fps"]["status"] == "NOT_SCOREABLE" and row["e3"]["parity"]["status"] == "NOT_SCOREABLE"
    # Mirrored: the first mover owns the final chunk, so FPS counts equal FMS counts.
    assert metrics["final_chunk_owner_role"] == "first"
    assert metrics["fps"]["final_owner_favoring"] == metrics["first_mover_favoring"] == 1


def test_an_early_mutual_elimination_is_decided_early(tmp_path: Path) -> None:
    out = _match(tmp_path, C_E4, "v4_probe", "v4_probe_twin")
    metrics = analyze_cell(out)["e4"]
    assert metrics["both_alive_ticks_by_first_mover"] == {"A": 1, "B": 1}
    assert metrics["fma"] == {"status": DECIDED_EARLY, "value": None, "exact": None, "band": None}
    assert metrics["checks"]["ok"]


def test_fma_is_half_the_parity_difference_of_the_mean_balance(tmp_path: Path) -> None:
    out = _match(tmp_path, C_E4, "e2_guarded_painter", "e2_guarded_painter_twin")
    metrics = analyze_cell(out)["e4"]
    n, s = metrics["both_alive_ticks_by_first_mover"], metrics["balance_sum_by_first_mover"]
    expected = Fraction(1, 2) * (Fraction(s["A"], n["A"]) - Fraction(s["B"], n["B"]))
    assert parse_exact(metrics["fma"]["exact"]) == expected
    assert min(n.values()) >= 10 and metrics["fma"]["band"] == fma_band(expected)


@pytest.mark.parametrize("tamper", ["swings", "final_owned", "zero_ticks", "both_alive"])
def test_a_reconstruction_disagreement_is_reported(tmp_path: Path, tamper: str) -> None:
    out = _match(tmp_path, C_E4, "e2_sniper", "e2_repair_guard", ticks=40)
    e3 = analyze_actions(out / "replay.jsonl", out / "result.json", names_inferring_core=matrix.CORE_INFERRING_AGENTS)
    bad = copy.deepcopy(e3)
    if tamper == "swings":
        bad["parity"]["swing_ticks"] += 1
    elif tamper == "final_owned":
        bad["seats"]["A"]["capture"]["final_owned"] += 1
    elif tamper == "zero_ticks":
        bad["seats"]["B"]["capture"]["zero_ticks_own_first"] += 1
    else:
        bad["both_alive_ticks"] += 1
    assert cell_metrics(out / "replay.jsonl", e3)["checks"]["ok"]
    checks = cell_metrics(out / "replay.jsonl", bad)["checks"]
    assert checks["reconstruction_agrees"] is False and checks["ok"] is False and checks["problems"]
