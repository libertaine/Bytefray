"""Gate-8 N1 typed M3 check, pre-U template check and Gate-8 U issuance (implementer tests).

SYNTHETIC QUALIFICATION FIXTURES ONLY (see test_v6_e9_v2_gate8_producer). No REAL entropy is
consumed; REAL appears only as an input declaration inside hand-built synthetic studies.
"""

from __future__ import annotations

import base64
import copy
import re

import pytest

from engine.tests._e9_v2_synthetic_records import actor, fixture, through_g
from engine.tests.test_v6_e9_v2_gate8_producer import (
    LEAD,
    POSITIONS,
    Study,
    realistic_K,
    uint64,
)
from tools.research.v6.e9.v2 import private_verification as pv
from tools.research.v6.e9.v2.commitment import (
    PrivateValues,
    public_text_surface,
    publish_commitment,
    validate_publication_template,
)
from tools.research.v6.e9.v2.inventory import revealed_lists
from tools.research.v6.e9.v2.records import (
    IntegrityError,
    canonical_bytes,
    make_record,
    record_ref,
    sha256,
)

SALT = sha256(b"synthetic publication salt")
SALT_BYTES = bytes.fromhex(SALT)
ROOT = "D:/synthetic-private-root/authority"
GENERATED = POSITIONS[:16]
E6_E8 = sorted(set().union(*revealed_lists().values()))


def private(K=None, generated=GENERATED):
    return PrivateValues(frozenset(set(generated) | set(realistic_K() if K is None else K)),
                         (SALT_BYTES,), (ROOT,))


def publication(*, decision="AUTHORIZED", evidence=None, publisher=None, status=None):
    """Fixture C, the U approving its exact template, and W (validator level; real digests)."""
    earlier = through_g()
    boundary = fixture("GenerationBoundary", earlier)
    earlier["S"] = fixture("S", earlier, generation_boundary=record_ref(boundary))
    c = sha256(b"synthetic commitment value")
    earlier["W"] = fixture("W", earlier, commitment=c)
    overrides = {"commitment": c, "decision": decision}
    if evidence is not None:
        overrides["evidence"] = evidence
    if publisher is not None:
        overrides["actor"] = publisher
    draft = fixture("C", {**earlier, "U": fixture("U", earlier, commitment=c)}, **overrides)["body"]
    proposed = copy.deepcopy(draft)
    del proposed["dependencies"]["U"]
    template = {"body": proposed, "digest": sha256(canonical_bytes(proposed)), "U_insertion_slot": "body.dependencies.U"}
    U = fixture("U", earlier, commitment=c, active_authority_tip="a" * 64, approved_public_record_body=template)
    C = fixture("C", {**earlier, "U": U}, **overrides)
    if status is not None:
        C = make_record("C", C["body"], status=status)
    return C, U, earlier["W"]


def validate(records, values):
    validate_publication_template(*records, expected_tip="a" * 64, private=values)


def non_text_tokens(C):
    """Every decimal run and 16-hex window in C's constant, derived and typed fields."""
    texts = set(public_text_surface(C))
    tokens = set()

    def walk(value, key=None):
        if isinstance(value, dict):
            for k, item in value.items():
                tokens.update(_tokens(k))
                walk(item, k)
        elif isinstance(value, list):
            for item in value:
                walk(item)
        elif isinstance(value, (str, int)) and not isinstance(value, bool):
            text = str(value)
            if text not in texts or key not in {"decision", "actor_id", "evidence_id", "status"}:
                tokens.update(_tokens(text))
    walk(C)
    return tokens


def _tokens(text):
    out = {f"{int(run):016x}" for run in re.findall(r"\d+", text) if int(run) < 2**64}
    out |= {text[i:i + 16] for i in range(len(text) - 15) if re.fullmatch(r"[0-9a-f]{16}", text[i:i + 16])}
    return out


def test_n1_01_realistic_small_value_K_publishes_end_to_end_and_at_the_validator(tmp_path):
    validate(publication(), private())
    study = Study(tmp_path)
    assert {f"{v:016x}" for v in (0, 1, 2, 3, 5, 7, 42)} <= set(study.K)
    study.complete()
    _, _, C, published = study.through_publication()
    assert published == record_ref(C)
    with pytest.raises(IntegrityError, match="already consumed"):
        publish_commitment(study.log, C, expected_tip=study.log.tip, operation_id="synthetic-publication",
                           publisher=C["body"]["actor"], destination=tmp_path / "second-C.json")


