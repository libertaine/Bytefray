# Bytefray V6 E4 — Pre-registration v2 (P-1 Interpretation Amendment) and Analysis Freeze v2

**Status:** Pre-registration v2 and analysis freeze v2, **`v6-e4-freeze-v2-68d262a0dbd1`**, are registered and frozen. **When they were frozen, neither treatment condition (T-E4, T-E4K1) had been run**, and no treatment artifact existed. Nothing here is a gameplay result.
**Branch:** `v6-research`. Amendment tooling at `0488176e685e42ce4a9c60598986219070dbf98a`; tests, and the freeze v2 tooling commit, at `516022950d660e17028e8d3f3864667b44257254`; freeze v2 record at `94bc65b86574ee08a1a76133ff1450d7f6081234`.
**Date:** 2026-09-24
**Predecessor:** [`V6_E4_EXPERIMENT_FREEZE.md`](V6_E4_EXPERIMENT_FREEZE.md), covering pre-registration v1, analysis freeze `v6-e4-freeze-v1-101a941f5e30`, the control qualification and finding P-1. It is an unchanged historical record; its only change is an appended, dated addendum that points here.

## Why an amendment

The freeze record's pre-treatment finding **P-1** was found on control data only (C-E4 read against itself):

- Every P-PAR unit is STAYS, so E4-H0 is SUPPORTED, E4-H1 is REFUTED and E4-H3 (STAYS ≥ 2/3 of OPENING-ONLY P-PAR) is SUPPORTED.
- Under O-INTERPRETATION, two rows therefore apply:
  - "H0": "Order is not load-bearing. The line closes";
  - "¬H1 ∧ H3": "The residual is the opening-pass effect. The in-tick order line closes. Next: co-location".

H3 does not discriminate on its own. Under an inert treatment the OPENING-ONLY units stay last-side for the same reason every other unit does. A null result would therefore also satisfy a row that attributes the residual to a mechanism. That attribution would rest on evidence the global null produces too.

The freeze record left two ways forward: accept P-1 as a registered limitation, or re-register under a new freeze while still blind to treatment. The project owner chose re-registration. Recording P-1 only as a limitation would have left the loophole open, and closing it before any treatment data exists moves no experimental goalpost.

## The amendment (verbatim)

`tools/research/v6/e4/preregistration_v2.json`, SHA-256 **`d69680c400e6670ea1f5d1304e2c2930792aaa1e3279eaf17027b428595ccd9f`**, is pinned in `preregistration_v2.py`. It holds the owner's text verbatim, with only code formatting removed.

**O-INTERPRETATION-2 / P-1 amendment.** H3 is not independently mechanism-identifying because the H3 STAYS signature is also expected under the global-null condition.

1. If H0 is satisfied, H0 takes precedence over ¬H1 ∧ H3. H3 is reported as consistent with opening-pass persistence but is non-discriminating under the global null.
2. H1 ∧ H3 ∧ ¬H2 retains its registered interpretation. The contrast between MULTI-PASS change and OPENING-ONLY persistence provides the discriminating signature.
3. If ¬H0 ∧ ¬H1 ∧ H3 occurs and no other registered interpretation applies, do not conclude that the residual is caused by the opening-pass effect. Report: "No registered causal interpretation applies; H3 persistence is consistent with, but does not identify, an opening-pass mechanism."
4. No hypothesis definition, threshold, population, metric, contest classification, matrix cell, treatment, or analyzer calculation changes.

