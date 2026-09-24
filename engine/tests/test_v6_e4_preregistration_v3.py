"""E4 pre-registration v3 and analysis freeze v3 (O-INTERPRETATION-3).

Pre-registrations v1 and v2 and freezes v1 and v2 are preserved byte for byte
and still hold. The amendment changes only the interpretation reading: when H2
is SUPPORTED it takes precedence over the standalone "¬H1 ∧ H3" row, and when
H2 and H3 are both SUPPORTED the combined "H2 ∧ H3" statement is reported after
"H2". Freeze v3 pins freeze v2 and freeze v1 whole and requires every
measurement file to equal v1's pin and every v2 interpretation file v2's.
"""

from __future__ import annotations

import itertools
import json
import shutil
from pathlib import Path

import pytest

from tools.research.v6.e4 import (
    analysis_freeze,
    analysis_freeze_v2,
    analysis_freeze_v3,
    matrix,
    populations,
)
from tools.research.v6.e4 import preregistration as v1
from tools.research.v6.e4 import preregistration_v2 as v2
from tools.research.v6.e4 import preregistration_v3 as v3
from tools.research.v6.e4.analyze_e4 import (
    HOLDS,
    NEITHER,
    NOT_EVALUABLE,
    REFUTED,
    STOP,
    SUPPORTED,
    read_interpretation,
)

PREREG_V3 = v3.load_preregistration_v3()
V1_FREEZE_ID = "v6-e4-freeze-v1-101a941f5e30"
V2_FREEZE_ID = "v6-e4-freeze-v2-68d262a0dbd1"
# The committed v1 and v2 files, preserved byte for byte (SHA-256 with LF line endings).
V1_PREREGISTRATION_SHA256 = "56307844e1c01a52b46b3fc1d100a34706e13d6a645614d6d2bcea94757b9973"
V2_PREREGISTRATION_SHA256 = "d69680c400e6670ea1f5d1304e2c2930792aaa1e3279eaf17027b428595ccd9f"
V1_FREEZE_RECORD_SHA256 = "2c2018b1d755901e51b51dcae28e96899973ea94806d2900e71c8a0bc0cc4d91"
V2_FREEZE_RECORD_SHA256 = "8605aac091410ae011b536f3d67e04fe303ceb587a912a3e975cadb938080188"
V2_TOOLING_SOURCE_SHA = "516022950d660e17028e8d3f3864667b44257254"
V2_FREEZE_COMMIT = "94bc65b86574ee08a1a76133ff1450d7f6081234"

# The owner's amendment, verbatim (emphasis and code formatting removed).
COMBINED_TEXT = (
    "The treatment identifies two contest-class-specific signatures. In MULTI-PASS matchups, the privilege "
    "follows the final pre-sample chunk, supporting an evaluation-adjacency/final-position mechanism. In "
    "OPENING-ONLY matchups, last-side persistence remains, consistent with an opening-pass mechanism. H3 does "
    "not override H2 and does not close the in-tick order line globally. Evaluation structure is the registered "
    "next question for the MULTI-PASS effect; anchor/core-0 co-location remains a separate follow-up for the "
    "OPENING-ONLY residual."
)
RULES = (
    "If H2 is SUPPORTED, the H2 interpretation takes precedence over the standalone ¬H1 ∧ H3 interpretation.",
    f"If H2 and H3 are both SUPPORTED, report: “{COMBINED_TEXT}”",
    "Do not additionally emit the old standalone ¬H1 ∧ H3 conclusion.",
    ("No hypotheses, thresholds, populations, metrics, matrix, treatment semantics, or analyzer measurements "
     "change."),
)
COMBINED = "H2 ∧ H3"
OPENING = "¬H1 ∧ H3"
RULE_3_V2 = "¬H0 ∧ ¬H1 ∧ H3"
PATHOLOGY = "H5, H6, H8"


