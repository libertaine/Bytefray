"""Every consuming operation, publication, recovery conflicts and persisted terminal stages.

Complete synthetic tuples make hold/terminal denials depend on the hold or terminal
event itself rather than on a missing binding. No match, entropy or bootstrap runs.
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
import random
import secrets

import pytest

from engine.tests._e9_v2_synthetic_records import (
    STUDY,
    actor,
    artifact,
    fixture,
    t_not_applicable,
    through_g,
)
from engine.tests.test_v6_e9_v2_independent_dispatch import begin, proof
from engine.tests.test_v6_e9_v2_independent_integrity import encode, history_fixture
from tools.research.v6.e9.v2.adoption import ROOT
from tools.research.v6.e9.v2.authority import OPERATION_ROLES, AuthorityLog, pinned_source_checker
from tools.research.v6.e9.v2.commitment import publish_commitment
from tools.research.v6.e9.v2.dispatch import ARTIFACT_NAMES, DispatchLedger
from tools.research.v6.e9.v2.integrity import IntegrityController, verify_history
from tools.research.v6.e9.v2.records import (
    ADOPTED,
    IntegrityError,
    canonical_bytes,
    make_record,
    read_record,
    record_ref,
    sha256,
)
from tools.research.v6.e9.v2.reporting import classify_report

OPERATIONS = ("raw_draw", "salt_creation", "payload_seal", "private_verification",
              "commitment_publication", "worker_start", "infrastructure_retry",
              "final_assembly", "final_seal", "result_promotion")
GENERATION_OPERATIONS = {"raw_draw", "salt_creation", "payload_seal"}
OP = "synthetic-operation"
LEAD = actor("research_lead", "synthetic-research_lead")
PUBLISHER = actor("publisher", "synthetic-publisher")
VERIFIER = actor("independent_integrity_verifier", "synthetic-integrity")


def build(tmp_path, *, through=("S", "W", "U", "C", "D", "F"), overrides=None, consume=True):
    """Synthetic operational tuple in stage order; it authorizes only test doubles."""
    overrides = overrides or {}
    records = {}
    for role in ("P", "I", "Q", "O", "V", "A", "R", "B", "G"):
        extra = {"operation_id": OP} if role == "G" else {}
        records[role] = fixture(role, records, **{**extra, **overrides.get(role, {})})
    boundary = fixture("GenerationBoundary", records, operation_id=OP, producer_fence_epoch=0)
    for role in through:
        extra = {}
        if role == "S":
            extra = {"operation_id": OP, "generation_boundary": record_ref(boundary)}
        elif role == "F":
            extra = {**classify_report(integrity=True, realized_positions=2, seat_a_positions=1,
                     seat_b_positions=1, statuses=dict.fromkeys("FDSH", "SUPPORTED"), gates_valid=True),
                     "counts": {"physical_cells": 900856, "started_attempts": 900856, "failed_attempts": 0,
                                "realized_revisions": 2, "realized_positions": 2,
                                "seat_positions": {"A": 1, "B": 1}}}
        records[role] = fixture(role, records, **{**extra, **overrides.get(role, {})})
    by_digest = {record["digest"]: record for record in (*records.values(), boundary)}
    actors = {record["body"]["actor"]["actor_id"]: record["body"]["actor"]["role"]
              for record in records.values() if "actor" in record["body"]}
    actors.update({VERIFIER["actor_id"]: VERIFIER["role"], PUBLISHER["actor_id"]: PUBLISHER["role"],
                   "synthetic-supervisor": "external_supervisor"})
    log = AuthorityLog(tmp_path / "authority", STUDY, {r: record_ref(v) for r, v in records.items()},
                       actors=actors, resolver=lambda ref: by_digest[ref["digest"]], source_check=lambda: None)
    log.append("ISSUE", LEAD, expected_tip=log.tip, operation_id=OP)
    if consume:
        root = tmp_path / "producer"
        root.mkdir()
        recorder = actor("recorder", "synthetic-recorder")
        log.register_producer(root, recorder, operation_id=OP)
        log.consume_generation(recorder, expected_tip=log.tip, operation_id=OP, evidence=[artifact()])
    return log, records


def run(log, operation, action):
    return log.protected(operation, expected_tip=log.tip,
                         operation_id=OP if operation in GENERATION_OPERATIONS else "synthetic-consumer",
                         action=action, consumer_actor=PUBLISHER)


@pytest.mark.parametrize("operation", OPERATIONS)
def test_every_consumer_runs_exactly_once_under_the_complete_current_tuple(tmp_path, operation):
    log, _ = build(tmp_path)
    leases = []
    assert run(log, operation, lambda lease: leases.append(lease) or operation) == operation
    assert len(leases) == 1 and leases[0].study_id == STUDY and leases[0].epoch == 0


@pytest.mark.parametrize("event", ["HOLD", "TERMINATE"])
@pytest.mark.parametrize("operation", OPERATIONS)
def test_every_consumer_denies_hold_and_terminal_for_that_reason_alone(tmp_path, operation, event):
    log, _ = build(tmp_path)
    log.append(event, VERIFIER if event == "HOLD" else LEAD, expected_tip=log.tip,
               operation_id="synthetic-consumer", evidence=[artifact()])
    with pytest.raises(IntegrityError, match="stale, held or terminal"):
        run(log, operation, lambda lease: pytest.fail("held or terminal consuming action"))


def test_publication_consumes_u_once_by_the_publisher_only(tmp_path):
    log, _ = build(tmp_path)
    with pytest.raises(IntegrityError):
        log.protected("commitment_publication", expected_tip=log.tip, operation_id="publish",
                      action=lambda lease: pytest.fail("no publisher"))
    with pytest.raises(IntegrityError):
        log.protected("commitment_publication", expected_tip=log.tip, operation_id="publish",
                      action=lambda lease: pytest.fail("lead is not the publisher"), consumer_actor=LEAD)
    assert log.protected("commitment_publication", expected_tip=log.tip, operation_id="publish",
                         action=lambda lease: "published", consumer_actor=PUBLISHER) == "published"
    with pytest.raises(IntegrityError, match="already consumed"):
        log.protected("commitment_publication", expected_tip=log.tip, operation_id="publish",
                      action=lambda lease: pytest.fail("second publication"), consumer_actor=PUBLISHER)


def uint64(label):
    return hashlib.sha256(label.encode()).hexdigest()[:16]


def private_study():
    """Independent synthetic private bytes with full-width values (no small decimal tokens)."""
    known, rejected = uint64("independent-known"), uint64("independent-rejected-candidate")
    positions = [{"position": i, "value_hex": uint64(f"independent-position-{i}")} for i in range(1, 1413)]
    raws = {"K": encode([known]), "E": encode([]), "L": encode({}),
            "payload": encode({"body": {"positions": positions}}),
            "audit": encode([{"raw_bytes_hex": value} for value in
                             (known, rejected, *(p["value_hex"] for p in positions))]),
            "salt": hashlib.sha256(b"independent-salt").digest()}
    refs = {name: {"bytes": len(raw), "sha256_raw": sha256(raw), "evidence_id": "independent-private-" + name,
                   "visibility": "PRIVATE"} for name, raw in raws.items()}
    commitment = sha256(b"bytefray-e9-seed-commitment-v2\n" + raws["salt"] + raws["payload"])
    return raws, refs, commitment, {"known": known, "rejected": rejected, "position": positions[0]["value_hex"]}


def publication(tmp_path, *, decision="AUTHORIZED"):
    raws, refs, commitment, _ = private_study()
    inventory = {name: refs[name] for name in ("K", "E", "L")}
    log, records = build(tmp_path, through=("S", "W"), overrides={
        "O": inventory, "A": inventory, "R": inventory,
        "S": {name: refs[name] for name in ("payload", "salt", "audit")},
        "W": {"commitment": commitment, "payload": refs["payload"], "salt": refs["salt"]}})
    for name, raw in raws.items():
        log.retain_artifact(raw, refs[name]["evidence_id"])
    draft = dict(records)
    draft["U"] = fixture("U", draft, commitment=commitment)
    proposed = copy.deepcopy(fixture("C", draft, commitment=commitment, decision=decision)["body"])
    del proposed["dependencies"]["U"]
    template = {"body": proposed, "digest": sha256(canonical_bytes(proposed)),
                "U_insertion_slot": "body.dependencies.U"}
    approval = fixture("U", records, commitment=commitment, active_authority_tip=log.tip,
                       approved_public_record_body=template)
    log.retain_record(approval)
    log.bindings = {**log.bindings, "U": record_ref(approval)}
    log.append("ISSUE", LEAD, expected_tip=log.tip, operation_id=OP)
    public = fixture("C", {**records, "U": approval}, commitment=commitment, decision=decision)
    return log, public


def test_publication_writes_exact_template_bytes_once_inside_single_use_u(tmp_path):
    log, public = publication(tmp_path)
    changed = make_record("C", {**public["body"], "decision": "CHANGED-AFTER-APPROVAL"})
    with pytest.raises(IntegrityError, match="template"):
        publish_commitment(log, changed, expected_tip=log.tip, operation_id="publish",
                           publisher=PUBLISHER, destination=tmp_path / "changed-C.json")
    assert not (tmp_path / "changed-C.json").exists()
    ref = publish_commitment(log, public, expected_tip=log.tip, operation_id="publish",
                             publisher=PUBLISHER, destination=tmp_path / "C.json")
    assert ref == record_ref(public)
    assert (tmp_path / "C.json").read_bytes() == canonical_bytes(public) + b"\n"
    with pytest.raises(IntegrityError, match="already consumed"):
        publish_commitment(log, public, expected_tip=log.tip, operation_id="publish",
                           publisher=PUBLISHER, destination=tmp_path / "second-C.json")
    assert not (tmp_path / "second-C.json").exists()


@pytest.mark.parametrize("leak", ["position", "position_upper", "position_decimal", "rejected", "known",
                                  "salt_hex", "salt_upper", "salt_base64", "authority_root"])
def test_publication_refuses_an_approved_template_exposing_actual_private_values(tmp_path, leak):
    import base64
    raws, _, _, values = private_study()
    salt = raws["salt"]
    text = {"position": values["position"], "position_upper": values["position"].upper(),
            "position_decimal": str(int(values["position"], 16)), "rejected": values["rejected"],
            "known": values["known"], "salt_hex": salt.hex(), "salt_upper": salt.hex().upper(),
            "salt_base64": base64.b64encode(salt).decode().rstrip("="),
            "authority_root": str((tmp_path / "authority").resolve()).replace("\\", "/")}[leak]
    log, public = publication(tmp_path, decision="AUTHORIZED; diagnostic " + text)
    with pytest.raises(IntegrityError, match="actual private"):
        publish_commitment(log, public, expected_tip=log.tip, operation_id="publish",
                           publisher=PUBLISHER, destination=tmp_path / "leaked-C.json")
    assert not (tmp_path / "leaked-C.json").exists()
    with log.exclusive():  # the refused publication never consumed the single-use U
        assert log.bindings["U"]["digest"] not in log._state()["consumed"]
    clean_log, clean = publication(tmp_path / "clean", decision="AUTHORIZED; diagnostic " + uint64("unrelated"))
    assert publish_commitment(clean_log, clean, expected_tip=clean_log.tip, operation_id="publish",
                              publisher=PUBLISHER, destination=tmp_path / "clean-C.json") == record_ref(clean)


@pytest.mark.parametrize("fault,match,consume", [
    ("mixed_study", "mixed study", True),
    ("mixed_KEL", "mixed original K/E/L", False),
    ("generic_waiver", "generic waiver", False),
    ("W_not_S_bytes", "W does not verify", True),
])
def test_consumers_reject_mixed_study_inventory_waiver_and_unbound_w(tmp_path, fault, match, consume):
    overrides = {"mixed_study": {"D": {"study_id": "other-synthetic-study"}},
                 "mixed_KEL": {"A": {"K": artifact("other-synthetic-K")}},
                 "generic_waiver": {"R": {"risk": "generic residual waiver accepted"}},
                 "W_not_S_bytes": {"W": {"payload": artifact("other-payload", private=True)}}}[fault]
    log, _ = build(tmp_path, overrides=overrides, consume=consume)
    operation = "raw_draw" if not consume else "worker_start"
    with pytest.raises(IntegrityError, match=match):
        log.protected(operation, expected_tip=log.tip, operation_id=OP,
                      action=lambda lease: pytest.fail("mixed or unbound consuming action"))


@pytest.mark.parametrize("fault", [None, "source_drift", "test_drift", "outside_repository", "protocol"])
def test_production_source_checker_rehashes_real_files_and_adoption(tmp_path, fault):
    source, test = "tools/research/v6/e9/v2/authority.py", "engine/tests/test_v6_e9_v2_independent_consumers.py"
    instrument = {"body": {"implementation_sources": {source: sha256((ROOT / source).read_bytes())}}}
    qualification = {"body": {"qualification_sources": {test: sha256((ROOT / test).read_bytes())}}}
    protocol = record_ref(read_record(ADOPTED, "P"))
    if fault == "source_drift":
        instrument["body"]["implementation_sources"][source] = "f" * 64
    elif fault == "test_drift":
        qualification["body"]["qualification_sources"][test] = "f" * 64
    elif fault == "outside_repository":
        outside = tmp_path / "outside.py"
        outside.write_bytes(b"synthetic")
        instrument["body"]["implementation_sources"] = {str(outside): sha256(b"synthetic")}
    elif fault == "protocol":
        protocol = {**protocol, "sha256_raw": "f" * 64}
    check = pinned_source_checker(ROOT, instrument, qualification, protocol)
    if fault is None:
        check()
    else:
        with pytest.raises(IntegrityError):
            check()


def overlap_receipt(*, mixed=False):
    proofs = [history_fixture(value=5)] + ([history_fixture(temporal="UNKNOWN", value=9)] if mixed else [])
    receipt = verify_history(accepted_raw=encode([{"position": 1, "value_hex": f"{5:016x}"}]),
        original_K_raw=encode(["0000000000000000"]), history_inputs=[raw for raw, _ in proofs],
        execution_inputs={k: v for _, execution in proofs for k, v in execution.items()},
        boundary_digest="a" * 64, verifier_id="independent-qualifier", producer_id="synthetic-recorder")
    assert receipt.disposition == "OVERLAP"
    return receipt


@pytest.mark.parametrize("mixed", [False, True])
@pytest.mark.parametrize("stage,through,kind,status", [
    ("GENERATED", ("S",), "TERMINATE", "CANCELLED_PRECOLLECTION_HISTORICAL_OVERLAP"),
    ("COMMITMENT_PUBLIC", ("S", "W", "U", "C"), "TERMINATE", "CANCELLED_PRECOLLECTION_HISTORICAL_OVERLAP"),
    ("COLLECTION", ("S", "W", "U", "C", "D"), "TERMINATE", "NOT EVALUABLE"),
    ("COLLECTED", ("S", "W", "U", "C", "D"), "TERMINATE", "NOT EVALUABLE"),
    ("FINAL_PUBLIC", ("S", "W", "U", "C", "D", "F"), "CORRECT", "INVALIDATED_HISTORICAL_OVERLAP"),
])
def test_persisted_post_generation_overlap_terminates_or_corrects_and_fences_all_consumers(
        tmp_path, stage, through, kind, status, mixed):
    log, records = build(tmp_path, through=through)
    ledger = DispatchLedger(tmp_path / "dispatch", log)
    controller = IntegrityController(log, verifier_actor=VERIFIER, lead_actor=LEAD, ledger=ledger)
    before = {role: canonical_bytes(record) for role, record in records.items()}
    result = controller.record(stage, overlap_receipt(mixed=mixed), expected_tip=log.tip, operation_id=OP,
                               evidence=[artifact("independent-overlap-adjudication")])
    assert result["decision"]["effective_status"] == status and result["decision"]["terminal"] is True
    event = result["event"]["body"]
    assert event["event_kind"] == kind and event["actor"] == LEAD
    assert event["affected_authorizations"] == [ref for r, ref in log.bindings.items() if r in {"G", "U", "D"}]
    assert {ref["schema"].rsplit(".", 1)[1] for ref in event["affected_authorizations"]} == {
        {"G": "generation_authorization", "U": "commitment_publication_authorization",
         "D": "payoff_authorization"}[r] for r in ("G", "U", "D") if r in records}
    notice = result["notice"]["body"]
    expected_originals = {r: record_ref(records[r]) for r in ("S", "C", "F") if r in records}
    assert notice["stage"] == stage and notice["original_records"] == expected_originals
    assert notice["immutable_original_F"] == expected_originals.get("F")
    assert notice["withdrawn_eligibility"] is True and notice["authority_event"] == record_ref(result["event"])
    for operation in OPERATIONS:
        with pytest.raises(IntegrityError):
            run(log, operation, lambda lease: pytest.fail("consumer after terminal integrity event"))
    with pytest.raises(IntegrityError):
        log.append("RELEASE", LEAD, expected_tip=log.tip, operation_id=OP, evidence=[artifact()])
    assert {role: canonical_bytes(record) for role, record in records.items()} == before


def suspicion_receipt():
    proof_raw, execution = history_fixture(temporal="UNKNOWN", value=5)
    return verify_history(accepted_raw=encode([{"position": 1, "value_hex": f"{6:016x}"}]),
        original_K_raw=encode(["0000000000000000"]), history_inputs=[proof_raw],
        execution_inputs=execution, boundary_digest="a" * 64,
        verifier_id="independent-qualifier", producer_id="synthetic-recorder")


@pytest.mark.parametrize("started,expected", [
    (False, "CANCELLED_PRECOLLECTION_UNRESOLVED_INTEGRITY"), (True, "NOT EVALUABLE")])
def test_unresolved_closure_reads_first_started_cell_from_the_durable_ledger(tmp_path, started, expected):
    log, _ = build(tmp_path, through=("S", "W", "U", "C", "D"))
    ledger = DispatchLedger(tmp_path / "dispatch", log)
    if started:
        def failed_launch(item, lease):
            raise RuntimeError("deterministic synthetic launch failure")
        with pytest.raises(RuntimeError):
            ledger.start("A", "RUSH8", 1, "A", expected_tip=log.tip, operation_id="synthetic-worker",
                         launch=failed_launch)
    receipt = suspicion_receipt()
    with pytest.raises(IntegrityError, match="durable attempt ledger"):
        IntegrityController(log, verifier_actor=VERIFIER, lead_actor=LEAD).record(
            "COMMITMENT_PUBLIC", receipt, expected_tip=log.tip, operation_id=OP,
            evidence=[artifact()], close_unresolved=True)
    controller = IntegrityController(log, verifier_actor=VERIFIER, lead_actor=LEAD, ledger=ledger)
    result = controller.record("COMMITMENT_PUBLIC", receipt, expected_tip=log.tip, operation_id=OP,
                               evidence=[artifact()], close_unresolved=True)
    assert result["decision"]["effective_status"] == expected
    assert result["event"]["body"]["event_kind"] == "TERMINATE"


def test_failed_launch_retains_started_attempt_and_is_never_retried_automatically(tmp_path):
    log, _ = build(tmp_path, through=("S", "W", "U", "C", "D"))
    ledger = DispatchLedger(tmp_path / "dispatch", log)

    def failed_launch(item, lease):
        raise RuntimeError("deterministic synthetic launch failure")
    with pytest.raises(RuntimeError):
        ledger.start("A", "RUSH8", 1, "A", expected_tip=log.tip, operation_id="synthetic-worker",
                     launch=failed_launch)
    cell = next((tmp_path / "dispatch").iterdir())
    started = json.loads((cell / "attempt-1.json").read_bytes())
    assert started["attempt"] == 1 and started["cell"] == {"row": "A", "opponent": "RUSH8",
                                                           "position": 1, "seat": "A"}
    with pytest.raises(IntegrityError):
        ledger.start("A", "RUSH8", 1, "A", expected_tip=log.tip, operation_id="synthetic-worker",
                     launch=lambda item, lease: pytest.fail("automatic relaunch"))
    assert ledger.first_cell_started() is True


def packet(text):
    return {name: ("independent " + text).encode() for name in ARTIFACT_NAMES}


def test_registered_recovery_pair_yields_one_usable_recovery_completion(tmp_path):
    log, ledger, _, facts = begin(tmp_path)
    second = ledger.start("A", "RUSH8", 1, "A", expected_tip=log.tip, operation_id="independent-worker",
        launch=lambda item, lease: None, retry_facts=facts, failure_receipt=proof(ledger, facts))
    receipt = ledger.complete(facts["cell_identity"], 2, second["lease"], artifacts=packet("recovery"))
    assert receipt["eligible"] is True
    assert ledger.usable_completion(facts["cell_identity"]) == receipt


def test_conflicting_original_completion_after_recovery_makes_block_unusable_and_keeps_every_packet(tmp_path):
    log, ledger, result, facts = begin(tmp_path)
    second = ledger.start("A", "RUSH8", 1, "A", expected_tip=log.tip, operation_id="independent-worker",
        launch=lambda item, lease: None, retry_facts=facts, failure_receipt=proof(ledger, facts))
    recovery = ledger.complete(facts["cell_identity"], 2, second["lease"], artifacts=packet("recovery"))
    assert recovery["eligible"] is True
    late = ledger.complete(facts["cell_identity"], 1, result["lease"], artifacts=packet("late original"))
    other = ledger.complete(facts["cell_identity"], 1, result["lease"], artifacts=packet("other late original"))
    assert late["eligible"] is False and other["eligible"] is False
    marker = json.loads((ledger.root / facts["cell_identity"] / "unusable.json").read_bytes())
    assert marker["reason"] == "original attempt completed after recovery started"
    with pytest.raises(IntegrityError, match="unusable"):
        ledger.usable_completion(facts["cell_identity"])
    retained = {path.read_bytes() for path in (log.root / "retained").glob("*.bin")}
    assert retained == {b"independent recovery", b"independent late original", b"independent other late original"}
    assert len(list((log.root / "retained").glob("*.bin"))) == 12


def test_completion_after_recorded_failure_makes_block_unusable_and_blocks_recovery(tmp_path):
    log, ledger, result, facts = begin(tmp_path)
    failure = proof(ledger, facts)
    receipt = ledger.complete(facts["cell_identity"], 1, result["lease"], artifacts=packet("conflicting"))
    assert receipt["eligible"] is False
    with pytest.raises(IntegrityError):
        ledger.start("A", "RUSH8", 1, "A", expected_tip=log.tip, operation_id="independent-worker",
            launch=lambda item, lease: pytest.fail("recovery after conflicting completion"),
            retry_facts=facts, failure_receipt=failure)
    with pytest.raises(IntegrityError, match="unusable"):
        ledger.usable_completion(facts["cell_identity"])


def test_identical_duplicate_completion_is_retained_without_conflict(tmp_path):
    _, ledger, result, facts = begin(tmp_path)
    first = ledger.complete(facts["cell_identity"], 1, result["lease"], artifacts=packet("complete"))
    duplicate = ledger.complete(facts["cell_identity"], 1, result["lease"], artifacts=packet("complete"))
    assert first["eligible"] is True and duplicate == first
    assert ledger.usable_completion(facts["cell_identity"]) == first
    changed = ledger.complete(facts["cell_identity"], 1, result["lease"], artifacts=packet("changed"))
    assert changed["eligible"] is False
    with pytest.raises(IntegrityError, match="unusable"):
        ledger.usable_completion(facts["cell_identity"])


@pytest.mark.parametrize("history,change", [
    ("HISTORICAL_OVERLAP", {"effective_registered_status": "SUPPORTED beneficial adaptation"}),
    ("HISTORICAL_OVERLAP", {"requirement_C": "ESTABLISHED in the registered bounded scope with "
                                             "permanent historical non-reuse limitation"}),
    ("HOLD_PENDING_ADJUDICATION", {"effective_registered_status": "NOT EVALUABLE"}),
    ("INTACT", {"requirement_C": "NOT ESTABLISHED"}),
])
def test_final_sealer_refuses_fields_that_contradict_historical_precedence(tmp_path, history, change):
    from tools.research.v6.e9.v2.reporting import seal_final
    records = through_g()
    records["S"] = fixture("S", records, generation_boundary=record_ref(fixture("GenerationBoundary", records)))
    for role in ("W", "U", "C", "D"):
        records[role] = fixture(role, records)
    finding = classify_report(integrity=True, realized_positions=2, seat_a_positions=1, seat_b_positions=1,
        statuses=dict.fromkeys("FDSH", "SUPPORTED"), gates_valid=True, historical_integrity=history)
    counts = {"physical_cells": 900856, "started_attempts": 900856, "failed_attempts": 0,
              "realized_revisions": 2, "realized_positions": 2, "seat_positions": {"A": 1, "B": 1}}
    body = fixture("F", records, **finding, counts=counts)["body"]
    assert seal_final(tmp_path / "consistent-F.json", body)
    with pytest.raises(IntegrityError, match="contradict"):
        seal_final(tmp_path / "contradictory-F.json", {**body, **change})
    assert not (tmp_path / "contradictory-F.json").exists()


def test_prefix_records_never_bind_completed_payload_records():
    records = through_g()
    records["GenerationBoundary"] = fixture("GenerationBoundary", records)
    snapshot = fixture("PrefixSnapshot", records)
    S = fixture("S", records, generation_boundary=record_ref(records["GenerationBoundary"]))
    body = copy.deepcopy(snapshot["body"])
    body["dependencies"]["S"] = record_ref(S)
    with pytest.raises(IntegrityError):
        make_record("PrefixSnapshot", body)


def test_qualification_runs_under_the_entropy_and_producer_guard(request):
    """Self-check of the audited harness; skipped only outside it."""
    name = "tools.research.v6.e9.v2.qualification_guard"
    if not request.config.pluginmanager.has_plugin(name):
        pytest.skip("guard plugin inactive: not an audited qualification run")
    from battle_engine.match_service import NativeMatchService
    from battle_engine.process_runtime import ProcessMatchController

    from tools.research.v6.e9 import analysis
    from tools.research.v6.e9.v2 import qualification_guard
    guarded = (os.urandom, random._urandom, secrets.token_bytes, secrets.randbits, secrets.randbelow,
               NativeMatchService.run, ProcessMatchController.run, analysis.uncertainty,
               analysis.registered_uncertainty)
    assert all(target is qualification_guard.forbidden for target in guarded)


def final_body(**statuses):
    records = through_g()
    records["S"] = fixture("S", records, generation_boundary=record_ref(fixture("GenerationBoundary", records)))
    for role in ("W", "U", "C", "D"):
        records[role] = fixture(role, records)
    finding = classify_report(integrity=True, realized_positions=2, seat_a_positions=1, seat_b_positions=1,
        statuses={**dict.fromkeys("FDSH", "SUPPORTED"), **statuses}, gates_valid=True)
    counts = {"physical_cells": 900856, "started_attempts": 900856, "failed_attempts": 0,
              "realized_revisions": 2, "realized_positions": 2, "seat_positions": {"A": 1, "B": 1}}
    return fixture("F", records, **finding, counts=counts)["body"]


REFUTED = "REFUTED bounded benefit claim"
NOT_ESTABLISHED = {"requirement_C_eligible": False, "requirement_C": "NOT ESTABLISHED"}


@pytest.mark.parametrize("change", [
    {"scientific_classification": REFUTED, "effective_registered_status": REFUTED,
     "F_D_S_H_statuses": dict.fromkeys("FDSH", "REFUTED")},
    {"F_D_S_H_statuses": {**dict.fromkeys("FDSH", "SUPPORTED"), "F": "UNRESOLVED"}},
    {"scientific_priority_row": 4, "scientific_classification": REFUTED,
     "effective_registered_status": REFUTED, **NOT_ESTABLISHED},
    {"scientific_priority_row": None, **NOT_ESTABLISHED},
])
def test_sealer_rejects_row7_c_eligibility_that_the_frozen_table_does_not_reproduce(tmp_path, change):
    from tools.research.v6.e9.v2.reporting import seal_final
    body = final_body()
    assert body["scientific_priority_row"] == 7 and body["requirement_C_eligible"] is True
    with pytest.raises(IntegrityError, match="frozen table|precedence"):
        seal_final(tmp_path / "unreproduced-F.json", {**body, **change})
    assert not (tmp_path / "unreproduced-F.json").exists()
    refuted = final_body(F="REFUTED")
    assert (refuted["scientific_priority_row"], refuted["scientific_classification"]) == (4, REFUTED)
    assert seal_final(tmp_path / "row4-F.json", refuted)


def test_partial_packet_without_terminal_result_keeps_the_recovery_route_open(tmp_path):
    log, ledger, result, facts = begin(tmp_path)
    partial = ledger.complete(facts["cell_identity"], 1, result["lease"],
                              artifacts={"trace.jsonl": b"independent interrupted partial trace"})
    assert partial["eligible"] is False
    cell = ledger.root / facts["cell_identity"]
    assert not (cell / "completion-1.json").exists() and len(list(cell.glob("partial-1-*.json"))) == 1
    second = ledger.start("A", "RUSH8", 1, "A", expected_tip=log.tip, operation_id="independent-worker",
        launch=lambda item, lease: None, retry_facts=facts, failure_receipt=proof(ledger, facts))
    recovery = ledger.complete(facts["cell_identity"], 2, second["lease"], artifacts=packet("recovered"))
    assert ledger.usable_completion(facts["cell_identity"]) == recovery
    assert (log.root / "retained").exists() and b"independent interrupted partial trace" in {
        path.read_bytes() for path in (log.root / "retained").glob("*.bin")}


def test_any_terminal_result_evidence_or_output_after_failure_blocks_recovery(tmp_path):
    _, ledger, result, facts = begin(tmp_path)
    ledger.complete(facts["cell_identity"], 1, result["lease"], artifacts={"result.json": b"independent result"})
    with pytest.raises(IntegrityError):
        proof(ledger, facts)
    log2, ledger2, result2, facts2 = begin(tmp_path / "second")
    failure = proof(ledger2, facts2)
    ledger2.complete(facts2["cell_identity"], 1, result2["lease"], artifacts={"trace.jsonl": b"late output"})
    marker = json.loads((ledger2.root / facts2["cell_identity"] / "unusable.json").read_bytes())
    assert marker["reason"] == "attempt delivered output after its recorded infrastructure failure"
    with pytest.raises(IntegrityError):
        ledger2.start("A", "RUSH8", 1, "A", expected_tip=log2.tip, operation_id="independent-worker",
            launch=lambda item, lease: pytest.fail("recovery after late output"),
            retry_facts=facts2, failure_receipt=failure)


def test_payload_cannot_seal_a_stale_preceding_chain_tip(tmp_path, monkeypatch):
    from engine.tests.test_v6_e9_v2_independent_generation import producer_fixture
    generator, log, _, _, _, calls, salt_calls, _, _ = producer_fixture(tmp_path, monkeypatch, [1])
    generator.consume(expected_tip=log.tip, boundary_evidence=artifact("boundary"))
    generator.draw_one(expected_tip=log.tip, durable_instant=artifact("boundary"))
    with pytest.raises(IntegrityError, match="preceding chain tip"):
        generator.complete(expected_tip=log.tip, preceding_chain_tip="f" * 64)
    with pytest.raises(IntegrityError, match="preceding chain tip"):
        generator.seal_payload(expected_tip=log.tip, preceding_chain_tip="f" * 64)
    with pytest.raises(IntegrityError, match="complete accepted list"):
        generator.seal_payload(expected_tip=log.tip, preceding_chain_tip=log.tip)
    assert calls == [8] and salt_calls == []


POST_GENERATION = [
    ("GENERATED", ("S",)), ("COMMITMENT_PUBLIC", ("S", "W", "U", "C")),
    ("COLLECTION", ("S", "W", "U", "C", "D")), ("COLLECTED", ("S", "W", "U", "C", "D")),
    ("FINAL_PUBLIC", ("S", "W", "U", "C", "D", "F")),
]


def adjudicate_hold(log, controller, stage, **proof):
    boundary = log.resolve(log.bindings["S"])["body"]["generation_boundary"]["digest"]
    proof_raw, execution = history_fixture(boundary=boundary, **{"value": 5, **proof})
    return controller.verify_disposition(stage, accepted_raw=encode([{"position": 1, "value_hex": f"{5:016x}"}]),
        original_K_raw=encode(["0000000000000000"]), history_inputs=[proof_raw], execution_inputs=execution,
        boundary_digest=boundary, expected_tip=log.tip, producer_id="synthetic-recorder")


@pytest.mark.parametrize("finding", ["NOT_EXECUTED", "POST_BOUNDARY"])
@pytest.mark.parametrize("stage,through", POST_GENERATION)
def test_released_hold_after_conclusive_disproval_resumes_every_consumer(tmp_path, stage, through, finding):
    """H1: the suspicion about accepted position 1 is disproved, so the study is not closed."""
    log, records = build(tmp_path, through=through)
    before = {role: canonical_bytes(record) for role, record in records.items()}
    controller = IntegrityController(log, verifier_actor=VERIFIER, lead_actor=LEAD,
                                     ledger=DispatchLedger(tmp_path / "dispatch", log))
    log.append("HOLD", VERIFIER, expected_tip=log.tip, operation_id=OP, evidence=[artifact("independent-suspicion")])
    for operation in OPERATIONS:
        with pytest.raises(IntegrityError):
            run(log, operation, lambda lease: pytest.fail("consumer during the hold"))
    adjudicated = adjudicate_hold(log, controller, stage, **(
        {"actual": False, "disproval": "NOT_EXECUTED"} if finding == "NOT_EXECUTED" else {"temporal": "AFTER"}))
    released = controller.release(stage, adjudicated["receipt"], expected_tip=log.tip, operation_id=OP,
                                  evidence=adjudicated["evidence"], original_bindings_valid=True)
    assert released["event"]["body"]["event_kind"] == "RELEASE"
    assert released["notice"]["body"]["withdrawn_eligibility"] is False
    for operation, roles in OPERATION_ROLES.items():
        if set(roles) <= set(log.bindings):
            assert run(log, operation, lambda lease, name=operation: name) == operation
    assert {role: canonical_bytes(record) for role, record in records.items()} == before


def test_release_without_new_history_needs_an_independent_conclusive_receipt(tmp_path):
    log, _ = build(tmp_path, through=("S", "W", "U", "C", "D"))
    controller = IntegrityController(log, verifier_actor=VERIFIER, lead_actor=LEAD)
    hold = log.append("HOLD", VERIFIER, expected_tip=log.tip, operation_id=OP, evidence=[artifact("independent-suspicion")])
    for unreleasable in ({"temporal": "UNKNOWN", "label": "-uncertain"}, {"value": 7}):
        adjudicated = adjudicate_hold(log, controller, "COLLECTION", **unreleasable)
        with pytest.raises(IntegrityError):  # suspicion stays held; new history needs a PG-R8 supplement
            controller.release("COLLECTION", adjudicated["receipt"], expected_tip=log.tip, operation_id=OP,
                               evidence=adjudicated["evidence"], original_bindings_valid=True)
    disproved = adjudicate_hold(log, controller, "COLLECTION", actual=False, disproval="NOT_EXECUTED")
    with pytest.raises(IntegrityError, match="disposition receipt"):
        controller.release("COLLECTION", disproved["receipt"], expected_tip=log.tip, operation_id=OP,
                           evidence=disproved["evidence"][1:], original_bindings_valid=True)
    with pytest.raises(IntegrityError, match="raw historical inputs"):
        controller.release("COLLECTION", disproved["receipt"], expected_tip=log.tip, operation_id=OP,
                           evidence=disproved["evidence"][:1], original_bindings_valid=True)
    with pytest.raises(IntegrityError):
        controller.release("BEFORE_GENERATION", disproved["receipt"], expected_tip=log.tip, operation_id=OP,
                           evidence=disproved["evidence"], original_bindings_valid=True)
    with pytest.raises(IntegrityError, match="independent"):
        IntegrityController(log, verifier_actor=LEAD, lead_actor=LEAD).verify_disposition(
            "COLLECTION", accepted_raw=encode([{"position": 1, "value_hex": f"{5:016x}"}]),
            original_K_raw=encode(["0000000000000000"]), history_inputs=[], execution_inputs={},
            boundary_digest="a" * 64, expected_tip=log.tip, producer_id="synthetic-recorder")
    # A CONTINUE cannot carry a disproval: continuation needs the PG-R8 supplement.
    log.retain_record(hold)
    body = {"record_role": "LeadContinuation", "study_id": STUDY, "actor": LEAD, "decision": "AUTHORIZED",
            "dependencies": {**log.bindings, "AuthorityEvent": record_ref(hold)}, "evidence": disproved["evidence"],
            "disposition": "CONTINUE", "operation_id": OP, "scope": "synthetic forged continuation",
            "still_incomplete_scope": "Historical coverage remains NOT ESTABLISHED.",
            "unchanged_original_tuple": log.bindings}
    forged = make_record("LeadContinuation", body)
    lead_raw = canonical_bytes(forged) + b"\n"
    lead_ref = {"bytes": len(lead_raw), "sha256_raw": sha256(lead_raw), "evidence_id": "forged-lead",
                "visibility": "PRIVATE"}
    with pytest.raises(IntegrityError, match="supplement"):
        log.append("CONTINUE", LEAD, expected_tip=log.tip, operation_id=OP,
                   evidence=[*disproved["evidence"], lead_ref], release_record=forged)
    with log.exclusive():
        assert log._state()["held"] is True
    controller.release("COLLECTION", disproved["receipt"], expected_tip=log.tip, operation_id=OP,
                       evidence=disproved["evidence"], original_bindings_valid=True)
    with log.exclusive():
        assert log._state()["held"] is False


@pytest.mark.parametrize("lead_identity", ["unregistered-lead", "synthetic-custodian"])
def test_absent_T_requires_the_registered_lead_not_applicable_disposition(tmp_path, lead_identity):
    attestation = {"actor": actor("custodian", "synthetic-custodian"),
                   "inspection_boundary": artifact("synthetic-custodian-boundary"),
                   "T_disposition": {**t_not_applicable(), "actor": actor("research_lead", lead_identity)}}
    log, _ = build(tmp_path, overrides={"O": {"custodian_attestation": attestation}}, consume=False)
    with pytest.raises(IntegrityError, match="NOT_APPLICABLE"):
        log.protected("raw_draw", expected_tip=log.tip, operation_id=OP,
                      action=lambda lease: pytest.fail("draw under an unattributed T disposition"))


@pytest.mark.parametrize("fault", ["absent", "both", "not_applicable_value", "custodian_actor", "no_reason",
                                   "no_evidence", "extra_attestation_field"])
def test_inventory_seal_binds_T_or_the_explicit_not_applicable_disposition(fault):
    records = through_g()
    attestation = copy.deepcopy(records["O"]["body"]["custodian_attestation"])
    body = copy.deepcopy(records["O"]["body"])
    disposition = attestation["T_disposition"]
    if fault == "absent":
        del attestation["T_disposition"]
    elif fault == "both":
        records["T"] = fixture("T", records)
        body["dependencies"]["T"] = record_ref(records["T"])
    elif fault == "not_applicable_value":
        disposition["disposition"] = "ABSENT"
    elif fault == "custodian_actor":
        disposition["actor"] = actor("custodian", "synthetic-custodian")
    elif fault == "no_reason":
        disposition["reason"] = " "
    elif fault == "no_evidence":
        del disposition["evidence"]
    else:
        attestation["unbound_note"] = "synthetic"
    body["custodian_attestation"] = attestation
    with pytest.raises(IntegrityError):
        make_record("O", body)
    assert records["O"]["body"]["custodian_attestation"]["T_disposition"]["disposition"] == "NOT_APPLICABLE"


def test_protected_final_seal_reproduces_the_row_only_under_current_final_authority(tmp_path):
    from tools.research.v6.e9.v2.scientific import seal_final_protected
    log, records = build(tmp_path)
    body = records["F"]["body"]
    assert body["scientific_priority_row"] == 7 and body["counts"]["realized_revisions"] == 2
    with pytest.raises(IntegrityError, match="frozen table"):
        seal_final_protected(log, tmp_path / "contradictory-F.json", {**body, "qualifiers": ["seat dependence"]},
                             expected_tip=log.tip, operation_id="synthetic-final")
    assert seal_final_protected(log, tmp_path / "F.json", body, expected_tip=log.tip,
                                operation_id="synthetic-final")
    log.append("HOLD", VERIFIER, expected_tip=log.tip, operation_id=OP, evidence=[artifact("independent-hold")])
    with pytest.raises(IntegrityError, match="held"):
        seal_final_protected(log, tmp_path / "held-F.json", body, expected_tip=log.tip,
                             operation_id="synthetic-final")
    assert not (tmp_path / "contradictory-F.json").exists() and not (tmp_path / "held-F.json").exists()
