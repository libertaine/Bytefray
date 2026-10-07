"""Gate-8 private commitment verification (W) and pre-U publication controls.

Scope: v2_gate8_scope_01.json (v6-e9-v2-gate8-scope-eae9f407f5d1) and its lead
confirmation, revised for seal 06 by v2_gate8_scope_02.json (v6-e9-v2-gate8-scope-0761c4e07487,
disposition 03 F1-F4) and its lead confirmation. The W producer is REAL-only. It has no entropy parameter, mode, flag
or alternative branch, takes no caller-supplied chain, tips, history, receipts or
commitment, and has no command-line entry point. The sealed verify_complete_private
alone decides PASS. Operational use of every function here needs separate lead
authorization; nothing in this module grants it.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from .authority import THROUGH_G, AuthorityLog, Lease, durable_bytes
from .commitment import (
    PrivateValues,
    check_public_content,
    commitment_value,
    study_private_values,
    verify_complete_private,
    verify_W_bytes,
)
from .generation import DOMAIN, N
from .integrity import HistoryReceipt, verify_history
from .inventory import strict_private_json
from .records import (
    BASE,
    IntegrityError,
    canonical_bytes,
    catalogue,
    exact_keys,
    make_record,
    record_ref,
    sha256,
    strict_json,
    validate_actor,
    validate_artifact_ref,
    validate_record,
)

OUTCOMES = ("REFUSED_PRECONDITION", "UNAVAILABLE", "INTERRUPTED", "FAILED_VERIFICATION", "PASS")
W_DEPENDENCIES = (*THROUGH_G, "S")
U_DEPENDENCIES = (*W_DEPENDENCIES, "W")
LATER_ROLES = ("W", "U", "C", "D", "F")
RESULT_ID = "GATE8-W-VERIFICATION-RESULT"
PRE_U_RECEIPT_KIND = "GATE8_PRE_U_TEMPLATE_CHECK_V1"
PRE_U_RECEIPT_ID = "GATE8-PRE-U-TEMPLATE-CHECK"
ISSUANCE_KIND = "GATE8_U_ISSUANCE_V1"
ISSUANCE_ID = "GATE8-U-ISSUANCE"
ISSUING_FUNCTION = "tools.research.v6.e9.v2.private_verification.issue_publication_authorization"


class Refused(IntegrityError):
    """A precondition failed before any private byte was read."""


class Unavailable(IntegrityError):
    """Retained private evidence is missing or unreadable; verification did not complete."""


def _raw(value: Any) -> bytes:
    return canonical_bytes(value) + b"\n"


def _folder(authority: AuthorityLog) -> Path:
    S = authority.bindings.get("S")
    return authority.root / "private-verification" / (S["digest"] if S else "S-absent")


def _outcomes(folder: Path) -> list[dict]:
    return [strict_private_json(path.read_bytes()) for path in sorted(folder.glob("attempt-*.outcome.json"))]


def _begin(folder: Path, *, S: dict | None, verifier: dict, expected_tip: str,
           operation_id: str) -> tuple[int, list[int]]:
    """Write-once attempt intent; earlier intents without an outcome are INTERRUPTED."""
    folder.mkdir(parents=True, exist_ok=True)
    intents = sorted(folder.glob("attempt-*.intent.json"))
    if [path.name for path in intents] != [f"attempt-{i:04d}.intent.json" for i in range(1, len(intents) + 1)]:
        raise IntegrityError("W attempt record gap/fork")
    ordinal = len(intents) + 1
    interrupted = [i for i in range(1, ordinal) if not (folder / f"attempt-{i:04d}.outcome.json").exists()]
    durable_bytes(folder / f"attempt-{ordinal:04d}.intent.json", _raw({
        "attempt": ordinal, "S": S, "verifier": verifier.get("actor_id"), "expected_tip": expected_tip,
        "operation_id": operation_id, "interrupted_prior_attempts": interrupted}))
    return ordinal, interrupted


def _finish(folder: Path, ordinal: int, outcome: str, *, interrupted: list[int],
            reason: str | None = None, W: dict | None = None) -> None:
    durable_bytes(folder / f"attempt-{ordinal:04d}.outcome.json", _raw({
        "attempt": ordinal, "outcome": outcome, "reason": reason, "W": W,
        "interrupted_prior_attempts": interrupted}))


def _reader(authority: AuthorityLog) -> Callable[[dict], bytes]:
    """Exact retained private bytes; absence is UNAVAILABLE, changed bytes an integrity failure."""
    def read(ref: dict) -> bytes:
        validate_artifact_ref(ref)
        path = authority.root / "evidence-raw" / (ref["sha256_raw"] + ".bin")
        try:
            raw = path.read_bytes()
        except OSError as exc:
            raise Unavailable("retained private evidence unavailable") from exc
        if len(raw) != ref["bytes"] or sha256(raw) != ref["sha256_raw"]:
            raise IntegrityError("private evidence raw bytes changed")
        return raw
    return read


def _durable_log(authority: AuthorityLog) -> list[dict]:
    return [strict_private_json(path.read_bytes()) for path in sorted(authority.root.glob("event-*.json"))]


def _resolver(authority: AuthorityLog, events: list[dict]) -> Callable[[dict], dict]:
    """Authority events come from the durable log itself; other records from retention."""
    by_digest = {event["digest"]: event for event in events}

    def resolve(ref: dict) -> dict:
        event = by_digest.get(ref["digest"])
        if event is not None:
            if record_ref(event) != ref:
                raise IntegrityError("authority event reference drift")
            return event
        retained = authority.root / "evidence-records" / (ref["digest"] + ".json")
        try:
            return authority.resolve(ref)
        except IntegrityError as exc:
            if not retained.exists() and str(exc) == "exact record unavailable":
                raise Unavailable("retained evidence record unavailable") from exc
            raise
    return resolve


def _preconditions(authority: AuthorityLog, verifier: dict, folder: Path) -> None:
    """After the sealed _check passed: tuple stage, verifier independence, single W."""
    if "S" not in authority.bindings or any(role in authority.bindings for role in LATER_ROLES):
        raise Refused("W requires exactly the issued tuple through S")
    try:
        validate_actor(verifier)
    except IntegrityError as exc:
        raise Refused("registered independent W verifier required") from exc
    identity = verifier["actor_id"]
    if verifier["role"] != "independent_verifier" or authority.actors.get(identity) != "independent_verifier":
        raise Refused("registered independent W verifier required")
    producers = {authority.resolve(authority.bindings[role])["body"]["actor"]["actor_id"]
                 for role in ("O", "S", "G")}
    if identity in producers:
        raise Refused("W verifier must be independent of the custodian, recorder and lead")
    if (folder / "W.json").exists():
        raise Refused("W already produced for this S, or a partial W file is present")
    if any(item["outcome"] == "FAILED_VERIFICATION" for item in _outcomes(folder)):
        raise Refused("a completed verification of this S already failed")
    # After a completed-stage continuation the sealed verifier requires the chain to end at the
    # active tip. Tuple-extending ISSUE events after it are permitted by W-04, so they block W as
    # an authority state, never as a section-11 material failure. Any other event falls to the
    # W-04 classification in derive_chain, exactly as in every other chain shape (F2).
    events = _durable_log(authority)
    continuations = [i for i, event in enumerate(events) if event["body"]["event_kind"] in ("CONTINUE", "RELEASE")]
    if continuations and "S" in events[continuations[-1]]["body"]["binding_tuple"]:
        previous = events[continuations[-1]]["body"]["binding_tuple"]
        tail = events[continuations[-1] + 1:]
        permitted = True
        for event in tail:
            if event["body"]["event_kind"] != "ISSUE" or not _extends(previous, event["body"]["binding_tuple"]):
                permitted = False
                break
            previous = event["body"]["binding_tuple"]
        if tail and permitted:
            raise Refused("only tuple-extending ISSUE events follow the completed-stage continuation; "
                          "W requires that tip")


def _durable(path: Path) -> bytes | None:
    """Exact durable bytes, or None when the file is missing or unreadable."""
    try:
        return path.read_bytes()
    except OSError:
        return None


def _operational_boundary(authority: AuthorityLog, boundary: dict, read: Callable[[dict], bytes]) -> None:
    """D5/N6: the registered producer root, the durable first-raw marker and one REAL declaration.

    F1 (disposition 03): the boundary's own hash-checked evidence is checked first and fixes the
    expected bytes of the durable registry and marker. A present durable artifact with other
    bytes is a verification failure even when the other one is missing; otherwise a missing or
    unreadable durable artifact is UNAVAILABLE, and only its exact restoration lets W proceed.
    """
    G = authority.bindings["G"]
    producers, markers, declarations = [], [], []
    for ref in boundary["body"]["evidence"]:
        raw = read(ref)
        item = strict_private_json(raw)
        if not isinstance(item, dict):
            raise IntegrityError("unrecognized generation-boundary evidence")
        if item.get("kind") == "FIRST_RAW_BOUNDARY_V2":
            markers.append(raw)
        elif item.get("kind") == "ENTROPY_SOURCE_V2":
            declarations.append(item)
        elif "producer_root" in item:
            producers.append(raw)
    if len(producers) != 1:
        raise IntegrityError("generation boundary does not bind the registered producer root")
    if len(markers) != 1:
        raise IntegrityError("generation boundary does not bind the durable first-raw marker")
    if len(declarations) != 1 or declarations[0].get("mode") != "REAL":
        raise IntegrityError("operational W requires exactly one REAL entropy declaration")
    mismatched, unavailable = [], []
    registry = _durable(authority.root / "producer-roots" / (G["digest"] + ".json"))
    if registry is None:
        unavailable.append("producer registry")
    else:
        try:
            registered = authority.registered_producers().get(G["digest"])
        except OSError:
            unavailable.append("producer registry")
        else:
            if registry != producers[0] or registered is None or _raw(registered) != producers[0]:
                mismatched.append("generation boundary does not bind the registered producer root")
    marker = _durable(authority.root / "first-raw" / (G["digest"] + ".json"))
    if marker is None:
        unavailable.append("first-raw marker")
    elif marker != markers[0]:
        mismatched.append("generation boundary does not bind the durable first-raw marker")
    if mismatched:
        raise IntegrityError(mismatched[0])
    if unavailable:
        raise Unavailable("durable " + " and ".join(unavailable) + " unavailable")


def _extends(earlier: dict, later: dict) -> bool:
    return all(later.get(role) == ref for role, ref in earlier.items())


def _lead_record(event: dict, read: Callable[[dict], bytes]) -> dict:
    leads = [ref for ref in event["body"]["evidence"] if ref["evidence_id"] == "LEAD-CONTINUATION"]
    if len(leads) != 1:
        raise IntegrityError("continuation event lacks exactly one lead continuation record")
    lead = strict_private_json(read(leads[0]))
    validate_record(lead)
    if lead["body"]["record_role"] != "LeadContinuation":
        raise IntegrityError("continuation evidence is not a lead continuation record")
    return lead


def derive_chain(authority: AuthorityLog, boundary: dict, events: list[dict], active_tip: str,
                 read: Callable[[dict], bytes]) -> tuple[list[dict], list[str]]:
    """N2/D6: the complete supplement/continuation chain from the durable log.

    Every event after the generation boundary's tip is accounted for. Outside the
    chain only ISSUE events that extend the tuple are allowed. Returns the chain
    RecordRefs and the draw-time authority tips (boundary tip, then each
    partial-generation continuation).
    """
    digests = [event["digest"] for event in events]
    start = boundary["body"]["active_authority_tip"]
    if start not in digests:
        raise IntegrityError("generation boundary tip absent from the durable authority log")
    if (digests[-1] if digests else None) != active_tip:
        raise IntegrityError("durable authority log does not end at the active tip")
    base = events[digests.index(start)]
    post = events[digests.index(start) + 1:]
    previous = base["body"]["binding_tuple"]
    for event in post:
        if not _extends(previous, event["body"]["binding_tuple"]):
            raise IntegrityError("post-boundary authority event replaces an original binding")
        previous = event["body"]["binding_tuple"]
    kinds = [event["body"]["event_kind"] for event in post]
    others = [i for i, kind in enumerate(kinds) if kind != "ISSUE"]
    continuations = [i for i, kind in enumerate(kinds) if kind in ("CONTINUE", "RELEASE")]
    if not others:
        return [], [start]
    if not continuations or others[0] > continuations[-1] or others[-1] > continuations[-1]:
        raise IntegrityError("authority event outside the complete continuation chain")
    chain: list[dict] = []
    tips = [start]
    for event in post[others[0]:continuations[-1] + 1]:
        if event["body"]["event_kind"] in ("CONTINUE", "RELEASE"):
            lead = _lead_record(event, read)
            dependencies = lead["body"]["dependencies"]
            for role in ("PartialGenerationSupplement", "CompletedMembershipSupplement"):
                if role in dependencies:
                    chain.append(dependencies[role])
            chain.append(record_ref(lead))
            if "S" not in event["body"]["binding_tuple"]:
                tips.append(event["digest"])
        chain.append(record_ref(event))
    return chain, tips


def _full_list_history(chain: list[dict], resolve: Callable[[dict], dict], read: Callable[[dict], bytes], *,
                       positions_raw: bytes, original_K_raw: bytes, boundary: dict, verifier_id: str,
                       producer_id: str) -> tuple[set[str], list[HistoryReceipt]]:
    """PG-R8: every supplement's retained raw history, rechecked on the complete list."""
    history: set[str] = set()
    receipts: list[HistoryReceipt] = []
    for ref in chain:
        record = resolve(ref)
        role = record["body"]["record_role"]
        if role == "PartialGenerationSupplement":
            inputs = [read(art) for art in record["body"]["new_evidence"]]
        elif role == "CompletedMembershipSupplement":
            listed = strict_private_json(read(record["body"]["independent_full_list_non_overlap_receipt"]))
            digests = listed.get("evidence_digests") if isinstance(listed, dict) else None
            if not isinstance(digests, list):
                raise IntegrityError("completed supplement receipt lacks its raw history inputs")
            inputs = [read(art) for art in record["body"]["evidence"] if art["sha256_raw"] in digests]
        else:
            continue
        executions = {}
        for raw in inputs:
            proof = strict_private_json(raw)
            if not isinstance(proof, dict) or not isinstance(proof.get("execution_evidence"), dict):
                raise IntegrityError("supplement history proof lacks execution evidence")
            executions[proof["execution_evidence"]["evidence_id"]] = read(proof["execution_evidence"])
        receipt = verify_history(accepted_raw=positions_raw, original_K_raw=original_K_raw,
                                 history_inputs=inputs, execution_inputs=executions,
                                 boundary_digest=boundary["digest"], verifier_id=verifier_id,
                                 producer_id=producer_id)
        if receipt.disposition != "NEW_HISTORY" or receipt.intersection:
            raise IntegrityError("supplemented history does not reproduce as non-overlapping new history")
        history.update(receipt.values)
        receipts.append(receipt)
    return history, receipts


