# Bytefray V6 — E2–E6 Cross-Experiment Synthesis and E8 Design Constraints

**Status:** **Approved by the research lead on 2026-09-29** as the V6 gameplay-design boundary for E8, after one wording revision: §I.5 now separates research success from gameplay-candidate success. The research lead confirmed every grade in §D unchanged.
- **What it is.** A descriptive synthesis of E2 through E6, read with the E7 design review and post-hoc audit. It sets the gameplay-design boundary for E8.
- **What it is not.** It is not an experiment, a re-analysis or a pre-registration. It creates no experimental result. It chooses no mechanic, no parent Ruleset and no seat criterion, and it sets no threshold.
- **Wording.** Every registered verdict and interpretation is quoted as its own record states it.

**Branch:** `v6-research`. Written against `4e71b89` ("docs(v6): close sensing-disruption follow-up"), the boundary at which the E7 line closed and the documentation was synchronized with the research record.
**Date:** 2026-09-29
**Relationship to the E2–E5 synthesis:** `V6_E2_E6_CROSS_EXPERIMENT_SYNTHESIS.md` **supersedes §G's forward-looking conclusions** of [`V6_E2_E5_CROSS_EXPERIMENT_SYNTHESIS.md`](V6_E2_E5_CROSS_EXPERIMENT_SYNTHESIS.md), while leaving the earlier synthesis intact as the authoritative E2–E5 historical record. It does not supersede the E2–E5 factual synthesis (§J.1).
**Authority:**
- [`V6_E6_PRICED_SENSING_RESULTS.md`](V6_E6_PRICED_SENSING_RESULTS.md) (**E6-R**), including its 2026-09-29 addendum pointer
- [`V6_E6_PRICED_SENSING_PREREGISTRATION.md`](V6_E6_PRICED_SENSING_PREREGISTRATION.md) (**PR**) and [`V6_E6_AMENDMENT_1_FAMILY_CORRECTIONS.md`](V6_E6_AMENDMENT_1_FAMILY_CORRECTIONS.md) (**A1**)
- [`V6_E7_SENSING_DISRUPTION_INTERACTION_DESIGN_REVIEW.md`](V6_E7_SENSING_DISRUPTION_INTERACTION_DESIGN_REVIEW.md) (**E7-DR**) and [`V6_E6_POST_HOC_FACTORIAL_AUDIT.md`](V6_E6_POST_HOC_FACTORIAL_AUDIT.md) (**PA**), including the research lead's decision in PA §13
- [`V6_E2_E5_CROSS_EXPERIMENT_SYNTHESIS.md`](V6_E2_E5_CROSS_EXPERIMENT_SYNTHESIS.md) (**SYN**), for the E2–E5 facts and for requirements A–G

§A.2 lists every other source and the limited role it plays.

**Where V6 stands**, in the research lead's words (2026-09-29):

> **V6 gameplay research: end of Branch B proof-of-concept / beginning of synthesis and next-mechanic selection.**

**The question this document prepares**, in the research lead's words:

> **What is the next clean way to turn information into an opponent-dependent strategic resource, now that E6 proved that direction is worth pursuing?**

---

## A. Scope and Evidence Rules

### A.1 What this document does

It answers five questions:

1. What do E6, the E7 design review and the post-hoc audit add to the E2–E5 record (§B, §C)?
2. How does E6 stand against the seven requirements of SYN §G (§D)?
3. Which E6 liabilities remain unresolved (§E)?
4. What must E8 preserve or avoid, and where does each constraint come from (§F)?
5. What must the E8 design review decide, what does it inherit, and which mechanic families does it compare (§G–§I)?

It does **not**:

- run, register or pre-register an experiment;
- re-analyze any corpus, or read any replay, telemetry file or analysis output;
- create, change or promote a Ruleset;
- choose E8's mechanic, its parent Ruleset, its seat criterion or any threshold;
- change any E2–E6 verdict, interpretation, disposition or record.

### A.2 Sources and the role each plays

| Source | Role here |
|---|---|
| E6-R, and the E2–E5 results records as SYN synthesizes them | **Authoritative.** Every verdict, interpretation, disposition and number. |
| PR and A1 | E6's registered question, conditions, family, flags and kill criteria, and the family's pre-freeze corrections |
| E7-DR and PA | **Authoritative for the post-hoc reading of KC-5 and for the closure of the E7 line** (PA §13). Every value in them is post-hoc description. |
| SYN | The E2–E5 facts, as synthesized there, and requirements A–G (§G), quoted in §D |
| [SR](V6_BRANCH_B_ACTION_CHOICE_SCOPE_REVIEW.md) (the Branch B scope review) and [DR](V6_PRICED_SENSING_DESIGN_REVIEW.md) (the priced-sensing design review) | **Framing only:** what Branch B asked and why; the candidate families, constraints K1–K8 and the bypass audit. Their predictions are priors, never results. |
| Engine source at `4e71b89` | [SOURCE] facts about current semantics, cited by file and line. Used only in §I. |
| The Phase 4A methodology and its 2026-09-22 Research Integrity Addendum; the Phase 4B–4D studies | **Background only**, described as the addendum governs (§C.4). Never evidence for E8. |

### A.3 Rules followed

- **SYN §A.3's rules are carried over unchanged.** Every number is copied from a committed record and cited, and nothing was recomputed. No metric, test, threshold or interpretation row is introduced. Statuses keep their record's own words. Evidence labels are inherited: a value resting on fewer than 8 distinct trajectories is a characterization, never a rate. Later evidence never rewrites an earlier conclusion.
- **Evidence tiers, as in SR.** [DOC] is a committed record. [SOURCE] is current source. [INFERENCE] is reasoning from those two. Every statement that a mechanic *would* do something is [INFERENCE].
- **Registered wording is kept.** Where a record says "supports", this document says "supports".
- **The research lead's decisions and framings are quoted and attributed**, not paraphrased into findings.

### A.4 The grading vocabulary (§D)

Grades are synthesis readings. They are not registered statuses, and they are not scores.

| Grade | Meaning |
|---|---|
| **DEMONSTRATED** | E6's records establish the requirement as written, within E6's scope (§D.0). |
| **PARTIAL** | E6's records establish part of the requirement, and a named part is not established or is qualified by a recorded liability. |
| **NOT ESTABLISHED** | E6 bore on the requirement, but its records do not establish it. |
| **NOT TESTED** | E6 did not measure the requirement at all. |

The grades separate **"E6 demonstrated something"** from **"E6 demonstrated the whole requirement"**. Each row in §D says which parts fall on which side.

---

## B. Executive Synthesis

**E2–E5 closed the forensic line on the stable-V4 forced capture. E6 then produced V6's first positive strategic result. Under priced sensing, the best fixed allocation of actions depends on the opponent, and spending less on information can win. The exact E6 candidate is rejected, because KC-5 fires. The E7 design review and audit showed that KC-5 was a unit-level interaction, not a family-level sensing × disruption problem, and the line closed with no experiment.**

