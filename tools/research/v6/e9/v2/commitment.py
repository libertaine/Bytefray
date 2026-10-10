"""Complete private v2 payload/commitment and materialized-source verification."""

from __future__ import annotations

import base64
import re
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .generation import DOMAIN, N, entropy_declaration
from .integrity import (
    DISPOSITION_RECEIPT_ID,
    RELEASABLE,
    HistoryReceipt,
    verify_history,
    verify_prefix_snapshot,
)
from .inventory import strict_private_json, values_checked
from .records import (
    IntegrityError,
    canonical_bytes,
    record_ref,
    sha256,
    validate_artifact_ref,
    validate_record,
    write_once,
)

COMMITMENT_DOMAIN = b"bytefray-e9-seed-commitment-v2\n"


def commitment_value(payload_raw: bytes, salt_raw: bytes) -> str:
    if not isinstance(salt_raw, bytes) or len(salt_raw) != 32:
        raise IntegrityError("commitment salt must be exactly 32 bytes")
    strict_private_json(payload_raw)
    return sha256(COMMITMENT_DOMAIN + salt_raw + payload_raw)


def verify_complete_private(*, payload_raw: bytes, salt_raw: bytes, audit_raw: bytes,
                            original_K_raw: bytes, expected_bindings: dict,
                            inventory_refs: dict, operation_id: str,
                            generation_boundary: dict, expected_commitment: str,
                            authority_tips: list[str], preceding_chain_tip: str,
                            entropy_source: str,
                            supplemented_history: list[str] | None = None,
                            supplement_chain: list[dict] | None = None,
                            history_receipts: list[HistoryReceipt] | None = None,
                            artifact_reader: Callable[[dict], bytes] | None = None,
                            resolver: Callable[[dict], dict] | None = None,
                            active_chain_tip: str | None = None) -> dict:
    """Recompute every position and raw candidate, rather than endorse S/prefix.

    The operational caller must execute this complete verifier through the
    private_verification protected authority operation and resolve every ref.
    Deterministic qualification may supply explicitly synthetic records. The
    verifier states the entropy source it expects; the boundary must declare it.
    """
    payload = strict_private_json(payload_raw)
    validate_record(payload, resolver=resolver)
    if payload["schema"] != "bytefray.v6.e9.seed_payload" or payload["version"] != 2:
        raise IntegrityError("wrong private payload schema/version")
    body = payload["body"]
    if (body["N"] != N or type(body["N"]) is not int or body["domain"] != DOMAIN
            or body["dependencies"] != expected_bindings
            or body["inventory_refs"] != inventory_refs
            or body["operation_id"] != operation_id
            or body["study_id"] != generation_boundary["body"]["study_id"]
            or body["generation_boundary"] != record_ref(generation_boundary)
            or body["preceding_chain_tip"] != preceding_chain_tip):
        raise IntegrityError("payload domain/order/study/source/original operation binding mismatch")
    if (inventory_refs["K"]["sha256_raw"] != sha256(original_K_raw)
            or inventory_refs["K"]["bytes"] != len(original_K_raw)):
        raise IntegrityError("original K private-copy drift")
    producer = marker = None
    declared = []
    for ref in generation_boundary["body"]["evidence"]:
        if artifact_reader is None:
            raise IntegrityError("complete original producer/boundary fencing evidence reader required")
        raw = artifact_reader(ref)
        if len(raw) != ref["bytes"] or sha256(raw) != ref["sha256_raw"]:
            raise IntegrityError("original producer boundary evidence raw bytes changed")
        auxiliary = strict_private_json(raw)
        if auxiliary.get("kind") == "FIRST_RAW_BOUNDARY_V2":
            marker = auxiliary
        elif auxiliary.get("kind") == "ENTROPY_SOURCE_V2":
            declared.append(auxiliary)
        elif "producer_root" in auxiliary:
            producer = (ref, auxiliary)
    if declared != [entropy_declaration(entropy_source, study_id=body["study_id"],
                                        G=expected_bindings["G"], operation_id=operation_id)]:
        raise IntegrityError("generation boundary does not declare the expected entropy source")
    if producer is not None or marker is not None:
        if producer is None or marker is None:
            raise IntegrityError("incomplete original producer/first-raw fencing evidence")
        producer_ref, producer_body = producer
        if (producer_body["G"] != expected_bindings["G"]
                or producer_body["operation_id"] != operation_id
                or producer_body["study_id"] != body["study_id"]
                or producer_body["recorder"] != body["actor"]
                or producer_body["binding_tuple"] != expected_bindings
                or marker["G"] != expected_bindings["G"]
                or marker["study_id"] != body["study_id"]
                or marker["producer_registry"] != producer_ref):
            raise IntegrityError("private payload does not bind original root/recorder/operation/source")
    audit_ref = body["audit"]
    validate_artifact_ref(audit_ref)
    if (audit_ref["visibility"] != "PRIVATE" or audit_ref["bytes"] != len(audit_raw)
            or audit_ref["sha256_raw"] != sha256(audit_raw)):
        raise IntegrityError("complete private raw audit binding mismatch")
    positions = body["positions"]
    if not isinstance(positions, list) or len(positions) != N:
        raise IntegrityError("all 1412 ordered positions are mandatory")
    accepted: list[str] = []
    for index, position in enumerate(positions, 1):
        if (not isinstance(position, dict) or set(position) != {"position", "value_hex"}
                or type(position["position"]) is not int or position["position"] != index):
            raise IntegrityError("private positions must be contiguous accepted order")
        accepted.append(position["value_hex"])
    values_checked(accepted)
    K = set(values_checked(strict_private_json(original_K_raw)))
    history = set(values_checked(supplemented_history or []))
    if set(accepted) & (K | history):
        raise IntegrityError("accepted-list original-K/supplement overlap")
    if history:
        receipts = history_receipts or []
        independently_verified: set[str] = set()
        positions_digest = sha256(canonical_bytes(positions) + b"\n")
        for receipt in receipts:
            if (not isinstance(receipt, HistoryReceipt) or receipt.disposition != "NEW_HISTORY"
                    or receipt.intersection or receipt.accepted_digest != positions_digest
                    or receipt.original_K_digest != sha256(original_K_raw)
                    or receipt.boundary_digest != generation_boundary["digest"]):
                raise IntegrityError("full-list independent history receipt unavailable or stale")
            independently_verified.update(receipt.values)
        if independently_verified != history:
            raise IntegrityError("full-list history differs from independent complete receipts")
    audit = strict_private_json(audit_raw)
    if not isinstance(audit, list) or not audit:
        raise IntegrityError("complete original raw-draw audit mandatory")
    chain = supplement_chain or []
    if chain and (resolver is None or artifact_reader is None):
        raise IntegrityError("full supplement/continuation chain requires exact record and private byte readers")
    resolved_chain = []
    last_supplement = None
    last_record = None
    last_event = None
    completed_chain = False
    # Draw-time authority the verified chain accounts for: the boundary tip, then
    # each partial-generation continuation in order. paused_positions[k] is the
    # audit position retained by the k-th partial supplement.
    draw_tips = [generation_boundary["body"]["active_authority_tip"]]
    paused_positions: list[int] = []
    stage_roles = {"P", "I", "Q", "T", "O", "V", "A", "R", "B", "G", "S", "W", "U", "C", "D", "F"}

    def bind_hold(deps: dict) -> dict:
        """The segment's preceding active hold, its exact stage tuple and chain order."""
        nonlocal last_event
        event_ref = deps.get("AuthorityEvent")
        if event_ref is None:
            raise IntegrityError("supplement lacks preceding active hold event")
        bound_event = resolver(event_ref)
        validate_record(bound_event, resolver=resolver)
        stage_tuple = {key: value for key, value in deps.items() if key in stage_roles}
        if (record_ref(bound_event) != event_ref
                or bound_event["body"]["event_kind"] != "HOLD"
                or bound_event["body"]["study_id"] != body["study_id"]
                or bound_event["body"]["operation_id"] != operation_id
                or bound_event["body"]["binding_tuple"] != stage_tuple
                or any(stage_tuple.get(key) != value for key, value in expected_bindings.items())):
            raise IntegrityError("supplement hold event exact tuple mismatch")
        if last_event is not None and record_ref(last_event) != event_ref:
            raise IntegrityError("supplement binds stale preceding hold tip")
        last_event = bound_event
        return stage_tuple

    def bind_paused_prefix(snapshot_ref: dict | None, paused_audit_raw: bytes | None = None) -> bytes:
        """The producer's sealed stop state is an exact prefix of the completed list/audit."""
        if snapshot_ref is None:
            raise IntegrityError("partial supplement omits exact immutable prefix")
        snapshot = resolver(snapshot_ref)
        paused = snapshot["body"]["audit_position"]
        if type(paused) is not int:
            raise IntegrityError("paused audit position must be an integer")
        if paused_audit_raw is None:
            paused_audit_raw = canonical_bytes(audit[:paused]) + b"\n"
        prefix_raw = artifact_reader(snapshot["body"]["ordered_prefix"])
        verify_prefix_snapshot(snapshot, prefix_raw=prefix_raw, audit_raw=paused_audit_raw,
                               original_K_raw=original_K_raw,
                               boundary_digest=generation_boundary["digest"])
        if (strict_private_json(paused_audit_raw) != audit[:paused]
                or strict_private_json(prefix_raw) != positions[:snapshot["body"]["accepted_count"]]):
            raise IntegrityError("completed list/audit replaces the retained paused prefix")
        paused_positions.append(paused)
        return prefix_raw

    def bind_original_completion(stage_tuple: dict) -> None:
        """Completed-stage segments bind the unchanged original S bytes and commitment."""
        S_ref = stage_tuple.get("S")
        if S_ref is None:
            raise IntegrityError("completed supplement omits exact immutable S")
        S = resolver(S_ref)
        validate_record(S, resolver=resolver)
        S_body = S["body"]
        if (record_ref(S) != S_ref or S_body["operation_id"] != operation_id
                or S_body["study_id"] != body["study_id"]
                or S_body["dependencies"] != expected_bindings
                or S_body["generation_boundary"] != body["generation_boundary"]):
            raise IntegrityError("completed supplement S differs from original private generation")
        for field, original_raw in (("payload", payload_raw), ("salt", salt_raw), ("audit", audit_raw)):
            S_artifact = S_body[field]
            if (S_artifact["sha256_raw"] != sha256(original_raw)
                    or S_artifact["bytes"] != len(original_raw)
                    or artifact_reader(S_artifact) != original_raw):
                raise IntegrityError("completed supplement S private bytes differ from original")
        for commitment_role in ("W", "U", "C"):
            if commitment_role in stage_tuple:
                committed_record = resolver(stage_tuple[commitment_role])
                validate_record(committed_record, resolver=resolver)
                if (record_ref(committed_record) != stage_tuple[commitment_role]
                        or committed_record["body"]["commitment"] != expected_commitment):
                    raise IntegrityError("completed supplement changes existing full commitment")

    def raw_history(evidence: list[dict], digests: Any) -> tuple[list[bytes], dict[str, bytes]]:
        """Every raw proof the receipt names, in receipt order, plus its execution receipt."""
        by_digest = {art["sha256_raw"]: art for art in evidence}
        if not isinstance(digests, list) or not digests or any(d not in by_digest for d in digests):
            raise IntegrityError("supplement omits full independent historical inputs")
        sources = [artifact_reader(by_digest[d]) for d in digests]
        executions = {}
        for raw in sources:
            execution_ref = strict_private_json(raw)["execution_evidence"]
            executions[execution_ref["evidence_id"]] = artifact_reader(execution_ref)
        return sources, executions

    for ref in chain:
        record = resolver(ref)
        validate_record(record, resolver=resolver)
        if record_ref(record) != ref or record["body"]["study_id"] != body["study_id"]:
            raise IntegrityError("supplement chain raw/body/study mismatch")
        role = record["body"]["record_role"]
        deps = record["body"]["dependencies"]
        for original_role, original_ref in expected_bindings.items():
            if deps.get(original_role) != original_ref:
                raise IntegrityError("supplement does not preserve full original operational tuple")
        if role in {"PartialGenerationSupplement", "CompletedMembershipSupplement"}:
            if last_supplement is not None:
                raise IntegrityError("supplement missing its separate lead continuation")
            if record["body"]["actor"]["role"] not in {
                    "recorder", "independent_verifier", "independent_integrity_verifier"}:
                raise IntegrityError("supplement actor lacks independent evidence role")
            stage_tuple = bind_hold(deps)
            if role == "PartialGenerationSupplement":
                if completed_chain:
                    raise IntegrityError("partial-generation supplement after completed generation")
                membership = resolver(record["body"]["membership_receipt"])
                validate_record(membership, resolver=resolver)
                if membership["body"]["actor"]["role"] not in {
                        "independent_verifier", "independent_integrity_verifier"}:
                    raise IntegrityError("prefix receipt lacks independent accountable verifier")
                candidates = [artifact_reader(art) for art in record["body"]["evidence"]]
                audit_candidates = [raw for raw in candidates if isinstance(strict_private_json(raw), list)]
                if len(audit_candidates) != 1:
                    raise IntegrityError("partial supplement lacks exact full paused raw audit")
                prefix_raw = bind_paused_prefix(deps.get("PrefixSnapshot"), audit_candidates[0])
                history_inputs = [artifact_reader(art) for art in record["body"]["new_evidence"]]
                execution_inputs = {}
                for proof_raw in history_inputs:
                    proof = strict_private_json(proof_raw)
                    execution_ref = proof["execution_evidence"]
                    execution_inputs[execution_ref["evidence_id"]] = artifact_reader(execution_ref)
                prefix_receipt = verify_history(accepted_raw=prefix_raw, original_K_raw=original_K_raw,
                    history_inputs=history_inputs, execution_inputs=execution_inputs,
                    boundary_digest=generation_boundary["digest"],
                    verifier_id=membership["body"]["actor"]["actor_id"],
                    producer_id=record["body"]["actor"]["actor_id"])
                full_receipt = verify_history(accepted_raw=canonical_bytes(positions) + b"\n",
                    original_K_raw=original_K_raw, history_inputs=history_inputs,
                    execution_inputs=execution_inputs, boundary_digest=generation_boundary["digest"],
                    verifier_id=membership["body"]["actor"]["actor_id"],
                    producer_id=record["body"]["actor"]["actor_id"])
                if (prefix_receipt.disposition != "NEW_HISTORY" or prefix_receipt.intersection
                        or not prefix_receipt.all_values_in_original_K
                        or full_receipt.disposition != "NEW_HISTORY" or full_receipt.intersection
                        or set(full_receipt.values) - history):
                    raise IntegrityError("full independent prefix/history/K reconstruction failed")
                private_receipt = strict_private_json(artifact_reader(
                    membership["body"]["prior_use_scope_temporal_receipt"]))
                if private_receipt.get("receipt_digest") != prefix_receipt.receipt_digest:
                    raise IntegrityError("stored private prefix receipt does not reproduce")
            else:
                completed_chain = True
                bind_original_completion(stage_tuple)
                raw_receipt = artifact_reader(record["body"]["independent_full_list_non_overlap_receipt"])
                receipt_data = strict_private_json(raw_receipt)
                if (receipt_data.get("accepted_digest") != sha256(canonical_bytes(positions) + b"\n")
                        or receipt_data.get("original_K_digest") != sha256(original_K_raw)
                        or receipt_data.get("boundary_digest") != generation_boundary["digest"]
                        or receipt_data.get("disposition") != "NEW_HISTORY" or receipt_data.get("intersection") != []):
                    raise IntegrityError("completed supplement lacks independent full-list receipt")
                source_raws = [artifact_reader(ref) for ref in record["body"]["evidence"]
                               if ref["sha256_raw"] in receipt_data["evidence_digests"]]
                if [sha256(raw) for raw in source_raws] != receipt_data["evidence_digests"]:
                    raise IntegrityError("completed supplement omits full independent historical inputs")
                execution_inputs = {}
                for raw in source_raws:
                    execution_ref = strict_private_json(raw)["execution_evidence"]
                    execution_inputs[execution_ref["evidence_id"]] = artifact_reader(execution_ref)
                rebuilt = verify_history(accepted_raw=canonical_bytes(positions) + b"\n",
                    original_K_raw=original_K_raw, history_inputs=source_raws,
                    execution_inputs=execution_inputs, boundary_digest=generation_boundary["digest"],
                    verifier_id=record["body"]["actor"]["actor_id"],
                    producer_id=payload["body"]["actor"]["actor_id"])
                if (rebuilt.receipt_digest != receipt_data["receipt_digest"]
                        or rebuilt.disposition != "NEW_HISTORY" or rebuilt.intersection
                        or set(rebuilt.values) - history):
                    raise IntegrityError("complete raw historical supplement does not reproduce")
            last_supplement = record
        elif role == "LeadContinuation":
            lead = record["body"]
            if (lead["actor"]["role"] != "research_lead" or lead["operation_id"] != operation_id
                    or any(lead["unchanged_original_tuple"].get(k) != v for k, v in expected_bindings.items())
                    or (last_supplement is None) != (lead["disposition"] == "RELEASE")
                    or last_supplement is not None and deps.get(
                        last_supplement["body"]["record_role"]) != record_ref(last_supplement)
                    or last_supplement is None and deps.keys() & {
                        "PartialGenerationSupplement", "CompletedMembershipSupplement"}):
                raise IntegrityError("lead continuation unbound, mixed or out of order")
            if last_supplement is None:
                # PG-R7 release without new history: reproduce the conclusive receipt on the full list.
                stage_tuple = bind_hold(deps)
                if "S" in stage_tuple:
                    completed_chain = True
                    bind_original_completion(stage_tuple)
                elif completed_chain:
                    raise IntegrityError("partial-generation release after completed generation")
                else:
                    bind_paused_prefix(deps.get("PrefixSnapshot"))
                receipts = [art for art in lead["evidence"] if art["evidence_id"] == DISPOSITION_RECEIPT_ID]
                if len(receipts) != 1:
                    raise IntegrityError("release lacks its independent disposition receipt")
                receipt_data = strict_private_json(artifact_reader(receipts[0]))
                if not isinstance(receipt_data, dict):
                    raise IntegrityError("release lacks its independent disposition receipt")
                source_raws, execution_inputs = raw_history(lead["evidence"], receipt_data.get("evidence_digests"))
                rebuilt = verify_history(accepted_raw=canonical_bytes(positions) + b"\n",
                    original_K_raw=original_K_raw, history_inputs=source_raws,
                    execution_inputs=execution_inputs, boundary_digest=generation_boundary["digest"],
                    verifier_id=receipt_data.get("verifier_id"),
                    producer_id=payload["body"]["actor"]["actor_id"])
                if (rebuilt.disposition not in RELEASABLE or rebuilt.values or rebuilt.intersection
                        or rebuilt.disposition != receipt_data.get("disposition")
                        or list(rebuilt.post_boundary_values) != receipt_data.get("post_boundary_values")
                        or receipt_data.get("boundary_digest") != generation_boundary["digest"]):
                    raise IntegrityError("release disposition does not reproduce on the complete list")
            last_supplement = None
        elif role == "AuthorityEvent":
            event_body = record["body"]
            prior_tip = event_body["prior_tip"]
            if last_event is not None and prior_tip != last_event["digest"]:
                raise IntegrityError("authority event does not bind preceding chain tip")
            kind = event_body["event_kind"]
            if kind not in {"HOLD", "CONTINUE", "RELEASE", "ISSUE", "CONSUME"}:
                raise IntegrityError("wrong authority event in continuation chain")
            if any(event_body["binding_tuple"].get(k) != v for k, v in expected_bindings.items()):
                raise IntegrityError("chain authority event changes the original operational tuple")
            # Stage-tuple extension or a later consumption may separate one
            # continuation from the next hold; it never sits inside a supplement.
            if kind in {"ISSUE", "CONSUME"} and (
                    last_event is None or last_supplement is not None
                    or any(event_body["binding_tuple"].get(k) != v
                           for k, v in last_event["body"]["binding_tuple"].items())
                    or kind == "CONSUME" and expected_bindings["G"] in event_body["affected_authorizations"]):
                raise IntegrityError("intervening authority event breaks the continuation chain")
            if kind in {"CONTINUE", "RELEASE"}:
                if (last_record is None or last_record["body"]["record_role"] != "LeadContinuation"
                        or last_record["body"]["disposition"] != kind):
                    raise IntegrityError("authority release has no earlier separate lead record")
                lead_raw = canonical_bytes(last_record) + b"\n"
                if not any(artifact["sha256_raw"] == sha256(lead_raw)
                           and artifact["bytes"] == len(lead_raw) for artifact in record["body"]["evidence"]):
                    raise IntegrityError("authority release does not bind exact lead record bytes")
                if not completed_chain:
                    draw_tips.append(record["digest"])
            last_event = record
        else:
            raise IntegrityError("wrong record role in supplement/continuation chain")
        if last_record is not None and role != "AuthorityEvent":
            prior_role = last_record["body"]["record_role"]
            if deps.get(prior_role) != record_ref(last_record):
                raise IntegrityError("supplement/continuation chain link missing or reordered")
        resolved_chain.append(record)
        last_record = record
    if last_supplement is not None:
        raise IntegrityError("supplement chain ends without fresh lead continuation")
    if resolved_chain and (resolved_chain[-1]["body"]["record_role"] != "AuthorityEvent"
                           or resolved_chain[-1]["body"]["event_kind"] not in {"CONTINUE", "RELEASE"}):
        raise IntegrityError("supplement chain must end at a lead continuation event")
    if completed_chain and (active_chain_tip is None or resolved_chain[-1]["digest"] != active_chain_tip):
        raise IntegrityError("completed supplements lack exact guarded current continuation tip")
    # The immutable payload binds the last pre-completion continuation (or the
    # boundary tip when generation was never paused); completed supplements
    # bind forward to the separate active tip instead.
    if preceding_chain_tip != draw_tips[-1]:
        raise IntegrityError("generation receipt does not bind complete preceding chain forward")
    if history and not chain:
        raise IntegrityError("supplemented history lacks complete forward-bound chain")
    tip_index = {value: index for index, value in enumerate(draw_tips)}
    reconstructed: list[str] = []
    tip = generation_boundary["digest"]
    counts = {"raw": 0, "accepted": 0, "K_rejected": 0, "duplicate_rejected": 0}
    fields = {"raw_draw_ordinal", "raw_bytes_hex", "disposition", "accepted_position",
              "authority_tip", "prior_entry_digest"}
    for ordinal, entry in enumerate(audit, 1):
        if (not isinstance(entry, dict) or set(entry) != fields
                or type(entry["raw_draw_ordinal"]) is not int
                or entry["raw_draw_ordinal"] != ordinal or entry["prior_entry_digest"] != tip
                or entry["authority_tip"] not in authority_tips):
            raise IntegrityError("raw draw ordinal/chain/active authority mismatch")
        # A draw after the k-th paused position must run under the k-th verified
        # continuation; any tip the chain does not account for fails closed.
        if tip_index.get(entry["authority_tip"]) != sum(p < ordinal for p in paused_positions):
            raise IntegrityError("raw draw authority tip is not the verified chain tip for its position")
        value = values_checked([entry["raw_bytes_hex"]])[0]
        decision = "REJECT_K" if value in K else (
            "REJECT_DUPLICATE" if value in reconstructed else "ACCEPT")
        expected_position = len(reconstructed) + 1 if decision == "ACCEPT" else None
        if (entry["disposition"] != decision or entry["accepted_position"] != expected_position
                or (entry["accepted_position"] is not None
                    and type(entry["accepted_position"]) is not int)):
            raise IntegrityError("complete raw acceptance/rejection reconstruction fails")
        if len(reconstructed) == N:
            raise IntegrityError("raw draw occurred after list completion")
        counts["raw"] += 1
        if decision == "ACCEPT":
            reconstructed.append(value)
            counts["accepted"] += 1
        elif decision == "REJECT_K":
            counts["K_rejected"] += 1
        else:
            counts["duplicate_rejected"] += 1
        tip = sha256(canonical_bytes(entry))
    if reconstructed != accepted:
        raise IntegrityError("full accepted list differs from complete original audit")
    actual_commitment = commitment_value(payload_raw, salt_raw)
    if actual_commitment != expected_commitment:
        raise IntegrityError("full primitive c mismatch")
    return {"decision": "PASS", "accepted_count": N, "audit_counts": counts,
            "payload_sha256_raw": sha256(payload_raw), "salt_sha256_raw": sha256(salt_raw),
            "audit_sha256_raw": sha256(audit_raw), "audit_tip": tip, "entropy_source": entropy_source,
            "commitment": actual_commitment, "full_private_read_back": True,
            "original_K_disjoint": True, "supplemented_history_disjoint": True,
            "historical_completeness": "NOT ESTABLISHED"}


