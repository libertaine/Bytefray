"""Seal 06: F1-F4 of disposition 03 under v2_gate8_scope_02.json (implementer tests).

SYNTHETIC QUALIFICATION FIXTURES ONLY. Every REAL-labelled study below is the hand-built
fixture of test_v6_e9_v2_gate8_producer.py, in a pytest temporary root, in the
synthetic-e9-v2-only namespace, with synthetic actors and synthetic bytes. REAL appears only
as an input declaration presented to the code under test. No REAL entropy is consumed,
salt_creation is never invoked, and nothing here is operational evidence.
"""

from __future__ import annotations

import inspect
import json

import pytest

from engine.tests._e9_v2_synthetic_records import STUDY, actor
from engine.tests.test_v6_e9_v2_gate8_producer import (
    CHECKER,
    INTEGRITY,
    LEAD,
    OP,
    RECORDER,
    VERIFIER,
    Study,
    built,
    encode,
)
from tools.research.v6.e9.v2 import private_verification as pv
from tools.research.v6.e9.v2.commitment import PrivateValues, commitment_value
from tools.research.v6.e9.v2.generation import DOMAIN, Generator, N
from tools.research.v6.e9.v2.inventory import artifact
from tools.research.v6.e9.v2.records import (
    IntegrityError,
    canonical_bytes,
    make_record,
    record_ref,
    sha256,
)


def labels(study):
    return [item["outcome"] for item in study.outcomes()]


def registry_path(study):
    return study.log.root / "producer-roots" / (study.log.bindings["G"]["digest"] + ".json")


def marker_path(study):
    return study.log.root / "first-raw" / (study.log.bindings["G"]["digest"] + ".json")


DURABLE = {"registry": registry_path, "marker": marker_path}


def events(study):
    return sorted(study.log.root.glob("event-*.json"))


def active_tip(study):
    """The durable active tip, read without taking the authority lock."""
    return json.loads((study.log.root / "active.json").read_bytes())["tip"]


def substitute(study, which):
    """Bytes of the same shape that are not the bytes the generation boundary binds."""
    raw = DURABLE[which](study).read_bytes()
    item = json.loads(raw)
    if which == "registry":
        item["producer_root"] = item["producer_root"] + "-substituted"
    else:
        item["producer_registry"] = {**item["producer_registry"], "sha256_raw": "0" * 64}
    assert encode(item) != raw
    return encode(item)


def make_unreadable(path):
    path.unlink()
    path.mkdir()  # a directory where the durable file belongs cannot be read as one


def restore(path, raw):
    if path.is_dir():
        path.rmdir()
    path.write_bytes(raw)


def no_generation(monkeypatch):
    for name in ("consume", "draw_one", "snapshot", "complete", "seal_payload", "generation_receipt"):
        monkeypatch.setattr(Generator, name, lambda *a, **k: pytest.fail("W recovery reached the producer"))


# ---- F1: durable registry and first-raw marker --------------------------------------------------

@pytest.mark.parametrize("which", ["registry", "marker"])
@pytest.mark.parametrize("fault", ["missing", "unreadable"])
def test_s6_f1_missing_or_unreadable_is_unavailable_until_exact_restoration(tmp_path, monkeypatch, which, fault):
    """S6-F1-01..04 and S6-F1-09."""
    study = built(tmp_path)
    path = DURABLE[which](study)
    retained = path.read_bytes()
    S_before, boundary_before = dict(study.log.bindings), study.log.resolve(study.S["body"]["generation_boundary"])
    event_count = len(events(study))
    (make_unreadable if fault == "unreadable" else lambda p: p.unlink())(path)
    no_generation(monkeypatch)
    with pytest.raises(pv.Unavailable, match="unavailable"):
        study.produce()
    assert labels(study) == ["UNAVAILABLE"] and not (study.folder / "W.json").exists()
    assert path.is_dir() if fault == "unreadable" else not path.exists()  # the producer wrote nothing
    restore(path, retained)
    W = study.log.resolve(study.produce())
    assert labels(study) == ["UNAVAILABLE", "PASS"] and W["body"]["decision"] == "PASS"
    # Recovery replaced nothing: same tuple, boundary, payload, salt, audit and K; no producer event.
    assert study.log.bindings == S_before and len(events(study)) == event_count
    assert study.log.resolve(study.S["body"]["generation_boundary"]) == boundary_before
    assert (W["body"]["payload"], W["body"]["salt"]) == (study.S["body"]["payload"], study.S["body"]["salt"])
    assert W["body"]["commitment"] == commitment_value(study.payload_raw, study.salt)
    assert path.read_bytes() == retained
    for ref in (study.S["body"]["payload"], study.S["body"]["salt"], study.S["body"]["audit"]):
        assert sha256(study.log.read_artifact(ref)) == ref["sha256_raw"]


