"""V6 E8: the machine-readable pre-registration equals the registered markdown.

docs/research/v6/V6_E8_ACTIVE_SPATIAL_SENSING_PREREGISTRATION.md, revision 3,
is the authoritative wording. ``tools/research/v6/e8/preregistration.json``
transcribes it. These tests show that the transcription is pinned, that it
records the registered revision's digest, that every registered text in it is
verbatim in the markdown, that every registered table and set equals the
markdown's, that its arithmetic recomputes, that any drift fails closed, and
that nothing loaded can be changed afterwards.
"""

from __future__ import annotations

import copy
import hashlib
import json
import subprocess
from pathlib import Path
from types import MappingProxyType
from typing import Any

import pytest

from tools.research.v6.e8 import preregistration

ROOT = Path(__file__).resolve().parents[2]
MARKDOWN = ROOT / "docs" / "research" / "v6" / "V6_E8_ACTIVE_SPATIAL_SENSING_PREREGISTRATION.md"


def _data() -> dict[str, Any]:
    return preregistration.parse(preregistration.PREREGISTRATION_PATH.read_text(encoding="utf-8"))


def _markdown() -> str:
    return MARKDOWN.read_text(encoding="utf-8")


def _lf_digest(content: bytes) -> str:
    return hashlib.sha256(content.replace(b"\r\n", b"\n")).hexdigest()


# ---------------------------------------------------------------------------
# Pinning and authority
# ---------------------------------------------------------------------------


def test_the_transcription_loads_and_is_pinned() -> None:
    data = preregistration.load_preregistration()
    assert preregistration.preregistration_digest() == preregistration.PREREGISTRATION_SHA256
    assert data["schema"] == "bytefray.v6.e8.preregistration"
    assert data["authority"]["document"] == "docs/research/v6/V6_E8_ACTIVE_SPATIAL_SENSING_PREREGISTRATION.md"
    assert data["authority"]["revision"] == 3 and data["authority"]["governs"] == "revision 3"


def test_it_records_the_registered_revision_and_keeps_revisions_1_and_2_as_history() -> None:
    authority = _data()["authority"]
    assert authority["registration_commit"] == "00fb420"
    assert preregistration.file_digest(MARKDOWN) == authority["document_sha256"]
    committed = subprocess.run(["git", "show", f"{authority['registration_commit']}:{authority['document']}"],
                               cwd=ROOT, capture_output=True, check=True).stdout
    assert _lf_digest(committed) == authority["document_sha256"]
    assert authority["history"] == [
        {"revision": 1, "commit": "28925fd",
         "document_sha256": "6d50dae648dbdb0def2bcb94644e0705b4d62d4e818f7288190df4f8fac4efbb",
         "standing": "historical provenance"},
        {"revision": 2, "commit": "090d11e",
         "document_sha256": "0c6d0b741a4584ac10bc5f2aa3837bbc83213b8a608352d86949bdf809737286",
         "standing": "historical provenance"}]
    for entry in authority["history"]:
        earlier = subprocess.run(["git", "show", f"{entry['commit']}:{authority['document']}"],
                                 cwd=ROOT, capture_output=True, check=True).stdout
        assert _lf_digest(earlier) == entry["document_sha256"]


def test_the_transcription_is_internally_consistent_and_equals_the_markdown() -> None:
    data = _data()
    assert preregistration.internal_problems(data) == []
    assert preregistration.markdown_problems(data, _markdown()) == []


def test_every_registered_text_is_verbatim_in_the_markdown() -> None:
    source = preregistration.plain(_markdown())
    texts = list(preregistration.verbatim_texts(_data()))
    assert len(texts) > 200
    missing = [path for path, text in texts if preregistration.plain(text) not in source]
    assert missing == []


# ---------------------------------------------------------------------------
# Drift fails closed
# ---------------------------------------------------------------------------


def _set(data: dict[str, Any], path: tuple[Any, ...], value: Any) -> None:
    target = data
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value


