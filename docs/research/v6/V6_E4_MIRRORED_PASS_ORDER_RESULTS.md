# Bytefray V6 E4 — Mirrored Pass Order: Results

**Status:** The full frozen E4 matrix (15,232 matches) has been executed and analyzed.

- **Measurement.** Every measurement was made by the frozen instrument of analysis freeze v1, `v6-e4-freeze-v1-101a941f5e30`.
- **Interpretation.** The results are interpreted under analysis freeze v3, `v6-e4-freeze-v3-80f21d822542`, the latest interpretation layer.
- **Reading.** The hypotheses are read literally under the frozen pre-registration.

This is a research result, not a product decision.

**Branch:** `v6-research`. Controls were generated at `e0d39b3`. The treatments were generated and analyzed at `ca820a3`.
**Date:** 2026-09-24
**Authority:**
- [`V6_E4_ORDER_VS_EVALUATION_TIMING_DESIGN_REVIEW.md`](V6_E4_ORDER_VS_EVALUATION_TIMING_DESIGN_REVIEW.md): §M metrics; §N populations, hypotheses and interpretation; §P evidence rules; §R hard stops.
- The pre-registration: `tools/research/v6/e4/preregistration.json` (v1), with the interpretation-only amendments `preregistration_v2.json` (O-INTERPRETATION-2) and `preregistration_v3.json` (O-INTERPRETATION-3).
- The freeze records: [`V6_E4_EXPERIMENT_FREEZE.md`](V6_E4_EXPERIMENT_FREEZE.md), [`V6_E4_ANALYSIS_FREEZE_V2.md`](V6_E4_ANALYSIS_FREEZE_V2.md) and [`V6_E4_ANALYSIS_FREEZE_V3.md`](V6_E4_ANALYSIS_FREEZE_V3.md).
- The Rulesets are recorded in [`V6_E4_MIRRORED_PASS_ORDER_REGISTRATION.md`](V6_E4_MIRRORED_PASS_ORDER_REGISTRATION.md).

This record has three layers, and they are kept apart:

1. **Registered verdicts.** E4-H0–H8 and D9′ exactly as the frozen criteria evaluate them, including `NEITHER`.
2. **Registered interpretation.** The pre-registered interpretation table, applied as written, under the latest amendment layer.
3. **Descriptive synthesis.** What the data establish beyond the registered rules. It is labelled as description and is not a pre-registered disposition rule.

## Answer in brief

- **Registered verdicts (primary arm, C-E4 → T-E4):**
  - **SUPPORTED:** H1 (response-order concentration is load-bearing), H3 (opening-pass response privilege) and H4 (hold × order masking).
  - **REFUTED:** H0 (no structural effect), H5 (new early-capture pathology), H6 (stasis) and H8 (tick-limit parity artifact).
  - **NEITHER:** H2 and H7.
    - H2 (the privilege follows the final pre-sample chunk): 2 of 18 MULTI-PASS matchups follow the final chunk, 1/9 ≈ 0.111. Support needs ≥ 2/3, and refutation needs ≤ 1/10.
    - H7 (seed-conditioned seat dependence remains).
  - D9′ **HOLDS**, with 0 completions.
- **Registered interpretation. No pre-registered interpretation row applies.** The row whose other inputs hold, H1 ∧ H3 ∧ ¬H2, requires H2 REFUTED, and H2 is NEITHER. No other row fires. The reading is the same under all three interpretation layers (v1, v2 and v3).
- **Descriptive synthesis.** The observed pattern is very close to the two-mechanism signature, but it is not a pre-registered conclusion.
  - Mirrored pass order removed most of the last-mover core advantage in MULTI-PASS contests: 16 of 18 matchups classified NEUTRALIZED, 14 of them substantively.
  - It left the OPENING-ONLY contests' last-side persistence in place: 13 of 14 STAYS, and all 14 keep their second-mover swing privilege.
  - One pairing (disrupt guard ↔ min guard, both orientations) instead follows the final chunk.
  - These are census counts of matchup characterizations, not rates: 17 of the 18 MULTI-PASS units rest on a single trajectory.
- **Disposition (descriptive, not a registered rule).** **E4 produced a strong descriptive two-mechanism pattern, but no pre-registered interpretation row applied. Mirrored pass order largely neutralized multi-pass response-order concentration while leaving opening-pass anchor/core-0 contests largely unchanged. The final-pre-sample hypothesis was not formally refuted under the frozen threshold because 2 of 18 multi-pass matchups followed the final chunk.**

---

## A. Execution provenance

