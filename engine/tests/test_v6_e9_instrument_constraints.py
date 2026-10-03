"""Independent exact-threshold, opportunity and tie-preservation fixtures."""

from copy import deepcopy

import pytest

from tools.research.v6.e9.constraints import evaluate
from tools.research.v6.e9.protocol import load_protocol


def fixture(n=30):
    protocol = load_protocol()
    protocol["historical_members"] = {"RUSH8": protocol["historical_members"]["RUSH8"]}
    records = {}
    for row in protocol["physical_rows"]:
        for position in range(1, n + 1):
            for seat in ("A", "B"):
                records[(row, "RUSH8", position, seat)] = {
                    "payoff_doubled": int(row == "A"), "terminal": "last_agent_standing",
                    "captures": {"A": False, "B": False}, "pressure": {"A": False, "B": False},
                    "behavior": {"phase_differences": {"1": 0, "2": 0, "3": 0}, "phase_exposure": []}}
    return protocol, records


def test_seat_opposing_margin_and_stall_zero_contribution_full_denominator():
    protocol, records = fixture()
    for (row, _, _, seat), record in records.items():
        record["payoff_doubled"] = (2 if row == "A" else 0) if seat == "A" else (0 if row == "A" else 2)
    output = evaluate(records, protocol, n=30)
    assert output["severe_seat_dependence"]
    protocol, records = fixture()
    for (row, _, position, _), record in records.items():
        record["payoff_doubled"] = 2 if row == "A" and position <= 15 else 0
        if row == "A" and position <= 15:
            record["terminal"] = "tick_limit"
    output = evaluate(records, protocol, n=30)
    assert output["strata"]["RUSH8/A"]["severe_stall"]
    assert set(output["strata"]["RUSH8/A"]["nonlimit_contribution_full_denominator"].values()) == {0}
    assert len(output["strata"]["RUSH8/A"]["strongest_fixed_ties"]) == 4


@pytest.mark.parametrize("n,expected", [(29, False), (30, True)])
def test_immunity_both_victim_directions_and_minimum_distinct_positions(n, expected):
    protocol, records = fixture(n)
    for (row, _, _, _), record in records.items():
        if row == "A":
            record["pressure"] = {"A": True, "B": True}
            record["terminal"] = "tick_limit"
        else:
            record["captures"] = {"A": True, "B": True}
    out = evaluate(records, protocol, n=n)["strata"]["RUSH8/A"]["immunity"]
    assert out["focal"]["severe"] is expected
    assert out["opponent"]["severe"] is expected


def test_phase_near_exclusivity_requires_alternative_opportunity_and_positive_contribution():
    protocol, records = fixture(90)
    for (row, _, position, _), record in records.items():
        if row == "A":
            phase = (position - 1) // 30 + 1
            record["behavior"] = {"phase_differences": {"1": 100 if phase == 1 else 0,
                "2": int(phase == 2), "3": int(phase == 3)}, "phase_exposure": [phase]}
    # Having small differences in the other phases destroys the only-phase
    # payoff predicate even though action counts exceed 95 percent.
    out = evaluate(records, protocol, n=90)
    assert not any(flag.startswith("phase/") for flag in out["severe"])
    for (row, _, position, _), record in records.items():
        if row == "A":
            # Positive gain is now confined to phase 1 cells; other phases
            # retain independently observed exposure and action differences.
            record["payoff_doubled"] = int(position <= 30)
    out = evaluate(records, protocol, n=90)
    assert any(flag.startswith("phase/") for flag in out["severe"])
    restricted = deepcopy(records)
    for (row, _, _, _), record in restricted.items():
        if row == "A":
            record["behavior"]["phase_exposure"] = [1]
    out = evaluate(restricted, protocol, n=90)
    assert not any(flag.startswith("phase/") for flag in out["severe"])
    assert any(d["scope_restriction"] for d in out["strata"]["RUSH8/A"]["phase_details"])
    for record in records.values():
        record["payoff_doubled"] = 0
    assert not any(flag.startswith("phase/") for flag in evaluate(records, protocol, n=90)["severe"])
