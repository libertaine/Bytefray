"""E4 pre-registration v3: pre-registration v2 plus the O-INTERPRETATION-3 amendment.

Pre-registrations v1 (``preregistration.json``) and v2 (``preregistration_v2.json``)
are preserved byte for byte and still load. Pre-registration v2's record
(``docs/research/v6/V6_E4_ANALYSIS_FREEZE_V2.md``) observed that "¬H1 ∧ H3"
can still apply beside "H2", so the reading would report "the in-tick order
line closes" next to "the privilege follows the final pre-sample chunk".
``preregistration_v3.json`` registers the owner's amendment before any
treatment data exists: H2 takes precedence over the standalone "¬H1 ∧ H3"
interpretation, and when H2 and H3 are both SUPPORTED a combined statement
is reported. It changes only how the interpretation table is read. No
hypothesis, threshold, population, metric, matrix cell, treatment semantics
or analyzer measurement changes.

``read_interpretation_v3`` computes the v2 reading with
``read_interpretation_v2``, unchanged, and then applies the precedence and the
combined outcome to it. ``PREREGISTRATION_V3_SHA256`` pins the amendment, and
loading fails closed if it, pre-registration v2 or pre-registration v1 changed.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from tools.research.v6.e4.preregistration import PREREGISTRATION_SHA256, PreregistrationError
from tools.research.v6.e4.preregistration_v2 import (
    AMENDED_ROW,
    PREREGISTRATION_V2_SHA256,
    load_preregistration_v2,
    read_interpretation_v2,
)

PREREGISTRATION_V3_PATH = Path(__file__).with_name("preregistration_v3.json")
PREREGISTRATION_V3_SHA256 = "4e99bc9e58a22291b0809859c4a858d4420b4513bd00fcc31ffeab483617a993"
AMENDMENT_ID = "O-INTERPRETATION-3"


def preregistration_v3_digest(path: Path = PREREGISTRATION_V3_PATH) -> str:
    """SHA-256 of the amendment with line endings normalized to LF."""
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def load_preregistration_v3(path: Path = PREREGISTRATION_V3_PATH) -> dict[str, Any]:
    """``{"v1": ..., "amendment": O-INTERPRETATION-2, "amendment_v3": O-INTERPRETATION-3}``."""
    digest = preregistration_v3_digest(path)
    if digest != PREREGISTRATION_V3_SHA256:
        raise PreregistrationError(
            f"E4 pre-registration v3 digest {digest} does not match the frozen "
            f"PREREGISTRATION_V3_SHA256 {PREREGISTRATION_V3_SHA256}; the amendment changed."
        )
    amendment: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    prereg_v2 = load_preregistration_v2()
    v1 = prereg_v2["v1"]
    reading = amendment["reading"]
    rows = [row["result"] for row in v1["interpretation"]]
    main = [row["result"] for row in v1["interpretation"] if row["rule"]["kind"] == "all"]
    outcome = reading["combined"]["outcome"]["result"]
    problems: list[str] = []
    if amendment["id"] != AMENDMENT_ID or reading["id"] != AMENDMENT_ID:
        problems.append(f"amendment id {amendment['id']!r} / {reading['id']!r} != {AMENDMENT_ID!r}")
    amends = amendment["amends"]
    if (amends["preregistration_v2"]["sha256"] != PREREGISTRATION_V2_SHA256
            or amends["preregistration"]["sha256"] != PREREGISTRATION_SHA256):
        problems.append("it does not amend the frozen pre-registrations v2 and v1")
    if reading["amended_row"] != AMENDED_ROW:
        problems.append(f"amended row {reading['amended_row']!r} is not {AMENDED_ROW!r}")
    if reading["precedence"]["row"] != "H2" or reading["combined"]["after"] != "H2" or "H2" not in main:
        problems.append("the precedence and the combined outcome are not anchored on v1's \"H2\" row")
    if outcome in rows or outcome == prereg_v2["amendment"]["reading"]["rule_3"]["outcome"]["result"]:
        problems.append("the combined outcome reuses an existing row or outcome label")
    if [rule["rule"] for rule in amendment["rules"]] != [1, 2, 3, 4]:
        problems.append("the amendment does not carry rules 1-4")
    if AMENDMENT_ID in {item["id"] for item in v1["operationalizations"]}:
        problems.append(f"{AMENDMENT_ID} already exists in v1")
    if problems:
        raise PreregistrationError("E4 pre-registration v3 is inconsistent with v2 and v1: " + "; ".join(problems))
    return {**prereg_v2, "amendment_v3": amendment}


def _meets(statuses: Mapping[str, str], requires: Mapping[str, str]) -> bool:
    return all(statuses.get(h) == status for h, status in requires.items())


def read_interpretation_v3(statuses: Mapping[str, str], prereg_v3: Mapping[str, Any]) -> dict[str, Any]:
    """O-INTERPRETATION-3: the v2 reading, then H2's precedence over the standalone
    "¬H1 ∧ H3" row and the combined H2 + H3 outcome.

    ``applies`` is the registered reading under pre-registration v3; ``v2_reading``
    (which carries ``v1_reading``) is reported alongside, unchanged."""
    reading = prereg_v3["amendment_v3"]["reading"]
    v2_reading = read_interpretation_v2(statuses, prereg_v3)
    applies = list(v2_reading["applies"])
    actions: list[str] = []
    withheld: list[str] = []
    if v2_reading["stop"] is None:
        if _meets(statuses, reading["precedence"]["requires"]) and AMENDED_ROW in applies:
            applies.remove(AMENDED_ROW)
            actions.append("precedence")
            withheld.append(AMENDED_ROW)
        combined = reading["combined"]
        if _meets(statuses, combined["requires"]):
            applies.insert(applies.index(combined["after"]) + 1, combined["outcome"]["result"])
            actions.append("combined")
    conclusions = {item["result"]: item["conclusion"] for item in v2_reading["conclusions"]}
    conclusions.update({row["result"]: row["conclusion"] for row in prereg_v3["v1"]["interpretation"]})
    conclusions[reading["combined"]["outcome"]["result"]] = reading["combined"]["outcome"]["conclusion"]
    return {
        "amendment": AMENDMENT_ID,
        "applies": applies,
        "stop": v2_reading["stop"],
        "actions": actions,
        "withheld": withheld,
        "notes": list(v2_reading["notes"]),
        "conclusions": [{"result": result, "conclusion": conclusions[result]} for result in applies],
        "v2_reading": v2_reading,
    }
