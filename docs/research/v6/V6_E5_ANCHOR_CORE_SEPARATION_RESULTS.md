# Bytefray V6 E5 — Anchor/Core-0 Separation: Results

**Status:** The full frozen E5 matrix (7,168 matches) has been executed and analyzed.

- **Instrument.** Every measurement and the registered interpretation come from the frozen instrument of analysis freeze `v6-e5-freeze-v1-5ba12be258c8`.
- **Reading.** The hypotheses are read literally under the frozen pre-registration.

This is a research result, not a product decision.

**Branch:** `v6-research`. Controls were generated at `a6d1116`. The treatments were generated, gated and analyzed at `e6c789e`.
**Date:** 2026-09-25
**Authority:**
- [`V6_E5_ANCHOR_CORE_SEPARATION_DESIGN_REVIEW.md`](V6_E5_ANCHOR_CORE_SEPARATION_DESIGN_REVIEW.md) (§K hypotheses and pathology flags, §P V6 implications) and [`V6_E5_DESIGN_REVIEW_REVISION_1.md`](V6_E5_DESIGN_REVIEW_REVISION_1.md) (§R2 E5-D, §R5 census, §R6 interpretation).
- The pre-registration: `tools/research/v6/e5/preregistration.json`, SHA-256 `6e226fa8e620ff9c62bdbff46c7bc67af2331ae300607a4dcd1f8019a40818f4`.
- The freeze record [`V6_E5_EXPERIMENT_FREEZE.md`](V6_E5_EXPERIMENT_FREEZE.md) and the registration [`V6_E5_ANCHOR_CORE_SEPARATION_REGISTRATION.md`](V6_E5_ANCHOR_CORE_SEPARATION_REGISTRATION.md).
- The research lead's disposition of these results (2026-09-25), recorded in §I.

This record has three layers, and they are kept apart:

1. **Registered verdicts.** E5-D, E5-H1–H5, the pathology flags and D9 exactly as the frozen criteria evaluate them, including `NEITHER`.
2. **Registered interpretation.** The pre-registered interpretation table, applied as written.
3. **Descriptive synthesis.** What the data establish beyond the registered rules. It is labelled as description and is not a pre-registered disposition rule.

## Answer in brief

- **Registered verdicts (primary arm, C-E5 → T-E5):**
  - **E5-D PASS.** The decoupling manipulation gate holds in every treatment cell. **D9 HOLDS** with 0 completions.
  - **E5-H2 SUPPORTED.** 13 of the 17 SWEEP-BACKED P-BASE units STAY in their band: 13/17 ≈ 0.765, against a threshold of ≥ 2/3.
  - **E5-H1 NEITHER.** The other 4 units are NEUTRALIZED: 4/17 ≈ 0.235. Support needs ≥ 2/3, and refutation needs ≤ 1/10.
  - **E5-H3 REFUTED.** It measures continuity only: 18 of the 28 E4 residual units keep their FMA band, 9/14 < 9/10.
  - **E5-H4 NEITHER.** 64 of 1,344 F1 cells change outcome class (1/21). All 64 are lost captures, and none is gained.
  - **E5-H5 NEITHER.** \|2/21 − 1/21\| = 1/21.
  - **Pathology.** **PF-2 (stasis) and PF-3 (new immunity) are raised.** PF-1, PF-4 and PF-5 are not.
- **Registered interpretation: `R-H2-PRIME`.** Co-location is not necessary for the directed base privilege in a supermajority of sweep-backed contests. The four registered exceptions are named in §E. Combined with E4, this supports the second response in the opening exchange as the remaining mechanism. **The anchor/core forensic line closes.**
- **Descriptive synthesis.**
  - All 15 ANCHOR-ONLY units neutralized, and so did both MIXED-INFERENCE units.
  - Where the attacker already sweeps the core, separation mostly leaves the base privilege intact. Where the attacker's only core contact came through the co-located anchor, the privilege goes with the contact.
  - The K = 1 companion reproduces the primary census, with the same four exceptions.
  - Separation changes how matches end far more than who wins:
    - 190 of the 320 F1 captures disappear, and no new capture replaces them;
    - tick-limit endings rise from 1,024 to 1,214;
    - only 64 cells change outcome class, each a win becoming a tick-limit tie, and no winner is reversed.
- **Disposition (research lead; descriptive, not a registered rule).** Co-location creates free contact with the core, but not the directed second-mover base privilege in most contests where the attacker already attacks the core explicitly. On these results, and principally because of PF-2 and PF-3, `before_core` is **not recommended for promotion into the V6 gameplay Ruleset**. The E2–E5 forensic capture/order/placement line is closed (§I).

---

## A. Execution provenance