def test_s6_f1_an_unreadable_registry_listing_is_unavailable(tmp_path, monkeypatch):
    study = built(tmp_path)

    def unreadable():
        raise PermissionError("simulated unreadable producer registry")
    monkeypatch.setattr(study.log, "registered_producers", unreadable)
    with pytest.raises(pv.Unavailable):
        study.produce()
    monkeypatch.undo()
    study.produce()
    assert labels(study) == ["UNAVAILABLE", "PASS"]


@pytest.mark.parametrize("which", ["registry", "marker"])
@pytest.mark.parametrize("bytes_", ["substituted", "corrupt"])
def test_s6_f1_present_wrong_bytes_are_a_verification_failure(tmp_path, which, bytes_):
    """S6-F1-05, S6-F1-06."""
    study = built(tmp_path)
    path = DURABLE[which](study)
    path.write_bytes(substitute(study, which) if bytes_ == "substituted" else b'{"corrupt"')
    with pytest.raises(IntegrityError) as raised:
        study.produce()
    assert not isinstance(raised.value, pv.Unavailable)
    assert labels(study) == ["FAILED_VERIFICATION"] and not (study.folder / "W.json").exists()
    with pytest.raises(pv.Refused, match="already failed"):
        study.produce()


@pytest.mark.parametrize("which", ["registry", "marker"])
def test_s6_f1_substituted_restoration_after_unavailable_fails(tmp_path, which):
    """S6-F1-07."""
    study = built(tmp_path)
    path = DURABLE[which](study)
    substituted = substitute(study, which)
    path.unlink()
    with pytest.raises(pv.Unavailable):
        study.produce()
    path.write_bytes(substituted)
    with pytest.raises(IntegrityError) as raised:
        study.produce()
    assert not isinstance(raised.value, pv.Unavailable)
    assert labels(study) == ["UNAVAILABLE", "FAILED_VERIFICATION"]
    with pytest.raises(pv.Refused, match="already failed"):
        study.produce()


@pytest.mark.parametrize("missing", ["registry", "marker"])
def test_s6_f1_a_present_mismatch_takes_precedence_over_a_missing_artifact(tmp_path, missing):
    """S6-F1-08."""
    study = built(tmp_path)
    other = "marker" if missing == "registry" else "registry"
    DURABLE[other](study).write_bytes(substitute(study, other))
    DURABLE[missing](study).unlink()
    with pytest.raises(IntegrityError) as raised:
        study.produce()
    assert not isinstance(raised.value, pv.Unavailable)
    assert labels(study) == ["FAILED_VERIFICATION"]


@pytest.mark.parametrize("parts", [("producer", "entropy"), ("marker", "entropy")])
def test_s6_f1_boundary_content_defects_stay_failed_with_a_durable_artifact_missing(tmp_path, parts):
    """S6-F1-10."""
    study = Study(tmp_path, parts=parts)
    study.complete()
    marker_path(study).unlink()
    with pytest.raises(IntegrityError) as raised:
        study.produce()
    assert not isinstance(raised.value, pv.Unavailable)
    assert labels(study) == ["FAILED_VERIFICATION"]


# ---- F2: W-04 classification in every chain shape -----------------------------------------------

def forbidden_event(study, kind):
    if kind == "consume":
        study.log.append("CONSUME", RECORDER, expected_tip=study.log.tip, operation_id=OP,
                         affected=[study.log.bindings["S"]])
    else:  # a lead REVOKE affecting no authorization passes the sealed authority check
        study.log.append("REVOKE", LEAD, expected_tip=study.log.tip, operation_id=OP,
                         evidence=[artifact(b"synthetic revoke", "SYNTHETIC-REVOKE")])


