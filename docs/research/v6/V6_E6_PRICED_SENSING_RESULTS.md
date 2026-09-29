# Bytefray V6 E6 — Priced Sensing: Results

**Status:** The full frozen E6 matrix (11,520 matches) has been executed, gated and analyzed. The seed list has been revealed, D-6 has passed, and the frozen interpreter has issued the registered interpretation and disposition.

- **Instrument.** Every measurement, the interpretation and the disposition come from the frozen instrument of analysis freeze `v6-e6-freeze-v2-275057e27725`.
- **Reading.** The hypotheses are read literally under the frozen pre-registration.

This is a research result, not a product decision.

**Branch:** `v6-research`. Controls were generated at `0d8b638`. The treatments were generated, gated and analyzed at `6949557`. The pre-reveal boundary `69724fd` was pushed before the reveal. The seed list was revealed at `0951fa3`, and D-6 and the registered interpretation are recorded at `5100ec0`.
**Date:** 2026-09-29
**Authority:**
- [`V6_E6_PRICED_SENSING_PREREGISTRATION.md`](V6_E6_PRICED_SENSING_PREREGISTRATION.md) (**PR**), transcribed in `tools/research/v6/e6/preregistration.json`, SHA-256 `e1ccc1cc7ef2f3b193019590984b9f34fafb0b7e176b1f4ebb8387d0566ee5f4`.
- [`V6_E6_PRICED_SENSING_IMPLEMENTATION_PLAN.md`](V6_E6_PRICED_SENSING_IMPLEMENTATION_PLAN.md) (**plan**), [`V6_PRICED_SENSING_DESIGN_REVIEW.md`](V6_PRICED_SENSING_DESIGN_REVIEW.md) (**DR**), [`V6_E6_AMENDMENT_1_FAMILY_CORRECTIONS.md`](V6_E6_AMENDMENT_1_FAMILY_CORRECTIONS.md) and the [implementation record](V6_E6_IMPLEMENTATION_RECORD.md).
- The research lead's authorizations and disposition of these results (Checkpoint B; the pre-reveal checkpoint and the finalization authorization of 2026-09-29), recorded in §H.

This record has three layers, and they are kept apart:

1. **Registered findings (§D).** E6-D, E6-H0–H3, the pathology flags, the kill criteria, the payoff tables, the companion reading, and the interpretation and disposition exactly as the frozen interpreter issued them.
2. **Descriptive and mechanism findings (§E, §F).** What the data show beyond the registered rules. They are labelled as description and are never inputs to a row or a kill.
3. **Engineering and research disposition, limitations and protocol notes (§G–§J).** The research lead's reading, the protocol incident at the pre-reveal checkpoint, and what the results do not establish.

## Answer in brief

- **Registered findings (primary arm, C-E6 → T-E6):**
  - **E6-D PASS.** Every clause D-1 to D-7 passes, D-6 included (§B).
  - **E6-H1T SUPPORTED.** No fixed member is a best response to every opponent under priced sensing, in the point estimate and in 1000 of 1000 bootstrap resamples.
  - **E6-H1C REFUTED.** Under the parent, SPLIT is universal (stability 1).
  - **E6-H2 SUPPORTED.** Spending less on information beats spending more against at least one opponent, with stability 1.
  - **E6-H0 NEITHER.** A = 769/1152 ≈ 0.668, B = 670/769 ≈ 0.871.
  - **E6-H3 REFUTED.** No attacker has a delayed forced line against both defenders; the largest minimum is SPLIT's 1/16.
  - **Pathology:** **PF-4 raised** (one new seat artifact, the PACED–ADAPT pairing); PF-1, PF-2 and PF-3 not raised.
  - **Kill criteria:** **KC-5 fires**; KC-1 to KC-4 do not.
- **Registered interpretation (frozen interpreter): `R-CREATES`**, qualified by E6-H2 SUPPORTED: *"Under the parent, one fixed policy is a best response to every opponent. Under priced sensing, none is: priced sensing creates an opponent-dependent choice of how to allocate actions"*, *"and spending less on information beats spending more against at least one opponent: an information/action tradeoff, not a discovery tax"*.
- **Registered disposition (frozen interpreter): `REJECT as a gameplay candidate`**, because KC-5 fires.
- **Companion (λ = 1, never a verdict):** "differs". It reproduces E6-H1T, E6-H1C, E6-H2 and E6-H3, but KC-5 does not fire there.
- **The research lead's reading (§H; descriptive, not a registered rule).** Priced sensing succeeds at the strategic objective E6 was designed to test, but this mechanic/parent combination introduces an unacceptable seat artifact. E6 answers "yes" to its research question and "no" to promotion: **strategically successful, product-unsuitable in its current form.** The companion points the next design problem at the interaction between priced sensing and whole-tick disruption.
- **Protocol incident (§I.1).** One of the 32 seed values was inadvertently disclosed to the analyst after all matrix execution and after the original frozen analysis, but before the formal reveal. It is recorded as a limitation, not an E6-D failure.

---

## A. Execution provenance

| Item | Value |
|---|---|
| Structural matrix | `v6-e6-matrix-v2-7de29a4a6954` (digest `7de29a4a…6fbfc2`), unchanged since the freeze |
| Execution matrix | `v6-e6-exec-v1-62b88ba3ddb4`, from seed commitment `61e292f6…5e1c83`. Both committed at I-7 (`0d8b638`), before the first cell. The seeds were generated once, on 2026-09-26 at 03:01:25 UTC, with the tooling at `f4e4411`. |
| Instrument | Analysis freeze `v6-e6-freeze-v2-275057e27725` (digest `275057e2…3ca2`): E6 analyzer, gates, re-derivation, telemetry and trace index, all version 1, and the reused E2–E5 analyzers pinned through E5's freeze. Tooling qualified at `539e26b`, record committed at `24440b8`, control qualification added at `6949557`. |
| Family | 9 members, 18 packages, one policy source (`agent.py` SHA-256 `5374092e…3b63`); fingerprints equal `family_fingerprints.json`; D-5 passes |
| Engine | `engine/src` tree `691f6666…`, equal to the frozen match-generation tree |
| Controls | C-E6 and C-E6L at `0d8b638` with a clean tree, launched 2026-09-26 04:08:12 UTC; last evaluation 04:24:57, telemetry complete 04:55:36 |
| Treatments | T-E6 and T-E6L at `6949557` with a clean tree, launched 2026-09-26 12:20:41 UTC (below) |
| Treatment gates | `treatment_gates_T-E6.json` `1893923f…4b48` (13:10:26 UTC) and `treatment_gates_T-E6L.json` `0dd9cc4d…c409` (13:13:08 UTC) |
| Frozen analysis | `run_e6 analyze` at `6949557`, seeds hidden: `e6_analysis.json`, SHA-256 `eb5c49ef34deb5e18ef51a445f72440e71af11f60d16a8b79520b6a1b017bb51` (13:34:12 UTC) |
| Pre-reveal boundary | `69724fd` fixes the SHA-256 of every artifact the interpretation reads (`tools/research/v6/e6/pre_reveal_manifest.json`). It was independently re-verified at the pre-reveal checkpoint (§G) and pushed to `origin/v6-research` before the reveal. |
| Reveal and D-6 | `tools/research/v6/e6/seeds_revealed.txt`, a byte copy of the private list, SHA-256 equal to the commitment, committed at `0951fa3`. `run_e6 reveal` on 2026-09-29: `d6.json` `e771802e…9ac1` (21:03:46 UTC). |
| Interpretation | `run_e6 interpret`: `e6_interpretation.json` `0b1c21bd…a32f` (21:04:44 UTC). D-6 and the interpretation are kept verbatim, with their hashes, in `tools/research/v6/e6/final_record.json` (`5100ec0`). |
| Environment | Python 3.13.14, `Windows-11-10.0.26120-SP0` |
| Retries | None. No quarantine or relaunch in any field. |
| Artifacts | `runs/research_v6_e6/v6-e6-matrix-v2-7de29a4a6954/{C-E6,T-E6,C-E6L,T-E6L}/{F1,F2}` and `records/`. Every replay, `result.json`, raw trace and callback-telemetry file is preserved (git-ignored); retention is "all". |

