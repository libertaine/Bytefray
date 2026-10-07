"""Independent Gate-8 publication qualification: N1-01 to N1-10 and D3 of v2_gate8_scope_01.json.

Written from the write-once Gate-8 scope record (fields, representation_set,
pre_U_template_check, D1-D3) and its lead confirmation (the D3 clarification), not from the
implementer's Gate-8 tests or the M3 code path. The field classification is read from the
scope record itself; the representation set is re-implemented independently as a reference
matcher (test_v6_e9_v2_independent_gate8_producer.exposed) and every expected refusal or
PASS is predicted by it before the instrument is asked.

D4 provenance: the studies here are the REAL-labelled synthetic qualification fixtures of the
independent producer module (study "synthetic-e9-v2-only", synthetic actors, hash-derived
uint64 values, a literal 32-byte test constant in place of a salt), built by hand inside pytest
temporary roots. REAL appears only as the frozen-shape entropy declaration; no fixture
consumes entropy, invokes salt_creation or writes salt.bin, and none is operational evidence.

No REAL entropy was consumed. REAL was represented only as an input declaration inside
synthetic qualification fixtures.
"""

from __future__ import annotations

import base64
import dataclasses
import inspect
import json
import os
import re
from pathlib import Path

import pytest

from engine.tests import test_v6_e9_v2_independent_gate8_producer as producer
from engine.tests._e9_v2_synthetic_records import actor
from tools.research.v6.e9.v2 import commitment
from tools.research.v6.e9.v2 import private_verification as pv
from tools.research.v6.e9.v2.commitment import (
    PrivateValues,
    check_public_content,
    public_text_surface,
    study_private_values,
)
from tools.research.v6.e9.v2.inventory import revealed_lists
from tools.research.v6.e9.v2.records import IntegrityError, record_ref

SCOPE = json.loads((producer.FROZEN / "v2_gate8_scope_01.json").read_bytes())["body"]
FIELDS = ("decision", "actor_id", "authority_evidence_id", "evidence_id", "status")
MARKERS = ("value_hex", "raw_bytes_hex", "salt.bin", "runs/", "runs\\", ":\\")
STRUCTURAL = (2, 6, 8, 9, 256, 1412)  # constant-field digit runs present in every C (plan F2)
REFUSED = "actual private|private values/paths"


@pytest.fixture
def bases(tmp_path_factory):
    return producer.base_getter(tmp_path_factory)


@pytest.fixture
def study(bases, tmp_path):
    """A REAL-labelled synthetic study at the pre-U stage (S and W issued), one per test."""
    return producer.clone(bases("w-issued"), tmp_path)


def scope_classes() -> dict[str, str]:
    """C field classes exactly as the scope record lists them (fields.*)."""
    fields = SCOPE["fields"]
    classes = {name.split(" ")[0]: "text" for name in fields["protected_text_fields"]}
    for kind, entry in fields["not_scanned"].items():
        for name in entry["fields"]:
            if name == "every object key":
                continue  # keys are constant; the leaves below are classified one by one
            if name == "every ArtifactRef visibility":
                classes["body.actor.authority_evidence.visibility"] = kind
                classes["body.evidence[*].visibility"] = kind
                continue
            classes[name.split(" ")[0]] = kind  # "identity prefix"/"identity suffix"
    return classes


def scope_class(classes: dict[str, str], path: str) -> str | None:
    for name, kind in classes.items():
        if path == name or path.startswith((name + ".", name + "[")):
            return kind
    return None


def leaf_items(value, path: str = ""):
    if isinstance(value, dict):
        for key, item in value.items():
            yield from leaf_items(item, f"{path}.{key}" if path else key)
    elif isinstance(value, list):
        for item in value:
            yield from leaf_items(item, path + "[*]")
    else:
        yield path, value


def object_keys(value) -> list[str]:
    if isinstance(value, dict):
        return [text for key, item in value.items() for text in (key, *object_keys(item))]
    if isinstance(value, list):
        return [text for item in value for text in object_keys(item)]
    return []


def structural_values(record: dict) -> set[str]:
    """Every decimal digit run and 16-hex window of C outside its protected text fields."""
    classes = scope_classes()
    texts = object_keys(record) + [str(value) for path, value in leaf_items(record)
                                   if scope_class(classes, path) != "text"]
    values: set[str] = set()
    for text in texts:
        values.update(f"{int(run):016x}" for run in re.findall(r"[0-9]+", text)
                      if int(run) < 2 ** 64)
        lowered = text.lower()
        values.update(lowered[i:i + 16] for i in range(len(lowered) - 15)
                      if re.fullmatch(r"[0-9a-f]{16}", lowered[i:i + 16]))
    return values