| Step | Record | What it established | What it left |
|---|---|---|---|
| **E2–E5** | SYN | Four single-field interventions on capture, disruption duration, pass order and spawn placement. Each cut a real link, and none was the whole explanation. `R-H2-PRIME` supports the second response in the opening exchange as the remaining mechanism. | A forensic line closed by its own records. No intervention gave an agent a new decision (SYN §B). |
| **E6** | E6-R | **`R-CREATES`, qualified by E6-H2 SUPPORTED:** an opponent-dependent choice of how to allocate actions, and an information/action tradeoff, not a discovery tax. | **REJECT as a gameplay candidate**, because KC-5 fires, on one unit (PACED–ADAPT). |
| **E7** | E7-DR, PA | KC-5 was a real unit-level interaction among priced sensing, whole-tick lockout and ADAPT's absolute-tick damage-check schedule. It was not evidence of a stable family-level sensing × disruption interaction. I_all = −31/720, positive in 1/1000 resamples. | Closed at design review and audit, with no experiment executed. **E8 is the next experiment number.** |

**Five readings.** These are synthesis readings, not registered findings.

1. **The program moved from forensics to choice.** Every E2–E5 treatment changed *when* or *where* an existing action takes effect (SYN §F.3). E6 was the first to put a price on something an agent could choose to buy: finding the opponent.
2. **E6 establishes opponent-dependent policy value in one frozen nine-member family at A = 512, d = 32** (§D.1). It does not establish within-match adaptation, so **requirement C remains open** (§D.3).
3. **Seat bias is not a general E6 failure.** Priced sensing increased seat neutrality overall, from 26 to 38 of 45 units, while producing one registered KC-5 unit (E6-R §D.2, §F.4).
4. **E6's unresolved liabilities are specific** (§E):
   - 29.7% of T-E6 F1 cells in which neither entrant ever detects the other;
   - EVADER's 83.4% tick-limit rate;
   - seed-based placement inference, which remains a product-level bypass.
5. **The next design should keep the information/action opportunity cost and change the mechanism that turns information into gameplay.** It does not start from "how do we fix E6?" (§I).

---

## C. The Record Since the E2–E5 Synthesis

### C.1 Lineage

| Date | Record | Role |
|---|---|---|
| 2026-09-25 | SYN | Closed E2–E5, set requirements A–G, and named Branches A and B |
| 2026-09-25 | SR | Selected priced sensing (variant I-a) for Branch B's first mechanic. Held contestable valuable cells in reserve. Rejected banking and deployment as first mechanics. Kept Branch A open. |
| 2026-09-25 | DR | The design and adversarial review. Found one zero-action bypass, seed inference, and closed it by methodology (DR §E.2). |
| 2026-09-25 | PR; A1 | E6 registered; three pre-freeze corrections to the family's implementation |
| 2026-09-29 | E6-R | E6 executed, gated, revealed and interpreted |
| 2026-09-29 | E7-DR | Verdict RE-ANALYZE E6 FIRST. I_all defined, not computed. The audit (PA) authorized. |
| 2026-09-29 | PA | REPRODUCED. The research lead's decision: **NO NEW EXPERIMENT** (PA §13). |

### C.2 E6 — Priced Sensing

**Design** [DOC]:
- **Treatment.** One field, `RulesetPolicy.detection_radius`, from `None` to 32. A friendly process whose declared reach is *r* sees an enemy anchor if and only if their circular distance is ≤ min(*r*, 32) (PR §2).
- **What is priced.** Sensing stays passive and free. Search is priced through movement, and reading is the alternative channel (PR §1).
- **Fixed in every condition:** arena 512, tick limit 1000, Q = 8, chunk 2, rotation, K = 1, seeded placement, `core_base` spawn and forward pass order (PR §2).
- **Conditions.** The primary arm is C-E6 (`research-scale`, whole-tick disruption) → T-E6. The companion arm is C-E6L (`research-disruption-slot1`, λ = 1) → T-E6L, and it is never a verdict (PR §6.8). The matrix has 11,520 matches.
- **Population.** Nine members: RUSH, PACED, SPLIT, STEALTH, LURK, GUARD, EVADER, GREED and ADAPT. The candidate set Π_F excludes ADAPT, which is secondary evidence and never a row or kill input (PR §3.1, §6.7).

**The four layers** (E6-R):

1. **Registered verdicts.** E6-D PASS, D-6 included. E6-H1T SUPPORTED (1000/1000). E6-H1C REFUTED (SPLIT universal under the parent, stability 1). E6-H2 SUPPORTED. E6-H0 NEITHER (A = 769/1152 ≈ 0.668). E6-H3 REFUTED. PF-4 raised; PF-1, PF-2 and PF-3 not raised. KC-5 fires; KC-1 to KC-4 do not.
2. **Registered interpretation: `R-CREATES`**, verbatim: *"Under the parent, one fixed policy is a best response to every opponent. Under priced sensing, none is: priced sensing creates an opponent-dependent choice of how to allocate actions."* Its E6-H2 qualifier: *"and spending less on information beats spending more against at least one opponent: an information/action tradeoff, not a discovery tax"*.
3. **Descriptive findings.**
   - SPLIT is universal in 0 of 1000 resamples under T-E6. PACED is in 7 of the 9 BR_ε sets (§E.1).
   - 766 of 2,304 paired F1 cells change outcome class (§E.3).
   - Seat-neutral units rise from 26 to 38 of 45 (§F.4).
   - In 29.7% of F1 cells neither entrant ever detects the other (§F.1). EVADER reaches the tick limit in 83.4% of its F1 cells (§F.3).
4. **Disposition.** **REJECT as a gameplay candidate** (KC-5). In the research lead's reading, E6 is *"strategically successful, product-unsuitable in its current form"* (E6-R §H). Both E6 Rulesets remain research-only.

**The companion reading is "differs".** The registered comparison set differs only in *"KC-5: fires (primary) vs does not fire (companion)"*. The companion reproduces E6-H1T, E6-H1C, E6-H2 and E6-H3 (E6-R §D.5).

### C.3 E7 — design review and post-hoc audit, with no experiment

- **The question** (E7-DR). Was KC-5 caused by priced sensing, by whole-tick disruption, or by their interaction?
- **The design review's finding.** E6 is structurally a complete 2×2, but it was not registered as a factorial, so every interaction value computed from it is post hoc (E7-DR §3.1). Its verdict was RE-ANALYZE E6 FIRST.
- **The audit.**
  - It reproduced the review: 0 of 66 values differ, and all four load-bearing findings hold (PA §9, §10).
  - I_all, computed for the first time, is −31/720, and it is positive in 1/1000 resamples. Its sign comes from a floor effect in four attacker–EVADER units. The other strata sit near zero (PA §5.1).
  - I_common_neutral is −3/1664, positive in 519/1000 (PA §5.2).