Record hashes are SHA-256 of the records' LF bytes, the convention by which the tooling pins its records.

**How the treatments ran** (all four fields launched together at 12:20:41 UTC as parallel processes through `run_e6 execute` with both confirmations):

| Condition | Field | Cells | Finished, including the bound trace pass and telemetry (UTC) | Harness evaluation time |
|---|---|---|---|---|
| T-E6 | F1 | 2,304 | 12:48:56 | 483 s |
| T-E6 | F2 | 576 | 12:29:06 | 114 s |
| T-E6L | F1 | 2,304 | 13:05:26 | 873 s |
| T-E6L | F2 | 576 | 12:29:59 | 124 s |

- **Provenance.** Every field's provenance names `6949557`, `git_dirty: false`, both matrix identities, the seed commitment, the freeze id, the pre-registration SHA-256 and the treatment Ruleset. The reflog shows HEAD at `6949557` without interruption from 05:11 UTC until the pre-reveal commit at 13:37 UTC.
- **Worker count.** The execution record states one worker per field. Field provenance does not record the worker count.

## B. Gates

**Before treatment** (Checkpoint B; `qualification.json` `89f448e0…cacd1`, pinned in the freeze record):

- **D-3:** PASS. The parent byte-identity freeze re-runs, and control provenance is clean.
- **CQ-1:** PASS. 2,688 matched comparisons per control, 0 failures.
- **D-2 and D-7 on the controls:** PASS (0 failures each).
- **Control-against-control, both arms:** PASS. E6-H0 SUPPORTED with A = B = 1, E6-H2 REFUTED, no PF raised, E6-H1T = E6-H1C.
- **Trace size:** 0.443 GB projected for the whole matrix, under 40 GB, so every raw trace is kept.

**E6-D** (a hard stop; it reads no gameplay outcome). Final status from `run_e6 interpret`:

| Clause | Kind | T-E6 | T-E6L | Status |
|---|---|---|---|---|
| D-1 Visibility | Ruleset invariant | 2,880 cells; 11,706,676 callbacks re-derived | 2,880 cells; 20,286,565 callbacks | **PASS**, 0 failures |
| D-2 Initial invisibility | Ruleset invariant | 2,880 cells; closest opposing spawns 66 apart (> 32) | 2,880 cells; 66 | **PASS**, 0 failures |
| D-3 Parent identity | Ruleset invariant | from the control qualification | | **PASS** |
| D-4 No early blind strike | Family characterization | 2,237 tick-1–2 writes to the opponent's core, all informed | 2,602, all informed | **PASS**, 0 failures |
| D-5 Discipline | Family characterization, static | re-checked at interpretation | | **PASS** |
| D-6 Seed commitment | Protocol | canonical; commitment; execution identity; every one of 11,520 cell seeds on the list | | **PASS**, 0 off-list |
| D-7 Mirror relabeling | Ruleset invariant | 288 mirror units | 288 mirror units | **PASS**, 0 failures |
| **E6-D** | | | | **PASS** |

An independent D-6 cross-check, outside `seeds.d6`, agrees:
- the revealed list is canonical;
- its SHA-256 equals the commitment, and any reordering would not;
- the execution identity recomputes;
- all 11,520 cells carry a listed seed;
- every one of the 32 seed positions carries exactly 360 cells (72 F1 and 18 F2 in each of the four conditions).

## C. Corpus

| Condition | Ruleset | F1 | F2 | Total |
|---|---|---|---|---|
| C-E6 | `bytefray-rules-6-research-scale` | 2,304 | 576 | 2,880 |
| T-E6 | `bytefray-rules-6-research-sensing-r32` | 2,304 | 576 | 2,880 |
| C-E6L | `bytefray-rules-6-research-disruption-slot1` | 2,304 | 576 | 2,880 |
| T-E6L | `bytefray-rules-6-research-disruption-slot1-sensing-r32` | 2,304 | 576 | 2,880 |
| **Total** | | | | **11,520** |

- **F1** is every ordered pair of distinct members (72) at each of the 32 seeds; **F2** is every twin mirror (9), both orientations, at each seed.
- **Evidence (O-EVIDENCE).** n_distinct counts distinct harness `trajectory_key` values among a unit's matches. A value resting on fewer than 8 is a characterization, not a rate.
- **n_distinct under the treatments** runs from 4 to 64 per pairing. Three T-E6 pairings are below 8: RUSH–GUARD (7), GUARD–EVADER (4) and ADAPT–GUARD (7). Two T-E6L pairings are: RUSH–GREED (5) and GUARD–EVADER (5).
- **Under the controls,** most C-E6 entries have n_distinct 2 to 4. The exceptions are SPLIT–EVADER (62) and GREED against GUARD, EVADER and ADAPT (15, 30, 28). C-E6L is similar (2 to 7), except SPLIT against GUARD, EVADER and ADAPT (39, 57, 41) and GREED against the same three (14 each). The control tables are therefore largely deterministic characterizations (§I.2).

---

## D. Layer 1 — Registered findings

### D.1 Primary arm (C-E6 → T-E6)

| ID | Statement | Status | Frozen criterion value |
|---|---|---|---|
| E6-D | Manipulation and integrity gate | **PASS** | §B |
| E6-H1T | The best response under T-E6 is not constant | **SUPPORTED** | P_none holds at the point estimate; stab(P_none) = **1000/1000** |
| E6-H1C | The best response under C-E6 is not constant | **REFUTED** | P_none fails (SPLIT is universal); stab(not P_none) = **1000/1000** |
| E6-H2 | Less information can win under T-E6 | **SUPPORTED** | P_win holds; stab(P_win) = **1000/1000**. Witnesses in §D.4. |
| E6-H0 | Delay only: priced sensing is a discovery tax | **NEITHER** | A = **769/1152 ≈ 0.668** (1,538 of 2,304 paired F1 cells keep their outcome class); B = **670/769 ≈ 0.871** (1,340 of those 1,538 end no earlier). Support needs A ≥ 9/10 and B ≥ 9/10; refutation needs A ≤ 2/3. |
| E6-H3 | A delayed forced line defeats every defender | **REFUTED** | Every attacker's minimum over the two defenders of FL(a, d) is ≤ 1/10 (table below) |

**FL(a, d) under T-E6** (share of the 64 F1 matches of *a* against *d* that are forced-line captures of *d* at tick ≤ 3; n_distinct in brackets):

| Attacker | FL(a, GUARD) | FL(a, EVADER) | Minimum |
|---|---|---|---|
| RUSH | 0 [7] | 0 [10] | 0 |
| PACED | 0 [19] | 0 [26] | 0 |
| SPLIT | 1/8 [12] | 1/16 [26] | **1/16** |
| STEALTH | 1/8 [22] | 1/64 [20] | 1/64 |
| LURK | 0 [13] | 0 [17] | 0 |

### D.2 Pathology flags (primary F1, recorded whatever else holds)

