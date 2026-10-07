"""Implementer worker doubles; no native service or entropy sources."""
from __future__ import annotations

import pytest

from engine.tests._e9_v2_synthetic_records import STUDY, actor, artifact, fixture, through_g
from tools.research.v6.e9.v2.authority import AuthorityLog
from tools.research.v6.e9.v2.dispatch import ARTIFACT_NAMES, DispatchLedger
from tools.research.v6.e9.v2.records import IntegrityError, canonical_bytes, record_ref


def full_authority(tmp_path):
    rs = through_g()
    boundary = fixture("GenerationBoundary", rs, operation_id="synthetic-operation",
                       producer_fence_epoch=0)
    rs["S"] = fixture("S", rs, operation_id="synthetic-operation", generation_boundary=record_ref(boundary))
    for role in ("W", "U", "C", "D"):
        rs[role] = fixture(role, rs)
    by_digest = {r["digest"]: r for r in (*rs.values(), boundary)}
    actors = {r["body"]["actor"]["actor_id"]: r["body"]["actor"]["role"]
              for r in rs.values() if "actor" in r["body"]}
    actors.update({"synthetic-recorder": "recorder", "synthetic-integrity": "independent_integrity_verifier",
                   "synthetic-supervisor": "external_supervisor"})
    log = AuthorityLog(tmp_path / "authority", STUDY, {r: record_ref(v) for r, v in rs.items()},
                       actors=actors, resolver=lambda ref: by_digest[ref["digest"]], source_check=lambda: None)
    log.append("ISSUE", rs["G"]["body"]["actor"], expected_tip=log.tip, operation_id="synthetic-operation")
    producer_root = tmp_path / "synthetic-producer"
    producer_root.mkdir()
    log.register_producer(producer_root, actor("recorder", "synthetic-recorder"),
                          operation_id="synthetic-operation")
    log.consume_generation(actor("recorder", "synthetic-recorder"), expected_tip=log.tip,
                           operation_id="synthetic-operation", evidence=[artifact()])
    return log


def test_one_original_and_one_fenced_identical_infrastructure_retry(tmp_path):
    log = full_authority(tmp_path)
    ledger = DispatchLedger(tmp_path / "dispatch", log)
    launched = []
    result = ledger.start("A", "RUSH8", 1, "A", expected_tip=log.tip, operation_id="synthetic-worker",
                          launch=lambda item, lease: launched.append(item))
    first = result["attempt"]
    facts = {"cell_identity": first["cell_identity"], "binding_digest": first["binding_digest"],
             "attempt": 1, "origin": "external-supervisor", "failure_class": "host_worker_loss",
             "before_completion": True, "completion_known_absent": True,
             "original_stopped_or_fenced": True, "semantic_integrity_failed": False}
    supervisor = actor("external_supervisor", "synthetic-supervisor")
    evidence = canonical_bytes({"facts": facts, "supervisor_id": supervisor["actor_id"]}) + b"\n"
    ref = {"bytes": len(evidence), "sha256_raw": __import__("hashlib").sha256(evidence).hexdigest(),
           "evidence_id": "synthetic-supervisor-proof", "visibility": "PRIVATE"}
    proof = ledger.record_failure(first["cell_identity"], facts, supervisor=supervisor,
                                  evidence_raw=evidence, evidence_ref=ref)
    second = ledger.start("A", "RUSH8", 1, "A", expected_tip=log.tip, operation_id="synthetic-worker",
        launch=lambda item, lease: launched.append(item), retry_facts=facts, failure_receipt=proof)
    assert second["attempt"]["attempt"] == 2 and len(launched) == 2
    with pytest.raises(IntegrityError):
        ledger.start("A", "RUSH8", 1, "A", expected_tip=log.tip, operation_id="synthetic-worker",
            launch=lambda item, lease: pytest.fail("third attempt"), retry_facts=facts, failure_receipt=proof)


def test_started_failed_launch_retained_and_hold_fences_complete_artifacts(tmp_path):
    log = full_authority(tmp_path)
    ledger = DispatchLedger(tmp_path / "dispatch", log)
    result = ledger.start("A", "RUSH8", 1, "A", expected_tip=log.tip, operation_id="synthetic-worker",
                          launch=lambda item, lease: None)
    log.append("HOLD", actor("independent_integrity_verifier", "synthetic-integrity"),
               expected_tip=log.tip, operation_id="synthetic-worker", evidence=[artifact()])
    receipt = ledger.complete(result["attempt"]["cell_identity"], 1, result["lease"],
                              artifacts={name: b"synthetic artifact" for name in ARTIFACT_NAMES})
    assert not receipt["eligible"] and all(r["late_fenced"] for r in receipt["receipts"].values())
    assert len(list((log.root / "retained").glob("*.bin"))) == 4
    with pytest.raises(IntegrityError):
        ledger.start("A", "RUSH8", 2, "A", expected_tip=log.tip, operation_id="synthetic-worker",
                     launch=lambda item, lease: pytest.fail("held worker start"))
