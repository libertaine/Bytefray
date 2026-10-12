"""Independent full-list audit/commitment reconstruction and corruption faults."""

from __future__ import annotations

import copy
import hashlib
import json

import pytest

from engine.tests._e9_v2_synthetic_records import STUDY, actor, fixture, through_g
from tools.research.v6.e9.v2.commitment import (
    commitment_value,
    verify_complete_private,
    verify_W_bytes,
)
from tools.research.v6.e9.v2.records import record_ref


def encode(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"),
                      allow_nan=False).encode() + b"\n"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def artifact(raw, label):
    return {"bytes": len(raw), "sha256_raw": sha(raw), "evidence_id": "independent-" + label,
            "visibility": "PRIVATE"}


def entropy_source(mode, earlier):
    # Independently written declaration: where every raw draw and the salt came from.
    source = {"REAL": "os.urandom", "SYNTHETIC": "injected deterministic synthetic byte stream"}[mode]
    return encode({"kind": "ENTROPY_SOURCE_V2", "mode": mode, "draw_source": source, "salt_source": source,
                   "study_id": STUDY, "G": record_ref(earlier["G"]), "operation_id": "synthetic-operation"})


def independent_complete_fixture(entropy_modes=("SYNTHETIC",)):
    K_raw = encode(["0000000000000000"])
    refs = {"K": artifact(K_raw, "K"), "E": artifact(encode([]), "E"), "L": artifact(encode({}), "L")}
    earlier = through_g(inventory_refs=refs)
    original = {role: record_ref(record) for role, record in earlier.items()}
    private = {}
    for mode in entropy_modes:
        raw = entropy_source(mode, earlier)
        private[sha(raw)] = raw
    boundary = fixture("GenerationBoundary", earlier, operation_id="synthetic-operation",
                       active_authority_tip="a" * 64, durable_instant=artifact(b"durable", "boundary"),
                       producer_fence_epoch=0, evidence=[artifact(private[sha(entropy_source(mode, earlier))],
                                                                  "entropy-" + mode) for mode in entropy_modes])
    audit, accepted, tip = [], [], boundary["digest"]
    for candidate in [0, 1, 1] + list(range(2, 1413)):
        value = f"{candidate:016x}"
        decision = "REJECT_K" if candidate == 0 else "REJECT_DUPLICATE" if value in accepted else "ACCEPT"
        entry = {"raw_draw_ordinal": len(audit) + 1, "raw_bytes_hex": value,
                 "disposition": decision, "accepted_position": len(accepted) + 1 if decision == "ACCEPT" else None,
                 "authority_tip": "a" * 64, "prior_entry_digest": tip}
        audit.append(entry)
        tip = sha(encode(entry)[:-1])
        if decision == "ACCEPT":
            accepted.append(value)
    audit_raw = encode(audit)
    payload = fixture("SeedPayload", {**earlier, "GenerationBoundary": boundary},
        N=1412, domain="uint64/big-endian/OS CSPRNG/accepted draw order", operation_id="synthetic-operation",
        audit=artifact(audit_raw, "audit"), inventory_refs=refs, generation_boundary=record_ref(boundary),
        positions=[{"position": i, "value_hex": value} for i, value in enumerate(accepted, 1)],
        preceding_chain_tip="a" * 64, dependencies=original)
    salt = bytes(range(32))
    payload_raw = encode(payload)
    expected = sha(b"bytefray-e9-seed-commitment-v2\n" + salt + payload_raw)
    return {"payload_raw": payload_raw, "salt_raw": salt, "audit_raw": audit_raw,
            "original_K_raw": K_raw, "expected_bindings": original, "inventory_refs": refs,
            "operation_id": "synthetic-operation", "generation_boundary": boundary,
            "expected_commitment": expected, "authority_tips": ["a" * 64],
            "preceding_chain_tip": "a" * 64, "entropy_source": "SYNTHETIC",
            "artifact_reader": lambda ref: private[ref["sha256_raw"]]}, earlier


def reseal_payload(payload):
    # Deliberately use independent serialization and hash derivation for faults.
    digest = sha(encode(payload["body"])[:-1])
    payload["digest"] = digest
    payload["identity"] = "v6-e9-seed-payload-v2-" + digest[:12]
    return encode(payload)


def test_full1412_private_read_back_reproduces_independent_commitment_and_every_raw_draw():
    inputs, _ = independent_complete_fixture()
    assert commitment_value(inputs["payload_raw"], inputs["salt_raw"]) == inputs["expected_commitment"]
    result = verify_complete_private(**inputs)
    assert result["decision"] == "PASS"
    assert result["accepted_count"] == 1412
    assert result["audit_counts"] == {"raw": 1414, "accepted": 1412, "K_rejected": 1, "duplicate_rejected": 1}
    assert result["full_private_read_back"] is True
    assert result["entropy_source"] == "SYNTHETIC"
    assert result["historical_completeness"] == "NOT ESTABLISHED"