| Flag | Frozen value | Raised? |
|---|---|---|
| PF-1 Stalling | Tick-limit share 259/1152 (≈ 0.225) under C-E6 → 641/2304 (≈ 0.278) under T-E6: a rise of 123/2304 ≈ 0.053, below 1/10 | No |
| PF-2 Loss of contact | Share with no hostile core contact: 0 → 83/2304 ≈ 0.036 | No |
| PF-3 New immunity | No member of Π_F is never captured under T-E6 while captured under C-E6 | No |
| PF-4 Seat artifact | **`F1|PACED|ADAPT`**: under C-E6, SDom 0 and GSB 0 (seat-neutral; n_distinct 2). Under T-E6, SDom 0 and **GSB 1/8** (Seat A wins 8 more of the 64 matches than Seat B; n_distinct 25, rate-eligible), so \|GSB\| > 1/10. No other unit newly leaves seat neutrality. | **Yes** |

### D.3 Kill criteria (PR §8; evaluated on the primary arm)

| ID | Fires if and only if | Fires? |
|---|---|---|
| KC-1 Constant best response | E6-H1T is REFUTED | No |
| KC-2 Greed dominance | GREED universal at the point estimate with stab ≥ 9/10 | No (GREED is not universal; stab 0) |
| KC-3 Stalling or loss of contact | PF-1 or PF-2 is raised | No |
| KC-4 Delayed forced line | E6-H3 is SUPPORTED | No |
| KC-5 Seat artifact | PF-4 is raised | **Yes** |

### D.4 The payoff tables (PR §6.4)

The full tables for both arms are in Appendix T: u(i, j) with n_distinct, every BR_ε set with its stabilities, the universal members, and every Δ_j with both stabilities. The registered structure of the primary arm:

**Best responses under T-E6** (ε = 1/16; stability in brackets):

| Opponent j | BR_ε(j) |
|---|---|
| RUSH | PACED (999/1000) |
| PACED | PACED (97/100), EVADER (16/25) |
| SPLIT | RUSH (999/1000), PACED (599/1000) |
| STEALTH | RUSH (1), PACED (997/1000) |
| LURK | SPLIT (1), STEALTH (1), PACED (413/500) |
| GUARD | RUSH, PACED, SPLIT, LURK, GREED (1 each) |
| EVADER | SPLIT (1), GREED (1), LURK (987/1000) |
| GREED | RUSH, PACED, SPLIT, STEALTH (1 each) |
| ADAPT | SPLIT (1) |

- **Universal members under T-E6: none.** Every fixed member's stab(universal) is 0 of 1000.
- **Under C-E6: SPLIT is universal**, with stab 1. Every search variant (RUSH, PACED, STEALTH, LURK) ties SPLIT at 1/2 in every attacker contest, and SPLIT alone scores 1 against EVADER (the other attackers 97/128).

**The registered lower-information contrasts under T-E6** (Δ_j(lo, hi) = u(lo, j) − u(hi, j); P_win needs some Δ ≥ 1/16):

| Contrast | Opponents where Δ ≥ ε | Values | stab(Δ ≥ ε) |
|---|---|---|---|
| LURK − RUSH | EVADER | **57/128 ≈ 0.445**: u(LURK, EVADER) = 31/32 [n 17] against u(RUSH, EVADER) = 67/128 [n 10] | 1 |
| PACED − RUSH | RUSH and PACED (the head-to-head) | **5/32 ≈ 0.156**: u(PACED, RUSH) = 21/32 [n 43], so Δ_RUSH = 21/32 − 1/2 and Δ_PACED = 1/2 − 11/32 | 951/1000 each |

- **LURK − RUSH elsewhere:** 0 against GUARD, and negative against the other seven opponents, with stab(Δ ≤ 0) = 1 in each.
- **PACED − RUSH elsewhere:** every other Δ is below ε. The largest is +7/128 against ADAPT (stab(Δ ≥ ε) 457/1000).
- **Under C-E6:** every Δ is exactly 0, with stab(Δ ≤ 0) = 1 (P_never), as CQ-1 predicts.

**ADAPT (PR §6.7; secondary, never a row or kill input).** Under T-E6, u(ADAPT, j) − u(j, ADAPT) is:
- positive against GUARD (+1), EVADER (+61/64), GREED (+55/64) and LURK (+25/32);
- negative against SPLIT (−1), STEALTH (−27/32), PACED (−13/16) and RUSH (−45/64).

ADAPT, added to the candidate set, enters BR_ε only for GUARD and EVADER. Under C-E6 it is in no BR_ε set, and every difference is 0 or −1.

### D.5 Companion arm (C-E6L → T-E6L; PR §6.8, never a verdict)

| Quantity | Companion | Primary |
|---|---|---|
| E6-H1T | SUPPORTED (stab 1) | SUPPORTED |
| E6-H1C | REFUTED (SPLIT universal under C-E6L, stab 1) | REFUTED |
| E6-H2 | SUPPORTED (stab 1) | SUPPORTED |
| E6-H0 | REFUTED: A = 725/1152 ≈ 0.629, B = 1431/1450 | NEITHER |
| E6-H3 | REFUTED (largest minimum: STEALTH 1/64; SPLIT 0) | REFUTED |
| PF-1 | Not raised: 7/12 ≈ 0.583 → 271/576 ≈ 0.470 (falls) | Not raised (rises 0.053) |
| PF-2 | Not raised: 0 → 17/576 ≈ 0.030 | Not raised |
| PF-3, PF-4 | Not raised | PF-3 no; **PF-4 raised** |
| KC-1 to KC-5 | None fires | **KC-5 fires** |

- **Registered companion reading:** **"differs"**. The frozen comparison set is E6-H1T, E6-H2, E6-H3 and every kill criterion, and the one difference in it is *"KC-5: fires (primary) vs does not fire (companion)"*.
- **Also different, outside the registered comparison set:** E6-H0 (NEITHER against REFUTED) and the direction of the tick-limit change.
- **Companion H2 witnesses:**
  - LURK − RUSH: +31/64 against GUARD and +59/128 against EVADER (stab 1 each).
  - PACED − RUSH: +19/128 in the head-to-head (stab 233/250).
- **Companion best responses:** no universal member. SPLIT is in 6 of the 9 BR_ε sets, and RUSH alone is the best response to SPLIT and to STEALTH (Appendix T).

### D.6 Registered interpretation and disposition (PR §7, §8; issued by `run_e6 interpret`)

The frozen rule: a row applies if and only if E6-D has the row's status and (E6-H1T, E6-H1C) is among its listed combinations. The inputs are **(E6-D PASS, E6-H1T SUPPORTED, E6-H1C REFUTED)**, with E6-H2 SUPPORTED, E6-H0 NEITHER and fired = [KC-5].

`e6_interpretation.json` (SHA-256 `0b1c21bd35748e053375aa23163fe92e00b5bcbee1eafa355ccc62a64b16a32f`), verbatim:

- **Row:** `R-CREATES`
- **Reading:** "Under the parent, one fixed policy is a best response to every opponent. Under priced sensing, none is: priced sensing creates an opponent-dependent choice of how to allocate actions."
- **Qualifier (E6-H2 SUPPORTED):** "and spending less on information beats spending more against at least one opponent: an information/action tradeoff, not a discovery tax"
- **Disposition:** `REJECT as a gameplay candidate`
- **Recorded alongside:** E6-H3 REFUTED; PF-1 false, PF-2 false, PF-3 false, **PF-4 true**; companion "differs" (KC-5).

The disposition is the first matching clause of PR §8: E6-D passed, so not VOID; a kill criterion fired, so REJECT. **R-CREATES and REJECT are not in tension.** The row says what priced sensing did to the choice structure. The kill says this combination is not a gameplay candidate. PR §8: "A REJECT or a NOT ESTABLISHED is a successful result of the method."

---

## E. Layer 2 — Descriptive findings: the payoff topology

*Description, not registered rules.*

### E.1 What replaced SPLIT's universality

Under both controls, SPLIT is universal. Every attacker ties every other attacker at 1/2 (visibility is complete from the first callback), and SPLIT's two-process line also beats EVADER outright. Priced sensing removes that universality completely: SPLIT is universal in 0 of 1000 resamples under T-E6. Nothing replaces it as a single answer:

