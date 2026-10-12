"""Independent deterministic paired denominators and outcome-blind recovery."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from tools.research.v6.e9.v2.scientific import pair_blocks_v2, recovery_eligible


@pytest.mark.parametrize("seat", ["A", "B"])
def test_independent_causal_expected_transition_and_receipt_hashes(seat):
    from engine.tests.test_v6_e9_v2_scientific import offline_callbacks
    from tools.research.v6.e9.behavior import context_for
    from tools.research.v6.e9.v2.scientific import audit_behavior

    # Input production is shared; predictions and hash derivation are separate.
    injected = offline_callbacks(seat)
    actual = audit_behavior(injected, context_for(seat, 0), row="A", opponent="RUSH8", position=1, seat=seat)
    assert actual["committed_revisions"] == actual["realized_revisions"] == 1
    revision, request = actual["revisions"][0], actual["requests"][0]
    assert (revision["prior_mode"], revision["committed_mode"]) == (1, 4)
    assert revision["first_difference_callback"] is not None
    assert request["cause"] == "confirmations"
    assert request["withholding_passed"] is True
    assert request["withheld_selector_state"][:2] == (1, 0)
    coordinate = ["v6-e9-prereg-v2-539a60806eab", "A", "RUSH8", 1, seat]
    cell = "v6-e9-cell-v2-" + hashlib.sha256(json.dumps(coordinate,
        sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    for receipt in actual["receipt_records"]:
        identity_body = {name: receipt[name] for name in ("cell_identity", "entrant", "process",
            "issuance_callback_ordinal", "issue_tick", "target", "delivery_callback_ordinal")}
        assert identity_body["cell_identity"] == cell
        assert receipt["identity"] == hashlib.sha256(json.dumps(identity_body,
            sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()
        assert receipt["delivery_callback_ordinal"] == receipt["issuance_callback_ordinal"] + 1
    withheld = audit_behavior(offline_callbacks(seat, withhold_confirmations=True), context_for(seat, 0),
        row="A", opponent="RUSH8", position=1, seat=seat)
    assert withheld["committed_revisions"] == withheld["realized_revisions"] == 0


def independently_constructed_rectangle(n=2):
    root = Path(__file__).resolve().parents[2]
    freeze = json.loads((root / "tools/research/v6/e9/protocol_freeze_v2_proposed_02.json").read_bytes())
    pins = freeze["body"]["inherited_scientific_source_pins"]
    result = []
    for row in pins["physical_rows"]:
        for opponent in pins["historical_members"]:
            for position in range(1, n + 1):
                for seat in ("A", "B"):
                    coordinate = [freeze["identity"], row, opponent, position, seat]
                    raw = json.dumps(coordinate, sort_keys=True, separators=(",", ":")).encode()
                    result.append({"cell": {"row": row, "opponent": opponent, "position": position, "seat": seat},
                        "cell_identity": "v6-e9-cell-v2-" + hashlib.sha256(raw).hexdigest(),
                        "payoff_doubled": 1, "terminal": "last_agent_standing",
                        "pressure": {"A": False, "B": False}, "captures": {"A": False, "B": False},
                        "behavior": {"committed_revisions": 1, "realized_revisions": 1,
                        "phase_differences": {"1": 1, "2": 0, "3": 0}, "phase_exposure": [1]} if row == "A" else None})
    return result


def test_complete_paired29_by11_by2_seat_rectangle_has_one_statistical_weight_per_coordinate():
    records = independently_constructed_rectangle()
    scores, evidence = pair_blocks_v2(records, n=2)
    assert len(evidence) == 29 * 11 * 2 * 2
    assert len(scores) == 29
    assert "D" not in scores and "OFF" not in scores and "DENSE" not in scores
    assert all(vector == [22, 22] for vector in scores.values())


@pytest.mark.parametrize("fault", ["missing", "duplicate", "wrong_identity", "alias", "bool_payoff",
                                  "missing_behavior", "phase_count_without_exposure", "wrong_seat"])
def test_any_unusable_cell_rejects_full_paired_rectangle(fault):
    records = independently_constructed_rectangle()
    if fault == "missing":
        records.pop()
    elif fault == "duplicate":
        records.append(records[0])
    elif fault == "wrong_identity":
        records[0]["cell_identity"] = "v6-e9-cell-v2-" + "0" * 64
    elif fault == "alias":
        records[0]["cell"]["row"] = "D"
    elif fault == "bool_payoff":
        records[0]["payoff_doubled"] = True
    elif fault == "missing_behavior":
        records[0]["behavior"] = None
    elif fault == "phase_count_without_exposure":
        records[0]["behavior"]["phase_exposure"] = []
    else:
        records[0]["cell"]["seat"] = "other-seat"
    with pytest.raises(ValueError):
        pair_blocks_v2(records, n=2)


def test_registered_default_requires_every1412_position():
    with pytest.raises(ValueError):
        pair_blocks_v2(independently_constructed_rectangle())


def recovery_fixture():
    cell = "v6-e9-cell-v2-" + hashlib.sha256(b"independent-recovery-coordinate").hexdigest()
    binding = hashlib.sha256(b"independent-recovery-binding").hexdigest()
    return {"cell_identity": cell, "binding_digest": binding, "attempt": 1,
            "origin": "external-supervisor", "failure_class": "host_worker_loss",
            "before_completion": True, "completion_known_absent": True,
            "original_stopped_or_fenced": True, "semantic_integrity_failed": False}, cell, binding


@pytest.mark.parametrize("failure", ["host_worker_loss", "platform_eviction", "external_infrastructure_shutdown", "storage_io_interruption"])
def test_exact_infrastructure_recovery_allowlist_only(failure):
    facts, cell, binding = recovery_fixture()
    facts["failure_class"] = failure
    assert recovery_eligible(facts, cell_identity=cell, binding_digest=binding) is True


@pytest.mark.parametrize("field,bad", [("attempt", 2), ("attempt", True), ("origin", "agent"),
    ("failure_class", "runtime_exception"), ("before_completion", False), ("completion_known_absent", False),
    ("original_stopped_or_fenced", False), ("semantic_integrity_failed", True),
    ("cell_identity", "v6-e9-cell-v2-" + "0" * 64), ("binding_digest", "0" * 64)])
def test_recovery_never_changes_cell_binding_uses_outcomes_or_retries_semantics(field, bad):
    facts, cell, binding = recovery_fixture()
    facts[field] = bad
    assert recovery_eligible(facts, cell_identity=cell, binding_digest=binding) is False


def test_outcome_bearing_recovery_evidence_rejected_before_classification():
    facts, cell, binding = recovery_fixture()
    facts["payoff"] = "outcome-forbidden"
    with pytest.raises(ValueError):
        recovery_eligible(facts, cell_identity=cell, binding_digest=binding)
