# Bytefray V6 E7 — Sensing × Disruption Interaction: Design and Adversarial Review

**Status:** Design and adversarial review only. Nothing is registered. No engine code, Ruleset, agent, pre-registration, seed, matrix cell or gameplay probe was created or run. E6 is closed and is not edited, rerun or reinterpreted. Every E6 registered finding, flag, kill criterion and disposition stands exactly as the frozen interpreter issued it.
**Revision:** This version incorporates the research lead's rulings of 2026-09-29, made before commit:
- **An all-unit family measure.** A new interaction measure over all 45 frozen units, **I_all**, is added to the post-hoc audit as the primary family-level description. It is defined here and deliberately not computed (§6.1).
- **A rename.** The measure over the units neutral under both controls is renamed **I_common_neutral**. It is kept as a secondary analysis, comparable to PF-4.
- **A revised post-audit rule.** A material disagreement between the audit and this review now means STOP and reconcile, not an automatic E7-F (§8.1).

§16 records every ruling.
**Branch:** `v6-research` at `dfe8432`. The tree was clean before this review, and this file is its only change.
**Date:** 2026-09-29
**Governing records:**
- [`V6_E6_PRICED_SENSING_PREREGISTRATION.md`](V6_E6_PRICED_SENSING_PREREGISTRATION.md) (**PR**);
- [`V6_E6_PRICED_SENSING_RESULTS.md`](V6_E6_PRICED_SENSING_RESULTS.md) (**E6-R**);
- [`V6_PRICED_SENSING_DESIGN_REVIEW.md`](V6_PRICED_SENSING_DESIGN_REVIEW.md) (**DR**);
- [`V6_E6_PRICED_SENSING_IMPLEMENTATION_PLAN.md`](V6_E6_PRICED_SENSING_IMPLEMENTATION_PLAN.md) (**plan**) and [`V6_E6_AMENDMENT_1_FAMILY_CORRECTIONS.md`](V6_E6_AMENDMENT_1_FAMILY_CORRECTIONS.md) (**A1**);
- [`V6_E2_E5_CROSS_EXPERIMENT_SYNTHESIS.md`](V6_E2_E5_CROSS_EXPERIMENT_SYNTHESIS.md) (**synthesis**).

**The question under review:**

> **Was E6's KC-5 seat artifact caused by priced sensing itself, by whole-tick disruption, or by an interaction between priced sensing and disruption duration?**

The provisional name for any follow-on experiment is **E7**. This review decides whether a clean causal experiment can isolate the question, and if so, what the smallest defensible one is. It does not assume the answer.

---

## 1. Status and Evidence Tiers

| Tier | Meaning |
|---|---|
| [SOURCE] | Current source at `dfe8432`, cited by file and line. |
| [DOC] | A committed research record. |
| [CORPUS] | A value read from the frozen E6 artifacts under `runs/research_v6_e6/v6-e6-matrix-v2-7de29a4a6954/`: `e6_analysis.json`, each field's `experiment_result.json`, the telemetry summaries and the stored per-callback rows. Before use, `e6_analysis.json`, `e6_interpretation.json` and `d6.json` were hashed and equal the SHA-256 values in E6-R Appendix R. |
| [POST-HOC] | An exploratory descriptive calculation made in this review on [CORPUS] values: arithmetic, cross-tabulation, and seed resampling with the registered O-BOOT draws (`payoff.resample_positions`, `random.Random(42)`, 1000 × 32). **Not registered, not an E6 result, and unable to confirm anything.** No threshold in this review was chosen from one. |
| [STRUCT] | A non-outcome structural check: a field-by-field comparison of the four Ruleset policy objects, and source searches. |
| [TRACE] | A hand trace of source semantics. It was not executed, and it is not a result. |
| [INFERENCE] | Reasoning from the tiers above. |

**What was run.** Only read-only Python over the frozen corpus, and pure comparisons of Ruleset objects. No controller, agent, match or probe was constructed. Nothing was written under `runs/`. The scratch scripts live in the session scratchpad, not in the repository. The E6 seed values have been public since `0951fa3`. This review nevertheless refers to seeds only by their position (s01 to s32) in the revealed list.

**The one re-implementation.** The frozen E4 seat metrics key cells by unique seed, so they cannot take a resampled multiset. The [POST-HOC] resampling therefore re-implements `pairing_seat_metrics` and `mirror_seat_metrics` with multiplicity. On the identity resample it reproduces **all 180 frozen (unit, condition) values of GSB and SDom exactly** (45 units × 4 conditions).

---

## Verdict in Brief

**RE-ANALYZE E6 FIRST — registration of E7 is premature.**

1. **E6 is structurally a complete 2×2, but it was not registered as a factorial.** [STRUCT, CORPUS]
   - The four Rulesets differ exactly as a factorial: `detection_radius` ∈ {None, 32} × `disruption_slot_limit` ∈ {None, 1}, and no other field.
   - All 2,880 cell keys pair across the four conditions, with identical seat geometry and seat assignment. The family, executor and analyzer are also identical.
   - What E6 lacks is registration. The companion is "never a verdict", no interaction estimand was registered, and PF-4 is a point-estimate, control-conditioned "any unit" flag. The question itself was raised by the results.
2. **KC-5, as it fired, is an exact-counterfactual interaction at the level of one unit.** [CORPUS] PACED–ADAPT has GSB 0 under C-E6, 0 under C-E6L, −1/64 under T-E6L and **+1/8 under T-E6**. The engine is deterministic and the cells are matched, so each of these 64 matches has an exact counterfactual in every other condition.
3. **The mechanism runs through ADAPT's absolute-tick damage check. Who sees first does not drive it.** [SOURCE, CORPUS]
   - PACED sees first in all 64 cells of both treatments.
   - Under whole-tick disruption, once PACED has hit it, ADAPT gets no callback in a tick where PACED moves first. So ADAPT acts only on ticks of the parity its seat fixes, until it evades out of sight.
   - ADAPT's first action in a tick is a READ of own-core cell (*t* − 1) mod 8 (plan P-4). So the seat decides which cell it checks and when.
   - ADAPT then evades in 22 of 32 cells when PACED is Seat B, against 11 of 32 when PACED is Seat A. Every T-E6 tie follows such an evasion.
   - Under λ = 1, ADAPT is locked out of no tick examined. It evades in 64 of 64 cells, and 57 of 64 end tied.
4. **At the family level, the arm contrast is fragile, and there is no stable average interaction.** [POST-HOC]
   - Under the registered seed resampling, PF-4 is raised in **967/1000 resamples of the primary arm and 819/1000 of the companion**. The observed pattern, raised in the primary but not the companion, occurs in 177/1000.
   - **I_common_neutral**, the mean interaction on |GSB| over the 26 units neutral under both controls, is **−3/1664 ≈ −0.002**. It is positive in 519/1000 resamples: a coin flip.
   - Without ADAPT's units, neither arm raises PF-4 at the point estimate. The resampling rates are 429 and 477 per 1000, and the mean interaction leans negative (751/1000 at or below zero). The only positive lean is inside ADAPT's nine units (746/1000 above zero).
   - **I_all**, the same interaction averaged over all 45 frozen units, is defined in §6.1 but not computed here. The audit computes it first (§8.1).
5. **So the tempting inference fails as a general statement.** "The companion lacked KC-5, so whole-tick disruption caused the seat artifact" holds for one hindsight-selected unit, and there only through a family-specific mechanism. It does not hold for the family.
6. **No E7 is ready to register.**
   - A unit-level E7 would retest a mechanism already traced to source.
   - A family-level E7 would test a hypothesis the corpus already contradicts descriptively.
   - The only experiment that adds evidence is a fresh-seed replication of the whole E6 matrix with a registered interaction estimand: 11,520 matches, the size of E6 itself (§8.2).

   Findings 2–5 rest on this review's exploratory scripts. They should be formalized, independently verified and committed as a labelled post-hoc audit before anyone registers E7 or closes the line (§8.1). If the audit reproduces them, this interaction question closes with no new experiment. If it materially disagrees, the line stops until the discrepancy is reconciled.

---

## 2. Exact E6 Factual Baseline

### 2.1 Identities and registered results [DOC]

| Item | Value |
|---|---|
| Structural matrix | `v6-e6-matrix-v2-7de29a4a6954` |
| Execution matrix | `v6-e6-exec-v1-62b88ba3ddb4` (seed commitment `61e292f6…5e1c83`) |
| Analysis freeze | `v6-e6-freeze-v2-275057e27725` |
| History | `6949557` controls qualified (Checkpoint B); `69724fd` pre-reveal boundary; `0951fa3` seed reveal; `5100ec0` D-6 and interpretation; `dfe8432` results record |
| Corpus | 11,520 cells: 2,880 per condition (F1 2,304 + F2 576), 32 seeds, 9 members |
| E6-D | PASS (D-1 to D-7) |
| Primary arm | E6-H1T SUPPORTED, E6-H1C REFUTED, E6-H2 SUPPORTED, E6-H0 NEITHER, E6-H3 REFUTED; PF-4 raised (`F1\|PACED\|ADAPT` only); KC-5 fires |
| Interpretation | `R-CREATES`, qualified by E6-H2 SUPPORTED |
| Disposition | `REJECT as a gameplay candidate` (KC-5) |
| Companion reading | "differs": the one difference in the registered comparison set is "KC-5: fires (primary) vs does not fire (companion)". It is never a verdict (PR §6.8). |

