# Bytefray V6 — E2–E5 Cross-Experiment Synthesis

**Status:** A descriptive synthesis of the completed and closed E2–E5 forensic line. It is not an experiment, a re-analysis or a pre-registration, and it creates no experimental result. Every registered verdict and interpretation below is quoted as its own record states it.
**Branch:** `v6-research`. Written against `cb91471` ("docs(v6): record the E5 anchor/core-0 separation results"), the E5 boundary.
**Date:** 2026-09-25
**Authority:** The four results records, for everything they state. §A.2 lists every other source and the limited role it plays.

- [`V6_E2_CAPTURE_HOLD_RESULTS.md`](V6_E2_CAPTURE_HOLD_RESULTS.md) (**E2-R**)
- [`V6_E3_SLOT_LIMITED_DISRUPTION_RESULTS.md`](V6_E3_SLOT_LIMITED_DISRUPTION_RESULTS.md) (**E3-R**), including its 2026-09-24 addendum
- [`V6_E4_MIRRORED_PASS_ORDER_RESULTS.md`](V6_E4_MIRRORED_PASS_ORDER_RESULTS.md) (**E4-R**)
- [`V6_E5_ANCHOR_CORE_SEPARATION_RESULTS.md`](V6_E5_ANCHOR_CORE_SEPARATION_RESULTS.md) (**E5-R**), including the research lead's disposition in its §I

A citation such as "E4-R §F.3" points to a section of one of these records. "E4-DR" is the E4 design review (§A.2).

---

## A. Scope and Evidence Rules

### A.1 What this document does

It reads E2 through E5 as one sequential forensic program and answers four questions:

1. What did the sequence rule out, or substantially weaken, as an explanation (§D)?
2. What mechanism or pattern survived it (§E)?
3. Which interventions failed as plausible gameplay improvements, and why (§F)?
4. What should the first genuinely new V6 gameplay mechanic satisfy (§G)?

It also records why V6 should now move away from further capture, scheduler and placement forensics (§B, §J).

It does **not**:

- run, register or pre-register an experiment;
- re-analyze any corpus, or read any replay, telemetry file or analysis output;
- create, change or promote a Ruleset;
- choose the next mechanic.

### A.2 Sources and the role each plays

| Source | Role here |
|---|---|
| E2-R, E3-R, E4-R, E5-R | **Authoritative.** Every verdict, interpretation, disposition and number. |
| The registrations: [E2](V6_E2_CAPTURE_HOLD_REGISTRATION.md), [E3](V6_E3_SLOT_LIMITED_DISRUPTION_REGISTRATION.md), [E4](V6_E4_MIRRORED_PASS_ORDER_REGISTRATION.md), [E5](V6_E5_ANCHOR_CORE_SEPARATION_REGISTRATION.md) | The registered research question of each experiment. |
| The design reviews: [E2-DR](V6_E2_CAPTURE_HOLD_DESIGN_REVIEW.md), [E3-DR](V6_E3_SLOT_LIMITED_DISRUPTION_DESIGN_REVIEW.md), [E4-DR](V6_E4_ORDER_VS_EVALUATION_TIMING_DESIGN_REVIEW.md), [E5-DR](V6_E5_ANCHOR_CORE_SEPARATION_DESIGN_REVIEW.md) and [E5 Revision 1](V6_E5_DESIGN_REVIEW_REVISION_1.md) | **Framing only:** what question was being asked, and why. Their probe values are priors. They are set against results only where a results record itself makes that comparison. |
| [Phase 0 baseline](V6_PHASE0_BASELINE.md); [Phase 4A methodology](V6_PHASE4_GAMEPLAY_RESEARCH_METHODOLOGY.md) and its 2026-09-22 Research Integrity Addendum; the Phase 4B–4E studies; [ROADMAP](../../ROADMAP.md); [FUTURE_PLANS](../../FUTURE_PLANS.md) | **Broader V6 context** outside the E2–E5 sequence. Labelled as such wherever it is used. |
| [ARCHITECTURE.md](../../../ARCHITECTURE.md) | The recorded separation between engine execution and replay consumption (§I.3). |

### A.3 Rules followed

- **Numbers.** Every number is copied from a committed record and cited. Nothing was recomputed. No raw corpus, replay, telemetry file or analysis output was read, and no analyzer was run.
- **No new instruments.** No metric, statistical test, unit classification, threshold or interpretation row is introduced.
- **Omitted comparisons.** Where a useful comparison would need a new calculation, this document says that the frozen records do not provide it, and leaves it out (§A.5, §E.4).
- **Vocabulary.** Statuses keep their record's own words. E2 predates the three-layer results format and uses Supported, Partially supported and Unsupported. E3–E5 use SUPPORTED, REFUTED and NEITHER. `NEITHER` stays `NEITHER`, and "supports" stays "supports".
- **Evidence labels.** Counts inherit their record's label. A value resting on fewer than 8 distinct trajectories is a deterministic or limited characterization, never a rate. Most E4 and E5 census units are deterministic (§E.3).
- **No retroactive reading.** Later evidence never rewrites an earlier experiment's conclusion. Where E5 bears on E4's population, this document reports it the way E5 registered it: as E5-H3, a continuity reading.

### A.4 The four layers kept apart

For each experiment, §C keeps four layers separate:

1. **Registered verdict.** The exact status of each hypothesis and hard stop.
2. **Registered interpretation.** The interpretation row that fired, or the record's explicit statement that none did.
3. **Descriptive findings.** What the record labels as description.
4. **Disposition.** Any research or engineering decision about whether the treatment should become a gameplay rule. Only E5 carries an explicit promotion decision. E2, E3 and E4 each record a research disposition and keep their Rulesets research-only.

### A.5 The experiments do not share an instrument

Each experiment measured with its own frozen instrument, on its own population:

| | Primary instrument | Primary population |
|---|---|---|
| E2 | Outcome transitions, seat-determination index (SDI), phase lock, capture telemetry | Field F1: 10 fixtures, 45 pairings |
| E3 | First-mover swing share (FMS) and two-sided parity dependence (PD) | 738 stalemate cells, defined on the C-E2 control (which runs E2's treatment Ruleset) |
| E4 | First-mover core advantage (FMA) and final-chunk-owner share (FPS), per matchup | 32 P-PAR matchup units, frozen on control |
| E5 | Directed base parity (BP) of core cell 0, per directed unit | 34 P-BASE directed units (17 sweep-backed), a 7-fixture field, frozen on control |

No metric spans all four experiments, and the frozen records contain no common scale. This document therefore compares the experiments only through their registered statuses and recorded counts. It never sets one experiment's metric beside another's as if they measured the same quantity. In particular, E4's FMA (whole core, per matchup) and E5's BP (core cell 0, per direction) are different readings. E5 reports FMA only for continuity with E4 (E5-R §F.6).

### A.6 Terms

- **First and second mover.** The scheduler rotates which seat acts first in a tick: Seat A on odd ticks, Seat B on even ticks. Each tick has four passes, and in each pass every live entrant receives a chunk of two action offers (Q = 8 per tick). Under the stock ("forward") order the tick's second mover acts second in every pass and owns the tick's final chunk.
- **K** (E2). The capture hold: the number of consecutive end-of-tick evaluations at zero owned core cells that completes a capture. Stable V4 is K = 1.
- **λ** (E3). The disruption slot limit: a hit suppresses its victim for that entrant's next λ offers instead of the rest of the tick. Stable V4 has no limit (whole-tick disruption).
- **Companion arm.** A K = 1 arm run beside a K = 2 primary to separate the hold's effect from the treatment's. It never replaces a primary verdict.
- **OPENING-ONLY and MULTI-PASS** (E4). Contest classes derived from the fixtures' source roles. A MULTI-PASS contest is fought in every pass. An OPENING-ONLY contest is fought once per tick, in the first pass, over the base cell (§C.4).
- **SB, AO and MIXED-INFERENCE** (E5). A directed base contest is **sweep-backed (SB)** when the attacker also attacks the victim's core explicitly and located it correctly in every control cell. It is **anchor-only (AO)** when the attacker has no core sweep or never located the victim's core, so the anchor hit is its only core contact. Anything else is **MIXED-INFERENCE**, which is reported but excluded from E5-H1 and E5-H2.
- **Base privilege.** In E5, BP > 0 means the victim owns its base (core cell 0) more often at the end of the ticks on which it moves second than at the end of those on which it moves first. BP reads core cell 0 only, not whole-core ownership or match outcome (E5-R §H.3).

---

## B. Executive Synthesis

**E2–E5 followed the stable-V4 tick-1 forced capture through four single-field interventions. Each one cut a real link, and none was the whole explanation.**

| Step | What the intervention removed | What remained |
|---|---|---|
| **E2** — capture hold K = 2 | Immediate fatality. The canonical forced line broke (H1 Supported). | Control of each tick by its first mover: stalemates phase-locked to the scheduler, and pairing-level seat determination unchanged in 45 of 45 pairings. |
| **E3** — one-offer disruption | Whole-tick denial. Exclusive ticks went from 62% to none, first-mover control did not persist (D4 REFUTED), and seat determination largely collapsed (D2 SUPPORTED). | A moderate, last-mover-leaning order dependence (D1 and D8 NEITHER). |
| **E4** — mirrored later passes | Most multi-pass response-order concentration (H1 SUPPORTED, 16 of 18). | The second mover's privilege in opening-pass contests (H3 SUPPORTED, 13 of 14 STAYS). |
| **E5** — spawn anchor off core cell 0 | Every base contest that existed only through the anchor hit (15 of 15 anchor-only contests neutralized, descriptive). | The directed second-mover base privilege in 13 of 17 sweep-backed contests (E5-H2 SUPPORTED; E5-H1 NEITHER). |

The last registered reading of the line is E5's `R-H2-PRIME`. Combined with E4, it **supports the second response in the opening exchange as the remaining mechanism**. That is support, not proof. Four sweep-backed contests are registered exceptions, and no mechanism for them is established.

**Four cross-experiment patterns.** These are descriptive readings of the recorded results, not registered findings.

1. **Internal dynamics moved more than winners did.** Mirrored order changed no F1 outcome class in 2,304 cells (E4-R §F.5). Separation lost 190 of 320 F1 captures and reversed no winner (E5-R §F.7). Under K = 2, 1,066 of 1,884 V4-decisive cells kept their winner, one tick later (E2-R §D.2).
2. **The hold changes which outcomes register more than whether the structure exists.** E3's K = 1 companion moves in the same direction as its primary on exclusivity and seat determination (E3-R §F.8). E5's reproduces the sweep-backed census with the same four exceptions (E5-R §F.8). E4-H4 is SUPPORTED: K = 2 masked outcome changes that K = 1 exposed. The companion readings are never verdicts, and elsewhere they differ from their primaries: E3's companion reading of D7 (draw-ification) is SUPPORTED, while the primary's is REFUTED (E3-R §D.2).
3. **The cost in decisive endings depended on the intervention.** Tick-limit endings rose sharply under E2 (a share of 0.333 → 0.545; H3a Partially supported) and under E5 (PF-2 raised). They did not under E3 (D7 REFUTED, a rise of 0.051) or E4 (H6 REFUTED, a rise of 0).
4. **No intervention gave an agent a new decision.** Each changed one timing or placement field of the Ruleset, and every primary field was made of scripted research fixtures. When E5 made a full disrupt-plus-sweep cost one action more, the fixtures did not choose. They lost one cell of core coverage per tick (E5-R §F.2, §J).

**Why V6 should now move on.**

- **The line is closed by its own records.** The research lead closed the E2–E5 forensic capture/order/placement line with E5, and registered no E5.1 (E5-R §I).
- **What survives sits in how scripted fixtures play the opening exchange.** E5's fixtures "never choose between disrupting and attacking the core, and never re-contest a cell within a tick" (E5-R §H.8). The lead declined to chase the four exceptions because "a further fixture-specific forensic experiment would study those agents more than it studies Bytefray" (E5-R §I). *Synthesis reading:* the same concern applies to the surviving pattern as a whole.
- **The rule changes tested make poor gameplay rules**, for reasons the records give (§F).
- **V6's gameplay objective is opponent dependence** (Phase 4A §1.2). E2 was the only experiment in the line that asked about it directly, and it answered that the hold "alone does not create sufficient strategic opponent-dependence" (E2-R §J). E3–E5 were forensic by design.

The next evidence therefore has to come either from agents that can choose (Branch A, §H) or from a mechanic that gives agents something worth choosing between (Branch B). The research lead's stated direction is Branch B, after this synthesis. Neither branch is registered.

---

## C. Experiment Sequence

### C.1 Lineage

Each treatment differs from its parent in exactly one Ruleset field (the registrations). Every Ruleset ID below begins `bytefray-rules-6-research-`.

| | Field changed | Primary: parent → treatment | K = 1 companion: parent → treatment | Matches | Analysis identity |
|---|---|---|---|---|---|
| **E2** | `capture_hold_ticks`: 1 → 2 | `scale` → `capture-hold-k2` | none (controls C-V4 and C-RS) | 15,360 | `v6-e2-freeze-v2-db6458596d82` |
| **E3** | `disruption_slot_limit`: none → 1 | `capture-hold-k2` → `capture-hold-k2-disruption-slot1` | `scale` → `disruption-slot1` | 19,456 | `v6-e3-freeze-v1-506811e78ad8` |
| **E4** | `scheduler_pass_order`: forward → mirrored | `capture-hold-k2-disruption-slot1` → `…-mirrored-passes` | `disruption-slot1` → `disruption-slot1-mirrored-passes` | 15,232 | measured under `v6-e4-freeze-v1-101a941f5e30`; interpreted under `v6-e4-freeze-v3-80f21d822542` |
| **E5** | `initial_anchor_placement`: `core_base` → `before_core` | `capture-hold-k2-disruption-slot1` → `…-anchor-before-core` | `disruption-slot1` → `disruption-slot1-anchor-before-core` | 7,168 | `v6-e5-freeze-v1-5ba12be258c8` |

Two structural facts matter when reading the sequence:

- **E4 and E5 are siblings, not a stack.** Both branch from E3's primary treatment (K = 2, λ = 1, forward order). E5 ran under forward order only, so no E5 result says anything about mirrored order.
- **Controls reproduced their parents, and gates held.** E3's controls reproduced E2's corpora byte for byte in 7,040 cells, E4's reproduced E3's treatments in 7,616, and E5's reproduced E4's controls in 3,584 (E3-R §B, E4-R §B, E5-R §B). Every E3–E5 treatment gate passed. E2's matrix was halted once before its treatment on a capture-analyzer defect ([execution halt](V6_E2_MATRIX_EXECUTION_HALT.md)). The analyzer was repaired and requalified on control data alone before any treatment match existed (E2-R §A).

### C.2 The sequence at a glance

| | Variable manipulated | Registered question | Registered result | What remained unresolved |
|---|---|---|---|---|
| **E2** | Capture hold K (1 → 2) | "does delaying fatal capture for one additional qualifying tick create meaningful opponent-dependent response, or does it merely transform the original forced line into delay, scheduler-locked draws, or another seat pathology?" | H1 Supported. H0 Unsupported. H2 and H3a Partially supported. H3b, H3c, H3f and H3g Supported. H3d and H3e Unsupported. The pre-registered clean negative is not declared. | Whether per-tick first-mover control ("a single disrupting write silencing every co-located process of the opposing entrant for the rest of the tick") is the load-bearing cause of the seat and scheduler-parity determination that remains (E2-R §L). |
| **E3** | Disruption duration (rest of the tick → the victim's next offer) | Whether bounding disruption to the victim's next action offer removes whole-tick denial, and so the first-mover-takes-all tick, without adding any new mechanic. | D2, D3, D6 and D9 SUPPORTED. D0, D4, D5 and D7 REFUTED. D1 and D8 NEITHER. **No pre-registered interpretation row applies.** | "Is the remaining order dependence caused primarily by the scheduler's last-action position, or by evaluating capture/state only at the end of the tick?" (E3-R §I) |
| **E4** | Pass-level response order (forward → mirrored) | "Does balancing pass-level response order neutralize the multi-pass residual while leaving opening-pass anchor contests unchanged?" | H1, H3 and H4 SUPPORTED. H0, H5, H6 and H8 REFUTED. H2 and H7 NEITHER. D9′ HOLDS. **No pre-registered interpretation row applies** (the registered "none" outcome), under all three interpretation layers. | "Does separating process anchor location from core cell 0 remove the opening-pass response privilege without changing disruption scope or scheduler order?" (E4-R §J: future work, not part of the E4 verdict) |
| **E5** | Spawn anchor placement (core cell 0 → `core_base − 1`) | "Is anchor/core-0 co-location necessary for the second mover's directed base privilege, where the base is also attacked explicitly (sweep-backed contests)?" | E5-D PASS. E5-H2 SUPPORTED. E5-H1 NEITHER. E5-H3 REFUTED (continuity only). E5-H4 and E5-H5 NEITHER. PF-2 and PF-3 raised. D9 HOLDS. **Registered interpretation: `R-H2-PRIME`.** | The four registered exceptions, left unexplained by decision (E5-R §F.3, §I). Whether agents that choose would show the privilege, which no experiment in the line tested (§E.4). The forensic line closes. |

### C.3 E2 — Multi-Tick Capture Hold

**Why K = 2 was introduced.** Under stable V4, competent global-reach play produces a deterministic tick-1 Seat-A forced core capture (E2 registration). E2-DR §D.2 traces it: Seat A's first write lands on Seat B's only anchor, which is also Seat B's core cell 0. That write disrupts Seat B for the rest of the tick, so Seat B forfeits all 8 offers and is captured at the end of tick 1. E2 changed one link of that chain: zero core ownership stops being immediately fatal, and a capture completes only after two consecutive end-of-tick evaluations at zero.

**The response window it created.** After a tick-1 onset, Seat B's disruption has expired by tick 2 and Seat B moves first, so it always gets two executable actions before Seat A acts (E2-DR §D.7, which framed the question). The matrix shows the window is real for defenders that disrupt first, and nominal for a pure repairer: the repair guard recovered 0 of 64 times against the sniper (E2-R §F).

**Registered verdict** (E2-R §H):

- **H1, defense becomes viable: Supported.** Defenders now survive orientations they lost under V4. Their survival is a draw for the disrupt guard, the min guard and the spread defender, and a win only for the guarded painter. The pure repair guard is the exception: it recovers 0 of 64 times against the sniper.
- **H0, delay only: Unsupported** as an explanation of the matrix. It "holds locally, as a deterministic characterization": 1,066 of 1,884 V4-decisive cells (0.566) keep their winner exactly one tick later, against a threshold of ≥ 0.90.
- **H2, genuine tradeoff: Partially supported.** "Present as a deterministic characterization; not established as a structural or rate result."
- **H3a, perpetual repair stalemate: Partially supported.** **H3b, phase-locked alternation: Supported** (610 of 610 stalemate entrants at phase lock ≥ 0.95). **H3c, new deterministic seat inversion: Supported** (one flip, no new seat determination). **H3f, zero-core winners: Supported** (343 of 1,274 decisive F1 wins). **H3g, capture never resolves: Supported.**
- **H3d, dominant always-defend, and H3e, location-count arms race: Unsupported.** Location count's dominance over stacked defenders is "unchanged from V4", so it is not an E2 effect.

**Registered interpretation.** E2 predates the interpretation-table format. Its pre-registered negative-result rule was **not** declared. That rule needs H2 to be unsupported after seat conditioning, and H2's tradeoff pattern survives seat conditioning as a deterministic characterization (E2-R §H, §K). The record states its scientific conclusion separately (E2-R §J):

> **K = 2 capture hold alone does not create sufficient strategic opponent-dependence under otherwise-V4 semantics.**

**Descriptive findings**, in three kinds:

- **Elimination and capture semantics.** No E2 treatment match is decided at tick 1 (E2-R §D.3). Winning while holding zero core cells becomes reachable: 343 of 1,274 decisive F1 wins, against none under V4 (H3f). Every capture stays attributed to its onset capturer (E2-R §A).
- **Interaction dynamics.** Of the 2,880 F1 cells (E2-R §D.2): 1,066 keep their winner exactly one tick later; 448 go from decisive to a tie after recovery; 162 keep their winner, now on score at the tick limit; 192 reverse, every one to the guarded painter and every one won at zero core; 16 keep their winner 6–198 ticks later; and the 996 that V4 did not decide are unchanged. The opponent dependence E2 creates is a deterministic "rock-paper-draw" pattern: sniper beats painter, painter beats defender on score, and defender draws sniper. Its draw edge "*is* the phase-locked stalemate" (E2-R §G.4, §J).
- **Scheduler and order effects.** The F1 tick-limit share rises from 0.333 to 0.545 (H3a), and every one of the 610 added tick-limit matches is a recovery stalemate phase-locked to the scheduler's first-mover rotation (H3b). Pairing-level seat determination is unchanged in 45 of 45 pairings, and the guarded-painter mirror's seat bias inverts from +0.688 (Seat A) to −1.000 (Seat B) (E2-R §E).

**Disposition.** "E2 is a useful but insufficient mechanic, and it should remain research-only" (E2-R §K). This is a research disposition, not a product or balance recommendation.

**What E2 handed on.** E2 did not fail at what it attempted. It created the intended response window and broke the canonical forced line. What it exposed is where the remaining determinism lives: "the defended state is the alternation, and whoever moves first in a tick controls that tick" (E2-R §J). The record traces this to mechanics held constant in E2: scheduler rotation, "the rule that one disrupting write disables every co-located process for the rest of the tick", and co-located spawn. That moved the question from **when capture completes** to **how long disruption lasts**.

### C.4 E3 — Slot-Limited Disruption

**Why disruption duration.** E2 left each tick to its first mover. Under whole-tick disruption, one successful write to the address where an entrant's processes are anchored makes all of them ineligible, and blind, for the rest of the tick (E3 registration). E3 changed only how long a hit suppresses its victim: λ = 1, meaning that entrant's next offer, still within the tick. Trigger and scope were unchanged.

**Registered verdict** (E3-R §D.1):

- **SUPPORTED:** D2, seat determination decreases (5 of 6 seat-determined units fall below SDI 0.9); D3, defense no longer needs disrupt-first (192 of 192 of the repair guard's capture losses become non-losses; n_distinct 6, a limited characterization); D6, re-disruption recreates control (through the min guard only; deterministic); D9, hold × order immunity (0 completions against the repair and disrupt guards).
- **REFUTED:** D0, no structural change (0.636 of exposed cells unchanged, below 0.90); D4, first-mover control persists (median FMS 0.143); D5, location/process-count exploit (under the accepted limitation P-1, only the refutation branch was reachable, and it holds); D7, draw-ification (a rise of 0.051).
- **NEITHER:** D1, parity lock decreases, and D8, last-mover inversion. The median two-sided parity dependence, 0.714, lies between their thresholds.

**Registered interpretation.** "No pre-registered interpretation row applies" (E3-R §E). The closest rows, D1 ∧ D2 and D2 ∧ D8, both fail on the parity criterion. The registered clean negative ("not load-bearing; the disruption line closes") does not fire either, because D2 is SUPPORTED.

**Descriptive findings** (E3-R §F):

- **Whole-tick denial is gone.** The exclusive-tick share falls from 0.622 to 0.000, and the second mover's mean executed actions per tick rise from 2.50 to 7.37 (§F.1).
- **Seat determination collapses.** F1 seat-determined pairings go from 3 to 0, and the maximum |seat bias| from 1.000 to 0.0625 (§F.2).
- **Zero-core winners nearly vanish.** They fall from 343 to 12 in F1 (§F.3).
- **Order dependence persists, and changes direction.** In the 738-cell stalemate population, first-mover-dominated or first-mover-leaning cells go from 642 of 642 scoreable cells to 0 (§F.3, §F.10). Under the treatment, 287 cells are last-mover-dominated, 66 last-mover-leaning and 224 neutral. The canonical sniper-versus-disrupt-guard stalemate goes from an FMS of exactly 1.0 to exactly 0.0, and it is still a tick-limit tie.
- **The field is restructured, not draw-ified.** About half of the stalemate draws become decisive, split evenly between the seats (§F.4).
- **Companion (K = 1).** It reads in the same direction, with a sharper last-mover skew. The record takes this to suggest that "the residual order effect is not an artifact of K = 2" (§F.8, a companion reading).
- **The record's synthesis** (§F.10): "Slot-limited disruption clearly removes whole-tick first-mover monopoly and substantially reduces seat determination, but it does not eliminate order dependence. The remaining interaction is moderately last-mover-leaning, rather than strongly parity-neutral or strongly last-mover-dominated."
- **Addendum (2026-09-24).** The guarded-painter mirror's seed split is 19 Seat-A seeds to 13 Seat-B seeds, not 20 to 12. Twin-mirror SDI is 1.0 by construction on every decisive seed. No verdict changes.

**The contest structure behind the residual.** *This is the E4 design review's classification, not an E3 finding.* E3's record does not classify its residual by contest type. The E4 design review did so afterwards, from E3's frozen telemetry, to frame the E4 question (E4-DR §D.1–§D.2). Of E3's 353 last-mover-leaning or last-mover-dominated stalemate cells:

- **OPENING-ONLY: 257 (73%).** The contest is fought once per tick, in pass 1. The first mover hits the enemy anchor (which is the enemy's core cell 0) and repairs its own base; the second mover then does the same, after it; neither writes those cells again that tick.
- **MULTI-PASS: 96 (27%).** The same cells are fought in every pass, for example a sniper sweeping the disrupt guard's core while the guard repairs it.
- **None** was a final-chunk effect. The 192 incidental painting-front cells all fell in the neutral class.

E5 later used these classes only as a descriptive secondary stratum (E5-R §F.2), because E4's class definition itself assumes the anchor is core cell 0 (E5-DR §M, AF-1).

**Disposition.** Descriptive: **"E3 is a successful causal intervention but not a complete gameplay solution."** The registered disposition is simply that no interpretation row triggered. Both Rulesets remain research-only (E3-R §H).

**Why E3 pointed at order.** The distinction to keep is this: whole-tick denial disappeared completely, and the order phenomenon did not. With denial gone, both entrants act in every tick, so what remains cannot be first-mover exclusivity. E3's record named the suspects as "the tick's final action and the end-of-tick evaluation instant" (E3-R §I). The E4 design review then found that those two cannot be separated by any scheduler-only or evaluation-only treatment, and that every evaluation-timing change is really a new capture-strictness rule (E4-DR §E.1, §G; E4 registration). That left the in-tick response order as the next single-field lever.

### C.5 E4 — Mirrored Pass Order

**Why pass order.** The E4 design review reframed E3's residual in terms of which entrant responds last within each pass. Under forward order the tick's second mover is the later responder in all four passes. Mirrored order keeps it the later responder in passes 1–2, makes the first mover the later responder in passes 3–4, and gives the final chunk to the first mover (E4 registration). That gave three distinguishable signatures: a privilege that **follows the final chunk**, one that is **neutralized** (response-order concentration), and one that **stays** (the opening pass, which mirroring leaves untouched) (E4-DR §F).

**Registered verdict** (E4-R §D.1):

- **SUPPORTED:** H1, response-order concentration is load-bearing (16 of 18 MULTI-PASS units NEUTRALIZED); H3, opening-pass response privilege (13 of 14 OPENING-ONLY units STAY); H4, hold × order masking (under the companion 128 of 640 exposed MULTI-PASS F1 cells change outcome class, under the primary 0 of 640).
- **REFUTED:** H0, no structural effect (13 of 32); H5, new early-capture pathology (0 of 1,463); H6, stasis (a rise of 0); H8, tick-limit parity artifact (all 9 mirror claims agree at 1000 and 1001 ticks).
- **NEITHER:** H2, the privilege follows the final pre-sample chunk: 2 of 18 MULTI-PASS units, 1/9 ≈ 0.111, against support at ≥ 2/3 and refutation at ≤ 1/10. H7, seed-conditioned seat dependence.
- **D9′ HOLDS**, with 0 completions.

**Registered interpretation.** **No pre-registered interpretation row applies.** The registered "none" row fires, and the census is reported (E4-R §E). The closest row, H1 ∧ H3 ∧ ¬H2, would have read "Two order mechanisms. In multi-pass contests it is response-order concentration, which order can remove. In anchor-base contests it is the second mover's opening response, which order cannot touch" (abridged in E4-R §E). It needs H2 REFUTED, and H2 is NEITHER. All three interpretation layers give the same reading, and both interpretation-only amendments were frozen before any treatment cell existed (E4-R §E.1).

**Descriptive findings** (E4-R §F):

- **Substantial internal ownership changes.** F1 cell FMA bands move from strong-last 128 → 0, moderate-last 776 → 322 and neutral 881 → 1,399 (§F.5). In MULTI-PASS, 14 units are substantively neutralized and 2 more cross a band boundary by 0.002 (§F.2).
- **The genuine FOLLOWS-FINAL case.** One pairing, the disrupt guard against the min guard, in both orientations. FMA goes from −3.5 to +0.5, and FPS confirms that the privilege now tracks the owner of the final chunk, "so this pairing's classification is not a banding artifact". It is much smaller in magnitude, and deterministic (§F.4). It is why H2 is NEITHER, and the record never treats H2 as refuted (§D.2).
- **Opening-pass contests remained important.** All 14 OPENING-ONLY units keep their second-mover swing privilege. Their FPS goes from about 1 to about 0, because the swings stay with the tick's second mover, who no longer owns the final chunk (§F.3). Six of these units are rate-eligible, which makes OPENING-ONLY the best-sampled part of the population.
- **Weak propagation into K = 2 outcomes.** 0 of 2,304 F1 cells change outcome class, and 41 of 3,808 primary cells do in all (§F.5). H1's "load-bearing" refers to its FMA-band criterion, and no outcome-level claim is made from it (§H.5).
- **Stronger K = 1 sensitivity.** Under the companion, 230 of 3,808 cells change outcome class, and completions against the repair and disrupt guards fall from 192 to 0 (§F.6).
- **Evidence weight.** 17 of the 18 MULTI-PASS units rest on a single trajectory. The counts are census counts of matchup characterizations, not rates (§H.2).

**Disposition.** Descriptive (E4-R §I):

> **E4 produced a strong descriptive two-mechanism pattern, but no pre-registered interpretation row applied. Mirrored pass order largely neutralized multi-pass response-order concentration while leaving opening-pass anchor/core-0 contests largely unchanged. The final-pre-sample hypothesis was not formally refuted under the frozen threshold because 2 of 18 multi-pass matchups followed the final chunk.**

The registered disposition is that no interpretation row triggered. Both Rulesets remain research-only.

**Neither "order caused it" nor "order did not matter".** E4 supports neither simplification. Order is load-bearing for the multi-pass concentration it was designed to test (H1), it masks or exposes outcome effects together with the hold (H4), and one pairing follows the final chunk (H2 NEITHER). It is not what carries the opening-pass privilege (H3).

**Why E4 led to E5, and what it did not mandate.** E4 did not formally mandate E5. Its registered interpretation was "none", and the row that names the opening response did not fire. E4-R §J states the co-location question as "future work, not part of the E4 verdict", and gives §F.3, the OPENING-ONLY units keeping their second-mover privilege, as the reason for asking it. The E5 registration supplies the spatial reason: every Agent API v2 process spawns on its entrant's core cell 0, so a write to a never-moved enemy anchor both disrupts the process and flips a core cell. No rotation-preserving pass order can move that opening exchange (E4-DR §E.3). The E4 result E5 later combined with is its registered verdict H3 (SUPPORTED), not its interpretation.

### C.6 E5 — Anchor/Core-0 Separation

**Why placement.** E5 moved the default spawn to `(core_base − 1) % arena_size`. The E5 design review had found that moving the anchor by an arbitrary offset also changes where the frozen fixtures think the enemy core is, and returned a REDESIGN verdict (ROADMAP, E5 entry). The corrected design (Revision 1 §R1) uses the one offset at which that anchor-derived targeting stays behaviorally inert, on a seven-fixture field with four fixtures excluded. It scores each victim's core cell 0 by directed base parity (BP).

**Registered verdict** (E5-R §D):

- **E5-D, the decoupling manipulation gate: PASS.** **D9: HOLDS**, with 0 completions.
- **E5-H2, co-location is not necessary for the directed base privilege: SUPPORTED.** 13 of 17 sweep-backed units STAY: 13/17 ≈ 0.765, against ≥ 2/3.
- **E5-H1, co-location carries the directed base privilege: NEITHER.** 4 of 17 units NEUTRALIZED: 4/17 ≈ 0.235. Support needs ≥ 2/3, and refutation needs ≤ 1/10, which admits at most one unit.
- **E5-H3, the E4 residual-population null: REFUTED.** 18 of 28 E4 residual units keep their FMA band (9/14, below 9/10). It measures continuity only.
- **E5-H4, separation changes match outcomes (K = 2): NEITHER.** 64 of 1,344 F1 cells (1/21) change outcome class. All 64 are captures lost, and none is gained.
- **E5-H5, the hold changes how much separation changes outcomes: NEITHER.** |2/21 − 1/21| = 1/21.
- **Pathology flags:** PF-2 (stasis) and PF-3 (new immunity) raised; PF-1, PF-4 and PF-5 not raised.

**Registered interpretation: `R-H2-PRIME`** (E5-R §E), verbatim:

> Co-location is not necessary for the directed base privilege in a supermajority of SB contests. Removing the dual-purpose anchor/core write leaves the SB privilege intact in those contests; the SB units that weakened, neutralized or flipped are named as registered exceptions. Combined with E4's finding that the OPENING-ONLY privilege survives mirrored later-pass order, this supports the second response in the opening exchange as the remaining mechanism. The anchor/core forensic line closes.

**The four registered exceptions.** All four NEUTRALIZED (none weakened or flipped). Each is a deterministic characterization (n_distinct 1), and the same four neutralize under K = 1 (E5-R §E, §F.3, §F.8).

| Attacker → victim | Control BP → treatment BP | E4 class |
|---|---|---|
| min guard → repair guard | 1/2 → 1/4 | MULTI-PASS |
| spread defender → repair guard | 249/500 → 1/4 | MULTI-PASS |
| min guard → spread defender | 1 → 1/500 | OPENING-ONLY |
| sniper → spread defender | 1 → 1/500 | OPENING-ONLY |

Recorded alongside the interpretation, and not inputs to it: E5-H3 REFUTED is "never a mechanism reading"; E5-H4 is NEITHER, recorded with its direction; E5-H5 is NEITHER, a companion reading; PF-2 and PF-3 are recorded as pathologies whatever else holds.

**Descriptive findings** (E5-R §F):

- **Sweep-backed contests: 13 of 17 retain the directed privilege, and 4 neutralize.** Nine STAYS units sit at BP 1 in both arms, two move from 1 to 497/500, and two repair-guard units stay at about 1/2. The attacker still makes its first hostile contact at tick 1 and keeps writing the base. What it loses is one cell of core coverage per both-alive tick, because disrupting the process and writing core cell 0 are now two writes, and "the scripted fixtures do not choose between them" (§F.2).
- **The exceptions cluster by victim.** Every sweep-backed unit whose victim is the disrupt guard, the guarded painter or the min guard stays (11 of 11). Both sweep-backed attacks on the spread defender neutralize. The repair guard's four sweep-backed units split by attacker. The one-cell coverage loss is common to the exceptions and the STAYS units, so it does not explain them, and no mechanism is established (§F.3).
- **Anchor-only contests: all 15 neutralized**, 9 of them rate-eligible. This is an outcome reported descriptively. Revision 1 removed it from the manipulation gate, so it is not part of E5-D (§F.4).
- **Mixed-inference contests are reported separately and excluded from H1 and H2.** Both units, sweeper attacks on the spread defender, go from 499/500 to 0 (§F.4).
- **Separation can also create the privilege.** One contest that was neutral in control (spread sniper → spread defender) gains the second-mover parity signature under separation. It lies outside every registered census (§F.5).
- **Outcomes and captures** (§F.7, primary F1):
  - 190 of the 320 control captures disappeared;
  - 126 of them kept the same winning seat, now as tick-limit wins on score;
  - 64 became ties;
  - no winner was reversed;
  - no new capture appeared (PF-1: 0 of 1,024);
  - tick-limit endings rose from 1,024 to 1,214.
- **E4's residual population** (E5-H3, continuity only). The 10 of 28 residual matchups that left their FMA band are exactly the matchups whose base contests are all anchor-only or mixed-inference: 8 of E4's 14 OPENING-ONLY units and 2 of its 14 MULTI-PASS units (§F.6).
- **Companion (K = 1).** It reproduces the sweep-backed census with the same four exceptions, and all 15 anchor-only units neutralize. 128 of its 1,344 F1 cells change outcome class, and separation closes its guard captures (64 → 0) (§F.8).

**Disposition** (the research lead, 2026-09-25; descriptive, not a registered rule; E5-R §I). The lead's summary, verbatim:

> **Anchor/core co-location creates free contact with the core. It does not create the directed second-mover base privilege in most contests where the attacker already has an explicit core attack.**

- **Not recommended for promotion.** `before_core` is not recommended for promotion into the V6 gameplay Ruleset. The record calls this "an engineering and research decision, based principally on PF-2 and PF-3. It is not a new pre-registered hypothesis." Together, PF-2 and PF-3 describe a large loss of decisive resolution (190 of 320 F1 captures lost) without a correspondingly large change in competitive ordering (64 outcome-class changes, no winner reversed). In the lead's words, separation "substantially changes **how matches resolve** without substantially changing **who ends up winning**" (§F.7), and "We removed a lot of decisive interaction and mostly converted it into longer versions of the same competitive ordering."
- **The four exceptions stay exceptions.** They are real and seed-invariant, they do not overturn the registered interpretation, and no E5.1 is registered to chase them.
- **E5-H3 REFUTED "is not bad news".** It is continuity only. It shows that part of E4's residual population existed "because anchor disruption was also supplying free core pressure", and it does not explain the surviving sweep-backed privilege.
- **The forensic line closes.** "With E5, the E2–E5 forensic line is closed: capture hold, then disruption duration, then pass order, then spatial co-location."

---

## D. What the Sequence Ruled Out

For almost every candidate, the sequence established that the mechanism is **not sufficient** to explain the structure, not that it is irrelevant. Every mechanism below had a measured effect. The accurate general statement is:

> **These mechanisms are not sufficient explanations of the persistent strategic and order structure.**

Two rows are registered refutations rather than "not sufficient" readings: the location-count exploit once disruption lasts one offer (row 3), and tick-limit parity (row 5).

### D.1 Within the E2–E5 sequence

| # | Candidate explanation | Tested by | Registered evidence | Reading | What it does **not** mean |
|---|---|---|---|---|---|
| 1 | The absence of a response window | E2 | H1 Supported; pairing-level seat determination unchanged in 45 of 45; H3b Supported | A real window exists under K = 2 and breaks the canonical forced line, but control passes to each tick's first mover. **Not sufficient.** | Not "the window did nothing": 610 cells became recovery stalemates and 192 reversed (E2-R §D.2). |
| 2 | Whole-tick disruption denial | E3 | D4 REFUTED; D2 SUPPORTED; D1 and D8 NEITHER | Load-bearing for first-mover exclusivity and for much of the seat determination (E3's descriptive disposition). **Not sufficient** for the order dependence that remains. | Not "disruption is harmless": re-disruption still recreates control against the min guard (D6 SUPPORTED). |
| 3 | Location or process count as a durable exploit | E2, E3 | E2-H3e Unsupported ("unchanged from V4"); E3-D5 REFUTED, on its reachable branch (P-1) | Under whole-tick denial, location count dominated stacked defenders, and a disrupt-first defender was captured only by an attacker with more locations than one disrupting chunk can cover (E2-R §J). Under λ = 1, "Location count stops paying" (E3-R §F.6, descriptive). | Not a claim about multi-process play in general: the evidence comes from two spread fixtures. |
| 4 | The capture hold as the source of the order structure | E3, E4 and E5 companions | E4-H4 SUPPORTED (masking); companion readings in E3-R §F.8 and E5-R §F.8 | The structure appears under both K = 1 and K = 2. K changes which outcomes register (companion readings, not verdicts). | Not "K is irrelevant": K = 2 with λ = 1 makes continuous repairers provably uncapturable (E3-D9 SUPPORTED; E4-D9′ HOLDS), and K decides which captures survive separation (E5-R §F.8). |
| 5 | Tick-limit parity | E3, E4 | E4-H8 REFUTED; every E3 mirror claim is the same at 1000 and 1001 ticks (E3-R §F.2) | **Ruled out** as the source of the mirror seat claims. | — |
| 6 | Later-pass response-order concentration as the complete explanation | E4 | H1 SUPPORTED; H3 SUPPORTED | Load-bearing, in its registered FMA-band sense, for most multi-pass contests. **Does not explain** the opening-pass privilege. | Neither "scheduler order caused the problem" nor "scheduler order did not matter" (§C.5). |
| 7 | The final chunk, or the end-of-tick evaluation instant, as the carrier of the privilege | E3's question, tested by E4 | E4-H2 NEITHER | **Not established, and not excluded.** One pairing follows the final chunk. The opening-pass units do not: their swings stay with the second mover (E4-R §F.3). | Not a refutation. H2 is NEITHER. |
| 8 | Anchor/core co-location as necessary for the sweep-backed privilege | E5 | E5-H2 SUPPORTED; E5-H1 NEITHER; `R-H2-PRIME` | Not necessary in a supermajority, 13 of 17. Co-location is the only source of contact in anchor-only contests (15 of 15 neutralized, descriptive), and it supplied part of E4's residual population (E5-H3, continuity only). | Not "co-location has no effect": four sweep-backed contests neutralized, and separation cost 190 captures. |

### D.2 Broader V6 context (outside the E2–E5 sequence)

These lines ran before E2, or before V6. They are not part of the E2–E5 causal sequence, and their figures are not E2–E5 evidence.

- **Arena scaling and movement normalization as the route to a stronger strategic ecology.** Phases 4B–4D varied arena size and movement semantics under otherwise-V4 rules. As the ROADMAP summarizes them: the aggregate competitive hierarchy stayed scale-robust (4B); movement-stride normalization was inert for the frozen agents, with every gameplay delta exactly 0.0 (4C); and proportional movement induced sublattice tunneling, so that 49.6% of matches at arena size 65,536 never made contact (4D). The line was closed on 2026-09-22 by a Research Integrity Addendum. The addendum records that the line "was grounded in flawed causal premises and compromised by test and benchmark defects", and that the stable-V4 tick-1 forced capture was "the unacknowledged driver of apparent lethality in global probes" (Phase 4A addendum). It is recorded here as a line not pursued.
- **Simple bounded reach.** Pre-V6 research found that bounded reach produced a "bulldozer effect": contiguous expanders swept through stationary cores, search collapsed into slow expansion, and defense collapsed (V3 Phase 2, as cited in Phase 4A §1.1 and §11.4). Phase 4A §11.4 concludes that any information restriction "must pair reach bounds with anti-bulldozer rules".

---

## E. What Survived

### E.1 The surviving pattern

**A strong directed second-mover base privilege survives in most explicit core contests.**

- **Registered.** E4-H3 is SUPPORTED: 13 of 14 OPENING-ONLY units STAY under mirrored later-pass order. E5-H2 is SUPPORTED: 13 of 17 sweep-backed units STAY when the spawn anchor leaves core cell 0.
- **Registered interpretation.** `R-H2-PRIME`: "Combined with E4's finding that the OPENING-ONLY privilege survives mirrored later-pass order, this supports the second response in the opening exchange as the remaining mechanism."
- **The mechanism the reading refers to.** *The E4 design review's source-derived description, used here as framing.* In the first pass, the first mover's chunk hits the enemy anchor and repairs its own base; the second mover's chunk then does the same, after it; and neither fixture writes those cells again that tick. The privilege is the "second response in the only exchange", not the last action (E4-DR §D.3). `R-H2-PRIME` supports this reading. It does not prove it.
- **Where it appeared.** It first showed in E3's residual order dependence, once whole-tick denial no longer gave each tick to its first mover, as the E4 design review later classified that residual (§C.4). It then survived mirrored later passes (E4-H3) and spawn separation (E5-H2).

### E.2 What remains alongside it

- **Four registered exceptions** (E5-R §E, §F.3): the min guard and the spread defender against the repair guard, and the min guard and the sniper against the spread defender. They are real and seed-invariant (n_distinct 1 in both arms), they cluster on two victims, and they are unexplained.
- **The multi-pass privilege is order-sensitive.** E4-H1 is SUPPORTED, and one pairing follows the final chunk (E4-H2 NEITHER).
- **The surviving privilege is narrower than E4's OPENING-ONLY class.** Under separation, 8 of the 14 OPENING-ONLY units in E5's residual population left their FMA band: the ones whose base contests were anchor-only or mixed-inference (E5-R §F.6, E5-H3, continuity only). The sweep-backed STAYS units span both E4 classes, 7 OPENING-ONLY and 6 MULTI-PASS: "The privilege does not follow E4's contest class" (E5-R §F.2).
- **Separation can create the signature.** One contest that was neutral in control gained it under separation (E5-R §F.5).

### E.3 Scope and evidence weight

- **A scripted-fixture ecology.** The E5 result holds for "2 entrants, Q = 8, chunk 2, arena 512, rotation, 1,000 ticks and the seven scripted fixtures as written. Those fixtures never choose between disrupting and attacking the core, and never re-contest a cell within a tick. No external-validity claim is made" (E5-R §H.8; compare E4-R §H.7). It is an observation about that ecology, not a theorem about Bytefray agents.
- **Mostly deterministic units.** 13 of the 17 sweep-backed units, including all four exceptions, are deterministic characterizations, and 17 of E4's 18 MULTI-PASS units rest on one trajectory. The censuses are "mechanistically consistent, but … not population-rate evidence" (E5-R §F.10; E4-R §F.9). Most fixtures are deterministic by design, so seeds are not independent trials (E2-R §C).
- **Whole-unit margins.** E5-H2 needed 12 of 17 units and observed 13 (E5-R §H.2).
- **What "base privilege" covers.** The directed parity reading of core cell 0, "nothing broader" (E5-R §H.3).

### E.4 What has not been established

- **No universal law** of Bytefray strategy.
- **No proof that an adaptive or searched agent would show the same privilege.** The E5 design review offers an untested inference, which is a question for Branch A, not a finding: "A defender that repaired its base with its final in-tick action would own it in both roles" (E5-DR §P).
- **No explanation of E5's four exceptions.** None was sought (E5-R §F.3, §I).
- **No claim that scheduler details are irrelevant.** E4-H1 and E4-H4 are SUPPORTED, and E4-H2 is NEITHER.
- **No reading of base parity under mirrored order.** Six of E5's 13 STAYS units belong to E4's MULTI-PASS class, where mirrored order removed most of the FMA privilege (E4-H1). E5 ran under forward order only, and E4 measured matchup FMA rather than directed BP. **The frozen records do not provide this comparison**, and this synthesis does not estimate it.
- **No exclusion of free information as an upstream cause.** "Information is free and global (R4b's unmet precondition), and E3 cannot rule it out as an upstream cause" (E3-R §G.7). No later experiment varied information.
- **No K = 3 result** (E2-R, "What this report does not claim").

---

## F. Scientific Probe vs Gameplay Candidate

> **A manipulation may be valuable as a causal probe without being a good gameplay rule.**

Every E2–E5 treatment passed its manipulation gates and taught something causal. None of them has become a gameplay rule. All seven E2–E5 research Rulesets remain research-only and resolvable. Only E5's record states a promotion decision. For E2–E4, the records keep the Rulesets research-only and propose no rule change.

### F.1 Within the E2–E5 sequence

| Intervention | What it taught | Recorded effects that bear on its use as a rule | Recorded disposition |
|---|---|---|---|
| **K = 2 capture hold** (E2) | Immediate fatality carries the canonical forced line. Once it is removed, the first mover controls each tick. | 610 phase-locked recovery stalemates; 343 of 1,274 decisive F1 wins taken at zero core; a new seat-determined mirror. The opponent dependence it creates is "constituted by pathologies" (E2-R §K). | "useful but insufficient … research-only"; "Nothing in it is ready to shape a Ruleset" (E2-R §K). |
| **λ = 1 slot-limited disruption** (E3) | Whole-tick denial carries first-mover exclusivity and much of the seat determination. | A last-mover-leaning order dependence remains. With K = 2, continuous repairers become provably uncapturable (D9: 0 completions), which the record treats as a confound (E3-R §F.5). Decisive games get longer: the upper-quartile decision tick rises from 4 to 59 (E3-R §F.4). | "a successful causal intervention but not a complete gameplay solution" (E3-R §H); research-only. |
| **Mirrored pass order** (E4) | Separates multi-pass concentration from the opening-pass privilege. | Changes within-match ownership widely and F1 outcomes not at all under K = 2 (0 of 2,304). Leaves the opening privilege in place. | A descriptive disposition only; research-only. |
| **`before_core` anchor separation** (E5) | Co-location supplies free core contact, not the sweep-backed privilege. | PF-2 (tick-limit endings up by 190) and PF-3 (190 of 320 captures lost), with no winner reversed. | **Not recommended for promotion**, principally because of PF-2 and PF-3 (the research lead, E5-R §I). |

### F.2 Broader V6 and pre-V6 context (not part of the E2–E5 sequence)

| Intervention | Recorded problem | Status |
|---|---|---|
| Proportional movement (Phase 4D) | Sublattice tunneling and non-contact (49.6% of matches never made contact at arena size 65,536); timeouts rose to 66.7% (ROADMAP, Phase 4D) | Line closed (Phase 4A addendum) |
| Movement-stride normalization (Phase 4C) | Inert for agents that clamp their own strides (ROADMAP, Phase 4C) | Line closed |
| Simple reach caps (V3 Phase 2, cited in Phase 4A §11.4) | The bulldozer effect | Never to be introduced naively (Phase 4A §11.4) |

### F.3 What the probes have in common

*This is a synthesis reading of the recorded treatments, not a registered finding.*

- **Each E2–E5 treatment changed *when* or *where* an existing action takes effect.** None added an action, a resource, or information an agent could pay to acquire. Their recorded effects are therefore all redistributions of contact and timing among fixtures that each play one fixed policy.
- **A lost decisive ending is not inevitable.** Two of the four treatments (E2, E5) paid for their causal effect with decisive resolution. The other two did not: E3's D7 and E4's H6 are both REFUTED.
- **Imposed cost is not choice.** E5 made a full disrupt-plus-sweep cost one action more (E5-R §J). Because the fixtures do not choose, that cost appeared as one cell of lost core coverage per tick, the same in the contests that kept the privilege and in the exceptions (E5-R §F.2, §F.3). A mechanic meant to create a tradeoff has to be judged against agents that can take either side of it (§G.3).

---

## G. Requirements for the Next V6 Mechanic

These are **design requirements derived from the recorded findings**. They are not hypotheses, thresholds or a pre-registration, and they do not select a mechanic. A design review for any candidate should show how the candidate meets each one, or argue why it need not.

The first genuinely new V6 mechanic should preferably satisfy the following.

### G.1 (A) Create opponent-dependent action value

- **Requirement.** The value of an action should depend materially on what the opponent is doing, so that the best policy against one opponent is not the best against every other.
- **Derived from.** V6's gameplay objective is that agent effectiveness become "genuinely **opponent-dependent**" (Phase 4A §1.2), after a history of strictly transitive races (Phase 4A §1.1). The only opponent dependence E2 created was a deterministic draw-mediated pattern whose draw edge is a stalemate (E2-R §J). E3's secondary residual reading found nothing to count, because the field is saturated by dominance pairings (E3-R §G.6).
- **Would not satisfy it.** Another mechanic in which every agent optimizes the same independent race, only faster or slower.

### G.2 (B) Create a real opportunity cost

- **Requirement.** An agent should have to choose among competing uses of limited actions, for example attack, defense or repair, information or scouting, and investment or expansion. Doing one should genuinely delay or weaken another.
- **Derived from.** E5 is the clue. "Separating disruption from damage made a full disrupt-plus-core sweep cost one more action, and the scripted fixtures, which do not choose, simply lost one cell of core coverage per tick" (E5-R §J). The record names the aim: to make opportunity cost "strategic and selectable, rather than imposed by geometry" (E5-R §J).
- **Would not satisfy it.** A rule that only raises the price of an action every agent must take anyway, whatever the opponent does.

### G.3 (C) Permit adaptation

- **Requirement.** A capable agent should be able to observe enough, directly or by spending actions, to change its policy according to the opponent or the game state. Imposed inefficiency is not strategic decision-making.
- **Derived from.** The surviving privilege is recorded for fixtures that "never choose between disrupting and attacking the core, and never re-contest a cell within a tick" (E5-R §H.8). Information is free and global under the current rules (E3-R §G.7), so no experiment has yet put a price on it.
- **Implication for evaluation.** A mechanic whose value lies in a choice can only be shown by agents that make the choice. Judged only against the frozen scripted fixtures, its cost would register the way E5's did: as lost coverage, not as a decision. How choosing agents are supplied belongs to the mechanic's own design review (§H).

### G.4 (D) Preserve interaction

- **Requirement.** The mechanic should not reach "balance" mainly by eliminating contact, creating immunity or pushing matches toward the tick limit.
- **Derived from.** Separation raised PF-2 (stasis) and PF-3 (new immunity) (E5-R §D.3). K = 2 added 610 recovery stalemates (E2-R §D.2). K = 2 with λ = 1 makes continuous repairers provably uncapturable (E3-D9 SUPPORTED; E4-D9′ and E5-D9 HOLD). Broader context: proportional movement produced large-scale non-contact (Phase 4D). E3 and E4 show that the cost can be avoided, since neither draw-ified (E3-D7 and E4-H6 REFUTED).
- **Implication for evaluation.** E5's practice of recording pathology flags "whatever else holds" (stasis, new immunity, loss of interaction, seat artifacts) is the recorded precedent.

### G.5 (E) Affect strategic topology, not merely termination timing

- **Requirement.** Prefer changes that alter matchup relationships and counterplay, meaning who beats whom and why, over changes that turn captures into score wins, or wins into ties, while the same winner remains.
- **Derived from.** Separation lost 190 captures and reversed no winner; 126 of those cells became tick-limit wins for the same seat (E5-R §F.7). Mirrored order changed no F1 outcome class (E4-R §F.5). E2's most common change was the same winner one tick later (E2-R §D.2). The research lead's summary of E5: "longer versions of the same competitive ordering" (E5-R §I).
- **Would not satisfy it.** A mechanic judged mainly by the balance of capture versus score resolution.

### G.6 (F) Remain explainable

- **Requirement.** The mechanic should remain comprehensible enough that agent authors can reason about it, the Designer can expose it, replay visualization can make it visible, and research tooling can measure it.
- **Derived from.** Every E2–E5 effect needed a new instrument before it could be seen: phase lock, FMS and PD, FMA and FPS, BP. Inherited instruments misled on these fields. Twin-mirror SDI turned out to be 1.0 by construction on every decisive seed (E3-R addendum). E2's pre-registered residual procedure also counted residuals in the V4 control, so it could not separate treatment from control (E2-R §G.3, a supplementary reading). Even a capture-timing change needed an attribution refinement to keep captures credited to their capturer (E2-R §A). Under the engine/replay separation (§I.3), a mechanic's state reaches frontends only as recorded replay facts.
- **Would not satisfy it.** Effects visible only to a bespoke analyzer, or state that replays do not record.

### G.7 (G) Be independently testable

- **Requirement.** Introduce one new strategic dimension at a time, with clean control and treatment semantics, controls that reproduce their parent byte for byte, and no simultaneous redesign of the engine.
- **Derived from.** Every E2–E5 conclusion rests on one-field treatments against byte-identical parents (§C.1). The costliest problems in the line were confounds inside the instrument:
  - the K × λ immunity, which needed a companion arm to separate (E3-R §F.5);
  - interpretation rows that could overlap or fail to fire, closed by two blind amendments in E4 (E4-R §E.1) and a row redesign in E5 (Revision 1 §R6);
  - fixtures whose targeting encoded the very variable under test, which sent E5's first design back for redesign (ROADMAP, E5 entry).

  Where a new mechanic interacts with an existing variable such as K, a companion arm or a registered masking limitation is needed (E4-H4).

### G.8 Measurement lessons the next pre-registration inherits

These are recorded lessons, not new metrics:

- Most fixtures are deterministic, so most units rest on one trajectory. Report n_distinct beside every count (all four records).
- Analyse mirrors at the seed level, and treat relabel identity as a gate, not a metric (E3-R addendum).
- Rating-residual significance saturates on dominance pairings (E2-R §G.3; E3-R §G.6).
- A negated hypothesis in an interpretation row means REFUTED, so a `NEITHER` can leave a row unfired. Every status combination needs exactly one row (E4-R §E; Revision 1 §R6).
- Design-review probes missed some predictions in every experiment, at the verdict level, the unit level or both (E2-R §I, E3-R §F.9, E4-R §F.8, E5-R §F.9). A probe is not a substitute for a registered run.

---

## H. Candidate Research Branches

E5-R §J names two branches, first set out in the E5 design review's §P for an H2 reading. **Neither is registered here.** Each would need its own scope decision, design review and pre-registration (E5-R §J).

### Branch A — Policy-space study

- **Question.** Do the current rules contain strategic depth that the scripted fixtures do not expose? It would study adaptive or searched agents under the current rules.
- **Why it is legitimate.** Every E2–E5 finding is scoped to scripted fixtures that never choose and never re-contest a cell within a tick (E5-R §H.8). The E5 design review's untested inference is that a defender that repaired its base with its final in-tick action "would own it in both roles" (E5-DR §P). Nothing in E2–E5 tests or refutes that. **Branch A has not been disproven.**
- **What it would not do.** Change the rules.

### Branch B — New economic or opportunity-cost mechanic

- **Question.** Does a minimal mechanism that creates selectable tradeoffs between uses of an action (attack, defense, investment) create opponent-dependent choice?
- **Why it follows from the record.** The imposed extra cost in E5 became lost coverage because nothing chose (§G.2). Branch B supplies the choice.
- **What it inherits from §G.3.** A Branch B mechanic still needs agents that exercise its choice before its value can be measured.

### The current direction

The research lead's current direction, as given for this synthesis:

> **Cross-experiment synthesis first, then investigate the economic/action-choice branch.**

The committed records state the same direction in their own words. E5-R §J: "The research lead's stated direction is the second, preceded by the synthesis." The ROADMAP's E5 entry: "a cross-experiment synthesis of E2–E5, followed by a pivot to a mechanic that makes the choice between uses of an action (attack, defense, investment) strategic; neither is registered yet".

This document is the first step. The second has not started, no mechanic has been selected, and nothing is registered. Branch A remains a legitimate future alternative.

---

## I. Relationship to the Broader V6 Program

### I.1 "Bytefray goes on a diet and a makeover"

V6's guiding rule is "Delete before refactoring; refactor before redesigning; measure before changing gameplay" (ROADMAP; Phase 0 §14). Phases 1–2 were the diet: they retired obsolete execution paths, runtimes and tooling. Phase 3 decomposed the largest evaluation module, as part of the architecture makeover. E2–E5 is the gameplay "measure" step: four controlled measurements of the stable-V4 forced line, none of which promoted a rule.

Phase 0 asked, as its default null hypothesis, whether there is "any evidence-backed need for a gameplay change at all right now" (Phase 0 §12), and its charter designs no mechanic until a research question produces that evidence (§13). E2–E5 found that none of four single-field changes aimed at the forced line and what it left behind is ready to become a gameplay rule (§F). Whether that, together with the forced line itself, justifies a new mechanic is for Branch B's scope decision to argue. This synthesis is the evidence summary that decision can cite.

### I.2 Earlier catalogued ideas, read against E2–E5

*Each reading is a synthesis reading, not a decision. Nothing here designs a Ruleset.*

| Idea | Where catalogued | Reading after E2–E5 |
|---|---|---|
| Replication and deployment economics | FUTURE_PLANS, "Replication / deployment"; Phase 0 §12, question 3 | **More promising.** It is directly an attack-versus-investment choice (§G.2), and E5-R §J names it as the closest catalogued idea. One caution from the record: extra locations were an exploit under whole-tick denial (E2-R §J) and stopped paying once denial ended (E3-D5). A deployment mechanic has to price locations, not hand them out. |
| Agent lifecycle: mutation, evolution and replication economics | FUTURE_PLANS; Phase 0 §12, question 4 | **Split.** "Controlled replication economics" belongs with the row above. Offline evolution and online adaptation are ways of producing agents that choose, which is closer to Branch A than to a Ruleset mechanic. |
| Investment and expansion: the greed / rush / defense triangle | Phase 4A §11.5 | **The goal survives; its proposed route does not.** §11.5 expected spatial scale and bounded reach to reopen the setup window, and that line is closed (§D.2). E2 showed that delaying capture by one tick does not by itself create a strategic setup window. A triangle would have to come from the tradeoff itself (§G.2). |
| Information and scouting cost | FUTURE_PLANS, fog of war; Phase 0 §12, question 6; Phase 4A §11.4 | **Promising as a priced choice, not as a cap.** Free global information is an unexcluded upstream cause (E3-R §G.7), and paying actions to learn fits §G.2–§G.3. A simple hard reach cap is not resurrected (the bulldozer effect, §D.2). |
| Special or valuable memory locations | Phase 4A §11.1 | **More promising in a contestable, valuable form than in an immutable one.** Cells worth fighting over create opponent-dependent value (§G.1). Indestructible cells create immunity, which §G.4 argues against. |
| Later anti-stasis mechanisms: shrinking arena, environmental sweep, territory decay | Phase 4A §11.2–§11.3 (research stage 5); FUTURE_PLANS, "Territory maintenance / memory decay" | **Later, not first.** They act on how matches end, which §G.5 says is not the primary target. Stasis also proved specific to the intervention (E2-H3a and E5 PF-2 against E3-D7 and E4-H6). They may matter once a mechanic with real choices exists. |
| Bounded environment variation | No committed catalogue entry at `cb91471` | **Secondary.** Seeded placement already varies geometry, yet most fixtures are deterministic by design, so seeds are not independent trials (E2-R §C). Variation adds trajectory diversity, but by itself it creates no choice (§G.2). If pursued, it should stay bounded, so that it remains explainable (§G.6). |
| Execution-trace and intent semantics | FUTURE_PLANS; Phase 0 §12, question 5 | **Not addressed by E2–E5.** Unchanged. |

**Not resurrected:**

- giant arena scaling;
- proportional movement;
- simple hard reach-cap fog;
- anchor-before-core as a product rule.

Each is closed by the records cited in §D and §F.

### I.3 The replay and UI track is separate

V6 also has a product and UI "makeover" direction, which the research lead has described as including replay activity visualization. It is a separate track from gameplay research.

- **No design exists yet.** At `cb91471` no committed design record for it exists, and this synthesis neither designs nor implements it.
- **Its bar is already set.** Phase 0's charter says Designer and Replay Viewer changes follow evidence of a real gap (Phase 0 §13).
- **The architecture already separates the two tracks.** ARCHITECTURE.md records that engine execution never reads a replay back, and that replay consumption never re-executes an agent. This synthesis states the principle as:

> **The engine produces authoritative match/replay facts; replay analysis and frontends derive and visualize those facts independently.**

Its only relevance to gameplay research is §G.6. A new mechanic's state and events must be recorded as replay facts, additively where possible (Phase 4A §14.3). Analysis tooling and any frontend can then derive and show them without re-running the engine or depending on a particular frontend.

---

## J. Decision Boundary

- **The E2–E5 forensic work is closed.** Capture hold, disruption duration, pass order and spatial co-location have each been tested once, under frozen instruments (E5-R §I).
- **There is no E5.1.** The four exceptions remain registered exceptions, unexplained.
- **No new scheduler, anchor or capture forensic experiment follows from this synthesis.**
- **This synthesis creates no experimental result.** It changes no verdict, interpretation, threshold, population or record, and it reads no corpus.
- **No Ruleset is created, changed or promoted.** All seven E2–E5 research Rulesets remain research-only and resolvable, as their registrations' permanent obligations require.
- **Any new mechanic requires a separate design review and pre-registration**, after a scope decision and before any implementation.
- **Nothing is registered here.** Neither branch in §H is registered, and the next mechanic is not selected.

---

## What this synthesis does not claim

- **No proof.** `R-H2-PRIME` *supports* the second response in the opening exchange as the remaining mechanism. It does not prove it, and four sweep-backed contests are registered exceptions.
- **No refutation of any `NEITHER`.** E3-D1 and D8, E4-H2 and H7, and E5-H1, H4 and H5 keep their frozen status.
- **No mechanism for the four exceptions.**
- **No rate claim** from a value resting on fewer than 8 distinct trajectories.
- **No universal claim** about Bytefray agents or strategy. Every result is scoped to the frozen fixtures and parameters of its record.
- **No claim that any E2–E5 mechanism has no effect.**
- **No new calculation.** Every figure is copied from a cited record, and no comparison was computed.
- **No product decision** beyond what the records already carry: E5's recommendation against promoting `before_core`.
- **No selection or registration** of the next mechanic.

---

## Appendix. Sources

**Authoritative results records** (`docs/research/v6/`):

- [`V6_E2_CAPTURE_HOLD_RESULTS.md`](V6_E2_CAPTURE_HOLD_RESULTS.md)
- [`V6_E3_SLOT_LIMITED_DISRUPTION_RESULTS.md`](V6_E3_SLOT_LIMITED_DISRUPTION_RESULTS.md), with its 2026-09-24 addendum
- [`V6_E4_MIRRORED_PASS_ORDER_RESULTS.md`](V6_E4_MIRRORED_PASS_ORDER_RESULTS.md)
- [`V6_E5_ANCHOR_CORE_SEPARATION_RESULTS.md`](V6_E5_ANCHOR_CORE_SEPARATION_RESULTS.md)

**Registrations** (the registered questions):

- [`V6_E2_CAPTURE_HOLD_REGISTRATION.md`](V6_E2_CAPTURE_HOLD_REGISTRATION.md)
- [`V6_E3_SLOT_LIMITED_DISRUPTION_REGISTRATION.md`](V6_E3_SLOT_LIMITED_DISRUPTION_REGISTRATION.md)
- [`V6_E4_MIRRORED_PASS_ORDER_REGISTRATION.md`](V6_E4_MIRRORED_PASS_ORDER_REGISTRATION.md)
- [`V6_E5_ANCHOR_CORE_SEPARATION_REGISTRATION.md`](V6_E5_ANCHOR_CORE_SEPARATION_REGISTRATION.md)

**Design reviews** (framing only):

- [`V6_E2_CAPTURE_HOLD_DESIGN_REVIEW.md`](V6_E2_CAPTURE_HOLD_DESIGN_REVIEW.md)
- [`V6_E3_SLOT_LIMITED_DISRUPTION_DESIGN_REVIEW.md`](V6_E3_SLOT_LIMITED_DISRUPTION_DESIGN_REVIEW.md)
- [`V6_E4_ORDER_VS_EVALUATION_TIMING_DESIGN_REVIEW.md`](V6_E4_ORDER_VS_EVALUATION_TIMING_DESIGN_REVIEW.md)
- [`V6_E5_ANCHOR_CORE_SEPARATION_DESIGN_REVIEW.md`](V6_E5_ANCHOR_CORE_SEPARATION_DESIGN_REVIEW.md)
- [`V6_E5_DESIGN_REVIEW_REVISION_1.md`](V6_E5_DESIGN_REVIEW_REVISION_1.md)

**Execution and freeze records** (provenance, not read for new facts): [`V6_E2_EXPERIMENT_FREEZE.md`](V6_E2_EXPERIMENT_FREEZE.md), [`V6_E2_MATRIX_EXECUTION_HALT.md`](V6_E2_MATRIX_EXECUTION_HALT.md), [`V6_E2_ANALYSIS_FREEZE_V2.md`](V6_E2_ANALYSIS_FREEZE_V2.md), [`V6_E3_EXPERIMENT_FREEZE.md`](V6_E3_EXPERIMENT_FREEZE.md), [`V6_E4_EXPERIMENT_FREEZE.md`](V6_E4_EXPERIMENT_FREEZE.md), [`V6_E4_ANALYSIS_FREEZE_V2.md`](V6_E4_ANALYSIS_FREEZE_V2.md), [`V6_E4_ANALYSIS_FREEZE_V3.md`](V6_E4_ANALYSIS_FREEZE_V3.md), [`V6_E5_EXPERIMENT_FREEZE.md`](V6_E5_EXPERIMENT_FREEZE.md).

**Broader V6 context:**

- [`V6_PHASE0_BASELINE.md`](V6_PHASE0_BASELINE.md)
- [`V6_PHASE4_GAMEPLAY_RESEARCH_METHODOLOGY.md`](V6_PHASE4_GAMEPLAY_RESEARCH_METHODOLOGY.md) and its Research Integrity Addendum (2026-09-22)
- [`V6_PHASE4B_ARENA_SCALING_STUDY.md`](V6_PHASE4B_ARENA_SCALING_STUDY.md), [`V6_PHASE4C_MOVEMENT_NORMALIZATION_STUDY.md`](V6_PHASE4C_MOVEMENT_NORMALIZATION_STUDY.md), [`V6_PHASE4D_PROPORTIONAL_MOVEMENT_STUDY.md`](V6_PHASE4D_PROPORTIONAL_MOVEMENT_STUDY.md), [`V6_PHASE4E_TERRITORY_SCORING_STUDY.md`](V6_PHASE4E_TERRITORY_SCORING_STUDY.md)
- [`docs/ROADMAP.md`](../../ROADMAP.md) and [`docs/FUTURE_PLANS.md`](../../FUTURE_PLANS.md)
- [`ARCHITECTURE.md`](../../../ARCHITECTURE.md)
