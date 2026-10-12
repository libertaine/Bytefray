# Bytefray V6 E2 — Multi-Tick Capture Hold: Results

**Status:** The full frozen E2 matrix (15,360 matches) has been executed and analyzed under analysis freeze `v6-e2-freeze-v2-db6458596d82`. Every hypothesis verdict is read from frozen outputs, under the pre-registered interpretation rules. This is a research result, not a product decision.
**Branch:** `v6-research`. Controls were generated at `062feeb`; the treatment was generated and analyzed at `f4ad557`.
**Date:** 2026-09-23
**Authority:** [`V6_E2_CAPTURE_HOLD_DESIGN_REVIEW.md`](V6_E2_CAPTURE_HOLD_DESIGN_REVIEW.md) (§H hypotheses, §I matrix and interpretation rules), `tools/research/v6/e2/preregistration.json` (frozen operationalizations), [`V6_E2_ANALYSIS_FREEZE_V2.md`](V6_E2_ANALYSIS_FREEZE_V2.md) (the analysis instrument). Execution history: [`V6_E2_EXPERIMENT_FREEZE.md`](V6_E2_EXPERIMENT_FREEZE.md), [`V6_E2_MATRIX_EXECUTION_HALT.md`](V6_E2_MATRIX_EXECUTION_HALT.md).

## Answer in brief

The question was whether preventing immediate fatal capture creates meaningful opponent-dependent strategic interaction, or mainly turns V4's forced line into delay, alternation, draws, location-count races or new seat pathologies. **Mostly the latter.** K = 2 does break the canonical forced line: single-location global attackers no longer beat disrupt-first defenders. But every change it produces in the primary field is one of three kinds:

- **Delay.** 1,066 of the 1,884 V4-decisive cells keep their winner exactly one tick later. Another 16, all in one pairing, are decided 6–198 ticks later.
- **A scheduler-phase-locked recovery stalemate**, ending as a draw or as a loss on score at the tick limit (610 cells).
- **A win reversal for one agent, the guarded painter**, reached through the same phase-locked alternation and finished while the winner holds zero core cells (192 cells).

Pairing-level seat determination is unchanged in all 45 primary pairings, and one new deterministic mirror seat inversion appears.

E2 does create a deterministic "rock-paper-draw" structure in both seat tables: a single-location sniper beats a painter, the painter beats a disrupt-first defender on score, and the defender draws the sniper. But its draw edge *is* the phase-locked stalemate. The pre-registered significance evidence does not distinguish the treatment from the V4 control.

**K = 2 capture hold alone does not create sufficient strategic opponent-dependence under otherwise-V4 semantics.** Disposition: **useful but insufficient; E2 remains research-only.** §J and §K explain why this is not recorded as a pre-registered "clean negative".

---

## A. Execution provenance

| Item | Value |
|---|---|
| Matrix | `v6-e2-matrix-v1-9048907fdc3b` (digest `9048907f…497427e0`), unchanged since freeze v1 |
| Analysis freeze | `v6-e2-freeze-v2-db6458596d82`: capture analyzer version 2, tooling qualified at `d584ea9`, requalified on control data only before any treatment match existed |
| Pre-registration | `5b0fafd3…a9d3b856`, unchanged. O-TOL, O-H2-SIGNIFICANCE and O-H2-TRIPLE applied as approved. |
| Controls | C-V4 and C-RS generated at `062feeb28d84c8da0af3f41716e3b5468e0b3eed`, clean tree, 2026-09-23 18:19–18:50 UTC |
| Treatment | T-E2 generated at `f4ad5573a4774348fe1b91acab262ad05062a4e5`, clean tree, 2026-09-23 19:43–20:03 UTC. Each field was started through `run_e2 execute`, whose unlock chain (committed freeze, gate and requalification under that freeze, execution-source check) passed before it ran. `HEAD:engine/src` equals the controls' tree, `5b7495ee…`. |
| Analysis | Unmodified `python -m tools.research.v6.e2.analyze_e2` at `f4ad557`, clean tree, source manifest byte-identical before and after. Output `runs/research_v6_e2/v6-e2-matrix-v1-9048907fdc3b/freezes/v6-e2-freeze-v2-db6458596d82/analysis/e2_analysis.json`, SHA-256 `dc66a64ea1e366918887d2067ef34feae8983e675b37634c96423fd269156fda`, `e2_analysis_version` 2, harness analyzer 2, capture analyzer 2 |
| Environment | Python 3.13.14, `Windows-11-10.0.26120-SP0`, one match worker |
| Retries | None. No cell failed, and no cell was rerun. |
| Artifacts | `runs/research_v6_e2/v6-e2-matrix-v1-9048907fdc3b/{C-V4,C-RS,T-E2}/{F1,F2,F3}`: every `result.json` and replay preserved (git-ignored) |

Nothing in the analysis instrument was changed after the treatment ran. The frozen capture analyzer's self-validation holds on the treatment: 5,120 T-E2 replays, 0 disagreements with the engine's capture record, 0 unattributed completions, 0 onset/killer mismatches. Every E2 capture is credited to its onset capturer, which confirms the design review's §C.5 attribution refinement on the real corpus.

## B. Control gate

**FULL CONTROL GATE PASS, twice.**

- **Under freeze v1:** 5,120 / 5,120 cells, 0 mismatches, deep replay comparison. Record SHA-256 `99b99a34…`.
- **Reconfirmed under freeze v2:** the same numbers. Record `freezes/v6-e2-freeze-v2-db6458596d82/control_gate.json`, SHA-256 `01949677…`.

