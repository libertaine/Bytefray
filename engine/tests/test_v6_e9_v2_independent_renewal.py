"""Independent original-producer exclusivity and actual pre-draw reapproval."""
from __future__ import annotations

import copy
import json

import pytest

from engine.tests._e9_v2_synthetic_records import actor, fixture, through_g
from engine.tests.test_v6_e9_v2_independent_generation import artifact, encode, producer_fixture
from tools.research.v6.e9.v2.authority import AuthorityLog
from tools.research.v6.e9.v2.generation import Generator
from tools.research.v6.e9.v2.records import record_ref


def replacement(log, generator):
    refs = copy.deepcopy(generator.inventory_refs)
    refs["E"] = artifact(encode({"synthetic_changed_evidence_same_K": True}), "renewed-E")
    new_records = through_g(inventory_refs=refs)
    all_records = {record["digest"]: record for record in
        [*(log.resolve(ref) for ref in log.bindings.values()), *new_records.values()]}
    log.resolver = lambda ref: all_records[ref["digest"]]
    return {role: record_ref(record) for role, record in new_records.items()}, refs


@pytest.mark.parametrize("consumed", [False, True])
def test_same_k_new_evidence_reapproval_preserves_old_history_and_allows_only_new_g_first_draw(tmp_path, monkeypatch, consumed):
    generator, log, lead, recorder, verifier, calls, _, _, K_raw = producer_fixture(tmp_path, monkeypatch, [1])
    if consumed:
        generator.consume(expected_tip=log.tip, boundary_evidence=artifact(b"before-boundary", "boundary"))
    old_bindings = copy.deepcopy(log.bindings)
    new_bindings, refs = replacement(log, generator)
    assert new_bindings["G"] != old_bindings["G"]
    assert all(new_bindings[role] == old_bindings[role] for role in ("P", "I", "Q"))
    log.append("HOLD", verifier, expected_tip=log.tip, operation_id="synthetic-operation",
        evidence=[artifact(b"renewal-stop", "stop")])
    old_raw = {path.name: path.read_bytes() for path in log.root.glob("event-*.json")}
    result = log.renew_before_generation(new_bindings, lead, verifier, expected_tip=log.tip,
        producer_roots=log.registered_producers(), evidence=[artifact(b"no-first-draw-independent-inspection", "inspection")])
    assert [result[key]["body"]["event_kind"] for key in ("revocation", "issue", "release")] == ["REVOKE", "ISSUE", "RELEASE"]
    assert all((log.root / name).read_bytes() == raw for name, raw in old_raw.items())
    state = log._state()
    assert state["active_bindings"] == new_bindings and state["held"] is False
    assert old_bindings["G"]["digest"] in state["revoked"]
    if consumed:
        assert old_bindings["G"]["digest"] in state["consumed"]
    receipt = json.loads(log.read_artifact(result["receipt"]))
    assert receipt["verified_no_first_draw"] is True
    assert receipt["old_bindings"] == old_bindings and receipt["new_bindings"] == new_bindings
    restarted = AuthorityLog(log.root, log.study_id, new_bindings, actors=log.actors,
        resolver=log.resolver, source_check=lambda: None)
    assert restarted.tip == log.tip
    with pytest.raises(ValueError):
        generator.draw_one(expected_tip=log.tip, durable_instant=artifact(b"boundary", "boundary"))
    renewed_calls = []

    def draw(size):
        renewed_calls.append(size)
        marker = restarted.root / "first-raw" / (new_bindings["G"]["digest"] + ".json")
        assert marker.exists()
        return (1).to_bytes(size, "big")

    renewed = Generator(tmp_path / "renewed-producer", restarted, operation_id="synthetic-operation",
        recorder=recorder, original_K_raw=K_raw, inventory_refs=refs,
        draw_bytes=draw, salt_bytes=lambda size: pytest.fail("incomplete renewed salt"), mode="SYNTHETIC")
    renewed.consume(expected_tip=restarted.tip, boundary_evidence=artifact(b"new-boundary", "boundary"))
    assert renewed.draw_one(expected_tip=restarted.tip, durable_instant=artifact(b"new-boundary", "boundary"))["accepted_position"] == 1
    assert calls == [] and renewed_calls == [8]


@pytest.mark.parametrize("fault", ["stale_tip", "unregistered_root_map", "changed_P", "same_G",
    "not_held", "after_draw", "boundary_only", "raw_intent_only", "missing_registered_root", "missing_evidence"])