- **The research lead's decision (PA §13): NO NEW EXPERIMENT.** The durable causal reading, in the research lead's words:

  > E6's KC-5 was a real unit-level interaction involving priced sensing, whole-tick lockout, and ADAPT's absolute-tick damage-check schedule. It was not evidence of a stable family-level sensing × disruption interaction.

- **Lockout is necessary, not sufficient.** GUARD is locked out under T-E6 just as ADAPT is, yet PACED–GUARD stays seat-neutral (PA §7.2).
- **E6 stands as registered.** The audit explains the pathology; it does not retroactively rescue the candidate (PA §13).
- **Chronology.** E7 is closed at design review and audit, with no experiment executed. No E7 registration, matrix, seed or gameplay match exists. The next registered gameplay experiment, if V6 needs one, is E8. The E7 number is not reused for a different question (PA §13).

### C.4 What E2–E5 contributes, and what stays background

**From SYN, unchanged:**

- **E2** (capture hold K = 2). The canonical forced line broke (H1 Supported), and control passed to each tick's first mover. Pairing-level seat determination was unchanged in 45 of 45 pairings (SYN §B).
- **E3** (λ = 1). Whole-tick denial is load-bearing for first-mover exclusivity and for much of the seat determination (D4 REFUTED, D2 SUPPORTED). A moderate, last-mover-leaning order dependence remains (D1 and D8 NEITHER) (SYN §B, §D.1).
- **E4** (mirrored later passes). **Substantial within-match behavioral change, with no F1 outcome-class change across 2,304 cells** (SYN §B, pattern 1, and §F.1; E4-R §F.5). The second mover's privilege in opening-pass contests survives (H3 SUPPORTED, 13 of 14).
- **E5** (spawn anchor off core cell 0). Co-location is not necessary for the sweep-backed privilege in 13 of 17 contests (E5-H2 SUPPORTED; `R-H2-PRIME`). PF-2 and PF-3 were raised, and `before_core` is not recommended for promotion (SYN §B, §F.1).

**Carried forward:** the forensic line stays closed, and no new scheduler, anchor or capture forensic experiment follows (SYN §J).

**Background only: Phases 4B–4D.** As SYN §D.2 records them:
- the aggregate competitive hierarchy stayed scale-robust under larger arenas (4B);
- movement-stride normalization was inert for the frozen agents (4C);
- proportional movement induced sublattice tunneling, with 49.6% of matches never making contact at arena size 65,536 (4D).

The 2026-09-22 Research Integrity Addendum closed that line as *"grounded in flawed causal premises and compromised by test and benchmark defects"* (SYN §D.2). **These studies are not evidence for E8, and no constraint in this document rests on them.**

---

## D. E6 Graded Against Requirements A–G

Each requirement is quoted from SYN §G, with its "would not satisfy" or implication clause where SYN gives one. No requirement is added, removed or reworded.

### D.0 The scope of every grade

- **The family.** One frozen nine-member family of scripted policies. One member, ADAPT, adapts, and it is secondary evidence.
- **The parameters.** A = 512, d = 32, K = 1, Q = 8, forward order and 32 seeds. There are two parents: whole-tick disruption and λ = 1.
- **The evidence weight.** Most control-table entries rest on 2 to 7 distinct trajectories. SPLIT's control universality is therefore a deterministic characterization of this family under the parents, not a rate (E6-R §I.2).

A DEMONSTRATED grade means demonstrated within this scope, and nothing wider.

### D.1 (A) Create opponent-dependent action value

> "The value of an action should depend materially on what the opponent is doing, so that the best policy against one opponent is not the best against every other." (SYN §G.1)

- **What E6 established** [DOC]:
  - E6-H1T is SUPPORTED: no fixed member is a best response to every opponent under T-E6, in 1000 of 1000 resamples.
  - E6-H1C is REFUTED: SPLIT is universal under the parent.
  - Together they fire `R-CREATES`. The companion reproduces both (E6-R §D.5).
  - Nothing replaces SPLIT as a single answer. Against searching attackers a searcher is best, and against passive, defensive and adaptive opponents SPLIT stays best (E6-R §E.1).
- **What it did not establish:** anything beyond §D.0's scope.
- **Grade: DEMONSTRATED**, in scope: opponent-dependent policy value among fixed allocations.

### D.2 (B) Create a real opportunity cost

> "An agent should have to choose among competing uses of limited actions, for example attack, defense or repair, information or scouting, and investment or expansion. Doing one should genuinely delay or weaken another." (SYN §G.2)

- **What E6 established** [DOC]:
  - E6-H2 is SUPPORTED, and the registered qualifier reads: *"and spending less on information beats spending more against at least one opponent: an information/action tradeoff, not a discovery tax"*.
  - The two witnesses are LURK − RUSH against EVADER (57/128, stability 1) and PACED − RUSH in the head-to-head (5/32, 951/1000 each) (E6-R §D.4). The companion reproduces E6-H2.
- **Qualifications the records themselves carry:**
  - **PACED differs from RUSH in more than information.** It also differs in *when* it acquires information, which changes who sees first, so a PACED win "cannot be read purely as 'less information won'". LURK was added for that reason (PR §0, O-2).
  - **The LURK witness sits in a stalling-heavy matchup.** It is against EVADER, whose matches mostly end at the tick limit (E6-R §E.2, §F.3).
  - **The price is paid through movement and reading.** Search is priced through movement (PR §1), and SPLIT's sensor made every one of SPLIT's MOVEs (E6-R §F.2). In E6's design, the measured cost cannot be separated from locomotion.
- **Grade: DEMONSTRATED**, in scope, as registered. In the research lead's words:

  > **B — DEMONSTRATED:** E6 establishes, within its frozen family and experimental scope, that spending less on information can outperform spending more against some opponents, demonstrating a selectable information/action opportunity cost. This does not establish that the cost is independent of movement.

  - The qualifications bound what kind of cost was shown. They do not change the registered status.
  - Independence from movement is not part of requirement B, and it is not imported as a criterion after the fact. It is carried as a family rationale (§I.3).

### D.3 (C) Permit adaptation

> "A capable agent should be able to observe enough, directly or by spending actions, to change its policy according to the opponent or the game state. Imposed inefficiency is not strategic decision-making." Implication: "A mechanic whose value lies in a choice can only be shown by agents that make the choice." (SYN §G.3)

- **What E6 did** [DOC]:
  - It made observation purchasable by action, through search MOVEs and the READ channel (PR §1).
  - It included one adaptive member, ADAPT, registered as secondary evidence (PR §5.3, §6.7).
- **The ADAPT reading** (E6-R §D.4; secondary and descriptive):
  - Under T-E6, u(ADAPT, *j*) − u(*j*, ADAPT) is positive against GUARD (+1), EVADER (+61/64), GREED (+55/64) and LURK (+25/32).
  - It is negative against SPLIT (−1), STEALTH (−27/32), PACED (−13/16) and RUSH (−45/64).
  - Added to the candidate set, ADAPT enters BR_ε only for GUARD and EVADER. Under C-E6 it is in no BR_ε set.
