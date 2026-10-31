"""Frozen E9 science: current-tree evidence guard and historical verification.

Two separate guarantees, both governed by ``frozen_science_e9.json`` beside
this file:

``guard``
    The current development tree has not modified protected V6/E9 research
    evidence. Expected identities are read from the pinned historical
    snapshot commit -- an immutable, content-addressed object -- never
    regenerated from the checkout under test. Requires the snapshot commit
    in the local object store (a full-history clone).

``verify-snapshot``
    A checkout of the historical snapshot is exactly the pinned commit and
    tree, is unmodified, and its own frozen E9 boundary verifies
    (``load_protocol(verify=True)`` and the E9 v2 inherited-source check)
    using the snapshot's own code.

``run-historical``
    Inside a verified snapshot checkout, run the original, unmodified
    historical inventory with the invocations it was qualified with (the
    E9 v2 modules through the recorded ``qualification_run.py`` command and
    its entropy/match-execution guard), then require each JUnit report to
    hold exactly the pinned number of cases with no failure and no error.

Nothing here draws entropy, writes research evidence or executes an E9
experiment. E9 remains LOCKED; Requirement C remains NOT ESTABLISHED.
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
POLICY = Path(__file__).with_name("frozen_science_e9.json")


class FrozenScienceError(RuntimeError):
    """A frozen-science identity or verification did not hold."""


def load_policy(path: Path = POLICY) -> dict[str, Any]:
    policy = json.loads(path.read_text(encoding="utf-8"))
    if policy.get("schema") != "bytefray.qualification.frozen_science" or policy.get("version") != 1:
        raise FrozenScienceError(f"{path} is not a version 1 frozen-science policy")
    return policy


def _git(repo: Path, *args: str, binary: bool = False) -> Any:
    result = subprocess.run(["git", *args], cwd=repo, capture_output=True, check=False)
    if result.returncode != 0:
        raise FrozenScienceError(
            f"git {' '.join(args)} failed in {repo}: {result.stderr.decode('utf-8', 'replace').strip()}"
        )
    return result.stdout if binary else result.stdout.decode("utf-8")


def in_scope(path: str, scopes: dict[str, list[str]]) -> bool:
    return any(path.startswith(prefix) for prefix in scopes["prefixes"]) or any(
        fnmatch.fnmatchcase(path, pattern) for pattern in scopes["patterns"]
    )


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def manifest_digest(entries: dict[str, str]) -> str:
    """SHA-256 of ``"<sha256>  <path>\\n"`` lines in path order."""

    return _sha256("".join(f"{entries[p]}  {p}\n" for p in sorted(entries)).encode("utf-8"))


def anchor_manifest(repo: Path, commit: str, scopes: dict[str, list[str]]) -> dict[str, str]:
    """Raw-byte SHA-256 of every protected blob in the immutable anchor commit."""

    listing = _git(repo, "ls-tree", "-r", "-z", "--full-tree", commit, binary=True)
    blobs: list[tuple[str, str]] = []
    for record in listing.split(b"\0"):
        if not record:
            continue
        meta, path_bytes = record.split(b"\t", 1)
        mode, kind, oid = meta.decode("ascii").split()
        path = path_bytes.decode("utf-8")
        if not in_scope(path, scopes):
            continue
        if kind != "blob" or mode not in ("100644", "100755"):
            raise FrozenScienceError(f"protected anchor entry {path} is a {kind} ({mode}), not a regular file")
        blobs.append((path, oid))
    batch = subprocess.run(
        ["git", "cat-file", "--batch"], cwd=repo, capture_output=True, check=False,
        input="".join(f"{oid}\n" for _, oid in blobs).encode("ascii"),
    )
    if batch.returncode != 0:
        raise FrozenScienceError("git cat-file could not read the protected anchor blobs")
    out, offset, result = batch.stdout, 0, {}
    for path, oid in blobs:
        end = out.index(b"\n", offset)
        header = out[offset:end].decode("ascii").split()
        if header[0] != oid or header[1] != "blob":
            raise FrozenScienceError(f"anchor blob {oid} for {path} is unavailable")
        size = int(header[2])
        result[path] = _sha256(out[end + 1:end + 1 + size])
        offset = end + 1 + size + 1
    return result


def current_manifest(repo: Path, scopes: dict[str, list[str]]) -> tuple[dict[str, str], list[str]]:
    """Raw working-tree SHA-256 of every tracked protected path, and untracked additions."""

    tracked = [p for p in _git(repo, "ls-files", "-z").split("\0") if p and in_scope(p, scopes)]
    untracked = [
        p for p in _git(repo, "ls-files", "-z", "--others", "--exclude-standard").split("\0")
        if p and in_scope(p, scopes)
    ]
    result = {}
    for path in tracked:
        file = repo / path
        result[path] = _sha256(file.read_bytes()) if file.is_file() else "<missing>"
    return result, sorted(untracked)


def guard(repo: Path = ROOT, policy: dict[str, Any] | None = None) -> dict[str, Any]:
    """Fail closed unless every protected path is byte-identical to the anchor."""

    policy = policy or load_policy()
    protected = policy["protected_evidence"]
    anchor = protected["anchor_commit"]
    if _git(repo, "cat-file", "-t", anchor).strip() != "commit":
        raise FrozenScienceError(f"anchor {anchor} is not a commit")
    tree = _git(repo, "rev-parse", f"{anchor}^{{tree}}").strip()
    if tree != protected["anchor_tree"]:
        raise FrozenScienceError(f"anchor {anchor} has tree {tree}, not the pinned {protected['anchor_tree']}")
    expected = anchor_manifest(repo, anchor, protected["scopes"])
    if len(expected) != protected["files"] or manifest_digest(expected) != protected["sha256_manifest"]:
        raise FrozenScienceError(
            f"the anchor's protected manifest ({len(expected)} files, {manifest_digest(expected)}) "
            f"differs from the pinned identity ({protected['files']} files, {protected['sha256_manifest']})"
        )
    current, untracked = current_manifest(repo, protected["scopes"])
    changed = sorted(p for p in expected.keys() & current.keys() if expected[p] != current[p])
    removed = sorted(expected.keys() - current.keys())
    added = sorted((current.keys() - expected.keys()) | set(untracked))
    if changed or removed or added:
        lines = [f"  changed: {p}" for p in changed] + [f"  removed: {p}" for p in removed]
        lines += [f"  added:   {p}" for p in added]
        raise FrozenScienceError(
            "protected frozen-science evidence differs from the immutable anchor "
            f"{anchor}:\n" + "\n".join(lines)
        )
    return {"anchor": anchor, "files": len(expected), "sha256_manifest": protected["sha256_manifest"]}


def verify_snapshot(source: Path, policy: dict[str, Any] | None = None) -> dict[str, Any]:
    """Verify a historical checkout's identity, cleanliness and own frozen boundary."""

    policy = policy or load_policy()
    snapshot = policy["historical_snapshot"]
    head = _git(source, "rev-parse", "HEAD").strip()
    tree = _git(source, "rev-parse", "HEAD^{tree}").strip()
    if (head, tree) != (snapshot["commit"], snapshot["tree"]):
        raise FrozenScienceError(
            f"{source} is {head} (tree {tree}); expected {snapshot['commit']} (tree {snapshot['tree']})"
        )
    dirty = _git(source, "status", "--porcelain", "--untracked-files=no").strip()
    if dirty:
        raise FrozenScienceError(f"historical checkout has tracked modifications:\n{dirty}")
    inventory = policy["historical_e9_inventory"]
    for entry in inventory["modules"]:
        module, _, test = entry.partition("::")
        source_file = source / module
        if not source_file.is_file():
            raise FrozenScienceError(f"historical inventory module {module} is absent at {head}")
        if test and f"\ndef {test.split('[', 1)[0]}(" not in source_file.read_text(encoding="utf-8"):
            raise FrozenScienceError(f"historical inventory test {entry} is absent at {head}")
    # The snapshot's own, unmodified verifiers -- not a reimplementation.
    probe = (
        "import sys\n"
        "sys.path.insert(0, '.')\n"
        "from tools.research.v6.e9.protocol import load_protocol\n"
        "from tools.research.v6.e9.v2.scientific import verify_inherited_sources\n"
        "body = load_protocol(verify=True)\n"
        "verify_inherited_sources()\n"
        "print(body['engine_source']['files'])\n"
    )
    result = subprocess.run([sys.executable, "-I", "-c", probe], cwd=source, capture_output=True, text=True,
                            check=False)
    if result.returncode != 0:
        raise FrozenScienceError(
            "the historical snapshot's frozen E9 boundary did not verify:\n" + result.stderr.strip()
        )
    return {"commit": head, "tree": tree, "engine_source_files": int(result.stdout.strip())}


