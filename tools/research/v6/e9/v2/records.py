"""Strict canonical v2 evidence records, distinct from authority consumption."""
from __future__ import annotations

import json
import os
import re
import stat
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

from .adoption import ADOPTED, ATTESTATION, BASE, CONVENTION, P_DIGEST, P_ID
from .adoption import canonical as canonical_bytes
from .adoption import digest as sha256


class IntegrityError(ValueError):
    """The required exact evidence does not reproduce."""


class ExecutionLocked(IntegrityError):
    """An operation lacks its separate current authorization."""


class DurableUnavailable(IntegrityError):
    """Expected regular durable evidence is missing, unreadable or unsupported."""


def regular_bytes(path: Path) -> bytes:
    """Read through Path.open after a type check, detecting ordinary object drift.

    Symlinks to regular files are supported. The check/open interval assumes no
    hostile concurrent replacement; Path.open cannot prevent that attack.
    """
    try:
        before = path.stat()
        if not stat.S_ISREG(before.st_mode):
            raise DurableUnavailable("durable path is not a regular file; unavailable")
        with path.open("rb") as stream:
            opened = os.fstat(stream.fileno())
            if not stat.S_ISREG(opened.st_mode):
                raise DurableUnavailable("opened durable object is not a regular file; unavailable")
            if (before.st_dev, before.st_ino) != (opened.st_dev, opened.st_ino):
                raise IntegrityError("durable object identity changed before read")
            raw = stream.read()
            after = os.fstat(stream.fileno())
            current = path.stat()
            if ((opened.st_dev, opened.st_ino, opened.st_size, opened.st_mtime_ns)
                    != (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
                    or (after.st_dev, after.st_ino) != (current.st_dev, current.st_ino)
                    or len(raw) != after.st_size):
                raise IntegrityError("durable object or bytes changed during read")
            return raw
    except OSError as exc:
        raise DurableUnavailable("regular durable evidence unavailable") from exc


def flush_directory(path: Path) -> bool:
    """Flush directory metadata on POSIX; Windows stdlib has no such primitive.

    This supports the absent-or-complete publication model, not a guarantee
    against controller, filesystem or physical power-loss corruption.
    """
    if os.name == "nt":
        return False
    fd = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(fd)
    finally:
        os.close(fd)
    return True


def publication_directory(path: Path) -> None:
    """Create and flush each newly introduced parent entry for scoped outputs."""
    missing = []
    parent = path
    while not parent.exists():
        missing.append(parent)
        parent = parent.parent
    for directory in reversed(missing):
        directory.mkdir(exist_ok=True)
        flush_directory(directory)
        flush_directory(directory.parent)


def publish_once(path: Path, raw: bytes, candidate: Path, *,
                 writer: Callable[[Path, bytes], None]) -> None:
    """Scoped W publication: retained candidate, flush/readback, atomic no-replace.

    Hard-link installation has no direct-write or overwrite-capable fallback.
    Unsupported filesystems fail without publishing the canonical destination.
    An existing complete destination is only compared, never written again.
    """
    publication_directory(path.parent)
    publication_directory(candidate.parent)
    if path.exists():
        if regular_bytes(path) != raw:
            raise IntegrityError("immutable publication collision")
        flush_directory(path.parent)
        return
    writer(candidate, raw)
    if regular_bytes(candidate) != raw:
        raise IntegrityError("publication candidate read-back failed")
    flush_directory(candidate.parent)
    try:
        os.link(candidate, path)
    except FileExistsError:
        if regular_bytes(path) != raw:
            raise IntegrityError("immutable publication collision") from None
    flush_directory(path.parent)


ADOPTED_RAW = "63e678d75dc8b73cc7e69ac2c413bc58d26220ec883748355d9e85c6a227f2b4"
ATTESTATION_RAW = "3dc816fa66311a58c92e041ab5acc1b3ce0ec143ceb96ee348bc10b7df92628a"
INTEGRITY_STAGES = {"BEFORE_GENERATION", "PARTIAL_GENERATION", "GENERATED", "COMMITMENT_PUBLIC",
                    "COLLECTION", "COLLECTED", "FINAL_PUBLIC"}
EVENT_KINDS = {"ISSUE", "CONSUME", "HOLD", "RELEASE", "CONTINUE", "REVOKE", "TERMINATE", "CORRECT"}


def strict_json(raw: bytes) -> Any:
    def unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for k, v in pairs:
            if k in result:
                raise IntegrityError("duplicate key")
            result[k] = v
        return result
    try:
        return json.loads(raw.decode("utf-8"), object_pairs_hook=unique,
                          parse_constant=lambda _: (_ for _ in ()).throw(
                              IntegrityError("nonfinite number")))
    except (UnicodeError, ValueError) as e:
        raise IntegrityError("invalid UTF-8 JSON") from e


def catalogue() -> dict[str, Any]:
    return strict_json(regular_bytes(BASE / "amended_record_schemas_v2_proposed_02.json"))


def exact_keys(value: Any, required: set[str], optional: set[str] | None = None) -> None:
    if (type(value) is not dict or not required <= value.keys()
            or value.keys() - required - (optional or set())):
        raise IntegrityError("missing, unknown or mistyped fields")


def nonempty(value: Any) -> None:
    if type(value) is not str or not value.strip():
        raise IntegrityError("nonempty text required")


def integer(value: Any, low: int = 0, high: int | None = None) -> None:
    if type(value) is not int or value < low or (high is not None and value > high):
        raise IntegrityError("strict integer out of range")


def validate_digest(value: Any) -> None:
    if type(value) is not str or re.fullmatch(r"[0-9a-f]{64}", value) is None:
        raise IntegrityError("full lowercase sha256 required")


def validate_artifact_ref(value: Any) -> None:
    exact_keys(value, {"bytes", "evidence_id", "sha256_raw", "visibility"})
    integer(value["bytes"])
    nonempty(value["evidence_id"])
    validate_digest(value["sha256_raw"])
    if value["visibility"] not in ("PRIVATE", "PUBLIC"):
        raise IntegrityError("unknown artifact visibility")


def validate_record_ref(value: Any) -> None:
    exact_keys(value, {"digest", "identity", "schema", "sha256_raw", "version"})
    validate_digest(value["digest"])
    validate_digest(value["sha256_raw"])
    nonempty(value["identity"])
    integer(value["version"], 1)
    matches = [s for s in catalogue()["records"].values()
               if s["schema"] == value["schema"] and s["version"] == value["version"]]
    if not matches or not any(value["identity"] == s["identity_prefix"] + value["digest"][:12]
                              for s in matches):
        raise IntegrityError("unregistered reference schema/version/identity")


def validate_actor(value: Any) -> None:
    exact_keys(value, {"actor_id", "authority_evidence", "role"})
    nonempty(value["actor_id"])
    nonempty(value["role"])
    validate_artifact_ref(value["authority_evidence"])


def validate_refs(value: Any) -> None:
    if type(value) is not dict or "c" in value:
        raise IntegrityError("dependency map requires actual earlier records; c is primitive")
    cat = catalogue()["records"]
    for role, ref in value.items():
        if role not in cat:
            raise IntegrityError("unknown dependency role")
        validate_record_ref(ref)
        if ref["schema"] != cat[role]["schema"] or ref["version"] != cat[role]["version"]:
            raise IntegrityError("dependency role/tag mismatch; v1 grants no v2 authority")


OPERATIONAL = ("P", "I", "Q", "O", "V", "A", "R", "B", "G")


def dependency_roles(role: str, body: dict[str, Any]) -> tuple[set[str], set[str]]:
    spec = catalogue()["records"][role]
    if "record_reference_dependencies" in spec:
        required = set(spec["record_reference_dependencies"])
        return required, required
    declared = spec["dependencies"]
    required = {r for r in declared if r in catalogue()["records"]}
    allowed = set(required)
    if role == "O":
        allowed.add("T")
    if role in ("S", "SeedPayload", "GenerationBoundary", "PartialGenerationSupplement"):
        required |= set(OPERATIONAL)
        allowed |= required
        allowed.add("T")  # Applicable qualification footprint remains anchored by O.
        # GenerationBoundary is a dedicated typed field in SeedPayload/S;
        # symbolic input lists do not duplicate those refs in dependencies.
        if role in ("S", "SeedPayload"):
            required.discard("GenerationBoundary")
            allowed.discard("GenerationBoundary")
        if role == "PartialGenerationSupplement":
            required.add("GenerationBoundary")
            allowed.add("GenerationBoundary")
        allowed |= {"PartialGenerationSupplement", "LeadContinuation", "PrefixSnapshot",
                    "PrefixAndKVerification", "AuthorityEvent"} - {role}
    if role == "F":
        required |= set(OPERATIONAL) | {"S", "W", "U", "C", "D"}
        allowed |= required
        allowed.add("T")
    if role in ("AuthorityEvent", "J", "LeadContinuation", "CompletedMembershipSupplement",
                "PrefixSnapshot", "PrefixAndKVerification"):
        # Dedicated fields/chains determine applicable existing records at a stage.
        allowed |= set(catalogue()["records"]) - {role, "F"}
        if role in ("J", "AuthorityEvent", "LeadContinuation", "CompletedMembershipSupplement"):
            allowed.add("F")
        if role in ("PrefixSnapshot", "PrefixAndKVerification"):
            # Partial-generation evidence precedes every completed-payload record.
            allowed -= {"SeedPayload", "S", "W", "U", "C", "D", "CompletedMembershipSupplement", "J"}
    return required, allowed


def _field(name: str, value: Any, desc: str) -> None:
    if name == "stage":
        if type(value) is not str or value not in INTEGRITY_STAGES:
            raise IntegrityError("unknown integrity stage")
    elif name == "event_kind":
        if type(value) is not str or value not in EVENT_KINDS:
            raise IntegrityError("unknown authority event")
    elif desc == "CONTINUE or RELEASE":
        if value not in ("CONTINUE", "RELEASE"):
            raise IntegrityError("unknown lead continuation disposition")
    elif name == "historical_integrity":
        if value not in ("INTACT", "HOLD_PENDING_ADJUDICATION", "HISTORICAL_OVERLAP",
                         "UNRESOLVED_HISTORICAL_INTEGRITY", "CANCELLED_PRECOLLECTION"):
            raise IntegrityError("unknown historical integrity classification")
    elif name == "F_D_S_H_statuses":
        exact_keys(value, {"F", "D", "S", "H"})
        if any(v not in ("SUPPORTED", "REFUTED", "UNRESOLVED", "NOT EVALUABLE") for v in value.values()):
            raise IntegrityError("unknown registered contrast classification")
    elif name == "scientific_classification":
        if value not in (None, "NOT EVALUABLE", "REFUTED bounded benefit claim",
                         "Behavior demonstrated; benefit NEITHER", "SUPPORTED beneficial adaptation"):
            raise IntegrityError("unknown registered scientific classification")
    elif name == "implementation_sources":
        if type(value) is not dict or not value:
            raise IntegrityError("complete raw implementation manifest required")
        for path, digest in value.items():
            nonempty(path)
            validate_digest(digest)
    elif name == "digest_recipe":
        if value != catalogue()["records"]["I"]["required_body_fields"]["digest_recipe"]:
            raise IntegrityError("instrument digest recipe is frozen")
    elif desc in ("ArtifactRef", "PRIVATE ArtifactRef", "independent PRIVATE ArtifactRef",
                  "PRIVATE ArtifactRef for exactly 32 bytes"):
        validate_artifact_ref(value)
        if "PRIVATE" in desc and value["visibility"] != "PRIVATE":
            raise IntegrityError("private artifact required")
        if name == "salt" and value["bytes"] != 32:
            raise IntegrityError("salt artifact must bind exactly 32 bytes")
    elif desc in ("Actor",):
        validate_actor(value)
    elif desc == "RecordRef" or desc.startswith("RecordRef when"):
        if value is not None:
            validate_record_ref(value)
    elif desc == "AuthorityEvent":
        validate_record_ref(value)
        if value["schema"] != catalogue()["records"]["AuthorityEvent"]["schema"]:
            raise IntegrityError("authority event reference required")
    elif "ArtifactRef list" in desc or desc == "exact ArtifactRef list" or desc == "ordered list of ArtifactRef":
        if type(value) is not list:
            raise IntegrityError("artifact list required")
        for ref in value:
            validate_artifact_ref(ref)
            if desc.startswith("PRIVATE") and ref["visibility"] != "PRIVATE":
                raise IntegrityError("private artifact required")
    elif desc == "InventoryStatus":
        spec = catalogue()["types"]["InventoryStatus"]
        exact_keys(value, set(spec))
        for flag in ("known_inventory_verification", "E6_membership", "E8_membership"):
            if value[flag] not in ("PASS", "FAIL"):
                raise IntegrityError("explicit finite verification status required")
        for flag in ("historical_completeness", "exhaustive_historical_non_reuse"):
            if value[flag] != "NOT ESTABLISHED":
                raise IntegrityError("finite verification cannot establish exhaustive history")
        contract = strict_json(regular_bytes(BASE / "amended_rule_contract_v2_proposed_02.json"))
        if (value["unresolved_gap_ids"] != contract["preserved_gap_ids"]
                or value["unresolved_dependency_ids"] != contract["preserved_dependency_ids"]):
            raise IntegrityError("all historical gap/dependency IDs must remain preserved")
    elif name in ("binding_tuple", "original_records", "unchanged_original_tuple"):
        validate_refs(value)
    elif name in ("affected_authorizations", "supplement_chain"):
        if type(value) is not list:
            raise IntegrityError("record reference chain must be a list")
        for ref in value:
            validate_record_ref(ref)
    elif name == "inventory_refs":
        exact_keys(value, {"K", "E", "L"})
        for ref in value.values():
            validate_artifact_ref(ref)
    elif desc in ("sha256", "sha256 c"):
        validate_digest(value)
    elif desc.startswith("sha256 or"):
        if value not in ("genesis", "GENESIS"):
            validate_digest(value)
    elif desc == "explicit true":
        if value is not True:
            raise IntegrityError("explicit true required")
    elif desc == "explicit boolean" or desc.startswith("explicit independently verified boolean"):
        if type(value) is not bool:
            raise IntegrityError("boolean required")
    elif desc == "1412":
        integer(value, 1412, 1412)
    elif desc.startswith("integer >= "):
        integer(value, int(desc.removeprefix("integer >= ")))
    elif name == "producer_fence_epoch":
        integer(value)
    elif name == "scientific_priority_row":
        if value is not None:
            integer(value, 1, 7)
    elif name == "last_acceptance_ordinal":
        if value is not None:
            integer(value, 1)
    elif desc == "integer 0..1411":
        integer(value, 0, 1411)
    elif name == "positions":
        if type(value) is not list or len(value) != 1412:
            raise IntegrityError("full position list required")
        for i, pos in enumerate(value, 1):
            exact_keys(pos, {"position", "value_hex"})
            integer(pos["position"], i, i)
            if type(pos["value_hex"]) is not str or not re.fullmatch(r"[0-9a-f]{16}", pos["value_hex"]):
                raise IntegrityError("uint64 representation required")
    elif name == "claim_profile":
        if value != "C-LIMITED":
            raise IntegrityError("frozen claim profile mismatch")
    elif desc == "NOT ESTABLISHED":
        if value != "NOT ESTABLISHED":
            raise IntegrityError("historical coverage remains not established")
    elif name == "permanent_limitation":
        contract = strict_json(regular_bytes(BASE / "amended_rule_contract_v2_proposed_02.json"))
        if value != contract["exact_interpretation"]["permanent_limitation_text"]:
            raise IntegrityError("permanent limitation mismatch")
    else:
        _json_tree(value)
        if value is None and name not in ("scientific_classification", "scientific_priority_row",
                                          "last_acceptance_ordinal", "immutable_original_F"):
            raise IntegrityError("required evidence cannot be null")
        if type(value) is str:
            nonempty(value)


def _T_disposition(attestation: Any, *, bound: bool) -> None:
    """O depends on T if applicable; otherwise on an explicit NOT_APPLICABLE
    disposition with reason and lead actor evidence (common.absent_records). The
    schema has no typed slot, so it lives in the custodian attestation."""
    exact_keys(attestation, {"actor", "inspection_boundary"} | (set() if bound else {"T_disposition"}))
    validate_actor(attestation["actor"])
    validate_artifact_ref(attestation["inspection_boundary"])
    if not bound:
        disposition = attestation["T_disposition"]
        exact_keys(disposition, {"actor", "disposition", "evidence", "reason"})
        nonempty(disposition["reason"])
        validate_actor(disposition["actor"])
        validate_artifact_ref(disposition["evidence"])
        if disposition["disposition"] != "NOT_APPLICABLE" or disposition["actor"]["role"] != "research_lead":
            raise IntegrityError("T absent without the lead's explicit NOT_APPLICABLE disposition")


def _json_tree(value: Any, *, floats: bool = False) -> None:
    if value is None or type(value) in (str, bool, int):
        return
    if type(value) is list:
        for item in value:
            _json_tree(item, floats=floats)
        return
    if type(value) is dict and all(type(k) is str for k in value):
        for item in value.values():
            _json_tree(item, floats=floats)
        return
    if floats and type(value) is float:
        canonical_bytes(value)  # rejects NaN/Infinity
        return
    raise IntegrityError("new record uses unsupported type or floating arithmetic")


def validate_record(record: Any, resolver: Mapping[str, Any] | Callable | None = None) -> dict:
    exact_keys(record, {"body", "digest", "digest_convention", "identity", "schema", "version"},
               {"status"})
    integer(record["version"], 2, 2)
    cat = catalogue()["records"]
    body = record["body"]
    if type(body) is not dict:
        raise IntegrityError("record body must be an object")
    role = "P" if record["schema"] == cat["P"]["schema"] else body.get("record_role")
    if role is None and record["schema"] == cat["I"]["schema"]:
        role = "I"
    if role not in cat:
        raise IntegrityError("unregistered record role")
    spec = cat[role]
    if record["schema"] != spec["schema"]:
        raise IntegrityError("record schema/role mismatch")
    fields = dict(spec["required_body_fields"])
    if role == "I":
        fields["dependencies"] = "earlier P RecordRef map"
    if role not in ("P", "I"):
        fields.update(catalogue()["common"]["body_common_fields"])
    exact_keys(body, set(fields))
    _json_tree(body, floats=role == "P")
    validate_digest(record["digest"])
    computed = sha256(canonical_bytes(body))
    if role == "I":
        validate_refs(body["dependencies"])
        if set(body["dependencies"]) != {"P"}:
            raise IntegrityError("instrument binds P only")
        computed = sha256(canonical_bytes({"protocol_digest": body["dependencies"]["P"]["digest"],
                                           "sources": body["implementation_sources"]}))
    if (record["digest"] != computed or record["identity"] != spec["identity_prefix"] + computed[:12]
            or record["digest_convention"] != CONVENTION):
        raise IntegrityError("full record digest/identity/convention mismatch")
    if role == "P":
        if record["identity"] != P_ID or record["digest"] != P_DIGEST:
            raise IntegrityError("unreviewed protocol")
        return record
    for name, desc in fields.items():
        _field(name, body[name], desc)
    if role not in ("P", "I"):
        validate_actor(body["actor"])
        if body["record_role"] != role:
            raise IntegrityError("role mismatch")
        nonempty(body["study_id"])
        nonempty(body["decision"])
        if type(body["evidence"]) is not list:
            raise IntegrityError("evidence must be an artifact list")
        for ref in body["evidence"]:
            validate_artifact_ref(ref)
        refs = body["dependencies"]
        validate_refs(refs)
        required, allowed = dependency_roles(role, body)
        if not required <= refs.keys() or refs.keys() - allowed:
            raise IntegrityError("missing/future dependency role")
        if role == "O":
            _T_disposition(body["custodian_attestation"], bound="T" in refs)
    if resolver is not None and "dependencies" in body:
        for ref in body["dependencies"].values():
            target = resolver(ref) if callable(resolver) else resolver.get(ref["digest"])
            if target is None or record_ref(target) != ref:
                raise IntegrityError("unresolved or changed exact reference")
            validate_record(target)
        for name in ("generation_boundary", "membership_receipt", "immutable_original_F"):
            ref = body.get(name)
            if ref is None:
                continue
            validate_record_ref(ref)
            target = resolver(ref) if callable(resolver) else resolver.get(ref["digest"])
            if target is None or record_ref(target) != ref:
                raise IntegrityError("unresolved dedicated record reference")
            validate_record(target)
    return record


def make_record(role: str, body: dict, status: str | None = None) -> dict:
    spec = catalogue()["records"][role]
    if role == "I":
        d = sha256(canonical_bytes({"protocol_digest": body["dependencies"]["P"]["digest"],
                                   "sources": body["implementation_sources"]}))
    else:
        d = sha256(canonical_bytes(body))
    record = {"schema": spec["schema"], "version": spec["version"], "body": body,
              "digest": d, "identity": spec["identity_prefix"] + d[:12],
              "digest_convention": CONVENTION}
    if status is not None:
        record["status"] = status
    return validate_record(record)


def record_ref(record: dict) -> dict:
    return {k: record[k] for k in ("digest", "identity", "schema", "version")} | {
        "sha256_raw": sha256(canonical_bytes(record) + b"\n")}


def read_record(path: Path, role: str | None = None, resolver=None) -> dict:
    raw = regular_bytes(path)
    record = strict_json(raw)
    if raw != canonical_bytes(record) + b"\n":
        raise IntegrityError("noncanonical record file")
    validate_record(record, resolver)
    if role is not None and record["schema"] != catalogue()["records"][role]["schema"]:
        raise IntegrityError("unexpected requested role")
    return record


def write_once(path: Path, value: Any) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = canonical_bytes(value) + b"\n"
    with path.open("xb") as handle:
        handle.write(raw)
        handle.flush()
        os.fsync(handle.fileno())
    return sha256(raw)


def load_protocol() -> dict:
    if sha256(ADOPTED.read_bytes()) != ADOPTED_RAW or sha256(ATTESTATION.read_bytes()) != ATTESTATION_RAW:
        raise IntegrityError("exact original adoption bytes required")
    p = read_record(ADOPTED, "P")
    att_raw = ATTESTATION.read_bytes()
    att = strict_json(att_raw)
    exact_keys(att, {"body", "digest", "digest_convention", "identity", "schema", "version"})
    from .adoption import PROPOSED_RAW
    if (att_raw != canonical_bytes(att) + b"\n"
            or att["body"]["reviewed_proposed_envelope_raw_sha256"] != PROPOSED_RAW):
        raise IntegrityError("exact reviewed proposal and canonical adoption attestation required")
    if (p.get("status") != "FROZEN" or att["body"]["reviewed_body_digest"] != P_DIGEST
            or att["body"]["adopted_record"]["sha256_raw"] != sha256(ADOPTED.read_bytes())
            or att["digest"] != sha256(canonical_bytes(att["body"]))):
        raise IntegrityError("valid separate adoption required")
    for name, pin in p["body"]["contract_files"].items():
        if sha256((BASE.parents[3] / name).read_bytes()) != pin["sha256_raw"]:
            raise IntegrityError("frozen contract source drift")
    return p["body"]
