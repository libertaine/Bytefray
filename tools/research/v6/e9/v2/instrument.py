"""Complete v2 source boundaries and read-only v1 compatibility.

This module has no experiment-running command. Operational consumers must supply
independently accepted Q and the separate complete operational authority tuple.
"""
from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from .adoption import ROOT, verify_review
from .identities import instrument_identity
from .records import IntegrityError, load_protocol, sha256, strict_json, validate_digest


def rehash_manifest(manifest: dict[str, str]) -> dict[str, str]:
    if type(manifest) is not dict or not manifest:
        raise IntegrityError("complete source manifest required")
    actual = {}
    for name, expected in manifest.items():
        validate_digest(expected)
        path = (ROOT / name).resolve()
        if path != ROOT and ROOT not in path.parents:
            raise IntegrityError("source escapes repository")
        actual[name] = sha256(path.read_bytes())
        if actual[name] != expected:
            raise IntegrityError("exact implementation/qualification source drift")
    return actual


def source_checker(*, protocol_digest: str, instrument_digest: str,
                   implementation_sources: dict[str, str],
                   qualification_sources: dict[str, str]) -> Callable[[], None]:
    def verify() -> None:
        from .adoption import P_DIGEST
        load_protocol()
        if protocol_digest != P_DIGEST:
            raise IntegrityError("mixed protocol source boundary")
        actual = rehash_manifest(implementation_sources)
        rehash_manifest(qualification_sources)
        if instrument_identity(protocol_digest, actual)["digest"] != instrument_digest:
            raise IntegrityError("mixed instrument source boundary")
        verify_review()  # statically hashes all inherited engine/E8/package pins
    return verify


def read_v1_evidence(path: Path) -> dict[str, Any]:
    """Read frozen v1 evidence without rewriting or converting it to authority."""
    value = strict_json(path.read_bytes())
    if type(value) is not dict or value.get("version") != 1:
        raise IntegrityError("historical v1 record required")
    if "body" in value and "digest" in value:
        from .records import canonical_bytes
        if sha256(canonical_bytes(value["body"])) != value["digest"]:
            raise IntegrityError("historical canonical body changed")
    return value
