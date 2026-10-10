"""Offline verification of additive historical recovery; never invokes matches."""

from __future__ import annotations

import argparse
import ast
import hashlib
import subprocess
import zipfile
from pathlib import Path
from typing import Any

from tools.research.v6.e9.verify_historical_scope import (
    canonical,
    file_sha,
    loads,
    require,
    tournament_seed,
    values_hex,
)


def verify_addition(original: dict[str, Any], proposal: dict[str, Any],
                    witnessed: set[str]) -> set[str]:
    prior = values_hex(original["match_seeds_hex"])
    current = values_hex(proposal["match_seeds_hex"])
    require(original["complete"] is False and proposal["complete"] is False,
            "unsupported completeness")
    require(proposal["coverage"] == original["coverage"], "candidate coverage changed")
    require(current == prior | witnessed, "candidate addition lacks provenance or loses values")
    return current - prior


def verify_witness(witness: dict[str, Any], included: set[str]) -> str:
    require(witness["scope"] == "listed_witnessed_executions_only", "unproved scope expansion")
    seed = witness["recorded_seed_hex"]
    require(seed in included, "witness is not excluded")
    result_path = Path(witness["result_path"])
    replay_path = Path(witness["replay_path"])
    require(file_sha(result_path) == witness["result_sha256_raw"], "result binding changed")
    require(file_sha(replay_path) == witness["replay_sha256_raw"], "replay binding changed")
    result = loads(result_path.read_bytes())
    with replay_path.open("rb") as stream:
        header = loads(stream.readline())
    require(result["schema"] == "battle2.result" and header["schema"] == "battle2.replay",
            "unsupported artifact identity")
    for key in ("match_id", "result_id", "ruleset_id"):
        require(result[key] == header[key], "artifact identity mismatch")
    require(result["replay"]["sha256"] == witness["replay_sha256_raw"], "result replay digest mismatch")
    require(result["replay"]["replay_id"] == header["replay_id"] == result["match_id"],
            "replay association mismatch")
    require(type(result["reproducibility"]["seed"]) is int
            and type(header["config"]["seed"]) is int
            and result["reproducibility"]["seed"] == header["config"]["seed"] == int(seed, 16),
            "artifact seed mismatch")
    if "reconstruction" in witness:
        require(tournament_seed(**witness["reconstruction"]) == seed, "derivation mismatch")
        path = Path(witness["schedule_path"])
        require(file_sha(path) == witness["schedule_sha256_raw"], "schedule binding changed")
        state = loads(path.read_bytes())
        matches = [m for m in state["matches"] if m.get("match_id") == result["match_id"]]
        require(len(matches) == 1, "schedule association ambiguous")
        match = matches[0]
        require(match == witness["schedule_match"], "schedule witness changed")
        require(match["seed"] == int(seed, 16) and match["result_id"] == result["result_id"]
                and match["status"] == "completed", "schedule execution mismatch")
        inputs = witness["reconstruction"]
        require(match["round_number"] == inputs["round_number"]
                and match["entrant_ids"] == [inputs["first"], inputs["second"]],
                "schedule derivation inputs mismatch")
    return seed


def verify_attempt(response: dict[str, Any], jobs_response: dict[str, Any]) -> int:
    require(response["returncode"] == jobs_response["returncode"] == 0, "attempt unavailable")
    run = loads(response["stdout"].encode())
    jobs = loads(jobs_response["stdout"].encode())["jobs"]
    require(run["id"] == response["run_id"] == jobs_response["run_id"]
            and run["run_attempt"] == response["attempt"] == jobs_response["attempt"],
            "attempt identity mismatch")
    require(len({j["id"] for j in jobs}) == len(jobs), "duplicate job identity")
    for job in jobs:
        require(job["run_id"] == run["id"] and job["run_attempt"] == run["run_attempt"]
                and job["head_sha"] == run["head_sha"], "job attempt/source mismatch")
    return len(jobs)


def verify_default_domain(test_raw: bytes, core_raw: bytes, expected_hex: str) -> None:
    """Check the bound legacy smoke family's literal default-only Config use.

    This is a source domain, not an execution or whole-job attestation.
    """
    tree = ast.parse(test_raw.decode("utf-8-sig"))
    core = ast.parse(core_raw.decode("utf-8-sig"))
    require(all(isinstance(n, (ast.Import, ast.ImportFrom, ast.FunctionDef)) for n in tree.body),
            "unexpected smoke source structure")
    require(all(isinstance(n, ast.FunctionDef) and n.name.startswith("test_")
                for n in tree.body if isinstance(n, ast.FunctionDef)), "unexpected smoke helper")
    calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call)]
    allowed = {"Kernel", "Config", "k.run", "k.spawn", "bytes"}
    require(all(ast.unparse(n.func) in allowed for n in calls), "unbounded smoke call")
    for call in calls:
        if ast.unparse(call.func) in {"Kernel", "Config"}:
            require(not call.args and all(k.arg is not None and k.arg != "seed" for k in call.keywords),
                    "external smoke seed input")
    config = next(n for n in core.body if isinstance(n, ast.ClassDef) and n.name == "Config")
    value = next(n.value for n in config.body if isinstance(n, ast.AnnAssign)
                 and isinstance(n.target, ast.Name) and n.target.id == "seed")
    require(isinstance(value, ast.Constant) and type(value.value) is int
            and 0 <= value.value < 2**64 and f"{value.value:016x}" == expected_hex,
            "historical default mismatch")


