# Bytefray V6 E3 — Slot-Limited Disruption: Results

**Status:** The full frozen E3 matrix (19,456 matches) has been executed and analyzed under analysis freeze `v6-e3-freeze-v1-506811e78ad8`. The hypotheses are read literally under the frozen pre-registration. This is a research result, not a product decision.
**Branch:** `v6-research`. Controls were generated at `b8ac343`; the treatments were generated and analyzed at `6f0fd3f`.
**Date:** 2026-09-24
**Authority:** [`V6_E3_SLOT_LIMITED_DISRUPTION_DESIGN_REVIEW.md`](V6_E3_SLOT_LIMITED_DISRUPTION_DESIGN_REVIEW.md) (§J hypotheses and interpretation, §K metrics, §M evidence rules); `tools/research/v6/e3/preregistration.json` (frozen criteria and operationalizations); [`V6_E3_EXPERIMENT_FREEZE.md`](V6_E3_EXPERIMENT_FREEZE.md) (the instrument, the control qualification, and the addendum accepting P-1). The Rulesets are recorded in [`V6_E3_SLOT_LIMITED_DISRUPTION_REGISTRATION.md`](V6_E3_SLOT_LIMITED_DISRUPTION_REGISTRATION.md).

This record has three layers, and they are kept apart:

1. **Registered verdicts.** D0–D9 exactly as the frozen criteria evaluate them, including `NEITHER`.
2. **Registered interpretation.** The pre-registered interpretation table, applied as written.
3. **Descriptive synthesis.** What the data establish beyond the registered rules. It is labelled as description, and it is not a pre-registered disposition rule.

## Answer in brief

- **Registered verdicts (primary arm, C-E2 → T-E3).**
  - SUPPORTED: D2 (seat determination decreases), D3 (defense no longer needs disrupt-first), D6 (re-disruption recreates control; through the min guard only), D9 (hold × order immunity).
  - REFUTED: D0 (no structural change), D4 (first-mover control persists), D5 (location exploit), D7 (draw-ification).
  - NEITHER: D1 (parity lock decreases) and D8 (last-mover inversion). The median two-sided parity dependence, 0.714, lies between their thresholds.
- **Registered interpretation. No pre-registered interpretation row applies.** The table specifies conclusions only for D1 ∧ D2, D2 ∧ D8, (D4 ∨ D8) ∧ ¬D2, and D7. D1 and D8 are `NEITHER` and D7 is refuted, so none of the four fires. The registered clean negative ("not load-bearing; the disruption line closes") does not fire either, because D2 is supported.
- **Descriptive synthesis.** Slot-limited disruption clearly removes whole-tick first-mover monopoly and substantially reduces seat determination. It does not eliminate order dependence. The remaining interaction is moderately last-mover-leaning, rather than strongly parity-neutral or strongly last-mover-dominated.
- **Disposition (descriptive, not a registered rule).** **E3 is a successful causal intervention but not a complete gameplay solution.** Whole-tick disruption is load-bearing for first-mover exclusivity and for much of the prior seat determination. Removing it exposes a weaker residual order effect, tied to the last-mover position or to end-of-tick evaluation.

---

## A. Execution provenance