### 2.2 The four Rulesets, field by field [SOURCE, STRUCT]

Every field of the four policy objects (`ruleset_policy.py:664–674, 789–802, 940–956, 960–976`):

| Field | C-E6 `research-scale` | T-E6 `research-sensing-r32` | C-E6L `research-disruption-slot1` | T-E6L `research-disruption-slot1-sensing-r32` |
|---|---|---|---|---|
| scheduler | chunked, chunk 2, rotate start | same | same | same |
| core placement / selection / stride / displacement | seeded / round robin / `fixed_64` / literal | same | same | same |
| `capture_hold_ticks` | 1 | 1 | 1 | 1 |
| `scheduler_pass_order` | forward | forward | forward | forward |
| `initial_anchor_placement` | `core_base` | `core_base` | `core_base` | `core_base` |
| **`disruption_slot_limit`** (λ) | **None** (whole tick) | **None** | **1** | **1** |
| **`detection_radius`** | **None** | **32** | **None** | **32** |

A field-by-field `dataclasses.asdict` comparison (ruleset_id aside) gives exactly:

| Comparison | Fields that differ |
|---|---|
| C-E6 vs T-E6 | `detection_radius` only |
| C-E6L vs T-E6L | `detection_radius` only |
| C-E6 vs C-E6L (the parents) | `disruption_slot_limit` only |
| T-E6 vs T-E6L | `disruption_slot_limit` only |
| C-E6 vs T-E6L, and T-E6 vs C-E6L | both, and nothing else |

### 2.3 How the corpus pairs [CORPUS, STRUCT]

- **Cells.** All 2,880 cell keys (field, subject, opponent, orientation, seed) exist in all four conditions. All 2,880 have identical seat geometry (`subject_start`, `opponent_start`) and seat assignment across the four.
- **Family.** The same 18 packages and one policy source (`agent.py` SHA-256 `5374092e…3b63`). The policy never reads `detection_radius` or any disruption setting. It sees the treatment only through its observations.
- **Analysis.** Both arms are computed by the same `analyze_arm` (`analyze_e6.py:356`), including the seat metrics of all 45 units in all four conditions (`analyze_e6.py:249–261`).
- **Evaluation identity.** The Ruleset-ID predicates in `evaluation_contracts.py:609–634` select evaluation methodology only. All four E6 identities resolve to the same seeded-geometry, identity-v7 recipe (`is_ruleset_v4_derived_methodology`, `:637`). None of them changes gameplay.
- **Execution.** Controls ran at `0d8b638` and treatments at `6949557`, with the same engine tree (`691f6666…`) (E6-R §A).

---

## 3. What E6 Does and Does Not Establish

### 3.1 Question 1 in the brief: is there a valid 2×2?

**Structurally, yes.** Sensing is the only within-arm treatment variable, and disruption duration is the only cross-arm parent difference (§2.2). Cells are matched across all four conditions (§2.3). No scheduler, capture, spawn, process-selection, placement or scoring semantic differs between any two conditions.

**Two couplings are part of the factors themselves, not confounds:**

1. **Suppression governs sensing as well as acting.** `_is_suppressed` is the single predicate behind both eligibility and passive sensing (`process_runtime.py:800–821, 846–850, 890`). Disruption duration therefore also sets how long a victim is blind. Under the controls this matters only for SPLIT: every member declares reach 256, and a suppressed single-process entrant gets no callback at all. Under the treatments it is part of how the two factors interact.
2. **The family counts its own callbacks.** PACED moves on odd callback indexes (fixture `agent.py:293–296`). ADAPT checks its core at callback index 1 of each tick (`:368–369`). A lost offer changes those counts. So the disruption factor changes this population's behavior through callback counting as well as through action denial. That is a property of the population, not of the Rulesets (§5, D).

**Inferentially, no.** The 2×2 is not a registered factorial, for four reasons:

- **The companion was registered only as a status comparison.** It "never replaces a primary verdict, and it never triggers a kill" (PR §6.8). No sensing × disruption estimand, threshold or interpretation row exists.
- **PF-4 is not an interaction measure.** It is a point-estimate flag with no bootstrap requirement. It fires when *any* unit that was neutral under its own arm's control is non-neutral under that arm's treatment. The two arms condition on different eligible sets: 26 units under C-E6 and 30 under C-E6L (§4.7). "KC-5 fires in one arm and not the other" is a difference of two maxima over different denominators, not a contrast of effects.
- **The interaction question and the unit that carries it were both found in the results.** Any estimand aimed at PACED–ADAPT is selected with hindsight.
- **The E6 seeds are public**, and E6's cells are the data that generated the hypothesis. They cannot also test it.

"Factorial" is therefore used in this review only in the structural sense. Every interaction value computed from E6 is [POST-HOC].

### 3.2 What E6 establishes

**By registration (unchanged):**
- **`R-CREATES`, qualified by E6-H2 SUPPORTED.** Priced sensing creates an opponent-dependent allocation of actions, with an information/action tradeoff. The companion reproduces E6-H1T, E6-H1C, E6-H2 and E6-H3.
- **KC-5 fires on the primary arm**, so the disposition is REJECT.
- **The registered companion reading is "differs" (KC-5).** It is literally true of the point estimates.

**Descriptively, from exact counterfactual cells [CORPUS]:**
- **In PACED–ADAPT, the seat bias needs both factors.** Neither alone produces any (§4.2).
- **Priced sensing mostly removes seat determination in both arms.** Neutral units rise from 26 to 38 in the primary and from 30 to 39 in the companion (E6-R §F.4).
- **The disruption regime almost never changes who sees first.** The first seer is the same entrant under T-E6 and T-E6L in 2,299 of 2,304 F1 cells, and the first-detection tick and callback order are identical in 2,285. The disruption factor acts after first contact.

### 3.3 What E6 does not establish

- **No general causal claim about whole-tick disruption.** E6 does not show that whole-tick disruption is what makes priced sensing seat-unsafe. E6-R itself says so ("No causal claim", §"What this report does not claim"), and §6 of this review shows that the family-level description does not support it.
- **Not that λ = 1 is seat-clean under priced sensing.** Under resampling, the companion raises PF-4 in 819/1000 resamples (§6.2). At the point estimate, six units remain non-neutral under T-E6L. PF-4 cannot see them, because their controls were already non-neutral (§4.7).
- **Not that the interaction is independent of the family.** The only unit that carries it runs through ADAPT's own schedule (§4).
- **No rate claim about control seat neutrality.** PACED–ADAPT's neutrality rests on 2 distinct trajectories in each control (E6-R §I.4).

---

## 4. Mechanism Reconstruction of KC-5

### 4.1 The registered trigger [CORPUS]

- **The unit.** PF-4 was raised by `F1|PACED|ADAPT` alone.
- **Under C-E6:** SDom 0 and GSB 0, with n_distinct 2.
- **Under T-E6:** SDom 0 and GSB **+8/64 = 1/8**, with n_distinct 25.
- **The bound.** |GSB| > 1/10 needs a Seat A–Seat B difference of at least 7 of the 64 matches. So the margin is two single-match steps: one decisive match moving to the other seat, or two turning into ties.
- **SDom is 0 in every condition.** No seed has the same seat winning both orientations, because ADAPT never wins a match. PF-4 therefore fired through GSB alone.

### 4.2 The pairing in all four conditions [CORPUS]

| Condition | PACED in Seat A (win / tie / loss) | PACED in Seat B (win / tie / loss) | Seat A wins | Seat B wins | GSB | u(PACED, ADAPT) | n_distinct | How matches end |
|---|---|---|---|---|---|---|---|---|
| C-E6 | 32 / 0 / 0 | 32 / 0 / 0 | 32 | 32 | 0 | 1 | 2 | PACED captures ADAPT |
| **T-E6** | **30 / 2 / 0** | **22 / 10 / 0** | 30 | 22 | **+1/8** | 29/32 | 25 | captures at ticks 3–12; tick-limit ties |
| C-E6L | 0 / 32 / 0 | 0 / 32 / 0 | 0 | 0 | 0 | 1/2 | 2 | tick-limit ties |
| T-E6L | 3 / 29 / 0 | 4 / 28 / 0 | 3 | 4 | −1/64 | 71/128 | 30 | 7 captures (ticks 7–35); 57 tick-limit ties |

- **Which seat gains.** Seat A, by 8 wins. But ADAPT wins no match in any condition. The artifact is that **the attacker's capture reliability depends on its seat**: PACED captures from Seat A in 30 of 32 matches, and from Seat B in 22 of 32.
- **Outcome classes under T-E6.** PACED as Seat A gives 30 A_WIN and 2 TICK_LIMIT_TIE. PACED as Seat B gives 22 B_WIN and 10 TICK_LIMIT_TIE. Every decisive match is a core capture.
- **Decision ticks under T-E6.** PACED in Seat A captures at tick 4 (4 cells), 5 (21), 6 (2) and 10 (3). PACED in Seat B captures at tick 3 (5), 4 (1), 5 (4), 6 (9), 11 (2) and 12 (1).
- **Both factors are necessary in this unit.** Each control is seat-neutral, and so is the sensing treatment under λ = 1. Only the combination of sensing radius 32 and whole-tick disruption produces the bias. The four cells of each (seed, orientation) are exact counterfactuals of one another, so this is a statement about these 64 matches, not an estimate.

### 4.3 The lockout rule [SOURCE, TRACE]