def test_pre_generation_renewal_refuses_unverified_absence_mixed_or_unapproved_replacements(tmp_path, monkeypatch, fault):
    generator, log, lead, _, verifier, calls, _, _, _ = producer_fixture(tmp_path, monkeypatch, [1])
    old = copy.deepcopy(log.bindings)
    new, _ = replacement(log, generator)
    if fault == "after_draw":
        generator.consume(expected_tip=log.tip, boundary_evidence=artifact(b"boundary", "boundary"))
        generator.draw_one(expected_tip=log.tip, durable_instant=artifact(b"boundary", "boundary"))
    elif fault == "boundary_only":
        (generator.root / "boundary.json").write_bytes(b"synthetic interrupted boundary")
    elif fault == "raw_intent_only":
        (generator.root / "draw-00000001.intent.json").write_bytes(b"synthetic interrupted raw intent")
    elif fault == "missing_registered_root":
        generator.root.rmdir()
    if fault != "not_held":
        log.append("HOLD", verifier, expected_tip=log.tip, operation_id="synthetic-operation",
            evidence=[artifact(b"stop", "stop")])
    roots, expected = log.registered_producers(), log.tip
    if fault == "stale_tip":
        expected = "f" * 64
    elif fault == "unregistered_root_map":
        roots = {}
    elif fault == "changed_P":
        new["P"] = {**new["P"], "sha256_raw": "f" * 64}
    elif fault == "same_G":
        new = old
    prior_tip = log.tip
    with pytest.raises(ValueError):
        log.renew_before_generation(new, lead, verifier, expected_tip=expected, producer_roots=roots,
            evidence=[] if fault == "missing_evidence" else [artifact(b"inspection", "inspection")])
    assert log.tip == prior_tip and log.bindings == old
    assert calls == ([8] if fault == "after_draw" else [])


@pytest.mark.parametrize("fault", ["new_root", "changed_recorder", "lost_boundary", "lost_registry", "changed_root_after_constructor"])
def test_one_consumed_g_cannot_fork_or_restart_its_retained_original_list(tmp_path, monkeypatch, fault):
    generator, log, _, recorder, _, calls, _, refs, K_raw = producer_fixture(tmp_path, monkeypatch, [1, 2])
    generator.consume(expected_tip=log.tip, boundary_evidence=artifact(b"boundary", "boundary"))
    generator.draw_one(expected_tip=log.tip, durable_instant=artifact(b"boundary", "boundary"))
    boundary_raw = (generator.root / "boundary.json").read_bytes()
    if fault in ("new_root", "changed_recorder"):
        alternative = actor("recorder", "independent-alternative-recorder")
        log.actors[alternative["actor_id"]] = alternative["role"]
        with pytest.raises(ValueError):
            Generator(tmp_path / "fork" if fault == "new_root" else generator.root, log,
                operation_id="synthetic-operation", recorder=alternative if fault == "changed_recorder" else recorder,
                original_K_raw=K_raw, inventory_refs=refs,
                draw_bytes=lambda size: pytest.fail("fork raw draw"), salt_bytes=lambda size: pytest.fail("fork salt"),
                mode="SYNTHETIC")
    else:
        if fault == "lost_boundary":
            # Deterministic fault injection removes only the original synthetic boundary.
            (tmp_path / "fault-preserved-boundary.bin").write_bytes(boundary_raw)
            (generator.root / "boundary.json").unlink()
        elif fault == "lost_registry":
            path = log._producer_path(log.bindings["G"]["digest"])
            (tmp_path / "fault-preserved-registry.bin").write_bytes(path.read_bytes())
            path.unlink()
        else:
            changed = tmp_path / "changed-root"
            changed.mkdir()
            generator.root = changed
        with pytest.raises(ValueError):
            generator.draw_one(expected_tip=log.tip, durable_instant=artifact(b"boundary", "boundary"))
    assert calls == [8]
    if fault != "lost_boundary":
        assert (tmp_path / "producer/boundary.json").read_bytes() == boundary_raw


