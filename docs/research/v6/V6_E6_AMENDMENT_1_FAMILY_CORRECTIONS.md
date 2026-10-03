# Bytefray V6 E6 — Amendment 1: Pre-Freeze Family Corrections

**Status: APPROVED by the research lead at Checkpoint A, 2026-09-25.** This amendment corrects the *implementation* of the registered E6 family before the family becomes an experimental object. It bundles three corrections into one amendment and one re-freeze (v2). When they were corrected, **no E6 seed set, execution matrix identity, matrix cell (control or treatment) or outcome probe existed**, and no family member had played under a treatment Ruleset.
**Branch:** `v6-research`
**Date:** 2026-09-25
**Governing records:**
- [pre-registration](V6_E6_PRICED_SENSING_PREREGISTRATION.md) (**PR**);
- [implementation plan](V6_E6_PRICED_SENSING_IMPLEMENTATION_PLAN.md) (**plan**), whose §5.2 this amendment corrects;
- [design review](V6_PRICED_SENSING_DESIGN_REVIEW.md) (**DR**);
- [implementation record](V6_E6_IMPLEMENTATION_RECORD.md), which carries the identities, evidence and counts.

The PR, the plan and the DR are not edited. This amendment carries the corrections, and the fixture README records the corrected specification.

---

## 1. What This Amendment Does Not Change

None of the three corrections changes any of the following:
- the registered research question;
- the hypotheses E6-H0 to E6-H3, their thresholds, or the tolerance, bootstrap and tick bound (O-3 to O-5);
- the interpretation table, the pathology flags or the kill criteria;
- the four conditions, their Rulesets, the two fields, the counts or the seed protocol;
- the nine members as conceptual members: each keeps its registered parameter setting, package and opaque ID;
- the analysis instrument: no analyzer, gate, telemetry, re-derivation or trace-method change.

They correct how the one shared policy source implements plan §5.2, which the PR adopts as the family's parameter semantics (PR §3.1).

## 2. How the Defects Were Found, and Why They Block

At the first Checkpoint A review, the research lead required P-6 to be refined (correction C-1). While qualifying that refinement, the new **engine-level behavior tests** found two more defects: the family played against scripted, non-family opponents under the two control Rulesets only, with its actions asserted and no outcome recorded. The I-3 tests had driven the policy with hand-built observations, which cannot show how the policy interacts with the engine's own write semantics.

Each defect can change which registered interpretation fires:
- **C-1:** a control-only, seat-dependent false core inference against EVADER. It feeds E6-H1C (the control best-response topology), E6-H0 and the pathology flags.
- **C-2:** under the treatment, every attacker but STEALTH could find a stationary core but never confirm it. Under the refined P-6, the same held for every Seat B attacker under the controls. It feeds E6-H1T, E6-H1C, E6-H3 (KC-4) and KC-5 (seat artifact).
- **C-3:** an attacker that also disrupts an off-core anchor never wrote core cell 7, and SPLIT never wrote cell 7 at all. EVADER was therefore uncapturable once moved, and SPLIT could capture nothing. It feeds E6-H1C, E6-H1T, E6-H3 ("the evasive one included") and SPLIT's registered role.

## 3. The Corrections

### C-1. P-6: unverified adoption only by the first mover, on tick 1

- **Before:** at the entrant's first callback, one visible anchor at circular distance ≥ 64 from its own core base is adopted as the enemy core base.
- **After:** the same, but only on the **tick-1 first callback of the entrant scheduled to move first, before the opponent could have acted**. Under every E6 Ruleset that is **Seat A**: chunk 2, the start rotated by (tick − 1) mod 2, and seat order equal to scheduler order. A test pins this premise under all four E6 Rulesets.
- **Why:** under the controls, a Seat B attacker whose first callback came after EVADER's first-callback MOVE adopted the moved anchor and never revised it. The refinement keeps what P-6 was for, the parent's canonical Seat A tick-1 forced line, which is unchanged callback for callback. It stays inert under the treatment, where nothing farther than 32 cells is visible at a first callback. EVADER keeps evading immediately: the unsafe inference is corrected, not evasion.

### C-2. Verification: anchor + 1 sampling and eight-cell confirmation

- **Before:**
  - READ at a stride of 8 across [*a* − 64, *a* + 64], starting at the last-known anchor *a*;
  - after the first hit, READ downward until a miss;
  - the base is the last hit.