**How a hit suppresses its victim** [SOURCE]:
- A hit sets `disrupted_until_tick = tick + 1` (`process_runtime.py:1344`), and `is_disrupted` is `tick < disrupted_until_tick` (`:124–125`). So the window is the hit tick only, and every tick starts fresh.
- **Whole tick (λ = None).** The victim is ineligible, and blind, for the rest of the tick (`:816–821`). A single-process entrant with nothing eligible forfeits each offer without a callback (`:1132–1138`).
- **λ = 1.** The victim loses exactly its next offer (`:1366–1393`). A second hit re-assigns the count and never adds to it (`:1345–1349`).
- **Offers come in contiguous pairs.** An entrant's two offers in a pass are consecutive (`scheduler.py:98–104`), so no opponent action falls between them.

**The family's attacker re-hits once per tick** [SOURCE]. Its first priority is to WRITE any visible enemy anchor not yet written in the current tick (fixture `agent.py:325–328`, with the per-tick `written` set reset at `:135–138`).

**Consequence for a victim that stays visible and does not move** [TRACE]:

| | A tick the attacker moves first in | A tick the victim moves first in |
|---|---|---|
| Whole tick | No callback: the hit lands at the attacker's first offer | Its first chunk (2 offers), then none once the attacker's chunk hits it, unless the victim disrupts the attacker first |
| λ = 1 | 7 of its 8 offers | at least 7 of its 8 offers |

A victim that moves presents a new, unwritten anchor and can be hit again in the same tick. Even an attacker that re-hit in every one of its chunks could take at most one offer per victim chunk under λ = 1, leaving the victim at least 4 per tick.

**So whole-tick lockout confines a re-hit victim to the ticks on which it moves first.** Under the rotation rule those are the odd ticks for Seat A and the even ticks for Seat B (`scheduler.py:86–88`; A1 C-1). Under λ = 1 the victim acts in every tick.

This half of the mechanism is a property of the Ruleset and the attacker's priority rule, and needs no experiment. It holds under the controls too. There, though, the parent's canonical tick-1 lines end PACED–ADAPT before the defender's schedule matters.

### 4.4 ADAPT's damage check [SOURCE]

**The rule.** Plan decision P-4 is implemented at fixture `agent.py:368–369`:
- At callback index 1 of tick *t* (its first callback of the tick, whenever that comes), ADAPT READs own-core cell (*t* − 1) mod 8.
- It does this before anything else, including disrupting a visible enemy.
- The result is judged at its next callback (`:163–171`). An owner other than itself sets `pending_evade`, and the next action is the evade MOVE (`:370–373`), at most once per match.

**This is the frozen, approved specification, and the implementation matches it.** It is not a defect in the sense of A1.

**The schedule is keyed to the absolute tick.** With §4.3, the tick on which a locked-out ADAPT next acts, and so the core cell it checks then, depends on its seat.

### 4.5 What the callback rows show under T-E6 [CORPUS]

| | PACED in Seat A | PACED in Seat B |
|---|---|---|
| PACED sees first | 32 of 32 | 32 of 32 |
| PACED's first-detection tick | 1 in 15 cells, 2 in 17 | 1 in 17 cells, 2 in 15 |
| Ticks with no ADAPT callback, after detection | the PACED-first (odd) ticks after the detection tick, typically 3 and 5, until ADAPT evades out of PACED's sight or is captured | the PACED-first (even) ticks after the detection tick, typically 2, or 2 and 4, with the same ending |
| ADAPT's first callback after PACED's detection | tick 2 (after a tick-1 detection) or tick 4 (after a tick-2 detection) | tick 3 in all 32 cells |
| The cell that check reads | cell 1 (tick 2) or cell 3 (tick 4) | cell 2 (tick 3) |
| Damage found at that first check | 0 of 15 at tick 2; 4 of 17 at tick 4 | 11 of 17 after a tick-1 detection; 0 of 15 after a tick-2 detection |
| ADAPT evades | **11 of 32** (tick 4: 6; tick 6: 5) | **22 of 32** (tick 3: 11; tick 5: 10; tick 9: 1) |
| Tick-limit ties | 2, both after an evasion at tick 4 | 10: 6 after an evasion at tick 3, 4 at tick 5 |
| Cells without an evasion | 21, all captured (all at tick 5) | 10, all captured (9 at tick 6, 1 at tick 4) |

- **All 12 ties follow an ADAPT evasion**, and all 31 cells without an evasion end in PACED's capture.
- **Reading the table** [INFERENCE]. Take PACED as Seat B, detecting on tick 1, a tick ADAPT moved first in. The lockout gives PACED the rest of tick 1 and all of tick 2 uninterrupted before ADAPT's first callback at tick 3. By then PACED has confirmed the core and started its in-order cursor over cells 1, 2, … (A1 C-3). ADAPT's tick-3 check of cell 2 finds it overwritten in 11 of 17 such cells.
- **The Seat A counterpart.** PACED's corresponding long lockout, after a tick-2 detection, ends at tick 4. That check reads cell 3, and finds damage in 4 of 17.
- **So the seat difference is an alignment.** It lines up three things: ADAPT's (*t* − 1) mod 8 schedule, the tick parity the seat fixes, and PACED's cursor order.
- **Why evasion leads to ties.** An evaded anchor off the core makes a disruption plus a full core sweep cost 9 actions against 8 (DR T2), and some of those cells stall into tick-limit ties.
- **Scope of the reading.** It rests on the rows' detection ticks, callback counts, check results and MOVEs. PACED's per-tick write progress was not traced in every cell, so "cell 2 is overwritten more often than cell 3" is read from the check results, not from write histories.

### 4.6 Why the same pairing is seat-neutral under λ = 1 [CORPUS]

- **Detection is unchanged.** PACED's first detection has the same tick and callback order as under T-E6 in all 64 cells. ADAPT then sees PACED one callback later, in the same tick.
- **ADAPT is never locked out.** It has a callback in every tick examined (ticks 1–12 of every cell), so it checks every tick. It finds damage somewhere between tick 1 and tick 9, and evades in **64 of 64** cells.
- **Most cells tie.** 57 of 64 end in tick-limit ties, and PACED captures 3 times from Seat A and 4 times from Seat B.
- **The low GSB is largely automatic.** GSB counts decisive matches only, so a decisive share of 7/64 guarantees |GSB| ≤ 7/64 whatever the seat pattern. Most of this unit's between-arm difference in GSB follows from λ = 1 turning the pairing into a draw. That is a main effect of disruption on decisiveness, and it enters any interaction computed on GSB (§10.1).

### 4.7 Context units: recorded, not promoted [CORPUS]

**Eligibility differs by arm.**
- **The two eligible sets.** PF-4 can only fire on a unit that is neutral under its own arm's control: 26 units under C-E6 and 30 under C-E6L. The primary's 26 are all among the companion's 30.
- **The four extra units.** The companion adds RUSH, PACED, STEALTH and LURK against EVADER. Under C-E6 each has GSB 31/64, because whole-tick disruption gives a Seat A attacker the tick-1 forced line against an EVADER that has not yet moved (E6-R §F.3–F.4; A1 C-1).
- **What that shows.** This is whole-tick disruption creating seat determination by itself, under free sensing.

**Near-threshold neutral units** (within one match or seed of the bound):
- T-E6: the ADAPT mirror at 3/32 (one seed short of 4/32), and GREED–ADAPT at −5/64.
- T-E6L: LURK–ADAPT at +6/64 and LURK–GREED at −6/64, each one match short of 7/64.

**Non-neutral under a treatment but never eligible**, because the control was already non-neutral. PF-4 is blind to these by construction.
- T-E6: RUSH–PACED 7/16, RUSH–SPLIT 17/64, PACED–SPLIT 9/64, SPLIT–STEALTH −5/32, PACED mirror 7/32, RUSH mirror 5/32.
- T-E6L: RUSH–PACED 27/64, RUSH–SPLIT 9/32, PACED–SPLIT 7/64, PACED mirror 1/8, RUSH mirror 5/32, SPLIT mirror 5/32.

**LURK–GREED is a different mechanism.**
- **Under priced sensing, neither member ever sees the other**, since neither moves or searches. The match becomes a painting race that ends in single or mutual core loss.
- **Its outcomes.** T-E6: 17 LURK wins, 17 GREED wins and 30 mutual eliminations. T-E6L: 7, 7 and 50.
- **Under both controls,** LURK sees GREED from its first callback and wins 64 of 64.
- **Its seat sensitivity** comes from paint-front order, not from ADAPT.

**The companion's near-threshold units lean to Seat B.** Examples are LURK–GREED, and the LURK and STEALTH mirrors at −3/32. This fits the moderate last-mover-leaning order dependence that E3 found once whole-tick denial was removed, and that survived E4 and E5 (synthesis §C.4 and §E.1). [DOC, INFERENCE]

None of these is a registered finding. They are listed so that the reconstruction does not quietly narrow to one unit.

### 4.8 What the reconstruction does not show

- **That another defender would behave the same way.** Only ADAPT's specific schedule was observed. E6 does not show that every family with a periodic defender check would produce the artifact.
- **The magnitude on other seeds.** E6 has 32 seeds and one family.
- **A rate.** PACED–ADAPT's treatment values rest on 25 (T-E6) and 30 (T-E6L) distinct trajectories, and its control values on 2.

---

## 5. Candidate Causal Explanations

### A. Priced sensing alone