| Item | Value |
|---|---|
| Matrix | `v6-e5-matrix-v1-ef7fa327ea81` (digest `ef7fa327…8d28`), unchanged since the freeze |
| Instrument | Analysis freeze `v6-e5-freeze-v1-5ba12be258c8` (digest `5ba12be2…6227`): E5 analyzer v1, E5 cell metrics v1, E4 cell metrics v1, capture analyzer v2 and E3 action/parity analyzer v1. Freeze committed at `aab8fa4`, control qualification at `4d889e0`, mutation-gap tests at `acba511`, freeze record at `e6c789e`. `e6c789e` changed documentation only. |
| Pre-registration | `6e226fa8…18f4`, unchanged |
| Controls | C-E5 and C-E5K1, generated at `a6d1116` with a clean tree, 2026-09-25 01:31–01:46 UTC. Their 3,584 cells are byte-identical to the preserved E4 C-E4 and C-E4K1 cells. |
| Treatments | T-E5 and T-E5K1, generated at `e6c789e` with a clean tree, 2026-09-25 03:07–03:22 UTC (details below) |
| Treatment telemetry and gates | At `e6c789e` with a clean tree. `treatment_gates_T-E5.json` `8ad22140…7b4d` (03:24:57 UTC) and `treatment_gates_T-E5K1.json` `12f62950…7ef4` (03:25:05 UTC). Telemetry: T-E5 F1 `2cd6c46c…5001`, F2 `93f89e8d…80a3`; T-E5K1 F1 `d93eec27…b564`, F2 `abaa79ef…97c5`. |
| Analysis | `run_e5 analyze` at `e6c789e`, with a clean tree and unmodified, run after both treatment-gate records had passed (03:25:17 UTC). Output: `…/freezes/v6-e5-freeze-v1-5ba12be258c8/e5_analysis.json`, SHA-256 `1fa01a502ff9d07cfe6a6262da1578f7b31604373d479d921c15cc31ffeae09a`. |
| Environment | Python 3.13.14, `Windows-11-10.0.26120-SP0` |
| Retries | None (§G) |
| Artifacts | `runs/research_v6_e5/v6-e5-matrix-v1-ef7fa327ea81/{C-E5,T-E5,C-E5K1,T-E5K1}/{F1,F2}`. Every `result.json` and replay is preserved (git-ignored). |

Record hashes are SHA-256 of the LF-normalized bytes, the convention by which the tooling pins its records (`record_sha256`).

**How the treatments ran:**

| Condition | Field | Cells | Provenance timestamp (UTC) | Last cell completed (UTC) |
|---|---|---|---|---|
| T-E5 | F1 | 1,344 | 03:07:43 | 03:22:03 |
| T-E5 | F2 | 448 | 03:07:46 | 03:12:09 |
| T-E5K1 | F1 | 1,344 | 03:07:49 | 03:21:11 |
| T-E5K1 | F2 | 448 | 03:07:51 | 03:11:37 |

- **Invocation and guards.** The four fields ran as parallel processes through `run_e5 execute` with both confirmations; the runner refuses a treatment without them. Each execution re-runs the full unlock chain and the execution-source check before its first cell.
- **Provenance.** Every field's provenance names `e6c789e`, `git_dirty: false`, the frozen matrix digest, freeze id and pre-registration SHA-256, and the treatment Ruleset.
- **Worker count.** The command registered in the freeze record uses `--workers 1`. Field provenance does not record the worker count.

**Verification made for this record, before anything was written:**

- `HEAD` was still `e6c789e`, and the tracked tree was clean.
- `run_e5`'s `treatment_unlock` passed. It fails closed on any tooling drift from the freeze, on any control-record SHA mismatch and on any population that no longer recomputes.
- The frozen evaluation was re-run in memory through the runner's own loading and `evaluate_hypotheses` calls, without writing. It reproduces the `result` block of `e5_analysis.json` exactly.

Nothing in the instrument changed after the treatments ran.

## B. Gates

**Before treatment** (from the [freeze record](V6_E5_EXPERIMENT_FREEZE.md)):

- **Parent reproduction: FULL PASS.** 3,584 cells are byte-identical to the preserved E4 control corpus.
- **Analyzer qualification: PASS.** 7,168 control replays with 0 failures, 0 disagreements and 0 second-pass differences.
- **Frozen populations.** The primary P-BASE has 34 units: 17 SWEEP-BACKED, 15 ANCHOR-ONLY and 2 MIXED-INFERENCE. O-MIN-SB passes, 17 ≥ 6.
- **Control census and clauses.** The control-against-control census is 100% identity classes. The control-side D-5 and D-6 clauses pass, and the global null reads STOP.
- **Non-matrix gates.** The P5 inertness, observation-delta and D9 real-fixture gates all passed.

**Treatment gates.** Both passed; any failure would have been a hard STOP.

| | T-E5 | T-E5K1 |
|---|---|---|
| Corpus integrity (F1, F2) | PASS: 1,344 and 448 cells, generated at `e6c789e` with a clean tree | PASS (the same) |
| Manipulation checks in every cell (E4's hard stops 5–7 with forward passes, and the E5 metrics' own cross-checks) | PASS | PASS |
| E5-D D-1 to D-4, per cell | PASS: 0 violations in 1,792 cells | PASS: 0 in 1,792 |
| E5-D D-5, per ANCHOR-ONLY P-BASE unit (anchor-induced core-0 contact absent in treatment) | PASS: 544 directed cells, 0 failures | PASS: 544, 0 |
| Twin relabel gate (F2) | PASS: 224 pairs, 0 failures | PASS: 224, 0 |
| **E5-D** | **PASS** | **PASS** |
| Completions against the repair and disrupt guards (and twins) | **0: D9 holds, no stop** | 0 (reported; the companion is never a stop) |

## C. Corpus

| Condition | F1 | F2 | Total |
|---|---|---|---|
| C-E5 | 1,344 | 448 | 1,792 |
| T-E5 | 1,344 | 448 | 1,792 |
| C-E5K1 | 1,344 | 448 | 1,792 |
| T-E5K1 | 1,344 | 448 | 1,792 |
| **Total** | | | **7,168** |

**Units and evidence (O-BP-UNIT, O-EVIDENCE):**

- **The unit.** The directed unit: each ordered round-robin matchup gives two, one per victim seat, and each twin mirror gives one. That makes 91 per arm.
- **n_distinct.** It counts distinct (control, treatment) trajectory pairs over a unit's 32 seeds.
- **SWEEP-BACKED P-BASE (17).**
  - 13 units are deterministic characterizations (n_distinct = 1).
  - 4 are rate-eligible (n_distinct 28–31), and all four STAY.
  - No unit lies within 1/50 of a band edge in either arm.