def place(body: dict, field: str, text: str) -> tuple[dict, str | None]:
    """The template body (and envelope status) with `text` in one protected text field."""
    if field == "decision":
        return {**body, "decision": "PUBLISHED " + text}, None
    if field == "actor_id":
        return {**body, "actor": {**body["actor"], "actor_id": "synthetic-publisher-" + text}}, None
    if field == "authority_evidence_id":
        evidence = {**body["actor"]["authority_evidence"],
                    "evidence_id": "synthetic/publisher-" + text}
        return {**body, "actor": {**body["actor"], "authority_evidence": evidence}}, None
    if field == "evidence_id":
        notice = {**producer.PUBLIC_NOTICE, "evidence_id": "synthetic/notice-" + text}
        return {**body, "evidence": [notice]}, None
    assert field == "status"
    return body, "synthetic status " + text


def representations(study) -> dict[str, tuple[str, PrivateValues]]:
    """Every scope representation, each with a PrivateValues holding only what it encodes."""
    generated, candidate = study.accepted[0], study.entries[0]["raw_bytes_hex"]
    small, revealed = f"{42:016x}", min(revealed_lists()["E6"])
    salt = study.salt_raw
    authority_root = str(study.log.root.resolve())
    producer_root = str(study.producer_root.resolve())

    def value(item: str) -> PrivateValues:
        return PrivateValues(frozenset({item}), (), ())

    def root(item: str) -> PrivateValues:
        return PrivateValues(frozenset(), (), (item,))
    salt_only = PrivateValues(frozenset(), (salt,), ())
    return {
        "generated_hex": (generated, value(generated)),
        "generated_hex_upper": (generated.upper(), value(generated)),
        "generated_decimal": (str(int(generated, 16)), value(generated)),
        "raw_candidate_hex": (candidate, value(candidate)),
        "raw_candidate_decimal": (str(int(candidate, 16)), value(candidate)),
        "K_hex": (small, value(small)),
        "K_hex_upper": (small.upper(), value(small)),
        "K_decimal": ("42", value(small)),
        "K_revealed_decimal": (str(int(revealed, 16)), value(revealed)),
        "salt_hex": (salt.hex(), salt_only),
        "salt_hex_upper": (salt.hex().upper(), salt_only),
        "salt_base64": (base64.b64encode(salt).decode().rstrip("="), salt_only),
        "salt_base64_urlsafe": (base64.urlsafe_b64encode(salt).decode().rstrip("="), salt_only),
        "authority_root_slash": (authority_root.replace("\\", "/"), root(authority_root)),
        "authority_root_backslash": (authority_root.replace("/", "\\"), root(authority_root)),
        "authority_root_upper": (authority_root.upper(), root(authority_root)),
        "producer_root_slash": (producer_root.replace("\\", "/"), root(producer_root)),
        "producer_root_backslash": (producer_root.replace("/", "\\"), root(producer_root)),
    }


def reference(study) -> dict:
    """The complete scope set: every generated value, every K member in hex and decimal."""
    return producer.study_forms(study, every_decimal=True)


def refused_pre_u(study, body: dict, **kwargs) -> dict | None:
    """D3: the check refuses with FAIL and a value-free PRIVATE receipt, or by raising.
    Either way it is read-only: no authority event and no tip change."""
    tip, events = study.log.tip, len(producer.event_files(study))
    try:
        result = producer.pre_u(study, body, **kwargs)
    except IntegrityError:
        result = None
    else:
        assert result["decision"] == "FAIL"
        assert result["receipt"]["visibility"] == "PRIVATE"
        producer.assert_private_free(study, study.log.read_artifact(result["receipt"]))
    assert study.log.tip == tip and len(producer.event_files(study)) == events
    return result


def assert_not_issued(study, tip: str) -> None:
    assert study.log.tip == tip and "U" not in study.log.bindings
    assert not producer.u_active(study)


# ---- N1-01, N1-02, N1-03: no structural content can make C unpublishable ---------------------

