# Bytefray V6 E5 Design Review — Revision 1: Decisions, Corrections and Exact BP Specification

**Date:** 2026-09-24.

**Layering.** This revision sits on top of `V6_E5_ANCHOR_CORE_SEPARATION_DESIGN_REVIEW.md`, which stays unchanged as delivered. The revision records the research lead's decisions and corrections, gives the exact BP mathematics, and closes one further pre-freeze ambiguity (§R6).

**State when written.** No E5 code, Ruleset, tooling, pre-registration or data exists, and the repository is unchanged at `ecf2769`.

**Disposition.** The practical verdict moves from REDESIGN to **GO for E5 implementation and pre-registration**. **Treatment execution is not authorized.**

---

## R1. Decisions (all five approved)

1. **Offset.** `initial_anchor_placement = "before_core"` means exactly `(core_base − 1) % arena_size`. The mode set is closed; no general integer offset is exposed.
2. **Exclusions.** `v4_probe`, `e3_jam_sniper`, `e2_greedy_painter` and `e2_counter` are excluded. The analyzed field is `e2_sniper`, `e2_min_guard`, `e2_disrupt_guard`, `e2_repair_guard`, `e2_guarded_painter`, `e2_spread_sniper` and `e2_spread_defender`.
3. **Primary instrument.** BP is primary, with aggregation and bands fully defined (§R5).
4. **Companion.** The K = 1 companion is kept, because E4 showed K = 2 can absorb large internal effects.
5. **Offset-aware copies.** They are **test-only gate instruments** for P5 (inertness). They never enter the matrix, the populations, the analysis or any reported E5 gameplay result.

---

## R2. Correction 1 — E5-D tests the manipulation, not a gameplay outcome

This replaces the review's §K E5-D and §L gate 11. The requirement "every AO unit neutral" is **removed**. Later contact from painting fronts is independent, legitimate gameplay and must not stop the experiment. AO treatment BP is reported as a characterization only.

**E5-D — Decoupling manipulation gate.** Every clause is a hard STOP, and no clause reads a gameplay outcome.

| Clause | Evaluated on | Exact condition | Kind |
|---|---|---|---|
| **D-1 Spawn** | every T-E5 and T-E5K1 cell, tick-0 snapshot | every process anchor equals `(pc_e − 1) mod 512` for its entrant e, and no tick-0 anchor lies in any entrant's core | Ruleset invariant |
| **D-2 No dual default-anchor write** | every T cell, every tick | 0 hostile writes to an address that is both (i) the tick-0 anchor of a still-unmoved process of victim V and (ii) a cell of V's core | Ruleset invariant (follows from D-1) |
| **D-3 DUAL, any occupied anchor** | every T cell, every tick | 0 hostile writes, by X in tick t to address a, with a ∈ core_V and a ∈ {anchor_p(t−1), anchor_p(t)} for some live process p of V ≠ X | **E5-corpus characterization** |
| **D-4 Own-core occupancy** | every T cell, every tick boundary | no process's anchor lies in its own entrant's core | **E5-corpus characterization** |
| **D-5 AO contact removed** | every AO directed unit | *control* (checked before treatment): every DEFINED control cell has ≥ 1 D-2-type write by the attacker to the victim's cell 0, so the anchor-induced contact existed; *treatment*: 0 such writes | manipulation, per contest |
| **D-6 Sensitivity** | C-E5 and C-E5K1 (checked before treatment) | the D-3 count is > 0 in every cell with ≥ 1 hostile write to an unmoved enemy process's anchor | instrument sensitivity |

**Operational notes.**

- **"Unmoved at tick t"** means the process's anchor equals its tick-0 anchor at every snapshot 0 … t−1.
- **Why D-3 uses two boundaries.** Replays store anchors only at tick boundaries, and a MOVE is atomic. So {anchor(t−1), anchor(t)} contains every position the process held during tick t, and D-3 is a conservative superset of the true DUAL count. The gate therefore needs no "ambiguous" category.
- **Descriptive counts are different.** For descriptive anchor-hit counts, a write made in a tick in which the victim moved stays AMBIGUOUS.

---

## R3. Correction 2 — Ruleset invariant versus E5-corpus characterization

**Ruleset semantics of `"before_core"`** concern **default spawn only**:

- Every process whose declaration has no explicit position spawns at `(core_base − 1) mod A`.
- Nothing restricts movement. A process that later MOVEs onto its own core is legal. An enemy WRITE there then both disrupts it and flips that core cell, exactly as under `"core_base"`.
- The **spawn-validity guard** rejects, at match start, any layout in which a default spawn lies inside any entrant's core. It is a spawn check only.