- **ANCHOR-ONLY P-BASE (15).** 9 rate-eligible, 5 deterministic and 1 limited (n_distinct 2).
- **How to read the counts.** E5-H1 and E5-H2 are census counts of unit characterizations (evidence rule 2), not rates.
- **Thresholds in whole units.** With N = 17, SUPPORTED needs at least 12 units, REFUTED at most 1, and 2 to 11 reads NEITHER.
- **Rate-eligible values.** E5-H4 and E5-H5 are rate-eligible: n_distinct 305 (primary) and 310 (companion).

---

## D. Layer 1 — Registered verdicts

### D.1 Primary arm (C-E5 → T-E5)

| ID | Statement | Status | Frozen criterion value | Evidence |
|---|---|---|---|---|
| E5-D | Decoupling manipulation gate (a hard stop; it reads no gameplay outcome) | **PASS** | D-1 to D-4: 0 violations in every treatment cell. D-5: 0 failures. D-6 and the control side of D-5 passed before treatment. | Gate |
| E5-H1 | Co-location carries the directed base privilege | **NEITHER** | NEUTRALIZED + WEAKENED + FLIPPED = **4 / 17 ≈ 0.235** (4 NEUTRALIZED, 0 WEAKENED, 0 FLIPPED). Support needs ≥ 2/3; refutation needs ≤ 1/10. | Census of 17 SB P-BASE units; 13 deterministic |
| E5-H2 | Co-location is not necessary for the directed base privilege | **SUPPORTED** | STAYS + STRENGTHENED = **13 / 17 ≈ 0.765** (13 STAYS, 0 STRENGTHENED), ≥ 2/3 | The same census |
| E5-H3 | Residual-population null (E4 continuity only) | **REFUTED** | E4 STAYS + UNCHANGED-NEUTRAL = **18 / 28 = 9/14 ≈ 0.643** (< 9/10). 18 STAYS, 10 NEUTRALIZED. | 28 P-PAR-E5 units |
| E5-H4 | Separation changes match outcomes (K = 2) | **NEITHER** | Outcome-class change in **64 / 1,344 = 1/21 ≈ 0.048** of F1 cells. Support needs ≥ 1/10; refutation needs ≤ 1/50. **Direction:** all 64 are captures lost (capture wins become tick-limit ties); 0 captures are gained. | n_distinct 305; rate-eligible |
| E5-H5 | The capture hold changes how much separation changes outcomes | **NEITHER** | \|companion − primary\| = \|128/1,344 − 64/1,344\| = **1/21 ≈ 0.048** | n_distinct 310 and 305; rate-eligible |
| D9 | G.5 immunity under T-E5 (theorem; a hard stop) | **HOLDS** | **0** completions against the repair and disrupt guards (and twins) in all 1,792 T-E5 cells | Theorem check |

No SB P-BASE unit is DECIDED-EARLY (0 of 17).

### D.2 The H1 status, stated plainly

E5-H1 is `NEITHER`, not REFUTED. Four of the 17 units are NEUTRALIZED. The frozen refutation threshold of ≤ 1/10 admits at most one. This record never treats H1 as refuted, and the four units stand as real, registered exceptions (§E).

### D.3 Pathology flags (primary F1, recorded whatever else holds)

| Flag | Frozen value | Raised? |
|---|---|---|
| PF-1 new captures | 0 of the 1,024 control non-capture cells become captures | No |
| PF-2 stasis | Tick-limit share 1,024 / 1,344 (16/21) → **1,214 / 1,344** (607/672): a rise of 190 / 1,344 ≈ 0.141, ≥ 1/10 | **Yes** |
| PF-3 new immunity | **190 of 320** control capture cells (19/32 ≈ 0.594) become non-captures | **Yes** |
| PF-4 loss of interaction | Cells with no hostile core contact in either direction: 0 → 64 (1/21); the rise is below 1/10 | No |
| PF-5 seat artifact | No pairing or mirror newly reaches SDom ≥ 9/10 or \|GSB\| > 1/10 | No |

### D.4 Companion arm (C-E5K1 → T-E5K1): an H5 input, not a verdict

The companion feeds E5-H5 and companion readings only, and it never replaces a primary verdict.

- **Its SB census.** 15 units: **11 STAYS and 4 NEUTRALIZED** (§F.8).
- **D9.** It reports **0** completions under T-E5K1.

## E. Layer 2 — Registered interpretation

The frozen rule: a row applies if and only if E5-D has the row's status and the pair (E5-H1, E5-H2) is one of the row's listed combinations. Every combination is listed in exactly one row or as impossible, and an impossible one fails closed.

The inputs are **(E5-D PASS, E5-H1 NEITHER, E5-H2 SUPPORTED)**.

| Row | Requires | Fires? |
|---|---|---|
| STOP | E5-D FAIL | No: E5-D is PASS |
| R-H2 | PASS; (REFUTED, SUPPORTED) | No: H1 is NEITHER |
| **R-H2-PRIME** | PASS; (NEITHER, SUPPORTED) | **Yes** |
| R-H1 | PASS; (SUPPORTED, REFUTED) | No |
| R-H1-PRIME | PASS; (SUPPORTED, NEITHER) | No |
| NONE | PASS; the four NEITHER/REFUTED mixes | No |

Exactly one row matches, and no invariant violation was raised. **The registered outcome is `R-H2-PRIME`.** Its frozen reading, verbatim:

> Co-location is not necessary for the directed base privilege in a supermajority of SB contests. Removing the dual-purpose anchor/core write leaves the SB privilege intact in those contests; the SB units that weakened, neutralized or flipped are named as registered exceptions. Combined with E4's finding that the OPENING-ONLY privilege survives mirrored later-pass order, this supports the second response in the opening exchange as the remaining mechanism. The anchor/core forensic line closes.

**The registered exceptions.** The four SB units that neutralized; none weakened or flipped:

