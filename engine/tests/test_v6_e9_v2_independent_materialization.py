"""Independent complete materialization bytes and sanitized forward publication."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest

from engine.tests._e9_v2_synthetic_records import artifact, fixture, through_g
from tools.research.v6.e9.v2.commitment import (
    PrivateValues,
    validate_publication_template,
    verify_materialization,
)
from tools.research.v6.e9.v2.records import make_record, record_ref

ROOT = Path(__file__).resolve().parents[2]


def encoded(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"),
        allow_nan=False).encode() + b"\n"


def hashed(raw):
    return hashlib.sha256(raw).hexdigest()


def independent_materialization():
    pins = json.loads((ROOT / "tools/research/v6/e9/protocol_freeze_v2_proposed_02.json").read_bytes())["body"]["inherited_scientific_source_pins"]
    files = {}
    for package in pins["historical_packages"]:
        for name in ("agent.py", "agent.yaml"):
            files[package + "/" + name] = (ROOT / "tools/research/v6/e8/fixtures/agents" / package / name).read_bytes()
    for row, package in pins["physical_packages"].items():
        if package not in pins["prospective_packages"]:
            continue
        if row == "A":
            config = "Variant()"
        elif row in ("MEDIUM", "SPARSE"):
            config = f'Variant(kind="fixed", mode=Mode.{row})'
        else:
            schedule = next(item for item in pins["schedules"] if item["id"] == row)
            edges = repr(tuple(schedule["edges"]))
            config = f'Variant(kind="schedule", schedule=Schedule(Mode.{schedule["initial"]}, {edges}, "{schedule["clock"]}"))'
        manifest = f'name: {package}\nkind: python\napi_version: 2\nentrypoint: "agent.py:create_agent"\nversion: "1.0.0"\n'
        source = ('from tools.research.v6.e9.policy import Agent, Variant\n'
            'from tools.research.v6.e9.selectors import Mode, Schedule\n\n'
            f'def create_agent():\n    return Agent({config})\n')
        for name, text in (("agent.py", source), ("agent.yaml", manifest)):
            files[package + "/" + name] = text.replace("\n", "\r\n").encode()
    packages = {name.split("/", 1)[0] for name in files}
    # Explicit synthetic defaults are declared as exact independent input bytes.
    # Operational effective-default adoption is a later B gate.
    defaults = {name: encoded({"package": name, "scope": "synthetic-default-pin-only"}) for name in packages}
    t8, aliases = encoded(pins["effective_t8"]), encoded(pins["logical_aliases"])
    return {"files": files, "defaults": defaults, "frozen_pins": pins, "effective_T8": t8, "aliases": aliases,
        "expected_defaults": {name: hashed(raw) for name, raw in defaults.items()},
        "expected_T8_digest": hashed(t8), "expected_aliases_digest": hashed(aliases)}


def test_complete41_packages82_files_defaults_t8_aliases_independent_reference():
    inputs = independent_materialization()
    result = verify_materialization(**inputs)
    assert {key: result[key] for key in ("decision", "packages", "files", "defaults")} == {
        "decision": "PASS", "packages": 41, "files": 82, "defaults": 41}
    raw_file_map = {name: hashed(raw) for name, raw in inputs["files"].items()}
    assert result["materialized_manifest_digest"] == hashed(encoded(raw_file_map)[:-1])
    assert result["defaults_digest"] == hashed(encoded(inputs["expected_defaults"])[:-1])
    # Historical LF normalization is inherited; new prospective pins are raw.
    historical = next(iter(inputs["frozen_pins"]["historical_packages"])) + "/agent.py"
    inputs["files"][historical] = inputs["files"][historical].replace(b"\r\n", b"\n")
    assert verify_materialization(**inputs)["decision"] == "PASS"


@pytest.mark.parametrize("fault", ["missing_file", "extra_file", "historical_drift", "prospective_lf",
    "missing_default", "default_drift", "default_manifest_drift", "t8_raw_drift", "t8_semantic_drift",
    "alias_raw_drift", "alias_semantic_drift"])
def test_full_materialization_any_incomplete_or_changed_bound_bytes_fails(fault):
    inputs = independent_materialization()
    historical = next(iter(inputs["frozen_pins"]["historical_packages"])) + "/agent.py"
    if fault == "missing_file":
        del inputs["files"][historical]
    elif fault == "extra_file":
        inputs["files"]["foreign/agent.py"] = b"synthetic"
    elif fault == "historical_drift":
        inputs["files"][historical] += b"# drift\n"
    elif fault == "prospective_lf":
        inputs["files"]["e9_a/agent.py"] = inputs["files"]["e9_a/agent.py"].replace(b"\r\n", b"\n")
    elif fault == "missing_default":
        del inputs["defaults"][next(iter(inputs["defaults"]))]
    elif fault == "default_drift":
        inputs["defaults"][next(iter(inputs["defaults"]))] += b"\n"
    elif fault == "default_manifest_drift":
        inputs["expected_defaults"][next(iter(inputs["expected_defaults"]))] = "f" * 64
    else:
        field, digest = ("effective_T8", "expected_T8_digest") if fault.startswith("t8") else ("aliases", "expected_aliases_digest")
        inputs[field] = encoded({"synthetic_wrong_frozen_semantics": True}) if "semantic" in fault else inputs[field] + b"\n"
        if "semantic" in fault:
            inputs[digest] = hashed(inputs[field])
    with pytest.raises(ValueError):
        verify_materialization(**inputs)


# Independent full-width private values for the sanitization comparison.
PRIVATE = PrivateValues(frozenset({"9f3c5a7e1b2d4c60", "0123456789abcdef"}), (bytes(range(100, 132)),),
                        ("D:/independent-private-root/authority",))


def independent_publication(*, private_evidence=False):
    earlier = through_g()
    boundary = fixture("GenerationBoundary", earlier)
    earlier["S"] = fixture("S", earlier, generation_boundary=record_ref(boundary))
    earlier["W"] = fixture("W", earlier, commitment="c" * 64)
    earlier["U"] = fixture("U", earlier, commitment="c" * 64)
    public = fixture("C", earlier, commitment="c" * 64,
        evidence=[artifact("independent-publication-proof", private=private_evidence)])
    proposed = copy.deepcopy(public["body"])
    del proposed["dependencies"]["U"]
    template = {"body": proposed, "digest": hashed(encoded(proposed)[:-1]),
        "U_insertion_slot": "body.dependencies.U"}
    earlier.pop("U")
    authorization = fixture("U", earlier, commitment="c" * 64, active_authority_tip="a" * 64,
        approved_public_record_body=template)
    earlier["U"] = authorization
    public = fixture("C", earlier, commitment="c" * 64,
        evidence=[artifact("independent-publication-proof", private=private_evidence)])
    return public, authorization, earlier["W"]


def test_exact_sanitized_public_body_primitive_c_and_forward_u_slot_independent_template():
    public, authorization, verification = independent_publication()
    assert "U" not in authorization["body"]["approved_public_record_body"]["body"]["dependencies"]
    assert "C" not in authorization["body"]["dependencies"]
    assert public["body"]["dependencies"]["U"] == record_ref(authorization)
    validate_publication_template(public, authorization, verification, expected_tip="a" * 64, private=PRIVATE)


@pytest.mark.parametrize("fault", ["stale_tip", "mismatch_c", "changed_body", "missing_slot", "wrong_slot",
    "wrong_template_digest", "future_u_in_template", "private_evidence", "private_marker", "wrong_w"])
def test_publication_rejects_stale_cyclic_changed_or_unsanitized_templates(fault):
    public, authorization, verification = independent_publication(private_evidence=fault == "private_evidence")
    expected_tip = "b" * 64 if fault == "stale_tip" else "a" * 64
    body = copy.deepcopy(authorization["body"])
    template = body["approved_public_record_body"]
    if fault == "mismatch_c":
        body["commitment"] = "b" * 64
    elif fault == "changed_body":
        template["body"]["decision"] = "CHANGED"
        template["digest"] = hashed(encoded(template["body"])[:-1])
    elif fault == "missing_slot":
        del template["U_insertion_slot"]
    elif fault == "wrong_slot":
        template["U_insertion_slot"] = "body.dependencies.C"
    elif fault == "wrong_template_digest":
        template["digest"] = "f" * 64
    elif fault == "future_u_in_template":
        template["body"]["dependencies"]["U"] = record_ref(authorization)
        template["digest"] = hashed(encoded(template["body"])[:-1])
    elif fault == "private_marker":
        # Exact approved bytes still must satisfy the public exclusion policy.
        template["body"]["evidence"][0]["evidence_id"] = "value_hex"
        template["digest"] = hashed(encoded(template["body"])[:-1])
    elif fault == "wrong_w":
        verification = make_record("W", {**verification["body"], "commitment": "b" * 64})
    if fault not in ("stale_tip", "private_evidence", "wrong_w"):
        authorization = make_record("U", body)
        pbody = copy.deepcopy(public["body"])
        pbody["dependencies"]["U"] = record_ref(authorization)
        if fault == "private_marker":
            pbody["evidence"] = template["body"]["evidence"]
        public = make_record("C", pbody)
    with pytest.raises(ValueError):
        validate_publication_template(public, authorization, verification, expected_tip=expected_tip,
                                      private=PRIVATE)


def approved(decision):
    """A U-approved template and C whose decision text the lead approved verbatim."""
    public, authorization, verification = independent_publication()
    body = copy.deepcopy(authorization["body"])
    template = body["approved_public_record_body"]
    template["body"]["decision"] = decision
    template["digest"] = hashed(encoded(template["body"])[:-1])
    authorization = make_record("U", body)
    pbody = copy.deepcopy(public["body"])
    pbody["decision"] = decision
    pbody["dependencies"]["U"] = record_ref(authorization)
    return make_record("C", pbody), authorization, verification


@pytest.mark.parametrize("leak", ["9f3c5a7e1b2d4c60", "9F3C5A7E1B2D4C60", str(int("9f3c5a7e1b2d4c60", 16)),
    str(int("0123456789abcdef", 16)), bytes(range(100, 132)).hex(), bytes(range(100, 132)).hex().upper(),
    "ZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXp7fH1+f4CBgoM", "ZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXp7fH1-f4CBgoM",
    "D:/INDEPENDENT-PRIVATE-ROOT/AUTHORITY/log"])
def test_sanitization_compares_against_the_actual_private_values_not_a_pattern(leak):
    with pytest.raises(ValueError, match="actual private"):
        validate_publication_template(*approved("AUTHORIZED; " + leak), expected_tip="a" * 64, private=PRIVATE)
    # Look-alike values that are not this study's private bytes remain publishable.
    validate_publication_template(*approved("AUTHORIZED; 9f3c5a7e1b2d4c61 0123456789abcdee"),
                                  expected_tip="a" * 64, private=PRIVATE)


@pytest.mark.parametrize("role,field,value", [
    ("J", "stage", "UNKNOWN_STAGE"), ("J", "stage", 1),
    ("AuthorityEvent", "event_kind", "IMPLICIT_PASS"),
    ("AuthorityEvent", "event_kind", False),
    ("LeadContinuation", "disposition", "AUTO_RESTART"),
    ("F", "historical_integrity", "COMPLETE_HISTORY"),
    ("F", "requirement_C_eligible", "true"),
    ("PrefixAndKVerification", "all_new_values_in_original_K", 1),
])
def test_clearly_finite_frozen_schema_enums_and_booleans_reject_wrong_values(role, field, value):
    from engine.tests.test_v6_e9_v2_independent_serialization import independent_schema_records
    record = independent_schema_records()[role]
    body = copy.deepcopy(record["body"])
    body[field] = value
    with pytest.raises(ValueError):
        make_record(role, body)


@pytest.mark.parametrize("fault", [None, "implementation", "qualification", "instrument", "protocol"])
def test_actual_source_checker_rehashes_implementation_qualification_and_preserved_review(fault):
    from tools.research.v6.e9.v2.instrument import source_checker
    p = "539a60806eab03f1c3534406d96616cec59fc8868fa7df1b567953aa08239ae0"
    source_path = "tools/research/v6/e9/v2/records.py"
    test_path = "engine/tests/test_v6_e9_v2_independent_materialization.py"
    sources = {source_path: hashed((ROOT / source_path).read_bytes())}
    tests = {test_path: hashed((ROOT / test_path).read_bytes())}
    instrument = hashed(encoded({"protocol_digest": p, "sources": sources})[:-1])
    if fault == "implementation":
        sources[source_path] = "f" * 64
    elif fault == "qualification":
        tests[test_path] = "f" * 64
    elif fault == "instrument":
        instrument = "f" * 64
    elif fault == "protocol":
        p = "f" * 64
    checker = source_checker(protocol_digest=p, instrument_digest=instrument,
        implementation_sources=sources, qualification_sources=tests)
    if fault:
        with pytest.raises(ValueError):
            checker()
    else:
        checker()


@pytest.mark.parametrize("fault", ["changed_adopted_body", "wrong_proposed_binding", "unknown_attestation_envelope", "noncanonical_attestation"])
def test_adoption_authority_reader_requires_exact_reviewed_body_and_attestation_bytes(tmp_path, monkeypatch, fault):
    from tools.research.v6.e9.v2 import records
    adopted = json.loads(records.ADOPTED.read_bytes())
    attestation = json.loads(records.ATTESTATION.read_bytes())
    if fault == "changed_adopted_body":
        changed = {**adopted["body"], "adoption_rule": adopted["body"]["adoption_rule"] + " synthetic changed rule"}
        changed_digest = hashed(encoded(changed)[:-1])
        adopted = {**adopted, "body": changed, "digest": changed_digest,
            "identity": "v6-e9-prereg-v2-" + changed_digest[:12]}
    adopted_path, attestation_path = tmp_path / "adopted.json", tmp_path / "attestation.json"
    adopted_path.write_bytes(encoded(adopted))
    attestation["body"]["adopted_record"]["sha256_raw"] = hashed(adopted_path.read_bytes())
    if fault == "wrong_proposed_binding":
        attestation["body"]["reviewed_proposed_envelope_raw_sha256"] = "f" * 64
    attestation["digest"] = hashed(encoded(attestation["body"])[:-1])
    attestation["identity"] = "v6-e9-adoption-v2-" + attestation["digest"][:12]
    if fault == "unknown_attestation_envelope":
        attestation["unexpected_authority"] = True
    raw = encoded(attestation)
    attestation_path.write_bytes(raw + b"\n" if fault == "noncanonical_attestation" else raw)
    monkeypatch.setattr(records, "ADOPTED", adopted_path)
    monkeypatch.setattr(records, "ATTESTATION", attestation_path)
    with pytest.raises(ValueError, match="exact original adoption bytes"):
        records.load_protocol()
    # Behind the raw pins, each fault still fails at its own specific check.
    monkeypatch.setattr(records, "ADOPTED_RAW", hashed(adopted_path.read_bytes()))
    monkeypatch.setattr(records, "ATTESTATION_RAW", hashed(attestation_path.read_bytes()))
    expected = {"changed_adopted_body": "unreviewed protocol",
                "wrong_proposed_binding": "exact reviewed proposal and canonical adoption attestation",
                "unknown_attestation_envelope": "missing, unknown or mistyped fields",
                "noncanonical_attestation": "exact reviewed proposal and canonical adoption attestation"}[fault]
    with pytest.raises(ValueError, match=expected):
        records.load_protocol()
