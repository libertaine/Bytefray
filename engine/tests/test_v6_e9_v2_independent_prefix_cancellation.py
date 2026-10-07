"""Actual persisted partial supplements, cancellation and consumer fencing."""
from __future__ import annotations

import json

import pytest

from engine.tests.test_v6_e9_v2_independent_generation import artifact, encode, producer_fixture
from tools.research.v6.e9.v2.integrity import IntegrityController


@pytest.mark.parametrize("values,expected", [
    ([1], "CANCELLED_PRECOLLECTION_HISTORICAL_OVERLAP"),
    ([2], "CANCELLED_PRECOLLECTION_LATE_HISTORY_OUTSIDE_APPROVED_K"),
    ([0, 2], "CANCELLED_PRECOLLECTION_LATE_HISTORY_OUTSIDE_APPROVED_K"),
])
def test_actual_prefix_overlap_outside_k_and_mixed_batches_terminally_cancel_without_repair(tmp_path, monkeypatch, values, expected):
    generator, log, lead, _, verifier, calls, salts, _, K_raw = producer_fixture(tmp_path, monkeypatch, [1, 2])
    generator.consume(expected_tip=log.tip, boundary_evidence=artifact(b"boundary", "boundary"))
    generator.draw_one(expected_tip=log.tip, durable_instant=artifact(b"boundary", "boundary"))
    log.append("HOLD", verifier, expected_tip=log.tip, operation_id="synthetic-operation",
        evidence=[artifact(b"stop", "stop")])
    snapshot = generator.snapshot(evidence=artifact(b"stop", "stop"), snapshot_id="cancelprefix")
    raw_prefix = (tmp_path / "producer/prefix-cancelprefix.json").read_bytes()
    boundary = json.loads((tmp_path / "producer/boundary.json").read_bytes())
    encoded_values = [f"{value:016x}" for value in values]
    execution = encode({"executed_values": encoded_values, "started": True, "scope": "IN_SCOPE",
        "temporal_order": "BEFORE", "generation_boundary_digest": boundary["digest"]})
    execution_ref = artifact(execution, "cancel-execution")
    proof = encode({"values": encoded_values, "actual_execution": True, "scope_verified": True,
        "temporal_order": "BEFORE", "generation_boundary_digest": boundary["digest"],
        "execution_evidence": execution_ref})
    controller = IntegrityController(log, verifier_actor=verifier, lead_actor=lead)
    result = controller.partial_supplement(generator=generator, snapshot=snapshot,
        prefix_raw=raw_prefix, audit_raw=encode(generator.read_audit()[0]), original_K_raw=K_raw,
        history_inputs=[proof], execution_inputs={execution_ref["evidence_id"]: execution},
        expected_tip=log.tip, operation_id="synthetic-operation")
    assert result["decision"]["effective_status"] == expected
    assert result["decision"]["result_status"] == "NOT PRODUCED"
    assert result["terminal"]["event"]["body"]["event_kind"] == "TERMINATE"
    assert result["terminal"]["notice"]["body"]["stage"] == "PARTIAL_GENERATION"
    assert (tmp_path / "producer/prefix-cancelprefix.json").read_bytes() == raw_prefix
    with pytest.raises(ValueError):
        generator.draw_one(expected_tip=log.tip, durable_instant=artifact(b"boundary", "boundary"))
    with pytest.raises(ValueError):
        generator.complete(expected_tip=log.tip, preceding_chain_tip=log.tip)
    with pytest.raises(ValueError):
        controller.release("PARTIAL_GENERATION", result["receipt"], expected_tip=log.tip,
            operation_id="synthetic-operation", evidence=[artifact(proof, "history")],
            original_bindings_valid=True, supplement=result["supplement"])
    assert calls == [8] and salts == []
    assert not (tmp_path / "producer/salt.bin").exists()


