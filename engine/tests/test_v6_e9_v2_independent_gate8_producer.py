"""Independent Gate-8 W-producer qualification: W-01 to W-14 of v2_gate8_scope_01.json.

Written from the write-once Gate-8 scope record (v6-e9-v2-gate8-scope-eae9f407f5d1), its lead
confirmation (including the D3 clarification), the frozen rule contract and the record
schemas, not from the implementer's Gate-8 tests or the producer's internal decision path.
Expected outcomes come from those texts and from independent reference calculations in this
module: the primitive commitment, the raw-audit chain, the draw-time authority tips, the
hand-listed gap-free supplement/continuation chain and the private-value representation set.

D4 provenance, recorded here and outside the frozen-shape entropy declaration. Every
REAL-labelled study in this module is a synthetic qualification fixture: its study is
"synthetic-e9-v2-only", its actors are synthetic, its uint64 values are hash-derived
synthetic numbers, and its 32-byte stand-in for the salt is a literal test constant. Each
fixture exists only inside a pytest temporary root. REAL appears only as an input
declaration with the frozen generation.entropy_declaration shape. No fixture consumes REAL
entropy, calls Generator.draw_one or Generator.complete in REAL mode, invokes
salt_creation, writes salt.bin or makes an entropy source return bytes. A REAL-mode
Generator is constructed only as a passive producer registrar and paused-prefix reader. The
injected SYNTHETIC Generator appears only in the W-11 boundary-layout parity check. None of
this material is operational evidence, and no real-study path accepts it.

No REAL entropy was consumed. REAL was represented only as an input declaration inside
synthetic qualification fixtures.
"""

from __future__ import annotations

import ast
import base64
import hashlib
import inspect
import json
import os
import random
import re
import secrets
import shutil
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any

import pytest

from engine.tests._e9_v2_synthetic_records import STUDY, actor, fixture, through_g
from tools.research.v6.e9.v2 import private_verification as pv
from tools.research.v6.e9.v2.authority import AuthorityLog
from tools.research.v6.e9.v2.commitment import publish_commitment, verify_W_bytes
from tools.research.v6.e9.v2.generation import Generator, entropy_declaration
from tools.research.v6.e9.v2.integrity import IntegrityController
from tools.research.v6.e9.v2.inventory import revealed_lists
from tools.research.v6.e9.v2.qualification_guard import forbidden
from tools.research.v6.e9.v2.records import (
    IntegrityError,
    make_record,
    record_ref,
    validate_record,
)

ROOT = Path(__file__).resolve().parents[2]
FROZEN = ROOT / "tools/research/v6/e9"
CATALOGUE = json.loads((FROZEN / "amended_record_schemas_v2_proposed_02.json").read_bytes())
CONTRACT = json.loads((FROZEN / "amended_rule_contract_v2_proposed_02.json").read_bytes())

# Frozen schema facts, read from the catalogue and contract rather than from the instrument.
W_DEPENDENCIES = tuple(CATALOGUE["records"]["W"]["record_reference_dependencies"])  # P..G, S
U_DEPENDENCIES = tuple(CATALOGUE["records"]["U"]["record_reference_dependencies"])  # .., W
THROUGH_G = W_DEPENDENCIES[:-1]
COMMITMENT_DOMAIN = CATALOGUE["primitive_commitment"]["domain"].encode("utf-8")
DOMAIN = CATALOGUE["records"]["SeedPayload"]["required_body_fields"]["domain"]
PERMANENT_LIMITATION = CONTRACT["exact_interpretation"]["permanent_limitation_text"]
N = 1412

OP = "synthetic-operation"
PV_OP = "synthetic-private-verification"
OUTCOME_KEYS = {"attempt", "outcome", "reason", "W", "interrupted_prior_attempts"}
SMALL_K = (0, 1, 2, 3, 5, 7, 42, 6, 8, 9, 256, 1412)
PAUSES = (4, 9)
# Literal synthetic test bytes standing in for the 32-byte salt: never salt_creation and
# never salt.bin. Hex letters only, digit-free in both base64 alphabets, and the standard and
# URL-safe base64 forms differ.
SALT = bytes.fromhex("fbefbeffffffaaaaaaaaafcfaabcfeaacccdaadbeeaaebcbaafaecabeabfcaaa")

LEAD = actor("research_lead", "synthetic-research_lead")
RECORDER = actor("recorder", "synthetic-recorder")
INTEGRITY = actor("independent_integrity_verifier", "synthetic-integrity")
VERIFIER = actor("independent_verifier", "synthetic-private-verifier")
CHECKER = actor("independent_verifier", "synthetic-template-checker")
SECOND_CHECKER = actor("independent_verifier", "synthetic-second-template-checker")
PUBLISHER = actor("publisher", "synthetic-publisher")
ACTORS = (LEAD, RECORDER, INTEGRITY, VERIFIER, CHECKER, SECOND_CHECKER, PUBLISHER)