def test_n1_01_realistic_K_passes_the_pre_u_check_and_publication_with_U_consumed_once(
        study, tmp_path):
    lists = revealed_lists()
    expected_K = {f"{n:016x}" for n in producer.SMALL_K} | lists["E6"] | lists["E8"]
    assert set(study.K) == expected_K
    private = study_private_values(study.log)
    generated = set(study.accepted) | {entry["raw_bytes_hex"] for entry in study.entries}
    assert private.uint64_hex == frozenset(generated | expected_K)
    assert private.salts == (study.salt_raw,)
    assert set(private.paths) == {str(study.log.root.resolve()),
                                  os.path.normcase(str(study.producer_root.resolve()))}
    body = producer.template_body(study)
    result = producer.pre_u(study, body)
    assert result["decision"] == "PASS" and result["template_digest"] == producer.body_digest(body)
    assert result["receipt"]["evidence_id"].startswith("GATE8-PRE-U-TEMPLATE-CHECK")
    receipt = study.log.read_artifact(result["receipt"])
    texts = producer.json_texts(json.loads(receipt))
    assert result["template_digest"] in texts and "PASS" in texts
    producer.assert_private_free(study, receipt)
    U = producer.make_U(study, body, [result["receipt"]])
    tip = study.log.tip
    issued = producer.issue_U(study, U)
    assert {"U", "event", "attestation"} <= set(issued)
    event = producer.last_event(study)["body"]
    assert (event["event_kind"], event["actor"], event["prior_tip"]) == ("ISSUE", producer.LEAD,
                                                                         tip)
    assert event["binding_tuple"]["U"] == record_ref(U) == study.log.bindings["U"]
    assert result["receipt"] in event["evidence"] and len(event["evidence"]) == 2
    attestation = next(ref for ref in event["evidence"] if ref != result["receipt"])
    assert attestation["visibility"] == "PRIVATE"
    producer.assert_private_free(study, study.log.read_artifact(attestation))
    assert pv.verify_operational_u(study.log)["decision"] == "ADMISSIBLE"
    C = producer.public_C(body, U)
    # N1 reproduction: the seal-04 whole-record scan refuses this exact C on structure alone.
    assert private.exposed_in(C)
    for k in STRUCTURAL:
        assert PrivateValues(frozenset({f"{k:016x}"}), (), ()).exposed_in(C), k
    assert not private.exposed_in_public_record(C)
    assert producer.publish(study, C, tmp_path / "C.json") == record_ref(C)
    assert (tmp_path / "C.json").read_bytes() == producer.encode(C)
    assert producer.u_consumed(study)
    with pytest.raises(IntegrityError, match="already consumed"):
        producer.publish(study, C, tmp_path / "second-C.json")
    assert not (tmp_path / "second-C.json").exists()


def test_n1_02_adversarial_K_and_salt_built_from_C_structure_pass(study):
    body = producer.template_body(study)
    C = producer.public_C(body, producer.make_U(study, body, []), "synthetic descriptive status")
    adversarial = structural_values(C)
    assert {f"{k:016x}" for k in STRUCTURAL} <= adversarial
    assert body["commitment"][:16] in adversarial and C["digest"][-16:] in adversarial
    actual = study_private_values(study.log)
    hostile = PrivateValues(actual.uint64_hex | adversarial, actual.salts, actual.paths)
    assert hostile.exposed_in(C)  # the seal-04 whole-record scan refuses
    assert not hostile.exposed_in_public_record(C)
    check_public_content(C, hostile)
    # A salt equal to a derived digest of C (c, a dependency digest, C's own digest).
    for digest in (body["commitment"], body["dependencies"]["P"]["digest"], C["digest"]):
        salted = PrivateValues(actual.uint64_hex, (bytes.fromhex(digest),), actual.paths)
        assert salted.exposed_in(C) and not salted.exposed_in_public_record(C)
        check_public_content(C, salted)