| Unit (Seat A \| Seat B \| victim) | Attacker → victim | Control BP → T-E5 BP | Class | E4 class | n_distinct |
|---|---|---|---|---|---|
| F1 min_guard \| repair_guard \| B | min guard → repair guard | 1/2 → 1/4 | NEUTRALIZED | MULTI-PASS | 1 |
| F1 min_guard \| spread_defender \| B | min guard → spread defender | 1 → 1/500 | NEUTRALIZED | OPENING-ONLY | 1 |
| F1 sniper \| spread_defender \| B | sniper → spread defender | 1 → 1/500 | NEUTRALIZED | OPENING-ONLY | 1 |
| F1 spread_defender \| repair_guard \| B | spread defender → repair guard | 249/500 → 1/4 | NEUTRALIZED | MULTI-PASS | 1 |

**Recorded alongside, and not inputs to the interpretation:**

- **E5-H3 REFUTED.** Continuity only: "never a mechanism reading".
- **E5-H4 NEITHER.** Recorded with its direction: captures lost, none gained.
- **E5-H5 NEITHER.** A companion reading.
- **PF-2 and PF-3 raised.** Recorded as pathologies, whatever else holds.
- **D9 holds.**

---

## F. Layer 3 — Descriptive synthesis

*Everything in this section describes frozen outputs:*

- *the unit rows in `e5_analysis.json`;*
- *the companion's unit rows, computed by the frozen `unit_rows` over the same telemetry;*
- *tallies made with the analyzer's own helpers: `outcome_class`, `is_capture`, `is_tick_limit`, `_no_core_contact`, `d9_completions`, and E4's `unit_rows` and `units`;*
- *the frozen per-cell directed contact counts in the E5 telemetry: core-0 writes, mean core coverage per both-alive tick, and the first contact tick.*

*No threshold, row or metric is added. BP > 0 means the victim owns its base (core cell 0) more often at the end of its second-mover ticks than of its first-mover ticks.*

### F.1 The manipulation took (E5-D; a gate, not a finding)

In every treatment cell, the checks below held. Together they show the intervention is exactly the registered one: where a process spawns, and nothing else.

- **Spawn.** Every default spawn is at `pc − 1`.
- **Dual writes.** No hostile write is both an anchor hit and a write to the same victim's core.
- **Own core.** No process ever sits on its own core.
- **Anchor-only contact.** Every ANCHOR-ONLY P-BASE unit loses the attacker's anchor-induced core-0 contact.

The frozen contact counts show the size of that change. In the 15 ANCHOR-ONLY units and the 2 MIXED-INFERENCE units:

- the attacker's median core coverage falls from about one cell per both-alive tick (1.00–1.08) to 0–0.08;
- its median core-0 writes per match fall from 104–1,010 to 0–10.

### F.2 SWEEP-BACKED: the privilege mostly stays (E5-H2)

| Unit (Seat A \| Seat B \| victim) | Attacker → victim | Control BP | T-E5 BP | Class | E4 class | n_distinct | K = 1 class |
|---|---|---|---|---|---|---|---|
| F1 disrupt_guard \| min_guard \| A | min guard → disrupt guard | 1 | 1 | STAYS | MULTI-PASS | 1 | STAYS |
| F1 disrupt_guard \| sniper \| A | sniper → disrupt guard | 1 | 1 | STAYS | MULTI-PASS | 1 | STAYS |
| F1 guarded_painter \| min_guard \| A | min guard → guarded painter | 1 | 497/500 | STAYS | OPENING-ONLY | 31 | STAYS |
| F1 guarded_painter \| sniper \| A | sniper → guarded painter | 1 | 1 | STAYS | OPENING-ONLY | 28 | STAYS |
| F1 min_guard \| disrupt_guard \| B | min guard → disrupt guard | 1 | 1 | STAYS | MULTI-PASS | 1 | STAYS |
| F1 min_guard \| guarded_painter \| B | min guard → guarded painter | 1 | 497/500 | STAYS | OPENING-ONLY | 28 | STAYS |
| F1 min_guard \| repair_guard \| B | min guard → repair guard | 1/2 | 1/4 | **NEUTRALIZED** | MULTI-PASS | 1 | NEUTRALIZED |
| F1 min_guard \| sniper \| A | sniper → min guard | 1 | 1 | STAYS | OPENING-ONLY | 1 | STAYS |
| F1 min_guard \| spread_defender \| B | min guard → spread defender | 1 | 1/500 | **NEUTRALIZED** | OPENING-ONLY | 1 | NEUTRALIZED |
| F1 sniper \| disrupt_guard \| B | sniper → disrupt guard | 1 | 1 | STAYS | MULTI-PASS | 1 | STAYS |
| F1 sniper \| guarded_painter \| B | sniper → guarded painter | 1 | 1 | STAYS | OPENING-ONLY | 28 | STAYS |
| F1 sniper \| min_guard \| B | sniper → min guard | 1 | 1 | STAYS | OPENING-ONLY | 1 | STAYS |
| F1 sniper \| repair_guard \| B | sniper → repair guard | 1/2 | 1/2 | STAYS | MULTI-PASS | 1 | not in P-BASE (DECIDED-EARLY control) |
| F1 sniper \| spread_defender \| B | sniper → spread defender | 1 | 1/500 | **NEUTRALIZED** | OPENING-ONLY | 1 | NEUTRALIZED |
| F1 spread_defender \| repair_guard \| B | spread defender → repair guard | 249/500 | 1/4 | **NEUTRALIZED** | MULTI-PASS | 1 | NEUTRALIZED |
| F1 spread_sniper \| repair_guard \| B | spread sniper → repair guard | 1/2 | 249/500 | STAYS | MULTI-PASS | 1 | not in P-BASE (DECIDED-EARLY control) |
| F2 min_guard mirror | each twin → the other | 1 | 1 | STAYS | OPENING-ONLY | 1 | STAYS |

