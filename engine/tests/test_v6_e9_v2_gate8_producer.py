"""Gate-8 W producer: outcomes, chain reconstruction, entropy and boundary (implementer tests).

SYNTHETIC QUALIFICATION FIXTURES ONLY. Every REAL-labelled study below is built by hand in a
pytest temporary root, in the synthetic-e9-v2-only namespace, with synthetic actors and
synthetic bytes. REAL appears only as an input declaration presented to the code under
test. No REAL entropy is consumed: Generator.draw_one and Generator.complete are never
called in REAL mode, salt_creation is never invoked, no salt.bin is written, and nothing
here is operational evidence or acceptable to any real-study path.
"""

from __future__ import annotations

import hashlib
import inspect
import json
import os

import pytest

from engine.tests._e9_v2_synthetic_records import STUDY, actor, fixture, through_g
from tools.research.v6.e9.v2 import private_verification as pv
from tools.research.v6.e9.v2.authority import AuthorityLog
from tools.research.v6.e9.v2.commitment import (
    PrivateValues,
    commitment_value,
    publish_commitment,
    verify_complete_private,
    verify_W_bytes,
)
from tools.research.v6.e9.v2.generation import DOMAIN, Generator, N, entropy_declaration
from tools.research.v6.e9.v2.integrity import IntegrityController
from tools.research.v6.e9.v2.inventory import artifact, revealed_lists
from tools.research.v6.e9.v2.records import (
    BASE,
    IntegrityError,
    canonical_bytes,
    make_record,
    record_ref,
    sha256,
    strict_json,
)

OP = "synthetic-operation"
LEAD = actor("research_lead", "synthetic-research_lead")
RECORDER = actor("recorder", "synthetic-recorder")
INTEGRITY = actor("independent_integrity_verifier", "synthetic-integrity")
VERIFIER = actor("independent_verifier", "synthetic-private-verifier")
CHECKER = actor("independent_verifier", "synthetic-template-checker")
PUBLISHER = actor("publisher", "independent-publisher")
SMALL_K = (0, 1, 2, 3, 5, 7, 42, 6, 8, 9, 256, 1412)
LIMITATION = strict_json((BASE / "amended_rule_contract_v2_proposed_02.json").read_bytes())[
    "exact_interpretation"]["permanent_limitation_text"]


def encode(value):
    return canonical_bytes(value) + b"\n"


def uint64(label):
    return hashlib.sha256(label.encode()).hexdigest()[:16]


def realistic_K():
    """Small public literals, structural-collision values and the complete pinned E6/E8 lists."""
    values = {f"{value:016x}" for value in SMALL_K}
    for listed in revealed_lists().values():
        values |= listed
    return sorted(values)


POSITIONS = [uint64(f"gate-eight-position-{i}") for i in range(1, N + 1)]