def test_n1_02_adversarial_K_built_from_C_own_structure_never_refuses():
    records = publication()
    tokens = non_text_tokens(records[0])
    assert len(tokens) > 500
    validate(records, private(K=sorted(tokens)))
    assert private(K=sorted(tokens)).exposed_in(records[0]["body"])  # the seal-04 whole-record scan


def test_n1_03_sweep_every_value_below_65536_and_the_n1_reproduction():
    C = publication()[0]
    base = set(GENERATED) | set(realistic_K())
    for k in range(65536):
        values = PrivateValues(frozenset(base | {f"{k:016x}"}), (SALT_BYTES,), (ROOT,))
        assert not values.exposed_in_public_record(C), k
    for k in (2, 6, 8, 9, 256, 1412):
        old = PrivateValues(frozenset({f"{k:016x}"}), (), ())
        assert old.exposed_in(C["body"]) and not old.exposed_in_public_record(C)


def test_n1_04_generated_values_equal_to_structural_tokens_do_not_refuse_but_disclosure_does():
    records = publication()
    window = records[0]["body"]["dependencies"]["P"]["digest"][:16]
    generated = [f"{k:016x}" for k in (2, 6, 8, 9, 256, 1412)] + [window]
    validate(records, private(K=E6_E8, generated=generated))
    for leak in ("1412", window, window.upper()):
        with pytest.raises(IntegrityError, match="actual private"):
            validate(publication(decision="AUTHORIZED; " + leak), private(K=E6_E8, generated=generated))


REPRESENTATIONS = {
    "position_hex": GENERATED[0], "position_upper": GENERATED[0].upper(),
    "position_decimal": str(int(GENERATED[0], 16)), "K_hex": f"{42:016x}", "K_upper": f"{42:016x}".upper(),
    "K_decimal": "42", "salt_hex": SALT, "salt_upper": SALT.upper(),
    "salt_base64": base64.b64encode(SALT_BYTES).decode().rstrip("="),
    "salt_base64url": base64.urlsafe_b64encode(SALT_BYTES).decode().rstrip("="),
    "root_forward": ROOT.upper(), "root_backslash": ROOT.replace("/", "\\"),
}
FIELDS = ("decision", "actor_id", "authority_evidence_id", "evidence_id", "status")


def leaking(field, text):
    if field == "decision":
        return publication(decision="AUTHORIZED leak " + text)
    if field == "actor_id":
        return publication(publisher=actor("publisher", "publisher leak " + text))
    if field == "authority_evidence_id":
        publisher = actor("publisher", "synthetic-publisher")
        publisher["authority_evidence"] = {**publisher["authority_evidence"], "evidence_id": "leak " + text}
        return publication(publisher=publisher)
    if field == "evidence_id":
        return publication(evidence=[{"evidence_id": "leak " + text, "sha256_raw": sha256(b"public"),
                                      "bytes": 6, "visibility": "PUBLIC"}])
    return publication(status="leak " + text)


@pytest.mark.parametrize("representation", REPRESENTATIONS)
@pytest.mark.parametrize("field", FIELDS)
def test_n1_05_every_protected_field_and_representation_is_refused(field, representation):
    with pytest.raises(IntegrityError):
        validate(leaking(field, REPRESENTATIONS[representation]), private())


@pytest.mark.parametrize("field", FIELDS[:4])
def test_n1_05_pre_u_check_refuses_disclosure_and_u_cannot_be_issued(tmp_path, field):
    study = Study(tmp_path)
    study.complete()
    study.issue("W", study.log.resolve(study.produce()))
    leak = str(int(study.accepted[0], 16))
    body = study.template()
    if field == "decision":
        body["decision"] = "PUBLISHED " + leak
    elif field == "actor_id":
        body["actor"] = {**body["actor"], "actor_id": "publisher " + leak}
    elif field == "authority_evidence_id":
        body["actor"] = {**body["actor"], "authority_evidence": {**body["actor"]["authority_evidence"],
                                                                 "evidence_id": "publisher " + leak}}
    else:
        body["evidence"] = [{"evidence_id": "notice " + leak, "sha256_raw": sha256(b"n"), "bytes": 1,
                             "visibility": "PUBLIC"}]
    checked = study.check(body)
    assert checked["decision"] == "FAIL"
    with pytest.raises(IntegrityError):
        study.issue_U(study.U(body, [checked["receipt"]]))
    assert "U" not in study.log.bindings


def test_n1_06_look_alike_values_remain_publishable():
    # Hex look-alikes contain short digit runs, which option A protects for small K members, so
    # generated-value look-alikes are checked against a K without small members.
    near = [f"{int(GENERATED[0], 16) + 1:016x}", str(int(GENERATED[0], 16) - 1)]
    validate(publication(decision="AUTHORIZED " + " ".join(near)), private(K=E6_E8))
    validate(publication(decision="AUTHORIZED 41 43 4200"), private())