- **What was not established: that adapting within a match pays.**
  - No registered hypothesis tests it. PR §5.3: *"Primary evidence of a choice is E6-H1T together with E6-H2. ADAPT is secondary evidence."*
  - E6's registered choice is between fixed allocations. It is the choice of which policy to field, not a choice made during the match.
  - SR §F's signature, that the adaptive agent does at least as well as every fixed θ against the mixed field, was not registered.
- **A related finding.** ADAPT's own absolute-tick damage check is the schedule through which KC-5 ran (E7-DR §4.4; PA §7.1).
- **Grade: NOT ESTABLISHED.** In the research lead's words:

  > **C — NOT ESTABLISHED:** E6 does not establish that an agent can observe the opponent and adapt its allocation during the match.

  B establishes that different allocations have opponent-dependent value. C asks whether a capable agent can discover and exploit that fact dynamically. Requirement C remains open (§G.3).

### D.4 (D) Preserve interaction

> "The mechanic should not reach 'balance' mainly by eliminating contact, creating immunity or pushing matches toward the tick limit." (SYN §G.4)

- **What the registered flags show** [DOC]:
  - PF-1 is not raised: the tick-limit share went from 0.225 to 0.278, a rise of 0.053.
  - PF-2 is not raised: matches with no hostile core contact went from 0 to 0.036.
  - PF-3 is not raised, and KC-3 does not fire (E6-R §D.2, §D.3).
  - Capture still decides most F1 matches: 0.775 under C-E6 and 0.722 under T-E6 (E6-R §E.3).
- **The descriptive liabilities** (§E):
  - In 684 of 2,304 T-E6 F1 cells (29.7%), neither entrant ever detects the other. The count is the same under T-E6L (E6-R §F.1).
  - EVADER's matches reach the tick limit in 83.4% of its F1 cells, up from 63.9% under C-E6. Under the companion, stalling concentrates on the defenders, with GUARD at 89.6% and EVADER at 98.8% (E6-R §F.3).
- **Detection is not contact.** The 29.7% is visibility detection (O-DETECT, descriptive only). Hostile core contact (O-CONTACT, the basis of PF-2) was absent in only 3.6% of cells. Contact continues without visibility: STEALTH, for example, locates cores by READ (E6-R §F.1).
- **Grade: PARTIAL.** The registered interaction flags are not raised. The no-detection share and EVADER's stalling are unresolved.

### D.5 (E) Affect strategic topology, not merely termination timing

> "Prefer changes that alter matchup relationships and counterplay, meaning who beats whom and why, over changes that turn captures into score wins, or wins into ties, while the same winner remains." (SYN §G.5)

- **What E6 established** [DOC]:
  - The best-response map goes from one universal member to none (E6-H1T with E6-H1C; `R-CREATES`).
  - New head-to-head relations appear. PACED beats RUSH, 21/32, and "RUSH, then PACED, is best against SPLIT and STEALTH" (E6-R §D.4, §E.1).
  - 766 of 2,304 paired F1 cells change outcome class (E6-R §E.3).
- **A qualification.** E6-H0 is NEITHER: its A lands 2 cells above the refutation bound (E6-R §E.3). The row's "not a discovery tax" comes from its E6-H2 qualifier, not from E6-H0 (PR §7).
- **Grade: DEMONSTRATED**, in scope: who beats whom changed.

### D.6 (F) Remain explainable

> "The mechanic should remain comprehensible enough that agent authors can reason about it, the Designer can expose it, replay visualization can make it visible, and research tooling can measure it." Would not satisfy: "Effects visible only to a bespoke analyzer, or state that replays do not record." (SYN §G.6)

- **What E6 established** [DOC]:
  - The rule is one sentence: "you see enemy processes within *d* cells of your own" (SR §D.1).
  - The observation's shape did not change (PR §2).
  - The spectator pipeline already derives detection events from traced observations (SR §D.1).
- **What it did not establish:**
  - **The replay cannot show visibility.** Per-callback visibility, and the order in which two entrants first see each other, cannot be reconstructed from the replay, because process snapshots are recorded only at tick boundaries (DR §C.4). E6 therefore needed callback-level traces for every control and treatment cell (PR §6.6).
  - **KC-5's mechanism needed bespoke tooling.** It became visible only through a post-hoc cell decomposition and mechanism tables built for the audit (PA §4, §7).
- **Grade: PARTIAL.**

### D.7 (G) Be independently testable

> "Introduce one new strategic dimension at a time, with clean control and treatment semantics, controls that reproduce their parent byte for byte, and no simultaneous redesign of the engine." And: "Where a new mechanic interacts with an existing variable such as K, a companion arm or a registered masking limitation is needed (E4-H4)." (SYN §G.7)

- **What E6 established** [DOC]:
  - One field changed. The parent byte-identity goldens reproduce with `detection_radius = None` (D-3), and the controls run the unmodified parents (PR §5.1).
  - Search is inert under each control (CQ-1), and the control-against-control reading passed (PR §5.2, §10.3). E6-D passed.
  - A companion arm existed, as SYN §G.7 asks.
  - Engine-level behavior tests found two family implementation defects before any seed existed (A1 §2).
- **A qualification.** The companion was registered only as a status comparison. The sensing × disruption interaction it pointed to could therefore be estimated only descriptively and post hoc (E7-DR §3.1).
- **Grade: DEMONSTRATED** for the treatment's isolation. The companion's limit is a lesson (§H, item 2), not a failure of G.

### D.8 Summary

| | Grade | What E6 demonstrated | What it did not |
|---|---|---|---|
| **A** | DEMONSTRATED | Opponent-dependent value among fixed allocations | Anything beyond §D.0's scope |
| **B** | DEMONSTRATED | An information/action tradeoff (E6-H2), in two registered witnesses | A cost separable from locomotion (not part of B) |
| **C** | **NOT ESTABLISHED** | Purchasable observation; one secondary adaptive member | That adapting within a match pays |
| **D** | PARTIAL | PF-1 to PF-3 not raised; KC-3 does not fire | The no-detection share; EVADER's stalling |
| **E** | DEMONSTRATED | A changed best-response map; 766 of 2,304 outcome-class changes | — (E6-H0 is NEITHER) |
| **F** | PARTIAL | A one-sentence rule; derivable detection events | Visibility in the replay; KC-5 visible only post hoc |
| **G** | DEMONSTRATED | One field; parent identity; qualified controls; E6-D PASS | A registered interaction estimand |

No requirement is NOT TESTED.

---

## E. E6's Unresolved Liabilities

The registered disposition, **REJECT as a gameplay candidate**, stands. These are the liabilities E6's records name, and the E8 design review must address each:

