"""Frozen deterministic identity and index recipes; never performs statistical analysis."""
from __future__ import annotations

import hashlib
from collections.abc import Iterator

from .records import IntegrityError, canonical_bytes, integer, nonempty, sha256, validate_digest


def instrument_identity(protocol_digest: str, sources: dict[str, str]) -> dict[str, str]:
    validate_digest(protocol_digest)
    if type(sources) is not dict or not sources:
        raise IntegrityError("complete implementation source manifest required")
    for path, d in sources.items():
        nonempty(path)
        validate_digest(d)
    d = sha256(canonical_bytes({"protocol_digest": protocol_digest, "sources": sources}))
    return {"identity": "v6-e9-instrument-v2-" + d[:12], "digest": d}


def logical_cell_id(protocol_identity: str, row: str, opponent: str,
                    position: int, seat: str) -> str:
    from .records import load_protocol
    p = load_protocol()["inherited_scientific_source_pins"]
    integer(position, 1, 1412)
    if row not in p["physical_rows"] or opponent not in p["historical_members"] or seat not in ("A", "B"):
        raise IntegrityError("coordinate outside the complete registered rectangle")
    nonempty(protocol_identity)
    return "v6-e9-cell-v2-" + sha256(canonical_bytes([protocol_identity, row, opponent, position, seat]))


def dispatch_id(study_id: str, protocol_digest: str, instrument_digest: str,
                cell_id: str, attempt: int) -> str:
    nonempty(study_id)
    validate_digest(protocol_digest)
    validate_digest(instrument_digest)
    if not cell_id.startswith("v6-e9-cell-v2-"):
        raise IntegrityError("versioned logical cell required")
    validate_digest(cell_id.removeprefix("v6-e9-cell-v2-"))
    integer(attempt, 1, 2)
    return "v6-e9-dispatch-v2-" + sha256(canonical_bytes(
        [study_id, protocol_digest, instrument_digest, cell_id, attempt]))


def private_root_token(protocol_digest: str, instrument_digest: str) -> str:
    validate_digest(protocol_digest)
    validate_digest(instrument_digest)
    return sha256(b"bytefray-e9-private-root-v1\n" + bytes.fromhex(protocol_digest)
                  + bytes.fromhex(instrument_digest))[:16]


def bootstrap_index_stream(protocol_digest: str, instrument_digest: str,
                           N: int = 1412) -> Iterator[int]:
    validate_digest(protocol_digest)
    validate_digest(instrument_digest)
    integer(N, 1, 2**64)
    key = hashlib.sha256(b"bytefray-e9-analysis-bootstrap-v1\n"
                         + (protocol_digest + "\n" + instrument_digest + "\n").encode()).digest()
    limit = (2**64 // N) * N
    for counter in range(2**64):
        v = int.from_bytes(hashlib.sha256(key + counter.to_bytes(8, "big")).digest()[:8], "big")
        if v < limit:
            yield v % N
    raise IntegrityError("analysis counter exhausted")