**E5-corpus characterization:**

- D-3 (DUAL = 0) and D-4 hold for the seven fixtures, because none of them moves onto its own core. Only the spread movers move: once each, by ±16–64 from `base − 1`.
- Gate records and the results record label these clauses as corpus characterization, not as Ruleset semantics.

**Required test.** Under `"before_core"`, a scripted process MOVEs onto its own core cell. An enemy WRITE to that cell then disrupts it and flips the cell's ownership, a DUAL write. This proves the Ruleset carries no hidden movement prohibition.

**Wording.** The policy docstring, the registration note and the ROADMAP say "default spawn is off-core". They never say "processes are never on their core".

**Amended in the review:**

- §F P2 keeps the spawn part as the invariant. The movers' positions become a characterization.
- §F P4 is restated as: DUAL = 0 is a characterization of the E5 fixture set, and D-2 is the Ruleset-level guarantee.
- §L gate 10 becomes D-1 (invariant) plus D-4 (characterization).

---

## R4. Correction 3 — H2 claims only what E5 manipulates

The H2 reading adopts the lead's wording (the logical form is corrected in §R6):

> **Co-location is not necessary for the directed base privilege.** Removing the dual-purpose anchor/core write leaves the SB privilege intact. Combined with E4's finding that the OPENING-ONLY privilege survives mirrored later-pass order, this supports the second response in the opening exchange as the remaining mechanism. The anchor/core forensic line closes.

The H1 reading is restated in the same register:

> **Removing the dual-purpose anchor/core write weakens or removes the SB base privilege: co-location is load-bearing for it.** Separation becomes a candidate rule change; H4, H5 and the pathology flags describe its costs.

---

## R5. Exact BP specification (O-BP)

This replaces the review's §J BP row and the "thirds" prose in §K. Wherever an E4 convention exists it is reused unchanged, and E4's frozen module is named.

### R5.1 Objects

- **Cell c.** One match: (condition, field, Seat-A agent, Seat-B agent, seed, orientation).
- **Core base b_e.** Entrant e's recorded `pc` in the tick-0 snapshot. It is verified against the seeding diffs exactly as `e4/cell_metrics.py` does. **It is never the anchor.**
- **Base ownership o_e(t) ∈ {0, 1}.** It is 1 iff the owner of b_e equals e after tick t's memory diffs are applied to the tick-(t−1) owner map. That is the same end-of-tick instant that capture evaluation reads.
- **First mover at tick t.** `first_mover_seat(t, 2, rotate_start=True)`: Seat A on odd ticks and Seat B on even ticks.
- **Both-alive tick.** Every entrant is `alive` in the tick-t snapshot. This is E4 `cell_metrics`'s rule, unchanged.
- **P_A and P_B.** The both-alive ticks whose first mover is Seat A, and those whose first mover is Seat B.

### R5.2 Cell BP (per seed; ticks are never pooled across cells)

The cell is **DEFINED** iff |P_A| ≥ 10 and |P_B| ≥ 10 (E4 `MIN_TICKS_PER_PARITY`, so BP-DEFINED ⇔ FMA-DEFINED). Otherwise it is **DECIDED_EARLY**.

Victim A moves second on P_B ticks:

```
BP_A(c) = Σ_{t∈P_B} o_A(t) / |P_B|  −  Σ_{t∈P_A} o_A(t) / |P_A|
```

Victim B moves second on P_A ticks:

```
BP_B(c) = Σ_{t∈P_A} o_B(t) / |P_A|  −  Σ_{t∈P_B} o_B(t) / |P_B|
```

- **Arithmetic.** Exact `Fraction`s, with range [−1, 1].
- **Sign.** +1 means the victim owns its base at every both-alive tick on which it moves second and at none on which it moves first. Positive values favour the victim's second-mover role.

### R5.3 Units and unit values

- **F1 directed unit:** (F1, Seat-A agent, Seat-B agent, victim seat v).
  - Each orientation is its own ordered matchup (E4 O-UNIT).
  - One pairing therefore yields up to four directed units.
- **F2 mirror directed unit:** one unit per twin mirror, following E4's convention (candidate-first orientation cells, with seeds as the observations).
  - Cell value = (BP_A(c) + BP_B(c)) / 2.
  - Both values share P_A and P_B, so they are DEFINED together. This is open choice O-1.
