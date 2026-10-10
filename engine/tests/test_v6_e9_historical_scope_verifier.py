"""Synthetic offline fixtures; no match service, engine runtime or native calls."""

import ast
import hashlib
import inspect
import json
import zipfile

import pytest

from tools.research.v6.e9 import verify_historical_scope as verifier


def candidate(values):
    return verifier.canonical({"complete": False, "coverage": {"E6": True, "E8": True,
                               "all_prior_match_qualification": False}, "match_seeds_hex": values})


@pytest.mark.parametrize("values", [["0000000000000001"] * 2, ["000000000000000A"],
                                    ["1"], [True], ["fffffffffffffffff"],
                                    ["0000000000000002", "0000000000000001"]])
def test_candidate_rejects_noncanonical_domain_or_duplicates(values):
    with pytest.raises(ValueError):
        verifier.candidate_values(candidate(values))


def test_integrity_and_membership_do_not_promote_candidate():
    raw = candidate(["0000000000000001"])
    assert verifier.candidate_values(raw) == {"0000000000000001"}
    assert json.loads(raw)["complete"] is False
    with pytest.raises(ValueError):
        verifier.candidate_values(raw.rstrip())
    record = json.loads(raw)
    record["complete"] = True
    with pytest.raises(ValueError):
        verifier.candidate_values(verifier.canonical(record))


def test_duplicate_json_keys_are_rejected():
    with pytest.raises(ValueError, match="duplicate JSON key"):
        verifier.loads(b'{"complete":false,"complete":true}')


def test_match_field_reader_excludes_policy_rng_and_invalid_numbers():
    assert verifier.match_values({"seed": True, "config": {"seed": 2**64},
                                  "reproducibility": {"match_seed": 1},
                                  "policy_rng": {"seed": 2}}) == {"0000000000000001"}


def proof():
    raw = b"battle2-tournament-v1\x003\x001\x00left\x00right"
    expected = hashlib.sha256(raw).digest()[:8].hex()
    values = [expected]
    return {"scope": "listed_witnessed_executions_only", "set_hex": values, "cardinality": 1,
            "set_sha256_raw": hashlib.sha256(verifier.canonical(values)).hexdigest(),
            "witnesses": [{"id": "synthetic-one", "recorded_seed_hex": expected,
                           "evidence_refs": ["synthetic-bytes"],
                           "reconstruction": {"base": 3, "round_number": 1,
                                              "first": "left", "second": "right"}}]}


def test_finite_historical_derivation_has_an_independent_hash_oracle():
    item = proof()
    assert verifier.verify_finite_containment(item, set(item["set_hex"])) == 1
    item["witnesses"][0]["reconstruction"]["base"] += 1
    with pytest.raises(ValueError, match="derivation mismatch"):
        verifier.verify_finite_containment(item, set(item["set_hex"]))


def test_finite_proof_cannot_expand_its_input_scope_or_omit_membership():
    item = proof()
    with pytest.raises(ValueError, match="missing from candidate"):
        verifier.verify_finite_containment(item, set())
    item["scope"] = "all_historical_executions"
    with pytest.raises(ValueError, match="unproved domain expansion"):
        verifier.verify_finite_containment(item, set(item["set_hex"]))


def test_finite_proof_binds_witnesses_encoding_and_cardinality():
    item = proof()
    item["witnesses"].append(dict(item["witnesses"][0]))
    with pytest.raises(ValueError, match="witness identities"):
        verifier.verify_finite_containment(item, set(item["set_hex"]))
    item = proof()
    item["cardinality"] = 2
    with pytest.raises(ValueError, match="cardinality"):
        verifier.verify_finite_containment(item, set(item["set_hex"]))