def encode(value: Any) -> bytes:
    """Frozen digest convention: UTF-8 canonical JSON, sorted keys, compact, then one LF."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                      allow_nan=False).encode("utf-8") + b"\n"


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def body_digest(value: Any) -> str:
    return sha(encode(value)[:-1])


def private_ref(raw: bytes, evidence_id: str) -> dict:
    return {"bytes": len(raw), "evidence_id": evidence_id, "sha256_raw": sha(raw),
            "visibility": "PRIVATE"}


NOTICE_RAW = b"synthetic public commitment notice\n"
PUBLIC_NOTICE = {"bytes": len(NOTICE_RAW), "evidence_id": "synthetic/public-commitment-notice",
                 "sha256_raw": sha(NOTICE_RAW), "visibility": "PUBLIC"}


def uint64(label: str) -> str:
    """A full-width synthetic uint64 (top bit set) derived from a label; never a draw."""
    value = int.from_bytes(hashlib.sha256(label.encode()).digest()[:8], "big")
    return f"{value | 1 << 63:016x}"


def realistic_K() -> list[str]:
    """Small public literals plus the complete pinned E6/E8 revealed lists (N1-01)."""
    lists = revealed_lists()
    return sorted({f"{n:016x}" for n in SMALL_K} | lists["E6"] | lists["E8"])


def positions(values: list[str]) -> list[dict]:
    return [{"position": index, "value_hex": value} for index, value in enumerate(values, 1)]


@dataclass
class Study:
    """One synthetic qualification study; REAL appears only as its boundary declaration."""

    root: Path
    log: AuthorityLog
    records: dict
    by_digest: dict
    flags: dict
    K: list
    K_raw: bytes
    refs: dict
    producer_root: Path | None = None
    producer_ref: dict | None = None
    generator: Any = None
    durable_ref: dict | None = None
    consume_tip: str = ""
    boundary: dict | None = None
    audit_tip: str = ""
    entries: list = field(default_factory=list)
    accepted: list = field(default_factory=list)
    draw_tips: list = field(default_factory=list)
    chain: list = field(default_factory=list)
    segments: list = field(default_factory=list)
    history: set = field(default_factory=set)
    files_written: int = 0
    payload: dict | None = None
    payload_raw: bytes = b""
    audit_raw: bytes = b""
    salt_raw: bytes = SALT
    S: dict | None = None
    issue_S: dict | None = None


def authority(path: Path, bindings: dict, by_digest: dict, flags: dict,
              actors: dict) -> AuthorityLog:
    def source_check() -> None:
        if flags["source_drift"]:
            raise IntegrityError("instrument/qualification source pin drift (synthetic fault)")
    return AuthorityLog(path, STUDY, bindings, actors=actors,
                        resolver=lambda ref: by_digest[ref["digest"]], source_check=source_check)


def new_study(root: Path, *, K: list[str] | None = None) -> Study:
    K = realistic_K() if K is None else sorted(K)
    raws = {"K": encode(K), "E": encode([]), "L": encode({})}
    refs = {name: private_ref(raw, "synthetic-original-" + name) for name, raw in raws.items()}
    records = through_g(inventory_refs=refs)
    by_digest = {record["digest"]: record for record in records.values()}
    actors = {record["body"]["actor"]["actor_id"]: record["body"]["actor"]["role"]
              for record in records.values() if "actor" in record["body"]}
    actors.update({who["actor_id"]: who["role"] for who in ACTORS})
    flags = {"source_drift": False}
    log = authority(root / "authority", {role: record_ref(r) for role, r in records.items()},
                    by_digest, flags, actors)
    log.append("ISSUE", LEAD, expected_tip=log.tip, operation_id=OP)
    for name, raw in raws.items():
        log.retain_artifact(raw, refs[name]["evidence_id"])
    return Study(root=root, log=log, records=dict(records), by_digest=by_digest, flags=flags,
                 K=K, K_raw=raws["K"], refs=refs)


def register(study: Study, *, reader: bool = False) -> None:
    """Register the original producer root; a REAL Generator is only a passive registrar."""
    study.producer_root = study.root / "producer"
    study.producer_root.mkdir(parents=True)
    if reader:
        study.generator = Generator(study.producer_root, study.log, operation_id=OP,
                                    recorder=RECORDER, original_K_raw=study.K_raw,
                                    inventory_refs=study.refs, draw_bytes=None, salt_bytes=None,
                                    mode="REAL")
        study.producer_ref = study.generator.producer_ref
    else:
        study.producer_ref = study.log.register_producer(study.producer_root, RECORDER,
                                                         operation_id=OP)


def consume(study: Study, *, consumed: bool = True) -> None:
    instant = encode({"kind": "SYNTHETIC_QUALIFICATION_DURABLE_INSTANT", "study_id": STUDY})
    study.durable_ref = study.log.retain_artifact(instant, "SYNTHETIC-DURABLE-INSTANT")
    if consumed:
        study.log.consume_generation(RECORDER, expected_tip=study.log.tip, operation_id=OP,
                                     evidence=[study.durable_ref])
    study.consume_tip = study.log.tip


def declaration(study: Study, *, mode: str = "REAL", G: dict | None = None) -> bytes:
    """Frozen ENTROPY_SOURCE_V2 shape, written independently of generation.py."""
    source = {"REAL": "os.urandom", "SYNTHETIC": "injected deterministic synthetic byte stream"}
    return encode({"kind": "ENTROPY_SOURCE_V2", "mode": mode, "draw_source": source[mode],
                   "salt_source": source[mode], "study_id": STUDY,
                   "G": study.log.bindings["G"] if G is None else G, "operation_id": OP})


def fencing(study: Study) -> list[dict]:
    """Boundary evidence as the sealed producer lays it out: registry, marker, declaration."""
    marker = study.log.mark_first_raw(study.producer_ref)
    real = study.log.retain_artifact(declaration(study),
                                     "ENTROPY-SOURCE-" + study.log.bindings["G"]["digest"])
    return [study.producer_ref, marker, real]


def write_boundary(study: Study, evidence: list[dict] | None = None, *,
                   own_root: bool = True) -> None:
    body = {"record_role": "GenerationBoundary", "study_id": STUDY, "actor": RECORDER,
            "decision": "RECORDED", "dependencies": dict(study.log.bindings),
            "evidence": fencing(study) if evidence is None else evidence,
            "active_authority_tip": study.consume_tip, "durable_instant": study.durable_ref,
            "operation_id": OP, "producer_fence_epoch": 0}
    study.boundary = make_record("GenerationBoundary", body)
    study.log.retain_record(study.boundary)
    if own_root:  # clones share their base's producer root and never write into it
        (study.producer_root / "boundary.json").write_bytes(encode(study.boundary))
    study.audit_tip = study.boundary["digest"]
    study.draw_tips = [study.consume_tip]


def accepted_values(study: Study, count: int = N, *, exclude: Any = ()) -> list[str]:
    taken, values, index = set(study.K) | set(exclude), [], 0
    while len(values) < count:
        value = uint64(f"synthetic-gate8-accepted-{index}")
        index += 1
        if value not in taken:
            taken.add(value)
            values.append(value)
    return values


def raw_sequence(study: Study, accepted: list[str]) -> list[str]:
    """One original-K rejection and one duplicate rejection ahead of the accepted list."""
    return [study.K[-1], accepted[0], accepted[0], *accepted[1:]]


def draw(study: Study, values: list[str], *, force_accept: Any = ()) -> None:
    """Hand-built raw audit entries under the current draw-time authority tip."""
    K, accepted = set(study.K), set(study.accepted)
    for value in values:
        if value in K and value not in force_accept:
            disposition = "REJECT_K"
        elif value in accepted:
            disposition = "REJECT_DUPLICATE"
        else:
            disposition = "ACCEPT"
        entry = {"raw_draw_ordinal": len(study.entries) + 1, "raw_bytes_hex": value,
                 "disposition": disposition,
                 "accepted_position": len(study.accepted) + 1 if disposition == "ACCEPT" else None,
                 "authority_tip": study.draw_tips[-1], "prior_entry_digest": study.audit_tip}
        study.entries.append(entry)
        study.audit_tip = body_digest(entry)
        if disposition == "ACCEPT":
            study.accepted.append(value)
            accepted.add(value)


def write_draw_files(study: Study) -> None:
    """Intent/audit files for the passive reader's paused prefix (plain writes, no fsync)."""
    for entry in study.entries[study.files_written:]:
        ordinal = entry["raw_draw_ordinal"]
        intent = {"ordinal": ordinal, "operation_id": OP, "authority_tip": entry["authority_tip"],
                  "prior_tip": entry["prior_entry_digest"]}
        (study.producer_root / f"draw-{ordinal:08d}.intent.json").write_bytes(encode(intent))
        (study.producer_root / f"draw-{ordinal:08d}.audit.json").write_bytes(
            encode({"entry": entry, "digest": body_digest(entry)}))
    study.files_written = len(study.entries)


def hold(study: Study, label: str) -> tuple[dict, dict]:
    stop = study.log.retain_artifact(encode({"kind": "SYNTHETIC_STOP_EVIDENCE", "label": label}),
                                     "SYNTHETIC-STOP-" + label)
    event = study.log.append("HOLD", INTEGRITY, expected_tip=study.log.tip, operation_id=OP,
                             evidence=[stop])
    return event, stop


def paused_prefix(study: Study, label: str, stop: dict) -> tuple[dict, bytes]:
    """The recorder's sealed stop state, built by hand (Generator.snapshot is not called)."""
    prefix_raw = encode(positions(study.accepted))
    last = next((entry["raw_draw_ordinal"] for entry in reversed(study.entries)
                 if entry["disposition"] == "ACCEPT"), None)
    dependencies = {**study.log.bindings, "GenerationBoundary": record_ref(study.boundary)}
    body = {"record_role": "PrefixSnapshot", "study_id": STUDY, "actor": RECORDER,
            "decision": "SEALED", "evidence": [], "dependencies": dependencies,
            "accepted_count": len(study.accepted), "audit_position": len(study.entries),
            "audit_tip": study.audit_tip, "last_acceptance_ordinal": last,
            "ordered_prefix": private_ref(prefix_raw, "PREFIX-" + label),
            "stop_fencing_evidence": stop}
    return make_record("PrefixSnapshot", body), prefix_raw


def history_proof(study: Study, value: str, label: str, *,
                  disproved: bool = False) -> tuple[bytes, dict]:
    """A synthetic private actual-use proof and its execution receipt (PG-R7/PG-R8 input)."""
    order = "UNKNOWN" if disproved else "BEFORE"
    boundary = study.boundary["digest"]
    execution = encode({"executed_values": [value], "started": not disproved, "scope": "IN_SCOPE",
                        "temporal_order": order, "generation_boundary_digest": boundary})
    execution_ref = private_ref(execution, "synthetic-execution-" + label)
    proof = {"values": [value], "actual_execution": not disproved,
             "scope_verified": not disproved, "temporal_order": order,
             "generation_boundary_digest": boundary, "execution_evidence": execution_ref}
    if disproved:
        proof["disproval"] = "NOT_EXECUTED"
    return encode(proof), {execution_ref["evidence_id"]: execution}