| # | Liability | Evidence | Status |
|---|---|---|---|
| **L-1** | **No-detection cells.** In 684 of 2,304 T-E6 F1 cells (29.7%), neither entrant ever detects the other. The count is the same under T-E6L. | E6-R §F.1 | Descriptive. It is distinct from PF-2 (3.6%, not raised). |
| **L-2** | **EVADER's stalling.** It reaches the tick limit in 83.4% of its F1 cells (63.9% under C-E6), and in 98.8% under the companion. | E6-R §F.3 | Descriptive. PF-1 is not raised field-wide. |
| **L-3** | **Seed-based placement inference.** A zero-action bypass: the enemy core base, exactly, for zero actions. E6 closed it only experimentally, by the seed-set blindness protocol and gates D-4 and D-5. A product-level closure is *"a promotion prerequisite, not a research blocker"*. | DR §E.1–§E.2; PR §5.1, §9; E6-R §I.5 | Open at product level |
| **L-4** | **KC-5, the registered liability.** PACED–ADAPT's GSB is 0 under C-E6 and 1/8 under T-E6. Under λ = 1 it is 0 under C-E6L and −1/64 under T-E6L. | E6-R §D.2; PA §7.1 | REJECT stands. Explained, not rescued (PA §13). |

**Seat bias as a whole is not a liability.** Priced sensing moved 13 units into neutrality and exactly one out of it (E6-R §F.4).

---

## F. E8 Invariants

These are **design constraints**, not hypotheses, thresholds or a pre-registration. Each is derived from one or more of requirements A–G plus a named research finding. The E8 design review should show how its candidate meets each one, or argue why it need not.

### F.1 E8-I1 — Preserve opponent-dependent information allocation

> **E8's mechanic must preserve an opponent-dependent allocation between acquiring information and acting on it.**

- **Derived from** A and B.
- **Finding.** `R-CREATES`, qualified by E6-H2 SUPPORTED, in both arms (E6-R §D.1, §D.5).
- **Does not require** reproducing E6's best-response map or its two witnesses, or using a detection radius.

### F.2 E8-I2 — No search race

> **A candidate must not collapse into a deterministic search race.**

- **Derived from** A.
- **Findings.**
  - The scope review names this failure: "If each side's best search policy is the same whatever the opponent does, the choice collapses into a geometry-and-seat race" (SR §D.1, failure mode 1).
  - E6 registered it as KC-1's search-race label (PR §8). KC-1 did not fire, because E6-H1T is SUPPORTED (E6-R §D.3).
- **Inherited unchanged.**

### F.3 E8-I3 — Contact

> **Contact must remain sufficiently likely that strategic choice is exercised.**

- **Derived from** D, and from C's implication that a choice can only be shown by agents that make it (SYN §G.3).
- **Findings:** L-1 and L-2, while PF-2 is not raised (§D.4).
- **What the E8 review must define.** It must say which contact the invariant means. E6 recorded visibility detection (O-DETECT, descriptive) and hostile core contact (O-CONTACT, PF-2) separately, and they differ widely: 29.7% against 3.6%. No threshold is set here.

### F.4 E8-I4 — Seat neutrality without excluding tick-keyed agents

> **Seat neutrality must not depend on excluding agents whose behavior is keyed to absolute tick or scheduler phase.**

- **Consequence.** E8's family deliberately retains at least one **tick- or callback-phase-sensitive stress member**, because E7 showed suppression interacting with policies that count their own callbacks, as well as with absolute ticks. In the research lead's words: *"Removing ADAPT-like behavior would make the next family easier rather than the mechanic more robust."*
- **Derived from:**
  - **D.** Seat artifacts are among the pathologies recorded whatever else holds (SYN §G.4).
  - **G.** The costliest E2–E5 problems were confounds inside the instrument, including fixtures whose targeting encoded the very variable under test (SYN §G.7). [INFERENCE] A family chosen so that the mechanic cannot meet its known failure is the mirror image of that confound.
- **Findings:**
  - **The family counts its own callbacks.** PACED moves on odd callback indexes, ADAPT checks its core at callback index 1 of each tick, and a lost offer changes those counts (E7-DR §3.1, coupling 2).
  - **ADAPT's schedule is keyed to the absolute tick** (E7-DR §4.4).
  - **The mechanism reproduced cell for cell.** PACED–GUARD shows that lockout without a tick-keyed defender reaction produced no seat bias (PA §7).
- **What it replaces.** The research lead's draft invariant "avoid strong seat coupling" is carried by this invariant and by the seat-criterion decision (§G.2). E6 increased seat neutrality overall (§B, reading 3).

### F.5 E8-I5 — Product-level closure of seed reconstruction

> **Any product candidate involving hidden placement must close zero-action seed reconstruction at the product level.**

- **Derived from** B, and through B from A. [INFERENCE] If the opponent's location can be reconstructed for zero actions, information has no price for an agent that reconstructs it. The tradeoff then exists only for agents that do not.
- **Findings:** L-3 (DR §E.2; PR §9; E6-R §I.5).
- **Scope.** A research experiment may keep closing the channel by methodology, as E6 did. The invariant binds a **product candidate**.

### F.6 Summary

| Invariant | Requirements | Main finding |
|---|---|---|
| E8-I1 Opponent-dependent information allocation | A, B | `R-CREATES` with E6-H2 SUPPORTED, in both arms |
| E8-I2 No deterministic search race | A | SR failure mode 1; KC-1 did not fire |
| E8-I3 Contact sufficiently likely | D (and C) | L-1, L-2; detection is not contact |
| E8-I4 No exclusion of tick-keyed agents; a stress member kept | D, G | E7-DR §3.1, §4.4; PA §7 |
| E8-I5 Product-level closure of seed reconstruction | B (and A) | L-3; DR §E.2 |

---

## G. Decisions the E8 Design Review Must Make

**None of these is decided here.** Each is stated with the evidence the E8 design review inherits.

### G.1 The disruption parent

The E8 design review makes this decision explicitly, with the evidence on both sides. It is not inherited by default.