@dataclass(frozen=True)
class PrivateValues:
    """Exact private study values a public record must never expose in any common form."""
    uint64_hex: frozenset[str]
    salts: tuple[bytes, ...]
    paths: tuple[str, ...]

    def exposed_in(self, value: Any) -> bool:
        return self._exposed(_public_text(value))

    def exposed_in_public_record(self, record: dict) -> bool:
        """M3 over the designated human-written text surface of C only (Gate 8, D1/D2)."""
        return self._exposed(iter(public_text_surface(record)))

    def _exposed(self, texts: Iterator[str]) -> bool:
        decimals = {str(int(item, 16)) for item in self.uint64_hex}
        salt_hex = {salt.hex() for salt in self.salts}
        salt_base64 = {form.decode().rstrip("=") for salt in self.salts
                       for form in (base64.b64encode(salt), base64.urlsafe_b64encode(salt))}
        roots = {path.lower().replace("\\", "/") for path in self.paths}
        for text in texts:
            lowered = text.lower()
            if (any(item in lowered for item in self.uint64_hex)
                    or decimals.intersection(re.findall(r"\d+", text))
                    or any(item in lowered for item in salt_hex)
                    or any(item in text for item in salt_base64)
                    or any(root in lowered.replace("\\", "/") for root in roots)):
                return True
        return False