| Item | Value |
|---|---|
| Matrix | `v6-e4-matrix-v1-fc29d575dd25` (digest `fc29d575…c703ceff4ef`), unchanged since the freeze |
| Measurement instrument | Analysis freeze v1 `v6-e4-freeze-v1-101a941f5e30`: E4 analyzer v1, cell metrics v1, capture analyzer v2 and E3 action/parity analyzer v1. Tooling qualified at `108d08d`; freeze committed at `e0d39b3`; control qualification committed at `6815cab`. |
| Interpretation layers | Freeze v2 `v6-e4-freeze-v2-68d262a0dbd1` (record `94bc65b`) and freeze v3 `v6-e4-freeze-v3-80f21d822542` (record `d17ce32`). Each was registered and frozen before any treatment cell existed, and each is layered on the preserved earlier freeze (§E.1). |
| Pre-registration | v1 `56307844…b9973`; the v2 amendment `d69680c4…5ccd9f`; the v3 amendment `4e99bc9e…17a993`. No hypothesis, threshold, population, metric or calculation changed in either amendment. |
| Controls | C-E4 and C-E4K1, generated at `e0d39b3` with a clean tree, 2026-09-24 18:33–18:51 UTC. They reproduce E3's T-E3 and T-E3K1 byte for byte in all 7,616 cells. |
| Treatments | T-E4 and T-E4K1, generated at `ca820a3` with a clean tree, 2026-09-24 20:30–21:05 UTC (details below). |
| Analysis | `run_e4 analyze` at `ca820a3`, unmodified, run after both treatments passed their gates. Output: `…/freezes/v6-e4-freeze-v1-101a941f5e30/e4_analysis.json`, SHA-256 `2fa52a2e8d34aef705b839d12d18dd52aa7438323a068a7594f73111ab238955`. |
| Interpretation | `analysis_freeze_v3 interpret` at `ca820a3`. Output: `…/freezes/v6-e4-freeze-v3-80f21d822542/interpretation_v3.json`, SHA-256 `4a2162ce864ca8f4c7cc179e1a855f2bddef5ca9a204d9c761a47c1b5b0eca0f`. It contains the v3 reading and, inside it, the v2 and v1 readings. |
| Environment | Python 3.13.14, `Windows-11-10.0.26120-SP0`, one match worker per field |
| Retries | One. The T-E4K1 F1 cell set was re-run from empty after an operational abort; §G records it. No other cell failed or was re-run. |
| Artifacts | `runs/research_v6_e4/v6-e4-matrix-v1-fc29d575dd25/{C-E4,T-E4,C-E4K1,T-E4K1}/{F1,F2,F2-P,F4}`. Every `result.json` and replay is preserved (git-ignored). |

**How the treatments ran:**

- **Invocation.** Each field was started through `run_e4 execute … --confirm-matrix-execution --confirm-treatment-execution --workers 1`, with T-E4's four fields in parallel processes and then T-E4K1's.
- **Guards.** Each execution passed the full unlock chain and the execution-source check before and after its run.
- **Timings.** T-E4 ran 20:30:37–20:46:27 UTC. T-E4K1's F2, F2-P and F4 ran 20:46:46–20:51:27, and F1 re-ran 20:52:30–21:05:36.
- **Before execution:**
  - `analysis_freeze_v3 verify --execution` passed at `ca820a3`;
  - all 20 live entrant fingerprints equalled the frozen ones;
  - no treatment artifact existed.
- **Afterwards.** A source manifest was recorded before execution, covering `HEAD`, the trees of `engine/src` and `tools/research/v6`, and the SHA-256 of 48 research-tooling files and the harness. It was identical after execution and again after the analysis and interpretation.

Nothing in the instrument changed after the treatments ran.

## B. Gates

**Before treatment** (from the [freeze record](V6_E4_EXPERIMENT_FREEZE.md)):

- **Parent reproduction: FULL PASS.** 7,616 cells are byte-identical to E3's preserved T-E3 and T-E3K1 corpora.
- **Analyzer qualification: PASS.** 15,232 control replays with 0 failures and 0 disagreements.
- **G.4′ manipulation gate: PASS.**
- **D9′ real-fixture gate: PASS.** 132 scenarios, with 0 completions against the real guards.
- **Control-vs-control census: PASS.** 100% identity classes.

**Treatment gates.** Both passed; any failure would have been a hard STOP.

| | T-E4 (`treatment_gates_T-E4.json`, `e8b00fb0…`) | T-E4K1 (`treatment_gates_T-E4K1.json`, `98da2ca6…`) |
|---|---|---|
| Corpus integrity (every field) | PASS | PASS |
| G.4′ checks on every cell: both movers' minimum executed actions 5, no exclusive or zero-action live tick, the final-chunk owner the first mover, and the `cpu_used` cross-check | PASS: 3,808 cells | PASS: 3,808 cells |
| Twin relabel gate | PASS: F2 288 pairs, F4 32 pairs | PASS: F2 288, F4 32 |
| Telemetry (3,808 replays) | 0 analyzer failures, 0 capture, ownership or E4 reconstruction disagreements, 0 FPS identity failures | the same |
| Completions against the repair and disrupt guards (and twins) | **0: D9′ holds, no stop** | 0 (reported; the companion is never a stop) |

