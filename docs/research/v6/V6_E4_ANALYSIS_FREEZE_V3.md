# Bytefray V6 E4 — Pre-registration v3 (H2 Precedence Amendment) and Analysis Freeze v3

**Status:** Pre-registration v3 and analysis freeze v3, **`v6-e4-freeze-v3-80f21d822542`**, are registered and frozen. **When they were frozen, neither treatment condition (T-E4, T-E4K1) had been run**, and no treatment artifact existed. Nothing here is a gameplay result.
**Branch:** `v6-research`. Amendment tooling at `c7211bf`; tests, and the freeze v3 tooling commit, at `a5857f9cc36bfea92ca95bf5dd5133727c39a865`; freeze v3 record at `d17ce32`.
**Date:** 2026-09-24
**Predecessors:** Each is an unchanged historical record, and the v2 record carries only an appended, dated successor pointer.
- [`V6_E4_EXPERIMENT_FREEZE.md`](V6_E4_EXPERIMENT_FREEZE.md): pre-registration v1 and freeze v1 `v6-e4-freeze-v1-101a941f5e30`.
- [`V6_E4_ANALYSIS_FREEZE_V2.md`](V6_E4_ANALYSIS_FREEZE_V2.md): pre-registration v2 and freeze v2 `v6-e4-freeze-v2-68d262a0dbd1`.

**The chain.** v1 is the original. v2 fixes the H0/H3 overlap (P-1). v3 fixes the H2/H3 interpretation precedence.

## Why a second amendment

The v2 record's reading section ended with an observation it did not act on. "¬H1 ∧ H3" can still apply beside "H2" when H0 and H1 are refuted and H2 and H3 are supported. The v1 and v2 readings then report both rows. The project owner decided it before any treatment data existed, in these words:

> The issue is not that H2 ∧ ¬H1 ∧ H3 is ambiguous. It actually gives useful discrimination. The problem is that the old ¬H1 ∧ H3 interpretation says, in effect, the in-tick order line closes and the residual is the opening-pass effect. That statement is too broad if H2 is simultaneously supported, because H2 says the multi-pass privilege does follow the final pre-sample position. We shouldn't allow both conclusions to stand side by side.

## The amendment (verbatim)

`tools/research/v6/e4/preregistration_v3.json`, SHA-256 **`4e99bc9e58a22291b0809859c4a858d4420b4513bd00fcc31ffeab483617a993`**, is pinned in `preregistration_v3.py`.

- **Text.** It holds the owner's text verbatim, with only emphasis and code formatting removed, and the rules numbered in the owner's order.
- **Pins.** It pins pre-registration v2 (`d69680c4…`) and v1 (`56307844…`), and names freeze v2.

**O-INTERPRETATION-3: H2 precedence / combined H2+H3 interpretation.**

1. If H2 is SUPPORTED, the H2 interpretation takes precedence over the standalone ¬H1 ∧ H3 interpretation.
2. If H2 and H3 are both SUPPORTED, report: "The treatment identifies two contest-class-specific signatures. In MULTI-PASS matchups, the privilege follows the final pre-sample chunk, supporting an evaluation-adjacency/final-position mechanism. In OPENING-ONLY matchups, last-side persistence remains, consistent with an opening-pass mechanism. H3 does not override H2 and does not close the in-tick order line globally. Evaluation structure is the registered next question for the MULTI-PASS effect; anchor/core-0 co-location remains a separate follow-up for the OPENING-ONLY residual."
3. Do not additionally emit the old standalone ¬H1 ∧ H3 conclusion.
4. No hypotheses, thresholds, populations, metrics, matrix, treatment semantics, or analyzer measurements change.

The owner confirmed pre-registration v2's three mechanization choices as written. They are unchanged here:

- "other registered interpretation" means the other main rows;
- rule 3's outcome replaces the withheld row;
- the rules are exhaustive given E4-H0's definition.

## The reading (O-INTERPRETATION-3)

`preregistration_v3.read_interpretation_v3` works in two steps:

1. It computes the v2 reading with `read_interpretation_v2`, unchanged. That reading carries the v1 reading inside it.
2. It then applies the precedence (rules 1 and 3) and the combined outcome (rule 2).

| Statuses | v1 reading | v2 reading | v3 reading (O-INTERPRETATION-3) |
|---|---|---|---|
| H0, H1 REFUTED; H2, H3 SUPPORTED | "H2", "¬H1 ∧ H3" | "H2", "¬H1 ∧ H3" | **"H2", "H2 ∧ H3"**; "¬H1 ∧ H3" withheld |
| H2, H3 SUPPORTED; H1 NEITHER | "H2" | "H2" | **"H2", "H2 ∧ H3"** |
| H2 SUPPORTED; H3 not SUPPORTED | "H2" | "H2" | unchanged |
| H0 SUPPORTED, H3 SUPPORTED (the frozen global null) | "¬H1 ∧ H3", "H0" | "H0" (+ H3 note) | unchanged |
| H0, H1 REFUTED; H3 SUPPORTED; no other main row | "¬H1 ∧ H3" | "¬H0 ∧ ¬H1 ∧ H3" | unchanged |
| H1, H3 SUPPORTED; H2 REFUTED | "H1 ∧ H3 ∧ ¬H2" | unchanged | unchanged |
| D9′ STOP | STOP | STOP | STOP |

