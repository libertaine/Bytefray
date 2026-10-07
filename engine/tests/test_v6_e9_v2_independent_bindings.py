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
    preserved = json.loads((E9 / "v2_inherited_preservation_manifest_01.json").read_bytes())
    for path, expected in preserved["tracked_files"].items():
        assert independent_sha((ROOT / path).read_bytes()) == expected


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