def test_n1_03_every_k_below_65536_added_to_realistic_K_passes(study):
    body = producer.template_body(study)
    C = producer.public_C(body, producer.make_U(study, body, []))
    actual = study_private_values(study.log)
    realistic = frozenset(study.K)
    flagged = [k for k in range(65536)
               if PrivateValues(realistic | {f"{k:016x}"}, actual.salts,
                                actual.paths).exposed_in_public_record(C)]
    assert flagged == []
    # Exposure is monotone in the value set, so one check over all of them at once, with
    # every actual generated value, is the same sweep through the full publication check.
    everything = PrivateValues(actual.uint64_hex | {f"{k:016x}" for k in range(65536)},
                               actual.salts, actual.paths)
    check_public_content(C, everything)
    # Whole-run matching compares a digit run with str(int(value)), so only canonical runs
    # (no leading zero) can equal a value; "032" inside a digest never matches 32.
    runs = {int(run) for text in producer.json_texts(C) for run in re.findall(r"[0-9]+", text)
            if run == str(int(run)) and int(run) < 65536}
    assert set(STRUCTURAL) <= runs
    old = [k for k in sorted(runs) if PrivateValues(frozenset({f"{k:016x}"}), (), ()).exposed_in(C)]
    assert old == sorted(runs)  # each would have blocked publication under seal 04


def test_n1_04_generated_values_that_look_structural_pass_and_fail_only_in_text(tmp_path):
    lists = revealed_lists()
    K = sorted({f"{n:016x}" for n in (0, 1, 3, 5, 7, 42)} | lists["E6"] | lists["E8"])
    special: list[str] = []

    def accepted(built):
        P, G = built.log.bindings["P"]["digest"], built.log.bindings["G"]["digest"]
        special.extend([f"{n:016x}" for n in STRUCTURAL] + [P[:16], G[8:24]])
        return [*special, *producer.accepted_values(built, producer.N - len(special),
                                                    exclude=special)]
    s = producer.build_issued(tmp_path / "study", K=K, accepted=accepted)
    producer.issue_W(s, producer.produce(s))
    private = study_private_values(s.log)
    assert set(special) <= set(s.accepted) and set(special) <= private.uint64_hex
    assert not set(special) & set(K)
    body = producer.template_body(s)
    U0 = producer.make_U(s, body, [])
    C0 = producer.public_C(body, U0)
    assert private.exposed_in(C0)  # seal 04 would refuse: 2, 6, 8, 9, 256, 1412 and windows
    assert not private.exposed_in_public_record(C0)
    check_public_content(C0, private)
    for value in special:
        for text in (str(int(value, 16)), value, value.upper()):
            leaked = producer.public_C({**body, "decision": "PUBLISHED " + text}, U0)
            assert producer.exposed(leaked["body"]["decision"], **reference(s))
            with pytest.raises(IntegrityError, match="actual private"):
                check_public_content(leaked, private)
    refused_pre_u(s, {**body, "decision": "PUBLISHED 1412"})
    refused_pre_u(s, place(body, "evidence_id", special[-1].upper())[0])
    passed = producer.pre_u(s, body)
    assert passed["decision"] == "PASS"
    U = producer.make_U(s, body, [passed["receipt"]])
    producer.issue_U(s, U)
    C = producer.public_C(body, U)
    assert producer.publish(s, C, tmp_path / "C.json") == record_ref(C)
    assert producer.u_consumed(s)


# ---- N1-05, N1-06, N1-08: genuine disclosure in protected text is still refused ---------------

def test_n1_05_every_protected_field_by_every_representation_is_refused(study):
    body = producer.template_body(study)
    U = producer.make_U(study, body, [])
    actual, forms = study_private_values(study.log), reference(study)
    clean = producer.public_C(body, U)
    check_public_content(clean, actual)
    reps = representations(study)
    assert len({text for text, _ in reps.values()}) == len(reps)
    for name, (text, isolated) in reps.items():
        assert producer.exposed(text, **forms), name  # the reference predicts the refusal
        assert not isolated.exposed_in_public_record(clean), name
        for field in FIELDS:
            leaked_body, status = place(body, field, text)
            C = producer.public_C(leaked_body, U, status)
            assert isolated.exposed_in_public_record(C), (name, field)  # its own rule matches
            assert actual.exposed_in_public_record(C), (name, field)
            with pytest.raises(IntegrityError, match=REFUSED):
                check_public_content(C, actual)
    # The authority-level pre-U check, one representation per template text field. Envelope
    # status is not part of the U-approved template body; publication covers it below.
    tip = study.log.tip
    for field, name in (("decision", "generated_decimal"), ("actor_id", "salt_base64_urlsafe"),
                        ("authority_evidence_id", "K_hex_upper"),
                        ("evidence_id", "producer_root_slash")):
        leaked_body, _ = place(body, field, reps[name][0])
        study.log.actors[leaked_body["actor"]["actor_id"]] = "publisher"
        failed = refused_pre_u(study, leaked_body)
        if field == "decision":
            evidence = [] if failed is None else [failed["receipt"]]
            with pytest.raises(IntegrityError):
                producer.issue_U(study, producer.make_U(study, leaked_body, evidence))
    assert_not_issued(study, tip)