- **The 13 STAYS units.**
  - Nine sit at BP 1 under both control and treatment, and two move from 1 to 497/500. At BP 1, the victim owns its base at the end of every one of its second-mover ticks and none of its first-mover ticks.
  - Two repair-guard units stay at about 1/2.
  - All four rate-eligible SB units are among them.
- **By E4 stratum** (a descriptive secondary stratum only): OPENING-ONLY 7 STAYS and 2 NEUTRALIZED; MULTI-PASS 6 STAYS and 2 NEUTRALIZED. The privilege does not follow E4's contest class.
- **What the sweeper loses.** In every cell of all 17 units, the attacker's first hostile contact (a core or anchor write) is at tick 1 in both arms. Its median core-0 writes per match are unchanged or higher, so it keeps attacking the base. What it loses is **one cell of core coverage per both-alive tick**: the per-cell drop is 0.97–1.03 cells with a median of exactly 1 (for example 7 → 6 or 4 → 3):
  - under co-location, the anchor hit was also a core write;
  - under separation, disrupting the process and writing the core are separate writes;
  - the scripted fixtures do not choose between them.

  The design review's probe had predicted this (its Ch 6: "Coverage drops by one cell per tick").

### F.3 The four exceptions

- **Stable across arms.** The same four units neutralize under K = 1 (§F.8). Each is a deterministic characterization (n_distinct = 1) in both arms, so none is a seed effect.
- **They cluster by victim:**
  - every SB unit whose victim is the disrupt guard, the guarded painter or the min guard stays (11 of 11);
  - both SB units against the **spread defender** neutralize (1 → 1/500). So do both MIXED-INFERENCE units, which are also sweeper attacks on the spread defender (499/500 → 0). Every P-BASE attack on the spread defender loses its base privilege under separation;
  - the **repair guard**'s four SB units split by attacker. When the min guard or the spread defender attacks it, its BP halves, from about 1/2 to 1/4. That crosses the 1/3 band edge by 1/12, well outside the 1/50 near-boundary flag. When the sniper or the spread sniper attacks it, its BP stays at about 1/2.
- **Coverage does not explain them.** The one-cell coverage loss of §F.2 is common to the STAYS units and the exceptions, so it does not distinguish them on its own.

No mechanism for the exceptions is established here. None is sought: under the disposition (§I), no further experiment is registered for them.

### F.4 ANCHOR-ONLY: 15 of 15 neutralized

| Unit (Seat A \| Seat B \| victim) | Attacker → victim | Control BP | T-E5 BP | E4 class | n_distinct |
|---|---|---|---|---|---|
| F1 disrupt_guard \| guarded_painter \| A | guarded painter → disrupt guard | 124/125 | 1/500 | OPENING-ONLY | 8 |
| F1 disrupt_guard \| guarded_painter \| B | disrupt guard → guarded painter | 497/500 | 0 | OPENING-ONLY | 8 |
| F1 disrupt_guard \| min_guard \| B | disrupt guard → min guard | 1 | 0 | MULTI-PASS | 1 |
| F1 disrupt_guard \| repair_guard \| B | disrupt guard → repair guard | 1/2 | 0 | OPENING-ONLY | 1 |
| F1 disrupt_guard \| spread_defender \| B | disrupt guard → spread defender | 1 | 0 | MULTI-PASS | 1 |
| F1 guarded_painter \| disrupt_guard \| A | disrupt guard → guarded painter | 124/125 | 0 | OPENING-ONLY | 8 |
| F1 guarded_painter \| disrupt_guard \| B | guarded painter → disrupt guard | 124/125 | 1/500 | OPENING-ONLY | 8 |
| F1 guarded_painter \| min_guard \| B | guarded painter → min guard | 1 | 1/500 | OPENING-ONLY | 31 |
| F1 guarded_painter \| spread_defender \| B | guarded painter → spread defender | 1 | 0 | OPENING-ONLY | 31 |
| F1 min_guard \| disrupt_guard \| A | disrupt guard → min guard | 1 | 0 | MULTI-PASS | 1 |
| F1 min_guard \| guarded_painter \| A | guarded painter → min guard | 1 | 1/500 | OPENING-ONLY | 28 |
| F1 spread_defender \| disrupt_guard \| A | disrupt guard → spread defender | 499/500 | 0 | MULTI-PASS | 2 |
| F1 spread_defender \| guarded_painter \| A | guarded painter → spread defender | ≈ 0.992 | 0 | OPENING-ONLY | 31 |
| F2 disrupt_guard mirror | each twin → the other | 1 | 0 | OPENING-ONLY | 1 |
| F2 guarded_painter mirror | each twin → the other | ≈ 0.985 | 1/500 | OPENING-ONLY | 32 |

- **Where they land.** Every ANCHOR-ONLY unit lands at BP 0 or 1/500, and 9 of the 15 are rate-eligible. The companion reads the same 15 of 15.
- **Not a gate.** Revision 1 §R2 removed the original review's requirement that every ANCHOR-ONLY unit be neutral, and made E5-D contact-based so that the gate reads no gameplay outcome. **This 15 of 15 is therefore an outcome, reported descriptively; it is not part of E5-D.**
- **The contrast.** Read with §F.2, this is the contrast the design was built to separate. Where the attacker already sweeps the core, moving the anchor mostly leaves the base privilege intact. Where the attacker's only core contact came through the co-located anchor, the privilege goes with that contact.

**MIXED-INFERENCE (frozen, reported, excluded from H1 and H2).** `F1 spread_defender | min_guard | A` and `F1 spread_defender | sniper | A` both go from 499/500 to 0 (n_distinct 2) in both arms.