def _public_text(value: Any) -> Iterator[str]:
    if isinstance(value, dict):
        for key, item in value.items():
            yield key
            yield from _public_text(item)
    elif isinstance(value, list):
        for item in value:
            yield from _public_text(item)
    elif isinstance(value, str):
        yield value
    elif type(value) is int:
        yield str(value)


# Gate 8 (v2_gate8_scope_01.json, D1): every C field is classified by schema type.
# Only "text" fields are human-written and scanned; constant fields are fixed by the
# frozen schema, derived fields are recomputed or bound by equality (study_id is fixed
# at O, before any generated value exists), and typed fields are validated by type.
_C_ENVELOPE_FIELDS = {"schema": "constant", "version": "constant", "digest_convention": "constant",
                      "identity": "derived", "digest": "derived", "status": "text", "body": "body"}
_C_BODY_FIELDS = {"record_role": "constant", "N": "constant", "claim_profile": "constant",
                  "historical_coverage": "constant", "permanent_limitation": "constant",
                  "commitment": "derived", "dependencies": "derived", "study_id": "derived",
                  "decision": "text", "actor": "actor", "evidence": "artifact_list"}
_ACTOR_FIELDS = {"actor_id": "text", "role": "constant", "authority_evidence": "artifact"}
_ARTIFACT_FIELDS = {"evidence_id": "text", "sha256_raw": "typed", "bytes": "typed",
                    "visibility": "constant"}