def verifier_calls(monkeypatch):
    calls, real = [], pv.verify_complete_private

    def spy(**kwargs):
        calls.append(True)
        return real(**kwargs)
    monkeypatch.setattr(pv, "verify_complete_private", spy)
    return calls


@pytest.mark.parametrize("shape", [(), ("partial_continue",), ("generated_continue",), ("generated_release",)],
                         ids=["no-continuation", "partial", "completed-continue", "completed-release"])
@pytest.mark.parametrize("kind", ["consume", "revoke"])
def test_s6_f2_a_forbidden_tail_event_fails_verification_in_every_chain_shape(tmp_path, monkeypatch, shape, kind):
    """S6-F2-01: the same W-04 outcome after a completed-stage continuation as in any other shape."""
    study = built(tmp_path, *shape)
    forbidden_event(study, kind)
    calls = verifier_calls(monkeypatch)
    with pytest.raises(IntegrityError, match="outside the complete continuation chain") as raised:
        study.produce()
    assert not isinstance(raised.value, (pv.Refused, pv.Unavailable))
    assert labels(study) == ["FAILED_VERIFICATION"] and calls == []
    with pytest.raises(pv.Refused, match="already failed"):
        study.produce()


@pytest.mark.parametrize("shape", ["generated_continue", "generated_release"])
@pytest.mark.parametrize("issues", [1, 2])
def test_s6_f2_only_tuple_extending_issues_after_a_completed_continuation_are_refused(
        tmp_path, monkeypatch, shape, issues):
    """S6-F2-02: W-04 permits these events; the frozen verifier cannot consume that tip."""
    study = built(tmp_path, shape)
    for _ in range(issues):
        study.log.append("ISSUE", LEAD, expected_tip=study.log.tip, operation_id=OP)
    reads, real_reader = [], pv._reader
    monkeypatch.setattr(pv, "_reader", lambda authority: (lambda ref: reads.append(ref) or real_reader(authority)(ref)))
    with pytest.raises(pv.Refused, match="completed-stage continuation"):
        study.produce()
    assert reads == [] and labels(study) == ["REFUSED_PRECONDITION"]


@pytest.mark.parametrize("order", ["issue-then-forbidden", "forbidden-then-issue"])
def test_s6_f2_a_mixed_tail_fails_verification(tmp_path, order):
    """S6-F2-03."""
    study = built(tmp_path, "generated_continue")
    steps = [lambda: study.log.append("ISSUE", LEAD, expected_tip=study.log.tip, operation_id=OP),
             lambda: forbidden_event(study, "consume")]
    for step in steps if order == "issue-then-forbidden" else reversed(steps):
        step()
    with pytest.raises(IntegrityError) as raised:
        study.produce()
    assert not isinstance(raised.value, (pv.Refused, pv.Unavailable))
    assert labels(study) == ["FAILED_VERIFICATION"]


# ---- F3: W, its retained record and PASS under the verifying lease ----------------------------------

def write_spy(monkeypatch, study, *, on_W=None):
    """Lock state and durable tip at every producer write, retention of W included."""
    seen, real_bytes, real_retain = [], pv.durable_bytes, study.log.retain_record
    lock = study.log.root / "exclusive.lock"

    def durable(path, raw):
        if path.name == "W.json" and on_W is not None:
            on_W()
        seen.append((path.name, lock.exists(), active_tip(study)))
        return real_bytes(path, raw)

    def retain(record):
        if record["body"]["record_role"] == "W":
            seen.append(("retain W", lock.exists(), active_tip(study)))
        return real_retain(record)
    monkeypatch.setattr(pv, "durable_bytes", durable)
    monkeypatch.setattr(study.log, "retain_record", retain)
    return seen


