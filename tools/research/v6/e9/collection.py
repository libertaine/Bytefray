"""Durable, outcome-blind attempt accounting and automatic fixed-cap recovery.

The supervisor evidence is external to the policy/match worker. Ordinary
runtime exceptions and a missing file never manufacture infrastructure proof.
"""

from __future__ import annotations

import dataclasses
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .protocol import (
    Cell,
    ExecutionLocked,
    IntegrityError,
    canonical,
    digest,
    file_digest,
    read_json,
    write_once,
)

ALLOWLIST = frozenset({"host_worker_loss", "platform_eviction", "external_infrastructure_shutdown",
                      "storage_io_interruption"})


@dataclass(frozen=True)
class RecoveryEvidence:
    """The only facts available to the outcome-blind eligibility checker."""

    cell_identity: str
    binding_digest: str
    attempt: int
    origin: str
    failure_class: str
    before_completion: bool
    completion_known_absent: bool
    original_stopped_or_fenced: bool
    semantic_integrity_failed: bool

    def eligible(self, cell_identity: str, binding_digest: str) -> bool:
        predicates = (self.before_completion, self.completion_known_absent,
                      self.original_stopped_or_fenced, self.semantic_integrity_failed)
        return (all(type(value) is bool for value in predicates)
                and self.cell_identity == cell_identity and self.binding_digest == binding_digest
                and type(self.attempt) is int and self.attempt == 1
                and self.origin == "external-supervisor" and self.failure_class in ALLOWLIST
                and self.before_completion and self.completion_known_absent
                and self.original_stopped_or_fenced and not self.semantic_integrity_failed)

    @classmethod
    def read(cls, path: Path) -> RecoveryEvidence:
        payload = read_json(path)
        names = {field.name for field in dataclasses.fields(cls)}
        if set(payload) != names:
            raise IntegrityError("supervisor record has unregistered or outcome-bearing fields")
        for name in ("before_completion", "completion_known_absent", "original_stopped_or_fenced",
                     "semantic_integrity_failed"):
            if type(payload[name]) is not bool:
                raise IntegrityError("supervisor predicates must be explicit booleans")
        return cls(**payload)


class WorkerInterrupted(RuntimeError):
    """An external supervisor terminated/lost the worker, not an agent exception."""


