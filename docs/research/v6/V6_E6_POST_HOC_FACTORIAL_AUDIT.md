# Bytefray V6 E6 — Post-Hoc Factorial Audit (PA)

**Status:** A post-hoc descriptive audit of E6's own frozen cells. It is not an experiment and not a registration. **The research lead accepted it on 2026-09-29 and decided NO NEW EXPERIMENT: the sensing × disruption interaction question is closed (§13).**
- **What it reads.** The frozen E6 corpus, verified byte for byte against E6's own pins. It changes nothing in the corpus.
- **What it does not do.** It runs no gameplay match and generates no seed. The only matches are scripted, non-family engine tests (PA-8).
- **E6 is untouched.** It changes **zero E6 registered findings**. Every E6 hypothesis status, pathology flag, kill criterion, interpretation row and disposition stands exactly as the frozen interpreter issued it.

**Branch:** `v6-research`. It is built on `4a135f8`, the E7 design review commit. The audit's tooling and tests are committed at `22c9e76`, byte for byte as they were for the single run. The run's record, `pa_record.json`, and this document are committed after it.
**Date:** 2026-09-29
**Authority:**
- [`V6_E7_SENSING_DISRUPTION_INTERACTION_DESIGN_REVIEW.md`](V6_E7_SENSING_DISRUPTION_INTERACTION_DESIGN_REVIEW.md) (**E7-DR**). Its §8.1 fixes PA-1 to PA-9 and the decision rule, and its §16 records the research lead's authorization and rulings of 2026-09-29.
- The E6 records: [`V6_E6_PRICED_SENSING_PREREGISTRATION.md`](V6_E6_PRICED_SENSING_PREREGISTRATION.md) (**PR**), [`V6_E6_PRICED_SENSING_RESULTS.md`](V6_E6_PRICED_SENSING_RESULTS.md) (**E6-R**), `tools/research/v6/e6/pre_reveal_manifest.json` and `tools/research/v6/e6/final_record.json`.

**How to read the numbers.**
- **They are post-hoc description.** Every value here was produced after E6's results were known.
- **The 9/10 bar is a decision convention.** It is the research program's convention, reused from E6's O-4, and reaching it or not is never a hypothesis verdict. This record uses no SUPPORTED, REFUTED or NEITHER, and no interpretation row.
- **Most values verify a prior computation.** E7-DR had already computed most of them with exploratory scripts, so for those values PA is a verification and a durable record, not a blind test. The exception is **I_all**. E7-DR defined it but did not compute it, and this audit computes it for the first time (§5.1).

---

## Answer in Brief

**Under E7-DR's adopted rule, the outcome is REPRODUCED: close the sensing × disruption interaction question with no E7 experiment.** The research lead confirmed it on 2026-09-29: **NO NEW EXPERIMENT** (§13).

| Load-bearing finding (E7-DR §8.1) | PA |
|---|---|
| LB-1 The PACED–ADAPT outcome and mechanism counts of E7-DR §4.2, §4.5 and §4.6 reproduce exactly | **Yes.** All 28 checks are equal. |
| LB-2 The arm contrast (PF-4 raised in the primary but not the companion) is below the 9/10 convention | **Yes:** 177/1000 |
| LB-3 I_common_neutral's positive stability is below the 9/10 convention | **Yes:** 519/1000 |
| LB-4 I_all's positive stability is below the 9/10 convention | **Yes:** 1/1000 |

**The supporting checks:**
- **Integrity (PA-1).** 42 pinned files and 2,176 callback-row files match their pins, and the seed list matches the commitment.
- **Identity (PA-2).** 180 of 180 frozen GSB and SDom values reproduce.
- **The review comparison.** Of the 66 values E7-DR reports and PA recomputes, **none differs**.

**The first computation of I_all** is **−31/720 ≈ −0.043**, and it is at or below zero in 999 of 1000 resamples. So across the whole frozen family, whole-tick disruption does not amplify the seat-bias effect of priced sensing. The pre-declared baseline strata show why the value is negative rather than near zero (§5.1):
- **Stratum (ii) carries it.** Its four units are neutral under C-E6L only: RUSH, PACED, STEALTH and LURK against EVADER. They contribute −59/32 of I_all's total of −31/16. Under C-E6, whole-tick disruption gives Seat A a tick-1 forced line against EVADER, a seat bias of 31/64, and priced sensing removes it. That is the floor effect E7-DR recorded before this computation.
- **Strata (i) and (iii) sit near zero,** at −3/1664 and −1/320, positive in 519/1000 and 508/1000 resamples.

**The mechanism.** It reproduces cell for cell: KC-5's trigger was a unit-level interaction among priced sensing, whole-tick lockout and ADAPT's absolute-tick own-core check. PA-8 turns the Ruleset half into a tested fact under all four E6 Rulesets:
- **Whole tick.** A re-hit victim gets no callback in any tick its opponent moves first.
- **One offer.** The victim loses exactly one offer per hit.

