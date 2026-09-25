"""V6 E6: the structural matrix identity and the pre-registration transcription.

Implementation plan Sec 2 (I-6) and Sec 7.1; pre-registration Sec 3 and 9.
The structural identity is frozen before any seed exists and names no seed
value. The transcription (``preregistration.json``) must equal the analysis
code, value by value, and its key terms must appear in the markdown
pre-registration.
"""

from __future__ import annotations

import copy
import json
import re
from pathlib import Path
from typing import Any

import pytest

from tools.research.v6.e6 import family, interpretation, matrix, preregistration, seeds

PR_PATH = Path(__file__).resolve().parents[2] / "docs" / "research" / "v6" / "V6_E6_PRICED_SENSING_PREREGISTRATION.md"


def test_the_structural_identity_is_pinned_and_recomputes() -> None:
    assert matrix.structural_digest() == matrix.STRUCTURAL_DIGEST
    assert matrix.matrix_id() == f"v6-e6-matrix-v2-{matrix.STRUCTURAL_DIGEST[:12]}" == "v6-e6-matrix-v2-7de29a4a6954"
    matrix.verify_frozen_matrix()


def test_structural_matrix_v1_is_superseded_not_reused() -> None:
    # Amendment 1 changed only the family policy: v2 differs from v1 in the
    # package fingerprints (and its version), and in nothing else.
    v1 = matrix.SUPERSEDED_STRUCTURAL_MATRIX
    assert v1 == {"id": "v6-e6-matrix-v1-cd040eac42ef",
                  "digest": "cd040eac42ef6554f3d6c0faf4a7fbe83dd963d416cfad8e7f9c4aa8630f13a6"}
    assert v1["digest"] != matrix.STRUCTURAL_DIGEST and v1["id"] != matrix.matrix_id()
    definition = matrix.structural_definition()
    assert definition["matrix_version"] == 2
    assert {record["agent_py_sha256"] for record in definition["package_fingerprints"].values()} == {
        "5374092e8c419a01071782cf5383ea481f8d62097acab8adb7064dad20ff3b63"}


def test_the_structure_names_no_seed_value() -> None:
    definition = matrix.structural_definition()
    assert definition["seed_count"] == 32
    assert "seeds" not in definition
    text = json.dumps(definition)
    assert not re.search(r'"seeds?"\s*:\s*\[', text)


def test_counts_fields_and_conditions() -> None:
    assert (matrix.F1.expected_matches, matrix.F2.expected_matches) == (2304, 576)
    assert matrix.matches_per_condition() == 2880 and matrix.matches_total() == 11_520
    assert len(matrix.F1.pairs) == 36 and matrix.F1.pairing == "triangular"
    assert matrix.F1.agents == tuple(family.package_id(m) for m in family.OPPONENTS)
    assert matrix.F2.pairs == tuple((family.package_id(m), family.package_id(m, "twin")) for m in family.OPPONENTS)
    assert [(c.condition_id, c.parent, c.detection_radius, c.disruption_slot_limit) for c in matrix.CONDITIONS] == [
        ("C-E6", None, None, None), ("T-E6", "C-E6", 32, None), ("C-E6L", None, None, 1), ("T-E6L", "C-E6L", 32, 1)]
    assert matrix.ARMS == {"primary": ("C-E6", "T-E6"), "companion": ("C-E6L", "T-E6L")}
    assert matrix.PARENT_FREEZE == {"commit": "ddf0eda", "path": "engine/tests/test_v6_e6_parent_byte_identity.py",
                                    "matches": 84}


def test_the_structure_binds_the_family(monkeypatch: pytest.MonkeyPatch) -> None:
    assert matrix.structural_definition()["package_fingerprints"] == family.fingerprints()
    drifted = {pid: {**entry, "agent_py_sha256": "0" * 64} for pid, entry in family.fingerprints().items()}
    monkeypatch.setattr(family, "fingerprints", lambda: drifted)
    assert matrix.structural_digest() != matrix.STRUCTURAL_DIGEST
    with pytest.raises(matrix.MatrixDefinitionError):
        matrix.verify_frozen_matrix()


