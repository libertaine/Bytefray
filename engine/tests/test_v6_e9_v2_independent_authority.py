"""Independent durable authority negative/race/fault qualification."""

from __future__ import annotations

import hashlib

import pytest

from tools.research.v6.e9.v2.authority import AuthorityLog, Lease

OPERATIONS = ("raw_draw", "salt_creation", "payload_seal", "private_verification",
              "commitment_publication", "worker_start", "infrastructure_retry",
              "final_assembly", "final_seal", "result_promotion")


def evidence():
    return {"bytes": 19, "sha256_raw": hashlib.sha256(b"independent-fixture").hexdigest(),
            "evidence_id": "independent-authority-fixture", "visibility": "PRIVATE"}


def actor(role):
    return {"actor_id": role, "role": role, "authority_evidence": evidence()}


def log_at(tmp_path):
    return AuthorityLog(tmp_path, "independent-synthetic-study", {},
                        actors={r: r for r in ("research_lead", "recorder",
                                               "independent_integrity_verifier")},
                        resolver=lambda ref: pytest.fail("absent record resolved"),
                        source_check=lambda: None)


@pytest.mark.parametrize("operation", OPERATIONS)
def test_every_consumer_denies_absent_tuple_before_action(tmp_path, operation):
    log = log_at(tmp_path)
    log.append("ISSUE", actor("research_lead"), expected_tip=log.tip,
               operation_id="independent-fixture-operation", evidence=[evidence()])
    with pytest.raises(ValueError):
        log.protected(operation, expected_tip=log.tip, operation_id="independent-fixture-operation",
                      action=lambda lease: pytest.fail("unauthorized consuming action"))


@pytest.mark.parametrize("operation", OPERATIONS)
def test_every_consumer_denies_hold_before_action(tmp_path, operation):
    log = log_at(tmp_path)
    log.append("HOLD", actor("independent_integrity_verifier"), expected_tip=log.tip,
               operation_id="independent-fixture-operation", evidence=[evidence()])
    with pytest.raises(ValueError):
        log.protected(operation, expected_tip=log.tip, operation_id="independent-fixture-operation",
                      action=lambda lease: pytest.fail("held consuming action"))


@pytest.mark.parametrize("operation", OPERATIONS)
def test_every_consumer_denies_terminal_closure_before_action(tmp_path, operation):
    log = log_at(tmp_path)
    log.append("TERMINATE", actor("research_lead"), expected_tip=log.tip,
               operation_id="independent-fixture-operation", evidence=[evidence()])
    with pytest.raises(ValueError):
        log.protected(operation, expected_tip=log.tip, operation_id="independent-fixture-operation",
                      action=lambda lease: pytest.fail("terminal consuming action"))


def test_actor_role_and_stale_tip_fail_before_event_append(tmp_path):
    log = log_at(tmp_path)
    with pytest.raises(ValueError):
        log.append("ISSUE", actor("recorder"), expected_tip="genesis", operation_id="fixture")
    assert not list(tmp_path.glob("event-*.json"))
    log.append("ISSUE", actor("research_lead"), expected_tip="genesis", operation_id="fixture")
    with pytest.raises(ValueError):
        log.append("ISSUE", actor("research_lead"), expected_tip="genesis", operation_id="fixture")
    assert len(list(tmp_path.glob("event-*.json"))) == 1


@pytest.mark.parametrize("fault", ["missing_tip", "forked_tip", "crash_lock", "event_gap"])
def test_faulted_durable_state_retained_and_never_repaired(tmp_path, fault):
    log = log_at(tmp_path)
    log.append("ISSUE", actor("research_lead"), expected_tip="genesis", operation_id="fixture")
    event_raw = (tmp_path / "event-00000001.json").read_bytes()
    if fault == "missing_tip":
        (tmp_path / "active.json").unlink()
    elif fault == "forked_tip":
        (tmp_path / "active.json").write_bytes(b'{"sequence":1,"tip":"unknown"}\n')
    elif fault == "crash_lock":
        (tmp_path / "exclusive.lock").write_bytes(b"deterministic interrupted transaction\n")
    else:
        (tmp_path / "event-00000001.json").rename(tmp_path / "event-00000002.json")
    with pytest.raises(ValueError):
        _ = log.tip
    assert event_raw in [p.read_bytes() for p in tmp_path.glob("event-*.json")]


def test_exclusive_lock_serializes_revocation_against_protected_action(tmp_path):
    log = log_at(tmp_path)
    with log.exclusive(), pytest.raises(ValueError):
        log.append("REVOKE", actor("research_lead"), expected_tip="genesis", operation_id="fixture")
    assert log.tip == "genesis"


def test_terminal_closure_never_releases_and_late_artifacts_retained(tmp_path):
    log = log_at(tmp_path)
    lease = Lease("independent-synthetic-study", "fixture", 0, "genesis")
    log.append("TERMINATE", actor("research_lead"), expected_tip="genesis",
               operation_id="fixture", evidence=[evidence()])
    receipt = log.retain_worker_artifact(lease, b"synthetic late artifact", artifact_id="late-fixture")
    assert receipt["late_fenced"] is True
    assert receipt["eligible"] is False
    assert (tmp_path / "retained/late-fixture.bin").read_bytes() == b"synthetic late artifact"
    with pytest.raises(ValueError):
        log.append("RELEASE", actor("research_lead"), expected_tip=log.tip,
                   operation_id="fixture", evidence=[evidence()])