def check_junit(report: Path, expected_collected: int) -> dict[str, int]:
    """Require exactly the pinned inventory size and no failure or error."""

    try:
        root = ET.parse(report).getroot()
    except (OSError, ET.ParseError) as exc:
        raise FrozenScienceError(f"no readable JUnit report at {report}: {exc}") from exc
    suites = [root] if root.tag == "testsuite" else list(root.iter("testsuite"))
    counts = {key: sum(int(s.get(key, 0)) for s in suites) for key in ("tests", "failures", "errors", "skipped")}
    if counts["tests"] != expected_collected:
        raise FrozenScienceError(f"historical E9 inventory ran {counts['tests']} cases; expected {expected_collected}")
    if counts["failures"] or counts["errors"]:
        raise FrozenScienceError(
            f"historical E9 inventory: {counts['failures']} failed, {counts['errors']} errors (integrity failure)"
        )
    return counts


def check_preservation_pins(source: Path, entry: dict[str, Any]) -> dict[str, int]:
    """Bound a not-reproducible preservation assertion to exactly its recorded pins.

    Read-only: every pin of the snapshot's preservation manifest must match
    the checkout's raw bytes except exactly the recorded working-tree pins
    (with exactly their recorded values) and the superseded entries (whose
    current bytes must equal their recorded superseding SHA-256).
    """

    pins = json.loads((source / entry["preservation_manifest"]).read_bytes())["tracked_files"]
    def current(path: str) -> str | None:
        file = source / path
        return _sha256(file.read_bytes()) if file.is_file() else None

    mismatched = {p: d for p, d in pins.items() if current(p) != d}
    recorded = entry["working_tree_pins"]
    superseded = entry["superseded_pins"]
    if set(mismatched) != set(recorded) | set(superseded):
        unexpected = sorted(set(mismatched) - set(recorded) - set(superseded))
        absent = sorted((set(recorded) | set(superseded)) - set(mismatched))
        raise FrozenScienceError(
            f"preservation pins: unexpected mismatches {unexpected}, recorded but matching {absent}"
        )
    if any(pins[p] != recorded[p] for p in recorded):
        raise FrozenScienceError("preservation pins: a recorded working-tree pin differs from the manifest")
    for path, values in superseded.items():
        if pins[path] != values["pinned"] or current(path) != values["current_sha256"]:
            raise FrozenScienceError(f"preservation pins: superseded {path} is not the recorded superseding bytes")
    return {"pins": len(pins), "verified": len(pins) - len(mismatched), "recorded_not_reproducible": len(recorded)}