class Study:
    """A hand-built REAL-labelled synthetic study through S (fixture only)."""

    def __init__(self, tmp_path, *, declared="REAL", K=None, parts=("producer", "marker", "entropy"),
                 declarations=None, positions=None):
        self.tmp = tmp_path
        self.K = realistic_K() if K is None else sorted(K)
        self.K_raw = encode(self.K)
        self.refs = {"K": artifact(self.K_raw, "ORIGINAL-K"), "E": artifact(encode([]), "ORIGINAL-E"),
                     "L": artifact(encode({}), "ORIGINAL-L")}
        self.records = through_g(inventory_refs=self.refs)
        self.by_digest = {record["digest"]: record for record in self.records.values()}
        actors = {record["body"]["actor"]["actor_id"]: record["body"]["actor"]["role"]
                  for record in self.records.values() if "actor" in record["body"]}
        actors.update({a["actor_id"]: a["role"] for a in (LEAD, RECORDER, INTEGRITY, VERIFIER, CHECKER,
                                                          PUBLISHER)})
        self.log = AuthorityLog(tmp_path / "authority", STUDY,
                                {role: record_ref(record) for role, record in self.records.items()},
                                actors=actors, resolver=lambda ref: self.by_digest[ref["digest"]],
                                source_check=lambda: None)
        self.log.append("ISSUE", LEAD, expected_tip=self.log.tip, operation_id=OP)
        stub = None if declared == "REAL" else (lambda size: pytest.fail("fixture never draws"))
        self.generator = Generator(tmp_path / "producer", self.log, operation_id=OP, recorder=RECORDER,
                                   original_K_raw=self.K_raw, inventory_refs=self.refs,
                                   draw_bytes=stub, salt_bytes=stub, mode=declared)
        self.generator.consume(expected_tip=self.log.tip,
                               boundary_evidence=artifact(b"fixture consumption", "FIXTURE-CONSUMPTION"))
        self.controller = IntegrityController(self.log, verifier_actor=INTEGRITY, lead_actor=LEAD)
        self.entries, self.accepted, self.chain, self.pending = [], [], [], []
        self.boundary = self._boundary(declared, parts, declarations)
        positions = POSITIONS if positions is None else positions
        k_member = self.K[2] if len(self.K) > 2 else None
        self.script = ([k_member] if k_member else []) + [positions[0], positions[0], *positions[1:]]
        self.S = None

    def _boundary(self, declared, parts, declarations):
        G = self.log.bindings["G"]
        marker = self.log.mark_first_raw(self.generator.producer_ref)
        real = entropy_declaration(declared, study_id=STUDY, G=G, operation_id=OP)
        declarations = [real] if declarations is None else declarations(real, G)
        available = {"producer": [self.generator.producer_ref], "marker": [marker], "entropy": [
            self.log.retain_artifact(encode(item), f"ENTROPY-SOURCE-{index}-" + G["digest"])
            for index, item in enumerate(declarations)]}
        body = {"record_role": "GenerationBoundary", "study_id": STUDY, "actor": RECORDER,
                "decision": "RECORDED", "dependencies": dict(self.log.bindings),
                "evidence": [ref for part in parts for ref in available[part]],
                "active_authority_tip": self.log.tip, "operation_id": OP, "producer_fence_epoch": 0,
                "durable_instant": artifact(b"synthetic fixture instant", "FIXTURE-INSTANT")}
        boundary = make_record("GenerationBoundary", body)
        (self.generator.root / "boundary.json").write_bytes(encode(boundary))
        self.audit_tip = boundary["digest"]
        return boundary

    def draw(self, count=None):
        """Write the producer's durable intent/audit files for the next scripted values."""
        K = set(self.K)
        count = len(self.script) - len(self.entries) if count is None else count
        tip = self.log.tip  # unchanged during a batch of draws; reading it revalidates the log
        for value in self.script[len(self.entries):len(self.entries) + count]:
            ordinal = len(self.entries) + 1
            disposition = "REJECT_K" if value in K else (
                "REJECT_DUPLICATE" if value in self.accepted else "ACCEPT")
            entry = {"raw_draw_ordinal": ordinal, "raw_bytes_hex": value, "disposition": disposition,
                     "accepted_position": len(self.accepted) + 1 if disposition == "ACCEPT" else None,
                     "authority_tip": tip, "prior_entry_digest": self.audit_tip}
            root = self.generator.root
            (root / f"draw-{ordinal:08d}.intent.json").write_bytes(encode(
                {"ordinal": ordinal, "operation_id": OP, "authority_tip": tip, "prior_tip": self.audit_tip}))
            (root / f"draw-{ordinal:08d}.audit.json").write_bytes(encode(
                {"entry": entry, "digest": sha256(canonical_bytes(entry))}))
            self.entries.append(entry)
            if disposition == "ACCEPT":
                self.accepted.append(value)
            self.audit_tip = sha256(canonical_bytes(entry))

    def _hold(self, label):
        hold = self.log.append("HOLD", INTEGRITY, expected_tip=self.log.tip, operation_id=OP,
                               evidence=[artifact(label.encode(), "STOP-" + label)])
        # Tuple-extending ISSUE events before the first chain event stay outside the chain.
        self.chain += [*(self.pending if self.chain else []), record_ref(hold)]
        self.pending = []
        return hold

    def proof(self, value, *, executed=True):
        temporal = "BEFORE" if executed else "UNKNOWN"
        execution = encode({"executed_values": [value], "started": executed, "scope": "IN_SCOPE",
                            "temporal_order": temporal, "generation_boundary_digest": self.boundary["digest"]})
        execution_ref = artifact(execution, "EXECUTION-" + uint64(value + str(executed)))
        body = {"values": [value], "actual_execution": executed, "scope_verified": executed,
                "temporal_order": temporal, "generation_boundary_digest": self.boundary["digest"],
                "execution_evidence": execution_ref}
        if not executed:
            body["disproval"] = "NOT_EXECUTED"
        return encode(body), {execution_ref["evidence_id"]: execution}

    def partial_continue(self, label="partial"):
        """PG-R8: verified new history already in original K; same-operation continuation."""
        self._hold(label)
        snapshot = self.generator.snapshot(evidence=artifact(label.encode(), "STOP-" + label), snapshot_id=label)
        proof, executions = self.proof(self.K[5])
        supplement = self.controller.partial_supplement(
            generator=self.generator, snapshot=snapshot,
            prefix_raw=(self.generator.root / f"prefix-{label}.json").read_bytes(),
            audit_raw=encode(self.generator.read_audit()[0]), original_K_raw=self.K_raw,
            history_inputs=[proof], execution_inputs=executions, expected_tip=self.log.tip, operation_id=OP)
        released = self.controller.release(
            "PARTIAL_GENERATION", supplement["receipt"], expected_tip=self.log.tip, operation_id=OP,
            evidence=[artifact(proof, "HISTORY-" + label)], original_bindings_valid=True,
            supplement=supplement["supplement"], scope="remaining original synthetic draws")
        self.chain += [record_ref(supplement["supplement"]), record_ref(released["lead_continuation"]),
                       record_ref(released["event"])]

    def partial_release(self, label="disproved"):
        """PG-R7: conclusive disproval of an alleged prior use; same paused operation resumes."""
        self._hold(label)
        snapshot = self.generator.snapshot(evidence=artifact(label.encode(), "STOP-" + label), snapshot_id=label)
        proof, executions = self.proof(self.accepted[-1], executed=False)
        decided = self.controller.verify_disposition(
            "PARTIAL_GENERATION", accepted_raw=(self.generator.root / f"prefix-{label}.json").read_bytes(),
            original_K_raw=self.K_raw, history_inputs=[proof], execution_inputs=executions,
            boundary_digest=self.boundary["digest"], expected_tip=self.log.tip,
            producer_id=RECORDER["actor_id"], generator=self.generator, snapshot=snapshot)
        released = self.controller.release(
            "PARTIAL_GENERATION", decided["receipt"], expected_tip=self.log.tip, operation_id=OP,
            evidence=decided["evidence"], original_bindings_valid=True, snapshot=snapshot,
            scope="remaining original synthetic draws")
        self.chain += [record_ref(released["lead_continuation"]), record_ref(released["event"])]

    def complete(self, *, payload_changes=None, audit_entries=None):
        """Hand-built SeedPayload, literal synthetic salt bytes and S; then the lead's ISSUE(+S)."""
        self.draw()
        assert len(self.accepted) == N
        entries = self.entries if audit_entries is None else audit_entries
        audit_raw = encode(entries)
        preceding = self.log.tip
        body = {"record_role": "SeedPayload", "study_id": STUDY, "actor": RECORDER, "decision": "SEALED",
                "dependencies": dict(self.log.bindings), "evidence": [], "N": N, "domain": DOMAIN,
                "operation_id": OP, "audit": artifact(audit_raw, "COMPLETE-AUDIT"),
                "generation_boundary": record_ref(self.boundary), "inventory_refs": self.refs,
                "positions": [{"position": i, "value_hex": v} for i, v in enumerate(self.accepted, 1)],
                "preceding_chain_tip": preceding}
        body.update(payload_changes or {})
        self.payload = make_record("SeedPayload", body)
        self.payload_raw = encode(self.payload)
        self.salt = hashlib.sha256(b"synthetic qualification fixture salt bytes").digest()
        self.audit_raw = audit_raw
        counts = {"raw": len(entries), "accepted": N,
                  "K_rejected": sum(e["disposition"] == "REJECT_K" for e in entries),
                  "duplicate_rejected": sum(e["disposition"] == "REJECT_DUPLICATE" for e in entries)}
        S = make_record("S", {
            "record_role": "S", "study_id": STUDY, "actor": RECORDER, "decision": "RECORDED",
            "dependencies": dict(self.log.bindings), "evidence": [], "accepted_count": N,
            "audit": artifact(audit_raw, "COMPLETE-AUDIT"), "audit_counts": counts,
            "authority_tip_at_completion": preceding, "generation_boundary": record_ref(self.boundary),
            "operation_id": OP, "payload": artifact(self.payload_raw, "COMPLETE-PAYLOAD"),
            "salt": artifact(self.salt, "COMPLETE-SALT")})
        for raw, label in ((self.payload_raw, "COMPLETE-PAYLOAD"), (self.salt, "COMPLETE-SALT"),
                           (audit_raw, "COMPLETE-AUDIT"), (self.K_raw, "ORIGINAL-K")):
            self.log.retain_artifact(raw, label)
        self.log.retain_record(self.boundary)
        self.log.retain_record(S)
        self.S = S
        self.issue("S", S)
        return S

    def issue(self, role, record):
        self.by_digest[record["digest"]] = record
        self.log.bindings = {**self.log.bindings, role: record_ref(record)}
        event = self.log.append("ISSUE", LEAD, expected_tip=self.log.tip, operation_id=OP)
        self.pending.append(record_ref(event))
        return event

    def generated_continue(self, label="completed"):
        """Completed-payload supplement: newly evidenced history outside K, full-list non-overlap."""
        self._hold(label)
        proof, executions = self.proof("ffffffffffffffff")
        completed = self.controller.completed_supplement(
            "GENERATED", accepted_raw=encode(self.payload["body"]["positions"]), original_K_raw=self.K_raw,
            history_inputs=[proof], execution_inputs=executions, generation_boundary=self.boundary,
            expected_tip=self.log.tip, producer_id=RECORDER["actor_id"],
            inspection_boundary="synthetic full list only")
        released = self.controller.release(
            "GENERATED", completed["receipt"], expected_tip=self.log.tip, operation_id=OP,
            evidence=[artifact(proof, "COMPLETED-HISTORY-" + label)], original_bindings_valid=True,
            supplement=completed["supplement"])
        self.chain += [record_ref(completed["supplement"]), record_ref(released["lead_continuation"]),
                       record_ref(released["event"])]

    def generated_release(self, label="generated-disproval"):
        self._hold(label)
        proof, executions = self.proof(self.accepted[0], executed=False)
        decided = self.controller.verify_disposition(
            "GENERATED", accepted_raw=encode(self.payload["body"]["positions"]), original_K_raw=self.K_raw,
            history_inputs=[proof], execution_inputs=executions, boundary_digest=self.boundary["digest"],
            expected_tip=self.log.tip, producer_id=RECORDER["actor_id"])
        released = self.controller.release(
            "GENERATED", decided["receipt"], expected_tip=self.log.tip, operation_id=OP,
            evidence=decided["evidence"], original_bindings_valid=True)
        self.chain += [record_ref(released["lead_continuation"]), record_ref(released["event"])]

    @property
    def folder(self):
        return self.log.root / "private-verification" / self.log.bindings["S"]["digest"]

    def outcomes(self):
        return [json.loads(path.read_bytes()) for path in sorted(self.folder.glob("attempt-*.outcome.json"))]

    def produce(self, verifier=VERIFIER, expected_tip=None):
        return pv.produce_private_verification(self.log, verifier=verifier,
                                               expected_tip=expected_tip or self.log.tip,
                                               operation_id="synthetic-private-verification")

    def template(self, *, decision="PUBLISHED", evidence=(), actor_=PUBLISHER):
        W = self.log.resolve(self.log.bindings["W"])
        return {"record_role": "C", "study_id": STUDY, "actor": actor_, "decision": decision,
                "dependencies": {role: self.log.bindings[role] for role in pv.U_DEPENDENCIES},
                "evidence": list(evidence), "N": N, "claim_profile": "C-LIMITED",
                "commitment": W["body"]["commitment"], "historical_coverage": "NOT ESTABLISHED",
                "permanent_limitation": LIMITATION}

    def check(self, body):
        return pv.check_publication_template(self.log, body, checker=CHECKER, expected_tip=self.log.tip,
                                             operation_id="synthetic-pre-u-check")

    def U(self, body, receipts):
        W = self.log.resolve(self.log.bindings["W"])
        return make_record("U", {
            "record_role": "U", "study_id": STUDY, "actor": LEAD, "decision": "AUTHORIZED",
            "dependencies": {role: self.log.bindings[role] for role in pv.U_DEPENDENCIES},
            "evidence": list(receipts), "active_authority_tip": self.log.tip,
            "approved_public_record_body": {"body": body, "digest": sha256(canonical_bytes(body)),
                                            "U_insertion_slot": "body.dependencies.U"},
            "commitment": W["body"]["commitment"], "scope": "specific experimental commitment publication only"})

    def issue_U(self, U):
        result = pv.issue_publication_authorization(self.log, U, lead=LEAD, expected_tip=self.log.tip,
                                                    operation_id="synthetic-u-issuance")
        self.by_digest[U["digest"]] = U
        return result

    def through_publication(self, *, decision="PUBLISHED"):
        """W, ISSUE(+W), pre-U check, Gate-8 issuance of U, then exact publication of C."""
        W_ref = self.produce()
        self.issue("W", self.log.resolve(W_ref))
        body = self.template(decision=decision)
        checked = self.check(body)
        assert checked["decision"] == "PASS"
        U = self.U(body, [checked["receipt"]])
        self.issue_U(U)
        C = make_record("C", {**body, "dependencies": {**body["dependencies"], "U": record_ref(U)}})
        published = publish_commitment(self.log, C, expected_tip=self.log.tip, operation_id="synthetic-publication",
                                       publisher=PUBLISHER, destination=self.tmp / "C.json")
        self.by_digest[C["digest"]] = C
        return W_ref, U, C, published