class Journal:
    """Exclusive immutable event files form an append-only, hash-bound chain."""

    def __init__(self, root: Path, cell: Cell, binding: dict[str, Any]) -> None:
        self.cell = cell
        self.binding = digest(canonical(binding))
        self.root = root / cell.identity
        self.root.mkdir(parents=True, exist_ok=True)
        identity = {"cell": dataclasses.asdict(cell), "cell_identity": cell.identity,
                    "binding_digest": self.binding}
        identity_path = self.root / "identity.json"
        if identity_path.exists():
            if read_json(identity_path) != identity:
                raise IntegrityError("resume changed the cell/seed/configuration binding")
        else:
            write_once(identity_path, identity)
        self.events()

    def events(self) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        previous = None
        paths = sorted((self.root / "events").glob("*.json"))
        for index, path in enumerate(paths):
            event = read_json(path)
            if (path.name != f"{index:06d}.json" or event.get("sequence") != index
                    or event.get("previous_digest") != previous
                    or event.get("cell_identity") != self.cell.identity
                    or event.get("binding_digest") != self.binding):
                raise IntegrityError("attempt ledger is incomplete or inconsistent")
            previous = digest(path.read_bytes())
            out.append(event)
        starts = [event for event in out if event["kind"] == "started"]
        if [event["attempt"] for event in starts] != list(range(1, len(starts) + 1)):
            raise IntegrityError("attempt ordinals are not consecutive")
        if len(starts) > 2:
            raise IntegrityError("more than two started attempts")
        if len(starts) == 2:
            approvals = [e for e in out if e["kind"] == "recovery_eligible"]
            if len(approvals) != 1 or approvals[0]["sequence"] >= starts[1]["sequence"]:
                raise IntegrityError("second start lacks a durable prior recovery decision")
        completions = [event for event in out if event["kind"] == "completed"]
        if len(completions) > 1:
            raise IntegrityError("multiple authoritative completions for the same cell")
        state, active = "unstarted", 0
        for event in out:
            kind, attempt = event["kind"], event["attempt"]
            if type(attempt) is not int:
                raise IntegrityError("invalid attempt type")
            if kind == "started" and ((state == "unstarted" and attempt == 1)
                                      or (state == "eligible" and attempt == 2)):
                state, active = "started", attempt
            elif kind == "recovery_eligible" and state == "started" and active == attempt == 1:
                state = "eligible"
            elif kind == "completed" and state == "started" and active == attempt:
                state = "completed"
            elif kind == "validated" and state == "completed" and active == attempt:
                state = "validated"
            elif kind == "invalid" and state in ("started", "completed", "validated") and active == attempt:
                state = "invalid"
            else:
                raise IntegrityError("illegal attempt ledger transition")
        return out

    def append(self, kind: str, attempt: int, **facts: Any) -> None:
        events = self.events()
        previous = None if not events else digest(
            (self.root / "events" / f"{len(events)-1:06d}.json").read_bytes())
        event = {"sequence": len(events), "previous_digest": previous,
                 "cell_identity": self.cell.identity, "binding_digest": self.binding,
                 "kind": kind, "attempt": attempt, **facts}
        write_once(self.root / "events" / f"{len(events):06d}.json", event)

    def start(self, *, recovery: bool = False) -> Path:
        events = self.events()
        starts = [e for e in events if e["kind"] == "started"]
        if any(e["kind"] in ("completed", "invalid", "validated") for e in events):
            raise IntegrityError("completed or invalid evidence cannot be redispatched")
        if (not recovery and starts) or (recovery and len(starts) != 1):
            raise IntegrityError("invalid original/recovery start")
        if recovery and not any(e["kind"] == "recovery_eligible" for e in events):
            raise IntegrityError("automatic recovery lacks a durable eligibility decision")
        if recovery:
            self.check_recovery()
        attempt = len(starts) + 1
        path = self.root / f"attempt-{attempt:02d}"
        if path.exists():
            if any(path.iterdir()):
                raise IntegrityError("unrecorded attempt directory contains evidence")
        else:
            path.mkdir()
        self.append("started", attempt)
        return path

    def approve_recovery(self, evidence: RecoveryEvidence) -> None:
        events = self.events()
        starts = [e for e in events if e["kind"] == "started"]
        # Presence is deliberately conservative and reads no winner/score fields.
        completion_artifact = (any(self.root.glob("attempt-*/result.json"))
                               or any(self.root.glob("attempt-*/worker-completion.json")))
        integrity_failure = any(self.root.glob("attempt-*/semantic-integrity-failure.json"))
        if (len(starts) != 1 or completion_artifact or integrity_failure
                or any(e["kind"] in ("completed", "invalid", "validated", "recovery_eligible")
                       for e in events)
                or not evidence.eligible(self.cell.identity, self.binding)):
            raise IntegrityError("infrastructure recovery is not mechanically eligible")
        write_once(self.root / "attempt-01" / "supervisor-evidence.json", dataclasses.asdict(evidence))
        partial = {p.relative_to(self.root / "attempt-01").as_posix(): file_digest(p)
                   for p in sorted((self.root / "attempt-01").rglob("*")) if p.is_file()}
        self.append("recovery_eligible", 1,
                    supervisor_digest=digest(canonical(dataclasses.asdict(evidence))),
                    retained_artifact_digests=partial)

    def check_recovery(self) -> None:
        approval = next((e for e in self.events() if e["kind"] == "recovery_eligible"), None)
        if approval is None:
            raise IntegrityError("missing retained recovery approval")
        original = self.root / "attempt-01"
        proof = RecoveryEvidence.read(original / "supervisor-evidence.json")
        actual = {p.relative_to(original).as_posix(): file_digest(p)
                  for p in sorted(original.rglob("*")) if p.is_file()}
        if (not proof.eligible(self.cell.identity, self.binding)
                or digest(canonical(dataclasses.asdict(proof))) != approval["supervisor_digest"]
                or actual != approval["retained_artifact_digests"]):
            raise IntegrityError("retained original attempt/proof changed or completed late")

    def complete(self, attempt: int) -> None:
        if (any(e["kind"] == "completed" for e in self.events())
                or not (self.root / f"attempt-{attempt:02d}" / "result.json").is_file()
                or any((self.root / f"attempt-{i:02d}" / "result.json").exists()
                       for i in range(1, attempt))):
            raise IntegrityError("late/conflicting original completion")
        self.append("completed", attempt)

    def validate_attempts(self) -> tuple[Path, dict[str, int]]:
        events = self.events()
        starts = [e for e in events if e["kind"] == "started"]
        completed = [e for e in events if e["kind"] == "completed"]
        validated = [e for e in events if e["kind"] == "validated"]
        actual_results = list(self.root.glob("attempt-*/result.json"))
        if (len(completed) != 1 or len(validated) != 1 or len(actual_results) != 1
                or any(e["kind"] == "invalid" for e in events)
                or completed[0]["attempt"] != validated[0]["attempt"]):
            raise IntegrityError("cell does not have exactly one fully validated completion")
        attempt = completed[0]["attempt"]
        path = self.root / f"attempt-{attempt:02d}"
        if actual_results[0].parent != path:
            raise IntegrityError("result belongs to a different attempt")
        if len(starts) == 2:
            self.check_recovery()
        hashes = validated[0]["artifact_digests"]
        if set(hashes) != {"result.json", "replay.jsonl", "trace.jsonl", "diagnostic.json"}:
            raise IntegrityError("validated completion lacks the registered artifact inventory")
        if any(file_digest(path / name) != sha for name, sha in hashes.items()):
            raise IntegrityError("validated attempt artifacts changed")
        return path, {"started": len(starts), "completed": 1, "validated": 1,
                      "eligible_failures": int(len(starts) == 2),
                      "recovery_starts": int(len(starts) == 2),
                      "recovered_completions": int(len(starts) == 2)}