- **Against searching attackers, a searcher is best.**
  - PACED alone is the best response to RUSH: it wins the head-to-head 21/32.
  - RUSH, then PACED, is best against SPLIT and STEALTH.
  - SPLIT loses its head-to-heads to RUSH (45/128) and PACED (53/128), and falls outside BR(STEALTH), scoring 53/64 against RUSH's 29/32.
- **Against passive, defensive and adaptive opponents, SPLIT stays best.** It scores 1 against LURK, GUARD, EVADER, GREED and ADAPT.
- **Membership counts (T-E6).** PACED is in 7 of the 9 BR_ε sets (all except EVADER and ADAPT), SPLIT in 5, RUSH in 4.

The companion shows the same split, with SPLIT in more sets (6 of 9).

### E.2 Less information wins, in both registered contrasts

- **LURK over RUSH, against EVADER.** The non-searching attacker scores 31/32 against EVADER, where the fast searcher scores 67/128. Most of EVADER's matches end at the tick limit (§F.3).
- **PACED over RUSH, head-to-head.** The registered lower-information searcher wins the searcher duel 21/32. PACED detected first in 93.8% of its F1 cells, RUSH in 44.1% (§F.1).

Neither witness is a margin effect. Both hold in at least 951 of 1000 resamples.

### E.3 The outcome structure changes; it is not only delayed

- 766 of 2,304 paired F1 cells change outcome class (A = 1,538/2,304). Of the 1,538 that keep their class, 198 end earlier under T-E6.
- **E6-H0's A lands 2 cells above its refutation bound** (1,536 of 2,304). That is stated as a fact; the registered status is NEITHER, and the threshold is unchanged.
- Capture still decides most F1 matches: 0.775 under C-E6, 0.722 under T-E6.

---

## F. Layer 2 — Descriptive findings: mechanisms

*Aggregations of the frozen O-DETECT telemetry and the E4 cell metrics, made at the pre-reveal checkpoint from the frozen summaries. Not frozen-analysis outputs, and never hypothesis inputs. "Detection" means the opponent's anchor in the pooled visible set. "Probe READ" is the O-DETECT definition, an applied READ outside the reader's own core, and includes READs made after detection.*

### F.1 Search versus READ, and first-detection timing (T-E6 F1; 512 entrant-appearances per member)

| Member | Detected | First-detection tick (median / mean) | Saw first | Pre-detection MOVEs (mean) | Probe READs (mean) | Off-core MOVEs (mean) |
|---|---|---|---|---|---|---|
| RUSH | 512 (100%) | 1 / 1.75 | 44.1% | 4.4 | 274.7 | 1.03 |
| PACED | 512 (100%) | 1.5 / 1.54 | 93.8% | 3.95 | 264.1 | 0.98 |
| SPLIT | 512 (100%) | 2 / 2.26 | 81.4% | 4.13 | 81.0 | 0.98 |
| STEALTH | 199 (38.9%) | 3 / 2.82 | 7.6% | 0 | 46.2 | 0 |
| LURK | 258 (50.4%) | 3 / 6.36 | 13.7% | 0 | 54.1 | 0 |
| GUARD | 261 (51.0%) | 3 / 6.52 | 13.3% | 0 | 0 | 0 |
| EVADER | 276 (53.9%) | 3 / 5.8 | 18.8% | 0.98 | 0 | 1.0 |
| GREED | 258 (50.4%) | 3 / 6.36 | 13.7% | 0 | 0 | 0 |
| ADAPT | 446 (87.1%) | 17 / 11.05 | 30.1% | 2.12 | 17.8 | 0.72 |

- **Under C-E6,** every entrant that gets a callback detects in its first ticks (median tick 1), the attackers make about 3 probe READs per match, and seat A detects first in all 2,304 cells.
- **Under T-E6, neither entrant ever detects the other in 684 of 2,304 F1 cells** (29.7%). The count is the same under T-E6L.
- **STEALTH** locates by READ, not by visibility, so its visibility detection stays low.
- **ADAPT**'s median first detection falls just after its registered no-contact switch at tick 16 (O-6).

### F.2 SPLIT's sensor and striker (T-E6 F1)

- **The sensor** (share 1/4) made all of SPLIT's 2,133 MOVEs and 11,693 WRITEs.
- **The striker** (share 3/4) made 41,899 READs and 19,939 WRITEs, and no MOVE.
- **First detection.** Visibility is pooled over an entrant's unsuppressed processes (D-1), so the first callback carrying a detection was the striker's in 419 of 512 cells, and the sensor's in 93. That reflects the striker's larger share of callbacks, not which process did the sensing.
- **Under C-E6,** both processes only WRITE (the striker also makes 1,383 READs), and the sensor carries the first detection in every cell where SPLIT gets a callback.
- **Outcomes.** SPLIT's own core was captured in 17.8% of its F1 cells (25.0% under C-E6), and it captured its opponent's core in 82.6% (72.9%).

### F.3 Evasion and stalling

- **EVADER.**
  - Its matches reach the tick limit in 83.4% of its F1 cells, up from 63.9% under C-E6.
  - Its own core is captured in 16.6%, down from 36.1%.
  - It is caught still on its core 6 of 512 times (all in seat B), against 256 of 512 under C-E6 (all in seat B).
- **The whole field.** The tick-limit share rises by 0.053 (PF-1 not raised). Cells with no hostile core contact rise from 0 to 3.6% (PF-2 not raised).
- **Under the companion,** stalling concentrates on the defenders instead:
  - GUARD's matches reach the tick limit in 89.6% of its cells and EVADER's in 98.8%.
  - RUSH and PACED score only about 1/2 against both defenders.
  - Yet the field's tick-limit share falls, from 0.583 to 0.470.

### F.4 Seat and parity

| | C-E6 | T-E6 | C-E6L | T-E6L |
|---|---|---|---|---|
| First detection by seat (A / B / neither) | 2,304 / 0 / 0 | 797 / 823 / 684 | 2,304 / 0 / 0 | 797 / 823 / 684 |
| EVADER caught on core (seat A / seat B) | 0 / 256 | 0 / 6 | 0 / 256 | 0 / 6 |
| Seat-neutral units, of 45 (36 F1 pairings, 9 F2 mirrors) | 26 | 38 | 30 | 39 |

- **Priced sensing mostly removes seat determination.**
  - Under T-E6, 13 units become seat-neutral: the STEALTH, LURK and SPLIT mirrors, EVADER's pairings with RUSH, PACED, STEALTH and LURK, and six attacker pairings (RUSH–STEALTH, RUSH–LURK, PACED–STEALTH, PACED–LURK, STEALTH–LURK, SPLIT–LURK).
  - Exactly one unit leaves neutrality: PACED–ADAPT, which is PF-4.
  - Under T-E6L, 9 units become neutral and none leaves.
- **Fast-searcher arrival parity** is mixed for RUSH. For SPLIT it leans even (401 even against 111 odd under T-E6; 474 against 37 under T-E6L).

### F.5 Alternation (E4 cell metrics, PR §6.2)

| Condition | FMA decided early / defined | FMA bands (defined cells) | FPS scored / not scoreable |
|---|---|---|---|
| C-E6 | 1,668 / 636 | neutral 352, strong-first 252, moderate-first 32 | 436 / 1,868 |
| T-E6 | 1,443 / 861 | neutral 610, strong-first 187, moderate-last 37, strong-last 20, moderate-first 7 | 526 / 1,778 |
| C-E6L | 960 / 1,344 | neutral 880, moderate-last 460, strong-last 4 | 1,072 / 1,232 |
| T-E6L | 1,066 / 1,238 | neutral 764, moderate-last 421, strong-last 53 | 891 / 1,413 |

