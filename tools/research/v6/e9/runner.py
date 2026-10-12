"""Locked collection/analysis entry points with same-attempt native capture.

There is deliberately no seed-generation command. An external supervisor
must supply infrastructure and fencing proof; worker exit codes do not.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from collections import Counter
from dataclasses import asdict
from pathlib import Path
from typing import Any

from battle_engine.agent_parameters import resolve_entrant_parameters
from battle_engine.agents import agent_spec_from_dir
from battle_engine.config import Config, Weights
from battle_engine.match_service import (
    MatchEntrant,
    MatchRequest,
    NativeMatchService,
    canonical_match_id,
)
from battle_engine.placement import resolve_direct_match_starts
from battle_engine.ruleset_policy import resolve_ruleset_policy

from .artifacts import validate
from .collection import (
    Dispatcher,
    Journal,
    RecoveryEvidence,
    WorkerInterrupted,
    require_execution_approval,
)
from .instrument import assemble, require_qualified, seal
from .protocol import (
    PROTOCOL_DIGEST,
    PROTOCOL_ID,
    ROOT,
    Cell,
    ExecutionLocked,
    IntegrityError,
    canonical,
    cells,
    digest,
    file_digest,
    load_protocol,
    package_bytes,
    read_json,
    verify_package,
    write_once,
)

DOMAIN = {"bits": 64, "encoding": "big-endian", "source": "OS CSPRNG", "ordering": "accepted draw order"}


def private_root(instrument_digest: str) -> Path:
    token = digest(b"bytefray-e9-private-root-v1\n" + bytes.fromhex(PROTOCOL_DIGEST)
                   + bytes.fromhex(instrument_digest))[:16]
    return ROOT / "runs" / ("research_v6_e9_" + token)


def check_private(root: Path) -> None:
    relative = root.resolve().relative_to(ROOT.resolve()).as_posix()
    if not relative.startswith("runs/research_v6_e9_"):
        raise IntegrityError("experimental data root is outside the registered private location")
    ignored = subprocess.run(["git", "check-ignore", "--quiet", relative + "/seed_payload.json"],
                             cwd=ROOT, check=False, capture_output=True)
    tracked = subprocess.check_output(["git", "ls-files", "--", relative], cwd=ROOT)
    if ignored.returncode != 0 or tracked.strip():
        raise IntegrityError("private evidence root is not ignored or has tracked data")


def verify_seeds(root: Path, instrument_digest: str, commitment: dict[str, Any]) -> list[int]:
    """Verify a later authorized, previously sealed seed payload; never draw values."""
    check_private(root)
    payload_path = root / "seed_payload.json"
    payload = read_json(payload_path)
    if payload_path.read_bytes() != canonical(payload) + b"\n":
        raise IntegrityError("seed payload is not canonical ordered UTF-8 JSON")
    salt = (root / "seed_salt.bin").read_bytes()
    exclusion = read_json(root / "exclusion_inventory.json")
    if (len(salt) != 32 or payload.get("protocol_digest") != PROTOCOL_DIGEST
            or payload.get("instrument_digest") != instrument_digest or payload.get("domain") != DOMAIN
            or payload.get("exclusion_inventory_digest") != file_digest(root / "exclusion_inventory.json")
            or exclusion.get("complete") is not True
            or exclusion.get("coverage") != {"E6": True, "E8": True, "all_prior_match_qualification": True}
            or not exclusion.get("provenance")):
        raise IntegrityError("seed/exclusion identity or completeness evidence failed")
    # Every referenced exclusion source remains immutable. Completeness is a
    # separately approved inventory prerequisite, not inferred from filenames.
    for source in exclusion["provenance"]:
        if file_digest(Path(source["path"])) != source["sha256_raw"]:
            raise IntegrityError("exclusion provenance changed")
    entries = payload.get("positions", [])
    if (len(entries) != 1412 or any(set(e) != {"position", "value_hex"}
            or type(e["position"]) is not int or e["position"] != i
            or not isinstance(e["value_hex"], str) or len(e["value_hex"]) != 16
            or any(c not in "0123456789abcdef" for c in e["value_hex"])
            for i, e in enumerate(entries, 1))):
        raise IntegrityError("seed count/domain/position ordering failed")
    seeds = [int(e["value_hex"], 16) for e in entries]
    excluded = {int(v, 16) for v in exclusion["match_seeds_hex"]}
    computed = digest(b"bytefray-e9-seed-commitment-v1\n" + salt + payload_path.read_bytes())
    if (len(set(seeds)) != 1412 or set(seeds) & excluded
            or commitment.get("commitment") != computed or commitment.get("N") != 1412
            or commitment.get("protocol_digest") != PROTOCOL_DIGEST
            or commitment.get("instrument_digest") != instrument_digest
            or commitment.get("exclusion_inventory_digest") != payload["exclusion_inventory_digest"]):
        raise IntegrityError("private seed commitment/uniqueness/exclusion failed")
    return seeds


def materialize(root: Path, protocol: dict[str, Any]) -> dict[str, dict[str, Any]]:
    defaults: dict[str, dict[str, Any]] = {}
    for name in (*protocol["historical_packages"], *protocol["prospective_packages"]):
        target = root / "agents" / name
        if name in protocol["historical_packages"]:
            source = ROOT / "tools/research/v6/e8/fixtures/agents" / name
            data = {f: (source / f).read_bytes() for f in ("agent.py", "agent.yaml")}
        else:
            row = next(r for r, p in protocol["physical_packages"].items() if p == name)
            data = package_bytes(row, protocol)
        target.mkdir(parents=True, exist_ok=True)
        for filename, content in data.items():
            destination = target / filename
            if destination.exists():
                if destination.read_bytes() != content:
                    raise IntegrityError("materialized evaluation package changed")
            else:
                with destination.open("xb") as handle:
                    handle.write(content)
                    handle.flush()
                    os.fsync(handle.fileno())
        verify_package(name, target, protocol)
        spec = agent_spec_from_dir(target)
        defaults[name] = resolve_entrant_parameters(api_version=spec.api_version,
            schema=spec.parameter_schema, legacy_defaults=spec.defaults, path=target)
    return defaults


def native_request(root: Path, attempt: Path, cell: Cell, seed: int,
                   protocol: dict[str, Any], defaults: dict[str, dict[str, Any]]) -> MatchRequest:
    names = cell.packages(protocol)
    policy = protocol["effective_t8"]["policy"]
    live = asdict(resolve_ruleset_policy(policy["ruleset_id"]))
    if canonical(live) != canonical(policy):
        raise IntegrityError("complete effective T8 policy drift")
    config = protocol["effective_t8"]["config_without_seed"]
    starts = resolve_direct_match_starts(ruleset_id=policy["ruleset_id"], arena_size=512,
        entrant_count=2, supplied_starts=(None, None), seed=seed)
    entrants = []
    for seat, name, start in zip(("A", "B"), names, starts):
        package = root / "agents" / name
        verify_package(name, package, protocol)
        spec = agent_spec_from_dir(package)
        actual = resolve_entrant_parameters(api_version=spec.api_version, schema=spec.parameter_schema,
                                            legacy_defaults=spec.defaults, path=package)
        if actual != defaults[name]:
            raise IntegrityError("materialized default parameters changed")
        entrants.append(MatchEntrant.python(seat, name, start, spec, actual))
    return MatchRequest(config=Config(arena_size=512, instr_per_tick=8, seed=seed,
                                      weights=Weights(**config["weights"]), win_mode=config["win_mode"]),
        entrants=tuple(entrants), max_ticks=1000, replay_path=attempt / "replay.jsonl",
        verbose=False, trace_path=attempt / "trace.jsonl", agent_call_timeout=None,
        ruleset_id=policy["ruleset_id"])


def manifest(root: Path, protocol: dict[str, Any], execution: dict[str, Any]) -> None:
    target = root / "cell_manifest.jsonl"
    expected_count = protocol["sample"]["payoff_cells"]
    if target.exists():
        with target.open("rb") as handle:
            for cell in cells(protocol):
                if handle.readline() != canonical({"cell": asdict(cell), "identity": cell.identity,
                    "packages": cell.packages(protocol), "execution_digest": digest(canonical(execution))}) + b"\n":
                    raise IntegrityError("complete cell manifest changed or is incomplete")
            if handle.read(1):
                raise IntegrityError("cell manifest contains surplus cells")
    else:
        with target.open("xb") as handle:
            count = 0
            execution_digest = digest(canonical(execution))
            for cell in cells(protocol):
                handle.write(canonical({"cell": asdict(cell), "identity": cell.identity,
                    "packages": cell.packages(protocol), "execution_digest": execution_digest}) + b"\n")
                count += 1
            handle.flush()
            os.fsync(handle.fileno())
        if count != expected_count:
            raise IntegrityError("registered manifest count failed")


def preflight(authorization: Path | None, commitment_path: Path, *, bind_manifest: bool = True
              ) -> tuple[dict[str, Any], str, Path, list[int], dict]:
    protocol = load_protocol()
    instrument_digest = require_qualified()
    commitment = read_json(commitment_path)
    require_execution_approval(authorization, protocol_id=PROTOCOL_ID,
        instrument_digest=instrument_digest, seed_commitment=commitment["commitment"])
    root = private_root(instrument_digest)
    seeds = verify_seeds(root, instrument_digest, commitment)
    defaults = materialize(root, protocol)
    execution = {"protocol_id": PROTOCOL_ID, "instrument_digest": instrument_digest,
                 "seed_commitment": commitment["commitment"], "effective_t8": protocol["effective_t8"],
                 "defaults": defaults, "aliases": protocol["logical_aliases"]}
    boundary = root / "execution.json"
    if boundary.exists():
        if canonical(read_json(boundary)) != canonical(execution):
            raise IntegrityError("collection boundary changed")
    else:
        write_once(boundary, execution)
    if bind_manifest:
        manifest(root, protocol, execution)
    return protocol, instrument_digest, root, seeds, execution


def collect(authorization: Path | None, commitment_path: Path) -> None:
    protocol, instrument_digest, root, seeds, execution = preflight(authorization, commitment_path)
    for cell in cells(protocol):
        # Recheck frozen sources and qualified instrument before every dispatch.
        load_protocol()
        if require_qualified() != instrument_digest:
            raise IntegrityError("instrument changed during collection")
        journal = Journal(root / "cells", cell, {"execution": execution,
                           "seed_hex": f"{seeds[cell.position - 1]:016x}", "packages": cell.packages(protocol)})

        def proof(current: Journal) -> RecoveryEvidence | None:
            path = root / "supervisor" / (current.cell.identity + ".json")
            return RecoveryEvidence.read(path) if path.exists() else None

        def backend(attempt: Path, cell: Cell = cell, journal: Journal = journal) -> None:
            # Native execution occurs in a separate worker. An ordinary failure
            # is non-retryable; only external proof can identify infrastructure.
            command = [sys.executable, "-B", "-m", "tools.research.v6.e9.runner", "worker", "--authorization", str(authorization),
                       "--commitment", str(commitment_path), "--cell", cell.identity,
                       "--attempt", str(attempt)]
            completed = subprocess.run(command, cwd=ROOT, capture_output=True, check=False)
            for name, output in (("worker-stdout.log", completed.stdout), ("worker-stderr.log", completed.stderr)):
                with (attempt / name).open("xb") as handle:
                    handle.write(output)
                    handle.flush()
                    os.fsync(handle.fileno())
            write_once(attempt / "worker-exit.json", {"returncode": completed.returncode})
            if completed.returncode:
                if proof(journal) is not None:
                    raise WorkerInterrupted()
                raise IntegrityError("worker failed without independent infrastructure evidence")

        def validator(attempt: Path, cell: Cell = cell) -> dict[str, str]:
            load_protocol()
            require_qualified()
            for name in cell.packages(protocol):
                verify_package(name, root / "agents" / name, protocol)
            expected = canonical_match_id(native_request(root, attempt, cell, seeds[cell.position - 1],
                                                         protocol, execution["defaults"]))
            return validate(attempt, cell, protocol, seed=seeds[cell.position - 1],
                            package_names=cell.packages(protocol), expected_match_id=expected)

        Dispatcher(backend, validator, proof).dispatch(journal)


def finalize(authorization: Path | None, commitment_path: Path) -> dict[str, Any]:
    protocol, instrument_digest, root, seeds, execution = preflight(authorization, commitment_path)
    counts: Counter[str] = Counter({"planned": 900856, "missing": 0, "failed": 0, "duplicates": 0,
                                   "eligible_failures": 0, "recovery_starts": 0,
                                   "recovered_completions": 0, "exhausted_recoveries": 0})
    records = []
    expected_ids: set[str] = set()
    for cell in cells(protocol):
        expected_ids.add(cell.identity)
        directory = root / "cells" / cell.identity
        if not directory.exists():
            counts["missing"] += 1
            continue
        try:
            journal = Journal(root / "cells", cell, {"execution": execution,
                "seed_hex": f"{seeds[cell.position - 1]:016x}", "packages": cell.packages(protocol)})
            events = journal.events()
            counts["started"] += sum(e["kind"] == "started" for e in events)
            counts["completed"] += sum(e["kind"] == "completed" for e in events)
            counts["eligible_failures"] += sum(e["kind"] == "recovery_eligible" for e in events)
            counts["recovery_starts"] += sum(e["kind"] == "started" and e["attempt"] == 2 for e in events)
            counts["exhausted_recoveries"] += sum(e.get("reason") == "recovery_exhausted" for e in events)
            path, accounting = journal.validate_attempts()
            # Re-derive diagnostics independently from the immutable raw evidence.
            expected = canonical_match_id(native_request(root, path, cell, seeds[cell.position - 1],
                                                         protocol, execution["defaults"]))
            validate(path, cell, protocol, seed=seeds[cell.position - 1], package_names=cell.packages(protocol),
                     expected_match_id=expected)
            diagnostic_record = read_json(path / "diagnostic.json")
            diagnostic_record["execution_provenance"] = {
                "attempt_ledger_digest": file_digest(journal.root / "events" / f"{len(events)-1:06d}.json"),
                "artifact_digests": next(e["artifact_digests"] for e in events if e["kind"] == "validated")}
            records.append(diagnostic_record)
            counts["validated"] += 1
            counts["recovered_completions"] += accounting["recovered_completions"]
        except (IntegrityError, OSError, KeyError, TypeError, ValueError):
            counts["failed"] += 1
    actual = {path.name for path in (root / "cells").glob("*") if path.is_dir()}
    counts["duplicates"] = len(actual - expected_ids)
    if counts["missing"] or counts["failed"] or counts["duplicates"]:
        record = {"schema": "bytefray.v6.e9.registered_result", "version": 1, "protocol_id": PROTOCOL_ID,
                  "instrument_digest": instrument_digest, "collection": dict(counts),
                  "classification": {"priority": 1, "primary": "NOT EVALUABLE"},
                  "requirement_C": "NOT ESTABLISHED"}
    else:
        record = assemble(records, protocol, instrument_digest, dict(counts))
    seal(record, root / "final_registered_result.json")
    return record


def worker(authorization: Path | None, commitment_path: Path, identity: str, attempt: Path) -> None:
    protocol, _, root, seeds, execution = preflight(authorization, commitment_path, bind_manifest=False)
    retained = read_json(attempt.parent / "identity.json")
    cell = Cell(**retained["cell"])
    if cell.identity != identity or attempt.parent != root / "cells" / identity:
        raise IntegrityError("worker cell/attempt is outside the fixed private rectangle")
    journal = Journal(root / "cells", cell, {"execution": execution,
        "seed_hex": f"{seeds[cell.position - 1]:016x}", "packages": cell.packages(protocol)})
    events = journal.events()
    if not events or events[-1]["kind"] != "started" or attempt.name != f"attempt-{events[-1]['attempt']:02d}":
        raise IntegrityError("worker lacks an exclusive durable started attempt")
    if any(attempt.iterdir()):
        raise IntegrityError("worker may never overwrite existing attempt evidence")
    request = native_request(root, attempt, cell, seeds[cell.position - 1], protocol, execution["defaults"])
    # A durable exclusive worker claim prevents duplicate dispatch of a started
    # attempt even if two collectors race after reading the same ledger.
    write_once(attempt / "worker-claim.json", {"cell_identity": identity, "binding_digest": journal.binding})
    try:
        NativeMatchService().run(request)
    except Exception as exc:
        if not isinstance(exc, OSError) or isinstance(exc, TimeoutError):
            write_once(attempt / "semantic-integrity-failure.json", {"failed": True})
        raise
    write_once(attempt / "worker-completion.json", {"completed": True, "cell_identity": identity})


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("check", "collect", "finalize", "worker"))
    parser.add_argument("--authorization", type=Path)
    parser.add_argument("--commitment", type=Path)
    parser.add_argument("--cell")
    parser.add_argument("--attempt", type=Path)
    args = parser.parse_args()
    try:
        if args.command == "check":
            load_protocol()
            sha = require_qualified()
            print(f"FROZEN {PROTOCOL_ID}; qualified instrument {sha}; execution LOCKED")
        else:
            if args.authorization is None or args.commitment is None:
                raise ExecutionLocked("separate payoff authorization and seed commitment required")
            if args.command == "collect":
                collect(args.authorization, args.commitment)
            elif args.command == "finalize":
                finalize(args.authorization, args.commitment)
            elif args.cell is None or args.attempt is None:
                raise IntegrityError("worker requires its durable cell and attempt identity")
            else:
                worker(args.authorization, args.commitment, args.cell, args.attempt)
    except (IntegrityError, OSError, KeyError, TypeError, ValueError):
        # No raw seed-bearing paths, values or agent output enter public logs.
        print("E9 gate refused: missing authorization, changed identity or unusable evidence", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