- **Unit status** follows E4's `fma_summary` rule.
  - The unit is **DECIDED-EARLY** iff it has no DEFINED cells, or 2 × (DEFINED cells) < (cells).
  - Otherwise it is **DEFINED**, with BP_unit = `statistics.median` over the DEFINED cell values: an exact `Fraction`, and for an even count the mean of the two middle values.
- **n_distinct.** The number of distinct (control `trajectory_key`, treatment `trajectory_key`) pairs over the unit's seeds, using `harness.trajectory_key` unchanged. Rate claims need n_distinct ≥ 8.

### R5.4 Bands

The bands are exact, and each edge is closed on the side away from neutral, as in E4's `fma_band`.

| Band | Condition | Side | Strength |
|---|---|---|---|
| second-strong | BP ≥ 2/3 | second | 2 |
| second-moderate | 1/3 ≤ BP < 2/3 | second | 1 |
| neutral | −1/3 < BP < 1/3 | none | 0 |
| first-moderate | −2/3 < BP ≤ −1/3 | first | 1 |
| first-strong | BP ≤ −2/3 | first | 2 |

- **Rationale.** BP is a difference of two proportions, and the bands are equal thirds of its half-range [0, 1]. They are fixed before any E5 data exist, and no probe or corpus value was used.
- **Naming.** Bands are named by the victim's role (moving second or first in the tick), not "last", so they stay unambiguous.
- **Boundary proximity.** A unit whose BP_unit lies within 1/50 of ±1/3 or ±2/3 in either arm is flagged, and its class stands as computed (E4 P-2 practice).

### R5.5 Transition classes

Precedence is the order listed. The classes partition all directed units.

1. **DECIDED-EARLY.** The control or the treatment unit is DECIDED-EARLY.
2. **FIRST-SIDE-CONTROL.** The control side is first.
3. **UNCHANGED-NEUTRAL.** Control neutral, treatment neutral.
4. **NEW.** Control neutral, treatment non-neutral.

The remaining classes apply when the control side is second:

5. **NEUTRALIZED.** The treatment band is neutral.
6. **FLIPPED.** The treatment side is first.
7. **STAYS.** The treatment band equals the control band.
8. **WEAKENED.** The treatment side is second with lower strength (strong → moderate).
9. **STRENGTHENED.** The treatment side is second with higher strength (moderate → strong).

This is E4's `transition_class` structure, with FOLLOWS-FINAL renamed FLIPPED: E5 changes no final chunk.

### R5.6 Population and contest classification

- **P-BASE.** Directed units whose control unit is DEFINED with side second, i.e. BP_C ≥ 1/3. This replaces the review's "≥ 1/2" (open choice O-3).
- **Sweep role.** This is `writes_enemy_non_base` from E4's `SOURCE_ROLES`:
  - True for the sniper, min guard, spread sniper and spread defender;
  - False for the disrupt guard, guarded painter and repair guard.
- **Classes:**
  - **SB (sweep-backed).** The attacker has a sweep role, *and* its capture-analyzer `CoreInference` for the victim has status `inferred` with `correct = True` in **every** control cell of the unit.
  - **AO (anchor-only).** The attacker has no sweep role, *or* its status is `not_inferred` in **every** control cell.
  - **MIXED-INFERENCE.** Anything else, including any `ambiguous` status or a mix of statuses. These units are reported and excluded from H1 and H2 (open choice O-5).
  - **Twin mirrors.** A mirror is SB iff the fixture has a sweep role and inferred the other's core in every cell, in both directions.
- **Freezing.** Classes are assigned from control data before treatment. The rule's code and the output table are pinned by digest. N_SB is frozen and published before treatment.

### R5.7 Census criteria

Let N be the number of SB units in P-BASE, with DECIDED-EARLY units included.

| Hypothesis | Census value | SUPPORTED iff | REFUTED iff | Otherwise |
|---|---|---|---|---|
| H1 | (NEUTRALIZED + WEAKENED + FLIPPED) / N | value ≥ 2/3 | value ≤ 1/10 | NEITHER |
| H2 | (STAYS + STRENGTHENED) / N | value ≥ 2/3 | value ≤ 1/10 | NEITHER |

- **Arithmetic.** Exact `Fraction`s; ≥ and ≤ are inclusive.
- **DECIDED-EARLY units** count in N and in neither numerator.
- **Empty census.** If N = 0, both hypotheses are NOT_EVALUABLE.

**Properties** (each asserted by a test):

