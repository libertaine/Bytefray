"""Offline historical scope read-back. Standard library only; never runs matches.

The receipt verifies bytes and recorded seed membership. It cannot supply an
authority declaration, infer exhaustive history, or authorize generation.
Private input paths and values are never included in stdout or error messages.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import zipfile
from pathlib import Path
from typing import Any

HEX = re.compile(r"[0-9a-f]{16}\Z")
SHA = re.compile(r"[0-9a-f]{64}\Z")


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise ValueError(reason)


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8") + b"\n"


def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        require(key not in result, "duplicate JSON key")
        result[key] = value
    return result


def loads(raw: bytes) -> Any:
    return json.loads(raw, object_pairs_hook=unique_object)


def file_sha(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1_048_576), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def values_hex(values: Any) -> set[str]:
    require(isinstance(values, list), "exclusions must be an explicit list")
    require(all(isinstance(v, str) and HEX.fullmatch(v) for v in values), "invalid uint64 encoding")
    require(values == sorted(set(values)), "exclusions are not sorted and unique")
    require(len(values) < 2**64, "whole-domain exclusion is prohibited")
    return set(values)


def candidate_values(raw: bytes) -> set[str]:
    record = loads(raw)
    require(raw == canonical(record), "candidate encoding changed")
    require(record.get("complete") is False, "partial candidate cannot claim completeness")
    require(record.get("coverage") == {"E6": True, "E8": True,
                                      "all_prior_match_qualification": False}, "candidate scope changed")
    return values_hex(record["match_seeds_hex"])


def match_values(record: Any) -> set[str]:
    if not isinstance(record, dict):
        return set()
    blocks = [record] + [record[k] for k in ("config", "reproducibility", "effective_config", "header")
                        if isinstance(record.get(k), dict)]
    return {f"{value:016x}" for block in blocks for key in ("seed", "match_seed")
            if type(value := block.get(key)) is int and 0 <= value < 2**64}


def tournament_seed(base: int, round_number: int, first: str, second: str) -> str:
    """Independent transcription, bound externally to historical Git sources."""
    require(type(base) is int and 0 <= base < 2**64, "invalid historical base input")
    require(type(round_number) is int and round_number >= 1, "invalid historical round input")
    require(isinstance(first, str) and isinstance(second, str) and first != second,
            "invalid historical entrants")
    raw = f"battle2-tournament-v1\0{base}\0{round_number}\0{first}\0{second}".encode()
    return hashlib.sha256(raw).digest()[:8].hex()


def verify_finite_containment(proof: dict[str, Any], included: set[str]) -> int:
    """Check only the explicitly witnessed family, never its unknown history."""
    require(proof.get("scope") == "listed_witnessed_executions_only", "unproved domain expansion")
    witnesses = proof["witnesses"]
    require(bool(witnesses) and len({w["id"] for w in witnesses}) == len(witnesses), "invalid witness identities")
    proposed = values_hex(proof["set_hex"])
    require(proposed <= included, "containment set missing from candidate")
    for witness in witnesses:
        require(bool(witness.get("evidence_refs")), "witness lacks evidence")
        value = witness["recorded_seed_hex"]
        require(isinstance(value, str) and HEX.fullmatch(value) is not None and value in proposed,
                "recorded seed is not contained")
        if "reconstruction" in witness:
            require(tournament_seed(**witness["reconstruction"]) == value, "historical derivation mismatch")
    require(proof["cardinality"] == len(proposed), "containment cardinality mismatch")
    require(proof["set_sha256_raw"] == hashlib.sha256(canonical(proof["set_hex"])).hexdigest(),
            "containment set encoding mismatch")
    return len(witnesses)


def verify_crosswalk(original: list[dict[str, Any]], current: list[dict[str, Any]],
                     dependencies: list[dict[str, Any]]) -> None:
    ids = [r["id"] for r in original]
    require(len(ids) == len(set(ids)), "duplicate original gap identity")
    require([r["id"] for r in current] == ids, "original gap crosswalk changed")
    dependency_ids = {d["id"] for d in dependencies}
    require(len(dependency_ids) == len(dependencies), "duplicate dependency identity")
    for prior, row in zip(original, current, strict=True):
        require(row["original_category"] == prior["category"], "original category changed")
        require(row["original_disposition"] == prior["original_disposition"], "original disposition changed")
        require(row["dependencies"] and set(row["dependencies"]) <= dependency_ids,
                "unresolved row lacks a concrete dependency")
        require(row["coverage_status"] == "UNRESOLVED", "unsupported original-row closure")


def verify_packet(path: Path) -> int:
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        require(len(names) == len(set(names)), "duplicate packet member")
        require(all(not n.startswith(("/", "\\")) and ".." not in Path(n).parts for n in names),
                "unsafe packet member")
        checks = loads(archive.read("transport_checksums.json"))
        require(set(checks) == set(names) - {"transport_checksums.json"}, "packet checksum coverage mismatch")
        for name, expected in checks.items():
            require(hashlib.sha256(archive.read(name)).hexdigest() == expected, "packet member changed")
        return len(names)


def verify_saved_inventory(path: Path, audit_path: Path, included: set[str]) -> dict[str, int]:
    audit = loads(audit_path.read_bytes())
    originals = {r["path"]: r for r in audit["retained_metadata"]}
    require(len(originals) == len(audit["retained_metadata"]), "duplicate original metadata identity")
    seen: set[str] = set()
    matched: set[str] = set()
    counts = {"saved_rows": 0, "original_metadata_rows": 0, "no_decoded_seed_rows": 0, "malformed_rows": 0}
    with path.open("rb") as stream:
        for raw in stream:
            row = loads(raw)
            require(row["path_ref"] not in seen, "duplicate saved census identity")
            require(row["path_ref"] == "PATH-" + hashlib.sha256(row["path"].encode()).hexdigest()[:16],
                    "saved census path binding changed")
            seen.add(row["path_ref"])
            values = {f["value_hex"] for f in row["seed_fields"] if f["valid_uint64"]}
            values_hex(sorted(values))
            require(values <= included, "saved seed observation is not excluded")
            counts["saved_rows"] += 1
            if row["path"] in originals:
                prior = originals[row["path"]]
                require(prior["sha256_raw"] == row["sha256_metadata_raw"]
                        and prior["hash_scope"] == row["metadata_hash_scope"]
                        and set(prior["match_seeds_hex"]) == values, "original metadata binding changed")
                matched.add(row["path"])
                counts["original_metadata_rows"] += 1
            elif row["parse_status"] == "MALFORMED":
                counts["malformed_rows"] += 1
            elif not values:
                counts["no_decoded_seed_rows"] += 1
    require(matched == set(originals), "original saved metadata identities missing")
    return counts


def verify_retained_execution(witness: dict[str, Any], lookup: dict[str, str], included: set[str]) -> None:
    target = witness["target"]
    records = {}
    seed = witness["seed_hex"]
    require(seed in included, "retained execution seed is not excluded")
    for key, item in target.items():
        if key not in {"result_binding", "replay_binding", "replay_header_binding", "tournament_state_binding"}:
            continue
        path = Path(lookup[item["path_ref"]])
        with path.open("rb") as stream:
            raw = stream.readline(1_048_577) if key == "replay_header_binding" else stream.read()
        expected = item.get("sha256_whole_file_raw", item.get("sha256_raw"))
        require(hashlib.sha256(raw).hexdigest() == expected, "retained execution bytes changed")
        metadata = raw.splitlines(keepends=True)[0] if key == "replay_binding" else raw
        if "sha256_header_raw" in item:
            require(hashlib.sha256(metadata).hexdigest() == item["sha256_header_raw"], "retained header changed")
        records[key] = loads(metadata)
        if key != "tournament_state_binding":
            require(match_values(records[key]) == {seed}, "retained seed records disagree")
    if "result_binding" in records:
        result, replay = records["result_binding"], records["replay_binding"]
        require(result["schema"] == "battle2.result" and replay["schema"] == "battle2.replay",
                "retained native schema mismatch")
        require(result["match_id"] == replay["match_id"] and result["ruleset_id"] == replay["ruleset_id"]
                and result["replay"]["sha256"] == target["replay_binding"]["sha256_whole_file_raw"],
                "retained result/replay association mismatch")
    else:
        replay = records["replay_header_binding"]
        schedule = records["tournament_state_binding"]["matches"]
        expected_inputs = target["actual_schedule_inputs"]
        matches = [m for m in schedule if m["round_number"] == expected_inputs["round_number"]
                   and m["entrant_ids"] == expected_inputs["entrant_ids"]]
        require(len(matches) == 1 and match_values(matches[0]) == {seed}, "retained schedule/replay seed mismatch")
        saved = matches[0]
        state_path = Path(lookup[target["tournament_state_binding"]["path_ref"]])
        replay_path = Path(lookup[target["replay_header_binding"]["path_ref"]])
        relative = Path(saved["artifact_dir"].replace("\\", "/"))
        require(not relative.is_absolute() and ".." not in relative.parts
                and (state_path.parent / relative).resolve() == replay_path.parent.resolve(),
                "retained schedule/replay directory mismatch")
        require(replay["schema"] == "battle2.replay" and bool(replay["match_id"])
                and replay["reproducibility"]["entrant_order"] == expected_inputs["entrant_ids"],
                "retained replay identity mismatch")
        if saved.get("match_id") is None:
            require(saved["status"] == "corrupted" and saved["error_code"] == "resumed_result_mismatch",
                    "unexplained missing schedule match identity")
        else:
            require(saved["match_id"] == replay["match_id"], "retained schedule/replay identity mismatch")


def verify_ci_witness(witness: dict[str, Any], included: set[str]) -> None:
    jobs_response = loads(Path(witness["jobs_response_path"]).read_bytes())
    require(jobs_response["returncode"] == 0, "CI jobs unavailable")
    jobs = loads(jobs_response["stdout"])["jobs"]
    steps = [step for job in jobs for step in job["steps"] if step["name"] == witness["step_name"]]
    require(len(steps) == 1 and steps[0]["conclusion"] == "success", "CI reference step lacks success evidence")
    observed: set[str] = set()
    with zipfile.ZipFile(witness["log_archive_path"]) as archive:
        for name in archive.namelist():
            text = archive.read(name).decode("utf-8", errors="strict")
            for number in re.findall(r"--seed\s+(\d+)", text):
                value = int(number)
                require(0 <= value < 2**64, "CI input outside match-seed domain")
                observed.add(f"{value:016x}")
    require(observed == {witness["seed_hex"]} and observed <= included, "CI reference seed membership failed")


def verify(root: Path, evidence_path: Path) -> dict[str, Any]:
    evidence = loads(evidence_path.read_bytes())
    require(evidence["complete"] is False, "read-back cannot establish authority")
    bindings = evidence["bindings"]
    for item in bindings.values():
        require(SHA.fullmatch(item["sha256_raw"]) is not None, "invalid byte binding")
        require(file_sha(Path(item["path"])) == item["sha256_raw"], "evidence byte binding changed")
    for boundary in evidence["git_bindings"]:
        raw = subprocess.check_output(["git", "show", boundary["revision"] + ":" + boundary["repository_path"]], cwd=root)
        require(hashlib.sha256(raw).hexdigest() == boundary["sha256_git_raw"], "Git boundary changed")
        if boundary.get("worktree_sha256_raw"):
            require(file_sha(root / boundary["repository_path"]) == boundary["worktree_sha256_raw"],
                    "frozen worktree bytes changed")
    candidate = candidate_values(Path(bindings["CANDIDATE"]["path"]).read_bytes())
    require(len(candidate) == 157, "original candidate cardinality changed")
    packet_counts = {ref: verify_packet(Path(bindings[ref]["path"])) for ref in ("PACKET-01", "PACKET-02", "PACKET-03")}
    freeze = loads((root / "tools/research/v6/e9/protocol_freeze.json").read_bytes())
    require(hashlib.sha256(canonical(freeze["body"])[:-1]).hexdigest() == freeze["digest"], "protocol body digest failed")
    e6_record = loads((root / "tools/research/v6/e6/final_record.json").read_bytes())
    e6_raw = (root / e6_record["revealed_list"]["path"]).read_bytes()
    e6 = [int(v) for v in e6_raw.decode("ascii").splitlines()]
    require(e6_raw == b"".join(f"{v}\n".encode("ascii") for v in e6), "E6 list encoding changed")
    require(hashlib.sha256(e6_raw).hexdigest() == e6_record["seed_commitment"] == e6_record["revealed_list"]["sha256"],
            "E6 reveal commitment failed")
    e8_record = loads((root / "tools/research/v6/e8/seed_reveal.json").read_bytes())
    e8 = e8_record["seeds"]
    require(e8_record["seed_reveal"] is True and hashlib.sha256(b"".join(f"{v}\n".encode("ascii") for v in e8)).hexdigest()
            == e8_record["seed_commitment"], "E8 reveal commitment failed")
    for revealed in (e6, e8):
        require(len(revealed) == len(set(revealed)) == 32, "historical reveal cardinality failed")
        require(all(type(v) is int and 0 <= v < 2**64 and f"{v:016x}" in candidate for v in revealed),
                "historical reveal membership failed")
    scope = loads(Path(bindings["SCOPE"]["path"]).read_bytes())
    crosswalk = loads(Path(bindings["CROSSWALK"]["path"]).read_bytes())
    prior = loads(Path(bindings["PRIOR-DISPOSITIONS"]["path"]).read_bytes())
    verify_crosswalk(prior["rows"], crosswalk["rows"], scope["dependencies"])
    original = loads(Path(bindings["ORIGINAL-LEDGER"]["path"]).read_bytes())
    require([r["id"] for r in original["gaps"]] == [r["id"] for r in crosswalk["rows"]], "original ledger changed")
    require(len(crosswalk["rows"]) == 357 and scope["coverage_authority"] == "NOT ESTABLISHED",
            "unsupported scope authority")
    require(scope["complete"] is False and all(scope[key] is False for key in
            ("seed_generation", "commitment_publication", "payoff_execution")), "scope crosses authorization boundary")
    for dependency in scope["dependencies"]:
        require(all(dependency.get(k) for k in ("missing_scope_or_fact", "resolving_evidence", "recoverability",
                                                "custodian", "exact_limit")), "imprecise unresolved dependency")
    manifest = loads(Path(bindings["PARTIAL-MANIFEST"]["path"]).read_bytes())
    reverse = loads(Path(bindings["REVERSE-MAP"]["path"]).read_bytes())["seed_refs"]
    require(manifest["complete"] is False and len({g["id"] for g in manifest["groups"]}) == len(manifest["groups"]),
            "partial manifest identity or completeness failed")
    for group in manifest["groups"]:
        recorded = values_hex(group["match_seeds_hex"])
        require(recorded <= candidate and {reverse[ref] for ref in group["seed_refs"]} == recorded,
                "partial manifest seed/reference mismatch")
    manifest_index = loads(Path(bindings["MANIFEST-INDEX"]["path"]).read_bytes())
    require(manifest_index["private_manifest_sha256_raw"] == file_sha(Path(bindings["PARTIAL-MANIFEST"]["path"])),
            "shareable manifest digest failed")
    counts = verify_saved_inventory(Path(bindings["SAVED-INVENTORY"]["path"]), Path(bindings["ORIGINAL-AUDIT"]["path"]), candidate)
    require(counts == {"saved_rows": 464207, "original_metadata_rows": 462553,
                       "no_decoded_seed_rows": 1491, "malformed_rows": 163}, "saved census accounting changed")
    lookup = evidence["path_lookup"]
    for witness in evidence["retained_execution_witnesses"]:
        verify_retained_execution(witness, lookup, candidate)
    verify_ci_witness(evidence["ci_reference_witness"], candidate)
    contained = sum(verify_finite_containment(p, candidate) for p in evidence["containment_checks"])
    private_root = Path(evidence["existing_private_root"])
    require(not any((private_root / n).exists() for n in ("seed_payload.json", "seed_salt.bin", "cells", "execution.json",
                                                         "exclusion_inventory.json")), "unauthorized boundary present")
    return {"schema": "bytefray.v6.e9.historical_scope_verification", "version": 1,
            "evidence_sha256_raw": file_sha(evidence_path), "integrity": "PASS", "membership": "PASS",
            "byte_bindings_checked": len(bindings), "Git_bindings_checked": len(evidence["git_bindings"]),
            "inherited_files_unchanged": sum(ref.startswith("INHERITED-") for ref in bindings),
            "saved_inventory_readback": counts, "raw_corpus_readback_this_pass": "TEN_LINKED_B08_B12_EXECUTIONS_ONLY",
            "prior_whole_corpus_raw_rehash": "REPORTED_EVIDENCE; RETAINED_RECEIPT_BYTES_VERIFIED",
            "packet_members": packet_counts, "original_candidate_entries": len(candidate), "original_gap_rows": 357,
            "linked_execution_witnesses": len(evidence["retained_execution_witnesses"]),
            "CI_explicit_reference_step_seed_inclusion": "PASS", "partial_manifest_groups": len(manifest["groups"]),
            "finite_containment_witnesses": contained, "containment_scope": "listed_witnessed_executions_only",
            "E6_E8_inclusion": "PASS", "sampling_rules": "UNCHANGED; EXPLICIT_LIST_SUPPORTED",
            "completeness": "NOT ESTABLISHED", "coverage": "Coverage incomplete; generation LOCKED",
            "seed_generation": False, "commitment_publication": False, "payoff_execution": False,
            "requirement_C": "NOT ESTABLISHED"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = verify(Path(__file__).resolve().parents[4], args.evidence)
        raw = canonical(result)
        if args.receipt.exists():
            require(args.receipt.read_bytes() == raw, "existing receipt differs")
        else:
            with args.receipt.open("xb") as stream:
                stream.write(raw)
    except (OSError, ValueError, KeyError, IndexError, TypeError, subprocess.CalledProcessError, zipfile.BadZipFile):
        print("REFUSED: historical scope evidence is unusable; generation LOCKED")
        return 2
    print("PASS: integrity and membership; historical coverage incomplete; generation LOCKED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