The frozen v2 analysis output is also **identical** for C-V4 and C-RS in F1, F2 and F3: every outcome, seat, rating, decision-tick and capture-telemetry value, apart from the condition label. The two controls were kept separate and not pooled. Every treatment delta below is stated against C-V4, the historical control, and it is numerically identical against C-RS, E2's structural parent. H3a is evaluated against C-RS, as O-H3A specifies.

## C. Corpus

| Condition | F1 | F2 | F3 | Total | Provenance |
|---|---|---|---|---|---|
| C-V4 | 2,880 | 640 | 1,600 | 5,120 | `062feeb`, clean |
| C-RS | 2,880 | 640 | 1,600 | 5,120 | `062feeb`, clean |
| T-E2 | 2,880 | 640 | 1,600 | 5,120 | `f4ad557`, clean, `e2_freeze_id` = freeze v2 |
| **Total** | | | | **15,360** | |

Integrity was checked for all nine condition/field runs with the frozen `requalification.corpus_integrity`:

- the exact expected cell set (pair × seeds 1–32 × both orientations), with no duplicates and no extras;
- every cell `completed`, with an outcome and its artifacts;
- on-disk match directories equal to the recorded cells;
- the condition's Ruleset in every `result.json`;
- the frozen matrix and pre-registration digests and the agent fingerprints in every `provenance.json`;
- placements identical cell for cell across all three conditions.

All nine pass.

**Effective evidence.** Most E2 fixtures are deterministic by design (review §G.1), so seeds are not independent trials. In F1, 46 of the 90 ordered cells (pairing × orientation) under T-E2 are deterministic characterizations (1 distinct trajectory across 32 seeds), 27 have 2–7 distinct trajectories, and 17 are rate-claim eligible (≥ 8). Under C-V4 the counts are 53, 23 and 14. Every count below is match-weighted over 32 seeds, and `n_distinct` is given with it. A pairing with one trajectory is reported as a characterization, never as `n = 32` evidence.

---

## D. Headline treatment effects

### D.1 Outcomes (F1, primary; both controls identical)

| | C-V4 | T-E2 | Δ |
|---|---|---|---|
| Seat-A wins | 1,231 (0.427) | 975 (0.339) | −256 |
| Seat-B wins | 973 (0.338) | 781 (0.271) | −192 |
| Ties | 676 (0.235) | 1,124 (0.390) | +448 |
| Terminations: last agent standing / all dead / tick limit | 1,884 / 36 / 960 | 1,274 / 36 / 1,570 | −610 / 0 / +610 |
| Distinct trajectories (field) | 439 | 489 | |

### D.2 Where every changed cell went (F1, C-V4 → T-E2, cell by cell)

Every one of the 2,880 matched cells falls in exactly one row below. Pairings are written Seat A v Seat B, and "both" means both orientations.

| Cells | Distinct transitions | C-V4 → T-E2 | Pairings |
|---|---|---|---|
| 1,066 | 137 | Same winner, exactly one tick later | Probe v sniper; probe and sniper v repair guard, greedy painter, counter and spread sniper; guarded painter v greedy painter; the decisive greedy painter v counter cells; every spread-sniper win |
| 996 | 122 | V4 not decisive: unchanged result | 960 tick-limit + 36 mutual eliminations |
| 448 | 16 | **Decisive → tie** at the tick limit, after recovery | Disrupt guard and min guard v probe, sniper and counter (both); probe and sniper (A) v spread defender |
| 192 | 166 | **Winner reversed**, every reversal won at zero core | Guarded painter v probe, sniper and counter (both): V4's attacker wins become guarded-painter wins |
| 162 | 145 | Same winner, now **on score at the tick limit** after the loser kept recovering | Min guard v greedy and guarded painters (both); repair guard v guarded painter (34) |
| 16 | 16 | Same winner, still decisive, 6–198 ticks later | Repair guard v guarded painter |

Of the 1,884 V4-decisive cells, 1,082 (0.574) keep their winner decisively, 1,066 (0.566) of them exactly one tick later. The 610 new tick-limit matches are exactly the 448 + 162 recovery rows. None of the 960 V4 tick-limit matches contains a recovery, and each of the 610 does.

### D.3 Decisive timing (HD-6: decisive, mutual elimination and tick limit kept apart)

| F1 | Decisive: n (n_distinct) | Median [Q1, Q3] | Min–max | Mutual elimination: n, median | Tick limit: n (n_distinct), share |
|---|---|---|---|---|---|
| C-V4 | 1,884 (317) | 2 [1, 3] | 1–876 | 36, 38 | 960 (88), 0.333 |
| T-E2 | 1,274 (319) | 3 [2, 4] | 2–441 | 36, 39 | 1,570 (136), 0.545 |

No T-E2 match is decided at tick 1. The decisive median and quartiles move exactly one tick later. Mutual eliminations are the same 36 cells (counter and greedy painter), one tick later. F2 decisive: median 1 → 2, n 248 → 184. F3 decisive: median 10 → 9, n 1,078 → 858.

### D.4 Agent-level seat-conditioned records (F1, match-weighted; secondary to the pairing tables)

