"""The values the E7 design review reports, as data, so PA can compare them mechanically.

docs/research/v6/V6_E7_SENSING_DISRUPTION_INTERACTION_DESIGN_REVIEW.md
(committed at ``4a135f8``). Each entry cites the review section it transcribes.
The review computed these with exploratory scratch scripts, not with this
tooling. PA recomputes each value independently, and ``run_audit`` reports
every difference.

The four **load-bearing** findings are the review's Sec 8.1 list:

1. the PACED-ADAPT outcome and mechanism counts of Sec 4.2 and Sec 4.5
   (and Sec 4.6 for lambda = 1), reproduced exactly;
2. the arm contrast (PF-4 raised in the primary but not the companion)
   holds in fewer than 9/10 of resamples;
3. I_common_neutral's positive stability is below 9/10;
4. I_all's positive stability is below 9/10. The review did not compute I_all,
   so this is its committed reading, not a transcribed value.
"""

from __future__ import annotations

from typing import Any

PACED_ADAPT = "F1|PACED|ADAPT"

#: Sec 4.2: PACED's outcomes by its seat, per condition (X = PACED, Y = ADAPT).
OUTCOMES: dict[str, dict[str, dict[str, int]]] = {
    "C-E6": {"X@A": {"X": 32, "tie": 0, "Y": 0, "other": 0}, "X@B": {"X": 32, "tie": 0, "Y": 0, "other": 0}},
    "T-E6": {"X@A": {"X": 30, "tie": 2, "Y": 0, "other": 0}, "X@B": {"X": 22, "tie": 10, "Y": 0, "other": 0}},
    "C-E6L": {"X@A": {"X": 0, "tie": 32, "Y": 0, "other": 0}, "X@B": {"X": 0, "tie": 32, "Y": 0, "other": 0}},
    "T-E6L": {"X@A": {"X": 3, "tie": 29, "Y": 0, "other": 0}, "X@B": {"X": 4, "tie": 28, "Y": 0, "other": 0}},
}

#: Sec 4.2 and Sec 4.5, under T-E6. Paths into ``mechanism.unit_table``'s block for each seat.
T_E6_MECHANISM: dict[str, dict[str, Any]] = {
    "X@A": {
        "saw_first": {"X": 32},
        "first_detection.X": {"1": 15, "2": 17},
        "first_callback_after_rival_detection.Y": {"2": 15, "4": 17},
        "adapt_Y.first_check_after_contact": {"t2:cell1:own": 15, "t4:cell3:damage": 4, "t4:cell3:own": 13},
        "adapt_Y.evasion_tick": {"4": 6, "6": 5, "none": 21},
        "adapt_Y.outcome_for_X_by_evasion.evaded": {"X": 9, "tie": 2},
        "adapt_Y.outcome_for_X_by_evasion.not_evaded": {"X": 21},
        "decision_tick_of_X_wins": {"4": 4, "5": 21, "6": 2, "10": 3},
    },
    "X@B": {
        "saw_first": {"X": 32},
        "first_detection.X": {"1": 17, "2": 15},
        "first_callback_after_rival_detection.Y": {"3": 32},
        "adapt_Y.first_check_after_contact": {"t3:cell2:damage": 11, "t3:cell2:own": 21},
        "adapt_Y.evasion_tick": {"3": 11, "5": 10, "9": 1, "none": 10},
        "adapt_Y.outcome_for_X_by_evasion.evaded": {"X": 12, "tie": 10},
        "adapt_Y.outcome_for_X_by_evasion.not_evaded": {"X": 10},
        "decision_tick_of_X_wins": {"3": 5, "4": 1, "5": 4, "6": 9, "11": 2, "12": 1},
    },
}

#: Sec 4.6, under T-E6L: ADAPT evades in 64 of 64 cells and has no silent tick in ticks 1-12.
T_E6L_MECHANISM: dict[str, dict[str, Any]] = {
    "X@A": {"adapt_Y.evasion_tick.none": 0, "cells_with_silent_ticks_after_rival_detection.Y": 0},
    "X@B": {"adapt_Y.evasion_tick.none": 0, "cells_with_silent_ticks_after_rival_detection.Y": 0},
}