def test_crosswalk_preserves_ids_and_requires_specific_dependencies():
    original = [{"id": "REC-001", "category": "unreadable_record", "original_disposition": "UNRESOLVED"}]
    row = {"id": "REC-001", "original_category": "unreadable_record", "original_disposition": "UNRESOLVED",
           "dependencies": ["DEP-HISTORY"], "coverage_status": "UNRESOLVED"}
    dependencies = [{"id": "DEP-HISTORY"}]
    verifier.verify_crosswalk(original, [row], dependencies)
    row["dependencies"] = ["missing"]
    with pytest.raises(ValueError, match="concrete dependency"):
        verifier.verify_crosswalk(original, [row], dependencies)
    row["dependencies"] = ["DEP-HISTORY"]
    row["id"] = "REC-002"
    with pytest.raises(ValueError, match="crosswalk changed"):
        verifier.verify_crosswalk(original, [row], dependencies)


def test_packet_checksum_coverage_and_corruption(tmp_path):
    path = tmp_path / "synthetic.zip"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("record.json", b"{}\n")
        archive.writestr("transport_checksums.json", verifier.canonical({"record.json": hashlib.sha256(b"{}\n").hexdigest()}))
    assert verifier.verify_packet(path) == 2
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("record.json", b"changed\n")
        archive.writestr("transport_checksums.json", verifier.canonical({"record.json": hashlib.sha256(b"{}\n").hexdigest()}))
    with pytest.raises(ValueError, match="member changed"):
        verifier.verify_packet(path)


def test_saved_inventory_checks_original_bindings_without_opening_corpus(tmp_path):
    missing_corpus = str(tmp_path / "not-retained" / "replay.jsonl")
    seed = "0000000000000001"
    row = {"path": missing_corpus, "path_ref": "PATH-" + hashlib.sha256(missing_corpus.encode()).hexdigest()[:16],
           "seed_fields": [{"valid_uint64": True, "value_hex": seed}], "sha256_metadata_raw": "bound-hash",
           "metadata_hash_scope": "first_line", "parse_status": "PARSED_OBJECT"}
    original = {"retained_metadata": [{"path": missing_corpus, "sha256_raw": "bound-hash",
                                      "hash_scope": "first_line", "match_seeds_hex": [seed]}]}
    saved, audit = tmp_path / "saved.jsonl", tmp_path / "audit.json"
    saved.write_bytes(verifier.canonical(row))
    audit.write_bytes(verifier.canonical(original))
    assert verifier.verify_saved_inventory(saved, audit, {seed}) == {
        "saved_rows": 1, "original_metadata_rows": 1, "no_decoded_seed_rows": 0, "malformed_rows": 0}
    row["sha256_metadata_raw"] = "different-hash"
    saved.write_bytes(verifier.canonical(row))
    with pytest.raises(ValueError, match="binding changed"):
        verifier.verify_saved_inventory(saved, audit, {seed})


def test_retained_result_replay_seed_agreement_and_association(tmp_path):
    seed = "0000000000000001"
    replay = {"schema": "battle2.replay", "match_id": "match-one", "ruleset_id": "synthetic-rules",
              "config": {"seed": 1}}
    replay_raw = verifier.canonical(replay) + b"offline trajectory bytes\n"
    result = {"schema": "battle2.result", "match_id": "match-one", "ruleset_id": "synthetic-rules",
              "reproducibility": {"seed": 1}, "replay": {"sha256": hashlib.sha256(replay_raw).hexdigest()}}
    replay_path, result_path = tmp_path / "replay.jsonl", tmp_path / "result.json"
    replay_path.write_bytes(replay_raw)
    result_path.write_bytes(verifier.canonical(result))
    target = {"replay_binding": {"path_ref": "REPLAY", "sha256_whole_file_raw": hashlib.sha256(replay_raw).hexdigest()},
              "result_binding": {"path_ref": "RESULT", "sha256_whole_file_raw": verifier.file_sha(result_path)}}
    witness = {"seed_hex": seed, "target": target}
    lookup = {"REPLAY": str(replay_path), "RESULT": str(result_path)}
    verifier.verify_retained_execution(witness, lookup, {seed})
    result["reproducibility"]["seed"] = 2
    result_path.write_bytes(verifier.canonical(result))
    target["result_binding"]["sha256_whole_file_raw"] = verifier.file_sha(result_path)
    with pytest.raises(ValueError, match="seed records disagree"):
        verifier.verify_retained_execution(witness, lookup, {seed})
    result["reproducibility"]["seed"] = 1
    result["match_id"] = "different-match"
    result_path.write_bytes(verifier.canonical(result))
    target["result_binding"]["sha256_whole_file_raw"] = verifier.file_sha(result_path)
    with pytest.raises(ValueError, match="association mismatch"):
        verifier.verify_retained_execution(witness, lookup, {seed})