| Agent | C-V4 Seat A: W / L / T (P(win)) | C-V4 Seat B | T-E2 Seat A | T-E2 Seat B |
|---|---|---|---|---|
| `v4_probe` | 288 / 0 / 0 (1.000) | 192 / 64 / 32 (0.667) | 160 / 32 / 96 (0.556) | 96 / 96 / 96 (0.333) |
| `e2_sniper` | 288 / 0 / 0 (1.000) | 192 / 64 / 32 (0.667) | 160 / 32 / 96 (0.556) | 96 / 96 / 96 (0.333) |
| `e2_repair_guard` | 0 / 192 / 96 | 0 / 192 / 96 | 0 / 192 / 96 | 0 / 192 / 96 |
| `e2_disrupt_guard` | 0 / 192 / 96 | 0 / 192 / 96 | 0 / 96 / 192 | 0 / 96 / 192 |
| `e2_min_guard` | 0 / 192 / 96 | 0 / 192 / 96 | 0 / 96 / 192 | 0 / 96 / 192 |
| `e2_greedy_painter` | 133 / 137 / 18 (0.462) | 132 / 138 / 18 (0.458) | unchanged | unchanged |
| `e2_guarded_painter` | 128 / 128 / 32 (0.444) | 128 / 128 / 32 (0.444) | 224 / 32 / 32 (0.778) | 224 / 32 / 32 (0.778) |
| `e2_counter` | 138 / 100 / 50 (0.479) | 137 / 101 / 50 (0.476) | 42 / 132 / 114 (0.146) | 41 / 133 / 114 (0.142) |
| `e2_spread_sniper` | 256 / 0 / 32 (0.889) | 192 / 64 / 32 (0.667) | unchanged | unchanged |
| `e2_spread_defender` | 0 / 32 / 256 | 0 / 96 / 192 | 0 / 32 / 256 | 0 / 32 / 256 |

The disrupt-first and minimal guards turn half their losses into draws but win nothing, in either condition. The single-location attackers keep a Seat-A advantage under E2; the Seat-A minus Seat-B win-rate gap narrows from 0.333 to 0.222. The guarded painter becomes the strongest stacked agent, symmetrically in both seats.

---

## E. Seat analysis

**Pairing-level seat determination is unchanged.** Under both C-V4 and T-E2, exactly 3 of the 45 F1 pairings are seat-determined (SDI ≥ 0.9). All three favour Seat A with SDI 1.0 and are deterministic:

- probe v sniper (n_distinct 1);
- probe v spread sniper (n_distinct 2);
- sniper v spread sniper (n_distinct 2).

In each, the Seat-A entrant wins in both orientations. No pairing's SDI changed by more than the O-TOL tolerance: 0 of 45. The only other pairing with nonzero SDI, greedy painter v counter, is 0.267 under both (n_distinct 30). Seat-pathology summary: max |seat bias| 1.0 in both conditions, and seat-determined share 0.067 in both.

**Mirror seat bias (F2; mirrors are never pooled into ratings).**

| Mirror | C-V4: A / B / T, bias, SDI (favoured, n_distinct) | T-E2 |
|---|---|---|
| `v4_probe` | 64 / 0 / 0, +1.000, 1.0 (A, 1) | 64 / 0 / 0, +1.000, 1.0 (A, 1), at tick 2 instead of tick 1, every winner at zero core |
| `e2_sniper` | 64 / 0 / 0, +1.000, 1.0 (A, 1) | Same as the probe |
| `e2_guarded_painter` | 54 / 10 / 0, +0.688, 1.0 (A, 30) | **0 / 64 / 0, −1.000, 1.0 (B, 29)**, every match to the tick limit |
| `e2_greedy_painter` | 12 / 16 / 36, −0.062, 0.433 (B, 30) | Identical outcomes, decisive ticks +1 |
| `e2_counter` | 18 / 10 / 36, +0.125, 0.433 (A, 30) | Identical outcomes, decisive ticks +1 |
| Repair, disrupt and min guards; spread sniper; spread defender | 0 / 0 / 64 ties, 0.000 | Identical |

Mirror seat bias changed in 1 of 10 mirrors: the guarded painter, +0.688 → −1.000. That is a **new deterministic seat inversion**. Under V4, Seat A wins the mirror decisively in 27 of 32 seeds and Seat B in 5, in both orientations. Under E2, Seat B wins every seed on score at the tick limit, after roughly 10,800 onsets per side (about 170 per match per entrant). F1 and F2 are consistent. The guarded painter's F1 dominance is seat-symmetric, and its mirror is seat-determined, favouring the seat that moves second on tick 1.

**Seat-conditioned rating tables** are in §G. F3 (secondary): seat-determined pairings 3 → 1 (sniper v Octave remains).

---

## F. Capture dynamics (replay-derived, capture analyzer v2)

Under K = 1 every onset is a completion. C-V4 F1 shows 1,956 onsets and completions and 0 recoveries. T-E2 F1 shows **232,640 onsets, 230,726 recoveries and 1,346 completions**, all 1,346 attributed and every count consistent with the engine.

| T-E2 F1 agent (576 matches each) | Onsets | Recoveries | Recovery rate | Completions | Zero-core evaluations | Phase-lock | Max streak | Threatened at end | Max locations |
|---|---|---|---|---|---|---|---|---|---|
| `e2_min_guard` | 124,774 | 124,582 | 0.998 | 64 | 124,838 | 0.9995 | 2 | 128 | 1 |
| `e2_disrupt_guard` | 96,032 | 95,872 | 0.998 | 64 | 96,096 | 0.9993 | 2 | 96 | 1 |
| `e2_guarded_painter` | 10,347 | 10,091 | 0.975 | 64 | 10,411 | 0.9939 | 2 | 192 | 1 |
| `e2_repair_guard` | 340 | 117 | 0.344 | 222 | 562 | 0.605 | 2 | 1 | 1 |
| `e2_counter` | 315 | 0 | 0.000 | 301 | 616 | 0.503 | 2 | 14 | 1 |
| `e2_greedy_painter` | 320 | 0 | 0.000 | 311 | 631 | 0.507 | 2 | 9 | 1 |
| `e2_sniper` / `v4_probe` (each) | 192 | 0 | 0.000 | 128 | 320 | 0.600 | 2 | 64 | 1 |
| `e2_spread_defender` | 64 | 64 | 1.000 | 0 | 64 | 1.000 | 1 | 0 | 3 |
| `e2_spread_sniper` | 64 | 0 | 0.000 | 64 | 128 | 0.500 | 2 | 0 | 3 |