def public_text_surface(record: dict) -> list[str]:
    """The explicit protected text fields of a C envelope or {"body": template}.

    body.decision, body.actor.actor_id, body.actor.authority_evidence.evidence_id,
    each body.evidence[].evidence_id and the envelope status when present. Any field
    outside the classification fails closed.
    """
    def classified(value: Any, fields: dict[str, str]) -> dict:
        if not isinstance(value, dict) or set(value) - set(fields):
            raise IntegrityError("unclassified public commitment field")
        return value

    def text(value: Any) -> str:
        if not isinstance(value, str):
            raise IntegrityError("protected public text field must be a string")
        return value

    envelope = classified(record, _C_ENVELOPE_FIELDS)
    body = classified(envelope.get("body"), _C_BODY_FIELDS)
    texts = [text(envelope["status"])] if "status" in envelope else []
    if "decision" in body:
        texts.append(text(body["decision"]))
    if "actor" in body:
        actor = classified(body["actor"], _ACTOR_FIELDS)
        if "actor_id" in actor:
            texts.append(text(actor["actor_id"]))
        if "authority_evidence" in actor:
            texts.append(text(classified(actor["authority_evidence"], _ARTIFACT_FIELDS)["evidence_id"]))
    evidence = body.get("evidence", [])
    if not isinstance(evidence, list):
        raise IntegrityError("public evidence must be an artifact list")
    texts.extend(text(classified(ref, _ARTIFACT_FIELDS)["evidence_id"]) for ref in evidence)
    return texts