@pytest.mark.parametrize(("path", "value"), [
    (("interpretation", "rows", 1, "reading", "text"), "Under the whole-tick parent, some fixed policy wins."),
    (("interpretation", "rows", 2, "combinations"), [["SUPPORTED", "NEITHER"]]),
    (("interpretation", "no_choice_tax_qualifier", "NEITHER", "text"), "a dominant policy under both channels"),
    (("interpretation", "qualifiers", "H8-CHANNEL", "REFUTED_naming", "text"), "naming the attacker"),
    (("interpretation", "repeat_readings", "REFUTED", "text"), "Against the census, re-acquisition pays."),
    (("interpretation", "adapt", "readings", "NEITHER", "text"), "Within the {𝒞} stratum, adaptation pays."),
    (("interpretation", "core_answer", "order", 0, "outcome"), "NO"),
    (("population", "members", "EVADE8", "evade"), "off"),
    (("population", "members", "SPLIT8", "shares", "sensor"), "1/2"),
    (("population", "sets", "a8"), ["RUSH8", "REACQ8", "PACED8", "STEALTH8", "LURK8", "SPLIT8"]),
    (("definitions", "FL(a, d)", "defenders"), ["GUARD8", "EVADE8"]),
    (("definitions", "L8", "pairs"), [["LURK8", "RUSH8"]]),
    (("census", "predicted"), ["EVADE8", "GUARD8"]),
    (("kill_criteria", "KC8-6", "name"), "Acquisition"),
    (("gates", "E8-D", "clauses", 2, "kind"), "Ruleset invariant"),
    (("gates", "CQ8", "checks", 1, "name"), "Twin identity"),
    (("hypotheses", "H8-SEAT", "refuted", "text"), "ΔG < 0, and stab(ΔG ≤ 0) ≥ 9/10"),
    (("decisions", "R-4", "value"), "1/8"),
    (("decisions", "R-8", "value"), 3),
    (("boundaries", "B-3", "where"), ["§3"]),
    (("conditions", 1, "ruleset_id"), "bytefray-rules-6-research-sensing-active-w28"),
    (("traces", "fields", 0, "field"), "previous_sensed"),
    (("member_semantics", "parameters", "acquire=ownership", "active", "same_as_passive"), False),
    (("member_semantics", "reacquisition_precedence", "rules", 1, "text"), "The first offer restarts verification."),
    (("seat_criterion", "reported", "quantiles", "rule"), "sorted(xs)[int(q * n)]"),
    (("operationalizations", "O-BOOT", "draw_form"), "tuple(rng.randrange(32) for _ in range(31))"),
    (("member_semantics", "initial_acquisition", "rule", "text", 0),
     "Initial acquisition ends once an enemy anchor is known."),
    (("member_semantics", "acquisition_eligible", "text"),
     "An offer is acquisition-eligible when the acquisition step is reached and no enemy anchor is known (discovery)."),
    (("arithmetic", "A.2", "text"), "At most 16 stride-8 READs hit one of them (E8-DR Appendix A.2)."),
    (("references", "DR"), "docs/research/v6/V6_PRICED_SENSING_REVIEW.md"),
])
def test_drift_from_the_markdown_is_reported(path: tuple[Any, ...], value: Any) -> None:
    data = copy.deepcopy(_data())
    _set(data, path, value)
    assert preregistration.markdown_problems(data, _markdown()) or preregistration.internal_problems(data)


@pytest.mark.parametrize(("path", "value"), [
    (("thresholds", "epsilon"), "1/8"),
    (("thresholds", "stability"), "8/10"),
    (("thresholds", "stability_count"), 899),
    (("thresholds", "resamples"), 999),
    (("thresholds", "adapt_k"), 3),
    (("thresholds", "seat_magnitude_floor"), "1/20"),
    (("fields", "cells_total"), 16895),
    (("fields", "F1", "cells_per_condition"), 3552),
    (("operationalizations", "O-BOOT", "rng_seed"), 43),
    (("seat_criterion", "reported", "quantiles", "indices"), [25, 499, 974]),
    (("arithmetic", "A.3", "expectation"), "2"),
    (("arithmetic", "A.1", "expectation"), "7/2"),
    (("arithmetic", "A.2", "reads_at_most"), 16),
    (("arithmetic", "A.2", "worst_case_core_above_anchor"), [57, 64]),
    (("gates", "E8-D", "clauses", 2, "matched_pairs_per_condition"), 640),
    (("gates", "E8-D", "clauses", 2, "opponents"),
     ["RUSH8", "REACQ8", "PACED8", "STEALTH8", "SPLIT8", "GUARD8", "EVADE8", "ADAPT8", "STRESS8", "GREED8"]),
    (("population", "sets", "pi_f"),
     ["RUSH8", "REACQ8", "PACED8", "STEALTH8", "LURK8", "SPLIT8", "GUARD8", "EVADE8", "GREED8", "ADAPT8", "STRESS8"]),
    (("disposition", "order", 2, "outcome"), "CANDIDATE"),
])
def test_internal_drift_is_reported(path: tuple[Any, ...], value: Any) -> None:
    data = copy.deepcopy(_data())
    _set(data, path, value)
    assert preregistration.internal_problems(data)


