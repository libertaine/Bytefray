"""Implementer-only synthetic checks; no matches, entropy or resampling."""
from copy import deepcopy
from dataclasses import asdict, replace
from fractions import Fraction

import pytest

from tools.research.v6.e9.v2.records import P_ID, IntegrityError, canonical_bytes, sha256
from tools.research.v6.e9.v2.reporting import contrast_status, row_intervals, timing_reproduced
from tools.research.v6.e9.v2.scientific import (
    _collection_counts,
    audit_behavior,
    deduplicate_copies_v2,
    evaluate_constraints_v2,
    pair_blocks_v2,
    recovery_eligible,
    registered_analysis,
    verify_inherited_sources,
)


def rectangle(n=1):
    p = verify_inherited_sources()
    out = {}
    for row in p["physical_rows"]:
        for opp in p["historical_members"]:
            for pos in range(1, n + 1):
                for seat in ("A", "B"):
                    out[(row, opp, pos, seat)] = {
                        "cell": {"row": row, "opponent": opp, "position": pos, "seat": seat},
                        "cell_identity": "v6-e9-cell-v2-" + sha256(canonical_bytes([P_ID, row, opp, pos, seat])),
                        "payoff_doubled": int(row == "A"), "terminal": "last_agent_standing",
                        "pressure": {"A": False, "B": False}, "captures": {"A": False, "B": False},
                        "behavior": {"committed_revisions": 0, "realized_revisions": 0,
                                     "phase_differences": {"1": 0, "2": 0, "3": 0}, "phase_exposure": []},
                    }
    return out


def test_complete_rectangle_denominator_and_logical_alias_no_extra_weight():
    records = rectangle()
    scores, evidence = pair_blocks_v2(records.values(), n=1)
    assert len(evidence) == 638 and len(scores) == 29
    assert scores["A"] == [22]
    assert "OFF" not in scores and "D" not in scores and "DENSE" not in scores
    missing = list(records.values())[:-1]
    with pytest.raises(IntegrityError, match="rectangle"):
        pair_blocks_v2(missing, n=1)
    with pytest.raises(IntegrityError, match="duplicate coordinate"):
        pair_blocks_v2([*records.values(), next(iter(records.values()))], n=1)


@pytest.mark.parametrize("field,value", [("payoff_doubled", True), ("terminal", "tie"),
                                         ("pressure", {"A": 1, "B": False}), ("behavior", None)])
def test_invalid_diagnostics_fail_closed(field, value):
    records = rectangle()
    records[("A", "RUSH8", 1, "A")][field] = value
    with pytest.raises(IntegrityError):
        pair_blocks_v2(records.values(), n=1)


def test_duplicate_only_byte_equal_copies_with_complete_provenance():
    item = next(iter(rectangle().values()))
    with pytest.raises(IntegrityError):
        deduplicate_copies_v2([item, deepcopy(item)])
    item["execution_provenance"] = {
        "attempt_ledger_digest": "0" * 64,
        "artifact_digests": {n: "1" * 64 for n in ("result.json", "replay.jsonl", "trace.jsonl", "diagnostic.json")},
    }
    retained, copies = deduplicate_copies_v2([item, deepcopy(item)])
    assert retained == [item] and copies == 1
    changed = deepcopy(item)
    changed["payoff_doubled"] = 2
    with pytest.raises(IntegrityError):
        deduplicate_copies_v2([item, changed])


def test_opposing_seat_margin_and_stall_preserve_tied_comparators():
    records = rectangle(30)
    for (row, _, _, seat), item in records.items():
        item["payoff_doubled"] = (2 if row == "A" else 0) if seat == "A" else (0 if row == "A" else 2)
    assert evaluate_constraints_v2(records, n=30)["severe_seat_dependence"]
    for (row, _, pos, _), item in records.items():
        item["payoff_doubled"] = 2 if row == "A" and pos <= 15 else 0
        if row == "A" and pos <= 15:
            item["terminal"] = "tick_limit"
    out = evaluate_constraints_v2(records, n=30)["strata"]["RUSH8/A"]
    assert out["severe_stall"] and out["tick_limit_fraction"] == Fraction(1, 2)
    assert len(out["strongest_fixed_ties"]) == 4
    assert set(out["nonlimit_contribution_full_denominator"].values()) == {Fraction(0)}