def controller(study: Study) -> IntegrityController:
    return IntegrityController(study.log, verifier_actor=INTEGRITY, lead_actor=LEAD)


def partial_continue(study: Study, label: str) -> None:
    write_draw_files(study)
    event, stop = hold(study, label)
    snapshot, prefix_raw = paused_prefix(study, label, stop)
    value = study.K[0]  # PG-R8: a partial continuation needs every new value inside original K
    proof, executions = history_proof(study, value, label)
    control = controller(study)
    supplement = control.partial_supplement(
        generator=study.generator, snapshot=snapshot, prefix_raw=prefix_raw,
        audit_raw=encode(study.entries), original_K_raw=study.K_raw, history_inputs=[proof],
        execution_inputs=executions, expected_tip=study.log.tip, operation_id=OP)
    released = control.release(
        "PARTIAL_GENERATION", supplement["receipt"], expected_tip=study.log.tip, operation_id=OP,
        evidence=[private_ref(proof, "synthetic-history-" + label)], original_bindings_valid=True,
        supplement=supplement["supplement"], scope="remaining original synthetic draws")
    segment = [record_ref(supplement["supplement"]), record_ref(released["lead_continuation"]),
               record_ref(released["event"])]
    study.chain += [record_ref(event), *segment]
    study.segments.append(("PC", segment))
    study.draw_tips.append(released["event"]["digest"])
    study.history.add(value)


def partial_release(study: Study, label: str) -> None:
    write_draw_files(study)
    event, stop = hold(study, label)
    snapshot, prefix_raw = paused_prefix(study, label, stop)
    proof, executions = history_proof(study, study.accepted[0], label, disproved=True)
    control = controller(study)
    adjudicated = control.verify_disposition(
        "PARTIAL_GENERATION", accepted_raw=prefix_raw, original_K_raw=study.K_raw,
        history_inputs=[proof], execution_inputs=executions,
        boundary_digest=study.boundary["digest"], expected_tip=study.log.tip,
        producer_id=RECORDER["actor_id"], generator=study.generator, snapshot=snapshot)
    released = control.release(
        "PARTIAL_GENERATION", adjudicated["receipt"], expected_tip=study.log.tip, operation_id=OP,
        evidence=adjudicated["evidence"], original_bindings_valid=True, snapshot=snapshot,
        scope="remaining original synthetic draws")
    segment = [record_ref(released["lead_continuation"]), record_ref(released["event"])]
    study.chain += [record_ref(event), *segment]
    study.segments.append(("PR", segment))
    study.draw_tips.append(released["event"]["digest"])


def bridge(study: Study) -> None:
    """An ISSUE between a continuation and the next hold lies inside the chain."""
    reference = record_ref(study.issue_S)
    if study.chain and reference not in study.chain:
        study.chain.append(reference)


def generated_continue(study: Study, label: str) -> None:
    bridge(study)
    event, _ = hold(study, label)
    late = uint64("synthetic-gate8-late-history-" + label)
    assert late not in study.accepted
    proof, executions = history_proof(study, late, label)
    control = controller(study)
    completed = control.completed_supplement(
        "GENERATED", accepted_raw=encode(positions(study.accepted)), original_K_raw=study.K_raw,
        history_inputs=[proof], execution_inputs=executions, generation_boundary=study.boundary,
        expected_tip=study.log.tip, producer_id=RECORDER["actor_id"],
        inspection_boundary="independent synthetic full list only")
    continued = control.release(
        "GENERATED", completed["receipt"], expected_tip=study.log.tip, operation_id=OP,
        evidence=[private_ref(proof, "synthetic-history-" + label)], original_bindings_valid=True,
        supplement=completed["supplement"])
    segment = [record_ref(completed["supplement"]), record_ref(continued["lead_continuation"]),
               record_ref(continued["event"])]
    study.chain += [record_ref(event), *segment]
    study.segments.append(("GC", segment))
    study.history.add(late)


def generated_release(study: Study, label: str) -> None:
    bridge(study)
    event, _ = hold(study, label)
    proof, executions = history_proof(study, study.accepted[1], label, disproved=True)
    control = controller(study)
    adjudicated = control.verify_disposition(
        "GENERATED", accepted_raw=encode(positions(study.accepted)), original_K_raw=study.K_raw,
        history_inputs=[proof], execution_inputs=executions,
        boundary_digest=study.boundary["digest"], expected_tip=study.log.tip,
        producer_id=RECORDER["actor_id"])
    released = control.release(
        "GENERATED", adjudicated["receipt"], expected_tip=study.log.tip, operation_id=OP,
        evidence=adjudicated["evidence"], original_bindings_valid=True)
    segment = [record_ref(released["lead_continuation"]), record_ref(released["event"])]
    study.chain += [record_ref(event), *segment]
    study.segments.append(("GR", segment))


def seal(study: Study, *, rows: list[dict] | None = None, preceding_tip: str | None = None) -> None:
    """Hand-built SeedPayload and S over literal salt bytes, retained privately (no salt.bin)."""
    study.audit_raw = encode(study.entries)
    through = {role: study.log.bindings[role] for role in THROUGH_G}
    audit_ref = private_ref(study.audit_raw, "COMPLETE-AUDIT")
    study.payload = make_record("SeedPayload", {
        "record_role": "SeedPayload", "study_id": STUDY, "actor": RECORDER, "decision": "SEALED",
        "dependencies": through, "evidence": [], "N": N, "domain": DOMAIN, "operation_id": OP,
        "audit": audit_ref, "generation_boundary": record_ref(study.boundary),
        "inventory_refs": study.refs,
        "positions": positions(study.accepted) if rows is None else rows,
        "preceding_chain_tip": study.draw_tips[-1] if preceding_tip is None else preceding_tip})
    study.payload_raw = encode(study.payload)
    dispositions = [entry["disposition"] for entry in study.entries]
    body = {"record_role": "S", "study_id": STUDY, "actor": RECORDER, "decision": "RECORDED",
            "dependencies": through, "evidence": [], "accepted_count": N, "audit": audit_ref,
            "audit_counts": {"raw": len(dispositions), "accepted": dispositions.count("ACCEPT"),
                             "K_rejected": dispositions.count("REJECT_K"),
                             "duplicate_rejected": dispositions.count("REJECT_DUPLICATE")},
            "authority_tip_at_completion": study.log.tip,
            "generation_boundary": record_ref(study.boundary), "operation_id": OP,
            "payload": private_ref(study.payload_raw, "COMPLETE-PAYLOAD"),
            "salt": private_ref(study.salt_raw, "COMPLETE-SALT")}
    study.S = make_record("S", body)
    for name, raw in (("payload", study.payload_raw), ("salt", study.salt_raw),
                      ("audit", study.audit_raw)):
        study.log.retain_artifact(raw, body[name]["evidence_id"])
    study.log.retain_record(study.S)
    study.records["S"] = study.S


def issue_S(study: Study) -> None:
    study.log.bindings = {**study.log.bindings, "S": record_ref(study.S)}
    study.issue_S = study.log.append("ISSUE", LEAD, expected_tip=study.log.tip, operation_id=OP)


def build_issued(root: Path, *, K: list[str] | None = None, accepted: Any = None,
                 consumed: bool = True) -> Study:
    """No holds: ISSUE, register, CONSUME, boundary, 1414 hand-built draws, S, ISSUE(+S)."""
    study = new_study(root, K=K)
    register(study)
    consume(study, consumed=consumed)
    write_boundary(study)
    values = accepted_values(study) if accepted is None else accepted(study)
    draw(study, raw_sequence(study, values))
    seal(study)
    issue_S(study)
    return study


def build_consumed(root: Path) -> Study:
    study = new_study(root)
    register(study)
    consume(study)
    return study