| | Whole-tick parent (`bytefray-rules-6-research-scale`) | λ = 1 parent (`bytefray-rules-6-research-disruption-slot1`) |
|---|---|---|
| **Distance from stable** | The stable-equivalent research control. An E8 treatment on it is one field from stable (SR §B.3, S5; SR §G.2, decision 3). | Itself an unpromoted research Ruleset, so an E8 treatment on it is two fields from stable (SR §B.3, S5; compare SR §D.2, objection 2). |
| **What E2–E5 recorded** | It was historically load-bearing for first-mover and tick control. Once immediate fatality was removed, control of each tick passed to its first mover (E2; SYN §B). Whole-tick denial is load-bearing for first-mover exclusivity and for much of the seat determination (E3: D4 REFUTED, D2 SUPPORTED). | It removes whole-tick denial: exclusive ticks went from 62% to none (E3; SYN §B). It keeps a residual, last-mover-leaning order dependence (E3: D1 and D8 NEITHER). The second-response privilege survives on λ = 1 parents (E4-H3 and E5-H2 SUPPORTED, both under K = 2; SR §C, K1). |
| **What the same Ruleset showed as E3's K = 1 companion** | — | A strong last-mover skew (median FMS 0.019, PD 0.963) and a tick-limit rise of +0.131 (E3-R §F.8). These are companion readings, never verdicts. |
| **What E6 recorded** | Whole-tick lockout is part of the mechanism behind E6's lone KC-5: a re-hit victim gets no callback in any tick its opponent moves first (E7-DR §4.3–§4.5; PA §7.1, §8). It is not sufficient by itself (PA §7.2). "B is true of the controls. It is not what caused KC-5" (E7-DR §5, overall reading). | At the point estimate, KC-5 does not fire. Under resampling, the companion raises PF-4 in 819/1000, and six units remain non-neutral under T-E6L (E7-DR §3.3). In E7-DR's words, *"The λ = 1 companion is not 'cleaner' in any robust sense"* (§14.1). Its own control's tick-limit share is 7/12 ≈ 0.583, against 0.225 under C-E6, and under T-E6L stalling concentrates on the defenders (E6-R §D.2, §D.5, §F.3). |
| **In short** (the research lead's reading) | It carries a known seat-sensitive timing mechanism. | It is not a neutral or "fixed" parent either. |

- **The standard the review must meet.** In the research lead's words, *"The E8 review must justify which imperfection is the cleaner research baseline for the mechanic being tested."*
- **What this decision is not.** It is *"very different from 'move E6 to λ=1 because it looked better,' which we explicitly rejected"* (the research lead; §I.4).
- **A registered two-parent factorial is an available option, not a recommendation.**
  - It could be justified if parent dependence cannot be separated from the candidate mechanic.
  - Under requirement G, the review should first ask whether a single parent plus a companion is cleaner.
  - E7-DR §3.1 records why a companion registered as a status comparison could not answer an interaction question (§H, item 2).

### G.2 The seat criterion

**The lesson, in the research lead's words:**

> E6 showed that an any-unit point-estimate seat kill can be sensitive to one threshold-crossing unit. The E8 design review must decide, on methodological grounds before preregistration, whether seat-safety requires bootstrap/stability evidence, a family-level quantity, both, or some other registered treatment.

**The evidence behind it:**
- **PF-4 is a point-estimate flag with no bootstrap requirement.** It fires when any unit that was neutral under its own arm's control is non-neutral under that arm's treatment. The two arms condition on different eligible sets: 26 units under C-E6 and 30 under C-E6L (E7-DR §3.1).
- **Resampled, the flag rarely separates the arms.** Under O-BOOT, PF-4 is raised in 967/1000 primary resamples and 819/1000 companion resamples. The observed pattern, primary only, occurs in 177/1000, and both arms raise it in 790 (PA §6).
- **KC-5 rested on one unit.** Its treatment \|GSB\| = 1/8 exceeds the 1/10 bound by 1/40, and its control neutrality rests on 2 distinct trajectories (E6-R §I.4).

**What the lesson does not do:**
- **It reopens nothing in E6.** These stabilities are hypothetical, and KC-5 fired exactly as registered (PA §6).
- **It copies nothing blindly.** PF-4 is not copied unchanged, and no replacement criterion or threshold is chosen here.

### G.3 Requirement C: a registered target, or secondary evidence

- **E6's choice.** E6 kept ADAPT secondary, by the research lead's decision: "never a condition of any row" (PR §5.3, citing DR §M, decision 9).
- **The scope review's requirement.** Any Branch B mechanic needs at least one adaptive agent, and SR §F names a signature for it.
- **What the review must decide.** Whether within-match adaptation is a registered E8 target, and, if so, how it is operationalized. It must also say whether the adaptive member and the tick-keyed stress member of E8-I4 are the same agent or different ones.

### G.4 Which mechanic state reaches the replay

- **Requirement F** asks that replay visualization can make the mechanic visible.
- **E6 could not.** Its visibility is not reconstructible from the replay (DR §C.4), so it needed callback-level traces (PR §6.6).
- **New events cost schema work.** [SOURCE] The replay reader rejects an unsupported event type (`replay.py:359`), so a new event type needs replay-schema work (SR §C, K8).
- **What the review must state, before implementation rather than afterward:** which new authoritative facts, if any, must enter the observation and the replay. SYN §I.3's principle stands: *"The engine produces authoritative match/replay facts; replay analysis and frontends derive and visualize those facts independently."*

---

## H. Method and Measurement Lessons E8 Inherits

These are recorded lessons, not new metrics. **SYN §G.8 is carried forward unchanged**:
- report n_distinct beside every count;
- analyse mirrors at the seed level, and treat relabel identity as a gate;
- rating-residual significance saturates on dominance pairings;
- every status combination needs exactly one interpretation row;
- a probe is not a substitute for a registered run.

New from E6 and E7. **Each is a lesson resting on a named event, not a binding rule.** The E8 design review decides which, if any, become pre-registration requirements.

1. **The seat criterion.** An any-unit point-estimate kill fired on one threshold-crossing unit (§G.2).
2. **A companion arm did not answer an interaction question.**
   - E6 was structurally a complete 2×2. Its companion was registered only as a status comparison, so every interaction value computed from it is post hoc (E7-DR §3.1).
   - Where post-hoc work followed, one practice held up: I_all was defined and committed in E7-DR before the audit computed it (PA §11, item 1).
3. **A registered contrast differed in more than information.** PACED differs from RUSH also in who sees first. LURK was added so that one contrast differs only in searching (PR §0, O-2).
4. **Engine-level family tests found defects that unit tests could not.** Behavior tests against scripted opponents under the controls, run before any seed existed, found two implementation defects. The earlier tests used hand-built observations, which "cannot show how the policy interacts with the engine's own write semantics" (A1 §2).
5. **Suppression governed sensing as well as acting.** In E6, disruption duration also set how long a victim was blind (E7-DR §3.1, coupling 1).
6. **Family-internal counters coupled to disruption semantics.** A lost offer changed the behavior of members that count their own callbacks (E7-DR §3.1, coupling 2). See E8-I4.
7. **Key-name redaction exposed a seed value.** Artifact paths embed match seeds, so a key-name-based redaction printed one seed value to the analyst. From then on, a value-based filter was used (E6-R §I.1).
8. **The process sequence did its job.** The research lead intends to reuse it almost unchanged: *"design review → adversarial/source audit → preregistration → implementation/checkpoint A → blinded seeds → controls/checkpoint B → treatment → analysis/reveal"*. The reason given: *"the engine-level pre-freeze tests caught real family defects, and the blinded/frozen analysis gave us a result we could trust."*

---

## I. Candidate Mechanic Families for the E8 Design Review

**These are families for the E8 design review to compare, not specifications, and they are not ranked.**
- Every statement about what a family would do is [INFERENCE].
- **Every family inherits:**
  - SR's constraints K1, K2, K6, K7 and K8 (SR §C);
  - invariants E8-I1 to E8-I5 (§F);
  - the parent decision (§G.1).
- **The question they serve, in the research lead's words:** E8 *"should not start by asking 'how do we fix E6?'"*

### I.1 Information decay, or uncertain last-known position

**The idea** (the research lead): *"Passive detection may remain relatively cheap, but information becomes stale when opponents move. The decision becomes whether to spend actions reacquiring certainty versus acting on uncertain information."*

**The prior record.** SR §D.1 named this failure mode 4, "One-shot discovery": *"Cores never move. If the scouting choice exists only until each side has found the other's core, the choice may be real but short-lived. The design review must check whether tracking anchors, for disruption, keeps it alive."*

**The risk: fixed cores and rarely moving anchors may make the mechanic inert.**
- **Cores are fixed.** [SOURCE] Core cells are set once, when the match is initialized (`process_runtime.py:757–763`). Under `core_base` spawn, every default-spawned anchor starts on its core cell 0. `core_base` is the default (`ruleset_policy.py:162`) and E6's placement (PR §2).
- **E6's anchors rarely moved.** [DOC] Its members made at most about one off-core MOVE per match on average: 1.03 for RUSH, and 0 for STEALTH, LURK, GUARD and GREED (E6-R §F.1).
- **Agents already remember.** [SOURCE] An agent is a stateful object. It is reset once per match, then asked to act at each offer (`agent_api.py:261–264`). [DOC] E6's family already keeps state across callbacks, such as ADAPT's pending evasion (E7-DR §4.4). An agent therefore holds a last-known position for as long as it chooses to.
- **What follows.** [INFERENCE] Information about a core never goes stale. Information about an anchor goes stale only as fast as anchors move. Against E6-like opponents, the mechanic would change little.

**Where it could act** [INFERENCE]:
- **Only on what the engine delivers.** The engine cannot make an agent forget.
- **Engine-side expiry overlaps §I.3.** Expiry that must be renewed by spending actions converges on a priced refresh.
- **Mobile targets may mean a second change.** Making staleness matter needs targets that move. That may mean changing the family alongside the mechanic, which G's one-variable rule forbids unless the design separates the two.
- **It may add stalling.** If staleness rewards moving away, evasion gains, and E6's evasion already carried a stalling liability (L-2).

**The first question for the design review:** what exactly goes stale, given fixed cores and stateful agents?

### I.2 Localized or partial information

**The idea** (the research lead): *"Instead of 'anchor visible inside radius, invisible outside,' an agent could know a coarse region, direction, age of contact, or confidence level. More precise information costs actions. That gives us more gradations than E6's search/no-search split."*

**Its strength: the best explanatory potential** (requirement F). [INFERENCE] A graded signal can be shown and reasoned about directly.

**Its cost: the largest API, observation and replay surface.**
- **New observation fields.** [SOURCE] `ObservationV2`'s only direct enemy information is `visible_enemy_anchor_addresses`, beside the results of the entrant's own READs (`agent_api.py:232–244`). A region, direction, age or confidence needs new observation fields.
- **A compatibility surface.** [DOC] Research-only additive API members have precedent without a version bump (SR §B.3, S2). Every new field is still a compatibility surface (SR §C, K8).
- **Replay work.** [DOC] E6's simpler visibility already could not be reconstructed from the replay (DR §C.4). [SOURCE] The replay reader rejects an unsupported event type (`replay.py:359`).

**The hardest requirement-G problem.** [INFERENCE]
- A graded channel has several parameters: what is graded, its resolution, and the price of precision. Each is a candidate variable.
- G asks for one new dimension at a time. So the review would have to fix all but one a priori, as E6 fixed *d* from geometry and never tuned it (SR §G.2, decision 4).

**The first question for the design review:** which single graded quantity is the manipulated variable, and how are the others fixed without tuning against outcomes?

### I.3 Resource-priced sensing

**The idea** (the research lead): *"Keep normal movement semantics but make better information consume a finite or regenerating match resource/action budget."*

**The rationale** (the research lead):

> **Separate information acquisition from movement so that the opportunity cost measured in E6 is not inseparable from locomotion.**

- **The evidence for it.** [DOC] E6 priced search through movement (PR §1), and SPLIT's sensor made every one of SPLIT's MOVEs (E6-R §F.2). The fast and paced searchers averaged 3.95 to 4.4 pre-detection MOVEs (E6-R §F.1).
- **Not the rationale: avoiding seat-sensitive first detection.** First detection was nearly seat-balanced under T-E6: 797 cells by Seat A, 823 by Seat B, 684 by neither (E6-R §F.4). The disruption regime almost never changes who sees first (E7-DR §3.2).

**The prior record.**
- **The nearest recorded form** is SR §D.1's variant I-b, a SCAN action. SR held it in reserve: "I-b only if movement-based discovery collapses into a search race or proves too geometry-bound" (SR §G.2, decision 2).
- **Stage 5 rejected it** as unjustified given local detection (SR §D.1).
- **SR's fallback condition was not met.** E6's KC-1 did not fire. So the case for this family rests on the separation rationale above, not on SR's fallback.

**The caution: the resource must compete with a meaningful alternative use.**
- In the research lead's words: *"A sensing-only fuel gauge merely meters sensing; it does not necessarily create requirement-B opportunity cost."*
- SR §B.1's condition C1 says the same: at least two uses must draw on the same finite budget.

**Inherited constraints.** [DOC]
- **K2.** If the resource can convert into actions, acting more than 8 times in a tick crosses the Q = CORE_SIZE boundary (SR §C).
- **K8.** A new action kind must be rejected under every other Ruleset.
- **Accounting.** It needs trace and scan accounting (SR §D.1, footprint).

**The first question for the design review:** what does the resource compete with, and how is it kept from converting into extra actions?

### I.4 Not E8: re-running priced sensing on the λ = 1 parent

- **The research lead's decision** (2026-09-29): *"I would **not** immediately make λ=1 the new parent and rerun priced sensing. The audit tells us that would amount to trying to rescue E6, and we explicitly decided not to do that."*
- **This is not the parent decision.** The parent for whatever mechanic E8 tests remains open (§G.1).
- **E7-F is not registered** (E7-DR §8.2; PA §13).

### I.5 Other recorded candidates, and the conditions for their return

**The scope review's conditions** [DOC] (SR §G.3):
- **Contestable valuable cells (the reserve).** They "come back if priced sensing is rejected on the search-race or greed criteria", and "in combination, if priced sensing succeeds". Either way, K1 must be answered first.
- **Deployment.** It "comes back if priced sensing succeeds and sensors become valuable". It still needs a monolith-equivalence argument (K5) and a decision on the free roster.
- **Banking.** It "stays out while K2 holds".

**How E6 bears on them.** E6 was rejected on KC-5, not on the search-race or greed criteria: KC-1 and KC-2 did not fire.

**"Priced sensing succeeds" has two meanings,** and SR's conditions must be read against each separately. In the research lead's words:

> **Research success:** E6 satisfied the Branch B strategic objective within its registered scope: opponent-dependent policy value and an information/action tradeoff were established.

> **Candidate success:** E6 did not produce a promotable gameplay mechanic; the candidate was rejected and the product-level seed-inference problem remains open.

- **By these definitions,** E6 is a research success and not a candidate success.
- **Left to the E8 design review:** which of SR's historical return conditions each meaning satisfies.
- **Excluded:** no reading of "priced sensing succeeded" implies that an E6 Ruleset should be promoted.

**The delayed-initial-visibility control arm.** SR §D.4 and §F recommended it, to separate "the forced line removed" from "a choice created". E6's four conditions did not include it (PR §2).

**Branch A remains a legitimate open research direction** (SYN §H; SR §D.5).
- E6's control reading, SPLIT universal under the parent for this family, is the parent-side by-product SR §F anticipated.
- It characterizes one scripted family. It does not disprove Branch A.
- In the research lead's words: *"E6 did not establish C, so 'adaptive agents under existing mechanics' is arguably more relevant now than it was before E6—not less."*

---

## J. Relationship to the E2–E5 Synthesis and the Broader Program

### J.1 What this document supersedes, and what it does not

> `V6_E2_E6_CROSS_EXPERIMENT_SYNTHESIS.md` **supersedes §G's forward-looking conclusions** of `V6_E2_E5_CROSS_EXPERIMENT_SYNTHESIS.md`, while leaving the earlier synthesis intact as the authoritative E2–E5 historical record.

- **Superseded:** SYN §G's role as the forward guidance for the next mechanic. The E8 design review works from §D–§I of this document.
- **Not replaced: the requirements themselves.** §D quotes A–G, and they remain the requirement set. SYN §G.8's measurement lessons are carried forward (§H).
- **Not superseded: the E2–E5 factual synthesis.**
  - SYN §A–§F, its record of the two branches (§H), §I and its decision boundary (§J) stand as written.
  - SYN is not edited.

### J.2 The makeover track

In the research lead's words: *"There is one other track that can run later or partially in parallel: the 'makeover' side of V6—replay interpretation, visual dramatization, and human readability. But I would hold off on deep UI work until we know what the next gameplay mechanic actually exposes."*
- **What connects the two tracks:** requirement F, and §G.4.
- **The engine/replay separation** of SYN §I.3 stands.

### J.3 Not resurrected

- **SYN §I.2's list stands:** giant arena scaling, proportional movement, simple hard reach-cap fog, and anchor-before-core as a product rule.
- **Added:**
  - a further sensing × disruption interaction experiment (E7-F);
  - re-running priced sensing on the λ = 1 parent as E8 (§I.4).

---

## K. Decision Boundary

- **The E7 line is closed** at design review and audit, with no experiment executed. E8 is the next experiment number.
- **E6's records are unchanged.** `R-CREATES` and REJECT stand, and both E6 Rulesets remain research-only.
- **Nothing is selected.** No E8 mechanic, parent Ruleset, seat criterion or threshold is chosen.
- **Nothing is started.** Nothing is registered, implemented or probed.
- **The next steps**, as the research lead set them out:
  1. this synthesis and the E8 design constraints;
  2. the E8 mechanic-family design review and selection;
  3. E8 pre-registration, implementation and qualification.

---

## What this synthesis does not claim

- **No new result**, and no new calculation. Every figure is copied from a cited record.
- **No claim beyond E6's scope** (§D.0).
- **No claim that adapting within a match pays.** Requirement C is open.
- **No causal claim about disruption regimes:**
  - not that whole-tick disruption generally makes priced sensing seat-unsafe;
  - not that λ = 1 is seat-clean (E6-R, "What this report does not claim"; E7-DR §3.3).
- **No ranking or selection** of a mechanic family, and no choice of parent, seat criterion or threshold.
- **No product decision**, and no change to E6's REJECT.
- **No use of Phases 4B–4D as evidence.**
- **No disproof of Branch A.**

---

## Appendix. Sources

**Authoritative records** (`docs/research/v6/`):

- [`V6_E6_PRICED_SENSING_RESULTS.md`](V6_E6_PRICED_SENSING_RESULTS.md), with its 2026-09-29 addendum pointer
- [`V6_E6_POST_HOC_FACTORIAL_AUDIT.md`](V6_E6_POST_HOC_FACTORIAL_AUDIT.md), including the research lead's decision (§13)
- [`V6_E7_SENSING_DISRUPTION_INTERACTION_DESIGN_REVIEW.md`](V6_E7_SENSING_DISRUPTION_INTERACTION_DESIGN_REVIEW.md), including the research lead's decisions (§16)
- [`V6_E2_E5_CROSS_EXPERIMENT_SYNTHESIS.md`](V6_E2_E5_CROSS_EXPERIMENT_SYNTHESIS.md), and through it the E2–E5 results records
- [`V6_E3_SLOT_LIMITED_DISRUPTION_RESULTS.md`](V6_E3_SLOT_LIMITED_DISRUPTION_RESULTS.md) §F.8 (the K = 1 companion), cited directly in §G.1

**Registration and implementation:**

- [`V6_E6_PRICED_SENSING_PREREGISTRATION.md`](V6_E6_PRICED_SENSING_PREREGISTRATION.md)
- [`V6_E6_AMENDMENT_1_FAMILY_CORRECTIONS.md`](V6_E6_AMENDMENT_1_FAMILY_CORRECTIONS.md)

**Framing only:**

- [`V6_BRANCH_B_ACTION_CHOICE_SCOPE_REVIEW.md`](V6_BRANCH_B_ACTION_CHOICE_SCOPE_REVIEW.md) §B, §C, §D, §F, §G
- [`V6_PRICED_SENSING_DESIGN_REVIEW.md`](V6_PRICED_SENSING_DESIGN_REVIEW.md) §C.4, §E.1–§E.2, §M

**Background only:**

- [`V6_PHASE4_GAMEPLAY_RESEARCH_METHODOLOGY.md`](V6_PHASE4_GAMEPLAY_RESEARCH_METHODOLOGY.md) and its Research Integrity Addendum (2026-09-22), and the Phase 4B–4D studies, as SYN §D.2 records them

**Source at `4e71b89`:**

- `engine/src/battle_engine/agent_api.py:232–244` (`ObservationV2`) and `:261–264` (the `AgentV2` protocol)
- `engine/src/battle_engine/process_runtime.py:757–763` (core cells set at initialization)
- `engine/src/battle_engine/ruleset_policy.py:162` (`initial_anchor_placement` defaults to `core_base`)
- `engine/src/battle_engine/replay.py:359` (unsupported event types rejected)
