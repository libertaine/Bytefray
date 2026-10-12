"""E4 pre-registration v2: pre-registration v1 plus the O-INTERPRETATION-2 amendment.

Pre-registration v1 (``preregistration.json``) is preserved byte for byte and
still loads through ``preregistration.load_preregistration``. Finding P-1
(``docs/research/v6/V6_E4_EXPERIMENT_FREEZE.md``) showed, on control data
only, that a no-effect treatment satisfies both the "H0" and the "¬H1 ∧ H3"
interpretation rows. ``preregistration_v2.json`` registers the owner's
amendment before any treatment data exists: H3's STAYS signature is also
expected under the global null, so H3 alone never identifies a mechanism. It
changes only how the interpretation table is read. No hypothesis, criterion,
threshold, population, metric, contest class, matrix cell, treatment or
analyzer calculation changes.

``read_interpretation_v2`` computes the v1 reading with the analyzer's own
``read_interpretation``, unchanged, and then applies the amendment's rules 1
and 3 to it. ``PREREGISTRATION_V2_SHA256`` pins the amendment, and loading
fails closed if it or pre-registration v1 changed.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from tools.research.v6.e4.analyze_e4 import read_interpretation
from tools.research.v6.e4.preregistration import (
    PREREGISTRATION_SHA256,
    PreregistrationError,
    load_preregistration,
)

PREREGISTRATION_V2_PATH = Path(__file__).with_name("preregistration_v2.json")
PREREGISTRATION_V2_SHA256 = "d69680c400e6670ea1f5d1304e2c2930792aaa1e3279eaf17027b428595ccd9f"
AMENDMENT_ID = "O-INTERPRETATION-2"
AMENDED_ROW = "¬H1 ∧ H3"


class InterpretationError(RuntimeError):
    """The v2 reading met statuses the registered definitions cannot produce."""


def preregistration_v2_digest(path: Path = PREREGISTRATION_V2_PATH) -> str:
    """SHA-256 of the amendment with line endings normalized to LF."""
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def load_preregistration_v2(path: Path = PREREGISTRATION_V2_PATH) -> dict[str, Any]:
    """``{"v1": the frozen v1 pre-registration, "amendment": O-INTERPRETATION-2}``."""
    digest = preregistration_v2_digest(path)
    if digest != PREREGISTRATION_V2_SHA256:
        raise PreregistrationError(
            f"E4 pre-registration v2 digest {digest} does not match the frozen "
            f"PREREGISTRATION_V2_SHA256 {PREREGISTRATION_V2_SHA256}; the amendment changed."
        )
    amendment: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    v1 = load_preregistration()
    reading = amendment["reading"]
    rows = [row["result"] for row in v1["interpretation"]]
    main = [row["result"] for row in v1["interpretation"] if row["rule"]["kind"] == "all"]
    problems: list[str] = []
    if amendment["id"] != AMENDMENT_ID or reading["id"] != AMENDMENT_ID:
        problems.append(f"amendment id {amendment['id']!r} / {reading['id']!r} != {AMENDMENT_ID!r}")
    if amendment["amends"]["preregistration"]["sha256"] != PREREGISTRATION_SHA256:
        problems.append("it does not amend the frozen pre-registration v1")
    if reading["amended_row"] != AMENDED_ROW or AMENDED_ROW not in main:
        problems.append(f"amended row {reading['amended_row']!r} is not v1's {AMENDED_ROW!r} row")
    if sorted([*reading["rule_3"]["unless_any_applies"], AMENDED_ROW]) != sorted(main):
        problems.append("rule 3's other main rows are not v1's main rows")
    if reading["rule_3"]["outcome"]["result"] in rows:
        problems.append("the rule-3 outcome reuses a v1 row label")
    if [rule["rule"] for rule in amendment["rules"]] != [1, 2, 3, 4]:
        problems.append("the amendment does not carry rules 1-4")
    if AMENDMENT_ID in {item["id"] for item in v1["operationalizations"]}:
        problems.append(f"{AMENDMENT_ID} already exists in v1")
    if problems:
        raise PreregistrationError("E4 pre-registration v2 is inconsistent with v1: " + "; ".join(problems))
    return {"v1": v1, "amendment": amendment}


def _meets(statuses: Mapping[str, str], requires: Mapping[str, str]) -> bool:
    return all(statuses.get(h) == status for h, status in requires.items())


def read_interpretation_v2(statuses: Mapping[str, str], prereg_v2: Mapping[str, Any]) -> dict[str, Any]:
    """O-INTERPRETATION-2: the v1 reading, then amendment rules 1 and 3 (rule 2 needs no action).

    ``applies`` is the registered reading under pre-registration v2; ``v1_reading``
    is O-INTERPRETATION's, reported alongside and unchanged."""
    v1 = prereg_v2["v1"]
    reading = prereg_v2["amendment"]["reading"]
    v1_reading = read_interpretation(statuses, v1)
    applies = list(v1_reading["applies"])
    rule: int | None = None
    notes: list[dict[str, Any]] = []
    if v1_reading["stop"] is None and AMENDED_ROW in applies:
        rule_1, rule_3 = reading["rule_1"], reading["rule_3"]
        if _meets(statuses, rule_1["requires"]):
            applies.remove(AMENDED_ROW)
            rule, notes = 1, [dict(rule_1["note"])]
        elif _meets(statuses, rule_3["requires"]):
            if not any(row in applies for row in rule_3["unless_any_applies"]):
                applies[applies.index(AMENDED_ROW)] = rule_3["outcome"]["result"]
                rule = 3
        else:
            raise InterpretationError(
                f"{AMENDED_ROW!r} applies but E4-H0 is {statuses.get('E4-H0')!r}; its registered "
                "definition makes it SUPPORTED or REFUTED whenever E4-H1 is REFUTED."
            )
    conclusions = {row["result"]: row["conclusion"] for row in v1["interpretation"]}
    conclusions[reading["rule_3"]["outcome"]["result"]] = reading["rule_3"]["outcome"]["conclusion"]
    return {
        "amendment": AMENDMENT_ID,
        "applies": applies,
        "stop": v1_reading["stop"],
        "rule": rule,
        "withheld": [AMENDED_ROW] if rule is not None else [],
        "notes": notes,
        "conclusions": [{"result": result, "conclusion": conclusions[result]} for result in applies],
        "v1_reading": v1_reading,
    }
