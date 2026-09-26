"""E4 pre-registration v2 and analysis freeze v2 (finding P-1, O-INTERPRETATION-2).

Pre-registration v1 and freeze v1 are preserved byte for byte and still hold.
The amendment changes only the interpretation reading. Rule 1 lets "H0" take
precedence over "¬H1 ∧ H3"; rule 2 leaves "H1 ∧ H3 ∧ ¬H2" alone; rule 3
replaces "¬H1 ∧ H3" by the no-causal-interpretation outcome when H0 is refuted
and no other main row applies. Freeze v2 pins freeze v1 whole and requires
every measurement file to equal v1's pin.
"""

from __future__ import annotations

import itertools
import json
import shutil
from pathlib import Path

import pytest

from tools.research.v6.e4 import analysis_freeze, analysis_freeze_v2, matrix, populations
from tools.research.v6.e4 import preregistration as v1
from tools.research.v6.e4 import preregistration_v2 as v2
from tools.research.v6.e4.analyze_e4 import (
    HOLDS,
    NEITHER,
    NOT_EVALUABLE,
    REFUTED,
    STOP,
    SUPPORTED,
    read_interpretation,
)

PREREG_V2 = v2.load_preregistration_v2()
V1_FREEZE_ID = "v6-e4-freeze-v1-101a941f5e30"
# The committed v1 files, preserved byte for byte (SHA-256 with LF line endings).
V1_PREREGISTRATION_SHA256 = "56307844e1c01a52b46b3fc1d100a34706e13d6a645614d6d2bcea94757b9973"
V1_FREEZE_RECORD_SHA256 = "2c2018b1d755901e51b51dcae28e96899973ea94806d2900e71c8a0bc0cc4d91"
V1_TOOLING_SOURCE_SHA = "108d08d358611c073731ae1b1020b91da8c907fb"

# The owner's amendment, verbatim (code formatting removed).
STATEMENT = ("H3 is not independently mechanism-identifying because the H3 STAYS signature is also "
             "expected under the global-null condition.")
RULES = (
    ("If H0 is satisfied, H0 takes precedence over ¬H1 ∧ H3. H3 is reported as consistent with "
     "opening-pass persistence but is non-discriminating under the global null."),
    ("H1 ∧ H3 ∧ ¬H2 retains its registered interpretation. The contrast between MULTI-PASS change and "
     "OPENING-ONLY persistence provides the discriminating signature."),
    ("If ¬H0 ∧ ¬H1 ∧ H3 occurs and no other registered interpretation applies, do not conclude that the "
     "residual is caused by the opening-pass effect. Report: “No registered causal interpretation applies; "
     "H3 persistence is consistent with, but does not identify, an opening-pass mechanism.”"),
    ("No hypothesis definition, threshold, population, metric, contest classification, matrix cell, "
     "treatment, or analyzer calculation changes."),
)
RULE_3_OUTCOME = "¬H0 ∧ ¬H1 ∧ H3"
RULE_3_TEXT = ("No registered causal interpretation applies; H3 persistence is consistent with, but does not "
               "identify, an opening-pass mechanism.")
RULE_1_NOTE = {"hypothesis": "E4-H3",
               "text": "H3 is consistent with opening-pass persistence but is non-discriminating under the global null."}
OPENING = "¬H1 ∧ H3"
PATHOLOGY = "H5, H6, H8"


def _statuses(d9: str = HOLDS, **hypotheses: str) -> dict[str, str]:
    """Every hypothesis REFUTED (H7 NEITHER) unless overridden, e.g. ``H0=SUPPORTED``."""
    statuses = {f"E4-H{n}": REFUTED for n in range(9)} | {"E4-H7": NEITHER, "D9-PRIME": d9}
    statuses.update({f"E4-{name}": status for name, status in hypotheses.items()})
    return statuses


def _read(statuses: dict[str, str]) -> tuple[dict, dict]:
    return read_interpretation(statuses, PREREG_V2["v1"]), v2.read_interpretation_v2(statuses, PREREG_V2)


def _head() -> str:
    return analysis_freeze.git_text("rev-parse", "HEAD")


# ---------------------------------------------------------------------------
# v1 is preserved; the amendment is pinned and changes no criterion
# ---------------------------------------------------------------------------