def check_public_content(record: dict, private: PrivateValues) -> None:
    """Public-evidence, marker and M3 checks shared by publication and the pre-U check."""
    body = record["body"]
    for ref in body["evidence"]:
        if ref["visibility"] != "PUBLIC":
            raise IntegrityError("public commitment exposes private evidence")
    text = canonical_bytes(body).decode("utf-8")
    if any(marker in text for marker in ("value_hex", "raw_bytes_hex", "salt.bin", "runs/", "runs\\", ":\\")):
        raise IntegrityError("public template contains private values/paths/diagnostics")
    if private.exposed_in_public_record(record):
        raise IntegrityError("public template exposes actual private study values or paths")


def study_private_values(authority: Any) -> PrivateValues:
    """Read back S-bound positions, raw candidates and salt, original K and private roots."""
    try:
        S = authority.resolve(authority.bindings["S"])["body"]
        positions = strict_private_json(authority.read_artifact(S["payload"]))["body"]["positions"]
        audit = strict_private_json(authority.read_artifact(S["audit"]))
        original = authority.resolve(authority.bindings["O"])["body"]
        values = ({position["value_hex"] for position in positions}
                  | {entry["raw_bytes_hex"] for entry in audit}
                  | set(values_checked(strict_private_json(authority.read_artifact(original["K"])))))
        roots = (str(Path(authority.root).resolve()),
                 *(item["producer_root"] for item in authority.registered_producers().values()))
        return PrivateValues(frozenset(values_checked(sorted(values))),
                             (authority.read_artifact(S["salt"]),), roots)
    except (KeyError, TypeError) as exc:
        raise IntegrityError("actual private values unavailable; publication cannot be sanitized") from exc