class Dispatcher:
    """Automatically retries every eligible interruption once; never selects outcomes."""

    def __init__(self, backend: Callable[[Path], None], validator: Callable[[Path], dict[str, str]],
                 supervisor: Callable[[Journal], RecoveryEvidence | None]) -> None:
        self.backend, self.validator, self.supervisor = backend, validator, supervisor

    def dispatch(self, journal: Journal) -> Path:
        events = journal.events()
        if any(e["kind"] == "validated" for e in events):
            return journal.validate_attempts()[0]
        if any(e["kind"] == "invalid" for e in events):
            raise IntegrityError("non-retryable failure; no replacement")
        completion = next((e for e in events if e["kind"] == "completed"), None)
        if completion is not None:
            attempt = completion["attempt"]
            path = journal.root / f"attempt-{attempt:02d}"
            try:
                hashes = self.validator(path)
                journal.append("validated", attempt, artifact_digests=hashes)
                return journal.validate_attempts()[0]
            except Exception:
                journal.append("invalid", attempt, reason="completed_evidence_validation_failed")
                raise IntegrityError("completed evidence is non-retryable") from None
        started = any(e["kind"] == "started" for e in events)
        if started:
            if any(e["kind"] == "recovery_eligible" for e in events):
                if sum(e["kind"] == "started" for e in events) != 1:
                    raise IntegrityError("registered recovery exhausted")
                journal.check_recovery()
            else:
                proof = self.supervisor(journal)
                if proof is None:
                    raise IntegrityError("interrupted started cell lacks infrastructure proof")
                journal.approve_recovery(proof)
        path = journal.start(recovery=started)
        while True:
            attempt = int(path.name.rsplit("-", 1)[1])
            try:
                self.backend(path)
            except WorkerInterrupted:
                if attempt != 1:
                    journal.append("invalid", attempt, reason="recovery_exhausted")
                    raise IntegrityError("registered recovery exhausted") from None
                proof = self.supervisor(journal)
                if proof is None:
                    journal.append("invalid", attempt, reason="no_external_infrastructure_proof")
                    raise IntegrityError("no qualified infrastructure proof") from None
                journal.approve_recovery(proof)
                path = journal.start(recovery=True)
                continue
            except Exception:
                journal.append("invalid", attempt, reason="non_infrastructure_worker_failure")
                raise IntegrityError("non-retryable collection failure") from None
            journal.complete(attempt)
            try:
                hashes = self.validator(path)
                journal.append("validated", attempt, artifact_digests=hashes)
                journal.validate_attempts()
            except Exception:
                journal.append("invalid", attempt, reason="completed_evidence_validation_failed")
                raise IntegrityError("completed evidence failed validation; no retry") from None
            return path


def require_execution_approval(path: Path | None, *, protocol_id: str,
                               instrument_digest: str, seed_commitment: str) -> None:
    if path is None:
        raise ExecutionLocked("payoff execution remains separately unauthorized")
    record = read_json(path)
    if record != {"schema": "bytefray.v6.e9.payoff_authorization", "version": 1,
                  "research_lead_authorized": True, "protocol_id": protocol_id,
                  "qualified_instrument_digest": instrument_digest,
                  "seed_commitment": seed_commitment}:
        raise ExecutionLocked("explicit authorization does not bind this qualified execution")