def test_v1_is_preserved_byte_for_byte_and_its_freeze_still_holds() -> None:
    assert v1.preregistration_digest() == v1.PREREGISTRATION_SHA256 == V1_PREREGISTRATION_SHA256
    assert analysis_freeze.file_sha256(analysis_freeze_v2.BASE_FREEZE_FILE) == V1_FREEZE_RECORD_SHA256
    record = analysis_freeze.load_freeze()
    assert (record["freeze_id"], record["identity"]["tooling_source_sha"]) == (V1_FREEZE_ID, V1_TOOLING_SOURCE_SHA)
    assert record["control_qualification"]["status"] == "PASS"
    assert PREREG_V2["v1"] == v1.load_preregistration()


def test_the_amendment_carries_the_owner_text_verbatim_and_names_v1() -> None:
    amendment = PREREG_V2["amendment"]
    assert (amendment["id"], amendment["title"]) == ("O-INTERPRETATION-2", "O-INTERPRETATION-2 / P-1 amendment")
    assert amendment["statement"] == STATEMENT
    assert tuple(rule["text"] for rule in amendment["rules"]) == RULES
    assert amendment["amends"]["preregistration"]["sha256"] == V1_PREREGISTRATION_SHA256
    assert amendment["amends"]["analysis_freeze"]["freeze_id"] == V1_FREEZE_ID
    assert amendment["finding"]["id"] == "P-1"
    reading = amendment["reading"]
    assert reading["amended_row"] == OPENING
    assert reading["rule_1"] == {"requires": {"E4-H0": SUPPORTED}, "note": RULE_1_NOTE}
    assert reading["rule_3"]["requires"] == {"E4-H0": REFUTED}
    assert reading["rule_3"]["outcome"] == {"result": RULE_3_OUTCOME, "conclusion": RULE_3_TEXT}
    assert f"“{RULE_3_TEXT}”" in RULES[2]


def test_the_amendment_changes_no_hypothesis_criterion_row_or_population() -> None:
    amendment, prereg = PREREG_V2["amendment"], PREREG_V2["v1"]
    # Only metadata keys are shared: nothing in v1's scientific content is restated or overridden.
    assert set(amendment) & set(prereg) == {"schema", "schema_version", "status", "authority"}
    assert "O-INTERPRETATION-2" not in {item["id"] for item in prereg["operationalizations"]}
    main = [row["result"] for row in prereg["interpretation"] if row["rule"]["kind"] == "all"]
    assert sorted([*amendment["reading"]["rule_3"]["unless_any_applies"], OPENING]) == sorted(main)
    assert RULE_3_OUTCOME not in {row["result"] for row in prereg["interpretation"]}


def test_a_changed_amendment_fails_closed(tmp_path: Path) -> None:
    path = tmp_path / "preregistration_v2.json"
    shutil.copyfile(v2.PREREGISTRATION_V2_PATH, path)
    assert v2.load_preregistration_v2(path)["amendment"]["id"] == "O-INTERPRETATION-2"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["reading"]["rule_1"]["requires"] = {"E4-H0": NEITHER}
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    with pytest.raises(v1.PreregistrationError, match="the amendment changed"):
        v2.load_preregistration_v2(path)


