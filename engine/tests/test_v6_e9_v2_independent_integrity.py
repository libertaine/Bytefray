"""Independent seven-stage cross-product and private temporal checklist."""

from __future__ import annotations

import hashlib
import json

import pytest

from engine.tests._e9_v2_synthetic_records import actor, fixture
from engine.tests.test_v6_e9_v2_independent_private import independent_complete_fixture
from tools.research.v6.e9.v2.authority import AuthorityLog
from tools.research.v6.e9.v2.integrity import (
    IntegrityController,
    adjudicate,
    verify_history,
    verify_prefix_snapshot,
)
from tools.research.v6.e9.v2.records import record_ref
from tools.research.v6.e9.v2.reporting import classify_report

STAGES = ("BEFORE_GENERATION", "PARTIAL_GENERATION", "GENERATED", "COMMITMENT_PUBLIC",
          "COLLECTION", "COLLECTED", "FINAL_PUBLIC")


def encode(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode() + b"\n"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


@pytest.mark.parametrize("stage", STAGES)
def test_proven_overlap_in_every_stage(stage):
    result = adjudicate(stage, finding="OVERLAP")
    expected = {"BEFORE_GENERATION": "INVENTORY_GATE_REOPENED",
                "PARTIAL_GENERATION": "CANCELLED_PRECOLLECTION_HISTORICAL_OVERLAP",
                "GENERATED": "CANCELLED_PRECOLLECTION_HISTORICAL_OVERLAP",
                "COMMITMENT_PUBLIC": "CANCELLED_PRECOLLECTION_HISTORICAL_OVERLAP",
                "COLLECTION": "NOT EVALUABLE", "COLLECTED": "NOT EVALUABLE",
                "FINAL_PUBLIC": "INVALIDATED_HISTORICAL_OVERLAP"}[stage]
    assert result["effective_status"] == expected
    assert result["stop_all_consumers"] is True
    assert result["terminal"] is (stage != "BEFORE_GENERATION")
    assert result["correction_required"] is (stage == "FINAL_PUBLIC")
    assert result["promotion_eligible"] is False


@pytest.mark.parametrize("stage", STAGES)
@pytest.mark.parametrize("finding", ["SUSPICION", "UNRESOLVED_CLOSE", "DISPROVED", "NEW_HISTORY",
                                     "POST_BOUNDARY", "PLANNED_REUSE"])
def test_every_stage_suspicion_closure_release_no_overlap_and_temporal_separation(stage, finding):
    result = adjudicate(stage, finding=finding, all_new_values_in_original_K=True)
    if finding == "SUSPICION":
        assert result["effective_status"] == "INTEGRITY_HOLD_PENDING_ADJUDICATION"
        assert result["stop_all_consumers"] is True
        assert result["terminal"] is False
    elif finding == "UNRESOLVED_CLOSE":
        expected = "INVENTORY_GATE_REOPENED" if stage == "BEFORE_GENERATION" else (
            "CANCELLED_PRECOLLECTION_UNRESOLVED_INTEGRITY" if stage in STAGES[1:4] else (
            "INVALIDATED_UNRESOLVED_HISTORICAL_INTEGRITY" if stage == "FINAL_PUBLIC" else "NOT EVALUABLE")
        )
        assert result["effective_status"] == expected
        assert result["terminal"] is (stage != "BEFORE_GENERATION")
    elif finding in ("DISPROVED", "NEW_HISTORY"):
        expected = "INVENTORY_GATE_REOPENED" if stage == "BEFORE_GENERATION" else "VERIFIED_NO_OVERLAP_PENDING_LEAD_CONTINUATION"
        assert result["effective_status"] == expected
        assert result["stop_all_consumers"] is True
        assert result["continuation_required"] is (stage != "BEFORE_GENERATION")
    else:
        expected = "SEPARATE_FUTURE_INVENTORY_HISTORY" if finding == "POST_BOUNDARY" else "PLANNED_PAIRED_REUSE"
        assert result["effective_status"] == expected
        assert result["terminal"] is False
    assert result["historical_completeness"] == "NOT ESTABLISHED"
    assert result["Requirement_C"] == "NOT ESTABLISHED"


def test_failed_first_cell_start_changes_unresolved_closure_without_complete_rectangle():
    before = adjudicate("COMMITMENT_PUBLIC", finding="UNRESOLVED_CLOSE")
    after = adjudicate("COMMITMENT_PUBLIC", finding="UNRESOLVED_CLOSE", first_cell_started=True)
    assert before["effective_status"] == "CANCELLED_PRECOLLECTION_UNRESOLVED_INTEGRITY"
    assert after["effective_status"] == "NOT EVALUABLE"


@pytest.mark.parametrize("overlap,inside,bindings,expected", [
    (True, True, True, "CANCELLED_PRECOLLECTION_HISTORICAL_OVERLAP"),
    (False, False, True, "CANCELLED_PRECOLLECTION_LATE_HISTORY_OUTSIDE_APPROVED_K"),
    (False, True, True, "VERIFIED_NO_OVERLAP_PENDING_LEAD_CONTINUATION"),
    (False, True, False, "INTEGRITY_HOLD_PENDING_ADJUDICATION"),
])
def test_partial_prefix_conditions(overlap, inside, bindings, expected):
    result = adjudicate("PARTIAL_GENERATION", finding="NEW_HISTORY", prefix_overlap=overlap,
                        all_new_values_in_original_K=inside, original_bindings_valid=bindings)
    assert result["effective_status"] == expected


def history_fixture(temporal="BEFORE", actual=True, scope=True, value=1, *, disproval=None,
                    receipt_scope=None, boundary="a" * 64, label=""):
    execution = encode({"executed_values": [f"{value:016x}"], "started": actual,
                        "scope": receipt_scope or ("IN_SCOPE" if scope else "OUT_OF_SCOPE"),
                        "temporal_order": temporal, "generation_boundary_digest": boundary})
    evidence_id = f"independent-synthetic-execution-{value}{label}"
    proof = {"values": [f"{value:016x}"], "actual_execution": actual,
             "scope_verified": scope, "temporal_order": temporal,
             "generation_boundary_digest": boundary,
             "execution_evidence": {"bytes": len(execution), "sha256_raw": sha(execution),
             "evidence_id": evidence_id, "visibility": "PRIVATE"}}
    if disproval is not None:
        proof["disproval"] = disproval
    return encode(proof), {evidence_id: execution}


def batch_receipt(*proofs, accepted=(1,)):
    raws, executions = [], {}
    for proof_raw, execution in proofs:
        raws.append(proof_raw)
        executions.update(execution)
    return verify_history(
        accepted_raw=encode([{"position": i, "value_hex": f"{v:016x}"} for i, v in enumerate(accepted, 1)]),
        original_K_raw=encode(["0000000000000002"]), history_inputs=raws, execution_inputs=executions,
        boundary_digest="a" * 64, verifier_id="independent-qualifier", producer_id="implementation-producer")


@pytest.mark.parametrize("proof,expected,post_boundary,disproved", [
    ({"actual": False, "disproval": "NOT_EXECUTED"}, "DISPROVED", (), ("0000000000000001",)),
    ({"receipt_scope": "OUT_OF_SCOPE", "disproval": "OUT_OF_SCOPE"}, "DISPROVED", (), ("0000000000000001",)),
    ({"actual": False, "scope": False, "temporal": "UNKNOWN", "disproval": "NOT_EXECUTED"},
     "DISPROVED", (), ("0000000000000001",)),
    ({"temporal": "AFTER"}, "POST_BOUNDARY", ("0000000000000001",), ()),
])
def test_conclusive_disproval_and_post_boundary_use_of_an_accepted_value_are_not_history(
        proof, expected, post_boundary, disproved):
    # The suspected value equals accepted position 1; only actual in-scope
    # pre-boundary use would make it overlap (PG-R4).
    receipt = batch_receipt(history_fixture(value=1, **proof))
    assert receipt.disposition == expected
    assert receipt.values == () and receipt.intersection == ()
    assert receipt.post_boundary_values == post_boundary and receipt.disproved_values == disproved


@pytest.mark.parametrize("proof", [
    {"actual": True, "disproval": "NOT_EXECUTED"},  # the receipt says the match started
    {"disproval": "OUT_OF_SCOPE"},  # the receipt says the match was in scope
    {"scope": False, "receipt_scope": "OUT_OF_SCOPE", "disproval": "OUT_OF_SCOPE"},  # scope unverified
    {"actual": False, "disproval": "MISSING_EVIDENCE"},
    {"actual": False, "disproval": True},
])
def test_uncorroborated_disproval_fails_closed_and_missing_evidence_stays_suspected(proof):
    with pytest.raises(ValueError, match="disproval"):
        batch_receipt(history_fixture(value=1, **proof))
    assert batch_receipt(history_fixture(value=1, actual=False)).disposition == "SUSPICION"
    assert batch_receipt(history_fixture(value=1, scope=False)).disposition == "SUSPICION"


@pytest.mark.parametrize("stage", STAGES[1:])
def test_proven_overlap_terminates_even_beside_uncertain_evidence(stage):
    receipt = batch_receipt(history_fixture(value=1), history_fixture(temporal="UNKNOWN", value=9))
    assert receipt.disposition == "OVERLAP" and receipt.intersection == ("0000000000000001",)
    decision = adjudicate(stage, finding=receipt.disposition, prefix_overlap=True)
    assert decision["terminal"] is True and decision["reason"] == "HISTORICAL_OVERLAP"
    assert decision["effective_status"] != "INTEGRITY_HOLD_PENDING_ADJUDICATION"


def test_batch_disposition_order_after_overlap():
    uncertain = history_fixture(temporal="UNKNOWN", value=9)
    disproved = history_fixture(actual=False, value=7, disproval="NOT_EXECUTED")
    assert batch_receipt(disproved, uncertain).disposition == "SUSPICION"
    assert batch_receipt(disproved, history_fixture(value=8)).disposition == "NEW_HISTORY"
    assert batch_receipt(disproved, history_fixture(temporal="AFTER", value=6)).disposition == "POST_BOUNDARY"
    # Disproving one alleged execution never cancels a separately proven use.
    both = batch_receipt(history_fixture(actual=False, value=1, disproval="NOT_EXECUTED", label="-alleged"),
                         history_fixture(value=1, label="-proven"))
    assert both.disposition == "OVERLAP" and both.disproved_values == ()


@pytest.mark.parametrize("temporal,actual,scope,expected", [
    ("BEFORE", True, True, "OVERLAP"), ("AFTER", True, True, "POST_BOUNDARY"),
    ("SIMULTANEOUS", True, True, "SUSPICION"), ("UNKNOWN", True, True, "SUSPICION"),
    ("BEFORE", False, True, "SUSPICION"), ("BEFORE", True, False, "SUSPICION"),
])
def test_private_actual_execution_scope_temporal_and_equality_are_separate(temporal, actual, scope, expected):
    proof, execution = history_fixture(temporal, actual, scope)
    receipt = verify_history(accepted_raw=encode([{"position": 1, "value_hex": "0000000000000001"}]),
        original_K_raw=encode(["0000000000000002"]),
        history_inputs=[proof], execution_inputs=execution, boundary_digest="a" * 64,
        verifier_id="independent-qualifier", producer_id="implementation-producer")
    assert receipt.disposition == expected


def test_mixed_inside_outside_history_cancels_even_with_disjoint_prefix():
    inside, inside_execution = history_fixture(value=2)
    outside, outside_execution = history_fixture(value=3)
    receipt = verify_history(accepted_raw=encode([{"position": 1, "value_hex": "0000000000000001"}]),
        original_K_raw=encode(["0000000000000002"]), history_inputs=[inside, outside],
        execution_inputs={**inside_execution, **outside_execution}, boundary_digest="a" * 64,
        verifier_id="independent-qualifier", producer_id="implementation-producer")
    assert receipt.intersection == ()
    assert receipt.all_values_in_original_K is False
    assert adjudicate("PARTIAL_GENERATION", finding=receipt.disposition,
        prefix_overlap=bool(receipt.intersection), all_new_values_in_original_K=receipt.all_values_in_original_K)["effective_status"] == "CANCELLED_PRECOLLECTION_LATE_HISTORY_OUTSIDE_APPROVED_K"


def test_unread_execution_receipt_never_substitutes_for_complete_private_verification():
    proof, _ = history_fixture(value=2)
    with pytest.raises(ValueError):
        verify_history(accepted_raw=encode([]), original_K_raw=encode(["0000000000000002"]),
            history_inputs=[proof], boundary_digest="a" * 64,
            verifier_id="independent-qualifier", producer_id="implementation-producer")


@pytest.mark.parametrize("count", [0, 1, 706, 1411])
def test_prefix_empty_one_intermediate_last_incomplete_and_rejected_candidate_not_position(count):
    prefix, audit, accepted, tip, last = [], [], [], "a" * 64, None
    known = "0000000000000000"
    for candidate in [0] + list(range(1, count + 1)) + ([1] if count else []):
        value = f"{candidate:016x}"
        disposition = "REJECT_K" if value == known else "REJECT_DUPLICATE" if value in accepted else "ACCEPT"
        entry = {"raw_draw_ordinal": len(audit) + 1, "raw_bytes_hex": value, "disposition": disposition,
                 "accepted_position": len(accepted) + 1 if disposition == "ACCEPT" else None,
                 "authority_tip": "b" * 64, "prior_entry_digest": tip}
        audit.append(entry)
        tip = sha(encode(entry)[:-1])
        if disposition == "ACCEPT":
            accepted.append(value)
            prefix.append({"position": len(accepted), "value_hex": value})
            last = len(audit)
    prefix_raw = encode(prefix)
    body = {"ordered_prefix": {"bytes": len(prefix_raw), "sha256_raw": sha(prefix_raw)},
            "accepted_count": count, "audit_position": len(audit), "audit_tip": tip,
            "last_acceptance_ordinal": last}
    verify_prefix_snapshot({"body": body}, prefix_raw=prefix_raw, audit_raw=encode(audit),
                           original_K_raw=encode([known]), boundary_digest="a" * 64)
    body["accepted_count"] = count + 1
    with pytest.raises(ValueError):
        verify_prefix_snapshot({"body": body}, prefix_raw=prefix_raw, audit_raw=encode(audit),
                               original_K_raw=encode([known]), boundary_digest="a" * 64)


def ref(raw, label):
    return {"bytes": len(raw), "sha256_raw": sha(raw), "evidence_id": "independent-completed-" + label,
            "visibility": "PRIVATE"}


def completed_stage(tmp_path, stage):
    """Complete synthetic payload, the records existing at a post-generation stage and an active hold."""
    inputs, earlier = independent_complete_fixture()
    boundary = inputs["generation_boundary"]
    earlier["S"] = fixture("S", earlier, operation_id="synthetic-operation", generation_boundary=record_ref(boundary),
        payload=ref(inputs["payload_raw"], "payload"), salt=ref(inputs["salt_raw"], "salt"),
        audit=ref(inputs["audit_raw"], "audit"), audit_counts={"raw": 1414, "accepted": 1412,
        "K_rejected": 1, "duplicate_rejected": 1})
    if stage != "GENERATED":
        for role in ("W", "U", "C"):
            earlier[role] = fixture(role, earlier, commitment=inputs["expected_commitment"])
    if stage in ("COLLECTION", "COLLECTED", "FINAL_PUBLIC"):
        earlier["D"] = fixture("D", earlier)
    if stage == "FINAL_PUBLIC":
        finding = classify_report(integrity=True, realized_positions=2, seat_a_positions=1, seat_b_positions=1,
            statuses=dict.fromkeys(("F", "D", "S", "H"), "SUPPORTED"), gates_valid=True)
        earlier["F"] = fixture("F", earlier, **finding,
            dependencies={role: record_ref(earlier[role]) for role in
                ("P", "I", "Q", "O", "V", "A", "R", "B", "G", "S", "W", "U", "C", "D")},
            counts={"physical_cells": 900856, "started_attempts": 900856, "failed_attempts": 0,
                    "realized_revisions": 2, "realized_positions": 2, "seat_positions": {"A": 1, "B": 1}})
    by_digest = {record["digest"]: record for record in (*earlier.values(), boundary)}
    verifier = actor("independent_integrity_verifier", "independent-completed-verifier")
    registry = {record["body"]["actor"]["actor_id"]: record["body"]["actor"]["role"]
                for record in earlier.values() if "actor" in record["body"]}
    registry[verifier["actor_id"]] = verifier["role"]
    log = AuthorityLog(tmp_path / "authority", "synthetic-e9-v2-only",
        {role: record_ref(record) for role, record in earlier.items()}, actors=registry,
        resolver=lambda item: by_digest[item["digest"]], source_check=lambda: None)
    for field in ("payload", "salt", "audit"):
        log.retain_artifact(inputs[field + "_raw"], earlier["S"]["body"][field]["evidence_id"])
    for evidence in boundary["body"]["evidence"]:
        log.retain_artifact(inputs["artifact_reader"](evidence), evidence["evidence_id"])
    lead = earlier["G"]["body"]["actor"]
    log.append("ISSUE", lead, expected_tip=log.tip, operation_id="synthetic-operation")
    recorder = earlier["S"]["body"]["actor"]
    log.register_producer(tmp_path / "producer", recorder, operation_id="synthetic-operation")
    log.consume_generation(recorder, expected_tip=log.tip, operation_id="synthetic-operation",
                           evidence=[ref(b"boundary", "boundary")])
    log.append("HOLD", verifier, expected_tip=log.tip, operation_id="synthetic-operation", evidence=[ref(b"stop", "stop")])
    return inputs, earlier, by_digest, log, verifier, lead


@pytest.mark.parametrize("stage", ["GENERATED", "COMMITMENT_PUBLIC", "COLLECTION", "COLLECTED", "FINAL_PUBLIC"])
def test_complete_payload_no_overlap_supplements_existing_records_without_reseal(tmp_path, stage):
    inputs, earlier, by_digest, log, verifier, lead = completed_stage(tmp_path, stage)
    payload = json.loads(inputs["payload_raw"])
    boundary = inputs["generation_boundary"]
    immutable_before = {role: encode(record) for role, record in earlier.items()}
    execution = encode({"executed_values": ["ffffffffffffffff"], "started": True, "scope": "IN_SCOPE",
                        "temporal_order": "BEFORE", "generation_boundary_digest": boundary["digest"]})
    execution_ref = ref(execution, "execution")
    proof = encode({"values": ["ffffffffffffffff"], "actual_execution": True, "scope_verified": True,
                    "temporal_order": "BEFORE", "generation_boundary_digest": boundary["digest"],
                    "execution_evidence": execution_ref})
    controller = IntegrityController(log, verifier_actor=verifier, lead_actor=lead)
    result = controller.completed_supplement(stage, accepted_raw=encode(payload["body"]["positions"]),
        original_K_raw=inputs["original_K_raw"], history_inputs=[proof],
        execution_inputs={execution_ref["evidence_id"]: execution}, generation_boundary=boundary,
        expected_tip=log.tip, producer_id=earlier["S"]["body"]["actor"]["actor_id"],
        inspection_boundary="independent complete synthetic inputs only")
    assert result["receipt"].intersection == ()
    assert result["receipt"].all_values_in_original_K is False
    assert result["decision"]["continuation_required"] is True
    release = controller.release(stage, result["receipt"], expected_tip=log.tip,
        operation_id="synthetic-operation", evidence=[ref(proof, "history")],
        original_bindings_valid=True, supplement=result["supplement"])
    assert release["lead_continuation"]["body"]["unchanged_original_tuple"] == log.bindings
    assert release["notice"]["body"]["original_records"] == {
        role: record_ref(record) for role, record in earlier.items() if role in ("S", "C", "F")}
    assert {role: encode(record) for role, record in earlier.items()} == immutable_before
    # A post-generation supplement binds the current authority tip separately
    # from the original immutable pre-completion payload tip.
    from tools.research.v6.e9.v2.commitment import verify_complete_private
    from tools.research.v6.e9.v2.records import make_record
    chain = [record_ref(result["supplement"]), record_ref(release["lead_continuation"]),
        record_ref(release["event"])]
    complete = {**inputs, "supplemented_history": ["ffffffffffffffff"],
        "history_receipts": [result["receipt"]], "supplement_chain": chain,
        "resolver": log.resolve, "artifact_reader": log.read_artifact,
        "active_chain_tip": log.tip}
    assert verify_complete_private(**complete)["decision"] == "PASS"
    assert json.loads(inputs["payload_raw"])["body"]["preceding_chain_tip"] == "a" * 64
    for tip in (None, "f" * 64):
        with pytest.raises(ValueError):
            verify_complete_private(**{**complete, "active_chain_tip": tip})
    for role in (("S", "F") if stage == "FINAL_PUBLIC" else ("S",)):
        # Rebind only the supplement's stage record. The actual HOLD retains
        # the original record, so the full stage tuple must reject the swap.
        swapped_body = dict(earlier[role]["body"])
        if role == "S":
            swapped_body["authority_tip_at_completion"] = "e" * 64
        else:
            swapped_body["counts"] = {"synthetic_changed_original_F": True}
        swapped = make_record(role, swapped_body)
        by_digest[swapped["digest"]] = swapped
        supplement_body = dict(result["supplement"]["body"])
        supplement_body["dependencies"] = {**supplement_body["dependencies"], role: record_ref(swapped)}
        changed_supplement = make_record("CompletedMembershipSupplement", supplement_body)
        by_digest[changed_supplement["digest"]] = changed_supplement
        changed_chain = [record_ref(changed_supplement), *chain[1:]]
        with pytest.raises(ValueError):
            verify_complete_private(**{**complete, "supplement_chain": changed_chain})
    assert {role: encode(record) for role, record in earlier.items()} == immutable_before


@pytest.mark.parametrize("finding", ["NOT_EXECUTED", "OUT_OF_SCOPE", "POST_BOUNDARY"])
@pytest.mark.parametrize("stage", ["GENERATED", "COMMITMENT_PUBLIC", "COLLECTION", "COLLECTED", "FINAL_PUBLIC"])
def test_release_after_conclusive_disproval_is_independently_reproduced_by_w(tmp_path, stage, finding):
    """PG-R7: a hold over accepted position 1 ends in RELEASE, not forced closure."""
    from tools.research.v6.e9.v2.commitment import verify_complete_private
    inputs, earlier, _, log, verifier, lead = completed_stage(tmp_path, stage)
    boundary = inputs["generation_boundary"]
    immutable_before = {role: encode(record) for role, record in earlier.items()}
    proof, execution = history_fixture(value=1, boundary=boundary["digest"], **{
        "NOT_EXECUTED": {"actual": False, "disproval": "NOT_EXECUTED"},
        "OUT_OF_SCOPE": {"receipt_scope": "OUT_OF_SCOPE", "disproval": "OUT_OF_SCOPE"},
        "POST_BOUNDARY": {"temporal": "AFTER"}}[finding])
    controller = IntegrityController(log, verifier_actor=verifier, lead_actor=lead)
    adjudicated = controller.verify_disposition(stage, accepted_raw=encode(
        json.loads(inputs["payload_raw"])["body"]["positions"]), original_K_raw=inputs["original_K_raw"],
        history_inputs=[proof], execution_inputs=execution, boundary_digest=boundary["digest"],
        expected_tip=log.tip, producer_id=earlier["S"]["body"]["actor"]["actor_id"])
    receipt = adjudicated["receipt"]
    assert receipt.disposition == ("POST_BOUNDARY" if finding == "POST_BOUNDARY" else "DISPROVED")
    assert adjudicated["decision"]["terminal"] is False
    released = controller.release(stage, receipt, expected_tip=log.tip, operation_id="synthetic-operation",
                                  evidence=adjudicated["evidence"], original_bindings_valid=True)
    lead_record, event = released["lead_continuation"], released["event"]
    assert lead_record["body"]["disposition"] == "RELEASE" and event["body"]["event_kind"] == "RELEASE"
    assert not {"PartialGenerationSupplement", "CompletedMembershipSupplement"} & lead_record["body"]["dependencies"].keys()
    notice = released["notice"]["body"]
    assert notice["withdrawn_eligibility"] is False
    assert notice["immutable_original_F"] == (record_ref(earlier["F"]) if "F" in earlier else None)
    with log.exclusive():
        assert log._state()["held"] is False and log._state()["terminal"] is False
    assert {role: encode(record) for role, record in earlier.items()} == immutable_before
    complete = {**inputs, "supplement_chain": [record_ref(lead_record), record_ref(event)],
                "resolver": log.resolve, "artifact_reader": log.read_artifact, "active_chain_tip": log.tip}
    assert verify_complete_private(**complete)["decision"] == "PASS"
    for chain in ([record_ref(lead_record)], [record_ref(event)]):
        with pytest.raises(ValueError):
            verify_complete_private(**{**complete, "supplement_chain": chain})
    with pytest.raises(ValueError):
        verify_complete_private(**{**complete, "active_chain_tip": "f" * 64})