### F.5 Units outside P-BASE

Of the 91 primary units, 52 are UNCHANGED-NEUTRAL, 34 are P-BASE (above), 4 are DECIDED-EARLY and **1 is NEW**. No unit FLIPPED or became first-side.

- **NEW: `F1 spread_sniper | spread_defender | B`** (spread sniper → spread defender; SWEEP-BACKED by class, but neutral in control, so outside P-BASE).
  - **Control.** BP is 0 in 31 of 32 seeds. The spread defender owns its base at the end of every both-alive tick, whichever seat moves first.
  - **T-E5.** BP is 1 in all 32 seeds. The spread defender owns its base at the end of all 500 ticks on which it moves second, and of none on which it moves first.
  - **Companion.** The same holds under K = 1.
  - **What it shows.** Separation also *creates* the directed second-mover parity signature where none existed. It is outside every registered census, and n_distinct is 2.
- **DECIDED-EARLY.** The four control DECIDED-EARLY units are the sniper ↔ spread sniper directed units (three SB, one MIXED). Their control cells end early by capture. Under T-E5 the captures are gone (§F.7), and the units are DEFINED at BP 0.

### F.6 E5-H3: which E4 residual matchups left their band

Ten of the 28 P-PAR-E5 matchups are NEUTRALIZED in FMA band. Negative FMA favours the tick's second mover.

| Matchup (Seat A v Seat B) | E4 class | Control FMA | T-E5 FMA | n_distinct |
|---|---|---|---|---|
| disrupt guard v guarded painter | OPENING-ONLY | −1.001 | −0.009 | 8 |
| guarded painter v disrupt guard | OPENING-ONLY | −1.002 | −0.011 | 8 |
| guarded painter v spread defender | OPENING-ONLY | −0.509 | −0.0065 | 31 |
| spread defender v guarded painter | OPENING-ONLY | −0.501 | −0.002 | 31 |
| spread defender v min guard | OPENING-ONLY | −0.501 | −0.002 | 2 |
| spread defender v sniper | OPENING-ONLY | −0.501 | −0.002 | 2 |
| disrupt guard mirror (F2) | OPENING-ONLY | −1.000 | 0.000 | 1 |
| guarded painter mirror (F2) | OPENING-ONLY | −0.991 | −0.003 | 32 |
| disrupt guard v spread defender | MULTI-PASS | −0.501 | −0.001 | 1 |
| spread defender v disrupt guard | MULTI-PASS | −0.501 | −0.002 | 2 |

- **Which matchups.** The ten are **exactly the P-PAR-E5 matchups whose P-BASE directed units are all ANCHOR-ONLY or MIXED-INFERENCE**, and every one of those units neutralized (§F.4).
- **Which stayed.** Each of the 14 P-PAR-E5 matchups that contains a SWEEP-BACKED P-BASE unit kept its FMA band. That includes the two whose SB unit neutralized in BP (min guard v repair guard −1 → −0.75; spread defender v repair guard −0.995 → −0.749). The other four STAYS matchups contain no P-BASE unit.
- **By E4 class.** 8 of E4's 14 OPENING-ONLY units and 2 of its 14 MULTI-PASS units left their band.
- **Magnitude changes inside a band.** Some STAYS matchups changed magnitude without leaving their band, as the review's probe predicted (AF-2): disrupt guard ↔ min guard −3.5 → −1.5, disrupt guard ↔ sniper −2.0 → −3.0, and guarded painter ↔ min guard about −1.0 → about −0.5.

As registered, H3 is continuity only. It says that 10 of E4's 28 residual matchups in this field depended on anchor-only contact. It is not a mechanism reading, and it does not bear on the SB privilege that H1 and H2 address.

### F.7 Outcomes: how matches end changes far more than who wins (H4, PF-1–PF-4)

**Primary F1:**

| 1,344 cells | C-E5 | T-E5 |
|---|---|---|
| Captures | 320 | 130 |
| Tick-limit endings | 1,024 | **1,214** |
| — tick-limit ties | 896 | 960 |
| — tick-limit wins on score | 128 | 254 |
| Seat A wins / Seat B wins | 224 / 224 | 192 / 192 |

**Outcome classes.** 1,280 cells keep their outcome class: 192 Seat-A wins, 192 Seat-B wins and 896 ties. The other **64** go from a win to a tick-limit tie. No winner is reversed, and no tie becomes a win.

**Where the 320 control captures go.** They are 10 matchups × 32 seeds:

| Control captures | Cells | Under T-E5 |
|---|---|---|
| The guarded painter captures the sniper and the spread sniper (both orientations) | 128 | All still captures |
| The guarded painter captures the min guard and the spread defender (both orientations) | 128 | 126 become tick-limit **wins for the same seat**; 2 are still captures (one seed each, both with the guarded painter in Seat A) |
| The spread sniper captures the sniper (both orientations) | 64 | All become **tick-limit ties**: these are E5-H4's 64 outcome changes |

- **The 190 lost captures (PF-3).** 126 keep their winner, and 64 become ties. No new capture appears anywhere (PF-1: 0 of 1,024).
- **PF-4's 64 cells.** They are the disrupt guard against the repair guard, both orientations, every seed. Neither sweeps. Under separation neither makes any hostile core write, whereas every one of these cells had core contact in control. They are 0-capture tick-limit ties in both arms, so no outcome changes.

**Primary F2.** Only the guarded-painter mirror changes.

- **Captures.** They fall from 32 to 1 in each orientation.
- **Tick-limit endings.** They rise from 384 to 446.
- **Winners.** In 16 of its 32 seeds the winning seat changes, 8 each way, so its seed split stays at 19 A / 13 B.
- **The other mirrors.** The other six are tick-limit ties in both arms.
- **Seats.** PF-5 finds no newly seat-dominant or biased unit.