def test_s6_f3_w_retention_w_json_and_pass_are_written_under_the_verifying_lease(tmp_path, monkeypatch):
    """S6-F3-01."""
    study = built(tmp_path)
    seen = write_spy(monkeypatch, study)
    W = study.log.resolve(study.produce())
    tip = W["body"]["active_authority_tip"]
    assert [name for name, _, _ in seen] == [
        "attempt-0001.intent.json", "retain W", "W.json", "attempt-0001.outcome.json"]
    assert seen[0][1] is False  # the intent precedes the lease
    assert all(locked and durable_tip == tip for _, locked, durable_tip in seen[1:])
    assert labels(study) == ["PASS"]


def test_s6_f3_an_authority_append_cannot_interleave_before_pass(tmp_path, monkeypatch):
    """S6-F3-02."""
    study = built(tmp_path)
    tip, count, attempts = study.log.tip, len(events(study)), []

    def interleave():
        try:
            study.log.append("HOLD", INTEGRITY, expected_tip=tip, operation_id=OP,
                             evidence=[artifact(b"interleaving hold", "STOP-INTERLEAVE")])
        except IntegrityError as exc:
            attempts.append(str(exc))
        else:
            attempts.append("appended")
    write_spy(monkeypatch, study, on_W=interleave)
    W = study.log.resolve(study.produce())
    assert attempts == ["authority busy or interrupted transaction"]
    assert len(events(study)) == count and labels(study) == ["PASS"]
    assert W["body"]["active_authority_tip"] == tip == study.log.tip
    study.log.append("HOLD", INTEGRITY, expected_tip=tip, operation_id=OP,
                     evidence=[artifact(b"later hold", "STOP-LATER")])
    assert len(events(study)) == count + 1


def test_s6_f3_a_write_failure_leaves_no_outcome_and_is_listed_as_interrupted(tmp_path, monkeypatch):
    """S6-F3-03: retention of W fails."""
    study = built(tmp_path)
    real_retain = study.log.retain_record

    def failing(record):
        if record["body"]["record_role"] == "W":
            raise IntegrityError("simulated W retention failure")
        return real_retain(record)
    monkeypatch.setattr(study.log, "retain_record", failing)
    with pytest.raises(IntegrityError, match="simulated W retention failure"):
        study.produce()
    assert labels(study) == [] and not (study.folder / "W.json").exists()
    assert not (study.log.root / "exclusive.lock").exists()
    monkeypatch.undo()
    study.produce()
    second = json.loads((study.folder / "attempt-0002.outcome.json").read_bytes())
    assert (second["outcome"], second["interrupted_prior_attempts"]) == ("PASS", [1])


def test_s6_f3_a_partial_w_file_leaves_no_outcome_and_fails_closed(tmp_path, monkeypatch):
    """S6-F3-03: the W.json write is interrupted after partial bytes."""
    study = built(tmp_path)
    real_bytes = pv.durable_bytes

    def partial(path, raw):
        if path.name == "W.json":
            path.write_bytes(raw[:20])
            raise OSError("simulated interrupted W write")
        return real_bytes(path, raw)
    monkeypatch.setattr(pv, "durable_bytes", partial)
    with pytest.raises(OSError):
        study.produce()
    assert labels(study) == []
    monkeypatch.undo()
    with pytest.raises(pv.Refused, match="partial W file"):
        study.produce()
    assert labels(study) == ["REFUSED_PRECONDITION"] and len((study.folder / "W.json").read_bytes()) == 20


def test_s6_f3_a_failed_post_action_recheck_after_pass_adds_no_second_outcome(tmp_path):
    """S6-F3-04: exceptional drift after PASS propagates; nothing is tidied."""
    study = built(tmp_path)
    passed = study.folder / "attempt-0001.outcome.json"

    def drift():
        if passed.exists():
            raise IntegrityError("instrument/qualification source pin drift")
    study.log.source_check = drift
    with pytest.raises(IntegrityError, match="source pin drift"):
        study.produce()
    assert labels(study) == ["PASS"] and (study.folder / "W.json").exists()
    assert sorted(path.name for path in study.folder.glob("attempt-*.outcome.json")) == [passed.name]


