"""Independent read-only qualification of the exact reviewed v2 boundary.

No production record encoder, match service, entropy source or bootstrap
statistic is used to derive these expected values.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
E9 = ROOT / "tools/research/v6/e9"
P_DIGEST = "539a60806eab03f1c3534406d96616cec59fc8868fa7df1b567953aa08239ae0"
P_RAW = "c021e6713d13d3831b31f246f821ca3dfca0e3d0f10229c94efd97a0dd850a8d"


def independent_json(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def independent_sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def reviewed() -> dict:
    return json.loads((E9 / "protocol_freeze_v2_proposed_02.json").read_bytes())


def test_reviewed_exact_body_envelope_and_all_contract_hashes():
    raw = (E9 / "protocol_freeze_v2_proposed_02.json").read_bytes()
    record = reviewed()
    assert independent_sha(raw) == P_RAW
    assert independent_sha(independent_json(record["body"])) == P_DIGEST
    assert record["identity"] == "v6-e9-prereg-v2-539a60806eab"
    assert record["status"] == "PROPOSED_NOT_FROZEN"
    assert raw == independent_json(record) + b"\n"
    for path, ref in record["body"]["contract_files"].items():
        assert independent_sha((ROOT / path).read_bytes()) == ref["sha256_raw"]


def test_separate_adoption_attestation_exact_review_and_unchanged_body():
    proposed = reviewed()
    adopted_raw = (E9 / "protocol_freeze_v2_adopted_02.json").read_bytes()
    adopted = json.loads(adopted_raw)
    assert adopted == {**proposed, "status": "FROZEN"}
    assert independent_sha(adopted_raw) == "63e678d75dc8b73cc7e69ac2c413bc58d26220ec883748355d9e85c6a227f2b4"
    att_raw = (E9 / "protocol_adoption_attestation_v2_02.json").read_bytes()
    att = json.loads(att_raw)
    assert independent_sha(independent_json(att["body"])) == att["digest"]
    assert att_raw == independent_json(att) + b"\n"
    assert att["body"]["reviewed_body_digest"] == P_DIGEST
    assert att["body"]["reviewed_proposed_envelope_raw_sha256"] == P_RAW
    assert att["body"]["adopted_record"]["sha256_raw"] == independent_sha(adopted_raw)
    for path, expected in att["body"]["verified_review_bindings"].items():
        assert independent_sha((ROOT / path).read_bytes()) == expected
    archive = ROOT / "docs/research/v6/e9_amended_freeze_review_02.zip"
    with zipfile.ZipFile(archive) as z:
        assert len(z.namelist()) == len(set(z.namelist())) == 20
        for path in z.namelist():
            assert z.read(path) == (ROOT / path).read_bytes()
    adoption_commit = "2dd8f69c5c6feb5f3a7d8fc0eb81b0c06802dee2"
    adoption_blob = "7064b0bb9d533b312b45f0c368610a64777ec8b6"
    adoption_pin = "d26332b37bbcac74a5e369317df33cbbecd4042f4ca6867770e38a54307bfd86"
    checkpoint_commit = "e035def989dfc5e26ae3eb2c9ccfd16aed54b66c"
    checkpoint_blob = "89bba2ee71b70188107be24fd918c078b0b6ae76"
    superseding_sha = "97128feeef25cbe98af6770173d09a809b1c0f626ec2a5ac558236aaf4b99555"
    manifest_raw = (E9 / "v2_inherited_preservation_manifest_01.json").read_bytes()
    assert independent_sha(manifest_raw) == "b1f86c1d9b59be0f8841bf1b587b7a88d3ffb7bed34cffa476ef582606660147"
    preserved = json.loads(manifest_raw)
    pins = preserved["tracked_files"]
    assert pins[".gitattributes"] == adoption_pin
    record_raw = (E9 / "v2_inherited_preservation_supersession_01.json").read_bytes()
    assert independent_sha(record_raw) == "319528a4d7e29266a680e198acea9769229cef41aaf86693607e5044852b4661"
    record = json.loads(record_raw)
    assert record_raw == independent_json(record) + b"\n"
    assert independent_sha(independent_json(record["body"])) == record["digest"]
    assert record["digest"] == "a82d0caccf3b131d4ee853bac1174868db338b6b71d032be33c2677178dd4e9f"
    assert record["identity"] == "v6-e9-v2-preservation-supersession-a82d0caccf3b"
    original = record["body"]["original_manifest"]
    assert original["path"] == "tools/research/v6/e9/v2_inherited_preservation_manifest_01.json"
    assert original["sha256_raw"] == independent_sha(manifest_raw)
    assert original["tracked_file_pins"] == len(pins) == 1203
    assert record["body"]["semantics"]["superseded_paths"] == [".gitattributes"]
    entry = record["body"]["superseded_entry"]
    assert entry["path"] == ".gitattributes"
    assert entry["adoption_pin_sha256_raw"] == adoption_pin
    assert entry["superseding_bytes"]["commit_parent"] == adoption_commit
    assert independent_sha(entry["change"]["diff_utf8"].encode("utf-8")) == entry["change"]["diff_sha256_raw"]
    parents = subprocess.check_output(["git", "rev-list", "--parents", "-n", "1", checkpoint_commit],
                                      cwd=ROOT, text=True)
    assert parents == f"{checkpoint_commit} {adoption_commit}\n"
    for side, commit, blob, sha in (("adoption_bytes", adoption_commit, adoption_blob, adoption_pin),
                                    ("superseding_bytes", checkpoint_commit, checkpoint_blob, superseding_sha)):
        assert (entry[side]["commit"], entry[side]["git_blob"], entry[side]["sha256_raw"]) == (commit, blob, sha)
        tree_entry = subprocess.check_output(["git", "rev-parse", "--verify", f"{commit}:.gitattributes"],
                                             cwd=ROOT, text=True)
        assert tree_entry == f"{blob}\n"
        blob_raw = subprocess.check_output(["git", "cat-file", "blob", blob], cwd=ROOT)
        assert hashlib.sha1(b"blob " + str(len(blob_raw)).encode() + b"\x00" + blob_raw).hexdigest() == blob
        assert independent_sha(blob_raw) == sha
        assert blob_raw == entry[side]["utf8"].encode("utf-8")
    current = (ROOT / ".gitattributes").read_bytes()
    assert independent_sha(current) == superseding_sha
    assert current == subprocess.check_output(["git", "cat-file", "blob", checkpoint_blob], cwd=ROOT)
    actual = {path: independent_sha((ROOT / path).read_bytes()) for path in pins}
    mismatched = {path: digest for path, digest in actual.items() if digest != pins[path]}
    assert mismatched == {".gitattributes": superseding_sha}


def test_preserved_r0_parent_and_draft_bytes():
    body = reviewed()["body"]
    for key in ("amendment_decision", "parent_freeze", "original_draft_3"):
        ref = body[key]
        raw = (ROOT / ref["path"]).read_bytes()
        assert independent_sha(raw) == ref["sha256_raw"]
        if key != "original_draft_3":
            old = json.loads(raw)
            assert old["identity"] == ref["identity"]
            assert old["digest"] == ref["digest"]
            assert independent_sha(independent_json(old["body"])) == ref["digest"]


def test_preserved_all_frozen_scientific_raw_and_lf_sources():
    pins = reviewed()["body"]["inherited_scientific_source_pins"]
    for path, expected in pins["qualified_e9_raw"].items():
        assert independent_sha((ROOT / path).read_bytes()) == expected
    for path, expected in pins["frozen_e8_lf"].items():
        assert independent_sha((ROOT / path).read_bytes().replace(b"\r\n", b"\n")) == expected
    for path, expected in pins["governing_files"].items():
        raw = (ROOT / path).read_bytes()
        assert independent_sha(raw) == expected["sha256_raw"]
        assert independent_sha(raw.replace(b"\r\n", b"\n")) == expected["sha256_lf"]
    paths = sorted(subprocess.check_output(["git", "ls-files", "engine/src"], cwd=ROOT,
                                           text=True).splitlines())
    manifest = "".join(independent_sha((ROOT / path).read_bytes().replace(b"\r\n", b"\n"))
                       + "  " + path + "\n" for path in paths)
    assert len(paths) == pins["engine_source"]["files"] == 116
    assert independent_sha(manifest.encode()) == pins["engine_source"]["sha256_lf_manifest"]
    for package, pin in pins["historical_packages"].items():
        for filename, field in (("agent.py", "agent_py_sha256"), ("agent.yaml", "agent_yaml_sha256")):
            raw = (ROOT / "tools/research/v6/e8/fixtures/agents" / package / filename).read_bytes()
            assert independent_sha(raw.replace(b"\r\n", b"\n")) == pin[field]


def test_exact_scientific_rectangle_and_decision_constants():
    pins = reviewed()["body"]["inherited_scientific_source_pins"]
    assert pins["sample"]["N"] == 1412
    assert len(pins["physical_rows"]) == 29
    assert pins["sample"]["opponents"] == 11
    assert pins["sample"]["seats"] == ["A", "B"]
    assert 29 * 11 * 1412 * 2 == pins["sample"]["payoff_cells"] == 900856
    assert len(pins["schedules"]) == 16
    assert pins["analysis"]["resamples"] == 20000
    assert pins["analysis"]["order_statistic_one_based"] == 19000
    assert pins["analysis"]["benefit_margin"] == pins["analysis"]["timing_allowance"] == "1/10"
    assert pins["analysis"]["row_guard"] == "1/20"
    assert pins["recovery"]["max_started_attempts"] == 2
    assert pins["recovery"]["max_recovery_attempts"] == 1
    assert pins["logical_aliases"] == {"D": "REACQ8", "DENSE": "REACQ8", "OFF": "RUSH8"}
    assert len(pins["historical_packages"]) + len(pins["prospective_packages"]) == 41


def test_all_gap_and_dependency_ids_remain_frozen():
    contract = json.loads((E9 / "amended_rule_contract_v2_proposed_02.json").read_bytes())
    assert len(contract["preserved_gap_ids"]) == len(set(contract["preserved_gap_ids"])) == 357
    assert contract["preserved_dependency_ids"] == [f"DEP-{i:02}" for i in range(1, 6)]
    assert contract["claim_profile"] == "C-LIMITED"
    schemas = json.loads((E9 / "amended_record_schemas_v2_proposed_02.json").read_bytes())
    assert len(schemas["records"]) == 25


@pytest.mark.parametrize("role,expected", [
    ("W", "P I Q O V A R B G S"),
    ("U", "P I Q O V A R B G S W"),
    ("C", "P I Q O V A R B G S W U"),
])
def test_w_u_c_catalogue_actual_record_refs_exclude_primitive_c(role, expected):
    schemas = json.loads((E9 / "amended_record_schemas_v2_proposed_02.json").read_bytes())
    record = schemas["records"][role]
    assert record["record_reference_dependencies"] == expected.split()
    assert record["primitive_dependency_fields"] == {"c": "commitment"}
    assert "c" not in record["record_reference_dependencies"]
    assert "C" not in record["record_reference_dependencies"]
