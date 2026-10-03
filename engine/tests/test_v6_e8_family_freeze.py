"""V6 E8: the family freeze (phase I8-4), v1.

The record turns the implemented, qualified family into an immutable
experimental input. It pins, at the tooling commit, the 22 packages and the
one policy source, the manifest parameter table and the declarations, the
sets (A8 among them), the census from the manifests of both roles, the
compatibility classification, the final Ruleset identifiers, the structural
matrix identity, the RNG and behavior invariants with the tests that pin them,
the qualification evidence (every E8 test file of I8-1 to I8-4, by digest and
collected count), the engine source the family was qualified against, and the
implementation notes the research lead asked for. It recomputes from the live
checkout, every pinned file equals its content at the tooling commit, any
drift fails closed, and no seed exists.
"""

from __future__ import annotations

import copy
import hashlib
import json
import subprocess
from pathlib import Path

import pytest

from tools.research.v6.e8 import decision, family, family_freeze, matrix, preregistration_freeze

ROOT = Path(__file__).resolve().parents[2]
IDENTITY = "v6-e8-family-v1-981fc8b12beb"
TOOLING_COMMIT = "2ba2487"


def _stored() -> dict:
    return json.loads(family_freeze.FREEZE_PATH.read_text(encoding="utf-8"))


def _git_digest(commit: str, path: str) -> str:
    content = subprocess.run(["git", "show", f"{commit}:{path}"], cwd=ROOT, capture_output=True, check=True).stdout
    return hashlib.sha256(content.replace(b"\r\n", b"\n")).hexdigest()


def test_the_freeze_loads_and_its_identity_is_pinned() -> None:
    frozen = family_freeze.load_freeze()
    assert frozen["identity"] == IDENTITY
    assert family_freeze.identity(frozen["digest"]) == IDENTITY
    assert family_freeze.record_digest(_stored()["body"]) == frozen["digest"]
    assert _stored()["body"]["tooling_commit"] == TOOLING_COMMIT


def test_it_builds_on_the_pre_registration_freeze_and_the_structural_identity() -> None:
    body = _stored()["body"]
    assert body["preregistration_freeze"]["identity"] == preregistration_freeze.load_freeze()["identity"] \
        == "v6-e8-prereg-v4-0166cdc0b37a"
    assert body["structural_matrix"] == {"identity": "v6-e8-matrix-v1-e0d322b597da",
                                         "digest": matrix.STRUCTURAL_DIGEST, "matches_per_condition": 4224,
                                         "matches_total": 16_896}
    assert body["implementation_commits"] == {"I8-1": ["3f3f709", "2cfd4e8"], "I8-2": ["e170895", "230fe71"],
                                              "I8-3": ["4b58d27", "621c95d"]}


def test_every_pinned_file_equals_its_content_at_the_tooling_commit() -> None:
    body = _stored()["body"]
    assert set(body["files"]) == set(family_freeze.PINNED_FILES)
    for path, digest in body["files"].items():
        assert _git_digest(body["tooling_commit"], path) == digest, path
    for path, entry in body["qualification"].items():
        assert _git_digest(body["tooling_commit"], path) == entry["sha256"], path


def test_every_package_equals_its_content_at_the_tooling_commit() -> None:
    body = _stored()["body"]
    assert len(body["packages"]) == 22
    for pid, entry in body["packages"].items():
        for name in ("agent.py", "agent.yaml"):
            path = f"tools/research/v6/e8/fixtures/agents/{pid}/{name}"
            assert _git_digest(body["tooling_commit"], path) == entry[name.replace(".", "_") + "_sha256"], path


def test_the_packages_mapping_and_one_policy_source() -> None:
    body = _stored()["body"]
    assert body["policy_source"] == {"sha256": ["369323136a4307198b2a734379ad5789fe3d19b29307329bda7016e9039cf8bc"],
                                     "packages": 22}
    assert {pid: (e["member"], e["role"]) for pid, e in body["packages"].items()} == dict(family.PACKAGES)
    assert body["packages"] == json.loads(family.FINGERPRINTS_PATH.read_text(encoding="utf-8"))