def _verify(authority: AuthorityLog, verifier: dict, lease: Lease) -> dict:
    """Complete private verification under the held lease; returns the unwritten W."""
    events = _durable_log(authority)
    read, resolve = _reader(authority), _resolver(authority, events)
    S = resolve(authority.bindings["S"])["body"]
    boundary = resolve(S["generation_boundary"])
    payload_raw, salt_raw, audit_raw = read(S["payload"]), read(S["salt"]), read(S["audit"])
    original = resolve(authority.bindings["O"])["body"]
    original_K_raw = read(original["K"])
    _operational_boundary(authority, boundary, read)
    chain, tips = derive_chain(authority, boundary, events, lease.authority_tip, read)
    payload = strict_private_json(payload_raw)
    positions_raw = _raw(payload["body"]["positions"])
    history, receipts = _full_list_history(
        chain, resolve, read, positions_raw=positions_raw, original_K_raw=original_K_raw,
        boundary=boundary, verifier_id=verifier["actor_id"], producer_id=payload["body"]["actor"]["actor_id"])
    commitment = commitment_value(payload_raw, salt_raw)
    result = verify_complete_private(
        payload_raw=payload_raw, salt_raw=salt_raw, audit_raw=audit_raw, original_K_raw=original_K_raw,
        expected_bindings=authority.original_bindings(),
        inventory_refs={key: original[key] for key in ("K", "E", "L")},
        operation_id=resolve(authority.bindings["G"])["body"]["operation_id"],
        generation_boundary=boundary, expected_commitment=commitment, authority_tips=tips,
        preceding_chain_tip=tips[-1], entropy_source="REAL",
        supplemented_history=sorted(history) or None, supplement_chain=chain,
        history_receipts=receipts or None, artifact_reader=read, resolver=resolve,
        active_chain_tip=lease.authority_tip)
    if result.get("decision") != "PASS" or result.get("entropy_source") != "REAL":
        raise IntegrityError("complete private verification did not pass for REAL entropy")
    evidence = authority.retain_artifact(_raw({
        "kind": "GATE8_PRIVATE_VERIFICATION_RESULT_V1", "verifier_result": result,
        "supplement_chain": chain, "authority_tips": tips, "active_chain_tip": lease.authority_tip,
        "history_receipts": [receipt.receipt_digest for receipt in receipts]}), RESULT_ID)
    W = make_record("W", {
        "record_role": "W", "study_id": authority.study_id, "actor": verifier, "decision": "PASS",
        "dependencies": {role: authority.bindings[role] for role in W_DEPENDENCIES},
        "evidence": [evidence], "active_authority_tip": lease.authority_tip,
        "all_position_checks": {"accepted_count": N, "contiguous_order": True, "domain": DOMAIN,
                                "original_K_disjoint": True, "strict_uint64": True, "unique": True,
                                "supplemented_history_count": len(history),
                                "supplemented_history_disjoint": True},
        "audit_reproduction": {"audit_counts": result["audit_counts"],
                               "audit_sha256_raw": result["audit_sha256_raw"],
                               "audit_tip": result["audit_tip"], "entropy_source": "REAL",
                               "full_private_read_back": True,
                               "historical_completeness": "NOT ESTABLISHED"},
        "commitment": commitment, "payload": S["payload"], "salt": S["salt"],
        "supplement_chain": chain})
    verify_W_bytes(W, payload_raw=payload_raw, salt_raw=salt_raw, expected_commitment=commitment)
    return W


