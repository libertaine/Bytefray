"""Loader for the frozen E4 hypothesis pre-registration (``preregistration.json``).

The JSON holds the design review's Sec N hypotheses E4-H0 .. E4-H8 and D9',
their machine criteria, the interpretation table with its mechanical reading
rule, the threshold rationale, the Sec M metric and transition-class
definitions, the Sec P evidence rules and the Sec R hard stops, verbatim, plus
the operationalizations fixed before any treatment data exists.
``PREREGISTRATION_SHA256`` pins its exact content: loading fails closed if the
file changed, so a criterion cannot drift after results are seen.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

PREREGISTRATION_PATH = Path(__file__).with_name("preregistration.json")
PREREGISTRATION_SHA256 = "56307844e1c01a52b46b3fc1d100a34706e13d6a645614d6d2bcea94757b9973"

REQUIRED_HYPOTHESES: tuple[str, ...] = (
    "E4-H0", "E4-H1", "E4-H2", "E4-H3", "E4-H4", "E4-H5", "E4-H6", "E4-H7", "E4-H8", "D9-PRIME",
)
REQUIRED_ROWS: tuple[str, ...] = (
    "H1 ∧ H3 ∧ ¬H2", "H1 ∧ ¬H3 ∧ ¬H2", "H2", "¬H1 ∧ H3", "H0", "H5, H6, H8", "none",
)


class PreregistrationError(RuntimeError):
    """The E4 pre-registration is not the frozen one."""


def preregistration_digest(path: Path = PREREGISTRATION_PATH) -> str:
    """SHA-256 of the file with line endings normalized to LF."""
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def load_preregistration(path: Path = PREREGISTRATION_PATH) -> dict[str, Any]:
    digest = preregistration_digest(path)
    if digest != PREREGISTRATION_SHA256:
        raise PreregistrationError(
            f"E4 pre-registration digest {digest} does not match the frozen "
            f"PREREGISTRATION_SHA256 {PREREGISTRATION_SHA256}; the pre-registration changed."
        )
    data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    ids = tuple(item["id"] for item in data["hypotheses"])
    if ids != REQUIRED_HYPOTHESES:
        raise PreregistrationError(f"E4 pre-registration hypotheses {ids} != {REQUIRED_HYPOTHESES}")
    rows = tuple(row["result"] for row in data["interpretation"])
    if rows != REQUIRED_ROWS:
        raise PreregistrationError(f"E4 interpretation rows {rows} != {REQUIRED_ROWS}")
    known = {item["id"] for item in data["operationalizations"]}
    referenced = [ref for item in data["hypotheses"] for ref in item["operationalizations"]]
    referenced += list(data["populations"]["operationalizations"]) + list(data["metrics"]["operationalizations"])
    missing = sorted(set(referenced) - known)
    if missing:
        raise PreregistrationError(f"E4 pre-registration references unknown operationalizations {missing}")
    return data


def criterion(prereg: dict[str, Any], hypothesis_id: str) -> dict[str, Any]:
    for item in prereg["hypotheses"]:
        if item["id"] == hypothesis_id:
            value: dict[str, Any] = item["criterion"]
            return value
    raise KeyError(hypothesis_id)