---

## 1. What Was Run

| Item | Value |
|---|---|
| Tooling | `tools/research/v6/e6_audit/`: `corpus.py` (PA-1), `seat.py` (PA-2), `decompose.py` (PA-3), `estimands.py` (PA-4 to PA-6), `mechanism.py` (PA-7), `review_values.py` (E7-DR's values, as data) and `run_audit.py` (the run, the comparison and the decision rule). It never writes under `runs/`. The frozen `tools/research/v6/e6/` is used and not modified. |
| Tests | `engine/tests/test_v6_e6_audit.py`: 22 tests. `engine/tests/test_v6_e6_audit_lockout.py` (PA-8): 16 tests. All 38 pass. Two of the 22 read the git-ignored corpus and are skipped where it is absent. The full repository suite over the same bytes gives 5,441 passed, 18 skipped and 3 deselected (exit 0). |
| The run | `python -m tools.research.v6.e6_audit.run_audit`, once, after the tests passed, in about 70 s. Output: `tools/research/v6/e6_audit/pa_record.json`, SHA-256 `b2c661fb1796f15d522c71584b5743ddf718025c98f06550a53ef2ba1a0bacdc`. The record is deterministic: sorted keys, exact fractions, no clock. |
| Order | The tooling was tested before its only run. No estimand, set or convention was changed after I_all was first computed. The code did not change at all after the run. At commit, every module's SHA-256 was rechecked against the record's `tooling_sha256` and matched, and the tests were last modified before the run. Both are committed at `22c9e76`. |
| Environment | Python 3.13 in the repository `.venv`, on Windows 11 |

The tooling's SHA-256 digests are in the record (`tooling_sha256`) and in Appendix A.

---

## 2. PA-1: Integrity

- **Pinned files.** 42 files match their pins: each field's `experiment_result.json`, `provenance.json`, `traces/summaries.jsonl` and `traces/trace_index.json` (32), the eight records the manifest pins, and `d6.json` and `e6_interpretation.json` from the final record.
- **Cell counts.** Every field's cell count equals the manifest's, and every cell's seed is on the revealed list.
- **Seeds.** The revealed list has 32 unique seeds, and its SHA-256 equals the seed commitment `61e292f6…5e1c83` in both the manifest and the final record.
- **Callback rows.** All **2,176** callback-row files PA-7 read were checked against their summary's `rows_sha256`, and all match.
- **PF-4.** At the point estimate, PF-4 as PA computes it equals the frozen analysis's: primary `F1|PACED|ADAPT`, companion none.

## 3. PA-2: Identity

The multiplicity-aware seat metrics reproduce **all 180 frozen (unit, condition) values of GSB and SDom** exactly (45 units × 4 conditions).

The tests also check the re-implementation against the frozen E4 `pairing_seat_metrics` and `mirror_seat_metrics`. They compare the two on 200 random unique-seed tables each, and they pin the multiset handling.

## 4. PA-3: The Exact Cell-Level Decomposition

Each of the 2,880 cell keys was played in all four conditions, with identical seat geometry and seat assignment (§9). So its four seat results are exact counterfactuals. Each key is classified by which factor changes its result (E7-DR §7.5; `decompose.py`):

| Class | F1 | F2 | All |
|---|---|---|---|
| Invariant | 1,070 | 270 | **1,340** |
| Sensing only | 521 | 172 | **693** |
| Disruption only | 232 | 22 | **254** |
| Interaction | 481 | 112 | **593** |

The interaction keys break down by which condition is the odd one out:

| Odd one out | Keys |
|---|---|
| C-E6L | 211 |
| C-E6 | 120 |
| T-E6L | 79 |
| T-E6 | 54 |
| Diagonal | 24 |
| Other | 105 |

**PACED–ADAPT's 64 keys:**
- **47 are disruption-only:** captured under whole tick in both sensing conditions, tied under λ = 1 in both.
- **17 are interactions:**
  - **10 odd C-E6:** a capture under C-E6 that becomes a tie under T-E6, where both λ = 1 cells already tie.
  - **5 odd C-E6L:** the λ = 1 control ties, and the other three capture.
  - **2 diagonal:** a capture under C-E6 and T-E6L, and a tie under T-E6 and C-E6L.

  The 10 odd C-E6 keys and the 2 diagonal keys are exactly the 12 T-E6 ties that carry the seat bias.

The per-unit breakdown for all 45 units is in the record (`decomposition.by_unit`).

---

## 5. PA-4 to PA-6: The Estimands

### 5.1 I_all, computed for the first time

| Quantity (E7-DR §6.1) | Units | Point | Positive in | At or below zero in |
|---|---|---|---|---|
| **I_all** | all 45 | **−31/720 ≈ −0.043** | **1/1000** | 999/1000 |
| stratum (i): neutral under both controls | 26 | −3/1664 ≈ −0.002 | 519/1000 | 481/1000 |
| stratum (ii): neutral under exactly one control | 4 | −59/128 ≈ −0.461 | 0/1000 | 1000/1000 |
| stratum (iii): neutral under neither control | 15 | −1/320 ≈ −0.003 | 508/1000 | 492/1000 |
| units containing ADAPT | 9 | +7/576 ≈ +0.012 | 746/1000 | 254/1000 |
| units without ADAPT | 36 | −131/2304 ≈ −0.057 | 0/1000 | 1000/1000 |
| pairings | 36 | −61/1152 ≈ −0.053 | 0/1000 | 1000/1000 |
| mirrors | 9 | −1/288 ≈ −0.003 | 578/1000 | 422/1000 |

The strata were fixed from the controls alone in E7-DR §6.1, before this computation.

**The reading, descriptive:**
- **I_all does not show amplification.** Averaged over the whole frozen family, the sensing effect on |GSB| is not larger under whole-tick disruption than under one-offer disruption. The point value is negative, and 999 of 1000 resamples are at or below zero.
- **Stratum (ii) makes it negative.** Its four units are RUSH, PACED, STEALTH and LURK against EVADER. Under C-E6 each has GSB 31/64, because whole-tick disruption gives a Seat A attacker the tick-1 forced line against an EVADER that has not yet moved. Under the other three conditions each is within 3/64 of zero. So each has I_u of −15/32 or −7/16, and together they contribute −59/32 of I_all's total of −31/16. Strata (i) and (iii) contribute −3/32.
- **The negative sign is not a general finding.** It is the floor effect E7-DR §6.1 disclosed before the computation. Priced sensing removes a seat bias that only the whole-tick control had. It is not evidence that whole-tick disruption makes priced sensing more seat-neutral in general.
- **Where baselines match, the interaction is indeterminate.** In strata (i) and (iii), both controls carry the same baseline bias: neutral in (i), seat-determined in (iii). There the interaction is near zero, positive in about half the resamples.
- **The only positive lean is ADAPT's.** It is confined to the nine ADAPT units, 746 of 1000 above zero, all of which sit in stratum (i).

### 5.2 The common-neutral and flag forms (PF-4 lineage)

| Quantity | Point | Positive in |
|---|---|---|
| I_common_neutral (U*, 26 units) | −3/1664 | 519/1000 |
| … without ADAPT's units (17) | −5/544 | 249/1000 |
| … ADAPT's units (9) | +7/576 | 746/1000 |
| L(0), L(1) | 1/26, 0 | — |
| I_flag = L(0) − L(1) | 1/26 | 530/1000 |

**Units in U* with a positive I_u:** PACED–ADAPT +7/64, the ADAPT mirror +1/16, GREED–ADAPT +3/64 and EVADER–ADAPT +1/64. All four contain ADAPT, and every other unit in U* has I_u ≤ 0.

### 5.3 The full per-unit table (PA-4)

- **GSB** is the registered Seat A–Seat B balance. An asterisk marks a non-neutral value (SDom ≥ 9/10 or |GSB| > 1/10).
- **Decisive share** is the share of the unit's matches that end with a winner.
- **I_u** = (|G(T-E6)| − |G(C-E6)|) − (|G(T-E6L)| − |G(C-E6L)|).
- **Strata:** (i) neutral under both controls, (ii) under exactly one, (iii) under neither.

| Unit | Stratum | GSB C-E6 | GSB T-E6 | GSB C-E6L | GSB T-E6L | Decisive share T-E6 / T-E6L | I_u |
|---|---|---|---|---|---|---|---|
| `F1\|RUSH\|PACED` | (iii) | 1* | 7/16* | 1* | 27/64* | 1 / 63/64 | 1/64 |
| `F1\|RUSH\|SPLIT` | (iii) | 1* | 17/64* | 1* | 9/32* | 63/64 / 1 | −1/64 |
| `F1\|RUSH\|STEALTH` | (iii) | 1* | 0 | 1* | 5/64 | 1 / 63/64 | −5/64 |
| `F1\|RUSH\|LURK` | (iii) | 1* | 1/32 | 1* | 3/32 | 1 / 1 | −1/16 |
| `F1\|RUSH\|GUARD` | (i) | 0 | 0 | 0 | −1/32 | 1 / 1/32 | −1/32 |
| `F1\|RUSH\|EVADER` | (ii) | 31/64* | −1/64 | 0 | 0 | 3/64 / 0 | −15/32 |
| `F1\|RUSH\|GREED` | (i) | 0 | 0 | 0 | 0 | 1 / 1 | 0 |
| `F1\|RUSH\|ADAPT` | (i) | 0 | 1/64 | 0 | 3/64 | 45/64 / 25/64 | −1/32 |
| `F1\|PACED\|SPLIT` | (iii) | 1* | 9/64* | 1* | 7/64* | 63/64 / 63/64 | 1/32 |
| `F1\|PACED\|STEALTH` | (iii) | 1* | 1/32 | 1* | 0 | 1 / 31/32 | 1/32 |
| `F1\|PACED\|LURK` | (iii) | 1* | 3/32 | 1* | 3/32 | 1 / 1 | 0 |
| `F1\|PACED\|GUARD` | (i) | 0 | 0 | 0 | −1/32 | 1 / 1/32 | −1/32 |
| `F1\|PACED\|EVADER` | (ii) | 31/64* | −3/64 | 0 | 0 | 7/64 / 0 | −7/16 |
| `F1\|PACED\|GREED` | (i) | 0 | 0 | 0 | 0 | 1 / 1 | 0 |
| **`F1\|PACED\|ADAPT`** | (i) | 0 | **1/8*** | 0 | −1/64 | 13/16 / 7/64 | **7/64** |
| `F1\|SPLIT\|STEALTH` | (iii) | 1* | −5/32* | 1* | −1/32 | 1 / 31/32 | 1/8 |
| `F1\|SPLIT\|LURK` | (iii) | 1* | 0 | 1* | 0 | 1 / 1 | 0 |
| `F1\|SPLIT\|GUARD` | (i) | 0 | 0 | 0 | 0 | 1 / 1 | 0 |
| `F1\|SPLIT\|EVADER` | (i) | 0 | 0 | 0 | 0 | 1 / 1 | 0 |
| `F1\|SPLIT\|GREED` | (i) | 0 | 0 | 0 | 0 | 1 / 1 | 0 |
| `F1\|SPLIT\|ADAPT` | (i) | 0 | 0 | 0 | 0 | 1 / 1 | 0 |
| `F1\|STEALTH\|LURK` | (iii) | 1* | 0 | 1* | 0 | 1 / 1 | 0 |
| `F1\|STEALTH\|GUARD` | (i) | 0 | 1/64 | 0 | 3/64 | 55/64 / 49/64 | −1/32 |
| `F1\|STEALTH\|EVADER` | (ii) | 31/64* | −3/64 | 0 | −1/32 | 7/64 / 3/32 | −15/32 |
| `F1\|STEALTH\|GREED` | (i) | 0 | 0 | 0 | 0 | 1 / 1 | 0 |
| `F1\|STEALTH\|ADAPT` | (i) | 0 | 0 | 0 | 1/32 | 27/32 / 3/4 | −1/32 |
| `F1\|LURK\|GUARD` | (i) | 0 | 0 | 0 | 0 | 1 / 1 | 0 |
| `F1\|LURK\|EVADER` | (ii) | 31/64* | −1/32 | 0 | −1/64 | 15/16 / 59/64 | −15/32 |
| `F1\|LURK\|GREED` | (i) | 0 | 1/32 | 0 | −3/32 | 17/32 / 7/32 | −1/16 |
| `F1\|LURK\|ADAPT` | (i) | 0 | 1/32 | 0 | 3/32 | 1 / 1 | −1/16 |
| `F1\|GUARD\|EVADER` | (i) | 0 | 0 | 0 | 0 | 0 / 0 | 0 |
| `F1\|GUARD\|GREED` | (i) | 0 | 0 | 0 | 0 | 1 / 1 | 0 |
| `F1\|GUARD\|ADAPT` | (i) | 0 | 0 | 0 | 0 | 1 / 1 | 0 |
| `F1\|EVADER\|GREED` | (i) | 0 | 0 | 0 | 0 | 1 / 1 | 0 |
| `F1\|EVADER\|ADAPT` | (i) | 0 | 1/64 | 0 | 0 | 61/64 / 31/32 | 1/64 |
| `F1\|GREED\|ADAPT` | (i) | 0 | −5/64 | 0 | −1/32 | 63/64 / 1 | 3/64 |
| `F2\|RUSH\|RUSH` | (iii) | 1* | 5/32* | 1* | 5/32* | 25/32 / 25/32 | 0 |
| `F2\|PACED\|PACED` | (iii) | 1* | 7/32* | 1* | 1/8* | 25/32 / 9/16 | 3/32 |
| `F2\|SPLIT\|SPLIT` | (iii) | 1* | 1/16 | 1* | 5/32* | 15/16 / 27/32 | −3/32 |
| `F2\|STEALTH\|STEALTH` | (iii) | 1* | −1/16 | 1* | −3/32 | 15/16 / 19/32 | −1/32 |
| `F2\|LURK\|LURK` | (iii) | 1* | 1/32 | 1* | −3/32 | 17/32 / 7/32 | −1/16 |
| `F2\|GUARD\|GUARD` | (i) | 0 | 0 | 0 | 0 | 0 / 0 | 0 |
| `F2\|EVADER\|EVADER` | (i) | 0 | 0 | 0 | 0 | 0 / 0 | 0 |
| `F2\|GREED\|GREED` | (i) | 1/32 | 1/32 | −3/32 | −3/32 | 17/32 / 7/32 | 0 |
| `F2\|ADAPT\|ADAPT` | (i) | 0 | 3/32 | 0 | 1/32 | 25/32 / 21/32 | 1/16 |

PACED–ADAPT's decisive share is 13/16 under T-E6 and 7/64 under T-E6L. That is the GSB cap E7-DR §4.6 described: a unit that mostly draws cannot carry a large GSB, whatever its seat pattern.

---

## 6. PA-5: PF-4 Stability (O-BOOT, 1000 resamples)

| | Primary arm | Companion arm |
|---|---|---|
| stab(PF-4 raised), all 45 units | 967/1000 | 819/1000 |
| stab(PF-4 raised), the 36 units without ADAPT | 429/1000 | 477/1000 |

**The joint arm pattern:**

| Pattern | All units | Without ADAPT |
|---|---|---|
| Raised in both | 790 | 190 |
| **Primary only** (the observed E6 pattern) | **177** | 239 |
| Companion only | 29 | 287 |
| Neither | 4 | 284 |

**Units raising PF-4 across resamples:**
- **Primary:** PACED–ADAPT 752, the ADAPT mirror 549, LURK–GREED 421, GREED–ADAPT 257, LURK–ADAPT 157, RUSH–ADAPT 44, STEALTH–ADAPT 44, STEALTH–GUARD 17, EVADER–ADAPT 2.
- **Companion:** the ADAPT mirror 443, LURK–GREED 432, LURK–ADAPT 382, STEALTH–ADAPT 143, STEALTH–GUARD 100, RUSH–ADAPT 93, STEALTH–EVADER 19, GREED–ADAPT 17, LURK–EVADER 8, PACED–GUARD 6, RUSH–GUARD 6, PACED–ADAPT 4.

**PACED–ADAPT on its own:**
- Its signed interaction is +9/64, positive in 1000/1000. The 2.5%, 50% and 97.5% nearest-rank points are 3/64, 9/64 and 1/4.
- |GSB| > 1/10 in 752/1000 resamples under T-E6, and in 4/1000 under T-E6L.

These stabilities are hypothetical. The registered PF-4 is a point flag, and KC-5 fired exactly as registered.

---

## 7. PA-7: Mechanism Tables

### 7.1 PACED–ADAPT (E7-DR §4.2, §4.5, §4.6): reproduced

Every count E7-DR §4.2, §4.5 and §4.6 reports for PACED–ADAPT is reproduced exactly by an independent implementation (`mechanism.py`, not the review's scratch script). That is 28 checks:
- the outcomes by PACED's seat in all four conditions;
- PACED's first-detection ticks;
- ADAPT's first callback after contact;
- the cell and result of ADAPT's first check after contact;
- ADAPT's evasion ticks;
- outcomes with and without evasion;
- PACED's decision ticks;
- under T-E6L, 64 of 64 evasions and no silent tick for ADAPT.

The table itself is E7-DR §4.5.

**A check on the evasion definition.** An ADAPT evasion is defined as the MOVE at the callback right after a check that found damage. Any other ADAPT MOVE before its tick-17 hunt would falsify that definition. Across all 2,176 cells read there are **0** such MOVEs.

### 7.2 The named units (E7-DR §8.1, PA-7)

- **The columns.** Outcomes are for the first-named member (X) against the second (Y), by X's seat. "ADAPT evades" counts cells with an ADAPT evasion. "Silent" counts cells in which Y has at least one tick with no callback after X's first detection, within ticks 1–12.
- **Mirrors.** They use candidate-first cells only, with X in Seat A, so both ADAPTs are listed for the mirror.

| Unit | Condition | X in Seat A: X / tie / Y | X in Seat B: X / tie / Y | ADAPT evades (X@A; X@B) | Silent Y (X@A; X@B) |
|---|---|---|---|---|---|
| `F1\|PACED\|ADAPT` | C-E6 | 32 / 0 / 0 | 32 / 0 / 0 | 0; 32 | 0; 32 |
| | **T-E6** | **30 / 2 / 0** | **22 / 10 / 0** | **11; 22** | **32; 32** |
| | C-E6L | 0 / 32 / 0 | 0 / 32 / 0 | 32; 32 | 0; 0 |
| | T-E6L | 3 / 29 / 0 | 4 / 28 / 0 | 32; 32 | 0; 0 |
| `F1\|RUSH\|ADAPT` | C-E6 | 32 / 0 / 0 | 32 / 0 / 0 | 0; 32 | 0; 32 |
| | T-E6 | 23 / 9 / 0 | 22 / 10 / 0 | 26; 27 | 32; 32 |
| | C-E6L | 0 / 32 / 0 | 0 / 32 / 0 | 32; 32 | 0; 0 |
| | T-E6L | 14 / 18 / 0 | 11 / 21 / 0 | 32; 31 | 0; 0 |
| `F1\|STEALTH\|ADAPT` | C-E6 | 32 / 0 / 0 | 32 / 0 / 0 | 0; 32 | 0; 32 |
| | T-E6 | 27 / 5 / 0 | 27 / 5 / 0 | 11; 13 | 0; 0 |
| | C-E6L | 0 / 32 / 0 | 0 / 32 / 0 | 32; 32 | 0; 0 |
| | T-E6L | 25 / 7 / 0 | 23 / 9 / 0 | 13; 16 | 0; 0 |
| `F1\|LURK\|ADAPT` | C-E6 | 32 / 0 / 0 | 32 / 0 / 0 | 0; 32 | 0; 32 |
| | T-E6 | 4 / 0 / 28 | 3 / 0 / 29 | 2; 1 | 0; 0 |
| | C-E6L | 0 / 32 / 0 | 0 / 32 / 0 | 32; 32 | 0; 0 |
| | T-E6L | 6 / 0 / 26 | 3 / 0 / 29 | 2; 1 | 0; 0 |
| `F1\|GREED\|ADAPT` | C-E6 | 32 / 0 / 0 | 32 / 0 / 0 | 32; 30 | 0; 0 |
| | T-E6 | 1 / 0 / 31 | 3 / 1 / 28 | 2; 1 | 0; 0 |
| | C-E6L | 32 / 0 / 0 | 32 / 0 / 0 | 28; 24 | 0; 0 |
| | T-E6L | 4 / 0 / 28 | 5 / 0 / 27 | 2; 1 | 0; 0 |
| `F2\|ADAPT\|ADAPT` | C-E6 | 0 / 32 / 0 | — | 32 + 32 | 32 |
| | T-E6 | 14 / 7 / 11 | — | 0 + 8 | 0 |
| | C-E6L | 0 / 32 / 0 | — | 32 + 32 | 0 |
| | T-E6L | 11 / 11 / 10 | — | 0 + 8 | 0 |
| `F1\|LURK\|GREED` | C-E6 | 32 / 0 / 0 | 32 / 0 / 0 | — | 0; 32 |
| | T-E6 | 9 / 15 / 8 | 8 / 15 / 9 | — | 0; 0 |
| | C-E6L | 32 / 0 / 0 | 32 / 0 / 0 | — | 0; 0 |
| | T-E6L | 2 / 25 / 5 | 5 / 25 / 2 | — | 0; 0 |
| `F1\|PACED\|GUARD` | C-E6 | 32 / 0 / 0 | 32 / 0 / 0 | — | 0; 32 |
| | T-E6 | 32 / 0 / 0 | 32 / 0 / 0 | — | 32; 32 |
| | C-E6L | 0 / 32 / 0 | 0 / 32 / 0 | — | 0; 0 |
| | T-E6L | 0 / 32 / 0 | 2 / 30 / 0 | — | 0; 0 |
| `F1\|PACED\|EVADER` | C-E6 | 32 / 0 / 0 | 1 / 31 / 0 | — | 0; 32 |
| | T-E6 | 2 / 30 / 0 | 5 / 27 / 0 | — | 32; 32 |
| | C-E6L | 0 / 32 / 0 | 0 / 32 / 0 | — | 0; 0 |
| | T-E6L | 0 / 32 / 0 | 0 / 32 / 0 | — | 0; 0 |

**What the table adds to E7-DR, descriptively.** Nothing here is promoted to a finding.
- **PACED–GUARD is the cleanest comparison.**
  - GUARD is a stationary defender with no damage check.
  - Under T-E6 it is locked out exactly as ADAPT is (silent in 32 of 32 cells, from either seat).
  - Yet PACED captures it from both seats, 32 of 32. So it stays seat-neutral.
  - Lockout without a tick-keyed defender reaction produced no seat bias here.
- **RUSH–ADAPT is also locked out under T-E6,** in 32 of 32 cells, yet it is near seat-neutral (GSB 1/64).
- **STEALTH–ADAPT locks ADAPT out in none of its cells.** STEALTH finds cores by READ, so it rarely sees ADAPT's anchor.

So among the ADAPT pairings, whole-tick lockout is necessary but not sufficient for the PACED–ADAPT seat pattern. It also takes the alignment of PACED's paced search, its in-order core cursor and ADAPT's (*t* − 1) mod 8 schedule (E7-DR §4.5).

---

## 8. PA-8: The Lockout Characterization

`engine/tests/test_v6_e6_audit_lockout.py`, 16 tests, under all four E6 Rulesets. The attacker and victim are scripted, non-family executors on a directly constructed controller. Every callback is recorded, and no outcome is asserted.

**The preconditions each test asserts first, on the real run:**
- the rotation puts Seat A first on odd ticks and Seat B first on even ticks;
- the attacker is offered all eight of its offers every tick;
- every scripted hit lands on the victim's anchor, per `disruption_hits_received` and `disrupted_match_ticks`.

**What is then proven:**

| Ruleset | Attacker hits | Victim's offers in a tick the attacker moves first | … in a tick the victim moves first |
|---|---|---|---|
| `research-scale`, `research-sensing-r32` (whole tick) | its offer 0 | **none** | **0, 1** only |
| the same | offers 0, 2, 4 and 6 | none | 0, 1 only; the later hits still land |
| `research-disruption-slot1` and its sensing variant (λ = 1) | its offer 0 | 1–7 (loses 0) | 0, 1, 3–7 (loses 2) |
| the same | offers 0, 2, 4 and 6 | 1, 3, 5, 7 | 0, 1, 3, 5, 7 |

- **Whole tick.** A re-hit victim acts only on ticks of its own seat's parity: 1, 3 and 5 for Seat A; 2, 4 and 6 for Seat B.
- **Sensing is irrelevant to the rule.** Each rule holds identically with and without `detection_radius = 32`.
- **The effect.** This turns E7-DR §4.3's hand trace into a tested Ruleset characterization.

---

## 9. PA-9 and the Comparison with E7-DR

**Scope, as the record states it (`scope`):**

> Post-hoc description of E6's own frozen cells. It changes zero E6 registered findings: every E6 hypothesis status, pathology flag, kill criterion, interpretation row and disposition stands exactly as the frozen interpreter issued it. No match was run, no E6 record was edited, and nothing was written under runs/. The 9/10 bar is a research-program decision convention, never a hypothesis verdict.

**The comparison.** `run_audit.compare` checks 66 values E7-DR reports against PA's own computation, and finds **0 differences**. The values cover:
- the corpus pairing checks: 2,880 keys, 2,880 with identical geometry, and the T-E6/T-E6L first-seer agreement of 2,299 and 2,285 of 2,304;
- the neutral counts: 26, 38, 30 and 39;
- the stratum sizes: 26, 4 and 15;
- every §6.2 point value and stability;
- both joint arm patterns;
- the per-unit PF-4 crossings;
- the units with a positive interaction;
- the point PF-4 of each arm;
- the 28 PACED–ADAPT mechanism checks (LB-1), and the two values behind LB-2 and LB-3.

The full list is `review_comparison.checks` in the record.

## 10. The Adopted Decision Rule, Applied

E7-DR §8.1 as adopted (§16, OD-2):
- **Reproduction** of the load-bearing findings closes the interaction question with no E7 experiment.
- **A material disagreement** means STOP and reconcile.

| | |
|---|---|
| PA-1 and PA-2 | PASS |
| LB-1 to LB-4 | all hold (Answer in Brief) |
| Material disagreement | none |
| **Outcome** | **REPRODUCED: close the sensing × disruption interaction question with no E7 experiment** |

This is a decision-convention reading under the adopted rule, not a hypothesis verdict. The research lead confirmed it on 2026-09-29 (§13).

---

## 11. Hostile Self-Review and Limitations

1. **Not blind.** E7-DR had already computed every value except I_all. PA's independent re-implementation is a verification, not a test. I_all's definition, strata and 9/10 convention were committed in E7-DR at `4a135f8` before this run. E7-DR also discloses that its reviewer had seen per-unit interaction values before I_all was requested (E7-DR §6.1).
2. **I_all's sign reflects a baseline asymmetry.** It is negative because of stratum (ii), a floor effect of |GSB| that E7-DR recorded before the computation. It should not be quoted without its strata.
3. **Could a test pass while the mechanism never runs?**
   - PA-8's tests assert their preconditions (the hits land, the rotation holds) before any callback assertion.
   - Its whole-tick and one-offer tests run the same scripted play and require different, exact slot sequences.
   - The corpus-backed tests read real frozen cells.
   - The mechanism extractor's synthetic-row tests pin its definitions, and its real-artifact evidence is the exact reproduction of E7-DR's counts, which an independent script computed from the same rows.
4. **Definitions that could be wrong.**
   - The ADAPT evasion definition was checked against the rows: 0 unclassified moves.
   - "Silent tick" is bounded to ticks 1–12 (`WINDOW`).
   - Quantiles are nearest-rank at indices 25, 500 and 974 of 1000.
5. **Two corpus-backed tests skip where the git-ignored corpus is absent.** Their evidence is local to a machine that holds it.
6. **A type-check finding outside this work.** `mypy --explicit-package-bases tools/research/v6/e6_audit` reports one error. It is in the frozen `tools/research/v6/e6/telemetry.py:110` (a dict-comprehension value type) and predates this audit. The documented mypy scope is `engine/src` and `client/src`, and the frozen file was not modified. The audit's own modules are clean. On 2026-09-29 the research lead ruled that this error is not a blocker. It is recorded as a pre-existing, out-of-scope baseline issue, and the frozen E6 tooling is not modified to make a broader mypy invocation pass. The audit's qualification is its own tests and lint.
7. **Scope.** One family, arena 512, radius 32, two parents and 32 seeds, as in E6.

## 12. What This Record Does Not Claim

- **No E6 status changes.** No E6 record was edited.
- **No hypothesis verdict**, and no confirmatory claim.
- **No claim that whole-tick disruption makes priced sensing seat-neutral** (the sign of I_all; §5.1). None that λ = 1 removes seat artifacts, either (§6).
- **No product recommendation.** E6's `REJECT as a gameplay candidate` stands.
- **No generality** beyond the frozen family.

## 13. Decision of the Research Lead (2026-09-29)

**NO NEW EXPERIMENT. The sensing × disruption interaction question is closed.** The audit met the closure rule adopted in E7-DR §16: it reproduced the load-bearing findings with no material disagreement. I_all = −31/720, positive in 1/1000 resamples, gives no evidence that whole-tick disruption generally amplifies the seat-bias effect of priced sensing.

**The durable causal reading**, in the research lead's words:

> E6's KC-5 was a real unit-level interaction involving priced sensing, whole-tick lockout, and ADAPT's absolute-tick damage-check schedule. It was not evidence of a stable family-level sensing × disruption interaction.

- **Lockout is necessary, not sufficient.** GUARD is locked out under T-E6 just as ADAPT is, yet PACED–GUARD stays seat-neutral (§7.2). Whole-tick lockout is part of the PACED–ADAPT mechanism, but it does not produce the artifact by itself.
- **E6 stands as registered.** E6-D PASS, `R-CREATES` qualified by E6-H2 SUPPORTED, and `REJECT as a gameplay candidate` (KC-5) are unchanged. The audit explains the pathology; it does not retroactively rescue the candidate.
- **Not pursued.** E7-F (E7-DR §8.2) is not registered, and no fresh seed is generated.
- **Chronology.** E7 is closed at design review and audit, with no experiment executed. No E7 registration, matrix, seed or gameplay match exists. The next registered gameplay experiment, if V6 needs one, is **E8**; the E7 number is not reused for a different question.
- **Repository.**
  - The tooling and tests are committed at `22c9e76`, and this record and `pa_record.json` after them.
  - E6-R gains a dated addendum pointer to this record (OD-8). No E6 wording is changed.
- **What comes next.** The branch returns to the broader V6 question: which candidate follows from E6's positive strategic result.

This section replaces the four review requests of the draft submitted on 2026-09-29. The first three (confirm §10, commit, OD-8) are resolved above. The fourth, whether ROADMAP and FUTURE_PLANS should also record the closure, is still open.

---

## Appendix A. Reproduction and Digests

    python -m tools.research.v6.e6_audit.run_audit
    python -m pytest engine/tests/test_v6_e6_audit.py engine/tests/test_v6_e6_audit_lockout.py

| File | SHA-256 |
|---|---|
| `pa_record.json` | `b2c661fb1796f15d522c71584b5743ddf718025c98f06550a53ef2ba1a0bacdc` |
| `__init__.py` | `1fffb4f56cbc8a548ac438f5df5f843f40a72e33cf0c8aa1168875f6494e095e` |
| `corpus.py` | `498bd19c9edc838aeff90cc4a9fc1786d90c52e301479f8c9b89806bd5193b0b` |
| `decompose.py` | `157bbd601030f981e5e9a050fc425665072c0422ae43e16f74aab6b67329492a` |
| `estimands.py` | `476c2016b8f1a2ca88aa294a3a8c600938aa0cffaf35accbaab7f4250ebcfb77` |
| `mechanism.py` | `d410cad7324fb679df79dbc8ca0bfb17fc4c6ed0ceb06ecaa8b9feb5f3691d53` |
| `review_values.py` | `040a5f8cac313506ac3b9a95998af18398ffad6261789986b5ad8edd13784bcc` |
| `run_audit.py` | `dff8603c90978460e34f0cc6e98f6fcd8ac96c1876a5b0d7a09dfe176cc48434` |
| `seat.py` | `a6c03e7cce00f1a63c4415d5fd4ef0255677fd387e912a20ef4fc297a009ffbe` |