## C. Corpus

| Condition | F1 | F2 | F2-P | F4 | Total |
|---|---|---|---|---|---|
| C-E4 | 2,304 | 576 | 288 | 640 | 3,808 |
| T-E4 | 2,304 | 576 | 288 | 640 | 3,808 |
| C-E4K1 | 2,304 | 576 | 288 | 640 | 3,808 |
| T-E4K1 | 2,304 | 576 | 288 | 640 | 3,808 |
| **Total** | | | | | **15,232** |

**Units and evidence (O-UNIT, §P):**

- **The unit.** It is the ordered matchup, summarized by its median FMA over seeds. A twin mirror is one unit whose observations are its seeds.
- **P-PAR.** The primary population is frozen at 32 units: 18 MULTI-PASS and 14 OPENING-ONLY, all last-side under the control.
- **Evidence labels in P-PAR:**
  - 21 units are deterministic characterizations (n_distinct = 1), including **17 of the 18 MULTI-PASS units**; the 18th has n_distinct = 2;
  - 5 units have limited distinct trajectories (2–7);
  - 6 are rate-eligible, all of them OPENING-ONLY.
- **How to read the counts.** H1, H2 and H3 are therefore census counts over matchup characterizations (§P rule 2). Where a count rests on deterministic units, it is not an inferential rate.
- **Exposed-F1 rates.** H4 rests on 21 distinct transitions per arm, and H5 on 105; both are rate-eligible.

---

## D. Layer 1 — Registered verdicts

### D.1 Primary arm (C-E4 → T-E4)

| ID | Statement | Status | Frozen criterion value | Evidence |
|---|---|---|---|---|
| E4-H0 | No structural effect | **REFUTED** | STAYS + UNCHANGED-NEUTRAL = 13 / 32 of P-PAR (< 0.90) | Census of 32 P-PAR units |
| E4-H1 | Response-order concentration is load-bearing | **SUPPORTED** | MULTI-PASS NEUTRALIZED + WEAKENED = **16 / 18** (≥ 2/3); overall FOLLOWS-FINAL = 2 / 32 = 1/16 (≤ 1/10) | Census; 17 of 18 units deterministic characterizations |
| E4-H2 | Final pre-sample position is load-bearing: the privilege transfers | **NEITHER** | MULTI-PASS FOLLOWS-FINAL = **2 / 18 = 1/9 ≈ 0.111**. Support needs ≥ 2/3; refutation needs ≤ 1/10. | The same census |
| E4-H3 | Opening-pass response privilege | **SUPPORTED** | OPENING-ONLY STAYS = **13 / 14** (≥ 2/3) | Census; 6 of 14 units rate-eligible |
| E4-H4 | Hold × order masking | **SUPPORTED** | Companion outcome-class change in MULTI-PASS exposed F1 = 128 / 640 = 1/5 (≥ 0.10), while the primary's = 0 / 640 (≤ 0.02) | n_distinct 21 in each arm; rate-eligible |
| E4-H5 | New early-capture pathology | **REFUTED** | 0 of 1,463 control non-capture exposed F1 cells become captures (< 0.10) | n_distinct 105; rate-eligible |
| E4-H6 | Stasis / draw-ification | **REFUTED** | Exposed-F1 tick-limit share 1,463 / 2,304 in both arms: a rise of **0** (< 0.10). Static neutralization, reported: 2 of 17 NEUTRALIZED units | Census of cells |
| E4-H7 | Seed-conditioned seat dependence remains | **NEITHER** | Not supported: \|GSB\| ≤ 0.10 fails in one unit, the guarded-painter mirror (3/16). Not refuted: that mirror has SCD = 13/16 ≥ 0.5 at n_distinct 32. | 45 T-E4 seat units (F1 36, F2 9) |
| E4-H8 | Tick-limit parity artifact | **REFUTED** | All 9 mirror claims agree at 1000 and 1001 ticks | Seed-level mirror claims |
| D9′ | G.5′ immunity (theorem; also a hard stop) | **HOLDS** | T-E4: **0** completions against the repair and disrupt guards (and twins) across all 3,808 cells | Theorem check; no stop |

### D.2 The H2 threshold, stated plainly

H2 is `NEITHER`. Two of the 18 MULTI-PASS P-PAR matchups are FOLLOWS-FINAL: 2/18 = 1/9 = 0.111…, one matchup above the frozen refutation threshold of ≤ 1/10. The frozen classification is `NEITHER`, not "effectively refuted", and this record does not treat it as a refutation anywhere.

The two matchups are one pairing, the disrupt guard and the min guard, in both orientations. O-UNIT counts each orientation as its own ordered matchup, as registered. §F.4 describes them.

### D.3 Companion arm (C-E4K1 → T-E4K1): an H4 input, not a verdict

