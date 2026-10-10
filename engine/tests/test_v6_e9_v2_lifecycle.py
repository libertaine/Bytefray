"""Implementer checks: injected synthetic bytes only; no match execution imports."""

from __future__ import annotations

from pathlib import Path

import pytest

from engine.tests._e9_v2_synthetic_records import STUDY, actor, fixture
from tools.research.v6.e9.v2.authority import AuthorityLog
from tools.research.v6.e9.v2.generation import Generator
from tools.research.v6.e9.v2.integrity import adjudicate
from tools.research.v6.e9.v2.inventory import artifact, frozen_limitations, verify_known_inventory
from tools.research.v6.e9.v2.records import IntegrityError, canonical_bytes, record_ref, sha256


def raw(value: object) -> bytes:
    return canonical_bytes(value) + b"\n"


def operational(K_raw: bytes) -> tuple[dict, dict]:
    refs = {"K": artifact(K_raw, "SYNTHETIC-K"), "E": artifact(raw([]), "SYNTHETIC-E"),
            "L": artifact(raw({}), "SYNTHETIC-L")}
    records = {}
    for role in ("P", "I", "Q", "O", "V", "A", "R", "B", "G"):
        overrides = dict(refs) if role in {"O", "A", "R"} else {}
        if role == "G":
            overrides["operation_id"] = "synthetic-operation"
        records[role] = fixture(role, records, **overrides)
    return records, refs


def authority(tmp_path: Path, records: dict) -> AuthorityLog:
    by_digest = {record["digest"]: record for record in records.values()}
    actors = {record["body"]["actor"]["actor_id"]: record["body"]["actor"]["role"]
              for record in records.values() if "actor" in record["body"]}
    actors["synthetic-recorder"] = "recorder"
    actors["synthetic-integrity"] = "independent_integrity_verifier"
    return AuthorityLog(tmp_path / "authority", STUDY,
                        {r: record_ref(v) for r, v in records.items()}, actors=actors,
                        resolver=lambda ref: by_digest[ref["digest"]], source_check=lambda: None)


def test_durable_consumption_replay_and_guarded_action(tmp_path: Path) -> None:
    records, _ = operational(raw(["0000000000000001"]))
    log = authority(tmp_path, records)
    lead = records["G"]["body"]["actor"]
    log.append("ISSUE", lead, expected_tip=log.tip, operation_id="synthetic-operation")
    recorder = actor("recorder", "synthetic-recorder")
    producer_root = tmp_path / "producer"
    producer_root.mkdir()
    log.register_producer(producer_root, recorder, operation_id="synthetic-operation")
    log.consume_generation(recorder, expected_tip=log.tip, operation_id="synthetic-operation",
                           evidence=[artifact(b"synthetic", "BOUNDARY")])
    tip = log.tip
    assert log.protected("raw_draw", expected_tip=tip, operation_id="synthetic-operation",
                         action=lambda lease: lease.epoch) == 0
    with pytest.raises(IntegrityError):
        log.consume_generation(recorder, expected_tip=tip, operation_id="synthetic-operation",
                               evidence=[])
    assert log.tip == tip
    with pytest.raises(IntegrityError):
        log.protected("raw_draw", expected_tip=tip, operation_id="different-operation",
                      action=lambda lease: pytest.fail("unauthorized action"))