def run_historical(source: Path, work: Path, policy: dict[str, Any] | None = None) -> dict[str, Any]:
    """Run every pinned historical invocation; fail on any count, failure or error."""

    policy = policy or load_policy()
    inventory = policy["historical_e9_inventory"]
    outcome: dict[str, Any] = {}
    problems: list[str] = []
    for entry in inventory["not_reproducible_from_commits"]:
        try:
            outcome[entry["node_id"]] = check_preservation_pins(source, entry)
        except FrozenScienceError as exc:
            problems.append(f"{entry['node_id']}: {exc}")
    for index, run in enumerate(inventory["runs"]):
        name = run["name"]
        report = work / f"{name}.xml"
        # Short temp paths, as the recorded native POSIX qualification used
        # (/tmp/<attempt>/temp): AF_UNIX socket paths are limited to 108 bytes.
        temp = work / f"t{index}"
        temp.mkdir(parents=True, exist_ok=False)
        command = [sys.executable, "-X", "utf8", "-m", "pytest", *run["selection"], *run["pytest_args"],
                   "--basetemp", str(temp / "temp"), "--junitxml", str(report)]
        for node in run["deselect"]:
            command += ["--deselect", node]
        print(f"[{name}] {' '.join(command)}", flush=True)
        completed = subprocess.run(command, cwd=source, env={**os.environ, **run["env"]}, check=False)
        try:
            outcome[name] = {**check_junit(report, run["expected_collected"]), "exit_code": completed.returncode}
        except FrozenScienceError as exc:
            problems.append(f"{name}: {exc}")
            continue
        if completed.returncode != 0:
            problems.append(f"{name}: pytest exited {completed.returncode}")
    if problems:
        raise FrozenScienceError("; ".join(problems))
    return outcome


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    commands = parser.add_subparsers(dest="command", required=True)
    guard_cmd = commands.add_parser("guard", help="verify protected evidence in the current tree")
    guard_cmd.add_argument("--repo", type=Path, default=ROOT)
    snap_cmd = commands.add_parser("verify-snapshot", help="verify a historical snapshot checkout")
    snap_cmd.add_argument("--source", type=Path, required=True)
    run_cmd = commands.add_parser("run-historical", help="run the historical inventory in a snapshot checkout")
    run_cmd.add_argument("--source", type=Path, required=True)
    run_cmd.add_argument("--work", type=Path, required=True, help="basetemp/report root outside the snapshot")
    args = parser.parse_args(argv)
    policy = load_policy()
    try:
        if args.command == "guard":
            outcome: Any = guard(args.repo, policy)
        elif args.command == "verify-snapshot":
            outcome = verify_snapshot(args.source, policy)
        else:
            outcome = run_historical(args.source.resolve(), args.work.resolve(), policy)
    except FrozenScienceError as exc:
        print(f"FROZEN SCIENCE FAILURE: {exc}", file=sys.stderr)
        return 1
    print(json.dumps({"command": args.command, "result": outcome}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
