"""Run the E6 post-hoc factorial audit (PA-1 to PA-7 and PA-9) and write its record.

    python -m tools.research.v6.e6_audit.run_audit [--out PATH]

The record (``pa_record.json`` beside this module by default) is deterministic
JSON with sorted keys and exact fractions as ``"n/d"``. It carries no clock.
PA-8, the scripted lockout characterization, is a test module
(``engine/tests/test_v6_e6_audit_lockout.py``), not a corpus reading.

The run reads only pinned bytes (``corpus``) and refuses to write under
``runs/``. Its readings are post-hoc description. It applies the E7 design
review's adopted decision rule (Sec 8.1): if the load-bearing findings
reproduce, the interaction question closes with no E7 experiment; if they
materially disagree, STOP and reconcile. It never issues a hypothesis verdict.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections.abc import Mapping
from fractions import Fraction
from pathlib import Path
from typing import Any

from tools.research.v6.e6 import family
from tools.research.v6.e6_audit import corpus as corpus_mod
from tools.research.v6.e6_audit import decompose, estimands, mechanism, review_values, seat
from tools.research.v6.e6_audit.corpus import CONDITIONS, REPO_ROOT

PA_VERSION = 1
SCHEMA = "bytefray.v6.e6.post_hoc_factorial_audit"
DEFAULT_OUT = Path(__file__).resolve().parent / "pa_record.json"
PACED_ADAPT = f"F1|{family.package_id('PACED')}|{family.package_id('ADAPT')}"

#: PA-7's named units (design review Sec 8.1): the five of Sec 6.2, then the comparison units of Sec 7.3.
NAMED_UNITS: tuple[tuple[str, str, str], ...] = (
    ("F1", "PACED", "ADAPT"), ("F2", "ADAPT", "ADAPT"), ("F1", "GREED", "ADAPT"), ("F1", "LURK", "ADAPT"),
    ("F1", "LURK", "GREED"), ("F1", "RUSH", "ADAPT"), ("F1", "STEALTH", "ADAPT"), ("F1", "PACED", "GUARD"),
    ("F1", "PACED", "EVADER"),
)

SCOPE_STATEMENT = (
    "Post-hoc description of E6's own frozen cells. It changes zero E6 registered findings: every E6 "
    "hypothesis status, pathology flag, kill criterion, interpretation row and disposition stands exactly "
    "as the frozen interpreter issued it. No match was run, no E6 record was edited, and nothing was "
    "written under runs/. The 9/10 bar is a research-program decision convention, never a hypothesis verdict."
)


def unit_key(field_id: str, first: str, second: str) -> str:
    if field_id == "F2":
        return f"F2|{family.package_id(first)}|{family.package_id(first, 'twin')}"
    return f"F1|{family.package_id(first)}|{family.package_id(second)}"


def text(value: Fraction | None) -> str | None:
    return estimands.text(value)


def _dig(block: Mapping[str, Any], path: str) -> Any:
    value: Any = block
    for part in path.split("."):
        value = value.get(part, 0) if isinstance(value, Mapping) else None
    return value


# ---------------------------------------------------------------------------
# Corpus pairing checks (design review Sec 2.3, Sec 3.2)
# ---------------------------------------------------------------------------


def pairing_checks(data: corpus_mod.Corpus) -> dict[str, int]:
    keys: dict[tuple[str, str, str, str, int], dict[str, Mapping[str, Any]]] = {}
    for condition in CONDITIONS:
        for field_id in corpus_mod.FIELDS:
            for cell in data.cells[condition][field_id]:
                keys.setdefault(decompose.cell_key(field_id, cell), {})[condition] = cell
    complete = [k for k, v in keys.items() if set(v) == set(CONDITIONS)]
    geometry = sum(
        len({(v[c]["subject_start"], v[c]["opponent_start"], v[c]["seat_a_id"], v[c]["seat_b_id"]) for c in CONDITIONS}) == 1
        for k, v in keys.items() if k in set(complete))
    same_seer = same_detection = f1 = 0
    for key, by_condition in keys.items():
        if key[0] != "F1":
            continue
        f1 += 1
        s1 = data.summaries["T-E6"]["F1"][str(by_condition["T-E6"]["schedule_id"])]["summary"]
        s2 = data.summaries["T-E6L"]["F1"][str(by_condition["T-E6L"]["schedule_id"])]["summary"]
        if s1["saw_first"] == s2["saw_first"]:
            same_seer += 1
            first = s1["saw_first"]
            if first is None or s1["first_detection"][first] == s2["first_detection"][first]:
                same_detection += 1
    return {"keys": len(keys), "keys_in_all_four_conditions": len(complete),
            "identical_seat_geometry_and_assignment": geometry, "f1_cells": f1,
            "same_first_seer_T-E6_vs_T-E6L": same_seer, "same_first_detection_T-E6_vs_T-E6L": same_detection}


# ---------------------------------------------------------------------------
# The per-unit table (PA-4)
# ---------------------------------------------------------------------------


def unit_rows(results: Mapping[str, Mapping[str, Any]], point: estimands.Values,
              sets: Mapping[str, list[str]]) -> list[dict[str, Any]]:
    stratum_of = {u: name.removeprefix("stratum_") for name in ("stratum_neutral_both", "stratum_neutral_one",
                                                                 "stratum_neutral_neither") for u in sets[name]}
    rows = []
    for unit in seat.unit_keys():
        rows.append({
            "unit": seat.label(unit),
            "stratum": stratum_of[unit],
            "contains_adapt": seat.contains_adapt(unit),
            "gsb": {c: text(point[c][unit][0]) for c in CONDITIONS},
            "sdom": {c: text(point[c][unit][1]) for c in CONDITIONS},
            "neutral": {c: estimands.is_neutral(point, c, unit) for c in CONDITIONS},
            "decisive_share": {c: text(seat.decisive_share(unit, results[c][unit])) for c in CONDITIONS},
            "I_u": text(estimands.unit_interaction(point, unit)),
            "signed_I_u": text(estimands.signed_interaction(point, unit)),
        })
    return rows


# ---------------------------------------------------------------------------
# The comparison with the review, and the decision rule
# ---------------------------------------------------------------------------


def _same(expected: Any, actual: Any) -> bool:
    if isinstance(expected, str) and isinstance(actual, str) and "/" in expected + actual:
        return Fraction(expected) == Fraction(actual)
    return bool(expected == actual)


def compare(record: Mapping[str, Any]) -> dict[str, Any]:
    """Every review value against PA's, grouped into the four load-bearing findings and the rest."""

    checks: list[dict[str, Any]] = []

    def check(group: str, name: str, expected: Any, actual: Any) -> None:
        checks.append({"group": group, "name": name, "review": expected, "pa": actual, "same": _same(expected, actual)})

    tables = record["mechanism_tables"][review_values.PACED_ADAPT]
    for condition, by_seat in review_values.OUTCOMES.items():
        for x_seat, expected in by_seat.items():
            check("LB-1", f"{condition} {x_seat} outcome_for_X", expected, tables[condition][x_seat]["outcome_for_X"])
    for x_seat, paths in review_values.T_E6_MECHANISM.items():
        for path, expected in paths.items():
            check("LB-1", f"T-E6 {x_seat} {path}", expected, _dig(tables["T-E6"][x_seat], path))
    for x_seat, paths in review_values.T_E6L_MECHANISM.items():
        for path, expected in paths.items():
            check("LB-1", f"T-E6L {x_seat} {path}", expected, _dig(tables["T-E6L"][x_seat], path))

    boot = record["stability"]
    joint = boot["pf4_joint"]
    contrast = Fraction(joint.get("primary=raised,companion=not", 0), boot["resamples"])
    check("LB-2", "arm contrast (primary raised, companion not) share", "177/1000", text(contrast))
    check("LB-3", "stab(I_common_neutral > 0)", review_values.STABILITY["common_neutral>0"], boot["positive"]["common_neutral>0"])

    for name, count in review_values.PAIRING.items():
        check("other", f"pairing {name}", count, record["pairing_checks"][name])
    for condition, count in review_values.NEUTRAL_COUNTS.items():
        check("other", f"neutral units {condition}", count, record["neutral_counts"][condition])
    for name, count in review_values.STRATA_SIZES.items():
        check("other", f"size {name}", count, len(record["unit_sets"][name]))
    point = record["point"]
    check("other", "I_common_neutral", review_values.POINT["I_common_neutral"], point["I_common_neutral"])
    check("other", "I over U* without ADAPT", review_values.POINT["common_neutral_non_adapt"], point["means"]["common_neutral_non_adapt"])
    check("other", "I over ADAPT units of U*", review_values.POINT["common_neutral_adapt"], point["means"]["common_neutral_adapt"])
    check("other", "I_flag", review_values.POINT["I_flag"], point["I_flag"])
    pa_row = next(row for row in record["units"] if row["unit"] == review_values.PACED_ADAPT)
    check("other", "PACED-ADAPT signed interaction", review_values.POINT["PACED-ADAPT signed interaction"], pa_row["signed_I_u"])
    check("other", "PACED-ADAPT I_u", review_values.POINT["PACED-ADAPT I_u"], pa_row["I_u"])
    tracked = boot["tracked_units"][review_values.PACED_ADAPT]
    stab_actual = {
        "common_neutral_non_adapt>0": boot["positive"]["common_neutral_non_adapt>0"],
        "common_neutral_adapt>0": boot["positive"]["common_neutral_adapt>0"],
        "I_flag>0": boot["positive"]["I_flag>0"],
        "pf4_raised.primary": boot["pf4_raised"]["primary"],
        "pf4_raised.companion": boot["pf4_raised"]["companion"],
        "pf4_raised.primary_non_adapt": boot["pf4_raised"]["primary_non_adapt"],
        "pf4_raised.companion_non_adapt": boot["pf4_raised"]["companion_non_adapt"],
        "PACED-ADAPT signed interaction positive": tracked["signed_interaction_positive"],
        "PACED-ADAPT |GSB|>1/10 under T-E6": tracked["abs_gsb_above_one_tenth"]["T-E6"],
        "PACED-ADAPT |GSB|>1/10 under T-E6L": tracked["abs_gsb_above_one_tenth"]["T-E6L"],
    }
    for name, actual in stab_actual.items():
        check("other", f"stab {name}", review_values.STABILITY[name], actual)
    check("other", "PF-4 joint", review_values.JOINT, joint)
    check("other", "PF-4 joint without ADAPT", review_values.JOINT_NON_ADAPT, boot["pf4_joint_non_adapt"])
    check("other", "PACED-ADAPT signed interaction quantiles", review_values.PACED_ADAPT_QUANTILES,
          tracked["signed_interaction_quantiles"])
    for arm, expected in review_values.CROSSINGS.items():
        check("other", f"PF-4 crossings {arm}", expected, boot["pf4_crossings"][arm])
    positive_units = {row["unit"]: row["I_u"] for row in record["units"]
                      if row["stratum"] == "neutral_both" and Fraction(row["I_u"]) > 0}
    check("other", "units of U* with a positive I_u", review_values.POSITIVE_INTERACTION_UNITS, positive_units)
    check("other", "point PF-4 units", review_values.PF4_POINT, record["pf4_point"])
    return {"checks": checks, "differences": [c for c in checks if not c["same"]]}