| Item | Value |
|---|---|
| Matrix | `v6-e3-matrix-v1-634132ec3c15` (digest `634132ec…37215e8`), unchanged since the freeze |
| Analysis freeze | `v6-e3-freeze-v1-506811e78ad8`: analyzer version 1, capture analyzer v2, tooling qualified at `d1f69b9`, and the freeze committed at `b8ac343`. Its control qualification was recorded at `8812ffa` before any treatment existed. |
| Pre-registration | `2b5f82b4…cafbdd0`, unchanged. P-1 (D5's unreachable support branch) was accepted as a documented limitation before the treatment ran (`6f0fd3f`); there was no re-freeze. |
| Controls | C-E2 and C-RS, generated at `b8ac343` with a clean tree, 2026-09-24 01:44–02:17 UTC |
| Treatments | T-E3 and T-E3K1, generated at `6f0fd3f` with a clean tree, 2026-09-24 03:00–03:40 UTC. Each field was started through `run_e3 execute … --confirm-matrix-execution --confirm-treatment-execution`, and the full unlock chain passed before it ran. `engine/src` is the frozen tree `67b73c9a…`. The source manifest was identical before and after execution. |
| Analysis | Unmodified `python -m tools.research.v6.e3.run_e3 analyze` at `6f0fd3f`, run after both treatments passed their gates. The output is `runs/research_v6_e3/v6-e3-matrix-v1-634132ec3c15/freezes/v6-e3-freeze-v1-506811e78ad8/e3_analysis.json`, SHA-256 `7bdb11047e6e02b7f0f4bde12ecc5c2746879febb73b13aec253049b20e09fc6`. |
| Environment | Python 3.13.14, `Windows-11-10.0.26120-SP0`, one match worker per condition |
| Retries | None. No cell failed, and no cell was re-run. |
| Artifacts | `runs/research_v6_e3/v6-e3-matrix-v1-634132ec3c15/{C-E2,T-E3,C-RS,T-E3K1}/{F1,F2,F2-P,F4}`: every `result.json` and replay is preserved (git-ignored). |

Nothing in the instrument changed after the treatments ran.

## B. Gates

**Before treatment** ([freeze record](V6_E3_EXPERIMENT_FREEZE.md)):

- **Parent reproduction: FULL PASS.** 7,040 cells are byte-identical to the preserved E2 corpora.
- **Analyzer qualification: PASS.** 19,968 control replays, with 0 failures and 0 mismatches.
- **D9 real-fixture gate: PASS.** 132 scenarios, with 0 completions against the real guards.

**Treatment gates.** Both passed; any failure would have been a STOP.

| | T-E3 (`treatment_gates_T-E3.json`, `7bcda770…`) | T-E3K1 (`treatment_gates_T-E3K1.json`, `29345f6a…`) |
|---|---|---|
| Corpus integrity (every field) | PASS | PASS |
| Prefix gate: identical to the parent control through its first hit; the 64 F2 and 64 F2-P hit-free cells reproduced entirely | PASS, every field | PASS, every field |
| Exclusive ticks / zero-action live ticks / G.4 violations | 0 / 0 / 0 | 0 / 0 / 0 |
| Σ `cpu_used` ≠ `cpu_total`; capture disagreements | 0; 0 | 0; 0 |
| Telemetry (4,864 replays) | 0 analyzer failures | 0 analyzer failures |
| Completions against the repair and disrupt guards | **0: no D9 stop** | 192 (reported to D9; the companion is never a stop) |

## C. Corpus

| Condition | F1 | F2 | F2-P | F4 | Total |
|---|---|---|---|---|---|
| C-E2 | 2,880 | 640 | 640 | 704 | 4,864 |
| T-E3 | 2,880 | 640 | 640 | 704 | 4,864 |
| C-RS | 2,880 | 640 | 640 | 704 | 4,864 |
| T-E3K1 | 2,880 | 640 | 640 | 704 | 4,864 |
| **Total** | | | | | **19,456** |

- **Distinct trajectories.** F1 has 489 under C-E2 and 590 under T-E3. The distinct (C key, T key) transitions behind the main criteria are 1,003 for D0, 187 for D1/D4/D8 and 722 for D7.
- **Weighting.** Counts below are match-weighted over 32 seeds unless labelled otherwise, and each criterion carries its n_distinct. Any value resting on fewer than 8 distinct transitions is a deterministic or limited characterization, never a rate.

---

## D. Layer 1 — Registered verdicts

### D.1 Primary arm (C-E2 → T-E3)

| ID | Statement | Status | Frozen criterion value | Evidence |
|---|---|---|---|---|
| D0 | No structural change | **REFUTED** | Outcome class unchanged in 2,646 / 4,160 exposed standard cells = **0.636** (< 0.90) | 1,003 distinct transitions; rate-eligible |
| D1 | Parity lock decreases | **NEITHER** | Median two-sided PD = **0.714** in the stalemate population. Support needs ≤ 0.5; refutation needs ≥ 0.9. | 577 scoreable, 161 `NOT_SCOREABLE` of 738; n_distinct 187; rate-eligible |
| D2 | Seat determination decreases | **SUPPORTED** | 5 of 6 C-E2 seat-determined units fall below SDI 0.9 (≥ half); no new F1 or F2 unit reaches 0.9; all ten mirror claims agree at 1000 and 1001 | Unit-level count. Each fallen unit rests on 1–6 distinct trajectories, so each fall is a deterministic characterization, not a rate. |
| D3 | Defense no longer needs disrupt-first | **SUPPORTED** | 192 / 192 of the repair guard's C-E2 capture losses become non-losses (≥ half) | n_distinct 6: **limited distinct trajectories, not a rate claim** |
| D4 | First-mover control persists | **REFUTED** | Median first-mover swing share = **0.143** (≤ 0.5) | Same population as D1 |
| D5 | Location/process-count exploit | **REFUTED** | Spread win-or-draw against the 8 stacked agents falls in both seat tables: −0.195 (Seat A), −0.068 (Seat B) | Under P-1 the support branch was unreachable; the refutation branch was reachable, and it holds. |
| D6 | Re-disruption recreates control | **SUPPORTED** | The jam sniper beats the **min guard** decisively in both seats, 32 / 32 per seat. It ties the repair and disrupt guards. | n_distinct 1 per seat: **deterministic characterization** |
| D7 | Draw-ification | **REFUTED** | Exposed-F1 tick-limit share 0.545 → 0.596, a rise of **+0.051** (< 0.10) | 722 distinct transitions; rate-eligible |
| D8 | Last-mover inversion | **NEITHER** | Median PD 0.714 (support needs ≥ 0.9; refutation needs ≤ 0.5) and median FMS 0.143 (support needs ≤ 0.1) | Same population as D1 |
| D9 | Hold × order immunity | **SUPPORTED** | T-E3: **0** completions against the repair and disrupt guards (and twins) across all 4,864 cells. T-E3K1: 192 (> 0). | Theorem check; no stop |

The seat-conditioned Bradley–Terry residual reading (§M rule 4, secondary) counts **no** residual in either T-E3 seat table. Every candidate residual is a dominance pairing.

### D.2 Companion arm (C-RS → T-E3K1): λ-only deconfounder, not a verdict

These values use identical code and C-RS's own frozen populations (O-COMPANION). They never replace a primary verdict.

| ID | Companion reading | Value |
|---|---|---|
| D0 | REFUTED | 0.652 unchanged (1,102 distinct transitions) |
| D1, D4, D8 | NOT_EVALUABLE | K = 1 leaves no recovery, so C-RS has no stalemate population. On the secondary exposed population the median PD is 0.963 and the median FMS 0.019. |
| D2 | SUPPORTED | All 6 units fall (guarded-painter mirror 1.0 → 0.516) |
| D3 | SUPPORTED | 96 / 192 = 0.500 non-losses (96 ties, 96 losses); n_distinct 6 |
| D5 | NEITHER | −0.195 (Seat A), +0.057 (Seat B) |
| D6 | SUPPORTED | The jam sniper beats the disrupt and min guards decisively in both seats; it ties the repair guard |
| D7 | SUPPORTED | 0.333 → 0.464, +0.131 (876 distinct transitions) |
| D9 | reported to the primary arm | 192 completions against the guards |

## E. Layer 2 — Registered interpretation

| Registered result | Registered conclusion | Status of its inputs | Fires? |
|---|---|---|---|
| D1 ∧ D2 | Whole-tick disruption is load-bearing for scheduler-locked play | D1 NEITHER, D2 SUPPORTED | **No** |
| D2 ∧ D8 | Load-bearing for first-mover outcome determination, but parity control persists through the last position… | D2 SUPPORTED, D8 NEITHER | **No** |
| (D4 ∨ D8) ∧ ¬D2 | Not load-bearing; the disruption line closes | D4 REFUTED, D8 NEITHER, D2 SUPPORTED | **No** |
| D7 | Recorded as a pathology whatever else holds | D7 REFUTED | **No** |

**No pre-registered interpretation row applies.** That is itself the registered outcome. No row is added after the fact, and `NEITHER` is not collapsed into support or refutation.

The closest registered rows, D1 ∧ D2 and D2 ∧ D8, both fail on the parity criterion. The stalemate population's median PD, 0.714, is neither low enough for "parity lock decreases" (≤ 0.5) nor high enough for "last-mover inversion" (≥ 0.9). §F.3 describes why.

---

## F. Layer 3 — Descriptive synthesis

*Everything in this section is description of frozen outputs and tallies over the same cell records and telemetry. No threshold, row or metric was added.*

### F.1 The manipulation took (MC-1, MC-2; a gate, not a finding)

| Standard fields (F1, F2, F4) | C-E2 | T-E3 | C-RS | T-E3K1 |
|---|---|---|---|---|
| Exclusive-tick share (one live entrant executes 0) | 0.622 (1,362,000 / 2,191,081) | **0.000** | 0.481 | **0.000** |
| Second-mover mean executed actions (alive at tick end) | 2.50 | **7.37** | 3.37 | 7.42 |
| First-mover mean executed actions | 6.80 | 7.40 | 6.48 | 7.44 |
| Mean ADF: second / first mover | 0.688 / 0.150 | 0.079 / 0.075 | 0.579 / 0.191 | 0.072 / 0.070 |
| Minimum executed actions (alive throughout): first / second | 2 / 0 | **5 / 4** (the G.4 bound, attained) | 2 / 0 | 5 / 4 |

Under λ = 1 both entrants act in every tick, and the first- and second-mover budgets become nearly equal. The jam sniper holds opponents to exactly the G.4 minimum. Whole-tick denial, the mechanism the review identified, is gone in both arms.

### F.2 Seat determination collapses (PM-4; D2)

- **F1.** Seat-determined pairings go from 3 to **0**. The maximum |seat bias| across the 45 pairings falls from 1.000 to 0.0625, and the mean from 0.067 to 0.002.
- **Single-location attackers lose their Seat-A edge.** Under C-E2 the probe won 0.556 of its Seat-A matches and 0.333 of its Seat-B matches; under T-E3 it wins 0.566 and 0.569. The sniper's rates, 0.556 and 0.333, become 0.222 and 0.222.
- **Mirrors (F2):**
  - the probe mirror (Seat A 64/64) becomes **mutual elimination at tick 3** in all 64 cells, exactly the review's §I prediction;
  - the sniper mirror (Seat A 64/64) becomes a tick-limit tie in all 64;
  - the greedy-painter and counter mirrors go from SDI 0.433 to 0.2;
  - the guarded-painter mirror is discussed in G.1.
- **1000 vs 1001 ticks.** Every mirror's claim, under every condition, is the same at both tick limits, so no claim is `TICK_LIMIT_PARITY_DEPENDENT`.
- **F4 stratum.** The jam sniper's seat-determined pairings (against the counter, and its own mirror) both disappear.

### F.3 First-mover monopoly is gone; order dependence is not (PM-1, PM-2; D1, D4, D8)

The stalemate population is 738 cells: 610 F1, 64 F2 and 64 F4.

| Direction (PM-1) | C-E2 (control) | T-E3 |
|---|---|---|
| first-mover-dominated / leaning | 589 / 53 | **0 / 0** |
| neutral/weak (PD ≤ 0.5) | 0 | 224 |
| last-mover-leaning / dominated | 0 / 0 | 66 / **287** |
| `NOT_SCOREABLE` (< 10 swings) | 96 | 161 |
| Median FMS / median PD (scoreable) | 1.000 / 1.000 | **0.143 / 0.714** |

**Distribution of FMS under T-E3 (scoreable stalemate cells):**

| FMS bin | [0, 0.1) | [0.1, 0.2) | [0.2, 0.3) | [0.3, 0.4) | [0.4, 0.5) | [0.5, 0.6) | ≥ 0.6 |
|---|---|---|---|---|---|---|---|
| Cells | 287 | 66 | 32 | 180 | 10 | 2 | 0 |

- **Every scoreable cell now favours the last mover or is roughly neutral; none favours the first mover beyond 0.6.** The median PD of 0.714 describes a mixture of two regimes, not a single moderate mechanism:
  - **Strict last-mover lock (FMS ≈ 0).** This is the sniper against the disrupt guard, the min guard and the spread defender, the min guard against the guarded painter, and the guarded-painter mirror. For sniper v disrupt guard, FMS goes from exactly 1.0 to exactly 0.0, and the match is still a tick-limit tie. This reproduces the design review's §D prior that "every change in core balance now favors the tick's last mover". The probe against the disrupt guard sits lower, with FMS ≈ 0.20.
  - **Moderate last-mover skew (FMS ≈ 0.36).** This is the disrupt and min guards against the counter, and the min guard against the greedy painter. These stalemates now end decisively.
- **PM-2.** Of the 1,476 stalemate-entrant readings, **993 are now `NO_ZERO_CORE_TICKS`** (674 under the control). The 483 remaining readings are now own-first (303), balanced (178) or opponent-first (2). Under the control, all 802 were opponent-first. The E2 phase-lock has largely vanished, as the review's O-7 anticipated, and FMS is the parity reading that remains defined.
- **Zero-core winners (F1).** They fall from 343 to **12**.

### F.4 Where the stalemates went (PM-3; D0, D7)

| Stalemate cells, C-E2 → T-E3 | → Seat-A win | → Seat-B win | → tick-limit tie |
|---|---|---|---|
| From tick-limit tie (512) | 131 | 128 | 253 |
| From Seat-A score win (78) | 78 | 0 | 0 |
| From Seat-B score win (148) | 38 | 110 | 0 |

About half of the draws become decisive, split evenly between the seats. Across all of F1 the effect nets out:

- tick-limit ties go from 1,088 to 1,081;
- tick-limit score wins rise from 482 to 636;
- mutual eliminations rise from 36 to 59;
- decisive wins fall from 1,274 to 1,104. Their median decision tick stays at 3, but the upper quartile rises from 4 to 59, and the latest decisive tick from 441 to 822, so decisive games get longer.

D0's 0.636 unchanged share and D7's +0.051 both describe a restructured field that is not draw-ified.

### F.5 Defense without disrupt-first (D3, D9)

- **The repair guard's C-E2 capture losses** (192: 64 each to the probe, the sniper and the spread sniper) all become **tick-limit ties** under T-E3. None becomes a win.
- **D9.** Across all 4,864 T-E3 cells, 0 completions are against the repair or disrupt guards, while T-E3K1 has 192. G.5 behaves exactly as the theorem, and as the real-fixture gate, predicted.
- **The companion arm separates the two causes.** With K = 1, λ alone turns half of the repair guard's capture losses into ties (96), and the other half stay losses. In the primary, the guard's full survival is therefore partly the λ × K = 2 immunity (review O-2). It is not evidence that disruption became weak in isolation.

### F.6 Location count stops paying (D5)

The spread agents' win-or-draw rate against the eight stacked agents falls from 0.9375 to 0.742 (Seat A) and from 0.8125 to 0.744 (Seat B). The spread sniper's decisive wins over stacked defenders turn into ties; for example, spread sniper v disrupt guard, which under C-E2 the spread sniper won by capture at tick 3–4 from both seats, is a tie in all 64 cells. This matches the review's prior that location count stops being decisive. P-1 still applies: the "supported" branch could not have been reached.

### F.7 Re-disruption (D6)

- **Against the min guard.** The jam sniper's repeated in-tick suppression recreates a decisive win, at tick 4 in both seats (32 of 32 per seat, one trajectory per seat). Under C-E2 that pairing was a tie.
- **Against the repair and disrupt guards.** It only ties them, as G.5 requires.
- **Reading.** Re-disruption recreates control where the defender's final action on its second-mover ticks is not a repair: the min guard reclaims only one core cell. It does not recreate control against continuous repairers.
- **Evidence label.** This is a deterministic characterization.

### F.8 The companion arm (λ only, K = 1)

- **Same direction as the primary.** λ alone also ends exclusivity and collapses all six seat-determined units, including the guarded-painter mirror (1.0 → 0.516).
- **More draws.** It raises the tick-limit share (+0.131).
- **Strong last-mover skew.** With no stalemate population, its exposed cells are strongly last-mover-dominated (median FMS 0.019, PD 0.963).
- **What this suggests.** The residual order effect is not an artifact of K = 2: without the hold it shows up more sharply, favouring the last mover. This is consistent with the effect being tied to the last action position and end-of-tick evaluation. Under O-COMPANION this remains a companion reading, not a primary verdict.

### F.9 The design review's probe priors, compared with the matrix

| Prior (review §I, §J) | Matrix | |
|---|---|---|
| D0 fails | REFUTED | Reproduced |
| D1 fails | NEITHER (0.714) | Partly: not supported, and not refuted either |
| D2 supported | SUPPORTED (5 of 6) | Reproduced |
| D3 supported, via G.5 | SUPPORTED; every loss becomes a tie | Reproduced |
| D4 fails | REFUTED | Reproduced |
| D5 fails | REFUTED | Reproduced |
| D6 fails; "jam sniper v repair guard: a tie" | SUPPORTED, through the min guard; the repair guard is a tie | The repair-guard trace is reproduced; the hypothesis-level prior is **not** |
| D7 likely | REFUTED (+0.051) | **Not reproduced** |
| D8 supported | NEITHER (median FMS 0.143, not ≤ 0.1) | **Not reproduced.** The strict last-mover lock holds in the canonical stalemates, but not across the population. |
| D9 supported by analysis | SUPPORTED | Reproduced |
| Sniper v disrupt guard: a tie, 0 of 999 swings favour the first mover | Tie in all 64; FMS exactly 0.0 | Reproduced |
| Probe mirror: mutual completion at tick 3 | Mutual elimination at tick 3, 64 / 64 | Reproduced |
| Sniper mirror: a tie at 1000 | 64 / 64 ties | Reproduced |
| Guarded-painter mirror: seed-dependent decisive captures, with the Seat-B inversion gone | A in 20 seeds, B in 12; decisive at ticks 30–378 | Reproduced (and see G.1) |
| Min guard v sniper: a tie | Tie in all 64 | Reproduced |
| Sniper v greedy painter: unchanged | Unchanged | Reproduced |

### F.10 Synthesis

**Slot-limited disruption clearly removes whole-tick first-mover monopoly and substantially reduces seat determination, but it does not eliminate order dependence. The remaining interaction is moderately last-mover-leaning, rather than strongly parity-neutral or strongly last-mover-dominated.**

The evidence:

- Exclusivity goes from 62% of ticks to none.
- First-mover-favouring stalemates go from 642 of 642 scoreable cells to 0.
- Five of six seat-determined units collapse, and every F1 seat bias shrinks to ≤ 0.0625.
- Strong first-mover locking has therefore weakened into mixed, moderate order dependence with a last-mover skew. It has not been "solved", and it has not been "inverted" in the registered sense.

---

## G. Limitations

- **G.1 The SDI definition on mirrors.** The frozen SDI (E2's O-SDI-UNIT, retained unchanged) marks a seed as seat-determined when the same seat wins both orientations. Under T-E3 the guarded-painter mirror has that property for **every** seed, so its SDI is 1.0. But the winning seat varies by seed: Seat A in 20 seeds and Seat B in 12, a mirror seat bias of only +0.19, with decisive captures between ticks 30 and 378. SDI 1.0 therefore does not distinguish "each seed is seat-consistent" from "one seat always wins". This does not invalidate the frozen analysis, and D2 counted this unit as not falling, exactly as registered. A future pre-registration should pair SDI with the favoured-seat share across seeds, or with a bias-based criterion. It is not changed retroactively here.
- **G.2 P-1 (accepted before the treatment).** D5's "supported" branch was unreachable in the Seat-A table. D5 is refuted on the reachable branch.
- **G.3 Evidence labels.**
  - D3 rests on 6 distinct transitions: a limited characterization, not a rate claim.
  - D6 rests on 1 per seat: a deterministic characterization.
  - D2 counts units whose individual SDIs rest on 1–6 distinct trajectories.
  - D1, D4, D8 (n_distinct 187), D0 (1,003) and D7 (722) are rate-eligible.
- **G.4 The parity medians pool two regimes.** The stalemate FMS distribution is bimodal (§F.3), so D1 and D8 landing in `NEITHER` reflects a mixture: a strict last-mover lock in some pairings and a moderate skew in others. The frozen criteria are cell-weighted medians and are read as such.
- **G.5 `NOT_SCOREABLE` cells.** 161 of 738 stalemate cells had fewer than 10 swings under T-E3. All 64 jam-sniper-v-min-guard cells were decided at tick 4, and the probe-v-min-guard cells at tick 3 or 4. They are counted and reported, and they are outside the medians.
- **G.6 Residuals are silent.** No residual counts in either condition, because the field is saturated by dominance pairings. The secondary Bradley–Terry reading neither supports nor contradicts the synthesis.
- **G.7 Scope** (review O-10 to O-12).
  - Information is free and global (R4b's unmet precondition), and E3 cannot rule it out as an upstream cause.
  - The fixtures were written for whole-tick semantics.
  - The G.4 bound and G.5 immunity are specific to 2 entrants, Q = 8, chunk 2 and rotation.
  - No external-validity claim is made.

## H. Disposition

**E3 is a successful causal intervention but not a complete gameplay solution.** Whole-tick disruption is load-bearing for first-mover exclusivity and for much of the prior seat determination. Removing it exposes a weaker residual order effect, tied to the last-mover position or to end-of-tick evaluation.

This is a descriptive disposition. The registered disposition is simply that **no interpretation row triggered**. The research Rulesets `bytefray-rules-6-research-capture-hold-k2-disruption-slot1` and `bytefray-rules-6-research-disruption-slot1` stay research-only and resolvable, and nothing is added inside E3.

## I. Next research question

> **Is the remaining order dependence caused primarily by the scheduler's last-action position, or by evaluating capture/state only at the end of the tick?**

The companion arm's strong last-mover skew under K = 1 (§F.8), and the canonical stalemates' exact FMS 0.0, both point at the tick's final action and the end-of-tick evaluation instant. The review's §E names the two candidate interventions: ABBA (or otherwise non-rotating-final) in-tick order, and per-chunk capture evaluation. Each is a new scheduler design or a new core rule, so the next study needs its own scope decision, design review and pre-registration. It is registered separately; nothing is implemented here.

## What this report does not claim

- No product or balance recommendation. The disposition is a research disposition.
- No rate claim from a value resting on fewer than 8 distinct transitions.
- No pre-registered interpretation beyond "no row applies". The synthesis and disposition are labelled as description.
- No change to any threshold, criterion, operationalization, fixture or analysis tool after the treatment ran.
- No claim from the companion arm that replaces a primary verdict.

## Appendix R. Reproduction

- **Primary analysis (frozen, unmodified):** `python -m tools.research.v6.e3.run_e3 analyze` at `6f0fd3f`, or any later commit that preserves freeze v1. It requires both treatment gate records. Its output hash is in §A.
- **Treatment gates:** `python -m tools.research.v6.e3.run_e3 treatment-gates T-E3` and `… T-E3K1`.
- **Descriptive tallies (§F).**
  - These are tallies of the same frozen outputs: harness cell records, `analyze_e3.outcome_class`, `transitions`, `parity_summary`, `action_summary` and `pm4_paired`, applied to the loaded runs (`run_e3.control_runs` for each condition) and to the frozen populations in `control_populations.json`.
  - The FMS bins, per-pairing medians, agent seat records and per-seed mirror winners are counts over the same rows.
  - No threshold or new metric was introduced.

## Addendum, 2026-09-24: descriptive erratum and mirror-methodology clarification

This addendum is additive. The report above is left exactly as written. No registered verdict, threshold, criterion, operationalization or calculation changes, and E3 is not recomputed. Both items were raised by the E4 design review ([V6_E4_ORDER_VS_EVALUATION_TIMING_DESIGN_REVIEW.md](V6_E4_ORDER_VS_EVALUATION_TIMING_DESIGN_REVIEW.md) §B, §S-7 and §S-8). Each was re-verified independently against the preserved E3 corpus before being recorded here.

**Erratum: the guarded-painter mirror's seed split.** §F.9 ("A in 20 seeds, B in 12") and §G.1 ("Seat A in 20 seeds and Seat B in 12") misstate a descriptive count.

- The preserved T-E3 harness cell records give **19 Seat-A seeds and 13 Seat-B seeds** (38 and 26 matches), with no mixed seeds. F2 and F2-P agree.
- The frozen `e3_analysis.json` gives the mirror's seat bias as 0.1875 at both 1000 and 1001 ticks.
- The bias quoted above, +0.19, was therefore already the 19/13 value: (19 − 13) / 32 = +0.1875. A 20/12 split would give +0.25.
- The decisive-tick range (30–378) is unchanged.
- **No registered E3 verdict changes.** D2 counted this unit exactly as registered, and no criterion reads the seed split.

**Clarification: twin-mirror SDI is degenerate on decisive seeds.** Under the current harness, swapping a twin mirror's orientation is a pure relabelling. The twin's `agent.py` is byte-identical, and seat geometry and each entrant's derived RNG seed are keyed to the seat (`A`/`B`) and slot, not to the agent's name. Both orientations therefore play the same match with the names exchanged.

- **Verified on the preserved corpus:** every twin-mirror orientation pair has byte-identical replay tick records and the same winning seat. That holds for 352 of 352 pairs in each of C-E2, T-E3 and T-E3K1: the 320 F2 pairs and the 32 F4 jam-mirror pairs.
- **Consequence:** the historical mirror SDI (E2's O-SDI-UNIT, as used in E2 and E3) is 1.0 by construction on every decisive seed. For twin mirrors it measured decisiveness, not per-seed seat consistency.
- Mirror seat bias and the favoured seat remain valid.
- This sharpens §G.1: the guarded-painter mirror's SDI of 1.0 follows from the construction; it is not an observation.

This is a prospective methodological correction only. It alters no historical calculation or verdict. From E4 onward, mirrors are analysed at the seed level, and relabel identity is a gate, not a metric (E4 design review §M.1).
