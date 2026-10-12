"""Independent read-back of prepared artifacts and included exclusion evidence.

This checks recorded values and bytes. It cannot promote historical coverage
to complete, draw seeds, or authorize payoff execution.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from .instrument import require_qualified
from .protocol import ROOT, IntegrityError, load_protocol, write_once
from .runner import check_private, materialize, private_root


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def encoded(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                      allow_nan=False).encode("utf-8")


def read(path: Path):
    return json.loads(path.read_bytes())


def verify() -> None:
    protocol = load_protocol()
    instrument = require_qualified()
    root = private_root(instrument)
    check_private(root)
    public = read(ROOT / "tools/research/v6/e9/preparation_record.json")
    private = read(root / "preparation.json")
    binding = read(root / "evaluation_artifacts.json")
    body = binding["body"]
    if (sha(encoded(body)) != binding["digest"] or binding["digest"] != private["artifact_binding_digest"]
            or binding["digest"] != public["artifact_binding"]["digest"]
            or body["instrument_digest"] != instrument
            or public["preparation_source_sha256_raw"] != sha((ROOT / "tools/research/v6/e9/prepare.py").read_bytes())):
        raise IntegrityError("preparation source or binding changed")
    qualification = read(ROOT / "tools/research/v6/e9/instrument_qualification.json")
    paths = {**qualification["sources"], **qualification["qualification_sources"],
             "tools/research/v6/e9/instrument_qualification.json": "01456bdda6a1b6749af2a6c7e81ea82abefcacfabe0b6cab5cc5ee38611d6d0a"}
    for name, expected in paths.items():
        committed = subprocess.check_output(["git", "show", body["instrument_commit"] + ":" + name], cwd=ROOT)
        if sha(committed) != expected or committed != (ROOT / name).read_bytes():
            raise IntegrityError("qualified commit bytes changed")
    if materialize(root, protocol) != body["resolved_defaults"]:
        raise IntegrityError("parameter defaults changed")
    expected_names = set(protocol["historical_packages"]) | set(protocol["prospective_packages"])
    if set(body["packages"]) != expected_names or len(expected_names) != 41:
        raise IntegrityError("materialized package inventory changed")
    for name, files in body["packages"].items():
        if set(files) != {"agent.py", "agent.yaml"}:
            raise IntegrityError("package file inventory changed")
        for filename, expected in files.items():
            if sha((root / "agents" / name / filename).read_bytes()) != expected:
                raise IntegrityError("package bytes changed")
    for key in ("effective_t8", "logical_aliases", "physical_packages", "historical_members"):
        if encoded(body[key]) != encoded(protocol[key]):
            raise IntegrityError("registered conditions changed")
    inventory_path = root / "exclusion_inventory.candidate.json"
    audit_path = root / "exclusion_audit.json"
    inventory, audit = read(inventory_path), read(audit_path)
    for path, value, expected in (
            (inventory_path, inventory, public["exclusion"]["candidate_sha256_raw"]),
            (audit_path, audit, public["exclusion"]["audit_sha256_raw"])):
        raw = path.read_bytes()
        if raw != encoded(value) + b"\n" or sha(raw) != expected:
            raise IntegrityError("canonical exclusion evidence changed")
    values = inventory["match_seeds_hex"]
    if (values != sorted(set(values))
            or any(len(v) != 16 or set(v) - set("0123456789abcdef") for v in values)
            or inventory["complete"] is not False
            or inventory["coverage"] != {"E6": True, "E8": True, "all_prior_match_qualification": False}):
        raise IntegrityError("candidate domain/uniqueness/coverage changed")
    included = set(values)
    for source in inventory["provenance"]:
        if sha(Path(source["path"]).read_bytes()) != source["sha256_raw"]:
            raise IntegrityError("exclusion provenance changed")
    e6_record = read(ROOT / "tools/research/v6/e6/final_record.json")
    e6_raw = (ROOT / e6_record["revealed_list"]["path"]).read_bytes()
    e6 = [int(v) for v in e6_raw.decode("ascii").splitlines()]
    e8_record = read(ROOT / "tools/research/v6/e8/seed_reveal.json")
    e8 = e8_record["seeds"]
    if (len(e6) != len(set(e6)) or len(e6) != 32 or len(e8) != len(set(e8)) or len(e8) != 32
            or sha(e6_raw) != e6_record["seed_commitment"]
            or sha(b"".join((str(v) + "\n").encode("ascii") for v in e8)) != e8_record["seed_commitment"]
            or any(f"{v:016x}" not in included for v in (*e6, *e8))):
        raise IntegrityError("E6/E8 exclusion membership failed")

    def metadata(source):
        path = Path(source["path"])
        if source["hash_scope"] == "first_line":
            with path.open("rb") as handle:
                raw = handle.readline(1_048_577)
        else:
            raw = path.read_bytes()
        if sha(raw) != source["sha256_raw"]:
            raise IntegrityError("retained metadata bytes changed")
        record = json.loads(raw)
        actual = set()
        for item in (record, *(record.get(k) for k in ("config", "reproducibility", "effective_config", "header"))):
            if not isinstance(item, dict):
                continue
            for key in ("seed", "match_seed"):
                number = item.get(key)
                if type(number) is int and 0 <= number < 2**64:
                    actual.add(f"{number:016x}")
        if actual != set(source["match_seeds_hex"]) or not actual <= included:
            raise IntegrityError("independently decoded exclusion membership failed")

    with ThreadPoolExecutor(max_workers=16) as pool:
        for start in range(0, len(audit["retained_metadata"]), 512):
            list(pool.map(metadata, audit["retained_metadata"][start:start + 512]))
            if start % 65536 == 0:
                print("Independent metadata read-back:", min(start + 512, len(audit["retained_metadata"])), flush=True)
    if any((root / name).exists() for name in ("seed_payload.json", "seed_salt.bin", "cells", "execution.json")):
        raise IntegrityError("unauthorized seed/payoff boundary crossed")
    record = {"schema": "bytefray.v6.e9.preparation_verification", "version": 1,
              "artifact_binding": "PASS", "instrument_commit": body["instrument_commit"],
              "artifact_binding_digest": binding["digest"], "package_count": len(body["packages"]),
              "exclusion_canonical_domain_uniqueness_provenance": "PASS",
              "E6_E8_committed_lists_excluded": "PASS", "retained_match_metadata_reverified": len(audit["retained_metadata"]),
              "all_prior_qualification_coverage": "NOT ESTABLISHED", "seed_generation": False,
              "payoff_execution": False, "requirement_C": "NOT ESTABLISHED"}
    destination = ROOT / "tools/research/v6/e9/preparation_verification.json"
    if destination.exists():
        if destination.read_bytes() != encoded(record) + b"\n":
            raise IntegrityError("prior verification evidence differs")
    else:
        write_once(destination, record)
    companion = {"schema": "bytefray.v6.e9.preparation_verifier", "version": 1,
                 "source_sha256_raw": sha(Path(__file__).read_bytes()),
                 "verification_sha256_raw": sha(destination.read_bytes()),
                 "method": "independent JSON/hex/membership read-back with raw SHA-256; bounded parallel I/O",
                 "coverage": "NOT COMPLETE", "seed_generation": False, "payoff_execution": False}
    write_once(ROOT / "tools/research/v6/e9/preparation_verifier.json", companion)
    print("PASS: bound artifacts and included exclusion values; historical coverage NOT COMPLETE; execution LOCKED")


if __name__ == "__main__":
    try:
        verify()
    except (IntegrityError, OSError, ValueError, KeyError, TypeError):
        print("Independent preparation verification refused: unusable evidence")
        raise SystemExit(2) from None
