"""Synthetic complete private finite-set reproduction, not inventory adoption."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from tools.research.v6.e9.v2.inventory import verify_known_inventory


def encode(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"),
                      allow_nan=False).encode() + b"\n"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


REPOSITORY = Path(__file__).resolve().parents[2]


def revealed(kind):
    """The complete public revealed lists, read independently of the instrument."""
    if kind == "E6":
        lines = (REPOSITORY / "tools/research/v6/e6/seeds_revealed.txt").read_text(encoding="ascii").splitlines()
        return [f"{int(line):016x}" for line in lines]
    reveal = json.loads((REPOSITORY / "tools/research/v6/e8/seed_reveal.json").read_bytes())
    return [f"{seed:016x}" for seed in reveal["seeds"]]


def independent_inventory_fixture(**values):
    contract_path = REPOSITORY / "tools/research/v6/e9/amended_rule_contract_v2_proposed_02.json"
    contract = json.loads(contract_path.read_bytes())
    K, E, sources = [], [], {}
    for ordinal, kind in enumerate(("E6", "E8", "KNOWN", "CONSERVATIVE"), 1):
        kind_values = values.get(kind, revealed(kind) if kind in ("E6", "E8") else [f"{ordinal:016x}"])
        source_id, receipt_id = f"independent-source-{ordinal}", f"independent-receipt-{ordinal}"
        source = encode({"values": kind_values})
        receipt = encode({"actual_execution": kind != "CONSERVATIVE", "scope_verified": True,
                          "preboundary_verified": True, "source_sha256_raw": sha(source)})
        sources[source_id], sources[receipt_id] = source, receipt
        K.extend(kind_values)
        E.append({"evidence_id": source_id, "sha256_raw": sha(source), "kind": kind,
                  "recipe": "explicit", "values": kind_values, "scope_verified": True,
                  "preboundary_verified": True, "execution_receipt": {
                      "evidence_id": receipt_id, "sha256_raw": sha(receipt),
                      "bytes": len(receipt), "visibility": "PRIVATE"}})
    L = {"gap_ids": contract["preserved_gap_ids"], "dependency_ids": contract["preserved_dependency_ids"]}
    return K, E, L, sources


def check(K, E, L, sources):
    return verify_known_inventory(encode(K), encode(E), encode(L), sources=sources,
                                  inspection_boundary="independent opaque synthetic-only scope")


def test_finite_known_verification_pass_never_establishes_completeness():
    K, E, L, sources = independent_inventory_fixture()
    result = check(K, E, L, sources)
    assert result["known_inventory_verification"] == "PASS"
    assert result["historical_completeness"] == "NOT ESTABLISHED"
    assert result["exhaustive_historical_non_reuse"] == "NOT ESTABLISHED"
    assert len(result["unresolved_gap_ids"]) == 357
    assert result["unresolved_dependency_ids"] == [f"DEP-{i:02}" for i in range(1, 6)]


@pytest.mark.parametrize("fault", ["missing_K", "extra_K", "wrong_K", "duplicate_K", "missing_E6",
                                  "missing_E8", "missing_source", "extra_source", "changed_source",
                                  "missing_receipt", "unknown_recipe", "wrong_derivation", "scope",
                                  "temporal", "gap", "dependency", "duplicate_source", "bool_value"])
def test_exact_private_membership_provenance_and_preserved_ids_fail_closed(fault):
    K, E, L, sources = independent_inventory_fixture()
    if fault == "missing_K":
        K.pop()
    elif fault == "extra_K":
        K.append("ffffffffffffffff")
    elif fault == "wrong_K":
        K[0] = "ffffffffffffffff"
    elif fault == "duplicate_K":
        K.append(K[0])
    elif fault == "missing_E6":
        E.pop(0)
    elif fault == "missing_E8":
        E.pop(1)
    elif fault == "missing_source":
        sources.pop(E[0]["evidence_id"])
    elif fault == "extra_source":
        sources["extra-synthetic-source"] = encode({"values": []})
    elif fault == "changed_source":
        sources[E[0]["evidence_id"]] += b"\n"
    elif fault == "missing_receipt":
        E[0]["execution_receipt"] = None
    elif fault == "unknown_recipe":
        E[0]["recipe"] = "unsupported"
    elif fault == "wrong_derivation":
        E[0]["values"] = ["ffffffffffffffff"]
    elif fault == "scope":
        E[0]["scope_verified"] = False
    elif fault == "temporal":
        E[0]["preboundary_verified"] = False
    elif fault == "gap":
        L["gap_ids"].pop()
    elif fault == "dependency":
        L["dependency_ids"].pop()
    elif fault == "duplicate_source":
        E.append(E[0])
    else:
        K[0] = True
    with pytest.raises(ValueError):
        check(K, E, L, sources)


def test_exact_evidence_changes_with_same_K_produce_new_raw_operational_binding():
    K, E, L, sources = independent_inventory_fixture()
    original = check(K, E, L, sources)
    E.reverse()
    changed = check(K, E, L, sources)
    assert original["input_raw_digests"]["K"] == changed["input_raw_digests"]["K"]
    assert original["input_raw_digests"]["E"] != changed["input_raw_digests"]["E"]


@pytest.mark.parametrize("values", [
    {"E6": revealed("E6")[:-1]},  # truncated E6 list
    {"E8": revealed("E8")[1:]},  # truncated E8 list
    {"E6": [*revealed("E6"), "00000000000000ff"]},  # extra value labelled E6
    {"E6": [], "KNOWN": ["0000000000000003", *revealed("E6")]},  # E6 values relabelled as known use
    {"E8": revealed("E6"), "E6": revealed("E8")},  # lists swapped
])
def test_complete_e6_e8_inclusion_is_exact_even_when_K_equals_the_source_union(values):
    K, E, L, sources = independent_inventory_fixture(**values)
    assert set(K) == {value for item in E for value in item["values"]}  # only completeness differs
    with pytest.raises(ValueError, match="complete revealed lists"):
        check(K, E, L, sources)


def test_complete_inventory_contains_both_pinned_revealed_lists():
    K, E, L, sources = independent_inventory_fixture()
    result = check(K, E, L, sources)
    assert result["E6_membership"] == result["E8_membership"] == "PASS"
    assert set(revealed("E6")) | set(revealed("E8")) <= set(K) and len(revealed("E6")) == len(revealed("E8")) == 32