Under T-E6 more matches last long enough for FMA to be defined, and first-mover concentration thins: the neutral band grows from 352 to 610 cells, and strong-first shrinks from 252 to 187.

---

## G. Layer 3 — Engineering notes: execution, checkpoint verification and finalization

**Chronology:**
1. The treatment, its gates and the frozen analysis ran on 2026-09-26, under the research lead's Checkpoint B authorization. The pre-reveal manifest was committed as `69724fd`.
2. At the pre-reveal checkpoint (2026-09-29), a new session found that execution already complete. It did not re-execute anything: the runner refuses to re-run a field in place, and a second run would duplicate registered cells.
3. Instead it treated the earlier session's records as untrusted and re-verified them without writing to `runs/` (below).

**What the checkpoint re-verified:**
- All 40 committed artifact hashes in the pre-reveal manifest.
- **The registered commands, re-run in memory with writes intercepted.** `treatment-gates` for both conditions and `analyze` reproduced `treatment_gates_T-E6.json`, `treatment_gates_T-E6L.json` and `e6_analysis.json` **byte for byte**.
- **A supplementary check of every treatment cell:**
  - completeness, coverage and seed membership;
  - evaluation-state binding;
  - replay SHA-256 against `result.json`;
  - raw-trace integrity against the trace index;
  - byte-identical re-extraction of the callback telemetry, which is D-1's input;
  - E3/E4 agreement on the 4,608 treatment F1 cells (0 disagreements).
- **An independent recomputation of u(i, j) from `result.json`,** outside `payoff.py`: it agrees on all 162 treatment entries.
- **The corpus.** A full-corpus snapshot of all 58,356 files was unchanged across the checkpoint and up to the reveal.

**A defect in a checkpoint script, not in the instrument.** The first version of the supplementary `result.json` comparison flagged 1,460 cells: exactly the tie cells of the four treatment fields (329, 238, 565 and 328). `result.json` writes a tie as `winner: "tie"`, while the harness cell writes `outcome: "tie"` with a null `winner_seat`. Corrected, the comparison agrees on 5,760 of 5,760 cells, with no cell lacking an outcome.

**Test counts:**
- The complete set of 12 E6 test files: **745 passed**, the count recorded at `24440b8`.
- The checkpoint report's earlier figure of 663 came from an incomplete set of 11 files that omitted `test_ruleset_v6_research_sensing.py`.

**Order of the reveal operations:**
1. The revealed list was written to `tools/research/v6/e6/seeds_revealed.txt` and staged before D-6. Its bytes equal the private file's, and its SHA-256 equals the commitment.
2. D-6 and the interpretation ran against that file.
3. The list's git commit followed D-6 and the interpretation. An automated permission guard in the agent's environment declined the agent's first attempt to commit the seed list. The research lead then explicitly authorized the commit, and it was made exactly as staged, at `0951fa3`. Its blob's SHA-256 equals the commitment.
4. The final record (`5100ec0`) and this record followed, in that order.

The bytes D-6 verified are the bytes committed. Nothing in the frozen instrument, the family, the matrix or the corpus changed at any step.

## H. Layer 3 — Research disposition (research lead, 2026-09-29; descriptive, not a registered rule)

- **The registered result.** E6 answers its research question: priced sensing makes the best allocation of actions depend on the opponent, and the registered lower-information contrast shows an information/action tradeoff rather than a discovery tax (`R-CREATES`, qualified by E6-H2 SUPPORTED).
- **Why it matters.** The change is not merely "different agents win now". Both registered lower-information contrasts produced witnesses, so E6 has evidence that **the action value of acquiring information depends on the opponent**. That is the central Branch B objective.
- **The registered disposition.** `REJECT as a gameplay candidate`, because KC-5 fires. In the research lead's words: *priced sensing succeeds at the strategic objective E6 was designed to test, but this particular mechanic/parent combination introduces an unacceptable seat artifact.* The two answers are compatible. E6 answers "yes" to the research question and "no" to promotion.
- **In short:** **the mechanic appears strategically successful but product-unsuitable in its current form.** That is more useful than either "priced sensing works" or "priced sensing failed". It gives Branch B's thesis evidence, and it names a specific next design problem instead of a return to broad mechanic ideation.
- **What the companion adds (a clue, not a causal proof).** The λ = 1 companion reproduces the strategic findings: E6-H1T supported, E6-H1C refuted, E6-H2 supported, E6-H3 refuted. It does not produce KC-5. So the new seat pathology observed in the primary is not reproduced when whole-tick disruption is replaced by one-offer disruption. That motivates follow-on design work on the **interaction between priced sensing and whole-tick disruption**, rather than a conclusion that local sensing itself creates the seat artifact. The primary remains authoritative, and the companion does not rescue the candidate.
- **Rulesets.** Both E6 Rulesets remain research-only.

## I. Limitations and protocol notes

1. **Pre-reveal seed disclosure (protocol incident).** One of 32 seed values was inadvertently disclosed to the analyst after all matrix execution and after the original frozen analysis had completed, but before formal reveal. No agent had access to it, no matrix cell was rerun, and independent re-analysis remained byte-identical. The remaining seed list and private artifact remained unchanged until reveal.
   - **What happened.** At the pre-reveal checkpoint, a key-name-based redaction printed one cell's `artifact_dir`. Harness artifact directories embed the match seed in their names, so the path exposed one seed value in the session transcript. From then on, every output passed through a value-based seed filter, which needed no further redaction.
   - **Why it does not affect E6-D.** D-6 is a commitment and integrity test: the revealed list must hash to the precommitted value, and every executed cell must use a member of it. It passed. The protocol's purpose, keeping the frozen agents from reconstructing placement during execution, was not affected: execution had finished, and agents cannot read the transcript. The incident is recorded here, not as an E6-D failure. This record does not claim that every seed stayed hidden until the reveal.
2. **The control tables are largely characterizations.** Most C-E6 and C-E6L entries rest on 2 to 7 distinct trajectories (§C), so SPLIT's control universality, and with it E6-H1C, is a deterministic characterization of this family under the parents rather than a rate.
3. **Evidence thresholds.** The treatment pairings below n_distinct 8 (T-E6: RUSH–GUARD, GUARD–EVADER, ADAPT–GUARD; T-E6L: RUSH–GREED, GUARD–EVADER) are characterizations. FL(RUSH, GUARD) rests on 7 distinct trajectories.
4. **KC-5 rests on one unit.** PF-4 is raised by the PACED–ADAPT pairing alone. Its control neutrality rests on 2 distinct trajectories, and its treatment \|GSB\| = 1/8 exceeds the 1/10 bound by 1/40. The registered rule does not weigh margins, and the kill is binding as registered. This note describes the size of the artifact; it does not qualify the disposition. **E6-H0's A** likewise sits 2 cells above its refutation bound, and its status stands as NEITHER.
5. **Scope.** Every claim is about this frozen nine-member family on a 512-cell arena, with detection radius 32, under the `research-scale` parent (primary) and the `disruption-slot1` parent (companion). Claims are limited to agents that do not reconstruct placement from the seed, a channel closed here only methodologically (DR §E.2). Closing it in the product remains a promotion prerequisite.
6. **Descriptive definitions.** Visibility is pooled across an entrant's processes, so per-process "first detection" measures callback share. "Probe READ" includes READs made after detection. §F's aggregations were computed at the checkpoint from the frozen summaries and are not frozen outputs.
7. **Provenance gaps.** Field provenance does not record the worker count.

## J. Next research direction (research lead; not registered)

Examine the interaction between priced sensing and whole-tick disruption: the primary's seat artifact is absent when whole-tick disruption is replaced by one-offer disruption. Any such work is a new, separately registered question. E6's matrix, freeze and records stay as they are.