- **After:**
  1. **Sampling.** The 17 verification READs are *a* + 1, *a* + 1 − 8, *a* + 1 + 8, …, *a* + 1 − 64, *a* + 1 + 64. This is the stride-8 lattice through the cell one past the anchor, covering [*a* − 63, *a* + 65].
  2. **The run.** A hit (an applied READ of `0xCE` owned by the opponent, unchanged) starts a run of contiguous enemy beacons. The run is grown downward until a cell is not a beacon, then upward until a cell is not a beacon, and stops as soon as it holds eight cells.
  3. **Confirmation.**
     - **Eight cells.** Eight contiguous enemy beacons are the core; the lowest is the base. The anchor is not used.
     - **Seven cells.** Exactly seven beacons are the core only if the cell immediately below them is an **enemy anchor address this entrant has written** and a READ of it shows the entrant's own **applied** write. That written anchor then stands in for core cell 0 and is the base.
     - **Otherwise** the core stays unconfirmed, and verification goes on with the window.
- **Why the sampling changed:** the attack's first priority is to WRITE every visible enemy anchor. A stationary anchor sits on core cell 0, and at stride 8 it was the only lattice point inside the core. So the disruption erased the one sample that could confirm the core. In the engine, a Seat B attacker's READ of that cell returned its own write. Over 40 ticks it made 265 READs, none of which returned the enemy's `0xCE`, and it never wrote cells 1–7.
- **Why the confirmation rule is explicit:** once overwritten, an anchor cell cannot be read, so two cases must be told apart:
  - an anchor **on** core cell 0 leaves seven intact beacons directly above it, and the anchor is the base;
  - an anchor **one cell below** the core leaves eight intact beacons, and the base is the cell above it.

  Counting the written anchor as a beacon would give the second case the wrong base, so it is not done. Each case is pinned by a synthetic test and by an engine test.
- **One point to review:** the research lead's text names "the last-known anchor" as the stand-in. The implementation accepts **any** enemy anchor address this entrant has written and still holds. The family's last-known anchor is the lowest visible address (fixed detail 1). A treatment attacker that sees both of SPLIT's anchors, with the sensor below the striker, would therefore never confirm SPLIT's core under the narrower wording. A synthetic test pins that case. The two-case analysis above is unchanged by this widening.
- **Scope of the rule:** one case remains that the rule does not tell apart. If an anchor stood directly **below** a core whose **top** cell the entrant already held, seven beacons would sit above a written anchor, and the anchor would be taken as the base. That needs an anchor one cell below its own core, which no family member can produce:
  - stationary anchors sit on core cell 0;
  - the searchers' anchors sit at base ± 64*k*;
  - an evasion moves an anchor by 8 to 64 once.

  ADAPT evades only after detecting damage, and detected damage permanently rules out its switch to hunting, so ADAPT never combines the two. (This corrects the Checkpoint A report, which named such an ADAPT corner.)

### C-3. Attack: a cyclic core cursor

- **Before:** when the core is known, WRITE "the first cell, in base order, not yet written this tick" (fixed detail 7, chosen at I-3).
- **After:** WRITE the core cell at a **cyclic cursor over cells 0–7**. The cursor is:
  - carried across ticks;
  - advanced past a cell only when that cell's WRITE is chosen;
  - skipping cells already written this tick.
- **What it does not change:** a disruption still costs one of the eight offers. A single-process attacker that disrupts an off-core anchor writes seven core cells that tick, as before. The cell it omits now rotates from tick to tick instead of always being cell 7.
- **Why:** the old order restarted at cell 0 every tick, so cell 7 was never written whenever a slot went elsewhere. That happened in two cases:
  - an off-core anchor, as after an evasion;
  - SPLIT, whose striker has 6 of the 8 offers.

  Neither could ever be captured. The tick-1 forced line is unchanged: the anchor is written as cell 0, and the cursor then writes cells 1–7 in order.

## 4. The Fixed Details (fixture README)

- **Changed:** fixed details 2 (verification order), 4 (base finding) and 7 (the next core cell), and the note on P-6.
- **Clarified:** detail 3 (an exhausted window). A run that ends unconfirmed does not exhaust the window.
- **Unchanged:** the other eleven.

## 5. Identities

- **v1 is superseded before exposure.** Analysis freeze `v6-e6-freeze-v1-428033032ce2` and structural matrix `v6-e6-matrix-v1-cd040eac42ef` never received seeds or data. The v1 record stays byte for byte at `tools/research/v6/e6/analysis_freeze.json` as historical evidence.
- **v2 is operative.** The structural matrix identity becomes `v6-e6-matrix-v2-<first 12 hex of the structural digest>`, and the analysis freeze becomes freeze v2, recorded in `tools/research/v6/e6/analysis_freeze_v2.json`. The freeze v2 identity names the record it supersedes.
- **The execution identity keeps its registered scheme** (`v6-e6-exec-v1-<first 12 hex of X>`, PR §9). None has been computed. The first one will bind the v2 structural digest.

**Next:** the research lead's review of the v2 family and freeze at Checkpoint A. Seed generation (I-7), the controls and the treatment each still need separate authorization.
