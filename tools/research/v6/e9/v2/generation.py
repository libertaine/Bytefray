"""Single-operation, fenced deterministic-injection-capable generation producer.

There is no command-line entropy or match entry point. Qualification injects
byte streams. Real entropy is reached only inside a verified G protected action.
All raw candidates, intents and interrupted attempts are retained privately.
"""

from __future__ import annotations

import json
import os
from collections.abc import Callable
from pathlib import Path

from .authority import AuthorityLog, Lease, durable_bytes
from .inventory import artifact, strict_private_json, values_checked
from .records import (
    IntegrityError,
    canonical_bytes,
    make_record,
    record_ref,
    sha256,
    validate_artifact_ref,
)

N = 1412
DOMAIN = "uint64/big-endian/OS CSPRNG/accepted draw order"
ENTROPY_SOURCES = {"REAL": "os.urandom", "SYNTHETIC": "injected deterministic synthetic byte stream"}


def entropy_declaration(mode: str, *, study_id: str, G: dict, operation_id: str) -> dict:
    """Private boundary evidence naming where every raw draw and the salt come from."""
    if mode not in ENTROPY_SOURCES:
        raise IntegrityError("entropy source must be REAL or SYNTHETIC")
    return {"kind": "ENTROPY_SOURCE_V2", "mode": mode, "draw_source": ENTROPY_SOURCES[mode],
            "salt_source": ENTROPY_SOURCES[mode], "study_id": study_id, "G": G,
            "operation_id": operation_id}