- **Supports.**
  - Sensing is necessary for PACED–ADAPT's artifact: both controls are neutral (§4.2).
  - Under resampling, priced sensing produces new near-threshold seat flags under *both* disruption regimes: PF-4 is raised in 967 and 819 of 1000 [POST-HOC]. In this family, priced sensing is associated with seat sensitivity whatever the disruption regime.
- **Contradicts.**
  - Sensing alone does not produce PACED–ADAPT's artifact: under T-E6L its GSB is −1/64, and |GSB| exceeds 1/10 in only 4 of 1000 resamples.
  - The proposed pathway, local visibility changing who detects first, is not the one at work. PACED sees first in 64 of 64 cells of both treatments, and the first seer is the same under both disruption regimes in 2,299 of 2,304 F1 cells (§3.2).
- **Unresolved.** Whether priced sensing creates *stable* seat artifacts in a population without ADAPT. At the point estimate, neither arm raises PF-4 without ADAPT's units. The resampling rates are 429 and 477 per 1000, below any stability bar.

### B. Whole-tick disruption alone

- **Supports.**
  - Under free sensing, whole-tick disruption already produces seat determination: 19 non-neutral units under C-E6 against 15 under C-E6L, including the four attacker–EVADER pairings at GSB 31/64 (§4.7).
  - This matches E3. The synthesis's §D.1 table reads whole-tick denial as "Load-bearing for first-mover exclusivity and for much of the seat determination", with E3's D2 (seat determination decreases) SUPPORTED. [DOC, CORPUS]
- **Contradicts.**
  - Whole-tick disruption alone leaves PACED–ADAPT seat-neutral: under C-E6, PACED captures 64 of 64.
  - PF-4 cannot fire on any artifact that whole-tick disruption creates in the control, because such a unit is already non-neutral there.
- **"Priced sensing merely exposes an existing instability": partly, and then it is an interaction.**
  - The lockout rule of §4.3 exists under C-E6 too.
  - But there, unverified adoption and the canonical tick-1 lines end the match before ADAPT's schedule can matter.
  - Priced sensing lengthens the opening enough for lockout and schedule to meet: verification replaces adoption (A1 C-1, C-2). That is not "B alone".

### C. Interaction

- **Supports.**
  - An exact-counterfactual interaction at the unit level (§4.2).
  - The resampled interaction on PACED–ADAPT's GSB is positive in 1000 of 1000 resamples, with median 9/64 and a 95% band of [3/64, 1/4] [POST-HOC].
  - The mechanism is traced (§4.3–§4.5).
- **Contradicts.**
  - As a family-level effect: I_common_neutral, over the 26 units neutral under both controls, is −3/1664 and is positive in 519 of 1000 resamples. I_all was not computed here (§6.1). The flag-level arm contrast is realized in 177 of 1000, and the companion raises PF-4 in 819 of 1000 (§6.2).
  - **The stated form is also wrong in its first step.** The timing variable that matters is not first detection, which is identical across the arms. It is which ticks the defender may act in after the first hit.
- **Unresolved.** Whether the interaction exists for any defender whose behavior does not depend on the absolute tick.

### D. Agent-family artifact

- **Supports.**
  - The pathway runs through ADAPT's absolute-tick check (P-4) and PACED's in-order cursor (A1 C-3) (§4.4–§4.5).
  - Under resampling, ADAPT's units account for most PF-4 crossings in both arms:
    - primary: PACED–ADAPT 752, the ADAPT mirror 549, GREED–ADAPT 257 and LURK–ADAPT 157;
    - companion: the ADAPT mirror 443, LURK–ADAPT 382 and STEALTH–ADAPT 143 [POST-HOC].
  - Removing ADAPT's units removes the point flag in both arms. The interaction's only positive lean is inside ADAPT's nine units (746 of 1000 above zero). Outside them it leans negative (751 of 1000 at or below zero). Every unit in U* with a positive I_u contains ADAPT (§6.2).
  - The ADAPT mirror's sensitivity probably has the same root [INFERENCE]. Both ADAPTs switch to fast search at the first callback of tick 17 (O-6; implementation record §3.4), an odd tick, on which Seat A moves first.
- **Contradicts.**
  - It is not a defect: the behavior is the frozen, approved specification (P-4, O-6), and the implementation matches it.
  - Not only ADAPT's units cross under resampling. LURK–GREED crosses in 421 and 432 of 1000, and STEALTH–GUARD in 17 and 100. So seat sensitivity under priced sensing is not an ADAPT-only phenomenon.
- **Unresolved.** Nothing within E6 remains open on this point. The interaction is *not* general within the matched family: one ADAPT unit carries it.

### E. Metric artifact

- **Supports.**
  - KC-5 rests on one unit, and its margin is two single-match steps (§4.1).
  - The registered PF-4 has no stability requirement.
  - GSB counts decisive matches only, so a tie-heavy unit is capped. PACED–ADAPT under T-E6L is capped at 7/64 (§4.6).
  - The flag is a maximum over 26 or 30 eligible units, and several sit near the bound in both arms (§4.7).
  - The arm contrast is realized in 177 of 1000 resamples [POST-HOC].
- **Contradicts.** At the unit level the effect is not weak.
  - Under T-E6, |GSB| > 1/10 in 752 of 1000 resamples.
  - The 30-against-22 split in captures is systematic, and its mechanism is traced.
- **Unresolved.** Nothing within E6. The registered KC-5 stands as registered. None of this qualifies the disposition.

### Overall reading (descriptive)

| Level | Best-supported explanation |
|---|---|
| **KC-5 as it fired** (one unit) | **C through D.** An interaction between priced sensing, whole-tick lockout and ADAPT's absolute-tick schedule. |
| **"KC-5 in one arm, not the other"** | **Largely E.** A threshold realization of flags that both arms raise under resampling. |
| **Seat sensitivity under priced sensing, family-wide** | **A, for this family.** Priced sensing moves many units into neutrality and some back near the bound, under both disruption regimes. |
| **Whole-tick disruption** | **B is true of the controls.** It is not what caused KC-5. |

---

## 6. Whether the Existing E6 Data Can Estimate the Interaction

### 6.1 The estimand E6 can support

For each unit *u*, write G_u(*s*, *d*) for its registered GSB. The sensing index *s* is 0 for none and 1 for radius 32. The disruption index *d* is 0 for whole tick and 1 for λ = 1. So C-E6 is (0, 0), T-E6 is (1, 0), C-E6L is (0, 1) and T-E6L is (1, 1). N_u(*s*, *d*) is 1 if *u* is non-neutral (SDom ≥ 9/10 or |GSB| > 1/10), and 0 otherwise.

| Quantity | Definition |
|---|---|
| Sensing effect under disruption *d* | Δ_u(*d*) = \|G_u(1, *d*)\| − \|G_u(0, *d*)\| |
| Unit interaction | I_u = Δ_u(0) − Δ_u(1) |
| The frozen unit set | U_all = the 45 frozen E6 seat-metric units: 36 F1 pairings and 9 F2 mirrors. The matrix fixes it, before any outcome. |
| **All-unit interaction (primary family-level description)** | **I_all = (1/45) Σ_{u ∈ U_all} I_u** |
| Common-neutral set | U* = { *u* : N_u(0, 0) = N_u(0, 1) = 0 }, the units neutral under both controls |
| Common-neutral interaction (secondary; PF-4 lineage) | I_common_neutral = (1/\|U*\|) Σ_{u ∈ U*} I_u |
| Flag form (secondary) | L(*d*) = \|{ *u* ∈ U* : N_u(1, *d*) = 1 }\| / \|U*\|, and I_flag = L(0) − L(1) |

All of these are computable from the frozen seat metrics, with no new match. Seeds are resampled jointly across the four conditions and all units, exactly as O-BOOT resamples them.

**The two family-level measures answer different questions:**
- **I_all:** across the frozen family as a whole, does whole-tick disruption amplify the seat-bias effect of priced sensing? A difference-in-differences already subtracts each unit's own baseline, so no unit needs to be excluded for having a non-neutral control. The unit set is fixed by the matrix, not by any observed outcome. This is the cleaner family-level interaction.
- **I_common_neutral:** among units neutral under both controls, does whole-tick disruption amplify newly introduced seat bias? This is the question the registered KC-5 lineage asks, restricted to a set that is eligible in both arms.

**Baseline strata for I_all, fixed now from the controls alone.** |GSB| has a floor at 0. So a unit whose control already carries seat bias can mostly lose bias under a treatment, and a neutral unit can mostly gain it. The two controls differ in baseline seat bias by design: whole-tick disruption gives Seat A the tick-1 forced line, which λ = 1 does not (E6-R §F.4; §4.7). I_all therefore mixes "sensing creates seat bias" with "sensing removes seat bias the whole-tick control created". To keep the two readable, the audit reports I_all within three strata defined by control neutrality only:

| Stratum | Definition | Size in E6 |
|---|---|---|
| (i) | Neutral under both controls: the set U* | 26 |
| (ii) | Neutral under exactly one control | 4, all neutral under C-E6L only |
| (iii) | Neutral under neither control | 15 |

The strata are a disclosure layer, not a redefinition: I_all itself stays the plain mean over all 45 units.

**Disclosure.** This review did not compute I_all, nor any stability of it. But one of its exploratory scratch tables printed each unit's |GSB| interaction as a column, for all 45 units, before the research lead asked for I_all. The floor property above is structural. It follows from the definition of |GSB| and from the documented difference between the two controls. Still, it is recorded here that the reviewer had seen those per-unit values when writing the caveat. No definition, stratum or convention in this review was chosen from them, and I_all is first computed by the audit.