def produce_private_verification(authority: AuthorityLog, *, verifier: dict, expected_tip: str,
                                 operation_id: str) -> dict:
    """Produce W once for the issued S, or record why not. Returns the W RecordRef.

    Outcomes: REFUSED_PRECONDITION and UNAVAILABLE (no private verification
    completed), INTERRUPTED (an intent with no outcome), FAILED_VERIFICATION (a
    completed verification failed; later attempts for this S are refused) and PASS.
    Retries are new, separately recorded attempts; nothing alters the bound bytes.
    """
    folder = _folder(authority)
    ordinal, interrupted = _begin(folder, S=authority.bindings.get("S"), verifier=verifier,
                                  expected_tip=expected_tip, operation_id=operation_id)
    phase = "precondition"

    def action(lease: Lease) -> dict:
        nonlocal phase
        _preconditions(authority, verifier, folder)
        phase = "verification"
        W = _verify(authority, verifier, lease)
        # F3: W, its retained record and PASS are written under the lease that verified them, so
        # no authority change can interleave between the verified state and the durable result.
        phase = "write"
        authority.retain_record(W)
        durable_bytes(folder / "W.json", _raw(W))
        _finish(folder, ordinal, "PASS", interrupted=interrupted, W=record_ref(W))
        phase = "recorded"
        return W

    try:
        W = authority.protected("private_verification", expected_tip=expected_tip,
                                operation_id=operation_id, action=action)
    except IntegrityError as exc:
        if phase in ("write", "recorded"):
            # A failed write leaves no outcome, as before seal 06; a failed post-action recheck
            # after PASS propagates without a second, contradictory outcome.
            raise
        if isinstance(exc, Unavailable):
            outcome = "UNAVAILABLE"
        elif isinstance(exc, Refused) or phase != "verification":
            outcome = "REFUSED_PRECONDITION"
        else:
            outcome = "FAILED_VERIFICATION"
        _finish(folder, ordinal, outcome, interrupted=interrupted, reason=str(exc))
        raise
    return record_ref(W)