def _statuses(d9: str = HOLDS, **hypotheses: str) -> dict[str, str]:
    """Every hypothesis REFUTED (H7 NEITHER) unless overridden, e.g. ``H2=SUPPORTED``."""
    statuses = {f"E4-H{n}": REFUTED for n in range(9)} | {"E4-H7": NEITHER, "D9-PRIME": d9}
    statuses.update({f"E4-{name}": status for name, status in hypotheses.items()})
    return statuses


def _read(statuses: dict[str, str]) -> tuple[dict, dict]:
    return v2.read_interpretation_v2(statuses, PREREG_V3), v3.read_interpretation_v3(statuses, PREREG_V3)


def _head() -> str:
    return analysis_freeze.git_text("rev-parse", "HEAD")


def _global_null() -> dict[str, str]:
    pinned = analysis_freeze.load_freeze()["control_qualification"]["populations"]["sha256"]
    frozen = populations.load_record(populations.POPULATIONS_PATH, freeze_id=V1_FREEZE_ID, expected_sha256=pinned)
    inputs: dict[str, str] = frozen["arms"]["primary"]["control_vs_control_hypotheses"]["interpretation_inputs"]
    return inputs


# ---------------------------------------------------------------------------
# v1 and v2 are preserved; the amendment is pinned and changes no criterion
# ---------------------------------------------------------------------------


def test_v1_and_v2_are_preserved_byte_for_byte_and_their_freezes_still_hold() -> None:
    assert v1.preregistration_digest() == V1_PREREGISTRATION_SHA256
    assert v2.preregistration_v2_digest() == v2.PREREGISTRATION_V2_SHA256 == V2_PREREGISTRATION_SHA256
    assert analysis_freeze.file_sha256(analysis_freeze_v3.ROOT_FREEZE_FILE) == V1_FREEZE_RECORD_SHA256
    assert analysis_freeze.file_sha256(analysis_freeze_v3.BASE_FREEZE_FILE) == V2_FREEZE_RECORD_SHA256
    assert analysis_freeze.load_freeze()["freeze_id"] == V1_FREEZE_ID
    assert analysis_freeze_v2.load_freeze_v2()["freeze_id"] == V2_FREEZE_ID
    prereg_v2 = v2.load_preregistration_v2()
    assert (PREREG_V3["v1"], PREREG_V3["amendment"]) == (prereg_v2["v1"], prereg_v2["amendment"])


def test_the_amendment_carries_the_owner_text_verbatim_and_names_v2_and_v1() -> None:
    amendment = PREREG_V3["amendment_v3"]
    assert (amendment["id"], amendment["title"]) == ("O-INTERPRETATION-3",
                                                     "H2 precedence / combined H2+H3 interpretation")
    assert tuple(rule["text"] for rule in amendment["rules"]) == RULES
    assert amendment["issue"].startswith("The issue is not that H2 ∧ ¬H1 ∧ H3 is ambiguous.")
    assert amendment["issue"].endswith("We shouldn't allow both conclusions to stand side by side.")
    amends = amendment["amends"]
    assert (amends["preregistration_v2"]["sha256"], amends["preregistration"]["sha256"]) == (
        V2_PREREGISTRATION_SHA256, V1_PREREGISTRATION_SHA256)
    assert amends["analysis_freeze"]["freeze_id"] == V2_FREEZE_ID
    reading = amendment["reading"]
    assert reading["amended_row"] == OPENING
    assert reading["precedence"] == {"requires": {"E4-H2": SUPPORTED}, "row": "H2"}
    assert reading["combined"] == {"requires": {"E4-H2": SUPPORTED, "E4-H3": SUPPORTED}, "after": "H2",
                                   "outcome": {"result": COMBINED, "conclusion": COMBINED_TEXT}}


def test_the_amendment_changes_no_hypothesis_criterion_row_or_population() -> None:
    amendment, prereg = PREREG_V3["amendment_v3"], PREREG_V3["v1"]
    assert set(amendment) & set(prereg) == {"schema", "schema_version", "status", "authority"}
    assert "O-INTERPRETATION-3" not in {item["id"] for item in prereg["operationalizations"]}
    assert COMBINED not in {row["result"] for row in prereg["interpretation"]} | {RULE_3_V2}


