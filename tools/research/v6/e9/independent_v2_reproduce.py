"""Independent manifest/reference auditor; never executes matches or draws.

The qualifier owns this source separately from the instrument. It rehashes
exact complete manifests, frozen adoption and inherited source pins, and
derives deterministic identity/index digests with standard-library code.
The caller executes only the explicitly audited tests in a separate process.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
BASE = ROOT / "tools/research/v6/e9"
P_DIGEST = "539a60806eab03f1c3534406d96616cec59fc8868fa7df1b567953aa08239ae0"
P_RAW = "c021e6713d13d3831b31f246f821ca3dfca0e3d0f10229c94efd97a0dd850a8d"


def encoded(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"),
                      allow_nan=False).encode()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def rehash_manifest(manifest):
    actual = {path: digest((ROOT / path).read_bytes()) for path in manifest}
    if actual != manifest:
        raise ValueError("exact manifest bytes changed")
    return actual


def independently_derive_vectors(p, instrument):
    key = hashlib.sha256(b"bytefray-e9-analysis-bootstrap-v1\n" + p.encode() + b"\n"
                         + instrument.encode() + b"\n").digest()
    values, counter = [], 0
    ceiling = (2**64 // 1412) * 1412
    while len(values) < 64:
        candidate = int.from_bytes(hashlib.sha256(key + counter.to_bytes(8, "big")).digest()[:8], "big")
        if candidate < ceiling:
            values.append(candidate % 1412)
        counter += 1
    p_id = "v6-e9-prereg-v2-" + p[:12]
    cell = "v6-e9-cell-v2-" + digest(encoded([p_id, "A", "RUSH8", 1, "A"]))
    return {"bootstrap_index_fixture": {"opaque_id": "IV2-INDEX-64", "count": 64,
                                       "canonical_vector_sha256": digest(encoded(values))},
            "private_root_token_fixture": {"opaque_id": "IV2-ROOT", "digest": digest(
                b"bytefray-e9-private-root-v1\n" + bytes.fromhex(p) + bytes.fromhex(instrument))},
            "logical_cell_fixture": {"opaque_id": "IV2-CELL", "identity": cell},
            "dispatch_fixture": {"opaque_id": "IV2-DISPATCH", "identity": "v6-e9-dispatch-v2-" + digest(
                encoded(["independent-vector-study", p, instrument, cell, 1]))}}


def verify(implementation_manifest, qualification_manifest):
    proposed_raw = (BASE / "protocol_freeze_v2_proposed_02.json").read_bytes()
    proposed = json.loads(proposed_raw)
    if digest(proposed_raw) != P_RAW or digest(encoded(proposed["body"])) != P_DIGEST:
        raise ValueError("authorized reviewed protocol binding mismatch")
    for path, pin in proposed["body"]["contract_files"].items():
        if digest((ROOT / path).read_bytes()) != pin["sha256_raw"]:
            raise ValueError("reviewed contract-file mismatch")
    adopted_raw = (BASE / "protocol_freeze_v2_adopted_02.json").read_bytes()
    adopted = json.loads(adopted_raw)
    if adopted["body"] != proposed["body"] or adopted["digest"] != P_DIGEST or adopted["status"] != "FROZEN":
        raise ValueError("adoption altered reviewed body or lacks frozen status")
    attestation_raw = (BASE / "protocol_adoption_attestation_v2_02.json").read_bytes()
    attestation = json.loads(attestation_raw)
    att_body = attestation["body"]
    if (digest(encoded(att_body)) != attestation["digest"]
            or att_body["reviewed_body_digest"] != P_DIGEST
            or att_body["reviewed_proposed_envelope_raw_sha256"] != P_RAW
            or att_body["adopted_record"]["sha256_raw"] != digest(adopted_raw)):
        raise ValueError("independent adoption-attestation reproduction failed")
    for path, expected in att_body["verified_review_bindings"].items():
        if digest((ROOT / path).read_bytes()) != expected:
            raise ValueError("independent reviewed/archive binding drift")
    sources = rehash_manifest(implementation_manifest)
    tests = rehash_manifest(qualification_manifest)
    instrument = digest(encoded({"protocol_digest": P_DIGEST, "sources": sources}))
    return {"qualifier": "independent_qualifier", "independent_of_implementation": True,
            "protocol_identity": proposed["identity"], "protocol_digest": P_DIGEST,
            "reviewed_proposed_envelope_sha256_raw": P_RAW,
            "adopted_record_sha256_raw": digest(adopted_raw),
            "adoption_attestation_sha256_raw": digest(attestation_raw),
            "adoption_attestation_identity": attestation["identity"],
            "implementation_sources": sources, "qualification_sources": tests,
            "instrument_identity": "v6-e9-instrument-v2-" + instrument[:12],
            "instrument_digest": instrument,
            "reference_vectors": independently_derive_vectors(P_DIGEST, instrument),
            "experimental_execution": "LOCKED", "historical_coverage": "NOT ESTABLISHED",
            "requirement_C": "NOT ESTABLISHED", "match_execution_count": 0,
            "real_seed_or_salt_draw_count": 0, "qualification_execution": "SEPARATE_EXACT_MANIFEST_TEST_RUN_REQUIRED"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--implementation-manifest", type=Path, required=True)
    parser.add_argument("--qualification-manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = verify(json.loads(args.implementation_manifest.read_bytes()),
                    json.loads(args.qualification_manifest.read_bytes()))
    with args.output.open("xb") as stream:
        stream.write(encoded(result) + b"\n")
    print(json.dumps({"manifest_verification": "PASS", "instrument_identity": result["instrument_identity"],
                      "output_sha256_raw": digest(args.output.read_bytes())}, sort_keys=True))


if __name__ == "__main__":
    main()