def test_prefix_retains_rejections_and_hold_blocks_entropy(tmp_path: Path) -> None:
    K_raw = raw(["0000000000000001"])
    records, refs = operational(K_raw)
    log = authority(tmp_path, records)
    log.append("ISSUE", records["G"]["body"]["actor"], expected_tip=log.tip,
               operation_id="synthetic-operation")
    draws = iter((1, 2, 2, 3))
    calls: list[int] = []
    def injected(size: int) -> bytes:
        calls.append(size)
        return next(draws).to_bytes(size, "big")
    generator = Generator(tmp_path / "generation", log, operation_id="synthetic-operation",
                          recorder=actor("recorder", "synthetic-recorder"), original_K_raw=K_raw,
                          inventory_refs=refs, draw_bytes=injected,
                          salt_bytes=lambda size: pytest.fail("salt before list completion"),
                          mode="SYNTHETIC")
    boundary = artifact(b"synthetic-before-first-draw", "BOUNDARY")
    generator.consume(expected_tip=log.tip, boundary_evidence=boundary)
    for _ in range(4):
        generator.draw_one(expected_tip=log.tip, durable_instant=boundary)
    entries, accepted, tip = generator.read_audit()
    assert [e["disposition"] for e in entries] == ["REJECT_K", "ACCEPT", "REJECT_DUPLICATE", "ACCEPT"]
    assert accepted == ["0000000000000002", "0000000000000003"]
    assert len(tip) == 64 and calls == [8, 8, 8, 8]
    with pytest.raises(IntegrityError):  # a prefix is sealed only at the producer stop
        generator.snapshot(evidence=artifact(b"stop", "STOP"), snapshot_id="early")
    log.append("HOLD", actor("independent_integrity_verifier", "synthetic-integrity"),
               expected_tip=log.tip, operation_id="synthetic-operation", evidence=[boundary])
    snapshot = generator.snapshot(evidence=artifact(b"stop", "STOP"), snapshot_id="one")
    assert snapshot["body"]["accepted_count"] == 2
    with pytest.raises(IntegrityError):
        generator.draw_one(expected_tip=log.tip, durable_instant=boundary)
    with pytest.raises(IntegrityError):
        generator.complete(expected_tip=log.tip, preceding_chain_tip=log.tip)
    assert calls == [8, 8, 8, 8]


def inventory_fixture() -> tuple[bytes, bytes, bytes, dict]:
    from engine.tests.test_v6_e9_v2_independent_inventory import revealed
    entries, sources, K = [], {}, []
    for index, kind in enumerate(("E6", "E8", "KNOWN", "CONSERVATIVE"), 1):
        values = revealed(kind) if kind in ("E6", "E8") else [f"{index:016x}"]
        K.extend(values)
        source_raw = raw({"values": values})
        proof_raw = raw({"actual_execution": kind != "CONSERVATIVE", "scope_verified": True,
                         "preboundary_verified": True, "source_sha256_raw": sha256(source_raw)})
        source_id, proof_id = "SOURCE-" + kind, "PROOF-" + kind
        sources[source_id], sources[proof_id] = source_raw, proof_raw
        entries.append({"evidence_id": source_id, "sha256_raw": sha256(source_raw), "kind": kind,
                        "recipe": "explicit", "values": values, "execution_receipt": artifact(proof_raw, proof_id),
                        "scope_verified": True, "preboundary_verified": True})
    gaps, dependencies = frozen_limitations()
    return raw(K), raw(entries), raw({
        "gap_ids": gaps, "dependency_ids": dependencies}), sources


def test_known_set_finite_and_all_limitations_preserved() -> None:
    K, E, L, sources = inventory_fixture()
    result = verify_known_inventory(K, E, L, sources=sources, inspection_boundary="synthetic-only")
    assert result["known_inventory_verification"] == "PASS"
    assert result["historical_completeness"] == "NOT ESTABLISHED"
    assert len(result["unresolved_gap_ids"]) == 357
    assert len(result["unresolved_dependency_ids"]) == 5
    with pytest.raises(IntegrityError):
        verify_known_inventory(raw([f"{i:016x}" for i in range(1, 6)]), E, L,
                               sources=sources, inspection_boundary="synthetic-only")
    with pytest.raises(IntegrityError):
        verify_known_inventory(K, E, L, sources={k: v for k, v in sources.items() if k != "SOURCE-E8"},
                               inspection_boundary="synthetic-only")


@pytest.mark.parametrize("stage", ("PARTIAL_GENERATION", "GENERATED", "COMMITMENT_PUBLIC"))
def test_precollection_cancellation_has_no_result(stage: str) -> None:
    result = adjudicate(stage, finding="OVERLAP")
    assert result["terminal"] is True
    assert result["effective_status"] == "CANCELLED_PRECOLLECTION_HISTORICAL_OVERLAP"
    assert result["result_status"] == "NOT PRODUCED"


def test_outside_K_partial_and_failed_first_cell_boundaries() -> None:
    assert adjudicate("PARTIAL_GENERATION", finding="NEW_HISTORY")["effective_status"] == (
        "CANCELLED_PRECOLLECTION_LATE_HISTORY_OUTSIDE_APPROVED_K")
    assert adjudicate("GENERATED", finding="UNRESOLVED_CLOSE",
                      first_cell_started=True)["result_status"] == "NOT EVALUABLE"
    assert adjudicate("BEFORE_GENERATION", finding="UNRESOLVED_CLOSE")["effective_status"] == (
        "INVENTORY_GATE_REOPENED")