def validate_publication_template(public_record: dict, authorization: dict,
                                  verification: dict, *, expected_tip: str,
                                  private: PrivateValues) -> None:
    """Verify approved sanitized C bytes and the forward U-ref insertion slot."""
    for record, role in ((public_record, "C"), (authorization, "U"), (verification, "W")):
        validate_record(record)
        if record["body"]["record_role"] != role:
            raise IntegrityError("wrong publication record role")
    C, U, W = public_record["body"], authorization["body"], verification["body"]
    if (U["actor"]["role"] != "research_lead" or C["actor"]["role"] != "publisher"
            or U["active_authority_tip"] != expected_tip or U["decision"] != "AUTHORIZED"
            or W["decision"] != "PASS" or C["commitment"] != U["commitment"]
            or U["commitment"] != W["commitment"]
            or C["study_id"] != U["study_id"] or U["study_id"] != W["study_id"]):
        raise IntegrityError("publication primitive c/study/authority mismatch")
    if C["dependencies"].get("U") != record_ref(authorization):
        raise IntegrityError("C missing exact forward U binding")
    if C["dependencies"].get("W") != record_ref(verification):
        raise IntegrityError("C missing exact private W binding")
    if U["dependencies"].get("W") != record_ref(verification):
        raise IntegrityError("U missing exact earlier W binding")
    for role, ref in U["dependencies"].items():
        if C["dependencies"].get(role) != ref:
            raise IntegrityError("publication operational tuple mismatch")
    template = U["approved_public_record_body"]
    if not isinstance(template, dict) or set(template) != {"body", "digest", "U_insertion_slot"}:
        raise IntegrityError("exact sanitized C template required")
    proposed = template["body"]
    if (template["U_insertion_slot"] != "body.dependencies.U"
            or not isinstance(proposed, dict) or "U" in proposed.get("dependencies", {})
            or "C" in U["dependencies"] or template["digest"] != sha256(canonical_bytes(proposed))):
        raise IntegrityError("cyclic/mismatched U template insertion slot")
    actual_without_U = {**C, "dependencies": {k: v for k, v in C["dependencies"].items() if k != "U"}}
    if actual_without_U != proposed:
        raise IntegrityError("public C differs from exact U-approved template")
    check_public_content(public_record, private)