PUBLICATION_LEAKS = {"decision": "generated_hex_upper", "actor_id": "K_revealed_decimal",
                     "authority_evidence_id": "salt_hex", "evidence_id": "raw_candidate_hex",
                     "status": "authority_root_slash"}


@pytest.mark.parametrize("field", FIELDS)
def test_n1_05_publication_refuses_each_protected_field_without_consuming_U(field, study,
                                                                           tmp_path):
    text = representations(study)[PUBLICATION_LEAKS[field]][0]
    leaked_body, status = place(producer.template_body(study), field, text)
    publisher = leaked_body["actor"]
    study.log.actors[publisher["actor_id"]] = "publisher"
    U = producer.make_U(study, leaked_body, [])
    producer.generic_issue_U(study, U)  # bypasses D3 so that publication's own M3 is reached
    C = producer.public_C(leaked_body, U, status)
    with pytest.raises(IntegrityError, match="actual private"):
        producer.publish(study, C, tmp_path / "leaked-C.json", publisher=publisher)
    assert not (tmp_path / "leaked-C.json").exists()
    assert not producer.u_consumed(study)


def generated_lookalikes(value: str) -> list[str]:
    number = int(value, 16)
    nibble = "a" if value[0] != "a" else "b"
    return [str(number + 1), str(number - 1), str(number) + "0", str(number)[:-1],
            nibble + value[1:], value[:15], value[1:]]


def test_n1_06_off_by_one_look_alikes_pass(study):
    forms = reference(study)

    def clean(text: str) -> bool:
        return not producer.exposed(text, **forms)
    value = next(item for item in study.accepted if all(map(clean, generated_lookalikes(item))))
    revealed = int(min(revealed_lists()["E6"]), 16)
    salt_hex = study.salt_raw.hex()
    salt_b64 = base64.b64encode(study.salt_raw).decode().rstrip("=")
    lookalikes = [*generated_lookalikes(value), "4", "41", "43", "255", "257", "1411", "1413",
                  "10", "11", str(revealed + 1), str(revealed - 1),
                  ("e" if salt_hex[0] != "e" else "d") + salt_hex[1:], salt_hex[:63],
                  salt_b64[:-1], salt_b64.swapcase()]
    body = producer.template_body(study)
    U = producer.make_U(study, body, [])
    actual = study_private_values(study.log)
    for text in lookalikes:
        assert clean(text), text  # the reference predicts PASS
        C = producer.public_C({**body, "decision": "PUBLISHED " + text}, U)
        assert not actual.exposed_in_public_record(C), text
        check_public_content(C, actual)
    # Root look-alikes in isolation (temporary paths carry incidental digit runs).
    for root in (str(study.log.root.resolve()), str(study.producer_root.resolve())):
        only = PrivateValues(frozenset(), (), (root,))
        for text in (root[:-1].replace("\\", "/"), str(Path(root).parent).replace("\\", "/")):
            assert not producer.exposed(text, hexes=(), decimals=(), salts=(), roots=(root,))
            C = producer.public_C({**body, "decision": "PUBLISHED " + text}, U)
            assert not only.exposed_in_public_record(C), text
    combined = {**body, "decision": "PUBLISHED " + " ".join(lookalikes)}
    assert producer.pre_u(study, combined)["decision"] == "PASS"


def test_n1_08_free_text_K_collision_fails_before_U_and_rewording_passes(study):
    assert f"{2:016x}" in study.K
    colliding = producer.template_body(study, decision="2 artifacts recorded")
    assert producer.exposed(colliding["decision"], **reference(study))
    tip = study.log.tip
    refused_pre_u(study, colliding)
    reworded = producer.template_body(study, decision="two artifacts recorded")
    assert not producer.exposed(reworded["decision"], **reference(study))
    assert producer.pre_u(study, reworded)["decision"] == "PASS"
    assert_not_issued(study, tip)


# ---- N1-07, D3: the pre-U check gates the dedicated issuance path ----------------------------

