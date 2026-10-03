"""Bind seed-free packages and audit prior-use evidence without unlocking E9.

The census is a candidate inventory. Retained records and current source
references cannot themselves prove coverage of every prior qualification.
No seeds are drawn, no matches run, and completeness is never inferred.
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import subprocess
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from itertools import islice
from pathlib import Path
from typing import Any

from .instrument import require_qualified
from .protocol import (
    PROTOCOL_DIGEST,
    PROTOCOL_ID,
    ROOT,
    IntegrityError,
    canonical,
    digest,
    file_digest,
    load_protocol,
    read_json,
    verify_package,
    write_once,
)
from .runner import check_private, materialize, private_root

PUBLIC = ROOT / "tools/research/v6/e9/preparation_record.json"


def match_values(value: Any) -> set[int]:
    """Read match configuration/header fields, never agent RNG state."""
    found: set[int] = set()
    if not isinstance(value, dict):
        return found
    candidates = [value.get("seed"), value.get("match_seed")]
    for key in ("config", "reproducibility", "effective_config", "header"):
        item = value.get(key)
        if isinstance(item, dict):
            candidates.extend((item.get("seed"), item.get("match_seed")))
    for item in candidates:
        if type(item) is int and 0 <= item < 2**64:
            found.add(item)
    return found


def historical_lists() -> tuple[set[int], list[dict[str, Any]]]:
    e6_record = read_json(ROOT / "tools/research/v6/e6/final_record.json")
    e6_path = ROOT / e6_record["revealed_list"]["path"]
    raw = e6_path.read_bytes()
    e6 = [int(line) for line in raw.splitlines()]
    if (raw != "".join(f"{s}\n" for s in e6).encode("ascii")
            or digest(raw) != e6_record["seed_commitment"]
            or digest(raw) != e6_record["revealed_list"]["sha256"]
            or len(e6) != 32 or len(set(e6)) != 32):
        raise IntegrityError("E6 reveal evidence failed")
    e8_path = ROOT / "tools/research/v6/e8/seed_reveal.json"
    e8_record = read_json(e8_path)
    e8 = e8_record["seeds"]
    raw8 = "".join(f"{s}\n" for s in e8).encode("ascii")
    if (len(e6) != 32 or len(e8) != 32 or len(set(e8)) != 32
            or any(type(s) is not int or not 0 <= s < 2**53 for s in (*e6, *e8))
            or digest(raw8) != e8_record["seed_commitment"]
            or not e8_record["seed_reveal"]
            or not all(e6_record["d6"]["content"]["checks"].values())):
        raise IntegrityError("historical seed count/domain/commitment failed")
    sources = [{"path": str(path.resolve()), "sha256_raw": file_digest(path),
                "kind": kind} for path, kind in (
        (e6_path, "E6 revealed match list"),
        (ROOT / "tools/research/v6/e6/final_record.json", "E6 reveal verification"),
        (e8_path, "E8 revealed match list and verification"))]
    return set(e6) | set(e8), sources


def source_census() -> tuple[set[int], dict[str, Any], list[dict[str, Any]]]:
    paths = subprocess.check_output(["git", "ls-files"], cwd=ROOT, text=True).splitlines()
    found: set[int] = set()
    sites, sources = [], []
    counts: Counter[str] = Counter()
    for name in paths:
        if not name.endswith(".py") or not ("test" in name or name.startswith("tools/research/")):
            continue
        path = ROOT / name
        tree = ast.parse(path.read_text(encoding="utf-8-sig"))
        local = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                for keyword in node.keywords:
                    if keyword.arg not in {"seed", "match_seed"}:
                        continue
                    expression = keyword.value
                    literal = (isinstance(expression, ast.Constant)
                               and type(expression.value) is int and 0 <= expression.value < 2**64)
                    if literal:
                        found.add(expression.value)
                    counts["literal_sites" if literal else "nonliteral_sites"] += 1
                    local.append({"line": node.lineno, "callee": ast.unparse(node.func),
                                  "argument": keyword.arg, "expression": ast.unparse(expression),
                                  "literal_candidate": literal})
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                args = [*node.args.posonlyargs, *node.args.args]
                defaults = list(zip(args[-len(node.args.defaults):], node.args.defaults)) if node.args.defaults else []
                defaults.extend(zip(node.args.kwonlyargs, node.args.kw_defaults))
                for arg, default in defaults:
                    if (arg.arg in {"seed", "match_seed"} and isinstance(default, ast.Constant)
                            and type(default.value) is int and 0 <= default.value < 2**64):
                        found.add(default.value)
                        counts["literal_harness_defaults"] += 1
        if local:
            sources.append({"path": str(path.resolve()), "sha256_raw": file_digest(path),
                            "kind": "current seed-argument source"})
            sites.append({"source": name, "sites": local})
    return found, {"counts": dict(counts), "sites": sites,
                   "limits": ["nonliteral sites require call-chain and derived-value coverage",
                              "current source does not establish coverage of removed historical sources",
                              "literal candidates are not assertions that a match executed"]}, sources


def metadata(path: Path) -> tuple[set[int], dict[str, Any] | None, dict[str, str] | None]:
    is_header = path.suffix == ".jsonl"
    try:
        if is_header:
            with path.open("rb") as handle:
                raw = handle.readline(1_048_577)
            if len(raw) > 1_048_576:
                raise IntegrityError("oversized metadata header")
        else:
            raw = path.read_bytes()
        value = json.loads(raw)
        values = match_values(value)
        if not values:
            return set(), None, None
        # Bind precisely the read header for large replay/trace files.
        # It is seed evidence; no trajectory/payoff analysis occurs.
        return values, {"path": str(path), "sha256_raw": digest(raw),
                        "hash_scope": "first_line" if is_header else "whole_file",
                        "kind": "retained match metadata",
                        "match_seeds_hex": [f"{s:016x}" for s in sorted(values)]}, None
    except (OSError, ValueError, TypeError):
        return set(), None, {"path": str(path), "reason": "unreadable match metadata"}


def artifact_census(root: Path) -> tuple[set[int], list[dict[str, Any]], dict[str, int], list[dict[str, str]]]:
    found: set[int] = set()
    sources, failures = [], []
    counts: Counter[str] = Counter()
    roots = [ROOT / "runs", ROOT / ".pytest-tmp", ROOT / "engine/tests/fixtures",
             ROOT / "client/tests/fixtures"]

    def paths():
        for parent in roots:
            if not parent.exists():
                continue
            for directory, dirs, files in os.walk(parent, onerror=lambda _: counts.update({"inaccessible_directories": 1})):
                if Path(directory) == root:
                    dirs[:] = []
                    continue
                dirs[:] = sorted(d for d in dirs if d not in {"__pycache__", "agents", ".git"})
                for name in sorted(files):
                    is_header = name.endswith(".jsonl") and ("replay" in name or "trace" in name)
                    if name in {"result.json", "summary.json"} or is_header:
                        yield Path(directory) / name

    iterator = iter(paths())
    with ThreadPoolExecutor(max_workers=16) as pool:
        while batch := list(islice(iterator, 512)):
            for values, source, failure in pool.map(metadata, batch):
                found.update(values)
                counts["records_examined"] += 1
                if source is not None:
                    sources.append(source)
                    counts["records_with_match_seed"] += 1
                elif failure is not None:
                    failures.append(failure)
                    counts["unreadable_metadata_records"] += 1
                else:
                    counts["records_without_match_seed"] += 1
                if counts["records_examined"] % 10000 == 0:
                    print("Audited retained match metadata records:", counts["records_examined"], flush=True)
    return found, sources, dict(counts), failures


def bind() -> dict[str, Any]:
    protocol = load_protocol()
    qualified = require_qualified()
    root = private_root(qualified)
    check_private(root)
    if PUBLIC.exists() or (root / "preparation.json").exists():
        raise IntegrityError("preparation evidence already exists; verify it without overwriting")
    defaults = materialize(root, protocol)
    packages = {}
    for name in defaults:
        verify_package(name, root / "agents" / name, protocol)
        packages[name] = {filename: file_digest(root / "agents" / name / filename)
                          for filename in ("agent.py", "agent.yaml")}
    # This binding has no match seeds, commitment, started attempts or payoff.
    body = {"protocol_id": PROTOCOL_ID, "protocol_digest": PROTOCOL_DIGEST,
            "instrument_digest": qualified, "instrument_commit": subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
            "packages": packages, "resolved_defaults": defaults,
            "effective_t8": protocol["effective_t8"], "logical_aliases": protocol["logical_aliases"],
            "physical_packages": protocol["physical_packages"], "historical_members": protocol["historical_members"]}
    binding = {"schema": "bytefray.v6.e9.evaluation_artifact_binding", "version": 1,
               "body": body, "digest": digest(canonical(body)), "status": "PASS"}
    binding_path = root / "evaluation_artifacts.json"
    if binding_path.exists():
        if binding_path.read_bytes() != canonical(binding) + b"\n":
            raise IntegrityError("retained evaluation artifact binding changed")
    else:
        write_once(binding_path, binding)
    historical, provenance = historical_lists()
    literal, source_audit, source_provenance = source_census()
    retained, metadata, counts, failures = artifact_census(root)
    # Header-only hashes do not satisfy the qualified runner's whole-file
    # provenance contract. Preserve them in the audit, never promote them.
    audit = {"source_census": source_audit, "retained_metadata": metadata,
             "retained_metadata_counts": counts, "unreadable_records": failures}
    audit_sha = write_once(root / "exclusion_audit.json", audit)
    inventory = {"schema": "bytefray.v6.e9.exclusion_inventory", "version": 1,
                 "complete": False,
                 "coverage": {"E6": True, "E8": True, "all_prior_match_qualification": False},
                 "match_seeds_hex": [f"{s:016x}" for s in sorted(historical | literal | retained)],
                 "provenance": provenance + source_provenance + [{"path": str((root / "exclusion_audit.json").resolve()),
                                  "sha256_raw": audit_sha, "kind": "retained metadata and source audit"}],
                 "audit_digest": audit_sha,
                 "status": "CANDIDATE; qualification coverage not established",
                 "seed_generation": False, "payoff_execution": False}
    inventory_sha = write_once(root / "exclusion_inventory.candidate.json", inventory)
    private = {"resolved_private_root": str(root.resolve()), "artifact_binding_digest": binding["digest"],
               "exclusion_candidate_sha256_raw": inventory_sha, "exclusion_audit_sha256_raw": audit_sha,
               "seed_generation": False, "payoff_execution": False}
    write_once(root / "preparation.json", private)
    record = {"schema": "bytefray.v6.e9.preparation", "version": 1,
              "date": "2026-10-02", "protocol_id": PROTOCOL_ID,
              "protocol_digest": PROTOCOL_DIGEST, "instrument_digest": qualified,
              "instrument_commit": body["instrument_commit"], "preparation_source_sha256_raw": file_digest(Path(__file__)),
              "artifact_binding": {"status": "PASS", "digest": binding["digest"], "package_count": len(packages),
                                   "package_file_count": 2 * len(packages), "defaults_count": len(defaults)},
              "exclusion": {"status": "NOT COMPLETE", "candidate_sha256_raw": inventory_sha,
                            "audit_sha256_raw": audit_sha, "coverage": inventory["coverage"],
                            "candidate_count": len(inventory["match_seeds_hex"]),
                            "source_counts": source_audit["counts"], "retained_metadata_counts": counts,
                            "missing_evidence": "complete historical qualification match-seed coverage, including derived selections"},
              "seed_generation": False, "payoff_execution": False, "requirement_C": "NOT ESTABLISHED"}
    write_once(PUBLIC, record)
    return record


def verify() -> dict[str, Any]:
    """Recompute byte bindings and independently check every retained seed source."""
    protocol = load_protocol()
    qualified = require_qualified()
    root = private_root(qualified)
    check_private(root)
    public = read_json(PUBLIC)
    private = read_json(root / "preparation.json")
    binding = read_json(root / "evaluation_artifacts.json")
    body = binding["body"]
    if (digest(canonical(body)) != binding["digest"]
            or binding["digest"] != public["artifact_binding"]["digest"]
            or private["artifact_binding_digest"] != binding["digest"]
            or body["protocol_digest"] != PROTOCOL_DIGEST or body["instrument_digest"] != qualified
            or public["preparation_source_sha256_raw"] != file_digest(Path(__file__))):
        raise IntegrityError("preparation binding/source drift")
    for path, expected in {**read_json(ROOT / "tools/research/v6/e9/instrument_qualification.json")["sources"],
                           **read_json(ROOT / "tools/research/v6/e9/instrument_qualification.json")["qualification_sources"]}.items():
        committed = subprocess.check_output(["git", "show", body["instrument_commit"] + ":" + path], cwd=ROOT)
        if digest(committed) != expected or (ROOT / path).read_bytes() != committed:
            raise IntegrityError("committed instrument/test byte mismatch")
    if materialize(root, protocol) != body["resolved_defaults"]:
        raise IntegrityError("resolved default binding changed")
    for name, files in body["packages"].items():
        verify_package(name, root / "agents" / name, protocol)
        if any(file_digest(root / "agents" / name / filename) != sha for filename, sha in files.items()):
            raise IntegrityError("bound package changed")
    for key in ("effective_t8", "logical_aliases", "physical_packages", "historical_members"):
        if canonical(body[key]) != canonical(protocol[key]):
            raise IntegrityError("bound environment/alias/seat mapping changed")
    candidate_path = root / "exclusion_inventory.candidate.json"
    audit_path = root / "exclusion_audit.json"
    candidate, audit = read_json(candidate_path), read_json(audit_path)
    if (file_digest(candidate_path) != public["exclusion"]["candidate_sha256_raw"]
            or file_digest(audit_path) != public["exclusion"]["audit_sha256_raw"]
            or candidate_path.read_bytes() != canonical(candidate) + b"\n"
            or audit_path.read_bytes() != canonical(audit) + b"\n"
            or candidate["complete"] is not False or candidate["coverage"]["all_prior_match_qualification"] is not False):
        raise IntegrityError("candidate inventory was changed or promoted without coverage evidence")
    entries = candidate["match_seeds_hex"]
    if (len(entries) != len(set(entries)) or entries != sorted(entries)
            or any(len(s) != 16 or any(c not in "0123456789abcdef" for c in s) for s in entries)):
        raise IntegrityError("candidate inventory encoding/uniqueness failed")
    for source in candidate["provenance"]:
        if file_digest(Path(source["path"])) != source["sha256_raw"]:
            raise IntegrityError("exclusion source drift")
    entries_set = set(entries)
    # Independent readers of the two public reveal representations.
    e6_final = read_json(ROOT / "tools/research/v6/e6/final_record.json")
    e6_bytes = (ROOT / e6_final["revealed_list"]["path"]).read_bytes()
    e6_values = [int(line) for line in e6_bytes.decode("ascii").split("\n")[:-1]]
    e8_reveal = read_json(ROOT / "tools/research/v6/e8/seed_reveal.json")
    e8_values = e8_reveal["seeds"]
    if (digest(e6_bytes) != e6_final["seed_commitment"]
            or digest(b"".join((str(n) + "\n").encode("ascii") for n in e8_values)) != e8_reveal["seed_commitment"]
            or len(e6_values) != 32 or len(e8_values) != 32
            or any(f"{s:016x}" not in entries_set for s in (*e6_values, *e8_values))):
        raise IntegrityError("independent E6/E8 exclusion membership failed")
    for source in audit["retained_metadata"]:
        path = Path(source["path"])
        if source["hash_scope"] == "first_line":
            with path.open("rb") as handle:
                raw = handle.readline(1_048_577)
        else:
            raw = path.read_bytes()
        if digest(raw) != source["sha256_raw"] or not set(source["match_seeds_hex"]) <= entries_set:
            raise IntegrityError("retained match evidence drift or omitted exclusion")
    if any((root / name).exists() for name in ("seed_payload.json", "seed_salt.bin", "cells", "execution.json")):
        raise IntegrityError("unauthorized experimental preparation crossed the seed/payoff boundary")
    record = {"schema": "bytefray.v6.e9.preparation_verification", "version": 1,
              "artifact_binding": "PASS", "instrument_commit": body["instrument_commit"],
              "artifact_binding_digest": binding["digest"], "package_count": len(body["packages"]),
              "exclusion_canonical_domain_uniqueness_provenance": "PASS",
              "E6_E8_committed_lists_excluded": "PASS", "retained_match_metadata_reverified": len(audit["retained_metadata"]),
              "all_prior_qualification_coverage": "NOT ESTABLISHED", "seed_generation": False,
              "payoff_execution": False, "requirement_C": "NOT ESTABLISHED"}
    destination = ROOT / "tools/research/v6/e9/preparation_verification.json"
    if destination.exists():
        if destination.read_bytes() != canonical(record) + b"\n":
            raise IntegrityError("previous preparation verification differs")
    else:
        write_once(destination, record)
    return record


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("bind", "verify"))
    args = parser.parse_args()
    try:
        if args.command == "bind":
            record = bind()
            count = record["artifact_binding"]["package_count"]
        else:
            record = verify()
            count = record["package_count"]
        print("PASS: bound", count, "packages; exclusion NOT COMPLETE; generation/execution LOCKED")
    except (IntegrityError, OSError, ValueError, KeyError, TypeError):
        print("Preparation refused: unusable evidence or an existing immutable boundary")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