class Generator:
    def __init__(self, root: Path, authority: AuthorityLog, *, operation_id: str,
                 recorder: dict, original_K_raw: bytes, inventory_refs: dict,
                 draw_bytes: Callable[[int], bytes] | None,
                 salt_bytes: Callable[[int], bytes] | None, mode: str):
        if mode not in ENTROPY_SOURCES or not operation_id:
            raise IntegrityError("explicit generation mode and original operation required")
        if mode == "SYNTHETIC" and (not callable(draw_bytes) or not callable(salt_bytes)):
            raise IntegrityError("synthetic byte streams must be injected")
        if mode == "REAL" and (draw_bytes is not None or salt_bytes is not None):
            raise IntegrityError("real OS-CSPRNG generation accepts no injected byte stream")
        self.root, self.authority = Path(root), authority
        self.operation_id, self.recorder, self.mode = operation_id, recorder, mode
        self.K = set(values_checked(strict_private_json(original_K_raw)))
        self.original_K_raw = bytes(original_K_raw)
        self.inventory_refs = json.loads(canonical_bytes(inventory_refs))
        if set(inventory_refs) != {"K", "E", "L"}:
            raise IntegrityError("original exact K/E/L refs required")
        for ref in inventory_refs.values():
            validate_artifact_ref(ref)
        if (inventory_refs["K"]["sha256_raw"] != sha256(original_K_raw)
                or inventory_refs["K"]["bytes"] != len(original_K_raw)):
            raise IntegrityError("original K bytes do not match binding")
        seal_ref = authority.bindings.get("O")
        if seal_ref is None:
            raise IntegrityError("original approved inventory seal absent")
        seal = authority.resolver(seal_ref)["body"]
        if any(seal[key] != inventory_refs[key] for key in ("K", "E", "L")):
            raise IntegrityError("generation K/E/L differ from original authority tuple")
        self.draw_bytes, self.salt_bytes = draw_bytes, salt_bytes
        self.root.mkdir(parents=True, exist_ok=True)
        self.producer_ref = self.authority.register_producer(self.root, self.recorder,
                                                            operation_id=self.operation_id)

    def _common(self, role: str, decision: str, dependencies: dict) -> dict:
        return {"record_role": role, "study_id": self.authority.study_id,
                "actor": self.recorder, "decision": decision,
                "dependencies": dependencies, "evidence": []}

    def _boundary(self) -> dict | None:
        self.authority.assert_producer(self.root, self.recorder, operation_id=self.operation_id)
        path = self.root / "boundary.json"
        if not path.exists():
            return None
        raw = path.read_bytes()
        boundary = strict_private_json(raw)
        from .records import validate_record
        validate_record(boundary)
        body = boundary["body"]
        if (body["operation_id"] != self.operation_id
                or body["study_id"] != self.authority.study_id
                or body["dependencies"] != self.authority.bindings):
            raise IntegrityError("generation boundary tuple changed")
        marker_path = self.authority.root / "first-raw" / (
            self.authority.bindings["G"]["digest"] + ".json")
        marker_raw = canonical_bytes(self.authority.first_raw_marker(self.producer_ref)) + b"\n"
        if not marker_path.exists() or marker_path.read_bytes() != marker_raw:
            raise IntegrityError("original first-raw fencing marker unavailable or corrupt")
        if self.producer_ref not in body["evidence"]:
            raise IntegrityError("generation boundary omits original producer identity")
        declared = []
        for ref in body["evidence"]:
            raw = self.authority.read_artifact(ref)
            if ref["evidence_id"].startswith("ENTROPY-SOURCE-"):
                declared.append(strict_private_json(raw))
        if declared != [self._entropy()]:
            raise IntegrityError("generation boundary entropy source differs from this producer")
        return boundary

    def _entropy(self) -> dict:
        return entropy_declaration(self.mode, study_id=self.authority.study_id,
                                   G=self.authority.bindings["G"], operation_id=self.operation_id)

    def read_audit(self) -> tuple[list[dict], list[str], str]:
        boundary = self._boundary()
        entries: list[dict] = []
        accepted: list[str] = []
        tip = boundary["digest"] if boundary else "genesis"
        intents = sorted(self.root.glob("draw-*.intent.json"))
        audits = sorted(self.root.glob("draw-*.audit.json"))
        if len(intents) != len(audits):
            raise IntegrityError("interrupted raw draw; audit integrity unresolved")
        for ordinal, path in enumerate(audits, 1):
            if path.name != f"draw-{ordinal:08d}.audit.json":
                raise IntegrityError("raw audit gap/fork")
            intent_path = self.root / f"draw-{ordinal:08d}.intent.json"
            if not intent_path.exists() or boundary is None:
                raise IntegrityError("draw without durable boundary/intent")
            intent = strict_private_json(intent_path.read_bytes())
            item = strict_private_json(path.read_bytes())
            if set(item) != {"entry", "digest"}:
                raise IntegrityError("unknown audit envelope field")
            entry = item["entry"]
            if (set(entry) != {"raw_draw_ordinal", "raw_bytes_hex", "disposition",
                              "accepted_position", "authority_tip", "prior_entry_digest"}
                    or type(entry["raw_draw_ordinal"]) is not int
                    or entry["raw_draw_ordinal"] != ordinal
                    or entry["prior_entry_digest"] != tip
                    or item["digest"] != sha256(canonical_bytes(entry))
                    or intent != {"ordinal": ordinal, "operation_id": self.operation_id,
                                  "authority_tip": entry["authority_tip"], "prior_tip": tip}):
                raise IntegrityError("raw audit/intention/chain mismatch")
            value = values_checked([entry["raw_bytes_hex"]])[0]
            disposition = "REJECT_K" if value in self.K else (
                "REJECT_DUPLICATE" if value in accepted else "ACCEPT")
            position = len(accepted) + 1 if disposition == "ACCEPT" else None
            if (entry["disposition"] != disposition or entry["accepted_position"] != position
                    or position is not None and type(entry["accepted_position"]) is not int):
                raise IntegrityError("raw acceptance/rejection decision does not reproduce")
            if disposition == "ACCEPT":
                accepted.append(value)
            entries.append(entry)
            tip = item["digest"]
        if len(accepted) > N:
            raise IntegrityError("accepted list exceeds fixed N")
        return entries, accepted, tip

    def consume(self, *, expected_tip: str, boundary_evidence: dict) -> dict:
        if self._boundary() is not None or list(self.root.glob("draw-*")):
            raise IntegrityError("generation operation already started")
        return self.authority.consume_generation(
            self.recorder, expected_tip=expected_tip, operation_id=self.operation_id,
            evidence=[boundary_evidence])

    def draw_one(self, *, expected_tip: str, durable_instant: dict) -> dict:
        def action(lease: Lease) -> dict:
            entries, accepted, audit_tip = self.read_audit()
            if len(accepted) == N or (self.root / "salt.bin").exists():
                raise IntegrityError("no raw draws after accepted-list completion")
            boundary = self._boundary()
            if boundary is None:
                marker_path = self.authority.root / "first-raw" / (
                    self.authority.bindings["G"]["digest"] + ".json")
                marker_raw = canonical_bytes(self.authority.first_raw_marker(self.producer_ref)) + b"\n"
                marker_copy = self.authority.root / "evidence-raw" / (sha256(marker_raw) + ".bin")
                if marker_path.exists() or marker_copy.exists():
                    raise IntegrityError("first raw began but original boundary is unavailable; integrity hold required")
                marker_ref = self.authority.mark_first_raw(self.producer_ref)
                entropy_ref = self.authority.retain_artifact(
                    canonical_bytes(self._entropy()) + b"\n",
                    "ENTROPY-SOURCE-" + self.authority.bindings["G"]["digest"])
                body = self._common("GenerationBoundary", "RECORDED", self.authority.bindings)
                body["evidence"] = [self.producer_ref, marker_ref, entropy_ref]
                body.update(active_authority_tip=lease.authority_tip,
                            durable_instant=durable_instant, operation_id=self.operation_id,
                            producer_fence_epoch=lease.epoch)
                boundary = make_record("GenerationBoundary", body)
                durable_bytes(self.root / "boundary.json", canonical_bytes(boundary) + b"\n")
                self._boundary()
                audit_tip = boundary["digest"]
            ordinal = len(entries) + 1
            self.authority.assert_producer(self.root, self.recorder, operation_id=self.operation_id)
            intent = {"ordinal": ordinal, "operation_id": self.operation_id,
                      "authority_tip": lease.authority_tip, "prior_tip": audit_tip}
            durable_bytes(self.root / f"draw-{ordinal:08d}.intent.json",
                          canonical_bytes(intent) + b"\n")
            source = self.draw_bytes if self.mode == "SYNTHETIC" else os.urandom
            raw = source(8)
            if not isinstance(raw, bytes) or len(raw) != 8:
                raise IntegrityError("raw uint64 draw must be exactly eight bytes")
            value = f"{int.from_bytes(raw, 'big'):016x}"
            disposition = "REJECT_K" if value in self.K else (
                "REJECT_DUPLICATE" if value in accepted else "ACCEPT")
            entry = {"raw_draw_ordinal": ordinal, "raw_bytes_hex": value,
                     "disposition": disposition,
                     "accepted_position": len(accepted) + 1 if disposition == "ACCEPT" else None,
                     "authority_tip": lease.authority_tip, "prior_entry_digest": audit_tip}
            item = {"entry": entry, "digest": sha256(canonical_bytes(entry))}
            durable_bytes(self.root / f"draw-{ordinal:08d}.audit.json",
                          canonical_bytes(item) + b"\n")
            self.read_audit()
            return entry
        return self.authority.protected("raw_draw", expected_tip=expected_tip,
                                        operation_id=self.operation_id, action=action)

    def snapshot(self, *, evidence: dict, snapshot_id: str) -> dict:
        with self.authority.exclusive():
            self.authority.source_check()
            self.authority.assert_producer(self.root, self.recorder, operation_id=self.operation_id)
            state = self.authority._state()
            if state["active_bindings"] != self.authority.bindings:
                raise IntegrityError("snapshot uses superseded operational bindings")
            if not state["held"] or state["terminal"]:
                # Draws are fenced only while held, so the sealed prefix is the stop state.
                raise IntegrityError("prefix snapshot requires the active stop/hold")
        entries, accepted, tip = self.read_audit()
        boundary = self._boundary()
        if boundary is None or len(accepted) >= N or not snapshot_id.isalnum():
            raise IntegrityError("partial immutable prefix snapshot required")
        prefix_raw = canonical_bytes([{"position": i, "value_hex": v}
                                      for i, v in enumerate(accepted, 1)]) + b"\n"
        durable_bytes(self.root / f"prefix-{snapshot_id}.json", prefix_raw)
        body = self._common("PrefixSnapshot", "SEALED", {
            **self.authority.bindings, "GenerationBoundary": record_ref(boundary)})
        body.update(accepted_count=len(accepted), audit_position=len(entries), audit_tip=tip,
                    last_acceptance_ordinal=next((e["raw_draw_ordinal"] for e in reversed(entries)
                                                if e["disposition"] == "ACCEPT"), None),
                    ordered_prefix=artifact(prefix_raw, "PREFIX-" + snapshot_id),
                    stop_fencing_evidence=evidence)
        record = make_record("PrefixSnapshot", body)
        durable_bytes(self.root / f"snapshot-{snapshot_id}.json", canonical_bytes(record) + b"\n")
        return record

    def complete(self, *, expected_tip: str, preceding_chain_tip: str) -> dict:
        if preceding_chain_tip != expected_tip:
            raise IntegrityError("payload must bind the current preceding chain tip")

        def salt_action(_: Lease) -> None:
            self.authority.assert_producer(self.root, self.recorder, operation_id=self.operation_id)
            _, accepted, _ = self.read_audit()
            if len(accepted) != N:
                raise IntegrityError("salt forbidden before complete accepted list")
            if (self.root / "salt.intent.json").exists() or (self.root / "salt.bin").exists():
                raise IntegrityError("salt creation already attempted")
            durable_bytes(self.root / "salt.intent.json", canonical_bytes({
                "operation_id": self.operation_id, "authority_tip": expected_tip}) + b"\n")
            source = self.salt_bytes if self.mode == "SYNTHETIC" else os.urandom
            salt = source(32)
            if not isinstance(salt, bytes) or len(salt) != 32:
                raise IntegrityError("salt must contain exactly 32 bytes")
            durable_bytes(self.root / "salt.bin", salt)
        self.authority.protected("salt_creation", expected_tip=expected_tip,
                                 operation_id=self.operation_id, action=salt_action)
        payload = self.seal_payload(expected_tip=expected_tip, preceding_chain_tip=preceding_chain_tip)
        self.generation_receipt(expected_tip=expected_tip)
        return payload

    def seal_payload(self, *, expected_tip: str, preceding_chain_tip: str) -> dict:
        def action(lease: Lease) -> dict:
            # PG-R8: the immutable payload binds the current continuation tip forward.
            if preceding_chain_tip != lease.authority_tip:
                raise IntegrityError("payload must bind the current preceding chain tip")
            self.authority.assert_producer(self.root, self.recorder, operation_id=self.operation_id)
            entries, accepted, _ = self.read_audit()
            if len(accepted) != N or len((self.root / "salt.bin").read_bytes()) != 32:
                raise IntegrityError("complete accepted list and exact salt required")
            audit_raw = canonical_bytes(entries) + b"\n"
            durable_bytes(self.root / "audit.json", audit_raw)
            boundary = self._boundary()
            body = self._common("SeedPayload", "SEALED", self.authority.bindings)
            body.update(N=N, domain=DOMAIN, operation_id=self.operation_id,
                        audit=artifact(audit_raw, "COMPLETE-AUDIT"),
                        generation_boundary=record_ref(boundary), inventory_refs=self.inventory_refs,
                        positions=[{"position": i, "value_hex": v}
                                   for i, v in enumerate(accepted, 1)],
                        preceding_chain_tip=preceding_chain_tip)
            payload = make_record("SeedPayload", body)
            durable_bytes(self.root / "payload.json", canonical_bytes(payload) + b"\n")
            return payload
        return self.authority.protected("payload_seal", expected_tip=expected_tip,
                                        operation_id=self.operation_id, action=action)

    def generation_receipt(self, *, expected_tip: str) -> dict:
        def action(_: Lease) -> dict:
            payload_raw = (self.root / "payload.json").read_bytes()
            salt_raw = (self.root / "salt.bin").read_bytes()
            audit_raw = (self.root / "audit.json").read_bytes()
            entries, accepted, _ = self.read_audit()
            if len(accepted) != N or len(salt_raw) != 32:
                raise IntegrityError("cannot receipt incomplete generation")
            body = self._common("S", "RECORDED", self.authority.bindings)
            body.update(accepted_count=N, audit=artifact(audit_raw, "COMPLETE-AUDIT"),
                        audit_counts={"raw": len(entries), "accepted": N,
                                      "K_rejected": sum(e["disposition"] == "REJECT_K" for e in entries),
                                      "duplicate_rejected": sum(e["disposition"] == "REJECT_DUPLICATE" for e in entries)},
                        authority_tip_at_completion=expected_tip,
                        generation_boundary=record_ref(self._boundary()),
                        operation_id=self.operation_id, payload=artifact(payload_raw, "COMPLETE-PAYLOAD"),
                        salt=artifact(salt_raw, "COMPLETE-SALT"))
            record = make_record("S", body)
            durable_bytes(self.root / "receipt.json", canonical_bytes(record) + b"\n")
            for field, raw in (("payload", payload_raw), ("salt", salt_raw), ("audit", audit_raw)):
                self.authority.retain_artifact(raw, body[field]["evidence_id"])
            self.authority.retain_artifact(self.original_K_raw, self.inventory_refs["K"]["evidence_id"])
            self.authority.retain_record(self._boundary())
            self.authority.retain_record(record)
            return record
        return self.authority.protected("payload_seal", expected_tip=expected_tip,
                                        operation_id=self.operation_id, action=action)