def test_the_parameter_table_declarations_and_sets() -> None:
    body = _stored()["body"]
    assert body["parameters"]["members"] == {m: dict(v) for m, v in family.MEMBERS.items()}
    for pid, values in body["parameters"]["resolved_from_manifests"].items():
        assert values == dict(family.MEMBERS[family.PACKAGES[pid][0]]), pid
    assert body["parameters"]["registered_encoding"] == [["reacquire", None, "none"], ["stress", None, False]]
    for pid, declared in body["declarations"].items():
        expected = [["sensor", 256, 0.25], ["striker", 256, 0.75]] if family.PACKAGES[pid][0] == "SPLIT8" \
            else [["main", 256, 1.0]]
        assert declared == expected, pid
    assert body["sets"] == {"pi": list(decision.PI), "pi_f": list(decision.PI_F),
                            "a8": ["RUSH8", "REACQ8", "PACED8", "STEALTH8", "LURK8"],
                            "phase_sensitive": ["PACED8", "EVADE8", "ADAPT8", "STRESS8"]}


def test_the_census_is_re_derived_from_both_roles_manifests() -> None:
    assert _stored()["body"]["census"] == {"primary": ["EVADE8"], "twin": ["EVADE8"], "prediction": ["EVADE8"]}
    assert list(family.census("primary")) == list(family.census("twin")) == ["EVADE8"]


def test_the_compatibility_classification_and_final_ruleset_identifiers() -> None:
    body = _stored()["body"]
    compat = body["compatibility"]
    assert set(compat["static_classes"]) == set(family.PACKAGES)
    assert set(compat["static_classes"].values()) == {"context-gated"}
    assert compat["d8_9_violations"] == {}
    assert compat["compatible_conditions"] == ["C8", "T8", "C8L", "T8L"]
    assert compat["accepted"]["ungated"] == sorted([compat["condition_rulesets"]["T8"],
                                                    compat["condition_rulesets"]["T8L"]])
    assert body["ruleset_identifiers"] == {
        "C8": {"ruleset_id": "bytefray-rules-6-research-sensing-r32", "registered_as_provisional": False},
        "T8": {"ruleset_id": "bytefray-rules-6-research-sensing-active-w27", "registered_as_provisional": True},
        "C8L": {"ruleset_id": "bytefray-rules-6-research-disruption-slot1-sensing-r32",
                "registered_as_provisional": False},
        "T8L": {"ruleset_id": "bytefray-rules-6-research-disruption-slot1-sensing-active-w27",
                "registered_as_provisional": True},
    }


def test_every_invariant_is_pinned_by_tests_that_exist() -> None:
    invariants = _stored()["body"]["invariants"]
    assert [i["id"] for i in invariants] == [*(f"RNG-{n}" for n in range(1, 6)), *(f"BEH-{n}" for n in range(1, 19)),
                                             *(f"ENG-{n}" for n in range(1, 5))]
    assert family_freeze.invariant_problems() == []
    assert all(i["pinned_by"] for i in invariants)


def test_a_missing_pinned_test_is_reported(monkeypatch: pytest.MonkeyPatch) -> None:
    planted = ({"id": "BEH-X", "source": "-", "statement": "-",
                "pinned_by": ["engine/tests/test_v6_e8_family.py::test_that_does_not_exist"]},)
    monkeypatch.setattr(family_freeze, "INVARIANTS", planted)
    assert family_freeze.invariant_problems() == [
        "BEH-X: no test test_that_does_not_exist in engine/tests/test_v6_e8_family.py"]


