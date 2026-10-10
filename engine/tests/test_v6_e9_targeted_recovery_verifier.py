"""Synthetic-only negative controls for historical recovery verification."""

from __future__ import annotations

import copy
import hashlib
import json

import pytest

from tools.research.v6.e9.verify_targeted_recovery import (
    verify_addition,
    verify_attempt,
    verify_ci_smoke,
    verify_default_domain,
    verify_generator_source,
    verify_literal_input,
    verify_witness,
)


def synthetic_hex(value: int) -> str:
    return f"{value:016x}"


def test_candidate_is_additive_and_provenance_bound():
    original = {"complete": False, "coverage": {"all_prior_match_qualification": False},
                "match_seeds_hex": [synthetic_hex(1)]}
    proposal = {**original, "match_seeds_hex": [synthetic_hex(1), synthetic_hex(2)]}
    assert verify_addition(original, proposal, {synthetic_hex(2)}) == {synthetic_hex(2)}
    for bad in ({**proposal, "complete": True}, {**proposal, "match_seeds_hex": []},
                {**proposal, "match_seeds_hex": proposal["match_seeds_hex"] + [synthetic_hex(3)]},
                {**proposal, "coverage": {"all_prior_match_qualification": True}}):
        with pytest.raises(ValueError):
            verify_addition(original, bad, {synthetic_hex(2)})


@pytest.fixture
def synthetic_witness(tmp_path):
    header = {"schema": "battle2.replay", "match_id": "m", "result_id": "r", "ruleset_id": "historical",
              "replay_id": "m", "config": {"seed": 7}}
    replay = tmp_path / "replay.jsonl"
    replay.write_text(json.dumps(header) + "\n", encoding="utf-8")
    replay_sha = hashlib.sha256(replay.read_bytes()).hexdigest()
    result = {"schema": "battle2.result", "match_id": "m", "result_id": "r", "ruleset_id": "historical",
              "reproducibility": {"seed": 7}, "replay": {"replay_id": "m", "sha256": replay_sha}}
    result_path = tmp_path / "result.json"
    result_path.write_text(json.dumps(result), encoding="utf-8")
    return {"scope": "listed_witnessed_executions_only", "recorded_seed_hex": synthetic_hex(7),
            "result_path": str(result_path), "replay_path": str(replay),
            "result_sha256_raw": hashlib.sha256(result_path.read_bytes()).hexdigest(),
            "replay_sha256_raw": replay_sha}


def test_synthetic_artifact_association(synthetic_witness):
    assert verify_witness(synthetic_witness, {synthetic_hex(7)}) == synthetic_hex(7)


@pytest.mark.parametrize("field,value", [("match_id", "other"), ("result_id", "other"),
                                       ("ruleset_id", "other"), ("reproducibility", {"seed": True}),
                                       ("replay", {"replay_id": "other", "sha256": "bad"})])
def test_rebound_contradictory_result_is_refused(synthetic_witness, field, value):
    from pathlib import Path

    path = Path(synthetic_witness["result_path"])
    result = json.loads(path.read_bytes())
    result[field] = value
    path.write_text(json.dumps(result), encoding="utf-8")
    synthetic_witness["result_sha256_raw"] = hashlib.sha256(path.read_bytes()).hexdigest()
    with pytest.raises(ValueError):
        verify_witness(synthetic_witness, {synthetic_hex(7)})


def test_corruption_missing_membership_and_false_scope_are_refused(synthetic_witness):
    for bad, included in [({**synthetic_witness, "replay_sha256_raw": "0" * 64}, {synthetic_hex(7)}),
                          (synthetic_witness, set()),
                          ({**synthetic_witness, "scope": "all_history"}, {synthetic_hex(7)})]:
        with pytest.raises(ValueError):
            verify_witness(bad, included)


def test_wrong_derivation_is_refused(synthetic_witness):
    synthetic_witness["reconstruction"] = {"base": 1, "round_number": 1, "first": "a", "second": "b"}
    with pytest.raises(ValueError, match="derivation"):
        verify_witness(synthetic_witness, {synthetic_hex(7)})