def built(tmp_path, *shapes, **options):
    study = Study(tmp_path, **options)
    plan = {"partial_continue": 4, "partial_release": 8}
    for shape in shapes:
        if shape in plan:
            study.draw(plan[shape] - len(study.entries))
            getattr(study, shape)(label=shape.replace("_", ""))
    study.complete()
    for shape in shapes:
        if shape not in plan:
            getattr(study, shape)(label=shape.replace("_", ""))
    return study


def test_w01_no_holds_full_flow_through_publication_and_worker_start(tmp_path):
    study = built(tmp_path)
    W_ref, U, C, published = study.through_publication()
    W = study.log.resolve(W_ref)
    body = W["body"]
    assert set(body["dependencies"]) == {"P", "I", "Q", "O", "V", "A", "R", "B", "G", "S"}
    assert body["commitment"] == commitment_value(study.payload_raw, study.salt)
    assert (body["payload"], body["salt"]) == (study.S["body"]["payload"], study.S["body"]["salt"])
    assert body["supplement_chain"] == [] and body["decision"] == "PASS"
    assert body["audit_reproduction"]["entropy_source"] == "REAL"
    assert body["audit_reproduction"]["historical_completeness"] == "NOT ESTABLISHED"
    assert body["audit_reproduction"]["audit_counts"] == {"raw": N + 2, "accepted": N, "K_rejected": 1,
                                                          "duplicate_rejected": 1}
    assert body["all_position_checks"]["accepted_count"] == N
    verify_W_bytes(W, payload_raw=study.payload_raw, salt_raw=study.salt, expected_commitment=body["commitment"])
    assert (study.folder / "W.json").read_bytes() == encode(W)
    assert [item["outcome"] for item in study.outcomes()] == ["PASS"]
    assert published == record_ref(C) and (tmp_path / "C.json").read_bytes() == encode(C)
    assert pv.verify_operational_u(study.log)["decision"] == "ADMISSIBLE"
    D = fixture("D", {**study.records, "S": study.S, "W": W, "U": U, "C": C})
    study.issue("C", C)
    study.issue("D", D)
    assert study.log.protected("worker_start", expected_tip=study.log.tip, operation_id="synthetic-consumer",
                               action=lambda lease: "started") == "started"