The companion arm feeds E4-H4 only, and it never replaces a primary verdict (§P rule 7). Its H4 value is in the table above. D9′ also reports its completions: **0** under T-E4K1, against 192 under C-E4K1. Its other readings are description, in §F.6.

## E. Layer 2 — Registered interpretation

Under pre-registration v3 (O-INTERPRETATION-3 over O-INTERPRETATION-2 over O-INTERPRETATION), a row applies when every hypothesis it names has the required status. A plain hypothesis needs SUPPORTED and a negated one needs REFUTED. NEITHER satisfies neither.

| Registered result | Registered conclusion (abridged) | Status of its inputs | Fires? |
|---|---|---|---|
| H1 ∧ H3 ∧ ¬H2 | Two order mechanisms. In multi-pass contests it is response-order concentration, which order can remove. In anchor-base contests it is the second mover's opening response, which order cannot touch. | H1 SUPPORTED, H3 SUPPORTED, **H2 NEITHER** | **No** |
| H1 ∧ ¬H3 ∧ ¬H2 | Response-order concentration causes the residual broadly | H3 SUPPORTED, H2 NEITHER | **No** |
| H2 | The privilege follows the final pre-sample chunk | H2 NEITHER | **No** |
| ¬H1 ∧ H3 | The residual is the opening-pass effect; the in-tick order line closes. (Never reported as a standalone conclusion under v3.) | H1 SUPPORTED | **No** |
| H0 | Order is not load-bearing; the line closes | H0 REFUTED | **No** |
| H5, H6, H8 | Recorded as pathologies whatever else holds | All REFUTED | **No** |
| *O-INTERPRETATION-2 outcome* ¬H0 ∧ ¬H1 ∧ H3 | No registered causal interpretation applies… | Acts only when "¬H1 ∧ H3" applies | **No** |
| *O-INTERPRETATION-3 outcome* H2 ∧ H3 | Two contest-class-specific signatures… | Needs H2 SUPPORTED | **No** |
| none | "No registered row applies" is itself the registered outcome. The census is reported. | No main row applies | **Yes** |

**No pre-registered interpretation row applies.** That is the registered outcome.

- **The closest row.** The first row, H1 ∧ H3 ∧ ¬H2, requires H2 REFUTED, and H2 is NEITHER (§D.2).
- **No row added.** No row is added after the fact, and NEITHER is not collapsed into support or refutation.
- **The census.** The census the "none" row asks for is in §F.2–§F.3.

### E.1 Freeze lineage

The interpretation record carries all three readings:

| Layer | Freeze | Reading of the frozen verdicts | Amendment acted? |
|---|---|---|---|
| v1 (O-INTERPRETATION) | `v6-e4-freeze-v1-101a941f5e30` | "none" | — |
| v2 (O-INTERPRETATION-2, P-1: H0/H3 overlap) | `v6-e4-freeze-v2-68d262a0dbd1` | "none" | No. It acts only when "¬H1 ∧ H3" applies, which needs H1 REFUTED. |
| v3 (O-INTERPRETATION-3: H2/H3 precedence) | `v6-e4-freeze-v3-80f21d822542` | **"none"** (registered) | No. It acts only when H2 is SUPPORTED. |

**How the layers were built.**

- **Additive.** v2 was built on the preserved v1, and v3 on the preserved v2.
- **Blind.** Both amendments were registered and frozen before any treatment cell existed. Each fixed one overlap found on control data or on the registered definitions alone.
- **Checked before execution.** v1 and v2 still hold, byte for byte, and v3's execution-source check passed before the treatments ran.

**What the lineage shows.** The amendments did not decide this result: all three layers give the same registered outcome.

---

## F. Layer 3 — Descriptive synthesis

*Everything in this section describes frozen outputs. The figures are the frozen unit rows, telemetry summaries and tallies over the same cell records, made with the analyzer's own functions (§R). No threshold, row or metric is added. FMA is the first-mover core advantage, and negative values favour the tick's second mover. FPS is the share of swing ticks favouring the tick's final-chunk owner. Under forward order the final chunk is the second mover's; under mirrored order it is the first mover's.*

### F.1 The manipulation took (G.4′; a gate, not a finding)

Under both treatment Rulesets:

- every tick's offer sequence is `F F L L F F L L | L L F F L L F F`;
- both movers keep at least 5 executed actions in every live tick;
- no tick is exclusive or zero-action;
- the first mover owns the final chunk in every cell of every field.

The intervention is exactly the registered one: pass order, and nothing else.

### F.2 MULTI-PASS: most of the last-mover advantage is removed (H1, H2)

