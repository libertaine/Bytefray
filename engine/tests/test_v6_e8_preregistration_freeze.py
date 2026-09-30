"""V6 E8: the pre-registration freeze identity (phase I8-0), freeze v2.

The record pins, at the tooling commit, the markdown pre-registration
(revision 3), its transcription, the loader, the decision logic, their tests
and the implementation plan. It also pins the registered O-BOOT draws and the
predicted census. It recomputes from the live checkout, every pinned file
equals its content at the tooling commit, any drift fails closed, and no seed
exists. Freeze v1, which pinned revision 2, is kept byte for byte as
superseded before any exposure, and no longer loads.
"""

from __future__ import annotations

import copy
import hashlib
import json
import subprocess
from pathlib import Path

import pytest

from tools.research.v6.e8 import decision, preregistration, preregistration_freeze

ROOT = Path(__file__).resolve().parents[2]
IDENTITY = "v6-e8-prereg-v2-e478f519c070"
V1_IDENTITY = "v6-e8-prereg-v1-116c9ed83400"


def _stored() -> dict:
    return json.loads(preregistration_freeze.FREEZE_PATH.read_text(encoding="utf-8"))


def test_the_freeze_loads_and_its_identity_is_pinned() -> None:
    frozen = preregistration_freeze.load_freeze()
    assert frozen["identity"] == IDENTITY
    assert preregistration_freeze.identity(frozen["digest"]) == IDENTITY
    assert preregistration_freeze.record_digest(_stored()["body"]) == frozen["digest"]


def test_it_pins_revision_2_and_the_transcription() -> None:
    body = _stored()["body"]
    assert body["preregistration"]["revision"] == 3
    assert body["preregistration"]["registration_commit"] == "00fb420"
    assert body["preregistration"]["sha256"] == "a822bd15d9be8f968facb2f7b9c7e228d0e59b65ce34b790ae2a9e3538583a5a"
    assert [entry["commit"] for entry in body["preregistration"]["historical"]] == ["28925fd", "090d11e"]
    assert body["transcription"]["sha256"] == preregistration.PREREGISTRATION_SHA256
    assert body["files"]["tools/research/v6/e8/preregistration.json"] == preregistration.PREREGISTRATION_SHA256
    assert set(body["files"]) == set(preregistration_freeze.PINNED_FILES)


def test_every_pinned_file_equals_its_content_at_the_tooling_commit() -> None:
    body = _stored()["body"]
    for path, digest in body["files"].items():
        content = subprocess.run(["git", "show", f"{body['tooling_commit']}:{path}"], cwd=ROOT,
                                 capture_output=True, check=True).stdout
        assert hashlib.sha256(content.replace(b"\r\n", b"\n")).hexdigest() == digest, path


def test_the_registered_draws_and_census_are_pinned() -> None:
    body = _stored()["body"]
    assert body["registered_draws"] == {"resamples": 1000, "draws_per_resample": 32, "rng": "random.Random(42)",
                                        "sha256": preregistration_freeze.draws_digest()}
    assert body["census_prediction"] == ["EVADE8"] == list(decision.census())


def test_no_seed_exists() -> None:
    body = _stored()["body"]
    assert body["seeds"] == "none exist"
    assert "seed_commitment" not in body and "commitment" not in json.dumps(body)
    assert not list((ROOT / "tools" / "research" / "v6" / "e8").glob("seeds*"))


def test_a_tampered_record_fails_to_load(tmp_path: Path) -> None:
    stored = _stored()
    changed = copy.deepcopy(stored)
    changed["body"]["census_prediction"] = ["EVADE8", "GUARD8"]
    path = tmp_path / "freeze.json"
    path.write_text(json.dumps(changed), encoding="utf-8")
    with pytest.raises(preregistration_freeze.FreezeError, match="digest"):
        preregistration_freeze.load_freeze(path)
    changed = copy.deepcopy(stored)
    changed["identity"] = "v6-e8-prereg-v1-000000000000"
    path.write_text(json.dumps(changed), encoding="utf-8")
    with pytest.raises(preregistration_freeze.FreezeError, match="identity"):
        preregistration_freeze.load_freeze(path)


def test_a_changed_pinned_file_fails_to_load(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    real = preregistration.file_digest

    def drifted(path: Path) -> str:
        return "0" * 64 if path.name == "decision.py" else real(path)

    monkeypatch.setattr(preregistration, "file_digest", drifted)
    with pytest.raises(preregistration_freeze.FreezeError, match="files"):
        preregistration_freeze.load_freeze()


def test_the_loaded_freeze_is_immutable() -> None:
    frozen = preregistration_freeze.load_freeze()
    with pytest.raises(TypeError):
        frozen["body"]["census_prediction"] = ()  # type: ignore[index]
    assert isinstance(frozen["body"]["census_prediction"], tuple)


def test_v1_is_kept_byte_for_byte_superseded_and_no_longer_loads() -> None:
    body = _stored()["body"]
    assert body["supersedes"]["identity"] == V1_IDENTITY
    v1 = ROOT / body["supersedes"]["record"]
    assert preregistration.file_digest(v1) == body["supersedes"]["record_sha256"]
    committed = subprocess.run(["git", "show", f"7974e2a:{body['supersedes']['record']}"], cwd=ROOT,
                               capture_output=True, check=True).stdout
    assert preregistration.file_digest(v1) == hashlib.sha256(committed).hexdigest()
    assert json.loads(v1.read_text(encoding="utf-8"))["identity"] == V1_IDENTITY
    with pytest.raises(preregistration_freeze.FreezeError):
        preregistration_freeze.load_freeze(v1)


def test_a_missing_or_altered_v1_record_fails_to_load(monkeypatch: pytest.MonkeyPatch) -> None:
    real = preregistration.file_digest

    def drifted(path: Path) -> str:
        return "0" * 64 if path.name == "preregistration_freeze.json" else real(path)

    monkeypatch.setattr(preregistration, "file_digest", drifted)
    with pytest.raises(preregistration_freeze.FreezeError, match="superseded"):
        preregistration_freeze.load_freeze()