@pytest.mark.parametrize("modes,expected", [
    ((), "SYNTHETIC"),  # no declaration bound by the boundary
    (("SYNTHETIC", "SYNTHETIC"), "SYNTHETIC"),  # duplicate declaration
    (("SYNTHETIC", "REAL"), "SYNTHETIC"),  # conflicting declarations
    (("REAL",), "SYNTHETIC"),  # a real-source declaration verified as synthetic
    (("SYNTHETIC",), "REAL"),  # a synthetic payload never verifies as OS-CSPRNG
])
def test_w_requires_exactly_the_expected_bound_entropy_source(modes, expected):
    inputs, _ = independent_complete_fixture(entropy_modes=modes)
    with pytest.raises(ValueError, match="entropy source"):
        verify_complete_private(**{**inputs, "entropy_source": expected})
    with pytest.raises(ValueError):
        verify_complete_private(**{**inputs, "entropy_source": "UNDECLARED"})


@pytest.mark.parametrize("fault", ["short_salt", "changed_salt", "bad_commitment", "prefix_only",
    "wrong_order", "duplicate_value", "bad_uint64", "wrong_domain", "wrong_study", "wrong_operation",
    "wrong_source", "wrong_tip", "private_copy", "audit_order", "audit_rejection", "history_overlap",
    "unbound_history", "audit_corruption", "original_K_member", "noncanonical_payload"])
def test_complete_private_integrity_and_primitive_commitment_failures(fault):
    inputs, _ = independent_complete_fixture()
    payload = json.loads(inputs["payload_raw"])
    body = payload["body"]
    body_mutation = False
    if fault == "short_salt":
        inputs["salt_raw"] = inputs["salt_raw"][:-1]
    elif fault == "changed_salt":
        inputs["salt_raw"] = b"x" * 32
    elif fault == "bad_commitment":
        inputs["expected_commitment"] = "0" * 64
    elif fault == "prefix_only":
        body["positions"] = body["positions"][:1]
        body_mutation = True
    elif fault == "wrong_order":
        body["positions"][0], body["positions"][1] = body["positions"][1], body["positions"][0]
        body_mutation = True
    elif fault == "duplicate_value":
        body["positions"][1]["value_hex"] = body["positions"][0]["value_hex"]
        body_mutation = True
    elif fault == "bad_uint64":
        body["positions"][0]["value_hex"] = "1" * 17
        body_mutation = True
    elif fault == "wrong_domain":
        body["domain"] = "bytefray-e9-seed-commitment-v1"
        body_mutation = True
    elif fault == "wrong_study":
        body["study_id"] = "other-synthetic-study"
        body_mutation = True
    elif fault == "wrong_operation":
        inputs["operation_id"] = "other-synthetic-operation"
    elif fault == "wrong_source":
        inputs["expected_bindings"] = copy.deepcopy(inputs["expected_bindings"])
        inputs["expected_bindings"]["I"]["sha256_raw"] = "f" * 64
    elif fault == "wrong_tip":
        inputs["authority_tips"] = ["f" * 64]
    elif fault == "private_copy":
        inputs["original_K_raw"] = encode([])
    elif fault in ("audit_order", "audit_rejection"):
        audit = json.loads(inputs["audit_raw"])
        if fault == "audit_order":
            audit[0], audit[1] = audit[1], audit[0]
        else:
            audit[0]["disposition"] = "ACCEPT"
        inputs["audit_raw"] = encode(audit)
        body["audit"] = artifact(inputs["audit_raw"], "audit")
        body_mutation = True
    elif fault == "history_overlap":
        inputs["supplemented_history"] = [body["positions"][0]["value_hex"]]
    elif fault == "unbound_history":
        inputs["supplemented_history"] = ["ffffffffffffffff"]
    elif fault == "original_K_member":
        body["positions"][0]["value_hex"] = "0000000000000000"
        body_mutation = True
    elif fault == "noncanonical_payload":
        # Same JSON value, different bytes: the commitment matches but bytes are not canonical.
        inputs["payload_raw"] = inputs["payload_raw"].replace(b"{", b"{ ", 1)
        inputs["expected_commitment"] = sha(b"bytefray-e9-seed-commitment-v2\n" + inputs["salt_raw"] + inputs["payload_raw"])
    else:
        inputs["audit_raw"] += b"\n"
    if body_mutation:
        inputs["payload_raw"] = reseal_payload(payload)
        inputs["expected_commitment"] = sha(b"bytefray-e9-seed-commitment-v2\n" + inputs["salt_raw"] + inputs["payload_raw"])
    with pytest.raises(ValueError):
        verify_complete_private(**inputs)


def test_ds_w7_complete_primitive_c_and_artifact_byte_reproduction():
    inputs, earlier = independent_complete_fixture()
    earlier["S"] = fixture("S", earlier, generation_boundary=record_ref(inputs["generation_boundary"]))
    W = fixture("W", earlier, actor=actor("independent_verifier", "independent-fixture"),
                commitment=inputs["expected_commitment"], payload=artifact(inputs["payload_raw"], "payload"),
                salt=artifact(inputs["salt_raw"], "salt"))
    verify_W_bytes(W, payload_raw=inputs["payload_raw"], salt_raw=inputs["salt_raw"],
                   expected_commitment=inputs["expected_commitment"])
    with pytest.raises(ValueError):
        verify_W_bytes(W, payload_raw=inputs["payload_raw"], salt_raw=b"x" * 32,
                       expected_commitment=inputs["expected_commitment"])