def test_a_changed_amendment_fails_closed(tmp_path: Path) -> None:
    path = tmp_path / "preregistration_v3.json"
    shutil.copyfile(v3.PREREGISTRATION_V3_PATH, path)
    assert v3.load_preregistration_v3(path)["amendment_v3"]["id"] == "O-INTERPRETATION-3"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["reading"]["combined"]["requires"] = {"E4-H2": SUPPORTED}
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    with pytest.raises(v1.PreregistrationError, match="the amendment changed"):
        v3.load_preregistration_v3(path)


def test_a_changed_v2_or_v1_fails_the_v3_load(monkeypatch: pytest.MonkeyPatch) -> None:
    with monkeypatch.context() as patch:
        patch.setattr(v2, "PREREGISTRATION_V2_SHA256", "0" * 64)
        with pytest.raises(v1.PreregistrationError, match="pre-registration v2 digest"):
            v3.load_preregistration_v3()
    monkeypatch.setattr(v1, "PREREGISTRATION_SHA256", "0" * 64)
    with pytest.raises(v1.PreregistrationError, match="the pre-registration changed"):
        v3.load_preregistration_v3()


def test_an_amendment_inconsistent_with_v2_fails_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = tmp_path / "preregistration_v3.json"
    data = json.loads(v3.PREREGISTRATION_V3_PATH.read_text(encoding="utf-8"))
    data["amends"]["preregistration_v2"]["sha256"] = "0" * 64
    data["reading"]["combined"]["after"] = "H0"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    monkeypatch.setattr(v3, "PREREGISTRATION_V3_SHA256", v3.preregistration_v3_digest(path))
    with pytest.raises(v1.PreregistrationError, match="does not amend the frozen.*not anchored"):
        v3.load_preregistration_v3(path)


# ---------------------------------------------------------------------------
# The O-INTERPRETATION-3 reading
# ---------------------------------------------------------------------------


def test_h2_takes_precedence_and_the_combined_statement_is_reported() -> None:
    """The observation v3 closes: "¬H1 ∧ H3" beside "H2" (H0 and H1 refuted)."""
    older, new = _read(_statuses(H2=SUPPORTED, H3=SUPPORTED))
    assert older["v1_reading"]["applies"] == older["applies"] == ["H2", OPENING]
    assert (new["applies"], new["actions"], new["withheld"]) == (["H2", COMBINED], ["precedence", "combined"],
                                                                 [OPENING])
    assert new["conclusions"][1] == {"result": COMBINED, "conclusion": COMBINED_TEXT}
    assert new["conclusions"][0]["conclusion"].startswith("The privilege follows the final pre-sample chunk.")
    assert new["v2_reading"] == older


def test_the_combined_statement_needs_only_h2_and_h3() -> None:
    older, new = _read(_statuses(H1=NEITHER, H2=SUPPORTED, H3=SUPPORTED))
    assert older["applies"] == ["H2"]
    assert (new["applies"], new["actions"], new["withheld"]) == (["H2", COMBINED], ["combined"], [])


@pytest.mark.parametrize("h3", [REFUTED, NEITHER])
def test_h2_without_h3_is_unchanged(h3: str) -> None:
    older, new = _read(_statuses(H2=SUPPORTED, H3=h3))
    assert older["applies"] == new["applies"] == ["H2"]
    assert (new["actions"], new["withheld"]) == ([], [])


def test_the_pathology_row_is_kept() -> None:
    older, new = _read(_statuses(H2=SUPPORTED, H3=SUPPORTED, H8=SUPPORTED))
    assert older["applies"] == ["H2", OPENING, PATHOLOGY]
    assert new["applies"] == ["H2", COMBINED, PATHOLOGY]


def test_the_v2_readings_stand_where_h2_is_not_supported() -> None:
    # The frozen global null (v2 rule 1), v2 rule 3, and the two-mechanism row.
    for statuses in (_global_null(), _statuses(H3=SUPPORTED), _statuses(H1=SUPPORTED, H3=SUPPORTED)):
        older, new = _read(statuses)
        assert new["applies"] == older["applies"] and new["actions"] == []
        assert new["notes"] == older["notes"]
    assert _read(_global_null())[1]["applies"] == ["H0"]
    assert _read(_statuses(H3=SUPPORTED))[1]["applies"] == [RULE_3_V2]