def test_a_removed_row_combination_breaks_totality() -> None:
    data = copy.deepcopy(_data())
    data["interpretation"]["rows"][7]["combinations"].pop()
    assert any("row coverage" in problem for problem in preregistration.internal_problems(data))
    data = copy.deepcopy(_data())
    data["interpretation"]["rows"][5]["combinations"].append(["SUPPORTED", "SUPPORTED"])
    assert any("row coverage" in problem for problem in preregistration.internal_problems(data))


def test_a_changed_transcription_file_fails_to_load(tmp_path: Path) -> None:
    changed = tmp_path / "preregistration.json"
    changed.write_text(preregistration.PREREGISTRATION_PATH.read_text(encoding="utf-8").replace('"1/16"', '"1/8"'),
                       encoding="utf-8")
    with pytest.raises(preregistration.PreregistrationError, match="digest"):
        preregistration.load_preregistration(changed)


def test_a_changed_markdown_fails_to_load(tmp_path: Path) -> None:
    changed = tmp_path / "prereg.md"
    changed.write_text(_markdown().replace("**k = 2**", "**k = 3**"), encoding="utf-8")
    with pytest.raises(preregistration.PreregistrationError, match="registered revision"):
        preregistration.load_preregistration(markdown=changed)


def test_a_consistent_but_disagreeing_transcription_fails_to_load(tmp_path: Path) -> None:
    data = copy.deepcopy(_data())
    data["interpretation"]["repeat_readings"]["REFUTED"]["text"] = "Against the census, re-acquisition pays."
    changed = tmp_path / "preregistration.json"
    changed.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    with pytest.raises(preregistration.PreregistrationError, match="disagrees"):
        preregistration.load_preregistration(changed, expected_sha256=preregistration.file_digest(changed))


def test_duplicate_keys_are_refused() -> None:
    with pytest.raises(preregistration.PreregistrationError, match="duplicate"):
        preregistration.parse('{"a": 1, "a": 2}')


# ---------------------------------------------------------------------------
# Specific registered items
# ---------------------------------------------------------------------------


def test_the_registered_sets() -> None:
    sets = _data()["population"]["sets"]
    assert sets["pi"] == ["RUSH8", "REACQ8", "PACED8", "STEALTH8", "LURK8", "SPLIT8", "GUARD8", "EVADE8", "GREED8",
                          "ADAPT8", "STRESS8"]
    assert sets["pi_f"] == [m for m in sets["pi"] if m != "ADAPT8"]
    assert sets["a8"] == ["RUSH8", "REACQ8", "PACED8", "STEALTH8", "LURK8"]
    assert _data()["census"]["predicted"] == ["EVADE8"]
    assert preregistration.static_census(_data()) == ("EVADE8",)


def test_the_registered_numbers() -> None:
    data = _data()
    assert data["thresholds"]["stability"] == "9/10" and data["thresholds"]["resamples"] == 1000
    assert data["thresholds"]["stability_count"] == 900
    assert data["fields"]["cells_total"] == 16_896 and data["fields"]["cells_per_condition"] == 4_224
    assert data["gates"]["E8-D"]["clauses"][2]["matched_pairs_per_condition"] == 576
    assert data["seat_criterion"]["reported"]["quantiles"]["indices"] == [25, 500, 974]
    assert [preregistration.quantile_index(q, 1000) for q in (0.025, 0.5, 0.975)] == [25, 500, 974]
    assert data["decisions"]["R-8"]["value"] == 2 and data["decisions"]["R-2"]["value"] == 27


