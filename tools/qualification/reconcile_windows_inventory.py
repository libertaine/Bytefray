"""Export M1-6A inventories and privacy-filtered JUnit records without running tests.

Run from the repository root after the separately recorded supplemental checks:
    python -B tools/qualification/reconcile_windows_inventory.py

Original local XML/logs remain unchanged. Exported XML preserves case identities,
outcomes, timings and suite totals; hostnames, captured streams and absolute local
paths are omitted. Raw input hashes allow reviewers to identify the originals.
"""

from __future__ import annotations

import hashlib
import json
import re
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOCAL = ROOT / "work/m1_6a_closure_20261011"
OUTPUT = ROOT / "docs/v6/evidence/m1_6a_windows"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def cases(path: Path) -> dict[str, ET.Element]:
    found: dict[str, ET.Element] = {}
    for case in ET.parse(path).findall(".//testcase"):
        parts = case.attrib["classname"].split(".")
        index = next(i for i, part in enumerate(parts) if part.startswith("test_"))
        module = "/".join(parts[:index + 1]) + ".py"
        node = module + "::" + "::".join(parts[index + 1:] + [case.attrib["name"]])
        assert node not in found, node
        found[node] = case
    return found


def skip_category(message: str) -> str:
    if "POSIX symlink" in message:
        return "POSIX symlink semantics only"
    if "symlink" in message.lower():
        return "Windows symlink privilege unavailable"
    if "alternate data streams" in message:
        return "NTFS colon names are alternate data streams"
    if "BYTEFRAY_FROZEN_EXE" in message:
        return "BYTEFRAY_FROZEN_EXE unset; frozen executable qualification deferred"
    raise AssertionError(f"Unclassified skip: {message}")