def test_unread_private_execution_proof_retains_hold_and_never_becomes_continuation(tmp_path, monkeypatch):
    generator, log, lead, _, verifier, calls, salts, _, K_raw = producer_fixture(tmp_path, monkeypatch, [1, 2])
    generator.consume(expected_tip=log.tip, boundary_evidence=artifact(b"boundary", "boundary"))
    generator.draw_one(expected_tip=log.tip, durable_instant=artifact(b"boundary", "boundary"))
    log.append("HOLD", verifier, expected_tip=log.tip, operation_id="synthetic-operation",
        evidence=[artifact(b"stop", "stop")])
    snapshot = generator.snapshot(evidence=artifact(b"stop", "stop"), snapshot_id="unresolved")
    boundary = json.loads((tmp_path / "producer/boundary.json").read_bytes())
    proof = encode({"values": ["0000000000000000"], "actual_execution": True, "scope_verified": True,
        "temporal_order": "BEFORE", "generation_boundary_digest": boundary["digest"],
        "execution_evidence": artifact(b"unread", "missing-execution")})
    controller = IntegrityController(log, verifier_actor=verifier, lead_actor=lead)
    with pytest.raises(ValueError):
        controller.partial_supplement(generator=generator, snapshot=snapshot,
            prefix_raw=(tmp_path / "producer/prefix-unresolved.json").read_bytes(),
            audit_raw=encode(generator.read_audit()[0]), original_K_raw=K_raw, history_inputs=[proof],
            execution_inputs={}, expected_tip=log.tip, operation_id="synthetic-operation")
    assert log._state()["held"] is True
    with pytest.raises(ValueError):
        log.append("CONTINUE", lead, expected_tip=log.tip, operation_id="synthetic-operation",
            evidence=[artifact(proof, "unread-history")])
    execution = encode({"executed_values": ["0000000000000000"], "started": True, "scope": "IN_SCOPE",
        "temporal_order": "UNKNOWN", "generation_boundary_digest": boundary["digest"]})
    execution_ref = artifact(execution, "uncertain-execution")
    uncertain = encode({"values": ["0000000000000000"], "actual_execution": True, "scope_verified": True,
        "temporal_order": "UNKNOWN", "generation_boundary_digest": boundary["digest"],
        "execution_evidence": execution_ref})
    result = controller.partial_supplement(generator=generator, snapshot=snapshot,
        prefix_raw=(tmp_path / "producer/prefix-unresolved.json").read_bytes(),
        audit_raw=encode(generator.read_audit()[0]), original_K_raw=K_raw, history_inputs=[uncertain],
        execution_inputs={execution_ref["evidence_id"]: execution}, expected_tip=log.tip,
        operation_id="synthetic-operation")
    assert result["receipt"].disposition == "SUSPICION"
    assert result["membership"]["body"]["decision"] == "UNRESOLVED"
    assert result["terminal"] is None
    with pytest.raises(ValueError):
        controller.release("PARTIAL_GENERATION", result["receipt"], expected_tip=log.tip,
            operation_id="synthetic-operation", evidence=[artifact(uncertain, "uncertain-history")],
            original_bindings_valid=True, supplement=result["supplement"])
    with pytest.raises(ValueError):
        generator.draw_one(expected_tip=log.tip, durable_instant=artifact(b"boundary", "boundary"))
    assert calls == [8] and salts == []