def test_n1_07_refused_template_is_corrected_and_issuance_needs_its_one_pass_receipt(study,
                                                                                    tmp_path):
    body = producer.template_body(study)
    leaky = {**body, "decision": "PUBLISHED " + str(int(study.accepted[0], 16))}
    failed = refused_pre_u(study, leaky)
    passed = producer.pre_u(study, body)
    second = producer.pre_u(study, body, checker=producer.SECOND_CHECKER)
    assert passed["decision"] == second["decision"] == "PASS"
    assert passed["template_digest"] == second["template_digest"] == producer.body_digest(body)
    tip = study.log.tip
    refusals = {
        "refused template, no receipt": producer.make_U(study, leaky, []),
        "corrected template, no receipt": producer.make_U(study, body, []),
        "PASS receipt for another template": producer.make_U(study, leaky, [passed["receipt"]]),
    }
    if failed is not None:
        refusals["FAIL receipt"] = producer.make_U(study, leaky, [failed["receipt"]])
    if second["receipt"] != passed["receipt"]:
        refusals["two PASS receipts"] = producer.make_U(study, body, [passed["receipt"],
                                                                      second["receipt"]])
    for name, U in refusals.items():
        with pytest.raises(IntegrityError):
            producer.issue_U(study, U)
        assert study.log.tip == tip, name
        assert_not_issued(study, tip)
    U = producer.make_U(study, body, [passed["receipt"]])
    with pytest.raises(IntegrityError):  # only the research lead issues U
        producer.issue_U(study, U, lead=producer.PUBLISHER)
    with pytest.raises(IntegrityError):  # stale active tip
        producer.issue_U(study, U, expected_tip=study.consume_tip)
    assert_not_issued(study, tip)
    producer.issue_U(study, U)
    assert study.log.bindings["U"] == record_ref(U) and producer.u_active(study)
    assert pv.verify_operational_u(study.log)["decision"] == "ADMISSIBLE"
    C = producer.public_C(body, U)
    assert producer.publish(study, C, tmp_path / "C.json") == record_ref(C)
    assert producer.u_consumed(study)
    with pytest.raises(IntegrityError, match="already consumed"):
        producer.publish(study, C, tmp_path / "second-C.json")


def test_d3_generic_append_U_is_not_operationally_admissible(bases, study, tmp_path):
    body = producer.template_body(study)
    passed = producer.pre_u(study, body)
    U = producer.make_U(study, body, [passed["receipt"]])
    producer.generic_issue_U(study, U)  # even with a genuine PASS receipt bound in U
    with pytest.raises(IntegrityError):
        pv.verify_operational_u(study.log)
    # Scope residual: publish_commitment keeps its sealed semantics and does not demand the
    # receipt, so the Gate-9 procedure must call verify_operational_u before publication.
    C = producer.public_C(body, U)
    assert producer.publish(study, C, tmp_path / "C.json") == record_ref(C)
    other = producer.clone(bases("w-issued"), tmp_path / "without-receipt")
    producer.generic_issue_U(other, producer.make_U(other, body, []))
    with pytest.raises(IntegrityError):
        pv.verify_operational_u(other.log)


def test_d3_pre_u_check_runs_only_between_W_and_U_for_the_exact_template(bases, study,
                                                                         tmp_path):
    body = producer.template_body(study)
    early = producer.clone(bases("issued"), tmp_path / "before-W")
    refused_pre_u(early, body)  # W not yet issued
    for checker in (actor("independent_verifier", "synthetic-unregistered-checker"),
                    producer.INTEGRITY, producer.PUBLISHER, producer.LEAD):
        refused_pre_u(study, body, checker=checker)
    W_ref = study.log.bindings["W"]
    faults = {
        "missing W": {**body, "dependencies": {role: ref for role, ref
                                               in body["dependencies"].items() if role != "W"}},
        "U slot filled": {**body, "dependencies": {**body["dependencies"], "U": W_ref}},
        "other commitment": {**body, "commitment": "0" * 64},
        "other N": {**body, "N": 1411},
        "other study": {**body, "study_id": "synthetic-other-study"},
        "unregistered publisher": {**body, "actor": actor("publisher", "synthetic-unknown-pub")},
        "non-publisher actor": {**body, "actor": producer.LEAD},
    }
    for fault in faults.values():
        refused_pre_u(study, fault)
    passed = producer.pre_u(study, body)
    assert passed["decision"] == "PASS"
    producer.issue_U(study, producer.make_U(study, body, [passed["receipt"]]))
    refused_pre_u(study, body)  # U already issued


# ---- N1-09, N1-10: classification fails closed; the marker layer is unchanged ---------------

