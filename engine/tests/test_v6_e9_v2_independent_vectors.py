"""Independently calculated deterministic vectors; no payoff statistics."""

from __future__ import annotations

import hashlib
import itertools
import json

import pytest

from tools.research.v6.e9.v2 import identities

P = "539a60806eab03f1c3534406d96616cec59fc8868fa7df1b567953aa08239ae0"


def raw(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"),
                      allow_nan=False).encode("utf-8")


def hash256(value):
    return hashlib.sha256(value).hexdigest()


def independently_derived_indices(p, instrument, n, count):
    key = hashlib.sha256(b"bytefray-e9-analysis-bootstrap-v1\n" + p.encode() + b"\n"
                         + instrument.encode() + b"\n").digest()
    threshold = (2**64 // n) * n
    result = []
    counter = 0
    while len(result) < count:
        block = hashlib.sha256(key + counter.to_bytes(8, "big")).digest()
        candidate = int.from_bytes(block[:8], "big")
        if candidate < threshold:
            result.append(candidate % n)
        counter += 1
    return result


@pytest.mark.parametrize("n", [1, 1412, 2**63 + 1])
def test_bootstrap_domain_counter_big_endian_and_unbiased_rejection(n):
    instrument = hash256(b"independent-synthetic-implementation-vector")
    expected = independently_derived_indices(P, instrument, n, 64)
    actual = list(itertools.islice(identities.bootstrap_index_stream(P, instrument, n), 64))
    assert actual == expected


def test_full_identity_reference_recipe_and_changes():
    sources = {"opaque-fixture-a.py": hash256(b"synthetic-source-a\n"),
               "opaque-fixture-b.py": hash256(b"synthetic-source-b\n")}
    expected_i = hash256(raw({"protocol_digest": P, "sources": sources}))
    instrument = identities.instrument_identity(P, sources)
    assert instrument["digest"] == expected_i
    assert instrument["identity"] == "v6-e9-instrument-v2-" + expected_i[:12]
    expected_root = hash256(b"bytefray-e9-private-root-v1\n" + bytes.fromhex(P)
                           + bytes.fromhex(expected_i))[:16]
    assert identities.private_root_token(P, expected_i) == expected_root
    p_id = "v6-e9-prereg-v2-" + P[:12]
    coordinate = [p_id, "A", "RUSH8", 1, "A"]
    cell = "v6-e9-cell-v2-" + hash256(raw(coordinate))
    assert identities.logical_cell_id(*coordinate) == cell
    expected_dispatch = "v6-e9-dispatch-v2-" + hash256(raw(
        ["independent-fixture-study", P, expected_i, cell, 1]))
    assert identities.dispatch_id("independent-fixture-study", P, expected_i, cell, 1) == expected_dispatch
    changed_i = identities.instrument_identity(P, {**sources, "opaque-fixture-c.py": "a" * 64})
    assert changed_i["digest"] != expected_i
    assert identities.logical_cell_id(*coordinate) == cell
    assert identities.private_root_token(P, changed_i["digest"]) != expected_root
    assert identities.dispatch_id("independent-fixture-study", P, changed_i["digest"], cell, 1) != expected_dispatch
    assert identities.dispatch_id("other-fixture-study", P, expected_i, cell, 1) != expected_dispatch
    changed_p = hash256(b"changed-protocol-fixture")
    assert identities.instrument_identity(changed_p, sources)["digest"] != expected_i
    assert identities.private_root_token(changed_p, expected_i) != expected_root
    changed_stream = list(itertools.islice(identities.bootstrap_index_stream(changed_p, expected_i), 64))
    assert changed_stream == independently_derived_indices(changed_p, expected_i, 1412, 64)
    assert changed_stream != list(itertools.islice(identities.bootstrap_index_stream(P, expected_i), 64))


@pytest.mark.parametrize("bad", [True, 0, -1, 1.5])
def test_invalid_bootstrap_dimensions_fail_closed(bad):
    with pytest.raises((ValueError, TypeError)):
        next(identities.bootstrap_index_stream(P, "b" * 64, bad))


@pytest.mark.parametrize("bad", ["A" * 64, "0" * 63, "g" * 64, "0" * 65])
def test_invalid_full_digest_inputs_fail_closed(bad):
    with pytest.raises((ValueError, TypeError)):
        identities.private_root_token(bad, "b" * 64)