| Matchup (Seat A v Seat B) | Control FMA (band) | T-E4 FMA (band) | Class | FPS C → T | n_distinct |
|---|---|---|---|---|---|
| disrupt guard v min guard | −3.500 (strong-last) | **+0.500 (moderate-first)** | **FOLLOWS-FINAL** | 1.000 → 0.999 | 1 |
| min guard v disrupt guard | −3.500 (strong-last) | **+0.500 (moderate-first)** | **FOLLOWS-FINAL** | 1.000 → 1.000 | 1 |
| disrupt guard v sniper | −2.000 (strong-last) | 0.000 (neutral) | NEUTRALIZED | 1.000 → n/s (static) | 1 |
| sniper v disrupt guard | −2.000 (strong-last) | 0.000 (neutral) | NEUTRALIZED | 1.000 → n/s (static) | 1 |
| disrupt guard v probe | −0.874 | +0.001 | NEUTRALIZED | 0.750 → 0.500 | 1 |
| probe v disrupt guard | −0.751 | +0.124 | NEUTRALIZED | 0.857 → 0.571 | 1 |
| min guard v repair guard | −1.000 | 0.000 | NEUTRALIZED | 0.750 → 0.501 | 1 |
| repair guard v min guard | −0.750 | +0.250 | NEUTRALIZED | 0.750 → 0.665 | 1 |
| repair guard v sniper | −1.000 | 0.000 | NEUTRALIZED | 0.750 → 0.570 | 1 |
| sniper v repair guard | −1.000 | 0.000 | NEUTRALIZED | 0.856 → 0.402 | 1 |
| repair guard v spread sniper | −1.000 | 0.000 | NEUTRALIZED | 0.750 → 0.570 | 1 |
| spread sniper v repair guard | −0.999 | +0.001 | NEUTRALIZED | 0.856 → 0.403 | 1 |
| repair guard v probe | −1.000 | 0.000 | NEUTRALIZED | 0.750 → 0.570 | 1 |
| probe v repair guard | −1.000 | 0.000 | NEUTRALIZED | 0.856 → 0.402 | 1 |
| repair guard v spread defender | −0.748 | +0.248 | NEUTRALIZED | 0.750 → 0.664 | 1 |
| spread defender v repair guard | −0.995 | +0.001 | NEUTRALIZED | 0.749 → 0.501 | 1 |
| disrupt guard v spread defender | −0.501 (moderate-last) | −0.499 (neutral) | NEUTRALIZED (boundary) | 1.000 → 0.000 | 1 |
| spread defender v disrupt guard | −0.501 (moderate-last) | −0.499 (neutral) | NEUTRALIZED (boundary) | 0.999 → 0.001 | 2 |

The 18 units fall into three groups. Each is a deterministic characterization unless its n_distinct says otherwise.

- **14 units are substantively neutralized.**
  - Their control FMAs run from −2.0 to −0.748, and their treatment FMAs all lie within |FMA| ≤ 0.25.
  - Their swings now split between the entrants (FPS 0.40–0.67), where the control's swings strongly favoured the final-chunk owner.
  - Two of them, the disrupt guard against the sniper, become static: one swing tick. They are H6's two static neutralizations.
- **2 units are boundary crossings (P-2).**
  - The disrupt guard and the spread defender, in both orientations, cross the neutral boundary with an FMA change of 0.002 (−0.501 → −0.499).
  - Their swings favour the second mover in both arms, FPS 1.0 → 0.0. Mirroring did not move their privilege, and they are NEUTRALIZED by band only.
  - The registered class stands as computed.
- **2 units follow the final chunk.** §F.4 describes them.

### F.3 OPENING-ONLY: last-side persistence remains (H3)

| Matchup (Seat A v Seat B) | Control FMA | T-E4 FMA | Class | FPS C → T | n_distinct |
|---|---|---|---|---|---|
| disrupt guard v guarded painter | −1.001 | −0.985 | STAYS | 1.000 → 0.000 | 6 |
| guarded painter v disrupt guard | −1.002 | −0.985 | STAYS | 1.000 → 0.000 | 7 |
| guarded painter v min guard | −1.015 | −1.002 | STAYS | 1.000 → 0.004 | 31 |
| min guard v guarded painter | −1.000 | −0.989 | STAYS | 0.993 → 0.007 | 28 |
| guarded painter v spread defender | −0.509 | −0.508 | STAYS | 0.994 → 0.007 | 31 |
| sniper v guarded painter | −0.550 | −0.550 | STAYS | 0.965 → 0.035 | 26 |
| min guard v sniper | −0.500 | −0.500 | STAYS | 1.000 → 0.000 | 1 |
| sniper v min guard | −0.500 | −0.500 | STAYS | 1.000 → 0.000 | 1 |
| spread defender v min guard | −0.501 | −0.501 | STAYS | 0.999 → 0.001 | 2 |
| spread defender v sniper | −0.501 | −0.501 | STAYS | 0.999 → 0.001 | 2 |
| spread defender v guarded painter | −0.501 (moderate-last) | −0.495 (neutral) | NEUTRALIZED (boundary) | 0.995 → 0.007 | 31 |
| disrupt guard mirror (F2) | −1.000 | −1.000 | STAYS | 1.000 → 0.000 | 1 |
| guarded painter mirror (F2) | −0.991 | −0.985 | STAYS | 1.000 → 0.000 | 32 |
| min guard mirror (F2) | −1.000 | −1.000 | STAYS | 1.000 → 0.000 | 1 |