def test_the_execution_identity_binds_the_structure_to_a_commitment() -> None:
    commitment = "c" * 64
    assert matrix.execution_identity(commitment) == seeds.execution_identity(matrix.STRUCTURAL_DIGEST, commitment)
    assert matrix.execution_identity(commitment) != matrix.execution_identity("d" * 64)


# ---------------------------------------------------------------------------
# The pre-registration transcription
# ---------------------------------------------------------------------------


def _data() -> dict[str, Any]:
    return json.loads(preregistration.PREREGISTRATION_PATH.read_text(encoding="utf-8"))


def test_the_transcription_loads_and_is_pinned() -> None:
    data = preregistration.load_preregistration()
    assert preregistration.preregistration_digest() == preregistration.PREREGISTRATION_SHA256
    assert data["authority"]["document"] == "docs/research/v6/V6_E6_PRICED_SENSING_PREREGISTRATION.md"
    assert preregistration.consistency_problems(data) == []


@pytest.mark.parametrize(("path", "value"), [
    (("thresholds", "epsilon"), "1/8"),
    (("thresholds", "stability"), "8/10"),
    (("thresholds", "h0_refute"), "3/4"),
    (("thresholds", "forced_line_tick"), 4),
    (("operationalizations", "O-BOOT", "resamples"), 999),
    (("operationalizations", "O-CONTRAST", "L"), [["LURK", "RUSH"]]),
    (("population", "fixed_set_pi_f"), ["RUSH"]),
    (("hypotheses", "E6-H3", "defenders"), ["GUARD"]),
    (("gates", "CQ-1", "members"), ["RUSH", "PACED"]),
    (("fields", "cells_total"), 11519),
])
def test_any_drift_between_transcription_and_code_is_reported(path: tuple[str, ...], value: Any) -> None:
    data = copy.deepcopy(_data())
    target = data
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    assert preregistration.consistency_problems(data)


def test_a_changed_row_is_reported() -> None:
    data = copy.deepcopy(_data())
    data["interpretation"]["rows"][1]["combinations"].append(["SUPPORTED", "NEITHER"])
    assert any("R-CREATES" in problem for problem in preregistration.consistency_problems(data))


def test_a_changed_file_fails_to_load(tmp_path: Path) -> None:
    changed = tmp_path / "preregistration.json"
    changed.write_text(preregistration.PREREGISTRATION_PATH.read_text(encoding="utf-8").replace('"1/16"', '"1/8"'),
                       encoding="utf-8")
    with pytest.raises(preregistration.PreregistrationError):
        preregistration.load_preregistration(changed)


def test_the_markdown_carries_the_transcribed_terms() -> None:
    text = PR_PATH.read_text(encoding="utf-8")
    for row in interpretation.ROWS:
        assert f"| **{row.row_id}** | {row.e6d} |" in text, row.row_id
    for kc in interpretation.KILL_CRITERIA:
        assert f"| **{kc}**" in text
    for clause in (f"D-{n}" for n in range(1, 8)):
        assert f"| **{clause}**" in text
    for term in ("**1/16**", "**1000** resamples", "`random.Random(42)`", "**≤ 3**", "**32**", "9/10", "2/3",
                 "1/10", "{ (LURK, RUSH), (PACED, RUSH) }", "`bytefray-rules-6-research-sensing-r32`",
                 "`bytefray-rules-6-research-disruption-slot1-sensing-r32`", "`secrets.randbelow(2**53)`",
                 "`v6-e6-matrix-v1-<first 12 hex of the structural digest>`", "`v6-e6-exec-v1-<first 12 hex of X>`"):
        assert term in text, term
    for member in family.OPPONENTS:
        assert f"| **{member}**" in text, member