In the research lead's words, separation "substantially changes **how matches resolve** without substantially changing **who ends up winning**" (§I).

### F.8 The companion arm (K = 1)

- **SB census.** 11 STAYS and 4 NEUTRALIZED of 15 units. The four NEUTRALIZED are **the same four exceptions**, each at n_distinct 1. The primary's `sniper → repair guard` and `spread sniper → repair guard` units are DECIDED-EARLY under C-E5K1, where the repair guard is captured, so they are not companion P-BASE units.
- **The other units.** ANCHOR-ONLY is 15 of 15 NEUTRALIZED, MIXED-INFERENCE 2 of 2, and the NEW unit of §F.5 recurs.
- **F1 outcomes.** **128 of 1,344** cells change outcome class (2/21). Captures fall from 384 to 256, tick-limit endings rise from 960 to 1,088, and no capture is gained. The 128 changed cells are:
  - the sniper's and the spread sniper's Seat-A captures of the repair guard (64), which become tick-limit ties;
  - the spread sniper's captures of the sniper (64), also ties.
- **Guard completions.** They go from **64** under C-E5K1 to **0** under T-E5K1: separation closes the K = 1 captures of the repair guard. The design review's probe predicted this ("sniper v repair guard goes from a capture at tick 8 to a tie").
- **Where K matters.** Under K = 1, all 256 capture cells in the guarded painter's pairings survive separation, including its 128 captures of the min guard and the spread defender. Under K = 2, 126 of those 128 are lost (§F.7). The hold and separation interact at capture resolution. Their effect on the outcome-change share differs by 1/21, between E5-H5's thresholds.
- **Companion F2.** The guarded-painter mirror's 15 mutual eliminations become wins, and its split goes from 7 A / 10 B / 15 mutual to 19 A / 13 B.

The companion does not reverse or hide the primary reading. The SB census, the exceptions and the ANCHOR-ONLY collapse are the same under both holds. K = 1 differs in which captures survive.

### F.9 The design review's probe priors, compared with the matrix

| Hypothesis | Probe prior (disclosed before the freeze) | Matrix | |
|---|---|---|---|
| E5-D | Holds | PASS | Reproduced |
| E5-H1 | Fails | NEITHER (4/17) | Not supported, as predicted, but not refuted |
| E5-H2 | Supported ("every SB unit probed: BP 1.0 → 1.0, or 0.5 → 0.5") | SUPPORTED (13/17) | Verdict reproduced. **"Every SB unit" not reproduced**: four neutralized, including two repair-guard units at 1/2 → 1/4 |
| E5-H3 | Refuted, through the AO units | REFUTED (18/28) | Reproduced: the ten are the AO- and MIXED-only matchups (§F.6) |
| E5-H4 | Uncertain (the painter pairings change) | NEITHER (1/21) | **Not reproduced as stated**: the painter pairings lose captures but keep their winners; the changed cells are the sniper ↔ spread sniper pairing |
| E5-H5 | Likely: the two arms change different cells | NEITHER (1/21) | **Not reproduced**: the arms share 64 changed cells, and the difference is below 1/10 |
| PF-3 | New immunity under K = 1; lost painter captures under K = 2 | Raised (190/320); companion guard captures 64 → 0 | Reproduced |
| Contact (Ch 6) | Coverage drops by one cell per tick | −1 cell per tick in all 17 SB units | Reproduced |

As in E4, the probe got the verdict-level picture right, but not every unit-level detail.

### F.10 Synthesis

**Separating the spawn anchor from core cell 0 removed the free core contact that the dual-purpose write supplied, and with it every base privilege that rested only on that contact. It left the directed second-mover base privilege intact in 13 of 17 contests where the attacker already attacked the core explicitly. It cost the game a large share of its decisive endings without changing who wins.**

The evidence:

- **SWEEP-BACKED.** 13 STAYS and 4 NEUTRALIZED, the same four under both holds (§F.2, §F.3, §F.8).
- **ANCHOR-ONLY.** 15 of 15 NEUTRALIZED, 9 of them rate-eligible (§F.4).
- **Created privilege.** One neutral contest *gains* the second-mover parity signature under separation (§F.5).
- **Outcomes.**
  - 190 of 320 F1 captures are lost and none is gained;
  - tick-limit endings rise by 190;
  - only 64 cells change outcome class, all from a win to a tie, with no winner reversed (§F.7).

The SB counts are census counts of mostly deterministic unit characterizations (13 of 17 rest on one trajectory). They are mechanistically consistent, but they are not population-rate evidence.

---

## G. Execution note

- **No retries.** No cell failed, and no field was re-run:
  - each field's provenance timestamp precedes its first completed cell by under a second;
  - every field holds its full cell set;
  - no quarantine directory exists under `runs/research_v6_e5/`.
- **No `evaluation.json` failure.** The Windows `evaluation.json` `PermissionError` recorded in E4 did not stop any E5 field.
- **Analysis order.** The analysis ran only after both treatment-gate records had passed, as the runner enforces.

## H. Limitations

1. **Evidence weight.**
   - 13 of the 17 SB units, including all four exceptions, are deterministic characterizations. E5-H1 and E5-H2 are census counts, as registered, not rates.
   - The ANCHOR-ONLY census is better sampled: 9 of 15 units are rate-eligible.
