"""Serial audited synthetic/static check runner with exclusive retained attempts."""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from .adoption import BASE, ROOT
from .records import canonical_bytes, sha256, strict_json, write_once

TEMP_ROOT = Path("D:/Projects/BATTLE2-test-temp")


def run(*, attempt_id: str, owner: str, kind: str, modules: list[str],
        implementation_manifest: dict, qualification_manifest: dict) -> dict:
    if (not attempt_id or any(c not in "abcdefghijklmnopqrstuvwxyz0123456789-" for c in attempt_id)
            or owner not in {"implementer", "independent_qualifier"}):
        raise ValueError("explicit opaque attempt and evidence owner required")
    outer = (TEMP_ROOT / attempt_id).resolve()
    if TEMP_ROOT.resolve() not in outer.parents:
        raise ValueError("attempt root escapes authorized test root")
    outer.mkdir(parents=True, exist_ok=False)
    for label, manifest in (("implementation", implementation_manifest),
                            ("qualification", qualification_manifest)):
        write_once(outer / (label + "_manifest.json"), manifest)
        for path, expected in manifest.items():
            raw = (ROOT / path).read_bytes()
            if sha256(raw) != expected:
                raise ValueError("pre-attempt exact source/test bytes changed")
            snapshot = outer / "source_snapshot" / path
            snapshot.parent.mkdir(parents=True, exist_ok=True)
            if snapshot.exists():
                if snapshot.read_bytes() != raw:
                    raise ValueError("snapshot source mismatch")
            else:
                snapshot.write_bytes(raw)
    if kind == "pytest":
        if not modules or any(not (p.startswith("engine/tests/test_v6_e9_v2_")
                                   and p.endswith(".py") and p in qualification_manifest) for p in modules):
            raise ValueError("only explicitly manifested audited v2 synthetic tests allowed")
        command = [sys.executable, "-X", "utf8", "-m", "pytest", *modules,
                   "-o", "addopts=-q", "-p", "no:cacheprovider",
                   "-p", "tools.research.v6.e9.v2.qualification_guard",
                   "--basetemp", str(outer / "temp"), "--junitxml", str(outer / "results.xml")]
    elif kind == "ruff":
        command = [sys.executable, "-X", "utf8", "-m", "ruff", "check", *modules]
    elif kind == "mypy":
        if modules not in (["engine/src/battle_engine"], ["client/src/battle_client"]):
            raise ValueError("separate registered type-check roots required")
        command = [sys.executable, "-X", "utf8", "-m", "mypy", *modules,
                   "--cache-dir", str(outer / "mypy-cache")]
    else:
        raise ValueError("unaudited check kind")
    env = {**os.environ, "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1", "PYTHONUTF8": "1"}
    write_once(outer / "started.json", {"owner": owner, "kind": kind, "modules": modules,
                                        "command": command, "status": "STARTED"})
    with (outer / "stdout.log").open("xb") as out, (outer / "stderr.log").open("xb") as err:
        completed = subprocess.run(command, cwd=ROOT, env=env, stdout=out, stderr=err, check=False)
    counts = None
    if (outer / "results.xml").exists():
        suites = ET.parse(outer / "results.xml").getroot()
        cases = list(suites.iter("testcase"))
        counts = {"collected": len(cases), "passed": sum(
            not any(c.find(k) is not None for k in ("failure", "error", "skipped")) for c in cases),
            "failed": sum(c.find("failure") is not None for c in cases),
            "errors": sum(c.find("error") is not None for c in cases),
            "skipped": sum(c.find("skipped") is not None for c in cases)}
    report = {"attempt_id": attempt_id, "owner": owner, "kind": kind, "modules": modules,
              "exit_code": completed.returncode, "counts": counts,
              "implementation_manifest_sha256_raw": sha256(canonical_bytes(implementation_manifest) + b"\n"),
              "qualification_manifest_sha256_raw": sha256(canonical_bytes(qualification_manifest) + b"\n"),
              "retained_artifact_digests": {name: sha256((outer / name).read_bytes())
                  for name in ("stdout.log", "stderr.log", "started.json", "results.xml")
                  if (outer / name).exists()},
              "execution": "LOCKED", "historical_coverage": "NOT ESTABLISHED",
              "requirement_C": "NOT ESTABLISHED"}
    report["source_bytes_unchanged_during_attempt"] = all(
        sha256((ROOT / path).read_bytes()) == expected
        for manifest in (implementation_manifest, qualification_manifest)
        for path, expected in manifest.items())
    write_once(outer / "completed.json", report)
    write_once(BASE / (attempt_id + ".json"), report)
    return report


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--attempt-id", required=True)
    p.add_argument("--owner", required=True)
    p.add_argument("--kind", required=True)
    p.add_argument("--implementation-manifest", type=Path, required=True)
    p.add_argument("--qualification-manifest", type=Path, required=True)
    p.add_argument("modules", nargs="*")
    a = p.parse_args()
    result = run(attempt_id=a.attempt_id, owner=a.owner, kind=a.kind, modules=a.modules,
                 implementation_manifest=strict_json(a.implementation_manifest.read_bytes()),
                 qualification_manifest=strict_json(a.qualification_manifest.read_bytes()))
    print(canonical_bytes(result).decode())


if __name__ == "__main__":
    main()
