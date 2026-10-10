"""Synthetic filesystem validation only; no native/research match imports."""

import hashlib
import json
from pathlib import Path

from tools.research.v6.e9.historical_inventory import (
    HEADER_LIMIT,
    collect,
    inspect_file,
    seed_fields,
    walk_selected,
)


def test_full_digest_and_first_line_parse_have_distinct_scopes(tmp_path):
    path = tmp_path / "replay.jsonl"
    raw = b'{"schema":"battle2.replay","config":{"seed":7}}\n' + b'not parsed trajectory\n'
    path.write_bytes(raw)
    result = inspect_file(path)
    assert result["sha256_whole_file_raw"] == hashlib.sha256(raw).hexdigest()
    assert result["sha256_metadata_raw"] == hashlib.sha256(raw.splitlines(keepends=True)[0]).hexdigest()
    assert result["parse_status"] == "PARSED_OBJECT"
    assert result["seed_fields"][0]["value_hex"] == "0000000000000007"
    assert result["stable_during_read"] is True


def test_seed_roles_do_not_accept_bool_policy_rng_or_out_of_domain():
    fields = seed_fields({"seed": True, "match_seed": -1, "config": {"seed": 2**64},
                          "header": {"match_seed": 2**64 - 1}, "agents": {"seed": 23}})
    assert sum(f["valid_uint64"] for f in fields) == 1
    assert fields[-1]["json_pointer"] == "/header/match_seed"
    assert fields[-1]["execution_origin"] == "UNRESOLVED"


def test_empty_malformed_nonobject_and_no_seed_records_are_retained(tmp_path):
    statuses = []
    for i, raw in enumerate((b"", b"{broken", b"[]", b'{"synthetic":true}')):
        path = tmp_path / str(i) / "result.json"
        path.parent.mkdir()
        path.write_bytes(raw)
        record = inspect_file(path)
        assert record["sha256_whole_file_raw"] == hashlib.sha256(raw).hexdigest()
        assert record["seed_fields"] == []
        statuses.append(record["parse_status"])
    assert statuses == ["MALFORMED", "MALFORMED", "PARSED_NONOBJECT", "PARSED_OBJECT"]


def test_read_failure_retains_identity_and_exception(tmp_path):
    row = inspect_file(tmp_path / "missing" / "result.json")
    assert row["path"].endswith("result.json")
    assert row["read_exception"]["type"] == "FileNotFoundError"
    assert row["sha256_whole_file_raw"] is None
    assert row["parse_status"] == "NOT_ATTEMPTED"


def test_oversized_header_still_hashes_whole_file_and_identifies_prefix_scope(tmp_path):
    path = tmp_path / "trace.jsonl"
    raw = b"x" * (HEADER_LIMIT + 2) + b"\nlast\n"
    path.write_bytes(raw)
    row = inspect_file(path)
    assert row["parse_status"] == "HEADER_LIMIT_EXCEEDED"
    assert row["metadata_hash_scope"] == "first_line_prefix"
    assert row["sha256_whole_file_raw"] == hashlib.sha256(raw).hexdigest()


def test_traversal_retains_errors_and_excludes_prepared_private_root(tmp_path):
    include = tmp_path / "include"
    include.mkdir()
    (include / "result.json").write_bytes(b"{}")
    excluded = include / "private"
    excluded.mkdir()
    (excluded / "result.json").write_bytes(b"{}")
    failures, auxiliary = [], []
    paths = list(walk_selected([include, tmp_path / "missing"], excluded, failures, auxiliary))
    assert paths == [include / "result.json"]
    assert failures[0]["path"] == str(tmp_path / "missing")
    assert failures[0]["exception"]["type"] == "FileNotFoundError"
    assert failures[0]["original_directory_gap_id"] is None


def test_additive_collection_reconciles_known_bytes_without_claiming_lost_identities(tmp_path):
    inputs = tmp_path / "inputs"
    inputs.mkdir()
    path = inputs / "result.json"
    raw = b'{"seed":7}'
    path.write_bytes(raw)
    no_seed = inputs / "summary.json"
    no_seed.write_bytes(b"{}")
    original = {"retained_metadata": [{"path": str(path), "sha256_raw": hashlib.sha256(raw).hexdigest(),
                 "hash_scope": "whole_file", "match_seeds_hex": ["0000000000000007"]}],
                "unreadable_records": [], "retained_metadata_counts": {"records_examined": 2}}
    result = collect([inputs], inputs / "excluded", tmp_path / "output", original, {},
                     {"0000000000000007"}, workers=1)
    rows = [json.loads(line) for line in (tmp_path / "output/selected_files.jsonl").read_bytes().splitlines()]
    assert result["counts"]["original_retained_binding_matches"] == 1
    assert result["counts"]["records_without_decoded_seed"] == 1
    assert rows[1]["original_reconciliation"]["original_no_seed_identity"] is None
    assert result["coverage"] == "NOT COMPLETE"
    assert result["new_decoded_candidate_values_hex"] == []
    assert Path(result["excluded_root"]).name == "excluded"