def build_shape(root: Path, partial: tuple, generated: tuple) -> Study:
    """Partial-generation segments at PAUSES, then ISSUE(+S), then GENERATED segments."""
    study = new_study(root)
    register(study, reader=bool(partial))
    consume(study)
    write_boundary(study)
    raw = raw_sequence(study, accepted_values(study))
    start = 0
    for index, kind in enumerate(partial):
        draw(study, raw[start:PAUSES[index]])
        start = PAUSES[index]
        (partial_continue if kind == "PC" else partial_release)(study, f"partial-{index}")
    draw(study, raw[start:])
    seal(study)
    issue_S(study)
    for index, kind in enumerate(generated):
        (generated_continue if kind == "GC" else generated_release)(study, f"generated-{index}")
    return study


def clone(base: Study, target: Path) -> Study:
    """A copy of a base study's private authority root, owned by one test."""
    shutil.copytree(base.log.root, target / "authority")
    flags = {"source_drift": False}
    log = authority(target / "authority", base.log.bindings, base.by_digest, flags,
                    dict(base.log.actors))
    return replace(base, root=target, log=log, flags=flags, generator=None,
                   records=dict(base.records), entries=list(base.entries),
                   accepted=list(base.accepted), draw_tips=list(base.draw_tips),
                   chain=list(base.chain), segments=list(base.segments),
                   history=set(base.history))


def produce(study: Study, *, verifier: dict = VERIFIER, expected_tip: str | None = None) -> dict:
    tip = study.log.tip if expected_tip is None else expected_tip
    return pv.produce_private_verification(study.log, verifier=verifier, expected_tip=tip,
                                           operation_id=PV_OP)


def issue_W(study: Study, reference: dict) -> None:
    study.log.bindings = {**study.log.bindings, "W": reference}
    study.log.append("ISSUE", LEAD, expected_tip=study.log.tip, operation_id=OP)
    study.records["W"] = study.log.resolve(reference)


_BASES: dict[str, Study] = {}


def _w_issued(root: Path, get: Any) -> Study:
    study = clone(get("issued"), root)
    issue_W(study, produce(study))
    return study


BUILDERS = {
    "issued": lambda root, get: build_issued(root),
    "consumed": lambda root, get: build_consumed(root),
    "partial-release-continue": lambda root, get: build_shape(root, ("PR", "PC"), ()),
    "generated-continue": lambda root, get: build_shape(root, (), ("GC",)),
    "generated-release": lambda root, get: build_shape(root, (), ("GR",)),
    "combination": lambda root, get: build_shape(root, ("PC", "PR"), ("GC", "GR")),
    "w-issued": _w_issued,
}


def base_getter(factory: Any) -> Any:
    """Lazily built, cached base studies. Built inside a test, so always under the guard."""
    def get(name: str) -> Study:
        if name not in _BASES:
            _BASES[name] = BUILDERS[name](factory.mktemp(name), get)
        return _BASES[name]
    return get


@pytest.fixture
def bases(tmp_path_factory):
    return base_getter(tmp_path_factory)


# ---- Publication helpers shared with the independent publication module -----------------

def template_body(study: Study, **changes: Any) -> dict:
    """The exact C body without U: dependencies P..G, S, W; W's c; frozen constants."""
    body = {"record_role": "C", "study_id": STUDY, "actor": PUBLISHER, "decision": "PUBLISHED",
            "dependencies": {role: study.log.bindings[role] for role in U_DEPENDENCIES},
            "evidence": [PUBLIC_NOTICE], "N": N, "claim_profile": "C-LIMITED",
            "commitment": study.records["W"]["body"]["commitment"],
            "historical_coverage": "NOT ESTABLISHED", "permanent_limitation": PERMANENT_LIMITATION}
    body.update(changes)
    return body


def pre_u(study: Study, body: dict, *, checker: dict = CHECKER) -> dict:
    return pv.check_publication_template(study.log, body, checker=checker,
                                         expected_tip=study.log.tip,
                                         operation_id="synthetic-template-check")


def make_U(study: Study, body: dict, evidence: list[dict]) -> dict:
    template = {"body": body, "digest": body_digest(body),
                "U_insertion_slot": "body.dependencies.U"}
    return make_record("U", {
        "record_role": "U", "study_id": STUDY, "actor": LEAD, "decision": "AUTHORIZED",
        "dependencies": {role: study.log.bindings[role] for role in U_DEPENDENCIES},
        "evidence": list(evidence), "active_authority_tip": study.log.tip,
        "approved_public_record_body": template,
        "commitment": study.records["W"]["body"]["commitment"],
        "scope": "synthetic qualification commitment publication only"})


def issue_U(study: Study, U: dict, *, lead: dict = LEAD, expected_tip: str | None = None) -> dict:
    tip = study.log.tip if expected_tip is None else expected_tip
    return pv.issue_publication_authorization(study.log, U, lead=lead, expected_tip=tip,
                                              operation_id="synthetic-u-issuance")


def generic_issue_U(study: Study, U: dict) -> None:
    """Bypass the dedicated Gate-8 path with a plain lead ISSUE (the D3 clarification case)."""
    study.log.retain_record(U)
    study.log.bindings = {**study.log.bindings, "U": record_ref(U)}
    study.log.append("ISSUE", LEAD, expected_tip=study.log.tip, operation_id=OP)


def public_C(body: dict, U: dict, status: str | None = None) -> dict:
    return make_record("C", {**body, "dependencies": {**body["dependencies"], "U": record_ref(U)}},
                       status=status)


def publish(study: Study, C: dict, destination: Path, *, publisher: dict = PUBLISHER) -> dict:
    return publish_commitment(study.log, C, expected_tip=study.log.tip,
                              operation_id="synthetic-publication", publisher=publisher,
                              destination=destination)


def u_consumed(study: Study) -> bool:
    with study.log.exclusive():
        state = study.log._state()
    U = state["active_bindings"].get("U")
    return U is not None and U["digest"] in state["consumed"]


def u_active(study: Study) -> bool:
    with study.log.exclusive():
        return "U" in study.log._state()["active_bindings"]


def start_worker(study: Study, U: dict, C: dict) -> None:
    study.log.retain_record(C)
    D = fixture("D", {**study.records, "U": U, "C": C}, active_authority_tip=study.log.tip)
    study.log.retain_record(D)
    study.log.bindings = {**study.log.bindings, "C": record_ref(C), "D": record_ref(D)}
    study.log.append("ISSUE", LEAD, expected_tip=study.log.tip, operation_id=OP)
    leases: list = []
    started = study.log.protected("worker_start", expected_tip=study.log.tip,
                                  operation_id="synthetic-worker",
                                  action=lambda lease: leases.append(lease) or "started")
    assert started == "started" and len(leases) == 1


# ---- Observation helpers ------------------------------------------------------------------

def w_folder(study: Study) -> Path:
    return study.log.root / "private-verification" / study.S["digest"]


def read_W(study: Study) -> dict:
    return json.loads((w_folder(study) / "W.json").read_bytes())


def written_W(study: Study) -> list[Path]:
    base = study.log.root / "private-verification"
    return sorted(base.rglob("W.json")) if base.exists() else []


def outcomes(study: Study) -> list[dict]:
    base = study.log.root / "private-verification"
    paths = sorted(base.rglob("attempt-*.outcome.json")) if base.exists() else []
    return [json.loads(path.read_bytes()) for path in paths]


def labels(study: Study) -> list[str]:
    records = outcomes(study)
    assert all(set(record) == OUTCOME_KEYS for record in records)
    return [record["outcome"] for record in records]


def event_files(study: Study) -> list[Path]:
    return sorted(study.log.root.glob("event-*.json"))


def last_event(study: Study) -> dict:
    return json.loads(event_files(study)[-1].read_bytes())


def contains_run(sequence: list, run: list) -> bool:
    return any(sequence[i:i + len(run)] == run for i in range(len(sequence) - len(run) + 1))


def leaves(value: Any) -> list:
    if isinstance(value, dict):
        return [item for nested in value.values() for item in leaves(nested)]
    if isinstance(value, list):
        return [item for nested in value for item in leaves(nested)]
    return [value]


