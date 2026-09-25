"""Loader for the frozen E5 hypothesis pre-registration (``preregistration.json``).

The JSON holds the decisions recorded before implementation, the exact
operationalizations (O-BP and its bands, units, transitions, contest classes,
populations, the minimum of 6 SWEEP-BACKED units, statuses and the census),
the hypotheses E5-D, E5-H1 .. E5-H5, the pathology flags and D9, the threshold
rationale, the evidence rules, the hard stops and the interpretation table.
``PREREGISTRATION_SHA256`` pins its exact content: loading fails closed if the
file changed, so a criterion cannot drift after results are seen.

Loading also proves the interpretation table is *total and unambiguous*: every
(E5-D, E5-H1, E5-H2) status combination must match exactly one row or be
listed as impossible, never both. The table is thereby frozen together with
the transition function (``analyze_e5``), as the research lead required.
"""

from __future__ import annotations

import hashlib
import json
from itertools import product
from pathlib import Path
from typing import Any

PREREGISTRATION_PATH = Path(__file__).with_name("preregistration.json")
PREREGISTRATION_SHA256 = "6e226fa8e620ff9c62bdbff46c7bc67af2331ae300607a4dcd1f8019a40818f4"

REQUIRED_HYPOTHESES: tuple[str, ...] = ("E5-D", "E5-H1", "E5-H2", "E5-H3", "E5-H4", "E5-H5", "PATHOLOGY", "D9")
REQUIRED_ROWS: tuple[str, ...] = ("STOP", "R-H2", "R-H2-PRIME", "R-H1", "R-H1-PRIME", "NONE")
D_STATUSES: tuple[str, ...] = ("PASS", "FAIL")
H_STATUSES: tuple[str, ...] = ("SUPPORTED", "REFUTED", "NEITHER", "NOT_EVALUABLE")
MIN_SWEEP_BACKED_UNITS = 6


class PreregistrationError(RuntimeError):
    """The E5 pre-registration is not the frozen one, or its table is not total."""


def preregistration_digest(path: Path = PREREGISTRATION_PATH) -> str:
    """SHA-256 of the file with line endings normalized to LF."""
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def classify_combination(table: dict[str, Any], d: str, h1: str, h2: str) -> tuple[list[str], bool]:
    """The rows a combination matches, and whether it is listed as impossible."""
    pair = [h1, h2]
    rows = [row["id"] for row in table["rows"] if row["e5_d"] == d and pair in row["combinations"]]
    impossible = any(item["e5_d"] in (d, "*") and pair in item["combinations"] for item in table["impossible"])
    return rows, impossible


def check_table_is_total(table: dict[str, Any]) -> None:
    """Every combination: exactly one row, or impossible -- never both, never neither."""
    problems = []
    for d, h1, h2 in product(D_STATUSES, H_STATUSES, H_STATUSES):
        rows, impossible = classify_combination(table, d, h1, h2)
        if impossible and rows:
            problems.append(f"({d}, {h1}, {h2}) is impossible but matches {rows}")
        elif not impossible and len(rows) != 1:
            problems.append(f"({d}, {h1}, {h2}) matches {len(rows)} rows: {rows}")
    for item in (*table["rows"], *table["impossible"]):
        for pair in item["combinations"]:
            if len(pair) != 2 or any(status not in H_STATUSES for status in pair):
                problems.append(f"{item.get('id', 'impossible')} lists a malformed combination {pair!r}")
    if problems:
        raise PreregistrationError("E5 interpretation table is not total and unambiguous: " + "; ".join(problems))


def validate(data: dict[str, Any]) -> dict[str, Any]:
    ids = tuple(item["id"] for item in data["hypotheses"])
    if ids != REQUIRED_HYPOTHESES:
        raise PreregistrationError(f"E5 pre-registration hypotheses {ids} != {REQUIRED_HYPOTHESES}")
    rows = tuple(row["id"] for row in data["interpretation"]["rows"])
    if rows != REQUIRED_ROWS:
        raise PreregistrationError(f"E5 interpretation rows {rows} != {REQUIRED_ROWS}")
    known = {item["id"] for item in data["operationalizations"]}
    referenced = [ref for item in data["hypotheses"] for ref in item["operationalizations"]]
    referenced += list(data["populations"]["operationalizations"]) + list(data["metrics"]["operationalizations"])
    missing = sorted(set(referenced) - known)
    if missing:
        raise PreregistrationError(f"E5 pre-registration references unknown operationalizations {missing}")
    check_table_is_total(data["interpretation"])
    return data


def load_preregistration(path: Path = PREREGISTRATION_PATH) -> dict[str, Any]:
    digest = preregistration_digest(path)
    if digest != PREREGISTRATION_SHA256:
        raise PreregistrationError(
            f"E5 pre-registration digest {digest} does not match the frozen "
            f"PREREGISTRATION_SHA256 {PREREGISTRATION_SHA256}; the pre-registration changed."
        )
    return validate(json.loads(path.read_text(encoding="utf-8")))


def criterion(prereg: dict[str, Any], hypothesis_id: str) -> dict[str, Any]:
    for item in prereg["hypotheses"]:
        if item["id"] == hypothesis_id:
            value: dict[str, Any] = item["criterion"]
            return value
    raise KeyError(hypothesis_id)