def test_n1_09_every_C_field_is_classified_and_unclassified_fields_fail_closed(study):
    classes = scope_classes()
    second = {**producer.PUBLIC_NOTICE, "evidence_id": "synthetic/second-public-notice"}
    body = producer.template_body(study, evidence=[producer.PUBLIC_NOTICE, second])
    C = producer.public_C(body, producer.make_U(study, body, []), "synthetic descriptive status")
    items = list(leaf_items(C))
    assert [path for path, _ in items if scope_class(classes, path) is None] == []
    texts = sorted(value for path, value in items if scope_class(classes, path) == "text")
    assert len(texts) == 6 and sorted(public_text_surface(C)) == texts
    template = sorted(value for path, value in leaf_items({"body": body})
                      if scope_class(classes, path) == "text")
    assert sorted(public_text_surface({"body": body})) == template
    actual = study_private_values(study.log)
    check_public_content(C, actual)
    extra = "synthetic unclassified field"
    actor_ = C["body"]["actor"]
    variants = {
        "envelope": {**C, "note": extra},
        "body": {**C, "body": {**C["body"], "note": extra}},
        "actor": {**C, "body": {**C["body"], "actor": {**actor_, "note": extra}}},
        "authority_evidence": {**C, "body": {**C["body"], "actor": {
            **actor_, "authority_evidence": {**actor_["authority_evidence"], "note": extra}}}},
        "evidence": {**C, "body": {**C["body"], "evidence": [{**producer.PUBLIC_NOTICE,
                                                               "note": extra}]}},
    }
    for variant in variants.values():
        for check in (public_text_surface, actual.exposed_in_public_record,
                      lambda record: check_public_content(record, actual)):
            with pytest.raises(IntegrityError):
                check(variant)
    refused_pre_u(study, {**body, "note": extra})


def test_n1_10_marker_layer_is_an_unchanged_whole_record_check(study):
    body = producer.template_body(study)
    U = producer.make_U(study, body, [])
    nothing = PrivateValues(frozenset(), (), ())
    for marker in MARKERS:
        for field in ("decision", "evidence_id"):
            C = producer.public_C(place(body, field, marker)[0], U)
            assert not nothing.exposed_in_public_record(C)
            with pytest.raises(IntegrityError, match="private values/paths/diagnostics"):
                check_public_content(C, nothing)
    C = producer.public_C(body, U)
    with pytest.raises(IntegrityError, match="private values/paths/diagnostics"):
        check_public_content({"body": {**C["body"], "study_id": "synthetic/runs/x"}}, nothing)
    private = producer.public_C({**body, "evidence": [{**producer.PUBLIC_NOTICE,
                                                       "visibility": "PRIVATE"}]}, U)
    with pytest.raises(IntegrityError, match="private evidence"):
        check_public_content(private, nothing)
    refused_pre_u(study, place(body, "evidence_id", "value_hex")[0])


# ---- Signatures the scope keeps or introduces -----------------------------------------------

def test_gate8_public_signatures_are_the_scoped_ones():
    def shape(function):
        return [(p.name, p.kind) for p in inspect.signature(function).parameters.values()]
    positional, keyword = inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.KEYWORD_ONLY
    assert shape(pv.check_publication_template) == [
        ("authority", positional), ("proposed_body", positional), ("checker", keyword),
        ("expected_tip", keyword), ("operation_id", keyword)]
    assert shape(pv.issue_publication_authorization) == [
        ("authority", positional), ("U", positional), ("lead", keyword),
        ("expected_tip", keyword), ("operation_id", keyword)]
    assert shape(pv.verify_operational_u) == [("authority", positional)]
    assert shape(commitment.validate_publication_template) == [
        ("public_record", positional), ("authorization", positional),
        ("verification", positional), ("expected_tip", keyword), ("private", keyword)]
    assert shape(commitment.publish_commitment) == [
        ("authority", positional), ("public_record", positional), ("expected_tip", keyword),
        ("operation_id", keyword), ("publisher", keyword), ("destination", keyword)]
    assert shape(commitment.study_private_values) == [("authority", positional)]
    assert [item.name for item in dataclasses.fields(PrivateValues)] == [
        "uint64_hex", "salts", "paths"]
    assert PrivateValues(frozenset(), (), ()) == PrivateValues(uint64_hex=frozenset(), salts=(),
                                                               paths=())