@pytest.mark.parametrize("outcome", ["UNAVAILABLE", "REFUSED_PRECONDITION", "FAILED_VERIFICATION"])
def test_s6_f3_non_pass_outcomes_are_written_after_the_lease(tmp_path, monkeypatch, outcome):
    """S6-F3-05: the protected section is not widened to the other outcomes."""
    study = built(tmp_path)
    if outcome == "UNAVAILABLE":
        marker_path(study).unlink()
    elif outcome == "REFUSED_PRECONDITION":
        study.log.append("HOLD", INTEGRITY, expected_tip=study.log.tip, operation_id=OP,
                         evidence=[artifact(b"held", "STOP-HELD")])
    else:
        forbidden_event(study, "consume")
    seen = write_spy(monkeypatch, study)
    with pytest.raises(IntegrityError):
        study.produce()
    assert labels(study) == [outcome]
    assert [(name, locked) for name, locked, _ in seen] == [
        ("attempt-0001.intent.json", False), ("attempt-0001.outcome.json", False)]


# ---- F4: operational W admissibility at the pre-U check and U issuance -----------------------------

def produced(tmp_path, *shapes):
    """A study whose W the producer made, not yet issued."""
    study = built(tmp_path, *shapes)
    return study, study.log.resolve(study.produce())


def issued(tmp_path):
    study, W = produced(tmp_path)
    study.issue("W", W)
    return study


def W_body(study, **changes):
    """A W body as the producer shapes it, built by hand."""
    counts = study.S["body"]["audit_counts"]
    body = {"record_role": "W", "study_id": STUDY, "actor": VERIFIER, "decision": "PASS",
            "dependencies": {role: study.log.bindings[role] for role in pv.W_DEPENDENCIES},
            "evidence": [], "active_authority_tip": study.log.tip,
            "all_position_checks": {"accepted_count": N, "contiguous_order": True, "domain": DOMAIN,
                                    "original_K_disjoint": True, "strict_uint64": True, "unique": True,
                                    "supplemented_history_count": 0, "supplemented_history_disjoint": True},
            "audit_reproduction": {"audit_counts": counts, "audit_sha256_raw": study.S["body"]["audit"]["sha256_raw"],
                                   "audit_tip": study.audit_tip, "entropy_source": "REAL",
                                   "full_private_read_back": True, "historical_completeness": "NOT ESTABLISHED"},
            "commitment": commitment_value(study.payload_raw, study.salt), "payload": study.S["body"]["payload"],
            "salt": study.S["body"]["salt"], "supplement_chain": []}
    body.update(changes)
    return body


def forged_receipt(study, body):
    """A PASS receipt retained without the check, so issuance's own F4 refusal is reached."""
    digest = sha256(canonical_bytes(body))
    return study.log.retain_artifact(encode({
        "kind": pv.PRE_U_RECEIPT_KIND, "study_id": STUDY, "template_digest": digest, "decision": "PASS",
        "reason": None, "checker": CHECKER, "active_authority_tip": study.log.tip,
        "W": study.log.bindings["W"]}), pv.PRE_U_RECEIPT_ID + "-" + digest[:16])


def raw_evidence(study):
    return {path.name for path in (study.log.root / "evidence-raw").iterdir()}


def assert_value_free(study, text):
    private = PrivateValues(frozenset(study.accepted), (study.salt,), (str(study.log.root.resolve()),))
    assert not private.exposed_in(text)


def refused_at_both(study, match):
    """Pre-U retains no receipt; issuance writes no attestation, U or event."""
    body = study.template()
    tip, retained = study.log.tip, raw_evidence(study)
    with pytest.raises(IntegrityError, match=match) as raised:
        study.check(body)
    assert_value_free(study, str(raised.value))
    assert study.log.tip == tip and raw_evidence(study) == retained
    U = study.U(body, [forged_receipt(study, body)])
    retained = raw_evidence(study)
    with pytest.raises(IntegrityError, match=match):
        study.issue_U(U)
    assert study.log.tip == tip and "U" not in study.log.bindings and raw_evidence(study) == retained
    assert not (study.log.root / "evidence-records" / (U["digest"] + ".json")).exists()


def rewrite(path, change):
    item = json.loads(path.read_bytes())
    change(item)
    path.unlink()
    path.write_bytes(encode(item))


