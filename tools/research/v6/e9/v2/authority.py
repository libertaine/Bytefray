"""Durable, exclusive v2 authority operations. No implicit execution authority.

The caller supplies an accountable actor registry and exact record resolver.
Each protected operation rereads every record and source binding while holding
the same exclusive lock used by revocation. Interrupted append transactions
remain fail closed; they are never silently repaired by this module.
"""

from __future__ import annotations

import json
import os
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import TypeVar

from .records import (
    DurableUnavailable,
    IntegrityError,
    canonical_bytes,
    exact_keys,
    make_record,
    record_ref,
    regular_bytes,
    sha256,
    validate_actor,
    validate_artifact_ref,
    validate_record,
    validate_record_ref,
    validate_refs,
)

T = TypeVar("T")


class ProducerRegistryUnavailable(DurableUnavailable):
    """S7-DEV-F1: a registered_producers read of an entry, its G record or an event file is unavailable."""


@contextmanager
def _producer_registry_read() -> Iterator[None]:
    """Type only these mapped reads so F1 can defer them; any other Unavailable stays immediate."""
    try:
        yield
    except DurableUnavailable as exc:
        raise ProducerRegistryUnavailable(*exc.args) from exc


GENESIS = "genesis"
THROUGH_G = ("P", "I", "Q", "O", "V", "A", "R", "B", "G")
OPERATION_ROLES = {
    "raw_draw": THROUGH_G,
    "salt_creation": THROUGH_G,
    "payload_seal": THROUGH_G,
    "private_verification": (*THROUGH_G, "S"),
    "commitment_publication": (*THROUGH_G, "S", "W", "U"),
    "worker_start": (*THROUGH_G, "S", "W", "U", "C", "D"),
    "infrastructure_retry": (*THROUGH_G, "S", "W", "U", "C", "D"),
    "final_assembly": (*THROUGH_G, "S", "W", "U", "C", "D"),
    "final_seal": (*THROUGH_G, "S", "W", "U", "C", "D"),
    "result_promotion": (*THROUGH_G, "S", "W", "U", "C", "D", "F"),
}
EVENT_ROLES = {
    "ISSUE": "research_lead", "CONSUME": "recorder",
    "HOLD": "independent_integrity_verifier", "RELEASE": "research_lead",
    "CONTINUE": "research_lead", "REVOKE": "research_lead",
    "TERMINATE": "research_lead", "CORRECT": "research_lead",
}
RECORD_ROLES = {"Q": "independent_qualifier", "O": "custodian",
                "V": "independent_verifier", "B": "independent_verifier",
                "W": "independent_verifier", "S": "recorder", "C": "publisher",
                "F": "recorder", "A": "research_lead", "R": "research_lead",
                "G": "research_lead", "U": "research_lead", "D": "research_lead"}


def pinned_source_checker(repo_root: Path, instrument: dict, qualification: dict,
                          protocol_ref: dict) -> Callable[[], None]:
    """Production source callback: full I/Q raw manifests and adopted P readback."""
    root = Path(repo_root).resolve()
    def check() -> None:
        from .records import ADOPTED, read_record
        if record_ref(read_record(ADOPTED, "P")) != protocol_ref:
            raise IntegrityError("active protocol adoption changed")
        for record, key in ((instrument, "implementation_sources"),
                            (qualification, "qualification_sources")):
            manifest = record["body"].get(key)
            if not isinstance(manifest, dict) or not manifest:
                raise IntegrityError("complete source/qualification manifest required")
            for relative, expected in manifest.items():
                path = (root / relative).resolve()
                if not path.is_relative_to(root):
                    raise IntegrityError("source manifest outside repository or absent")
                if sha256(regular_bytes(path)) != expected:
                    raise IntegrityError("instrument/qualification source pin drift")
    return check