- the two numerators are disjoint;
- H1 value + H2 value + DECIDED-EARLY share = 1;
- H1 and H2 cannot both be SUPPORTED;
- if either is SUPPORTED, the other's value is ≤ 1/3.

---

## R6. Further pre-freeze defect: the "∧ ¬H1" row can miss (the E4 trap again)

H1 and H2 are complements up to DECIDED-EARLY. So H2 SUPPORTED means H1's value is ≤ 1/3, and that value lands in **NEITHER** whenever 1/10 < H1 ≤ 1/3.

Under the registered semantics "¬H1" means REFUTED. The row `E5-D ∧ H2 ∧ ¬H1` would therefore **fail to fire** in, for example, the case where 24 of 30 SB units STAY and 6 neutralize. The registered outcome would then be "none".

This is exactly how E4's `H1 ∧ H3 ∧ ¬H2` row missed at 2 of 18.

**Corrected interpretation rows.** There is no gap between the rows, and every combination of statuses maps to exactly one row.

| Row | Condition | Registered reading |
|---|---|---|
| **STOP** | E5-D fails | No gameplay reading |
| **R-H2** | E5-D ∧ H2 SUPPORTED ∧ H1 REFUTED | The §R4 H2 reading, verbatim |
| **R-H2′** | E5-D ∧ H2 SUPPORTED ∧ H1 NEITHER | The same reading, qualified: "for a supermajority of SB contests. The units that weakened, neutralized or flipped are named as registered exceptions." The line closes. |
| **R-H1** | E5-D ∧ H1 SUPPORTED ∧ H2 REFUTED | The §R4 H1 reading, with the split between NEUTRALIZED/FLIPPED and WEAKENED reported |
| **R-H1′** | E5-D ∧ H1 SUPPORTED ∧ H2 NEITHER | The same reading, qualified by the named STAYS/STRENGTHENED minority |
| **none** | E5-D passes and no row above applies (both NEITHER, or both REFUTED because most units are DECIDED-EARLY, or NOT_EVALUABLE) | "No registered interpretation row applies" is the registered outcome. The census and the pathology flags are reported. |

The H3 (continuity-only), H4, H5 and PF rows are unchanged, and they are recorded whatever else holds.

---

## R7. Remaining choices for the blind checkpoint

The recommended option is listed first in each case.

| # | Choice | Recommendation | Alternative |
|---|---|---|---|
| O-1 | How to aggregate mirrors | Per-seed mean of BP_A and BP_B, one unit per mirror (E4 convention). In either case, report a seat-disagreement diagnostic: seeds where BP_A and BP_B are non-neutral with opposite signs. | Two directed units per mirror |
| O-2 | WEAKENED in H1's numerator | Keep it (E4 continuity). R-H1's text says "weakens or removes", and the split is reported. | Count only NEUTRALIZED + FLIPPED, with WEAKENED counted in neither numerator |
| O-3 | P-BASE selection edge | BP_C ≥ 1/3, the band edge, as E4's P-PAR used \|FMA\| ≥ 1/2, which was its own band edge. Every selected unit then has a well-defined NEUTRALIZED transition. | The review's ≥ 1/2 |
| O-4 | Small N_SB | Freeze N_SB. If N_SB < 10, the pre-registration states that REFUTED at ≤ 1/10 means zero units. If N_SB < 3, halt before treatment and redesign. | — |
| O-5 | MIXED-INFERENCE units | Exclude them from H1 and H2 and report them | Treat them as AO |

---

## R8. Cross-reference: what changes in the review

| Review section | Change |
|---|---|
| §F P2 and P4 | Split into the Ruleset invariant (spawn) and the E5-corpus characterization (§R3) |
| §I | Selection is BP_C ≥ 1/3, pending O-3 |
| §J (BP row) | Replaced by §R5 |
| §K | E5-D replaced by §R2; H1 and H2 made exact by §R5.7 |
| §L gates 10 and 11 | Replaced by D-1 … D-6 |
| §N | Replaced by the §R6 rows |
| Blueprint tests | Add: the MOVE-onto-own-core test (§R3); BP golden cases, including exact-edge values ±1/3 and ±2/3; partition tests for §R5.5 and §R5.7; a row-gap test in which every feasible (E5-D, H1, H2) status triple maps to exactly one row |
| Blueprint mutation tests | Add: pooling ticks across seeds; taking b_e from the anchor instead of `pc`; the unit DECIDED-EARLY rule off by one (`<` versus `≤`); flipping the closedness of band edges; reading "¬H1" as "not SUPPORTED" instead of REFUTED |

Nothing else in the review changes.