#: Sec 2.3 and Sec 3.2: the corpus pairing checks.
PAIRING: dict[str, int] = {
    "keys": 2880,
    "keys_in_all_four_conditions": 2880,
    "identical_seat_geometry_and_assignment": 2880,
    "f1_cells": 2304,
    "same_first_seer_T-E6_vs_T-E6L": 2299,
    "same_first_detection_T-E6_vs_T-E6L": 2285,
}

#: Sec 4.7 / E6-R Sec F.4: neutral units per condition, and the baseline strata of Sec 6.1.
NEUTRAL_COUNTS: dict[str, int] = {"C-E6": 26, "T-E6": 38, "C-E6L": 30, "T-E6L": 39}
STRATA_SIZES: dict[str, int] = {"stratum_neutral_both": 26, "stratum_neutral_one": 4, "stratum_neutral_neither": 15}

#: Sec 6.2 point values (exact) and stabilities (per 1000 resamples).
POINT: dict[str, str] = {
    "I_common_neutral": "-3/1664",
    "common_neutral_non_adapt": "-5/544",
    "common_neutral_adapt": "7/576",
    "I_flag": "1/26",
    "PACED-ADAPT signed interaction": "9/64",
    "PACED-ADAPT I_u": "7/64",
}
STABILITY: dict[str, str] = {
    "common_neutral>0": "519/1000",
    "common_neutral_non_adapt>0": "249/1000",
    "common_neutral_adapt>0": "746/1000",
    "I_flag>0": "53/100",
    "pf4_raised.primary": "967/1000",
    "pf4_raised.companion": "819/1000",
    "pf4_raised.primary_non_adapt": "429/1000",
    "pf4_raised.companion_non_adapt": "477/1000",
    "PACED-ADAPT signed interaction positive": "1/1",
    "PACED-ADAPT |GSB|>1/10 under T-E6": "94/125",
    "PACED-ADAPT |GSB|>1/10 under T-E6L": "1/250",
}
JOINT: dict[str, int] = {
    "primary=raised,companion=raised": 790,
    "primary=raised,companion=not": 177,
    "primary=not,companion=raised": 29,
    "primary=not,companion=not": 4,
}
JOINT_NON_ADAPT: dict[str, int] = {
    "primary=raised,companion=raised": 190,
    "primary=raised,companion=not": 239,
    "primary=not,companion=raised": 287,
    "primary=not,companion=not": 284,
}
PACED_ADAPT_QUANTILES: dict[str, str] = {"0.025": "3/64", "0.5": "9/64", "0.975": "1/4"}
CROSSINGS: dict[str, dict[str, int]] = {
    "primary": {"F1|PACED|ADAPT": 752, "F2|ADAPT|ADAPT": 549, "F1|LURK|GREED": 421, "F1|GREED|ADAPT": 257,
                "F1|LURK|ADAPT": 157, "F1|RUSH|ADAPT": 44, "F1|STEALTH|ADAPT": 44, "F1|STEALTH|GUARD": 17,
                "F1|EVADER|ADAPT": 2},
    "companion": {"F2|ADAPT|ADAPT": 443, "F1|LURK|GREED": 432, "F1|LURK|ADAPT": 382, "F1|STEALTH|ADAPT": 143,
                  "F1|STEALTH|GUARD": 100, "F1|RUSH|ADAPT": 93, "F1|STEALTH|EVADER": 19, "F1|GREED|ADAPT": 17,
                  "F1|LURK|EVADER": 8, "F1|PACED|GUARD": 6, "F1|RUSH|GUARD": 6, "F1|PACED|ADAPT": 4},
}
#: Sec 6.2: the units of U* with a positive I_u, all of which contain ADAPT.
POSITIVE_INTERACTION_UNITS: dict[str, str] = {
    "F1|PACED|ADAPT": "7/64", "F2|ADAPT|ADAPT": "1/16", "F1|GREED|ADAPT": "3/64", "F1|EVADER|ADAPT": "1/64",
}
#: Sec 2.1 / E6-R: the registered point PF-4 of each arm.
PF4_POINT: dict[str, list[str]] = {"primary": ["F1|PACED|ADAPT"], "companion": []}