def test_n1_07_template_refused_before_u_then_corrected_and_d3_issuance_refusals(tmp_path):
    study = Study(tmp_path)
    study.complete()
    with pytest.raises(IntegrityError):  # no pre-U check before W is issued
        study.check({"record_role": "C"})
    study.issue("W", study.log.resolve(study.produce()))
    bad = study.template(decision="PUBLISHED " + str(int(study.accepted[3], 16)))
    failed = study.check(bad)
    assert failed["decision"] == "FAIL"
    tip = study.log.tip
    for receipts in ([], [failed["receipt"]]):
        with pytest.raises(IntegrityError):
            study.issue_U(study.U(bad, receipts))
    good = study.template()
    passed = study.check(good)
    with pytest.raises(IntegrityError):  # a PASS receipt for a different template
        study.issue_U(study.U(bad, [passed["receipt"]]))
    assert study.log.tip == tip and "U" not in study.log.bindings
    U = study.U(good, [passed["receipt"]])
    issued = study.issue_U(U)
    assert issued["event"]["body"]["evidence"] == [passed["receipt"], issued["attestation"]]
    assert pv.verify_operational_u(study.log)["decision"] == "ADMISSIBLE"
    C = make_record("C", {**good, "dependencies": {**good["dependencies"], "U": record_ref(U)}})
    assert publish_commitment(study.log, C, expected_tip=study.log.tip, operation_id="synthetic-publication",
                              publisher=good["actor"], destination=tmp_path / "C.json") == record_ref(C)


def test_n1_07_a_u_issued_by_generic_append_is_not_operationally_admissible(tmp_path):
    study = Study(tmp_path)
    study.complete()
    study.issue("W", study.log.resolve(study.produce()))
    body = study.template()
    U = study.U(body, [study.check(body)["receipt"]])
    study.log.retain_record(U)
    study.issue("U", U)  # bypasses issue_publication_authorization
    with pytest.raises(IntegrityError, match="Gate-8 issuance path"):
        pv.verify_operational_u(study.log)


def test_n1_08_free_text_k_collision_is_caught_before_u_and_avoided_by_rewording(tmp_path):
    study = Study(tmp_path)
    assert f"{2:016x}" in study.K
    study.complete()
    study.issue("W", study.log.resolve(study.produce()))
    assert study.check(study.template(decision="PUBLISHED 2 notices"))["decision"] == "FAIL"
    assert study.check(study.template(decision="PUBLISHED"))["decision"] == "PASS"


def test_n1_09_every_field_is_classified_and_unclassified_fields_fail_closed(tmp_path):
    C = publication()[0]
    assert public_text_surface(C) == ["AUTHORIZED", "synthetic-publisher", "synthetic/synthetic-publisher"]
    for broken in ({**C, "extra": "x"}, {**C, "body": {**C["body"], "extra": "x"}},
                   {**C, "body": {**C["body"], "actor": {**C["body"]["actor"], "extra": "x"}}},
                   {**C, "body": {**C["body"], "decision": 7}}):
        with pytest.raises(IntegrityError):
            public_text_surface(broken)
    study = Study(tmp_path)
    study.complete()
    study.issue("W", study.log.resolve(study.produce()))
    assert study.check({**study.template(), "extra": "x"})["decision"] == "FAIL"


def test_n1_10_marker_layer_is_unchanged():
    marked = publication(evidence=[{"evidence_id": "value_hex", "sha256_raw": sha256(b"m"), "bytes": 1,
                                    "visibility": "PUBLIC"}])
    with pytest.raises(IntegrityError, match="private values/paths/diagnostics"):
        validate(marked, private())


def test_issuance_requires_the_registered_lead(tmp_path):
    study = Study(tmp_path)
    study.complete()
    study.issue("W", study.log.resolve(study.produce()))
    body = study.template()
    receipt = study.check(body)["receipt"]
    U = study.U(body, [receipt])
    with pytest.raises(IntegrityError):
        pv.issue_publication_authorization(study.log, U, lead=actor("research_lead", "other-lead"),
                                           expected_tip=study.log.tip, operation_id="synthetic-u-issuance")
    assert pv.issue_publication_authorization(study.log, U, lead=LEAD, expected_tip=study.log.tip,
                                              operation_id="synthetic-u-issuance")["U"] == record_ref(U)
    assert uint64("unused") not in canonical_bytes(U).decode()