**Rationale (the owner's).** H3 itself is not changed; it is still useful. In the expected H1 ∧ H3 ∧ ¬H2 result, its value comes from the contrast:

- MULTI-PASS units react to the mirrored order.
- OPENING-ONLY units remain last-side.
- The privilege does not follow the new final chunk.

That remains the clean signature E4 was designed to look for. The amendment only prevents H3 from being treated as affirmative causal evidence when essentially nothing changes.

The file also pins pre-registration v1's SHA-256 and names freeze v1. It records P-1 and lists everything that stays unchanged. It shares no scientific key with v1, only `schema`, `schema_version`, `status` and `authority`, and it restates or overrides no hypothesis, criterion, row or population.

## The reading (O-INTERPRETATION-2)

`preregistration_v2.read_interpretation_v2` works in two steps:

1. It computes the v1 reading with the analyzer's own `read_interpretation`, imported unchanged, and reports it as `v1_reading`.
2. It then applies rules 1 and 3. Rule 2 needs no action.

Statuses are read as O-INTERPRETATION reads them: a plain hypothesis is SUPPORTED and a negated one REFUTED.

| Statuses | v1 reading (O-INTERPRETATION) | v2 reading (O-INTERPRETATION-2) |
|---|---|---|
| H0 SUPPORTED (so H1 REFUTED), H3 SUPPORTED | "¬H1 ∧ H3", "H0" | **"H0"**; "¬H1 ∧ H3" withheld (rule 1); E4-H3 carries the note "H3 is consistent with opening-pass persistence but is non-discriminating under the global null." |
| H1 SUPPORTED, H3 SUPPORTED, H2 REFUTED | "H1 ∧ H3 ∧ ¬H2" | unchanged (rule 2) |
| H0 REFUTED, H1 REFUTED, H3 SUPPORTED, no other main row | "¬H1 ∧ H3" | **"¬H0 ∧ ¬H1 ∧ H3"**: "No registered causal interpretation applies; H3 persistence is consistent with, but does not identify, an opening-pass mechanism." "¬H1 ∧ H3" withheld (rule 3) |
| H0 REFUTED, H1 REFUTED, H3 SUPPORTED, H2 SUPPORTED | "H2", "¬H1 ∧ H3" | unchanged: another registered interpretation applies, so rule 3 does not act |
| "¬H1 ∧ H3" does not apply | any | unchanged |
| D9′ STOP | STOP | STOP |

The pathology row (H5, H6, H8) is kept in every case. Both readings are written to the interpretation record, and the registered reading under pre-registration v2 is `applies`.

The reading had to be made mechanical, and each choice below follows from the amendment's own words:

- **Other registered interpretation.** In rule 3 this means the other four main rows: "H1 ∧ H3 ∧ ¬H2", "H1 ∧ ¬H3 ∧ ¬H2", "H2" and "H0". The pathology row is recorded whatever else holds and is not a causal interpretation, so it neither blocks rule 3 nor is removed by it.
- **Rule 3's outcome.** It takes the place of the withheld row. The "none" row is not added beside it, because the outcome itself states that no registered causal interpretation applies. Its label, "¬H0 ∧ ¬H1 ∧ H3", names a reading outcome, not a new hypothesis or criterion.
- **Exhaustiveness.** E4-H0's registered status is SUPPORTED exactly when the STAYS + UNCHANGED-NEUTRAL share is ≥ 0.90 and H1 is REFUTED, and REFUTED exactly when the share is < 0.90. The frozen P-PAR has 32 units, so it is never empty. Whenever "¬H1 ∧ H3" applies, H0 is therefore SUPPORTED or REFUTED, and rules 1 and 3 cover every reachable case. Any other H0 status there is an analyzer inconsistency, and the reading fails closed.

**Observation (outside P-1, not acted on).** When "¬H1 ∧ H3" and "H2" apply together, the v1 reading reports both rows, and their conclusions point to different next steps: co-location against evaluation structure. This is not the P-1 loophole. The global null is excluded there, and OPENING-ONLY persistence sits beside a MULTI-PASS change, so H3 does discriminate. Rule 3 is explicitly scoped to "no other registered interpretation applies", so the v1 reading stands, and O-INTERPRETATION already requires every applying row to be reported.

On the frozen control-vs-control inputs, which are P-1 itself, the v1 reading is `["¬H1 ∧ H3", "H0"]` and the v2 reading is `["H0"]` with the H3 note.

## Three identities

| Identity | Value | Changed by this amendment? |
|---|---|---|
| Matrix | `v6-e4-matrix-v1-fc29d575dd25`: which matches run | No |
| Analysis freeze v1 | `v6-e4-freeze-v1-101a941f5e30`: the measurement instrument (analyzer, gates, runner, populations, pre-registration v1) and its control qualification | No: preserved byte for byte, and it still holds |
| Analysis freeze v2 | **`v6-e4-freeze-v2-68d262a0dbd1`**: freeze v1 plus the O-INTERPRETATION-2 reading, the instrument that interprets E4 | New |

**Why v2 is layered on v1 instead of replacing it.** E2's freeze v2 rewrote its freeze record in place. That was right there, because E2 repaired its analyzer. Here nothing that measures changes, and v1 is to be preserved permanently. Editing `analysis_freeze.py`, `preregistration.py` or `run_e4.py` in place would have changed files freeze v1 pins, and v1 would no longer have verified. It would also have forced the control qualification, whose every record is keyed to v1's id, to be re-run or relabelled, although no measurement input changed. So:

- **v1 records.** `run_e4` keeps producing every measurement record under freeze v1's id, exactly as registered. This covers control and treatment telemetry, the gates and `e4_analysis.json`.
- **v2 records.** Freeze v2 governs the reading and writes its interpretation record under its own id.

`tools/research/v6/e4/analysis_freeze_v2.json`, freeze digest `68d262a0dbd1cd89885f0e8a5419035995f0918a30114c0a1cc30a7bbcf191ca`, holds this identity:

| Input | Value |
|---|---|
| Base freeze | `v6-e4-freeze-v1-101a941f5e30`, digest `101a941f…c8f87`; record `tools/research/v6/e4/analysis_freeze.json`, SHA-256 `2c2018b1d755901e51b51dcae28e96899973ea94806d2900e71c8a0bc0cc4d91` (which also pins v1's PASS control qualification) |
| Measurement tooling | the SHA-256 of all 31 files freeze v1 pins, each **required equal to its v1 pin** |
| Matrix | `v6-e4-matrix-v1-fc29d575dd25` (`fc29d575…c703ceff4ef`), 15,232 matches |
| Pre-registration v1 | `56307844e1c01a52b46b3fc1d100a34706e13d6a645614d6d2bcea94757b9973` (unchanged) |
| Pre-registration v2 (amendment) | `d69680c400e6670ea1f5d1304e2c2930792aaa1e3279eaf17027b428595ccd9f` |
| Interpretation files | `analysis_freeze_v2.py` `2cd492f4…fe7e0a`, `preregistration_v2.json` `d69680c4…5ccd9f`, `preregistration_v2.py` `547a4628…71bbe6` |
| Tooling commit | `516022950d660e17028e8d3f3864667b44257254` |
| Match-generation tree | `engine/src` = `940a27bcf8c62268eb15210cc30c28cae4d33e50` (freeze v1's, unchanged) |

**Control qualification.** It is **inherited, not re-run.** Freeze v2 pins v1's record, and through it the parent-reproduction, analyzer-qualification, G.4′ and D9′ records and `control_populations.json`. The v1 treatment unlock re-verifies all of them.

**Fail-closed checks.** `load_freeze_v2` fails closed unless all of the following hold:

- freeze v1 holds;
- v1's record has the pinned SHA-256;
- every measurement file equals v1's pin;
- the pre-registration v2 digest and its consistency with v1 hold;
- every live input equals the record.

`verify_execution_source_v2` adds a check to v1's execution-source check: each interpretation file must equal its content at the tooling commit.

## The treatment sequence under freeze v2

1. `python -m tools.research.v6.e4.analysis_freeze_v2 verify --execution` (read-only), before and after execution.
2. `run_e4 execute T-E4 <field> --confirm-matrix-execution --confirm-treatment-execution --workers 1` for F1, F2, F2-P and F4, then the same for T-E4K1. One match worker per field is the configuration that qualified the controls. The six-worker Windows `evaluation.json` race of the aborted first control attempt is not reintroduced.
3. `run_e4 treatment-telemetry` and `run_e4 treatment-gates` for each treatment. Any gate failure is a STOP.
4. `run_e4 analyze`, which records the verdicts and the v1 reading.
5. `python -m tools.research.v6.e4.analysis_freeze_v2 interpret`, which gives the registered reading under pre-registration v2. It refuses to read unless all of the following hold:
   - every treatment field's provenance and the analysis record name a clean tree at a commit that already held this freeze v2 record, byte for byte;
   - every treatment field ran under freeze v1's id;
   - the analysis record is freeze v1's, and its v1 reading recomputes from its inputs.

## Qualification

**Tests.** `engine/tests/test_v6_e4_preregistration_v2.py` has 27 test functions, 31 tests. They check:

- **v1 is preserved.** Pre-registration v1 and the freeze v1 record are at their committed SHA-256s, and freeze v1 still holds with its PASS control qualification.
- **The amendment.** The statement and rules 1–4 are verbatim, the v1 pin is present, and v1 and the amendment share only metadata. Any change to the amendment or to v1 fails closed, and so does an amendment inconsistent with v1's rows.
- **The reading, case by case:**
  - rule 1 on the real frozen control-vs-control inputs;
  - rule 1 with a pathology;
  - rule 2 unchanged;
  - rule 3 with H2 REFUTED or NEITHER, and with a pathology;
  - rule 3 not acting beside "H2";
  - the D9′ STOP;
  - an unreachable H0 status failing closed.
- **The reading, exhaustively.** A comparison over every status combination of H0–H3 and a pathology shows that v2 differs from v1 only where "¬H1 ∧ H3" applies.
- **The identity.** Freeze v2 pins v1 and the amendment. The measurement pins equal v1's, and the freeze id is distinct while the matrix id is unchanged.
- **Fail-closed paths:**
  - interpretation drift;
  - measurement drift, through freeze v1;
  - a changed v1 record;
  - a tampered v2 record;
  - self-consistent measurement pins that differ from v1's;
  - interpretation files that differ at the tooling commit.
- **The committed freeze.** It holds. Only commits that hold the record count as producing data under it. `interpret` runs end to end on a synthetic run root, where the frozen global-null inputs read "H0" alone. It refuses data from before the record, from a dirty tree, under another freeze id, or with a v1 reading that does not recompute.

**Full E4 set.** All eight E4 test modules ran at `94bc65b` in one sequential invocation (2 min 34 s): **271 passed, 0 failed, 0 skipped.**

- **Integrity manifest.** Before the run it recorded `HEAD`, `git status` and the SHA-256 of every E2, E3 and E4 research tooling file and the harness: 44 files, plus the `engine/src` tree. After the run the manifest was identical.
- **Lint and types.** `ruff check` passes on all E4 tooling and tests, and `mypy` is clean on both new modules.

**Mutation testing.** Each mutation was applied to the committed file, the v2 tests were run, and the file was restored from `HEAD`. The tree was verified clean, with `HEAD` unchanged, before the next mutation.

A pinned interpretation file makes every freeze-dependent test fail on *any* edit. So the mutations were run a second time with the freeze v2 pin blinded: a scratchpad-only pytest plugin made the pin see each file's committed content. **All 13 were detected both ways.** The table lists the behavioral tests that detect each one with the pin blinded.

| # | Mutation | File | Detected by (pin blinded) |
|---|---|---|---|
| V1 | Rule 1 never acts | `preregistration_v2.py` | `test_rule_1_the_frozen_global_null_reads_h0_alone`, `test_rule_1_keeps_the_pathology_row`, `test_v2_differs_from_v1_only_where_the_amended_row_applies`, `test_interpret_reads_the_v1_analysis_under_freeze_v2` |
| V2 | Rule 3 acts beside another main row | `preregistration_v2.py` | `test_rule_3_does_not_act_when_another_registered_row_applies`, `test_v2_differs_from_v1_only_where_the_amended_row_applies` |
| V3 | Rule 3 treats any non-SUPPORTED H0 as refuted | `preregistration_v2.py` | `test_an_h0_status_the_definition_cannot_produce_fails_closed`, `test_v2_differs_from_v1_only_where_the_amended_row_applies` |
| V4 | Rule 1 drops the H3 note | `preregistration_v2.py` | `test_rule_1_the_frozen_global_null_reads_h0_alone` |
| V5 | Amendment digest pin ignored | `preregistration_v2.py` | `test_a_changed_amendment_fails_closed` |
| V6 | Amendment not required to amend frozen v1 | `preregistration_v2.py` | `test_an_amendment_inconsistent_with_v1_fails_closed` |
| V7 | Measurement pins not compared with freeze v1 | `analysis_freeze_v2.py` | `test_measurement_pins_that_differ_from_v1_fail_closed_even_if_self_consistent` |
| V8 | Non-tooling identity inputs (including the v1 record SHA-256) not compared | `analysis_freeze_v2.py` | `test_a_changed_v1_record_fails_closed` |
| V9 | Any commit counts as holding freeze v2 | `analysis_freeze_v2.py` | `test_only_commits_holding_the_record_count_as_generated_under_freeze_v2`, `test_interpret_refuses_data_not_produced_under_freeze_v2` |
| V10 | Dirty-tree provenance accepted | `analysis_freeze_v2.py` | `test_interpret_refuses_data_not_produced_under_freeze_v2` |
| V11 | v1 reading not recomputed | `analysis_freeze_v2.py` | `test_interpret_refuses_an_analysis_whose_v1_reading_does_not_recompute` |
| V12 | Interpretation files not checked at the tooling commit | `analysis_freeze_v2.py` | `test_the_execution_source_check_covers_the_interpretation_files` |
| V13 | Treatment freeze id not checked | `analysis_freeze_v2.py` | `test_interpret_refuses_data_not_produced_under_freeze_v2` |

**Readiness (read-only, at `94bc65b`):**

- `analysis_freeze_v2 verify --execution` reports freeze v2 holds, base freeze v1, unlocked, execution source PASS and no treatment artifacts.
- `run_e4 unlock` reports `{"unlocked": true}`.
- No `T-E4` or `T-E4K1` directory exists under `runs/research_v6_e4/v6-e4-matrix-v1-fc29d575dd25/`, and no treatment telemetry exists under any freeze.

## What this record does not change or claim

- **Nothing v1 pins changed.** No hypothesis, supported-if or refuted-if clause, criterion, threshold or probe prior changed. Neither did any population, the frozen control populations, any metric, transition class or contest class, the matrix or any cell, either treatment or its Ruleset, the analyzer or any calculation, any evidence rule or hard stop, or any other operationalization. Pre-registration v1 (`56307844…`), the freeze v1 record (`2c2018b1…`) and all 31 files freeze v1 pins are byte-identical to their committed state. The v1 reading is still computed and reported beside the v2 reading.
- **P-2 to P-4 are unchanged.** They stand as recorded limitations: P-PAR sits near the neutral boundary, MULTI-PASS P-PAR is deterministic, and the D9′ parity condition is vacuous on the primary.
- **No E4 result.** No gameplay result and no hypothesis verdict. No treatment data existed when this amendment was registered and frozen.

## Addendum (2026-09-24): the observation resolved by pre-registration v3 and analysis freeze v3

Everything above is unchanged. It remains the record of pre-registration v2 and analysis freeze v2.

The project owner confirmed the three mechanization choices above as written, and decided the observation above while the experiment was still blind to treatment: "¬H1 ∧ H3" can still apply beside "H2", and the two conclusions must not stand side by side.

- **Pre-registration v3.** The O-INTERPRETATION-3 amendment gives "H2" precedence over the standalone "¬H1 ∧ H3" interpretation. When H2 and H3 are both SUPPORTED, it reports a combined statement after "H2". It never emits the standalone "¬H1 ∧ H3" conclusion. No hypothesis, threshold, population, metric, matrix, treatment semantics or analyzer measurement changes.
- **Analysis freeze v3.** `v6-e4-freeze-v3-80f21d822542` pins this freeze v2 and freeze v1 whole and adds that reading.
- **What stays.** Pre-registration v2 and freeze v2 are preserved byte for byte and still hold.

See [`V6_E4_ANALYSIS_FREEZE_V3.md`](V6_E4_ANALYSIS_FREEZE_V3.md).