## What this report does not claim

- No product decision: `REJECT as a gameplay candidate` is a research disposition, and both E6 Rulesets remain research-only.
- No causal claim that whole-tick disruption produces the seat artifact: the companion difference is a clue for the next design problem.
- No claim beyond the frozen family, arena, radius and parents (§I.5).
- No rate claim on a value resting on fewer than 8 distinct trajectories.
- No claim that all seeds stayed hidden until the reveal (§I.1).

---

## Appendix T. Payoff tables (PR §6.4), both arms

Generated directly from `e6_analysis.json` (`eb5c49ef…`). ε = 1/16; stabilities are over the 1000 O-BOOT resamples. u(i, i) = 1/2 by definition. n_distinct is given in brackets beside every off-diagonal entry.

### T-E6 (primary arm, treatment)

P_none = True (stab 1); P_win = True (stab 1); P_never = False (stab 0). Universal members: none; stab(i universal): 0 for every member.

u(i, j), row i against column j, exact value with n_distinct in brackets:

| i \ j | RUSH | PACED | SPLIT | STEALTH | LURK | GUARD | EVADER | GREED | ADAPT |
|---|---|---|---|---|---|---|---|---|---|
| **RUSH** | 1/2 | 11/32 [43] | 83/128 [40] | 29/32 [13] | 59/64 [23] | 1 [7] | 67/128 [10] | 1 [11] | 109/128 [32] |
| **PACED** | 21/32 [43] | 1/2 | 75/128 [43] | 57/64 [24] | 61/64 [24] | 1 [19] | 71/128 [26] | 1 [15] | 29/32 [29] |
| **SPLIT** | 45/128 [40] | 53/128 [43] | 1/2 | 53/64 [20] | 1 [23] | 1 [12] | 1 [26] | 1 [17] | 1 [22] |
| **STEALTH** | 3/32 [13] | 7/64 [24] | 11/64 [20] | 1/2 | 1 [35] | 119/128 [22] | 71/128 [20] | 1 [35] | 59/64 [39] |
| **LURK** | 5/64 [23] | 3/64 [24] | 0 [23] | 0 [35] | 1/2 | 1 [13] | 31/32 [17] | 1/2 [60] | 7/64 [38] |
| **GUARD** | 0 [7] | 0 [19] | 0 [12] | 9/128 [22] | 0 [13] | 1/2 | 1/2 [4] | 0 [13] | 0 [7] |
| **EVADER** | 61/128 [10] | 57/128 [26] | 0 [26] | 57/128 [20] | 1/32 [17] | 1/2 [4] | 1/2 | 0 [17] | 3/128 [22] |
| **GREED** | 0 [11] | 0 [15] | 0 [17] | 0 [35] | 1/2 [60] | 1 [13] | 1 [17] | 1/2 | 9/128 [33] |
| **ADAPT** | 19/128 [32] | 3/32 [29] | 0 [22] | 5/64 [39] | 57/64 [38] | 1 [7] | 125/128 [22] | 119/128 [33] | 1/2 |

BR_ε(j), with each fixed member's bootstrap stability of being in BR_ε(j) (members at 0 omitted):

| j | BR_ε(j) | stab (nonzero) |
|---|---|---|
| RUSH | PACED | RUSH 9/125, PACED 999/1000, EVADER 4/125 |
| PACED | EVADER, PACED | RUSH 67/1000, PACED 97/100, SPLIT 389/1000, EVADER 16/25 |
| SPLIT | PACED, RUSH | RUSH 999/1000, PACED 599/1000, SPLIT 27/250 |
| STEALTH | PACED, RUSH | RUSH 1, PACED 997/1000, SPLIT 103/250 |
| LURK | PACED, SPLIT, STEALTH | RUSH 411/1000, PACED 413/500, SPLIT 1, STEALTH 1 |
| GUARD | GREED, LURK, PACED, RUSH, SPLIT | RUSH 1, PACED 1, SPLIT 1, STEALTH 57/125, LURK 1, GREED 1 |
| EVADER | GREED, LURK, SPLIT | SPLIT 1, LURK 987/1000, GREED 1 |
| GREED | PACED, RUSH, SPLIT, STEALTH | RUSH 1, PACED 1, SPLIT 1, STEALTH 1 |
| ADAPT | SPLIT | RUSH 3/500, PACED 73/500, SPLIT 1, STEALTH 159/500 |

Δ_j(lo, hi) = u(lo, j) − u(hi, j), with stab(Δ ≥ ε) / stab(Δ ≤ 0):

| j | LURK − RUSH | PACED − RUSH |
|---|---|---|
| RUSH | -27/64 (-0.422); 0 / 1 | 5/32 (0.156); 951/1000 / 1/125 |
| PACED | -19/64 (-0.297); 0 / 1 | 5/32 (0.156); 951/1000 / 1/125 |
| SPLIT | -83/128 (-0.648); 0 / 1 | -1/16 (-0.062); 3/1000 / 477/500 |
| STEALTH | -29/32 (-0.906); 0 / 1 | -1/64 (-0.016); 0 / 1 |
| LURK | -27/64 (-0.422); 0 / 1 | 1/32 (0.031); 69/500 / 141/1000 |
| GUARD | 0 (0.000); 0 / 1 | 0 (0.000); 0 / 1 |
| EVADER | 57/128 (0.445); 1 / 0 | 1/32 (0.031); 21/200 / 83/1000 |
| GREED | -1/2 (-0.500); 0 / 1 | 0 (0.000); 0 / 1 |
| ADAPT | -95/128 (-0.742); 0 / 1 | 7/128 (0.055); 457/1000 / 1/10 |

### C-E6 (primary arm, control)

P_none = False (stab 0); P_win = False (stab 0); P_never = True (stab 1). Universal members: SPLIT; stab(i universal): SPLIT 1.

u(i, j), row i against column j, exact value with n_distinct in brackets:

| i \ j | RUSH | PACED | SPLIT | STEALTH | LURK | GUARD | EVADER | GREED | ADAPT |
|---|---|---|---|---|---|---|---|---|---|
| **RUSH** | 1/2 | 1/2 [2] | 1/2 [2] | 1/2 [2] | 1/2 [2] | 1 [2] | 97/128 [3] | 1 [2] | 1 [3] |
| **PACED** | 1/2 [2] | 1/2 | 1/2 [2] | 1/2 [2] | 1/2 [2] | 1 [2] | 97/128 [3] | 1 [2] | 1 [3] |
| **SPLIT** | 1/2 [2] | 1/2 [2] | 1/2 | 1/2 [2] | 1/2 [2] | 1 [2] | 1 [62] | 1 [2] | 1 [2] |
| **STEALTH** | 1/2 [2] | 1/2 [2] | 1/2 [2] | 1/2 | 1/2 [2] | 1 [2] | 97/128 [3] | 1 [2] | 1 [3] |
| **LURK** | 1/2 [2] | 1/2 [2] | 1/2 [2] | 1/2 [2] | 1/2 | 1 [2] | 97/128 [3] | 1 [2] | 1 [3] |
| **GUARD** | 0 [2] | 0 [2] | 0 [2] | 0 [2] | 0 [2] | 1/2 | 1/2 [3] | 0 [15] | 1/2 [3] |
| **EVADER** | 31/128 [3] | 31/128 [3] | 0 [62] | 31/128 [3] | 31/128 [3] | 1/2 [3] | 1/2 | 0 [30] | 1/2 [4] |
| **GREED** | 0 [2] | 0 [2] | 0 [2] | 0 [2] | 0 [2] | 1 [15] | 1 [30] | 1/2 | 1 [28] |
| **ADAPT** | 0 [3] | 0 [3] | 0 [2] | 0 [3] | 0 [3] | 1/2 [3] | 1/2 [4] | 0 [28] | 1/2 |