- **Phase lock.** The three agents that survive by recovering spend 99.4–99.95% of their zero-core ticks on the opponent's first-mover ticks: they are zeroed when the attacker moves first and recover when they move first. This is the design review's §D.5 alternation, reproduced at scale.
- **Onset parity (review §L.2).** Disrupt guard, min guard and guarded painter each have exactly 64 onsets on their *own* first-mover tick, and those are exactly their 64 completions. Every one is a capture by the three-location spread sniper. Location count and the parity exposure coincide, as the review's prior expected: no capture of a disrupt-first defender in F1 happens any other way. Every other onset of theirs falls on an opponent-first tick.
- **Zero-core winners.**
  - F1: 343 of 1,274 decisive wins (0.269, n_distinct 191). These are the guarded painter over probe, sniper and counter (192); probe and sniper over each other (64); probe and sniper over counter (64); and counter and greedy painter against each other (23).
  - F2: 184 of 184 (every decisive mirror win).
  - F3: 134 of 858 (`nemesis_alpha2` over probe and sniper 128; guarded painter over scout striker 6).
  - C-V4: 0 in every field.
- **Unresolved capture.** 448 F1 matches (n_distinct 14) and 64 F2 matches (n_distinct 58) have some entrant with ≥ 10 onsets and no completion. They are the disrupt guard and min guard v probe, sniper and counter stalemates, and min guard v guarded painter.
- **The pure repair guard.** It recovers only against the guarded painter (all 117 of its recoveries). Its window against the sniper stays nominal: 64 onsets, 0 recoveries, 64 captures at tick 2. This reproduces §D.4.
- **Attribution integrity.** Every completion in all 15,360 matches is an attributed `kill`, whose killer equals the independently re-derived onset capturer.
- **Enemy-core inference.** 0 incorrect in F1 and F2. In F3, `e2_sniper` and `e2_spread_defender` return `ambiguous` with a wrong possible base against `v5_core_defender`, `v4_claimer` and `v5_scout_striker` (32 matches each). This is identical under C-V4, so it is an information limit of the inferring fixtures against those reference agents, not an E2 effect.

---

## G. Opponent dependence

All rating-model quantities count each distinct trajectory once (HD-2). Most F1 pairings contribute 1–2 distinct outcomes, so the tables summarize a largely deterministic round robin.

### G.1 Bradley–Terry fits (F1)

| Table | Converged (iterations) | Components | Authoritative | RMSR (bootstrap SE) | Directed 3-cycles: robust / fragile |
|---|---|---|---|---|---|
| C-V4 Seat A | yes (504) | 3: {probe} > {sniper} > {the other eight} | **no (separable)** | 0.210 (0.0003) | 0 / 0 |
| C-V4 Seat B | yes (641) | 1 | yes | 0.270 (0.0011) | 0 / 0 |
| T-E2 Seat A | yes (444) | 1 | yes | 0.330 (0.0028) | **2 / 0** |
| T-E2 Seat B | yes (867) | 1 | yes | 0.266 (0.0036) | 0 / 0 |
| T-E2 pooled (*subordinate*) | yes (499) | 1 | yes | 0.271 (0.0143) | 0 / 0 |

T-E2 seat-conditioned ratings. These are meaningful as an ordering only: they are fitted to mostly deterministic pairings.

| Agent | Seat A | Seat B |
|---|---|---|
| `e2_guarded_painter` | 2158 | 2194 |
| `e2_spread_sniper` | 1855 | 2401 |
| `v4_probe` | 1578 | 1387 |
| `e2_sniper` | 1510 | 1466 |
| `e2_greedy_painter` | 1471 | 1414 |
| `e2_counter` | 1468 | 1452 |
| `e2_spread_defender` | 1451 | 1384 |
| `e2_disrupt_guard` | 1266 | 1224 |
| `e2_min_guard` | 1237 | 1148 |
| `e2_repair_guard` | 1006 | 928 |

Under C-V4, the Seat-A table is separable: probe and sniper win every Seat-A match, so no global ratings exist there. The Seat-B ratings are sniper 1877, probe 1748, guarded painter 1846, spread sniper 2268, counter 1540, spread defender 1489, greedy painter 1443, disrupt guard 1039, repair guard 882, min guard 868.

Two things move. The guarded painter overtakes the single-location attackers in both seats, which is the only reversed edge. The probe and sniper fall toward the middle, because their wins over the disrupt guard, min guard and spread defender become draws. In the Seat-B order the counter and greedy painter now sit level with or above them. Nothing else reverses; the rest of the order shifts only through those draws.

### G.2 Reversals, cycles and fragile edges

