"""Fenced worker launches and immutable per-cell attempts; no native runner import.

The injected launcher schedules work while the authority lock is held and returns
immediately. Completion arrives separately, so a hold can fence active workers.
"""
from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from .authority import AuthorityLog, Lease, durable_bytes
from .identities import dispatch_id, logical_cell_id
from .inventory import artifact, strict_private_json
from .records import P_ID, IntegrityError, canonical_bytes, sha256, validate_artifact_ref
from .scientific import recovery_eligible

ARTIFACT_NAMES = {"result.json", "replay.jsonl", "trace.jsonl", "diagnostic.json"}


class DispatchLedger:
    def __init__(self, root: Path, authority: AuthorityLog):
        self.root, self.authority = Path(root), authority
        self.root.mkdir(parents=True, exist_ok=True)

    def _attempts(self, cell_id: str) -> list[dict]:
        entries = []
        for ordinal, path in enumerate(sorted((self.root / cell_id).glob("attempt-*.json")), 1):
            if path.name != f"attempt-{ordinal}.json" or ordinal > 2:
                raise IntegrityError("dispatch attempt gap or retry-cap failure")
            item = strict_private_json(path.read_bytes())
            if (item["attempt"] != ordinal or item["cell_identity"] != cell_id
                    or item["study_id"] != self.authority.study_id):
                raise IntegrityError("dispatch ledger mixed cell/study/attempt")
            entries.append(item)
        return entries

    def start(self, row: str, opponent: str, position: int, seat: str, *,
              expected_tip: str, operation_id: str,
              launch: Callable[[dict, Lease], Any],
              retry_facts: dict | None = None, failure_receipt: dict | None = None) -> dict:
        cell_id = logical_cell_id(P_ID, row, opponent, position, seat)
        operation = "infrastructure_retry" if retry_facts is not None else "worker_start"

        def schedule(lease: Lease) -> dict:
            if (self.root / cell_id / "unusable.json").exists():
                raise IntegrityError("seed block unusable after a conflicting completion")
            attempts = self._attempts(cell_id)
            ordinal = len(attempts) + 1
            if ordinal > 2 or (ordinal == 2) != (retry_facts is not None):
                raise IntegrityError("original attempt or sole retry already started")
            binding = sha256(canonical_bytes(self.authority.bindings))
            if ordinal == 2:
                original = attempts[0]
                if original["binding_digest"] != binding:
                    raise IntegrityError("retry requires exact original cell inputs/source tuple")
                if (self.root / cell_id / "completion-1.json").exists():
                    raise IntegrityError("terminal completion prohibits recovery")
                proof_path = self.root / cell_id / "failure-1.json"
                if failure_receipt is None or not proof_path.exists():
                    raise IntegrityError("independently recorded infrastructure failure required")
                proof_raw = proof_path.read_bytes()
                validate_artifact_ref(failure_receipt)
                if (failure_receipt["sha256_raw"] != sha256(proof_raw)
                        or failure_receipt["bytes"] != len(proof_raw)
                        or strict_private_json(proof_raw)["facts"] != retry_facts):
                    raise IntegrityError("recovery failure receipt changed")
                if not recovery_eligible(retry_facts, cell_identity=cell_id, binding_digest=binding):
                    raise IntegrityError("recovery fails frozen outcome-blind conditions")
            dispatch = dispatch_id(self.authority.study_id, self.authority.bindings["P"]["digest"],
                                   self.authority.bindings["I"]["digest"], cell_id, ordinal)
            item = {"study_id": self.authority.study_id, "cell_identity": cell_id,
                    "cell": {"row": row, "opponent": opponent, "position": position, "seat": seat},
                    "attempt": ordinal, "dispatch_identity": dispatch, "binding_digest": binding,
                    "binding_tuple": self.authority.bindings, "authority_tip": lease.authority_tip,
                    "fence_epoch": lease.epoch, "operation_id": operation_id,
                    "first_started_attempt_counts_as_collection": True}
            durable_bytes(self.root / cell_id / f"attempt-{ordinal}.json",
                          canonical_bytes(item) + b"\n")
            # Launch failures leave the started attempt intact; they are not auto-retried.
            launch(item, lease)
            return {"attempt": item, "lease": lease}

        return self.authority.protected(operation, expected_tip=expected_tip,
                                        operation_id=operation_id, action=schedule)

    def record_failure(self, cell_id: str, facts: dict, *, supervisor: dict,
                       evidence_raw: bytes, evidence_ref: dict) -> dict:
        """Retain explicit external failure facts; no payoff fields are accepted."""
        with self.authority.exclusive():
            attempts = self._attempts(cell_id)
            if not attempts or len(attempts) != 1:
                raise IntegrityError("first started attempt required before recovery")
            if (supervisor.get("role") != "external_supervisor"
                    or self.authority.actors.get(supervisor.get("actor_id")) != "external_supervisor"):
                raise IntegrityError("external infrastructure supervisor authority required")
            validate_artifact_ref(evidence_ref)
            if (sha256(evidence_raw) != evidence_ref["sha256_raw"]
                    or len(evidence_raw) != evidence_ref["bytes"]):
                raise IntegrityError("complete supervisor evidence readback required")
            proof_input = strict_private_json(evidence_raw)
            if proof_input != {"facts": facts, "supervisor_id": supervisor["actor_id"]}:
                raise IntegrityError("supervisor evidence does not reproduce exact failure facts")
            if not recovery_eligible(facts, cell_identity=cell_id,
                                     binding_digest=attempts[0]["binding_digest"]):
                raise IntegrityError("semantic/outcome/unknown failure cannot authorize retry")
            if (self.root / cell_id / "completion-1.json").exists():
                raise IntegrityError("completed first attempt cannot be retried")
            proof = {"facts": facts, "supervisor": supervisor, "evidence": evidence_ref}
            path = self.root / cell_id / "failure-1.json"
            durable_bytes(path, canonical_bytes(proof) + b"\n")
            return artifact(path.read_bytes(), "FAILURE-" + cell_id)

    def complete(self, cell_id: str, attempt: int, lease: Lease, *,
                 artifacts: dict[str, bytes]) -> dict:
        """Retain every late/partial artifact; eligibility requires an active lease."""
        if (type(attempt) is not int or attempt not in (1, 2) or not artifacts
                or set(artifacts) - ARTIFACT_NAMES or any(type(v) is not bytes for v in artifacts.values())):
            raise IntegrityError("strict attempt and canonical named artifact bytes required")
        with self.authority.exclusive():
            attempts = self._attempts(cell_id)
            if len(attempts) < attempt:
                raise IntegrityError("artifact without a started attempt")
            original = attempts[attempt - 1]
            if (lease.study_id != original["study_id"] or lease.operation_id != original["operation_id"]
                    or lease.epoch != original["fence_epoch"] or lease.authority_tip != original["authority_tip"]):
                raise IntegrityError("artifact belongs to a different started worker lease")
            try:
                state = self.authority._state()
            except Exception:
                # Unavailable or malformed authority still retains arriving evidence.
                state = {"epoch": None, "held": True, "terminal": False, "active_bindings": None}
            late = (lease.epoch != state["epoch"] or state["held"] or state["terminal"]
                    or state["active_bindings"] != self.authority.bindings
                    or original["binding_tuple"] != self.authority.bindings
                    or attempt != len(attempts)
                    or (self.root / cell_id / f"failure-{attempt}.json").exists())
            try:
                self.authority.source_check()
            except Exception:
                # Source validation failures cannot discard the raw worker packet.
                late = True
            # Content-addressed retention: a repeated or conflicting packet is kept, never lost.
            for name, raw in artifacts.items():
                path = self.authority.root / "retained" / (
                    sha256(canonical_bytes([cell_id, attempt, name, sha256(raw)])) + ".bin")
                if not path.exists():
                    durable_bytes(path, raw)
                elif path.read_bytes() != raw:
                    raise IntegrityError("retained worker artifact collision")
            digests = {name: sha256(raw) for name, raw in artifacts.items()}
            cell_root = self.root / cell_id
            # Draft 3 recovery rule 1: only evidence of a completed terminal result is a
            # completion; an incomplete packet without it is a retained partial artifact.
            terminal = "result.json" in artifacts
            kind = "completion" if terminal else "partial"
            earlier = [strict_private_json(path.read_bytes())
                       for path in sorted(cell_root.glob(f"{kind}-{attempt}*.json"))]
            # Rules 4 and 8: output from an original attempt after its recorded failure or
            # its recovery start, or a different second completion of one attempt, makes
            # the seed block unusable.
            delivered = "completed" if terminal else "delivered output"
            conflict = None
            if attempt < len(attempts):
                conflict = f"original attempt {delivered} after recovery started"
            elif (cell_root / f"failure-{attempt}.json").exists():
                conflict = f"attempt {delivered} after its recorded infrastructure failure"
            elif terminal and any({n: r["sha256_raw"] for n, r in e["receipts"].items()} != digests
                                  for e in earlier):
                conflict = "conflicting second completion of one attempt"
            if conflict is not None and not (cell_root / "unusable.json").exists():
                durable_bytes(cell_root / "unusable.json", canonical_bytes(
                    {"cell_identity": cell_id, "attempt": attempt, "reason": conflict,
                     "artifact_digests": digests}) + b"\n")
            unusable = (cell_root / "unusable.json").exists()
            receipts = {name: {"sha256_raw": digests[name], "bytes": len(raw),
                               "late_fenced": late, "eligible": not late and not unusable,
                               "lease_epoch": lease.epoch, "active_epoch": state["epoch"]}
                        for name, raw in artifacts.items()}
            receipt = {"cell_identity": cell_id, "attempt": attempt, "receipts": receipts,
                       "eligible": set(artifacts) == ARTIFACT_NAMES and not late and not unusable}
            raw_receipt = canonical_bytes(receipt) + b"\n"
            # Identical artifact bytes re-delivered are already retained; no second receipt.
            if not any({n: r["sha256_raw"] for n, r in e["receipts"].items()} == digests for e in earlier):
                name = f"completion-{attempt}.json" if terminal and not earlier else (
                    f"{kind}-{attempt}-{sha256(raw_receipt)[:16]}.json")
                durable_bytes(cell_root / name, raw_receipt)
            return receipt

    def usable_completion(self, cell_id: str) -> dict:
        """The single eligible completion of the cell's final attempt, or fail closed."""
        with self.authority.exclusive():
            cell_root = self.root / cell_id
            if (cell_root / "unusable.json").exists():
                raise IntegrityError("seed block unusable; full registered result NOT EVALUABLE")
            attempts = self._attempts(cell_id)
            completions = [strict_private_json(path.read_bytes())
                           for path in sorted(cell_root.glob("completion-*.json"))]
            if (not attempts or len(completions) != 1 or not completions[0]["eligible"]
                    or completions[0]["attempt"] != len(attempts)):
                raise IntegrityError("cell lacks exactly one eligible completion of its final attempt")
            return completions[0]

    def first_cell_started(self) -> bool:
        """Any durably started attempt, including a failed one, starts collection."""
        return any(self.root.glob("*/attempt-*.json"))