def _frozen_limitation() -> str:
    contract = strict_json((BASE / "amended_rule_contract_v2_proposed_02.json").read_bytes())
    return contract["exact_interpretation"]["permanent_limitation_text"]


def _template_structure(authority: AuthorityLog, body: Any, W: dict) -> None:
    """The proposed C body is the exact sanitized template U may approve."""
    records = catalogue()
    exact_keys(body, set(records["records"]["C"]["required_body_fields"])
               | set(records["common"]["body_common_fields"]))
    if (body["record_role"] != "C" or body["study_id"] != authority.study_id
            or body["N"] != N or type(body["N"]) is not int or body["claim_profile"] != "C-LIMITED"
            or body["historical_coverage"] != "NOT ESTABLISHED"
            or body["permanent_limitation"] != _frozen_limitation()
            or body["commitment"] != W["body"]["commitment"]
            or body["dependencies"] != {role: authority.bindings[role] for role in U_DEPENDENCIES}):
        raise IntegrityError("proposed C template does not bind the exact frozen fields and tuple through W")
    validate_actor(body["actor"])
    if body["actor"]["role"] != "publisher" or authority.actors.get(body["actor"]["actor_id"]) != "publisher":
        raise IntegrityError("proposed C template must name a registered publisher")
    if not isinstance(body["decision"], str) or not body["decision"].strip() or not isinstance(body["evidence"], list):
        raise IntegrityError("proposed C template decision/evidence malformed")
    for ref in body["evidence"]:
        validate_artifact_ref(ref)