def json_texts(value: Any) -> list[str]:
    """Every key and scalar of a JSON value as text (integers in decimal)."""
    if isinstance(value, dict):
        return [text for key, item in value.items() for text in (key, *json_texts(item))]
    if isinstance(value, list):
        return [text for item in value for text in json_texts(item)]
    if isinstance(value, str):
        return [value]
    if type(value) is int:
        return [str(value)]
    return []


def exposed(text: str, *, hexes: Any, decimals: Any, salts: Any, roots: Any) -> bool:
    """Independent reference for the scope's representation set, over one text."""
    lowered = text.lower()
    if any(value in lowered for value in hexes):
        return True
    if set(decimals) & set(re.findall(r"[0-9]+", text)):
        return True
    for salt in salts:
        forms = (base64.b64encode(salt).decode().rstrip("="),
                 base64.urlsafe_b64encode(salt).decode().rstrip("="))
        if salt.hex() in lowered or any(form in text for form in forms):
            return True
    normalized = lowered.replace("\\", "/")
    return any(root.lower().replace("\\", "/") in normalized for root in roots)


def study_forms(study: Study, *, every_decimal: bool = False) -> dict:
    """Private values of a study: every generated value and K member in 16-hex form, the
    salt and the private roots. The scope's complete set (every_decimal) also matches every
    decimal form. Record scans (W-10) match only full-width decimals: a small number such as
    1, 2 or 1412 occurs as a structural integer or digest digit run in any record, whether it
    is a public K literal or a deliberately small fixture value (W-07 K overlap, N1-04)."""
    values = set(study.accepted) | {entry["raw_bytes_hex"] for entry in study.entries}
    values |= set(study.K)
    return {"hexes": values,
            "decimals": {str(int(value, 16)) for value in values
                         if every_decimal or int(value, 16) >= 10 ** 6},
            "salts": (study.salt_raw,),
            "roots": (str(study.log.root.resolve()), str(study.producer_root.resolve()))}


SHA256 = re.compile(r"[0-9a-f]{64}")


def assert_private_free(study: Study, raw: bytes) -> None:
    """W-10: no private value in any representation in a record's decoded keys and fields.
    A full sha256 field is typed, not chosen content (D1), so it is compared with the salt
    only; N1-04 deliberately uses generated values that are windows of dependency digests."""
    forms = study_forms(study)
    salts = {salt.hex() for salt in forms["salts"]}
    flagged = [text for text in json_texts(json.loads(raw))
               if (text in salts if SHA256.fullmatch(text) else exposed(text, **forms))]
    assert flagged == []


def verifier_spy(monkeypatch) -> list[dict]:
    """Observe, and pass through to, the sealed verify_complete_private the producer calls."""
    calls: list[dict] = []
    sealed = pv.verify_complete_private

    def spy(**kwargs):
        calls.append(kwargs)
        return sealed(**kwargs)
    monkeypatch.setattr(pv, "verify_complete_private", spy)
    return calls


def private_read_spy(monkeypatch, study: Study) -> list[str]:
    """Record every open or read of the S-bound payload/salt/audit bytes or original K."""
    names = {sha(raw) + ".bin" for raw in (study.payload_raw, study.salt_raw, study.audit_raw,
                                           study.K_raw) if raw}
    seen: list[str] = []
    opener, reader = Path.open, AuthorityLog.read_artifact

    def spy_open(self, *args, **kwargs):
        if self.name in names:
            seen.append(self.name)
        return opener(self, *args, **kwargs)

    def spy_read(self, ref):
        if isinstance(ref, dict) and f"{ref.get('sha256_raw')}.bin" in names:
            seen.append(str(ref.get("evidence_id")))
        return reader(self, ref)
    monkeypatch.setattr(Path, "open", spy_open)
    monkeypatch.setattr(AuthorityLog, "read_artifact", spy_read)
    return seen


def entropy_spy(monkeypatch, request) -> list:
    """W-12: under the guard every entropy source is the guard's refusal; count any call."""
    guard = "tools.research.v6.e9.v2.qualification_guard"
    if request.config.pluginmanager.has_plugin(guard):
        assert all(target is forbidden for target in (
            os.urandom, random._urandom, secrets.token_bytes, secrets.randbits,
            secrets.randbelow))
    calls: list = []

    def refuse(*args, **kwargs):
        calls.append(args)
        raise AssertionError("W production reached an entropy source")
    for module, name in ((os, "urandom"), (random, "_urandom"), (secrets, "token_bytes"),
                         (secrets, "randbits"), (secrets, "randbelow")):
        monkeypatch.setattr(module, name, refuse)
    return calls


def check_W(study: Study, W: dict, *, tip: str) -> None:
    """W-01/W-13: every W field against the frozen schema and independent recomputation."""
    validate_record(W)
    spec = CATALOGUE["records"]["W"]
    assert (W["schema"], W["version"]) == (spec["schema"], spec["version"])
    assert W["identity"] == spec["identity_prefix"] + W["digest"][:12]
    body = W["body"]
    assert (body["record_role"], body["study_id"], body["decision"]) == ("W", STUDY, "PASS")
    assert body["actor"] == VERIFIER
    # DS-W1-01/02, DS-W2-01: exactly P..G and S; no c, T, U or C dependency.
    assert body["dependencies"] == {role: study.log.bindings[role] for role in W_DEPENDENCIES}
    assert not {"c", "T", "U", "C"} & set(body["dependencies"])
    # DS-W7-01: primitive c, recomputed independently from the declared private bytes.
    c = sha(COMMITMENT_DOMAIN + study.salt_raw + study.payload_raw)
    assert isinstance(body["commitment"], str) and body["commitment"] == c
    assert body["payload"] == study.S["body"]["payload"]
    assert body["salt"] == study.S["body"]["salt"]
    assert body["payload"]["visibility"] == body["salt"]["visibility"] == "PRIVATE"
    assert body["active_authority_tip"] == tip
    assert body["evidence"] and all(ref["visibility"] == "PRIVATE" for ref in body["evidence"])
    for ref in body["evidence"]:
        study.log.read_artifact(ref)  # retained under the private authority root
    reproduction = leaves(body["audit_reproduction"])
    assert {"REAL", "NOT ESTABLISHED", sha(study.audit_raw), study.audit_tip} <= {
        item for item in reproduction if isinstance(item, str)}
    assert any(item is True for item in reproduction)  # full private read-back
    assert len(study.entries) in reproduction and N in leaves(body["all_position_checks"])
    verify_W_bytes(W, payload_raw=study.payload_raw, salt_raw=study.salt_raw,
                   expected_commitment=c)
    raw = (w_folder(study) / "W.json").read_bytes()
    assert raw == encode(W)
    assert_private_free(study, raw)


def check_verifier_inputs(study: Study, inputs: dict, *, tip: str, chain: list) -> None:
    """D6/W-14: what reached the sealed verifier was derived by the producer, REAL only."""
    assert inputs["entropy_source"] == "REAL"
    assert (inputs["payload_raw"], inputs["salt_raw"]) == (study.payload_raw, study.salt_raw)
    assert (inputs["audit_raw"], inputs["original_K_raw"]) == (study.audit_raw, study.K_raw)
    assert inputs["expected_bindings"] == {role: study.log.bindings[role] for role in THROUGH_G}
    assert inputs["inventory_refs"] == study.refs and inputs["operation_id"] == OP
    assert inputs["generation_boundary"] == study.boundary
    assert inputs["expected_commitment"] == sha(COMMITMENT_DOMAIN + study.salt_raw
                                                + study.payload_raw)
    assert inputs["authority_tips"] == study.draw_tips
    assert inputs["preceding_chain_tip"] == study.draw_tips[-1]
    assert inputs["active_chain_tip"] == tip
    assert (inputs.get("supplement_chain") or []) == chain
    receipts = inputs.get("history_receipts") or []
    assert set(inputs.get("supplemented_history") or []) == study.history
    assert {value for receipt in receipts for value in receipt.values} == study.history
    for receipt in receipts:  # PG-R8: full-list receipts recomputed under W's own verifier
        assert receipt.disposition == "NEW_HISTORY" and not receipt.intersection
        assert receipt.verifier_id == VERIFIER["actor_id"]
        assert receipt.accepted_digest == sha(encode(positions(study.accepted)))
    assert callable(inputs["resolver"]) and callable(inputs["artifact_reader"])