SHAPES = [("partial_continue",), ("partial_release",), ("partial_continue", "partial_release"),
          ("generated_continue",), ("generated_release",),
          ("partial_continue", "partial_release", "generated_continue"),
          ("partial_release", "generated_release")]


@pytest.mark.parametrize("shapes", SHAPES, ids=["+".join(s) for s in SHAPES])
def test_w02_complete_chain_is_rebuilt_from_the_durable_log_for_every_shape(tmp_path, shapes):
    study = built(tmp_path, *shapes)
    W = study.log.resolve(study.produce())
    assert W["body"]["supplement_chain"] == study.chain
    new_history = sum(shape.endswith("continue") for shape in shapes)
    assert W["body"]["all_position_checks"]["supplemented_history_count"] == new_history
    assert W["body"]["active_authority_tip"] == study.log.tip


def test_w03_generated_stage_release_is_always_included_where_the_sealed_verifier_would_accept_none(
        tmp_path):
    study = built(tmp_path, "generated_release")
    common = {"payload_raw": study.payload_raw, "salt_raw": study.salt, "audit_raw": study.audit_raw,
              "original_K_raw": study.K_raw, "expected_bindings": study.log.original_bindings(),
              "inventory_refs": study.refs, "operation_id": OP, "generation_boundary": study.boundary,
              "expected_commitment": commitment_value(study.payload_raw, study.salt),
              "authority_tips": [study.boundary["body"]["active_authority_tip"]],
              "preceding_chain_tip": study.boundary["body"]["active_authority_tip"],
              "entropy_source": "REAL", "artifact_reader": study.log.read_artifact, "resolver": study.log.resolve}
    # N2 as recorded: the sealed verifier passes an empty chain despite the GENERATED-stage release.
    assert verify_complete_private(**common)["decision"] == "PASS"
    W = study.log.resolve(study.produce())
    assert W["body"]["supplement_chain"] == study.chain and len(study.chain) == 3