def _template_decision(authority: AuthorityLog, body: Any, private: PrivateValues) -> tuple[str, str | None]:
    W = authority.resolve(authority.bindings["W"])
    try:
        _template_structure(authority, body, W)
        check_public_content({"body": body}, private)
    except IntegrityError as exc:
        return "FAIL", str(exc)
    return "PASS", None


def _stage_through_W(authority: AuthorityLog) -> None:
    if "W" not in authority.bindings or any(role in authority.bindings for role in ("U", "C", "D", "F")):
        raise IntegrityError("pre-U template check requires the issued tuple through W and no U")


def verify_operational_w(authority: AuthorityLog) -> dict:
    """F4 (disposition 03): the W an operational consumer relies on is this producer's PASS W.

    Read-only checks A1-A6 of v2_gate8_scope_02.json under the existing evidence model. They stop
    a W added by generic append from reaching the pre-U check or U issuance; they do not
    authenticate on-disk artifacts against an actor able to rewrite the private root.
    """
    W_ref, S_ref = authority.bindings.get("W"), authority.bindings.get("S")
    if W_ref is None or S_ref is None:
        raise IntegrityError("no issued W")
    W = authority.resolve(W_ref)
    body = W["body"]
    # A1: study, tuple through S (which binds P and I) and a registered independent verifier.
    validate_record(W, resolver=authority.resolve)
    actor = body["actor"]
    validate_actor(actor)
    if (body["record_role"] != "W" or body["decision"] != "PASS" or body["study_id"] != authority.study_id
            or body["dependencies"] != {role: authority.bindings[role] for role in W_DEPENDENCIES}
            or actor["role"] != "independent_verifier"
            or authority.actors.get(actor["actor_id"]) != "independent_verifier"):
        raise IntegrityError("W does not bind this study's tuple through S and an independent verifier")
    events = _durable_log(authority)
    read, resolve = _reader(authority), _resolver(authority, events)
    # A2: the D5 producer root and first-raw marker of S's generation boundary.
    _operational_boundary(authority, resolve(resolve(S_ref)["body"]["generation_boundary"]), read)
    # A3: the producer wrote exactly this W for this S.
    folder = _folder(authority)
    if _durable(folder / "W.json") != _raw(W):
        raise IntegrityError("W was not written by the Gate-8 producer for this S")
    # A4: one retained PASS outcome for this W, no completed failure, and its own attempt intent.
    outcomes = _outcomes(folder)
    passes = [item for item in outcomes if item.get("outcome") == "PASS"]
    if (len(passes) != 1 or any(item.get("outcome") == "FAILED_VERIFICATION" for item in outcomes)
            or passes[0].get("W") != W_ref or type(passes[0].get("attempt")) is not int):
        raise IntegrityError("W lacks exactly one matching retained PASS outcome")
    intent = strict_private_json(_durable(folder / f"attempt-{passes[0]['attempt']:04d}.intent.json") or b"")
    if (not isinstance(intent, dict) or intent.get("attempt") != passes[0]["attempt"]
            or intent.get("S") != S_ref or intent.get("verifier") != actor["actor_id"]
            or intent.get("expected_tip") != body["active_authority_tip"]):
        raise IntegrityError("W's PASS outcome does not match its producer attempt")
    # A5: the retained verification result W binds.
    results = [ref for ref in body["evidence"] if ref["evidence_id"] == RESULT_ID]
    if len(results) != 1:
        raise IntegrityError("W must bind exactly one retained private verification result")
    result = strict_private_json(read(results[0]))
    verified = result.get("verifier_result") if isinstance(result, dict) else None
    if (not isinstance(result, dict) or result.get("kind") != "GATE8_PRIVATE_VERIFICATION_RESULT_V1"
            or result.get("active_chain_tip") != body["active_authority_tip"]
            or result.get("supplement_chain") != body["supplement_chain"]
            or not isinstance(verified, dict) or verified.get("decision") != "PASS"
            or verified.get("entropy_source") != "REAL"):
        raise IntegrityError("W's retained verification result does not match W")
    # A6: the lead's ISSUE(+W) with no intervening non-ISSUE event, and W not since revoked.
    digests = [event["digest"] for event in events]
    if body["active_authority_tip"] not in digests:
        raise IntegrityError("W's active authority tip is absent from the durable log")
    start = digests.index(body["active_authority_tip"])
    adding = next((i for i, event in enumerate(events) if event["body"]["binding_tuple"].get("W") == W_ref), None)
    if (adding is None or adding <= start or events[adding]["body"]["event_kind"] != "ISSUE"
            or events[adding]["body"]["actor"]["role"] != "research_lead"):
        raise IntegrityError("W was not issued by the research lead after it was produced")
    previous = events[start]["body"]["binding_tuple"]
    for event in events[start + 1:adding + 1]:
        if event["body"]["event_kind"] != "ISSUE" or not _extends(previous, event["body"]["binding_tuple"]):
            raise IntegrityError("a non-ISSUE authority event precedes the lead's ISSUE(+W)")
        previous = event["body"]["binding_tuple"]
    if any(event["body"]["event_kind"] in ("REVOKE", "TERMINATE", "CORRECT")
           and W_ref in event["body"]["affected_authorizations"] for event in events):
        raise IntegrityError("W has been revoked")
    return {"decision": "ADMISSIBLE", "W": W_ref, "pass_attempt": passes[0]["attempt"],
            "issuance_event": record_ref(events[adding])}