def decide(record: Mapping[str, Any], comparison: Mapping[str, Any]) -> dict[str, Any]:
    """The adopted post-PA rule (design review Sec 8.1), applied mechanically."""

    boot = record["stability"]
    joint = boot["pf4_joint"]
    contrast = Fraction(joint.get("primary=raised,companion=not", 0), boot["resamples"])
    findings = {
        "LB-1 PACED-ADAPT counts reproduce exactly": all(c["same"] for c in comparison["checks"] if c["group"] == "LB-1"),
        "LB-2 arm contrast below the 9/10 convention": not estimands.meets_convention(text(contrast)),
        "LB-3 I_common_neutral positive stability below the 9/10 convention":
            not estimands.meets_convention(boot["positive"]["common_neutral>0"]),
        "LB-4 I_all positive stability below the 9/10 convention":
            not estimands.meets_convention(boot["positive"]["all>0"]),
    }
    integrity = record["integrity"]["identity_check"]["status"] == "PASS"
    reproduced = integrity and all(findings.values())
    return {
        "load_bearing_findings": findings,
        "integrity_and_identity_pass": integrity,
        "outcome": ("REPRODUCED: close the sensing x disruption interaction question with no E7 experiment"
                    if reproduced else "MATERIAL DISAGREEMENT: STOP and reconcile before deciding whether E7-F is justified"),
        "note": "A decision-convention reading under the adopted rule, not a hypothesis verdict.",
    }