def test_a_d9_stop_still_replaces_the_reading() -> None:
    older, new = _read(_statuses(d9=STOP, H2=SUPPORTED, H3=SUPPORTED))
    assert older["applies"] == new["applies"] == [] and new["stop"] == older["stop"] is not None
    assert new["actions"] == []


@pytest.mark.parametrize("h0", [NEITHER, NOT_EVALUABLE])
def test_an_h0_status_the_definition_cannot_produce_still_fails_closed(h0: str) -> None:
    with pytest.raises(v2.InterpretationError, match="SUPPORTED or REFUTED"):
        v3.read_interpretation_v3(_statuses(H0=h0, H2=SUPPORTED, H3=SUPPORTED), PREREG_V3)


def test_v3_differs_from_v2_only_by_the_precedence_and_the_combined_outcome() -> None:
    """Every status combination of H0-H3 and a pathology: the standalone "¬H1 ∧ H3"
    conclusion is never reported, and v3 changes v2's reading only where H2 is SUPPORTED."""
    states = (SUPPORTED, REFUTED, NEITHER, NOT_EVALUABLE)
    for h0, h1, h2, h3, h5 in itertools.product(states, states, states, states, (SUPPORTED, REFUTED)):
        statuses = _statuses(H0=h0, H1=h1, H2=h2, H3=h3, H5=h5)
        try:
            older = v2.read_interpretation_v2(statuses, PREREG_V3)
        except v2.InterpretationError:
            with pytest.raises(v2.InterpretationError):
                v3.read_interpretation_v3(statuses, PREREG_V3)
            continue
        new = v3.read_interpretation_v3(statuses, PREREG_V3)
        expected = list(older["applies"])
        if h2 == SUPPORTED:
            expected = [row for row in expected if row != OPENING]
            if h3 == SUPPORTED:
                expected.insert(expected.index("H2") + 1, COMBINED)
        assert new["applies"] == expected, statuses
        assert OPENING not in new["applies"], statuses
        assert new["v2_reading"] == older


# ---------------------------------------------------------------------------
# Analysis freeze v3
# ---------------------------------------------------------------------------


def _identity() -> dict:
    return analysis_freeze_v3.identity_inputs(
        tooling_source_sha=_head(), match_generation_tree=analysis_freeze.git_text("rev-parse", "HEAD:engine/src"))


def _write(path: Path, identity: dict) -> Path:
    path.write_text(json.dumps(analysis_freeze_v3.build_freeze_record(identity), indent=2, sort_keys=True),
                    encoding="utf-8")
    return path


def test_the_v3_identity_pins_freezes_v2_and_v1_and_the_amendments() -> None:
    identity = _identity()
    base, root = analysis_freeze_v2.load_freeze_v2(), analysis_freeze.load_freeze()
    assert identity["base_freeze"] == {"freeze_id": V2_FREEZE_ID, "freeze_digest": base["freeze_digest"],
                                       "path": analysis_freeze_v3.BASE_FREEZE_FILE, "sha256": V2_FREEZE_RECORD_SHA256}
    assert identity["root_freeze"] == {"freeze_id": V1_FREEZE_ID, "freeze_digest": root["freeze_digest"],
                                       "path": analysis_freeze_v3.ROOT_FREEZE_FILE, "sha256": V1_FREEZE_RECORD_SHA256}
    assert identity["measurement_tooling_sha256"] == root["identity"]["tooling_sha256"]
    assert identity["prior_interpretation_tooling_sha256"] == base["identity"]["interpretation_tooling_sha256"]
    assert identity["match_generation_tree"] == root["identity"]["match_generation_tree"]
    assert (identity["preregistration_sha256"], identity["preregistration_v2_sha256"],
            identity["preregistration_v3_sha256"]) == (V1_PREREGISTRATION_SHA256, V2_PREREGISTRATION_SHA256,
                                                       v3.PREREGISTRATION_V3_SHA256)
    assert (identity["matrix_id"], identity["matches_total"]) == ("v6-e4-matrix-v1-fc29d575dd25", 15232)
    assert set(identity["interpretation_tooling_sha256"]) == set(analysis_freeze_v3.INTERPRETATION_FILES)
    assert not set(analysis_freeze_v3.INTERPRETATION_FILES) & (
        set(analysis_freeze.TOOLING_FILES) | set(analysis_freeze_v2.INTERPRETATION_FILES))
    record = analysis_freeze_v3.build_freeze_record(identity)
    assert record["freeze_id"].startswith("v6-e4-freeze-v3-")
    assert record["freeze_id"] not in (V1_FREEZE_ID, V2_FREEZE_ID)
    assert record["control_qualification"]["from"] == V1_FREEZE_ID