2. **Whole-unit margins.** E5-H2 needed 12 of 17 and observed 13, one unit of margin. E5-H1 would have needed at most 1 of 17 to be refuted and observed 4.
3. **BP scope.** BP reads end-of-tick ownership of core cell 0 only. It does not read whole-core ownership or match outcome. "Base privilege" means that directed parity reading, nothing broader.
4. **H4 and H5 are F1-only.** The F2 guarded-painter mirror's seat exchanges (§F.7) lie outside them.
5. **D-3 and D-4 are corpus characterizations.** They hold for these seven fixtures, which never move onto their own core. They are not Ruleset invariants.
6. **Carried from the freeze record.** P5 inertness was confirmed at non-matrix seeds only. Clean-export reproducibility (done for E4) was not repeated for E5.
7. **Descriptive contact figures.** The coverage and core-0 figures in §F are descriptive readings of frozen cell metrics, not registered measures.
8. **Scope.** The results hold for 2 entrants, Q = 8, chunk 2, arena 512, rotation, 1,000 ticks and the seven scripted fixtures as written. Those fixtures never choose between disrupting and attacking the core, and never re-contest a cell within a tick. No external-validity claim is made.

## I. Disposition

**Registered.** The interpretation is `R-H2-PRIME`, with the four exceptions named in §E, and **the anchor/core forensic line closes**.

**The research lead's disposition (2026-09-25).** It is descriptive, not a registered rule, and it rests on the results above. The research lead's summary, verbatim:

> **Anchor/core co-location creates free contact with the core. It does not create the directed second-mover base privilege in most contests where the attacker already has an explicit core attack.**

The lead's decisions:

- **Not recommended for promotion.** **The E5 treatment is not recommended for promotion into the V6 gameplay Ruleset on these results.** This is an engineering and research decision, based principally on PF-2 and PF-3. It is not a new pre-registered hypothesis. Separation succeeds as a causal probe, but the lead does not see it as a gameplay solution: in the lead's words, "We removed a lot of decisive interaction and mostly converted it into longer versions of the same competitive ordering."
- **The four exceptions stay exceptions.** They are real and seed-invariant, and they cluster on two victims, the repair guard and the spread defender. They do not overturn the registered interpretation, and no E5.1 is registered to chase them: a further fixture-specific forensic experiment would study those agents more than it studies Bytefray.
- **H3 REFUTED is not bad news.** It is continuity only, and it shows that part of E4's residual population existed because anchor disruption was also supplying free core pressure (§F.6). It does not explain the surviving SB privilege.
- **The K = 1 companion did its job.** It does not reverse the primary reading (§F.8).
- **The forensic line closes.** No further anchor, scheduler or capture forensic experiment is run from these data. With E5, the E2–E5 forensic line is closed: capture hold, then disruption duration, then pass order, then spatial co-location.

Both E5 Rulesets remain research-only and resolvable, as the registration's permanent obligation requires. Nothing is promoted.

## J. Next research direction

This is future work, not part of the E5 verdict, and nothing is registered or implemented here.

1. **Synthesis.** A cross-experiment synthesis of E2–E5.
2. **A new mechanic.** Then a pivot to a mechanic that creates an actual choice between uses of an action (attack, defense, investment) or economic counterplay. The aim is to make opportunity cost strategic and selectable, rather than imposed by geometry.

E5 supplies one concrete input. Separating disruption from damage made a full disrupt-plus-core sweep cost one more action, and the scripted fixtures, which do not choose, simply lost one cell of core coverage per tick (§F.2).

The design review anticipated this branch on an H2 reading (§P). It named two options: a policy-space study of adaptive or searched agents under the current rules, or a new economic/opportunity-cost mechanic. The research lead's stated direction is the second, preceded by the synthesis. Each needs its own scope decision, design review and pre-registration. The closest catalogued ideas are the "Replication / deployment" and "Agent lifecycle: mutation, evolution, and replication economics" entries in [`FUTURE_PLANS.md`](../../FUTURE_PLANS.md).

## What this report does not claim

- **No product change.** No product or balance change is made. `before_core` is not promoted, and the recommendation against promotion is the research lead's disposition, not a registered rule.
- **No refutation of E5-H1.** Its frozen status is NEITHER.
- **No proof.** R-H2-PRIME *supports* the second response in the opening exchange as the remaining mechanism, and nothing here proves it. Four SB contests are registered exceptions.
- **No explanation of the exceptions.** No mechanism for the four exceptions is claimed.
- **No rate claims** from a value resting on fewer than 8 distinct trajectories.
- **No companion override.** Nothing from the companion arm replaces a primary verdict.
- **No change after the treatment ran.** No hypothesis, threshold, population, metric, operationalization, contest class, fixture or analysis tool changed.
- **No reinterpretation of earlier experiments.** No E2, E3 or E4 freeze, pre-registration, corpus or result is reinterpreted.

## Appendix R. Reproduction

- **Treatment execution:** `python -m tools.research.v6.e5.run_e5 execute {T-E5,T-E5K1} {F1,F2} --confirm-matrix-execution --confirm-treatment-execution --workers 1`, at `e6c789e` or any later commit that preserves the freeze.
- **Treatment telemetry and gates:** `… run_e5 treatment-telemetry T-E5` (and T-E5K1), then `… run_e5 treatment-gates T-E5` (and T-E5K1). The telemetry worker count only parallelizes read-only replay analysis.
- **Analysis (frozen, unmodified):** `python -m tools.research.v6.e5.run_e5 analyze`. It requires both passing treatment-gate records. Its output hash is in §A.
- **Descriptive tallies (§F).** Counts over the same frozen outputs:
  - the unit rows in `e5_analysis.json`;
  - `analyze_e5.unit_rows` over the companion arm's control and treatment runs;
  - `analyze_e5.outcome_class`, `is_capture`, `is_tick_limit`, `_no_core_contact` and `d9_completions`, and `analyze_e4.unit_rows` and `units`, applied to `run_e5.condition_runs` for each condition;
  - the `directed` block of each cell's frozen E5 telemetry.

  No threshold or new metric was introduced.