In every OPENING-ONLY unit, the FMA is unchanged or shifts by at most 0.017, and FPS goes from about 1 to about 0. The swing privilege therefore stays with the tick's **second** mover. It does not follow the final chunk, which mirroring gave to the first mover.

- **13 units** stay in their band.
- **The fourteenth**, the spread defender against the guarded painter, crosses the −1/2 boundary by 0.005 (P-2). The registered class stands as computed.

This is the signature the design review attributes to the second mover's opening-pass response. Six of these units are rate-eligible (n_distinct 26–32), which makes OPENING-ONLY the best-sampled part of P-PAR.

### F.4 The one pairing that follows the final chunk (H2)

The disrupt guard against the min guard is the only P-PAR pairing whose privilege moves with the final chunk.

- **Control.** FMA is −7/2 in both orientations, the strongest last-mover lock in P-PAR, with FPS 1.0: every swing favours the second mover, who owns the final chunk.
- **Treatment.** FMA is exactly **+1/2** in both orientations, and FPS is 0.999 and 1.0: every swing favours the first mover, who now owns the final chunk.
- **Band.** O-FMA-BAND places +1/2 in moderate-first, whose lower bound is inclusive.
- **FPS confirms it.** FPS independently shows the privilege tracking the final chunk, so this pairing's classification is not a banding artifact.
- **Magnitude.** It is much smaller than under the control: +0.5 against −3.5.
- **Evidence.** Both units are deterministic characterizations (one trajectory each).

### F.5 Core balance changes; outcomes almost do not (primary)

Cell-level FMA bands, F1:

| F1 cells | C-E4 | T-E4 | C-E4K1 | T-E4K1 |
|---|---|---|---|---|
| `DECIDED_EARLY` | 519 | 519 | 647 | 519 |
| strong-last | 128 | **0** | 128 | **0** |
| moderate-last | 776 | 322 | 603 | 288 |
| neutral | 881 | 1,399 | 926 | 1,433 |
| moderate-first | 0 | 64 | 0 | 64 |
| strong-first | 0 | 0 | 0 | 0 |

In both arms the 64 moderate-first F1 cells are the disrupt guard ↔ min guard pairing (32 seeds × 2 orientations). F2, F2-P and F4 cell bands are identical between control and treatment in the primary arm.

**Outcome classes, C-E4 → T-E4 (every cell).** Mirrored order changes the within-match core balance widely and match outcomes almost not at all.

- **F1:** **0 of 2,304** change. Captures stay at 841 and tick-limit ends at 1,463.
- **F2:** 6 of 576, which is 3 seeds each counted in both twin orientations.
  - The greedy-painter mirror's seed 31 goes from a Seat-A win to mutual elimination.
  - The guarded-painter mirror's seeds 9 and 10 exchange winning seats, so its seed split stays 19 A / 13 B.
- **F2-P:** 3 of 288, the same three seeds.
- **F4 (separate stratum):** 32 of 640. The jam sniper against the probe, with the probe in Seat A, goes from mutual elimination to a Seat-A win in all 32 seeds.

In total, **41 of 3,808** primary cells change outcome class. The neutralization of §F.2 is a change in how core ownership swings within a match (FMA, FPS), not in who wins.

### F.6 The companion arm (K = 1): outcome changes and the guards

- **H4's input.** 128 of the 640 MULTI-PASS exposed F1 cells change outcome class. They are four pairings in which an attacker in Seat A captured a guard under C-E4K1:
  - the spread sniper, the sniper and the probe against the repair guard;
  - the probe against the disrupt guard.

  All 128 become tick-limit ties under T-E4K1.
- **Guard completions.** In all, completions against the repair and disrupt guards go from **192** under C-E4K1 (F1 128, F4 64) **to 0** under T-E4K1. The F4 64 are the jam sniper against the disrupt guard, from both seats. Without the capture hold, mirrored order therefore also closes the guard captures that λ alone left open in E3's companion arm.
- **Other outcome changes.** The companion's other changes are 4 F2 cells, 2 F2-P cells and 32 more in F4 (the jam sniper against the probe, as in the primary). In total **230 of 3,808** companion cells change.
- **F1 cell bands.** They shift as in the primary (table above), with 128 fewer decided-early cells.
- **Seats.** The companion's maximum F1 |GSB| falls from 1/2 to 3/32. Its guarded-painter mirror goes from 7 A / 10 B decisive seeds to 7 A / 11 B.