def test_s6_f4_a_valid_producer_w_progresses_and_admissibility_is_value_free(tmp_path):
    """S6-F4-07, S6-F4-08."""
    study = built(tmp_path)
    _, _, C, published = study.through_publication()
    assert published == record_ref(C) and pv.verify_operational_u(study.log)["decision"] == "ADMISSIBLE"
    other = issued(tmp_path / "admissible")
    result = pv.verify_operational_w(other.log)
    assert (result["decision"], result["W"], result["pass_attempt"]) == ("ADMISSIBLE", other.log.bindings["W"], 1)
    assert result["issuance_event"] == record_ref(json.loads(events(other)[-1].read_bytes()))
    assert_value_free(other, canonical_bytes(result).decode())


def test_s6_f4_later_events_that_do_not_revoke_w_keep_it_admissible(tmp_path):
    """A6 is not a rule against later events; a tuple-extending ISSUE may also precede ISSUE(+W)."""
    study, W = produced(tmp_path)
    study.log.append("ISSUE", LEAD, expected_tip=study.log.tip, operation_id=OP)
    study.issue("W", W)
    forbidden_event(study, "revoke")  # a later REVOKE that affects no authorization
    assert pv.verify_operational_w(study.log)["decision"] == "ADMISSIBLE"
    assert study.check(study.template())["decision"] == "PASS"


def test_s6_f4_a_hand_built_w_without_producer_evidence_is_refused(tmp_path):
    """S6-F4-01."""
    study = built(tmp_path)
    study.issue("W", make_record("W", W_body(study)))
    refused_at_both(study, "not written by the Gate-8 producer")


def test_s6_f4_a_hand_built_w_after_a_failed_verification_is_refused(tmp_path):
    """S6-F4-05: even with W.json and a PASS outcome planted beside the completed failure."""
    study = built(tmp_path)
    marker_path(study).write_bytes(substitute(study, "marker"))
    with pytest.raises(IntegrityError):
        study.produce()
    assert labels(study) == ["FAILED_VERIFICATION"]
    marker_path(study).unlink()
    study.log.mark_first_raw(study.generator.producer_ref)  # put the durable marker back
    W = make_record("W", W_body(study))
    (study.folder / "W.json").write_bytes(encode(W))
    (study.folder / "attempt-0002.intent.json").write_bytes(encode({
        "attempt": 2, "S": study.log.bindings["S"], "verifier": VERIFIER["actor_id"],
        "expected_tip": study.log.tip, "operation_id": "planted", "interrupted_prior_attempts": []}))
    (study.folder / "attempt-0002.outcome.json").write_bytes(encode({
        "attempt": 2, "outcome": "PASS", "reason": None, "W": record_ref(W), "interrupted_prior_attempts": []}))
    study.issue("W", W)
    refused_at_both(study, "matching retained PASS outcome")


def test_s6_f4_a_producer_w_without_its_pass_outcome_is_refused(tmp_path):
    """S6-F4-02."""
    study = issued(tmp_path)
    (study.folder / "attempt-0001.outcome.json").unlink()
    refused_at_both(study, "matching retained PASS outcome")


def test_s6_f4_a_mismatched_pass_outcome_is_refused(tmp_path):
    """S6-F4-03."""
    study = issued(tmp_path)
    rewrite(study.folder / "attempt-0001.outcome.json", lambda item: item.update(W=study.log.bindings["S"]))
    refused_at_both(study, "matching retained PASS outcome")


@pytest.mark.parametrize("field", ["verifier", "S", "expected_tip"])
def test_s6_f4_a_pass_outcome_from_another_attempt_is_refused(tmp_path, field):
    """S6-F4-04: the PASS attempt's own intent names another S, verifier or tip."""
    study = issued(tmp_path)
    other = {"verifier": "synthetic-other-verifier", "S": study.log.bindings["G"],
             "expected_tip": study.boundary["body"]["active_authority_tip"]}[field]
    rewrite(study.folder / "attempt-0001.intent.json", lambda item: item.update({field: other}))
    refused_at_both(study, "does not match its producer attempt")


