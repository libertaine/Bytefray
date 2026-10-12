"""Independent byte-level malformed record and typed reference checks."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest

from engine.tests._e9_v2_synthetic_records import artifact, fixture, through_g
from tools.research.v6.e9.v2 import records

ROOT = Path(__file__).resolve().parents[2]


def reference_encode(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"),
                      allow_nan=False).encode("utf-8")


def test_canonical_unicode_case_sensitive_keys_raw_lf_and_no_normalization():
    value = {"é": "e\u0301", "c": "primitive", "C": "record", "n": 1412}
    assert records.canonical_bytes(value) == reference_encode(value)
    assert records.canonical_bytes(value) != reference_encode({**value, "é": "é"})


@pytest.mark.parametrize("mutation", [
    lambda raw: b"\xef\xbb\xbf" + raw,
    lambda raw: raw[:-1],
    lambda raw: raw + b"\n",
    lambda raw: raw.replace(b'"body":', b'"body":{},"body":', 1),
    lambda raw: raw.replace(b'"version":2', b'"version":true', 1),
    lambda raw: raw.replace(b'"version":2', b'"version":1', 1),
    lambda raw: raw.replace(b'"body":', b'"unrecognized":1,"body":', 1),
    lambda raw: raw.replace(b'"body":', b'"body" :', 1),
])
def test_noncanonical_duplicate_unknown_bom_type_version_trailing_bytes_rejected(tmp_path, mutation):
    raw = (ROOT / "tools/research/v6/e9/protocol_freeze_v2_proposed_02.json").read_bytes()
    path = tmp_path / "synthetic-malformed-record.json"
    path.write_bytes(mutation(raw))
    with pytest.raises((ValueError, TypeError, KeyError)):
        records.read_record(path, role="P")


def test_raw_body_and_full_reference_digest_are_distinct():
    path = ROOT / "tools/research/v6/e9/protocol_freeze_v2_proposed_02.json"
    record = records.read_record(path, role="P")
    ref = records.record_ref(record)
    assert ref["digest"] == hashlib.sha256(reference_encode(record["body"])).hexdigest()
    assert ref["sha256_raw"] == hashlib.sha256(path.read_bytes()).hexdigest()
    assert ref["digest"] != ref["sha256_raw"]
    altered = copy.deepcopy(record)
    altered["digest"] = ref["digest"][:12] + "0" * 52
    with pytest.raises((ValueError, TypeError)):
        records.validate_record(altered)


@pytest.mark.parametrize("field,bad", [
    ("bytes", True), ("bytes", -1), ("sha256_raw", "A" * 64),
    ("visibility", "private"), ("evidence_id", ""), ("surprise", "unknown"),
])
def test_artifact_refs_are_strict_and_boolean_is_not_byte_count(field, bad):
    ref = {"bytes": 32, "evidence_id": "independent-opaque-salt-fixture",
           "sha256_raw": "a" * 64, "visibility": "PRIVATE"}
    ref[field] = bad
    with pytest.raises((ValueError, TypeError)):
        records.validate_artifact_ref(ref)


def test_artifact_and_record_refs_never_interchange():
    artifact = {"bytes": 32, "evidence_id": "opaque-fixture",
                "sha256_raw": "a" * 64, "visibility": "PRIVATE"}
    record = {"digest": "b" * 64, "sha256_raw": "a" * 64,
              "identity": "v6-e9-prereg-v2-" + "b" * 12,
              "schema": "bytefray.v6.e9.protocol_freeze", "version": 2}
    records.validate_artifact_ref(artifact)
    records.validate_record_ref(record)
    with pytest.raises((ValueError, TypeError)):
        records.validate_record_ref(artifact)
    with pytest.raises((ValueError, TypeError)):
        records.validate_artifact_ref(record)


def independent_w_body():
    # These are opaque schema fixtures; they confer no operational authority.
    cat = json.loads((ROOT / "tools/research/v6/e9/amended_record_schemas_v2_proposed_02.json").read_bytes())
    artifact = {"bytes": 32, "evidence_id": "independent-opaque-artifact",
                "sha256_raw": "a" * 64, "visibility": "PRIVATE"}
    deps = {}
    for ordinal, role in enumerate(["P", "I", "Q", "O", "V", "A", "R", "B", "G", "S"], 1):
        digest = hashlib.sha256(f"independent-schema-ref-{ordinal}".encode()).hexdigest()
        spec = cat["records"][role]
        deps[role] = {"digest": digest, "identity": spec["identity_prefix"] + digest[:12],
                      "schema": spec["schema"], "version": spec["version"], "sha256_raw": "b" * 64}
    return {"record_role": "W", "study_id": "independent-schema-study", "decision": "PASS",
            "dependencies": deps, "actor": {"actor_id": "independent-fixture-qualifier",
            "role": "independent_verifier", "authority_evidence": artifact},
            "evidence": [artifact], "active_authority_tip": "d" * 64,
            "all_position_checks": {"synthetic_fixture": "PASS"},
            "audit_reproduction": {"synthetic_fixture": "PASS"}, "commitment": "c" * 64,
            "payload": artifact, "salt": artifact, "supplement_chain": []}


def test_ds_w1_accepts_primitive_c_artifact_fields_and_actual_record_maps():
    body = independent_w_body()
    record = records.make_record("W", body)
    assert record["body"]["commitment"] == "c" * 64
    assert "c" not in record["body"]["dependencies"]
    with pytest.raises(ValueError):
        records.validate_record(record, resolver={})


@pytest.mark.parametrize("fault", ["primitive_dep_c", "fabricated_dep_c", "artifact_dep",
                                  "record_commitment", "future_U", "future_C", "missing_c",
                                  "bad_c", "record_payload", "record_salt", "artifact_evidence_record"])
def test_ds_w1_w2_w7_typed_and_future_dependency_failures(fault):
    body = independent_w_body()
    if fault == "primitive_dep_c":
        body["dependencies"]["c"] = body["commitment"]
    elif fault == "fabricated_dep_c":
        body["dependencies"]["c"] = body["dependencies"]["S"]
    elif fault == "artifact_dep":
        body["dependencies"]["S"] = body["payload"]
    elif fault == "record_commitment":
        body["commitment"] = body["dependencies"]["S"]
    elif fault.startswith("future_"):
        role = fault[-1]
        spec = records.catalogue()["records"][role]
        body["dependencies"][role] = {"digest": "a" * 64, "identity": spec["identity_prefix"] + "a" * 12,
                                      "schema": spec["schema"], "version": 2, "sha256_raw": "b" * 64}
    elif fault == "missing_c":
        del body["commitment"]
    elif fault == "bad_c":
        body["commitment"] = "C" * 64
    elif fault == "record_payload":
        body["payload"] = body["dependencies"]["S"]
    elif fault == "record_salt":
        body["salt"] = body["dependencies"]["S"]
    else:
        body["evidence"] = [body["dependencies"]["S"]]
    with pytest.raises((ValueError, TypeError)):
        records.make_record("W", body)


def test_ds_w2_u_and_c_bind_forward_without_future_record_or_primitive_dependency():
    earlier = through_g()
    boundary = fixture("GenerationBoundary", earlier)
    earlier["S"] = fixture("S", earlier, generation_boundary=records.record_ref(boundary))
    earlier["W"] = fixture("W", earlier, commitment="c" * 64)
    U = fixture("U", earlier, commitment="c" * 64)
    assert set(U["body"]["dependencies"]) == {"P", "I", "Q", "O", "V", "A", "R", "B", "G", "S", "W"}
    earlier["U"] = U
    C = fixture("C", earlier, commitment="c" * 64)
    assert set(C["body"]["dependencies"]) == {"P", "I", "Q", "O", "V", "A", "R", "B", "G", "S", "W", "U"}
    bad_u = copy.deepcopy(U["body"])
    bad_u["dependencies"]["C"] = records.record_ref(C)
    with pytest.raises(ValueError):
        records.make_record("U", bad_u)
    bad_c = copy.deepcopy(C["body"])
    del bad_c["dependencies"]["U"]
    with pytest.raises(ValueError):
        records.make_record("C", bad_c)


SCHEMA_ROLES = ("P", "I", "Q", "O", "V", "A", "R", "B", "G", "GenerationBoundary",
                "SeedPayload", "S", "W", "U", "C", "D", "F", "T", "AuthorityEvent",
                "PrefixSnapshot", "PrefixAndKVerification", "PartialGenerationSupplement",
                "CompletedMembershipSupplement", "LeadContinuation", "J")


def independent_schema_records():
    """Explicit stage ordered opaque shapes, with no operational approval use."""
    earlier = through_g()
    original = {role: records.record_ref(value) for role, value in earlier.items()}
    earlier["GenerationBoundary"] = fixture("GenerationBoundary", earlier)
    earlier["SeedPayload"] = fixture("SeedPayload", earlier, dependencies=original,
        inventory_refs={key: artifact(key, private=True) for key in ("K", "E", "L")},
        positions=[{"position": i, "value_hex": f"{i:016x}"} for i in range(1, 1413)])
    earlier["S"] = fixture("S", earlier, dependencies=original)
    for role in ("W", "U", "C", "D", "F", "T", "AuthorityEvent", "PrefixSnapshot",
                 "PrefixAndKVerification", "PartialGenerationSupplement",
                 "CompletedMembershipSupplement", "LeadContinuation", "J"):
        overrides = {}
        if role == "AuthorityEvent":
            overrides["prior_tip"] = "genesis"
        if role == "F":
            overrides["dependencies"] = {name: records.record_ref(earlier[name]) for name in
                ("P", "I", "Q", "O", "V", "A", "R", "B", "G", "S", "W", "U", "C", "D")}
        if role == "PrefixAndKVerification":
            overrides.update(all_new_values_in_original_K=True, original_bindings_valid=True)
        if role == "PartialGenerationSupplement":
            overrides["membership_receipt"] = records.record_ref(earlier["PrefixAndKVerification"])
        if role == "J":
            overrides.update(immutable_original_F=records.record_ref(earlier["F"]), withdrawn_eligibility=False)
        earlier[role] = fixture(role, earlier, **overrides)
    assert set(earlier) == set(SCHEMA_ROLES) == set(records.catalogue()["records"])
    return earlier


@pytest.mark.parametrize("role", SCHEMA_ROLES)
def test_every_frozen_schema_roundtrips_exact_independent_bytes_and_rejects_unknown_fields(tmp_path, role):
    all_records = independent_schema_records()
    record = all_records[role]
    raw = reference_encode(record) + b"\n"
    path = tmp_path / (role + ".json")
    path.write_bytes(raw)
    resolver = {value["digest"]: value for value in all_records.values()}
    assert records.read_record(path, role=role, resolver=resolver) == record
    assert records.record_ref(record)["sha256_raw"] == hashlib.sha256(raw).hexdigest()
    body = copy.deepcopy(record["body"])
    body["unexpected_qualification_field"] = "reject"
    with pytest.raises(ValueError):
        records.make_record(role, body)
    wrong_version = copy.deepcopy(record)
    wrong_version["version"] = True
    with pytest.raises(ValueError):
        records.validate_record(wrong_version)
    if role not in ("P", "I") and record["body"]["dependencies"]:
        bad = copy.deepcopy(record["body"])
        first = next(iter(bad["dependencies"]))
        bad["dependencies"][first] = artifact("record-artifact-interchange")
        with pytest.raises(ValueError):
            records.make_record(role, bad)
    # Exercise every declared typed artifact/reference field in each schema.
    for field, desc in records.catalogue()["records"][role]["required_body_fields"].items():
        replacement = None
        if "ArtifactRef" in desc:
            replacement = records.record_ref(all_records["P"])
        elif desc == "RecordRef" or desc.startswith("RecordRef when"):
            replacement = artifact("wrong-dedicated-reference")
        elif desc == "Actor":
            replacement = artifact("wrong-actor")
        elif desc in ("sha256", "sha256 c"):
            replacement = "A" * 64
        elif desc == "AuthorityEvent":
            replacement = records.record_ref(all_records["P"])
        if replacement is not None:
            bad = copy.deepcopy(record["body"])
            bad[field] = replacement
            with pytest.raises(ValueError):
                records.make_record(role, bad)
        if "PRIVATE ArtifactRef" in desc and "list" not in desc:
            bad = copy.deepcopy(record["body"])
            bad[field] = {**bad[field], "visibility": "PUBLIC"}
            with pytest.raises(ValueError):
                records.make_record(role, bad)
