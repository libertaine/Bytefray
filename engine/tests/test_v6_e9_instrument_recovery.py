"""Independent state-machine, retention, outcome blindness and execution-lock fixtures."""

from dataclasses import asdict, replace

import pytest

from tools.research.v6.e9.collection import (
    ALLOWLIST,
    Dispatcher,
    Journal,
    RecoveryEvidence,
    WorkerInterrupted,
    require_execution_approval,
)
from tools.research.v6.e9.protocol import (
    Cell,
    ExecutionLocked,
    IntegrityError,
    file_digest,
    write_once,
)


def make(tmp_path):
    return Journal(tmp_path, Cell("A", "RUSH8", 1, "A"), {"synthetic": "no experimental seed"})


def evidence(journal, kind="host_worker_loss"):
    return RecoveryEvidence(journal.cell.identity, journal.binding, 1, "external-supervisor", kind,
                            True, True, True, False)


def finish(path):
    for name in ("result.json", "replay.jsonl", "trace.jsonl", "diagnostic.json"):
        write_once(path / name, {"synthetic": True})


def validate(path):
    return {name: file_digest(path / name) for name in ("result.json", "replay.jsonl", "trace.jsonl", "diagnostic.json")}


@pytest.mark.parametrize("kind", sorted(ALLOWLIST))
def test_every_allowlisted_failure_is_recovered_automatically_once(tmp_path, kind):
    journal = make(tmp_path)
    starts = []

    def backend(path):
        starts.append(path.name)
        if len(starts) == 1:
            write_once(path / "partial.json", {"synthetic_partial": True})
            raise WorkerInterrupted()
        finish(path)

    output = Dispatcher(backend, validate, lambda j: evidence(j, kind)).dispatch(journal)
    assert starts == ["attempt-01", "attempt-02"]
    assert output.name == "attempt-02"
    assert (journal.root / "attempt-01/partial.json").exists()
    assert journal.validate_attempts()[1]["recovered_completions"] == 1
    Dispatcher(lambda _: pytest.fail("validated cell reran"), validate, lambda _: None).dispatch(journal)


@pytest.mark.parametrize("change", [
    {"failure_class": "agent_exception"}, {"failure_class": "unknown_crash"},
    {"failure_class": "timeout"}, {"failure_class": "resource_exhaustion"},
    {"origin": "worker"}, {"before_completion": False}, {"completion_known_absent": False},
    {"original_stopped_or_fenced": False}, {"semantic_integrity_failed": True},
    {"attempt": 2}, {"binding_digest": "changed"}, {"cell_identity": "changed"},
    {"before_completion": 1},
])
def test_all_nonqualifying_evidence_fails_closed(tmp_path, change):
    journal = make(tmp_path)
    journal.start()
    with pytest.raises(IntegrityError):
        journal.approve_recovery(replace(evidence(journal), **change))
    assert not any(e["kind"] == "recovery_eligible" for e in journal.events())


def test_completed_corrupt_evidence_and_outcome_fields_prohibit_retry(tmp_path):
    journal = make(tmp_path)
    path = journal.start()
    (path / "result.json").write_bytes(b"corrupt authoritative evidence")
    with pytest.raises(IntegrityError):
        journal.approve_recovery(evidence(journal))
    proof = path / "bad-supervisor.json"
    write_once(proof, {**asdict(evidence(journal)), "winner": "A"})
    with pytest.raises(IntegrityError):
        RecoveryEvidence.read(proof)


def test_recovery_exhaustion_never_allows_third_attempt(tmp_path):
    journal = make(tmp_path)
    dispatcher = Dispatcher(lambda _: (_ for _ in ()).throw(WorkerInterrupted()), validate, evidence)
    with pytest.raises(IntegrityError, match="exhausted"):
        dispatcher.dispatch(journal)
    with pytest.raises(IntegrityError):
        dispatcher.dispatch(journal)
    assert sum(e["kind"] == "started" for e in journal.events()) == 2


def test_durable_eligibility_crash_resume_and_original_retention(tmp_path):
    journal = make(tmp_path)
    path = journal.start()
    write_once(path / "partial.json", {"partial": 1})
    journal.approve_recovery(evidence(journal))
    resumed = make(tmp_path)
    Dispatcher(finish, validate, lambda _: pytest.fail("eligibility was already durable")).dispatch(resumed)
    (path / "partial.json").write_bytes(b"overwritten")
    with pytest.raises(IntegrityError):
        resumed.validate_attempts()


def test_late_original_completion_and_noninfra_errors_and_bad_validation(tmp_path):
    journal = make(tmp_path / "late")
    journal.start()
    journal.approve_recovery(evidence(journal))
    second = journal.start(recovery=True)
    finish(second)
    write_once(journal.root / "attempt-01/result.json", {"late": True})
    with pytest.raises(IntegrityError):
        journal.complete(2)
    for name, backend, validator in (("semantic", lambda _: (_ for _ in ()).throw(ValueError()), validate),
                                    ("corrupt", finish, lambda _: (_ for _ in ()).throw(IntegrityError()))):
        failed = make(tmp_path / name)
        with pytest.raises(IntegrityError):
            Dispatcher(backend, validator, lambda _: pytest.fail("noninfra requested recovery")).dispatch(failed)
        assert sum(e["kind"] == "started" for e in failed.events()) == 1


def test_missing_ledger_and_binding_changes_and_unstarted_resume(tmp_path):
    journal = make(tmp_path)
    (journal.root / "attempt-01").mkdir()
    Dispatcher(finish, validate, lambda _: None).dispatch(journal)
    with pytest.raises(IntegrityError):
        Journal(tmp_path, journal.cell, {"synthetic": "changed"})
    (journal.root / "events/000001.json").unlink()
    with pytest.raises(IntegrityError):
        journal.events()


def test_freeze_alone_never_unlocks_payoff_execution():
    with pytest.raises(ExecutionLocked):
        require_execution_approval(None, protocol_id="frozen", instrument_digest="qualified", seed_commitment="committed")


@pytest.mark.parametrize("marker", ["worker-completion.json", "semantic-integrity-failure.json"])
def test_independent_completion_or_integrity_markers_override_infrastructure_proof(tmp_path, marker):
    journal = make(tmp_path)
    path = journal.start()
    write_once(path / marker, {"marked": True})
    with pytest.raises(IntegrityError):
        journal.approve_recovery(evidence(journal))


def test_late_partial_or_completion_after_durable_eligibility_blocks_redispatch(tmp_path):
    journal = make(tmp_path)
    original = journal.start()
    journal.approve_recovery(evidence(journal))
    write_once(original / "late-artifact.json", {"late": True})
    with pytest.raises(IntegrityError):
        journal.start(recovery=True)
    assert sum(e["kind"] == "started" for e in journal.events()) == 1