def check_publication_template(authority: AuthorityLog, proposed_body: dict, *, checker: dict,
                               expected_tip: str, operation_id: str) -> dict:
    """D3: read-only template check before U is issued. Returns the decision and PRIVATE receipt."""
    def action(lease: Lease) -> dict:
        validate_actor(checker)
        if checker["role"] != "independent_verifier" or authority.actors.get(checker["actor_id"]) != checker["role"]:
            raise IntegrityError("registered independent template checker required")
        _stage_through_W(authority)
        verify_operational_w(authority)  # F4: no receipt for a W lacking producer evidence
        private = study_private_values(authority)
        decision, reason = _template_decision(authority, proposed_body, private)
        template_digest = sha256(canonical_bytes(proposed_body))
        receipt = authority.retain_artifact(_raw({
            "kind": PRE_U_RECEIPT_KIND, "study_id": authority.study_id, "template_digest": template_digest,
            "decision": decision, "reason": reason, "checker": checker,
            "active_authority_tip": lease.authority_tip, "W": authority.bindings["W"]}),
            PRE_U_RECEIPT_ID + "-" + template_digest[:16])
        return {"decision": decision, "receipt": receipt, "template_digest": template_digest}
    return authority.protected("private_verification", expected_tip=expected_tip,
                               operation_id=operation_id, action=action)