Read together with the primary's 0 of 640, this is H4's registered masking pattern. The capture hold hides the order change's outcome effect, and K = 1 exposes it. It stays a companion reading.

### F.7 Seats and mirrors (H7, H8)

- **Primary F1.** Seat metrics are unchanged: maximum |GSB| 1/64, and no unit has SDom ≥ 0.9 or SCD ≥ 0.5.
- **Guarded-painter mirror (F2).** It is identical in aggregate: 19 A / 13 B, GSB 3/16, SCD 13/16, `seed_conditioned`. That keeps H7 at NEITHER: this mirror both breaks the |GSB| ≤ 0.10 condition and provides the SCD unit.
- **The other eight mirrors** are `not_seat_determined`.
- **1000 against 1001 ticks.** All nine claims agree, so H8 is refuted.

### F.8 The design review's probe priors, compared with the matrix

| Hypothesis | Probe prior (pre-registered) | Matrix | |
|---|---|---|---|
| H0 | Fails | REFUTED | Reproduced |
| H1 | Supported | SUPPORTED (16/18) | Reproduced |
| H2 | Fails (0 flips in any named scenario) | NEITHER (2/18 FOLLOWS-FINAL) | **Not reproduced**: one pairing follows the final chunk (§F.4) |
| H3 | Supported | SUPPORTED (13/14) | Reproduced |
| H4 | Supported (under K = 1, 3 named cases change outcome; under K = 2, none) | SUPPORTED (companion 128/640, primary 0/640) | Reproduced |
| H5 | Fails | REFUTED (0/1,463) | Reproduced |
| H6 | Static neutralization present; the flag unknown | REFUTED (rise 0); static neutralization 2/17 | Reproduced |
| H7 | Likely (guarded-painter mirror) | NEITHER | **Not reproduced**: the mirror is seed-conditioned but keeps \|GSB\| 3/16 |
| H8 | Unknown | REFUTED | — |
| D9′ | Theorem | HOLDS (0) | Reproduced |

### F.9 Synthesis

**Mirrored pass order removed most of the second mover's core advantage in contests where the two sides trade repeated writes and repairs across passes. It left the second mover's advantage in anchor-base contests in place. The pattern is very close to the two-mechanism signature the design review looked for, but it does not meet its registered form, because one pairing's privilege followed the final chunk instead of disappearing.**

The evidence:

- **MULTI-PASS.** 16 of 18 units are NEUTRALIZED: 14 substantively and 2 by boundary crossings (§F.2).
- **OPENING-ONLY.** All 14 keep their second-mover swing privilege under mirrored order (§F.3).
- **Final chunk.** One pairing follows it, at a much smaller magnitude (§F.4).
- **Outcomes.** Primary match outcomes are almost untouched: 0 of 2,304 F1 cells change (§F.5).

Each MULTI-PASS figure is a deterministic characterization of a matchup (17 of 18 units rest on a single trajectory). The pattern is mechanistically consistent, but it is not population-rate evidence.

---

## G. Execution note: the aborted T-E4K1 F1 attempt

This is an execution note, not a caveat on the results.

- **What failed.** The first T-E4K1 F1 attempt (one match worker; started 20:46:46 UTC) stopped at 20:49:43 after 538 of 2,304 cells. The harness's atomic replace of `.evaluation.json.<tmp>` over `evaluation.json` raised a Windows `PermissionError` (WinError 5). The other three T-E4K1 fields, and all of T-E4, completed normally.
- **What was done.**
  1. The partial cell set was moved, unchanged, out of the matrix root to `runs/research_v6_e4/_aborted_treatment_attempt_1_T-E4K1_F1_workers1/`.
  2. The field was re-run from an empty directory with the same command and the same commit (`ca820a3`, clean tree).
  3. Nothing but cell counts and provenance fields was inspected before the re-run. No outcome, metric or telemetry value had been read.
- **The identity check.** Afterwards, **all 538 quarantined cells were byte-identical to the re-run**: replay SHA-256, and `result.json` apart from `completed_at` and `occurrence_id`; 0 missing, 0 replay differences, 0 result differences. There is no evidence that the incident affected any scientific output. The quarantined cells are not part of the corpus and are not analyzed.
- **Correcting the earlier explanation.** The E4 freeze record explained the aborted control attempt as a file-system race between six workers. A single worker has now reproduced the failure, so a multi-worker race is no longer supported as the explanation. External or transient file-handle contention on `evaluation.json` remains the leading operational explanation, for example from a scanner or indexer, but it is not a demonstrated cause. The freeze record carries a dated addendum to the same effect. Its original wording, and the byte-identity result for the aborted control cells, are unchanged.

## H. Limitations