def test_ci_reference_seed_requires_successful_step_and_raw_log_input(tmp_path):
    jobs = {"returncode": 0, "stdout": json.dumps({"jobs": [{"steps": [{"name": "reference", "conclusion": "success"}]}]})}
    jobs_path, archive_path = tmp_path / "jobs.json", tmp_path / "logs.zip"
    jobs_path.write_bytes(verifier.canonical(jobs))
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("job.txt", "synthetic command --seed 1\n")
    witness = {"jobs_response_path": str(jobs_path), "log_archive_path": str(archive_path),
               "step_name": "reference", "seed_hex": "0000000000000001"}
    verifier.verify_ci_witness(witness, {"0000000000000001"})
    jobs["stdout"] = jobs["stdout"].replace("success", "failure")
    jobs_path.write_bytes(verifier.canonical(jobs))
    with pytest.raises(ValueError, match="success evidence"):
        verifier.verify_ci_witness(witness, {"0000000000000001"})


def test_deliberate_tournament_corruption_preserves_seed_and_directory_obligation(tmp_path):
    seed = "0000000000000001"
    artifact = tmp_path / "matches" / "synthetic-match"
    artifact.mkdir(parents=True)
    replay_path, state_path = artifact / "replay.jsonl", tmp_path / "tournament.json"
    replay = {"schema": "battle2.replay", "match_id": "native-match", "config": {"seed": 1},
              "reproducibility": {"seed": 1, "entrant_order": ["left", "right"]}}
    replay_path.write_bytes(verifier.canonical(replay))
    entry = {"seed": 1, "round_number": 1, "entrant_ids": ["left", "right"], "match_id": None,
             "artifact_dir": "matches\\synthetic-match", "status": "corrupted", "error_code": "resumed_result_mismatch"}
    state_path.write_bytes(verifier.canonical({"matches": [entry]}))
    target = {"actual_schedule_inputs": {"round_number": 1, "entrant_ids": ["left", "right"]},
              "replay_header_binding": {"path_ref": "REPLAY", "sha256_raw": verifier.file_sha(replay_path)},
              "tournament_state_binding": {"path_ref": "STATE", "sha256_whole_file_raw": verifier.file_sha(state_path)}}
    witness = {"seed_hex": seed, "target": target}
    lookup = {"REPLAY": str(replay_path), "STATE": str(state_path)}
    verifier.verify_retained_execution(witness, lookup, {seed})
    entry["artifact_dir"] = "matches/wrong-match"
    state_path.write_bytes(verifier.canonical({"matches": [entry]}))
    target["tournament_state_binding"]["sha256_whole_file_raw"] = verifier.file_sha(state_path)
    with pytest.raises(ValueError, match="directory mismatch"):
        verifier.verify_retained_execution(witness, lookup, {seed})
    entry["artifact_dir"] = "matches/synthetic-match"
    entry["match_id"] = "wrong-native-match"
    state_path.write_bytes(verifier.canonical({"matches": [entry]}))
    target["tournament_state_binding"]["sha256_whole_file_raw"] = verifier.file_sha(state_path)
    with pytest.raises(ValueError, match="identity mismatch"):
        verifier.verify_retained_execution(witness, lookup, {seed})


def test_verifier_imports_only_standard_library_and_git_is_its_only_subprocess():
    tree = ast.parse(inspect.getsource(verifier))
    imports = {n.module.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
    imports |= {a.name.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
    assert imports <= {"__future__", "argparse", "hashlib", "json", "re", "subprocess", "zipfile", "pathlib", "typing"}
    calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
             and isinstance(n.func.value, ast.Name) and n.func.value.id == "subprocess"]
    assert len(calls) == 1
    assert calls[0].func.attr == "check_output"
    assert ast.literal_eval(calls[0].args[0].elts[0]) == "git"