def durable_bytes(path: Path, raw: bytes) -> None:
    """Exclusive creation and read-back; interrupted bytes are retained."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    if regular_bytes(path) != raw:
        raise IntegrityError("durable evidence read-back failed")


@dataclass(frozen=True)
class Lease:
    study_id: str
    operation_id: str
    epoch: int
    authority_tip: str


class AuthorityLog:
    def __init__(self, root: Path, study_id: str, binding_tuple: dict[str, dict], *,
                 actors: dict[str, str], resolver: Callable[[dict], dict],
                 source_check: Callable[[], None]):
        if not study_id or not callable(resolver) or not callable(source_check):
            raise IntegrityError("explicit study/resolver/source checker required")
        self.root, self.study_id = Path(root), study_id
        self.bindings = json.loads(canonical_bytes(binding_tuple))
        for ref in self.bindings.values():
            validate_record_ref(ref)
        self.actors, self.resolver, self.source_check = dict(actors), resolver, source_check
        self.root.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def exclusive(self) -> Iterator[None]:
        lock = self.root / "exclusive.lock"
        try:
            fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError as exc:
            raise IntegrityError("authority busy or interrupted transaction") from exc
        try:
            os.write(fd, b"exclusive authority transaction\n")
            os.fsync(fd)
            yield
        finally:
            os.close(fd)
            lock.unlink()

    def _state(self) -> dict:
        paths = sorted(self.root.glob("event-*.json"))
        tip, epoch, held, terminal = GENESIS, 0, False, False
        active_bindings: dict = {}
        consumed: dict[str, str] = {}
        revoked: set[str] = set()
        for ordinal, path in enumerate(paths, 1):
            if path.name != f"event-{ordinal:08d}.json":
                raise IntegrityError("authority event gap/fork")
            raw = regular_bytes(path)
            event = json.loads(raw)
            if raw != canonical_bytes(event) + b"\n":
                raise IntegrityError("noncanonical authority event")
            validate_record(event)
            body = event["body"]
            if (body["prior_tip"] != tip or body["sequence"] != ordinal
                    or body["study_id"] != self.study_id):
                raise IntegrityError("authority chain or tuple mismatch")
            replaced = any(body["binding_tuple"].get(k) != v for k, v in active_bindings.items())
            if replaced:
                if body["event_kind"] != "ISSUE" or not held:
                    raise IntegrityError("replacement outside verified pre-generation reapproval")
                receipt = self._renewal_receipt(body["evidence"], active_bindings, body["binding_tuple"])
                if receipt["revocation_tip"] != tip:
                    raise IntegrityError("renewal does not bind preceding durable revocation")
                if any(active_bindings[r]["digest"] not in revoked for r in ("G", "U", "D")
                       if r in active_bindings):
                    raise IntegrityError("renewal did not revoke old generation authorities")
            if body["binding_tuple"] != active_bindings and body["event_kind"] != "ISSUE":
                raise IntegrityError("new authority bindings require an explicit ISSUE event")
            active_bindings = body["binding_tuple"]
            for ref in active_bindings.values():
                self.resolve(ref)
            self._actor(body["actor"], body["event_kind"])
            kind = body["event_kind"]
            if terminal:
                raise IntegrityError("event after terminal authority closure")
            if kind == "CONSUME":
                for ref in body["affected_authorizations"]:
                    previous = consumed.get(ref["digest"])
                    if previous is not None:
                        raise IntegrityError("replayed consumed authorization")
                    consumed[ref["digest"]] = body["operation_id"]
            if kind in {"HOLD", "REVOKE", "TERMINATE", "CORRECT"}:
                epoch += 1
            if kind == "HOLD":
                held = True
            if kind in {"RELEASE", "CONTINUE"}:
                if not held or not body["evidence"]:
                    raise IntegrityError("release without hold and independent evidence")
                held = False
            if kind in {"REVOKE", "TERMINATE", "CORRECT"}:
                revoked.update(ref["digest"] for ref in body["affected_authorizations"])
            if kind in {"TERMINATE", "CORRECT"}:
                terminal = True
            tip = event["digest"]
        active_path = self.root / "active.json"
        if paths:
            if not active_path.exists():
                raise IntegrityError("active authority tip unavailable")
            marker = json.loads(regular_bytes(active_path))
            if marker != {"sequence": len(paths), "tip": tip}:
                raise IntegrityError("unknown/stale/forked active tip")
        elif active_path.exists():
            raise IntegrityError("active tip without chain")
        return {"tip": tip, "epoch": epoch, "held": held, "terminal": terminal,
                "consumed": consumed, "revoked": revoked, "sequence": len(paths),
                "active_bindings": active_bindings}

    @property
    def tip(self) -> str:
        with self.exclusive():
            return self._state()["tip"]

    def resolve(self, ref: dict) -> dict:
        path = self.root / "evidence-records" / (ref["digest"] + ".json")
        try:
            if path.exists():
                raw = regular_bytes(path)
                record = json.loads(raw)
                if raw != canonical_bytes(record) + b"\n":
                    raise IntegrityError("retained evidence record bytes changed")
            else:
                record = self.resolver(ref)
        except DurableUnavailable:
            raise
        except (KeyError, OSError, ValueError) as exc:
            raise IntegrityError("exact record unavailable") from exc
        if record_ref(record) != ref:
            raise IntegrityError("resolved evidence record hash drift")
        return record

    def retain_record(self, record: dict) -> dict:
        validate_record(record, resolver=self.resolve)
        path = self.root / "evidence-records" / (record["digest"] + ".json")
        raw = canonical_bytes(record) + b"\n"
        if path.exists():
            if regular_bytes(path) != raw:
                raise IntegrityError("immutable evidence record collision")
        else:
            durable_bytes(path, raw)
        return record_ref(record)

    def retain_artifact(self, raw: bytes, evidence_id: str) -> dict:
        from .inventory import artifact
        ref = artifact(raw, evidence_id)
        path = self.root / "evidence-raw" / (ref["sha256_raw"] + ".bin")
        if path.exists():
            if regular_bytes(path) != raw:
                raise IntegrityError("immutable private evidence collision")
        else:
            durable_bytes(path, raw)
        return ref

    def read_artifact(self, ref: dict) -> bytes:
        validate_artifact_ref(ref)
        try:
            raw = regular_bytes(self.root / "evidence-raw" / (ref["sha256_raw"] + ".bin"))
        except OSError as exc:
            raise IntegrityError("complete private evidence unavailable") from exc
        if len(raw) != ref["bytes"] or sha256(raw) != ref["sha256_raw"]:
            raise IntegrityError("private evidence raw bytes changed")
        return raw

    def _producer_path(self, G_digest: str) -> Path:
        return self.root / "producer-roots" / (G_digest + ".json")

    def registered_producers(self) -> dict:
        """Every durable producer-registry entry, checked against its G record and the event log.

        D8-01 (Seal 08): an unavailable mapped read is deferred rather than ending the scan. Every
        check whose inputs are readable still runs, so positive mismatch evidence found later
        raises as before; only a scan that finds none raises the first deferred error. Any other
        error after a deferral ends the scan with that deferred error, where it used to stop.
        """
        from .inventory import strict_private_json
        result = {}
        deferred: ProducerRegistryUnavailable | None = None
        try:
            for path in sorted((self.root / "producer-roots").glob("*.json")):
                try:
                    with _producer_registry_read():
                        raw = regular_bytes(path)
                except ProducerRegistryUnavailable as exc:
                    deferred = deferred or exc
                    continue
                item = strict_private_json(raw)
                exact_keys(item, {"study_id", "G", "operation_id", "producer_root", "recorder", "binding_tuple"})
                validate_actor(item["recorder"])
                validate_refs(item["binding_tuple"])
                if (path.stem != item["G"]["digest"] or item["study_id"] != self.study_id
                        or item["recorder"]["role"] != "recorder"
                        or self.actors.get(item["recorder"]["actor_id"]) != "recorder"):
                    raise IntegrityError("producer registry source/study/actor mismatch")
                validate_record_ref(item["G"])
                try:
                    with _producer_registry_read():
                        G = self.resolve(item["G"])["body"]
                except ProducerRegistryUnavailable as exc:
                    deferred = deferred or exc
                else:
                    if (G["study_id"] != item["study_id"] or G["operation_id"] != item["operation_id"]
                            or item["binding_tuple"].get("G") != item["G"]):
                        raise IntegrityError("producer registry original G operation/source mismatch")
                from .inventory import artifact
                ref = artifact(raw, "PRODUCER-ROOT-" + path.stem)
                for event_path in self.root.glob("event-*.json"):
                    try:
                        with _producer_registry_read():
                            event_raw = regular_bytes(event_path)
                    except ProducerRegistryUnavailable as exc:
                        deferred = deferred or exc
                        continue
                    event = json.loads(event_raw)["body"]
                    if (event["event_kind"] == "CONSUME" and item["G"] in event["affected_authorizations"]
                            and ref not in event["evidence"]):
                        raise IntegrityError("producer registry differs from immutable G consumption evidence")
                result[path.stem] = item
        except Exception as exc:
            if deferred is None or (isinstance(exc, IntegrityError) and not isinstance(exc, DurableUnavailable)):
                raise
            raise deferred  # DV8-4: not positive mismatch evidence; the scan ends where it previously stopped
        if deferred is not None:
            raise deferred
        return result

    def register_producer(self, producer_root: Path, recorder: dict, *, operation_id: str) -> dict:
        with self.exclusive():
            state = self._state()
            if state["active_bindings"] != self.bindings or state["terminal"]:
                raise IntegrityError("producer registration uses superseded or terminal source tuple")
            self._check("raw_draw", state["tip"], operation_id, unconsumed=True, renewal_check=True)
            if recorder.get("role") != "recorder" or self.actors.get(recorder.get("actor_id")) != "recorder":
                raise IntegrityError("registered accountable recorder required")
            validate_actor(recorder)
            validate_artifact_ref(recorder["authority_evidence"])
            G = self.bindings["G"]
            item = {"study_id": self.study_id, "G": G, "operation_id": operation_id,
                    "producer_root": os.path.normcase(str(Path(producer_root).resolve())),
                    "recorder": recorder, "binding_tuple": self.original_bindings()}
            path = self._producer_path(G["digest"])
            raw = canonical_bytes(item) + b"\n"
            if path.exists():
                if path.read_bytes() != raw:
                    raise IntegrityError("same G cannot fork producer root, actor or operation")
            else:
                if G["digest"] in self._state()["consumed"]:
                    raise IntegrityError("consumed G has no recoverable original producer registry")
                for prior in self.registered_producers().values():
                    if (prior["producer_root"] == item["producer_root"]
                            and prior["G"]["digest"] not in state["revoked"]):
                        raise IntegrityError("producer root remains bound to another live G")
                durable_bytes(path, raw)
            return self.retain_artifact(raw, "PRODUCER-ROOT-" + G["digest"])

    def assert_producer(self, producer_root: Path, recorder: dict, *, operation_id: str) -> dict:
        G = self.bindings.get("G")
        if G is None:
            raise IntegrityError("producer has no G")
        item = self.registered_producers().get(G["digest"])
        if (item is None or item["operation_id"] != operation_id or item["recorder"] != recorder
                or item["producer_root"] != os.path.normcase(str(Path(producer_root).resolve()))
                or item["binding_tuple"] != self.original_bindings()):
            raise IntegrityError("producer is not original registered root/actor/tuple")
        raw = canonical_bytes(item) + b"\n"
        ref = self.retain_artifact(raw, "PRODUCER-ROOT-" + G["digest"])
        if G["digest"] in self._state()["consumed"]:
            matched = False
            for path in self.root.glob("event-*.json"):
                event = json.loads(path.read_bytes())["body"]
                if event["event_kind"] == "CONSUME" and G in event["affected_authorizations"]:
                    matched = ref in event["evidence"]
            if not matched:
                raise IntegrityError("G consumption does not bind durable original producer root")
        return ref

    def first_raw_marker(self, producer_ref: dict) -> dict:
        return {"kind": "FIRST_RAW_BOUNDARY_V2", "study_id": self.study_id,
                "G": self.bindings["G"], "producer_registry": producer_ref}

    def original_bindings(self) -> dict:
        return {role: self.bindings[role] for role in (*THROUGH_G, "T") if role in self.bindings}

    def mark_first_raw(self, producer_ref: dict) -> dict:
        raw = canonical_bytes(self.first_raw_marker(producer_ref)) + b"\n"
        path = self.root / "first-raw" / (self.bindings["G"]["digest"] + ".json")
        if path.exists():
            if path.read_bytes() != raw:
                raise IntegrityError("first raw marker corrupt or mixed")
        else:
            durable_bytes(path, raw)
        return self.retain_artifact(raw, "FIRST-RAW-" + self.bindings["G"]["digest"])

    def _renewal_receipt(self, evidence: list[dict], old: dict, new: dict) -> dict:
        from .inventory import strict_private_json
        for ref in evidence:
            if ref["evidence_id"].startswith("PREGENERATION-REAPPROVAL-"):
                receipt = strict_private_json(self.read_artifact(ref))
                if (receipt["kind"] != "PREGENERATION_REAPPROVAL_V2"
                        or receipt["study_id"] != self.study_id or receipt["old_bindings"] != old
                        or receipt["new_bindings"] != new or receipt["verified_no_first_draw"] is not True
                        or any(old.get(r) != new.get(r) for r in ("P", "I", "Q"))
                        or receipt["independent_actor"]["role"] not in {"independent_verifier", "independent_integrity_verifier"}
                        or self.actors.get(receipt["independent_actor"]["actor_id"]) != receipt["independent_actor"]["role"]):
                    raise IntegrityError("invalid exact independent pre-generation reapproval receipt")
                for digest in receipt["registered_producers"]:
                    if (self.root / "first-raw" / (digest + ".json")).exists():
                        raise IntegrityError("pre-generation renewal has a raw-generation marker")
                return receipt
        raise IntegrityError("replacement lacks independent exact pre-generation reapproval")

    def renew_before_generation(self, new_bindings: dict, lead_actor: dict, independent_actor: dict, *,
                                expected_tip: str, producer_roots: dict, evidence: list[dict]) -> dict:
        """Renew operational approvals after actual no-draw proof; preserve the same chain."""
        with self.exclusive():
            state = self._state()
            if state["tip"] != expected_tip or not state["held"] or state["terminal"]:
                raise IntegrityError("renewal requires exact current held nonterminal tip")
            old = state["active_bindings"]
            if any(old.get(r) != new_bindings.get(r) for r in ("P", "I", "Q")):
                raise IntegrityError("operational renewal cannot change P/I/Q")
            if (not set(THROUGH_G) <= set(new_bindings) or set(new_bindings) - {*THROUGH_G, "T"}
                    or any(r in old for r in ("S", "W", "C", "F"))):
                raise IntegrityError("renewal is only a complete pre-generation operational tuple")
            registered = self.registered_producers()
            if (not registered or producer_roots != registered
                    or "G" not in old or old["G"]["digest"] not in registered):
                raise IntegrityError("exact known registered producer roots required for no-draw proof")
            self.source_check()
            observed = {}
            for digest, item in registered.items():
                root = Path(item["producer_root"])
                producer_ref = self.retain_artifact(canonical_bytes(item) + b"\n", "PRODUCER-ROOT-" + digest)
                marker_raw = canonical_bytes({"kind": "FIRST_RAW_BOUNDARY_V2", "study_id": self.study_id,
                                              "G": item["G"], "producer_registry": producer_ref}) + b"\n"
                marker_copy = self.root / "evidence-raw" / (sha256(marker_raw) + ".bin")
                if (not root.is_dir() or (self.root / "first-raw" / (digest + ".json")).exists()
                        or marker_copy.exists() or any(root.glob("draw-*"))
                        or any((root / name).exists() for name in (
                            "boundary.json", "salt.bin", "salt.intent.json", "payload.json", "audit.json", "receipt.json"))):
                    raise IntegrityError("first-draw absence unverified; generation/integrity gate remains held")
                observed[digest] = {"producer_root": item["producer_root"], "no_generation_artifacts": True}
            if (independent_actor.get("role") not in {"independent_verifier", "independent_integrity_verifier"}
                    or self.actors.get(independent_actor.get("actor_id")) != independent_actor.get("role")
                    or independent_actor["actor_id"] == lead_actor["actor_id"] or not evidence):
                raise IntegrityError("specific independent no-first-draw inspection evidence required")
            validate_actor(independent_actor)
            self._actor(lead_actor, "ISSUE")
            for ref in old.values():
                self.retain_record(self.resolve(ref))
            for ref in new_bindings.values():
                self.retain_record(self.resolve(ref))
            new_G = self.resolve(new_bindings["G"])["body"]
            old_G = self.resolve(old["G"])["body"]
            if new_bindings["G"] == old["G"]:
                raise IntegrityError("renewal requires separately issued new exact G")
            previous = self.bindings
            try:
                self.bindings = json.loads(canonical_bytes(new_bindings))
                self._check("raw_draw", expected_tip, new_G["operation_id"], unconsumed=True, renewal_check=True)
            finally:
                self.bindings = previous
            revoked = self._append("REVOKE", lead_actor, state, old_G["operation_id"],
                                   [old[r] for r in ("G", "U", "D") if r in old], evidence)
            receipt = {"kind": "PREGENERATION_REAPPROVAL_V2", "study_id": self.study_id,
                       "old_bindings": old, "new_bindings": new_bindings, "prior_held_tip": expected_tip,
                       "revocation_tip": revoked["digest"], "registered_producers": registered,
                       "observed_absence": observed, "verified_no_first_draw": True,
                       "independent_actor": independent_actor, "lead_actor": lead_actor}
            receipt_ref = self.retain_artifact(canonical_bytes(receipt) + b"\n",
                                              "PREGENERATION-REAPPROVAL-" + new_bindings["G"]["digest"])
            self.bindings = json.loads(canonical_bytes(new_bindings))
            issued = self._append("ISSUE", lead_actor, self._state(), new_G["operation_id"], [],
                                  [receipt_ref, *evidence], renewal_receipt=receipt_ref)
            released = self._append("RELEASE", lead_actor, self._state(), new_G["operation_id"], [],
                                    [receipt_ref, *evidence], renewal_receipt=receipt_ref)
            return {"revocation": revoked, "issue": issued, "release": released, "receipt": receipt_ref}

    def _actor(self, actor: dict, kind: str) -> None:
        role = EVENT_ROLES.get(kind)
        if kind == "CONSUME" and actor.get("role") in {"recorder", "publisher"}:
            role = actor["role"]
        if (role is None or actor.get("role") != role
                or self.actors.get(actor.get("actor_id")) != role):
            raise IntegrityError("actor lacks event authority")
        validate_artifact_ref(actor["authority_evidence"])

    def _append(self, kind: str, actor: dict, state: dict, operation_id: str,
                affected: list[dict], evidence: list[dict], release_record: dict | None = None,
                renewal_receipt: dict | None = None) -> dict:
        self._actor(actor, kind)
        if state["terminal"]:
            raise IntegrityError("study authority terminal")
        if kind != "ISSUE" and state["active_bindings"] != self.bindings:
            raise IntegrityError("new binding tuple not actively issued")
        if kind == "ISSUE":
            if any(self.bindings.get(r) != ref for r, ref in state["active_bindings"].items()):
                if renewal_receipt is None or not state["held"]:
                    raise IntegrityError("changed operational tuple requires verified no-draw reapproval")
                self._renewal_receipt(evidence, state["active_bindings"], self.bindings)
            for ref in self.bindings.values():
                resolved = self.resolve(ref)
                validate_record(resolved, resolver=self.resolve)
                if record_ref(resolved) != ref:
                    raise IntegrityError("ISSUE references unavailable/swapped record")
                for earlier_role, earlier_ref in resolved["body"].get("dependencies", {}).items():
                    if self.bindings.get(earlier_role) != earlier_ref:
                        raise IntegrityError("ISSUE depends on an absent/future/mixed record")
        if kind in {"RELEASE", "CONTINUE"} and (not state["held"] or not evidence):
            raise IntegrityError("release without hold and independent evidence")
        if kind == "RELEASE" and renewal_receipt is not None:
            from .inventory import strict_private_json
            receipt = strict_private_json(self.read_artifact(renewal_receipt))
            self._renewal_receipt([renewal_receipt], receipt["old_bindings"], self.bindings)
            if receipt["lead_actor"] != actor:
                raise IntegrityError("renewal release actor differs from exact reapproval")
        elif kind in {"RELEASE", "CONTINUE"}:
            if release_record is None:
                raise IntegrityError("exact separate lead continuation record required")
            validate_record(release_record, resolver=self.resolve)
            body = release_record["body"]
            if (body["record_role"] != "LeadContinuation" or body["actor"] != actor
                    or body["study_id"] != self.study_id or body["operation_id"] != operation_id
                    or body["unchanged_original_tuple"] != self.bindings
                    or body["decision"] != "AUTHORIZED" or body["disposition"] != kind):
                raise IntegrityError("invalid exact lead continuation authority")
            event_ref = body["dependencies"].get("AuthorityEvent")
            if event_ref is None or event_ref["digest"] != state["tip"]:
                raise IntegrityError("lead continuation does not bind active hold tip")
            supplements = [body["dependencies"].get(role) for role in (
                "PartialGenerationSupplement", "CompletedMembershipSupplement")]
            supplement_ref = next((ref for ref in supplements if ref is not None), None)
            # CONTINUE follows verified new history (PG-R8); RELEASE follows a
            # conclusive disproval or post-boundary-only use (PG-R7).
            if (supplement_ref is None) != (kind == "RELEASE"):
                raise IntegrityError("lead continuation lacks independent supplement")
            supplement = None if supplement_ref is None else self.resolve(supplement_ref)["body"]
            if supplement is None:
                self._check_disproval_release(body, actor, state)
            elif supplement["record_role"] == "PartialGenerationSupplement":
                membership = self.resolve(supplement["membership_receipt"])["body"]
                if (membership["actor"]["role"] not in {"independent_verifier", "independent_integrity_verifier"}
                        or self.actors.get(membership["actor"]["actor_id"]) != membership["actor"]["role"]
                        or membership["original_bindings_valid"] is not True
                        or membership["all_new_values_in_original_K"] is not True
                        or membership["accepted_prefix_intersection"].get("count") != 0):
                    raise IntegrityError("partial continuation fails independent prefix/K receipt")
                from .inventory import strict_private_json
                private_receipt = strict_private_json(self.read_artifact(
                    membership["prior_use_scope_temporal_receipt"]))
                snapshot = self.resolve(supplement["dependencies"]["PrefixSnapshot"])["body"]
                original = self.resolve(self.bindings["O"])["body"]
                if (membership["decision"] != "PASS" or private_receipt["disposition"] != "NEW_HISTORY"
                        or private_receipt["intersection"] != []
                        or private_receipt["all_values_in_original_K"] is not True
                        or private_receipt["accepted_digest"] != snapshot["ordered_prefix"]["sha256_raw"]
                        or private_receipt["original_K_digest"] != original["K"]["sha256_raw"]):
                    raise IntegrityError("partial continuation evidence unresolved/mixed/outside original K")
            else:
                from .inventory import strict_private_json
                private_receipt = strict_private_json(self.read_artifact(
                    supplement["independent_full_list_non_overlap_receipt"]))
                if private_receipt["disposition"] != "NEW_HISTORY" or private_receipt["intersection"] != []:
                    raise IntegrityError("completed continuation lacks independently proved non-overlap")
            raw_release = canonical_bytes(release_record) + b"\n"
            if not any(ref["sha256_raw"] == sha256(raw_release) and ref["bytes"] == len(raw_release)
                       for ref in evidence):
                raise IntegrityError("continuation event missing exact lead record evidence")
        for ref in affected:
            validate_record_ref(ref)
            if ref not in self.bindings.values():
                raise IntegrityError("affected authorization absent from exact tuple")
            if kind == "CONSUME" and ref["digest"] in state["consumed"]:
                raise IntegrityError("authorization already consumed")
            if kind == "CONSUME":
                required_actor = "publisher" if ref == self.bindings.get("U") else "recorder"
                if actor["role"] != required_actor:
                    raise IntegrityError("wrong authorization consumer role")
        for ref in evidence:
            validate_artifact_ref(ref)
        event = make_record("AuthorityEvent", {
            "record_role": "AuthorityEvent", "decision": kind,
            "dependencies": self.bindings,
            "actor": actor, "affected_authorizations": affected,
            "binding_tuple": self.bindings, "event_kind": kind, "evidence": evidence,
            "operation_id": operation_id, "prior_tip": state["tip"],
            "sequence": state["sequence"] + 1, "study_id": self.study_id,
        })
        durable_bytes(self.root / f"event-{state['sequence'] + 1:08d}.json",
                      canonical_bytes(event) + b"\n")
        # A crash between event and active-tip replacement fails closed on reopen.
        pending = self.root / f"active-{state['sequence'] + 1:08d}.pending"
        durable_bytes(pending, canonical_bytes({"sequence": state["sequence"] + 1,
                                               "tip": event["digest"]}) + b"\n")
        os.replace(pending, self.root / "active.json")
        self._state()
        return event

    def _check_disproval_release(self, body: dict, actor: dict, state: dict) -> None:
        """PG-R7 release: an independent verifier's conclusive receipt, its raw inputs
        and, during partial generation, the producer's sealed paused prefix."""
        from .integrity import DISPOSITION_RECEIPT_ID, RELEASABLE
        from .inventory import strict_private_json
        refs = [ref for ref in body["evidence"] if ref["evidence_id"] == DISPOSITION_RECEIPT_ID]
        if len(refs) != 1:
            raise IntegrityError("release lacks exactly one independent disposition receipt")
        receipt = strict_private_json(self.read_artifact(refs[0]))
        if not isinstance(receipt, dict):
            raise IntegrityError("release lacks exactly one independent disposition receipt")
        verifier = receipt.get("verifier_id")
        if (receipt.get("disposition") not in RELEASABLE or receipt.get("values") != []
                or receipt.get("intersection") != [] or verifier == actor["actor_id"]
                or self.actors.get(verifier) not in {"independent_verifier", "independent_integrity_verifier"}):
            raise IntegrityError("release lacks an independent conclusive disproval or post-boundary receipt")
        inputs = {ref["sha256_raw"]: ref for ref in body["evidence"]}
        digests = receipt.get("evidence_digests")
        if not isinstance(digests, list) or not digests or any(d not in inputs for d in digests):
            raise IntegrityError("release omits the receipt's raw historical inputs")
        for digest in digests:
            self.read_artifact(inputs[digest])
        generation = self.bindings.get("G")
        if generation is None or generation["digest"] not in state["consumed"]:
            raise IntegrityError("before generation a disposed allegation renews the inventory gate")
        if "S" in self.bindings:
            boundary = self.resolve(self.bindings["S"])["body"]["generation_boundary"]
        else:
            snapshot_ref = body["dependencies"].get("PrefixSnapshot")
            if snapshot_ref is None:
                raise IntegrityError("partial-generation release must bind the sealed paused prefix")
            snapshot = self.resolve(snapshot_ref)["body"]
            if (snapshot["record_role"] != "PrefixSnapshot" or snapshot["study_id"] != self.study_id
                    or snapshot["actor"]["role"] != "recorder"
                    or self.actors.get(snapshot["actor"]["actor_id"]) != "recorder"):
                raise IntegrityError("paused prefix snapshot lacks the original recorder")
            boundary = snapshot["dependencies"]["GenerationBoundary"]
        if receipt.get("boundary_digest") != boundary["digest"]:
            raise IntegrityError("disposition receipt binds a different generation boundary")

    def append(self, kind: str, actor: dict, *, expected_tip: str, operation_id: str,
               affected: list[dict] | None = None, evidence: list[dict] | None = None,
               release_record: dict | None = None) -> dict:
        with self.exclusive():
            state = self._state()
            if state["tip"] != expected_tip:
                raise IntegrityError("stale active authority tip")
            return self._append(kind, actor, state, operation_id, affected or [], evidence or [], release_record)

    def _check(self, operation: str, expected_tip: str, operation_id: str, *,
               unconsumed: bool = False, publication_consumed: bool = False,
               renewal_check: bool = False) -> dict:
        state = self._state()
        if (state["tip"] != expected_tip or state["terminal"]
                or not renewal_check and (state["held"] or state["active_bindings"] != self.bindings)):
            raise IntegrityError("stale, held or terminal authority")
        roles = OPERATION_ROLES.get(operation)
        if roles is None or not operation_id or state["sequence"] == 0:
            raise IntegrityError("unknown or unissued operation")
        self.source_check()
        for role in roles:
            ref = self.bindings.get(role)
            if ref is None or ref["digest"] in state["revoked"]:
                raise IntegrityError("missing/revoked authority binding")
            record = self.resolve(ref)
            validate_record(record, resolver=self.resolve)
            if record_ref(record) != ref:
                raise IntegrityError("authority raw/body hash drift")
            body = record["body"]
            if role == "P" and record.get("status") != "FROZEN":
                raise IntegrityError("proposed protocol envelope supplies no frozen authority")
            if role in RECORD_ROLES:
                actor = body["actor"]
                if (actor["role"] != RECORD_ROLES[role]
                        or self.actors.get(actor["actor_id"]) != actor["role"]):
                    raise IntegrityError("record actor lacks required scoped role")
                approved = {"PASS"} if role in {"Q", "V", "B", "W"} else {
                    "AUTHORIZED", "APPROVED", "SEALED", "RECORDED", "PUBLISHED"}
                if body["decision"] not in approved:
                    raise IntegrityError("record lacks affirmative scoped decision")
            if role not in {"P", "I"} and body.get("study_id") != self.study_id:
                raise IntegrityError("mixed study authority")
            for dependency, bound in body.get("dependencies", {}).items():
                if self.bindings.get(dependency) != bound:
                    raise IntegrityError("mixed dependency binding")
            if role in {"A", "R"}:
                original = self.resolve(self.bindings["O"])["body"]
                if any(body[key] != original[key] for key in ("K", "E", "L")):
                    raise IntegrityError("mixed original K/E/L operational versions")
                from .inventory import frozen_limitations
                gaps, dependencies = frozen_limitations()
                scope = body["approved_scope"] if role == "A" else body["accepted_limitation"]
                if (not isinstance(scope, dict)
                        or scope.get("historical_coverage") != "NOT ESTABLISHED"
                        or scope.get("unresolved_gap_ids") != gaps
                        or scope.get("unresolved_dependency_ids") != dependencies
                        or not scope.get("inspection_boundary")):
                    raise IntegrityError("approval/risk waiver omits exact unresolved scope")
                if role == "R" and (body["risk"] != "H UNKNOWN; no useful numeric bound; only worst-case bound 1"
                        or scope.get("assurance") != "known-history non-reuse only"
                        or scope.get("unknown_history_risk") != body["risk"]
                        or body["claim_profile"] != "C-LIMITED"):
                    raise IntegrityError("generic waiver cannot accept specific operational residual risk")
            if role in {"O", "V"}:
                status = body["status_fields"]
                if any(status[key] != "PASS" for key in (
                        "known_inventory_verification", "E6_membership", "E8_membership")):
                    raise IntegrityError("finite known inventory verification failed")
                if role == "V" and body["unreproduced_items"]:
                    raise IntegrityError("inventory contains unreproduced known derivations")
                if role == "O":
                    attestation = body["custodian_attestation"]
                    if (not isinstance(attestation, dict) or attestation.get("actor") != body["actor"]
                            or "inspection_boundary" not in attestation):
                        raise IntegrityError("custodian exact inspection-boundary attestation absent")
                    validate_artifact_ref(attestation["inspection_boundary"])
                    # T if applicable; otherwise the lead's explicit NOT_APPLICABLE disposition.
                    not_applicable = attestation.get("T_disposition")
                    if ("T" in body["dependencies"]) == (not_applicable is not None) or (
                            not_applicable is not None
                            and self.actors.get(not_applicable["actor"]["actor_id"]) != "research_lead"):
                        raise IntegrityError("T requires a receipt or the lead's explicit NOT_APPLICABLE disposition")
            if role == "S" and body["operation_id"] != self.resolve(
                    self.bindings["G"])["body"]["operation_id"]:
                raise IntegrityError("different original generation operation")
            if (role == "G" and operation in {"raw_draw", "salt_creation", "payload_seal"}
                    and body["operation_id"] != operation_id):
                raise IntegrityError("different original generation operation")
        commitments = [self.resolve(self.bindings[role])["body"]["commitment"]
                       for role in ("W", "U", "C") if role in roles]
        if len(set(commitments)) > 1:
            raise IntegrityError("mixed W/U/C primitive commitment")
        if "W" in roles:
            # R11: W binds S and the exact private payload/salt bytes that S records.
            verified = self.resolve(self.bindings["W"])["body"]
            receipt = self.resolve(self.bindings["S"])["body"]
            if any((verified[f]["sha256_raw"], verified[f]["bytes"])
                   != (receipt[f]["sha256_raw"], receipt[f]["bytes"]) for f in ("payload", "salt")):
                raise IntegrityError("W does not verify the payload/salt bytes bound by S")
        if "I" in roles and "Q" in roles:
            producer_ids = set()
            for role in ("O", "S"):
                if role in self.bindings:
                    producer_ids.add(self.resolve(self.bindings[role])["body"]["actor"]["actor_id"])
            for role in ("Q", "V", "B", "W"):
                if role in roles and self.resolve(self.bindings[role])["body"]["actor"]["actor_id"] in producer_ids:
                    raise IntegrityError("independent verifier equals producing actor")
        if not unconsumed and "G" in roles:
            generation_op = self.resolve(self.bindings["G"])["body"]["operation_id"]
            if state["consumed"].get(self.bindings["G"]["digest"]) != generation_op:
                raise IntegrityError("G is not consumed by this exact operation")
        if operation == "commitment_publication":
            consumed = state["consumed"].get(self.bindings["U"]["digest"])
            if (consumed is not None and (not publication_consumed or consumed != operation_id)
                    or publication_consumed and consumed is None):
                raise IntegrityError("publication authority already consumed or not consumed here")
        return state

    def consume_generation(self, actor: dict, *, expected_tip: str,
                           operation_id: str, evidence: list[dict]) -> dict:
        with self.exclusive():
            # Validate complete sources and tuple before the durable single use.
            state = self._state()
            if state["tip"] != expected_tip or state["held"] or state["terminal"]:
                raise IntegrityError("generation authority unavailable")
            self.source_check()
            generation = self.bindings.get("G")
            if generation is None or generation["digest"] in state["consumed"]:
                raise IntegrityError("G absent or already consumed")
            # Temporarily check tuple through a non-consuming gate, then consume.
            record = self.resolve(generation)
            validate_record(record, resolver=self.resolve)
            if (record_ref(record) != generation or record["body"]["operation_id"] != operation_id
                    or record["body"]["study_id"] != self.study_id):
                raise IntegrityError("G binding/operation drift")
            self._check("raw_draw", expected_tip, operation_id, unconsumed=True)
            registered = self.registered_producers().get(generation["digest"])
            if registered is None or registered["recorder"] != actor:
                raise IntegrityError("G cannot be consumed without its exact original accountable producer")
            producer_ref = self.assert_producer(Path(registered["producer_root"]), actor,
                                                operation_id=operation_id)
            return self._append("CONSUME", actor, state, operation_id,
                                [generation], [*evidence, producer_ref])

    def protected(self, operation: str, *, expected_tip: str, operation_id: str,
                  action: Callable[[Lease], T], consumer_actor: dict | None = None) -> T:
        with self.exclusive():
            state = self._check(operation, expected_tip, operation_id)
            if operation == "commitment_publication":
                if consumer_actor is None or consumer_actor.get("role") != "publisher":
                    raise IntegrityError("explicit authorized publisher required")
                consumed = self._append("CONSUME", consumer_actor, state, operation_id,
                                        [self.bindings["U"]], [])
                expected_tip = consumed["digest"]
                state = self._check(operation, expected_tip, operation_id, publication_consumed=True)
            lease = Lease(self.study_id, operation_id, state["epoch"], state["tip"])
            result = action(lease)
            self._check(operation, expected_tip, operation_id,
                        publication_consumed=operation == "commitment_publication")
            return result

    def retain_worker_artifact(self, lease: Lease, raw: bytes, *, artifact_id: str) -> dict:
        if not artifact_id or any(c not in "abcdefghijklmnopqrstuvwxyz0123456789-_" for c in artifact_id):
            raise IntegrityError("opaque artifact ID required")
        with self.exclusive():
            state = self._state()
            late = (lease.study_id != self.study_id or lease.epoch != state["epoch"]
                    or state["held"] or state["terminal"])
            durable_bytes(self.root / "retained" / (artifact_id + ".bin"), raw)
            receipt = {"artifact_id": artifact_id, "sha256_raw": sha256(raw),
                       "bytes": len(raw), "late_fenced": late, "eligible": not late,
                       "lease_epoch": lease.epoch, "active_epoch": state["epoch"]}
            durable_bytes(self.root / "retained" / (artifact_id + ".json"),
                          canonical_bytes(receipt) + b"\n")
            return receipt
