"""Deterministic R2 mortality-H* selection from the frozen R1 diagnostic run.

Section 5 (Arm C) of the R2 charter requires the single finite integrity
value used as R2's mortality instrument to be chosen by a **pre-declared,
mechanical rule applied to the R1 evidence**, never by picking whichever H
makes R2 look best. This module implements that rule as a pure function of
``runs/v5_r1_diagnostic/r1b_manifest.json`` (the frozen R1B execution the
published R1 report's tables are built from), so the same H is reproducible
by anyone re-running it against the same manifest.

The rule, stated before looking at any R2 outcome:

1. **Admissibility.** Consider only the finite H values R1 actually tested.
   Exclude ``H == 1`` outright: a process with one integrity point dies to
   the first hostile anchor hit it ever takes, which is precisely the
   "merely creates immediate first-hit deletion" case the charter excludes.

2. **Pathology reproduction.** For each admissible H, compute the set of
   ``(match_label, entrant)`` pairs exhibiting the *target-loss pathology*
   R2 exists to investigate: the entrant reached zero live processes, stayed
   alive with an intact (non-captured) core, and remained in that state for
   at least ``MIN_PATHOLOGY_ZERO_PROCESS_TICKS`` ticks. The tick floor keeps
   an incidental one-or-two-tick gap immediately before a core capture from
   counting as the stalemate pathology, which is a different phenomenon.

3. **Selection.** Keep only those admissible H whose pathology set is a
   superset of every other admissible H's -- i.e. H reproduces every
   pathology case any admissible H produces, so the instrument is not
   weakened relative to the alternatives. Among those, select the
   **largest** (least-extreme) H, since a larger integrity budget absorbs
   more hits before dying and is therefore the least aggressive instrument
   that still exposes the condition under test.

If step 3 leaves no candidate, ``select_r2_mortality_h`` raises rather than
silently falling back -- the charter requires stopping and explaining rather
than expanding the experiment on an unjustified H.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

# A zero-process interval shorter than this is not the stalemate pathology
# R2 investigates (it is typically the last tick or two before a core
# capture completes). Pre-declared here, not tuned against any R2 outcome.
MIN_PATHOLOGY_ZERO_PROCESS_TICKS = 100

# H == 1 kills a process on its first hostile anchor hit. Excluded by the
# charter's "did not merely create immediate first-hit deletion" criterion.
MIN_ADMISSIBLE_H = 2


class HSelectionError(RuntimeError):
    """No single H satisfies the pre-declared R2 selection rule."""


def _variant_label(h: int) -> str:
    return f"H{h}"


def pathology_set(manifest: dict[str, Any], h: int) -> set[tuple[str, str]]:
    """Return the ``(match_label, entrant)`` pairs showing target loss at ``h``.

    The target-loss pathology is: zero live processes, entrant still alive,
    own core never captured, sustained for at least
    :data:`MIN_PATHOLOGY_ZERO_PROCESS_TICKS` ticks.
    """

    found: set[tuple[str, str]] = set()
    label_key = _variant_label(h)
    for match_label, variants in manifest["results"].items():
        row = variants.get(label_key)
        if row is None:
            continue
        for entrant, extinction_tick in row["process_extinction_tick"].items():
            if extinction_tick is None:
                continue
            if row["core_capture_outcome"].get(entrant) != "survived":
                continue
            zero_ticks = row["entrant_zero_process_ticks"].get(entrant, 0)
            if zero_ticks >= MIN_PATHOLOGY_ZERO_PROCESS_TICKS:
                found.add((match_label, entrant))
    return found


def select_r2_mortality_h(r1b_manifest_path: Path) -> dict[str, Any]:
    """Return the selected H* plus the full evidence the rule was applied to.

    The returned dict is the auditable record of the selection: every tested
    H, which were admissible, each one's pathology set, and why the winner
    won -- so the choice can be re-checked without re-running R1.
    """

    with open(r1b_manifest_path, "r", encoding="utf-8") as handle:
        manifest = json.load(handle)

    tested_h = sorted((int(h) for h in manifest["h_values"]), reverse=True)
    admissible = [h for h in tested_h if h >= MIN_ADMISSIBLE_H]
    excluded = [h for h in tested_h if h < MIN_ADMISSIBLE_H]

    sets = {h: pathology_set(manifest, h) for h in admissible}
    union_of_all = set().union(*sets.values()) if sets else set()

    # Step 3: keep only H reproducing every pathology case any admissible H
    # produces, then take the largest (least-extreme) survivor.
    qualifying = [h for h in admissible if sets[h] >= union_of_all]
    if not qualifying:
        raise HSelectionError(
            "No admissible H reproduces every target-loss pathology case "
            f"observed across H in {admissible}; per the R2 charter the "
            "experiment must stop and explain rather than pick one anyway. "
            f"Pathology sets: { {h: sorted(sets[h]) for h in admissible} }"
        )

    selected = max(qualifying)
    return {
        "selected_h": selected,
        "tested_h": tested_h,
        "admissible_h": admissible,
        "excluded_h": excluded,
        "excluded_reason": (
            "H=1 kills a process on its first hostile anchor hit "
            "(immediate first-hit deletion, excluded by the R2 charter)"
        ),
        "min_pathology_zero_process_ticks": MIN_PATHOLOGY_ZERO_PROCESS_TICKS,
        "pathology_sets": {
            str(h): sorted(f"{label}:{entrant}" for label, entrant in sets[h])
            for h in admissible
        },
        "qualifying_h": qualifying,
        "selection_reason": (
            f"H={selected} is the largest (least-extreme) admissible integrity "
            f"value whose target-loss pathology set covers every case observed "
            f"at any admissible H ({len(union_of_all)} case(s))."
        ),
    }


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="Select R2's mortality H* from the frozen R1B manifest."
    )
    parser.add_argument(
        "--r1b-manifest",
        type=Path,
        default=Path(__file__).resolve().parents[3]
        / "runs"
        / "v5_r1_diagnostic"
        / "r1b_manifest.json",
    )
    args = parser.parse_args()

    record = select_r2_mortality_h(args.r1b_manifest)
    print(json.dumps(record, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
