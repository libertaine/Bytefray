"""V6 E5 cell metrics (O-BP and the E5-D quantities) on real replays.

Blindness: BP is exercised only on the *parent* (control) Rulesets. Under the
E5 treatments only the manipulation quantities are read -- spawn mode, D-2,
DUAL and own-core occupancy -- never a BP value or any other outcome, so these
tests expose no treatment result. All matches use seed 7, outside the matrix
seeds 1..32.
"""

from __future__ import annotations

from fractions import Fraction
from pathlib import Path
from typing import Any

import pytest
from battle_engine.agents import resolve_agent
from battle_engine.config import Config
from battle_engine.match_service import MatchEntrant, MatchRequest, NativeMatchService
from battle_engine.placement import resolve_direct_match_starts

from tools.research.v6.e3.entrants import prepare_data_root
from tools.research.v6.e4.telemetry import analyze_cell as e4_analyze_cell
from tools.research.v6.e5 import matrix
from tools.research.v6.e5.cell_metrics import DECIDED_EARLY, DEFINED, cell_metrics
from tools.research.v6.e5.telemetry import analyze_cell

PARENT = matrix.condition(matrix.PRIMARY_CONTROL).ruleset_id
TREATMENT = matrix.condition(matrix.PRIMARY_TREATMENT).ruleset_id
COMPANION = matrix.condition(matrix.COMPANION_TREATMENT).ruleset_id
SEED = 7


def run(root: Path, ruleset_id: str, names: tuple[str, str], ticks: int = 60) -> Path:
    prepare_data_root(root, list(names))
    starts = resolve_direct_match_starts(ruleset_id=ruleset_id, arena_size=512, entrant_count=2,
                                         supplied_starts=[None, None], seed=SEED)
    out = root / "cell"
    out.mkdir(parents=True, exist_ok=True)
    NativeMatchService().run(MatchRequest(
        config=Config(seed=SEED, arena_size=512, instr_per_tick=8),
        entrants=tuple(MatchEntrant.python(seat, name, start, resolve_agent(root, name))
                       for seat, name, start in zip("AB", names, starts, strict=True)),
        max_ticks=ticks, replay_path=out / "replay.jsonl", verbose=False, ruleset_id=ruleset_id))
    return out


def metrics(directory: Path) -> dict[str, Any]:
    return analyze_cell(directory)["e5"]


def test_sweep_backed_opening_contest_under_the_parent(tmp_path: Path) -> None:
    # Sniper (A) v min guard (B): the min guard owns its base exactly when it
    # moves second, and the sniper never owns its own (review Sec B.4).
    e5 = metrics(run(tmp_path, PARENT, ("e2_sniper", "e2_min_guard")))
    assert e5["checks"]["ok"]
    assert (e5["bp"]["A"]["status"], e5["bp"]["A"]["exact"]) == (DEFINED, "0/1")
    assert (e5["bp"]["B"]["status"], e5["bp"]["B"]["exact"]) == (DEFINED, "1/1")
    assert e5["bp"]["B"]["base_owned_by_first_mover"] == {"A": 30, "B": 0}
    assert e5["both_alive_ticks_by_first_mover"] == {"A": 30, "B": 30}
    # Under the parent every anchor hit on an unmoved process is also a core write.
    assert e5["d_gate"]["spawn_mode"] == "core_base"
    assert e5["d_gate"]["dual_writes"] == e5["d_gate"]["default_dual_writes"] == 120
    for pair in ("A->B", "B->A"):
        directed = e5["directed"][pair]
        assert directed["unmoved_anchor_hits"] == directed["default_anchor_core0_writes"] == 60
        assert directed["first_contact_tick"] == 1


def test_anchor_only_contest_under_the_parent_is_carried_by_anchor_hits(tmp_path: Path) -> None:
    e5 = metrics(run(tmp_path, PARENT, ("e2_disrupt_guard", "e2_guarded_painter")))
    assert e5["checks"]["ok"]
    for seat in "AB":
        assert e5["bp"][seat]["status"] == DEFINED
        assert Fraction(*map(int, e5["bp"][seat]["exact"].split("/"))) > Fraction(2, 3)
    # The disrupt guard never attacks the enemy core except through the anchor hit.
    assert e5["directed"]["A->B"]["core0_writes"] == e5["directed"]["A->B"]["default_anchor_core0_writes"]


@pytest.mark.parametrize("ruleset_id", [TREATMENT, COMPANION])
@pytest.mark.parametrize("names", [("e2_sniper", "e2_min_guard"), ("e2_disrupt_guard", "e2_guarded_painter"),
                                   ("e2_spread_defender", "e2_spread_sniper")])
def test_treatment_manipulation_quantities_only(tmp_path: Path, ruleset_id: str, names: tuple[str, str]) -> None:
    # Blind: only D-1 .. D-4 inputs are read under a treatment.
    e5 = metrics(run(tmp_path, ruleset_id, names))
    assert e5["checks"]["ok"]
    gate = e5["d_gate"]
    assert gate["spawn_mode"] == "before_core" and gate["spawn_offsets"] == [511]
    assert (gate["default_dual_writes"], gate["dual_writes"], gate["own_core_occupancy"]) == (0, 0, 0)
    assert all(item["default_anchor_core0_writes"] == 0 for item in e5["directed"].values())


def test_spread_fixtures_occupy_their_own_core_only_under_the_parent(tmp_path: Path) -> None:
    e5 = metrics(run(tmp_path, PARENT, ("e2_spread_defender", "e2_spread_sniper"), ticks=20))
    # The home processes sit on core cell 0 at every boundary; the movers only at tick 0.
    assert e5["d_gate"]["own_core_occupancy"] == 2 * 21 + 4


def test_a_short_match_is_decided_early(tmp_path: Path) -> None:
    e5 = metrics(run(tmp_path, PARENT, ("e2_sniper", "e2_min_guard"), ticks=12))
    assert all(e5["bp"][seat]["status"] == DECIDED_EARLY for seat in "AB")
    assert all(e5["bp"][seat]["exact"] is None for seat in "AB")


def test_a_reconstruction_disagreement_is_reported(tmp_path: Path) -> None:
    directory = run(tmp_path, PARENT, ("e2_sniper", "e2_min_guard"))
    base = e4_analyze_cell(directory)
    tampered = {**base["e4"], "both_alive_ticks_by_first_mover": {"A": 29, "B": 30}}
    e5 = cell_metrics(directory / "replay.jsonl", base["e3"], tampered)
    assert not e5["checks"]["ok"] and "both-alive ticks" in e5["checks"]["problems"][0]


def test_the_base_is_the_recorded_pc_never_the_anchor(tmp_path: Path) -> None:
    parent = metrics(run(tmp_path / "c", PARENT, ("e2_sniper", "e2_min_guard"), ticks=1))
    treated = metrics(run(tmp_path / "t", TREATMENT, ("e2_sniper", "e2_min_guard"), ticks=1))
    assert parent["core_base"] == treated["core_base"]