BR_ε(j), with each fixed member's bootstrap stability of being in BR_ε(j) (members at 0 omitted):

| j | BR_ε(j) | stab (nonzero) |
|---|---|---|
| RUSH | LURK, PACED, RUSH, SPLIT, STEALTH | RUSH 1, PACED 1, SPLIT 1, STEALTH 1, LURK 1 |
| PACED | LURK, PACED, RUSH, SPLIT, STEALTH | RUSH 1, PACED 1, SPLIT 1, STEALTH 1, LURK 1 |
| SPLIT | LURK, PACED, RUSH, SPLIT, STEALTH | RUSH 1, PACED 1, SPLIT 1, STEALTH 1, LURK 1 |
| STEALTH | LURK, PACED, RUSH, SPLIT, STEALTH | RUSH 1, PACED 1, SPLIT 1, STEALTH 1, LURK 1 |
| LURK | LURK, PACED, RUSH, SPLIT, STEALTH | RUSH 1, PACED 1, SPLIT 1, STEALTH 1, LURK 1 |
| GUARD | GREED, LURK, PACED, RUSH, SPLIT, STEALTH | RUSH 1, PACED 1, SPLIT 1, STEALTH 1, LURK 1, GREED 1 |
| EVADER | GREED, SPLIT | SPLIT 1, GREED 1 |
| GREED | LURK, PACED, RUSH, SPLIT, STEALTH | RUSH 1, PACED 1, SPLIT 1, STEALTH 1, LURK 1 |
| ADAPT | GREED, LURK, PACED, RUSH, SPLIT, STEALTH | RUSH 1, PACED 1, SPLIT 1, STEALTH 1, LURK 1, GREED 1 |

Δ_j(lo, hi) = u(lo, j) − u(hi, j), with stab(Δ ≥ ε) / stab(Δ ≤ 0):

| j | LURK − RUSH | PACED − RUSH |
|---|---|---|
| RUSH | 0 (0.000); 0 / 1 | 0 (0.000); 0 / 1 |
| PACED | 0 (0.000); 0 / 1 | 0 (0.000); 0 / 1 |
| SPLIT | 0 (0.000); 0 / 1 | 0 (0.000); 0 / 1 |
| STEALTH | 0 (0.000); 0 / 1 | 0 (0.000); 0 / 1 |
| LURK | 0 (0.000); 0 / 1 | 0 (0.000); 0 / 1 |
| GUARD | 0 (0.000); 0 / 1 | 0 (0.000); 0 / 1 |
| EVADER | 0 (0.000); 0 / 1 | 0 (0.000); 0 / 1 |
| GREED | 0 (0.000); 0 / 1 | 0 (0.000); 0 / 1 |
| ADAPT | 0 (0.000); 0 / 1 | 0 (0.000); 0 / 1 |

### T-E6L (companion arm, treatment)

P_none = True (stab 1); P_win = True (stab 1); P_never = False (stab 0). Universal members: none; stab(i universal): 0 for every member.

u(i, j), row i against column j, exact value with n_distinct in brackets:

| i \ j | RUSH | PACED | SPLIT | STEALTH | LURK | GUARD | EVADER | GREED | ADAPT |
|---|---|---|---|---|---|---|---|---|---|
| **RUSH** | 1/2 | 45/128 [45] | 41/64 [34] | 111/128 [16] | 57/64 [17] | 33/64 [17] | 1/2 [16] | 1 [5] | 89/128 [29] |
| **PACED** | 83/128 [45] | 1/2 | 71/128 [45] | 25/32 [24] | 57/64 [27] | 33/64 [22] | 1/2 [42] | 1 [15] | 71/128 [39] |
| **SPLIT** | 23/64 [34] | 57/128 [45] | 1/2 | 3/4 [22] | 15/16 [28] | 1 [48] | 1 [61] | 1 [8] | 1 [57] |
| **STEALTH** | 17/128 [16] | 7/32 [24] | 1/4 [22] | 1/2 | 1 [24] | 113/128 [25] | 35/64 [19] | 1 [24] | 7/8 [35] |
| **LURK** | 7/64 [17] | 7/64 [27] | 1/16 [28] | 0 [24] | 1/2 | 1 [13] | 123/128 [17] | 1/2 [64] | 9/64 [34] |
| **GUARD** | 31/64 [17] | 31/64 [22] | 0 [48] | 15/128 [25] | 0 [13] | 1/2 | 1/2 [5] | 0 [13] | 0 [16] |
| **EVADER** | 1/2 [16] | 1/2 [42] | 0 [61] | 29/64 [19] | 5/128 [17] | 1/2 [5] | 1/2 | 0 [15] | 1/64 [20] |
| **GREED** | 0 [5] | 0 [15] | 0 [8] | 0 [24] | 1/2 [64] | 1 [13] | 1 [15] | 1/2 | 9/64 [39] |
| **ADAPT** | 39/128 [29] | 57/128 [39] | 0 [57] | 1/8 [35] | 55/64 [34] | 1 [16] | 63/64 [20] | 55/64 [39] | 1/2 |

BR_ε(j), with each fixed member's bootstrap stability of being in BR_ε(j) (members at 0 omitted):

| j | BR_ε(j) | stab (nonzero) |
|---|---|---|
| RUSH | PACED | RUSH 89/1000, PACED 999/1000, SPLIT 1/200, GUARD 47/1000, EVADER 89/1000 |
| PACED | EVADER, GUARD, PACED, SPLIT | RUSH 7/100, PACED 471/500, SPLIT 67/125, GUARD 907/1000, EVADER 471/500 |
| SPLIT | RUSH | RUSH 1, PACED 153/500, SPLIT 137/1000 |
| STEALTH | RUSH | RUSH 1, PACED 253/1000, SPLIT 63/1000 |
| LURK | SPLIT, STEALTH | RUSH 143/1000, PACED 143/1000, SPLIT 641/1000, STEALTH 1 |
| GUARD | GREED, LURK, SPLIT | SPLIT 1, STEALTH 49/1000, LURK 1, GREED 1 |
| EVADER | GREED, LURK, SPLIT | SPLIT 1, LURK 24/25, GREED 1 |
| GREED | PACED, RUSH, SPLIT, STEALTH | RUSH 1, PACED 1, SPLIT 1, STEALTH 1 |
| ADAPT | SPLIT | SPLIT 1, STEALTH 7/1000 |

Δ_j(lo, hi) = u(lo, j) − u(hi, j), with stab(Δ ≥ ε) / stab(Δ ≤ 0):

| j | LURK − RUSH | PACED − RUSH |
|---|---|---|
| RUSH | -25/64 (-0.391); 0 / 1 | 19/128 (0.148); 233/250 / 13/1000 |
| PACED | -31/128 (-0.242); 0 / 1 | 19/128 (0.148); 233/250 / 13/1000 |
| SPLIT | -37/64 (-0.578); 0 / 1 | -11/128 (-0.086); 0 / 1 |
| STEALTH | -111/128 (-0.867); 0 / 1 | -11/128 (-0.086); 0 / 1 |
| LURK | -25/64 (-0.391); 0 / 1 | 0 (0.000); 0 / 1 |
| GUARD | 31/64 (0.484); 1 / 0 | 0 (0.000); 0 / 1 |
| EVADER | 59/128 (0.461); 1 / 0 | 0 (0.000); 0 / 1 |
| GREED | -1/2 (-0.500); 0 / 1 | 0 (0.000); 0 / 1 |
| ADAPT | -71/128 (-0.555); 0 / 1 | -9/64 (-0.141); 0 / 1 |

### C-E6L (companion arm, control)

P_none = False (stab 0); P_win = False (stab 0); P_never = True (stab 1). Universal members: SPLIT; stab(i universal): SPLIT 1.