def test_attempt_identity_and_failed_partial_jobs():
    run = {"id": 1, "run_attempt": 2, "head_sha": "bound"}
    job = {"id": 4, "run_id": 1, "run_attempt": 2, "head_sha": "bound", "conclusion": "failure"}
    response = {"returncode": 0, "run_id": 1, "attempt": 2, "stdout": json.dumps(run)}
    jobs = {**response, "stdout": json.dumps({"jobs": [job]})}
    assert verify_attempt(response, jobs) == 1
    for field, value in [("run_attempt", 1), ("run_id", 2), ("head_sha", "unbound")]:
        bad = copy.deepcopy(job)
        bad[field] = value
        with pytest.raises(ValueError):
            verify_attempt(response, {**jobs, "stdout": json.dumps({"jobs": [bad]})})
    with pytest.raises(ValueError):
        verify_attempt(response, {**jobs, "stdout": json.dumps({"jobs": [job, job]})})


def test_default_source_domain_is_bounded_without_running_source():
    source = b"from core import Kernel, Config\ndef test_ticks():\n k = Kernel(cfg=Config(arena_size=16))\n k.run(max_ticks=5)\n"
    core = b"class Config:\n seed: int = 7\n"
    verify_default_domain(source, core, synthetic_hex(7))
    for bad in (source.replace(b"arena_size=16", b"seed=8"), source + b"external_hook()\n",
                source.replace(b"k.run", b"external.run")):
        with pytest.raises(ValueError):
            verify_default_domain(bad, core, synthetic_hex(7))
    with pytest.raises(ValueError):
        verify_default_domain(source, core, synthetic_hex(8))


def test_literal_caller_and_generator_bindings_reject_changed_inputs():
    direct = b"def factory():\n return Config(seed=7)\n"
    verify_literal_input(direct, "factory", 7, "config_seed")
    with pytest.raises(ValueError):
        verify_literal_input(direct, "factory", 8, "config_seed")
    caller = b"def caller():\n arguments = ('tournament', '--seed', '7')\n"
    verify_literal_input(caller, "caller", 7, "argv_seed")
    default = b"def parser():\n p.add_argument('--seed', type=int, default=7)\n"
    verify_literal_input(default, "parser", 7, "cli_default")
    generator = (
        b'def derive_match_seed(seed, round_number, first, second):\n'
        b' material = f"battle2-tournament-v1\\0{seed}\\0{round_number}\\0{first}\\0{second}"\n'
        b' return int.from_bytes(hashlib.sha256(material.encode()).digest()[:8], "big")\n'
    )
    verify_generator_source(generator)
    with pytest.raises(ValueError):
        verify_generator_source(generator.replace(b'[:8]', b'[:4]'))


def test_ci_smoke_requires_attempt_source_default_and_execution_output(tmp_path):
    import zipfile

    def write(name, value):
        path = tmp_path / name
        path.write_text(value, encoding="utf-8")
        return str(path)

    run = {"id": 1, "run_attempt": 1, "head_sha": "bound"}
    job = {"id": 4, "run_id": 1, "run_attempt": 1, "head_sha": "bound",
           "steps": [{"name": "smoke", "conclusion": "success"}]}
    response = {"returncode": 0, "run_id": 1, "attempt": 1, "stdout": json.dumps(run)}
    source = 'def test_smoke():\n engine_main(["--a-type", "writer", "--b-type", "runner"])\n'
    role = {"scope": "identified_successful_test_only", "seed_hex": synthetic_hex(7),
            "run_id": 1, "attempt": 1, "step_name": "smoke", "test_function": "test_smoke",
            "run_response": write("run.json", json.dumps(response)),
            "jobs_response": write("jobs.json", json.dumps({**response, "stdout": json.dumps({"jobs": [job]})})),
            "test_source": write("caller.txt", source),
            "config_source": write("config.txt", "class Config:\n seed: int = 7\n"),
            "cli_source": write("cli.txt", 'p.add_argument("--seed", type=int)\nif args.seed is not None:\n cfg_kwargs["seed"] = args.seed\ncfg = Config(**cfg_kwargs)\n'),
            "log_archive": str(tmp_path / "logs.zip"), "log_member": "step.txt"}
    with zipfile.ZipFile(role["log_archive"], "w") as archive:
        archive.writestr("step.txt", "Run xvfb-run -a python -m pytest -q client/tests/test_linux_pygame_smoke.py\n.                                                                        [100%]\n")
    verify_ci_smoke(role, {synthetic_hex(7)})
    write("caller.txt", source.replace('["--a-type"', '["--seed", "7", "--a-type"'))
    with pytest.raises(ValueError):
        verify_ci_smoke(role, {synthetic_hex(7)})
    write("caller.txt", source)
    with zipfile.ZipFile(role["log_archive"], "w") as archive:
        archive.writestr("step.txt", "command proposed but no execution outcome\n")
    with pytest.raises(ValueError):
        verify_ci_smoke(role, {synthetic_hex(7)})
