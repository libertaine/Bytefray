"""Independent injected producer execution and immutable same-operation audit."""

from __future__ import annotations

import hashlib
import json
import os

import pytest

from engine.tests._e9_v2_synthetic_records import actor, through_g
from tools.research.v6.e9.v2.authority import AuthorityLog
from tools.research.v6.e9.v2.commitment import verify_complete_private
from tools.research.v6.e9.v2.generation import Generator
from tools.research.v6.e9.v2.integrity import IntegrityController, verify_history
from tools.research.v6.e9.v2.records import make_record, record_ref


def encode(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode() + b"\n"


def artifact(raw, label):
    return {"evidence_id": "independent-" + label, "bytes": len(raw),
            "sha256_raw": hashlib.sha256(raw).hexdigest(), "visibility": "PRIVATE"}


def producer_fixture(tmp_path, monkeypatch, values):
    monkeypatch.setattr(os, "urandom", lambda size: pytest.fail("OS entropy forbidden in synthetic qualification"))
    K_raw = encode(["0000000000000000"])
    refs = {"K": artifact(K_raw, "K"), "E": artifact(encode([]), "E"), "L": artifact(encode({}), "L")}
    records = through_g(inventory_refs=refs)
    bindings = {role: record_ref(record) for role, record in records.items()}
    resolver = {record["digest"]: record for record in records.values()}
    lead, recorder, verifier = actor(), actor("recorder", "independent-recorder"), actor(
        "independent_integrity_verifier", "independent-verifier")
    actors = {record["body"]["actor"]["actor_id"]: record["body"]["actor"]["role"]
              for record in records.values() if "actor" in record["body"]}
    actors.update({a["actor_id"]: a["role"] for a in (lead, recorder, verifier)})
    log = AuthorityLog(tmp_path / "authority", "synthetic-e9-v2-only", bindings,
        actors=actors,
        resolver=lambda ref: resolver[ref["digest"]], source_check=lambda: None)
    log.append("ISSUE", lead, expected_tip=log.tip, operation_id="synthetic-operation", evidence=[artifact(b"issue", "issue")])
    sequence, calls = iter(values), []

    def draw(size):
        assert size == 8
        # Durable receipt and intent must exist before the injected raw call.
        assert (tmp_path / "producer/boundary.json").exists()
        ordinal = len(calls) + 1
        assert (tmp_path / "producer" / f"draw-{ordinal:08d}.intent.json").exists()
        calls.append(size)
        return next(sequence).to_bytes(8, "big")

    salt_calls = []

    def salt(size):
        assert size == 32
        salt_calls.append(size)
        return bytes(range(32))

    generator = Generator(tmp_path / "producer", log, operation_id="synthetic-operation", recorder=recorder,
        original_K_raw=K_raw, inventory_refs=refs, draw_bytes=draw, salt_bytes=salt, mode="SYNTHETIC")
    return generator, log, lead, recorder, verifier, calls, salt_calls, refs, K_raw


def test_no_raw_draw_without_consumed_G_and_no_salt_before_completion(tmp_path, monkeypatch):
    generator, log, _, _, _, calls, salt_calls, _, _ = producer_fixture(tmp_path, monkeypatch, [1])
    with pytest.raises(ValueError):
        generator.draw_one(expected_tip=log.tip, durable_instant=artifact(b"boundary", "boundary"))
    assert calls == []
    generator.consume(expected_tip=log.tip, boundary_evidence=artifact(b"boundary", "boundary"))
    with pytest.raises(ValueError):
        generator.complete(expected_tip=log.tip, preceding_chain_tip=log.tip)
    assert salt_calls == []


def test_partial_hold_rejects_draw_salt_and_preserves_rejected_raw_positions(tmp_path, monkeypatch):
    generator, log, _, _, verifier, calls, salt_calls, _, _ = producer_fixture(tmp_path, monkeypatch, [0, 1, 1, 2])
    generator.consume(expected_tip=log.tip, boundary_evidence=artifact(b"boundary", "boundary"))
    for _ in range(4):
        generator.draw_one(expected_tip=log.tip, durable_instant=artifact(b"boundary", "boundary"))
    log.append("HOLD", verifier, expected_tip=log.tip, operation_id="synthetic-operation", evidence=[artifact(b"stop", "stop")])
    snapshot = generator.snapshot(evidence=artifact(b"stop", "stop"), snapshot_id="independentprefix")
    assert snapshot["body"]["accepted_count"] == 2
    assert snapshot["body"]["audit_position"] == 4
    assert snapshot["body"]["last_acceptance_ordinal"] == 4
    assert [entry["disposition"] for entry in generator.read_audit()[0]] == ["REJECT_K", "ACCEPT", "REJECT_DUPLICATE", "ACCEPT"]
    with pytest.raises(ValueError):
        generator.draw_one(expected_tip=log.tip, durable_instant=artifact(b"boundary", "boundary"))
    with pytest.raises(ValueError):
        generator.complete(expected_tip=log.tip, preceding_chain_tip=log.tip)
    assert len(calls) == 4
    assert salt_calls == []


def test_full_original_operation1412_boundary_draw_order_rejections_salt_and_private_read_back(tmp_path, monkeypatch):
    values = [0, 1, 1] + list(range(2, 1413))
    generator, log, lead, _, verifier, calls, salt_calls, refs, K_raw = producer_fixture(tmp_path, monkeypatch, values)
    generator.consume(expected_tip=log.tip, boundary_evidence=artifact(b"boundary", "boundary"))
    current_tip = log.tip
    authority_tips = [current_tip]
    supplement_chain = []
    history_proof = execution_inputs = None
    for expected_ordinal in range(1, len(values) + 1):
        entry = generator.draw_one(expected_tip=current_tip, durable_instant=artifact(b"boundary", "boundary"))
        assert entry["raw_draw_ordinal"] == expected_ordinal
        if expected_ordinal == 4:
            log.append("HOLD", verifier, expected_tip=current_tip, operation_id="synthetic-operation",
                       evidence=[artifact(b"stop", "stop")])
            snapshot = generator.snapshot(evidence=artifact(b"stop", "stop"), snapshot_id="fullprefix")
            boundary = json.loads((tmp_path / "producer/boundary.json").read_bytes())
            execution = encode({"executed_values": ["0000000000000000"], "started": True,
                "scope": "IN_SCOPE", "temporal_order": "BEFORE", "generation_boundary_digest": boundary["digest"]})
            execution_ref = artifact(execution, "complete-history-execution")
            history_proof = encode({"values": ["0000000000000000"], "actual_execution": True,
                "scope_verified": True, "temporal_order": "BEFORE", "generation_boundary_digest": boundary["digest"],
                "execution_evidence": execution_ref})
            execution_inputs = {execution_ref["evidence_id"]: execution}
            controller = IntegrityController(log, verifier_actor=verifier, lead_actor=lead)
            supplement = controller.partial_supplement(generator=generator, snapshot=snapshot,
                prefix_raw=(tmp_path / "producer/prefix-fullprefix.json").read_bytes(),
                audit_raw=encode(generator.read_audit()[0]), original_K_raw=K_raw,
                history_inputs=[history_proof], execution_inputs=execution_inputs,
                expected_tip=log.tip, operation_id="synthetic-operation")
            assert supplement["receipt"].intersection == ()
            assert supplement["receipt"].all_values_in_original_K is True
            assert "S" not in supplement["supplement"]["body"]["dependencies"]
            assert "C" not in supplement["supplement"]["body"]["dependencies"]
            release = controller.release("PARTIAL_GENERATION", supplement["receipt"],
                expected_tip=log.tip, operation_id="synthetic-operation", evidence=[artifact(history_proof, "history")],
                original_bindings_valid=True, supplement=supplement["supplement"], scope="remaining original synthetic draws")
            supplement_chain = [record_ref(supplement["supplement"]), record_ref(release["lead_continuation"]), record_ref(release["event"])]
            current_tip = log.tip
            authority_tips.append(current_tip)
        if expected_ordinal == 8:
            # PG-R7: a suspicion about accepted position 3 is conclusively disproved
            # (the alleged run never started); the same paused operation resumes.
            hold = log.append("HOLD", verifier, expected_tip=current_tip, operation_id="synthetic-operation",
                              evidence=[artifact(b"second-stop", "second-stop")])
            paused = generator.snapshot(evidence=artifact(b"second-stop", "second-stop"), snapshot_id="disproved")
            assert (paused["body"]["accepted_count"], paused["body"]["audit_position"]) == (6, 8)
            boundary = json.loads((tmp_path / "producer/boundary.json").read_bytes())
            alleged = encode({"executed_values": ["0000000000000003"], "started": False, "scope": "IN_SCOPE",
                "temporal_order": "UNKNOWN", "generation_boundary_digest": boundary["digest"]})
            alleged_ref = artifact(alleged, "never-started-execution")
            disproval = encode({"values": ["0000000000000003"], "actual_execution": False, "scope_verified": False,
                "temporal_order": "UNKNOWN", "generation_boundary_digest": boundary["digest"],
                "execution_evidence": alleged_ref, "disproval": "NOT_EXECUTED"})
            adjudicated = controller.verify_disposition("PARTIAL_GENERATION",
                accepted_raw=(tmp_path / "producer/prefix-disproved.json").read_bytes(), original_K_raw=K_raw,
                history_inputs=[disproval], execution_inputs={alleged_ref["evidence_id"]: alleged},
                boundary_digest=boundary["digest"], expected_tip=log.tip, producer_id=generator.recorder["actor_id"],
                generator=generator, snapshot=paused)
            assert adjudicated["receipt"].disposition == "DISPROVED"
            with pytest.raises(ValueError):  # the paused prefix is mandatory during partial generation
                controller.release("PARTIAL_GENERATION", adjudicated["receipt"], expected_tip=log.tip,
                    operation_id="synthetic-operation", evidence=adjudicated["evidence"], original_bindings_valid=True)
            released = controller.release("PARTIAL_GENERATION", adjudicated["receipt"], expected_tip=log.tip,
                operation_id="synthetic-operation", evidence=adjudicated["evidence"], original_bindings_valid=True,
                snapshot=paused, scope="remaining original synthetic draws")
            assert released["event"]["body"]["event_kind"] == "RELEASE"
            supplement_chain += [record_ref(hold), record_ref(released["lead_continuation"]),
                                 record_ref(released["event"])]
            current_tip = log.tip
            authority_tips.append(current_tip)
    payload = generator.complete(expected_tip=current_tip, preceding_chain_tip=current_tip)
    assert len(calls) == 1414
    assert salt_calls == [32]
    assert [pos["value_hex"] for pos in payload["body"]["positions"]] == [f"{value:016x}" for value in range(1, 1413)]
    root = tmp_path / "producer"
    raw_payload, salt = (root / "payload.json").read_bytes(), (root / "salt.bin").read_bytes()
    expected = hashlib.sha256(b"bytefray-e9-seed-commitment-v2\n" + salt + raw_payload).hexdigest()
    boundary = json.loads((root / "boundary.json").read_bytes())
    complete_history = verify_history(accepted_raw=encode(payload["body"]["positions"]), original_K_raw=K_raw,
        history_inputs=[history_proof], execution_inputs=execution_inputs, boundary_digest=boundary["digest"],
        verifier_id=verifier["actor_id"], producer_id=generator.recorder["actor_id"])
    result = verify_complete_private(payload_raw=raw_payload, salt_raw=salt, audit_raw=(root / "audit.json").read_bytes(),
        original_K_raw=K_raw, expected_bindings=log.bindings, inventory_refs=refs,
        operation_id="synthetic-operation", generation_boundary=boundary, expected_commitment=expected,
        authority_tips=authority_tips, preceding_chain_tip=current_tip, supplemented_history=["0000000000000000"],
        supplement_chain=supplement_chain, history_receipts=[complete_history], resolver=log.resolve,
        artifact_reader=log.read_artifact, entropy_source="SYNTHETIC")
    assert result["decision"] == "PASS"
    assert result["accepted_count"] == 1412
    assert result["entropy_source"] == "SYNTHETIC"
    assert authority_tips == [authority_tips[0], supplement_chain[2]["digest"], supplement_chain[5]["digest"]]
    for chain in (supplement_chain[:-1], supplement_chain[:3]):  # unbound release; omitted disproval segment
        with pytest.raises(ValueError):
            verify_complete_private(payload_raw=raw_payload, salt_raw=salt, audit_raw=(root / "audit.json").read_bytes(),
                original_K_raw=K_raw, expected_bindings=log.bindings, inventory_refs=refs,
                operation_id="synthetic-operation", generation_boundary=boundary, expected_commitment=expected,
                authority_tips=authority_tips, preceding_chain_tip=current_tip, supplemented_history=["0000000000000000"],
                supplement_chain=chain, history_receipts=[complete_history], resolver=log.resolve,
                artifact_reader=log.read_artifact, entropy_source="SYNTHETIC")
    with pytest.raises(ValueError):
        generator.draw_one(expected_tip=current_tip, durable_instant=artifact(b"boundary", "boundary"))
    assert len(calls) == 1414
    with pytest.raises(ValueError):
        generator.consume(expected_tip=current_tip, boundary_evidence=artifact(b"boundary", "boundary"))

    # GENERATED-stage history after the partial continuation: the stage tuple gains S,
    # then an independent full-list supplement and a separate lead continuation.
    original = dict(log.bindings)
    common = {"salt_raw": salt, "original_K_raw": K_raw, "expected_bindings": original,
        "inventory_refs": refs, "operation_id": "synthetic-operation", "generation_boundary": boundary,
        "authority_tips": authority_tips, "resolver": log.resolve, "artifact_reader": log.read_artifact,
        "entropy_source": "SYNTHETIC"}
    real = {**common, "payload_raw": raw_payload, "audit_raw": (root / "audit.json").read_bytes(),
        "expected_commitment": expected, "preceding_chain_tip": current_tip}
    log.bindings = {**original, "S": record_ref(json.loads((root / "receipt.json").read_bytes()))}
    issue_S = log.append("ISSUE", lead, expected_tip=log.tip, operation_id="synthetic-operation")
    log.retain_record(issue_S)
    hold = log.append("HOLD", verifier, expected_tip=log.tip, operation_id="synthetic-operation",
        evidence=[artifact(b"completed-stop", "completed-stop")])
    late_execution = encode({"executed_values": ["ffffffffffffffff"], "started": True, "scope": "IN_SCOPE",
        "temporal_order": "BEFORE", "generation_boundary_digest": boundary["digest"]})
    late_ref = artifact(late_execution, "completed-history-execution")
    late_proof = encode({"values": ["ffffffffffffffff"], "actual_execution": True, "scope_verified": True,
        "temporal_order": "BEFORE", "generation_boundary_digest": boundary["digest"], "execution_evidence": late_ref})
    completed = controller.completed_supplement("GENERATED", accepted_raw=encode(payload["body"]["positions"]),
        original_K_raw=K_raw, history_inputs=[late_proof], execution_inputs={late_ref["evidence_id"]: late_execution},
        generation_boundary=boundary, expected_tip=log.tip, producer_id=generator.recorder["actor_id"],
        inspection_boundary="independent synthetic full list only")
    continued = controller.release("GENERATED", completed["receipt"], expected_tip=log.tip,
        operation_id="synthetic-operation", evidence=[artifact(late_proof, "completed-history")],
        original_bindings_valid=True, supplement=completed["supplement"])
    completed_chain = [record_ref(completed["supplement"]), record_ref(continued["lead_continuation"]),
        record_ref(continued["event"])]
    both = {"supplemented_history": ["0000000000000000", "ffffffffffffffff"],
        "history_receipts": [complete_history, completed["receipt"]], "active_chain_tip": log.tip}
    gap_free = [*supplement_chain, record_ref(issue_S), record_ref(hold), *completed_chain]
    assert verify_complete_private(**real, **both, supplement_chain=gap_free)["decision"] == "PASS"
    for chain in ([*supplement_chain, record_ref(hold), *completed_chain],  # ISSUE gap
                  [*supplement_chain, *completed_chain],  # no link to the later hold
                  gap_free[:-1]):  # no final continuation event
        with pytest.raises(ValueError):
            verify_complete_private(**real, **both, supplement_chain=chain)
    with pytest.raises(ValueError):  # the payload binds a partial chain the verifier never saw
        verify_complete_private(**real, supplemented_history=["ffffffffffffffff"],
            history_receipts=[completed["receipt"]], active_chain_tip=log.tip, supplement_chain=completed_chain)
    with pytest.raises(ValueError):
        verify_complete_private(**real)
    with pytest.raises(ValueError):  # the prefix receipt never substitutes for full-list verification
        verify_complete_private(**real, supplemented_history=["0000000000000000"],
            history_receipts=[supplement["receipt"]], supplement_chain=supplement_chain)

    def resealed(**changes):
        alternative = encode(make_record("SeedPayload", {**payload["body"], **changes}))
        return {"payload_raw": alternative, "expected_commitment": hashlib.sha256(
            b"bytefray-e9-seed-commitment-v2\n" + salt + alternative).hexdigest()}

    # A stale seal that omits the partial chain: later draws ran under an unverified tip.
    stale = {**common, **resealed(preceding_chain_tip=authority_tips[0]),
        "audit_raw": real["audit_raw"], "preceding_chain_tip": authority_tips[0]}
    with pytest.raises(ValueError):
        verify_complete_private(**stale)
    # A final list that replaces retained prefix position 1 never verifies.
    entries, accepted_values, prior = [], [], boundary["digest"]
    for index, value in enumerate([0, 7, 7, 2, 1, *range(3, 7), *range(8, 1413)]):
        hex_value = f"{value:016x}"
        decision = "REJECT_K" if value == 0 else "REJECT_DUPLICATE" if hex_value in accepted_values else "ACCEPT"
        entry = {"raw_draw_ordinal": index + 1, "raw_bytes_hex": hex_value, "disposition": decision,
            "accepted_position": len(accepted_values) + 1 if decision == "ACCEPT" else None,
            "authority_tip": authority_tips[0] if index < 4 else authority_tips[1] if index < 8 else authority_tips[2],
            "prior_entry_digest": prior}
        entries.append(entry)
        prior = hashlib.sha256(encode(entry)[:-1]).hexdigest()
        if decision == "ACCEPT":
            accepted_values.append(hex_value)
    replaced_audit = encode(entries)
    replaced_positions = [{"position": i, "value_hex": v} for i, v in enumerate(accepted_values, 1)]
    replaced = {**common, **resealed(positions=replaced_positions, audit=artifact(replaced_audit, "replaced-audit")),
        "audit_raw": replaced_audit, "preceding_chain_tip": current_tip}
    replaced_history = verify_history(accepted_raw=encode(replaced_positions), original_K_raw=K_raw,
        history_inputs=[history_proof], execution_inputs=execution_inputs, boundary_digest=boundary["digest"],
        verifier_id=verifier["actor_id"], producer_id=generator.recorder["actor_id"])
    with pytest.raises(ValueError):
        verify_complete_private(**replaced, supplemented_history=["0000000000000000"],
            history_receipts=[replaced_history], supplement_chain=supplement_chain)


def test_entropy_source_is_explicit_bound_at_the_boundary_and_fixed_for_the_operation(tmp_path, monkeypatch):
    generator, log, _, recorder, _, calls, _, refs, K_raw = producer_fixture(tmp_path, monkeypatch, [1, 2])
    base = {"operation_id": "synthetic-operation", "recorder": recorder, "original_K_raw": K_raw,
            "inventory_refs": refs}
    with pytest.raises(TypeError):  # no implicit synthetic default
        Generator(generator.root, log, **base, draw_bytes=generator.draw_bytes, salt_bytes=generator.salt_bytes)
    with pytest.raises(ValueError):  # real OS-CSPRNG generation accepts no injected stream
        Generator(generator.root, log, **base, draw_bytes=generator.draw_bytes, salt_bytes=None, mode="REAL")
    generator.consume(expected_tip=log.tip, boundary_evidence=artifact(b"boundary", "boundary"))
    generator.draw_one(expected_tip=log.tip, durable_instant=artifact(b"boundary", "boundary"))
    boundary = json.loads((tmp_path / "producer/boundary.json").read_bytes())
    declared = [json.loads(log.read_artifact(ref)) for ref in boundary["body"]["evidence"]
                if json.loads(log.read_artifact(ref)).get("kind") == "ENTROPY_SOURCE_V2"]
    assert declared == [{"kind": "ENTROPY_SOURCE_V2", "mode": "SYNTHETIC",
        "draw_source": "injected deterministic synthetic byte stream",
        "salt_source": "injected deterministic synthetic byte stream", "study_id": "synthetic-e9-v2-only",
        "G": log.bindings["G"], "operation_id": "synthetic-operation"}]
    # The same registered producer resumed with the other source fails before any draw.
    resumed = Generator(generator.root, log, **base, draw_bytes=None, salt_bytes=None, mode="REAL")
    with pytest.raises(ValueError, match="entropy source"):
        resumed.draw_one(expected_tip=log.tip, durable_instant=artifact(b"boundary", "boundary"))
    assert calls == [8]
    generator.draw_one(expected_tip=log.tip, durable_instant=artifact(b"boundary", "boundary"))
    assert calls == [8, 8]


def test_post_boundary_only_use_releases_the_same_paused_operation(tmp_path, monkeypatch):
    generator, log, lead, _, verifier, calls, salt_calls, _, K_raw = producer_fixture(
        tmp_path, monkeypatch, [0, 1, 1, 2, 3])
    generator.consume(expected_tip=log.tip, boundary_evidence=artifact(b"boundary", "boundary"))
    for _ in range(4):
        generator.draw_one(expected_tip=log.tip, durable_instant=artifact(b"boundary", "boundary"))
    log.append("HOLD", verifier, expected_tip=log.tip, operation_id="synthetic-operation",
               evidence=[artifact(b"stop", "stop")])
    paused = generator.snapshot(evidence=artifact(b"stop", "stop"), snapshot_id="postboundary")
    boundary = json.loads((tmp_path / "producer/boundary.json").read_bytes())
    # Accepted position 1 was later used by a qualification match that first ran after the boundary.
    later = encode({"executed_values": ["0000000000000001"], "started": True, "scope": "IN_SCOPE",
        "temporal_order": "AFTER", "generation_boundary_digest": boundary["digest"]})
    later_ref = artifact(later, "post-boundary-execution")
    proof = encode({"values": ["0000000000000001"], "actual_execution": True, "scope_verified": True,
        "temporal_order": "AFTER", "generation_boundary_digest": boundary["digest"], "execution_evidence": later_ref})
    controller = IntegrityController(log, verifier_actor=verifier, lead_actor=lead)
    adjudicated = controller.verify_disposition("PARTIAL_GENERATION",
        accepted_raw=(tmp_path / "producer/prefix-postboundary.json").read_bytes(), original_K_raw=K_raw,
        history_inputs=[proof], execution_inputs={later_ref["evidence_id"]: later},
        boundary_digest=boundary["digest"], expected_tip=log.tip, producer_id=generator.recorder["actor_id"],
        generator=generator, snapshot=paused)
    assert adjudicated["receipt"].disposition == "POST_BOUNDARY"
    assert adjudicated["receipt"].post_boundary_values == ("0000000000000001",)
    with pytest.raises(ValueError, match="stop state"):
        controller.verify_disposition("PARTIAL_GENERATION", accepted_raw=encode([]), original_K_raw=K_raw,
            history_inputs=[proof], execution_inputs={later_ref["evidence_id"]: later},
            boundary_digest=boundary["digest"], expected_tip=log.tip, producer_id=generator.recorder["actor_id"])
    with pytest.raises(ValueError):  # held: no draw before the lead's release
        generator.draw_one(expected_tip=log.tip, durable_instant=artifact(b"boundary", "boundary"))
    released = controller.release("PARTIAL_GENERATION", adjudicated["receipt"], expected_tip=log.tip,
        operation_id="synthetic-operation", evidence=adjudicated["evidence"], original_bindings_valid=True,
        snapshot=paused)
    assert released["lead_continuation"]["body"]["dependencies"]["PrefixSnapshot"] == record_ref(paused)
    entry = generator.draw_one(expected_tip=log.tip, durable_instant=artifact(b"boundary", "boundary"))
    assert entry["authority_tip"] == released["event"]["digest"] and entry["accepted_position"] == 3
    assert len(calls) == 5 and salt_calls == []