def test_the_qualification_evidence_and_its_counts() -> None:
    qualification = _stored()["body"]["qualification"]
    assert {path: (entry["phase"], entry["collected"]) for path, entry in qualification.items()} == {
        "engine/tests/test_v6_e8_parent_byte_identity.py": ("I8-1", 99),
        "engine/tests/_e8_sensing_harness.py": ("I8-2", None),
        "engine/tests/test_v6_e8_sensing_semantics.py": ("I8-2", 58),
        "engine/tests/test_ruleset_v6_research_sensing_active.py": ("I8-2", 68),
        "engine/tests/test_v6_e8_sensing_context.py": ("I8-2", 42),
        "engine/tests/_e8_family_harness.py": ("I8-3", None),
        "engine/tests/_e8_family_engine_harness.py": ("I8-3", None),
        "engine/tests/test_v6_e8_family.py": ("I8-3", 174),
        "engine/tests/test_v6_e8_family_policy.py": ("I8-3", 106),
        "engine/tests/test_v6_e8_family_engine.py": ("I8-3", 330),
        "engine/tests/test_v6_e8_adapt8_freeze.py": ("I8-3", 145),
        "engine/tests/test_v6_e8_family_fixed_details.py": ("I8-4", 27),
        "engine/tests/test_v6_e8_matrix.py": ("I8-4", 14),
    }


def test_the_implementation_notes() -> None:
    notes = {note["id"]: note for note in _stored()["body"]["implementation_notes"]}
    assert list(notes) == [f"N8-{n}" for n in range(1, 15)]
    assert notes["N8-8"]["text"] == (
        "P8-6's same-chunk rationale applies to whole-tick disruption but not universally to λ=1. "
        "Qualification establishes the intended same-tick result-delivery behavior under both parents, so no "
        "registered family behavior changes.")
    assert "defensive validation introduced by I8-2" in notes["N8-1"]["text"]
    assert "delivered to the agent through previous_sense_anchors" in notes["N8-6"]["text"]
    assert "lowest selected address a" in notes["N8-7"]["text"]


def test_no_seed_exists_and_nothing_was_played() -> None:
    body = _stored()["body"]
    assert body["exposure"] == {"seeds": "none exist", "matrix_cells": "none run",
                                "family_vs_family_matches": "none played"}
    assert "commitment" not in json.dumps(body)
    assert not list((ROOT / "tools" / "research" / "v6" / "e8").glob("seeds*"))


def test_a_tampered_record_fails_to_load(tmp_path: Path) -> None:
    changed = copy.deepcopy(_stored())
    changed["body"]["census"]["primary"] = ["EVADE8", "GUARD8"]
    path = tmp_path / "family_freeze.json"
    path.write_text(json.dumps(changed), encoding="utf-8")
    with pytest.raises(family_freeze.FreezeError, match="body digest"):
        family_freeze.load_freeze(path)


def test_a_re_signed_tampered_record_still_fails_to_load(tmp_path: Path) -> None:
    changed = copy.deepcopy(_stored())
    changed["body"]["sets"]["a8"] = ["RUSH8", "REACQ8", "PACED8", "STEALTH8"]
    changed["digest"] = family_freeze.record_digest(changed["body"])
    changed["identity"] = family_freeze.identity(changed["digest"])
    path = tmp_path / "family_freeze.json"
    path.write_text(json.dumps(changed), encoding="utf-8")
    with pytest.raises(family_freeze.FreezeError, match="sets"):
        family_freeze.load_freeze(path)


def test_a_drifted_package_fails_to_load(monkeypatch: pytest.MonkeyPatch) -> None:
    drifted = {pid: {**entry, "agent_yaml_sha256": "0" * 64} for pid, entry in family.fingerprints().items()}
    monkeypatch.setattr(family, "fingerprints", lambda: drifted)
    with pytest.raises(family_freeze.FreezeError):
        family_freeze.load_freeze()


def test_a_missing_record_fails_closed(tmp_path: Path) -> None:
    with pytest.raises(family_freeze.FreezeError, match="freeze the family first"):
        family_freeze.load_freeze(tmp_path / "absent.json")


def test_the_engine_source_check_detects_drift(monkeypatch: pytest.MonkeyPatch) -> None:
    # The engine is shared by later experiments, so the suite never pins the live tree to the record
    # (E6's convention); the E8 runner calls verify_engine_source before execution.
    live = family_freeze.engine_source()
    assert live["path"] == "engine/src" and live["files"] > 0
    record = {"body": {"engine_source": live}}
    family_freeze.verify_engine_source(record)
    monkeypatch.setattr(family_freeze, "engine_source", lambda: {**live, "sha256": "0" * 64})
    with pytest.raises(family_freeze.FreezeError, match="engine source"):
        family_freeze.verify_engine_source(record)