# ---- W-01, W-09, W-10, W-12, W-13 -------------------------------------------------------------

def test_w01_w09_w10_w12_w13_no_hold_sequence_from_issued_S_to_worker_start(
        bases, tmp_path, monkeypatch, request):
    study = clone(bases("issued"), tmp_path)
    entropy = entropy_spy(monkeypatch, request)
    calls = verifier_spy(monkeypatch)
    tip, events = study.log.tip, len(event_files(study))
    reference = produce(study)
    W = read_W(study)
    assert record_ref(W) == reference
    check_W(study, W, tip=tip)
    assert W["body"]["supplement_chain"] == []
    assert len(event_files(study)) == events and study.log.tip == tip  # W appends no event
    (inputs,) = calls
    check_verifier_inputs(study, inputs, tip=tip, chain=[])
    (outcome,) = outcomes(study)
    assert set(outcome) == OUTCOME_KEYS
    assert (int(outcome["attempt"]), outcome["outcome"], outcome["W"]) == (1, "PASS", reference)
    assert outcome["interrupted_prior_attempts"] == []
    folder = w_folder(study)
    assert (folder / "attempt-0001.intent.json").exists()
    for path in folder.glob("attempt-*.json"):
        assert_private_free(study, path.read_bytes())
    # W-09: W is written once and every later attempt for this S is refused.
    written = (folder / "W.json").read_bytes()
    with pytest.raises(IntegrityError):
        produce(study)
    assert labels(study) == ["PASS", "REFUSED_PRECONDITION"] and len(calls) == 1
    assert (folder / "W.json").read_bytes() == written
    # The lead's ISSUE(+W) follows with no intervening event; W in the tuple refuses again.
    assert W["body"]["active_authority_tip"] == study.log.tip
    issue_W(study, reference)
    with pytest.raises(IntegrityError):
        produce(study)
    assert labels(study)[-1] == "REFUSED_PRECONDITION" and len(calls) == 1
    # Pre-U check, dedicated issuance, single-use publication, then worker_start.
    body = template_body(study)
    result = pre_u(study, body)
    assert result["decision"] == "PASS" and result["template_digest"] == body_digest(body)
    assert result["receipt"]["visibility"] == "PRIVATE"
    assert result["receipt"]["evidence_id"].startswith("GATE8-PRE-U-TEMPLATE-CHECK")
    U = make_U(study, body, [result["receipt"]])
    issue_U(study, U)
    assert study.log.bindings["U"] == record_ref(U) and u_active(study)
    assert pv.verify_operational_u(study.log)["decision"] == "ADMISSIBLE"
    C = public_C(body, U)
    assert publish(study, C, tmp_path / "C.json") == record_ref(C)
    assert (tmp_path / "C.json").read_bytes() == encode(C) and u_consumed(study)
    start_worker(study, U, C)
    assert entropy == []


# ---- W-02, W-03, W-14: the complete chain from the durable log ------------------------------

@pytest.mark.parametrize("shape", ["partial-release-continue", "generated-continue",
                                   "generated-release", "combination"])
def test_w02_w03_w14_derived_chain_is_the_hand_listed_gap_free_chain(
        shape, bases, tmp_path, monkeypatch):
    study = clone(bases(shape), tmp_path)
    calls = verifier_spy(monkeypatch)
    tip = study.log.tip
    reference = produce(study)
    W = read_W(study)
    assert record_ref(W) == reference
    derived = W["body"]["supplement_chain"]
    # The hand-listed chain names every event after the boundary tip up to the last
    # continuation, each supplement and lead record before its event; the first segment's
    # HOLD may instead be bound only by that segment's AuthorityEvent reference.
    assert derived in (study.chain, study.chain[1:])
    for _kind, segment in study.segments:  # W-03: GENERATED-stage segments always included
        assert contains_run(derived, segment)
    check_W(study, W, tip=tip)
    (inputs,) = calls
    check_verifier_inputs(study, inputs, tip=tip, chain=derived)
    assert labels(study) == ["PASS"]


@pytest.mark.parametrize("fault", ["deleted_generated_continuation", "reordered_events"])
def test_w03_missing_or_reordered_chain_evidence_fails_closed(fault, bases, tmp_path,
                                                              monkeypatch):
    study = clone(bases("generated-continue"), tmp_path)
    calls = verifier_spy(monkeypatch)
    tip = study.log.tip
    if fault == "reordered_events":
        last, before = event_files(study)[-1], event_files(study)[-2]
        last_raw, before_raw = last.read_bytes(), before.read_bytes()
        last.write_bytes(before_raw)
        before.write_bytes(last_raw)
        with pytest.raises(IntegrityError):
            produce(study, expected_tip=tip)
        assert written_W(study) == [] and "PASS" not in labels(study) and calls == []
        return
    segment = next(refs for kind, refs in study.segments if kind == "GC")
    lead = segment[1]
    held = {}
    for path in (study.log.root / "evidence-records" / (lead["digest"] + ".json"),
                 study.log.root / "evidence-raw" / (lead["sha256_raw"] + ".bin")):
        held[path] = path.read_bytes()
        path.unlink()
    with pytest.raises(IntegrityError):
        produce(study)
    assert labels(study) == ["UNAVAILABLE"] and written_W(study) == []
    assert calls == []  # a chain missing its continuation never reaches the sealed verifier
    for path, raw in held.items():  # hash-checked, byte-identical restoration
        assert sha(raw) == lead["sha256_raw"]
        path.write_bytes(raw)
    produce(study)
    assert labels(study) == ["UNAVAILABLE", "PASS"]
    assert contains_run(read_W(study)["body"]["supplement_chain"], segment)


@pytest.mark.parametrize("shape", ["issued", "partial-release-continue"])
def test_w04_w14_tail_event_other_than_extending_issue_fails_before_the_verifier(
        shape, bases, tmp_path, monkeypatch):
    study = clone(bases(shape), tmp_path)
    study.log.append("CONSUME", RECORDER, expected_tip=study.log.tip,
                     operation_id="synthetic-tail-consumption")
    calls = verifier_spy(monkeypatch)
    with pytest.raises(IntegrityError):
        produce(study)
    assert labels(study) == ["FAILED_VERIFICATION"]
    assert written_W(study) == [] and calls == []
    for path in w_folder(study).glob("attempt-*.json"):
        assert_private_free(study, path.read_bytes())
    with pytest.raises(IntegrityError):
        produce(study)
    assert labels(study) == ["FAILED_VERIFICATION", "REFUSED_PRECONDITION"] and calls == []


# ---- W-05: N6 declaration and D5 producer root / first-raw marker ---------------------------

def w05_evidence(study: Study, case: str, tmp_path: Path) -> list[dict]:
    log, G = study.log, study.log.bindings["G"]
    entropy_id = "ENTROPY-SOURCE-" + G["digest"]
    real = log.retain_artifact(declaration(study), entropy_id)
    if case == "foreign_root":  # a registry-shaped root that is not the registered one
        registry = json.loads((log.root / "producer-roots" / (G["digest"] + ".json")).read_bytes())
        root = os.path.normcase(str((tmp_path / "foreign-producer").resolve()))
        fake = log.retain_artifact(encode({**registry, "producer_root": root}),
                                   "PRODUCER-ROOT-" + G["digest"])
        return [fake, log.mark_first_raw(fake), real]
    if case == "marker_not_durable":  # the bound marker bytes exist; the durable marker does not
        marker = encode({"kind": "FIRST_RAW_BOUNDARY_V2", "study_id": STUDY, "G": G,
                         "producer_registry": study.producer_ref})
        return [study.producer_ref, log.retain_artifact(marker, "FIRST-RAW-" + G["digest"]), real]
    if case == "producer_absent":
        return [log.mark_first_raw(study.producer_ref), real]
    if case == "fencing_absent":  # accepted by the sealed verifier alone; D5 must refuse it
        return [real]
    fenced = [study.producer_ref, log.mark_first_raw(study.producer_ref)]
    if case == "synthetic":
        return [*fenced, log.retain_artifact(declaration(study, mode="SYNTHETIC"), entropy_id)]
    if case == "absent":
        return fenced
    if case == "duplicate":
        return [*fenced, real, log.retain_artifact(declaration(study), entropy_id + "-COPY")]
    if case == "mixed":
        synthetic = log.retain_artifact(declaration(study, mode="SYNTHETIC"), entropy_id + "-S")
        return [*fenced, real, synthetic]
    assert case == "other_G"
    other = log.retain_artifact(declaration(study, G=record_ref(study.records["I"])), entropy_id)
    return [*fenced, other]