### 6.2 The descriptive values [POST-HOC]

| Quantity | Value |
|---|---|
| \|U*\| | 26 |
| PACED–ADAPT, signed: (G(1,0) − G(0,0)) − (G(1,1) − G(0,1)) | +9/64. Resampled 2.5%, 50% and 97.5% points: 3/64, 9/64 and 1/4. Positive in 1000/1000. |
| PACED–ADAPT, I_u | +7/64, the largest in U* |
| Other extremes of I_u in U* | ADAPT mirror +1/16, GREED–ADAPT +3/64; LURK–ADAPT −1/16, LURK–GREED −1/16 |
| **I_all** over all 45 units | **Not computed in this review.** The audit computes it first (§8.1). |
| **I_common_neutral** over U* (26 units) | **−3/1664 ≈ −0.0018**; positive in 519/1000, at or below zero in 481/1000 |
| I_common_neutral without ADAPT's units (17) | −5/544 ≈ −0.009; positive in 249/1000, at or below zero in 751/1000 |
| I_common_neutral over ADAPT's units in U* (9) | +7/576 ≈ +0.012; positive in 746/1000 |
| I_flag over U* | 1/26 at the point estimate; positive in 530/1000 |
| stab(PF-4 raised), primary / companion | 967/1000 / 819/1000 |
| The joint arm pattern | raised in both 790; primary only 177; companion only 29; neither 4 |
| Without ADAPT's units (36 of 45) | raised in neither arm at the point estimate; 429/1000 and 477/1000; both 190, primary only 239, companion only 287, neither 284 |

Two readings follow. Neither is registered:
- **I_common_neutral is far from the 9/10 stability convention.** It is positive in only 519 of 1000 resamples. Had it been a registered E7-F reading under §10.2, it would be NEITHER.
- **The positive lean lives entirely in ADAPT's stratum.** Exactly four units in U* have a positive I_u: PACED–ADAPT, the ADAPT mirror, GREED–ADAPT and EVADER–ADAPT (+1/64). Every one contains ADAPT. Every other unit has I_u ≤ 0.

### 6.3 Why this is not enough for a confirmatory claim

- **Selection.** The unit, the question and the arm contrast were all found in the data. Every value in §6.2 was computed after KC-5 was known.
- **Registration.** Nothing in §6.1 was registered. PR §10.6 forbids any threshold, set, operationalization, row or rule changing after a matrix cell exists, so no new E6 reading can acquire registered status.
- **Evidence weight.** Most control values in U* are deterministic characterizations (n_distinct 1 to 3), so the interaction's variation is essentially the treatment's. Thirty-two seeds bound GSB's resolution at 1/64.
- **Public seeds are no problem for re-analysis.** The cells were executed while the list was hidden. Seed publicity matters only for new execution (§11).

### 6.4 Post-hoc description against a new registered experiment

- **What a re-analysis of E6 can do.** It can describe the four conditions exactly, since the cells are deterministic counterfactuals. It can verify the mechanism. And it can decide whether a registered E7 is worth running.
- **What it cannot do.** It cannot confirm, generalize beyond the family, or change any E6 status.
- **The answer to question 3.** The interaction can be estimated descriptively, and exactly, for E6's cells. It cannot be estimated confirmatorily. So far the description is strongly positive for one post-hoc unit, and indeterminate over the common-neutral units, with the positive part confined to ADAPT's units. The all-unit description, I_all, waits for the audit.

---

## 7. Comparison of Candidate E7 Designs

| Design | Causal cleanliness | Can it be registered? | New evidence | Main risk | Assessment |
|---|---|---|---|---|---|
| **A. Re-analysis only** | Exact counterfactuals for E6's own cells | No: post hoc | None new. It verifies, describes and decides. | Mistaking description for confirmation | **Necessary first step. Not an experiment.** |
| **B. Dedicated 2×2 factorial** | The factors cross cleanly. E6's four Rulesets already are the four cells, so no new Ruleset is needed. | Yes, blind, with fresh seeds | A fresh-seed family-level replication | Retests E6 under a new label. E6's own analogue reads NEITHER (§6.2). | **Conditional only (§8.2)** |
| **C. Narrow PACED/ADAPT study** | Clean, but narrow | Only with hindsight selection built in | Little: the mechanism is already traced | Overfits to the discovered pathology; one unit is not a census | **Reject as a primary design** |
| **D. Scheduler/disruption timing intervention** | Changes timing and persistence together, and couples to the family's callback counting | Needs new Ruleset identities | A disruption dose–response, not an interaction test | More than one causal variable. It becomes an E3/E4-style scheduler study. | **Reject for E7** |
| **E. Exact cell-level decomposition, plus a lockout characterization** | Exact, for E6's cells; the lockout half is a Ruleset property | Not an experiment | Makes §4 durable and tested | None beyond A's | **Fold into A (§8.1)** |

### 7.1 Design A — re-analysis only

- **Causal cleanliness is high for what E6 contains.** Every cell key has four exact counterfactuals (§2.3).
- **The registration problem is fundamental.** Every quantity would be defined after the data were seen (§6.3). A re-analysis can support description and a decision, never a confirmatory claim.
- **It is enough to decide whether another experiment is justified.** It already bears on that decision: the family-level reading is indeterminate, and the unit-level reading is family-specific (§6.2).

### 7.2 Design B — a dedicated 2×2 factorial

- **Can the factors be crossed independently?** Yes. The four E6 Rulesets differ exactly on the two fields (§2.2). The couplings in §3.1 are the factors' own semantics.
- **Can E6's cells serve as frozen cells? No.** All four conditions must be rerun under one new identity, on one new seed list:
  - **Pairing.** Old controls mixed with new treatment cells would break the seed pairing.
  - **Determinism.** Running the E6 family and Rulesets on E6's seeds reproduces E6's cells byte for byte. The trace re-execution verified replay bytes for every E6 cell (implementation record §3.1). A "replication" on E6 seeds would be E6 again.
  - **Hindsight.** E6's cells generated the hypothesis.
- **Family.** Reuse it unchanged (§12).
- **Seeds.** New and blinded (§11).
- **Matrix size.** 4 conditions × (72 + 18) cells × *S* seeds = 360 *S*. At *S* = 32 that is 11,520, E6's own size.
- **Estimands.** Primary: I_all over all of E7's frozen units. Secondary: I_common_neutral, over the set fixed from E7's own controls before any treatment cell exists (§10.2).

### 7.3 Design C — a narrow PACED/ADAPT mechanism study

- **Not sufficient.** One unit is below E5's minimum of six inferential units. It cannot address the family-level question, and it was chosen because it fired.
- **Overfitting risk is high.** ADAPT is secondary evidence in E6, never a row or kill input (PR §6.7). A study built around its schedule would test the fixture more than the Ruleset.
- **Matched comparisons, if it were pursued.** The natural ones would be:
  - RUSH–ADAPT (pace), STEALTH–ADAPT (search mode) and LURK–ADAPT (no search);
  - PACED–GUARD (a stationary defender with no check) and PACED–EVADER (evades at once, with no check).

  All five already exist in E6, in all four conditions. They belong in the audit's tables (§8.1), not in a new study.
- **Sequencing.** It should follow a broader factorial, never precede it. Here neither is recommended now.
- **What would remain.** Its only new measurement would be the magnitude of a mechanism whose Ruleset half is a theorem (§4.3, S-4).

### 7.4 Design D — a scheduler or disruption-timing intervention

- **What it would test.** Varying λ (for example 1, 2 and 4), or when a hit takes effect, while holding sensing at 32, isolates disruption *duration*. It does not isolate the *interaction* unless it is also crossed with sensing.
- **More than one variable changes.** A new λ changes how many offers a victim loses. Through the family's callback counting (§3.1), it also changes PACED's pacing parity and ADAPT's check timing.
- **An equivalence, untested.** At Q = 8 with chunk 2, λ = 8 is equivalent to whole-tick disruption in eligibility and sensing, since suppression never runs past the end of the tick (`ruleset_policy.py:123–134`) [TRACE].
- **The result.** It would be a new E3-lineage scheduler study with new Ruleset identities, not an E7 interaction test.

### 7.5 Design E — something better, folded into A

Two additions make the re-analysis stronger than a unit-level interaction table:

1. **An exact cell-level decomposition.** For every cell key, record the four-tuple of seat results across the conditions, and classify each key by which factors change its outcome. That uses E6's determinism, which a unit-level DiD throws away.
2. **A lockout characterization with scripted, non-family agents.** Engine behavior tests assert callbacks and actions, and record no outcome: the Checkpoint A precedent (A1 §2).
   - Under both whole-tick Rulesets, a re-hit victim gets no callback in a tick its opponent moves first.
   - Under both λ = 1 Rulesets, a stationary victim re-hit once per tick keeps 7 of 8 offers.

   This turns §4.3 from a hand trace into a tested Ruleset characterization, with no gameplay outcome.

---

## 8. Recommended E7 Design, If Any

### 8.1 First: an E6 post-hoc factorial audit (**PA**), which is not an experiment

**Form.**
- **The record.** A committed record, for example `docs/research/v6/V6_E6_POST_HOC_FACTORIAL_AUDIT.md`.
- **The tooling.** It lives under its own directory, for example `tools/research/v6/e6_audit/`, never inside the frozen `tools/research/v6/e6/`.
- **No new matches.** It reads the frozen corpus and changes nothing in it.