def test_a_v3_record_loads_and_v3_interpretation_drift_fails_closed(tmp_path: Path,
                                                                    monkeypatch: pytest.MonkeyPatch) -> None:
    path = _write(tmp_path / "analysis_freeze_v3.json", _identity())
    assert analysis_freeze_v3.load_freeze_v3(path)["freeze_id"].startswith("v6-e4-freeze-v3-")
    real = analysis_freeze_v3.file_sha256

    def drifted(relative: str, *args: object) -> str:
        return "0" * 64 if relative == "tools/research/v6/e4/preregistration_v3.py" else real(relative)

    monkeypatch.setattr(analysis_freeze_v3, "file_sha256", drifted)
    with pytest.raises(analysis_freeze.AnalysisFreezeError, match="interpretation_tooling_sha256"):
        analysis_freeze_v3.load_freeze_v3(path)


def test_v2_interpretation_drift_fails_freeze_v2_and_so_freeze_v3(tmp_path: Path,
                                                                 monkeypatch: pytest.MonkeyPatch) -> None:
    path = _write(tmp_path / "analysis_freeze_v3.json", _identity())
    real = analysis_freeze_v2.file_sha256

    def drifted(relative: str, *args: object) -> str:
        return "0" * 64 if relative == "tools/research/v6/e4/preregistration_v2.py" else real(relative)

    monkeypatch.setattr(analysis_freeze_v2, "file_sha256", drifted)
    with pytest.raises(analysis_freeze.AnalysisFreezeError, match="freeze v2 does not hold"):
        analysis_freeze_v3.load_freeze_v3(path)


def test_measurement_drift_fails_freeze_v1_and_so_freeze_v3(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = _write(tmp_path / "analysis_freeze_v3.json", _identity())
    real = analysis_freeze.file_sha256

    def drifted(relative: str, *args: object) -> str:
        return "0" * 64 if relative == analysis_freeze.ANALYSIS_FILE else real(relative)

    monkeypatch.setattr(analysis_freeze, "file_sha256", drifted)
    with pytest.raises(analysis_freeze.AnalysisFreezeError, match="analyze_e4|e4_analysis_sha256"):
        analysis_freeze_v3.load_freeze_v3(path)


@pytest.mark.parametrize("changed_file", [analysis_freeze_v3.BASE_FREEZE_FILE, analysis_freeze_v3.ROOT_FREEZE_FILE])
def test_a_changed_v2_or_v1_record_fails_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
                                                changed_file: str) -> None:
    path = _write(tmp_path / "analysis_freeze_v3.json", _identity())
    real = analysis_freeze_v3.file_sha256

    def changed(relative: str, *args: object) -> str:
        return "0" * 64 if relative == changed_file else real(relative)

    monkeypatch.setattr(analysis_freeze_v3, "file_sha256", changed)
    with pytest.raises(analysis_freeze.AnalysisFreezeError, match="base_freeze|root_freeze"):
        analysis_freeze_v3.load_freeze_v3(path)