def test_the_revision_2_corrections_are_transcribed() -> None:
    semantics = _data()["member_semantics"]
    precedence = [rule["text"] for rule in semantics["reacquisition_precedence"]["rules"]]
    assert precedence[0].startswith("Once a re-acquisition search is in progress")
    assert "neither advances nor resets the count" in semantics["parameters"]["reacquire=adaptive"]["passive"]["text"][1]
    assert "not engine visibility" in semantics["known_set"]["scope"]["text"]
    assert semantics["parameters"]["stress"]["repair_value"] == "the normal core beacon value"
    assert [rule["id"] for rule in _data()["traversal"]["knowledge_rules"]["rules"]] == [f"KU-{n}" for n in range(1, 10)]
    kc86 = _data()["kill_criteria"]["KC8-6"]["label"]["rules"]
    assert [rule["label"] for rule in kc86] == ["channel race", "information dominated", "mixed dominance"]


def test_the_revision_3_corrections_are_transcribed() -> None:
    semantics = _data()["member_semantics"]
    assert semantics["acquisition_eligible"]["requires"] == [
        "the acquisition step is reached", "no enemy anchor is known", "the entrant has not confirmed the enemy core"]
    rule = semantics["initial_acquisition"]["rule"]["text"]
    assert rule[0] == ("Initial acquisition ends once the enemy core is confirmed. Loss of current passive visibility "
                       "alone does not restart initial acquisition.")
    assert rule[1].startswith("Re-acquisition is a separate state.") and rule[2].startswith("SPLIT8: its sensor")
    assert semantics["initial_acquisition"]["supports_reacquisition"] == ["repeat", "adaptive"]
    assert "before the enemy core is confirmed" in semantics["channel_difference"]["passive"]["text"]
    members = _data()["population"]["members"]
    assert members["SPLIT8"]["reacquire"] == "once"
    assert [m for m, v in members.items() if v["reacquire"] in ("repeat", "adaptive")] == ["REACQ8", "ADAPT8"]
    # The re-derived census is recomputed from the corrected registration, not copied from a freeze.
    assert preregistration.static_census(_data()) == ("EVADE8",) == tuple(_data()["census"]["predicted"])
    assert len(_data()["census"]["revision_3_rederivation"]["text"]) == 5


def test_appendix_a2_is_17_reads_under_e6s_verification_order() -> None:
    # Revision 3: E6's verification window, anchor + 1 first, needs 17 READs in the worst case, not 16.
    def order(center: int) -> list[int]:
        window = [center + 1]
        for step in range(8, 65, 8):
            window += [center + 1 - step, center + 1 + step]
        return window

    worst = 0
    for m in range(8, 65):
        for sign in (1, -1):
            base = -m if sign == 1 else m
            cells = set(range(base, base + 8))
            worst = max(worst, next(i + 1 for i, x in enumerate(order(0)) if x in cells))
    assert worst == 17
    assert _data()["arithmetic"]["A.2"]["reads_at_most"] == 17
    assert preregistration.verification_window_worst_case(_data()) == (17, list(range(58, 65)))
    assert "transcription_notes" not in _data()
    assert _data()["references"]["DR"] == "docs/research/v6/V6_PRICED_SENSING_DESIGN_REVIEW.md"


# ---------------------------------------------------------------------------
# Nothing loaded can be changed
# ---------------------------------------------------------------------------


def test_the_loaded_registration_is_deeply_immutable() -> None:
    data = preregistration.load_preregistration()
    assert isinstance(data, MappingProxyType)
    with pytest.raises(TypeError):
        data["thresholds"] = {}  # type: ignore[index]
    with pytest.raises(TypeError):
        data["thresholds"]["stability"] = "1/2"  # type: ignore[index]
    sets = data["population"]["sets"]
    assert all(isinstance(value, tuple) for value in sets.values())
    with pytest.raises(AttributeError):
        sets["a8"].append("SPLIT8")  # type: ignore[attr-defined]
    with pytest.raises(TypeError):
        data["interpretation"]["rows"][0]["combinations"] = ()  # type: ignore[index]
    assert isinstance(data["interpretation"]["rows"], tuple)


def test_freeze_is_deep() -> None:
    frozen = preregistration.freeze({"a": [1, {"b": [2, 3]}]})
    assert frozen["a"][1]["b"] == (2, 3)
    with pytest.raises(TypeError):
        frozen["a"][1]["b"] = ()
