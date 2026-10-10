"""Independent worker doubles, recovery cap and arrival fencing; no matches."""

from __future__ import annotations

import hashlib
import json

import pytest

from engine.tests._e9_v2_synthetic_records import actor, artifact, fixture
from engine.tests.test_v6_e9_v2_dispatch import full_authority
from tools.research.v6.e9.v2.authority import AuthorityLog
from tools.research.v6.e9.v2.dispatch import DispatchLedger
from tools.research.v6.e9.v2.records import record_ref

ARTIFACT_NAMES = ("result.json", "replay.jsonl", "trace.jsonl", "diagnostic.json")


def begin(tmp_path):
    log = full_authority(tmp_path)
    ledger = DispatchLedger(tmp_path / "independent-dispatch", log)
    result = ledger.start("A", "RUSH8", 1, "A", expected_tip=log.tip,
        operation_id="independent-worker", launch=lambda item, lease: None)
    first = result["attempt"]
    facts = {"cell_identity": first["cell_identity"], "binding_digest": first["binding_digest"],
             "attempt": 1, "origin": "external-supervisor", "failure_class": "host_worker_loss",
             "before_completion": True, "completion_known_absent": True,
             "original_stopped_or_fenced": True, "semantic_integrity_failed": False}
    return log, ledger, result, facts


def proof(ledger, facts):
    supervisor = actor("external_supervisor", "synthetic-supervisor")
    raw = json.dumps({"facts": facts, "supervisor_id": supervisor["actor_id"]},
                     sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode() + b"\n"
    ref = {"bytes": len(raw), "sha256_raw": hashlib.sha256(raw).hexdigest(),
           "evidence_id": "independent-supervisor-receipt", "visibility": "PRIVATE"}
    return ledger.record_failure(facts["cell_identity"], facts, supervisor=supervisor,
                                 evidence_raw=raw, evidence_ref=ref)


def test_independently_verified_failure_allows_exact_second_attempt_and_never_third(tmp_path):
    log, ledger, result, facts = begin(tmp_path)
    receipt = proof(ledger, facts)
    second = ledger.start("A", "RUSH8", 1, "A", expected_tip=log.tip,
        operation_id="independent-worker", launch=lambda item, lease: None,
        retry_facts=facts, failure_receipt=receipt)
    assert second["attempt"]["attempt"] == 2
    assert second["attempt"]["binding_tuple"] == result["attempt"]["binding_tuple"]
    assert second["attempt"]["cell"] == result["attempt"]["cell"]
    with pytest.raises(ValueError):
        ledger.start("A", "RUSH8", 1, "A", expected_tip=log.tip,
            operation_id="independent-worker", launch=lambda item, lease: pytest.fail("third worker launch"),
            retry_facts=facts, failure_receipt=receipt)


@pytest.mark.parametrize("field,value", [("failure_class", "unknown"), ("semantic_integrity_failed", True),
    ("completion_known_absent", False), ("original_stopped_or_fenced", False), ("binding_digest", "0" * 64),
    ("payoff", "outcome-forbidden")])
def test_worker_failures_never_invent_eligible_infrastructure_retry(tmp_path, field, value):
    _, ledger, _, facts = begin(tmp_path)
    facts[field] = value
    with pytest.raises(ValueError):
        proof(ledger, facts)


def test_terminal_completion_blocks_failure_receipt_and_retry(tmp_path):
    log, ledger, result, facts = begin(tmp_path)
    receipt = ledger.complete(facts["cell_identity"], 1, result["lease"],
        artifacts={name: b"independent synthetic complete artifact" for name in ARTIFACT_NAMES})
    assert receipt["eligible"] is True
    with pytest.raises(ValueError):
        proof(ledger, facts)
    with pytest.raises(ValueError):
        ledger.start("A", "RUSH8", 1, "A", expected_tip=log.tip, operation_id="independent-worker",
            launch=lambda item, lease: pytest.fail("completed worker retry"), retry_facts=facts)


def test_hold_fences_all_four_late_artifacts_and_new_starts(tmp_path):
    log, ledger, result, facts = begin(tmp_path)
    log.append("HOLD", actor("independent_integrity_verifier", "synthetic-integrity"),
        expected_tip=log.tip, operation_id="independent-worker", evidence=[artifact()])
    receipt = ledger.complete(facts["cell_identity"], 1, result["lease"],
        artifacts={name: b"independent synthetic late artifact" for name in ARTIFACT_NAMES})
    assert receipt["eligible"] is False
    assert all(part["late_fenced"] for part in receipt["receipts"].values())
    assert len(list((log.root / "retained").glob("*.bin"))) == 4
    with pytest.raises(ValueError):
        ledger.start("A", "RUSH8", 2, "A", expected_tip=log.tip, operation_id="independent-worker",
            launch=lambda item, lease: pytest.fail("held worker launch"))


def test_changed_current_tuple_never_promotes_old_worker_completion(tmp_path):
    log, ledger, result, facts = begin(tmp_path)
    log.bindings["I"] = {**log.bindings["I"], "sha256_raw": "f" * 64}
    receipt = ledger.complete(facts["cell_identity"], 1, result["lease"],
        artifacts={name: b"independent mixed-tuple artifact" for name in ARTIFACT_NAMES})
    assert receipt["eligible"] is False


def test_stopped_original_worker_cannot_promote_late_completion_after_retry_start(tmp_path):
    log, ledger, result, facts = begin(tmp_path)
    failure_receipt = proof(ledger, facts)
    ledger.start("A", "RUSH8", 1, "A", expected_tip=log.tip, operation_id="independent-worker",
        launch=lambda item, lease: None, retry_facts=facts, failure_receipt=failure_receipt)
    receipt = ledger.complete(facts["cell_identity"], 1, result["lease"],
        artifacts={name: b"independent stopped original late artifact" for name in ARTIFACT_NAMES})
    assert receipt["eligible"] is False


def test_full_record_bindings_never_hide_mismatched_primitive_w_u_c_commitment(tmp_path):
    original = full_authority(tmp_path / "original")
    records = {role: original.resolve(ref) for role, ref in original.bindings.items()}
    earlier = {role: record for role, record in records.items() if role not in {"U", "C", "D"}}
    earlier["U"] = fixture("U", earlier, commitment="b" * 64)
    earlier["C"] = fixture("C", earlier, commitment="0" * 64)
    earlier["D"] = fixture("D", earlier)
    by_digest = {record["digest"]: record for record in earlier.values()}
    boundary = original.resolve(records["S"]["body"]["generation_boundary"])
    by_digest[boundary["digest"]] = boundary
    log = AuthorityLog(tmp_path / "mismatched-authority", original.study_id,
        {role: record_ref(record) for role, record in earlier.items()},
        actors=original.actors, resolver=lambda ref: by_digest[ref["digest"]], source_check=lambda: None)
    log.append("ISSUE", earlier["G"]["body"]["actor"], expected_tip=log.tip,
               operation_id="synthetic-operation")
    producer_root = tmp_path / "mismatched-registered-producer"
    producer_root.mkdir()
    log.register_producer(producer_root, actor("recorder", "synthetic-recorder"),
        operation_id="synthetic-operation")
    log.consume_generation(actor("recorder", "synthetic-recorder"), expected_tip=log.tip,
        operation_id="synthetic-operation", evidence=[artifact()])
    ledger = DispatchLedger(tmp_path / "mismatched-dispatch", log)
    with pytest.raises(ValueError):
        ledger.start("A", "RUSH8", 2, "A", expected_tip=log.tip, operation_id="independent-worker",
            launch=lambda item, lease: pytest.fail("mismatched primitive commitment worker"))
