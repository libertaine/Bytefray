"""Read-only historical evidence census; no engine or research execution imports.

All output paths and decoded values are private evidence. A current observation
never establishes an original count-only identity or historical completeness.
"""

from __future__ import annotations

import hashlib
import json
import os
from collections import Counter
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from itertools import islice
from pathlib import Path
from typing import Any

HEADER_LIMIT = 1_048_576


def selected(name: str) -> bool:
    return name in {"result.json", "summary.json"} or (
        name.endswith(".jsonl") and ("replay" in name or "trace" in name)
    )


def exception_record(exc: OSError) -> dict[str, Any]:
    return {"type": type(exc).__name__, "errno": exc.errno,
            "winerror": getattr(exc, "winerror", None), "message": str(exc)}


def seed_fields(value: Any) -> list[dict[str, Any]]:
    """Report the original collector's shallow match-configuration candidates."""
    if not isinstance(value, dict):
        return []
    blocks = [("", value)]
    blocks.extend(("/" + key, value[key]) for key in (
        "config", "reproducibility", "effective_config", "header"
    ) if isinstance(value.get(key), dict))
    fields = []
    for prefix, block in blocks:
        for key in ("seed", "match_seed"):
            if key not in block:
                continue
            number = block[key]
            valid = type(number) is int and 0 <= number < 2**64
            fields.append({"json_pointer": prefix + "/" + key,
                           "valid_uint64": valid,
                           "value_hex": f"{number:016x}" if valid else None,
                           "invalid_type": None if valid else type(number).__name__,
                           "role": "MATCH_CONFIGURATION_CANDIDATE" if valid else "INVALID_FIELD",
                           "execution_origin": "UNRESOLVED"})
    return fields


def inspect_file(path: Path) -> dict[str, Any]:
    """Stream a full-file digest; parse only metadata, without replay analysis."""
    row: dict[str, Any] = {"path": str(path), "path_ref": "PATH-" + hashlib.sha256(
        str(path).encode()).hexdigest()[:16], "read_status": "UNREADABLE",
        "parse_status": "NOT_ATTEMPTED", "sha256_whole_file_raw": None,
        "sha256_metadata_raw": None, "seed_fields": [],
        "historical_attribution": "UNRESOLVED"}
    total = 0
    whole = hashlib.sha256()
    try:
        before = path.stat()
        with path.open("rb") as stream:
            if path.suffix == ".jsonl":
                metadata = stream.readline(HEADER_LIMIT + 1)
                whole.update(metadata)
                total += len(metadata)
                while chunk := stream.read(1_048_576):
                    whole.update(chunk)
                    total += len(chunk)
                scope = "first_line"
            else:
                metadata = stream.read()
                whole.update(metadata)
                total = len(metadata)
                scope = "whole_file"
        after = path.stat()
        row.update(read_status="READ", byte_count=total,
                   sha256_whole_file_raw=whole.hexdigest(),
                   sha256_metadata_raw=hashlib.sha256(metadata).hexdigest(),
                   metadata_hash_scope=scope, size_before=before.st_size,
                   mtime_ns_before=before.st_mtime_ns, size_after=after.st_size,
                   mtime_ns_after=after.st_mtime_ns,
                   stable_during_read=(before.st_size == after.st_size == total
                                       and before.st_mtime_ns == after.st_mtime_ns))
        if scope == "first_line" and len(metadata) > HEADER_LIMIT:
            row.update(parse_status="HEADER_LIMIT_EXCEEDED",
                       metadata_hash_scope="first_line_prefix")
            return row
        try:
            value = json.loads(metadata)
        except (ValueError, UnicodeError) as exc:
            row.update(parse_status="MALFORMED", parse_exception=type(exc).__name__)
            return row
        row["parse_status"] = "PARSED_OBJECT" if isinstance(value, dict) else "PARSED_NONOBJECT"
        if isinstance(value, dict):
            row["schema_evidence"] = {key: value.get(key) for key in (
                "schema", "schema_version", "record_type", "ver", "runtime_kind", "ruleset_id"
            ) if isinstance(value.get(key), (str, int, bool, type(None)))}
            row["explicit_synthetic_marker"] = value.get("synthetic") is True
            row["seed_fields"] = seed_fields(value)
            row["remaining_question"] = "schema/seed fields do not establish an executed match"
        return row
    except OSError as exc:
        row["read_exception"] = exception_record(exc)
        row["bytes_read_before_error"] = total
        row["remaining_question"] = "recover authoritative readable bytes and historical origin"
        return row


