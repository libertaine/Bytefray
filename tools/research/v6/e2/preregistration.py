"""Loader for the frozen E2 hypothesis pre-registration (``preregistration.json``).

The JSON holds the design review's Sec H hypotheses, evidence criteria and
thresholds verbatim, the Sec I.5 interpretation rules, the negative-result
rule, and the operationalizations fixed before any T-E2 data exists.
``PREREGISTRATION_SHA256`` pins its exact content: loading fails closed if
the file changed, so a criterion cannot drift after results are seen.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

PREREGISTRATION_PATH = Path(__file__).with_name("preregistration.json")
PREREGISTRATION_SHA256 = "5b0fafd3ffb1e6f79b5d6170196b642cc7461149691f1c031c24d456a9d3b856"

REQUIRED_HYPOTHESES: tuple[str, ...] = (
    "H0",
    "H1",
    "H2",
    "H3a",
    "H3b",
    "H3c",
    "H3d",
    "H3e",
    "H3f",
    "H3g",
)


def preregistration_digest(path: Path = PREREGISTRATION_PATH) -> str:
    """SHA-256 of the file with line endings normalized to LF."""
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def load_preregistration(path: Path = PREREGISTRATION_PATH) -> dict[str, Any]:
    digest = preregistration_digest(path)
    if digest != PREREGISTRATION_SHA256:
        raise RuntimeError(
            f"E2 pre-registration digest {digest} does not match the frozen "
            f"PREREGISTRATION_SHA256 {PREREGISTRATION_SHA256}; the pre-registration changed."
        )
    data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    ids = tuple(item["id"] for item in data["hypotheses"])
    if ids != REQUIRED_HYPOTHESES:
        raise RuntimeError(f"E2 pre-registration hypotheses {ids} != {REQUIRED_HYPOTHESES}")
    known = {item["id"] for item in data["operationalizations"]}
    for item in data["hypotheses"]:
        missing = set(item["operationalizations"]) - known
        if missing:
            raise RuntimeError(f"{item['id']} references unknown operationalizations {sorted(missing)}")
    return data