def _pass_receipt(authority: AuthorityLog, refs: list[dict], template_digest: str) -> tuple[dict, dict]:
    receipts = [ref for ref in refs if ref["evidence_id"].startswith(PRE_U_RECEIPT_ID)]
    if len(receipts) != 1:
        raise IntegrityError("U must bind exactly one pre-U template check receipt")
    receipt = strict_private_json(authority.read_artifact(receipts[0]))
    if (not isinstance(receipt, dict) or receipt.get("kind") != PRE_U_RECEIPT_KIND
            or receipt.get("decision") != "PASS" or receipt.get("template_digest") != template_digest
            or receipt.get("study_id") != authority.study_id or receipt.get("W") != authority.bindings.get("W")):
        raise IntegrityError("U does not bind a PASS pre-U check of its exact template")
    return receipts[0], receipt


def issue_publication_authorization(authority: AuthorityLog, U: dict, *, lead: dict, expected_tip: str,
                                    operation_id: str) -> dict:
    """The Gate-8 operational path for issuing U: D3 must pass, then the lead's ISSUE adds U."""
    validate_record(U, resolver=authority.resolve)
    body = U["body"]
    validate_actor(lead)
    if (body["record_role"] != "U" or body["actor"] != lead or lead["role"] != "research_lead"
            or authority.actors.get(lead["actor_id"]) != "research_lead"
            or body["study_id"] != authority.study_id):
        raise IntegrityError("U must be the registered research lead's record for this study")
    _stage_through_W(authority)
    template = body["approved_public_record_body"]
    if not isinstance(template, dict) or set(template) != {"body", "digest", "U_insertion_slot"}:
        raise IntegrityError("exact sanitized C template required")
    template_digest = sha256(canonical_bytes(template["body"]))
    W = authority.resolve(authority.bindings["W"])
    if (template["digest"] != template_digest or template["U_insertion_slot"] != "body.dependencies.U"
            or body["dependencies"] != {role: authority.bindings[role] for role in U_DEPENDENCIES}
            or body["commitment"] != W["body"]["commitment"] or body["active_authority_tip"] != expected_tip):
        raise IntegrityError("U does not approve the checked template against the tuple through W")
    receipt_ref, receipt = _pass_receipt(authority, body["evidence"], template_digest)

    def recheck(_lease: Lease) -> str:
        verify_operational_w(authority)  # F4: U is issued only against an admissible producer W
        return _template_decision(authority, template["body"], study_private_values(authority))[0]
    if authority.protected("private_verification", expected_tip=expected_tip, operation_id=operation_id,
                           action=recheck) != "PASS":
        raise IntegrityError("pre-U template check fails; U is not issued")
    attestation = authority.retain_artifact(_raw({
        "kind": ISSUANCE_KIND, "function": ISSUING_FUNCTION, "study_id": authority.study_id,
        "U": record_ref(U), "template_digest": template_digest, "pre_U_receipt": receipt_ref,
        "checker": receipt["checker"], "lead": lead, "prior_tip": expected_tip}),
        ISSUANCE_ID + "-" + U["digest"][:16])
    authority.retain_record(U)
    previous = authority.bindings
    authority.bindings = {**previous, "U": record_ref(U)}
    try:
        event = authority.append("ISSUE", lead, expected_tip=expected_tip, operation_id=operation_id,
                                 evidence=[receipt_ref, attestation])
    except BaseException:
        authority.bindings = previous
        raise
    return {"U": record_ref(U), "event": event, "attestation": attestation}