**Contents**, fixed now, before its formal run:

| # | Item |
|---|---|
| PA-1 | **Integrity.** Every artifact read is checked against `pre_reveal_manifest.json` and `final_record.json`, and every seed against `seeds_revealed.txt`. |
| PA-2 | **Identity.** The multiplicity-aware seat metrics reproduce all 180 frozen (unit, condition) values of GSB and SDom. Synthetic tests with duplicated seeds pin the multiset handling. |
| PA-3 | **The exact cell-level decomposition** (§7.5). |
| PA-4 | **The estimands.** I_u for all 45 units, as the full per-unit table. **I_all** over all 45 units, computed here for the first time. **I_common_neutral**, L(*d*) and I_flag over U* (§6.1). |
| PA-5 | **Stability.** O-BOOT stabilities of each estimand; stab(PF-4 raised) per arm; the joint arm distribution; the per-unit crossing counts. |
| PA-6 | **Strata, fixed now.** Three strata, each applied to I_all and, where it applies, to I_common_neutral:<br>• units containing ADAPT against the rest (9 of the 45 contain ADAPT, and all 9 are in U*);<br>• pairings against mirrors;<br>• the three baseline strata of §6.1, which are defined from the controls alone. |
| PA-7 | **Mechanism tables** in the form of §4.5, for the named units: PACED–ADAPT, the ADAPT mirror, GREED–ADAPT, LURK–ADAPT and LURK–GREED, plus the five comparison units of §7.3. |
| PA-8 | **The lockout characterization** (§7.5), under all four E6 Rulesets. |
| PA-9 | **A scope statement.** No E6 registered value, flag, kill, row or disposition changes, and no E6 record is edited. Any pointer from E6-R is a dated addendum under the chronology convention. |

**Honesty about order.** This review has already computed exploratory versions of PA-4 to PA-7 (§6.2), except I_all. So PA is a verification and a durable record, not a blind test, and it must say so.

**Language.** Everything PA reports is post-hoc description. PA may say whether a stability meets the 9/10 convention. That bar is a research-program decision convention, reused from E6's O-4. PA never states a hypothesis verdict: no SUPPORTED, REFUTED or NEITHER, and no row. Every PA output also states that it changes zero E6 registered findings.

**The decision rule after PA** (adopted with revision by the research lead, §16):

**Load-bearing findings.** PA reproduces this review if all of the following hold:
1. The PACED–ADAPT outcome and mechanism counts of §4.2 and §4.5 are reproduced exactly. The corpus is deterministic, so exact equality is expected.
2. The arm contrast (PF-4 raised in the primary but not the companion) holds in fewer than 9/10 of resamples. The exploratory value is 177/1000.
3. I_common_neutral's positive stability is below 9/10. The exploratory value is 519/1000.
4. I_all's positive stability is below 9/10.

Reading 4 is not a reproduction, since this review did not compute I_all. It is committed here, before PA runs, as the reading that this review's family-level description ("no stable amplification") implies.

**The rule:**
- **If PA reproduces the load-bearing findings,** close this interaction question with no E7 experiment. PA records the descriptive answer: KC-5 was a unit-level interaction between priced sensing, whole-tick lockout and ADAPT's absolute-tick schedule, and the family shows no stable interaction.
- **If PA materially disagrees, STOP and reconcile the discrepancy** before deciding whether E7-F is justified. A material disagreement is either of:
  - any failure of PA-1 or PA-2;
  - any discrepancy that changes a load-bearing finding.

  The reconciliation establishes whether the cause is a scratch-script error in this review, an error in the audit tooling, or a genuinely different descriptive reading. Only then is E7-F reconsidered. A disagreement does not launch it.
- **Every other numeric difference** from a value in this review is reported and explained in the PA record.
- **The bar's position does not matter here.** Given the exploratory values for readings 2 and 3, the branch taken does not depend on where the bar sits anywhere from 3/5 to 9/10. For reading 4 the bar is fixed at 9/10 before I_all exists.

### 8.2 Conditional: E7-F, a confirmatory family-level factorial replication

**Deferred.** E7-F is reconsidered only if PA materially disagrees with this review, the disagreement is reconciled, and the research lead then judges a new experiment justified. OD-3 to OD-6 are deferred with it (§16).

- **Question**, a question and not a promise: *In the frozen E6 family under priced sensing, does whole-tick disruption produce more seat bias than one-offer disruption?*
- **Conditions.** Exactly E6's four Rulesets, unchanged. No engine change and no new Ruleset.
- **Population.** The E6 family unchanged: all 18 packages, the same fingerprints, both fields (§9, §12).
- **Seeds.** Fresh and blinded, under the full E6 protocol (§11). *S* = 32 was the proposed default. The count is deferred (§16, OD-4).
- **Matrix.** 11,520 cells. E6's executions took about 47 minutes for the controls and 45 for the treatments with fields in parallel (E6-R §A), so the whole run needs about two hours.
- **Primary estimand.** I_all over all of E7-F's frozen units, with the sign-and-stability status rule (§10.2).
- **Registered secondary quantities:**
  - I_common_neutral over U*_E7, and I_flag;
  - I_all within the baseline strata of §6.1;
  - PF-4 per arm, unchanged, for comparability with E6;
  - stab(PF-4) per arm;
  - I_all without ADAPT's units, a stratum pre-declared here;
  - PACED–ADAPT's signed interaction, as a named replication unit. It is hindsight-selected and never a row input.