@pytest.mark.parametrize("n,severe", [(29, False), (30, True)])
def test_immunity_counts_seed_positions_in_each_victim_direction(n, severe):
    records = rectangle(n)
    for (row, _, _, _), item in records.items():
        if row == "A":
            item["pressure"] = {"A": True, "B": True}
            item["terminal"] = "tick_limit"
        else:
            item["captures"] = {"A": True, "B": True}
    result = evaluate_constraints_v2(records, n=n)["strata"]["RUSH8/A"]["immunity"]
    for direction in ("focal", "opponent"):
        assert result[direction]["exposed_positions"] == n
        assert result[direction]["severe"] is severe


def test_phase_concentration_retains_positive_gain_and_alternative_exposure():
    records = rectangle(90)
    for (row, _, pos, _), item in records.items():
        if row == "A":
            phase = (pos - 1) // 30 + 1
            item["payoff_doubled"] = int(phase == 1)
            item["behavior"]["phase_differences"] = {
                "1": 100 if phase == 1 else 0, "2": int(phase == 2), "3": int(phase == 3)}
            item["behavior"]["phase_exposure"] = [phase]
    result = evaluate_constraints_v2(records, n=90)
    assert any(flag.startswith("phase/") for flag in result["severe"])
    for (row, _, pos, _), item in records.items():
        if row == "A" and pos > 60:
            item["behavior"]["phase_differences"]["3"] = 0
            item["behavior"]["phase_exposure"] = []
    result = evaluate_constraints_v2(records, n=90)
    assert not any(flag.startswith("phase/") for flag in result["severe"])
    assert any(d["scope_restriction"] for d in result["strata"]["RUSH8/A"]["phase_details"])


def test_attempt_counts_complete_and_at_most_one_recovery_each():
    counts = {"started": 900857, "completed": 900856, "validated": 900856,
              "eligible_failures": 1, "recovery_starts": 1, "recovered_completions": 1}
    _collection_counts(counts)
    with pytest.raises(IntegrityError):
        _collection_counts({**counts, "started": 900858})
    with pytest.raises(IntegrityError):
        _collection_counts({**counts, "validated": 900855})


@pytest.mark.parametrize("changed", [{}, {"attempt": 2}, {"semantic_integrity_failed": True},
                                    {"failure_class": "policy_exception"}, {"origin": "worker"},
                                    {"completion_known_absent": False}, {"original_stopped_or_fenced": False}])
def test_recovery_is_outcome_blind_and_first_attempt_only(changed):
    item = next(iter(rectangle().values()))
    facts = {"cell_identity": item["cell_identity"], "binding_digest": "0" * 64,
             "attempt": 1, "origin": "external-supervisor", "failure_class": "host_worker_loss",
             "before_completion": True, "completion_known_absent": True,
             "original_stopped_or_fenced": True, "semantic_integrity_failed": False, **changed}
    assert recovery_eligible(facts, cell_identity=item["cell_identity"], binding_digest="0" * 64) is (not changed)
    with pytest.raises(IntegrityError):
        recovery_eligible({**facts, "winner": "A"}, cell_identity=item["cell_identity"], binding_digest="0" * 64)


def test_registered_statistics_cannot_run_before_final_authority():
    class DenyingAuthority:
        def protected(self, operation, **kwargs):
            assert operation == "final_assembly"
            raise IntegrityError("synthetic denial before analysis")
    with pytest.raises(IntegrityError, match="before analysis"):
        registered_analysis(DenyingAuthority(), [], expected_tip="genesis", operation_id="synthetic",
                            instrument_digest="0" * 64, collection_counts={}, historical_integrity="INTACT")


def test_exact_guard_margin_and_timing_width_without_resampling():
    bands = row_intervals({"A": Fraction(1), "q": Fraction(4, 5)}, Fraction(0))
    assert bands["A"] == (Fraction(19, 20), Fraction(1))
    assert contrast_status(Fraction(1, 10), Fraction(3, 10)) == "SUPPORTED"
    assert contrast_status(Fraction(0), Fraction(1, 10)) == "UNRESOLVED"
    assert contrast_status(Fraction(0), Fraction(9, 100)) == "REFUTED"
    assert timing_reproduced(Fraction(1, 10), Fraction(1, 10))
    assert not timing_reproduced(Fraction(1, 10), Fraction(11, 100))


