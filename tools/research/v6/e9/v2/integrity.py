"""Outcome-blind historical-integrity dispositions and append-only controls.

Scientific numbers never enter these functions. Actual accepted-position
equality, actual in-scope use and trustworthy strict temporal order are separate
requirements; incomplete proof stays on hold.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .authority import AuthorityLog
from .inventory import strict_private_json, values_checked
from .records import (
    IntegrityError,
    canonical_bytes,
    make_record,
    record_ref,
    sha256,
    validate_artifact_ref,
)

STAGES = ("BEFORE_GENERATION", "PARTIAL_GENERATION", "GENERATED", "COMMITMENT_PUBLIC",
          "COLLECTION", "COLLECTED", "FINAL_PUBLIC")
FINDINGS = ("OVERLAP", "SUSPICION", "DISPROVED", "NEW_HISTORY", "POST_BOUNDARY",
            "PLANNED_REUSE", "UNRESOLVED_CLOSE")
# PG-R7 release without new pre-boundary history: conclusive disproval or
# post-boundary-only first use. The retained receipt carries this evidence ID.
RELEASABLE = ("DISPROVED", "POST_BOUNDARY")
DISPOSITION_RECEIPT_ID = "INDEPENDENT-DISPOSITION-RECEIPT"


def adjudicate(stage: str, *, finding: str, first_cell_started: bool = False,
               prefix_overlap: bool = False, all_new_values_in_original_K: bool = False,
               original_bindings_valid: bool = True) -> dict:
    if stage not in STAGES or finding not in FINDINGS:
        raise IntegrityError("unknown historical integrity stage/finding")
    if any(type(value) is not bool for value in (first_cell_started, prefix_overlap,
            all_new_values_in_original_K, original_bindings_valid)):
        raise IntegrityError("explicit integrity booleans required")
    started = first_cell_started or STAGES.index(stage) >= STAGES.index("COLLECTION")
    if started and stage in {"BEFORE_GENERATION", "PARTIAL_GENERATION"}:
        raise IntegrityError("impossible accepted-prefix/first-cell stage")
    result = {"stage": stage, "finding": finding, "effective_status": "INTACT",
              "result_status": "NOT PRODUCED" if not started else "PENDING",
              "terminal": False, "continuation_required": False,
              "historical_completeness": "NOT ESTABLISHED", "Requirement_C": "NOT ESTABLISHED",
              "promotion_eligible": False, "correction_required": False,
              "stop_all_consumers": False, "first_cell_started": started}
    if finding in {"POST_BOUNDARY", "PLANNED_REUSE"}:
        result["effective_status"] = "SEPARATE_FUTURE_INVENTORY_HISTORY" if (
            finding == "POST_BOUNDARY") else "PLANNED_PAIRED_REUSE"
        return result
    if not original_bindings_valid:
        finding = "SUSPICION" if finding != "UNRESOLVED_CLOSE" else finding
        result["finding"] = finding
    if finding == "SUSPICION":
        result.update(effective_status="INTEGRITY_HOLD_PENDING_ADJUDICATION",
                      continuation_required=True, stop_all_consumers=True,
                      correction_required=stage == "FINAL_PUBLIC")
        return result
    if stage == "BEFORE_GENERATION":
        result.update(effective_status="INVENTORY_GATE_REOPENED", stop_all_consumers=True)
        return result
    reason = None
    if finding == "OVERLAP" or (finding == "NEW_HISTORY" and prefix_overlap):
        reason = "HISTORICAL_OVERLAP"
    elif finding == "UNRESOLVED_CLOSE":
        reason = "UNRESOLVED_INTEGRITY"
    elif (finding == "NEW_HISTORY" and stage == "PARTIAL_GENERATION"
          and not all_new_values_in_original_K):
        reason = "LATE_HISTORY_OUTSIDE_APPROVED_K"
    if reason is not None:
        if started:
            effective = "NOT EVALUABLE"
            if stage == "FINAL_PUBLIC":
                effective = "INVALIDATED_HISTORICAL_OVERLAP" if reason == "HISTORICAL_OVERLAP" else (
                    "INVALIDATED_UNRESOLVED_HISTORICAL_INTEGRITY")
            result.update(effective_status=effective, result_status="NOT EVALUABLE",
                          terminal=True, stop_all_consumers=True,
                          correction_required=stage == "FINAL_PUBLIC", reason=reason)
        else:
            result.update(effective_status="CANCELLED_PRECOLLECTION_" + reason,
                          result_status="NOT PRODUCED", terminal=True,
                          stop_all_consumers=True, reason=reason)
        return result
    if finding in {"DISPROVED", "NEW_HISTORY"}:
        result.update(effective_status="VERIFIED_NO_OVERLAP_PENDING_LEAD_CONTINUATION",
                      continuation_required=True, stop_all_consumers=True,
                      correction_required=stage == "FINAL_PUBLIC")
    return result


@dataclass(frozen=True)
class HistoryReceipt:
    disposition: str
    values: tuple[str, ...]
    intersection: tuple[str, ...]
    all_values_in_original_K: bool
    evidence_digests: tuple[str, ...]
    receipt_digest: str
    accepted_digest: str
    original_K_digest: str
    boundary_digest: str
    verifier_id: str
    post_boundary_values: tuple[str, ...]
    disproved_values: tuple[str, ...]


def verify_history(*, accepted_raw: bytes, original_K_raw: bytes,
                   history_inputs: list[bytes], boundary_digest: str,
                   verifier_id: str, producer_id: str,
                   execution_inputs: dict[str, bytes] | None = None) -> HistoryReceipt:
    """Reproduce an independently supplied private actual-use checklist.

    Each proof binds exact uint64 values, execution evidence and strict boundary
    order. The proof shape makes source-only defaults and uncertain timestamps
    incapable of establishing non-overlap: a false or unverified field is
    uncertainty, and only an explicit ``disproval`` statement corroborated by the
    authoritative execution receipt is conclusive. Authenticity of authoritative
    execution receipts belongs to the independent evidence inspection boundary.
    """
    if not verifier_id or verifier_id == producer_id or not history_inputs:
        raise IntegrityError("independent complete history inspection required")
    accepted_rows = strict_private_json(accepted_raw)
    if not isinstance(accepted_rows, list):
        raise IntegrityError("ordered accepted positions required")
    accepted = []
    for index, position in enumerate(accepted_rows, 1):
        if (not isinstance(position, dict) or set(position) != {"position", "value_hex"}
                or type(position["position"]) is not int or position["position"] != index):
            raise IntegrityError("accepted-position order mismatch")
        accepted.append(position["value_hex"])
    values_checked(accepted)
    K = set(values_checked(strict_private_json(original_K_raw)))
    history: set[str] = set()
    post_boundary: set[str] = set()
    disproved: set[str] = set()
    uncertain = False
    expected = {"values", "actual_execution", "scope_verified", "temporal_order",
                "generation_boundary_digest", "execution_evidence"}
    for raw in history_inputs:
        proof = strict_private_json(raw)
        if (not isinstance(proof, dict) or not expected <= proof.keys()
                or proof.keys() - expected - {"disproval"}):
            raise IntegrityError("unknown/missing private history proof fields")
        values = values_checked(proof["values"])
        execution_ref = proof["execution_evidence"]
        validate_artifact_ref(execution_ref)
        execution_raw = (execution_inputs or {}).get(execution_ref["evidence_id"])
        if (not isinstance(execution_raw, bytes) or len(execution_raw) != execution_ref["bytes"]
                or sha256(execution_raw) != execution_ref["sha256_raw"]):
            raise IntegrityError("complete actual execution evidence was not read back")
        execution = strict_private_json(execution_raw)
        if not isinstance(execution, dict) or set(execution) != {
            "executed_values", "started", "scope", "temporal_order", "generation_boundary_digest"
        }:
            raise IntegrityError("unsupported/unreproduced authoritative execution receipt")
        if (values_checked(execution["executed_values"]) != values
                or execution["generation_boundary_digest"] != boundary_digest
                or execution["temporal_order"] != proof["temporal_order"]):
            raise IntegrityError("actual-use equality/temporal receipt differs from historical proof")
        if proof["generation_boundary_digest"] != boundary_digest:
            raise IntegrityError("history proof has wrong generation boundary")
        if proof["temporal_order"] not in {"BEFORE", "AFTER", "SIMULTANEOUS", "UNKNOWN"}:
            raise IntegrityError("unknown temporal proof")
        if "disproval" in proof:
            # Conclusive only when the read-back authoritative receipt says so too.
            supported = {
                "NOT_EXECUTED": proof["actual_execution"] is False and execution["started"] is False,
                "OUT_OF_SCOPE": proof["scope_verified"] is True and execution["scope"] == "OUT_OF_SCOPE",
            }.get(proof["disproval"]) if isinstance(proof["disproval"], str) else None
            if supported is not True:
                raise IntegrityError("disproval is not corroborated by the authoritative execution receipt")
            disproved.update(values)
        elif (proof["actual_execution"] is not True or execution["started"] is not True
                or proof["scope_verified"] is not True or execution["scope"] != "IN_SCOPE"
                or proof["temporal_order"] in {"SIMULTANEOUS", "UNKNOWN"}):
            uncertain = True
        elif proof["temporal_order"] == "BEFORE":
            history.update(values)
        else:
            post_boundary.update(values)
    intersection = tuple(sorted(set(accepted) & history))
    # PG-R5/R6: proven overlap terminates even when other evidence is uncertain.
    if intersection:
        disposition = "OVERLAP"
    elif uncertain:
        disposition = "SUSPICION"
    elif history:
        disposition = "NEW_HISTORY"
    elif post_boundary:
        disposition = "POST_BOUNDARY"
    else:
        disposition = "DISPROVED"
    body = {"disposition": disposition, "values": sorted(history),
            "intersection": list(intersection), "all_values_in_original_K": history <= K,
            "evidence_digests": [sha256(raw) for raw in history_inputs],
            "accepted_digest": sha256(accepted_raw), "original_K_digest": sha256(original_K_raw),
            "boundary_digest": boundary_digest, "verifier_id": verifier_id,
            "post_boundary_values": sorted(post_boundary - history),
            "disproved_values": sorted(disproved - history - post_boundary)}
    return HistoryReceipt(disposition, tuple(sorted(history)), intersection, history <= K,
                          tuple(body["evidence_digests"]), sha256(canonical_bytes(body)),
                          body["accepted_digest"], body["original_K_digest"], boundary_digest,
                          verifier_id, tuple(body["post_boundary_values"]),
                          tuple(body["disproved_values"]))


def verify_prefix_snapshot(snapshot: dict, *, prefix_raw: bytes, audit_raw: bytes,
                           original_K_raw: bytes, boundary_digest: str) -> None:
    """Rebuild prefix, audit positions, rejection decisions and complete chain."""
    body = snapshot["body"]
    ref = body["ordered_prefix"]
    if ref["sha256_raw"] != sha256(prefix_raw) or ref["bytes"] != len(prefix_raw):
        raise IntegrityError("prefix raw binding mismatch")
    positions = strict_private_json(prefix_raw)
    audit = strict_private_json(audit_raw)
    K = set(values_checked(strict_private_json(original_K_raw)))
    accepted: list[str] = []
    tip, last_acceptance = boundary_digest, None
    for ordinal, entry in enumerate(audit, 1):
        if (entry["prior_entry_digest"] != tip or entry["raw_draw_ordinal"] != ordinal
                or type(entry["raw_draw_ordinal"]) is not int):
            raise IntegrityError("prefix raw audit chain/ordinal mismatch")
        value = values_checked([entry["raw_bytes_hex"]])[0]
        decision = "REJECT_K" if value in K else (
            "REJECT_DUPLICATE" if value in accepted else "ACCEPT")
        if (entry["disposition"] != decision or entry["accepted_position"] != (
                len(accepted) + 1 if decision == "ACCEPT" else None)
                or entry["accepted_position"] is not None and type(entry["accepted_position"]) is not int):
            raise IntegrityError("prefix acceptance/rejection mismatch")
        if decision == "ACCEPT":
            accepted.append(value)
            last_acceptance = ordinal
        tip = sha256(canonical_bytes(entry))
    expected_positions = [{"position": i, "value_hex": value}
                          for i, value in enumerate(accepted, 1)]
    if (positions != expected_positions or len(accepted) >= 1412
            or any(type(row["position"]) is not int for row in positions)
            or type(body["accepted_count"]) is not int or type(body["audit_position"]) is not int
            or body["accepted_count"] != len(accepted) or body["audit_position"] != len(audit)
            or body["last_acceptance_ordinal"] != last_acceptance or body["audit_tip"] != tip):
        raise IntegrityError("prefix count/order/audit/acceptance position mismatch")


class IntegrityController:
    """Transcribe verified outcome-blind findings into durable stop events."""
    def __init__(self, authority: AuthorityLog, *, verifier_actor: dict, lead_actor: dict,
                 ledger: Any = None):
        self.authority = authority
        self.verifier_actor, self.lead_actor = verifier_actor, lead_actor
        self.ledger = ledger  # durable dispatch attempt ledger, once dispatch can exist

    def _common(self, role: str, actor: dict, decision: str, dependencies: dict,
                evidence: list[dict] | None = None) -> dict:
        return {"record_role": role, "study_id": self.authority.study_id, "actor": actor,
                "decision": decision, "dependencies": dependencies, "evidence": evidence or []}

    def notice(self, stage: str, decision: dict, receipt: HistoryReceipt,
               event: dict, *, operation_id: str) -> dict:
        """J binds only actually existing S/C/F; the original published F is immutable."""
        originals = {r: ref for r, ref in self.authority.bindings.items() if r in {"S", "C", "F"}}
        self.authority.retain_record(event)
        receipt_ref = self.authority.retain_artifact(
            canonical_bytes(asdict(receipt)) + b"\n", "INDEPENDENT-HISTORY-RECEIPT")
        body = self._common("J", self.verifier_actor, "RECORDED",
                            {**originals, "AuthorityEvent": record_ref(event)}, [receipt_ref])
        # Active holds and terminal events withdraw eligibility; a release after verified
        # non-overlap is a disclosure bound to the immutable originals.
        withdrawn = event["body"]["event_kind"] in {"HOLD", "TERMINATE", "CORRECT"}
        body.update(adjudication=receipt_ref, authority_event=record_ref(event),
                    disposition=decision["effective_status"], immutable_original_F=originals.get("F"),
                    original_records=originals, stage=stage, withdrawn_eligibility=withdrawn)
        notice = make_record("J", body)
        self.authority.retain_record(notice)
        return notice

    def partial_supplement(self, *, generator: Any, snapshot: dict, prefix_raw: bytes,
                           audit_raw: bytes, original_K_raw: bytes,
                           history_inputs: list[bytes], execution_inputs: dict[str, bytes],
                           expected_tip: str, operation_id: str) -> dict:
        """Independently reproduce exact retained prefix before scoped continuation."""
        if (operation_id != generator.operation_id or generator.authority is not self.authority
                or self.verifier_actor["actor_id"] == generator.recorder["actor_id"]
                or self.authority.actors.get(self.verifier_actor["actor_id"]) not in {
                    "independent_verifier", "independent_integrity_verifier"}):
            raise IntegrityError("independent same-operation prefix verifier required")
        with self.authority.exclusive():
            state = self.authority._state()
            if state["tip"] != expected_tip or not state["held"] or state["terminal"]:
                raise IntegrityError("prefix verification requires active fenced hold")
            self.authority.source_check()
            for ref in self.authority.bindings.values():
                self.authority.resolve(ref)
        boundary = generator._boundary()
        if boundary is None or sha256(original_K_raw) != generator.inventory_refs["K"]["sha256_raw"]:
            raise IntegrityError("original boundary/K cannot be independently reproduced")
        verify_prefix_snapshot(snapshot, prefix_raw=prefix_raw, audit_raw=audit_raw,
                               original_K_raw=original_K_raw, boundary_digest=boundary["digest"])
        if strict_private_json(audit_raw) != generator.read_audit()[0]:
            raise IntegrityError("prefix snapshot is not the producer's stopped audit state")
        receipt = verify_history(accepted_raw=prefix_raw, original_K_raw=original_K_raw,
                                 history_inputs=history_inputs, execution_inputs=execution_inputs,
                                 boundary_digest=boundary["digest"], verifier_id=self.verifier_actor["actor_id"],
                                 producer_id=generator.recorder["actor_id"])
        for index, raw in enumerate(history_inputs):
            self.authority.retain_artifact(raw, "HISTORY-" + str(index))
        for evidence_id, raw in execution_inputs.items():
            self.authority.retain_artifact(raw, evidence_id)
        self.authority.retain_artifact(prefix_raw, snapshot["body"]["ordered_prefix"]["evidence_id"])
        audit_ref = self.authority.retain_artifact(audit_raw, "PAUSED-RAW-AUDIT")
        self.authority.retain_record(boundary)
        self.authority.retain_record(snapshot)
        receipt_ref = self.authority.retain_artifact(canonical_bytes(asdict(receipt)) + b"\n",
                                                   "PREFIX-PRIOR-USE-SCOPE-TEMPORAL")
        membership_body = self._common("PrefixAndKVerification", self.verifier_actor,
                                       "PASS" if receipt.disposition != "SUSPICION" else "UNRESOLVED", {
            **self.authority.bindings, "PrefixSnapshot": record_ref(snapshot)})
        membership_body.update(accepted_prefix_intersection={"count": len(receipt.intersection),
                                                             "receipt": receipt_ref},
                               all_new_values_in_original_K=receipt.all_values_in_original_K,
                               original_bindings_valid=True, prior_use_scope_temporal_receipt=receipt_ref)
        membership = make_record("PrefixAndKVerification", membership_body)
        self.authority.retain_record(membership)
        from .inventory import frozen_limitations
        gaps, dependencies = frozen_limitations()
        hold_path = self.authority.root / f"event-{state['sequence']:08d}.json"
        event = strict_private_json(hold_path.read_bytes())
        self.authority.retain_record(event)
        evidence_refs = [self.authority.retain_artifact(raw, "HISTORY-" + str(i))
                         for i, raw in enumerate(history_inputs)]
        supplement_body = self._common("PartialGenerationSupplement", generator.recorder, "RECORDED", {
            **self.authority.bindings, "GenerationBoundary": record_ref(boundary),
            "PrefixSnapshot": record_ref(snapshot), "PrefixAndKVerification": record_ref(membership),
            "AuthorityEvent": record_ref(event)}, [audit_ref, receipt_ref])
        supplement_body.update(membership_receipt=record_ref(membership), new_evidence=evidence_refs,
                               prefix_count_and_audit_position={"accepted_count": snapshot["body"]["accepted_count"],
                                                                "audit_position": snapshot["body"]["audit_position"],
                                                                "audit_tip": snapshot["body"]["audit_tip"]},
                               still_incomplete_scope={"gap_ids": gaps, "dependency_ids": dependencies,
                                                       "historical_completeness": "NOT ESTABLISHED"},
                               stop_fencing_evidence=snapshot["body"]["stop_fencing_evidence"])
        supplement = make_record("PartialGenerationSupplement", supplement_body)
        self.authority.retain_record(supplement)
        decision = adjudicate("PARTIAL_GENERATION", finding=receipt.disposition,
                              prefix_overlap=bool(receipt.intersection),
                              all_new_values_in_original_K=receipt.all_values_in_original_K)
        if decision["terminal"]:
            terminal = self.record("PARTIAL_GENERATION", receipt, expected_tip=expected_tip,
                                   operation_id=operation_id, evidence=[receipt_ref, audit_ref])
        else:
            terminal = None
        return {"receipt": receipt, "membership": membership, "supplement": supplement,
                "decision": decision, "terminal": terminal}

    def completed_supplement(self, stage: str, *, accepted_raw: bytes,
                             original_K_raw: bytes, history_inputs: list[bytes],
                             execution_inputs: dict[str, bytes], generation_boundary: dict,
                             expected_tip: str, producer_id: str,
                             inspection_boundary: str) -> dict:
        """Full-list verification after generation; original payload bytes retained."""
        if stage not in {"GENERATED", "COMMITMENT_PUBLIC", "COLLECTION", "COLLECTED", "FINAL_PUBLIC"}:
            raise IntegrityError("completed payload supplement requires completed generation")
        positions = strict_private_json(accepted_raw)
        if not isinstance(positions, list) or len(positions) != 1412:
            raise IntegrityError("completed supplement requires independent all-1412 readback")
        with self.authority.exclusive():
            state = self.authority._state()
            if state["tip"] != expected_tip or not state["held"] or state["terminal"]:
                raise IntegrityError("completed history verification requires active hold")
            self.authority.source_check()
        S_ref = self.authority.bindings.get("S")
        if S_ref is None:
            raise IntegrityError("completed supplement requires existing immutable S")
        S = self.authority.resolve(S_ref)["body"]
        payload_raw = self.authority.read_artifact(S["payload"])
        payload = strict_private_json(payload_raw)["body"]
        original = self.authority.resolve(self.authority.bindings["O"])["body"]
        if (canonical_bytes(payload["positions"]) + b"\n" != accepted_raw
                or payload["generation_boundary"] != record_ref(generation_boundary)
                or payload["inventory_refs"] != {key: original[key] for key in ("K", "E", "L")}
                or sha256(original_K_raw) != original["K"]["sha256_raw"]):
            raise IntegrityError("completed history proof does not bind immutable original payload/K")
        from .commitment import commitment_value
        computed_c = commitment_value(payload_raw, self.authority.read_artifact(S["salt"]))
        for role in ("W", "U", "C"):
            if role in self.authority.bindings and self.authority.resolve(
                    self.authority.bindings[role])["body"]["commitment"] != computed_c:
                raise IntegrityError("completed supplement primitive c original binding drift")
        receipt = verify_history(accepted_raw=accepted_raw, original_K_raw=original_K_raw,
                                 history_inputs=history_inputs, execution_inputs=execution_inputs,
                                 boundary_digest=generation_boundary["digest"],
                                 verifier_id=self.verifier_actor["actor_id"], producer_id=producer_id)
        if receipt.disposition != "NEW_HISTORY" or receipt.intersection:
            raise IntegrityError("completed supplement is not independent full-list non-overlap")
        receipt_ref = self.authority.retain_artifact(canonical_bytes(asdict(receipt)) + b"\n",
                                                   "FULL-LIST-NON-OVERLAP")
        evidence_refs = [self.authority.retain_artifact(raw, "COMPLETED-HISTORY-" + str(i))
                         for i, raw in enumerate(history_inputs)]
        for evidence_id, raw in execution_inputs.items():
            self.authority.retain_artifact(raw, evidence_id)
        hold_path = self.authority.root / f"event-{state['sequence']:08d}.json"
        hold = strict_private_json(hold_path.read_bytes())
        self.authority.retain_record(hold)
        stage_refs = dict(self.authority.bindings)
        body = self._common("CompletedMembershipSupplement", self.verifier_actor, "PASS", {
            **stage_refs, "AuthorityEvent": record_ref(hold)}, [receipt_ref, *evidence_refs])
        body.update(independent_full_list_non_overlap_receipt=receipt_ref,
                    original_K_E_L_payload_commitment_unchanged=True,
                    updated_inspection_boundary={"scope": inspection_boundary, "stage": stage,
                                                 "historical_completeness": "NOT ESTABLISHED"})
        supplement = make_record("CompletedMembershipSupplement", body)
        self.authority.retain_record(supplement)
        return {"receipt": receipt, "supplement": supplement,
                "decision": adjudicate(stage, finding="NEW_HISTORY")}

    def verify_disposition(self, stage: str, *, accepted_raw: bytes, original_K_raw: bytes,
                           history_inputs: list[bytes], execution_inputs: dict[str, bytes],
                           boundary_digest: str, expected_tip: str, producer_id: str,
                           generator: Any = None, snapshot: dict | None = None) -> dict:
        """Independent adjudication under the exact active hold; raw inputs retained.

        During partial generation the accepted list is the producer's sealed stopped
        prefix, independently reproduced against its current raw audit.
        """
        if stage not in STAGES or stage == "BEFORE_GENERATION":
            raise IntegrityError("adjudication of accepted positions requires a generation boundary")
        if (self.authority.actors.get(self.verifier_actor["actor_id"]) not in {
                "independent_verifier", "independent_integrity_verifier"}
                or self.verifier_actor["actor_id"] in {producer_id, self.lead_actor["actor_id"]}):
            raise IntegrityError("independent accountable integrity verifier required")
        partial = stage == "PARTIAL_GENERATION"
        if partial != (generator is not None and snapshot is not None):
            raise IntegrityError("partial-generation adjudication binds the producer's sealed stop state")
        with self.authority.exclusive():
            state = self.authority._state()
            if state["tip"] != expected_tip or not state["held"] or state["terminal"]:
                raise IntegrityError("adjudication requires the exact active hold")
            self.authority.source_check()
        if partial:
            boundary = generator._boundary()
            if (generator.authority is not self.authority or boundary is None
                    or boundary["digest"] != boundary_digest
                    or generator.recorder["actor_id"] != producer_id):
                raise IntegrityError("prefix adjudication requires the original paused producer")
            audit = generator.read_audit()[0]
            verify_prefix_snapshot(snapshot, prefix_raw=accepted_raw, audit_raw=canonical_bytes(audit) + b"\n",
                                   original_K_raw=original_K_raw, boundary_digest=boundary_digest)
            self.authority.retain_record(boundary)
            self.authority.retain_record(snapshot)
            self.authority.retain_artifact(accepted_raw, snapshot["body"]["ordered_prefix"]["evidence_id"])
        receipt = verify_history(accepted_raw=accepted_raw, original_K_raw=original_K_raw,
                                 history_inputs=history_inputs, execution_inputs=execution_inputs,
                                 boundary_digest=boundary_digest,
                                 verifier_id=self.verifier_actor["actor_id"], producer_id=producer_id)
        inputs = [self.authority.retain_artifact(raw, "DISPOSITION-HISTORY-" + str(index))
                  for index, raw in enumerate(history_inputs)]
        inputs += [self.authority.retain_artifact(raw, evidence_id)
                   for evidence_id, raw in execution_inputs.items()]
        receipt_ref = self.authority.retain_artifact(canonical_bytes(asdict(receipt)) + b"\n",
                                                   DISPOSITION_RECEIPT_ID)
        decision = adjudicate(stage, finding=receipt.disposition,
                              prefix_overlap=bool(receipt.intersection),
                              all_new_values_in_original_K=receipt.all_values_in_original_K)
        return {"receipt": receipt, "evidence": [receipt_ref, *inputs], "decision": decision}

    def record(self, stage: str, receipt: HistoryReceipt, *, expected_tip: str,
               operation_id: str, evidence: list[dict], first_cell_started: bool = False,
               close_unresolved: bool = False, original_bindings_valid: bool = True) -> dict:
        finding = "UNRESOLVED_CLOSE" if close_unresolved else receipt.disposition
        if self.ledger is not None:
            first_cell_started = first_cell_started or self.ledger.first_cell_started()
        elif stage == "COMMITMENT_PUBLIC":
            raise IntegrityError("first-cell status must come from the durable attempt ledger")
        decision = adjudicate(stage, finding=finding, first_cell_started=first_cell_started,
                              prefix_overlap=bool(receipt.intersection),
                              all_new_values_in_original_K=receipt.all_values_in_original_K,
                              original_bindings_valid=original_bindings_valid)
        if decision["terminal"]:
            kind = "CORRECT" if stage == "FINAL_PUBLIC" else "TERMINATE"
            actor = self.lead_actor
        elif decision["stop_all_consumers"]:
            kind, actor = "HOLD", self.verifier_actor
        else:
            return {"decision": decision, "event": None}
        affected = [ref for role, ref in self.authority.bindings.items()
                    if role in {"G", "U", "D"}] if decision["terminal"] else []
        event = self.authority.append(kind, actor, expected_tip=expected_tip,
                                      operation_id=operation_id, affected=affected,
                                      evidence=evidence)
        notice = self.notice(stage, decision, receipt, event, operation_id=operation_id)
        return {"decision": decision, "event": event, "notice": notice}

    def release(self, stage: str, receipt: HistoryReceipt, *, expected_tip: str,
                operation_id: str, evidence: list[dict], original_bindings_valid: bool,
                supplement: dict | None = None, snapshot: dict | None = None,
                scope: str = "same-operation continuation") -> dict:
        """CONTINUE after verified new history (PG-R8 supplement) or RELEASE after
        conclusive disproval/post-boundary-only use (PG-R7; no new history, so the
        independent receipt and its raw inputs are bound instead of a supplement)."""
        releasable = receipt.disposition in RELEASABLE
        if receipt.disposition != "NEW_HISTORY" and not releasable:
            raise IntegrityError("independent non-overlap receipt required for release")
        if releasable and (receipt.values or receipt.intersection or stage == "BEFORE_GENERATION"):
            raise IntegrityError("release after disproval needs a boundary and no pre-boundary history")
        decision = adjudicate(stage, finding=receipt.disposition,
                              prefix_overlap=bool(receipt.intersection),
                              all_new_values_in_original_K=receipt.all_values_in_original_K,
                              original_bindings_valid=original_bindings_valid)
        if decision["terminal"] or not original_bindings_valid or not evidence:
            raise IntegrityError("cannot release terminal or unverifiable original tuple")
        if releasable:
            if supplement is not None or (stage == "PARTIAL_GENERATION") != (snapshot is not None):
                raise IntegrityError("disproval release binds the receipt and only a paused prefix snapshot")
        elif supplement is None:
            raise IntegrityError("lead release requires exact independent membership supplement")
        with self.authority.exclusive():
            state = self.authority._state()
            if state["tip"] != expected_tip or not state["held"]:
                raise IntegrityError("release must bind current held authority")
            event_path = self.authority.root / f"event-{state['sequence']:08d}.json"
            hold = strict_private_json(event_path.read_bytes())
        self.authority.retain_record(hold)
        dependencies = {**self.authority.bindings, "AuthorityEvent": record_ref(hold)}
        for bound in (supplement, snapshot):
            if bound is not None:
                self.authority.retain_record(bound)
                dependencies[bound["body"]["record_role"]] = record_ref(bound)
        kind = "RELEASE" if releasable else "CONTINUE"
        body = self._common("LeadContinuation", self.lead_actor, "AUTHORIZED", dependencies, evidence)
        body.update(disposition=kind, operation_id=operation_id, scope=scope,
                    still_incomplete_scope="Historical coverage remains NOT ESTABLISHED.",
                    unchanged_original_tuple=self.authority.bindings)
        lead = make_record("LeadContinuation", body)
        self.authority.retain_record(lead)
        lead_ref = self.authority.retain_artifact(canonical_bytes(lead) + b"\n", "LEAD-CONTINUATION")
        event = self.authority.append(kind, self.lead_actor, expected_tip=expected_tip,
                                      operation_id=operation_id, evidence=[*evidence, lead_ref],
                                      release_record=lead)
        notice = self.notice(stage, decision, receipt, event, operation_id=operation_id)
        return {"decision": decision, "lead_continuation": lead, "event": event, "notice": notice}