u(i, j), row i against column j, exact value with n_distinct in brackets:

| i \ j | RUSH | PACED | SPLIT | STEALTH | LURK | GUARD | EVADER | GREED | ADAPT |
|---|---|---|---|---|---|---|---|---|---|
| **RUSH** | 1/2 | 1/2 [2] | 1/2 [2] | 1/2 [2] | 1/2 [2] | 1/2 [2] | 1/2 [7] | 1 [2] | 1/2 [3] |
| **PACED** | 1/2 [2] | 1/2 | 1/2 [2] | 1/2 [2] | 1/2 [2] | 1/2 [2] | 1/2 [7] | 1 [2] | 1/2 [3] |
| **SPLIT** | 1/2 [2] | 1/2 [2] | 1/2 | 1/2 [2] | 1/2 [2] | 1 [39] | 1 [57] | 1 [2] | 1 [41] |
| **STEALTH** | 1/2 [2] | 1/2 [2] | 1/2 [2] | 1/2 | 1/2 [2] | 1/2 [2] | 1/2 [7] | 1 [2] | 1/2 [3] |
| **LURK** | 1/2 [2] | 1/2 [2] | 1/2 [2] | 1/2 [2] | 1/2 | 1/2 [2] | 1/2 [7] | 1 [2] | 1/2 [3] |
| **GUARD** | 1/2 [2] | 1/2 [2] | 0 [39] | 1/2 [2] | 1/2 [2] | 1/2 | 1/2 [3] | 0 [14] | 1/2 [3] |
| **EVADER** | 1/2 [7] | 1/2 [7] | 0 [57] | 1/2 [7] | 1/2 [7] | 1/2 [3] | 1/2 | 0 [14] | 1/2 [4] |
| **GREED** | 0 [2] | 0 [2] | 0 [2] | 0 [2] | 0 [2] | 1 [14] | 1 [14] | 1/2 | 1 [14] |
| **ADAPT** | 1/2 [3] | 1/2 [3] | 0 [41] | 1/2 [3] | 1/2 [3] | 1/2 [3] | 1/2 [4] | 0 [14] | 1/2 |

BR_ε(j), with each fixed member's bootstrap stability of being in BR_ε(j) (members at 0 omitted):

| j | BR_ε(j) | stab (nonzero) |
|---|---|---|
| RUSH | EVADER, GUARD, LURK, PACED, RUSH, SPLIT, STEALTH | RUSH 1, PACED 1, SPLIT 1, STEALTH 1, LURK 1, GUARD 1, EVADER 1 |
| PACED | EVADER, GUARD, LURK, PACED, RUSH, SPLIT, STEALTH | RUSH 1, PACED 1, SPLIT 1, STEALTH 1, LURK 1, GUARD 1, EVADER 1 |
| SPLIT | LURK, PACED, RUSH, SPLIT, STEALTH | RUSH 1, PACED 1, SPLIT 1, STEALTH 1, LURK 1 |
| STEALTH | EVADER, GUARD, LURK, PACED, RUSH, SPLIT, STEALTH | RUSH 1, PACED 1, SPLIT 1, STEALTH 1, LURK 1, GUARD 1, EVADER 1 |
| LURK | EVADER, GUARD, LURK, PACED, RUSH, SPLIT, STEALTH | RUSH 1, PACED 1, SPLIT 1, STEALTH 1, LURK 1, GUARD 1, EVADER 1 |
| GUARD | GREED, SPLIT | SPLIT 1, GREED 1 |
| EVADER | GREED, SPLIT | SPLIT 1, GREED 1 |
| GREED | LURK, PACED, RUSH, SPLIT, STEALTH | RUSH 1, PACED 1, SPLIT 1, STEALTH 1, LURK 1 |
| ADAPT | GREED, SPLIT | SPLIT 1, GREED 1 |

Δ_j(lo, hi) = u(lo, j) − u(hi, j), with stab(Δ ≥ ε) / stab(Δ ≤ 0):

| j | LURK − RUSH | PACED − RUSH |
|---|---|---|
| RUSH | 0 (0.000); 0 / 1 | 0 (0.000); 0 / 1 |
| PACED | 0 (0.000); 0 / 1 | 0 (0.000); 0 / 1 |
| SPLIT | 0 (0.000); 0 / 1 | 0 (0.000); 0 / 1 |
| STEALTH | 0 (0.000); 0 / 1 | 0 (0.000); 0 / 1 |
| LURK | 0 (0.000); 0 / 1 | 0 (0.000); 0 / 1 |
| GUARD | 0 (0.000); 0 / 1 | 0 (0.000); 0 / 1 |
| EVADER | 0 (0.000); 0 / 1 | 0 (0.000); 0 / 1 |
| GREED | 0 (0.000); 0 / 1 | 0 (0.000); 0 / 1 |
| ADAPT | 0 (0.000); 0 / 1 | 0 (0.000); 0 / 1 |

## Appendix R. Reproduction

The registered order of commands (`python -m tools.research.v6.e6.run_e6 …`), each refusing to run out of order:

| Step | Command | Record (under `runs/research_v6_e6/v6-e6-matrix-v2-7de29a4a6954/records/`) | SHA-256 |
|---|---|---|---|
| I-7 | `generate-seeds --confirm-seed-generation` | the freeze record's seed block (committed at `0d8b638`) | commitment `61e292f6…5e1c83` |
| Q | `execute C-E6/C-E6L F1/F2 --confirm-matrix-execution`, then `qualify` | `qualification.json` | `89f448e0b2b6b4878eea3248804afd8b6e8c1ba47094d6ebb567dae5cd6cacd1` |
| T | `execute T-E6/T-E6L F1/F2 --confirm-matrix-execution --confirm-treatment-execution` | per-field `experiment_result.json`, `provenance.json`, `traces/` | pinned in `pre_reveal_manifest.json` |
| T gates | `treatment-gates T-E6`, `treatment-gates T-E6L` | `treatment_gates_T-E6.json`, `treatment_gates_T-E6L.json` | `1893923fa07eebf69fbc12e654d0d1be731c64c37473606a27d36795122b4f48`, `0dd9cc4d7eea1ff210befc27a87719442d125c8d9ca6e127719d49c529b9c409` |
| Analysis | `analyze` | `e6_analysis.json` | `eb5c49ef34deb5e18ef51a445f72440e71af11f60d16a8b79520b6a1b017bb51` |
| Reveal, D-6 | `reveal tools/research/v6/e6/seeds_revealed.txt` | `d6.json` | `e771802e256ac88c42ce18f95f0522d20c58f2881a58c1021f69620d806f9ac1` |
| Interpretation | `interpret` | `e6_interpretation.json` | `0b1c21bd35748e053375aa23163fe92e00b5bcbee1eafa355ccc62a64b16a32f` |

Supplementary records: `checkpoint_b_supplementary.json` `4a5c3b94…98b7a`, `treatment_supplementary.json` `dcac3f9f…4500`, `control_against_control_readings.json` `7c6ad0d6…da83`, `trace_size.json` `008fefaf…9167`.

**Tracked records:**
- `tools/research/v6/e6/analysis_freeze_v2.json`: the freeze, the seed block and the control qualification.
- `tools/research/v6/e6/pre_reveal_manifest.json`: every artifact the interpretation reads, pinned before the reveal (`69724fd`).
- `tools/research/v6/e6/seeds_revealed.txt`: the revealed list (`0951fa3`).
- `tools/research/v6/e6/final_record.json`: `d6.json` and `e6_interpretation.json` verbatim, with their SHA-256 (`5100ec0`).

The frozen analysis is deterministic. Re-running `treatment-gates` and `analyze` over the preserved corpus reproduces the recorded files byte for byte (§G).
