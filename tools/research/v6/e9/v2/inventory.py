"""Independent finite known-set verification, never historical completeness.

This reader accepts explicit values or reproducible arithmetic source receipts.
Every source is supplied as exact private bytes. Neither hashes, source defaults
nor the number of exclusions establish historical execution.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .records import IntegrityError, canonical_bytes, sha256, validate_artifact_ref

HEX64 = re.compile(r"[0-9a-f]{16}\Z")
CONTRACT = Path(__file__).parents[1] / "amended_rule_contract_v2_proposed_02.json"
REPOSITORY = Path(__file__).resolve().parents[5]
# The complete public E6/E8 revealed lists, pinned as in
# v2_inherited_preservation_manifest_01.json; drift fails closed.
REVEALED_LISTS = {
    "E6": ("tools/research/v6/e6/seeds_revealed.txt",
           "61e292f6f9dcd951ccc6d8eaf5dc77a41c04c6c4865246ca3b5e5bac5c0e1c83"),
    "E8": ("tools/research/v6/e8/seed_reveal.json",
           "2023484ead61a6cf5f3b2c06dbddf641bb6373153b8479544f238f5b6f97c495"),
}


def strict_private_json(raw: bytes) -> Any:
    def pairs(items: list[tuple[str, Any]]) -> dict:
        result = {}
        for key, value in items:
            if key in result:
                raise IntegrityError("duplicate private key")
            result[key] = value
        return result
    try:
        value = json.loads(raw, object_pairs_hook=pairs,
                           parse_constant=lambda _: (_ for _ in ()).throw(
                               IntegrityError("nonfinite private value")))
    except (ValueError, UnicodeError) as exc:
        raise IntegrityError("malformed private JSON") from exc
    if raw != canonical_bytes(value) + b"\n":
        raise IntegrityError("private JSON must be canonical with one LF")
    return value


def values_checked(values: Any) -> list[str]:
    if not isinstance(values, list) or any(
        not isinstance(v, str) or HEX64.fullmatch(v) is None for v in values
    ):
        raise IntegrityError("strict uint64 hex list required")
    if len(values) != len(set(values)):
        raise IntegrityError("duplicate private inventory value")
    return list(values)


def artifact(raw: bytes, evidence_id: str, visibility: str = "PRIVATE") -> dict:
    ref = {"evidence_id": evidence_id, "sha256_raw": sha256(raw),
           "bytes": len(raw), "visibility": visibility}
    validate_artifact_ref(ref)
    return ref


def frozen_limitations() -> tuple[list[str], list[str]]:
    contract = json.loads(CONTRACT.read_bytes())
    return contract["preserved_gap_ids"], contract["preserved_dependency_ids"]


def revealed_lists() -> dict[str, set[str]]:
    """Read back both complete pinned revealed lists as uint64 hex values."""
    lists = {}
    for kind, (relative, pin) in REVEALED_LISTS.items():
        raw = (REPOSITORY / relative).read_bytes()
        if sha256(raw) != pin:
            raise IntegrityError("pinned revealed list drift")
        if kind == "E6":
            lines = raw.decode("ascii").split("\n")
            if lines[-1] != "":
                raise IntegrityError("revealed list must end with one LF")
            seeds: Any = lines[:-1]
            if any(not line.isdigit() or line != str(int(line)) for line in seeds):
                raise IntegrityError("revealed list must be canonical decimal lines")
            seeds = [int(line) for line in seeds]
        else:
            reveal = json.loads(raw)
            seeds = reveal["seeds"]
            if reveal["seed_count"] != len(seeds):
                raise IntegrityError("revealed list count mismatch")
        if len(seeds) != 32 or any(type(n) is not int or not 0 <= n < 2**64 for n in seeds):
            raise IntegrityError("revealed list must hold 32 uint64 seeds")
        lists[kind] = set(values_checked([f"{n:016x}" for n in seeds]))
    return lists


def verify_known_inventory(K_raw: bytes, E_raw: bytes, L_raw: bytes, *,
                           sources: dict[str, bytes], inspection_boundary: str) -> dict:
    K = values_checked(strict_private_json(K_raw))
    evidence, ledger = strict_private_json(E_raw), strict_private_json(L_raw)
    gaps, dependencies = frozen_limitations()
    if (not isinstance(ledger, dict) or set(ledger) != {"gap_ids", "dependency_ids"}
            or ledger["gap_ids"] != gaps or ledger["dependency_ids"] != dependencies):
        raise IntegrityError("preserved gap/dependency IDs changed or omitted")
    if not isinstance(inspection_boundary, str) or not inspection_boundary.strip():
        raise IntegrityError("inspection boundary absent")
    if not isinstance(evidence, list) or not evidence:
        raise IntegrityError("complete known-source index absent")
    expected_fields = {"evidence_id", "sha256_raw", "kind", "recipe", "values",
                       "execution_receipt", "scope_verified", "preboundary_verified"}
    ids: set[str] = set()
    union: set[str] = set()
    kind_counts = {"E6": 0, "E8": 0, "KNOWN": 0, "CONSERVATIVE": 0}
    kind_values: dict[str, set[str]] = {kind: set() for kind in kind_counts}
    for item in evidence:
        if not isinstance(item, dict) or set(item) != expected_fields:
            raise IntegrityError("unknown/missing inventory source fields")
        evidence_id = item["evidence_id"]
        if not isinstance(evidence_id, str) or not evidence_id or evidence_id in ids:
            raise IntegrityError("duplicate/missing evidence ID")
        ids.add(evidence_id)
        raw = sources.get(evidence_id)
        if not isinstance(raw, bytes) or sha256(raw) != item["sha256_raw"]:
            raise IntegrityError("missing or changed exact known source")
        source = strict_private_json(raw)
        recipe = item["recipe"]
        if recipe == "explicit":
            if not isinstance(source, dict) or set(source) != {"values"}:
                raise IntegrityError("invalid explicit-value source")
            reproduced = values_checked(source["values"])
        elif recipe == "arithmetic":
            if (not isinstance(source, dict) or set(source) != {"start", "step", "count"}
                    or any(type(source[k]) is not int for k in source)
                    or source["count"] < 0):
                raise IntegrityError("invalid arithmetic source")
            numbers = [source["start"] + i * source["step"] for i in range(source["count"])]
            if any(n < 0 or n >= 2**64 for n in numbers):
                raise IntegrityError("derived source outside uint64")
            reproduced = values_checked([f"{n:016x}" for n in numbers])
        else:
            raise IntegrityError("unsupported/unreproduced source derivation")
        if reproduced != values_checked(item["values"]):
            raise IntegrityError("known-source derivation mismatch")
        kind = item["kind"]
        if kind not in kind_counts:
            raise IntegrityError("unknown source role")
        kind_counts[kind] += 1
        kind_values[kind].update(reproduced)
        receipt = item["execution_receipt"]
        if receipt is None:
            raise IntegrityError("execution or conservative-provenance receipt absent")
        validate_artifact_ref(receipt)
        receipt_raw = sources.get(receipt["evidence_id"])
        if (not isinstance(receipt_raw, bytes) or len(receipt_raw) != receipt["bytes"]
                or sha256(receipt_raw) != receipt["sha256_raw"]):
            raise IntegrityError("unread exact execution/provenance evidence")
        ids.add(receipt["evidence_id"])
        proof = strict_private_json(receipt_raw)
        if not isinstance(proof, dict) or set(proof) != {
            "actual_execution", "scope_verified", "preboundary_verified", "source_sha256_raw"
        }:
            raise IntegrityError("unreproduced receipt checklist")
        if (proof["source_sha256_raw"] != item["sha256_raw"]
                or type(item["scope_verified"]) is not bool
                or type(item["preboundary_verified"]) is not bool
                or item["scope_verified"] is not True
                or item["preboundary_verified"] is not True
                or proof["scope_verified"] is not True
                or proof["preboundary_verified"] is not True
                or proof["actual_execution"] is not (kind != "CONSERVATIVE")):
            raise IntegrityError("actual-use/scope/temporal/provenance proof fails")
        union.update(reproduced)
    if ids != set(sources):
        raise IntegrityError("missing/extra private input manifest member")
    if set(K) != union:
        raise IntegrityError("missing/extra/wrong K membership")
    # Complete inclusion: each labelled source union is exactly its pinned list.
    for kind, complete in revealed_lists().items():
        if kind_values[kind] != complete:
            raise IntegrityError("E6/E8 sources are not exactly the complete revealed lists")
    return {"known_inventory_verification": "PASS", "E6_membership": "PASS",
            "E8_membership": "PASS", "historical_completeness": "NOT ESTABLISHED",
            "exhaustive_historical_non_reuse": "NOT ESTABLISHED",
            "inspection_boundary": inspection_boundary, "unresolved_gap_ids": gaps,
            "unresolved_dependency_ids": dependencies,
            "input_raw_digests": {"K": sha256(K_raw), "E": sha256(E_raw), "L": sha256(L_raw)},
            "K_count": len(K), "source_counts": kind_counts}