def walk_selected(roots: list[Path], excluded: Path, failures: list[dict[str, Any]],
                  auxiliary: list[str]) -> Iterator[Path]:
    """Preserve every onerror path; do not follow directory symlinks."""
    def onerror(exc: OSError) -> None:
        failures.append({"path": exc.filename, "exception": exception_record(exc),
                         "observation_scope": "CURRENT_TRAVERSAL_ONLY",
                         "original_directory_gap_id": None})

    for parent in roots:
        for directory, dirs, files in os.walk(parent, onerror=onerror, followlinks=False):
            if Path(directory) == excluded:
                dirs[:] = []
                continue
            dirs[:] = sorted(d for d in dirs if d not in {"__pycache__", "agents", ".git"})
            for name in sorted(files):
                path = Path(directory) / name
                if name.endswith((".xml", ".log")) or (
                    name.endswith(".json") and any(s in name for s in (
                        "qualification", "manifest", "seed", "prereg", "matrix", "freeze"
                    ))
                ):
                    auxiliary.append(str(path))
                if selected(name):
                    yield path


def collect(roots: list[Path], excluded: Path, output: Path,
            original: dict[str, Any], captures: dict[str, str],
            candidate: set[str], *, workers: int = 16) -> dict[str, Any]:
    """One additive pass, with private path/hash/status records for every file."""
    output.mkdir(parents=True, exist_ok=True)
    inventory = output / "selected_files.jsonl"
    retained = {s["path"]: s for s in original["retained_metadata"]}
    unreadable = {s["path"] for s in original["unreadable_records"]}
    original_paths = set(retained) | unreadable
    counts: Counter[str] = Counter()
    membership: Counter[str] = Counter()
    new_values: set[str] = set()
    directory_failures: list[dict[str, Any]] = []
    auxiliary: list[str] = []
    paths = iter(walk_selected(roots, excluded, directory_failures, auxiliary))
    with inventory.open("xb") as handle, ThreadPoolExecutor(max_workers=workers) as pool:
        while batch := list(islice(paths, 512)):
            for row in pool.map(inspect_file, batch):
                path = row["path"]
                original_paths.discard(path)
                if path in retained:
                    prior = retained[path]
                    expected = row.get("sha256_metadata_raw")
                    same = expected == prior["sha256_raw"] and row.get("metadata_hash_scope") == prior["hash_scope"]
                    row["original_reconciliation"] = {"kind": "RETAINED_DECODED_PATH", "raw_binding_matches": same,
                        "decoded_membership_matches": set(prior["match_seeds_hex"]) == {
                            f["value_hex"] for f in row["seed_fields"] if f["valid_uint64"]}}
                    counts["original_retained_binding_matches" if same else "original_retained_binding_mismatch"] += 1
                elif path in unreadable:
                    row["original_reconciliation"] = {"kind": "ORIGINAL_UNREADABLE_PATH",
                        "first_handoff_capture_matches": row.get("sha256_whole_file_raw") == captures.get(path)}
                    counts["original_unreadable_paths_observed"] += 1
                else:
                    row["original_reconciliation"] = {"kind": "NOT_IDENTIFIABLE_FROM_ORIGINAL_PATH_LEDGER",
                        "original_no_seed_identity": None}
                    counts["current_paths_outside_original_recorded_paths"] += 1
                valid = {f["value_hex"] for f in row["seed_fields"] if f["valid_uint64"]}
                for field in row["seed_fields"]:
                    field["candidate_inclusion"] = field["value_hex"] in candidate if field["valid_uint64"] else None
                for value in valid:
                    membership["included" if value in candidate else "not_included"] += 1
                    if value not in candidate:
                        new_values.add(value)
                counts["records_examined"] += 1
                counts["full_file_bytes_hashed"] += row.get("byte_count", 0)
                counts["parse_" + row["parse_status"]] += 1
                counts["records_with_decoded_seed" if valid else "records_without_decoded_seed"] += 1
                counts["read_" + row["read_status"]] += 1
                if row.get("stable_during_read") is False:
                    counts["unstable_files"] += 1
                handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")).encode() + b"\n")
            if counts["records_examined"] % 32768 == 0:
                print("Current census records:", counts["records_examined"], flush=True)
    result = {"schema": "bytefray.v6.e9.current_historical_inventory", "version": 1,
        "counts": dict(counts), "candidate_membership": dict(membership),
        "new_decoded_candidate_values_hex": sorted(new_values),
        "current_directory_failures": directory_failures,
        "original_recorded_paths_not_observed": sorted(original_paths),
        "original_directory_identity_recovery": "NOT ESTABLISHED",
        "original_no_seed_identity_recovery": "NOT ESTABLISHED",
        "original_counts": original["retained_metadata_counts"],
        "inventory_sha256_raw": hash_file(inventory), "inventory_bytes": inventory.stat().st_size,
        "roots": [str(p) for p in roots], "excluded_root": str(excluded),
        "coverage": "NOT COMPLETE", "seed_generation": False, "payoff_execution": False}
    with (output / "inventory_summary.json").open("x", encoding="utf-8") as handle:
        json.dump(result, handle, sort_keys=True, indent=2)
        handle.write("\n")
    with (output / "auxiliary_paths.json").open("x", encoding="utf-8") as handle:
        json.dump(auxiliary, handle)
        handle.write("\n")
    return result


def hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1_048_576):
            digest.update(chunk)
    return digest.hexdigest()