def test_a_tampered_v3_record_fails_closed(tmp_path: Path) -> None:
    path = _write(tmp_path / "analysis_freeze_v3.json", _identity())
    record = json.loads(path.read_text(encoding="utf-8"))
    record["identity"]["preregistration_v3_sha256"] = "0" * 64
    path.write_text(json.dumps(record), encoding="utf-8")
    with pytest.raises(analysis_freeze.AnalysisFreezeError, match="digest or id"):
        analysis_freeze_v3.load_freeze_v3(path)


@pytest.mark.parametrize(("key", "path", "message"), [
    ("measurement_tooling_sha256", analysis_freeze.ANALYSIS_FILE, "differs from freeze v1's pins"),
    ("prior_interpretation_tooling_sha256", "tools/research/v6/e4/preregistration_v2.py",
     "differ from freeze v2's pins"),
])
def test_pins_that_differ_from_v1_or_v2_fail_closed_even_if_self_consistent(tmp_path: Path, key: str, path: str,
                                                                           message: str) -> None:
    identity = _identity()
    identity[key] = {**identity[key], path: "0" * 64}
    record_path = _write(tmp_path / "analysis_freeze_v3.json", identity)
    with pytest.raises(analysis_freeze.AnalysisFreezeError, match=message):
        analysis_freeze_v3.load_freeze_v3(record_path)


def test_the_execution_source_check_covers_the_v3_interpretation_files(monkeypatch: pytest.MonkeyPatch) -> None:
    # Freeze v2's own check (and v1's inside it) is covered by their tests; isolate v3's.
    monkeypatch.setattr(analysis_freeze_v2, "verify_execution_source_v2", lambda record: None)
    identity = _identity()
    identity["interpretation_tooling_sha256"] = {**identity["interpretation_tooling_sha256"],
                                                 "tools/research/v6/e4/preregistration_v3.json": "0" * 64}
    with pytest.raises(analysis_freeze.AnalysisFreezeError, match="freeze v3 execution source check failed"):
        analysis_freeze_v3.verify_execution_source_v3(analysis_freeze_v3.build_freeze_record(identity))


# ---------------------------------------------------------------------------
# The committed freeze v3
# ---------------------------------------------------------------------------

FREEZE_V3_ID = "v6-e4-freeze-v3-80f21d822542"
V3_TOOLING_SOURCE_SHA = "a5857f9cc36bfea92ca95bf5dd5133727c39a865"
ENGINE_TREE = "940a27bcf8c62268eb15210cc30c28cae4d33e50"


def test_the_committed_v3_freeze_holds(monkeypatch: pytest.MonkeyPatch) -> None:
    record = analysis_freeze_v3.load_freeze_v3()
    assert record["freeze_id"] == FREEZE_V3_ID
    assert record["status"] == "frozen before any T-E4 or T-E4K1 matrix data exists"
    identity = record["identity"]
    assert (identity["tooling_source_sha"], identity["match_generation_tree"]) == (V3_TOOLING_SOURCE_SHA, ENGINE_TREE)
    assert (identity["base_freeze"]["freeze_id"], identity["base_freeze"]["sha256"]) == (V2_FREEZE_ID,
                                                                                         V2_FREEZE_RECORD_SHA256)
    assert (identity["root_freeze"]["freeze_id"], identity["root_freeze"]["sha256"]) == (V1_FREEZE_ID,
                                                                                         V1_FREEZE_RECORD_SHA256)
    assert identity["preregistration_v3_sha256"] == v3.PREREGISTRATION_V3_SHA256
    assert record["control_qualification"]["from"] == V1_FREEZE_ID
    # The v3 interpretation files equal their content at the tooling commit (v2's and v1's checks isolated).
    monkeypatch.setattr(analysis_freeze_v2, "verify_execution_source_v2", lambda record: None)
    analysis_freeze_v3.verify_execution_source_v3(record)


def test_only_commits_holding_the_v3_record_count_as_generated_under_freeze_v3() -> None:
    assert analysis_freeze_v3.held_at(V2_FREEZE_COMMIT) is False
    assert analysis_freeze_v3.held_at(V3_TOOLING_SOURCE_SHA) is False
    assert analysis_freeze_v3.held_at(_head()) is True