- **Explicit reversals, C-V4 → T-E2, both seats.** Guarded painter v probe, v sniper and v counter: V4's attacker wins become guarded-painter wins (192 cells, 166 distinct transitions, every one won at zero core). No other F1 edge reverses. Decisive edges against disrupt and min guards become ties (probe, sniper, counter) and do not reverse.
- **Cycles.** Both robust cycles in the T-E2 Seat-A table run {probe or sniper} → spread sniper → guarded painter → {probe or sniper}. Each closes through a *seat-determined* edge: probe and sniper beat the spread sniper only as Seat A (SDI 1.0, n_distinct 1; the spread sniper wins the other orientation). The Seat-B table has no cycle. Under interpretation rule 2 these are Seat-A artifacts of an unchanged seat determination, not structural cycles. No cycle edge lies within ±0.05 of 0.5, so none is fragile.
- **Upsets** (the lower-rated agent wins, rating gap > 20):
  - T-E2 Seat A, 3: probe and sniper beat the spread sniper, which is seat-determined, and the spread sniper beats the guarded painter.
  - T-E2 Seat B, 2: the probe beats the higher-rated greedy painter and counter (n_distinct 1 each).
  - C-V4: 1 (Seat A) and 3 (Seat B).

### G.3 Residuals and O-H2-SIGNIFICANCE (applied exactly)

A residual counts only if its pairing has n_distinct ≥ 8 in that seat table and its 95% interval from 1,000 distinct-trajectory bootstrap resamples (seed 42) excludes 0.

| T-E2 table | Counting residuals (residual, n_distinct, 95% CI) |
|---|---|
| Seat A: 7 of 7 eligible | probe v guarded painter −0.034 (26, [−0.0342, −0.0339]); sniper v guarded painter −0.023 (26, [−0.0235, −0.0232]); repair guard v guarded painter −0.0013 (22); disrupt guard v guarded painter −0.0058 (9); greedy v guarded painter −0.019 (29); greedy painter v counter −0.055 (30, [−0.073, −0.037]); guarded painter v counter +0.018 (29) |
| Seat B: 10 of 10 eligible | probe v guarded painter −0.0095 (29); sniper v guarded painter −0.015 (29); repair guard v greedy painter −0.057 (9); repair guard v guarded painter −0.0007 (23); repair guard v counter −0.047 (9); disrupt guard v guarded painter −0.0037 (8); **min guard v greedy painter −0.178 (8, [−0.192, −0.166])**; greedy v guarded painter −0.011 (29); greedy painter v counter −0.062 (30); guarded painter v counter +0.014 (27) |

How to read these, following interpretation rule 1 ("no single threshold crossing counts as evidence on its own"):

1. **Most are saturation residuals.** In every guarded-painter pairing, one agent wins every distinct trajectory. A single-component Bradley–Terry fit can only approach, never reach, 1.0, so the residual is a small nonzero number (|R| ≤ 0.034). Because the resampled pairing outcome never varies, its bootstrap interval is only a few thousandths wide. These residuals record the guarded painter's near-total dominance, which is a transitive re-ranking, not opponent dependence.
2. **The procedure does not separate treatment from control.** *Supplementary; not a pre-registered criterion.* The identical frozen code (`analyze_e2.hypothesis_metrics` with C-V4 in the treatment slot; Appendix R) marks 6 residuals in the C-V4 Seat-A table and 8 in the C-V4 Seat-B table as counting. That is the exploit-bearing baseline, and it has no cycles. Greedy painter v counter counts in both conditions, and its outcomes are identical under V4 and E2.
3. **One counting residual reflects the E2 tradeoff.** Min guard v greedy painter in Seat B (−0.178, n_distinct 8) is the Bradley–Terry model failing to place a defender that draws the sniper yet loses to the painter, which in turn loses to the sniper. In the Seat-A table the same pairing has 6 distinct trajectories, so it is ineligible. The tradeoff's residual signature is therefore rate-eligible in **one** seat table, not both.

This is not an analyzer correctness defect. The code computes the approved procedure exactly. The observation concerns what the approved procedure measures on a largely deterministic field, and it is recorded for future pre-registrations.

### G.4 O-H2-TRIPLE (applied exactly)

The pattern is: defender D, non-attacker N and core attacker S such that, in each seat separately, N beats D by majority on score at the tick limit, S beats N by majority, and D wins or ties S by majority.

| | Triples (D, N, S) | Every edge's n_distinct across both seats |
|---|---|---|
| **T-E2**: 7, all present in both seats | (disrupt guard, greedy painter, probe), (disrupt guard, greedy painter, sniper), (min guard, greedy painter, probe), (min guard, greedy painter, sniper), (spread defender, greedy painter, probe), (spread defender, greedy painter, sniper), (spread defender, greedy painter, spread sniper) | N v D: 2–14; S v N: 2; D v S: 2–4 |
| C-V4 (supplementary, same code) | (spread defender, greedy painter, spread sniper) | |

Six of the seven triples are created by E2. In every one, the D-v-S edge ("defence prevents death") is a draw produced by the phase-locked recovery stalemate (disrupt and min guards: about 500 onsets and recoveries per match) or by a single recovery (spread defender). Every S-v-N and D-v-S edge has 1–2 distinct trajectories per seat. Only the min guard's N-v-D edge reaches 8, in one seat. Each triple is therefore a **deterministic characterization in both seat tables, not a rate claim**.

---

## H. Hypothesis verdicts

Each verdict applies the frozen criterion and its operationalizations, then the §I.5 interpretation rules. The criterion values come from `hypothesis_metrics` in the frozen analysis output.