@pytest.mark.parametrize("case", ["synthetic", "absent", "duplicate", "mixed", "other_G",
                                  "producer_absent", "marker_not_durable", "fencing_absent",
                                  "foreign_root"])
def test_w05_declaration_and_fencing_faults_fail_verification_without_w(case, bases, tmp_path):
    study = clone(bases("consumed"), tmp_path)
    write_boundary(study, w05_evidence(study, case, tmp_path), own_root=False)
    draw(study, raw_sequence(study, accepted_values(study)))
    seal(study)
    issue_S(study)
    with pytest.raises(IntegrityError):
        produce(study)
    if case == "marker_not_durable":  # scope 02 F1, edit E2: a missing durable marker: UNAVAILABLE
        assert labels(study) == ["UNAVAILABLE"] and written_W(study) == []
        bound = next(ref for ref in study.boundary["body"]["evidence"]
                     if ref["evidence_id"].startswith("FIRST-RAW-"))
        durable = study.log.root / "first-raw" / (study.log.bindings["G"]["digest"] + ".json")
        assert not durable.exists()  # the producer wrote no marker
        durable.parent.mkdir(parents=True, exist_ok=True)
        durable.write_bytes(study.log.read_artifact(bound))  # exactly the bytes the boundary binds
        reference = produce(study)  # a new attempt, not refused as already failed
        assert labels(study) == ["UNAVAILABLE", "PASS"] and record_ref(read_W(study)) == reference
        for path in w_folder(study).glob("attempt-*.json"):
            assert_private_free(study, path.read_bytes())
        return
    assert labels(study) == ["FAILED_VERIFICATION"] and written_W(study) == []
    for path in w_folder(study).glob("attempt-*.json"):
        assert_private_free(study, path.read_bytes())


# ---- W-06: preconditions before any private read ---------------------------------------------

VERIFIER_CASES = {
    "unregistered_verifier": actor("independent_verifier", "synthetic-unregistered-verifier"),
    "integrity_role_verifier": INTEGRITY,
    "recorder_as_verifier": actor("independent_verifier", RECORDER["actor_id"]),
    "custodian_as_verifier": actor("independent_verifier", "synthetic-custodian"),
    "lead_as_verifier": actor("independent_verifier", LEAD["actor_id"]),
    "publisher_as_verifier": actor("independent_verifier", PUBLISHER["actor_id"]),
}


def hand_W(study: Study) -> dict:
    """A W added without the producer, so W already sits in the active tuple."""
    W = make_record("W", {
        "record_role": "W", "study_id": STUDY, "actor": VERIFIER, "decision": "PASS",
        "dependencies": {role: study.log.bindings[role] for role in W_DEPENDENCIES},
        "evidence": [], "active_authority_tip": study.log.tip,
        "all_position_checks": {"accepted_count": N},
        "audit_reproduction": {"entropy_source": "REAL"},
        "commitment": sha(COMMITMENT_DOMAIN + study.salt_raw + study.payload_raw),
        "payload": study.S["body"]["payload"], "salt": study.S["body"]["salt"],
        "supplement_chain": []})
    study.log.retain_record(W)
    return record_ref(W)


@pytest.mark.parametrize("case", ["held", "terminal", "stale", "revoked", "source_drift",
                                  "W_issued", "S_not_issued", "S_absent", *VERIFIER_CASES])
def test_w06_precondition_failures_are_refused_before_any_private_read(case, bases, tmp_path,
                                                                       monkeypatch):
    study = clone(bases("consumed" if case.startswith("S_") else "issued"), tmp_path)
    log, verifier, tip = study.log, VERIFIER_CASES.get(case, VERIFIER), None
    stop = log.retain_artifact(encode({"kind": "SYNTHETIC_STOP_EVIDENCE", "label": case}),
                               "SYNTHETIC-STOP-" + case)
    if case == "S_not_issued":
        write_boundary(study, own_root=False)
        draw(study, raw_sequence(study, accepted_values(study)))
        seal(study)
        log.bindings = {**log.bindings, "S": record_ref(study.S)}  # bound in memory only
    elif case == "held":
        log.append("HOLD", INTEGRITY, expected_tip=log.tip, operation_id=OP, evidence=[stop])
    elif case == "terminal":
        log.append("TERMINATE", LEAD, expected_tip=log.tip, operation_id=OP,
                   affected=[log.bindings["G"]], evidence=[stop])
    elif case == "revoked":
        log.append("REVOKE", LEAD, expected_tip=log.tip, operation_id=OP,
                   affected=[log.bindings["S"]], evidence=[stop])
    elif case == "stale":
        tip = study.consume_tip
    elif case == "source_drift":
        study.flags["source_drift"] = True
    elif case == "W_issued":
        issue_W(study, hand_W(study))
    reads = private_read_spy(monkeypatch, study)
    calls = verifier_spy(monkeypatch)
    with pytest.raises(IntegrityError):
        produce(study, verifier=verifier, expected_tip=tip)
    assert reads == [] and calls == [] and written_W(study) == []
    recorded = labels(study)
    if case == "S_absent":  # no S digest names the attempt folder; any record is a refusal
        assert set(recorded) <= {"REFUSED_PRECONDITION"}
    else:
        assert recorded == ["REFUSED_PRECONDITION"]


def test_w06_generation_authority_not_consumed_by_its_operation_is_refused(tmp_path,
                                                                           monkeypatch):
    study = build_issued(tmp_path, consumed=False)
    reads = private_read_spy(monkeypatch, study)
    calls = verifier_spy(monkeypatch)
    with pytest.raises(IntegrityError):
        produce(study)
    assert reads == [] and calls == [] and written_W(study) == []
    assert labels(study) == ["REFUSED_PRECONDITION"]


# ---- W-07: sealed verifier faults are completed, final verification failures -----------------

@pytest.mark.parametrize("fault", ["K_overlap", "order", "audit_chain", "stale_preceding_tip"])
def test_w07_sealed_verifier_faults_through_the_producer_are_final(fault, bases, tmp_path,
                                                                    monkeypatch):
    study = clone(bases("consumed"), tmp_path)
    write_boundary(study, own_root=False)
    values = accepted_values(study)
    member = study.K[1]
    if fault == "K_overlap":  # an original-K member recorded as accepted
        values = [*values[:2], member, *values[3:]]
    draw(study, raw_sequence(study, values), force_accept={member} if fault == "K_overlap" else ())
    rows = preceding = None
    if fault == "order":
        rows = positions(study.accepted)
        rows[0]["value_hex"], rows[1]["value_hex"] = rows[1]["value_hex"], rows[0]["value_hex"]
    elif fault == "audit_chain":
        study.entries[9] = {**study.entries[9], "prior_entry_digest": "0" * 64}
    elif fault == "stale_preceding_tip":
        preceding = json.loads(event_files(study)[0].read_bytes())["digest"]
    seal(study, rows=rows, preceding_tip=preceding)
    issue_S(study)
    calls = verifier_spy(monkeypatch)
    with pytest.raises(IntegrityError):
        produce(study)
    assert labels(study) == ["FAILED_VERIFICATION"] and written_W(study) == []
    # The sealed verifier itself detects these faults; a stale preceding tip may also be
    # caught earlier by the producer's own chain derivation.
    assert len(calls) == 1 or (fault == "stale_preceding_tip" and calls == [])
    for path in w_folder(study).glob("attempt-*.json"):
        assert_private_free(study, path.read_bytes())
    reached = len(calls)
    with pytest.raises(IntegrityError):  # every later attempt for this S is refused
        produce(study)
    assert labels(study) == ["FAILED_VERIFICATION", "REFUSED_PRECONDITION"]
    assert len(calls) == reached and written_W(study) == []