def export_xml(source: Path, target: Path) -> None:
    tree = ET.parse(source)
    for element in tree.iter():
        element.attrib.pop("hostname", None)
        for child in list(element):
            if child.tag in {"system-out", "system-err", "properties"}:
                element.remove(child)
        if element.tag == "skipped":
            message = skip_category(element.attrib["message"])
            element.attrib["message"] = message
            element.text = message
    text = ET.tostring(tree.getroot(), encoding="unicode")
    # Literal malicious-input vectors (C:/evil.py, C:/outside/replay.jsonl)
    # are public test identities, not paths to evidence on this workstation.
    assert not re.search(r"[A-Za-z]:[\\/]+(?:Users|Projects|Program Files)\b", text, re.IGNORECASE)
    target.write_text(text + "\n", encoding="utf-8", newline="\n")
    # Filtering must never change the identity or outcome of any test.
    before, after = cases(source), cases(target)
    assert set(before) == set(after)
    for node in before:
        assert before[node].attrib == after[node].attrib
        assert [c.tag for c in before[node] if c.tag in {"skipped", "failure", "error"}] == [
            c.tag for c in after[node] if c.tag in {"skipped", "failure", "error"}
        ]


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    broad_path = ROOT / "work/m1_6a_windows_regression_final.xml"
    previous_path = ROOT / "work/m1_1_archive_20261010/current_regression_final.xml"
    baseline_path = ROOT / "work/m1_1_archive_20261010/baseline_frozen_71.xml"
    broad = cases(broad_path)
    previous = cases(previous_path)
    supplemental = cases(LOCAL / "supplemental_compatibility.xml")
    gui = cases(LOCAL / "client_gui.xml")
    planned = set((LOCAL / "supplemental_nodes.txt").read_text().splitlines())
    assert set(supplemental) == planned and not set(supplemental) & set(broad)
    assert (len(broad), len(supplemental), len(gui)) == (3218, 328, 7)
    assert all(c.find("failure") is None and c.find("error") is None for c in broad.values())
    assert all(not list(c) for c in [*supplemental.values(), *gui.values()])
    baseline = cases(baseline_path)
    assert len(baseline) == 71 and all(not list(c) for c in baseline.values())
    historical = set(json.loads((ROOT / "work/m1_1_archive_20261010/frozen_failure_nodes.json").read_text()))
    assert len(historical) == 72 and not historical & (set(broad) | set(supplemental))
    assert set(baseline) < historical and len(historical - set(baseline)) == 1

    modules = Counter(n.split("::")[0] for n in broad)
    supplemental_modules = Counter(n.split("::")[0] for n in supplemental)
    old_modules = Counter(n.split("::")[0] for n in previous)
    all_engine = {"engine/tests/" + p.name for p in (ROOT / "engine/tests").glob("test_*.py")}
    excluded = sorted(all_engine - set(modules))
    difference = {m: old_modules[m] for m in excluded if not Path(m).stem.startswith("test_v6_e")}
    assert len(difference) == 21 and sum(difference.values()) == 906
    assert len([m for m in modules if m.startswith("engine/")]) == 114
    skips = {n: skip_category(c.find("skipped").attrib["message"])
             for n, c in broad.items() if c.find("skipped") is not None}
    assert len(skips) == 19
    inventory = {
        "earlier_estimate": 4124,
        "broad_selected_cases": len(broad),
        "broad_module_counts": dict(sorted(modules.items())),
        "difference_module_counts": difference,
        "difference": sum(difference.values()),
        "excluded_engine_modules": {
            m: {
                "prior_current_case_count": old_modules[m],
                "historical_partition_count": sum(n.startswith(m + "::") for n in historical),
                "supplemental_current_case_count": supplemental_modules[m],
                "classification": "mixed inventory and compatibility; required cases supplemented"
                if supplemental_modules[m] else "research or experiment; outside Windows product campaign",
            } for m in excluded
        },
        "supplemental_module_counts": dict(sorted(supplemental_modules.items())),
        "skips": skips,
        "gui_cases": sorted(gui),
        "historical_partition": {
            "baseline_junit_passed": len(baseline),
            "separate_guard_case": sorted(historical - set(baseline)),
            "guard_case_pass_evidence": "M1-1 adopted Disposition 03: separate existing plugin process, 1 passed",
        },
    }
    (OUTPUT / "inventory.json").write_text(json.dumps(inventory, indent=2) + "\n", encoding="utf-8", newline="\n")
    for name, selection in [("regression_nodes", broad), ("supplemental_nodes", supplemental), ("gui_nodes", gui)]:
        (OUTPUT / (name + ".txt")).write_text("\n".join(sorted(selection)) + "\n", encoding="utf-8", newline="\n")
    (OUTPUT / "regression_modules.txt").write_text("\n".join(sorted(modules)) + "\n", encoding="utf-8", newline="\n")
    sources = [(broad_path, "regression.xml"), (LOCAL / "supplemental_compatibility.xml", "supplemental_compatibility.xml"),
               (LOCAL / "client_gui.xml", "client_gui.xml")]
    hashes = {}
    for source, name in sources:
        export_xml(source, OUTPUT / name)
        hashes[name] = {
            "original_relative_path": source.relative_to(ROOT).as_posix(),
            "original_sha256": sha(source),
            "filtered_sha256": sha(OUTPUT / name),
        }
    for path in [previous_path, baseline_path, ROOT / "work/m1_6a_windows_regression_final.log",
                 LOCAL / "qualification_before_closure.md", LOCAL / "supplemental_compatibility.log", LOCAL / "client_gui.log"]:
        hashes[path.relative_to(ROOT).as_posix()] = {"sha256": sha(path), "staged": False}
    screenshots = ROOT / "docs/screenshots/v6_alpha1_windows"
    hashes["screenshots"] = {
        p.name: {"sha256": sha(p), "bytes": p.stat().st_size,
                 "staged": not p.name.startswith(("06_", "07_"))}
        for p in sorted(screenshots.glob("*.png"))
    }
    (OUTPUT / "evidence_hashes.json").write_text(json.dumps(hashes, indent=2) + "\n", encoding="utf-8", newline="\n")
    print("Verified: 3218 broad cases, exact 906 difference, 328 supplemental passes, 7 separate GUI passes, 19 classified skips.")


if __name__ == "__main__":
    main()