def test_continued_partial_generation_rejects_retained_prefix_duplicates_under_original_K(tmp_path, monkeypatch):
    generator, log, lead, _, verifier, calls, salts, _, K_raw = producer_fixture(tmp_path, monkeypatch, [1, 2, 1, 0, 3])
    generator.consume(expected_tip=log.tip, boundary_evidence=artifact(b"boundary", "boundary"))
    for _ in range(2):
        generator.draw_one(expected_tip=log.tip, durable_instant=artifact(b"boundary", "boundary"))
    log.append("HOLD", verifier, expected_tip=log.tip, operation_id="synthetic-operation",
        evidence=[artifact(b"stop", "stop")])
    snapshot = generator.snapshot(evidence=artifact(b"stop", "stop"), snapshot_id="continued")
    raw_prefix = (tmp_path / "producer/prefix-continued.json").read_bytes()
    boundary = json.loads((tmp_path / "producer/boundary.json").read_bytes())
    execution = encode({"executed_values": ["0000000000000000"], "started": True, "scope": "IN_SCOPE",
        "temporal_order": "BEFORE", "generation_boundary_digest": boundary["digest"]})
    execution_ref = artifact(execution, "continued-execution")
    proof = encode({"values": ["0000000000000000"], "actual_execution": True, "scope_verified": True,
        "temporal_order": "BEFORE", "generation_boundary_digest": boundary["digest"],
        "execution_evidence": execution_ref})
    controller = IntegrityController(log, verifier_actor=verifier, lead_actor=lead)
    result = controller.partial_supplement(generator=generator, snapshot=snapshot, prefix_raw=raw_prefix,
        audit_raw=encode(generator.read_audit()[0]), original_K_raw=K_raw, history_inputs=[proof],
        execution_inputs={execution_ref["evidence_id"]: execution}, expected_tip=log.tip,
        operation_id="synthetic-operation")
    release = controller.release("PARTIAL_GENERATION", result["receipt"], expected_tip=log.tip,
        operation_id="synthetic-operation", evidence=[artifact(proof, "history")],
        original_bindings_valid=True, supplement=result["supplement"])
    # Same paused operation: the retained prefix and original K still reject later draws.
    entries = [generator.draw_one(expected_tip=log.tip, durable_instant=artifact(b"boundary", "boundary"))
               for _ in range(3)]
    assert [(e["raw_bytes_hex"], e["disposition"], e["accepted_position"]) for e in entries] == [
        ("0000000000000001", "REJECT_DUPLICATE", None), ("0000000000000000", "REJECT_K", None),
        ("0000000000000003", "ACCEPT", 3)]
    assert all(e["authority_tip"] == release["event"]["digest"] for e in entries)
    assert generator.read_audit()[1] == ["0000000000000001", "0000000000000002", "0000000000000003"]
    assert (tmp_path / "producer/prefix-continued.json").read_bytes() == raw_prefix
    assert result["membership"]["body"]["decision"] == "PASS"
    assert release["notice"]["body"]["withdrawn_eligibility"] is False  # disclosure, not a hold
    # A later stop cannot reuse the earlier sealed prefix: it is no longer the stop state.
    log.append("HOLD", verifier, expected_tip=log.tip, operation_id="synthetic-operation",
        evidence=[artifact(b"second-stop", "second-stop")])
    with pytest.raises(ValueError, match="stopped audit state"):
        controller.partial_supplement(generator=generator, snapshot=snapshot, prefix_raw=raw_prefix,
            audit_raw=encode(generator.read_audit()[0][:2]), original_K_raw=K_raw, history_inputs=[proof],
            execution_inputs={execution_ref["evidence_id"]: execution}, expected_tip=log.tip,
            operation_id="synthetic-operation")
    assert calls == [8] * 5 and salts == []


@pytest.mark.parametrize("fault", ["source_value_error", "source_os_error", "source_unknown_error", "malformed_active_json"])
def test_late_worker_packets_are_retained_ineligible_when_any_current_source_or_state_read_fails(tmp_path, fault):
    from engine.tests.test_v6_e9_v2_dispatch import full_authority
    from tools.research.v6.e9.v2.dispatch import ARTIFACT_NAMES, DispatchLedger
    log = full_authority(tmp_path)
    ledger = DispatchLedger(tmp_path / "independent-late-source", log)
    start = ledger.start("A", "RUSH8", 1, "A", expected_tip=log.tip,
        operation_id="independent-late-source", launch=lambda item, lease: None)
    if fault == "malformed_active_json":
        (log.root / "active.json").write_bytes(b"{")
    else:
        exception = {"source_value_error": ValueError, "source_os_error": OSError,
            "source_unknown_error": RuntimeError}[fault]

        def failed_read():
            raise exception("deterministic injected current-source failure")

        log.source_check = failed_read
    artifacts = {name: b"independent synthetic retained source-fault packet" for name in ARTIFACT_NAMES}
    receipt = ledger.complete(start["attempt"]["cell_identity"], 1, start["lease"], artifacts=artifacts)
    assert receipt["eligible"] is False
    assert all(part["late_fenced"] for part in receipt["receipts"].values())
    retained = list((log.root / "retained").glob("*.bin"))
    assert len(retained) == 4
    assert all(path.read_bytes() == next(iter(artifacts.values())) for path in retained)