def _run_root(tmp_path: Path, inputs: dict[str, str], *, git_sha: str, git_dirty: bool = False,
              measured_under: str = V1_FREEZE_ID) -> Path:
    """A synthetic run root: treatment provenance for every field and a v1 analysis record."""
    from tools.research.v6.e4 import run_e4

    provenance = {"git_sha": git_sha, "git_dirty": git_dirty}
    for condition_id in matrix.TREATMENT_CONDITIONS:
        for field_id in matrix.FIELD_IDS:
            path = run_e4.condition_root(tmp_path, condition_id, field_id) / "provenance.json"
            path.parent.mkdir(parents=True)
            path.write_text(json.dumps({**provenance, "e4_freeze_id": measured_under}), encoding="utf-8")
    analysis = {"freeze_id": V1_FREEZE_ID, "matrix_id": matrix.matrix_id(), "e4_analysis_version": 1,
                "preregistration_sha256": V1_PREREGISTRATION_SHA256, "provenance": provenance,
                "result": {"interpretation_inputs": inputs,
                           "interpretation": read_interpretation(inputs, PREREG_V3["v1"])}}
    path = run_e4.freeze_root(tmp_path, V1_FREEZE_ID) / run_e4.ANALYSIS_RECORD_NAME
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(analysis, ensure_ascii=False), encoding="utf-8")
    return tmp_path


@pytest.mark.parametrize(("case", "expected"), [
    ("global_null", ["H0"]),
    ("h2_and_h3", ["H2", COMBINED]),
])
def test_interpret_reads_the_v1_analysis_under_freeze_v3(tmp_path: Path, case: str, expected: list[str]) -> None:
    from tools.research.v6.e4 import run_e4

    inputs = _global_null() if case == "global_null" else _statuses(H2=SUPPORTED, H3=SUPPORTED)
    root = _run_root(tmp_path, inputs, git_sha=_head())
    record = analysis_freeze_v3.interpret(run_root=root)
    assert (record["freeze_id"], record["base_freeze_id"], record["measurement_freeze_id"]) == (
        FREEZE_V3_ID, V2_FREEZE_ID, V1_FREEZE_ID)
    assert record["reading"]["applies"] == expected
    assert record["reading"]["v2_reading"] == v2.read_interpretation_v2(inputs, PREREG_V3)
    written = run_e4.freeze_root(root, FREEZE_V3_ID) / analysis_freeze_v3.INTERPRETATION_RECORD_NAME
    assert json.loads(written.read_text(encoding="utf-8"))["reading"] == record["reading"]


@pytest.mark.parametrize(("kwargs", "message"), [
    ({"git_sha": V2_FREEZE_COMMIT}, "commit holding freeze v3"),
    ({"git_sha": V3_TOOLING_SOURCE_SHA}, "commit holding freeze v3"),
    ({"git_sha": "HEAD", "git_dirty": True}, "clean tree"),
    ({"git_sha": "HEAD", "measured_under": V2_FREEZE_ID}, "ran under"),
])
def test_interpret_refuses_data_not_produced_under_freeze_v3(tmp_path: Path, kwargs: dict, message: str) -> None:
    if kwargs["git_sha"] == "HEAD":
        kwargs = {**kwargs, "git_sha": _head()}
    with pytest.raises(analysis_freeze.AnalysisFreezeError, match=message):
        analysis_freeze_v3.interpret(run_root=_run_root(tmp_path, _global_null(), **kwargs))


def test_interpret_refuses_an_analysis_whose_v1_reading_does_not_recompute(tmp_path: Path) -> None:
    from tools.research.v6.e4 import run_e4

    root = _run_root(tmp_path, _global_null(), git_sha=_head())
    path = run_e4.freeze_root(root, V1_FREEZE_ID) / run_e4.ANALYSIS_RECORD_NAME
    analysis = json.loads(path.read_text(encoding="utf-8"))
    analysis["result"]["interpretation"] = {"applies": ["H0"], "stop": None}
    path.write_text(json.dumps(analysis, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(analysis_freeze.AnalysisFreezeError, match="does not recompute"):
        analysis_freeze_v3.interpret(run_root=root)
