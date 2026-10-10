"""Non-operational fixtures: these actors and approvals authorize only test doubles."""
from __future__ import annotations

from typing import Any

from tools.research.v6.e9.v2.records import (
    ADOPTED,
    BASE,
    catalogue,
    make_record,
    read_record,
    record_ref,
    sha256,
    strict_json,
)

STUDY = "synthetic-e9-v2-only"


def artifact(label: str = "fixture", *, private: bool = False, size: int = 0) -> dict:
    return {"evidence_id": "synthetic/" + label, "sha256_raw": sha256(label.encode()),
            "bytes": size, "visibility": "PRIVATE" if private else "PUBLIC"}


def actor(role: str = "research_lead", identity: str = "synthetic-lead") -> dict:
    return {"actor_id": identity, "role": role, "authority_evidence": artifact(identity)}


def inventory_status() -> dict:
    c = strict_json((BASE / "amended_rule_contract_v2_proposed_02.json").read_bytes())
    return {"known_inventory_verification": "PASS", "E6_membership": "PASS", "E8_membership": "PASS",
            "historical_completeness": "NOT ESTABLISHED", "exhaustive_historical_non_reuse": "NOT ESTABLISHED",
            "inspection_boundary": {"scope": "synthetic-only", "evidence": artifact()},
            "unresolved_gap_ids": c["preserved_gap_ids"],
            "unresolved_dependency_ids": c["preserved_dependency_ids"]}