def test_w03_deleted_retained_record_or_reordered_log_fails_closed(tmp_path):
    study = built(tmp_path, "partial_continue")
    supplement = study.chain[1]
    path = study.log.root / "evidence-records" / (supplement["digest"] + ".json")
    retained = path.read_bytes()
    path.unlink()
    with pytest.raises(pv.Unavailable):
        study.produce()
    path.write_bytes(retained)
    tip = study.log.tip
    events = sorted(study.log.root.glob("event-*.json"))
    first, second = events[-2].read_bytes(), events[-1].read_bytes()
    events[-2].write_bytes(second)
    events[-1].write_bytes(first)
    with pytest.raises(IntegrityError):
        study.produce(expected_tip=tip)
    assert not (study.folder / "W.json").exists()
    assert [item["outcome"] for item in study.outcomes()] == ["UNAVAILABLE", "REFUSED_PRECONDITION"]


def test_w04_a_tail_event_other_than_a_tuple_extending_issue_fails_verification(tmp_path):
    study = built(tmp_path)
    study.log.append("CONSUME", RECORDER, expected_tip=study.log.tip, operation_id=OP,
                     affected=[study.log.bindings["S"]])
    with pytest.raises(IntegrityError, match="outside the complete continuation chain"):
        study.produce()
    assert [item["outcome"] for item in study.outcomes()] == ["FAILED_VERIFICATION"]