@pytest.mark.parametrize("fault", ["substituted registry", "substituted marker", "missing marker"])
def test_s6_f4_a_w_whose_producer_root_or_marker_no_longer_holds_is_refused(tmp_path, fault):
    """S6-F4-04 and A2."""
    study = issued(tmp_path)
    if fault == "missing marker":
        marker_path(study).unlink()
    else:
        which = fault.split()[1]
        DURABLE[which](study).write_bytes(substitute(study, which))
    refused_at_both(study, "unavailable" if fault == "missing marker" else "producer|marker")


def test_s6_f4_a_w_json_other_than_the_bound_w_is_refused(tmp_path):
    """A3."""
    study = issued(tmp_path)
    path = study.folder / "W.json"
    raw = path.read_bytes()
    changed = raw.replace(b'"decision":"PASS"', b'"decision":"PASS" ', 1)
    assert changed != raw
    path.unlink()
    path.write_bytes(changed)
    refused_at_both(study, "not written by the Gate-8 producer")


def test_s6_f4_a_w_whose_retained_result_does_not_match_is_refused(tmp_path):
    """A5: chain/evidence bindings, with W.json and the PASS outcome rewritten to match."""
    study, W = produced(tmp_path)
    result = json.loads(study.log.read_artifact(W["body"]["evidence"][0]))
    result["active_chain_tip"] = study.boundary["body"]["active_authority_tip"]
    forged = make_record("W", {**W["body"], "evidence": [study.log.retain_artifact(encode(result), pv.RESULT_ID)]})
    (study.folder / "W.json").unlink()
    (study.folder / "W.json").write_bytes(encode(forged))
    rewrite(study.folder / "attempt-0001.outcome.json", lambda item: item.update(W=record_ref(forged)))
    study.issue("W", forged)
    refused_at_both(study, "retained verification result")


def test_s6_f4_a_w_naming_an_unregistered_verifier_is_refused(tmp_path):
    """A1."""
    study, W = produced(tmp_path)
    forged = make_record("W", {**W["body"], "actor": actor("independent_verifier", "synthetic-unregistered")})
    study.issue("W", forged)
    refused_at_both(study, "independent verifier")


def test_s6_f4_an_intervening_non_issue_event_before_issue_w_is_refused(tmp_path):
    """A6."""
    study, W = produced(tmp_path)
    forbidden_event(study, "revoke")
    study.issue("W", W)
    refused_at_both(study, "non-ISSUE authority event")


def test_s6_f4_a_revoked_w_is_refused(tmp_path):
    """A6: a validly produced PASS W that was later revoked."""
    study = issued(tmp_path)
    body = study.template()
    passed = study.check(body)
    assert passed["decision"] == "PASS"
    study.log.append("REVOKE", LEAD, expected_tip=study.log.tip, operation_id=OP,
                     affected=[study.log.bindings["W"]], evidence=[artifact(b"revoke W", "SYNTHETIC-REVOKE-W")])
    with pytest.raises(IntegrityError, match="revoked"):
        pv.verify_operational_w(study.log)
    refused_at_both(study, "revoked")
    with pytest.raises(IntegrityError, match="revoked"):  # the genuine PASS receipt does not help
        study.issue_U(study.U(body, [passed["receipt"]]))


def test_s6_f4_public_signatures():
    """S6-F4-08."""
    def shape(function):
        return [(p.name, p.kind) for p in inspect.signature(function).parameters.values()]
    positional, keyword = inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.KEYWORD_ONLY
    assert shape(pv.verify_operational_w) == [("authority", positional)]
    assert shape(pv.verify_operational_u) == [("authority", positional)]
    assert shape(pv.produce_private_verification) == [
        ("authority", positional), ("verifier", keyword), ("expected_tip", keyword), ("operation_id", keyword)]
    assert shape(pv.check_publication_template) == [
        ("authority", positional), ("proposed_body", positional), ("checker", keyword),
        ("expected_tip", keyword), ("operation_id", keyword)]
    assert shape(pv.issue_publication_authorization) == [
        ("authority", positional), ("U", positional), ("lead", keyword),
        ("expected_tip", keyword), ("operation_id", keyword)]
