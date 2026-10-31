"""The development line's compatibility record agrees with the code.

docs/releases/BYTEFRAY_DEVELOPMENT_COMPATIBILITY.json is the single
authoritative compatibility declaration for this line
(docs/COMPONENT_VERSIONING.md). These run tools/release_compatibility.py's
checks, and the negative controls prove those checks actually catch a
disagreement rather than passing vacuously.

The published 5.1.0-alpha.1 record describes a release that still runs
Classic, so it no longer agrees with this tree's code by design; only its
generated page is still checked against its own JSON.
"""

from __future__ import annotations

import copy
from pathlib import Path

import pytest

from tools.release_compatibility import (
    companion_markdown,
    generated_block,
    load_record,
    python_package_version,
    render_markdown,
    runtime_problems,
)

RELEASES = Path(__file__).resolve().parents[2] / "docs" / "releases"
RECORD = RELEASES / "BYTEFRAY_DEVELOPMENT_COMPATIBILITY.json"
PUBLISHED_5_1_RECORD = RELEASES / "BYTEFRAY_5_1_0_ALPHA_1_COMPATIBILITY.json"


@pytest.fixture(scope="module")
def record() -> dict:
    return load_record(RECORD)


def test_record_agrees_with_the_code(record: dict) -> None:
    assert runtime_problems(record) == []


def test_generated_summary_is_current(record: dict) -> None:
    markdown = companion_markdown(RECORD).read_text(encoding="utf-8")
    assert generated_block(markdown) == render_markdown(record), (
        "Rerun: python tools/release_compatibility.py "
        "docs/releases/BYTEFRAY_DEVELOPMENT_COMPATIBILITY.json --write"
    )


def test_published_5_1_record_page_still_matches_its_own_record() -> None:
    markdown = companion_markdown(PUBLISHED_5_1_RECORD).read_text(encoding="utf-8")
    assert generated_block(markdown) == render_markdown(load_record(PUBLISHED_5_1_RECORD))


def test_record_is_proposed_retires_classic_and_names_the_bundled_spectator_build(record: dict) -> None:
    """A development line's record stays proposed until a release candidate
    exists (docs/COMPONENT_VERSIONING.md §6)."""

    assert record["status"] == "proposed"
    assert record["rulesets"]["default"] == "bytefray-rules-6-alpha1"
    assert [entry["id"] for entry in record["rulesets"]["offered"]] == ["bytefray-rules-6-alpha1"]
    assert "bytefray-rules-4" in record["rulesets"]["historical_readable_not_executable"]
    viewer = record["spectator"]["application"]
    assert viewer["version"] == "0.1.0-alpha.1"
    assert viewer["source"]["commit"] == "14089a7bf624a5974346306a277e307ea8f48c07"


@pytest.mark.parametrize(
    ("version", "expected"),
    [
        ("5.1.0", "5.1.0"),
        ("5.1.0-alpha.1", "5.1.0a1"),
        ("5.1.0-beta.2", "5.1.0b2"),
        ("5.1.0-rc.10", "5.1.0rc10"),
    ],
)
def test_application_versions_map_to_pep_440(version: str, expected: str) -> None:
    assert python_package_version(version) == expected


@pytest.mark.parametrize("version", ["5.1", "5.1.0-alpha1", "5.1.0a1", "v5.1.0"])
def test_non_semver_application_versions_are_rejected(version: str) -> None:
    with pytest.raises(ValueError):
        python_package_version(version)


def _tampered(record: dict, change) -> list[str]:
    copied = copy.deepcopy(record)
    change(copied)
    return runtime_problems(copied)


@pytest.mark.parametrize(
    "change",
    [
        lambda r: r["rulesets"].__setitem__("default", "bytefray-rules-4"),
        lambda r: r["rulesets"]["offered"][0].__setitem__("display_name", "Classic"),
        lambda r: r["rulesets"]["offered"][0].__setitem__("stability", "stable"),
        lambda r: r["rulesets"]["offered"].append(
            {"id": "bytefray-rules-4", "display_name": "Classic", "stability": "stable", "selection": "x"}
        ),
        lambda r: r["rulesets"]["surfaces"]["Designer Simple"].append("bytefray-rules-4"),
        lambda r: r["rulesets"]["surfaces"]["bytefray tournament"].append("bytefray-rules-4"),
        lambda r: r["rulesets"]["historical_readable_not_executable"].remove("bytefray-rules-4"),
        lambda r: r["rulesets"]["historical_readable_not_executable"].append("bytefray-rules-6-alpha1"),
        lambda r: r["agent_api"].__setitem__("executable", [1, 2]),
        lambda r: r["agent_api"].__setitem__("retired_from_execution", [2]),
        lambda r: r["agent_api"].__setitem__("retired_from_execution", []),
        lambda r: r["agent_api"]["manifest_capabilities"].__setitem__("version", 99),
        lambda r: r["formats"]["evaluation"].__setitem__("writes", 4),
        lambda r: r["formats"]["evaluation"].__setitem__("identity", 4),
        lambda r: r["formats"]["replay"].__setitem__("writes", 5),
        lambda r: r["formats"]["trace"].__setitem__("reads", [2]),
        lambda r: r["spectator"]["presentation_protocol"].__setitem__("bytefray_writes", 3),
        lambda r: r["spectator"]["supported_matches"].__setitem__("entrants", ["A", "B", "C"]),
        lambda r: r["application"].__setitem__("python_package_version", "6.0.0-alpha.1"),
        # A candidate must describe the version this tree builds.
        lambda r: r.__setitem__("status", "candidate"),
        lambda r: r.__setitem__("status", "published"),
        # The named Spectator build is the one tools/spectator_companion.json pins.
        lambda r: r["spectator"]["application"].__setitem__("version", "0.1.0"),
        lambda r: r["spectator"]["application"]["source"].__setitem__("commit", "b8a4f49"),
        lambda r: r["spectator"]["application"]["windows_build"].__setitem__("sha256", "0" * 64),
        lambda r: r["spectator"]["presentation_protocol"].__setitem__("spectator_reads", [2]),
    ],
)
def test_a_disagreement_is_reported(record: dict, change) -> None:
    assert _tampered(record, change)