The pathology row (H5, H6, H8) is kept in every case.

**The one choice this amendment's mechanization needed.** Under rule 2, the combined outcome "H2 ∧ H3" is reported **immediately after** the "H2" row, and the "H2" row is kept. Rule 1 says the H2 interpretation takes precedence, and the combined statement restates and extends it. Rule 3 forbids only the standalone "¬H1 ∧ H3" conclusion. So removing "H2" would take out a row the amendment keeps. Whenever E4-H2 is SUPPORTED, the "H2" row applies, so the combined outcome always follows it. The label "H2 ∧ H3" names a reading outcome, not a hypothesis or criterion.

**Consequence.** Under pre-registration v3, the standalone "¬H1 ∧ H3" conclusion ("the residual is the opening-pass effect; the in-tick order line closes") is never reported. That row needs E4-H1 REFUTED, so the only main rows that can apply beside it are "H0" and "H2":

- with E4-H0 SUPPORTED, v2's rule 1 withholds it;
- with E4-H0 REFUTED and no other main row, v2's rule 3 replaces it;
- beside "H2", v3 withholds it.

An exhaustive test over every H0–H3 status combination confirms that the conclusion never appears. It also confirms that v3 changes the v2 reading only where H2 is SUPPORTED.

## Four identities

| Identity | Value | Role |
|---|---|---|
| Matrix | `v6-e4-matrix-v1-fc29d575dd25` | Which matches run. Unchanged. |
| Analysis freeze v1 | `v6-e4-freeze-v1-101a941f5e30` | The measurement instrument and its control qualification. Preserved; still holds. |
| Analysis freeze v2 | `v6-e4-freeze-v2-68d262a0dbd1` | v1 + O-INTERPRETATION-2. Preserved; still holds. |
| Analysis freeze v3 | **`v6-e4-freeze-v3-80f21d822542`** | v2 + O-INTERPRETATION-3: the instrument that interprets E4. |

Freeze v3 is layered on the preserved v2, as v2 is on v1. `tools/research/v6/e4/analysis_freeze_v3.json` (freeze digest `80f21d82254218bcd2804a0fec8fa5bfade9bd1d8016f26b28a1ca0f8fe3482e`) pins:

| Input | Value |
|---|---|
| Base freeze (v2) | `v6-e4-freeze-v2-68d262a0dbd1`, digest `68d262a0…f191ca`; record SHA-256 `8605aac091410ae011b536f3d67e04fe303ceb587a912a3e975cadb938080188` |
| Root freeze (v1) | `v6-e4-freeze-v1-101a941f5e30`, digest `101a941f…c8f87`; record SHA-256 `2c2018b1d755901e51b51dcae28e96899973ea94806d2900e71c8a0bc0cc4d91` (pins v1's PASS control qualification) |
| Measurement tooling | all 31 files freeze v1 pins, each **required equal to its v1 pin** |
| v2 interpretation files | all 3, each **required equal to its v2 pin** |
| Matrix / engine tree | `v6-e4-matrix-v1-fc29d575dd25` (15,232 matches) / `engine/src` = `940a27bc…` (unchanged) |
| Pre-registrations | v1 `56307844…b9973`; v2 `d69680c4…5ccd9f`; v3 `4e99bc9e…17a993` |
| v3 interpretation files | `analysis_freeze_v3.py` `22e25f7a…6fa270`, `preregistration_v3.json` `4e99bc9e…17a993`, `preregistration_v3.py` `024ce224…a52920` |
| Tooling commit | `a5857f9cc36bfea92ca95bf5dd5133727c39a865` |

**Control qualification and records.** The control qualification is inherited from v1, not re-run. `run_e4` still writes every measurement record under v1's id, exactly as registered. `analysis_freeze_v3 interpret` writes `interpretation_v3.json`, which contains the v3, v2 and v1 readings, under `freezes/v6-e4-freeze-v3-80f21d822542/`.

**`interpret` refuses to read** unless all of the following hold:

- every treatment field and the analysis record were produced from a clean tree at a commit that already held the v3 record, byte for byte;
- every treatment field ran under v1's id;
- the v1 reading recomputes.

## Qualification

**Tests.** `engine/tests/test_v6_e4_preregistration_v3.py` has 35 tests. They check:

- v1 and v2 are preserved;
- the owner's text is verbatim and the pins are present;
- the amendment fails closed on any change to itself, to v2 or to v1;
- every reading case in the table above, including the exhaustive comparison;
- the identity and every fail-closed path;
- the committed freeze;
- `interpret` end to end, where the global null reads "H0" and an H2 + H3 result reads "H2", "H2 ∧ H3";
- refusal of data produced at the v2 freeze commit or at the v3 tooling commit (before the v3 record existed), from a dirty tree, or under another freeze id.

**Full E4 set.** All nine E4 test modules ran at `d17ce32` in one sequential invocation (2 min 37 s): **306 passed, 0 failed, 0 skipped.**

- **Integrity manifest.** It recorded `HEAD`, `git status`, the SHA-256 of 48 E2, E3 and E4 research tooling files and the harness, and the `engine/src` tree. It was identical before and after the run.
- **Lint and types.** `ruff check` passes, and `mypy` is clean on both new modules.

**Mutation testing.** 16 mutations were run, each applied to the committed file and then restored from `HEAD` with a verified clean tree. **16 of 16 were detected**, both with the freeze pin in force and with it blinded. The blinded run used a scratchpad-only plugin that shows the pin each file's committed content, so every detection there comes from a behavioral test.

| # | Mutation | Detected by (pin blinded) |
|---|---|---|
| W1 | Precedence never acts | `test_h2_takes_precedence_and_the_combined_statement_is_reported`, `test_the_pathology_row_is_kept`, the exhaustive test, `interpret` |
| W2 | Combined statement never reported | the precedence test, `test_the_combined_statement_needs_only_h2_and_h3`, the pathology test, the exhaustive test, `interpret` |
| W3 | Combined statement on H2 alone | `test_h2_without_h3_is_unchanged`, the exhaustive test |
| W4 | Combined statement replaces the "H2" row | the precedence, combined, pathology and exhaustive tests, `interpret` |
| W5 | Withheld row not recorded | the precedence test |
| W6 | Amendment digest pin ignored | `test_a_changed_amendment_fails_closed` |
| W7 | Amendment not required to amend frozen v2 and v1 | `test_an_amendment_inconsistent_with_v2_fails_closed` |
| W8 | Precedence and combined outcome not anchored on "H2" | `test_an_amendment_inconsistent_with_v2_fails_closed` |
| W9 | v2 interpretation pins not compared with freeze v2 | `test_pins_that_differ_from_v1_or_v2_fail_closed_even_if_self_consistent` |
| W10 | Measurement pins not compared with freeze v1 | the same |
| W11 | Non-tooling identity inputs (including the v2 and v1 record SHA-256s) not compared | `test_a_changed_v2_or_v1_record_fails_closed` |
| W12 | Any commit counts as holding freeze v3 | `test_only_commits_holding_the_v3_record_count_as_generated_under_freeze_v3`, `test_interpret_refuses_data_not_produced_under_freeze_v3` |
| W13 | Dirty-tree provenance accepted | `test_interpret_refuses_data_not_produced_under_freeze_v3` |
| W14 | v1 reading not recomputed | `test_interpret_refuses_an_analysis_whose_v1_reading_does_not_recompute` |
| W15 | v3 files not checked at the tooling commit | `test_the_execution_source_check_covers_the_v3_interpretation_files` |
| W16 | Treatment freeze id not checked | `test_interpret_refuses_data_not_produced_under_freeze_v3` |

**Readiness (read-only, at `d17ce32`):**

- `analysis_freeze_v3 verify --execution` reports that freeze v3 holds, over freeze v2 and freeze v1. It also reports unlocked, execution source PASS and no treatment artifacts.
- `analysis_freeze_v2 verify --execution` and `run_e4 unlock` pass as well.
- No `T-E4` or `T-E4K1` directory exists, and no treatment telemetry exists under any freeze.

## Treatment authorization

The project owner authorized the treatment, conditional on freeze v3 passing these integrity and readiness checks and on the absence of treatment artifacts. Both conditions are met above. The authorization, in the owner's words:

> GO. Run T-E4, then T-E4K1, one worker per field, followed by treatment telemetry, treatment gates with hard STOP on failure, analysis, and the latest interpretation layer. No further confirmation from me is needed before treatment execution once that v3 freeze passes.

The treatment runs from a clean checkout at a commit holding this freeze v3 record, in this order:

1. `analysis_freeze_v3 verify --execution`.
2. `run_e4 execute T-E4 <field> --confirm-matrix-execution --confirm-treatment-execution --workers 1` for F1, F2, F2-P and F4, then the same for T-E4K1.
3. `run_e4 treatment-telemetry` and `run_e4 treatment-gates` for each treatment. Any failure is a hard STOP.
4. `run_e4 analyze`.
5. `analysis_freeze_v3 interpret`.

## What this record does not change or claim

- **No criterion or instrument changed.** No hypothesis, criterion, threshold, population, metric, transition class or contest class changed. Neither did the matrix or any cell, the treatment semantics or Rulesets, or the analyzer or any measurement. Pre-registrations v1 and v2, freeze records v1 and v2, the 31 measurement files and the 3 v2 interpretation files are byte-identical to their committed state. The v1 and v2 readings are still computed and reported inside the v3 reading.
- **P-2 to P-4 are unchanged.** They stand as recorded limitations.
- **No E4 result.** No gameplay result and no hypothesis verdict. No treatment data existed when this amendment was registered and frozen.
