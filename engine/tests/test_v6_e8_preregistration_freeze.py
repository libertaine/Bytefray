"""V6 E8: the pre-registration freeze identity (phase I8-0), freeze v3.

The record pins, at the tooling commit, the markdown pre-registration
(revision 4), its transcription, the loader, the decision logic, their tests
and the implementation plan. It also pins the registered O-BOOT draws and the
predicted census. It recomputes from the live checkout, every pinned file
equals its content at the tooling commit, any drift fails closed, and no seed
exists. Freezes v2 and v1, which pinned revisions 3 and 2, are kept byte for
byte as superseded before any exposure, and neither loads.
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
IDENTITY = "v6-e8-prereg-v3-4058c890e992"
# Each superseded freeze: its identity, its record, and the commit that wrote the record.
SUPERSEDED = (("v6-e8-prereg-v2-e478f519c070", "tools/research/v6/e8/preregistration_freeze_v2.json", "63ecff6"),
              ("v6-e8-prereg-v1-116c9ed83400", "tools/research/v6/e8/preregistration_freeze.json", "7974e2a"))


def _stored() -> dict:
    return json.loads(preregistration_freeze.FREEZE_PATH.read_text(encoding="utf-8"))


def test_the_freeze_loads_and_its_identity_is_pinned() -> None:
    frozen = preregistration_freeze.load_freeze()
    assert frozen["identity"] == IDENTITY
    assert preregistration_freeze.identity(frozen["digest"]) == IDENTITY
    assert preregistration_freeze.record_digest(_stored()["body"]) == frozen["digest"]


def test_it_pins_revision_4_and_the_transcription() -> None:
    body = _stored()["body"]
    assert body["preregistration"]["revision"] == 4
    assert body["preregistration"]["registration_commit"] == "ae37cf9"
    assert body["preregistration"]["sha256"] == "8a9971a0630f85291e41034a07940cdf915e97cde4c87fb133dcb6bca8ae63fa"
    assert [entry["commit"] for entry in body["preregistration"]["historical"]] == ["28925fd", "090d11e", "00fb420"]
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
    changed["identity"] = "v6-e8-prereg-v2-000000000000"
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


def test_the_superseded_freezes_are_named_in_order() -> None:
    body = _stored()["body"]
    assert [(entry["identity"], entry["record"]) for entry in body["supersedes"]] == [
        (identity, record) for identity, record, _ in SUPERSEDED]
    assert body["supersedes"] == [dict(entry) for entry in preregistration_freeze.SUPERSEDED]


@pytest.mark.parametrize(("superseded_identity", "record", "written_at"), SUPERSEDED)
def test_each_superseded_freeze_is_kept_byte_for_byte_and_no_longer_loads(
        superseded_identity: str, record: str, written_at: str) -> None:
    entry = next(e for e in _stored()["body"]["supersedes"] if e["identity"] == superseded_identity)
    kept = ROOT / record
    assert preregistration.file_digest(kept) == entry["record_sha256"]
    committed = subprocess.run(["git", "show", f"{written_at}:{record}"], cwd=ROOT,
                               capture_output=True, check=True).stdout
    assert preregistration.file_digest(kept) == hashlib.sha256(committed).hexdigest()
    stored = json.loads(kept.read_text(encoding="utf-8"))
    assert stored["identity"] == superseded_identity and stored["digest"] == entry["digest"]
    with pytest.raises(preregistration_freeze.FreezeError):
        preregistration_freeze.load_freeze(kept)


@pytest.mark.parametrize("record", [record for _, record, _ in SUPERSEDED])
def test_a_missing_or_altered_superseded_record_fails_to_load(record: str, monkeypatch: pytest.MonkeyPatch) -> None:
    real = preregistration.file_digest

    def drifted(path: Path) -> str:
        return "0" * 64 if path.name == Path(record).name else real(path)

    monkeypatch.setattr(preregistration, "file_digest", drifted)
    with pytest.raises(preregistration_freeze.FreezeError, match="superseded"):
        preregistration_freeze.load_freeze()