def publish_commitment(authority: Any, public_record: dict, *, expected_tip: str, operation_id: str,
                       publisher: dict, destination: Path) -> dict:
    """Write the exact U-approved sanitized C once, inside the single-use U consumption."""
    def check() -> None:
        approval = authority.resolve(authority.bindings["U"])
        verification = authority.resolve(authority.bindings["W"])
        chain = {strict_private_json(path.read_bytes())["digest"]
                 for path in authority.root.glob("event-*.json")}
        if approval["body"]["active_authority_tip"] not in chain:
            raise IntegrityError("U approves a template against an unknown authority tip")
        validate_publication_template(public_record, approval, verification,
                                      expected_tip=approval["body"]["active_authority_tip"],
                                      private=study_private_values(authority))
        if public_record["body"]["actor"] != publisher:
            raise IntegrityError("public C must record the consuming publisher")

    def action(_lease: Any) -> dict:
        check()
        write_once(destination, public_record)
        return record_ref(public_record)
    check()  # never consume the single-use U for bytes it does not approve
    return authority.protected("commitment_publication", expected_tip=expected_tip,
                               operation_id=operation_id, action=action, consumer_actor=publisher)


def verify_W_bytes(record: dict, *, payload_raw: bytes, salt_raw: bytes,
                   expected_commitment: str) -> None:
    """DS-W7-01: primitive c plus ArtifactRefs, no synthetic c record."""
    validate_record(record)
    if record["body"]["record_role"] != "W":
        raise IntegrityError("private verification requires W role")
    body = record["body"]
    if (body["commitment"] != expected_commitment
            or commitment_value(payload_raw, salt_raw) != expected_commitment):
        raise IntegrityError("private verification primitive c mismatch")
    for field, raw in (("payload", payload_raw), ("salt", salt_raw)):
        ref = body[field]
        validate_artifact_ref(ref)
        if (ref["visibility"] != "PRIVATE" or ref["bytes"] != len(raw)
                or ref["sha256_raw"] != sha256(raw)):
            raise IntegrityError("private payload/salt ArtifactRef mismatch")