def offline_callbacks(seat, *, withhold_confirmations=False):
    """Typed injected feedback, without an arena, replay or match service.

    A fixed anchor is introduced by the first discovery SENSE. Subsequent
    verification SENSE results either confirm it or deliberately withhold it.
    All callbacks and feedback are synthetic; they are not native artifacts.
    """
    from battle_engine.agent_api import ActionKindV2, ObservationV2
    from battle_engine.agent_trace import DecisionRecordV2, TraceActionV2, TraceObservationV2

    from tools.research.v6.e9.behavior import context_for
    from tools.research.v6.e9.policy import Agent

    agent = Agent()
    context = context_for(seat, 0)
    agent.reset(context)
    records = []
    previous = None
    previous_tick = 0
    discovered_anchor = None
    feedback_anchors = None
    for tick in range(1, 7):
        for _ in range(8):
            obs = ObservationV2(tick, previous_tick, previous_tick, "main", 100, 256, 100, 8,
                                (), True, 0 if previous and previous.kind == ActionKindV2.READ else None,
                                None, feedback_anchors)
            action = agent.act(obs)
            records.append(DecisionRecordV2(
                seat, "main", 0.0, TraceObservationV2(**asdict(obs)),
                TraceActionV2(action.kind.value, action.operand, action.value)))
            feedback_anchors = None
            if action.kind == ActionKindV2.SENSE:
                purpose = agent.pending["main"][0]
                if purpose == "discover" and discovered_anchor is None:
                    discovered_anchor = action.operand
                feedback_anchors = (() if withhold_confirmations and purpose == "verify"
                                    else (discovered_anchor,))
            previous, previous_tick = action, tick
    return records


@pytest.mark.parametrize("seat", ["A", "B"])
def test_offline_causal_revision_withholding_and_v2_receipt_provenance(seat):
    from tools.research.v6.e9.behavior import context_for

    records = offline_callbacks(seat)
    out = audit_behavior(records, context_for(seat, 0), row="A", opponent="RUSH8", position=1, seat=seat)
    assert out["committed_revisions"] == out["realized_revisions"] == 1
    revision, request = out["revisions"][0], out["requests"][0]
    assert (revision["prior_mode"], revision["committed_mode"]) == (1, 4)
    assert revision["budget_remaining_before"] == 4 and revision["cooldown_elapsed_before"] >= 2
    assert revision["first_difference_callback"] is not None
    assert request["cause"] == "confirmations" and request["disposition"] == "satisfied"
    assert request["withholding_passed"] and request["trigger_receipt_ids"]
    # Independently specified evidence withholding leaves the initial selector
    # unchanged, with zero confirmations and no revision demand.
    assert tuple(request["withheld_selector_state"])[0:2] == (1, 0)
    assert not tuple(request["withheld_selector_state"])[3]
    receipts = {r["identity"]: r for r in out["receipt_records"]}
    assert len(receipts) == out["receipts"]
    for receipt in receipts.values():
        assert receipt["issuance_callback_ordinal"] + 1 == receipt["delivery_callback_ordinal"]
        issued = records[receipt["issuance_callback_ordinal"] - 1]
        assert issued.action.kind == "sense" and issued.action.operand % 512 == receipt["target"]
    elsewhere = audit_behavior(records, context_for(seat, 0), row="A", opponent="RUSH8", position=2, seat=seat)
    assert {r["identity"] for r in elsewhere["receipt_records"]}.isdisjoint(receipts)
    withheld = audit_behavior(offline_callbacks(seat, withhold_confirmations=True), context_for(seat, 0),
                              row="A", opponent="RUSH8", position=1, seat=seat)
    assert withheld["committed_revisions"] == withheld["realized_revisions"] == 0


def test_offline_causal_audit_rejects_foreign_callback_and_changed_action():
    from tools.research.v6.e9.behavior import context_for

    records = offline_callbacks("A")
    for change in (replace(records[0], agent_id="B"),
                   replace(records[0], action=replace(records[0].action, kind="write", operand=0, value=1))):
        with pytest.raises(IntegrityError):
            audit_behavior([change, *records[1:]], context_for("A", 0), row="A", opponent="RUSH8", position=1, seat="A")
