"""The product / frozen-science qualification boundary stays exact and enforced.

Product CI deselects only the inventory that
tools/qualification/frozen_science_e9.json transfers to the historical
workflow; protected V6/E9 evidence in this tree must still equal the
immutable snapshot commit. See docs/releases/FROZEN_SCIENCE_QUALIFICATION.md.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path

import pytest

from tools.qualification.frozen_science import (
    FrozenScienceError,
    anchor_manifest,
    check_junit,
    check_preservation_pins,
    guard,
    load_policy,
    manifest_digest,
    verify_snapshot,
)

ROOT = Path(__file__).resolve().parents[2]
POLICY = load_policy()
HEX40 = re.compile(r"[0-9a-f]{40}\Z")


def _root_conftest():
    import importlib.util

    spec = importlib.util.spec_from_file_location("bytefray_root_conftest", ROOT / "conftest.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_policy_pins_immutable_identities_and_locked_status() -> None:
    snapshot = POLICY["historical_snapshot"]
    protected = POLICY["protected_evidence"]
    for value in (snapshot["commit"], snapshot["tree"], protected["anchor_commit"], protected["anchor_tree"]):
        assert HEX40.match(value), value
    assert protected["anchor_commit"] == snapshot["commit"]
    assert POLICY["status"] == {"E9": "LOCKED", "requirement_C": "NOT ESTABLISHED"}


def test_product_transfer_is_exact_and_limited_to_frozen_research() -> None:
    transfer = POLICY["product_ci_transfer"]
    modules = [entry["path"] for entry in transfer["modules"]]
    assert len(modules) == len(set(modules))
    for entry in transfer["modules"]:
        assert re.fullmatch(r"engine/tests/test_v6_e9\w*\.py", entry["path"]), entry
        assert (ROOT / entry["path"]).is_file(), entry
        assert entry["reason"].strip()
    for entry in transfer["cases"]:
        path, _, name = entry["node_id"].partition("::")
        assert re.fullmatch(r"engine/tests/test_v6_e[2-8]\w*\.py", path), entry
        function = name.split("[", 1)[0]
        assert re.search(rf"^def {re.escape(function)}\(", (ROOT / path).read_text(encoding="utf-8"), re.MULTILINE), entry
        assert entry["reason"].strip()
        assert entry["historical_verification"].strip()


def test_every_transferred_module_is_in_the_historical_inventory() -> None:
    historical = set(POLICY["historical_e9_inventory"]["modules"])
    transferred = {entry["path"] for entry in POLICY["product_ci_transfer"]["modules"]}
    transferred |= {entry["node_id"] for entry in POLICY["product_ci_transfer"]["cases"]}
    assert transferred <= historical


def test_historical_runs_partition_the_inventory_and_exclude_only_recorded_irreproducible_cases() -> None:
    inventory = POLICY["historical_e9_inventory"]
    selections = [entry for run in inventory["runs"] for entry in run["selection"]]
    assert sorted(selections) == sorted(inventory["modules"])
    deselected = [node for run in inventory["runs"] for node in run["deselect"]]
    recorded = [entry["node_id"] for entry in inventory["not_reproducible_from_commits"]]
    assert deselected == recorded
    for entry in inventory["not_reproducible_from_commits"]:
        assert entry["node_id"].split("::", 1)[0] in inventory["modules"]
        assert entry["reason"].strip() and entry["evidence"].strip() and entry["disposition"].strip()
    v2 = next(run for run in inventory["runs"] if run["name"] == "e9-v2-recorded-harness")
    assert v2["selection"] == sorted(m for m in inventory["modules"] if m.startswith("engine/tests/test_v6_e9_v2_"))
    assert "tools.research.v6.e9.v2.qualification_guard" in v2["pytest_args"]
    for entry in inventory["not_reproducible_from_commits"]:
        assert len(entry["working_tree_pins"]) == 28
        assert all(re.fullmatch(r"[0-9a-f]{64}", pin) for pin in entry["working_tree_pins"].values())
        assert set(entry["superseded_pins"]) == {".gitattributes"}
    # 1,507 transferred cases; exactly the recorded irreproducible ones are not executed.
    assert sum(run["expected_collected"] for run in inventory["runs"]) == 1507 - len(recorded)


def test_historical_inventory_is_every_e9_module_of_the_snapshot() -> None:
    listing = subprocess.run(
        ["git", "ls-tree", "--name-only", POLICY["historical_snapshot"]["commit"], "engine/tests/"],
        cwd=ROOT, capture_output=True, text=True, check=True,
    ).stdout.split()
    snapshot_e9 = {p for p in listing if re.fullmatch(r"engine/tests/test_v6_e9\w*\.py", p)}
    inventory = set(POLICY["historical_e9_inventory"]["modules"])
    assert snapshot_e9 == {p for p in inventory if "::" not in p}


@pytest.mark.parametrize(
    ("node_id", "expected"),
    [
        ("engine/tests/test_v6_e9_v2_records.py::test_x", True),
        ("engine/tests/test_v6_e9_v2_records.py::test_x[a-b]", True),
        ("engine/tests/test_v6_e9_v2_records_extra.py::test_x", False),
        ("engine/tests/test_v6_e4_freeze.py::test_the_committed_freeze_holds", True),
        ("engine/tests/test_v6_e4_freeze.py::test_the_committed_freeze_holds[p]", True),
        ("engine/tests/test_v6_e4_freeze.py::test_the_committed_freeze_holds_too", False),
        ("engine/tests/test_v6_e4_freeze.py::test_other", False),
        ("engine/tests/test_process_runtime_integration.py::test_x", False),
    ],
)
def test_selection_matches_only_exact_entries(node_id: str, expected: bool) -> None:
    conftest = _root_conftest()
    modules = frozenset({"engine/tests/test_v6_e9_v2_records.py"})
    cases = frozenset({"engine/tests/test_v6_e4_freeze.py::test_the_committed_freeze_holds"})
    assert conftest.is_transferred(node_id, modules, cases) is expected


def test_selection_reads_the_policy_inventory() -> None:
    modules, cases = _root_conftest().transferred_inventory()
    assert modules == {entry["path"] for entry in POLICY["product_ci_transfer"]["modules"]}
    assert cases == {entry["node_id"] for entry in POLICY["product_ci_transfer"]["cases"]}


def test_protected_evidence_is_identical_to_the_immutable_snapshot() -> None:
    outcome = guard(ROOT, POLICY)
    assert outcome["files"] == POLICY["protected_evidence"]["files"]


def test_this_tree_is_not_accepted_as_the_historical_snapshot() -> None:
    if subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True,
                      check=True).stdout.strip() == POLICY["historical_snapshot"]["commit"]:
        pytest.skip("running at the snapshot itself")
    with pytest.raises(FrozenScienceError, match="expected " + POLICY["historical_snapshot"]["commit"]):
        verify_snapshot(ROOT, POLICY)


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid", "-c", "core.autocrlf=false", *args],
        cwd=repo, capture_output=True, text=True, check=True,
    ).stdout.strip()


@pytest.fixture
def synthetic(tmp_path: Path) -> tuple[Path, dict]:
    repo = tmp_path / "repo"
    (repo / "tools/research/v6/e9").mkdir(parents=True)
    (repo / "engine/tests").mkdir(parents=True)
    (repo / "tools/research/v6/e9/record.json").write_bytes(b'{"sealed": true}\r\n')
    (repo / "engine/tests/test_v6_e9_kernel.py").write_bytes(b"def test_x():\n    pass\n")
    (repo / "engine/tests/test_product.py").write_bytes(b"def test_y():\n    pass\n")
    (repo / ".gitattributes").write_bytes(b"* -text\n")
    _git(repo, "init", "-q")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "anchor")
    anchor = _git(repo, "rev-parse", "HEAD")
    scopes = {"prefixes": ["tools/research/v6/"], "patterns": ["engine/tests/test_v6_e9*.py"]}
    expected = anchor_manifest(repo, anchor, scopes)
    policy = {"protected_evidence": {
        "anchor_commit": anchor, "anchor_tree": _git(repo, "rev-parse", "HEAD^{tree}"),
        "scopes": scopes, "files": len(expected), "sha256_manifest": manifest_digest(expected),
    }}
    return repo, policy


def test_guard_accepts_the_unchanged_anchor_and_ignores_product_files(synthetic) -> None:
    repo, policy = synthetic
    (repo / "engine/tests/test_product.py").write_bytes(b"def test_y():\n    assert True\n")
    assert guard(repo, policy)["files"] == 2


@pytest.mark.parametrize("change", ["modify", "line_endings", "remove", "add", "add_untracked"])
def test_guard_detects_every_kind_of_protected_change(synthetic, change: str) -> None:
    repo, policy = synthetic
    record = repo / "tools/research/v6/e9/record.json"
    if change == "modify":
        record.write_bytes(b'{"sealed": false}\r\n')
    elif change == "line_endings":
        record.write_bytes(b'{"sealed": true}\n')
    elif change == "remove":
        _git(repo, "rm", "-q", "tools/research/v6/e9/record.json")
    elif change == "add":
        (repo / "engine/tests/test_v6_e9_new.py").write_bytes(b"")
        _git(repo, "add", "engine/tests/test_v6_e9_new.py")
    else:
        (repo / "tools/research/v6/e9/extra.json").write_bytes(b"{}")
    with pytest.raises(FrozenScienceError, match="differs from the immutable anchor"):
        guard(repo, policy)


def test_guard_rejects_a_pinned_identity_that_the_anchor_does_not_have(synthetic) -> None:
    repo, policy = synthetic
    policy["protected_evidence"]["sha256_manifest"] = "0" * 64
    with pytest.raises(FrozenScienceError, match="differs from the pinned identity"):
        guard(repo, policy)
    policy["protected_evidence"]["anchor_tree"] = "0" * 40
    with pytest.raises(FrozenScienceError, match="not the pinned"):
        guard(repo, policy)


def test_guard_fails_closed_without_the_anchor_commit(synthetic) -> None:
    repo, policy = synthetic
    policy["protected_evidence"]["anchor_commit"] = "1" * 40
    with pytest.raises(FrozenScienceError):
        guard(repo, policy)


def _junit(tmp_path: Path, tests: int, failures: int = 0, errors: int = 0) -> Path:
    report = tmp_path / "junit.xml"
    report.write_text(
        f'<testsuites><testsuite name="pytest" tests="{tests}" failures="{failures}" '
        f'errors="{errors}" skipped="0"/></testsuites>',
        encoding="utf-8",
    )
    return report


def test_check_junit_requires_the_exact_inventory_and_no_failure(tmp_path: Path) -> None:
    assert check_junit(_junit(tmp_path, 10), 10)["tests"] == 10
    with pytest.raises(FrozenScienceError, match="expected 11"):
        check_junit(_junit(tmp_path, 10), 11)
    with pytest.raises(FrozenScienceError, match="integrity failure"):
        check_junit(_junit(tmp_path, 10, failures=1), 10)
    with pytest.raises(FrozenScienceError, match="integrity failure"):
        check_junit(_junit(tmp_path, 10, errors=1), 10)
    with pytest.raises(FrozenScienceError, match="no readable JUnit report"):
        check_junit(tmp_path / "absent.xml", 10)


def test_policy_file_is_canonical_json() -> None:
    raw = (ROOT / "tools/qualification/frozen_science_e9.json").read_bytes()
    assert raw == (json.dumps(json.loads(raw), indent=2) + "\n").encode("utf-8")


def test_preservation_pin_check_accepts_only_the_exact_recorded_mismatches(tmp_path: Path) -> None:
    def sha(data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

    (tmp_path / "kept.py").write_bytes(b"kept\n")
    (tmp_path / "working_tree.py").write_bytes(b"lf\n")
    (tmp_path / ".gitattributes").write_bytes(b"new\n")
    pins = {"kept.py": sha(b"kept\n"), "working_tree.py": sha(b"lf\r\n"), ".gitattributes": sha(b"old\n")}
    (tmp_path / "manifest.json").write_text(json.dumps({"tracked_files": pins}), encoding="utf-8")
    entry = {
        "preservation_manifest": "manifest.json",
        "working_tree_pins": {"working_tree.py": pins["working_tree.py"]},
        "superseded_pins": {".gitattributes": {"pinned": pins[".gitattributes"], "current_sha256": sha(b"new\n")}},
    }
    assert check_preservation_pins(tmp_path, entry) == {"pins": 3, "verified": 1, "recorded_not_reproducible": 1}
    (tmp_path / "kept.py").write_bytes(b"changed\n")
    with pytest.raises(FrozenScienceError, match="unexpected mismatches"):
        check_preservation_pins(tmp_path, entry)
    (tmp_path / "kept.py").write_bytes(b"kept\n")
    (tmp_path / "working_tree.py").write_bytes(b"lf\r\n")
    with pytest.raises(FrozenScienceError, match="recorded but matching"):
        check_preservation_pins(tmp_path, entry)
    (tmp_path / "working_tree.py").write_bytes(b"lf\n")
    (tmp_path / ".gitattributes").write_bytes(b"other\n")
    with pytest.raises(FrozenScienceError, match="superseded"):
        check_preservation_pins(tmp_path, entry)