def test_w04_an_event_after_a_completed_continuation_is_refused_not_a_material_failure(tmp_path, monkeypatch):
    study = built(tmp_path, "generated_continue")
    study.log.append("ISSUE", LEAD, expected_tip=study.log.tip, operation_id=OP)  # redundant re-issue
    reads = []
    real_reader = pv._reader
    monkeypatch.setattr(pv, "_reader", lambda authority: (lambda ref: reads.append(ref) or real_reader(authority)(ref)))
    with pytest.raises(pv.Refused, match="completed-stage continuation"):
        study.produce()
    assert reads == [] and [item["outcome"] for item in study.outcomes()] == ["REFUSED_PRECONDITION"]


DECLARATIONS = {
    "absent": lambda real, G: [],
    "duplicate": lambda real, G: [real, real],
    "mixed": lambda real, G: [real, {**real, "mode": "SYNTHETIC",
                                     "draw_source": "injected deterministic synthetic byte stream",
                                     "salt_source": "injected deterministic synthetic byte stream"}],
    "other_study": lambda real, G: [{**real, "study_id": "other-synthetic-study"}],
    "other_G": lambda real, G: [{**real, "G": {**G, "digest": "f" * 64}}],
    "other_operation": lambda real, G: [{**real, "operation_id": "other-synthetic-operation"}],
}
PARTS = {"no_producer": ("marker", "entropy"), "no_marker": ("producer", "entropy"), "neither": ("entropy",)}


@pytest.mark.parametrize("variant", ["synthetic", *DECLARATIONS, *PARTS, "marker_file_removed"])
def test_w05_operational_w_requires_real_and_the_registered_producer_root_and_marker(tmp_path, variant):
    options = {"synthetic": {"declared": "SYNTHETIC"}}.get(variant, {})
    if variant in DECLARATIONS:
        options = {"declarations": DECLARATIONS[variant]}
    elif variant in PARTS:
        options = {"parts": PARTS[variant]}
    study = Study(tmp_path, **options)
    study.complete()
    if variant == "marker_file_removed":  # seal 06, F1: a missing durable marker is UNAVAILABLE
        marker = study.log.root / "first-raw" / (study.log.bindings["G"]["digest"] + ".json")
        retained = marker.read_bytes()
        marker.unlink()
    with pytest.raises(IntegrityError):
        study.produce()
    assert not (study.folder / "W.json").exists()
    if variant == "marker_file_removed":
        assert [item["outcome"] for item in study.outcomes()] == ["UNAVAILABLE"]
        marker.write_bytes(retained)  # exact restoration; a new attempt can then pass
        assert study.log.resolve(study.produce())["body"]["decision"] == "PASS"
        assert [item["outcome"] for item in study.outcomes()] == ["UNAVAILABLE", "PASS"]
        return
    assert [item["outcome"] for item in study.outcomes()] == ["FAILED_VERIFICATION"]
    with pytest.raises(pv.Refused, match="already failed"):
        study.produce()


@pytest.mark.parametrize("condition", ["held", "terminal", "stale_tip", "S_not_issued", "source_drift",
                                       "unregistered_verifier", "publisher_verifier", "recorder_verifier",
                                       "W_already_issued"])
def test_w06_preconditions_refuse_before_any_private_read(tmp_path, monkeypatch, condition):
    study = built(tmp_path)
    reads = []
    real_reader = pv._reader

    def spying_reader(authority):
        read = real_reader(authority)

        def spy(ref):
            reads.append(ref["evidence_id"])
            return read(ref)
        return spy
    monkeypatch.setattr(pv, "_reader", spying_reader)
    verifier, tip = VERIFIER, None
    if condition == "held":
        study.log.append("HOLD", INTEGRITY, expected_tip=study.log.tip, operation_id=OP,
                         evidence=[artifact(b"held", "STOP-HELD")])
    elif condition == "terminal":
        study.log.append("TERMINATE", LEAD, expected_tip=study.log.tip, operation_id=OP,
                         evidence=[artifact(b"terminal", "TERMINAL")])
    elif condition == "stale_tip":
        tip = study.boundary["body"]["active_authority_tip"]
    elif condition == "S_not_issued":
        study.log.bindings = {role: ref for role, ref in study.log.bindings.items() if role != "S"}
    elif condition == "source_drift":
        def drift():
            raise IntegrityError("instrument/qualification source pin drift")
        study.log.source_check = drift
    elif condition == "unregistered_verifier":
        verifier = actor("independent_verifier", "unregistered-verifier")
    elif condition == "publisher_verifier":
        verifier = {**PUBLISHER, "role": "independent_verifier"}
    elif condition == "recorder_verifier":
        verifier = {**RECORDER, "role": "independent_verifier"}
    else:
        W_ref = study.produce()
        study.issue("W", study.log.resolve(W_ref))
    attempts_before = len(list(study.log.root.glob("private-verification/*/attempt-*.outcome.json")))
    with pytest.raises(IntegrityError):
        study.produce(verifier=verifier, expected_tip=tip)
    outcomes = [json.loads(p.read_bytes())["outcome"]
                for p in sorted(study.log.root.glob("private-verification/*/attempt-*.outcome.json"))]
    assert outcomes[attempts_before:] == ["REFUSED_PRECONDITION"]
    if condition != "W_already_issued":
        assert reads == []