def fixture(role: str, earlier: dict[str, dict], **overrides: Any) -> dict:
    spec = catalogue()["records"][role]
    if role == "P":
        return read_record(ADOPTED, "P")
    if role == "I":
        return make_record("I", {"digest_recipe": spec["required_body_fields"]["digest_recipe"],
                                  "implementation_sources": {"synthetic_source.py": sha256(b"fixture")},
                                  "dependencies": {"P": record_ref(earlier["P"])}})
    body: dict[str, Any] = {}
    for name, desc in spec["required_body_fields"].items():
        if name in overrides:
            body[name] = overrides[name]
            continue
        if "ArtifactRef list" in desc:
            body[name] = [artifact(name, private="PRIVATE" in desc)]
        elif "ArtifactRef" in desc and "inventory_refs" != name:
            body[name] = artifact(name, private="PRIVATE" in desc, size=32 if name == "salt" else 0)
        elif desc in ("sha256", "sha256 c"):
            body[name] = "0" * 64
        elif desc.startswith("sha256 or"):
            body[name] = "genesis"
        elif desc == "1412":
            body[name] = 1412
        elif name in ("producer_fence_epoch", "scientific_priority_row", "last_acceptance_ordinal"):
            body[name] = 1 if name == "scientific_priority_row" else (None if name == "last_acceptance_ordinal" else 0)
        elif name == "stage":
            body[name] = "BEFORE_GENERATION"
        elif name == "event_kind":
            body[name] = "ISSUE"
        elif desc == "CONTINUE or RELEASE":
            body[name] = "CONTINUE"
        elif name == "historical_integrity":
            body[name] = "INTACT"
        elif name == "F_D_S_H_statuses":
            body[name] = dict.fromkeys(("F", "D", "S", "H"), "NOT EVALUABLE")
        elif name == "scientific_classification":
            body[name] = "NOT EVALUABLE"
        elif desc.startswith("integer >="):
            body[name] = int(desc.split()[-1])
        elif desc.startswith("integer 0.."):
            body[name] = 0
        elif desc == "explicit true" or "explicit" in desc and "boolean" in desc:
            body[name] = True
        elif desc == "InventoryStatus":
            body[name] = inventory_status()
        elif desc == "C-LIMITED":
            body[name] = "C-LIMITED"
        elif desc == "NOT ESTABLISHED":
            body[name] = "NOT ESTABLISHED"
        elif name == "permanent_limitation":
            c = strict_json((BASE / "amended_rule_contract_v2_proposed_02.json").read_bytes())
            body[name] = c["exact_interpretation"]["permanent_limitation_text"]
        elif name == "risk":
            body[name] = "H UNKNOWN; no useful numeric bound; only worst-case bound 1"
        elif name in ("accepted_limitation", "approved_scope"):
            status = inventory_status()
            body[name] = {"assurance": "known-history non-reuse only",
                          "historical_coverage": "NOT ESTABLISHED",
                          "unknown_history_risk": "H UNKNOWN; no useful numeric bound; only worst-case bound 1",
                          "unresolved_gap_ids": status["unresolved_gap_ids"],
                          "unresolved_dependency_ids": status["unresolved_dependency_ids"],
                          "inspection_boundary": "synthetic-only-exact-private-fixture"}
        elif name == "custodian_attestation":
            body[name] = {"actor": actor("custodian", "synthetic-custodian"),
                          "inspection_boundary": artifact("synthetic-custodian-boundary"),
                          "T_disposition": t_not_applicable()}
        elif name in ("affected_authorizations", "supplement_chain", "unreproduced_items"):
            body[name] = []
        elif name in ("binding_tuple", "original_records", "unchanged_original_tuple"):
            body[name] = {r: record_ref(v) for r, v in earlier.items()}
        elif name == "generation_boundary":
            body[name] = record_ref(earlier["GenerationBoundary"])
        elif desc == "AuthorityEvent":
            body[name] = record_ref(earlier["AuthorityEvent"])
        else:
            body[name] = "synthetic-only"
    declared = spec.get("record_reference_dependencies", spec["dependencies"])
    deps = {r: record_ref(earlier[r]) for r in declared if r in earlier}
    if role in ("S", "SeedPayload"):
        deps.pop("GenerationBoundary", None)
    if role in ("S", "SeedPayload", "GenerationBoundary", "PartialGenerationSupplement", "F"):
        deps.update({r: record_ref(earlier[r]) for r in ("P", "I", "Q", "O", "V", "A", "R", "B", "G")})
    if role == "F":
        deps.update({r: record_ref(earlier[r]) for r in ("S", "W", "U", "C", "D")})
    authority_roles = {"Q": "independent_qualifier", "O": "custodian", "V": "independent_verifier",
                       "B": "independent_verifier", "W": "independent_verifier",
                       "S": "recorder", "SeedPayload": "recorder", "GenerationBoundary": "recorder",
                       "C": "publisher", "F": "recorder", "AuthorityEvent": "research_lead"}
    role_tag = authority_roles.get(role, "research_lead")
    body.update({"record_role": role, "study_id": STUDY, "actor": actor(role_tag, "synthetic-" + role_tag),
                 "decision": "PASS" if role in ("Q", "V", "B", "W") else "AUTHORIZED",
                 "evidence": [], "dependencies": deps})
    body.update(overrides)
    if role == "O" and "custodian_attestation" not in overrides and "T" in body["dependencies"]:
        del body["custodian_attestation"]["T_disposition"]  # a bound T replaces NOT_APPLICABLE
    return make_record(role, body)


def t_not_applicable() -> dict:
    """The lead's explicit synthetic-only NOT_APPLICABLE disposition for T."""
    return {"disposition": "NOT_APPLICABLE", "actor": actor("research_lead", "synthetic-research_lead"),
            "reason": "synthetic fixture: no match-producing qualification was authorized",
            "evidence": artifact("synthetic-T-not-applicable")}


def through_g(*, inventory_refs: dict | None = None) -> dict[str, dict]:
    records: dict[str, dict] = {}
    for role in ("P", "I", "Q", "O", "V", "A", "R", "B", "G"):
        overrides = {"operation_id": "synthetic-operation"} if role == "G" else {}
        if inventory_refs is not None and role in ("O", "A", "R"):
            overrides.update(inventory_refs)
        records[role] = fixture(role, records, **overrides)
    return records