def test_a_changed_v1_fails_the_v2_load(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(v1, "PREREGISTRATION_SHA256", "0" * 64)
    with pytest.raises(v1.PreregistrationError, match="the pre-registration changed"):
        v2.load_preregistration_v2()


def test_an_amendment_inconsistent_with_v1_fails_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = tmp_path / "preregistration_v2.json"
    data = json.loads(v2.PREREGISTRATION_V2_PATH.read_text(encoding="utf-8"))
    data["reading"]["rule_3"]["unless_any_applies"].remove("H2")
    data["amends"]["preregistration"]["sha256"] = "0" * 64
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    monkeypatch.setattr(v2, "PREREGISTRATION_V2_SHA256", v2.preregistration_v2_digest(path))
    with pytest.raises(v1.PreregistrationError, match="does not amend the frozen.*other main rows"):
        v2.load_preregistration_v2(path)


# ---------------------------------------------------------------------------
# The O-INTERPRETATION-2 reading
# ---------------------------------------------------------------------------


def test_rule_1_the_frozen_global_null_reads_h0_alone() -> None:
    """P-1 itself: C-E4 read against itself, from the frozen control populations."""
    pinned = analysis_freeze.load_freeze()["control_qualification"]["populations"]["sha256"]
    frozen = populations.load_record(populations.POPULATIONS_PATH, freeze_id=V1_FREEZE_ID, expected_sha256=pinned)
    inputs = frozen["arms"]["primary"]["control_vs_control_hypotheses"]["interpretation_inputs"]
    assert (inputs["E4-H0"], inputs["E4-H1"], inputs["E4-H2"], inputs["E4-H3"]) == (SUPPORTED, REFUTED, REFUTED,
                                                                                 SUPPORTED)
    old, new = _read(inputs)
    assert old == {"applies": [OPENING, "H0"], "stop": None}
    assert (new["applies"], new["rule"], new["withheld"], new["notes"]) == (["H0"], 1, [OPENING], [RULE_1_NOTE])
    assert new["conclusions"] == [{"result": "H0", "conclusion": "Order is not load-bearing. The line closes"}]
    assert new["v1_reading"] == old


def test_rule_1_keeps_the_pathology_row() -> None:
    old, new = _read(_statuses(H0=SUPPORTED, H3=SUPPORTED, H6=SUPPORTED))
    assert old["applies"] == [OPENING, "H0", PATHOLOGY]
    assert (new["applies"], new["rule"]) == (["H0", PATHOLOGY], 1)


def test_rule_2_the_two_mechanism_row_is_unchanged() -> None:
    old, new = _read(_statuses(H1=SUPPORTED, H3=SUPPORTED))
    assert old["applies"] == new["applies"] == ["H1 ∧ H3 ∧ ¬H2"]
    assert (new["rule"], new["withheld"], new["notes"]) == (None, [], [])
    assert new["conclusions"][0]["conclusion"].startswith("The residual has two order mechanisms.")


@pytest.mark.parametrize("h2", [REFUTED, NEITHER])
def test_rule_3_no_registered_causal_interpretation(h2: str) -> None:
    old, new = _read(_statuses(H3=SUPPORTED, H2=h2))
    assert old["applies"] == [OPENING]
    assert (new["applies"], new["rule"], new["withheld"]) == ([RULE_3_OUTCOME], 3, [OPENING])
    assert new["conclusions"] == [{"result": RULE_3_OUTCOME, "conclusion": RULE_3_TEXT}]
    assert "none" not in new["applies"]


def test_rule_3_keeps_the_pathology_row_and_is_not_blocked_by_it() -> None:
    old, new = _read(_statuses(H3=SUPPORTED, H5=SUPPORTED))
    assert old["applies"] == [OPENING, PATHOLOGY]
    assert (new["applies"], new["rule"]) == ([RULE_3_OUTCOME, PATHOLOGY], 3)


def test_rule_3_does_not_act_when_another_registered_row_applies() -> None:
    old, new = _read(_statuses(H3=SUPPORTED, H2=SUPPORTED))
    assert old["applies"] == new["applies"] == ["H2", OPENING]
    assert (new["rule"], new["withheld"]) == (None, [])


def test_a_d9_stop_still_replaces_the_reading() -> None:
    old, new = _read(_statuses(d9=STOP, H0=SUPPORTED, H3=SUPPORTED))
    assert old["applies"] == new["applies"] == [] and new["stop"] == old["stop"] is not None
    assert new["rule"] is None


@pytest.mark.parametrize("h0", [NEITHER, NOT_EVALUABLE])
def test_an_h0_status_the_definition_cannot_produce_fails_closed(h0: str) -> None:
    with pytest.raises(v2.InterpretationError, match="SUPPORTED or REFUTED"):
        v2.read_interpretation_v2(_statuses(H0=h0, H3=SUPPORTED), PREREG_V2)


def test_v2_differs_from_v1_only_where_the_amended_row_applies() -> None:
    """Every status combination of H0-H3 and a pathology: the amendment never adds a causal
    row, never removes a row other than "¬H1 ∧ H3", and never keeps "¬H1 ∧ H3" beside H0."""
    states = (SUPPORTED, REFUTED, NEITHER, NOT_EVALUABLE)
    main = ("H1 ∧ H3 ∧ ¬H2", "H1 ∧ ¬H3 ∧ ¬H2", "H2", "H0")
    for h0, h1, h2, h3, h5 in itertools.product(states, states, states, states, (SUPPORTED, REFUTED)):
        statuses = _statuses(H0=h0, H1=h1, H2=h2, H3=h3, H5=h5)
        old = read_interpretation(statuses, PREREG_V2["v1"])
        if OPENING in old["applies"] and h0 not in (SUPPORTED, REFUTED):
            with pytest.raises(v2.InterpretationError):
                v2.read_interpretation_v2(statuses, PREREG_V2)
            continue
        new = v2.read_interpretation_v2(statuses, PREREG_V2)
        others = [row for row in old["applies"] if row in main]
        if OPENING not in old["applies"]:
            expected, rule = old["applies"], None
        elif h0 == SUPPORTED:
            expected, rule = [row for row in old["applies"] if row != OPENING], 1
        elif not others:
            expected, rule = [RULE_3_OUTCOME if row == OPENING else row for row in old["applies"]], 3
        else:
            expected, rule = old["applies"], None
        assert (new["applies"], new["rule"]) == (expected, rule), statuses
        assert new["v1_reading"] == old


# ---------------------------------------------------------------------------
# Analysis freeze v2
# ---------------------------------------------------------------------------


def _frozen_engine_tree() -> str:
    # The E4 interpretation identities pin freeze v1's match-generation tree.
    # Read it from the frozen v1 record rather than from HEAD: a later
    # experiment (V6 E5) legitimately changes engine/src, and E4's identity
    # is about E4's engine, which the committed-freeze tests below still pin
    # to the E4 implementation commit.
    tree: str = analysis_freeze.load_freeze()["identity"]["match_generation_tree"]
    return tree


def _identity() -> dict:
    return analysis_freeze_v2.identity_inputs(
        tooling_source_sha=_head(), match_generation_tree=_frozen_engine_tree())


def _write(path: Path, identity: dict) -> Path:
    path.write_text(json.dumps(analysis_freeze_v2.build_freeze_record(identity), indent=2, sort_keys=True),
                    encoding="utf-8")
    return path


def test_the_v2_identity_pins_freeze_v1_and_the_amendment() -> None:
    identity = _identity()
    base = analysis_freeze.load_freeze()
    assert identity["base_freeze"] == {"freeze_id": V1_FREEZE_ID, "freeze_digest": base["freeze_digest"],
                                       "path": analysis_freeze_v2.BASE_FREEZE_FILE, "sha256": V1_FREEZE_RECORD_SHA256}
    # Rule 4: no measurement file changes; every one equals its freeze-v1 pin.
    assert identity["measurement_tooling_sha256"] == base["identity"]["tooling_sha256"]
    assert identity["match_generation_tree"] == base["identity"]["match_generation_tree"]
    assert (identity["preregistration_sha256"], identity["preregistration_v2_sha256"]) == (
        V1_PREREGISTRATION_SHA256, v2.PREREGISTRATION_V2_SHA256)
    assert (identity["matrix_id"], identity["matches_total"]) == ("v6-e4-matrix-v1-fc29d575dd25", 15232)
    assert identity["matrix_id"] == matrix.matrix_id() == base["identity"]["matrix_id"]
    assert set(identity["interpretation_tooling_sha256"]) == set(analysis_freeze_v2.INTERPRETATION_FILES)
    assert not set(analysis_freeze_v2.INTERPRETATION_FILES) & set(analysis_freeze.TOOLING_FILES)
    record = analysis_freeze_v2.build_freeze_record(identity)
    assert record["freeze_id"].startswith("v6-e4-freeze-v2-") and record["freeze_id"] != V1_FREEZE_ID
    assert record["control_qualification"]["status"] == "INHERITED"
    assert record["control_qualification"]["from"] == V1_FREEZE_ID


def test_a_v2_record_loads_and_interpretation_drift_fails_closed(tmp_path: Path,
                                                                 monkeypatch: pytest.MonkeyPatch) -> None:
    path = _write(tmp_path / "analysis_freeze_v2.json", _identity())
    assert analysis_freeze_v2.load_freeze_v2(path)["freeze_id"].startswith("v6-e4-freeze-v2-")
    real = analysis_freeze_v2.file_sha256

    def drifted(relative: str, *args: object) -> str:
        return "0" * 64 if relative == "tools/research/v6/e4/preregistration_v2.py" else real(relative)

    monkeypatch.setattr(analysis_freeze_v2, "file_sha256", drifted)
    with pytest.raises(analysis_freeze.AnalysisFreezeError, match="interpretation_tooling_sha256"):
        analysis_freeze_v2.load_freeze_v2(path)


def test_measurement_drift_fails_freeze_v1_and_so_freeze_v2(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = _write(tmp_path / "analysis_freeze_v2.json", _identity())
    real = analysis_freeze.file_sha256

    def drifted(relative: str, *args: object) -> str:
        return "0" * 64 if relative == analysis_freeze.ANALYSIS_FILE else real(relative)

    monkeypatch.setattr(analysis_freeze, "file_sha256", drifted)
    with pytest.raises(analysis_freeze.AnalysisFreezeError, match="analyze_e4|e4_analysis_sha256"):
        analysis_freeze_v2.load_freeze_v2(path)


def test_a_changed_v1_record_fails_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = _write(tmp_path / "analysis_freeze_v2.json", _identity())
    real = analysis_freeze_v2.file_sha256

    def changed(relative: str, *args: object) -> str:
        return "0" * 64 if relative == analysis_freeze_v2.BASE_FREEZE_FILE else real(relative)

    monkeypatch.setattr(analysis_freeze_v2, "file_sha256", changed)
    with pytest.raises(analysis_freeze.AnalysisFreezeError, match="base_freeze"):
        analysis_freeze_v2.load_freeze_v2(path)


def test_a_tampered_v2_record_fails_closed(tmp_path: Path) -> None:
    path = _write(tmp_path / "analysis_freeze_v2.json", _identity())
    record = json.loads(path.read_text(encoding="utf-8"))
    record["identity"]["preregistration_v2_sha256"] = "0" * 64
    path.write_text(json.dumps(record), encoding="utf-8")
    with pytest.raises(analysis_freeze.AnalysisFreezeError, match="digest or id"):
        analysis_freeze_v2.load_freeze_v2(path)


def test_measurement_pins_that_differ_from_v1_fail_closed_even_if_self_consistent(tmp_path: Path) -> None:
    identity = _identity()
    identity["measurement_tooling_sha256"] = {**identity["measurement_tooling_sha256"],
                                              analysis_freeze.ANALYSIS_FILE: "0" * 64}
    path = _write(tmp_path / "analysis_freeze_v2.json", identity)
    with pytest.raises(analysis_freeze.AnalysisFreezeError, match="differs from freeze v1's pins"):
        analysis_freeze_v2.load_freeze_v2(path)


def test_the_execution_source_check_covers_the_interpretation_files(monkeypatch: pytest.MonkeyPatch) -> None:
    # Freeze v1's own check (clean tree, engine tree, v1 tooling) is covered by its tests; isolate v2's.
    monkeypatch.setattr(analysis_freeze, "verify_execution_source", lambda record: None)
    identity = _identity()
    identity["interpretation_tooling_sha256"] = {**identity["interpretation_tooling_sha256"],
                                                 "tools/research/v6/e4/preregistration_v2.json": "0" * 64}
    with pytest.raises(analysis_freeze.AnalysisFreezeError, match="freeze v2 execution source check failed"):
        analysis_freeze_v2.verify_execution_source_v2(analysis_freeze_v2.build_freeze_record(identity))


# ---------------------------------------------------------------------------
# The committed freeze v2
# ---------------------------------------------------------------------------

FREEZE_V2_ID = "v6-e4-freeze-v2-68d262a0dbd1"
V2_TOOLING_SOURCE_SHA = "516022950d660e17028e8d3f3864667b44257254"
ENGINE_TREE = "940a27bcf8c62268eb15210cc30c28cae4d33e50"


def test_the_committed_v2_freeze_holds(monkeypatch: pytest.MonkeyPatch) -> None:
    record = analysis_freeze_v2.load_freeze_v2()
    assert record["freeze_id"] == FREEZE_V2_ID
    assert record["status"] == "frozen before any T-E4 or T-E4K1 matrix data exists"
    identity = record["identity"]
    assert (identity["tooling_source_sha"], identity["match_generation_tree"]) == (V2_TOOLING_SOURCE_SHA, ENGINE_TREE)
    assert identity["base_freeze"]["freeze_id"] == V1_FREEZE_ID
    assert identity["base_freeze"]["sha256"] == V1_FREEZE_RECORD_SHA256
    assert identity["preregistration_v2_sha256"] == v2.PREREGISTRATION_V2_SHA256
    assert record["control_qualification"]["from"] == V1_FREEZE_ID
    # The interpretation files equal their content at the tooling commit (v1's own check isolated).
    monkeypatch.setattr(analysis_freeze, "verify_execution_source", lambda record: None)
    analysis_freeze_v2.verify_execution_source_v2(record)


def test_only_commits_holding_the_record_count_as_generated_under_freeze_v2() -> None:
    assert analysis_freeze_v2.held_at(V1_TOOLING_SOURCE_SHA) is False
    assert analysis_freeze_v2.held_at(V2_TOOLING_SOURCE_SHA) is False
    assert analysis_freeze_v2.held_at(_head()) is True


def _run_root(tmp_path: Path, *, git_sha: str, git_dirty: bool = False, base: str = V1_FREEZE_ID) -> Path:
    """A synthetic run root: treatment provenance for every field and a v1 analysis record
    carrying the frozen global-null (control-vs-control) inputs."""
    from tools.research.v6.e4 import run_e4

    provenance = {"git_sha": git_sha, "git_dirty": git_dirty}
    for condition_id in matrix.TREATMENT_CONDITIONS:
        for field_id in matrix.FIELD_IDS:
            path = run_e4.condition_root(tmp_path, condition_id, field_id) / "provenance.json"
            path.parent.mkdir(parents=True)
            path.write_text(json.dumps({**provenance, "e4_freeze_id": base}), encoding="utf-8")
    frozen = json.loads(populations.POPULATIONS_PATH.read_text(encoding="utf-8"))
    inputs = frozen["arms"]["primary"]["control_vs_control_hypotheses"]["interpretation_inputs"]
    analysis = {"freeze_id": V1_FREEZE_ID, "matrix_id": matrix.matrix_id(), "e4_analysis_version": 1,
                "preregistration_sha256": V1_PREREGISTRATION_SHA256, "provenance": provenance,
                "result": {"interpretation_inputs": inputs,
                           "interpretation": read_interpretation(inputs, PREREG_V2["v1"])}}
    path = run_e4.freeze_root(tmp_path, V1_FREEZE_ID) / run_e4.ANALYSIS_RECORD_NAME
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(analysis, ensure_ascii=False), encoding="utf-8")
    return tmp_path


def test_interpret_reads_the_v1_analysis_under_freeze_v2(tmp_path: Path) -> None:
    from tools.research.v6.e4 import run_e4

    root = _run_root(tmp_path, git_sha=_head())
    record = analysis_freeze_v2.interpret(run_root=root)
    assert (record["freeze_id"], record["base_freeze_id"]) == (FREEZE_V2_ID, V1_FREEZE_ID)
    assert record["reading"]["applies"] == ["H0"] and record["reading"]["v1_reading"]["applies"] == [OPENING, "H0"]
    written = run_e4.freeze_root(root, FREEZE_V2_ID) / analysis_freeze_v2.INTERPRETATION_RECORD_NAME
    assert json.loads(written.read_text(encoding="utf-8"))["reading"] == record["reading"]


@pytest.mark.parametrize(("kwargs", "message"), [
    ({"git_sha": V2_TOOLING_SOURCE_SHA}, "commit holding freeze v2"),
    ({"git_sha": "HEAD", "git_dirty": True}, "clean tree"),
    ({"git_sha": "HEAD", "base": FREEZE_V2_ID}, "ran under"),
])
def test_interpret_refuses_data_not_produced_under_freeze_v2(tmp_path: Path, kwargs: dict, message: str) -> None:
    if kwargs["git_sha"] == "HEAD":
        kwargs = {**kwargs, "git_sha": _head()}
    with pytest.raises(analysis_freeze.AnalysisFreezeError, match=message):
        analysis_freeze_v2.interpret(run_root=_run_root(tmp_path, **kwargs))


def test_interpret_refuses_an_analysis_whose_v1_reading_does_not_recompute(tmp_path: Path) -> None:
    from tools.research.v6.e4 import run_e4

    root = _run_root(tmp_path, git_sha=_head())
    path = run_e4.freeze_root(root, V1_FREEZE_ID) / run_e4.ANALYSIS_RECORD_NAME
    analysis = json.loads(path.read_text(encoding="utf-8"))
    analysis["result"]["interpretation"] = {"applies": ["H0"], "stop": None}
    path.write_text(json.dumps(analysis, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(analysis_freeze.AnalysisFreezeError, match="does not recompute"):
        analysis_freeze_v2.interpret(run_root=root)