def test_restart_exact_registered_producer_continues_existing_audit_without_new_consumption(tmp_path, monkeypatch):
    original, log, _, recorder, _, calls, _, refs, K_raw = producer_fixture(tmp_path, monkeypatch, [1])
    original.consume(expected_tip=log.tip, boundary_evidence=artifact(b"boundary", "boundary"))
    original.draw_one(expected_tip=log.tip, durable_instant=artifact(b"boundary", "boundary"))
    prior_tip = log.tip
    resumed_calls = []

    def next_draw(size):
        resumed_calls.append(size)
        return (2).to_bytes(size, "big")

    restarted = Generator(original.root, log, operation_id="synthetic-operation", recorder=recorder,
        original_K_raw=K_raw, inventory_refs=refs, draw_bytes=next_draw,
        salt_bytes=lambda size: pytest.fail("incomplete restart salt"), mode="SYNTHETIC")
    assert restarted.producer_ref == original.producer_ref
    assert restarted.draw_one(expected_tip=log.tip, durable_instant=artifact(b"boundary", "boundary"))["accepted_position"] == 2
    assert restarted.read_audit()[1] == ["0000000000000001", "0000000000000002"]
    assert calls == resumed_calls == [8] and log.tip == prior_tip


def test_optional_synthetic_t_is_anchored_before_o_and_preserved_in_original_generation_tuple(tmp_path):
    # This is a wire fixture. No qualification match or real consumed value exists.
    K_raw = encode(["0000000000000000"])
    refs = {"K": artifact(K_raw, "optional-T-K"), "E": artifact(encode([]), "optional-T-E"),
        "L": artifact(encode({}), "optional-T-L")}
    records = {}
    for role in ("P", "I", "Q", "T", "O", "V", "A", "R", "B", "G"):
        extra = dict(refs) if role in ("O", "A", "R") else {}
        if role == "O":
            extra["dependencies"] = {key: record_ref(records[key]) for key in ("P", "I", "Q", "T")}
        if role == "G":
            extra["operation_id"] = "synthetic-operation"
        records[role] = fixture(role, records, **extra)
    by_digest = {record["digest"]: record for record in records.values()}
    recorder = actor("recorder", "optional-T-synthetic-recorder")
    verifier = actor("independent_integrity_verifier", "optional-T-synthetic-verifier")
    registry = {record["body"]["actor"]["actor_id"]: record["body"]["actor"]["role"]
        for record in records.values() if "actor" in record["body"]}
    registry[recorder["actor_id"]] = recorder["role"]
    registry[verifier["actor_id"]] = verifier["role"]
    log = AuthorityLog(tmp_path / "optional-T-authority", "synthetic-e9-v2-only",
        {role: record_ref(record) for role, record in records.items()}, actors=registry,
        resolver=lambda ref: by_digest[ref["digest"]], source_check=lambda: None)
    log.append("ISSUE", records["G"]["body"]["actor"], expected_tip=log.tip,
        operation_id="synthetic-operation")
    calls = []

    def draw(size):
        calls.append(size)
        return (1).to_bytes(size, "big")

    producer = Generator(tmp_path / "optional-T-producer", log, operation_id="synthetic-operation",
        recorder=recorder, original_K_raw=K_raw, inventory_refs=refs, draw_bytes=draw,
        salt_bytes=lambda size: pytest.fail("incomplete optional-T salt"), mode="SYNTHETIC")
    producer.consume(expected_tip=log.tip, boundary_evidence=artifact(b"boundary", "boundary"))
    producer.draw_one(expected_tip=log.tip, durable_instant=artifact(b"boundary", "boundary"))
    boundary = json.loads((producer.root / "boundary.json").read_bytes())
    assert boundary["body"]["dependencies"]["T"] == record_ref(records["T"])
    assert log.registered_producers()[records["G"]["digest"]]["binding_tuple"]["T"] == record_ref(records["T"])
    log.append("HOLD", verifier, expected_tip=log.tip, operation_id="synthetic-operation",
        evidence=[artifact(b"synthetic-stop", "stop")])
    snapshot = producer.snapshot(evidence=artifact(b"synthetic-stop", "stop"), snapshot_id="optionalT")
    assert snapshot["body"]["dependencies"]["T"] == record_ref(records["T"])
    # Typed standalone shapes preserve T through O/S; W/U/C exact maps stay frozen.
    records["S"] = fixture("S", records, generation_boundary=record_ref(boundary))
    for role, expected in (("W", {"P", "I", "Q", "O", "V", "A", "R", "B", "G", "S"}),
        ("U", {"P", "I", "Q", "O", "V", "A", "R", "B", "G", "S", "W"}),
        ("C", {"P", "I", "Q", "O", "V", "A", "R", "B", "G", "S", "W", "U"})):
        records[role] = fixture(role, records)
        assert set(records[role]["body"]["dependencies"]) == expected
    assert calls == [8]