def verify_literal_input(raw: bytes, function: str, expected: int, kind: str) -> None:
    """Read a literal historical caller input without importing its source."""
    tree = ast.parse(raw.decode("utf-8-sig"))
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == function)
    if kind == "config_seed":
        values = [k.value.value for n in ast.walk(node) if isinstance(n, ast.Call)
                  and ast.unparse(n.func) == "Config" for k in n.keywords
                  if k.arg == "seed" and isinstance(k.value, ast.Constant)]
    elif kind == "argv_seed":
        argv = next(n.value for n in node.body if isinstance(n, ast.Assign)
                    and any(isinstance(t, ast.Name) and t.id == "arguments" for t in n.targets))
        if not isinstance(argv, ast.Tuple):
            raise ValueError("unexpected argv source")
        values = []
        for i, item in enumerate(argv.elts):
            if isinstance(item, ast.Constant) and item.value == "--seed":
                require(i + 1 < len(argv.elts), "missing literal argv seed")
                following = argv.elts[i + 1]
                if not isinstance(following, ast.Constant) or not isinstance(following.value, str):
                    raise ValueError("nonliteral argv seed")
                values.append(int(following.value))
    elif kind == "cli_default":
        values = [k.value.value for n in ast.walk(node) if isinstance(n, ast.Call)
                  and n.args and isinstance(n.args[0], ast.Constant) and n.args[0].value == "--seed"
                  for k in n.keywords if k.arg == "default" and isinstance(k.value, ast.Constant)]
    else:
        raise ValueError("unsupported input kind")
    require(values == [expected] and type(expected) is int and 0 <= expected < 2**64,
            "historical literal input mismatch")


def verify_generator_source(raw: bytes) -> None:
    tree = ast.parse(raw.decode("utf-8-sig"))
    generator = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "derive_match_seed")
    reference = ast.parse(
        'material = f"battle2-tournament-v1\\0{seed}\\0{round_number}\\0{first}\\0{second}"\n'
        'return int.from_bytes(hashlib.sha256(material.encode()).digest()[:8], "big")\n'
    )
    require([ast.dump(n) for n in generator.body] == [ast.dump(n) for n in reference.body],
            "historical generator differs from independent transcription")


def verify_ci_smoke(role: dict[str, Any], included: set[str]) -> None:
    require(role["scope"] == "identified_successful_test_only" and role["seed_hex"] in included,
            "unsupported CI smoke scope")
    run_response = loads(Path(role["run_response"]).read_bytes())
    jobs_response = loads(Path(role["jobs_response"]).read_bytes())
    verify_attempt(run_response, jobs_response)
    require(run_response["run_id"] == role["run_id"] and run_response["attempt"] == role["attempt"],
            "CI smoke attempt mismatch")
    jobs = loads(jobs_response["stdout"].encode())["jobs"]
    steps = [s for j in jobs for s in j.get("steps", []) if s["name"] == role["step_name"]]
    require(len(steps) == 1 and steps[0]["conclusion"] == "success", "CI smoke step unavailable")
    tree = ast.parse(Path(role["test_source"]).read_text(encoding="utf-8-sig"))
    test = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == role["test_function"])
    calls = [n for n in ast.walk(test) if isinstance(n, ast.Call) and ast.unparse(n.func) == "engine_main"]
    require(len(calls) == 1 and len(calls[0].args) == 1 and isinstance(calls[0].args[0], ast.List),
            "unbounded CI smoke invocation")
    argv = calls[0].args[0]
    if not isinstance(argv, ast.List):
        raise ValueError("unexpected CI smoke argv source")
    flags = [n.value for n in argv.elts if isinstance(n, ast.Constant)]
    require("--seed" not in flags and "--a-type" in flags and "--b-type" in flags,
            "CI smoke input changed")
    core = ast.parse(Path(role["config_source"]).read_text(encoding="utf-8-sig"))
    config = next(n for n in core.body if isinstance(n, ast.ClassDef) and n.name == "Config")
    default = next(n.value for n in config.body if isinstance(n, ast.AnnAssign)
                   and isinstance(n.target, ast.Name) and n.target.id == "seed")
    require(isinstance(default, ast.Constant) and type(default.value) is int
            and default.value == int(role["seed_hex"], 16), "CI smoke historical default mismatch")
    cli = Path(role["cli_source"]).read_text(encoding="utf-8-sig")
    require('p.add_argument("--seed", type=int)' in cli
            and 'if args.seed is not None:' in cli and 'cfg_kwargs["seed"] = args.seed' in cli
            and 'cfg = Config(**cfg_kwargs)' in cli, "CI smoke default path changed")
    with zipfile.ZipFile(role["log_archive"]) as archive:
        log = archive.read(role["log_member"]).decode("utf-8")
    require("Run xvfb-run -a python -m pytest -q client/tests/test_linux_pygame_smoke.py" in log
            and ".                                                                        [100%]" in log,
            "CI smoke execution witness unavailable")