def verify_operational_u(authority: AuthorityLog) -> dict:
    """D3 clarification: a U is operationally admissible only if issued through the Gate-8 path."""
    U_ref = authority.bindings.get("U")
    if U_ref is None:
        raise IntegrityError("no issued U")
    adding = next((event for event in _durable_log(authority)
                   if event["body"]["binding_tuple"].get("U") == U_ref), None)
    if (adding is None or adding["body"]["event_kind"] != "ISSUE"
            or adding["body"]["actor"]["role"] != "research_lead"):
        raise IntegrityError("U was not issued by a research-lead ISSUE event")
    evidence = adding["body"]["evidence"]
    attestations = [ref for ref in evidence if ref["evidence_id"].startswith(ISSUANCE_ID)]
    if len(attestations) != 1:
        raise IntegrityError("U was not issued through the Gate-8 issuance path")
    attestation = strict_private_json(authority.read_artifact(attestations[0]))
    U = authority.resolve(U_ref)
    template_digest = sha256(canonical_bytes(U["body"]["approved_public_record_body"]["body"]))
    if (not isinstance(attestation, dict) or attestation.get("kind") != ISSUANCE_KIND
            or attestation.get("function") != ISSUING_FUNCTION or attestation.get("U") != U_ref
            or attestation.get("study_id") != authority.study_id
            or attestation.get("prior_tip") != adding["body"]["prior_tip"]
            or attestation.get("lead") != adding["body"]["actor"]
            or attestation.get("template_digest") != template_digest
            or attestation.get("pre_U_receipt") not in evidence
            or attestation.get("pre_U_receipt") not in U["body"]["evidence"]):
        raise IntegrityError("U issuance attestation does not match the issuing event")
    receipt = strict_private_json(authority.read_artifact(attestation["pre_U_receipt"]))
    if (not isinstance(receipt, dict) or receipt.get("kind") != PRE_U_RECEIPT_KIND
            or receipt.get("decision") != "PASS" or receipt.get("template_digest") != template_digest):
        raise IntegrityError("U issuance lacks a PASS pre-U check of its exact template")
    return {"decision": "ADMISSIBLE", "U": U_ref, "issuance_event": record_ref(adding),
            "pre_U_receipt": attestation["pre_U_receipt"]}