# ---------------------------------------------------------------------------
# The run
# ---------------------------------------------------------------------------


def tooling_digests() -> dict[str, str]:
    here = Path(__file__).resolve().parent
    return {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(here.glob("*.py"))}


def run(repo: Path = REPO_ROOT) -> dict[str, Any]:
    pins = corpus_mod.verify_pins(repo)
    data = corpus_mod.load_corpus(repo)
    frozen = corpus_mod.frozen_analysis(repo)
    results = {condition: seat.per_seed_results(data.cells[condition], data.seeds) for condition in CONDITIONS}
    identity = seat.identity_check(results, frozen)
    point = estimands.values_at(results)
    sets = estimands.unit_sets(point)
    point_reading = estimands.reading(point, sets)
    boot = estimands.bootstrap(results, sets, estimands.draws(len(data.seeds)), tracked=[PACED_ADAPT])
    named = [unit_key(*spec) for spec in NAMED_UNITS]
    tables = mechanism.unit_tables(data, named)
    record: dict[str, Any] = {
        "schema": SCHEMA,
        "pa_version": PA_VERSION,
        "scope": SCOPE_STATEMENT,
        "governing_review": {"path": "docs/research/v6/V6_E7_SENSING_DISRUPTION_INTERACTION_DESIGN_REVIEW.md",
                             "commit": "4a135f8"},
        "integrity": {"pins": pins, "identity_check": identity},
        "pairing_checks": pairing_checks(data),
        "neutral_counts": {c: sum(estimands.is_neutral(point, c, u) for u in seat.unit_keys()) for c in CONDITIONS},
        "unit_sets": {name: [seat.label(u) for u in units] for name, units in sets.items()},
        "units": unit_rows(results, point, sets),
        "point": {
            "I_all": text(point_reading["I_all"]),
            "I_common_neutral": text(point_reading["I_common_neutral"]),
            "means": {name: text(value) for name, value in point_reading["means"].items()},
            "L0": text(point_reading["L0"]), "L1": text(point_reading["L1"]), "I_flag": text(point_reading["I_flag"]),
        },
        "pf4_point": {"primary": [seat.label(u) for u in point_reading["pf4_primary"]],
                      "companion": [seat.label(u) for u in point_reading["pf4_companion"]]},
        "stability": boot,
        "decomposition": decompose.decompose(data.cells),
        "mechanism_tables": tables,
        "tooling_sha256": tooling_digests(),
    }
    frozen_pf4 = {"primary": frozen["arms"]["primary"]["pathology"]["PF-4"]["units"],
                  "companion": frozen["arms"]["companion"]["pathology"]["PF-4"]["units"]}
    record["integrity"]["pf4_point_equals_frozen"] = record["pf4_point"] == frozen_pf4
    record["integrity"]["callback_row_files_verified"] = data.rows_verified
    comparison = compare(record)
    record["review_comparison"] = comparison
    record["decision_rule"] = decide(record, comparison)
    return record


def write(record: Mapping[str, Any], out: Path) -> None:
    resolved = out.resolve()
    runs = (REPO_ROOT / "runs").resolve()
    if resolved == runs or runs in resolved.parents:
        raise SystemExit(f"refusing to write under runs/: {out}")
    resolved.write_text(json.dumps(record, indent=1, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args(argv)
    record = run()
    write(record, args.out)
    decision = record["decision_rule"]
    print(f"identity check: {record['integrity']['identity_check']['status']} "
          f"({record['integrity']['identity_check']['compared']} values)")
    print(f"review differences: {len(record['review_comparison']['differences'])}")
    for name, value in decision["load_bearing_findings"].items():
        print(f"  {name}: {value}")
    print(decision["outcome"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