# ---- W-08, W-09: non-completion is retried manually and never becomes a failure ---------------

@pytest.mark.parametrize("missing", ["salt", "original_K"])
def test_w08_missing_retained_artifact_is_unavailable_until_exact_restoration(
        missing, bases, tmp_path, monkeypatch):
    study = clone(bases("issued"), tmp_path)
    if missing == "salt":
        raw, bound = study.salt_raw, study.S["body"]["salt"]
    else:
        raw, bound = study.K_raw, study.records["O"]["body"]["K"]
    path = study.log.root / "evidence-raw" / (bound["sha256_raw"] + ".bin")
    held = path.read_bytes()
    path.unlink()
    calls = verifier_spy(monkeypatch)
    with pytest.raises(IntegrityError):
        produce(study)
    assert labels(study) == ["UNAVAILABLE"] and written_W(study) == [] and calls == []
    assert held == raw and (len(held), sha(held)) == (bound["bytes"], bound["sha256_raw"])
    path.write_bytes(held)  # hash-checked, byte-identical restoration against the bound ref
    reference = produce(study)
    assert labels(study) == ["UNAVAILABLE", "PASS"] and record_ref(read_W(study)) == reference
    assert outcomes(study)[-1]["interrupted_prior_attempts"] == []


class SimulatedStop(BaseException):
    """A process stop between an attempt's intent and its outcome (not an IntegrityError)."""


def test_w09_interrupted_attempt_is_retained_and_listed_by_the_next_attempt(
        bases, tmp_path, monkeypatch):
    study = clone(bases("issued"), tmp_path)
    sealed, stopped = pv.verify_complete_private, []

    def stop_once(**kwargs):
        if not stopped:
            stopped.append(True)
            raise SimulatedStop
        return sealed(**kwargs)
    monkeypatch.setattr(pv, "verify_complete_private", stop_once)
    with pytest.raises(SimulatedStop):
        produce(study)
    folder = w_folder(study)
    first = folder / "attempt-0001.outcome.json"
    assert (folder / "attempt-0001.intent.json").exists() and not (folder / "W.json").exists()
    assert not first.exists() or json.loads(first.read_bytes())["outcome"] == "INTERRUPTED"
    assert not (study.log.root / "exclusive.lock").exists()
    reference = produce(study)
    second = json.loads((folder / "attempt-0002.outcome.json").read_bytes())
    assert (second["outcome"], second["W"]) == ("PASS", reference)
    assert len(second["interrupted_prior_attempts"]) == 1
    assert (folder / "attempt-0001.intent.json").exists() and labels(study)[-1] == "PASS"


def test_w09_partial_w_file_fails_closed(bases, tmp_path):
    study = clone(bases("issued"), tmp_path)
    partial = b'{"body":{"record_role":"W"'
    path = w_folder(study) / "W.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(partial)
    with pytest.raises(IntegrityError):
        produce(study)
    assert path.read_bytes() == partial and "PASS" not in labels(study)


# ---- W-11: layout parity with the injected generator (layout only) ---------------------------

def boundary_layout(log: AuthorityLog, boundary: dict) -> dict:
    body = boundary["body"]
    evidence = body["evidence"]
    registry, marker, declared = (json.loads(log.read_artifact(ref)) for ref in evidence)
    durable = (log.root / "first-raw" / (log.bindings["G"]["digest"] + ".json")).read_bytes()
    return {"ids": [ref["evidence_id"] for ref in evidence],
            "visibility": [ref["visibility"] for ref in evidence],
            "registry": {k: v for k, v in registry.items() if k != "producer_root"},
            "marker": {k: v for k, v in marker.items() if k != "producer_registry"},
            "marker_binds_registry": marker["producer_registry"] == evidence[0],
            "durable_marker": durable == log.read_artifact(evidence[1]),
            "declaration": {k: v for k, v in declared.items()
                            if k not in ("mode", "draw_source", "salt_source")},
            "fields": sorted(body), "durable_instant": sorted(body["durable_instant"]),
            **{name: body[name] for name in ("record_role", "study_id", "actor", "decision",
                                             "dependencies", "operation_id",
                                             "producer_fence_epoch")}}


def test_w11_injected_generator_boundary_layout_equals_the_real_labelled_fixture(bases,
                                                                                tmp_path):
    real = bases("issued")
    synthetic = new_study(tmp_path)
    values = iter([(1 << 63) + 101, (1 << 63) + 202])
    generator = Generator(tmp_path / "producer", synthetic.log, operation_id=OP,
                          recorder=RECORDER, original_K_raw=synthetic.K_raw,
                          inventory_refs=synthetic.refs,
                          draw_bytes=lambda size: next(values).to_bytes(size, "big"),
                          salt_bytes=lambda size: pytest.fail("qualification creates no salt"),
                          mode="SYNTHETIC")
    instant = private_ref(b"synthetic durable instant\n", "SYNTHETIC-DURABLE-INSTANT")
    generator.consume(expected_tip=synthetic.log.tip, boundary_evidence=instant)
    consume_tip = synthetic.log.tip
    for _ in range(2):
        generator.draw_one(expected_tip=synthetic.log.tip, durable_instant=instant)
    boundary = json.loads((tmp_path / "producer" / "boundary.json").read_bytes())
    assert boundary["body"]["active_authority_tip"] == consume_tip
    assert real.boundary["body"]["active_authority_tip"] == real.consume_tip
    assert synthetic.log.bindings["G"] == real.log.bindings["G"]
    assert boundary_layout(synthetic.log, boundary) == boundary_layout(real.log, real.boundary)
    G = real.log.bindings["G"]
    for mode, log, bound in (("SYNTHETIC", synthetic.log, boundary),
                             ("REAL", real.log, real.boundary)):
        declared = json.loads(log.read_artifact(bound["body"]["evidence"][2]))
        assert declared == entropy_declaration(mode, study_id=STUDY, G=G, operation_id=OP)


# ---- W-12, W-14: static entropy absence and the producer's closed input surface ---------------

def test_w12_producer_module_references_no_entropy_source_mode_or_entry_point():
    tree = ast.parse(Path(pv.__file__).read_text(encoding="utf-8"))
    modules, names, strings = set(), set(), set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0 and node.module:
                modules.add(node.module.split(".")[0])
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.Name):
            names.add(node.id)
        elif isinstance(node, ast.Attribute):
            names.add(node.attr)
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            strings.add(node.value)
    assert not modules & {"secrets", "random", "argparse"}
    assert not names & {"urandom", "getrandom", "token_bytes", "token_hex", "token_urlsafe",
                        "randbits", "randbelow", "SystemRandom", "draw_one", "draw_bytes",
                        "salt_bytes"}
    assert not strings & {"SYNTHETIC", "salt_creation", "raw_draw", "__main__"}


def test_w14_producer_api_accepts_no_chain_tips_history_receipts_commitment_or_mode():
    parameters = inspect.signature(pv.produce_private_verification).parameters
    assert list(parameters) == ["authority", "verifier", "expected_tip", "operation_id"]
    assert parameters["authority"].kind is inspect.Parameter.POSITIONAL_OR_KEYWORD
    assert all(parameters[name].kind is inspect.Parameter.KEYWORD_ONLY
               for name in ("verifier", "expected_tip", "operation_id"))
    for name in ("supplement_chain", "chain", "authority_tips", "active_chain_tip",
                 "preceding_chain_tip", "supplemented_history", "history_receipts", "receipts",
                 "expected_commitment", "commitment", "entropy_source", "mode",
                 "allow_synthetic"):
        with pytest.raises(TypeError):
            pv.produce_private_verification(object(), verifier=VERIFIER, expected_tip="0" * 64,
                                            operation_id=PV_OP, **{name: None})