- **Gates.** E6-D's clauses carry over: D-1, D-2, D-3, D-4, D-5, D-6, D-7. So do CQ-1 on both controls and the control-against-control reading. That reading places each control in its own treatment slot and must give I_all = I_common_neutral = 0 exactly.
- **Interpretation rows (sketch; nothing registered).** The inputs are (I_all, I_all without ADAPT's units), each SUPPORTED, REFUTED or NEITHER. The rows must cover all nine combinations, with NEITHER given its own rows and exhaustive, fail-closed mapping tests (the E4/E5 lesson). The candidate readings:

  | Pattern | Candidate reading |
  |---|---|
  | (SUPPORTED, SUPPORTED) | Whole-tick disruption amplifies priced sensing's seat bias in this family, beyond ADAPT's schedule |
  | (SUPPORTED, NEITHER or REFUTED) | The interaction is carried by ADAPT's units: a family dependence |
  | (REFUTED, any) | Whole-tick disruption does not increase priced sensing's seat bias in this family |
  | NEITHER | Its own explicit rows |
- **A known risk to record before registration.** E6's own analogue of the secondary measure reads NEITHER (519/1000, §6.2), so at *S* = 32 a NEITHER is a live outcome. **Decided (OD-7): a NEITHER on the primary closes the line.** A fresh confirmatory replication that returns NEITHER would not justify another iteration.
- **What E7-F could show:** a family-level interaction, or its absence, on seeds nobody has seen.
- **What it could not show:** generality beyond the family, or product acceptability.

### 8.3 Confirmatory or mechanistic? (question 6)

**Confirmatory, if there is an E7 at all.** The mechanism is already identified from E6's rows and from source (§4). A mechanistic E7 would decompose steps that E6's callback rows already expose. Its only new manipulations would be agent or scheduler changes, and those are excluded (§7.4, §12).

The mechanism enters E7-F only as a secondary descriptive analysis: the §4.5 tables, recomputed on fresh seeds. The two are not combined.

---

## 9. Population Recommendation (question 7)

**The full nine-member E6 family, both fields.** Any reduction is chosen with hindsight, and each one changes the eligible set U* that the estimand is defined over.

| Option | Verdict | Why |
|---|---|---|
| PACED and ADAPT only | Reject | One unit, selected because it fired, and below E5's six-unit minimum. It builds the positive answer into the population. |
| PACED, ADAPT and matched neighbors | Reject | The neighbors (§7.3) are already in the full family at no extra cost, and choosing them is still hindsight selection. It would also drop the non-ADAPT units that cross under resampling (LURK–GREED, STEALTH–GUARD) and the mirrors. |
| The full nine-member family | **Adopt** | The population KC-5 was registered on. It keeps U* comparable to E6's 26 units and lets the ADAPT stratum be pre-declared, not chosen. |
| The family without ADAPT | Reject | ADAPT carries the mechanism, so removing it builds a null in. It is also in the registered opponent set (PR §3.1). The ADAPT stratum is the honest form. |
| A reduced diagnostic family plus mirrors | Reject | Cost does not bind: the whole matrix runs in about two hours (§8.2). |
| Special scripted characterization agents | **Only for PA-8** | They characterize Ruleset mechanics in engine tests. They are never matrix members and never produce an outcome. |

- **Matched-agent discipline.** Every member keeps its registered parameters and opaque ID.
- **Independent evidential units.** The primary, I_all, uses all 45 frozen units, a set fixed by the matrix. The secondary, I_common_neutral, uses U*, which had 26 units in E6. E7-F's U* is fixed from its own controls before treatment. If |U*_E7| < 6, report I_common_neutral as not interpretable (the E5 census rule), without changing the primary.

---

## 10. Measurement and Interaction Estimand (questions 8 and 9)

### 10.1 Reuse the registered seat metrics unchanged

**Reused as registered** (E4 `pairing_seat_metrics` and `mirror_seat_metrics`, E5 PF-5 lineage):
- SDom and GSB for pairings, the mirror metrics seed by seed;
- neutrality as SDom < 9/10 and |GSB| ≤ 1/10;
- PF-4 itself.

That keeps E7-F directly comparable to E6.

**Four weaknesses the post-hoc audit exposed.** Under the three-layer reading rule, they are recorded against E6 as limitations, never fixed in it:

| # | Weakness | How E7-F handles it, with no new primary metric |
|---|---|---|
| (a) | PF-4 has no stability requirement | Register stab(PF-4) per arm as a secondary descriptor |
| (b) | PF-4 is a maximum over arm-specific eligible sets | Define the estimand over U*, the units eligible in both arms |
| (c) | GSB counts decisive matches only, so it is capped by the decisive share | Report every unit's decisive share beside its GSB in all four conditions. It is a disclosure, not a correction. |
| (d) | PF-4 cannot see seat bias in units whose control was already non-neutral | Report those units descriptively, as §4.7 does |

**No new primary seat metric.** E6's metric is sufficient for this question once the estimand is defined over a common set.

### 10.2 The estimand

**The unit** is the registered seat-metric unit:
- an F1 pairing, whose GSB is taken over 2*S* matches (*S* seeds, both orientations);
- an F2 mirror, over its *S* candidate-first cells.

It is not pairing × seed: GSB is defined over seeds, and per-seed seat results are binary. The family-level quantities are means over a unit set. Seeds are resampled jointly across the four conditions and all units (O-BOOT, 1000 draws, `random.Random(42)`).

**Primary, over the full frozen unit set:**

> I_all = (1/|U_all|) Σ_{u ∈ U_all} [ ( |G_u(1,0)| − |G_u(0,0)| ) − ( |G_u(1,1)| − |G_u(0,1)| ) ]

in the notation of §6.1. With E6's population, |U_all| = 45. Each unit's own control terms are subtracted, so no unit is excluded for a non-neutral control. The matrix fixes the unit set before any outcome exists.

**Secondary, the common-neutral form:** I_common_neutral is the same mean taken over U* only. The control terms are kept there too, because a unit in U* may have a non-zero |GSB| up to 1/10.

**Why the absolute value.** Seat bias has no preferred seat across units, and its sign varies from unit to unit. The floor at 0 is why I_all is also reported by baseline stratum (§6.1).

**Status in a future registered E7-F**, a structural reuse of E6's rule (PR §5.3, O-4):

| Status | Condition |
|---|---|
| SUPPORTED | I_all > 0 at the point estimate, and stab(I_all > 0) ≥ 9/10 |
| REFUTED | I_all ≤ 0 at the point estimate, and stab(I_all ≤ 0) ≥ 9/10 |
| NEITHER | Otherwise |

These status words belong to a registered experiment only. The post-hoc audit reports the same stabilities against the 9/10 decision convention, and never as a verdict (§8.1).

No magnitude threshold is set here (§16, OD-3).

**Secondary:**
- **I_common_neutral and I_flag = L(0) − L(1),** with the same status rule.
- **I_all without ADAPT's units, and I_all within each baseline stratum.**
- **PACED–ADAPT's signed interaction,** (G(1,0) − G(0,0)) − (G(1,1) − G(0,1)), whose direction E6 fixes in advance: positive, favoring Seat A under whole-tick disruption.

---

## 11. Seed and Blinding Plan (question 10)

**Fresh, blinded seeds for every E7 cell, under the full E6 protocol:**
- The family is already frozen and fingerprinted.
- Freeze E7's structural identity (`v6-e7-matrix-v1-…`) before any seed exists.
- Generate the seeds once, with `secrets.randbelow(2**53)`.
- Before the first control cell, commit only the SHA-256 commitment and the execution identity.
- Keep the list private and git-ignored during execution.
- Reveal after the treatment gates and the frozen analysis, and run D-6 before interpretation.
- Carry forward the E6 lesson: redact by seed value, not key name, because artifact paths embed seeds.

**The public E6 seeds are excluded from every E7 cell**, for three reasons:
1. **Rerun, not replication.** The engine and family are deterministic, so E6's seeds with E6's Rulesets and family reproduce E6's cells byte for byte.
2. **Hindsight.** The hypothesis came from those cells.
3. **Protocol.** They have been public since `0951fa3`, and the protocol requires a list that agents and fixture authors could not know.

The frozen family cannot read seeds (D-5), so seed publicity is not an in-match bypass *for this family*. Reasons 1 and 2 are the decisive ones. Reason 3 keeps the protocol whole and guards against any later fixture edit.

**Also rejected:** a subset of the E6 seeds, seeds derived from them, and a published master seed.

**Where E6's seeds do belong.** They stay the identity of E6's already-executed cells, and PA uses them only for that (§8.1).

---

## 12. Agent Reuse and Modification (question 11)

**No modification.** Use the E6 family unchanged: 18 packages, the fingerprints in `family_fingerprints.json`, and the D-5 gate.

- **What unchanged agents can answer:** E7-F's question, whether this family shows a family-level interaction.
- **What they cannot answer:** whether the interaction holds for defenders whose behavior does not depend on the absolute tick. Answering that would need a changed or new agent, for example ADAPT's check keyed to its own callback count instead of the tick. That change would be:
  - **agent tuning motivated by E6's outcome**, which is excluded here;
  - **a new family identity**, with new fingerprints and a new matrix;
  - **a break in comparability with E6.** ADAPT is in every member's opponent set, so every unit's values would change, not only ADAPT's own.

**So generality is out of E7's scope.** If the lead wants it, it is a separate design review, and a REDESIGN in this review's terms (§13, S-9).

---

## 13. STOP and REDESIGN Criteria (question 12)

| # | Criterion | Status now | Consequence |
|---|---|---|---|
| S-1 | **E6's apparent interaction disappears under exact re-analysis** | **Provisionally met at the family level** [POST-HOC]: the arm contrast is realized in 177/1000 resamples, and I_common_neutral is −3/1664, positive in 519/1000. I_all waits for PA. **Not met at the unit level**: PACED–ADAPT is positive in 1000/1000. | If PA reproduces the load-bearing findings, close the question with no E7 experiment. If it materially disagrees, STOP and reconcile (§8.1). |
| S-2 | **KC-5 is traceable to a fixture defect** | **Not met.** ADAPT and PACED behave as specified (P-4, O-6, A1 C-3). The artifact is specified behavior, a family dependence of the GAMEPLAY FINDING kind, not an implementation bug. | Record it; no fix, and no family change |
| S-3 | **The factors cannot be independently crossed** | **Not met** (§2.2) | — |
| S-4 | **The seat effect is a deterministic first-mover theorem requiring no experiment** | **Partly met.** The lockout half is a property of the Ruleset and of the attacker's once-per-tick re-hit (§4.3). Seat dependence then follows for any defender behavior keyed to the absolute tick. Only the magnitudes are empirical. | No unit-level E7 (Design C) |
| S-5 | **The population cannot provide independent evidential units** | **Met** by a PACED–ADAPT-only study (one unit). **Not met** by the full family (45 units; 26 in E6's U*). | If \|U*_E7\| < 6, the secondary I_common_neutral is not interpretable |
| S-6 | **The study would merely retest E6 with different labels** | **Met** by Design C. **Largely met** by Design B on the same family: its new elements are the registered estimand and the fresh seeds. | Design B only after a reconciled PA disagreement, and then only by the research lead's decision |
| S-7 | **Public seed reuse contaminates the hidden-information question** | **Met** by any design that reuses E6's seeds. That is a rerun (§11). | Fresh seeds are mandatory |
| S-8 | **A new intervention introduces more than one causal variable** | **Met** by the Design D variants (§7.4), and by any agent change (§12) | Reject D and agent changes for E7 |
| S-9 | *(added)* **The question cannot be separated from agent semantics** | **Met** for the generality question (§12) | REDESIGN, if the lead wants generality |
| S-10 | *(added)* **E7's hypothesis is already contradicted descriptively by E6** | **Provisionally met** at the family level (§6.2) | As S-1 |

---

## 14. Risks and Limitations

1. **The quantitative findings here are exploratory.** They come from unreviewed scratch scripts. The identity check (§1) reduces the risk, but does not remove it. PA exists to close that gap.
2. **Hindsight.** Every number here was computed after KC-5 was known. None can confirm anything, and none was used to set a threshold.
3. **Scope.** One family, one arena (512), one radius (32), two parents, 32 seeds.
4. **What the resampling stabilities reflect.** They treat seeds as the sampling unit. With most control values deterministic, they mostly reflect treatment variation.
5. **The PF-4 stabilities are hypothetical.** The registered PF-4 is a point flag, and KC-5 fired exactly as registered. Nothing here says the companion "really" had KC-5. The claim is only that its absence is not a stable property of the arm.
6. **The mechanism is inferred from rows and source.** PACED's per-tick write progress was not traced cell by cell (§4.5).
7. **Narrowing.** A line focused on PACED–ADAPT would quietly replace V6's broader requirement of meaningful opponent-dependent choices. E6 already met that requirement in both arms (`R-CREATES` and E6-H2, reproduced by the companion), and nothing here touches it.
8. **Rescue.** Reading "the companion lacked KC-5" as "priced sensing under λ = 1 is a candidate" is not supported. The companion raises PF-4 in 819/1000 resamples, and six of its units are non-neutral at the point estimate (§4.7). Its non-firing does not rescue the rejected candidate.

### 14.1 Product interpretation boundary (question 13)

- **The research question, which is E7's.** What caused E6's seat artifact? The descriptive answer, pending PA: a unit-level interaction mediated by ADAPT's absolute-tick schedule under whole-tick lockout. There is no stable interaction over the common-neutral units, and I_all waits for PA.
- **The product question.** How should Bytefray ultimately handle sensing and disruption? Not addressed here.
  - Nothing here supports changing stable gameplay.
  - The λ = 1 companion is not "cleaner" in any robust sense.
  - The promotion prerequisites stand: the product-level closure of seed inference (DR §E.2), and E6's REJECT.
- **Strategically successful against product-acceptable.** E6 established the first in both arms (`R-CREATES`, qualified by E6-H2). It rejected the second through KC-5. This review reopens neither.

---

## 15. Verdict

**RE-ANALYZE E6 FIRST — registration of E7 is premature.**

**Why not the other verdicts:**
- **Not NO NEW EXPERIMENT yet.** The corpus answers the historical causal question for KC-5 exactly, at the unit level. But the answer, and the finding that the arm contrast is unstable, rest on this review's exploratory scripts. The program's evidence standard requires a committed, independently verified record before a research line is closed on an audit finding. The all-unit measure I_all has not been computed at all yet. If PA reproduces the load-bearing findings, this question closes with no E7 experiment (§8.1).
- **Not GO WITH CONDITIONS.** The only E7 that adds evidence, E7-F, would test a hypothesis that E6's own description already fails to support. E6's own analogue of its common-neutral measure reads NEITHER.
- **Not REDESIGN.** The Ruleset-level question can be isolated: the factors cross cleanly. REDESIGN applies only to the generality question (S-9).
- **Not STOP.** The line still owes a durable descriptive record, and PA may yet contradict this review.

### 15.1 Direct answers

1. **Does E6 contain a valid 2×2 sensing × disruption contrast?** Structurally yes. Exactly two fields differ, the cells are exact counterfactuals, and the family and analyzer are identical. Inferentially no: it was not registered as a factorial (§3.1).
2. **Is KC-5 consistent with an interaction, or merely correlated with disruption duration?** For the unit that fired, it is an exact-counterfactual interaction: both factors are necessary, and it is mediated by ADAPT's absolute-tick schedule under whole-tick lockout (§4). Between the arms, "KC-5 fires in one, not the other" is mostly a threshold realization (177/1000), not a stable property of disruption duration (§6.2).
3. **Can the interaction be estimated credibly from the E6 corpus?** Descriptively, and exactly, yes. Confirmatorily, no (§6.3–§6.4).
4. **If a new experiment is needed, what is the smallest one that answers the question?** E7-F: the full E6 2×2 on fresh blinded seeds, with I_all as its registered primary estimand. That is 11,520 matches. No smaller design answers the question without building the answer into its population (§8.2, §9). It comes into consideration only if PA materially disagrees with this review, and then only after the disagreement is reconciled.
5. **The full E6 family or a diagnostic subset?** The full family, with ADAPT as a pre-declared stratum (§9).
6. **New blinded seeds?** Yes, mandatory. E6's seeds would reproduce E6 byte for byte (§11).
7. **What result would support "whole-tick disruption converts sensing timing into a seat artifact"?** In E7-F:
   - I_all SUPPORTED;
   - I_all without ADAPT's units also SUPPORTED, so the effect is not only ADAPT's schedule;
   - as secondary support, I_common_neutral SUPPORTED, and PF-4 raised under whole-tick but not under λ = 1 in at least 9/10 of resamples.

   "Timing" should be read as *which ticks the defender may act in after the first hit*. First detection is identical across the disruption regimes (§3.2).
8. **What would refute the interaction explanation?** Any of:
   - I_all REFUTED;
   - I_all SUPPORTED, but I_all without ADAPT's units REFUTED. The effect would then be ADAPT's (reading D), and a Ruleset interaction beyond ADAPT would be refuted in this family. With that stratum at NEITHER instead, the general interaction is not supported, though not refuted;
   - PF-4 raised in both arms at similar stability.
9. **What would make the whole E7 line not worth pursuing?** PA reproducing the load-bearing findings of §8.1: an unstable arm contrast, and neither I_common_neutral nor I_all reaching the 9/10 convention for a positive interaction. E7-F would then test a hypothesis the corpus already fails to support, and a unit-level E7 would only measure the magnitudes of a theorem. The same holds if the only route to generality needs agent modification (S-9), and it holds for E7-F returning NEITHER on its primary (OD-7).
10. **Does the design preserve E6's strategic finding without trying to rescue the rejected candidate?** Yes. No E6 status changes. `R-CREATES` with E6-H2 stands for both arms, and REJECT stands. Nothing here makes λ = 1 priced sensing a candidate (§14.1).

---

## 16. Decisions of the Research Lead (2026-09-29)

These were raised as open decisions in the first draft of this review. The research lead ruled on each before commit, and the rulings are recorded here.

| # | Decision | Ruling |
|---|---|---|
| OD-1 | Authorize PA as the next step, and fix its record name and tooling location | **AUTHORIZED**, after the two amendments in this revision: I_all, and the revised disagreement rule. Record `docs/research/v6/V6_E6_POST_HOC_FACTORIAL_AUDIT.md`; tooling `tools/research/v6/e6_audit/`. |
| OD-2 | The post-PA decision rule (§8.1), including the reuse of the 9/10 bar | **ADOPTED WITH REVISION.** Reproduction closes the interaction question with no E7 experiment. A material disagreement means STOP and reconcile, not an automatic E7-F. The 9/10 bar is a research-program decision convention, never a new hypothesis verdict. |
| OD-3 | If E7-F proceeds: a minimum magnitude for its primary | **DEFERRED.** No E7 registration exists. |
| OD-4 | If E7-F proceeds: the seed count | **DEFERRED** |
| OD-5 | PACED–ADAPT's signed replication as a named secondary | **DEFERRED.** Yes, if E7-F is ever justified. |
| OD-6 | stab(PF-4) per arm as a secondary descriptor | **DEFERRED.** Likely yes. |
| OD-7 | What a NEITHER on E7-F's primary means for the line | **DECIDED: close the line.** A fresh confirmatory replication that returns NEITHER would not justify another iteration. |
| OD-8 | Whether E6-R gets a pointer to PA | **A dated addendum pointer only.** E6 is never rewritten. |
| OD-9 | Whether the generality question (defenders not keyed to the absolute tick) opens as a separate design review | **Not now.** No V6 branch around modified defenders. |
| OD-10 | The λ = 1 last-mover lean and the paint-race seat sensitivity (LURK–GREED) | **Context only.** Tracked with the E3/E4 lineage if useful. They are not part of E7. |

**Also decided:**
- **I_all** (§6.1) is the primary family-level description in PA, and the primary estimand of any future E7-F. The U* measure is renamed **I_common_neutral** and kept as a secondary analysis in the PF-4 lineage. I_all is defined here and committed, and PA produces it. It is not computed in scratch first.
- **PA-8**, the scripted, non-family lockout characterization with no outcome assertions, is approved.
- **Sequencing:** commit this review; implement and run PA only; stop for the research lead's review. There is no E7 registration, no fresh seed and no new gameplay match.

---

## What This Review Does Not Claim

- **No new E6 result.** Every E6 registered verdict, flag, kill criterion, row and disposition stands as issued. No E6 file was edited, and no E6 cell was rerun.
- **No confirmatory claim.** Every interaction value here is post hoc and descriptive.
- **No claim that whole-tick disruption causes seat artifacts under priced sensing in general,** and none that λ = 1 removes them.
- **No claim of a fixture defect.** ADAPT and PACED behave as specified.
- **No claim beyond** the frozen family, arena 512, radius 32, the two parents and the 32 revealed seeds.
- **No product recommendation.**
- **No registration.** No threshold, population, estimand or row is registered here. The E7-F elements are proposals.

---

## Appendix C. Computations

All of these were run with the repository's `.venv` Python at `dfe8432`, read-only, from the session scratchpad. None is committed. PA would re-implement them as tested tooling (§8.1).

| # | What | Result used in |
|---|---|---|
| C-1 | SHA-256 of `e6_analysis.json`, `e6_interpretation.json` and `d6.json` | Equal to E6-R Appendix R (§1) |
| C-2 | Read the seat metrics of all 45 units in all four conditions from `e6_analysis.json`; neutrality counts | 26, 38, 30 and 39 neutral units, matching E6-R §F.4 (§4.7) |
| C-3 | The 64 PACED–ADAPT F1 cells in each condition, joined with the telemetry summaries | §4.2 |
| C-4 | The stored callback rows of those cells: detection ticks, callback counts per tick, ADAPT's index-1 check READs and their owners, and ADAPT's MOVEs | §4.5, §4.6 |
| C-5 | Pairing checks over all 2,880 keys: presence, seat geometry, seat assignment; first seer and first detection, T-E6 against T-E6L | §2.3, §3.2 |
| C-6 | A field-by-field comparison of the four Ruleset objects; searches for Ruleset-ID-keyed behavior, and for any use of the radius or disruption settings in the family policy | §2.2, §2.3 |
| C-7 | Multiplicity-aware seat metrics: the identity check against all 180 frozen values; O-BOOT stabilities of PF-4 per arm, the joint pattern, per-unit crossings, PACED–ADAPT's GSB and interaction | §6.2 |
| C-8 | The eligible sets per arm; U*; I_common_neutral and I_flag with stabilities, over U*, without ADAPT's units, and within them. I_all was not computed. | §6.2 |
| C-9 | The LURK–GREED outcome tally in all four conditions | §4.7 |
