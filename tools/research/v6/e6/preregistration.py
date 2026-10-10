"""Loader for the frozen E6 pre-registration transcription (``preregistration.json``).

The markdown pre-registration is authoritative; the JSON transcribes it for
the instrument. ``PREREGISTRATION_SHA256`` pins the JSON's exact content, so
loading fails closed if it changed. Loading also checks that every threshold,
set and interpretation row in the JSON equals what the analysis code uses,
so the transcription, the code and (by test) the markdown cannot disagree.
"""

from __future__ import annotations

import hashlib
import json
from fractions import Fraction
from pathlib import Path
from typing import Any

from tools.research.v6.e6 import analyze_e6, family, gates, interpretation, matrix, payoff
from tools.research.v6.e6.traces import SUBSET_SEED_POSITIONS, TRACE_RETENTION_LIMIT_BYTES

PREREGISTRATION_PATH = Path(__file__).with_name("preregistration.json")
PREREGISTRATION_SHA256 = "e1ccc1cc7ef2f3b193019590984b9f34fafb0b7e176b1f4ebb8387d0566ee5f4"


class PreregistrationError(RuntimeError):
    """The E6 pre-registration transcription is not the frozen one, or disagrees with the code."""


def preregistration_digest(path: Path = PREREGISTRATION_PATH) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _fraction(text: str) -> Fraction:
    return Fraction(text)


def consistency_problems(data: dict[str, Any]) -> list[str]:
    """Every place the transcription and the frozen code disagree (empty when they agree)."""
    problems: list[str] = []

    def expect(name: str, actual: Any, wanted: Any) -> None:
        if actual != wanted:
            problems.append(f"{name}: transcription {actual!r} != code {wanted!r}")

    thresholds = data["thresholds"]
    expect("epsilon", _fraction(thresholds["epsilon"]), payoff.EPSILON)
    expect("stability", _fraction(thresholds["stability"]), payoff.STABILITY_MIN)
    expect("stability (analysis)", _fraction(thresholds["stability"]), analyze_e6.NINE_TENTHS)
    expect("h0_keep", _fraction(thresholds["h0_keep"]), analyze_e6.NINE_TENTHS)
    expect("h0_refute", _fraction(thresholds["h0_refute"]), analyze_e6.TWO_THIRDS)
    expect("h3_supported", _fraction(thresholds["h3_supported"]), analyze_e6.NINE_TENTHS)
    expect("h3_refuted", _fraction(thresholds["h3_refuted"]), analyze_e6.ONE_TENTH)
    expect("pathology", _fraction(thresholds["pathology"]), analyze_e6.ONE_TENTH)
    expect("forced_line_tick", thresholds["forced_line_tick"], analyze_e6.FORCED_LINE_TICK)
    boot = data["operationalizations"]["O-BOOT"]
    expect("bootstrap resamples", boot["resamples"], payoff.BOOTSTRAP_RESAMPLES)
    expect("bootstrap rng", boot["rng"], f"random.Random({payoff.BOOTSTRAP_SEED})")
    expect("bootstrap draws", boot["draws"], matrix.SEED_COUNT)
    expect("L", [tuple(pair) for pair in data["operationalizations"]["O-CONTRAST"]["L"]],
           list(payoff.LOWER_INFORMATION))
    population = data["population"]
    expect("Pi_F", tuple(population["fixed_set_pi_f"]), family.FIXED_MEMBERS)
    expect("Pi", tuple(population["opponent_set_pi"]), family.OPPONENTS)
    for member, values in population["members"].items():
        if member == "ADAPT":
            expect("ADAPT adaptive", family.MEMBERS[member]["adaptive"], True)
            continue
        live = family.MEMBERS[member]
        expect(f"{member}", values, {key: live[key] for key in ("search", "posture", "evade", "processes")})
    h3 = data["hypotheses"]["E6-H3"]
    expect("attackers", tuple(h3["attackers"]), analyze_e6.ATTACKERS)
    expect("defenders", tuple(h3["defenders"]), analyze_e6.DEFENDERS)
    expect("CQ-1 members", tuple(data["gates"]["CQ-1"]["members"]), gates.SEARCH_VARIANTS)
    expect("D-4 ticks", tuple(data["gates"]["E6-D"][3]["ticks"]), (1, 2))
    expect("gate ids", [gate["id"] for gate in data["gates"]["E6-D"]], [f"D-{n}" for n in range(1, 8)])
    fields = data["fields"]
    expect("F1 cells", fields["F1"]["cells_per_condition"], matrix.F1.expected_matches)
    expect("F2 cells", fields["F2"]["cells_per_condition"], matrix.F2.expected_matches)
    expect("cells total", fields["cells_total"], matrix.matches_total())
    expect("conditions", [(c["id"], c["ruleset_id"], c["parent"]) for c in data["conditions"]],
           [(c.condition_id, c.ruleset_id, c.parent) for c in matrix.CONDITIONS])
    expect("treatment radius", data["treatment"]["to"], matrix.DETECTION_RADIUS)
    rows = data["interpretation"]["rows"]
    expect("row ids", [row["id"] for row in rows], [row.row_id for row in interpretation.ROWS])
    for row, code in zip(rows, interpretation.ROWS, strict=False):
        expect(f"{row['id']} E6-D", row["e6_d"], code.e6d)
        combos = interpretation.ALL_PAIRS if row["combinations"] == "all" else {tuple(c) for c in row["combinations"]}
        expect(f"{row['id']} combinations", frozenset(combos), code.pairs)
    expect("kill criteria", list(data["kill_criteria"]), list(interpretation.KILL_CRITERIA))
    expect("retention limit", data["decisions"]["P-1"]["decided"].startswith("40 GB"),
           TRACE_RETENTION_LIMIT_BYTES == 40 * 10**9)
    expect("retention subset", SUBSET_SEED_POSITIONS, (1, 2, 3, 4))
    expect("seed count", data["seed_protocol"]["count"], matrix.SEED_COUNT)
    return problems


def load_preregistration(path: Path = PREREGISTRATION_PATH) -> dict[str, Any]:
    digest = preregistration_digest(path)
    if digest != PREREGISTRATION_SHA256:
        raise PreregistrationError(
            f"E6 pre-registration digest {digest} does not match the frozen PREREGISTRATION_SHA256 "
            f"{PREREGISTRATION_SHA256}; the pre-registration changed.")
    data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    problems = consistency_problems(data)
    if problems:
        raise PreregistrationError("E6 pre-registration and code disagree: " + "; ".join(problems))
    return data