@pytest.mark.parametrize("fault", ["reversed_positions", "wrong_domain", "wrong_operation", "stale_tip",
                                   "audit_disposition", "changed_retained_bytes"])
def test_w07_completed_verification_failures_are_terminal_for_that_S(tmp_path, fault):
    study = built(tmp_path) if fault == "changed_retained_bytes" else Study(tmp_path)
    if fault != "changed_retained_bytes":
        study.draw()
        positions = [{"position": i, "value_hex": v} for i, v in enumerate(study.accepted, 1)]
        changes, entries = {}, None
        if fault == "reversed_positions":
            changes = {"positions": [{"position": i, "value_hex": p["value_hex"]}
                                     for i, p in enumerate(reversed(positions), 1)]}
        elif fault == "wrong_domain":
            changes = {"domain": "uint64/little-endian/OS CSPRNG/accepted draw order"}
        elif fault == "wrong_operation":
            changes = {"operation_id": "other-synthetic-operation"}
        elif fault == "stale_tip":
            changes = {"preceding_chain_tip": study.boundary["digest"]}
        else:
            entries = [dict(entry) for entry in study.entries]
            entries[0]["disposition"] = "ACCEPT"
        study.complete(payload_changes=changes, audit_entries=entries)
    else:
        path = study.log.root / "evidence-raw" / (study.S["body"]["audit"]["sha256_raw"] + ".bin")
        path.write_bytes(path.read_bytes().replace(b"REJECT_DUPLICATE", b"REJECT_DUPLICATES"))
    with pytest.raises(IntegrityError):
        study.produce()
    assert [item["outcome"] for item in study.outcomes()] == ["FAILED_VERIFICATION"]
    assert not (study.folder / "W.json").exists()
    with pytest.raises(pv.Refused):
        study.produce()
    assert [item["outcome"] for item in study.outcomes()] == ["FAILED_VERIFICATION", "REFUSED_PRECONDITION"]


def test_w08_unavailable_evidence_then_byte_identical_restoration(tmp_path):
    study = built(tmp_path)
    path = study.log.root / "evidence-raw" / (study.S["body"]["payload"]["sha256_raw"] + ".bin")
    retained = path.read_bytes()
    path.unlink()
    with pytest.raises(pv.Unavailable):
        study.produce()
    path.write_bytes(retained)
    W = study.log.resolve(study.produce())
    assert W["body"]["decision"] == "PASS"
    assert [item["outcome"] for item in study.outcomes()] == ["UNAVAILABLE", "PASS"]


def test_w09_write_once_interrupted_attempt_and_partial_w_file(tmp_path):
    study = built(tmp_path)
    study.folder.mkdir(parents=True)
    (study.folder / "attempt-0001.intent.json").write_bytes(encode({"attempt": 1, "simulated": "interrupted"}))
    study.produce()
    second = json.loads((study.folder / "attempt-0002.intent.json").read_bytes())
    assert second["interrupted_prior_attempts"] == [1]
    assert [item["outcome"] for item in study.outcomes()] == ["PASS"]
    with pytest.raises(pv.Refused, match="already produced"):
        study.produce()
    other = built(tmp_path / "partial")
    other.folder.mkdir(parents=True)
    (other.folder / "W.json").write_bytes(b'{"partial"')
    with pytest.raises(pv.Refused):
        other.produce()
    assert (other.folder / "W.json").read_bytes() == b'{"partial"'


def test_w10_w_and_attempt_records_expose_no_private_value(tmp_path):
    """Generated values (accepted and non-K raw candidates), the salt and the private roots in every
    representation, and K members in their 16-hex form. A small K member's decimal form occurs
    structurally in any record (versions, digests): that is N1's false positive, not a disclosure."""
    study = built(tmp_path, "partial_continue")
    W = study.log.resolve(study.produce())
    raws = {entry["raw_bytes_hex"] for entry in study.entries} - set(study.K)
    generated = PrivateValues(frozenset(set(study.accepted) | raws), (study.salt,),
                              (str(study.log.root.resolve()), str(study.generator.root.resolve())))
    texts = [canonical_bytes(W).decode()] + [path.read_text() for path in study.folder.glob("attempt-*.json")]
    for text in texts:
        assert not generated.exposed_in(text)
        assert not any(member in text.lower() for member in study.K)