- **H.1 The FMA bands' boundaries (P-2, recorded before treatment).** Five P-PAR units are classified at a band boundary:
  - three cross −1/2 with an FMA change of at most 0.006: the disrupt guard ↔ spread defender, both orientations (MULTI-PASS), and the spread defender v guarded painter (OPENING-ONLY);
  - the two FOLLOWS-FINAL units sit exactly on +1/2;

  The bands have integer resolution by design (§M.2), and every class stands as computed. FPS is reported beside each unit so that the direction of the swing privilege can be read independently (§F.2–§F.4).
- **H.2 Evidence strength (P-3).** H1, H2 and H3 are census counts of matchup characterizations.
  - 17 of the 18 MULTI-PASS units have n_distinct = 1. OPENING-ONLY has 6 rate-eligible units.
  - The 16/18 and 13/14 counts are therefore mechanistically consistent characterizations, not inferential rates.
  - No rate claim is made from any value resting on fewer than 8 distinct trajectories.
- **H.3 H2's small denominator.** With 18 MULTI-PASS units, the ≤ 1/10 refutation threshold admits at most one FOLLOWS-FINAL unit. The two observed are one pairing in both orientations, counted as two ordered matchups under O-UNIT, exactly as registered.
- **H.4 D9′'s parity condition is vacuous on the primary (P-4).** The real guards never reach a zero core under T-E4's Ruleset, so D9′ holds through its completion count.
- **H.5 FMA and FPS measure core-balance dynamics, not outcomes.** H1's "load-bearing" refers to its registered FMA-band criterion. Primary outcome classes are unchanged in F1 (§F.5), and no outcome-level claim is made from H1.
- **H.6 Strata and arms.** F4 is never pooled with the standard fields, and the companion feeds H4 only.
- **H.7 Scope.** The results hold for 2 entrants, Q = 8, chunk 2, rotation and the fixtures as written. No external-validity claim is made.

## I. Disposition

**E4 produced a strong descriptive two-mechanism pattern, but no pre-registered interpretation row applied. Mirrored pass order largely neutralized multi-pass response-order concentration while leaving opening-pass anchor/core-0 contests largely unchanged. The final-pre-sample hypothesis was not formally refuted under the frozen threshold because 2 of 18 multi-pass matchups followed the final chunk.**

This is a descriptive disposition. The registered disposition is simply that **no interpretation row triggered**. The research Rulesets `bytefray-rules-6-research-capture-hold-k2-disruption-slot1-mirrored-passes` and `bytefray-rules-6-research-disruption-slot1-mirrored-passes` stay research-only and resolvable, and nothing is added inside E4.

## J. Next research question

This is future work, not part of the E4 verdict:

> **Does separating process anchor location from core cell 0 remove the opening-pass response privilege without changing disruption scope or scheduler order?**

§F.3 is the reason for asking it. Every OPENING-ONLY unit kept its second-mover privilege when pass order was mirrored.

Answering it would need its own scope decision, design review and pre-registration. It is registered separately, and nothing is implemented here.

## What this report does not claim

- No product or balance recommendation. The disposition is a research disposition.
- No refutation of H2. Its frozen status is NEITHER.
- No rate claim from a value resting on fewer than 8 distinct trajectories.
- No pre-registered interpretation beyond "no row applies". The synthesis and disposition are labelled as description.
- No change to any hypothesis, threshold, population, metric, operationalization, contest class, fixture or analysis tool after the treatment ran. Both interpretation amendments predate the treatment.
- No claim from the companion arm that replaces a primary verdict.
- No demonstrated cause for the `evaluation.json` failure (§G).

## Appendix R. Reproduction

- **Treatment execution:** `python -m tools.research.v6.e4.run_e4 execute {T-E4,T-E4K1} {F1,F2,F2-P,F4} --confirm-matrix-execution --confirm-treatment-execution --workers 1`, at `ca820a3` or any later commit that preserves freezes v1–v3.
- **Treatment telemetry and gates:** `… run_e4 treatment-telemetry T-E4 --workers 20` (and T-E4K1), then `… run_e4 treatment-gates T-E4` (and T-E4K1). The telemetry worker count only parallelizes read-only replay analysis. The control qualification's repeatability check used the same count and found 0 differences.
- **Primary analysis (frozen, unmodified):** `python -m tools.research.v6.e4.run_e4 analyze`. It requires both passing treatment-gate records. Its output hash is in §A.
- **Registered interpretation:** `python -m tools.research.v6.e4.analysis_freeze_v3 interpret`. It requires every treatment field and the analysis to come from a clean tree at a commit holding freeze v3. Its output hash is in §A.
- **Descriptive tallies (§F).** These are counts over the same frozen outputs:
  - the unit rows in `e4_analysis.json`;
  - `telemetry.summarize` over each condition's frozen telemetry;
  - `analyze_e4.outcome_class`, `is_capture`, `is_tick_limit`, `d9_completions`, `seat_units` and `mirror_claim`, applied to `run_e4.condition_runs` for each condition.

  No threshold or new metric was introduced.