def verify_materialization(*, files: dict[str, bytes], defaults: dict[str, bytes],
                           effective_T8: bytes, aliases: bytes, frozen_pins: dict,
                           expected_defaults: dict[str, str],
                           expected_T8_digest: str, expected_aliases_digest: str) -> dict:
    """Verify all 41 packages/82 files and separate effective/default/alias bytes."""
    expected = {}
    for package, pins in frozen_pins["historical_packages"].items():
        expected[package + "/agent.py"] = pins["agent_py_sha256"]
        expected[package + "/agent.yaml"] = pins["agent_yaml_sha256"]
    for package, pins in frozen_pins["prospective_packages"].items():
        for name, digest in pins.items():
            expected[package + "/" + name] = digest
    packages = {name.split("/", 1)[0] for name in expected}
    if len(packages) != 41 or len(expected) != 82 or set(files) != set(expected):
        raise IntegrityError("complete exact 41-package/82-file materialization required")
    historical = set(frozen_pins["historical_packages"])
    if any(sha256(files[name].replace(b"\r\n", b"\n")
                  if name.split("/", 1)[0] in historical else files[name]) != digest
           for name, digest in expected.items()):
        raise IntegrityError("materialized inherited/prospective package pin drift")
    if set(defaults) != packages or set(expected_defaults) != packages:
        raise IntegrityError("complete 41 exact defaults required")
    if any(sha256(defaults[name]) != expected_defaults[name] for name in packages):
        raise IntegrityError("effective package-default drift")
    if sha256(effective_T8) != expected_T8_digest or sha256(aliases) != expected_aliases_digest:
        raise IntegrityError("effective T8 or logical-alias pin drift")
    if strict_private_json(effective_T8) != frozen_pins["effective_t8"]:
        raise IntegrityError("complete effective T8 conditions differ from frozen gameplay")
    if strict_private_json(aliases) != frozen_pins["logical_aliases"]:
        raise IntegrityError("logical aliases differ from frozen mapping")
    return {"decision": "PASS", "packages": 41, "files": 82, "defaults": 41,
            "materialized_manifest_digest": sha256(canonical_bytes(
                {name: sha256(raw) for name, raw in files.items()})),
            "defaults_digest": sha256(canonical_bytes(expected_defaults)),
            "T8_digest": expected_T8_digest, "aliases_digest": expected_aliases_digest}