def test_w11_injected_generator_boundary_layout_matches_the_fixture_layout(tmp_path):
    fixture_study = Study(tmp_path / "real-labelled")
    records = through_g(inventory_refs=fixture_study.refs)
    by_digest = {record["digest"]: record for record in records.values()}
    actors = {r["body"]["actor"]["actor_id"]: r["body"]["actor"]["role"]
              for r in records.values() if "actor" in r["body"]}
    actors[RECORDER["actor_id"]] = "recorder"
    log = AuthorityLog(tmp_path / "injected-authority", STUDY, {r: record_ref(v) for r, v in records.items()},
                       actors=actors, resolver=lambda ref: by_digest[ref["digest"]], source_check=lambda: None)
    log.append("ISSUE", LEAD, expected_tip=log.tip, operation_id=OP)
    stream = iter([uint64("parity-a"), uint64("parity-b")])
    injected = Generator(tmp_path / "injected-producer", log, operation_id=OP, recorder=RECORDER,
                         original_K_raw=fixture_study.K_raw, inventory_refs=fixture_study.refs,
                         draw_bytes=lambda size: bytes.fromhex(next(stream)),
                         salt_bytes=lambda size: pytest.fail("no salt"), mode="SYNTHETIC")
    injected.consume(expected_tip=log.tip, boundary_evidence=artifact(b"consume", "CONSUME"))
    for _ in range(2):
        injected.draw_one(expected_tip=log.tip, durable_instant=artifact(b"instant", "INSTANT"))
    boundary = json.loads((tmp_path / "injected-producer" / "boundary.json").read_bytes())

    def layout(authority, record):
        items = [json.loads(authority.read_artifact(ref)) for ref in record["body"]["evidence"]]
        return [item.get("kind") or ("PRODUCER_ROOT" if "producer_root" in item else "?") for item in items], items
    injected_kinds, injected_items = layout(log, boundary)
    fixture_kinds, fixture_items = layout(fixture_study.log, fixture_study.boundary)
    assert injected_kinds == fixture_kinds == ["PRODUCER_ROOT", "FIRST_RAW_BOUNDARY_V2", "ENTROPY_SOURCE_V2"]
    assert set(injected_items[2]) == set(fixture_items[2])
    assert (injected_items[2]["mode"], fixture_items[2]["mode"]) == ("SYNTHETIC", "REAL")


def test_w12_producer_is_real_only_with_no_entropy_reference_or_mode_switch():
    source = inspect.getsource(pv)
    for forbidden in ("urandom", "import secrets", "import random", "import os", "SYNTHETIC", "mode="):
        assert forbidden not in source
    assert list(inspect.signature(pv.produce_private_verification).parameters) == [
        "authority", "verifier", "expected_tip", "operation_id"]
    assert os.urandom.__name__ == "forbidden"  # the qualification guard is active


def test_w13_produced_w_meets_ds_w1_w2_w7(tmp_path):
    study = built(tmp_path)
    W = study.log.resolve(study.produce())
    deps = W["body"]["dependencies"]
    assert "c" not in deps and not ({"T", "U", "C"} & set(deps))
    assert isinstance(W["body"]["commitment"], str) and len(W["body"]["commitment"]) == 64
    assert W["body"]["payload"]["visibility"] == W["body"]["salt"]["visibility"] == "PRIVATE"
    verify_W_bytes(W, payload_raw=study.payload_raw, salt_raw=study.salt,
                   expected_commitment=commitment_value(study.payload_raw, study.salt))


def test_w14_no_incomplete_selective_or_stale_chain_reaches_the_verifier(tmp_path, monkeypatch):
    calls = []
    real = pv.verify_complete_private

    def spy(**kwargs):
        calls.append(kwargs["supplement_chain"])
        return real(**kwargs)
    monkeypatch.setattr(pv, "verify_complete_private", spy)
    with pytest.raises(TypeError):
        pv.produce_private_verification(object(), verifier=VERIFIER, expected_tip="a" * 64, operation_id="x",
                                        supplement_chain=[])
    study = built(tmp_path, "partial_continue", "generated_continue")
    lead = study.chain[2]
    assert lead["schema"] == "bytefray.v6.e9.continuation_release"
    lead_raw = study.log.root / "evidence-raw" / (lead["sha256_raw"] + ".bin")
    retained = lead_raw.read_bytes()
    lead_raw.unlink()
    with pytest.raises(pv.Unavailable):
        study.produce()
    with pytest.raises(IntegrityError):
        study.produce(expected_tip=study.boundary["body"]["active_authority_tip"])
    assert calls == []
    lead_raw.write_bytes(retained)
    study.produce()
    assert calls == [study.chain]