def verify(root: Path, evidence_path: Path) -> dict[str, Any]:
    evidence = loads(evidence_path.read_bytes())
    require(evidence["complete"] is False and all(evidence[k] is False for k in
            ("seed_generation", "commitment_publication", "payoff_execution")), "authorization boundary crossed")
    for binding in evidence["bindings"]:
        require(file_sha(Path(binding["path"])) == binding["sha256_raw"], "evidence byte binding changed")
    for binding in evidence["git_bindings"]:
        raw = subprocess.check_output(["git", "show", binding["revision"] + ":" + binding["repository_path"]], cwd=root)
        require(hashlib.sha256(raw).hexdigest() == binding["sha256_raw"], "historical source binding changed")
    original = loads(Path(evidence["original_candidate"]).read_bytes())
    proposal = loads(Path(evidence["proposal_candidate"]).read_bytes())
    included = values_hex(proposal["match_seeds_hex"])
    witnesses = evidence["witnesses"]
    require(len({w["id"] for w in witnesses}) == len(witnesses), "duplicate execution witness")
    witnessed = {verify_witness(w, included) for w in witnesses}
    lookup = {w["id"]: w for w in witnesses}
    input_covered: set[str] = set()
    for domain in evidence["literal_inputs"]:
        verify_literal_input(Path(domain["source"]).read_bytes(), domain["function"], domain["value"], domain["kind"])
        for ref in domain["witness_refs"]:
            witness = lookup[ref]
            observed = (witness["reconstruction"]["base"] if "reconstruction" in witness
                        else int(witness["recorded_seed_hex"], 16))
            require(observed == domain["value"], "witness caller input mismatch")
            input_covered.add(ref)
    require(input_covered == set(lookup), "witness lacks historical caller input")
    verify_generator_source(Path(evidence["generator_source"]).read_bytes())
    verify_ci_smoke(evidence["CI_smoke_reconstruction"], included)
    additions = verify_addition(original, proposal, witnessed)
    require(proposal["parent_sha256_raw"] == file_sha(Path(evidence["original_candidate"])),
            "proposal parent changed")
    job_count = sum(verify_attempt(loads(Path(a["run"]).read_bytes()), loads(Path(a["jobs"]).read_bytes()))
                    for a in evidence["attempts"])
    for d in evidence["source_domains"]:
        require(d["scope"] == "bound_source_family_only" and d["seed_hex"] in included,
                "unsupported source-domain coverage")
        verify_default_domain(Path(d["test"]).read_bytes(), Path(d["core"]).read_bytes(), d["seed_hex"])
    prior = loads((root / "tools/research/v6/e9/historical_scope_crosswalk.json").read_bytes())
    current = loads((root / "tools/research/v6/e9/historical_targeted_crosswalk.json").read_bytes())
    require(len(current["rows"]) == 357 and [r["id"] for r in current["rows"]] == [r["id"] for r in prior["rows"]],
            "original crosswalk identities changed")
    for old, new in zip(prior["rows"], current["rows"], strict=True):
        require(all(new[k] == v for k, v in old.items()), "prior crosswalk evidence changed")
        require(new["coverage_status"] == "UNRESOLVED" and new["targeted_recovery"]["scope_complete"] is False,
                "unsupported row closure")
    return {"schema": "bytefray.v6.e9.targeted_recovery_verification", "version": 1,
            "integrity": "PASS", "membership": "PASS", "derivations": "PASS",
            "original_candidate_entries": len(original["match_seeds_hex"]),
            "proposal_candidate_entries": len(included), "additional_historical_values": len(additions),
            "recovered_execution_witnesses": len(witnesses), "attempts_verified": len(evidence["attempts"]),
            "CI_smoke_reconstructed_executions": 1,
            "attempt_jobs_verified": job_count, "source_domains_verified": len(evidence["source_domains"]),
            "original_ids_preserved": 357, "completeness": "NOT ESTABLISHED",
            "coverage": "Coverage incomplete; generation LOCKED", "requirement_C": "NOT ESTABLISHED",
            "seed_generation": False, "commitment_publication": False, "payoff_execution": False,
            "private_evidence_sha256_raw": file_sha(evidence_path)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    try:
        receipt = verify(Path(__file__).resolve().parents[4], args.evidence)
        raw = canonical(receipt)
        if args.receipt.exists():
            require(args.receipt.read_bytes() == raw, "receipt differs")
        else:
            args.receipt.write_bytes(raw)
    except (OSError, ValueError, KeyError, IndexError, TypeError, StopIteration, SyntaxError,
            subprocess.CalledProcessError, zipfile.BadZipFile):
        print("REFUSED: targeted historical evidence unusable; generation LOCKED")
        return 2
    print("PASS: additive integrity, membership and derivations; coverage incomplete; generation LOCKED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
