"""Loader for the frozen E3 hypothesis pre-registration (``preregistration.json``).

The JSON holds the design review's Sec J hypotheses D0-D9, their criteria,
refutations and probe priors, the interpretation table, the threshold
rationale, the Sec M evidence rules and the Sec N hard stops, verbatim, plus
the operationalizations fixed before any treatment data exists.
``PREREGISTRATION_SHA256`` pins its exact content: loading fails closed if
the file changed, so a criterion cannot drift after results are seen.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

PREREGISTRATION_PATH = Path(__file__).with_name("preregistration.json")
PREREGISTRATION_SHA256 = "2b5f82b4411efca561726e0e63a70fcfe24e5804b2b86b7eef7b71696cafbdd0"

REQUIRED_HYPOTHESES: tuple[str, ...] = ("D0", "D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8", "D9")


class PreregistrationError(RuntimeError):
    """The E3 pre-registration is not the frozen one."""


def preregistration_digest(path: Path = PREREGISTRATION_PATH) -> str:
    """SHA-256 of the file with line endings normalized to LF."""
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def load_preregistration(path: Path = PREREGISTRATION_PATH) -> dict[str, Any]:
    digest = preregistration_digest(path)
    if digest != PREREGISTRATION_SHA256:
        raise PreregistrationError(
            f"E3 pre-registration digest {digest} does not match the frozen "
            f"PREREGISTRATION_SHA256 {PREREGISTRATION_SHA256}; the pre-registration changed."
        )
    data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    ids = tuple(item["id"] for item in data["hypotheses"])
    if ids != REQUIRED_HYPOTHESES:
        raise PreregistrationError(f"E3 pre-registration hypotheses {ids} != {REQUIRED_HYPOTHESES}")
    known = {item["id"] for item in data["operationalizations"]}
    referenced = [ref for item in data["hypotheses"] for ref in item["operationalizations"]]
    referenced += list(data["populations"]["operationalizations"]) + list(data["metrics"]["operationalizations"])
    missing = sorted(set(referenced) - known)
    if missing:
        raise PreregistrationError(f"E3 pre-registration references unknown operationalizations {missing}")
    return data


def hypothesis(prereg: dict[str, Any], hypothesis_id: str) -> dict[str, Any]:
    for item in prereg["hypotheses"]:
        if item["id"] == hypothesis_id:
            criterion: dict[str, Any] = item["criterion"]
            return criterion
    raise KeyError(hypothesis_id)