| ID | Verdict | Frozen evidence |
|---|---|---|
| **H0** Delay only | **Unsupported** as an explanation of the matrix. It holds locally, as a deterministic characterization. | V4-decisive cells keeping their winner exactly one tick later: **0.566** (1,066 / 1,884) against a ≥ 0.90 threshold (O-H0-KEEP); winner kept at all: 0.574. SDI unchanged in 45 of 45 pairings, and mirror seat bias changed in 1 of 10, both under O-TOL. Recovery rate ≈ 0 for none of the 5 defenders (disrupt 0.998, min 0.998, guarded painter 0.975, spread defender 1.000, repair guard 0.344). **Refuting evidence present:** 224 matches (the metric's n_distinct is 7, keyed on defender, orientation and E2 result) in which a defender survives the sniper in the orientation it lost under V4 — disrupt and min guards draw in both orientations, the guarded painter wins in both, and the spread defender draws as Seat B. Where H0 does hold (the 1,066 cells of §D.2), it holds exactly. |
| **H1** Defense becomes viable | **Supported** | Recovery followed by survival (O-H1-SURVIVAL), in matches of 576: disrupt 192 (n_distinct 6), min 320 (22), guarded painter 192 (166), spread defender 64 (4), repair guard 34 (16). V4-lost orientations that now tie or win: disrupt 192, min 192, guarded painter 192, spread defender 64. The refuting condition fails: recovery against the sniper is 0.999 (disrupt and min), 0.981 (guarded painter) and 1.000 (spread defender); only the repair guard is ≈ 0 (0 of 64). *Qualifications:* survival becomes **draws** for the disrupt guard, min guard and spread defender (deterministic, 1–2 trajectories per ordered cell), and **wins** only for the guarded painter (rate-eligible, 26–29 distinct trajectories per ordered cell, every win at zero core). No defender survives the three-location spread sniper. |
| **H2** Genuine tradeoff | **Partially supported.** Present as a deterministic characterization; not established as a structural or rate result. | *O-H2-SIGNIFICANCE, literal:* counting residuals in both seat tables (7 in Seat A, 10 in Seat B). Under rule 1, however, they are almost all saturation residuals of deterministic-winner pairings, and the identical procedure counts 6 and 8 residuals in the V4 control, so this clause does not separate the treatment (§G.3). The one counting residual that reflects the tradeoff (min guard v greedy painter, −0.178) is rate-eligible in the Seat-B table only. *O-H2-TRIPLE, literal:* 7 triples, all holding in both seats; 6 are new relative to the control. Every one is a deterministic characterization whose "defence prevents death" edge is the phase-locked stalemate of H3a/H3b (§G.4). *Refuting operationalization:* not met literally, since both tables have counting residuals and the Seat-A table has 2 robust cycles. But both cycles close through a seat-determined edge (§G.2), and the Seat-B table is cycle-free. **Seat conditioning leaves a draw-mediated rock-paper-draw pattern that is real, seat-symmetric and new, but deterministic, with no rate-eligible support in both seat tables.** It is not pooled-ranking evidence: the pooled table was not used. |
| **H3a** Perpetual repair stalemate | **Partially supported** | Tick-limit share rises against C-RS (O-H3A): **0.333 → 0.545** (960 → 1,570; n_distinct 88 → 136, both rate-eligible). All 610 added tick-limit matches contain recovery, and none of the 960 control ones does. The literal "≥ 1 recovery per 2 ticks" criterion (the larger per-entrant recoveries ÷ ticks ≥ 0.5) is met by **128 of 1,570** tick-limit matches (0.082, n_distinct 4). The same alternation seen from the other orientation scores 499 / 1,000 = 0.499, because of tick-limit parity (287 matches fall in [0.45, 0.5)). The threshold is applied as registered and not re-tuned. |
| **H3b** Phase-locked alternation | **Supported** | Phase-lock ≥ 0.95 for **610 of 610** entrants in the 610 F1 stalemated matches (n_distinct 48), and 128 of 128 in the 64 F2 stalemates (n_distinct 58). None lies within 0.5 ± 0.05 (O-TOL). Agent-level phase-lock is 0.994–0.9995. |
| **H3c** New deterministic seat inversion | **Supported** (one flip; no new seat determination) | Favoured-seat flip (O-H3C): **guarded-painter mirror**, SDI 1.0 favouring A (C-V4, 30 distinct seed trajectories; A 54 / B 10) → SDI 1.0 favouring B (T-E2, 29; B 64 / 64). New seat determination (SDI < 0.9 → ≥ 0.9): none in F1 or F2. The three A-favoured F1 pairings are unchanged. |
| **H3d** Dominant always-defend | **Unsupported** | No defender has 0 losses (O-H3D). Spread defender: 0 wins / 64 losses / 512 ties (tie rate 0.889, n_distinct 30), and all 64 losses are to the greedy painter on score. Disrupt and min guards: 0 / 192 / 384 (0.667). Guarded painter: 448 / 64 / 64. Repair guard: 0 / 384 / 192. |
| **H3e** Location-count arms race | **Unsupported** | Neither multi-location agent beats every stacked agent in both seats (O-H3E); both are confirmed at 3 locations. The spread sniper beats 6 of 8 stacked agents in both seats (the repair, disrupt and min guards, both painters and the counter), but beats the probe and sniper only as Seat A (seat-determined). The spread defender beats none of them. Location count's dominance over stacked defenders is **unchanged from V4** (one tick later), so it is not an effect of E2. |
| **H3f** Zero-core winners | **Supported** (present; no threshold registered) | Decisive wins by an entrant at zero core (O-H3F): **F1 343 / 1,274 (0.269, n_distinct 191)**, F2 184 / 184 (1.000), F3 134 / 858 (0.156). C-V4: 0 everywhere. This is a new reachable state, and it is how every E2 winner reversal is won. |
| **H3g** Capture never resolves | **Supported** (present) | Matches with some entrant at ≥ 10 onsets and 0 completions (O-H3G): **F1 448 / 2,880 (n_distinct 14)**, F2 64 / 640 (n_distinct 58). They coincide with the H3a/H3b stalemates. |

**Consistency between F1 and F2 (rule 2).** The mirrors agree with F1:

- probe and sniper keep a pure Seat-A win (H0);
- the disrupt, min and spread defenders tie their twins, as in their F1 draws;
- the guarded painter's F1 rise pairs with a seat-determined mirror that has flipped (H3c).

**The negative-result rule.** Its first condition essentially holds for F1: every outcome change there is H0 delay or an H3a/H3b stalemate, except the 192 guarded-painter reversals, which run through H3b alternation and finish as H3f zero-core wins. Its second condition requires H2 to be *unsupported* after seat conditioning. H2's triple pattern survives seat conditioning as a deterministic characterization, so that condition does not hold literally, and this report does **not** declare the pre-registered clean negative. The substantive conclusion the rule protects does hold, and is stated in §J.

---

## I. Exploratory priors (design review §D.8, §H) compared with the matrix

The implemented fixtures differ from the probe in two deliberate ways. The inferring agents adopt an enemy core base only when every visible enemy anchor coincides, and the spread agents draw seed-derived offsets. Where a prior failed to reproduce, that is recorded as a difference, not a defect. **The matrix is authoritative.**

| Prior | Matrix | |
|---|---|---|
| Probe and sniper mirrors: Seat A, tick 1 → Seat A, tick 2 (32/32) | 64/64 Seat A at tick 2 in both, every winner at zero core | Reproduced |
| Disrupt-guard, min-guard and spread-defender mirrors: tick-limit ties under both | 64/64 ties under both | Reproduced |
| Greedy-painter mirror: A 6 / B 8 / 18 ties, identical under both | A 6 / B 8 / T 18 per orientation, identical, decisive ticks +1 | Reproduced |
| Guarded-painter mirror: A 27 / B 5 → B 32/32 | A 27 / B 5 per orientation → B 32/32 per orientation | Reproduced exactly |
| Spread-sniper mirror: Seat A, tick 2 → Seat A, tick 3 | Tick-limit ties under both (64/64) | **Not reproduced.** The implemented spread sniper infers the enemy core only from a single visible location, so against its spread twin it never infers a core and never attacks. |
| Sniper v disrupt guard, min guard or spread defender: A wins at tick 1 → tie | All three are ties under E2 (probe too) | Reproduced |
| Sniper v guarded painter: A wins at tick 1 → B wins; guarded painter v sniper: B wins at tick 2 → A wins | Both reproduced, with 26–29 distinct trajectories per ordered cell | Reproduced |
| Disrupt guard v sniper: B wins at tick 2 → tie | Reproduced | Reproduced |
| Sniper v greedy painter or pure repair guard: A wins at tick 1 → A wins at tick 2 | Reproduced (the §D.4 nominal window: 0 recoveries of 64) | Reproduced |
| Spread sniper v disrupt guard (§D.6): A captures at tick 3 | A wins at tick 3, with the onset on the defender's own first-mover tick | Reproduced |
| Grid totals: Seat-A wins −22%, Seat-B −4%, ties +65% | F1: Seat A −21%, **Seat B −20%**, ties +66% | Direction reproduced. The Seat-B drop is much larger than the prior. |
| H0 holds for the probe mirror, sniper mirror and pure repair guard, and fails for disrupt-first defenders | Exactly this pattern | Reproduced |
| H1 supported, "but survival yields draws, not wins" | Draws for disrupt, min and spread defenders; **wins** for the guarded painter | Partly reproduced |
| H2 weakly suggested: sniper > greedy painter > spread defender ≈ sniper | This exact triple, in both seats, plus six more; not established as a rate result | Reproduced as a characterization |
| H3a present, H3b 150/150 attacker-first zero ticks, H3c guarded-painter mirror, H3f probe mirror, H3g as H3a | All present (H3b: 610/610 entrants ≥ 0.95) | Reproduced |
| H3d: spread defender "never beaten by the probe's attackers, but loses to painters on score" | Exactly that. It is still not unbeaten, so the criterion fails. | Descriptively reproduced |
| H3e present against stacked defenders | The spread sniper beats every stacked *defender* in both seats, but not every stacked agent, and the same held under V4 | Partly reproduced; not an E2 effect |
| §L.2: parity exposure dominated by location count | Every own-first-tick onset that captured a disrupt-first defender belongs to the spread sniper | Reproduced |
| K = 3 identical to K = 2 | Not tested: no K = 3 arm, by design | — |

---

## J. Scientific conclusion

**Does preventing immediate fatal capture create meaningful opponent-dependent strategic interaction, or primarily transform V4's forced line into delay, alternation, draws, location-count races or new seat pathologies?**

**Primarily the latter.** In the primary field, K = 2 changes the V4 result in three ways and no others:

1. **Delay.** 1,066 of 1,884 V4-decisive cells keep their winner exactly one tick later, and 16 cells of repair guard v guarded painter keep it but are decided 6–198 ticks later. This covers the single-location attackers' wins over the repair guard, the greedy painter and the counter (none of which disrupts before its core is taken), probe v sniper, the guarded painter's wins over the greedy painter, and every spread-sniper win.
2. **Scheduler-locked stalemate.** 610 cells now reach the tick limit, all through recovery. For every one of the 610 recovering entrants, zero-core ticks are phase-locked (≥ 0.95) to the scheduler's first-mover rotation. There are 448 draws, and 162 matches in which the recovering defender survives but loses on territory.
3. **One family of reversals.** 192 cells in which the guarded painter now beats the probe, sniper and counter in both seats. It does so by surviving the same phase-locked alternation until its painting front overwrites the attacker's core, and it wins while holding zero core cells.

Around those changes:

- **Pairing-level seat determination does not move** (0 of 45 SDI changes). The single-location attackers keep a Seat-A advantage (P(win) 0.556 as Seat A against 0.333 as Seat B).
- **A new deterministic seat inversion appears** in the guarded-painter mirror.
- **Location count's dominance over stacked defenders is untouched.**

K = 2 does do something real, and H1 is supported. It breaks the canonical V4 forced line: a single-location global attacker no longer beats a disrupt-first defender, in either seat. The opponent dependence this creates is a deterministic rock-paper-draw pattern (§G.4): sniper beats painter, painter beats defender on score, defender draws sniper. Its draw edge *is* the phase-locked stalemate. None of it has rate-eligible support in both seat tables, and the pre-registered significance test cannot tell it apart from the V4 control.

**K = 2 capture hold alone does not create sufficient strategic opponent-dependence under otherwise-V4 semantics.**

What it reveals is where the remaining determinism lives. With fatality delayed:

- the **defended state is the alternation**, and whoever moves first in a tick controls that tick;
- the only way a disrupt-first defender is ever captured is through an attacker with more locations than one disrupting chunk can cover.

Both effects come from the held-constant mechanics the design review named: scheduler rotation, the rule that one disrupting write disables every co-located process for the rest of the tick, and co-located spawn.

## K. E2 disposition

**E2 is a useful but insufficient mechanic, and it should remain research-only.**

- **Not "carry forward into V6 design".** The opponent dependence E2 creates is deterministic and constituted by pathologies: scheduler-locked stalemates, zero-core winners, and a new seat-determined mirror. Nothing in it is ready to shape a Ruleset.
- **Not a pre-registered "clean negative".** That rule requires H2 to be unsupported after seat conditioning. H2's tradeoff pattern survives seat conditioning in both tables as a deterministic characterization, and H1 is supported: E2 breaks the forced line it targeted. Recording a clean negative would overstate the rule.
- **Research-only, and no mechanic added inside E2.** `bytefray-rules-6-research-capture-hold-k2` stays a resolvable research Ruleset (registration §E.5). No mechanic is added inside E2, and K is not tuned: there is no K = 3 run. Any follow-up is a separately registered single-variable study (review §L.3).

## L. Next research question

**The single causal question best supported by these results:**

> *Is per-tick first-mover control — a single disrupting write silencing every co-located process of the opposing entrant for the rest of the tick — the load-bearing cause of the seat and scheduler-parity determination that remains once capture is no longer immediately fatal?*

Why this question and not another:

- Every E2 stalemate is phase-locked to which seat moves first (§F, H3b).
- Every E2 capture of a disrupt-first defender comes from an attacker with more locations than one two-action chunk can disrupt, with its onset on the victim's own first-mover tick (§F, onset parity).
- The design review's §D.5 conditions identify co-location plus single-write disruption as the mechanism that makes each tick first-mover-takes-all.

Candidates such as spawn dispersion, a disruption cap, or counting K in the victim's first-mover ticks each act on part of this link. Choosing among them, the parent Ruleset, and the pre-registration belong to a new, separately registered study. **Nothing is implemented here.**

---

## What this report does not claim

- No product or balance recommendation: the disposition above is a research disposition.
- No rate claim from a pairing with fewer than 8 distinct trajectories.
- No claim from the pooled table; it is reported only as subordinate.
- No K = 3 result.
- No change to any threshold, hypothesis, operationalization, fixture or analysis tool after the treatment ran.

## Appendix R. Reproduction

- **Primary analysis (frozen, unmodified):** `python -m tools.research.v6.e2.analyze_e2 --out <path>` at `f4ad557` or any later commit that preserves freeze v2. Its output hash is in §A.
- **Supplementary control-side reading of the H2 metrics (§G.3, §G.4; not a pre-registered criterion).** This runs the same frozen function with C-V4 in the treatment slot:

  ```python
  from tools.research.v6.e2.analyze_e2 import load_field_run, hypothesis_metrics
  from tools.research.v6.e2.preregistration import load_preregistration
  from tools.research.v6.e2.run_e2 import DEFAULT_RUN_ROOT, condition_root
  runs = {(c, f): load_field_run(condition_root(DEFAULT_RUN_ROOT, c, f), c, f)
          for c in ("C-V4", "C-RS") for f in ("F1", "F2")}
  runs[("T-E2", "F1")], runs[("T-E2", "F2")] = runs[("C-V4", "F1")], runs[("C-V4", "F2")]
  m = hypothesis_metrics(runs, load_preregistration())  # read h2.* only
  ```

- **Descriptive breakdowns (§D.2, §D.4, §F).** Cell-by-cell accounting, agent-level seat records, onset parity, zero-core winner identities and inference audits are tallies of frozen outputs only: the harness cell records, `trajectory_key`, the matchup `by_entrant` records, and `capture_analyzer.analyze_replay` telemetry. No threshold or new metric was introduced.
