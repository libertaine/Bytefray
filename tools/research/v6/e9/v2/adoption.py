"""Exact review-02 adoption, separate from the unchanged reviewed envelope."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import zipfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[5]
BASE = ROOT / "tools/research/v6/e9"
P_DIGEST = "539a60806eab03f1c3534406d96616cec59fc8868fa7df1b567953aa08239ae0"
P_ID = "v6-e9-prereg-v2-539a60806eab"
PROPOSED_RAW = "c021e6713d13d3831b31f246f821ca3dfca0e3d0f10229c94efd97a0dd850a8d"
PROPOSED = BASE / "protocol_freeze_v2_proposed_02.json"
ADOPTED = BASE / "protocol_freeze_v2_adopted_02.json"
ATTESTATION = BASE / "protocol_adoption_attestation_v2_02.json"
CONVENTION = "SHA256 of UTF-8 canonical body, sorted keys, compact separators, no trailing LF"


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def exclusive(path: Path, value: Any) -> str:
    raw = canonical(value) + b"\n"
    with path.open("xb") as handle:
        handle.write(raw)
        handle.flush()
        os.fsync(handle.fileno())
    return digest(raw)


def verify_review() -> tuple[dict[str, Any], dict[str, str]]:
    raw = PROPOSED.read_bytes()
    p = json.loads(raw)
    if (digest(raw) != PROPOSED_RAW or digest(canonical(p["body"])) != P_DIGEST
            or p["identity"] != P_ID or p["digest"] != P_DIGEST
            or p["status"] != "PROPOSED_NOT_FROZEN"):
        raise ValueError("reviewed P binding mismatch")
    bindings = {str(PROPOSED.relative_to(ROOT)).replace("\\", "/"): PROPOSED_RAW}
    for name, expected in p["body"]["contract_files"].items():
        actual = digest((ROOT / name).read_bytes())
        if actual != expected["sha256_raw"]:
            raise ValueError("reviewed contract-file mismatch")
        bindings[name] = actual
    for key in ("amendment_decision", "parent_freeze", "original_draft_3"):
        ref = p["body"][key]
        actual = digest((ROOT / ref["path"]).read_bytes())
        if actual != ref["sha256_raw"]:
            raise ValueError("reviewed antecedent mismatch")
        bindings[ref["path"]] = actual
    package_path = BASE / "amended_freeze_review_package_02.json"
    package = json.loads(package_path.read_bytes())
    if digest(canonical(package["body"])) != package["digest"]:
        raise ValueError("review package canonical digest mismatch")
    for name, expected in package["body"]["files"].items():
        data = (ROOT / name).read_bytes()
        if len(data) != expected["bytes"] or digest(data) != expected["sha256_raw"]:
            raise ValueError("review package member mismatch")
        bindings[name] = digest(data)
    archive = ROOT / "docs/research/v6/e9_amended_freeze_review_02.zip"
    checksum = Path(str(archive) + ".sha256").read_text().split()[0].lower()
    if digest(archive.read_bytes()) != checksum:
        raise ValueError("review archive digest mismatch")
    with zipfile.ZipFile(archive) as z:
        names = z.namelist()
        if len(names) != 20 or len(set(names)) != 20:
            raise ValueError("review archive member count/uniqueness mismatch")
        for name in names:
            if name.endswith("/") or name.startswith("/") or ".." in Path(name).parts:
                raise ValueError("unexpected archive member")
            if z.read(name) != (ROOT / name).read_bytes():
                raise ValueError("review archive bytes differ from local input")
            bindings[name] = digest(z.read(name))
    bindings[str(archive.relative_to(ROOT)).replace("\\", "/")] = checksum
    # The frozen v1 verifier only hashes/reads sources and packages; it runs no matches.
    from tools.research.v6.e9.protocol import load_protocol, package_bytes
    inherited = load_protocol(verify=True)
    pins = p["body"]["inherited_scientific_source_pins"]
    if any(key not in inherited or inherited[key] != value for key, value in pins.items()):
        raise ValueError("inherited complete source/scientific pins differ")
    for row in inherited["physical_rows"]:
        if row in ("A", "MEDIUM", "SPARSE") or row.startswith(("S0", "S1")):
            package_bytes(row, inherited)
    return p, bindings


def adopt() -> dict[str, Any]:
    p, bindings = verify_review()
    if ADOPTED.exists() or ATTESTATION.exists():
        raise FileExistsError("adoption evidence already exists; never overwrite")
    adopted = {**p, "status": "FROZEN"}
    adopted_raw = exclusive(ADOPTED, adopted)
    body = {
        "date": "2026-10-03", "actor": "research lead via explicit user authorization",
        "authorization_source": "current conversation: exact freeze and implementation/qualification authorization",
        "authorization": "Adopt the exact reviewed amended protocol; implement all review 02 workstreams; independent synthetic qualification only. No native matches, historical suites, experimental bootstrap analyses, real seed/salt draws, inventory adoption, operational risk acceptance R, commitment publication or payoff execution. Leave changes uncommitted.",
        "protocol_identity": P_ID, "reviewed_body_digest": P_DIGEST,
        "reviewed_proposed_envelope_raw_sha256": PROPOSED_RAW,
        "adopted_record": {"path": str(ADOPTED.relative_to(ROOT)).replace("\\", "/"),
                           "sha256_raw": adopted_raw},
        "verified_review_bindings": bindings, "reviewed_body_preserved": True,
        "reviewed_proposed_envelope_preserved": True, "governing_after_adoption": P_ID,
        "execution": "LOCKED", "historical_coverage": "NOT ESTABLISHED",
        "requirement_C": "NOT ESTABLISHED", "private_inventory_adoption": "NOT AUTHORIZED",
        "qualification_authority": "independent synthetic only; exact source/test manifests; deterministic injected inputs/faults",
        "qualification_temp_root": "D:/Projects/BATTLE2-test-temp/",
    }
    d = digest(canonical(body))
    attestation = {"schema": "bytefray.v6.e9.protocol_adoption_attestation", "version": 2,
                   "identity": "v6-e9-adoption-v2-" + d[:12], "digest": d,
                   "digest_convention": CONVENTION, "body": body}
    attestation_raw = exclusive(ATTESTATION, attestation)
    if PROPOSED.read_bytes() != canonical(p) + b"\n":
        raise ValueError("reviewed proposed bytes changed")
    tracked = subprocess.check_output(["git", "ls-files"], cwd=ROOT, text=True).splitlines()
    inherited_manifest = {name: digest((ROOT / name).read_bytes()) for name in tracked
                          if (ROOT / name).is_file()}
    exclusive(BASE / "v2_inherited_preservation_manifest_01.json", {
        "schema": "bytefray.v6.e9.inherited_preservation_manifest", "version": 2,
        "protocol_digest": P_DIGEST, "tracked_files": inherited_manifest,
        "review_bindings": bindings})
    return {"protocol_identity": P_ID, "protocol_body_digest": P_DIGEST,
            "adopted_raw_sha256": adopted_raw, "attestation_identity": attestation["identity"],
            "attestation_body_digest": d, "attestation_raw_sha256": attestation_raw,
            "review_bindings_verified": len(bindings)}


if __name__ == "__main__":
    print(json.dumps(adopt(), indent=2))
